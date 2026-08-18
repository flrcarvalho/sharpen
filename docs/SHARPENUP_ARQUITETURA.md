# SharpenUp — arquitetura da captura

> **O que é:** referência de como a extensão captura bilhetes e como uma casa se liga ao
> sistema. Documento de **mapa**, não de regra: as regras de domínio vivem nos
> `global/MASTER_*`, as de marca no `pack/CLAUDE.md`, e **o código é a verdade** — ao mudar
> o comportamento, atualize este mapa na mesma sessão.
>
> **Para CRIAR uma casa nova, siga o procedimento:** [`GUIA_CASA_SHARPENUP.md`](GUIA_CASA_SHARPENUP.md).
> **Gate determinístico:** `python tools/audit_sharpenup.py`.
> **Regressão:** `node extensor/harness/run.mjs`.

---

## 1. O caminho de um bilhete

```
   casa (site)
      │  a página baixa o próprio histórico (fetch/XHR)
      ▼
  ┌───────────────┐   window.postMessage        ┌──────────────┐
  │ xx_inject.js  │ ──────────────────────────► │  content.js  │
  │ mundo MAIN    │ ◄────────────────────────── │ mundo isolado│
  │ hook + replay │   {__sharpenupXXReq}        │ robô + texto │
  └───────────────┘                             └──────┬───────┘
                                                       │ chrome.runtime
                                                       ▼
                                              ┌─────────────────┐
                                              │  background.js  │
                                              └────────┬────────┘
                                                       │ POST /captura/enviar (token)
                                                       ▼
                                    ┌──────────────────────────────────┐
                                    │ app/captura.py  (sessão efêmera) │
                                    └────────────────┬─────────────────┘
                                                     │ poll + drenar
                                                     ▼
                                    ┌──────────────────────────────────┐
                                    │ dashboard → /extrair → IA → TSV  │
                                    │ chunking · pré-dedup · cobertura │
                                    └──────────────────────────────────┘
```

**Por que dois mundos:** o `content.js` roda isolado e **não enxerga o `fetch` da página**.
Quem intercepta a resposta da API tem de rodar no mundo `MAIN` — daí o `xx_inject.js`.
Eles só conversam por `postMessage`.

> ⚠️ **A escolha do mundo não é só sobre `fetch`: ela decide se o CLIQUE funciona.** Ler a
> resposta exige `MAIN`; **dirigir a página pode exigir o ISOLATED**. Na bet365 (s279) o mesmo
> `.click()`, no mesmo `div.hl-SummaryRenderer_ShowMore`, dá **8 cliques com zero requisição**
> quando disparado do `b3_inject` (MAIN) e **carrega a página seguinte** quando disparado de um
> content script comum — enquanto pelo console (que também é MAIN) funciona. Foram descartados
> por medição, não por dedução: patch de `HTMLElement.prototype.click` (é `[native code]`),
> barreira `isTrusted` (o clique sintético carregou 3×), handler num filho (o div não tem
> filhos) e viewport (o iframe não rola). **Casa que precise clicar: separe o arquivo que
> escuta do arquivo que clica**, como `b3_inject.js` (MAIN, escuta) + `b3_expand.js` (ISOLATED,
> clica), conversando por `window.postMessage` na mesma window. E note o custo de não fazer
> isso: o laço no mundo errado **não dá erro** — ele clica, conta os cliques e reporta fim.

**O que a extensão NÃO faz:** decidir W/L/V, traduzir mercado, calcular P/L. Ela entrega
**texto cru e fiel** (com o marcador `[Código: …]`); quem interpreta é a IA com os
`global/MASTER_*` + `casas/CASA_*.md`. Regra da casa: *cálculo é global, localização é da casa*.

---

## 2. Modos de captura

| Modo | Quando | Custo | Precisão |
|---|---|---|---|
| **API passiva** | a página baixa a lista inteira ao rolar/paginar | baixo | máxima (JSON exato) |
| **API + replay** | a lista pagina, ou tem abas, ou o scroll não dispara | baixo | máxima |
| **Navegação por rota** | o detalhe só existe atrás de um clique e o token rotaciona (bet365) | médio | máxima |
| **Texto (DOM)** | não há API legível, mas o card inteiro está no DOM | baixo | boa |
| **Print (moldura + Snap)** | nada acima serve — é o default de toda casa nova | alto (OCR) | depende do print |

> **Lição da s192 (KTO):** o robô de texto genérico (`roboScroll`) parte o `innerText` por
> **linha em branco**. Se a lista da casa não tiver linha em branco entre bilhetes, os ~140
> cupons viram **um bloco só** com menu e rodapé — a IA lê os primeiros e **perde o resto em
> silêncio**. Antes de escolher "texto", confira essa fronteira. Quase sempre a resposta certa
> é *"vir por trás, pelo F12"*.

---

## 3. Contrato de mensagens (inject ⇄ content)

Toda casa segue o mesmo formato — mudam só as duas letras do prefixo.

**inject → content** (sempre, mesmo com 0 bilhetes — é o heartbeat do autodiagnóstico):

```js
window.postMessage({
  __sharpenupXXData: true,
  hook: true,          // o inject carregou (distingue de "endpoint mudou")
  respostas: 12,       // respostas do endpoint que o hook viu
  <lista>: [...],      // bets / tickets / items / cupons — normalizados
  fim: false,          // fim AUTORITATIVO (a casa disse que acabou), não heurística
}, "*");
```

**content → inject** (o robô pede o acumulado e arranca o replay):

```js
window.postMessage({ __sharpenupXXReq: true, /* dias, limite… */ }, "*");
```

Regras que valem para todos:

1. **Re-enviar sob demanda.** A 1ª página chega no `load`, antes de o content estar
   ouvindo. Sem o `Req`/`enviar()`, ela se perde.
2. **`hook` + `respostas` sempre.** É o que separa "não injetei" de "endpoint mudou" de
   "conta vazia" no autodiagnóstico. Sem isso, falha de captura vira silêncio.
3. **Resolvida vence aberta.** O mesmo bilhete pode voltar nas duas abas; o dado final é
   o liquidado.
4. **`fim` só quando a CASA disse que acabou** (`more:false`, `LastId` ausente,
   `moreAvailable:false`). Teto de tempo é rede de segurança, não critério.
5. **O inject não decide nada.** Ele normaliza campos crus. Status desconhecido sobe cru —
   nunca vira W/L por chute.

---

## 4. Casas de captura hoje

| Casa | Modo | Endpoint | Inject | Chave de dedup | Fim autoritativo | Data que vai pro TSV |
|---|---|---|---|---|---|---|
| **Superbet** | API passiva | `GET /user/<id>/tickets?status=finished\|active` | `sb_inject.js` | `ticketId` | 5 rolagens sem novo | evento mais recente (UTC→SP) |
| **BETesporte** | API passiva | `POST /api/bet/RequestUserTickets` | `be_inject.js` | `id` | 5 s sem novo | `date` (já local) |
| **Betano** | API passiva | `GET /api/ma/bet/bet-history-v3?settled=` | `bn_inject.js` | `BetId` | página sem `LastId` | `PlacedAt` (UTC→SP) |
| **Betfair** | API + replay | `POST /activity/sportsbook` | `bf_inject.js` | `betId` `O/…` | `moreAvailable:false` | `settledDate` (já local) |
| **Pinnacle** | API + replay | `POST /member-service/v2/wager-filter` | `pn_inject.js` | `id` (array posicional!) | replay das 2 abas | data do evento |
| **KTO** | API + replay | `GET /coupon/history.json` (Kambi) | `kto_inject.js` | `couponRef` | `range.more:false` | `placedDate` (UTC→BRT) |
| **Stake** | API + replay (paginado) | `POST /restapi/v1/betslip/history` (Kambi atrás de REST próprio) | `stk_inject.js` | `internal_bet_id` (7 díg.) | `next_page_exists:false` | `ticket_placed_date` (UTC→SP) |
| **Bet365** | rota (`location.hash`) + "Mostrar Mais" automático | `/sportshistoryapi/summary` + `/confirmation` | `b3_inject.js` (MAIN) + `b3_expand.js` (ISOLATED, clica) | `BR` (do confirmation) | fim + 0 sem código | kickoff + folga, UK→BR |
| **Tivo** | API + replay (1 chamada) | `POST /api/game/p/messagetosport` (`gethistory`) | `tv_inject.js` | `ID` | `Error:null` + `len == Count` | evento mais recente (UTC→SP) |
| **Betfast** | **espelho da Tivo** — mesmo motor BetConstruct | idem | **`tv_inject.js`** (o mesmo) | `ID` | teto de 50 + varredura por `to` ⚠ | evento mais recente (UTC→SP) |
| **BetNacional** | API + replay (janelas de datas) | `GET /api/v2/all-bets` | `bnc_inject.js` | `ticket_id` | janelas até secar | ⚠ ver nota abaixo |
| **VaideBet** | API + replay (paginado) | `POST /api/WidgetReports/widgetExpandedBetHistory` (Altenar) | `vb_inject.js` | `id` | `isLastPage:true` | evento mais recente (UTC→SP) |
| **Esportiva** | **espelho da VaideBet** — mesmo motor Altenar/BIA | idem, **mesmo host de gateway** | **`vb_inject.js`** (o mesmo) | `id` | `isLastPage:true` | evento mais recente (UTC→SP) |
| **Jogo de Ouro** | **espelho da VaideBet** — 3ª casa Altenar | idem ⚠ **só na TELA CHEIA** (o painel lateral usa `widgetBetHistory`) | **`vb_inject.js`** (o mesmo) | `id` | `isLastPage:true` | evento mais recente (UTC→SP) |
| **Betpix365** | **espelho da VaideBet** — 4ª casa Altenar | idem ⚠ **a casa só dispara o `widgetBetHistory` compacto**; o replay aprende dele e busca o Expanded | **`vb_inject.js`** (o mesmo) | `id` | `isLastPage:true` | evento mais recente (UTC→SP) |
| **Jonbet** | API + replay (paginado) | `GET /api/v1/my_bets/list` (BetBy/sptpub) | `jb_inject.js` | `id` (19 díg.) | `skip >= count` ou lista vazia | evento mais recente (epoch **s**→SP) |
| **Pitaco** | **replay puro** (o passivo é impossível) | `POST /…UiMyBetsService/GetUiMyBetsTabContent` — **gRPC-Web / protobuf binário** | `pt_inject.js` | `.4.1.1` (17 díg.) | campo `.5` ausente na resposta | evento mais recente ⚠ **sem ano** — derivado da colocação |
| **Novibet** | **replay puro** (o passivo é impossível) | `POST /spt/api/historytickets/search` (gateway BlueBrown, host da casa) | `nv_inject.js` | `ticketId` (9 díg.) | `skip >= statistics.count` | `placedAt` (colocação, UTC→SP) ⚠ **não há data de evento** |

> ⚠ **BetNacional — divergência de rótulo NÃO medida (anotada na s248, ao preencher esta tabela).**
> `formatTicketBNC` emite só `Data (colocação):` (de `t.colocada`), enquanto `CASA_BETNACIONAL §4`
> diz que a coluna Data é a **do evento** e que o campo do Histórico já é "evento / liquidação".
> Pode ser só nome infeliz da variável — o campo da casa talvez já seja o do evento — ou pode ser
> o mesmo defeito que a VaideBet levou a produção na s210. **Ninguém mediu se as duas datas
> divergem nessa casa.** Para decidir: comparar `t.colocada` com `pernas[].inicio` (que o bloco já
> emite como `Início:`) num lote real. Enquanto isso, esta célula fica marcada, não chutada.
>
> **Altenar/BIA também é PLATAFORMA (s254).** A Esportiva entrou **sem uma linha de código
> novo de captura**: reusa `vb_inject.js`, `formatTicketVB` e `roboVBPassive`. Mudou só o ramo
> do `iniciarRobo`, a entrada de autodiagnóstico e os 12 registros — o desenho Tivo/Betfast e
> Jonbet/Betboom pela terceira vez. Aqui o espelho é ainda mais apertado que nos outros dois:
> não é só "mesmo motor", é o **mesmo host de gateway**
> (`sb2bethistory-gateway-altenar2.biahosted.com`), e o que separa as marcas é o campo
> `integration` do corpo (`esportiva` × `vaidebet`). **Detecção pré-login:** a home carrega
> `sb2frontend-altenar2.biahosted.com` / `sb2wsdk-cdn-altenar2.biahosted.net` com
> `integration=<marca>` na query — dá para confirmar o motor sem credencial nenhuma, como no
> BetBy. ⚠ Registrar `ESPORTIVA` no `_CASA_DISPLAY` foi mudança retroativa sobre **351
> bilhetes** que já existiam na grafia `Esportiva` (ver o aviso do §5): a grafia foi **medida
> no banco antes**, e o round-trip foi provado em 61 grafias (0 quebradas).
>
> ⚠️ **A Betpix365 (s258) levou o "espelho não é liso" ao extremo: a casa NÃO CHAMA o
> endpoint de que ela mesma precisa.** A tela "Minhas Apostas" dispara só o
> `widgetBetHistory` **compacto** — que foi finalmente MEDIDO aqui e **não traz
> `selections`** em nenhum dos 9 bilhetes (sem perna, sem mercado, sem data de evento). O
> detalhe existe, mas num `WidgetGetBetDetails` **por item** — o anti-padrão do `CLAUDE.md`
> ("peça a FAIXA"). E o `widgetExpandedBetHistory` **responde 200 com `selections`** para
> `integration=betpix365`: a casa só não o usa.
>
> A saída foi **separar o regex que APRENDE do que CONSOME** no `vb_inject.js`:
> `RX_APRENDE = /widget(?:Expanded)?BetHistory/i` aprende url+headers de qualquer um dos dois
> e `capturarReq` reescreve o path para o Expanded; `RX` (consumir) segue casando **só** o
> Expanded, então o corpo do compacto nunca vira bilhete. **A distinção é o que mantém a
> regra da Jogo de Ouro de pé** — e os dois casos de harness travam os dois lados: o
> `jogodeouro.mjs` prova que o bilhete do widget errado não entra no lote, o `betpix365.mjs`
> prova que o Expanded é buscado mesmo quando a página nunca o pediu.
>
> **A lição geral: "a casa expõe o endpoint" e "a casa usa o endpoint" são perguntas
> diferentes.** Vale testar o endpoint conhecido com os headers da página antes de concluir
> que a casa não o tem.
>
> Outros achados da Betpix365: **"Ganhos extra"** (`bets[].bonus`) é bônus de múltipla pago
> **por fora da odd** — `totalWin ÷ stake` (4,23) ≠ `totalOdds` (4,08345), a 1ª casa Altenar
> em que a odd declarada não explica o retorno; a régua do dinheiro vence (regra global do W)
> · **`boostedBet.boostPercentage` vem `0` mesmo com boost real** — o sinal é
> `preBoostedPrice ≠ totalOdds` · selo **`GOLDEN BOOST`** (mesmo `boostProperty: 3`), 8 de 9
> boostados · tela trunca o riscado (`3.3334` → `3.33`) · `totalOdds` **não zera** em perdida
> · ⚠ **`Betpix365` ≠ `PixBet`**: casas diferentes, e a `PixBet` tem 56 bilhetes na base —
> `PIXBET` ficou **fora** do `_CASA_DISPLAY` de propósito (round-trip provado em 62 grafias,
> 0 quebradas antes e depois).

> ⚠️ **Espelho não quer dizer LISO — a Jogo de Ouro (s256) provou isso.** Ela é a 3ª casa
> Altenar e reusa tudo, mas serve **dois** widgets de histórico: o painel lateral chama
> `widgetBetHistory` (**compacto**) e só a **tela cheia** chama o `widgetExpandedBetHistory`
> que o `RX` casa. A regex **não** foi afrouxada: a única amostra do compacto veio com
> `bets: []`, ninguém mediu seus campos, e consumi-lo seria chute — o `Expanded` virou
> comentário load-bearing no inject, com o caso de harness travando que o bilhete do widget
> errado não entra no lote. **A lição geral: ao ligar uma casa espelho, confira QUAL tela
> dispara o endpoint conhecido** — "mesmo motor" não garante "mesma superfície". Quando o
> custo cai no operador (aqui: capturar com a tela cheia aberta), o autodiagnóstico da casa
> tem de dizer onde clicar, senão o erro vira "0 bilhetes" indistinguível de endpoint mudado.

> ⚠️ **Mesmo motor NÃO basta para reusar o inject — a Stake (s257) é o contra-exemplo.** Ela
> roda a **mesma Kambi da KTO** (provado pelo vocabulário: `Total de Escanteio por <time>`
> aparece literalmente nas fixtures das duas, mais `range_start`/`range_size`), e mesmo assim
> ganhou inject próprio. O motivo é que ela **não expõe a Kambi**: embrulha num REST próprio,
> com nomes snake_case, dinheiro em **reais** (não milésimos), status em **inteiro** (não
> string) e fim por `next_page_exists` (não `range.more`). **A regra que sai daqui: o que
> autoriza o reuso é o motor que CHEGA AO NAVEGADOR, não o motor que a casa licenciou.** O
> teste barato é olhar os nomes de campo de um payload real — se eles mudaram, é casa nova na
> captura, ainda que seja espelho na leitura (o `CASA_STAKE.md §9` herda o mapa da KTO).
>
> **Stake — duas armadilhas que nenhuma outra casa tinha mostrado.** (1) **`bet_total_stake`
> vem `0` em toda ANULADA**; o valor real mora em `bet_request_stake` — mesma família do
> `betOdds:0` da KTO e do `total_k:0` da Jonbet, mas no **stake**, não na odd. (2) **O dinheiro
> não distingue anulada de perdida**: as duas têm `bet_payout: 0`. A leitura financeira que a
> KTO usa (`payout == 0 → L`) marcaria toda anulada como derrota — **nesta casa o enum manda**,
> e por isso o bloco emite `Status (API): bet_status=N` cru. Generalizando: **antes de derivar
> resultado do dinheiro, prove que o dinheiro separa os casos.**
>
> **Stake — a casa PARTE a aposta em dois bilhetes** quando não aceita o stake inteiro (medido:
> 7 de 10 apostas, IDs distintos, mesmo segundo, stakes somando redondo). Os dois lados são
> bilhetes reais e viram duas linhas; a dedup por código já lida, mas qualquer análise por
> *aposta* conta em dobro. Travado no `casos/stake.mjs` com a soma esperada por par.

> **Jonbet (s248) — três coisas que só essa casa tem até agora.** (1) O motor **BetBy** renderiza
> na **própria página** (`bt-renderer.min.js`), não em iframe — o `content.js` alcança tudo. (2) A
> página dispara a lista **antes de o token existir** e toma **401**, com um corpo que **tem uma
> chave `status`** que não é status de bilhete; por isso o inject só aprende requisição **com
> `Authorization`** e só processa corpo com `results` array. (3) A odd (`total_k`) vem **0 em toda
> perdida**, com `k` guardando a real — mesma família do `betOdds` da KTO. **BetBy é plataforma:**
> casa nova que carregue `sptpub.com` é **casa espelho** pelo padrão da Betfast abaixo.

> ⚠️ **Pitaco (s270) — três coisas que nenhuma outra casa tinha mostrado.**
>
> **(1) O passivo pode ser IMPOSSÍVEL.** Até aqui, todo inject lia a resposta que a página já
> recebia (`clone().text()`), e o replay era só para repaginar. A Pitaco cancela o stream da
> própria resposta (`AbortController`): o clone morre com *"The user aborted a request"* em
> 5 de 5 tentativas medidas. O inject **só aprende url+headers** e busca o dado ele mesmo —
> e por isso `respostas` conta as do REPLAY, não as da página. Ao ligar uma casa nova, vale
> conferir se o clone realmente resolve antes de assumir o modelo passivo.
>
> **(2) Paginar pode ser PIOR que não paginar.** A paginação por número de página desta casa
> é furada de um jeito determinístico: `20 · 10 · 20 · 0 · 1`, com a página 3 repetindo o
> primeiro código da página 1 — a varredura vê **31 códigos únicos onde existem 49**. E os
> dois critérios de parada mais usados falham juntos: "página menor que a pedida = fim" é
> falso (a 2ª veio com 10 e a 3ª veio cheia), e não há `more`/`hasNext` nomeado. O que existe
> é um campo (`.5`) que **aparece só quando a página encheu E há mais**. A saída foi pedir a
> lista inteira num `pageSize` grande e escalar enquanto esse campo vier. **A própria tela da
> casa sofre do defeito** — o filtro "Perdidas" trava em 20 cards por mais que se role,
> enquanto a API tem 38 —, o que é um bom lembrete de que a conferência "contagem da tela ×
> contagem da API" pode divergir sem que o lado errado seja o nosso.
>
> **(3) Transporte binário muda o harness, não só o inject.** Protobuf sem `.proto` publicado:
> o de-para foi medido cruzando payload e card, e as fixtures guardam a resposta em base64
> (`{b64: …}`) porque ler binário por `text()` corrompe todo byte 0x80-0xFF no decode UTF-8.
> O `resposta()` do `sandbox.mjs` ganhou `arrayBuffer()` por isso — mudança aditiva, os 15
> casos anteriores não a enxergam.
>
> Outros achados: **a odd exibida é arredondada a 2 casas e não explica o retorno** (3.67x
> onde o real é 3,6795 — R$ 0,95 de erro num bilhete), com o **produto das pernas batendo em
> 49 de 49** como conferência independente · **a data do evento vem sem ano** em bilhete
> finalizado (112 de 112 pernas), e a colocação não a substitui (divergem em 41%) ·
> **retorno de bilhete aberto = potencial** (a vitória fantasma da VaideBet de novo) ·
> **anulada devolve o stake**, então o dinheiro não distingue V de W · **não há campo de
> esporte** no payload · auth **por header** (Firebase), não por cookie.
>
> ⚠️ **A casa REBATIZOU, e a grafia foi unificada na mesma sessão.** A "Rei do Pitaco" virou
> `Pitaco`, e por algumas horas as duas grafias conviveram no banco (54 bilhetes na antiga, 3
> na nova) — o `casa_canonica()` **não** funde nomes distintos, ele só normaliza caixa e
> espaço. Registrar as duas chaves funcionava, mas custava três mecanismos paralelos
> (equivalência no backstop, alias de manual, alias de exibição). O Feca decidiu que `Pitaco`
> é o nome padrão, e a unificação apagou os três: `scripts/unificar_casas.py --somente
> "Rei do Pitaco"` moveu **54 bilhetes de 2 donos** com **54 assinaturas recalculadas**,
> resíduo **zero** nas 7 tabelas.
>
> **A lição que fica é sobre a ORDEM.** Enquanto as duas chaves existiam, o backstop
> casa↔site quebrava: `casa_de_host` devolve a **primeira** chave que casa o host, então a
> comparação exata rejeitava com **409** quem pareasse pela grafia antiga e capturasse do
> site **certo**. Casa que rebatiza deve ser **unificada antes** de ser registrada — registrar
> duas grafias é uma ponte cara, não um estado de repouso. Round-trip medido nas duas pontas:
> 63 grafias no banco, **0 quebradas** antes e depois.

> ⚠️ **Novibet (s271) — a 2ª casa em que o PASSIVO É IMPOSSÍVEL, e a 1ª em que a TELA é o
> gargalo.** Plataforma própria (gateway `BlueBrown.OnlineSportsbook.Gateway`), API no mesmo
> host do site.
>
> **(1) O passivo morre igual ao da Pitaco, por outro motivo.** A página é Angular e o
> `HttpClient` aborta o próprio request ao desinscrever: `clone().text()` rejeita com *"The
> user aborted a request."*. A Pitaco ensinou o sintoma; aqui ele apareceu numa casa sem
> nenhum parentesco técnico com ela. **Vale checar o clone em toda casa nova** — o custo é uma
> medição e o preço de errar é um inject que parece funcionar (o replay cobre) enquanto o
> `respostas` do autodiagnóstico conta outra coisa.
>
> **(2) A requisição da TELA é estreita em dois eixos, e isso é novo.** Até aqui o replay
> existia para *repaginar*. Nesta casa ele existe para **alargar o filtro**: a página pede
> `dateFrom`/`dateTo` de ~24h **e** `result:2` (só fechadas). Um inject passivo perfeito
> capturaria 11 de 42 bilhetes e **nenhuma aposta em aberto** — e pareceria estar funcionando.
> O `result:null` (que a página nunca usa) devolve abertas + fechadas numa chamada.
> **A pergunta a fazer numa casa nova não é só "como pagino?", é "o que a tela NÃO pediu?".**
>
> **(3) Fim autoritativo de verdade:** `statistics.count` é o total da janela e **não muda**
> com `skip`/`take` — distingue "acabou" de "a consulta encheu", que é justamente o que o
> `Count` da Tivo não distinguia. Paginação provada por códigos ÚNICOS em três estratégias
> (`take` 50, 20 e 7 → 42/42 nas três). `take` tem teto **50** (51 → 400).
>
> Outros achados: **odd de SISTEMA não é a do card** — em `Fold2` o `placedPrice` é a SOMA dos
> produtos das C(n,k) linhas (19 de 19), e a odd estrutural é essa soma ÷ `multiplier` (a média
> do `MASTER_RESULTADO §7.3`); o card estampa `@ 10.33` num bilhete de odd real 1,097 ·
> **`cost` é o stake TOTAL e `amount` o por linha** · **`finalFinancials.payout` é sempre
> POTENCIAL**, inclusive em perdida (o retorno real é `settlement.payout`, e `settlement` é
> `null` em toda aberta) · **esporte em pt-PT** (`Ténis`, `Voleibol`) → traduzir pelo
> `competitionContextSysname` · 🚀 vem colado no nome do mercado · histórico limitado a **12
> meses** pela casa, com `maxDurationExceeded` avisando (pedir a janela cheia LIGA a flag —
> o inject deixa 2 dias de folga para o aviso não virar ruído).

> **Casa espelho — o padrão da Betfast (s211).** Quando uma casa nova roda o **mesmo motor** de
> uma já ligada, ela **não ganha inject próprio**: entra nos 12 pontos de registro apontando
> para o inject existente (`popup.js` + `content_scripts` do manifest) e reusa o ramo do
> `content.js`. O que muda é só o domínio. Duplicar `tv_inject.js` seriam 270 linhas gêmeas
> divergindo com o tempo — a dívida nº 3 do §8. **O que torna isso seguro é o teste:** o
> `casos/betfast.mjs` roda a MESMA fixture pelos dois domínios e compara os blocos byte a
> byte, então nada pode se amarrar ao host sem ficar vermelho. Antes de tratar uma casa como
> espelho, **prove o motor** (não confie na aparência): HTML servindo o mesmo loader, mesmo
> caminho de API respondendo 401 (contra 400/404 numa rota falsa) e os mesmos nomes de campo
> num payload real.
>
> ⚠ **Tivo/Betfast — `Count` é teto da CONSULTA, não fim de conta.** A Betfast respondeu
> `Count: 50` com 50 bilhetes (a Tivo, 24) e a lista dela **para aí, sem "mostrar mais"**
> (confirmado pelo operador). `len == Count` significa "a consulta encheu". **Lição geral:
> só chame de fim autoritativo o sinal que distingue os dois casos** — `more:false` e
> `isLastPage` distinguem; "o tamanho bateu" não. Quando não distinguir, use um segundo
> eixo: aqui o `gethistory` aceita `to`, então ao tocar o teto o inject varre para trás
> (`varrerParaTras`) até uma janela voltar vazia. Custa 1 requisição quando não havia nada;
> recupera o histórico inteiro quando havia. **Validado contra o servidor real** (s211):
> partindo de um teto simulado de 6 bilhetes, a varredura recuperou os 32 da conta e parou
> sozinha — ver `CASA_BETFAST §2.1.1`. O harness prova o algoritmo; só o ao vivo prova que
> a casa colabora com o segundo eixo.

Freios no popup: **dias + ID de parada** (Superbet/BETesporte/Betano/KTO/Pinnacle/Tivo/Betfast) ·
**quantidade + dias + varrer tudo** (Betfair, histórico ilimitado e fora de ordem) ·
**nenhum** (Bet365 — o freio virou o pré-dedup do backend).

---

## 5. Superfície de registro — os 12 pontos

Uma casa nova só funciona ponta a ponta se estiver em **todos** os lugares abaixo. Não há
um registro único: são listas paralelas que precisam concordar. **Rode
`python tools/audit_sharpenup.py` para conferir** — foi construído exatamente para isso.

| # | Onde | O quê | Se faltar |
|---|---|---|---|
| 1 | `casas/CASA_<KEY>.md` | tradução fina (15 seções) | roda em modo cego (funciona, traduz pior) |
| 2 | `app/main.py` `_CASA_DISPLAY` | `"KEY": "Nome Canônico"` | casa não existe para o sistema — **e ver o aviso retroativo abaixo** |
| 3 | `app/main.py` tupla do `_build_chunks` | `"KEY"` | fatia pelo frágil `\n\n` em vez do `[Código:]` |
| 4 | `app/main.py` tupla do pré-dedup | `"KEY"` | paga IA de novo por bilhete já resolvido |
| 5 | `app/repository.py` regex de código | formato do `[Código: …]` | **conferência de cobertura desligada** (perda silenciosa de chunk passa batido) |
| 6 | `app/captura.py` `_MODO_POR_CASA` | `"KEY": "texto"` | a extensão cai em modo print |
| 7 | `app/captura.py` `_HOSTS_POR_CASA` | domínios | backstop casa↔site cego no servidor |
| 8 | `app/static/index.html` `CASAS_CONECTAVEIS` | `'KEY'` | **botão "Conectar" nasce desabilitado — nada roda** (s191) |
| 9 | `app/static/index.html` `NOMES` + `DOMINIOS` | chave e domínio | seletor/favicon quebrados |
| 10 | `app/static/dash/.../data.js` + `inicio.html` | favicon (3 mapas) | ícone quebrado no dashboard/início |
| 11 | `extensor/popup.js` | `CASA_HOSTS` + dispatch do inject | aba já aberta não injeta; sem aviso de aba errada |
| 12 | `extensor/manifest.json` | `content_scripts` + **bump da `version`** | não injeta no load; ninguém vê que há versão nova |

E, dentro do `extensor/content.js`: **ouvinte** da mensagem, **`formatTicketXX`**, **`roboXXPassive`**,
**ramo no `iniciarRobo`** e **entrada no mapa de autodiagnóstico**.

### ⚠️ Registrar casa no `_CASA_DISPLAY` é mudança RETROATIVA

O ponto 2 não é só cadastro: ele **reinterpreta toda conta que já existe** numa grafia gêmea.

O `/salvar` resolve a conta por `parceiro_id` e depois roda a casa por
`_casa_display(_display_to_key(casa))`. Enquanto a chave **não** está no mapa, o
`_display_to_key` cai no ramo verbatim e o round-trip é **identidade**. Assim que ela entra,
o round-trip passa a devolver o nome do mapa — e a conta cadastrada na outra grafia deixa de
casar com o bilhete, porque a grade filtra `casa = $1` **exato**.

Foi assim que a Jonbet quebrou (s249): conta `JonBet`, bilhete gravado `Jonbet`, captura
perfeita e **grade vazia**. O sintoma é o guard da s195 com os dois nomes **iguais** —
`N salvo(s) em «X» — não aparecem na conta ativa «X»`: quem diverge é a casa, não o parceiro.

**Passo obrigatório antes de adicionar a linha:** meça a grafia que já existe no banco
(`parceiros`, `bilhetes`, `casas_meta`, `correcoes`, `uso_tokens`, `tipsters.casas`).
**A base manda, não a marca.** Na Betboom (s250) isso evitou repetir o defeito: a marca
escreve `BetBoom`, mas havia 172 bilhetes e 3 contas em `Betboom` — adotar a grafia da marca
custaria 172 recálculos de assinatura em duas bases.

Teste rápido do defeito, para toda grafia distinta de `parceiros`:
`_casa_display(_display_to_key(x)) == x`. Em 06/08/2026 dava 1 quebrada em 57.

Conserto, se escapar: `scripts/unificar_casas.py --somente <grafia>` (o `--somente` existe
porque o `MAPA` é cumulativo — sem o recorte, corrigir uma casa arrasta a base de outro dono
na mesma transação).

---

## 6. Backend da ponte

- Sessão **em memória** (`app/captura.py`): código `ABCD-EFGH` válido 15 min para conectar,
  sessão viva 6 h, fila de 60 capturas. Restart do Railway derruba as pontes — reconectar.
- `POST /captura/conectar` → `{token, casa, parceiro, modo, dono, versao_atual, desatualizada}`
- `POST /captura/validar` → o popup só diz "conectado" se a sessão existe de fato.
- `POST /captura/enviar` → `token` + `tipo=imagem|texto` + `origem` (host, backstop casa↔site).
- As três são isentas do guarda CSRF (autenticam por código/token).

## 7. Depois da ponte: o que protege o dado

| Guarda | Onde | O que evita |
|---|---|---|
| Pré-dedup por `[Código:]` | `main.py::_dedup_superbet_text` | pagar IA por bilhete já resolvido |
| Chunking por `[Código:]` | `main.py::_build_chunks` | lote grande num request só |
| **Conferência de cobertura** | `repository.py::conferir_cobertura` | **chunk que some sem erro** (s179: 39 de 61 bilhetes) |
| Correção de código | `repository.py::corrigir_codigos_tsv` | ID transposto pela IA virando duplicata |
| UPSERT por código | `repository.py::upsert_bilhetes` | aberta→resolvida atualiza, não duplica |

> A conferência de cobertura só liga se o formato do código for reconhecido (ponto 5). É a
> proteção mais barata do pipeline e a mais fácil de esquecer.

---

## 8. Limites conhecidos (dívida estrutural)

1. **`content.js` roda em TODA página** (`matches: http://*/*`) e já tem 119 KB. Cada casa
   soma ~150 linhas ao mesmo arquivo. Em ~20 casas isso é ~300 KB parseados em todo site que
   o operador abrir. Candidato a `chrome.scripting.registerContentScripts` por host.
2. **7 blocos quase idênticos** (ouvinte + formatador + robô) — ~60 % do arquivo é o mesmo
   laço com nomes trocados. Um `roboPassivoGenerico({chave, mapa, fim, formatar})` colapsaria
   isso e faria casa nova custar ~30 linhas.
3. **Os `*_inject.js` repetem o mesmo esqueleto** (hook de fetch/XHR + `postAll` + `seen`).
   `sb/be/bn_inject` são o mesmo arquivo com 4 diferenças.
4. **Os ouvintes de `message` não checam a origem.** Qualquer página poderia postar
   `__sharpenupXXData` com bilhetes forjados enquanto há pareamento ativo. Conserto barato:
   `if (ev.source !== window && ev.source !== window.top) return;`.
5. **Nenhum teste automatizado da extensão até a s192** — o harness em `extensor/harness/`
   é o começo; hoje cobre só a KTO.

---

VERSÃO: 2026
ATUALIZADO: 2026-08-17 (sessão 271 — Novibet: replay puro, e a TELA como gargalo do filtro)
