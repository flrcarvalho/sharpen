# Runbook — Rotação da senha do Postgres (Railway)

> Procedimento de produção. Causa ~30-60s de blip no app durante o redeploy.
> Fazer em horário de baixo uso. **Nenhuma senha real neste arquivo** (vai pro git).

## Contexto / coordenadas (não são segredo)
- Projeto Railway: **victorious-generosity** (`dbeaf2ee-6581-4a0f-b397-8caa62fa2aa5`)
- Serviços: **extrator** (`1ef53fd8-0f5b-4a42-bf2e-04e03c4cbcec`) e **Postgres** (`2a5e709c-86ee-45b7-9486-ee35f581a2e7`)
- Ambiente: **production** (`0c3f36e9-1a5d-44b9-9141-87dfa9db66e9`)
- As variáveis de conexão são **literais** (não referências `${{}}`), então cada uma precisa ser atualizada à mão.

As variáveis que carregam a senha (todas com o MESMO valor):
| Serviço | Variável | Forma |
|---|---|---|
| Postgres | `POSTGRES_PASSWORD` | senha pura |
| Postgres | `PGPASSWORD` | senha pura |
| Postgres | `DATABASE_URL` | `postgresql://postgres:<SENHA>@postgres.railway.internal:5432/railway` |
| Postgres | `DATABASE_PUBLIC_URL` | `postgresql://postgres:<SENHA>@<host-proxy>:<porta>/railway` (ver valor atual no Railway) |
| extrator | `DATABASE_URL` | `postgresql://postgres:<SENHA>@postgres.railway.internal:5432/railway` |
| local | `.env` → `DATABASE_URL` | usa o **host público** (proxy), não o `.internal` |

## Pré-requisitos
- `railway` CLI logado (`railway whoami`).
- Acesso ao banco com a senha ATUAL (para o `ALTER USER`). Use o `DATABASE_PUBLIC_URL` atual.
- Gerar senha nova **só alfanumérica** (sem `@ : / # ?` — quebram a URL). Ex.: 32 chars `A-Za-z0-9`.

## Passos (ordem importa)
1. **Gerar** `<NOVA_SENHA>` (alfanumérica, 32 chars).
2. **Trocar no banco vivo** (conexões abertas seguem; novas precisam da nova):
   ```sql
   ALTER USER postgres WITH PASSWORD '<NOVA_SENHA>';
   ```
   (via `psql "<DATABASE_PUBLIC_URL atual>"` ou um script asyncpg pontual.)
3. **Atualizar as 4 variáveis do Postgres** (substitua `<NOVA_SENHA>` e mantenha host/porta atuais):
   ```bash
   P=dbeaf2ee-6581-4a0f-b397-8caa62fa2aa5
   railway variable set "POSTGRES_PASSWORD=<NOVA_SENHA>" -s Postgres -p $P -e production --skip-deploys
   railway variable set "PGPASSWORD=<NOVA_SENHA>"        -s Postgres -p $P -e production --skip-deploys
   railway variable set "DATABASE_URL=postgresql://postgres:<NOVA_SENHA>@postgres.railway.internal:5432/railway" -s Postgres -p $P -e production --skip-deploys
   railway variable set "DATABASE_PUBLIC_URL=postgresql://postgres:<NOVA_SENHA>@<host-proxy>:<porta>/railway"     -s Postgres -p $P -e production --skip-deploys
   ```
4. **Atualizar o extrator** (e deixar redeployar):
   ```bash
   railway variable set "DATABASE_URL=postgresql://postgres:<NOVA_SENHA>@postgres.railway.internal:5432/railway" -s extrator -p $P -e production
   ```
5. **Atualizar o `.env` local** (`DATABASE_URL` com o host público + nova senha).
6. **Verificar:** conectar com a nova credencial (um `SELECT count(*) FROM bilhetes`) → OK; e que a senha antiga **falha**.
7. Se algo travar: a senha antiga ainda está com você — `ALTER USER ... WITH PASSWORD '<senha antiga>'` reverte o banco enquanto você ajusta as variáveis.

## Por que rotacionar
A `DATABASE_URL` apareceu em texto numa transcrição de chat (sessão 82). **Não vazou pelo git** (`.env` sempre esteve no `.gitignore`, nunca commitado), então é higiene preventiva — sem urgência.
