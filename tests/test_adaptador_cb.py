"""Gate do adaptador `cb` (Cloudbet, plataforma própria, só o sportsbook), s442.

Os crus são montados da fixture da bancada, byte a byte da casa
(`extensor/harness/fixtures/cloudbet.recon.json`, recon de 10/11/2026, conta em USDT: 15 abertas
e 4 perdidas, todas múltiplas de 3, NBA e NFL), pelo `cb.bilhetes_da_resposta`, do mesmo jeito
que o `cb_inject.js` monta. Ganha, simples, cashout e posição com mais de uma aposta não têm
amostra: os testes deles clonam a perdida e trocam só o campo, e cada valor esperado vem da
`CASA_CLOUDBET.md §5` e do card da casa, nunca do código.

Medido antes de ligar: a base tem 283 apostas Cloudbet do Jaao26 (01 a 10/11/2026), por print e
manual, e nenhum cru da casa. Não há par Ficha × IA para comparar: a 1ª captura virada é a
medição (`virada_log`).

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. retorno = returnAmount (sem somar a stake)          → test_ganha_que_fecha
  2. ganha sem conferir stake × price                     → test_win_que_nao_fecha_recusa
  3. anulada pelo rótulo, não pelo dinheiro               → test_lucro_zero_e_anulada
  4. perdida aceita com retorno                           → test_perdida_com_retorno_recusa
  5. odd da lista (`aggregate.odds`) no lugar do `price`  → test_perdidas_batem_com_o_card
  6. código = positionId                                  → test_codigo_e_o_uuid_do_card
  7. Bet Builder sem agrupar por jogo                     → test_bet_builder_agrupa_por_jogo
  8. sentinela 0001-01-01 vira liquidação                 → test_aberta_sem_liquidacao_sentinela
  9. cashout deixa de recusar                             → test_sem_amostra_recusa
 10. WIN com perna PUSH recusa                            → test_win_com_perna_push_e_ganha
 11. início da perna fora do evento                       → test_data_e_o_evento
(11 de 11 detectadas, 10/11/2026.)

O QUE NÃO COBRE: ganha real (só clone), simples avulsa, cashout, freebet, boost, posição com
mais de uma aposta, aposta em moeda que não USDT, Criar Aposta com perna PUSH (sem amostra:
`status_perna` None).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import descricao_ficha  # noqa: E402
import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, cb  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures" / "cloudbet.recon.json"
CRUS = {cb.codigo(c): c for c in cb.bilhetes_da_resposta(json.loads(_FIX.read_text(encoding="utf-8")))}
SGP2 = "225709c2-3e94-467c-9812-37379a7082cf"     # Bet Builder DET×WAS (3,52) + TOR×MEM (1,97), L
SGP1 = "d4789569-da3e-4732-a7e1-995257a42fd1"     # Criar Aposta puro, CHA×CLE, 9,67, L
PARLAY = "0b08efd7-5995-425a-8f7c-cd8c42403bc6"   # 3 jogos, 7,68, L (PENDING, PUSH, LOSS)
ABERTA = "1e7c2017-c4ba-437d-b7a0-304833f85d24"   # parlay 30 USDT @ 6,937


def _montar(cru, casa="CLOUDBET"):
    f, motivos = ficha.montar_ficha("cb", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=PARLAY, **campos):
    c = copy.deepcopy(CRUS[cod])
    c["aposta"].update(campos)
    return c


def _ganha_clone(lucro, push=False):
    c = _clone(state="COMPLETED", result="WIN", returnAmount=lucro)
    for s in c["aposta"]["selections"]:
        s["result"] = "PUSH" if (push and s["result"] == "PUSH") else "WIN"
    return c


def test_familia_registrada_e_toda_fixture_monta():
    assert ADAPTADORES["cb"] is cb
    assert len(CRUS) == 19
    for cod, cru in CRUS.items():
        f, _ = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] == "USDT"


def test_codigo_e_o_uuid_do_card():
    """O card expandido mostra `ID: 225709c2-3e94-…`; o `positionId` é outro valor (hash)."""
    f, _ = _montar(CRUS[SGP2])
    assert f["codigo"] == SGP2
    assert CRUS[SGP2]["posicao"]["positionId"] != SGP2


def test_perdidas_batem_com_o_card():
    """Card: as 4 perdidas, 30 USDT cada; a odd é a da aposta (@ 6.93 no card expandido), não a
    da lista (`aggregate.odds` 0 em três delas)."""
    esperado = {SGP2: "6,934", SGP1: "9,67", PARLAY: "7,68", "c763f002-585d-406a-920e-369d564ee5de": "6,48"}
    for cod, odd in esperado.items():
        f, d = _montar(CRUS[cod])
        assert (f["status"], f["retorno"], f["stake"]) == ("perdida", "0", "30")
        assert (d["resultado"], d["odd"], d["stake"]) == ("L", odd, "30")


def test_bet_builder_agrupa_por_jogo():
    """225709c2: duas seleções do DET×WAS num Criar Aposta (3,52) e uma do TOR×MEM (1,97). Vira
    multipla de 2 pernas, a do Criar Aposta com a odd do grupo; o produto fecha o card (6,934)."""
    f, _ = _montar(CRUS[SGP2])
    assert f["tipo"] == "multipla" and len(f["pernas"]) == 2
    bb, avulsa = f["pernas"]
    assert bb["mercado_casa"] == "Bet Builder"
    assert bb["selecao_casa"] == "Paul Reed Total Assists: Under 2.5; Kyshawn George Total Rebounds: Over 4.5"
    assert (bb["odd"], bb["status_perna"], bb["evento"]) == ("3.52", "perdida", "DET Pistons v WAS Wizards")
    assert (avulsa["mercado_casa"], avulsa["selecao_casa"], avulsa["odd"]) == \
        ("Collin Murray-Boyles Total Points + Assists", "Under 15.5", "1.97")
    assert avulsa["status_perna"] == "anulada"
    # Criar Aposta puro: uma perna só, simples, com a odd do bilhete
    g, _ = _montar(CRUS[SGP1])
    assert g["tipo"] == "simples" and g["pernas"][0]["mercado_casa"] == "Bet Builder"
    assert g["pernas"][0]["odd"] == g["odd"] == "9.67"


def test_parlay_cada_perna_diz_a_sua():
    f, _ = _montar(CRUS[PARLAY])
    assert [p["status_perna"] for p in f["pernas"]] == [None, "anulada", "perdida"]   # PENDING = None
    p = f["pernas"][0]
    assert (p["mercado_casa"], p["selecao_casa"], p["linha"], p["odd"]) == ("Tari Eason Total Rebounds", "Under 5.5", "5.5", "2.1")
    assert (p["esporte_casa"], p["liga_casa"], p["mandante"], p["visitante"]) == ("Basketball", "NBA", "HOU Rockets", "DEN Nuggets")
    assert descricao_ficha.mercado_com_jogador(p) == "{jogador} Total Rebounds"


def test_data_e_o_evento():
    """O início é o `cutoffTime` do evento. Perdida: a perna perdida mais cedo (CHA×CLE, 00:00 UTC
    de 10/11 = 21:00 de 09/11 em São Paulo), o dia do card ("Mon 9 Nov")."""
    f, d = _montar(CRUS[PARLAY])
    assert [p["inicio"] for p in f["pernas"]] == ["2026-11-10T01:30:00Z", "2026-11-10T00:30:00Z", "2026-11-10T00:00:00Z"]
    assert d["data"] == "09/11/2026"
    assert f["colocada_em"] == "2026-11-09T17:53:03.964243Z"


def test_aberta_sem_liquidacao_sentinela():
    """A aberta traz `completeTime: 0001-01-01T00:00:00Z`: data falsa é pior que ausente."""
    assert CRUS[ABERTA]["aposta"]["completeTime"].startswith("0001-")
    f, d = _montar(CRUS[ABERTA])
    assert (f["status"], f["retorno"], f["liquidada_em"]) == ("aberta", None, None)
    assert [p["status_perna"] for p in f["pernas"]] == ["aberta"] * 3
    assert (d["resultado"], d["odd"]) == ("", "6,937")
    # A mesma sentinela numa liquidada (o `ficha.validar` aceitaria 0001-01-01 como instante).
    f2, _ = _montar(_clone(completeTime="0001-01-01T00:00:00Z"))
    assert f2["liquidada_em"] is None


def test_lucro_zero_e_anulada():
    for res in ("WIN", "LOSS", "PUSH"):
        f, d = _montar(_clone(result=res, returnAmount="0"))
        assert (f["status"], d["resultado"]) == ("anulada", "V")


def test_ganha_que_fecha():
    """30 × 7,68 = 230,40; `returnAmount` (lucro) 200,40."""
    f, d = _montar(_ganha_clone("200.4"))
    assert (f["status"], f["retorno"]) == ("ganha", "230.4")
    assert (d["resultado"], d["odd"]) == ("W", "7,68")


def test_win_que_nao_fecha_recusa():
    with pytest.raises(Recusa):
        cb.adaptar(_ganha_clone("200.43"), "CLOUDBET")        # 3 centavos acima


def test_win_com_perna_push_e_ganha():
    """A casa refaz a odd sem a perna anulada (6,934 ÷ 1,97 = 3,52 no card). O retorno manda:
    30 × 2,1 × 1,67 = 105,21, e a planilha leva retorno ÷ stake."""
    f, d = _montar(_ganha_clone("75.21", push=True))
    assert (f["status"], f["retorno"]) == ("ganha", "105.21")
    assert (d["resultado"], d["odd"]) == ("W", "3,507")


def test_perdida_com_retorno_recusa():
    with pytest.raises(Recusa):
        cb.adaptar(_clone(returnAmount="-12.5"), "CLOUDBET")
    with pytest.raises(Recusa):                                # rótulo novo, sem amostra
        cb.adaptar(_clone(result="HALF_WIN", returnAmount="100"), "CLOUDBET")
    with pytest.raises(Recusa):                                # liquidada sem returnAmount
        cb.adaptar(_clone(returnAmount=None), "CLOUDBET")


def test_sem_amostra_recusa():
    with pytest.raises(Recusa):
        cb.adaptar(_clone(isCashoutBet=True), "CLOUDBET")
    c = _clone()
    c["posicao"] = dict(c["posicao"], betCount=2)
    with pytest.raises(Recusa):
        cb.adaptar(c, "CLOUDBET")
    c = _clone()
    c["eventos"] = {}
    with pytest.raises(Recusa):                                # sem o evento não há jogo nem início
        cb.adaptar(c, "CLOUDBET")


def test_recusa_grava_o_codigo():
    f, motivos = ficha.montar_ficha("cb", _clone(isCashoutBet=True), "CLOUDBET")
    assert motivos and f["cru_recusado"] and f["codigo"] == PARLAY
