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

-- Aposentado o fluxo de copiar/marcar para a planilha (sessão 89): a coluna
-- copy_state ('pendente'|'copiada') não é mais usada por nenhum código. DROP é
-- metadados no Postgres (rápido, não reescreve a tabela) e idempotente (IF EXISTS).
ALTER TABLE bilhetes DROP COLUMN IF EXISTS copy_state;

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

-- Stake original em USD (só Polymarket: o valor que saiu da conta, antes da conversão
-- USD→BRL). NULL para casas em R$ nativo. Número cru; a máscara é responsabilidade da UI.
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS stake_usd REAL;

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

-- Log de uso de tokens da API Anthropic por extração (observabilidade de custo).
-- Uma linha por chamada a /extrair que consumiu modelo. custo_usd é calculado no
-- ato (preço por modelo × tokens) — congela o custo mesmo se o preço mudar depois.
CREATE TABLE IF NOT EXISTS uso_tokens (
    id           SERIAL PRIMARY KEY,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dono         TEXT NOT NULL,
    casa         TEXT,
    modelo       TEXT,
    chunks       INT NOT NULL DEFAULT 1,
    n_itens      INT NOT NULL DEFAULT 0,
    input        BIGINT NOT NULL DEFAULT 0,
    output       BIGINT NOT NULL DEFAULT 0,
    cache_read   BIGINT NOT NULL DEFAULT 0,
    cache_write  BIGINT NOT NULL DEFAULT 0,
    custo_usd    REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS uso_tokens_dono_criado ON uso_tokens (dono, criado_em);

-- Correções do usuário (Fase 1 do plano worldwide). Cada vez que alguém edita um
-- campo de um bilhete, registramos rótulo→antigo→novo. É a SEMENTE do cache
-- aprendido (Fase 3): por casa, o que a extração errou e o humano corrigiu.
-- Append-only; nunca altera o bilhete. Ver docs/PLANO_EXTRACAO_WORLDWIDE.md.
CREATE TABLE IF NOT EXISTS correcoes (
    id             BIGSERIAL PRIMARY KEY,
    bilhete_id     BIGINT,
    dono           TEXT NOT NULL,
    casa           TEXT,
    campo          TEXT NOT NULL,
    valor_anterior TEXT,
    valor_novo     TEXT,
    descricao      TEXT,
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS correcoes_casa_campo ON correcoes (casa, campo);

-- Metadados de casa por dono (Fase 2): domínio para o favicon das casas novas
-- adicionadas em autosserviço. O front (faviconUrl) resolve o ícone pelo domínio
-- via Google S2 e aplica o chip padrão do sistema (REFERENCIA_CHIPS_CASAS.md).
CREATE TABLE IF NOT EXISTS casas_meta (
    dono          TEXT NOT NULL,
    casa          TEXT NOT NULL,
    dominio       TEXT,
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (dono, casa)
);

-- ── Tipsters — Perfil de Tipster (Fatia 0) ────────────────────────────────────
-- Dá existência de verdade ao tipster, que hoje é só texto livre em bilhetes.tipster.
-- Chave (dono, nome): mesmo tipster em N casas = UM registro; unificação por nome
-- SEMPRE (decisão do Feca, 2026-07-14). Quer separar? Nomes distintos ("João 365").
-- Espelha `parceiros`. Os campos de info (casas/mercados/obs) nascem vazios → tipster
-- "incompleto" (sinal (i) no onboarding). Ver docs/PLANO_TIPSTER.md.
CREATE TABLE IF NOT EXISTS tipsters (
    id        SERIAL PRIMARY KEY,
    nome      TEXT NOT NULL,
    dono      TEXT NOT NULL DEFAULT 'Feca',
    casas     TEXT,
    mercados  TEXT,
    obs       TEXT,
    arquivado BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (dono, nome)
);

-- Backfill idempotente: todo tipster distinto já presente nos bilhetes vira registro
-- (incompleto). Roda a cada boot; ON CONFLICT DO NOTHING → nunca duplica nem
-- ressuscita um tipster que foi arquivado à mão.
INSERT INTO tipsters (dono, nome)
SELECT DISTINCT dono, tipster FROM bilhetes
WHERE tipster IS NOT NULL AND tipster <> ''
ON CONFLICT (dono, nome) DO NOTHING;
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
