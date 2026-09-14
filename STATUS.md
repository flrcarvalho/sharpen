# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-13 (sessao 357: **a base do `Ewanderson1` entrou, e o que auditou a traducao foi o DINHEIRO que o proprio arquivo ja trazia pronto.** Pedido do Feca: *"Subir base do ewanferreira962385@gmail.com pra ele comecar a usar o sharpen. Novo cadastro"*. **O DONO FOI CONFERIDO NA TABELA, nao deduzido:** username `Ewanderson1`, e-mail conferindo, `status='ativo'`, hash de 60 chars, criado em 13/09 16:24 UTC por autosservico (Fase 2) e aprovado na mesma sessao. **Nao existe env var nem linha em `app/auth.py` para esta conta.** Base ZERADA antes (0 bilhetes, 0 contas). **A FONTE:** `01 a 11.csv`, tracker de SEGUIDOR de tipster (nao de casa), 784 apostas de 01/09 a 14/09 — o nome do arquivo diz "01 a 11" e o conteudo vai ate o dia 14; a data mandou. 5 tipsters, 22 casas, 461 simples e 323 multiplas. **O ACHADO QUE VALEU A SESSAO: a coluna `RESULT` e o P/L em unidades, ja calculado, e por isso da para ler as cinco formulas do `calcular_pl` AO CONTRARIO contra o rotulo do arquivo.** 230 `won` batem exatos com `stake x (odd-1)` (tolerancia 0,02), o que ja prova que nao ha meia-vitoria escondida. **E cinco linhas foram pegas mentindo:** 2 `lost` com RESULT POSITIVO que bate com a formula de VITORIA (L476 e L779) e 3 `void` com RESULT = -stake (L483, L704, L705). Void devolve o stake e da P/L 0; retorno 0 e `L`. O dinheiro mandou nas cinco, e elas saem NOMEADAS no relatorio do ensaio: correcao automatica que ninguem ve e correcao que ninguem audita. **Zero nao e ausencia:** 3 linhas trazem `ODD 0.00` e entram com odd VAZIA, nunca 0 — todas sao `L`, onde o P/L nao depende da odd, e desde a s259 a odd so e exigida em `W`/`HW`. Odd alta nao e defeito: a maior multipla e 16.946,72, com o RESULT batendo. **CASA: grafia MEDIDA no banco, nunca a do arquivo.** Nove de-paras (`TivoBet`->`Tivo`, `BetNacional`->`Betnacional`, `Rei do Pitaco`->`Pitaco`, `Esportiva Bet`->`Esportiva`, `BetEsporte`->`BETesporte`, `Onabet`->`OnaBet`, `Bateu Bet`->`Bateu`, `Esporte da Sorte`->`Esportes da Sorte`, `Outras Casas`->`Outra`) e **duas casas novas que entram VERBATIM** (`LottoLand` 16, `Esporte 365` 11). Sem o mapa seriam 9 casas paralelas. **DOIS DEFEITOS MEUS, os dois pegos pela AMOSTRA do ensaio e nenhum por leitura:** (1) `Jardas por recepcao` caia em Player Props e `Jardas corridas` em Jardas, dois nomes para a mesma coisa, porque a regra de props vinha antes; (2) `Tentativas de Corrida` do NFL caia em `Corridas`, que e categoria de BASEBALL (`MASTER_APOSTAS §6`: corridas e RBIs) — hoje `Corridas` so vale com esporte `Baseball` e o resto cai em Player Props. Quatro rotulos foram decididos por PRECEDENTE MEDIDO na base, nao por palpite: tiros de meta e laterais -> `Team Props` (17 e 34 linhas ja assim), defesas -> `Player Props` (89), strikeouts/sacks/top 3 -> `Player Props`. **DESCRICAO E COPIA, e onde a fonte cala, ela DIZ que calou:** 271 multiplas chegam com `GAME=N/A` e `BET=Multipla` (o tracker nao exporta as pernas) e 7 simples nao tem nem mercado nem confronto — estas ficam `Sem detalhe no export`, porque chamar de `Multipla` uma simples seria inventar o que o arquivo nao tem. Nenhum acento foi reposto: o tracker exportou `Cartoes`/`Finalizacoes` e "corrigir" isso e escrever texto que a fonte nao tem. **QUATRO DECISOES DO FECA, com os numeros na mesa:** stake em UNIDADES verbatim (converter para R$ exigiria o tamanho da unidade, que o arquivo nao traz); uma conta `Padrao` por casa (22 linhas no Painel, cada uma com custo proprio); `Padovan` e `Padovan NBA/NFL` SEPARADOS, porque o P/L dos dois diverge de verdade (+59,19u contra -10,13u) e fundir apagaria uma medicao que ja existe; e o dinheiro mandando sobre o rotulo. **RESULTADO, conferido no banco DEPOIS de gravar:** 784 bilhetes, 22 casas, 22 contas, `W` 232 / `L` 545 / `V` 2 / 5 abertas, 0 descricao vazia, 0 odd igual a zero. **P/L do BANCO +46,04u** em 552,98u de turnover (ROI 8,33%), contra os +46,13u que o arquivo soma: a diferenca de 0,09u e arredondamento do tracker (P/L ao centavo de unidade, odd com 2 casas) e **nenhuma linha estoura a tolerancia** — se estourasse, ela apareceria nomeada. **RISCO DECLARADO, e e do Feca:** o CSV nao tem ID de bilhete, entao a assinatura e de CONTEUDO; se ele instalar a extensao e capturar uma casa que ja esta aqui, as apostas voltam COM codigo e **assinatura por ID nunca colide com assinatura por conteudo — nao deduplica, duplica**. Sao 383 linhas nos ultimos 7 dias e 32 nos ultimos 2. Foi para o `BACKLOG`. **ONDE ESTA:** `scripts/import_ewanderson_csv.py`, com ENSAIO como padrao, o `dono` reconferido em `usuarios` dentro da transacao, `DELETE` por `origem='import'` (idempotente, nao acumula) e `criado_em` ancorado na data da aposta, para o feed sair cronologico. **FORA DO ESCOPO, de proposito:** as gemeas `Esporte Da Sorte` (102) e `Esportes da Sorte` (87) seguem duplicadas na base; unificar exige recalcular assinatura (`scripts/unificar_casas.py`) e e trabalho a parte. **ACHADO LATERAL:** o `check_docs.py` ja vinha com 2 FAIL herdados — `CLAUDE.md` em 67,4 KB (teto 65) e 223 copias de STATUS/HISTORICO no `Backups/` (28,7 MB) —, nenhum deles criado aqui. **E o caso 8 aconteceu de novo, ao contrario:** o `STATUS.md` desta sessao foi levado pelo commit `4fee628` da sessao vizinha, que estava aberta ao mesmo tempo. O conteudo esta integro no repo e **historico ja pushado nao se reescreve** — fica o registro, como manda o invariante #8. **E A SESSAO NAO FECHOU AI: o Feca mandou o print do notebook do usuario novo e a tela estava QUEBRADA, nao "apertada".** *"ta horrivel... melhorou com ele diminuindo o zoom... UX pessima"*. **MEDIDO headless contra o `servidor_demo`, e o numero e feio:** num notebook de **1366 a zoom 100%**, que e o padrao, `#partner-page` mede **1050x0**, `.grade-section` **1050x2** e `#caixaBox` **1050x2 carregando 333px de conteudo dentro**. A zoom 125% e 150% o mesmo; a **80%** (viewport 1707) tudo volta, ou seja o "melhorou diminuindo o zoom" e a assinatura do defeito, nao a solucao. **O ponto de virada e 1444px de JANELA:** a casca come 264px de sidebar (`SHELL_SPEC §1`), o iframe cai sob 1180 e entra o `@media` que empilha. **A CAUSA:** o empilhado empilhava dentro de uma altura FIXA (`.workfull` e `flex:1` com `min-height:0`), com tres blocos disputando ~398px. Com espaco livre negativo o grid comprime a linha ate o **min-content**, e o min-content de quem tem `overflow:hidden` e ZERO. Dai o `grid-template-rows` resolver `396px 2px 0px`, sem scrollbar e sem erro. Estava no `BACKLOG §3.8` desde a s346, medido e esperando decisao; o que hoje acrescenta e que **a Caixa Inteligente colapsa junto** (o item so citava a grade) e que o caso e o de qualquer notebook de 1366 sem zoom. **O CONSERTO E FLUXO, NAO GRID:** no empilhado o `.workfull` vira flex column e quem rola e ele. **DUAS TENTATIVAS ERRADAS ANTES, as duas pegas por medicao e nenhuma por leitura:** (1) com linhas `auto` a `.colmain` continuava comprimida e os filhos, ja com altura propria, VAZAVAM para fora dela, e o RAIO-X nascia **por cima** da Caixa (rail em 372px, Caixa de 353 a 688); (2) `flex: none` nos filhos sem por na `.colmain` deixou a coluna encolher para **266px com 1.148px de conteudo**, e o vazamento voltou igual. Quem tem altura propria nao pode ter shrink, e isso vale para o container tambem. **Os KPIs junto:** `repeat(4,1fr)` fixo virou `auto-fit` com piso de 145px e **teto de 4 colunas** pelo `max()`. Em 1445px os tiles caiam a 116px com **2px de folga** em tres deles, e o `auto-fit` sozinho subia para 5 colunas em 1920, deixando dois buracos na 2a linha. **RESULTADO MEDIDO em 8 larguras** (1920 a 910): zero overflow horizontal, zero tile estourando ou apertado, e em 1366 a lista de apostas foi de **0 para 538px** e a Caixa de **2 para 335px**. Desktop intacto (4 colunas, grade 1566x313 em 1920). A ordem no empilhado passou a ser a do DOM: tiles e captura, Caixa, GRADE, e so entao o RAIO-X. **FICA ABERTO, e e decisao do Feca:** em tela estreita a Caixa (335px) ainda fica ENTRE a captura e a grade; inverter as duas com `order` poe o trabalho antes do painel de conferencia, e e uma linha.)

_Anterior: 2026-09-13 (sessao 356: **duas linhas paradas em AGUARDANDO RESULTADO na conta do Marlon eram DUAS causas diferentes, e a segunda so apareceu porque duas tabelas que ninguem usava para isso guardavam o codigo que o robo REALMENTE mandou.** O relato do Feca: *"fiz mtas extracoes agora, pois a conta de 1 aposta em aberto e eu nao conseguia resolver essas duas do print... vi q elas sao duplicadas, ou seja, temos o resultado delas em outra linha... isso e erro crasso"*. **O DIAGNOSTICO:** `#265501` tinha codigo `TQ8770485441W` e `#265341`, resolvida `L`, tinha `TQ8770485441I` — a mesma raiz, a ultima letra trocada. `#265429` nasceu **sem codigo nenhum**, copia do bloco de `#265405`. **A PROVA NAO FOI DEDUCAO:** `sombra_rotulos` so grava a linha quando o codigo da IA existe no texto do robo (`parear_sombra`), e `bloco_visto` grava TODO codigo do texto, tenha a IA acertado ou nao. `…I` aparece seis vezes; `…W`, **zero**. Idem `JQ3249290491F` contra `JQ3249290491I`. **A CAUSA RAIZ: o `codigo_bilhete` e a ultima coluna de IDENTIDADE sem extracao deterministica** — quem a escreve e a IA, copiando o `[Codigo: …]`, e um caractere trocado nao e erro de digitacao, e um bilhete NOVO para a assinatura. Mesma familia do `codigo_ocr` (s338), mas com o flag em FALSE: o lote e de texto, entao nenhuma trava atual olhava para ele. **TAXA REAL: 0,21%** (20 em 9.475 desde 09/09, com `bloco_visto` como gabarito) — e **nao 3,3%**, que foi a primeira medicao, inflada 20x porque a sombra so enxerga o que a IA acertou. **O ACHADO QUE MUDOU O CONSERTO: 21 dos 22 pares da bet365 nasceram no MESMO SEGUNDO.** Nao era o codigo mudando entre capturas: com o codigo falso na coluna 11, `conferir_cobertura` julga o bilhete verdadeiro faltante, **repesca**, e a linha repescada entra ao lado da inventada. Por isso o `_corrigir_codigos_fantasma` roda **antes** da cobertura; depois dela seria tarde. **A bet365 tem so TRES letras finais reais** (`I`/`W`/`F`) e as contas reais usam exatamente essas tres; as outras 23, quase uniformes, vinham todas da conta `realtrial`, cujo export anonimizado randomiza o codigo — artefato da demo contaminando a medicao da base real. **O SEGUNDO DEFEITO era de logica:** o descarte do `_reconciliar_orfas` so agia `if not livres`, e num lote grande quase sempre sobra um codigo livre; a orfa era fiel a um bloco que **ja tinha linha propria** (logo nao havia o que adotar) e atravessou as duas portas. Ganhou um segundo criterio, que a julga por si. **A VARREDURA DA BASE INTEIRA, e o que ela ISENTOU:** 170.306 linhas, 1.007 grupos de conteudo identico, 1.084 excedentes — e **a maior parte nao era defeito**. 412 sao codigos distintos vindos do robo (166 grupos na mesma extracao: gente apostando a mesma coisa duas vezes, e a regua de dedup esta CERTA em mante-las), 191 sao repeticao da planilha de origem, 406 sao da conta demo e 152 tem descricao generica demais. **Defeito de verdade, pela regua do script (a reproduzivel): 90 grupos fora da conta demo** — 88 que ele remove sozinho (−R$ 3.810,22 saindo do total) mais os 2 que ele se recusa a decidir. Com a demo dentro sao 289 linhas e −R$ 5.216,80. A classificacao exploratoria tinha dito 126 porque somava a demo na familia das orfas; **o numero que vale e o que o script mede**, porque e o que roda de novo amanha. A esmagadora maioria duplica com o MESMO resultado (P/L em dobro); 2 grupos divergem e 3 deixaram linha aberta. `archived` nao protege nada disso: ele so controla a grade da extracao, nao o feed, os KPIs nem a Caixa. **Abertas fantasma na base inteira: 4** — as duas do print e duas da Betano do Tonelada. Das 1.274 abertas, 129 tem gemea por conta/data/stake/odd e so essas 4 tem a descricao batendo: **a regua frouxa acusaria 32x mais do que existe.** **O QUE SUBIU:** `_corrigir_codigos_fantasma` (no-op em lote com IMAGEM, onde o codigo vem do card), o segundo criterio de descarte de orfa, e `scripts/reparar_duplicatas_codigo_fantasma.py` com ensaio por padrao, lixeira e recusa de decidir onde o RESULTADO diverge. **GATE: `tests/test_codigo_fantasma.py`, 14 provas e 8 de 8 mutacoes detectadas.** Suite: 996 passed / 36 skipped (982 sem o arquivo novo). **PENDENTE E E DO FECA:** (1) rodar o `--aplicar` (o modo automatico desta sessao barra escrita em producao) — 88 grupos, 88 linhas, −R$ 3.810,22 saindo do total; (2) os **2 grupos com resultado divergente**, que o script se recusa a decidir sozinho: o Mbappe 09/07 (`#48767` W contra `#48771` L, as duas sem codigo, nada no sistema desempata) e o Nathan Potter 01/07 na Betfair (`#45567` W sem codigo contra `#47568` L **com** codigo do robo, onde a fonte deterministica manda mas a decisao de trocar um W por um L e do dono); (3) ~~a conta `realtrial`~~ **DECIDIDO: fica como esta** (*"realtrial n tem importancia algumo"*) — mas a licao fica, porque foi o codigo randomizado da demo que contaminou a primeira medicao da bet365: **dado sintetico na mesma tabela do dado real entra em toda medicao que ninguem filtrou por `dono`.** **ACHADO LATERAL:** `sombra_rotulos` e `bloco_visto` nasceram para o tradutor e para a barreira de recaptura, e acabam de virar o **gabarito de procedencia do codigo** — e a diferenca entre as duas foi exatamente o que separou 3,3% de 0,21%.)

_Anterior: 2026-09-13 (sessao 355: **a base do SharkTrack entrou DENTRO da base viva do Diogo, e o trabalho de verdade foi o NOME.** O pedido do Feca: *"preciso importar a base do diogo dentro da base q ele vem utilizando... precisa ser feito um trabalho com o nome das casas e principalmente com o nome dos tipsters dele"*, com o exemplo `araujo` / `ARAUJO` / `Araujo` sendo tudo o mesmo. **O ESTADO MEDIDO ANTES:** 891 bilhetes vivos, todos `origem='extracao'` do SharpenUp, de 07/09 a 13/09, com o tipster em MINUSCULO; o export do SharkTrack traz 6.410 linhas de 24/06 a 06/09, em duas caixas. **Zero sobreposicao de periodo: o import para exatamente onde a captura comeca. TRES DECISOES DO FECA:** Title Case em tudo (renomeando tambem o que ja estava no banco), nenhum merge semantico (`pei` segue separado de `peixe`) e conta `SharkTrack` para toda linha, porque o export nao tem coluna de titular. **O ACHADO QUE JUSTIFICOU A SESSAO INTEIRA: o `_CASA_MAP` do importador criaria QUATRO casas paralelas.** Ele foi escrito na s255 sem medir, e `casa` e TEXTO em 7 tabelas: `Rei do Pitaco` nao existe em lugar nenhum da base (0 linhas) e levaria 48 bilhetes; `VixeBet` tambem nao (o Diogo ja tem 8 em `Vixebet`); `Sportingbet` idem, contra `SportingBet` (467). Faltavam `bet mgm` (`BetMGM`, 864), `ice bet` (`icebet`, 76, e a grafia MINUSCULA e a que existe) e `bateubet` (`Bateu`, 136 contra 2). **Cada linha do mapa agora carrega a contagem que a autorizou.** **O NOME DO TIPSTER VIVE EM TRES LUGARES, e o terceiro e o que se esquece:** `bilhetes.tipster`, `tipsters.nome` (o que o matcher le) e as **CHAVES** de `custo_store.custo_tipster` / `custo_tipster_meta`. Renomear os dois primeiros e deixar o terceiro para tras e o caso *tipster cobrado e ineditavel* do `CLAUDE.md`. As 22 chaves do Diogo estavam todas sem valor lancado, entao o rename foi barato; a proxima base nao tera essa sorte. **UM MODULO, NAO DUAS FUNCOES:** `scripts/tipster_nomes.py` e a fonte unica que o import e o rename consultam. Dois normalizadores separados concordam hoje e divergem no primeiro acento, e ai o tipster nasce partido de novo (mesma razao de o `parseNum` do dashboard ser um so). A regra de desempate esta escrita e provada pelo dado: dentro do grupo (casefold + sem acento) **vence a variante ACENTUADA mais frequente**, porque o acento e informacao que a digitacao sem acento perdeu, e o contrario nunca e verdade. Hoje nao ha nenhum caso de acento divergente na base do Diogo; a regra existe para o `Araujo` do proximo export. **O de-para ficou num JSON versionado** (`scripts/tipsters_diogo_map.json`, 79 grafias -> 45 tipsters), que e onde um merge de APELIDO entra depois sem tocar em codigo. Merge de apelido nunca e inferido: dois apelidos parecidos podem ser duas pessoas. **DEFEITO DO IMPORTADOR QUE SO APARECE AGORA:** ele ancorava `criado_em` em `NOW()`, escrito quando a base do Diogo estava vazia. Com captura ao vivo rodando, isso jogaria as 6.410 linhas historicas para o TOPO do feed, acima dos bilhetes de hoje. Passou a ancorar na data da aposta, com a posicao dentro do dia como desempate. **DOIS ESPORTES FORA DO VOCABULARIO, corrigidos junto por serem o mesmo problema:** `Counter-Strike 2` (5 linhas) virou `E-Sports` como manda o `MASTER_ESPORTES §7`; `Automobilismo` (1 linha) **NAO** virou F1, porque o bilhete e `CBPS Azul - Lagomar` / `Total de Pontos` / `Liga de Ascenso`, ou seja o rotulo mente na origem, e traduzir rotulo que mente e inventar o dado. Ele cai em `Outro`. **RESULTADO, conferido no banco DEPOIS de gravar:** 7.301 bilhetes (6.410 import + 891 captura), turnover R$ 1.855.101,42, P/L +R$ 158.728,54, ROI 8,56%, identicos ao ensaio; 45 grafias de tipster e **nenhuma comecando em minuscula**; 26 casas e nenhuma paralela; o topo do feed continua sendo a captura de hoje. Residuo: 9 linhas em `Outros` (0,14%), 63 em esporte `Outro` (1%), 1 sem odd. A Caixa do Diogo esta desligada (0 movimentos), entao nada de `abertas_corte` foi tocado. **FORA DO ESCOPO, de proposito:** as contas reais do Diogo seguem intactas, e a conta `SharkTrack` (25 casas) nao puxa o custo de aquisicao delas para 24/06, que e o que aconteceria se o historico fosse atribuido as contas verdadeiras. **AS DUAS PENDENCIAS FECHARAM NA PROPRIA SESSAO, as duas com o Feca decidindo:** (1) **`Pei` e `Peixe` sao DUAS PESSOAS** (*"Pei e Pei mesmo. Tem o Pei, tem o Peixe"*), entao nao ha merge de apelido a fazer. Isso e a prova de que semelhanca de grafia nunca autoriza merge: um normalizador ingenuo juntaria os dois e apagaria um tipster inteiro, em silencio. Caixa e acento o modulo une sozinho; apelido so por declaracao humana, e o lugar dela e o JSON. (2) **A CAPTURA VIRA A FONTE UNICA** (*"ele vai importar so no sharpen agora"*): o SharkTrack deixa de ser exportado e o que esta no banco como `origem='import'` passa a ser **historico congelado**, exatamente o desfecho que a regra *Planilha e bot escrevem na MESMA serie de codigo* ja prescrevia. Com isso some o unico risco estrutural que sobrava, o de dois escritores para a mesma aposta a partir de 07/09, que **nao teriam como deduplicar entre si** (contas diferentes: `SharkTrack` de um lado, a conta real do outro). `teste`, `teste bask`, `fix`, `dark`, `dynamite` e `vini` ficam na base verbatim, sem decisao, e nenhum deles atrapalha nada.)






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
