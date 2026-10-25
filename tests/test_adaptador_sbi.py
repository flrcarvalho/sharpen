"""Gate do adaptador `sbi` (Sportsbet.io, plataforma própria GraphQL), s428.

Os crus são os `node` das fixtures `extensor/harness/fixtures/sportsbetio.settled.json` (17
liquidadas) e `sportsbetio.active.json` (14 abertas), as respostas da casa ao replay no recon de
25/10/2026 (conta do Feca, USDT). Cada valor esperado vem do card da casa (Minhas Apostas,
`casos/sportsbetio.mjs`), nunca do que o código produz.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. escala 1e6 no lugar de 1e8                                → test_ganha_bate_com_o_card
  2. odd do bilhete por `odds` (sem o turbo)                   → test_turbinada_usa_a_odd_do_card
  3. `voidFactor` ignorado na perna                             → test_perna_anulada_como_o_card
  4. código = o id em base64, não o ObjectId                    → test_codigo_e_o_objectid_do_card
  5. perdida sem exigir perna perdida                           → test_sem_retorno_e_sem_perna_perdida_recusa
  6. Bet Builder deixa de recusar                               → test_sem_amostra_recusa
  7. moeda fora de USDT aceita                                  → test_sem_amostra_recusa
  8. retorno = stake não vira anulada                           → test_retorno_igual_a_stake_e_anulada

O QUE NÃO COBRE: anulada inteira, cashout, freebet e sistema reais (a conta não tinha; os testes
de dinheiro clonam a perdida); `liga_casa` (a casa não manda a liga no bilhete); esporte de slug
fora do mapa (vai vazio).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, sbi  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {}
for _nome in ("sportsbetio.settled.json", "sportsbetio.active.json"):
    for _c in sbi.bilhetes_da_resposta(json.loads((_FIX / _nome).read_text(encoding="utf-8"))):
        CRUS[sbi.codigo(_c)] = _c

GANHA = "6add45c3bf9e9d0001114d46"      # simples, 60,01 @ 1,77 → "+ 106,21" no card
TURBO_W = "6adc8eefbf9e9d00016fa2ac"    # TURBINADO, 25 @ 13,15 (odds 12,71) → "+ 328,75"
TURBO_L = "6adbc55dbf9e9d0001c75309"    # TURBINADO perdido, card 5,83 (odds 5,71)
ANULADA = "6add828bbf9e9d0001c921a7"    # 25 @ 5,07: vermelha · CINZA · vermelha no card
PERDIDA = "6addf2d1bf9e9d0001d7fda3"    # 25 @ 11,64: verde · vermelha · pendente
ABERTA = "6add8201bf9e9d000151e59d"     # 25 @ 15,66, aberta
BUILDER = "6add3525bf9e9d0001ae48c4"    # INVENTOR (Bet Builder), 30,01 @ 4,75


def _montar(cru, casa="SPORTSBETIO"):
    f, motivos = ficha.montar_ficha("sbi", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=ANULADA, **campos):
    c = copy.deepcopy(CRUS[cod])
    c.update(campos)
    return c


def test_familia_registrada_e_fixture_inteira():
    assert ADAPTADORES["sbi"] is sbi
    assert len(CRUS) == 31
    aceitas = [c for c, cru in CRUS.items()
               if not any(s.get("marketName") == "Bet Builder" for s in cru["bets"][0]["selections"])]
    assert len(aceitas) == 20             # 13 liquidadas + 7 abertas; os 11 Bet Builders recusam
    for cod in aceitas:
        f, _ = _montar(CRUS[cod])
        assert f["codigo"] == cod and f["moeda"] == "USDT"


def test_codigo_e_o_objectid_do_card():
    assert sbi.codigo(CRUS[PERDIDA]) == PERDIDA
    assert CRUS[PERDIDA]["id"].startswith("U3BvcnRzYmV0VGlja2V0c1RpY2tldD")    # base64 da casa


def test_ganha_bate_com_o_card():
    f, d = _montar(CRUS[GANHA])
    assert (f["status"], f["stake"], f["odd"], f["retorno"], f["tipo"]) == ("ganha", "60.01", "1.77", "106.2177", "simples")
    assert d["resultado"] == "W"
    assert f["colocada_em"].startswith("2026-10-24T23:56:51")          # 20:56:51 em São Paulo
    p = f["pernas"][0]
    assert (p["evento"], p["mandante"], p["visitante"]) == ("Dallas Mavericks - San Antonio Spurs", "Dallas Mavericks", "San Antonio Spurs")
    assert (p["mercado_casa"], p["selecao_casa"], p["linha"]) == ("Zaccharie Risacher pontos (inc. prorrogação)", "Menos de 13.5", "13.5")
    assert p["esporte_casa"] == "Basketball" and p["status_perna"] == "ganha"


def test_turbinada_usa_a_odd_do_card():
    f, d = _montar(CRUS[TURBO_W])
    assert (f["odd"], f["retorno"], d["resultado"]) == ("13.15", "328.75", "W")
    assert [p["odd"] for p in f["pernas"]] == ["2.2", "2.29", "2.61"]    # as turbinadas da perna
    f, d = _montar(CRUS[TURBO_L])
    assert (f["odd"], f["status"], d["odd"]) == ("5.83", "perdida", "5,83")


def test_perna_anulada_como_o_card():
    f, d = _montar(CRUS[ANULADA])
    assert [p["status_perna"] for p in f["pernas"]] == ["perdida", "anulada", "perdida"]
    assert (f["status"], f["retorno"], d["resultado"]) == ("perdida", "0", "L")
    f, _ = _montar(CRUS[PERDIDA])
    assert [p["status_perna"] for p in f["pernas"]] == ["ganha", "perdida", "aberta"]
    assert f["pernas"][0]["mercado_casa"] == "1º tempo - Cadiz CF total de escanteios"
    assert f["pernas"][2]["esporte_casa"] == "Basketball"


def test_aberta():
    f, _ = _montar(CRUS[ABERTA])
    assert (f["status"], f["retorno"], f["odd"], f["stake"]) == ("aberta", None, "15.66", "25")


def test_retorno_igual_a_stake_e_anulada():
    f, d = _montar(_clone(wonAmount="2500000000"))
    assert (f["status"], d["resultado"]) == ("anulada", "V")


def test_sem_retorno_e_sem_perna_perdida_recusa():
    c = _clone()
    for s in c["bets"][0]["selections"]:
        s["status"], s["voidFactor"] = "1", 0
    with pytest.raises(Recusa, match="sem perna perdida"):
        sbi.adaptar(c, "SPORTSBETIO")


def test_retorno_que_nao_fecha_recusa():
    with pytest.raises(Recusa, match="sem amostra"):
        sbi.adaptar(_clone(wonAmount="4000000000"), "SPORTSBETIO")


@pytest.mark.parametrize("mexer,motivo", [
    (lambda c: c["bets"][0].update(freeBet=True), "freeBet"),
    (lambda c: c.update(cashout={"id": "x", "instances": [{"amount": "1", "paidAmount": "1"}]}), "cashout"),
    (lambda c: c.update(bets=c["bets"] * 2), "sistema"),
    (lambda c: c.update(currencyCode="BRL"), "escala"),
])
def test_sem_amostra_recusa(mexer, motivo):
    c = _clone()
    mexer(c)
    with pytest.raises(Recusa, match=motivo):
        sbi.adaptar(c, "SPORTSBETIO")
    with pytest.raises(Recusa, match="Bet Builder"):
        sbi.adaptar(CRUS[BUILDER], "SPORTSBETIO")
