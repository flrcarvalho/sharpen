# CLAUDE.md — Planilhador (FDC Capital)

> Regras operacionais obrigatórias para este projeto.
> A bíblia de marca e design está em [`../pack/CLAUDE.md`](../pack/CLAUDE.md).
> O ponteiro de navegação do projeto pai está em [`../CLAUDE.md`](../CLAUDE.md).

---

## Estrutura do projeto

```
Planilhador/
├── global/          ← 6 masters globais (fonte única de verdade)
├── casas/           ← 1 arquivo por casa (traduz; nunca redefine)
├── golden_set/      ← bilhetes reais + TSV esperado (validação)
├── Backups/         ← snapshots antes de cada edição
└── STATUS.md        ← estado atual; ler antes de qualquer sessão
```

---

## Invariantes (nunca quebrar)

1. O app **lê** os masters, **nunca escreve**. Mudança = diff revisado + aprovação humana.
2. Arquivo de casa **traduz**; nunca redefine regra global.
3. **Cálculo é global, localização é da casa.**
4. Backup em `Planilhador/Backups/<nome-descritivo>/` antes de qualquer edição. Nunca usar `FDC Capital/Backups/`.
5. Arquivos completos, nunca diffs parciais.
6. Uma mudança por vez. Propor → aguardar confirmação → executar.
7. Atualizar `STATUS.md` ao fim de cada mudança aplicada.

---

## ⚠️ REGRA DE PROPAGAÇÃO OBRIGATÓRIA

**Toda vez que uma categoria for criada, renomeada ou removida do `MASTER_APOSTAS_2026.md`, os seguintes arquivos DEVEM ser atualizados na mesma sessão, sem exceção:**

| O que atualizar | Onde | O quê |
|---|---|---|
| Tabela de categorias | `MASTER_APOSTAS_2026.md §3` | Adicionar / renomear / remover linha |
| Sinônimos | `MASTER_APOSTAS_2026.md §4` | Adicionar bloco de sinônimos |
| Regras por categoria | `MASTER_APOSTAS_2026.md §5` | Documentar casos especiais |
| Regras por esporte | `MASTER_APOSTAS_2026.md §6` | Atualizar se o esporte for afetado |
| Validação final | `MASTER_APOSTAS_2026.md §9` | Adicionar checagem da nova categoria |
| **Mapa de mercados de TODAS as casas** | `casas/CASA_*.md §9` | Atualizar cada casa que oferece o mercado |
| Template de descrição | `MASTER_DESCRICAO_2026.md §12 ou §13` | Adicionar template se o formato for novo |
| Prioridade semântica | `MASTER_APOSTAS_2026.md §7` | Atualizar se houver risco de confusão com Player Props / Outras |

> **Motivo:** em 13/06/2026 as categorias `Dupla Chance`, `Impedimentos` e `Chutes no Gol` foram criadas no MASTER mas os mapas das casas ficaram desatualizados apontando para `Outras ⚠️`. Essa regra existe para evitar que isso se repita.

**Checklist rápido ao criar/renomear/remover uma categoria:**

- [ ] `MASTER_APOSTAS §3` atualizado
- [ ] `MASTER_APOSTAS §4` (sinônimos) atualizado
- [ ] `MASTER_APOSTAS §9` (validação) atualizado
- [ ] `CASA_BET365 §9` verificado e atualizado se aplicável
- [ ] `CASA_BETANO §9` verificado e atualizado se aplicável
- [ ] `CASA_BETFAIR §9` verificado e atualizado se aplicável
- [ ] `CASA_PINNACLE §9` verificado e atualizado se aplicável
- [ ] `CASA_SUPERBET §9` verificado e atualizado se aplicável
- [ ] `MASTER_DESCRICAO §12/§13` atualizado se o formato de descrição for novo

---

## Convenções de output

- Separador: **TAB real** (U+0009) — nunca espaços, ponto-e-vírgula ou pipe
- 10 colunas exatas: `Data | Esporte | Tipster | Casa | Parceiro | Aposta | Descrição | Stake | Odd | Resultado`
- Decimal: **vírgula** (`2,35`) — nunca ponto
- Resultado: apenas `W · L · V · HW · HL`
- Odd sem limite de casas decimais (planilha usa a precisão completa)

---

## Regra de cashout (planilha-compatível)

| Situação | Resultado | Odd |
|---|---|---|
| Cashout ≠ stake | **W** | Cashout ÷ Stake |
| Cashout = stake | **V** | exibida no bilhete |
| Void / Cancelada | **V** | exibida no bilhete |

---

VERSÃO: 2026
ATUALIZADO: 2026-06-13 (sessão 7)
