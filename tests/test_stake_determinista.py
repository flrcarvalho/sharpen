"""Testes da stake determinística (coluna 8 lida do bloco cru, não da IA) — s311.

O CASO REAL QUE ABRIU A REGRA: a Pinnacle `3113103675` (LOUD v MIBR) foi gravada com
stake `400,00` — a stake do `3114339695` (Patrick Rivera), **duas linhas acima no mesmo
chunk**. É o carryover que a s302 documentou na descrição, agora no financeiro; o
`CLAUDE.md` afirmava que "o financeiro não viaja junto", e isso era observação medida,
não garantia.

POR QUE NENHUM GATE PEGAVA: a descrição estava certa (passa em `checar_descricao` e em
`checar_fidelidade`), o código estava lá (a cobertura conta o bilhete), e a odd de W é
derivada de `Retorno ÷ Stake` — recalculada sobre a stake errada, `(400 + 330,48) ÷ 400
= 1,8262`, ela mantém o **P/L exato**. Erram só turnover, ROI e a assinatura de stake do
matcher de tipster. Silêncio completo.

Os blocos abaixo são os TRÊS bilhetes REAIS do lote (`sombra_rotulos`, 01/09/2026,
conta Feca·Pinnacle), verbatim — inclusive o vizinho aberto que emprestou a stake.

MUTAÇÕES QUE ESTES TESTES PEGAM (rodadas, uma a uma, contra o código real):
  • trocar `parts[7] = stake_bloco` por `pass`            → o carryover volta
  • pular a correção da odd (`odd_nova` nunca aplicada)   → P/L fica errado em W
  • trocar `len(set(valores)) != 1` por `not valores`     → bloco ambíguo passa a mandar
  • aplicar a odd derivada em L/V também                  → a perda ganha odd inventada
  • tolerância `<= 0.005` virando `!=`                     → `204,00` × `204,0` reescreve à toa

O QUE ESTES TESTES **NÃO** COBREM:
  • extração por PRINT — imagem não tem `[Código: …]` nem `Stake:`, então o gate nunca
    dispara ali; a stake da imagem segue 100% por conta da IA;
  • bloco cujo `Stake:` está errado NA ORIGEM (a KTO manda `Stake: 1,00`) — o gate copia
    o bloco fielmente e reproduz o erro da casa. É captura, não tradução;
  • troca de stake entre dois bilhetes que têm a MESMA stake: indistinguível por
    construção, e sem efeito financeiro.

Funções puras: rodam na suíte normal, sem banco.
"""
import repository as R

TAB = "\t"

# Blocos REAIS, na ordem em que a IA os viu no chunk (o vizinho de stake 400 vem ANTES).
TEXTO = """[Código: 3114339695]
Data: 01/09/2026
Apostado em: 01/09/2026
Stake: 400,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd total: 4,190
Esporte (casa): Mixed Martial Arts · UFC

Seleções:
  • Patrick Rivera · Adam Darby v Patrick Rivera (Regular)

[Código: 3113769568]
Data: 31/08/2026
Apostado em: 31/08/2026
Stake: 204,00
Status: Perdeu (LOST) → L · P/L -204,00
Odd total: 2,340
Esporte (casa): E Sports · CS2 - BLAST Open Porto
Seleções:
  • FUT · FUT v Vitality (Regular)

[Código: 3113103675]
Data: 30/08/2026
Apostado em: 30/08/2026
Stake: 204,00
Status: Ganho (WON) → W · P/L 330,48
Odd total: 2,620
Esporte (casa): E Sports · Valorant - Champions Tour: Americas
Seleções:
  • LOUD · LOUD v MIBR (Regular)
"""

ABERTO = "3114339695"     # o vizinho que emprestou a stake
PERDIDO = "3113769568"
LOUD = "3113103675"


def _linha(*campos):
    return TAB.join(campos)


def _tsv(stake_loud="400,00", odd_loud="1,826199999999999"):
    """O TSV como a IA o devolveu no dia (default) — a linha do LOUD com a stake do
    vizinho e a odd derivada dela."""
    return "\n".join([
        _linha("01/09/2026", "MMA", "", "Pinnacle", "Feca [Eu]", "ML",
               "Patrick Rivera [Adam Darby v Patrick Rivera]", "400,00", "4,190", "", ABERTO),
        _linha("31/08/2026", "E-Sports", "Zora", "Pinnacle", "Feca [Eu]", "ML",
               "FUT [FUT v Vitality]", "204,00", "2,340", "L", PERDIDO),
        _linha("30/08/2026", "E-Sports", "", "Pinnacle", "Feca [Eu]", "ML",
               "LOUD [LOUD v MIBR]", stake_loud, odd_loud, "W", LOUD),
    ])


def _por_codigo(tsv):
    return {p[10]: p for p in (ln.split(TAB) for ln in tsv.split("\n")) if len(p) > 10}


# ── o defeito do dia ──────────────────────────────────────────────────────────

def test_carryover_de_stake_e_corrigido_pelo_bloco():
    out, info = R.corrigir_stake_tsv(_tsv(), TEXTO)
    assert info["stakes"] == 1
    assert _por_codigo(out)[LOUD][7] == "204,00"


def test_odd_de_W_acompanha_a_stake_corrigida():
    """A odd de W é derivada da stake (`Retorno ÷ Stake`). Corrigir a stake e deixar a
    odd velha trocaria um erro invisível por um erro no P/L — que é o que hoje está
    certo. `(204 + 330,48) ÷ 204 = 2,62`, e o bloco confirma: grava o texto do bloco."""
    out, _ = R.corrigir_stake_tsv(_tsv(), TEXTO)
    assert _por_codigo(out)[LOUD][8] == "2,620"


def test_pl_derivado_fica_igual_ao_da_casa():
    """O número que o Feca confere na tela: R$ 330,48, o mesmo do extrato da Pinnacle."""
    linha = _por_codigo(R.corrigir_stake_tsv(_tsv(), TEXTO)[0])[LOUD]
    stake, odd = R._num_or_none(linha[7]), R._num_or_none(linha[8])
    assert round(stake * odd - stake, 2) == 330.48


def test_o_vizinho_que_emprestou_a_stake_nao_e_tocado():
    out, _ = R.corrigir_stake_tsv(_tsv(), TEXTO)
    assert _por_codigo(out)[ABERTO][7] == "400,00"
    assert _por_codigo(out)[ABERTO][8] == "4,190"


# ── o caso normal: não mexer em nada ──────────────────────────────────────────

def test_lote_correto_passa_byte_a_byte_igual():
    tsv = _tsv(stake_loud="204,00", odd_loud="2,620")
    out, info = R.corrigir_stake_tsv(tsv, TEXTO)
    assert info["stakes"] == 0
    assert out == tsv


def test_mesma_stake_escrita_diferente_nao_reescreve():
    """`204,0` e `204,00` são o mesmo dinheiro. Comparação é numérica, não textual —
    senão o gate reescreveria linha certa e poluiria o log de correções."""
    tsv = _tsv(stake_loud="204,0", odd_loud="2,620")
    out, info = R.corrigir_stake_tsv(tsv, TEXTO)
    assert info["stakes"] == 0
    assert out == tsv


def test_linha_perdida_mantem_a_odd_exibida():
    """Em L a odd não depende da stake: corrigir uma não pode inventar a outra."""
    tsv = _tsv(stake_loud="204,00", odd_loud="2,620").replace(
        f"FUT [FUT v Vitality]{TAB}204,00", f"FUT [FUT v Vitality]{TAB}99,00")
    out, info = R.corrigir_stake_tsv(tsv, TEXTO)
    assert info["stakes"] == 1
    assert _por_codigo(out)[PERDIDO][7] == "204,00"
    assert _por_codigo(out)[PERDIDO][8] == "2,340"      # intacta


# ── fail-closed: sem prova, não corrige ───────────────────────────────────────

def test_bloco_ambiguo_nao_corrige_nada():
    """Bloco com dois `Stake:` distintos não prova qual é o do bilhete. Ausência de
    prova nunca autoriza escrita."""
    ambiguo = TEXTO.replace("Odd total: 2,620", "Odd total: 2,620\nStake: 777,00")
    out, info = R.corrigir_stake_tsv(_tsv(), ambiguo)
    assert info["stakes"] == 0
    assert _por_codigo(out)[LOUD][7] == "400,00"


def test_sem_texto_nada_acontece():
    """Extração por print: sem texto do robô, não há bloco — a stake segue com a IA."""
    tsv = _tsv()
    assert R.corrigir_stake_tsv(tsv, None) == (tsv, {"stakes": 0, "exemplos": []})
    assert R.corrigir_stake_tsv(tsv, "")[0] == tsv


def test_codigo_fora_do_texto_passa_intacto():
    tsv = _tsv().replace(LOUD, "9999999999")
    out, info = R.corrigir_stake_tsv(tsv, TEXTO)
    assert info["stakes"] == 0
    assert out == tsv


def test_linha_sem_codigo_passa_intacta():
    tsv = "\n".join(ln.rsplit(TAB, 1)[0] for ln in _tsv().split("\n"))
    out, info = R.corrigir_stake_tsv(tsv, TEXTO)
    assert info["stakes"] == 0
    assert out == tsv


def test_nota_de_texto_livre_sobrevive():
    """Linha que não é TSV (aviso do modelo) não pode ser cortada nem deslocada."""
    tsv = "Observação: 3 bilhetes lidos.\n" + _tsv()
    out, _ = R.corrigir_stake_tsv(tsv, TEXTO)
    assert out.split("\n")[0] == "Observação: 3 bilhetes lidos."


def test_decima_segunda_coluna_sobrevive_a_correcao():
    """A coluna de SISTEMA é anexada no mesmo trecho do pipeline; reescrever a linha
    não pode perdê-la (nem empurrá-la para a casa da 11ª)."""
    tsv = _tsv() + TAB + "3x Duplas"
    out, _ = R.corrigir_stake_tsv(tsv, TEXTO)
    ultima = out.split("\n")[-1].split(TAB)
    assert ultima[7] == "204,00" and ultima[10] == LOUD and ultima[11] == "3x Duplas"


# ── W sem P/L no bloco: corrige a stake, não inventa odd ──────────────────────

def test_w_sem_pl_no_bloco_mantem_a_odd():
    sem_pl = TEXTO.replace("Ganho (WON) → W · P/L 330,48", "Ganho (WON) → W")
    out, info = R.corrigir_stake_tsv(_tsv(), sem_pl)
    assert info["stakes"] == 1
    assert _por_codigo(out)[LOUD][7] == "204,00"
    assert _por_codigo(out)[LOUD][8] == "1,826199999999999"    # não inventa


def test_exemplos_dizem_o_que_a_ia_escreveu_e_o_que_o_bloco_diz():
    _, info = R.corrigir_stake_tsv(_tsv(), TEXTO)
    assert info["exemplos"] == [{"codigo": LOUD, "ia": "400,00", "bloco": "204,00"}]
