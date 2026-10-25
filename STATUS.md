# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-10-25 (sessao 428: **20bet no SharpenUp (0.7.64), espelho da Vave, recon no Chrome do Feca (conta do Gabriel, USD).** Prova do motor: a home carrega `platform.20betz0ne1.com/api/v2/...`, o historico responde ao Bearer de `localStorage.customer.token` e a uniao de chaves deu 167, zero nova contra a Vave. Mesmo `vv_inject`, mesmo `formatTicketVV`, mesmo adaptador `vv`; dominio numerado (`20betz0ne1.com`), fora do `CASA_HOSTS` como a Vave. Grafia da BASE `20bet` (57 bilhetes de print do Gabriel, codigo de 8 digitos igual ao do card). Medido no card e novo para a familia: perna `0` Pending e `3` Returned (`_PERNA_VV` e `vv._PERNA`), e o Bet Builder em perna unica `BetBuilder` com as selecoes do cupom em `betBetBuilderLegs` (o inject sobe `legsBB`, TAB colapsado na entrada; o bloco leva `Selecoes do Criar Aposta`; a Ficha RECUSA bet builder e o texto vai a IA). O dicionario `/pt` da 20bet vem em PORTUGUES (o da Vave vinha em ingles). Gates: harness 52 casos verde (`20bet.mjs`: 12 bilhetes reais, 2 abertas, a multipla Lost/Returned/Won, 3 bet builders, partida a frio, TAB na entrada), 6 mutacoes no inject/formatador detectadas (uma errou o alvo e foi refeita); `test_adaptador_vv_20bet` 6 testes, 3 mutacoes detectadas; `test_cru` com `20bet.cru.json`; audits sharpenup/casas/grafias/check_docs sem FAIL; pytest 1991. Nota generica no changelog (`--so-changelog`), grupo NAO avisado. **NAO validado:** ganha, cashout e a captura pela extensao instalada. Commit `8cdc146`. **Depois, Sportsbet.io no SharpenUp (0.7.65), plataforma propria GraphQL, recon na conta do Feca (USDT).** `POST /graphql` (`SettledTicketsQuery`/`myBettingHistory` + `ActiveTicketsQuery`/`myActiveTickets`), Bearer = o cookie `token` (JWT, nao HttpOnly: partida a frio); sem ele HTTP 200 com a lista `null` e sem `errors` (vira erro dito, nunca conta vazia). Cursor `mongodbconnection:N` ate `hasNextPage:false` nas DUAS listas (a tela pede as abertas sem `pageInfo`; `first` 100/500/1000 aceitos; 5+cursor = 16 de 16). Dinheiro em 1e8 (medido so em USDT; outra moeda a Ficha recusa). `wonAmount` = retorno (null na perdida); odd do card = `boostedOdds` (TURBINADO 5,83 com `odds` 5,71). Perna 1 verde, 2 vermelha, 0 pendente, `voidFactor` 1 cinza mesmo com status 2. Bet Builder (INVENTOR) em perna unica com `;`. Codigo = o ObjectId de 24 hex que o botao ID copia. 1a casa com PONTO no nome: grafia da base `Sportsbet.io` (2 contas, 6 bilhetes de print), chave `SPORTSBETIO`; `_casaConectavel` e o `content.js` passam a tirar ponto e espaco, e os simuladores do `audit_sharpenup` leem isso (2 mutacoes: as duas viram FAIL). Adaptador novo `sbi` (aceita perdida/ganha/anulada pelo dinheiro/aberta; recusa Bet Builder, freebet, cashout, sistema e moeda fora de USDT). Gates: harness 53 verde (`sportsbetio.mjs`: 31 reais, paginacao 230 em 3 cursores exatos, liquidada vence aberta, token aprendido da pagina, sem sessao, cookie vencido), 16 mutacoes detectadas; `test_adaptador_sbi` 13 testes, 8 mutacoes detectadas; `test_cru` com `sbi`; pytest 2005; audits sharpenup/casas/grafias/check_docs/tokens sem FAIL. **Inject real ao vivo** nas duas abas logadas (servido por localhost e colado depois do load): Sportsbet.io 31 de 31 a frio fora de Minhas Apostas (uma aposta liquidou no meio e saiu W 25 x 11,8 = 295), 20bet 12 de 12 com dicionario no cru; token fora da mensagem nas duas. Nota generica no changelog, grupo NAO avisado (decisao do Feca: casa nova nao vira aviso). Commit `98790b1`, botao Conectar provado em producao (`[true, true, false]`, as duas em `/casas`). **Virada:** o Feca rodou o `railway variables --set` com `VAVE`, `20BET` e `SPORTSBETIO` nas 3 listas (`FICHA_SOMBRA_CASAS`, `FICHA_CASAS_VIRADAS`, `EXTRACAO_SEM_PENSAMENTO`), deploy `3e5fb052` SUCCESS. Semente NAO aplicada (fica para a rodada diaria das 04h): rodando a mao em producao, ela segurou lock em `bilhetes` enquanto o push de docs fazia deploy, e o startup (ALTER TABLE) travou atras dela; o Sharpen ficou fora do ar alguns minutos ate eu parar o script (sem conexao presa depois). Conserto estrutural proposto ao Feca: `lock_timeout` nos DDL do startup e healthcheck no `railway.toml`. **Tornadobet no SharpenUp (0.7.66), 10a casa Altenar, espelho da BetMartini, SEM conta.** Recon no Chrome do Feca sem login: `altenarWSDK` na propria pagina `/sportsbook`, `integration=tornadobet`, `culture=en-GB`, cluster `altenar2`; o gateway de historico da 403 sem sessao na rota real e numa falsa (a prova 401x404 nao separa). Espelho NUMERADO: o Feca usa `tornadobet82.com` e `tornadobet.com` redirecionava para `tornadobet34.com` no mesmo dia; os tres registrados. Grafia da base `Tornadobet` (25 bilhetes de print do Gabriel, codigo de 10 digitos, que virou o `CODIGO_EXEMPLO` real). Mesmo `vb_inject`, `formatTicketVB`, `roboVBPassive` e adaptador `vb`. Harness `tornadobet.mjs` com a fixture da Estrela Bet (declarado), 4 mutacoes (integration errado, ramo, Conectar: detectadas; manifest: WARN por desenho). Harness 54, pytest 2005, audits sem FAIL. Sem aviso ao grupo. `TORNADOBET` nas 3 listas da Railway (o Feca rodou o `--set`; deploy `35dc7c51` SUCCESS), semente fica para a rodada das 04h. **Stake.com no SharpenUp (0.7.67), a Stake INTERNACIONAL (nao e a `Stake` .bet.br), GraphQL, recon na conta do Feca (USDT).** `POST /_api/v1/graphql`, token = cookie `session` (a frio) ou o header `x-access-token`; introspeccao desligada e a pagina compila as queries em AST, entao o `stc_inject` usa a COPIA LITERAL de `SportSportList` (historico, 7 status, 20 por vez) e `ActiveBets_User` (4 listas de abertas por tipo, 50 por vez). Armadilhas: `limit` > 50 devolve VAZIO sem erro (51/100/500 medidos); a tela `/pt/sports/my-bets` diz "Nenhum resultado" com a conta cheia (a certa e `/pt/my-bets/sports`); no historico o `iid` mora fora da aposta e a props (`SwishBet`) nao o repete, entao o cru e `{iid, bet}`. Codigo = numero do `iid` (o "ID da Aposta" do modal, 9 digitos), `payout` = retorno, `user` (nome da conta) fora do cru. Grafia da base `Stake.com` (Jaao26, 288 de import), chave `STAKECOM`. Adaptador novo `stc` (comum e props; recusa corrida, XMulti, promocao, cashout parcial e cashout != stake). Gates: harness 55 (`stakecom.mjs`: 18 reais, paginacao 0/20/40, liquidada vence aberta, sem sessao, sessao vencida, token aprendido), 16 mutacoes com 15 detectadas e 1 inocua (odd da props por `potentialMultiplier`: iguais nas 15); `test_adaptador_stc` 7 mutacoes detectadas; pytest 2018; audits sem FAIL. Achado no harness: sessao vencida subia "formato desconhecido" em vez do erro da casa (corrigido). Inject real ao vivo colado na aba: 18 de 18, 18 crus com `iid`, sem `user`, token fora. Sem aviso ao grupo; `STAKECOM` nas 3 listas da Railway pedida ao Feca. Viradas SEM backtest Ficha x IA nas duas novas (nao ha cru real no banco; a Vave teve o da s427): decisao do Feca (25/10/2026, "precisa sim estar todas nas fichas"). **Falta:** a 1a captura de cada uma pela extensao instalada, conferida no `virada_log`)_

_Anterior: 2026-10-23 (sessao 427: **Vave na Ficha (adaptador `vv`, SharpenUp 0.7.63) e as 6 casas com adaptador viradas.** Seis casas tinham adaptador e nao estavam viradas: backtest Ficha x IA nos crus reais (BETREBELS 193/212 iguais, SAPPHIREBET 25/28, BETFURY 24/57, BETCOIN 10/25, MELBET 17/18, JACK 14/14); toda divergencia e data (a IA usou a colocacao ou a data em UTC; a Ficha segue a regra do MASTER, evento em SP e perdida pela perna perdida mais cedo) ou odd de L (a exata da casa x a truncada da IA). O Feca rodou o `railway variables --set` (as 6 em `FICHA_SOMBRA_CASAS` e `FICHA_CASAS_VIRADAS`, JACK em `EXTRACAO_SEM_PENSAMENTO`), deploy `ebd2ce2b` SUCCESS, semente aplicada (1717 termos). Vave: o historico nao traz o nome do mercado, so o id; o `vv_inject` passa a mandar no cru as linhas do dicionario publico que o bilhete usa (`dicionario`, o TEMPLATE verbatim) e o servidor resolve (`app/adaptadores/vv.py`). Ganha medida nos crus reais: `win` = `winFull` = retorno. Cru sem `dicionario` (os 35 de antes) recusa e vai a IA. Backtest nos 35 crus com o dicionario baixado a parte: 35 aceitos, 34 iguais a IA, 1 com a odd do card (5,02; a IA gravou 5,019999999778). Generico: chave de categoria com o time do jogo trocado por `{time}` (`descricao_ficha.mercado_com_time`, `dicionario._merc_time`), a mesma familia do `{jogador}` da s415 (`{$competitor1} clean sheet`). Gates: `test_adaptador_vv` 17 testes, 10 mutacoes detectadas; harness da Vave com o dicionario do cru (3 mutacoes detectadas); `test_cru` com a familia `vv`; pytest 1968. Decisao do Feca (23/10/2026): as casas .bet.br que nunca gravaram cru ficam em banho-maria ate a legislacao liberar (`BACKLOG`). Commit `54e355d`. Depois, a regra para toda casa nova: `audit_sharpenup` da FAIL em casa de captura cuja familia nao tem adaptador (`FAMILIAS_SEM_ADAPTADOR` com data: so as .bet.br em banho-maria), 2 mutacoes detectadas (tirar `vv` do `ADAPTADORES`, tirar `b3` da excecao); `/sharpenup-casa` ganhou a Fase 6b (cru que basta, adaptador, testes, medicao, virada com o comando completo ao Feca, semente, `virada_log`), `/sharpenup-validar` o item, `/sharpenup-recon` o plano da Ficha, `GUIA_CASA_SHARPENUP` a Fase 6b. O `CLAUDE.md` nao ganhou linha: esta no teto (65 KB). **Falta:** push, deploy, `VAVE` nas 3 listas da Railway, e a 1a captura da Vave com a 0.7.63)_

_Anterior: 2026-10-22 (sessao 426: **Thunderpick no SharpenUp (0.7.61), plataforma propria, conta em EUR, recon na conta do Feca.** Front React Router v7 com API `/api/*` no mesmo dominio (Cloudflare; feeds Oddin.gg e DATA.BET, nao e Altenar/BetBy/Kambi/BetConstruct/softlabs). `GET /api/wagers/v2/resolved?take=&skip=&sortColumn=finishTime` (liquidadas) + `/pending` (abertas, sem paginacao), header `thunderpick-token` (sem ele 403 `errorCode 2013`; o mesmo valor em `localStorage["thp.sessionData"].sessionId`, entao o replay parte a frio). Fim = `totalWagersCount` da 1a PAGINA (`skip` alem do fim devolve total 0); teto do `take` nao medido (100/500/1000 aceitos), o inject pede 100 e avanca pelo que voltou. Dinheiro em CENTAVOS DE EURO e a conta e sempre em euro: a tela em USD usa o cambio do DIA (medido 24,98 -> 24,97 USD no mesmo bilhete de 2025; a propria Wallet Settings diz que tudo e liquidado em euro). Decisao do Feca (22/10): conta cadastrada em EUR, bloco com `Moeda: EUR` + carimbo, uma conversao so pela PTAX no `/salvar`. `wagerId` em DUAS series (multipla ~2,2M, simples 4,9M-10,3M): o codigo leva prefixo `C`/`S`. Esporte so por `gameId` (6 CS2, 10 futebol, 11 basquete, 14 hoquei, 15 tenis, medido pela liga; id novo sobe cru). Retorno arredondado sem regra fixa (18720,66 -> 18720; 3952,8 -> 3953): `W` com tolerancia de 1 centavo e odd do card. Prefixo `thp` (`tp_` e da 1win). Grafia `Thunderpick` (a base nao tinha a casa, `audit_grafias` 136 casas). Registro nos 12 pontos, `CASA_THUNDERPICK.md`, cru = o wager inteiro (familia `thp`, sem adaptador). Gates: harness 51 casos verde (`thunderpick.mjs`: 29 liquidadas + 13 abertas reais, paginacao 230/200 exatas e com teto de 50 por pagina, liquidada vence aberta, partida a frio, sem sessao, dinheiro por clone); 26 mutacoes, 24 detectadas, 2 inocuas (total lido de toda pagina, porque o inject nunca pede alem do fim; `r.ok`, porque o 403 traz `errorCode`); audits sharpenup/casas/grafias/changelog/check_docs sem FAIL; pytest 1950 passed. **Inject real provado ao vivo** colado na aba logada: partida a frio, 48 de 48 (42 liquidadas + 6 abertas, igual aos totais da casa), 48 crus, token fora da mensagem. Erro meu corrigido no caminho: eu tinha dito 12 ganhas/17 perdidas na fixture; sao 8/21. Nota generica no changelog (`--so-changelog`), grupo NAO avisado. **NAO validado:** devolvida, cancelada, cashout, freebet, boost (sobem a conferir) e a captura pela extensao instalada. Pendencias em `BACKLOG §4.0o` (inclui a mensagem do cadastro em EUR, via `/nova-ui`, e a pergunta do sigilo). **Proximo passo:** o Feca atualiza para a 0.7.61, cadastra a conta em EUR, Ctrl+Shift+R na aba da Thunderpick e na do painel, captura; prova do botao Conectar em producao **23/10, a Thunderpick estava fora da Ficha (erro meu):** o Feca viu as exportacoes demorando; os 180 crus `thp` chegavam e nenhum virava Ficha, tudo ia a IA. Adaptador `app/adaptadores/thp.py` (codigo C/S, centavos, EUR, ganha com 1 centavo, recusa cancel/cashout/freebet, esporte por `gameId` com 43 = Badminton, mercado de jogador com o nome na ordem da IA para a chave `{jogador}` generalizar), `tests/test_adaptador_thp.py` 16 testes e 11 mutacoes detectadas. Nos crus reais: 147 de 152 aceitas, as 43 com linha no banco iguais a IA (resultado, data, odd), deixa-um-de-fora 26 de 43 sem IA. SharpenUp 0.7.62. **Falta:** `THUNDERPICK` em `FICHA_CASAS_VIRADAS` (CLI da Railway deslogada), semente na hora e a varredura das casas em uso (Vave tambem sem adaptador). `DIARIO.md` da Ficha atualizado)_


> **Histórico completo das sessões 332 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 342)

> **Sessão longa, de custo e do tradutor.** O registro durável está nos planos; isto aqui
> é o mapa para retomar.

### O que entrou no ar hoje

| | Onde está |
|---|---|
| Estudo de custo **remedido** | [`ESTUDO_PRECIFICACAO_2026 §7`](docs/ESTUDO_PRECIFICACAO_2026.md) |
| **Barreira de recaptura**, Fases 0 e 1 | [`PLANO_BARREIRA_RECAPTURA.md`](docs/PLANO_BARREIRA_RECAPTURA.md) (novo) |
| O gate do tradutor **trocado** | [`PLANO_TRADUTOR §II.9`](docs/PLANO_TRADUTOR_DETERMINISTICO.md) |
| Decisões **A e B** do Feca, aplicadas | `MASTER_DESCRICAO §10.1` e **§10.1.1** · `MASTER_OUTPUT §19` |

### O achado que reorganiza a frente

**Em 76,7% das releituras a IA descreveu de forma diferente algo que ela mesma já tinha
descrito.** No maior mercado da base a mesma seleção saiu de **doze** jeitos. O teto de
acerto de qualquer tradutor determinístico contra esse juiz é **~23%**.

E a causa não é a casa (a entrada é byte a byte idêntica) nem só o buraco do MASTER. A
instabilidade segue **quantas decisões o modelo precisa tomar para montar a frase**:

| A descrição exige | Instável |
|---|---|
| Copiar um nome | 18% |
| Montar com linha meia (**tem** template) | 42% |
| Montar com linha partida (sem template) | **100%** |

> **Descrição montada por modelo estocástico não converge para um formato só, por melhor
> que fique o MASTER.** Só compor em código elimina. O tradutor ganhou com isso uma
> segunda justificativa que não depende do preço da API: **ele é o que dá formato único
> ao dado.**

### Onde o tradutor está

| | |
|---|---|
| Cobertura na Bet365 | **68,0%** (7.606 de 11.186) |
| **Conformidade com o MASTER** | **100,0%** contra 67,1% da IA |
| Maior buraco de cobertura | `mercado desconhecido`, 1.644 bilhetes |

### O PRÓXIMO PASSO, concreto

**Ampliar o mapa com a régua nova.** Ela mudou o jogo: rótulo que eu rejeitei na s334 por
"divergir 98% da IA" pode estar certo. Já reavaliei os 10 podados e **dois voltaram**
(`total de pontos`, `corrida - handicap`); os outros quatro têm agora motivo nomeado no
próprio `app/tradutor.py`, logo abaixo do mapa. Falta rodar a mesma reavaliação nos
**1.644 bilhetes de `mercado desconhecido`**, que é onde está o volume.

O script que produz a lista de trabalho está descrito no `PLANO_TRADUTOR §II.8`; ele
casa cada rótulo desconhecido com a maioria da IA e a frequência.

### O que depende do Feca

`BACKLOG §3.8`, decisões **C** (prop de SIM/NÃO, ~100 leituras) e **D** (escopo de tempo,
~60). São pequenas perto das ~5.700 que A e B resolveram, mas destravam quatro rótulos
que hoje estão de fora com motivo escrito.

### Três hipóteses de custo que MORRERAM medidas

Estão no `BACKLOG §3.10`, e valem por poupar a próxima sessão de tentar de novo: aparato
editorial no prompt (**US$ 0,76/mês**), fatiar esportes por casa (**US$ 7,30**), e cortar
o preâmbulo do output (**o modelo não aceita prefill de assistente**; sobra US$ 9/mês pelo
`stop_sequences`). **Os masters estão densos, não inchados.**

### Duas coisas que não são minhas e ficaram vermelhas

- **`CLAUDE.md` está em 65,4 KB, acima do teto de 65.** Veio commitado em `db5b77c` /
  `cea574b`. Pela regra do próprio arquivo, o conserto é mover **caso** para o
  `docs/CASOS.md`, nunca subir o teto.
- **`test_changelog` com 3 falhas:** o `extensor/manifest.json` está numa versão sem nota
  de changelog. Resolve rodando o `scripts/avisar_testers.py`.

---

## Sessão 344 — as 298 de 2025 saíram, e o que impede elas de voltarem

### O que estava errado

A 1ª captura da Betbra (s343) gravou **411 bilhetes de uma vez**, e **298 eram de 2025**
(01/06 a 31/10). A Betbra é a **única** casa deste dono com bilhete daquele ano: toda a
base dele começa em 2026. A exportação da casa trouxe o histórico inteiro junto.

### A metade que faltava: apagar não bastava

`extensor/bda_inject.js` varre **3 anos** por desenho (`DIAS_HISTORICO = 1095`), e o
`lookbackDias` do painel só é respeitado quando pede **mais**. Isso é deliberado desde a
s299, quando a janela curta fez o robô trazer 21 de 418 bilhetes da Bolsa.

Consequência: a próxima captura reencontra os mesmos 298 códigos e regrava tudo, sem erro
nenhum. **Exclusão sem corte dura até a varredura seguinte**, que é a mesma família do
"volta pela CASA, nunca pelo banco". E não havia nada no sistema segurando isso:
`lixeira_bilhetes` é snapshot de reparo, ninguém a consulta no `/salvar`.

### Onde o corte ficou, e por quê

No **`/extrair`**, não na extensão. Dois motivos:

| | |
|---|---|
| O inject é **compartilhado** com a Bolsa de Aposta e vale para todo dono | encurtar o horizonte lá quebraria a casa que ele existe para proteger |
| Aqui a régua é por **(dono, casa)** e roda **antes da IA** | o bloco cortado não paga leitura, não vira TSV e não chega ao `/salvar` |

Régua em `main._CORTE_HISTORICO`, um mapa de par exato: **Feca × Betbra, nada anterior a
01/01/2026**. Casa nenhuma entra ali sem decisão escrita.

Três decisões de leitura, todas com gate próprio:

- A data que manda é a do **EVENTO**, a mesma que decide a coluna Data. Ler a colocação
  cortaria aposta feita em dezembro para jogo de janeiro.
- Bloco **sem data legível FICA** (fail-open). Esconder bilhete é o modo de falha caro,
  porque ninguém reclama do que não apareceu; um a mais para a IA é o que a barreira de
  recaptura já devolve.
- A contagem tem **balde próprio** na tela (`fora_corte`), nunca somada em `xls_skipped`:
  "já salva" afirma que existe uma linha no banco, e esta nunca existiu.

### O que saiu da base

Aplicado **depois** de conferir o deploy no ar (o `/static/index.html` de produção já
servia o campo novo), por `scripts/excluir_historico_fora_do_corte.py`, que lê a régua do
próprio `_CORTE_HISTORICO` em vez de repetir a data.

| | |
|---|---|
| Movidas para `lixeira_bilhetes` | **298**, motivo nomeado, snapshot JSONB |
| Saiu da base | R$ 10.125,25 de turnover · **+R$ 5.262,25 de P/L** |
| Restam na Betbra do Feca | **113**, todas de 2026 |
| Bilhete de 2025 em qualquer casa dele | **zero** |
| Contas dos outros 4 donos na Betbra | intactas |

### Gates

`tests/test_corte_historico.py`: 16 casos sobre blocos **reais** da `sombra_rotulos`,
**6 de 7 mutações detectadas**. A 7ª é inócua (o log some) e está registrada como tal.

A mutação nº 5 é a que interessa: **a chamada removida da rota**. Sem ela o corte fica
verde e inútil, que é como uma regra sem gate morre neste repo.

863 passed / 36 skipped · `check-tokens` verde · `index.html` renderizado headless sem
erro de script.

### Pendente

**Validar ao vivo:** recapturar a Betbra e conferir que as 298 não voltam. É o único teste
que fecha isto, porque o gate lê o fonte da rota, não a executa ponta a ponta.

> **Duas sessões no mesmo `index.html`.** O 1º commit levou junto o selo de captura que a
> outra sessão estava escrevendo no arquivo. Corrigido **antes do push**: o blob do índice
> foi trocado por uma versão com só os meus hunks, e o trabalho dela seguiu intacto no
> working copy. O `git show --stat` é o que acusa isso, e ele só serve se for lido.

---

## Sessão 343 — Betbra: a casa espelho e o cupom que virava múltipla falsa

### A casa

A **Betbra** entrou na captura como **casa espelho da Bolsa de Aposta** — é a mesma
plataforma com outra marca. Medido no navegador, lendo o `src` real dos dois iframes:
rotas de casca idênticas (`/b/exchange` · `/fbook`), Exchange LayBack em
`mexchange.betbra.bet.br` (cookie, 0 parâmetros) e Sportsbook msjxk em
`prod20454-176166310.msjxk.com` (`operatorToken` na URL). **Zero inject novo, zero
formatador novo:** os dois já derivavam o endereço de `location`.

**O único bloqueio real era o `match` do manifest**, preso em `*.bolsadeaposta.bet.br` —
o `bda_inject` nunca subiria em `mexchange.betbra.bet.br`. O Sportsbook já vinha coberto
pelo curinga `*://*.msjxk.com/*`.

Volume: **403 ofertas no Exchange** (mai/2025 → set/2026, varridas em 29 chamadas com zero
erro) e 7 liquidadas + 3 abertas no Sportsbook.

### O achado: `Selections` não é a lista do que foi apostado

No Criador de Apostas (bet builder) o Sportsbook manda, dentro do MESMO array: as **pernas
soltas**, cada uma com a odd de mercado dela — que não foi apostada —, e uma entrada
**agregada** do cupom (`MarketTypeId: "QA0"`), com a odd do conjunto e os textos das pernas
concatenados por ` | `. Quem diz o que entrou é **`MappedSelections`**, uma lista de índices.

O código lia todas. Uma aposta de **4,61** virava uma múltipla de **26,72** (1,13 × 2,30 ×
2,23 × 4,61) — **sem erro nenhum, e com o P/L continuando certo**, porque a odd do bilhete
vem de outro campo. Errariam só turnover, ROI e a assinatura de stake do matcher. Mesma
família de "a stake que era do vizinho, com o P/L intacto" (s311).

Medido em **10 de 10** bilhetes: a odd bate com o produto das *mapped* em 10/10 e com o
produto de todas em **0/10**.

> **O defeito atravessou o recon da Bolsa sem aparecer.** Lá `MappedSelections` é sempre
> `[0]` com uma seleção só: as duas leituras coincidem. O caso da Bolsa fica **verde com ou
> sem a correção** — falso verde do tipo 2 do `CLAUDE.md` ("o dado sintético não exerce a
> regra"), e está escrito no cabeçalho dos dois arquivos.

**Decisões de formato**, todas contra a tela: a ordem das pernas vem do **texto agregado**
(o array traz outra ordem — o `SelectionId` da agregada é `0VS0|2|1`); a perna de um cupom
**não tem odd própria** no bloco (publicá-la seria oferecer à IA um número que parece conta
feita e não é); e o tipo virou `Criador de Apostas (bet builder — N seleções do MESMO jogo,
odd única do cupom)`, nunca "Múltipla", que mentiria em três frentes.

### O boost, que a Bolsa tinha como "não confirmado"

`ClientOdds` é a odd **com** boost e `DbTrueOdds` da agregada é a **sem**. A tela risca a
segunda e estampa a primeira (`2.89 → 3.36`). A odd que vale é a `ClientOdds` do bilhete —
200 × 3,36 = 672 = "Retorno Total" da tela. A regra global de W (`retorno ÷ stake`) absorve
o boost sozinha; o percentual **não** se deduz do `Campaigns[].Type` (1,32 e 1,16 medidos em
tipos diferentes).

### Gates

| | |
|---|---|
| Harness | **28 casos, 447 bilhetes** — verde |
| Mutação | **5 de 5 detectadas** pelo caso Betbra · **0 de 5** pelo caso Bolsa |
| `audit_sharpenup` / `audit_casas` / `audit_changelog` | sem FAIL |
| `pytest` | 826 passed / 36 skipped |
| Manifest | 0.7.10 → **0.7.11**, aviso publicado no grupo (`message_id 3380`) |

As 5 mutações confirmam por medição o que o cabeçalho do caso dizia por dedução: **a fixture
da Bolsa não protege esta regra.** Sem o caso da Betbra, a correção teria entrado parecendo
coberta.

### Duas coisas medidas antes de registrar

**A grafia.** `_CASA_DISPLAY` é retroativo, e o código já tinha duas grafias divergentes
(`import_arrudex_xlsx.py` grava `Betbra`, `import_dashboard_xlsx.py` grava `BetBra`). No
banco só existe **`Betbra`**, em todas as cinco tabelas onde `casa` é texto: 5 contas, 158
bilhetes, 1 em `casas_meta`, 23 em `correcoes`, 1 em `uso_tokens`. A decisão do Feca
("Betbra para todos") confirmou a base.

**As séries de código são por CASA, não por plataforma.** Exchange da Betbra: 7–8 dígitos.
Exchange da Bolsa: 9. Mesma plataforma, contadores independentes — **comprimento de código
não diz de que casa o bilhete é**.

### Pendente

**Validação ao vivo**, que não fecha sem o operador: recarregar a extensão, **Ctrl+Shift+R
na aba da Betbra** (recarregar a extensão não re-injeta em aba já aberta) e **F5 no
dashboard** (a casa nova não aparece no seletor numa aba que já estava aberta).

**Sem cobertura automatizada no harness, e portanto ainda dependentes de teste ao vivo:**
`SUPERBET` e `BETESPORTE` — nenhuma das duas tocada por este diff.

**Não provado nesta casa** (medido, não suposto): `lay` (403 de 403 são `back`),
cashout/Retirada, freebet, `push_win`/`push_lose`, casamento parcial no Exchange, e
`MappedSelections` com 2+ índices (múltipla de eventos diferentes).

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
