---
description: Propaga criacao/renomeacao/remocao de categoria do MASTER_APOSTAS para todo o sistema
argument-hint: "<criar|renomear|remover> <Categoria> [-> NovoNome]"
allowed-tools: Bash(git:*), Bash(grep:*), Bash(python tools/audit_casas.py:*), Read, Edit, Grep
---

# Propagar categoria: $ARGUMENTS

Executa a REGRA DE PROPAGACAO do `CLAUDE.md` quando uma categoria muda no
`MASTER_APOSTAS_2026`. Sob a camada fina, a superficie de propagacao e pequena:
o §9 das casas lista so o que cada uma confirma. Uma etapa por vez.

> A **regra** fica no `CLAUDE.md` (propagar na MESMA sessao, sem excecao). O mapa
> completo do que tocar veio para ca na s382, porque procedimento se le ao FAZER.

## 0. O mapa completo — o que atualizar, onde, o que

| O que atualizar | Onde | O que |
|---|---|---|
| Tabela de categorias | `MASTER_APOSTAS_2026.md §3` | Adicionar / renomear / remover linha |
| Sinonimos | `MASTER_APOSTAS_2026.md §4` | Adicionar bloco de sinonimos |
| Regras por categoria | `MASTER_APOSTAS_2026.md §5` | Documentar casos especiais |
| Regras por esporte | `MASTER_APOSTAS_2026.md §6` | Atualizar se o esporte for afetado |
| Validacao final | `MASTER_APOSTAS_2026.md §9` | Adicionar checagem da nova categoria |
| **Mapa de mercados — so casas afetadas** | `casas/CASA_*.md §9` | **Apenas** as casas cujo §9 ja referencia a categoria/rotulo afetado. Buscar com `grep -rl "<categoria>" casas/`. Sob a camada fina, o §9 lista so mercados confirmados — uma categoria nunca vista por uma casa **nao** aparece la e **nao** precisa de update. |
| Template de descricao | `MASTER_DESCRICAO_2026.md §12 ou §13` | Adicionar template se o formato for novo |
| Prioridade semantica | `MASTER_APOSTAS_2026.md §7` | Atualizar se houver risco de confusao com Player Props / Outros |

Os menus de esporte e mercado do editor de tipster **nao** entram nesta lista: eles leem
o MASTER em tempo de execucao (`/taxonomia`). Categoria criada aparece la sozinha.

**Checklist rapido:**

- [ ] `MASTER_APOSTAS §3` (tabela) atualizado
- [ ] `MASTER_APOSTAS §4` (sinonimos) atualizado
- [ ] `MASTER_APOSTAS §9` (validacao) atualizado
- [ ] `MASTER_APOSTAS §7` (prioridade semantica) atualizado se houver risco de confusao
- [ ] `MASTER_DESCRICAO §12/§13` atualizado se o formato de descricao for novo
- [ ] `grep -rl "<categoria afetada>" casas/` -> atualizar **so** os §9 que aparecerem (renomear/remover); novo nome quase nunca exige update de casa
- [ ] Rodar `/audit-casas` para confirmar que nenhum §9 ficou apontando para categoria inexistente

## 1. MASTER_APOSTAS_2026.md (fonte unica)
- **§3** tabela de categorias: adicionar / renomear / remover a linha.
- **§4** sinonimos: adicionar/ajustar o bloco da categoria.
- **§9** validacao final: adicionar/ajustar a checagem.
- **§7** prioridade semantica: atualizar se houver risco de confusao com Player Props / Outros.
- **§5 / §6** regras por categoria / por esporte: so se aplicavel.

## 2. MASTER_DESCRICAO_2026.md
- **§12/§13**: adicionar template de descricao se o formato for novo.

## 3. Casas afetadas — SO as que ja referenciam
- Rode `grep -rl "<Categoria>" casas/` (use o nome antigo em renomear/remover).
- **criar:** quase nunca exige tocar casa (a IA classifica pelo §3 quando o mercado surgir).
- **renomear:** trocar o nome nos §9 que apareceram no grep.
- **remover:** reclassificar (provavel `Outros` ⚠️) nos §9 que apareceram; registrar no §Feedback da casa.
- Nao adicionar a categoria a casas que nao a oferecem (isso recria a duplicacao).

## 4. Auditar + commit
- `python tools/audit_casas.py` -> **zero FAIL** (nenhum §9 apontando para categoria inexistente).
- Atualizar `STATUS.md`.
- `git add/commit/push` (deploy Railway).

## Ao final
- Resumir: o que mudou no global, quais casas foram tocadas (e por que), audit OK, hash.
