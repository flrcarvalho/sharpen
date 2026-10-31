"""Kalshi (s435) — o coletor traduz a conta pela API, sem IA.

Fixture: a aposta REAL do recon de 30/10/2026 (conta do Feca), recortada aos campos
que o coletor lê. É um combo de mesmo jogo, perdido: 231,74 cotas a US$ 0,081 + taxa
US$ 1,20756. O golden do `casas/CASA_KALSHI.md §15` sai daqui.

O que NÃO cobre (sem amostra): o formato de `revenue` numa vitória, venda antes de
liquidar além de "fica fora do lote", mercado anulado/escalar além de "levanta", o
histórico arquivado (`/historical/positions`) e a Caixa. A rede HTTP é dublada por
`httpx.MockTransport`: a assinatura é conferida contra a chave pública, mas nunca contra
a Kalshi de verdade.

Mutação: 13 aplicadas em 30/10/2026, 12 detectadas. A que escapa é INÓCUA: tirar o
`_normalizar_pem` não quebra nada porque a `cryptography` 48 já aceita sozinha as quatro
formas de colar (uma linha, a quebra da tela da Kalshi, recuo, `\\r\\n`). Ele fica pela
faixa do `requirements.txt` (a partir da 42, não medida).
"""
import asyncio
import base64
import json

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

import kalshi

ORDEM = "01a18a7b-b308-7092-9090-73f505ebce19"
TICKER = "KXMVECROSSCATEGORY-S20265YRLKBHJASBWFORV-P3OK25B7M"

FILL = {
    "action": "buy", "count_fp": "231.74", "created_time": "2026-10-30T01:45:25.391108Z",
    "fee_cost": "1.207560", "fill_id": "0727a395-7f29-ba7a-c643-bf29430792c2",
    "market_ticker": TICKER, "no_price_dollars": "0.9190", "order_id": ORDEM,
    "side": "yes", "ticker": TICKER, "yes_price_dollars": "0.0810",
}
SETTLEMENT = {"ticker": TICKER, "market_result": "no", "revenue": 0,
              "settled_time": "2026-10-30T04:27:23.6105Z", "yes_count_fp": "231.74"}


def _ordem(**kw):
    ordens, _ = kalshi.agrupar_ordens([{**FILL, **kw}])
    return ordens[ORDEM]


# ── Ordem, stake e taxa ──────────────────────────────────────────────────────

def test_stake_e_custo_mais_taxa_da_ordem_real():
    o = _ordem()
    assert o["cotas"] == pytest.approx(231.74)
    assert o["custo"] == pytest.approx(18.77094)
    assert o["taxa"] == pytest.approx(1.20756)
    assert o["custo"] + o["taxa"] == pytest.approx(19.9785)


def test_lado_no_usa_o_preco_do_no():
    o = _ordem(side="no")
    assert o["custo"] == pytest.approx(231.74 * 0.919)


def test_fills_da_mesma_ordem_somam_e_fill_repetido_conta_uma_vez():
    f2 = {**FILL, "fill_id": "outro", "count_fp": "10", "fee_cost": "0.05"}
    ordens, _ = kalshi.agrupar_ordens([FILL, f2, FILL])   # FILL repetido: live + arquivado
    o = ordens[ORDEM]
    assert o["cotas"] == pytest.approx(241.74)
    assert o["taxa"] == pytest.approx(1.25756)


def test_venda_tira_o_mercado_inteiro_do_lote():
    venda = {**FILL, "fill_id": "v1", "order_id": "outra", "action": "sell"}
    ordens, vendas = kalshi.agrupar_ordens([FILL, venda])
    assert ordens == {}
    assert vendas == [TICKER]


# ── Resultado pelo dinheiro ──────────────────────────────────────────────────

def test_combo_perdido_e_L_com_odd_cotas_sobre_stake():
    res, odd = kalshi.liquidacao(_ordem(), SETTLEMENT)
    assert res == "L"
    assert odd == pytest.approx(231.74 / 19.9785)          # 11,5995, não o 12,35 da tela


def test_lado_certo_e_W_com_odd_retorno_sobre_stake():
    res, odd = kalshi.liquidacao(_ordem(), {**SETTLEMENT, "market_result": "yes"})
    assert res == "W"
    assert odd == pytest.approx(231.74 / 19.9785)


def test_retorno_igual_a_stake_e_V():
    # 10 cotas a US$ 0,99 + US$ 0,10 de taxa = US$ 10,00; acertou → retorno US$ 10,00
    o = _ordem(count_fp="10", yes_price_dollars="0.99", fee_cost="0.10")
    res, _ = kalshi.liquidacao(o, {**SETTLEMENT, "market_result": "yes"})
    assert res == "V"


def test_sem_liquidacao_e_aberta():
    assert kalshi.liquidacao(_ordem(), None) is None


def test_liquidacao_nao_medida_levanta_em_vez_de_chutar():
    with pytest.raises(kalshi.KalshiErro):
        kalshi.liquidacao(_ordem(), {**SETTLEMENT, "market_result": "void"})


# ── Data, esporte, descrição ─────────────────────────────────────────────────

def test_data_e_a_do_jogo_pelo_ticker_nao_a_da_liquidacao():
    assert kalshi.data_do_ticker("KXNBA2D-26OCT29MEMPOR") == "2026-10-29"
    assert kalshi._iso_brt(SETTLEMENT["settled_time"]) == "2026-10-30"   # o dia seguinte
    assert kalshi.data_do_ticker("KXMVECROSSCATEGORY-S20265YRLKBHJASBWFORV") == ""


NBA = {"tags": ["Basketball"]}


def test_esporte_mesmo_jogo_fica_com_o_esporte():
    evs = ["KXNBA2D-26OCT29MEMPOR", "KXNBAAST-26OCT29MEMPOR"]
    assert kalshi.esporte_e_jogo([NBA, NBA], evs) == "Basquete"


def test_esporte_tres_jogos_ou_dois_esportes_e_multiplos():
    tres = ["KXNBA2D-26OCT29MEMPOR", "KXNBA2D-26OCT29LALBOS", "KXNBA2D-26OCT29NYKMIA"]
    assert kalshi.esporte_e_jogo([NBA] * 3, tres) == "Múltiplos"
    kalshi.ESPORTE_POR_TAG["Soccer"] = "Futebol"
    try:
        assert kalshi.esporte_e_jogo([NBA, {"tags": ["Soccer"]}],
                                     ["KXNBA2D-26OCT29MEMPOR", "KXEPL-26OCT29ARSCHE"]) == "Múltiplos"
    finally:
        del kalshi.ESPORTE_POR_TAG["Soccer"]


def test_tag_desconhecida_e_outro():
    assert kalshi.esporte_e_jogo([{"tags": ["Politics"]}], ["KXFED-26DEC"]) == "Outro"


def test_lado_no_na_descricao():
    assert kalshi.descricao_perna({"title": "Ja Morant: 10+ assists"}, "no") == "Não: Ja Morant: 10+ assists"


def test_golden_da_linha():
    o = _ordem()
    res, odd = kalshi.liquidacao(o, SETTLEMENT)
    r = kalshi.montar_linha(o, "Feca [Eu]", esporte="Basquete", aposta="Múltipla",
                            descricao="d", iso="2026-10-29", cotacao=5.3744,
                            resultado=res, odd=odd)
    assert r["data"] == "29/10/2026"
    assert r["stake_orig"] == 19.98 and r["moeda"] == "USD"
    assert r["stake"] == "107,37"                      # 19,9785 × 5,3744
    assert r["taxa_orig"] == pytest.approx(1.20756)    # informação: já dentro da stake
    assert r["odd"].startswith("11,5994")
    assert r["codigo_bilhete"] == ORDEM and r["casa"] == "Kalshi"


# ── Chave: formato, assinatura e escopo ──────────────────────────────────────

def _par():
    priv = ed25519.Ed25519PrivateKey.generate()
    pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()
    return priv, pem


def test_pem_numa_linha_so_carrega():
    # A cópia da tela da Kalshi vem com espaços no lugar das quebras de linha.
    _, pem = _par()
    uma_linha = " ".join(pem.split())
    assert "\n" not in uma_linha
    kalshi.carregar_chave(uma_linha)


def test_pem_invalido_da_mensagem_de_chave():
    with pytest.raises(kalshi.KalshiChaveInvalida):
        kalshi.carregar_chave("-----BEGIN PRIVATE KEY----- lixo -----END PRIVATE KEY-----")


def _cliente(priv, escopos, key_id):
    pub = priv.public_key()

    def handler(req: httpx.Request):
        ts = req.headers["KALSHI-ACCESS-TIMESTAMP"]
        sig = base64.b64decode(req.headers["KALSHI-ACCESS-SIGNATURE"])
        # Assina o caminho SEM query: verificar levanta se a mensagem for outra.
        pub.verify(sig, (ts + "GET" + req.url.path).encode())
        assert req.url.path == "/trade-api/v2/api_keys"
        return httpx.Response(200, json={"api_keys": [
            {"api_key_id": key_id, "name": "Sharpen", "scopes": escopos}]})
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


KEY_ID = "55bd53ea-6b28-4d31-b9a1-0d8c52eb45d6"


def test_chave_so_leitura_passa_e_assinatura_confere():
    priv, pem = _par()
    cred = kalshi.Credencial(KEY_ID, pem)

    async def go():
        async with _cliente(priv, ["read"], KEY_ID) as c:
            await kalshi.conferir_chave(c, cred)
    asyncio.run(go())


@pytest.mark.parametrize("escopos", [["read", "write"], ["write"], ["read", "write::trade"]])
def test_chave_que_pode_operar_e_recusada(escopos):
    priv, pem = _par()
    cred = kalshi.Credencial(KEY_ID, pem)

    async def go():
        async with _cliente(priv, escopos, KEY_ID) as c:
            await kalshi.conferir_chave(c, cred)
    with pytest.raises(kalshi.KalshiChaveInvalida):
        asyncio.run(go())


def test_credencial_nao_vaza_a_chave_no_repr():
    _, pem = _par()
    cred = kalshi.Credencial(KEY_ID, pem)
    corpo = pem.split("-----")[2].strip()[:20]
    assert corpo not in repr(cred) and KEY_ID not in repr(cred)
