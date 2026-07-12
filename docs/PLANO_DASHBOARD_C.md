# PLANO — Opção C: agregação no servidor do Dashboard

- **Status:** proposta detalhada, aguardando decisão do Feca. Não iniciado.
- **Origem:** ADR-002 (Fase 2, Opção C). Conversa de escala (sessão 128): de ~500 usuários pra cima, C deixa de ser "velocidade" e vira sobrevivência de custo/Postgres.
- **Princípio-guia:** construir **C agora, projetado para virar D depois**. Não construir D já (ver ADR-002 e a discussão de escala). O caro-de-mudar é o **contrato**, não a máquina de materialização.

---

## 1. Problema (recapitulação)

O dashboard baixa a **base inteira** do dono em `/dashboard/data` (~24k linhas do Feca, ~8 MB crus, ~1,2 MB gzip) e faz **toda a matemática no cliente**. Consequências:

- 1ª carga (sem cache) 20-30s; com cache, boot instantâneo com dado velho + revalidação de 20-30s (o que a máscara da sessão 128 disfarça, mas não resolve).
- A carga escala como `payload_por_usuário × concorrência` — a pior combinação. No 15k usuários: ~2,7 TB/mês de egress e Postgres/CPU do app derretendo no pico (ver §6).

**Objetivo de C:** o servidor agrega e manda ~20 KB por página em vez de ~8 MB da base. Carga 20-30s → ~1-2s. Deixa de escalar com o tamanho da base.

---

## 2. O que o dashboard computa hoje (inventário — base para o dimensionamento)

Levantado no código (10 páginas + 3 drills). Classificação: **A** = group-by puro (materializável em SQL) · **B** = varre linhas mas SQL-expressível (acumulado, window, bucket, desvio) · **C** = simulação/stateful (não vira view).

| Página | Computações | Classe dominante |
|---|---|---|
| **Overview** | KPIs (P/L, turnover, ROI, odd média, WR, contagens W/L/HW/HL/V); bankroll (P/L diário + acumulado); ROI mensal; distribuição de odds; Cenário Atual (topo, drawdown atual/máx, recovery); **Diagnóstico de Risco (Monte Carlo 10k)**; calendário | A + B + **C** (Monte Carlo) |
| **Resultados** | KPIs; matriz tipster×período; chart acumulado; dia-da-semana; contribuição/consistência (volatilidade = desvio de P/L mensal); **correlação entre tipsters (Pearson)** | A + B + **C** (correlação) |
| **Esportes** | KPIs de portfólio; cards por esporte (P/L, ROI, turnover, WR, odd ponderada, stake média); sparklines; tabela; drill | A |
| **Casas** | KPIs; cards por casa; drill (janelas turnover 15/30d) | A + B |
| **Apostas** | KPIs; **tabela espelho da base (virtual scroll, filtro por coluna, sort)** | **linhas cruas** — não agregável |
| **Tipsters** | KPIs; cards por tipster; comparativo; drill | A |
| **Parceiros/Fornecedores** | resumo por fornecedor; cross casa×fornecedor; contas individuais (P/L, ROI, 1ª/última aposta) | A |
| **Custos de Contas** | contagem de contas por casa×fornecedor + custo unitário | A + **localStorage** |
| **Custo de Tipsters** | tabelas mensais de custo | **100% localStorage** |
| **Métricas** | fundamentais + risco (MDD, recovery) + **Monte Carlo (p-value, DD p95/p99, Solidez)** | A + B + **C** |
| **Drills (×3)** | KPIs, análise mensal, breakdown por casa/esporte, chart acumulado, **Cenário + Risco (Monte Carlo)** | A + B + **C** |

**Conclusão:** a **grande maioria é A** (group-by direto). Poucos **B** (curvas/janelas/desvio). Os **C irredutíveis** são poucos e concentrados: **Monte Carlo** (presente em quase toda página via "Diagnóstico de Risco") e a **correlação de tipsters**. Calendários são A com layout próprio.

---

## 3. Arquitetura de C (as decisões que importam)

### 3.1 Contrato novo (a interface — acertar isto é "crescer certo")

Trocar o `/dashboard/data` (array de linhas) por endpoints **agregados e parametrizados por filtro**:

- **`GET /dashboard/summary?dono&sport&casa&tipster&operador`** → devolve **buckets diários** (por dia: `{n, wins, halfwins, losses, void, stake, retorno, pl}`) + os group-bys por dimensão (esporte/casa/tipster/fornecedor) + KPIs. ~5-20 KB.
- **`GET /dashboard/risk?…filtros`** → os cálculos **C** (Monte Carlo, drawdown, correlação) já computados no servidor. Devolve ~dezenas de números. **Lazy** (como o worker é hoje).
- **`GET /dashboard/apostas?…filtros&page&sort`** → **linhas cruas paginadas** para a tabela-espelho (única página não-agregável).
- **`GET /dashboard/meta`** → listas de filtro (esportes/casas/tipsters/operadores distintos) + **accounts-meta** (conta → data da 1ª aposta), pequeno.

### 3.2 A jogada de UX: navegação de período fica no cliente

O filtro mais usado é **período**. Se o servidor manda **buckets diários**, o cliente **fatia o período localmente** (soma os dias do intervalo) e recompõe KPIs + bankroll **sem round-trip** — navegação dia/mês/WTD/MTD/YTD instantânea, igual hoje. Só os filtros **categóricos** (esporte/casa/tipster/operador) batem no servidor (mudam o agrupamento), com cache. Isso preserva a fluidez atual onde ela mais importa.

### 3.3 Custo continua no cliente (NÃO é bloqueador de C)

Correção importante ao que se supunha: **migrar os custos (localStorage) NÃO é pré-requisito de C.** O servidor manda os agregados **brutos**; o cliente aplica a **camada de custo por cima** (subtração fina), lendo o custo do `localStorage` como hoje, e usando a **accounts-meta** (data da 1ª aposta por conta, vinda de `/dashboard/meta`) para o `calcCostFiltered`. Migrar custo para o Postgres vira um trabalho **separado e opcional** (necessário só para D/materialização de P/L líquido ou custo cross-device) — e de quebra corrige o vazamento do store global de custo de tipster.

### 3.4 Onde a matemática roda (a chave do "C agora, D depois")

Dois backends de dados hoje (Postgres para todos, exceto `LavaFatuch` que é Apps Script/Google Sheets). Para casar isso com escala **sem sacrificar paridade**, faseia-se **onde** a agregação roda:

- **Fase 1 — agregação em Python no app server.** As linhas são buscadas como hoje (Postgres + planilha), mas a **matemática roda no servidor** (um agregador Python único, source-agnóstico: opera sobre a lista de linhas venha de SQL ou da planilha). Ganho imediato: payload do cliente 8 MB → ~50 KB, CPU do cliente zerada, parse de 8 MB some. Carga 20-30s → ~2-5s. **Ainda lê todas as linhas do Postgres** (não corta a carga de DB), mas já entrega o maior ganho (cliente + egress + serialize) com **risco baixo** e um único lugar para provar paridade.
- **Fase 2 — GROUP BY em SQL para o caminho Postgres** (atrás do mesmo contrato). O Postgres agrega e devolve centenas de linhas em vez de 24k → corta leitura de DB + CPU do app. O caminho Apps Script continua com o agregador Python (é 1 dono).
- **Fase 3 / D — views materializadas** para os group-bys pesados, atualizadas por gatilho/cron → carga de DB perto de zero no pico. Só quando a concorrência (milhares) justificar.

O agregador Python da Fase 1 **é** a especificação executável que a Fase 2 traduz para SQL. Escrever os agregados como GROUP BY-expressíveis desde já é o que torna a Fase 2/D **mecânica** (o guardrail do "crescer certo").

### 3.5 Os cálculos C (Monte Carlo, correlação)

Dependem do **recorte filtrado**, não de dimensões fixas → **não** viram view. Migram para Python/numpy no `/dashboard/risk`, computados por request e **cacheados por assinatura de filtro**. Paridade **estatística** (tolerância), não bit-exata — o RNG (`mulberry32`) e o bootstrap não precisam bater dígito a dígito, só distribuição. Alternativa considerada e descartada: manter no cliente exigiria enviar P/L por bilhete do recorte (grande no não-filtrado).

### 3.6 Normalização de nomes

`normalizeDados` (canoniza tipster/casa/esporte por frequência) roda no cliente hoje **antes** de qualquer group-by. Precisa migrar para o servidor (senão os group-by divergem). Melhor: **normalizar na ingestão** (gravar nome canônico) ou um passo de canonização no agregador. Testar que as chaves de group-by batem com os números atuais.

### 3.7 Boot offline preservado (melhorado)

Mantém-se o IndexedDB + stale-while-revalidate, mas cacheando os **blocos agregados (~20 KB)** em vez da base (~8 MB). Boot instantâneo continua, agora barato, e a máscara de sincronização (sessão 128) cobre a revalidação — que agora dura ~1-2s, não 20-30s.

---

## 4. Fases e previsão de entrega

Assume execução assistida por Claude Code (Feca + IA), meio-período. Gates entre fases.

| Fase | Escopo | Entrega (calendário) | Gate para avançar |
|---|---|---|---|
| **0 — Revalidação condicional (independente de C)** | `/dashboard/data` responde `304` quando o `builtAt` do cliente == servidor (cliente já rastreia `builtAt`). Mata o re-fetch de 8 MB a cada open sem mudar nada de arquitetura. | **~1 sessão (½ dia)** | Ship imediato — alívio de escala grátis |
| **1 — C-core (agregação Python + contrato + refactor do cliente)** | Agregador Python source-agnóstico; endpoints `summary`/`risk`/`apostas`/`meta`; refactor do cliente (fetch no lugar de `DADOS`); camada de custo por cima; **harness de paridade**; MC/correlação em numpy. Piloto na **Overview**, depois fan-out página a página (pipeline). | **~2-3 semanas** (piloto Overview ~3-4 sessões; fan-out ~1-2 sessões/página) | Paridade validada na base real + ganho de carga medido |
| **2 — SQL GROUP BY (caminho Postgres)** | Substitui a agregação Python do Postgres por SQL, atrás do mesmo contrato. Corta leitura de DB + CPU do app. | **~1 semana** | Concorrência real justificando (medição) |
| **3 / D — Views materializadas** | Materializa os group-by pesados + refresh por gatilho/cron. | **Adiado** — gatilho ~500-1000 usuários | Medição de carga de DB no pico |

**Marco "C entregue" (Fases 0+1):** ~3-4 semanas meio-período. É onde mora ~99% do ganho de cliente/egress e ~15-20× de tempo de carga.

---

## 5. Custos financeiros

### 5.1 Delta de infra (recorrente) — C **economiza**

Egress/mês (≈2% de concorrência, ~5 opens/dia; atual 1,2 MB vs C 20 KB por open):

| Usuários | Egress atual | Egress com C | $ atual (~$0,10/GB) | $ com C |
|---|---|---|---|---|
| 100 | ~18 GB | ~0,3 GB | ~$2 | ~$0 |
| 500 | ~90 GB | ~1,5 GB | ~$9 | ~$0,15 |
| 1.000 | ~180 GB | ~3 GB | ~$18 | ~$0,30 |
| 2.000 | ~360 GB | ~6 GB | ~$36 | ~$0,60 |
| 15.000 | ~2.700 GB | ~45 GB | **~$270** | **~$4,50** |

Além do egress: a Fase 1 corta CPU do app (fim do serialize de 8 MB/request) e a Fase 2 corta leitura de Postgres (GROUP BY devolve centenas de linhas, não 24k). Cache (in-process = grátis; Redis no Railway ~$5-10/mês se preferir compartilhado) colapsa opens repetidos. **Sem C, a conta de infra e o Postgres viram o teto de escala; com C, deixam de ser o gargalo.**

### 5.2 Custo de build (uma vez)

- **Tempo de engenharia** (assistido por Claude Code): Fase 0 ~½ dia; Fase 1 ~2-3 semanas meio-período; Fase 2 ~1 semana. É o custo dominante — mas é **tempo**, não dinheiro direto.
- **Custo de tokens de IA:** ordem de grandeza de **baixas centenas de dólares** para o build inteiro (dominado pelas sessões Opus do núcleo de paridade; o fan-out em Sonnet é barato). Trivial perto do que a infra economiza e do risco que remove. Para orçamento fino, confirmar preços atuais dos modelos antes.

---

## 6. Riscos e mitigação

| # | Risco | Severidade | Mitigação |
|---|---|---|---|
| 1 | **Divergência de número** (SQL/Python vs JS de hoje) — corrói confiança silenciosamente | **Alta** | **Harness de paridade**: roda os dois caminhos sobre a base real + combinações-golden de filtro e faz diff de cada KPI por página. Ship atrás de flag; dual-run em produção comparando antes de cortar o legado. |
| 2 | **Monte Carlo/correlação não-determinístico** entre JS e Python | Média | Paridade **estatística** com tolerância (não bit-exata); seed controlado; validar distribuição, não dígito. |
| 3 | **Regressão de UX nos filtros** (round-trips) | Média | Buckets diários → período fatiado no cliente (instantâneo); só categórico bate no servidor; cache + optimistic. |
| 4 | **Custo em localStorage** | Baixa (desacoplado) | Camada de custo fica no cliente sobre os agregados brutos; servidor manda accounts-meta. Migração de custo é trabalho separado/opcional. |
| 5 | **Caminho Apps Script (LavaFatuch)** não alcançável por SQL | Média | Agregador Python é source-agnóstico (roda sobre o array da planilha também). Longo prazo: migrar LavaFatuch para Postgres. |
| 6 | **Perda do boot offline** | Baixa | SWR preservado sobre blocos de ~20 KB; com carga ~1-2s o offline importa pouco. |
| 7 | **Normalização de nomes** diverge se não migrar | Média | Portar a canonização por frequência para o servidor (ou normalizar na ingestão); testar chaves de group-by. |
| 8 | **Vazamento entre tenants** em query nova | Alta (se ocorrer) | Escopo por `dono` em TODO endpoint; teste de isolamento cross-dono. |
| 9 | **Reescrita de núcleo (scope creep)** | Média | Fatiar página a página (pipeline), flag-gated; piloto Overview prova antes do fan-out. |
| 10 | **Bug pré-existente:** store de custo de tipster é global (não escopado por dono) | Baixa | Fora do escopo de C; corrigir junto se/quando migrar custo para o Postgres. |

---

## 7. Quem executa: Opus, Sonnet ou Fable?

O trabalho tem duas naturezas distintas — a recomendação é **híbrida**:

| Parte | Natureza | Modelo ideal |
|---|---|---|
| Desenho do contrato; **agregador de paridade** (odd ponderada, WR com HW/HL, drawdown/window, consolidação dos 2 backends); **port de Monte Carlo/correlação** para numpy; harness de paridade | Correção crítica, equivalência numérica sutil, estatística | **Opus 4.8** — um número errado aqui contamina a confiança em silêncio; é onde a capacidade máxima paga |
| Wiring dos endpoints por página; refactor do cliente (fetch no lugar de `DADOS`); paginação da tabela Apostas; testes; fan-out página a página | Volume mecânico, bem-especificado depois do contrato pronto | **Sonnet 5** — cobre a largura com bom custo |
| Polimento cosmético (estados de loading, cópia) | Não-crítico | **Fable 5** opcional — orientado a geração rápida/criativa, **não** para o núcleo de correção/estatística; manter fora do caminho crítico |

**Fluxo recomendado no Claude Code:** Opus como loop principal desenhando o contrato e dono do núcleo de paridade; Sonnet em subagentes para o fan-out de endpoints/cliente/testes. Fable, se usado, só em bordas cosméticas.

---

## 8. Recomendação / próximo passo

1. **Fazer a Fase 0 já** (revalidação condicional `304`) — barata, independente de C, e sozinha já tira o maior desperdício de escala (re-fetch de 8 MB a cada open).
2. **Piloto da Fase 1 só na Overview** — construir o agregador + `/dashboard/summary` + refactor da Overview + harness de paridade, provar que os números batem na base real e **medir** o ganho de carga. Isso valida o contrato e o método antes de comprometer o fan-out.
3. Só depois do piloto validado, **fan-out** do resto das páginas.
4. **Fases 2 e D ficam gated** por medição de carga real (não fazer no escuro).

> Regra de ouro: o valor de C está em acertar o **contrato** e escrever os agregados **SQL-expressíveis**, para a promoção a view materializada (D) ser mecânica quando a carga chegar. Construir C assim é o que significa "crescer certo".
