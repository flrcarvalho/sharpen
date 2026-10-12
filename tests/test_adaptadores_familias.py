"""Gate dos adaptadores jb (BetBy), shf (Shuffle), tv (Tivo) e vb (Altenar), s409.

Os crus são REAIS (`captura_crua`, 12/10/2026, contas do Feca), reduzidos aos campos que o
adaptador lê, sem nenhum dado de pessoa: `tests/ficha_crus_familias.json`. Cada teste prende
uma leitura que a régua Ficha × IA dos 545 crus mostrou ser a certa, passando pelo
`ficha.derivar` real.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. jb: odd pelo `total_k` (truncado em 3 casas)           → test_jb_odd_e_o_produto_e_nao_o_k_truncado
  2. jb: perna `refund` vale 1,00 também na perdida          → test_jb_perna_devolvida…
  3. jb: perna `refund` com a odd cheia na ganha            → test_jb_perna_devolvida…
  4. jb: ComboBOOST sem o `total_multiplier`                → test_jb_comboboost_multiplica
  5. jb: sistema pelo `k` (soma das linhas ganhas)          → test_jb_sistema_e_a_media_das_linhas
  6. shf: ganha pela odd da colocação, não a liquidada      → test_shf_ganha_com_perna_pushed…
  7. shf: `originalAmount` diferente aceito                 → test_shf_cashout_parcial_e_recusado
  8. tv: ganha pelo `Koef`, não o `WinKoef`                 → test_tv_ganha_com_perna_anulada…
  9. vb: sistema pelo `totalOdds` arredondado               → test_vb_sistema_e_a_media_exata

O QUE NÃO COBRE: sistema GANHO na `derivar` (regra "sistema: odd da casa" mesmo em W, que a
régua mostrou errada contra o `MASTER_RESULTADO §7.1`: está fora destes adaptadores e fica
como pendência), bet builder da Altenar e odd oferecida da Tivo (recusados por falta de
amostra), e qualquer cru de casa que não esteja nas fixtures.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import Recusa, jb, shf, tv, vb  # noqa: E402

CRUS = json.loads((Path(__file__).resolve().parent / "ficha_crus_familias.json")
                  .read_text(encoding="utf-8"))


def _montar(mod, cod, casa="CASA"):
    f = mod.adaptar(CRUS[cod], casa)
    f = dict(f, impressao="x")
    assert ficha.validar(f, casa) == [], ficha.validar(f, casa)
    return f, ficha.derivar(f)


def test_jb_odd_e_o_produto_e_nao_o_k_truncado():
    """`k` 4,367 é 2,12 × 2,06 = 4,3672 truncado; a casa pagou 25 × 4,3672 = 109,18. Pelo `k`,
    25 × 4,367 = 109,175 "fecha" na borda da folga e a odd gravada seria a errada."""
    f, d = _montar(jb, "2718383996802310522")
    assert f["odd"] == "4.3672" and f["odd_calculada"] is True
    assert (d["resultado"], d["odd"]) == ("W", "4,3672")


def test_jb_perna_devolvida_vale_1_na_ganha_e_fica_cheia_na_perdida():
    # ganha com perna refund: 1,8 devolvida, paga 2,02 (`k` 2,02)
    f, d = _montar(jb, "2720423703182713770")
    assert f["odd"] == "2.02" and d["resultado"] == "W"
    # perdida com perna refund: odd ORIGINAL, sem tirar a perna (MASTER_RESULTADO §5.5.1)
    f, d = _montar(jb, "2719374078761902184")
    assert f["odd"] == "5.671" and d["resultado"] == "L"


def test_jb_comboboost_multiplica():
    f, d = _montar(jb, "2717464096248308141")
    assert f["odd"] == "9.0041112" and d["odd"] == "9,0041112"     # 8,575344 × 1,05


def test_jb_sistema_e_a_media_das_linhas():
    """2/3, as três duplas ganhas, 12 por linha: `k` 12,608 é a SOMA; a média é 4,2028."""
    f, d = _montar(jb, "2717463857143615814")
    assert f["tipo"] == "sistema" and f["sistema"] == "2/3"
    assert f["odd"] == "4.2028"


def test_shf_ganha_com_perna_pushed_usa_a_odd_liquidada():
    """Colocação 5,454 (2,7 × 2,02); a perna de 2,02 deu PUSHED e a casa pagou 25 × 2,7."""
    f, d = _montar(shf, "CfqDUmZMEHCsrWs6k6UGK")
    assert f["odd"] == "2.7" and (d["resultado"], d["odd"]) == ("W", "2,7")


def test_shf_cashout_parcial_e_recusado():
    """`originalAmount` 90 e `amount` 59,56: vendeu parte antes, e o valor da venda não está
    no cru. A IA gravou só a parte que sobrou; a Ficha recusa em vez de perder dinheiro."""
    with pytest.raises(Recusa, match="originalAmount"):
        shf.adaptar(CRUS["CfqYSukd8DqCGMcrVfm4x"], "CASA")


def test_tv_ganha_com_perna_anulada_usa_o_winkoef():
    """`Koef` 9,0288 (2,2 × 2,4 × 1,71); a perna de 2,2 anulou e a casa pagou 100 × 4,104."""
    f, d = _montar(tv, "307310722")
    assert f["odd"] == "4.104" and (d["resultado"], d["odd"]) == ("W", "4,104")
    assert f["pernas"][0]["status_perna"] == "anulada"


def test_tv_freebet_e_dinheiro_da_casa():
    t = dict(CRUS["307310722"], TicketType=3)
    assert tv.adaptar(t, "CASA")["stake_freebet"] == "100"
    with pytest.raises(Recusa, match="TicketType"):
        tv.adaptar(dict(t, TicketType=7), "CASA")


def test_vb_sistema_e_a_media_exata():
    """3 x Duplas de 2,4 × 1,8696 × 2,5455: a casa manda 5,12 (média arredondada)."""
    f, _ = _montar(vb, "5504514128")
    assert f["tipo"] == "sistema" and f["odd_calculada"] is True
    assert f["odd"] == "5.1184356"


def test_vb_ganha_que_a_casa_pagou_truncado_fica_com_o_dinheiro():
    """Dupla 3,3334 × 2,2858: `totalOdds` 7,619486 exato, mas a casa pagou 190,48 (25 ×
    7,619486 = 190,487, TRUNCADO). Nenhuma odd fecha no centavo: vale retorno ÷ stake."""
    f, d = _montar(vb, "5508528206")
    assert f["odd"] == "7.619486"
    assert (d["odd"], d["fonte_odd"]) == ("7,6192", "nenhuma fecha: retorno ÷ stake")
