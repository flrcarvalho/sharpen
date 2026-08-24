# CASA_SPORTINGBET
## Camada de tradução — SportingBet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da SportingBet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> ⭐ **PRIMEIRA CASA DO MOTOR bwin / ENTAIN.** Não é Altenar, BetBy, BetConstruct, Kambi nem BlueBrown — não há espelho para reusar, e `spb_inject.js` nasceu próprio. Se outra casa Entain entrar (bwin, Betboo), este é o espelho pronto: procure `x-bwin-accessid` e `/cds-api/` no F12 **antes do login**, como se faz com Altenar e BetBy.

---

## 1. Identidade

- Casa canônica: `SportingBet` · site: `sportingbet.bet.br`
- ⚠ Grafia **MEDIDA no banco antes de registrar** (s289), não escolhida pela marca: `SportingBet` tinha **119 bilhetes / 5 contas / 4 donos** (Feca, Tonelada, Jonathan, LavaPessoal) contra **4 bilhetes / 1 conta** de `Sportingbet` (Diogo). A gêmea foi unificada na mesma sessão — sem isso, registrar a casa deixaria a grade do Diogo vazia sem erro nenhum (o bug da s249).
- O domínio dos favicons estava **errado** até a s289 (`sportingbet.com`, o site global). O correto é a operação regulada `sportingbet.bet.br`.
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `currency: "BRL"` em cada valor
- **Decimal exibido na tela: PONTO** (`2.50`, `R$50.00`) → normalizar para vírgula.
- Motor: **bwin / Entain**. Front Angular servido de `/ClientDist/`; catálogo em `/cds-api/`.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/spb_inject.js`).

```
POST https://www.sportingbet.bet.br/pt-br/sports/api/mybets/betslips
{"index":1,"maxItems":6,"typeFilter":"Open","pinnedBetslipIds":"","eventIds":[],
 "useGroupedView":false}
→ {"summary":{…},"betslips":[…],"typeFilter":"Open","errorLoadingBets":false}
```

Quatro consequências que mandam no desenho, todas **medidas** na conta em 24/08/2026:

1. **Não basta o cookie.** O endpoint exige headers próprios do motor — `x-xsrf-token`, `x-bwin-sports-api`, `sports-api-version`, `x-from-product`, `x-device-type`, `x-bwin-browser-url`. O replay reusa os headers exatos da requisição real.
   > ⚠️ **A falha não grita: um GET no mesmo path devolve o HTML da SPA com HTTP 200.** Por isso o `forward` do inject só aceita resposta com `betslips` como **array** — sem esse guarda, o autodiagnóstico contaria lixo como "endpoint respondendo" e diria que a conta está vazia.
2. **`index` é a PÁGINA, não offset.** Provado: `index:1,maxItems:5` e `index:2,maxItems:5` devolveram 10 ids distintos, sem repetição.
3. **Fim autoritativo = lista VAZIA.** Esta casa **não** manda `isLastPage`, `more` nem `hasNext` — `index:2,maxItems:50` voltou `betslips: []`. É o único sinal que ela dá.
4. **As abas são o `typeFilter` do corpo**, mesma URL: `Settled` · `Open`. A terceira aba da tela ("Ao Vivo") é recorte das abertas. O robô varre as duas a cada rodada, partindo de qualquer uma que o operador tenha aberto.

**Janela de datas: NÃO existe no corpo.** Diferente de Altenar e BetConstruct, esta API não aceita `dateFrom`/`dateTo` — o corte por dias é feito no `content.js`, pela colocação.

### 2.2 Tipo do bilhete declarado

- `slipType: "Combo"` (ou `bets.length ≥ 2`) → **Múltipla**;
- `slipType: "Single"` com 1 perna → **Simples**;
- `optionBetDetails.isBetBuilder` existe no payload, **sem amostra** na conta.

### 2.3 Layout do bilhete

Lista corrida, um card por bilhete, com `Valor` / `Cota` / `Ganhos` no rodapé, faixa de estado à direita (`Ganho` / `Derrota`) e um chevron que expande as pernas.

**⚠️ Não há linha em branco entre bilhetes** — medido: **6 bilhetes, 0 linhas em branco** no `innerText`. A casa nunca pode cair no robô de texto genérico (`roboScroll`), que parte por linha em branco: a lista viraria um bloco só e a IA perderia o resto **em silêncio** (lição da KTO, s192). O card colapsado ainda por cima não mostra o ID nem as pernas.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo (API) | Significado | Observação |
|---|---|---|
| `betSlipNumber` | **ID do bilhete** | alfanumérico de 10 (`20PGTUNX29`) · chave de dedup e do `[Código:]` |
| `state` | estado do bilhete | enum bruto — ver §5 |
| `conclusionDateUtc` | **colocação**, ISO UTC | ⚠️ **o nome mente** — ver §4 |
| `bets[].fixture.date` | início do evento, ISO UTC | a **mais recente** vira a coluna Data |
| `stake` / `stakePerBet` | **stake** | objeto `{currency,value}` · unidade normal (`50` = R$ 50,00), **não** há milésimos |
| `payout` / `grossPayout` | retorno **realizado** | `0` em aberta e em perdida |
| `maxPayout` / `grossPossibleWinnings` | retorno **potencial** | campo SEPARADO do realizado — ver §5 |
| `totalOdds.european` | **odd total, já boostada** | precisão completa |
| `bets[].optionBetDetails.priceBoostData.originalOdds.european` | odd **antes** do boost | é o riscado do card · nunca é a odd válida |
| `bets[].market.name` | mercado | ⚠️ vem o nome da PROMOÇÃO em bilhete turbinado — ver §6 |
| `bets[].option.name` | seleção | é aqui que mora a descrição real |
| `bets[].fixture.name` | confronto (`Botafogo - Cienciano`) | ⚠️ vem `"Quinta-feira"` nas Múltiplas Aumentadas |
| `bets[].sport.id` / `.name` | esporte | ⚠️ **usar o id**, nunca o nome — ver §12 |
| `bets[].competition.name` | competição | `Brasileiro Serie A`, `MLB` |
| `bets[].cancellationReason` | motivo da anulação | só em perna `Canceled` |
| `isFreeBet` | aposta grátis | 1 caso na amostra |
| `isEarlyPayout` / `earlyPayoutInformation` | cashout | **sem amostra** |
| `bestOddsGuaranteedInformation` | Best Odds Guaranteed | existe; **sem amostra acionada** |

---

## 3. ID do bilhete

- Formato: **alfanumérico de 10** (`20PGTUNX29`, `20NK1SSKST`), sempre presente no payload.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.
- A regex de cobertura do `repository.py` é a **genérica** (`_ID_MARCADOR_RE`): casa nova entra sem regex nova, e a conferência de cobertura já nasce ligada.

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da seleção mais recente** (`MASTER_OUTPUT §4`) — `bets[].fixture.date`.

> ⚠️ **`conclusionDateUtc` MENTE: é a COLOCAÇÃO, não a conclusão.** Prova medida, não deduzida: o bilhete `20PSJ4C9B6` tem `conclusionDateUtc: 2026-08-24T21:28Z` (18:28 de Brasília) e o jogo é às `23:00Z` — **uma conclusão não pode ser anterior ao próprio evento**. Confirmado também nos liquidados: no `20PGTUNX29` o campo dá 18/08 13:31, que é o rodapé do card, com o jogo em 20/08.

Fuso: todos os campos são **ISO com `Z` = UTC** → converter para America/Sao_Paulo. Sem converter, o bilhete pula de dia.

---

## 5. Status e Resultado

De-para do `state` do bilhete — confirmado contra a faixa do card:

| `state` | Leitura | Código |
|---|---|---|
| `Open` | Em aberto | *(vazio — não liquidar)* |
| `Won` | Ganhou — conferir o dinheiro | `W` |
| `Won` + retorno **igual** à stake | Devolvida / void | `V` |
| `Lost` | Perdeu (faixa `Derrota`) | `L` |
| `Canceled` | **Anulada** (`cancellationReason`) | `V` |
| outros | **sem amostra** — sobem crus, não liquidar automaticamente | — |

O `state` também existe **por perna**, com os mesmos valores. O combo `20NK1SSKST` tem `Lost/Lost/Won/Won/Lost/Canceled` — e é `L`, porque uma perna ganha não salva o bilhete.

> **O `Canceled` entrou no de-para no primeiro dia, de propósito.** Nenhum bilhete inteiro anulado apareceu ainda (só a perna do combo), mas a Esportiva mostrou na s285 o preço de deixar o enum de anulada sem tradução: a linha nasce "aguardando", nenhuma recaptura a resolve, e ninguém percebe porque não há erro.

> ⚠️ **A armadilha do potencial, e por que aqui ela é MENOR.** Em bilhete aberto o retorno potencial vem preenchido (`maxPayout` = `grossPossibleWinnings` = 1,29 = 0,43 × 3) — mas em campo **separado**: `payout` e `grossPayout` ficam em `0`. Diferente da VaideBet, onde `totalWin` servia às duas coisas e virou vitória fantasma em produção (s210). A regra: **`payout` só vale com `state: Won`; `maxPayout` nunca é retorno realizado.** O bloco emite `Retorno potencial:` nesse caso, nunca `Retorno:`.

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho. Na amostra os dois concordam: `20PGTUNX29` tem stake 50, `payout` 125 e odd 2,5 — e 125 ÷ 50 = 2,5 exato.

---

## 6. Boost / promoção

Marcado em `bets[].optionBetDetails.isPriceBoost: true`, com a odd anterior em `priceBoostData.originalOdds.european`. **O boost já está embutido em `totalOdds`** — é essa a odd válida; a original nunca vai para o TSV, só como `Marcação da casa: odd turbinada …`.

> ⚠️ **A armadilha mais cara da casa: o nome da promoção chega em `market.name`.**
>
> Bilhete turbinado vem com `market.name` = **`"BIG ODD"`** ou **`"Múltiplas Aumentadas"`** — que não são mercado, são o nome da campanha. O mercado real só existe em `option.name` (*"Kevin Viveros tem 2 ou mais chutes no gol"*). Copiar `market.name` jogaria **todo bilhete turbinado em `Outros`** — e turbinada aqui é o padrão, não a exceção.
>
> O bloco por isso **não emite `Mercado:`** quando o nome está em `_PROMO_SPB`; emite `Marcação da casa: promoção «…»` e deixa a categoria sair da descrição da seleção. Travado no harness.

**"Múltiplas Aumentadas" é uma múltipla disfarçada de simples.** O `20PGHDRPX3` tem `slipType: "Single"`, **uma** perna, `fixture.name: "Quinta-feira"` (não é confronto, e o `compoundId` começa com `1:` em vez de `2:`) — e os três jogos existem só dentro de `option.name`: *"Besiktas, RB Salzburg e Universitatea Craiova vencem"*. Pelo `MASTER_APOSTAS`, três seleções de jogos diferentes é **Múltipla**; o payload não dá como separá-las, então a descrição preserva a frase inteira.

---

## 7. Cashout

Os campos existem (`isEarlyPayout`, `isDelayedForEarlyPayout`, `earlyPayoutInformation.autoCashoutTriggered`) e vieram `false`/`0` em **100% da amostra**. Quando aparecer, vale a regra global: cashout **=** stake → `V`; **≠** stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

<!-- TODO: capturar um bilhete com cashout real, ver em que `state` ele cai e travar no harness. -->

---

## 8. Bônus

`isFreeBet: true` no `20P828C463` (R$ 20 @ 10,5). O bloco emite `Marcação da casa: aposta grátis (freebet) — o stake não saiu do saldo`.

Existe também `promoTokens`, `edsPromoTokens`, `signPostingRewards`, `signPostings` e `isEditBet` (Edit Bet) — todos vazios/`false` na amostra.

---

## 9. Mapa de mercados (SportingBet → `Aposta` global)

Só mercados **confirmados nesta conta** (camada fina — o que a casa nunca mostrou não entra):

| SportingBet exibe (`market.name`) | Aposta global |
|---|---|
| `Marcador a qualquer momento` | Anytime |
| `Total de Cartões - 1º Tempo` | Cartões |
| `<Time> - Total de Escanteios` · `<Time> - Total de Escanteios - 2º tempo` | Escanteios |
| `<Jogador> - Corridas` | Corridas |
| `<Jogador> - Player singles` | Player Props |

**As duas entradas que NÃO são mercado** ficam fora da tabela de propósito — elas não têm
categoria global, porque não são categoria nenhuma:

- **`BIG ODD`** — campanha de odd turbinada. A categoria sai da seleção:
  `Vasco to qualify` · `Kevin Viveros tem 2 ou mais chutes no gol`.
- **`Múltiplas Aumentadas`** — campanha de múltipla pronta. A categoria sai da seleção:
  `Besiktas, RB Salzburg e Universitatea Craiova vencem`.

> `<Jogador> - Corridas` vai para **`Corridas`** e não para `Player Props` pelo mesmo
> princípio que manda cartão de jogador para `Cartões`: **objeto com categoria própria vence
> a entidade** (`MASTER_APOSTAS §Player Props`). Já `Player singles` (rebatidas simples no
> beisebol) **não tem** categoria própria no MASTER — por isso cai em `Player Props`.

> Amostra pequena e enviesada: 27 bilhetes, só futebol e beisebol, com 5 dos 6 bilhetes do
> harness em promoção. O §9 cresce quando a casa mostrar mais.

---

## 10. Stake

`stake.value` em **unidade normal** (`50` = R$ 50,00) — não há milésimos. `stakePerBet` é igual em aposta simples; em sistema (sem amostra) seria o valor por linha.

---

## 11. Odds

`totalOdds.european`, precisão completa, **já boostada**. Formato europeu declarado em `oddsFormat` — se um dia vier `Fractional`/`American`, o bloco tem de recusar em vez de converter às cegas (`MASTER_RESULTADO`: odd é sempre decimal).

No `W` a régua global (`retorno ÷ stake`) manda; na amostra ela concorda com a declarada ao centavo.

---

## 12. Ruído a ignorar

- `oddsChangeAcceptanceMode`, `isBanker`, `isVirtual`, `isStartingPrice`, `xCastSettlementDeviated`, `positionInBet`, `businessContext`, `pick`/`picks` (duplicam `option.name`).
- `type` / `typeAsName` (`"Simples"` / `"Single bet"`) — redundantes com `slipType`.

> ⚠️ **`sport.name` é ruído PERIGOSO, não ruído inofensivo.** A casa escreve **`"Beisebol"`** (id 23), que o `MASTER_ESPORTES` lista como **sinônimo de entrada** — o valor oficial é **`Baseball`**. A IA copia o rótulo verbatim, então o formatador mapeia por **id** (`4 = Futebol`, `23 = Baseball`) e nunca copia o nome. Foi assim que a VaideBet gravou duas grafias do mesmo esporte no banco (s210). O harness trava isso com a perna de MLB do combo — o único bilhete da conta em que o mapa e o nome da casa divergem.

---

## 13. Pegadinhas (resumo rápido)

- **`conclusionDateUtc` é a colocação**, apesar do nome (§4).
- **`market.name` traz o nome da PROMOÇÃO** em bilhete turbinado (§6).
- **`sport.name` traz sinônimo, não o valor oficial** (§12).
- **GET no endpoint devolve HTML com HTTP 200** — falha silenciosa (§2.1).
- **Fim = lista vazia**; não há `isLastPage` (§2.1).
- **`index` é página, não offset** (§2.1).
- Retorno potencial mora em `maxPayout`, separado do `payout` (§5).
- A lista **não** tem linha em branco entre bilhetes → texto/DOM está proibido (§2.3).
- Sem filtro de data na API → o corte por dias é do `content.js` (§2.1).

---

## 14. Validações específicas

- Copiar a linha `Data (evento mais recente):` **literalmente**, nunca inferir da vizinhança (a IA arrastou data de vizinho na VaideBet, s210).
- Conferir que nenhum bilhete `Open` recebeu código de resultado.
- Conferir que o rótulo de esporte é o **oficial** do MASTER.
- Em bilhete de promoção, conferir que a categoria saiu da **seleção**, não do rótulo da campanha.

---

## 15. Exemplos golden (bilhetes reais)

Fixtures: `extensor/harness/fixtures/sportingbet.settled.json` (5 bilhetes) e
`sportingbet.open.json` (1). Caso: `extensor/harness/casos/sportingbet.mjs`.

| ID | Estado | Stake | Odd | Retorno | O que prova |
|---|---|---|---|---|---|
| `20PGTUNX29` | Won | 50,00 | 2,5 | 125,00 | régua do W ao centavo + boost 1,98 → 2,5 |
| `20NK1SSKST` | Lost | 25,00 | 133,03 | — | múltipla de 6 pernas, uma `Canceled` |
| `20PL2W0FBK` | Lost | 127,00 | 3,4 | — | boost 3,0 → 3,4 |
| `20PGHDRPX3` | Lost | 28,00 | 3,2 | — | "Múltiplas Aumentadas" (promo ≠ mercado) |
| `20P828C463` | Lost | 20,00 | 10,5 | — | freebet |
| `20PSJ4C9B6` | Open | 0,43 | 3 | potencial 1,29 | aberta não liquida; potencial em campo próprio |

---

## Feedback para a camada global / MODELO

- **"Nome de campo é hipótese, não fato."** `conclusionDateUtc` guardando a colocação é o terceiro caso do gênero (depois de `totalWin` da VaideBet e `bet_total_stake` da Stake). O `CASA_MODELO` poderia pedir, em toda casa nova, que **cada campo de data seja cruzado com um bilhete cujo evento ainda não aconteceu** — é o teste que desmascara os três.
- **Mercado promocional é padrão de mercado, não exceção desta casa.** Vale checar se Betano/Superbet fazem o mesmo com "Odds Turbinadas" — se fizerem, a regra sobe para o `MASTER_APOSTAS`.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA (harness verde · 6 bilhetes reais + 3 controles negativos, com dente provado por mutação) · mapa de mercados §9 **parcial** (27 bilhetes, só futebol e beisebol) · ⚠️ **NÃO validada ao vivo** (nenhum lote extraído pela IA ainda) · sem amostra de cashout, Edit Bet, bet builder e bilhete inteiro anulado
