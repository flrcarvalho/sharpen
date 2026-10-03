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
| 2a | Moeda no cadastro da conta (rota + modal) | **NO AR (s391)** |
| 2b | Aviso quando a captura contradiz o cadastro (extensão + `/extrair` + `/salvar`) | **NO AR (s391)** |
| 3 | Tela: valor original ao lado da stake e seletor BRL/moeda original (`/nova-ui`) | **NO AR (s391)** |
| 4a | Captura: **Bet Panda** | **NO AR e validada ao vivo (s391)**: 45 de 45 |
| 4b | Captura: **Dexsport** (escolha do Feca, antes das 1xBet) | **NO AR (s391)**, falta validar ao vivo |
| 4c | Captura: SapphireBet + PariPesa | aberto |
| 5 | Caixa em conta USD/USDT (depósito/saque/ajuste na moeda da conta) | aberto |

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

### O que o passo 2a fez (s391)

- `POST /parceiros` e `POST /parceiros/{id}/editar` aceitam `moeda`, validada na fronteira
  contra `cambio.MOEDAS` (minúscula vira maiúscula; fora da lista dá 400). `GET /parceiros`
  devolve a `moeda` de cada conta.
- **Ausente = não mexe.** Na edição e na reativação de conta arquivada pelo `ON CONFLICT`
  do `criar_parceiro`: recriar pelo campo inline (que só tem o nome) uma conta USDT
  arquivada não a devolve em BRL. Conta nova sem escolha nasce BRL.
- Modal de conta: seletor BRL / USD / USDT (o `.cxm-seg` da Caixa), na criação e na edição.
  A criação inline da lista lateral continua só com o nome, então nasce BRL.
- **Trocar a moeda vale daqui para frente** (decisão do Feca, 03/10/2026): nenhum bilhete é
  reconvertido, e o modal avisa quantas apostas da conta ficam como estão. A aposta
  liquidada tem a stake congelada pelo UPSERT; a aberta é refrescada pela recaptura e passa
  a converter pela moeda nova, que é a leitura certa do que a casa mostra.
- Gates: `tests/test_moeda_conta.py` (rota: 4 mutações à mão, 4 detectadas; front:
  13 mutações automáticas sobre `tests/js/moeda_conta_front.mjs`, 13 detectadas) e
  `test_moeda_no_cadastro_cria_lista_edita_e_reativa_sem_perder` no `test_repository_db.py`
  (só no CI).

### O que o passo 2b fez (s391)

O achado que o originou: os injects sempre leram a moeda da casa (`moeda:` no jb, x1, kto,
rg, stk, tv e bda), mas **nenhum formatador do `content.js` a escrevia no bloco**. Ela
morria dentro da extensão e o servidor nunca soube em que moeda a casa falou.

- `content.js`: `_linhaMoeda` escreve `Moeda: X` logo depois do `Stake:` nos 7
  formatadores, **só quando X não é real** (`BRL`, `R$` e vazio, sem caixa, não geram
  linha). O texto das casas em real fica byte a byte igual, o hash do `bloco_visto` também,
  e o harness segue verde sem tocar em fixture. O valor sai verbatim (`$`, `usdt`).
- `cambio.moedas_do_texto` lê do texto cru (início de linha) e o `/extrair` devolve
  `moedas` no `done` dos três caminhos (sequencial, chunks e contrato de 4 campos). O front
  transporta ao `/salvar`, igual ao `carimbos`.
- `/salvar`: `cambio.moedas_contraditorias` compara com a moeda da conta. `$` cabe em USD e
  em USDT, `US$` em USD, sem caixa. Divergência vira **alerta apontando a conta** (nome e
  casa) e a gravação segue pela moeda cadastrada.
- **Versão da extensão não subiu:** nenhuma casa capturada hoje manda moeda diferente de
  real, então nada muda para ninguém até o passo 4, que sobe a versão com as casas novas.
- Gates: `tests/test_moeda_captura.py` (`cambio`: 8 mutações automáticas, 8 detectadas;
  `content.js`: 9 automáticas sobre `tests/js/moeda_captura_content.mjs`, 9 detectadas;
  rota: 4 à mão, 4 detectadas).

### O que o passo 3 fez (s391)

Decisões do Feca (03/10/2026): o formato é **`US$ 1.234,50`** e **`1.234,50 USDT`**, com milhar
pt-BR; o seletor fica **só na grade da Extração**; e a stake editada à mão **limpa a origem**.

- **Grade da Extração:** sob a stake em R$, o valor na moeda da conta (o mesmo
  `.btbl-stake-usd` do Polymarket). Com a conta ativa em USD/USDT aparece no título o
  seletor `Ver em R$ | USDT` (o `.cxm-seg`, variante `seg-2`). Vendo na moeda da conta: a
  stake e o P/L das linhas convertidas trocam de moeda, o R$ desce para a sub-linha, os
  cabeçalhos viram `Stake · USDT` e `P/L · USDT`, e a linha sem origem segue em R$. A stake
  convertida **não é editável** nesse modo (sem `data-field`): o campo grava R$, e quem lê
  USDT digitaria USDT.
- **P/L na moeda da conta** (`pl_orig`, na listagem da grade): `calcular_pl` aplicado à
  `stake_orig`, nunca `pl ÷ cotacao`. A stake em R$ foi arredondada ao centavo, e o erro
  cresce com a odd: 1 US$ a 5,0049 @ 101 dá 100,00 pelo certo e 99,90 pela divisão.
- **P/L com sub-linha** (pedido do Feca, 03/10/2026): o mesmo desenho da stake, R$ colorido
  em cima e a outra moeda neutra embaixo, com sinal (`+1.188,49 USDT`); na grade e na Base
  Completa (o feed leva `lucro_orig` só nas linhas convertidas e liquidadas). Aberta não ganha.
- **Base Completa:** só a sub-linha, sem seletor (as contas se misturam ali). O feed leva
  `moeda`/`stake_orig` **só** nas linhas convertidas. A tabela é virtualizada com altura
  fixa de linha (68 px), medida igual com e sem a sub-linha.
- **Edição à mão da stake** (`PATCH`, modal, lote) limpa `moeda`/`stake_orig`/`cotacao`
  quando o NÚMERO muda (`_limpa_origem`); regravar a mesma stake mantém.
- Gates: `tests/test_moeda_valor_original.py` (repositório: 6 mutações automáticas sobre
  uma cópia do módulo, 6 detectadas; front: 14 sobre `tests/js/moeda_grade_front.mjs`, 14
  detectadas) e `test_moeda_original_no_feed_e_a_edicao_que_limpa` (só no CI).
- **Fica como estava:** o `$ 10,00` do Polymarket (`fmtUSD`, sem milhar, exceção do
  `UI_REFERENCE §5.3`), a home (`inicio.html`) e o modal de edição, que segue em R$.

### O que o passo 4a fez (s391): Bet Panda

- 4ª casa BetBy, espelho da Jonbet/Betboom/Blaze: **zero linha nova de captura** (mesmo
  `jb_inject.js`, `formatTicketJB`, `roboJBPassive`). Registro nos 12 pontos com a chave
  `BETPANDA` e a grafia da marca `Betpanda` (a base não tinha nenhuma). Tradução em
  [`casas/CASA_BETPANDA.md`](../casas/CASA_BETPANDA.md).
- O formatador da BetBy deixou de escrever "R$" fixo: `_dinJB` rotula o dinheiro na moeda
  do bilhete (`retorno 126,00 $`) e mantém as casas em real byte a byte iguais.
- Harness `casos/betpanda.mjs` com a conta inteira do Feca (45 bilhetes), 10 cards lidos na
  tela; 4 mutações de controle, todas detectadas.
- SharpenUp **0.7.34** com nota genérica só na home (`--so-changelog`, decisão do Feca):
  a nota não nomeia a casa e o grupo **não** foi avisado.
- **Botão Conectar provado em produção** (`_casaConectavel('Betpanda')` true, controle negativo
  false, `Betpanda` em `captura` no `/casas`).
- **Não validado ao vivo:** a captura pela extensão na conta do Feca e a conversão USDT no
  `/salvar` em produção (a Binance nunca foi medida a partir do Railway).

### O que o passo 4b fez (s391): Dexsport

- Plataforma PRÓPRIA, primeira casa do motor: `extensor/dx_inject.js` (novo), `formatTicketDX`
  e `roboDXPassive`. Lista do SDK de esportes, `GET prod.dexsport.work//api/sportsbook/history/
  tickets?status=placed|finished&page=N`, por XHR, com o `Authorization` aprendido da chamada
  real e replay por XHR até `meta.totalPages`. Tradução em
  [`casas/CASA_DEXSPORT.md`](../casas/CASA_DEXSPORT.md).
- **O recon achou duas listas.** A do perfil (`txs_list`) carrega `token`, `ip` e `userId` no
  corpo e lê o retorno de um campo que guarda o potencial na perdida: descartada. O inject só
  casa o caminho do SDK, e o token nunca sai do inject (o harness confere).
- Harness `casos/dexsport.mjs` com a conta inteira do Feca (41 bilhetes, sem `nickname`), 10
  conferidos; perna anulada (odd 3,75 e não 12,56), `payout` 0 na aberta, evento em UTC.
  8 mutações de controle, todas detectadas (uma escapou e virou linha nova do caso).
- SharpenUp **0.7.35** com a mesma nota genérica só na home (`--so-changelog`); grupo não
  avisado. **Não validado ao vivo:** a captura pela extensão na conta do Feca.

### Limites conhecidos do passo 1

- ~~Nada grava `parceiros.moeda` ainda~~: resolvido no passo 2a (s391). Até alguém escolher
  outra moeda numa conta, nenhum número no ar muda.
- USD de aposta de hoje usa a PTAX mais recente como proxy (regra do Polymarket). Em
  bilhete **sem código** isso pode mudar a assinatura entre dois envios; as 4 casas têm código.
- ~~Edição manual da stake grava R$ e não toca na origem~~: desde o passo 3 (s391) ela
  limpa a origem quando o número muda.
- A **Caixa** soma depósitos e stakes em R$; conta em USDT vai precisar de depósito em
  USDT convertido. **Visto em uso real (03/10/2026):** o Feca lançou os depósitos da Betpanda
  em USDT e a Caixa os leu como R$. Pendência no `BACKLOG` (moeda, item 5).
- ~~Do Railway não foi medida~~: **medida em produção em 03/10/2026**, a 1ª captura da
  Betpanda converteu os 45 bilhetes. Texto original: Binance medida acessível de casa (03/10). Do Railway **não foi medida**: o primeiro
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
