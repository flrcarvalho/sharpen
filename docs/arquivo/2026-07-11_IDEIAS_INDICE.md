# 💡 Ideias & Planos — página única

> Índice mestre de **tudo que é plano, estudo ou ideia futura** do Sharpen/Planilhador.
> Cada frente aponta para o documento-fonte (que continua onde está) e traz status + horizonte.
> Atualizado em **2026-07-11**. Quando uma frente sair do papel, atualize a linha aqui.

Horizontes: **🟢 curto** (próximas sessões) · **🟡 médio** (semanas) · **🔵 longo** (mês+ / condicional)

---

## 1. Frente estratégica maior — Sharpen como plataforma

### 1.1 SaaS multiusuário — `../docs/PLANO_MULTIUSUARIO_2026.md`
Transformar o Sharpen de app provisionado à mão em SaaS: cadastro no site, login social, tabela de
usuários no banco, e depois assinatura. **Aprovado em princípio (sessão 116), execução não iniciada.**
Ponto de convergência limpo: qualquer login novo só precisa produzir um `usuario` confiável e chamar
`criar_token` + `set_cookie` (já existem).

| Fase | O que é | Horizonte |
|---|---|---|
| 1 | Tabela `usuarios` no Postgres + mover identidade dos dicts de `auth.py` p/ o banco | 🟢 **próximo passo** |
| 2 | Cadastro self-service ("aberto com aprovação") | 🟢 |
| 3 | Login Google / Telegram (o Telegram conecta com **1.3 Perfil de Tipster**) | 🟡 |
| 4 | Pagamento / assinatura (gate `assinatura_ativa` + webhook) | 🟡 |

### 1.2 Assinatura de tipsters — `Estudo_Assinatura_Tipsters_Sharpen.pdf` + `Modelo_Financeiro_Rota_propag_Sharpen.pdf`
Sharpen virar a página de assinatura recorrente dos tipsters (hoje eles usam Pix manual / Hubla / prop.ag).
**Estudo concluído (sessão 122); execução não iniciada.** É extensão natural do SaaS multiusuário (1.1).
- **Rota recomendada = B (estilo prop.ag):** NÃO virar instituição de pagamento; sentar sobre gateway
  regulado com split — **Asaas** (aceita bets; libera em 1–2 dias vs 8–30 da prop.ag). Stripe descartada
  (proíbe previsões esportivas no BR). **Pix Automático** = diferencial que nenhum concorrente usa.
- **Números:** take 5,9%; tipster médio (R$150×100 membros) → ~R$586/mês de lucro (66% margem);
  break-even ~3 tipsters; 100 tipsters ≈ R$344k/ano com folha realista.

| Próximo | Horizonte |
|---|---|
| Fundir os 2 PDFs num documento mestre | 🟢 |
| Slider de opex/time + churn/impostos na calculadora (Artifact já existe) | 🟢 |
| Conversa comercial com Asaas | 🟡 |
| MVP Fase 1: tipsters como usuários do SaaS + afiliados | 🟡 (depende de 1.1) |
| Fase 2: página de assinatura recorrente completa | 🔵 |

### 1.3 Perfil de Tipster (unidades, atribuição, Telegram) — `../docs/PLANO_TIPSTER.md`
Dar ao tipster existência real no Sharpen (hoje é só texto livre). Três facetas do mesmo cadastro:
P1 resultado em unidades no tempo (escada de stake, view derivada), P2 atribuição por watermark
(stake exato tipo 199/401), P3 Telegram como fonte (MTProto + casamento tip↔bilhete). Invariante #0:
anti-repasse (o Sharpen nunca surfa tip fresca). **Passo zero:** tabela `tipsters` + backfill.
**Fase 0 no ar:** coluna `origem_tipster` (procedência do rótulo, `52b39ae`) + backtest do matcher
(baseline por carteira). Fases 1+ ainda sem código.
- **Horizontes:** P1 🟢 (backend pronto; UI trava no formato "u" via `/nova-ui`) · P2 🟡 · P3 🔵.
  **Ordem:** cadastro de tipster → P1 → P2 → Telegram. Onboarding: tipster nasce sozinho e incompleto
  (sinal `(i)` + lista de pendências no login).

---

## 2. Planos de produto/UI

### 2.1 Casca unificada — `../docs/PLANO_CASCA_UNIFICADA.md`
Fazer Planilhador e Dashboard parecerem "um app só" (sidebar viva, sem recarga entre eles), em fatias.
- Fatia 1 (geometria do sidebar) ✅ · Fatia 2 (shell hospedeiro `/app` com iframes) ✅ no ar ·
  Fatia 3 parcial (crossfade + botão "Atualizar dados") 🟡
- **Pendente:** Fatia 3 completar (topbar compartilhada, poda de CSS morto, aposentar links cross-app) — 🟢
  aguardando validação humana da Fatia 2. Fatia 4 (SPA único) só se o host com iframe não bastar — 🔵

### 2.2 Página Contas & Parceiros / rail "Análise IA"
Da auditoria visual da casca (`../docs/AUDITORIA_VISUAL_CASCA_2026-06-30.md`, hoje quase toda superada):
- Página dedicada de gestão de contas/custos — 🟡
- Rail "Análise IA" evoluir para 3 KPIs + notas estruturadas (Confiança já parcial) — 🟡
- Tema claro (toggle) — 🔵 **adiado por decisão de marca** (produto = dark)

---

## 3. Planos técnicos / dívida (detalhe em `../docs/AUDITORIA_2026.md`)

| Frente | Doc-fonte | Status | Horizonte |
|---|---|---|---|
| Migração dinheiro → NUMERIC/Decimal | `../docs/ADR-001-migracao-numeric-decimal.md` | Fase 0 (não iniciado), gate parcial | 🔵 adiado por design |
| Dashboard 1ª carga (agregação no servidor) | `../docs/ADR-002-dashboard-primeira-carga.md` | Fase 1 (gzip) ✅ · Fase 2 condicional | 🔵 condicional a medição |
| ~~Rename métricas quant + disclaimer (p-value/MC/solidez)~~ ✅ fechado (11/07) — nomes técnicos mantidos + explicação no tooltip (decisão do Feca) | `../docs/AUDITORIA_2026.md` #29–31 | ✅ Fechado | — |
| Polymarket: separar entry_odd / realized_odd | `../docs/AUDITORIA_2026.md` #32 | Aberto | 🟡 |
| Observabilidade (request_id + log estruturado) | #44 | Aberto | 🟡 |
| Rotação da senha do Postgres | `../docs/runbook-rotacao-postgres.md` | Runbook pronto, execução pendente | 🟢 |
| Self-host das fontes (fechar CSP) | #36 | Aberto | 🟡 |

---

## 4. Planos da máquina de extração (o produto original)

### 4.1 Plano de construção — `../docs/PLANO_CONSTRUCAO.md` ⚠️ *desatualizado*
Fases 0–4 (repo, núcleo de extração, Postgres, Scanner UI, extensão de captura) ✅ concluídas.
**O documento tem referências vencidas** (cita Haiku como padrão, `MASTER_TSV.md`, arquivos que não
existem) — vale ler só como histórico. Frentes ainda vivas dele:
- **Fase 5: Telegram → tipster automático** — consolidada em **§1.3 Perfil de Tipster / P3**
  (`../docs/PLANO_TIPSTER.md`); segue sendo a maior lacuna de atribuição, agora com plano e a
  pré-condição anti-repasse — 🔵
- Fase 6 (inspetor/eval automatizado) — 🔵 · Fase 7 (scraper leve, opcional) — 🔵

### 4.2 Extração híbrida — custo ~zero
Parser determinístico via DOM da extensão para casas de alto volume + IA só na cauda. Log de tokens já
construído (`/uso/tokens`); parser determinístico ainda não codado. 🟡

### 4.3 Migração planilha → Postgres — `../docs/PLANO_UNIFICACAO_2026.md`
Trazer as ~25.726 apostas da planilha p/ o Postgres (era-split, em fatias). Grosso feito e auditado;
**cauda de casas** ainda pode faltar (Pinnacle, Superbet, Novibet, Bet365 ativas, Betnacional) —
confirmar no `../STATUS.md`. 🟢

---

## 4b. Polymarket — sessão em andamento (11/07)
- ✅ Odd unificada = 1/preço (retorno/investimento) + KPIs renomeados (Saldo em Aberto/Disponível/Total) — 🟢 feito
- ✅ Confiabilidade de saldo (RPCs caem → "—", não R$0) — 🟢 feito
- ⏳ **Persistir posições ativas** (ativas viram bilhete aberto na tabela Apostas; fim da seção "Posições Ativas") — 🟢 plano pronto em `../docs/PLANO_POLY_PERSISTIR_ATIVAS.md`

## 5. Extensão de captura (SharpenUp) — `../extensor/`
No ar; pareia por código com o dashboard. Submetida à Chrome Web Store (análise pendente).
- Instalar nos perfis Octo após aprovação — 🟢
- Bet365 modo texto — **pausado** (card fechado não expõe detalhe) — ⏸️ decisão do Feca

---

## 6. Frentes de manutenção gatilhadas (pós-SharpenUp) — ver `../docs/AUDITORIA_2026.md` e `../STATUS.md`

Da recuperação da sessão 119, **duas já foram fechadas** (Betfair Duka na 121; guardrail de chunk +
Betano determinística na 120b). **Restam:**
- Limpeza de duplicatas reais Bet365 — **só depois** das descrições completas (re-extrair, não deletar às cegas) — 🟢
- Medir na base quantas linhas de marcador/props estão sem sufixo/confronto (contaminam a dedup) — 🟢
- Redesenho da dedup Bet365 para não depender de nome via OCR — 🟡 (decisão do Feca)
- Fix estrutural: Betano sempre capturar o ID visível na extração — 🟢

---

## 7. Onde cada documento-fonte vive

| Documento | Caminho | Papel |
|---|---|---|
| SaaS multiusuário | `../docs/PLANO_MULTIUSUARIO_2026.md` | plano ativo |
| Perfil de Tipster (unidades/atribuição/Telegram) | `../docs/PLANO_TIPSTER.md` | plano ativo |
| Migração planilha→Postgres | `../docs/PLANO_UNIFICACAO_2026.md` | plano ativo |
| Casca unificada | `../docs/PLANO_CASCA_UNIFICADA.md` | plano ativo (polimento) |
| ADR-001 / ADR-002 | `../docs/ADR-00*.md` | decisões com gate |
| Auditoria consolidada | `../docs/AUDITORIA_2026.md` | risco técnico vivo |
| Runbook rotação Postgres | `../docs/runbook-rotacao-postgres.md` | procedimento |
| Plano original (histórico) | `../docs/PLANO_CONSTRUCAO.md` | ⚠️ desatualizado |
| Estudos de negócio (PDFs) | `Estudo_*.pdf`, `Modelo_*.pdf` | esta pasta |

---

_Página viva. Última atualização: 2026-07-11._
