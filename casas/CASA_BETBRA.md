# CASA_BETBRA
## Camada de tradução — Betbra → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betbra.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betbra`
- Domínio: `betbra.bet.br`
- Locale: pt-BR · Moeda: R$ prefixo, ponto de milhar, vírgula decimal (ex.: `R$1.000,00`)
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

> ⚠️ **A grafia canônica é `Betbra`, e ela foi MEDIDA antes de registrar** (s343, o aviso de
> mudança retroativa de `SHARPENUP_ARQUITETURA §5`): é a única grafia no banco em todas as
> tabelas onde `casa` é texto — 5 contas em `parceiros`, 158 bilhetes, 1 em `casas_meta`,
> 23 em `correcoes`, 1 em `uso_tokens`, 0 em `tipsters.casas`. **Não escrever `BetBra`**:
> `scripts/import_dashboard_xlsx.py` mapeia para essa grafia gêmea, mas ela nunca chegou ao
> banco — se chegasse, seria uma casa diferente para o sistema inteiro.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** captura por API (SharpenUp 0.7.11) — ver §2.5
- **FALLBACK:** screenshot / visão

### 2.2 Tipo do bilhete declarado

A casa não exibe rótulo de tipo confiável: o Sportsbook chama **todo** bilhete de
`single bet`, inclusive um cupom de 3 seleções. O tipo é inferido — ver §2.5 e §11.

---

### 2.5 Captura por API — DOIS ambientes, como na Bolsa de Aposta

A Betbra é a **mesma plataforma** da Bolsa de Aposta com outra marca. A casca `betbra.bet.br`
é Angular e **não faz uma única requisição de bilhete**; quem captura são os injects, dentro
dos iframes. Medido no navegador em 10/09/2026, lendo o `src` real de cada iframe:

| | Exchange | Sportsbook |
|---|---|---|
| rota da casca | `/b/exchange` | `/fbook` (redireciona para `/fbook/br-pt/spbkv4`) |
| iframe | `mexchange.betbra.bet.br/exchange` | `prod20454-176166310.msjxk.com/br-pt/spbk` |
| plataforma | LayBack / FulltBet (Next.js) | fornecedor próprio (Express) |
| sessão | **cookie** (é subdomínio do site), 0 parâmetros | **na URL**, 4 parâmetros, um deles o `operatorToken` |
| endpoint | `GET mexchange-api.betbra.bet.br/api/offers/reportsv2` | `GET <origem>/api/master/my-bets/history` + `/api/betslip/my-bets/open` |
| inject | `bda_inject.js` (o mesmo da Bolsa) | `bds_inject.js` (o mesmo da Bolsa) |
| formatador | `formatTicketBDA` | `formatTicketBDS` |
| ID | `id` — 7 a 8 dígitos | `TicketId` — 18 dígitos |
| paginação | `offset` / `per-page`, fim por `total` | `offset` / `limit`, fim por `totalCount` |
| volume medido | **403** ofertas (mai/2025 → set/2026) | **7** liquidadas + **3** abertas |

**Nada é próprio da Betbra na mecânica** — mesmas rotas de casca, mesmos injects, mesmo
`_bolsaMontarFaltantes`. O único registro que faltava era o `match` do manifest, que estava
preso em `*.bolsadeaposta.bet.br` e nunca subiria o `bda_inject` em `mexchange.betbra.bet.br`.
O Sportsbook já vinha coberto pelo curinga `*://*.msjxk.com/*`.

> ⚠️ **O prefixo do Exchange aqui é `mexchange.`, SEM número** (a Bolsa é `mexchange2.`).
> O guard do inject é `/^mexchange\d*\./i` e `\d*` aceita zero dígitos — passa, mas por
> sorte medida, não por desenho. Trocar por `\d+` mata a captura da Betbra em silêncio; o
> caso do harness trava isso.

**Séries de código são POR CASA, não por plataforma.** O Exchange da Betbra usa 7–8 dígitos
(`5393061` … `12567916`) e o da Bolsa usa 9. Mesma plataforma, contadores independentes:
**comprimento de código não diz de que casa o bilhete é**. Não há risco de dedup, porque
`casa` entra na assinatura.

**Janelas — as duas telas perguntam errado, e o replay existe para corrigir** (idêntico à
Bolsa, reconfirmado aqui): o Exchange recusa intervalo acima de **95 dias**
(`Max allowed interval is 95 days`, HTTP 400) e, **sem `status`, devolve só as liquidadas** —
aposta em aberto exige `status=matched,unmatched`. O Sportsbook não aceita `lastHours` como
número; **omitir o parâmetro** traz o histórico inteiro. A varredura completa de 3 anos custou
**29 chamadas, com zero erro**.

**A janela de dias do painel (`lookbackDias`) NÃO corta nesta casa.** O horizonte é fixo
(~3 anos) e o freio incremental é o `stopId`. A data escolhida no calendário da tela é
irrelevante para a captura: o robô fala com a API por conta própria.

---

## 3. ID do bilhete

- Caso: **visível**
- Formato **Exchange**: numérico, 7–8 dígitos (`12536715`) — série própria da casa, crescente
- Formato **Sportsbook**: numérico, 18 dígitos (`817057028597719041`)
- Na captura: `id` (Exchange) e `TicketId` (Sportsbook); o robô emite os dois como `[Código: …]`
- ⚠️ **No Sportsbook o card mostra OUTRO número.** A tela estampa o id da COMPRA
  (`PurchaseTicketID`), que é `TicketId − 1` — conferido na Betbra em 10/09/2026 no bilhete
  aberto `885271132847751169`, cujo card exibe `885271132847751168`. O `[Código:]` continua
  saindo do `TicketId` **de propósito**: `PurchaseTicketID` é da compra, e uma compra com
  duas apostas daria o mesmo número às duas — o UPSERT fundiria bilhetes distintos e um
  sumiria sem erro (incidente da s276). O bloco traz `ID no card da casa: …` para cruzar.
- Nunca vai no output; serve para dedup e auditoria (11ª coluna interna)

---

## 4. Data

- Fonte primária: **data do evento** — `event-start-time` (Exchange) / `Selections[].EventDate`
  (Sportsbook), ambos **UTC com `Z`** → converter para America/Sao_Paulo
- Fallback: data de colocação (`created-at` / `CreationDate`)
- Múltipla: data = evento da **perna mais recente** (regra global, `MASTER_OUTPUT_2026`)

> ⚠️ **Mercado `custom` do Exchange pode ter data de evento posterior à liquidação.** Medido
> no `7447879`: `event-start-time` 15/12/2025, `settled-time` 13/12/2025. O Criador de
> Eventos amarra o mercado a um evento de referência que nem sempre é o que decide a aposta.
> A regra da casa segue sendo o `event-start-time` (não estimar nada a partir da liquidação —
> `CLAUDE.md`, "data derivada por estimativa é dado inventado"), mas o caso está registrado.

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO:** nunca copiar o sinal visual. Traduzir sempre para `W · L · V · HW · HL`.

**Exchange** (`status`, texto) — contagem medida em **403 ofertas** da conta:

| Bruto | n | `profit-and-loss` | Nosso |
|---|---|---|---|
| `win` | 81 | presente (é LUCRO) | **W** (odd = `(stake+pl) ÷ stake`) |
| `lose` | 311 | `−stake` | **L** |
| `push` | 1 | **ausente** (não é zero) | **V** |
| `matched` | 9 | ausente | **aberta** |
| `failed` | 1 | ausente, e **sem `stake-matched`** | **nenhum — não é bilhete** |
| `flushed` · `unmatched` · `open` · `edited` · `delayed` | 0 | — | aberta (exceto `flushed`, que não é bilhete) |
| `push_win` · `push_lose` | 0 | — | **sobem crus** (a conferir) |

**Sportsbook** (`BetStatus`, enum numérico):

| Bruto | Badge na tela | Nosso |
|---|---|---|
| `2` | VENCEU | **W** (odd = `CurrentBetBalanceDecimal ÷ StakeDecimal`) |
| `1` | PERDIDO | **L** |
| `4` | CANCELADA | **V** — odd é o `ClientOdds`, **nunca** retorno÷stake |
| `0` / vazio | ABERTO | aberta |
| qualquer outro | — | sobe cru (a conferir) |

> ⚠️ **`GainDecimal` é o retorno POTENCIAL, sempre.** O bilhete `817057028597719041` traz
> `"230.5"` com `BetStatus: 1` (perdido). O realizado é `CurrentBetBalanceDecimal` = `"0"`.
> **E a coluna "Retorno" da tela do Exchange tem o mesmo defeito**: o `12536715` mostra
> `R$520,00` num bilhete **Perdeu**. Nos dois ambientes, o realizado sai do outro campo.

Apostas abertas → `extraction_state = aberta`.

---

## 6. Boost / promoção

- Tem boost: **sim, confirmado** (s343) — "ODDS TURBINADAS" / "Criador de Aposta Turbinado"
- No Sportsbook, `ClientOdds` já é a odd **COM** boost e `DbTrueOdds` da seleção agregada é a
  **SEM** boost. A tela risca a segunda e estampa a primeira: card do `885271132847751169`
  mostra `2.89 → 3.36`, e `ClientOdds` = `3.36`, `DbTrueOdds` da agregada = `2.89`.
- **A odd que vale é a `ClientOdds` do bilhete** — é ela que explica o dinheiro
  (200 × 3,36 = 672 = `GainDecimal` = "Retorno Total" da tela). A regra global de W
  (`retorno ÷ stake`) absorve o boost sozinha.
- A campanha aplicada aparece em `Campaigns[].Promotions[].Type` (`1` e `2` observados, com
  percentuais diferentes: 4,61/3,49 = 1,32 e 3,36/2,89 = 1,16). O percentual **não** se
  deduz do tipo — não usar isso para reconstruir odd nenhuma.

---

## 7. Cashout

- Tem cashout: **não confirmado** — aguarda amostra (`IsPartialCashOut: false` em 10 de 10)
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → `V`.

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — `FreeBet: null` em 10 de 10 bilhetes medidos
- O boost de odd (§6) **não** é freebet: o dinheiro apostado é real.

---

## 9. Mapa de mercados (Betbra → `Aposta` global)

> Camada fina: aqui só o que **esta casa** confirma. A lista de categorias vive no
> `MASTER_APOSTAS_2026 §3`; mercado sem categoria global → `Outros` + registrar no §Feedback.

| Betbra exibe | Aposta global | Status |
|---|---|---|
| `Resultado Final 1x2` | ML | ✓ confirmado |
| `Resultado do 1º Tempo` | ML | ✓ confirmado |
| `Total de Gols Acima/Abaixo` · `Primeiro Tempo Total de Gols Acima/Abaixo` | Gols | ✓ confirmado |
| `Vencer Algum Tempo` | ML | ✓ confirmado |
| `<Time>: Não sofrer gol no 1º Tempo` | Team Props | ✓ confirmado |
| `Total de chutes na partida` | Chutes | ✓ confirmado |
| Mercado `custom` do Criador de Eventos (Exchange) | seguir o nome → MASTER_APOSTAS | ✓ confirmado |

**Notas de reconstrução:**

- Confronto: a casa exibe `Time A vs Time B` → normalizar para `[Time A v Time B]` (sem "s").
- **Os nomes bons estão em `Translations`.** O nível de cima vem em inglês/interno
  (`EventName: "America MG vs CEFAT Tirol"`, `LineTypeName: "1X2"`); a tela mostra
  `Translations.*`, em pt-BR e com acento (`América MG`).
- ⚠️ **Seleção `Não` NEGA o mercado — não é o mercado.** Vale para todo mercado booleano do
  Exchange (`runner-name`) e do Sportsbook: `Não` + `Ambas Marcam` → `Ambas Não Marcam`;
  `Não` + `Over X` → `Under X`. Os formatadores já sobem a seleção rotulada.
- **`Mais de X` / `Menos de X` → `Over X` / `Under X`**: padrão global, `MASTER_DESCRICAO_2026 §11`.
- **Cupom de mesmo jogo (Criador de Apostas)**: as N seleções vão separadas por ` // `, o
  separador único de seleção (`MASTER_DESCRICAO`). Ver §11.

---

## 10. Stake

- Exchange: `stake-matched` — ⚠️ **nunca `stake`**: a oferta `failed` traz `stake: 26` com
  risco zero, e ler o campo errado lança uma aposta que não existiu
- Sportsbook: `StakeDecimal` (string com **ponto** decimal: `"50"` → R$ 50,00)
- Na tela: "Aposta" (Exchange) / "Aposta Total" (Sportsbook)

---

## 11. Odds

| Resultado | Regra da odd |
|---|---|
| W | `retorno ÷ stake` — Exchange: `(stake + profit-and-loss) ÷ stake`; Sportsbook: `CurrentBetBalanceDecimal ÷ StakeDecimal` |
| L | odd estrutural (`avg-decimal-odds-matched` / `ClientOdds`) — nunca `0,00` |
| V | odd estrutural — nunca `1,00` (no cancelado a stake volta e o quociente daria 1,00) |
| aberta | odd estrutural |
| HW / HL | aguarda amostra |

- ⚠️ **`profit-and-loss` é LUCRO, não retorno.** Retorno = `stake + pl`.
- Exchange: a odd efetiva é `avg-decimal-odds-matched` (a MÉDIA do que casou), não
  `decimal-odds` (a pedida). Nas 403 ofertas as duas coincidem — todas casaram integralmente —
  mas em casamento parcial elas divergem por natureza e manda o que casou.
- Precisão: preservar — não truncar nem arredondar (`MASTER_RESULTADO_2026`).

### 11.1 ⚠️ Cupom de mesmo jogo: `Selections` NÃO é a lista do que foi apostado

**Esta é a armadilha própria da Betbra, e ela não produz erro nenhum.** No Criador de Apostas
(bet builder) o Sportsbook manda, dentro de `Selections`:

1. as **pernas soltas**, cada uma com a odd de **mercado** dela — que não foi apostada;
2. uma entrada **agregada** do cupom (`MarketTypeId: "QA0"`), com a odd do **conjunto** e os
   textos das pernas concatenados por ` | `.

Quem diz o que entrou na aposta é **`MappedSelections`**, uma lista de índices. Iterar tudo
transforma UMA aposta de 4,61 numa múltipla de 26,72 (1,13 × 2,30 × 2,23 × 4,61) — e o P/L
continua certo, porque a odd do bilhete vem de outro campo. Errariam só turnover, ROI e a
assinatura de stake do matcher, exatamente como em "a stake que era do vizinho" (s311).

Medido em **10 de 10** bilhetes desta conta: a odd do bilhete bate com o produto das
**mapped** em 10/10 e com o produto de **todas** em 0/10.

- **A ordem das pernas vem do texto agregado, não do array.** Conferido no card: o array traz
  `[América MG, Mais de 3.5, Mais de 1.5]` e o agregado traz `América MG | Mais de 1.5 |
  Mais de 3.5` — o `SelectionId` da agregada é `0VS0|2|1`, os índices na ordem impressa.
- **A perna de um cupom não tem odd própria** no output: a casa precifica o conjunto.
- Tipo no bloco: `Criador de Apostas (bet builder — N seleções do MESMO jogo, odd única do
  cupom)` — **nunca** "Múltipla", que sugere jogos diferentes e odd composta.

> Na Bolsa de Aposta `MappedSelections` é sempre `[0]` com uma seleção só: lá as duas leituras
> coincidem, e é por isso que o defeito atravessou o recon dela sem aparecer. Fonte canônica:
> `_selecoesApostadas` / `_pernasDoCupom` (`extensor/bds_inject.js`).

---

## 12. Ruído a ignorar

Cabeçalhos de coluna (`Data Liquidada`, `Descrição`, `Tipo`, `Odd Back`, `Odd Lay`, `Aposta`,
`Responsabilidade`, `Retorno`, `Lucro / Perda`, `Estado`) · `Apostas a favor` / `Aposta a favor`
(tipo de aposta — informacional) · `Login ID: …` (id da conta, não do bilhete) · `Repetir seleções`
· `Compartilhar` · selo `ABERTO` · `ODDS TURBINADAS` / `Criador de Aposta Turbinado 25%`
(slogan promocional) · o aviso `Esteja ciente que o valor das cotas … arredondado até a
precisão de 0.01`

---

## 13. Pegadinhas (resumo rápido)

- **`Selections` traz seleções que não foram apostadas** — `MappedSelections` manda (§11.1).
- **`GainDecimal` é potencial, inclusive em perdida**; e a coluna "Retorno" da tela do
  Exchange também (R$ 520,00 num bilhete Perdeu). O realizado é `CurrentBetBalanceDecimal` /
  `stake + profit-and-loss`.
- **`ClientOdds` já é a odd boostada**; `DbTrueOdds` é a sem boost. Não somar boost duas vezes.
- **O card do Sportsbook estampa `TicketId − 1`** (§3).
- **`push` vem sem `profit-and-loss`** — ausente, não zero. Zero não é ausência.
- **`failed` não é bilhete** — oferta que nunca casou, sem `stake-matched`.
- **`mexchange.` sem número** (§2.5).
- **Séries de código são por casa**, não por plataforma: 7–8 dígitos aqui, 9 na Bolsa.
- **`Odd Lay` vem `--`** em 403 de 403: a conta só tem `back`. `lay` inverte o L/P e **não há
  amostra** — se aparecer, o lado sobe explícito no bloco e a leitura não deve assumir "a favor".

---

## 14. Validações específicas

- W: conferir `(stake + pl) ÷ stake ≈ odd` (Exchange) e `retorno ÷ stake ≈ ClientOdds` (Sportsbook)
- L: `pl = −stake` (Exchange) · `CurrentBetBalanceDecimal = 0` (Sportsbook)
- V: stake devolvida · odd nunca `1,00`
- Cupom: nº de seleções no bloco = nº de segmentos do texto agregado; o separador ` | ` da
  casa **não** pode sobrar dentro de uma linha de seleção
- Nenhum bilhete com `stake` ou `odd` igual a 0 (`validar_linhas` recusa na fronteira)

---

## 15. Exemplos golden (bilhetes reais)

Fixtures do harness (payload real, anonimizado): `extensor/harness/fixtures/betbra.reportsv2.json`,
`betbra.sportsbook.json`, `betbra.sportsbook_open.json`. Gate: `node extensor/harness/run.mjs betbra`.

| Ambiente | Código | Cruzado com a tela |
|---|---|---|
| Exchange | `12515190` | Odd Back 5.80 · Aposta R$100,00 · Retorno R$580,00 · Lucro R$480,00 · **Ganhou** |
| Exchange | `12536715` | Odd Back 13.00 · Aposta R$40,00 · Retorno R$520,00 · Perda −R$40,00 · **Perdeu** |
| Exchange | `7447879` | `push` sem `profit-and-loss` → **V** |
| Exchange | `12567916` | `matched` — aposta viva, sem L/P e sem Retorno |
| Sportsbook | `817057028597719041` | 3 pernas · odd 4,61 · **Perdido** · card mostra `…040` |
| Sportsbook | `885271132847751169` | 3 pernas · `2.89 → 3.36` · Aposta Total R$200,00 · Retorno Total R$672,00 · **ABERTO** · card mostra `…168` |

---

## Feedback para a camada global / MODELO

- **Cupom de mesmo jogo com entrada agregada no mesmo array das pernas** é um formato que
  vale procurar em outras casas de bet builder: o sintoma é uma seleção cujo texto contém o
  separador da casa e cuja odd é a do bilhete inteiro. Família de "linha bem-formada pode ser
  de OUTRO bilhete" — aqui, de outro NÍVEL do mesmo bilhete.
- **Não provado nesta casa** (medido, não suposto): `lay`, cashout/Retirada, freebet,
  `push_win`/`push_lose` (HW/HL), casamento parcial no Exchange, `MappedSelections` com 2+
  índices (múltipla de eventos diferentes), e `market-type` diferente de `custom` no Exchange.
