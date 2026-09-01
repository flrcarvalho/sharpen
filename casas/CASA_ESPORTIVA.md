# CASA_ESPORTIVA
## Camada de tradução — Esportiva → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Esportiva.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> ⭐ **CASA ESPELHO DA VAIDEBET.** As duas rodam o **mesmo motor Altenar/BIA**, no **mesmo host de gateway** e no **mesmo endpoint** — o que as separa é o `integration` do corpo (`esportiva` × `vaidebet`). Elas compartilham `extensor/vb_inject.js`, `formatTicketVB` e `roboVBPassive`, sem uma linha de código duplicada. **Toda pegadinha registrada em [`CASA_VAIDEBET.md`](CASA_VAIDEBET.md) vale aqui**, e vice-versa: quem mexer numa das duas mexe nas duas. O que este arquivo traz de próprio é o que foi medido **nesta** conta.

---

## 1. Identidade

- Casa canônica: `Esportiva` · site: `esportiva.bet.br`
- ⚠ A **marca** escreve `EsportivaBet` (logo) e `Esportiva Bet` (título da página). A canônica do sistema é **`Esportiva`** porque **a base manda**: em 09/08/2026 havia **351 bilhetes**, **2 contas** e **4 perfis de tipster** nessa grafia. Adotar o nome da marca custaria recálculo de assinatura em todas elas (`SHARPENUP_ARQUITETURA §5`).
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `currency: "BRL"`
- **Decimal exibido na tela: PONTO** (`1.65`, `R$30.00`) → normalizar para vírgula.
- Motor: **Altenar / BIA** (`biahosted.com`), embutido num site Nuxt próprio. O histórico é um widget do motor, mas roda no **frame de topo** (o `origin` da requisição é `esportiva.bet.br`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Como reconhecer outra casa deste motor sem login:** a home carrega `sb2frontend-altenar2.biahosted.com` / `sb2wsdk-cdn-altenar2.biahosted.net` com `integration=<marca>` na query. Foi assim que a Esportiva foi confirmada como espelho **antes** de qualquer credencial (mesmo método do BetBy em `betby_plataforma_espelho`).

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js` — o **mesmo** da VaideBet).

```
POST https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory
{"culture":"pt-BR","timezoneOffset":180,"integration":"esportiva","deviceType":1,
 "countryCode":"BR","dateFrom":"…Z","dateTo":"…Z","liveOnly":false,"numFormat":"en-GB",
 "pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}
→ {"isLastPage":false,"bets":[…]}
```

O host do gateway é **idêntico** ao da VaideBet — não é um cluster por marca. É isso que torna o espelho seguro: o `RX` do inject casa por **PATH** (`/widgetExpandedBetHistory`) e o arquivo não cita host nenhum.

Quatro consequências que mandam no desenho (as mesmas da VaideBet, reconfirmadas aqui):

1. **O endpoint é de OUTRA origem** (`biahosted.com`) e autentica por header **`Authorization: Bearer <JWT da sessão>`**, não por cookie. O replay tem de reusar os headers exatos da requisição que a página fez.
2. **A lista NÃO carrega sozinha:** vem de 10 em 10 e a tela tem o botão **"Mostrar mais apostas"**. O robô não usa o botão — pagina por `pageNumber` na própria API. **Provado ao vivo nesta conta (s254):** `pageNumber:2` devolveu 10 ids novos, nenhum repetido, ainda com `isLastPage:false`.
3. **As abas são o array `statuses` do corpo**, mesma URL — e são as mesmas cinco da VaideBet:
   - **Processado** (resolvidas): `[1, 8, 2, 4, 18]`
   - **Aberto**: `[0, 10, 3, 20, 17]`
   A tela ainda mostra os filtros `Ganho`, `Perdida` e `Cashout`, que são recortes dos mesmos estados. O robô varre as duas abas a cada rodada, partindo de qualquer uma que o operador tenha aberto.
4. **Fim autoritativo: `isLastPage: true`.** Sinal explícito da casa — nada de heurística por rolagem.

**Janela de datas:** `dateFrom`/`dateTo` são nativos do corpo (a tela expõe os dois como campos de data no topo direito). As **resolvidas** respeitam os dias pedidos no popup; as **abertas** vão com janela larga de propósito.

### 2.2 Tipo do bilhete declarado

O card não rotula "Simples/Múltipla". O tipo sai da estrutura:

- `selections.length ≥ 2` → **Múltipla**;
- 1 seleção com `isBetBuilder: true` → **Bet Builder** (pernas em `bbOdds[]`, todas do mesmo evento) — o bloco escreve `Bet Builder (mesmo jogo · N seleções)`;
- 1 seleção sem `bbOdds` → **Simples**.

> A amostra desta conta (13 bilhetes, 09/08/2026) tem **simples e bet builder de 2 pernas**. Múltipla de jogos diferentes **nunca foi vista aqui** — o formato aguenta (coberto pelo caso sintético do harness da VaideBet), mas não há amostra.

### 2.3 Layout do bilhete

Cards em **grid de até 4 colunas** (mais denso que o da VaideBet), com faixa colorida de status no topo (`ABERTO` / `GANHOU / VENCIDO` / `PERDIDO`) e rodapé cinza com `DD/MM • HH:MM` **da colocação** + `ID: …`. Vêm **colapsados**: só o cabeçalho e o rodapé aparecem até o operador ligar o toggle **"Expandir tudo"**.

**Não** há linha em branco entre bilhetes — por isso a casa nunca pode cair no robô de texto genérico (`roboScroll`), que parte o `innerText` por linha em branco (lição da KTO, s192). O colapso agrava: no estado padrão o DOM nem tem odd, stake ou retorno.

---

## 2.5 Campos da API (o que o inject entrega)

Idênticos aos da VaideBet — ver [`CASA_VAIDEBET §2.5`](CASA_VAIDEBET.md) para a tabela completa. Os que esta amostra confirmou um a um contra o card:

| Campo (API) | Significado | Observação |
|---|---|---|
| `id` | ID do bilhete | é o `ID:` do rodapé do card · chave de dedup e do `[Código:]` |
| `status` | estado do bilhete | enum bruto — ver §5 |
| `createdDate` | **colocação**, ISO **UTC** (`…Z`) | converter para America/Sao_Paulo · **não** é a coluna Data (ver §4) |
| `selections[].eventDate` | início do evento, ISO UTC | a **mais recente** vira a coluna Data |
| `totalStake` (= `unitStake` = `finalStake`) | **stake** | unidade normal (`124.0` = R$ 124,00) — **não** há milésimos |
| `totalWin` | retorno | ⚠ **na aberta é POTENCIAL e já vem preenchido** — ver §5 |
| `openStake` / `remainingTotalWin` | só existem em bilhete **aberto** | reforço para distinguir aberta de resolvida |
| `totalOdds` | **odd total, já boostada** | precisão completa; a tela trunca o riscado — ver §11 |
| `selections[].boostedSelection.preBoostedPrice` | odd **antes** do boost | é o número riscado do card · nunca é a odd válida |
| `selections[].bbOdds[]` | pernas do **bet builder** | `marketName` + `oddName` + `status` por perna |
| `selections[].eventScore` | **placar** (`"0:2"`) | vem preenchido inclusive em bilhete ao vivo |
| `selections[].gameTime` | minuto do jogo (`"60'"`) | só em bilhete ao vivo — não existe na VaideBet documentada |
| `selections[].isLive` | aposta feita **ao vivo** | as 3 abertas da amostra são live |
| `selections[].sportTypeId` | esporte, **só o id** | `1` = `Futebol` (único visto aqui) — ver §12 |
| `cashOutValue` / `partialCashOut` | cashout | **0 em 100% da amostra**, inclusive com botão ativo — ver §7 |
| `isLastPage` (raiz) | **fim autoritativo** da paginação | |

---

## 3. ID do bilhete

- Formato: **numérico, 10 dígitos** (ex.: `5277832732`), exibido no rodapé do card como `ID: 5277832732`.
- Mesmo espaço de IDs da VaideBet (é o mesmo motor) — mas os bilhetes vivem em contas diferentes, então não há colisão prática.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da seleção mais recente** (`MASTER_OUTPUT §4`).

A Esportiva expõe as duas, e elas divergem:

- **colocação** — `createdDate`. É o que o **rodapé do card** mostra (`09/08 • 11:10`). Serve de contexto e de ordem; **não** é a coluna Data.
- **evento** — `selections[].eventDate`, exibido dentro do bloco branco (`09/08 • 16:00`). **Usar a mais recente.**

> Nesta amostra a divergência aparece em **1 de 13** (`5276761434`: colocado **08/08 23:50**, jogo em **09/08 19:30**) — bem menos que na Betboom (7 de 7), porque quase toda a conta é aposta do mesmo dia, muita coisa ao vivo. **Mas 1 em 13 já basta:** travar a colocação poria essa linha no dia errado, e a proporção muda com o perfil de aposta. O harness (`extensor/harness/casos/esportiva.mjs`) trava as duas leituras.

Fuso: os dois campos são **ISO com `Z` = UTC** → converter para America/Sao_Paulo. Sem converter, o `5276761434` (`2026-08-09T02:50:35Z`) apareceria em **09/08** em vez de **08/08** — e o card mostra `08/08 • 23:50`.

---

## 5. Status e Resultado

De-para do `status` do bilhete — **confirmado contra a faixa colorida do card** nesta conta:

| `status` | Leitura | Código |
|---|---|---|
| 0 | Em aberto (faixa `ABERTO`) | *(vazio — não liquidar)* |
| 1 | Ganhou (faixa `GANHOU / VENCIDO`) — conferir o dinheiro | `W` |
| 1 + retorno **igual** à stake | Devolvida / void | `V` |
| 2 | Perdeu (faixa `PERDIDO`) | `L` |
| **8** | **Anulada** (faixa `ANULADA`) — `totalWin == totalStake` | **`V`** |
| **4** e **18** | **Cashout** (faixa `CASHOUT`) — valor encerrado no `totalWin` | **`V` ou `W`, pelo valor** (§5.4) |
| **7** | **Órfão** — fora de todos os filtros da casa; sobe cru | — |
| 3 · 10 · 17 · 20 | Sem amostra — sobem crus, não liquidar automaticamente | — |

### 5.1 O `status 8` é ANULADA (s285)

Provado contra os cards desta conta, em 4 bilhetes reais — `5281584944` (30/30) ·
`5296262805` (100/100) · `5306439522` (124/124) · `5317731393` (1/1). Em todos, `totalWin`
**repete** `totalStake`, e a **seleção também vem com `status: 8`**. O card estampa a faixa
`ANULADA` e o rodapé "Ganho total" igual ao "Valor total de aposta".

> ⚠️ **A casa lista as anuladas dentro do filtro `Ganho`** (`statuses:[1,8]`), não num filtro
> próprio. Quem for conferir na tela procura em "anuladas" e não acha.

O `V` leva a **odd exibida**, nunca 1,00 (`MASTER_RESULTADO §5.1.2`). Por isso o bloco emite
`Devolução do stake:` em vez de `Retorno:` — com o rótulo errado a IA aplicaria retorno ÷
stake e gravaria 1,00 (o `5317731393`, de odd 51,42, mostra o tamanho do estrago).

**Antes da s285 esses 4 subiam como "a conferir"**, a IA devolvia resultado vazio, a linha
nascia `aguardando` — e ficava assim para sempre, porque toda recaptura repetia o bloco.

### 5.2 O `status 7` não existe para a tela — e quase não existiu para nós

Um caso em 250 bilhetes: `5310191599` (19/08, Flamengo × Cruzeiro, R$40). As **duas pernas**
do bet builder ganharam (`status: 1`, placar 2:1) e mesmo assim `totalWin: 0`, sem cashout.

O que o torna especial não é o dinheiro, é onde ele **não** está: `7` fica fora dos **cinco**
filtros da casa — Aberto `[0,10,3,20,17]` · Processado `[1,8,2,4,18]` · Ganho `[1,8]` ·
Perdida `[2]` · Cashout `[4,18]`. A tela não tem onde mostrá-lo, e a captura não o pediria:
o bilhete some dos dois lados, sem erro nenhum. O inject passou a pedir o `7` de propósito
(o gateway aceita o valor extra — medido: `statuses:[7,8]` devolve os dois) só para ele
**chegar**; a leitura segue crua até alguém descobrir o que ele significa.

> Ele é também o contraexemplo que proíbe deduzir desfecho pelo dinheiro nesta casa: uma
> régua "retorno 0 → L" o marcaria como perda, e "pernas ganhas → W" como ganho. Nenhuma das
> duas tem prova. <!-- TODO: perguntar ao suporte o que é o 7 e para onde foram os R$40. -->

### 5.3 Medição que sustenta a tabela

**250 bilhetes, 2026 inteiro, conta `anapetry03`, 23/08/2026:** `0` (9) · `1` (117) ·
`2` (119) · `7` (1) · `8` (4). Os outros seis valores dos filtros seguiam **sem uma única
amostra** — até a s310 trazer os três primeiros cashouts (§5.4). Os quatro restantes
(`3` · `10` · `17` · `20`) continuam subindo crus, e é assim que devem ficar.

### 5.4 `status 4` e `18` são CASHOUT (s310)

Provado por três eixos que se fecham, na conta, em 01/09/2026:

1. **O filtro da própria tela.** A aba **Cashout** manda `statuses:[4,18]` no corpo e devolve
   **exatamente** três bilhetes, nenhum a mais: `5341163017`/18 · `5339901091`/18 ·
   `5339889186`/4. Os cinco filtros já estavam registrados no §5.2 desde a s285 — faltava a
   amostra para batizar os dois.
2. **O card.** Os três estampam a faixa azul **CASHOUT**.
3. **O dinheiro.** O `5339889186` **ganhou** a perna a odd 1,5 (pagaria R$ 5,00) e recebeu
   **R$ 2,83 — menos que a própria stake** (R$ 3,33). Nenhum outro desfecho produz isso.

> ⚠️ **A armadilha que escondeu o cashout por duas versões: `cashOutValue` e `partialCashOut`
> vêm ZERO nos três** (e `partialCashouts: []`). O valor encerrado mora no **`totalWin`**.
> Quem procurar cashout por aqueles dois campos conclui que a casa não tem cashout — e era
> por isso que o `4` subia "a conferir", a IA devolvia resultado vazio e a linha nascia
> `aguardando` **para sempre**: a mesma morte silenciosa das 4 anuladas da s285.

O desfecho sai da régua global (`MASTER_RESULTADO §5.1.2` e `§5.6`), que olha o **valor**, não
o enum:

| Caso | Amostra | Resultado | Odd |
|---|---|---|---|
| valor encerrado **=** stake | `5341163017` (1,31/1,31) · `5339901091` (3,03/3,03) | **`V`** | a **exibida** |
| valor encerrado **≠** stake | `5339889186` (2,83 sobre 3,33) | **`W`** | **cashout ÷ stake** = `0,84984985` |

O `5341163017` é o que mais engana: as **três** pernas ganharam (placar 5:1) e a odd 3,8
pagaria R$ 4,98 — quem olhar as pernas em vez do dinheiro grava um W fantasma. E no
`5339889186`, manter a odd exibida (1,5) gravaria **+R$ 1,67 onde o real é −R$ 0,50**.

**O que NÃO está provado: a diferença entre o `4` e o `18`.** A conta inteira de 2026 tem
três cashouts — um `4` e dois `18` —, e nessa amostra todo `18` veio com valor igual à stake
e o `4` com valor menor. É pouco para batizar, e não precisa: quem decide é o valor. O enum
cru segue saindo no bloco (`Status (API): status=…`) para o dia em que houver amostra.

> A linha de boost também mudou por causa daqui: o "valendo" é a odd **contratada**
> (`totalOdds`), não a que o bloco imprime em `Odd:`. Antes o `5339889186` saía
> "odd antes do boost 1,3847 · valendo 0,84984985" — a casa turbinando a odd para baixo.

O `status` também existe **por perna** (`bbOdds[].status`), com os mesmos valores: `0` pendente · `1` ganhou · `2` perdeu. Confere com o ✓ verde / ✗ vermelho do card. **Um bet builder perde com uma perna ganha** — o `5277858243` tem `Chance dupla ✓` e `Mais de 0.5 ✗` e o bilhete é `L`.

> ⚠️ **A armadilha central desta casa (herdada e reconfirmada).** Em bilhete **aberto**, `totalWin` **já vem preenchido com o valor potencial** e o card estampa isso como "Ganho total". Os 3 abertos da amostra: stake 30 → `totalWin: 54` · stake 30 → `47.1` · stake 50 → `125`, todos com o jogo **ainda rolando** (`60'`, placar `1:0`). Lê-los como retorno realizado transforma **toda** aposta em aberto numa vitória fantasma. Só `status: 1` autoriza a régua financeira do W. O bloco emite `Retorno potencial:` nesse caso, nunca `Retorno:`.

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho.

---

## 6. Boost / promoção

O selo desta casa é **`TURBINADA`** (amarelo, dentro do card), correspondente a `boostedSelection.boostProperty: 3` — o mesmo valor que na VaideBet aparece como `GOLDEN BOOST`. **O nome do selo é da marca; o enum é do motor.**

O card mostra `1.48 » 1.65` (odd antiga riscada → odd valendo). **O boost já está embutido em `totalOdds`** — é essa a odd válida. O `preBoostedPrice` é a odd **antes** do boost e nunca vai para o TSV; o bloco o emite apenas como `Marcação da casa: odd turbinada …`.

> **13 de 13 bilhetes da amostra são turbinados.** Nesta casa o boost não é exceção, é o padrão — o que aumenta o custo de ler a odd errada.

Nos 2 `W` da amostra a odd declarada explica o retorno ao centavo (49,50 ÷ 30 = 1,65 · 198,40 ÷ 124 = 1,6). A regra global do `W` (`retorno ÷ stake`) continua valendo — se um dia a casa aplicar boost só na liquidação, o dinheiro pega sozinho.

---

## 7. Cashout

A casa tem cashout, ele cai em **`status 4` ou `18`**, e os três primeiros bilhetes reais
estão medidos e travados no harness — o de-para e as três provas vivem no **§5.4**.

**A conclusão que ninguém esperava: os campos com "cashout" no nome não servem.**

| Campo | Bilhete **aberto** com botão de venda | Bilhete **cashouteado** de verdade |
|---|---|---|
| `cashOutValue` | `0` | **`0`** |
| `partialCashOut` | `0` | **`0`** |
| `partialCashouts[]` | `[]` | **`[]`** |
| `totalWin` | retorno **potencial** | **o valor encerrado** ← a fonte |

A metade de cima já era conhecida (a oferta de venda vem de outro endpoint,
`GetOpenBetsCashoutValues`) e é uma **proteção**: se a oferta viesse no payload, um bilhete
aberto sairia com "Cash Out" e viraria liquidação fantasma — a armadilha do `cashout_amount`
da Betboom (s250). O harness trava que ela não sai.

A metade de baixo é a novidade da s310, e é o que fazia o cashout passar despercebido: quem
procura cashout por `cashOutValue` conclui que a casa não tem nenhum. O valor está no
`totalWin`, e é o `status` (4/18) que diz que aquele `totalWin` é um encerramento, não um
prêmio. O formatador tenta `cashOutValue` → `partialCashOut` → `totalWin` nessa ordem, e o
harness fica **vermelho** se a casa um dia passar a preencher os dois primeiros — aí o número
tem de ser reconferido contra o card antes de virar fonte.

Vale a regra global: cashout **=** stake → `V` (odd exibida); cashout **≠** stake → `W` com
`Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

---

## 8. Bônus

`bonus`, `bonusPart`, `bonusInsurance` existem no payload; **sem caso na amostra** (todos 0) — apesar de a conta ter **10 freebets ativas** na seção "Bônus" da mesma tela. Ou seja: freebet disponível **não** marca o bilhete; só marcaria um bilhete efetivamente colocado com ela, e não há amostra disso. O bloco emite `Marcação da casa: aposta com bônus (R$ …)` quando vier valor.

---

## 9. Mapa de mercados (Esportiva → `Aposta` global)

Só os mercados **confirmados** no dado real (camada fina — mercado nunca visto não entra aqui). Amostra: 13 bilhetes de 09/08/2026, todos futebol (Brasileirão Série A).

| Esportiva exibe | Aposta global |
|---|---|
| `Total de gols` · `Bahia - Total de Gols` | Gols |
| `Total de escanteios` · `Bahia total de escanteios` · `1º tempo - Palmeiras total de escanteios` | Escanteios |
| `Ambas equipes 2+ cartões cada uma` | Cartões |
| `Ambas equipes marcam` | Ambas Marcam |
| `Chance dupla` | Dupla Chance |
| `Vencedor do encontro` | ML |
| `Totais chutes a Gol` | Chutes no Gol |
| `Total (mais/menos) Chutes Bahia` | Chutes |

> ⚠ **`Chutes` × `Chutes no Gol` são categorias DIFERENTES e esta casa usa as duas, com nomes quase iguais.** `MASTER_APOSTAS §3`: `Chutes` = total de finalizações · `Chutes no Gol` = finalizações no alvo (SOT). `Totais chutes a Gol` (SOT) → **Chutes no Gol**; `Total (mais/menos) Chutes Bahia` (finalizações) → **Chutes**. Ler os dois como a mesma categoria é o erro fácil aqui.

> **`Total (mais/menos) Chutes Bahia` é estatística de TIME e mesmo assim NÃO é `Team Props`:** o objeto apostado (finalizações) tem categoria própria, e `MASTER_APOSTAS §Player Props` é explícito — categoria própria vence entidade. Mesmo raciocínio que manda cartão de jogador para `Cartões`.

> **`Ambas equipes 2+ cartões cada uma` → `Cartões`**, pelo objeto contado. Padrão idêntico ao `Ambas equipes N+ escanteios cada uma` → `Escanteios` de `CASA_VAIDEBET §9`.

---

## 10. Stake

- Origem: `totalStake` (unidade normal, sem milésimos). `unitStake` e `finalStake` trazem o mesmo valor em 100% da amostra.
- O card rotula **"Valor total de aposta"** (`R$30.00`), com **ponto** decimal → normalizar para vírgula.
- Normalização de moeda/milhar = global.

---

## 11. Odds

- Origem: `totalOdds` (bilhete) e `selections[].price` (seleção), **precisão completa**. O card rotula **"Cotações totais"**.
- ⚠ **A tela trunca a odd riscada em 2 casas**: `preBoostedPrice: 1.625` aparece como `1.62`, `1.8889` como `1.88`, `1.6364` como `1.63`, `1.4167` como `1.41`. **Nunca ler odd do card.**
- A odd que vale é a **boostada** (`totalOdds`), não a riscada — ver §6.
- No `W`, o dinheiro confirma: `totalOdds × stake == totalWin` ao centavo nos 2 casos da amostra.
- Bilhete **aberto** usa `totalOdds`; `totalWin` ali é potencial e **não** pode virar odd.

---

## 12. Ruído a ignorar

- **`sportTypeId` é o esporte, mas só como número** — e desde a s310 o de-para **não sai mais de amostra**: ver §12.1. Há ainda `sportId` (66), numeração paralela do motor — usar `sportTypeId`. Id fora do mapa sobe cru e a IA resolve pelo evento/mercado.
- `spec` (`{"1":"2.5"}`, `{"24":"2"}`, `{"65":"111604"}`) — a linha já vem legível no `oddName`/`name`.
- `marketTypeId`, `sportMarketId`, `childMarketTypeId`, `selectionTypeId`, `marketId`, `dbId` — internos do motor.
- `champId` (11318) / `catId` (593) — liga e país, **só como id**. Não há campo de liga legível no payload.
- `device`, `priceType`, `isBanker`, `isVirtual`, `linesCount`, `combLength` — internos.
- `gameTime` / `eventScore` — estado do jogo no momento da consulta, não é dado do bilhete (mas ajudam a explicar por que um aberto tem placar).

### 12.1 O esporte a própria casa publica — sem login (s310)

Até aqui o mapa de `sportTypeId` crescia de bilhete em bilhete, e cada id novo custava uma
amostra. Não precisa: **`GET /api/widget/GetAllSports`** (mesmo host e mesma query do resto
do motor, **sem sessão**) devolve os 25 esportes com os três campos no mesmo objeto —

```json
{"typeId": 4, "id": 68, "name": "Tênis"}
```

`typeId` é o `sportTypeId` do bilhete, `id` é o `sportId`, `name` é como a casa chama. Não é
dedução por nome de time nem por mercado: é a casa dizendo como ela mesma nomeia o id.
`GetSportMenu` e `GetClickableSportMenu` devolvem a mesma lista, e ela bate com o menu da tela.

**Mapeados** (nome da casa ≡ valor oficial do `MASTER_ESPORTES_2026`):

| `sportTypeId` | `sportId` | Nome na casa | Sai como |
|---|---|---|---|
| 1 | 66 | Futebol | `Futebol` |
| **4** | 68 | Tênis | **`Tênis`** |
| 5 · 9 · 14 · 15 · 16 · 17 | 102 · 78 · 89 · 85 · 70 · 73 | Rugby · Dardos · Ciclismo · Golfe · Hóquei · Handebol | `Rugby` · `Dardos` · `Ciclismo` · **`Golf`** · `Hóquei` · `Handebol` |
| 12 | 67 | Basquete | `Basquete` |
| 13 | 76 | **Beisebol** | **`Baseball`** ⚠️ |
| 19 · 20 · 35 · 40 | 69 · 75 · 72 · 84 | Vôlei · Futebol Americano · Badminton · MMA | idem |
| **317** | 145 | **`E-sports +\t\t`** | **`E-Sports`** ⚠️ |
| **318** | 146 | E-Footbal | **`eSoccer`** |

> ⚠️ Três armadilhas de grafia, todas do tipo que cria **duas colunas para o mesmo esporte**:
> o `13` a casa chama de "Beisebol" (o oficial é `Baseball`); o `318` é "E-Footbal"
> (eFootball/FIFA → `eSoccer`); e o **`317` vem com TAB literal no nome** — mais uma da
> família da s303 (`casa_dado_sujo_tab_corrompe_tsv`), e TAB é separador de coluna no TSV.
> Mapeado, o TAB nunca chega ao bloco.

**Deixados CRUS de propósito** — a casa os oferece, mas nenhum tem valor oficial no MASTER, e
batizá-los aqui seria criar taxonomia por conta do arquivo de casa: `6` Sinuca · `7`
Automobilismo · `11` Boxe · `18` Floorball · `23` Futsal · `31` Cricket · `34` Tênis de mesa ·
`43` Biatlo · `82` Rugby League. O `7` é o que mais engana: **"Automobilismo" não é `F1`** — o
valor oficial cobre só a F1. Quando algum deles aparecer num bilhete, a decisão é de MASTER.

### 12.2 `sportTypeId 300` NÃO é esporte — é a gaveta de ESPECIAIS

Mapeá-lo para qualquer esporte erraria metade dos bilhetes. Medido nas **16 seleções** que a
conta tem: todas em `sportId 115` / `champId 61714` / `catId 1365` (uma gaveta só),
`marketName === eventName` em **100%** (o evento *é* a campanha), e o conteúdo mistura CS2
(`BLAST Open Fall 2026 (26/08)`, `Keyd Stars vs Fluxo | FURIA vs LOUD`) com futebol
(`Libertadores Hoje 🔥`, `Copa do Brasil - Sábado (01/08)`) — uma delas se chama literalmente
`Especiais Copa do Brasil | 05/08`. O `115` não aparece em **nenhum** menu de esporte da casa.

Por isso o bloco o marca como `aposta ESPECIAL da casa (sportTypeId 300 — não é esporte…)` em
vez de "id não mapeado": o esporte real está no nome do evento, e é a IA que o resolve de lá.

---

## 13. Pegadinhas (resumo rápido)

- **`totalWin` de aposta ABERTA é potencial e vem preenchido** → nunca ler como retorno (§5).
- Odd: a tela **trunca** a riscada; a válida é a **boostada** (`totalOdds`). **Todo** bilhete daqui é turbinado.
- `Chutes` **≠** `Chutes no Gol`, e a casa usa os dois com nomes parecidos (§9).
- Data: card mostra colocação no rodapé; o TSV quer o **evento**.
- Datas em `Z` = UTC → converter; sem isso o bilhete pula de dia.
- `status` fora de {0,1,2,8} nunca vira W/L por dedução — 6 valores ainda não batizados.
- Enum que **nenhum filtro da casa pede** existe (`7`): sem pedi-lo, o bilhete some da tela
  **e** da captura, sem erro nenhum (s285).
- A lista **não** carrega sozinha ("Mostrar mais apostas") → só API paginada resolve.
- Os cards nascem **colapsados** ("Expandir tudo") — mais um motivo para nunca tentar DOM/texto.
- O endpoint é de outra origem e usa **Bearer**: replay sem os headers reais volta 401.
- `cashOutValue` = 0 **não** significa "sem cashout disponível" (o valor vem de outro endpoint).
- Nome do esporte **não existe** no payload — só id.
- Bet builder pode ser `L` **com uma perna ganha** — o resultado é do bilhete, não da perna.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

- **Coluna Data = a linha `Data (evento mais recente):` do bloco, copiada literalmente.** Nunca inferir da vizinhança nem da ordem da lista — o defeito real da s210 na casa gêmea foi exatamente esse (a IA arrastou a data do bilhete vizinho, embora o bloco trouxesse a certa).
- Odd com precisão completa, decimal com vírgula, e sempre a **pós-boost**.
- Bilhete aberto sai **sem** resultado (`extraction_state = aberta`) e **sem** retorno realizado.
- Bet builder: pernas unidas por `" // "` na Descrição (achado #19) e `Aposta = Múltipla` **mesmo sendo tudo do mesmo jogo** (`MASTER_APOSTAS §Bet Builder`).
- Esporte: copiar o valor **oficial** do bloco (`Futebol`), nunca um sinônimo.
- Mercado de finalização: conferir se o rótulo diz **"a Gol"/"no alvo"** (→ `Chutes no Gol`) ou só **"Chutes"** (→ `Chutes`).

---

## 15. Exemplos golden (bilhetes reais)

Amostra do reconhecimento (s254 · 13 bilhetes de 09/08/2026 · cada valor conferido contra o card expandido). **Ainda não houve lote real extraído pela IA** — estes são o gabarito esperado, não linhas já validadas em produção:

```text
09/08/2026	Futebol		Esportiva		Chutes no Gol	Under 10,5 Chutes a Gol [Bahia v Vasco da Gama]	124,00	1,6	W	5277832732
09/08/2026	Futebol		Esportiva		Escanteios	Over 8,5 Escanteios [Santos v Athletico-PR]	30,00	1,65	W	5277928754
09/08/2026	Futebol		Esportiva		Chutes	Over 12,5 Chutes Bahia [Bahia v Vasco da Gama]	30,00	1,6	L	5277875995
09/08/2026	Futebol		Esportiva		Múltipla	Chance Dupla: Bahia ou Empate [Bahia v Vasco da Gama] // Over 0,5 Gols Bahia [Bahia v Vasco da Gama]	30,00	1,6	L	5277858243
09/08/2026	Futebol		Esportiva		Cartões	Ambas Equipes 2+ Cartões Cada Uma: Sim [Flamengo v Vitória]	50,00	2,5		5276761434
```

Por que estes cinco: o `W` de stake alta em **`Chutes no Gol`** · o `W` de escanteio · o **`Chutes`** (par confusível do primeiro, categoria diferente) · um **bet builder** que é `L` com uma perna ganha · e uma **aberta**, com Resultado **vazio** apesar de o payload trazer `totalWin: 125` e o card dizer "Ganho total R$125.00" — além de ser o bilhete cuja **data do evento (09/08) difere da colocação (08/08)**.

A regressão da CAPTURA (campos, data, odd, boost, status, aberta × potencial, rótulo do esporte, paginação e **igualdade byte a byte com o bloco da VaideBet**) está travada em `extensor/harness/casos/esportiva.mjs`: 13 bilhetes reais + controle negativo.

---

## Feedback para a camada global / MODELO

1. **Altenar/BIA é PLATAFORMA, não casa** — como o BetBy e o BetConstruct. Três marcas `.bet.br` já apareceram sobre ele (VaideBet, Esportiva) e o padrão de detecção é barato e pré-login (`integration=<marca>` nos assets `altenar2.biahosted.*`). Casa nova deste motor deve custar **registro, não implementação**.
2. **`Chutes` × `Chutes no Gol` merecem um alerta no `MASTER_APOSTAS §5`.** A distinção está correta e documentada (§3 e a tabela de finalizações), mas os rótulos das casas são quase homógrafos (`Totais chutes a Gol` × `Total (mais/menos) Chutes`) e a diferença some numa leitura rápida. Um aviso explícito de "par confusível" reduziria o risco em qualquer casa.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA (harness verde · 13 bilhetes reais + controle negativo) · mapa de mercados §9 **parcial** (1 dia de amostra, só futebol) · ⚠️ **NÃO validada ao vivo** (nenhum lote extraído pela IA ainda)
CASA: Esportiva
