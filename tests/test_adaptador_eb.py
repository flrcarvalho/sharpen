"""Gate do adaptador `eb` (EpicBet, plataforma própria `epicbet.com`, API tRPC), s462.

Os crus vêm das fixtures `extensor/harness/fixtures/epicbet.pending.json` e
`epicbet.settled.json`: as respostas inteiras de `ticket.listWithMatchInfo` no recon de
21/11/2026 (Chrome do Feca; SHA-256 conferido com o da aba; `walletId` trocado por 1). 13
múltiplas de 3 pernas em USDT. Os valores esperados vêm do CARD do painel "My Bets" (rótulo
WON/LOST, "Odds", "Stake", "Payout", o "ID" e o horário de cada perna, em Brasília), nunca do
código.

Mutações provadas (aplicadas no `eb.py`, teste vermelho), 21/11/2026: 12 aplicadas, 12
detectadas. As 10 principais, com o teste que acusa (as outras duas: linha do mercado fora do
`mercado_casa` e bet builder aceito):
  1. código = `bet.id`                                        → test_fixture_inteira_monta
  2. odd = produto das pernas                                 → test_perdida_com_perna_meia_usa_a_odd_do_card
  3. `won` vira ganha sem exigir toda perna `won`             → test_sem_amostra_recusa
  4. `lost` vira perdida sem perna perdida                    → test_sem_amostra_recusa
  5. cashout aceito                                           → test_sem_amostra_recusa
  6. boost aceito                                             → test_sem_amostra_recusa
  7. status desconhecido aceito como perdida                  → test_sem_amostra_recusa
  8. retorno da ganha ausente                                 → test_ganha_bate_com_o_card
  9. perna `pushed` sem mapear                                → test_aberta_com_perna_pushed
 10. moeda ignorada                                           → test_fixture_inteira_monta

O QUE NÃO COBRE: simples, cashout, boost, bet builder, anulada e ganha com perna pushed/meia
REAIS (a conta do recon não tem nenhum; os testes usam clone com o campo trocado) e o
`liquidada_em` (a casa não publica).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, eb  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {}
for _n in ("epicbet.pending.json", "epicbet.settled.json"):
    for _t in eb.bilhetes_da_resposta(json.loads((_FIX / _n).read_text(encoding="utf-8"))):
        CRUS[eb.codigo(_t)] = _t

GANHA = "11"     # card: WON, Odds 7.14, Stake 40, Payout 285.6; pernas até 21/11 09:00
PERDIDA = "10"   # card: LOST, Odds 12.41, Stake 40, Payout 0; pernas 20/11 21:00, 22:00, 23:00
MEIA = "7"       # card: LOST, Odds 5.87 (perna 1 "Half Won" @2.53), Payout 0
ABERTA = "12"    # card: pendente, Odds 6.14 (perna 1 "Pushed" @1.97), Stake 40, Payout 245.6


def _montar(cru):
    f, motivos = ficha.montar_ficha("eb", cru, "EPICBET")
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _recusa(cru):
    with pytest.raises(Recusa):
        eb.adaptar(cru, "EPICBET")


def test_fixture_inteira_monta():
    assert ADAPTADORES["eb"] is eb
    assert sorted(CRUS, key=int) == [str(i) for i in range(1, 14)]
    contagem = {}
    for cod, cru in CRUS.items():
        f, _ = _montar(cru)
        assert f["codigo"] == cod
        assert f["moeda"] == "USDT" and f["tipo"] == "multipla" and len(f["pernas"]) == 3
        contagem[f["status"]] = contagem.get(f["status"], 0) + 1
    assert contagem == {"aberta": 2, "ganha": 2, "perdida": 9}


def test_ganha_bate_com_o_card():
    f, d = _montar(CRUS[GANHA])
    assert f["retorno"] == "285.6" and f["stake"] == "40" and f["odd"] == "7.14"
    assert d["resultado"] == "W" and d["odd"] == "7,14" and d["data"] == "21/11/2026"
    _, d6 = _montar(CRUS["6"])
    assert d6["resultado"] == "W" and d6["odd"] == "8,09"


def test_perdida_bate_com_o_card():
    f, d = _montar(CRUS[PERDIDA])
    assert f["retorno"] == "0" and d["resultado"] == "L" and d["odd"] == "12,41"
    assert d["data"] == "20/11/2026"


def test_perdida_com_perna_meia_usa_a_odd_do_card():
    f, d = _montar(CRUS[MEIA])
    assert d["resultado"] == "L" and d["odd"] == "5,87"
    assert [p["status_perna"] for p in f["pernas"]] == ["meio_ganha", "perdida", "ganha"]
    p0 = f["pernas"][0]
    assert p0["mercado_casa"] == "Goals Handicap 0 - 0.25" and p0["selecao_casa"] == "FC Voluntari +0.25"
    assert p0["evento"] == "Botosani - FC Voluntari" and p0["esporte_casa"] == "Football"
    assert f["pernas"][1]["selecao_casa"] == "Under 164.5"


def test_aberta_com_perna_pushed():
    f, d = _montar(CRUS[ABERTA])
    assert f["status"] == "aberta" and f["retorno"] is None and f["odd"] == "6.14"
    assert f["pernas"][0]["status_perna"] == "anulada"
    assert d["resultado"] == ""


def test_sem_amostra_recusa():
    g = CRUS[GANHA]

    def clone(cod=GANHA, **bet):
        c = copy.deepcopy(CRUS[cod])
        c["bet"].update(bet)
        return c

    _recusa(clone(cashouts=[{"amount": 100}]))
    _recusa(clone(oddsBoost={"factor": 1.1}))
    for st in ("void", "cashed out", "partially_won", "campaign settled", "cancelled"):
        _recusa(clone(status=st))
    c = copy.deepcopy(g)
    c["bet"]["selections"][0]["status"] = "pushed"
    _recusa(c)                                         # ganha com perna pushed: sem amostra
    c = copy.deepcopy(g)
    c["bet"]["selections"][0]["status"] = "half_won"
    _recusa(c)
    p = copy.deepcopy(CRUS[PERDIDA])
    for s in p["bet"]["selections"]:
        s["status"] = "won"
    _recusa(p)                                         # lost sem perna perdida
    c = copy.deepcopy(g)
    c["bet"]["selections"][0]["selectionInfo"]["betBuilderSelectionInfo"] = {"x": 1}
    _recusa(c)
    _recusa(clone(odds=0))
    c = copy.deepcopy(g)
    c["sequence"] = None
    _recusa(c)


def test_codigo_e_o_sequence_nunca_o_bet_id():
    assert eb.codigo(CRUS[GANHA]) == "11" and CRUS[GANHA]["bet"]["id"] == 39939822
    assert eb.codigo({"sequence": True}) == "" and eb.codigo(None) == ""
