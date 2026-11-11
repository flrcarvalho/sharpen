# CASA_3ET
## Camada de tradução — 3et → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da 3et.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `3et` · site: `www.3et.com` · apostas em **My Bets** (abas Open Bets e
  Statement).
- Locale: a interface está em inglês, e **esporte, mercado, seleção, times e ligas vêm em
  INGLÊS** (`American Football`, `Team Points UNLV Rebels`, `UNDER 22.5`, `NCAA Division I FBS`).
- Moeda: a da conta, lida de `/accounts/v3/loggedIn` → `currencyCode`. A conta do recon é
  **USD**. O bilhete não diz a moeda.
- Dinheiro e odd em número decimal, **sem milésimos**; o dinheiro pode ter **3 casas**
  (`profit` 127.908).
- Plataforma **PRÓPRIA**: front React, API no mesmo domínio (`/betting/v3/eurasian/…`,
  `/accounts/v3/…`). Nenhuma outra casa do sistema usa essa API. Família `et` (inject
  `et_inject.js`). A casa também tem **exchange** (`isExchange`), que fica **fora** da captura
  por enquanto (decisão do Feca, 08/11/2026).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s441):** `3et`, a da marca (minúscula, como no logo). Medido em 08/11/2026 em
> `parceiros`, `bilhetes`, `casas_meta` e `correcoes`: a base não tinha a casa em grafia nenhuma.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/et_inject.js`).

```
GET https://www.3et.com/betting/v3/eurasian/statement/reports/betsByDate?page=N&size=200&after=0&before=<epoch s>
GET https://www.3et.com/betting/v3/eurasian/reports/bets/current/normal?filter=&page=N&size=200
    (cookie da sessão; nenhum header de token)
→ { "content":[…], "number":N, "size":200, "totalElements":T, "totalPages":P, "last":true, … }
```

Medido com a sessão do Feca (07-08/11/2026):

- **Auth é só o COOKIE.** `fetch` com `credentials:"include"` e nenhum header extra devolve
  200. O replay arranca a frio, com ou sem a página ter pedido algo.
- **A tela de extrato pede um DIA por clique** (`betsByDate?after=<dia>&before=<dia>`) e a de
  abertas pede 50 por página. O replay pede `after=0` (a conta inteira: medido igual a 3 e 10
  anos) e 200 por página. A janela filtra pela **colocação**.
- **`size` acima de 200 volta 200.** Paginação por índice (`page`); **fim = `last:true`**
  (medido com size 5 e 2: páginas exatas, sem bilhete repetido).
- A tela "Statement" sem clique (`statement/reports/bets`) só traz **totais por dia**: não serve.
- Outras rotas no bundle, fora da captura: `statement/reports/betsByLeague|betsByEvent`,
  `exchangeMarketsByDate`, `mobile/reports/bets/settled`, `cashier/…/fundings`.

### 2.3 Layout do bilhete (card)

Tabela por bilhete (`PLACED / SETTLED / BET TYPE / SELECTION / ODDS / STAKE / PAYOUT /
STATUS`), uma linha por perna com esporte, mercado, período, liga, jogo e seleção. Não há
prova de linha em branco entre bilhetes no `innerText`: **texto por DOM não serve; por isso API.**

---

## 2.5 Campos da API (o que o inject entrega)

A **liquidada vem PLANA**; a **aberta vem EMBRULHADA** em `{bet:{…}, betType, translatedBetType}`.

| Campo | Confirmado na 3et |
|---|---|
| `betId` | numérico, **8 dígitos** (`51776597`). É o código. As pernas têm `betId` de outra série (64M), que **não** é código |
| `status` | aberta: `"Open"`. Liquidada: `{result:"Win"\|"Lose"}` |
| `betStatus` | `"paid"` nas liquidadas |
| `betType` / `submittedType` | `Multiplier` / `MULTIPLIER`; `multiplierName` = `Double` (dupla) |
| `stake` · `trueStake` · `showTrueStake` | stake; `trueStake` igual à stake em toda a amostra |
| `freeBetStake` | `0` em toda a amostra (§8) |
| `odds` | odd do bilhete, a do card (9,175; 6,814). **Não** é o produto das pernas (6,815 na ganha) |
| `profit` · `payout` | ⚠ **LUCRO**, não retorno: `-25` na perdida, `127.908` na ganha de 22 @ 6,814. Retorno = `stake + profit` |
| `potentialProfit` | lucro potencial (o "Est. Return" da tela também é LUCRO) |
| `datePlaced` · `dateSettled` | colocação e liquidação, ISO UTC (`…Z`). **Não há início de evento** |
| `isExchange` | `false` (só nas abertas). `true` = aposta da exchange, fora da captura |
| `legs[]` | pernas: `sportName`, `competition`, `eventName`, `marketName`, `runnerName`, `periodName`, `odds`, `status` |
| `legs[].status` | liquidada: `{result, finalScore, periodScore}` (`Push` = perna anulada, DNB empatado); aberta: texto de andamento `finished`/`graded`, que **não** diz ganha nem perdida |

**⚠ SIMPLES não tem `legs` (s443, conta do Gabriel).** Sem isso o bloco ia com `Seleções:` vazio,
a IA devolvia `Mercado Especial - REVISAR` ou nenhuma linha ("Nenhuma linha válida encontrada no
TSV") e a Ficha recusava (`bilhete sem legs`). A seleção vem solta no bilhete, em dois formatos
(medidos no mesmo `51851882`, aberto e depois liquidado):

| Campo da perna | Simples liquidada (plana) | Simples aberta (embrulhada) |
|---|---|---|
| jogo | `selection.event` | `bet.eventName` |
| liga | `selection.competition` | **`competition` do EMBRULHO** (fora do `bet`) |
| esporte · período | `betType.sport` · `betType.period` | `bet.sportName` · `bet.periodName` |
| mercado | `marketName` (= `betType.marketType`) | `bet.marketName` |
| seleção | `runnerName` (`Over 5.5`) | `bet.runnerName` (`Total Touchdowns  (Over 5.5)`: repete o mercado) |
| `betType` | objeto `{betType:"Bet", sport, …}` | texto `"Betting"` no embrulho, `"Bet"` no `bet` |

O inject monta UMA perna com esses campos (`pernaSimples`); a Ficha faz o mesmo e tira da seleção
da aberta o mercado repetido, para ela dizer o que a liquidada diz. O `eventStartDate` do embrulho
da aberta **não** vira data: a liquidada não o traz, e a data da aposta mudaria ao liquidar (§4).

**Ficha (s441):** adaptador `app/adaptadores/et.py`, gate `tests/test_adaptador_et.py`. O cru é o
item da lista como a casa devolveu, mais `moeda_conta` (anexado pelo inject). O jogo `A at B`
vai à Ficha como `A vs B`, na ordem da casa, para o dicionário trocar o time do mercado
(`Team Points UNLV Rebels`) por `{time}`.

---

## 3. ID do bilhete

- `betId` do bilhete, numérico de 8 dígitos. Dedup forte por ID. Vai para a 11ª coluna interna
  (`Código`).

---

## 4. Data

**A API não publica o início do evento.** A coluna Data é a **colocação** (`datePlaced`), de
UTC para São Paulo, como na Novibet. A conversão cruza a meia-noite: `51758258` foi colocada
às 00:06 UTC de 07/11, que é **06/11 21:06** em São Paulo; carimbo `20261106210616`.

> A liquidação (`dateSettled`) não entra no bloco: data derivada de outro instante que não o
> da aposta seria estimativa.

---

## 5. Status e Resultado

O retorno é `stake + profit`. Na ganha da amostra ele fecha exato com stake × odd do card
(22 × 6,814 = 149,908); `W` exige fechar com **tolerância de 1 centavo**.

| `status` · dinheiro | Leitura | Código |
|---|---|---|
| `Open` (aberta) | Em aberto | *(vazio — não liquidar)* |
| `Lose` · `profit` = −stake | Perdeu | `L` |
| qualquer · `profit` = 0 (retorno = stake) | P/L zero | `V` |
| `Win` · stake + profit = stake × odd (± 1 centavo) | Ganhou | `W` |
| `Lose` com retorno, `Win` que não fecha, `freeBetStake` > 0, `trueStake` ≠ stake, rótulo novo no bilhete (`Half Win`, `Push`…) | sobe cru | *(a conferir)* |

Medido: `Lose` 12 e `Win` 1 nas liquidadas, `Open` 4. O resto é a régua acima, travada por
clone no harness, **não** por amostra real. O bloco sempre leva
`Status (API): result=… · betStatus=… · betType=… (Double) · betId=…`.

A perna liquidada diz o próprio resultado (`[perna ganha]` / `[perna perdida]` /
`[perna anulada (push)]`; o Push foi medido no `52019175`, s443). O bilhete continua decidido
pelo dinheiro. A perna da
aberta leva só `Estado da perna (casa): finished|graded`, sem marcar resultado.

---

## 6. Boost / promoção

Nenhum campo de boost na amostra. Se aparecer, vale a regra global do `W` (`retorno ÷ stake`)
e o bilhete sobe "a conferir" até ser medido.

---

## 7. Cashout

Nenhum campo de cashout na amostra. Sem amostra: só retorno = stake vira `V`; o resto sobe
"a conferir". A regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`) vale quando for medido.

---

## 8. Bônus

`freeBetStake` = 0 em toda a amostra. Se vier maior que zero, o bloco escreve
`Freebet (cru da casa): freeBetStake X` e o bilhete fica "a conferir" (e a Ficha recusa): ainda
não se sabe se o `profit` já desconta a freebet.

---

## 9. Mapa de mercados (3et → `Aposta` global)

Só os mercados **confirmados** no dado real, e só onde a tradução é direta (camada fina):

| 3et exibe (mercado) | Aposta global |
|---|---|
| `1x2` | ML |
| `Moneyline`, `Moneyline First Half` | ML |
| `AH` (futebol), `HDP` (basquete) | Handicap |
| `Draw no bet` | DNB |

> `Team Points <time>`, `Team Goals <time>` e `Corner Total` também aparecem na amostra: a
> categoria sai do `MASTER_APOSTAS` pelo objeto medido, sem atalho aqui. O período
> (`periodName`) diz o tempo do mercado; `Full Time` é o jogo inteiro. A descrição segue o
> `MASTER_DESCRICAO` em pt-BR, com o confronto em ` v ` (a casa escreve `A at B` no esporte
> americano e `A vs B` no resto).

---

## 10. Stake

Campo `stake`, na moeda da conta; a conversão para R$ é do `/salvar`.

---

## 11. Odds

- **A odd do bilhete é `odds`**, a mesma do card. Na múltipla ela **não** é o produto das
  pernas (a casa trunca: 6,814 contra 6,815).
- **W:** a odd do card, que fecha o retorno.
- **L e aberta:** `odds`. Na perdida ela **não** zera.
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `eventId`, `marketId`, `runnerId`, `sportId`, `clickablePositionMatrix`, `liveBet`,
  `isUSPlayerProp`, `showHomePlayerAsFirst`, `translatedSportName`, `oddsType`.
- `periodScore` (o placar do período; o `finalScore` já sobe).
- Totais da página (`stakeTotal`, `payoutTotal`, `totalStake`…).

---

## 13. Pegadinhas (resumo rápido)

1. **`profit`/`payout` e o "Est. Return" da tela são LUCRO**, não retorno (§2.5).
2. **Aberta embrulhada, liquidada plana** (§2.5). **Simples sem `legs`**, com a seleção solta e a
   liga da aberta no embrulho (§2.5, s443).
3. **Sem data de evento**: a Data é a colocação (§4).
4. **Odd do bilhete ≠ produto das pernas** (§11).
5. **Moeda fora do bilhete**: vem da conta (§1).
6. **Exchange fora da captura** (§1).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada na moeda da casa (**USD** na conta do recon) antes da 1ª captura.
- [ ] Nenhuma aberta liquidada; nenhuma perdida com odd zero.
- [ ] Coluna Data = colocação em São Paulo.
- [ ] Contagem capturada == Open Bets + liquidadas do Statement.
- [x] **1ª simples e 1º Push** (s443, conta do Gabriel): fixtures `3et.simples.settled.json` e
      `3et.simples.open.json`, travadas em `simplesReais` (harness) e no `test_adaptador_et.py`.
- [ ] **1ª anulada / meia / cashout / freebet:** salvar o JSON como fixture e trocar o clone do
      harness.
- [ ] **1ª aposta da exchange:** medir onde ela aparece (fora de `betsByDate`?) antes de ligar.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 07-08/11/2026 — conta inteira (**17 bilhetes**: 13 liquidadas, 4 abertas, todas
duplas): `extensor/harness/fixtures/3et.settled.json` e `3et.open.json`.

| Código | Tipo | Estado | Stake (USD) | Odd | Retorno (USD) | Colocação (SP) | Fonte |
|---|---|---|---|---|---|---|---|
| 51776597 | Dupla futebol + futebol americano | `Win` | 22,00 | 6,814 | 149,908 | 07/11/2026 08:45 | card |
| 51835571 | Dupla futebol americano | `Lose` | 25,00 | 9,175 | 0 | 07/11/2026 14:28 | card |
| 51831830 | Dupla (1 perna ganha) | `Lose` | 30,00 | 5,642 | 0 | 07/11/2026 14:07 | JSON |
| 51758258 | Dupla futebol americano | `Lose` | 20,00 | 11,062 | 0 | 06/11/2026 21:06 | JSON |
| 51867098 | Dupla futebol americano | `Open` | 20,00 | 9,765 | potencial 195,30 | 07/11/2026 18:35 | card |

**Simples e Push (s443, conta do Gabriel, 10-11/11/2026):** `3et.simples.settled.json` (4 simples
liquidadas + a dupla com Push) e `3et.simples.open.json` (2 simples abertas).

| Código | Tipo | Estado | Stake (USD) | Odd | Retorno (USD) | Colocação (SP) |
|---|---|---|---|---|---|---|
| 51663167 | Simples NFL, `Team Points` | `Win` | 25,00 | 3,25 | 81,25 | 05/11/2026 10:36 |
| 51666575 | Simples basquete, prop de jogador | `Lose` | 36,00 | 1,94 | 0 | 05/11/2026 14:07 |
| 51851882 | Simples NFL, `Total Touchdowns` (aberta e liquidada) | `Lose` | 50,00 | 2,19 | 0 | 07/11/2026 16:05 |
| 52022943 | Simples NCAA, `Team Points` | `Win` | 36,00 | 3,90 | 140,40 | 10/11/2026 20:49 |
| 52028388 | Simples NBA, `HDP` | `Open` | 2,00 | 1,96 | potencial 3,92 | 11/11/2026 07:50 |
| 52019175 | Dupla com perna `Push` (DNB) | `Lose` | 24,00 | 11,798 | 0 | 10/11/2026 15:14 |

**Sem amostra:** simples anulada · meia · cashout · freebet · boost · sistema · exchange.

---

## 16. Roteiro da 1ª captura

1. Cadastrar a conta na moeda da casa (USD).
2. Atualizar a extensão (**SharpenUp 0.7.72**) e dar **Ctrl+Shift+R** na aba da 3et **e** na
   aba do painel.
3. Estar logado na 3et (qualquer página: o inject parte do cookie).
4. Conectar → Copiar bilhetes. O toast diz `respostas` e `vistos`; HTTP 401/403 = sessão caída.
5. Conferir no dashboard: contagem, código, colocação, odd e moeda.
6. Na 1ª anulada/meia/cashout/freebet, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

1. **Campo `payout` que é lucro.** O nome engana; toda casa nova precisa conferir `payout`
   contra stake × odd na ganha antes de usar.
2. **Casa sem data de evento.** Segunda depois da Novibet; a Data cai na colocação.
