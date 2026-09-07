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
