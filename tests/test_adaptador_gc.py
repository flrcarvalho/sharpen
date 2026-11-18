"""Gate do adaptador `gc` (GiroCerto, plataforma própria `girocerto.fun`), s455.

Os crus vêm da fixture `extensor/harness/fixtures/girocerto.bets.json`: a resposta inteira de
`GET /api/esportes/bets` no recon de 15/11/2026 (Chrome do Feca; SHA-256 conferido com o da
aba). 50 simples liquidadas. Os valores esperados vêm do CARD de "Minhas apostas" (rótulo,
cotação, "Valor apostado", "Valor recebido", hora da colocação), nunca do código. O início do
evento o card não mostra: vem do JSON (UTC).

Mutações provadas (aplicadas, teste ao lado vermelho), 15/11/2026:
  1. `retorno` = `payoutCents` (o potencial)                  → test_perdida_bate_com_o_card
  2. odd = `odds` (a reescrita da liquidação)                → test_anulada_e_meias_usam_a_odd_original
  3. código = `id` (UUID)                                     → test_familia_registrada_e_fixture_inteira_monta
  4. `lost` vira perdida sem conferir crédito zero           → test_dinheiro_que_nao_fecha_recusa
  5. `won` vira ganha sem conferir stake × odd               → test_dinheiro_que_nao_fecha_recusa
  6. tolerância de 1 centavo tirada (exato)                   → test_ganha_com_pagamento_cortado_no_centavo
  7. meia derrota sem exigir a perna `half_lost`             → test_dinheiro_que_nao_fecha_recusa
  8. meia vitória vira `ganha` (perna ignorada)              → test_anulada_e_meias_usam_a_odd_original
  9. aberta / rejected / cashout / freebet / múltipla aceitas → test_sem_amostra_recusa

s461 (18/11/2026), múltiplas reais em `girocerto.multiplas.json`: mutações 6 aplicadas, 5
detectadas (perna meia aceita, produto com as anuladas, sem fechar o produto, tipo errado,
múltipla de 1 perna). A que escapa é INÓCUA: sem exigir perna anulada, o produto das ganhas é a
odd cheia, e ganhar por ela é ganhar pela odd da casa.

O QUE NÃO COBRE: aberta, builder, múltipla com meia, cashout e freebet REAIS (a conta do recon não tem nenhum;
os testes usam clone com o campo trocado) e o `liquidada_em` contra a tela (o card não mostra
a hora da liquidação).
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, gc  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {c["code"]: c for c in gc.bilhetes_da_resposta(
    json.loads((_FIX / "girocerto.bets.json").read_text(encoding="utf-8")))}

GANHA = "ZHUUMZ423Z"      # card: GANHOU, 01/11 21:54, Mais de 1.0, 1.5 @2.02, R$ 750,00 → recebido R$ 1.515,00
CORTADA = "HMD2Y7X9E9"    # card: GANHOU, 3.45, R$ 336,08 → recebido R$ 1.159,47 (1.159,476 cortado)
PERDIDA = "QTPTYJD9Z3"    # card: PERDEU, 2.50, R$ 750,00, "Ganho potencial R$ 1.875,00"
ANULADA = "P4YT7HM9MW"    # card: ANULADA, "Cotação 1.76 1.00", R$ 1.500,00 → recebido R$ 1.500,00
MEIA_V = "6M3YQUCREG"     # card: GANHOU, "meio ganha", "Cotação 1.825 1.413", R$ 300 → recebido R$ 423,75
MEIA_D = "GGGT2EW6RZ"     # card: PERDEU, "meio perdida", "Cotação 2.025 1.00", R$ 525 (voltou R$ 262,50)


def _montar(cru):
    f, motivos = ficha.montar_ficha("gc", cru, "GIROCERTO")
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=GANHA, perna=None, **campos):
    c = copy.deepcopy(CRUS[cod])
    c.update(campos)
    if perna:
        c["legs"][0].update(perna)
    return c


def test_familia_registrada_e_fixture_inteira_monta():
    assert ADAPTADORES["gc"] is gc
    assert len(CRUS) == 50
    contagem = {}
    for cod, cru in CRUS.items():
        f, _ = _montar(cru)
        assert f["codigo"] == cod and gc.codigo(cru) == cod
        assert f["moeda"] is None and f["tipo"] == "simples"
        contagem[f["status"]] = contagem.get(f["status"], 0) + 1
    assert contagem == {"ganha": 26, "meio_ganha": 1, "perdida": 14, "meio_perdida": 2, "anulada": 7}


def test_ganha_bate_com_o_card():
    f, d = _montar(CRUS[GANHA])
    assert (f["status"], f["stake"], f["odd"], f["retorno"]) == ("ganha", "750", "2.02", "1515")
    assert (d["resultado"], d["odd"], d["data"]) == ("W", "2,02", "01/11/2026")
    assert f["colocada_em"] == "2026-11-02T00:54:02.590Z"      # card: 01/11, 21:54 (Brasília)
    p = f["pernas"][0]
    assert (p["evento"], p["mercado_casa"], p["selecao_casa"], p["status_perna"], p["esporte_casa"]) == \
        ("Olancho FC x CD Platense", "1º tempo - total asiático 1.0, 1.5", "Mais de 1.0, 1.5", "ganha", "football")
    assert p["inicio"] == "2026-11-02T01:30:00.000Z"           # 01/11 22:30 em Brasília


def test_ganha_com_pagamento_cortado_no_centavo():
    """336,08 × 3,45 = 1.159,476 e a casa pagou 1.159,47: é ganha, não recusa."""
    f, d = _montar(CRUS[CORTADA])
    assert (f["status"], f["stake"], f["odd"], f["retorno"]) == ("ganha", "336.08", "3.45", "1159.47")
    assert d["resultado"] == "W"


def test_perdida_bate_com_o_card():
    f, d = _montar(CRUS[PERDIDA])
    assert (f["status"], f["retorno"], d["resultado"], d["odd"]) == ("perdida", "0", "L", "2,5")
    assert f["pernas"][0]["esporte_casa"] == "basketball"


def test_anulada_e_meias_usam_a_odd_original():
    """A casa reescreve `odds` para 1 (anulada, meia derrota) e para a efetiva (meia vitória)."""
    f, d = _montar(CRUS[ANULADA])
    assert (f["status"], f["odd"], f["retorno"], d["resultado"], d["odd"]) == ("anulada", "1.76", "1500", "V", "1,76")
    f, d = _montar(CRUS[MEIA_V])
    assert (f["status"], f["odd"], f["retorno"], d["resultado"], d["odd"]) == ("meio_ganha", "1.825", "423.75", "HW", "1,825")
    assert f["pernas"][0]["status_perna"] == "meio_ganha"
    f, d = _montar(CRUS[MEIA_D])
    assert (f["status"], f["odd"], f["retorno"], d["resultado"], d["odd"]) == ("meio_perdida", "2.025", "262.5", "HL", "2,025")
    assert f["pernas"][0]["status_perna"] == "meio_perdida"


@pytest.mark.parametrize("cod,campos,perna", [
    (PERDIDA, {"creditedCents": 187500}, None),           # lost com dinheiro (o potencial)
    (GANHA, {"creditedCents": 132000}, None),             # won que não fecha
    (GANHA, {"creditedCents": 75000}, None),              # won devolvendo a stake
    (GANHA, {"creditedCents": 151398}, None),             # 2 centavos abaixo: fora do corte
    (ANULADA, {"creditedCents": 0}, None),                # void sem devolver
    (MEIA_D, {}, {"status": "lost"}),                     # metade sem a perna half_lost
    (MEIA_D, {"creditedCents": 30000}, None),             # half_lost fora do centavo
    (MEIA_V, {}, {"status": "won"}),                      # meia vitória sem a perna
    (GANHA, {}, {"status": "half_won"}),                  # half_won com crédito de vitória cheia
    (GANHA, {"status": "suspensa"}, None),
])
def test_dinheiro_que_nao_fecha_recusa(cod, campos, perna):
    with pytest.raises(Recusa, match="não fecha"):
        gc.adaptar(_clone(cod, perna=perna, **campos), "GIROCERTO")


@pytest.mark.parametrize("campos,perna,motivo", [
    ({"status": "accepted"}, None, "aberta"),
    ({"status": "pending"}, None, "aberta"),
    ({"status": "placing"}, None, "aberta"),
    ({"status": "cashing"}, None, "aberta"),
    ({"status": "voiding"}, None, "aberta"),
    ({"status": "rejected"}, None, "recusou"),
    ({"status": "cashed_out"}, None, "cashout"),
    ({"cashedCents": 50000}, None, "cashout"),
    ({"lastCashout": {"cents": 1}}, None, "cashout"),
    ({"freebet": True}, None, "freebet"),
    ({"kind": "builder"}, None, "kind"),
    ({"kind": "multiple"}, None, "múltipla com 1 perna"),
    ({}, {"status": "zzz"}, "perna"),
    ({"code": ""}, None, "sem code"),
])
def test_sem_amostra_recusa(campos, perna, motivo):
    with pytest.raises(Recusa, match=motivo):
        gc.adaptar(_clone(perna=perna, **campos), "GIROCERTO")


def test_duas_pernas_recusa():
    c = _clone()
    c["legs"] = c["legs"] * 2
    with pytest.raises(Recusa, match="perna"):
        gc.adaptar(c, "GIROCERTO")


# s461: as 2 primeiras múltiplas reais (Gabriel, 16-17/11/2026), crus de produção verbatim.
MULT = {c["code"]: c for c in json.loads((_FIX / "girocerto.multiplas.json").read_text(encoding="utf-8"))}
M_PERD, M_ANUL = "GRSQYRB7FZ", "Q6GEKXMSRV"


def test_multipla_perdida():
    """3 pernas, a de hóquei (Mais de 5.5) perdeu às 15:30 de 17/11; as outras ganharam."""
    f, d = _montar(MULT[M_PERD])
    assert (f["tipo"], f["status"], f["odd"], f["retorno"]) == ("multipla", "perdida", "7.252", "0")
    assert (d["resultado"], d["odd"], d["data"]) == ("L", "7,252", "17/11/2026")
    assert [p["status_perna"] for p in f["pernas"]] == ["perdida", "ganha", "ganha"]


def test_multipla_ganha_com_duas_pernas_anuladas():
    """Crédito R$ 750 sobre R$ 300 = a única perna que valeu (2,5). A odd cheia 14,795 não pagou."""
    f, d = _montar(MULT[M_ANUL])
    assert (f["tipo"], f["status"], f["odd"], f["retorno"]) == ("multipla", "ganha", "14.795", "750")
    assert (d["resultado"], d["odd"], d["data"]) == ("W", "2,5", "17/11/2026")
    assert [p["status_perna"] for p in f["pernas"]] == ["anulada", "ganha", "anulada"]


def _mclone(cod=M_ANUL, pernas=None, **campos):
    c = copy.deepcopy(MULT[cod])
    c.update(campos)
    for i, st in (pernas or {}).items():
        c["legs"][i]["status"] = st
    return c


@pytest.mark.parametrize("campos,pernas,motivo", [
    ({"creditedCents": 76000}, None, "não fecha"),                 # fora do produto das ganhas
    ({}, {0: "won", 2: "won"}, "não fecha"),                       # sem anulada: produto cheio não pagou
    ({}, {0: "half_won"}, "múltipla com perna"),                   # perna meia numa múltipla
    ({}, {0: "open"}, "múltipla com perna"),                       # perna aberta
    ({}, {0: "lost"}, "não fecha"),                                # perna perdida com crédito
    ({"status": "lost"}, None, "não fecha"),                       # lost com crédito
])
def test_multipla_que_nao_fecha_recusa(campos, pernas, motivo):
    with pytest.raises(Recusa, match=motivo):
        gc.adaptar(_mclone(pernas=pernas, **campos), "GIROCERTO")


def test_recusa_grava_o_code_nunca_o_uuid():
    f, motivos = ficha.montar_ficha("gc", _clone(status="rejected"), "GIROCERTO")
    assert motivos and f == {"codigo": GANHA, "cru_recusado": True}
