# -*- coding: utf-8 -*-
"""Procedência do código do bilhete (s338): quem leu o número, a captura ou a IA?

O `codigo_bilhete` entra na assinatura, então um dígito trocado é um bilhete NOVO. Só que
ele nem sempre veio da mesma fonte: da captura vem do `[Código: …]`, exato da API; do
PRINT, vem da IA lendo o card. Num id de 19 dígitos ela erra quase sempre, e erra
DIFERENTE a cada leitura — medido na Blaze: 53 dos 55 códigos gravados por print têm
comprimento errado (17, 18, 20, 21), um saiu como `270625314492244...` e dois com espaço
no meio. O mesmo bilhete do Jonathan chegou a 5 linhas.

A coluna `codigo_ocr` carrega essa procedência e é ela que autoriza a Migração B' a ADOTAR
a linha quando o bilhete voltar pela captura, em vez de inserir a sexta.

O QUE ESTE ARQUIVO **NÃO** COBRE
--------------------------------
Aqui só se testa a FORMA do INSERT e da fórmula de confiança, lendo o fonte real com `ast`
(nada é reimplementado). O comportamento — adotar, recusar o ambíguo, não rebaixar o que já
foi confirmado — exige Postgres e vive em `tests/test_repository_db.py`, que só roda no CI.
Um teste de forma prova que a coluna está cabeada; não prova que ela decide certo.
"""
import ast
import io
import pathlib
import re

import pytest

_FONTE = pathlib.Path(__file__).resolve().parent.parent / "app" / "repository.py"
_SRC = io.open(_FONTE, encoding="utf-8").read()
_ARVORE = ast.parse(_SRC)


def _upsert():
    for no in ast.walk(_ARVORE):
        if isinstance(no, ast.AsyncFunctionDef) and no.name == "upsert_bilhetes":
            return no
    pytest.fail("`upsert_bilhetes` sumiu do repository.py")


def _chamadas_com_sql(trecho: str):
    """(sql, n_argumentos) de cada `conn.fetchrow(...)` do upsert cujo SQL contém `trecho`."""
    achadas = []
    for no in ast.walk(_upsert()):
        if not isinstance(no, ast.Call) or not no.args:
            continue
        alvo = no.func
        if not (isinstance(alvo, ast.Attribute) and alvo.attr in ("fetchrow", "execute")):
            continue
        primeiro = no.args[0]
        if isinstance(primeiro, ast.Constant) and isinstance(primeiro.value, str) \
                and trecho in primeiro.value:
            achadas.append((primeiro.value, len(no.args) - 1))
    return achadas


def test_o_insert_de_bilhetes_e_unico():
    chamadas = _chamadas_com_sql("INSERT INTO bilhetes")
    assert len(chamadas) == 1, (
        "há mais de um INSERT em `bilhetes` dentro do upsert — se um ganhar coluna e o "
        "outro não, a procedência do código passa a depender de qual caminho gravou")


def test_colunas_placeholders_e_argumentos_do_insert_batem():
    """O gate por LISTA, não por lembrança. Coluna nova cabeada pela metade não dá erro de
    sintaxe: o INSERT explode em runtime, no meio de um lote real, e o operador vê
    "0 exportadas". Aqui as três contagens são conferidas de uma vez.
    """
    sql, n_args = _chamadas_com_sql("INSERT INTO bilhetes")[0]
    corpo = sql.split("INSERT INTO bilhetes", 1)[1]
    colunas_txt = corpo[corpo.index("(") + 1:corpo.index(")")]
    colunas = [c.strip() for c in colunas_txt.split(",") if c.strip()]

    values = corpo[corpo.index("VALUES"):corpo.index("ON CONFLICT")]
    placeholders = {int(n) for n in re.findall(r"\$(\d+)", values)}

    assert "codigo_ocr" in colunas, "a procedência do código saiu do INSERT"
    assert len(colunas) == len(placeholders), (
        f"{len(colunas)} colunas para {len(placeholders)} placeholders")
    assert placeholders == set(range(1, len(colunas) + 1)), (
        f"os placeholders do VALUES não são 1..{len(colunas)}: {sorted(placeholders)}")
    assert n_args == len(colunas), (
        f"{len(colunas)} colunas no INSERT e {n_args} argumentos Python — "
        "o asyncpg levanta antes de qualquer SQL rodar")


@pytest.mark.parametrize("sql_trecho", ["INSERT INTO bilhetes", "UPDATE bilhetes SET"])
def test_confianca_do_codigo_e_um_AND_nos_dois_caminhos_de_escrita(sql_trecho):
    """A fórmula é `AND` de propósito, e vale nos DOIS caminhos: o ON CONFLICT e o UPDATE
    do fallback de `UniqueViolationError`. Basta uma leitura confiável para o código
    deixar de ser suspeito, e nenhuma leitura de print o rebaixa de volta.

    Um `COALESCE` aqui manteria TRUE para sempre (a linha nunca seria confirmada) e um
    `OR` faria um print colado depois desconfiar de um código que veio da API.
    """
    sqls = [s for s, _ in _chamadas_com_sql(sql_trecho)]
    assert sqls, f"não achei o `{sql_trecho}` do upsert"
    for sql in sqls:
        if "codigo_ocr" not in sql:
            continue
        atribuicoes = re.findall(r"codigo_ocr\s*=\s*([^,\n]+)", sql)
        assert atribuicoes, "codigo_ocr aparece mas não é atribuído"
        for expr in atribuicoes:
            assert " AND " in expr.upper(), (
                f"a confiança do código virou `{expr.strip()}` — ela só pode DESCER")
            assert "COALESCE" not in expr.upper() and " OR " not in expr.upper()


def test_a_adocao_por_ocr_exige_candidato_unico():
    """A Migração B (linha SEM código) faz `pop(0)` em qualquer candidato: a linha não tem
    identidade a perder. A B' tem de ser mais dura — o candidato dela CARREGA um código, e
    adotar o errado não duplica, sequestra a identidade de outro bilhete.
    """
    corpo = ast.get_source_segment(_SRC, _upsert()) or ""
    assert "ocr_no_banco" in corpo, "o índice da Migração B' sumiu"
    assert re.search(r"len\(cand_ocr\)\s*==\s*1", corpo), (
        "a trava de candidato único caiu — a B' passa a adotar no escuro")
    assert re.search(r"if not codigo_ocr:", corpo), (
        "o índice da B' deixou de ser condicionado ao lote confiável: print passa a "
        "adotar print, que é trocar uma incerteza por outra")
