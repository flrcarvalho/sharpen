# Arquivo — o que foi verdade e virou registro

> **Nada aqui foi apagado.** Estes documentos saíram de `docs/` e da raiz na faxina de
> documentação de 2026-09-07 porque descreviam um estado que já passou, ou porque o trabalho
> que planejavam **já foi feito**. O nome ganhou a data da fonte na frente, para o arquivo se
> ordenar sozinho.
>
> **O que ficou aberto neles não ficou aqui.** Antes de mover, cada pendência viva foi
> **remedida contra o código** e migrada para o [`BACKLOG.md`](../../BACKLOG.md), com o número
> original preservado. Ver [`FAXINA_PROPOSTA.md`](../FAXINA_PROPOSTA.md).
>
> Estado atual → [`STATUS.md`](../../STATUS.md) · o que está aberto →
> [`BACKLOG.md`](../../BACKLOG.md) · o que aconteceu → [`HISTORICO.md`](../HISTORICO.md).

---

## Auditorias

| Arquivo | O que era | Onde o resultado vive hoje |
|---|---|---|
| [`2026-07-02_AUDITORIA_CRITICA.md`](2026-07-02_AUDITORIA_CRITICA.md) | Os 50 achados originais do Codex. | Consolidada na `AUDITORIA_2026`, que por sua vez foi remedida para o `BACKLOG §4.1`. |
| [`2026-07-03_RELATORIO_CORRECOES.md`](2026-07-03_RELATORIO_CORRECOES.md) | O que foi corrigido na primeira leva, para revisão do Codex. | Idem. O próprio `AUDITORIA_2026` já declarava este arquivo histórico. |
| [`2026-07-03_RISK_REDUCTION_PLAN.md`](2026-07-03_RISK_REDUCTION_PLAN.md) | A priorização calibrada dos 50 achados. | Idem. |
| [`2026-07-10_AUDITORIA_2026.md`](2026-07-10_AUDITORIA_2026.md) | Declarava-se "documento único e vivo" — e não era reconciliado desde a s122. | **`BACKLOG §4.1`**, com os números originais (`#32`, `#44`, `#16`, `#10`, `#37`…) e uma tabela de "não reabrir" com os 5 que já estavam fechados. |
| [`2026-07-19_AUDITORIA_TURBO.md`](2026-07-19_AUDITORIA_TURBO.md) + [`auditoria_turbo_2026-07-19/`](auditoria_turbo_2026-07-19/) | A maior auditoria do projeto (26 especialistas, 9 áreas) e os 11 relatórios de gerência. 19 dos 25 achados fecharam. | **`BACKLOG §4.2`** — os 6 que sobraram vivos (#6, #15/#16, #18, #21, #25 e o link do #24, este último já fechado no Lote C). |
| [`2026-07-20_AUDITORIA_TURBO_PROFUNDA.md`](2026-07-20_AUDITORIA_TURBO_PROFUNDA.md) | O mergulho de 219 agentes: 104 achados brutos, 95 confirmados, **zero tracker**. | **`BACKLOG §4.3`** (os 17 ALTOS, remedidos em 06/09) e **`§4.4`** (os 78 MÉDIO/BAIXO). ⚠️ Os 78 **nunca foram escritos** — ver [`RECONCILIACAO_TURBO_20-07.md`](../RECONCILIACAO_TURBO_20-07.md). |
| [`2026-07-25_AUDITORIA_SHARPENUP.md`](2026-07-25_AUDITORIA_SHARPENUP.md) | Auditoria da captura ponta a ponta; pedia "o padrão que faltava". | **Executada.** O padrão existe: [`GUIA_CASA_SHARPENUP.md`](../GUIA_CASA_SHARPENUP.md) (12 pontos de registro), [`SHARPENUP_ARQUITETURA.md`](../SHARPENUP_ARQUITETURA.md), `tools/audit_sharpenup.py` (verde) e as 4 skills `/sharpenup-*`. |
| [`2026-06-30_AUDITORIA_VISUAL_CASCA.md`](2026-06-30_AUDITORIA_VISUAL_CASCA.md) | Punch-list visual da casca contra o modelo. | Quase todo superado; o que sobrou é a Fatia 3 de [`PLANO_CASCA_UNIFICADA.md`](../PLANO_CASCA_UNIFICADA.md). |

## Planos executados

| Arquivo | O que era | Onde o resultado vive hoje |
|---|---|---|
| [`2026-06_PLANO_CONSTRUCAO.md`](2026-06_PLANO_CONSTRUCAO.md) | O plano original do scanner (Fases 0-4). Já se declarava histórico, com banner. | Fases 0-4 concluídas. A Fase 5 (Telegram) virou o **P3** de [`PLANO_TIPSTER.md`](../PLANO_TIPSTER.md). |
| [`2026-06-27_PLANO_UNIFICACAO.md`](2026-06-27_PLANO_UNIFICACAO.md) | Trazer as ~25.726 apostas da planilha para o Postgres. Dizia "aguardando CSV limpo". | **Executado** — o `STATUS §4` registra "migração planilha → Postgres **completa e reconciliada**". Os scripts vivem em `scripts/import_*.py`. |
| [`2026-07-22_PLANO_BET365_CAPTURA_API.md`](2026-07-22_PLANO_BET365_CAPTURA_API.md) | Promover a Bet365 de print para captura passiva pela `sportshistoryapi`. Dizia "falta escrever o código". | **Executado** — `extensor/b3_inject.js` existe e a Bet365 passa no `audit_sharpenup` como casa-robô. Manual em `casas/CASA_BET365.md`. |
| [`2026-07-11_PLANO_POLY_PERSISTIR_ATIVAS.md`](2026-07-11_PLANO_POLY_PERSISTIR_ATIVAS.md) | Posições ativas da Polymarket virarem aposta aberta na tabela Apostas. | **Executado** — `_derivar_ativas` em `app/polymarket.py`; ativa entra com `extraction_state='aberta'` e sem P/L. |

## Pesquisas aplicadas

| Arquivo | O que era | Onde o resultado vive hoje |
|---|---|---|
| [`2026-07-21_PESQUISA_BADMINTON.md`](2026-07-21_PESQUISA_BADMINTON.md) | Tudo o que era preciso para cadastrar Badminton como esporte novo. | **Aplicado na s245.** Conferido em 07/09: o `MASTER_ESPORTES_2026.md` tem 27 menções a Badminton e carrega o roster. |
| [`2026-07-21_DESAMBIGUACAO_RAQUETE.md`](2026-07-21_DESAMBIGUACAO_RAQUETE.md) | Rosters Tier 1/2 para separar Badminton × Tênis × Dardos, "prontos pra colar". | **Aplicado.** Conferido em 07/09: os nomes de badminton (An Se-young, Shi Yuqi, Anders Antonsen, Akane Yamaguchi, Chen Yufei, Kunlavut) **e** os de dardos (Humphries, van Gerwen, Littler, Smith, Cross) estão no `MASTER_ESPORTES §7`. |

## Mapas de projeto que ficaram para trás

| Arquivo | O que era | Onde o resultado vive hoje |
|---|---|---|
| [`2026-07-19_ONDE_ESTOU.md`](2026-07-19_ONDE_ESTOU.md) | "Bater o olho e saber exatamente onde o projeto está". O corpo é de **11/07 (s122)**, com um banner de 19/07 por cima dizendo que o corpo não vale. | O estado → [`STATUS.md`](../../STATUS.md); o que estava aberto → [`BACKLOG.md`](../../BACKLOG.md), **corrigido** (ele listava a Fase 1 do multiusuário como próximo passo, e ela está no ar desde a s233). |
| [`2026-07-11_IDEIAS_INDICE.md`](2026-07-11_IDEIAS_INDICE.md) | "Índice mestre de tudo que é plano, estudo ou ideia futura… página viva", de **11/07**. | **`BACKLOG §5`** ("Planos com fase aberta"). Os 2 PDFs de estudo de negócio continuam em `Ideias/`. |

---

## Por que arquivar, e não deletar

Os quatro arquivos que disputavam o papel de "onde o projeto está" (`CLAUDE.md`, `STATUS.md`,
`ONDE_ESTOU.md`, `Ideias/README.md`) se contradiziam em fatos simples — número de testes,
número de casas, status de uma frente. Três descreviam o projeto entre 30/06 e 19/07, e uma
sessão nova não tinha como saber em qual acreditar. A varredura da s261 já tinha medido o
custo: *"a primeira pendência que eu fui atacar já estava feita desde 26/07"*.

Sair de `docs/` resolve a disputa. Ser apagado perderia o **porquê** de cada decisão — e o
porquê é a parte que não se reconstrói.

_Arquivo criado em 2026-09-07 (faxina de documentação, Lote D)._
