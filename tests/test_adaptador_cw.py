"""Gate do adaptador `cw` (CopaWin, plataforma própria `wncopa.com`), s451.

Os crus vêm da fixture `extensor/harness/fixtures/copawin.my-bets.json`: a resposta inteira de
`GET /api/bet/my-bets` no recon de 12/11/2026 (conta do Jaao26, `user_id` trocado por marcador;
SHA-256 conferido com a da aba). 15 simples liquidadas. Os valores esperados vêm do card de
`/my-bets` (data de colocação, stake, rótulo, jogo, RETORNO da ganha), nunca do código; a odd
não aparece no card e é a do JSON, conferida pelo dinheiro.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. `retorno` = `potential_return`                          → test_perdida_nautico_bate_com_o_card
  2. evento lido em Brasília em vez de UTC                    → test_perdida_nautico_bate_com_o_card
  3. `lost` vira perdida sem conferir retorno zero            → test_dinheiro_que_nao_fecha_recusa
  4. `won` vira ganha sem conferir stake × odd                → test_dinheiro_que_nao_fecha_recusa
  5. `void` vira anulada sem conferir retorno = stake         → test_dinheiro_que_nao_fecha_recusa
  6. Odd Turbinada deixa de recusar                           → test_odd_turbinada_recusa
  7. aberta / múltipla / cashout / boost deixam de recusar    → test_sem_amostra_recusa
  8. colocação lida em UTC                                    → test_ganha_bate_com_o_card

O QUE NÃO COBRE: aberta, múltipla, cashout e boost REAIS (a conta, limitada, não tem nenhum;
os testes usam clone com o campo trocado), meia vitória real, `liquidada_em` contra a tela
(o card não mostra a hora da liquidação).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, cw  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {str(c["id"]): c for c in cw.bilhetes_da_resposta(
    json.loads((_FIX / "copawin.my-bets.json").read_text(encoding="utf-8")))}

GANHA = "660730"       # card: Ganha, 07/11/2026 14:43:20, Menos 1.5, APOSTA R$ 825,00, RETORNO R$ 1.815,00
NAUTICO = "660703"     # card: Perdida, 14:41:45, Nautico vs CRB, APOSTA R$ 525,00, "RETORNO" R$ 2.247,00 (potencial)
ANULADA = "660753"     # card: Anulada, 14:44:34, Ind. Rivadavia (DNB, empate 1x1), APOSTA R$ 750,00
TURBINADA = "652529"   # card: Perdida, 08:10:02, Odd Turbinada, 4 seleções de 4 jogos


def _montar(cru):
    f, motivos = ficha.montar_ficha("cw", cru, "COPAWIN")
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=GANHA, item=None, **campos):
    c = copy.deepcopy(CRUS[cod])
    c.update(campos)
    if item:
        c["items"][0].update(item)
    return c


def test_familia_registrada_e_fixture_inteira_monta():
    assert ADAPTADORES["cw"] is cw
    assert len(CRUS) == 15
    aceitas = 0
    for cod, cru in CRUS.items():
        if cod == TURBINADA:
            continue
        f, _ = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] is None and f["tipo"] == "simples"
        aceitas += 1
    assert aceitas == 14


def test_ganha_bate_com_o_card():
    f, d = _montar(CRUS[GANHA])
    assert (f["status"], f["stake"], f["odd"], f["retorno"]) == ("ganha", "825", "2.2", "1815")
    assert (d["resultado"], d["odd"], d["data"]) == ("W", "2,2", "07/11/2026")
    assert f["colocada_em"] == "2026-11-07T14:43:20-03:00"     # o card mostra 14:43:20
    p = f["pernas"][0]
    assert (p["evento"], p["selecao_casa"], p["status_perna"], p["esporte_casa"]) == \
        ("GV San Jose vs Real Oruro", "Menos 1.5", "ganha", "futebol")
    assert p["inicio"] == "2026-11-07T19:00:00Z"


def test_perdida_nautico_bate_com_o_card():
    """O card estampa R$ 2.247,00 de "RETORNO" e a aposta perdeu; o jogo foi 07/11 às 21:30
    em Brasília, e a API manda `2026-11-08 00:30:00` (UTC)."""
    f, d = _montar(CRUS[NAUTICO])
    assert (f["status"], f["retorno"], d["resultado"], d["odd"]) == ("perdida", "0", "L", "4,28")
    assert d["data"] == "07/11/2026"
    assert f["pernas"][0]["evento"] == "Nautico vs CRB"


def test_anulada_draw_no_bet():
    f, d = _montar(CRUS[ANULADA])
    assert (f["status"], f["retorno"], d["resultado"], d["odd"]) == ("anulada", "750", "V", "1,73")


def test_odd_turbinada_recusa():
    with pytest.raises(Recusa, match="Turbinada"):
        cw.adaptar(CRUS[TURBINADA], "COPAWIN")
    # A recusa vale pelo `market_key` sozinho também (sem `leg_statuses`).
    with pytest.raises(Recusa, match="Turbinada"):
        cw.adaptar(_clone(TURBINADA, item={"leg_statuses": None}), "COPAWIN")


@pytest.mark.parametrize("cod,campos,motivo", [
    (NAUTICO, {"actual_return": "2247.00"}, "não fecha"),   # lost com dinheiro
    (GANHA, {"actual_return": "1320.00"}, "não fecha"),      # won que não fecha (meia/boost)
    (GANHA, {"actual_return": "825.00"}, "não fecha"),       # won devolvendo a stake
    (ANULADA, {"actual_return": "0.00"}, "não fecha"),       # void sem devolver
    (GANHA, {"status": "suspensa"}, "não fecha"),
])
def test_dinheiro_que_nao_fecha_recusa(cod, campos, motivo):
    with pytest.raises(Recusa, match=motivo):
        cw.adaptar(_clone(cod, **campos), "COPAWIN")


@pytest.mark.parametrize("campos,item,motivo", [
    ({"status": "pending"}, None, "aberta"),
    ({"status": "active"}, None, "aberta"),
    ({"type": "multiple"}, None, "type"),
    ({"status": "cashout"}, None, "cashout"),
    ({"cashout_used": 1}, None, "cashout"),
    ({}, {"boost_pct": "10"}, "boost"),
    ({}, {"result": "half_won"}, "result"),
])
def test_sem_amostra_recusa(campos, item, motivo):
    with pytest.raises(Recusa, match=motivo):
        cw.adaptar(_clone(GANHA, item=item, **campos), "COPAWIN")
