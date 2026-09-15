# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-14 (sessao 358 - continuacao: **as tres telas antigas de custo sairam do MENU, e o gate de documentacao ficou VERDE pela primeira vez em varias sessoes.** **FATIA 5 (menu), decisao do Feca:** `Custos de Contas`, `Custos de Tipsters` e `Fornecedores & Parceiros` nao aparecem mais em nenhuma das duas sidebars, e a tela nova deixou de se chamar `Custos (previa)` — com as outras fora, o rotulo *previa* passaria a descrever o produto inteiro. **Sairam do MENU, nao do codigo:** as paginas seguem alcancaveis por hash direto (`#dash/custos`), o que mantem a volta em uma linha e nao arrisca funcao compartilhada — `_ctTipsters`, `_ctSituacao`, `_ctSugestao` e `buildCostState` sao lidos pela tela nova. **A regua velha dessas tres NAO foi consertada, de proposito.** **GATE NOVO: `tests/test_sidebar_dupla.py`, 5 de 5 mutacoes detectadas.** O menu e DUPLO (`app/static/app.html` e o array de nav do `dash/assets/js/app.js`) e nada ligava as duas listas; mexer numa so ja custou a s144 inteira (*"nao achei nada"*, porque a sidebar que o Feca ve e a da casca). O teste nao julga QUAIS telas existem — exige que as duas cascas concordem. **FAXINA, e o achado dela vale mais que os KB:** o `CLAUDE.md` estava em **72,8 KB** com teto de 65, aberto no BACKLOG desde a s339. A s339 tinha MEDIDO que nao havia mais duplicacao para mover e concluido que fechar o teto exigiria **decidir qual regra sai**. A medicao estava certa e a conclusao nao: o arquivo guardava **PROCEDIMENTO** junto com regra. Sairam inteiras, com ponteiro e **sem cortar uma linha**, `docs/RUNBOOK_CONTAS_E_ACESSO.md` (6,2 KB) e `docs/RUNBOOK_AVISO_TESTERS.md` (3,2 KB); com mais 0,5 KB de caso para o `CASOS.md`, o arquivo fechou em **64,5 KB**. **A licao entrou no invariante #10:** *nao ha mais nada para mover* costuma significar *nao ha mais nada DO TIPO que eu estava movendo* — a pergunta que destravou nao foi *o que corto?*, foi *o que aqui nao e regra?*. **BACKUPS: as 223 copias de STATUS/HISTORICO sairam (28,7 MB), autorizadas pelo Feca.** Nao foram apagadas direto: viraram um zip de 11,8 MB na propria pasta, **conferido entrada a entrada (nome, tamanho e hash de amostra) ANTES de qualquer remocao** — se algo falhasse no meio, nada teria sido apagado. O git ja versiona os dois arquivos, entao o zip e cinto e suspensorio para quem abrir a pasta sem saber git. 69 pastas vazias sairam junto. **`check_docs.py`: sem FAILs.** Suite 1.079 passed; os 3 vermelhos do `test_changelog` seguem sendo o manifest 0.7.13 sem nota, de outra sessao — e enquanto ficar assim a **home mostra versao atrasada para os testers**, que e o que aquele gate existe para dizer. **PENDENTE, e e do Feca:** (1) o **aviso aos testers** da leva de custo inteira, que muda o P/L Liquido de todo mundo (sobe pelo custo de conta, desce para quem lancou custos gerais); (2) **remover o CODIGO** das tres telas, quando ele confirmar que nao sentiu falta; (3) a nota do changelog da 0.7.13. **E A SESSAO FECHOU COM O REDESENHO DO RODAPE, vindo do Claude Design:** *"precisamos mudar esse visual e esse nome horroroso"*. A faixa full-width SAIU e a informacao virou RODAPE do proprio cartao Custo de Contas: dois pares rotulo/valor mais uma ressalva. **O nome `parque` morreu com ela** — era jargao de frota e nao dizia que o numero e custo JA PAGO. Hoje e **Contas em operacao**, e a palavra virou PROIBIDA no produto (com *investido* e *imobilizado*), com gate proprio. **Quatro estados, todos medidos na tela:** sem compra no periodo (topo em `--ink` + *ja pago, fora do P/L*), com compra (topo negativo em `--neg` + *X pagos neste periodo, ja no P/L*), filtro de tipster (rotulo vira *Contas deste tipster* + badge *escopo · Tipster*) e sem conta com custo (uma linha so, **sem zeros**). **REGRA NOVA, e ela exigiu medicao antes de escrever codigo:** o filtro de TIPSTER passou a recortar as contas, e o vinculo conta-tipster **nao existe no cadastro** — existe no bilhete. Medido: **96% das contas do Feca sao usadas por mais de um tipster** (89% no Jonathan, 100% no germano), entao a mesma conta entra no recorte de varios e os rodapes **nao somam**. E por isso que o rotulo muda junto com o numero. **DUAS DIVERGENCIAS DO DESENHO, as duas por MEDICAO na tela:** (1) o badge era `position:absolute` com reserva de 104px no rotulo, e medindo deu 118px de badge contra 112px de titulo em 210px uteis — o titulo quebrava em duas linhas; virou uma linha flex onde o badge DESCE quando nao cabe, em vez de espremer o titulo. (2) o componente de dinheiro dentro da ressalva precisou do mesmo carve-out de largura que o `.kpi-sub` ja tinha, senao a nota quebrava em varias linhas. **Token novo `--neg-2` (#EF8C86) no canonico `pack/tokens/tokens.css`**, propagado pelo `build-tokens.mjs`: custo em linha secundaria nao e resultado negativo, e por isso nao usa o `--neg`. Gate: 53 testes no arquivo de custo. Suite 1.080 passed. **ETIQUETA:** o working tree tinha uma frente inteira ALHEIA e nao commitada (o cartao *Dia da Semana*, em `shared.js`, `performance.js`, `app.js` e parte do `overview.js` e do `components.css`). Separei por reconstrucao: commitei so os meus hunks e devolvi os dela ao working tree, intactos. **E O TRABALHO DELA FOI COMMITADO no fim (bc715e3), a pedido do Feca:** o cartao Dia da Semana, em quatro JS e um CSS, como estava. Conferido antes, porque codigo alheio nao se commita sem ver funcionando: suite verde, tokens verdes, node --check nos quatro, e a tela aberta headless nas TRES superficies que o usam, sem erro de pagina. Bumpei os cinco ?v= que faltavam — dois deles ja tinham subido em outra versao no commit anterior, entao sem bump o cartao nao apareceria para quem carregou a pagina no meio. **E A BARRA DO CARTAO TROCOU DE REGUA no mesmo dia, por achado do Feca na tela:** ela media VOLUME de apostas, e enganava. No print dele o sabado (8.545 apostas, R$ 97.726) tinha a barra mais longa e a quarta (5.494 apostas, R$ 135.911, ROI 11,56% contra 5,66%) ficava atras: *"faz sentido eu ter ganhado mais dinheiro na quarta com roi mto melhor, e ser a linha do sabado q ta la na frente?"*. Nao fazia. O olho le a barra mais longa como o melhor dia, e **volume nao e merito**. **A LICAO: a legenda DIZIA o que a barra media, e mesmo assim enganou.** A saida registrada no `CLAUDE.md` para *numero que parece contradizer o vizinho na mesma tela* e a tela DIZER o corte — e aqui dizer nao bastou, porque o problema nao era falta de aviso: era o canal visual mais forte do cartao medindo a grandeza errada. Legenda nenhuma salva barra que mede a coisa errada. Hoje o comprimento e o **P/L do dia contra o melhor do periodo** e a cor e o sinal; o volume ficou so na coluna Apostas, como numero, que e o peso certo para ele (decisao do Feca entre P/L, ROI e barra bidirecional com zero no meio). **Piso de 1,5% de largura:** o dia que apostou e quase nao rendeu (terca, R$ 1.136 contra R$ 135 mil) renderizava ~0,8% e sumia, e barra ausente le como defeito, nao como *quase nao rendeu*. P/L exatamente zero tem barra NEUTRA, nao verde nem vermelha: cor ali afirmaria um sinal que o numero nao tem. Medido headless nas tres superficies; `?v=` de `components.css` e `shared.js` bumpados junto. **2a ITERACAO DO DESENHO DO CARTAO DE CUSTO, no mesmo dia:** o bloco virou DUAS CELULAS lado a lado com divisor, no lugar dos pares empilhados; o badge de escopo SAIU (a 1a celula ja declara, *Deste tipster*, e o badge repetia a informacao noutro canto do mesmo cartao); o estado vazio deixou de ter bloco (nunca *0 contas · R$ 0*); e os OITO cartoes da Visao Geral passaram a ter a MESMA altura, 180px — a referencia reprova altura solta so no cartao de custo, porque ela estica a fileira inteira. **O `min-height` ficou escopado em `#kpiGrid`**: o `.kpi` e usado nos drills, nas Metricas e na tela de Custos, onde 180px seria vao morto. **O cartao estourava os 180 por 1 a 7px** — a nota quebra em duas linhas quando o andar tem 5 tiles e o cartao fica estreito. Quem cedeu foi o RESPIRO acima do valor, **nunca a copy**: encurtar texto para caber em pixel e trocar informacao por layout. **O grid voltou a colunas fixas** (4, com 2 abaixo de 1100px e 1 abaixo de 560px), mas cada andar cai no proprio numero de cartoes — fixar 4 deixaria o 5o (Custos Gerais) sozinho numa linha so dele. Medido nos 4 estados: alturas iguais, celulas na mesma linha, divisor em `--line-2`, custo em `--neg-2`, zero erro de pagina. **E o gate de vocabulario pegou a MIM:** sobrou a palavra proibida num comentario do CSS que eu mesmo escrevi para explicar a troca de nome. **2a ITERACAO DO DESENHO DO CARTAO DE CUSTO, no mesmo dia:** o bloco virou DUAS CELULAS lado a lado com divisor, no lugar dos pares empilhados; o badge de escopo SAIU (a 1a celula ja declara, *Deste tipster*, e o badge repetia a informacao noutro canto do mesmo cartao); o estado vazio deixou de ter bloco (nunca *0 contas · R$ 0*); e os OITO cartoes da Visao Geral passaram a ter a MESMA altura, 180px — a referencia reprova altura solta so no cartao de custo, porque ela estica a fileira inteira. **O `min-height` ficou escopado em `#kpiGrid`**: o `.kpi` e usado nos drills, nas Metricas e na tela de Custos, onde 180px seria vao morto. **O cartao estourava os 180 por 1 a 7px** — a nota quebra em duas linhas quando o andar tem 5 tiles e o cartao fica estreito. Quem cedeu foi o RESPIRO acima do valor, **nunca a copy**: encurtar texto para caber em pixel e trocar informacao por layout. **O grid voltou a colunas fixas** (4, com 2 abaixo de 1100px e 1 abaixo de 560px), mas cada andar cai no proprio numero de cartoes — fixar 4 deixaria o 5o (Custos Gerais) sozinho numa linha so dele. Medido nos 4 estados: alturas iguais, celulas na mesma linha, divisor em `--line-2`, custo em `--neg-2`, zero erro de pagina. **E o gate de vocabulario pegou a MIM:** sobrou a palavra proibida num comentario do CSS que eu mesmo escrevi para explicar a troca de nome. **E O FECA PEDIU CARTOES MENORES, com o print na mesa** (*"achei q os cards ficaram grandes demais"*) **e o bloco sem link** (*"nao precisa linkar dentro do card, n ficou legal"*). O link saiu inteiro: sem `onclick`, sem cursor, sem hover, e a funcao de navegacao foi junto por ficar sem chamador. **A altura foi de 180 para 156px, e o caminho foi MEDIR o que ocupava espaco, nao chutar um numero:** o cartao de custo tinha 178px naturais e os outros sete, 120 — 60px de vao morto em sete lugares. Dos 178, **13 eram a SEGUNDA linha da nota**, que quebrava em toda largura de 5 colunas; *neste periodo* saiu da copy por ser redundante (o cartao inteiro ja e do periodo) e a nota passou a caber em uma linha em qualquer largura. O resto veio de espacamento: margens do bloco, padding do cartao. **DUAS VARIANTES FORAM MEDIDAS E DESCARTADAS na tela, nao na cabeca:** reduzir o valor principal nao muda nada (ele ja e 22px, nao 28), e o bloco em linhas corridas ficou MAIOR (164 contra 159). **O piso e 155px** — abaixo disso o cartao de custo corta conteudo. **E a referencia violava a Escada de Tinta:** `.kpi__cl` e `.kpi__pnote` vinham em **9px `--ink-mute`**, abaixo do piso do papel (label pede `--ink-soft` 9,5px; metadado pede `--ink-mute` 10px). Era por isso que apareciam apagados no print. Subiram um degrau, o que atende a regra da casa E o "legivel" que ele pediu. **E O CARTAO DIA DA SEMANA FOI PARA A v3, importada do Claude Design ("Sharpen - Dia da Semana v3 (Opcao 04)"):** ordem nova das colunas (**Apostas -> Turnover -> P/L -> ROI**, do input para o resultado, com o ROI fechando a linha), o nome do dia passou a viver DENTRO da barra, entrou linha de TOTAL do periodo e entraram **chips que trocam a metrica da barra** (R$ / ROI / Turnover). **A barra ganhou ESCALA COMPRIMIDA (raiz quadrada), e ela e load-bearing:** em proporcao direta a terca (R$ 1.136 contra R$ 135.911 da quarta) rendia 0,8% de largura e sumia, e barra ausente le como defeito, nao como "quase nao rendeu"; a raiz puxa os pequenos sem inverter ordem nenhuma (raiz e monotonica). **REGRA NOVA, e ela e ASSIMETRICA de proposito:** ganho com |ROI| < 0,25% sai em CINZA, porque e ruido estatistico e nao resultado; PERDA continua vermelha por menor que seja, porque o dinheiro saiu de verdade. O corte ficou no meio do vao medido entre o ruido da terca (+0,10%) e o menor ganho real, a quinta (+0,55%). **TRES DESVIOS DELIBERADOS do arquivo de desenho, cada um por regra medida deste repo:** (1) `opacity:.85` sobre `--ink-mute` no cabecalho SAIU — opacidade nao e degrau da escada, e multiplicador, e derruba contraste sem aparecer em grep de cor nenhum; (2) legenda, rotulo do rodape e chips vinham em `--ink-mute` a 9,5px, abaixo do piso desse tom, e os tres sao LABEL (papel de `--ink-soft`); (3) o chip aceso era `#fff` sobre `--accent` — medido, **3,36:1**, reprovado; com `var(--bg)` da **5,8:1**. **UM DESVIO QUE VAI NO SENTIDO CONTRARIO e precisa da palavra do Feca:** o P/L e o turnover da tabela saem **sem o `R$`**, com a unidade no cabecalho da coluna ("P/L (R$)"), porque com duas colunas de dinheiro lado a lado o cifrao repetido 16 vezes e ruido. Isso contraria o `UI_REFERENCE §5.1` ("todo valor em R$ usa o componente `.money`"), que NAO tem gate automatico — o `check-tokens` so barra abreviacao. Ou vira excecao nomeada no `UI_REFERENCE`, ou volta para o `.money`; hoje esta como o desenho pediu. **DOIS DEFEITOS QUE SO O TESTE DE CLIQUE PEGOU.** (a) O componente foi escrito para receber um `id` por cartao e os TRES call sites nao passavam nenhum: todos caiam no id padrao, entao o chip do drill repintava o cartao da Visao Geral **atras do modal**, sem erro nenhum. (b) O `min-width` de 880px do desenho nao cabe no drill: **MEDIDO, o container da 820px**, nao os 872 que a conta pelo CSS sugere (modal 920 menos dois paddings de 24) — e a coluna ROI, justo a que fecha a linha, so aparecia com scroll. Foi para 800px. **GATES (scratchpad, headless):** o de sempre nas 3 superficies; um de CLIQUE nos chips (as larguras mudam, o cabecalho acompanha, e trocar num cartao nao mexe no outro); um de LARGURA (`scrollWidth > clientWidth` nas duas superficies); e um da regra do cinza com dado fabricado, **7 de 7 faixas**, com as duas bordas (0,249% cinza, 0,251% verde) — a base de demo nao tem nenhum dia na faixa de ruido, entao sem ele a regra subiria sem ter sido exercida uma vez. **E O CORTE PASSOU A LER O ROI COMO A TELA O IMPRIME** (2 casas), decisao do Feca na sequencia: com o valor cru, 0,249% e 0,251% saiam os DOIS como "+0,25%" e ganhavam cores diferentes — dois numeros identicos lado a lado com cores distintas leem como defeito, e o digito que decidiu a cor e justamente o que o arredondamento apagou, entao quem le nao tem como saber por que. Hoje "+0,24%" e cinza e "+0,25%" e verde, e o que se ve e o que decide. O teste da regra virou a prova disso: dois dias com ROI cru diferente que a tela imprime igual TEM de sair na mesma cor, e ha mutacao para os dois lados (sem o corte, a terca sairia verde; com a regua lendo o cru, quinta e sexta sairiam diferentes com o mesmo texto). **E DE 156 FOI A 140px, com o Feca pedindo o mesmo tamanho para todos e um pouco menor.** A anatomia do cartao de custo foi MEDIDA pedaco a pedaco antes de cortar qualquer coisa: padding 25px, rotulo 16, valor 27, bloco 61, nota 24. **O bloco era o maior**, e a altura desceu por ESPACO (margens do bloco, respiro da nota, padding do cartao, valor de 22 para 20px) — nunca por conteudo. **Duas variantes foram medidas e DESCARTADAS na tela:** por a celula em linha unica (rotulo e valor lado a lado) ficaria em 137px, mas **estoura o texto**; e a mesma coisa somada aos apertos daria 124px e estoura igual. **A MEDICAO ACHOU UM DEFEITO QUE JA ESTAVA NO AR:** em 1366 (tile de 200px) a celula tinha 68px uteis, e ali *Em operacao* pedia 75 (saia com reticencias) e **o valor `R$ 29.400` pedia 68 numa coluna de 51 — numero de dinheiro TRUNCADO**. A culpa era do padding interno de 16px por celula; foi para 8, o tracking do rotulo de .12em para .06em e o valor da celula de 14,5 para 13,5px. Conferido depois: nenhum dos quatro textos corta, em 1600 nem em 1366. **Resultado: 140px nos quatro estados, contra os 180 originais — 22% mais baixo**, com o piso de conteudo em 139. **AVISADO AO GRUPO** (`Sharpen - Testers`, destino conferido por getChat, message_id 4020) pelo modo `--novidade`: e painel, nao SharpenUp, e numerar versao ali versionaria o produto inteiro. A mesma nota foi para a home no mesmo ato. **PROXIMO PASSO, tudo do Feca:** (1) decidir o P/L e o turnover **sem `R$`** na tabela do Dia da Semana, com a unidade no cabecalho, como o desenho pediu: contraria o `UI_REFERENCE §5.1` e aquela regra **nao tem gate**, entao ou vira excecao nomeada no documento ou volta ao `.money`; (2) a nota da **0.7.13** do SharpenUp, unico FAIL do `audit_changelog` e herdado - enquanto ficar assim a home mostra versao atrasada da extensao; (3) o aviso represado da leva de CUSTO, que muda o P/L Liquido de todo mundo. **E o `CLAUDE.md` esta a 0,1 KB do teto (64,9 de 65).** A licao desta sessao (regua que decide COR tem de ler o numero como a tela o imprime, nao o cru) ficou so aqui e no comentario do `_dowClasse`, sem ponteiro no lugar canonico, porque cabe-la exige mover algo para fora primeiro. Faxina dedicada, decisao do Feca. **E DE 140 FOI A 120px, tirando a LINHA DE NOTA** (*"o valor ja pago e o valor que aparece maior, certo? nao precisa repetir ele nessa ultima linha"*). Ele estava certo: a nota dizia `R$ 79.300 pagos · ja no P/L` ao lado de `−R$ 79.300,00` em corpo grande. **O corte que ela carregava foi para o ROTULO, que nao custa linha:** a 2a celula virou `CUSTO DELAS`, que amarra o valor as contas em operacao e, por oposicao, deixa o topo como o custo do periodo. **A ideia das TRES celulas foi implementada e MEDIDA, e nao coube:** com tres, a celula fica com 57px em 1366 e o valor `R$ 29.400` (68px) e truncado — o mesmo defeito que eu tinha acabado de consertar, de volta por outro caminho. Com duas, nada corta em largura nenhuma. **Sem a nota o conteudo do cartao caiu para 117px**, contra 112 dos simples — praticamente iguais —, e o piso foi de 140 para **120px: 33% abaixo dos 180 originais**. Medido nos 4 estados, zero erro de pagina. **FICA ABERTO, e e PERGUNTA ao Feca:** o print dele mostra `1 conta em operacao` com `R$ 79.300` pagos, e eu **nao consegui reproduzir** — nem na demo (que hoje da 102 contas, com o cadastro chegando a tempo mesmo com o `/parceiros` atrasado em 3s de proposito) nem em base nenhuma de producao: ninguem tem 39.861 apostas, custo total de 79.300 nem conta de R$ 800. Sem saber de qual tela e o print, mexer na regua seria chutar.))

_Anterior: 2026-09-14 (sessao 360: **auditoria dos FILTROS do dashboard, aba a aba.** Nasceu de um print da aba Tipsters com o relato *"o filtro de Tipster esta mto desatualizado. Falta dezenas de nomes"*. **Eram SEIS defeitos, e nenhum deles da erro: todos produzem uma lista que PARECE inteira.** (1) **A lista de opcao congelava no primeiro paint.** `buildHTML` roda uma vez so; com cache local ele monta as opcoes com o dado CACHEADO, e quando o feed fresco chega o `loadData` repintava a view sem tocar em seletor nenhum. Numa aba aberta por dias, todo tipster, casa, esporte ou conta novo ficava invisivel em TODOS os filtros enquanto os cards, que leem `DADOS` ao vivo, seguiam mostrando ele. "Atualizar dados" tambem nao refazia. Mesma familia da invalidacao de `_filterCache` (s322): a lista muda por FORA de quem a pintou. Entrou `atualizarOpcoesFiltros` + `msRepintar`, que preserva selecao e busca digitada. (2) **A ordem nao era pt-BR.** `.sort()` puro ordena por codigo UTF-16 e joga minuscula e acento para depois do Z: medido, **63 dos 76 tipsters do Feca fora do lugar**, com `deLucca`, `eSoccer LBB`, `eSports LG` e `fullpicks` exilados atras de `Zora`. Entrou `cmpNome`, um comparador so para os cinco eixos. (3) **NENHUMA busca por nome ignorava acento**, em 10 superficies. Medido na base inteira: 59 dos 334 tipsters, 10 dos 39 esportes, 45 das 474 contas e 3 das 98 casas tem acento. Quem digitava `criquete`, `tenis`, `formula 1` ou `araujo` recebia ZERO, e **lista vazia na tela nao se distingue de "nao existe"**. Entrou `dobra()`, que existe duas vezes porque o dash e a Extracao sao DOIS documentos. (4) **O autocomplete cortava em 50 calado**: com 76 tipsters (Feca) ou 111 (realtrial), 26 nomes nao existiam para quem rolava sem digitar. Teto foi a 200 e passou a DIZER quando corta. (5) **O filtro de Fornecedor da Custos (previa) nascia do BILHETE**, numa tela de custo: 26 contas ativas cadastradas sem nenhum bilhete e 4 fornecedores so no cadastro ficavam invisiveis. Virou cadastro uniao base. (6) **Tipsters & Metodos listava so o cadastro** enquanto Custo de Tipsters lista a uniao. A causa e que `garantir_tipster` cria o perfil quando o tipster e atribuido EDITANDO um bilhete, mas **nao roda no `/salvar`** (IA, bot, imports): tipster vindo do bot dava para cobrar e nao dava para configurar. Zero casos medidos hoje, entao e blindagem. Abrir o box passou a criar a linha, porque o editor precisa de um `id` e sem ele a tela dizia "Tipster nao encontrado no cadastro". **DECISOES DO FECA, aprovadas com os numeros na mesa:** eixo **Tipster** entrou em Esportes, Bookies, Fornecedores e Metricas (os dois descrevem a APOSTA, entao ou recortam juntos ou nenhum recorta), e eixo **Operador** entrou na Custos (previa), onde a tela aplicava metade da regra. **E o eixo novo trouxe um efeito que a sessao vizinha viu antes de mim:** com Tipster em Bookies, o drill poe P/L do recorte ao lado de um custo que NAO recorta por tipster. Consertado pela regra da Caixa, sem mexer em numero nenhum: a TELA DIZ o corte. O aviso dispara para ESPORTE tambem, e aquele buraco ja existia. **GATES:** `tests/js/opcoes_filtro.mjs` + `tests/test_opcoes_filtro.py`, **11 de 11 mutacoes detectadas**, mais dois testes de FORMA (o feed fresco chama a repintura, e os seis eixos estao nela por LISTA e nao por lembranca). **Duas mutacoes ficaram REGISTRADAS em vez de virar assercao inventada:** tirar `sensitivity:'base'` do `cmpNome` e inocuo sob o ICU do node, e o descarte de nome vazio do `_tmNomes` divide a linha com o `_ctTipsters`, entao mutar cairia na funcao errada. **Dois harness quebraram com o commit da busca** (`ReferenceError: dobra is not defined`) porque eles RECORTAM a funcao de producao e o recorte ficou com a chamada sem a definicao; consertados no `d155a1c`, e os dois ganharam prova da regra nova. Suite 1.077 passed. **O QUE NAO ESTA PROVADO, e fica dito:** a criacao do perfil sob demanda nao foi exercida em ambiente nenhum. O `servidor_demo` nao implementa o POST (405) e a base dele tem cobertura total, como a de producao. O que a tela provou e que o caminho comum nao quebrou. **DUAS TELAS DA AUDITORIA MORREM no proximo passo** (decisao do Feca: Custos de Contas, Custos de Tipsters e Fornecedores & Parceiros saem do menu na Fatia 5), entao o achado de que as duas de custo nao tem barra de filtro nenhuma nao virou pendencia, e o eixo Tipster que entrou no Fornecedores sai junto com a tela. **COORDENACAO: a sessao vizinha (custos) e esta editaram os MESMOS arquivos o dia inteiro, e os dois erros que cometemos estao medidos.** (a) **O `git show --stat` NAO pega trecho alheio dentro de arquivo compartilhado** - ele lista `dash/index.html` como "um arquivo que eu editei", e esta certo, porque o hunk do outro esta DENTRO dele. Foi assim que ela levou dois bumps meus sem ver e que eu escrevi no corpo do `91f95fa` que tinha levado dois dela quando nao tinha levado nenhum. O que pega e `git show <sha> -- <arquivo>`. **O invariante #8 do `CLAUDE.md` manda conferir com o comando que nao detecta**, e trocar aquela linha ficou como proposta no BACKLOG, esperando o Feca. (b) **Bump de `?v=` so vale junto com o codigo que ele anuncia.** Dois bumps subiram no meu commit antes do codigo deles, e quem carregasse a pagina naqueles minutos guardaria o JS velho sob a chave nova, permanentemente. Bump adiantado e pior que bump nenhum. **PROXIMO PASSO:** nada aberto desta frente. A proposta do invariante #8 esta no `BACKLOG`.)

_Anterior: 2026-09-14 (sessao 359: **a `Dupla` do rodape sumia quando o cupom nao tinha bloco — o Soh Props planilhou 2 apostas de 3, e o aviso culpou o print.** Relato do Feca sobre o bilhete #454 (14/09, bet365): *"considerou a primeira linha, considerou o N/A da segunda, mas nao considerou os 0.25 da dupla"*. O print traz **duas simples soltas, cada uma com a odd DELA** (17,00 e 6,00) e o rodape `Dupla 102.00`; a legenda dizia `0.5u / 0u / 0.25u`. Saiu com 2 apostas e o aviso *"a legenda tem 3 linha(s) de aposta simples e o print tem 2 selecao(oes)"*. **A MONTAGEM NUNCA ESTEVE QUEBRADA, e medir isso foi o que evitou consertar o lugar errado:** simulando o bilhete com `acumulador: {Dupla, 102}` saem as 3 apostas e **zero aviso** — 2 selecoes com 3 linhas fecham o portao 3 (`nLinhas === sels.length + 1`) e 17 x 6 = 102 fecha o portao 4. `encaixarAcumulador` nunca foi chamada: **a VISAO devolveu `acumulador: null`**. **A CAUSA estava em DOIS textos de prompt, e os dois negavam o que o print mostrava:** o `REGRAS_CUPOM` (`src/cupom.js`, nucleo) amarrava o rodape aos blocos (*"o ACUMULADOR sobre os blocos"*) e este cupom nao tem bloco `Criar Aposta` nenhum; e o formato de N simples dos **tres** perfis que leem cupom (`sohprops`, `rogerin`, `grego`) dizia *"NAO existe uma odd combinada unica"* — verdade sobre `oddTotal`, **falso sobre o rodape**. Somava a dica injetada (`legenda declarou N stakes -> forte indicio do formato A`), que empurrava justamente para o formato onde estava a negacao. **A REGRA GERAL, e ela e' a licao:** a regra de leitura descrevia o caso pelo ARRANJO em que ele foi medido (*sobre os blocos*, s320/s351) em vez de pelo que ele E' (*o rodape que combina as selecoes*). O arranjo virou condicao de entrada e o dado que esta na tela deixou de ser lido, calado — mesma familia do prompt de visao travado numa casa. **MUDOU SO PROMPT:** o `REGRAS_CUPOM` passa a nomear o cupom feito so de simples soltas e a dizer que o acumulador **nao depende de bloco nenhum**; os tres perfis param de negar a odd combinada e mandam o rodape para `"acumulador"`; a dica injetada do `sohprops` diz que a linha que sobra costuma ser o rodape. **NADA foi derivado por codigo:** o portao 1 continua exigindo que o PRINT declare o acumulador — sem ele, uma selecao que a visao nao leu viraria multipla fantasma. **GATE: teste novo em `test/testes.js`** (cupom SEM bloco: 2 simples + `Dupla` = 3 apostas, `idxs [0,1]`, zero aviso), mais o caso inverso (sem o rodape no print a 3a stake **nao** vira dupla e a divergencia sai como aviso) e o **gate de PROMPT**, que e' o que segura o defeito de verdade: a montagem passaria verde com o texto antigo, entao o assert e' sobre o `REGRAS_CUPOM` e sobre o `SYSTEM` dos tres perfis. **7 de 7 mutacoes detectadas** (as 4 de texto e as 3 de codigo: acumulador perdido em cupom sem bloco, portao 3 afrouxado, portao 1 removido). Suite do bot verde. Commit `04dffea` em `Downloads/BOTS/sharpen-bot`, branch `master`, deploy automatico; `git show --stat` conferido, nenhum arquivo da sessao vizinha junto. **ETIQUETA:** o repo do bot tinha `src/atualizar.js`, `src/casas.js` e `src/perfis/zora.js` modificados por outra sessao — `add` por nome e no MESMO comando do `commit`, invariante #8. **HIGIENE DE DOC:** o bloco da s357 saiu da janela deslizante para `docs/historico/HISTORICO_s300-s327.md` (o STATUS estava em 49,4 KB com teto de 50), e o indice e o cabecalho da particao foram atualizados. **Os 2 FAIL do `check_docs.py` seguem herdados** (CLAUDE.md acima do teto e as 223 copias de STATUS/HISTORICO no `Backups/`), nenhum criado aqui.)



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
