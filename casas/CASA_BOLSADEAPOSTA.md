# CASA_BOLSADEAPOSTA
## Camada de tradução — Bolsa de Aposta → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Bolsa de Aposta.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Bolsa de Aposta`
- Domínio: `bolsadeaposta.bet.br`
- Locale: pt-BR · Moeda: R$ prefixo, ponto de milhar, vírgula decimal (ex.: `R$1.000,00`)
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** texto colado — copiar o conteúdo da aba **Ordens** (histórico de apostas) da interface web, com todas as apostas expandidas (ícone `∨` clicado)
- **FALLBACK:** screenshot / visão — usar quando o texto colado não estiver disponível

### 2.2 Tipo do bilhete declarado

A Bolsa de Aposta não exibe rótulo fixo de tipo (Simples / Múltipla). O tipo é inferido:
- 1 seleção → categoria do mercado
- 2+ seleções → `Múltipla`

### 2.3 Layout do bilhete

**Estrutura de duas linhas por aposta (texto colado, com aposta expandida):**

```
[espaços]  [Data/Hora evento: DD/MM/AAAA HH:MM]  [Esporte]
[Confronto / Mercado]
[L/P]
A favor (Back)
[Data/Hora colocação: DD/MM/AAAA HH:MM]
[Seleção] @[odd] • R$[stake]
ID da Aposta: [ID]
[L/P] (repetido)
```

**Campos por posição:**
- Linha 1: data e hora do **evento** (autoridade para coluna Data) + esporte
- Linha 2: `Confronto / Mercado` — separador `/` divide confronto (antes) de mercado (depois)
- Linha 3: L/P total do bilhete — positivo = W, negativo = L
- Linha 4: `A favor (Back)` — indica bet de Back (apostar a favor)
- Linha 5: data e hora de **colocação** (secundária, usar como fallback de data)
- Linha 6: `Seleção @odd • R$stake` — fonte da odd e da stake
- Linha 7: `ID da Aposta: XXXXX` — ID do bilhete

**Modo screenshot:** mesma anatomia. Linha branca = dados principais; linha azul expandida = detalhes (A favor, seleção, ID).

**Ordem do output:** a interface exibe da mais recente (topo) para a mais antiga (baixo). TSV: **último no texto = 1ª linha** (cronológico crescente, mais antiga primeiro).

---

### 2.5 Captura por API — DOIS ambientes (SharpenUp 0.7.0, s299)

A casa serve **dois produtos de fornecedores diferentes**, cada um num iframe de origem
própria. A casca `bolsadeaposta.bet.br` é Angular e **não faz uma única requisição de
bilhete** — quem captura são os injects, dentro dos iframes.

| | Exchange | Sportsbook |
|---|---|---|
| iframe | `mexchange*.bolsadeaposta.bet.br` | `*.msjxk.com` |
| plataforma | LayBack / FulltBet (Next.js) | fornecedor próprio (Express) |
| endpoint | `GET mexchange-api.<domínio>/api/offers/reportsv2` | `GET <origem>/api/master/my-bets/history` |
| inject | `bda_inject.js` | `bds_inject.js` |
| formatador | `formatTicketBDA` | `formatTicketBDS` |
| ID | `id` — 9 dígitos | `TicketId` — 18 dígitos |
| paginação | `offset` / `per-page`, fim por `total` | `offset` / `limit`, fim por `totalCount` |

> A Bolsa é **plataforma, não casa**: o mesmo bundle atende `matchbook.bet.br`,
> `verdinhabet`, `fulltbet.bet.br`, `betespecial.bet.br` e `bet-bra.bet.br`.

**A sessão viaja diferente em cada ambiente — e isso decide como o robô monta o que falta.**
Medido em 26/08/2026, lendo o `src` real dos dois iframes:

| | Exchange | Sportsbook |
|---|---|---|
| `src` do iframe | `mexchange2.<domínio>/exchange` | `prod…msjxk.com/br-pt/spbk?…&operatorToken=…` |
| parâmetros | **nenhum** | 4, um deles o token (86 caracteres) |
| sessão | **cookie** (é subdomínio do site) | **na URL**, renovada a cada carga |

Por isso o robô monta a **rota da casca** (`/b/exchange` · `/fbook`) e não o endereço do
ambiente: guardar a URL do Sportsbook sem a query é guardar a porta sem a chave — o frame
sobe deslogado e a API responde `{data: []}` **sem erro nenhum** (foi o que exportou 820 em
vez de 837 na 2ª captura ao vivo). E guardar a query seria gravar credencial em disco, que
ainda vence. Pedindo à casca, o token nasce novo e nunca passa pelo SharpenUp.

Consequência de forma: com a casca no meio, o inject deixa de ser filho do topo e vira
**neto** — `_bdaPedir` desce dois níveis. Entre origens só `frames`, `length` e
`postMessage` são legíveis, e a descida usa exatamente esses três. A volta não depende
disso (o `enviar()` responde direto ao `window.top`).

**Campos do Exchange** (JSON kebab-case, valores em reais, **sem milésimos**):

| Campo | Vem de | Observação |
|---|---|---|
| Stake | `stake-matched` | ⚠️ **nunca `stake`** — a oferta `failed` traz `stake: 100` com risco zero |
| Odd | `avg-decimal-odds-matched` | correta inclusive na perdida |
| L/P | `profit-and-loss` | é **lucro**, não retorno → retorno = `stake + pl` |
| Data | `event-start-time` | **UTC com `Z`** → America/Sao_Paulo |
| Seleção | `runner-name` | ⚠️ `Sim`/`Não` — ver §9 |

**Campos do Sportsbook** (PascalCase, dinheiro e odd como **string com ponto decimal**):

| Campo | Vem de | Observação |
|---|---|---|
| Stake | `StakeDecimal` | `"400"` → 400,00 |
| Odd | `ClientOdds` | `"1.80"` → 1,80 |
| Retorno | `CurrentBetBalanceDecimal` | ⚠️ **`GainDecimal` é o POTENCIAL**, inclusive em perdida |
| Data | `Selections[].EventDate` | UTC com `Z`; múltipla usa a perna mais recente |
| Seleções | `Selections[].Translations` | o nível de cima vem em inglês (`"Custom QA"`) |

**Janelas — as duas telas perguntam ERRADO, e o replay existe para corrigir:**

- Exchange: a tela oferece no máximo 30 dias e o servidor recusa acima de **95**
  (`Max allowed interval is 95 days`, HTTP 400). O replay fatia em 90 dias.
  E **sem `status` a casa devolve só as liquidadas** — aposta em aberto exige
  `status=matched,unmatched`.
- Sportsbook: a tela manda `lastHours=1M` e, com histórico mais velho que 30 dias, isso
  devolve **`totalCount: 0`** — captura zero parecendo sucesso. **Omitir `lastHours`** traz
  tudo. O campo não aceita número: `8760` devolve 0, `12M` devolve tudo.

**A janela de dias do painel (`lookbackDias`) NÃO corta nesta casa.** O robô varre o
histórico inteiro (horizonte fixo de ~3 anos no Exchange, ~13 fatias de 90 dias; o
Sportsbook traz tudo numa chamada) e o freio incremental é o `stopId`, não o tempo.
Medido na 1ª captura ao vivo: com o padrão de 30 dias o robô varria 27/07→26/08, parava na
borda exata e trazia **21 de 418 bilhetes** — e como ele não lê a tela, a data escolhida no
calendário da casa nunca chegava até ele. O operador lia isso como "travou na primeira
página". Capturar tudo é barato porque a casa está no pré-dedup por código do backend:
bilhete já resolvido não paga IA de novo numa recaptura.

> **A data selecionada na tela da casa é irrelevante para a captura.** Ela muda só o que o
> operador **vê**; o robô fala com a API por conta própria.

## 3. ID do bilhete

- Caso: **visível**
- Formato **Exchange**: numérico, 8–9 dígitos (ex.: `98293971` em jun/2026, `119530135` em ago/2026 — a série cresce)
- Formato **Sportsbook**: numérico, 18 dígitos (ex.: `867908924308574209`) — série distinta, sem risco de colidir com a do Exchange
- Localização na tela: linha 7 do bloco de detalhe — `ID da Aposta: XXXXX`
- Na captura por API: `id` (Exchange) e `TicketId` (Sportsbook); o robô emite os dois como `[Código: …]`
- ⚠️ **No Sportsbook o card mostra OUTRO número.** A tela estampa o id da COMPRA
  (`PurchaseTicketID`), que é sempre `TicketId − 1` (conferido em 6 cards e em 17 de 17 pela
  API). O `[Código:]` continua saindo do `TicketId` **de propósito**: `PurchaseTicketID` é da
  compra, e uma compra com duas apostas daria o mesmo número às duas — o UPSERT fundiria
  bilhetes distintos e um sumiria sem erro (incidente da s276). Duplicata se vê e se apaga;
  bilhete absorvido, não. O bloco traz `ID no card da casa: …` para cruzar com a tela.
- Nunca vai no output; serve para dedup e auditoria (11ª coluna interna)

---

## 4. Data

- Fonte primária: `Data/Hora evento` — linha 1 do bloco (coluna `Data/Hora` da interface), ex.: `20/06/2026 22:57`
- Fallback: `Data/Hora colocação` — linha 5 do bloco de detalhe, ex.: `19/06/2026 23:50`
- Formato fonte: `DD/MM/AAAA HH:MM` → converter para `DD/MM/AAAA` (descartar horário)
- Múltipla: data = evento da **perna mais recente** (regra global, `MASTER_OUTPUT_2026`)

> ⚠️ Duas datas por aposta: linha 1 = evento (preferir sempre); linha 5 = colocação (só usar se evento não disponível).

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar o sinal visual diretamente. Traduzir sempre para `W · L · V · HW · HL`.

| Bolsa de Aposta exibe | Nosso código |
|---|---|
| L/P positivo (verde, sem sinal) | W |
| L/P negativo (vermelho, prefixo `-`) | L |
| L/P = R$0,00 + stake devolvida | V (aguarda amostra) |
| Meia vitória | HW (aguarda amostra) |
| Meia derrota | HL (aguarda amostra) |

Conferência financeira (segunda linha de defesa): `L/P = −stake` → L · `L/P = 0` → V · `L/P > 0` → W.

### 5.1 De-para de status na CAPTURA por API (s299)

O inject sobe o status **cru**; quem traduz é o `content.js`. Os dois ambientes têm
vocabulários diferentes e nenhum deles é texto de tela.

**Exchange** (`status`, texto) — medido em **834 ofertas de 3 anos** (a contagem por status é dessa base):

| Bruto | n | `profit-and-loss` | Nosso |
|---|---|---|---|
| `win` | 371 | presente | **W** (odd = `(stake+pl) ÷ stake`) |
| `lose` | 374 | `−stake` | **L** |
| `push` | 75 | **ausente** (não é zero) | **V** |
| `failed` | 13 | ausente, e **sem `stake-matched`** | **nenhum — não é bilhete** |
| `flushed` | 1 | ausente, `stake-matched` = **0** | **nenhum — não é bilhete** |
| `matched` · `unmatched` · `open` · `edited` · `delayed` | — | — | aberta |
| `push_win` · `push_lose` | 0 | — | **sobem crus** (a conferir) |

> `failed` e `flushed` são ofertas que **nunca casaram**: dinheiro que jamais esteve em risco. O inject a
> descarta e **conta** em `naoCasadas`, que aparece no autodiagnóstico. Ela reaparece tanto
> em `status=liquidated` quanto em `status=cancelled` — a contagem é por id, não por
> ocorrência.
>
> `push_win`/`push_lose` existem no código da casa (meia-vitória / meia-derrota) mas **não
> houve amostra real**. Ficam sem tradução de propósito: chutar HW/HL sem ter visto um
> bilhete é exatamente o que esta seção existe para impedir.

**Sportsbook** (`BetStatus`, enum numérico) — conferido contra os badges da tela:

| Bruto | Badge na tela | Nosso |
|---|---|---|
| `2` | VENCEU | **W** (odd = `CurrentBetBalanceDecimal ÷ StakeDecimal`) |
| `1` | PERDIDO | **L** |
| `4` | CANCELADA | **V** — odd é o `ClientOdds`, **nunca** retorno÷stake (daria 1,00) |
| vazio / `0` | — | aberta |
| qualquer outro | — | sobe cru (a conferir) |

> ⚠️ **`GainDecimal` é o retorno POTENCIAL, sempre.** O bilhete `857454677280481281` traz
> `"720"` e a tela dele diz **PERDIDO, Ganho Potencial 0,00**. Ler esse campo como retorno
> marca **toda perda como ganho**. O realizado é `CurrentBetBalanceDecimal`.

**Gatilho de meia-liquidação (HW/HL):**
- Primário: aguarda amostra (rótulo explícito da plataforma não confirmado)
- Confirmação por assinatura financeira exata: `HL → L/P = −stake/2` · `HW → L/P = (stake/2) × (odd − 1)`
- Só ocorre em linhas asiáticas de quarto (`.25` / `.75`)

Apostas abertas → `extraction_state = aberta`.

---

## 6. Boost / promoção

- Tem boost: **não confirmado** — aguarda amostra
- Observado: rótulo `"BEST ODDS IN BRAZIL"` aparece no campo Descrição como parte do nome do mercado (ex.: `Germany vs. Ivory Coast "BEST ODDS IN BRAZIL"`). Indica promoção de melhores odds garantidas.
- Comportamento confirmado nas amostras: @odd da linha de detalhe coincide exatamente com `(Stake + L/P) ÷ Stake` → odd exibida é a odd real (sem discrepância de boost).
- Regra enquanto não confirmado: usar `@odd` da linha de detalhe como autoritativa.

<!-- TODO: confirmar se algum mercado exibe odd decorativa diferente do retorno real. -->

---

## 7. Cashout

- Tem cashout: **não confirmado** — aguarda amostra
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → resultado `V`.

<!-- TODO: confirmar localizador visual e rótulo de cashout encerrado. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — aguarda amostra
- **Política:** pendente até ter amostra real.

<!-- TODO: confirmar se há apostas de bônus e como identificá-las. -->

---

## 9. Mapa de mercados (Bolsa de Aposta → `Aposta` global)

> A Bolsa de Aposta exibe descrições de mercado predominantemente em inglês.
> Traduzir para a categoria global; não traduzir a Descrição final (usar seleção como mostrada no bilhete).

| Bolsa de Aposta exibe | Aposta global | Status |
|---|---|---|
| `Both Score` / `Both Teams to Score` | Ambas Marcam | ✓ confirmado |
| `Over X Goals` / `Under X Goals` | Gols | ✓ confirmado |
| Nome de time como seleção (ex.: `Alemanha`) + mercado de resultado | ML | ✓ confirmado |
| Outros mercados sem categoria específica | Outros ⚠️ | fallback |

**Notas de reconstrução:**
- Confronto: a Bolsa exibe `Time A vs Time B` (inglês, com "s" em "vs") → normalizar para `[Time A v Time B]` (sem "s").
- Seleção `Sim` = resultado booleano ("sim/não") — indica mercado de BTTS, Over/Under etc.; usar a categoria do mercado (não "Sim").
- ⚠️ **Seleção `Não` NEGA o mercado — não é o mercado.** Bilhete real (`119530135`, s299):
  mercado `Arsenal over 3.5 gols`, seleção **`Não`**, odd 1,35. A aposta é que o Arsenal
  **NÃO** faz mais de 3,5 gols, então a descrição correta é `Under 3,5 [Arsenal v Coventry
  City]` — traduzir como "Over 3,5" inverte o bilhete. A regra vale para todo mercado
  booleano: `Não` + `Ambas Marcam` → `Ambas Não Marcam`; `Não` + `Over X` → `Under X`;
  `Não` + `<jogador> marca` → o jogador **não** marca.
  Na captura o campo é `runner-name`, e o `formatTicketBDA` já sobe a seleção rotulada.
- Seleção = nome de time → ML; usar nome como mostrado no bilhete (ex.: `Alemanha`).
- `Enner Valencia: Ready to Score at Any Moment` → Anytime; jogador = `Enner Valencia`; descrição = `Enner Valencia [Confronto]`.
- `Over X Goals` / `Under X Goals` → Gols; descrição = `Over X,Y [Confronto]` (ponto → vírgula no número).
- **`Mais de X` / `Menos de X` em qualquer mercado → `Over X` / `Under X`**: padrão global — ver `MASTER_DESCRICAO_2026 §11`.
- `"BEST ODDS IN BRAZIL"` no campo mercado = rótulo promocional; ignorar para classificação.
- Mercado sem categoria global → `Outros ⚠️` + registrar no §Feedback.

---

## 10. Stake

- Localização: linha 6 do bloco de detalhe — `[Seleção] @[odd] • R$[stake]`
- Formato: pt-BR — `R$100,00` (vírgula decimal, ponto de milhar quando necessário)
- Extrair o valor após `R$` e antes do fim da linha ou próximo separador

---

## 11. Odds

> **Campo financeiro principal:** `@odd` na linha 6 do bloco de detalhe (ex.: `Sim @1.90 • R$100,00`).
> Este é o campo autoritativo para a odd. Em Back bets de exchange, a odd exibida é a odd real negociada.

- Campo financeiro principal: `@odd` (linha de detalhe)
- Localização: após `@`, antes de `•`
- Verificação por L/P: para W, confirmar que `(Stake + L/P) ÷ Stake ≈ @odd`

| Resultado | Regra da odd |
|---|---|
| W | `@odd` da linha de detalhe (verificar: `(Stake + L/P) ÷ Stake`) |
| L | `@odd` da linha de detalhe — nunca `0,00` |
| V | `@odd` da linha de detalhe — nunca `1,00` |
| HW | `@odd` da linha de detalhe (aguarda amostra) |
| HL | `@odd` da linha de detalhe (aguarda amostra) |
| Cashout | `Odd = Cashout ÷ Stake` (aguarda amostra) |

**Múltiplas:**
- Aguarda amostra para confirmar se a Bolsa exibe odd combinada ou se deve calcular produto das seleções.

> ⚠️ Regra crítica: em `L` a odd nunca vira `0,00`; em `V` nunca vira `1,00`. Usar sempre `@odd` exibida.
> Precisão: preservar — não truncar nem arredondar (`MASTER_RESULTADO_2026`).

---

## 12. Ruído a ignorar

`Ordens` (cabeçalho de coluna) · `Data/Hora` (cabeçalho) · `Esporte` (cabeçalho) · `Descrição` (cabeçalho) · `L/P` (cabeçalho) · `A favor (Back)` (tipo de aposta — informacional) · `Subtotal` (linha de total ao fim da listagem) · `∨` / `^` (ícones de expansão de linha) · links de confronto (o texto do link é o confronto — usar) · `"BEST ODDS IN BRAZIL"` ou outros slogans promocionais no nome do mercado

---

## 13. Pegadinhas (resumo rápido)

- **L/P ≠ retorno total:** L/P = lucro/prejuízo, não retorno bruto. Para W: retorno = Stake + L/P. Para calcular odd via financeiro: `(Stake + L/P) ÷ Stake`. Nunca confundir L/P com retorno total.
- **Confronto em inglês com "vs":** o separador é "vs" (com "s"). Normalizar para "v" (sem "s") no output: `[Time A v Time B]`.
- **Seleção "Sim" não vai na Descrição:** "Sim" = resposta booleana ao mercado (BTTS, Over/Under etc.). A descrição segue o padrão global (ex.: `Ambas Marcam [...]`, `Over 2,5 [...]`).
- **L/P aparece duas vezes:** a última repetição (linha 8) é idêntica à linha 3 — ignorar a repetição.
- **"BEST ODDS IN BRAZIL"** = rótulo promocional no campo Descrição; ignorar para classificação de mercado e categoria.
- **Odd com ponto decimal:** o campo `@odd` usa ponto como separador decimal (en-US), ex.: `@1.90`. Converter para vírgula no output: `1,90`.
- **Data do evento vs data de colocação:** a data do evento está na linha 1 (branca); a de colocação na linha 5 (azul). Para múltiplas apostas no mesmo evento, as datas podem diferir entre os dois campos. Sempre usar data do **evento**.
- **Exchange — Back vs Lay:** amostras contêm apenas Back (`A favor`). Se aparecer Lay (`A contra`), a lógica de L/P se inverte — documentar quando surgir.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

**Específicas da Bolsa de Aposta:**
- L/P negativo → L; L/P positivo → W. Nunca invertir.
- `@odd` convertido de ponto para vírgula decimal no output.
- Confronto normalizado: `vs` → `v`; sem "s".
- Seleção `Sim` não aparece na Descrição final (substituída pelo padrão global do mercado).
- ID extraído de `ID da Aposta: XXXXX` — apenas os dígitos.

---

## 15. Exemplos golden (bilhetes reais)

Bilhetes da aba Ordens em 20/06/2026. Texto colado com apostas expandidas.

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

**Ordem de output:** última no texto (mais antiga) = primeira linha TSV.

---

### G1 — W simples · Ambas Marcam (Netherlands vs Sweden)

**Input (texto):**
```
    20/06/2026 15:45    Futebol    
Netherlands vs Sweden / Both Score
R$77,00
A favor (Back)
19/06/2026 23:51
Sim @1.77 • R$100,00
ID da Aposta: 98223602
R$77,00
```

**Verificação:** L/P = R$77,00 (positivo) → W. Odd: @1.77 = (100 + 77) ÷ 100 = 1,77 ✓

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		Ambas Marcam	Ambas Marcam [Netherlands v Sweden]	100,00	1,77	W	98223602
```

---

### G2 — W simples · ML (Germany vs Ivory Coast) com rótulo promocional

**Input (texto):**
```
    20/06/2026 19:03    Futebol    
Germany vs Ivory Coast / Germany vs. Ivory Coast "BEST ODDS IN BRAZIL"
R$53,76
A favor (Back)
20/06/2026 11:35
Alemanha @1.56 • R$96,00
ID da Aposta: 98318394
R$53,76
```

**Verificação:** L/P = R$53,76 (positivo) → W. Odd: @1.56 = (96 + 53,76) ÷ 96 = 1,56 ✓. Seleção "Alemanha" = time → ML. "BEST ODDS IN BRAZIL" = ruído.

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		ML	Alemanha [Germany v Ivory Coast]	96,00	1,56	W	98318394
```

---

### G3 — L simples · Gols Over (Ecuador vs Curaçao)

**Input (texto):**
```
    20/06/2026 22:57    Futebol    
Ecuador vs Curaçao / Ecuador Over 2.5 Goals
-R$100,00
A favor (Back)
19/06/2026 23:50
Sim @1.90 • R$100,00
ID da Aposta: 98223547
-R$100,00
```

**Verificação:** L/P = −R$100,00 (negativo = −stake) → L. Odd: @1.90 (lida diretamente).

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		Gols	Over 2,5 [Ecuador v Curaçao]	100,00	1,90	L	98223547
```

---

### G4 — L simples · Anytime (Enner Valencia)

**Input (texto):**
```
    20/06/2026 22:57    Futebol    
Ecuador vs Curaçao / Enner Valencia: Ready to Score at Any Moment
-R$100,00
A favor (Back)
20/06/2026 08:09
Sim @1.90 • R$100,00
ID da Aposta: 98293971
-R$100,00
```

**Verificação:** L/P = −R$100,00 → L. Odd: @1.90 (lida diretamente). Seleção "Sim" → ignorar; jogador = "Enner Valencia" (do nome do mercado) → Anytime.

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		Anytime	Enner Valencia [Ecuador v Curaçao]	100,00	1,90	L	98293971
```

---

## Feedback para a camada global / MODELO

1. **`Resultado Correto` (Correct Score)** — mercado comum em exchanges; não tem categoria no `MASTER_APOSTAS_2026`. Aguarda amostra para propor adição ao MASTER.
2. **Apostas Lay (`A contra`)** — exchanges permitem apostar contra. Não há amostra; se aparecer, o tratamento de L/P se inverte (Lay W = receber lucro quando evento NÃO ocorre). Aguarda amostra para documentar.
3. **Comissão sobre ganhos** — exchanges tipicamente cobram comissão (ex.: 2–5%) sobre L/P positivo. Nas amostras, `(Stake + L/P) ÷ Stake = @odd` exatamente (sem desconto visível). Confirmar se Bolsa de Aposta cobra comissão ou já embute no spread de odds.

---

VERSÃO: 2026
STATUS: ATIVO (v2 — captura por API nos dois ambientes, s299/26-08-2026; leitura v1 com 4 goldens reais de 21/06/2026)
CASA: `Bolsa de Aposta`
