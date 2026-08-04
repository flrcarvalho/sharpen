"""Barramento de eventos "base mudou" — a peça server-side do tempo real (s241).

Fluxo completo: trigger em `bilhetes` (database.py) → pg_notify('base_mudou',
<dono>) → escutar_banco() (conexão DEDICADA, viva a sessão inteira do app) →
filas dos assinantes (rota /eventos em main.py) → SSE → a casca (/app) chama o
loadData() dos iframes. O evento não carrega dado nenhum, só "mudou" — quem
busca o dado é o loadData de sempre.

Por que a conexão do LISTEN é dedicada e não vem do pool: LISTEN prende a
conexão para sempre, e com max_size=5 no pool um listener permanente comeria
20% da capacidade de requisições.
"""

import asyncio
import logging

import asyncpg

from database import dsn

logger = logging.getLogger("scanner.eventos")

_CANAL = "base_mudou"

# Assinantes vivos: (escopo de donos que interessam, fila de entrega). A fila é
# curta de propósito: descartar aviso com a fila cheia não perde nada, porque o
# aviso que já está lá força o mesmo reload que o descartado forçaria.
_assinantes: set[tuple[frozenset, asyncio.Queue]] = set()


def assinar(donos: list[str]) -> tuple[frozenset, asyncio.Queue]:
    """Registra um assinante para os donos do escopo. Devolve a entrada inteira —
    o chamador precisa dela para cancelar() no fim do stream."""
    entrada = (frozenset(donos), asyncio.Queue(maxsize=8))
    _assinantes.add(entrada)
    return entrada


def cancelar(entrada: tuple[frozenset, asyncio.Queue]) -> None:
    _assinantes.discard(entrada)


def _on_notify(_conn, _pid, _canal, payload) -> None:
    """Callback do add_listener (roda no loop). payload = dono cuja base mudou."""
    for escopo, fila in list(_assinantes):
        if payload in escopo:
            try:
                fila.put_nowait(payload)
            except asyncio.QueueFull:
                pass  # já há aviso pendente — o reload dele cobre este


async def escutar_banco() -> None:
    """Task de vida inteira do app (lifespan): mantém o LISTEN vivo, reconectando
    com backoff quando a conexão cai (restart do Postgres, rede). O ping de 30s
    existe porque conexão de LISTEN morta não levanta erro sozinha — sem ele o
    app ficaria surdo em silêncio, o mesmo modo de falha do polling do bot."""
    espera = 1.0
    while True:
        conn = None
        try:
            conn = await asyncpg.connect(dsn())
            await conn.add_listener(_CANAL, _on_notify)
            logger.info("eventos: LISTEN %s ativo", _CANAL)
            espera = 1.0
            while True:
                await asyncio.sleep(30)
                await conn.execute("SELECT 1")
        except Exception:
            logger.exception("eventos: listener caiu — reconectando em %.0fs", espera)
            await asyncio.sleep(espera)
            espera = min(espera * 2, 60.0)
        finally:
            if conn is not None:
                try:
                    await conn.close(timeout=5)
                except Exception:
                    pass
