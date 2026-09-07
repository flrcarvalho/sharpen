# -*- coding: utf-8 -*-
"""Migração B do UPSERT: a linha SEM código é adotada pelo bilhete que chega COM código.

O caso que abriu a regra (s327, Betnacional / renanfernando01 [Richard]): a captura de
05/09 devolveu a múltipla do Falkirk sem a 11ª coluna, gravando a linha com `odd = "14"`.
Em 06/09 o mesmo bilhete voltou liquidado, agora COM código e `odd = "14,00"`. A Migração
B comparava a odd como STRING CRUA, não adotou a órfã, e o bilhete entrou como linha
NOVA — a velha ficou `aberta` para sempre. Sem erro, sem aviso: a única pista foi um
`AGUARDANDO RESULTADO 1` na grade e R$ 150,00 "em aberto" na Caixa num dia em que a casa
não tinha aposta pendente nenhuma.

O QUE ESTE ARQUIVO **NÃO** COBRE
--------------------------------
Aqui só se testa a CHAVE de identidade (`repository.chave_orfa`), que é pura. O caminho
de escrita de ponta a ponta (o UPDATE que adota a linha e o `pop` que impede duas linhas
do lote de reivindicarem a mesma órfã) vive em `tests/test_repository_db.py`, que exige
Postgres e por isso só roda no CI.
"""
import pytest

from repository import chave_orfa

CONTA = ("Betnacional", "renanfernando01 [Richard]")
BILHETE = ("05/09/2026", "Múltipla", "150,00")


def _k(odd, casa=CONTA[0], parceiro=CONTA[1], data=BILHETE[0],
       aposta=BILHETE[1], stake=BILHETE[2]):
    return chave_orfa(casa, parceiro, data, aposta, stake, odd)


def test_caso_medido_falkirk_14_e_14_00_sao_o_mesmo_bilhete():
    """O caso real: a órfã gravada com "14" e o bilhete liquidado com "14,00"."""
    assert _k("14") == _k("14,00")


@pytest.mark.parametrize("a,b", [
    ("14", "14,00"),        # o caso medido
    ("1,9", "1,90"),        # zero à direita
    ("2,05", "2,050"),      # três casas
    ("1,833", "1,83"),      # odd calculada (retorno÷stake) × odd exibida — regra do _norm_odd
    ("14.00", "14,00"),     # ponto decimal (import) × vírgula (extração)
])
def test_odds_equivalentes_casam(a, b):
    assert _k(a) == _k(b)


@pytest.mark.parametrize("a,b", [
    ("14", "15"),           # odds realmente diferentes
    ("1,90", "1,95"),       # diferença acima da tolerância de 2 casas
    ("2,05", "20,5"),       # vírgula no lugar errado não pode fundir bilhetes
])
def test_odds_diferentes_nao_casam(a, b):
    """A normalização não pode fundir bilhetes distintos — só absorve formatação."""
    assert _k(a) != _k(b)


def test_odd_ilegivel_nao_vira_curinga():
    """`_norm_odd` devolve o valor cru quando não dá para converter. Duas odds ilegíveis
    diferentes continuam diferentes; e uma ilegível nunca casa com uma numérica."""
    assert _k("abc") != _k("xyz")
    assert _k("abc") != _k("14,00")
    assert _k("abc") == _k("abc")


@pytest.mark.parametrize("campo,valor", [
    ("casa", "Betano"),
    ("parceiro", "outro [Richard]"),
    ("data", "06/09/2026"),
    ("aposta", "Cartões"),
    ("stake", "301,00"),
])
def test_cada_campo_restritivo_separa_bilhetes(campo, valor):
    """Todo campo da chave é load-bearing: mudar qualquer um separa os bilhetes.

    Sem isso a Migração B adotaria uma linha de OUTRA conta ou de outro dia — ela
    reescreve a assinatura e o código de uma linha existente, então errar aqui não
    duplica: sequestra.
    """
    assert _k("14,00") != _k("14,00", **{campo: valor})


def test_descricao_fica_de_fora_de_proposito():
    """A chave não tem `descricao`: a Migração B nasceu para casar import por imagem com
    a captura da casa, e é a descrição que diverge entre as duas. Este teste existe para
    a ausência ser uma DECISÃO registrada, não um esquecimento — quem for adicionar
    descrição à chave quebra aqui e vai ler o porquê."""
    import inspect
    assert "descricao" not in inspect.signature(chave_orfa).parameters
