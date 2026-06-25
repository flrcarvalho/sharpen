---
description: Auditoria de consistencia casa x global (camada fina) + spot-check de goldens
argument-hint: "[CASA_X.md ...] opcional - default: todas as casas"
allowed-tools: Bash(python tools/audit_casas.py:*), Read, Grep, Glob
---

# Auditoria casa x global

Objetivo: garantir que cada `casas/CASA_*.md` continua sendo camada fina de traducao
(nao redefine o global) e que nada quebrou. Read-only — nao commitar sem o usuario pedir.

## 1. Checagem deterministica
- Rode `python tools/audit_casas.py $ARGUMENTS` na raiz do Planilhador.
- O script cobre, por casa:
  - **Categoria orfa** no §9 (categoria que nao existe no `MASTER_APOSTAS_2026 §3`).
  - **Placeholder** `aguarda amostra` dentro do §9 (proibido na camada fina).
  - Bloco **Transversais cru** no §14 (deveria ser ponteiro `> **Transversais ...**`).
  - **Registro no app**: casa ausente em `app/main.py` (_CASA_DISPLAY) ou `index.html` (NOMES).
- Mostre a saida integral. Para cada FAIL, diga exatamente o que corrigir e onde.

## 2. Spot-check de goldens (§15) — modelo, nao deterministico
- Para cada casa com FAIL (ou 2-3 amostras se rodou no default), abra o §15 e confira em 1-2 goldens W:
  - Odd ~= (campo financeiro de retorno / Stake), arredondado a 2 casas.
  - Resultado em {W, L, V, HW, HL} ou vazio (aposta aberta).
  - Linha TSV com 10 colunas (+ Codigo quando a casa expoe ID).
- Reportar discrepancias; nao corrigir sem aprovacao.

## 3. Residuo transversal (casas antigas)
- Bet365 / Betano / Betfair / Pinnacle / Superbet podem ter bullets transversais soltos
  no §14 (ex.: "odd exibida em L/HL/V", "liga nao e esporte"). Sinalizar como WARN —
  limpeza e opcional e nao bloqueia.

## Ao final
- Resuma: N casas OK, N FAIL, N WARN. Se exit 0 e sem discrepancia de golden, diga
  "camada fina integra".
- Se houver FAIL, proponha o diff de correcao e aguarde aprovacao antes de aplicar.
