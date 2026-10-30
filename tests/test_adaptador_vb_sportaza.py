"""Gate do adaptador `vb` na Sportaza (11ª casa Altenar, espelho da Vavada), s434.

Os crus são o expandido REAL da conta do Feca (`extensor/harness/fixtures/sportaza.*.json`, recon
de 30/10/2026, Chrome logado, conta em USD), recortado em 6 bilhetes e conferido verbatim por
SHA-256 contra a página. Na Altenar o cru É o bilhete (`_crus(…, "id", true)` no `vb_inject`),
então a fixture entra direto no adaptador. Cada valor esperado vem do CARD da casa (abas Aberto,
Ganhou e Perdido), nunca do que o código produz; a data esperada é a do MASTER (evento em SP).

O que a Sportaza trouxe: o BÔNUS DE ACUMULADA (`bonus`), pago por fora da odd e já DENTRO do
`totalWin` (5589842458: 30 × 8,697344 = 260,92 + 6,92 = 267,84). A Ficha aceita e o W sai de
retorno ÷ stake (8,928), não da "Odds totais" do card (8.69).

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. `bonus` > 0 passa a recusar                   → test_multipla_ganha_com_bonus_de_acumulada
  2. odd de W pela odd da casa, sem o retorno       → test_multipla_ganha_com_bonus_de_acumulada
  3. data pela colocação em vez do evento           → test_perdida_pela_perna_perdida_mais_cedo

O QUE NÃO COBRE: cashout, anulada, sistema, bet builder e o `status 21` que a tela pede (nenhum
na conta). A conversão de USD é do servidor, pela moeda do cadastro, e não passa por aqui.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import vb  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {str(t["id"]): t for nome in ("sportaza.open.json", "sportaza.settled.json")
        for t in vb.bilhetes_da_resposta(json.loads((_FIX / nome).read_text(encoding="utf-8")))}


def _montar(cod):
    f, motivos = ficha.montar_ficha("vb", CRUS[cod], "SPORTAZA")
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def test_os_seis_crus_reais_montam():
    assert len(CRUS) == 6
    for cod in CRUS:
        f, _ = _montar(cod)
        assert f["codigo"] == cod and f["moeda"] == "USD" and f["casa"] == "SPORTAZA"
        assert len(cod) == 10 and cod.isdigit()        # "Identificação" do card


@pytest.mark.parametrize("cod,stake,odd,data", [
    ("5590494619", "75", "1,8334", "30/10/2026"),      # card: 1.83 · $75.00 · ganho $137.50
])
def test_simples_ganha(cod, stake, odd, data):
    f, d = _montar(cod)
    assert (f["status"], f["tipo"], f["retorno"]) == ("ganha", "simples", "137.5")
    assert (d["resultado"], d["stake"], d["odd"], d["data"]) == ("W", stake, odd, data)


def test_simples_perdida():
    f, d = _montar("5590485064")                       # card: 1.83 · $90.00 · PERDIDO
    assert (f["status"], f["retorno"]) == ("perdida", "0")
    assert (d["resultado"], d["stake"], d["odd"], d["data"]) == ("L", "90", "1,8334", "30/10/2026")


def test_multipla_ganha_com_bonus_de_acumulada():
    f, d = _montar("5589842458")                       # card: 8.69 · $30.00 · ganho $267.84
    assert (f["status"], f["tipo"], f["odd"], f["retorno"]) == ("ganha", "multipla", "8.697344", "267.84")
    assert {p["status_perna"] for p in f["pernas"]} == {"ganha"}
    assert (d["resultado"], d["odd"]) == ("W", "8,928")
    # A última perna começa 2026-10-30T02:00Z = 29/10 23:00 em SP.
    assert d["data"] == "29/10/2026"


def test_perdida_pela_perna_perdida_mais_cedo():
    f, d = _montar("5590902372")                       # card: 21.48 · $30.00 · PERDIDO
    assert [p["status_perna"] for p in f["pernas"]] == ["perdida", "perdida", "ganha"]
    assert (d["resultado"], d["odd"]) == ("L", "21,483")
    # Perna perdida mais cedo: 10:18Z de 30/10; a colocação foi 09:50Z do mesmo dia, então a
    # data só separa as duas réguas pelo `fonte_data`.
    assert d["data"] == "30/10/2026" and d["fonte_data"] == "perna perdida mais cedo"


@pytest.mark.parametrize("cod,odd,data", [
    ("5590916289", "10.97184", "31/10/2026"),          # card: 10.97 · potencial $338.12
    ("5588982337", "6.8265", "30/10/2026"),            # card: 6.82 · potencial $210.03
])
def test_aberta_sem_retorno(cod, odd, data):
    f, d = _montar(cod)
    assert f["status"] == "aberta" and f["retorno"] is None and f["odd"] == odd
    assert d["resultado"] == "" and d["data"] == data
