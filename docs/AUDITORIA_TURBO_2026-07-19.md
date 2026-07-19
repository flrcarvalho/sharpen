# 🔍 AUDITORIA TURBO — Sharpen / Planilhador

> **Maior auditoria já feita no projeto.** Rodada na madrugada de **18→19/07/2026** a pedido do Feca ("modo turbo, tudo precisa estar perfeito").
> **CEO** (orquestrador) → **9 gerências** → **26 especialistas** em paralelo, com **verificação adversarial** dos achados críticos/altos.
> Tudo **READ-ONLY** — nenhum arquivo de código, master ou casa foi editado. Os achados são propostas para o Feca aprovar ponto a ponto.
> Relatórios completos por área: [`docs/auditoria_turbo/`](auditoria_turbo/). Dados brutos: [`docs/auditoria_turbo/findings.json`](auditoria_turbo/findings.json).

---

## 0. Sumário executivo

| Métrica | Valor |
|---|---|
| Especialistas | 26 (23 no workflow + 3 reforços) em 9 gerências |
| Achados brutos | 188 |
| Refutados na verificação | 2 |
| **Sobreviventes** | **~200** (186 + 3 reforços) |
| **Críticos** | **0** |
| **Altos** | **7** (2 UX/dinheiro + 2 cobertura de teste + 2 UI + 1 Polymarket/decisão) |
| Médios / Baixos / Info | ~63 / ~70 / ~64 |
| Baseline de saúde | ✅ 140 testes passam · `check-tokens` verde · compila · working tree limpo, tudo pushado |

> ### ⚙️ Progresso da execução (sessão 158 — 19/07)
> **11 correções no ar** (uma por commit, todas testadas · suíte 140 → 169):
> - **Onda 1** — schema banco vazio `201b223` · polymarket/sync base certa `eee55c1` · P/L zero neutro `31166ad` · tooltip+dot HW/HL `d2f23ba`. _(custo tipster #1/#2 → amanhã com Jonathan)_
> - **Onda 2** — X-Forwarded-For `afad142` · `.dockerignore` `947cef7` · SESSION_SECRET fail-closed `06be977` · `test_auth.py` (27 testes) `0bf12f2`. _(resta #11 harness de DB)_
> - **Onda 3** — índices em `bilhetes` `8e6e7c4`. _(resta #13 autodiagnóstico, #14 domain.py, #14b polymarket robustez)_
> - **Onda 4** — win rate backend = dashboard (HW=½) `0941bf7`. _(resta solidez #15/#16, backtest #18)_
> - **Onda 6** — faxina: planos→docs/, link, remove NOTA `0d528a0`. _(resta re-sync docs, Backups retenção)_
>
> Abertos maiores: Onda 5 (dados), A (polymarket robustez). Verificação visual ao vivo (Ctrl+F5) pendente.

**Veredito global do CEO:** o sistema está **firme e no ar, sem nada crítico e sem risco ativo de corromper dinheiro ou vazar dado entre clientes nos caminhos atuais.** As duas fundações mais importantes — **núcleo de dinheiro** (P/L derivado) e **isolamento multi-tenant** — foram auditadas a fundo e voltaram **sólidas e bem defendidas**. O que existe é uma camada de **dívida de segunda ordem** (bugs de UI/filtro, cobertura de teste nas bordas, drift de cor, dívida de arquitetura e escala) e uma **defasagem dos documentos de planejamento** que faz o backlog parecer pior do que é. Saúde por área: **verde** em Segurança/Infra; **amarelo** em todo o resto; **nenhuma vermelha**.

---

## 1. Contexto operacional da noite (terminais paralelos)

O Feca rodou **vários terminais em paralelo** antes de dormir. Diagnóstico:

- ✅ **Sem perda de trabalho.** Working tree limpo, `origin/main` atualizado. A sessão 157 deixou a `NOTA_AO_AUDIT.md` confirmando isso.
- ⚠️ **Colisão de sessões:** o commit **`3798488`** (rotulado "faxina da janela deslizante") **varreu junto** o trabalho de "Baixar CSV de-triplicado" (app.html, index.html, app.js, layout.css, dash/index.html). **A mensagem do commit engana** — quem auditar por commit precisa abrir o diff completo. Lição já anotada pela 157: evitar duas sessões editando/commitando o mesmo working tree.
- ⚠️ **Servidor dev vivo:** sobrou um **uvicorn na porta 8000 (PID 4048)** + processos python/node dos terminais. Não matei (podem ser intencionais) — decisão sua.
- ⚠️ **`NOTA_AO_AUDIT.md` está commitada** na raiz — deve sair depois desta auditoria (`git rm`).

---

## 2. 🎯 As prioridades reais (o que atacar primeiro)

> Ordenado por **impacto ÷ esforço**. Cada bloco é uma "onda" que pode virar uma sessão focada. Todos os itens marcados ✅ foram **verificados por mim direto no código**, não só reportados.

### 🌊 Onda 1 — Correções rápidas de dinheiro/dados (algumas horas, alto valor)
> **🟠 ATUALIZAÇÃO 19/07 — itens #1 e #2 ADIADOS (incidente de produção do Jonathan).** O achado foi **confirmado ao vivo**: o Jonathan preencheu o Custo por Tipster no PC do trabalho e viu a tabela quase zerada em outra máquina (só o Arrudex sobreviveu). A causa é o furo (2) — localStorage não sincroniza entre aparelhos nem tem backup no servidor. **A direção mudou:** escopar por `::dono` no localStorage é só paliativo; a correção definitiva é **migrar Custo por Tipster + Custo Geral para o Postgres, por dono**. **⚠️ Recuperação: a cópia completa do Jonathan só existe no localStorage do PC do trabalho — a subida pro Postgres tem que ser ação EXPLÍCITA disparada daquela máquina (auto-migração oficializaria a cópia incompleta se outra máquina abrir primeiro). Não tocar nas chaves de localStorage antes do Jonathan confirmar.** Detalhe na memória `custo_tipster_incidente_jonathan`.

| # | Achado | Local | Sev | Esforço | Verificado |
|---|---|---|---|---|---|
| 1 | **Custo de Tipsters e Custos Gerais vazam entre donos + não sincronizam entre aparelhos** → migrar p/ Postgres por dono (ver nota acima) | `dash/assets/js/app.js:907-915` | **Alto** | médio | ✅ **prod** · ⏸️ adiado |
| 2 | **P/L Líquido subtrai custo de tipster do histórico inteiro, ignorando o filtro de data** (acoplado ao #1) — decisão do Feca: **respeitar o filtro** (somar só meses no período, igual custo de contas) | `charts/overview.js:16-23` | **Alto** | médio | ✅ · ⏸️ com o #1 |
| 3 | **Schema quebra banco vazio**: `UPDATE parceiros` roda antes do `CREATE TABLE parceiros` → rollback total em DR / novo cliente / dev local | `app/database.py:60-69` | Médio | trivial | ✅ |
| 4 | **`/polymarket/sync` grava na base errada** em modo "ver como" (`Depends(dono_efetivo)` em vez de `usuario_atual`) | `app/main.py:1565` | Médio | trivial | ✅ |
| 5 | **`fmtPL` do dashboard pinta P/L zero de verde com `+`** (viola §5.1; todo Void aparece verde) | `dash/assets/js/app.js:14` | Médio | trivial | ✅ |
| 6 | **Tooltip do gráfico de Esportes vaza HTML cru** (`<span class="money">…</span>` literal na tela) | `charts/performance.js:154` | Médio | trivial | — |
| 6b | **`.dot.hw` e `.dot.hl` pintam meia-vitória e meia-derrota com o MESMO âmbar** → indistinguíveis na streak + viola marca (`!important` trava override) | `dash/assets/css/components.css:662-663` | **Alto** (UI) | baixo | ✅ |

> **Itens 1 e 2 estão acoplados** (o vazamento alimenta a fórmula) — tratar na mesma sessão.
>
> **✅ STATUS 19/07 (sessão 158):** tiros **3, 4, 5, 6, 6b FEITOS e no ar** — schema (`201b223`), polymarket/sync (`eee55c1`), fmtPL zero neutro (`31166ad`), tooltip HTML + dot HW/HL (`d2f23ba`). **#1 e #2 (custo) adiados** para amanhã com o Jonathan (migração p/ Postgres, recuperação manual — ver nota acima).

### 🌊 Onda 2 — Segurança barata + rede de testes das bordas
| # | Achado | Local | Esforço |
|---|---|---|---|
| 7 | **`SESSION_SECRET` fail-closed em produção** (hoje cai em segredo efêmero e só avisa → login some a cada restart) | `app/auth.py:37` | pequeno |
| 8 | **Rate-limit não confiar em `X-Forwarded-For` spoofável** (confiar só no hop do proxy Railway) | `app/main.py` | pequeno |
| 9 | **Criar `.dockerignore`** (hoje `Backups/` + `__pycache__` entram no contexto de build) | raiz | trivial |
| 10 | **`tests/test_auth.py`** — auth.py é 100% função pura e **não tem um único teste**; guarda a fronteira entre inquilinos (forja de cookie, escalada de privilégio) | `app/auth.py:116-204` | pequeno |
| 11 | **Harness de camada-DB** para exercer `upsert_bilhetes` + queries por `dono` (hoje o conftest stuba o banco → ~50 funções async sem teste: dinheiro, dedup, tenancy) | `app/repository.py:614-870` | grande |

> Itens 7-9 são o "trio barato de segurança" — fazer os três juntos numa sessão.
>
> **✅ STATUS 19/07 (sessão 158):** trio de segurança **FEITO e no ar** — SESSION_SECRET fail-closed em produção (`06be977`, segredo setado no Railway pelo Feca), X-Forwarded-For não-spoofável (`afad142`), `.dockerignore` (`947cef7`). **#10 `test_auth.py` FEITO** (`0bf12f2`, 27 testes, suíte 140→167). **Resta #11** — harness de camada-DB (exercer `upsert_bilhetes` + queries por dono; esforço grande, sessão dedicada).

### 🌊 Onda 3 — Arquitetura de maior retorno
| # | Achado | Local | Esforço |
|---|---|---|---|
| 12 | **Índices na tabela `bilhetes`**: `(dono, criado_em)` p/ o feed + parcial `(dono, codigo_bilhete)` p/ o pré-dedup. Hoje toda home é seq scan + sort por dono | `app/database.py:8-29` | pequeno — **maior ROI por hora** |
| 13 | **Autodiagnóstico universal nas casas-robô da extensão** (só a Betfair tem). Quando a casa muda o DOM, a captura **zera silenciosamente** e o cliente só descobre reclamando | `extensor/content.js` | médio |
| 14 | **Separar `repository.py` em `domain.py` (puro) + `repository.py` (só DB)** — destrava teste unitário do dedup e remove stubs asyncpg do conftest | `app/repository.py` | médio |
| 14b | **Robustez Polymarket**: paginação sem teto (loop infinito com proxy travado), `_portfolio` engole exceção e devolve R$0 (deveria ser `None`→"—") | `app/polymarket.py:97-111, 714-726` | pequeno |
| 14c | **`.seg-btn` órfão + duplicação de componentes CSS**: segmented-button existe em 4 cópias (a "canônica" tem zero uso), pill de resultado e número de KPI reimplementados 2-4× | `dash/assets/css/components.css` | médio |

### 🌊 Onda 4 — Fórmulas / estatística (antes de escalar a inteligência de tipster)
| # | Achado | Local | Esforço |
|---|---|---|---|
| 15 | **Solidez sela perdedor como "Baixa", nunca "Muito Baixa"** — 40% do índice é agnóstico a lucro; book grande e perdedor floreia. Adicionar gate de rentabilidade | `charts/app.js:253-261` | pequeno |
| 16 | **Solidez infla para edge trivial** — +0,5% de yield sobre 25k apostas vira "Muito Alta" (significância estatística ≠ prática). Separar força do sinal de tamanho de amostra + disclaimer | `charts/app.js:253-261` | médio |
| 17 | **Win Rate diverge entre extrator e dashboard** — backend conta HW como vitória cheia; front usa ½. Mesma conta, dois números. Reabre o #27 da AUDITORIA_2026 | `app/repository.py:1107-1115` | pequeno |
| 18 | **Backtest do matcher não faz split temporal** que o próprio plano exige, e não mede Jonathan/Lava (`criado_em` constante em base importada) — as carteiras que provariam overfit ao Feca | `scripts/backtest_matcher.py` | médio |

### 🌊 Onda 5 — Dados / domínio
| # | Achado | Local | Esforço |
|---|---|---|---|
| 19 | **Separador de bet builder divergente**: mesmo tipo de aposta sai no TSV como ` // `, ` & ` **e** ` + ` — dois não existem no global (fere invariante #2). Decidir no `MASTER_DESCRICAO §16` | `casas/*` | médio |
| 20 | **3 lacunas de propagação entre masters**: `Primeiro/Último Marcador` órfãos, `aposta aberta → Resultado vazio` não propagada ao OUTPUT, `Múltiplos` fora da whitelist de ESPORTES §7 | `global/*` | trivial cada |
| 21 | **Popular `golden_set/bilhetes/`** — não há nenhuma regressão print→TSV por casa; editar um §9 errado não quebra teste nenhum | `golden_set/` | grande |

### 🌊 Onda 6 — Organização (a bússola aponta pro retrato errado)
| # | Achado | Ação | Esforço |
|---|---|---|---|
| 22 | **Docs de consolidação defasados ~35 sessões** (ONDE_ESTOU / AUDITORIA_2026 / Ideias escritos na sessão 122; STATUS já na 157) | Re-sincronizar + travar cadência (dentro do `/encerrar`) | pequeno |
| 23 | Itens **já resolvidos ainda listados como abertos** (win rate ½ #27, rename métricas #29-31, CASA_BETANO scraping) | Corrigir os docs | trivial |
| 24 | **2 planos na raiz** contra a estrutura `/docs` declarada + link quebrado no HISTORICO + `NOTA_AO_AUDIT.md` commitada | Mover p/ docs/, corrigir link, `git rm` | pequeno |
| 25 | **`Backups/` sem política de retenção** (55MB, 370 pastas; copia HISTORICO 497KB a cada backup) | Retenção N sessões/90d + parar de copiar HISTORICO | pequeno |

---

## 3. ⚖️ Decisões que precisam de você (Feca)

1. **Pendência da sessão 157 (NÃO toquei):** gatear o botão "Atualizar" (`#hostRefresh`) da casca por `planilha_ao_vivo(dono)`. **Bloqueio:** dentro do `/app` a sidebar do dash é escondida, então esse é o único "Atualizar" visível; esconder pra base Postgres deixaria todos menos o Fatuch sem o botão até existir auto-sync. **Decisão A** (adiar/juntar com auto-sync) vs **B** (esconder já). Ver memória `rodape_sidebar_botoes_decisao`.
2. **Separador de bet builder** (#19): mesmo símbolo próprio no §16, ou converter tudo para ` // `?
3. **Qual verde/vermelho é o oficial dos gráficos** (#3 de UI) — hoje há 4 verdes e 3 vermelhos hardcoded pro mesmo "positivo/negativo".
4. **HW conta meia vitória no win rate?** (#17) — decisão de produto que muda o número exibido.
5. **Polymarket — odd de entrada vs realizada:** hoje a odd gravada é `1/preço` (entrada) e o P/L a trata como realizada → **superestima o lucro das vitórias** pela taxa/slippage on-chain; a doc `CASA_POLYMARKET §11` diz o oposto do código. **(a)** manter odd de entrada e corrigir a doc, ou **(b)** persistir P/L realizado (`cashPnl`) separado para os agregados da casa? (dívida conhecida #32)
6. **Matar os processos/porta 8000** dos terminais paralelos?

---

## 4. Relatórios por gerência (digest + link)

> Cada gerência tem o relatório completo em [`docs/auditoria_turbo/gerente_<Area>.md`](auditoria_turbo/).

### 🟡 Código — [`gerente_Codigo.md`](auditoria_turbo/gerente_Codigo.md)
**Sólido.** Núcleo de dedup/persistência, tenancy e segurança maduro, sem bug crítico de correção. Urgência única: ordem do SCHEMA_SQL (banco novo). Reforço do `main.py`: **loop de continuação sem teto de tokens** (custo ilimitado), `texto`/`csv_content` sem limite de tamanho, chunker `\n\n` fragmenta casa em modo cego, `_cache_warmer` sem referência (GC) e sem timeout total no modelo. Reforço do **Polymarket** ([`gerente_Codigo_reforco_polymarket.md`](auditoria_turbo/gerente_Codigo_reforco_polymarket.md)): odd entrada vs realizada (decisão #5), paginação sem teto, `_portfolio` engolindo erro; **câmbio guard exemplar** (falha em vez de mentir). **Positivos:** P/L correto, SQL 100% parametrizado, canonização de resultado, isolamento por dono, retry idempotente, hardening de perímetro.

### 🟡 Fórmulas — [`gerente_Formulas.md`](auditoria_turbo/gerente_Formulas.md)
**Precisa atenção.** O dinheiro (P/L) está correto e espelha a planilha; o problema é o índice composto **"Solidez"** (dois modos de falha: sela perdedor e infla edge trivial) e o **backtest de tipster que não mede o que promete** (sem split temporal, ignora carteiras importadas). Win rate diverge front↔backend. **Positivos:** P/L centralizado e correto, odd com precisão plena, Monte Carlo/bootstrap bem construídos, unidades corretas e testadas, disclaimers honestos.

### 🟡 UI — [`gerente_UI.md`](auditoria_turbo/gerente_UI.md)
**Sólido com atenção.** Fundação (guardrail + tokens) robusta. Defeitos: `fmtPL` pinta zero de verde, tooltip vaza HTML, **4 verdes + 3 vermelhos hardcoded** fora de token nos gráficos, ticks de eixo abaixo do mínimo WCAG. Reforço do `components.css` ([`gerente_UI_reforco_components.md`](auditoria_turbo/gerente_UI_reforco_components.md)): **`.dot.hw/.hl` âmbar idêntico** (bug visível), **`.seg-btn` órfão** + segmented-button/pill/KPI-number duplicados, contraste `--ink-mute` 3.2:1 em labels pequenos, z-index sem sistema, falta `:focus-visible`. **Positivos:** `check-tokens` bloqueante, `.money` implementa o §5, colisão `.kpi` resolvida com disciplina, heatmaps daltônico-safe, tokens theme-aware.

### 🟡 UX — [`gerente_UX.md`](auditoria_turbo/gerente_UX.md)
**Sólido no núcleo.** Fluxo de extração/análise resiliente e bem feito. 2 altos de dinheiro (vazamento de custo + filtro de data), edição inline sem pista visual (`class` duplicado descarta `.ap-edit`), dashboard sem responsividade (`layout.css` sem `@media`). **Positivos:** contador 15/15, cards paralelos com progresso granular, carimbo de hora, datas em fuso local, virtual scroll, boot instantâneo.

### 🟡 Arquitetura — [`gerente_Arquitetura.md`](auditoria_turbo/gerente_Arquitetura.md)
**Sólido no núcleo, dívida crescente.** Sem crítico/alto. Topo: autodiagnóstico das casas-robô, índices na `bilhetes`, split `domain.py`. Comportamento por casa hardcoded em Python contradiz o invariante "casa localiza, global calcula". Sessão de pareamento em memória = cliff de escala. **Positivos:** P/L nunca persistido (decisão mais elegante do sistema), multi-tenancy fail-closed, extensão passiva de leitura de API, `corrigir_codigos_tsv` determinístico.

### 🟢 Segurança — [`gerente_Seguranca.md`](auditoria_turbo/gerente_Seguranca.md)
**Verde.** A varredura dedicada voltou quase vazia (1 achado placeholder de baixa confiança). **A cobertura de segurança real veio das gerências Código/Infra e Arquitetura** e foi positiva: CSRF por Origin, CSP + headers, SQL parametrizado, isolamento por dono fail-closed, cookie HMAC. Os itens acionáveis de segurança são o **trio barato** da Onda 2 (SESSION_SECRET, X-Forwarded-For, .dockerignore).

### 🟡 Dados — [`gerente_Dados.md`](auditoria_turbo/gerente_Dados.md)
**Sólido.** 6 masters maduros, 14 casas passam no auditor determinístico. Sem crítico/alto. Degraus que a IA tropeça: separador de bet builder, marcadores órfãos, dessincronia OUTPUT↔RESULTADO, `Múltiplos` fora da whitelist. **Positivos:** auditor determinístico verde, cashout padrão-ouro de propagação, guardas anti-colapso de dedup, casas atípicas bem traduzidas, **CASA_BETANO já não descreve scraping** (dívida da memória resolvida).

### 🔴→🟡 Testes — [`gerente_Testes.md`](auditoria_turbo/gerente_Testes.md)
**Atenção (2 dos 4 altos da auditoria).** Núcleo matemático exemplarmente coberto, mas **as bordas de maior risco estão 100% descobertas**: `auth.py` sem nenhum teste (isolação/forja de sessão) e o caminho de escrita de dinheiro (`upsert_bilhetes` + queries por dono) sem teste porque o conftest stuba o banco. **Positivos:** `test_formulas`/`test_dedup`/`test_assinatura_edicao` amarram cada caso ao bug real — o padrão a replicar.

### 🟡 Organização — [`gerente_Organizacao.md`](auditoria_turbo/gerente_Organizacao.md)
**Atenção.** Sistema técnico sólido e higiene de repo boa (`.gitignore` correto, 0 lixo versionado), mas a camada de backlog derivou ~35 sessões e aponta para o retrato errado. **Positivos:** consolidação em doc único vivo, janela deslizante STATUS→HISTORICO disciplinada, hub de ideias com dono-fonte, `PLANO_CONSTRUCAO` corretamente sinalizado como histórico.

---

## 5. ✅ O que está SÓLIDO (não mexer — confirmado pela auditoria)

- **Núcleo de dinheiro (P/L)** — derivado em `calcular_pl`, nunca persistido; as 5 fórmulas (W/L/V/HW/HL) e cashout batem com `MASTER_RESULTADO §5`, cobertas por golden tests. Corrigir stake/odd retroativo recalcula o histórico de graça.
- **Isolamento multi-tenant** — toda query escopada por `dono`, fail-closed, HMAC reavaliado a cada request; cookie "ver como" forjado cai no fallback sem escalar.
- **SQL 100% parametrizado** — nomes de coluna por whitelist, valores por `$N`. Sem superfície de injeção.
- **Perímetro HTTP** — CSRF por Origin, CSP + headers, exception handler que não vaza stack, validação de upload server-side.
- **Extensão passiva** — lê as respostas JSON que a própria casa baixa (dado exato) em vez de OCR/scraping frágil.
- **Guardrail de marca** — `check-tokens.mjs` bloqueante (drift de token, cor banida, abreviação de dinheiro).

---

_Auditoria conduzida em 18→19/07/2026. Read-only. Deliverables uncommitted — aguardando revisão do Feca antes de qualquer correção. As correções serão propostas uma a uma, no fluxo "propor → aprovar → executar" do CLAUDE.md._
