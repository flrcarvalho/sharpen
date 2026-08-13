"""Testes da 12ª coluna — estrutura de SISTEMA (`3 x Duplas`), s265.

POR QUE ESTA COLUNA EXISTE: a odd de um sistema é a MÉDIA das linhas, não o produto
(`MASTER_RESULTADO §7.3`), mas NADA no banco dizia que a linha era sistema — `Aposta` é a
categoria canônica (`Múltipla`) e a descrição de um `3 x Duplas` é **idêntica** à da tripla
das mesmas seleções. Sem a coluna não dá para varrer o histórico atrás de odd errada nem
medir o volume desse tipo de aposta.

O QUE ESTES TESTES TRAVAM, e é a decisão de desenho que importa: a coluna **não é escrita
pela IA**. O backend a extrai do texto do robô (`Tipo: SISTEMA …`) e a casa pelo código —
determinístico, sem modelo no caminho, sem mexer no formato canônico das 10 colunas.
Funções puras: rodam na suíte normal, sem banco.
"""
import repository as R

TAB = "\t"


def _linha(*campos):
    return TAB.join(campos)


# Os dois bilhetes irmãos REAIS do caso que abriu a s265 (conta BrunnoAD, 14/08/2026):
# mesmas 3 seleções, mesmas odds — só a estrutura os separa.
TEXTO = """[Código: LK9931120902I]
Data (encerramento): 14/08/2026
Stake: 303,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Tipo: SISTEMA Duplas — 3 apostas de 2 seleção(ões), sobre 3 seleções · aposta unitária R$ 101,00 · total R$ 303,00
Odd (estrutural do sistema): 3,282  ← JÁ CALCULADA (média das 3 linhas).
Seleções:
  • Ringmahon Rangers @ 1,42

[Código: LK9931120901I]
Stake: 51,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Tipo: Múltipla (3 seleções)
Seleções:
  • Ringmahon Rangers @ 1,42
"""

DUPLAS = "LK9931120902I"
TRIPLA = "LK9931120901I"


def _tsv_dos_irmaos():
    return "\n".join([
        _linha("14/08/2026", "Futebol", "", "Bet365", "BrunnoAD", "Múltipla",
               "A // B // C", "303,00", "3,282", "", DUPLAS),
        _linha("14/08/2026", "Futebol", "", "Bet365", "BrunnoAD", "Múltipla",
               "A // B // C", "51,00", "5,8149", "", TRIPLA),
    ])


def test_mapa_so_traz_o_bilhete_de_sistema():
    mapa = R.sistemas_do_texto(TEXTO)
    assert mapa == {DUPLAS: ("Duplas", 3)}, "a tripla (1 aposta) não pode entrar no mapa"


def test_texto_sem_sistema_devolve_mapa_vazio():
    assert R.sistemas_do_texto("[Código: X]\nStake: 10,00\nTipo: Múltipla (3 seleções)") == {}
    assert R.sistemas_do_texto(None) == {}
    assert R.sistemas_do_texto("") == {}


def test_anexa_12a_coluna_so_na_linha_do_sistema():
    novo, fix = R.anexar_sistema_tsv(_tsv_dos_irmaos(), TEXTO)
    assert fix["sistemas"] == 1
    l_dup, l_tri = novo.split("\n")
    assert l_dup.split(TAB)[11] == "3x Duplas"
    # A linha da tripla passa INTACTA — nem ganha coluna vazia a mais.
    assert len(l_tri.split(TAB)) == 11


def test_parse_tsv_le_a_estrutura():
    novo, _ = R.anexar_sistema_tsv(_tsv_dos_irmaos(), TEXTO)
    dup, tri = R.parse_tsv(novo)
    assert dup["sistema"] == "Duplas"
    assert dup["sistema_linhas"] == 3
    assert dup["codigo_bilhete"] == DUPLAS
    # Bilhete de linha única não ganha estrutura — a AUSÊNCIA é o sinal de "não é sistema".
    assert "sistema" not in tri
    assert "sistema_linhas" not in tri


def test_sem_texto_e_no_op():
    tsv = _tsv_dos_irmaos()
    novo, fix = R.anexar_sistema_tsv(tsv, None)
    assert novo == tsv and fix["sistemas"] == 0


def test_linha_sem_codigo_passa_intacta():
    # Sem código não há como casar com o texto — e inventar seria pior que não marcar.
    tsv = _linha("14/08/2026", "Futebol", "", "Bet365", "BrunnoAD", "Múltipla",
                 "A // B // C", "303,00", "3,282", "")
    novo, fix = R.anexar_sistema_tsv(tsv, TEXTO)
    assert novo == tsv and fix["sistemas"] == 0


def test_nota_e_texto_livre_passam_intactos():
    # O TSV vem seguido do bloco de notas da IA; nada ali pode virar coluna.
    tsv = _tsv_dos_irmaos() + "\n\nObservação: conferir o bilhete X."
    novo, _ = R.anexar_sistema_tsv(tsv, TEXTO)
    assert novo.endswith("Observação: conferir o bilhete X.")


def test_rotulo_sem_nome_vira_Sistema():
    # O robô escreve `?` quando a casa não nomeou o tipo; o nº de linhas ainda vale, e é ele
    # que separa sistema de múltipla.
    texto = "[Código: ZZ1]\nTipo: SISTEMA ? — 6 apostas de 2 seleção(ões), sobre 4 seleções\n"
    assert R.sistemas_do_texto(texto) == {"ZZ1": ("Sistema", 6)}


def test_reanexar_nao_duplica_coluna():
    # Rodar duas vezes (repesca de cobertura, reprocessamento) tem de ser idempotente.
    novo, _ = R.anexar_sistema_tsv(_tsv_dos_irmaos(), TEXTO)
    duas, fix = R.anexar_sistema_tsv(novo, TEXTO)
    assert duas == novo and fix["sistemas"] == 1
    assert len(duas.split("\n")[0].split(TAB)) == 12


def test_estrutura_nao_entra_na_assinatura():
    # `sistema` é METADADO. Se entrasse no hash, marcar um bilhete antigo mudaria a
    # assinatura dele e a próxima captura duplicaria o histórico inteiro (CLAUDE.md).
    base = {"casa": "Bet365", "parceiro": "BrunnoAD", "data": "14/08/2026",
            "aposta": "Múltipla", "descricao": "A // B // C", "stake": "303,00",
            "odd": "3,282"}
    com = dict(base, sistema="Duplas", sistema_linhas=3)
    assert R._assinatura(base) == R._assinatura(com)
