# CASA_1XBET
## Camada de tradução — 1xBet → padrão global (FDC Capital)

> **Esta é a camada FINA.** Ela só descreve o que a 1xBet faz de diferente. Cálculo, resultado,
> descrição e output são **globais** — `global/MASTER_*`. Arquivo de casa **traduz**, nunca
> redefine regra global (invariante 2 do `CLAUDE.md`).
>
> Reconhecida na **sessão 298**, pelo `tools/recon_casa.js` — **a primeira casa ligada sem
> ninguém aqui ter conta nela**. O payload veio de um tester; a sessão nunca saiu do navegador
> dele. Ver [`docs/GUIA_RECON_TESTER.md`](../docs/GUIA_RECON_TESTER.md).
>
> Base da medição: **91 bilhetes / 271 pernas** de uma conta real (21→26/08/2026), mais três
> consultas ao vivo de 365 dias (95 bilhetes). Tudo o que está abaixo foi **medido**; o que não
> foi, está marcado como não medido.

---

## 1. Identidade

- **Marca:** `1xBet` · **domínio regulado:** `1xbet.bet.br`
- **Chave no sistema:** `1XBET` → display `1xBet`
- **Motor:** **PRÓPRIO**. App Vue, API toda em `/service/` no host da casa. **Não é**
  Altenar/BIA, **não é** BetBy/sptpub, **não é** Kambi, **não é** BetConstruct, **não é**
  BlueBrown (Novibet). Inject próprio (`extensor/x1_inject.js`), formatador próprio.
- ⚠️ **A grafia `1xBet` já existia na base antes do registro:** 267 bilhetes e 1 conta (dono
  `arrudex`, conta `Eu`, `origem='import'`, todos sem `codigo_bilhete`). Grafia **única** — a
  varredura das 7 tabelas onde `casa` é texto não achou `1XBET`, `1x Bet` nem variante. O
  round-trip `_casa_display(_display_to_key("1xBet"))` fecha em identidade. Ver o aviso de
  mudança RETROATIVA em `docs/SHARPENUP_ARQUITETURA.md §5`.
- **`1xBet` é a única marca deste motor no sistema.** Se aparecer casa espelho (Melbet, 22bet
  e afins rodam o mesmo motor no mundo), **prove o motor antes** pelo padrão da Betfast: mesmo
  caminho de API, mesmos nomes de campo num payload real.

---

## 2. Modo de ingestão e layout

**Captura por API — passivo + replay** (`x1_inject.js`, mundo MAIN):

```
POST /service/bethistory/GetBetInfoHistoryWithSummaryByDates
```

- **Auth por COOKIE.** Não há `Authorization`. Os headers são só de canal (`accept`,
  `content-type`, `x-language`) — mas o inject **aprende de uma requisição real** mesmo assim,
  porque o **corpo** carrega `PartnerId`, `PartnerGroupId`, `Whence`, `CfView` e `BonusUserId`,
  que são do tenant e da conta.
- **Uma chamada traz ABERTAS e FECHADAS juntas.** Não há aba nem filtro de estado a alternar —
  diferente da Novibet, que exigiu `result:null`.
- **O passivo FUNCIONA** (o `clone().text()` resolve; 34 de 34 no recon), ao contrário de
  Pitaco e Novibet.

### 2.1 Por que o replay é obrigatório

**A tela é estreita e nunca se alarga sozinha:** a página pede uma janela **fixa de ~5,2 dias**
e reconsulta **essa mesma janela a cada ~5 segundos**, para sempre. Um passivo perfeito
capturaria 91 bilhetes de 95 e pareceria completo. O replay pede **12 meses**.

**Não há paginação.** Não existe `skip`, `page`, `offset` nem cursor: os únicos controles são
`Count` e a janela. Quando o lote volta menor que o total, o único movimento é **pedir um
`Count` maior** — o inject escala (1000 → 5000 → …) até alcançar.

**Fim autoritativo de verdade:** `BetsSummaryInfo.Count` é o total da **janela** e **não muda**
com o `Count` pedido. Medido ao vivo: `Count:10` devolveu 10 bilhetes e seguiu dizendo
`Count: 95`; `Count:1000` e `Count:5000` devolveram os 95. Isso distingue *"acabou"* de *"a
consulta encheu"* — exatamente o que o `Count` da Tivo **não** distinguia (s211), e por isso
aqui não é preciso o segundo eixo de varrer a janela para trás.

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

`BetSum`, em **reais**, como número (`150` = R$ 150,00). **Não há milésimos** (ao contrário da
KTO). Não há stake por linha — não apareceu bilhete de sistema na amostra.

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

**Gate executável:** `node extensor/harness/run.mjs 1xbet` — 12 conferências travadas contra o
payload real, com as 9 mutações da s298 provadas (cada uma quebra o caso).

---

## 15. Exemplos golden (bilhetes reais — captura por API, 21→26/08/2026)

| BetId | Situação | Stake | Odd correta | Resultado | Por que está aqui |
|---|---|---|---|---|---|
| `16108953` | ganha com perna anulada | 150,00 | **4,14166667** | `W` | a casa recalculou o `Coef`; a odd sai do dinheiro (621,25 ÷ 150) |
| `16101007` | perdida com perna anulada | 150,00 | **4,5787** | `L` | o `Coef` declarado diz 8,607956 — **pré-anulação** |
| `16061009` | perdida com **duas** anuladas | 150,00 | **2,375** | `L` | `Coef` 9,771938 → 4× a estrutura real |
| `16100981` | perdida com uma anulada | 120,00 | **7,74** | `L` | `Coef` 23,0652 → 3× |
| `16001193` | **anulada disfarçada de ganha** | 10,00 | **1** | `V` | `BetStatus=4`, `WinSum == BetSum` |
| `16119951` | perdida limpa | 150,00 | **14,704694** | `L` | guarda contra "corrigir" o que não está quebrado |
| `16131833` | em aberto | 180,00 | **7,7224** | *(vazio)* | `PossibleWinSum` 1390,03 confirmado no card (`7,722`) |

---

## Feedback para a camada global / MODELO

- **Lição nova, generalizável:** *antes de derivar resultado do ENUM, prove que o enum separa os
  casos*. O `MASTER` já pedia isso do dinheiro (lição da Stake, s257); esta casa mostra o mesmo
  defeito com os papéis trocados. Vale como par simétrico no livro de armadilhas.
- **Família de PII nova:** geolocalização em header (`x-location-latitude`/`-longitude`). Não é
  credencial e não é campo de identidade — escapava dos dois crivos do coletor de recon. Já
  corrigido em `tools/recon_casa.js` na mesma sessão.
- **Homóglifo cirílico** é uma classe de defeito que nenhuma casa anterior mostrou. Se aparecer
  em outra casa, o normalizador do `content.js` (`_latinX1`) é reusável como está.

---

VERSÃO: 2026
ATUALIZADO: 2026-08-26 (sessão 298 — nasce da 1ª captura reconhecida sem conta nossa)
