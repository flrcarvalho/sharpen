# CASA_MELBET
## Camada de tradução — MelBet → padrão global (FDC Capital)

> **Esta é a camada FINA.** Ela só descreve o que a MelBet faz de diferente. Cálculo, resultado,
> descrição e output são **globais** — `global/MASTER_*`. Arquivo de casa **traduz**, nunca
> redefine regra global (invariante 2 do `CLAUDE.md`).
>
> **Espelho da 1xBet** (§1.2), ligada **SEM recon de conta** (s420, 18/10/2026): ninguém aqui
> tinha conta na casa. Do §3 em diante, o corpo deste arquivo é o da
> [`CASA_1XBIT`](CASA_1XBIT.md) / [`CASA_1XBET`](CASA_1XBET.md), **medido lá, não aqui**. Nenhum
> número deste arquivo foi conferido num card da MelBet. A 1ª captura real é o recon: ver §16.

---

## 1. Identidade

- **Marca:** `MelBet` · **domínio:** `melbet.com` (responde do Brasil e serve `/br` e `/pt`,
  medido por fora em 18/10/2026). ⚠️ **A marca é conhecida por rodar em espelhos**, e o domínio
  da conta logada não foi medido: a casa fica **fora** do `CASA_HOSTS` do popup e **dentro** do
  `X1_ESPELHOS_MOVEIS` (s410), que registra o domínio novo e recarrega a aba sozinho.
- **Chave no sistema:** `MELBET` → display `MelBet`
- **Motor:** o da **1xBet** (§1.2). Inject `extensor/x1_inject.js`, formatador `formatTicket1X`.
- **Grafia (s420):** a da **BASE**, `MelBet` (1 conta do tester Jaao26, criada em 14/10/2026,
  1 bilhete lido de print). A marca no site escreve `MelBet` também; o bundle chama `Melbet`.
- **Moeda:** **não medida.** A única conta da base está em **BRL**, e a casa aceita real.

### 1.1 A MOEDA é da conta  ⭐

O bloco carrega a moeda que a API manda (`CurrencyCode`), nunca a que se supõe da casa:

- conta em **BRL** → bloco de sempre, com "R$", sem linha `Moeda:` (byte a byte o da 1xBet);
- conta em **USD/USDT** → `Moeda: <código>`, dinheiro rotulado na moeda da casa, e o
  `Carimbo de colocação: AAAAMMDDhhmmss` (São Paulo) que decide o dia da cotação.

Cadastre a conta com a moeda certa antes da 1ª captura
([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)): moeda do cru diferente da
conta gera o alerta no `/salvar`.

### 1.2 Espelho da 1xBet

O que foi **medido**, por fora e sem login (18/10/2026):

- `melbet.com` serve o MESMO app das quatro espelho medidas, o `sys-v3-host-app`
  (`sys-v3-host-app-static/Desktop/Melbet/entry-*.js`; SapphireBet e PariPesa servem
  `Desktop/Other`, Megapari `Desktop/Megapari`, 1xBit `Desktop/DefaultBit`);
- o código do único bilhete da base, `88772424445`, tem 11 dígitos: a mesma série de `BetId`.

O que é **inferido**: o caminho `POST /bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates`,
que é o das quatro do mesmo app. O `RX` do inject também casa o `/service/bethistory/` da
1xBet, então os dois caminhos capturam. Irmãs: 1xBet, SapphireBet, PariPesa, Megapari e 1xBit.

> **Ao mexer numa das seis, rode o harness das seis.**

> ⚠️ **SIGILO**, aplicado por analogia com as outras espelho (decisão do Feca de 03/10/2026
> para SapphireBet, PariPesa e Megapari; **a MelBet não foi decidida nominalmente**): casa normal
> no seletor, mas **fora** de aviso ao grupo de testers, do `changelog.json` e da home. A versão
> sai com nota genérica (`scripts/avisar_testers.py --so-changelog`).

---

## 2. Modo de ingestão e layout

**Captura por API — passivo + replay** (`x1_inject.js`, o MESMO da 1xBet, mundo MAIN). Tudo
nesta seção foi medido nas irmãs e **vale aqui por herança, até a 1ª captura provar**:

```
POST /bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates   (na 1xBet: /service/bethistory/)
```

- **Abra o Histórico de apostas ANTES de capturar.** O inject aprende da requisição real os
  headers (na 1xBit o `x-auth` é obrigatório, sem ele 401) e o corpo (`PartnerId`,
  `PartnerGroupId`, `BonusUserId` são da conta). Sem requisição real, o replay não tem o que
  copiar: o autodiagnóstico diz "hook ATIVO · respostas 0".
- **O app guarda a referência do `fetch` no load.** Recarregar a extensão sem recarregar a aba
  da casa deixa a captura muda (o `document_start` do manifest cobre `melbet.com`).
- **Uma chamada traz ABERTAS e FECHADAS juntas.** Não há aba a alternar.

### 2.1 Por que o replay é obrigatório

Na 1xBet a tela pede uma janela **fixa de ~5,2 dias** e a reconsulta a cada ~5 s. O replay pede
**12 meses**. **Não há paginação**: só `Count` e a janela, e o fim autoritativo é o
`BetsSummaryInfo.Count`.

### 2.2 Teto de `Count`: desconhecido, e coberto

A 1xBit recusa `Count` acima de 500 com HTTP 400 e o teto escrito no corpo. O inject lê o teto
da recusa e, se o lote ainda vier curto, **parte a janela ao meio**. O harness desta casa roda
com teto 500 **e** teto 3, então o caminho está provado para qualquer teto que a MelBet tenha.

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

`BetSum`, como número, **na moeda que a API manda** (`CurrencyCode`, §1.1). **Os números do TSV são os da casa**, na moeda dela: quem converte para
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

## 13. Pegadinhas (resumo rápido, herdadas das irmãs)

1. **Anulada vem como `BetStatus: 4` (ganha).** Só o dinheiro (`WinSum == BetSum`) separa V de W.
2. **`Coef` fica pré-anulação em bilhete perdido.** Usar o produto das pernas quando há
   `Coef == 1` numa perna e a divergência passa de 1%.
3. **Homóglifos cirílicos** em mercado, campeonato e **nome de clube** (§3.1).
4. **`CoefView` é truncada**, não arredondada.
5. **`Total` é agnóstico de objeto** — o esporte decide (§9).
6. **A tela pede só ~5,2 dias**, para sempre. Sem replay, faltam bilhetes em silêncio.
7. **`Badminton `** com espaço final e **`Tenis de Mesa`** sem acento.
8. **Não há paginação** — só `Count` e janela. O fim é o `BetsSummaryInfo.Count`.
9. **A moeda é a que a API manda** (§1.1): BRL sai com "R$", dólar sai com `Moeda:`.
10. **Sistema perdido pode vir SEM `Coef`**: odd vazia, nunca produto nem zero (§11.5).
11. **Teto de `Count`** desconhecido aqui; o inject recua e parte a janela (§2.2).
12. **Abra o Histórico de apostas antes de capturar** (§2).

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

**Gate executável:** `node extensor/harness/run.mjs melbet` (conferência comum em
`extensor/harness/x1_espelho.mjs`), com teto 500 e teto 3. ⚠️ **A fixture é EMPRESTADA da
PariPesa**, servida no endereço da MelBet: o caso trava a LIGAÇÃO (inject casa o caminho no
domínio da casa, replay varre, formatador sai igual), não os dados da MelBet.

---

## 15. Exemplos golden

**Nenhum bilhete da MelBet ainda.** O caso de harness usa os da PariPesa (recon de 03/10/2026,
valores em USDT, conferidos no card de lá):

| BetId | Situação | Stake | Odd correta | Resultado |
|---|---|---|---|---|
| `88194620599` | anulada (`BetStatus` 4, `Coef` 1, `WinSum` = stake) | 7,00 | **1** | `V` |
| `88194577145` | simples perdida | 8,40 | **2** | `L` |
| `88195014537` | múltipla perdida (2) | 10,00 | **12,9536** | `L` |
| `88237452875` | aberta | 5,20 | **2,08** | vazio (potencial 10,82) |

---

## 16. O que falta medir (a 1ª captura real é o recon)

Na primeira captura de um tester, conferir **contra o card da casa**, nesta ordem:

1. O autodiagnóstico do popup diz **respostas > 0**. Se disser 0 com a página de histórico
   aberta, o caminho da API é outro: abrir o F12 → Network e procurar
   `GetBetInfoHistoryWithSummaryByDates`.
2. O domínio da aba. Se não for `melbet.com`, o `X1_ESPELHOS_MOVEIS` já cobre; pôr o domínio
   no `_HOSTS_POR_CASA` (`app/captura.py`) e no manifest na versão seguinte.
3. A moeda que a API mandou × a da conta (alerta no `/salvar`).
4. Stake, odd e status de 3 bilhetes contra o card: um ganho, um perdido, uma múltipla.
5. Se houver perdida com perna anulada, o `Coef` pré-anulação (§11.2).
6. Salvar o payload como `extensor/harness/fixtures/melbet.bethistory.json` (sem id de conta)
   e trocar o caso do harness pelos bilhetes da casa.

---

VERSÃO: 2026
ATUALIZADO: 2026-10-18 (sessão 420, espelho da 1xBet, ligada sem recon de conta)
