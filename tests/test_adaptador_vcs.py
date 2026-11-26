"""Gate do adaptador `vcs` (Vem com Sorte, plataforma própria `vemcomsorte.com`), s467.

O cru vem da fixture `extensor/harness/fixtures/vemcomsorte.bet_history.json`: a resposta
inteira de `POST /api/bettor/bet:history` com 120 dias, no recon de 26/11/2026 (Chrome do
Feca; SHA-256 conferido com o da aba). 7 múltiplas de 3 pernas em BRL, R$ 250 cada. Os
valores esperados vêm do CARD do painel "Minhas Apostas" (rótulo, "Valor da aposta", "Saque",
"Odds totais" — truncada em 2 casas — e o resultado de cada perna), nunca do código. O card
não mostra data: a data esperada é a do `event.startTime` em Brasília, pela régua da Ficha.

Mutações provadas (aplicadas no `vcs.py`, teste vermelho), 26/11/2026: 13 aplicadas, 13
detectadas, com o teste que acusa:
  1. sem dividir pelo multiplier (stake 25000)             → test_fixture_inteira_monta
  2. odd do status = `odds` (truncada do card)              → test_fixture_inteira_monta
  3. odd da Ficha = `odds` (truncada do card)               → test_ganha_bate_com_o_card
  4. retorno = possiblePayout                               → test_fixture_inteira_monta
  5. WIN sem exigir toda perna WIN                          → test_sem_amostra_recusa
  6. LOSE sem exigir perna perdida                          → test_sem_amostra_recusa
  7. WIN sem conferir retorno × stake × odd                 → test_sem_amostra_recusa
  8. VOID aceito como anulada                               → test_sem_amostra_recusa
  9. SYSTEM aceito como múltipla                            → test_sem_amostra_recusa
 10. multiplier ausente vira 100                            → test_sem_amostra_recusa
 11. parâmetro fora da seleção (handicap sem a linha)       → test_pernas_com_o_que_o_card_mostra
 12. início em segundos (epoch ms lido como s)              → test_fixture_inteira_monta
 13. código = billingTransactionId                          → test_fixture_inteira_monta

O QUE NÃO COBRE: simples, VOID, CASHOUT, HALF_WIN/HALF_LOSE no bilhete e SYSTEM/FLEXIBLE/
ONE_CUT REAIS (a conta do recon não tem nenhum; os testes usam clone com o campo trocado) e o
`liquidada_em` (`updateTime` não é provadamente a liquidação).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, vcs  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {vcs.codigo(t): t for t in vcs.bilhetes_da_resposta(
    json.loads((_FIX / "vemcomsorte.bet_history.json").read_text(encoding="utf-8")))}

GANHA = "3602620"     # card: VENCEU, Valor R$ 250,00, Saque R$ 1.648,95, Odds 6.59 (Combo Boost +3%)
PERDIDA = "4826593"   # card: Perdeu, Saque R$ 0,00, Odds 7.21; pernas VENCEU/Perdeu/Perdeu
PERD_ABERTA = "3420609"  # card: Perdeu, Odds 6.56; pernas Perdeu/Não resolvida/Perdeu
ABERTA = "5898642"    # card: Não resolvida, Ganho possível R$ 8.138,51, Odds 32.55


def _montar(cru):
    f, motivos = ficha.montar_ficha("vcs", cru, "VEMCOMSORTE")
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _recusa(cru):
    with pytest.raises(Recusa):
        vcs.adaptar(cru, "VEMCOMSORTE")


def test_fixture_inteira_monta():
    assert ADAPTADORES["vcs"] is vcs
    assert sorted(CRUS) == sorted(["5898642", "3420609", "1324669", "8282618", "3602620", "4826593", "5258640"])
    contagem = {}
    for cod, cru in CRUS.items():
        f, d = _montar(cru)
        assert f["codigo"] == cod
        assert f["moeda"] == "BRL" and f["tipo"] == "multipla" and len(f["pernas"]) == 3
        assert f["stake"] == "250" and d["stake"] == "250"          # card: R$ 250,00 (armadilha: centavos)
        contagem[f["status"]] = contagem.get(f["status"], 0) + 1
    assert contagem == {"aberta": 2, "ganha": 1, "perdida": 4}


def test_ganha_bate_com_o_card():
    f, d = _montar(CRUS[GANHA])
    assert f["retorno"] == "1648.95"                                # card: Saque R$ 1.648,95
    assert f["odd"] == "6.595784"                                   # card: 6.59 (truncada)
    assert d["resultado"] == "W" and d["odd"] == "6,595784"         # fecha o retorno no meio centavo
    assert d["data"] == "26/11/2026"                                # perna mais recente 07:00 (Brasília)


def test_perdida_bate_com_o_card():
    f, d = _montar(CRUS[PERDIDA])
    assert f["retorno"] == "0" and d["resultado"] == "L"
    assert d["odd"] == "7,2109"                                     # card: 7.21; o produto seria 7,03
    assert d["data"] == "26/11/2026"
    f2, d2 = _montar(CRUS[PERD_ABERTA])
    assert d2["resultado"] == "L" and d2["odd"] == "6,56303"        # card 6.56; possiblePayout = 6,401
    assert [p["status_perna"] for p in f2["pernas"]] == ["perdida", "aberta", "perdida"]
    # Régua da Ficha: na perdida, a perna perdida mais cedo (Eudald 07:30 do dia 26, Brasília).
    assert d2["data"] == "26/11/2026"
    assert f2["pernas"][0]["inicio"] == "2026-11-26T03:10:00+00:00"   # Noguchi × Hassan, 00:10 em Brasília


def test_aberta_bate_com_o_card():
    f, d = _montar(CRUS[ABERTA])
    assert f["status"] == "aberta" and f["retorno"] is None and f["odd"] == "32.55405"
    assert d["resultado"] == "" and d["odd"] == "32,55405"


def test_pernas_com_o_que_o_card_mostra():
    f, _ = _montar(CRUS[GANHA])
    p0 = f["pernas"][0]
    assert p0["mercado_casa"] == "Asian Handicap Games" and p0["selecao_casa"] == "Aryan Lakshmanan +6.5"
    assert p0["evento"] == "Aryan Lakshmanan vs Dev Javia" and p0["esporte_casa"] == "Tennis"
    assert p0["odd"] == "1.72" and p0["status_perna"] == "ganha"
    fa, _ = _montar(CRUS[ABERTA])
    assert fa["pernas"][0]["selecao_casa"] == "X2"                  # sem parâmetro
    assert fa["pernas"][1]["selecao_casa"] == "Al Baq'a SC 0"       # card: "Al Baq'a SC (0)"


def test_sem_amostra_recusa():
    def clone(cod=GANHA, **campos):
        c = copy.deepcopy(CRUS[cod])
        c.update(campos)
        return c

    for st in ("VOID", "CASHOUT", "HALF_WIN", "HALF_LOSE", "SUSPENSA"):
        _recusa(clone(status=st))
    for tp in ("SYSTEM", "FLEXIBLE", "ONE_CUT", None):
        _recusa(clone(type=tp))
    c = copy.deepcopy(CRUS[GANHA])
    c["outcomes"][0]["status"] = "VOID"
    _recusa(c)                                                      # ganha com perna anulada
    c = copy.deepcopy(CRUS[GANHA])
    c["money"]["payout"] = 150000
    _recusa(c)                                                      # retorno que não fecha
    p = copy.deepcopy(CRUS[PERDIDA])
    for o in p["outcomes"]:
        o["status"] = "WIN"
    _recusa(p)                                                      # LOSE sem perna perdida
    p = copy.deepcopy(CRUS[PERDIDA])
    p["money"]["payout"] = 10000
    _recusa(p)                                                      # LOSE com retorno
    c = copy.deepcopy(CRUS[GANHA])
    del c["money"]["multiplier"]
    _recusa(c)
    c = copy.deepcopy(CRUS[GANHA])
    c["outcomes"][1]["status"] = "PUSH"
    _recusa(c)
    _recusa(clone(initialOdds=None, odds=None))
    _recusa(clone(id=None))


def test_codigo_e_o_id_da_aposta():
    assert vcs.codigo(CRUS[GANHA]) == "3602620" and CRUS[GANHA]["billingTransactionId"] == "2764363861"
    assert vcs.codigo({"id": True}) == "" and vcs.codigo(None) == ""


def test_data_null_e_lista_vazia():
    assert vcs.bilhetes_da_resposta({"data": None, "hasMore": False}) == []
    assert vcs.bilhetes_da_resposta(None) == []

