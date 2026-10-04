"""Gate do P/L com FREEBET (s392, passo 2b) — `MASTER_RESULTADO §5.8` aplicado ao número.

Decisão do Feca (03-04/10/2026): freebet é dinheiro da casa.

    P/L = retorno − (stake − freebet)     em W e L
    V   → 0                               a casa devolve a freebet como crédito
    HW / HL com freebet → None            sem amostra: "a conferir", não liquidar

O que este arquivo cobre:
  • `calcular_pl` contra os três exemplos REAIS da §5.8 (MyStake, Superbet, SportingBet), e a
    REGRESSÃO: sem freebet o P/L é idêntico ao de antes, ao centavo, nos cinco resultados;
  • `dinheiro_real` (o que conta como turnover) e o resumo por conta;
  • a Caixa nas TRÊS pontas que mudam juntas: P/L, "em aberto" e preso no corte — mudar só
    o P/L deixaria a projeção errada pelo valor exato da freebet;
  • a Caixa de conta em USDT: a freebet (gravada em R$) volta à moeda da conta;
  • por leitura do fonte, que cada leitor do banco passa a `stake_freebet` ao `calcular_pl`.

Mutações provadas (04/10/2026), cada uma APLICADA e com teste vermelho:
  1. ignorar a freebet no W/L (`valor − s`)        → test_os_exemplos_reais_da_secao_5_8
  2. tirar o `V → 0`                               → test_void_com_freebet_e_zero
  3. tirar o `HW/HL → None`                        → test_meia_com_freebet_fica_a_conferir
  9. tirar o cashout de freebet inteira abaixo do stake → test_cashout_de_freebet_inteira_abaixo_do_stake_e_zero
  4. aceitar freebet maior que a stake             → test_freebet_invalida_nao_muda_nada
  5. Caixa: `aberto += stake`                      → test_caixa_freebet_aberta_nao_sai_do_saldo
  6. Caixa: `preso_corte += stake`                 → test_caixa_freebet_aberta_no_corte_e_perdida_zera
  7. `_freebet_na_origem` sem dividir pela cotação → test_caixa_usdt_leva_a_freebet_a_moeda_da_conta
  8. turnover pela stake cheia                     → test_resumo_turnover_e_dinheiro_real

O QUE NÃO ESTÁ COBERTO: o cashout de freebet INTEIRA (P/L 0 pela §5.8) chega como W com
`odd = cashout ÷ stake` e é indistinguível de uma vitória — lacuna declarada no
`calcular_pl` e no BACKLOG 4.0a. O banco de verdade fica no `test_repository_db.py` (CI).
"""
import itertools
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import repository as R  # noqa: E402
from repository import calcular_pl, dinheiro_real  # noqa: E402

REPO = (ROOT / "app" / "repository.py").read_text(encoding="utf-8")
MAIN = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


# ── calcular_pl ───────────────────────────────────────────────────────────────

def test_os_exemplos_reais_da_secao_5_8():
    assert calcular_pl("45,00", "29,7667", "L", "45.00") == 0.0          # MyStake 306558902
    assert calcular_pl("200,00", "24,446016", "L", "10.00") == -190.0    # Superbet 890Y-QHQ8VF
    assert calcular_pl("17,00", "1,35", "W", "17.00") == 22.95           # SportingBet 20NWTMBZYW


def test_vitoria_com_freebet_parcial_desconta_so_o_dinheiro_real():
    # 200 apostados, 10 de freebet, ganhou a 2,0: retorno 400, do bolso saíram 190.
    assert calcular_pl("200,00", "2,0", "W", "10.00") == 210.0


def test_cashout_de_freebet_inteira_abaixo_do_stake_e_zero():
    """W com odd < 1 só existe por cashout; numa freebet inteira o valor volta como nova
    freebet (§5.8). O caso real: Jonathan, Superbet 899Z-EBX0V7 (R$ 30 → R$ 23,83)."""
    assert calcular_pl("30,00", "0,79433333333333", "W", "30.00") == 0.0
    # sem freebet, o mesmo cashout é perda parcial de dinheiro real (§5.6), como sempre
    assert calcular_pl("30,00", "0,79433333333333", "W") == -6.17
    # freebet PARCIAL com cashout: a parte real conta, regra de sempre (sem amostra)
    assert calcular_pl("30,00", "0,8", "W", "10.00") == round(24 - 20, 2)
    # vitória de verdade numa freebet inteira continua sendo lucro
    assert calcular_pl("17,00", "1,35", "W", "17.00") == 22.95


def test_void_com_freebet_e_zero():
    assert calcular_pl("45,00", "2,0", "V", "45.00") == 0.0
    assert calcular_pl("200,00", "2,0", "V", "10.00") == 0.0


def test_meia_com_freebet_fica_a_conferir():
    assert calcular_pl("45,00", "2,0", "HW", "45.00") is None
    assert calcular_pl("45,00", "2,0", "HL", "45.00") is None


@pytest.mark.parametrize("res,odd,stake", list(itertools.product(
    ["W", "L", "V", "HW", "HL"], ["1,35", "2,0", "19,88"], ["17,00", "100,00", "1.234,50"])))
def test_sem_freebet_o_pl_e_identico_ao_de_antes(res, odd, stake):
    """A regressão que importa: a base inteira, sem freebet, não pode mudar um centavo.

    O oráculo é o SWITCH da planilha escrito no `MASTER_RESULTADO §8` (a especificação),
    não uma cópia do `calcular_pl`."""
    s = R._num(stake)
    o = R._num(odd)
    antes = round({"W": s * o, "L": 0.0, "V": s, "HW": (s / 2) * o + s / 2,
                   "HL": s / 2}[res] - s, 2)
    for vazio in (None, "", 0, "0", "0.00"):
        assert calcular_pl(stake, odd, res, vazio) == antes
    assert calcular_pl(stake, odd, res) == antes


def test_freebet_invalida_nao_muda_nada():
    """Maior que a stake ou ilegível não é freebet de nada: conta como aposta normal."""
    assert calcular_pl("10,00", "2,0", "L", "45.00") == -10.0
    assert calcular_pl("10,00", "2,0", "L", "abc") == -10.0
    assert calcular_pl("10,00", "2,0", "L", "-5") == -10.0


def test_dinheiro_real():
    assert dinheiro_real("45,00", "45.00") == 0.0
    assert dinheiro_real("200,00", "10.00") == 190.0
    assert dinheiro_real("70,00", None) == 70.0
    assert dinheiro_real("10,00", "45.00") == 10.0      # freebet inválida


def test_resumo_turnover_e_dinheiro_real():
    rows = [
        {"stake": "45,00", "odd": "29,7667", "resultado": "L", "data": "03/10/2026",
         "stake_freebet": "45.00"},
        {"stake": "70,00", "odd": "29,7667", "resultado": "L", "data": "03/10/2026"},
    ]
    r = R._resumir_apostas(rows)
    assert r["pl"] == -70.0
    assert r["turnover"] == 70.0


# ── Caixa ─────────────────────────────────────────────────────────────────────

def _inicial(valor=100.0, data="2026-10-01", abertas=()):
    return {"tipo": "inicial", "data": data, "valor": valor, "abertas_corte": list(abertas)}


def _aposta(id_, stake, res="", fb=None, odd="2,0", data="03/10/2026", **kw):
    d = {"id": id_, "stake": stake, "odd": odd, "resultado": res, "data": data,
         "criado_em": None, "stake_freebet": fb}
    d.update(kw)
    return d


def test_caixa_freebet_perdida_nao_mexe_na_banca():
    """O caso da MyStake: conferência divergia em exatamente R$ 45."""
    out = R._caixa_projetar([_inicial()], [_aposta(1, "45,00", "L", "45.00"),
                                           _aposta(2, "70,00", "L")])
    assert out["banca"] == 30.0                       # 100 − 70; a freebet não sai
    assert out["disponivel"] == 30.0


def test_caixa_freebet_aberta_nao_sai_do_saldo():
    out = R._caixa_projetar([_inicial()], [_aposta(1, "45,00", "", "45.00"),
                                           _aposta(2, "70,00", "")])
    assert out["aberto"] == 70.0
    assert out["disponivel"] == 30.0


def test_caixa_freebet_aberta_no_corte_e_perdida_zera():
    """Aberta no instante do corte, liquidada depois: preso e P/L mudam JUNTOS."""
    out = R._caixa_projetar([_inicial(abertas=[1])], [_aposta(1, "45,00", "L", "45.00")])
    assert out["banca"] == 100.0
    parcial = R._caixa_projetar([_inicial(abertas=[1])],
                                [_aposta(1, "200,00", "L", "10.00", data="30/09/2026")])
    assert parcial["banca"] == 100.0                  # preso 190 + P/L −190


def test_caixa_usdt_leva_a_freebet_a_moeda_da_conta():
    """Conta em USDT: stake 25 USDT (R$ 130 a 5,2), freebet 10 USDT gravada como R$ 52."""
    ap = _aposta(1, "130,00", "", "52.00", stake_orig=25.0, moeda="USDT", cotacao=5.2)
    out = R._caixa_projetar([_inicial(valor=100.0)], [ap], moeda="USDT")
    assert out["aberto"] == 15.0                      # 25 − 10, em USDT


# ── quem lê o banco passa a freebet adiante ───────────────────────────────────

@pytest.mark.parametrize("trecho", [
    'd["pl"] = calcular_pl(d.get("stake"), d.get("odd"), d.get("resultado"),\n'
    '                              d.get("stake_freebet"))',
    'lucro = calcular_pl(r.get("stake"), r.get("odd"), resultado, r.get("stake_freebet"))',
    'lucro = calcular_pl(r.get("stake"), r.get("odd"), resultado,\n'
    '                                    r.get("stake_freebet"))',
    'pl = calcular_pl(r["stake"], r["odd"], r["resultado"], r["stake_freebet"])',
    '"SELECT data, stake, odd, resultado, stake_freebet FROM bilhetes "',
    '"stake_freebet FROM bilhetes "',
    '"cotacao, stake_freebet "',
    '"stake_freebet",\n)',
])
def test_cada_leitor_do_repositorio_passa_a_freebet(trecho):
    assert trecho in REPO.replace("\r\n", "\n")


def test_export_e_resolver_abertas_passam_a_freebet():
    m = MAIN.replace("\r\n", "\n")
    assert 'r.get("stake_freebet"))\n            # Decimal vírgula' in m
    assert 'aberta.get("stake_freebet"))}' in m
