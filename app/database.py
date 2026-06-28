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
    archived         BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (casa, parceiro, assinatura)
);

-- Migrações seguras: adicionam colunas se ainda não existirem
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS codigo_bilhete TEXT;
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Multiusuário: coluna dono. Registros pré-existentes pertencem ao dono do projeto ('Feca').
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS dono TEXT NOT NULL DEFAULT 'Feca';

-- Troca a unicidade para incluir o dono: cada usuário tem seu próprio espaço.
-- (sem isto, dois usuários não poderiam ter o mesmo casa+parceiro+assinatura)
DO $$
BEGIN
    ALTER TABLE bilhetes DROP CONSTRAINT IF EXISTS bilhetes_casa_parceiro_assinatura_key;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'bilhetes_dono_casa_parceiro_assinatura_key'
    ) THEN
        ALTER TABLE bilhetes
            ADD CONSTRAINT bilhetes_dono_casa_parceiro_assinatura_key
            UNIQUE (dono, casa, parceiro, assinatura);
    END IF;
END$$;

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

-- Multiusuário: dono dos parceiros (mesma lógica de bilhetes).
ALTER TABLE parceiros ADD COLUMN IF NOT EXISTS dono TEXT NOT NULL DEFAULT 'Feca';

DO $$
BEGIN
    ALTER TABLE parceiros DROP CONSTRAINT IF EXISTS parceiros_casa_nome_key;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'parceiros_dono_casa_nome_key'
    ) THEN
        ALTER TABLE parceiros
            ADD CONSTRAINT parceiros_dono_casa_nome_key
            UNIQUE (dono, casa, nome);
    END IF;
END$$;

-- Origem do registro: extracao (IA) | sync (Polymarket API) | import (migração da planilha).
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS origem TEXT NOT NULL DEFAULT 'extracao';

-- Tipster atribuído a POSIÇÕES ATIVAS da Polymarket (dashboard ao vivo).
-- Vive separado de `bilhetes` (que só guarda apostas resolvidas/exportáveis);
-- chave = código do bilhete (conditionId/__i). Carregado p/ a grade quando resolve.
CREATE TABLE IF NOT EXISTS polymarket_ativos_tipster (
    dono          TEXT NOT NULL,
    codigo        TEXT NOT NULL,
    tipster       TEXT NOT NULL DEFAULT '',
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (dono, codigo)
);
"""


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        url = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
        _pool = await asyncpg.create_pool(
            url,
            min_size=1,
            max_size=5,
            max_inactive_connection_lifetime=60,
        )
    return _pool


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)
