# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-11 (sessao 348: **as tres telas de custo viram UMA, e a Fatia 0 subiu como PREVIA so-leitura.** Pedido do Feca sobre `Custo de Tipsters`, `Custos de Contas` e `Fornecedores & Parceiros`: *"todas essas paginas eu como dono do site nao to usando, e isso significa q elas sao pessimas. Desorganizadas, dificeis de preencher os dados (...) falta ela entregar oq realmente ela foi feita pra fazer"*. O desenho foi fechado num canvas (diagnostico + tres direcoes + a tela recomendada) e as decisoes dele cravaram: **uma tela so, topo fixo (filtros do sistema + KPIs + cascata + aviso do que falta) e quatro abas** — Contas, Tipsters, Gerais e Raio-X; a pergunta *"a operacao na Superbet vale a pena?"* vai para **Bookies**, nao para Custos; a tabela que ranqueava ativo por payback vira **"o que falta lancar"**, porque comparar durabilidade entre fornecedores nao e comparacao justa (*"bet365 eh bet365 e super eh super"*); e o `% do lucro` / staking fica como **rotulo com o percentual combinado, sem motor de calculo** — *"o usuario apenas imputa o valor"*. **O QUE SUBIU: so a Fatia 0.** `charts/custos2.js` + a pagina `custos_v2`, registrada nas DUAS cascas (o array de nav do `dash/assets/js/app.js` e o `app.html`). Ela **nao grava**: le `custoData`, `ctData`/`cgData` e `_contasVida`, que ja estao no ar, e nao cria estrutura nenhuma. As tres telas antigas **ficam no menu ate a Fatia 5**, decisao do Feca — a previa nao grava, tira-las agora deixaria o Feca sem onde lancar. **A DIVERGENCIA DE REGUA, medida e ROTULADA na tela:** a Visao Geral cobra custo de conta pela **janela de vida** (`calcCostFiltered`: custo cheio de toda conta VIVA no recorte) e a tela nova cobra por **lancamento** (conta COMPRADA no recorte). No demo, set/26 da `Contas R$ 0` aqui e um valor cheio la — os dois certos, respondendo perguntas diferentes. E o caso *"os dois numeros certos que pareciam defeito"* do `CLAUDE.md`, e a saida foi a mesma: a tela DIZ o corte (`.c2-corte`). **Qual vira a regua unica e decisao da Fatia 2.** **A barra de filtros e COMPOSTA, nunca reescrita:** `buildFiltersCustos` monta `_grupoPeriodo` + `_grupoCasa` + um `buildMS` de Fornecedor. O primeiro rascunho tinha um navegador de mes proprio, que era um SEGUNDO Periodo na mesma tela (o defeito da s317) — o `_grupoPeriodo` ja abre as setas de mes quando o MTD esta ativo, entao o fechamento mensal e o MTD do componente que ja existe. Esporte e Tipster ficam de fora de proposito: descrevem a APOSTA e nao recortam custo. **TRES DEFEITOS QUE SO A TELA ABERTA PEGOU** (o `node --check` e o `check-tokens` passaram verdes nos tres): **(1)** o `.money` e largura de COLUNA (`width:100%` + `.money-val{min-width:10ch}`) e, posto dentro de uma frase, empurrava o vizinho para a linha de baixo — media 205px no cabecalho do Raio-X; carve-out escopada, igual a que o `.kpi-sub .money` ja tem. **(2)** dinheiro dentro de `.c2-eyebrow` (9,5px) faz o `.money-sign` (.76em) cair para **7,2px**, abaixo do piso do papel de label na Escada de Tinta — o valor saiu do eyebrow e foi para `.c2-total`, que e 13px. **(3)** com recorte de varios meses, o rodape das abas Tipsters e Gerais somava o PERIODO enquanto a tabela mostrava o MES: em YTD a tabela dizia set/26 e o rodape dizia jan a set. Passou a somar o mes que a tabela mostra, e a tela diz quando o recorte e maior. **Metodo que vale para a proxima tela do dash:** o screenshot headless com `--virtual-time-budget` da **falso vazio** — ele dispara antes do encadeamento `contasLoad + ctLoad + tipstersCadastroLoad`, e a primeira foto mostrou a pagina em branco com o codigo certo. A prova valida foi no Chrome de verdade, medindo `getComputedStyle` e os totais por `_c2totais()` dentro do **iframe** do dash (a casca redireciona `/` para `/app`, entao o contexto que interessa nunca e o do topo). **Gates:** `node --check` nos dois JS, `check-tokens` verde, Escada de Tinta varrida nos tres criterios (os unicos dois corpos de 9,5px sao `.c2-eyebrow` e `.c2-badge`, ambos `--ink-soft`, exatamente no piso; nenhum `--ink-mute` abaixo de 10px; nenhuma `opacity` como degrau) e a tela fotografada nas quatro abas contra o `servidor_demo`. **PROXIMO PASSO: o Feca navegar na previa com a base REAL** (171 contas, 62 tipsters) e criticar antes da Fatia 1, que e a tabela de precos do fornecedor com data de vigencia. As fatias 2 a 5 (custo por CONTA em vez de por par, tipo de cobranca do tipster, categorias de gerais, e Bookies recebendo custo e P/L liquido) estao no canvas e no BACKLOG. Os 2 FAIL do `check_docs` (`CLAUDE.md` e as copias no `Backups/`) sao os mesmos preexistentes das s345 a s347.)

_Anterior: 2026-09-11 (sessao 347: **o aviso de captura batia na porta de quem ja tinha entrado.** Relato do Feca, com print: *"a mensagem ta linda (...) Mas ela aparece em extracao por texto tbm. O problema e, que quando usamos o sharpenup, ele envia o texto pra caixa de texto e ai ao clicar em processar ele mostra a msg para usar o sharpenup q na verdade ja estamos usando"*. **A causa e de ONTOLOGIA, nao de logica:** `_avisarSeTemCaptura` (s345) pergunta uma coisa so, *esta CASA tem captura?*, e nunca perguntou de ONDE veio o conteudo. O texto que a ponte despeja no textarea (`pollExtensao`) e byte a byte indistinguivel de um texto colado a mao — mesmo campo, mesmo evento `input`, mesmo estado —, entao a tela oferecia a extensao a quem tinha acabado de usa-la. **O conserto e uma PROCEDENCIA, nao uma condicao a mais:** `extCapturaParceiro` guarda o id do parceiro cujo lote atual veio da ponte; o aviso sai da frente quando a marca e do parceiro selecionado. Marcada em `pollExtensao` para texto E imagem (captura de print tem o mesmo direito de nao ser advertida); zerada em `limparExtrator(true)` — que roda no envio e no botao Limpar — e em `desconectarExtensao`. **Por PARCEIRO, nao global:** captura recebida na conta A nao silencia o aviso na conta B, e essa distincao e um dos dois casos de teste que mutacao pegou. **Zerar so no `explicit` tambem e deliberado:** no `limparExtrator` implicito o conteudo continua vivo em `estadoExtrator` e volta ao formulario depois — a procedencia tem de voltar junto com ele, senao o aviso reaparece para o mesmo lote que ja veio da ponte. **Lote MISTO (texto da ponte + print colado no mesmo envio) fica sem aviso, por decisao:** a alternativa seria comparar o texto injetado com o que esta na caixa, e o operador edita o texto — comparacao que falha em silencio e pior que um aviso a menos. **Gates: recorte + 2 de 2 mutacoes detectadas, e a prova rodou tambem no Chrome.** O harness em node **recorta a funcao real** do `index.html` (nunca copia o trecho) e roda 5 casos; mutar a linha nova para fora derruba os casos 2 e 3, e troca-la por uma marca GLOBAL (`!= null`) derruba o caso 4, que e justamente o do parceiro vizinho. Por cima disso, uma prova de ponta a ponta contra o `servidor_demo` exercita as duas pontas de verdade: a ponte entrega uma captura (`pollExtensao` com `fetch` dublado), a marca aparece no parceiro certo, o aviso nao abre, o `limparExtrator(true)` zera e o texto colado a mao **volta a abrir** o modal. **Duas notas de metodo que valem para o proximo harness desta tela:** `page.evaluate` do puppeteer roda em ISOLATED WORLD e **nao enxerga `let` de topo de script** — `parceirosCache` e `extCapturaParceiro` so aparecem por `Runtime.evaluate` via CDP, no main world; e a casca redireciona `/` para `/app`, entao o contexto que interessa e o do **iframe** da Extracao, achado por `Page.getFrameTree` + `executionContextCreated`. Sem as duas, o harness da ReferenceError e parece defeito do codigo. **Medido de lado, nao corrigido aqui:** o `/casas` do `servidor_demo` ainda **nao devolve o campo `captura`** que a rota real passou a devolver na s345, entao no demo o selo e o aviso nunca acendem sozinhos (no harness o Set foi alimentado a mao, declarado no cabecalho do script). Vai para o `BACKLOG`. Os dois 404 do demo (`/eventos`, `/changelog`) sao rotas que ele nao implementa, medidos contra a pagina limpa e preexistentes. **Gates:** 863 passed / 36 skipped, `check-tokens` verde, `check_docs` com os mesmos 2 FAIL preexistentes (`CLAUDE.md` 66,3 KB e 223 copias no `Backups/`). **Pendente: validar ao vivo** — capturar pela extensao numa casa com captura e conferir que o Processar nao pergunta mais; depois colar um texto a mao na mesma conta e conferir que o aviso volta.)

_Anterior: 2026-09-11 (sessao 346: **a ALCA do RAIO-X ficou; a DIETA DE COLUNAS foi REVERTIDA pelo Feca no mesmo dia.** Leia o veredito antes do resto: *"na tela grande ficou pessimo, um monte de espaco sobrando (...) a unica mudanca que eu gostei foi o raio-x recolher. TODAS AS MUDANCAS FEITAS NA LINHA DA APOSTA FICARAM HORRIVEIS. VOLTA A LINHA ANTERIOR COM O RAIO-X RECOLHIVEL"*. A linha voltou byte a byte ao estado pre-dieta (`git show 8835927:app/static/index.html` + reaplicacao so do patch da alca, 6 hunks, 11 colunas e 11 celulas conferidas no headless). **O QUE A REVERSAO ENSINA, e que a medicao nao pegava:** eu medi OVERFLOW e nao medi VAZIO. Em tela grande a coluna elastica unica (`minmax(...,1fr)`) absorve toda a sobra e vira um vao entre a descricao e as colunas de dinheiro — tirar 3 colunas de conteudo PIORA isso, porque sobra ainda mais para ela absorver. 'Cabe' e 'fica bom' sao criterios diferentes, e o gate que eu montei so media o primeiro. **E a assimetria da recusa e o dado:** o mesmo aperto que o tester sente em laptop vira desperdicio em monitor grande, entao mexer na LINHA (que e a mesma em toda tela) para resolver um problema de LARGURA (que varia por tela) ataca no lugar errado — quem varia com a tela e o LAYOUT, e e por isso que a alca sobreviveu e a dieta nao. O registro do que foi feito fica abaixo porque a medicao segue valendo para quem tentar de novo. **O QUE FICOU NO AR: a alca.** ||| REGISTRO DA TENTATIVA REVERTIDA: **a grade nao cabia em MONITOR NENHUM, e o tester achava que o problema era o RAIO-X.** Relato: *"se der pra recolher o raio x fica melhor de visualizar as bets / quero ver se marcou o resultado certo, ou a stake que usei / tenho que puxar pro lado"*. **Medido antes de mexer:** as 11 colunas de `.btbl-cols` somavam **1.300px fixos** (gaps e padding inclusos) e a coluna que as hospeda recebe **662px** num laptop de 1366 — stake, odd, resultado e P/L viviam atras do scroll horizontal, e **nem em 1920 a tabela aparecia inteira** (1.216 disponiveis contra 1.300 pedidos). **O pedido do tester nao fechava sozinho:** recolher o RAIO-X devolve 388px e ainda faltariam 250 em 1366, agora sem o painel que diz se a extracao esta limpa. **O corte que resolveu e de CONTEUDO, nao de espaco:** esta grade e sempre de UMA conta (`carregarTodosBilhetes` filtra por `casa`+`parceiro`), entao `Casa · Parceiro` (162px) repetia a conta ativa do topo em **toda** linha. Saiu. `Esporte` ficou no chip com o nome no `title` (108→40), `Acoes` perdeu a folga (80→48) e `Data` perdeu o seculo (74→62, `_dataCurta`). **Stake, odd, resultado, P/L e tipster ficaram INTACTOS** — sao o que ele foi procurar. A tabela passou a pedir **946px**. **O achado de UI repetiu a licao da s345 (o degrau mede a CELULA, nao a tabela):** o piso da coluna elastica comecou como `@media` da janela e o headless mostrou **13px faltando em 1600** — a janela nao sabe se o RAIO-X esta aberto nem quanto a casca cedeu; a LISTA sabe. Virou `@container btbl`, e quando ela aperta quem cede e a DESCRICAO (trunca, com o texto inteiro no `.desc-pop` e no `data-full`), porque stake e resultado nao tem para onde ceder. **Medicao headless contra o `servidor_demo`, 7 larguras: 1280, 1366, 1440, 1600, 1920 e 2560 CABEM com overflow ZERO** (antes faltavam 724px em 1280 e 84px ate em 1920). **`BTBL_COLS_KEY` subiu para v4**: a chave guarda 11 larguras e restaura-las traria a tabela velha de volta **em silencio**, justo para quem mais usa a tela. **Preexistente, medido e NAO corrigido aqui** (provado por remocao contra o `HEAD`, identico com e sem a mudanca): com o iframe abaixo de 1180 o `.workfull` empilha, o `#partner-page` fica com **altura 0** e o RAIO-X sobrepoe a area de captura — some a grade inteira em janela menor que ~1450. Vai para o `BACKLOG`. **Gates:** 863 passed / 36 skipped, `check-tokens` verde, Escada de Tinta varrida nos tres criterios (nada novo abaixo do piso; `.btbl-th` em 9px `--ink-mute` e desvio PREEXISTENTE, ja registrado no conflito `UI_REFERENCE §2` x Escada), JS inline sem erro de sintaxe e a tela fotografada em 1700 e 2200. ||| FIM DO REGISTRO REVERTIDO. **A ETAPA QUE FICOU: a ALCA do RAIO-X.** O botao de recolher NAO foi para a `.grade-actions` — o Feca leu o rascunho ali e disse *"ta bem estranho perto dos demais botoes"*, e ele estava certo: aquela barra e de acao sobre a APOSTA (inserir/exportar/sugerir) e recolher painel e acao sobre a TELA. O controle mora na BORDA do painel que ele controla (`.rx-alca`): fita de 18px no vao entre a lista e o rail quando aberto; recolhido, e a propria coluna de 22px com o rotulo na vertical (so um chevron seria enfeite mudo). **A alca carrega o ESTADO** (`.rx-dot`, verde limpa / ambar pendencia, lido do `verdict` da extracao) — recolher nao pode esconder que ha pendencia a conferir, e qualquer veredito que nao seja `ok` acende ambar, porque "nao sei" nao pode passar por "esta tudo certo" numa fita de 18px. **O default da 1a visita e MEDIDO, nao um breakpoint escrito na mao:** `decidirRaioXInicial` le `scrollWidth > clientWidth` da propria lista no fim do `renderGrade` — se a tabela nao couber, o RAIO-X nasce recolhido. Medido headless: **1450 e 1500 nascem recolhidos** (aberto teria 143 e 93px de overflow) e **1600, 1700, 1920 e 2560 nascem abertos**, com overflow ZERO em todas, e o clique alterna nos dois sentidos. A preferencia salva sempre manda. **Custo honesto, diferente do que a maquete prometia:** recolhido o rail vira faixa de 22px (+16 de vao), entao devolve 350px dos 388 — a alca flutuante sobre a lista sobreporia o botao de deletar da linha do meio. **Duas armadilhas de cascata:** `[hidden]` nao vence o `display:flex` proprio do `.rail-card`, e `.workfull.rx-off` (duas classes) vencia a regra de uma classe DENTRO do `@media 1180`, deixando coluna fantasma numa tela ja empilhada — as duas desfeitas explicitamente. Regra registrada no lugar canonico (`UI_REFERENCE §4`), com o `Recolher captura` marcado como desvio anterior a ela. **A prova do teste que mentia:** a 1a medicao do default deu resultado alternado (1500 aberto com 93px de overflow, 1600 recolhido sem precisar) e a culpa era do HARNESS, nao do codigo — o clique de cada iteracao persistia a preferencia, e com ela salva o decisor nem roda, por desenho. Limpar o `localStorage` ANTES do load poe as 6 larguras no lugar certo. **Depois da reversao, o decisor da 1a visita passou a valer MAIS, nao menos:** com as 11 colunas de volta a tabela pede ~1.300px, entao em 1700 a tela nasce com o RAIO-X **recolhido** (lista 1.344, overflow 0) e so em 2000 ela nasce aberta — ou seja, a alca virou sozinha o conserto do relato do tester, sem tocar em coluna nenhuma. Medido: 1700, 2000 e 2560, 11 colunas / 11 celulas, overflow 0 e o clique alternando nos dois sentidos. **TERCEIRO ATO: o VAZIO, que era a queixa de verdade.** Com a linha de volta ao original, o Feca conferiu a ordem das colunas (identica byte a byte ao `8835927`, provado contra o HTML servido em `www.sharpen.bet`) e nomeou o que o incomodava: *"acho que eu me confundindo pelo posicionamento e espaco vazio"*. **Medido no print dele:** a coluna `Aposta / Evento` com ~890px e o texto ocupando ~210 — 680px de buraco numa celula so. **Causa:** ela era a UNICA coluna elastica, entao toda a sobra da tela caia nela. E isso nasceu de uma decisao anterior do proprio Feca (tirar o spacer 1fr morto a direita das Acoes): a sobra tinha de ir para algum lugar, e foi toda para a descricao. **Conserto: repartir.** `Tipster` e `Casa · Parceiro` deixam de ser px fixo e viram `minmax(piso, fr)` junto com a descricao — os PISOS sao os mesmos de antes, entao **em tela apertada nada muda** (sem sobra, nao ha o que repartir) e o resize por arrasto continua valendo (o px salvo vira o piso). `Esporte` fica fixo de proposito: nome curto e conhecido, crescer nao mostra mais nada. **Calibrado por medicao, em duas rodadas:** 1,5/1/1,5 deixava 286px de vazio na coluna Casa e o olho lia o salto ate a Stake; **1,2/0,9/1** poe as tres com ar parelho (medido em 2560: descricao 419px, tipster 314, casa 349, ar ~230 em cada). O `fr` do CSS Grid **nao e piso + fatia da sobra** — ele divide o espaco livre TOTAL pelas fracoes, e foi por isso que a 1a calibragem errou o alvo. **O aviso saiu no fim, depois da reversao** (`message_id 3463` + a mesma nota na home, `changelog.json` com 17 itens): fala do RAIO-X recolhivel e do encaixe em monitores diferentes, e diz que as colunas continuam as mesmas, na mesma ordem — quem viu a versao do meio do dia precisa saber que ela nao ficou. A 1a versao da mensagem, escrita antes de o Feca abrir a tela, descrevia colunas que foram revertidas: **e para isso que serve nunca enviar sem o 'pode mandar'**. **PROXIMO PASSO:** validar ao vivo no monitor do Feca (Ctrl+Shift+R, conferir o ar entre as colunas em tela larga e a alca nos dois estados) e decidir o `BACKLOG 3.8`, que e o unico caso em que a tela ainda quebra de verdade em monitor pequeno. Os 2 FAIL do `check_docs` (CLAUDE.md 66,3 KB e 223 copias no `Backups/`) sao os mesmos da s345. **QUARTO ATO: o botao que nao sabia que a conta ja estava arquivada.** Relato: entrar numa conta da aba **Inativas** e o idcard oferecer *Arquivar*. O `#acctArchive` nascia estatico no markup (icone, `title` e a classe `danger` fixos) e o handler chamava `contasArquivar` sempre — o clique batia de novo no `/parceiros/{id}/arquivar`, sem efeito visivel nenhum. O Painel de Contas ja era bimodal; era so o idcard da Extracao. **Conserto:** o estado sai de `_contaAtivaArquivada()`, que usa **o mesmo teste de `_acctListaPlana()`** (estar ou nao em `parceirosCache`) — um segundo criterio aqui (`p.arquivado`) poderia divergir em silencio do que separa as duas abas no resto da tela. Em conta arquivada: icone de reativar, `title` "Reativar conta" e `danger` **desligado**, porque o `--neg` do hover e a intencao de arquivar, nao a de reativar. O handler le o MESMO `_contaAtivaArquivada()` **no clique**, entao rotulo e acao nao tem como discordar; o markup nasce vazio de proposito, senao haveria dois lugares dizendo qual e o modo. Zero CSS e zero icone novos (reuso de `_ICO_ACAO` e de `.chgbtn.p.danger`). **Sintoma para reconhecer isto noutro botao:** acao cujo rotulo foi escrito uma vez no HTML e cujo alvo tem DOIS estados — a tela nao erra, ela so convida para o lado errado. **Gates:** 863 passed / 36 skipped, `check-tokens` verde, e os dois estados fotografados headless contra o `servidor_demo` (7K / Davi [Norte]), com paths de SVG diferentes e zero erro de JS. **Pendente: validar ao vivo** (F5, abrir uma conta pela aba Inativas e conferir que o botao mostra a seta de reativar e que o clique devolve a conta as Ativas) — tudo aqui foi provado headless contra o demo.)


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
