"""Gate da sombra de NÚMEROS (s407).

Critério do Feca: *"A odd tem que ser 100% igual, a stake tem que ser 100% igual, o
resultado tem que ser 100% igual. Se ele entregar uma palavra diferente na descrição,
não importa."* A sombra de números responde: depois dos MESMOS fiscais, o candidato
gravaria os mesmos números que o titular?

Três coisas precisam ser verdade:

  1. **A régua é a do `/salvar`, sem tolerância.** `1,85` = `1.85`, `8,9688` = `8,96880`,
     e `1,85` ≠ `1,86`. Uma régua frouxa aprovaria o candidato que erra o centavo; uma
     régua de string reprovaria o que só mudou a vírgula.
  2. **Ausência e invenção são contadas, nunca comparadas.** Aposta que o candidato não
     devolveu não é "igual" nem "diferente": é falta. Código fora do texto é invenção.
  3. **O candidato passa pelos fiscais REAIS do titular.** O `corrigir_stake_tsv` corrige
     a stake dos dois lados; sem isso a sombra culparia o candidato por um erro que o
     sistema já conserta antes de gravar.

O QUE ESTE GATE **NÃO** COBRE:

  • Não chama a API. O comportamento do candidato é medido em produção, na
    `sombra_numeros`.
  • Não exercita o INSERT (é SQL; vive no harness de banco quando fizer falta).
  • Não prova que a ordem dos fiscais da sombra é a do titular linha a linha: a
    ordem está escrita em `_fiscais_da_sombra` e conferida por leitura. O que o teste
    prova é que a cadeia real roda e corrige.
"""
import sys

sys.path.insert(0, "app")

import main  # noqa: E402
import repository  # noqa: E402
import sombra_numeros as sn  # noqa: E402


_TEXTO = (
    "[Código: AB1]\n"
    "Stake: R$ 10,00\n"
    "Seleções:\n"
    "  • Time A @ 1,85\n\n"
    "[Código: AB2]\n"
    "Stake: R$ 20,00\n"
    "Seleções:\n"
    "  • Time B @ 2,00\n"
)


def _linha(cod, stake, odd, res):
    return f"01/07/2026\tFutebol\t\tBet365\tc1\tML\tTime\t{stake}\t{odd}\t{res}\t{cod}"


def _tsv(*linhas):
    return f"```tsv\n{main._TSV_HEADER}\n" + "\n".join(linhas) + "\n```"


def _cmp(titular, candidato, texto=_TEXTO, **kw):
    """Bruto = final dos dois lados: isola a comparação dos fiscais."""
    return sn.comparar(titular, titular, candidato, candidato, texto, **kw)


# ── 1. a régua ────────────────────────────────────────────────────────────────

def test_virgula_e_ponto_sao_o_mesmo_numero():
    assert sn.norm_numero("1,85") == sn.norm_numero("1.85")
    assert sn.norm_numero("1.234,50") == sn.norm_numero("1234.5")


def test_um_centavo_de_diferenca_e_diferente():
    assert sn.norm_numero("1,85") != sn.norm_numero("1,86")


def test_zero_a_direita_na_odd_de_multipla_nao_conta():
    assert sn.norm_numero("8,9688") == sn.norm_numero("8,96880")


def test_meia_vitoria_nao_e_vitoria_e_aberta_nao_e_vitoria():
    assert sn.norm_resultado("HW") != sn.norm_resultado("W")
    assert sn.norm_resultado("") is None
    assert sn.norm_resultado("") != sn.norm_resultado("W")
    assert sn.norm_resultado(" w ") == "W"


def test_ilegivel_nao_vira_vazio():
    """Lixo vazio = aposta aberta; lixo ilegível = linha que o `/salvar` recusaria.
    Achatar os dois esconderia uma recusa atrás de uma aposta em aberto."""
    assert sn.norm_numero("abc") == "!abc"
    assert sn.norm_resultado("GANHO") == "!GANHO"


def test_comparacao_aponta_o_campo_que_diverge():
    r = _cmp(_tsv(_linha("AB1", "10,00", "1,85", "W"), _linha("AB2", "20,00", "2,00", "")),
             _tsv(_linha("AB1", "10.00", "1,86", "W"), _linha("AB2", "20", "2.0", "W")))
    por = {l["codigo"]: l for l in r["linhas"]}
    assert por["AB1"]["igual_stake"] is True
    assert por["AB1"]["igual_odd"] is False, "1,85 × 1,86 tem de divergir"
    assert por["AB1"]["igual_res"] is True
    assert por["AB2"]["igual_stake"] and por["AB2"]["igual_odd"]
    assert por["AB2"]["igual_res"] is False, "aberta × W tem de divergir"
    assert r["resumo"]["comparadas"] == 2
    assert r["resumo"]["iguais_tres"] == 0


def test_tudo_igual_conta_como_tres_iguais():
    t = _tsv(_linha("AB1", "10,00", "1,85", "W"), _linha("AB2", "20,00", "2,00", ""))
    r = _cmp(t, t)
    assert r["resumo"]["comparadas"] == 2 and r["resumo"]["iguais_tres"] == 2


# ── 2. ausência e invenção ───────────────────────────────────────────────────

def test_aposta_que_o_candidato_nao_devolveu_e_falta_nao_divergencia():
    r = _cmp(_tsv(_linha("AB1", "10,00", "1,85", "W"), _linha("AB2", "20,00", "2,00", "")),
             _tsv(_linha("AB1", "10,00", "1,85", "W")))
    falta = [l for l in r["linhas"] if l["faltou"]]
    assert [l["codigo"] for l in falta] == ["AB2"]
    assert falta[0]["igual_stake"] is None, "falta não é igual nem diferente"
    assert r["resumo"]["comparadas"] == 1 and r["resumo"]["faltou"] == 1


def test_codigo_inventado_pelo_candidato_e_contado():
    r = _cmp(_tsv(_linha("AB1", "10,00", "1,85", "W")),
             _tsv(_linha("ZZ9", "10,00", "1,85", "W")))
    assert r["resumo"]["inventado"] == 1
    assert any(l["inventado"] and l["codigo"] == "ZZ9" for l in r["linhas"])


def test_em_lote_com_imagem_codigo_fora_do_texto_nao_e_inventado():
    """No print o código vem do card, legitimamente fora do texto: o fantasma do
    titular é no-op ali, e a sombra tem de ser também."""
    r = _cmp(_tsv(_linha("AB1", "10,00", "1,85", "W")),
             _tsv(_linha("ZZ9", "10,00", "1,85", "W")), codigo_ocr=True)
    assert r["resumo"]["inventado"] == 0


def test_linha_sem_codigo_e_contada_e_nunca_pareada():
    r = _cmp(_tsv(_linha("", "10,00", "1,85", "W")), _tsv(_linha("", "10,00", "1,85", "W")))
    assert r["resumo"]["comparadas"] == 0
    assert r["resumo"]["sem_chave_titular"] == 1 and r["resumo"]["sem_chave_candidato"] == 1


def test_codigo_repetido_pareia_pela_ordem():
    t = _tsv(_linha("AB1", "10,00", "1,85", "W"), _linha("AB1", "10,00", "3,00", "L"))
    c = _tsv(_linha("AB1", "10,00", "1,85", "W"), _linha("AB1", "10,00", "3,10", "L"))
    r = _cmp(t, c)
    por = {l["ocorrencia"]: l for l in r["linhas"]}
    assert por[1]["igual_odd"] is True and por[2]["igual_odd"] is False


# ── 3. os fiscais reais ──────────────────────────────────────────────────────

def test_stake_errada_no_bruto_e_consertada_pelos_fiscais_dos_dois_lados():
    """O titular e o candidato escrevem a stake do vizinho; o `corrigir_stake_tsv`
    conserta os dois a partir do bloco. A sombra tem de ver: brutos diferentes do
    final, finais iguais entre si."""
    titular_bruto = _tsv(_linha("AB1", "20,00", "1,85", "W"))
    titular_final, _ = repository.corrigir_stake_tsv(titular_bruto, _TEXTO)
    cand_bruto = _tsv(_linha("AB1", "99,00", "1,85", "W"))
    cand_final, repescaria = main._fiscais_da_sombra(cand_bruto, _TEXTO, False, None)

    r = sn.comparar(titular_bruto, titular_final, cand_bruto, cand_final, _TEXTO)
    ab1 = next(l for l in r["linhas"] if l["codigo"] == "AB1")
    assert ab1["stake_tb"] == "20" and ab1["stake_cb"] == "99"
    assert ab1["stake_tf"] == ab1["stake_cf"] == "10", "os dois finais vêm do bloco"
    assert ab1["igual_stake"] is True
    assert repescaria == 1, "AB2 não voltou: a cobertura teria repescado 1"


def test_fiscais_da_sombra_consertam_codigo_inventado_como_no_titular():
    """O `_corrigir_codigos_fantasma` troca o código inventado pelo do bloco de que a
    linha é fiel. Sem ele na cadeia, o candidato perderia a aposta que o titular salva."""
    texto = "[Código: TQ8770485441I]\nStake: R$ 10,00\nSeleções:\n  • Time A @ 1,85\n"
    bruto = _tsv("01/07/2026\tFutebol\t\tBet365\tc1\tML\tTime A\t10,00\t1,85\tW\tTQ8770485441W")
    final, _ = main._fiscais_da_sombra(bruto, texto, False, None)
    assert "TQ8770485441I" in final and "TQ8770485441W" not in final


# ── custo ────────────────────────────────────────────────────────────────────

def test_o_modelo_da_sombra_tem_preco():
    """Sem linha em `_PRECOS` o custo da sombra sairia ao preço do Sonnet 4.6 e o
    experimento mentiria para o lado que favorece o candidato (s385)."""
    assert main._SOMBRA_MODELO in repository._PRECOS


def test_prompt_longo_do_haiku_5_5_cobra_a_tabela_longa():
    curto = {"input": 50_000, "output": 1_000}
    longo = {"input": 50_000, "cache_read": 60_000, "output": 1_000}
    assert repository.custo_usd_chamada("claude-haiku-5-5", curto) == \
        repository.custo_usd("claude-haiku-5-5", curto)
    esperado = (50_000 * 0.50 + 60_000 * 0.05 + 1_000 * 2.50) / 1_000_000
    assert abs(repository.custo_usd_chamada("claude-haiku-5-5", longo) - esperado) < 1e-12
