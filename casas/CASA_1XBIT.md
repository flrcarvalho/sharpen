# CASA_1XBIT
## Camada de tradução — 1xBit → padrão global (FDC Capital)

> **Esta é a camada FINA.** Ela só descreve o que a 1xBit faz de diferente. Cálculo, resultado,
> descrição e output são **globais** — `global/MASTER_*`. Arquivo de casa **traduz**, nunca
> redefine regra global (invariante 2 do `CLAUDE.md`).
>
> **Espelho da 1xBet** (§1.2): o corpo deste arquivo é o da [`CASA_1XBET`](CASA_1XBET.md), medido
> lá, e o recon desta casa confirmou cada campo. Base da medição aqui: **8 bilhetes** na conta (`BetsSummaryInfo.Count`, 12 meses), os 8 na fixture e os 8 cards conferidos na tela, **todos perdidos**. Ganho, aberta, anulada e sistema **não foram vistos nesta casa**: valem os da 1xBet e das outras espelho.

---

## 1. Identidade

- **Marca:** `1xBit` · **domínio:** `1xbit1.com` (o do recon, 06/10/2026). ⚠️ **Roda em espelho
  numerado** (`1xbit1.com`, `1xbit2.com`…), por isso a casa fica fora do `CASA_HOSTS` do popup
  (domínio novo não trava). O `manifest.json` injeta em `1xbit.com` e `1xbit1.com`: **espelho
  com outro número não recebe o inject no load**; o popup ainda o injeta na aba aberta.
- **Chave no sistema:** `1XBIT` → display `1xBit`
- **Motor:** o da **1xBet** (§1.2). Inject `extensor/x1_inject.js`, formatador `formatTicket1X`.
- **Grafia (s399):** a base não tinha nenhuma (medido em 06/10/2026, `parceiros` e `bilhetes`),
  então vale a da marca. ⚠️ **Uma letra da `1xBet`** (`1XBIT` × `1XBET`): escolha a casa **na
  lista** ao criar a conta.
- **Moeda:** **USDT** (§1.1). A casa é só cripto.

### 1.1 A MOEDA é da conta  ⭐

A API diz `CurrencyCode: "USDT"` em todo bilhete, e o bloco capturado leva `Moeda: USDT`
com o dinheiro rotulado na moeda da casa, nunca "R$".

- Cadastre a conta com a moeda **USDT** antes da 1ª captura
  ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)). Conta em real gera o aviso de
  contradição no `/salvar`; USD × USDT não (a casa não distingue, decisão do Feca, 04/10/2026).
- O bloco também leva `Carimbo de colocação: AAAAMMDDhhmmss` (São Paulo): é a data da cotação.

### 1.2 Espelho da 1xBet

Mesmo motor, provado no recon de 06/10/2026 com conta do Feca: `POST
/bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates`, corpo com `DateFrom`/`DateTo`/`Count`/
`CfView`/`PartnerId`, resposta `{BetInfos, BetsSummaryInfo}`, `BetStatus` 1/2/4. **Muda só o
caminho** (`/bethistory-api/Web/` no lugar de `/service/bethistory/`). Inject, formatador e robô
são os da 1xBet. Irmãs no mesmo caminho: SapphireBet, PariPesa, Megapari e 1xBit.

> **Ao mexer numa das cinco, rode o harness das cinco.**

> ⚠️ **SIGILO**, aplicado por analogia com as outras espelho (decisão do Feca de 03/10/2026
> para SapphireBet, PariPesa e Megapari; **a 1xBit não foi decidida nominalmente**): casa normal no seletor, mas **fora** de aviso ao
> grupo de testers, do `changelog.json` e da home. Nenhum passo desta casa roda
> `scripts/avisar_testers.py` (versão sai com nota genérica, `--so-changelog`).

---

## 2. Modo de ingestão e layout

**Captura por API — passivo + replay** (`x1_inject.js`, o MESMO da 1xBet, mundo MAIN).
O que segue nesta seção foi medido na 1xBet (s298) e o recon desta casa confirmou o
mesmo corpo e o mesmo JSON:

```
POST /bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates   (na 1xBet: /service/bethistory/)
```

- **Auth NÃO é só cookie, ao contrário da 1xBet** (medido ao vivo, s399). A chamada leva o header
  `x-auth` (mais `x-hd`, `x-app-n`, `x-svc-source`, `is-srv`, `x-requested-with`), e sem ele a
  casa responde **401**. O inject **aprende os headers da requisição real** e os reenvia no replay,
  então nada muda no código. É por isso que **a página de histórico tem de abrir antes** do
  robô: sem uma requisição real não há header para aprender.
- **O app guarda a referência do `fetch` no load.** Um gancho instalado depois do carregamento
  não vê a chamada; só o `document_start` do inject (ou um iframe ganchado cedo, como no recon)
  enxerga. Recarregar a extensão sem recarregar a aba da casa deixa a captura muda.
- **Uma chamada traz ABERTAS e FECHADAS juntas.** Não há aba nem filtro de estado a alternar —
  diferente da Novibet, que exigiu `result:null`.
- **O passivo FUNCIONA** (o `clone().text()` resolve; 34 de 34 no recon), ao contrário de
  Pitaco e Novibet.

### 2.1 Por que o replay é obrigatório

**A tela é estreita e nunca se alarga sozinha:** a página pede uma janela **fixa de ~5,2 dias**
e reconsulta **essa mesma janela a cada ~5 segundos**, para sempre. Um passivo perfeito
capturaria 91 bilhetes de 95 e pareceria completo. O replay pede **12 meses**.

**Não há paginação.** Não existe `skip`, `page`, `offset` nem cursor: os únicos controles são
`Count` e a janela.

### 2.2 ⚠️ TETO DE `Count` = 500, o que só esta casa tem (s399)

Medido ao vivo: `Count:500` passa e `Count:501` volta **HTTP 400**
`{"ErrorCode":25,"ErrorName":"InvalidArgument","ErrorMessage":"Requested count must be less or
equal 500"}`. O replay da 1xBet começava em `Count:1000` e **morria no primeiro pedido**: a
captura entregava só a janela da tela, sem acusar bilhete faltante.

O inject agora lê o teto **do texto da recusa** e passa a pedir nele; se o lote ainda vier menor
que o total, **parte a janela ao meio** e varre cada metade (até 20 níveis).

- **Fim autoritativo continua valendo:** `Count:3` devolveu 3 bilhetes e o
  `BetsSummaryInfo.Count` seguiu dizendo 8.
- **O filtro é por `BetDate`, inclusivo nas DUAS pontas:** `[ini, meio]` e `[meio, fim]`
  devolvem o bilhete colocado exatamente em `meio` duas vezes (medido: 6 + 3 = 9 para 8). A
  repetição sai por `BetId`; a fronteira nunca se perde.
- **Janelas de 365 e 730 dias passam** com `Count:500`: não há teto de janela.

**Não medido:** a profundidade real do histórico. A casa devolveu 95 em 365 dias, mas a conta
só tinha 95 — não se provou se existe corte mais atrás. `UseArchive: true` já vem no corpo da
própria página, então o arquivo morto está incluído.

---

## 3. Esporte — pt-BR, mas SUJO

A casa já escreve em português. **Duas sujeiras medidas**, e as duas quebram casamento exato:

| A casa escreve | Problema | Ler como |
|---|---|---|
| `Badminton ` | **espaço no fim** | `Badminton` |
| `Tenis de Mesa` | **sem acento** (o individual é `Tênis`, com) | `Tênis de Mesa` |

Demais, verbatim: `Futebol` · `Beisebol` · `Tênis` · `Vôlei` · `Basquete` · `Handebol` ·
`eSports` · `Críquete` · `Vólei de praia` · `Rúgbi` · `Artes Marciais` · `Dardos` ·
`Regras Australianas` · `Sinuca` · `Hóquei no gelo` · `Futebol Americano`.

> `eSports` → o Esporte global é **E-Sports** e a categoria de estatística é **E-Sports Props**,
> nunca `Player Props` (`MASTER_APOSTAS §6/§7`).

### 3.1 ⚠️ HOMÓGLIFOS CIRÍLICOS no dicionário da casa

**Esta casa mistura letras cirílicas em texto latino.** Medido na amostra real:

| Vem assim | Deveria ser | Onde |
|---|---|---|
| `Handiсap 1 (-2.5) Sets` | `Handicap` | `с` = U+0441, em 3 pernas |
| `Superсopa - Alemanha` | `Supercopa` | `с` = U+0441, num campeonato |
| `АС Lorient` | `AC Lorient` | `А` = U+0410 e `С` = U+0421, **num nome de clube** |

São **visualmente idênticos** ao latino e são strings **diferentes**. Nenhum mapa do §9, nenhum
`grep` e nenhuma comparação de descrição casaria com eles, e nada acusa — `АС Lorient` jamais
casaria com `AC Lorient` em dedup ou matching.

O `formatTicket1X` normaliza os homóglifos **só quando a string é predominantemente latina**,
para não mutilar um nome legitimamente cirílico (clube russo escrito em russo sobe verbatim,
pela mesma política de nunca title-casear nome de casa). O caso de harness varre **todos** os
blocos e falha se sobrar qualquer caractere cirílico.

---

## 4. Data

**A coluna `Data` usa `UnixGameStartDate`** — epoch em **segundos**, convertido para
America/Sao_Paulo.

Ele é **exatamente o maior `StartDate` das pernas em 91 de 91** bilhetes: a casa já entrega o
"evento mais recente" pronto, que é a convenção da coluna. Não é preciso derivar.

| Campo | O que é |
|---|---|
| `UnixGameStartDate` | evento mais recente do bilhete → **a coluna `Data`** |
| `BetDate` | colocação (vai no bloco como `Colocada:`) |
| `BetSettlingDate` | liquidação — **ausente ⇒ aposta em aberto** |
| `Events[].StartDate` | início de cada perna |

---

## 5. Status e Resultado

`BetStatus` só assumiu **três** valores em 95 bilhetes de 12 meses:

| `BetStatus` | Significa | Resultado global |
|---|---|---|
| `1` | em aberto (sem `BetSettlingDate`, com `PossibleWinSum`) | **vazio** (não liquidar) |
| `2` | perdida | `L` |
| `4` | ganha **ou anulada** — ver abaixo | `W` ou `V` |

### 5.1 ⚠️ A ANULADA NÃO TEM CÓDIGO PRÓPRIO — o enum não separa V de W

A aposta anulada vem como **`BetStatus: 4` (ganha)**, com o stake devolvido inteiro
(`WinSum == BetSum`) e `Coef == 1`. Medido: o bilhete `16001193` apostou R$ 10 e recebeu R$ 10.

**Quem lê o enum cru marca V como VITÓRIA e infla o P/L em toda anulação.**

> **A regra:** `BetStatus == 4` **e** `WinSum == BetSum` ⇒ **`V`** (`MASTER_RESULTADO §5.1.2`).
> Caso contrário, `W`.

É o **inverso exato da lição da Stake** (s257): lá o dinheiro não separava V de L e o enum tinha
de mandar; aqui o **enum não separa V de W e o dinheiro manda**. A generalização que vale para
casa nova: *antes de derivar resultado do enum, prove que o enum separa os casos* — o mesmo
teste que se faz no dinheiro.

**Enum fora de {1,2,4} sobe CRU** e não é liquidado. O bloco sempre emite
`Status (API): BetStatus=N` para isso.

**Não medido:** meia-liquidação (`HW`/`HL`) e cashout — não apareceram na amostra.

---

## 6. Boost / promoção

**Nenhum boost observado em 95 bilhetes.** Não há campo de boost no payload, e o `Coef` nunca
ficou acima do produto das pernas por promoção — nos 15 ganhos, `stake × Coef == WinSum` ao
centavo, o que não sobraria espaço para bônus por fora.

> Se aparecer boost, a regra global já cobre: em `W` a odd é **`Retorno ÷ Stake`**, que absorve
> qualquer promoção sozinha.

---

## 7. Cashout

**Não medido.** A requisição da própria página manda `CalculateSaleInfo: false` e
`OnlyBetsForSale: false`, então nenhum dado de venda antecipada chegou na amostra. Se aparecer,
vale a regra global: cashout ≠ stake → `W` com `Odd = Cashout ÷ Stake`; cashout = stake → `V`
(`MASTER_RESULTADO §5.1.2` e `§5.6`).

---

## 8. Bônus

**Não medido.** O corpo carrega um `BonusUserId` (que é o id da conta, não um bônus), e nenhum
bilhete da amostra trouxe freebet ou crédito promocional.

---

## 9. Mapa de mercados (1xBet → `Aposta` global)

> Vocabulário **próprio** da casa: **135 rótulos distintos em 271 pernas reais**. Os de baixo
> são os **confirmados nesta casa**. A classificação segue `MASTER_APOSTAS_2026 §3` e o
> princípio do §1: a categoria registra o **objeto** apostado, não o formato do mercado —
> exceto `Handicap`, que é categoria de primeira classe no MASTER.
>
> ⚠️ **`Total` nesta casa é AGNÓSTICO DE OBJETO — quem define é o ESPORTE.** `Total Acima de
> (1.5)` é gols no futebol, pontos no basquete, games no tênis e rounds no MMA. Nunca
> classificar `Total …` sem olhar o `SportName` da perna.
>
> ⚠️ Comparar sempre **normalizado**: há homóglifo cirílico e espaço final (ver §3.1).

### Transversais (qualquer esporte)

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `V1` · `V2` | ML | ✓ confirmado (vitória mandante / visitante) |
| `1X` · `2X` | Dupla Chance | ✓ confirmado |
| `Equipe 1 Vence` · `Equipe 2 Vence` | ML | ✓ confirmado (esportes sem empate) |
| `Handicap 1 (X)` · `Handicap 2 (X)` | Handicap | ✓ confirmado (35 pernas, 11 esportes) |
| `Handicap Europeu (1:0) V1` | Handicap | ✓ confirmado |
| `Handiсap 1 (-2.5) Sets` | Handicap | ✓ confirmado ⚠️ **`с` cirílico** — ver §3.1 |
| `Se Qualifica - Equipe N` | ML | ✓ objeto = avanço na competição |

### Futebol

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `Total Acima de (X)` · `Total Abaixo de (X)` | Gols | ✓ confirmado |
| `Total Individual 1 Acima de (X)` · `Total Individual 2 Abaixo de (X)` | Gols | ✓ total do time; objeto = gol |
| `Equipe 1 Total Acima de X no 75° Minuto` | Gols | ✓ confirmado (67 pernas) — o minuto é **forma**, não objeto |
| `Total Acima de 3.5 no 75º Minuto` | Gols | ✓ confirmado ⚠️ note o `º` (masculino) contra o `°` (grau) do rótulo acima |
| `Primeiro a Fazer (2) Gols - Nenhuma Equipe` | Gols | ✓ Race → `MASTER_APOSTAS §Race` |
| `Primeiro a Fazer (5) Escanteios Equipe 1` | Escanteios | ✓ confirmado |

### Tênis · Badminton · Tênis de Mesa

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `Total Acima de (X)` · `Total Abaixo de (X)` | Games | ✓ confirmado (linhas de 17,5 a 23,5 = games) |
| `Total Individual N Acima de (X)` | Games | ✓ games do jogador |
| `Total de Sets Acima de (2.5)` | Sets | ✓ confirmado |
| `Tie Break - Sim` | Sets | ✓ objeto = o set (o tie break decide um set) |

### Basquete · Vôlei · Vólei de praia · Handebol · Rúgbi · Regras Australianas · Futebol Americano

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `Total Acima de (X)` (basquete, vôlei, rúgbi, aussie) | Pontos | ✓ confirmado |
| `Total Acima de (X)` (handebol) | Gols | ✓ objeto do handebol é gol |
| `Total Individual N` (basquete, hóquei, rúgbi, FA) | Pontos | ✓ total do time |

### Artes Marciais

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `Total Abaixo de (1.5)` · `Total Acima de (X)` | Rounds | ✓ confirmado (o objeto do MMA é o round) |

### Beisebol

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `Equipe N Total de Batidas Acima de (X)` | Team Props | ✓ total do time (`Team Totals`) |
| `Maioria Das Rebatidas - Equipe N` | Team Props | ✓ confirmado |
| `Total de Batidas Abaixo de (14.5)` | Team Props | ⚠️ total do JOGO, não do time — classificação a confirmar com o Feca |

### Críquete

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `1 - Over, Total de Runs da Equipe N Acima de X` | Corridas | ✓ `Runs` é sinônimo canônico |

### E-Sports

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `Duração do Mapa Acima de (X)` | E-Sports Props | ✓ `Map / Series Total` |
| `Equipe N, Frags, Total Abaixo de (X)` | E-Sports Props | ✓ frags = kills |
| `Primeiro a Fazer (10) Frags - V2` | E-Sports Props | ✓ confirmado |
| `Handicap Equipe N (X) Frags` | Handicap | ✓ formato handicap manda (categoria de 1ª classe) |

### Dardos

| 1xBet exibe | Aposta global | Status |
|---|---|---|
| `180s do Jogo Jogador N Acima de (0.5)` | Player Props | ✓ estatística individual |

---

## 10. Stake

`BetSum`, como número, **em USDT** (`CurrencyCode: "USDT"`). **Os números do TSV são os da casa**, na moeda dela: quem converte para
R$ é o servidor, pela moeda da conta e pela cotação do dia da colocação (§1.1). Nunca a IA.

---

## 11. Odds

### 11.1 A odd exata é `Coef`, nunca `CoefView`

`CoefView` é **truncada, não arredondada**: `14.704694` vira `"14.704"` (arredondar daria
14,705). É o número que o card estampa — conferido contra a tela do operador:
`Cotação geral 7,722 · Possíveis ganhos R$ 1.390,03` ⇄ `Coef 7.7224`, `BetSum 180`,
`PossibleWinSum 1390.03`. **Odd nunca truncada** é regra primordial.

### 11.2 ⚠️ O `Coef` do bilhete MENTE na PERDIDA

Quando uma perna é anulada, a casa:

- **recalcula** o `Coef` se o bilhete **ganhou** — 7 de 7: `Coef` == produto das pernas, e
  `stake × Coef == WinSum` ao centavo;
- **não recalcula** se o bilhete **perdeu** — 9 de 9 ficam com o valor **pré-anulação**.

O bilhete `16101007` declara `Coef 8,607956` onde a estrutura real é `2,11 × 1 × 2,17 = 4,5787`
— quase o dobro. Ler o `Coef` cru poria odd inflada em **9 dos 66 perdidos** (13,6%).

> **A perna anulada se reconhece por `Coef == 1`.** Só 6 das 18 trazem
> `ReturnedBetEventReasonName` — **o texto da razão não serve de detector**.

**O gatilho da correção é a perna anulada, nunca a divergência sozinha.** Num bilhete perdido,
"Coef inflado por anulação" e "Coef turbinado por boost" são **indistinguíveis** (nos dois o
`Coef` fica acima do produto e não há dinheiro para arbitrar). Corrigir por divergência pura
destruiria uma odd de boost legítima.

A tolerância é de **1%**, e é folga de ponto flutuante, não de negócio: os 9 casos reais
divergem entre 47% e 311%, enquanto o produto em float erra na 7ª casa (o `16094935` dá
7,509859 contra 7,50986 declarado, e **não deve ser "corrigido"**).

### 11.3 Odd por resultado

| Resultado | Odd |
|---|---|
| `W` | **`WinSum ÷ BetSum`**, sempre (`MASTER_RESULTADO §2`) |
| `L` · `V` · aberta | odd **estrutural** — `Coef`, ou o produto das pernas quando o `Coef` está velho (§11.2) |

> O `Coef` declarado explica o retorno ao centavo em 15 de 15, mas diverge na 5ª casa
> (4,14164 × 4,14166667). **Regra global não se negocia por arquivo de casa** — em `W` vale o
> dinheiro, e "a casa não tem boost" nunca autoriza a exibida.

### 11.4 Retorno potencial não contamina o real

`PossibleWinSum` só existe em **aberta** e `WinSum` só em **resolvida** — medido em 10 / 15 / 66
sem interseção. **A vitória fantasma da VaideBet/Novibet/Betpix365 não é risco nesta casa.**
Ainda assim o bloco rotula o potencial explicitamente: o guarda custa nada e a casa pode mudar.

### 11.5 Sistema (`BetTypeId` 2) — medido na SapphireBet, s391

Não apareceu na 1xBet. `BetTypeName: "Sistema"`, `BetSystemType: 20203` (2 de 3). O bloco diz
`Tipo: Sistema (…)`, nunca múltipla.

- **Ganho:** a odd é `WinSum ÷ BetSum`, como todo `W` (o `88105563743`: 156,96 ÷ 60 = 2,616).
- **Perdido:** a casa pode mandar **sem `Coef`** (`CoefView: ""`, o `88092600919`). A odd fica
  **VAZIA**: o produto das pernas não é a odd de um sistema, e zero é uma odd que não existe
  (`CLAUDE.md`, "Zero não é ausência"). O P/L de `L` é `−stake` e não depende dela.

---

## 12. Ruído a ignorar

- `/service/LineFeed/*` e `/service/LiveFeed/*` — **feed de odds**, não bilhete. São as maiores
  respostas da página (`Get1x2_VZip`, ~77 KB, repetido a cada poucos segundos) e enganam quem
  procura a lista de bilhetes pelo tamanho.
- `/api/web/user/v1/bets/uncalculated` — só o **total exposto** em aberto (bate com
  `BetsSummaryInfo.UnsettledSum`). Redundante: o `bethistory` já traz as abertas.
- `/service/accountmanagementservice/v1/user/accounts` — saldo e id da conta.
- `CanPrint`, `Broadcasting`, `ChampImage`, `Opp1Images`, `StatId`, `GameKind` — irrelevantes.

---

## 13. Pegadinhas (resumo rápido)

1. **Anulada vem como `BetStatus: 4` (ganha).** Só o dinheiro (`WinSum == BetSum`) separa V de W.
2. **`Coef` fica pré-anulação em bilhete perdido.** Usar o produto das pernas quando há
   `Coef == 1` numa perna e a divergência passa de 1%.
3. **Homóglifos cirílicos** em mercado, campeonato e **nome de clube** (§3.1).
4. **`CoefView` é truncada**, não arredondada.
5. **`Total` é agnóstico de objeto** — o esporte decide (§9).
6. **A tela pede só ~5,2 dias**, para sempre. Sem replay, faltam bilhetes em silêncio.
7. **`Badminton `** com espaço final e **`Tenis de Mesa`** sem acento.
8. **Não há paginação** — só `Count` e janela. O fim é o `BetsSummaryInfo.Count`.
9. **Dinheiro em USDT**: o bloco leva `Moeda: USDT` e nenhum "R$" (§1.1).
10. **Sistema perdido pode vir SEM `Coef`**: odd vazia, nunca produto nem zero (§11.5).
11. **`Count` acima de 500 é HTTP 400** (§2.2): o inject recua para o teto e parte a janela.
12. **Header `x-auth` obrigatório** (§2): abra o Histórico de apostas antes de capturar.

---

## 14. Validações específicas

> **Transversais (dedup, TSV, arredondamento, colunas):** seguir
> [`global/MASTER_OUTPUT_2026.md §9`](../global/MASTER_OUTPUT_2026.md) — não repetir aqui.

Específico desta casa:

- [ ] Todo bilhete `BetStatus=4` com `WinSum == BetSum` saiu como **`V`**, não `W`.
- [ ] Nenhum bilhete com perna `Coef == 1` levou o `Coef` declarado como odd (salvo os ganhos,
      onde a casa já recalculou).
- [ ] Nenhum bloco carrega caractere cirílico.
- [ ] `Data` veio de `UnixGameStartDate`, não de `BetDate`.
- [ ] Bilhete aberto **não** emitiu linha `Retorno:` — só `Retorno potencial:`.
- [ ] Em `W`, a odd é `WinSum ÷ BetSum`.

**Gate executável:** `node extensor/harness/run.mjs 1xbit` (conferência comum em
`extensor/harness/x1_espelho.mjs`). Roda com o teto real (500) e com teto 3, que força a
partição da janela; 6 mutações do inject da s399 provadas. As regras herdadas seguem travadas
pelo caso da 1xBet.

---

## 15. Exemplos golden (bilhetes reais, recon de 06/10/2026, valores em USDT)

Fixture: `extensor/harness/fixtures/1xbit.bethistory.json` (8 bilhetes, só os campos que o
inject lê: sem id de conta, sem header).

| BetId | Situação | Stake | Odd correta | Resultado | Fonte |
|---|---|---|---|---|---|
| `88346311263` | acumulada perdida com perna anulada (desistência, `Coef` 1) | 24,50 | **8,9179** | `L` | json (card declara 33,175, pré-anulação) |
| `88345477545` | simples perdida, "Handiсap" cirílico | 50,00 | **2,1** | `L` | card |
| `88344024423` | simples perdida | 40,00 | **2,375** | `L` | card |
| `88343782199` | simples perdida | 25,00 | **2,75** | `L` | card |
| `88342809691` | acumulada perdida (3) | 20,00 | **25,13049** | `L` | card (`25.13`) |
| `88342710499` | acumulada perdida (3) | 20,00 | **17,4105** | `L` | card (`17.41`) |
| `88342557245` | acumulada perdida (3) | 20,00 | **31,455** | `L` | card |
| `88342462855` | acumulada perdida (3) | 20,00 | **11,85597** | `L` | card (`11.856`) |

---

## Feedback para a camada global / MODELO

- **O espelho pode mudar o PROTOCOLO sem mudar o JSON.** Mesmo caminho e mesma resposta das
  outras espelho, e ainda assim: header `x-auth` obrigatório e teto de `Count`. As docs das
  outras três copiaram a medição da 1xBet (`Count:5000` devolvendo 95) sem repeti-la no caminho
  `/bethistory-api/Web/`, e o teto pode existir nelas também. O inject agora cobre os dois casos.

---

VERSÃO: 2026
ATUALIZADO: 2026-10-06 (sessão 399, espelho da 1xBet, recon com conta do Feca)
