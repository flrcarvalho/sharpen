# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-09 (sessao 335: **tres casas novas no SharpenUp, num motor novo: Rogue.** Betao, R7 e 7Games sao espelho de verdade, servido do PROPRIO dominio da casa em `/api/sportsbook/rogue/...`, como a Novibet. Nao e Altenar, nao e BetBy, nao e Kambi, nao e BetConstruct. Um `rg_inject.js` e um `formatTicketRG` servem as tres, e a irmandade foi MEDIDA antes de escrever codigo (mesma stack Next.js, mesmo conjunto de hosts, mesmo mapa de endpoints extraido dos bundles das tres). **O contrato:** `GET /v1/betsreporting/purchases?status=all&take=<1..100>&skip=<n>&fromDate&toDate` com `authorization: Bearer`, devolvendo `{Purchases, PurchasesCount}`; `take` tem teto de 100 e a casa DIZ o limite (`ErrorCode 2003`) em vez de truncar calada. **A semantica saiu do DINHEIRO, nao do rotulo** (a API manda enum numerico puro), provada em 27 de 27 bilhetes: `BetStatusId` 0 com saldo 0 e sem `Result` e aberta, 1 e L, 2 com `saldo = stake x odd` e W, 4 com `saldo = stake` exato e V. **A armadilha central e o `Gain`:** ele e o retorno POTENCIAL e vale `stake x odd` em 27/27, INCLUSIVE em perdida e em aberta; o realizado e `CurrentBetBalance`. Quem le o campo obvio marca toda perda como ganho, que e o `totalWin` da VaideBet (s210) com o terceiro nome. **Dois achados mudaram o codigo:** (1) a TELA E ESTREITA, abre em `Ult. 24 horas` com `take=10` e no recon o filtro de 30 dias do Betao devolvia `PurchasesCount: 0` numa conta com 9 bilhetes, entao o replay alarga para 36 meses e pede `status=all`; (2) **o Bearer EXPIRA**, medido testando o inject contra a casa real (token de ~1h responde 401), e guardar so a PRIMEIRA requisicao fazia o contexto envelhecer junto com a aba. **A gemea `r7.bet` foi unificada ANTES do registro** (a base decidiu: 40 bilhetes de 2 donos contra 1), senao o bilhete do Jaao26 ficaria numa casa que a conta dele nao enxerga, o defeito da s249. **O gate pegou um defeito meu antes de subir:** `_casaConectavel()` normalizava espaco mas nao ACENTO, e a chave e `BETAO` enquanto o display e `Betao` com til, entao o botao Conectar nasceria desabilitado (o bug da s191 na terceira encarnacao). **Gates:** harness 26 casos / 428 bilhetes, `audit_sharpenup` 31 casas sem FAIL nem WARN, `audit_casas` limpo, check-tokens verde, 772 passed, e **mutacao 12 de 12 detectadas** (as duas que escaparam de primeira eram buraco de TESTE, nao de codigo, e viraram caso proprio). **NAO coberto, medido:** as 27 apostas sao todas simples, sem multipla, sistema, cashout, freebet nem meia-liquidacao. Falta a Fase 7, que so o operador faz.)

_Anterior: 2026-09-09 (sessao 334: **Fase 1 do tradutor deterministico avancada na Bet365. Cobertura de 66,6% para 70,7% COM a divergencia de descricao caindo de 21,4% para 20,5%** — subir uma e baixar a outra e a unica combinacao que autoriza seguir. **A sombra medida:** 15.181 pares, 13 dias, 21 casas. A Bet365 usa 228 rotulos de mercado, ou 180 depois de normalizar; **40 cobrem 90% das linhas** e a cauda e 0,18%. Um dicionario por voto de maioria concorda com a IA em **97,66%**. A Betano usa 686 rotulos porque **embute nome proprio no rotulo** (`Josh Coburn Total de chutes`); normalizando por sufixo eles colapsam 60%, mas ela so tem 552 bilhetes de 1 selecao contra 7.779 da Bet365, entao ela ESPERA. **A regra que a medicao obrigou a criar:** dezessete rotulos passaram na regua de categoria (maioria >=95%, n>=5) e **so sete ficaram**, porque acertar a categoria nao basta, a DESCRICAO tem de bater junto — aplicando os dezessete, a cobertura ia a 73,5% e a divergencia de descricao SUBIA para 22,8%. Os dez cortados sao duas familias que pedem codigo e nao linha de tabela: prop de SIM/NAO, onde a selecao e `Sim` e quem carrega a aposta e o ROTULO (`Terminar com Pontos` sai `Franco Colapinto - Sim` e a IA escreve `Franco Colapinto - Terminar com Pontos`, 98% de divergencia em 52 casos), e escopo de tempo, onde o periodo muda a aposta e precisa aparecer (`1º Tempo - Escanteios Asiaticos`, 98% em 41). **Entrou o corte do sufixo `- N Opcoes`** como ULTIMA tentativa: `Total - 2 Opcoes` esta no mapa por inteiro e cortar antes deixaria a chave em `total`, derrubando 498 blocos de uma vez. **Tres achados de desenho:** (1) o esporte NAO sai do codigo da casa, `CL=18` deu eBasket 607 e Basquete 223 e quem decide e a liga; (2) a normalizacao de prefixo e obrigatoria e difere por casa; (3) `Tipo: … (N selecoes)` conta PERNAS, nao mercados. **A triagem que muda a leitura dos 20%:** das 1.376 divergencias de descricao, 657 sao nome de time localizado (limitacao declarada), 538 sao notacao de numero e 81 sao a IA escrevendo `Mais de` onde o MASTER manda `Over`. Das 538, **520 (96,7%) sao NOTACAO e nao valor** — o MASTER nao fixa a forma da linha partida e e ali que a IA improvisa em tres formatos. **Buraco de MASTER, nao defeito de tradutor** (`BACKLOG §3.8`, decisao do Feca). **Gates:** 24 passed, mutacao provada nos dois sentidos do corte do sufixo, e replay contra os 9.641 blocos reais da sombra. Registrado no `PLANO_TRADUTOR_DETERMINISTICO §II.8`. A s333 rodou em PARALELO, noutra sessao.)

_Anterior: 2026-09-09 (sessao 333: **handoff `Contas e Parceiros v2` — Fases 7 e 8 aplicadas.** A Fase 7 e distribuicao por LARGURA e a Fase 8 e a zona de Fornecedores. **O vao de ~800px no monitor de 32" nao era margem errada, era COLUNA SOBRANDO:** a folga vivia numa faixa antes das acoes, entao nome/status/caixa ficavam ancorados a esquerda e os botoes na borda direita, com nada no meio. Agora a unica coluna elastica e a PRIMEIRA (o nome, que sempre tem o que mostrar) e a folga vira INFORMACAO: duas faixas nascem em 0px e abrem por degrau — `Fornecedor` e `Ultima captura`. **Dois containers, cada um medindo o que governa:** o `pc` mede a AREA DO APP e decide quantas zonas cabem lado a lado; o `acct` mede a TABELA e decide quantas colunas cabem nela. Um container so nao resolveria: o mesmo monitor da larguras diferentes a tabela conforme o numero de zonas ao lado, e foi por isso que a coluna de fornecedor abriu em 1366 (log embaixo, tabela inteira) e nao em 1440 (log ao lado). **Os cortes do handoff (1500/1900/170/176) NAO foram copiados — foram MEDIDOS, e tres deles nao fechavam:** as acoes medem 208px e a trilha proposta era 176; a linha da CASA precisa de 220px de nome (favicon + `Esportes da Sorte` + pilula de contagem) e a proposta era 170; e com os cortes de pagina em 1500/1900 a tabela caia abaixo do proprio piso em 1440, 1600 e 1920 — sem erro, porque `justify-content:flex-end` transborda para a ESQUERDA e isso some do `scrollWidth` (a armadilha da s331d). Os cortes agora saem da conta do conteudo: 842px de piso de tabela, 1094 / 1334 / 1738 / 2030 de area de app. **Fase 8 — a tela se chama Contas & Parceiros e nao dizia nada sobre FORNECEDOR.** Risco de fornecedor nao e risco de casa: casa que trava saque e burocracia, fornecedor que some e o dinheiro. Entrou a terceira zona (ordenada por caixa, com o proprio usuario como contraponto), o 4o KPI `Em contas de fornecedores`, o segmentado de fornecedor na barra da tabela e a linha de total no rodape, na MESMA grade das linhas. Nenhum dado novo: tudo e agregacao do `[Fornecedor]` que ja vive no nome da conta. **Estado novo `Parada ha N dias`, em CINZA:** conta ativa sem captura ha mais de 30 dias se disfarcava de `Conciliada` — estava limpa porque ninguem a usava. Cinza e nao ambar de proposito: abandono nao e pendencia e nao pode competir com pendencia de verdade. O unico campo novo e o `ultima_captura` do `/caixa/visao`, que e o maior `criado_em` dos bilhetes da conta — e o rotulo diz **captura**, nao "extracao", porque extracao que nao achou bilhete novo nao aparece ali. **Gates:** check-tokens verde, 767 passed / 30 skipped, o gate novo `tests/test_contas_status.py` com **8 mutacoes, 8 detectadas**, e `scripts/demo/medir_contas.mjs` medindo a tela em 1366/1440/1600/1920/2560 (transbordo 0 em todas, zero tag na casa, 29 chips TOTAL, nenhuma abreviacao). **Achado medindo, NAO corrigido:** ha dois `Banca total` na mesma tela e eles divergem — o KPI soma toda conta ligada, a faixa da Concentracao soma so casas com `banca > 0`. Foi para o `BACKLOG §4`.)


> **Histórico completo das sessões 331 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 335)

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

## Sessão 333 — Contas e Parceiros v2, Fases 7 e 8

### Contas & Parceiros: a folga do monitor largo virou informação

As Fases 7 e 8 do handoff v2 estão aplicadas. A tela tem cinco leituras: quatro
números de dinheiro no topo, `Últimas ações` na lateral inteira e, embaixo,
`Concentração de caixa` · `Contas` · `Fornecedores`.

| Área do app | Zonas | Colunas da tabela | Ações |
|---|---|---|---|
| < 1.094px | tudo empilhado, log embaixo | Conta (fornecedor ao lado) · Status · Caixa | no hover |
| 1.094–1.333 | log ao lado, zonas empilhadas | idem, e a de Fornecedor abre se a tabela ≥ 990 | no hover |
| 1.334–1.737 | Concentração ao lado da tabela | + **Fornecedor** como coluna própria | no hover |
| ≥ 1.738 | as três zonas lado a lado | + **Última captura** com a tabela ≥ 1.150 | sempre visíveis |

> **O que esta sessão ensinou, e vale para qualquer tela com degrau:** o corte não
> sai do número do handoff, sai da conta do conteúdo — e a conta muda conforme o
> que está ao lado. Por isso são DOIS containers e não um: o `pc` mede a área do
> app e decide as zonas; o `acct` mede a tabela e decide as colunas. Com um só,
> o mesmo monitor abriria a coluna numa largura e a fecharia noutra sem motivo
> visível. E encostar num corte cedo demais **não dá erro**: a tabela transborda
> para dentro do `overflow:hidden` do painel e some do `scrollWidth`.

### O que ficou aberto desta sessão

Os dois `Banca total` divergentes ([`BACKLOG §4`](BACKLOG.md#4-dívida-técnica-medida)) —
medido, não corrigido, porque o conserto muda o significado de um dos dois e essa
escolha é do Feca.

---

## Sessão 332 — a remedição do custo

### A remedição do custo: as correções acertaram o alvo, e o alvo era o outro

O [`ESTUDO_PRECIFICACAO_2026 §7`](docs/ESTUDO_PRECIFICACAO_2026.md#7-revisão-de-08092026-s332--o-que-aconteceu-depois-de-a-e-c)
tem a medição inteira. O resumo é que **capturamos 47% mais bilhete pagando 3% menos**,
e mesmo assim a tabela de preços ficou mais difícil de fechar.

| | Estudo (25/07 a 24/08) | Agora (25/08 a 08/09) |
|---|---|---|
| Conta real de API | US$ 404/mês | US$ 391/mês |
| Bilhetes novos por IA | 15.150/mês | **22.316/mês** |
| Custo **real** por bilhete | R$ 0,137 | **R$ 0,090** |
| Custo **variável** por bilhete | R$ 0,078 | **R$ 0,087** |

A correção A fechou um vazamento de US$ 173/mês, e ele era **fixo**. O custo variável, que
é o que a escada de preço consome, subiu 12%.

### O que isso muda na decisão

A pré-condição do modelo de preço deixou de ser uma casa e passou a ser duas. Só com a
Bet365 determinística, Pro e Operação fecham em 12% de margem bruta, que não paga infra
nem gateway. Com Bet365 e Betano a escada fecha em 41 a 64%. As duas juntas são 64,3% da
conta e 58% dos bilhetes por IA, e a Fase 0 do tradutor já acumulou 13.965 pares em 21
casas para validar as duas.

> **Sintoma para reconhecer isto noutra frente:** uma otimização que melhora exatamente o
> indicador que ela mira e piora o que decide o preço. A correção A mirou custo fixo e
> acertou. O `_BILHETES_POR_CHUNK` da s301 mirou output e latência e acertou. Nenhum dos
> dois mirou o custo variável por bilhete, e ninguém mediu o outro depois. Toda otimização
> daqui em diante declara qual custo mira e mede o outro na sequência.

### O que ficou aberto

Está tudo no [`BACKLOG.md`](BACKLOG.md): a decisão de escopo do tradutor (`§3.7`), o
rótulo errado do `/uso/tokens` (`§4`, de pé desde a s295), a remedição em 30 dias e a
infra do Railway, que segue não medida.

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
