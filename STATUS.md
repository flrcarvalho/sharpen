# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-09 (sessao 333: **handoff `Contas e Parceiros v2` — Fases 7 e 8 aplicadas.** A Fase 7 e distribuicao por LARGURA e a Fase 8 e a zona de Fornecedores. **O vao de ~800px no monitor de 32" nao era margem errada, era COLUNA SOBRANDO:** a folga vivia numa faixa antes das acoes, entao nome/status/caixa ficavam ancorados a esquerda e os botoes na borda direita, com nada no meio. Agora a unica coluna elastica e a PRIMEIRA (o nome, que sempre tem o que mostrar) e a folga vira INFORMACAO: duas faixas nascem em 0px e abrem por degrau — `Fornecedor` e `Ultima captura`. **Dois containers, cada um medindo o que governa:** o `pc` mede a AREA DO APP e decide quantas zonas cabem lado a lado; o `acct` mede a TABELA e decide quantas colunas cabem nela. Um container so nao resolveria: o mesmo monitor da larguras diferentes a tabela conforme o numero de zonas ao lado, e foi por isso que a coluna de fornecedor abriu em 1366 (log embaixo, tabela inteira) e nao em 1440 (log ao lado). **Os cortes do handoff (1500/1900/170/176) NAO foram copiados — foram MEDIDOS, e tres deles nao fechavam:** as acoes medem 208px e a trilha proposta era 176; a linha da CASA precisa de 220px de nome (favicon + `Esportes da Sorte` + pilula de contagem) e a proposta era 170; e com os cortes de pagina em 1500/1900 a tabela caia abaixo do proprio piso em 1440, 1600 e 1920 — sem erro, porque `justify-content:flex-end` transborda para a ESQUERDA e isso some do `scrollWidth` (a armadilha da s331d). Os cortes agora saem da conta do conteudo: 842px de piso de tabela, 1094 / 1334 / 1738 / 2030 de area de app. **Fase 8 — a tela se chama Contas & Parceiros e nao dizia nada sobre FORNECEDOR.** Risco de fornecedor nao e risco de casa: casa que trava saque e burocracia, fornecedor que some e o dinheiro. Entrou a terceira zona (ordenada por caixa, com o proprio usuario como contraponto), o 4o KPI `Em contas de fornecedores`, o segmentado de fornecedor na barra da tabela e a linha de total no rodape, na MESMA grade das linhas. Nenhum dado novo: tudo e agregacao do `[Fornecedor]` que ja vive no nome da conta. **Estado novo `Parada ha N dias`, em CINZA:** conta ativa sem captura ha mais de 30 dias se disfarcava de `Conciliada` — estava limpa porque ninguem a usava. Cinza e nao ambar de proposito: abandono nao e pendencia e nao pode competir com pendencia de verdade. O unico campo novo e o `ultima_captura` do `/caixa/visao`, que e o maior `criado_em` dos bilhetes da conta — e o rotulo diz **captura**, nao "extracao", porque extracao que nao achou bilhete novo nao aparece ali. **Gates:** check-tokens verde, 767 passed / 30 skipped, o gate novo `tests/test_contas_status.py` com **8 mutacoes, 8 detectadas**, e `scripts/demo/medir_contas.mjs` medindo a tela em 1366/1440/1600/1920/2560 (transbordo 0 em todas, zero tag na casa, 29 chips TOTAL, nenhuma abreviacao). **Achado medindo, NAO corrigido:** ha dois `Banca total` na mesma tela e eles divergem — o KPI soma toda conta ligada, a faixa da Concentracao soma so casas com `banca > 0`. Foi para o `BACKLOG §4`.)

_Anterior: 2026-09-08 (sessao 332: **remedicao do estudo de custo. Nenhuma alteracao de codigo.** Medicao read-only no Postgres de producao, comparando a janela do estudo (25/07 a 24/08) com a pos-correcoes (25/08 a 08/09). **Validacao do metodo:** refazendo a conta na janela original deu US$ 0,0152 por bilhete contra os 0,0150 do documento, entao o resto e comparavel. **As correcoes A e C entregaram o que prometiam:** `cache_write` por chamada de 13.745 para 3.371 tokens, chamadas chegando frias de 34,8% para 1,9%, aquecedor de US$ 173 para US$ 12,5 por mes. **E mesmo assim o numero que decide o preco piorou:** o custo VARIAVEL por bilhete subiu 12% (R$ 0,078 para R$ 0,087), porque A e C mexeram no custo FIXO, e custo fixo dilui com escala. Duas causas, as duas medidas: (1) o `_BILHETES_POR_CHUNK = 6` da s301 levou os chunks de 3,27 para 4,02 por chamada, com cauda ate 55, e cada pedaco rele o manual inteiro, entao o `cache_read` por chamada foi de 156k para 231k; (2) bilhetes novos por chamada caiu de 14,5 para 11,6 e o input por bilhete subiu 43%, que e recaptura de bilhete que o banco ja tem. **O saldo liquido e bom:** capturamos 47% mais bilhete pagando 3% menos, e o custo REAL por bilhete caiu 34% (R$ 0,137 para R$ 0,090). **A consequencia para o preco e a correcao do estudo:** a escada do §4 nao fecha so com a Bet365 deterministica, porque Pro e Operacao ficariam em 12% de margem bruta. Bet365 mais Betano sao 64,3% da conta e 58% dos bilhetes por IA, e com as duas a escada fecha em 41 a 64%. A Fase 0 do tradutor ja tem massa para a Fase 1: 13.965 pares bruto x decisao da IA, em 21 casas, em 13 dias. Registrado no `docs/ESTUDO_PRECIFICACAO_2026.md §7` e no `BACKLOG §3.7`, com tres pendencias novas no `BACKLOG §4` (o rotulo errado do `/uso/tokens`, a remedicao em 30 dias e a infra do Railway). O STATUS voltou de 46,9 para 36 KB, com as sessoes 329 e 328 arquivadas verbatim na particao do historico.)

_Anterior: 2026-09-07 (sessao 331 — **handoff v2 aplicado: `Contas e Parceiros v2`, 6 fases num commit so.** A tela deixa de ser tres colunas concorrendo e passa a ter QUATRO leituras: dinheiro no topo estreito · `Ultimas acoes` na lateral inteira comecando na MESMA linha dos KPIs · `Concentracao de caixa` ao lado da tabela de Contas. **O rail da casca saiu desta tela** — ele e o RAIO-X, que pertence a Extracao. **Concentracao substitui `Contas por casa`, que contava CONTAS:** contar conta nao diz risco nenhum, e 52 contas numa casa com R$ 0 desenhavam uma barra maior que 1 conta com metade da banca. Agora e rosca por `stroke-dasharray` sobre perimetro 100 (cada arco e literalmente "P por cento"), rampa FIXA de 8 tons — tom calculado do valor faria a MESMA casa mudar de cor entre duas aberturas, e a cor e a chave que liga rosca e lista. Clicar filtra a tabela; clicar de novo solta. **Pilulas de status** num helper unico, lista fechada, numero em `<b>`, com o estado NOVO `Aguardando tipster N` em AZUL: bilhete sem tipster e espera externa, nao erro, e antes ele somava com as apostas abertas num numero so — apagando a diferenca entre "eu resolvo" e "depende de alguem". **Tabela:** 4 trilhas, chip `TOTAL` na trilha da Caixa, `.acct-group` fechando o bloco, SEM traco/arvore, e os tres botoes de volta na linha. Sairam as colunas Duracao/Dias ativos/Apostas (descreviam ATIVIDADE; a tela responde "quanto tem e esta conciliado?"). **Duas armadilhas de largura, as duas invisiveis na leitura e medidas no headless:** (1) media query DENTRO do iframe le a largura do IFRAME, e a sidebar (~300px) fica fora dele — num monitor de 1440 a pagina tem 1120, e o breakpoint de 1180 do handoff disparava sempre, jogando o log para baixo em TODA largura; (2) com as trilhas em px cravado sobravam 130px para o nome em 1440 e "Esportes da Sorte" saia cortado — as tres viraram `minmax(min, alvo)` e cedem antes do NOME ceder. Conferido em 1366/1440/1600/1920/2560. **Gates:** check-tokens verde, 756 passed / 30 skipped, Escada em 3 criterios sem achado novo, fumaca no navegador (zero tag na casa, 29 chips TOTAL, sem arvore, filtro ligando e soltando) e a rosca provada com 12 casas sinteticas: 9 arcos somando exatamente 100.)


> **Histórico completo das sessões 329 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 333)

### Contas & Parceiros: a folga do monitor largo virou informação

As Fases 7 e 8 do handoff v2 estão aplicadas. A tela tem cinco leituras: quatro
números de dinheiro no topo, `Últimas ações` na lateral inteira e, embaixo,
`Concentração de caixa` · `Contas` · `Fornecedores`.

| Área do app | Zonas | Colunas da tabela | Ações |
|---|---|---|---|
| < 1.094px | tudo empilhado, log embaixo | Conta (fornecedor ao lado) · Status · Caixa | no hover |
| 1.094–1.333 | log ao lado, zonas empilhadas | idem, e a de Fornecedor abre se a tabela ≥ 990 | no hover |
| 1.334–1.737 | Concentração ao lado da tabela | + **Fornecedor** como coluna própria | no hover |
| ≥ 1.738 | as três zonas lado a lado | + **Última captura** com a tabela ≥ 1.150 | sempre visíveis |

> **O que esta sessão ensinou, e vale para qualquer tela com degrau:** o corte não
> sai do número do handoff, sai da conta do conteúdo — e a conta muda conforme o
> que está ao lado. Por isso são DOIS containers e não um: o `pc` mede a área do
> app e decide as zonas; o `acct` mede a tabela e decide as colunas. Com um só,
> o mesmo monitor abriria a coluna numa largura e a fecharia noutra sem motivo
> visível. E encostar num corte cedo demais **não dá erro**: a tabela transborda
> para dentro do `overflow:hidden` do painel e some do `scrollWidth`.

### O que ficou aberto desta sessão

Os dois `Banca total` divergentes ([`BACKLOG §4`](BACKLOG.md#4-dívida-técnica-medida)) —
medido, não corrigido, porque o conserto muda o significado de um dos dois e essa
escolha é do Feca.

---

## Sessão 332 — a remedição do custo

### A remedição do custo: as correções acertaram o alvo, e o alvo era o outro

O [`ESTUDO_PRECIFICACAO_2026 §7`](docs/ESTUDO_PRECIFICACAO_2026.md#7-revisão-de-08092026-s332--o-que-aconteceu-depois-de-a-e-c)
tem a medição inteira. O resumo é que **capturamos 47% mais bilhete pagando 3% menos**,
e mesmo assim a tabela de preços ficou mais difícil de fechar.

| | Estudo (25/07 a 24/08) | Agora (25/08 a 08/09) |
|---|---|---|
| Conta real de API | US$ 404/mês | US$ 391/mês |
| Bilhetes novos por IA | 15.150/mês | **22.316/mês** |
| Custo **real** por bilhete | R$ 0,137 | **R$ 0,090** |
| Custo **variável** por bilhete | R$ 0,078 | **R$ 0,087** |

A correção A fechou um vazamento de US$ 173/mês, e ele era **fixo**. O custo variável, que
é o que a escada de preço consome, subiu 12%.

### O que isso muda na decisão

A pré-condição do modelo de preço deixou de ser uma casa e passou a ser duas. Só com a
Bet365 determinística, Pro e Operação fecham em 12% de margem bruta, que não paga infra
nem gateway. Com Bet365 e Betano a escada fecha em 41 a 64%. As duas juntas são 64,3% da
conta e 58% dos bilhetes por IA, e a Fase 0 do tradutor já acumulou 13.965 pares em 21
casas para validar as duas.

> **Sintoma para reconhecer isto noutra frente:** uma otimização que melhora exatamente o
> indicador que ela mira e piora o que decide o preço. A correção A mirou custo fixo e
> acertou. O `_BILHETES_POR_CHUNK` da s301 mirou output e latência e acertou. Nenhum dos
> dois mirou o custo variável por bilhete, e ninguém mediu o outro depois. Toda otimização
> daqui em diante declara qual custo mira e mede o outro na sequência.

### O que ficou aberto

Está tudo no [`BACKLOG.md`](BACKLOG.md): a decisão de escopo do tradutor (`§3.7`), o
rótulo errado do `/uso/tokens` (`§4`, de pé desde a s295), a remedição em 30 dias e a
infra do Railway, que segue não medida.

---

## Sessão 331 — Contas e Parceiros v2, em 6 fases

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

### `Aguardando resultado`, não `Pendências` — e o que o rótulo novo revelou

Correção do Feca, e ele está certo: aquilo vem de `abertasDe()`, são apostas **não
liquidadas**. *Pendência* promete algo a fazer; ali não há o que fazer — espera-se o
jogo acabar. O rótulo passou a descrever o fato.

A classe virou `.aguard` e **não** `.pend` de propósito: `.pend` continua existindo para
o log, onde *pendência* é pendência de **extração** — essa sim é algo a resolver. Mesmo
tom âmbar, fatos diferentes; reusar o nome misturaria os dois. A precedência também
mudou: entre as duas esperas, a de **resultado** vem antes da de **tipster**, porque a
primeira resolve sozinha com o tempo e a segunda depende de alguém agir.

> **O rótulo mais longo revelou um truncamento silencioso.** `Aguardando resultado 13`
> mede 175px e a trilha de Status dava 148. A pílula tinha `overflow:hidden` +
> `text-overflow: ellipsis`, então **o que caía fora era o NÚMERO** — exatamente a
> mentira que a regra "nunca abreviar, número sempre real" existe para impedir, e sem
> erro nenhum. A trilha foi para `minmax(160px, 200px)` e a pílula **perdeu o ellipsis**:
> se um dia não couber, o defeito aparece na tela em vez de virar dado errado.
>
> Sintoma para reconhecer isto noutro lugar: `text-overflow: ellipsis` num componente
> que carrega **dado**, e não só rótulo. Ellipsis é honesto num nome próprio (o `title`
> devolve o resto); num número ele apaga a informação e não deixa rastro.

Junto: rosca **+50%** (150 → 225) e a **banca total destacada** — faixa própria em
`--surface-2` com tarja de acento, valor em 22px, o maior número do painel porque é o
denominador de todos os outros. Crescer a rosca ainda corrigiu de graça uma violação
herdada do handoff: o rótulo do centro estava em 7,5px, abaixo do piso de 9,5px do papel
*Label*; agora cabe em 11px.

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
