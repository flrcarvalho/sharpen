"""Regressão de ORDENAÇÃO da Bet365 (feed newest-first → oldest→newest).

Guarda o bug do "embaralhamento em blocos": com >4 bilhetes, o caminho paralelo
invertia só a ORDEM DOS CHUNKS (não as linhas), e 6 bilhetes T1..T6 (newest-first)
saíam T5,T6,T3,T4,T1,T2 em vez de T6..T1. O fix é inversão determinística no nível
de LINHA (não depende do modelo inverter). Ver CASA_BET365 §2 + app/main.py.

Importa `app/main.py` — que cria o cliente Anthropic e importa `database.init_db`
no topo. O conftest já stuba `database` (só com get_pool) e `asyncpg`; aqui
completamos o stub com `init_db` e injetamos uma ANTHROPIC_API_KEY dummy antes do
import (nenhuma chamada de rede é feita — só a construção do cliente).
"""
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")

# conftest.py já inseriu app/ no sys.path e stubou `database` com get_pool.
# main.py faz `from database import init_db` → completamos o stub.
import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover - nunca chamado nos testes
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

import main  # noqa: E402


def _tsv(rows):
    """Monta um bloco ```tsv com header + linhas (cada `row` é o texto da coluna Descrição,
    o resto é preenchido de forma mínima só para ter 10 colunas)."""
    linhas = [main._TSV_HEADER]
    for r in rows:
        linhas.append(f"10/07/2026\tFutebol\t\tBet365\t\tML\t{r}\t100,00\t2,00\tW\t")
    return "```tsv\n" + "\n".join(linhas) + "\n```\n\n## Notas Críticas\nNenhuma"


def _descricoes(text):
    """Extrai a coluna Descrição (índice 6) das linhas de dados do bloco ```tsv."""
    return [r.split("\t")[6] for r in main._extract_tsv_rows(text)]


# ── _reverse_tsv_rows (caminho sequencial) ────────────────────────────────────

def test_reverse_tsv_rows_inverte_linhas_preserva_header_e_notas():
    entrada = _tsv(["T1", "T2", "T3", "T4", "T5", "T6"])
    saida = main._reverse_tsv_rows(entrada)
    assert _descricoes(saida) == ["T6", "T5", "T4", "T3", "T2", "T1"]
    # header e notas preservados
    assert "Data\tEsporte" in saida
    assert "## Notas Críticas" in saida


def test_reverse_tsv_rows_sem_bloco_tsv_no_op():
    txt = "sem bloco tsv aqui"
    assert main._reverse_tsv_rows(txt) == txt


def test_reverse_tsv_rows_um_bilhete_idempotente():
    entrada = _tsv(["T1"])
    assert _descricoes(main._reverse_tsv_rows(entrada)) == ["T1"]


# ── _combine_parallel_results(reverse_rows=True) (caminho paralelo) ────────────

def test_combine_paralelo_reverse_rows_desfaz_embaralhamento_em_blocos():
    # 6 bilhetes newest-first, chunkados 2 a 2 na ORDEM DE CAPTURA (idx crescente).
    # chunk0=[T1,T2] chunk1=[T3,T4] chunk2=[T5,T6]. Inversão no nível de linha → T6..T1.
    results = [
        (0, _tsv(["T1", "T2"]), {}),
        (1, _tsv(["T3", "T4"]), {}),
        (2, _tsv(["T5", "T6"]), {}),
    ]
    combinado, _tok, _idx = main._combine_parallel_results(results, reverse_rows=True)
    assert _descricoes(combinado) == ["T6", "T5", "T4", "T3", "T2", "T1"]


def test_combine_paralelo_sem_reverse_mantem_ordem():
    results = [
        (0, _tsv(["A", "B"]), {}),
        (1, _tsv(["C", "D"]), {}),
    ]
    combinado, _tok, _idx = main._combine_parallel_results(results)
    assert _descricoes(combinado) == ["A", "B", "C", "D"]


# ── _build_chunks: split por [Bilhete Bet365] ─────────────────────────────────

def test_build_chunks_bet365_split_por_marcador():
    texto = (
        "[Bilhete Bet365]\nT1 linha a\n\nlinha b interna\n"
        "[Bilhete Bet365]\nT2\n"
        "[Bilhete Bet365]\nT3\n"
        "[Bilhete Bet365]\nT4\n"
        "[Bilhete Bet365]\nT5\n"
    )
    base = [{"type": "text", "text": texto}]
    instr = {"type": "text", "text": "INSTR"}
    chunks = main._build_chunks(base, instr, casa_key="BET365")
    # 5 bilhetes → >1 chunk (paraleliza). A linha em branco interna do 1º bilhete NÃO
    # deve fragmentá-lo: o marcador é a fronteira, não o "\n\n".
    assert len(chunks) > 1
    corpo = "\n\n".join(
        b["text"] for ch in chunks for b in ch if b.get("text") != "INSTR"
    )
    assert corpo.count("[Bilhete Bet365]") == 5
    assert "linha b interna" in corpo  # 1º bilhete inteiro preservado
