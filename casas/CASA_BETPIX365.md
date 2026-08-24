# CASA_BETPIX365
## Camada de tradução — `Betpix365` → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betpix365.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betpix365` — grafia **medida antes de registrar** (s258): a base já tinha 1 conta em `parceiros` e 1 linha em `casas_meta` exatamente nessa grafia, e **0 bilhetes** (conta criada sem captura). Round-trip `_casa_display(_display_to_key(x))` rodado nas **62 grafias distintas do banco**: 0 quebradas, antes e depois do registro.
- ⚠️ **`Betpix365` ≠ `PixBet`.** São casas **diferentes**, com domínios diferentes. A base tem 56 bilhetes e 3 contas em `PixBet`, que **não** entrou no `_CASA_DISPLAY` — o round-trip dela segue verbatim e nada foi reinterpretado. Nunca unificar as duas.
- Domínio: `betpix365.bet.br`
- Locale: pt-BR (rótulos em português)
- Formato numérico: **en-US** — ponto decimal em dinheiro e odds (ex.: `R$30.00`, `5.80`) → converter para vírgula (`30,00`, `5,80`)
- Moeda: `R$`
- **Motor: Altenar / BIA** (`biahosted.com`) — o mesmo da VaideBet, Esportiva e Jogo de Ouro. É a **4ª casa** do motor. Ver §2.1.
- `Parceiro` / `Tipster`: preenchidos pelo app

> **Como se confirma o motor sem login:** a home carrega `sb2wsdk-altenar2.biahosted.com/altenarWSDK.js` e `sb2wsdk-cdn-altenar2.biahosted.net`; o `integration` da casa é `betpix365`.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js` — o **mesmo** das outras três casas Altenar). Casa nasceu já com captura; nunca foi de print.

```
POST https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory
{"culture":"pt-BR","timezoneOffset":180,"integration":"betpix365","deviceType":1,
 "numFormat":"en-GB","countryCode":"BR","dateFrom":"…Z","dateTo":"…Z","liveOnly":false,
 "pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}
→ {"isLastPage":true,"bets":[…]}
```

- **Abas = array `statuses` do corpo**, mesma URL: Processado `[1,8,2,4,18]` · Aberto `[0,10,3,20,17]`.
- **Fim autoritativo: `isLastPage: true`.** Paginação por `pageNumber`, **provada ao vivo** na s258 com `pageSize:5`: pág.1 `isLastPage:false` (5 ids) · pág.2 `isLastPage:true` (4 ids novos, zero repetido) · pág.3 vazia.
- Autenticação por header **`Authorization: Bearer`**, de outra origem — **não é cookie**. Medido: `credentials:"include"` sozinho falha; o replay reusa os headers reais da requisição da página.
- O robô varre as duas abas a cada rodada. Aberta sobe com Resultado **vazio** (`extraction_state = aberta`).

### 2.1.1 ⚠️ Esta casa NÃO chama o endpoint que ela mesma precisa

É o inverso da Jogo de Ouro, e **não custa nada ao operador** — mas é o que decide se a captura funciona:

| Endpoint | Quem dispara | Traz `selections`? |
|---|---|---|
| `widgetBetHistory` (**compacto**) | a tela "Minhas Apostas" — **é o único que a casa chama** | **Não** (medido: 0 de 9 bilhetes) |
| `WidgetGetBetDetails` | um clique por card (`id` + `createdDate`) | Sim, mas **um item por chamada** |
| `widgetExpandedBetHistory` | **ninguém na casa** — responde 200 assim mesmo | Sim |

O compacto é **estruturalmente insuficiente**: sem `selections` não há perna, mercado nem data de evento. E o `WidgetGetBetDetails` por item é o anti-padrão do `CLAUDE.md` ("API externa por item = latência E falha multiplicadas. Peça a FAIXA.").

**Desenho adotado:** o inject **aprende** url + headers do compacto (`RX_APRENDE`) e reescreve o path para o expandido no replay. O compacto entra como **molde**, jamais como dado — `RX` (consumir) continua casando só `widgetExpandedBetHistory`. Os casos `casos/betpix365.mjs` e `casos/jogodeouro.mjs` travam os dois lados: o corpo do compacto não pode virar bilhete.

**Consequência operacional: nenhuma.** Basta abrir *Minhas Apostas* e capturar. Se vier `respostas: 0` com o hook ATIVO, não é tela errada — é sessão expirada (Bearer inválido) ou path mudado; o autodiagnóstico da casa diz isso.

### 2.1.2 ⚠️ Dois obstáculos ao diagnosticar esta casa pelo F12

Ambos custaram tempo na s258 e escondem a requisição de quem for investigar:

1. **A tela busca as DUAS abas no load e serve o resto de cache.** Trocar Aberto ⇄ Processado, mexer no filtro de data ou clicar em qualquer lugar **não dispara rede nenhuma** depois disso. Quem instalar um hook de `fetch` *depois* do load (console, snippet, `javascript_tool`) **nunca vê a requisição** — só um hook em `document_start` pega, que é exatamente o que o `content_scripts` do manifest faz (`"run_at": "document_start"`, `world: MAIN`). Para inspecionar à mão, use o **painel Network do DevTools aberto ANTES do reload**.
2. **`performance.getEntriesByType('resource')` mente por buffer cheio.** O padrão é **250 entradas** e esta página já estoura isso no load — a chamada do histórico simplesmente não aparece na lista. Antes de concluir "não há requisição", rode `performance.setResourceTimingBufferSize(3000)` + `performance.clearResourceTimings()`.

### 2.2 Tipo do bilhete declarado

- `type: 0` + `selections[0].isBetBuilder: true` → **Bet Builder** (seleções do mesmo jogo, pernas em `bbOdds`). Card sem título de confronto próprio: usa o nome do jogo. → `Aposta = Múltipla` (`MASTER_APOSTAS §Bet Builder`).
- `type: 0` + `isBetBuilder: false` + 1 seleção → **Simples** (categoria do mercado).
- `type: 1` → **Múltipla** de jogos distintos. O card se intitula literalmente **`Múltipla`** e o payload traz `eventName: null`.

### 2.3 Anatomia do bilhete (card)

**Bilhete Bet Builder (colapsado → expandir no `⌄`):**
```
[Confronto]                                    [GANHOU / VENCIDO | PERDIDO]
• [Mercado 1]
  [Seleção 1]                                  [odd_original] >> [odd_final]
• [Mercado 2]
  [Seleção 2]
[Badge: GOLDEN BOOST]
[Badge: CA]
[Confronto] [placar]                           DD/MM · HH:MM   ← início do evento
Cotações totais                                [ODD_FINAL]
Valor total de aposta                          R$[STAKE]
Ganho total                                    R$[RETORNO]   ← só em W; vazio em L
DD/MM · HH:MM   ID: [número]                  ← colocação + ID
```

**Múltipla de jogos distintos:**
```
Múltipla                                       [GANHOU / VENCIDO]
[Seleção]                                      [odd da seleção]
[Mercado]
[Confronto] [placar]                           DD/MM · HH:MM
… (repete por seleção)
Cotações totais                                [ODD_DECLARADA]
Valor total de aposta                          R$[STAKE]
Ganhos extra                                🎁 R$[BÔNUS]     ← ⚠ ver §8
Ganho total                                    R$[RETORNO]
DD/MM · HH:MM   ID: [número]
```

---

## 3. ID do bilhete

- Caso: **visível** (`bets[].id`)
- Formato: numérico, **10 dígitos** (ex.: `5273628588`, `5255274526`)
- Localização no card: última linha, `ID: [número]`
- **Mesmo espaço de IDs das casas irmãs Altenar** — a regex de código de `repository.py` já o reconhece (conferido na s258), então a **conferência de cobertura** está ligada nesta casa.
- Nunca vai no output do usuário — serve para dedup e validação (11ª coluna interna).

---

## 4. Data

O card traz **duas** ocorrências de `DD/MM · HH:MM`:

| Ocorrência | Campo na API | Posição no card | Usar? |
|---|---|---|---|
| **Data do evento** | `selections[].eventDate` | à direita do confronto, dentro do card expandido | **Sim** |
| Data de colocação | `createdDate` | última linha, antes de `ID:` | Não |

- **Fuso: as duas vêm em ISO com `Z` (UTC)** → converter para America/São_Paulo. Errar aqui desloca a linha inteira.
- Múltipla multi-jogo: data = perna **mais recente** (regra global, `MASTER_OUTPUT §4`).

> ⚠️ **A conversão não é detalhe cosmético.** No bilhete `5260272324` a colocação é `04/08 05:32Z` e o jogo é `05/08 02:00Z`: em UTC caem em **dias diferentes**, em Brasília os dois caem em **04/08**. Sem converter, a coluna Data sairia um dia à frente. Travado no `casos/betpix365.mjs`.

---

## 5. Status e Resultado

O estado vem do campo `status` do bilhete, **conferido contra a faixa colorida do card** (s258) — mesmo enum das casas irmãs:

| `status` (API) | Card | Nosso código |
|---|---|---|
| 0 | faixa `ABERTO` | *(vazio — não liquidar)* |
| 1 | `GANHOU / VENCIDO` | W (conferir o dinheiro) |
| 1 + retorno = stake | — | V |
| 2 | `PERDIDO` | L |
| **8** | faixa `ANULADA` (`totalWin == totalStake`) | **V** — odd exibida |
| **7** | **fora de todos os filtros da casa** | **sobe CRU** — não liquidar |
| 3 · 4 · 10 · 17 · 18 · 20 | só nos filtros das abas | **sobem CRUS** — não liquidar |

> O `8` e o `7` foram batizados na **Esportiva** (s285) e valem aqui porque o enum é do
> **motor** (Altenar/BIA), não da marca — o de-para com os 4 bilhetes reais e a medição de
> 250 bilhetes está em [`CASA_ESPORTIVA.md §5`](CASA_ESPORTIVA.md). Dois detalhes que pegam:
> a casa lista as anuladas dentro do filtro **`Ganho`** (`statuses:[1,8]`), e o `7` não está
> em filtro nenhum — sem pedi-lo de propósito, o bilhete some da tela **e** da captura.

Conferência financeira (segunda linha de defesa): `Ganho total` vazio/`0` → L · `Ganho total = Stake` → V · `Ganho total > Stake` → W.

> ⚠️ Em bilhetes `PERDIDO` o campo `Ganho total` aparece **vazio** e `totalWin: 0`. Nunca inferir retorno para L.

> ⚠️ **`totalWin` de bilhete ABERTO é o retorno POTENCIAL** e vem preenchido — a armadilha que a VaideBet levou a produção na s210. **Não há amostra dela nesta casa** (a conta tinha 0 apostas em aberto no recon), mas o formatador é o MESMO das quatro casas Altenar e o ramo está travado nos harnesses da VaideBet e da Esportiva; o caso desta casa prova, no controle negativo, que ele continua de pé. Só `status: 1` autoriza `retorno ÷ stake`.

**Gatilho de meia-liquidação (HW/HL):** aguarda amostra. Usar assinatura financeira: `HL → Ganho total = stake/2` · `HW → Ganho total = (stake/2) × (odd + 1)`.

---

## 6. Boost / promoção

- Tem boost: **sim**, e é o **padrão, não a exceção** — **8 de 9 bilhetes** da amostra da s258 são boostados.
- Localizador visual: `[odd_original] >> [odd_final]` à direita da seleção + badge verde **`GOLDEN BOOST`**.
- Na API: `selections[].boostedSelection.boostProperty: 3` — **o mesmo enum** que a Esportiva estampa como `TURBINADA` e a Jogo de Ouro como `ODDS DE OURO`. **O nome do selo é da marca; o enum é do motor.**
- `Cotações totais` (= `totalOdds`) já reflete a odd **final (boostada)**. O riscado é `boostedSelection.preBoostedPrice` e **nunca** é a odd válida.

> ⚠️ **`boostedBet.boostPercentage` vem `0` mesmo com boost real.** O sinal do boost é `preBoostedPrice ≠ totalOdds` — não esse campo. (`boostedBet.preBoostedPotWin ÷ totalStake` reproduz o riscado e serve de conferência cruzada.)

> ⚠️ **A TELA TRUNCA a odd riscada em 2 casas** (medido na s258): `preBoostedPrice: 3.3334` aparece como `3.33` no card do bilhete `5260259052`. **Nunca ler odd do card** — a captura emite o valor cheio.

---

## 7. Cashout

- Tem cashout: **campos existem** (`cashOutValue`, `partialCashOut`, `partialCashouts[]`), mas vieram **`0` em 9 de 9** — nenhuma amostra executada.
- Regra global quando aparecer: `Odd = Cashout ÷ Stake`; se `Cashout = Stake` → resultado `V` (`MASTER_RESULTADO §5.1.2` / `§5.6`).

<!-- TODO: confirmar o rótulo visual do card encerrado por cashout com amostra real. -->

---

## 8. Bônus — ⚠️ "Ganhos extra" quebra `totalOdds`

**A novidade desta casa, que nenhuma das outras três Altenar tinha mostrado.**

A Betpix365 paga um **bônus de múltipla** por fora da odd. O card o chama de **`Ganhos extra`** (com ícone 🎁) e a API o traz em `bets[].bonus`.

Consequência: **`totalWin ÷ totalStake` ≠ `totalOdds`.** No bilhete `5255274526`:

| Fonte | Valor |
|---|---|
| `totalOdds` (API) | `4.08345` |
| `Cotações totais` (card) | `4.08` ← ainda truncado |
| `Valor total de aposta` | `R$1.00` |
| `Ganhos extra` | `R$0.15` |
| `Ganho total` | `R$4.23` |

**A odd do TSV é `4,23`** — a regra global do W manda (`Odd = Retorno ÷ Stake`, `MASTER_OUTPUT`), e a odd declarada só venceria se explicasse o retorno **até o centavo**, o que aqui não acontece.

> Copiar o card erra **duas vezes**: `4,08` é truncado *e* ignora o bônus. Usar `totalOdds` erra uma: deixa R$ 0,15 fora do P/L. Travado no `casos/betpix365.mjs`.

---

## 9. Mapa de mercados (Betpix365 → `Aposta` global)

Fonte de verdade das categorias: `MASTER_APOSTAS_2026 §3`. Este mapa lista **apenas** os mercados já confirmados num bilhete real desta casa (camada fina) — a taxonomia completa vive no MASTER e **não** se reescreve aqui.

| Betpix365 exibe | Aposta global | Status |
|---|---|---|
| `1x2` | ML | ✓ confirmado |
| `Total de gols` · `1º tempo - total` · `<Time> total` | Gols | ✓ confirmado |
| `Total de escanteios` · `1º tempo - total de escanteios` · `<Time> total de escanteios` | Escanteios | ✓ confirmado |
| `Primeiro escanteio` | Escanteios | ✓ confirmado (é um `Race 1` — o objeto manda, `MASTER_APOSTAS §Race`) |
| `Total cartões` | Cartões | ✓ confirmado |
| `Ambas equipes marcam` | Ambas Marcam | ✓ confirmado |
| `<Time> para vencer um dos tempos` | Team Props | ✓ confirmado (mesmo precedente de `CASA_LOTTU §9`) |
| `BetBuilder` (`isBetBuilder: true`, 2+ pernas em `bbOdds`) | Múltipla | ✓ confirmado |
| (mercado não mapeado) | Outros | ✓ fallback |

**Notas de reconstrução:**
- Separador de times: `vs.` (ex.: `Remo vs. Atlético-MG`) → normalizar para `[Remo v Atlético-MG]` (lowercase `v`, colchetes).
- Odd e dinheiro em en-US (ponto decimal): `5.80` → `5,80`; `R$30.00` → `30,00`.
- **`Mais de X` / `Menos de X` → `Over X` / `Under X`** (`MASTER_DESCRICAO §11`). A casa exibe em português; a saída TSV é sempre em inglês.
- Recorte temporal de mercado: `1º tempo - total de escanteios` → manter o recorte na descrição (`Escanteios 1ºT`).
- Bet Builder e Múltipla: separador ` // ` entre seleções (`MASTER_DESCRICAO §16`) — o único separador de seleção do sistema, inclusive no mesmo jogo.
- No payload, o `name` da seleção de Bet Builder já vem com as pernas concatenadas por ` | `; **usar `bbOdds`**, que é o único lugar com o status de cada perna.
- Placar do jogo (`2:2`) ao lado do confronto → ruído, ignorar.

---

## 10. Stake

- Localização: campo `Valor total de aposta R$XX.XX` (= `totalStake`, também em `unitStake` e `finalStake`).
- Valores em **reais**, não em milésimos.
- Formato fonte: **en-US** — ponto decimal (ex.: `R$30.00`).
- Normalizar: remover `R$`, converter ponto decimal para vírgula (`30,00`).

---

## 11. Odds

- Campo principal: `Cotações totais` (= `totalOdds`, en-US) = odd final boostada.
- Sem limite de casas decimais: a amostra tem `4.08345` (5 casas). **Nunca truncar.**

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Ganho total ÷ Stake` (captura o boost **e** o "Ganhos extra") |
| L | `Cotações totais` — nunca `0,00`. ✅ **`totalOdds` NÃO zera em perdida** nesta casa (ao contrário de `betOdds` na KTO e `total_k` na Jonbet) |
| V | `Cotações totais` exibida — nunca `1,00` |
| HW / HL | `Cotações totais` exibida — nunca metade |
| Cashout (≠ stake) | `Odd = Cashout ÷ Stake` |

> Nos 8 bilhetes **sem** bônus da amostra, `totalOdds × stake == totalWin` fecha ao centavo nos dois W (`4×20 = 80`). O único caso em que as duas réguas divergem é o do "Ganhos extra" — §8.

---

## 12. Ruído a ignorar

`Aberto` (aba) · Badge `GOLDEN BOOST` (branding de boost) · Badge `CA` · `[odd_original] >>` (odd pré-boost) · Placar do jogo (`2:2`) · Ícone de compartilhar (↗) · `DD/MM · HH:MM` da linha do `ID:` (colocação — usar a data do evento) · `boostPercentage: 0` (não é o sinal de boost)

---

## 13. Pegadinhas (resumo rápido)

- **"Ganhos extra" quebra a odd declarada:** `totalWin ÷ stake` ≠ `totalOdds`. A odd do TSV é a do dinheiro. §8.
- **A tela trunca odd:** `3.3334` vira `3.33`, `4.08345` vira `4.08`. Nunca ler odd do card.
- **Decimal en-US:** `R$30.00`, `5.80` usam **ponto**. Converter para vírgula.
- **Duas datas, as duas em UTC:** evento vs colocação; converter para Brasília antes de comparar dias.
- **Boost é o padrão** (8/9), não caso de borda.
- **`boostPercentage: 0` mentindo:** o sinal do boost é `preBoostedPrice ≠ totalOdds`.
- **`Ganho total` vazio em L:** nunca inferir retorno.
- **Bet Builder = Múltipla**, mesmo com tudo no mesmo jogo.
- **`Betpix365` ≠ `PixBet`:** casas diferentes; jamais unificar.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

**Específicas da Betpix365:**
- Nenhum bilhete da aba `Aberto` deve sair com Resultado preenchido.
- Para W **sem** `Ganhos extra`: `Ganho total ÷ Stake = Cotações totais` (validação cruzada do boost).
- Para W **com** `Ganhos extra`: as duas divergem **por desenho** — vale `Ganho total ÷ Stake`.
- Separador de times no output: `v` — nunca `vs.` nem `x`.
- Odd e stake sempre com vírgula decimal (en-US → pt-BR).
- Bilhete com `isBetBuilder: true` → `Aposta = Múltipla`.

---

## 15. Exemplos golden (bilhetes reais)

> Amostra de 09/08/2026 (s258). Tipster e Parceiro deixados em branco (preenchidos pelo app).

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

---

### G1 — L · Bet Builder turbinado (3 pernas, mesmo jogo) · ID 5273628588

**Card (PERDIDO):**
```
Remo vs. Atlético-MG                           PERDIDO
• Total de gols
  Mais de 2.5                                  4.50 >> 5.80
• Total de escanteios
  Mais de 8.5
• Total cartões
  Mais de 3.5
GOLDEN BOOST
CA
Remo 2:2 Atlético-MG                           08/08 · 18:30
Cotações totais                                5.80
Valor total de aposta                          R$30.00
Ganho total
08/08 · 09:44   ID: 5273628588
```

**Odd:** `5,80` (lida de `Cotações totais` — bilhete L; o riscado `4.50` é pré-boost e se ignora)

**TSV esperado:**
```
08/08/2026	Futebol		Betpix365		Múltipla	Over 2,5 Gols // Over 8,5 Escanteios // Over 3,5 Cartões [Remo v Atlético-MG]	30,00	5,80	L
```

---

### G2 — W · Múltipla de 3 jogos **com "Ganhos extra"** · ID 5255274526

**Card (GANHOU / VENCIDO):**
```
Múltipla                                       GANHOU / VENCIDO
Não                                            1.55
Ambas equipes marcam
Internacional 2:0 Corinthians                  02/08 · 19:30
Não                                            1.50
Ambas equipes marcam
Palmeiras 3:0 Fortaleza                        02/08 · 16:00
Não                                            1.75
Ambas equipes marcam
Chapecoense 0:0 Cruzeiro                       02/08 · 18:30
Cotações totais                                4.08
Valor total de aposta                          R$1.00
Ganhos extra                                🎁 R$0.15
Ganho total                                    R$4.23
02/08 · 10:34   ID: 5255274526
```

**Odd:** `Ganho total ÷ Stake = 4,23 ÷ 1,00 = 4,23` — **não** `4,08345` (`totalOdds`) nem `4,08` (card truncado). O `Ganhos extra` de R$ 0,15 entra por fora da odd; ver §8.

**Data:** perna mais recente = `02/08 · 19:30` (Internacional × Corinthians).

**TSV esperado:**
```
02/08/2026	Futebol		Betpix365		Múltipla	Under Ambas Marcam [Internacional v Corinthians] // Under Ambas Marcam [Palmeiras v Fortaleza] // Under Ambas Marcam [Chapecoense v Cruzeiro]	1,00	4,23	W
```

---

## Feedback para a camada global

1. **"Ganhos extra" (bônus de múltipla) é o 1º caso, entre as casas Altenar, em que a odd declarada NÃO explica o retorno.** A regra global (`Odd = Retorno ÷ Stake` em W) já resolve, mas vale registrar o padrão: casa que paga bônus por fora exige que a régua do dinheiro vença a da estrutura. Ver `MASTER_OUTPUT`.
2. **`Primeiro escanteio: <Time>`** é um mercado de corrida (`Race 1`) sem número explícito no rótulo. Classificado como `Escanteios` pelo objeto (§Race). Avaliar se o `MASTER_DESCRICAO` deve padronizar o rótulo de `Race 1` implícito.
3. **Casas homógrafas** (`Betpix365` × `PixBet`) — o sistema trata casa como texto em 7 tabelas, então marcas de nome parecido precisam de checagem explícita antes de qualquer unificação. Já anotado em `docs/SHARPENUP_ARQUITETURA.md §5`.

---

VERSÃO: 2026
STATUS: **CAPTURA POR API** desde a s258 (casa nova — nunca foi print) · harness verde (`casos/betpix365.mjs`, 9 bilhetes reais + múltipla com bônus + controle negativo + espelho byte a byte com o host da VaideBet) · ⚠️ **NÃO validada ao vivo pela extensão**
CASA: `Betpix365`
ATUALIZADO: 2026-08-09 (sessão 258 — captura por API, 4ª casa do motor Altenar)

<!-- Sem amostra nesta casa (a conta do recon tinha 9 resolvidas e ZERO abertas):
     aposta em aberto · cashout executado · V/HW/HL · freebet · qualquer esporte além de
     futebol (`sportTypeId: 1` em 9 de 9) · os 6 valores de `status` fora de {0,1,2,8} ·
     aposta ao vivo (`isLive: false` em todas) · aposta especial (marketTypeId 5001). -->
