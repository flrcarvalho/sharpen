# CASA_STAKE
## Camada de tradução — Stake → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Stake.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Stake`
- Domínio: `stake.bet.br`
- Locale: pt-BR na interface, **mas valores monetários e odds em formato en-US** — ponto decimal e **vírgula de milhar** (`R$1,273.08`, `R$18.88`, `3.95`). Converter sempre para o padrão BR no output. Mesma pegadinha da KTO.
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

> **A Stake roda KAMBI — o mesmo motor da KTO.** Provado pelo vocabulário, não pela aparência: a string `Total de Escanteio por Philadelphia Union` aparece literalmente nas fixtures das duas casas, junto de `Resultado Final`, esportes em caixa alta e a paginação `range_start`/`range_size`. Por isso o **§9 herda o mapa da KTO**. Mas ela **não expõe a Kambi**: embrulha num REST próprio, com nomes snake_case, dinheiro em reais (não milésimos) e status em inteiro (não string) — então a **captura** é código próprio (`stk_inject.js`), não casa espelho.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO (captura SharpenUp):** **API** — o `stk_inject.js` lê as respostas de `POST /restapi/v1/betslip/history` (e `/active`) que a própria página recebe e repagina o histórico inteiro. Dado estruturado e exato (ver §2.5).
- **SECUNDÁRIO:** screenshot / visão — cards de "Minhas Apostas".
- **FALLBACK:** texto colado da mesma lista.

> ⚠️ O robô de **rolagem genérico** (`roboScroll`) **não serve**: os cards ficam num grid de 3 colunas, sem linha em branco entre bilhetes, então o `innerText` vira um bloco único e a extração perde tudo depois dos primeiros (lição da KTO, s192).

### 2.2 Tipo do bilhete

A tela não estampa rótulo de tipo (não há "Dupla"/"Tripla"). O tipo sai do **número de seleções** do bilhete:

| Seleções | Categoria `Aposta` |
|---|---|
| 1 | categoria do mercado da seleção |
| 2+ em **jogos diferentes** | `Múltipla` |
| 2+ no **mesmo jogo** (mesmo `event_id`) | `Múltipla` — bet builder; seleções separadas por ` // ` (regra global #19) |

> Na amostra do recon (17 bilhetes) **100 % eram múltiplas de 2 a 4 seleções**. Simples e bet builder **ainda não apareceram** — o campo `bet_type` veio `1` em todos, então não há de-para provado para ele.

### 2.3 Anatomia do card

```
[Ativa | Ganha | Perdida | Anulada]  D de mmmm de AAAA HH:MM   ← status + data/hora de colocação
[Jogo: Time A - Time B]                                         ← uma linha por seleção
[Mercado]
[✓|✗] [Seleção]                    [odd da perna]
[Mais|Menos]                                                    ← resultado do mercado (só liquidado)
────────────────────────────────
Probabilidades           X.XX      ← odd total (ARREDONDADA a 2 casas — ver §11)
Valor Total          R$XXX.XX      ← stake
Pagamento            R$XXX.XX      ← retorno real (R$0.00 em perdida E em anulada)
[Sacar R$XXX.XX]                   ← botão de cashout (só em bilhete ativo)
```

O ID **não aparece no card**: só no modal que abre pelo ícone ☰ do canto superior direito, como `ID NNNNNNN` (ver §3).

### 2.4 Ordem do output

A lista exibe do **mais recente (topo)** para o **mais antigo (baixo)**. O TSV sai na ordem **inversa**: bilhete mais antigo = 1ª linha.

### 2.5 Captura por API — campos e armadilhas

Endpoint: `POST https://web-api.stake.bet.br/restapi/v1/betslip/history`
Corpo: `{"token":"<uuid de sessão>","range_start":0,"range_size":N,"status":1}`
Paginação: `next_page_exists === false` encerra; o avanço soma quantos bilhetes **voltaram**, não o `range_size` pedido.

**O campo `status` do corpo é opcional** e o de-para foi medido no recon (s257):

| `status` enviado | Devolve |
|---|---|
| `0` | só abertas |
| `1` | todas as liquidadas |
| `2` | só perdidas |
| `3` | só ganhas |
| **ausente** | **tudo — abertas + liquidadas numa chamada só** |

`POST /restapi/v1/betslip/active` devolve as abertas com os mesmos campos **mais** `bet_cashout_value` / `bet_cashout_status`, que **não existem** na resposta de liquidadas.

| Campo da API | Vira | Observação |
|---|---|---|
| `ticket_bets[].internal_bet_id` | `Código` | **7 dígitos — é o `ID` do modal (§3)** |
| `ticket_id` | — | 11 dígitos, agrupador interno da casa; **não** vai para o `Código` |
| `ticket_placed_date` | `Data` | ISO **UTC** (`+00:00`) → converter para America/São_Paulo |
| `bet_total_stake` | `Stake` | ⚠️ **vem `0` em toda ANULADA** — nunca usar sozinho |
| `bet_request_stake` | `Stake` (fallback) | é o valor que o card mostra em "Valor Total" na anulada |
| `bet_payout` | retorno real | usado para W (`Odd = payout ÷ stake`) |
| `bet_potential_payout` | retorno potencial | `0` na perdida; > 0 na aberta e na anulada |
| `bet_total_odds` | odd exibida | ⚠️ **arredondada a 2 casas** — não é a odd exata (§11) |
| `bet_selections[].bet_selection_odd` | odd da perna | o **produto** delas é a odd exata (§11) |
| `bet_status` | resultado | inteiro — de-para no §5 |
| `ticket_status` | estado do ticket | `1` ativo · `2` liquidado |
| `bet_selections[].event_sport` | esporte | enum Kambi (`FOOTBALL`, `TENNIS`…) — acaba a heurística de desempate |
| `bet_selections[].bet_selection_criteria` | mercado | rótulo pt-BR — entra no mapa do §9 |
| `bet_selections[].bet_selection_label` | seleção | `Mais 4.5` / `Justin Chung` |
| `bet_selections[].bet_selection_outcome_score` | resultado do mercado | `Mais`/`Menos`/`1`/`N/A` — `N/A` = ainda sem resultado |
| `bet_selections[].bet_selection_status` | status da perna | `1` sem marcação · `2` ganha · `3` perdida |
| `bet_selections[].early_settlement` | liquidação antecipada | `false` em toda a amostra |
| `bet_total_odds_boosted` · `bet_potential_payout_boosted` · `bet_bonus_type` | boost / bônus | **`null` em toda a amostra** (§6, §8) |

**Nunca observado na amostra** (17 bilhetes, conta do Feca): simples, boost, cashout já liquidado, freebet, bet builder e eSports. Nada disso tem de-para provado.

---

## 3. ID do bilhete

- Caso: **ID visível, mas só no detalhe** — abrir o card pelo ícone ☰ → o modal mostra `ID NNNNNNN` (numérico, 7 dígitos), ex.: `8342050`.
- Na API é o `internal_bet_id`. **Não** é o `ticket_id` (11 dígitos): conferido cruzando o modal com o JSON — `ID 8342050` é o `internal_bet_id` do ticket `12980227100`.
- O ID vai para a 11ª coluna interna `Código` exatamente como exibido.
- Dedup: por `Código` via `repository.py`.
- **IDs diferentes = bilhetes distintos** — sempre INSERT, mesmo com conteúdo idêntico. Isso é **load-bearing nesta casa**: ver o desdobramento em dois bilhetes no §13.

---

## 4. Data

- Fonte: `ticket_placed_date` (API) / cabeçalho do card = **data/hora de colocação**.
- **Fuso:** ISO em **UTC** (`+00:00`) → converter para America/São_Paulo. Sem converter, todo bilhete da madrugada pula de dia (ex.: `2026-08-09T02:11:20Z` = **08/08/2026 23:11** em Brasília).
- A data do **evento** existe por perna (`event_date`, também UTC), mas a coluna `Data` usa a de colocação — é a que o card estampa.
- **Coluna `Data`:** descartar horário → `DD/MM/AAAA`.

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar sinal visual diretamente. Traduzir sempre para `W · L · V · HW · HL`.

| Stake exibe | `bet_status` | Nosso código |
|---|---|---|
| `Ganha` | `2` | W |
| `Perdida` | `3` | L |
| `Anulada` | `4` | V |
| `Ativa` | `1` | — (não liquidada → `extraction_state = aberta`, coluna Resultado vazia) |

> ⚠️ **O DINHEIRO NÃO DISTINGUE ANULADA DE PERDIDA NESTA CASA.** As duas vêm com `Pagamento R$0.00` (`bet_payout: 0`). A conferência financeira que funciona na KTO (`payout == 0 → L`) marcaria **toda anulada como derrota** aqui. **Nesta casa o enum manda**, e a leitura financeira é só o desempate secundário: anulada tem `bet_potential_payout > 0` e `bet_total_stake == 0`, perdida tem os dois `0`.

> ⚠️ **Status fora desta tabela (cashout liquidado, meia-liquidação, recusado) ainda não apareceu em amostra.** Nunca inferir W/L de um enum desconhecido — o bloco capturado traz `Status (API): bet_status=N · ticket_status=M` cru justamente para isso. Em dúvida, deixar em aberto e sinalizar.

**Gatilho de meia-liquidação (HW/HL):** rótulo não confirmado. Confirmação por assinatura financeira (`HL → Pagamento = Aposta/2`; `HW → Pagamento = (Aposta/2)×(odd+1)`), só em linhas asiáticas de quarto (`.25`/`.75`).

---

## 6. Boost / promoção

- Tem boost: **não confirmado** — a API tem os campos (`bet_total_odds_boosted`, `bet_selection_odd_boosted`, `bet_potential_payout_boosted`), mas vieram `null` nos 17 bilhetes da amostra.
- A home anuncia promoções ("Aposta Protegida", "Odds Turbinadas"), então o caso deve existir.
- Regra global quando aparecer: em W, `Pagamento ÷ Stake` já embute o boost automaticamente.

<!-- TODO: confirmar como o boost aparece no card e qual campo carrega a odd final. -->

---

## 7. Cashout

- Tem cashout: **sim** — bilhete ativo mostra o botão `Sacar R$XX.XX`, e a API de abertas traz `bet_cashout_value` + `bet_cashout_status` (`ENABLED`).
- **O bilhete já sacado ainda não apareceu em amostra**: não se sabe qual `bet_status` ele recebe nem se o `bet_payout` passa a ser o valor do saque. Esses campos **não existem** na resposta de liquidadas.
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → `V`.

<!-- TODO: capturar um bilhete sacado e fixar o de-para do bet_status no §5. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado**. O campo `bet_bonus_type` existe e veio `null` nos 17 bilhetes.
- **Política:** pendente até ter amostra real.

---

## 9. Mapa de mercados (Stake → `Aposta` global)

> Vocabulário **Kambi**, idêntico ao da KTO — os rótulos abaixo são os confirmados **nesta casa**.
> A classificação segue `MASTER_APOSTAS_2026 §3` (30 categorias) e o princípio do §1: a categoria registra o **objeto** apostado, não o formato do mercado.

| Stake exibe | Aposta global | Status |
|---|---|---|
| `Total de Escanteio por [Time]` | Escanteios | ✓ confirmado |
| `Total de escanteios` | Escanteios | ✓ confirmado |
| `Total de Gols do [Time]` | Gols | ✓ confirmado |
| `Total asiático` (linha asiática de gols) | Gols | ⚠️ objeto = gol; linha asiática é forma, não objeto (§1 do MASTER_APOSTAS). Sem sinônimo no master — registrado no §Feedback |
| `Resultado Final` | ML | ✓ confirmado |
| `Vencedor da partida` | ML | ✓ confirmado |

**Notas de reconstrução:**
- Confronto: separador `-` (`Rotherham United - West Bromwich`) → normalizar para `v` com colchetes: `[Rotherham United v West Bromwich]`.
- `Mais X` / `Menos X` → `Over X` / `Under X` (padrão global `MASTER_DESCRICAO_2026 §11`).
- Mercado **por time** (`Total de Escanteio por Southampton`) leva o time à frente na Descrição: `Southampton - Over 5,5 Escanteios [Colchester United v Southampton]`.
- `Vencedor da partida` entre dois indivíduos: desambiguar o esporte pelo `event_sport` da API (`TENNIS`), nunca por heurística de nome.
- Mercado sem categoria → `Outros ⚠️` + registrar no §Feedback.

---

## 10. Stake

- Localização: campo `Valor Total` do card / `bet_total_stake` na API.
- Formato: **en-US — ponto decimal e vírgula de milhar** (`R$281.12`, `R$1,273.08`).
- Normalização: remover `R$`, tirar a vírgula de milhar, ponto decimal → **vírgula** (`281.12` → `281,12`).
- ⚠️ **Anulada:** `bet_total_stake` vem `0`; o valor real é o `bet_request_stake` (é o que o card mostra). Regra: `stake = bet_total_stake > 0 ? bet_total_stake : bet_request_stake`.

---

## 11. Odds

> **Campo de odd exibida:** `Probabilidades X.XX` no card. **Campo financeiro de W:** `Pagamento`.

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Pagamento ÷ Stake` (regra global) |
| L | produto das odds das pernas — **não há dinheiro para derivar** (`Pagamento` e potencial são os dois `0`) |
| V | produto das pernas (confere com `bet_potential_payout ÷ stake`) |
| HW / HL | aguarda amostra |
| Aberta | `bet_potential_payout ÷ stake`; coluna Resultado vazia + `extraction_state = aberta` |
| Cashout | `Odd = Cashout ÷ Stake` (aguarda amostra) |

**⚠️ `Probabilidades` / `bet_total_odds` é ARREDONDADA a 2 casas.** A odd exata é o **produto das odds das pernas**, e ela se prova contra o dinheiro até o centavo:

- bilhete `8357256`: `1,63 × 1,67 × 1,36 = 3,702056`; `× R$150,00 = R$555,3084` → pago **R$555,31** ✓. O card mostra `3.70`.
- bilhete `8342052`: produto `5,07428064 × R$250,00 = R$1.268,5702` → pago **R$1.268,57** ✓. O card mostra `5.07`.

Critério (mesmo da KTO): **se o produto explica o dinheiro até o centavo, ele é a odd verdadeira**; se não explica — boost, cashout, liquidação antecipada — o **dinheiro manda**. Nunca truncar; só escolher a fonte exata.

- Formato de odd: en-US (ponto) → vírgula.
- Precisão: preservar — não truncar nem arredondar (`MASTER_RESULTADO_2026`).

---

## 12. Ruído a ignorar

`Esportes Ativos` + placar + cronômetro (`55'  2º Tempo  0-0`) · logotipo `Stake` no rodapé do card · botão `Sacar R$XX.XX` (sinaliza cashout disponível, mas o bilhete continua **aberto**) · rótulos de campo `Probabilidades:` / `Valor Total:` / `Pagamento:` · setas ✓/✗ das pernas (traduzir via `bet_selection_status`, não pelo ícone) · abas `Ativas` / `Definidas` · paginação `Anterior` / `Próxima` · a tabela de "apostas de outros usuários" abaixo da lista (`Jogo · Usuário · Tempo · Chances · Valor da aposta` com nomes `Escondido`) — **não são bilhetes do operador**

---

## 13. Pegadinhas (resumo rápido)

- **⚠️ A Stake PARTE a aposta em dois bilhetes quando não aceita o valor inteiro.** Medido: **7 das 10 apostas** da amostra chegaram como **dois bilhetes**, com IDs distintos, mesmas seleções, mesmo segundo de colocação, e stakes somando número redondo — `265,55 + 34,45 = R$300`, `199,81 + 100,19 = R$300`, `126,28 + 273,72 = R$400`, `76,03 + 73,97 = R$150`. Às vezes a segunda metade é **aceita** (as duas viram W ou L), às vezes é **Anulada**. As três apostas que passaram inteiras têm stake redondo (150, 200, 250). **São bilhetes distintos e os dois têm de virar linha** — a régua de duplicata não se aplica (os `Códigos` diferem). Travado em `extensor/harness/casos/stake.mjs`.
- **`bet_total_stake` = 0 em toda anulada.** O valor real está em `bet_request_stake`. Ler o campo óbvio grava R$0,00 em 100% das anuladas (§10).
- **`Pagamento R$0.00` não significa derrota.** Anulada e perdida têm o mesmo zero — só o `bet_status` separa (§5).
- **A odd do card é arredondada.** `3.70` é na verdade `3,702056` (§11).
- **O ID não está no card.** Só no modal do ☰, e é o `internal_bet_id` de 7 dígitos — não o `ticket_id` de 11 (§3).
- **Formato en-US em dinheiro E odds:** ponto é decimal, vírgula é milhar (`R$1,273.08` = mil duzentos e setenta e três reais e oito centavos). Nunca interpretar `R$281.12` como 281 mil.
- **Data em UTC:** bilhete da madrugada pula de dia se não converter (§4).
- **A tabela abaixo da lista não é sua.** É o feed de apostas de outros usuários (`Usuário: Escondido`) — ignorar por completo.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

**Específicas da Stake:**
- Dinheiro e odds convertidos de en-US para BR (`1,268.57` → `1268,57`; `3.95` → `3,95`).
- Anulada → `V` com stake do `bet_request_stake` (nunca `0,00`, nunca `L`).
- W cross-check: `Pagamento ÷ Stake ≈ produto das odds das pernas` (devem bater até o centavo — discrepância indica boost/cashout ou leitura errada).
- `Código` presente na 11ª coluna, com **7 dígitos**.
- Bilhetes gêmeos (mesmo conteúdo, `Códigos` diferentes) geram **duas linhas** — não deduplicar.

---

## 15. Exemplos golden (bilhetes reais — captura por API, 07–09/08/2026)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

**Ordem de output:** lista = mais recente primeiro. TSV: inverso (mais antigo primeiro).

---

### G1 — L · Múltipla (3 escanteios) · metade aceita do par

**Input (card + API):**
```
Perdida   7 de Agosto de 2026 22:16      ID 8342050
Rotherham United - West Bromwich | Total de Escanteio por Rotherham United | ✗ Mais 2.5   1.46
Cheltenham - Charlton Athletic   | Total de Escanteio por Charlton Athletic | ✗ Mais 4.5  1.65
Colchester United - Southampton  | Total de Escanteio por Southampton      | ✗ Mais 5.5  1.64
Probabilidades 3.95 · Valor Total R$18.88 · Pagamento R$0.00
```

**Verificação:** `bet_status=3` → L. Odd exata = `1,46 × 1,65 × 1,64 = 3,95076` (o card arredonda para `3.95`). Data UTC `2026-08-08T01:16:48Z` → **07/08/2026** em Brasília.

**TSV esperado:**
```
07/08/2026	Futebol		Stake		Múltipla	Rotherham United - Over 2,5 Escanteios [Rotherham United v West Bromwich] // Charlton Athletic - Over 4,5 Escanteios [Cheltenham v Charlton Athletic] // Southampton - Over 5,5 Escanteios [Colchester United v Southampton]	18,88	3,95076	L	8342050
```

---

### G2 — L · Múltipla · **a gêmea de G1** (mesmo conteúdo, outro Código)

**Input:** idêntico ao G1, `ID 8342049`, `Valor Total R$281.12`.

**Verificação:** mesmas 3 seleções, mesma odd, colocado no mesmo segundo. **Não é duplicata** — `Códigos` diferentes, e `18,88 + 281,12 = R$300,00` (§13). Gera a **segunda** linha.

**TSV esperado:**
```
07/08/2026	Futebol		Stake		Múltipla	Rotherham United - Over 2,5 Escanteios [Rotherham United v West Bromwich] // Charlton Athletic - Over 4,5 Escanteios [Cheltenham v Charlton Athletic] // Southampton - Over 5,5 Escanteios [Colchester United v Southampton]	281,12	3,95076	L	8342049
```

---

### G3 — W · Múltipla (2 gols)

**Input (card + API):**
```
Ganha   8 de Agosto de 2026 13:02      ID 8347538
CA Bartolome Mitre - Atletico Sarmiento de la Banda | Total de Gols do CA Bartolome Mitre | ✓ Menos 1.5  1.43
Sporting Hasselt - Belisia Bilzen SV                | Total de Gols do Belisia Bilzen SV   | ✓ Menos 1.5  1.43
Probabilidades 2.04 · Valor Total R$44.69 · Pagamento R$91.39
```

**Verificação:** `bet_status=2` → W. Odd = `91,39 ÷ 44,69 = 2,04497…`; o produto `1,43 × 1,43 = 2,0449` explica o pagamento até o centavo (`2,0449 × 44,69 = R$91,386`) → odd = **2,0449**. O card mostra `2.04`.

**TSV esperado:**
```
08/08/2026	Futebol		Stake		Múltipla	CA Bartolome Mitre - Under 1,5 Gols [CA Bartolome Mitre v Atletico Sarmiento de la Banda] // Belisia Bilzen SV - Under 1,5 Gols [Sporting Hasselt v Belisia Bilzen SV]	44,69	2,0449	W	8347538
```

---

### G4 — V · Múltipla (3 escanteios) · **anulada com `bet_total_stake` = 0**

**Input (card + API):**
```
Anulada   9 de Agosto de 2026 11:11      ID 8360137
Náutico-PE - Atlético-GO      | Total de Escanteio por Náutico-PE      | Mais 4.5   1.43
San Diego FC - Club Tijuana   | Total de Escanteio por San Diego FC    | Menos 6.5  1.47
Cruz Azul - New York City FC  | Total de Escanteio por New York City FC| Mais 2.5   1.50
Probabilidades 3.15 · Valor Total R$34.45 · Pagamento R$0.00
API: bet_status=4 · bet_total_stake=0 · bet_request_stake=34.45 · bet_potential_payout=108.63
```

**Verificação:** `bet_status=4` → **V**, não L — o `Pagamento R$0.00` é o mesmo de uma perdida (§5). Stake vem do `bet_request_stake` = **34,45**, que é o que o card mostra (§10). Odd = `1,43 × 1,47 × 1,50 = 3,15315` (confere: `× 34,45 = R$108,626` ≈ potencial `108,63`). É a metade **recusada** do par com o bilhete `8360136` (R$265,55, ativo) — `34,45 + 265,55 = R$300,00` (§13).

**TSV esperado:**
```
09/08/2026	Futebol		Stake		Múltipla	Náutico-PE - Over 4,5 Escanteios [Náutico-PE v Atlético-GO] // San Diego FC - Under 6,5 Escanteios [San Diego FC v Club Tijuana] // New York City FC - Over 2,5 Escanteios [Cruz Azul v New York City FC]	34,45	3,15315	V	8360137
```

---

## Feedback para a camada global / MODELO

1. **`Total asiático` (total de gols com linha asiática):** sem sinônimo no `MASTER_APOSTAS_2026 §4`. Classificado como `Gols` pelo princípio do objeto (§1). Avaliar se merece sinônimo explícito — é rótulo padrão da Kambi e deve aparecer também na KTO.
2. **Bilhete partido em dois pela casa:** a Stake desdobra a aposta quando não aceita o stake inteiro, gerando **dois `Códigos`** para uma decisão só do apostador. O sistema lida bem (IDs distintos → duas linhas, P/L soma correto), mas qualquer análise por *aposta* (e não por *bilhete*) vai contar em dobro. Avaliar se o Dashboard precisa de um agrupador de "aposta lógica" (mesmas seleções + mesmo segundo de colocação).
3. **Formato en-US em casa pt-BR:** mesma pegadinha da KTO — interface em português, dinheiro e odds com ponto decimal e vírgula de milhar. Reforça a regra global de normalização de locale por casa.
4. **Odd exibida arredondada a 2 casas:** ao contrário da KTO (que trunca em 3), a Stake arredonda em 2 e só o produto das pernas dá a odd exata. Reforça a regra de nunca aceitar a odd exibida sem conciliar com o dinheiro.

---

VERSÃO: 2026
STATUS: ATIVO (v1 — 4 goldens reais da captura por API, 07–09/08/2026; **não validado ao vivo na extensão**)
CASA: `Stake`
