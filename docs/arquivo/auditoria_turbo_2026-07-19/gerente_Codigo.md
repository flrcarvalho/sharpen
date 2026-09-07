## Codigo

**Veredito da area:** Solido — o nucleo de dedup/persistencia, tenancy e seguranca esta maduro e sem bugs criticos de correcao; as pendencias sao de segunda ordem, com uma unica correcao urgente (init de banco novo).

**Top 3 acoes prioritarias:**
- **Corrigir a ordem do SCHEMA_SQL** (`database.py:63-69`): o `UPDATE parceiros` roda antes do `CREATE TABLE parceiros`, dando rollback de todo o batch em banco vazio. Invisivel em prod, mas quebra 100% da inicializacao em DR, novo ambiente ou dev local. Correcao trivial (mover o CREATE para antes) — mas o impacto e total onde ocorre.
- **Trocar `/polymarket/sync` para `Depends(usuario_atual)`** (`main.py:1565/1609`): unica rota de criacao que grava dado novo na base do operador visualizado em modo "ver como", violando a regra da sessao 82. Nao vaza entre tenants, mas grava na base errada e e dificil de desfazer. Trivial.
- **Remover as Migracoes A/B do hot path da extracao** (`repository.py:743-789`): 2 UPDATEs de backfill nunca-gated rodam por bilhete COM codigo em TODA extracao, permanentemente — 2N round-trips desperdicados por lote, afetando 0 linhas. Gatear/mover para script offline.

### Achados criticos e altos (detalhados)

**1. SCHEMA_SQL: UPDATE antes do CREATE quebra banco novo** — `database.py:63-69` (bug, medio/alto impacto no cenario)
Os cinco `UPDATE parceiros SET casa=...` estao nas linhas 63-67, mas o `CREATE TABLE IF NOT EXISTS parceiros` so aparece na 69. Como `conn.execute(SCHEMA_SQL)` roda em transacao implicita, num banco vazio o primeiro UPDATE falha com `relation "parceiros" does not exist` e faz rollback de TODO o batch — inclusive o `CREATE TABLE bilhetes`. Uma instancia limpa (recuperacao de desastre, novo cliente, dev local) nunca inicializa. Passa despercebido em prod so porque as tabelas ja existem.
**Rec:** mover o bloco `CREATE TABLE parceiros` para antes dos UPDATEs (idealmente logo apos o CREATE de `bilhetes`), e testar o init contra um Postgres vazio no CI para travar a regressao.

**2. /polymarket/sync cria dado novo com `dono_efetivo`** — `main.py:1565` (arquitetura)
As tres rotas de criacao (`/extrair`, `/salvar`, `/bilhetes/manual`) usam `Depends(usuario_atual)` com comentario explicito: em modo "ver como operador", dado novo vai para a base de quem esta LOGADO. O `/polymarket/sync` tambem cria bilhetes (`upsert_bilhetes(..., origem='sync')`) mas usa `Depends(dono_efetivo)`. Consequencia: um dono com cookie "ver como" ativo (dura 30 dias) que sincronize uma carteira Polymarket grava na base do operador visualizado — o cenario que a sessao 82 diz evitar. Nao e vazamento entre tenants (o dono tem acesso), mas e dado na base errada e dificil de desfazer.
**Rec:** trocar a dependencia de criacao para `Depends(usuario_atual)`, mantendo `dono_efetivo` so nas leituras e na associacao de tipster de ativas. Se a intencao for gravar na base do operador, documentar a excecao como nas outras rotas.

### Achados medios e baixos (resumidos em tabela)

| Sev | Achado | Local | Rec | Esforco |
|---|---|---|---|---|
| Medio | Migracao A/B roda 2 UPDATEs por bilhete com codigo em TODA extracao, permanentemente (backfill nunca gated) | `repository.py:743-789` | Gatear (flag de lote legado), mover offline ou fundir em CTE unica | Pequeno |
| Medio | Doc canonica (tabela de dedup do CLAUDE.md) diverge do codigo: lote identico NAO salva uma vez, salva as duas via counter + aviso | `repository.py:690-711` | Atualizar a linha da tabela no CLAUDE.md (codigo e a verdade): salva ambas + aviso | Trivial |
| Baixo | Assimetria de normalizacao: odd passa por `_norm_odd`, stake entra crua → mesmo bilhete com stake "250" vs "250,00" nao dedupa (manual vs extracao) | `repository.py:558-562` | Aplicar `_norm_stake` espelhando `_norm_odd`, ou normalizar stake no `/bilhetes/manual` | Pequeno |
| Baixo | Lote de upsert em autocommit por linha (sem `conn.transaction()`): erro nao-UniqueViolation deixa commit parcial + contadores inconsistentes | `repository.py:641-861` | Decidir: atomicidade (`conn.transaction()`) OU resiliencia por linha (capturar `Exception` por linha) | Medio |
| Baixo | Migracao A/B fora do try/except do INSERT: corrida de unique (dois `/salvar` do mesmo lote) aborta o lote inteiro (0 exportadas) | `repository.py:751-789` | Envolver A/B em `try/except UniqueViolationError` (log + segue), como no INSERT | Trivial |
| Baixo | `estado_extracao` exige `odd>0` para V/L/HL: resolvidos sem odd (P/L correto) ficam eternamente "aberta" no badge ambar da sidebar | `repository.py:252-264` | Alinhar com `calcular_pl`: exigir odd so para W/HW | Trivial |
| Baixo | `/bilhetes/restaurar` re-insere `linhas: list[dict]` cru do cliente sem `validar_linhas` nem field_validators; unica escrita que contorna a validacao | `main.py:1757-1762` | Validar com `validar_linhas` / recomputar assinatura no servidor, ou restringir payload a IDs de lote com TTL server-side | Pequeno |
| Baixo | Rate-limit de login in-memory (`_login_fails`): multiplicado por replica, zera no restart | `main.py:1100-1112` | Store compartilhado (Postgres/Redis) se >1 replica; senao documentar premissa de replica unica | Medio |
| Baixo | `_login_fails` cresce sem poda: brute-force distribuido incha a memoria do processo | `main.py:1086-1112` | Podar entradas expiradas periodicamente ou cache com TTL/tamanho maximo | Pequeno |
| Baixo | Modelos em alias nao-datado (`claude-sonnet-4-6`, `claude-opus-4-8`) + deps sem lockfile: rebuild pode mudar modelo/libs silenciosamente | `config.py:10-18` | Pinar snapshot datado em prod + congelar lockfile (uv lock/pip-tools) | Pequeno |
| Baixo | SCHEMA_SQL inteiro (DDL+DML+backfills full-table de ~25k linhas) re-executa a cada boot, sem versionamento de migracao | `database.py:57-203` | Adotar `schema_migrations`; separar DDL idempotente de DML de backfill; curto prazo remover UPDATEs saturados | Medio |
| Info | `dashboard_rows` faz `SELECT *` por dono sem LIMIT e deriva P/L em Python por request — teto de escala do feed | `repository.py:1148-1205` | Quando apertar: agregar/paginar no banco, views materializadas ou cache por dono | Grande |
| Info | Identidade do dono-plataforma `'Feca'` hardcoded como string magica espalhada (auth, database, index, gestao) | `main.py:1209` | Centralizar em `DONO_PLATAFORMA` (env var) e referenciar | Pequeno |
| Info | Forma da resposta de salvar/sync duplicada em 3 rotas — ajuste de contrato exige tocar as tres | `main.py:1551-1553` | Extrair helper `_resposta_upsert(...)` | Pequeno |
| Info | `get_pool` sem lock: corrida teorica cria dois pools (inofensivo hoje — lifespan popula antes do trafego) | `database.py:244-254` | Blindar com `asyncio.Lock` (dupla checagem) se surgir chamada concorrente fora do lifespan | Trivial |
| Info | Enumeracao de usuario por timing: usuario inexistente pula bcrypt (~100ms de diferenca) — mitigado por sleep 0,5s + rate-limit | `auth.py:126-137` | `bcrypt.checkpw` contra hash dummy fixo tambem no caminho de usuario inexistente | Trivial |
| Info | Regex de data do checador pode falso-positivar em placar/handicap com barra ('6/4', '0/0.5') — advisory, golden atual limpo | `descricao_check.py:42` | Restringir heuristica se o formato surgir na descricao, ou documentar se o MASTER proibir N/N | Trivial |

### Pontos positivos (o que esta bem feito)

- **P/L derivado e correto** — nunca persistido; `HW=(s/2)(odd-1)` e `HL=-s/2` corretos vs handicap asiatico, com guard que devolve `None` em vitoria com odd ilegivel (impede virar menos-stake no agregado). *(`repository.py:70-110`)*
- **SQL 100% seguro** — toda a superficie e parametrizada; onde a query e montada por f-string, os nomes de coluna vem de whitelists hardcoded (`_EDITAVEIS`, listas literais) e os valores sempre entram como `$N`. Sem superficie de injecao. *(`repository.py:1714-1776`)*
- **Canonizacao de resultado consistente** — `.strip().upper()` aplicada em todos os writes (upsert, atualizar, manual), fechando o bug historico do 'v' minusculo.
- **Dedup resiliente** — `except UniqueViolationError` no INSERT converte colisao de corrida em UPDATE em vez de abortar o lote; counter + guard cross-dono cobrem os cenarios.
- **Isolamento por dono solido** — toda rota de dados injeta `dono` via `Depends` (`dono_efetivo` p/ gestao, `usuario_atual` p/ criacao) e cada funcao aplica `WHERE dono = $`. `dono_efetivo` reavalia `pode_ver_como` contra o usuario REAL a cada request — cookie "ver como" forjado cai no fallback, sem escalonamento. Nenhuma rota de dados sem checagem de dono. *(`main.py:1655-1994`)*
- **Camadas de defesa web maduras** — CSRF por Origin/Referer complementando SameSite=Lax (isencao restrita e justificada so para a extensao), security headers (CSP, nosniff, X-Frame-Options), exception handler global que nao vaza detalhe. *(`main.py:235-264`)*
- **Auth hardening fail-closed** — `SESSION_SECRET` sem default conhecido (segredo efemero aleatorio se ausente); bcrypt com retorno False em hash vazio/lib ausente; cookie HMAC-SHA256 verificado com `hmac.compare_digest`; flags httponly/secure/samesite; rate-limit + delay constante. *(`auth.py:37-137`)*
- **Validacao de fronteira financeira** — `_BilheteFinanceiroBase` (Pydantic) valida stake/odd/resultado/data e retorna 422 antes de qualquer INSERT/UPDATE; `/salvar` complementa com `validar_linhas`. *(`main.py:1836-1862`)*
- **Conexoes nunca vazam** — ~55 pontos de acesso usam `async with pool.acquire()`; pool singleton com limites sanos (`min_size=1, max_size=5`), criado uma vez, `init_db` no lifespan antes do trafego. *(`repository.py:641-1966`)*

> **Nota transversal:** os achados marcados `nao-verificado` sao observacoes verificadas por leitura mas nao exercitadas em runtime. Recomendo travar o achado #1 (SCHEMA_SQL) com um teste de init contra Postgres vazio no CI — e o unico com modo de falha total.