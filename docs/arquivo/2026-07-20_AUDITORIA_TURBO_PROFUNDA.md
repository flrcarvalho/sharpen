# 🤿 RE-AUDITORIA TURBO — MERGULHO PROFUNDO (Sharpen / Planilhador · 2026-07-20)

> **Segunda passada da Auditoria Turbo, em profundidade.** Rodada na madrugada de **20/07/2026** a pedido do Feca — que corrigiu a definição: _"Turbo é ser o melhor e mais produtivo possível, não terminar rápido. Temos horas e horas, capricha no detalhe. Pensar em escala sempre."_
> **Como foi feito (de verdade):** **219 agentes**, **58 min**, **11,6 milhões de tokens**, **1905 usos de ferramenta**, **0 erros**. Cada agente **leu arquivos INTEIROS** (não trechos), traçou fluxos ponta a ponta, e o chão foi **medido** (suíte, check-tokens, audit_casas rodados de verdade). Cinco fases: regressão na diff de hoje → deep-read por arquivo → modelagem de escala em números → **verificação adversarial de CADA achado (2 lentes)** → **crítico de completude** ("o que a própria auditoria NÃO olhou?").
> Tudo **READ-ONLY** — nenhum arquivo de código/master/casa editado. Supersede o rascunho raso anterior desta data.

---

## 0. Sumário executivo — o que a profundidade mudou

| | Passada rasa (13 min, 27 ag.) | **Mergulho profundo (58 min, 219 ag.)** |
|---|---|---|
| Achados brutos | ~20 | **104** |
| Confirmados pós-adversarial | 14 | **95** (9 refutados) |
| **Altos confirmados (2/2 céticos)** | 1 novo | **17** |
| Médios | 2 | 36 · Baixos 34 · Info 8 |
| De escala | ~7 | **70** |
| **Lacunas de completude** (o que ninguém auditou) | — | **31** + 5 cadeias de risco de 2ª ordem |

**Veredito do CEO, revisado pela profundidade:** o **núcleo continua sólido** — 178 testes verdes, as 29 correções de hoje seguraram, P/L derivado intacto, isolamento por dono re-confirmado. **Mas o mergulho achou uma camada que a passada rasa não via, e ela importa exatamente porque você quer escalar.** Três temas emergiram: **(1) o event loop único é uma fragilidade compartilhada** — várias operações bloqueantes (bcrypt no login, gzip da base inteira, re-zip da extensão, upload sem teto) congelam TODOS os usuários; **(2) falhas silenciosas de dinheiro/dado em escala** — o chunker de modo cego fragmenta bilhete e corrompe stake/odd em casa nova, o import de XLS múltiplo perde arquivos calado, dois goldens ensinam o separador proibido; **(3) superfície de segurança nova** — XSS armazenado via nome de casa, offboarding que não revoga sessão, e — o mais grave achado pela completude — **a base financeira AO VIVO do Fatuch é servida por um Apps Script público sem autenticação**. Nada disso corrompe dinheiro no caminho feliz de hoje; tudo isso é o que quebra quando a base dobra. **Nenhum crítico** sob a operação atual (1 worker, poucos donos); **17 altos** sob a lente de escala.

---

## 1. O chão está firme (medido, não afirmado)

- **Suíte: 178 passed, 4 skipped** (os 4 skipped = harness de DB, só roda no CI com Postgres).
- **check-tokens: VERDE** — porém quantifica o drift: **491 cores literais / 158 valores** fora dos tokens.css (o guardrail barra drift NOVO, não afirma conformidade).
- **audit_casas: sem FAILs** — mas **cego a separador** (passa Betnacional apesar do `' + '`).
- **As 29 correções de hoje: 100% seguraram** (verificação da 1ª passada, re-confirmada aqui).
- **Refactor Polymarket `coletar_tudo`: verde** — provado ponta a ponta que o cache de câmbio não contamina entre bilhetes e não há cross-mutation (subconjuntos disjuntos).

---

## 2. Os 17 ALTOS — agrupados por tema (todos confirmados 2/2 pelos céticos)

### 🔥 Tema A — O event loop único é uma fragilidade compartilhada (disponibilidade/DoS)
> O container roda **1 worker uvicorn**. Qualquer operação bloqueante síncrona no handler async **congela todos os outros** (polls de captura a cada 2,5s, SSE de extração, login, dashboard). Cinco altos convergem aqui.

| # | Achado | Local | Esf. |
|---|---|---|---|
| A1 | **`bcrypt.checkpw` síncrono no `/login`** (~250ms CPU, sem `run_in_executor`) congela o loop a cada tentativa. DoS amplificado + enumeração por timing (usuário inexistente pula o bcrypt). ✅ *verifiquei: `main.py:1190` → `auth.py:137`* | `main.py:1190` | pequeno |
| A2 | **`/extensao/download` re-zipa a pasta inteira síncrono** (rglob+read+deflate), **público, sem auth/rate-limit/cache**. Um laço de GETs anônimos serializa o app. | `main.py:1135` | pequeno |
| A3 | **`/dashboard/data` serializa a base inteira + `gzip` síncrono** no loop, sem paginação nem cache. A 2,5M linhas: 3-8s de loop 100% travado + pico de memória de vários GB por request. | `main.py:1794` · `repository.py:1103` | médio/grande |
| A4 | **Upload multipart parseado e carregado em memória ANTES da auth** — FastAPI lê `request.form()` antes do handler. Um POST anônimo de 5-10GB para `/captura/enviar` enche o disco efêmero e derruba o serviço. | `main.py:1385-1431` | pequeno |
| A5 | **Sem teto de BYTES agregado nas capturas** — só limite por contagem (60/sessão). ~960MB retidos numa sessão abandonada; num container de 1GB, **1 sessão causa OOM** → derruba as 300 pontes + zera o rate-limit. | `captura.py:29` | médio |

**Correção-raiz do tema:** offload de trabalho bloqueante para threadpool (`anyio.to_thread`) + limite de corpo ANTES do parse (middleware ASGI 413) + não guardar imagem base64 em RAM + cache do zip/feed por versão/dono. Mais um guardrail explícito de "1 worker/1 réplica".

### 💸 Tema B — Falhas silenciosas de dinheiro/dado em escala
> Estas **não dão erro** — o número sai "válido" e errado. As mais perigosas porque ninguém percebe.

| # | Achado | Local | Esf. |
|---|---|---|---|
| B1 | **Chunker de modo cego fragmenta 1 bilhete via `split('\n\n')`** — para casa NOVA (sem marcador de fronteira), um card com linha em branco interna vira 2 chamadas de IA → **stake/odd corrompidos sem aviso**. Ataca direto a meta das 50 casas (worldwide). | `main.py:627-636` | pequeno |
| B2 | **Import de XLS múltiplo: a UI mostra N cards, o backend processa só o primeiro** (`xlsFiles[0]`, campo único). Arrasta 3 planilhas → 2 evaporam sem card/alerta/log. Onboarding depende disso. | `index.html:4082` · `main.py:1442` | pequeno |
| B3 | **Dois goldens ensinam o separador `' + '` PROIBIDO** — `CASA_VITORIABET` (3 exemplos) e `CASA_BETNACIONAL` emitem `+` na Descrição; o prompt injeta o arquivo inteiro como few-shot → o modelo replica. As duas redes deterministas (`audit_casas`, `descricao_check`) são cegas a separador. Gera **duplicata-fantasma** no dedup + planilha errada. | `CASA_VITORIABET.md:238,251,290` · `CASA_BETNACIONAL.md:192` | trivial |
| B4 | **P/L Líquido mistura custo de contas filtrado com custo de tipster da vida inteira** (=N3, agora com número: 24 meses × R$3k = filtrar "Hoje" mostra P/L Líquido de **−R$71.500 num dia**). | `overview.js:16-23` | pequeno |

### 🔒 Tema C — Superfície de segurança (nova + profunda)
| # | Achado | Local | Esf. |
|---|---|---|---|
| C1 | **XSS armazenado via nome de casa (modo cego)** — nome persistido verbatim entra cru em `src=`/`data-casa` em 6 sinks. Pior que o refletido: **armazenado** e com caminho **cross-tenant** em conta compartilhada (Feca→Lava). | `index.html:2159+` | pequeno |
| C2 | **XSS refletido `/extensao?v=`** (=N1) — reconfirmado sempre-alcançável (público, não-autenticado). | `extensao.html:158,162` | trivial |
| C3 | **Offboarding via env não revoga sessão** — apagar `SENHA_X_HASH` no Railway (ação natural de desligar) **não invalida o cookie**: `ler_token` só checa `usuario in USUARIOS` (dict hardcoded). Token vive até **30 dias**. | `auth.py:172` | médio |
| — | *(A4 upload-antes-de-auth também é vetor de segurança — ver Tema A)* | | |

### 📉 Tema D — Cliffs de escala (mobile + horizontal + feed + estatística)
| # | Achado | Local | Esf. |
|---|---|---|---|
| D1 | **Casca zero-responsiva** *(única área VERMELHA)* — **0 `@media` na casca**; sidebar rígida de 264px come **68% de um iPhone** e não colapsa; overlays de "dados desatualizados" caem fora da tela no mobile → operador lê cache velho como real. A ferramenta é **inviável no celular**, o dispositivo primário de conferência ao vivo. | `app.html` · `layout.css` · `shell.css` | grande |
| D2 | **Pareamento + rate-limit em memória de processo** — subir para 2+ réplicas Railway mata a captura (**>99% de falha de handshake**: `(1/N)^8`) e multiplica o orçamento de brute-force por N. | `captura.py:101` · `main.py:1165` | médio |
| D3 | **Monte Carlo síncrono** (=N5) — o worker só foi ligado na Visão Geral; **Métricas e drill de tipster seguem síncronos**. Medido: 25k linhas = **13-25s de freeze no browser**; a maior carteira viva **já cruza o watchdog do Chrome hoje**. | `gestao.js:378` · `performance.js:911` | pequeno |
| D4 | **Feed `SELECT *` sem LIMIT + P/L em Python por request** (=raiz de A3) — OOM antes do alvo de escala; ~0,5-1,2 GB transferidos do PG a 2,5M linhas. | `repository.py:1103` | médio |

---

## 3. 🕳️ O que NINGUÉM auditou — o crítico de completude (31 lacunas)

> A parte mais valiosa do mergulho: achar os buracos da **própria auditoria**. Estes não são achados de código — são **superfícies inteiras nunca olhadas**.

**Modalidades/superfícies nunca lidas:**
1. **🚨 `apps_script/Code_LavaFatuch.gs` — `doGet` PÚBLICO sem autenticação.** ✅ *verifiquei: `doGet(e)` na linha 95, zero checagem de segredo/token no arquivo.* É a fronteira que alimenta `planilha_viva.py` — **a base financeira AO VIVO do Fatuch**. Qualquer um com a URL lê os dados. **Merece auditoria dedicada urgente.**
2. **Os 4 inject scripts (`sb/be/bn/bf_inject.js`) — o parser REAL que vira P/L — nunca foram lidos** na lógica de campo. Monkeypatcham `fetch`/`XHR` nas casas e decidem quais campos viram dinheiro. +199 linhas mudadas hoje, zero teste.
3. **`postMessage` sem validação de origin/source** — `content.js` roda em `*://*/*` e lê `ev.data` cru de 4 listeners; injects postam com `targetOrigin '*'`.
4. **Scripts de migração/backfill (`import_*.py`) — `DELETE FROM bilhetes` + INSERT em massa contra o DATABASE_URL de PROD**, sem dry-run, sem transação, zero teste.
5. **Prompt-injection nunca auditado** — texto de OCR/colado vai direto pro Sonnet; um print adulterado pode desviar a extração.
6. **Acessibilidade/teclado, vendor JS (chart.umd/html2canvas sem versão/SRI/CVE), cadeia de deploy/segredos** — modalidades nunca rodadas.

**Claims aceitos sem prova executável:**
- "Isolamento fail-closed" só foi provado na **escrita de 1 função**; as **40+ queries de leitura** por dono nunca foram exercidas contra o banco.
- O **wiring dos 57 endpoints** (44 `dono_efetivo` + 13 `usuario_atual`) que decide leitura-vs-escrita **nunca foi testado** — só a função pura.
- "O P/L bate com a planilha real" **nunca foi reconciliado** contra uma carteira real (só entradas sintéticas).
- `golden_set/bilhetes` **vazio** — a extração print→TSV nunca é verificada ponta a ponta.
- Dedup sem-ID **sob corrida** nunca testada (harness é single-loop).

**5 cadeias de risco de 2ª ordem (piores que a soma das partes):**
- **Cadeia 1 — Segurança de input × isolamento de dados:** XSS (C1/C2) executa na sessão autenticada e alcança rotas de escrita same-origin sob cookie ambiente. Modelar N1+C1 **junto** com o modelo de ameaça multi-tenant, não como bug de UI.
- **Cadeia 2 — Os fixes de latência ARMAM o cliff horizontal:** mover trabalho pra fora do loop convida a subir réplicas — o que detona `_SESSOES` + rate-limit + 3 caches em memória **de uma vez**. Tratar "escala horizontal" como **um** feature-flag com pré-condições acopladas.
- **Cadeia 3 — As 3 redes contra drift de casa falham JUNTAS:** guardrail cego (N4) + golden envenenado (B3) + auditoria amnésica (N13) + 186 pontos hardcoded. Fechar as três na mesma rodada.
- **Cadeia 4 — Ninguém somou a barra de erro do "P/L Líquido":** custo vaza + filtro ignorado + duplicata-fantasma infla stake + P/L sem trilha de auditoria. Fazer **um** exercício de "error budget do P/L".
- **Cadeia 5 — Buraco metodológico:** o `findings.json` é lista PLANA sem arestas de correlação → **estruturalmente não enxerga cadeias**. Evoluir para grafo (`relacionado_a: [ids]` + severidade composta).

**Ângulos de produto/escala (visão CEO):**
- **Unit economics da IA a 100x** — custo registrado, nunca capado nem repassado; sem circuit-breaker por dono.
- **Onboarding de dono é hardcoded** — cadastrar cliente = editar 2 dicts + env + deploy.
- **LGPD** — dado financeiro pessoal de clientes reais, captura passiva de JSON, sem base legal/retenção/DPA mapeados.
- **Fornecedor único em conta PESSOAL** — proxy Polymarket (`flrcarvalho.workers.dev`), chave Anthropic, domínio: SPOF de negócio.
- **Deploy sem migrations versionadas** + **DR/backup do Postgres sem RPO/RTO definido**.

---

## 4. ✅ A verificação adversarial funcionou — 9 refutados

O ceticismo derrubou exageros dos leitores profundos (prova de que os 95 não são inflados):
- **bn_inject "catástrofe"** (liquidado→aberta) → **refutado**: o guard do UPSERT protege (vazio não rebaixa resolvida). *Vira médio como higiene.*
- **`:focus-visible` único / foco invisível** → **refutado**: premissa falsa, não há reset global de outline.
- **DEFAULT `'Feca'` contamina base** → **refutado**: latente, todo INSERT passa dono explícito.
- **Colisão lexical Múltipla×Múltiplos** → **refutado**: não são comparadas como string no código.
- **Overlays brancos invisíveis no claro / redeems / sinais divergentes de "aberta"** → refutados por premissa falsa.

---

## 5. 🎯 FOCO DE AMANHÃ — recalibrado pela profundidade

> O escopo cresceu, mas o princípio segue: **fechável, priorizado, e depois parar de olhar pra trás.** A profundidade **muda a ordem** — agora há itens de disponibilidade/segurança que sobem na fila.

### 🔴 Onda 0 — URGENTE de segurança (curto, alto risco)
- **Fatuch `doGet` público** (completude #1) — proteger a base financeira ao vivo com segredo/HMAC no header. **Antes de tudo.**
- **C1/C2** os dois XSS (nome de casa armazenado + `?v=` refletido) → `textContent`/escape.
- **C3** revogação de sessão no offboarding (claim `iat` + epoch por usuário).

### 🟠 Onda 1 — Tirar trabalho bloqueante do event loop (Tema A, pequeno→médio)
- **A1** `bcrypt` em threadpool + dummy-hash no caminho de usuário inexistente.
- **A2** cache do zip da extensão por versão · **A4** limite de corpo ANTES do parse (413) · **A5** teto de bytes de captura.
- *(A3/D4 feed = médio/grande, planejar; curto prazo: mover `json.dumps`+`gzip` para thread.)*

### 🟡 Onda 2 — Falhas silenciosas de dinheiro (Tema B, trivial→pequeno)
- **B1** exigir marcador de fronteira antes do `split('\n\n')` em modo cego (senão corrompe casa nova).
- **B2** bloquear/loopar XLS múltiplo (não perder arquivo calado).
- **B3** corrigir os goldens de Vitória Bet/Betnacional (`+`→`//`) + ensinar `descricao_check` e `audit_casas` a barrar separador (fecha a **Cadeia 3** inteira).
- **B4** custo de tipster respeitar o filtro de data (+ a sessão do Jonathan: localStorage→Postgres).

### 🟢 Onda 3 — Escala barata de alto valor
- **D3** Monte Carlo async em Métricas/drill (copy-paste do padrão da Visão Geral) — a carteira do Feca já trava hoje.
- Gatear a **Migração A/B** no hot path do upsert.
- **D2** guardrail explícito "1 worker/1 réplica" (torna o invariante à-prova-de-clique).

### 🔵 Onda 4 — Higiene da auditoria (fecha a Cadeia 5)
- Campo `status` + `relacionado_a` no `findings.json` → a próxima rodada custa menos e enxerga cadeias.

### 🅿️ Sessões dedicadas (não amanhã)
Casca responsiva (D1, grande) · auditoria do `Code_LavaFatuch.gs` e dos 4 injects · reconciliação P/L vs planilha real · popular `golden_set` · migrations versionadas + DR · Solidez (redesenho) · Poly incremental · registro `CASA_INGEST` (fecha os 186 hardcoded).

---

## 6. O que segue SÓLIDO (re-confirmado no mergulho)

- **Núcleo de dinheiro (P/L derivado)** — nunca persistido; a rajada não o tocou; as guardas de resultado seguram mesmo com abertas.
- **Isolamento multi-tenant** na escrita — re-confirmado (ressalva: leitura nunca *exercida*, ver completude).
- **Refactor Polymarket `coletar_tudo`** — provado são (câmbio puro por data, subconjuntos disjuntos, sem corrida).
- **UPSERT blindado das abertas** — os dois caminhos (ON CONFLICT + fallback) não divergem; None-safe.
- **SQL parametrizado · CSRF-Origin · cookie HMAC · guardrail de marca bloqueante.**
- **Rede de testes** — os 2 altos de cobertura de ontem fechados; padrão docstring↔bug replicado.

---

_Mergulho profundo em 20/07/2026. Read-only. 219 agentes, 0 erros, 58 min, 11,6M tokens. Deliverables uncommitted. Correções propostas uma a uma no fluxo propor→aprovar→executar. **Este é o retrato para amanhã; depois das ondas, voltar a construir pra frente.**_
