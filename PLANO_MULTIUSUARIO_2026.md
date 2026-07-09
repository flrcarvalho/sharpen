# PLANO — Multiusuário / Cadastro / Login social / Pagamento (Sharpen)

> **Status:** na CANTEIRA (aprovado em princípio, a executar "muito em breve" — sessão 116, 08/07/2026).
> **Fonte de verdade operacional:** este arquivo. A memória `saas_multiusuario_plano.md` aponta pra cá.
> Antes de executar: reler `CLAUDE.md` (backup → uma etapa por vez → commit+push) e conferir o código atual (`app/auth.py`, `app/database.py`, `app/main.py`) — este plano foi escrito lendo esses arquivos em 08/07/2026; podem ter mudado.

---

## Contexto — por que esta frente existe

O Feca quer transformar o Sharpen de app multi-tenant **provisionado à mão** em produto de verdade: **página de cadastro no site, login via Google (Gmail) ou Telegram, base cadastral, e depois método de pagamento/assinatura.** Não estava no `PLANO_CONSTRUCAO.md` original (aquele era a máquina de extração).

### Estado atual do auth (lido em 08/07/2026)
- Login por **cookie assinado HMAC-SHA256** (`app/auth.py`) — sem sessão em banco, sem JWT lib, sem OAuth. Token = `base64url({"u":usuario,"exp":ts}).hmac`. Validade 30 dias. Segredo `SESSION_SECRET` (env Railway).
- **7 usuários HARDCODED** no dict `USUARIOS` (`auth.py:50`), hashes **bcrypt** vindos de env vars `SENHA_<USER>_HASH`. Sem default no código (fail-closed).
- Hierarquia dono→operador no dict `OPERADORES` (`auth.py:66`): Feca→[Lava], Diogo→[Primo], Fatuch→[LavaFatuch]. Jonathan é solo.
- Planilha viva no dict `PLANILHAS_AO_VIVO` (`auth.py:79`): LavaFatuch lê Google Apps Script em vez do Postgres.
- **NÃO existe tabela de usuários.** O `dono` é só uma coluna TEXT em `bilhetes`/`parceiros`/`polymarket_ativos_tipster`/`uso_tokens` que isola cada cliente. Adicionar cliente hoje = editar código + criar env var + redeploy.
- Rotas protegidas por `Depends(usuario_atual)` (identidade real) / `Depends(dono_efetivo)` (base visível; reavalia `pode_ver_como` a cada request). Sem middleware global. `/privacidade` é a única rota pública.
- **Ponto de convergência limpo p/ qualquer login novo:** produzir um `usuario` (string) confiável e chamar `criar_token(usuario)` + `resp.set_cookie(COOKIE_NAME, ...)` — já existem (`auth.py:119`, `main.py:893`).

### Decisões já tomadas pelo Feca
- **Modelo de cadastro = "aberto com aprovação":** qualquer um se cadastra, mas a conta fica **pendente** até o Feca aprovar. Ele mantém controle de quem entra sem editar código.
- Ordem faseada: **fundação (tabela `usuarios`) → cadastro → login social → pagamento.**

---

## FASE 1 — Fundação: tabela `usuarios` + migração da identidade

Mover a fonte de verdade da identidade dos dicts de `auth.py` para uma tabela no Postgres, **sem quebrar nada e sem risco de lockout**. Sozinha não muda nada visível — é infraestrutura. Cookies atuais seguem válidos (formato do token não muda).

### 1.1 Schema da tabela `usuarios`
```sql
CREATE TABLE IF NOT EXISTS usuarios (
    username      TEXT PRIMARY KEY,          -- = coluna `dono` (ex.: 'Feca')
    senha_hash    TEXT,                      -- bcrypt; NULL p/ quem loga só via social
    email         TEXT UNIQUE,               -- cadastro/Google/recuperação (NULL nos 7 atuais)
    nome          TEXT,                      -- nome de exibição (opcional)
    status        TEXT NOT NULL DEFAULT 'pendente'
                     CHECK (status IN ('ativo','pendente','suspenso')),
    role          TEXT NOT NULL DEFAULT 'user'
                     CHECK (role IN ('admin','user')),
    parent_owner  TEXT,                      -- substitui OPERADORES (NULL = é dono)
    planilha_url  TEXT,                      -- substitui PLANILHAS_AO_VIVO ('' = lê do Postgres)
    google_sub    TEXT UNIQUE,               -- 'sub' do Google OIDC (NULL até vincular)
    telegram_id   TEXT UNIQUE,               -- id do Telegram (NULL até vincular)
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```
- **`status`** implementa "aberto com aprovação": novo cadastro entra `pendente`, Feca aprova → `ativo`. Login só passa se `ativo`.
- **`role`**: Feca=`admin` (aprova cadastros / vê carteira inteira). Substitui o hardcode `"Feca"` de `/uso/tokens`.
- **`parent_owner`**: `operadores_de(x)` vira `SELECT username WHERE parent_owner=x`.
- Colunas de social (`google_sub`/`telegram_id`/`email`) **já entram agora** — baratas, evitam 2ª migração na Fase 3.
- **Sem FK** `bilhetes.dono → usuarios.username`: integridade lógica (como hoje), pra não falhar por `dono` órfão de importação.

### 1.2 Virada de arquitetura — cache em memória lastreado no banco
Validar o cookie a cada request tem que continuar I/O-zero. Solução: **dict em memória `_usuarios_cache`** carregado do banco no startup, recarregado após mutações (cadastro/aprovação/troca de senha) + **TTL defensivo ~60s** (rede de segurança p/ caso de múltiplos workers no Railway). O hot-path segue sem I/O; o banco é a fonte de verdade.
As funções de `auth.py` passam a ler do cache: `verificar_credenciais` (+ exige `status='ativo'`), o check final de `ler_token`, `operadores_de`, `planilha_ao_vivo`.

### 1.3 Execução em 2 deploys (checkpoint no meio)
**Deploy A — schema + seed (comportamento 100% inalterado):**
1. `CREATE TABLE usuarios` no `SCHEMA_SQL` (idempotente, roda no `init_db`).
2. **Seed idempotente** no startup: popula `usuarios` a partir dos dicts atuais (que leem as env vars) com `ON CONFLICT (username) DO NOTHING`. Os 7 entram `status='ativo'`, `role` (Feca=admin), `parent_owner` (Lava→Feca, Primo→Diogo, LavaFatuch→Fatuch), `planilha_url`, `senha_hash` das env vars.
3. **Auth ainda lê dos dicts** — nada muda.
   → **Checkpoint:** inspecionar a tabela (read-only) e confirmar os 7 corretos **antes** de virar a chave.

**Deploy B — virar a chave:**
4. Refatorar `auth.py` pra ler do `_usuarios_cache` (lastreado no banco). Dicts viram só a semente. Carregar o cache no startup após `init_db`.
   → Rollback trivial: reverter o commit volta a ler dos dicts (que continuam no código).

### 1.4 Mudanças por arquivo
- **`app/database.py`**: `CREATE TABLE usuarios` no `SCHEMA_SQL`; `async seed_usuarios(...)` e `async carregar_usuarios()`.
- **`app/auth.py`**: `_usuarios_cache` + refresh; `verificar_credenciais`/`ler_token`/`operadores_de`/`planilha_ao_vivo` lendo do cache e respeitando `status`; dicts mantidos como semente.
- **`app/main.py`**: chamar `seed_usuarios()`+`carregar_usuarios()` no startup (onde `init_db()` já roda); (opcional, recomendado) trocar hardcode `"Feca"` de `/uso/tokens` por `role=='admin'`.
- **`tests/test_auth.py`** (novo): testa `verificar_credenciais`/`operadores_de`/`pode_ver_como`/gate de `status` contra cache injetado — valida a lógica **sem** banco.

### 1.5 Validação
- `py_compile` + `tests/test_auth.py` (lógica isolada, sem banco).
- Deploy A: inspeção read-only da tabela (7 corretos).
- Deploy B: **Feca loga e confirma** que os 7 entram e o "ver como" funciona — teste final (por isso o deploy A separado).
- Backup em `Backups/` antes de cada edição; commit+push por deploy.

### 1.6 Decisões abertas (bater o martelo antes de codar)
1. Manter env vars `SENHA_*_HASH` por ora (seed lê delas; aposentar só depois)? → **recomendo sim.**
2. `email` NULL nos 7 atuais (preenche ao vincular Google/próximo login)? → **recomendo sim.**
3. Trocar já o hardcode `"Feca"` de `/uso/tokens` por `role='admin'` (1 linha)? → **recomendo sim.**
4. Quantos workers o uvicorn roda no Railway? (só afeta o TTL do cache; TTL de 60s cobre ambos os casos.)

---

## FASE 2 — Cadastro self-service ("aberto com aprovação")
- Rota `POST /signup` (pública) ao lado de `POST /login`: valida email+senha, cria usuário `status='pendente'`, `senha_hash` bcrypt.
- UI de cadastro no `login.html` (hoje só tem usuário/senha, sem link de cadastro).
- **Painel/rota de admin** (só `role='admin'`): `GET /admin/usuarios` lista pendentes; `POST /admin/usuarios/{u}/aprovar|suspender` muda `status` e invalida o cache. Notificação ao Feca de novo pendente (email/Telegram — opcional).
- Mensagem clara ao usuário pendente ("cadastro em análise").

## FASE 3 — Login Google / Telegram
- **Google:** rotas `GET /auth/google` + `GET /auth/google/callback` (OAuth2/OIDC). No callback, casar `google_sub`/`email` com um `usuarios` existente OU criar `pendente`; reusar `criar_token`+`set_cookie`. Precisa de client id/secret Google (Console) + lib (authlib ou fluxo manual com httpx).
- **Telegram:** Telegram Login Widget no `login.html`; rota `POST /auth/telegram` valida o `hash` HMAC (o projeto já usa `hmac`/`hashlib`); casa `telegram_id`; reusa `criar_token`+`set_cookie`. Precisa de bot token.
- Ambos convergem no mesmo ponto de sessão já existente — só muda a etapa de *identificação*.

## FASE 4 — Pagamento / assinatura
- Colunas de plano/status na tabela `usuarios` (ou tabela `assinaturas` separada): plano, status (trial/ativo/inadimplente/cancelado), validade, id externo do gateway.
- Gate `assinatura_ativa` — dependency modelada sobre `usuario_atual`, aplicada nas rotas de dados no mesmo ponto de `dono_efetivo`.
- Webhook do gateway como rota **pública** (padrão de `/privacidade`) pra receber eventos de pagamento.
- Definir gateway (Stripe / Mercado Pago / etc.) e preços (a conversa de custo diz ~$0,011/bilhete, ~$10/usuário/mês no cenário médio — ver [[custo_escala_extracao]]).

---

## Frentes pendentes do PLANO original (contexto, não parte desta frente)
Do `PLANO_CONSTRUCAO.md` (8 fases; 0–4 feitas): **Fase 5 Telegram→tipster automático** (maior lacuna; tipster ainda é carimbado à mão), **Bet365 ponta-a-ponta** (pausada), **parser determinístico por casa** (custo ~R$0, IA fallback), Fase 6 inspetor/eval automatizado, fixes estruturais de dedup (Betano sem-código) e data-guarda Superbet. Ver `STATUS.md`.

---

VERSÃO: 2026 · CRIADO: sessão 116 (08/07/2026)
