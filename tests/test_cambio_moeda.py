"""Testes da conta em outra moeda (s390): `app/cambio.py` e a ligação no `/salvar`.

O QUE ABRIU A REGRA: as casas cripto (Bet Panda, Dex Sport, PariPesa, SapphireBet) apostam
em USD/USDT, e o sistema inteiro (P/L, KPI, dedup, Caixa) lê `bilhetes.stake` como R$. A
stake precisa chegar ao banco em R$, com a origem guardada ao lado.

A moeda é da CONTA e não da API: medido na Bet Panda em 03/10/2026, a lista do BetBy manda
`currency: "$"` e a URL pede `currency=USD`, com a carteira em Tether.

MUTAÇÕES QUE ESTES TESTES PEGAM (rodadas uma a uma contra o código real):
  • `float(k[1])` → `float(k[4])` (fechamento no lugar da abertura) → a stake de hoje
    mudaria a cada reenvio; o teste do candle pega
  • carimbo ignorado em `_iso_da_linha` (só a data do evento)       → cotação do dia errado
  • `if not taxa:` removido (grava sem cotação)                      → USDT vira R$
  • recusa sem `_linha` (posição recontada depois do filtro)          → id da linha boa some
  • `row["stake"]` não reescrita (só preenche `stake_orig`)            → banco fica em USDT
  • fallback USD sem o corte de 7 dias                                 → aposta velha no câmbio de hoje
  • `_dec` devolvendo float                                            → DataError no asyncpg
  s392 (EUR/AUD pelo PTAX genérico, ARS cruzado), 8 de 8 detectadas: sem o filtro de
  Fechamento · ARS invertido · ARS sem buscar USDT/ARS · PTAX sem recuo · `$` cabendo no
  peso · PTAX indo à rede com a faixa coberta · EUR fora do `_PTAX_MOEDAS` · `@moeda` fixo

O QUE ESTES TESTES **NÃO** COBREM:
  • a REDE: Binance e BCB são dublados aqui; a forma real do candle foi conferida à mão
    em 03/10/2026 (`data-api.binance.vision` e `api.binance.com`, mesmo candle);
  • o SQL do UPSERT: a regra "a origem anda junto com a stake" é exercida contra Postgres
    real em `tests/test_repository_db.py` (só no CI);
  • a tela: nenhuma tela lê `moeda`/`stake_orig` ainda (passo 3 da frente de moeda).
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

import cambio as C
import polymarket as P
import repository as R


def _row(**kw):
    base = dict(data="02/10/2026", esporte="Futebol", tipster="", aposta="Múltipla",
                descricao="Thame United x Rival", stake="25,00", odd="7,8", resultado="L",
                codigo_bilhete="1a26237f", casa="Dex Sport", parceiro="Feca")
    base.update(kw)
    return base


def _limpa():
    C._USDT_MAPA.clear()
    C._USDTARS_MAPA.clear()
    C._PTAX_MOEDA_MAPA.clear()
    C._PTAX_MOEDA_FAIXA.clear()
    C._HOJE_USD["v"] = None
    P._PTAX_MAPA.clear()


# ── conversão ────────────────────────────────────────────────────────────────

def test_conta_em_brl_nao_toca_em_nada():
    _limpa()
    rows = [_row()]
    ok, rej = C.converter_linhas(rows, "BRL", {}, R._num_or_none)
    assert rej == [] and ok[0]["stake"] == "25,00"
    assert "moeda" not in ok[0] and "stake_orig" not in ok[0]


def test_usdt_converte_a_stake_e_guarda_a_origem():
    _limpa()
    C._USDT_MAPA["2026-10-02"] = 5.2
    ok, rej = C.converter_linhas([_row()], "USDT", {}, R._num_or_none)
    assert rej == []
    assert ok[0]["stake"] == "130,00"            # 25 × 5,20
    assert ok[0]["stake_orig"] == 25.0
    assert ok[0]["cotacao"] == 5.2
    assert ok[0]["moeda"] == "USDT"
    assert ok[0]["odd"] == "7,8"                 # odd não tem moeda


def test_o_carimbo_de_colocacao_manda_sobre_a_data_do_evento():
    """O dinheiro sai quando a aposta é FEITA. Jogo de amanhã apostado hoje usa hoje."""
    _limpa()
    C._USDT_MAPA["2026-10-01"] = 5.0
    C._USDT_MAPA["2026-10-02"] = 9.0
    rows = [_row(data="02/10/2026")]
    ok, _ = C.converter_linhas(rows, "USDT", {"1a26237f": "20261001231000"}, R._num_or_none)
    assert ok[0]["cotacao"] == 5.0
    assert ok[0]["stake"] == "125,00"


def test_aberta_com_jogo_futuro_usa_a_cotacao_de_hoje():
    """s391: a data do bilhete é a do EVENTO. Aberta em jogo de amanhã pedia a cotação de
    um dia que não existe e era RECUSADA (10 de 12 abertas da DEX Sport). O dinheiro saiu
    no máximo hoje: vale a cotação de hoje."""
    _limpa()
    hoje = datetime.now(P.BRT).date()
    amanha = hoje + timedelta(days=1)
    C._USDT_MAPA[hoje.isoformat()] = 5.4
    rows = [_row(data=amanha.strftime("%d/%m/%Y"), resultado="")]
    ok, rej = C.converter_linhas(rows, "USDT", {}, R._num_or_none)
    assert rej == [], rej
    assert ok[0]["cotacao"] == 5.4 and ok[0]["stake"] == "135,00"
    # ISO e passado distante seguem como estavam.
    assert C._iso_da_linha(_row(data=amanha.isoformat()), None) == hoje.isoformat()
    assert C._iso_da_linha(_row(data="02/10/2026"), None) == "2026-10-02"


def test_data_iso_tambem_vale():
    _limpa()
    C._USDT_MAPA["2026-10-02"] = 5.0
    ok, _ = C.converter_linhas([_row(data="2026-10-02")], "USDT", {}, R._num_or_none)
    assert ok[0]["stake"] == "125,00"


def test_sem_cotacao_a_linha_e_recusada_e_nunca_gravada_como_real():
    _limpa()
    rows = [_row(_linha=4)]
    ok, rej = C.converter_linhas(rows, "USDT", {}, R._num_or_none)
    assert ok == []
    assert rej[0]["linha"] == 4
    assert rej[0]["campo"] == "stake" and "sem cotação USDT" in rej[0]["erro"]


def test_stake_vazia_passa_sem_conversao_e_sem_moeda():
    """Aberta lida pela metade: ausência viaja como ausência, sem moeda inventada."""
    _limpa()
    ok, rej = C.converter_linhas([_row(stake="")], "USDT", {}, R._num_or_none)
    assert rej == [] and ok[0]["stake"] == "" and "moeda" not in ok[0]


def test_numeracao_das_recusas_e_a_do_tsv_parseado():
    """O `/salvar` marca `_linha` ANTES do `validar_linhas`. Se a conversão numerasse a
    lista já filtrada, a recusa apontaria a linha errada e o front tiraria o id da boa."""
    _limpa()
    C._USDT_MAPA["2026-10-02"] = 5.0
    rows = [_row(odd="abc", codigo_bilhete="A"),            # 1: o validar recusa
            _row(codigo_bilhete="B"),                       # 2: converte
            _row(data="05/05/2020", codigo_bilhete="C")]    # 3: sem cotação
    for i, r in enumerate(rows, 1):
        r["_linha"] = i
    validas, rej_v = R.validar_linhas(rows)
    ok, rej_c = C.converter_linhas(validas, "USDT", {}, R._num_or_none)
    assert [r["linha"] for r in rej_v] == [1]
    assert [r["linha"] for r in rej_c] == [3]
    assert [r["codigo_bilhete"] for r in ok] == ["B"]


# ── cotação ──────────────────────────────────────────────────────────────────

def test_usdt_usa_a_abertura_do_candle():
    """A abertura do dia é fixa desde 00:00 UTC; o fechamento muda até meia-noite."""
    _limpa()

    async def fake_klines(client, inicio_ms, simbolo="USDTBRL"):
        return [[1790899200000, "5.19980000", "5.23", "5.19", "5.22960000"]]  # 02/10/2026

    original = C._klines
    C._klines = fake_klines
    try:
        asyncio.run(C._carregar_usdt(None, "2026-10-02"))
    finally:
        C._klines = original
    assert C.cotacao("USDT", "2026-10-02") == 5.1998


def test_usdt_pagina_ate_a_ultima_pagina_curta():
    _limpa()
    chamadas = []
    dia = 86_400_000

    async def fake_klines(client, inicio_ms, simbolo="USDTBRL"):
        chamadas.append(inicio_ms)
        n = C._BINANCE_LIMITE if len(chamadas) == 1 else 3
        # Como a API real: só candles com abertura >= startTime (o 1º dia cheio).
        base = -(-inicio_ms // dia) * dia
        return [[base + i * dia, "5.0"] for i in range(n)]

    original = C._klines
    C._klines = fake_klines
    try:
        asyncio.run(C._carregar_usdt(None, "2020-01-01"))
    finally:
        C._klines = original
    assert len(chamadas) == 2
    assert len(C._USDT_MAPA) == C._BINANCE_LIMITE + 3


def test_usd_usa_a_ptax_do_mesmo_mapa_do_polymarket():
    _limpa()
    P._PTAX_MAPA["2026-09-30"] = 5.31
    # 01/10 sem boletim: recua até o último publicado, como no Polymarket.
    assert C.cotacao("USD", "2026-10-01") == 5.31


def test_usd_sem_ptax_so_cai_na_de_hoje_para_aposta_recente():
    _limpa()
    C._HOJE_USD["v"] = 5.4
    hoje = datetime.now(P.BRT).date()
    recente = (hoje - timedelta(days=2)).isoformat()
    velha = (hoje - timedelta(days=60)).isoformat()
    assert C.cotacao("USD", recente) == 5.4
    assert C.cotacao("USD", velha) is None


def test_moeda_desconhecida_nao_tem_cotacao():
    assert C.cotacao("JPY", "2026-10-02") is None


# ── EUR / AUD pelo PTAX genérico, ARS cruzado na Binance (s392) ──────────────

def _boletins(dia, abertura, fechamento):
    """Os 5 boletins que o `CotacaoMoedaPeriodo` devolve por dia (forma medida em
    03/10/2026). O Fechamento NÃO é o primeiro: quem pega o 1º do dia pega a abertura."""
    return [
        {"cotacaoVenda": abertura, "dataHoraCotacao": f"{dia} 10:09:10.6", "tipoBoletim": "Abertura"},
        {"cotacaoVenda": abertura + 0.01, "dataHoraCotacao": f"{dia} 11:10:10.6", "tipoBoletim": "Intermediário"},
        {"cotacaoVenda": fechamento, "dataHoraCotacao": f"{dia} 13:03:16.2", "tipoBoletim": "Fechamento"},
    ]


class _Resp:
    def __init__(self, valor):
        self._v = valor

    def json(self):
        return {"value": self._v}


def _carrega_ptax(moeda, valor, de="2026-10-02"):
    chamadas = []

    async def fake_get(client, url, params):
        chamadas.append((url, params))
        return _Resp(valor)

    original = P._get_retry
    P._get_retry = fake_get
    try:
        asyncio.run(C._carregar_ptax_moeda(None, moeda, de))
    finally:
        P._get_retry = original
    return chamadas


def test_ptax_generico_usa_o_boletim_de_fechamento():
    _limpa()
    chamadas = _carrega_ptax("EUR", _boletins("2026-10-02", 5.8657, 5.8815))
    assert C.cotacao("EUR", "2026-10-02") == 5.8815
    url, params = chamadas[0]
    assert "CotacaoMoedaPeriodo" in url and params["@moeda"] == "'EUR'"


def test_ptax_generico_recua_no_fim_de_semana_e_separa_as_moedas():
    _limpa()
    _carrega_ptax("AUD", _boletins("2026-10-02", 3.62, 3.6321))     # sexta
    assert C.cotacao("AUD", "2026-10-04") == 3.6321                # domingo → sexta
    assert C.cotacao("EUR", "2026-10-02") is None                   # nada vaza entre moedas
    assert C.cotacao("AUD", "2026-11-30") is None                   # além dos 10 dias de recuo


def test_ptax_generico_nao_volta_a_rede_com_a_faixa_coberta():
    _limpa()
    _carrega_ptax("EUR", _boletins("2026-10-02", 5.8, 5.9))
    assert _carrega_ptax("EUR", [], de="2026-10-02") == []


def test_usd_continua_no_mapa_do_polymarket():
    """O USD NÃO passa a sair do PTAX genérico: seriam duas réguas de dólar."""
    _limpa()
    C._PTAX_MOEDA_MAPA["USD"] = {"2026-10-02": 9.99}
    P._PTAX_MAPA["2026-10-02"] = 5.22
    assert C.cotacao("USD", "2026-10-02") == 5.22


def test_ars_cruza_usdtbrl_por_usdtars_do_mesmo_dia():
    _limpa()
    C._USDT_MAPA["2026-10-02"] = 5.2266
    C._USDTARS_MAPA["2026-10-02"] = 1622.0
    assert abs(C.cotacao("ARS", "2026-10-02") - 5.2266 / 1622.0) < 1e-12
    # Falta um dos dois → não há cotação (nada de recuo nem de par de outro dia).
    C._USDT_MAPA["2026-10-01"] = 5.2
    assert C.cotacao("ARS", "2026-10-01") is None


def test_ars_converte_a_stake_em_reais():
    _limpa()
    C._USDT_MAPA["2026-10-02"] = 5.0
    C._USDTARS_MAPA["2026-10-02"] = 1000.0      # 1 peso = R$ 0,005
    ok, rej = C.converter_linhas([_row(stake="20000")], "ARS", {}, R._num_or_none)
    assert rej == [] and ok[0]["stake"] == "100,00" and ok[0]["moeda"] == "ARS"


def test_carregar_ars_busca_os_dois_pares():
    _limpa()
    pedidos = []

    async def fake_klines(client, inicio_ms, simbolo="USDTBRL"):
        pedidos.append(simbolo)
        return [[1790899200000, "5.0" if simbolo == "USDTBRL" else "1600.0"]]

    original = C._klines
    C._klines = fake_klines
    try:
        asyncio.run(C.carregar("ARS", ["2026-10-02"]))
    finally:
        C._klines = original
    assert sorted(pedidos) == ["USDTARS", "USDTBRL"]
    assert C.cotacao("ARS", "2026-10-02") == 5.0 / 1600.0


def test_todas_as_moedas_do_seletor_tem_fonte():
    """Moeda oferecida sem fonte faria toda captura da conta ser recusada."""
    for m in C.MOEDAS:
        assert m in (C.BRL, "USD", "USDT", "ARS") or m in C._PTAX_MOEDAS, m


def test_dolar_solto_contradiz_conta_em_peso():
    assert C.moedas_contraditorias("ARS", ["$"]) == ["$"]
    assert C.moedas_contraditorias("EUR", ["€", "EUR"]) == []
    assert C.moedas_contraditorias("AUD", ["A$"]) == []


def test_brl_e_identidade():
    assert C.cotacao("BRL", "") == 1.0


# ── fronteira com o banco ───────────────────────────────────────────────────

def test_numeric_vai_como_decimal_e_nunca_float():
    """asyncpg: NUMERIC exige Decimal, e `Decimal(25.1)` carrega lixo binário."""
    assert R._dec(25.1) == Decimal("25.1")
    assert isinstance(R._dec(5.1998), Decimal)
    assert R._dec(None) is None and R._dec("") is None
