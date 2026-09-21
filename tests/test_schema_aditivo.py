"""O schema migra sozinho a cada boot, e é isso que torna o rollback seguro (s374).

`init_db()` roda no `lifespan` do FastAPI (`main.py`) e executa o `SCHEMA_SQL` inteiro:
**todo deploy migra o banco**, sem passo manual. Isso é conveniente e tem um preço
escondido — se a migração deixar de ser idempotente, **voltar o código para de bastar**.
O banco fica à frente, a versão antiga não conhece a restrição nova, e o rollback que o
[`RUNBOOK_ROLLBACK.md`](../docs/RUNBOOK_ROLLBACK.md) promete falha na hora em que mais
se precisa dele.

Medido na s374: 18 `CREATE TABLE IF NOT EXISTS`, 24 `ADD COLUMN IF NOT EXISTS`, 10
índices com guarda, um `DROP COLUMN IF EXISTS` de coluna morta (`bilhetes.copy_state`),
dois `DROP CONSTRAINT IF EXISTS` que trocam a unique antiga pela versão com `dono`
(migração multiusuário), e **zero** `SET NOT NULL`, `DROP TABLE`, `ALTER COLUMN` ou DDL
sem guarda.

Este arquivo trava essa propriedade. Ele NÃO proíbe migração destrutiva para sempre:
proíbe que ela entre **em silêncio**. Quem precisar de uma muda o `SCHEMA_SQL`, vê o CI
quebrar aqui, e aí escreve no runbook o caminho de volta daquele deploy específico.
É o mesmo desenho do prazo de validade em `test_modelo_e_preco.py`: o gate existe para
forçar a conversa, não para impedir a mudança.

**O que este teste NÃO cobre:** se a migração é *correta*, se o índice é o certo, e DDL
que chegue por script fora do `SCHEMA_SQL` (`scripts/*.py` roda à mão, com olho humano,
e não entra no caminho do deploy).

Provado por mutação: **8/8 detectadas**, sobre CÓPIAS via `ALVO_DATABASE`.
"""
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
# `ALVO_DATABASE` existe para a prova por MUTAÇÃO rodar sobre uma CÓPIA. Mutar o
# `database.py` de verdade e restaurar depois é como se deixa uma mutação gravada no
# repo — aconteceu na s371, com duas baterias concorrentes. Em CI e no uso normal a
# variável não existe e o gate lê o arquivo real.
DATABASE_PY = Path(os.environ.get("ALVO_DATABASE") or (RAIZ / "app" / "database.py"))
MAIN_PY = RAIZ / "app" / "main.py"
RUNBOOK = RAIZ / "docs" / "RUNBOOK_ROLLBACK.md"

FONTE = DATABASE_PY.read_text(encoding="utf-8")

# Formas que quebram o rollback: a versão ANTIGA do código volta e encontra um banco
# que ela não sabe usar. Cada uma com o porquê, porque o CI vai citar isto.
DESTRUTIVAS = {
    r"\bSET\s+NOT\s+NULL\b":
        "coluna vira obrigatória e o INSERT da versão antiga, que não a preenche, falha",
    r"\bDROP\s+TABLE\b":
        "tabela some e a versão antiga ainda a consulta",
    r"\bALTER\s+COLUMN\s+\w+\s+TYPE\b":
        "o tipo muda debaixo da versão antiga",
    r"\bTRUNCATE\b":
        "apaga dado no boot; num rollback isso roda de novo",
}

# DDL sem guarda não é destrutiva, mas quebra o boot no SEGUNDO deploy (o objeto já
# existe) — ou seja, quebra exatamente o redeploy que o rollback usa.
#
# `DROP … IF EXISTS` entra aqui, e não em DESTRUTIVAS, porque este repo troca restrição
# assim de propósito: os dois `DROP CONSTRAINT IF EXISTS` do schema derrubam a unique
# pré-multiusuário para recriá-la com `dono` junto. O que o gate exige é a GUARDA.
SEM_GUARDA = [
    (r"\bADD\s+COLUMN\s+(?!IF\s+NOT\s+EXISTS)", "ADD COLUMN sem IF NOT EXISTS"),
    (r"\bCREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)", "CREATE TABLE sem IF NOT EXISTS"),
    (r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!IF\s+NOT\s+EXISTS)",
     "CREATE INDEX sem IF NOT EXISTS"),
    (r"\bDROP\s+CONSTRAINT\s+(?!IF\s+EXISTS)", "DROP CONSTRAINT sem IF EXISTS"),
    (r"\bDROP\s+COLUMN\s+(?!IF\s+EXISTS)", "DROP COLUMN sem IF EXISTS"),
]


def _schema_sql() -> str:
    """O conteúdo do `SCHEMA_SQL`, sem os comentários SQL (`-- …`).

    ⚠️ Esta função já foi um FALSO VERDE, e o jeito como ela falhou vale mais que ela.
    A primeira versão varria o arquivo INTEIRO e tirava docstrings de Python para não
    acusar comentário como DDL. Só que o `SCHEMA_SQL` **é** uma triple-quoted string: o
    limpador apagava o schema inteiro, o gate passava a inspecionar uma string vazia, e
    os dez testes ficavam verdes por não olharem para nada. **8 mutações, 8 escaparam.**

    Quem pegou foi a bateria de mutação, que é exatamente o que o `CLAUDE.md` promete:
    "teste verde não é teste que detecta". Por isso o `test_o_gate_esta_mesmo_lendo_o_schema`
    existe logo abaixo — o piso de tamanho é a rede contra esta família inteira.
    """
    m = re.search(r'SCHEMA_SQL\s*=\s*"""(.*?)"""', FONTE, re.DOTALL)
    if not m:
        pytest.fail(
            'não achei `SCHEMA_SQL = """…"""` no database.py. O gate de rollback não '
            "tem o que ler — conserte a extração antes de confiar no verde."
        )
    return re.sub(r"--[^\n]*", "", m.group(1))


def test_o_gate_esta_mesmo_lendo_o_schema():
    """Rede contra o falso verde: o gate precisa estar olhando para ALGO.

    Piso de tamanho e presença das formas que sabidamente existem. Sem isto, qualquer
    mudança que quebre a extração (renomear a constante, trocar aspas, partir o schema
    em dois) transforma os testes abaixo em decoração silenciosa.
    """
    schema = _schema_sql()
    assert len(schema) > 10_000, (
        f"o SCHEMA_SQL extraído tem só {len(schema)} chars. Ou ele encolheu de verdade, "
        "ou a extração quebrou e os gates abaixo pararam de olhar para o schema."
    )
    assert schema.count("CREATE TABLE IF NOT EXISTS") >= 15, (
        "o schema extraído não tem as tabelas esperadas — a extração lê a coisa errada."
    )


@pytest.mark.parametrize("padrao,porque", sorted(DESTRUTIVAS.items()))
def test_a_migracao_de_boot_nao_tem_ddl_destrutiva(padrao, porque):
    """DDL destrutiva no `SCHEMA_SQL` quebra a promessa do runbook de rollback."""
    achados = re.findall(padrao, _schema_sql(), re.IGNORECASE)
    assert not achados, (
        f"`{padrao}` apareceu no SCHEMA_SQL ({len(achados)}x): {porque}.\n"
        "Voltar o código deixa de bastar — o banco fica à frente da versão antiga.\n"
        "Se a migração é mesmo necessária: tire um backup provado "
        "(`python scripts/backup_postgres.py --provar`), escreva o caminho de volta "
        "em docs/RUNBOOK_ROLLBACK.md e só então libere este gate."
    )


@pytest.mark.parametrize("padrao,rotulo", SEM_GUARDA)
def test_toda_ddl_de_boot_e_idempotente(padrao, rotulo):
    """O boot roda a CADA deploy. DDL sem guarda quebra no segundo.

    E o segundo boot é exatamente o redeploy do rollback.
    """
    achados = re.findall(padrao, _schema_sql(), re.IGNORECASE)
    assert not achados, (
        f"{rotulo} no SCHEMA_SQL ({len(achados)}x). O `init_db()` roda a cada boot; "
        "sem a guarda, o segundo deploy falha no arranque — inclusive o redeploy que "
        "o rollback usa."
    )


def test_o_init_db_continua_no_arranque():
    """Se o `init_db` sair do `lifespan`, a migração passa a ser manual.

    Não é pior nem melhor: é OUTRO procedimento, e o runbook de rollback descreve este.
    O gate existe para o runbook não descrever um mundo que deixou de existir.
    """
    main = MAIN_PY.read_text(encoding="utf-8")
    i = main.index("async def lifespan(")
    assert "await init_db()" in main[i:i + 800], (
        "`init_db()` saiu do lifespan. A migração deixou de ser automática no deploy, "
        "e docs/RUNBOOK_ROLLBACK.md descreve o comportamento antigo."
    )


def test_o_runbook_de_rollback_existe_e_tem_o_registro_de_ensaio():
    """Procedimento de emergência nunca executado é ficção.

    A tabela de ensaios é o que separa "está escrito" de "a gente sabe que funciona".
    """
    txt = RUNBOOK.read_text(encoding="utf-8")
    assert "### Registro dos ensaios" in txt, (
        "o RUNBOOK_ROLLBACK perdeu a tabela de registro de ensaios."
    )
    assert "railway down" in txt, (
        "o runbook precisa manter o aviso sobre `railway down`, que REMOVE a "
        "implantação em vez de voltar para a anterior."
    )
