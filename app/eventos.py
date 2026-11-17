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


def _invalidar_caches(dono: str) -> None:
    """s459 (auditoria de 17/11, SERVIDOR P6): a invalidação dos caches por dono sai das
    rotas e vem do BANCO. Cada rota tinha de lembrar de derrubar o cache certo, e três que
    gravam tipster (`/bilhetes/tipster`, `DELETE /bilhetes`, `/bilhetes/restaurar`) não
    lembravam: a sugestão de tipster seguia velha por até 5 min. Todo escritor de `bilhetes`
    (rota, bot, script) dispara o `base_mudou`, então este ponto cobre todos."""
    try:
        import matcher
        matcher.invalidar(dono)
    except Exception:  # noqa: BLE001 — cache que não cai só demora o TTL dele
        pass
    try:
        import repository
        repository._CATEGORIAS_DONO.pop(dono, None)
    except Exception:  # noqa: BLE001
        pass


def _avisar_todos() -> None:
    """Depois de o LISTEN cair e voltar, o que mudou no vão não gerou aviso: toda tela
    aberta recarrega uma vez, e os caches de quem tem tela aberta caem (s459, SERVIDOR P7)."""
    for escopo, fila in list(_assinantes):
        for dono in escopo:
            _invalidar_caches(dono)
        try:
            fila.put_nowait(next(iter(escopo), ""))
        except asyncio.QueueFull:
            pass


def _on_notify(_conn, _pid, _canal, payload) -> None:
    """Callback do add_listener (roda no loop). payload = dono cuja base mudou."""
    _invalidar_caches(payload)
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
    ja_conectou = False
    while True:
        conn = None
        try:
            conn = await asyncpg.connect(dsn(), timeout=15)
            await conn.add_listener(_CANAL, _on_notify)
            logger.info("eventos: LISTEN %s ativo", _CANAL)
            if ja_conectou:
                _avisar_todos()           # o vão sem LISTEN não gerou aviso nenhum
            ja_conectou = True
            espera = 1.0
            while True:
                await asyncio.sleep(30)
                # s459 (SERVIDOR P7): com prazo. Sem ele, numa conexão TCP meio aberta o
                # ping esperava o keepalive do sistema (horas) e o app ficava surdo.
                await conn.execute("SELECT 1", timeout=10)
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
