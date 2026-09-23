# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-23 (sessao 384: **auditoria do que este repo AFIRMA, e a faxina que ela cobrou. Rodou em paralelo com as s381-383 do outro terminal.** O Feca pediu o mapa dos arquivos de instrucao e a auditoria desceu para o conteudo deles. **O ACHADO PRINCIPAL: a reprovacao do Haiku que a s380 RETIROU continuava viva no `app/config.py`.** O commit da retirada (`18e456d`) mexeu em BACKLOG, STATUS, CASOS e HISTORICO e **nao tocou o config.py**, onde o comentario ainda dizia *'perdeu 8,7% dos bilhetes e inventou 19 codigos em 253 blocos'*, com a frase *'para ninguem tentar de novo sem dado novo'* enquanto o dado novo ja existia. **Decisao do Feca, e ela separa duas coisas que estavam coladas: o VETO ao Haiku PERMANECE** (e dele, de jun/2026, testado no pipeline de print+texto daquela data, anterior e independente da bancada), **o que sai sao os NUMEROS**. Para reabrir, rodar `tools/eval_zeroshot/` CEGO, sem informar o veto ao avaliador. **DAI NASCEU A SECAO `Regra de morte` do CLAUDE.md**, logo apos os Invariantes: afirmacao empirica carrega data, amostra e harness, e sem harness reexecutavel e placar, nao regra; decisao do dono nao precisa de evidencia mas carrega data e cenario, e nao cai quando o cenario muda; reavaliacao de veredito roda CEGA; **regua desmentida uma vez tira todo numero que emitiu de onde estiver, inclusive de comentario de codigo**; arquivo no teto move caso/sessao/procedimento e nunca corta regra para caber. **A CONTRADICAO C2, MEDIDA E DESARMADA COMO ALARME FALSO:** o CLAUDE.md chamava de *'a regua do projeto'* duas reguas diferentes (`_num_bloco` diz que um separador so e SEMPRE decimal; o `parseNum` trata `^\d{1,3}(\.\d{3})+$` como milhar). Rodei as duas, recortadas dos arquivos reais, contra 10 entradas: divergem em 4, sempre por **1000x**. **Na base inteira, 187.621 bilhetes, sao 4 odds** (todas do `Jaao26`, 02 a 12/09) e **zero stakes**; `_num_or_none` e `_num_bloco` **nao divergiram em nenhuma linha gravada**. Em `custo_store`, **zero** dos 160 valores casa o padrao. **O unico cruzamento real e o `_apFaixa`** da tela de Apostas, onde o limite DIGITADO passa pelo `parseNum` e e comparado com `r.odd` vindo do `_num_or_none`: quem digitar `1.500` querendo odd 1,50 recebe tabela vazia, sem erro. **Registrado, nao consertado.** **O CUSTO DE EXTRACAO MEDIDO CONTRA A ESTIMATIVA DE JUL:** `uso_tokens` tem 3.889 chamadas e **US$ 880,91** desde 05/07; contra os 70.590 bilhetes de `origem='extracao'` da janela da **US$ 0,0125/bilhete**, e a estimativa bottom-up da s107 dizia ~US$ 0,011. **Ela se sustentou.** **CAMINHOS QUEBRADOS:** 5 referencias do CLAUDE.md nao resolviam da raiz (`dash/assets/js/app.js` 3x e `charts/gestao.js` 2x; o certo e `app/static/dash/assets/js/...`). **REGRA DUPLICADA, resolvida para UMA copia:** o aviso aos testers estava no invariante 9 E na secao propria, as duas dizendo *'toda atualizacao fechada = perguntar'*, contra a memoria de 16/09 (s368, *'desnecessario, e so correcao de bug'*). Ficou a secao, com o corte que decide: **o tester precisa fazer algo, ou passa a PODER fazer algo que nao podia? Se nao, nao pergunte.** **QUATRO MEMORIAS CORRIGIDAS** (`memory/`, fora do git): `project_planilhador` dizia *'FastAPI + Haiku 4.5'* tres meses depois do veto; `feedback_modelo_haiku_sonnet` mandava indicar `claude-sonnet-4-6`, que o `ALLOWED_MODELS` recusa desde a s377; `custo_conta_isolado_por_dono` descrevia o custo vivendo em localStorage, contra a secao do CLAUDE.md que existe por causa dos 16 donos; `custo_conta_janela_de_vida` defendia a regua NAO-aditiva que a s358 trocou, com um *'nao conserte isso achando que e bug'* que hoje aponta para o lado errado. **As duas primeiras guardam o veto intacto; so o ALVO foi atualizado.** **FAXINA DO CLAUDE.md, que estava em 66.560 B com teto de 66.560, folga ZERO:** **2.427 B liberados**, todos de PROCEDIMENTO, registro de sessao ou copia literal. A tabela de propagacao e o checklist que a repetia foram para `.claude/commands/propagar-categoria.md`, a skill que ja executava o procedimento (era a **terceira** copia do mesmo mapa); o diagnostico em 3 passos do matcher virou `docs/RUNBOOK_MATCHER_TIPSTER.md`; as narrativas dos tetos e das tres telas de custo ja estavam inteiras no `docs/historico/`; os dois blocos `Motivo:` eram copia literal do `CASOS.md:575` e `:636`. **Nenhuma regra cortada, e as tres que o Feca mandou conferir ficaram:** *reescreva os caminhos relativos ao mover*, *nunca corte os blocos de sintoma* e *Menu e DUPLO + gate `tests/test_sidebar_dupla.py`*. **CLAUDE.md fechou em 65.049 B, folga de 1.511 B.** **INVARIANTE 8 CARREGADO, e o registro e obrigatorio:** enquanto eu rodava os gates, a outra sessao commitou 5 vezes e **levou o meu `BACKLOG.md` dentro do `de7b0d0`** (a renumeracao do segundo `3.13` para `3.17`). E o caso `docs/CASOS.md#8` acontecendo com os papeis invertidos: desta vez foi o meu arquivo que pegou carona. `de7b0d0` ja estava pushado, entao **nao reescrevi historico**. A renumeracao esta correta no `main`, so nao esta no commit certo. O que me protegeu do resto foi `add` por NOME: os outros 15 arquivos em voo da outra sessao nao entraram. **ERRO MEU, corrigido pela metade:** rotulei o commit `8b75c18` e um ponteiro do CLAUDE.md de **s382**, que e a sessao do `aposta_em` do outro terminal. O ponteiro virou s384; **a mensagem do commit ja estava pushada e fica errada**. **NAO FEITO, de proposito:** o `_apFaixa` acima, e as linhas 407/530 do CLAUDE.md, que citam `app.js` e `filters.js` sem caminho (ambiguas, nao erradas; `filters.js` mora em `app/static/dash/assets/js/`, nao sob `charts/`). **ALERTA:** o `docs/CASOS.md` esta a **1.211 B** do teto, com menos folga que o CLAUDE.md que acabamos de destravar, e e o destino padrao de *mova o caso*. **Gates:** `check_docs` sem FAILs, `audit_casas` sem FAILs, `check-tokens` verde, suite **1.299 passed** (o `test_landing` dos travessoes voltou ao verde no `0578edd`, da outra sessao). Commits `190ac3f` e `8b75c18`. Faxina de documentacao: sem aviso ao grupo. **EM PARALELO, no terminal de LANCAMENTO (outra janela):** **os dois gates da CAPTURA entraram no CI, e estavam de fora desde sempre.** O CI rodava 4 dos 6: faltavam `node extensor/harness/run.mjs` e `python tools/audit_sharpenup.py`, justamente os que cobrem o robo que le as casas. O `CLAUDE.md` manda rodar o harness *"antes de todo commit que toque `extensor/`"*, e ate aqui isso dependia de alguem LEMBRAR — numa semana em que o `extensor/` muda quase todo dia (bet365 `aposta_em`, Lottu, 0.7.18). **O modo de falha que eles pegam nao e o site cair: e a captura gravar dado ERRADO na base de um dono, em silencio.** **CONFERIDO ANTES DE LIGAR, porque gate que nunca reprova e enfeite:** os dois propagam codigo de erro (`process.exit(1)` no `run.mjs`, `return 1` no `audit_sharpenup`), provado rodando o harness com filtro sem correspondencia (exit 1). O YAML foi validado por `yaml.safe_load` e o job passou de 9 para **11 passos**. Os 6 gates verdes localmente na ordem do CI (harness 29 casos / 474 bilhetes). **DECISAO DE PROCESSO, do Feca:** *"vc pode decidir as ordens, vc entende eu nao"* — a fila passa a ser definida aqui e executada uma de cada vez, com relato em linguagem simples. **Fila combinada, nesta ordem:** (1) gates no CI [FEITO]; (2) runbook de suporte para *"a captura da casa X parou"*, que e a pergunta que o tester vai fazer e hoje so existe na cabeca do Feca; (3) a aba Metricas parar de emitir veredito sobre base vazia (`Solidez Muito Baixa`, `Win Rate 0,0%` com zero aposta encerrada) junto do `overview.js:293`. **Pequenas, quando der:** `POST /tipsters/sugerir` registrado duas vezes no `main.py` (a segunda e codigo morto) e documentar que o app e PROCESSO UNICO (sessao de captura, rate limit e caches vivem em memoria; subir um 2o worker quebra o pareamento em silencio). **PARADO DE PROPOSITO:** o `figs.map is not a function` da aba Contas, visto UMA vez e nao reproduzido em 11 tentativas — sem repeticao, conserto seria chute em cima de sintoma. **PENDENTE E SO DO FECA: o ENSAIO do rollback** (`docs/RUNBOOK_ROLLBACK.md`), que segue com a tabela de registro vazia.)

_Anterior: 2026-09-23 (sessao 383: **o "u" do calendario era R$ com a etiqueta errada: o escopo de unidade do modal do tipster nao morria ao fechar.** Relato do Ewanderson1 no Telegram, sobre o Calendario da aba Resultados: *"Era p ser, mas eu n fiz 2.041u no dia 15"*. A base dele e em R$ (1u = R$ 50, s373), e a propria tela entregava: `Stake media 36,40u` nao existe, e R$ 36,40. **A CAUSA:** a s375 (`7d93e0e`) fez o drill do tipster seguir o switch R$/u e ligou `_uEscopo` no `renderTipsterDrill`; o comentario dizia que o `closeTipsterDrill` o desligava, **mas a linha foi parar no `closeCasaDrill`**, que nunca liga nada. Bastava abrir e fechar um perfil com o switch em u: calendario e Dia da Semana do dashboard inteiro passavam a escrever "u" sobre valor em reais (so a etiqueta, a conversao vive dentro do modal) ate recarregar a pagina. **CONSERTO:** a linha mudou para o `closeTipsterDrill`, e o `renderPage` ganhou uma rede: pagina pintada com o overlay do tipster FECHADO e sempre R$ (com ele aberto, o escopo e preservado, senao repintar por baixo tiraria o modal de u). **GATE:** `tests/test_uescopo_fecha_com_modal.py` + `tests/js/uescopo_fecha_com_modal.mjs`, recortando `closeTipsterDrill`, a rede do `renderPage` e o `mkCalendarHeatmap` de producao; **4 mutacoes, 4 detectadas** (inclusive o defeito original). **MEDIDO NO DEMO, headless:** abrir o drill em u (`emUnidades()` true), fechar (false), ir a Resultados: calendario com 0 "u" e 24 `R$`; escopo forcado ligado + `showPage` tambem volta a R$; zero erro de pagina. Suite 1.289 passed (o `test_landing` dos travessoes segue vermelho, anterior e de outra sessao). `check-tokens` verde. `?v=` performance 25, app 63. Bugfix: sem aviso ao grupo.)

_Anterior: 2026-09-22 (sessao 382: **a Bet365 passou a guardar a HORA em que a aposta foi feita, e a ideia do "Resolver apostas abertas" deixou de ser hipotese: esta medida.** O Feca retomou o [`PLANO_RESOLVER_ABERTAS`](docs/PLANO_RESOLVER_ABERTAS.md) e cobrou o caminho inteiro antes de qualquer codigo (*"como e onde vc vai buscar o resultado dela?"*). **A MEDICAO QUE DESTRAVOU O PLANO (§8.1), e ela era OFFLINE o tempo todo:** o `_resultadoB3` (`content.js`) ja deriva o Status do bloco a partir do `t.rt` — o RT do summary — e a `sombra_rotulos` guarda o bloco cru desde 26/08. Entao cruzar **13.115 bilhetes de Bet365** com `_veredito_do_retorno` respondeu a pergunta sem abrir uma aba: **W 98,7% · L 99,9% · V 99,0% · HW 100% (124/124) · HL 99,5%**. Nenhum desfecho sai do escopo; **zero bilhetes em SISTEMA** entre os converiveis, entao a ressalva do §8.2 nao morde hoje. **ACHADO DE QUEBRA, no BACKLOG 4.9:** as divergencias apontam para o BANCO, nao para o RT — **82 linhas**, das quais **69 sao `W` que o dinheiro diz `HW`**, todas em linha asiatica partida (a familia da s356, com 69 no lugar dos 39). **O QUE ENTROU:** a coluna `bilhetes.aposta_em` (TEXT) e o caminho completo do **carimbo de colocacao** — `formatTicketB3` imprime `Carimbo (colocacao · uso interno — NAO usar como data)` com o `TP`/`DA` **verbatim, 14 digitos**; `carimbos_do_texto` (novo, `repository.py`) le do TEXTO CRU e pareia por bloco; o `/extrair` devolve o mapa no `done`; o front transporta; o `/salvar` grava. **Nao passa pelo TSV nem pela IA de proposito** — e campo de IDENTIDADE, e a ultima coluna de identidade que a IA transcreve erra 0,21% (e o que o `_corrigir_codigos_fantasma` existe para consertar). **VERBATIM, sem converter fuso:** o `_dataKickoffB3` converte UK→Brasilia por fuso ASSUMIDO, e chave convertida obrigaria os dois lados do casamento a repetir a mesma suposicao; como chave, o que importa e os dois lados lerem a MESMA string. **So PREENCHE** (`COALESCE` nos DOIS caminhos do UPSERT): o instante de uma aposta nao muda, entao recaptura de bilhete antigo vira backfill de graca, inclusive em linha resolvida. **GATES: 7 mutacoes, 7 detectadas** — harness §6c (carimbo verbatim contra a fixture; e bilhete com `TP=00010101…` NAO ganha linha, porque chave falsa casa a aposta errada) e `tests/test_carimbo_colocacao.py` (fronteira do bloco, rotulo tolerante, tamanho, e as duas asserções estruturais do `COALESCE`). Harness verde nas 29 casas (474 bilhetes); suite 1.301 passed; o unico vermelho segue o `test_landing` dos travessoes, **anterior e de outra sessao** (confirmado rodando com as minhas mudancas em stash). **DECISAO DO FECA, e ela encolhe o plano:** *"nao tem problema nao resolver as abertas, e passar a resolver as proximas extracoes"* — o estoque de **480 abertas sem carimbo** fica FORA do escopo, e com ele sai o fallback de janela chutada do §6.3. **PENDENTE E HUMANO:** o carimbo so comeca a ser gravado quando os testers atualizarem a extensao. Versao **0.7.18** bumpada para isso. **CORRECAO de algo que eu afirmei errado no meio da sessao:** eu disse que a 0.7.17 nunca tinha sido avisada, porque li a PRIMEIRA ocorrencia de versao no `changelog.json` (uma linha solta com `v0.7.16`) em vez da lista `sharpenup`. A 0.7.17 **tem nota, datada de 21/09, e foi avisada**. O gate `test_changelog.py` e quem cobra isso: manifest bumpado sem nota deixa a suite VERMELHA, e a nota so nasce pelo `avisar_testers.py` — que publica no grupo no mesmo ato. Por isso o bump da 0.7.18 fica **sem commit** ate o Feca decidir avisar ou so gravar a nota (`--so-changelog`). **A SEGUIR, na ordem:** medir a colisao real de (carimbo, stake, odd) agora que o carimbo existe — o proxy pessimista (dia+stake+odd) deu **11.792 trios repetidos**, com casos de 14 no mesmo dia, entao a trava de par unico nos dois sentidos e o que segura a funcionalidade — depois a Fase A (listar o que resolveu, sem escrever), depois o aviso de truncagem da expansao, depois a Fase B com ensaio.)








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
