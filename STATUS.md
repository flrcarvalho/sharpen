# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-09-06 (sessao 328 - **a Pinnacle chama o PUSH de "DRAW", e o rotulo desconhecido virava pendente eterno.** O bilhete `3117191609` (Aguila 0.0 no 1o tempo contra o Alianza, 1:1 no intervalo, R$ 408) liquidou como REEMBOLSADO na casa e ficou com "?" na grade. A tela mostra "Decidido / REEMBOLSADO" e `Vitoria/derrota 0.00`, mas o rotulo CRU que a API devolve e `DRAW` - que nao estava no de-para do `formatTicketPN`. O bloco saia `Status: DRAW (a conferir - nao liquidar automaticamente)`, **a IA obedeceu a instrucao** (e ainda registrou no RAIO-X que o P/L 0,00 indicava reembolso, sem poder agir) e o backend gravou `aberta`. Nao foi a IA errando: foi a extensao mandando nao liquidar. Duas travas, e a segunda e a que importa: `DRAW`/`TIE` entraram no de-para, e **por baixo dele** ficou a rede do DINHEIRO - resolvido + rotulo desconhecido + P/L exatamente 0 => retorno = stake => V, pelas cinco formulas de `_veredito_do_retorno` lidas ao contrario. Fecha a familia inteira: o proximo nome que a casa inventar para push ja nasce coberto. Com P/L != 0 o rotulo desconhecido continua indo para a IA como "a conferir" - inferir W/L de um nome que ninguem conhece e chute. Provado por mutacao: tirar `DRAW` PEGOU, tirar a rede PEGOU, e as duas juntas reproduzem o bug palavra por palavra. Uma 3a mutacao ESCAPOU e esta anotada no caso como inocua - o `!t.aberta` dentro do `plZero` e defesa dupla, quem decide a aberta e o `if (t.aberta)` de cima. SharpenUp 0.7.7; a linha presa fecha sozinha na proxima captura, sem script no banco.)

_Anterior: 2026-09-06 (sessao 327 - **ligar a Caixa no meio da captura nasce com a divergencia que ela existe para denunciar.** A conta `Betnacional / renanfernando01 [Richard]` projetava R$ 3.195,83 e a casa mostrava R$ 4.558,09. `abertas_corte` e um retrato do que o SHARPEN SABIA naquele segundo, nao do que a CASA TINHA: a Caixa foi ligada as 03:17:32, o /salvar so gravou as 3 abertas (R$ 600,00) as 03:18:19, e a conferencia das 03:18:35 mediu projetado -599,00 - o Ajuste entao cimentou o erro em +R$ 600,00. Junto veio um segundo defeito, independente: a captura devolveu a multipla do Falkirk SEM a 11a coluna, e a Migracao B do UPSERT (que adota linha sem codigo) exige `odd` identica - "14" nao e "14,00" -, entao o bilhete liquidado entrou como linha NOVA e a velha ficou aberta para sempre. A diferenca de R$ 1.362,26 e exatamente +1.662,26 (retorno da aberta no corte que a Caixa nao conta) -300,00 (Falkirk descontado duas vezes), conferido contra a casa bilhete a bilhete no Chrome - 11 cards, 11 linhas, zero pendente. Corrigido por `scripts/corrigir_caixa_fantasma_s327.py`: disponivel 4.558,09, divergencia 0,00. **Nenhum defeito na exportacao da Betnacional.** Os DOIS defeitos de produto foram corrigidos na mesma sessao: a Migracao B do UPSERT passa a comparar a odd pela regua do sistema (_norm_odd, extraida em chave_orfa), e a aposta que nasce aberta com captura anterior a ativacao entra sozinha no abertas_corte. Gates provados por mutacao (6+1+1+1+2 vermelhos), com gate proprio para a LIGACAO no harness de DB. Suite 748 passed, 30 skipped. Backup em `Backups/s327-caixa-betnacional-fantasma/`.)_

_Anterior: 2026-09-06 (sessão 325 — **8º tipster público: `Grego Tips - VIP`, e a fonte externa é o gate mais forte que a planilha tem.** Conta `gregozxrd` aprovada no `/admin`; 956 apostas importadas (01/08 → 01/09/2026, `GV202608-1` … `GV202609-32`), 12 contas `Padrão`, uma por casa. A base é quase monomodal como a do Soh Props — **prop de jogador de futebol** (Chutes 472 · Anytime 229 · Múltipla 120 · Desarmes 30 · Faltas 29 · Assistência 25). **O que valida este import não é a conferência interna: é o fechamento que ELE publicou no canal em 01/09** (`924 apostas · P/L +127,84u · ROI 13,02%`), contra o qual o derivado dá **924 · +127,73u · 13,00%** — a diferença de 0,11u é o arredondamento a centavo da coluna `Ganho` acumulado em 267 vitórias. A reconciliação interna (P/L derivado × coluna `Lucro`) fecha em **0 divergências nas 956**. **As 6 linhas sem casa saíram do export do Telegram, não de uma decisão:** as mensagens de 01/09 dizem Bet365 (msgs 938 e 940) e Betano (msg 942), e o script **ABORTA** se aparecer linha sem casa fora do mapa citado — casa chutada não dá erro, dá conta paralela. Três leituras de categoria não eram óbvias e estão medidas: **`<Nome> +2 Gols` é `Anytime`**, não `Gols` (§3 põe marcador 2+ na família Anytime; as odds de 11 a 81 e a escada do canal — `Tresoldi Anytime` + `Tresoldi +2 Gols` — confirmam), **`25%`/`50%` no título é odd TURBINADA** e não mercado (ele escreve a conta no canal: `2.02 + 25% = 2,27@`), e **` e ` separa PERNAS** em 12 títulos que combinam sem dizer "dupla". **O `%` tem DOIS papéis nesta fonte** e por isso a categoria lê o texto já limpo: em 2 títulos o `0.50%` é a própria STAKE vazando, e lida como turbinada ela transformaria duas apostas de Chutes em bet builder; a limpeza só corta o sufixo quando o número **é** a stake da linha, que é o que mantém `cruzeiro -1` (handicap, stake 2,50) intocado. Prefixo **`GV`**, conferido com `LIKE` sobre a coluna inteira: `GR`, `GT`, `GG`, `GX` e `GP` estão todos ocupados por **código NATIVO da bet365** (`GR3383912251I`), que um regex ancorado em `XX<aaaamm>-<n>` não enxerga (regra da s316). **`Betsson` é casa nova no banco** e entrou nos 4 mapas de favicon, com o domínio MEDIDO no link do canal (`betsson.bet.br`), não deduzido do nome. Anotado e **não resolvido**: 18 linhas `Nome N+` sem mercado (nem o canal diz qual) vão para `Player Props`, nunca para o total do esporte. **`SOA` eu havia lido como `Chutes no Gol`, e estava ERRADO** — perguntado, ele respondeu no mesmo dia: é **"score or assist", marcar OU assistir**, e as 5 linhas foram para `Player Props` junto com o `G/A` do mesmo arquivo (base reimportada; o script é idempotente por `origem='import'`, reconciliação segue em 0). A inferência era razoável e ainda assim falhou — `SOA` e `SOT` aparecem na MESMA escada, os dois pareados com `Anytime`: **vizinhança tipográfica não é significado**, e o que fez a pergunta acontecer foi ela estar marcada como inferência declarada no relatório em vez de passar como fato. **E o ATRASO DO CANAL foi planilhado a partir dos PRINTS:** ele parou de registrar no tracker na msg 969 (01/09 22:04), e daí até a última do export são **79 mensagens / 196 linhas**, agora em `GV202609-33 … -228` (base do dono: 1.152 bilhetes, 83 em aberto — sem marca entra sem resultado e ele completa à mão). A legenda dá stake e marca; **o print dá odd, seleção e confronto**, e 67 das 196 linhas (34%) têm legenda CEGA (`1.50%`, sem nome) — sem a imagem elas não existiriam. O pareamento stake↔seleção, que é onde isso erra em silêncio, tem três conferências e todas foram usadas: **a caixa de valor do print traz o R$ igual ao `%` da legenda**, a escada de odd, e **o nome MANDA sobre a posição** (msg 986: legenda `+2/+4/+3` fora de ordem contra print em ordem — parear por posição erraria duas das três). O gate que não depende de eu ter lido certo: as marcas contadas por regex no export (`❌ 73 · ✔️ 40 · ⌛ 15 · sem marca 68`) fecham exatas com a leitura dos prints (73 L · 40 W · 83 abertas), **4 de 5 mutações pegas** — e a que escapa está escrita no código: trocar a STAKE passa reto, o gate conta marcas e linhas, não valor. Descrição no formato do MASTER, com a forma da linha seguindo a CASA (Betano discreto `3+ Chutes`, bet365 contínuo `Over 2.5 Chutes`). **`origem='extracao'` e idempotência por FAIXA DE CÓDIGO** — com `origem='import'` um reimport do tracker levaria as 196 junto, em silêncio. Ids conferidos por `getChat`: canal `-1003928624343` (`channel`, bot **administrator**) e apoio `-5577016989` (`group`, bot **membro**, sem migração para supergrupo — a armadilha da s316 não se aplica). **Renomear o apoio para `Apoio - Grego` falhou** (`not enough rights to change chat title`) e não foi insistido: o bot precisa ser admin ali, ou o Feca renomeia na mão. Suíte: **717 passed, 26 skipped**. `data.js?v=18`. Backup em `Backups/s325-import-grego/`. **O perfil do bot (8º tenant) NÃO foi feito** — escopo desta sessão era só o import.)_

_Anterior: 2026-09-06 (sessão 324 — **botão que não leva a lugar nenhum confunde mais que botão ausente.** O `Entrar com Telegram` saiu do `/login`: o fluxo não conclui e o relato de uso era gente apertando sem retorno. Só o BOTÃO saiu — backend, rotas e os 27 testes do login social seguem inteiros, e o teste que trava a remoção diz como desfazê-la. `temSocial` deixou de olhar `m.telegram` para o separador **ou** não acender sozinho. 2 mutações aplicadas e 2 detectadas; 717 passed. Causa raiz do clique morto segue ABERTA (suspeito: `/setdomain` do BotFather) — não medida, o pedido era tirar o botão. Antes, s323 — **filtrar um dia zerava o Custo de Contas com o parque inteiro em uso.** A régua velha lançava o custo de aquisição num ÚNICO dia — o da primeira aposta LIQUIDADA — e só o cobrava quando o intervalo das LINHAS filtradas continha aquele dia; recorte sem aposta zerava, e conta comprada e ainda não usada não existia no mapa (entrava nos R$ 3.100 da aba Custos e nunca no KPI). Agora o custo tem JANELA DE VIDA: `ini = menor(adquirida_em, 1ª aposta)`, `fim = maior(última aposta, arquivada_em)`, e todo período que CRUZA a janela cobra o custo cheio. Colunas novas `parceiros.adquirida_em` / `arquivada_em`, editável no modal. O escopo saiu das linhas e foi para o filtro: Casa e Operador recortam o custo, Esporte e Tipster não. ⚠️ A régua NÃO é aditiva e o preço foi aceito na mesa: o P/L Líquido de um dia carrega o custo cheio das contas vivas. 9 mutações aplicadas e 9 detectadas; 716 passed. Método: o vídeo do tester tinha ÁUDIO e a tela sozinha apontava para o alvo errado. Antes, s322 — mexer no multiselect invalida o recorte cacheado: o `_filterCache` só era zerado pelo `renderPage`, e a barra própria da Base Completa não passava por ele.)_

_Anterior: 2026-09-05 (sessão 321 — **gate que confere UM campo deixa os vizinhos livres: a odd só era reconferida como efeito colateral da stake, e o RETORNO do bloco foi gravado como ODD.** O Feca abriu com o caixa da `denisesampa01` não batendo e dois bilhetes absurdos: um `HL` num Player Props de F1 (meia derrota exige linha asiática partida) e um `Under 4.0 Gols [Loiske v TP-T]` com **odd 195,53**. Medido antes de tocar em código: `195,53 ÷ 99,00 = 1,9751`, a MESMA aposta noutra conta tinha odd `1,975`, e o bloco cru diz `Status: Ganho → W (retorno R$ 195,53)` com `Odd: 1,975` **duas linhas abaixo**. A IA copiou o retorno para a coluna Odd; P/L de **+R$ 19.258,47** onde o real era +R$ 96,53. **A raiz é de desenho:** desde a s311 a stake vem do bloco, mas a odd só era recalculada DENTRO do `if` que roda quando a stake diverge (`_odd_da_stake`) — stake certa + odd errada passava reto — e o `resultado` não tinha conferência nenhuma. **A prova é o RETORNO**, contra as cinco fórmulas do `calcular_pl` lidas ao contrário (`repository._veredito_do_retorno`), agora rodando SEMPRE que o bloco prova o retorno. **O rótulo do Status não serve de fonte:** `_resultadoB3` escreve `Ganho → W` para qualquer retorno maior que a stake, meia vitória inclusive — ler o texto reescreveria como W 14 bilhetes `HW` que estavam certos. **Varredura da sombra (5.316 blocos, 20 casas): 33 linhas com dinheiro errado, Δ −R$ 19.711,29** (Feca −19.796,51 · Gabriel +69,39 · Jonathan +15,83), corrigidas por `scripts/corrigir_resultado_odd_s321.py` (ensaio por padrão, snapshot que APENSA em `Backups/s321-odd-resultado-contra-bloco/`). O P/L da `denisesampa01` caiu de R$ 28.001,63 para **R$ 8.321,45** — ⚠️ a Caixa precisa ser RECONFERIDA, a conferência registrada não se recalcula sozinha. **Três armadilhas medidas, todas load-bearing:** (1) a Betfair mistura BR e EN no mesmo bloco (stake `300,00`, retorno `1,642.38`) e um parser BR lê 1,64 e destrói 5 odds certas → `_num_bloco` decide pelo ÚLTIMO separador, e **um separador só é sempre decimal** (a regra `3 dígitos = milhar` faz `1,775` virar 1775); (2) **correção humana manda** — 3 bilhetes Betano em que alguém inverteu `W→L` e `L→W` no mesmo minuto são PULADOS pelo script (o gate em extração NÃO tem essa trava, e `resultado` nunca foi congelado pelo UPSERT: recaptura desfaz a edição); (3) só se escreve onde o **dinheiro** muda — piso de R$ 1,00, senão a 'correção' troca `1,925` pela dízima `1,925087108`. **GATES:** `tests/test_odd_resultado_determinista.py` (17 testes, **5 mutações aplicadas e todas pegas** — 2 escaparam na 1ª rodada e o defeito era do teste, registrado no cabeçalho junto com a mutação INÓCUA do lookbehind `(?<!potencial )`), suíte inteira verde (**699**), e **replay do gate na sombra real**: reproduz sozinho as 33 correções do script e mexe em **3** dos 5.316 blocos — exatamente as 3 de edição humana, zero falso positivo. **Bug meu, achado pelo replay e registrado:** o script pulava em silêncio odd truncada com reticências (`1,45070184...`), porque só o `_num_or_none` do repo faz `.rstrip('.')` — 1 bilhete ficou de fora da 1ª aplicação e entrou na 2ª.)_

_Anterior: 2026-09-05 (sessão 320 — **o cupom tem DOIS NÍVEIS, e agora isso é do núcleo do bot, não de um perfil.** Print do Soh Props (Betano, bookingcode `AAUKTQUQ`): dois blocos `Criar Aposta` de 2 pernas cada, com odd PRÓPRIA (12,50 e 7,40), e o rodapé `Dupla = 1 · 92,50` combinando os dois — três apostas, legenda `0.5u / 0.5u / 0.25u`. O bot respondeu **"⚠️ Li o print mas não consegui montar nenhuma aposta"**, e a causa foi provada por replay antes de tocar em código: a regra do bet builder manda `odd: null` por perna (certo — a casa não precifica perna), a montagem consome perna por perna e `if (!odd) return` dispara três vezes. **O pedido do Feca foi que isso valesse para TODOS os tipsters, não virar mais uma ferramenta exclusiva** — e a queixa tem número: o mesmo problema já tinha sido resolvido **três vezes separado** (`reidocriquete.reconciliar` na s272, nascida do bilhete KTO que também saiu com zero apostas; `rogerin` na s306, 22 pontos de `betBuilder`; `sohprops` na s316, 20 pontos, cópia do anterior), e as três compartilhavam o **mesmo ponto cego**: um bet builder por cupom. **`src/cupom.js`** passa a ser o lugar único: `REGRAS_CUPOM` (o parágrafo de prompt que os três reescreviam à mão, agora com `bloco`/`oddBloco`/`acumulador`), `normalizarCupom` (colapsa cada bloco numa seleção com a odd dele) e `encaixarAcumulador` (a regra do N+1 promovida do Rei do Criquete, mais o 4º portão que este print oferece de graça: 12,50 × 7,40 = 92,50 — divergiu, a odd do print manda e sai aviso). **O que NÃO foi unificado, de propósito:** `categoriaDaPerna`/`esporteDe` do `rogerin` e do `sohprops` parecem gêmeos e **não são** (um classifica Gols/Games/Pontos/Sets multi-esporte, o outro Faltas/Desarmes/Impedimentos de props de futebol) — unificar mudaria a classificação de um dos dois em silêncio, trocando a ferramenta exclusiva por um erro compartilhado. Genérico é a leitura do CUPOM (propriedade da casa); a gramática da LEGENDA continua de cada tipster. **Duas armadilhas achadas ao ligar, as duas de perda calada:** o colapso só vale de **dois** blocos para cima — colapsar um bloco só mudaria a descrição planilhada e apagaria os botões de perna do painel (`aplicarMarcas` indexa SELEÇÕES); e o `pernasDe` do `rogerin` usa `.pernas` para reconhecer a forma antiga de registro dele (≤ s306), então `ehBloco` exige o **número** do bloco — sem isso um cupom de dois blocos seria lido como registro velho e o **segundo bloco sumiria sem erro nenhum**. **GATES:** `npm test` inteiro verde (era 1.024 asserts; nada mudou onde não havia bloco múltiplo) · gate novo exercendo a montagem nos **3 perfis** (as três chegam em `0,5u@12,50 · 0,5u@7,40 · 0,25u@92,50`, com o acumulador ligado aos dois blocos por `idxs`) · **mutação 8 de 8** (colapso desligado · `ehBloco` sem o número do bloco · portão do N+1 removido · colapso de bloco único · categoria do bloco deixando de ser Múltipla · ramo do acumulador removido no `sohprops` · `multiBloco` removido do `rogerin` · `pernasDe` desembrulhando o bloco). O `zora` ficou **fora e por medição**: a visão dele não lê cupom nenhum — só acha a odd de uma seleção já declarada na legenda —, então não há onde encaixar as regras; o `passatips` é sem visão. **O que o gate NÃO cobre, e está escrito nele:** que o MODELO leia `bloco`/`oddBloco`/`acumulador` de um print de verdade — a visão é dublada, e isso só se mede mandando o print. ⚠️ O bilhete de hoje continua **não planilhado**: a correção vale do próximo em diante. Backup em `sharpen-bot/Backups/s320-cupom-dois-niveis/`.)_

_Anterior: 2026-09-05 (sessão 319 — **o calendário da Visão Geral passou a seguir os filtros e a dizer o próprio escopo.** O Feca abriu com dois P/L na mesma tela: com o período em MTD (01/09 → 05/09) o KPI dizia `+R$ 12.033,68 · 483 apostas` e o calendário logo abaixo dizia `+R$ 11.833 · 487 apostas`. **Os dois estavam certos** — o cartão soma o MÊS fechado, os KPIs somam o PERÍODO —, e a diferença eram **4 bilhetes com data de EVENTO depois do corte**: três voids da Bet365 (P/L 0, mas contam na contagem) e uma perdida de R$ 201 no GP da Itália. Todos já resolvidos antes do jogo, que é o que `bilhetes.data` ser a data do evento permite. Medido contra o banco antes de tocar em código, e as três casas fecham nos centavos (turnover 81.377,66 × 81.578,66). **Duas correções.** (1) `renderOvHeatmap` passava `DADOS` **cru** e por isso o cartão ignorava também Esporte, Casa, Tipster e Operador — escolher um tipster mudava os KPIs de cima e não mudava nada no calendário; agora ele recebe `filtrarSemData('overview')`, o mesmo helper do ROI Mensal (os quatro filtros valem, só o corte por data não — o cartão é um calendário de mês, com nav própria). Junto, o mês selecionado entrou na lista de meses do `mkCalendarHeatmap` mesmo quando o filtro o esvazia, senão o `indexOf` dá −1 e as setas ‹ › travam num cartão em branco. (2) Quando o período não cobre o mês inteiro, a barra do cartão **diz** o que ficou de fora, com contagem e P/L em `fmtPL`. Essa nota **não é um estilo novo**: a `.apf-nota` da Base Completa (os KPIs que não seguem o filtro de resultado) é o mesmo papel, então ela subiu para `.nota-escopo` compartilhada em vez de ganhar um gêmeo — CLAUDE.md §8. Gate novo `tests/test_calendario_escopo.py` + `tests/js/calendario_escopo.mjs`, recortando o `mkCalendarHeatmap` e o `filtrarSemData` reais; **provado por mutação, 9/9 detectadas**. Suíte inteira verde (682), check-tokens verde, e a tela foi renderizada headless contra a base real do Feca antes do commit — as três leituras (sem filtro, só DartsVader, só Peixe) batem com o KPI ao lado. **Nota de método:** para tirar esse print eu subi o `app.main` local contra o `DATABASE_URL` de produção e ele acordou o scanner e o extrator — matei em minutos e conferi que nada anômalo foi escrito (o que apareceu era captura real do Jaao26 em curso), mas o certo é o que ficou: servidor **só-leitura**, servindo os estáticos e um `dashboard_rows` lido uma vez. Detalhe em "Ainda aberto da sessão 316".)_

_Anterior: 2026-09-05 (sessões 316 e 318 — **7º tipster público no ar: `Soh Props - Vip`**, 7.276 apostas importadas e o bot dele como 6º tenant. Junto vieram a página `/bot` com o manual de operação e um dia de correções tiradas do uso real. Detalhe em "Ainda aberto da sessão 316".)_

_Anterior: 2026-09-04 (sessão 318 — **`/bot`: o manual de operação do @sharpenbetbot nos grupos**, página pública e standalone (`app/static/bot.html`), no molde da `/extensao`. Três partes: o **dia a dia** (uma linha de stake por aposta, link da casa, data+hora; marcar é **editar a própria mensagem**), os **13 comandos** com a sintaxe real recortada do `index.js`, e o **passo a passo de colocar um tipster no ar** — os oito passos que a s316/s317 mostraram serem necessários, com as duas armadilhas que morderam em produção destacadas: **grupo que vira supergrupo troca de id e deixa o bot SURDO** (sem erro nenhum) e **contador não semeado engole a aposta** pelo UPSERT. Duas distinções que a página existe para fixar: `🔁` (void da casa, FICA na planilha como V) × `/anular` (a aposta nunca valeu, SAI), e `/repostar` (só o texto do post) × `/redescrever` (ESCREVE na planilha por PATCH). Sem R$ nenhum, então o `UI_REFERENCE §5` não se aplica; a Escada de Tinta sim — `--ink-mute` usado uma vez só, em 13px, no rodapé. Linka o `/static/tokens.css` sincronizado em vez de redeclarar cor, que é o que a `extensao.html` faz e é o desvio, não a regra. check-tokens verde, zero cor literal, zero script inline, e a tela foi renderizada headless de ponta a ponta antes do commit. **Revisada no mesmo dia, com três correções do Feca:** o `👽` SAIU do padrão — ele não é do Sharpen e o próprio Soh Props passa a usar o `🔁` (o código segue **aceitando** o alien de propósito: são 82 apostas de hábito no histórico dele, e se o dedo escorregar é melhor a aposta ser marcada do que ficar aberta em silêncio — documentar é uma coisa, tolerar é outra); o `/anular` ganhou destaque na nota que o separa do `🔁`; e **a seção de pôr um tipster no ar saiu da página pública** — ela é de quem opera, não do tipster, e foi para `docs/GUIA_BOT_TIPSTER.md` em vez de sumir. **E o `/nova-ui` foi rodado DE VERDADE depois de o Feca cobrar** — eu tinha invocado a skill e pulado o passo 1 (ler `UI_REFERENCE` e `pack/CLAUDE.md`), decidindo por dedução que "não tem dinheiro, §5 não se aplica", que é exatamente o argumento que a memória diz não dispensar. Lendo, o checklist pegou **cinco** coisas: faltava o **grid de fundo** (`§3` e `SHELL_SPEC §0`, idêntico nos dois apps) e o **estilo de scrollbar**; o `.card` usava `--r-lg` onde o `§4` pede `--r-sm/md` e não tinha `--shadow-card`; havia **espaço fora da escala `--sp-*`** (38px, paddings de 1px/2px); e o `.nota.aviso` virou CSS morto ao remover a seção interna — âmbar sem aviso é cor sem semântica (`§1`). O único ponto em que a página já estava certa por acaso é o conflito conhecido `UI_REFERENCE §2` × Escada de Tinta na cor do eyebrow: o §2 pede `--ink-mute` e a Escada manda `--ink-soft`, que é o que está lá. **Mais três, e essas eram de MARCA, não de CSS:** o tile do cabeçalho tinha um 🤖 e um wordmark "SharpenBot" que eu inventei — o `pack/CLAUDE.md §2` lista **"❌ emojis decorativos"** como regra inegociável e o §5 diz que a marca tem símbolo próprio, que não se substitui; virou o lockup de verdade (`brand-sharpen/blade/lockup-dark.svg`), como a landing e o login. E **nenhum título estava no padrão**: o `SHELL_SPEC §2` define `.pagehead-title` como `--text-xl` (22px), weight 800, ls `-.035em`, lh 1 e **gradiente azul em clip** — o meu era 28px chapado em `--ink`, e o `h2` vinha em 22px, ou seja no mesmo peso do título (dois níveis iguais não são hierarquia). Nenhuma das três apareceria em grep nenhum: só lendo.)_

_Anterior: 2026-09-04 (sessão 317 — **filtros da Base Completa, agora numa barra SÓ.** A primeira volta entregou os filtros novos num segundo cartão embaixo dos KPIs, com a barra da página lá em cima; o Feca leu a tela — *"faltou filtro para Tipster, Casa e Esporte"* (existiam, estavam no outro cartão) e *"alguns filtros ficaram lá no topo, bem confuso"*. **Partido em dois cartões, o de cima sai do campo de visão e a tela parece não ter o filtro que tem.** Hoje é um cartão com três zonas — carteira (período/esporte/casa/tipster/conta/operador), aposta (chips de resultado com contagem + faixas de stake/odd/P/L) e texto —, montado das MESMAS peças que as outras 8 telas usam (`buildFilters` foi quebrado em `_grupoPeriodo` e cia.). **Achado sobre o gate:** o `/nova-ui` rodou e acertou o átomo (`.money`, tokens, Escada nos 3 critérios) — ele **não cobre composição**, que é o que quebrou. O sintoma barato: dois estilos para o mesmo papel na mesma tela. `.apf-lbl` foi excluído e a barra reusa `.filter-label`, que subiu para `--ink-soft` 9,5px; junto foram `.btbl-th` e `.btbl-counter`, os dois desvios que a s317 tinha só registrado. **A decisão que continua valendo: o desfecho corta a TABELA, não a régua** — filtrar `W` faria o Win Rate virar 100%, então os KPIs leem `apostasKpiRows` e a tela avisa enquanto o filtro está ligado. Aposta aberta sai de qualquer faixa de P/L: o zero dela é ausência, não valor. Resultado ordena em ordem semântica (`W · HW · V · HL · L`), nunca alfabética. Gates provados por mutação: **17/17** no `.mjs` que executa o código recortado, **10/10** no pytest estrutural.)_

_Anterior: 2026-09-03 (sessão 314 — **A Caixa Inteligente: a conta agora diz quanto DEVERIA ter na casa, e acusa quando não bate.** Pedido do Feca, e o motivo é fraude, não contabilidade: terceiro que saca de pouquinho numa conta de alto turnover passa despercebido por semanas. A tela de Extração ganhou uma coluna de 300px à direita dos tiles e da captura (dentro da `.colmain`, sem encostar no rail; a grade segue ocupando a largura inteira), e o Painel de Contas ganhou a banca consolidada com o saldo casa a casa. **A conta é `banca = saldo inicial + preso no corte + depósitos − saques ± ajustes + P/L`, `disponível = banca − em aberto`** — e é o *disponível* que a casa mostra na tela, então é contra ele que a conferência bate. Vocabulário reusado da Polymarket (*Saldo Disponível · Saldo em Aberto · Saldo Total*), que já falava isso dentro do produto. **A METADE DIFÍCIL É O CORTE, e ela não estava no desenho aprovado — apareceu ao escrever a matemática:** toda aposta mexe no saldo DUAS vezes (−stake ao apostar, +retorno ao liquidar), e para a aposta que já estava ABERTA no dia em que o operador informa o saldo só a segunda ponta cai dentro da janela — o stake saiu ANTES, logo não está no saldo informado, e volta INTEIRO ao liquidar. Contar só o P/L dela deixaria **toda conta com aposta viva no dia da configuração** (ou seja, praticamente todas) com uma divergência permanente do tamanho desses retornos: a auditoria acusando a si mesma para sempre. Por isso o lançamento `inicial` grava `abertas_corte` — os ids dos bilhetes abertos naquele dia —, e o teste que trava isso tem uma **contraprova** (`test_sem_a_lista_a_aposta_velha_some_e_o_saldo_fica_baixo`) mostrando o erro que a lista existe para impedir. **A conferência REGISTRA, não absorve:** ela grava o `projetado` do momento (nunca recalculado contra a projeção de hoje, que já inclui aposta que nem existia lá atrás) e o box continua acusando até o operador lançar o que faltava ou clicar em "Lançar como ajuste", que grava um Ajuste **nomeado** e visível no extrato. Rebaselinar em silêncio apagaria a trilha do único caso que a função existe para pegar. Estado da conferência em 4 valores — nunca · confere · divergente · **reconferir** (houve lançamento depois de uma conferência que não bateu: o número velho já não descreve a conta, mas também não se pode dizer que bate). **DECISÕES:** dinheiro **por conta**, chaveado por `parceiro_id` e não pelo par (casa, parceiro) em texto — `casa` já é texto em 7 tabelas e mover conta de casa (s312) teria de propagar para cá também; a lixeira leva os lançamentos no MESMO snapshot do `DELETE ... RETURNING` dos bilhetes (restaurar a conta e perder o dinheiro seria a lixeira meio-cheia); **Polymarket fica de fora** (ela lê saldo real on-chain — estimar por cima do medido cria um segundo número para a mesma pergunta); escrita por `dono_efetivo` como toda rota de dados — **a proposta de restringir ao dono foi ABANDONADA na medição**: quem usa "ver como" é o supervisor olhando a base do operador, não o contrário, então o critério extra só bloquearia o supervisor e criaria uma regra de acesso órfã. **CONTA SEM CAIXA NÃO VIRA ZERO:** entra como "—", fica fora de toda soma e o painel diz quantas faltam — total que engole conta desconhecida mente com cara de exatidão (é a família do `DADOS só tem aposta liquidada`). **MARCA (`/nova-ui` item a item):** saldo é a **3ª variação documentada do `.money`** (UI_REFERENCE §5.1, escrito nesta mudança) — 2 casas como o stake, **decidido com o Feca**, porque o número existe para ser conferido contra o extrato e o centavo é a divergência que se procura; **saldo não tem cor** (verde/vermelho é semântica de resultado — saque não é prejuízo), o sinal fica no `.money-sign` neutro com minus U+2212, e a única linha colorida da caixa é o *Resultado*, que usa o `fmtPL` de sempre; **divergência é `--warn`**, nunca `--neg`. Escada de Tinta conferida nos 3 critérios: nenhum `--ink-mute` abaixo de 10px, nenhum `opacity` sobre tom apagado, nenhum nome próprio apagado. **GATES:** suíte **646 passed, 23 skipped** (era 617) · `check-tokens` verde · **mutação 9 de 9** (`scripts/mutar_caixa.py`: preso no corte fora da banca, corte ignorado nos lançamentos e nas apostas, disponível sem descontar o aberto, lista de abertas ignorada, divergência recalculada hoje, staleness sem olhar a data, tolerância afrouxada, saque somado) · `tests/js/caixa_front.mjs` **recorta** `fmtSaldo`/`_cxIso` do `index.html` real, com 2 mutações provadas · **a tela foi ABERTA em navegador headless** contra o `servidor_demo.py`, nos três estados (desligada, confere, divergente) e no Painel: caixa em 300px a x=782, grade **inteira** em 1.056px, 8 tiles, `rgb(224,162,26)` no aviso, **zero `pageerror`**. **E foi o navegador que pegou o único bug real:** o campo de data nascia com `dd/mm/aa` e o parser exigia 4 dígitos, então o primeiro lançamento seria recusado com "Data inválida" **num valor escrito pela própria tela** — `node --check` e a suíte passavam. Hoje há `_cxDataBR4` para campo, `_cxDataBR` para leitura, e o gate JS testa a ida e volta nos **366 dias** do ano. O `servidor_demo.py` ganhou as rotas da Caixa **importando o `_caixa_projetar` de produção** em vez de reimplementá-lo — projeção errada num print de venda é pior que print nenhum. Backup em `Backups/s314-caixa/`. Dois desvios **PRÉ-EXISTENTES** anotados e não tocados: `.pagehead-eyebrow` e `.rail-c .rail-k` usam `--text-nano` (9px) em `--ink-mute`, abaixo do piso da Escada — é mudança separada, e nenhuma das duas é minha. **REVIEW DO FECA, dois ajustes:** a Caixa passou de 300 para **450px** (ele viu que sobrava espaço; 360px entre 1180 e 1620); e o **modal de lançamento nascia com rolagem horizontal e o título cortado** — print dele. Causa: `.modal-narrow` tem 400px e eu pus DOIS campos lado a lado; `1fr` não encolhe abaixo do min-content de um `<input>` (~206px), então duas colunas nunca caberiam. Os outros modais estreitos escapam disso porque empilham em coluna (`.nc-body`, `.xc-body`). Conserto: largura própria de 440px + `min-width:0` nos campos. **E o mesmo print escondia um segundo defeito**: o `.ed-data-btn` é `position:absolute` POR DESENHO (mora dentro do campo, como no `.dref-wrap` da barra de captura) e meu wrapper não era `relative` — o botão do calendário se ancorava no modal e caía fora do campo. Os dois medidos no navegador antes e depois (`scrollWidth == clientWidth`, botão dentro do campo). **E ENTÃO O 'ATIVAR' NÃO FEZ NADA EM PRODUÇÃO — e o defeito era de TIPO, não de lógica:** `valor` e `projetado` são `NUMERIC`, e o asyncpg **recusa `float`** nessas colunas (exige `Decimal`). A rota devolvia 500 e o front mandava o erro para o `#status-msg` da **barra de captura**, longe do modal — da cadeira de quem clicou, nada acontecia. Dois consertos, porque um só repetiria o problema: `Decimal(str(valor))` na gravação (a string preserva as 2 casas sem o lixo binário do float) **e o erro passou a aparecer DENTRO do modal**, ao lado do botão que falhou. A matemática (`test_caixa.py`) estava certa o tempo todo: nenhum teste olhava o TIPO do argumento — agora `tests/test_caixa_lancar.py` olha (14 casos, com um `_FakeConn` que captura os args do INSERT), e as **2 mutações** que devolvem o float são pegas. **RENOMEADA para `Caixa Inteligente`** a pedido do Feca, em tela, docs, folder e mensagem; o botão virou **Ativar Caixa Inteligente** e o modal passou a nomear a conta inteira (`Casa · Parceiro [Fornecedor]`) num subtítulo — com dois parceiros na mesma casa, só o nome da casa não diz onde se está lançando. **O cabeçalho virou GÊMEO do RAIO-X** (mesmo `--accent-2`, 11px/600/.2em, mesmo padding 16/18 e mesma borda `--line`), com `--hd-h: 54px` de piso nos DOIS: os pills aparecem e somem, e sem piso a linha subiria e desceria. Medido no DOM: topo 90/90, linha 144/144, altura 54/54, `rgb(127,178,255)` nos dois. **E o fluxo inteiro foi exercido num Chrome de verdade** — ativar → lançar → conferir, com o `servidor_demo.py` ganhando `POST /caixa/lancar` em memória só para isso: um clique que 'não faz nada' não aparece em teste de unidade nenhum. **E MESMO ASSIM FALHOU DE NOVO — o MESMO INSERT, outro argumento:** `data` é `DATE` e eu mandava `str`; o asyncpg exige `datetime.date`. Pior: o teste da rodada anterior **afirmava a string como correta**, ou seja, gravou o segundo defeito como se fosse a regra. Nas duas vezes o 500 nasceu DENTRO do driver, antes de qualquer SQL. Conserto: `date.fromisoformat(data)` e o `::date` fora do SQL (sem cast o tipo do parâmetro vem da coluna e não há ambiguidade). **O gate deixou de ser por lembrança e passou a ser por LISTA**: `test_cada_argumento_do_insert_vai_no_tipo_da_coluna` percorre os 8 argumentos de uma vez (`str, int, str, date, Decimal, str, Decimal|None, list|None`) e quebra se o INSERT mudar de forma. **E desta vez foi MEDIDO contra o Postgres de produção**, em transação com `ROLLBACK`: `date`+`Decimal` passa; as duas tentativas anteriores levantam `DataError: 'str' object has no attribute 'toordinal'`. Depois o fluxo REAL (`caixa_lancar` → `caixa_conta` → `caixa_visao` → `caixa_excluir_mov`) rodou inteiro sobre uma conta de 2.584 apostas — ativar, depositar, conferir (divergência −418,75), excluir — e o rollback deixou **0 linhas**. Afirmar sem medir uma terceira vez não era opção. **E A TERCEIRA COISA NÃO ERA BUG DE CONTA — ERA A TELA NÃO EXPLICANDO A CONTA.** O Feca ligou a Caixa na conta #748 (Superbet · ricksa03) e viu `P/L · conta −R$ 1.608,00` no tile de cima e `Resultado R$ 0,00` na Caixa logo ao lado. **Medido no banco, os dois estavam certos:** as 13 apostas são de 02/09, o corte é 03/09, então as 12 perdidas já estavam dentro do R$ 1.950,00 informado, e a 13ª (`#218127`, aberta no corte) liquidou **W com odd 12,28684** — retorno de R$ 1.228,68 sobre um stake que saiu antes do corte, exatamente o caso que o `abertas_corte` existe para pegar. Projeção correta: **R$ 3.178,68**. Mas número que parece contradizer o vizinho na mesma tela é defeito, mesmo estando certo — então a Caixa passou a **dizer o corte**: o rótulo virou `Resultado · desde 03/09/26`, `Preso no corte` virou `Abertas no corte`, e uma nota fecha o ledger — *'12 apostas anteriores a 03/09/26 (−R$ 1.608,00) já estão dentro do saldo informado — por isso ficam fora desta conta'*. `pl_anterior`/`n_anteriores` existem SÓ para essa frase e não entram em soma nenhuma (2 mutações provam). **E junto veio um defeito de verdade, do meu jeito favorito de errar:** a faixa de erro do modal aparecia **vermelha e vazia** no modal limpo — `.cxm-erro` declara `display:flex`, que **vence o atributo `hidden`** (só a folha do agente o aplica). Regra explícita `.cxm-erro[hidden]{display:none}`, medida nos dois estados no navegador (limpo: `display:none`, altura 0; com falha: `display:flex` com o texto). Gates: **665 passed**, mutação **11 de 11**, e o caso da #748 remontado no `servidor_demo` para a tela poder ser LIDA na bancada.  **E o corte ficou SEM SAÍDA pela tela:** o Feca informou o saldo com a data de hoje quando ele era de ontem, e não havia como editar — só desligar a caixa pelo extrato e ligar de novo. O backend sempre soube (`inicial` é UPSERT: apaga o anterior e recalcula `abertas_corte`); faltava a porta. Agora a **linha do Saldo inicial é o botão** — lápis, `role=button` com teclado, e o MESMO formulário abrindo pré-preenchido (valor, data e observação), com título `Editar o saldo inicial`, botão `Salvar` e o aviso de que **mudar a data recalcula quais apostas entram**. Medido no navegador: mover o corte de 03/09 para 02/09 leva a caixa de `1 liquidada / R$ 3.178,68` para `13 liquidadas / R$ 678,68` e some com a nota do corte — que é exatamente o que tem de acontecer. O texto do modal também passou a dizer que entra **tudo a partir da data, inclusive as apostas do próprio dia**: é essa frase que decide qual saldo o operador digita. **DEPOIS DA PUBLICAÇÃO, mais três do Feca.** (1) A tabela *saldo por casa* saiu: com 26 de 27 contas sem caixa, ela era uma coluna de travessões — *"desorganizada"*. O saldo foi para onde já se olha a conta: o **cabeçalho de cada casa na lista**, com o valor e uma tag que diz DE ONDE ele vem — `batido` (todas as contas daquela casa conferidas e batendo, verde), `calculado` (projetado, ainda sem conferência, neutro) ou `a conferir` (âmbar, o único aviso da lista). Casa sem caixa nenhuma não ganha nada, que é o que apaga o ruído. O **caixa total** virou a 4ª estatística do rodapé do card Contas (`R$ … · 4 de 102`), lendo o MESMO `/caixa/visao` já cacheado — dois números para a mesma pergunta é como se cria divergência sem ninguém mexer em nada. (2) **Editar movimentação pelo extrato**: lápis em cada linha, abrindo o MESMO formulário com o tipo TRAVADO — trocar um depósito em saque é apagar um fato e criar outro, e para isso existem o ✕ e o botão de lançar. `PATCH /caixa/movimento/{id}` → `caixa_editar_mov`, com duas conservações deliberadas: editar o `inicial` **refaz** o `abertas_corte` (mudou o corte, mudou quem estava aberto nele) e editar uma `conferencia` **preserva o `projetado`** — ele registra o que o Sharpen projetava naquele dia, e recalculá-lo com a projeção de hoje reescreveria o passado e apagaria a divergência medida. O extrato **reabre** ao fechar o modal, para o operador não perder o lugar. (3) A validação virou `_caixa_valida`, uma só para lançar e editar — duas regras para o mesmo fato envelhecem separado. Medido no navegador de ponta a ponta: lançar → abrir extrato → lápis → editar 500 para 1.234,56 → salvar → box em R$ 4.413,24 e extrato reaberto com o valor novo, zero `pageerror`. **E A CONTA DO GABRIEL ACHOU UM BURACO MEU.** A SportingBet dele (#684) projetava R$ 2.482,67 e a casa mostrava R$ 2.571,79 — **R$ 89,12 a mais na casa**. Medido linha a linha: os 53 bilhetes, os 3 lançamentos e o saldo dia a dia (mínimo R$ 494,37 em 01/09, nunca negativo, logo o inicial de R$ 2.000 é compatível). **Naquela conta a diferença é externa mesmo** — cashout, bônus ou saldo inicial arredondado —, que é exatamente o que a Caixa existe para achar; o ajuste já foi lançado. **Mas procurando eu achei um defeito meu, de sinal IGUAL a esse:** `data` no Sharpen é a data do EVENTO, não a da aposta. Aposta feita ONTEM para um jogo da PRÓXIMA SEMANA tem `data` depois do corte — e mesmo assim o stake dela já saiu da conta, logo já está descontado do saldo que o operador acabou de ler. `abertas_corte` filtrava só por `data < corte`, essa aposta ficava de fora e a projeção descontava o stake **duas vezes**: conta nascendo com divergência no fluxo que a própria tela recomenda. Conserto em `_caixa_abertas_ids` (pura, testável): **corte = HOJE → toda aposta aberta entra** (se está aberta agora, o stake saiu antes de agora — é exato); **corte no passado → entra o que PROVADAMENTE já existia** (evento anterior ao corte, ou linha que o Sharpen já tinha antes dele, por `criado_em`), um piso honesto, e é por isso que o modal recomenda o saldo de hoje. 4 testes novos, incluindo a **contraprova** que mostra a regra antiga devolvendo lista vazia, e 2 mutações pegas. Suíte **669 passed**. **E as caixas JÁ LIGADAS foram corrigidas por script, não por pedido ao usuário** (`scripts/recalcular_abertas_corte_s314.py`, que CHAMA o `_caixa_abertas_ids` em vez de reimplementá-lo — dois cálculos do mesmo fato divergem em silêncio). Ensaio é o padrão; a lista só CRESCE, nunca encolhe: a ativação original reconheceu aquelas apostas e o saldo informado foi lido com elas já descontadas. **Medido em 31 caixas de 5 donos: 4 estavam erradas, todas com corte = hoje** — Jaao26 `#693` (+R$ 200,00), `#691` (+R$ 400,00) e `#692` (+R$ 1.955,00, com 19 apostas abertas de fora), e Marques19981 `#720` (+R$ 200,08). Todas as correções são para CIMA, que é o sinal previsto pelo defeito. Reexecução dá **0 a corrigir** (idempotente) e a varredura de invariantes passa em toda a base (total = soma das contas · disponível = banca − aberto · aberto ≥ 0). **No dia seguinte o próprio script tentou errar, e o ensaio pegou:** rodado de novo, ele queria adotar apostas com id `241xxx` em 3 contas do Gabriel — feitas HORAS DEPOIS da ativação, cujo stake saiu depois da leitura do saldo. Adotá-las inflaria a projeção em **+R$ 10.477 que não existem**. `_caixa_abertas_ids` ganhou o parâmetro `ate` (o instante em que o saldo foi lido): na ativação é o agora e nada muda; o backfill passa o `criado_em` do lançamento inicial. Regra num lugar só, mutação pega, ensaio limpo. **Estado no fim da sessão: 39 caixas ligadas em 5 donos** (Jaao26 24, Gabriel 12, Jonathan 1, Marques19981 1, Feca 1), **zero divergência aberta** e os invariantes passando na base inteira. `app/static/landing.html` seguiu FORA do commit.)_

_Anterior: 2026-09-02 (sessão 313 — **O "Drawdown Atual" marcava R$ 0,00 com a banca no vermelho, e o "Topo Histórico" exibia um valor NEGATIVO — um topo que nunca existiu.** Relato do tester Gabriel, com print: *"quando um grupo/método começa o primeiro dia negativo, ele desconsidera esse negativo no cálculo de drawdown"*. **Duas funções descrevem a MESMA curva e discordavam de onde ela começa:** `calcDrawdownReal` (o Max Drawdown) partia de `peak = 0` — a banca no zero, antes da primeira aposta — e por isso contava o mergulho inicial e acertava; `calcTopoDrawdown` (Topo + DD Atual) partia de **`peak = -Infinity`**, então o PRIMEIRO dia virava o topo fosse ele qual fosse. Numa série que só sobe depois do mergulho, o topo passava a ser o **último** ponto e `dd = peak - acc` dava **0 por construção**. É a família do UPSERT meio-atualizado: **metade do card certa, metade errada**, sem erro nenhum aparecendo. **O alcance era maior que o relato** — não dependia de "começar negativo": bastava o acumulado atual ser o máximo da série e ainda estar abaixo de zero, ou seja **qualquer carteira, casa ou esporte no vermelho vindo de recuperação**, em 4 renders (Visão Geral + as três telas de Performance). Reproduzido 1:1 antes de tocar em código: 3 dias (−2.514 / +500 / +408,70) devolvem os **quatro** números do print do Gabriel, RF `−0,64×` inclusive. **Conserto: `peak = 0`, o mesmo ponto de partida das duas funções.** Duas consequências tratadas junto, porque um conserto pela metade seria o defeito de novo: (1) `topoData` fica **null** quando o topo é o próprio início, e os 4 renders passaram a usar um `topoSub` único que escreve **"no início da série"** — `_fmtD(null)` imprimia `atingido em —`, que o leitor lê como dado faltando; (2) a % do DD atual era `dd/peak` (% do **lucro** acumulado) e **dividiria por zero** no caso corrigido — virou `dd/(BASE_BANK+peak)`, a **mesma régua do `mddPct`** do card vizinho, então os dois percentuais lado a lado passaram a ser comparáveis (na base demo: 9,5% e 16,3%, antes 12,6% e 16,3%). Junto veio um caso de cor **novo**: com topo = R$ 0,00, o `data-state="pos"` fixo pintaria o zero de **verde** (o `fmtPL` não tem classe para revidar e o valor herda a cor do KPI) — o atributo virou condicional a `topo > 0`, e o zero sai neutro (`UI_REFERENCE §5.1`). **GATES:** suíte inteira verde (**617 passed, 23 skipped**, era 611) · `check-tokens` verde · `/nova-ui` item a item (nenhum formatador novo — `fmtPL`/`fmtPct` reusados; `.kpi-sub` é 10px `--ink-mute`, **exatamente no piso** do papel metadado da Escada de Tinta, e nenhum CSS foi tocado) · **mutação 7 de 8** em `tests/js/topo_drawdown.mjs`, que **recorta** as três funções do `app.js` real (peak=-Infinity nas duas funções, denominador antigo, subtítulo do topo=início, data invertida, `>` virando `>=` no empate, topoData virando o último dia). **A 8ª é INÓCUA e está registrada como tal:** `dd=peak-acc` → `Math.max(0,peak-acc)` — `peak` é o máximo da série e inclui o `acc` atual, então o clamp é redundante, não é buraco de teste. **E duas armadilhas de teste morderam antes de eu fechar:** o gate de leitura reprovou a função **já corrigida** por causa do próprio comentário que cita `-Infinity` (mesmo falso positivo do `test_monte_carlo_worker.py`; resolvido com o `_sem_comentarios` dele), e o gate de cor **passou verde com a mutação aplicada** — o `.{80}` exigia 80 caracteres antes na mesma linha e a do `overview.js` tem ~70, então o `findall` vinha vazio; virou varredura por linha com contagem exata dos 4 renders. **A TELA foi aberta em navegador headless nos DOIS estados** contra o `servidor_demo.py` — `node --check` é falso verde para o que vive em template literal (s296). Medido no DOM real: carteira positiva **inalterada** (topo +R$ 305.451,22 verde, com data) e o caso do Gabriel agora com **Topo R$ 0,00 neutro** (`rgb(238,242,247)`, não o mint), "no início da série" e **DD Atual −R$ 1.605,30** onde antes lia R$ 0,00; zero `pageerror`. Descoberta de bancada anotada: trocar o hash da casca **não** troca a aba dentro do iframe — quem faz isso é o `showPage` do próprio iframe, senão `#page-overview` fica `display:none` e o card sai com rect 0×0. `?v=` bumpado nos três assets (`app.js?v=40`, `overview.js?v=15`, `performance.js?v=16`). Backup em `Backups/s313-drawdown-topo-peak-zero/`. **Dois desvios PRÉ-EXISTENTES achados e NÃO tocados** (mudança separada, decisão do Feca): o `Drawdown Atual` zerado herda o vermelho do `data-state="real"` — zero deveria ser neutro pelo §5.1 —, e o `Recovery Factor` negativo sai com **hífen ASCII** (`-0,64×`) em vez do minus U+2212, porque o `fmtOdd` usa `toLocaleString` cru. `app/static/landing.html` seguiu FORA do commit — é de outra sessão.)_

_Anterior: 2026-09-01 (sessão 310, parte 3 — escrita depois da s312 de outra sessão simultânea; a numeração é da sessão que fez o trabalho, não da ordem do arquivo — **O que o dono DECLARA voltou a falar, só onde a base é cega. A ideia é do Feca, e a medição bancou.** A s289 trocou o matcher declarativo pelo de evidência e resolveu metade do problema: a base sabe do Peixe, que viu milhares de vezes, e **não sabe nada de quem entrou semana passada**. Perfil sem histórico nem entra na disputa (`sugerir` pula quem tem `cls == 0`), nunca constrói a folga, e a coluna fica vazia **em silêncio** — o dono conclui, com razão, que preencher o perfil não serve para nada. O caso que abriu: o Feca tinha `Stake Final 3` escrito no perfil do **Fusion**, a base confirma (503/403/303/203), e o Fusion era sugerido **0 %** das vezes. **A MEDIÇÃO QUE AUTORIZA SOMAR OS DOIS** (carteira do Feca, prequential 30d, separando perfis grandes de pequenos): grandes → base **61 %** certo × declarado 55 %; **pequenos → base 4 % certo × declarado 64 %**. Os dois são fortes em lugares **opostos**, e é isso — não uma média — que justifica juntá-los. O declarado fala **apenas** onde a base se cala e **apenas** sobre quem a base mal conhece. **DOIS CORTES, os dois no servidor de propósito** (`app/matcher.py`): `NOVATO_MAX = 60` bilhetes rotulados à mão — acima disso a base já tem o que dizer e o declarado só atrapalha (liberar para todos leva o Feca a +331 acertos e **+134 erros**, 2,5:1, contra +139 e +28, **5,0:1**, com o corte); e `FOLGA_DECLARADA = 25`, **muito acima dos 7** que o declarativo usa como caminho principal. **A folga alta não é conservadorismo genérico — é escolha de SINAL:** os pesos do declarativo são stake 25-50, esporte/mercado exclusivos 10, casa 5, então exigir 25 significa na prática **"só fale quando a assinatura de STAKE decidir sozinha"**; somar esporte + mercado (10+10) deixa de bastar, e era exatamente daí que vinha o ruído histórico dele (`SóChutes→Arrudex`, 83 confusões na janela). Medido: folga 7 dá +148 acertos/+72 erros; folga 25 dá +139/+28 — **quase o mesmo ganho por um terço do erro**. **A rota devolve `novatos` + `folga_declarada` e a 2ª passada roda na TELA**, reusando o `_sugParaBilhete` que já vive no `index.html`. Deliberado: uma terceira implementação do declarativo (já existem a do front e a porta do backtest) divergiria em silêncio, e os dois cortes vêm do servidor para não haver um segundo número para a mesma regra. `_sugRanqueia`/`_sugParaBilhete` ganharam o parâmetro `folga` com **default 7** — o caminho principal não muda. **PLACAR DE PRODUÇÃO** (`scripts/backtest_matcher.py` ganhou a linha `PRODUÇÃO` = evidência + 2ª passada, porque medir duas metades que o app não usa isoladamente passaria a descrever outra coisa): **Feca 58 %/86 % → 64 %/86 %** (seis pontos de cobertura com a precisão **idêntica**, e sem confusão nova na lista) · **Jonathan 22 %/92 % → 62 %/97 %** (cobertura quase tripla e precisão **subindo**) · Gabriel, Lava, LavaPessoal, SóChutes e perereca **inalterados**. **NENHUMA carteira regride.** **E isso responde melhor à pergunta do Feca sobre os outros usuários do que a proposta anterior:** a mudança de peso da parte 1 dava +2 pontos e **piorava o arrudex em 8 e o LavaPessoal em 10** — foi **abandonada**. Esta não pode tocar quem não escreveu nada, e é medição, não dedução: **arrudex 0 de 34 perfis com info, LavaPessoal 0 de 15, perereca 0 de 7**; Gabriel (1 de 10) e Diogo (6 de 43) têm info e ainda assim registram **zero** mudança. Efeito colateral que importa: **preencher o perfil passa a pagar**, e paga mais no tipster novo, que é quando a base não tem nada. **GATES:** suíte **611 passed, 23 skipped** (era 586) · 8 testes de `tests/js/` verdes · `check-tokens` verde · **mutação 7 de 7** (`scripts/mutar_2a_passada.py`, quebrando os dois lados: folga voltando a ser o 7 fixo, folga não repassada ao ranqueador, default deixando de ser 7, casa dedicada parando de cravar, `novatos` incluindo todo mundo, `novatos` vazio, folga caindo para 7) · o teste do front **recorta** as funções do `index.html` real e o `tests/test_rota_sugerir.py` trava o CONTRATO da rota · tela de Extração **aberta em navegador headless**, zero `pageerror`, assinaturas novas no ar e botão ligado. **DOIS COMPORTAMENTOS ANTIGOS PRESERVADOS DE PROPÓSITO, e agora travados por teste:** casa dedicada a 1 dono **crava acima de qualquer folga** (curadoria humana explícita), e **dono único do esporte dispensa a folga** — é esse atalho que faz o Bad Milton e o MMA (únicos de Badminton e de MMA na carteira) serem sugeridos sem assinatura de stake. Os dois derrubaram asserções minhas antes de eu entender que a expectativa errada era a minha, não o código. **O que os testes NÃO cobrem, e está escrito neles:** o `salvarTipsterVal` (rede), e a decisão de quem é novato é do servidor por desenho, não do front. O `index.html` já sai com `Cache-Control: no-cache, must-revalidate`, então a mudança chega **sem Ctrl+F5** (o matcher é inline). Backup em `Backups/s310-hibrido-declarado/`. `app/static/landing.html` e os arquivos de outra sessão seguiram FORA do commit.)_

_Anterior: 2026-09-01 (sessão 312 — **Editar conta era um `prompt()` do navegador que só alcançava o nome; virou o MESMO modal completo da criação — casa, parceiro e fornecedor.** O gatilho foi um print do Feca da caixa branca do Chrome sobre o dashboard: *"o botão editar de uma casa precisa abrir um popup completo"*. **O modal completo já existia** (`novaconta-modal`, com combo de casa buscável + "cadastrar nova casa") — só nunca tinha sido reusado na edição, então quem precisasse corrigir o fornecedor tinha de digitar os **colchetes do modelo canônico na mão** (`Parceiro [Fornecedor]` — fornecedor não é coluna, mora dentro do nome; é o mesmo `_PARCEIRO_RE` que parte o texto no feed do dashboard), e quem cadastrasse na casa errada **não tinha saída nenhuma pela UI**. Um formulário, dois modos (`_ncModo`), nada de um segundo formulário que envelhece separado. **A metade cara é a casa.** `casa` e `parceiro` entram JUNTOS no hash de `_assinatura` — mover a conta sem recalcular deixaria todo bilhete dela com o hash da casa velha, a próxima captura não colidiria com nada, o UPSERT não deduparia e o **histórico duplicaria inteiro**: exatamente a falha da s198, com a outra metade da chave. `renomear_parceiro` virou wrapper de **`editar_parceiro`**, que numa transação só atualiza `parceiros`, propaga `casa`+`parceiro` aos bilhetes e recalcula a assinatura de cada um; os dois campos vão numa chamada só (`POST /parceiros/{id}/editar`) porque mudar um de cada vez gravaria uma assinatura intermediária que não corresponde a bilhete nenhum. A colisão de nome é conferida na casa de **destino**, não na de origem, e a grafia passa por `casa_canonica` como no `POST /parceiros` — casa é texto, e uma gêmea por caixa nasceria aqui. **Mover é destrutivo o bastante para ser dito, não descoberto:** trocando a casa no combo o modal acende um aviso `--warn` nomeando o custo (`Mover para Aposta1 leva junto 1.234 apostas desta conta`), com o número vindo do mesmo `GET /parceiros/{id}/resumo` que o modal de exclusão consome. **GATES:** suíte inteira verde (**607 passed, 23 skipped**) · `check-tokens` verde · `/nova-ui` conferido item a item (nenhum R$ novo; a contagem de apostas é unidade → `toLocaleString('pt-BR')`, nunca abreviada; `.nc-hint.warn` só troca o acento do `.nc-hint` que já existia, e o número fica neutro porque cor em número é semântica de resultado) · **mutação 3 de 3** (assinatura ignorando a casa nova; bilhete ficando na casa velha; colisão conferida na casa de origem). **A terceira mutação ESCAPOU na primeira tentativa** — o `_FakeConn` respondia "nunca colide" para qualquer consulta de `parceiros`, então a checagem não era exercida por teste nenhum; o defeito era do teste, e ele ganhou o par de casos que faltava (nome ocupado no destino recusa **sem tocar no banco**; nome ocupado só na origem não pode barrar). **E a tela foi ABERTA num navegador antes do commit**, contra o `servidor_demo.py` com puppeteer — `node --check` é falso verde para o que vive em template literal (s296). Medido no DOM real: `Davi [Norte]` chega partido em `Davi` + `Norte`, título e botão trocam com o modo, o aviso de mover acende só quando a casa difere, o modo criar não herda nada da edição, o botão da lista virou `Editar` → `contasEditar`, **zero `pageerror`**. Backup em `Backups/s312-editar-conta-modal/`. Sem versão de SharpenUp e sem nota de changelog — é tela do app, não extensão; **testers a avisar é decisão do Feca**. `app/static/landing.html` e os arquivos de outra sessão simultânea seguiram FORA do commit.)

_Anterior: 2026-09-01 (sessão 311 — **A stake de um bilhete pulou para outro e nada acusou, porque a odd derivada preservou o P/L.** A Pinnacle `3113103675` (LOUD v MIBR) foi gravada com `400,00`, a stake do `3114339695` **duas linhas acima no mesmo chunk** — e como em W a odd é `Retorno ÷ Stake`, ela foi recalculada sobre a stake errada (`(400 + 330,48) ÷ 400 = 1,8262`), devolvendo o P/L EXATO de R$ 330,48. Descrição certa, código certo, resultado certo: `checar_descricao`, `checar_fidelidade` e a cobertura passam todos. Erram só turnover, ROI e a assinatura de stake do matcher — foi por isso que a linha perdeu o tipster `Zora`. **É o carryover da s302 no financeiro**, e a regra do `CLAUDE.md` que dizia "o financeiro não viaja junto" era observação medida, não garantia. **Conserto: a stake saiu da mão da IA.** `repository.corrigir_stake_tsv`, irmão do `anexar_sistema_tsv` — a coluna 8 vem do `Stake:` do bloco daquele código, e a odd de W é refeita junto quando o bloco traz o `P/L`. Determinístico, sem modelo no caminho. **Medido antes de escrever:** a linha `Stake:` casa a regex ancorada em **100% dos 5.128 blocos** da sombra (20 casas), sempre com um valor só; e o replay do gate sobre **3.820 bilhetes** mexe em **3** — as 3 divergências reais, **zero falso positivo**. Bloco ambíguo (dois `Stake:`) não autoriza escrita; print, que não tem bloco, segue 100% com a IA. Dado: a linha do Feca corrigida por `scripts/corrigir_stake_infiel_s311.py` (204,00 · 2,620 · P/L 330,48). Gate: `tests/test_stake_determinista.py`, 15 casos, **6 mutações aplicadas e todas pegas**. **Adendo ("se tem erro precisa ser corrigido"): a varredura foi até o fim e 7 linhas foram corrigidas, em 4 donos.** Stake (3): Pinnacle `3113103675` [Feca], BETesporte `195072327` e Betano `20951200252` [WilliamOliveira]. Odd (4), da varredura que veio junto — 3.692 odds conferidas contra o bloco cru e classificadas pelas regras legítimas (verbatim 3.648 · `Retorno ÷ Stake` 27 · média de sistema 17): Betano `20926898412`, Betfast `301490938` e `301491163` [Gabriel], Bet365 `JR3841878921I` [Jonathan]. Hoje sobra **zero sem explicação**; nenhuma das 4 mexe em dinheiro (`L`/`HL`, onde `calcular_pl` não usa a odd). Os dois Betfast são os **mesmos gêmeos que a s302 corrigiu na descrição** — o carryover atingiu os dois campos e na época só a descrição foi olhada. **Raiz dos 4 erros de odd, ainda ABERTA e mexe em `extensor/`:** Bet365 e Novibet emitem o marcador canônico `Tipo: SISTEMA … — N apostas de k seleção(ões)` mais a `Odd (estrutural do sistema)` e acertaram 15 de 15; **Betano** (`Tipo: Dupla`) e **Betfast** (`Tipo: Sistema (3 seleções)`) não emitem nenhum dos dois, então a IA deduz a regra da odd (média × produto) e errou 3 vezes — e a coluna 12 (`sistema`) nunca é preenchida nessas casas. Script: `scripts/corrigir_odd_infiel_s311.py`.)_

_Anterior: 2026-09-01 (sessão 310, parte 3 — **O `status 4` da Esportiva subia sem resultado porque a casa esconde o cashout no campo errado: `cashOutValue`, `partialCashOut` e `partialCashouts[]` vêm ZERO até num bilhete cashouteado de verdade — o valor encerrado mora no `totalWin`.** Quem procura cashout pelos campos homônimos conclui que a casa não tem nenhum, e foi isso por duas versões. **Provado por três eixos que se fecham:** a aba Cashout da tela manda `statuses:[4,18]` e devolve **exatamente** os três bilhetes da conta (`5341163017`/18 · `5339901091`/18 · `5339889186`/4); os três cards estampam a faixa **CASHOUT**; e o dinheiro do `5339889186` só fecha assim — a perna **ganhou** a odd 1,5 (pagaria R$5,00) e ele recebeu **R$2,83, menos que a stake**. Agora sai `W` com odd 2,83÷3,33 = **0,84984985** (P/L −R$0,50; a odd exibida gravaria +R$1,67); os dois `18` seguem `V`, agora nomeados. **O que separa o `4` do `18` continua SEM prova** (n=1 e n=2 na conta inteira) — e não precisa, porque quem decide é o valor, não o enum. **Esporte: o mapa parou de crescer de bilhete em bilhete.** A própria casa publica a ponte **sem login** — `GetAllSports` devolve `{typeId, id, name}` no mesmo objeto para os 25 esportes; 16 ids mapeados (Tênis e E-Sports eram os que sangravam), **9 deixados crus de propósito** porque não têm valor oficial no MASTER (`7` "Automobilismo" **não** é `F1`). O `317` vem com **TAB literal** no nome (`"E-sports +		"`), família da s303. **E o `sportTypeId 300` NÃO é esporte:** as 16 seleções vivem todas em `sportId 115`/`champId 61714`, com `marketName === eventName`, misturando CS2 (BLAST Open) e futebol (Libertadores) — uma se chama `Especiais Copa do Brasil | 05/08`; sai marcado como **aposta especial**, e o esporte real fica com a IA. **Dois defeitos que só apareceram ao mexer:** a rede de segurança testava a lista de PROCESSADOS `[1,8,2,4,18]` e, com o `4`/`18` batizados, **virou código morto sem nenhum teste ficar vermelho** — passou a testar a família ABERTA, que é o que ela sempre quis cobrir (o teste dela usava o `4` e não exercia mais nada; trocado por `19`); e a linha de boost usava a odd **efetiva**, fazendo o `5339889186` sair "odd antes do boost 1,3847 · valendo 0,84984985" — a casa turbinando a odd para baixo. Doc propagado nas 5 casas do motor. Gates: harness **verde (23 casos, 395 bilhetes)**, `audit_casas` e `audit_sharpenup` sem FAILs, `pytest` 586 passed, e **5 mutações todas detectadas**. SharpenUp **0.7.6**; a pedido do Feca a nota foi só para a home — **o grupo de testers não foi avisado**. ⚠️ Pendência: as linhas JÁ gravadas de tênis/e-sports/especiais **não se consertam por recaptura** (o `ON CONFLICT` congela `esporte`/`aposta`/`descricao` fora de `origem='sync'`); o cashout, sim, porque `resultado` não é congelado.)_

_Anterior: 2026-09-01 (sessão 310, parte 2 — **A curadoria de casa vencida deixou de ser silenciosa: a tela agora acusa a linha que a própria evidência do dono não sustenta mais.** É a pendência aberta na parte 1, e ela existe porque `casa_config` é um **retrato datado que nunca se reavalia** — curada uma vez, a linha crava para sempre, e casa dedicada é resolvida **antes** do matcher (com 2 nomes ela restringe o pool a eles, e o resto da carteira sai da cédula sem o modelo ser ouvido). **A regra do aviso mora em `casas_visao`, colada na que já calcula a sugestão** (`repository.py`): a que SUGERE e a que AVISA são a mesma e não podem divergir — se morassem em lugares diferentes, o aviso passaria a discordar da regra em silêncio, que é exatamente o defeito que ele existe para pegar. Acende só no caso inequívoco: **curada `dedicada` + evidência de hoje dizendo `multi`**. `sug_modo is None` (volume < `CASA_MIN_VOL`) nunca acende — pouco dado não é evidência de nada. **MEDIDO antes de desenhar, que é o que garante que o aviso seja quieto:** em **49 casas curadas de 2 donos**, a regra acende em **zero** hoje, e fica apagada até na `Tivo` (89,6%, perto do corte de 85%); rodada contra o estado de 25/08 ela acende **só na Betnacional** (82%). Aviso que acende demais é aviso que ninguém lê. **O que a tela mostra:** um chip na célula da **evidência** — é a evidência que mudou, não a curadoria —, nomeando o **custo em apostas** (`40 de 223 apostas são de fora`) em vez de falar em "pureza", porque é esse número que decide se vale mexer; a linha sobe ao **topo** da lista e ganha uma marca; e o cabeçalho ganha `· N a revisar`. **Contador sem ponte para a linha vira caça manual**, então a ordenação é parte do aviso, não enfeite. **DUAS CORREÇÕES QUE SÓ APARECERAM NA CONFERÊNCIA DA ESCADA DE TINTA, e as duas eram desvio real:** (1) o tint de fundo que eu tinha posto na linha vencida empurrava o `--ink-mute` do `.cstats` de **3,06:1 para ~2,95:1** — abaixo do piso de 3,0 do papel metadado —, e isso vale para **qualquer** alpha testado (.020, .030, .045); a linha passou a ser marcada por **borda** (`box-shadow: inset`), que não entra no fundo efetivo do texto e sinaliza sem cobrar contraste. (2) eu havia criado uma classe `.meta-warn` quando **já existia `.w`** no mesmo bloco (`.tm-wrap .panel__head .meta .w`), usada pelo `N sem info` — reusada, e o teste trava isso. O chip é `--warn` em 11px sobre tint de 10%: **6,4:1**, acima do piso de 4,5 de label, e nunca `--ink-mute` (é aviso, não metadado). **GATES:** `/nova-ui` executado item a item · **suíte inteira verde (586 passed, 23 skipped)** · os 7 testes de `tests/js/` verdes · `check-tokens` verde · **mutação 6 de 6** (`scripts/mutar_casas_curadoria.py`: aviso nunca renderiza, aviso renderiza sempre, linha perde a marca, aviso deixa de nomear o custo, cabeçalho para de contar, cabeçalho conta fora da classe de warn) — o teste **recorta** as funções do `gestao.js` real, e a troca de assinatura de `_casaMetaTxt` **quebrou o recorte antes de eu atualizá-lo**, que é o gate funcionando. **E a tela foi ABERTA num navegador antes do commit**, contra o `servidor_demo.py` com puppeteer: `node --check` é falso verde para o que vive dentro de template literal. Medido no DOM real — chip renderizado, `rgb(224,162,26)`, 11px, linha vencida em 1º, `box-shadow` inset aplicado, meta com `1 a revisar`, **zero `pageerror`**. O `servidor_demo` ganhou os dois campos novos espelhando a regra (dá sempre falso lá, de propósito: print de venda não mostra aviso). **O QUE NÃO ESTÁ COBERTO, e está escrito no teste:** o gate de mutação é do FRONT; a regra do backend em `casas_visao` não tem teste unitário (a função toca o pool), e sua evidência é a **medição contra o Postgres real** descrita acima. `?v=` bumpado nos dois assets (`gestao.js?v=36`, `tipster-metodo.css?v=10`). Backup em `Backups/s310-curadoria-vencida/`. `app/static/landing.html` seguiu FORA do commit, e **os arquivos de `extensor/` também — são de outra sessão simultânea**.)_

> **Histórico completo das sessões 310 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 328)

### A Pinnacle chama o push de `DRAW` — e o rótulo desconhecido virava pendente eterno

O relato foi de uma linha só: *"Pinnacle não atualizou o resultado do void na última
extração"*. O bilhete `3117191609` — Aguila `0.0` no 1º tempo contra o Alianza, `1:1` no
intervalo, R$ 408 — estava **liquidado na casa** (`Decidido / REEMBOLSADO`,
`Vitória/derrota 0.00`) e com `?` na grade do Sharpen.

**O rótulo que a tela mostra não é o que a API devolve.** A tela diz `REEMBOLSADO`; o campo
cru do resultado (93 e 6) traz **`DRAW`**, que não estava no de-para do `formatTicketPN`. O
bloco entregue à IA saía:

```
Status: DRAW (a conferir — não liquidar automaticamente) · P/L 0,00
```

**A IA não errou — ela obedeceu.** Ainda registrou no RAIO-X que o `DRAW` ali não era empate
de jogo e que o P/L 0,00 confirmava reembolso; só não tinha autorização para liquidar. O
backend gravou `aberta` e a linha ficou pendente para sempre. Vale como sintoma: quando a
nota da IA explica o caso certo e mesmo assim nada acontece, a instrução veio de quem
formatou o bloco, não do modelo.

`DRAW` é o **push**: handicap ou total que bate exato na linha (`0.0`, `2.0`) devolve a
stake. Não é o empate do jogo — numa Moneyline de 3 vias o empate dá `LOST`. O campo nomeia
o desfecho da **aposta**, não o do jogo.

### A trava que vale é a de baixo: o dinheiro decide, não o rótulo

Duas foram para o código, e a segunda é a que fecha a família:

1. `DRAW`/`TIE` entraram no de-para junto de `PUSHED`/`VOID`/`REFUNDED`/`CANCELLED`.
2. **Rede por baixo dele:** resolvido + rótulo desconhecido + P/L **exatamente 0** ⇒
   retorno = stake ⇒ `V`, que é a 2ª das cinco fórmulas de `_veredito_do_retorno` lidas ao
   contrário. O próximo nome que a casa inventar para push já nasce coberto.

Com **P/L ≠ 0** o rótulo desconhecido continua subindo como "a conferir": inferir `W`/`L`
de um nome que ninguém conhece é chute, e a rede não pode alcançar a **aberta** (o payload
traz P/L 0 nela também — mesmo número, significado oposto).

### As mutações, incluindo a que escapou

| Mutação | Resultado |
|---|---|
| tirar `DRAW` do de-para | **PEGOU** |
| tirar a rede do P/L | **PEGOU** |
| as duas juntas | **PEGOU** — e reproduz o bug palavra por palavra: `DRAW (a conferir — não liquidar automaticamente) · P/L 0,00` |
| tirar o `!t.aberta` de dentro do `plZero` | **ESCAPOU** |

A que escapou está anotada no caso como **inócua**, não como buraco: quem decide a aberta é
o `if (t.aberta)` de cima, então o `!t.aberta` dentro do `plZero` é defesa dupla. O teste
trava o *comportamento* (aberta com P/L 0 não liquida), não aquela linha.

Anotado também que as duas travas **se cobrem de propósito** — tirar `DRAW` sozinho ainda
daria `V`, pela rede; o que a mutação pegou foi o texto do status mudar. É defesa em
profundidade, não independência.

### O que ficou

- `extensor/content.js` (`formatTicketPN`), `casas/CASA_PINNACLE.md §5.1` (o de-para do
  rótulo **cru**, que a tabela antiga não tinha), fixture + caso no harness.
- Fixture `9000000003` é **derivada** do `3099205574` — só o resultado mudou; nenhum campo
  inventado. O JSON cru do `3117191609` não foi capturado, e o cabeçalho do caso pede a
  troca quando aparecer.
- Harness verde (23 casos, 399 bilhetes) · `audit_sharpenup` e `audit_casas` sem FAIL.
- **SharpenUp 0.7.7.** A linha presa **fecha sozinha na próxima captura** — ela está
  `aberta`, e o UPSERT atualiza resultado em linha aberta. Nenhum script no banco.

### Anotado, não resolvido (não é desta sessão)

O mesmo bilhete entrou na grade como **ML**, não como Handicap Asiático `0.0`. A causa é
outra e é de descrição: `_linhaPN` devolve `""` quando a linha é `0`, então o `0.0` some do
bloco e a IA classifica pelo que sobrou. Some a informação que **distingue** DNB de
Moneyline — e é justamente a linha que explica o push. Não mexi: é mudança de descrição,
com o congelamento do UPSERT no caminho (linha já resolvida não reescreve `aposta`/
`descricao`), e merece sessão própria.

---

## Sessão 327 — a Caixa ligada no meio da captura

### `abertas_corte` mede o que o Sharpen SABE, não o que a casa TEM

O relato veio em três sintomas que pareciam três problemas: "a Betnacional não exporta",
"uma aposta de ontem não resolve" e "preenchi a Caixa e ela não bate". Era **um só**, e
nenhum deles estava na casa — os 11 bilhetes do período estão lá, completos, com odd e
retorno corretos (conferidos card a card no Chrome; a casa diz **"Sem apostas
pendentes"**).

**Defeito 1 — a Caixa foi ligada no meio da captura.** Cronologia medida no banco:

```
03:17:32  Caixa ligada     → abertas_corte = []   (o banco ainda não tinha aberta)
03:17:59  IA termina       (uso_tokens id 2163)
03:18:19  /salvar grava    → 3 apostas nascem ABERTAS: R$ 600,00
03:18:35  Conferência      → projetado −599,00 · saldo real 2.379,87
                           → Ajuste +2.978,87  (R$ 600,00 a mais do que devia)
```

`_caixa_abertas_ids` diz que com `corte = hoje` "toda aposta aberta entra: se ela está
aberta agora, o stake saiu antes de agora, é exato". **É exato só se o Sharpen já souber
da aposta.** O dinheiro sai da conta na casa, não no nosso banco — e entre a captura
começar e o `/salvar` gravar existe uma janela de ~1 minuto em que a Caixa enxerga zero
abertas e grava esse zero para sempre. Pior: o Ajuste da conferência, que existe para
fechar a conta, **cimenta o erro** com cara de número conferido.

**Defeito 2 — a linha órfã sem código.** A captura de 05/09 devolveu a múltipla do
Falkirk sem a 11ª coluna. Sem código a dedup cai na assinatura por conteúdo, e a
"Migração B" do UPSERT (que adota linha sem código) exige `odd` **idêntica**: `14` não é
`14,00`. Quando o bilhete liquidou em 06/09, entrou linha **nova** (246454) e a velha
(243667) ficou `aberta` para sempre — o `AGUARDANDO RESULTADO 1` da grade.

**A prova, contra a casa:**

```
Saldo no corte (05/09)                              2.379,87
+ retorno das 3 abertas no corte                    1.662,26
    243665  R$300 @2,834    L  →        0,00
    243666  R$150 @11,08173 W  →    1.662,26   ← card da casa: "Retorno R$ 1.662,26"
    243667  R$150 @14       L  →        0,00
+ líquido das 8 apostadas depois do corte             515,96
                                                 ──────────
= saldo esperado hoje                               4.558,09   ← bate com a casa
```

A Caixa projetava 3.195,83. A diferença de **1.362,26** é exatamente **+1.662,26** (o
retorno que ela não conta — a `data` 04/09 é anterior ao corte, então ela lê a linha como
"já embutida no saldo informado"; só o **stake** estava, o **retorno** não) **−300,00** (o
Falkirk descontado duas vezes: R$ 150 como fantasma em aberto e R$ 150 como L liquidado).

**Correção aplicada** (`scripts/corrigir_caixa_fantasma_s327.py`, ensaio → `--aplicar`):
apaga o fantasma, grava `abertas_corte = [243665, 243666, 246454]` (o id que carrega
**hoje** cada bilhete — o do Falkirk é o 246454) e baixa o Ajuste em exatamente o
`preso_corte` que faltou, `2.978,87 → 2.378,87`. O script **aborta** se a projeção
corrigida não fechar com o saldo lido na casa. Resultado, relido da API de produção:
`preso_corte 600,00 (3) · pl 1.578,22 (11) · aberto 0,00 (0) · banca 4.558,09 ·
disponível 4.558,09` — divergência **0,00** depois da nova conferência.

O lançamento `conferencia` de 05/09 **não** foi tocado: ele é a medição daquele momento e
não se recalcula. O que ele registrou aconteceu de verdade.

> **Sintoma para reconhecer isto noutro lugar:** um retrato tirado de uma fonte que ainda
> está sendo preenchida. Vale para todo campo que congela estado no instante do clique —
> se a escrita que o alimenta é assíncrona, o clique pode chegar antes dela.

### Os dois defeitos de produto, corrigidos

**1. A órfã não era adotada porque `"14"` não era `"14,00"`.** A Migração B do UPSERT
adota a linha sem código quando o mesmo bilhete volta COM código — e comparava a odd como
**string crua**. `_assinatura` já normaliza a odd (`_norm_odd`) para decidir se duas
linhas são o mesmo bilhete; a Migração B contradizia a própria régua do sistema. Agora as
duas usam `chave_orfa()`, onde o porquê e o caso medido estão escritos. `descricao` fica
de fora **de propósito** — a Migração B nasceu para casar import por imagem com captura da
casa, e é justamente a descrição que diverge entre as duas; há teste para essa ausência
ser decisão registrada, não esquecimento.

De quebra, o índice de órfãs virou **uma consulta por conta** em vez de um
UPDATE-com-subconsulta por linha do lote, e cada órfã só é adotada **uma vez** (`pop`):
sem isso dois bilhetes iguais reivindicariam a mesma linha antiga — e a Migração B, quando
erra, não duplica: ela **sequestra**.

**2. A Caixa ligada no meio da captura gravava `abertas_corte` vazio.** Ao INSERIR uma
aposta que **nasce** aberta e cuja captura (`criado_em`) antecede a ativação, o id agora
entra no `abertas_corte`. Não é heurística: a aposta não pode ter liquidado e
desliquidado, então o stake já tinha saído quando o saldo foi lido. Três travas — só linha
recém-**inserida**; a decisão é do próprio `_caixa_abertas_ids` com `ate` = instante da
ativação (um segundo critério divergiria do original em silêncio); e a lista **só cresce**,
porque tirar um id descontaria o stake duas vezes. `criado_em` nulo ou sem fuso fica de
fora: sem ele não há prova, e comparar um naive estouraria **dentro** do `/salvar`,
derrubando a gravação inteira por causa de uma linha de caixa.

**3. A raiz: a repescagem acrescentava a linha e deixava a órfã.** `conferir_cobertura`
cobra **quantidade por código** — ela não sabe que o bilhete "faltante" pode estar ali
como uma linha que perdeu a 11ª coluna. E a repescagem só ACRESCENTA
(`_extract_tsv_rows(resultado) + novas`); ninguém removia a órfã. Os dois desfechos
deixavam linha sem código: repescagem OK dava **duas** linhas do mesmo bilhete no lote;
repescagem falha (o que aconteceu em 05/09) deixava a órfã — e sem código ela nunca dedupa.

`_reconciliar_orfas` faz duas coisas, ambas conservadoras:

- **Adoção** — a órfã recebe o código do bloco faltante de que ela é **fiel**
  (`checar_fidelidade`, o gate de procedência da s302: todo nome próprio e todo decimal da
  descrição existem naquele bloco). Só quando o par é único **nos dois sentidos** — a órfã
  casa com um único bloco livre, e aquele bloco casa com uma única órfã. Ambíguo não vira
  chute.
- **Descarte** — sobrando órfã depois disso, e não havendo mais bilhete do texto sem linha
  própria, ela é cópia de alguém que já tem a sua. Sai.

**NO-OP integral onde a coluna 11 vazia é legítima:** casa sem marcador (prints, texto
colado) e texto que traga **qualquer** `[Código: ]` vazio — é o que a bet365 manda quando o
detalhe não chegou, e descartar ali apagaria bilhete real.

Roda em **todos** os caminhos de saída, inclusive quando não houve repescagem: era esse o
desfecho que deixava fantasma. O sort por posição no texto-fonte passou a rodar **só quando
este passo mexeu no TSV** — reordenar de graça mudaria calado a ordem que o resto do
sistema lê como hora de envio.

**Gates, provados por mutação** (cada uma pega por exatamente o teste que devia pegá-la):
`_norm_odd` → string crua deixa **6** vermelhos, incluindo o caso medido `14`/`14,00`;
tirar `aposta` da chave, **1**; tirar o `ate`, **1**; sobrescrever `abertas_corte` em vez
de unir, **1**; tirar a guarda de `criado_em`, **2**. Nas órfãs, **1** cada: trava de
par único, guarda do marcador vazio, descarte, adoção e a **ligação** dentro do
`_garantir_cobertura`.

> A **ligação** tem gate próprio no harness de DB (`test_upsert_adota_aberta_que_chegou_
> depois_da_caixa_ligada`). O dublê testa a função, não a chamada: removendo o
> `await _caixa_adotar_abertas_tardias(...)` do `upsert_bilhetes`, o arquivo de dublê fica
> **todo verde** e a Caixa volta a nascer torta. Foi o modo de falso verde nº 1 da
> s286. O mesmo vale para as órfãs: removendo a chamada de dentro do
> `_garantir_cobertura`, os 7 testes de `_reconciliar_orfas` seguem verdes — só o
> teste da ligação pega.

Suíte: **756 passed, 30 skipped**. CI verde em `863f67c`, com os 30 do harness de
Postgres (é lá que o SQL novo do UPSERT é exercido de verdade).

**Backfill: nada a fazer.** `recalcular_abertas_corte_s314.py` em ensaio sobre todas as
caixas ligadas devolve **0 a corrigir**. As 3 contas que uma primeira query apontou
(`Gabriel/Pinnacle`, `Gabriel/1xBet`, `Feca/Bet365 marloncezar01`) são o **piso
deliberado** de corte no passado — o `_caixa_abertas_ids` as exclui de propósito.

**Pendente para a próxima sessão:**

1. **Duas órfãs antigas**, anteriores à correção: `passapica / BETesporte` (04/09,
   R$ 0,75) e `Diogo / Betfair` (12/08, R$ 400,00). São linhas abertas sem código em
   conta que usa código. A Migração B as adota quando o bilhete voltar liquidado, **se**
   data, categoria e stake baterem — não é garantido, e a do Diogo está aberta há quase
   um mês. Duas linhas; resolver à mão é mais barato que esperar.
2. **Aviso aos testers não foi enviado.** Sem bump do SharpenUp, o tester não tem ação a
   tomar. Decisão do Feca; a pergunta ficou em aberto.

---

## Sessão 326 — data ausente não é data antiga

O relato veio da tela: a Caixa da `Betfair · Duka [Eu]` projetava **R$ 5.456,42** e a
casa mostrava **R$ 5.155,42** — divergência de R$ 301,00, exatamente o stake da única
aposta em aberto (`O/25146258/0001998`, Botafogo × Palmeiras). A conta do painel batia
consigo mesma; o que faltava era a linha **"Em aberto"**, que dizia `0 apostas`
enquanto a grade logo abaixo dizia `AGUARDANDO RESULTADO 1`.

- **A causa é a data VAZIA, e ela é vazia de propósito.** Onde a coluna `Data` é a data
  de **resolução** (Betfair, `extensor/content.js`), a aposta aberta sobe sem data — a
  resolução ainda não existe. O `_caixa_projetar` decidia a janela por
  `data_iso >= corte`; com `data_iso = None` a condição caía e a linha era lida como
  **anterior ao corte**.
- **Sumir de uma ponta é erro; sumir das DUAS é o erro silencioso.** Fora da janela e
  fora do `abertas_corte` (nasceu depois da ativação), o stake não entrava na banca
  **nem** em "em aberto". Nada acusava: os totais continuavam coerentes, só altos em
  exatamente um stake — e a auditoria acusava uma divergência que era **dela**.
- **Correção:** sem data, a data efetiva é `criado_em` — o único sinal restante de
  quando o stake saiu da conta. Onde há data, nada muda. Extraí `_caixa_criado_iso`
  para `_caixa_projetar` e `_caixa_abertas_ids` não discordarem sobre como ler o campo.
- **A query do Painel de Contas não trazia `criado_em`.** `caixa_conta` e `caixa_visao`
  chamam o mesmo núcleo mas montam queries próprias: sem o campo, o Painel projetaria
  **diferente** da tela da conta, com a mesma conta e sem erro nenhum.

**Alcance medido em produção:** 193 bilhetes sem data no sistema inteiro (187 Lottu,
5 Betfair, 1 Bet365), e **1 só** em conta com caixa ligada — a do relato. Nenhuma conta
Lottu tem caixa hoje; ligar uma cairia no mesmo buraco.

**Prova contra o dado real** (leitura pura, nada escrito): `preso_corte 421,00 ·
pl 1.250,58 (18 liquidadas) · aberto 301,00 (1) · banca 5.456,42 · **disponível
5.155,42**` — igual ao Principal da Betfair. A conta segue em `reconferir` porque o
ajuste de 05/09 endereçou a divergência antiga; a próxima conferência fecha.

**Gates, provados por mutação:** removendo o fallback, 3 testes ficam vermelhos
(incluindo `test_caso_medido_betfair_duka`, que reproduz os números da tela);
removendo `criado_em` da query do Painel, o gate de forma das duas queries fica
vermelho. O simétrico também está travado — aberta que o Sharpen **já conhecia** antes
do corte e ficou fora do `abertas_corte` continua fora, senão o stake seria descontado
duas vezes. Suíte: **724 passed, 26 skipped**.

---

## Sessão 325 — 8º tipster público: `Grego Tips - VIP`

### 8º tipster público — `Grego Tips - VIP`

Conta `gregozxrd` (alyssongrego587@gmail.com) aprovada no `/admin` e **956 apostas
importadas** (`scripts/import_grego_csv.py`), 01/08 → 01/09/2026, stake em
unidades, 12 contas `Padrão` — uma por casa.

| | |
|---|---|
| Slug / marca | `/tipsters/gregotipsvip` · `Grego Tips - VIP` (o username diverge pela 5ª vez) |
| Códigos | `GV202608-1` … `GV202609-32` |
| Carteira | prop de jogador de futebol: Chutes 472 · Anytime 229 · Múltipla 120 · Desarmes 30 · Faltas 29 · Assistência 25 |
| Resultado | L 675 · W 267 · **V 14** (`Reembolsada` → void, `Ganho` e `Lucro` zerados) |
| Total | 1.008,48u de turnover · **+132,79u** · ROI **+13,17%** |

### O gate mais forte não veio da planilha — veio do canal

Ele publicou o fechamento de agosto no grupo em 01/09: **924 apostas, P/L
+127,84u, ROI 13,02%**. O import, lendo só o CSV, deriva **924 apostas, +127,73u,
13,00%**. A diferença de 0,11u é o arredondamento a centavo da coluna `Ganho`,
acumulado em 267 vitórias — o derivado usa a odd inteira.

Isso é diferente da reconciliação interna (que também fecha: **0 divergências em
956** entre P/L derivado e a coluna `Lucro`). O número do canal saiu da boca do
dono **antes de existir import**: ele não pode estar errado pelo mesmo motivo que
a planilha estaria.

### As 6 linhas sem casa foram MEDIDAS, não decididas

O Rogerin resolveu isso com uma decisão do Feca (126 linhas → Betano). Aqui a
resposta estava no export do Telegram, nas mensagens do próprio dia:

    Nesta Elphege chutes 3+/4+/5+   01/09  → Bet365   (msg 938)
    Forson +2 Chutes / +3 Chutes    01/09  → Bet365   (msg 940)
    Summerville Ast                 01/09  → Betano   (msg 942)

O mapa é fechado e casado por (data, título): linha sem casa fora dele **aborta o
script**. Casa chutada não dá erro — dá conta paralela.

### Três leituras de categoria que não eram óbvias

- **`<Nome> +2 Gols` é `Anytime`, não `Gols`.** O `MASTER_APOSTAS §3` põe
  "marcar 2 ou mais gols (marcador 2+)" na família Anytime, e o limiar vai na
  descrição. As odds confirmam (11,0 a 81,0 — total de jogo não paga isso), e o
  canal mostra a escada: `Tresoldi Anytime 1.50%` + `Tresoldi +2 Gols 0.50%`,
  mesmo jogador. `Gols` ficou com o que é do JOGO: gol em ambos os tempos,
  próximo gol, linha decimal.
- **`25%` / `50%` no título é odd TURBINADA, não mercado** (24 linhas). Ele
  escreve a conta no canal: `2.02 + 25% = 2,27@`. Mesma família do `aumentada`
  do Rogerin e do `SuperMúltipla` da Estrela Bet.
- **` e ` separa PERNAS** em 12 títulos que combinam sem dizer "dupla"
  (`Priske e Tolaj` @24,96). Com 3 pernas declaradas o esporte vira `Múltiplos`.

### O `%` tem DOIS papéis na mesma fonte — e o segundo é a stake vazando

`Cuevas Christian Chutes +2 0.50%` não é bet builder: o `0.50%` é a **stake**
(u=0,50) escrita dentro do título. Lido como turbinada, ele transformava duas
apostas de `Chutes` em `Múltipla`. O mesmo vale para `- 1.50` no fim de
`Forson +2 Chutes - 1.50`, que viraria **handicap** (nesta fonte é o SINAL que
declara handicap).

A limpeza só corta o sufixo **quando o número é exatamente a stake da linha**, e
é essa condição que mantém `cruzeiro -1` (stake 2,50, handicap de verdade)
intocado. A categoria lê o texto já limpo — senão o mesmo caractere decide duas
coisas contraditórias.

### Prefixo `GV`, conferido contra a coluna INTEIRA

`GR` (233), `GT` (35), `GG` (8), `GX` (35) e `GP` (34) estão todos ocupados por
**código NATIVO da bet365** (`GR3383912251I`) — duas letras mais dígitos, que um
regex ancorado em `XX<aaaamm>-<n>` **não enxerga** (regra da s316). `GV` é o
único par com G livre: 0 linhas.

⚠️ **Ele vai usar o bot** (canal `-1003928624343`, apoio `-5577016989`). No dia em
que o bot entrar, suba o contador (`/contador N`) para além de **`GV202609-32`**
antes da primeira aposta — planilha e bot escrevem na MESMA série.

### Anotado, não resolvido

- **18 linhas `Nome N+` sem mercado** (`Julio Enciso 3+`, `Sebastian 2+`): nem o
  canal diz qual é. Vão para `Player Props` — a gaveta do §3 —, nunca para o
  total do esporte, que inventaria um objeto que ninguém escreveu.
- **`Betsson` é casa nova no banco** e entrou nos 4 mapas de favicon
  (`data.js` tem `CASA_ICONS` **e** `HOUSE_DOMAIN`), com o domínio **medido** no
  link do canal (`betsson.bet.br`), não deduzido do nome.

### `SOA` era `score or assist` — a inferência razoável estava errada

Perguntado, respondido no mesmo dia: **`SOA` = "marcar OU assistir"**, não chute
no gol. As 5 linhas foram para `Player Props`, junto com o `G/A` do mesmo arquivo
— é o mesmo mercado escrito de dois jeitos, o §3 não tem categoria para ele, e
escolher `Anytime` ou `Assistência` sozinhas jogaria metade do mercado fora.
Base reimportada (o script é idempotente por `origem='import'`): 956 linhas, a
reconciliação segue em **0 divergências**.

A inferência era razoável e ainda assim falhou: `SOA` e `SOT` aparecem na MESMA
escada e os dois pareados com `Anytime` (`Kvam SOA 2.00%` + `Kvam Anytime
1.00%`), o que fazia um parecer variação do outro. **Vizinhança tipográfica não é
significado.** Sigla que não aparece por extenso em lugar nenhum da fonte só se
resolve perguntando ao dono — e o que fez a pergunta acontecer foi ela estar
marcada como inferência declarada no relatório, em vez de passar como fato.

### O atraso do canal: 196 apostas que nunca chegaram ao tracker

Ele parou de planilhar na msg **969** (01/09 22:04) — a fronteira veio do Feca e
confere: nenhum bilhete de lá em diante aparece no CSV, que termina no lote de
01/09 23:28–23:35. Do 969 até a última mensagem do export (1110, 06/09 15:51) são
**79 mensagens de aposta e 196 linhas**, agora em `GV202609-33 … GV202609-228`
(`scripts/import_grego_canal_s325.py`). Base do dono: **1.152 bilhetes**, 83 em
aberto — o que não tinha marca entra sem resultado e ele completa à mão.

**A fonte aqui não é planilha nenhuma: são os 79 PRINTS.** A legenda dá stake e
marca; o print dá odd, seleção e confronto. E o print carrega mais do que a
legenda: **67 das 196 linhas (34%) têm legenda CEGA** (`1.50%`, sem nome) — sem a
imagem elas não existiriam.

### O pareamento stake ↔ seleção tem três conferências, e todas foram usadas

É onde esse tipo de trabalho erra em silêncio: legenda fora de ordem põe o valor
certo na aposta errada **sem o total mudar**.

1. **A caixa de valor do print traz o R$ igual ao `%` da legenda.** Na msg 990 o
   print mostra R$ 2,00 / 0,50 / 0,50 / 0,25 e a legenda diz `2.00% / 0.50% /
   0.50% / 0.25%`. Pareamento vira conferência, não suposição.
2. **A escada de odd** — limiar maior, odd maior, stake menor.
3. **O nome, quando a legenda o traz, MANDA sobre a posição.** Na msg 986 a
   legenda está fora de ordem (`+2`, `+4`, `+3`) e o print em ordem: quem pareia
   por posição erra duas das três.

Para a combinada, o produto das pernas confere a odd do cupom — msg 1085 dá
`1.95 × 1.98 × 2.50 = 9.65` exato. No `Criar Aposta` da Betano o produto fica
ACIMA do pago (a casa corta a combinação do mesmo jogo): ali vale o print.

### O gate que não depende de eu ter lido certo

As marcas foram contadas por regex sobre as 79 mensagens, **sem olhar print
nenhum**: `❌ 73 · ✔️ 40 · ⌛ 15 · sem marca 68`. A leitura dos prints produziu
**73 L, 40 W e 83 abertas (15 + 68)** — fecha nos três.

Provado por mutação, **4 de 5**: trocar `W` por `L`, trocar `L` por aberta,
remover uma linha e duplicar uma linha quebram o gate. **A 5ª escapou e está
escrita no código:** trocar a *stake* de uma linha passa reto. O gate conta
MARCAS e LINHAS, não confere valor — a conferência de stake é a do item 1 acima,
feita a olho, e não é automatizável sem reler as 79 imagens.

### Três coisas que só o print contou

- **Bet builder disfarçado de simples.** A legenda diz `Tyreece chutes 2+`; o
  print mostra `Criar Aposta @1.70 = 2+ Chutes + Over 0.5 Gols`. São 26 múltiplas
  no lote, e várias chegam assim — nomeadas pela perna que interessa a ele.
- **Cupom que a legenda NÃO menciona não entra.** Nas msgs 1046 e 1055 o print
  mostra o construtor montado, mas a legenda declara duas SIMPLES com odd própria
  (`1.25% @2,42❌ | 1.25% @1.95✔️`). São duas apostas, não um cupom.
- **A odd do print vence a da legenda quando o dinheiro depende dela.** Msg 1062:
  legenda `@3.5`, print `3.60` — e o print se prova sozinho (`R$4,50 ÷ R$1,25`).
  É `W`, então a odd entra no P/L. Já na msg 1057 (legenda `@1.39` × print
  `2.22`) o bilhete é `L` e a odd não muda nada: fica a da legenda, com a
  divergência anotada.

**Descrição no formato do MASTER** (decisão do Feca): `Entidade - Mercado
[Confronto]`, com `v` no confronto e a conversão `Mais de 2.5 → Over 2.5`. **A
forma da linha segue a CASA** (§10.1 × §10.2): Betano/MGM vendem discreto
(`3+ Chutes`), bet365/Superbet vendem contínuo (`Over 2.5 Chutes`) — reescrever
uma na outra seria inventar apresentação.

⚠️ **`origem='extracao'`, e a idempotência é por FAIXA DE CÓDIGO.** Com
`origem='import'` um reimport do tracker levaria estas 196 junto, em silêncio (o
importador apaga por origem antes de reescrever). O `DELETE ... WHERE
codigo_bilhete = ANY(...)` não depende de origem e não encosta no que o bot vier
a escrever.

### Os dois ids do Telegram, conferidos por `getChat`

    canal oficial  -1003928624343  channel  'Grego Tips - VIP'  bot = administrator ✔
    apoio          -5577016989     group    'sharpenbot'        bot = MEMBER

O apoio **não migrou para supergrupo** (o id `-5…` responde, sem
`migrate_to_chat_id`), então o tenant não nasce surdo — a armadilha da s316 não
se aplica aqui.

**Renomear o apoio para `Apoio - Grego` FALHOU** e não foi insistido:
`setChatTitle` → `Bad Request: not enough rights to change chat title`. O bot é
membro comum ali. Ou ele é promovido a admin com "alterar informações do grupo",
ou o Feca renomeia na mão.

### Pendência que não é desta sessão

**O perfil do bot (8º tenant) NÃO foi feito** — o escopo desta sessão era só o
import. O recon do canal já está medido: 1.074 mensagens, 31/07 → 06/09, 621 com
print, formato irmão do Soh Props (1 linha por aposta, stake em `%`, marca
`✅`/`✔️`/`❌`/`⌛` na própria linha, casa pelo NOME no rodapé, `⏰` com a hora do
evento). Falta medir se ele EDITA a mensagem para marcar depois — é o que decide
`legendaOpcional`/`recompoePorLegenda`.

---

## Sessão 324 — botão que não leva a lugar nenhum

### Botão que não leva a lugar nenhum confunde mais que botão ausente

O relato veio do uso: *"cadastro com telegram ainda não está funcionando… as pessoas
apertam e nada acontece"*. O `Entrar com Telegram` do `/login` saiu da tela.

- **Só o botão saiu.** O backend segue inteiro — `/auth/telegram/ir`,
  `/auth/telegram/retorno`, `POST /auth/telegram`, `/auth/metodos` e os 27 testes
  do fluxo. Não é rollback do login social, é tirar da vitrine o que não conclui.
- `temSocial` deixou de olhar `m.telegram`: senão o separador **ou** acenderia
  sozinho, sem botão nenhum embaixo (a mesma família do `display` vencendo o
  `hidden`, anotada logo acima no CSS).
- O gate de fail-safe (`test_botoes_sociais_nascem_escondidos_no_markup`) parou de
  listar ids na mão — varre `class="btn-social" id="…"` por regex, para não
  quebrar quando um botão sai nem passar batido quando um entra.
- `test_botao_telegram_esta_fora_da_tela` trava a decisão e **diz como desfazê-la**
  (devolver o `<a>`, voltar o `temSocial`, apagar o teste).

Provado por mutação: devolvendo o `<a id="btn-telegram">` os **dois** gates
falham. Suíte: **717 passed, 26 skipped**.

### Causa raiz não investigada — de propósito

Por que o clique não leva a lugar nenhum continua **aberto**. O suspeito de
sempre é o `/setdomain` do BotFather (o `oauth.telegram.org` recusa domínio não
registrado e a página não sai do lugar), mas **não foi medido nesta sessão** — o
pedido era tirar o botão, e diagnosticar mexeria noutro escopo.

---

## Sessão 323 — filtrar um dia zerava o Custo de Contas

### "Filtrei um dia e o custo de contas zerou — mas eu ainda uso essas contas"

Sugestão do tester **Jaao26**, em vídeo. Com o período em **Tudo**, o KPI dizia
`Custo de Contas −R$ 3.100,00`; filtrando **05/09 → 05/09**, virava **R$ 0**, com
o parque inteiro em uso. Nas palavras dele: *"ele acaba contabilizando esse custo
de contas só no dia que você cadastrou essa conta, então não no todo período (…)
ele mostra que o meu custo de conta é zero, mas ele não necessariamente é zero
porque eu ainda estou usando essas contas."*

> **Método:** o vídeo tem áudio, e a tela sozinha apontava para o alvo ERRADO. Os
> frames mostram o custo de tipster cobrando o mês inteiro ao lado do zero, e a
> primeira leitura foi que a queixa era esse contraste. Era o oposto: ele queria
> que o custo de CONTA não zerasse. `imageio-ffmpeg` + `faster-whisper` transcrevem
> offline nesta máquina — ver [[video-audio-transcricao-local]].

### A régua velha lançava o custo em UM dia

`calcCostFiltered` cobrava a conta quando a **primeira aposta liquidada** dela
caía no intervalo `[menor, maior]` data das **linhas filtradas**. Três defeitos
saíam de um desenho só:

- filtrar qualquer dia que não fosse o da estreia dava **R$ 0**;
- recorte **sem aposta nenhuma** zerava o custo, mesmo com o período na tela;
- conta **comprada e ainda não usada** não existia nesse mapa — entrava nos
  R$ 3.100 da aba Custos e **nunca** no KPI. Os dois números discordavam por
  construção, e o tester elogiou o comportamento da aba sem saber disso.

### A régua nova: o custo existe enquanto a conta existe

Decisão do Feca, escolhida contra uma alternativa de rateio que ele recusou —
*"o custo da conta é único, ele é pago na compra"*:

```
ini = menor(adquirida_em, 1ª aposta)
fim = maior(última aposta, arquivada_em)   — e HOJE p/ conta ativa ainda sem aposta
```

Todo período que **cruza** `[ini, fim]` cobra o custo **cheio** daquela conta.
Comprou dia 01 e usou até o 22: qualquer recorte dentro disso cobra; o dia 28 não
cobra; o mês inteiro cobra uma vez. **Não há constante arbitrária** — o fim vem do
uso, que é dado que já existia.

> ⚠️ **A régua NÃO é aditiva, e isso foi aceito com o preço na mesa.** Somar os
> dias de setembro dá muito mais que o custo de setembro, e o P/L Líquido de um dia
> passa a carregar o custo cheio das contas vivas. O Feca confirmou depois de ver a
> conta feita (`3.884,83 − ~3.100 − 577,32`). É o preço de "o custo está lá enquanto
> a conta está viva" — não dá para ter as duas coisas.

### Duas fontes novas, e um escopo que mudou de natureza

`parceiros.adquirida_em` e `parceiros.arquivada_em` (`DATE`). O backfill de
`adquirida_em` é a menor entre `criado_em` e a 1ª aposta — em base importada o
`criado_em` é a data do **import**, bem posterior às apostas que vieram junto. O
`bilhetes.data` guarda **DD/MM/YYYY e ISO na mesma coluna**, então o backfill lê as
duas formas com `to_date` (tolerante, nunca levanta) e roda dentro de um `DO` com
`EXCEPTION`: erro no `SCHEMA_SQL` faz rollback do schema **inteiro**, e este
backfill é conveniência — o init não é.

O escopo saiu das linhas e foi para o **filtro**: **Casa** e **Operador** descrevem a
conta e recortam o custo; **Esporte** e **Tipster** descrevem a aposta e **não**
recortam mais — a conta Bet365 custou R$ 900 quer se olhe tênis ou futebol.

Arquivar carimba `arquivada_em` (`COALESCE`, para arquivar duas vezes não empurrar o
fim); reativar zera o carimbo, senão a conta voltaria viva com o custo sumido dos
dias em que já está em uso. A data de compra ficou **editável no modal** da conta
(só no modo edição, SharpenCal, `POST /parceiros/{id}/editar`) — o backfill é chute
e sem esse campo não haveria como corrigi-lo.

### Medido na tela real (puppeteer + servidor demo)

| recorte | antes | depois |
|---|---|---|
| Tudo | −R$ 29.400 | **−R$ 29.400** · 102 contas — bate com a aba Custos |
| 1 dia (10/06) | R$ 0 | **−R$ 29.400** · 102 contas |
| 1 dia + Esporte=Tênis | recortava | **−R$ 29.400** (esporte não mexe) |
| 1 dia + Casa=Bet365 | — | **−R$ 17.700** · 43 contas |
| Jan/2027 (sem conta viva) | R$ 0 | **R$ 0** · "nenhuma conta no período" |

Gates: `tests/js/custo_janela_vida.mjs` recorta e executa o `calcCostFiltered`, o
`calcCasaCost` e o `_buildContaVida` reais (mais o `_selRange` do `filters.js`) —
**9 mutações aplicadas, 9 detectadas**; `tests/test_custo_janela_vida.py` guarda a
lista e os gates de leitura; `pytest tests/` **716 passed**; `check-tokens` verde.

### Anotado, não corrigido

`.modal-field label` é `--ink-mute` 10px caixa alta com tracking `.16em` — a Escada
de Tinta manda **`--ink-soft`** para label. É violação **preexistente da classe
compartilhada**, herdada por todos os modais. Dar `--ink-soft` só ao campo novo
criaria dois estilos para o mesmo papel (o que a regra 8 do CLAUDE.md proíbe), então
o campo reusa a classe como está. A correção é de uma linha e vale para todos os
modais — decisão do Feca. Ver [[ui_reference_vs_escada_tinta_label]].

### Pendência que não é desta sessão

`app/static/landing.html` segue modificado no working tree desde **26/08**, sem
commit, e ficou FORA deste commit — como nas sessões 310, 312, 313, 314, 319 e 322.

---

## Sessão 322 — o filtro dizia que estava ligado, e a tabela não obedecia

### O filtro dizia que estava ligado, e a tabela não obedecia

O Feca selecionou **Tipster: Fatuch** na Base Completa e mandou o print: o chip
`TIPSTER Fatuch` aparecendo em Filtros ativos, o contador em "336 de 336" e a
tabela listando MarcoF1, LBB, F1DP e Fatuch juntos. Nenhum erro, nenhum aviso —
o filtro simplesmente não filtrava.

### A causa é de FORMA, não de regra

`filtrarPagina` (`dash/assets/js/filters.js`) guarda o recorte num `_filterCache`
indexado por página. As entradas desse cache — o `gfs` do período e os Sets do
`MSS` — mudam **por fora** dele. Isso nunca apareceu porque o único caminho de
volta era o `renderPage`, que zera o cache na primeira linha: todo multiselect
caía no `_renderPageDebounced`.

A s317 deu à Base Completa uma barra de filtros própria, cujos multiselects
repintam **só aquela tela** (o `cb`, para não re-renderizar o dash inteiro a cada
clique). A partir daí `applyMS → renderApostas` passou a ler o recorte anterior
à seleção. O período seguia funcionando (ele passa pelo `renderPage`), e é por
isso que a tela parecia meio certa.

> **O contorno num chamador é o que esconde o defeito no outro.** O
> `apostasTirarMS` — o ✕ do chip — já desviava para `renderPage('apostas')`, com
> um comentário explicando o cache. Ele funcionava. Quem mentia era o caminho
> **sem** contorno: o botão OK do dropdown. Fechar o buraco em um dos dois
> chamadores é a mesma família de "blindar metade dos campos é pior que blindar
> todos ou nenhum".

### A correção mora no MUTADOR do estado

Uma linha: `msToggle` zera o `_filterCache` **na entrada**, antes do `return` do
ramo `__all__` (invalidar depois dele deixaria o "Limpar" sem efeito). Quem
escrever a próxima tela com `cb` próprio não precisa saber que existe cache. O
contorno do `apostasTirarMS` saiu junto — dois caminhos de repintura viraram um.

### Medido na tela real, com e sem o fix

Contra o `servidor_demo.py` com puppeteer, clicando no dropdown como um usuário
(botão → opção → OK):

```
com o fix   ANTES 24.000 linhas / 24 tipsters → DEPOIS 238 linhas / 1 tipster
sem o fix   ANTES 24.000 linhas / 24 tipsters → DEPOIS 24.000 linhas / 24 tipsters
```

A segunda linha é o print do Feca reproduzido.

**Gates:** `tests/js/filtro_multiselect_cache.mjs` recorta e executa o
`filtrarPagina`, o `MSS` e o `msToggle` **reais** — **3 mutações, 3 detectadas**
(invalidação removida, invalidação depois do `return` do `__all__`, cache
removido de vez). `pytest tests/` **702 passed, 23 skipped**; `check-tokens`
verde; `node --check` nos dois arquivos. `?v=` bumpado (`filters.js?v=11`,
`apostas.js?v=23`). Backup em `Backups/s322-cache-filtro-base-completa/`.

> **Nota de leitura:** o contador "336 de 336" **não** era sintoma. Ele é
> `apostasFiltered de baseRows`, e os dois lados saem do mesmo `filtrarPagina` —
> filtro de página ligado dá "X de X" mesmo funcionando. O sintoma era a coluna
> Tipster.

### Pendência que não é desta sessão

`app/static/landing.html` segue modificado no working tree desde **26/08**, sem
commit, e ficou FORA deste commit — como nas sessões 310, 312, 313, 314 e 319.

---

## Sessão 319 — o #10 do Só Chutes estava planilhado, com a data de ontem

### O #10 do Só Chutes estava planilhado — com a data de ontem

O Feca relatou que o bilhete #10 do Só Chutes de hoje não foi planilhado.
Não é isso. A linha existe:

```
#10  dJZmL-D1  id=219606  data=03/09/2026  Bet365  stake=1  odd=3,612  W  resolvida
     #10 Mikael de Sousa [CRB v América-MG] // Victor Osimhen [Istanbul Basaksehir v Galatasaray SK]
```

O que está errado é a coluna Data: **03/09/2026**, onde os irmãos do mesmo lote
estão em **04/09/2026**.

Os quatro bilhetes #10 a #13 são três duplas e uma tripla das mesmas três
seleções, postados em 03/09 às 20:04–20:06 BRT para jogos de 04/09. A legenda
não trazia linha de data, então todos nasceram com a data da MENSAGEM. É o
comportamento normal do `datas.js`, não um defeito.

### O que o log mostrou, e o banco não mostrava

A correção foi feita em três dos quatro:

```
[data:sochutes] bilhete #13: 03/09/2026 → 04/09/2026
[data:sochutes] bilhete #11: 03/09/2026 → 04/09/2026
[data:sochutes] bilhete #12: 03/09/2026 → 04/09/2026
```

O `/ajustar #10` nunca rodou. Quem olha o dia 04/09 vê #7, #8, #9, #11, #12 e
#13, e um buraco no lugar do #10. Da cadeira de quem olha, "sumiu da tela" e
"não foi planilhado" são a mesma coisa.

O banco sozinho mostra a data divergente, mas não diz que houve correção manual
parcial. Quem fecha o caso é o log do serviço.

### O lote de hoje bate

#14 a #19 (jogos de 05/09): o log diz `4, 4, 4, 4, 4, 3 novas` e o banco tem as
mesmas 23 linhas. Zero recusa.

### Método

Sessão de diagnóstico. Nenhum arquivo de código tocado. A conferência foi banco
(`bilhetes` do dono `SoChutes`) × log do serviço (`railway logs`).

### Próximo passo

1. Rodar no apoio do Só Chutes: **`/ajustar #10 04/09`**. Ele reenvia ao Sharpen
   e depois faz o `PATCH` — necessário porque a linha já está `resolvida` e o
   UPSERT sozinho não mexe mais em `data`. Mesmo comando que consertou #11, #12
   e #13.
2. Conferir depois: `data` do id 219606 tem de virar `04/09/2026`.

### Anotado, não decidido

Nenhuma regra nova foi decidida nesta sessão, então nada foi escrito em
`CLAUDE.md` nem nos MASTER.

Fica a observação para quando houver decisão: bilhete que nasce com a data da
mensagem nasce assim o **lote inteiro**, e corrigir um a um deixa buraco. Hoje
nada confere se os irmãos de um mesmo lote ficaram com datas divergentes.

### Pendência que não é desta sessão

`app/static/landing.html` está modificado no working tree desde **26/08** (mtime),
sem commit, e o diff cita a s296. Não foi tocado aqui e ficou FORA do commit,
como nas sessões 310, 312, 313 e 314.

---

## Sessão 318 — o zero que não era ausência

### Bilhete de mesmo jogo: a casa precifica só o CONJUNTO

O Feca mandou o print do Só Chutes #12 (04/09). Dupla de mesmo jogo na bet365
(Osimhen + Shomurodov, Istanbul Basaksehir x Galatasaray SK). O cupom mostra
`5.50` no topo e **nenhuma odd ao lado das seleções**. O bot montava a dupla como
produto das pernas: `0 × 0 = 0`.

**Zero passou por tudo.** Post do canal "@ 0.00", planilha com odd 0 e, com as
duas pernas ✅, o P/L de W (`stake × (odd − 1)`) deu **−1u num bilhete ganho**. A
linha tinha stake, tinha resultado, tinha P/L: nenhuma conferência de forma tinha
como reprovar. Quem viu foi o Feca, olhando o post.

Feito no `sharpen-bot` (`8f9f697`): a ausência de odd viaja como `null` (0 se
disfarça de conta feita); a combinação que cobre o **cupom inteiro** recebe a odd
do conjunto (valia só para `tipo === 'tripla'`, e a dupla de mesmo jogo ficava de
fora justamente onde a odd do print é a única que existe); combinação **parcial**
de cupom sem preço por perna fica sem odd e vira aviso no apoio; o post não
imprime `@ 0` nem P/L de W sem odd; o TSV manda a coluna odd **vazia**; o prompt
da visão ensina o formato SGM. Cinco de seis mutações pegas — a sexta é inócua
(`0` e `null` são falsy nos dois consumidores) e está registrada no teste.

Fora do alcance do gate: o prompt da visão. Só print de verdade prova que o
modelo devolve `null` no lugar de `0`.

### O "não tenho o id no Sharpen" era a linha nunca ter existido

O `/atualizaodd #12 5,50` corrigiu o canal, e o bot respondeu que não tinha o id
da aposta. A causa não era o id perdido.

O `/salvar` valida na fronteira (`validar_linhas`), recusa `odd` que não seja
número > 0, devolve as recusadas em `rejeitados` e responde **200**. O bot
ignorava o campo: marcou `planilhado = true`, publicou no canal e seguiu. **A
linha do #12 nunca entrou na planilha**, e a única pista apareceu um dia depois.

Feito (`cf3f620`): recusa **total** vira erro (o apoio avisa e o registro diz que
não planilhou); recusa **parcial** vira aviso persistente por linha; e o mapa
`código → id` se remonta pelas linhas **aceitas** (`rejeitados[].linha` é a
posição no TSV). Antes, uma recusa fazia as apostas BOAS perderem o id junto, e é
o id que o `PATCH` usa para corrigir linha já resolvida. Quatro de quatro
mutações pegas. A regra foi promovida ao `CLAUDE.md` ("Zero não é ausência").

### Estado do bilhete #12

Planilha **certa**, medido no Postgres: id `242225`, código `dJZrL-D1`, stake 1,
odd `5,5`, `W`, P/L **+4,50u**. Uma linha só, sem duplicata. Foi o reenvio do
`/atualizaodd` que a criou — antes dele não havia linha nenhuma.

**Falta um comando**, depois que o Railway terminar de subir: `/repostar #12` no
apoio. O post do VIP foi reeditado com o código antigo, então as duas linhas de
perna ainda mostram `@ 0`. O `/repostar` só redesenha o texto do post.

### Anotado, não aberto

- O aviso "corrigi no canal, mas não tenho o id no Sharpen — ajuste manual no
  dashboard" foi verdade pela metade: o reenvio seguinte criou a linha, e o
  ajuste manual não era preciso. Com o fix de hoje o caso não se repete, mas a
  frase segue sugerindo trabalho que pode não existir.
- Testers não avisados. A mudança é do lado do robô e não pede ação do tester.
- `app/static/landing.html` está modificado no repo desde antes desta sessão.
  Não é desta sessão e não foi commitado aqui.

## Sessão 317 — filtro é UMA superfície, não duas

### Correção: filtro é UMA superfície, não duas

Primeira volta da s317 entregou os filtros novos numa **segunda caixa**, embaixo dos KPIs,
com a barra da página continuando lá em cima. O Feca leu a tela: *"faltou bastante coisa
né? Ex: filtro para Tipster, Casa e Esporte"* — e eles **existiam**, só estavam no outro
cartão. Depois: *"na verdade alguns filtros ficaram lá no topo. Bem confuso"*.

O diagnóstico: partido em dois cartões com um bloco de KPI no meio, o de cima sai do campo
de visão de quem está mexendo no de baixo, e a tela passa a **parecer que não tem o filtro
que tem**. Não era falta de filtro, era falta de superfície única.

Corrigido: a Base Completa monta **uma barra só** (`buildFiltrosApostas`, em
`charts/apostas.js`) e **não chama mais `buildFilters`**. Três zonas no mesmo cartão, com
uma divisória entre as duas primeiras:

1. **carteira** — período · esporte · casa · tipster · conta · operador;
2. **aposta** — resultado (chips) · faixas de stake, odd e P/L;
3. **texto** — busca em aposta/descrição, e o CSV à direita.
   Abaixo, a faixa de filtros ativos com ✕ individual e `Limpar tudo`.

**As peças são as MESMAS das outras 8 telas.** `buildFilters` foi quebrado em
`_grupoPeriodo`/`_grupoEsporte`/`_grupoCasa`/`_grupoTipster`/`_grupoOperador`
(`filters.js`) e as duas barras compõem a partir delas — copiar o markup criaria dois
períodos que divergem no primeiro ajuste. Medido depois do refactor: as 8 telas com
exatamente **1** barra cada, grupos corretos, `abertas` seguindo sem período, zero
`pageerror`.

### O que o /nova-ui não pegou — e por quê

O checklist rodou e fez o trabalho dele: `.money`/`fmtPL`/`moneyStake`, zero cor literal,
Escada de Tinta nos três critérios. Mesmo assim a tela saiu *"fora do padrão"* aos olhos de
quem usa. **O gate cobre o átomo (número, cor, tom, tamanho) e não cobre a composição** —
quantos cartões, onde mora cada controle, se a tela tem uma ou duas superfícies para a
mesma função. Um componente novo pode passar item a item e ainda assim brigar com a tela.

O sintoma barato de reconhecer: **dois estilos para o mesmo papel na mesma tela.** A barra
nova nasceu com `.apf-lbl` (`--ink-soft` 9,5px, correto pela Escada) ao lado do
`.filter-label` da barra antiga (`--ink-mute` 9px, **errado** pela Escada). Duas metades,
uma certa e uma errada, e o olho lê as duas como "inconsistente" sem saber qual é qual.

Resolvido pela raiz, não por cima: `.apf-lbl` e `.apf-ativos__k` foram **excluídos** e a
barra reusa `.filter-label`, que subiu para o papel certo (`--ink-soft`, 9,5px). Junto
foram os outros dois desvios que a s317 tinha só registrado: `.btbl-th` (9px `--ink-mute`
→ 9,5px `--ink-soft`) e `.btbl-counter` (9px → 10px, piso do metadado). Hoje há **um**
estilo de label no dashboard inteiro.

### Nota de método

O `_dataBuiltMs` é setado em `app.js:1296` e o `buildHTML()` só roda em `1327`: script de
captura que espera o flag e renderiza em seguida pinta um DOM que é **substituído logo
depois**, e a tela sai em branco de forma intermitente. Foi o que aconteceu duas vezes na
conferência headless — artefato do script, não do app (o `capturar.mjs` já documenta a
mesma armadilha e resolve com "bounce"). Esperar o `#page-*` existir, e não o flag.

### Sessão 317 (primeira volta) — o desfecho corta a TABELA, não a régua

Filtro de resultado na Base Completa (pedido do tester João Henrique: *"ajuda bastante para
conferir e corrigir valores"*). A decisão que ficou, do Feca: os filtros de texto já mexiam
nos KPIs e está certo — recortar por casa é recortar carteira. O resultado é outra natureza:
filtrar `W` daria **Win Rate 100%**. Então os KPIs leem `apostasKpiRows` (o recorte da tela
sem o corte por desfecho), a tabela lê `apostasFiltered`, e **a tela diz isso numa nota**
enquanto o filtro está ligado — sem ela, ler P/L positivo filtrando `L` parece defeito.

- **Chips de resultado** `W · HW · L · HL · V · Aberta`, multi-seleção, **com a contagem do
  recorte** (é ela que responde "quantas red tenho aqui" antes do clique). Rótulo é o código
  canônico; o nome humano fica no `title`.
- **Faixas** de stake, odd e P/L. Passam pelo `parseNum`, então aceitam `1.250,50` e o minus
  U+2212 de um copiar/colar da própria tela. **Aposta aberta sai de qualquer faixa de P/L**:
  o zero que o feed traz é ausência, e a colocaria dentro de toda faixa que cruze o zero.
- **Conta virou multiselect**; as caixas de texto que duplicavam esporte/tipster/casa por
  substring (`Vinicius` pegava `Vinicius2`) saíram.
- **10 colunas ordenáveis** (eram 4). Resultado em ordem **semântica** — `W · HW · V · HL ·
  L · Aberta` —, nunca a alfabética (`HL, HW, L, V, W`), que não diz nada para quem confere.
- `moneyStake` entrou no dash: §5.1 previa a máscara de 2 casas para valor unitário e o
  dashboard não tinha nenhuma.

Gates: `tests/js/filtros_base_completa.mjs` **recorta e executa** o código real (parseNum,
os cinco matches, o comparador e o bloco de repartição de dentro do `renderApostas`) —
**17/17 mutações detectadas**; `tests/test_filtros_base_completa.py` trava as decisões
estruturais, inclusive a barra única — **10/10**. Duas mutações escaparam na primeira rodada
e as duas eram cegueira do teste, não mutação inócua: faltava ordem natural de dígito
(`conta2` × `conta10`) e P/L **negativo** — sem negativo, o `localeCompare` com
`numeric:true` acertava a ordem sozinho e o ramo numérico não era load-bearing. Uma terceira
escapou porque no caso combinado a faixa sozinha já dava o mesmo número (dado que não
exerce a regra).

### Ainda aberto da sessão 316

**7º tipster público: `Soh Props - Vip`** (`/tipsters/sohpropsvips`). Marca, slug e username
são três strings diferentes, e nenhuma é o nome do arquivo (`SOH PROPS`). Base de 7.276
apostas em unidades, 05/01 a 03/09, `+474,35u` e ROI `+8,21%`. É a primeira carteira
**monomodal** do registro: 100 % prop de jogador de futebol.

O import veio em três CSV disjuntos (`scripts/import_sohprops_csv.py`). Prefixo `SO`, não `SP`:
`SP` parece o óbvio para "Soh Props" e está ocupado pelos códigos NATIVOS da Superbet. Só
apareceu porque a primeira medição usou o regex da série `XX<aaaamm>-n` e ficou cega para eles.

**A barra `/` tem dois sentidos no mesmo título.** Em `1+ Chutes p/ fora` ela abrevia "para";
em `Marcar / 1+ Chutes no gol` separa bet builder. Só ` / ` com espaço dos dois lados é
separador. Havia mais dois (` e `, ` - `), cada um com contraexemplo na própria base
(`Brighton e Hove Albion`; `BN -`; `- CASHOUT`), resolvidos por posição e por mercado.

**O rótulo perdeu para o dinheiro:** `Perdida` com `Lucro=0,00` quer dizer que a stake voltou.
São void, não perda. Depois disso o P/L derivado bate com a coluna `Lucro` em 7.276 de 7.276.

**O bot (`sharpen-bot`), 6º tenant.** A LEGENDA declara quantas apostas há: uma linha de stake
por aposta, na ordem das seleções do print. A marcação mora na linha da stake e chega por
EDIÇÃO. A combinada é resolvida pelas PERNAS, não pela legenda, e a ARIDADE é o portão dela.

Antes do perfil, dois pré-requisitos: **48 casas por HOST** no `casas.js` (84,8 % para 99,4 %
dos links dele; nome não entra porque metade é palavra comum de legenda) e a **data do evento
com a hora colada**, que o núcleo não lia.

**A página `/bot`** (`app/static/bot.html`) é o manual de operação: dia a dia, os 13 comandos e
os avisos. O passo a passo de pôr um tipster no ar saiu dela e foi para
`docs/GUIA_BOT_TIPSTER.md`, que é interno.

**O que caiu em produção, e por quê:**

- O deploy do tenant novo entrou em **crash-loop e derrubou os outros cinco**. O `config.js`
  tinha o bloco e o perfil existia, mas faltava a linha no registro `PERFIS` do `index.js`.
  O guard de boot é fail-closed. Nada acusava: `npm test` e `node --check` passavam. Hoje há
  teste, com o bloco recortado do `index.js` real.
- O id do apoio **envelheceu** quando o grupo virou supergrupo. O roteamento compara
  `msg.chat.id` com o `apoioId`, então o tenant ficava **surdo**: sem erro, sem resposta.
- O JSON da visão veio malformado e **matou o bilhete**. Hoje repara quebra de linha crua,
  pergunta de novo, e o erro diz se foi truncada (`stop_reason`).
- O nome do jogador **sumia** do post e da planilha. O `rotuloPerna` descartava o mercado
  quando a seleção não era número, e no layout de prop da bet365 a seleção é o jogador.

**Pendente:**

- `/repostar` e `/redescrever` no apoio do Soh Props, para o #64 ao #88 pegarem o formato novo
  e a descrição corrigida. São comandos do tipster; não dá para disparar daqui.
- `dia 13 19h` e `domingo 17h` ainda não viram data (cerca de 60 mensagens no histórico dele).
  `amanhã` e `hoje` já viram.
- 22 linhas em `Outros` e 10 em `Player Props` sem mercado identificado, mais os 5 `CA`
  ambíguos. Dependem do tipster dizer o que é.
- **Autosserviço.** Hoje pôr um tipster no ar exige env var no Railway e deploy, ou seja passa
  por nós. O caminho proposto está no fim do `docs/GUIA_BOT_TIPSTER.md`: registro do tenant em
  tabela com tela no `/admin`, e um `/vincular` no apoio para o id se resolver sozinho (o bot
  já sabe o próprio `chat.id`, e ele chega já migrado).


### Ainda aberto da sessão 314

A Caixa Inteligente está no ar. Cada conta pode dizer quanto tinha numa data; a partir daí o
Sharpen projeta o saldo sozinho (lançamentos + P/L das apostas) e confronta com o
que a casa mostra. Divergência acende em âmbar na conta, na lista do Painel e no
KPI "A conferir".

Feito: `caixa_mov` (+ coluna `caixa` na lixeira), `_caixa_projetar` (puro),
`caixa_conta`/`caixa_lancar`/`caixa_excluir_mov`/`caixa_visao`, as 4 rotas
`/caixa/*`, o box na Extração com modal e extrato, a banca no Painel de Contas,
`fmtSaldo` documentado no `UI_REFERENCE §5.1`, `tests/test_caixa.py` (27),
`tests/test_caixa_lancar.py` (14),
`tests/js/caixa_front.mjs` e `scripts/mutar_caixa.py` (9 de 9).

**Anotado, não aberto:** (1) o corte informado numa data PASSADA não consegue
reconstruir quais apostas estavam abertas naquele dia — só as que ainda estão
abertas hoje entram no `abertas_corte`, e o texto do modal diz isso; informar o
saldo de HOJE é sempre exato; (2) o extrato não tem coluna de "saldo após" de
propósito: entre dois lançamentos o saldo muda a cada aposta que liquida, e a
coluna mentiria; (3) conta que muda de dono não existe hoje, mas se existir a
`caixa_mov` precisa do mesmo cuidado que `casa`/`parceiro`.

### Ainda aberto da sessão 313

O card "Cenário Atual" parou de mentir para quem está no vermelho. `Topo
Histórico` nunca mais fica abaixo de zero e `Drawdown Atual` deixou de dar 0 por
construção em toda carteira que mergulhou e está se recuperando. As duas funções
que descrevem a curva partem do MESMO ponto (`peak = 0`).

**Decisão do Feca, anotada e não aberta:** dois desvios do padrão monetário
anteriores àquela sessão ficaram no lugar — o `Drawdown Atual` em R$ 0,00 herda o
vermelho do `data-state="real"` e o `Recovery Factor` negativo imprime hífen ASCII
em vez do minus U+2212.

### Ainda aberto da sessão 312

O modal de conta passou a ser um só para criar e editar. O `prompt()` nativo do
navegador saiu do caminho: `contasEditar` abre o `novaconta-modal` em modo
edição, pré-preenchido, com o nome já partido em Parceiro + Fornecedor — o
operador nunca mais vê nem digita os colchetes do modelo canônico.

Feito: `repository.editar_parceiro` (transação única: `parceiros` + `casa`/
`parceiro` dos bilhetes + assinatura recalculada de cada um), `POST
/parceiros/{id}/editar`, `renomear_parceiro` reduzido a wrapper, o modo edição
no front com aviso de mover, e `tests/test_renomear_parceiro_assinatura.py`
crescido de 4 para 10 casos com as 3 mutações provadas.

**Ficou anotado, não aberto:** contas movidas de casa não têm desfazer — a
operação é reversível na mão (mover de volta), mas não há lixeira como na
exclusão. Só vale construir uma se o Feca vir alguém errando na prática.

### Ainda aberto da sessão 311

**Próximo passo, e é decisão do Feca:** as duas linhas do **WilliamOliveira** que
a medição achou (BETesporte `195072327`, stake 20,00 lida como 18,00; Betano
`20951200252`, stake 164,09 lida como 60,00). Estão erradas no banco, são base de
outro dono, e o script já as traz listadas e comentadas — ligar é tirar o
comentário. O gate novo impede que aconteça de novo, mas não conserta o passado.

**Duas frentes menores que ficaram anotadas, não abertas:**

- O aviso no rail não mostra a correção de stake (o `stake_fix` já viaja no `done`
  do stream). Mudança de UI passa pelo `/nova-ui`.
- A KTO manda `Stake: 1,00` no bloco (bilhete `13062628977`, corrigido à mão pelo
  Jaao26 para 175). É defeito de **captura**, não de tradução — o gate copia o
  bloco fielmente e reproduz o erro da casa.

### Ainda aberto da sessão 309

O perfil do Rogerin deixou de recusar print que não seja da Betano — e, junto,
deixou de transformar N apostas simples num bilhete só. Commitado e pushado no
`sharpen-bot` (`ed14a58`).

O gatilho foi ao vivo, no dia 1 do tenant: ele mandou três prints da bet365 e o
bot respondeu "⚠️ Não consegui ler o print" nas três, porque o prompt da visão
abria nomeando a Betano e fechava com "print ilegível → erro". Atrás desse
sintoma havia dois defeitos que **não** produziriam mensagem nenhuma: a casa do
bilhete nunca vinha do print (ia para o Sharpen como Betano) e as três apostas
simples do print virariam **uma múltipla de odd ~73** com a stake da primeira.

**O que ainda não foi exercido ao vivo:** a visão lendo um print de bet365 de
verdade. O `chamarVisao` está dublado nos testes, e o cabeçalho do bloco diz
isso — o gate prova a montagem, não a leitura da imagem. **O próximo bilhete
dele é a hora de conferir quatro coisas:** as três linhas 🎯 no canal com
2u/1u/0.25u, as três linhas `RG…-S1/-S2/-S3` na planilha, a casa gravada como
**Bet365** (não Betano) e a categoria **Chutes** (não Outros).

**Aberto da sessão 311, e é decisão do Feca porque mexe em `extensor/`:** Betano
(`Tipo: Dupla`) e Betfast (`Tipo: Sistema (3 seleções)`) não emitem o marcador
canônico `Tipo: SISTEMA <rótulo> — <N> apostas de <k> seleção(ões)` nem a
`Odd (estrutural do sistema)` já calculada. Bet365 e Novibet emitem os dois e
acertaram 15 de 15; sem eles a IA deduz a regra da odd (média × produto) e errou
3 vezes, e o `anexar_sistema_tsv` nunca preenche a coluna 12 nessas casas — a base
não distingue um `3 x Duplas` de uma tripla. Fazer as duas emitirem o marcador tira
a dedução do caminho. Exige `node extensor/harness/run.mjs` e caso novo no harness.

**Pendências, em ordem de quem decide:**

0. **`MASTER_RESULTADO §5.3/5.4` merece um adendo sobre MÚLTIPLA** — decisão do
   Feca, herdada da s307. O MASTER descreve meia vitória/derrota como situação
   de aposta **única**, e a fórmula que a planilha usa (`(stake/2) × odd +
   stake/2`) assume que a metade devolvida devolve a **stake**. Numa dupla ela
   ainda corre a outra perna, então `HW` ali pagaria a mais. O bot resolve por
   `W` com `Odd = Retorno ÷ Stake`, que é o mecanismo do cashout (`§5.6`) — mas
   isso hoje está escrito no `sharpen-bot/README.md` e no código, não no MASTER.
   **Mudança em MASTER exige diff revisado e aprovação humana (invariante 1).**
1. **Stake do post: ponto ou vírgula?** — decisão do Feca. O post de N apostas
   mostra `0.25u` (ponto) na linha da aposta e `+2,82u` (vírgula) no total, na
   mesma tela. O ponto é convenção **declarada** do `stakeFmt` (`"stake como no
   mockup do canal"`) e vale nos **cinco** perfis; a vírgula do total vem do
   `plFmt`. Unificar é uma linha, mas muda o post de todos os tipsters — por
   isso não mexi.
2. **Reclassificar as duplas da base do Rogerin** — decisão do Feca. 182 das 212
   linhas da ERA 2 são duplas de 2 pernas (o ` / ` é separador de perna), mas
   entraram como `ML` no esporte de uma das pernas. O certo seria `Múltipla`, e
   `Múltiplos` onde as pernas são de esportes diferentes. Não dá para separar
   pelo título — `A / B` também pode ser confronto real —, então precisa dos
   prints ou da palavra dele. **O P/L não é afetado.**
3. **Duas odds de `0,500`** na base (`Robinson 10+ pt`, `wendell carter jr 3+
   3pt`) são impossíveis. As duas em apostas perdidas, então não mexem no P/L.
   Só ele sabe o valor; corrige na grade.
4. **Avisar o grupo de testers** da página pública nova — perguntei, sem resposta
   ainda. Não é versão de SharpenUp; seria novidade do painel.
5. **`/atualizastake` e `/atualizaodd` nunca rodaram em bilhete real** (s308). O
   caminho está provado por fixture e por mutação; a ida ao Telegram e ao
   Sharpen é justamente o que os testes declaram não cobrir. O PassaTips já foi
   avisado no apoio dele (`message_id 2565`), então o primeiro uso pode vir a
   qualquer momento.
6. **O `#205` ficou no formato antigo** no canal. Do #206 em diante sai no novo.
   Re-renderizar exigiria adaptar o `scripts/rerender_canal.js`, que é da era
   mono-tenant, e rodar contra o volume do Railway. Não vale por um post.

**Também não exercido:** meia asiática (`½✅`/`½❌`) em bilhete real. Ela é rara
por natureza (4 linhas em 813 asiáticas no sistema inteiro, 0 nas 402 dele), e a
regra vem do MASTER e da fórmula do `app/repository.py`, não de bilhete pago.

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
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

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

## 5. Pendências (aguardam bilhete real)

> **Varrido em 10/08/2026 (s261), contra o código e o git.** Motivo: a primeira pendência
> que eu fui atacar (`renomear_parceiro`) **já estava feita desde 26/07** — o §5 misturava
> item vivo com item vencido, e não dava para saber qual era qual sem abrir o código.
>
> As marcas usadas abaixo:
> **✅ VIVA** = confirmada no código nesta data, com o arquivo:linha conferido ·
> **NÃO-MEDIDA** = plausível, mas ninguém provou (falta banco, amostra ou reprodução) ·
> **HUMANA** = depende de ação fora do repo (Feca, Railway, Telegram, extensão).
>
> **Duas coisas que a varredura ensinou, e que valem para a próxima:**
> **(1) Referência de linha apodrece.** Três itens apontavam para linha errada
> (`app.js:1183`, `content.js:911`, `main.py:2354`) — o código andou, o §5 não. Referência
> aqui é **pista, nunca endereço**: confirme por `grep` do símbolo antes de agir.
> **(2) A ausência de marca não é "vivo".** Item sem varredura é item **não verificado** —
> e o custo de descobrir isso no meio da execução é meia sessão.

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Bet365 — sistema, as 3 linhas `L` congeladas (s265). HUMANA + NÃO-MEDIDA.** O conserto da
  odd de sistema vale para captura nova, e as **10 abertas** se corrigem sozinhas na próxima
  passada do robô (o `ON CONFLICT` refresca `odd` enquanto `extraction_state='aberta'`). As **3
  já resolvidas como `L`** ficaram com a odd do produto e o UPSERT **não** as toca. Corrigir
  exige a odd **por perna**, que o banco não guarda → só re-lendo o bilhete na casa. Não mexer
  sem o Feca: `L` não move P/L (perda = −stake), então a urgência é baixa e o risco de UPDATE
  cru é alto. Medir de novo com `python scripts/medir_sistemas_bet365.py` (read-only).
- **Bet365 — sistema SEM irmão só some na base ANTIGA (s265, 2ª parte). ✅ RESOLVIDA para
  frente, HUMANA para trás.** A partir da 0.6.45 a captura grava `sistema`/`sistema_linhas`,
  então bilhete novo é medido sem heurística (`sistema IS NOT NULL`) — e como a estrutura
  atravessa o congelamento do UPSERT, **re-capturar bilhete antigo faz backfill**. O que ainda
  não aparece é só o que nunca foi re-capturado: ali valem as heurísticas de irmão, que perdem
  quem apostou só as duplas. Fecha sozinho conforme o histórico for re-passado; medir com
  `python scripts/medir_sistemas_bet365.py` (a seção **(0)** é a exata).
- **Trixie / Yankee / Lucky na captura (s265). NÃO-MEDIDA — sem bilhete real.** Sistemas que
  **misturam** tamanhos de linha não fecham `C(n,k) = BC`, então o robô entrega o dado e manda
  calcular pelo `MASTER_RESULTADO §7` em vez de emitir número. Nenhum apareceu nos payloads
  vistos até aqui; com um bilhete real dá para travar a fórmula deles no harness também.
- **Betfair:** cashout **parcial** (`isPartialCashOut`) sem amostra — o total já está travado no harness (2 casos) · HW/HL sem amostra · Each Way com `0 < Retorno < Stake` (o §5 não cobre essa faixa; hoje sai "a conferir", sem chute)
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

- **Betfast / Tivo (s211):** cashout · bônus · aposta de sistema · outright · **aposta ABERTA** (as 50 da amostra são liquidadas) · `§9` de duas categorias (`Total de defesas do goleiro` · `Handicap de mapas`/`Map Advantage`)
- **Jonbet:** ~~captura NÃO validada ao vivo~~ **VALIDADA na s249** — a extensão capturou na 1ª tentativa e gravou **13 bilhetes** (3 W · 7 L · 3 abertas), com código, stake e odd conferidos no banco. **A coluna Data ficou provada ao vivo:** saiu 04/08 (3) · 05/08 (4) · 06/08 (3) · **07/08 (3)**, e as 3 abertas são justamente as de 07/08 — eventos futuros, que a data de **colocação** teria carimbado em 05 ou 06/08. **Falta só a conferência visual do Feca contra o card** (contagem e datas lado a lado). Segue sem amostra: **cashout executado** · múltipla · bet builder · sistema · `half-won`/`half-lost` · `void`/`refund`/`rejected` · **boost** (`boost:false` em tudo) · **imposto** (`payout_tax:"0"` e `taxes` ausente — quando aparecer, decidir de uma vez se o `W` usa retorno bruto ou líquido, ver `CASA_JONBET` Feedback #2). `§9` só tem os 3 mercados de badminton confirmados.

- **Betboom (s250):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados, mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.38**), **Ctrl+Shift+R** em `betboom.bet.br`, Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **A leitura crítica é a DATA** — nesta casa colocação e evento divergem em **7 de 7**, e a coluna Data tem de sair com a do **evento**. Sem amostra (a conta tem 7 bilhetes, todos simples, badminton): **cashout executado** · múltipla · bet builder · sistema · `half-won`/`half-lost` · `void`/`refund`/`rejected` · boost · imposto. As abas `Cashout efetuado`, `Canceladas` e `Reembolsadas` **existem na tela** mas vieram vazias — quando encherem, elas fecham buracos das **duas** casas BetBy de uma vez. `§9` só tem 2 mercados confirmados (`Vencedor`, `Handicap pontos`); `Total pontos` está na Jonbet e **não** foi importado para cá de propósito (camada fina).

- **Stake (s257):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados (inclusive o replay, contra o servidor real), mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.41**), **Ctrl+Shift+R** em `stake.bet.br`, Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **As duas leituras críticas são o STAKE DA ANULADA** (tem de sair `34,45`, não `0,00`) e o **resultado da anulada** (`V`, não `L` — o dinheiro é o mesmo zero da perdida). Sem amostra (a conta tem 17 bilhetes, todos múltiplas de 2 a 4 pernas, futebol e tênis): **simples** (`bet_type` foi `1` nas 17 — não há de-para provado para esse campo) · **boost** (`*_boosted` todos `null`, embora a home anuncie promoções) · **cashout executado** (os campos `bet_cashout_*` só existem no endpoint de ABERTAS; que `bet_status` sobra depois de sacar é desconhecido) · freebet/bônus (`bet_bonus_type` sempre `null`) · bet builder · eSports · `half-won`/`half-lost`. `§9` só tem 6 mercados confirmados; `Total asiático` está mapeado para `Gols` pelo princípio do objeto, **sem sinônimo no MASTER** (registrado no Feedback da casa).

- **Pitaco (s270):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados
  (o replay rodou contra o servidor real, 200 e resposta idêntica à da tela), mas nenhum lote
  passou pela extensão. Fazer: recarregar a extensão (**0.6.46**), **Ctrl+Shift+R** em
  `pitaco.bet.br`, abrir **Minhas Apostas**, Conectar → "Copiar bilhetes". **As duas leituras
  críticas são do bilhete `80010000038606210`: a ODD tem de sair `3,6795` (não `3,67` — a casa
  exibe a odd arredondada e ela erra R$ 0,95 no retorno) e a DATA tem de ser a do evento,
  `15/08`, não a da colocação, `14/08`.** Conferir também que o lote traz **71** bilhetes (49
  finalizados + 22 abertos) e não 31 — 31 é o que a paginação por página devolveria, e é
  exatamente o defeito que o inject evita. Sem amostra: **bilhete simples** (a conta tem 51
  duplas e 20 triplas, nenhuma simples) · **cashout executado** (o filtro "Encerradas" veio com
  0 cards, embora o campo `.7` exista nas abertas com o valor de encerrar) · boost · freebet ·
  HW/HL. O `§9` tem 15 rótulos confirmados de 162 pernas reais. **A grafia já está unificada**
  (2ª parte da s270): a casa é `Pitaco` em toda a base — 57 bilhetes, 5 contas, resíduo zero
  da grafia velha e as 57 assinaturas conferidas contra o que a próxima captura vai gerar.

- **Novibet (s271):** o inject foi validado ao vivo — o `nv_inject.js` real rodou na página
  logada contra o servidor da casa e trouxe **42 bilhetes / 42 códigos únicos** (7 abertas,
  19 sistemas), com `hook:true`, `fim:true`, `truncado:false` e sem erro. Sem
  amostra: **bilhete simples** (a conta tem 3 de 2 seleções e 39 de 3) · **cashout executado**
  (`cashout` null em 42 de 42 — o card oferece, mas o preço vem por outro canal) · **imposto**
  (`withholdingTax` 0 em 35 de 35) · freebet · `costDiscount` · `isBanker` ·
  `overriddenResult` · e qualquer `result` fora de {Won, Lost, Pending} — **não há
  anulada/void na amostra**. O `§9` tem 34 rótulos confirmados de 123 pernas reais.

- **PassaTips VIP — o bot está pronto e PARADO num passo humano (s273). HUMANA.** Falta
  `PT_APOIO_ID`: **a Bot API do Telegram não cria grupo** (só cliente MTProto), então o
  apoio tem de ser criado à mão — Feca + `@passapano` (id `8290339271`) + `@sharpenbetbot`
  como **admin** (apagar mensagens e fixar). Falta também `SHARPEN_SENHA_PT` no Railway.
  O destino já está conferido por `getChat` (`-1003907895270`, `type: channel`) e o bot já
  é admin lá com `can_post_messages`/`can_edit_messages`. O tenant é **inerte** sem
  `PT_APOIO_ID`, então o código já em produção não faz nada até isso existir. **A 1ª
  captura ao vivo tem duas leituras críticas:** o bilhete tem de sair com o **esporte
  certo** (o padrão novo põe na 1ª linha) e a **casa vinda do host do link** — é o que a
  correção do `embutirLinks` destravou, e nenhum lote real atravessou a ponte ainda.
  Contador semeado em `data/passatips/contador.json` = **258**; a próxima do canal é a
  **#259**.
- **`Cobranças de lateral` e `Tiro de meta`: a régua ficou desalinhada de propósito
  (s273). NÃO-MEDIDA.** São a mesma família de `Faltas` (estatística de jogo), mas caem em
  lugares diferentes — lateral em `Outros` e tiro de meta em `Team Props`, por sinônimo
  explícito do `MASTER_APOSTAS §4`. A s273 criou **só** `Faltas`, que era o aprovado.
  Decidir se as duas viram categoria ou as duas viram `Outros` é mudança própria, com a
  regra de propagação inteira. Registrada no Feedback #2 da `CASA_BETFAST`.
- **PassaTips — 3 passos humanos para fechar o buraco do #259 (s276). HUMANA.** O
  `/contador 271` já foi feito (18/08 09:33), então daqui para frente está limpo. Falta:
  **(1)** o tipster **repostar a aposta de hoje** no apoio (`Futebol` / `Over 3.5 gols -
  @2,25 (1,00u)` / link Betnacional) — ela virá como **#272**, porque hoje ela **não está
  na base**: o bot salvou às 09:20 sobre a linha importada `PT202608-259` e foi absorvida;
  **(2)** `/anular #259` para desarmar o painel antigo — ⚠️ isso **apaga** a linha
  `Under 1.5 cartões Elche` (17/08, id 186709), porque o bot guardou o id dela por engano;
  **(3)** reimportar a planilha, que recria essa linha exata. **Ordem importa: (1) antes de
  (2).** Enquanto o painel do #259 estiver armado, um clique ✅ vira o `L` do dia 17 em `W`
  (`resultado` não é congelado).
- **Zora — falta `/ressincronizar` (s276). HUMANA.** Só Chutes (62/62) e Rei do Criquete
  (65/67, 114 linhas repostas) já foram. A Zora é o único tenant que não passou; ela tem 17
  bilhetes e a última escrita é de 02/08, então provavelmente não há nada a repor — mas isso
  é dedução, não medição.
- **As 3 senhas de tipster no Railway podem sair (s276). HUMANA.** `SHARPEN_SENHA`,
  `SHARPEN_SENHA_ZORA` e `SHARPEN_SENHA_RC` só servem de fallback agora. Com os quatro
  botões ligados no `/admin`, apagá-las fecha a porta velha. Confirmar antes no log do boot:
  cada tenant loga `[sharpen:<user>] token de serviço`.
- **O auto-deploy do `sharpen-bot` não está disparando com o push (s276). NÃO-MEDIDA.** O
  `casaPorHost` foi commitado às 12:07 e o bilhete `#131` falhou às 12:20 dizendo "não achei
  a casa" — código commitado e não rodando. É a mesma causa do `PT_APOIO_ID` não ser lido.
  **Deploy que não acontece é falha silenciosa:** o bot segue no ar respondendo, com código
  velho, e só se descobre por sintoma lateral. Investigar o gatilho do GitHub nesse serviço;
  até lá, conferir a aba Deployments depois de cada push.
- **O botão "Atualizar dados" mente na página pública `/tipsters/<slug>` (s276). ✅ VIVA.**
  A rota aceita e **ignora** o `?refresh=1` de propósito (cache de 5 min, `_PUBLICO_TTL`), e
  o botão promete algo que ela recusa — F5 e Ctrl+Shift+R também não furam, porque o cache é
  de servidor. Custou 4 minutos de "quebrou tudo" na s276. Duas saídas, decisão do Feca:
  esconder o botão no modo público (com rótulo "atualiza a cada 5 min") ou deixar o refresh
  furar o cache com teto por slug.
- **`Faltas` abriu uma régua desalinhada, de propósito (s273). NÃO-MEDIDA.** `Cobranças de
  lateral` e `Tiro de meta` são a mesma família e caem em lugares diferentes (`Outros` ×
  `Team Props`). Decidir se as duas viram categoria ou as duas viram `Outros` é mudança
  própria, com a regra de propagação inteira. Registrada no Feedback #2 da `CASA_BETFAST`.
- **Imposto no `W`: bruto ou líquido? A decisão continua ADIADA, agora com duas casas
  esperando (s271).** A Novibet é a **primeira casa nossa com imposto explícito no payload**
  (`settlement.withholdingTax` + `taxBonus`), mas veio **0 em 35 de 35** — então dá para
  registrar o campo sem decidir a regra. A mesma pergunta está aberta na `CASA_JONBET`
  (Feedback #2, `payout_tax`). **Quando aparecer o primeiro bilhete com imposto ≠ 0, decidir
  de uma vez no `MASTER_RESULTADO`** e propagar às duas — decidir por casa criaria duas
  verdades para a mesma regra global.

- **Bot Sharpen — bilhete #21 do Só Chutes ainda está SEM a dupla (s252).** O fix está no ar (`dde8141`), mas ele não age sozinho sobre o passado: a recomposição roda quando o Telegram entrega um `edited_message`. **Fazer: editar a legenda do #21 no apoio outra vez.** Ela já diz `0,25u dupla`, então basta uma edição qualquer (pôr e tirar um espaço serve) para o bot responder `➕ Bilhete #21: acrescentei Sanguinetti + Sen 0.25u @ 9.75`, atualizar o post e planilhar. **O post do canal não é anulado nem renumerado** — os 28 👍 ficam. Qualquer pessoa com permissão de editar a mensagem serve; o bot escuta a edição, não quem editou. A dupla nasce **aberta** e a odd sai como produto das pernas (3,25 × 3 = 9,75), que é o que o card mostra; se algum dia divergir por boost ou arredondamento da casa, `/ajustar #21` com a foto crava a odd certa. **Sem amostra ainda:** a recomposição nunca rodou contra o Telegram de verdade, só contra o registro reconstruído no teste.

- **Bot Sharpen no Railway (s251) — falta o smoke test de ponta a ponta, que é do Feca.** O serviço está no ar e verificado por fora (contador conferido de volta do volume, `login ok` nas duas contas, fila do Telegram drenando), mas **nada passou pelo Telegram ainda** — eu não tenho acesso ao app. Fazer: mandar `/status` no apoio do Só Chutes; se responder com os bilhetes do mês, o caminho todo fechou. Sobraram dois diretórios aninhados de uma tentativa de upload (inofensivos, o `storage.js` não os lê), e **o CLI recusa deleção pedida por agente** — rodar `railway volume files delete --volume sharpen-bot-volume /sochutes/sochutes` e o mesmo para `/zora/zora`. **Solto (segurança):** o `SHARPEN_SENHA` do `SoChutes` tem **4 caracteres** numa conta de produção exposta na internet; trocar é `.env` → `scripts\exportar_env_railway.ps1` → `railway redeploy`. Detalhes de operação vivem no `README.md` do repo do bot, não aqui.

- **Betpix365 (s258):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados (inclusive o replay e a paginação, contra o gateway real), mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.43**), **Ctrl+Shift+R** em `betpix365.bet.br`, abrir **Minhas Apostas**, Conectar → "Copiar bilhetes". **A leitura crítica é a ODD DA MÚLTIPLA `5255274526`: tem de sair `4,23`, não `4,08345` nem `4,08`** — a casa paga "Ganhos extra" (R$ 0,15) por fora da odd, e é a 1ª casa Altenar em que a odd declarada não explica o retorno. Conferir também que o lote tem **9 bilhetes** (a conta inteira) e não 0 — se vier 0 com hook ATIVO, o aprendizado do molde falhou (sessão expirada ou path mudado), **não** é tela errada. Sem amostra (a conta tem 9 resolvidas e **zero abertas**): **aposta em aberto** (a armadilha do `totalWin` potencial não pôde ser verificada aqui — segue travada nos harnesses da VaideBet e da Esportiva) · cashout executado (`cashOutValue: 0` em 9/9) · V/HW/HL · freebet · aposta ao vivo (`isLive: false` em todas) · qualquer esporte além de **futebol** (`sportTypeId: 1` em 9/9) · os 7 valores de `status` fora de {0,1,2}. O `§9` tem 9 rótulos confirmados, de **uma** conta pequena — a lista vai crescer.

- **Jogo de Ouro — 1ª tentativa ao vivo FALHOU (10/08). Diagnóstico feito, conserto NÃO aplicado.** O Feca capturou e recebeu `Jogo de Ouro: 0 bilhetes. Hook: ATIVO · respostas da API: 0 · bilhetes vistos: 0 · abra o histórico COMPLETO`. **A causa raiz do lote vazio ainda não foi medida** (falta a versão da extensão e o console do Feca), mas a investigação achou um defeito certo: **a s258 mudou o mecanismo e deixou 3 lugares mentindo.** O `vb_inject.js` ganhou `RX_APRENDE = /widget(?:Expanded)?BetHistory/i`, que aprende url+headers de **qualquer um** dos dois widgets e reescreve o path no replay. Ou seja, desde a **0.6.43 o painel lateral já serve de molde e a tela cheia deixou de ser obrigatória**. Só que o `git show b59c3cc --stat` confirma que a s258 **não tocou** `extensor/content.js`, `casas/CASA_JOGODEOURO.md` nem `extensor/harness/casos/jogodeouro.mjs`. Então: o toast (`content.js:867`) manda abrir a tela cheia, o comentário do ramo (`content.js:811-815`) afirma que só o expandido é casado, e a tabela do `CASA_JOGODEOURO §2.1.1` diz que o compacto **não** é capturado. Os três são pré-s258. **O `vb_inject.js` está certo; a documentação e a dica é que ficaram para trás.** Pior: `respostas: 0` hoje **mistura três causas** e o toast escolhe uma delas às cegas — (a) aba aberta antes da 0.6.43, sem POST novo (o SPA já tinha os dados em memória); (b) molde aprendido e **replay falhou** (Bearer expirado → 401); (c) endpoint mudou. **Medição que separa as três, e que só o Feca pode fazer:** versão em `chrome://extensions` + console filtrado por `[SharpenUp`, onde `hook instalado em`, `requisição capturada p/ replay` e `erro no replay` decidem. **Conserto proposto, aguardando aprovação:** (1) trocar o `extra` da Jogo de Ouro pelo texto da Betpix365 (recarregar / refazer login); (2) mandar no heartbeat se o **molde foi aprendido** (`reqCtx != null`) e o **último erro do replay**, para o toast apontar a causa em vez de chutar; (3) corrigir a tabela do `§2.1.1`; (4) travar o caminho novo no `casos/jogodeouro.mjs`, servindo **só** o compacto e exigindo lote cheio (hoje só o `betpix365.mjs` cobre isso, e o caso da Jogo de Ouro ainda entrega o expandido em `urlsExtra`). **✅ A metade documental do diagnóstico foi RECONFIRMADA na varredura da s261**, contra o código: `vb_inject.js:47` tem mesmo o `RX_APRENDE = /widget(?:Expanded)?BetHistory/i` (e `:133` aprende por ele), enquanto o toast (`content.js:869`) segue mandando *"abra o histórico COMPLETO"* e a tabela do `CASA_JOGODEOURO §2.1.1:59` segue marcando o compacto como **"Não"** capturado. Os dois estão errados desde a 0.6.43. **A causa raiz do lote vazio continua NÃO-MEDIDA** — isso não muda sem o console do Feca. **Não aplicado de propósito:** mexe em `vb_inject.js` e `content.js`, compartilhados pelas 4 casas Altenar, e o harness está verde (14 casos, 237 bilhetes) — mudança própria, com gates, depois da medição. Ao capturar de novo, conferir contagem/datas/odds/código contra o card; a odd é sempre a **pós-boost** (10 de 10 turbinados). Sem amostra: **aposta em aberto** (a conta tinha zero) · cashout executado · V/HW/HL · bônus · múltipla de jogos diferentes · qualquer esporte além de futebol · os 7 `status` fora de {0,1,2}. O **§9 (mapa de mercados) é herdado da era print e NÃO foi revisado** contra o payload: a amostra da API trouxe rótulos que ele não lista (`1º tempo - 1x2`, `1º tempo - total de escanteios`, `Chance dupla`); revisar quando houver lote real.

- **Esportiva (s254):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados, mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.39**), **Ctrl+Shift+R** em `esportiva.bet.br` (recarregar a extensão *não* re-injeta em aba já aberta), Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **As duas leituras críticas:** a **DATA** (tem de sair a do **evento** — 1 dos 13 diverge de dia) e a **odd**, que aqui é sempre a **pós-boost** (13 de 13 turbinados; a tela trunca a riscada). Sem amostra: **cashout executado** · múltipla de jogos diferentes · `void`/anulado · `half-won`/`half-lost` · bônus aplicado a bilhete · os 7 valores de `status` fora de {0,1,2} · qualquer esporte além de **futebol**. O `§9` tem 8 mercados confirmados, de **1 dia** de amostra — a lista vai crescer. **A conta tem mais histórico do que a fixture:** a página 2 já veio com `isLastPage:false`, então o lote real será bem maior que 13.

- **Superbet e BETesporte seguem SEM caso no harness** (anotado na s250, ao mexer no `content.js`). ✅ **VIVA (s263, encolhida)** — `extensor/harness/casos/` tem **15** arquivos e nenhuma das duas está lá; **a Pinnacle saiu da lista na s263** (`casos/pinnacle.mjs`, 14 bilhetes). As mudanças da s250 são aditivas (um `||` no ramo do `iniciarRobo` e uma entrada no mapa de autodiagnóstico) e não alcançam essas três — mas elas continuam dependendo de **teste ao vivo** a cada mexida no `content.js`.

- **`LavaPessoal`: 42 bilhetes em `Faz1bet` esperando a unificação da s199** (achado de passagem na s249, ao rodar o relatório do `unificar_casas.py`). A base dele foi importada na **s222**, depois da unificação, e trouxe de volta a grafia que a s199 tinha aposentado — `Faz1bet` → `Faz1Bet`. **Não aplicado de propósito:** é base de outro dono e mexe em `casa` de bilhete, então **recalcula 42 assinaturas** (a decisão da s234 vale: não tocar sem o dono pedir). Quando for: `python scripts/unificar_casas.py --somente Faz1bet` para o relatório, depois `--aplicar`. **A lição maior é do `MAPA`, não do LavaPessoal:** ele é cumulativo e **todo import futuro pode ressuscitar qualquer grafia já aposentada** — rodar o relatório sem filtro de tempos em tempos é o que revela isso.

- **Blindar o round-trip de casa no `/salvar` (proposto na s249, NÃO feito). ✅ VIVA (s261).** Quando a conta é resolvida por `parceiro_id`, `conta["casa"]` **já é** a grafia canônica daquela conta (`main.py:2472`) — e `:2478-2481` passa ela por `_casa_display(_display_to_key(...))` assim mesmo, o que só pode corromper; foi exatamente o que aconteceu com a Jonbet. (A linha `:2354` que esta pendência citava é de outro trecho hoje.) Gravar a casa **verbatim** nesse ramo fecha a classe inteira do defeito para toda casa que venha a ser registrada no `_CASA_DISPLAY` **depois** de já existirem contas. Mexe em caminho compartilhado por todas as casas → mudança própria, com harness e `pytest` antes. Hoje o mecanismo está de pé por sorte: **1 grafia quebrada em 57**, e só porque ninguém mais cadastrou conta antes do mapa.

**BetNacional — divergência de rótulo de data, NÃO medida (anotada de passagem na s248):** o
`formatTicketBNC` (`extensor/content.js:2439-2440`, com `t.colocada` — a linha `:2164` que
esta pendência citava mudou de lugar) emite só `Data (colocação):`, enquanto
`CASA_BETNACIONAL §4` diz que a coluna Data é a **do evento** — e que o campo do Histórico já é
"evento / liquidação". Pode ser só nome infeliz da variável (`t.colocada`), ou pode ser o mesmo
defeito que a VaideBet levou a produção na s210 e que a Jonbet quase repetiu (lá as duas datas
divergem em 7 de 10 bilhetes). **Custo de medir: baixo** — comparar `t.colocada` com
`pernas[].inicio` (o bloco já emite como `Início:`) num lote real da casa. Não mexer antes de
medir: se o campo já for o do evento, "corrigir" quebraria o que funciona.

**Badminton (s245) — medido, não aplicado (aguarda decisão do Feca):**
- ~~2 bilhetes em `Outro`~~ **CORRIGIDO na própria sessão** (ids 125105/125106 → `Badminton`) via `scripts/corrigir_esporte_bilhete.py` (novo), que **reusa `atualizar_bilhete`** em vez de rodar UPDATE cru — assim a trilha em `correcoes` é gravada (2 linhas, `esporte: Outro → Badminton`) e a assinatura é reavaliada (não muda: `esporte` ∉ `_SIG_COLS`). Base do Feca: **19 → 21** bilhetes de badminton, P/L do tipster **Bad Milton** 169,67 → **547,17** (+377,50 = os dois W que estavam fora do esporte). Varredura por nome de atleta + faixa de mercado não achou **nenhum outro** badminton escondido em `Tênis`/`Outro` na base do Feca; os 18 "candidatos" que o filtro pegou são todos legítimos de **times** (eBasket, Rugby, Basquete) — a fronteira que a regra nova já declara.
- **Superbet não emite esporte/liga no texto do bilhete. ✅ VIVA (s261).** `formatTicket` (`extensor/content.js:1034` — a linha `:911` que esta pendência citava é de outra função hoje) manda data, stake, odd, status e seleções, e **nenhum `Esporte (casa)`**; o grep dessa string no `content.js` só acha `:1292`, `:1457` e `:3148`, todos de outras casas. Fecharia o buraco de **todos** os esportes dessa casa, não só badminton — mas exige ler os nomes dos campos no JSON de `/user/{id}/tickets` (F12 → Network). Não há fixture de Superbet no harness.
- **Categoria (não esporte):** 5 bilhetes Betano de 10–11/06 com `Over 78.5 Pontos [dupla v dupla]` estão em `Player Props` — é total da **partida**, então `Pontos` (`MASTER_APOSTAS §6`); e 9 bilhetes em `Games` onde o mesmo §6 manda `Sets`.

**Achados de performance da s217 — medidos, não corrigidos (decisão do Feca, um por vez):**
- **`sims=10000` fixo mesmo com a base cheia. ✅ VIVA (s261)** — as 3 chamadas seguem lá: `charts/overview.js:320`, `charts/gestao.js:488`, `charts/performance.js:1081`. As chamadas passam `10000` explícito, o que **atropela** a escala adaptativa que o `_calcPValueMCraw` tem por dentro (`n>10000 → 3000`). Com 30.851 linhas são ~308 milhões de iterações por cálculo, duas vezes. Fora da thread principal a tela não trava mais, mas o valor ainda leva **~1 minuto** para chegar (conferido no demo com 24.000: os cards ficaram girando bem depois do render). Cair para ~2.000 sims em base grande resolveria — **muda número exibido** (p95/p99 e p-value), então exige antes/depois medido na mesa e aval do Feca.
- **`/uso/tokens` responde 500** em produção (visto ao cronometrar as rotas do feed). **NÃO-MEDIDA, mas a s261 achou uma causa candidata na leitura do código:** `uso_resumo` (`repository.py:2571` e `:2573`) monta `NOW() - $1::interval` e passa a **string** `"30 days"`. Com o cast explícito o Postgres resolve `$1` como tipo `interval`, e aí o asyncpg exige um `timedelta` — string levanta `DataError`. Isso explicaria um 500 **constante**, não intermitente. **O contraste está no mesmo arquivo:** a purga da lixeira (`:2367`, escrita depois) usa `NOW() - ($1 || ' days')::interval`, e a concatenação mantém `$1` como texto — é a forma segura, e a rota de tokens ficou na antiga. **Nenhum teste cobre `uso_resumo`**, o que é o motivo de ninguém ter percebido. **Provar antes de mexer:** basta um `SELECT NOW() - $1::interval` com `"30 days"` contra qualquer Postgres — se levantar `DataError`, é isto; se passar, a causa é outra e o palpite morre aqui.
- **A casca `/app` carrega 3 iframes e os 3 puxam `/dashboard/data`. ✅ VIVA (s261)** — as 3 chamadas conferidas: `inicio.html:483`, `index.html:3504` e `dash/assets/js/data.js:4`. `/inicio`, `/` (Extração) e `/dashboard/`, cada um montando o feed inteiro no servidor (3 × 11,6 MB por abertura). Um cache compartilhado entre os frames (ou o feed servido uma vez pela casca) cortaria 2/3 do trabalho.
- **Deep-link a frio monta a tela vazia. ✅ VIVA (s261).** Abrir `/app#dash/metrics` sem cache local: a casca chama `showPage('metrics')` antes de o `buildHTML` existir, `_lastPage`/`_lastPageSig` já ficam marcados (`app.js:459`), e o **caminho frio** do `loadData` (`app.js:1233-1250`) chama `buildHTML()` + `applyAparencia()` e **nunca** `renderPage` — o `showPage` seguinte volta cedo pelo `if(id===_lastPage&&sig===_lastPageSig)return` (`:458`). A tela fica com os `—` do markup. **O caminho quente já faz certo** (`:1225`, `if(_lastPage)renderPage(_lastPage)`), o que dá o formato do conserto: espelhar essa linha no ramo frio. **Pré-existente**, não veio da s217.

**Próximo passo (backlog vivo, um por vez):**
- **Backfill eSoccer — Feca FEITO (s234); resta o residual dos outros donos, se eles quiserem.** A auditoria da s234 varreu a Bet365 inteira e viu, fora do Feca: **Gabriel** ~14 bilhetes eSoccer como `Futebol` (tipsters próprios `Esoccer`/`LBB`) + **1 linha com grafia `Esoccer` na coluna esporte** (única da base; padroniza para `eSoccer` se mexer); Jonathan/William/LavaPessoal só têm eBasket-like (fora do escopo eSoccer). Método pronto e testado: script da s234 (`Backups/esoccer-backfill-feca-2026-08-02/`) — UPDATE por id auditado + perfil do tipster ganhando `eSoccer` nos `esportes` (senão o filtro duro do matcher mata as sugestões em silêncio, lição s221). `esporte`/`tipster` fora de `_SIG_COLS` → dedup intacta. Decisão do Feca (s234): **não tocar na base de outros donos sem eles pedirem**.
- **Matcher: "feudo empírico" — medido na s221, NÃO implementado.** O `Sugerir tipsters` é 100 % **declarativo**: lê só os perfis (casas · esportes · mercados · dica de stake) e **nunca** o histórico. Por isso as stakes **quebradas** (109,38 · 112,18 · 184,21…) ficam eternamente vazias — nenhum perfil declara quebrada na Bet365, e por stake elas são de todo mundo (M&M 284 · SóChutes 121 · SóTudo 31 · LBB 30). **O sinal que falta está na própria base:** no trio **casa · esporte · categoria**, um tipster domina. Medido na janela de 2.207 bilhetes que a tela **já carrega** (dá para computar no front, sem endpoint novo): `Bet365·Futebol·Gols → LBB 98 %` (226) · `Bet365·Futebol·Escanteios → SóTudo 82 %` (257) · `Bet365·eBasket·Pontos → Ctrl Alt Green 100 %` (219) · `Bet365·Tênis·ML → Robotenis 99 %` (168) · `Superbet·Múltiplos·Múltipla → Arrudex 92 %` (169) · `BETesporte·Futebol·Múltipla → Peixe 100 %`. Regra proposta: tipster **ativo** com ≥ 90 % e ≥ 15 bilhetes no trio leva; senão cai no matcher declarativo de hoje. **Cuidado que o próprio caso do 199 ensina:** o dono de um trio **muda com o tempo** (SóTudo → LBB entre maio e julho), então a janela precisa ser **recente**, não a base inteira — na base inteira `Bet365·Futebol·Gols` cai para 52 % de LBB e o critério não dispara. Fazer só depois de backtest com **holdout temporal** (treina no passado, mede no futuro), nunca in-sample.
- **Excluir conta: o caminho nunca rodou contra Postgres de verdade** (s219). ✅ **VIVA (s261)** — `tests/test_repository_db.py` tem 17 testes DB-real e **nenhum** toca `excluir_parceiro`. Os 7 casos de `test_excluir_parceiro.py` usam conn simulado, como o resto da suíte. Três coisas ficaram sem prova real: o `DELETE ... RETURNING to_jsonb(b.*)`, o cast `::jsonb` do snapshot no INSERT da lixeira, e o corpo do `DELETE` via HTTP. **Teste barato, fazer antes de excluir qualquer conta com histórico:** criar conta descartável, capturar 1 ou 2 bilhetes, excluir pelo modal, e rodar `python scripts/restaurar_conta_lixeira.py` para ver se a linha aparece com a contagem certa. Depois `--aplicar` num id e conferir se as apostas voltam. A forma travada seria um caso em `tests/test_repository_db.py` (roda no CI com `TEST_DATABASE_URL`, nunca em prod).
- **Betfast: rodar a captura pela EXTENSÃO** (s211). A API já foi validada ao vivo (varredura do teto: 32 de 32, ver acima), mas o robô em si nunca rodou: recarregar a extensão, **Ctrl+Shift+R** na aba, capturar e conferir contagem/datas/odds/código no dashboard. **O gatilho do teto continua sem exercício ao vivo** — a conta que loga no navegador tem 32 bilhetes e não chega nas 50; para ver o toast *"a captura foi além do teto"* seria preciso rodar na conta `fecanario`.
- ~~**Pinnacle sem fixture no harness** (s201)~~ **FEITO na s263** — `fixtures/pinnacle.settled.json` (6 bilhetes reais, inclusive uma múltipla de 2 pernas e a anulada) + `fixtures/pinnacle.open.json` + `casos/pinnacle.mjs` travam a ordem do replay, o freio por lista, o de-para posicional e o `CANCELLED → V`. **O que a fixture ainda NÃO cobre está escrito no cabeçalho do caso:** as duas ABERTAS são **derivadas** de linhas reais (a conta usada não tinha nenhuma em aberto no dia — a própria Pinnacle respondeu lista vazia nas três variantes de corpo testadas), `PUSHED`/`VOID`/`REFUND` seguem sem amostra, HW/HL também, e o campo 45 (categoria) é null nas 8 linhas. **A divergência "exibida × Retorno ÷ Stake" continua sem medição:** o payload traz P/L, não retorno, e o caso confere a odd exibida contra o JSON — não resolve a pergunta do §11.
- ~~**bet365 sem caso no harness** (s202)~~ **FEITO na s244** — `casos/bet365.mjs` trava a guarda `b3Emissivel`, o merge summary+confirmation, o corte do bloco KYC, a odd fracionária e o buraco da data. Harness passou de 7 para 8 casos (154 bilhetes).
- **Bet365 — data em bet builder de MESMO JOGO: DECISÃO DO FECA, medido e não corrigido** (s244). O `confirmation` desse tipo de bilhete vem com `TP=00010101000000` (sem kickoff) → `_dataFimB3` devolve vazio → o bloco sai **sem linha de data mesmo com o detalhe OK** → o backend cai na data de referência (= hoje). Provado por execução contra a fixture real, não deduzido. **O dado existe e está sem uso:** `da` (do confirmation, `DA=20260722233620`) e `tp` (do summary), ambos data de **colocação**. Usá-los contraria `CASA_BET365 §4`, que decide *"colocação nunca"* (cadeia `evento → informada → Brasília-hoje`) — logo é **mudança de regra**, não conserto de bug, e precisa da sua aprovação + atualização do §4 na mesma sessão. **CONFIRMADO na base, no fim da própria s244** (a 1ª medição tinha dado inconclusiva: 41,5% dos multi-seleção contra 24,1% dos simples, com captura diária confundindo o sinal — aquele número foi **descartado**, não use). O marcador `' // '` era grosseiro: mistura múltipla **entre jogos**, que tem kickoff, com bet builder de **mesmo jogo**, que não tem. Marcador exato: **2+ trechos e todos os confrontos `[A v B]` IGUAIS**. Com **controle dentro do mesmo lote** de captura (elimina o confundidor), `data == dia da captura`: **mesmo jogo 14/27 = 51,9%** · entre jogos 16/71 = 22,5% · simples 58/420 = 13,8%. O caso sem explicação inocente: no lote de 04/08 18:53:31, **0 de 20** simples eram do dia da captura e **2 de 2** bet builders de mesmo jogo eram. **Escala: pequena** — 34 bilhetes dessa classe na Bet365 do Feca desde 01/07, ~18 com data suspeita; hoje foram **6** (Internacional×Corinthians, Palmeiras×Fortaleza, Athletico-PR×Vitória, Juventude×Atlético-MG, Sonego×Griekspoor, Yu Chen Han×A Yeon Yoo). Dos 218 bilhetes Bet365 que entraram hoje, 84 têm data de hoje e **só esses 6** são da classe defeituosa; os outros 78 derivam do kickoff real. **O Feca viu o sintoma e o reportou** ("apostas de dias anteriores aparecendo como de hoje"), foi medido, ele leu o resultado e **decidiu não corrigir agora**. **Enquadramento para a decisão, quando ela vier:** a regra atual não escolhe entre colocação e data do evento — escolhe entre **colocação** (data do bilhete, erra por horas) e **o dia em que a captura rodou** (data da máquina, erra por semanas no modo Período). Proposta: cadeia `kickoff das pernas → colocação → data informada`, aplicando colocação **só** quando a API não dá kickoff, com o `CASA_BET365 §4` atualizado na mesma mudança. `casos/bet365.mjs` trava o estado atual **de propósito**: mexer nisso falha o gate e obriga a decisão consciente.
- ~~**Limpeza dos 139 da `marloncezar01`**~~ **APLICADA pelo Feca na s244** (o classificador barra escrita destrutiva em prod, então ele rodou via `!`). Verificado por fora, não pela saída do script: snapshot `removidos-Feca-20260804T194239Z.json` com **139 linhas de 22 colunas**, todas sem código e todas do parceiro certo, somando **exatos R$ 3.721,45** — o mesmo valor medido antes do DELETE. Base: **4447 → 4308** · sem-código **3586 → 3447** · `data = hoje` **168 → 29** (os 29 legítimos, que têm código) · lote do dia **206 → 67**, com código, data correta e confronto na descrição. Todos os deltas = 139.
- **Jonathan: 10 bilhetes Bet365 sem código em 04/08 — SUSPEITO, não confirmado** (s244). Mesma casa e mesmo dia do defeito do Feca, conta `edy-luc@hotmail.com [Gustavo]`, 10 de 10 sem código. **Não dá para separar robô de print pelo dado**: a coluna `origem` é `extracao` nos dois caminhos. Se for o mesmo defeito, o mesmo script limpa (trocando `--dono`/`--parceiro`); antes disso, perguntar ao Jonathan se ele capturou por print. **Não mexer na base de outro dono sem ele pedir** (mesma decisão da s234).
- ~~**`renomear_parceiro` não recalcula a assinatura** (s198)~~ **VENCIDA — feito em `50e68ee` (26/07)**, achado na varredura da s261. A função recalcula via `_assinatura_pos_edicao` com escalada de `_counter`, dentro da mesma transação (`repository.py:2439-2448`), e tem 4 testes em `tests/test_renomear_parceiro_assinatura.py`. O `CLAUDE.md` já a listava sob *"Quem já faz certo"* — **o §5 é que ficou para trás por duas semanas**, e eu quase gastei uma sessão "consertando" o que estava pronto.
- **41 apostas com odd truncada em reticências** (`2.50001664442...`): 22 Bet365, 6 Novibet, 6 Bolsa, 4 Betfair, 3 Esportiva Bet. A instrução proíbe reticências e uma odd assim não converte para número — mexe em P/L, não é cosmético. **NÃO-MEDIDA desde então (s261): a contagem é a do dia em que foi escrita e só o banco diz se ainda são 41** — `SELECT casa, count(*) FROM bilhetes WHERE odd LIKE '%...%' GROUP BY casa`.
- **165 bilhetes sem odd no sistema — MEDIDO na s262, não é defeito, não corrigir às cegas.** 149 são `origem='import'` (a planilha de origem trazia `0,00` na coluna Odd das perdidas; o import copia verbatim) e a esmagadora maioria é `L`, onde a odd não entra no P/L. Por dono: Feca 144 · LavaPessoal 8 · Lava 6 · ViniciusOliveira 4 · Jonathan 3. **A única classe que machuca é `W`/`HW`,** onde P/L vira não-calculável, e são **2**: `#18205` (Feca, KTO, 16/04, stake 331,57) e uma do LavaPessoal — as duas já em `extraction_state='aberta'` desde o backfill da s259. Backfill da odd das antigas **não é viável**: a Bet365 não mostra mais bilhete de abril/maio. Se for mexer, mexer só nas 2 de `W`.
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Solto (cosmético): favicon da KTO aponta para `kto.com`; o domínio real é `kto.bet.br`. ✅ VIVA (s261) — e são QUATRO arquivos, cinco ocorrências, não os "3 mapas" que esta linha dizia:** `extensor/popup.js:16` · `app/static/index.html:2432` · `app/static/dash/assets/js/data.js:52` **e** `:107` (o mesmo arquivo grafa duas vezes, uma na URL do serviço de favicon e outra no mapa de domínio) · `app/static/inicio.html:297`. É a mesma armadilha da memória *"Favicons: 3 mapas"* — o contador estava desatualizado, então **corrigir por `grep` de `kto.com`, nunca pela lista**.
- **Tela "Em Aberto" fora do material de venda** (s215): `scripts/demo/capturar.mjs` não captura a tela nova — o servidor de demonstração já a serve, falta só decidir se ela entra no showcase (e a numeração dos arquivos existentes muda). **Decisão do Feca: entra, mas só depois de a tela estar finalizada.**
- **Material de venda: 4 correções abertas nas capturas** (s214). O pipeline funciona (`scripts/demo/`: perfil → base fictícia → servidor → `capturar.mjs`) e as 8 telas saíram, mas quatro coisas travam o uso na landing. **(1) Contas irreais: o mock devolve 1.830 contas, o real são 102** — `servidor_demo.py:_parceiros()` deriva conta de cada par (parceiro, casa) visto no feed, então cada pessoa nasce com ~18 contas. **E a tela repete essas 1.830 embaixo de cada uma das 29 casas, somando 53.070** — essa segunda multiplicação foi medida, não diagnosticada; conferir se é forma do payload antes de mexer no front. **(2) `Diagnóstico de Risco` sai em "calculando…"**: é Monte Carlo de 10.000 simulações sobre 24 mil apostas e o screenshot dispara antes de terminar — esperar o cálculo, não o relógio. É o painel que sustenta o argumento estatístico da página. **(3) Custo de contas e de tipsters em R$ 0**, então o "P/L Líquido" fica idêntico ao bruto e a tela perde justamente o recurso que diferencia — popular `/custos/store` no mock. **(4) `Nível de Solidez: Baixa`**, com MDD 90,88% e Recovery Factor 0,94×. É coerente com odd média 7,7, mas é a nossa própria régua reprovando a operação da demonstração. Subir o edge de 4,5% para ~8% leva o ROI a ~4% e a folga para faixa saudável, sem sair do plausível.
- **Landing do usuário final: reescrita aprovada, não feita** (s214). O Feca pediu duas frentes: **tirar detalhe de arquitetura** e **entrar com print real**. Sai da página a seção "Integramos o motor" (Kambi/BetConstruct/Altenar), a aba "API do motor" do hero (`Koef`, `WinAmount`), os pesos e cortes da Solidez, "27 categorias fechadas", os "94,5% de acerto de categoria" e a faixa de números do hero. Fica o que é confiança e não mecanismo: não pedimos senha, a extensão não aposta nem move saldo, e o bloco "o que o Sharpen não é". **A ordem importa: print primeiro, texto depois** — hoje a página se defende explicando o mecanismo porque não mostra nada. Fonte em `docs/marketing/landing-usuario-final.html`.
- **Em Aberto: relato do Gabriel SEM confirmação** (s215, aberto): funciona para o Feca (57 abertas, R$ 13.325, conferido na sessão logada em `www.sharpen.bet`), mas o Gabriel disse que não. **Hipótese principal: casca velha ainda gravada no navegador dele** — o `no-cache` só vale a partir da próxima ida ao servidor, não desfaz cache já gravado; `Ctrl+Shift+R` uma vez resolve (F5 normal pode não recarregar o iframe do dashboard). **Antes de mexer na tela, distinguir pelo que ele vê:** cards com título e corpo vazio, sem nenhum KPI = ainda é cache; os 4 KPIs em `R$ 0` / "nada em aberto" = não é bug, a base dele não tem aposta aberta (conferir de quem é a base pelo filtro "Operador"). O jeito de medir é ler quais scripts o navegador dele carregou (`[...frame.contentDocument.scripts].map(s=>s.src)`) — versão antiga ou tag ausente = cache.
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

### Bloqueado por ação humana (não é bilhete)

- ~~Login `ZoraEsports` 401~~ **RESOLVIDO na própria s238** — mas a lição fica: **conta nova deployada ANTES da env var de senha nasce com hash vazio na tabela `usuarios`, e o seed (`ON CONFLICT DO NOTHING`) nunca conserta** — colar a env var depois não basta (desde o Deploy B da s233 quem autentica é a TABELA via cache; a docstring do seed ainda descreve a Fase 1). Medido: `length(senha_hash)=0` na linha. Fix: UPDATE manual do hash (o Feca rodou o script via `!`; o classificador do Claude Code barra mexida direta em credencial de produção) → login 200 na primeira tentativa. **Ordem certa daqui em diante: env var no Railway PRIMEIRO, push da conta depois.**
- **Env vars de senha no Railway (s216, s218, s220) — estado NÃO instrumentado.** `SENHA_LAVAPESSOAL_HASH` **está no ar e o Lava entra** (confirmado pelo Feca em 31/07, s222). `SENHA_WILLIAMOLIVEIRA_HASH` e `SENHA_VINICIUSOLIVEIRA_HASH`: **não confirmadas** — podem já ter sido coladas; ninguém atualiza esta linha quando a ação acontece fora do repo.
- **Login por Telegram: o botão saiu da tela, a causa raiz continua aberta (s324). HUMANA + NÃO-MEDIDA.** O relato foi de uso: aperta e nada acontece. O `Entrar com Telegram` foi retirado do `/login`; o backend segue inteiro (`/auth/telegram/*`, `/auth/metodos`, `tests/test_login_social.py`). **Ninguém mediu por que o clique morre.** Suspeito principal: o `/setdomain` do BotFather nunca apontou para `www.sharpen.bet`, e o `oauth.telegram.org` recusa domínio não registrado sem sair do lugar. **Como medir, sem tocar em código:** abrir `/auth/telegram/ir` com o console aberto e ler o que o `oauth.telegram.org` responde. Se for isso, o conserto é no BotFather, fora do repo. Para devolver o botão: repor o `<a id="btn-telegram">` no `login.html`, voltar `temSocial` a olhar `m.telegram` e apagar `test_botao_telegram_esta_fora_da_tela` (o próprio teste diz isso).
  > ⚠️ **Esta linha é uma pendência declarada, não uma medição.** Não afirme a partir dela que um login está quebrado — foi exatamente o erro cometido na s222. Para saber de verdade: `POST /login` devolvendo **200** = hash certo; **401** = ausente ou diferente (429 é rate-limit, 500 é erro do app). Sem esse teste ou a palavra do Feca, escreva "não confirmado".

  Procedimento, se algum dia faltar mesmo: os hashes **não entram no git** — se perdidos, gerar de novo com bcrypt e colar na caixa de Variables do Railway (literal, 60 caracteres, sem espaço nas pontas; o `$` do `$2b$12$…` chega mutilado por qualquer shell que interpole variável).
- **`LavaPessoal`: 30 apostas com stake 0** (s222) — importadas, mas **invisíveis no dashboard** (`dashboard_rows` corta `stake <= 0`). 23 delas têm resultado. Aparecem na grade da **Extração** (`list_bilhetes` não filtra), então a correção é humana: preencher a stake lá e elas entram no P/L. Todas do tipster `Peixe`, abr–jul.
- **`LavaPessoal`: duas contas pré-existentes vazias** (s222) — `Bet365 | monster@2025 [Richard]` e `Betano | karlmarxrosa@aurainteligente.com [221193Cy*]`, criadas em 30/07, arquivadas, **zero** bilhetes. Não vieram do import e não foram tocadas. Se forem lixo de teste, apagar pelo botão Excluir do Painel de Contas (s219).

Quando chegar um bilhete novo: abrir o arquivo da casa correspondente, preencher a pendência, rodar o checklist do `CLAUDE.md` se envolver categoria nova.

### O que a varredura da s261 NÃO conseguiu classificar

**Cinco pendências são de DADO, não de código — nenhuma delas é verificável por leitura**, e todas trazem número datado que só o Postgres confirma:

| Pendência | Query que decide |
|---|---|
| 41 odds com reticências | `SELECT casa, count(*) FROM bilhetes WHERE odd LIKE '%...%' GROUP BY casa` |
| `LavaPessoal`: 42 em `Faz1bet` | `SELECT count(*) FROM bilhetes WHERE dono='LavaPessoal' AND casa='Faz1bet'` |
| `LavaPessoal`: 30 com stake 0 | `SELECT count(*) FROM bilhetes WHERE dono='LavaPessoal' AND stake IN ('','0','0,00')` |
| `LavaPessoal`: 2 contas vazias | `SELECT p.nome FROM parceiros p LEFT JOIN bilhetes b ON …` |
| Residual do backfill eSoccer | contagem por dono, fora do Feca |

O `DATABASE_URL` de produção está no `.env` local. **Medir é só SELECT e não muda nada** — mas é base de outros donos, então segue a decisão da s234: **ler pode, tocar só se o dono pedir.**

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
