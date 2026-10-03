# Plano: conta em outra moeda e as 4 casas cripto (s390)

> **Sigilo, decisão do Feca (02/10/2026):** Bet Panda, Dex Sport, SapphireBet e PariPesa
> são casas normais no seletor, mas **não entram em aviso ao grupo de testers, no
> `changelog.json` nem na home**. Nenhum passo desta frente roda `scripts/avisar_testers.py`.

## Decisões do Feca (02 e 03/10/2026)

- **A moeda é da CONTA**, escolhida no cadastro (BRL, USD, USDT). A mesma casa pode ter
  uma conta em R$ e outra em USDT.
- **Cada moeda com a sua cotação.** USD pela PTAX/BCB (a mesma régua do Polymarket); USDT
  pela cotação real USDT/BRL da Binance, e não pela paridade com o dólar.
- A tela mostra tudo em BRL **com a opção de ver na moeda original**.

## Passos

| # | O quê | Estado |
|---|---|---|
| 1 | Banco + cotação + conversão no `/salvar` | **NO AR (s390)** |
| 2 | Moeda no cadastro da conta (rota + modal) + aviso quando a captura contradiz o cadastro | aberto |
| 3 | Tela: valor original ao lado da stake e seletor BRL/moeda original (`/nova-ui`) | aberto |
| 4 | Captura: Bet Panda → SapphireBet + PariPesa → Dex Sport | aberto |

### O que o passo 1 fez

- `parceiros.moeda` (padrão `BRL`) e, em `bilhetes`, `moeda` + `stake_orig` + `cotacao`.
  A coluna `stake` continua **sempre em R$**: nenhuma tela, KPI, dedup ou P/L muda.
- `app/cambio.py`: só a stake converte (a odd não tem moeda; o P/L é derivado). Data da
  cotação = carimbo de colocação quando o robô manda, senão a data do bilhete.
- **USDT usa a ABERTURA do candle diário**, fixa desde 00:00 UTC. O fechamento muda até o
  fim do dia, e o UPSERT congela a stake quando a aposta liquida: com o fechamento, o
  número final dependeria da hora da liquidação.
- Sem cotação, a linha é **recusada** (`rejeitados` do `/salvar`), nunca gravada como R$.
- No UPSERT a origem (`moeda`/`stake_orig`/`cotacao`) troca **exatamente** quando a
  stake troca, inclusive para NULL.
- Gates: `tests/test_cambio_moeda.py` (9 mutações, 9 detectadas), 3 casos em
  `tests/test_salvar_parceiro_id.py` (4 mutações na rota, 4 detectadas) e 4 casos em
  `tests/test_repository_db.py` (só no CI).

### Limites conhecidos do passo 1

- **Nada grava `parceiros.moeda` ainda:** toda conta é BRL até o passo 2. O passo 1 sozinho
  não muda nenhum número no ar.
- USD de aposta de hoje usa a PTAX mais recente como proxy (regra do Polymarket). Em
  bilhete **sem código** isso pode mudar a assinatura entre dois envios; as 4 casas têm código.
- Edição manual da stake na grade (`PATCH /bilhetes/{id}`) grava R$ e não toca na origem.
  O passo 3 decide o que a grade faz em conta de outra moeda.
- A **Caixa** soma depósitos e stakes em R$; conta em USDT vai precisar de depósito em
  USDT convertido. Não tratado.
- Binance medida acessível de casa (03/10). Do Railway **não foi medida**: o primeiro
  `/salvar` de conta USDT em produção é a prova; se o host falhar, cai no segundo.

## Recon das casas (03/10/2026, contas do Feca, Chrome)

| Casa | Motor | Lista de apostas | Moeda medida |
|---|---|---|---|
| **Bet Panda** (`betpandacasino.io`) | BetBy, como Jonbet/Blaze | `GET api-a-c7818b61-600.sptpub.com/api/v1/my_bets/list?currency=USD&lang=en&limit=15&skip=0&status=…` | API diz `currency: "$"`, carteira é **Tether** |
| **SapphireBet** (`sbethub2365.com`, cai muito) | 1xBet | `POST /bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates` | USD |
| **PariPesa** (`paripesa.com`) | 1xBet | o mesmo POST da Sapphire | USDT |
| **Dex Sport** (`dexsport.io`) | **própria** | `GET prod.dexsport.work//api/sportsbook/history/tickets?status=placed\|finished&page=N&locale=pt` (XHR) | `usdt` por bilhete |

**Bet Panda:** o host da API não segue o padrão `api-NN-sp-<hash>` das outras BetBy;
conferir o casamento de host do `jb_inject.js`. O inject não crava `currency=BRL`, repassa
o que a página pediu. Bilhete: `id` (19 díg.), `sum`, `k`, `result_sum`, `status`,
`timestamp` (epoch s).

**Sapphire e PariPesa:** o `x1_inject.js` só casa `/service/bethistory/` (o caminho da
1xBet). Basta ampliar o regex e registrar os hosts. O inject já lê `CurrencyCode`.

**Dex Sport:** JSON limpo, paginado em `meta.totalPages`.

| Campo | Valores vistos |
|---|---|
| `result` do bilhete | `0` aberta · `1` ganha · `2` perdida |
| `status` do bilhete | `2` aberta · `3` concluída |
| `status` da perna | `0` não decidida · `1` ganha · `2` perdida |
| `payout` | retorno (125,75 = 25 × 5,03 no WIN) |
| `placedAt` / `finishedAt` | epoch em segundos |

Bilhete: `id` (UUID), `amount`, `coefficient`, `currency`, `ticketType` (0/1),
`bets[]` com `eventDate`, `disciplineId`, `outcomeName`, `eventMarket{name}`, `event{name}`.
Uma perna pode ficar `0` num bilhete já perdido (a outra perdeu antes). **Void e cashout
não apareceram na amostra (11 concluídas):** o de-para nasce com W/L e o resto sobe como
"a conferir" até haver caso real.
