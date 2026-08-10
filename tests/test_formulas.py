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


def test_resumir_win_rate_fracao_hw_hl():
    # Win rate espelha o wrFrac do front (app.js, achado #17): HW=½ vitória,
    # HL=½ derrota, Void FORA do denominador.
    #   W=2, HW=1, L=1, HL=1, V=1
    #   wins(W+HW)=3 · settled(não-V)=5 · hw=1 · hl=1
    #   num = 3 − ½·1 = 2,5 ; den = 5 − ½·1 − ½·1 = 4 → 2,5/4 = 62,5%
    # O bug antigo (HW cheio: wins/settled = 3/5) daria 60,0 → este teste o pega.
    rows = [
        {"stake": "100", "odd": "2,00", "resultado": "W",  "data": "01/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "W",  "data": "02/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "HW", "data": "03/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "L",  "data": "04/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "HL", "data": "05/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "V",  "data": "06/01/2026"},
    ]
    r = R._resumir_apostas(rows)
    assert r["win_rate"] == 62.5
    assert r["win_rate"] != 60.0   # guarda: não é a conta antiga (HW cheio)
    assert r["apostas"] == 6       # settled(5) + V(1)


def test_resumir_win_rate_so_void_zero():
    # Denominador zero (só Void encerrado) → win_rate 0.0, nunca divisão por zero.
    rows = [
        {"stake": "100", "odd": "2,00", "resultado": "V", "data": "01/01/2026"},
        {"stake": "100", "odd": "2,00", "resultado": "V", "data": "02/01/2026"},
    ]
    r = R._resumir_apostas(rows)
    assert r["win_rate"] == 0.0


# ── validar_linhas (fronteira do /salvar) ─────────────────────────────────────
def test_validar_linhas_aceita_validas_e_incompletas():
    rows = [
        {"stake": "100", "odd": "2,00", "resultado": "W", "data": "01/01/2026", "aposta": "ML"},
        # aberta/incompleta (odd e resultado vazios) = OK, NÃO é rejeitada
        {"stake": "50", "odd": "", "resultado": "", "data": "02/01/2026", "aposta": "Gols"},
    ]
    validas, rejeitadas = R.validar_linhas(rows)
    assert len(validas) == 2
    assert rejeitadas == []


def test_validar_linhas_rejeita_malformada():
    rows = [
        {"stake": "100", "odd": "2,00", "resultado": "W", "data": "01/01/2026", "aposta": "ML"},
        {"stake": "abc", "odd": "2,00", "resultado": "W", "data": "03/01/2026", "aposta": "Gols"},   # stake lixo
        {"stake": "100", "odd": "0",    "resultado": "L", "data": "04/01/2026", "aposta": "ML"},     # odd = 0
        {"stake": "100", "odd": "2,00", "resultado": "Z", "data": "05/01/2026", "aposta": "ML"},     # resultado inválido
        {"stake": "100", "odd": "2,00", "resultado": "W", "data": "lixo",       "aposta": "ML"},     # data inválida
    ]
    validas, rejeitadas = R.validar_linhas(rows)
    assert len(validas) == 1
    assert len(rejeitadas) == 4
    assert {r["campo"] for r in rejeitadas} == {"stake", "odd", "resultado", "data"}
    assert rejeitadas[0]["linha"] == 2   # 1-based na lista parseada
    assert all(("erro" in r and "valor" in r and "resumo" in r) for r in rejeitadas)


# ── corrigir_codigos_tsv: correção determinística do ID contra o texto ────────
_A = "859409392033767424"          # ID real A
_B = "856187092232609792"          # ID real B (bem diferente de A)
_TEXTO = f"Bilhete X\nVenceu\n...\nID: {_A}\n\nBilhete Y\nPerdido\n...\nID: {_B}\n"


def _linha_tsv(cod):
    return "\t".join(["20/06/2026", "Futebol", "", "KingPanda", "Ellen [Eu]",
                      "ML", "Time [a v b]", "25,00", "2,33", "W", cod])


def test_corrige_id_exato_mantem():
    out, st = R.corrigir_codigos_tsv(_linha_tsv(_A), _TEXTO)
    assert out.split("\t")[10] == _A
    assert st == {"corrigidos": 0, "incertos": 0}


def test_corrige_id_garbled_snap():
    garb = "859409392033767420"           # 1 dígito off de _A
    out, st = R.corrigir_codigos_tsv(_linha_tsv(garb), _TEXTO)
    assert out.split("\t")[10] == _A       # snapou pro ID real
    assert st == {"corrigidos": 1, "incertos": 0}


def test_corrige_id_truncado_fica_incerto():
    trunc = "8594093920"                   # 10 dígitos → len < 16, não arrisca
    out, st = R.corrigir_codigos_tsv(_linha_tsv(trunc), _TEXTO)
    assert out.split("\t")[10] == trunc    # inalterado (nunca inventa)
    assert st == {"corrigidos": 0, "incertos": 1}


def test_corrige_sem_texto_noop():
    tsv = _linha_tsv("859409392033767420")
    assert R.corrigir_codigos_tsv(tsv, None) == (tsv, {"corrigidos": 0, "incertos": 0})
    assert R.corrigir_codigos_tsv(tsv, "texto sem ids") == (tsv, {"corrigidos": 0, "incertos": 0})


def test_corrige_nao_toca_notas():
    tsv = _linha_tsv("859409392033767420") + "\n=== Nota: confira a odd"
    out, st = R.corrigir_codigos_tsv(tsv, _TEXTO)
    assert out.split("\n")[1] == "=== Nota: confira a odd"   # nota intacta
    assert st["corrigidos"] == 1


def test_corrige_um_para_um():
    # um exato (_A, reivindica) + um garbled perto de _B → snap p/ _B (único livre)
    garb_b = "856187092232609790"          # 1 off de _B
    tsv = _linha_tsv(_A) + "\n" + _linha_tsv(garb_b)
    out, st = R.corrigir_codigos_tsv(tsv, _TEXTO)
    linhas = out.split("\n")
    assert linhas[0].split("\t")[10] == _A
    assert linhas[1].split("\t")[10] == _B
    assert st == {"corrigidos": 1, "incertos": 0}


def test_estado_extracao_exige_resultado_e_odd():
    # resolvida SÓ com resultado canônico E odd utilizável (> 0)
    assert R.estado_extracao("W", "2,04") == "resolvida"
    assert R.estado_extracao("L", "1,75") == "resolvida"
    assert R.estado_extracao("V", "2,00") == "resolvida"
    assert R.estado_extracao("W", "0.7") == "resolvida"   # ponto decimal, cashout parcial
    # sem odd na VITÓRIA → aberta: `calcular_pl` devolve None e a linha some do feed.
    assert R.estado_extracao("W", "") == "aberta"
    assert R.estado_extracao("HW", None) == "aberta"
    # sem resultado → aberta
    assert R.estado_extracao("", "2,00") == "aberta"
    # minúsculo canoniza (não regride o fix do 'v'/'w')
    assert R.estado_extracao("w", "2,0") == "resolvida"


def test_estado_extracao_perda_e_void_nao_exigem_odd():
    """s259 — a odd só é exigida onde o P/L depende dela. Em L/V/HL o P/L está completo
    sem odd (perda = −stake, void = 0), e exigi-la deixava a linha 'aberta' PARA SEMPRE
    no badge âmbar: caso real das 4 múltiplas perdidas da Betfair sem `combinedOdds`.
    O par com `calcular_pl` é o contrato — se um lado mudar, este teste quebra."""
    for res in ("L", "V", "HL"):
        assert R.estado_extracao(res, "") == "resolvida"
        assert R.estado_extracao(res, None) == "resolvida"
        assert R.estado_extracao(res, "0,00") == "resolvida"
        # e o P/L desses casos é calculável sem odd nenhuma — é essa a razão da regra
        assert R.calcular_pl("100", "", res) is not None
    # a recíproca: onde o P/L NÃO fecha sem odd, o estado continua 'aberta'
    for res in ("W", "HW"):
        assert R.calcular_pl("100", "", res) is None
        assert R.estado_extracao(res, "") == "aberta"
