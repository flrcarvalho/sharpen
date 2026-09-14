"""Regressão do CÓDIGO inventado pela IA e da órfã que é cópia (s356).

O defeito real, medido na base: o `codigo_bilhete` entra na assinatura de dedup, mas
quem escreve essa coluna é a IA, copiando o `[Código: …]` do bloco. Um caractere
trocado não é erro de digitação — é um bilhete NOVO para o sistema.

Provado com `bloco_visto`/`sombra_rotulos`, que guardam o código que o robô REALMENTE
emitiu: `TQ8770485441I` apareceu nas seis capturas do bilhete e `TQ8770485441W` em
NENHUMA, e mesmo assim as duas linhas estão no banco — a `…I` resolvida `L`, a `…W`
aberta para sempre. Idem `JQ3249290491F` contra `JQ3249290491I`. Na bet365 a letra
final real é só `I`, `W` ou `F`, e a troca medida é quase sempre `F ↔ I`: 22 pares em
26.609 códigos, 21 deles nascidos no MESMO segundo — porque o código falso faz o
bilhete verdadeiro parecer faltante e a repescagem entrega a segunda linha ali mesmo.

O segundo defeito é a outra linha do mesmo print: órfã sem código (id 265429), cópia
de um bloco que já tinha linha própria. O descarte antigo só agia quando NENHUM código
do texto tinha ficado livre, e num lote grande quase sempre sobra um.

O QUE ESTES TESTES NÃO COBREM
-----------------------------
· Não exercem o stream nem a chamada à IA: `_corrigir_codigos_fantasma` e
  `_reconciliar_orfas` são funções puras e é assim que são medidas aqui.
· Não cobrem lote com IMAGEM de verdade (só o flag `tem_imagem=True`, que é o que a
  rota passa); a procedência do código de print é assunto do `codigo_ocr` (s338).
· Não cobrem a Migração B/B' do UPSERT, que é a trava seguinte, no banco.
"""
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")

import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover - nunca chamado nos testes
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

import main  # noqa: E402


# Os dois bilhetes REAIS do par da s356 (conta marloncezar01, 12/09/2026). Os blocos
# reproduzem o formato que o `b3_inject` injeta, com os nomes próprios e os decimais
# que o `checar_fidelidade` compara.
BLOCO_LIU = (
    "[Código: TQ8770485441I]\n"
    "Data (encerramento): 12/09/2026\n"
    "Stake: 291,66\n"
    "Status: em aberto (aguardando resultado)\n"
    "Odd: 2,2\n"
    "Esporte (casa): CL=94 (Badminton)\n"
    "Seleções:\n"
    "  • Liu/Wang x Chou/Ko · Dupla Resultado e Total · "
    "Jia Yue Liu/Zi Meng Wang & Menos de 78.5 @ 2,2"
)
BLOCO_LANKSHEAR = (
    "[Código: GQ9767190881I]\n"
    "Data (encerramento): 12/09/2026\n"
    "Stake: 50,00\n"
    "Status: em aberto (aguardando resultado)\n"
    "Tipo: Múltipla (3 seleções)\n"
    "Seleções:\n"
    "  • Middlesbrough x Norwich · Para Marcar a Qualquer Momento · Will Lankshear @ 2,3\n"
    "  • Southampton x Bristol City · Para Marcar a Qualquer Momento · Cyle Larin @ 2,2"
)
BLOCO_GRIMLEY = (
    "[Código: JQ3249290491I]\n"
    "Data (encerramento): 12/09/2026\n"
    "Stake: 318,19\n"
    "Status: Ganho → W (retorno R$ 668,20)\n"
    "Odd: 2,1\n"
    "Seleções:\n"
    "  • Grimley/Grimley x Nebel/Soby · Dupla Resultado e Total · "
    "Christopher Grimley/Matthew Grimley & Menos de 79.5 @ 2,1"
)

DESC_LIU = ("Jia Yue Liu/Zi Meng Wang [Liu/Wang v Chou/Ko] // "
            "Under 78.5 Pontos [Liu/Wang v Chou/Ko]")
DESC_LANKSHEAR = ("Will Lankshear [Middlesbrough v Norwich] // "
                  "Cyle Larin [Southampton v Bristol City]")
DESC_GRIMLEY = ("Christopher Grimley/Matthew Grimley [Grimley/Grimley v Nebel/Soby] // "
                "Under 79.5 Pontos [Grimley/Grimley v Nebel/Soby]")


def _linha(desc, codigo, stake="291,66", odd="2,2", res=""):
    return (f"12/09/2026\tBadminton\tBad Milton\tBet365\tmarloncezar01 [Richard]\t"
            f"Múltipla\t{desc}\t{stake}\t{odd}\t{res}\t{codigo}")


def _tsv(*linhas):
    return ("```tsv\n" + "\n".join([main._TSV_HEADER, *linhas])
            + "\n```\n\n## Notas Críticas\nNenhuma")


def _cods(texto_tsv):
    return [l.split("\t")[10] for l in main._extract_tsv_rows(texto_tsv)]


def _descs(texto_tsv):
    return [l.split("\t")[6] for l in main._extract_tsv_rows(texto_tsv)]


# ── 1. código inventado: adoção pelo bloco livre ──────────────────────────────

def test_codigo_que_nao_existe_no_texto_e_trocado_pelo_do_bloco_fiel():
    """O caso exato do par da s356: a IA escreveu `…W`, o robô mandou `…I`."""
    tsv = _tsv(_linha(DESC_LIU, "TQ8770485441W"))
    out, fix = main._corrigir_codigos_fantasma(tsv, BLOCO_LIU, False)
    assert fix["fantasmas"] == 1
    assert fix["adotados"] == 1
    assert fix["esvaziados"] == 0
    assert _cods(out) == ["TQ8770485441I"]


def test_troca_de_letra_final_f_por_i_tambem_e_pega():
    """A troca `F ↔ I` é 21 dos 22 pares medidos na bet365."""
    tsv = _tsv(_linha(DESC_GRIMLEY, "JQ3249290491F", stake="318,19", odd="2,1", res="W"))
    out, fix = main._corrigir_codigos_fantasma(tsv, BLOCO_GRIMLEY, False)
    assert fix["adotados"] == 1
    assert _cods(out) == ["JQ3249290491I"]


def test_codigo_verdadeiro_passa_intacto():
    """A linha certa não pode ser tocada — senão o gate vira o defeito."""
    tsv = _tsv(_linha(DESC_LIU, "TQ8770485441I"))
    out, fix = main._corrigir_codigos_fantasma(tsv, BLOCO_LIU, False)
    assert fix == {"fantasmas": 0, "adotados": 0, "esvaziados": 0, "exemplos": []}
    assert out == tsv


# ── 2. código inventado: esvaziamento quando não há par único ─────────────────

def test_sem_bloco_livre_fiel_o_codigo_falso_e_esvaziado_nao_mantido():
    """Manter o código falso GARANTE linha nova; esvaziar entrega a linha às travas
    de órfã, que são três. A linha fala de Lankshear e o único bloco livre é o de
    Liu/Wang, então não há par possível."""
    tsv = _tsv(_linha(DESC_LANKSHEAR, "ZZ0000000001X"))
    out, fix = main._corrigir_codigos_fantasma(tsv, BLOCO_LIU, False)
    assert fix["fantasmas"] == 1
    assert fix["adotados"] == 0
    assert fix["esvaziados"] == 1
    assert _cods(out) == [""]


def test_bloco_que_serve_a_duas_linhas_fantasma_nao_e_adotado_por_nenhuma():
    """Ambíguo não vira chute: adotar o errado SEQUESTRA a identidade de outro bilhete,
    que é pior que duplicar."""
    tsv = _tsv(_linha(DESC_LIU, "ZZ0000000001X"), _linha(DESC_LIU, "ZZ0000000002X"))
    out, fix = main._corrigir_codigos_fantasma(tsv, BLOCO_LIU, False)
    assert fix["adotados"] == 0
    assert fix["esvaziados"] == 2
    assert _cods(out) == ["", ""]


def test_o_bloco_ja_usado_por_uma_linha_boa_nao_e_roubado_pela_fantasma():
    """`livres` exclui o que já está no TSV. Sem isso a fantasma levaria o código da
    linha correta e as duas linhas ficariam com o mesmo código."""
    texto = BLOCO_LIU + "\n\n" + BLOCO_LANKSHEAR
    tsv = _tsv(_linha(DESC_LIU, "TQ8770485441I"),
               _linha(DESC_LIU, "TQ8770485441W"))
    out, fix = main._corrigir_codigos_fantasma(tsv, texto, False)
    assert fix["fantasmas"] == 1
    assert fix["adotados"] == 0          # `…I` não está livre; o bloco livre é o do Lankshear
    assert _cods(out) == ["TQ8770485441I", ""]


# ── 3. no-op onde o código legitimamente não está no texto ────────────────────

def test_lote_com_imagem_e_no_op_integral():
    """No print o código vem do card, legitimamente fora do texto. Quem trata a
    procedência ali é o `codigo_ocr` (s338) — apagar seria destruir dado bom."""
    tsv = _tsv(_linha(DESC_LIU, "TQ8770485441W"))
    out, fix = main._corrigir_codigos_fantasma(tsv, BLOCO_LIU, True)
    assert fix["fantasmas"] == 0
    assert out == tsv


def test_casa_sem_marcador_e_no_op_integral():
    """Sem gabarito não há o que conferir; suspeitar no escuro apagaria a coluna toda."""
    tsv = _tsv(_linha(DESC_LIU, "QUALQUERCOISA"))
    out, fix = main._corrigir_codigos_fantasma(tsv, "texto colado sem marcador nenhum", False)
    assert fix["fantasmas"] == 0
    assert out == tsv


def test_linha_sem_codigo_nao_e_tratada_como_fantasma():
    """Coluna 11 vazia é órfã — assunto de `_reconciliar_orfas`, não deste gate."""
    tsv = _tsv(_linha(DESC_LIU, ""))
    out, fix = main._corrigir_codigos_fantasma(tsv, BLOCO_LIU, False)
    assert fix["fantasmas"] == 0
    assert out == tsv


# ── 4. órfã que é cópia de bloco já coberto (o buraco do descarte) ────────────

def test_orfa_copia_de_bloco_ja_coberto_sai_mesmo_sobrando_codigo_livre():
    """O fantasma do id 265429: a órfã é fiel ao bloco do Lankshear, que JÁ tem linha
    própria, e o lote ainda tem o bloco de Liu/Wang livre. Pelo critério antigo
    (`if not livres`) ela ficava, e virava `aberta` para sempre."""
    texto = BLOCO_LANKSHEAR + "\n\n" + BLOCO_LIU
    tsv = _tsv(_linha(DESC_LANKSHEAR, "GQ9767190881I", stake="50,00", odd="13,156"),
               _linha(DESC_LANKSHEAR, "", stake="50,00", odd="13,156"))
    out, orfas = main._reconciliar_orfas(tsv, texto)
    assert orfas["orfas"] == 1
    assert orfas["orfas_descartadas"] == 1
    assert _cods(out) == ["GQ9767190881I"]


def test_orfa_com_bloco_proprio_livre_e_adotada_nao_descartada():
    """Adoção continua tendo precedência: aqui a órfã é o único dono do bloco livre."""
    texto = BLOCO_LANKSHEAR + "\n\n" + BLOCO_LIU
    tsv = _tsv(_linha(DESC_LANKSHEAR, "GQ9767190881I", stake="50,00", odd="13,156"),
               _linha(DESC_LIU, ""))
    out, orfas = main._reconciliar_orfas(tsv, texto)
    assert orfas["orfas_adotadas"] == 1
    assert orfas["orfas_descartadas"] == 0
    assert _cods(out) == ["GQ9767190881I", "TQ8770485441I"]


def test_orfa_fiel_a_dois_blocos_ainda_livres_nao_e_descartada():
    """Dois bilhetes de conteúdo idêntico existem de verdade (a pessoa apostou duas
    vezes, e são 166 grupos assim na base). Com DOIS blocos livres a órfã pode ser
    qualquer um dos dois: a adoção não decide (ambígua) e o descarte também não pode,
    porque ela corresponde a um bilhete que ainda não tem linha. Descartar aqui apagaria
    aposta real — é este o caso que separa o critério novo de uma poda cega."""
    g2 = BLOCO_LIU.replace("TQ8770485441I", "TQ8770485442I")
    g3 = BLOCO_LIU.replace("TQ8770485441I", "TQ8770485443I")
    texto = "\n\n".join([BLOCO_LIU, g2, g3])
    tsv = _tsv(_linha(DESC_LIU, "TQ8770485441I"), _linha(DESC_LIU, ""))
    out, orfas = main._reconciliar_orfas(tsv, texto)
    assert orfas["orfas_adotadas"] == 0       # dois blocos livres servem: ambíguo
    assert orfas["orfas_descartadas"] == 0
    assert len(main._extract_tsv_rows(out)) == 2


def test_marcador_vazio_no_texto_mantem_o_no_op_da_reconciliacao():
    """`[Código: ]` é o que a bet365 manda quando o detalhe não chegou: ali a coluna 11
    vazia é legítima e descartar apagaria bilhete real."""
    texto = BLOCO_LANKSHEAR + "\n\n[Código: ]\nData: 12/09/2026\nStake: 10,00"
    tsv = _tsv(_linha(DESC_LANKSHEAR, "GQ9767190881I", stake="50,00", odd="13,156"),
               _linha(DESC_LANKSHEAR, "", stake="50,00", odd="13,156"))
    out, orfas = main._reconciliar_orfas(tsv, texto)
    assert orfas["orfas_descartadas"] == 0
    assert len(main._extract_tsv_rows(out)) == 2


def test_regra_antiga_do_descarte_continua_valendo():
    """Sem código livre nenhum, toda órfã sobrando é cópia — comportamento anterior,
    que não pode ter sido perdido na ampliação."""
    tsv = _tsv(_linha(DESC_LIU, "TQ8770485441I"), _linha(DESC_GRIMLEY, ""))
    out, orfas = main._reconciliar_orfas(tsv, BLOCO_LIU)
    assert orfas["orfas_descartadas"] == 1
    assert _cods(out) == ["TQ8770485441I"]
