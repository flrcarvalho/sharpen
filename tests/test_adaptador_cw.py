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

Cashout (s454), 3 reais em `copawin.cashout.json`; mutações provadas: sem conferir
`cashout_value`, sem exigir status E `cashout_used`, cashout virando `ganha`, ramo inteiro
fora (4 de 4 detectadas).

Múltipla e aberta (s465, E1.2): crus REAIS em `tests/fixtures/cw_multipla_s465.json`
(`captura_crua` de produção, 30 dias até 22/11/2026, sem `user_id`), com o gabarito = a linha
que a IA gravou no banco. Backtest D22 completo (fora daqui, só leitura): 321 múltiplas com
gabarito, 309 aceitas com stake, odd, resultado e retorno iguais e 12 recusadas; 345 passagens
de aberta a liquidada, a stake nunca mudou. Mutações provadas (aplicadas, teste vermelho):
  9. a recusa da múltipla que não fecha sai (fallback retorno ÷ stake da Ficha grava)
                                                    → test_multipla_won_que_nao_fecha_recusa
 10. sem a conta stake × total_odds                   → test_multipla_real_bate[718756]
 11. (a conta "produto de TODAS as pernas" escapou: inócua, medida em 144 crus `won`, e saiu
     do código)
 12. sem a conta do produto das NÃO anuladas          → test_multipla_real_bate[725108/819029]
 13. `won` com perna perdida/aberta deixa de recusar  → test_multipla_won_que_nao_fecha_recusa
 14. aberta volta a recusar                           → test_aberta_real_entra_sem_resultado
 15. aberta leva o `actual_return`                    → test_aberta_real_entra_sem_resultado
 16. múltipla `void`/cashout deixa de recusar          → test_multipla_sem_amostra_recusa
 17. tipo da Ficha fica `simples` na múltipla         → test_multipla_real_bate

O QUE NÃO COBRE: boost e meia vitória REAIS (os testes usam clone com o campo trocado),
múltipla `void` ou cashout real (não houve nenhuma em 30 dias), `liquidada_em` contra a tela
(o card não mostra a hora da liquidação). Que a aberta não rebaixa linha resolvida está no
harness de banco (`test_repository_db.py::test_cw_aberta_nao_rebaixa_linha_resolvida`).
"""
import copy
import json
import sys
from decimal import Decimal
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
    ({"type": "system"}, None, "type"),
    ({"type": "multiple"}, None, "múltipla com 1"),
    ({"status": "pending", "stake": "0.00"}, None, "aberta sem stake"),
    ({"status": "cashout"}, None, "cashout"),            # sem cashout_used
    ({"cashout_used": 1}, None, "cashout"),              # status won com cashout_used
    ({}, {"boost_pct": "10"}, "boost"),
    ({}, {"result": "half_won"}, "result"),
])
def test_sem_amostra_recusa(campos, item, motivo):
    with pytest.raises(Recusa, match=motivo):
        cw.adaptar(_clone(GANHA, item=item, **campos), "COPAWIN")


# ── Cashout (s454) ─────────────────────────────────────────────────────────────────────
# Os 3 cashouts reais da conta do Feca (13/11/2026), lidos de `GET /api/bet/my-bets` na aba
# logada e conferidos por SHA-256 contra a resposta da casa. O Feca: "dei 3 cashouts de 200
# pra 180 ... perdi 20 em cada". Antes da s454 os 3 ficavam ABERTOS no banco.
CASHOUTS = {str(c["id"]): c for c in cw.bilhetes_da_resposta(
    json.loads((_FIX / "copawin.cashout.json").read_text(encoding="utf-8")))}


@pytest.mark.parametrize("cod,odd_casa,perna", [
    ("718108", "9", "aberta"),    # Malásia, perna ainda pending depois do cashout
    ("718109", "2.2", "ganha"),   # Caernarfon: a perna GANHOU depois, e o dinheiro é o do cashout
    ("718110", "1.95", "aberta"),
])
def test_cashout_real_vira_w_pelo_dinheiro(cod, odd_casa, perna):
    f, d = _montar(CASHOUTS[cod])
    assert (f["status"], f["stake"], f["retorno"], f["odd"]) == ("cashout", "200", "180", odd_casa)
    assert (d["resultado"], d["odd"]) == ("W", "0,9")      # 180 ÷ 200, MASTER_RESULTADO §5.6
    assert f["pernas"][0]["status_perna"] == perna


def test_cashout_igual_a_stake_vira_v():
    c = copy.deepcopy(CASHOUTS["718109"])
    c.update(actual_return="200.00", cashout_value="200.00")
    f, d = _montar(c)
    assert f["status"] == "cashout" and (d["resultado"], d["odd"]) == ("V", "2,2")


@pytest.mark.parametrize("campos", [
    {"cashout_used": 0},                  # status cashout sem o carimbo de uso
    {"status": "won"},                    # carimbo de uso sem o status
    {"cashout_value": "170.00"},          # o dinheiro não bate com o valor do cashout
    {"cashout_value": None},
    {"actual_return": None},
])
def test_cashout_sem_as_tres_provas_recusa(campos):
    c = copy.deepcopy(CASHOUTS["718108"])
    c.update(campos)
    with pytest.raises(Recusa, match="cashout"):
        cw.adaptar(c, "COPAWIN")


# ── Múltipla e aberta (s465, E1.2): crus reais de produção ─────────────────────────────
MULT = json.loads((Path(__file__).resolve().parent / "fixtures" / "cw_multipla_s465.json")
                  .read_text(encoding="utf-8"))
_C = Decimal("0.01")


def _br(v):
    return Decimal(str(v).replace(".", "").replace(",", "."))


def test_fixture_sem_identidade():
    assert "user_id" not in json.dumps({k: v for k, v in MULT.items() if k != "_origem"})


@pytest.mark.parametrize("cod", sorted(MULT["aceitas"]))
def test_multipla_real_bate(cod):
    """Stake, resultado e DINHEIRO iguais à linha da IA; a odd da Ficha fecha o retorno."""
    caso = MULT["aceitas"][cod]
    f, d = _montar(caso["cru"])
    g = caso["gabarito"]
    assert f["tipo"] == "multipla" and len(f["pernas"]) >= 2
    assert (d["resultado"], _br(d["stake"])) == (g["resultado"], _br(g["stake"]))
    ret, stake, odd = Decimal(f["retorno"]), _br(d["stake"]), _br(d["odd"])
    if d["resultado"] == "W":
        assert abs(stake * odd - ret) <= _C                     # a odd gravada fecha o retorno
        assert abs(stake * _br(g["odd"]) - ret) <= _C           # e paga o mesmo que a da IA
    else:
        assert ret == 0 and odd == _br(g["odd"]) == Decimal(caso["cru"]["total_odds"])


@pytest.mark.parametrize("cod", sorted(MULT["recusadas"]))
def test_multipla_won_que_nao_fecha_recusa(cod):
    """Condição (a) da consultoria: os 12 `won` que nenhuma conta explica recusam no
    adaptador, ANTES da Ficha, cujo `_odd` gravaria `retorno ÷ stake`."""
    with pytest.raises(Recusa, match="não fecha"):
        cw.adaptar(MULT["recusadas"][cod]["cru"], "COPAWIN")


def test_passagem_real_aberta_e_liquidada():
    caso = MULT["passagem"]["739245"]
    fa, da = _montar(caso["aberta"])
    fl, dl = _montar(caso["liquidada"])
    assert (fa["status"], da["resultado"], fa["retorno"]) == ("aberta", "", None)
    assert fa["stake"] == fl["stake"] == "350"
    assert caso["aberta"]["total_odds"] != caso["liquidada"]["total_odds"]   # a perna anulou
    assert dl["resultado"] == "W" and abs(_br(dl["stake"]) * _br(dl["odd"])
                                          - Decimal(fl["retorno"])) <= _C


def test_aberta_real_entra_sem_resultado():
    cru = MULT["aberta_simples"]["836516"]["cru"]
    assert cru["status"] == "pending" and cru["potential_return"] != "0.00"
    f, d = _montar(cru)
    assert (f["status"], f["retorno"], d["resultado"], d["odd"], f["stake"]) ==         ("aberta", None, "", "3,7", "187")


@pytest.mark.parametrize("campos,perna,motivo", [
    ({"status": "void", "actual_return": "500.00"}, None, "não fecha"),
    ({"status": "cashout", "cashout_used": 1}, None, "cashout"),
    ({"cashout_used": 1}, None, "cashout"),
    ({}, {"result": "pending"}, "não fecha"),         # won com perna aberta
    ({}, {"result": "lost"}, "não fecha"),            # won com perna perdida
    ({"status": "lost", "actual_return": "10.00"}, None, "não fecha"),
])
def test_multipla_sem_amostra_recusa(campos, perna, motivo):
    c = copy.deepcopy(MULT["aceitas"]["819029"]["cru"])
    c.update(campos)
    if perna:
        c["items"][0].update(perna)
    with pytest.raises(Recusa, match=motivo):
        cw.adaptar(c, "COPAWIN")
