"""Gate do adaptador `et` (3et, plataforma própria, só o sportsbook), s441.

Os crus são as fixtures da bancada, byte a byte da casa (`extensor/harness/fixtures/3et.*.json`,
recon de 07-08/11/2026, conta do Feca em USD: 13 liquidadas, 12 perdidas e 1 ganha, e 4 abertas,
todas duplas), mais o `moeda_conta` que o `et_inject.js` anexa. Simples, anulada, freebet,
`trueStake` diferente e exchange não têm amostra: os testes deles clonam a perdida e trocam só o
campo, e cada valor esperado vem da `CASA_3ET.md §5` e do card da casa, nunca do código.

Medido antes de ligar: a casa não tinha cru nem bilhete no banco (08/11/2026, conta nova), então
não há par Ficha × IA para comparar. A 1ª captura virada é a medição (`virada_log`).

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. retorno = profit (sem somar a stake)                 → test_ganha_bate_com_o_card
  2. ganha sem conferir stake × odd                       → test_win_que_nao_fecha_recusa
  3. anulada pelo rótulo, não pelo dinheiro               → test_lucro_zero_e_anulada
  4. perdida aceita com retorno                           → test_perdida_com_retorno_recusa
  5-7. freeBetStake / trueStake / isExchange deixam de recusar (uma mutação cada)
                                                          → test_sem_amostra_recusa
  8. código do bilhete trocado pelo da perna               → test_codigo_e_o_do_bilhete
  9. `A at B` sem virar `A vs B` (o `{time}` some)          → test_jogo_at_vira_vs_e_o_time_generaliza
 10. aberta com o andamento da perna como resultado        → test_aberta_embrulhada
 11. período fora do mercado                               → test_periodo_entra_no_mercado
 12. moeda chutada quando o cru não traz                   → test_moeda_vem_do_cru
 13. perna com rótulo fora de Win/Lose/Push aceita         → test_perna_com_rotulo_novo_recusa
(13 de 13 detectadas, 08/11/2026.)

s443, SIMPLES e PUSH reais (conta do Gabriel, `3et.simples.*.json`: 4 simples liquidadas, 2 simples
abertas, uma delas o mesmo 51851882 antes de liquidar, e a dupla 52019175 com perna Push). Antes,
toda simples recusava com "bilhete sem legs" e ia à IA com "Seleções:" vazio. Mutações:
 14. simples volta a recusar (sem montar a perna)          → test_simples_reais_montam_como_o_card
 15. liga da simples aberta lida só do `bet` (o embrulho cai) → test_simples_aberta_liga_do_embrulho
 16. mercado repetido não sai da seleção da aberta         → test_simples_aberta_selecao_como_a_liquidada
 17. Push deixa de ser perna anulada                       → test_push_na_perna_e_anulada

O QUE NÃO COBRE: boost, cashout, sistema, bet builder, meia vitória/derrota, simples anulada (a
conta não tinha nenhum; todo rótulo fora de Win/Lose recusa no bilhete, e fora de Win/Lose/Push na
perna) e a exchange da casa (fora da captura).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import descricao_ficha  # noqa: E402
import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, et  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {et.codigo(c): dict(c, moeda_conta="USD")
        for nome in ("3et.settled.json", "3et.open.json")
        for c in et.bilhetes_da_resposta(json.loads((_FIX / nome).read_text(encoding="utf-8")))}
PERDIDA = "51835571"       # 25 USD @ 9,175
GANHA = "51776597"         # 22 USD @ 6,814, retorno 149,908
ABERTA = "51867098"        # 20 USD @ 9,765


def _montar(cru, casa="3ET"):
    f, motivos = ficha.montar_ficha("et", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=PERDIDA, **campos):
    c = copy.deepcopy(CRUS[cod])
    c.update(campos)
    return c


def test_familia_registrada_e_toda_fixture_monta():
    assert ADAPTADORES["et"] is et
    assert len(CRUS) == 17
    for cod, cru in CRUS.items():
        f, _ = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] == "USD" and f["tipo"] == "multipla"


def test_codigo_e_o_do_bilhete():
    """As pernas têm `betId` de outra série (64M); o código é o do bilhete (51M), plano ou
    embrulhado."""
    assert _montar(CRUS[GANHA])[0]["codigo"] == "51776597"
    assert _montar(CRUS[ABERTA])[0]["codigo"] == "51867098"
    assert et.codigo({"bet": {"betId": 1, "legs": [{"betId": 2}]}}) == "1"


def test_ganha_bate_com_o_card():
    """Card: 22,00 @ 6,814, lucro 127,908 → retorno 149,908. O produto das pernas (6,815) não
    fecha; a odd da planilha é a da casa."""
    f, d = _montar(CRUS[GANHA])
    assert (f["stake"], f["odd"], f["retorno"], f["status"]) == ("22", "6.814", "149.908", "ganha")
    assert (d["resultado"], d["odd"], d["data"]) == ("W", "6,814", "07/11/2026")
    assert [p["status_perna"] for p in f["pernas"]] == ["ganha", "ganha"]


def test_perdida_e_odd_da_casa():
    f, d = _montar(CRUS[PERDIDA])
    assert (f["status"], f["retorno"]) == ("perdida", "0")
    assert (d["resultado"], d["odd"]) == ("L", "9,175")
    # perdida com uma perna ganha: cada perna diz a sua
    f2, _ = _montar(CRUS["51831830"])
    assert [p["status_perna"] for p in f2["pernas"]] == ["ganha", "perdida"]


def test_data_e_a_colocacao_em_sao_paulo():
    """00:06 UTC de 07/11 = 21:06 de 06/11 em São Paulo. A casa não publica o início do evento."""
    f, d = _montar(CRUS["51758258"])
    assert all(p["inicio"] is None for p in f["pernas"])
    assert d["data"] == "06/11/2026"


def test_lucro_zero_e_anulada():
    for res in ("Win", "Lose", "Push"):
        f, d = _montar(_clone(status={"result": res}, profit=0, payout=0))
        assert (f["status"], d["resultado"]) == ("anulada", "V")


def test_win_que_nao_fecha_recusa():
    assert _montar(_clone(status={"result": "Win"}, profit=204.375))[0]["status"] == "ganha"
    with pytest.raises(Recusa):                       # 2 centavos acima: já não fecha
        et.adaptar(_clone(status={"result": "Win"}, profit=204.395), "3ET")


def test_perdida_com_retorno_recusa():
    with pytest.raises(Recusa):
        et.adaptar(_clone(profit=-12.5), "3ET")
    with pytest.raises(Recusa):                       # rótulo novo, sem amostra
        et.adaptar(_clone(status={"result": "Half Win"}, profit=102.19), "3ET")
    with pytest.raises(Recusa):                       # liquidada sem profit
        et.adaptar(_clone(profit=None), "3ET")


@pytest.mark.parametrize("campos", [
    {"freeBetStake": 25},
    {"trueStake": 20},
    {"isExchange": True},
])
def test_sem_amostra_recusa(campos):
    with pytest.raises(Recusa):
        et.adaptar(_clone(**campos), "3ET")


def test_perna_com_rotulo_novo_recusa():
    c = _clone()
    c["legs"][0]["status"] = {"result": "Void"}
    with pytest.raises(Recusa):
        et.adaptar(c, "3ET")


def test_aberta_embrulhada():
    """A aberta vem em `{bet:{…}}`; a perna diz só `finished`/`graded`, que não é resultado."""
    f, d = _montar(CRUS[ABERTA])
    assert (f["status"], f["retorno"], f["liquidada_em"]) == ("aberta", None, None)
    assert [p["status_perna"] for p in f["pernas"]] == ["aberta", "aberta"]
    assert (d["resultado"], d["odd"]) == ("", "9,765")


def test_jogo_at_vira_vs_e_o_time_generaliza():
    """`Wyoming Cowboys at UNLV Rebels` vira `Wyoming Cowboys vs UNLV Rebels`, na ordem da casa,
    e o mercado `Team Points UNLV Rebels` vira a chave `Team Points {time}` de qualquer time."""
    p = _montar(CRUS[ABERTA])[0]["pernas"][0]
    assert p["evento"] == "Wyoming Cowboys vs UNLV Rebels"
    assert p["mandante"] is None and p["visitante"] is None
    assert descricao_ficha.mercado_com_time(p) == "Team Points {time}"
    assert (p["selecao_casa"], p["linha"]) == ("UNDER 22.5", "22.5")
    # jogo com `vs` fica como veio
    q = _montar(CRUS[GANHA])[0]["pernas"][0]
    assert q["evento"] == "FK Taurage Tauras vs Transinvest II"
    assert (q["mercado_casa"], q["selecao_casa"], q["linha"]) == ("AH", "Tauras Erra Taurage -1.5", "-1.5")
    assert q["esporte_casa"] == "Soccer" and q["liga_casa"] == "Lithuania 1 Lyga"


def test_periodo_entra_no_mercado():
    f, _ = _montar(CRUS["51758408"])
    assert f["pernas"][0]["mercado_casa"] == "Moneyline First Half"   # o mercado já diz
    c = _clone()
    c["legs"][0]["periodName"] = "1st Quarter"
    assert _montar(c)[0]["pernas"][0]["mercado_casa"] == "Team Points Kansas State Wildcats (1st Quarter)"


def test_simples_leva_o_resultado_do_bilhete():
    c = _clone(odds=2.98)
    c["legs"] = c["legs"][:1]
    f, d = _montar(c)
    assert f["tipo"] == "simples" and f["pernas"][0]["status_perna"] == "perdida"


def test_moeda_vem_do_cru():
    c = _clone()
    del c["moeda_conta"]
    assert _montar(c)[0]["moeda"] is None                 # ausência, nunca "USD" por palpite


def test_recusa_grava_o_codigo():
    f, motivos = ficha.montar_ficha("et", _clone(freeBetStake=10), "3ET")
    assert motivos and f["cru_recusado"] and f["codigo"] == PERDIDA


# ── s443: simples e Push reais (conta do Gabriel) ─────────────────────────────────────────────
def _crus_simples(nome):
    return {et.codigo(c): dict(c, moeda_conta="USD")
            for c in et.bilhetes_da_resposta(json.loads((_FIX / nome).read_text(encoding="utf-8")))}


SIMPLES_LIQ = _crus_simples("3et.simples.settled.json")
SIMPLES_ABE = _crus_simples("3et.simples.open.json")


@pytest.mark.parametrize("cod,esperado", [
    # (status, resultado, odd, data, esporte, liga, evento, mercado, seleção, linha)
    ("51663167", ("ganha", "W", "3,25", "05/11/2026", "American Football", "US NFL",
                  "Jacksonville Jaguars vs Baltimore Ravens", "Team Points Jacksonville Jaguars",
                  "OVER 29.5", "29.5")),
    ("51666575", ("perdida", "L", "1,94", "05/11/2026", "Basketball", "Euroleague",
                  "Fenerbahce vs Cazoo Baskonia Vitoria Gasteiz", "Kobi Simmons - Assists",
                  "Under (+2.5)", None)),
    ("51851882", ("perdida", "L", "2,19", "07/11/2026", "American Football", "US NFL",
                  "Tampa Bay Buccaneers vs Chicago Bears", "Total Touchdowns", "Over 5.5", "5.5")),
    ("52022943", ("ganha", "W", "3,9", "10/11/2026", "American Football", "NCAA Division I FBS",
                  "Western Michigan Broncos vs Akron Zips", "Team Points Western Michigan Broncos",
                  "OVER 38.5", "38.5")),
])
def test_simples_reais_montam_como_o_card(cod, esperado):
    f, d = _montar(SIMPLES_LIQ[cod])
    assert f["tipo"] == "simples" and len(f["pernas"]) == 1
    p = f["pernas"][0]
    assert (f["status"], d["resultado"], d["odd"], d["data"], p["esporte_casa"], p["liga_casa"],
            p["evento"], p["mercado_casa"], p["selecao_casa"], p["linha"]) == esperado
    assert p["status_perna"] == f["status"]


def test_simples_aberta_liga_do_embrulho():
    """A aberta é plana no `bet`, e a liga vem no EMBRULHO (`competition` fora do `bet`)."""
    f, d = _montar(SIMPLES_ABE["52028388"])
    p = f["pernas"][0]
    assert (f["status"], d["resultado"], d["odd"]) == ("aberta", "", "1,96")
    assert (p["liga_casa"], p["esporte_casa"], p["evento"]) == ("US NBA", "Basketball", "Boston Celtics vs Toronto Raptors")
    assert (p["mercado_casa"], p["selecao_casa"], p["status_perna"]) == ("HDP", "HDP -7.5 (Boston Celtics)", "aberta")
    assert p["inicio"] is None            # o `eventStartDate` do embrulho não vira data


def test_simples_aberta_selecao_como_a_liquidada():
    """O mesmo 51851882: aberto, `runnerName` "Total Touchdowns  (Over 5.5)"; liquidado, "Over 5.5".
    A Ficha da aberta tem de dizer o mesmo que a da liquidada."""
    pa = _montar(SIMPLES_ABE["51851882"])[0]["pernas"][0]
    pl = _montar(SIMPLES_LIQ["51851882"])[0]["pernas"][0]
    assert (pa["selecao_casa"], pa["linha"]) == (pl["selecao_casa"], pl["linha"]) == ("Over 5.5", "5.5")
    assert pa["mercado_casa"] == pl["mercado_casa"] == "Total Touchdowns"


def test_push_na_perna_e_anulada():
    """52019175: DNB empatado (Push) + perna perdida. O bilhete é perdido pelo dinheiro."""
    f, d = _montar(SIMPLES_LIQ["52019175"])
    assert (f["tipo"], f["status"], d["resultado"], d["odd"]) == ("multipla", "perdida", "L", "11,798")
    assert [p["status_perna"] for p in f["pernas"]] == ["anulada", "perdida"]
