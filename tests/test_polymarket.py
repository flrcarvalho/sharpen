"""Polymarket — confiabilidade de saldo (#47) e cálculo de odd.

Guarda o fix: quando TODOS os RPCs públicos caem, `_rpc_balance` devolve None
(indisponível), NUNCA 0.0 (que mentiria "carteira vazia"). polymarket.py só usa
stdlib + httpx (sem asyncpg/database), então importa direto.
"""
import asyncio
from datetime import datetime, timezone

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

def test_reconciliar_redeems_preserva_eventslug_e_detecta_esporte():
    # A vitória resgatada some de /positions e é recuperada da activity. Antes o
    # eventSlug era descartado → o título en-US ("O/U 1.5 Rounds") não casava nada →
    # 'Outro'. Agora o slug ufc-… é preservado e a detecção acha MMA.
    activity = [
        {"type": "TRADE", "side": "BUY", "conditionId": "R1", "size": 10, "price": 0.5,
         "timestamp": 100, "title": "O/U 1.5 Rounds",
         "eventSlug": "ufc-abc-2026-07-11", "slug": "ufc-abc-totals-1pt5"},
        {"type": "REDEEM", "conditionId": "R1", "size": 20, "timestamp": 200,
         "title": "O/U 1.5 Rounds", "eventSlug": "ufc-abc-2026-07-11", "slug": "ufc-abc-totals-1pt5"},
    ]
    extras = polymarket._reconciliar_redeems([], activity, set())
    assert len(extras) == 1
    assert extras[0]["eventSlug"] == "ufc-abc-2026-07-11"
    assert polymarket._detes_raw(extras[0]["title"], extras[0]["eventSlug"]) == "MMA"


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
