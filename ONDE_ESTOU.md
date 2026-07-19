# 🧭 ONDE ESTOU — mapa do projeto Planilhador/Sharpen

> Feito na madrugada de **2026-07-10 → 11** (auditoria completa com agentes, a pedido do Feca).
> Objetivo: bater o olho e saber **exatamente onde o projeto está**, o que é firme, o que está aberto,
> e o que fazer a seguir. Versão bonita/visual = Artifact (link no fim). Este arquivo é o durável.

---

> ## 🔄 ATUALIZAÇÃO 19/07/2026 (sessões 158-159) — LEIA PRIMEIRO
> O corpo abaixo é o retrato de **10-11/07 (sessão 122)**. Desde então rolou a **Auditoria Turbo**
> (a maior do projeto — 26 especialistas / 9 áreas) + execução de **6 ondas**. **Fonte de verdade
> ATUAL do backlog:** [`docs/AUDITORIA_TURBO_2026-07-19.md`](docs/AUDITORIA_TURBO_2026-07-19.md) (com tracker de progresso).
>
> **Saúde hoje:** 0 críticos na auditoria · **172 testes** passam (eram 65) · no ar.
> **Feito (sessões 158-159):** schema-init de banco vazio · tenancy do `/polymarket/sync` · §5 P/L
> zero neutro · `.dot` HW/HL distintos · win rate backend=front (HW=½) · **trio de segurança**
> (SESSION_SECRET fail-closed + X-Forwarded-For + `.dockerignore`) · **`test_auth.py`** (27 testes) ·
> **índices** em `bilhetes` · faxina de docs (planos→`docs/`) · **Polymarket** (teto de paginação +
> auto-sync com throttle + fetch consolidado ~2×) · Betano lê apostas em aberto.
> **Feito (sessão 160 — turbo/CEO, +6 commits):** #14c faxina CSS morto · **#13 autodiagnóstico
> universal das casas-robô** (maior risco vivo — manifest 0.3.5, recarregar extensão) · **#11 harness
> de camada-DB real** (Postgres no CI, gateado em `TEST_DATABASE_URL`, nunca prod) · **#20** 3 lacunas
> de propagação nos masters (aprovado) · ~~#15/#16 Solidez~~ (revertido `9394553` — rumo errado; → sessão dedicada de redesenho).
> **Aberto (prioridade):** custo tipster→Postgres (com Jonathan, ver [[custo_tipster_incidente_jonathan]]) ·
> **Poly incremental + #5 odd** ([`docs/PLANO_POLY_INCREMENTAL.md`](docs/PLANO_POLY_INCREMENTAL.md) — precisa a carteira do Feca) ·
> #14 domain.py (adiado) · #18 backtest temporal · #19 separador bet builder ✅ (` // ` único separador) · #21 golden · #25 Backups.

---

## 1. Posição atual, em uma frase

O sistema está **de pé, no ar, testado e conectado** (sessão 122, commit `c4b49fd`, working tree limpo).
As últimas duas semanas foram de **recuperação pós-SharpenUp** e ela está **quase fechada** — o susto foi
menor do que parecia (os documentos/regras estão íntegros; o estrago foi só em código recente, e a maior
parte já foi consertada).

---

## 2. Saúde do sistema (verificado hoje)

| Check | Resultado |
|---|---|
| `pytest` (testes) | ✅ **65/65 passam** |
| `audit_casas.py` | ✅ **14 casas OK**, 0 FAIL |
| `check-tokens.mjs` (marca) | ✅ verde |
| `compileall` (compila) | ✅ tudo compila |
| Frontend ↔ Backend | ✅ rotas batem 1:1, sem rota órfã |
| Deploy | ✅ Railway via push; Docker não-root + healthcheck; CI no GitHub |
| Domínio | ✅ sharpen.bet / www.sharpen.bet no ar |

**Nenhum ponto de quebra óbvio.** O sistema não está degradado — o medo do SharpenUp não se confirmou nos docs.

---

## 3. O que está FIRME (não precisa mexer)

- **Núcleo de extração** (IA lê print → TSV padronizado): 6 masters globais + 14 casas em camada fina, íntegros.
- **Dinheiro**: fórmulas de P/L verificadas corretas e cobertas por golden tests. O único furo que corrompia
  dinheiro (odd ilegível) foi fechado.
- **Segurança barata**: XSS do dashboard escapado, CSP + headers, CSRF/Origin guard, CDN vendorizado,
  validação de fronteira nas rotas de escrita, `/salvar` rejeita linha ruim. Tudo feito.
- **Infra**: CI rodando, Docker endurecido, deps com teto de versão.
- **Multiusuário atual**: isolamento por `dono` consistente em todas as rotas (7 usuários, provisionados à mão).
- **Betfair Duka** (o network error que te assustava): **resolvido** na sessão 121.

---

## 4. O que está ABERTO — por prioridade

### ✅ Qualidade de descrição — pivotada pra frente (decisão do Feca, 11/07)
- **Decisão:** não fazer arqueologia do passado (as descrições antigas "sobreviveram até aqui"). O que
  importa, com multi-usuário chegando, é a descrição **beirar a perfeição na hora que é gerada**.
- **Entregue:** checador determinístico de conformidade (`app/descricao_check.py`, regras do
  `MASTER_DESCRICAO`) + golden set (`golden_set/descricoes.jsonl`) + backtest no CI + **aviso ao vivo**
  no rail de extração (toda extração nova se auto-denuncia quando a descrição foge do padrão). Suíte 65→77.
- **Sobra opcional** (sem pressa, não é prioridade): `scripts/medir_descricoes_colapsadas.py` pra medir o
  passivo antigo, e re-extrair lotes afetados **se/quando** você quiser — nunca deletar às cegas.

### 🔴 Curto prazo / operacional (o que dói na rotina)
1. **Teste ao vivo do Betfair com a conta Duka** — validar velocidade e datas do fix da sessão 121.
2. **`CASA_BETANO.md` desatualizada** — ainda descreve scraping, mas a Betano virou ingestão por API. Reescrever §2/§3/§12.
3. **Fix estrutural de dedup**: garantir que a extração da Betano sempre capture o ID visível (raiz do problema de duplicata).

### 🟡 Médio prazo / dívida técnica que vale pagar
6. **Polymarket**: separar `entry_odd` de `realized_odd` (hoje a odd muda de significado conforme o resultado — distorce o dashboard).
7. ~~Métricas quant~~ ✅ **fechado (11/07)**: nomes técnicos **mantidos** (sua decisão) + explicação de cada número no tooltip. O objetivo era explicar o porquê do número, não removê-lo — e isso já estava feito.
8. **Observabilidade**: request_id + log estruturado (hoje debugar produção é às cegas).
9. **`SESSION_SECRET`**: fail-closed em produção (hoje, se faltar a env, o login cai a cada restart e só avisa).
10. **Win rate**: decidir se HW conta meio (hoje conta vitória cheia, infla o número).

### 🔵 Longo prazo / estratégico (planejado, com gate)
- **SaaS multiusuário** (cadastro no site, login Google/Telegram, pagamento) — Fase 1 = tabela `usuarios`. Ver `Ideias/README.md`.
- **Assinatura de tipsters** (Rota Asaas) — estudo pronto, execução não iniciada.
- **ADR-001** (dinheiro→NUMERIC/Decimal) — adiado por design, com gate.
- **ADR-002 Fase 2** (agregação do dashboard no servidor) — condicional a medição pós-gzip.
- **Telegram → tipster automático** (Fase 5 do plano original) — maior lacuna do fluxo.

> Detalhe técnico completo de tudo isso: **`docs/AUDITORIA_2026.md`** (auditoria única e viva).
> Detalhe de todos os planos/ideias: **`Ideias/README.md`**.

---

## 5. Próximos passos (estado em 11/07)

1. ~~Fechar a recuperação (faxina do passado)~~ ✅ **pivotado** — em vez de arqueologia, foi entregue a **qualidade de descrição indo pra frente** (checador + golden + backtest no CI + aviso ao vivo). A limpeza do passivo antigo fica como opcional sem pressa.
2. ~~Métricas quant~~ ✅ **fechado** — nomes técnicos mantidos + explicação no tooltip (sua decisão de 11/07).
3. **Fase 1 do SaaS multiusuário** (tabela `usuarios`) → **na canteira** (Próximos Passos): é mudança de **auth**, projeto grande; sessão dedicada com você olhando o 1º login pós-deploy. Ver `Ideias/README.md §1.1`.

**Sempre melhorando (contínuo):** conforme aparecer descrição fraca no rail de avisos, é só adicionar o caso ao `golden_set/descricoes.jsonl` e, se for regra nova, ao `app/descricao_check.py` — o backtest cresce e a qualidade sobe sozinha.

---

## 6. Arrumação de arquivos — ✅ FEITA (aprovada e commitada)

Você aprovou e eu executei. Com `git mv` (histórico preservado) + correção de todas as referências cruzadas:

| Feito | Detalhe |
|---|---|
| ✅ 9 `.md` soltos → `docs/` | `AUDITORIA_CRITICA`, `RELATORIO_CORRECOES`, `RISK_REDUCTION_PLAN`, `REFERENCIA_CHIPS/EMOJIS/LISTA`, `PLANO_CONSTRUCAO`, `CASAS_CONFIABILIDADE`, `GUIA_NOVA_CASA` |
| ✅ Raiz enxuta | Sobrou só o essencial: `CLAUDE.md`, `STATUS.md`, `ONDE_ESTOU.md` + configs (os `PLANO_*.md` migraram para `docs/`) |
| ✅ Banner de "histórico/desatualizado" no `PLANO_CONSTRUCAO.md` | Deixa claro que é registro, não fonte viva |
| ✅ Referências cruzadas corrigidas | `Ideias/README`, `PLANO_MULTIUSUARIO`, skill `/nova-casa` — e vários links de `docs/` que estavam quebrados **passaram a resolver** (os alvos agora moram na mesma pasta) |
| ✅ `golden_set/README.md` | Explica o propósito da pasta (antes vazia, contradizendo o CLAUDE.md) |

**Deixei de fora de propósito (mais arriscado / opcional — só faço com seu OK específico):**
- **Rotacionar `STATUS.md` (370KB)** — é cirurgia de conteúdo num arquivo de linhas gigantes, não um simples move. Melhor fazer com calma numa etapa dedicada.
- **Fundir `_backups/` em `Backups/`** — `_backups/` é gitignorado (invisível ao repo); mexer não agrega ao versionado.
- **Zipar `Backups/`** (303 subpastas, 35MB) — o git já cobre tudo; zipar é peso operacional sem ganho real agora.

---

## 7. O que eu fiz nesta madrugada

- Lancei **5 agentes em paralelo** (opus/sonnet/fable): reconciliação de auditoria, inventário de arquivos, levantamento de planos, smoke test do sistema, extração do STATUS.md.
- **Consolidei as 3 auditorias antigas** numa só viva → `docs/AUDITORIA_2026.md` (os 50 achados com status de hoje).
- **Juntei todos os planos e ideias** numa página → `Ideias/README.md`.
- Criei **este mapa** (`ONDE_ESTOU.md`) + a versão visual (Artifact).
- **Arrumei a raiz** (com seu OK): 9 `.md` soltos → `docs/` via `git mv` (histórico preservado), refs corrigidas — ver §6.
- **Testei o sistema inteiro** — está verde (§2).

> Nada foi **deletado**; os moves preservam histórico (`git mv`). Nenhum código do app foi tocado. Tudo reversível com `git revert`.

---

_Bom dia, Feca. O projeto está mais firme do que o cansaço da semana fazia parecer. 🌅_
