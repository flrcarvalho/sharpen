# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-07 (sessao 331 — **handoff v2 aplicado: `Contas e Parceiros v2`, 6 fases num commit so.** A tela deixa de ser tres colunas concorrendo e passa a ter QUATRO leituras: dinheiro no topo estreito · `Ultimas acoes` na lateral inteira comecando na MESMA linha dos KPIs · `Concentracao de caixa` ao lado da tabela de Contas. **O rail da casca saiu desta tela** — ele e o RAIO-X, que pertence a Extracao. **Concentracao substitui `Contas por casa`, que contava CONTAS:** contar conta nao diz risco nenhum, e 52 contas numa casa com R$ 0 desenhavam uma barra maior que 1 conta com metade da banca. Agora e rosca por `stroke-dasharray` sobre perimetro 100 (cada arco e literalmente "P por cento"), rampa FIXA de 8 tons — tom calculado do valor faria a MESMA casa mudar de cor entre duas aberturas, e a cor e a chave que liga rosca e lista. Clicar filtra a tabela; clicar de novo solta. **Pilulas de status** num helper unico, lista fechada, numero em `<b>`, com o estado NOVO `Aguardando tipster N` em AZUL: bilhete sem tipster e espera externa, nao erro, e antes ele somava com as apostas abertas num numero so — apagando a diferenca entre "eu resolvo" e "depende de alguem". **Tabela:** 4 trilhas, chip `TOTAL` na trilha da Caixa, `.acct-group` fechando o bloco, SEM traco/arvore, e os tres botoes de volta na linha. Sairam as colunas Duracao/Dias ativos/Apostas (descreviam ATIVIDADE; a tela responde "quanto tem e esta conciliado?"). **Duas armadilhas de largura, as duas invisiveis na leitura e medidas no headless:** (1) media query DENTRO do iframe le a largura do IFRAME, e a sidebar (~300px) fica fora dele — num monitor de 1440 a pagina tem 1120, e o breakpoint de 1180 do handoff disparava sempre, jogando o log para baixo em TODA largura; (2) com as trilhas em px cravado sobravam 130px para o nome em 1440 e "Esportes da Sorte" saia cortado — as tres viraram `minmax(min, alvo)` e cedem antes do NOME ceder. Conferido em 1366/1440/1600/1920/2560. **Gates:** check-tokens verde, 756 passed / 30 skipped, Escada em 3 criterios sem achado novo, fumaca no navegador (zero tag na casa, 29 chips TOTAL, sem arvore, filtro ligando e soltando) e a rosca provada com 12 casas sinteticas: 9 arcos somando exatamente 100.)

_Anterior: 2026-09-07 (sessao 330 — **handoff de design aplicado: `FDC - Contas e Parceiros Opcao A`, 5 fases, 5 commits, todos pushados.** A tela tratava tudo com o mesmo peso: 4 KPIs (um deles sempre `0`), 3 colunas concorrentes, `Editar/Arquivar/Excluir` acesos nas ~100 linhas com um vermelho em cada uma, 29 casas em barras de escala inutil e um log de 40 acoes onde 37 diziam `100%`. **Fase 1** — titulo sai do gradiente azul (o maior texto da tela era acento, e com isso o azul deixava de significar sinal); eyebrow sobe um degrau na Escada de Tinta (9px/--ink-mute media 3,0:1, abaixo do 4,5:1 do papel Label). Aplicado tambem no Dashboard, com `SHELL_SPEC.md` e `check-tokens.mjs` atualizados junto. **Fase 2** — 4 KPIs viram 3, ordenados por CERTEZA DO DINHEIRO: disponivel (garantido) → em aberto (projecao, ambar) → banca total (soma, neutro). Sai o medidor ATIVAS/INATIVAS e o `Caixa total`, que imprimia o MESMO `totais.banca` do KPI ao lado. **Fase 3** — linha da casa e da conta na MESMA grade de 4 trilhas, com a coluna de acoes reservada mesmo vazia; acoes so no hover; `Excluir` sai da linha e vira o ultimo item do menu `⋯`. **Fase 4** — coluna Conciliacao com vocabulario FECHADO num helper so (`tagConciliacao`), sem abreviacao e sem teto no numero; vermelho so em `Divergencia` (erro realizado), ambar em pendencia (fato a conferir). **Fase 5** — `Contas por casa` colapsa a cauda e o rail vira fila de `Pendencias`. **As duas foram DESFEITAS na revisao** (abaixo). **A REVISAO, depois de o Feca ver a tela na base real (177 contas, 47 casas):** o rail voltou a ser `Ultimas acoes` — aquele painel e o historico de EXTRACOES (o RAIO-X), e rotular registro de fila promete tarefa que nao existe; rotulo errado e pior que rotulo repetido. A casa virou SOMA (fundo proprio + a palavra `total` + guia recuando as contas), porque o total da casa e o saldo das contas caiam na mesma coluna e liam como cinco parcelas a somar. E os TRES cards de baixo sairam: duracao, dias ativos e apostas viraram COLUNAS da lista, que passou a ter 7 trilhas com cabecalho. **O vao no monitor largo nao era da largura da lista — era de ela ter UMA coluna flexivel**; com todas em `minmax(min, Nfr)` a sobra se distribui entre todas. **Bug antigo achado medindo:** a barra de `Contas por casa` tinha `fill` de 0px em TODA linha (`%` sobre elemento inline nao se aplica), entao 43 contas e 2 contas desenhavam a mesma barra — era isso que fazia o card nao dizer nada. **Desvio do handoff que ficou:** a tag `Sem caixa` NAO vira tinta — a Caixa esta ligada em 4 de 102 contas e ela pintaria 98 linhas com o mesmo rotulo, que e o defeito que o handoff existe para matar. Tag em 10px e nao 9,5px porque dois rotulos sao --ink-mute e a Escada proibe --ink-mute abaixo de 10px. **Gates:** check-tokens verde, 3 blocos inline compilados por `vm.Script`, **756 passed / 30 skipped**, e render headless contra o `servidor_demo` a cada fase. Varredura da Escada em 3 criterios: os 3 achados sao excecoes ja documentadas (caret/seta e `opacity` como estado), nenhum e codigo novo.)

_Anterior: 2026-09-07 (sessao 329 — **a faxina de documentacao achou 14 regras que governavam o comportamento e nao estavam escritas.** Esse e o resultado, nao os KB. Quatro arquivos disputavam o papel de "onde o projeto esta" e tres descreviam o projeto de julho; a varredura da s261 ja tinha medido o custo disso ("a primeira pendencia que eu fui atacar ja estava feita desde 26/07"). Cinco lotes fechados. **F** — nasce o `BACKLOG.md` (70 KB), que absorve o §5 do STATUS VERBATIM: as 192 linhas nao-vazias conferidas uma a uma, zero perdida, com contraprova por canario. **B** — STATUS de 183 para 44 KB; as 1.157 linhas de antes reprocuradas uma a uma (483 ficaram, 491 foram para o HISTORICO, 183 para o BACKLOG, ZERO perdidas). **C** — HISTORICO de 1,21 MB vira indice de 3 KB + 6 particoes, com as 1.445 linhas conferidas. **D** — 16 docs + 11 anexos para `docs/arquivo/`, `docs/` cai de 43 para 27 vivos, 20 links consertados. **E** — CLAUDE.md de 68,3 para 62,7 KB e nasce o `docs/CASOS.md` (22,9 KB), que NAO e auto-carregado: a regra fica no CLAUDE, o bilhete/casa/valor/sessao vai para o CASOS. **O gate final de regras deu ZERO perdidas**: das 434 ancoras verificaveis, 384 seguem no CLAUDE e 57 migraram para o CASOS; dos 50 numeros que decidem comportamento, 36 ficaram e 11 migraram. 255 regras contadas item a item em 12 secoes. **E 14 regras foram ACRESCENTADAS** — o `git add` por nome, os tres 'os tetos travam crescimento', o trio de causas da Escada de Tinta, a inversao de hierarquia, o 'node --check e falso verde para tudo em template literal', e mais 7. Elas ja governavam o comportamento; so nao estavam escritas como regra. **Gate novo:** `tools/check_docs.py`, no CI, com 7 checagens todas provadas por mutacao — tetos de CLAUDE (65 KB), CASOS (60) e STATUS (50), forma do STATUS (<=3 blocos, <=2 _Anterior), copia em Backups por PREFIXO, link quebrado e ANCORA. Regra sem gate nao e cumprida neste repo: o invariante #4 estava escrito e claro, e Backups chegou a 551 pastas com 165 copias de STATUS/HISTORICO. **Reconciliacao da Auditoria Turbo:** os 78 achados MEDIO/BAIXO do mergulho de 20/07 NAO EXISTEM por escrito (o doc enumera 16 e o rodape diz "Deliverables uncommitted"); reconciliei os 139 do findings.json de 19/07 — 40 fechados, 68 abertos, 20 a confirmar na tela, 3 parciais e 3 que nao eram achado, um deles um placeholder de teste. **#129 medido e rebaixado:** a odd nao entra no calcular_pl em L/V e o risco de dedup deu ZERO de extracao em 528 multiplas sem codigo expostas; virou divida de documentacao. **Lote A ABERTO** — podar Backups (223 arquivos, 28,7 MB), com o zip para fora do repo ANTES de qualquer coisa apagada.)

> **Histórico completo das sessões 325 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 331)

### O handoff `Contas e Parceiros v2` está aplicado, nas 6 fases

A tela deixa de ser três colunas concorrendo e passa a ter **quatro leituras**: os três
números de dinheiro no topo estreito · `Últimas ações` na lateral inteira, começando na
mesma linha dos KPIs · `Concentração de caixa` ao lado da tabela de `Contas`.

**O rail da casca saiu desta tela.** Ele é o RAIO-X, que pertence à Extração — e
escondê-lo sem colapsar a trilha abriria 372px vazios (`.workfull.sem-rail`).

### Concentração de caixa: contar conta não diz risco

O painel que saiu (`Contas por casa`) contava **contas**. Isso desenhava uma barra maior
para 52 contas numa casa com R$ 0 do que para 1 conta com metade da banca — o oposto do
que importa. A pergunta certa é onde o **dinheiro** está.

A rosca usa `stroke-dasharray` sobre um círculo de perímetro 100, então cada arco é
literalmente "P por cento", sem conversão. A rampa de 8 tons é **fixa**: tom calculado a
partir do valor faria a mesma casa mudar de cor entre duas aberturas, e a cor é a chave
que liga a rosca à lista. Clicar numa casa filtra a tabela; clicar de novo solta —
filtro que só liga vira armadilha.

### Duas armadilhas de largura, as duas invisíveis na leitura

Nenhuma das duas dá erro, e as duas só apareceram medindo no headless.

1. **Media query dentro do iframe lê a largura do IFRAME, não da janela.** Esta página
   vive no `#fr-plan` da casca, e a sidebar (~300px) fica **fora** dele: num monitor de
   1440px a página tem ~1120. O breakpoint de 1180px do handoff disparava **sempre**, e o
   log caía para baixo em toda largura — parecendo que a coluna lateral não tinha sido
   implementada.
2. **Trilha em px cravado não cede — o nome cede.** Com `148/118/172` fixos sobravam
   130px para o nome em 1440, e `Esportes da Sorte` saía cortado. As três viraram
   `minmax(min, alvo)` e cedem **antes** do nome: nome é identidade, as outras são
   rótulo, valor e botão. A concentração também cede (`minmax(0,228px)`) e a tabela é
   quem declara piso (666px). Conferido em 1366/1440/1600/1920/2560.

> Sintoma para reconhecer o primeiro noutro lugar: um breakpoint que "não funciona" numa
> tela dentro de iframe. Meça `document.documentElement.clientWidth` **dentro** do frame
> antes de mexer no número — a janela mente sobre a largura que o CSS vê.

### `Aguardando tipster` virou estado próprio

Bilhete sem tipster somava com aposta aberta num número só. São coisas diferentes:
pendência eu resolvo olhando; tipster **depende de terceiro**. Agora é uma pílula azul —
espera externa não é erro, e âmbar diria "confira" onde não há o que conferir.

### Os seis ajustes depois de ver a v2 na base real

Concentração **+25%** (228 → 285) com a rosca proporcional (88 → 110) · `Últimas ações`
**+25%** (240 → 300) · favicon do log dessaturado, no padrão do `.ctx-hchip` · saíram o
chip `nada a conferir` e o botão `Fornecedores` · `+ Nova conta` desceu para o cabeçalho
de Contas · ícone nos três botões da linha.

**Ícone é SVG em `currentColor`, não emoji.** Emoji é glifo colorido do sistema: não
aceita tom e destoaria da paleta — o mesmo motivo de os favicons das casas irem
dessaturados. Em `currentColor` eles herdam `--ink-soft` do botão, viram `--ink` no
hover, e o de Excluir herda o vermelho apagado da classe.

### O defeito que o ícone revelou: transbordo para a ESQUERDA não aparece no `scrollWidth`

Com os ícones os três botões passaram a medir 208px, e a trilha de ações dava 158. A
linha **não** estourava: `justify-content: flex-end` empurra o excesso para a
**esquerda**, e transbordo à esquerda não entra no `scrollWidth`. O resultado era o botão
passando por cima da coluna Caixa, sem erro nenhum e sem o gate de largura acusar.

> Sintoma para reconhecer isto noutra grade: uma medição de transbordo que dá zero numa
> linha que visivelmente se sobrepõe. `scrollWidth` só enxerga o excesso do lado do fluxo
> — com `flex-end` (ou `direction: rtl`) ele é cego. Compare a **borda** do item com a do
> contêiner, e não a largura com o `scrollWidth`.

### O SharpenCal chegou à grade de Extração (e viajou dentro do commit da s331b)

Duplo-clique na coluna `Data` da grade de Extração abre o calendário da marca, que era o
único campo de data do sistema ainda sem ele (`UI_REFERENCE §4`). É a mesma chamada de
`_apInlineStart` (`charts/apostas.js:848`), que já servia a `Base Completa` e `Em Aberto`:
digitar continua valendo, escolher um dia preenche e salva. O `finish()` ganhou o
`SharpenCal.fechar()` junto, senão Enter e blur deixariam o popover aberto sem dono,
porque nenhum dos dois passa pelo "clicar fora" que fecha o calendário.

Provado em tela contra o `servidor_demo.py` com puppeteer headless, e não só por
`node --check`: o calendário abre no mês da própria célula com o dia dela selecionado ·
clicar num dia dispara `PATCH /bilhetes/{id}` e a célula fecha com a data nova · `Esc`
fecha só o calendário e mantém o editor. Duas armadilhas do arnês, nenhuma do produto:
`screenshot` com `clip` dispara `resize`, e o SharpenCal fecha no `resize` por desenho
(o print vai depois da medição); e `elementHandle.boundingBox()` de dentro do iframe não
serve para `mouse.click` na página, então o duplo-clique vai por evento sintético.

> **Registro do caso 8:** esta mudança **não tem commit próprio**. Ela estava no
> `index.html` esperando aprovação quando a sessão da s331b commitou o mesmo arquivo, e
> foi levada dentro do `eb0b342`. O histórico já estava pushado, então não foi reescrito.
> As duas sessões editaram o **mesmo arquivo**, e aí o `git add` por nome não separa nada
> — é o limite da regra do invariante 8, e vale escrevê-lo: com o arquivo compartilhado,
> quem termina primeiro leva o trabalho do outro junto, e a única defesa é a segunda
> sessão conferir o `git show --stat` e registrar, como está aqui.

### A 2ª rodada de ajustes: laterais +40%, banca total e cards

Concentração e `Últimas ações` **+40%** (285→399 e 300→420), rosca de 110 para **150** ·
a **banca total** entra na Concentração · `Ativas`/`Arquivadas` viram **cards** que são o
próprio filtro · as colunas da tabela se aproximam.

**A banca total mora na Concentração porque é o denominador dela.** Cada "% da banca" da
lista é uma fração daquele número; sem ele o percentual fica sem régua. É o mesmo valor
do KPI `Banca total`, mas ali ele é resultado e aqui é a base da conta que se está lendo.

**Os cards existem porque o mesmo dado estava em três lugares** — meta do cabeçalho,
segmentado e um `N contas` à direita — e nenhum dizia com clareza qual estava
selecionado. Agora o número vive uma vez só, no lugar onde também se escolhe. Trocar de
aba passou a **soltar** o recorte por casa: sem isso o usuário troca de aba e a lista
segue filtrada por uma casa que ele não vê mais marcada.

**A 5ª trilha é sobra, e conserta uma leitura.** O nome estava em `1fr` e engolia toda a
folga do monitor largo, empurrando Status e Caixa para longe da identidade — a linha lia
como duas ilhas. Agora o nome tem teto (340px) e a sobra fica **entre a Caixa e as
Ações**: as três primeiras colunas andam juntas à esquerda e os botões seguem encostados
na borda direita, que é onde se procura ação.

> 819px de painéis laterais pedem monitor largo, e isso não se espreme. O lado a lado
> exige 1.555px de **iframe** (399 + 12 + 712 de piso da tabela + 12 + 420) — cerca de
> 1.870px de janela. Abaixo disso a concentração sobe para cima da tabela, e lá ela ganha
> container query própria (rosca e frase lado a lado, lista em duas colunas) para o
> estado empilhado não parecer acidente.

### Ficou de fora, e está no `BACKLOG.md`

- **Título da página em 19px.** `.pagehead-title` é casca: o `SHELL_SPEC` e o
  `check-tokens` prendem o tamanho a um token, a escada não tem 19px (18 · 22) e o
  Dashboard usa o mesmo contrato. Ficou em `--text-xl`; a cor, que é o que carregava o
  argumento, já tinha ido para `--ink` na s330.
- **Eyebrow em 9px.** O handoff pede 9px/`--ink-soft`, e o piso do papel *Label* na
  Escada é 9,5px. Ficou em `--text-xxs` (10px).

## Sessão 330 — o handoff Opção A, em duas revisões

### O handoff `Contas e Parceiros Opção A` está aplicado, nas 5 fases

Um commit por fase, todos pushados. A tarefa era de **hierarquia**, não de redesenho:
nada de grid geral, raio, sombra, largura de sidebar, rota ou dado persistido.

| Fase | O que mudou |
|---|---|
| 1 | Título sai do gradiente azul · eyebrow sobe um degrau na Escada · `+ Nova conta` e `Fornecedores` no topo direito · `A conferir` vira chip |
| 2 | 4 KPIs viram 3, ordenados por certeza do dinheiro · sai o medidor e o `Caixa total` duplicado |
| 3 | Casa e conta na mesma grade de 4 trilhas · ações só no hover · `Excluir` vai para o menu `⋯` |
| 4 | Coluna Conciliação com vocabulário fechado num helper só · sem abreviação · uma tag por linha |
| 5 | `Contas por casa` mostra 6 e colapsa a cauda · rail vira fila de `Pendências` |

### O que o render pegou e a leitura do spec não pegaria

Duas coisas só apareceram porque cada fase foi fotografada headless contra o
`scripts/demo/servidor_demo.py`. Nenhuma das duas dá erro em lugar nenhum.

- **As trilhas fixas não cabiam.** O handoff pede `minmax(0,1fr) 190px 108px 202px`,
  que são 500px de coluna fixa. A maquete dava ~1.000px à lista; aqui ela dividia a
  linha com `Contas por casa` **e** com o rail da casca, e media **539px em 1600px de
  viewport**. Sobravam 9px para o nome, e o nome da casa saía **clipado**. Medido em
  quatro larguras: 679px em 1440, 539px em 1600, 736px em 1920. **Não é monotônico** —
  o rail entra entre 1440 e 1600 e come ~300px. Por isso a trilha compacta é
  `@container`, não `@media`: quem manda é a largura do painel, não a da janela.
- **Duas regras de `margin-left:auto` da era flex sobreviveram** e esticavam a célula do
  nome. Foi o que clipou o nome da casa na primeira tentativa, com o CSS novo correto.

### Os dois desvios do handoff, e por quê

- **`Sem caixa` não vira tinta.** A Caixa está ligada em **4 de 102 contas**: a tag
  pintaria 98 linhas com o mesmo rótulo, que é exatamente o defeito que o handoff
  existe para matar (os 37 `100%` do log) reencenado noutra coluna. A ausência já está
  dita pelo travessão da coluna Caixa. O estado segue nomeado no mapa, com a flag
  `vazio`, para ninguém inventar rótulo novo quando ele voltar a ser exceção.
- **Tag em 10px, não em 9,5px.** Dois rótulos da lista são `--ink-mute`, e a Escada de
  Tinta proíbe `--ink-mute` abaixo de 10px em qualquer superfície. Meio pixel preserva a
  distinção de cor; baixar a cor apagaria a diferença entre `Calculado` e `Sem caixa`.

O mesmo vale para o título: o handoff pede 20px e 9,5px, que **não existem na escada** do
`SHELL_SPEC` (9 · 10 · 11 · 13 · 14 · 15 · 18 · 22). O `check-tokens` barra px literal de
propósito. Ficou `--text-xl` no título (a mudança que carrega o argumento é a **cor**) e
`--text-xxs` no eyebrow, que é o degrau seguinte.

### Gates

`check-tokens` verde · 3 blocos inline compilados por `vm.Script` · **756 passed, 30
skipped** · render headless a cada fase · varredura da Escada em 3 critérios (px literal,
tamanho por token e `opacity` sobre tom apagado): 3 achados, **todos** exceções já
documentadas (caret/seta e `opacity` como estado), nenhum de código novo.

Comportamento conferido no navegador, não deduzido: 6 barras visíveis / 23 na cauda /
rótulo `+ 23 casas com 1–2 contas` com a faixa real / abre e fecha nos dois sentidos com
`aria-expanded` correto; menu `⋯` abre, fecha em `Esc` e devolve o foco a quem abriu.

### A revisão do Feca, depois de ver a tela na base real

As cinco fases subiram e a tela foi olhada com 177 contas e 47 casas. Quatro coisas
não sobreviveram ao teste, e **uma delas era bug antigo**:

- **O painel da direita não é fila de pendências — é o histórico de extrações (o
  RAIO-X).** A fase 5.2 foi desfeita. O que ele lista são extrações **já feitas**;
  rotular isso de `Pendências`, com contador `14 de 40 ações`, promete tarefa onde há
  registro. **Rótulo errado é pior que rótulo repetido.** A queixa do handoff (37 de 40
  dizem `100%`) continua válida e voltou para o `BACKLOG`.
- **A lista tinha teto de largura nenhum.** A coluna 1 é `minmax(0,1fr)`, e num monitor
  de 2.500px ela chegava a ~1.100px: a linha deixava de ler como linha e virava duas
  ilhas, nome numa ponta e tag na outra. Teto de **960px**, que sai da conta: 32 de
  padding + 42 de recuo + 500 das trilhas fixas + 30 de gap = 604, sobrando ~356px para
  o nome.
- **Casa e conta tinham o mesmo peso.** `R$ 47.376,90` da Bet365 e os quatro valores
  abaixo caíam na mesma coluna, no mesmo corpo, na mesma cor — lidos pela primeira vez,
  cinco parcelas a somar. Agora são três sinais dizendo a mesma frase: fundo próprio no
  cabeçalho, a palavra `total` antes do valor, e guia vertical recuando as contas.

### O bug que estava lá antes de hoje: a barra media 0px

A barra de `Contas por casa` tinha `fill` de **0px em todas as linhas**, inclusive na
maior. O que aparecia na tela era só o trilho vazio — **43 contas e 2 contas desenhavam
exatamente a mesma barra**, e era isso que fazia o card "não dizer nada".

`.painel-bar-fill` é um `<span>`, e em elemento **inline** `width`/`height` em `%`
simplesmente não se aplicam. O trilho escapou por ser filho de um flex
(`.painel-bar-main`) — flex item é blocado automaticamente; o neto não é. Com
`display:block`: 43 → 100%, 15 → 34,9%, 2 → 4,7%.

> Sintoma para reconhecer isto noutro lugar: uma barra proporcional em que **todas** as
> linhas parecem iguais. Antes de suspeitar do cálculo, meça o elemento — `getBoundingClientRect`
> na barra responde em uma linha, e `%` sobre inline é falha silenciosa: não há erro,
> não há aviso, e o CSS parece correto na leitura.

### A 2ª revisão: uma tabela completa no lugar de três cards pobres

O teto de 960px **consertou a linha e quebrou a página** — sobrava mais de mil pixels
de nada entre a lista e o rail. E os três cards de baixo diziam pouco, cada um por um
motivo diferente: `Contas por casa` repetia o contador que já vive no cabeçalho de cada
grupo; `Custos por fornecedor` tinha 3 de 5 linhas sem custo lançado, e o custo já tem
casa própria no Dashboard; `Atividade das contas` era uma **segunda tabela das mesmas
contas** da lista logo acima.

Duração, dias ativos e apostas viraram **colunas da lista**, e os três cards saíram. A
lista tem 7 trilhas e um cabeçalho de colunas — com 7 colunas o rótulo deixa de ser
opcional: `210d` e `165` lado a lado não se explicam sozinhos.

> **O vão não era da largura da lista — era de a lista ter UMA coluna flexível.** Num
> monitor largo ela vira 1.100px de nada e as demais não crescem junto. Com todas as
> trilhas em `minmax(min, Nfr)` a sobra se distribui entre todas, e o teto pôde sair: a
> tabela ocupa a largura porque tem o que pôr nela, não para preencher espaço.

**A margem é de 18px, e está medida.** A soma dos mínimos das 7 trilhas é 740px contra
758px de espaço útil na menor largura (painel de 892px em 1600px de viewport, o mais
apertado por causa do rail). Subir qualquer mínimo sem baixar outro estoura a linha lá —
e o estouro **não aparece no monitor em que se está editando**. Conferido em
1280/1440/1600/1920/2560, sem transbordo em nenhuma.

> Sintoma para reconhecer isto noutra grade: transbordo de célula é **silencioso**. O
> texto vaza por baixo da coluna vizinha, não há erro, e só aparece na largura em que
> ninguém estava olhando. Compare `scrollWidth` com a largura da célula em várias
> larguras — é uma linha, e é o que separa "cabe" de "coube aqui".

**Apostas da casa soma; duração e dias ativos não.** São janelas por conta, e somar dia
ativo de duas contas contaria o mesmo dia duas vezes. Onde não há agregado honesto a
célula fica vazia — não inventa número. E conta sem histórico entra como travessão,
nunca zero: ela não apostou zero vezes, ela não tem histórico.

> Os dois cards que a 1ª revisão melhorou (`Custos por fornecedor` e `Atividade das
> contas`) **saíram na 2ª**. O trabalho não foi perdido: a atividade virou coluna, e o
> custo já tinha casa no Dashboard. Ficou a lição de que melhorar um card não responde
> à pergunta de se ele devia existir naquela página.

### Ficou de fora, e está no `BACKLOG.md`

- **`Duplicar cadastro` e `Transferir de parceiro`** no menu `⋯`: o handoff os lista, mas
  não existe nada por trás dos dois. Item de menu que não faz nada é pior que item
  ausente, então entraram só `Ver extrato da conta` e `Excluir conta…`.
- **`Sincronizando`**: está no vocabulário e não é emitido — a extração em curso não é
  publicada por conta hoje. Fica no mapa para o dia em que houver a fonte.
- **Assimetria do `Custo de Tipsters`** (já aberta desde a s323) segue de pé.

---

## Sessão 329 — a faxina de documentação

### A faxina fechou em F, B, C, D, E. O Lote A ficou aberto, de propósito.

O que mudou de forma, e o custo de abrir uma sessão:

| Arquivo | Antes | Depois |
|---|---:|---:|
| `CLAUDE.md` (auto-carregado) | 68,3 KB | **62,7 KB** |
| `STATUS.md` | 187,6 KB | **~39 KB** |
| `docs/HISTORICO.md` | 1,21 MB | **3,0 KB** (índice + 6 partições) |
| `BACKLOG.md` | não existia | **70 KB** |
| `docs/CASOS.md` | não existia | **22,9 KB** (lido por escolha) |

**O resultado não é o corte de bytes — é que 14 regras que já governavam o comportamento
passaram a estar escritas.** Elas não vieram de análise nova: vieram de ler cada parágrafo
perguntando *"um agente que leia só isto faz a coisa certa?"*. As mais úteis: o `git add`
por nome (prática combinada, nunca escrita), os três "os tetos travam crescimento, não
mandam cortar", o trio de causas da Escada de Tinta e a inversão de hierarquia (as duas
narradas dentro de um caso), e o `node --check` ser falso verde para **tudo** que vive em
template literal (era o exemplo de uma crase).

**Nenhuma regra se perdeu**, e isso foi medido, não afirmado: das 434 âncoras verificáveis
do `CLAUDE.md`, 384 seguem lá e 57 migraram para o `docs/CASOS.md` — zero sumiram. O gate
automático achou **uma perda real** que a conferência manual não veria: uma âncora partida
por quebra de linha no `CASOS.md`.

### O que fica valendo daqui em diante

- **Um arquivo, uma pergunta** (invariante #10). Pendência nova vai para o `BACKLOG.md`,
  nunca para o `STATUS.md`; caso que originou regra vai para o `docs/CASOS.md`.
- **`python tools/check_docs.py`** roda no CI, com 7 checagens **todas provadas por
  mutação**. Ele declara no cabeçalho o que **não** cobre — não lê conteúdo, e a checagem
  de `Backups/` sai como AVISO no CI, nunca como verde vazio.
- **Os tetos travam crescimento; não mandam cortar.** Ao encostar num deles, mova caso ou
  sessão. Nunca corte bloco de "sintoma", nunca suba o teto.

### Este encerramento exerceu o `BACKLOG §1.3` pela primeira vez

O `STATUS.md` estava em 48,2 KB, a 1,8 KB do teto. O bloco desta sessão o estouraria. A
saída foi a que a regra manda: **mover o bloco mais antigo** (`Sessão 325`, 14,5 KB) para
`docs/historico/HISTORICO_s300-s327.md` **antes** de escrever o novo — não subir o teto.

### Ainda aberto

- **Lote A da faxina.** Podar `Backups/`: 223 arquivos `STATUS*`/`HISTORICO*`, 28,7 MB, num
  total de 551 pastas / 128 MB. Corte em **s ≥ 300**, e para as 396 pastas sem prefixo
  `sNNN` a mesma data de corte. ⚠️ **`Backups/` é gitignored — apagar é IRREVERSÍVEL.**
  Zipar a pasta inteira para **fora do repo** e confirmar que o zip abre **antes** de
  apagar qualquer coisa.
- **O resto está no [`BACKLOG.md`](BACKLOG.md)**, agora em um lugar só.

---

## Sessão 328 — a Pinnacle chama o push de `DRAW`


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
