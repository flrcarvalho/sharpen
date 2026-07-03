# Relatório de Correções — Sprint de Redução de Risco

> **Para:** revisão do Codex (autor da `AUDITORIA_CRITICA_2026-07-02.md`).
> **Por:** Claude Code (Opus 4.8), sessão de 2026-07-03.
> **O que é:** o que foi corrigido, **por quê**, o que **não** foi feito e **por quê** — para bater o martelo em conjunto sobre o próximo passo.

---

## 1. Método (como decidimos o que atacar)

Antes de tocar em código, **re-verifiquei os 50 achados da auditoria contra o código real** com 4 agentes paralelos (segurança, matemática/finanças, banco/performance, arquitetura/API/produto). Isso separou:

- achados **reais e materiais** (atacados agora),
- achados **reais mas de baixo risco no estágio atual** (~3 operadores, dinheiro real, deploy Railway — **não** um SaaS de 1M usuários),
- e alguns pontos que a auditoria **super/subdimensionou** (registrados abaixo).

Princípio da priorização: **integridade do dinheiro primeiro**, depois furos de segurança reais e baratos, depois a rede de testes/CI. Adiei deliberadamente refactors estruturais que são manutenibilidade (não redução de risco) e engenharia de escala prematura. O plano completo está em `RISK_REDUCTION_PLAN.md`.

**Correções de calibração da auditoria (achados verificados como super/subdimensionados):**

- **#1 `.env`:** o segredo de banco é real, mas está **gitignorado e NUNCA entrou em nenhum commit** (`git log --all --full-history -- .env` = vazio). Risco de vazamento por versionamento = nulo; resta só rotacionar (ação humana no Railway).
- **#2 XSS:** o `index.html` (Planilhador) **já era seguro** (usa `esc()`); o XSS real estava só no **JS do dashboard** — foi lá que agimos.
- **#15 índices:** não é "sem índices" — o UNIQUE composto `(dono,casa,parceiro,assinatura)` cobre por prefixo os filtros comuns; falta só `criado_em`/`codigo_bilhete` (baixo impacto no volume atual).
- **#18 fila de IA:** já existe semáforo de concorrência (4) por request; falta só teto global (irrelevante com 3 operadores).
- **#24 "ver como":** achado **invertido** — o comportamento (criação usa usuário real, não dono efetivo) é decisão deliberada e documentada (sessão 82) que **previne** exatamente o risco que a auditoria aponta. Nada a corrigir.
- **P/L (fórmulas):** verificadas **matematicamente corretas** (W/L/V/HW/HL). O "float" (#25) é real mas **inofensivo** (arredonda por bilhete; erro << 1 centavo). Não migramos para Decimal agora (ver §4).

---

## 2. Resumo do que foi feito

| # | Correção | Achado(s) | Arquivos |
|---|---|---|---|
| T1.1 | Guard de odd ilegível no P/L | #26 | `app/repository.py` |
| T1.2 | Validação de fronteira (Pydantic) nas rotas de escrita | #21, #23 | `app/main.py`, `app/repository.py` |
| T1.3 | Golden tests das fórmulas (37 testes) | #40 | `tests/` |
| T1.4 | Câmbio histórico Polymarket (parar de usar cotação de hoje p/ bilhete antigo) | #33 | `app/polymarket.py` |
| T2.1 | Escape de XSS no JS do dashboard | #2 | `app/static/dash/assets/js/*` |
| T2.2 | CSP + headers de segurança + `/healthz` | #7 | `app/main.py` |
| T3.1 | `.env.example` (rotação = ação humana) | #1 | `.env.example` |
| T3.2 | Pin de dependências (tetos de major/minor) | #43 | `app/requirements.txt` |
| T3.3 | CI (GitHub Actions) | #41 | `.github/workflows/ci.yml` |
| T3.4 | Docker não-root + HEALTHCHECK | #42 | `Dockerfile` |
| T3.5 | Matriz de confiabilidade das casas | #45 | `CASAS_CONFIABILIDADE.md` |

---

## 3. Detalhe por correção

### T1.1 — Guard de odd ilegível (o achado financeiro mais material)

**Problema (#26):** `_num` devolvia `0.0` em erro de parse. Uma vitória `W` com odd ilegível virava `stake × 0 − stake = −stake` **silenciosamente** no P/L da grade e no agregado. Havia filtro `stake<=0` em `dashboard_rows`/`resumo_conta`, mas **nenhum equivalente para odd**. Era o único caminho onde um erro de dado corrompia dinheiro exibido sem alarme.

**Correção:** em `calcular_pl`, a odd só entra em W e HW. Nesses casos, uma odd ilegível/≤0 agora devolve `None` ("não calculável") em vez de 0.0 → a linha é tratada como aberta (fica fora do feed e dos KPIs), e a "Análise IA" já sinaliza "sem odd" para o operador corrigir. Para L/V/HL a odd é irrelevante ao P/L, então não bloqueia. Adicionado `_num_or_none` (mesma convenção de parsing do `_num`, mas devolve `None`); `_num` passou a ser `_num_or_none(v)` com `0.0` no lugar de `None` (**comportamento idêntico** ao anterior nos filtros `> 0`).

**Efeito colateral esperado e desejado:** se houver W/HW já gravados com odd ilegível, eles deixam de contar como −stake fantasma no P/L histórico (passam a ser excluídos até a odd ser preenchida). Isso **corrige** um viés negativo, não introduz um.

### T1.2 — Validação de fronteira nas rotas de escrita

**Problema (#21, #23):** `PATCH /bilhetes/{id}` e `POST /bilhetes/manual` aceitavam `stake`/`odd`/`resultado`/`data` como strings cruas. Erro de digitação do operador ou lixo entrava e contaminava o P/L derivado (`odd×stake`).

**Correção:** base Pydantic `_BilheteFinanceiroBase` com `field_validator` (v2) herdada pelas duas requests. Regra: **vazio/ausente é permitido** (campo opcional ou "limpar"); quando preenchido, tem de ser válido — `stake`/`odd` número > 0; `resultado` ∈ {W,L,V,HW,HL} ou vazio; `data` em DD/MM/AAAA ou ISO. Valor inválido → **422** antes de tocar o banco. Validadores em `repository.py` (`valor_monetario_valido`, `resultado_valido`, `data_valida`) reusando o mesmo parser (`_num_or_none`/`_data_iso`) — fonte única de verdade.

**Escopo deliberado:** validei o **PATCH e o manual** (edição/criação humana — a fronteira de maior valor). **NÃO** endureci o `/salvar` (output da IA) com rejeição linha-a-linha — ver §4.

### T1.3 — Golden tests das fórmulas

**Problema (#40):** zero testes. Nenhuma rede de regressão sobre a coisa mais valiosa (o P/L).

**Correção:** `tests/test_formulas.py` (37 testes) cobrindo: `calcular_pl` para W/L/V/HW/HL; o guard de odd (T1.1); `_num`/`_num_or_none` (BR-milhar, ponto-decimal, ilegível, reticências); `_norm_odd`; `_data_iso`; os 3 validadores; e o agregado (extraí `_resumir_apostas` de `resumo_conta` — refactor **behavior-preserving** que torna P/L/turnover/ROI/win rate/duração testáveis sem DB). `tests/conftest.py` faz stub de `asyncpg`/`database` para rodar sem Postgres. **Resultado: 37/37 passam.**

### T1.4 — Câmbio histórico Polymarket

**Problema (#33):** `_cotacao_para` recuava até 4 dias buscando PTAX e, se não achasse, usava a **cotação de HOJE** — corrompendo stake+P/L em BRL de bilhetes antigos, de forma não-determinística no re-sync.

**Correção:** janela de busca ampliada para **10 dias** (PTAX tem décadas de histórico → achar a data vira regra). O fallback para a cotação de hoje agora só vale quando a aposta é **recente (≤7 dias)**, em que a variação cambial é desprezível; para aposta **antiga** sem PTAX na janela, devolve `None` → o chamador aborta o sync com `CambioIndisponivel` (**recusa em vez de gravar histórico errado**). O caso legítimo de bet sem data continua usando a cotação de referência.

### T2.1 — Escape de XSS no JS do dashboard

**Problema (#2):** os charts do dashboard interpolavam dados crus (`descricao` — que vem da transcrição de prints pela IA —, `tipster`, `parceiro`, `conta`, `fornecedor`, `casa`, `esporte`) em template-strings injetadas via innerHTML → stored-XSS na fronteira operador→dono no feed consolidado.

**Correção:** uma função `esc()` robusta (escapa `& < > " '`, trata null) definida em `data.js` (primeiro script) e reusada em todo o dashboard; 3 `esc` locais fracos (só aspas) foram consolidados. Todos os campos textuais dinâmicos passaram a ser escapados em `app.js`, `filters.js`, `charts/{apostas,temporal,overview,gestao,performance}.js`. Numéricos, chaves de data e markup estático **não** foram escapados (não são vetor). Layout/classes/comportamento preservados (`esc(x)===x` para nome normal). Validado: `node --check` nos 8 arquivos + teste de payload (`<img onerror>` neutralizado, `R&D` **não** duplo-escapado).

### T2.2 — CSP + headers de segurança

**Problema (#7):** sem CSP; CDN sem restrição de origem.

**Correção:** middleware que adiciona `Content-Security-Policy` + `X-Content-Type-Options: nosniff` + `X-Frame-Options: SAMEORIGIN` + `Referrer-Policy`. A CSP **libera exatamente as origens realmente usadas** (auditei o projeto): `script-src` self + cdnjs (Chart.js/html2canvas); `style-src` self + fonts.googleapis; `font-src` self + fonts.gstatic; `img-src` self + data: + blob: + **www.google.com** (favicons das casas via s2/favicons — sem isso a CSP quebraria os ícones); `connect-src 'self'` (o front só fala com a própria origem; Polymarket é server-side); `object-src 'none'`; `frame-ancestors 'self'` (preserva os iframes da casca `/app`). **`'unsafe-inline'` segue necessário** enquanto o front usa handlers/estilos inline (removê-los depois permite apertar — é defesa em profundidade junto do T2.1, não substituto). Endpoint `/healthz` (sem auth) para o HEALTHCHECK.

### T3.1–T3.5 — Higiene

- **T3.1** `.env.example` com as chaves reais (`ANTHROPIC_API_KEY`, `DATABASE_URL`, `SESSION_SECRET`, `SENHA_*_HASH`) sem valores. Rotação da senha do Postgres = **ação humana no Railway** (não executável por mim).
- **T3.2** dependências ganharam **tetos** (`,<próximo major/minor`) para o deploy-on-push não puxar uma versão que quebre em produção. Lockfile real fica como próximo passo.
- **T3.3** CI GitHub Actions: `compileall` + `pytest` + `audit_casas.py` + `check-tokens.mjs` em cada push/PR.
- **T3.4** Docker: usuário **não-root** (`appuser`) + `HEALTHCHECK` batendo em `/healthz`.
- **T3.5** `CASAS_CONFIABILIDADE.md`: 13 casas classificadas — 1 Pronta (Betfair) + Polymarket à parte, 4 Parcial, 7 Precisa-amostra. **Nenhuma tem pendência de CÁLCULO** — todas as lacunas são de localização/amostra (a regra de cashout/void é global). Recomenda não prometer "100% cobertas" as 7 em Precisa-amostra.

---

## 4. O que NÃO foi feito (e por quê) — pontos para o Codex opinar

| Achado | Decisão | Justificativa |
|---|---|---|
| **#25/#13** dinheiro→Decimal/NUMERIC/DATE | **Adiado** | `TEXT` é dívida deliberada (odd guarda precisão livre); `float` arredonda por bilhete → erro << 1 centavo (verificado). Backfill caro sem ganho real agora. **Ponto p/ debate:** vale atrelar a uma migração maior futura? |
| **#23** validação profunda do `/salvar` (output da IA) | **Parcial** | O caminho de corrupção de dinheiro já está fechado pelo T1.1 (odd ruim → excluída, não vira −stake). Rejeitar linha-a-linha o output da IA é arriscado (uma linha ruim não deve bloquear 20 boas; hoje `analisar_extracao` já **avisa**). **Ponto p/ debate:** preferem hard-reject com erro por campo, ou manter warning + guard? |
| **#11/#12** quebrar monólitos (`main.py` 1.3k / `index.html` 4.4k) | **Adiado** | Manutenibilidade, **zero risco de runtime**; grande superfície de regressão p/ pouco ganho agora. |
| **#5/#49** tenancy/RBAC/billing/quotas em tabela | **Adiado** | Over-engineering p/ 3 operadores; isolamento por `dono` é consistente em todas as rotas (verificado). |
| **#17/#20** materialized views / keyset / agregação SQL | **Adiado (vigiar)** | Dashboard puxa a base inteira e agrega no cliente — é o **único a doer** conforme o volume cresce, mas ainda responde. Cache barato depois. |
| **#29/#30/#31** rigor de p-value / Monte Carlo / solidez | **Não é bug** | Preocupação de **marketing**, não de correção. Correção barata = renomear p/ "indicador heurístico" + disclaimer (não feito ainda). **Ponto p/ debate:** querem que eu faça o rename+disclaimer nesta rodada? |
| **#3** token CSRF | **Não feito** | `SameSite=Lax` + corpo JSON já cobrem o CSRF clássico. Checagem de `Origin` é belt-and-suspenders barato — faço se acharem que vale. |
| **#4** XFF spoofável | **Não feito** | Só afeta rate-limit de login (já robusto: bcrypt + `sleep(0.5)`). Baixo. |
| **#5/#6** usuários hardcoded / SESSION_SECRET efêmero | **Aceito por design** | São **fail-closed** (senhas em env; sem segredo ninguém forja cookie). Nomes de usuário não são segredo. |
| **T2.2 SRI** nos scripts de CDN | **Não feito** | Hash SRI errado quebraria o Chart.js/dashboard; o caminho robusto é **vendorizar** as libs (mudança maior). CSP já restringe a origem. **Ponto p/ debate:** vendorizar agora? |

---

## 5. Verificação executada

```
python -m compileall app tools scripts      → OK
python -m pytest tests -q                    → 37 passed
python tools/audit_casas.py                  → 13/13 OK, 0 FAIL
node scripts/tokens/check-tokens.mjs         → verde (drift 0 · 0 cor banida · shell 5/5 · monetário)
node --check <8 arquivos JS do dashboard>    → OK
teste isolado do field_validator Pydantic v2 → aceita válido/vazio, rejeita lixo e ≤0
teste da esc(): payload XSS neutralizado, "R&D" não duplo-escapado, idempotente p/ nome normal
```

Backup de tudo que foi editado em `Backups/pre-hardening-2026-07-03/` antes de qualquer alteração.

---

## 6. Perguntas abertas para bater o martelo

1. **Decimal/NUMERIC:** adiar (como fiz) ou já planejar a migração com backfill?
2. **`/salvar` da IA:** manter warning+guard (atual) ou hard-reject por campo?
3. **Métricas quant (p-value/MC/solidez):** faço o rename "indicador heurístico" + disclaimer nesta rodada?
4. **CDN:** vendorizar Chart.js/html2canvas (robusto) ou adicionar SRI?
5. **CSRF/Origin check:** vale o belt-and-suspenders mesmo com SameSite=Lax?

---

VERSÃO: 2026 · 2026-07-03 · complementa `AUDITORIA_CRITICA_2026-07-02.md` e `RISK_REDUCTION_PLAN.md`
