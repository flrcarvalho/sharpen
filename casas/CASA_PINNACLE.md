# CASA_PINNACLE
## Camada de tradução — Pinnacle → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Pinnacle.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Pinnacle`
- Locale: pt-BR (site BR) · Moeda: R$ (BRL)
- **Decimal exibido: PONTO** (`1.609`, `400.00`) → normalizar para vírgula. *(particularidade — diferente das casas BR que já usam vírgula)*
- `Parceiro` / `Tipster`: não preenchidos na extração (vêm da app). O workspace Pinnacle tem `Parceiro = Feca [Eu]` (conta própria) — mas quem preenche é a app, não o extrator. *(o prompt antigo cravava "Feca [Eu]" fixo; na arquitetura nova isso cascateia do workspace)*

---

## 2. Modo de ingestão e layout  ⭐ (particularidade central)

A Pinnacle suporta **dois modos de ingestão**, ambos baseados na mesma tabela `.../account/my-bets-full`.
A estrutura das colunas é idêntica nos dois modos — o mapeamento de células abaixo vale para ambos.

### 2.1 Export estruturado (.xls) — modo preferencial

- Tela: `.../account/my-bets-full`, dois filtros de Status:
  - `Não decidido` → apostas **abertas** (coluna `Ganho` = retorno potencial; sem resultado ainda)
  - `Decidido` → apostas **fechadas** (coluna `Vitória/derrota` = P&L realizado)
- Botão **EXPORTAR** → arquivo `.xls` (Excel binário CDFV2). 1 linha = 1 aposta. Em geral são **simples** (cada linha tem ID próprio).

Colunas do export e como ler cada célula (multilinha, separada por `\n`):

| Coluna | Conteúdo (por linha interna) |
|---|---|
| Produto | constante "Apostas em competições esportivas" → ignorar |
| Detalhe | `ID` / `Esporte (genérico)` / `data-colocação` / `data-liquidação` |
| Seleção | `seleção + linha` / `confronto (A-vs-B)` / `tipo de mercado` / `liga @ data-do-evento` |
| Probabilidades | `odd` (3 casas, ponto) + label `Decimal` |
| Aposta (BRL) | `Risco: X.XX` + `(X.XX)` |
| Vitória/derrota | P&L **líquido** (`243.6` ganho; `-450.0` perda) |
| Status | `Decidido/Não decidido` / `Ganho/Perdeu/...` / linhas de placar |

> **Implicação:** o extrator Pinnacle é um **parser determinístico** (split das células + mapeamento), não um job de OCR. O LLM só entra para reconstruir/normalizar a descrição. Custo de extração ≈ zero. *(ver Feedback: o MODELO precisa de um campo "modo de ingestão")*
>
> **Automação:** o EXPORTAR dispara requisição autenticada na sessão logada. A extensão (Octo) pode acionar esse endpoint / ler a tabela e fazer POST direto pro scanner — sem download manual.

Os **rótulos diferem entre a tabela web e o export** (ex.: web `Partida Handicap` vs export `Partida HDP`; web `E-sports` vs export `E Sports`). O §8 cobre os dois.

**Ordenação de output (export .xls e screenshot):** aposta #1 = mais nova = última linha no TSV; aposta mais antiga = 1ª linha no TSV. Processar em ordem inversa à apresentada no arquivo ou na tela.

### 2.2 Print / Visão (screenshot da tabela web)

Quando o export não estiver disponível, o extrator aceita screenshot da tabela web.
O mapeamento de células é o mesmo do §2.1 — cada linha visual = 1 aposta.

**Regras específicas para visão:**
- Ler linha a linha; ignorar cabeçalho (`#`, `Produto`, `Detalhe`…)
- Conteúdo de cada célula: mesmo layout multilinha do §2.1
- Confronto: web exibe `-vs-` (ex.: `Nicolas Kicker -vs- Federico Coria`) → normalizar para `v` (`Nicolas Kicker v Federico Coria`)
- Placar ao vivo entre colchetes na seleção (ex.: `Project 51O -0.75 [0-0]`) → remover antes de montar a descrição
- `AO VIVO` no tipo de mercado → ignorar para classificação (ex.: `AO VIVO Partida Handicap` → Handicap)
- Cor da célula `Vitória/derrota` (verde/vermelho) = redundante; usar texto do `Status`
- Numeração `#` da primeira coluna → ignorar
- Dedup: ID (linha 1 do `Detalhe`) permanece a chave, igual ao export

---

## 3. ID do bilhete

- Formato: numérico (ex.: `3066865337`), linha 1 do `Detalhe`.
- Sempre visível (lista e export) → **dedup forte por ID, dispensa assinatura derivada.**
- O ID **nunca** vai pro output (não há coluna de ID no schema). Serve só para contar/validar/deduplicar.
- 1 ID = 1 linha.

---

## 4. Data

Regra global (decidida): a data é sempre a **data do resultado** — evento ou liquidação, que são equivalentes. A data de **colocação NUNCA é usada**.

A Pinnacle expõe as três:
- **colocação** — `Detalhe` linha 3 (ex.: `2026-06-12 16:53:51`) → **ignorar**
- **liquidação** — `Detalhe` linha 4 → equivalente ao evento
- **evento** — `Seleção` última linha, após `@` (ex.: `@ 2026-06-13`) → **usar esta**

Em múltiplas, a data é a do evento mais recente entre as pernas (regra global, `MASTER_OUTPUT_2026`).

Formato fonte: `YYYY-MM-DD HH:MM:SS` → converter para `DD/MM/AAAA`, descartar horário.

---

## 5. Status e Resultado

**Abertas** (`Status = Não decidido` / `Em andamento`): `extraction_state = aberta`. Não atribuir W/L; fica fora da fila de cópia até resolver (regra de estado = app/global).

**Fechadas** (`Status = Decidido`), linha 2 do Status:

| Pinnacle exibe | Código |
|---|---|
| Ganho | W |
| Perdeu | L |
| Reembolsado / Void | V |
| Half Win / Win Half | HW |
| Half Loss / Lose Half | HL |

Handicaps asiáticos de quarto (`0.25` / `0.75` / `1.25` / `1.75`) podem gerar `HW` / `HL` / `V`. Nunca rebaixar `HW→W` nem `HL→L`.

<!-- TODO: confirmar o rótulo EXATO que o export usa para HW/HL numa linha quarter liquidada (nos exemplos enviados só apareceu Ganho/Perdeu cheios). -->

---

## 6. Boost / promoção

**A Pinnacle não tem boost nem promoção.** Por isso a odd exibida é autoritativa — não há boost a capturar. *(É o oposto da Superbet, onde o boost obriga a usar Retorno÷Stake.)*

---

## 7. Cashout

**A Pinnacle não oferece cashout.** `Vitória/derrota` é P&L de liquidação normal, não cashout. *(Resolve por ausência a pendência que ficou aberta na Superbet — aqui simplesmente não existe.)*

---

## 8. Bônus

<!-- TODO: confirmar se a casa opera com bônus/freebets e qual a política de tratamento (excluir / marcar / incluir). Sem amostra ainda. -->

---

## 9. Mapa de mercados (Pinnacle → `Aposta` global)

Cobrindo rótulos web **e** export:

| Pinnacle exibe (web / export) | Aposta global |
|---|---|
| Partida Moneyline | ML |
| Partida 1X2 (seleção = um time) | ML |
| Partida Handicap / Partida HDP | Handicap |
| AO VIVO Partida HDP | Handicap (o "AO VIVO" é só ao vivo, ignorar p/ categoria) |
| Props de Jogadores / Especiais | Player Props |
| (mercados nomeados: Over/Under Gols, Cartões, Escanteios, Sets…) | seguir o nome → `MASTER_APOSTAS_2026` |

Notas de reconstrução:
- `(Sets)` / `(Games)` no nome da seleção = unidade do mercado em Tênis (ex.: `Segundo Goity Zapico (Games) -1.5` → Handicap em games). Entra na descrição conforme `MASTER_DESCRICAO_2026 §13.1`.
- Player props de NBA/WNBA/MLB → `Player Props` (estatística individual). Nome do jogador costuma vir na linha 1 do Seleção; normalizar (ex.: `Jesús Luzardo (Total Strikeouts)(must start)` → `Jesús Luzardo`, mercado `Strikeouts`).

---

## 10. Stake

- Origem: `Aposta (BRL)` → valor após `Risco:`. Ex.: `Risco: 400.00` → `400,00` (ponto→vírgula).
- Normalização (moeda/milhar/trim) = global (`MASTER_OUTPUT_2026 §11/§16`).

---

## 11. Odds

- Origem: coluna `Probabilidades`. Formato ponto (`1.609`, `18.060`) → vírgula (`1,609`, `18,060`). Preservar a precisão original do export — não truncar nem preencher zeros.
- **Sem boost e sem cashout** → a odd exibida é autoritativa para W/L/V/HW/HL. O `Retorno÷Stake` global daria o mesmo valor.
- `Vitória/derrota` é **P&L líquido**, não retorno total. Se for reconciliar: `retorno total = Stake + Vitória/derrota`. Ex.: stake 400, V/d +243,6 → retorno 643,6 → 643,6÷400 = 1,609 ✓.

---

## 12. Ruído a ignorar

Coluna `Produto` (constante) · label `Decimal` e abreviação `D` na coluna de odd · linhas de placar no `Status` (`1.º Set:1-0`, `Partida:1-0`, `Mapa 1:13-1`) · `AO VIVO` · a repetição `(X.XX)` da stake · placar ao vivo entre colchetes na seleção (`[0-0]`, `[1-0]`, etc.).

---

## 13. Pegadinhas (resumo rápido)

- Confronto: web/print usa `-vs-` (ex.: `Nicolas Kicker -vs- Federico Coria`) → normalizar para `v` (padrão global `MASTER_DESCRICAO_2026`).
- Placar ao vivo `[0-0]` pode aparecer colado à seleção → remover antes de montar a descrição.
- Esporte = o esporte **genérico** do `Detalhe` (`Basquetebol`→Basquete, `Beisebol`→Baseball). **NÃO** promover para a liga: Esporte é sempre o esporte, nunca a liga (regra global). A liga na linha `@` é contexto, não vai na coluna Esporte. *(isso simplifica a Pinnacle — usa o esporte do Detalhe direto)*
- Três datas — ver decisão global do §4.
- Odd: ponto → vírgula, preservar precisão original.
- `Vitória/derrota` = P&L líquido, não retorno.
- Sem boost, sem cashout.
- Rótulos divergem entre web e export.

---

## 14. Validações específicas

- Nº de linhas = nº de IDs detectados.
- ID nunca aparece no output.
- Esporte é o esporte, nunca a liga (`Basquetebol`→Basquete, nunca NBA).
- `AO VIVO` e linhas de placar removidos da descrição.
- Confronto `-vs-` normalizado para `v`.
- Placar ao vivo `[score]` removido da seleção.

---

## 15. Exemplos golden

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`
(Data = evento, conforme regra global do §4.)

**#1 — W, ML Tênis (`3066865337`):** *(export + print)*
```
12/06/2026	Tênis		Pinnacle		ML	Nicolas Kicker [Nicolas Kicker v Federico Coria]	400,00	1,609	W
```

**#2 — L, Handicap E-Sports (`3066775761`):** *(export + print)*
```
12/06/2026	E-Sports		Pinnacle		Handicap	Forsaken +1.5 [Karmine Corp Blue v Forsaken]	450,00	1,884	L
```

**#3 — W, Handicap asiático Futebol, linha quarter ganha cheia (`3066485724`):** *(export + print)*
```
11/06/2026	Futebol		Pinnacle		Handicap	Project 51O -0.75 [San Juan v Project 51O]	408,00	1,813	W
```

**#4 — L, Player Props MLB (`3065642274`):** *(export)*
```
10/06/2026	Baseball		Pinnacle		Player Props	Jesús Luzardo - Under 5.5 Strikeouts [Toronto Blue Jays v Philadelphia Phillies]	400,00	1,943	L
```

**#5 — L, Handicap Vôlei AO VIVO (`3065826963`):** *(print)*
```
10/06/2026	Vôlei		Pinnacle		Handicap	Argentina +1.5 [Sérvia v Argentina]	509,00	1,961	L
```

---

## Feedback para a camada global / MODELO (registrar p/ o passe de revisão)

1. **MODELO precisa de campo "Modo de ingestão"** (visão / export estruturado / DOM). A Pinnacle provou que isso varia por casa e muda toda a estratégia — é a primeira lacuna estrutural do esqueleto v1.
2. **DATA — DECIDIDO:** data = data do resultado (evento ≈ liquidação); colocação nunca. Vira regra no `MASTER_OUTPUT_2026` (texto pronto na conversa).
3. **`WNBA` — RESOLVIDO** pela regra liga≠esporte: WNBA → Basquete (como qualquer liga de basquete).
4. Confirmar herança: odd com nº de casas decimais variável por casa (Pinnacle 3, Superbet 2) — o §10 do MODELO já prevê, manter.

---

VERSÃO: 2026
STATUS: QUASE COMPLETO (pendência: §5 rótulo HW/HL no export)
CASA: Pinnacle
