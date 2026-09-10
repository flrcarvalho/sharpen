# CASOS — de onde cada regra do `CLAUDE.md` veio

> **Este arquivo não é lido por padrão.** O `CLAUDE.md` carrega a **regra**; aqui fica o
> **caso** — o bilhete, a casa, o valor em R$, o número da sessão. Abrir isto é ato
> deliberado, normalmente quando alguém quer contestar uma regra ou entender por que ela é
> tão específica.
>
> **A regra sempre vence o caso.** Se os dois divergirem, o `CLAUDE.md` é a verdade e este
> arquivo está velho.
>
> Cada seção tem o mesmo título da seção do `CLAUDE.md` que a originou.
> Criado em 2026-09-07 (faxina de documentação, Lote E). Teto de 60 KB no
> `tools/check_docs.py` — ao estourar, parte por assunto, como o `docs/historico/`.

---

## Invariantes (nunca quebrar)

### #8 — duas sessões commitando ao mesmo tempo, 24/08/2026

O index do git é compartilhado entre sessões. Arquivo que fica esperando entre o `git add`
e o `git commit` é levado por quem commitar primeiro. Aconteceu **duas vezes no mesmo dia,
nos dois sentidos**:

- **`75d93dc`** — uma sessão levou **17 arquivos** da outra.
- **`6cb8037`** — a mensagem era de uma sessão e o conteúdo do `STATUS.md` era da outra,
  **fazendo a narrativa do matcher se perder**: só o código subiu.

### #10 — o inchaço que originou o gate

O invariante #4 ("nunca copiar o `HISTORICO` para o backup, podar snapshots") estava
escrito e claro desde a auditoria de 19/07, e foi ignorado até `Backups/` chegar a
**551 pastas e 128 MB**, com **165 cópias** de `STATUS.md`/`HISTORICO.md` dentro (223 pelo
critério de prefixo). O ritual `/encerrar` mandava manter 3 sessões no `STATUS.md`; o
arquivo chegou a **187 KB**, com o §5 de pendências valendo **51 KB** escondidos atrás de
124 KB de changelog. Quatro arquivos passaram a disputar o papel de "onde o projeto está" —
e três descreviam o projeto de julho.

O custo foi medido: a varredura da s261 registra *"a primeira pendência que eu fui atacar já
estava feita desde 26/07"*.

---

## Aviso de versão ao grupo `Sharpen - Testers`

### O changelog ficou 8 versões atrás, duas vezes

**s254 e s292.** Bumpar o `manifest.json` é obrigatório para a extensão funcionar; escrever
a nota não era obrigatório para nada. Resultado: a caixa "SharpenUp — versão a versão" da
home ficou 8 versões defasada nas duas ocasiões. Daí o `tests/test_changelog.py` ficar
**vermelho** quando a versão do manifest não tem nota.

### O teste de diagnóstico foi parar no grupo

**s282.** Um envio devolveu `ok=false`. A reação foi chamar `sendMessage` de novo para
diagnosticar — e a segunda chamada **publicou o teste no grupo real**, que não tem desfazer.
A causa do `ok=false` estava no `description` da própria resposta: era o `curl` do Windows
não lendo path do Git Bash. Bastava imprimir.

### "Sharpen 0.6.46" versionou o produto inteiro

**s270**, com a mensagem já publicada. O número de versão é do **SharpenUp** (a extensão),
não do Sharpen (o sistema). Escrever o nome errado sugere que o produto inteiro virou 0.6.46.

---

## Conta de usuário nova = duas metades, e a segunda é humana

### A marca não é o username — `Fleury` × `Flurray`

**s260.** A marca do tipster é `Fleury`; o username na tabela é `Flurray`. O isolamento por
`dono` **falha em silêncio**: um import feito sob o nome de marca não dá erro nenhum, só
entrega tela vazia para o usuário certo.

### A senha simplesmente não era aquela

**s264.** O supervisor passou a senha que ele *planejou* (`fredpelado`). Quem se cadastrou
pelo site tinha escolhido outra, e o hash guardado era o dela. A env var estava presente e
íntegra, e mesmo assim o login dava 401. Meia sessão foi gasta procurando defeito de
transporte que não existia — quando `bcrypt.checkpw` contra o hash resolveria em uma linha.

---

## Bot de tipster: NUNCA peça a senha dele

### Como era antes, e por que mudou

Até a **s276** o bot fazia **login como o tipster**. Cada tipster novo obrigava a guardar a
**senha dele** numa env var do Railway — chegaram a três — e a subir deploy. Não escalava,
punha credencial de terceiro sob nossa guarda, e a senha nem era nossa para pedir: quem se
cadastra pelo site escolhe a própria.

### O token subiu antes dos botões

**s276.** O `SHARPEN_BOT_TOKEN` foi para o Railway com só **um dos quatro** tenants
habilitado. Os quatro trocaram de caminho de autenticação juntos, e os três sem botão
passaram a tomar **401 em cada operação**. Nenhum bilhete se perdeu — o `/salvar` é UPSERT
por código —, mas **a marcação de resultado parou de chegar**: o canal mostrava ✅/❌ e a
planilha não acompanhava, sem erro em lugar nenhum.

---

## "Sugerir tipsters" parou?

### O perfil novo que matou o antigo — `MultiLBB` × `LBB`

**s221.** O `MultiLBB` nasceu com a dica de stake `49, 99`. O parser deriva o **final** de
todo valor não-redondo (`49 → 9`, `99 → 9`), então ele virou dono do final 9 inteiro e
empatou com o `199` do `LBB` — **28 × 27**. Com folga menor que 7, o matcher fica vazio de
propósito: **os dois se anularam**, e nada apareceu no rail nem no console. Só a coluna
vazia.

### Os dois cortes que já quebraram o matcher em produção

- **Valor redondo** (50/100/250/800) não é assinatura, é valor comum. Sem esse corte, o
  `M&M` rouba os 50/100 do `Peixe`.
- **`valores.size === 1`** separa "este valor É minha assinatura única" de "é um dos vários
  que eu aposto".

### Assinatura tem ERA

O `199` foi do `SóTudo` até junho e virou do `LBB` em julho. Backtest in-sample pune o
acerto de hoje com bilhete velho.

---

## Teste verde não é teste que detecta

### O teste que reimplementava o código — s286

O harness **reescrevia** a ligação do listener em vez de recortá-la do arquivo. A mutação
que removia o guard passou **verde**: o teste estava exercitando a própria cópia, não o
código.

### O dado sintético que não exercia a regra — s287

Um feed com 5 itens nunca atinge um corte de 12. Sem empate, o desempate não decide nada. E
o sort do V8 é **estável**: um empate pode "acertar" sem regra nenhuma, se a ordem natural
já for a esperada.

### O DOM dublado que sempre clica — s279

O DOM de teste sempre "clica" e nunca rola de verdade. O verde não diz nada sobre rolagem.

---

## API externa por item = peça a FAIXA

### 113 chamadas ao Banco Central — s247

O sync da Polymarket levava mais de 3 minutos e "muitas vezes nem funcionava". A Polymarket
respondia em **3 s**. O resto era o BCB: o câmbio era pedido **uma data por vez**, e 76 datas
de bilhete viravam **113 chamadas sequenciais**.

- **Latência:** 113 × 179 ms = **25 s** com o BCB saudável, sem teto — cresce com o histórico.
- **Falha:** com o BCB oscilando (medido: **1 falha em 6**), 113 chamadas são 113 chances de
  derrubar o sync. Cada falha ainda carregava o backoff do `_get_retry` (3 tentativas + 3 s).

O endpoint de faixa entrega **3 anos de PTAX em uma chamada de 1,3 s**.

### O `except` que achatava dois casos

O `_ptax` antigo devolvia `None` tanto para "não houve boletim nesse dia" quanto para "o BCB
caiu". O laço tratava o timeout como feriado, recuava 10 dias, e só no fim derrubava o sync
inteiro.

### A conferência antes de trocar a fonte

A cotação nova foi comparada com a antiga **nas 76 datas, uma a uma: 0 divergências**. Sem
isso, o re-sync mexeria em stake já gravado, porque `origem='sync'` é `_ORIGEM_AUTORITATIVA`
e refresca `stake`/`odd`/`data` mesmo em bilhete resolvido. Detalhe que quase passou: o BCB
republica alguns dias com **dois** boletins, e o endpoint antigo pegava o primeiro
(`$top=1`) — o mapa novo mantém a mesma escolha (`setdefault`) de propósito.

---

## Regras de deduplicação (sistema)

### A órfã que virou fantasma — a múltipla do Falkirk, Betnacional, s327

A IA devolveu o bilhete mas **perdeu a 11ª coluna**, e a linha entrou sem código. Sem
código ela nunca dedupou: ao liquidar, o mesmo bilhete voltou com código e entrou como
**linha nova**, deixando a velha `aberta` para sempre. Sem erro e sem aviso.

As duas pistas que denunciaram: um `AGUARDANDO RESULTADO` na grade e um stake "em aberto"
na Caixa **num dia em que a casa não tinha pendente nenhuma**.

Na primeira tentativa de conserto, a Migração B ainda falhava: ela comparava a odd como
**string crua**, e `14` não era `14,00`. A adoção só passou a funcionar comparando pela
régua do sistema (`_norm_odd`).

### Blindar metade dos campos: 28 linhas de lucro fantasma

`resultado` nunca foi congelado pelo UPSERT. Com fonte determinística isso deixava a linha
**meio atualizada**: ao corrigir o cálculo do mercado anulado da Polymarket, o resultado
passou de `L` para `W` e a odd ficou a antiga, **dobrada**. **28 linhas viraram
+R$ 578 onde o real era −R$ 11,80.**

O mesmo vício, ao contrário, valia para `esporte`/`aposta`: eles só entravam no INSERT, e
isso trancou **40 linhas mal classificadas** fora de qualquer correção.

É daí que vem a regra: **blindar metade dos campos é pior que blindar todos ou nenhum.**

### O mesmo bilhete com 5 códigos — Blaze, s338

Relato do tester Jonathan: *"a blaze ta puxando bet duplicada, tinha feito isso ontem com
prints e agora com a extensao"*. Na base dele o bilhete do Susanto (31/08) estava **cinco
vezes**, cada uma com um código diferente:

```
#212907 [20] 27063531449244906924   01/09
#216590 [19] 2706253144924498034    02/09
#218223 [18] 270625314492244...     03/09   ← a IA escreveu as reticências
#257345 [20] 27062531440244968824   09/09
#258494 [19] 2706253144924496624    09/09
```

Todas de PRINT. **A Blaze só entrou na captura naquela mesma noite** (`d3f2233`, 19:24), e
o que separou print de captura foi o `uso_tokens.n_itens` (imagens + blocos de texto), não
a suposição: toda extração anterior é de imagem, só a de 20:43 é texto.

O id do BetBy tem 19 dígitos. Lendo o card, a IA errou em **53 dos 55** códigos de Blaze
do banco (17, 18, 20, 21 dígitos; dois com espaço no meio). Lendo o `[Código: …]` da
captura, a mesma IA acerta: Betboom **77 de 77**, Jonbet **18 de 18**.

Como o código entra na assinatura, cada leitura virou um bilhete novo, e o pré-dedup por
código nunca casou. Ao ligar a extensão, o histórico inteiro da casa duplicaria. Não era
só o Jonathan: germano tinha 20 linhas assim e Jaao26 uma.

> A pista para reconhecer isto noutra casa: o comprimento do código varia entre linhas da
> **mesma** casa. Id de casa é de tamanho fixo; leitura de imagem, não.

### A assinatura que ficou para trás — s198 e s312

`casa` e `parceiro` entram no hash de `_assinatura`. Trocar qualquer um dos dois sem
recalcular deixa a linha com o hash antigo — a próxima captura gera assinatura nova, não
colide com nada, o UPSERT não dedupa e **o histórico duplica inteiro**.

Mordeu duas vezes: no `renomear_parceiro` (s198) e no modal de edição de conta (s312), que
oferece nome e casa na mesma tela.

---

## `DADOS` só tem aposta LIQUIDADA

### A tela em branco do Diogo — s239

O Diogo cadastrou **16 contas** e tinha **12 bilhetes, todos em aberto**. A aba Custos de
Contas ficou **em branco**. Não houve erro: `DADOS` recebe só `W/L/V/HW/HL`, então um
usuário novo — que por definição só tem aposta em aberto — chega com `DADOS` vazio, e toda
tela derivada dele fica parada num "aguardando" que nunca resolve.

Na mesma sessão foram medidas as duas divergências que duplicariam linha ao unir cadastro e
bilhete — grafia de casa (`Bet365` × `BET365`) e fornecedor divergente para a mesma conta.
**As duas deram zero em todos os donos.** É medição datada, não garantia: meça de novo antes
de confiar.

### O tipster cobrado e ineditável — s274, feedback do tester João Henrique

A aba Custo de Tipsters listava a partir de `DADOS`, enquanto o `renderOvCusto`
(`overview.js`) somava o `ctData` **inteiro**, sem olhar a lista. Um tipster que ainda não
tinha aposta liquidada **saía da tabela com o custo dele seguindo no KPI da visão geral**:
cobrado, visível no total, e sem linha onde se pudesse editar.

O agravante que torna esse defeito difícil de ver: **o total continua certo.** Só a linha
some.

---

## Gate que confere UM campo deixa os vizinhos livres

### A odd que era o retorno — bet365, s321

`Under 4.0 Gols [Loiske v TP-T]`, bet365, stake **99,00**, entrou com **odd 195,53** — que
era o **RETORNO**, impresso pelo bloco na linha do Status. P/L de **+R$ 19.258,47** onde o
real era **+R$ 96,53**. O caixa da conta não bateu, e foi por aí que apareceu.

O mais duro: o bloco imprime `Odd: 1,975` **duas linhas abaixo**. O número certo estava lá;
ninguém o comparava.

**Por que passou:** a s311 tornou a stake determinística, e a odd só era reconferida como
**efeito colateral** — a chamada de `_odd_da_stake` vivia dentro do `if` que só roda quando
a stake diverge. Stake certa + odd errada passava reto, e o `resultado` não tinha
conferência nenhuma.

### Os 14 HW que um gate de rótulo teria destruído

`_resultadoB3` (`extensor/content.js`) escreve `Ganho → W` para **qualquer** retorno maior
que a stake, meia vitória inclusive. Um gate que lesse o rótulo em vez do número
reescreveria como `W` os **14 bilhetes `HW` que estavam certos**.

### O push da Pinnacle que ficou pendente depois de liquidado — `DRAW`, s328

O de-para de rótulo tinha um `else` dizendo "a conferir — não liquidar automaticamente", e a
IA **obedeceu**. O rótulo `DRAW` não estava cadastrado, então a linha ficou `aberta` para
sempre, sem erro em lugar nenhum.

O modelo até anotou no RAIO-X que o `P/L 0,00` indicava reembolso — **e não podia agir**,
porque a instrução do bloco mandava o contrário.

A tela da Pinnacle exibe `REEMBOLSADO`; a API manda `DRAW`. Documentar só o que a tela
mostra esconderia o caso.

### A Betfair que mistura BR e EN no mesmo bloco

Stake e odd em convenção BR (`300,00`, `5,4746`), retorno em EN (`Retorno 1,642.38`). Ler
tudo como BR dá **1,64** e "corrige" a odd para **0,0054** — **5 linhas certas destruídas**.

E a regra "3 dígitos = milhar", correta para dinheiro, multiplica toda odd de 3 casas por
mil: `1,775` vira **1775**.

### O piso de R$ 1,00 — a "correção" que sujava a odd

Abaixo de R$ 1,00 de diferença, corrigir troca a odd limpa da casa (`1,925`) pela dízima do
retorno arredondado ao centavo (`1,925087108`). Ruído por ruído.

### Os 3 bilhetes Betano em que alguém inverteu W e L

Três bilhetes com `W→L` e `L→W` trocados **no mesmo minuto** — edição humana deliberada.
Certo ou errado, é decisão do dono, e por isso o script de reparo pula bilhete cujo
`resultado`/`odd` já tenha registro em `correcoes`.

### A medição que autorizou o gate

Replay em **5.316 blocos** da sombra (**20 casas**): mexe em **3** — exatamente as 3 de
edição humana. **Zero falso positivo.** E o gate reproduziu, sozinho, as **33** correções
que o script já tinha feito. Os testes: **5 mutações aplicadas e pegas**.

---

## REGRA DE UI / MARCA OBRIGATÓRIA

### Os cards de KPI com formatador caseiro — s83

Cards de KPI foram criados com formatadores próprios que **abreviavam** (`1,4k`) e
**coloriam o valor inteiro** — violando 4 regras do padrão monetário de uma vez. O Feca teve
de voltar em detalhe **já documentado**.

A causa não foi falta de regra: **regra escrita sem hábito de conferir = pulada.** É por isso
que a seção do `CLAUDE.md` é um checklist numerado e não um texto.

### A crase que deixou o dash em branco — s296

Uma **crase** dentro de um comentário HTML, dentro do `buildHTML`, passou no `node --check` e
derrubou o dashboard inteiro com `ReferenceError`. O `node --check` é **falso verde** para
tudo que vive dentro de template literal.

Medir a tela é o único gate que pega isso.

### As duas armadilhas de reparsear o que a tela imprimiu — s300

Medidas em produção:

- O sinal negativo do `fmtPL` é **U+2212 (`−`)**, não hífen. `parseFloat` devolve `NaN`, que
  vira 0 — e **todo valor negativo ordena como zero**.
- O `fmtR` imprime milhar **sem decimal** (`R$ 5.180`). Uma regra de milhar que olhe o que
  vem depois do ponto erra; ela tem de decidir pela **forma** do número.

### O filtro que a tela já tinha — s317

Os filtros novos foram para um **segundo cartão**, embaixo dos KPIs, com a barra da página
seguindo em cima. Partido em dois, o de cima **sai do campo de visão** de quem mexe no de
baixo, e a tela passa a parecer que não tem o filtro que tem: o Feca pediu *"filtro para
Tipster, Casa e Esporte"* — **os três já existiam**, no outro cartão.

Na mesma tela, dois estilos para o mesmo papel: `.apf-lbl` (correto pela Escada de Tinta) ao
lado de `.filter-label` (errado). O olho lê as duas como inconsistentes **sem saber qual é
qual** — é o sintoma barato de "fora do padrão", e ele aparece mesmo quando uma das metades
está certa.

---

## Escada de Tinta

### O cabeçalho que virou textura — Painel de Contas

O cabeçalho de grupo usava `--ink-mute` em **9,5px caixa alta com tracking .16em** sobre
fundo efetivo `#1A1F26` — **2,9:1**. Reprova AA (4,5:1) e reprova até o piso de texto grande
(3:1).

**O feedback que abriu o caso foi de USO, não de auditoria:** *"essas letras nesse cinza
claro fica muito claro"*. Nenhum lint tinha acusado.

Três causas somaram — tom baixo, corpo minúsculo e tracking largo em caixa alta — e o que
escondeu o problema de quem media foi o **overlay de `.025`**: o contraste calculado sobre o
token do CSS passava; sobre o fundo efetivo, não.

Junto veio **inversão de hierarquia**: o e-mail da conta (13,5px / 700 / `--ink`) pesava
mais que o nome da casa, então a varredura da lista lia **endereços em vez de casas**.

---

## REGRA DE PROPAGAÇÃO OBRIGATÓRIA

### As três categorias que ficaram apontando para `Outros` — 13/06/2026

`Dupla Chance`, `Impedimentos` e `Chutes no Gol` foram criadas no MASTER, e os mapas das
casas ficaram desatualizados apontando para `Outros ⚠️`.

**A causa raiz era a DUPLICAÇÃO:** cada arquivo de casa reescrevia a lista inteira de
categorias. Desde a **sessão 49** (camada fina), o `§9` lista só o que aquela casa confirma
— e a superfície de propagação encolheu para as casas realmente afetadas.

> ⚠️ Este parágrafo, no `CLAUDE.md`, dizia "as 27 categorias". Medido em 07/09 pelo parser
> canônico (`audit_casas.categorias_oficiais()`), o `§3` tem **30**. A contagem literal saiu
> do `CLAUDE.md` de propósito: a lista canônica vive no `§3` e number solto apodrece. A
> string errada ainda está em 4 arquivos de casa — registrado no `BACKLOG` (`#99`).

---

## Perfil de tipster: a casa é SAÍDA da leitura

### As três recusas seguidas do Rogerin — s309, dia 1 do 6º tenant

O prompt dizia *"Você lê prints da casa de apostas Betano"*. Ele mandou **três prints de
bet365** e tomou **três recusas seguidas** — `⚠️ Não consegui ler o print`, culpando a foto.

O modelo leu as duas instruções como uma só: o prompt abria nomeando uma casa e fechava com
`Print ilegível → {"erro": …}`, então **casa diferente virou imagem ilegível**.

### As três simples que viraram uma múltipla de 73

Casa que vende N apostas simples num print só — stake e retorno **por seleção**, "Aposta
Total" no rodapé — quebra o perfil que assume "1 print = 1 bilhete". As pernas viram uma
múltipla, **sem erro nenhum**: odd `1,66 × 4,00 × 11,00 ≈ 73` no lugar de três apostas.

---

## Zero não é ausência

### O bilhete ganho que virou −1u — Só Chutes #12, s318

`Osimhen + Shomurodov @ 5.50`, bilhete de mesmo jogo, **os dois ✅**. A casa não precificou
as pernas — trouxe só a odd do conjunto —, e quem montou a combinação como produto das
pernas fez `0 × 0 = 0`.

O P/L de `W` é `stake × (odd − 1)`. Com odd 0, o bilhete **ganho** virou **−1u**.

### A linha que nunca existiu, e a pista que apareceu um dia depois

O `/salvar` recusou a linha na fronteira e devolveu **200** com a recusa em `rejeitados`. O
bot **ignorou o campo**: marcou "planilhado", publicou no canal e seguiu.

A linha do #12 **nunca existiu** na planilha. A única pista apareceu **um dia depois**, como
um *"não tenho o id no Sharpen"* na hora de corrigir.

---

## A data é a que a fonte TEM

### O mês que fechou negativo porque a folga datou 8 vitórias amanhã — s339

**22:50 de 09/09/2026.** O Feca abre o relatório do tipster `Ctrl Alt Green` e vê **MTD
−R$ 892,87**, com a grade mostrando oito apostas de eBasket **datadas de 10/09** — um dia
que ainda não chegou. Duas perguntas na mesma mensagem: *"o resultado não parece atualizado"*
e *"por que você finalizou apostas com 10/09?"*. **Era o mesmo defeito nas duas.**

As 8 linhas estavam no banco, todas `W`, somando **+R$ 928,00**. O MTD recorta
`[1º do mês, hoje]` (`filters.js`, `st.dt = today`), então bilhete datado de amanhã cai fora.
Com as 8 dentro, o mês vai de **−R$ 892,87 para +R$ 35,13**: o filtro trocou o **sinal** do
resultado do mês.

**A causa:** `_dataFimB3` somava ao kickoff uma folga por esporte (`_OFF_B3`) para estimar a
liquidação. eBasket chega da bet365 como `CL=18` — **Basquete**, porque a casa não separa os
dois; quem separa é o `_e_ebasket` do `app/tradutor.py`, pelo handle do gamer nos dois lados —
e levava **2,5 h de folga num jogo que dura ~4 minutos**. Kickoff 22:35 + 2,5 h = 01:05 do dia
seguinte.

A assinatura, medida: as 8 foram capturadas entre **22:30 e 22:40** e as 8 ganharam data +1.
Nenhum dos outros 397 eBasket da base, fora dessa faixa de horário, foi deslocado.

**A escala.** Todo esporte tinha folga (1,5 h a 3 h), então havia uma janela diária de ~21h à
meia-noite. Piso medido na base (data = dia da captura + 1, com captura depois das 21h):
**188 linhas** da Bet365 — 73 Múltiplos · 54 Futebol · 37 Badminton · 8 Basquete · 8 eBasket ·
5 Tênis · 2 Dardos · 1 E-Sports. É **piso**: quem foi capturado no lote da manhã seguinte
carrega o mesmo deslocamento e não aparece na conta, porque o banco não guarda o kickoff.

**Por que sobreviveu tanto tempo.** O efeito no KPI se desfaz sozinho: amanhã 10/09 entra no
MTD e o número "conserta". O que não se desfaz é o **dia errado** — o P/L de terça fica
lançado na quarta para sempre, e a coluna Data da planilha sai errada. Um defeito que se
apaga da tela sozinha toda madrugada não gera reclamação, gera desconfiança difusa.

**A decisão (Feca, s339):** `Data = kickoff`, para todos os esportes. É o que a tela da própria
bet365 mostra, o que as outras casas gravam, e a única data que o payload realmente tem.

### A mutação que passou verde

O gate novo (bloco 9 do `extensor/harness/casos/bet365.mjs`) nasceu com 5 mutações; **4
detectadas na primeira rodada.** A que escapou: fixar `ukToBr = 4` (ignorar o GMT do inverno
britânico) deixava tudo verde, porque nos casos escolhidos a diferença entre UK−3 e UK−4 caía
**dentro do mesmo dia**.

O horário de verão britânico só troca o **dia** na faixa **03:00–04:00 UK**. Foi preciso um
caso em janeiro e outro em julho, ambos às 03:30, para prender o erro **nos dois sentidos** —
com um só, metade do defeito passa. É o segundo modo de falso verde do `CLAUDE.md` ("o dado
sintético não exerce a regra") aparecendo num teste escrito **na mesma sessão** que a regra.

---

## Planilha e bot escrevem na MESMA série de código

### A aposta que foi absorvida — PassaTips #259, s276

O import gravou `PT202608-259` às **09:19**; o bot criou o bilhete **#259** às **09:20**,
mesma casa e mesma conta. A assinatura bateu, o `/salvar` tratou como o **mesmo bilhete**, o
congelamento manteve descrição/odd/stake da linha importada, e "vazio nunca rebaixa" manteve
o resultado.

**A aposta do dia foi absorvida — sem erro, sem aviso, sem linha nova.**

### O prefixo que parecia livre e não estava — `SP`, s316

`SP` quase foi dado ao `Soh Props`. É o prefixo da **Superbet**, que grava código nativo no
formato `SP8399910931W` — duas letras mais dígitos, igual à nossa série, mas **sem** o
`<aaaamm>-<n>`. Um regex ancorado no formato da série **não os enxerga**, e o prefixo
aparece livre quando não está.

`SH`, `SS`, `PR` e `HP` também estavam ocupados assim.

Não havia colisão de assinatura (o formato difere e `casa` entra no hash), mas um `SP` na
base lê como Superbet para qualquer humano depois.

---

## Linha bem-formada pode ser de OUTRO bilhete

### A descrição que era do vizinho — s302

`Matthew Dennant [Norwich v Burnley]`: separador certo, confronto bem formado, nada
proibido. Passou em `checar_descricao` **sem um arranhão**, e a cobertura contou 65 de 65.

O bilhete era `Norwich x Burnley · Mais/Menos de 3,5 Cartões`.

### A stake que era do vizinho, com o P/L intacto — Pinnacle, s311

Até a s311 a regra dizia que só esporte/categoria/descrição erravam, porque stake, odd e
resultado eram cópia. Era **observação medida, não garantia**.

Na Pinnacle `3113103675` a stake veio `400,00` — a do `3114339695`, **duas linhas acima no
mesmo chunk**. E como em `W` a odd é derivada (`Retorno ÷ Stake`), ela foi recalculada
**sobre a stake errada**: `(400 + 330,48) ÷ 400 = 1,8262`, mantendo o P/L **exato** em
R$ 330,48.

Descrição certa, código certo, resultado certo, P/L certo. Erraram só turnover, ROI e a
assinatura de stake do matcher — **o bilhete perdeu o tipster, porque 400 não é a stake
dele**.

### As medições que autorizaram o gate de stake

A linha `Stake:` casa em **100% dos 5.128 blocos** da sombra (20 casas), e o replay do gate
mexe em **3 linhas de 3.820** — as 3 divergências reais, zero falso positivo.

Na fidelidade de descrição: **1.327 de 1.337** passam; das 10 reprovações, **9 eram erro
real**.

### A IA que acertou nas duas últimas e o banco ficou com a primeira — `0001941`

A sombra mostra o mesmo bilhete lido **três vezes na MESMA extração**, com acerto nas duas
últimas. O banco ficou com a primeira: o `ON CONFLICT` nunca atualiza
`esporte`/`aposta`/`descricao` fora de `origem='sync'` — **nem com a linha `aberta`**, ao
contrário de odd/data/stake.

---

## Caixa Inteligente

### A Caixa ligada no meio da captura — Betnacional, s327

Entre a captura começar e o `/salvar` gravar há **~1 minuto**. A Caixa foi ligada dentro
dessa janela e gravou `abertas_corte` **vazio**: **R$ 600,00** de stake ficaram fora da
conta, e a projeção saiu **R$ 1.362,26 abaixo** do que a casa mostrava. O Ajuste da
conferência seguinte cimentou o erro **com cara de número conferido**.

### O script que inflou a projeção em R$ 10.477

Um script que recalcula depois precisa passar `ate` = o instante da ativação. Sem isso ele
adota aposta feita **mais tarde no mesmo dia** e infla a projeção — medido: **+R$ 10.477**.

### Os dois números certos que pareciam defeito

O tile dizia `P/L · conta −R$ 1.608,00` e a Caixa dizia `Resultado R$ 0,00`. **Os dois
certos**: as apostas eram anteriores ao corte, logo já estavam no saldo informado. E ainda
assim a tela parecia quebrada.

A saída não foi mudar número nenhum — foi a tela **dizer o corte** — `Resultado · desde 03/09` — mais a nota do que ficou de
fora.

---

## Custo de aquisição tem JANELA DE VIDA

### A régua antiga: R$ 0 de custo com o parque inteiro em uso

Antes, o custo da conta era lançado num **único dia** — o da **primeira aposta liquidada**.
Filtrar qualquer outro dia dava **R$ 0**, mesmo com o parque de contas em pleno uso.

A régua nova cobra o custo **cheio** em todo período que **cruza** a janela de vida da conta.
Ela **não é aditiva**, e isso foi aceito com a conta na mesa: somar os dias de setembro dá
muito mais que o custo de setembro. A alternativa — ratear pelos dias — foi **recusada de
propósito**, porque rateio exige um horizonte arbitrário e a janela pelo uso não tem
constante nenhuma.
