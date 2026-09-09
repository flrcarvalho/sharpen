# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-09 (sessao 337: **Blaze na captura automatica — 3a casa BetBy, sem uma linha de inject nova, e um defeito de odd que ela expos nas OUTRAS duas.** O espelho foi provado ANTES de escrever codigo e **sem login**: `/pt/sports` carrega `blaze.sptpub.com/bt-renderer` e o trafego sai em `api-31-sp-c7818b61-584` — **mesmo cluster e mesmo hash de operador da Jonbet**. Reusa `jb_inject.js`, `formatTicketJB` e `roboJBPassive`; mudou o ramo do `iniciarRobo`, o autodiagnostico e os 12 registros. **A varredura ao vivo deu 165 bilhetes** (`status` vazio, 5 cards lidos verbatim) e trouxe quatro achados que o espelho nao dispensava. (1) **A casa IGNORA o `limit` pedido**: pedi 100 e vieram 21 por pagina, oito paginas — quem avanca o `skip` pelo que PEDIU pula 79 por pagina, e o loop so nao quebra porque avanca pelo que VOLTOU. (2) **`total_k` zerou em 86 de 86 perdidas**, a armadilha conhecida da familia. (3) **A NOVA: em 4 dessas 86 o `k` TAMBEM vem zero** e a odd so existe dentro da selecao — **e o card deixa a linha "Total de odds" VAZIA**, ou seja a casa tambem nao tem o numero e nao escreve zero nenhum. Parar no `k` gravaria `0` numa coluna Odd, que e a familia do "zero nao e ausencia": passa em toda checagem de forma porque tem cara de conta feita, e num bilhete GANHO faria `stake x (0-1)` virar -1u. **O `_oddDeclJB` ganhou um terceiro degrau** (`total_k` -> `k` -> produto das selecoes -> `null`, nunca 0) e **conserta as tres casas de uma vez**. (4) `refund`/`canceled` achatam a odd para **1** — e ali o `1` e a VERDADE da tela, entao o degrau novo so pode disparar com os dois campos zerados; o caso trava os DOIS lados. **Gates:** harness 27 casos / 436 bilhetes verde, `audit_sharpenup` sem FAIL, `audit_casas` limpo (**e ele pegou uma categoria que eu inventei** — `Placar Exato` nao existe no MASTER; virou `Outros` mais um item de feedback, sem criar categoria por conta propria), e **mutacao provada nos dois sentidos**: o gate nasceu VERMELHO no bilhete certo e, com o produto vencendo sempre, acende 7 falhas, 2 delas nos `V`. A mesma mutacao passa **inocua** na Jonbet e na Betboom — espelho compartilha o conserto, nao compartilha a prova. **NAO coberto, medido e declarado no cabecalho do caso:** a conta nao tinha aposta ABERTA, cashout, boost, freebet nem sistema (`combinations` vazio em 165 de 165), e 3 dos 8 esperados vieram do corpo da resposta porque os cards de marco estavam ~100 posicoes abaixo e o filtro "Personalizado" da casa travou. **Descoberta de lado:** o BetBy da Blaze renderiza dentro de um **shadow root** — `document.body.innerText` traz 2,9 KB de casca e zero bilhete; casa assim nunca pode ter fallback de texto, porque o robo generico nao falha, ele manda a casca para a IA. **Os dois registros de `app/main.py` foram levados pelo commit da s336**, que estava com o arquivo — o caso 8 de novo, registrado e nao reescrito. Falta a validacao ao vivo, que so o operador faz. A s336 rodou em PARALELO, noutra sessao.)

_Anterior: 2026-09-09 (sessao 336: **Fase 0 da BARREIRA DE RECAPTURA no ar, e o estudo de custo remedido por usuario e por casa.** Origem: pergunta do Feca — extrair as ultimas 48h e repetir 2h depois paga hoje pelos MESMOS bilhetes, porque toda captura vai inteira para a IA e a dedup so acontece DEPOIS, no upsert. **Medido sobre 15.318 blocos reais da sombra (13 dias, 21 casas): 32,5% de tudo que pagamos e releitura de bloco IDENTICO**; na Bet365 e 39,9%. Alcance quase total: 99,3% dos bilhetes de extracao tem codigo. **A chave e o HASH DO BLOCO, nao o par (codigo, resultado) que seria o obvio:** as duas decidem igual em 97,7% dos casos e nos 2,3% restantes o bloco mudou COM o `Status:` igual, entao a chave por rotulo pularia e perderia a mudanca. Alem disso o texto de status nao e fonte confiavel de estado (`_resultadoB3` escreve `Ganho → W` para QUALQUER retorno maior que a stake, meia vitoria inclusive) — comparar bytes nao herda esse defeito porque nao interpreta nada. E liquidar nao mexe so no status: a odd muda junto, de potencial para `Retorno ÷ Stake`. **Simulado lote a lote e VALIDADO contra a conta real (erro +4,5%): −29,3% da conta, R$ 0,092 → R$ 0,065 por bilhete.** **Velocidade quase nao muda** e isso esta escrito no plano para ninguem prometer o que nao vai acontecer: a mediana fica em 30,5s (os pedacos ja correm em paralelo, o relogio e UM pedaco vezes o numero de ondas), so o p99 cai 43,7%; o ganho de verdade e a extracao que fica VAZIA, 30s viram menos de 1. **Esta fase NAO FILTRA NADA** — tabela `bloco_visto`, gravacao do hash no `done` e um log dizendo quantos blocos SERIAM pulados, para conferir o numero em producao antes de qualquer byte deixar de ser processado. **O custo remedido por usuario e por casa mostrou o driver unico:** o custo por bilhete e quase inteiramente funcao de BILHETES POR CHAMADA, porque o manual de 48k tokens e relido a cada pedaco. perereca faz 55,9 bilhetes/chamada e paga R$ 0,037; Marques19981 faz 2,4 e paga R$ 0,414. **E a Bet365 NAO e cara, ela e grande:** R$ 0,080/bilhete, ABAIXO da media de R$ 0,092 e a mais barata entre as casas de volume. A cara e a KTO, R$ 0,429 com 1,7 bilhete por chamada. **Gates:** 11 testes novos, 783 passed / 30 skipped, mutacao provada por fora (hash constante derruba 4 casos, restaurar devolve o verde) e uma mutacao INOCUA registrada como tal em vez de disfarcada. A s335 rodou em PARALELO, noutra sessao.)

_Anterior: 2026-09-09 (sessao 335: **tres casas novas no SharpenUp, num motor novo: Rogue.** Betao, R7 e 7Games sao espelho de verdade, servido do PROPRIO dominio da casa em `/api/sportsbook/rogue/...`, como a Novibet. Nao e Altenar, nao e BetBy, nao e Kambi, nao e BetConstruct. Um `rg_inject.js` e um `formatTicketRG` servem as tres, e a irmandade foi MEDIDA antes de escrever codigo (mesma stack Next.js, mesmo conjunto de hosts, mesmo mapa de endpoints extraido dos bundles das tres). **O contrato:** `GET /v1/betsreporting/purchases?status=all&take=<1..100>&skip=<n>&fromDate&toDate` com `authorization: Bearer`, devolvendo `{Purchases, PurchasesCount}`; `take` tem teto de 100 e a casa DIZ o limite (`ErrorCode 2003`) em vez de truncar calada. **A semantica saiu do DINHEIRO, nao do rotulo** (a API manda enum numerico puro), provada em 27 de 27 bilhetes: `BetStatusId` 0 com saldo 0 e sem `Result` e aberta, 1 e L, 2 com `saldo = stake x odd` e W, 4 com `saldo = stake` exato e V. **A armadilha central e o `Gain`:** ele e o retorno POTENCIAL e vale `stake x odd` em 27/27, INCLUSIVE em perdida e em aberta; o realizado e `CurrentBetBalance`. Quem le o campo obvio marca toda perda como ganho, que e o `totalWin` da VaideBet (s210) com o terceiro nome. **Dois achados mudaram o codigo:** (1) a TELA E ESTREITA, abre em `Ult. 24 horas` com `take=10` e no recon o filtro de 30 dias do Betao devolvia `PurchasesCount: 0` numa conta com 9 bilhetes, entao o replay alarga para 36 meses e pede `status=all`; (2) **o Bearer EXPIRA**, medido testando o inject contra a casa real (token de ~1h responde 401), e guardar so a PRIMEIRA requisicao fazia o contexto envelhecer junto com a aba. **A gemea `r7.bet` foi unificada ANTES do registro** (a base decidiu: 40 bilhetes de 2 donos contra 1), senao o bilhete do Jaao26 ficaria numa casa que a conta dele nao enxerga, o defeito da s249. **O gate pegou um defeito meu antes de subir:** `_casaConectavel()` normalizava espaco mas nao ACENTO, e a chave e `BETAO` enquanto o display e `Betao` com til, entao o botao Conectar nasceria desabilitado (o bug da s191 na terceira encarnacao). **Gates:** harness 26 casos / 428 bilhetes, `audit_sharpenup` 31 casas sem FAIL nem WARN, `audit_casas` limpo, check-tokens verde, 772 passed, e **mutacao 12 de 12 detectadas** (as duas que escaparam de primeira eram buraco de TESTE, nao de codigo, e viraram caso proprio). **NAO coberto, medido:** as 27 apostas sao todas simples, sem multipla, sistema, cashout, freebet nem meia-liquidacao. Falta a Fase 7, que so o operador faz.)


> **Histórico completo das sessões 332 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 337)

### Blaze: a terceira casa BetBy, e o degrau de odd que ela expôs nas outras duas

Detalhes em [`casas/CASA_BLAZE.md`](casas/CASA_BLAZE.md). O espelho foi **provado antes de
escrever código e sem login**: `/pt/sports` carrega `blaze.sptpub.com/bt-renderer`, e o
tráfego sai em `api-31-sp-c7818b61-584` — **mesmo cluster e mesmo hash de operador da
Jonbet**. Zero arquivo de captura novo: reusa `jb_inject.js`, `formatTicketJB` e
`roboJBPassive`.

Varredura ao vivo de **165 bilhetes** (`status` vazio), com 5 cards lidos verbatim na tela.

### O achado que muda código: a odd que a casa NÃO tem

`total_k` veio `"0"` em **86 de 86 perdidas** — a armadilha conhecida da família. A nova é
que **em 4 dessas 86 o `k` também vem zero**, e a odd só existe dentro da seleção.

E o card concorda com a API: a linha **"Total de odds" aparece VAZIA**. A casa também não
tem o número, e não escreve zero nenhum.

Parar no `k` gravaria `0` numa coluna Odd. É a família do *"zero não é ausência"*: o `0`
passa em toda checagem de forma porque tem cara de conta feita — e num bilhete **ganho**
faria `stake × (0 − 1)` virar `−1u`. O `_oddDeclJB` ganhou um terceiro degrau:

```
total_k, se ≠ 0  →  k, se ≠ 0  →  produto das seleções, se todas > 0  →  null (nunca 0)
```

**Conserta as três casas de uma vez.** E o degrau só pode disparar com os dois campos
zerados: em `refund`/`canceled` a casa achata a odd para **1** e ali o `1` é a verdade da
tela — o produto das pernas (2,5 · 1,5) seria invenção nossa por cima do card. O caso do
harness trava os **dois** lados.

### O que a paginação ensinou

Pedi `limit=100` e a Blaze devolveu **21 por página**, oito páginas, `count` constante em
165. A casa **ignora o `limit` pedido**. Quem avança o `skip` pelo que pediu pula 79
bilhetes por página; o loop do `jb_inject` só não quebra porque avança pelo tamanho que
**voltou**.

### Gates, e as duas coisas que eles pegaram

| Gate | Resultado |
|---|---|
| `node extensor/harness/run.mjs` | verde — 27 casos, **436 bilhetes** |
| `python tools/audit_sharpenup.py` | sem FAIL |
| `python tools/audit_casas.py` | limpo |
| `pytest tests/` | 773 passed (as falhas restantes são da s336, em curso noutra sessão) |

O `audit_casas` **pegou uma categoria que eu inventei**: `Placar Exato` não existe no
`MASTER_APOSTAS §3`. Virou `Outros ⚠️` mais um item de feedback no rodapé do arquivo da
casa — criar categoria é decisão do Feca e arrasta a propagação inteira.

E a **mutação foi provada nos dois sentidos**: o gate nasceu **vermelho** no bilhete certo
e, com o produto vencendo sempre, acende 7 falhas — 2 delas exatamente nos `V`. A mesma
mutação passa **inócua** na Jonbet e na Betboom: espelho compartilha o conserto, não
compartilha a prova.

### O que NÃO está coberto (medido, e escrito no cabeçalho do caso)

A conta não tinha **aposta aberta**, **cashout**, **boost**, **freebet** nem **sistema**
(`combinations` vazio em 165 de 165). E 3 dos 8 valores esperados vieram do corpo da
resposta, não do card: os bilhetes de março estão ~100 posições abaixo na lista e o filtro
"Personalizado" da casa travou carregando nas duas tentativas.

**Descoberta de lado:** o BetBy da Blaze renderiza dentro de um **shadow root** —
`document.body.innerText` traz 2,9 KB de casca e nenhum bilhete. Casa assim nunca pode ter
fallback de texto: o robô genérico não falharia, ele mandaria a casca para a IA.

**Pendente:** a validação ao vivo (recarregar a extensão, Ctrl+Shift+R na aba da Blaze e
capturar), que só o operador faz.

### Duas sessões, um index: os registros de `app/main.py` foram levados pela s336

Aconteceu de novo o [caso 8](docs/CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026),
e desta vez a favor: os dois registros da Blaze em `app/main.py` (`_CASA_DISPLAY` e
`_CASAS_MARCADOR_CODIGO`) entraram no commit `2143c06` da s336, que estava com o arquivo
para a Fase 1 da barreira. **Histórico já enviado não se reescreve** — fica registrado aqui
e segue. O resto dos 12 pontos veio no commit desta sessão.

Vale a lição inversa da regra: quando o arquivo é o MESMO, `git add` por nome não separa
nada. Antes de editar `main.py` com outra sessão aberta, o barato é combinar quem leva.

---

## Sessão 336 — a barreira de recaptura, Fase 0

### A barreira de recaptura: Fase 0 no ar, medindo sem filtrar

O plano inteiro está em
[`docs/PLANO_BARREIRA_RECAPTURA.md`](docs/PLANO_BARREIRA_RECAPTURA.md). Ele nasceu de uma
pergunta do Feca que virou medição.

**O problema, medido:** toda captura vai inteira para a IA, e a dedup só acontece depois,
no `upsert`. Dos 15.318 blocos com código que passaram pela IA em 13 dias, **4.975
(32,5%) eram releitura de bloco byte a byte idêntico**. Na Bet365, 39,9%.

| | Blocos | % |
|---|---|---|
| Primeira leitura | 8.753 | 57,1% |
| **Releitura IDÊNTICA** | **4.975** | **32,5%** |
| Releitura de bilhete que mudou | 1.590 | 10,4% |

### Por que hash do bloco, e não (código, resultado)

A proposta original era conferir ID e resultado. Medida contra o hash do bloco inteiro,
as duas decidem igual em **97,7%** dos casos. Nos 2,3% restantes o bloco mudou com o
`Status:` igual, e a chave por rótulo pularia.

Mas o argumento que decide é outro: **o texto de status não é fonte confiável de estado.**
`_resultadoB3` escreve `Ganho → W` para qualquer retorno maior que a stake, meia vitória
inclusive. Chave que lê rótulo herda esse defeito; chave que compara bytes não tem o que
herdar. É o mesmo princípio do "o rótulo não é a prova, o número é".

E liquidar não mexe só no status. Caso real da Novibet: a odd vai de `4,59` (potencial)
para `2,89` (`Retorno ÷ Stake`) na mesma leitura.

### O ganho, e o que ele NÃO é

Simulação lote a lote, com modelo calibrado nos agregados de `uso_tokens` e **validado
contra a conta real: erro de +4,5%**.

| | Hoje | Pós-barreira |
|---|---|---|
| Conta de API | US$ 391/mês | **US$ 281/mês** |
| Custo por bilhete | R$ 0,092 | **R$ 0,065** |

**Velocidade quase não muda, e isso está escrito no plano de propósito.** A mediana fica
em 30,5s: os pedaços já correm em paralelo, então o relógio é o tempo de UM pedaço vezes o
número de ondas, e uma extração de 20 bilhetes vira 4 pedaços antes e depois. Só o p99 cai
43,7%. O ganho real é a extração que fica **vazia** (30s viram menos de 1), que hoje seria
2,3% delas — número subestimado, porque reflete o hábito de quem paga caro para
recapturar.

### A Fase 0 não filtra nada, e é para isso que ela existe

Tabela `bloco_visto`, gravação do hash no `done` da extração, e um log dizendo quantos
blocos **seriam** pulados. Serve para conferir em produção o número da simulação **antes**
de qualquer byte deixar de ser processado.

### As quatro costuras da Fase 1, todas silenciosas se erradas

Estão no `§6` do plano. Nenhuma dá erro; todas dão dado faltando em silêncio.
`conferir_cobertura` precisa saber do filtro (senão acusa perda que não houve);
`_reconciliar_orfas` precisa ver **todos** os blocos, não só os filtrados (senão uma órfã
perde a adoção e vira fantasma, o caso do Falkirk); bilhete sem código não passa pela
barreira; e lote vazio é sucesso, não erro.

### O custo remedido por usuário e por casa: existe um driver único

O custo por bilhete é quase inteiramente função de **bilhetes por chamada**, porque o
manual de 48k tokens é relido a cada pedaço.

| | R$/bilhete | Bilhetes por chamada |
|---|---|---|
| perereca | 0,037 | 55,9 |
| Feca | 0,102 | 12,2 |
| Marques19981 | **0,414** | 2,4 |

**E a Bet365 não é cara, ela é grande:** R$ 0,080 por bilhete, **abaixo** da média de
R$ 0,092 e a mais barata entre as casas de volume. É 42% da conta por volume, não por
ineficiência. A cara é a KTO, R$ 0,429 com 1,7 bilhete por chamada.

> Isso corrige a leitura do `ESTUDO_PRECIFICACAO §1.3`, que listava a Bet365 como o topo
> do custo sem separar volume de eficiência.

---

## Sessão 335 — três casas novas na captura

### Três casas novas no SharpenUp, e um motor novo: **Rogue**

Betão, R7 e 7Games são espelho de verdade. Rodam a mesma plataforma, servida do **próprio
domínio da casa** em `/api/sportsbook/rogue/…`, como a Novibet. Não é Altenar, não é BetBy,
não é Kambi, não é BetConstruct. Um `rg_inject.js` e um `formatTicketRG` servem às três.

A irmandade foi medida antes de escrever código: mesma stack Next.js, mesmo conjunto de
hosts, mesmo mapa de endpoints extraído dos bundles das três, mesma rota de histórico
(`/account/sports-history`), mesmos campos.

**O contrato:**

```
GET /api/sportsbook/rogue/v1/betsreporting/purchases
    ?status=all&take=<1..100>&skip=<n>&locale=br-pt&fromDate=<ISO>&toDate=<ISO>
    header: authorization: Bearer <JWT da sessão>
→ {"Purchases":[…], "PurchasesCount": <total da janela>}
```

`take` tem teto de 100 e a casa **diz** o limite (`ErrorCode 2003`) em vez de truncar calada.
`PurchasesCount` é o fim autoritativo da paginação por `skip`.

### A semântica saiu do dinheiro, não do rótulo

A API manda enum numérico puro. O de-para foi provado em **27 de 27** bilhetes das três
contas:

| `BetStatusId` | `CurrentBetBalance` | → |
|---|---|---|
| 0 | `0` e sem `Result` | aberta |
| 1 | `0` | L |
| 2 | `= stake × odd` | W |
| 4 | `= stake` exato | V |

**A armadilha central é o `Gain`:** ele é o retorno POTENCIAL e vale `stake × odd` em 27/27,
inclusive em perdida e em aberta. O realizado é `CurrentBetBalance`. Quem lê o campo óbvio
marca toda perda como ganho: é o `totalWin` da VaideBet (s210) e o `finalFinancials.payout`
da Novibet (s271), com o terceiro nome de campo.

### Dois achados que mudaram o código

**A tela é ESTREITA.** O histórico abre em "Últ. 24 horas" com `take=10`. No dia do recon, o
filtro de 30 dias do Betão devolvia `PurchasesCount: 0` numa conta com 9 bilhetes. Um
passivo puro pareceria funcionar (hook ativo, respostas > 0) e entregaria quase nada. O
replay alarga para 36 meses e pede `status=all`.

**O Bearer EXPIRA.** Achado testando o inject contra a casa real: token de ~1h responde
**401**, não 403. A primeira versão guardava só a PRIMEIRA requisição, então numa aba aberta
desde a manhã o replay sairia com token vencido e voltaria vazio, com 401 e "endpoint mudou"
lendo igual no painel. Agora o contexto é renovado a cada busca da página, e há gate travando
isso nos dois sentidos (sobrescrever com token melhor, nunca com token nenhum).

### A gêmea `r7.bet` foi unificada ANTES do registro

A base decidiu, não a marca: `R7` tinha 40 bilhetes de 2 donos, 3 contas e 17 correções,
contra 1 bilhete e 2 contas em `r7.bet`, que é um domínio cadastrado à mão. Na ordem inversa,
o bilhete do Jaao26 ficaria numa casa que a conta dele não enxerga: grade vazia, sem erro
nenhum, o defeito da s249. Aplicado com `--somente r7.bet`, 1 bilhete e 1 assinatura
recalculada, 10 outras linhas, zero colisão. Round-trip nas 94 grafias de `parceiros`: 0
quebradas antes e depois.

### O gate pegou um defeito meu antes de subir

`_casaConectavel()` normalizava espaço mas não ACENTO, e a chave é `BETAO` enquanto o display
é `Betão`. O botão "Conectar" nasceria desabilitado: o bug da s191 na terceira encarnação
(s256 foi o espaço). Corrigido na raiz com `normalize('NFD')`, medido antes de mudar: nas 31
grafias de display conhecidas, zero mudança de comportamento.

### Gates

Harness **26 casos / 428 bilhetes**, `audit_sharpenup` 31 casas sem FAIL nem WARN,
`audit_casas` limpo, `check_docs` sem âncora quebrada, check-tokens verde, **772 passed**.

**Mutação: 12 de 12 detectadas.** Duas escaparam de primeira e as duas eram buraco de TESTE,
não de código: a regra "data da perna mais recente" não é exercível por fixture nenhuma
(todos os 27 bilhetes são de uma perna só) e nada disparava requisição sem `authorization`.
As duas viraram caso próprio.

### O que NÃO foi coberto

As 27 apostas são **todas simples**. Sem múltipla, sistema, cashout, freebet, bet builder ou
meia-liquidação: `BetTypeId` 1, `ComboSize` 0 e `NumberOfLines` 1 em 27/27, `AdditionalTickets`
vazio em todos, `PromotionIds` vazio em todos. Os endpoints `/v1/cashout/*` existem no bundle
e nenhum bilhete passou por eles. Está registrado como **não medido** nos três `CASA_*.md`,
não como resolvido.

### Próximo passo

**Fase 7, que só o operador faz.** Recarregar a extensão, dar Ctrl+Shift+R na aba de cada
casa, F5 no dashboard, conectar e conferir contagem, datas, odds e código. A validação ponta
a ponta com a extensão carregada é a única coisa que o harness não alcança: o hook precisa
rodar em `document_start`, antes de o bundle capturar o `fetch`.

Quando aparecer a primeira múltipla ou o primeiro cashout numa das três, a fixture volta para
`extensor/harness/fixtures/` e o caso trava a leitura nova.

---

## Sessão 334 — o tradutor determinístico da Bet365, Fase 1

### O mapa da Bet365 cresceu, e a régua de aceite cresceu junto

A Fase 1 do tradutor já existia desde a s301. Esta sessão mediu o que ele cobre, achou o
buraco e fechou parte dele com evidência.

| | Antes | Depois |
|---|---|---|
| Cobertura | 66,6% | **70,7%** |
| Bateu tudo | 76,1% | **77,0%** |
| Divergência de descrição | 21,4% | **20,5%** |

### A régua que a medição obrigou a criar

Eu ia aceitar rótulo por **categoria estável** (maioria ≥ 95% do que a IA decidiu, com
≥ 5 casos). Dezessete passaram. Aplicando, a cobertura subiu para 73,5% e **a divergência
de descrição subiu junto**, de 21,4% para 22,8%. Foi aí que a segunda régua apareceu:
**acertar a categoria não basta, a descrição tem de bater também.**

Dez rótulos saíram, e caem em duas famílias que pedem código, não linha de tabela:

- **Prop de SIM/NÃO.** A seleção é `Sim` e quem carrega a aposta é o rótulo.
  `Terminar com Pontos` sai daqui `Franco Colapinto - Sim` e a IA escreve
  `Franco Colapinto - Terminar com Pontos`. 52 casos, 98% de divergência.
- **Escopo de tempo.** `1º Tempo - Escanteios Asiáticos` sai `Over 3.5 Escanteios` e a IA
  escreve `Over 3.5 Escanteios 1º Tempo`. O período **não** é qualificador descartável
  como `Time da Casa -`: ele muda a aposta.

> Sintoma para reconhecer isto noutro gate: a régua mediu um campo e deixou o vizinho
> livre. É a mesma família do "gate que confere UM campo deixa os vizinhos livres" do
> `CLAUDE.md`, e aqui ela quase gravou descrição errada em silêncio em dez rótulos.

### A ordem do corte `- N Opções` é load-bearing

`- 2 Opções` e `- 3 Opções` contam as **saídas** do mercado (com ou sem o empate) e nunca
mudam a categoria, então cortar o sufixo resolve `Escanteios - 2 Opções` pela entrada
`escanteios`. Mas o corte é a **última** tentativa, nunca a primeira: `Total - 2 Opções`
está no mapa por inteiro, e cortar antes deixaria a chave em `total`, que não existe,
derrubando 498 blocos de uma vez. Há teste de mutação para os dois sentidos.

### O que a triagem dos 20% revelou

Quase nada é o tradutor errando. Das 1.376 divergências de descrição: **657 (47,7%)** são
nome de time localizado (`USA (W)` contra `EUA (F)`, limitação declarada no cabeçalho do
módulo), **538 (39,1%)** são notação de número e **81 (5,9%)** são a IA escrevendo
`Mais de` onde o MASTER manda `Over`.

Das 538, **520 (96,7%) são notação, não valor**: o MASTER mostra `Over 2.5 Gols` com ponto
e **não diz nada sobre linha partida**. É ali que a IA improvisa, escrevendo o mesmo caso
de três jeitos (`2,5/3,0`, `4,25`, `3.25`). Buraco de MASTER, não defeito de tradutor, e
virou decisão no [`BACKLOG §3.8`](BACKLOG.md).

### A Betano espera, e o motivo é amostra

Ela usa 686 rótulos contra 228 da Bet365 porque **embute nome próprio no rótulo**
(`Josh Coburn Total de chutes`, `Coritiba Total de Cartões`). Normalizando por sufixo eles
colapsam 60%, de 686 para 271, o que resolve o vocabulário. O que não resolve é a amostra:
ela tem **552 bilhetes de uma seleção contra 7.779 da Bet365**, porque é dominada por
`Criar Aposta` e múltipla, onde a categoria é estrutural e não diz nada sobre o rótulo.

---

---

## 1. O que estamos construindo

A base de conhecimento (masters) do scanner de bets. Camada **global** (regra única, muda devagar) + camada **por casa** (traduz cada casa para a língua global). A saída final é **TSV**.

---

## 2. Invariantes (não se quebram)

1. O app **lê** os masters, **nunca escreve** neles. Mudança de regra = diff revisado por humano + commit. Git é a porta de aprovação.
2. O arquivo de casa **traduz** a casa para a língua global; **não redefine** regra global.
3. **Cálculo é global, localização é da casa.** Ex.: "W → Retorno÷Stake" é global; "o retorno está no campo PRÊMIO" é da Superbet.
4. Nenhuma regra nova é aplicada sozinha. Propor como diff, esperar aprovação.

---

## 3. Estrutura-alvo do repo

```
/global/                 (autoridade única — 6 masters)
    MASTER_PIPELINE_2026.md
    MASTER_ESPORTES_2026.md
    MASTER_APOSTAS_2026.md
    MASTER_DESCRICAO_2026.md
    MASTER_RESULTADO_2026.md
    MASTER_OUTPUT_2026.md
/casas/                  (1 arquivo por casa — traduz, nunca redefine)
    CASA_MODELO.md         (gabarito — 15 seções)
    CASA_BET365.md
    CASA_BETANO.md
    CASA_BETESPORTE.md
    CASA_BETFAIR.md
    CASA_BETNACIONAL.md
    CASA_BOLSADEAPOSTA.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_NOVIBET.md        (plataforma própria BlueBrown — replay que ALARGA o filtro)
    CASA_PINNACLE.md
    CASA_PITACO.md         (ex-"Rei do Pitaco" — gRPC-Web/protobuf; 2 grafias, 1 manual)
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_JONBET.md
    CASA_BETBOOM.md        (espelho técnico da Jonbet — mesmo motor BetBy/sptpub)
    CASA_VAIDEBET.md
    CASA_ESPORTIVA.md      (espelho técnico da VaideBet — mesmo motor Altenar/BIA)
    CASA_JOGODEOURO.md     (3ª casa Altenar — captura na TELA CHEIA do histórico)
    CASA_BETPIX365.md      (4ª casa Altenar — a casa NÃO chama o endpoint que ela precisa)
    CASA_ESTRELABET.md     (5ª casa Altenar — a mais lisa na tela; o gateway recusa credencial)
    CASA_STAKE.md          (mesma Kambi da KTO, mas REST próprio — captura NÃO é espelho)
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (guias, referências, ADRs, planos VIVOS — índice em docs/README.md)
    CASOS.md               (os casos que originaram as regras do CLAUDE.md; não auto-carregado)
    HISTORICO.md           (índice) → historico/  (6 partições por faixa de sessão)
    arquivo/               (o que virou registro; índice em arquivo/README.md)
CLAUDE.md                  (regras vinculantes)
STATUS.md                  (este arquivo — estado atual + as 3 últimas sessões)
BACKLOG.md                 (tudo que está aberto)
```

**Um arquivo, uma pergunta** (invariante #10), com gate em `python tools/check_docs.py`.

Os 6 MASTER_*.md vivem em `/global/`; as **28** casas em `/casas/` (Polymarket por API, as demais por IA/texto), mais o gabarito `CASA_MODELO.md`.

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Identidade na tabela `usuarios` do Postgres via cache em memória (s233 — Fase 1 do `docs/PLANO_MULTIUSUARIO_2026.md`); os dicts de `app/auth.py` são a SEMENTE. Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway (o seed leva ao banco no boot); base nasce vazia sem migration. Suspender no banco (`status`) revoga login E sessão em ≤60s.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Base do `LavaPessoal` (s222):** 2.877 apostas importadas do `.xlsx` pessoal do Lava (23/02 → 30/07/2026), `origem='import'`, conta `Padrão` em cada uma das 19 casas (ele não anota fornecedor). Script próprio e idempotente: `scripts/import_lavapessoal_xlsx.py` (re-rodar limpa só `origem='import'` daquele dono; captura da extensão sobrevive). **Não confundir com o dono `Lava`** — são bases distintas que só compartilham o apelido. **O P/L do dashboard não bate com a planilha de origem por desenho** (ela contabiliza em unidade; ver s222 no topo).
- **Base do `SoChutes` (s224):** 23.199 apostas all-time do tipster Só Chutes (17/09/2024 → 27/07/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` (Bet365/Superbet/Betano; casa não informada entrou como Bet365 — decisão do Feca). **Stake em UNIDADES** (1u = 1; o P/L do dashboard é o P/L em unidades: +1.381,29u). Script idempotente: `scripts/import_sochutes_xlsx.py`. O planilhamento novo é do **bot Sharpen** (repo próprio `BOTS/sharpen-bot`, ver s223), que desde a **s251** roda 24/7 no Railway — serviço `sharpen-bot`, no mesmo projeto do app, com o estado em volume próprio. Ele escreve nesta base por `/salvar` + `/bilhetes/tipster`: **mudança no contrato dessas rotas quebra o bot em silêncio.**
- **Base do `Flurray` / tipster Fleury (s260):** 473 apostas (11/06 → 09/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 4 casas (Bet365, Betano, Superbet, BetMGM). Base de **nicho**: 100 % mercados de finalização no futebol. **Stake em UNIDADES** (1u = 1; P/L +122,30u sobre 447,80u de turnover). Script idempotente: `scripts/import_fleury_xlsx.py`. **⚠️ A marca é `Fleury` e o username é `Flurray`** — o `dono` é sempre o username; a ponte entre os dois é o `TIPSTERS_PUBLICOS`. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/fleury`** (3ª do sistema).
- **Base do `passapano` / tipster PassaTips VIP (s273):** 911 apostas (02/06 → 17/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 7 casas (Bet365, Betano, Betnacional, Betvip, Estrela Bet, Novibet, Suprema Bet). Base **multiesporte**: 20 esportes, de futebol e tênis a polo aquático e críquete. **Stake em UNIDADES** (1u = 1; P/L +90,20u sobre 1.102,61u de turnover liquidado). Script idempotente: `scripts/import_passatips_xlsx.py`. **⚠️ A marca é `PassaTips VIP` e o username é `passapano`** — mesmo caso do Fleury. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/passatipsvip`** (5ª do sistema). O planilhamento novo é do **bot Sharpen** (4º tenant, `passatips`) — **1º perfil sem visão**, porque a legenda dele já traz tudo.
- **Casas:** 28 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **25 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210), **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`), BetNacional, Jonbet (BetBy/sptpub, s248), **Betboom** (s250 — **espelho da Jonbet**: mesmo motor BetBy, mesmo `jb_inject.js`) **Pitaco** (s270 — plataforma própria, **gRPC-Web/protobuf binário**, replay puro) **Novibet** (s271 — plataforma própria BlueBrown, replay puro que **alarga o filtro** da tela: ela pede 24 h e só as fechadas) e **Estrela Bet** (s303 — **5ª casa Altenar**, mesmo `vb_inject.js`; a mais lisa na TELA e a única cujo gateway **recusa `credentials:"include"`**). **Dois pares de espelho, zero código duplicado** — o inject casa por caminho de API, nunca por host, e é isso que faz a casa seguinte da mesma plataforma custar registro em vez de implementação.
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências

> **As pendências mudaram de casa.** Elas moram em **[`BACKLOG.md`](BACKLOG.md)**, na raiz —
> organizadas por natureza (bloqueado por humano · por amostra · decisão do Feca · dívida
> técnica medida · planos com fase aberta · não medido), com as marcas
> **VIVA / NÃO-MEDIDA / HUMANA** da varredura da s261 preservadas.
>
> Motivo: o §5 tinha **51 KB** e ficava atrás de 124 KB de changelog. Quatro arquivos
> disputavam o papel de "onde o projeto está" e três descreviam o projeto de julho. Ver
> [`docs/FAXINA_PROPOSTA.md`](docs/FAXINA_PROPOSTA.md).
>
> **Pendência nova vai para o `BACKLOG.md`, nunca para cá** (invariante #10 do `CLAUDE.md`).
> Gate: `python tools/check_docs.py`.

As três mais quentes de hoje, com o resto no `BACKLOG.md`:

1. **`apps_script/Code_LavaFatuch.gs` expõe a base do Fatuch sem autenticação nenhuma.**
   `doGet(e)` na linha 95, zero token ou segredo no arquivo — e é a fronteira que alimenta o
   `app/planilha_viva.py`, a base financeira **ao vivo** de um cliente. Qualquer um com a URL
   lê. Medido em 06/09. → `BACKLOG §4.3`, e é sessão própria.

2. **PassaTips: 3 passos humanos para fechar o buraco do #259, e a ORDEM importa.**
   Enquanto o painel do #259 estiver armado, um clique ✅ vira o `L` do dia 17 em `W`
   (`resultado` não é congelado). O `/anular #259` **apaga** a linha `Under 1.5 cartões
   Elche`, então o tipster tem de repostar **antes**. → `BACKLOG §1`.

3. **Polymarket ainda mistura `entry_odd` e `realized_odd`** (`AUDITORIA_2026 #32`).
   `_calc_odd` (`app/polymarket.py:894`) devolve um número só, e o próprio comentário da
   `:987` admite "odd de entrada, **ou** a efetiva na liquidação". É o maior risco quant
   aberto e mexe em P/L. → `BACKLOG §4.1`.

---

## 6. Rodar / produção

**App em produção:** `https://sharpen.bet/` (www.sharpen.bet → Railway)

Para rodar localmente:
```
cd app
pip install -r requirements.txt
# .env na raiz do Planilhador com ANTHROPIC_API_KEY e DATABASE_URL
uvicorn main:app --reload
# Abrir http://localhost:8000
```

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/sharpen`, renomeado de `extrator` na sessão 129). Deploy automático via Railway conectado ao GitHub — push dispara deploy.
