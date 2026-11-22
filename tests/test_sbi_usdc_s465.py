"""Sportsbet.io em USDC pela Ficha (s465, E1.1 do plano do marco zero, 22/11/2026).

Os 5 crus de `tests/fixtures/sbi_usdc_s465.json` são TODOS os bilhetes em USDC que a casa mandou
(conta do Jonathan, 20 e 21/11/2026, `captura_crua`), sem campo de identidade do cliente. O
gabarito de cada um é o cru (escala 1e8) conferido contra a linha que a IA gravou para o mesmo
código e a mesma conta (`bilhetes`: `stake_orig`, `odd`, `resultado`), medido só leitura na
s465. A única diferença foi 45,4616 × 45,46: a IA arredondou, a Ficha fica com o número da casa.

Câmbio: USDC = USDT (decisão do Feca, 22/11/2026). `cambio._SIMBOLO` leva USDC a USDT.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. USDC fora de `sbi._MOEDAS_MEDIDAS`                        → test_os_5_reais_batem_com_o_gabarito
  2. escala 1e6 no lugar de 1e8                                → test_os_5_reais_batem_com_o_gabarito
  3. sem `"USDC": "USDT"` no `cambio._SIMBOLO`                  → test_usdc_e_usdt_no_cambio
  4. sem USDC no `_COMPATIVEIS["USDT"]`                         → test_usdc_e_usdt_no_cambio

O QUE NÃO COBRE: o card da casa (os 5 não foram vistos na tela; o gabarito é o cru e a linha da
IA), USDC aberto, anulado ou com cashout (não houve), e a conversão em R$ (`converter_linhas`,
que é a mesma do USDT e tem o gate dela). BRL segue recusado: `test_adaptador_sbi.py`.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import cambio  # noqa: E402
import ficha  # noqa: E402
from adaptadores import sbi  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "sbi_usdc_s465.json"
CRUS = {sbi.codigo(c): c for c in json.loads(_FIX.read_text(encoding="utf-8"))}

# código → (resultado, stake, odd, retorno) do cru a 1e8, e a stake que a IA gravou (stake_orig).
GABARITO = {
    "6b0097340446770001ccef0c": ("L", "27", "3.05", "0", "27.00"),
    "6b00998d04467700019b1812": ("L", "27", "2.64", "0", "27.00"),
    "6b00a129044677000143a295": ("W", "45.4616", "2.1", "95.46936", "45.46"),
    "6b00bdae0446770001e14484": ("W", "33", "1.86", "61.38", "33.00"),
    "6b01733c04467700017899f9": ("L", "27", "1.91", "0", "27.00"),
}


def test_fixture_inteira():
    assert set(CRUS) == set(GABARITO)
    assert {c["currencyCode"] for c in CRUS.values()} == {"USDC"}


def test_os_5_reais_batem_com_o_gabarito():
    for cod, (res, stake, odd, ret, stake_ia) in GABARITO.items():
        f, motivos = ficha.montar_ficha("sbi", CRUS[cod], "SPORTSBETIO")
        assert motivos == [], (cod, motivos)
        d = ficha.derivar(f)
        assert (d["resultado"], f["stake"], f["odd"], f["retorno"]) == (res, stake, odd, ret), cod
        assert f["moeda"] == "USDC"
        # a IA arredonda a 2 casas; o número da casa arredondado é o dela
        assert f"{float(stake):.2f}" == stake_ia, cod


def test_usdc_e_usdt_no_cambio():
    """Conta USDT: USDC cabe, sem alerta e sem trocar a moeda da linha. Conta em real: o USDC
    vira USDT (a cotação do USDT/BRL), nunca R$."""
    assert cambio.moeda_do_cru("USDT", "USDC") is None
    assert cambio.moedas_contraditorias("USDT", ["USDC"]) == []
    assert cambio.mesma_moeda("USDC", "USDT")
    assert cambio.moeda_do_cru("BRL", "USDC") == "USDT"
    assert cambio.moedas_contraditorias("BRL", ["USDC"]) == ["USDC"]
