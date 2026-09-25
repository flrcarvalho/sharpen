# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-24 (sessao 387: **auditoria independente do "Resolver apostas abertas" antes de tocar no token — e ela achou DOIS defeitos que ninguem procurava, um deles NO AR.** O Feca pediu para eu nao aceitar as decisoes ja escritas e conferir tudo contra o codigo. **ACHADO 1, MEDIDO NA BASE, e ele sozinho perderia 30% do trabalho:** a extensao manda `odd: _oddDecimal(b.oddFrac)`, que e a odd da **PRIMEIRA SELECAO**, enquanto o banco guarda o **produto** — a casa nao publica odd combinada (o proprio `formatTicketB3` so imprime `Odd:` em `nSel === 1`). Das **113 abertas de bet365 com carimbo**, 79 tem uma perna e **34 tem duas ou mais**; nessas 34 a odd do banco bate a da 1a perna em **0 de 34** e bate o **produto em 34 de 34** (2 casas, via `_norm_odd`). A stake nao tem esse problema: 113 de 113 iguais ao bloco. O casamento falharia em silencio (`sem_par`), com sintoma identico ao do token. **CONSERTADO no 2o commit:** a odd que viaja passou a ser a DO BILHETE, pela regua do `content.js` — produto das pernas, e **VAZIA** em SISTEMA (`BC > 1`, onde a odd e a MEDIA das linhas: a mutacao que tira esse guard produz `18,7`) e em perna sem odd legivel (produto parcial e um numero que existe e passa em toda checagem de forma). Vazia nao forma chave, entao o bilhete vira "a conferir" em vez de casar errado. **Nenhum gate podia pegar isso:** o `casaDublada` gerava todo bilhete com UMA selecao, o falso verde nº 2 do `CLAUDE.md`; o duble ganhou `pernas` e `bc`, e sao **4 mutacoes, 4 detectadas**. [o caso](docs/casos/CASOS_BET365.md#a-odd-que-era-a-da-primeira-perna-e-ela-valia-30-das-abertas-s387) **ACHADO 2, CONSERTADO AQUI, e estava em PRODUCAO na 0.7.28: o cursor da paginacao andava UM SEGUNDO por requisicao.** O `to` que se pede e UTC e o `TP` que volta e hora do Reino Unido; `cursor = menorMs` comparava os dois crus, o ramo de desempate ganhava todas as voltas e o laco gastava as **40 paginas do teto sem achar o alvo, com zero erro**. Converter o carimbo nao resolve (no caminho cego o offset e o que nao se conhece): o cursor passou a andar por **DIFERENCA** (`cursor − cobertura da pagina − 1s`), que e invariante ao fuso. **O DEFEITO ESTAVA ATRAS DE UM GATE VERDE, e essa e a licao:** o caso 10c do harness rodava COM o fuso lido, e ai a janela de 1 segundo acha na 1a chamada — **o laco nunca paginava**, e a mutacao do cursor travado passava verde desde a s382. Caso corrigido para `semFuso`, mais um caso novo (historico que ACABA dentro da janela) para a mutacao que ainda escapava. **GATE: 4 mutacoes, 4 detectadas.** [o caso](docs/casos/CASOS_BET365.md#o-nono-defeito-e-ele-estava-atrás-de-um-gate-verde--o-cursor-que-andava-1-s-por-requisição-s387) **E O DIAGNOSTICO DO TERMO FOI REFEITO, porque o que estava no ar podia voltar MUDO:** o espiao do `xcftr` filtrava por `RX_SUM` sobre o valor espiado, que e exatamente a incognita, e so era ligado no 1o summary da pagina (o pedido de termo ANTECEDE a requisicao). Agora liga na carga e loga tudo. **Tres medicoes que nunca tinham sido feitas:** (1) **o termo nunca foi olhado** — `fim(ev.detail)` mandava o valor direto para o header, e um objeto viraria `"[object Object]"`, produzindo os mesmos 200-com-corpo-0 em 19 de 19; agora o tipo e o conteudo sao logados e objeto e inventariado antes de qualquer tentativa; (2) os **cabecalhos da RESPOSTA** passaram a ser lidos; (3) **a SONDA**, que e o experimento que faltava: refaz a ULTIMA requisicao da PROPRIA PAGINA, verbatim, com termo novo, em duas variantes do que se escreve em `ns_gen5_net.url` (relativa e absoluta). Ela parte o problema ao meio em UMA chamada — payload significa que termo e cabecalhos estao certos e o defeito esta na URL que **nos** montamos; vazio significa que a URL nunca foi o problema. **E a URL E suspeita, ao contrario do que estava escrito:** `_urlSummary` remonta a query do zero com seis parametros a dedo e **descarta qualquer outro** que a pagina mande, e a ordem que o comentario jura ser "a da pagina" aparece de **duas formas diferentes** nos dois exemplos medidos do proprio plano. **Corrigido de passagem:** o `X-Request-Id` podia chegar DUPLICADO (`x-request-id` da pagina em minusculas, do hook de `fetch`, mais o nosso) e o `Headers` concatena os dois em `"a, b"` — o termo ja era tratado assim, o id nao; e `_pedirTermo` deixou de apagar o `ns_gen5_net.url` da pagina quando ela escreveu por cima. **E A 1a LEITURA VOLTOU, com DUAS RESPOSTAS (0.7.29, conta do Richard):** **(1) A URL ESTA DESCARTADA COMO CAUSA.** A sonda refez a requisicao com a URL **verbatim da propria pagina**, nas duas variantes do que se escreve em `ns_gen5_net.url`, e as duas voltaram `HTTP 200 · corpo 0 byte(s)` (`server: cloudflare`, `content-length: 0`, `content-type: text/plain`). As sete tentativas da s382 mexendo em ordem de parametro, escape de dois-pontos e formato de janela estavam **todas no lugar errado**. **(2) O TERMO NAO E LIXO:** `tipo=string`, `len=1500` para a URL relativa e `len=1576` para a absoluta — varia com o que assina, entao o mecanismo funciona. A hipotese do `"[object Object]"` morreu. **E o espiao respondeu a pergunta que o originou:** a PAGINA pede o termo **pelo mesmo evento**, com a URL no mesmo formato (caminho relativo com query) — `xcftr` e o caminho certo. Mas a **ORDEM da query dela e outra**: `settled, lid, cid, csid, from, to`, com os identificadores ANTES da janela, e o comentario do codigo afirmava o contrario. **Nao e a causa** (a URL verbatim falha igual), e mesmo assim foi corrigida, junto com o descarte de parametros desconhecidos: a query agora sai da URL da propria pagina e so `settled`/`from`/`to` sao trocados. **Gate: 2 mutacoes, 2 detectadas** (recriar a query do zero; a janela antes dos identificadores). **A 0.7.30 LEVA UMA BATERIA, que substitui a sonda de uma pergunta so:** cinco requisicoes, todas com a URL da pagina como controle, cada uma eliminando UMA das diferencas que sobraram — o termo **DELA** reusado (testa uso unico), o nosso termo com o `X-Request-Id` **dela**, sem `X-Request-Id`, por **XMLHttpRequest** (que e o que ela usa) e com o `ns_gen5_net.url` ainda preenchido. Junto vai a comparacao dos dois termos (tamanho, inicio e **fim**) e do `X-Request-Id` da pagina contra o `Locator.Guid`. **E O ANDAIME PERDIA UM CAMPO DO CONTRATO:** o XHR dublado do `sandbox.mjs` **descartava os cabecalhos**, entao toda requisicao por XHR parecia "sem token" e o gate acusava defeito que nao existia. Corrigido; as casas que capturam por XHR (KTO/Kambi) seguem verdes. **E A BATERIA RESPONDEU, NA 2a LEITURA: GERAR TERMO ESTA DESCARTADO, E O TERMO DA PAGINA REUSADO FUNCIONA.** Cinco requisicoes, uma variavel por vez, todas com a URL da pagina como controle: **o termo DELA reusado devolve `200 · 3.374 bytes · 10 bilhetes`**; o nosso termo e recusado com o `X-Request-Id` dela, sem `X-Request-Id`, por `XMLHttpRequest` e sem limpar o `ns_gen5_net.url`. **O `X-Request-Id` da pagina e IGUAL ao `Locator.Guid`**, entao essa hipotese tambem morreu. E a comparacao fecha o diagnostico: os dois termos assinam **a mesma URL**, tem o **mesmo tamanho (1.536)** e o **mesmo inicio**, e diferem **so no fim** — mesmo input, assinatura diferente. **O gerador tem estado, e o que ele entrega a quem pede por fora a casa recusa**, com o corpo vazio que se confunde com "nao ha aposta". E o desenho de um token marcado: nenhum conserto na requisicao ia funcionar. [o caso](docs/casos/CASOS_BET365.md#o-termo-que-a-casa-emite-para-quem-pede-por-fora-não-serve-e-o-dela-reusado-serve-s387) **A PERGUNTA VIROU OUTRA, e a 0.7.31 a mede:** o termo dela serve para **OUTRA JANELA**? O tamanho do termo cresce com o tamanho da URL (1.500 relativa × 1.576 absoluta), entao a URL esta la dentro e a resposta provavelmente e nao — e "provavelmente" nao decide nada. A bateria 2 mede a GRANULARIDADE da assinatura, do mais util ao menos: a NOSSA janela de 1s, a URL dela com um parametro a mais, com `settled=0`, e o 2o reuso (para saber se o termo tem cota ou prazo). **Se a 1a linha passar, o botao esta resolvido sem gerar termo nenhum**; se parar na 2a ou 3a, a fronteira da assinatura esta medida e o caminho passa a ser fazer a PAGINA pedir a janela que queremos. **E A BATERIA 2 FECHOU O DIAGNOSTICO: A ASSINATURA COBRE A URL EXATA.** Com o termo DA PAGINA: a URL dela pela 2a vez devolve **3.326 bytes, 10 bilhetes**; a NOSSA janela de 1s, a URL dela com um `&zz=1` a mais e a URL dela com `settled=0` devolvem **corpo 0**. Entao o reuso nao tem cota, mas so vale para a janela que ela pediu. **As duas metades fecham o caminho: nao da para GERAR (o termo emitido a quem pede por fora nunca e aceito) e nao da para REUSAR (o dela nao serve para outra URL). Chamar a API por fora esta ENCERRADO POR MEDICAO**, e o que sobra e dirigir a TELA, como o `PLANO_RESOLVER_ABERTAS` ja desenhava — a diferenca e que agora nao e escolha, e o unico caminho. **O QUE ENTROU NA 0.7.32, e paga por si:** a conferencia do mecanismo passou a rodar **ANTES** do laco. Ela nasceu depois, para nao gastar uma ida a casa confirmando o que a busca ja teria provado — certo no caso bom, caro no ruim, e o ruim e o normal quando o mecanismo e anti-automacao: **19 chamadas por clique** atras de 22 apostas, todas vazias pelo mesmo motivo, para no fim o controle dizer o que a primeira ja dizia. Invertido, custa **+1** requisicao quando tudo vai bem e economiza **18** quando nao vai. A bateria saiu (cumpriu o papel); ficaram o espiao do `xcftr` e o log do termo, que custam zero. **E O ANDAIME TINHA UM SEGUNDO DEFEITO, pior que o primeiro:** o dulbe separava a requisicao da PAGINA da nossa por um **cabecalho**, e desde a s382 o inject **copia todos os cabecalhos da pagina** — o marcador viajava junto em toda chamada nossa. Resultado: o gate do `semToken` **nao podia mais acusar**, e um cenario novo escrito para medir o abort simplesmente nao acontecia (a mutacao passou verde). Marca de ator mora no andaime, nunca no dado: a requisicao da pagina passou a ser **a primeira**, por booleano. **GATES: 2 mutacoes, 2 detectadas** (nao abortar com o controle morto; o controle voltar a rodar so no fim). [o caso](docs/casos/CASOS_BET365.md#o-marcador-que-o-código-sob-teste-copiava-e-por-isso-não-marcava-nada-s387) **DUAS COISAS PARA O FECA, e a primeira e um clique:** a **0.7.32** esta no ar (nota na home, grupo NAO avisado, como decidido) e basta **UM clique** no botao, com o console aberto, e o print — as linhas comecam com `[SharpenUp b3_inject] sonda` e `termo recebido`. **A segunda e uma decisao:** o botao grava em `correcoes` via `atualizar_bilhete`, e **sete scripts de reparo leem essa tabela como decisao do dono** — escrita de robo passa a blindar a linha contra reparo futuro, com procedencia mentirosa. A tabela nao tem coluna de origem. Divida que ja existe pelo bot de tipster, mas aqui passa a acontecer em massa; anotada no BACKLOG.)

_Anterior: 2026-09-23 (sessao 386: **o tradutor deterministico passou a decidir o esporte da MULTIPLA da Bet365 — e a medicao que autorizou isso corrigiu o alvo da sessao no meio do caminho.** Estado medido na entrada, 28.473 blocos na `sombra_rotulos` (a sombra cresceu dos 16.962 do briefing): cobertura **64,0%**, conformidade com o MASTER **tradutor 99,99% x IA 85,9%**, e a ORDEM dos baldes ja tinha invertido — `mercado desconhecido` 14,3% passou `esporte nao declarado` 12,7%. **O ALVO ERA A MULTIPLA:** 2.949 dos 3.621 blocos do balde do esporte (81,4%), todos com 2 pernas e 2 confrontos. A Bet365 nao escreve `Esporte (casa):` em multipla porque nao existe um esporte so, o tradutor procurava a linha, nao achava e desistia do bilhete inteiro. **A RESPOSTA ESTAVA NO BLOCO, NOUTRA LINHA:** quem escreve `Tipo: Multipla` e o `formatTicketB3` (`extensor/content.js:6118`), sob `multiplo = jogos.size >= 3 || cls.length > 1` — que **E** a regra do `MASTER_ESPORTES §2`. A mesma condicao suprime a linha do esporte. A regra ja tinha sido aplicada; nos e que nao liamos a resposta. **DUAS PROVAS, e a segunda nao passa pela IA:** (1) **codigo** — com 2 pernas, `jogos.size <= 2`, entao a marca so pode ter vindo de `cls.length > 1` = mistura de esportes; (2) **empirica** — montei um mapa liga→esporte a partir dos blocos em que a casa DECLARA o esporte (**713 ligas, 713 resolvidas** com >=95% num esporte so) e apliquei nos 2.949: nos **1.295 julgaveis, 1.295 tem as duas pernas em esportes diferentes — 100,00%, zero contraexemplo**. Os 1.654 restantes sao liga que nunca apareceu com esporte declarado, dominados por `MLB` (799) e `NFL` (489), que nao tem CL no `_CL_B3`; li os 16 que discordam da IA um a um e todos sao mistura clara (`B-ELSUPCUPM` e `B-SWESUPM` sao basquete, nao futebol). **A IA discorda em 62 (2,1%) e esta errada nos 62** — em varios o MESMO codigo foi lido duas vezes, uma dizendo `Futebol` e outra `Multiplos`, que e a instabilidade do §II.9 aparecendo de novo. **⚠️ O SINAL E DA CASA, NUNCA GLOBAL, e isso quase passou batido:** `formatTicketNV`, `formatTicketRG`, `formatTicket1X` e `formatTicketPN` tambem emitem `Tipo: Multipla`, mas por `n > 1` — CONTAGEM DE PERNAS, nao o §2. Numa delas a mesma linha marcaria dupla de 2 jogos do MESMO esporte como `Multiplos`. Dai o `_TIPO_MULTIPLA_E_VEREDITO`, um conjunto de casas, com o aviso escrito ao lado. **O ACHADO QUE CORRIGIU O ALVO: consertar o esporte entrega ZERO de cobertura.** Simulei antes de escrever e os 2.949 so trocam de parede — **89,1% caem em seguida por rotulo fora do mapa**, 10,0% pela odd combinada. A razao e estrutural: **a cobertura de uma multipla e o E LOGICO das pernas**, e os esportes que so aparecem em multipla (MLB, NFL) nunca tiveram o vocabulario aprendido. **A multipla e FORMATO na primeira parede e DICIONARIO na segunda.** **E MEDINDO A TERCEIRA PAREDE APARECEU A QUE MANDA: ZERO de 3.442 blocos `Tipo: Multipla` traz linha de odd.** O `formatTicketB3` so imprime `Odd:` em `nSel === 1`, e `Odd total`/`Odd (estrutural)` so em SISTEMA. Nenhuma multipla comum da Bet365 pode ser traduzida hoje, **com dicionario nenhum** — o guard da odd combinada e 100% do balde, os outros 89% so batem no rotulo antes. **ENTAO O QUE ESTA MUDANCA ENTREGA E O BALDE PARAR DE MENTIR:** `esporte nao declarado` 3.621 → **672**, `mercado desconhecido` 4.061 → 6.689. Era o motivo FALSO que fazia a multipla parecer problema de formato, e foi ele que escolheu o alvo errado no inicio desta sessao. Cobertura e conformidade **inalteradas** (64,0% e 100,0%), como a simulacao previu. **GATE:** 6 casos novos em `tests/test_tradutor.py`, dois blocos REAIS da sombra conferidos **linha a linha contra o banco** antes de entrar (`KT1443992451I`, a multipla; `RT7832775711I`, o `Tipo: 2 selecoes` de dois jogos de MLB com `CL=16` sem nome, que e o contra-caso). **4 mutacoes no arquivo de verdade, 4 detectadas**: sem a trava de casa, regex do `Tipo` aceitando qualquer coisa, o veredito atropelando o esporte declarado, e o veredito removido. Suite **1.339 passed**. **E A SEGUNDA MUDANCA E A QUE PAGA: A ODD ESTRUTURAL DA MULTIPLA, +6,0 PONTOS DE COBERTURA (64,0% -> 70,0%, 1.728 bilhetes).** O `MASTER_RESULTADO §7.1` diz QUANDO a odd estrutural e a resposta (`L` sem cashout, `V`, e aberta) e o **§7.2** diz o que ela e numa multipla comum: **o produto das odds das pernas**. O tradutor recusava todas por desenho — o cabecalho do modulo adiava *"aritmetica de odd"* para um incremento proprio, com gate proprio. Este e o incremento. **A PROVA E DO DINHEIRO, nao da IA:** em multipla GANHA a casa publica o retorno, e `stake x produto` bate o retorno **AO CENTAVO em 479 de 529 (90,5%)**. Os 50 que nao batem sao **perna ANULADA** (`GT8020619111I`: duas pernas @ 2,2 e retorno = 2,2 x stake — a outra virou 1,00) e **meia vitoria** de linha asiatica; os dois casos so se conhecem pelo dinheiro e os dois sao `W`. **`W` FICA DE FORA DE PROPOSITO:** ali o §7.1 manda `Retorno ÷ Stake`, e e justamente essa conta que ESCONDE meia vitoria — o `_resultadoB3` escreve `Ganho → W` para qualquer retorno maior que a stake, e fechar por `retorno ÷ stake` deixa o bilhete internamente consistente sem nunca chegar a `HW` (o caso da s356). Quem separa os dois e o `_veredito_do_retorno`, no servidor. **CONTRA O BANCO, 5.386 bilhetes: 96,5% batem** e as 154 divergencias sao a IA errando — ela **derruba pernas do produto** (`LB9804921624I`: 1,8 x 1,775 x 1,7 = 5,4315, gravada **1,8**, uma perna so; `DQ5129778651W`: 12 pernas, produto 119,80, gravada 17,93; `FP1746791294I`: o produto de DUAS das tres) com uma folga de ~0,2% por cima. **E a familia *"a odd que era outro campo do mesmo bloco"* do `CLAUDE.md`, agora com numero.** **DUAS DECISOES DE ENGENHARIA, as duas nascidas de medicao:** (1) **o ruido do `float64` nao pode vazar** — a perna chega como `1,5333333333333332` (23/15 em float64) e o produto EXATO daria `2,2999999999999998` onde a casa diz `2,3` (bilhete real `LP2437618471I`); multiplica-se com 34 digitos e **corta-se o resultado em 15 significativos, que e o piso de ruido da entrada**. (2) **`_num_bloco` MUDOU DE CASA**, do `repository` para o `tradutor` (que o reexporta), porque ganhou um irmao em `Decimal` — duplicar a regua de separador era o que o `CLAUDE.md` proibe, e ela existe por causa da Betfair, que mistura BR e EN no mesmo bloco (s321). **SISTEMA NAO E MULTIPLA, e a trava e o `Tipo:`** — trocar um pelo outro e a s265 (`3 x Duplas` lida como tripla). Hoje o sistema nunca chega ao produto porque TRAZ linha de odd, mas isso e defesa de segunda mao: **a mutacao que apaga o guard do `Tipo:` passou VERDE** ate eu escrever o caso do `GP3348650691I`, um sistema perdido real cuja media e 3,7347916666666667 e cujo produto seria **7,20875, quase o dobro**. **GATE:** 12 casos novos ao todo, **6 blocos reais conferidos linha a linha contra o banco**; **7 mutacoes na segunda bateria, 7 detectadas** (a 7a so depois do caso do sistema). Suite **1.350 passed**, `check_docs` e `audit_casas` sem FAILs. **A TERCEIRA MUDANCA, e ela e uma licao sobre como o rotulo engana: `Gols +/-` (+1,0 ponto, 70,0% -> 71,0%).** O mapa tinha `Gols + -` e nao tinha `Gols +/-`: **291 blocos iam para a IA por UM caractere** — a mesma casa escreve o mesmo mercado das duas formas (8.956 x 291). Passa a regua da s333 folgado (265 amostras de 1 selecao, 98,5% `Gols`). **Mas a linha de mapa SOZINHA nao entrega nada**, e medir antes mostrou isso: as **291 sao TODAS ao vivo** (`Ao-Vivo - Gols +/-`), e a casa prefixa a selecao com o placar do momento num formato que o `_PLACAR_AO_VIVO` nao conhecia — `(5-0) - Mais de 6.5,7.0`, com TRAVESSAO, contra o `(0-0) Time -0.5` colado que ele ja tratava. Com o rotulo resolvido e a selecao nao, o bilhete apenas TROCA de motivo (`mercado desconhecido` -> `selecao fora do template`) e some do balde certo parecendo progresso. **O `-\\s+` do regex exige ESPACO depois do traco, e isso e load-bearing:** sem ele, `(1-0) -0.5` perderia o SINAL e viraria `0.5` — a aposta invertida, sem erro em lugar nenhum. 3 casos novos, **3 mutacoes / 3 detectadas** (inclusive a do espaco). Linha registrada no `CASA_BET365 §9`. **`Total de Cartoes` (637 blocos) FICOU DE FORA, e o motivo e a segunda regua da s333:** **480 deles (75,4%) chegam como `Time da Casa - Total de Cartoes - 3 Opcoes` ou `Time Visitante - ...`**, e a IA escreve esse escopo NA DESCRICAO (`Under 2.0 Cartoes - Time da Casa`). O `_QUALIFICADORES` do tradutor DESCARTA o qualificador — e o proprio `§9` diz que eles *"entram na descricao conforme o master, mas nao mudam a categoria"*. **O comentario do codigo confundiu 'nao muda a categoria' com 'nao vai na descricao', e isso ja afeta rotulos que estao no mapa** (`Time Visitante - Total de Escanteios - 3 Opcoes` resolve por `total de escanteios` e sai sem o escopo). E a gemea espacial do escopo de TEMPO (decisao D, `BACKLOG 3.8`), e entra na fila com ela, nao como linha de tabela. **Suite 1.353 passed.** **O QUE SOBRA MEDIDO:** `mercado desconhecido` 6.398 segue como o maior balde; dentro dele, o escopo (tempo + time) e agora o maior grupo nomeado.)

_Anterior: 2026-09-23 (sessao 385: **a SOMBRA DE MODELO entrou no ar: o Haiku passa a ler EXATAMENTE o mesmo lote que o Sonnet, em background, com custo separado.** Decisao do Feca (*"tudo q o Sonnet fizer, o Haiku tem q receber EXATAMENTE a mesma instrucao no background e tudo isso estar sendo documentado"*). **Ela existe porque a bancada offline e' um RETRATO** — 300 blocos escolhidos por mim, num dia — **e ja errou duas vezes por defeito de arranjo da entrada, reprovando o Haiku por engano** (`docs/CASOS.md`). A sombra em producao nao tem esse problema: entrada real, distribuicao real, **e cobre print e PDF, que a bancada nunca cobriu**. **COMO:** `_sombra_modelo` (`main.py`) recebe o MESMO `system` e os MESMOS pedacos (chunks no paralelo, o content inteiro no sequencial) e replica no candidato; roda DEPOIS do `done`, fire-and-forget, com `except` proprio — falha dela nunca vira erro do usuario. **O juiz e' DETERMINISTICO** (`repository.pontuar_saida`, funcao PURA): bilhete que nao voltou, codigo inventado, coluna comida, descricao fora do MASTER e descricao infiel, pelos mesmos verificadores que ja rodam em producao. A IA nunca julga a IA (a s336 mediu que ela discorda dela mesma em 76,7% das releituras). **TABELA NOVA `sombra_modelo`, e ela NAO e' o `uso_tokens` de proposito:** aquela e' a conta da OPERACAO e e' lida por toda medicao de preco; gasto de experimento ali envenenaria as duas leituras (a armadilha do `realtrial` na s356). **CUSTA DINHEIRO DE VERDADE: ~US$ 150 a 200/mes** enquanto ligada, e o cache e' por modelo, entao as primeiras chamadas de cada casa pagam escrita. Desligar e' `SOMBRA_MODELO=''` ou `SOMBRA_MODELO_PCT=0`, **sem deploy**. **O GATE PEGOU UM DEFEITO REAL MEU antes do commit:** o `claude-haiku-4-5` nao tinha linha em `_PRECOS`, entao o custo da sombra sairia ao preco do Sonnet 4.6 e o experimento mentiria **para o lado que favorece o candidato**. E' exatamente a armadilha que eu documentei na s377 e cai nela um dia depois. **E O GATE PEGOU UM SEGUNDO:** o meu 1o script de mutacao (escrito em heredoc, que come escape) estourou no meio e **deixou o `main.py` MUTADO** — a sombra mandando `[]` no lugar do `system`. O `ast.parse` passou, porque `[]` e' sintaxe valida; quem acusou foi o teste que exige entrada IDENTICA a do titular. **Script de mutacao precisa de `finally`, e o heredoc nao serve para escrever um.** **GATE: `tests/test_sombra_modelo.py`, 9 mutacoes, 9 detectadas**, cobrindo os tres riscos: o juiz enxerga cada defeito (e aprova o que esta certo, senao um juiz que reprova tudo passaria), a sombra nao escreve em `uso_tokens`, e a entrada e' a MESMA do titular. Suite 1.317 passed. **PENDENTE: o primeiro relatorio da sombra**, depois de alguns dias de trafego. **E o CI voltou a rodar:** o `fix(ci)` de hoje tirou os 5 travessoes de COMENTARIO da landing que derrubavam o job no 1o passo — harness de banco, auditoria de casas, check de tokens e gate de docs nao rodavam ha 6 commits; os quatro voltaram VERDES, e o vermelho que sobra e' o cronico `BACKLOG 1.7` dos links `../pack/`.)

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
