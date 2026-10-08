# CASA_SHUFFLE
## Camada de tradução — Shuffle → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Shuffle.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Shuffle` · site: `shuffle.com` · esportes em `/pt/sports`
- Locale: `pt` na API, mas o texto dos mercados é **pt-PT** (`equipas`, `Hipótese dupla`,
  `Grande Prémio`). Moeda: a da **conta** (`currency: "USDT"` na amostra); o card escreve
  `US$` e a casa exibe `1 USDT = US$ 1,00`.
- **Dinheiro e odd em STRING decimal com ponto** (`"54.996"`, `"14.93856"`), sem milésimos.
- Plataforma **PRÓPRIA**, a 1ª casa **GraphQL** do SharpenUp. App Next.js, API no host da
  casa (`/main-api/graphql/…`). As odds vêm da Betradar (`provider: "BETRADAR"`), mas isso é o
  feed, não o motor de apostas. Não é espelho de ninguém.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s401):** `Shuffle`, a da marca. Medido em 08/10/2026: nenhuma ocorrência em
> `parceiros`, `bilhetes`, `casas_meta`, `casa_config`, `correcoes`, `uso_tokens` nem
> `tipsters.casas`.

### 1.1 A moeda é da conta

Cadastre a conta **na moeda da carteira usada na casa** (USDT na amostra). O `/salvar` converte
para R$ pela cotação do dia da aposta ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).
O bloco leva `Moeda: USDT`, `Carimbo de colocação:` (dia da cotação) e o dinheiro rotulado na
moeda. **Os números do TSV são os da casa**; quem converte é o servidor.

> A casa aceita várias criptomoedas. Dinheiro com mais de 2 casas sai com **todas** no bloco
> (`0,00123` em BTC, `54,996` em USDT): arredondar a 2 casas mudaria o retorno lido pelo gate.

### 1.2 Esporte: a API manda um enum

| `sports` | Esporte canônico |
|---|---|
| `SOCCER` | Futebol |
| `TENNIS` | Tênis |
| `BASKETBALL` | Basquete |
| `BASEBALL` | Baseball |
| `BADMINTON` | Badminton |
| `F1` | F1 |

Só os enums vistos na amostra. Enum novo: traduzir pelo `MASTER_ESPORTES`, nunca verbatim.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/shf_inject.js`).

```
POST https://shuffle.com/main-api/graphql/sports-main/graphql-sports-main
     content-type: application/json · authorization: Bearer <sessão>
     { "operationName": "GetSportsBets",
       "query": "query GetSportsBets(…) { sportsBets: sportsBetsV3(…) }",
       "variables": { "language": "pt", "first": 20, "skip": 0, "cursor": "<ISO>" } }
→ { "data": { "sportsBets": { "nodes": [ … ], "nextCursor": "<ISO>" | null } } }
```

- **A query não escolhe campos:** `sportsBetsV3` devolve o bilhete inteiro como JSON.
- **Auth por header.** Só cookie volta `200` com `errors: UNAUTHENTICATED`. Bastam
  `content-type` + `authorization`; o `x-correlation-id` não é exigido (medido).
- **O token é o mesmo em outras chamadas GraphQL autenticadas** da página (`sports/graphql-sports`,
  `api/graphql` · `ActiveTournaments`), então o inject arranca de qualquer tela de esportes.
- **A tela é estreita:** pede `first: 9` com o filtro de uma aba (`["PENDING"]` ou
  `["WON","CANCELLED","LOST","CASHED_OUT","VOIDED","PARTIAL"]`). O replay pede **sem
  `statuses`**: abertas e liquidadas juntas (31 de 31 na conta, 8 + 23).
- **Paginação por cursor de data:** `nextCursor` é o `createdAt` do 1º bilhete da página
  seguinte, e ela começa nele (inclusivo). Fim autoritativo: `nextCursor: null`. `first` tem
  teto **20** (21 → erro `first must not be greater than 20`). Provado com `first` 2 e 3: 23
  lidos / 23 únicos.
- Painel: **Esportes → Minhas Apostas**, seletor `Apostas pendentes` / `Apostas encerradas`,
  9 cards por página.

### 2.2 ⚠️ A OUTRA lista — nunca usar

O rodapé de esportes mostra `Últimas Apostas` e `Grandes apostadores`: **apostas de outros
usuários**. O inject só consome resposta cuja requisição foi `GetSportsBets` e descarta todo
nó com `user` preenchido (nos da própria conta é `null`, 31 de 31).

### 2.3 Layout do bilhete (card)

Cabeçalho com o jogo (simples), `2 Standard Multi` / `3 Standard Multi` (múltipla) ou
`Aposta de sistema` + `Duplos`; selo `VITÓRIA` / `PERDAS`; `Total De Probabilidades` com a odd
**arredondada a 2 casas**; `Sua Aposta US$ …`; `Você Ganhou` / `Sem Retorno`. Em sistema:
`Tipo De Aposta · 3 Apostas · US$ 20,00` (valor por linha). Nas pernas de múltipla, `ganhou` /
`perdeu`; a perna anulada fica **sem rótulo**. O card **não mostra o id** do bilhete.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Shuffle |
|---|---|
| `id` | nanoid de 21 (`Cfn16FgUcNikYecjCrA4j`) — chave de dedup e `[Código:]` |
| `currency` | moeda da conta (`USDT`) |
| `amount` | stake **TOTAL** (em sistema, soma das linhas) |
| `originalAmount` | `null` em toda a amostra (sobe cru se vier) |
| `totalOddsDecimal` | odd da **colocação**; **não muda** com perna anulada; em sistema já é a **média** das linhas |
| `actualOddsDecimal` | odd **liquidada** (= colocação enquanto aberta) |
| `status` | `PENDING` · `WON` · `LOST` (vistos) · `CANCELLED` · `CASHED_OUT` · `VOIDED` · `PARTIAL` (só no filtro da página) |
| `type` | `REGULAR` · `SYSTEM_BET` |
| `systemBetType` | `DOUBLES` (visto) · `null` fora de sistema |
| `createdAt` | colocação, ISO **UTC** |
| `settlement` | `null` na aberta; `{ payoutOddsDecimal, payout, createdAt }` na liquidada |
| `settlement.payout` | retorno REAL (0 na perdida) |
| `cashoutOddsDecimal` | **oferta** de cashout da aberta — não é retorno; o inject ignora |
| `legs[].oddsDecimal` | odd **apostada** da perna |
| `legs[].displayStatus` | `PENDING` · `WON` · `LOST` · `PUSHED` |
| `legs[].selections[].oddsNumerator/Denominator` | a mesma odd em **fracionário** (128/100 = 2,28) |
| `legs[].selections[].marketSelection.odds*` | ⚠️ odd **ATUAL** do mercado — nunca usar |
| `…selections[].fixture.name` · `startTime` | confronto e início (ISO **UTC**) |
| `…selections[].market.name` · `lineValue` | mercado (pt-PT) e linha |
| `…selections[].marketSelection.formattedName` | seleção (`Mais de 2.5`) |
| `…selections[].competition.name` | liga |
| `…selections[].unboostedOddsDecimal` | `null` em toda a amostra (boost) |
| `user` | `null` nos bilhetes da conta; preenchido = bilhete alheio (§2.2) |

---

## 3. ID do bilhete

- **nanoid de 21 caracteres** (alfanumérico, pode ter `_` e `-`). O card **não** estampa o id.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`).

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente), `startTime` em **UTC** convertido para
São Paulo. A diferença muda o dia: perna às 02:00Z de 08/10 é 23:00 de 07/10. A colocação
(`createdAt`) sai em São Paulo no bloco e no carimbo de colocação.

---

## 5. Status e Resultado

| `status` · dinheiro | Leitura | Código |
|---|---|---|
| `PENDING` | Em aberto | *(vazio — não liquidar)* |
| `LOST` · retorno 0 | Perdeu | `L` |
| `WON` · retorno > 0 e ≠ stake | Ganhou — odd = retorno ÷ stake | `W` |
| `WON` · retorno = stake | P/L zero | `V` |
| `VOIDED` / `CANCELLED` · retorno = stake | Anulada | `V` |
| `CASHED_OUT` | regra global do cashout (`MASTER_RESULTADO §5.1.2` e `§5.6`) | `V` ou `W` |
| `PARTIAL`, enum novo, ou rótulo que o dinheiro desmente | sobe cru | *(a conferir)* |

Medido: `PENDING` 8 · `WON` 11 · `LOST` 12 em 31.

> ⚠️ **`WON` não quer dizer lucro.** Sistema `Duplos` com uma perna perdida e outra anulada
> pagou **54,996 sobre 60** e o card diz `VITÓRIA`. É `W` com odd 0,9166 e P/L negativo — a
> regra global do retorno, não um erro da casa.

> **Perna `PUSHED`** é perna anulada: paga 1 na conta do bilhete. O card a deixa sem rótulo.

---

## 6. Boost / promoção

`unboostedOddsDecimal` = `null` em toda a amostra. Se vier preenchido, o bloco marca a perna
como `odd turbinada pela casa` e vale a regra global do `W` (`retorno ÷ stake`).

---

## 7. Cashout

O bilhete aberto traz `cashoutOddsDecimal` (a **oferta**, ex.: 0,8669) — não é retorno, o
inject ignora. Nenhum cashout executado na amostra; quando houver (`CASHED_OUT`), vale a regra
global (`MASTER_RESULTADO §5.1.2` e `§5.6`): retorno = stake → `V`; ≠ stake → `W` com
`odd = retorno ÷ stake`.

---

## 8. Bônus

Nenhum campo de bônus/freebet na amostra. `originalAmount` (sempre `null`) sobe cru no bloco
se vier diferente da stake.

---

## 9. Mapa de mercados (Shuffle → `Aposta` global)

Só os mercados **confirmados** no dado real, e só onde a tradução é direta (camada fina):

| Shuffle exibe | Aposta global |
|---|---|
| `Vencedor` · `1x2` | ML |
| `Handicap` · `Handicap (incluindo prolongamento)` | Handicap |
| `Hipótese dupla` | Dupla Chance |
| `Qual equipa para marcar` → `Ambas as equipas` | Ambas Marcam |
| `Total` (futebol) · `<time> total` | Gols |
| `<time> cartões exatos` | Cartões |
| `Total sets` | Sets |
| `Total jogos` (tênis) | Games |
| `Total pontos` (badminton) | Pontos |
| `Total hits (incluíndo extra innings)` · `… - Top 3` (F1) | seguir o nome → MASTER_APOSTAS |

> `(incluindo prolongamento)` é **recorte**, não mercado novo. O texto vem em pt-PT
> (`equipas`, `Hipótese`); a descrição segue o `MASTER_DESCRICAO` em pt-BR.

---

## 10. Stake

Campo `amount`, **TOTAL** do bilhete (em sistema, `linhas × valor por linha`: 60 = 3 × 20).
Na moeda da conta; a conversão para R$ é do `/salvar`.

---

## 11. Odds

- **W:** `retorno ÷ stake`, precisão total. Com perna anulada isso dá 5,1192, não os 11,5182
  da colocação que o card estampa.
- **L e aberta:** `totalOddsDecimal`. Em sistema ele **já é a média** das linhas
  (`MASTER_RESULTADO §7.3`): 2,28·2,34 + 2,28·2,8 + 2,34·2,8 = 18,2712 ÷ 3 = 6,0904.
- **Nunca** a odd do `marketSelection` (odd atual do mercado, §2.5).
- Odd **nunca** truncada (o card arredonda a 2 casas); decimal com vírgula.

---

## 12. Ruído a ignorar

- `cashoutOddsDecimal` / `cashoutInfo` / `cashoutAvailable` — oferta de cashout (§7).
- `SportsBetsCount`, `GetSportsStreamAndWidgetByFixturesIds`, `GetAppBootstrapData`,
  `GetGlobalUnauthData` — contagem, stream e dados da casca.
- `Últimas Apostas` / `Grandes apostadores` — apostas de outros usuários (§2.2).
- `matchState`, `streamExists`, `competitors[].iconPath`, `bannerType`.

---

## 13. Pegadinhas (resumo rápido)

1. **Três odds na mesma seleção** — só a da perna (`oddsDecimal`) é a apostada (§2.5, §11).
2. **`WON` com prejuízo** — sistema pagou 54,996 sobre 60 (§5).
3. **Odd da colocação não muda com perna anulada** — no W manda o dinheiro (§11).
4. **Sistema: stake TOTAL e odd MÉDIA** já prontas (§10, §11).
5. **Apostas de outros usuários na mesma página** (§2.2).
6. **Dinheiro de cripto com 3+ casas** — nunca arredondar (§1.1).
7. **`startTime` em UTC** (§4).
8. **pt-PT nos mercados** (§9).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada na moeda da carteira (USDT) **antes** da 1ª captura.
- [ ] Nenhum `W` com a odd da colocação quando há perna `PUSHED`.
- [ ] O sistema de 54,996 sobre 60 sai `W` @ 0,9166 (P/L −5,004), nunca `L` nem `V`.
- [ ] Nenhuma aberta liquidada; nenhuma perdida com odd zero.
- [ ] Coluna Data = evento em São Paulo.
- [ ] Contagem capturada == abertas + encerradas da tela.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 08/10/2026 — conta inteira (**31 bilhetes**): `extensor/harness/fixtures/shuffle.sportsbets.json`
(ids trocados por `SHFfixture…`; valores e textos da casa).

| Fixture | Tipo | Status | Stake | Odd | Evento (SP) | Retorno | Fonte |
|---|---|---|---|---|---|---|---|
| #2 | Simples | WON | 40,00 | 1,88 | 08/10 06:10 | 75,20 | card |
| #1 | Simples | LOST | 35,00 | 4,9 | 08/10 14:00 | 0 | card |
| #14 | Múltipla 3, 1 perna PUSHED | WON | 10,00 | **5,1192** (card 11,52) | 08/10 14:00 | **51,192** | card |
| #11 | Sistema Duplos de 3 | WON | 60,00 | **0,9166** | 08/10 01:20 | **54,996** (card 55,00) | card |
| #9 | Sistema Duplos de 3 | LOST | 60,00 | 5,6298 (média) | — | 0 | card |
| #7 | Múltipla 2 | WON | 25,00 | 8,82 | **07/10 23:00** | 220,50 | card |
| #18 | Múltipla 3 | LOST | 10,00 | 14,93856 (card 14,94) | 07/10 10:00 | 0 | card |
| #24 | Múltipla 2 | ABERTA | 25,00 | 8,066 (card 8,07) | 09/10 00:00 | — | card |

**Sem amostra:** cashout executado · anulada/cancelada · `PARTIAL` · boost · freebet · bet
builder (perna com 2+ seleções) · outra moeda.

---

## Feedback para a camada global / MODELO

1. **Primeira casa GraphQL.** A query com escalar JSON (`sportsBetsV3`) entrega o bilhete
   inteiro; o recon só precisou da operação, do header e do cursor.
2. **O rótulo `WON` cobre retorno menor que a stake** em sistema. É a régua do dinheiro (o
   retorno contra as fórmulas do `calcular_pl`) que dá o `W` com P/L negativo.
3. **Apostas de outros usuários convivem com as da conta na mesma tela.** Casa nova com feed
   público de apostas pede a mesma guarda: filtrar pela requisição E pelo dono do bilhete.
