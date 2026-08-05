"""Polymarket — confiabilidade de saldo (#47) e cálculo de odd.

Guarda o fix: quando TODOS os RPCs públicos caem, `_rpc_balance` devolve None
(indisponível), NUNCA 0.0 (que mentiria "carteira vazia"). polymarket.py só usa
stdlib + httpx (sem asyncpg/database), então importa direto.
"""
import asyncio
from datetime import datetime, timezone

import httpx
import pytest

import polymarket


class _Down:
    async def post(self, *a, **k):
        raise Exception("rpc down")


class _Ok:
    async def post(self, *a, **k):
        class R:
            def json(self_inner):
                return {"result": "0x" + format(5_000_000, "x").rjust(64, "0")}
        return R()


def test_rpc_balance_none_quando_todos_rpcs_caem():
    got = asyncio.run(polymarket._rpc_balance(_Down(), polymarket._PUSD, "0x" + "0" * 40))
    assert got is None   # indisponível — NÃO 0.0


def test_rpc_balance_valor_quando_responde():
    got = asyncio.run(polymarket._rpc_balance(_Ok(), polymarket._PUSD, "0x" + "0" * 40))
    assert got == 5.0    # 5_000_000 / 1e6 (6 casas)


def test_calc_odd_e_sempre_payout_ratio():
    # Uma odd pra tudo = 1/preço (retorno/investimento), independente de ganhar/perder
    # e IGNORANDO o cashPnl (que carrega taxa). Preço 0,40 → 2,5.
    assert abs(polymarket._calc_odd({"avgPrice": 0.40, "cashPnl": 60.0}) - 2.5) < 1e-9    # vencedora
    assert abs(polymarket._calc_odd({"avgPrice": 0.40, "cashPnl": -40.0}) - 2.5) < 1e-9   # perdedora
    # Lucro com taxa (55, não 60) NÃO altera a odd — é a limpa 1/preço:
    assert abs(polymarket._calc_odd({"initialValue": 40.0, "cashPnl": 55.0, "avgPrice": 0.40}) - 2.5) < 1e-9


def test_calc_odd_sem_preco_valido_cai_em_1():
    assert polymarket._calc_odd({"avgPrice": 0}) == 1.0
    assert polymarket._calc_odd({"avgPrice": 1.5}) == 1.0


# ── Persistir posições ATIVAS como bilhete aberto (frente A) ─────────────────

def test_montar_linha_ativa_e_bilhete_aberto():
    # Ativa = resultado vazio (→ extraction_state 'aberta', sem P/L), odd = 1/preço,
    # stake em BRL = stake_usd × cotação da data da COMPRA.
    pos = {"title": "Lakers vs Celtics", "eventSlug": "nba-lal-bos-2026-05-01",
           "initialValue": 40.0, "avgPrice": 0.40, "conditionId": "0xabc"}
    linha = polymarket._montar_linha(pos, "Feca [Eu]", "2026-05-01", 5.0, "")
    assert linha["resultado"] == ""            # aberta
    assert linha["casa"] == "Polymarket"
    assert linha["esporte"] == "Basquete"      # pelo prefixo do slug
    assert linha["odd"] == "2,5"               # 1/0,40
    assert linha["stake"] == "200,00"          # 40 × 5,0 (BRL, vírgula decimal)
    assert linha["stake_usd"] == 40.0
    assert linha["codigo_bilhete"] == "0xabc"
    assert linha["data"] == "01/05/2026"


def test_montar_linha_resolvida_e_ativa_mesma_formatacao():
    # O helper é IDÊNTICO nos dois caminhos; só o `resultado` muda (a resolvida traz W/L/V).
    pos = {"title": "x", "initialValue": 10.0, "avgPrice": 0.5, "conditionId": "0xd"}
    resolvida = polymarket._montar_linha(pos, "P", "2026-01-01", 5.0, "W")
    ativa = polymarket._montar_linha(pos, "P", "2026-01-01", 5.0, "")
    assert resolvida["resultado"] == "W" and ativa["resultado"] == ""
    for campo in ("stake", "odd", "stake_usd", "codigo_bilhete", "data", "esporte"):
        assert resolvida[campo] == ativa[campo]
    assert resolvida["stake"] == "50,00" and resolvida["odd"] == "2"


def test_montar_linha_split_descricao_indexada():
    pos = {"title": "Match", "_splitTotal": 3, "_splitIndex": 1,
           "initialValue": 5.0, "avgPrice": 0.25, "_splitId": "0xc__1", "conditionId": "0xc"}
    linha = polymarket._montar_linha(pos, "P", "2026-01-01", 5.0, "")
    assert linha["descricao"] == "Match [2/3]"
    assert linha["codigo_bilhete"] == "0xc__1"   # código do split, não do conditionId cru


def test_build_buy_cache_pega_menor_timestamp_de_buy():
    activity = [
        {"type": "BUY", "conditionId": "A", "timestamp": 200},
        {"type": "BUY", "conditionId": "A", "timestamp": 100},   # abertura da posição A
        {"side": "BUY", "conditionId": "B", "timestamp": 50},
        {"type": "REDEEM", "conditionId": "A", "timestamp": 10},  # REDEEM não conta
    ]
    cache = polymarket._build_buy_cache(activity)
    assert cache == {"A": 100, "B": 50}


def test_data_compra_iso_usa_buy_timestamp_do_split():
    ts = int(datetime(2026, 5, 1, 15, 0, tzinfo=timezone.utc).timestamp())  # 12:00 BRT
    pos = {"_buyTimestamp": ts, "conditionId": "A"}
    assert polymarket._data_compra_iso(pos, {}) == "2026-05-01"


def test_data_compra_iso_cai_no_buy_cache_para_compra_unica():
    ts = int(datetime(2026, 3, 10, 18, 0, tzinfo=timezone.utc).timestamp())  # 15:00 BRT
    pos = {"conditionId": "A"}   # compra única: sem _buyTimestamp
    assert polymarket._data_compra_iso(pos, {"A": ts}) == "2026-03-10"


def test_data_compra_iso_fallback_startdate_sem_buy():
    pos = {"conditionId": "Z", "startDate": "2026-02-20T10:00:00Z"}
    assert polymarket._data_compra_iso(pos, {}) == "2026-02-20"


# ── Esporte de vitórias reconciliadas (achado: caíam todas em 'Outro') ───────

def _reconciliar(activity, positions=()):
    """Atalho dos testes: monta movimento+payouts e reconcilia o que saiu da carteira."""
    mov = polymarket._movimento_por_lado(activity)
    payouts = polymarket._payouts_por_lado(list(positions), activity, mov)
    return polymarket._reconciliar_saidas([], activity, list(positions), payouts)


def test_reconciliar_saidas_preserva_eventslug_e_detecta_esporte():
    # A vitória resgatada some de /positions e é recuperada da activity. Antes o
    # eventSlug era descartado → o título en-US ("O/U 1.5 Rounds") não casava nada →
    # 'Outro'. Agora o slug ufc-… é preservado e a detecção acha MMA.
    activity = [
        {"type": "TRADE", "side": "BUY", "conditionId": "R1", "asset": "A1", "outcomeIndex": 0,
         "size": 10, "price": 0.5, "timestamp": 100, "title": "O/U 1.5 Rounds",
         "eventSlug": "ufc-abc-2026-07-11", "slug": "ufc-abc-totals-1pt5"},
        {"type": "REDEEM", "conditionId": "R1", "outcomeIndex": 0, "size": 10, "timestamp": 200,
         "title": "O/U 1.5 Rounds", "eventSlug": "ufc-abc-2026-07-11", "slug": "ufc-abc-totals-1pt5"},
    ]
    extras = _reconciliar(activity)
    assert len(extras) == 1
    assert extras[0]["eventSlug"] == "ufc-abc-2026-07-11"
    assert polymarket._detes_raw(extras[0]["title"], extras[0]["eventSlug"]) == "MMA"


# ── Liquidação: quanto CADA COTA pagou (sessão 195) ──────────────────────────
#
# Bugs que estes testes prendem, todos provados na carteira real do Feca:
#   1. anulada/vitória-não-resgatada viravam bilhete ABERTO para sempre;
#   2. anulada (50/50) virava W/L cheio, com o dobro da odd;
#   3. mercado comprado nos DOIS lados virava duas vitórias;
#   4. venda antecipada não gerava linha nenhuma.

def _pos(**kw):
    base = {"conditionId": "0xC", "asset": "A1", "title": "Time A vs Time B",
            "eventSlug": "cs2-a-b-2026-07-14", "size": 100.0, "avgPrice": 0.4,
            "initialValue": 40.0, "redeemable": True}
    base.update(kw)
    return base


def test_posicao_anulada_e_resolvida_nao_aberta():
    # curPrice 0,5 + redeemable = mercado ANULADO (50/50). Antes falhava o teste
    # `currentValue < 0.01` e virava bilhete aberto eterno (caso do Feca em 13/07).
    assert polymarket._posicao_resolvida(_pos(curPrice=0.5, currentValue=50.0)) is True


def test_vitoria_nao_resgatada_e_resolvida_nao_aberta():
    assert polymarket._posicao_resolvida(_pos(curPrice=1.0, currentValue=100.0)) is True


def test_derrota_continua_resolvida():
    assert polymarket._posicao_resolvida(_pos(curPrice=0.0, currentValue=0.0)) is True


def test_preco_de_mercado_nao_e_liquidacao():
    # Guarda: preço fora de {0; 0,5; 1} não é liquidação, mesmo com redeemable ligado.
    # Melhor deixar ABERTA do que gravar um W/L que o UPSERT depois não rebaixa.
    assert polymarket._posicao_resolvida(_pos(curPrice=0.63, currentValue=63.0)) is False
    assert polymarket._payout_de_liquidacao(0.63) is None


def test_anulada_vira_cashout_e_nao_vitoria_cheia():
    # Comprou a 0,40 e cada cota pagou 0,50 → retorno 50 sobre stake 40.
    # Régua de cashout (MASTER_RESULTADO §5.6): W com odd = retorno ÷ stake = 1,25.
    # Antes saía W com odd 2,5 (1/preço) → P/L 2× o real.
    pos = _pos(curPrice=0.5, currentValue=50.0, _cotas=100.0, _lado="A1")
    payouts = {"0xC": {"A1": 0.5}}
    assert polymarket._liquidacao(pos, payouts, {}) == ("W", 1.25)


def test_vitoria_cheia_mantem_odd_de_entrada():
    # Payout $1/cota → retorno ÷ stake É 1/preço. Devolvemos a odd de entrada para a
    # string da odd não mudar nos ~370 bilhetes já salvos (senão o re-sync os reescreve).
    pos = _pos(curPrice=1.0, currentValue=100.0, _cotas=100.0, _lado="A1")
    assert polymarket._liquidacao(pos, {"0xC": {"A1": 1.0}}, {}) == ("W", 2.5)


def test_derrota_mantem_odd_do_possivel_resultado():
    pos = _pos(curPrice=0.0, currentValue=0.0, _cotas=100.0, _lado="A1")
    assert polymarket._liquidacao(pos, {"0xC": {"A1": 0.0}}, {}) == ("L", 2.5)


def test_anulada_que_devolve_o_stake_e_void():
    # Comprou exatamente a 0,50 e recebeu 0,50 → devolveu o stake → V (P/L zero).
    pos = _pos(avgPrice=0.5, initialValue=50.0, _cotas=100.0, _lado="A1")
    assert polymarket._liquidacao(pos, {"0xC": {"A1": 0.5}}, {})[0] == "V"


def test_sem_liquidacao_continua_aberta():
    pos = _pos(_cotas=100.0, _lado="A1")
    assert polymarket._liquidacao(pos, {}, {}) is None


def _act(**kw):
    base = {"type": "TRADE", "side": "BUY", "conditionId": "0xC", "asset": "A1",
            "outcomeIndex": 0, "size": 100.0, "price": 0.4, "usdcSize": 40.0,
            "timestamp": 100, "title": "Time A vs Time B", "eventSlug": "cs2-a-b-2026-07-14"}
    base.update(kw)
    return base


def test_indice_999_com_metade_e_anulado():
    # 200 cotas, resgate de 100 = 0,50/cota → anulado.
    activity = [_act(size=200.0), {"type": "REDEEM", "conditionId": "0xC",
                                   "outcomeIndex": 999, "size": 100.0, "timestamp": 200}]
    mov = polymarket._movimento_por_lado(activity)
    assert polymarket._payouts_por_lado([], activity, mov) == {"0xC": {"A1": 0.5}}


def test_indice_999_com_total_do_lado_e_vitoria_cheia():
    # negative-risk: o resgate passa pelo adaptador e o índice vem 999, mas pagou $1/cota.
    # Ler 999 como "anulado" cortava a vitória pela metade (regressão pega no gate real).
    activity = [_act(size=200.0), {"type": "REDEEM", "conditionId": "0xC",
                                   "outcomeIndex": 999, "size": 200.0, "timestamp": 200}]
    mov = polymarket._movimento_por_lado(activity)
    assert polymarket._payouts_por_lado([], activity, mov) == {"0xC": {"A1": 1.0}}


def test_dois_lados_do_mesmo_mercado_sao_apostas_independentes():
    # Comprou os DOIS lados: um ganha, o outro perde. Antes o P/L era agregado por
    # conditionId e o MESMO resultado era carimbado nas duas pernas (5 derrotas viraram
    # vitória na carteira do Feca). Cada lado é aposta própria — pode ser de outro tipster.
    activity = [
        _act(asset="A1", outcomeIndex=0, size=100.0, price=0.4, timestamp=100),
        _act(asset="A2", outcomeIndex=1, size=200.0, price=0.6, timestamp=200),
        {"type": "REDEEM", "conditionId": "0xC", "outcomeIndex": 1, "size": 200.0,
         "timestamp": 300, "title": "Time A vs Time B"},
    ]
    mov = polymarket._movimento_por_lado(activity)
    payouts = polymarket._payouts_por_lado([], activity, mov)
    assert payouts == {"0xC": {"A1": 0.0, "A2": 1.0}}
    unidades = polymarket._split_multibuys(_reconciliar(activity), activity)
    res = {u["_splitId"]: polymarket._liquidacao(u, payouts, mov) for u in unidades}
    # códigos distintos (senão os dois lados colidem na dedup) e resultados opostos
    assert res["0xC__0"][0] == "L" and res["0xC__1"][0] == "W"


def test_venda_antecipada_vira_cashout():
    # Comprou 100 cotas por $40 e vendeu por $34 antes de liquidar. Antes a aposta
    # não gerava linha NENHUMA (o módulo só conhecia BUY e REDEEM).
    activity = [_act(), _act(side="SELL", size=100.0, price=0.34, usdcSize=34.0, timestamp=200)]
    extras = _reconciliar(activity)
    assert len(extras) == 1
    mov = polymarket._movimento_por_lado(activity)
    unidade = polymarket._split_multibuys(extras, activity)[0]
    resultado, odd = polymarket._liquidacao(unidade, {}, mov)
    assert resultado == "W" and abs(odd - 0.85) < 1e-9   # 34 ÷ 40


def test_venda_total_com_po_de_cota_conta_como_saida():
    # Comprou 352,941175 e vendeu 352,94: a sobra é pó de arredondamento, não posição
    # viva. O limiar é o mesmo `sizeThreshold` que faz a API parar de listar a posição.
    activity = [_act(size=352.941175, price=0.17, usdcSize=60.0),
                _act(side="SELL", size=352.94, price=0.16, usdcSize=55.05, timestamp=200)]
    assert len(_reconciliar(activity)) == 1


def test_detes_slug_nwsl_e_futebol():
    assert polymarket._detes_raw("Will Orlando Pride win?", "nwsl-pri-bay-2026-05-29") == "Futebol"


def test_detes_fallback_corners_sem_slug_e_futebol():
    # Rede de segurança de título: "Corners" só existe em futebol (o caso do Feca).
    assert polymarket._detes_raw("Spain vs. Belgium: O/U 3.5 Corners", "") == "Futebol"


def test_detes_fallback_kills_sem_slug_e_esports():
    assert polymarket._detes_raw("Total Kills Over/Under 30.5 in Game 2?", "") == "E-Sports"


# ── Paginação: teto de sanidade (anti loop-infinito de proxy preso) ──────────

def test_paginate_para_em_pagina_incompleta(monkeypatch):
    # 1 página cheia (100) + 1 parcial (50) → 150 itens, encerra normal sem loop.
    paginas = [[{"i": k} for k in range(100)], [{"i": k} for k in range(50)]]

    async def fake(client, url, params):
        idx = params["offset"] // 100
        return paginas[idx] if idx < len(paginas) else []

    monkeypatch.setattr(polymarket, "_get_json", fake)
    out = asyncio.run(polymarket._paginate(None, "positions", "0xw", {}, 100))
    assert len(out) == 150


def test_paginate_trava_proxy_preso(monkeypatch):
    # Proxy defeituoso devolvendo SEMPRE página cheia: sem o teto seria loop infinito.
    # Deve abortar com PolymarketRespostaInesperada em vez de pendurar.
    async def fake(client, url, params):
        return [{"i": 0}] * 100

    monkeypatch.setattr(polymarket, "_get_json", fake)
    with pytest.raises(polymarket.PolymarketRespostaInesperada):
        asyncio.run(polymarket._paginate(None, "positions", "0xw", {}, 100))


# ── Consolidação do fetch: coletar_tudo == coletar_bilhetes + coletar_ativas ──

# Vitória ainda NÃO resgatada: segue em /positions valendo o total das cotas
# (curPrice 1,0). É o caso que o filtro antigo (`currentValue < 0.01`) jogava para
# "aberta". O fixture anterior descrevia vitória com currentValue 0 — combinação que
# não existe no dado real: resgatou, some de /positions.
_POS_RESOLVIDA = {
    "conditionId": "0xRES", "redeemable": True, "curPrice": 1.0, "currentValue": 80.0,
    "avgPrice": 0.5, "title": "Lakers vs Celtics", "initialValue": 40.0, "size": 80.0,
    "eventSlug": "nba-lal-bos-2026-05-01", "endDate": "2026-05-02T00:00:00Z",
    "startDate": "2026-05-01T00:00:00Z",
}
_POS_ATIVA = {
    "conditionId": "0xATV", "redeemable": False, "curPrice": 0.5, "currentValue": 25.0,
    "avgPrice": 0.4, "title": "Heat vs Bucks", "initialValue": 20.0, "size": 20.0,
    "eventSlug": "nba-mia-mil-2026-06-01", "endDate": "2026-06-02T00:00:00Z",
    "startDate": "2026-06-01T00:00:00Z",
}


def test_coletar_tudo_paridade_com_funcoes_separadas(monkeypatch):
    # coletar_tudo busca positions+activity UMA vez e deriva resolvidas+ativas; deve dar a
    # MESMA saída que coletar_bilhetes + coletar_ativas (que buscavam 2×). Prova a consolidação
    # (o ganho é fazer 1 fetch em vez de 2 — a saída não pode mudar).
    async def fake_paginate(client, path, wallet, extra, page_size):
        # cópias frescas a cada chamada: mutações de _split_multibuys não vazam entre caminhos
        return [dict(_POS_RESOLVIDA), dict(_POS_ATIVA)] if path == "positions" else []

    async def fake_ptax_hoje(client):
        return 5.0

    async def fake_cotacao(client, iso, cache, hoje):
        return 5.0   # câmbio fixo → sem rede PTAX/BCB

    async def fake_cobertura(client, iso):
        return None  # a carga em massa também é rede — sem isto o teste sai para o BCB

    monkeypatch.setattr(polymarket, "_paginate", fake_paginate)
    monkeypatch.setattr(polymarket, "_ptax_hoje", fake_ptax_hoje)
    monkeypatch.setattr(polymarket, "_cotacao_para", fake_cotacao)
    monkeypatch.setattr(polymarket, "_garantir_cobertura", fake_cobertura)

    resolvidas_t, ativas_t = asyncio.run(polymarket.coletar_tudo("0xWALLET", "P [x]"))
    resolvidas_s = asyncio.run(polymarket.coletar_bilhetes("0xWALLET", "P [x]"))
    ativas_s = asyncio.run(polymarket.coletar_ativas("0xWALLET", "P [x]"))

    assert resolvidas_t == resolvidas_s   # resolvidas idênticas
    assert ativas_t == ativas_s           # ativas idênticas
    # e exercitou de fato os dois caminhos:
    assert len(resolvidas_t) == 1 and resolvidas_t[0]["resultado"] == "W"
    assert len(ativas_t) == 1 and ativas_t[0]["resultado"] == ""


# ── PTAX em massa: 1 chamada no lugar de N (s247) ────────────────────────────
#
# O sync levava >3 min porque pedia a cotação de UMA data por vez: 76 datas de
# bilhete viravam 111 chamadas sequenciais ao BCB, a ~1,7s cada. Pior, `_ptax`
# devolvia None tanto para "dia sem boletim" quanto para "o BCB falhou", então um
# timeout consumia os 10 recuos e derrubava o sync inteiro. Estes testes travam as
# duas correções: a faixa única e a distinção falha × sem-boletim.


@pytest.fixture(autouse=True)
def _mapa_ptax_limpo():
    """O mapa é de MÓDULO (vive entre requisições, de propósito). Zera entre testes
    para um não herdar a cobertura do outro."""
    polymarket._PTAX_MAPA.clear()
    polymarket._PTAX_DE = ""
    polymarket._PTAX_ATE = ""
    yield
    polymarket._PTAX_MAPA.clear()
    polymarket._PTAX_DE = ""
    polymarket._PTAX_ATE = ""


def _resposta_periodo(itens):
    class R:
        def json(self):
            return {"value": itens}
    return R()


def test_carregar_periodo_indexa_por_dia_e_mantem_o_primeiro(monkeypatch):
    # O BCB republica alguns dias com dois boletins (ex.: 23/04/2025, mesmo valor).
    # Vale o PRIMEIRO — é o que o `$top=1` do endpoint por data devolvia. Trocar a
    # escolha mudaria stake já gravado num re-sync.
    async def fake_get(client, url, params):
        assert url == polymarket.BCB_PTAX_PERIODO
        return _resposta_periodo([
            {"cotacaoVenda": 5.10, "dataHoraCotacao": "2026-08-03 13:05:10.123"},
            {"cotacaoVenda": 5.20, "dataHoraCotacao": "2026-08-04 13:06:30.416"},
            {"cotacaoVenda": 5.99, "dataHoraCotacao": "2026-08-04 13:06:30.443"},
        ])

    monkeypatch.setattr(polymarket, "_get_retry", fake_get)
    asyncio.run(polymarket._carregar_periodo(None, "2026-08-01", "2026-08-04"))
    assert polymarket._PTAX_MAPA == {"2026-08-03": 5.10, "2026-08-04": 5.20}
    assert polymarket._PTAX_DE == "2026-08-01" and polymarket._PTAX_ATE == "2026-08-04"


def test_cotacao_do_mapa_recua_ate_10_dias_e_para():
    polymarket._PTAX_MAPA.update({"2026-07-31": 5.0773})
    assert polymarket._cotacao_do_mapa("2026-07-31") == 5.0773   # o próprio dia
    assert polymarket._cotacao_do_mapa("2026-08-02") == 5.0773   # domingo → recua p/ sexta
    assert polymarket._cotacao_do_mapa("2026-08-09") == 5.0773   # 9 dias depois: ainda pega
    assert polymarket._cotacao_do_mapa("2026-08-10") is None     # 10 dias: fora da janela


def test_uma_unica_chamada_ao_bcb_para_muitas_datas(monkeypatch):
    # A regressão que importa: 76 datas distintas não podem virar 76 idas à rede.
    chamadas = []

    async def fake_get(client, url, params):
        chamadas.append(params["@dataInicial"])
        return _resposta_periodo([{"cotacaoVenda": 5.0, "dataHoraCotacao": f"2026-05-{d:02d} 13:00:00"}
                                  for d in range(1, 32)])

    monkeypatch.setattr(polymarket, "_get_retry", fake_get)
    monkeypatch.setattr(polymarket, "_hoje_iso", lambda: "2026-05-31")

    cache: dict = {}
    datas = [f"2026-05-{d:02d}" for d in range(10, 31)]
    for iso in datas:
        got = asyncio.run(polymarket._cotacao_para(None, iso, cache, 5.0))
        assert got == 5.0
    assert len(chamadas) == 1, f"esperava 1 carga em massa, houve {len(chamadas)}"


def test_bcb_fora_do_ar_aborta_em_vez_de_virar_dia_sem_boletim(monkeypatch):
    # Antes: falha de rede virava None, indistinguível de "não houve boletim" → o
    # código recuava 10 dias, chamava 10× e só então derrubava o sync. Agora a falha
    # é falha: CambioIndisponivel na hora (→ 503 "tente de novo").
    async def fake_get(client, url, params):
        raise httpx.ConnectError("BCB fora do ar")

    monkeypatch.setattr(polymarket, "_get_retry", fake_get)
    with pytest.raises(polymarket.CambioIndisponivel):
        asyncio.run(polymarket._garantir_cobertura(None, "2026-05-10"))


def test_cobertura_ja_carregada_nao_repete_chamada(monkeypatch):
    # Cotação de dia passado é imutável → o 2º sync não gasta rede nenhuma.
    chamadas = []

    async def fake_get(client, url, params):
        chamadas.append(params)
        return _resposta_periodo([{"cotacaoVenda": 5.0, "dataHoraCotacao": "2026-05-15 13:00:00"}])

    monkeypatch.setattr(polymarket, "_get_retry", fake_get)
    monkeypatch.setattr(polymarket, "_hoje_iso", lambda: "2026-05-20")

    asyncio.run(polymarket._garantir_cobertura(None, "2026-05-15"))
    asyncio.run(polymarket._garantir_cobertura(None, "2026-05-16"))   # dentro da faixa
    assert len(chamadas) == 1


def test_inicio_hint_pega_a_compra_mais_antiga():
    # 01/05/2026 12:00 BRT e 10/06/2026 — o hint tem que ser o menor, senão a 1ª carga
    # pede uma janela em torno de hoje e o histórico antigo dispara uma 2ª chamada.
    ts_maio = int(datetime(2026, 5, 1, 12, 0, tzinfo=polymarket.BRT).timestamp())
    ts_junho = int(datetime(2026, 6, 10, 12, 0, tzinfo=polymarket.BRT).timestamp())
    activity = [{"timestamp": ts_junho}, {"timestamp": ts_maio}, {"timestamp": 0}]
    assert polymarket._inicio_hint(activity) == "2026-05-01"
    assert polymarket._inicio_hint([]) == polymarket._hoje_iso()
