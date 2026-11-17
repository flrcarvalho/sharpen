# Auditoria independente: concorrência, consistência e escala (Sharpen)

Data: 17/11/2026 · Lente: corridas, event loop, pool, timeouts, volume, isolamento, fundo.
Fonte de verdade usada: só o código (`app/`, `extensor/`, `Dockerfile`, `railway.toml`) e medição.
Nada de `CLAUDE.md`/`STATUS`/`docs`/memória/comentários foi tomado como garantia.

## Como foi medido

- Postgres 17 **privado** iniciado em `scratchpad/aud_escala/pgdata`, porta 5499 (nunca o de
  produção, nem os 5432/5433 que já estavam no ar na máquina). Schema criado pelo próprio
  `init_db` do app.
- Volume sintético: 42 usuários; `u_big` com **60.000** apostas (20 casas, 200 contas),
  `u_small` com 50, outros 40 com 6.000 cada (300 mil linhas em `bilhetes`).
- App real (`uvicorn main:app`, 1 processo, como no `Dockerfile`) com `DATABASE_URL` local,
  `ANTHROPIC_BASE_URL` apontando para um **stub local** (`stub_anthropic.py`) que responde no
  formato de streaming da API depois de 8 s. Zero chamada paga.
- Scripts de medição (todos em `scratchpad/aud_escala/`): `mede_loop.py`, `perfil_feed.py`,
  `mede_salvar.py`, `mede_pool.py`, `mede_sse.py`, `mede_login.py`, `mede_deploy.py`,
  `trava_pool.py`, `corrida_caixa.py`, `corrida_custo.py`, `mede_extrair.py`, `mede_conc.py`.
- Máquina local (Python 3.14; produção roda 3.12 no Railway): os números absolutos variam,
  a **forma** do problema não.
- Working tree do repo intocado (`git status` igual ao início).

---

## Resumo: a causa sistêmica

O Sharpen é **um processo, um event loop, um pool de 5 conexões, estado vivo em memória e
deploy a cada push (~4,5/dia nos últimos 25 dias)**. Isso transforma qualquer coisa pesada de
UM usuário em problema de TODOS, e todo deploy em problema de quem estava no meio de algo.
Os achados abaixo não são bugs isolados: são três famílias.

1. **Recurso compartilhado sem teto por usuário** (event loop, pool, concorrência com a
   Anthropic, memória): um usuário grande trava os pequenos. (A1, A2, A3, A4, A5, A10)
2. **Estado que morre no deploy ou fica pela metade** (sessão da extensão em memória,
   escritas em vários passos sem transação, chave de idempotência gravada antes do
   trabalho): o usuário que volta encontra tudo "quebrado" de formas diferentes. (A6, A7, A9)
3. **Ler-calcular-gravar sem trava** (Caixa, custos): duas abas/fontes se sobrescrevem
   em silêncio. (A8, A11)

---

## A1. O feed do dashboard carrega a base inteira e congela o servidor para todos

- **Sintoma do usuário:** a tela de qualquer usuário "trava" ou demora vários segundos sem
  motivo aparente; quem tem base grande espera 10+ s a cada atualização; piora quando outros
  estão com o dashboard aberto.
- **Mecanismo:** `GET /dashboard/data` (`main.py:5148-5197`) chama `dashboard_rows`
  (`repository.py:4349`), que faz `SELECT *` de **todas** as linhas do dono
  (`export_bilhetes`, `repository.py:2857-2867`), transforma linha a linha em Python, faz
  `json.dumps` e `gzip.compress` **no event loop**. Não há cache, paginação, delta
  ("desde builtAt") nem limite. O decode do asyncpg, o laço Python, o JSON e o gzip são todos
  CPU síncrona dentro do único loop.
- **Evidência (COMPROVADO, medido):**
  - `perfil_feed.py`, 60 mil linhas: `export_bilhetes` 2,5 s · laço do `dashboard_rows` +2,4 s
    · `json.dumps` 1,3 s (19,5 MB) · `gzip` 0,5 s (1,2 MB). ~4,7 s de CPU por carga.
  - `mede_loop.py`: 1 carga do feed do `u_big` = 9,4 s; `/me` do `u_small` (não toca banco)
    passou de 10 ms para **máx. 7,5 s** durante ela. 3 cargas simultâneas: 27 s, e o `/me`
    de outro usuário chegou a **15 s**.
  - Memória: 3 cargas simultâneas levaram o processo de 172 MB para **pico de 453 MB**.
- **Severidade:** CRÍTICA (degrada todos os usuários; cresce linearmente com a base de cada um).
- **Pontual ou família:** família. Mesmo padrão em `/exportar.csv` (`main.py:5216`),
  `/tipsters/{slug}/data` (público, cache de 5 min sem single-flight: misses simultâneos
  calculam em paralelo), treino do `matcher` (síncrono no loop, `main.py:6365`) e o `/login`
  (A5).
- **Correção estrutural:** (a) feed incremental: o front guarda a base e pede
  `?desde=<atualizado_em>`; P/L e filtros já são do front; (b) enquanto isso, montar o feed
  em `asyncio.to_thread`/processo separado e servir gzip pré-calculado por dono com
  invalidação pelo `base_mudou` (single-flight); (c) teto de payload/paginação para bases
  grandes; (d) regra de projeto: nada O(base) em handler async sem `to_thread`.

## A2. Cada lote salvo gera um aviso de "base mudou" POR LINHA, e cada aviso recarrega a base inteira

- **Sintoma:** durante e após uma captura/importação, as telas abertas recarregam sozinhas
  e o servidor fica lento para todos (soma com A1).
- **Mecanismo:** o trigger `trg_bilhetes_base_mudou` é `FOR EACH ROW` (`database.py:528-543`)
  e o `upsert_bilhetes` (`repository.py:1841`, laço em 1988+) **não usa transação**: cada
  `INSERT … ON CONFLICT` é um commit próprio, então o `pg_notify` não deduplica. O comentário
  do schema diz que "lote de N bilhetes num só COMMIT vira 1 aviso" — isso não acontece neste
  caminho. Cada aviso chega ao front (`app.html:489-502`), que reagenda um refresh com
  debounce de 1,5 s → nova chamada ao `/dashboard/data` (A1) **por aba aberta, e para o
  supervisor também** (escopo inclui operadores).
- **Evidência (COMPROVADO):** `mede_sse.py`: um `/salvar` de 1.000 linhas emitiu **843
  eventos SSE `base_mudou`**; maior intervalo entre eventos 0,38 s. Se um lote tiver pausas
  > 1,5 s (Ficha em partes, extração com repescagem, banco lento), o front recarrega a base
  inteira várias vezes no meio do mesmo lote.
- **Severidade:** ALTA (amplificador de A1).
- **Família:** escrita em vários commits (ver A7).
- **Correção:** uma transação por lote no `upsert_bilhetes` (resolve também A7) ou trigger
  `FOR EACH STATEMENT`; e o front pedir delta em vez de base inteira.

## A3. Pool de 5 conexões, sem timeout de aquisição nem de comando: uma trava derruba o app inteiro e o healthcheck continua verde

- **Sintoma:** "o Sharpen parou", telas que nunca carregam, sem erro; o Railway não reinicia
  porque o `/healthz` responde.
- **Mecanismo:** `asyncpg.create_pool(min_size=1, max_size=5)` sem `timeout`,
  `command_timeout` nem `statement_timeout` (`database.py:1185-1194`); todo
  `pool.acquire()` espera para sempre. Quem segura conexão por muito tempo: `upsert_bilhetes`
  (uma conexão durante o lote inteiro, ~3 ms/linha), `dashboard_rows`, jobs de fundo
  (`dicionario.diario`, `aviso_diario`, `virada`) e qualquer consulta parada num lock. O
  `/healthz` não toca o banco (`main.py`, rota `/healthz`), e o fetch do front e da extensão
  não tem timeout (nenhum `AbortSignal.timeout` em `app/static` fora do stream de extração).
- **Evidência (COMPROVADO):**
  - `mede_pool.py`: 5 `/salvar` de 1.500 linhas simultâneos (≈10 s cada) → `/parceiros` do
    `u_small` (11 ms em repouso) chegou a **7,6 s** esperando conexão.
  - `trava_pool.py`: uma transação externa com lock em `parceiros` (o cenário "script de
    banco rodando à mão") + 5 requisições de `/parceiros` → o feed do `u_small`, que **nem
    toca `parceiros`**, ficou **preso > 20 s**; `/healthz` respondeu **200 em 4 ms** o tempo
    todo.
- **Severidade:** CRÍTICA (queda total silenciosa; já tem precedente de queda por lock).
- **Família:** recurso compartilhado sem teto (com A1, A4, A10).
- **Correção:** `create_pool(..., max_size` dimensionado ao plano do Postgres`, timeout=10,
  command_timeout=30)` + `SET statement_timeout`/`lock_timeout` por sessão do app; pool
  separado (ou semáforo) para rotas pesadas e jobs de fundo; `/healthz` de prontidão que faça
  `SELECT 1` com timeout curto; timeout no fetch do front e da extensão com mensagem clara.

## A4. Sem teto global de chamadas à Anthropic: N usuários = 8N chamadas simultâneas

- **Sintoma:** em horário de pico, extrações de todos começam a falhar/lentificar juntas
  (429/overload), inclusive de quem mandou um lote pequeno.
- **Mecanismo:** o semáforo de concorrência é criado **dentro** de cada requisição
  (`main.py:2582` e `main.py:2856`, `asyncio.Semaphore(_MAX_CONCURRENT=8)`), sobre um
  cliente global único (`main.py:124`). Não há limite por usuário nem global, nem fila.
  Também não há teto de tamanho do texto no `/extrair`: um histórico de meses vira centenas
  de chunks de 6 bilhetes.
- **Evidência (COMPROVADO):** `mede_conc.py` com o stub: 4 extrações simultâneas de 4
  usuários → **pico de 32 chamadas simultâneas** à "API" (= 8 × 4). `mede_extrair.py`: 400
  bilhetes levaram 89 s com 8 s por chamada; com latência real e lotes de milhares, a
  requisição dura dezenas de minutos (ver A6).
- **Severidade:** ALTA (custo e disponibilidade compartilhados entre tenants).
- **Correção:** semáforo/limitador **de módulo** (global) + cota por dono; fila de jobs de
  extração persistida (ver A6), com teto de bilhetes por job e partição automática.

## A5. `/login` faz bcrypt no event loop

- **Sintoma:** picos de lentidão geral quando várias pessoas entram (ex.: depois de um
  deploy que derruba as sessões, ou na troca de senha), e vetor de negação de serviço: cada
  tentativa com usuário válido custa ~0,4 s de CPU do processo inteiro.
- **Mecanismo:** `login` (`main.py:3311-3321`) chama `resultado_login` →
  `_verifica_hash` → `bcrypt.checkpw` (`auth.py:386-410`) **sincronamente**. O cadastro e a
  troca de senha já usam `asyncio.to_thread` (`main.py:3508`, `3964`, `3970`); o login não.
  O limite por IP só conta falhas e é em memória.
- **Evidência (COMPROVADO):** `mede_login.py`: 1 `checkpw` = 406 ms; 10 logins simultâneos
  → `/healthz` (4 ms em repouso) chegou a **5,3 s**.
- **Severidade:** MÉDIA/ALTA.
- **Correção:** `await asyncio.to_thread(resultado_login, ...)`; limitador por usuário além do
  IP, persistido.

## A6. Todo deploy desconecta a extensão de todo mundo e perde o que estava na fila

- **Sintoma:** "a extensão desconectou", "Sessão expirou — reconecte no popup", capturas que
  sumiram, extração que parou no meio. O usuário que volta depois de dias/meses encontra a
  extensão sempre desconectada. Com ~4,5 deploys/dia, isso acontece várias vezes por dia para
  quem está usando.
- **Mecanismo:** sessões de pareamento, token da extensão e a **fila de capturas** (imagens
  em base64) vivem só em memória (`captura.py:387-388`, `_SESSOES`; TTL 6 h; teto global de
  300 sessões que derruba a sessão inativa de **qualquer** usuário). Restart = tudo some. A
  extensão, ao receber 401, **apaga o token** e pede novo código (`extensor/background.js:147-152`,
  `191+`). A Ficha (`/captura/ficha`) usa o mesmo token, então a captura do cru também para.
  Extração (`/extrair`) é um stream HTTP único de minutos; o TSV só existe no navegador até
  o `/salvar` separado: deploy, aba fechada ou queda de rede no meio = trabalho de IA pago e
  perdido. O `CMD` do `Dockerfile` não define `--timeout-graceful-shutdown`, e há streams SSE
  infinitos (`/eventos`) abertos, então o desligamento não espera de forma controlada.
- **Evidência (COMPROVADO):** `mede_deploy.py`: pareei, conectei, validei (200) e enfileirei
  uma captura (200); reiniciei o processo; depois: `/captura/validar` → **401 "Sessão de
  captura expirada."**, poll do dashboard → **404**, captura enfileirada perdida. Deploys:
  113 commits em 25 dias (`git log`), e cada push faz deploy (sem watch paths no
  `railway.toml`).
- **Severidade:** CRÍTICA para a experiência (é exatamente o "voltei e nada funciona").
- **Família:** estado de processo (também `_login_fails`, `_trial_por_ip`, caches de câmbio,
  `virada._em_voo`, `matcher._CACHE`, `eventos._assinantes`). Isso também **impede escalar
  horizontalmente** (mais de 1 worker/réplica quebraria pareamento, rate limit, `virada` e SSE).
- **Correção:** sessões e fila de captura no Postgres (ou Redis), token da extensão de longa
  duração vinculado ao dono+conta (revogável), extensão que reconecta sozinha; extração como
  **job persistido** (id, status, resultado no banco) que o front acompanha e que sobrevive a
  aba fechada; graceful shutdown com prazo e drenagem; separar deploy de app de deploy de docs.

## A7. Gravação de lote sem transação: lote pela metade, sem como saber

- **Sintoma:** depois de um erro/deploy no meio do salvar, parte das apostas entrou e parte
  não; contagens e Caixa não batem; o usuário salva de novo e às vezes duplica/omite.
- **Mecanismo:** `upsert_bilhetes` faz, por linha, até 5 comandos (Migrações A, C, B, B',
  INSERT ON CONFLICT) em autocommit numa conexão só (`repository.py:1898-2400`). O
  `/salvar` depois faz absorção de juntadas, adoção de abertas na Caixa e log em passos
  separados (`main.py:4741+`). Qualquer falha no meio deixa estado intermediário, e os
  índices de candidatos (`sem_cod_no_banco`, `ocr_no_banco`) são lidos no início e usados
  sem trava: dois lotes simultâneos da mesma conta podem disputar a mesma órfã (o guard
  `assinatura != $1` não impede o segundo lote de sobrescrever a adoção do primeiro).
- **Evidência:** COMPROVADO por medição o efeito colateral (A2, 843 commits num lote) e a
  duração (3.000 linhas = 9,5 s, `mede_salvar.py`). Testei dois `/salvar` simultâneos do
  mesmo lote **com código**: a dedup por `ON CONFLICT` segurou (200 inseridos + 200
  atualizados, sem duplicata). A disputa de órfã entre dois lotes é **HIPÓTESE** (não reproduzi).
- **Severidade:** ALTA.
- **Correção:** uma transação por lote (ou por conta dentro do lote) + `pg_advisory_xact_lock`
  por (dono, casa, parceiro) no início do `upsert_bilhetes`, serializando escritores da mesma
  conta (extensão/Ficha × extrator × bot); escrita em lote (`executemany`/`UNNEST`) em vez de
  5 round-trips por linha.

## A8. Caixa: `abertas_corte` é ler-calcular-gravar sem trava (perda de atualização)

- **Sintoma:** a Caixa de uma conta aparece divergente pelo valor de uma aposta aberta; o
  usuário "confere", lança ajuste e cimenta um erro.
- **Mecanismo:** `_caixa_adotar_abertas_tardias` lê `abertas_corte` (`repository.py:3775`),
  une com as novas em Python e grava o array inteiro (`repository.py:3798`), **fora de
  transação e sem `FOR UPDATE`**. Outros escritores do mesmo array: `absorver_consolidadas`
  (`repository.py:2525-2532`, em transação mas sem `FOR UPDATE`, então em READ COMMITTED
  também perde) e `caixa_editar_mov` (`repository.py:3856`). A Ficha (pela extensão) e o
  `/salvar` do extrator gravam a mesma conta ao mesmo tempo por desenho.
- **Evidência (COMPROVADO):** `corrida_caixa.py` chama a função real duas vezes em conexões
  distintas, intercaladas (as duas leem antes de qualquer uma gravar): cada uma reporta "1
  adotada", resultado final **`[111]` em vez de `[111, 222]`**: o stake de R$ 70 da segunda
  aposta não volta ao saldo projetado.
- **Severidade:** MÉDIA (janela curta, mas erro de dinheiro silencioso).
- **Família:** ler-calcular-gravar (com A11).
- **Correção:** `UPDATE caixa_mov SET abertas_corte = (SELECT array_agg(DISTINCT x) FROM
  unnest(abertas_corte || $1) x) WHERE id = $2` (atômico), ou `SELECT … FOR UPDATE` dentro de
  transação em todos os escritores.

## A9. Ficha: a chave de idempotência é gravada ANTES do trabalho; falha no meio = aposta nunca planilhada pela Ficha

- **Sintoma:** aposta que a extensão capturou e não aparece; reenviar não resolve.
- **Mecanismo:** `/captura/ficha` grava o cru primeiro (`gravar_cru`, `ficha.py:291-307`,
  `INSERT … ON CONFLICT DO NOTHING RETURNING id`, um commit por item) e só depois monta a
  Ficha e grava a aposta (`ficha.py:575-585`). No reenvio, o cru igual devolve `None` e o
  item é **pulado** (`ficha.py:577`, "a Ficha dele já foi montada"). Se a requisição morrer
  entre os dois passos (deploy, pool travado A3, exceção no `gravar_aceitas`/câmbio), a
  extensão recebe erro e reenvia, mas o servidor acha que já fez.
- **Evidência:** HIPÓTESE forte (fluxo lido no código; não forcei a falha no meio porque
  exige adaptador de família ligado). O efeito "deploy no meio de requisição" é real (A6).
- **Severidade:** MÉDIA.
- **Correção:** marcar o cru como "processado" só no fim (coluna `processado_em`), e no
  reenvio reprocessar cru não processado; ou tudo numa transação.

## A10. Um processo, sem réplica: memória e CPU de um usuário viram limite de todos

- **Sintoma:** lentidão/queda geral em pico; possível reinício por memória.
- **Mecanismo:** `Dockerfile` roda `uvicorn` sem `--workers`; tudo o que é pesado roda no
  mesmo processo (A1, A5, montagem de PDF em thread, imagens base64 de até 12 MB na fila de
  captura em memória: 60 por sessão × até 300 sessões).
- **Evidência:** COMPROVADO o pico de 453 MB com 3 feeds de 60 mil linhas; o limite de
  memória do plano Railway não foi verificado (HIPÓTESE de OOM).
- **Severidade:** ALTA para escalar.
- **Correção:** primeiro tirar o estado da memória (A6) e o trabalho pesado do loop (A1);
  depois múltiplos workers/réplicas e um worker separado para extração e jobs de fundo.

## A11. Custos: duas abas/dispositivos sobrescrevem o blob inteiro

- **Sintoma:** custo lançado "some" depois de mexer em outra aba ou no celular.
- **Mecanismo:** `/custos/store` e `/custos/conta` gravam o **estado completo** mandado pelo
  front (`repository.py:5802-5845`, `5906-5930`), sem versão/ETag. O `semear` tem `FOR
  UPDATE`, a edição normal não precisa de trava porque substitui tudo, e é aí que perde.
- **Evidência (COMPROVADO):** `corrida_custo.py`: aba 1 adiciona `TipB`, aba 2 (estado
  velho) corrige `TipA`; final no servidor: só `TipA`, **`TipB` apagado**.
- **Severidade:** MÉDIA (dado financeiro digitado pelo usuário, perda silenciosa).
- **Correção:** gravação por chave (PATCH de um item) ou controle otimista
  (`atualizado_em` enviado e conferido; 409 se mudou).

## A12. Isolamento multiusuário: sem vazamento encontrado; dois riscos latentes

- **O que conferi:** todas as rotas de dados usam `Depends(dono_efetivo|dono_leitura|
  usuario_atual…)` ou token de sessão de captura; nenhuma lê `dono` de query/corpo. Varri o
  SQL de `repository.py`, `ficha.py`, `virada.py`, `main.py` por consultas a tabelas de
  tenant sem `dono`: os casos que apareceram filtram por `id` já validado contra o dono, ou
  são `{where}` dinâmico com dono. Sem achado comprovado.
- **Riscos latentes (HIPÓTESE de impacto, fato no schema):**
  - `bilhetes.dono`, `parceiros.dono` e outra tabela têm `DEFAULT 'Feca'`
    (`database.py:98`, `131`, `337`): qualquer INSERT futuro que esqueça `dono` grava na base
    do administrador em vez de falhar.
  - `/bilhetes/restaurar` reinsere linhas com `assinatura`, `origem`, `extraction_state`
    vindos do **cliente** (`repository.py:2594-2632`). O dono é o da sessão (sem vazamento),
    mas `origem='sync'` é autoritativa no UPSERT e a assinatura é identidade: o cliente pode
    gerar linha que não deduplica ou que se comporta como fonte determinística.
- **Correção:** remover os defaults (NOT NULL sem default); restaurar a partir da
  `lixeira_bilhetes` pelo `lixeira_id`, nunca do corpo.

---

## Prioridade sugerida (estrutural, nesta ordem)

1. Timeouts e teto: pool com `timeout`/`command_timeout`/`statement_timeout`, healthcheck que
   toca o banco, timeout no fetch (A3). Barato e evita a queda total.
2. Tirar CPU do loop: `to_thread` no login e na montagem do feed; cache por dono invalidado
   pelo `base_mudou` (A1, A5).
3. Uma transação + advisory lock por conta no `upsert_bilhetes` (A2, A7) e atualização atômica
   do `abertas_corte` (A8).
4. Estado de captura e extração no banco, como job (A6, A9). É o que mais muda a experiência
   de quem volta.
5. Feed incremental e limitador global/por dono de IA (A1, A4). Só depois disso, réplicas (A10).

## O que não consegui verificar

- Comportamento real do proxy do Railway: tempo máximo de requisição/stream, buffering do
  SSE, drenagem/SIGTERM no deploy, limite de memória do plano. Tratei como HIPÓTESE.
- Latência de rede app↔Postgres em produção (cada linha do upsert faz até 5 round-trips; com
  1 ms de RTT um lote de milhares fica bem mais lento que o medido aqui).
- Tamanho real das bases em produção e quantas abas/sessões simultâneas existem (não acessei
  produção, por regra).
- Disputa de órfã entre dois lotes simultâneos (A7) e falha no meio da Ficha (A9): lidos no
  código, não reproduzidos.
- Custo de CPU dos jobs de fundo (`dicionario.semear`, `virada`, aquecedor) com dados reais:
  o banco local não tinha `captura_crua` representativa.
- Comportamento da Anthropic sob 32+ chamadas simultâneas da mesma organização (rate limit
  real): só medi a concorrência que o app gera, contra stub.
- Bot de tipster (`sharpen-bot`) e serviço `web` separados: fora deste repo/processo.
- A extensão em navegador real (reconexão, reenvio do cru após 5xx): li `background.js`,
  não executei.
