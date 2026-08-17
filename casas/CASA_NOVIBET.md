# CASA_NOVIBET
## Camada de tradução — Novibet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Novibet.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Novibet`
- Domínio: `novibet.bet.br`
- Locale: pt-BR na interface, **mas o payload da API mistura duas convenções** — dinheiro e odds vêm como **número JSON** (`44.7`, `11.844`, ponto decimal), enquanto o card renderiza em pt-BR (`R$44,70`, `@ 11.84`). Converter sempre para o padrão BR no output.
- ⚠️ **O nome dos esportes vem em pt-PT** (`Ténis`, `Voleibol`) — ver §3.
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

> **A Novibet é PLATAFORMA PRÓPRIA.** Não é Altenar/BIA, não é BetBy, não é Kambi, não é BetConstruct. O gateway é `BlueBrown.OnlineSportsbook.Gateway` (aparece no `$type` de todo objeto do payload) e os endpoints vivem no **mesmo host da casa**, em `/spt/` e `/ngapi/`. Por isso ela tem `nv_inject.js` e `formatTicketNV` próprios — não é casa espelho de ninguém.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO (captura SharpenUp):** **API por replay puro** — o `nv_inject.js` aprende a requisição `POST /spt/api/historytickets/search` que a página faz e **refaz a chamada ele mesmo**, alargando o filtro. Dado estruturado e exato (ver §2.5).

> ⚠️ **O modo passivo é impossível nesta casa** (medido ao vivo, s271). A página é Angular e o `HttpClient` **aborta o próprio request** ao desinscrever: ler a resposta que ela recebeu falha com *"The user aborted a request."*. É o mesmo comportamento da Pitaco. Consequência prática: o contador `respostas` do autodiagnóstico conta as chamadas do **replay**, não as da página — `hook` ativo com `respostas: 0` significa que o replay não rodou, nunca "a casa não respondeu".
- **SECUNDÁRIO:** screenshot / visão — os cards do painel **Apostas**.
- **FALLBACK:** texto colado da mesma lista.

### 2.1.1 Onde o operador precisa estar

O endpoint só dispara quando o **painel "Apostas"** é aberto (o ícone no rodapé direito, ao lado de "Cupom"). Enquanto ele não abre, o inject nunca vê uma requisição real — e sem uma requisição real **não há os headers `x-gw-*` para aprender**, então o replay não sai do lugar. O autodiagnóstico da casa diz isso quando `respostas: 0`.

> Não é preciso navegar pelas abas nem rolar a lista: basta o painel abrir uma vez. O replay busca o resto sozinho.

### 2.2 O que a tela pede (e por que não basta)

A requisição que a página faz é **estreita em dois eixos ao mesmo tempo**:

```json
{"dateFrom":"…Z","dateTo":"…Z","skip":0,"take":20,"result":2,
 "sortOrder":"Descending","sorting":2,"type":null}
```

- `dateFrom`/`dateTo` cobrem **~24 horas** (é o filtro do próprio painel);
- `result: 2` traz **só as fechadas**.

Na conta do recon isso era **11 bilhetes de 42**. Um inject puramente passivo capturaria o dia corrente, sem nenhuma aposta em aberto, e ninguém perceberia — por isso aqui o replay não é otimização, é a captura.

### 2.3 O filtro `result`

| Valor | O que volta | Medido |
|---|---|---|
| `1` | `Pending` (em aberto) | 7 |
| `2` | fechadas (`Won` + `Lost`) | 35 |
| `3` | só `Won` | 9 |
| **`null`** | **tudo** | **42** (= 7 + 35) |
| `0` | — | HTTP 400 |

O inject usa **`result: null`**: uma chamada traz abertas e fechadas juntas. É um uso que a própria página nunca faz.

### 2.4 Paginação e fim autoritativo

- `skip` / `take`, com **`take` ≤ 50** — `51` já devolve **400** (medido por busca binária).
- **Fim autoritativo:** `statistics.count` é o total **da janela** e **não muda** com `skip`/`take` (medido: `skip=5` devolve 6 itens e segue dizendo `count: 11`). Isso distingue "acabou" de "a consulta encheu" — que é exatamente o que o `Count` da Tivo **não** distinguia.
- **A paginação é sólida:** três estratégias (`take` 50, 20 e 7) devolveram **42 lidos / 42 únicos** nas três, sem repetição nem perda. (Comparar com a Pitaco, onde paginar **perdia** bilhete.)
- **Teto de histórico:** `statistics.maxDurationInMonths: 12`, e `maxDurationExceeded` liga quando a janela pedida passa disso. Histórico anterior a 12 meses a casa não serve.

### 2.5 Tabela de decisão (o que a API entrega)

| Campo | Onde está | Observação |
|---|---|---|
| ID do bilhete | `ticketId` | numérico de 9 dígitos; o card estampa com `#` |
| Stake | `placedFinancials.cost` | **TOTAL**. `amount` é o valor **por linha** (só difere em sistema) |
| Retorno real | `settlement.payout` | **só existe depois de liquidar** |
| Retorno potencial | `finalFinancials.payout` | ⚠️ **SEMPRE potencial**, inclusive em bilhete perdido |
| Odd | `placedPrice.value` | exata; `placedPrice.text` é a do card, truncada a 2 casas |
| Odd revisada | `finalPrice.value` | difere quando uma perna é anulada/meio-anulada |
| Data | `placedAt` | **UTC com `Z`** → America/Sao_Paulo |
| Liquidação | `settlement.settledAt` | UTC |
| Status | `result` | `Won` / `Lost` / `Pending` (string, não enum numérico) |
| Estrutura | `ticketType` + `multiplier` | `Accumulator` (1 linha) · `Fold2` (duplas) |
| Esporte | `betContext.competitionContextSysname` | `SOCCER`, `TENNIS_SINGLES`, … (o `Caption` é pt-PT) |
| Mercado | `betInstance.offerCaption` | ⚠️ vem com 🚀 colado quando a odd é turbinada |
| Confronto | `betContext.betContextCaption` | `Chicago Fire FC - Portland Timbers` |
| Boost | `placedFinancials.boost` | `{amount, factor}` — multiplicativo, pago por fora |
| Imposto | `settlement.withholdingTax` | 0 em 35 de 35 na amostra |
| Cashout | `cashout` / `cashoutPrice` | `null` em 42 de 42 — ver §7 |

---

## 3. Esporte — a casa escreve em pt-PT

⚠️ **Esta é a tradução mais fácil de esquecer**, porque o texto parece correto. O `competitionContextCaption` vem em **português europeu**; o MASTER é pt-BR. Traduzir pelo **`competitionContextSysname`**, que é estável:

| `competitionContextSysname` | A casa exibe | `Esporte` global |
|---|---|---|
| `SOCCER` | Futebol | `Futebol` |
| `TENNIS_SINGLES` | **Ténis** | **`Tênis`** |
| `BASKETBALL` | Basquete | `Basquete` |
| `VOLLEYBALL` | **Voleibol** | **`Vôlei`** |
| `ICE_HOCKEY` | Hóquei no Gelo | `Hóquei no Gelo` |

> Gravar `Ténis` ou `Voleibol` cria um esporte paralelo no banco — o mesmo estrago que uma grafia nova de casa.

**O prefixo do `marketSysname` concorda com o esporte em 100% da amostra** (`SOCCER_*` → SOCCER, `TENNIS_*` → TENNIS_SINGLES, …), então serve de conferência independente quando o `betContext` faltar.

---

## 4. Data

- Campo: **`placedAt`** (colocação), **UTC com `Z`** → converter para **America/Sao_Paulo**.
- ⚠️ **Não existe data de evento no payload.** A varredura de todo campo temporal encontrou **apenas** `placedAt` e `settledAt` (liquidação). O card mostra a hora do evento nas pernas (`seg. 13:00`), mas isso vem de outro feed, não do histórico.
- Conferido ao segundo contra o card: `2026-08-16T15:01:27.0773689Z` ⇄ `16/8/2026, 12:01:27`.

> A coluna `Data` do TSV é, portanto, a **colocação**. É o que a casa tem e é o que o card mostra.

---

## 5. Status e Resultado

| `result` da API | Card | `Resultado` global |
|---|---|---|
| `Won` | verde, com "Retornos" | `W` |
| `Lost` | cinza, sem retorno | `L` |
| `Pending` | aba "Abertas" | **vazio** (não liquidada) |

**Separador determinístico entre aberta e resolvida:** `settlement` é **`null`** em toda aberta. Não é preciso interpretar enum nenhum.

Resultado por **perna** (`betInstance.finalResult`), confirmados na amostra:

| Perna | Significado |
|---|---|
| `Won` / `Lost` | ganha / perdida |
| `HalfLostHalfVoid` | metade perdida, metade anulada — **derruba a odd do bilhete** (ver §11) |
| `null` | ainda não liquidada (bilhete aberto) |

> **Sem amostra:** bilhete anulado/void, cashout executado, `HalfWon`, e qualquer `result` fora de `{Won, Lost, Pending}`. Valor novo sobe **cru** na linha `Status (API):` e **não** é liquidado automaticamente.

---

## 6. Boost / promoção

A casa tem **dois mecanismos diferentes**, e só o segundo aparece como campo:

1. **Odd turbinada (🚀)** — a odd sobe e **o payload já traz a efetiva**. O card mostra a riscada e a nova (`13.00@ 17.66`); o `placedPrice` traz só `17.661`, que bate com o produto das pernas turbinadas. **Não há nada a corrigir:** a odd do payload é a que vale. O emoji 🚀 vem colado no `offerCaption` e é separado na normalização.
2. **Boost multiplicativo** — `placedFinancials.boost = {amount, factor}`. É **pago por fora da odd**: `payout = cost × odd × factor` (medido: 51 × 7,61838 × 1,05 = 407,9643, exatamente o `payout` declarado). O `amount` é só o extra arredondado a 2 casas.

> Em bilhete **ganho** nada disso precisa de tratamento especial: a regra global do `W` (`Retorno ÷ Stake`) absorve os dois.
>
> **Sem amostra:** os 3 bilhetes com boost na fixture são todos `Lost`, então **não foi possível confirmar num W** que o `settlement.payout` inclui o `factor`. Quando aparecer um boost ganho, conferir e travar no harness.

---

## 7. Cashout

- Campos: `cashout`, `cashoutPrice`, `cashoutResult`, `cashedOutAt` — **`null` em 42 de 42** na amostra.
- O card **oferece** cashout nas abertas (`Cash out R$ 24,69`), mas esse valor **não vem no payload do histórico**: é preço ao vivo, servido por outro canal.
- Quando aparecer um bilhete efetivamente sacado, vale a regra global (`MASTER_RESULTADO §5.1.2` / `§5.6`): cashout **=** stake → `V`; **≠** stake → `W` com `Odd = Cashout ÷ Stake`.

> **Sem amostra.** Não inventar de-para.

---

## 8. Bônus

- `placedFinancials.bonus = {amount, factor}` — na amostra vem **sempre idêntico ao `boost`** (mesmos 19,42 / 16,42 / 19,82 com `factor: 1.05`), o que sugere que são duas leituras do mesmo evento, não dois bônus somados.
- `costDiscount`: 0 em 42 de 42.
- Freebet: **sem amostra** — nenhum campo de aposta grátis apareceu.

---

## 9. Mapa de mercados (Novibet → `Aposta` global)

> Vocabulário **próprio** da casa. Os rótulos abaixo são os **confirmados nesta casa**, de 123 pernas reais.
> A classificação segue `MASTER_APOSTAS_2026 §3` e o princípio do §1: a categoria registra o **objeto** apostado, não o formato do mercado.
> ⚠️ O rótulo real pode vir com **🚀 colado** (odd turbinada) e com espaço final — comparar sempre normalizado.

### Futebol

| Novibet exibe | Aposta global | Status |
|---|---|---|
| `Total de Gols` | Gols | ✓ confirmado |
| `Asiático Total de Gols` | Gols | ✓ objeto = gol; linha asiática é forma (§1) |
| `1° Tempo - [Time] Total de Gols` | Gols | ✓ segmento é forma, não objeto |
| `2° Tempo - [Time] Total de Gols` | Gols | ✓ confirmado |
| `Total de Escanteios` | Escanteios | ✓ confirmado |
| `[Time] Total de Escanteios` | Escanteios | ✓ confirmado |
| `Disputa até X Escanteios` | Escanteios | ✓ confirmado (a seleção é `Nenhum para 9`, `Casa para 7`…) |
| `Escanteios Resultado Final` | Escanteios | ✓ confirmado |
| `Total de Cartões` | Cartões | ✓ confirmado |
| `[Time] Total de Cartões` | Cartões | ✓ confirmado |
| `Cartões Resultado` | Cartões | ✓ objeto = cartão (§1) |
| `[Time] - Total de Chutes no gol` | Chutes no Gol | ✓ confirmado |
| `Handicap Asiático` | Handicap | ✓ confirmado |
| `Resultado ao Intervalo` | ML | ✓ 1x2 do intervalo — segmento é forma |
| `Bola na trave` | **Outros ⚠️** | ⚠️ objeto sem categoria no MASTER — ver §Feedback |

### Basquete

| Novibet exibe | Aposta global | Status |
|---|---|---|
| `Vencedor do Jogo` | ML | ✓ confirmado |
| `Handicap (Adicional)` | Handicap | ✓ confirmado |
| `[Jogador] - Pontos` | Player Props | ✓ estatística individual (§6 NBA/Basquete) |
| `[Jogador] - Rebotes` | Player Props | ✓ estatística individual |
| `[Time] Total de cestas de três pontos marcadas` | **Team Props ⚠️** | ⚠️ estatística de time; objeto é a cesta de 3, não o ponto |

### Tênis

| Novibet exibe | Aposta global | Status |
|---|---|---|
| `Total de Games` | Games | ✓ confirmado |
| `Handicap de Games` | Games | ✓ objeto = game (§1) |
| `Total de Quebras de Serviço` | Player Props | ✓ break points são estatística individual (§6 Tênis) |
| `[Jogador] Total de Quebras de Serviço` | Player Props | ✓ confirmado |
| `1° Set - [Jogador] Total de Breaks` | Player Props | ✓ confirmado |

### Vôlei / Hóquei

| Novibet exibe | Aposta global | Status |
|---|---|---|
| `1° Set Vencedor` | **ML ⚠️** | ⚠️ vencedor de um set — resultado, não contagem de sets; ver §Feedback |
| `Handicap` (hóquei) | Handicap | ✓ confirmado |

**Notas de reconstrução:**
- Confronto: separador `-` (`Chicago Fire FC - Portland Timbers`) → normalizar para `v` com colchetes: `[Chicago Fire FC v Portland Timbers]`.
- `Mais de X` / `Menos de X` → `Over X` / `Under X` (`MASTER_DESCRICAO_2026 §11`).
- Mercado **por time** (`Brusque SC Total de Escanteios`) leva o time à frente na Descrição.
- ⚠️ **A vírgula decimal aparece dentro da seleção** (`Menos de 2,00`, `Mais de 3,5`) — é linha de mercado, não valor monetário.
- Mercado sem categoria → `Outros ⚠️` + registrar no §Feedback.

---

## 10. Stake

- Localização: `placedFinancials.cost` na API · **"Valor"** (fechadas) ou **"Total"** (abertas) no card.
- ⚠️ **Em bilhete de sistema, `cost` é o TOTAL e `amount` é o valor POR LINHA** — `cost / amount == multiplier` em 19 de 19. O card mostra o **total** (`Valor R$303,00`), e é ele que vai para a coluna `Stake`. Emitir o `amount` dividiria por 3 o turnover de todo bilhete de sistema.

---

## 11. Odds

**A regra é global** (`MASTER_RESULTADO`); aqui só a localização:

| Situação | Odd |
|---|---|
| `Won` | **`settlement.payout ÷ cost`** — precisão total (absorve boost e sistema) |
| `Lost` / `Pending`, múltipla comum | `placedPrice.value` |
| `Lost` / `Pending`, **sistema** | `placedPrice.value ÷ multiplier` (ver abaixo) |

⚠️ **`placedPrice.text` é truncado a 2 casas** (`11.844` vira `"11.84"`). Nunca usar o `text` — odd sem truncar é regra primordial.

### 11.1 A odd do SISTEMA não é a do card

Esta é a armadilha central da casa, e é a mesma da bet365 (s265) com outra roupa.

Em `ticketType: "Fold2"`, **`placedPrice` não é a odd do bilhete**: é a **SOMA dos produtos das C(n,2) linhas** (medido em 19 de 19). A odd estrutural é essa soma **dividida pelo número de linhas** — que é exatamente a **média** do `MASTER_RESULTADO §7.3`.

Exemplo real (`#474269610`, sistema ganho):

```text
pernas:        1,76 · 1,87 · 1,94
duplas:        1,76×1,87 = 3,2912 | 1,76×1,94 = 3,4144 | 1,87×1,94 = 3,6278
soma:          10,3334  ← é ISTO que o card estampa como "@ 10.33"
odd estrutural: 10,3334 ÷ 3 = 3,44446667   (média das 3 linhas)
odd REAL (W):   R$ 332,4112 ÷ R$ 303,00 = 1,09706667
```

Ganharam **2 das 3 duplas**: `1,76 × 1,87 = 3,2912`, e `3,2912 × R$ 101,00` (o stake por linha) `= R$ 332,4112` — o retorno, ao centavo. **A conferência fecha em 7 de 7 sistemas ganhos da amostra.**

> Copiar o `@ 10.33` do card daria uma odd **9× maior** que a real.

### 11.2 Odd revisada (perna anulada)

Quando uma perna sai como `HalfLostHalfVoid`, `finalPrice` fica **menor** que `placedPrice`:

```text
#473922217: placedPrice 7,62734 → finalPrice 2,107
pernas: Lost 2,15 · Lost 1,96 · HalfLostHalfVoid 1,81
2,15 × 1,96 ÷ 2 = 2,107   (a perna meio-anulada vale metade do bilhete)
```

Nos dois casos da amostra o bilhete perdeu (`payout` 0), então a odd revisada não mudou o P/L. **Se aparecer num ganho, o dinheiro manda** (regra global do `W`).

---

## 12. Ruído a ignorar

- `$type` (nome da classe .NET do gateway) em todo objeto.
- `playerId`, `betInstanceId`, `marketInstanceId`, `marketId`, `betContextId` — ids internos.
- `marketOfferMetrics` — placar/estatística do evento no momento da liquidação.
- `competitorsCaptions: {"$type":"Empty"}`.
- `Aposta Blindada` no card: promoção da casa; `securedOdds` veio `false` em 123 de 123 pernas.
- `APOSTA` grudado no texto do card entre bilhetes (artefato de layout).

---

## 13. Pegadinhas (resumo rápido)

1. **`finalFinancials.payout` é SEMPRE potencial** — inclusive em bilhete perdido (529,4268 num `Lost`). O retorno real só existe em `settlement.payout`.
2. **A odd do sistema não é a do card** — `placedPrice` do `Fold2` é a SOMA das linhas (§11.1).
3. **`cost` (total) × `amount` (por linha)** — usar o `amount` como stake divide o turnover por 3.
4. **Esporte em pt-PT** — `Ténis` → `Tênis`, `Voleibol` → `Vôlei` (§3).
5. **`placedPrice.text` é truncado** — usar sempre o `value`.
6. **A tela pede 1 dia e só as fechadas** — sem o replay, a captura pega uma fatia mínima (§2.2).
7. **🚀 colado no nome do mercado** — normalizar antes de mapear (§9).
8. **Histórico limitado a 12 meses** pela própria casa (§2.4).

---

## 14. Validações específicas

- `Data` no fuso de São Paulo (o payload é UTC com `Z`).
- `Stake` = `cost`, nunca `amount`.
- Em `W`, `Odd` = `settlement.payout ÷ cost`, sem truncar.
- Em bilhete de sistema, a 12ª coluna interna (`Sistema`) tem de sair preenchida (`3x Duplas`) — o backend a anexa lendo a linha `Tipo: SISTEMA …` do texto do robô.
- Conferência independente da odd de múltipla comum: **o produto das odds das pernas bate com `placedPrice`** em 23 de 23 `Accumulator` da amostra.
- Esporte traduzido pelo `competitionContextSysname`, não pelo texto exibido.

---

## 15. Exemplos golden (bilhetes reais — captura por API, 16/08/2026)

**#474311813 — múltipla perdida (a armadilha do potencial)**

```text
Data 16/08/2026 · Stake R$ 44,70 · Odd 11,844 · Resultado L
3 seleções · placedPrice.text = "11.84" (truncado) · value = 11.844
finalFinancials.payout = 529,4268  ← POTENCIAL, o bilhete PERDEU
settlement.payout = 0              ← o retorno real
```

**#474269610 — sistema `Doublesx 3` ganho (a armadilha da odd)**

```text
Data 16/08/2026 · Stake R$ 303,00 (total; R$ 101,00 por linha) · Resultado W
card:  "@ 10.33"  ← SOMA das 3 duplas, NÃO a odd
odd estrutural: 3,44446667   ·   odd REAL: 332,4112 ÷ 303 = 1,09706667
12ª coluna (Sistema): 3x Duplas
```

**#474418534 — aberta com odd turbinada**

```text
Data 16/08/2026 · Stake R$ 39,70 · Odd 17,661 · Resultado (vazio — em aberto)
card: "13.00@ 17.66"  ← a riscada só existe na tela; o payload traz a efetiva
finalFinancials.payout = 701,1417  ← POTENCIAL (settlement = null)
produto das pernas: 2,90 × 2,10 × 2,90 = 17,661 ✓
```

---

## Feedback para a camada global / MODELO

1. **`Bola na trave`** (futebol, 6 pernas na amostra) não tem categoria no `MASTER_APOSTAS §3`. É um objeto estatístico de jogo, irmão de `Chutes no Gol` e `Impedimentos`. Hoje cai em `Outros ⚠️`. **Avaliar categoria própria** — a casa oferece o mercado com frequência.
2. **`Total de cestas de três pontos marcadas` por time** (basquete) foi classificado em `Team Props` pelo princípio do objeto, mas o MASTER não tem sinônimo para "cestas de três". Registrar quando houver mais amostra.
3. **`1° Set Vencedor`** (vôlei) foi para `ML` por ser resultado de segmento, não contagem de sets — a nota do `§Pontos` cobre `Sets` como *unidade contada*, e vencedor de set não conta nada. Vale uma linha explícita no MASTER separando "vencedor de parcial" de "total de parciais".
4. **Imposto:** a Novibet expõe `settlement.withholdingTax` e `taxBonus` — é a **primeira casa nossa com imposto explícito no payload**. Veio 0 em 35 de 35, mas quando vier diferente de zero será preciso decidir de uma vez, no MASTER, se o `W` usa retorno **bruto ou líquido**. A mesma pergunta está aberta na `CASA_JONBET` (Feedback #2).

---

VERSÃO: 2026
ATUALIZADO: 2026-08-17 (sessão 271 — casa nova; captura por API com replay que alarga a janela)
