---
description: Propaga criacao/renomeacao/remocao de categoria do MASTER_APOSTAS para todo o sistema
argument-hint: "<criar|renomear|remover> <Categoria> [-> NovoNome]"
allowed-tools: Bash(git:*), Bash(grep:*), Bash(python tools/audit_casas.py:*), Read, Edit, Grep
---

# Propagar categoria: $ARGUMENTS

Executa a REGRA DE PROPAGACAO do `CLAUDE.md` quando uma categoria muda no
`MASTER_APOSTAS_2026`. Sob a camada fina, a superficie de propagacao e pequena:
o §9 das casas lista so o que cada uma confirma. Uma etapa por vez.

## 1. MASTER_APOSTAS_2026.md (fonte unica)
- **§3** tabela de categorias: adicionar / renomear / remover a linha.
- **§4** sinonimos: adicionar/ajustar o bloco da categoria.
- **§9** validacao final: adicionar/ajustar a checagem.
- **§7** prioridade semantica: atualizar se houver risco de confusao com Player Props / Outras.
- **§5 / §6** regras por categoria / por esporte: so se aplicavel.

## 2. MASTER_DESCRICAO_2026.md
- **§12/§13**: adicionar template de descricao se o formato for novo.

## 3. Casas afetadas — SO as que ja referenciam
- Rode `grep -rl "<Categoria>" casas/` (use o nome antigo em renomear/remover).
- **criar:** quase nunca exige tocar casa (a IA classifica pelo §3 quando o mercado surgir).
- **renomear:** trocar o nome nos §9 que apareceram no grep.
- **remover:** reclassificar (provavel `Outras` ⚠️) nos §9 que apareceram; registrar no §Feedback da casa.
- Nao adicionar a categoria a casas que nao a oferecem (isso recria a duplicacao).

## 4. Auditar + commit
- `python tools/audit_casas.py` -> **zero FAIL** (nenhum §9 apontando para categoria inexistente).
- Atualizar `STATUS.md`.
- `git add/commit/push` (deploy Railway).

## Ao final
- Resumir: o que mudou no global, quais casas foram tocadas (e por que), audit OK, hash.
