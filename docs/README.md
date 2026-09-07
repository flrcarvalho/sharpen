# `docs/` — índice

> **Um arquivo, uma pergunta** (invariante #10 do [`CLAUDE.md`](../CLAUDE.md)).
> Regras vinculantes → [`CLAUDE.md`](../CLAUDE.md) · onde o projeto está →
> [`STATUS.md`](../STATUS.md) · o que está aberto → [`BACKLOG.md`](../BACKLOG.md) ·
> o que aconteceu → [`HISTORICO.md`](HISTORICO.md) · o que virou registro →
> [`arquivo/`](arquivo/README.md).
>
> Este índice existe porque **metade dos documentos daqui não era linkada por ninguém** — o
> que os fazia parecer órfãos sem serem. Doc que ninguém acha é doc que ninguém lê.

---

## Como se faz (procedimento)

| Arquivo | Responde |
|---|---|
| [`GUIA_NOVA_CASA.md`](GUIA_NOVA_CASA.md) | Cadastrar casa nova na camada de **leitura** (arquivo de tradução, seletor, favicon). Gate: `python tools/audit_casas.py`. |
| [`GUIA_CASA_SHARPENUP.md`](GUIA_CASA_SHARPENUP.md) | Ligar a casa à **captura** (12 pontos de registro em 4 camadas). Gate: `python tools/audit_sharpenup.py`. |
| [`GUIA_RECON_TESTER.md`](GUIA_RECON_TESTER.md) | O roteiro para repassar a **quem tem a conta** na casa, sem pedir login. |
| [`GUIA_BOT_TIPSTER.md`](GUIA_BOT_TIPSTER.md) | Pôr um tipster novo no ar no `sharpen-bot`. Uso interno — o manual público é `sharpen.bet/bot`. |
| [`GUIA_CREDENCIAIS_LOGIN_SOCIAL.md`](GUIA_CREDENCIAIS_LOGIN_SOCIAL.md) | Acordar o login Google/Telegram, que está no ar em modo dormente. Só env vars, sem deploy. |
| [`runbook-rotacao-postgres.md`](runbook-rotacao-postgres.md) | Rotacionar a senha do Postgres no Railway. Execução pendente (`BACKLOG §1.1`). |

## Como é (referência — muda pouco)

| Arquivo | Responde |
|---|---|
| [`SHARPENUP_ARQUITETURA.md`](SHARPENUP_ARQUITETURA.md) | O mapa da captura: extensão → ponte → backend. **O código é a verdade**; ao mudar o comportamento, atualize o mapa na mesma sessão. |
| [`UI_REFERENCE.md`](UI_REFERENCE.md) | Regras de UI da marca. O **§5 (padrão monetário)** é lei e é citado pelo `CLAUDE.md` e pela skill `/nova-ui`. |
| [`SHELL_SPEC.md`](SHELL_SPEC.md) | Contrato da casca compartilhada — cada elemento → o token que ele deve usar. Gate: `node scripts/tokens/check-tokens.mjs`. |
| [`REFERENCIA_CHIPS_CASAS.md`](REFERENCIA_CHIPS_CASAS.md) | Spec autocontida do chip de favicon de casa e da tabela "POR CASA". |
| [`REFERENCIA_EMOJIS_ESPORTES.md`](REFERENCIA_EMOJIS_ESPORTES.md) | Spec autocontida do chip de esporte e dos mapas `SPORT_KEY` / `SPORT_EMOJI` / `SPORT_SVG`. |
| [`REFERENCIA_LISTA_APOSTAS.md`](REFERENCIA_LISTA_APOSTAS.md) | Spec autocontida da tabela de Apostas (CSS Grid + scroll virtual). |
| [`CASAS_CONFIABILIDADE.md`](CASAS_CONFIABILIDADE.md) | Matriz de prontidão de extração por casa. ⚠️ **Espelha 13 de 28 casas** — atualizar é sessão própria (`BACKLOG §5`). |
| [`marketing/README.md`](marketing/README.md) | Regras dos 2 HTML de marketing. **DARK ONLY** — a regra é citada por `tests/test_landing.py`. |

## Decisões com gate (ADR)

| Arquivo | Estado |
|---|---|
| [`ADR-001-migracao-numeric-decimal.md`](ADR-001-migracao-numeric-decimal.md) | Dinheiro/odd/data → NUMERIC/DATE + Decimal. **Adiado por desenho**; erro medido do `float` << 1 centavo. |
| [`ADR-002-dashboard-primeira-carga.md`](ADR-002-dashboard-primeira-carga.md) | Fase 1 (gzip do `/dashboard/data`) **aplicada**; Fase 2 (agregação no servidor) condicional a medição. |

## Planos com fase aberta

Todos estão listados, com o que falta e o horizonte, em **[`BACKLOG.md §5`](../BACKLOG.md)**.

| Arquivo | Falta |
|---|---|
| [`PLANO_MULTIUSUARIO_2026.md`](PLANO_MULTIUSUARIO_2026.md) | Fase 4 (pagamento). Fases 1-3 no ar. |
| [`PLANO_TRADUTOR_DETERMINISTICO.md`](PLANO_TRADUTOR_DETERMINISTICO.md) | Fases 1-4. Fase 0 roda em modo sombra. |
| [`PLANO_TIPSTER.md`](PLANO_TIPSTER.md) | P1 (unidades), P2 (watermark), P3 (Telegram). |
| [`PLANO_INTELIGENCIA_TIPSTER.md`](PLANO_INTELIGENCIA_TIPSTER.md) | O resolvedor de atribuição. ⚠️ texto de 15/07, defasado. |
| [`PLANO_EXTRACAO_WORLDWIDE.md`](PLANO_EXTRACAO_WORLDWIDE.md) | Fases 1-5. Fase 0 validada. |
| [`PLANO_CASCA_UNIFICADA.md`](PLANO_CASCA_UNIFICADA.md) | Fatia 3. |
| [`PLANO_POLY_INCREMENTAL.md`](PLANO_POLY_INCREMENTAL.md) | A marca d'água. Precisa de teste de paridade na carteira do Feca. |
| [`PLANO_DASHBOARD_C.md`](PLANO_DASHBOARD_C.md) | Não iniciado, condicional. |
| [`PLANO_INFERENCIA_POR_CAMPO.md`](PLANO_INFERENCIA_POR_CAMPO.md) | Sem código; precisa de OK do Feca. |
| [`ESTUDO_PRECIFICACAO_2026.md`](ESTUDO_PRECIFICACAO_2026.md) | Correções A e C aplicadas; a **B** segue bloqueada. |

## Desta faxina

| Arquivo | O que é |
|---|---|
| [`FAXINA_PROPOSTA.md`](FAXINA_PROPOSTA.md) | O inventário e a proposta que originaram a faxina de 2026-09-07, com o que foi medido e como. |
| [`RECONCILIACAO_TURBO_20-07.md`](RECONCILIACAO_TURBO_20-07.md) | A remedição dos achados da Auditoria Turbo contra o código de hoje — e a descoberta de que os 78 do mergulho de 20/07 nunca foram escritos. |

---

_Índice criado em 2026-09-07 (faxina de documentação, Lote D)._
