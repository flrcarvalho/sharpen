"""Filtro de pendências da grade (ponte "aviso do RAIO-X → linha na tela", s258).

Testa a montagem do WHERE, que é pura (não abre conexão). Duas garantias:

1. **O nome da pendência nunca vira SQL.** O fragmento sai de `_PENDENCIAS_SQL` por
   lookup; nome desconhecido é IGNORADO (a listagem volta completa) em vez de ser
   interpolado. É o que separa este filtro de uma injeção por querystring.
2. **A régua bate com o rail.** `analisar_extracao` conta "sem odd" com
   `_num(odd) > 0`; o SQL tem de concordar em vazio e em zero, senão o chip mostra
   um número e a nota mostra outro — e o usuário perde a confiança nos dois.
"""
import re

import repository as R


def _where(**kw):
    base = dict(dono="D", casa=None, parceiro=None, extraction_state=None, archived="all")
    base.update(kw)
    return R._filtros_bilhetes(**base)[0]


# ── 1. Superfície: só nome conhecido entra ────────────────────────────────────
def test_pendencia_conhecida_entra_no_where():
    w = _where(pendencia="sem_odd")
    assert "odd IS NULL" in w


def test_pendencia_desconhecida_e_ignorada():
    """Nome fora do dicionário não filtra nada e, sobretudo, não é interpolado."""
    w = _where(pendencia="odd IS NULL) OR (1=1")
    assert "1=1" not in w
    assert w == _where(pendencia=None)


def test_todas_as_pendencias_da_ui_existem():
    """Os 4 chips do front (`PENDENCIAS` no index.html) precisam ter par no backend."""
    assert set(R._PENDENCIAS_SQL) == {"sem_odd", "sem_stake", "categoria", "sem_tipster"}


def test_pendencia_nao_consome_placeholder():
    """O fragmento é SQL constante: não pode gastar um $n e desalinhar os params."""
    where, params = R._filtros_bilhetes("D", "Betfair", "Vini", None, "all", "sem_odd")
    assert len(params) == 3                                  # dono, casa, parceiro
    assert set(re.findall(r"\$(\d+)", where)) == {"1", "2", "3"}


def test_pendencia_convive_com_os_outros_filtros():
    w = R._filtros_bilhetes("D", "Betfair", "Vini", None, "false", "categoria")[0]
    assert "archived = FALSE" in w and "aposta ILIKE" in w and "dono = $1" in w


# ── 2. Régua igual à do rail (`analisar_extracao`) ────────────────────────────
# `_PENDENCIAS_SQL` roda no Postgres; aqui exercitamos a MESMA classificação em
# Python (`_num(...) > 0`) sobre os valores que o banco guarda, para travar o
# contrato: o que o rail chama de "sem odd" é o que o chip tem de listar.
def test_regua_sem_odd_bate_com_a_do_rail():
    for vazio in ["", "  ", "0", "0,00", "0.00"]:
        assert R._num(vazio) <= 0, f"{vazio!r} deveria contar como sem odd"
    for cheio in ["1", "1,90", "2.35", "180"]:
        assert R._num(cheio) > 0, f"{cheio!r} NÃO é sem odd"


def test_stake_pt_br_com_milhar_nao_e_pendencia():
    """`stake` vem em pt-BR ("1.914,56"). Se a régua tratasse o ponto como decimal
    (ou tentasse `::numeric` no SQL) esta linha viraria pendência — ou derrubaria a
    query inteira. Por isso o predicado é regex de vazio-ou-zero, não cast."""
    assert R._num("1.914,56") > 0
