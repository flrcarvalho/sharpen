"""Regressão do TETO de bilhetes por chunk (`_BILHETES_POR_CHUNK`, s301).

O bug: `_MAX_CHUNKS = 4` era o único controle do caminho de TEXTO, e ele fixa o NÚMERO de
chunks, não o tamanho. Lote grande não virava mais chunks — virava chunks mais gordos. Os 91
bilhetes de uma captura 1xBet viravam 4 chunks de 23, e um chunk de 23 levou 272s e 17.500
tokens de saída (contra 26,5s e 1.214 tokens com 6). A extração estourava o timeout de borda
antes do evento `done`: o tester via "Processando… (246s)" e um erro de rede.

O que estes testes travam:
  • acima de ~24 bilhetes o chunk é APERTADO até `_BILHETES_POR_CHUNK`;
  • o teto NUNCA reduz o número de chunks (lote pequeno segue no paralelo — agrupá-lo num
    chunk só o mandaria para o `_stream_sequential`, onde a Superbet-texto sai na ordem
    trocada SEM ERRO NENHUM; é o aviso que já estava escrito no topo do `main.py`);
  • o fallback frágil "\n\n" (casa sem marcador de bilhete) NÃO é apertado — lá um "bloco" é
    um parágrafo, e apertar multiplicaria as fronteiras que cortam bilhete no meio;
  • nenhum bilhete se perde nem é partido entre dois chunks.

NÃO cobre: o tempo/custo real da chamada (isso é medição contra a API, não teste), nem a
escolha do número 6 — o valor foi medido na s301 e vive comentado no `main.py`.
"""
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")

# conftest.py já inseriu app/ no sys.path e stubou `database` com get_pool.
import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover - nunca chamado nos testes
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

import main  # noqa: E402

_INSTR = {"type": "text", "text": "INSTRUCAO"}


def _texto_marcado(n):
    """`n` bilhetes no formato do robô: `[Código: …]` como 1ª linha, corpo com linha em
    branco INTERNA (é o que prova que a fronteira é o marcador, não o "\\n\\n")."""
    return "\n\n".join(
        f"[Código: 161{i:05d}]\nStake: 180,00\n\nOdd: 7,7224\nStatus: Perdeu → L"
        for i in range(n)
    )


def _chunks(texto, casa="1XBET"):
    return main._build_chunks([{"type": "text", "text": texto}], _INSTR, casa)


def _por_chunk(chunks):
    """Nº de bilhetes em cada chunk (conta os marcadores, ignorando o bloco de instrução)."""
    return [
        sum(b["text"].count("[Código: ") for b in ch if b is not _INSTR)
        for ch in chunks
    ]


def test_lote_grande_aperta_o_chunk_ate_o_teto():
    """91 bilhetes (a captura real da 1xBet) → 16 chunks de ≤6, não 4 de 23."""
    chunks = _chunks(_texto_marcado(91))
    assert _por_chunk(chunks) == [6] * 15 + [1]
    assert len(chunks) == 16
    assert max(_por_chunk(chunks)) <= main._BILHETES_POR_CHUNK


def test_nenhum_bilhete_se_perde_nem_e_partido():
    """Cada código aparece exatamente uma vez, e o corpo do bilhete vai junto com ele."""
    chunks = _chunks(_texto_marcado(91))
    corpo = "\n\n".join(b["text"] for ch in chunks for b in ch if b is not _INSTR)
    assert corpo.count("[Código: ") == 91
    for i in range(91):
        assert corpo.count(f"[Código: 161{i:05d}]") == 1
    # A linha em branco interna não pode ter fragmentado nenhum bilhete: se tivesse, haveria
    # mais blocos que marcadores.
    assert corpo.count("Status: Perdeu") == 91


def test_teto_nunca_reduz_o_numero_de_chunks():
    """Lote pequeno fatia exatamente como antes do teto — nada pode cair no sequencial.

    Sem esta garantia, um "piso de bilhetes" mandaria lote de 2–6 para o `_stream_sequential`,
    cujo `seq_reverse` NÃO inclui a Superbet: a Superbet-texto sairia na ordem trocada, sem
    erro. É o aviso que já estava no topo do `main.py`.
    """
    # (bilhetes, nº de chunks esperado) — o comportamento histórico do `_MAX_CHUNKS`.
    for n, esperado in [(2, 2), (3, 3), (4, 4), (5, 3), (8, 4), (24, 4)]:
        chunks = _chunks(_texto_marcado(n))
        assert len(chunks) == esperado, f"{n} bilhetes → {len(chunks)} chunks (esperado {esperado})"
        assert len(chunks) > 1, f"{n} bilhetes caíram num chunk só → iria para o sequencial"


def test_fallback_sem_marcador_nao_e_apertado():
    """Casa sem marcador de bilhete fatia por "\\n\\n" — ali um bloco é um PARÁGRAFO.

    Apertar esse caminho até 6 multiplicaria as fronteiras que cortam bilhete no meio (100
    parágrafos passariam de 3 cortes para 16). Segue em `_MAX_CHUNKS`.
    """
    texto = "\n\n".join(f"paragrafo {i}" for i in range(100))
    chunks = _chunks(texto, casa="CASADESCONHECIDA")
    assert len(chunks) == main._MAX_CHUNKS


def test_xls_pinnacle_tambem_e_apertado():
    """`=== Aposta ID` é fronteira real de bilhete (parser da Pinnacle) → entra no teto."""
    texto = "\n".join(
        f"=== Aposta ID {3089350000 + i} ===\nData: 21/07/2026\nStake: 100,00" for i in range(30)
    )
    chunks = _chunks(texto, casa="PINNACLE")
    assert len(chunks) == 5
    assert max(ch[0]["text"].count("=== Aposta ID") for ch in chunks) <= main._BILHETES_POR_CHUNK
