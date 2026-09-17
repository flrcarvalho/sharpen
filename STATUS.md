# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-17 (sessao 373: **a base de setembro do Ewanderson1 subiu de novo, e desta vez a janela estava LIMPA — medido, nao suposto.** 1.104 apostas de 01 a 14/09, da planilha original dele. **O export novo traz 1.104 linhas para o MESMO periodo em que o de 13/09 trazia 784:** o anterior estava incompleto, e a fonte e a mesma. **A MEDICAO QUE AUTORIZOU A CARGA:** a base dele tinha **179 bilhetes, TODOS `origem='extracao'`, de 15/09 a 20/09**, e o CSV para em 14/09 — **sobreposicao zero**. O risco que derrubou a carga da s357 (import sem ID de bilhete + recaptura trazendo a mesma aposta COM codigo, que nao dedupa e duplica) simplesmente nao existe nesta janela; ele volta no dia em que ele capturar casa de historico longo (a Betano varre 3 anos por desenho), e a regua para isso e o `main._CORTE_HISTORICO`, nunca apagar do banco. **TRES COISAS MUDARAM DESDE SETEMBRO E O SCRIPT NAO SABIA, todas medidas contra o banco antes de escrever uma linha. (1) CONTA:** o script criava `Padrao` por casa, e ele hoje tem **conta com nome real por casa** (`Ykaro` na Betano, `Woshington` na Bet365, `Joao` na SportingBet), cobrindo 1.030 das 1.104 linhas. Decisao do Feca: conta **`Planilha`**, uma por casa, ao lado das reais. O CSV e tracker de TIPSTER e nao diz de quem era a conta em setembro — casar o historico com a conta capturada seria palpite gravado como fato; e como `parceiro` entra no hash da assinatura, a separacao tambem e dedup. **(2) TIPSTER:** o tracker exporta `Padovan` e na base dele o mesmo tipster e **`Padovan All Sports`**, no cadastro E nos 65 bilhetes ja capturados — os outros quatro nomes batem caractere a caractere. Sem o de-para, a carteira do Padovan nasceria partida em dois tipsters que a tela le como pessoas diferentes, e o filtro de tipster recorta por NOME. **(3) CASA:** `Rei do Pitaco` **RESSUSCITOU** — 4 bilhetes com codigo da casa, sob conta criada a mao, contra os 520 de `Pitaco` que a s270 unificou. Refundida ANTES do import (`unificar_casas.py --somente`), 4 assinaturas recalculadas e mais 11 linhas em `parceiros`/`casas_meta`/`correcoes`/`uso_tokens`; trocar a casa sem recalcular deixaria o hash velho e a proxima captura duplicaria o historico. `King Panda` entrou no mapa como **`KingPanda`** (447 bilhetes no banco), que title-casear mutilaria. **DOIS DEFEITOS DO PROPRIO SCRIPT, que a carga anterior nao podia ter:** ele ancorava o `criado_em` em `NOW()` — certo com a base vazia, e hoje jogaria as 1.104 linhas de 01 a 14/09 para o **TOPO do feed**, acima das capturadas de 15 a 20/09, com a data certa na grade e o feed de cabeca para baixo, sem erro nenhum; e a conferencia final comparava o **total do dono** com as linhas do CSV, o que acusaria colisao de assinatura que nao houve. **O DINHEIRO AUDITOU O ROTULO e pegou 5 linhas** (2 `lost` cujo RESULT bate com a formula de vitoria, 3 `void` com perda total), com **0 linhas divergentes** no confronto das cinco formulas do `calcular_pl` contra o P/L que a planilha ja trazia pronto. 4 odds `0.00` entram **VAZIAS**, nunca zero. **CONFERIDO NO BANCO depois de gravar:** 1.104 import (01→14/09) + 179 captura (15→20/09), `criado_em` do import terminando 1s antes do primeiro capturado, W 346 · L 756 · V 2, **0 assinaturas duplicadas**, 0 odd zero, 5 tipsters e nenhum `Padovan` solto. **PENDENTE no [`BACKLOG.md`](BACKLOG.md) §1.16:** nada impede recriar a grafia velha de uma casa ja unificada — o seletor do app so conhece `Pitaco`, mas o "+Nova conta" aceita nome verbatim, e foi por ai que a s270 voltou a ter residuo.)

_Anterior: 2026-09-17 (sessao 372: **a Betboo entrou na captura como ESPELHO da SportingBet, e o inject nao mudou uma linha.** 2a casa do motor bwin/Entain. **O espelho foi PROVADO antes de escrever codigo, e a prova precisou de TRES testes, nao um:** `POST /pt-br/sports/api/mybets/betslips` **com** os cabecalhos do motor e deslogado devolve **401** (rota existe, falta sessao); o MESMO path **sem** eles devolve **200 com o HTML da SPA** (109 KB, medido) como na gemea; e o controle — uma rota inexistente sob o mesmo prefixo — devolve o mesmo HTML 200. **Sem o terceiro teste, "veio 401" nao distinguiria rota de host.** Corpo, topo da resposta (`{summary, betslips, typeFilter, errorLoadingBets}`), `index` como PAGINA e fim por **lista vazia**: identicos. **A FASE 3 FOI NO-OP e isso esta medido, nao deduzido:** o `spb_inject.js` casa por PATH e monta a URL de `location.origin`, e o caso novo `harness/casos/betboo.mjs` roda o contrato inteiro contra a fixture DELA — duas abas partindo de qualquer uma, `index` avancando, arranque a frio entregando os 8 bilhetes, cabecalho do motor em toda requisicao, **e uma assercao que pega se alguem cravar o host da gemea**. **TEXTO descartado com medida mais dura que a da SportingBet:** dos 5 ids liquidados, **ZERO aparecem no `innerText`** (o card colapsado nao estampa codigo), zero linha em branco entre bilhetes, e as selecoes vem COLADAS (`"Indonesia -5.5Mais de 0.5Mais de 0.5"`). **TRES ACHADOS que a gemea nao tinha amostra para pegar. (1) `promoTokens[AccaBoost]` — boost de MULTIPLA**, no nivel do bilhete, em 3 dos 8. E o card **nao trata os dois numeros como equivalentes:** com o boost ele **troca o rotulo** de `Possiveis ganhos` para **`Ganhos melhorados`** e **RISCA** o valor sem boost — medido no `20RTRWRSKY`: `R$ 2.595,92` riscado ao lado de `R$ 2.715,67`, e a conta fecha exata (`maxPayout + WinningsBoost = BoostedWinnings`). **O potencial que vale e o COM boost**, e o `maxPayout` e o riscado: o bloco vinha dizendo um numero que a tela risca, R$ 119,75 a menos. Mesmo padrao da odd pre-boost, mas no DINHEIRO. **(2) `sport.id` 7 e 56** (Basquete, Tenis de mesa) fora do `_ESPORTE_SPB`, que so tinha `{4, 23}` — **4 dos 8 bilhetes** caiam em "id nao mapeado". As duas grafias foram **MEDIDAS no banco**, nao escolhidas pela marca: `Basquete` tem 17.979 bilhetes / 17 donos e `Tenis de Mesa` tem 43 / 5 donos / 3 casas, as duas sem gemea. **(3) DOIS catalogos de evento no mesmo bilhete** — perna com `compoundId: "1:"` vem **sem `optionBetDetails`** (logo sem `isBetBuilder`/`priceBoostData`), as vezes sem `outcome`, e com `market.name` em INGLES no meio de um bilhete em portugues. **A ODD DO W: a Cota do card nao explica o retorno.** Card `Cota 7.58`, `R$ 201,00`, `Ganhos R$ 1.524,59` — mas `201 x 7,58 = 1.523,58`, **um real a menos** do que a casa pagou. A Cota e arredondada a 2 casas e o retorno e exato, entao vale a regua global (odd = retorno / stake = **7,58502488**). O `_oddSPB` ja fazia certo; o que faltava era o gate provar. **GRAFIA MEDIDA ANTES DE REGISTRAR** (licao da s289): `Betboo` e unica no banco — 154 bilhetes, 5 contas, 4 donos — sem gemea para unificar antes, ao contrario da SportingBet. **⚠ E NAO E A BETBOOM:** uma letra de diferenca, outro motor (BetBy, 523 bilhetes), e `betboo` e **substring** de `betboom` — o que separa as duas e a amarracao casa<->site comparar host EXATO ou subdominio, nunca substring. Favicon corrigido de `betboo.com` para a regulada `betboo.bet.br` nos tres mapas, **verificado baixando os dois icones: sha256 IDENTICO** (791 bytes), entao o visual nao muda. **GATE: 17 confericoes, 9 mutacoes, 9 detectadas — e a 1a rodada teve DUAS escapadas, com causas opostas.** Uma era mutacao RUIM: o trecho da odd do W existe DUAS vezes no `content.js` (o `_oddSPB` nasceu copia do `_oddVB`) e o replace pegou a 1a, mutando a **VaideBet** — o caso da Betboo passou verde com razao. **Mutacao que escapa por mirar o alvo errado nao e buraco de teste.** A outra era buraco REAL e meu: `marca.includes("5%")` passava com `"+0,05%"`, entao estragar o fator de conversao do `AccaBoostRatio` escapava — corrigido para regex ancorada no `+`. **Uma das 10 falhas da Fase 2 tambem era minha:** errei a divisao ao escrever o esperado da odd (7,58507463 em vez de 7,58502488), e o codigo estava certo. Corrigido contra o card, nunca contra o codigo. **12 pontos de registro fechados**, `audit_sharpenup` sem FAIL nas 34 casas, `casas/CASA_BETBOO.md` nova (camada fina, aponta para a gemea), harness **29 casos / 471 bilhetes verdes** com a SportingBet inclusa. **O LOG E O TOAST PARARAM DE MENTIR O NOME DA CASA:** quem compartilha inject e formatador compartilhava a mensagem, e o operador na Betboo lia *"a SportingBet devolveu estado que o SharpenUp ainda nao traduz"* — entrou `ctx.nomeCasa`, o mesmo cuidado que o `diag` ja tinha. **E o CRLF me pegou:** `pathlib.write_text` no Windows converteu o `content.js` INTEIRO de LF para CRLF em silencio (o `git diff --stat` mostrava so as 102 linhas reais) — revertido em modo binario, e os scripts seguintes passaram a preservar a terminacao de cada arquivo. **O QUE NAO ESTA COBERTO, declarado no cabecalho do caso e no §14.1 da casa:** a conta tem **8 bilhetes, TODOS `Combo`** — nenhuma simples, nenhum `Canceled`, freebet, cashout, bet builder, nem **W com AccaBoost** (a unica incognita do §6: nao se sabe se o `payout` de um W turbinado ja vem somado, e o controle negativo (b) exercita as duas hipoteses). **PENDENTE: (a) validacao AO VIVO** — recarregar a extensao e Ctrl+Shift+R na aba da casa; nada disto rodou no navegador com a extensao carregada; **(b) `Tenis de Mesa` nao tem secao no `MASTER_ESPORTES_2026`**, apesar de ser a grafia do banco, do `CASA_1XBET`, do `content.js` e do mapa de emojis — propagacao e tarefa separada; **(c) o aviso aos testers da 0.7.14 esta em ENSAIO**, aguardando o "pode mandar" do Feca, e o `test_changelog` fica vermelho de proposito enquanto a nota nao existir. **[FECHADO no mesmo dia: a 0.7.14 foi ao ar, o aviso saiu no grupo (`message_id 4414`) DEPOIS do deploy confirmar `/extensao/versao`, e a nota entrou em `62c1fd4`.]** **E o Feca pediu processo para o que eu 'sempre esqueco': LIBERAR O BOTAO pra galera conectar.** A causa era estrutural, nao desatencao: a **skill** `/sharpenup-casa` (que e o que eu executo) mandava so *"recarregar a extensao e Ctrl+Shift+R na aba da casa"* e **nunca mencionava o PAINEL** — e e o painel que serve o `CASAS_CONECTAVEIS`, ou seja, o botao. O passo existia desde a s298, mas no `GUIA_CASA_SHARPENUP.md`, que e o guia longo e nao o checklist. **Sao dois Ctrl+Shift+R por motivos diferentes:** o da casa porque recarregar a extensao nao re-injeta em aba aberta; o do painel porque `CASAS_CONECTAVEIS` e `carregarCasas()` rodam UMA vez, no load. **E nenhum dos dois mandava PROVAR em producao.** Provado agora, e o botao ja estava liberado: `_casaConectavel('Betboo')` = `true` dentro do iframe `fr-plan` do app logado, com controle negativo dando `false`, e `GET /casas` traz a Betboo nas **31 de captura** entre 50 casas. **Virou processo em QUATRO lugares:** §7.1 nova na skill `sharpenup-casa` (com o snippet da prova e a tabela dos dois reloads), dois itens no checklist do `sharpenup-validar`, o aviso na Fase 7 do guia, e duas regras no `RUNBOOK_AVISO_TESTERS` — a do painel na mensagem e a de **so avisar DEPOIS do deploy**, porque o zip de `/extensao/download` e gerado do `extensor/` que esta no ar. **PENDENTE para o Feca decidir:** a mensagem das 0.7.14 ja publicada **nao** tem a linha do painel, e corrigi-la exige editar mensagem de grupo E o `changelog.json` juntos, para nao dessincronizar a home.)

_Anterior: 2026-09-17 (sessao 371: **o bot avisou "Nao consegui ler o print" num perfil que NAO LE PRINT.** Print do Feca do apoio do PassaTips: bilhete da Betano (Flamengo HT de 0, @2,50, 3,00u) e a resposta `⚠️ Nao consegui ler o print: fetch failed`, as 14:38. **A MENSAGEM CULPAVA A FOTO E A FOTO NUNCA FOI LIDA:** o log do Railway diz `[visao:passatips] fetch failed` as 14:38:33 e as 14:41:40, e o `passatips` e o unico dos 7 perfis SEM VISAO — o `lerPrint` dele e funcao pura da legenda, e o cabecalho do arquivo ja dizia *"nenhuma chamada de API, nenhum custo, nenhum erro de leitura de imagem"*. **O unico `fetch` daquele caminho era o DOWNLOAD da foto** no `api.telegram.org`, feito para todo mundo antes da leitura e dentro do MESMO `try`. **`fetch failed` e a mensagem crua do undici para QUALQUER falha de rede** (DNS, TLS, socket reset); o motivo real vive em `e.cause`, que o codigo descartava, entao nem o log sabia dizer o que tinha caido. **Intermitente, e por isso parecia coisa do print:** o mesmo canal planilhou o #219 as 13:34 e o #221 as 14:44. **TRES CAUSAS, TRES CORRECOES** (repo `sharpen-bot`, `src/foto.js` novo): o download virou CONDICIONAL (`usaVisao: false` no perfil; a foto continua indo ao canal, que recebe o `file_id` e nao passa por download nenhum); entrou RETRY de 3 tentativas com backoff e timeout de 20s, para os outros SEIS perfis, que leem a imagem de verdade e chamam a visao na 1a linha do `lerPrint`; e o erro passa a carregar a causa (`motivoDeRede` desce a cadeia de `cause`), com o aviso no apoio separando *"nao consegui BAIXAR a foto, e rede"* de *"nao consegui LER o print"*. **Gate: 3 casos em `test/testes.js`, 3 mutacoes, 3 detectadas** (sem retry, sem a descida do `cause`, sem a flag). **No ar em `6493762`, RUNNING as 14:51**, e o caminho COM imagem ja passou em producao depois disso (`[sharpen:sohprops] bilhete #519`, 14:59). **A licao e de familia:** aviso de erro que descreve **o que o codigo estava fazendo** em vez do que falhou manda o humano consertar a coisa certa no lugar errado, e aqui mandou o tipster reenviar uma foto que estava perfeita. **PENDENTE, no [`BACKLOG.md`](BACKLOG.md) §1.15:** os dois bilhetes das 14:38 e 14:41 nao existem em canal nem em planilha e so voltam por reenvio; o `#220` consumiu numero e nao tem desfecho no log; e o caminho SEM download ainda nao foi exercido em producao.)




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
