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

-- Normalizar nomes de casas em parceiros: UPPERCASE → display name.
-- (DEPOIS do CREATE TABLE parceiros — senão, em banco vazio, o UPDATE roda antes da
--  tabela existir e faz rollback de todo o SCHEMA_SQL, travando o init de zero.)
UPDATE parceiros SET casa = 'Bet365'   WHERE casa = 'BET365';
UPDATE parceiros SET casa = 'Betano'   WHERE casa = 'BETANO';
UPDATE parceiros SET casa = 'Betfair'  WHERE casa = 'BETFAIR';
UPDATE parceiros SET casa = 'Pinnacle' WHERE casa = 'PINNACLE';
UPDATE parceiros SET casa = 'Superbet' WHERE casa = 'SUPERBET';

-- Origem do registro: extracao (IA) | sync (Polymarket API) | import (migração da planilha).
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS origem TEXT NOT NULL DEFAULT 'extracao';

-- Stake original em USD (só Polymarket: o valor que saiu da conta, antes da conversão
-- USD→BRL). NULL para casas em R$ nativo. Número cru; a máscara é responsabilidade da UI.
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS stake_usd REAL;

-- Procedência do RÓTULO de tipster (Fase 0 do PLANO_INTELIGENCIA_TIPSTER): humano |
-- sugerido | telegram | importado | extracao. NULL = legado (linha anterior ao rastreio).
-- Separa verdade (humano/import/telegram) de chute do sistema (sugerido) → o treino
-- futuro nunca aprende da própria sugestão. NÃO entra em _SIG_COLS (não mexe na assinatura).
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS origem_tipster TEXT;

-- Índices da tabela mais quente (bilhetes). Sem eles, toda home do dashboard faz
-- seq scan + sort em memória por dono, e o pré-dedup por código varre sem índice.
-- IF NOT EXISTS = idempotente (roda a cada boot sem recriar). A dedup por assinatura
-- (dono, casa, parceiro, assinatura) já é servida pelo índice UNIQUE — não repetir aqui.
--   • feed/listagem: SELECT ... WHERE dono=$ ORDER BY criado_em, id
CREATE INDEX IF NOT EXISTS idx_bilhetes_dono_criado
    ON bilhetes (dono, criado_em, id);
--   • pré-dedup por código do bilhete (parcial: só as linhas que têm código)
CREATE INDEX IF NOT EXISTS idx_bilhetes_dono_codigo
    ON bilhetes (dono, codigo_bilhete) WHERE codigo_bilhete IS NOT NULL;

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

-- Fase B (esqueleto da auto-atribuição): campos que vão ALIMENTAR a detecção do tipster
-- na extração (ainda de gaveta — ver repository.sugerir_tipster). Aditivo e idempotente.
--   stake_min/stake_max = faixa de stake típica (R$); bilhete fora da faixa perde pontos.
--   apelidos            = marca d'água / apelidos no print (CSV); o sinal MAIS forte.
ALTER TABLE tipsters ADD COLUMN IF NOT EXISTS stake_min REAL;
ALTER TABLE tipsters ADD COLUMN IF NOT EXISTS stake_max REAL;
ALTER TABLE tipsters ADD COLUMN IF NOT EXISTS apelidos  TEXT;
-- Dica de stake: nota livre sobre a gestão de stake do tipster (ex.: "unidade 500, mas
-- passo 501/500,01 pra facilitar a leitura"). Separada de `obs` (observações gerais).
ALTER TABLE tipsters ADD COLUMN IF NOT EXISTS dica_stake TEXT;
-- Esportes principais (CSV): mais um sinal de identificação (um tipster só de tênis se
-- destaca na hora). Alimenta o "Sharpen sugere" e a futura auto-atribuição.
ALTER TABLE tipsters ADD COLUMN IF NOT EXISTS esportes TEXT;

-- Backfill idempotente: todo tipster distinto já presente nos bilhetes vira registro
-- (incompleto). Roda a cada boot; ON CONFLICT DO NOTHING → nunca duplica nem
-- ressuscita um tipster que foi arquivado à mão.
INSERT INTO tipsters (dono, nome)
SELECT DISTINCT dono, tipster FROM bilhetes
WHERE tipster IS NOT NULL AND tipster <> ''
ON CONFLICT (dono, nome) DO NOTHING;

-- ── Escada de valor-da-unidade no tempo (Perfil de Tipster, Fatia 1) ──────────
-- Cada linha é um DEGRAU: "a partir de vigente_desde, 1u do tipster vale `valor`
-- reais". A unidade é uma VIEW DERIVADA (como o P/L): NÃO se guarda "quantas u tinha
-- a aposta" — guarda-se só esta escada, e u = P/L_R$ ÷ valor_vigente_na_data. Assim
-- corrigir stake retroativa recalcula o histórico de graça. Chave por NOME (igual
-- bilhetes.tipster); renomear_tipster propaga. Ver docs/PLANO_TIPSTER.md §P1.
CREATE TABLE IF NOT EXISTS tipster_unidade (
    id            SERIAL PRIMARY KEY,
    dono          TEXT NOT NULL,
    tipster       TEXT NOT NULL,
    vigente_desde TEXT NOT NULL,   -- ISO YYYY-MM-DD: data em que este valor passa a valer
    valor         REAL NOT NULL,   -- R$ por 1 unidade a partir de vigente_desde (> 0)
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (dono, tipster, vigente_desde)
);

-- ── Casa dedicada (auto-atribuição por casa-feudo) ────────────────────────────
-- Muitas casas de nicho são MONOGÂMICAS na operação do dono: na BETesporte é sempre
-- Peixe, independente do valor. É um sinal FORTE que o matcher subusava (casa valia só
-- +5, afogado). Aqui o dono declara casa→tipster(s): 1 dono = crava; 2 = restringe o
-- candidato e o stake desempata; 'multi' = casa compartilhada (ignora). Linha ausente =
-- casa ainda não curada. A tela nasce pré-preenchida com a SUGESTÃO derivada da pureza
-- observada (só rótulos humanos, sem 'sugerido' → sem circularidade); o dono só confirma.
-- NÃO plugado no matcher na Etapa 1 (só o registro + curadoria). Ver STATUS s148.
CREATE TABLE IF NOT EXISTS casa_config (
    dono          TEXT NOT NULL,
    casa          TEXT NOT NULL,
    modo          TEXT NOT NULL DEFAULT 'dedicada',   -- 'dedicada' | 'multi'
    tipsters      TEXT NOT NULL DEFAULT '',           -- CSV de 1-2 nomes quando modo='dedicada'
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (dono, casa)
);
-- Procedência da curadoria da casa (tag "Origem" da tela): 'sharpen' = aplicada da sugestão
-- do sistema; 'custom' = o dono editou à mão. Qualquer edição de atribuição/tipster marca
-- 'custom'. Aditivo; linha nova default 'custom' (só se cria linha ao salvar = ação humana).
ALTER TABLE casa_config ADD COLUMN IF NOT EXISTS origem TEXT NOT NULL DEFAULT 'custom';

-- ── Custos por dono (Custo por Tipster + Custos Gerais) ───────────────────────
-- Migra o custo de assinatura/serviço (Gestão › Custos) do localStorage do
-- navegador para o Postgres, por dono. Antes vivia SÓ em localStorage (chaves
-- GLOBAIS custoTipsterData/custoGeralData, sem dono) → não sincronizava entre
-- aparelhos e não tinha backup: o que era digitado num PC sumia ao abrir noutro
-- (incidente Jonathan, 2026-07-19 — abriu noutra máquina e viu tudo zerado menos
-- um tipster). Blob único por dono: custo_tipster = {tipster:{"YYYY-MM":"valor"}};
-- custo_geral = [{id,tipo,values:{"YYYY-MM":"valor"}}]. O front sempre grava o
-- estado completo (como fazia no localStorage). Semeado UMA vez pela página
-- /dashboard/importar-custos.html (lê o localStorage do PC certo e sobe). O
-- dashboard nunca cria este registro sozinho quando há custo legado no navegador
-- (evita oficializar cópia parcial do aparelho errado). Ver STATUS s165.
CREATE TABLE IF NOT EXISTS custo_store (
    dono          TEXT PRIMARY KEY,
    custo_tipster JSONB NOT NULL DEFAULT '{}'::jsonb,
    custo_geral   JSONB NOT NULL DEFAULT '[]'::jsonb,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
