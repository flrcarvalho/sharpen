"""O LEITOR confere o tipo de cada campo, não só a contagem (s417, parecer 020; 14/10/2026).

O caso: a extração da BetMartini de 14/10 às 14:43 (`sombra_tsv` f86c6bc7). A IA pulou a
coluna Tipster em várias linhas, e em 5525074378 e 5525070140 ainda pôs um campo vazio antes
do código. A contagem deu 11: o leitor gravou a descrição em Aposta e a stake em Descrição, e
o conferidor de stake trocou a odd 4,761 por 25,00. As duas foram gravadas sem odd. A linha
de 10 campos (5525064887, só o Tipster pulado) era lida com o código no Resultado e recusada
em silêncio; entrou só na captura seguinte.

A saída real dessa extração é a fixture: `tests/leitor_betmartini_bruto.tsv` (a IA, antes de
qualquer fiscal) e `tests/leitor_betmartini_final.tsv` (depois do conferidor, como foi ao
banco). Sem dado de pessoa além do nome da conta, que é do Feca.

A regra (`repository.conferir_linha`, `alinhar_linha`, `alinhar_tsv`, `deslocada`):
  · data no campo de data; número > 0 na stake e na odd (odd vazia é recusa no `/extrair`);
    código com cara de código; casa igual à da captura; Aposta é categoria (Master ∪ base do
    dono) e nunca uma descrição; Descrição nunca é só um número;
  · fora do tipo, UMA hipótese de conserto (o Tipster pulado, e o vazio que sobrar antes do
    código sai). Bate em tudo → vale; senão a linha é recusada: no `/extrair` sai do lote e a
    cobertura a pede de novo à IA; no `/salvar` fica na mesma posição e o `validar_linhas` a
    recusa. Nunca grava;
  · o conferidor de stake não toca linha com sinal de coluna trocada.

Mutações (s417, `scratchpad/mutar7.py`), cada uma derrubou ao menos um teste daqui:
  L1. sem a odd obrigatória                                  → test_odd_vazia_e_recusa
  L2. Aposta com cara de descrição passa                     → test_toda_coluna_tirada_e_somada…
  L3. sem a hipótese do Tipster pulado                        → test_a_saida_real…
  L4. o vazio antes do código não sai                         → test_a_saida_real…
  L5. o conferidor corrige linha desalinhada                  → test_o_conferidor_nao_mexe…
  L6. o `parse_tsv` não realinha                              → test_o_salvar_le_a_saida_real…
  L7. o `validar_linhas` ignora a linha deslocada             → test_o_salvar_recusa…
  L8. sem a checagem da casa                                  → test_casa_e_categoria
  L9. sem a checagem da categoria                             → test_casa_e_categoria
  L10. Descrição só número passa                              → test_toda_coluna_tirada_e_somada…
  L11. o `/extrair` sem o leitor (seq ou par)                 → test_o_extrair_chama_o_leitor…
  L12. sem a checagem do Esporte                              → test_toda_coluna_tirada_e_somada…
  L13. a casa no campo do Tipster passa                       → test_toda_coluna_tirada_e_somada…
  L14. a casa no campo do Parceiro passa                      → test_toda_coluna_tirada_e_somada…
  L15. o `/salvar` sem a assinatura do Esporte                → test_toda_coluna_tirada_e_somada…
  L16. o `/salvar` sem a Descrição igual a categoria          → test_toda_coluna_tirada_e_somada…
  (16 de 16 detectadas; L10 escapou na 1ª rodada e ganhou a asserção direta em
  test_casa_e_categoria. As L12 a L16 nasceram de furos que a própria mutação de colunas achou.)

O `/salvar` é a rede de baixo, para qualquer origem (bot, import, extensão): realinha o
Tipster pulado e recusa as assinaturas de coluna trocada (Aposta com descrição ou número,
Descrição só número ou igual a uma categoria, Esporte com data, número ou descrição). Odd e
stake vazias ele aceita (o bot grava bet builder sem odd como vazio, s318; stake vazia é a aberta
lida pela metade): a garantia dele vale com as duas preenchidas. Stake e odd obrigatórias são do
leitor do `/extrair`, por onde passa toda linha da IA.

O que NÃO está coberto: a repescagem real da linha recusada (a cobertura já tem gate próprio)
e o caminho de print, onde o leitor só confere a forma (sem gabarito não há repescagem, e a
linha recusada seria aposta perdida).
"""
from pathlib import Path

import repository as R
import taxonomia

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = (RAIZ / "tests" / "leitor_betmartini_bruto.tsv").read_text(encoding="utf-8")
FINAL = (RAIZ / "tests" / "leitor_betmartini_final.tsv").read_text(encoding="utf-8")
MASTER = frozenset(taxonomia.categorias_canonicas())
KW = {"casa": "BetMartini", "categorias": MASTER, "exige_codigo": True, "exige_odd": True}


def _linhas(tsv):
    return [ln.split("\t") for ln in tsv.split("\n")
            if len(ln.split("\t")) >= 10 and ln[:2].isdigit()]


def test_a_saida_real_da_betmartini_sai_sem_nenhuma_linha_deslocada():
    tsv, st = R.alinhar_tsv(BRUTO, **KW)
    assert st["recusadas"] == 0 and st["realinhadas"] == 3
    linhas = {p[10]: p for p in _linhas(tsv)}
    assert len(linhas) == 7
    for p in linhas.values():
        assert len(p) == 11 and R.conferir_linha(p, **KW) == [], p
        assert p[3] == "BetMartini" and p[5] == "Múltipla" and "[" in p[6]
    assert (linhas["5525074378"][7], linhas["5525074378"][8]) == ("25,00", "4,761")
    assert (linhas["5525070140"][7], linhas["5525070140"][8]) == ("25,00", "4,759067")
    # a de 10 campos (só o Tipster pulado) é lida certo
    assert (linhas["5525064887"][7], linhas["5525064887"][8]) == ("25,00", "4,73")
    # as que vieram certas passam intactas
    assert linhas["5525081900"][4] == "Feca [Eu]" and linhas["5525081900"][8] == "4,80775"


def test_o_salvar_le_a_saida_real_sem_deslocar():
    rows = R.parse_tsv(BRUTO)
    assert len(rows) == 7 and not [r for r in rows if r.get("_deslocada")]
    por = {r["codigo_bilhete"]: r for r in rows}
    assert set(por) == {"5525064887", "5525074378", "5525070140", "5525081900", "5525078266",
                        "5525093870", "5525085428"}
    assert all(r["aposta"] == "Múltipla" for r in rows)
    assert (por["5525074378"]["stake"], por["5525074378"]["odd"]) == ("25,00", "4,761")
    assert R.validar_linhas(rows)[1] == []


def test_o_salvar_recusa_a_linha_deslocada_que_nao_se_conserta():
    # duas colunas a menos: nenhuma hipótese bate; fica na posição, e é recusada
    linha = "14/10/2026\tMúltiplos\tMúltipla\tA v B [A v B] // C [C v D]\t25,00\t4,5\t\t1234567"
    rows = R.parse_tsv("\n".join([linha + "\t\t", _boa()]))
    assert rows[0].get("_deslocada") is True
    ok, rec = R.validar_linhas(rows)
    assert len(ok) == 1 and rec[0]["linha"] == 1 and "desalinhada" in rec[0]["erro"]


def _boa():
    return "\t".join(["14/10/2026", "Futebol", "", "BetMartini", "Feca [Eu]", "ML",
                      "Time A [Time A v Time B]", "25,00", "1,85", "", "5525000001"])


def test_o_conferidor_nao_mexe_em_linha_desalinhada():
    """A linha como a IA mandou, sem o leitor antes: a coluna 8 é a odd, e o bloco diz stake
    25,00. Antes, ela virava 25,00."""
    texto = "[Código: 5525074378]\nStake: 25,00\nStatus: aberta\n"
    linha = next("\t".join(p) for p in _linhas(BRUTO) if p[-1] == "5525074378")
    tsv, st = R.corrigir_stake_tsv(linha, texto)
    assert tsv == linha and st["stakes"] == 0
    # e a mesma linha no lugar é conferida normalmente
    certa, _, _ = R.alinhar_linha(linha.split("\t"), **KW)
    certa[7] = "20,00"
    tsv, st = R.corrigir_stake_tsv("\t".join(certa), texto)
    assert st["stakes"] == 1 and tsv.split("\t")[7] == "25,00"


def test_odd_vazia_e_recusa():
    p = _boa().split("\t")
    p[8] = ""
    assert "odd" in R.conferir_linha(p, **KW)
    tsv, st = R.alinhar_tsv("\t".join(p), **KW)
    assert st["recusadas"] == 1 and tsv == ""
    p[9] = "L"
    assert R.alinhar_tsv("\t".join(p), **KW)[1]["recusadas"] == 1, "liquidada também"


def test_casa_e_categoria():
    p = _boa().split("\t")
    assert R.conferir_linha(p, **KW) == []
    assert R.conferir_linha(p, **dict(KW, casa="Bet Martini")) == []      # grafia
    q = list(p); q[3] = "SportingBet"
    assert R.conferir_linha(q, **KW) == ["casa"]
    q = list(p); q[6] = "25,00"                     # a stake no campo da Descrição (o caso)
    assert R.conferir_linha(q, **KW) == ["descrição"]
    q = list(p); q[5] = "Especiais"
    assert R.conferir_linha(q, **KW) == ["aposta"]
    assert R.conferir_linha(q, **dict(KW, categorias=MASTER | {"Especiais"})) == []


def test_toda_coluna_tirada_e_somada_em_qualquer_posicao_nunca_grava_deslocada():
    """Item 5 do parecer: de cada linha certa da saída real, tira uma coluna e soma uma vazia
    em todas as posições. O leitor devolve a linha CERTA ou recusa; nunca uma deslocada."""
    certas, _ = R.alinhar_tsv(BRUTO, **KW)
    n = recusadas = consertadas = 0
    for p in _linhas(certas):
        for i in range(11):
            for j in range(11):
                q = p[:i] + p[i + 1:]
                q = q[:j] + [""] + q[j:]
                if i == j:
                    continue            # tirar e somar no mesmo lugar só esvazia o campo
                n += 1
                linha, _re, _m = R.alinhar_linha(q, **KW)
                if linha is None:
                    recusadas += 1
                else:
                    consertadas += 1
                    _so_esvaziou(linha, p, (i, j, q))
                # o /salvar (outra origem, sem casa nem categoria) também nunca grava deslocada
                rows = R.parse_tsv("\t".join(q))
                ok, _rec = R.validar_linhas(rows)
                # Odd vazia o /salvar aceita (s318: o bot grava bet builder sem odd como vazio),
                # e stake vazia também (aberta lida pela metade, vira aviso); quem recusa as duas
                # é o leitor do /extrair, acima, por onde passa toda linha da IA.
                if ok and ok[0].get("odd") and ok[0].get("stake"):
                    r = ok[0]
                    # o /salvar aceita Esporte e Aposta vazios (187 linhas da extração em 60
                    # dias vieram assim); o leitor do /extrair não. Vazio não é valor no lugar
                    # errado: a garantia aqui é que nenhum VALOR cai em outro campo.
                    _so_esvaziou([r.get(c, "") for c in R._COLS] + [r.get("codigo_bilhete", "")],
                                 p, ("salvar", i, j, q), _SOBRESCRITOS | {1, 5, 10})
    assert n > 500 and consertadas > 0 and recusadas > 0


# Tipster, Casa e Parceiro: o `/salvar` grava os da conta. Sumir com um deles não é deslocar.
_SOBRESCRITOS = {2, 3, 4}


def _so_esvaziou(linha, p, onde, podem=_SOBRESCRITOS):
    for k, (a, b) in enumerate(zip(linha, p)):
        if onde[0] == "salvar" and k in _SOBRESCRITOS:
            continue                    # o /salvar grava tipster vazio e casa/conta da conta
        assert a == b or (k in podem and a == ""), (onde, k, a, b)


def test_o_extrair_chama_o_leitor_nos_dois_caminhos_antes_dos_fiscais():
    src = (RAIZ / "app" / "main.py").read_text(encoding="utf-8")
    for rot in ('"seq"', '"par"', '"seq pós-repesca"', '"par pós-repesca"'):
        assert f"await _leitor(" in src and rot in src, rot
    seq = src[src.index("async def _stream_sequential"):src.index("async def _stream_parallel")]
    assert seq.index('_leitor(accumulated, texto, dono, casa, "seq")') < \
        seq.index("corrigir_codigos_tsv(accumulated") < seq.index("_garantir_cobertura(")
    assert seq.index('"seq pós-repesca"') < seq.index("corrigir_stake_tsv(accumulated")
    par = src[src.index("async def _stream_parallel"):src.index("def _evento(")]
    assert par.index('_leitor(resultado, texto, dono, casa, "par")') < \
        par.index("corrigir_codigos_tsv(resultado") < par.index("_garantir_cobertura(")
    assert par.index('"par pós-repesca"') < par.index("corrigir_stake_tsv(resultado")
