# Runbook — a tabela de deduplicação

> **Fonte canônica: `app/repository.py`** — `_assinatura()` e `upsert_bilhetes()`. A
> tabela abaixo **documenta o comportamento do código**; ao mudar a lógica de dedup, o
> código é a verdade e a tabela se atualiza depois.
>
> Saiu do [`../CLAUDE.md`](../CLAUDE.md) na s366, quando ele encostou no teto de 65 KB.
> Critério do invariante #10: espelho de código é o primeiro a sair, porque duplicação
> foi o que originou o teto. **As regras que DECIDEM continuam lá** — órfã que vira
> fantasma, código escrito pela IA, o congelamento do UPSERT e o recálculo de assinatura.

---

O sistema determina se dois bilhetes são iguais ou diferentes na seguinte ordem de prioridade:

| Situação | Comportamento |
|---|---|
| **ID/código do bilhete disponível e igual** | Mesmo bilhete — UPSERT (atualiza resultado/estado) |
| **ID/código do bilhete disponível e diferente** | Bilhetes distintos — sempre INSERT (mesmo conteúdo idêntico) |
| **Sem ID, conteúdo diferente** (odd, descrição, etc.) | Bilhetes distintos — INSERT |
| **Sem ID, conteúdo idêntico, mesmo lote** | Possível sobreposição de prints — salva **ambas** as linhas (assinaturas distintas via `_counter`: `B`, `B\|2`, …) + aviso amarelo ao usuário; delete se for sobreposição real |
| **Sem ID, conteúdo idêntico, lotes diferentes** | Re-processamento do mesmo bilhete — UPSERT silencioso |

**Limitação:** onde o ID não é visível no print, dois bilhetes 100% idênticos não têm como ser distinguidos — é a 4ª linha da tabela, e ela vale por desenho: salvar ambos e avisar.

**Fonte canônica (implementação):** `app/repository.py` — `_assinatura()` e `upsert_bilhetes()`. Esta tabela documenta o comportamento do código; ao mudar a lógica de dedup, **o código é a verdade** (atualize a tabela depois).

---

> **O que NÃO está aqui, de propósito:** por que linha sem código nunca dedupa, por que
> o UPSERT congela campo de extração por IA, e por que mexer em `casa`/`parceiro` obriga
> a recalcular a assinatura. Os três decidem escrita e moram no
> [`../CLAUDE.md`](../CLAUDE.md).
