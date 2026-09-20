# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-19 (sessao 375: **as tres pendencias que estavam esperando o Feca sairam, e a primeira delas virou outra coisa no meio do caminho.** **(1) `Tenis de Mesa` ganhou secao na `MASTER_ESPORTES §7` — e a propagacao DESMENTIU a propria premissa.** A pendencia dizia *"e a grafia de facto do projeto, so falta a secao"*; medido, os **43 bilhetes** que carregam o rotulo sao **badminton mal classificado**: cruzando cada participante com as listas auxiliares da propria §7, **14 casam com Badminton** (`Supanida Katethong`, `Nhat Nguyen`, `Jeon Hyeok-jin`, `Chou Tien-chen`, `Lee Chia-hao`) e **ZERO com Tenis**; 41 dos 43 sao Bet365, onde o esporte vem da IA. **A secao entrou assim mesmo, e por um motivo diferente do que a pendencia dizia:** o de-para determinístico da SportingBet/Betboo (`_ESPORTE_SPB[56]`) vai gravar esse valor na primeira aposta real, e a `taxonomia.py` le os H2 da §7 como o universo do que existe — valor fora da lista canonica e divida. **Ela nasceu SEM lista de atletas, de proposito:** publicar uma lista tirada de um acervo que e badminton transformaria erro de classificacao em referencia canonica. E a **Regra Critica de raquete aprendeu o QUARTO esporte**, com sinais positivos proprios (`ITTF`, `WTT`, `Setka Cup`, `TT Cup`, `Liga Pro`, sets de 11 pontos contra os 21 do badminton) e a mesma exigencia que Badminton e Dardos ja tinham: **so com sinal positivo, NUNCA como desempate** — os 43 foram rotulados sem evidencia nenhuma, que e o que essa linha existe para impedir. **UMA AMBIGUIDADE FICOU DECLARADA E NAO CONSERTADA, de proposito:** o item 4 da regra trata *total de PONTOS entre pessoas* como sinal positivo **sozinho** de Badminton, com a justificativa de que *"o tenis nao tem total de pontos e os dardos contam legs"* — e **tenis de mesa tambem conta pontos**, entao a justificativa deixou de cobrir o universo. Medido: o item decide **1.294 de 2.813** bilhetes de badminton (46%), e mudar o desempate de quase metade de um corpus e mudanca propria, com medicao antes e depois, nao efeito colateral de uma propagacao. **(2) O drill-down do tipster passou a seguir o switch R$ ⇄ u** (`BACKLOG 1.18`, fechado). **O argumento que decidiu nao foi consistencia de tela:** a conversao e feita **linha a linha, pela unidade vigente na data de cada uma**, entao a serie em `u` e NORMALIZADA POR ERA e a serie em R$ nao e (uma stake de R$ 50 vale 2u numa epoca e 0,5u em outra). Drawdown e Monte Carlo medem RISCO; para isso a serie em unidades e a entrada mais honesta das duas. Regua nova: `_linhasEmU` (`app.js`), irma do `_tipsterUnidades` — este devolve TOTAIS, e quem anda linha a linha precisa da SERIE. **A TELA ACHOU TRES DEFEITOS QUE NENHUM `node --check` ou suite pegaria.** (a) **O calendario passou a dizer `u` MANTENDO o numero em reais** — pior que antes, porque mentia. Causa: a minha ancora de substituicao **nao era unica no arquivo** e eu troquei a ocorrencia errada, dentro do `_tipCalNav`, onde a variavel nem existia — teria estourado ao trocar de mes. A base convertida virou `_tipCalBase`, de MODULO, porque o calendario tem navegacao propria que repinta depois do render. (b) **Seis lugares do `shared.js` decidiam R$ x u por um ternario sobre `window.MODO_PUBLICO`** — o mesmo defeito que a s374 consertou nos cards, um nivel abaixo: calendario e Dia da Semana ficavam em R$ dentro de um modal em u. Virou **predicado UNICO** `emUnidades()`, que cobre o modo publico E o switch privado, com `_uEscopo` acompanhando o MODAL e nao o render. (c) **`TURNOVER (U)` em maiuscula** — o cabecalho tem `text-transform:uppercase` e a unidade e minuscula por definicao. **E UMA EXCECAO FICOU, agora DELIBERADA E ROTULADA:** o bloco Gestao do Tipster segue em R$ — `Stake Atual` e o TAMANHO da unidade (em u seria sempre `1,00u`) e o `Custo` e mensalidade lancada em reais POR MES, sem data por linha; converte-la exigiria eleger uma unidade para o mes inteiro, que e modelagem, nao formatacao. Ela ja saia certa **por acidente** (o `renderGestaoTipster` e `async` e caia depois da restauracao das mascaras); hoje esta escrito, e o sub diz *em R$* quando a tela esta em u. **(3) O aviso da 0.7.14 NAO foi editado** (decisao minha, registrada): acrescentar a linha do painel exigiria mexer na mensagem do grupo E no changelog juntos, duas operacoes dificeis de desfazer por uma linha. **O achado que importa e que o problema nao e de aviso, e de produto:** `CASAS_CONECTAVEIS` e um `Set` com 31 nomes escritos a mao no `index.html`, e o `GET /casas` **ja devolve** `captura`, derivado do `_HOSTS_POR_CASA`. **Conferido: os dois concordam hoje — 31 e 31, divergencia zero nos dois sentidos**, entao e duplicacao que ainda NAO driftou; o preco que ela ja cobra e de PROCESSO (um ponto de registro no guia e a linha do segundo `Ctrl+Shift+R` em todo aviso de casa nova). `BACKLOG 1.19`. **GATES: 18 mutacoes, 18 detectadas** (5 novas no `tipster_visao_u`, cobrindo a serie por era, a stake convertendo junto, a linha sem unidade ficando FORA em vez de virar zero, e a nao-mutacao da entrada). **A remocao quebrou um gate vizinho e o defeito nao era dele:** o `calendario_escopo.mjs` nao conhecia o predicado novo. **E A CRASE ME PEGOU DE NOVO**, no comentario que eu tinha acabado de escrever dentro de um template literal (o caso da s296) — segunda vez em duas sessoes. **E O `?v=` DE NOVO, pela terceira vez:** o meu `sed` com aritmetica produziu `shared 110`, `performance 123` e `app 161` em vez de 11/24/62. So a conferencia do resultado pegou. **`sed` em arquivo compartilhado se confere pelo RESULTADO, nunca pelo comando.** Medido no Chrome dentro do iframe: modal em u com 172 ocorrencias de `u` e 1 de `R$` (a excecao rotulada), Monte Carlo em u (`−108,80u` / `−230,20u`), calendario convertido de verdade (`+R$8.337` virou `+32,21u`), e as mascaras do MODULO restauradas depois do render — vazamento ali deixaria o dashboard inteiro formatando `u`. Suite 1.236 passed, `check-tokens` e `check_docs` verdes, harness do extensor verde (29 casos, 471 bilhetes). `?v=` de shared/performance/app em 11/24/62. **PENDENTE: reparar os 43 bilhetes e do Feca e dos 5 donos** (`BACKLOG 1.20`) — e o passo barato e **medir de novo depois de alguns lotes**, para saber se a regra nova ja evita a recaida antes de consertar o sintoma. **EM PARALELO, na sessao 373 (aba Contas, outra janela):** o 3o painel deixou de se chamar `Retorno sobre aquisicao`. O Feca pediu `Retorno sobre o custo da conta` ou `Retorno sobre os custos das contas`, depois de eu apontar que a sugestao anterior dele caia numa VARIANTE de grafia de uma das tres palavras que o `test_o_vocabulario_proibido_nao_volta_ao_produto` barra desde a s358: o gate lista a forma exata, e entrar pela variante seria driblar uma regra dele com um sinonimo. **O titulo foi ENCURTADO para `Retorno sobre o custo` por MEDIDA, nao por gosto:** em 1366 o titulo inteiro quebrava em duas linhas (28px contra os 14px dos dois vizinhos) e empurrava a figura 14px para baixo, desalinhando os tres paineis; o contexto a direita ja diz `N de N contas`. Com o titulo dizendo *retorno sobre o custo*, a pergunta antiga (`O que as contas devolveram sobre o que custaram?`) virava eco, entao ela passou a ser a DECISAO que o multiplo informa: `As contas se pagaram?`. **E a medicao da tela achou coisa que os gates de codigo nao veem:** com o drill aberto, a aba **rola 18px na horizontal em 1366** (fechada da +0; 1440 e acima dao +0 nas duas). Nao e artefato: `scrollLeft` chega a 18 de verdade e forcar reflow nao resolve. Causa medida na cadeia de ancestrais: `.main` e item flex (`layout.css:201`, `flex: 1`) com `min-width: auto`, entao ele se recusa a encolher abaixo do proprio min-content (1120,31) quando a barra de rolagem vertical aparece e o util cai para 1102; o piso vem do `#contasContent` (min-content 1075). **NAO corrigido de proposito:** a correcao canonica e `min-width: 0` no `.main`, que e CSS de casca e vale para todas as telas — a aba Apostas ja transborda +194 em 1366 por conta propria, e o encolhimento trocaria transbordo-com-rolagem por conteudo vazando sem rolagem. Virou `BACKLOG 4.5`, com a pista de medir o min-content dos cinco filhos do `#contasContent` antes de tocar em qualquer CSS. `contas_vida.mjs` 14 blocos verdes, `test_contas_vida.py` 11 casos, `check-tokens` e `check_docs` verdes, medicao headless nas cinco larguras. `?v=` de contas em 15.)

_Anterior: 2026-09-19 (sessao 372: **a aba Contas foi reescrita na v4, a partir de um handoff de design que o Feca trouxe do Claude Design** (`design_handoff_contas_v4`, zip + projeto). A logica de calculo NAO mudou; mudou a ORDEM DA LEITURA. A v1 entregava a resposta como PLANILHA (quatro KPIs neutros, tabela de dez colunas, e o retorno mais importante num cartao no fim da pagina); a v4 encadeia tres granularidades: **tres PAINEIS** pela base inteira (longevidade · volume e margem · retorno sobre aquisicao), **FICHAS por casa** repetindo a mesma ordem, e o **DRILL** por conta. Entrou o que nao existia: histograma de vida em 5 faixas, **ROI liquido**, **custo por dia de vida**, **gauge de multiplo com marca de piso em 1,00x**, composicao do custo, barra de cobertura de preco e o rodape de definicoes. **AS TRES DECISOES DO FECA, e a primeira desarmou um conflito aparente:** (1) o handoff mandava CORTAR `Apostas`, `Turnover bruto` e `ROI bruto` por casa — exatamente os tres que ele pediu na s366 —, mas o proprio handoff abre a porta (*“se voltar, tem de ser apostas por conta”*), entao os tres sobrevivem mudando de UNIDADE: turnover por conta, ROI bruto ao lado do liquido, apostas por conta. Nao havia conflito real. (2) Sobre os R$ 76.600 x R$ 59.600: o Feca encerrou como *“evolucao do custo ao longo do tempo (novas contas)”* e eu aceitei — **e a medicao, que a sessao vizinha ja tinha feito na s369, diz OUTRA coisa, com as duas causas identificadas.** R$ 59.600 era a regua lendo o `CUSTO_SEED` (11 pares cravados no `gestao.js`) e R$ 76.600 e a MESMA regua lendo o `custo_store` (14 pares); as duas tabelas concordam em 10 pares e os tres de Bet365 sao identicos, **que e a causa exata do “so a Bet365 bate”**. O R$ 500 constante que sobrava na Superbet era o segundo defeito: `arthurbarbosabets` gravada com colchete duplo (`[[JC]]`), cuja chave `[JC]||Superbet` nao existia em tabela de preco nenhuma. Provado por REMOCAO contra dump do Postgres real. **As duas causas ja morreram**: o `CUSTO_SEED` saiu na s369 e o colchete duplo foi corrigido na s369 a pedido do Feca. **Licao para mim: eu insisti tres dias numa investigacao que ja tinha sido fechada, e depois aceitei uma explicacao plausivel sem medir. `git log` e `BACKLOG` antes de abrir frente — e explicacao que cabe nos dados nao e a mesma coisa que causa medida.** (3) **`Inativas`, nunca `Encerradas`**: *“a palavra ja vem da base do Sharpen”*. Vale no segmentado E no estado da conta dentro do drill — um vocabulario so. **TRES DECISOES MINHAS, que o handoff deixou em aberto ou que colidiam com o que ja existe.** **A barra de filtros continua sendo a do APP**, nao o campo `.fv` desenhado no prototipo: o app inteiro usa `.filters`/multiselect, e adotar um segundo estilo so aqui e o item 8 do checklist de UI. Do handoff entra o que e da TELA. **Custo por dia = custo ÷ SOMA das duracoes**, e aqui o README do handoff CONTRADIZ os proprios numeros dele: o texto diz mediana, mas Novibet R$ 9.800 ÷ 15,22 = 644 dias = 28 contas x 23 de media, que e a soma. A soma tambem e a unica regua aditiva. **Default `inativas`** (era `ambas`), porque e a populacao que responde quanto uma conta aguenta. **O HANDOFF USA UMA PALAVRA BANIDA DO PRODUTO, e o gate pegou:** `Investido em contas` — `test_o_vocabulario_proibido_nao_volta_ao_produto` lista as tres proibidas desde a s358. Virou `Custo das contas` / `valor pago na aquisicao`. **E ele reprovou o meu proprio COMENTARIO** que explicava a regra, igual a s364: o gate varre o arquivo inteiro, entao nem para documentar se escreve a palavra. **A REESCRITA APAGOU TRABALHO DA SESSAO VIZINHA, e foram os gates DELA que acusaram:** ao reescrever o `contas.js` inteiro eu levei junto o `${_grupoLimpar('contas')}` e o `LIMPAR_EXTRA.contas` que a s371 tinha acabado de adicionar. `test_limpar_tudo_filtros` reprovou e os dois voltaram — o `LIMPAR_EXTRA` agora volta para uma constante `CN_POP_PADRAO` em vez do literal `ambas`, e **repinta as classes do segmentado**, porque a barra de filtros nao e remontada a cada render e mexer so na variavel deixava o botao aceso mentindo. **Licao: reescrever arquivo inteiro e uma operacao destrutiva quando ha outra sessao aberta — o `git diff` do backup e mais barato que o gate, mas foi o gate que salvou.** **TRES COISAS QUE SO A TELA DEU**, nenhuma visivel a `node --check`, ao `check-tokens` ou a suite: (a) **a aba nascia VAZIA e sem explicacao** — com o default `inativas`, um dono cujas contas estejam todas vivas abre a tela e ve tres paineis zerados; medido no `servidor_demo`, onde as 102 contas sao ativas. Entrou estado vazio que diz a RAZAO e oferece a saida (atalhos para as outras populacoes), que o handoff ja listava como pendente; (b) **classe escrita com DOIS nomes** — o botao do vazio saiu `cn-vazio__btn` no JS e `cn-empty__btn` no CSS, entao ele existia na tela com a cara nativa do navegador no meio de uma superficie estilizada. Virou gate de FORMA (`test_toda_classe_cn_usada_no_js_existe_no_css`, 52 classes conferidas, provado por mutacao); (c) concordancia — *“Nenhuma conta inativas”*, porque o rotulo do segmentado e plural por natureza e nao serve de adjetivo. **GATES: 12 de 12 mutacoes detectadas** no `contas_vida.mjs`, que ganhou os blocos 10-13 (ROI liquido sai do denominador ELEGIVEL e nao do turnover inteiro · custo/dia pela SOMA e nao pela mediana · histograma com faixas inclusivas nas duas pontas · o agregado dos paineis sai das MESMAS contas que as fichas). `test_contas_vida.py` em 10 casos. **Suite 1.231 passed**, `check-tokens` e `check_docs` verdes, Escada de Tinta varrida nos tres criterios. **Medido no Chrome dentro do iframe**: 3 paineis, histograma de 5 faixas, cobertura de 3 segmentos, drill abrindo e ordenando sem fechar, `Limpar tudo` voltando a Populacao ao default, e **transbordo 0 em 1366/1440/1600/1920/2560**. **PENDENTE:** o aviso ao grupo NAO sai ate o Feca testar (*“nao pq eu nem testei”*) — virou `BACKLOG 1.21`, escrito pela sessao vizinha. Fica tambem a conferencia do card `Custo das contas` contra a tela de Custos, na base real. O `1.13` ja estava FECHADO desde 16/09, com a reconciliacao acima. `?v=` de contas/components em 8/60.)

_Anterior: 2026-09-18 (sessao 374: **duas sugestoes do tester Joao, e a primeira ja esta no ar: o switch R$ / u da tela Tipsters passou a valer para a TELA inteira.** O “u” alcancava o KPI do topo e a coluna P/L do Comparativo; os **cards ficavam em R$**, porque eles so sabiam renderizar u pelo `MODO_PUBLICO`, que nao existe no dashboard privado. Um card dizendo `− R$ 1.520,31` logo abaixo de um KPI dizendo `−28,38u`: cada metade certa, a razao entre as duas impossivel de ler. **Agora trocam JUNTOS** o P/L, o Turnover, a Stake Media e a **sparkline** de cada card, o KPI `Turnover Total` e as colunas `Turnover` e `Stake media` do Comparativo Geral. **A REGUA E UMA SO** (`_tipsterUnidades`, `app.js`), e ela converte **por linha, pela unidade vigente na DATA daquela linha**: a escada muda no tempo, e dividir o total por uma unidade so misturaria eras. **Linha que nao da para converter (sem escada E sem stake) fica FORA das somas**, nunca entra como zero, que e a familia do “zero se disfarca de conta feita”. **ROI, Win Rate e Odd Media NAO entram, de proposito:** sao adimensionais, e converte-los seria inventar uma segunda regua para o mesmo numero. **A ORDENACAO passou a seguir o que esta na tela** (em u, P/L e Turnover trocam de ordem entre tipsters, porque cada um tem sua unidade). **E a mascara de agregado em u virou UMA**: o `fmtRU` nasceu do trecho que so existia dentro do modo publico, e o modo publico agora aponta para ele em vez de carregar copia propria. **GATE: 13 mutacoes, 13 detectadas** (`tests/test_tipster_visao_u.py` + `tests/js/tipster_visao_u.mjs`), com a ancora conferida como **UNICA** antes de mutar: os tres cards (esporte, casa, tipster) nasceram copiados um do outro, e mutacao que acerta o alvo errado passa verde com razao. **E foi MEDIDO NA TELA, nao so em teste:** headless contra o `servidor_demo`, 23 cards antes e depois da troca, **nenhum `R$` sobrando em modo u** nos cards, nos 4 KPIs e na linha do Comparativo, nenhum NaN, console limpo e o switch reversivel. 1.216 testes passando, `check-tokens` verde. **FICOU DE FORA, declarado no cabecalho do gate:** o drill-down do tipster (o modal que abre ao clicar no card) segue em R$, porque a curva e o Monte Carlo rodam sobre a serie em reais; converte-lo e decisao do Feca, nao consequencia desta. **A SEGUNDA SUGESTAO TAMBEM ENTROU, e com escopo maior do que o pedido** (decisao do Feca: *“verificar onde nao existe o limpar tudo e inserir tbm, nao so onde ele pediu”*): o **“Limpar tudo”** existia so na Base Completa, e quem recortava a Visao Geral por tres eixos desfazia um por um. Ele virou **peca da BARRA** (`_grupoLimpar`, em `filters.js`), entao as **10 telas** que montam barra o ganharam juntas: Visao Geral, Resultados, Esportes, Bookies, Tipsters, Fornecedores, Metricas, Em Aberto, Custos e Painel de Contas. Copiar o botao tela a tela criaria N botoes que divergem no primeiro ajuste (a licao da s317). **A Base Completa segue com o dela** na faixa de filtros ativos: dois botoes do mesmo papel na mesma tela e o sintoma de “fora do padrao” que o item 8 do `/nova-ui` manda evitar. **So aparece com filtro LIGADO**, como la: botao morto em tela limpa e ruido. **TRES DECISOES que o botao obrigou a tomar. (1) LIMPAR E VOLTAR AO PADRAO DA TELA, nao ao vazio:** a tela de Custos nasce em **MTD** de proposito (e de fechamento mensal, e “Tudo” nao fecha mes nenhum), entao ali o botao devolve o MES, e o proprio MTD **nao conta** como filtro ligado. **(2) O filtro LOCAL da tela entra na conta:** o seg de Populacao do Painel de Contas nao vive no `MSS`, e sem o registro (`LIMPAR_EXTRA`) o botao limparia metade da tela dizendo “Limpar tudo”. **(3) Eixo se casa por PREFIXO de duas letras, nunca por sufixo:** com `endsWith('_'+p)` a pagina `tipster` levaria junto o `ca_custos_tipster`, que e de outra tela, e o estrago so apareceria na proxima aba que o dono abrisse. **UM repaint so no fim** (limpar quatro eixos repintando em cada um mostra o recorte pela metade, e e essa a pintura que o olho pega). O botao acende e apaga pelo `rqb` e pelo `refreshMS`, que sao as DUAS portas por onde filtro muda; pendurar isso em cada setter deixaria o proximo de fora, calado. **GATE: 11 mutacoes, 11 detectadas** (`tests/test_limpar_tudo_filtros.py`), mais 3 de forma. **E MEDIDO NA TELA, nas 10:** escondido com a tela limpa, aceso ao ligar um filtro, e o clique devolvendo periodo E eixos ao estado inicial. **O `[hidden]` precisou de `display:none` explicito no CSS** porque o wrapper e `.filter-group`, que e `display:flex`, e display proprio vence o atributo. 1.231 testes passando.)





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
