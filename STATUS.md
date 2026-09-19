# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-19 (sessao 372: **a aba Contas foi reescrita na v4, a partir de um handoff de design que o Feca trouxe do Claude Design** (`design_handoff_contas_v4`, zip + projeto). A logica de calculo NAO mudou; mudou a ORDEM DA LEITURA. A v1 entregava a resposta como PLANILHA (quatro KPIs neutros, tabela de dez colunas, e o retorno mais importante num cartao no fim da pagina); a v4 encadeia tres granularidades: **tres PAINEIS** pela base inteira (longevidade · volume e margem · retorno sobre aquisicao), **FICHAS por casa** repetindo a mesma ordem, e o **DRILL** por conta. Entrou o que nao existia: histograma de vida em 5 faixas, **ROI liquido**, **custo por dia de vida**, **gauge de multiplo com marca de piso em 1,00x**, composicao do custo, barra de cobertura de preco e o rodape de definicoes. **AS TRES DECISOES DO FECA, e a primeira desarmou um conflito aparente:** (1) o handoff mandava CORTAR `Apostas`, `Turnover bruto` e `ROI bruto` por casa — exatamente os tres que ele pediu na s366 —, mas o proprio handoff abre a porta (*“se voltar, tem de ser apostas por conta”*), entao os tres sobrevivem mudando de UNIDADE: turnover por conta, ROI bruto ao lado do liquido, apostas por conta. Nao havia conflito real. (2) Sobre os R$ 76.600 x R$ 59.600 que eu vinha levantando ha dias: *“pra mim e mais q obvio q e evolucao do custo ao longo do tempo (novas contas). Ninguem fora vc pode conciliar”* — item encerrado como leitura do dono, e a conferencia vira rotina (comparar o card de custo com a tela de Custos), nao frente. (3) **`Inativas`, nunca `Encerradas`**: *“a palavra ja vem da base do Sharpen”*. Vale no segmentado E no estado da conta dentro do drill — um vocabulario so. **TRES DECISOES MINHAS, que o handoff deixou em aberto ou que colidiam com o que ja existe.** **A barra de filtros continua sendo a do APP**, nao o campo `.fv` desenhado no prototipo: o app inteiro usa `.filters`/multiselect, e adotar um segundo estilo so aqui e o item 8 do checklist de UI. Do handoff entra o que e da TELA. **Custo por dia = custo ÷ SOMA das duracoes**, e aqui o README do handoff CONTRADIZ os proprios numeros dele: o texto diz mediana, mas Novibet R$ 9.800 ÷ 15,22 = 644 dias = 28 contas x 23 de media, que e a soma. A soma tambem e a unica regua aditiva. **Default `inativas`** (era `ambas`), porque e a populacao que responde quanto uma conta aguenta. **O HANDOFF USA UMA PALAVRA BANIDA DO PRODUTO, e o gate pegou:** `Investido em contas` — `test_o_vocabulario_proibido_nao_volta_ao_produto` lista as tres proibidas desde a s358. Virou `Custo das contas` / `valor pago na aquisicao`. **E ele reprovou o meu proprio COMENTARIO** que explicava a regra, igual a s364: o gate varre o arquivo inteiro, entao nem para documentar se escreve a palavra. **A REESCRITA APAGOU TRABALHO DA SESSAO VIZINHA, e foram os gates DELA que acusaram:** ao reescrever o `contas.js` inteiro eu levei junto o `${_grupoLimpar('contas')}` e o `LIMPAR_EXTRA.contas` que a s371 tinha acabado de adicionar. `test_limpar_tudo_filtros` reprovou e os dois voltaram — o `LIMPAR_EXTRA` agora volta para uma constante `CN_POP_PADRAO` em vez do literal `ambas`, e **repinta as classes do segmentado**, porque a barra de filtros nao e remontada a cada render e mexer so na variavel deixava o botao aceso mentindo. **Licao: reescrever arquivo inteiro e uma operacao destrutiva quando ha outra sessao aberta — o `git diff` do backup e mais barato que o gate, mas foi o gate que salvou.** **TRES COISAS QUE SO A TELA DEU**, nenhuma visivel a `node --check`, ao `check-tokens` ou a suite: (a) **a aba nascia VAZIA e sem explicacao** — com o default `inativas`, um dono cujas contas estejam todas vivas abre a tela e ve tres paineis zerados; medido no `servidor_demo`, onde as 102 contas sao ativas. Entrou estado vazio que diz a RAZAO e oferece a saida (atalhos para as outras populacoes), que o handoff ja listava como pendente; (b) **classe escrita com DOIS nomes** — o botao do vazio saiu `cn-vazio__btn` no JS e `cn-empty__btn` no CSS, entao ele existia na tela com a cara nativa do navegador no meio de uma superficie estilizada. Virou gate de FORMA (`test_toda_classe_cn_usada_no_js_existe_no_css`, 52 classes conferidas, provado por mutacao); (c) concordancia — *“Nenhuma conta inativas”*, porque o rotulo do segmentado e plural por natureza e nao serve de adjetivo. **GATES: 12 de 12 mutacoes detectadas** no `contas_vida.mjs`, que ganhou os blocos 10-13 (ROI liquido sai do denominador ELEGIVEL e nao do turnover inteiro · custo/dia pela SOMA e nao pela mediana · histograma com faixas inclusivas nas duas pontas · o agregado dos paineis sai das MESMAS contas que as fichas). `test_contas_vida.py` em 10 casos. **Suite 1.231 passed**, `check-tokens` e `check_docs` verdes, Escada de Tinta varrida nos tres criterios. **Medido no Chrome dentro do iframe**: 3 paineis, histograma de 5 faixas, cobertura de 3 segmentos, drill abrindo e ordenando sem fechar, `Limpar tudo` voltando a Populacao ao default, e **transbordo 0 em 1366/1440/1600/1920/2560**. **PENDENTE:** fechar o `BACKLOG 1.13` com a leitura do Feca (o arquivo estava sendo editado pela sessao vizinha e eu nao encostei), e a conferencia do card `Custo das contas` contra a tela de Custos, na base real. `?v=` de contas/components em 8/60.)

_Anterior: 2026-09-18 (sessao 374: **duas sugestoes do tester Joao, e a primeira ja esta no ar: o switch R$ / u da tela Tipsters passou a valer para a TELA inteira.** O “u” alcancava o KPI do topo e a coluna P/L do Comparativo; os **cards ficavam em R$**, porque eles so sabiam renderizar u pelo `MODO_PUBLICO`, que nao existe no dashboard privado. Um card dizendo `− R$ 1.520,31` logo abaixo de um KPI dizendo `−28,38u`: cada metade certa, a razao entre as duas impossivel de ler. **Agora trocam JUNTOS** o P/L, o Turnover, a Stake Media e a **sparkline** de cada card, o KPI `Turnover Total` e as colunas `Turnover` e `Stake media` do Comparativo Geral. **A REGUA E UMA SO** (`_tipsterUnidades`, `app.js`), e ela converte **por linha, pela unidade vigente na DATA daquela linha**: a escada muda no tempo, e dividir o total por uma unidade so misturaria eras. **Linha que nao da para converter (sem escada E sem stake) fica FORA das somas**, nunca entra como zero, que e a familia do “zero se disfarca de conta feita”. **ROI, Win Rate e Odd Media NAO entram, de proposito:** sao adimensionais, e converte-los seria inventar uma segunda regua para o mesmo numero. **A ORDENACAO passou a seguir o que esta na tela** (em u, P/L e Turnover trocam de ordem entre tipsters, porque cada um tem sua unidade). **E a mascara de agregado em u virou UMA**: o `fmtRU` nasceu do trecho que so existia dentro do modo publico, e o modo publico agora aponta para ele em vez de carregar copia propria. **GATE: 13 mutacoes, 13 detectadas** (`tests/test_tipster_visao_u.py` + `tests/js/tipster_visao_u.mjs`), com a ancora conferida como **UNICA** antes de mutar: os tres cards (esporte, casa, tipster) nasceram copiados um do outro, e mutacao que acerta o alvo errado passa verde com razao. **E foi MEDIDO NA TELA, nao so em teste:** headless contra o `servidor_demo`, 23 cards antes e depois da troca, **nenhum `R$` sobrando em modo u** nos cards, nos 4 KPIs e na linha do Comparativo, nenhum NaN, console limpo e o switch reversivel. 1.216 testes passando, `check-tokens` verde. **FICOU DE FORA, declarado no cabecalho do gate:** o drill-down do tipster (o modal que abre ao clicar no card) segue em R$, porque a curva e o Monte Carlo rodam sobre a serie em reais; converte-lo e decisao do Feca, nao consequencia desta. **A SEGUNDA SUGESTAO TAMBEM ENTROU, e com escopo maior do que o pedido** (decisao do Feca: *“verificar onde nao existe o limpar tudo e inserir tbm, nao so onde ele pediu”*): o **“Limpar tudo”** existia so na Base Completa, e quem recortava a Visao Geral por tres eixos desfazia um por um. Ele virou **peca da BARRA** (`_grupoLimpar`, em `filters.js`), entao as **10 telas** que montam barra o ganharam juntas: Visao Geral, Resultados, Esportes, Bookies, Tipsters, Fornecedores, Metricas, Em Aberto, Custos e Painel de Contas. Copiar o botao tela a tela criaria N botoes que divergem no primeiro ajuste (a licao da s317). **A Base Completa segue com o dela** na faixa de filtros ativos: dois botoes do mesmo papel na mesma tela e o sintoma de “fora do padrao” que o item 8 do `/nova-ui` manda evitar. **So aparece com filtro LIGADO**, como la: botao morto em tela limpa e ruido. **TRES DECISOES que o botao obrigou a tomar. (1) LIMPAR E VOLTAR AO PADRAO DA TELA, nao ao vazio:** a tela de Custos nasce em **MTD** de proposito (e de fechamento mensal, e “Tudo” nao fecha mes nenhum), entao ali o botao devolve o MES, e o proprio MTD **nao conta** como filtro ligado. **(2) O filtro LOCAL da tela entra na conta:** o seg de Populacao do Painel de Contas nao vive no `MSS`, e sem o registro (`LIMPAR_EXTRA`) o botao limparia metade da tela dizendo “Limpar tudo”. **(3) Eixo se casa por PREFIXO de duas letras, nunca por sufixo:** com `endsWith('_'+p)` a pagina `tipster` levaria junto o `ca_custos_tipster`, que e de outra tela, e o estrago so apareceria na proxima aba que o dono abrisse. **UM repaint so no fim** (limpar quatro eixos repintando em cada um mostra o recorte pela metade, e e essa a pintura que o olho pega). O botao acende e apaga pelo `rqb` e pelo `refreshMS`, que sao as DUAS portas por onde filtro muda; pendurar isso em cada setter deixaria o proximo de fora, calado. **GATE: 11 mutacoes, 11 detectadas** (`tests/test_limpar_tudo_filtros.py`), mais 3 de forma. **E MEDIDO NA TELA, nas 10:** escondido com a tela limpa, aceso ao ligar um filtro, e o clique devolvendo periodo E eixos ao estado inicial. **O `[hidden]` precisou de `display:none` explicito no CSS** porque o wrapper e `.filter-group`, que e `display:flex`, e display proprio vence o atributo. 1.231 testes passando.)

_Anterior: 2026-09-17 (sessao 373: **a base de setembro do Ewanderson1 subiu de novo, e desta vez a janela estava LIMPA — medido, nao suposto.** 1.104 apostas de 01 a 14/09, da planilha original dele. **O export novo traz 1.104 linhas para o MESMO periodo em que o de 13/09 trazia 784:** o anterior estava incompleto, e a fonte e a mesma. **A MEDICAO QUE AUTORIZOU A CARGA:** a base dele tinha **179 bilhetes, TODOS `origem='extracao'`, de 15/09 a 20/09**, e o CSV para em 14/09 — **sobreposicao zero**. O risco que derrubou a carga da s357 (import sem ID de bilhete + recaptura trazendo a mesma aposta COM codigo, que nao dedupa e duplica) simplesmente nao existe nesta janela; ele volta no dia em que ele capturar casa de historico longo (a Betano varre 3 anos por desenho), e a regua para isso e o `main._CORTE_HISTORICO`, nunca apagar do banco. **TRES COISAS MUDARAM DESDE SETEMBRO E O SCRIPT NAO SABIA, todas medidas contra o banco antes de escrever uma linha. (1) CONTA:** o script criava `Padrao` por casa, e ele hoje tem **conta com nome real por casa** (`Ykaro` na Betano, `Woshington` na Bet365, `Joao` na SportingBet), cobrindo 1.030 das 1.104 linhas. Decisao do Feca: conta **`Planilha`**, uma por casa, ao lado das reais. O CSV e tracker de TIPSTER e nao diz de quem era a conta em setembro — casar o historico com a conta capturada seria palpite gravado como fato; e como `parceiro` entra no hash da assinatura, a separacao tambem e dedup. **(2) TIPSTER:** o tracker exporta `Padovan` e na base dele o mesmo tipster e **`Padovan All Sports`**, no cadastro E nos 65 bilhetes ja capturados — os outros quatro nomes batem caractere a caractere. Sem o de-para, a carteira do Padovan nasceria partida em dois tipsters que a tela le como pessoas diferentes, e o filtro de tipster recorta por NOME. **(3) CASA:** `Rei do Pitaco` **RESSUSCITOU** — 4 bilhetes com codigo da casa, sob conta criada a mao, contra os 520 de `Pitaco` que a s270 unificou. Refundida ANTES do import (`unificar_casas.py --somente`), 4 assinaturas recalculadas e mais 11 linhas em `parceiros`/`casas_meta`/`correcoes`/`uso_tokens`; trocar a casa sem recalcular deixaria o hash velho e a proxima captura duplicaria o historico. `King Panda` entrou no mapa como **`KingPanda`** (447 bilhetes no banco), que title-casear mutilaria. **DOIS DEFEITOS DO PROPRIO SCRIPT, que a carga anterior nao podia ter:** ele ancorava o `criado_em` em `NOW()` — certo com a base vazia, e hoje jogaria as 1.104 linhas de 01 a 14/09 para o **TOPO do feed**, acima das capturadas de 15 a 20/09, com a data certa na grade e o feed de cabeca para baixo, sem erro nenhum; e a conferencia final comparava o **total do dono** com as linhas do CSV, o que acusaria colisao de assinatura que nao houve. **O DINHEIRO AUDITOU O ROTULO e pegou 5 linhas** (2 `lost` cujo RESULT bate com a formula de vitoria, 3 `void` com perda total), com **0 linhas divergentes** no confronto das cinco formulas do `calcular_pl` contra o P/L que a planilha ja trazia pronto. 4 odds `0.00` entram **VAZIAS**, nunca zero. **CONFERIDO NO BANCO depois de gravar:** 1.104 import (01→14/09) + 179 captura (15→20/09), `criado_em` do import terminando 1s antes do primeiro capturado, W 346 · L 756 · V 2, **0 assinaturas duplicadas**, 0 odd zero, 5 tipsters e nenhum `Padovan` solto. **E A STAKE VIROU REAIS NA MESMA SESSAO, numa 2a carga:** o Feca lembrou, depois de gravar, que o tracker exporta em UNIDADES e que a unidade dele e **R$ 50,00**. **A conversao NAO entrou por UPDATE, e a razao e a dedup:** `stake` esta no hash da assinatura, entao trocar o valor por fora deixaria as 1.104 linhas com o hash velho, e a proxima captura que alcancasse a janela nao deduparia. O import e idempotente — apaga o que ele mesmo escreveu e regrava —, entao stake e assinatura saem certas no mesmo gesto. **O NUMERO NAO FOI ACEITO DE PALAVRA:** as stakes que a captura trouxe das casas, ja em R$, sao 12,50 · 25,00 · 37,50 · 50,00 · 100,00, ou seja 0,25u · 0,5u · 0,75u · 1u · 2u — os dois lados da mesma base concordando. **A AUDITORIA FICOU EM UNIDADES de proposito:** o `RESULT` vem em unidades e a `TOL` do confronto e centavo de unidade; converter antes multiplicaria a tolerancia por 50 e deixaria passar erro de ate R$ 1,00 por linha. **E o dono JA TINHA EDITADO uma linha na grade** (Tivo, 14/09, stake `2,33` → `0.25`, `correcoes` 44752, 18:42 BRT): apagar e regravar levaria a edicao junto, **sem erro e sem aviso**. Ela entrou no script como `_AJUSTES_STAKE`, por numero de linha do CSV, vale como unidades (decisao do Feca, logo R$ 12,50) e **sobrevive a qualquer recarga futura** — correcao humana manda sobre a fonte, e o confronto do relatorio continua usando a stake do CSV porque o que se audita ali e a traducao, nao a decisao do dono. **CONFERIDO POR SQL INDEPENDENTE do script:** turnover **R$ 38.995,00**, P/L **R$ +8.133,62**, ROI 20,86%, stakes de R$ 5,00 a R$ 200,00, 0 assinaturas duplicadas. **PENDENTE no [`BACKLOG.md`](BACKLOG.md) §1.16:** nada impede recriar a grafia velha de uma casa ja unificada — o seletor do app so conhece `Pitaco`, mas o "+Nova conta" aceita nome verbatim, e foi por ai que a s270 voltou a ter residuo. **E O SEGUNDO ASSUNTO DO DIA FOI A DATA DA BET365 — dois defeitos DIFERENTES, e o do print nao era o que o Feca descreveu.** O print (dois bilhetes MULTIPLA datados de 18/09 para jogos de 12 e 13) apontava para outra coisa. **MEDIDO:** no lote capturado hoje as 10:42, **13 dos 16 bilhetes da Bet365 nasceram com a data de HOJE**, e os 3 certos eram apostas SIMPLES. Os 13 tem um unico `[A v B]` na descricao inteira: sao **Criar Aposta / bet builder de MESMO JOGO**, que a casa manda com `TP=00010101000000` — sem kickoff. Sem kickoff o bloco saia **sem linha de data** e o backend datava com a data de referencia (= hoje), o que **so acerta quem captura no mesmo dia** — e a base dele esta sendo formada por captura de HISTORICO. Ele ja vinha corrigindo um a um a mao, 12 correcoes de `data` em 13 minutos. **A SAIDA NAO E ESTIMAR, E OUTRO CAMPO REAL:** a casa PUBLICA a colocacao em dois lugares, e **na fixture provei que sao o mesmo instante** — `DA` no cabecalho do confirmation (`20260722233620`) e `TP` no `01` do summary (`20260722233620000`). O formatador ignorava os dois. **O ROTULO DIZ A PROCEDENCIA:** sai `Data (colocacao):`, nunca `Data (evento):` — quem le o bloco e a IA (o tradutor deterministico ainda e sombra), e o backend casa a chave por PREFIXO (`app/tradutor.py`), entao a linha serve aos dois caminhos. **E o rotulo nem e novo: 13 outras casas ja o emitem no mesmo `content.js`** — a Bet365 era a excecao. **O gate ANTIGO travava exatamente esta mudanca** ("colocacao nunca — mudanca de REGRA, precisa de aprovacao humana"): a aprovacao veio do Feca, e o bloco 5 do caso passou a travar a decisao NOVA, com o fuso conferido (23:36 UK em BST = 19:36 BR do dia 22). **4 mutacoes, 4 detectadas** — colocacao removida · rotulo mentindo a procedencia · `else` virando `if` solto (que faria a colocacao competir com o kickoff em TODO bilhete que tenha os dois, erro invisivel porque as duas datas sao plausiveis) · guarda `y < 2000` removida. **A 5a e INOCUA e esta registrada como tal:** trocar `t.da || t.tp` por `t.tp || t.da` nao muda nada, porque os dois campos sao o mesmo instante. Harness verde (29 casos, 471 bilhetes), 1.197 testes passando, `manifest` em **0.7.15**. **O SEGUNDO DEFEITO — o que o Feca DESCREVEU — nao foi consertado, e a razao esta medida:** multipla com pernas em dias diferentes que a casa liquida quando a 1a perna perde fica com a data do jogo mais tarde e nasce **liquidada no futuro** (**112 na Bet365, 5 donos, 90 dias**; e nao e so ela — Pitaco 25, Pinnacle 13, Superbet 13, SportingBet 12, Estrela Bet 11). **Varri TODOS os campos dos dois endpoints: a bet365 nao publica instante de liquidacao** — so colocacao e kickoff por perna. Entao "respeitar a data de liquidacao" nao e implementavel, e derivar seria a mesma estimativa que a s339 removeu. A saida proposta, que preserva o principio sem inventar: em bilhete ja liquidado, a perna que manda e a mais recente **que ja comecou**. Isso e `MASTER_OUTPUT §4`, vale para TODAS as casas, e ficou como decisao no [`BACKLOG.md`](BACKLOG.md) §1.17. **PENDENTE:** o passivo no banco nao foi reparado (decisao do Feca — consertar a origem primeiro, senao repara-se de novo na captura seguinte), o `test_changelog` esta **vermelho de proposito** ate a nota da 0.7.15 existir, e **nada disto rodou no navegador com a extensao carregada**.)




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
