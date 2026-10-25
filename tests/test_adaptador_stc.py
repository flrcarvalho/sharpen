"""Gate do adaptador `stc` (Stake.com, a Stake INTERNACIONAL, GraphQL), s428.

Os crus vêm das fixtures `extensor/harness/fixtures/stakecom.settled.json` (15 props liquidadas)
e `stakecom.active.json` (3 abertas de Fórmula 1), as respostas da casa às queries da página no
recon de 25/10/2026 (conta do Feca, USDT, `user` trocado por marcador). Cada valor esperado vem
do card de `/pt/my-bets/sports` (abas Ativo e Definido, e o modal da aposta), nunca do código.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. código = o `iid` inteiro, não o número                     → test_codigo_e_o_id_do_modal
  2. odd da props por `potentialMultiplier`                      → INÓCUA na amostra (os dois iguais
                                                                    nas 15); registrada, sem teste
  3. retorno = stake não vira anulada                            → test_retirado_igual_a_stake_e_anulada
  4. ganha sem conferir stake × odd                              → test_retorno_que_nao_fecha_recusa
  5. perna da props simples sem herdar o bilhete                 → test_props_simples_bate_com_o_card
  6. corrida / promoção / cashout parcial deixam de recusar      → test_sem_amostra_recusa
  7. mercado da props sem o jogador na frente                    → test_props_simples_bate_com_o_card

O QUE NÃO COBRE: aposta comum (`SportBet`) LIQUIDADA (a conta só tinha abertas), cashout com
retorno ≠ stake, cancelada, sistema; `liquidada_em` (fica None).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, stc  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {}
for _nome in ("stakecom.settled.json", "stakecom.active.json"):
    for _c in stc.bilhetes_da_resposta(json.loads((_FIX / _nome).read_text(encoding="utf-8"))):
        CRUS[stc.codigo(_c)] = _c

PERDIDA = "676297455"     # Matisse Thybulle acima 2.5 rebotes, 75 @ "2,27", pagamento 0
GANHA = "676299526"       # Collin Sexton acima 0.5 três convertidos, 30 → 44,943819
RETIRADO = "675668548"    # "Retirado": 60,01 → 60,01
MULTIPLA = "674734395"    # "Múltipla de 2 jogos", 80 @ 2,23 → 178,73
ABERTA = "678433549"      # F1, Hamilton primeiro a fazer pit stop, 30 @ 21


def _montar(cru, casa="STAKECOM"):
    f, motivos = ficha.montar_ficha("stc", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=PERDIDA, **campos):
    c = copy.deepcopy(CRUS[cod])
    c["bet"].update(campos)
    return c


def test_familia_registrada_e_fixture_inteira_monta():
    assert ADAPTADORES["stc"] is stc
    assert len(CRUS) == 18
    for cod, cru in CRUS.items():
        f, _ = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] == "USDT"


def test_codigo_e_o_id_do_modal():
    assert CRUS[PERDIDA]["iid"] == "sport:676297455" and stc.codigo(CRUS[PERDIDA]) == "676297455"


def test_props_simples_bate_com_o_card():
    f, d = _montar(CRUS[PERDIDA])
    assert (f["status"], f["stake"], f["odd"], f["retorno"], d["resultado"]) == ("perdida", "75", "2.2716947", "0", "L")
    assert f["colocada_em"].startswith("2026-10-23T15:58:11")        # 12:58 em São Paulo no modal
    p = f["pernas"][0]
    assert (p["mercado_casa"], p["selecao_casa"], p["linha"], p["status_perna"]) == \
        ("Matisse Thybulle rebounds", "over 2.5", "2.5", "perdida")
    assert p["evento"] == "Los Angeles Lakers - Los Angeles Clippers"
    assert (p["mandante"], p["visitante"]) == ("Los Angeles Lakers", "Los Angeles Clippers")
    f, d = _montar(CRUS[GANHA])
    assert (f["status"], f["retorno"], d["resultado"], f["pernas"][0]["status_perna"]) == ("ganha", "44.943819", "W", "ganha")


def test_retirado_igual_a_stake_e_anulada():
    f, d = _montar(CRUS[RETIRADO])
    assert (f["status"], d["resultado"]) == ("anulada", "V")


def test_multipla_de_props():
    f, d = _montar(CRUS[MULTIPLA])
    assert (f["tipo"], f["status"], d["resultado"]) == ("multipla", "ganha", "W")
    assert [p["status_perna"] for p in f["pernas"]] == [None, None]     # a perna da props não diz


def test_aberta_de_formula_1():
    f, _ = _montar(CRUS[ABERTA])
    assert (f["status"], f["odd"], f["stake"], f["retorno"]) == ("aberta", "21", "30", None)
    p = f["pernas"][0]
    assert (p["selecao_casa"], p["status_perna"], p["mandante"]) == ("Hamilton, Lewis", "aberta", None)


def test_retorno_que_nao_fecha_recusa():
    with pytest.raises(Recusa, match="sem amostra"):
        stc.adaptar(_clone(payout=100), "STAKECOM")


@pytest.mark.parametrize("campos,motivo", [
    ({"__typename": "RacingBet"}, "tipo"),
    ({"promotionBet": {"status": "x"}}, "promotionBet"),
    ({"customPrices": [{"customOdds": 3}]}, "customPrices"),
    ({"cashouts": [{"cashoutAmount": 10}]}, "cashouts"),
    ({"status": "cashout", "payout": 90}, "cashout"),
])
def test_sem_amostra_recusa(campos, motivo):
    with pytest.raises(Recusa, match=motivo):
        stc.adaptar(_clone(**campos), "STAKECOM")
