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
    codigo_bilhete   TEXT,
    UNIQUE (casa, parceiro, assinatura)
);

-- Migração segura: adiciona coluna se ainda não existir
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS codigo_bilhete TEXT;

-- Normalizar nomes de casas: UPPERCASE → display name
UPDATE bilhetes  SET casa = 'Bet365'   WHERE casa = 'BET365';
UPDATE bilhetes  SET casa = 'Betano'   WHERE casa = 'BETANO';
UPDATE bilhetes  SET casa = 'Betfair'  WHERE casa = 'BETFAIR';
UPDATE bilhetes  SET casa = 'Pinnacle' WHERE casa = 'PINNACLE';
UPDATE bilhetes  SET casa = 'Superbet' WHERE casa = 'SUPERBET';
UPDATE parceiros SET casa = 'Bet365'   WHERE casa = 'BET365';
UPDATE parceiros SET casa = 'Betano'   WHERE casa = 'BETANO';
UPDATE parceiros SET casa = 'Betfair'  WHERE casa = 'BETFAIR';
UPDATE parceiros SET casa = 'Pinnacle' WHERE casa = 'PINNACLE';
UPDATE parceiros SET casa = 'Superbet' WHERE casa = 'SUPERBET';

CREATE TABLE IF NOT EXISTS parceiros (
    id        SERIAL PRIMARY KEY,
    casa      TEXT NOT NULL,
    nome      TEXT NOT NULL,
    arquivado BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (casa, nome)
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
