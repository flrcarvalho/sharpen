# CASA_CLOUDBET
## Camada de tradução — Cloudbet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Cloudbet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Cloudbet` · site: `www.cloudbet.com` · apostas em **My bets** (painel lateral,
  abas Active e Settled, só 72 h) e em **Bet history** (`/en/sports/bet-history`).
- Locale: a interface está em inglês, e **esporte, mercado, seleção, times e ligas vêm em
  INGLÊS** (`Basketball`, `Paul Reed Total Assists`, `Under 2.5`, `NBA`).
- Moeda: **cripto**, a da própria aposta (`baseCurrency`; a conta do recon aposta em **USDT**).
  A tela mostra o equivalente em dólar (`≈ $30.00`), que **não** entra no bilhete. A moeda da
  conta no Sharpen é a que o cliente escolheu no cadastro, como nas outras casas; o bloco leva
  `Moeda:` da aposta e o `/salvar` decide.
- Dinheiro e odd em texto decimal (`"30"`, `"6.934"`), **sem milésimos**.
- Plataforma **PRÓPRIA**: front Next.js, API no mesmo domínio (`/sports-betting/v4/…`,
  `/sports-api/v6/…`). Nenhuma outra casa do sistema usa essa API. Família `cb` (inject
  `cb_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s442):** `Cloudbet`, a da BASE. Medido em 10/11/2026: 283 bilhetes, 2 contas, 2
> `casas_meta` e 874 `correcoes`, todos em `Cloudbet` (uma grafia só). A conta do Jaao26 chama-se
> `CloudBet`, mas é o NOME da conta, não a casa.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/cb_inject.js`).

```
GET /sports-betting/v4/bets/positions?limit=999&locale=en&offset=N&status=ACCEPTED
GET /sports-betting/v4/bets/positions?limit=999&locale=en&offset=N&status=COMPLETED&from=<iso>&to=<iso>
    → { "hasNext": false, "items": [ posição ] }
GET /sports-betting/v4/bets/positions/{positionId}?currency=<moeda nativa>&locale=en
    → { "bets": [ aposta ] }
GET /sports-api/v6/sports/events/{eventId}?locale=en&markets=x
    → evento (nome, esporte, liga, cutoffTime, mandante, visitante)
    (cabeçalhos authorization + x-cloudbet-metadata + x-cloudbet-version)
```

Medido com a sessão do recon (10/11/2026):

- **O cookie NÃO basta** (HTTP 401). A página manda `authorization` (JWT),
  `x-cloudbet-metadata` e `x-cloudbet-version` em toda chamada de `/sports-api/` e
  `/sports-betting/`, e faz essas chamadas **sozinha** segundos depois de carregar (5 em
  `/sports-api/v6` sem tocar em nada). O inject aprende os três de uma chamada real.
- **O painel pede só 72 h** (`from` = agora − 3 dias). O replay pede as abertas sem janela e as
  liquidadas em janelas de 360 dias: `from`/`to` são **obrigatórios juntos** (só `to` = 400) e
  não podem passar de **1 ano** (400). A janela filtra pela **liquidação** (`positionTime`):
  aposta colocada em 09/11 e liquidada em 10/11 só aparece na janela de 10/11.
- **`limit` até 1000** (1001 = 400). Paginação por `offset`; **fim = `hasNext:false`** (medido
  com limit 6: 6, 6, 3, sem repetir posição). Sem `status`, a lista traz só as liquidadas.
- **Uma chamada de DETALHE por posição**, porque a lista não traz o ID da tela, a odd útil nem
  a colocação. ⚠ O detalhe **só responde na moeda nativa** da aposta: `currency=USDT` traz a
  aposta, `BTC`, `BRL` ou sem o parâmetro devolvem `{"bets":[]}`. A moeda nativa são as chaves
  de `positions[].portfolio` da lista.
- ⚠ **A lista CONVERTE o dinheiro** para a moeda pedida (`currency=BTC` → stake 0,000402 para
  30 USDT). Dinheiro da lista nunca entra no bilhete.
- **Uma chamada por EVENTO distinto**: a seleção não diz jogo, esporte nem início. `markets=x`
  tira os mercados (64 → 45 KB num evento aberto); não há pedido em lote (`?ids=` = 400).

### 2.3 Layout do bilhete (card)

Painel lateral: `3 leg parlay @ 6.93` / `Bet Builder`, contador `Won 1 · Lost 1 · Push 1`,
Stake e P/L. No Bet history, linha expansível com cada jogo, o placar e
`Bet 30 USDT @ 6.93 · ID: <uuid>`. Não há prova de linha em branco entre bilhetes no
`innerText`: **texto por DOM não serve; por isso API.**

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Onde | Confirmado na Cloudbet |
|---|---|---|
| `uuid` | detalhe, `bets[]` | **o código**: 36 caracteres, o `ID:` do card expandido |
| `positionId` | lista | hash de 40 caracteres da POSIÇÃO; só serve para pedir o detalhe |
| `state` | detalhe | `ACCEPTED` (aberta) · `COMPLETED` (liquidada) |
| `result` | detalhe, aposta e seleção | `WIN` · `LOSS` · `PUSH` · `PENDING` |
| `type` | detalhe | `PARLAY` · `SAME_GAME_PARLAY` (Bet Builder) |
| `stake` · `baseCurrency` | detalhe | stake na moeda nativa (`30`, `USDT`) |
| `price` | detalhe | **a odd da aposta**, a do card (`@ 6.93` = 6,934). Na múltipla é o produto das pernas, truncado em 3 casas |
| `returnAmount` | detalhe | ⚠ **LUCRO**, não retorno: `-30` na perdida de 30. Retorno = `stake + returnAmount` |
| `potentialReturnAmount` | detalhe | retorno potencial (bruto): 208,11 = 30 × 6,937 na aberta |
| `adjustedPrice` · `exhaustedPotentialReturnAmount` | detalhe | `0` em toda a amostra |
| `isCashoutBet` | detalhe | `false` em toda a amostra (§7) |
| `createTime` · `completeTime` | detalhe | colocação e liquidação, ISO UTC com 6 casas de fração. ⚠ A aberta traz `completeTime: 0001-01-01T00:00:00Z` (sentinela) |
| `selections[]` | detalhe | `eventId`, `marketKey`, `outcome`, `params`, `price`, `result`, `sportKey`, `competitionKey`: **sem nomes** |
| `selections[]` | lista | `marketName` (`Paul Reed Total Assists`), `outcomeName` (`Under 2.5`), `result` |
| `aggregate.odds` | lista | ⚠ **não usar**: 0 em 3 das 4 perdidas; recalculada sem a perna PUSH na outra (3,52) |
| evento | `/sports-api/v6` | `name` (`DET Pistons v WAS Wizards`), `sport.name`, `competition.name`, `cutoffTime` (início), `home`/`away` |

**Ficha (s442):** adaptador `app/adaptadores/cb.py`, gate `tests/test_adaptador_cb.py`. O cru é
`{aposta, posicao, eventos}`: a aposta do detalhe, o item da lista (os nomes de mercado só moram
nele) e os eventos das pernas. As seleções de um mesmo jogo num Bet Builder viram UMA perna
`Bet Builder` (D43, como a Sportsbet.io), com a odd do grupo.

---

## 3. ID do bilhete

- `uuid` da aposta (`225709c2-3e94-467c-9812-37379a7082cf`). Dedup forte por ID. Vai para a 11ª
  coluna interna (`Código`). Nunca o `positionId`.

> ⚠ **Histórico por print (s442):** antes da captura, o Jaao26 lançou 283 apostas Cloudbet por
> print e manual (01 a 10/11/2026), com código lido pela IA (`CLO-0266`, `codigo_ocr`) ou vazio.
> A captura traz as mesmas apostas com o `uuid`: quem casa as duas é a Migração B/B' do UPSERT.
> Conferir a 1ª captura dele (CLAUDE.md, "Casa nova na captura = o histórico dela por print vira
> dívida").

---

## 4. Data

A coluna Data é o **início do evento** (`cutoffTime`), de UTC para São Paulo. Na múltipla, a
regra global escolhe a perna (o bloco leva a mais recente e cada perna com o seu `Início:`).
`225709c2`: DET×WAS às 00:00 UTC de 10/11 = **09/11 21:00** em São Paulo. A colocação
(`createTime`) vai ao lado, com o carimbo para o dia da cotação.

---

## 5. Status e Resultado

O retorno é `stake + returnAmount`. `W` exige fechar com stake × `price` com **tolerância de 1
centavo**, ou ter perna `PUSH` (a casa refaz a odd sem ela: 6,934 ÷ 1,97 = 3,52 no card).

| `state` · `result` · dinheiro | Leitura | Código |
|---|---|---|
| `ACCEPTED` | Em aberto | *(vazio — não liquidar)* |
| `LOSS` · `returnAmount` = −stake | Perdeu | `L` |
| qualquer · `returnAmount` = 0 (retorno = stake) | P/L zero | `V` |
| `WIN` · stake + returnAmount = stake × price (± 1 centavo) | Ganhou | `W` |
| `WIN` · retorno > stake · alguma perna `PUSH` | Ganhou, odd = retorno ÷ stake | `W` |
| `LOSS` com retorno, `WIN` que não fecha sem PUSH, `isCashoutBet`, rótulo novo | sobe cru | *(a conferir)* |

Medido: `LOSS` 4 e `ACCEPTED` 15. O resto é a régua acima, travada por clone no harness,
**não** por amostra real. O bloco sempre leva
`Status (API): state=… · result=… · type=… · posição=…`.

Perna: `WIN` ganha · `LOSS` perdida · `PUSH` anulada · `PENDING` não decidida (perna de bilhete
que perdeu antes). Na aberta a casa já marca perna decidida, e o bloco a leva em linha própria
(`Estado da perna (casa): WIN`), nunca no colchete.

---

## 6. Boost / promoção

Nenhum campo de boost na amostra. Se aparecer, vale a regra global do `W` (`retorno ÷ stake`) e
o bilhete sobe "a conferir" até ser medido.

---

## 7. Cashout

`isCashoutBet` = `false` e `cashoutAmount` = `0` em toda a amostra. Com `isCashoutBet` o bilhete
sobe "a conferir" (e a Ficha recusa). A regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`) vale
quando for medido.

---

## 8. Bônus

Nenhum campo de freebet na amostra. Se aparecer, o bilhete fica "a conferir" até ser medido.

---

## 9. Mapa de mercados (Cloudbet → `Aposta` global)

Só os mercados **confirmados** no dado real. Todos são props de jogador
(`<Jogador> Total Rebounds|Assists|Points|3-Pointers Made|Points + Assists|Assists + Rebounds|
Receiving Yards`, seleção `Over|Under <linha>`): a categoria sai do `MASTER_APOSTAS` pelo objeto
medido, sem atalho aqui.

> **Bet Builder** (`SAME_GAME_PARLAY`) é `Múltipla` (`MASTER_APOSTAS`). Ele pode juntar um Criar
> Aposta de um jogo com seleções avulsas de outros: `225709c2` = DET×WAS (2 seleções, 3,52) +
> TOR×MEM (1, 1,97). A descrição segue o `MASTER_DESCRICAO` em pt-BR, confronto em ` v `
> (a casa já escreve `A v B`).

---

## 10. Stake

Campo `stake` do detalhe, na moeda nativa da aposta; a conversão para R$ é do `/salvar`.

---

## 11. Odds

- **A odd do bilhete é `price`**, a do card. Na múltipla é o produto das pernas truncado em 3
  casas (3,52 × 1,97 = 6,9344 → 6,934).
- **Bet Builder:** cada perna leva a odd do Criar Aposta do **seu jogo**; não é odd da perna.
  No Criar Aposta puro (um jogo só), as três pernas repetem a odd do bilhete.
- **L e aberta:** `price`. A lista (`aggregate.odds`) zera na perdida; o detalhe não.
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `portfolio` (o mesmo dinheiro por moeda; serve só para achar a moeda nativa), `betLegIdentifier`,
  `cashoutSupported`, `channel`, `side`, `spendingPoints`, `betSlipId`, `marketUrl`, `categoryKey`.
- Do evento: `players`, `metadata`, `media`, `streams`, `markets`, `sequence`.

---

## 13. Pegadinhas (resumo rápido)

1. **`returnAmount` é LUCRO**, não retorno (§2.5).
2. **Odd da lista zera na perdida**: a odd é o `price` do detalhe (§11).
3. **Detalhe só na moeda nativa**; a lista converte o dinheiro (§2.1).
4. **Janela pela liquidação, ≤ 1 ano, `from`+`to` juntos** (§2.1).
5. **Bet Builder pode ter vários jogos**, cada um com a odd do seu Criar Aposta (§9, §11).
6. **`completeTime` sentinela 0001-01-01 na aberta** (§2.5).
7. **Cookie não basta**: cabeçalhos aprendidos da página (§2.1).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada na moeda que o cliente usa (a do recon aposta em **USDT**).
- [ ] Nenhuma aberta liquidada; nenhuma perdida com odd zero.
- [ ] Coluna Data = início do evento em São Paulo.
- [ ] Contagem capturada == Active + Bet history.
- [ ] **1ª ganha / simples / cashout / freebet / posição com mais de uma aposta / aposta em
      outra cripto:** salvar o JSON como fixture e trocar o clone do harness.
- [ ] **1ª captura do Jaao26:** conferir que as 283 apostas por print não duplicaram (§3).

---

## 15. Exemplos golden (bilhetes reais)

Recon de 10/11/2026 — conta inteira (**19 apostas**: 4 liquidadas, 15 abertas, todas múltiplas
de 3): `extensor/harness/fixtures/cloudbet.recon.json`.

| Código (uuid) | Tipo | Estado | Stake (USDT) | Odd | Colocação (SP) | Evento (SP) | Fonte |
|---|---|---|---|---|---|---|---|
| 225709c2-… | Bet Builder DET×WAS + TOR×MEM | `LOSS` (Won 1 · Lost 1 · Push 1) | 30 | 6,934 | 09/11/2026 15:11:40 | 09/11 21:30 | card |
| d4789569-… | Criar Aposta CHA×CLE (3) | `LOSS` | 30 | 9,67 | 09/11/2026 17:19:46 | 09/11 21:00 | card |
| 0b08efd7-… | Parlay 3 jogos | `LOSS` (Lost 1 · Pending 1 · Push 1) | 30 | 7,68 | 09/11/2026 14:53:03 | 09/11 22:30 | card |
| c763f002-… | Bet Builder ATL×LAL + GS×NO | `LOSS` (Won 1 · Lost 1 · Pending 1) | 30 | 6,48 | 09/11/2026 18:41:53 | 10/11 00:00 | card |
| 1e7c2017-… | Parlay 3 jogos | `ACCEPTED` | 30 | 6,937 | 09/11/2026 16:16:57 | — | card (`@ 6.93`) |

**Sem amostra:** ganha · simples · cashout · freebet · boost · outra cripto.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão (**SharpenUp 0.7.73**) e dar **Ctrl+Shift+R** na aba da Cloudbet **e**
   na aba do painel.
2. Estar logado na Cloudbet e esperar a página carregar (é dela que o inject aprende os
   cabeçalhos; o toast avisa `faça login, espere a página carregar` se faltarem).
3. Conectar → Copiar bilhetes. Uma chamada por posição e por jogo: conta grande demora mais.
4. Conferir no dashboard: contagem, código (uuid), data do evento, odd e moeda.
5. Na 1ª ganha/simples/cashout, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

1. **Campo `return…` que é lucro.** Terceira casa (3et, Cloudbet): toda casa nova precisa
   conferir o campo de retorno contra stake × odd antes de usar.
2. **Lista que converte moeda.** O dinheiro de uma lista com `currency=` pode estar convertido
   para a moeda de EXIBIÇÃO; o da aposta mora no detalhe, na moeda nativa.
