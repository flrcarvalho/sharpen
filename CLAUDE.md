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
4. Backup em `Planilhador/Backups/<nome-descritivo>/` antes de qualquer edição. Nunca usar `FDC Capital/Backups/`. **Retenção (#25 auditoria):** copiar para o backup **só os arquivos que serão editados** — nunca `docs/HISTORICO.md` (500KB, já versionado no git) nem diretórios inteiros. `Backups/` é gitignored/manual; podar snapshots além de ~últimas sessões / 90 dias quando incomodar (o git cobre o histórico versionado).
5. Arquivos completos, nunca diffs parciais.
6. Uma mudança por vez. Propor → aguardar confirmação → executar.
7. Atualizar `STATUS.md` ao fim de cada mudança aplicada.
8. **Commit e push sempre juntos.** Após cada mudança aprovada: `git add` → `git commit` → `git push`. Deploy automático via Railway. Nunca deixar commit sem push.

---

## ⚠️ REGRA DE UI / MARCA OBRIGATÓRIA (antes de criar QUALQUER visual novo)

> **Motivo:** na sessão 83, cards de KPI foram criados com formatadores caseiros que abreviavam (`1,4k`) e coloriam o valor inteiro — violando 4 regras do padrão monetário. O Feca teve que voltar em detalhe já documentado. A causa: **regra escrita sem hábito de conferir = pulada.** Esta seção torna a conferência obrigatória.

**Antes de escrever qualquer render de número, dinheiro, cor, tipografia ou componente visual, NESTA ordem:**

1. **Ler** `docs/UI_REFERENCE.md` (§5 = padrão monetário) e, se tocar na casca, `docs/SHELL_SPEC.md`. A bíblia de marca é [`../pack/CLAUDE.md`](../pack/CLAUDE.md); tokens em [`../pack/tokens/tokens.css`](../pack/tokens/tokens.css).
2. **Reusar helper existente, nunca criar formatador.** `grep` por `fmtPL`/`fmtR`/`moneyStake`/`.money` no arquivo e reusar. Todo R$ usa o componente `.money`; só muda as casas por contexto (ver `UI_REFERENCE §5`): **P/L → `fmtPL` (2 casas**, `R$` menor `--ink-soft`, cor SÓ no número, minus U+2212, zero neutro); **agregado/KPI/turnover/custo → `fmtR` (inteiro)**. **Nunca abreviar milhar (`k`/`M`) — barrado pelo `check-tokens §d`.** `.toFixed`/`.replace` só nas exceções documentadas (odd/USD), nunca em R$.
3. **Cor sempre de token** (`var(--…)`), nunca literal. `.money-sign`/sinal ficam neutros.
4. **Auto-auditar item a item contra §5 ANTES do commit** + rodar `node scripts/tokens/check-tokens.mjs`.

> Dúvida de qual convenção (tabela vs card)? Pergunte ao Feca — não invente uma terceira. Use `/nova-ui` para rodar este checklist guiado.

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
| **Mapa de mercados — só casas afetadas** | `casas/CASA_*.md §9` | **Apenas** as casas cujo §9 já referencia a categoria/rótulo afetado. Buscar com `grep -rl "<categoria>" casas/`. Sob a camada fina, o §9 lista só mercados confirmados — uma categoria nunca vista por uma casa **não** aparece lá e **não** precisa de update. |
| Template de descrição | `MASTER_DESCRICAO_2026.md §12 ou §13` | Adicionar template se o formato for novo |
| Prioridade semântica | `MASTER_APOSTAS_2026.md §7` | Atualizar se houver risco de confusão com Player Props / Outros |

> **Motivo:** em 13/06/2026 as categorias `Dupla Chance`, `Impedimentos` e `Chutes no Gol` foram criadas no MASTER mas os mapas das casas ficaram desatualizados apontando para `Outros ⚠️`. A **causa raiz** era a duplicação: cada casa reescrevia as 27 categorias. Desde a sessão 49 (camada fina), o §9 lista só o que a casa confirma → a superfície de propagação encolheu para as casas realmente afetadas.

**Checklist rápido ao criar/renomear/remover uma categoria:**

- [ ] `MASTER_APOSTAS §3` (tabela) atualizado
- [ ] `MASTER_APOSTAS §4` (sinônimos) atualizado
- [ ] `MASTER_APOSTAS §9` (validação) atualizado
- [ ] `MASTER_APOSTAS §7` (prioridade semântica) atualizado se houver risco de confusão
- [ ] `MASTER_DESCRICAO §12/§13` atualizado se o formato de descrição for novo
- [ ] `grep -rl "<categoria afetada>" casas/` → atualizar **só** os §9 que aparecerem (renomear/remover); novo nome quase nunca exige update de casa
- [ ] Rodar `/audit-casas` para confirmar que nenhum §9 ficou apontando para categoria inexistente

> Dica: use `/propagar-categoria` para automatizar este checklist.

---

## Convenções de output

> **Fonte canônica:** `global/MASTER_OUTPUT_2026.md` (TAB, 10 colunas, 11ª coluna interna `Código`, decimal vírgula, códigos de resultado). O resumo abaixo é um **espelho operacional** — ao mudar o formato, mude no MASTER primeiro.

- Separador: **TAB real** (U+0009) — nunca espaços, ponto-e-vírgula ou pipe
- **10 colunas para a planilha do usuário**: `Data | Esporte | Tipster | Casa | Parceiro | Aposta | Descrição | Stake | Odd | Resultado`
- **11ª coluna interna** (`Código`): ID/código do bilhete visível no print — nunca vai para a planilha do usuário, só para o banco de dados. A AI sempre retorna essa coluna; se não houver ID visível, a célula fica vazia.
- Decimal: **vírgula** (`2,35`) — nunca ponto
- Resultado: `W · L · V · HW · HL` — ou **vazio** quando a aposta está aberta (não liquidada; ver `MASTER_OUTPUT §13.1` / `MASTER_RESULTADO §1.1`)
- Odd sem limite de casas decimais (planilha usa a precisão completa)

---

## Regras de deduplicação (sistema)

O sistema determina se dois bilhetes são iguais ou diferentes na seguinte ordem de prioridade:

| Situação | Comportamento |
|---|---|
| **ID/código do bilhete disponível e igual** | Mesmo bilhete — UPSERT (atualiza resultado/estado) |
| **ID/código do bilhete disponível e diferente** | Bilhetes distintos — sempre INSERT (mesmo conteúdo idêntico) |
| **Sem ID, conteúdo diferente** (odd, descrição, etc.) | Bilhetes distintos — INSERT |
| **Sem ID, conteúdo idêntico, mesmo lote** | Possível sobreposição de prints — salva uma vez + aviso amarelo ao usuário |
| **Sem ID, conteúdo idêntico, lotes diferentes** | Re-processamento do mesmo bilhete — UPSERT silencioso |

**Limitação:** Para casas onde o ID não é visível no print (ou a AI não consegue lê-lo), dois bilhetes 100% idênticos (mesmos jogos, odds, stake, casa) não têm como ser distinguidos. O sistema salva um e avisa. Use o botão de deletar e re-processe se necessário.

**Fonte canônica (implementação):** `app/repository.py` — `_assinatura()` e `upsert_bilhetes()`. Esta tabela documenta o comportamento do código; ao mudar a lógica de dedup, **o código é a verdade** (atualize a tabela depois).

---

## Regra de cashout (planilha-compatível)

> **Fonte canônica:** `global/MASTER_RESULTADO_2026.md §5.1.2` (cashout = stake → V) e `§5.6` (cashout ≠ stake → W), com resumo em `MASTER_OUTPUT_2026.md §14`. **Mudou? Mude no MASTER, nunca aqui.**

Resumo: cashout **≠** stake (maior **ou** menor) → **W**, `Odd = Cashout ÷ Stake`. Cashout **=** stake, void ou cancelada → **V**, odd exibida no bilhete.

---

VERSÃO: 2026
ATUALIZADO: 2026-06-14 (sessão 15)
