# PLANO — Flag de inferência por-campo (glifo âmbar "confirme" na grade)

> Origem: sessão 133 (rail v2 "RAIO-X"). O SPEC do glifo pedia assinar "a célula da grade
> quando um campo foi **inferido** pela IA (11px, `--warn`, 'confirme')". Entregamos isso para
> a **categoria** (sinal real que já existe). Este doc planeja estender o sinal a **outros
> campos** (tipster, data, odd…) de forma honesta — a IA marca o que **deduziu**, não o que leu.
>
> **Sem código ainda. Precisa de OK do Feca + passo dedicado (mexe no pipeline de extração).**

---

## 1. Objetivo

Quando a IA **deduz** um campo (ex.: tipster pelo torneio, data pelo contexto) em vez de **ler**
do bilhete, a célula correspondente na grade deve mostrar o **glifo âmbar + "confirme"** e abrir a
edição em 1 clique. Hoje isso só existe para a categoria (`Outros`/`⚠️`).

## 2. Estado atual (reaproveitar, não reinventar)

| Peça | Onde | Situação |
|---|---|---|
| Heurística de confiança/notas | `repository.analisar_extracao` | Lê só as linhas extraídas; **não há confiança por-campo da IA** |
| Sinal de incerteza da categoria | `repository._aposta_incerta` = `("⚠" in aposta) or startswith("outros")` | ✅ existe |
| Amarelo acionável + **glifo âmbar** | `index.html` `_apostaIncerta` + `.btbl-tipo.incerta` + `.inc-glifo` | ✅ pronto (sessão 133) |
| Loop de correções | tabela `correcoes` (edição ✎ → `PATCH`) | ✅ existe (extração worldwide) |
| Assinatura de dedup | `repository._assinatura` | Usa **código** OU **stake+odd+descrição** — **não** usa `aposta`/`tipster` |

**Achado que barateia tudo:** já existe uma **convenção `⚠` inline** — a IA escreve `⚠` no
**valor** do campo, ele é **gravado assim**, e backend+frontend detectam. Como a dedup não olha
`aposta`/`tipster`, marcar esses campos com `⚠` **não quebra deduplicação**.

## 3. Rota recomendada (A) — estender a convenção `⚠` inline

A mais barata e coerente com o que já roda. Mudança pequena e reversível.

1. **Prompt / masters** (`global/MASTER_OUTPUT_2026.md` + `MASTER_APOSTAS §7`): instruir a IA a
   **sufixar `⚠` no valor de um campo que ela DEDUZIU** (não leu literalmente). Regra explícita:
   - Tipster: só preencher se **derivável com segurança** do bilhete/torneio; ao derivar, marcar `Nome ⚠`.
     (Hoje tipster sai vazio de propósito — isso muda: passa a poder vir **preenchido-com-ressalva**.)
   - Data: se a data foi **inferida** (ex.: "hoje/ontem" resolvido, ou torneio "Longo Prazo"), marcar `dd/mm ⚠`.
   - Nunca marcar campo **lido** direto do print.
2. **Frontend** (`index.html`): generalizar o detector `_apostaIncerta` → `_campoIncerto(valor)`
   (`"⚠" in valor`) e aplicar o **glifo âmbar + clique→edição** também nas células **Tipster** e
   **Data** (o CSS `.inc-glifo` já existe; só replicar o padrão de `.btbl-tipo.incerta`).
3. **Limpeza do `⚠` ao confirmar**: quando o operador confirma/edita a célula (modal ou inline),
   **remover o `⚠`** do valor gravado (`atualizar_bilhete` faz `strip`), e **registrar a
   confirmação/correção na tabela `correcoes`** (semente do cache aprendido).
4. **Export do usuário**: garantir que o `⚠` **não vaze** para a planilha (10 colunas). Ou (a) o
   operador confirma antes de exportar (o amarelo empurra pra isso), ou (b) o export **stripa `⚠`**
   dos valores. Decidir com o Feca — hoje o `⚠` da categoria **já** pode ir pro export se não confirmado.

**Prós:** sem coluna nova, sem mudança de parse, dedup-safe, reaproveita glifo/CSS/loop de correções.
**Contras:** o sinal é binário (incerto/não), sem grau; o `⚠` mora no valor (precisa stripar no lugar certo).

## 4. Rota alternativa (B) — canal estruturado de confiança por-campo

Só se a Rota A se mostrar insuficiente (ex.: quiser **grau** de confiança, ou marcar odd/stake sem
poluir o valor numérico).

- A IA emite, por bilhete, um **campo estruturado** além das 10 colunas + `Código` (já existe a 11ª
  coluna interna) — ex.: 12ª coluna `Incertos` = lista compacta (`tipster;data`) **ou** um bloco
  JSON paralelo keyed pelo código/índice.
- **Parse** (`parseResposta` no front + backend do `/extrair`): ler o novo canal.
- **Armazenamento**: coluna nova em `bilhetes` (ex.: `campos_incertos TEXT`) — **fora** da
  assinatura de dedup (conferir `_assinatura` e a lista de colunas do upsert).
- **Render**: idem Rota A, mas o gatilho vem da coluna, não do `⚠` no valor.

**Prós:** não polui valores; suporta grau; extensível a qualquer campo. **Contras:** mais superfície
(prompt+parse+schema+upsert+dedup), mais custo de tokens, mais risco de drift.

## 5. Impacto transversal

- **Dedup:** Rota A é segura (assinatura não usa `aposta`/`tipster`); se um dia marcar **odd/stake/
  descrição**, aí **sim** stripar `⚠` **antes** de `_assinatura`. Rota B: coluna fora da assinatura.
- **Custo de tokens:** desprezível (poucos chars por bilhete). Não muda o ~$0,011/bilhete.
- **Regressão de extração:** qualquer mudança de prompt passa pelo **harness `tools/eval_zeroshot/`**
  ANTES (mede acerto de categoria/campos) — não mexer no prompt sem baseline verde.

## 6. Fases

- **P0 — FEITO (sessão 133):** glifo âmbar na célula de **categoria** incerta (sinal `Outros`/`⚠️`).
- **P1 — Tipster deduzido:** Rota A nos campos **Tipster** (o caso do mockup). 1 regra de prompt +
  `_campoIncerto` + glifo na célula tipster + strip ao confirmar + correção registrada.
- **P2 — Data inferida:** mesmo padrão na célula **Data** (casa bem com a nota `_dataRevisao` que já existe).
- **P3 — Generalizar / grau (Rota B):** só se P1/P2 pedirem grau ou campos numéricos.

## 7. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| IA marcar demais (`⚠` em tudo) → ruído | Regra de prompt restritiva ("só se DEDUZIU"); medir taxa no harness |
| `⚠` vazar pro export do usuário | Stripar no export **ou** exigir confirmação antes de exportar (decisão Feca) |
| Prompt drift derrubar acerto de categoria | Baseline `tools/eval_zeroshot` verde antes/depois |
| Dedup contaminada por `⚠` | Só marcar campos fora da assinatura (tipster/data/aposta); stripar antes se for stake/odd/descrição |

## 8. Conexão com o loop de correções (extração worldwide)

Cada confirmação/correção de campo incerto vira **linha em `correcoes`** (`casa/campo/antigo→novo`).
Isso alimenta o **cache aprendido** (Fase 3 da extração worldwide): o que a IA hoje **deduz com `⚠`**,
amanhã ela **acerta direto** porque o cache da casa aprendeu. O glifo âmbar é, na prática, a **porta
de entrada de sinal** desse loop para campos além da categoria.

## 9. Critérios de aceite (quando construir P1)

- [ ] IA marca tipster deduzido com `⚠`; tipster lido literalmente **não** é marcado.
- [ ] Célula Tipster mostra glifo âmbar + tooltip "confirme"; clique abre edição.
- [ ] Confirmar/editar **remove o `⚠`** e grava a correção em `correcoes`.
- [ ] `⚠` não vaza pro export do usuário (conforme decisão do Feca).
- [ ] `tools/eval_zeroshot` verde (sem regressão de categoria) + `check-tokens` verde.

> **Decisão pendente do Feca antes de P1:** (a) tipster passa a poder vir **preenchido-com-ressalva**
> na extração (hoje sai vazio de propósito) — ok? (b) no export, **stripar `⚠`** ou **exigir
> confirmação**? Ver [[railv2_raiox]] · `docs/PLANO_EXTRACAO_WORLDWIDE.md`.
