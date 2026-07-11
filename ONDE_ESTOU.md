# 🧭 ONDE ESTOU — mapa do projeto Planilhador/Sharpen

> Feito na madrugada de **2026-07-10 → 11** (auditoria completa com agentes, a pedido do Feca).
> Objetivo: bater o olho e saber **exatamente onde o projeto está**, o que é firme, o que está aberto,
> e o que fazer a seguir. Versão bonita/visual = Artifact (link no fim). Este arquivo é o durável.

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

### 🔴 Curto prazo / operacional (o que dói na rotina)
1. **Limpeza de duplicatas Bet365** — só DEPOIS das descrições estarem completas. Caminho: re-extrair os
   lotes afetados (código já corrigido), **nunca deletar às cegas**. Régua: stake+odd+descrição os três.
2. **Medir na base** quantas linhas de marcador/props estão sem sufixo/confronto (contaminam a dedup).
3. **Teste ao vivo do Betfair com a conta Duka** — validar velocidade e datas do fix da sessão 121.
4. **`CASA_BETANO.md` desatualizada** — ainda descreve scraping, mas a Betano virou ingestão por API. Reescrever §2/§3/§12.
5. **Fix estrutural de dedup**: garantir que a extração da Betano sempre capture o ID visível (raiz do problema de duplicata).

### 🟡 Médio prazo / dívida técnica que vale pagar
6. **Polymarket**: separar `entry_odd` de `realized_odd` (hoje a odd muda de significado conforme o resultado — distorce o dashboard).
7. **Métricas quant** (p-value, Monte Carlo, solidez): renomear para "indicador heurístico" + disclaimer. Barato, e é risco de produto vender como estatística rigorosa.
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

## 5. Próximos 3 passos que eu recomendo (quando você quiser)

1. **Fechar a recuperação pós-SharpenUp**: completar descrições → medir colapso na base → limpar duplicatas Bet365 por re-extração. (itens 1–2 acima)
2. **Rename das métricas quant + disclaimer** (item 7): barato, fecha um risco de produto, dá pra fazer numa sessão.
3. **Arrancar a Fase 1 do SaaS multiusuário** (tabela `usuarios`): destrava o cadastro self-service e a assinatura de tipsters, que é a frente de crescimento.

---

## 6. Arrumação de arquivos — ✅ FEITA (aprovada e commitada)

Você aprovou e eu executei. Com `git mv` (histórico preservado) + correção de todas as referências cruzadas:

| Feito | Detalhe |
|---|---|
| ✅ 9 `.md` soltos → `docs/` | `AUDITORIA_CRITICA`, `RELATORIO_CORRECOES`, `RISK_REDUCTION_PLAN`, `REFERENCIA_CHIPS/EMOJIS/LISTA`, `PLANO_CONSTRUCAO`, `CASAS_CONFIABILIDADE`, `GUIA_NOVA_CASA` |
| ✅ Raiz enxuta | Sobrou só o essencial: `CLAUDE.md`, `STATUS.md`, `ONDE_ESTOU.md`, `PLANO_MULTIUSUARIO_2026.md`, `PLANO_UNIFICACAO_2026.md` + configs |
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
