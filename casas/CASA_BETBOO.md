# CASA_BETBOO
## Camada de tradução — Betboo → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betboo.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betboo` · site: `betboo.bet.br`
- Grafia **MEDIDA no banco antes de registrar** (s372), como manda a lição da s289: `Betboo` é grafia **única** — 154 bilhetes, 5 contas, 4 donos — e não havia gêmea para unificar antes. O round-trip `_casa_display(_display_to_key("Betboo"))` já era identidade, então o registro não deixou nenhuma conta sem enxergar os próprios bilhetes.
- ⚠️ **NÃO confundir com a [`CASA_BETBOOM`](CASA_BETBOOM.md)**, que é outra casa e outro motor (BetBy, 523 bilhetes). Os nomes diferem por uma letra e `betboo` é **substring** de `betboom` — o que separa as duas em runtime é a amarração casa↔site comparar host **exato ou subdomínio**, nunca substring (`captura.casa_de_host`, `popup.hostBate`). Um grep descuidado não tem essa proteção.
- O domínio dos favicons apontava para `betboo.com` (o site global) até a s372. O correto é a operação regulada `betboo.bet.br` — mesma correção que a SportingBet levou na s289. Verificado baixando os dois ícones: **sha256 idêntico** (791 bytes), então o visual não mudou.
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `currency: "BRL"` em cada valor
- ⚠️ **Decimal na tela: a casa MISTURA as duas convenções no MESMO card.** A `Cota` vem com **PONTO** (`8.02`, `7.58`, `12.91`) e o dinheiro com **VÍRGULA** (`R$ 201,00`, `R$ 1.524,59`). Isto é diferente do que o §1 da gêmea registra (lá, ponto nos dois) e é a família do caso da Betfair: **formato de número é por TOKEN, não por casa**.
- Motor: **bwin / Entain**. Front Angular servido de `/ClientDist/`, temas em `themes-betboo-br-sports-*`.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

### 1.1 Espelho da SportingBet — o que isso significa na prática  ⭐

A Betboo é a **mesma casa técnica** que a [`CASA_SPORTINGBET`](CASA_SPORTINGBET.md): mesmo motor, mesmo endpoint, mesmos nomes de campo, mesmas armadilhas de data e de promoção. Muda o domínio e a cor.

Não foi assumido — foi **provado antes de escrever código** (recon de 17/09/2026):

| Prova | Betboo | SportingBet |
|---|---|---|
| `POST /pt-br/sports/api/mybets/betslips` **com** os cabeçalhos do motor, deslogado | **401** (existe, exige sessão) | 401 |
| o MESMO path **sem** os cabeçalhos do motor | **200 com o HTML da SPA** (109 KB) | 200 com HTML (135 KB) |
| rota inexistente sob o mesmo prefixo (controle) | 200 com o mesmo HTML | — |
| corpo do pedido | `{"index","maxItems","typeFilter","pinnedBetslipIds","eventIds","useGroupedView"}` | idêntico |
| topo da resposta | `{summary, betslips, typeFilter, errorLoadingBets}` | idêntico |
| `index` é PÁGINA (não offset) | sim — `index:2` devolveu `betslips: []` | sim |
| fim autoritativo | **lista VAZIA** (sem `isLastPage`/`more`/`hasNext`) | idêntico |
| strings no bundle | `mybets/betslips`, `typeFilter`, `useGroupedView`, `pinnedBetslipIds`, `betSlipNumber`, `slipType`, `isBetBuilder` | idem |

> O controle da rota inexistente é o que fecha a prova: o `401` só aparece quando a rota é **real** E os cabeçalhos são os do motor. Sem esse terceiro teste, "veio 401" não distinguiria rota de host.

Consequência de engenharia: a captura usa o **mesmo `extensor/spb_inject.js`** e o **mesmo formatador** (`formatTicketSPB`), sem uma linha duplicada — o inject casa por **PATH** (`/mybets/betslips`) e monta a URL de `location.origin`. O caso `extensor/harness/casos/betboo.mjs` roda a fixture **desta** casa contra esse código e tem asserção específica para pegar se alguém cravar o host da gêmea.

> **Ao mexer numa das duas, confira a outra.** Toda armadilha registrada aqui vale para a SportingBet e vice-versa. As duas amostras se completam: a SportingBet trouxe a perna anulada, a freebet, o `BIG ODD` e as `Múltiplas Aumentadas`; a Betboo trouxe o **AccaBoost** (§6), dois **esportes novos** (§12) e o **segundo catálogo de evento** (§12.2).

---

## 2. Modo de ingestão e layout

**Captura por API + replay** (SharpenUp · `extensor/spb_inject.js`, compartilhado). Endpoint, corpo, paginação, abas e fim autoritativo: ver [`CASA_SPORTINGBET §2`](CASA_SPORTINGBET.md#2-modo-de-ingestão-e-layout) — é idêntico, incluindo o **arranque a frio** (abrir Minhas Apostas não faz requisição nenhuma) e a **leitura passiva impossível** (a SPA aborta o `fetch` e mata o clone).

**Janela de datas: NÃO existe no corpo.** O corte por dias é feito no `content.js`, pela colocação, e corta **só resolvidas**.

### 2.1 Por que TEXTO está descartado — medido, não deduzido

O `innerText` da lista de liquidadas, com os 5 bilhetes na tela:

- **nenhum dos 5 ids aparece** (o card colapsado não estampa o código — sem id não há dedup);
- **zero linha em branco entre bilhetes** — o bilhete seguinte começa imediatamente depois da faixa de estado (`Derrota`), então o `roboScroll` genérico juntaria a lista num bloco só e a IA perderia o resto **em silêncio** (a lição da KTO, s192);
- as seleções vêm **coladas, sem separador**: `"Indonésia -5.5Mais de 0.5Mais de 0.5"`.

A medida aqui é mais dura que a da gêmea (lá foram 6 bilhetes e 0 linhas em branco; aqui soma-se o id ausente e a colagem das pernas).

---

## 2.5 Campos da API (o que o inject entrega)

A tabela completa está em [`CASA_SPORTINGBET §2.5`](CASA_SPORTINGBET.md#25-campos-da-api-o-que-o-inject-entrega) — os campos são os mesmos. O que esta conta mostrou **e a gêmea não tinha**:

| Campo (API) | Significado | Observação |
|---|---|---|
| `promoTokens[].tokenType: "AccaBoost"` | **boost de MÚLTIPLA**, no nível do bilhete | ver §6 — não é o `priceBoostData`, que é por seleção |
| `…informationItems[AccaBoostRatio]` | fração do boost | `"0.0500"` = 5% · o card estampa `+5% Múltipla+` |
| `…informationItems[BoostedWinnings]` | ganhos **COM** boost | é o valor que a tela exibe · `0` em bilhete perdido |
| `…informationItems[WinningsBoost]` | só o **acréscimo** | ausente quando não há dinheiro a declarar |
| `bets[].fixture.compoundId` | **catálogo de origem** do evento (`"1:…"` · `"2:…"`) | decide se a perna tem `optionBetDetails` — ver §12.2 |
| `businessContext.loginDomainId` | id do domínio de login (`99`) | ruído · não identifica a casa para o nosso lado |

---

## 3. ID do bilhete

`betSlipNumber` — alfanumérico de **10**, sem separador (`20RSMW9KJA`, `20RTRWRSKY`). É a chave de dedup e o conteúdo do `[Código: …]`. Sempre presente, inclusive em aberta.

Reconhecido pela regex **GENÉRICA** do `repository.codigos_do_texto`, não por regex de casa. Gabarito em `tools/audit_sharpenup.py::CODIGO_EXEMPLO`.

> ⚠️ **O espaço de ids é COMPARTILHADO com a SportingBet** (mesmo motor, mesma operação): um id sozinho **não diz de que casa é**, como já acontece entre Betão / R7 / 7Games. Isso **não** gera colisão de dedup, porque `casa` entra na assinatura (`repository._assinatura`) — mas é a amarração casa↔site que impede gravar na casa errada, e é por isso que ela não é enfeite.

---

## 4. Data

Regra global: a coluna Data é a do **evento** (`MASTER_OUTPUT §4`). Sai de `bets[].fixture.date`, a **mais recente** quando há várias pernas, convertida de UTC para America/São_Paulo.

⚠️ **`conclusionDateUtc` MENTE aqui também**: é a data em que a aposta foi **COLOCADA**, não a conclusão. Prova medida nesta casa: o card do `20RT3JEUU6` estampa `16/09/2026 • 21:54` e o campo traz `2026-09-17T00:54:07Z` (= 16/09 21:54 em Brasília), enquanto o evento mais recente do bilhete é **17/09 01:00**. Uma conclusão não pode ser anterior ao evento.

Ela sobe no bloco como `Data (colocação):`, separada, porque é o que o card mostra no cabeçalho do grupo — e é por ela que a janela de dias corta.

---

## 5. Status e Resultado

De-para do `state` (enum CRU da casa → global). Idêntico ao da gêmea:

| `state` (API) | Global | Observação |
|---|---|---|
| `Open` | *(sem resultado)* | sobe como "em aberto (aguardando resultado — NÃO liquidar)" |
| `Won` | **W** | com `payout = stake` → **V** (devolvida) · `0 < payout < stake` → conferir HW/HL ou cashout |
| `Lost` | **L** | |
| `Canceled` | **V** | anulada/void, stake devolvido · **sem amostra nesta conta** |

**Qualquer outro `state` sobe CRU e marcado "a conferir — não liquidar automaticamente".** Nunca se deduz W/L do dinheiro: é a lição da Esportiva (s285), onde um enum não traduzido deixou linha presa em "aguardando" por meses. O `avisarEstadoNaoMapeadoSPB` avisa no toast **com o nome desta casa** e aponta os ids no console.

---

## 6. Boost / promoção  ⭐ (o que esta casa trouxe de novo)

São **DOIS** mecanismos diferentes, que podem coexistir:

**a) `priceBoostData` — boost de ODD, por seleção.** O card mostra `1.98 » ⚡2.50` e o riscado é a odd **antes**. A odd válida é `totalOdds.european`, que já vem boostada. Ver [`CASA_SPORTINGBET §6`](CASA_SPORTINGBET.md#6-boost--promoção). **Sem amostra nesta conta.**

**b) `promoTokens[AccaBoost]` — boost de MÚLTIPLA, no bilhete.** ⭐ Amostra só aqui: **3 dos 8** bilhetes da conta. O card estampa, no rodapé, `Promoção usada  ⚡ +5% Múltipla+`.

⚠️ **E o card NÃO trata os dois números como equivalentes.** Com o boost ele **troca o rótulo** de `Possíveis ganhos` para **`Ganhos melhorados`** e **RISCA** o valor sem boost. Medido no `20RTRWRSKY`:

```
Valor R$ 201,00      Cota 12.91      Ganhos melhorados  R̶$̶ ̶2̶.̶5̶9̶5̶,̶9̶2̶  R$ 2.715,67
```

E a conta fecha exata: `maxPayout 2.595,92 + WinningsBoost 119,75 = BoostedWinnings 2.715,67`.

**Logo o retorno potencial que VALE é o com boost**, e o `maxPayout` do payload é o riscado — a mesma leitura que a odd pré-boost já recebe. Emitir o `maxPayout` como potencial subestimaria em R$ 119,75, e o bloco diria um número que a tela risca.

Em bilhete **perdido** a casa manda `BoostedWinnings: 0` e nem cria `WinningsBoost`: o token continua lá (a promoção foi usada) e só não há dinheiro a declarar. Por isso o potencial só troca quando o boost é **maior** — token sem dinheiro nunca rebaixa o valor exibido.

> ⚠️ **INCÓGNITA declarada, não resolvida: não há GANHO com AccaBoost nesta conta.** Então não se sabe se o `payout` de um W turbinado já vem somado ou se o bônus é creditado à parte. Isso **não** compromete a leitura: a odd de W sai da régua global (`retorno ÷ stake`, §11), que fecha certo nas duas hipóteses. Quando aparecer o primeiro W com boost, confira `payout` contra `BoostedWinnings` e registre aqui.

---

## 7. Cashout

**Sem amostra nesta conta.** Os campos existem no payload (`isEarlyPayout`, `isDelayedForEarlyPayout`, `earlyPayoutInformation.autoCashoutTriggered`) e, quando acionados, prefixam o status com `Cash Out ·`. Nos 8 bilhetes da amostra, `isEarlyPayout: false` e `autoCashoutTriggered: false` em todos.

A régua é **global** e não se redefine aqui: cashout **≠** stake → **W** com `Odd = Cashout ÷ Stake`; cashout **=** stake → **V** (`MASTER_RESULTADO §5.1.2` e `§5.6`).

> Na tela, o botão aparece como `Encerrar Aposta` e nos bilhetes ao vivo desta conta ele vinha **desabilitado** (`Encerrar Aposta Fechado`, com a nota "Apostas para uma ou mais de suas seleções não estão abertas agora"). Ou seja: a casa oferece cashout, a conta simplesmente não usou.

---

## 8. Bônus

`isFreeBet` marca aposta grátis — **sem amostra nesta conta** (a gêmea tem 1 caso). Quando vier, sobe como marcação, porque o stake não saiu do saldo e isso muda o P/L.

`bestOddsGuaranteedInformation` existe em todos os 8 bilhetes, sempre com `state: "NotEligible"` — logo **nunca acionado** nesta amostra. No W, ele traz `fixedPriceWinnings` repetindo o `payout`; não é fonte de nada.

O bônus que esta conta **sim** exercita é o **AccaBoost**, e ele não é bônus de saldo: é boost de retorno, tratado no §6.

---

## 9. Mapa de mercados (Betboo → `Aposta` global)

Só mercados **confirmados nesta conta** (camada fina — o que a casa nunca mostrou não entra):

| Betboo exibe (`market.name`) | Aposta global |
|---|---|
| `Resultado da partida` | ML |
| `Chance Dupla` | Dupla Chance |
| `Handicap` | Handicap |
| `Total de Cartões` · `Total de Cartões - 1º Tempo` · `<Time> - Total de Cartões` | Cartões |
| `2º tempo - total de escanteios` | Escanteios |
| `Total - 1º Tempo` (basquete) · `How many points will <Time> score in the 1st half?` | Pontos |
| `<Jogador> - Rebatidas simples` · `<Jogador>: Rebatidas` · `<Jogador> (<TIME>): Batter walks` | Player Props |
| `<Jogador> - Corridas` | Corridas |

> `<Jogador> - Corridas` vai para **`Corridas`** e não para `Player Props` porque **objeto com categoria própria vence a entidade** (`MASTER_APOSTAS §Player Props`). Já rebatidas e *batter walks* **não têm** categoria própria no MASTER, e por isso caem em `Player Props`.

> `Total - 1º Tempo` de basquete e a pergunta sobre pontos de um TIME vão as duas para `Pontos`: o discriminante do MASTER é jogo/time → `Pontos`, jogador → `Player Props` (`MASTER_APOSTAS §Pontos`, Discriminante 1).

### 9.1 A gêmea traduziu o MESMO mercado com outro nome

⚠️ O que a SportingBet exibe como **`<Jogador> - Player singles`**, a Betboo exibe como **`<Jogador> - Rebatidas simples`** — mesmo mercado do beisebol, rótulo em inglês numa e em português na outra.

**Isso é localização, e é por isso que o §9 é da casa e não do motor.** Compartilhar inject e formatador não significa compartilhar o mapa de mercados: quem lê pelo §9 da gêmea não acha este rótulo.

---

## 10. Stake

`stake` / `stakePerBet`, objeto `{currency, value}`, em unidade normal — `201` é R$ 201,00, **não** há milésimos. O card confirma: `Valor R$ 201,00`.

---

## 11. Odds

`totalOdds.european`, **precisão completa, nunca truncada**, decimal normalizado para vírgula.

⚠️ **A `Cota` do card é ARREDONDADA a 2 casas e pode não explicar o retorno.** Medido no único W da conta (`20RSMW9KJA`): card `Cota 7.58`, `Valor R$ 201,00`, `Ganhos R$ 1.524,59`. Mas `201 × 7,58 = 1.523,58`, **um real a menos** do que a casa pagou.

Então vale a régua global: em **W**, `Odd = Retorno ÷ Stake` (`MASTER_RESULTADO`), e a odd gravada é `1524,59 ÷ 201 = 7,58502488`. Travar a Cota do card seria gravar o arredondamento da casa no lugar do dinheiro.

A odd declarada só é mantida quando ela **explica o retorno até o centavo** — é o que `_oddSPB` faz, e é o que separa este caso de uma odd adulterada.

---

## 12. Ruído a ignorar / armadilhas próprias

### 12.1 O esporte sai do ID, e esta casa trouxe dois novos

⚠️ O rótulo do esporte vem do **`sport.id`**, nunca de `sport.name`: a casa escreve sinônimos de ENTRADA e a IA copia verbatim — foi assim que a VaideBet gravou duas grafias do mesmo esporte no banco (s210).

O mapa é **compartilhado** com a gêmea (`_ESPORTE_SPB`, no `content.js`), e a Betboo dobrou o tamanho dele: **4 dos 8** bilhetes desta conta caíam em "id não mapeado" antes da s372.

| `sport.id` | a casa escreve | valor oficial | como foi decidido |
|---|---|---|---|
| 4 | `Futebol` | `Futebol` | — |
| **7** | `Basquete` | **`Basquete`** | canônico no `MASTER_ESPORTES §336` · 17.979 bilhetes / 17 donos no banco |
| 23 | `Beisebol` | `Baseball` | sinônimo de entrada × valor oficial · 1.901 × 4 bilhetes no banco |
| **56** | `Tênis de mesa` | **`Tênis de Mesa`** | grafia única no banco (43 bilhetes / 5 donos / 3 casas) · ⚠ a casa usa `m` minúsculo |

> ✅ **RESOLVIDO (s375):** `Tênis de Mesa` ganhou seção própria na `MASTER_ESPORTES_2026 §7`, então este de-para passou a gravar um valor **canônico**. A seção nasceu sem lista de atletas de propósito: medido, os 43 bilhetes que hoje carregam o rótulo são **badminton mal classificado** (14 casam com a lista auxiliar de Badminton, nenhum com a de Tênis), e publicar lista tirada desse acervo viraria erro em referência.

### 12.2 DOIS catálogos de evento no mesmo bilhete

⚠️ `fixture.compoundId` tem dois prefixos, e a **forma da perna muda com ele**. Medido: 5 das 24 pernas da amostra vêm do catálogo `1:`, e essas:

- **não têm `optionBetDetails`** — logo não têm `isBetBuilder`, `isPriceBoost` nem `priceBoostData`;
- às vezes **não têm `outcome`**;
- trazem `market.name` **em inglês** no meio de um bilhete em português (`"How many points will Perth Wildcats score in the 1st half?"`, `"Emmanuel Rodriguez (MIN): Batter walks"`).

Quem ler `optionBetDetails` sem guarda de nulo quebra nelas. O formatador já protege, e o caso do harness tem controle negativo específico (`(e)`) para isso não regredir.

### 12.3 `fixture.name` tem dois formatos de confronto

`"Indonésia (F) - Tailândia (F)"` (hífen) e `"Seattle Mariners at Los Angeles Angels"` (`at`, padrão MLB). O segundo **não** usa separador de hífen. A descrição copia o nome verbatim — quem parsear confronto por hífen perde os jogos americanos.

### 12.4 Ruído puro

`businessContext`, `signPostings`, `signPostingRewards`, `edsPromoTokens`, `isTeaserBet`, `betGroups`, `combinations`, `isBasicModel`, `oddsChangeAcceptanceMode`, `isBanker`, `isBetCorrection`, `editBetInformation.editBetHistory` (vazio) — nada disso vai para o TSV.

---

## 13. Pegadinhas (resumo rápido)

1. **`conclusionDateUtc` é COLOCAÇÃO**, não conclusão (§4).
2. **A `Cota` do card é arredondada** e pode não explicar o retorno — em W, odd = retorno ÷ stake (§11).
3. **AccaBoost**: o card RISCA o `maxPayout` e o potencial que vale é o `BoostedWinnings` (§6).
4. **Esporte sai do `sport.id`**, nunca de `sport.name` (§12.1).
5. **Perna do catálogo `1:` não tem `optionBetDetails`** (§12.2).
6. **Sem os cabeçalhos do motor, a casa responde 200 com HTML** — a falha não grita (§1.1).
7. **Fim da paginação = lista vazia.** Não há `isLastPage`/`more`/`hasNext` (§1.1).
8. **Decimal misturado no mesmo card**: odd com ponto, dinheiro com vírgula (§1).
9. **Não é a Betboom.** Uma letra de diferença, outro motor, outra casa (§1).

---

## 14. Validações específicas

> **Transversais (toda casa):** ver `MASTER_PIPELINE_2026` e `MASTER_OUTPUT_2026 §9`.

Próprias desta casa, travadas em `extensor/harness/casos/betboo.mjs` (17 conferências, 9/9 mutações detectadas):

- toda requisição do replay leva `x-bwin-sports-api` (sem ele, HTML com 200);
- as URLs saem de `betboo.bet.br` — se alguém cravar o host da gêmea, fica vermelho;
- as duas abas são pedidas partindo de qualquer uma, e o arranque a frio entrega os 8 bilhetes;
- aberta nunca emite `Retorno:`, só `Retorno potencial:`, e nunca recebe código de resultado;
- `state` desconhecido sobe "a conferir", nunca convertido em W/L;
- o esporte sai do mapa de id (com as duas amostras em que o mapa e `sport.name` divergem);
- perna sem `optionBetDetails` não derruba o bloco nem vaza `undefined`.

### 14.1 O que o gate NÃO cobre

Declarado para o verde não virar promessa falsa. A amostra da conta tem **8 bilhetes, todos `slipType: "Combo"`** — e portanto **não há**:

- nenhuma aposta **simples**;
- nenhum `Canceled`, nenhum **freebet**, nenhum **cashout**, nenhum **bet builder** (a casa tem "Criar Aposta+" no menu, mas a conta não usou);
- nenhum **W com AccaBoost** (a incógnita do §6);
- nenhum `priceBoostData` (boost de odd por seleção).

Para esses casos, a referência é a amostra da gêmea — e o §9 e o §12 crescem quando esta casa mostrar mais.

---

## 15. Exemplos golden (bilhetes reais)

Conta do recon, 17/09/2026. Fixtures em `extensor/harness/fixtures/betboo.{settled,open}.json`.

| Código | Data (evento) | Tipo | Stake | Odd | Retorno | Res. | O que ele ensina |
|---|---|---|---|---|---|---|---|
| `20RSMW9KJA` | 16/09/2026 19:45:00 | Múltipla (2) | 201,00 | 7,58502488 | 1.524,59 | W | a Cota do card (`7.58`) **não** explica o retorno |
| `20RSN4R2C5` | 16/09/2026 16:00:00 | Múltipla (3) | 201,00 | 7,41 | — | L | AccaBoost **sem** dinheiro (`BoostedWinnings: 0`) · 1ª perna é `sport.id 56` |
| `20RT3JEUU6` | 17/09/2026 01:00:00 | Múltipla (3) | 201,00 | 8,02 | — | L | mistura Basquete (7) com Beisebol (23) · colocação cruza a meia-noite |
| `20RTRWRSKY` | 19/09/2026 08:30:00 | Múltipla (3) | 201,00 | 12,91 | *(potencial 2.715,67)* | aberta | AccaBoost **com** dinheiro: o card risca 2.595,92 · 2 pernas do catálogo `1:` |
| `20RTWGUF65` | 18/09/2026 15:30:00 | Múltipla (2) | 201,00 | 6,75 | *(potencial 1.356,75)* | aberta | `payout: 0` com potencial em campo próprio |

---

## Feedback para a camada global / MODELO

- ~~**`Tênis de Mesa` não existe no `MASTER_ESPORTES_2026`**~~ **FEITO na s375** — seção aberta na §7, com os sinônimos de entrada e os sinais positivos de circuito (`ITTF`, `WTT`, `Setka Cup`, `TT Cup`, `Liga Pro`). A propagação achou algo que a casa não via: **os 43 bilhetes do rótulo são badminton**, e a Regra Crítica de raquete passou a exigir sinal positivo para Tênis de Mesa, que **nunca** é desempate.
- **Promoção que mexe no RETORNO, e não na odd, não tem tratamento no `MASTER_RESULTADO`.** O AccaBoost paga por fora da odd declarada, e a régua atual só sabe reconciliar isso porque em W a odd é derivada do retorno. Numa casa que aplicasse boost em bilhete **aberto** e publicasse só a odd, o potencial ficaria errado sem ninguém notar.
