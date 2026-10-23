"""Gate do adaptador `vv` (Vave, plataforma própria `softlabs`), s427.

Os crus são a fixture `extensor/harness/fixtures/vave.cru.json`, gerada pelo `vv_inject.js` REAL
no sandbox do harness sobre a resposta da casa (`vave.history.json`, recon de 21/10/2026, conta
do Feca, 11 perdidas, `userId` zerado) e o recorte dos dicionários (`vave.dicionarios.json`).
Cada valor esperado vem do card da casa (`casos/vave.mjs`) e da `CASA_VAVE.md`, nunca do que o
código produz.

Ganha sem amostra na fixture: os testes dela clonam a perdida com o DINHEIRO de dois ganhos
reais da `captura_crua` (23/10/2026, só leitura; contas do Gabriel em USDC): 5402884, simples,
33 @ 1,9 → `win` = `winFull` = 62,7; e 5372493, múltipla, 39,84551559 @ 4,31 → 171,73417219.
Lá o `win` É o retorno, não o lucro, e a IA gravou W nos dois.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. cru sem `dicionario` deixa de recusar                    → test_cru_sem_dicionario_recusa
  2. `{-hcp}` sem inverter o sinal                            → test_template_como_o_card
  3. `{!quarternr}` sem ordinal                               → test_template_como_o_card
  4. placeholder sem valor fica no nome                       → test_placeholder_sem_valor_recusa
  5. retorno da ganha = stake + `win` (o lucro)               → test_ganha_com_o_dinheiro_real
  6. anulada pelo rótulo (status 3), não pelo dinheiro        → test_retorno_igual_a_stake_e_anulada
  7. perdida aceita com dinheiro                              → test_perdida_com_dinheiro_recusa
  8. system / bet builder / bônus / freebet / cashout deixam de recusar → test_sem_amostra_recusa
  9. perna pelo status do bilhete                             → test_perna_tem_o_status_dela
 10. o time do mercado não vira `{time}` na chave de categoria → test_mercado_com_time_vira_chave

O QUE NÃO COBRE: aberta, devolvida e cashout reais (a casa ainda não mostrou nenhum), bet
builder e sistema; e o `finishedAt`, que fica fora da Ficha porque o fuso não foi provado.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import dicionario  # noqa: E402
import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, vv  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {vv.codigo(c): c for c in vv.bilhetes_da_resposta(
    json.loads((_FIX / "vave.cru.json").read_text(encoding="utf-8")))}
SIMPLES = "5433760"        # 30 USDT @ 4,2, perdida
TRIPLA = "5433248"         # 30 USDT @ 15,7: perdida · ganha · perdida no card


def _montar(cru, casa="VAVE"):
    f, motivos = ficha.montar_ficha("vv", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=SIMPLES, **campos):
    c = copy.deepcopy(CRUS[cod])
    c["bet"].update(campos)
    return c


def test_familia_registrada_e_toda_fixture_monta():
    assert ADAPTADORES["vv"] is vv
    assert len(CRUS) == 11
    for cod, cru in CRUS.items():
        f, d = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] == "USDT" and d["resultado"] == "L"


def test_perdida_bate_com_o_card():
    f, d = _montar(CRUS[TRIPLA])
    assert (f["stake"], f["odd"], f["retorno"], f["tipo"]) == ("30", "15.7", "0", "multipla")
    assert d["odd"] == "15,7"                   # a odd do card, nunca zerada na perdida
    assert f["colocada_em"].startswith("2026-10-19T21:27:27")      # 18:27:27 em São Paulo
    assert [p["evento"] for p in f["pernas"]][1] == "EC Uniao Corinthians - Cruzeiro Basquete"
    assert f["pernas"][1]["esporte_casa"] == "Basketball"
    assert f["pernas"][1]["liga_casa"] == "Brazil · NBB"


def test_template_como_o_card():
    """`{-hcp}` com hcp=1 → `(-1)`; `{+hcp}` com hcp=-2.5 → `(-2.5)`; `{!quarternr}` → `1st`."""
    p = _montar(CRUS[TRIPLA])[0]["pernas"]
    assert (p[0]["mercado_casa"], p[0]["selecao_casa"]) == ("Oxford United clean sheet", "yes")
    assert (p[1]["mercado_casa"], p[1]["selecao_casa"]) == ("1st half - handicap", "Cruzeiro Basquete (-1)")
    assert (p[2]["mercado_casa"], p[2]["selecao_casa"]) == ("1st half - corner handicap", "Roma (-2.5)")
    q = _montar(CRUS["5432739"])[0]["pernas"][0]
    assert (q["mercado_casa"], q["selecao_casa"], q["linha"]) == ("1st quarter - total", "over 42.5", "42.5")
    assert _montar(CRUS[SIMPLES])[0]["pernas"][0]["mercado_casa"] == "Clube Atletico Mineiro clean sheet"


def test_perna_tem_o_status_dela():
    assert [p["status_perna"] for p in _montar(CRUS[TRIPLA])[0]["pernas"]] == \
        ["perdida", "ganha", "perdida"]


def test_cru_sem_dicionario_recusa():
    """O cru de antes da 0.7.63 (os 35 do banco) não tem como dar nome ao mercado."""
    c = copy.deepcopy(CRUS[SIMPLES])
    del c["dicionario"]
    with pytest.raises(Recusa, match="dicionario"):
        vv.adaptar(c, "VAVE")
    c = copy.deepcopy(CRUS[SIMPLES])
    c["dicionario"]["mercados"] = {}
    with pytest.raises(Recusa, match="dicionário sem o mercado"):
        vv.adaptar(c, "VAVE")


def test_placeholder_sem_valor_recusa():
    c = copy.deepcopy(CRUS["5432739"])
    c["bet"]["details"][0]["specifiers"] = "quarternr=1"          # sem o `total`
    with pytest.raises(Recusa, match="sem valor"):
        vv.adaptar(c, "VAVE")


def test_ganha_com_o_dinheiro_real():
    f, d = _montar(_clone(SIMPLES, status=2, amount=33, value=1.9, win=62.7, winFull=62.7))
    assert (f["status"], f["retorno"], d["resultado"], d["odd"]) == ("ganha", "62.7", "W", "1,9")
    f, d = _montar(_clone(TRIPLA, status=2, amount=39.84551559, value=4.31,
                          win=171.73417219, winFull=171.73417219))
    assert (f["retorno"], d["resultado"], d["odd"]) == ("171.73417219", "W", "4,31")


def test_ganha_que_nao_fecha_recusa():
    with pytest.raises(Recusa, match="sem amostra"):
        vv.adaptar(_clone(status=2, win=100, winFull=100), "VAVE")       # 30 × 4,2 = 126


def test_retorno_igual_a_stake_e_anulada():
    for st in (2, 3, 8):
        f, d = _montar(_clone(status=st, win=30, winFull=30))
        assert (f["status"], d["resultado"]) == ("anulada", "V")
    with pytest.raises(Recusa):
        vv.adaptar(_clone(status=3, win=126, winFull=126), "VAVE")      # dinheiro de W, rótulo 3


def test_perdida_com_dinheiro_recusa():
    with pytest.raises(Recusa, match="perdida com win"):
        vv.adaptar(_clone(win=5, winFull=5), "VAVE")


def test_aberta_sem_retorno():
    f, d = _montar(_clone(status=0))
    assert (f["status"], f["retorno"], d["resultado"]) == ("aberta", None, "")


@pytest.mark.parametrize("campo,valor", [("system", 2), ("betBetBuilderId", 7), ("bonusAmount", 3),
                                         ("freebetAmount", 5), ("betCashoutAmount", 20)])
def test_sem_amostra_recusa(campo, valor):
    with pytest.raises(Recusa):
        vv.adaptar(_clone(**{campo: valor}), "VAVE")


def test_mercado_com_time_vira_chave_de_categoria():
    """`{$competitor2} clean sheet` com times diferentes é UMA chave (s427), como o `{jogador}`."""
    a = _montar(CRUS[SIMPLES])[0]["pernas"][0]
    b = _montar(CRUS["5432746"])[0]["pernas"][1]
    assert dicionario._merc_time(a) == dicionario._merc_time(b) == "{time} clean sheet"
    f = _montar(CRUS[SIMPLES])[0]
    assert ("categoria", "{time} clean sheet") in dicionario.chaves(f)
    esp, cat, faltam = dicionario.traduzir(f, {("esporte", "football"): "Futebol",
                                               ("categoria", "{time} clean sheet"): "Clean Sheet"})
    assert (esp, cat, faltam) == ("Futebol", "Clean Sheet", [])
