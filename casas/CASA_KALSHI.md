# CASA_KALSHI — Tradução da casa para a língua global

> Casa **atípica**, irmã da Polymarket: a porta de entrada **não é screenshot + IA**, e
> sim a **API da conta**, assinada com a chave do usuário. A extração é determinística
> (coletor em Python, sem modelo no caminho). Este arquivo documenta a tradução; o
> cálculo continua sendo global.
>
> Reconhecimento feito em 30/10/2026 (s435) contra a conta do Feca: 1 aposta (combo,
> L), 1 depósito. Harness: `kalshi_recon.py` (scratchpad da s435, só GET). Tudo o que
> não apareceu nessa amostra está marcado como **não medido**.

---

## 1. Identidade

- Casa canônica: `Kalshi` · chave `KALSHI` · domínio `kalshi.com`
- Natureza: mercado de predição regulado (EUA), contratos SIM/NÃO que pagam US$ 1,00.
- Locale: en-US · Moeda nativa: **USD**, convertida para **BRL** na ingestão pelo PTAX
  do dia, a mesma régua da Polymarket (`CASA_POLYMARKET §2`).
- `Parceiro`: a conta é do próprio usuário e o parceiro é escolhido na sidebar, como nas
  demais casas. `Tipster`: atribuído depois, na grade ou pelo matcher.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** API REST `https://external-api.kalshi.com/trade-api/v2`, assinada.
- **Sem fallback por print.** O painel da casa troca o upload por **chave + Sincronizar**.

### 2.2 Autenticação: chave SÓ LEITURA

Cada chamada leva três cabeçalhos: `KALSHI-ACCESS-KEY` (o Key ID),
`KALSHI-ACCESS-TIMESTAMP` (ms) e `KALSHI-ACCESS-SIGNATURE` (base64). A assinatura cobre
`timestamp + MÉTODO + caminho`, **sem a query string**. Ed25519 assina direto, e RSA usa
PSS/SHA-256 com salt do tamanho do digest. O PEM não diz o tipo: ele sai da chave
carregada.

- A tela de criação da chave tem escopo: **Read all data** (`read`) × **Full access**
  (`write`). A doc (`getting_started/api_keys`) não cita isso; a tela cita.
- **O Sharpen só aceita chave com `Read all data` e SEM `Full access`.** Chave de escrita
  movimenta dinheiro do usuário, e o Sharpen não precisa disso para nada.
- O usuário **não precisa do arquivo baixado**: a tela final da Kalshi mostra o
  `API key id` e a `Private key` com botão de copiar. No Sharpen são dois campos de colar.
- A chave privada aparece **uma vez só** na Kalshi. Perdeu, apaga e cria outra.

### 2.3 Endpoints

| Endpoint | Uso |
|---|---|
| `GET /portfolio/fills` | cada execução: preço, cotas, lado, taxa, instante |
| `GET /portfolio/orders` | a ordem agrupa os fills: custo e taxa totais |
| `GET /portfolio/settlements` | o que liquidou: `market_result`, `revenue`, `settled_time` |
| `GET /portfolio/positions?settlement_status=all` | posição por mercado e por evento |
| `GET /historical/fills`, `/historical/positions` | registros **arquivados** (fora do live) |
| `GET /markets/{ticker}`, `/events/{ev}`, `/series/{s}` | descrição, esporte e mercado |
| `GET /portfolio/balance`, `/deposits`, `/withdrawals` | Caixa (§17) |

- Paginação por **`cursor`** até vir vazio, em todos os endpoints de lista.
- **O histórico mora em dois lugares.** O live tem só o recente; o resto vai para
  `/historical/*`. Coletor que lê só o live perde o passado **sem erro nenhum**.

### 2.4 Ordem do output

Inserção da **mais antiga para a mais nova** (pelo `created_time` da ordem), como na
Polymarket, para a grade (por `criado_em`) bater com a realidade.

---

## 3. Código do bilhete e deduplicação

- **Código = `order_id`** (UUID). Uma ordem é uma aposta; vários fills da mesma ordem
  somam na mesma linha.
- **Por que não o ticker com `__i`, como na Polymarket:** lá o código depende de QUANTAS
  compras o mercado tem, e a 2ª compra transforma a linha antiga em fantasma
  (`CASA_POLYMARKET §3`). O `order_id` não muda quando entra outra ordem no mesmo
  mercado, então essa armadilha não existe aqui.
- Duas ordens no mesmo mercado são **duas apostas** (podem até ser de tipsters
  diferentes), cada uma com o seu código.
- Ressincronizar a mesma conta é UPSERT limpo pela dedup global por ID.

---

## 4. Data

- **Data = a do EVENTO, como a fonte publica.** O ticker do evento traz a data do jogo
  (`KXNBA2D-26OCT29MEMPOR` → 29/10/2026), e o `sub_title` do evento repete
  (`MEM vs POR (Oct 29)`). Regra global: onde a casa só publica o dia do jogo, a data é
  esse dia (`CLAUDE.md`, "Data derivada por ESTIMATIVA é dado inventado").
- **Fallback:** `settled_time` convertido para BRT; aberta sem data de evento, o
  `created_time` da ordem em BRT.
- Combo: a data do evento das pernas; pernas em dias diferentes, a da última perna.
- ⚠️ A liquidação da amostra foi em **30/10 01:27 BRT** para um jogo de **29/10**. Usar
  `settled_time` como primária jogaria todo jogo noturno dos EUA no dia seguinte.

---

## 5. Resultado (W / L / V / HW / HL)

O contrato paga US$ 1,00 por cota do lado certo. O resultado sai do **dinheiro que a
liquidação devolveu**, pela régua global de cashout (`MASTER_RESULTADO §5.1.2` e
`§5.6`), igual à Polymarket:

- **L:** retorno zero.
- **V:** retorno igual à stake.
- **W:** retorno diferente da stake, com `odd = retorno ÷ stake`.

O `market_result` (`yes`/`no`) contra o `side` da ordem confirma o veredito, mas **quem
decide é o dinheiro** (`revenue` do settlement).

- **Não medido:** a unidade de `revenue` (a amostra deu `0`, que não distingue centavo de
  dólar), mercado anulado e mercado escalar (`settlement_value_dollars` entre 0 e 1).
  Conferir na primeira W.
- **HW / HL** não se aplicam (contrato binário, sem meia aposta).

---

## 6. Boost / promoção

- Não observado na amostra. Não há boost no modelo de contrato.

---

## 7. Cashout

- Venda antes de liquidar (`action: sell` no fill) é cashout: **W** com
  `odd = valor da venda ÷ stake`, como na Polymarket (`CASA_POLYMARKET §7`).
- **Não medido:** nenhuma venda na amostra.

---

## 8. Bônus

- Não se aplica. A stake é dinheiro depositado.

---

## 9. Mapa de mercados (apenas o confirmado)

> Camada fina: só o que a Kalshi confirmou na amostra. As categorias vivem no
> `MASTER_APOSTAS §3`.

> A categoria vem do `product_metadata.scope` da **série** (`GET /series/{s}`), não do
> título. É um campo estruturado da fonte.

| Kalshi exibe (`scope` da série) | Aposta global |
|---|---|
| `Double Double` | Double-Double |
| `Player Assists` | Assistência |
| combo (`KXMVE…`, várias pernas) | Múltipla |

---

## 10. Stake

- **Stake = o que saiu da conta, COM a taxa**: `taker_fill_cost_dollars +
  maker_fill_cost_dollars + taker_fees_dollars + maker_fees_dollars` da ordem.
  **Decisão do Feca, 30/10/2026 (s435):** é a mesma régua da Polymarket (decisões de
  05 e 06/10/2026, `CASA_POLYMARKET §11` e `§16`). Duas casas de predição medindo ROI
  por réguas diferentes enganariam a comparação entre tipsters que operam nas duas.
- **A taxa fica registrada à parte, só como informação**, para a tela poder mostrar
  "das quais US$ X em taxas". Ela **não** é somada de novo em custo nenhum: já está no
  P/L pela stake. Cenário da decisão: a alternativa (taxa fora da stake, como custo)
  obrigaria a reescrever o histórico inteiro da Polymarket.
- Campos em dólar já vêm como string decimal (`"18.770940"`). Os campos inteiros com
  sufixo `_cents` (depósitos) são centavos.
- Grava a origem em USD (`moeda`, `stake_orig`, `cotacao`) e a stake em R$, como a
  Polymarket.

---

## 11. Odds

- **L / aberta:** `odd = cotas ÷ stake` (o que paga se acertar, com a taxa na stake).
- **W:** `odd = retorno ÷ stake`.
- A odd da tela (`1 ÷ preço`) só coincide quando a taxa é zero. Na amostra: preço
  US$ 0,081 dá 12,35 na tela, e a odd gravada é **11,5995**.
- Vírgula, precisão completa, sem arredondar.

---

## 12. Descrição / ruído

- Simples: `Evento - Mercado: Escolha`, com o título do mercado (`Ja Morant: Double
  Double`) e o título do jogo do evento. Lado `no` vira `Não: <mercado>`.
- Combo: ver §16.
- Texto em inglês, verbatim. Não é print: não há ruído visual.

---

## 13. Pegadinhas

- **Esporte vem do `tags` da série** (`Basketball` → Basquete). Série sem tag de esporte
  (`category` diferente de `Sports`: política, economia, clima) cai em `Outro`.
- **Combo tem série própria e SEM tag** (`KXMVECROSSCATEGORY`, `category: Exotics`):
  o esporte sai das séries das **pernas**, nunca da série do combo.
- O saldo se divide por `exchange_index` (`balance_breakdown`). O total é
  `balance_dollars`; o campo `balance` é inteiro em centavos e **trunca**
  (27965 contra 279,6515).
- `revenue` e `value` do settlement são inteiros; `*_dollars` são string decimal. Nunca
  misturar os dois sem conferir a unidade.
- A doc de autenticação não cita escopo de chave; a tela de criação cita (§2.2).

---

## 14. Validações

> **Transversais (todas as casas):** ver `MASTER_PIPELINE §8` + `MASTER_OUTPUT §17–§18`.

- Toda linha tem Código (`order_id`). Sem código é falha de coleta.
- Stake já em BRL na coluna; o USD fica só na origem.
- **Trava da Caixa (§17):** depósitos − saques − stakes + retornos tem de dar o
  `balance_dollars`. Não fechou: o sync avisa e não esconde.

---

## 15. Exemplos golden

> Conta do Feca, 30/10/2026. Valores em **USD** (a coluna Stake recebe o BRL pelo PTAX
> do dia).

| Data | Esporte | Aposta | Descrição | Stake (US$) | Odd | Res | Código |
|---|---|---|---|---|---|---|---|
| 29/10/2026 | Basquete | Múltipla | Memphis vs Portland - Ja Morant: Double Double // Ja Morant: 10+ assists | 19,9785 | 11,5995 | L | 01a18a7b-b308-7092-9090-73f505ebce19 |

Conferência: 231,74 cotas a US$ 0,081 = 18,77094 + taxa 1,20756 = **19,9785**. Odd =
231,74 ÷ 19,9785 = **11,59946…**. Depósito 299,63 − 19,9785 = **279,6515**, igual ao
`balance_dollars`.

> Só um golden por enquanto: a conta tem uma aposta. Faltam W simples e simples L.

---

## 16. Combos (aposta combinada)

A Kalshi vende combo como **um mercado só**, da série `KXMVECROSSCATEGORY`, com as pernas
em `mve_selected_legs` (`event_ticker`, `market_ticker`, `side`).

- **Código, stake, odd e resultado:** iguais aos da simples (§3, §10, §11, §5). O combo é
  um contrato que paga US$ 1,00 se todas as pernas acertarem.
- **Aposta = `Múltipla`** sempre.
- **Esporte** (`MASTER_ESPORTES §2`): o das pernas quando é o mesmo jogo (bet builder);
  `Múltiplos` com esportes diferentes ou 3+ jogos diferentes.
- **Descrição:** o jogo, depois as pernas pelo título do mercado de cada uma, unidas por
  ` // `. Perna com `side: no` leva `Não: `.
- O `title` do mercado combo (`yes Ja Morant,yes Ja Morant: 10+`) **não** serve de
  descrição: é o `yes_sub_title` das pernas colado por vírgula, sem o mercado.
- Cada perna custa um `GET /markets/{ticker}` e um `GET /series/{s}`. Os dois são dados
  fixos depois de criados: cacheie por ticker entre syncs (`CLAUDE.md`, "API externa por
  item").

---

## 17. Caixa Inteligente automática

Mesmo desenho da Polymarket (`CASA_POLYMARKET §17`): a cada Sincronizar a Caixa confronta
o Sharpen com a conta.

- **Depósito / saque** = `/portfolio/deposits` e `/portfolio/withdrawals`, gravados em
  `caixa_mov` com `ref` = `id` do movimento (o sync regrava sem duplicar). Só
  `status: applied` conta.
- **Saldo observado** = `balance_dollars`.
- **Inicial** = 0 no 1º dia da conta: o extrato de depósitos traz tudo.
- **Medido em 30/10/2026:** 1 depósito (US$ 299,63) − 1 aposta perdida (US$ 19,9785) =
  US$ 279,6515, diferença **US$ 0,0000**. Isso só fecha porque a taxa está na stake
  (§10).
- **Não medido:** `fee_cents` de depósito diferente de zero, saque, e transferência
  entre `exchange_index`.
