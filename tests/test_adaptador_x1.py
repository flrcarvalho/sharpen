"""Gate do adaptador da família 1xBet (`x1`: 1xBet, Megapari, PariPesa, SapphireBet, 1xBit; s409).

Escrito ANTES do 1º cru real chegar ao banco, a partir das fixtures da bancada da extensão
(`extensor/harness/fixtures/*.bethistory.json`: respostas reais da API, 5 casas, 119
bilhetes), lidas pelo `bilhetes_da_resposta` do jeito que o `x1_inject.js` lê a casa. Cada
teste prende uma armadilha que a `CASA_1XBET.md` e o `formatTicket1X` já tinham medido.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. perdida com perna anulada fica com o `Coef` velho        → test_perdida_com_perna_anulada…
  2. status 4 com retorno = stake vira ganha (ou recusa)       → test_anulada_vem_como_ganha…
  3. sistema sem `Coef` usa o produto das pernas               → test_sistema_sem_coef_recusa
  4. aberta leva o `PossibleWinSum` como retorno               → test_aberta_nao_usa_o_potencial
  5. perna de `Coef` 1 sem a marca de anulada                  → test_perdida_com_perna_anulada…
  6. sistema que pagou abaixo da stake vira recusa             → test_sistema_ganho_parcial…

O QUE NÃO COBRE: o resultado de cada perna (`EventResult` é 0 em todas as 329 pernas, vai
vazio), cashout, freebet e bônus (nenhum nas fixtures: o status desconhecido RECUSA), e o
cru real do servidor (a régua roda no dia em que o cru do Gabriel chegar).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import Recusa, adaptador, x1  # noqa: E402

FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CASAS = ["1xbet", "1xbit", "megapari", "paripesa", "sapphirebet"]
BILHETES = {str(t["BetId"]): t for c in CASAS for t in x1.bilhetes_da_resposta(
    json.loads((FIX / f"{c}.bethistory.json").read_text(encoding="utf-8")))}


def _montar(cod, cru=None):
    f = dict(x1.adaptar(cru or BILHETES[cod], "MEGAPARI"), impressao="x")
    assert ficha.validar(f, "MEGAPARI") == [], ficha.validar(f, "MEGAPARI")
    return f, ficha.derivar(f)


def test_familia_registrada():
    assert adaptador("x1") is x1


def test_todas_as_fixtures_viram_ficha_menos_o_sistema_sem_coef():
    recusas = {}
    for cod, t in BILHETES.items():
        try:
            _montar(cod)
        except Recusa as e:
            recusas[cod] = str(e)
    assert len(BILHETES) == 119          # distintos: espelhos repetem BetId
    assert list(recusas) == ["88092600919"] and "sistema sem Coef" in recusas["88092600919"]


def test_perdida_com_perna_anulada_usa_o_produto():
    """16101007: o card diz 8,607956, de ANTES da anulação; a estrutura é 4,5787."""
    f, d = _montar("16101007")
    assert BILHETES["16101007"]["Coef"] == 8.607956
    assert (f["odd"], f["odd_calculada"], d["resultado"], d["odd"]) == ("4.5787", True, "L", "4,5787")
    assert any(p["status_perna"] == "anulada" for p in f["pernas"])


def test_ganha_com_perna_anulada_fica_com_o_coef_que_a_casa_recalculou():
    ganhas = [c for c, t in BILHETES.items() if t["BetStatus"] == 4 and t.get("BetTypeId") == 1
              and any(e["Coef"] == 1 for e in t["Events"]) and t["WinSum"] > t["BetSum"]]
    assert len(ganhas) == 7
    for cod in ganhas:
        f, d = _montar(cod)
        assert f["odd_calculada"] is False and d["resultado"] == "W"
        assert d["fonte_odd"] == "fecha o retorno: odd da casa"


def test_anulada_vem_como_ganha_com_retorno_igual_a_stake():
    """16001193: `BetStatus` 4, apostou 10, recebeu 10. O enum não separa V de W."""
    f, d = _montar("16001193")
    assert (f["status"], f["retorno"], d["resultado"]) == ("anulada", "10", "V")


def test_sistema_ganho_parcial_e_retorno_sobre_stake():
    """SapphireBet 88105563743, sistema com `Coef`: W = retorno ÷ stake (§7.1). E o mesmo
    sistema pagando abaixo da stake continua W, não recusa."""
    f, d = _montar("88105563743")
    assert (f["tipo"], d["resultado"], d["odd"]) == ("sistema", "W", "2,616")
    parcial = dict(BILHETES["88105563743"], WinSum=40)
    f2, d2 = _montar(None, parcial)
    assert (f2["status"], d2["resultado"], d2["odd"]) == ("ganha", "W", "0,6666666667")


def test_sistema_sem_coef_recusa():
    """O sistema perdido vem sem `Coef`; o produto das pernas não é a odd de um sistema."""
    with pytest.raises(Recusa, match="sistema sem Coef"):
        x1.adaptar(BILHETES["88092600919"], "SAPPHIREBET")


def test_aberta_nao_usa_o_potencial():
    abertas = [c for c, t in BILHETES.items() if t["BetStatus"] == 1]
    assert len(abertas) == 14 and all("PossibleWinSum" in BILHETES[c] for c in abertas)
    for cod in abertas:
        f, d = _montar(cod)
        assert (f["retorno"], d["resultado"]) == (None, "")


def test_status_desconhecido_recusa():
    with pytest.raises(Recusa, match="BetStatus 3"):
        x1.adaptar(dict(BILHETES["16001193"], BetStatus=3), "X")
    simples = dict(BILHETES["16001193"], WinSum=4)    # ganha abaixo da stake fora do sistema
    with pytest.raises(Recusa, match="a conferir"):
        x1.adaptar(simples, "X")
