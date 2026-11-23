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

XMulti liquidada (E1.3, s465), fixture `tests/fixtures/stc_xmulti_s465.json` (10 crus reais de
produção com o gabarito da linha que a IA gravou). Mutações provadas:
  8. odd do bilhete pelo `payoutMultiplier`                     → test_xmulti_liquidada_bate_com_o_gabarito
  9. ganha sem conferir stake × `payoutMultiplier`              → test_xmulti_sem_amostra_recusa[payout]
 10. odd da perna pela cotação ao vivo (`outcome.odds`)         → test_xmulti_pernas_do_cru_real
 11. `voided` da perna comum lido como ganha                    → test_xmulti_pernas_do_cru_real
 12. sem o ramo do payout = stake                               → test_xmulti_anulada_pelo_dinheiro
 13. sem as travas: moeda, cashoutMultiplier, perna única, 2 preços, dedução, providerBet, props
     com resultado, `voidedLost` em ganha, resultado desconhecido → test_xmulti_sem_amostra_recusa
 14. sem a recusa da aberta (`active`)                          → test_xmulti_aberta_segue_recusada
     (o `_betStatus` confirmed ainda recusaria; o teste confere o MOTIVO)
 15. `_betStatus` fora de settled aceito                         → test_xmulti_sem_amostra_recusa
 16. ganha com perna comum perdida aceita (condição da consultoria; a CopaWin teve 6)
                                                                → test_xmulti_sem_amostra_recusa

O QUE NÃO COBRE: aposta comum (`SportBet`) LIQUIDADA (a conta só tinha abertas), cashout com
retorno ≠ stake, cancelada, sistema; `liquidada_em` (fica None). XMulti anulada inteira não tem
amostra real (o teste a monta de um cru real com payout = stake); XMulti fora de USDT e com
cashout seguem recusadas.
"""
import copy
import json
import sys
from decimal import Decimal
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


# ── aliases (s445): o UUID da aberta é o outro código da MESMA aposta ─────────────────────
# Crus reais da conta do Gabriel (`stakecom.xmulti.json`): a XMulti 689207229 estava ABERTA como
# `18295be1-…` (a lista de abertas não traz `iid`) e voltou liquidada com o número.
_XM = json.loads((_FIX / "stakecom.xmulti.json").read_text(encoding="utf-8"))
_XM_LIQ = {stc.codigo(x): {"iid": x["iid"], "bet": x["bet"]} for x in _XM["settled"]}


def test_aliases_da_liquidada_e_o_uuid_da_aberta():
    """Mutação: `aliases` devolvendo [] → a liquidada não acha a aberta e duplica."""
    aberta = _XM["active"]["activeSportsbookXMultiBetList"][0]
    assert stc.aliases(_XM_LIQ["689207229"]) == [aberta["id"]]


def test_aberta_sem_iid_nao_tem_alias():
    """A aberta não sabe o número que vai ter: sem `iid`, nada a adotar (e não levanta)."""
    aberta = _XM["active"]["activeSportsbookXMultiBetList"][0]
    assert stc.aliases({"iid": "", "bet": aberta}) == []
    assert stc.aliases(None) == [] and stc.aliases({}) == []


def test_xmulti_aberta_segue_recusada():
    """A aberta traz a cotação AO VIVO na perna (mudou em 77 de 92 passagens): fica com a IA."""
    aberta = _XM["active"]["activeSportsbookXMultiBetList"][0]
    with pytest.raises(Recusa, match="sem iid"):
        stc.adaptar({"iid": "", "bet": aberta}, "STAKECOM")
    with pytest.raises(Recusa, match="XMulti aberta"):
        stc.adaptar({"iid": "sport:1", "bet": aberta}, "STAKECOM")
    with pytest.raises(Recusa, match="XMulti aberta"):
        stc.adaptar({"iid": "sport:1", "bet": dict(aberta, _betStatus="settled")}, "STAKECOM")


# ── E1.3 (s465): XMulti LIQUIDADA pela Ficha, contra o gabarito de produção ─────────────────
_XML = json.loads((Path(__file__).resolve().parent / "fixtures" / "stc_xmulti_s465.json").read_text(encoding="utf-8"))
XML = _XML["liquidadas"]
# A Ficha segue o MASTER_OUTPUT §4 (perna mais recente, no fuso de Brasília); nestas a IA gravou o
# dia da colocação. Linha já gravada não muda (resolvida congela a data).
_DATA_FICHA = {"696463077": "22/11/2026", "690143821": "12/11/2026", "691278078": "14/11/2026",
               "696459550": "22/11/2026"}
_C = Decimal("0.01")


def _br(v):
    return Decimal(str(v).replace(".", "").replace(",", ".") if "," in str(v) else str(v))


def test_xmulti_fixture_sem_identidade():
    assert len(XML) == 10
    texto = json.dumps(XML, ensure_ascii=False)
    assert '"user"' not in texto and "gfatuch" not in texto.lower()


@pytest.mark.parametrize("cod", sorted(XML))
def test_xmulti_liquidada_bate_com_o_gabarito(cod):
    caso = XML[cod]
    g = caso["gabarito"]
    f, d = _montar(caso["cru"])
    assert (f["tipo"], f["moeda"], f["codigo"]) == ("multipla", "USDT", cod)
    stake, odd, ret = _br(d["stake"]), _br(d["odd"]), Decimal(g["retorno_casa"])
    assert stake == _br(g["stake"]) and d["resultado"] == g["resultado"]
    pago = stake * odd if d["resultado"] == "W" else Decimal(0)
    assert abs(pago - ret) <= _C                                   # a odd gravada fecha o retorno
    if d["resultado"] == "L":
        assert abs(odd - _br(g["odd"])) <= _C                      # L: odd da casa = a da IA
    elif cod != "692098480":
        assert abs(stake * _br(g["odd"]) - ret) <= _C
    assert d["data"] == _DATA_FICHA.get(cod, g["data"])


def test_xmulti_props_anulada_sem_marca_paga_o_multiplicador():
    """692098480: a IA gravou 9,201848977 (0,17 USDT a mais); a casa pagou 70 × 9,19945194."""
    f, d = _montar(XML["692098480"]["cru"])
    assert (d["resultado"], d["odd"], f["retorno"]) == ("W", "9,19945194", "643.9616358")
    assert d["fonte_odd"] == "nenhuma fecha: retorno ÷ stake"


def test_xmulti_pernas_do_cru_real():
    f, _ = _montar(XML["692098480"]["cru"])
    p = f["pernas"]
    assert (p[0]["mercado_casa"], p[0]["selecao_casa"], p[0]["linha"], p[0]["status_perna"]) == \
        ("Artturi Lehkonen points", "over 0.5", "0.5", None)
    assert p[0]["evento"] == "Montreal Canadiens - Colorado Avalanche"
    assert (p[1]["evento"], p[1]["mercado_casa"], p[1]["selecao_casa"]) == \
        ("HC Friburgo-Gotteron - EHC Kloten Flyers", "1x2", "EHC Kloten Flyers")
    assert (p[1]["odd"], p[1]["status_perna"]) == ("4.7", "ganha")   # o preço da aposta, não o ao vivo (1,01)
    f, _ = _montar(XML["696463077"]["cru"])
    assert [x["status_perna"] for x in f["pernas"]] == [None, "anulada", None]
    f, _ = _montar(XML["696459550"]["cru"])
    assert [x["status_perna"] for x in f["pernas"]] == [None, None, None]   # voidedLost não se afirma
    f, _ = _montar(XML["691278078"]["cru"])
    assert "perdida" in [x["status_perna"] for x in f["pernas"]]


def _xm(cod="689759345", **campos):
    c = copy.deepcopy(XML[cod]["cru"])
    c["bet"].update(campos)
    return c


def test_xmulti_anulada_pelo_dinheiro():
    f, d = _montar(_xm(payout=50))
    assert (f["status"], d["resultado"], f["retorno"]) == ("anulada", "V", "50")


def _perna(cod, i, **campos):
    c = copy.deepcopy(XML[cod]["cru"])
    o = c["bet"]["outcomes"][i]
    for k, v in campos.items():
        if k == "_status":
            o["result"] = dict(o.get("result") or {}, _status=v)
        else:
            o[k] = v
    return c


@pytest.mark.parametrize("cru,motivo", [
    (_xm(currency="btc"), "USDT"),
    (_xm(cashoutMultiplier=1.2), "cashoutMultiplier"),
    (_xm(payout=200), "payoutMultiplier"),                    # W que não fecha
    (_xm(payout=30), "payoutMultiplier"),                     # entre 0 e a stake
    (_xm(_betStatus="cancelled"), "_betStatus"),
    (_xm(outcomes=_xm()["bet"]["outcomes"][:1]), "perna sem amostra"),
    (_perna("689759345", 0, prices=_xm()["bet"]["outcomes"][0]["prices"] * 2), "2 preços"),
    (_perna("689759345", 0, deductions=[{"x": 1}]), "dedução"),
    (_perna("689759345", 0, providerBet={"status": "settlePending"}), "providerBet"),
    (_perna("692098480", 0, result={"_status": "won"}), "props da XMulti com resultado"),
    (_perna("689759345", 0, _status="halfWon"), "resultado 'halfWon'"),
    (_perna("689759345", 0, _status="voidedLost"), "resultado 'voidedLost'"),   # só em perdida
    (_perna("689759345", 0, _market={"__typename": "RacingMarket"}), "RacingMarket"),
    (_perna("689759345", 0, _status="lost"), "ganha com perna perdida"),
])
def test_xmulti_sem_amostra_recusa(cru, motivo):
    with pytest.raises(Recusa, match=motivo):
        stc.adaptar(cru, "STAKECOM")


# ── s453: SportBet múltipla com perna anulada (cru real 691299159, conta do Gabriel) ──────
# 1 perna `voided` + 2 `won`: a casa pagou 70 × 4,482 = 313,74 (odd cheia 7,26084). Até aqui o
# adaptador recusava, o texto dizia "a conferir", a aposta ficou ABERTA e a Caixa 313,74 USDT
# abaixo da casa. Mutações: tirar o ramo do `payoutMultiplier` (recusa) e tirar a trava de 2+
# pernas (a simples com multiplicador ≠ odd passa a ganhar).
_ANULADA = json.loads((_FIX / "stakecom.sportbet-perna-anulada.json").read_text(encoding="utf-8"))


def test_s453_multipla_com_perna_anulada_ganha_pelo_dinheiro():
    f, d = _montar(_ANULADA)
    assert stc.codigo(_ANULADA) == "691299159"
    assert (f["status"], f["stake"], f["retorno"], d["resultado"]) == ("ganha", "70", "313.74", "W")
    assert d["odd"] == "4,482"
    assert [p["status_perna"] for p in f["pernas"]] == ["anulada", "ganha", "ganha"]


def test_s453_retorno_fora_do_multiplicador_e_simples_seguem_recusadas():
    c = copy.deepcopy(_ANULADA)
    c["bet"]["payout"] = 300
    with pytest.raises(Recusa, match="sem amostra"):
        stc.adaptar(c, "STAKECOM")
    s = copy.deepcopy(_ANULADA)
    s["bet"]["outcomes"] = s["bet"]["outcomes"][1:2]
    with pytest.raises(Recusa, match="sem amostra"):
        stc.adaptar(s, "STAKECOM")
