"""Gate do adaptador `tp` (1win, plataforma `top-parser`), s413.

Os crus são as fixtures da bancada, byte a byte da casa (`extensor/harness/fixtures/1win.*.json`,
recon s413, conta do Feca: 4 múltiplas abertas e 1 perdida, sem dado de pessoa). Os status 2, 3 e
4 não têm amostra: os testes deles clonam a perdida e trocam só o dinheiro, e cada valor
esperado vem da regra da `CASA_1WIN.md §5` (só o dinheiro decide), nunca do que o código produz.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. odd pelo produto das pernas, não o `cf`              → test_odd_e_o_cf_cortado_e_nao_o_produto
  2. aberta com `profitAmount` como retorno              → test_aberta_nao_tem_retorno
  3. ganha sem conferir retorno = stake × cf             → test_status_2_so_e_ganha_quando_o_dinheiro_fecha
  4. anulada pelo rótulo (status 3), não pelo dinheiro   → test_retorno_igual_a_stake_e_anulada_em_qualquer_status
  5. perdida aceita com retorno diferente de zero        → test_perdida_com_retorno_recusa
  6. freebet deixa de recusar                            → test_sem_amostra_recusa
  7. perna pendente vira "perdida" (data errada)         → test_perdida_data_pela_perna_perdida
  8. recusa volta a ler `cru.id` (código vazio)          → test_recusa_grava_o_codigo_de_bet_id
  s419, perna anulada (crus REAIS em `1win.perna_anulada.json`, 344388133 e 344381942):
  9. sem o ramo da perna anulada                         → test_status_2_com_perna_anulada_e_ganha_pelo_dinheiro
 10. produto de TODAS as pernas, não só as ganhas        → idem
 11. perna 3 sem rótulo `anulada`                        → idem
 12. perna fora de 2/3 aceita                            → test_perna_anulada_so_prova_quando_o_dinheiro_fecha
 13. qualquer status de bilhete, não só o 2              → idem
  INÓCUA: tirar a exigência de "pelo menos uma ganha e uma anulada". Sem anulada o produto
  das ganhas é a própria odd do bilhete (ganha cheia, o ramo de cima); só anuladas dá retorno
  = stake (anulada, também de cima). A trava fica por restringir ao formato medido.
  s431, cashout (crus REAIS em `1win.cashout.json`, 5 bilhetes do Feca de 27/10/2026):
 14. sem o ramo do status 4                              → test_status_4_e_cashout_pelo_dinheiro
 15. perna 4 sem rótulo `cashout`                        → idem
 16. cashout aceito com perna fora do 4                  → test_cashout_so_no_formato_medido
 17. cashout aceito com retorno zero                     → idem

O QUE NÃO COBRE: simples, sistema, bônus, freebet, polybet, carteira de bônus e meio retorno
(todos RECUSADOS por falta de amostra, o texto continua levando à IA), e cashout PARCIAL (sem
amostra). Medido na s419: status 2 = ganha (cheia ou com perna anulada), 3 = anulada (retorno =
stake); perna 2 = ganha, 3 = anulada. Na s431: status 4 = cashout, com toda perna em 4.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, tp  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {it["bet"]["id"]: it
        for nome in ("1win.settled.json", "1win.open.json")
        for it in tp.bilhetes_da_resposta(json.loads((_FIX / nome).read_text(encoding="utf-8")))}
PERDIDA = "337819068"


def _montar(cru, casa="1WIN"):
    f, motivos = ficha.montar_ficha("tp", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(status, retorno, cod=PERDIDA):
    c = copy.deepcopy(CRUS[cod])
    c["bet"]["status"], c["bet"]["profitAmount"] = status, retorno
    return c


def test_familia_registrada_e_toda_fixture_monta():
    assert ADAPTADORES["tp"] is tp
    assert len(CRUS) == 5
    for cod, cru in CRUS.items():
        f, _ = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] == "USDT" and f["tipo"] == "multipla"


def test_odd_e_o_cf_cortado_e_nao_o_produto():
    """337817372: pernas 1,79 × 2,75 = 4,9225; a casa mostra e paga 4,92 (25 × 4,92 = 123)."""
    f, d = _montar(CRUS["337817372"])
    assert f["odd"] == "4.92" and f["odd_calculada"] is False
    assert d["odd"] == "4,92"


def test_aberta_nao_tem_retorno():
    """`profitAmount` na aberta é o potencial (25 × 5,73 = 143,25), nunca o retorno."""
    f, d = _montar(CRUS["338019158"])
    assert f["status"] == "aberta" and f["retorno"] is None and f["liquidada_em"] is None
    assert d["resultado"] == ""


def test_perdida_data_pela_perna_perdida():
    """A perdida tem uma perna ainda pendente (início 13/10) e a que perdeu (12/10): a data é a
    da perna perdida, a régua do `data_da_perna_perdida`."""
    f, d = _montar(CRUS[PERDIDA])
    assert [p["status_perna"] for p in f["pernas"]] == ["aberta", "perdida"]
    assert (f["status"], f["retorno"], f["stake"]) == ("perdida", "0", "25")
    assert (d["resultado"], d["odd"], d["data"]) == ("L", "4,87", "12/10/2026")


def test_status_2_so_e_ganha_quando_o_dinheiro_fecha():
    f, d = _montar(_clone(2, 121.75))                     # 25 × 4,87
    assert (f["status"], f["retorno"]) == ("ganha", "121.75")
    assert (d["resultado"], d["odd"]) == ("W", "4,87")
    with pytest.raises(Recusa):                            # cashout ou perna anulada: a conferir
        tp.adaptar(_clone(2, 90), "1WIN")


def test_retorno_igual_a_stake_e_anulada_em_qualquer_status():
    for st in (2, 3, 4):
        f, d = _montar(_clone(st, 25))
        assert (f["status"], d["resultado"]) == ("anulada", "V")
    with pytest.raises(Recusa):                            # rótulo sem dinheiro que prove
        tp.adaptar(_clone(3, 40), "1WIN")


def test_perdida_com_retorno_recusa():
    with pytest.raises(Recusa):
        tp.adaptar(_clone(1, 10), "1WIN")


@pytest.mark.parametrize("mexer", [
    lambda b, s: b.update(freebetAmount=5),
    lambda b, s: b.update(bonusAmount=3.5),
    lambda b, s: b.update(betType="system"),
    lambda b, s: b.update(wallet="bonus"),
    lambda b, s: s[0].update(isHalfReturn=True),
])
def test_sem_amostra_recusa(mexer):
    c = copy.deepcopy(CRUS[PERDIDA])
    mexer(c["bet"], c["selections"])
    with pytest.raises(Recusa):
        tp.adaptar(c, "1WIN")


ANULADA = {it["bet"]["id"]: it for it in tp.bilhetes_da_resposta(
    json.loads((_FIX / "1win.perna_anulada.json").read_text(encoding="utf-8")))}


@pytest.mark.parametrize("cod, retorno, odd, anulada", [
    ("344388133", "38.5", "1,54", 1),     # tênis abandonado: 25 × 1,54 (a outra perna)
    ("344381942", "78.75", "3,15", 1),    # handicap +4 exato (push): 25 × 3,15
])
def test_status_2_com_perna_anulada_e_ganha_pelo_dinheiro(cod, retorno, odd, anulada):
    """s419: as duas ficaram ABERTAS no Sharpen com a casa já tendo pago (117,25 USDT fora da
    Caixa do Feca). A casa paga pelo produto das pernas ganhas; a odd é retorno ÷ stake, nunca
    o `cf` da colocação (3,23 e 6,02), que pagaria o dobro."""
    f, d = _montar(ANULADA[cod])
    assert (f["status"], f["retorno"]) == ("ganha", retorno)
    assert [p["status_perna"] for p in f["pernas"]].count("anulada") == anulada
    assert "ganha" in [p["status_perna"] for p in f["pernas"]]
    assert (d["resultado"], d["odd"]) == ("W", odd)


def test_perna_anulada_so_prova_quando_o_dinheiro_fecha():
    c = copy.deepcopy(ANULADA["344388133"])
    c["bet"]["profitAmount"] = 40                          # não é 25 × 1,54: a conferir
    with pytest.raises(Recusa):
        tp.adaptar(c, "1WIN")
    c = copy.deepcopy(ANULADA["344388133"])
    extra = copy.deepcopy(c["selections"][1])               # ganha + anulada continuam ali:
    extra["status"] = 4                                     # perna de cashout num bilhete 2: recusa
    c["selections"].append(extra)
    with pytest.raises(Recusa):
        tp.adaptar(c, "1WIN")
    c = copy.deepcopy(ANULADA["344388133"])
    c["bet"]["status"] = 4                                 # só o status 2 é ganha, e o 4 exige
    with pytest.raises(Recusa):                            # toda perna em 4
        tp.adaptar(c, "1WIN")


CASHOUT = {it["bet"]["id"]: it for it in tp.bilhetes_da_resposta(
    json.loads((_FIX / "1win.cashout.json").read_text(encoding="utf-8")))}


@pytest.mark.parametrize("cod, retorno, odd", [
    ("361482655", "31.8", "0,795"),       # recebeu menos que a stake: W com odd < 1
    ("362337573", "86.22", "2,1555"),
    ("362339071", "52.5", "1,3125"),
    ("363617382", "43.61", "1,09025"),
    ("363619481", "39.51", "0,98775"),
])
def test_status_4_e_cashout_pelo_dinheiro(cod, retorno, odd):
    """s431: os cinco ficaram ABERTOS no Sharpen com o cashout já recebido (253,64 USDT fora da
    Caixa do Feca). Cashout ≠ stake → W, odd = retorno ÷ stake (`MASTER_RESULTADO §5.6`),
    nunca o `cf` da colocação."""
    f, d = _montar(CASHOUT[cod])
    assert (f["status"], f["retorno"], f["stake"]) == ("cashout", retorno, "40")
    assert {p["status_perna"] for p in f["pernas"]} == {"cashout"}
    assert (d["resultado"], d["odd"]) == ("W", odd)


def test_cashout_so_no_formato_medido():
    cod = "361482655"
    c = copy.deepcopy(CASHOUT[cod])
    c["bet"]["profitAmount"] = 40                          # cashout = stake: V, odd da casa
    f, d = _montar(c)
    assert (d["resultado"], d["odd"]) == ("V", "6,15")
    for mexer in (lambda c: c["selections"][0].update(status=2),
                  lambda c: c["selections"][1].update(status=1),
                  lambda c: c["bet"].update(profitAmount=0)):
        c = copy.deepcopy(CASHOUT[cod])
        mexer(c)
        with pytest.raises(Recusa):
            tp.adaptar(c, "1WIN")


def test_recusa_grava_o_codigo_de_bet_id():
    """A 1win guarda o código em `cru.bet.id`; a Ficha recusada sem ele perde o bilhete."""
    f, motivos = ficha.montar_ficha("tp", _clone(3, 40), "1WIN")
    assert f == {"codigo": PERDIDA, "cru_recusado": True} and motivos
    # cru torto: recusa, com o código vazio, nunca exceção
    f, motivos = ficha.montar_ficha("tp", {"bet": "x"}, "1WIN")
    assert f["codigo"] == "" and motivos
