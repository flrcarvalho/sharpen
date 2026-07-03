"""Golden tests das fórmulas financeiras — o núcleo do dinheiro do Planilhador.

Cobre calcular_pl (W/L/V/HW/HL), o guard de odd ilegível (T1.1), os parsers
numéricos e de data, os validadores de fronteira e o agregado (P/L, turnover, ROI,
win rate, duração). Rede de regressão: qualquer mudança que altere um centavo
destas fórmulas quebra aqui antes de chegar em produção.
"""
import repository as R


# ── calcular_pl: valores por resultado ────────────────────────────────────────
def test_pl_win():
    assert R.calcular_pl("100", "2,5", "W") == 150.0


def test_pl_loss():
    assert R.calcular_pl("100", "2,5", "L") == -100.0


def test_pl_void_zero():
    assert R.calcular_pl("100", "2,5", "V") == 0.0


def test_pl_half_win():
    # (50*2) + 50 - 100 = 50
    assert R.calcular_pl("100", "2,0", "HW") == 50.0


def test_pl_half_loss():
    # 50 - 100 = -50
    assert R.calcular_pl("100", "2,0", "HL") == -50.0


def test_pl_odd_ponto_decimal():
    # odd "75.2606" (ponto = decimal, sem vírgula) não pode virar 752606
    assert R.calcular_pl("10", "75.2606", "W") == round(10 * 75.2606 - 10, 2)


def test_pl_stake_br_milhar():
    # "1.234,50" → 1234.5 (ponto = milhar, vírgula = decimal)
    assert R.calcular_pl("1.234,50", "2,00", "W") == round(1234.5 * 2 - 1234.5, 2)


# ── calcular_pl: resultado inválido / aberto → None ───────────────────────────
def test_pl_aberto_none():
    assert R.calcular_pl("100", "2,5", "") is None


def test_pl_resultado_invalido_none():
    assert R.calcular_pl("100", "2,5", "X") is None


# ── Guard de odd ilegível (T1.1): W/HW NÃO viram −stake ────────────────────────
def test_pl_win_odd_vazia_none():
    assert R.calcular_pl("100", "", "W") is None


def test_pl_win_odd_ilegivel_none():
    assert R.calcular_pl("100", "abc", "W") is None


def test_pl_win_odd_zero_none():
    assert R.calcular_pl("100", "0", "W") is None


def test_pl_halfwin_odd_vazia_none():
    assert R.calcular_pl("100", "", "HW") is None


def test_pl_loss_sem_odd_ok():
    # L não usa odd: continua computando −stake normalmente
    assert R.calcular_pl("100", "", "L") == -100.0


def test_pl_void_sem_odd_ok():
    assert R.calcular_pl("100", "", "V") == 0.0


def test_pl_halfloss_sem_odd_ok():
    assert R.calcular_pl("100", "", "HL") == -50.0


# ── _num / _num_or_none ───────────────────────────────────────────────────────
def test_num_br_milhar():
    assert R._num("1.234,50") == 1234.5


def test_num_virgula_decimal():
    assert R._num("1,81") == 1.81


def test_num_ponto_decimal_sem_virgula():
    assert R._num("75.2606") == 75.2606


def test_num_reticencia_trailing():
    assert R._num("1,83.") == 1.83


def test_num_ilegivel_zero():
    assert R._num("abc") == 0.0


def test_num_none_zero():
    assert R._num(None) == 0.0


def test_num_or_none_ilegivel():
    assert R._num_or_none("abc") is None


def test_num_or_none_vazio():
    assert R._num_or_none("") is None


def test_num_or_none_zero_string():
    assert R._num_or_none("0") == 0.0


# ── _norm_odd (usada na assinatura de dedup) ──────────────────────────────────
def test_norm_odd_arredonda():
    assert R._norm_odd("1,8331168") == "1.83"


def test_norm_odd_ilegivel_passa():
    assert R._norm_odd("abc") == "abc"


# ── _data_iso ─────────────────────────────────────────────────────────────────
def test_data_br_para_iso():
    assert R._data_iso("31/12/2026") == "2026-12-31"


def test_data_iso_passa():
    assert R._data_iso("2026-01-05") == "2026-01-05"


def test_data_br_curta():
    assert R._data_iso("5/1/2026") == "2026-01-05"


def test_data_lixo_none():
    assert R._data_iso("lixo") is None


# ── Validadores de fronteira (T1.2) ───────────────────────────────────────────
def test_resultado_valido():
    assert R.resultado_valido("W")
    assert R.resultado_valido("hw")   # case-insensitive
    assert R.resultado_valido("")     # vazio = aberto
    assert not R.resultado_valido("X")


def test_valor_monetario_valido():
    assert R.valor_monetario_valido("100")
    assert R.valor_monetario_valido("1,5")
    assert R.valor_monetario_valido("")     # vazio permitido
    assert not R.valor_monetario_valido("abc")
    assert not R.valor_monetario_valido("0")
    assert not R.valor_monetario_valido("-5")


def test_data_valida():
    assert R.data_valida("31/12/2026")
    assert R.data_valida("2026-01-05")
    assert R.data_valida("")
    assert not R.data_valida("lixo")


# ── _resumir_apostas (P/L, turnover, ROI, win rate, duração) ──────────────────
def test_resumir_agregado():
    rows = [
        {"stake": "100", "odd": "2,00", "resultado": "W", "data": "01/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "L", "data": "02/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "V", "data": "03/01/2026"},
    ]
    r = R._resumir_apostas(rows)
    assert r["apostas"] == 3
    assert r["pl"] == 0.0            # +100 -100 +0
    assert r["turnover"] == 200.0   # V não entra no turnover
    assert r["roi"] == 0.0
    assert r["win_rate"] == 50.0    # 1 win / 2 settled (V fora)
    assert r["dias_ativos"] == 3
    assert r["duracao_dias"] == 3   # 01→03 inclusive


def test_resumir_exclui_win_com_odd_ilegivel():
    # Uma vitória com odd ilegível é EXCLUÍDA (não vira −stake nem infla métrica).
    rows = [
        {"stake": "100", "odd": "2,00", "resultado": "W", "data": "01/01/2026"},
        {"stake": "50",  "odd": "",     "resultado": "W", "data": "02/01/2026"},
    ]
    r = R._resumir_apostas(rows)
    assert r["apostas"] == 1
    assert r["pl"] == 100.0
    assert r["turnover"] == 100.0


def test_resumir_vazio():
    r = R._resumir_apostas([])
    assert r["apostas"] == 0
    assert r["pl"] == 0.0
    assert r["roi"] == 0.0
    assert r["win_rate"] == 0.0
    assert r["duracao_dias"] == 0
