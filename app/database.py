import os

import asyncpg

_pool: asyncpg.Pool | None = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS bilhetes (
    id               SERIAL PRIMARY KEY,
    casa             TEXT NOT NULL,
    parceiro         TEXT NOT NULL,
    assinatura       TEXT NOT NULL,
    data             TEXT,
    esporte          TEXT,
    tipster          TEXT,
    aposta           TEXT,
    descricao        TEXT,
    stake            TEXT,
    odd              TEXT,
    resultado        TEXT,
    extraction_state TEXT NOT NULL DEFAULT 'aberta'
                         CHECK (extraction_state IN ('aberta', 'resolvida')),
    copy_state       TEXT NOT NULL DEFAULT 'pendente'
                         CHECK (copy_state IN ('pendente', 'copiada')),
    confianca        REAL,
    criado_em        TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (casa, parceiro, assinatura)
);
"""


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        url = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
        _pool = await asyncpg.create_pool(url)
    return _pool


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
