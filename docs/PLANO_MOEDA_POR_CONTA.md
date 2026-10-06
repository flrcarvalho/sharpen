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
| 4c | Captura: **SapphireBet + PariPesa + Megapari** (espelhos da 1xBet) | **NO AR e validadas ao vivo (s391)** |
| 5 | Caixa em conta USD/USDT (depósito/saque/ajuste na moeda da conta) | **NO AR (s391)** |
| 6 | Câmbio, corretoras e realização (8 etapas) | **DESENHADO (s398)**, ver [a seção](#passo-6-câmbio-corretoras-e-realização-desenho-s398) |

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
- `/salvar`: `cambio.moedas_contraditorias` compara com a moeda da conta. `$`, `US$`, USD e
  USDT cabem um no outro, sem caixa (**decisão do Feca, 04/10/2026**: a casa não distingue
  dólar de Tether, e o cadastro decide). O aviso fica para real × dólar e moeda fora da tabela. Divergência vira **alerta apontando a conta** (nome e
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
  avisado. **Botão Conectar provado em produção** (true, controle negativo false, casa em
  `captura`). **Não validado ao vivo:** a captura pela extensão na conta do Feca.

### O que o item 5 fez (s391): Caixa na moeda da conta

- Decisão do Feca: em conta USD/USDT a Caixa roda INTEIRA na moeda da conta. Saldo inicial,
  depósitos, saques, ajustes e conferência são digitados e mostrados nela; as apostas entram pela
  `stake_orig` e o P/L sai do `calcular_pl` sobre ela. A conferência compara USDT com USDT, sem
  cotação no meio (converter faria a divergência nunca zerar).
- `caixa_mov.moeda`: a moeda da conta no instante do lançamento; vazia = moeda da conta (todo
  lançamento anterior, inclusive os que o Feca já tinha feito, que passaram a valer em USDT).
  Lançamento de outra moeda e aposta sem origem ficam FORA e a tela diz quantos.
- Painel de Contas: cada conta na moeda dela; as somas em R$ convertem pela cotação de hoje,
  marcadas com ≈; sem cotação, a conta fica fora da soma.
- Gates: `tests/test_caixa_moeda.py` (projeção 5/5 e tela 6/6 mutações) e os testes de forma
  do INSERT e das queries. **Não validado ao vivo** com a conta do Feca.

### Correção pós-validação (s391): aberta com jogo futuro

- Na 1ª captura real da DEX Sport, **10 das 12 abertas foram recusadas** no `/salvar` por
  "sem cotação": sem carimbo de colocação, a cotação usava a data do bilhete, que é a do
  EVENTO (amanhã), e a Binance não tem candle de amanhã. Agora data posterior a hoje vira hoje
  (`cambio._iso_da_linha`): o dinheiro saiu no máximo hoje.
- A barreira de recaptura não segura os recusados (o JOIN com `bilhetes` só pula bilhete
  gravado): a próxima captura traz os 10.
- **Pendente (próxima versão da extensão):** Dex e Betpanda mandarem o carimbo de colocação
  (`placedAt`/`timestamp`), para a cotação ser a do dia exato da aposta.

### Limites conhecidos do passo 1

- ~~Nada grava `parceiros.moeda` ainda~~: resolvido no passo 2a (s391). Até alguém escolher
  outra moeda numa conta, nenhum número no ar muda.
- USD de aposta de hoje usa a PTAX mais recente como proxy (regra do Polymarket). Em
  bilhete **sem código** isso pode mudar a assinatura entre dois envios; as 4 casas têm código.
- ~~Edição manual da stake grava R$ e não toca na origem~~: desde o passo 3 (s391) ela
  limpa a origem quando o número muda.
- A **Caixa** soma depósitos e stakes em R$; conta em USDT vai precisar de depósito em
  USDT convertido. ~~Não tratado~~ (resolvido no item 5, s391). **Visto em uso real (03/10/2026):** o Feca lançou os depósitos da Betpanda
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

### O que o passo 4c fez (s391)

- **Três casas, não duas:** o Feca acrescentou a **Megapari** (USDT), que `megapari.com`
  redireciona para espelhos de domínio variável (`2479527mp.pro` no recon). Recon com a conta
  dele nas três: mesmo corpo, mesmo JSON e mesmo enum da 1xBet, caminho `/bethistory-api/Web/`.
- `x1_inject.js` casa os dois caminhos. `formatTicket1X` ganhou a moeda no dinheiro (`_dinJB`),
  o tipo **Sistema** (`BetTypeId` 2; o perdido vem sem `Coef` e a odd fica VAZIA, nunca o
  produto) e o **carimbo de colocação** — que agora sai também na Betpanda e na DEX Sport.
- **Carimbo de colocação** (`AAAAMMDDhhmmss`, São Paulo), só em bilhete de outra moeda: o
  servidor já o lia (`carimbos_do_texto`) e ele decide o **dia da cotação**. Fecha a pendência
  da DEX Sport (aberta com jogo amanhã cotada pela data do evento). Casa em real fica byte a byte
  igual (controle negativo no harness).
- Grafias `SapphireBet`, `PariPesa` e `Megapari`. ⚠️ A 1ª versão registrou `MegaPari` e a base já
  tinha `Megapari` (medição feita sem `lower()`): os 20 bilhetes da 1ª captura caíram numa casa
  gêmea, invisível na conta. Corrigido na 0.7.37 + `unificar_casas.py` (o bug da s249).
  **SapphireBet e Megapari ficam fora do `CASA_HOSTS` do popup** de propósito: trocam de domínio,
  e domínio listado travaria o espelho novo. A PariPesa (domínio estável) entra.
- Harness: um caso por casa sobre `x1_espelho.mjs` (12 + 4 + 4 bilhetes reais), 7 mutações
  detectadas. SharpenUp **0.7.36**, nota genérica só na home.

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

## Passo 6: câmbio, corretoras e realização (desenho, s398)

**Origem:** pergunta do Gabriel (Los Panas, 06/10/2026). Duas apostas de 40 USDT apareciam
como R$ 201,35 e R$ 208,53. O número estava certo (cotações de 5,034 e 5,213, dias
diferentes), mas a conversa expôs o defeito de fundo: **o P/L em R$ ignora o câmbio.** 100 USD
apostados com o dólar a 5, ganhos com odd 2 e com o dólar a 4,5 na liquidação: o sistema mostra
+R$ 500, e no bolso há R$ 400 a mais.

### Decisões do Feca, confirmadas com o Gabriel (06/10/2026)

Cenário: contas em USDT nas casas cripto (passo 4), dinheiro circulando entre casas por
corretora (Binance, Bybit), câmbio para real feito fora do Sharpen.

1. **A verdade é a moeda da conta.** Aposta, lucro, saldo, depósito e saque nascem e ficam
   na moeda dela. O R$ é visão derivada. Hoje é o contrário (`stake` em R$ é a verdade e
   `stake_orig` é anotação), e é isso que este passo inverte.
2. **Resultado das apostas não sofre com o câmbio.** ROI de tipster e de método leem só o P/L
   de apostas. Cada aposta vale em R$ pela cotação do **dia em que foi FEITA**, para a stake e
   o lucro usarem a mesma cotação: com a da liquidação, a mesma aposta de odd 2 daria ROI de
   90% em vez de 100%, câmbio disfarçado de resultado.
3. **Corretoras entram no sistema**, quantas o dono tiver. Saque de casa informa o DESTINO,
   depósito em casa informa a ORIGEM, e o saldo aparece na corretora.
4. **Taxas de transferência são informáveis** (saíram 100, chegaram 99) e entram como custo.
5. **Enquanto o dinheiro está na moeda, o câmbio é "no papel".** Mudar de casa ou ir para a
   corretora não é evento de câmbio: o dinheiro continua em USDT.
6. **O câmbio só realiza na troca por real**, declarada pelo dono na corretora ("vendi 200
   USDT, recebi R$ 900"). Daí em diante o valor trava.

### O modelo

O câmbio é da **MOEDA do dono**, não da casa: um "bolso" por moeda e por dono, somando todas
as casas e corretoras daquela moeda. USD e USDT são bolsos separados (a tolerância de
04/10/2026, em que `$`/USD/USDT cabem um no outro, vale só para o aviso de captura).

Cada bolso guarda **quantidade** e **custo em R$**, por custo médio:

| Evento | Quantidade | Custo em R$ |
|---|---|---|
| Compra declarada (paguei R$ X, recebi Y) | + Y | + X |
| Dinheiro que entra no bolso sem compra declarada (saldo inicial, depósito sem origem) | + valor | + valor × cotação do dia |
| Aposta liquidada | + P/L na moeda | + P/L × cotação do dia da aposta |
| Transferência entre casas e corretoras do mesmo bolso | nada | nada |
| Taxa de transferência | − taxa | − taxa × custo médio (vira custo no mês) |
| Venda declarada (vendi Y, recebi R$ X) | − Y | − Y × custo médio; **realizado = X − Y × custo médio** |

    câmbio no papel = quantidade × cotação de hoje − custo em R$
    resultado       = P/L de apostas + câmbio realizado + câmbio no papel − taxas

Conferência do exemplo: depósito de 100 a 5 (custo 500), aposta de odd 2 ganha +100 a 5
(custo 1.000, 200 no bolso), dólar a 4,5: o bolso vale 900, câmbio no papel −100, resultado
+400 = +500 de apostas − 100 de câmbio.

**No Dashboard, as duas réguas de sempre:** câmbio **realizado** e **taxas** são fluxo e
entram no mês em que aconteceram (a régua soma, como o custo). Câmbio **no papel** é estoque,
muda todo dia e fica FORA do P/L do período, rotulado, como as Contas em operação.

### Etapas (uma por vez, cada uma com gate por mutação)

| # | O quê | Observação |
|---|---|---|
| 6.0 | **Medir** a base: contas fora do real por dono, bilhetes com `stake_orig`, lançamentos da Caixa nessas contas | Dimensiona o backfill antes de qualquer código |
| 6.1 | **Inverter a verdade:** edição manual em conta de outra moeda grava na moeda e refaz o R$ pela `cotacao` gravada (hoje limpa a origem); P/L em R$ derivado do P/L na moeda | Reabre a decisão de 03/10 de "stake editada limpa a origem": levar ao Feca antes |
| 6.2 | **Corretoras:** cadastro, Caixa própria, conferência de saldo | Decidir na etapa: `parceiros` com tipo ou tabela própria. `parceiros` é lido por 15 queries só em `app/*.py` (filtros, custo, matcher, Contas em operação): corretora ali vaza como casa sem aposta. Medir antes |
| 6.3 | **Transferência:** saque com destino e depósito com origem, gravados como UMA operação (dois lançamentos ligados), taxa opcional | O par nasce e morre junto; apagar um lado sozinho deixa saldo fantasma |
| 6.4 | **Compra e venda** de moeda na corretora | É a venda que realiza o câmbio |
| 6.5 | **Bolso por moeda:** custo médio, realizado e no papel, função pura | Núcleo testável, como o `_caixa_projetar` |
| 6.6 | **Telas** (`/nova-ui`): Contas & Parceiros com saldo na moeda, ≈ R$ de hoje e o câmbio do bolso; Dashboard com apostas, câmbio realizado, taxas e câmbio no papel rotulados; a cotação usada visível com data e fonte | Número que se mexe sozinho sem dizer a cotação lê como defeito |
| 6.7 | **Polymarket** no mesmo modelo, como bolso em USD | Hoje a Caixa dela (s397) usa a PTAX da compra, uma régua própria |
| 6.8 | **Backfill** das contas que já existem: cotação do dia em cada lançamento, saldo inicial pela cotação do corte | Depende da medição da 6.0 |
