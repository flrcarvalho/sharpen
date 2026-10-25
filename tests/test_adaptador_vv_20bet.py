"""Gate do adaptador `vv` na 20bet (espelho da Vave, plataforma própria `softlabs`), s428.

Os crus são a fixture `extensor/harness/fixtures/20bet.cru.json`, gerada pelo `vv_inject.js` REAL
no sandbox do harness sobre a resposta da casa (`20bet.history.json`, recon de 25/10/2026, conta
do Gabriel aberta no Chrome do Feca, 12 bilhetes em USD, `userId` zerado) e o recorte dos
dicionários `/pt` (`20bet.dicionarios.json`). Cada valor esperado vem do card da casa
(Betting history, `casos/20bet.mjs`), nunca do que o código produz.

O que a 20bet trouxe que a Vave não tinha: ABERTA (status 0, "Pending"), perna DEVOLVIDA (status
de perna 3, "Returned" no card) e BET BUILDER (perna única "BetBuilder", seleções do cupom em
`betBetBuilderLegs`).

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. perna 3 sem nome (fora do `_PERNA`)                      → test_perna_devolvida_como_o_card
  2. perna 0 sem nome                                         → test_aberta_bate_com_o_card
  3. bet builder deixa de recusar                              → test_bet_builder_recusa
  s429 (as ganhas reais, `20bet.ganhas.cru.json`):
  4. sem o ramo da ganha que não fecha com a odd do card       → test_ganha_com_perna_devolvida…
                                                                 e test_ganha_paga_abaixo…
  5. perna perdida também aceita nesse ramo                    → test_ganha_que_nao_fecha_com_perna_perdida_recusa

O QUE NÃO COBRE: ganha que fecha com a odd do card (a régua está em `test_adaptador_vv.py`,
sobre os ganhos reais da Vave), cashout, freebet e sistema. Bet builder segue RECUSADO: a Ficha precisaria
de uma perna por seleção, e a casa só manda texto pronto (o texto leva o bilhete à IA).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import Recusa, vv  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {vv.codigo(c): c for c in vv.bilhetes_da_resposta(
    json.loads((_FIX / "20bet.cru.json").read_text(encoding="utf-8")))}
BUILDERS = {"68724463", "68651558", "68649008"}
TRIPLA = "68651106"        # 25 USD @ 7,36: Lost · Returned · Won no card, bilhete Lost
ABERTA = "68722991"        # 25 USD @ 10,19, Pending, "Win amount" 254,75


def _montar(cru, casa="20BET"):
    f, motivos = ficha.montar_ficha("vv", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def test_toda_fixture_menos_os_builders_monta():
    assert len(CRUS) == 12
    for cod, cru in CRUS.items():
        if cod in BUILDERS:
            continue
        f, d = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] == "USD" and f["casa"] == "20BET"
        assert len(cod) == 8 and cod.isdigit()        # o "#68651106" do card


def test_perna_devolvida_como_o_card():
    f, d = _montar(CRUS[TRIPLA])
    assert [p["status_perna"] for p in f["pernas"]] == ["perdida", "anulada", "ganha"]
    assert (f["status"], f["stake"], f["odd"], f["retorno"]) == ("perdida", "25", "7.36", "0")
    assert d["resultado"] == "L" and d["odd"] == "7,36"
    assert f["colocada_em"].startswith("2026-10-23T22:41:46")      # 19:41 em São Paulo no card
    assert f["pernas"][0]["mercado_casa"] == "Handicap"
    assert f["pernas"][0]["selecao_casa"] == "Club Atletico Ituzaingo (+1)"


def test_aberta_bate_com_o_card():
    f, d = _montar(CRUS[ABERTA])
    assert f["status"] == "aberta" and f["retorno"] is None
    assert (f["stake"], f["odd"]) == ("25", "10.19")
    assert {p["status_perna"] for p in f["pernas"]} == {"aberta"}


@pytest.mark.parametrize("cod", sorted(BUILDERS))
def test_bet_builder_recusa(cod):
    with pytest.raises(Recusa, match="betBetBuilderId"):
        vv.adaptar(CRUS[cod], "20BET")


# s429: as duas ganhas reais da conta do Gabriel (`captura_crua`, 25/10/2026, só leitura) que
# a Ficha recusava e a IA lia diferente a cada captura (o P/L dele mudava a cada exclusão).
GANHAS = {vv.codigo(c): c for c in vv.bilhetes_da_resposta(
    json.loads((_FIX / "20bet.ganhas.cru.json").read_text(encoding="utf-8")))}


def test_ganha_com_perna_devolvida_e_retorno_sobre_stake():
    """68703441: 30 USD @ 7,29 no card, perna 1,71 devolvida, a casa pagou 127,8."""
    f, d = _montar(GANHAS["68703441"])
    assert [p["status_perna"] for p in f["pernas"]] == ["anulada", "ganha", "ganha"]
    assert (f["status"], f["stake"], f["odd"], f["retorno"]) == ("ganha", "30", "7.29", "127.8")
    assert (d["resultado"], d["odd"]) == ("W", "4,26")


def test_ganha_paga_abaixo_da_odd_do_card():
    """68684132: 30 USD @ 11,25 no card, três pernas ganhas, a casa pagou 337,2 (não 337,5)."""
    f, d = _montar(GANHAS["68684132"])
    assert {p["status_perna"] for p in f["pernas"]} == {"ganha"}
    assert (d["resultado"], d["odd"]) == ("W", "11,24")


def test_ganha_que_nao_fecha_com_perna_perdida_recusa():
    """Sem as pernas provarem a vitória, dinheiro que não fecha segue com a IA."""
    c = copy.deepcopy(GANHAS["68703441"])
    c["bet"]["details"][0]["status"] = 1
    with pytest.raises(Recusa, match="sem amostra"):
        vv.adaptar(c, "20BET")
