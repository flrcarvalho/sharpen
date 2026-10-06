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


def test_anulado_com_indice_informado_e_metade_do_dinheiro():
    # Dado real (s397, Svrcina vs Darderi): 266,75 cotas a 0,60; o resgate traz o
    # índice do lado COMPRADO (1), `size` = 266,75 cotas e `usdcSize` = 133,375, metade.
    # Confiar só no índice gravava vitória cheia: 3 bilhetes do Feca, US$ 260,42 a
    # mais no P/L, achados pela Caixa da Polymarket.
    activity = [_act(size=266.75, price=0.5998, outcomeIndex=1),
                {"type": "REDEEM", "conditionId": "0xC", "outcomeIndex": 1, "size": 266.75,
                 "usdcSize": 133.375, "timestamp": 200}]
    mov = polymarket._movimento_por_lado(activity)
    assert polymarket._payouts_por_lado([], activity, mov) == {"0xC": {"A1": 0.5}}


def test_indice_informado_com_cota_cheia_continua_vitoria():
    # O caso comum (258 de 261 resgates medidos): `usdcSize` = `size`, $1 por cota.
    activity = [_act(size=100.0, price=0.5, outcomeIndex=1),
                {"type": "REDEEM", "conditionId": "0xC", "outcomeIndex": 1, "size": 100.0,
                 "usdcSize": 100.0, "timestamp": 200}]
    mov = polymarket._movimento_por_lado(activity)
    assert polymarket._payouts_por_lado([], activity, mov) == {"0xC": {"A1": 1.0}}


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

    async def fake_combos(client, wallet):
        return []   # combo tem teste próprio, abaixo; aqui só a paridade das simples

    monkeypatch.setattr(polymarket, "_paginate", fake_paginate)
    monkeypatch.setattr(polymarket, "_fetch_combos", fake_combos)
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


# ── Combos (s397) ─────────────────────────────────────────────────────────────
#
# A combo não aparece em /positions, então o coletor nunca a via: na carteira de
# referência (05/10/2026) só as 7 GANHAS entravam, e por acidente, pelo REDEEM no
# `_reconciliar_saidas`; 6 perdidas e 14 abertas ficavam de fora, com o sync verde.
#
# NÃO cobre: combo vendida antes de liquidar (nenhuma na carteira medida; a venda
# por RFQ não apareceu no /activity) e o painel ao vivo (`coletar_dashboard`), que
# continua sem listar combo aberta.

def _leg(i, evento, slug, mercado, escolha, event_id=None):
    return {"leg_index": i, "leg_outcome_label": escolha,
            "market": {"title": mercado, "slug": slug,
                       "event": {"event_id": event_id or slug, "event_slug": slug,
                                 "event_title": evento}}}


def _combo(cid="0xC1", status="OPEN", bruto="51.613988", pago="0.00", saldo="150.699708",
           legs=None, resolved_at=None):
    return {"combo_condition_id": cid, "status": status, "gross_entry_cost_usdc": bruto,
            "total_cost_usdc": "50.00", "realized_payout_usdc": pago, "shares_balance": saldo,
            "first_entry_at": "2026-10-06T01:08:43Z", "resolved_at": resolved_at,
            "legs": legs if legs is not None else [
                _leg(0, "Blues vs. Blackhawks", "nhl-stl-chi-2026-10-06", "Blues vs. Blackhawks", "Blackhawks"),
                _leg(1, "Wuning 3 (Doubles): Friend/Sueoka vs Ichikawa/Matsuda",
                     "atp-doubles-friesue-ichimat-2026-10-05",
                     "Wuning 3 (Doubles): Friend/Sueoka vs Ichikawa/Matsuda", "Ichikawa/Matsuda"),
            ]}


def _buy(cid, ts, size, usdc):
    return {"type": "TRADE", "side": "BUY", "conditionId": cid, "timestamp": ts,
            "size": size, "usdcSize": usdc, "isCombo": True, "asset": "A" + cid}


def test_separar_combos_tira_combo_do_caminho_das_simples():
    act = [_buy("0xC1", 1, 10, 5), {"type": "REDEEM", "conditionId": "0xC1", "isCombo": True},
           {"type": "TRADE", "side": "BUY", "conditionId": "0xS1"},
           # combo que a API de combos não listou: o `isCombo` do /activity também tira
           {"type": "TRADE", "side": "BUY", "conditionId": "0xC2", "isCombo": True}]
    pos = [{"conditionId": "0xC1"}, {"conditionId": "0xS1"}]
    a, p = polymarket._separar_combos([_combo("0xC1")], act, pos)
    assert [x["conditionId"] for x in a] == ["0xS1"]
    assert [x["conditionId"] for x in p] == ["0xS1"]


def test_combo_retorno_por_status():
    r = polymarket._combo_retorno_total
    assert r(_combo(status="OPEN")) is None
    assert r(_combo(status="PARTIAL")) is None
    assert r(_combo(status="RESOLVED_LOSS", saldo="274.7")) == 0.0
    # ganha e resgatada: o saldo zera e o pago é o retorno
    assert r(_combo(status="RESOLVED_WIN", pago="90.54", saldo="0")) == 90.54
    # ganha e NÃO resgatada: cada cota vale $1
    assert r(_combo(status="RESOLVED_WIN", pago="0", saldo="90.54")) == 90.54
    # perna anulada sem resgate ainda: aberta, não um W/L inventado
    assert r(_combo(status="RESOLVED_PARTIAL", pago="0", saldo="10")) is None
    assert r(_combo(status="RESOLVED_PARTIAL", pago="30", saldo="0")) == 30.0


def test_combo_ganha_l_e_aberta_viram_linhas_certas():
    act = [_buy("0xW", 100, 90.54, 63.958)]
    ganha = _combo("0xW", "RESOLVED_WIN", bruto="63.958100", pago="90.54", saldo="0",
                   resolved_at="2026-08-09T21:44:30Z")
    [(linha, iso, res)] = polymarket._combo_linhas_base(ganha, act)
    assert res == "W" and iso == "2026-08-09"
    assert linha["codigo_bilhete"] == "0xW"
    assert abs(linha["stake_usd_cru"] - 63.9581) < 1e-9            # COM a taxa
    assert linha["odd"] == polymarket._fmt_odd(90.54 / 63.9581)     # retorno ÷ stake
    assert linha["aposta"] == "Múltipla"

    perdida = _combo("0xL", "RESOLVED_LOSS", bruto="163.340789", saldo="274.725274",
                     resolved_at="2026-08-04T23:36:44Z")
    [(linha, iso, res)] = polymarket._combo_linhas_base(perdida, [_buy("0xL", 50, 274.725274, 163.340789)])
    assert res == "L"
    assert linha["odd"] == polymarket._fmt_odd(274.725274 / 163.340789)  # odd do possível resultado

    aberta = _combo("0xA", "OPEN", bruto="26.0", saldo="125")
    [(linha, iso, res)] = polymarket._combo_linhas_base(aberta, [_buy("0xA", 1791000000, 125, 26.0)])
    assert res == "" and iso == polymarket._iso_brt(1791000000)    # data da COMPRA


def test_combo_comprada_duas_vezes_parte_por_compra():
    # Dado real: 0x038925aa…, duas compras de ~US$ 26 dois minutos uma da outra.
    act = [_buy("0xC1", 1791248923, 56.315565, 25.695089),   # fora de ordem de propósito
           _buy("0xC1", 1791248843, 94.384143, 25.918899)]
    combo = _combo("0xC1", "RESOLVED_WIN", pago="150.699708", saldo="0",
                   resolved_at="2026-10-06T05:00:00Z")
    linhas = polymarket._combo_linhas_base(combo, act)
    assert [l["codigo_bilhete"] for l, _, _ in linhas] == ["0xC1__0", "0xC1__1"]
    assert [l["descricao"][-5:] for l, _, _ in linhas] == ["[1/2]", "[2/2]"]
    # a 1ª é a compra mais antiga (94,38 cotas), e as stakes fecham com o custo bruto
    assert abs(linhas[0][0]["stake_usd_cru"] - 25.918899) < 1e-6
    assert abs(sum(l["stake_usd_cru"] for l, _, _ in linhas) - 51.613988) < 1e-6
    # o retorno vai na proporção das cotas: cada compra recebe as suas
    assert linhas[0][0]["odd"] == polymarket._fmt_odd(94.384143 / 25.918899)


def test_combo_esporte_pela_regra_global():
    ec = polymarket._combo_esporte_categoria
    nhl = _leg(0, "Blues vs. Blackhawks", "nhl-stl-chi-2026-10-06", "Blues vs. Blackhawks", "Blackhawks")
    atp1 = _leg(1, "Suzhou: A vs B", "atp-a-b-2026-10-05", "Suzhou: A vs B", "A")
    atp2 = _leg(2, "Antofagasta: C vs D", "atp-c-d-2026-10-05", "Antofagasta: C vs D", "C")
    atp3 = _leg(3, "Villena: E vs F", "atp-e-f-2026-10-05", "Villena: E vs F", "E")
    assert ec([nhl, atp1]) == ("Múltiplos", "Múltipla")            # esportes diferentes
    assert ec([atp1, atp2]) == ("Tênis", "Múltipla")               # 2 jogos do mesmo esporte
    assert ec([atp1, atp2, atp3]) == ("Múltiplos", "Múltipla")     # 3+ jogos diferentes
    bb = [_leg(i, "LoL: Fluxo vs FURIA (BO3)", "lol-fxw7-fur-2026-08-09", m, "x", event_id="803535")
          for i, m in enumerate(["Game 1 Winner", "Total Kills Over/Under 30.5 in Game 1?", "Game 2 Winner"])]
    assert ec(bb) == ("E-Sports", "Múltipla")                       # bet builder: esporte do jogo


def test_combo_descricao_nao_repete_o_confronto():
    d = polymarket._combo_perna_desc
    assert d(_leg(0, "Villena: A vs B", "atp-x", "Villena: A vs B Set 1 O/U 8.5", "Under")) \
        == "Villena: A vs B Set 1 O/U 8.5: Under"
    assert d(_leg(0, "Vila Nova vs. Cuiabá - More Markets", "bra-x", "Vila Nova O/U 0.5", "Under")) \
        == "Vila Nova vs. Cuiabá - Vila Nova O/U 0.5: Under"
    assert d(_leg(0, "Blues vs. Blackhawks", "nhl-x", "Blues vs. Blackhawks", "Blackhawks")) \
        == "Blues vs. Blackhawks: Blackhawks"


class _Resp:
    def __init__(self, data):
        self._d = data

    def json(self):
        return self._d


def test_fetch_combos_pede_cada_status_e_segue_o_cursor(monkeypatch):
    # Sem filtro de status a API ESCONDE a ganha resgatada: a busca tem de pedir a
    # RESOLVED_WIN explicitamente. E pagina por cursor, não por offset.
    pedidos = []

    async def fake_get(client, url, params):
        pedidos.append((params["status"], params.get("cursor")))
        assert url.endswith("/v1/positions/combos")
        if params["status"] == "RESOLVED_WIN":
            if not params.get("cursor"):
                return _Resp({"combos": [_combo("0xW1", "RESOLVED_WIN")],
                              "pagination": {"has_more": True, "next_cursor": "c2"}})
            return _Resp({"combos": [_combo("0xW2", "RESOLVED_WIN")],
                          "pagination": {"has_more": False, "next_cursor": None}})
        if params["status"] == "OPEN":
            return _Resp({"combos": [_combo("0xO1")], "pagination": {"has_more": False}})
        return _Resp({"combos": [], "pagination": {"has_more": False}})

    monkeypatch.setattr(polymarket, "_get_retry", fake_get)
    out = asyncio.run(polymarket._fetch_combos(None, "0xw"))
    assert sorted(c["combo_condition_id"] for c in out) == ["0xO1", "0xW1", "0xW2"]
    assert ("RESOLVED_WIN", "c2") in pedidos
    assert {s for s, _ in pedidos} == set(polymarket._COMBO_STATUS)


def test_fetch_combos_resposta_estranha_falha_alto(monkeypatch):
    async def fake_get(client, url, params):
        return _Resp({"error": "rate limited"})

    monkeypatch.setattr(polymarket, "_get_retry", fake_get)
    with pytest.raises(polymarket.PolymarketRespostaInesperada):
        asyncio.run(polymarket._fetch_combos(None, "0xw"))


def test_coletar_tudo_combo_ganha_sai_uma_vez_e_aberta_entra(monkeypatch):
    # O caso que motivou a mudança, ponta a ponta: a ganha tem REDEEM no /activity e
    # saía pelo `_reconciliar_saidas` (stake sem taxa); a perdida e a aberta não saíam.
    ts = int(datetime(2026, 8, 9, 12, 0, tzinfo=polymarket.BRT).timestamp())
    activity = [
        _buy("0xW", ts, 90.54, 63.958),
        {"type": "REDEEM", "conditionId": "0xW", "timestamp": ts + 3600, "size": 90.54,
         "outcomeIndex": 999, "isCombo": True},
        _buy("0xL", ts, 274.7, 163.34),
        _buy("0xA", ts + 86400 * 50, 125, 26.0),
    ]
    combos = [
        _combo("0xW", "RESOLVED_WIN", bruto="63.958", pago="90.54", saldo="0",
               resolved_at="2026-08-09T21:44:30Z"),
        _combo("0xL", "RESOLVED_LOSS", bruto="163.34", saldo="274.7",
               resolved_at="2026-08-04T23:36:44Z"),
        _combo("0xA", "OPEN", bruto="26.0", saldo="125"),
    ]

    async def fake_paginate(client, path, wallet, extra, page_size):
        return [dict(a) for a in activity] if path == "activity" else []

    async def fake_combos(client, wallet):
        return combos

    async def fake_cotacao(client, iso, cache, hoje):
        return 5.0

    async def nada(*a, **k):
        return None

    async def fake_ptax_hoje(client):
        return 5.0

    monkeypatch.setattr(polymarket, "_paginate", fake_paginate)
    monkeypatch.setattr(polymarket, "_fetch_combos", fake_combos)
    monkeypatch.setattr(polymarket, "_cotacao_para", fake_cotacao)
    monkeypatch.setattr(polymarket, "_garantir_cobertura", nada)
    monkeypatch.setattr(polymarket, "_ptax_hoje", fake_ptax_hoje)

    res, atv = asyncio.run(polymarket.coletar_tudo("0xWALLET", "P [x]"))
    assert sorted(r["codigo_bilhete"] for r in res) == ["0xL", "0xW"]   # a ganha UMA vez
    assert [r["codigo_bilhete"] for r in atv] == ["0xA"]
    w = next(r for r in res if r["codigo_bilhete"] == "0xW")
    assert w["resultado"] == "W" and w["stake"] == polymarket._fmt_money(63.958 * 5.0)
    assert w["data"] == "09/08/2026" and w["parceiro"] == "P [x]" and "stake_usd_cru" not in w
    assert next(r for r in res if r["codigo_bilhete"] == "0xL")["resultado"] == "L"
    assert atv[0]["resultado"] == "" and atv[0]["esporte"] == "Múltiplos"


# ── Taxa de entrada nas apostas SIMPLES (s397) ───────────────────────────────
#
# Provado na blockchain (06/10/2026): na compra 0x6ae41b0c… saíram 166,00 pUSD da
# carteira, 160 para as cotas e 6,00 para o coletor de taxa; o `usdcSize` da activity
# é 166 e o `initialValue` da API é 160. A stake vinha do `initialValue`: as 564
# compras simples do Feca perderam US$ 730,94 de taxa, e em 10 posições a API manda
# `initialValue = 0` e a derrota gravava stake ZERO (P/L 0, a perda sumia).
#
# NÃO cobre: o painel ao vivo (`coletar_dashboard`) usa o mesmo `_stake_usd`, mas não
# tem teste próprio aqui.

def _buy_s(cid, ts, size, price, usdc, asset="A1"):
    return {"type": "TRADE", "side": "BUY", "conditionId": cid, "asset": asset,
            "timestamp": ts, "size": size, "price": price, "usdcSize": usdc}


def test_stake_usd_prefere_o_que_saiu_da_carteira():
    s = polymarket._stake_usd
    assert s({"_stakeBruto": 166.0, "grossInitialValue": 166, "initialValue": 160}) == 166.0
    # sem compra na activity: o bruto da API, nunca o valor sem taxa
    assert s({"grossInitialValue": 166, "initialValue": 160}) == 166
    # `initialValue` ZERO não é stake: cai para o que houver (aqui, cotas × preço)
    assert s({"initialValue": 0, "grossInitialValue": 0, "size": 213.65, "avgPrice": 0.25}) \
        == 213.65 * 0.25


def test_compra_unica_com_taxa_grava_stake_bruta_e_odd_sobre_ela():
    # Dado real: UFC, 640 cotas a 0,25, US$ 160 + US$ 6 de taxa, perdida.
    pos = {"conditionId": "0xU", "asset": "A1", "size": 640, "avgPrice": 0.25,
           "initialValue": 160, "grossInitialValue": 166, "entryFeesUsdc": 6,
           "redeemable": True, "curPrice": 0.0, "title": "UFC Fight Night: X vs Y",
           "eventSlug": "ufc-x-y-2026-08-01"}
    [u] = polymarket._split_multibuys([pos], [_buy_s("0xU", 1, 640, 0.25, 166)])
    assert polymarket._stake_usd(u) == 166
    assert polymarket._odd_de_entrada(u) == 640 / 166          # e não 1/0,25 = 4
    res, odd = polymarket._liquidacao(u, {"0xU": {"A1": 0.0}}, polymarket._movimento_por_lado(
        [_buy_s("0xU", 1, 640, 0.25, 166)]))
    assert res == "L"
    linha = polymarket._montar_linha(u, "P", "2026-08-01", 1.0, "L")
    assert linha["stake"] == "166,00" and linha["stake_usd"] == 166


def test_initial_value_zero_nao_vira_stake_zero():
    # Dado real (Karmine Corp GC vs Joblife GC): a API manda initialValue/gross 0; a
    # activity diz que saíram US$ 54,99. Antes: derrota com stake 0,00.
    pos = {"conditionId": "0xK", "asset": "A1", "size": 213.65, "avgPrice": 0.2481,
           "initialValue": 0, "grossInitialValue": 0, "entryFeesUsdc": 0,
           "redeemable": True, "curPrice": 0.0, "title": "Valorant: KC GC vs Joblife GC (BO3)"}
    [u] = polymarket._split_multibuys([pos], [_buy_s("0xK", 1, 213.65, 0.2481, 54.9926)])
    linha = polymarket._montar_linha(u, "P", "2026-08-08", 1.0, "L")
    assert linha["stake"] == "54,99"


def test_compra_repetida_cada_fatia_leva_a_propria_taxa():
    act = [_buy_s("0xM", 2, 100, 0.40, 41.5), _buy_s("0xM", 1, 50, 0.50, 26.25)]
    pos = {"conditionId": "0xM", "asset": "A1", "size": 150, "avgPrice": 0.433,
           "initialValue": 65, "grossInitialValue": 67.75, "redeemable": False, "curPrice": 0.5}
    fatias = polymarket._split_multibuys([pos], act)
    assert [polymarket._stake_usd(f) for f in fatias] == [26.25, 41.5]   # ordem cronológica
    assert polymarket._odd_de_entrada(fatias[0]) == 50 / 26.25


def test_reconciliada_soma_o_bruto_das_compras():
    # Vitória resgatada some de /positions e volta pela activity: a stake é o bruto.
    act = [_buy_s("0xR", 1, 100, 0.5, 52.5),
           {"type": "REDEEM", "conditionId": "0xR", "timestamp": 9, "size": 100, "outcomeIndex": 0}]
    act[0]["outcomeIndex"] = 0
    mov = polymarket._movimento_por_lado(act)
    payouts = polymarket._payouts_por_lado([], act, mov)
    [u] = polymarket._split_multibuys(polymarket._reconciliar_saidas([], act, [], payouts), act)
    assert polymarket._stake_usd(u) == 52.5
    res, odd = polymarket._liquidacao(u, payouts, mov)
    assert res == "W" and odd == 100 / 52.5                     # retorno ÷ o que saiu


def test_sem_taxa_a_odd_continua_a_mesma_string():
    # Bilhete antigo sem taxa: usdcSize = cotas × preço → odd = 1/preço literal, para o
    # re-sync não reescrever a odd já gravada por diferença de arredondamento.
    pos = {"conditionId": "0xN", "asset": "A1", "size": 80, "avgPrice": 0.5,
           "initialValue": 40, "redeemable": True, "curPrice": 1.0}
    [u] = polymarket._split_multibuys([pos], [_buy_s("0xN", 1, 80, 0.5, 40.0)])
    assert polymarket._odd_de_entrada(u) == 1 / 0.5
    # Aqui `cotas ÷ stake` dá 1,7543859649122806 e `1/preço` dá …808: só o literal
    # preserva a string gravada.
    pos2 = {"conditionId": "0xN2", "asset": "A1", "size": 121.4285, "avgPrice": 0.57,
            "initialValue": 69.214245, "redeemable": False, "curPrice": 0.6}
    [u2] = polymarket._split_multibuys([pos2], [_buy_s("0xN2", 1, 121.4285, 0.57, 69.214245)])
    assert polymarket._odd_de_entrada(u2) == 1 / 0.57


def test_anulada_com_taxa_perde_a_taxa():
    # Dado real (SPARTA vs Bebop): anulada, devolveu US$ 100 de US$ 101,50. Era V com
    # P/L 0; a taxa não volta, então é cashout abaixo da stake: W com odd < 1.
    act = [_buy_s("0xV", 1, 200, 0.5, 101.5)]
    pos = {"conditionId": "0xV", "asset": "A1", "size": 200, "avgPrice": 0.5,
           "initialValue": 100, "grossInitialValue": 101.5, "redeemable": True, "curPrice": 0.5}
    [u] = polymarket._split_multibuys([pos], act)
    mov = polymarket._movimento_por_lado(act)
    res, odd = polymarket._liquidacao(u, polymarket._payouts_por_lado([pos], act, mov), mov)
    assert res == "W" and abs(odd - 100 / 101.5) < 1e-12
