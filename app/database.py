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

-- Estrutura de SISTEMA (s265): `3 x Duplas`, `4 x Triplas`, Trixie… A odd de um sistema é
-- a MÉDIA das linhas, não o produto (MASTER_RESULTADO §7.3), mas nada no banco dizia que a
-- linha era sistema: `Aposta` é a categoria canônica (`Múltipla`) e a descrição de um
-- `3 x Duplas` é IDÊNTICA à da tripla das mesmas seleções. Sem estas colunas não dá para
-- varrer o histórico atrás de odd de sistema errada, nem medir o volume desse tipo de aposta
-- — e ele cresce. NULL = não é sistema (o caso normal). São dados de ESTRUTURA, imutáveis:
-- não entram na assinatura (`_SIG_COLS`) e o UPSERT só os preenche, nunca os apaga, então
-- re-capturar bilhete antigo faz backfill sem violar o congelamento financeiro.
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS sistema TEXT;
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS sistema_linhas INTEGER;

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
    custo_conta   JSONB NOT NULL DEFAULT '{}'::jsonb,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- custo_conta: custo por conta/fornecedor {fornecedor||casa: numero} (antes só no
-- localStorage dash_custos_v2::<dono>, mesma fragilidade cross-device do CT/CG). ALTER
-- p/ a custo_store que JÁ existe em prod desde s165. Ver STATUS s167 / [[custo_conta_isolado_por_dono]].
ALTER TABLE custo_store ADD COLUMN IF NOT EXISTS custo_conta JSONB NOT NULL DEFAULT '{}'::jsonb;

-- ── Lixeira de contas excluídas (rede de segurança da exclusão) ───────────────
-- A exclusão de conta é HARD DELETE: apaga a linha em `parceiros` e TODOS os
-- bilhetes dela. Esta tabela guarda o snapshot por 7 dias para o caso de
-- arrependimento (restauração manual via scripts/restaurar_conta_lixeira.py).
--
-- Por que uma tabela separada e NÃO um soft-delete (coluna `excluido` em
-- bilhetes): soft-delete obrigaria a filtrar em dezenas de queries espalhadas
-- (dashboard, KPIs, dedup, export, P/L) e UM esquecimento vira lucro fantasma —
-- a mesma família de bug do UPSERT meio-atualizado documentada no CLAUDE.md.
-- Aqui nada mais no sistema lê esta tabela: acoplamento zero, por construção.
--
-- Por que o snapshot é JSONB e não uma tabela-espelho de `bilhetes`: a `bilhetes`
-- ganha coluna de tempos em tempos via ALTER TABLE, e um espelho pararia de
-- copiar a coluna nova em silêncio. `to_jsonb(b.*)` copia a linha inteira, seja
-- ela qual for hoje ou amanhã — imune a drift de schema.
--
-- Purga preguiçosa (sem cron): toda exclusão apaga antes o que passou de 7 dias.
-- Mesmo padrão da poda de tipster órfão em list_tipsters_cadastro().
CREATE TABLE IF NOT EXISTS lixeira_contas (
    id           BIGSERIAL PRIMARY KEY,
    dono         TEXT NOT NULL,
    casa         TEXT NOT NULL,
    parceiro     TEXT NOT NULL,
    arquivado    BOOLEAN NOT NULL DEFAULT FALSE,   -- estado da conta no momento da exclusão
    n_bilhetes   INT NOT NULL DEFAULT 0,
    bilhetes     JSONB NOT NULL DEFAULT '[]'::jsonb,
    excluido_em  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS lixeira_contas_dono_excluido
    ON lixeira_contas (dono, excluido_em);

-- ── Usuários (Fase 1 do PLANO_MULTIUSUARIO_2026 — Deploy A) ───────────────────
-- Futura fonte de verdade da identidade (hoje: dicts hardcoded em auth.py +
-- env vars SENHA_<USER>_HASH). NESTA fase a tabela só é criada e semeada
-- (seed_usuarios) para inspeção — NENHUM código de auth a lê ainda; a virada
-- de chave é o Deploy B. `username` = coluna `dono` das tabelas de dados
-- (integridade lógica, sem FK — dono órfão de importação não pode travar).
--   status  → "aberto com aprovação": cadastro novo nasce 'pendente' até o
--             admin aprovar; login/sessão só passam com 'ativo' (é isto que
--             resolve o C3 da auditoria: desativar = revogar sessão na hora).
--   role    → 'admin' aprova cadastros (substituirá o hardcode "Feca").
--   parent_owner → substitui o dict OPERADORES (NULL = dono).
--   planilha_url → substitui PLANILHAS_AO_VIVO ('' /NULL = lê do Postgres).
--   senha_hash NULL → conta que loga só via social (Google/Telegram, Fase 3).
CREATE TABLE IF NOT EXISTS usuarios (
    username      TEXT PRIMARY KEY,
    senha_hash    TEXT,
    email         TEXT UNIQUE,
    nome          TEXT,
    status        TEXT NOT NULL DEFAULT 'pendente'
                     CHECK (status IN ('ativo','pendente','suspenso')),
    role          TEXT NOT NULL DEFAULT 'user'
                     CHECK (role IN ('admin','user')),
    parent_owner  TEXT,
    planilha_url  TEXT,
    google_sub    TEXT UNIQUE,
    telegram_id   TEXT UNIQUE,
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- `bot_habilitado` (s273) — o bot de tipster pode planilhar NA BASE DESTE dono.
-- Antes disso o bot fazia login COMO o tipster, então cada tipster novo obrigava
-- a guardar a senha DELE numa env var do Railway (eram três: Só Chutes, Zora e
-- Rei do Criquete). Não escalava e ainda punha credencial de terceiro sob nossa
-- guarda. Agora o bot usa UM token de serviço (SHARPEN_BOT_TOKEN, criado uma vez)
-- e diz em qual dono está escrevendo pelo header X-Sharpen-Dono; este flag é a
-- autorização, e é um botão no painel /admin. Tipster novo = aprovar + ligar.
-- Nasce FALSE de propósito: conta aprovada não ganha escrita de robô de brinde.
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS bot_habilitado BOOLEAN NOT NULL DEFAULT FALSE;

-- ── Tempo real: aviso de mudança na base (s241) ───────────────────────────────
-- Qualquer escrita em `bilhetes` (INSERT/UPDATE/DELETE — venha do app, da
-- extensão, do sync da Polymarket ou de script de import) dispara
-- pg_notify('base_mudou', dono). O backend escuta numa conexão dedicada
-- (eventos.py) e repassa via SSE (/eventos) para as telas abertas recarregarem
-- sozinhas. O trigger fica na TABELA, e não em hooks no código, para que nenhum
-- escritor fique de fora por esquecimento. pg_notify deduplica payload igual
-- dentro da mesma transação → lote de N bilhetes num só COMMIT vira 1 aviso.
CREATE OR REPLACE FUNCTION notificar_base_mudou() RETURNS trigger AS $fn$
BEGIN
    PERFORM pg_notify('base_mudou', COALESCE(NEW.dono, OLD.dono));
    RETURN NULL;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_bilhetes_base_mudou ON bilhetes;
CREATE TRIGGER trg_bilhetes_base_mudou
    AFTER INSERT OR UPDATE OR DELETE ON bilhetes
    FOR EACH ROW EXECUTE FUNCTION notificar_base_mudou();

-- ── Fase 0 do tradutor determinístico: MODO SOMBRA (s297) ─────────────────────
-- Grava, por bilhete extraído, o BLOCO BRUTO que o robô da casa emitiu ao lado da
-- DECISÃO que a IA tomou. É o corpo de treino do tradutor — hoje esse par não
-- existe em lugar nenhum: `bilhetes` guarda só a categoria canônica (o resultado),
-- nunca o rótulo que a casa usou (a entrada), e o `§9` dos arquivos de casa lista
-- de 4 a 35 mercados confirmados, longe de cobrir o mundo real.
--
-- ⚠️ ISTO NÃO É O MAPA — é a OBSERVAÇÃO de onde o mapa vai sair. O nome é
-- `sombra_rotulos` de propósito: quem procurar uma tabela de-para pronta não vai
-- achar aqui, e é bom que não ache.
--
-- POR QUE O BLOCO INTEIRO, e não o rótulo do mercado já isolado: medido na s297,
-- **só 4 dos 16 formatadores emitem o mercado como campo próprio** (`Mercado:` na
-- BETesporte e na Superbet, `Rótulo da casa:` no Pitaco, `Marcação da casa:` na
-- KTO). Nos outros 12 — a Bet365 inclusive, que é 43% do custo — ele vem
-- POSICIONAL, concatenado na linha de seleção (`jogo · mercado · seleção`), com
-- formato próprio de cada casa. Isolar isso no backend AGORA seria escrever o
-- parser por casa antes de ter o dado que diz como ele deve ser — exatamente o
-- trabalho que esta fase existe para informar. Gravamos cru; a agregação sai em
-- SQL depois, e errar a agregação não custa nada porque a matéria-prima ficou.
--
-- Uma linha por bilhete por extração (re-extração do mesmo bilhete grava de novo,
-- de propósito: é assim que se vê a IA decidir DIFERENTE para a mesma entrada).
-- Sem FK para `bilhetes`: a sombra observa a EXTRAÇÃO, e sobrevive a bilhete
-- apagado. Volume esperado ~15 mil linhas/mês; a purga preguiçosa abaixo segura.
CREATE TABLE IF NOT EXISTS sombra_rotulos (
    id           BIGSERIAL PRIMARY KEY,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dono         TEXT NOT NULL,
    casa         TEXT,
    codigo       TEXT,             -- código do bilhete; é o que pareia bruto × decisão
    bruto        TEXT NOT NULL,    -- o bloco do robô, verbatim (entrada da IA)
    ia_esporte   TEXT,             -- decisão 1: esporte canônico
    ia_aposta    TEXT,             -- decisão 2: categoria de mercado
    ia_descricao TEXT              -- decisão 3: a descrição montada (o campo de risco)
);
CREATE INDEX IF NOT EXISTS sombra_rotulos_casa_criado ON sombra_rotulos (casa, criado_em);
"""


def dsn() -> str:
    """DSN do Postgres no formato que o asyncpg aceita (postgres:// → postgresql://).
    Compartilhado com eventos.py, que abre uma conexão DEDICADA fora do pool."""
    return os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn(),
            min_size=1,
            max_size=5,
            max_inactive_connection_lifetime=60,
        )
    return _pool


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)


async def seed_usuarios() -> None:
    """Seed idempotente da tabela `usuarios` a partir dos dicts de auth.

    Fase 1 / Deploy A do PLANO_MULTIUSUARIO_2026: popula a tabela com os
    usuários atuais SEM mudar comportamento — o auth continua lendo os dicts.
    ON CONFLICT DO NOTHING: o que já está no banco nunca é sobrescrito (rodar
    a cada boot é seguro; senha trocada via env continua valendo porque quem
    autentica nesta fase são os dicts, não a tabela).
    """
    from auth import linhas_seed_usuarios  # import local: evita acoplar database→auth no import

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO usuarios (username, senha_hash, status, role, parent_owner, planilha_url)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (username) DO NOTHING
            """,
            linhas_seed_usuarios(),
        )


async def criar_usuario(username: str, email: str, senha_hash: str) -> str | None:
    """Cria um cadastro PENDENTE (Fase 2 — "aberto com aprovação").

    Retorna None se criou, ou o motivo do conflito ('usuario' | 'email').
    A checagem é case-insensitive de propósito: 'feca' e 'Feca' seriam DONOS
    diferentes no resto do sistema (a coluna `dono` é texto), então grafia
    gêmea de um username existente precisa ser barrada aqui, na porta.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        conflito = await conn.fetchrow(
            """
            SELECT
                EXISTS (SELECT 1 FROM usuarios WHERE lower(username) = lower($1)) AS u,
                EXISTS (SELECT 1 FROM usuarios WHERE lower(email)    = lower($2)) AS e
            """,
            username, email,
        )
        if conflito["u"]:
            return "usuario"
        if conflito["e"]:
            return "email"
        try:
            await conn.execute(
                """
                INSERT INTO usuarios (username, senha_hash, email, status, role)
                VALUES ($1, $2, $3, 'pendente', 'user')
                """,
                username, senha_hash, email,
            )
        except asyncpg.UniqueViolationError:
            return "usuario"  # corrida entre o SELECT e o INSERT: perde educadamente
    return None


async def atualizar_senha_usuario(username: str, senha_hash: str) -> bool:
    """Grava o hash novo da senha. True se o usuário existia.

    O chamador é obrigado a recarregar o cache de auth logo em seguida — e não
    só pelo login: desde a s275 a impressão do `senha_hash` entra no cookie, e
    é o cache que `ler_token` consulta. Sem a recarga, o usuário troca a senha
    e a sessão dele (a nova, recém-emitida) é recusada até o refresher rodar.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.execute(
            "UPDATE usuarios SET senha_hash = $2, atualizado_em = NOW() WHERE username = $1",
            username, senha_hash,
        )
    return r.endswith(" 1")


async def atualizar_email_usuario(username: str, email: str) -> str | None:
    """Define/troca o e-mail da conta. None se gravou, 'email' se já é de outro.

    Existe para as contas anteriores ao autosserviço (13 das 24 na s275, todas
    com `email` NULL): sem e-mail elas não têm como recuperar senha sozinhas e
    dependem do admin para sempre. Mesma checagem case-insensitive do cadastro
    — `Fulano@x.com` e `fulano@x.com` são a mesma caixa postal, e a UNIQUE do
    Postgres, que é sensível a caixa, não barraria a segunda.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        dono = await conn.fetchval(
            "SELECT username FROM usuarios WHERE lower(email) = lower($1)", email
        )
        if dono is not None and dono != username:
            return "email"
        try:
            await conn.execute(
                "UPDATE usuarios SET email = $2, atualizado_em = NOW() WHERE username = $1",
                username, email,
            )
        except asyncpg.UniqueViolationError:
            return "email"  # corrida entre o SELECT e o UPDATE: perde educadamente
    return None


async def listar_usuarios() -> list[dict]:
    """Lista para o painel /admin — pendentes primeiro, depois mais recentes.
    NUNCA devolve senha_hash (hash não sai do banco nem para admin)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch(
            """
            SELECT username, email, status, role, parent_owner,
                   COALESCE(planilha_url, '') <> '' AS planilha_viva,
                   bot_habilitado, criado_em
            FROM usuarios
            ORDER BY (status = 'pendente') DESC, criado_em DESC
            """
        )
    return [dict(l) for l in linhas]


async def definir_status_usuario(username: str, status: str) -> bool:
    """Aprovar ('ativo') / suspender ('suspenso') / voltar a 'pendente'.
    True se o usuário existia. O chamador recarrega o cache de auth."""
    if status not in ("ativo", "pendente", "suspenso"):
        raise ValueError(f"status inválido: {status!r}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.execute(
            "UPDATE usuarios SET status = $2, atualizado_em = NOW() WHERE username = $1",
            username, status,
        )
    return r.endswith(" 1")  # asyncpg devolve 'UPDATE 1' / 'UPDATE 0'


# Campos de vínculo social permitidos (Fase 3). Whitelist: o nome do campo entra
# na SQL por f-string, então NUNCA pode vir de entrada do usuário sem passar aqui.
_CAMPOS_SOCIAIS = ("google_sub", "telegram_id", "email")


async def buscar_usuario_social(campo: str, valor: str) -> dict | None:
    """Acha o usuário dono deste vínculo social (ou deste e-mail). None = não há."""
    if campo not in _CAMPOS_SOCIAIS:
        raise ValueError(f"campo social inválido: {campo!r}")
    comparacao = "lower(email) = lower($1)" if campo == "email" else f"{campo} = $1"
    pool = await get_pool()
    async with pool.acquire() as conn:
        linha = await conn.fetchrow(
            f"SELECT username, status, role FROM usuarios WHERE {comparacao}", valor
        )
    return dict(linha) if linha else None


async def vincular_social(username: str, campo: str, valor: str, email: str | None = None) -> None:
    """Grava o vínculo social num usuário existente (1º login Google/Telegram de
    uma conta que já existia). O e-mail só preenche se estava vazio — nunca
    sobrescreve um e-mail já cadastrado."""
    if campo not in ("google_sub", "telegram_id"):
        raise ValueError(f"campo social inválido: {campo!r}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            UPDATE usuarios
            SET {campo} = $2, email = COALESCE(email, $3), atualizado_em = NOW()
            WHERE username = $1
            """,
            username, valor, email,
        )


async def usernames_em_uso() -> set[str]:
    """Usernames existentes em lowercase — base da derivação de username social
    (colisão case-insensitive é colisão; ver criar_usuario)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch("SELECT lower(username) AS u FROM usuarios")
    return {l["u"] for l in linhas}


async def criar_usuario_social(
    username: str,
    email: str | None,
    *,
    google_sub: str | None = None,
    telegram_id: str | None = None,
    nome: str | None = None,
) -> None:
    """Cria a conta PENDENTE de quem chegou via Google/Telegram (sem senha local:
    senha_hash NULL). Mesmo funil de aprovação do /signup."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO usuarios (username, email, nome, status, role, google_sub, telegram_id)
            VALUES ($1, $2, $3, 'pendente', 'user', $4, $5)
            """,
            username, email, nome, google_sub, telegram_id,
        )


async def carregar_usuarios() -> list[dict]:
    """Lê a tabela `usuarios` no formato do `auth._usuarios_cache` (Deploy B).

    Devolve a lista crua; quem troca o cache é `auth.atualizar_cache_usuarios`
    (que ignora lista vazia — fail-safe contra leitura quebrada).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch(
            """
            SELECT username, senha_hash, email, status, role, parent_owner,
                   planilha_url, bot_habilitado
            FROM usuarios
            """
        )
    return [dict(l) for l in linhas]


async def definir_bot_habilitado(username: str, habilitado: bool) -> bool:
    """Liga/desliga o planilhamento pelo bot de tipster nesta base (s273).

    É a autorização do token de serviço: sem este flag, o token não escreve nada
    no dono, mesmo válido. True se o usuário existia; o chamador recarrega o
    cache de auth (o flag é lido de lá a cada request)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.execute(
            "UPDATE usuarios SET bot_habilitado = $2, atualizado_em = NOW() "
            "WHERE username = $1",
            username, habilitado,
        )
    return r.endswith(" 1")
