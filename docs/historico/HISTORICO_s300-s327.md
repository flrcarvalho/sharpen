# HISTÓRICO — Sessões 339 → 300

> Os blocos completos que saíram do `STATUS.md` (339 e 336 → 317), a Sessão 315 e a cadeia `_Anterior_` de 324 até 300.
>
> Partição do `docs/HISTORICO.md`, criada na faxina de documentação de 2026-09-07 (Lote C). **O texto é o original, verbatim** — só foi partido.

[↑ Índice](../HISTORICO.md) · [mais antigo: Sessões 299 → 243 →](HISTORICO_s243-s299.md)

---

## Sessão 339 — o mês que fechou negativo porque a folga datou 8 vitórias em amanhã

### O mês que fechava negativo porque a captura datava 8 vitórias em "amanhã"

**22:50 de 09/09/2026.** O relatório do tipster `Ctrl Alt Green` mostrava **MTD −R$ 892,87**
e a grade trazia oito apostas de eBasket datadas de **10/09** — um dia que ainda não tinha
chegado. Duas perguntas na mesma mensagem, *"o resultado não parece atualizado"* e *"por que
você finalizou apostas com 10/09?"*, e **era o mesmo defeito nas duas**.

As 8 estavam no banco, todas `W`, somando **+R$ 928,00**. O MTD recorta `[1º do mês, hoje]`
(`filters.js`, `st.dt = today`), então bilhete datado de amanhã cai fora. Com elas dentro o
mês vai para **+R$ 35,13**: o filtro trocava o **sinal** do resultado.

### A causa: uma folga que estimava um instante que a casa não informa

`_dataFimB3` somava ao kickoff uma folga de encerramento por esporte (`_OFF_B3`), para
estimar a liquidação. eBasket chega da bet365 como `CL=18` — **Basquete**, porque a casa não
separa os dois; quem separa é o `_e_ebasket` do `app/tradutor.py`, pelo handle do gamer nos
dois lados — e levava **2,5 h de folga num jogo que dura ~4 minutos**.

A assinatura bate: as 8 foram capturadas entre **22:30 e 22:40** e as 8 ganharam data +1.
Nenhum dos outros 397 eBasket da base, fora dessa faixa de horário, foi deslocado.

| Esporte (Bet365) | linhas com data = dia da captura + 1, capturadas após 21h |
|---|---|
| Múltiplos | 73 |
| Futebol | 54 |
| Badminton | 37 |
| Basquete | 8 |
| eBasket | 8 |
| Tênis · Dardos · E-Sports | 8 |
| **total** | **188** |

É **piso**, não total: quem foi capturado no lote da manhã seguinte carrega o mesmo
deslocamento e não entra nessa conta, porque o banco não guarda o kickoff para conferir.

> **Por que sobreviveu tanto tempo:** o efeito no KPI se desfaz sozinho — amanhã 10/09 entra
> no MTD e o número "conserta". O que não se desfaz é o **dia errado**. Um defeito que se
> apaga da tela toda madrugada não vira reclamação, vira desconfiança difusa.

### A decisão: `Data = kickoff`, para todos os esportes

Do Feca. É o que a tela da própria bet365 mostra, o que as outras casas gravam e a única data
que o payload realmente tem. Um jogo que começa 22:00 do dia 09 e termina 00:30 do dia 10 é
do dia 09. A **conversão UK→Brasília não é a folga** e continua obrigatória (o payload traz
hora de parede de Londres). O rótulo do bloco virou `Data (evento):`, que já era o das outras
casas de API — o tradutor casa a chave por prefixo, então nada mais precisou mudar.

Regra em `CASA_BET365 §4` e no `CLAUDE.md`; o caso em [`docs/CASOS.md`](../CASOS.md).

### O gate, e a mutação que passou verde

Bloco 9 do `extensor/harness/casos/bet365.mjs`, **provado por 5 mutações**. A terceira
**escapou na primeira rodada**: fixar `ukToBr = 4` (ignorar o GMT do inverno britânico)
deixava tudo verde, porque nos casos escolhidos a diferença entre UK−3 e UK−4 caía **dentro
do mesmo dia**. O horário de verão britânico só troca o **dia** na faixa **03:00–04:00 UK**,
então foram precisos um caso em janeiro e outro em julho, ambos às 03:30, para prender o erro
**nos dois sentidos** — com um só, metade do defeito passa.

É o segundo modo de falso verde do `CLAUDE.md` ("o dado sintético não exerce a regra")
aparecendo num teste escrito **na mesma sessão** que a regra.

### O reparo

`scripts/corrigir_data_folga_s339.py`, ensaio por padrão. Corrigiu as **8 linhas** do
Ctrl Alt Green e registrou cada uma em `correcoes`. A prova de que a data certa é o dia da
captura, e não um palpite: a linha entrou no banco **já resolvida**, e bilhete só resolve
depois de o evento acabar — logo o evento é anterior à captura.

Quatro travas, todas fail-closed: só linha **com código** (sem código a `data` entra na
assinatura), só onde a data é posterior ao dia da captura, pula bilhete com correção humana
em `data`, e escopo explícito obrigatório (`--dono` + `--tipster`).

O UPSERT congela `data` em linha resolvida, então **recapturar não conserta** o que já está
gravado. Foi por isso que precisou de script.

### O que ficou aberto, e o próximo passo

**Medido depois do reparo:** o MTD do Ctrl Alt Green fechou em **+R$ 35,02** com 137 apostas,
que são exatamente as 129 da tela mais as 8 recuperadas. O delta previsto e o medido batem.

1. **`CLAUDE.md` estourou o teto** (65,4 contra 65). Não há mais duplicação para mover, e isso
   foi medido: zero frases longas repetidas entre ele e o `CASOS.md`. Fechar significa escolher
   qual regra sai, e é curadoria do Feca. → `BACKLOG.md 1.6`, que já traz o candidato
   (`## Convenções de output`, espelho declarado do `MASTER_OUTPUT`).
2. **Sobraram 21 linhas arquivadas**, já resolvidas, ainda datadas no futuro, de outros
   tipsters (Coxadoido, Fatuch, Perereca NFL, MarcoF1 e outros). O script filtra
   `archived = FALSE` e o escopo aprovado foi um tipster só. → `BACKLOG.md 1.8`.
   **Próximo passo:** rodar o ensaio com o escopo que o Feca autorizar.

> Cuidado ao ler o item 2: das 43 arquivadas com data no futuro, 22 estão ABERTAS e são
> legítimas — aposta aberta em evento de amanhã tem data futura por direito. Só as 21
> **resolvidas** é que são impossíveis.

---

_Anterior: 2026-09-09 (sessao 339: **o mes do Ctrl Alt Green fechava negativo porque a captura datava 8 vitorias em AMANHA.** Relato do Feca as 22:50 de 09/09, com duas perguntas que eram o MESMO defeito: "o resultado nao parece atualizado" e "por que voce finalizou apostas com 10/09?". As 8 linhas estavam no banco, todas `W`, somando **+R$ 928,00** — mas datadas de **10/09**, um dia que ainda nao tinha chegado. O MTD recorta `[1o do mes, hoje]` (`filters.js`, `st.dt = today`), entao bilhete datado de amanha cai fora da conta do mes: com elas dentro o mes vai de **-R$ 892,87 para +R$ 35,02** (medido no banco DEPOIS do reparo: 137 apostas, exatamente as 129 da tela mais as 8), ou seja **o filtro trocava o SINAL do resultado**. **A causa:** `_dataFimB3` somava ao kickoff uma "folga de encerramento" por esporte (`_OFF_B3`: 2,5 h em basquete, 3 h em tenis) para estimar a liquidacao. eBasket chega da bet365 como `CL=18` — Basquete, porque a casa nao separa os dois; quem separa e o `_e_ebasket` do `app/tradutor.py`, pelo handle do gamer nos dois lados — e levava **2,5 h de folga num jogo que dura ~4 minutos**. **A assinatura, medida:** as 8 foram capturadas entre 22:30 e 22:40 e as 8 ganharam data +1; nenhum dos outros 397 eBasket da base, fora dessa faixa de horario, foi deslocado. **A escala:** todo esporte tinha folga, entao havia uma janela diaria de ~21h a meia-noite. Piso medido (data = dia da captura + 1, capturado depois das 21h): **188 linhas** da Bet365 (73 Multiplos, 54 Futebol, 37 Badminton, 8 Basquete, 8 eBasket, 5 Tenis, 2 Dardos, 1 E-Sports) — e e PISO, porque quem foi capturado no lote da manha seguinte carrega o mesmo deslocamento e o banco nao guarda o kickoff para conferir. **Por que sobreviveu tanto tempo:** o efeito no KPI se desfaz sozinho (amanha 10/09 entra no MTD), so o DIA errado fica — defeito que se apaga da tela toda madrugada nao vira reclamacao, vira desconfianca difusa. **Decisao do Feca: `Data = kickoff`, para todos os esportes** — e o que a tela da bet365 mostra, o que as outras casas gravam e a unica data que o payload tem. A conversao UK->Brasilia NAO e a folga e continua obrigatoria (hora de parede de Londres). O rotulo do bloco virou `Data (evento):`, que ja era o das outras casas de API. **Gate novo** (bloco 9 do `extensor/harness/casos/bet365.mjs`), **provado por 5 mutacoes** — e a 3a ESCAPOU na primeira rodada: fixar `ukToBr = 4` deixava tudo verde porque nos casos escolhidos a diferenca entre UK-3 e UK-4 caia dentro do MESMO dia. O horario de verao britanico so troca o dia na faixa **03:00-04:00 UK**, entao foram precisos um caso em janeiro e outro em julho, ambos as 03:30, para prender o erro nos dois sentidos. **Reparo aplicado:** `scripts/corrigir_data_folga_s339.py` (ensaio por padrao) corrigiu as 8 linhas do Ctrl Alt Green e registrou cada uma em `correcoes`; a prova de que a data certa e o dia da captura e que a linha entrou no banco **ja resolvida**, e bilhete so resolve depois de o evento acabar. Harness 27 casos / 436 bilhetes verde. **Fica aberto (BACKLOG 1.6 e 1.8):** o `CLAUDE.md` ESTOUROU o teto (65,4 contra 65) e nao ha mais duplicacao para mover — qual regra sai e decisao do Feca; e sobraram **21 linhas ARQUIVADAS** ja resolvidas com data no futuro, de outros tipsters, que o reparo nao tocou porque filtra `archived = FALSE` e o escopo aprovado foi um tipster so. Outra sessao rodou em PARALELO nesta noite.)

---

## Sessão 336 — a barreira de recaptura, Fase 0

### A barreira de recaptura: Fase 0 no ar, medindo sem filtrar

O plano inteiro está em
[`docs/PLANO_BARREIRA_RECAPTURA.md`](../PLANO_BARREIRA_RECAPTURA.md). Ele nasceu de uma
pergunta do Feca que virou medição.

**O problema, medido:** toda captura vai inteira para a IA, e a dedup só acontece depois,
no `upsert`. Dos 15.318 blocos com código que passaram pela IA em 13 dias, **4.975
(32,5%) eram releitura de bloco byte a byte idêntico**. Na Bet365, 39,9%.

| | Blocos | % |
|---|---|---|
| Primeira leitura | 8.753 | 57,1% |
| **Releitura IDÊNTICA** | **4.975** | **32,5%** |
| Releitura de bilhete que mudou | 1.590 | 10,4% |

### Por que hash do bloco, e não (código, resultado)

A proposta original era conferir ID e resultado. Medida contra o hash do bloco inteiro,
as duas decidem igual em **97,7%** dos casos. Nos 2,3% restantes o bloco mudou com o
`Status:` igual, e a chave por rótulo pularia.

Mas o argumento que decide é outro: **o texto de status não é fonte confiável de estado.**
`_resultadoB3` escreve `Ganho → W` para qualquer retorno maior que a stake, meia vitória
inclusive. Chave que lê rótulo herda esse defeito; chave que compara bytes não tem o que
herdar. É o mesmo princípio do "o rótulo não é a prova, o número é".

E liquidar não mexe só no status. Caso real da Novibet: a odd vai de `4,59` (potencial)
para `2,89` (`Retorno ÷ Stake`) na mesma leitura.

### O ganho, e o que ele NÃO é

Simulação lote a lote, com modelo calibrado nos agregados de `uso_tokens` e **validado
contra a conta real: erro de +4,5%**.

| | Hoje | Pós-barreira |
|---|---|---|
| Conta de API | US$ 391/mês | **US$ 281/mês** |
| Custo por bilhete | R$ 0,092 | **R$ 0,065** |

**Velocidade quase não muda, e isso está escrito no plano de propósito.** A mediana fica
em 30,5s: os pedaços já correm em paralelo, então o relógio é o tempo de UM pedaço vezes o
número de ondas, e uma extração de 20 bilhetes vira 4 pedaços antes e depois. Só o p99 cai
43,7%. O ganho real é a extração que fica **vazia** (30s viram menos de 1), que hoje seria
2,3% delas — número subestimado, porque reflete o hábito de quem paga caro para
recapturar.

### A Fase 0 não filtra nada, e é para isso que ela existe

Tabela `bloco_visto`, gravação do hash no `done` da extração, e um log dizendo quantos
blocos **seriam** pulados. Serve para conferir em produção o número da simulação **antes**
de qualquer byte deixar de ser processado.

### As quatro costuras da Fase 1, todas silenciosas se erradas

Estão no `§6` do plano. Nenhuma dá erro; todas dão dado faltando em silêncio.
`conferir_cobertura` precisa saber do filtro (senão acusa perda que não houve);
`_reconciliar_orfas` precisa ver **todos** os blocos, não só os filtrados (senão uma órfã
perde a adoção e vira fantasma, o caso do Falkirk); bilhete sem código não passa pela
barreira; e lote vazio é sucesso, não erro.

### O custo remedido por usuário e por casa: existe um driver único

O custo por bilhete é quase inteiramente função de **bilhetes por chamada**, porque o
manual de 48k tokens é relido a cada pedaço.

| | R$/bilhete | Bilhetes por chamada |
|---|---|---|
| perereca | 0,037 | 55,9 |
| Feca | 0,102 | 12,2 |
| Marques19981 | **0,414** | 2,4 |

**E a Bet365 não é cara, ela é grande:** R$ 0,080 por bilhete, **abaixo** da média de
R$ 0,092 e a mais barata entre as casas de volume. É 42% da conta por volume, não por
ineficiência. A cara é a KTO, R$ 0,429 com 1,7 bilhete por chamada.

> Isso corrige a leitura do `ESTUDO_PRECIFICACAO §1.3`, que listava a Bet365 como o topo
> do custo sem separar volume de eficiência.

---

_Anterior: 2026-09-09 (sessao 337: **Blaze na captura automatica — 3a casa BetBy, sem uma linha de inject nova, e um defeito de odd que ela expos nas OUTRAS duas.** O espelho foi provado ANTES de escrever codigo e **sem login**: `/pt/sports` carrega `blaze.sptpub.com/bt-renderer` e o trafego sai em `api-31-sp-c7818b61-584` — **mesmo cluster e mesmo hash de operador da Jonbet**. Reusa `jb_inject.js`, `formatTicketJB` e `roboJBPassive`; mudou o ramo do `iniciarRobo`, o autodiagnostico e os 12 registros. **A varredura ao vivo deu 165 bilhetes** (`status` vazio, 5 cards lidos verbatim) e trouxe quatro achados que o espelho nao dispensava. (1) **A casa IGNORA o `limit` pedido**: pedi 100 e vieram 21 por pagina, oito paginas — quem avanca o `skip` pelo que PEDIU pula 79 por pagina, e o loop so nao quebra porque avanca pelo que VOLTOU. (2) **`total_k` zerou em 86 de 86 perdidas**, a armadilha conhecida da familia. (3) **A NOVA: em 4 dessas 86 o `k` TAMBEM vem zero** e a odd so existe dentro da selecao — **e o card deixa a linha "Total de odds" VAZIA**, ou seja a casa tambem nao tem o numero e nao escreve zero nenhum. Parar no `k` gravaria `0` numa coluna Odd, que e a familia do "zero nao e ausencia": passa em toda checagem de forma porque tem cara de conta feita, e num bilhete GANHO faria `stake x (0-1)` virar -1u. **O `_oddDeclJB` ganhou um terceiro degrau** (`total_k` -> `k` -> produto das selecoes -> `null`, nunca 0) e **conserta as tres casas de uma vez**. (4) `refund`/`canceled` achatam a odd para **1** — e ali o `1` e a VERDADE da tela, entao o degrau novo so pode disparar com os dois campos zerados; o caso trava os DOIS lados. **Gates:** harness 27 casos / 436 bilhetes verde, `audit_sharpenup` sem FAIL, `audit_casas` limpo (**e ele pegou uma categoria que eu inventei** — `Placar Exato` nao existe no MASTER; virou `Outros` mais um item de feedback, sem criar categoria por conta propria), e **mutacao provada nos dois sentidos**: o gate nasceu VERMELHO no bilhete certo e, com o produto vencendo sempre, acende 7 falhas, 2 delas nos `V`. A mesma mutacao passa **inocua** na Jonbet e na Betboom — espelho compartilha o conserto, nao compartilha a prova. **NAO coberto, medido e declarado no cabecalho do caso:** a conta nao tinha aposta ABERTA, cashout, boost, freebet nem sistema (`combinations` vazio em 165 de 165), e 3 dos 8 esperados vieram do corpo da resposta porque os cards de marco estavam ~100 posicoes abaixo e o filtro "Personalizado" da casa travou. **Descoberta de lado:** o BetBy da Blaze renderiza dentro de um **shadow root** — `document.body.innerText` traz 2,9 KB de casca e zero bilhete; casa assim nunca pode ter fallback de texto, porque o robo generico nao falha, ele manda a casca para a IA. **Os dois registros de `app/main.py` foram levados pelo commit da s336**, que estava com o arquivo — o caso 8 de novo, registrado e nao reescrito. Falta a validacao ao vivo, que so o operador faz. A s336 rodou em PARALELO, noutra sessao.)

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


---

## Sessão 334 — o tradutor determinístico da Bet365, Fase 1

### O mapa da Bet365 cresceu, e a régua de aceite cresceu junto

A Fase 1 do tradutor já existia desde a s301. Esta sessão mediu o que ele cobre, achou o
buraco e fechou parte dele com evidência.

| | Antes | Depois |
|---|---|---|
| Cobertura | 66,6% | **70,7%** |
| Bateu tudo | 76,1% | **77,0%** |
| Divergência de descrição | 21,4% | **20,5%** |

### A régua que a medição obrigou a criar

Eu ia aceitar rótulo por **categoria estável** (maioria ≥ 95% do que a IA decidiu, com
≥ 5 casos). Dezessete passaram. Aplicando, a cobertura subiu para 73,5% e **a divergência
de descrição subiu junto**, de 21,4% para 22,8%. Foi aí que a segunda régua apareceu:
**acertar a categoria não basta, a descrição tem de bater também.**

Dez rótulos saíram, e caem em duas famílias que pedem código, não linha de tabela:

- **Prop de SIM/NÃO.** A seleção é `Sim` e quem carrega a aposta é o rótulo.
  `Terminar com Pontos` sai daqui `Franco Colapinto - Sim` e a IA escreve
  `Franco Colapinto - Terminar com Pontos`. 52 casos, 98% de divergência.
- **Escopo de tempo.** `1º Tempo - Escanteios Asiáticos` sai `Over 3.5 Escanteios` e a IA
  escreve `Over 3.5 Escanteios 1º Tempo`. O período **não** é qualificador descartável
  como `Time da Casa -`: ele muda a aposta.

> Sintoma para reconhecer isto noutro gate: a régua mediu um campo e deixou o vizinho
> livre. É a mesma família do "gate que confere UM campo deixa os vizinhos livres" do
> `CLAUDE.md`, e aqui ela quase gravou descrição errada em silêncio em dez rótulos.

### A ordem do corte `- N Opções` é load-bearing

`- 2 Opções` e `- 3 Opções` contam as **saídas** do mercado (com ou sem o empate) e nunca
mudam a categoria, então cortar o sufixo resolve `Escanteios - 2 Opções` pela entrada
`escanteios`. Mas o corte é a **última** tentativa, nunca a primeira: `Total - 2 Opções`
está no mapa por inteiro, e cortar antes deixaria a chave em `total`, que não existe,
derrubando 498 blocos de uma vez. Há teste de mutação para os dois sentidos.

### O que a triagem dos 20% revelou

Quase nada é o tradutor errando. Das 1.376 divergências de descrição: **657 (47,7%)** são
nome de time localizado (`USA (W)` contra `EUA (F)`, limitação declarada no cabeçalho do
módulo), **538 (39,1%)** são notação de número e **81 (5,9%)** são a IA escrevendo
`Mais de` onde o MASTER manda `Over`.

Das 538, **520 (96,7%) são notação, não valor**: o MASTER mostra `Over 2.5 Gols` com ponto
e **não diz nada sobre linha partida**. É ali que a IA improvisa, escrevendo o mesmo caso
de três jeitos (`2,5/3,0`, `4,25`, `3.25`). Buraco de MASTER, não defeito de tradutor, e
virou decisão no [`BACKLOG §3.8`](../../BACKLOG.md).

### A Betano espera, e o motivo é amostra

Ela usa 686 rótulos contra 228 da Bet365 porque **embute nome próprio no rótulo**
(`Josh Coburn Total de chutes`, `Coritiba Total de Cartões`). Normalizando por sufixo eles
colapsam 60%, de 686 para 271, o que resolve o vocabulário. O que não resolve é a amostra:
ela tem **552 bilhetes de uma seleção contra 7.779 da Bet365**, porque é dominada por
`Criar Aposta` e múltipla, onde a categoria é estrutural e não diz nada sobre o rótulo.


_Anterior: 2026-09-09 (sessao 335: **tres casas novas no SharpenUp, num motor novo: Rogue.** Betao, R7 e 7Games sao espelho de verdade, servido do PROPRIO dominio da casa em `/api/sportsbook/rogue/...`, como a Novibet. Nao e Altenar, nao e BetBy, nao e Kambi, nao e BetConstruct. Um `rg_inject.js` e um `formatTicketRG` servem as tres, e a irmandade foi MEDIDA antes de escrever codigo (mesma stack Next.js, mesmo conjunto de hosts, mesmo mapa de endpoints extraido dos bundles das tres). **O contrato:** `GET /v1/betsreporting/purchases?status=all&take=<1..100>&skip=<n>&fromDate&toDate` com `authorization: Bearer`, devolvendo `{Purchases, PurchasesCount}`; `take` tem teto de 100 e a casa DIZ o limite (`ErrorCode 2003`) em vez de truncar calada. **A semantica saiu do DINHEIRO, nao do rotulo** (a API manda enum numerico puro), provada em 27 de 27 bilhetes: `BetStatusId` 0 com saldo 0 e sem `Result` e aberta, 1 e L, 2 com `saldo = stake x odd` e W, 4 com `saldo = stake` exato e V. **A armadilha central e o `Gain`:** ele e o retorno POTENCIAL e vale `stake x odd` em 27/27, INCLUSIVE em perdida e em aberta; o realizado e `CurrentBetBalance`. Quem le o campo obvio marca toda perda como ganho, que e o `totalWin` da VaideBet (s210) com o terceiro nome. **Dois achados mudaram o codigo:** (1) a TELA E ESTREITA, abre em `Ult. 24 horas` com `take=10` e no recon o filtro de 30 dias do Betao devolvia `PurchasesCount: 0` numa conta com 9 bilhetes, entao o replay alarga para 36 meses e pede `status=all`; (2) **o Bearer EXPIRA**, medido testando o inject contra a casa real (token de ~1h responde 401), e guardar so a PRIMEIRA requisicao fazia o contexto envelhecer junto com a aba. **A gemea `r7.bet` foi unificada ANTES do registro** (a base decidiu: 40 bilhetes de 2 donos contra 1), senao o bilhete do Jaao26 ficaria numa casa que a conta dele nao enxerga, o defeito da s249. **O gate pegou um defeito meu antes de subir:** `_casaConectavel()` normalizava espaco mas nao ACENTO, e a chave e `BETAO` enquanto o display e `Betao` com til, entao o botao Conectar nasceria desabilitado (o bug da s191 na terceira encarnacao). **Gates:** harness 26 casos / 428 bilhetes, `audit_sharpenup` 31 casas sem FAIL nem WARN, `audit_casas` limpo, check-tokens verde, 772 passed, e **mutacao 12 de 12 detectadas** (as duas que escaparam de primeira eram buraco de TESTE, nao de codigo, e viraram caso proprio). **NAO coberto, medido:** as 27 apostas sao todas simples, sem multipla, sistema, cashout, freebet nem meia-liquidacao. Falta a Fase 7, que so o operador faz.)

---

## Blocos completos — sessões 333 → 317

> Blocos movidos INTACTOS do `STATUS.md` (Lote B da faxina de documentação). O STATUS passou
> a guardar só o estado atual e as 3 últimas sessões, como o ritual `/encerrar` já mandava.

## Sessão 333 — Contas e Parceiros v2, Fases 7 e 8

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

Os dois `Banca total` divergentes ([`BACKLOG §4`](../../BACKLOG.md#4-dívida-técnica-medida)) —
medido, não corrigido, porque o conserto muda o significado de um dos dois e essa
escolha é do Feca.

---

## Sessão 337 — a Blaze na captura

### Blaze: a terceira casa BetBy, e o degrau de odd que ela expôs nas outras duas

Detalhes em [`casas/CASA_BLAZE.md`](../../casas/CASA_BLAZE.md). O espelho foi **provado antes de
escrever código e sem login**: `/pt/sports` carrega `blaze.sptpub.com/bt-renderer`, e o
tráfego sai em `api-31-sp-c7818b61-584` — **mesmo cluster e mesmo hash de operador da
Jonbet**. Zero arquivo de captura novo: reusa `jb_inject.js`, `formatTicketJB` e
`roboJBPassive`.

Varredura ao vivo de **165 bilhetes** (`status` vazio), com 5 cards lidos verbatim na tela.

### O achado que muda código: a odd que a casa NÃO tem

`total_k` veio `"0"` em **86 de 86 perdidas** — a armadilha conhecida da família. A nova é
que **em 4 dessas 86 o `k` também vem zero**, e a odd só existe dentro da seleção.

E o card concorda com a API: a linha **"Total de odds" aparece VAZIA**. A casa também não
tem o número, e não escreve zero nenhum.

Parar no `k` gravaria `0` numa coluna Odd. É a família do *"zero não é ausência"*: o `0`
passa em toda checagem de forma porque tem cara de conta feita — e num bilhete **ganho**
faria `stake × (0 − 1)` virar `−1u`. O `_oddDeclJB` ganhou um terceiro degrau:

```
total_k, se ≠ 0  →  k, se ≠ 0  →  produto das seleções, se todas > 0  →  null (nunca 0)
```

**Conserta as três casas de uma vez.** E o degrau só pode disparar com os dois campos
zerados: em `refund`/`canceled` a casa achata a odd para **1** e ali o `1` é a verdade da
tela — o produto das pernas (2,5 · 1,5) seria invenção nossa por cima do card. O caso do
harness trava os **dois** lados.

### O que a paginação ensinou

Pedi `limit=100` e a Blaze devolveu **21 por página**, oito páginas, `count` constante em
165. A casa **ignora o `limit` pedido**. Quem avança o `skip` pelo que pediu pula 79
bilhetes por página; o loop do `jb_inject` só não quebra porque avança pelo tamanho que
**voltou**.

### Gates, e as duas coisas que eles pegaram

| Gate | Resultado |
|---|---|
| `node extensor/harness/run.mjs` | verde — 27 casos, **436 bilhetes** |
| `python tools/audit_sharpenup.py` | sem FAIL |
| `python tools/audit_casas.py` | limpo |
| `pytest tests/` | 773 passed (as falhas restantes são da s336, em curso noutra sessão) |

O `audit_casas` **pegou uma categoria que eu inventei**: `Placar Exato` não existe no
`MASTER_APOSTAS §3`. Virou `Outros ⚠️` mais um item de feedback no rodapé do arquivo da
casa — criar categoria é decisão do Feca e arrasta a propagação inteira.

E a **mutação foi provada nos dois sentidos**: o gate nasceu **vermelho** no bilhete certo
e, com o produto vencendo sempre, acende 7 falhas — 2 delas exatamente nos `V`. A mesma
mutação passa **inócua** na Jonbet e na Betboom: espelho compartilha o conserto, não
compartilha a prova.

### O que NÃO está coberto (medido, e escrito no cabeçalho do caso)

A conta não tinha **aposta aberta**, **cashout**, **boost**, **freebet** nem **sistema**
(`combinations` vazio em 165 de 165). E 3 dos 8 valores esperados vieram do corpo da
resposta, não do card: os bilhetes de março estão ~100 posições abaixo na lista e o filtro
"Personalizado" da casa travou carregando nas duas tentativas.

**Descoberta de lado:** o BetBy da Blaze renderiza dentro de um **shadow root** —
`document.body.innerText` traz 2,9 KB de casca e nenhum bilhete. Casa assim nunca pode ter
fallback de texto: o robô genérico não falharia, ele mandaria a casca para a IA.

**Pendente:** a validação ao vivo (recarregar a extensão, Ctrl+Shift+R na aba da Blaze e
capturar), que só o operador faz.

### Duas sessões, um index: os registros de `app/main.py` foram levados pela s336

Aconteceu de novo o [caso 8](../CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026),
e desta vez a favor: os dois registros da Blaze em `app/main.py` (`_CASA_DISPLAY` e
`_CASAS_MARCADOR_CODIGO`) entraram no commit `2143c06` da s336, que estava com o arquivo
para a Fase 1 da barreira. **Histórico já enviado não se reescreve** — fica registrado aqui
e segue. O resto dos 12 pontos veio no commit desta sessão.

Vale a lição inversa da regra: quando o arquivo é o MESMO, `git add` por nome não separa
nada. Antes de editar `main.py` com outra sessão aberta, o barato é combinar quem leva.

---

## Sessão 332 — a remedição do custo

### A remedição do custo: as correções acertaram o alvo, e o alvo era o outro

O [`ESTUDO_PRECIFICACAO_2026 §7`](../ESTUDO_PRECIFICACAO_2026.md#7-revisão-de-08092026-s332--o-que-aconteceu-depois-de-a-e-c)
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

Está tudo no [`BACKLOG.md`](../../BACKLOG.md): a decisão de escopo do tradutor (`§3.7`), o
rótulo errado do `/uso/tokens` (`§4`, de pé desde a s295), a remedição em 30 dias e a
infra do Railway, que segue não medida.

---

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
- **O resto está no [`BACKLOG.md`](../../BACKLOG.md)**, agora em um lugar só.

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

> **Parte 2 (07/09): o tenant do bot entrou em produção.** O que está escrito
> abaixo é o import; o resto da sessão está resumido aqui e mora no
> `sharpen-bot` (commits `5cd8c6b`, `eb1bca4`, `d283ed8`, `36b29ce`).

### O 8º tenant do bot, no ar

`src/perfis/grego.js` forkado do `sohprops`, bloco `GV_*`, linha no registro
`PERFIS` (a que faltando derruba TODOS em crash-loop, s316). Boot com **7
tenants**, suíte verde, **12 mutações aplicadas e 10 pegas** — as 2 inócuas
estão escritas no teste.

Cinco diferenças do irmão, todas medidas no export do canal: a stake é `%` e
**não abre a linha** (1.043 de 1.305 no meio/fim — ancorar em `^` perderia 80%
das apostas), o que obrigou a reconhecer a linha por CONTER stake e a criar
guardas, porque o `%` tem outros três papéis (`2.02 + 25% = 2,27@`, `só vale com
25% odd final`, `ROI: 15.28%`); `⌛` = aberta; casa por **apelido** (`mgm`,
`365`, `Super`, `Betan` devolvem null no `casas.js`); **34% das legendas cegas**;
e `Quadra`.

### O bloqueio não era código: era o bot ser MEMBRO do grupo

`getMe` diz `can_read_all_group_messages: false` — privacy mode ligado. Bot com
privacy, como membro comum, **recebe só comandos**: as mensagens com print não
chegam, e o tenant nasceria **surdo, sem erro nenhum**. Medido, não deduzido: os
6 apoios que funcionam têm o bot como `administrator`; o do Grego era o único
fora do padrão. Promovido, o log provou a virada
(`[apoio:grego] msg — foto=false texto=false`).

### A coluna `Tipster` passou a sair por AUTOR

O canal tem DOIS admins, e o **Sign messages** está ligado: cada post carrega
quem escreveu (`grego` 958 · `ricklxrd` 110). Isso tornou a atribuição do atraso
**determinística** — 148 `Grego` e 48 `Rick`, sem heurística.

Daqui pra frente quem resolve é o núcleo, por `msg.from.id` → `XX_TIPSTER_NOMES`
(genérico; vazio = comportamento de sempre; **inerte em canal**, onde não existe
`msg.from`). Autor fora do mapa cai na marca **com aviso dizendo o id**. Os dois
ids foram provados contra o grupo por `getChatMember`, e o `first_name` de cada
um é **exatamente a assinatura do canal** — a mesma pessoa chega pelo mesmo nome
pelos dois caminhos, e por isso as duas metades da coluna se somam.

**As 956 do tracker ficam sob a marca**, e é decisão com número atrás: o join
por (título, stake, data) fecha em **704 de 956 (73,6%), zero ambíguas**. Um
quarto sem autor faria um ROI "por admin" **parecer completo sem ser**.

### Dois defeitos que apareceram no uso

- **`/anular` dizia "3 apostas removidas" tendo removido 0.** O aviso repetia
  `ids.length` — o que foi MANDADO — e ignorava `resp.deletados`. Mesma família
  do `rejeitados` do `/salvar`: contagem devolvida pela API é dado, não enfeite.
  Hoje acusa (`removeu 0 de 3`), e resposta sem número vira `?`, nunca `0`.
- **Modo de teste desvia o POST, não o planilhamento.** Os dois bilhetes de
  teste entraram na base de verdade. Só não sobrescreveram o histórico porque o
  bot põe sufixo `-S<n>` quando há N apostas: `GV202609-1-S1` ≠ `GV202609-1`.
  **Teste de UMA aposta só, na mesma casa, teria batido a assinatura** — é a
  colisão que o `/contador` existe para evitar, e ela quase aconteceu.

### O post, como o tipster pediu

`🧠 <Nome>` na última linha, depois do total — o cabeçalho só diz a marca, igual
para os dois. É o **mesmo valor** que vai para a coluna `Tipster`: o núcleo
resolve uma vez e entrega nos dois caminhos, então canal e planilha não podem
divergir sobre de quem é a aposta. Autor desconhecido não imprime linha nenhuma
— repetir a marca ali seria fingir resposta.

E o **P/L saiu de `u` para `%`**, a régua que eles usam. Derivado do `plFmt`
compartilhado, não copiado: o sinal continua sendo **U+2212**, e a mutação que
copia o formatador perde exatamente isso.

### Estado final

    base gregozxrd   1.152 · Grego Tips - VIP 956 · Grego 148 · Rick 48
    série            GV202609-228 · contador 228 → próximo #229
    bot              publicando no canal (GV_MODO_TESTE=0), 2 autores mapeados

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

### Próximo passo (aprovado em conceito, texto NÃO aprovado)

Explicar a régua NA TELA. O Feca pediu ("vamos explicar melhor como o custo se aplica
ao filtro") e a redação ficou esperando o ok dele. Três peças, todas com componente
que já existe nesta tela — nenhum CSS novo, nenhum formatador novo:

1. um **ⓘ** no card Custo de Contas (`_mkTipAnchor`, o mesmo do Cenário Atual):
   fórmula `custo × contas vivas no período`; texto "Custo de aquisição de cada conta
   que EXISTIA no período — da compra até o arquivamento (ou a última aposta). Não é
   rateado: conta que viveu um dia do recorte custa inteiro."; selo "não soma entre
   períodos";
2. uma **`.nota-escopo`** sob o Andar 1, só com período filtrado: "Custo de Contas e de
   Tipsters não são proporcionais ao período — mostram o que existia nele, inteiro. Só
   o P/L acompanha o recorte." Com "Tudo" não aparece;
3. legenda `N contas no período` → `N contas **vivas** no período`.

A regra em si já está no canônico (`CLAUDE.md`, seção "Custo de aquisição tem JANELA DE
VIDA"), escrita no encerramento — não estava lá quando a mudança subiu.

### Anotado, não aberto

O **Custo de Tipsters** segue com a régua antiga: cobra o mês inteiro e ignora todo
filtro, inclusive o de tipster. Os dois cards ficam lado a lado medindo com réguas
diferentes. Não foi tocado nesta sessão, de propósito.

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


---

---

## Cadeia `_Anterior_` — sessões 338 → 310

_Anterior: 2026-09-09 (sessao 338: **a Blaze duplicando bilhete, e a causa nao era a Blaze: era a PROCEDENCIA do codigo.** Relato do Jonathan: "a blaze ta puxando bet duplicada, tinha feito isso ontem com prints e agora com a extensao". Medido no banco ANTES de tocar em codigo: o bilhete do Susanto (31/08) estava **5 vezes** na base dele, com **5 codigos diferentes**, um deles gravado literalmente como `270625314492244...` e outros dois com espaco no meio do numero. **Nao e defeito da captura: a Blaze so entrou na captura nesta mesma noite** (commit `d3f2233`, 19:24), entao 100% do que estava no banco veio de PRINT. O discriminador foi o `uso_tokens.n_itens`, que conta imagens + blocos de texto: toda extracao de Blaze anterior tem `n_itens` de imagem, e so a de 20:43 e texto. **O id do BetBy tem 19 digitos e a IA lendo o card erra quase sempre:** 53 dos 55 codigos de Blaze no banco tem comprimento errado (17, 18, 20, 21). Para comparar, Betboom (77 de 77) e Jonbet (18 de 18), que so entram por captura, acertam os 19 digitos em 100%. **Como o codigo entra na assinatura, cada leitura vira um bilhete novo** e o pre-dedup por codigo nunca casa: ao ligar a extensao, o historico inteiro da casa duplicaria. Nao e so o Jonathan (germano tem 20 linhas assim, Jaao26 uma). **Tres frentes.** (1) A coluna `codigo_ocr` carrega a PROCEDENCIA do codigo, decidida no servidor (o `/extrair` e quem sabe se o lote tinha imagem) e transportada pelo front ate o `/salvar`. A formula do ON CONFLICT e um **AND das duas pontas**, entao a confianca so DESCE: basta uma leitura confiavel para o codigo deixar de ser suspeito, e nenhum print o rebaixa de volta. O backfill da Blaze e **deterministico, nao heuristico**: toda linha criada antes do deploy da captura veio de print porque nao existia outro caminho. (2) A **Migracao B'** do UPSERT adota essa linha quando o mesmo bilhete volta pela captura com o codigo verdadeiro, em vez de inserir a sexta. Duas travas que a Migracao B nao tem, porque aqui o candidato CARREGA um codigo e adotar o errado nao duplica, **sequestra** a identidade de outro bilhete: candidato UNICO, e o indice so e montado quando o lote que chega e confiavel (print nao adota print). (3) `scripts/reparar_duplicatas_codigo_ocr.py` une o que ja esta duplicado: ensaio por padrao, escolha pelo valor **MODAL** de stake e odd (com N leituras do mesmo card, a moda e a melhor estimativa que o banco tem, e isso importa porque o UPSERT congela stake/odd em linha resolvida), e snapshot em `lixeira_bilhetes` pelo `DELETE ... RETURNING to_jsonb`, uma operacao so. **Gates:** 789 passed / 36 skipped, **7 de 7 mutacoes detectadas** (`scripts/mutar_codigo_ocr.py`), 6 testes de ponta a ponta no harness de DB, `check-tokens` e `audit_sharpenup` verdes.)


_Anterior: 2026-09-09 (sessao 333: **handoff `Contas e Parceiros v2` — Fases 7 e 8 aplicadas.** A Fase 7 e distribuicao por LARGURA e a Fase 8 e a zona de Fornecedores. **O vao de ~800px no monitor de 32" nao era margem errada, era COLUNA SOBRANDO:** a folga vivia numa faixa antes das acoes, entao nome/status/caixa ficavam ancorados a esquerda e os botoes na borda direita, com nada no meio. Agora a unica coluna elastica e a PRIMEIRA (o nome, que sempre tem o que mostrar) e a folga vira INFORMACAO: duas faixas nascem em 0px e abrem por degrau — `Fornecedor` e `Ultima captura`. **Dois containers, cada um medindo o que governa:** o `pc` mede a AREA DO APP e decide quantas zonas cabem lado a lado; o `acct` mede a TABELA e decide quantas colunas cabem nela. Um container so nao resolveria: o mesmo monitor da larguras diferentes a tabela conforme o numero de zonas ao lado, e foi por isso que a coluna de fornecedor abriu em 1366 (log embaixo, tabela inteira) e nao em 1440 (log ao lado). **Os cortes do handoff (1500/1900/170/176) NAO foram copiados — foram MEDIDOS, e tres deles nao fechavam:** as acoes medem 208px e a trilha proposta era 176; a linha da CASA precisa de 220px de nome (favicon + `Esportes da Sorte` + pilula de contagem) e a proposta era 170; e com os cortes de pagina em 1500/1900 a tabela caia abaixo do proprio piso em 1440, 1600 e 1920 — sem erro, porque `justify-content:flex-end` transborda para a ESQUERDA e isso some do `scrollWidth` (a armadilha da s331d). Os cortes agora saem da conta do conteudo: 842px de piso de tabela, 1094 / 1334 / 1738 / 2030 de area de app. **Fase 8 — a tela se chama Contas & Parceiros e nao dizia nada sobre FORNECEDOR.** Risco de fornecedor nao e risco de casa: casa que trava saque e burocracia, fornecedor que some e o dinheiro. Entrou a terceira zona (ordenada por caixa, com o proprio usuario como contraponto), o 4o KPI `Em contas de fornecedores`, o segmentado de fornecedor na barra da tabela e a linha de total no rodape, na MESMA grade das linhas. Nenhum dado novo: tudo e agregacao do `[Fornecedor]` que ja vive no nome da conta. **Estado novo `Parada ha N dias`, em CINZA:** conta ativa sem captura ha mais de 30 dias se disfarcava de `Conciliada` — estava limpa porque ninguem a usava. Cinza e nao ambar de proposito: abandono nao e pendencia e nao pode competir com pendencia de verdade. O unico campo novo e o `ultima_captura` do `/caixa/visao`, que e o maior `criado_em` dos bilhetes da conta — e o rotulo diz **captura**, nao "extracao", porque extracao que nao achou bilhete novo nao aparece ali. **Gates:** check-tokens verde, 767 passed / 30 skipped, o gate novo `tests/test_contas_status.py` com **8 mutacoes, 8 detectadas**, e `scripts/demo/medir_contas.mjs` medindo a tela em 1366/1440/1600/1920/2560 (transbordo 0 em todas, zero tag na casa, 29 chips TOTAL, nenhuma abreviacao). **Achado medindo, NAO corrigido:** ha dois `Banca total` na mesma tela e eles divergem — o KPI soma toda conta ligada, a faixa da Concentracao soma so casas com `banca > 0`. Foi para o `BACKLOG §4`.)


_Anterior: 2026-09-07 (sessao 331 — **handoff v2 aplicado: `Contas e Parceiros v2`, 6 fases num commit so.** A tela deixa de ser tres colunas concorrendo e passa a ter QUATRO leituras: dinheiro no topo estreito · `Ultimas acoes` na lateral inteira comecando na MESMA linha dos KPIs · `Concentracao de caixa` ao lado da tabela de Contas. **O rail da casca saiu desta tela** — ele e o RAIO-X, que pertence a Extracao. **Concentracao substitui `Contas por casa`, que contava CONTAS:** contar conta nao diz risco nenhum, e 52 contas numa casa com R$ 0 desenhavam uma barra maior que 1 conta com metade da banca. Agora e rosca por `stroke-dasharray` sobre perimetro 100 (cada arco e literalmente "P por cento"), rampa FIXA de 8 tons — tom calculado do valor faria a MESMA casa mudar de cor entre duas aberturas, e a cor e a chave que liga rosca e lista. Clicar filtra a tabela; clicar de novo solta. **Pilulas de status** num helper unico, lista fechada, numero em `<b>`, com o estado NOVO `Aguardando tipster N` em AZUL: bilhete sem tipster e espera externa, nao erro, e antes ele somava com as apostas abertas num numero so — apagando a diferenca entre "eu resolvo" e "depende de alguem". **Tabela:** 4 trilhas, chip `TOTAL` na trilha da Caixa, `.acct-group` fechando o bloco, SEM traco/arvore, e os tres botoes de volta na linha. Sairam as colunas Duracao/Dias ativos/Apostas (descreviam ATIVIDADE; a tela responde "quanto tem e esta conciliado?"). **Duas armadilhas de largura, as duas invisiveis na leitura e medidas no headless:** (1) media query DENTRO do iframe le a largura do IFRAME, e a sidebar (~300px) fica fora dele — num monitor de 1440 a pagina tem 1120, e o breakpoint de 1180 do handoff disparava sempre, jogando o log para baixo em TODA largura; (2) com as trilhas em px cravado sobravam 130px para o nome em 1440 e "Esportes da Sorte" saia cortado — as tres viraram `minmax(min, alvo)` e cedem antes do NOME ceder. Conferido em 1366/1440/1600/1920/2560. **Gates:** check-tokens verde, 756 passed / 30 skipped, Escada em 3 criterios sem achado novo, fumaca no navegador (zero tag na casa, 29 chips TOTAL, sem arvore, filtro ligando e soltando) e a rosca provada com 12 casas sinteticas: 9 arcos somando exatamente 100.)


_Anterior: 2026-09-07 (sessao 329 — **a faxina de documentacao achou 14 regras que governavam o comportamento e nao estavam escritas.** Esse e o resultado, nao os KB. Quatro arquivos disputavam o papel de "onde o projeto esta" e tres descreviam o projeto de julho; a varredura da s261 ja tinha medido o custo disso ("a primeira pendencia que eu fui atacar ja estava feita desde 26/07"). Cinco lotes fechados. **F** — nasce o `BACKLOG.md` (70 KB), que absorve o §5 do STATUS VERBATIM: as 192 linhas nao-vazias conferidas uma a uma, zero perdida, com contraprova por canario. **B** — STATUS de 183 para 44 KB; as 1.157 linhas de antes reprocuradas uma a uma (483 ficaram, 491 foram para o HISTORICO, 183 para o BACKLOG, ZERO perdidas). **C** — HISTORICO de 1,21 MB vira indice de 3 KB + 6 particoes, com as 1.445 linhas conferidas. **D** — 16 docs + 11 anexos para `docs/arquivo/`, `docs/` cai de 43 para 27 vivos, 20 links consertados. **E** — CLAUDE.md de 68,3 para 62,7 KB e nasce o `docs/CASOS.md` (22,9 KB), que NAO e auto-carregado: a regra fica no CLAUDE, o bilhete/casa/valor/sessao vai para o CASOS. **O gate final de regras deu ZERO perdidas**: das 434 ancoras verificaveis, 384 seguem no CLAUDE e 57 migraram para o CASOS; dos 50 numeros que decidem comportamento, 36 ficaram e 11 migraram. 255 regras contadas item a item em 12 secoes. **E 14 regras foram ACRESCENTADAS** — o `git add` por nome, os tres 'os tetos travam crescimento', o trio de causas da Escada de Tinta, a inversao de hierarquia, o 'node --check e falso verde para tudo em template literal', e mais 7. Elas ja governavam o comportamento; so nao estavam escritas como regra. **Gate novo:** `tools/check_docs.py`, no CI, com 7 checagens todas provadas por mutacao — tetos de CLAUDE (65 KB), CASOS (60) e STATUS (50), forma do STATUS (<=3 blocos, <=2 _Anterior), copia em Backups por PREFIXO, link quebrado e ANCORA. Regra sem gate nao e cumprida neste repo: o invariante #4 estava escrito e claro, e Backups chegou a 551 pastas com 165 copias de STATUS/HISTORICO. **Reconciliacao da Auditoria Turbo:** os 78 achados MEDIO/BAIXO do mergulho de 20/07 NAO EXISTEM por escrito (o doc enumera 16 e o rodape diz "Deliverables uncommitted"); reconciliei os 139 do findings.json de 19/07 — 40 fechados, 68 abertos, 20 a confirmar na tela, 3 parciais e 3 que nao eram achado, um deles um placeholder de teste. **#129 medido e rebaixado:** a odd nao entra no calcular_pl em L/V e o risco de dedup deu ZERO de extracao em 528 multiplas sem codigo expostas; virou divida de documentacao. **Lote A ABERTO** — podar Backups (223 arquivos, 28,7 MB), com o zip para fora do repo ANTES de qualquer coisa apagada.)


_Anterior: 2026-09-06 (sessão 324 — **botão que não leva a lugar nenhum confunde mais que botão ausente.** O `Entrar com Telegram` saiu do `/login`: o fluxo não conclui e o relato de uso era gente apertando sem retorno. Só o BOTÃO saiu — backend, rotas e os 27 testes do login social seguem inteiros, e o teste que trava a remoção diz como desfazê-la. `temSocial` deixou de olhar `m.telegram` para o separador **ou** não acender sozinho. 2 mutações aplicadas e 2 detectadas; 717 passed. Causa raiz do clique morto segue ABERTA (suspeito: `/setdomain` do BotFather) — não medida, o pedido era tirar o botão. Antes, s323 — **filtrar um dia zerava o Custo de Contas com o parque inteiro em uso.** A régua velha lançava o custo de aquisição num ÚNICO dia — o da primeira aposta LIQUIDADA — e só o cobrava quando o intervalo das LINHAS filtradas continha aquele dia; recorte sem aposta zerava, e conta comprada e ainda não usada não existia no mapa (entrava nos R$ 3.100 da aba Custos e nunca no KPI). Agora o custo tem JANELA DE VIDA: `ini = menor(adquirida_em, 1ª aposta)`, `fim = maior(última aposta, arquivada_em)`, e todo período que CRUZA a janela cobra o custo cheio. Colunas novas `parceiros.adquirida_em` / `arquivada_em`, editável no modal. O escopo saiu das linhas e foi para o filtro: Casa e Operador recortam o custo, Esporte e Tipster não. ⚠️ A régua NÃO é aditiva e o preço foi aceito na mesa: o P/L Líquido de um dia carrega o custo cheio das contas vivas. 9 mutações aplicadas e 9 detectadas; 716 passed. Método: o vídeo do tester tinha ÁUDIO e a tela sozinha apontava para o alvo errado. Antes, s322 — mexer no multiselect invalida o recorte cacheado: o `_filterCache` só era zerado pelo `renderPage`, e a barra própria da Base Completa não passava por ele.)_

_Anterior: 2026-09-05 (sessão 321 — **gate que confere UM campo deixa os vizinhos livres: a odd só era reconferida como efeito colateral da stake, e o RETORNO do bloco foi gravado como ODD.** O Feca abriu com o caixa da `denisesampa01` não batendo e dois bilhetes absurdos: um `HL` num Player Props de F1 (meia derrota exige linha asiática partida) e um `Under 4.0 Gols [Loiske v TP-T]` com **odd 195,53**. Medido antes de tocar em código: `195,53 ÷ 99,00 = 1,9751`, a MESMA aposta noutra conta tinha odd `1,975`, e o bloco cru diz `Status: Ganho → W (retorno R$ 195,53)` com `Odd: 1,975` **duas linhas abaixo**. A IA copiou o retorno para a coluna Odd; P/L de **+R$ 19.258,47** onde o real era +R$ 96,53. **A raiz é de desenho:** desde a s311 a stake vem do bloco, mas a odd só era recalculada DENTRO do `if` que roda quando a stake diverge (`_odd_da_stake`) — stake certa + odd errada passava reto — e o `resultado` não tinha conferência nenhuma. **A prova é o RETORNO**, contra as cinco fórmulas do `calcular_pl` lidas ao contrário (`repository._veredito_do_retorno`), agora rodando SEMPRE que o bloco prova o retorno. **O rótulo do Status não serve de fonte:** `_resultadoB3` escreve `Ganho → W` para qualquer retorno maior que a stake, meia vitória inclusive — ler o texto reescreveria como W 14 bilhetes `HW` que estavam certos. **Varredura da sombra (5.316 blocos, 20 casas): 33 linhas com dinheiro errado, Δ −R$ 19.711,29** (Feca −19.796,51 · Gabriel +69,39 · Jonathan +15,83), corrigidas por `scripts/corrigir_resultado_odd_s321.py` (ensaio por padrão, snapshot que APENSA em `Backups/s321-odd-resultado-contra-bloco/`). O P/L da `denisesampa01` caiu de R$ 28.001,63 para **R$ 8.321,45** — ⚠️ a Caixa precisa ser RECONFERIDA, a conferência registrada não se recalcula sozinha. **Três armadilhas medidas, todas load-bearing:** (1) a Betfair mistura BR e EN no mesmo bloco (stake `300,00`, retorno `1,642.38`) e um parser BR lê 1,64 e destrói 5 odds certas → `_num_bloco` decide pelo ÚLTIMO separador, e **um separador só é sempre decimal** (a regra `3 dígitos = milhar` faz `1,775` virar 1775); (2) **correção humana manda** — 3 bilhetes Betano em que alguém inverteu `W→L` e `L→W` no mesmo minuto são PULADOS pelo script (o gate em extração NÃO tem essa trava, e `resultado` nunca foi congelado pelo UPSERT: recaptura desfaz a edição); (3) só se escreve onde o **dinheiro** muda — piso de R$ 1,00, senão a 'correção' troca `1,925` pela dízima `1,925087108`. **GATES:** `tests/test_odd_resultado_determinista.py` (17 testes, **5 mutações aplicadas e todas pegas** — 2 escaparam na 1ª rodada e o defeito era do teste, registrado no cabeçalho junto com a mutação INÓCUA do lookbehind `(?<!potencial )`), suíte inteira verde (**699**), e **replay do gate na sombra real**: reproduz sozinho as 33 correções do script e mexe em **3** dos 5.316 blocos — exatamente as 3 de edição humana, zero falso positivo. **Bug meu, achado pelo replay e registrado:** o script pulava em silêncio odd truncada com reticências (`1,45070184...`), porque só o `_num_or_none` do repo faz `.rstrip('.')` — 1 bilhete ficou de fora da 1ª aplicação e entrou na 2ª.)_

_Anterior:` que saíram do cabeçalho do `STATUS.md` no mesmo Lote B.
> Ficam aqui verbatim.
>
> Os de **s327** e **s325** não vieram para cá de propósito: eles resumem sessões cujo
> **bloco completo continua no `STATUS.md`**, logo abaixo do cabeçalho. Arquivar o resumo de
> um texto que segue vivo duas telas adiante é duplicar, não preservar — e eram 6,6 KB. Os
> parágrafos de **s324** e **s321** ficaram no STATUS, porque são as duas sessões mais
> recentes que deixaram de ter bloco próprio lá.

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

---


---

---

## Sessão 315 — separador em parser de valor TROCA o número

**Uma lista de separadores é pior que inútil num parser de valor: ela não perde o
número, ela o TROCA.** A legenda do Rogerin veio `2u/1u/0,5u` e o perfil devolveu
`[2u, 5u]` — a barra não estava na classe `[\s,;]`, então `1u` e `0,5u` não casavam
pelo começo, e a vírgula de `0,5u` casou. O bilhete #21 foi planilhado com **5u** na
2ª aposta. O resultado estava certo, o P/L fechava, a descrição era fiel: nenhuma
conferência de forma tinha como reprovar. Quem viu foi o Feca, olhando a tela.

Feito no `sharpen-bot` (`b235002`): o começo do número agora é definido por
**exclusão** — `(?<!\w)` aceita qualquer separador (barra, pipe, hífen, parêntese) e
`(?<!\d[.,])` impede o pedaço decimal de virar stake própria. A vírgula é separador
quando **não** vem depois de dígito; é isso que separa `2u,1u` de `0,25u`. O
`replace` das URLs, que era mutação inócua documentada, **virou load-bearing** (a
barra é o caractere mais comum de uma URL) e ganhou asserção própria. O aviso de
contagem divergente parou de dar o conselho de "faltou stake" quando **sobrou**:
sobra aponta print cortado, que foi o caso. Três mutações provam os testes.

Feito no Sharpen (`scripts/corrigir_bilhete_rogerin_21_s315.py`): `RG202609-21-S2`
de 5u para 1u e a `RG202609-21-S3` que nunca existiu (0,5u @11,00, **L**). Precisa
de script porque o UPSERT **congela** stake em linha resolvida — recapturar não
conserta. A 3ª aposta fecha a aritmética do print: `Retorno Total R$12,83` =
3,33 + 4,00 + **5,50**, com o modal da bet365 rolando atrás de um rodapé fixo; o
`L` é dedução fechada, porque "Mais de 1.5" perdeu. P/L do #21: −3,68u → −0,18u.

**Medido, e contraria o comentário do `index.js`: o Telegram NÃO devolve ao bot os
posts que ele mesmo faz num canal.** Tentei disparar `/atualizastake #21 2 1` pela
Bot API no apoio do Rogerin e a mensagem ficou lá, sem update nenhum (o guard
anti-eco `enviadasPeloBot` nem chega a ser consultado). Consequência prática:
**comando de bot em apoio-canal só existe se um humano digitar** — o post do canal
do #21 segue com 5u na 2ª aposta até alguém colar o comando no apoio.

**Anotado, não aberto:** (1) o post do canal e o registro do bot seguem sem a 3ª
aposta — não há comando que ACRESCENTE aposta a bilhete já publicado, e inventar um
por causa de um print cortado é caro demais; (2) a mensagem `/atualizastake #21 2 1`
(id 135) continua no apoio do Rogerin, acima do recado — apagar foi barrado aqui;
(3) a lição do separador está no comentário do perfil e nos testes, não no
`CLAUDE.md` — promovê-la a regra escrita é decisão do Feca.

_Anterior: 2026-09-01 (sessão 310 — **"O indicar tipster não funcionou bem" eram DUAS causas independentes, e nenhuma delas é o perfil que o Feca atualizou na virada do mês.** Sessão de medição contra o Postgres (read-only, exceto uma linha de config); nenhuma mudança de código. **Antes de tudo, a notícia que economiza trabalho: editar perfil de tipster NÃO mexe na sugestão do Feca.** Desde a s289 a carteira dele roda em `fonte='evidencia'` (28.779 rótulos humanos, muito acima de `MIN_TREINO=200`), e nesse caminho a rota lê só o **nome** (para saber quem está ativo) e o Registro de Casas — esportes, mercados e dica de stake ficam inertes. O declarativo só volta a valer para dono de base pequena. **CAUSA 1 — os prints de sugestão errada (409 → Peixe; escanteio do Sonny → Peixe) são da CURADORIA DE CASAS, não do modelo.** O modelo **acerta** os dois com folga larga (Sonny 12,22; Iranian 8,14) e nunca é consultado: `casa_config` tinha `Feca · Betnacional · dedicada · Peixe,Arrudex`, salva em **25/08**, e casa dedicada **crava antes do modelo** — com dois nomes a rota restringe o pool a eles, e **Sonny, Iranian, TC Insider, Latino, SóChutes e Fusion saem da cédula antes de qualquer conta**. Sobra o maior dos dois. Por isso três esportes diferentes (basquete, vôlei, escanteios) deram o mesmo nome errado. **Medido em 143 bilhetes de Betnacional com rótulo humano (60 dias): pool travado = 92 PRONTO / 27 BRANCO / 24 ERRADO; modelo livre = 95 / 46 / 2.** Os erros de hoje são `Iranian→Peixe 9 · Araújo→Peixe 3 · Latino→Peixe 3 · TC Insider→Peixe 2 · Arrudex→Peixe 2 · Australia→Peixe 1`: **troca 22 erros por 19 brancos**, e branco o dono vê enquanto erro ele tem de caçar. **O que fecha o caso: a própria regra do Sharpen já não sustentava a curadoria.** `casas_visao` só sugere `dedicada` com 1-2 donos cobrindo ≥`CASA_COVER`=85%; a Betnacional dá **82%** hoje (Peixe 134, Arrudex 49, mais 40 de oito outros) — o Sharpen sugeriria **`multi`**. Ela envelheceu porque Iranian, Sonny e TC Insider entraram na casa **depois** do retrato de 25/08. **É a única das 23 casas dedicadas nessa situação** — as outras 22 estão entre 95% e 100% de pureza e ficaram intactas. **APLICADO (a única escrita da sessão): `Betnacional → multi`**, espelhando `salvar_casa_config` (`modo='multi'`, `tipsters=''`, `origem='sharpen'` — é o que a regra sugere hoje), e **verificado pelo caminho REAL da rota** `/tipsters/sugerir`, não pelo modelo isolado: os três bilhetes dos prints passam a devolver Sonny · Iranian · Iranian, e a BETesporte segue cravando Peixe por casa dedicada. **Resíduo conferido e desprezível:** dos 48 bilhetes de Betnacional ainda com rótulo `sugerido`, o modelo livre discorda de **2**, ambos múltiplas gravadas como Arrudex — nada a limpar. Rótulo `sugerido` fica fora do treino (`rotulos_humanos`), então o modelo nunca foi envenenado; ele só alimenta `dominio_esportes`. **CAUSA 2 — os que não são indicados (MarcoF1, F1DP, DarkTennis, MMA, Fusion) sofrem um HANDICAP ARITMÉTICO por serem pequenos, e isso NÃO foi corrigido.** O denominador do Naive-Bayes é `tot_tipster + ALFA × vocab`, e `ALFA × vocab = 299` é **fixo**: 1% do denominador do Peixe (30.445 features) e 73% do F1DP (112). Como as features são sempre 7, isso é um **viés constante por classe** de `7 × log(tot/(tot+299))` — medido: **Peixe −0,07 · Arrudex −0,12 · Robotenis −0,35 · Fatuch −1,91 · MarcoF1 −5,00 · DarkTennis −7,77 · F1DP −9,10 · Fusion −9,43**, numa corrida onde a `MARGEM` exigida é **2,5**. O MarcoF1 larga o dobro da folga atrás; não perde a disputa, não entra nela. **Nada a ver com o perfil deles, e por isso mexer no perfil não adiantou.** Dois agravantes reais medidos junto: o F1 é dividido por MarcoF1 (117) e F1DP (73), então `dono_do_esporte` não crava (exige `PUREZA_ESPORTE`=0,98, ali dá 0,58) e **os dois se anulam** — o motivo mais frequente do vazio do MarcoF1 é literalmente ser o 1º colocado sem folga sobre o 2º, a mesma forma do MultiLBB × LBB da s221; e o **DarkTennis** (21 bilhetes, nascido em 24/08) joga Tênis onde o Robotenis tem 1.161, então o "Robotenis indicado errado" que o Feca corrigiu era o **inverso**: bilhete do DarkTennis rotulado Robotenis. ⚠️ **O nome é `DarkTennis`, com dois "n"** — `DarkTenis` não existe na base e devolve zero em qualquer query. **PLACAR DE USUÁRIO FINAL** (prequential com retreino diário, como a produção; base importada usa `data` do evento como eixo, per o caveat do `backtest_matcher.py` — a coluna `data` é TEXTO `dd/mm/aaaa`, não ISO), em PRONTO/BRANCO/ERRADO: **Feca 56/39/6** (2.979) · **Jonathan 70/28/2** (767) · **Gabriel 67/28/5** (3.055) · **Diogo 56/39/5** (2.139) · **arrudex 53/44/3** (2.210) · **LavaPessoal 61/31/8** (887) · **perereca 74/21/5** (307) · **Lava 100/0/0** (202). O geral do Feca (62% cobertura / 91% precisão em 2.939 bilhetes) **não regrediu** — está em linha com os 61%/89% da s289 —, mas a média esconde um matcher de **duas velocidades**: Arrudex 80%/98% e Peixe 78%/99% carregam o placar enquanto MarcoF1, MMA e Fusion ficam em **0%**. **CANDIDATO DE CORREÇÃO MEDIDO E RECUSADO POR ORA:** alpha proporcional ao tamanho do perfil (`a_c = ALFA × tot_c / vocab`, que iguala o handicap para todos) com varredura de `MARGEM`. Na margem 1,5 ele leva os 6 perfis pequenos do Feca de **18%/75% para 49%/93%** e ganha no Jonathan (70→76) e no Diogo (56→61) — **mas perde no LavaPessoal (61→53) e no arrudex (53→52)**, carteiras onde um ou dois tipstões dominam e o handicap estava, por acidente, ajudando. **Não é troca global**, e mexer na `MARGEM` mexe em todas as carteiras de uma vez; fica para uma sessão própria, com o alvo de ganhar nos pequenos **sem** cobrar do LavaPessoal. **PENDÊNCIA NOVA, e é a lição estrutural:** `casa_config` é um **retrato datado que nunca se reavalia**. Curadoria aplicada num dia continua cravando meses depois, mesmo quando a casa já não passa na regra que a sugeriu, e o erro é **silencioso** — não há aviso na tela, e o modelo, que sabia a resposta, sequer é ouvido. É a mesma família de "assinatura tem ERA": o Registro de Casas precisa marcar a linha cuja evidência deixou de sustentá-la. Backup do `casa_config` inteiro do Feca (40 linhas, JSON) em `Backups/s308-casa-config-betnacional/casa_config_Feca_antes.json`. **Sem mudança de código, sem versão de SharpenUp, sem nota de changelog, testers não avisados** — a mudança é de configuração de uma carteira, não do produto. `app/static/landing.html` seguiu FORA do commit, como na s302/s304/s306/s307/s308. ⚠️ **Este commit carrega junto o texto s309 de OUTRA sessão simultânea**, que estava sem commit no `STATUS.md` quando esta entrada foi escrita — arquivo único, index compartilhado (invariante 8). Nada se perdeu: as duas narrativas estão no arquivo.)_

_Anterior: 2026-09-01 (sessão 309 — **O Rogerin mandou um print da bet365 no dia 1 e o bot respondeu "não consegui ler" três vezes. O prompt da visão estava travado numa casa — e atrás disso havia dois defeitos que ninguém veria.** Trabalho todo no repo `sharpen-bot`; o Planilhador só recebe este registro. **O sintoma, medido no apoio (01/09 18:53→18:55):** três prints da bet365, três `⚠️ Não consegui ler o print: Print não é da Betano, é da bet365 - formato incompatível`, e o tipster respondendo `kkkkkkkkkkkkkkk` e `Okay canalha`. **A causa é uma linha de prompt.** O `SYSTEM` de `src/perfis/rogerin.js` abria com *"Você lê prints de bilhetes da casa de apostas Betano"* e fechava com *"Print ilegível → {erro}"*: o modelo obedeceu **as duas ao mesmo tempo** e classificou "casa diferente" como "ilegível". **Nenhuma casa fora da Betano passava**, e a mensagem de erro não dizia que a culpa era do prompt. Hoje o prompt lista `NOMES_CASAS`, devolve `casa` e **diz explicitamente que casa/layout diferente NÃO é print ilegível** — o teste trava a 1ª linha contra nome de casa, e essa mutação fica vermelha. **2º defeito, calado: a `casa` do bilhete nunca vinha do print.** Ela saía só da legenda ou do host do link (`parseLegenda`), e o `CASA_PADRAO` cobria o resto — print de bet365 sem link ia para o Sharpen **gravado como Betano**, sem erro nenhum. `casa` é TEXTO em 7 tabelas: seria conta paralela, silenciosa. Precedência hoje é **legenda → print → default**, com `casaPorTexto` canonizando a grafia (`bet365` → `Bet365`; verbatim ali criaria a conta gêmea) e **aviso no apoio quando é o default que decide**. **3º defeito, o que ninguém veria nunca: o print são TRÊS apostas SIMPLES separadas.** Gerson Mais de 0.5 @1,66 · Mais de 1.5 @4,00 · Mais de 2.5 @11,00, legenda `2u, 1u, 0,25u`. O `montarApostas` devolvia **sempre uma aposta só**, com todas as pernas dentro: viraria uma múltipla de odd 1,66 × 4,00 × 11,00 ≈ **73** com stake **2u**, porque o `parseLegenda` casava **só a primeira stake** (`match` sem `/g`). Uma aposta fantasma no lugar de três, com o P/L errado e **sem um aviso**. **O discriminador é do próprio print e é confiável:** quando a casa vende N simples ela imprime **stake e retorno POR seleção** e um "Aposta Total" no rodapé; o bilhete único da Betano imprime **uma odd total no topo** e nenhuma stake por perna. A visão passou a devolver `apostasSeparadas` + a stake de cada perna, e o ramo novo só dispara com **três guardas**: a flag da visão, **forma nova de seleções** (o `idxs` indexa `selecoes`, e registro anterior à s307 apontaria para o lugar errado) e **toda perna com odd própria** (simples sem odd tem P/L de W incalculável). Bet builder vence a flag nos dois lugares — a casa precifica o **conjunto**. **⚠️ A stake planilhada continua vindo da LEGENDA, em unidades.** O print traz R$ e o tamanho da unidade dele **nunca foi medido**; converter seria inventar. A stake do print (`stakePrint`) entra **só como conferência**, e é uma conferência que vale: **as proporções não dependem da unidade**, então elas denunciam legenda escrita **fora da ordem** do print — que é o único jeito de o valor certo cair na aposta errada **sem o total mudar**. Sai aviso também quando o número de stakes ≠ número de apostas, e quando N apostas nascem juntas (um ✅ na legenda marca **todas**; o painel marca uma a uma). **Códigos:** `RG<aaaamm>-<n>-S1..-Sn`, o sufixo do Rei do Criquete e do PassaTips. **Aposta única segue SEM sufixo** — o que já está gravado no Sharpen não muda de código, não muda de post, não muda de odd. **Duas correções que vieram junto porque o print as exigia:** `Chutes` e `Chutes no Gol` entraram no `categoriaDaPerna` (o mercado é `Jogador - Chutes`; sem isso as três apostas cairiam em `Outros`), com a **ordem** deliberada — "Chutes no Gol" tem de sair antes do `\bgols?\b`, senão vira `Gols`, que é outro objeto (`MASTER_APOSTAS §3`); e o **confronto passou a sair uma vez por jogo** no post de N apostas, defeito que só apareceu ao renderizar o post de verdade (as três linhas são do mesmo Atlético-MG × Cruzeiro e o cabeçalho repetia três vezes). **GATES: 19 mutações, 18 pegas.** A 19ª — derrubar o `replace` das URLs no `parseLegenda` — é **inócua hoje** e está registrada como tal no teste, sem asserção inventada: quem barra o falso positivo é a classe de separador do regex (`(?:^|[\s,;])`), porque dentro de uma URL os dígitos nunca vêm depois de espaço, vírgula ou início de string; o `replace` só passa a ser load-bearing se alguém afrouxar essa classe. **Duas mutações escaparam na 1ª rodada e as duas eram buraco de TESTE**, da família já catalogada no `CLAUDE.md`: o clamp `betBuilder` do `lerPrint` era mascarado pela guarda própria do `montarApostas` (o teste chamava `montarApostas` direto, sem passar pela visão — agora passa) e a dedup do confronto não tinha asserção nenhuma. **`lerPrint` virou testável** por dublê de `chamarVisao` via `require.cache`, o que traz a montagem inteira para dentro do gate. **O que os testes declaram NÃO cobrir:** a leitura da imagem em si. Que o modelo de fato leia um print de bet365 **só se mede mandando um print** — o dublê prova a montagem, não a visão. **Próximo passo é exatamente esse:** o Rogerin repostar um dos três prints e conferir no canal as três linhas 🎯 com stakes 2u/1u/0.25u, e na planilha as três linhas `-S1/-S2/-S3` com casa **Bet365** e categoria **Chutes**. **Observação registrada, não corrigida:** a stake no post sai com **ponto** (`0.25u`) ao lado do total com **vírgula** (`+2,82u`). O ponto é convenção declarada do `stakeFmt` (`src/formatter.js`: *"stake como no mockup do canal"*) e vale nos **cinco** perfis — trocar seria mudança de marca em todos, decisão do Feca, não efeito colateral desta. Backup em `Backups/s309-rogerin-multicasa-multisimples/`; commit `ed14a58` pushado na `master` do `sharpen-bot`. `app/static/landing.html` seguiu FORA do commit, como na s302/s304/s306/s307 — já estava modificado quando a sessão abriu. **Sem mudança no SharpenUp e sem nota de changelog:** não é versão da extensão, não há nada para o tester atualizar.)_

_Anterior: 2026-09-01 (sessão 308 — **O tipster manda 4u, a casa só deixa passar R$250 — e agora o canal conta as duas coisas.** Pedido do PassaTips no WhatsApp: a banca simulada do grupo dele é R$100 a unidade, ele publica uma 4u, a casa limita em R$250 e ele planilha 2,50u. **São DUAS coisas e o pedido só parece uma:** trocar o número já dava para fazer à mão no dashboard; o que faltava era **mostrar as duas ao seguidor**, porque as duas são verdade — a recomendação e o que de fato entrou. Hoje sai `🎯 <s>4u</s> 2,8u | … @ 2,90` no post. Todo o trabalho é no repo `sharpen-bot`; o Planilhador só recebe este registro e **nada muda no app** (o `PATCH /bilhetes/{id}` já aceitava `stake`). **`/atualizastake #N [nº] 2,80` e `/atualizaodd #N [nº] 2,37`** (apelidos `/atualizar…` e `/stake`, `/odd`), nos **cinco** perfis. Um miolo só, puro e testável, em `src/atualizar.js`. **A numeração das apostas é a mesma nos dois comandos e cobre o `reg.apostas` INTEIRO, anuladas inclusas** — filtrar faria os números **andarem** entre a listagem e o comando, e o "2" que ele leu apontaria para outra aposta depois de um `/anularparcial`. Sem número explícito só vale com **uma** aposta viva; com duas o bot **lista em vez de chutar**, que é o desfecho certo quando errar significa trocar o número da aposta errada em silêncio. **A stake é da APOSTA; a odd pode ser da PERNA — e aí está a distinção que o arquivo existe para não perder.** Uma perna alimenta a aposta dela e as combinações que a contêm, mas **combo de odd DERIVADA se recalcula sozinho e combo de odd DECLARADA, não**: Só Chutes e Zora montam a múltipla como `produtoOdds`, então o produto novo é a odd nova; PassaTips e Rei do Criquete usam **a odd que o tipster escreveu**, que não é o produto exato (a casa arredonda) e é a que casa com o cupom — sobrescrevê-la inventaria um número que não está em bilhete nenhum. **Isso não está declarado em lugar nenhum do código, então é MEDIDO**: se o `oddOriginal` guardado bate com o produto das pernas de antes, era derivado. A mesma régua protege a **turbinada do Rogerin**, cujo bônus é pago **por fora** da odd exibida — recalcular pelo produto ali apagaria o bônus sem um erro sequer. Combo que fica para trás é **nomeado no aviso do apoio**; nada some em silêncio. **A saída reusa o `aplicarMarcacao`, e de propósito:** ele já reedita o post no canal, reenvia ao Sharpen e faz o `PATCH` do que já resolveu — **nessa ordem**, senão o reenvio reintroduz o valor antigo (é a lição do `ajustarData`). Duas mudanças lá dentro. **(1) A stake entrou na detecção de correção:** o UPSERT congela `stake` quando a linha resolve, então o reenvio sozinho deixaria a aposta liquidada com o número velho no banco e o novo no canal — UPSERT meio-atualizado com outra roupa. **(2) O retrato de ANTES virou parâmetro:** marcação e correção de odd passam por `oddOriginal` e o `aplicarMarcas` devolve objetos novos, então o "antes" sobrevive sozinho; **a stake não tem essa indireção** — quem a troca mexe no objeto, e sem a cópia o laço compararia o valor novo com ele mesmo e o `PATCH` nunca sairia. **O `<s>` da stake sai antes de qualquer risco externo** (`riscar` e os cinco `formatarBilheteAnulado`): `<s>` dentro de `<s>` não se lê e arrisca o parse do post **inteiro** — mesma família do `<code>` proibido dentro de strikethrough, que o `formatter.js` já documentava. **Desfazer existe:** trocar de volta para o valor original apaga o `stakeOriginal` e o riscado some do canal. Sem isso um dedo torto ficaria riscado para sempre. E a segunda troca preserva a **primeira** recomendação (4u → 2,80u → 2,50u continua riscando 4u), que é o número que o grupo viu. **GATES:** suíte do bot **inteira verde** · **mutação 13 de 13** (a original ignorada no post, `riscar` e o anulado voltando a aninhar `<s>`, a recomendação não guardada, o desfazer removido, o combo declarado recalculado, a turbinada perdendo o bônus, stake 0 aceita, alvo escolhido sozinho com duas vivas, numeração pulando anuladas, a stake fora do `PATCH`, e as duas pontas do retrato de antes) · o bloco que leva a stake ao banco é **RECORTADO do `index.js` real**, nunca copiado. **O que os testes NÃO cobrem está escrito no cabeçalho do bloco:** a ida ao Telegram e ao Sharpen; e a ponte entre `comandoAtualizar` e `aplicarMarcacao` é asserção de **fonte**, não de execução — está dito ali por quê. **Não é versão de SharpenUp:** nada para o tester atualizar, nenhuma nota de changelog. **Testers não avisados** — a mudança é do robô de um tipster, não do produto que eles usam. Quem precisava saber é o PassaTips, e o **aviso foi publicado com o "pode mandar" do Feca**, destino conferido por `getChat` antes (`PassaTips - Apoio` · `-5477004625` · type `group`): `message_id 2565`. Backup em `Planilhador/Backups/s308-atualiza-stake-odd/` e `sharpen-bot/Backups/s308-atualiza-stake-odd/`; commit `a9779cc`, pushado na `master`. `app/static/landing.html` segue FORA do commit, como na s302/s304/s306/s307 — já estava modificado quando a sessão abriu. **Sem mudança no SharpenUp.**)_

_Anterior: 2026-09-01 (sessão 307 — **O `/anular` ganhou volta, e o perfil do Rogerin foi consertado em três frentes no dia 1 dele. Todo o trabalho é no repo `sharpen-bot`; o Planilhador só recebe este registro.** **`/desanular #N`** (apelidos `/desanula`, `/restaurar`) tira o risco do post no canal, devolve o teclado do painel e recria as apostas na planilha. **A volta NÃO passa pelo `POST /bilhetes/restaurar` do app**, e por três motivos medidos: o `/salvar` devolve os **ids novos**, que o `reg.sharpenIds` precisa para qualquer correção posterior por `PATCH` (o `/restaurar` devolve só um contador e os ids ficariam mortos para sempre); o `submitted_at` vai junto e é ele que vira o `criado_em`, então a linha volta ao **mesmo lugar do feed** em vez de saltar para o topo; e o `/bilhetes/restaurar` usa `dono_efetivo`, **não** `_ou_bot` — o token de serviço do bot nem alcança a rota. Como o reenvio é o caminho já testado da marcação, **zero mudança no app**. **Dois passos, de propósito:** o que um `/anularparcial` tirou ANTES do `/anular` **não** volta junto, porque o `/anular` nunca tocou no `ap.anulada` dela (apaga no Sharpen só as vivas); o aviso nomeia quais seguem fora e diz que rodar `/desanular` de novo, com o bilhete já vivo, traz essas. A busca do bilhete **inverte** a precedência (o alvo é o anulado; com número reaproveitado o vivo sombrearia), e para isso o `acharBilhetePorNumero` saiu do `index.js` para `src/desanular.js` parametrizado: **uma implementação, dois sentidos** — e o teste que **copiava** essa função para dentro dele passou a exercitar o código real. Falha do Sharpen deixa o post restaurado e a planilha para trás: o aviso diz isso e aponta o `/ressincronizar`. **Mutação: 3 de 3.** **ROGERIN, três defeitos, e o terceiro era estrutural.** (1) **O link do bilhete não ia para o canal:** o `parseLegenda` já extraía o bookingcode desde a s306 — o post é que nunca chamava `linhasDeCasas`. Hoje sai `🏠 Betano` clicável, como nos outros três perfis. (2) **O P/L ficava colado na linha `🎯`;** agora o resultado vai em linha própria (`📊 Resultado: −1u`), como no Só Chutes. (3) **UMA seleção para N pernas.** O painel tinha um botão para uma dupla, e não existia como dizer "essa perna voltou, a outra ganhou". **Medido na base dele antes de mexer:** os bilhetes são todos duplas e a asiática entra dentro delas (`Mais de 1 Asiático (Mais/Menos) - Total de gols - 1° Tempo`, 3 linhas, 2 delas **abertas agora**). Hoje cada perna é uma seleção, com botão próprio; perna devolvida recalcula a odd da dupla sozinha, com a Turbinada reaplicada. **Um emoji na legenda continua marcando o bilhete inteiro** — é o hábito dele, 9 dos 11 posts medidos —, e vários viram um por perna, na ordem. **MEIA (HW/HL) entrou no núcleo:** `plAposta` (`src/bets.js`) aprendeu os dois códigos e o `formatter.js` **perdeu a cópia dele** (`plNum`) — em meia as duas divergiriam e o canal mostraria um número que a planilha não paga. O painel ganha `½✅`/`½❌` numa segunda linha **só na perna que pode resolver pela metade** (quarto de linha `.25`/`.75`, ou rótulo asiático — linha `.5` nunca empata e linha inteira devolve a perna, que é o 🔁); **não há emoji de meia na legenda**, de propósito. **A REGRA QUE FALTAVA NO MASTER: a fórmula do `HW` só fecha em aposta ÚNICA.** Ela assume que a metade devolvida devolve a **stake** (`app/repository.py`: `(stake/2) × odd + stake/2`), e numa dupla a metade devolvida **ainda corre a outra perna**. Então: simples asiática → `HW`/`HL` com a odd **exibida**, intacta (`MASTER_RESULTADO §5.3/5.4`); múltipla cujas outras pernas foram **todas devolvidas** → também `HW`/`HL`, mas com a odd da **perna que sobrou** (a do bilhete embutia as devolvidas e pagaria a mais); **múltipla de verdade com uma meia dentro → `W` com `Odd = Retorno ÷ Stake`**, que é o mecanismo do **cashout** (`§5.6`), inclusive quando o retorno é MENOR que a stake (odd < 1, P/L negativo). O modelo é o das **metades**: a aposta se parte em duas metades da stake — numa a meia perna vale, na outra ela é devolvida —, cada metade resolve pela regra normal e o retorno é a média. **RETROCOMPATIBILIDADE era risco real, não teórico:** havia **6 bilhetes abertos** no storage na forma velha (`selecoes[0].pernas`), e o post é remontado do zero a cada marcação. `pernasDe` aceita as duas formas, o `idxs` indexa `selecoes` (que na forma velha tem tamanho 1) e a marca única aparece em **todas** as pernas do post — indexar `marcas[i]` ali faria os bilhetes abertos mostrarem ✅ numa perna e nada na outra, sem ninguém ter marcado assim. Os testes da forma antiga ficaram no arquivo **como prova disso**. **GATES:** suíte do bot inteira verde · **mutação 8 de 8** no Rogerin (`pernasDe` cego à forma antiga, `permiteMeia` sempre true, HW pagando lucro cheio, múltipla-que-virou-simples sem HW/HL, post sem link, post sem a linha de resultado, `idxs` voltando a `[0]`, marca indexada por perna no registro velho) **+ 3 de 3** no `/desanular` · teste novo prova que **o P/L do bot é sempre `retorno − stake`** pela fórmula do `app/repository.py`, nos 5 códigos. **MEDIÇÕES que fundamentaram as decisões:** HW/HL são usados de verdade no sistema (**528 linhas em 12 donos**; Feca 176, Gabriel 139, Jonathan 120) e **ninguém desmembra** — o modelo canônico é uma linha com o código; asiático no sistema inteiro são 813 linhas (402 L, 350 W, 57 V, **4 HW/HL**), e na base do Rogerin **0 em 402**. Ou seja: meia é rara, e a regra veio do MASTER e da fórmula do app, nunca de bilhete dele já liquidado. **AVISOS PUBLICADOS** com o "pode mandar" do Feca, destinos conferidos por `getChat` antes: o `/desanular` nos **5 apoios** (Só Chutes 573 · Zora 10 · Rei do Criquete 2550 · PassaTips 2551 · Rogerin 33) e a mudança do painel **só no apoio do Rogerin** (34), porque o perfil é dele. Não é versão de SharpenUp: nada para o tester atualizar, nenhuma nota de changelog. `app/static/landing.html` seguiu FORA do commit, como na s302/s304/s306 — já estava modificado quando a sessão abriu. Backups em `sharpen-bot/Backups/s307-desanular/` e `sharpen-bot/Backups/s307-rogerin-asiatico/`; commits `fc3268e` e `a5c8a00`, pushados na `master`. **Sem mudança no SharpenUp.**)_

_Anterior: 2026-09-01 (sessão 306 — **6º tipster no ar: `RogerinComeuMeuSaldo`, 393 apostas importadas — e a coluna `Esporte` da fonte é comprovadamente errada.** O pedido chegou como "Tipsters/SoBolas" e a marca **mudou no meio da conversa** para `RogerinComeuMeuSaldo`; o arquivo continua se chamando `sobolas.csv`. **Nem o nome do arquivo nem o apelido inicial são fonte de marca ou de dono** — o `dono` é o username `Rogeringambler`, conferido na tabela `usuarios` antes de qualquer escrita (ativo, hash de 60 chars, e-mail `maodevaca.precos@gmail.com`, cadastro em autosserviço em 31/08/2026), como manda a regra da s260. Marca ≠ username pela terceira vez (Fleury/Flurray, PassaTips VIP/passapano). **A base:** export de tracker pt-PT em CSV (`Cotação`, `Ténis`, `Basquetebol`), 393 linhas, 10/04 → 31/08/2026, stake em **unidades** — turnover 458,82u, **P/L +72,66u, ROI +15,84 %**. **Catorze das 24 colunas estão VAZIAS nas 393**, e nenhuma das que sobram diz o mercado: a categoria sai da leitura do título, não de uma coluna. **O GATE DO IMPORT é a reconciliação com a própria fonte:** o P/L derivado é conferido contra a coluna `Lucro` linha a linha — **0 divergências em 393**. Sem isso, odd com ponto/vírgula trocados ou resultado mal lido passaria calado. **DUAS ERAS que não se parecem** (a regra "assinatura tem ERA", do `CLAUDE.md`): 10/04→30/05 é prop de jogador da NBA (181 apostas, ROI +7,61 %, green 29,8 %) e 27/07→31/08 é multiesporte (212, ROI +25,33 %, green 51,4 %), com hiato de ~2 meses entre elas — backtest que misture as duas mede duas pessoas. **A COLUNA `Esporte` ERRA, e erra mais do que dá para provar:** 13 props da NBA vêm rotuladas `Futebol` (`Kuminga 20 pt`, `Derrick white 4+ 3pt`, `Royce oneal 10+ reb`), corrigidas para `Basquete` por decisão do Feca; mas `Sakkari aces` (tenista) também está sob Futebol, e na ERA 2 os títulos pareiam entidades de esportes diferentes (`Altrincham / Hurkacz` sob Ténis, `Grécia / Swiatek` sob Basquetebol) — **indecidível qual metade é a certa, então rótulo e título entram os dois como estão**. **A CATEGORIA NÃO É GATEADA PELO ESPORTE, de propósito:** presa ao rótulo errado, essas 13 cairiam em `ML` e o import erraria DUAS colunas em vez de uma. Medido: a regra solta classifica 18 linhas como `Player Props` fora de Basquete e **nenhuma é falso positivo** (13 da NBA + 3 `G/A` de futebol + 2 de `aces` no tênis). **126 linhas (32 %) vinham SEM CASA → `Betano`, decisão do Feca** — e ficou registrado no docstring que isso **contraria** a distribuição por mês (nas linhas com casa, abr/mai é Bet365, 82 de 90; só agosto é Betano), para ninguém "consertar" depois achando que foi engano. Linha sem casa nasceria invisível no Painel de Contas, então não havia default seguro: o script **aborta** se rodar sem `--casa-vazia` em arquivo com linha vazia. **Três odds impossíveis, e uma delas não é defeito:** `Kostanay / Kaisar` tem odd 0,690 com `Estado=Ganha` e lucro −0,31 — retorno MENOR que a stake com resultado "ganha" é a assinatura de **cashout**, e o `MASTER_RESULTADO §5.6` já produz o resultado certo pela leitura literal (`W`, odd = cashout ÷ stake). As outras duas são 0,500 em apostas **perdidas**, onde o P/L é −stake e **não depende da odd** — entram como estão e saem listadas para ele corrigir na grade. **22 linhas declaram combinação no título** apesar de a coluna `Tipo` dizer `Simples` nas 393 (`Multipla 26-04` @500, `Bingo 28-04` @300, 13 "aumentada"/booster da Betano): todas ganham `aposta = Múltipla`, mas **só `multipla`/`bingo` viram `esporte = Múltiplos`** — `dupla` declara DUAS seleções e o `MASTER_ESPORTES §2` reserva `Múltiplos` para 3+. **Casas: as 3 grafias do arquivo batem EXATO com o banco** (Bet365 58.994, Betano 15.438, Pinnacle 3.189), medidas antes de escolher — nenhuma casa nova, nenhum favicon a cadastrar. `Beisebol` → `Baseball` de propósito (4 × 1.293 no banco: importar na grafia minoritária criaria esporte gêmeo). **Código `RG<aaaamm>-<n>`**, prefixo conferido **livre** no banco (em uso só `PT`, `RC`, `ZE` e um `BB` solitário); último gravado **`RG202608-204`**. **APLICADO EM PRODUÇÃO:** 393 bilhetes sob `Rogeringambler`, 3 contas `Padrão` (Betano 304 · Bet365 88 · Pinnacle 1), registro em `TIPSTERS_PUBLICOS` (`/tipsters/rogerincomeumeusaldo`) e `bot_habilitado` ligado — a ordem que o `CLAUDE.md` manda, botão ANTES do token, para o tenant não tomar 401 na migração. **O BOT NÃO FOI LIGADO, e o bloqueio é de MEDIÇÃO, não de configuração:** os 4 perfis existentes (`src/perfis/`) foram cada um escrito a partir de um export **medido** do canal daquele tipster — PassaTips 1.394 mensagens, Rei do Criquete 526, Zora o histórico de 01-02/08 — e eu não tenho nenhuma mensagem do canal dele. Escrever perfil por palpite falha em silêncio, que é exatamente o modo de falha que este projeto passa o tempo todo tentando evitar. Recebidos e guardados: grupo oficial `-1004319287532`, apoio `-1004311400244`, tipster `@mgdaraujo` (`1961444284`). **ADENDO (mesma sessão): a amostra chegou — 11 prints reais do chat dele — e o perfil do bot está escrito, testado e pushado.** Ele **não tinha canal**: postava num chat da galera, e começa "de forma séria via bot" em 01/09. **E os prints derrubaram uma coisa que eu tinha escrito como FATO no docstring do importador.** Eu afirmava que o ` / ` dos títulos da ERA 2 "NÃO é separador de seleção" e que ele pareava entidades de esportes diferentes por engano. **É separador de PERNA de uma DUPLA**, abreviada pelo sobrenome de cada seleção — e a prova é a odd, exata em **4 de 4**: `Egito / Mensik` 3,70 = 2,00 × 1,85 · `Altrincham / Hurkacz` 3,02 = 2,10 × 1,44 · `Virtanen /Sabalenka` 1,84 = 1,50 × 1,23 · `Mezxa / Arsenal` 2,36 = 1,30 × 1,82. O `Mezxa / Arsenal` mata a hipótese antiga: "Meza" é tenista e o Arsenal é clube — não era dado embaralhado, era abreviação. **182 das 212 linhas da ERA 2 (86 %) têm a barra.** Corrigi o docstring; **NÃO reclassifiquei os dados**, porque `A / B` também pode ser confronto real (`Kostanay / Kaisar` são dois clubes cazaques que se enfrentam) e sem o print não dá para separar — fica como decisão, e o **P/L não é afetado** (stake, odd e resultado estão certos; erra `esporte`/`aposta` num subconjunto). **A 2ª descoberta virou requisito do bot: a odd "aumentada" é a TURBINADA, e o bônus é pago POR FORA da odd exibida** — mesma família do `SuperMúltipla` da Estrela Bet (s303). A fórmula é `1 + (odd − 1) × (1 + N/100)`, porque o bônus incide sobre o **lucro**, e são **três provas independentes**: o print em R$ (aposta R$557,00 · "Ganhos Potenciais" R$1.364,65 = 557 × 2,45 · "Turbinada +50%" **+R$403,83**, que é 50 % exatos do lucro de R$807,65 → odd efetiva **3,175**); Barcelona print 2,18 +25% → 2,475 e **ele registrou 2,47**; Real Madrid 2,60 +25% → 3,00 e **registrou 3,00**. O contraexemplo aparente confirma: no Arsenal (3,05 +25%) ele registrou 3,05 cru, e aquele bilhete é **perdida**, onde o P/L é −stake e não depende da odd — é o `MASTER_RESULTADO` (odd em W = Retorno ÷ Stake). Planilhar a odd do print subestimaria toda vitória turbinada dele. **O perfil (`src/perfis/rogerin.js`, repo `sharpen-bot`) é o 2º em que o PRINT é o bilhete inteiro** — a legenda não nomeia seleção nenhuma; na Zora o print só resolve a odd. **1 bilhete = 1 aposta**, medido na base dele. **Stake 1u por padrão e ele informa quando variar (decisão do Feca)** — em 10 dos 11 posts não havia stake; o default é **ambíguo por construção** (legenda vazia não distingue "quis 1u" de "esqueci"), então `avisosMontagem` avisa no apoio **toda vez** que a stake é assumida. **Um defeito meu achado pelo próprio teste:** `linksDaLegenda` devolve OBJETOS `{url,casa,host}` e já resolve a casa; eu passava o objeto para `casaPorHost`, o `new URL()` falhava lá dentro e devolvia `null` **calado** — a casa do bookingcode nunca teria sido lida. **GATES:** 24 casos com fixtures **verbatim** dos prints · **provado por mutação: 22 de 22 detectadas**. As 2 que escaparam na 1ª rodada eram **buraco de TESTE**, não linha inócua, e da mesma família: o fixture de bet builder tinha as 3 pernas no mesmo esporte e sem odd própria, então nem o ramo de `betBuilder` do `esporteDe` nem o guard do produto eram exercidos — o caminho de baixo acertava **por acaso** (falso verde tipo 2 do `CLAUDE.md`). Entraram os dois casos que faltavam. Suíte do bot inteira verde. **Nada muda em produção até as env vars `RG_*` existirem no Railway** — o bloco só entra se `RG_APOIO_ID` existir. **ADENDO 2 — o bot está NO AR.** O Feca perguntou se eu não subia no Railway; o CLI já estava autenticado (`giving-appreciation` / `production` / `sharpen-bot`), então subi as quatro env vars (`RG_APOIO_ID`, `RG_DESTINO_ID`, `RG_TIPSTER_IDS`, `RG_SHARPEN_USER`) com `--skip-deploys` + **um** redeploy, **conferindo o que CHEGOU** e não o que mandei (sinal negativo dos ids preservado, sem truncar). Boot limpo: `contador rogerin 2026-08 = 204` e `RogerinComeuMeuSaldo` na lista dos 5 tenants, com `[sharpen:Rogeringambler] token de serviço (sem fallback de senha)`. **Autorização de escrita PROVADA sem gravar nada:** `POST /bilhetes/tipster` com `ids:[]` — a dependência `dono_efetivo_ou_bot` resolve ANTES do handler, então **401 = identidade recusada** e **400 = identidade aceita, pedido recusado no conteúdo**. `Rogeringambler` → **400**; e o controle negativo `perereca` (ativo, mas sem o botão) → **401**, que é o que prova que a sonda discrimina em vez de responder 400 sempre. **E a conferência dos destinos por `getChat` — que o `CLAUDE.md` manda fazer ANTES de qualquer publicação — achou o defeito da noite: os dois chats são CANAL, não grupo** (`Apoio - Rogerin` e `Rogerin comeu meu saldo`, bot `administrator` com `can_post_messages` nos dois). Isso importa porque **vários dos 11 posts dele vêm com a legenda VAZIA** — o print é postado e o ✅/❌ entra depois por EDIÇÃO. No fluxo antigo, foto sem legenda ia para `pendentes` esperando um texto que nunca chega, **e a edição não salva**: `processarEdicao` só age sobre bilhete que já existe (`getBilhete` devolve `undefined` e volta). **O bilhete morreria em silêncio, sem nada no canal e sem nada na planilha** — falha certa no dia 1. Em canal é pior: a chave dos pendentes é a string `'canal'` para TODOS os posts, então prints em sequência perderiam todos menos o último. **Correção ADITIVA: `legendaOpcional` no perfil**, ligada só no rogerin (onde o PRINT é o bilhete inteiro e a legenda carrega no máximo a stake, que tem default); os outros quatro não a declaram e nada muda neles. Nota: `RG_TIPSTER_IDS` é **inerte em canal** — não existe `msg.from`, e o gate `if (msg.from && !ehTipster(…))` é pulado; ficou setada mesmo assim, porque documenta quem é o tipster e passa a valer se o apoio virar grupo. **Mutação do ramo novo: 3 de 3**, mais a 4ª (pôr a chave na Zora deixa o teste vermelho) — e a 1ª tentativa dessa 4ª foi **mal aplicada por mim** (acrescentava um comentário no `rogerin.js`, que não faz a flag vazar para lugar nenhum) e "escapou" sem haver buraco: a armadilha da s304, refeita no alvo certo. Regressão do perfil: **22 de 22**. O teste **recorta o ramo do `index.js` real lido do disco**, nunca copiado, e declara o que não cobre (o `tratarEntrada` de verdade precisa de bot do Telegram e I/O). ⚠️ O commit `sharpen-bot` desse fix teve a **mensagem mutilada**: as crases dispararam substituição de comando no bash e comeram três identificadores (`pendentes`, `legendaOpcional`, o gate do `ehTipster`); o código está correto e o histórico pushado não foi reescrito. **ADENDO 3 — EXERCIDO AO VIVO, e deu certo de ponta a ponta.** O último elo não testado era a visão lendo um print de verdade; o Feca postou e saiu o **`RG202608-205`**: `Tênis` · `Múltipla` · `Betano`/`Padrão` · descrição `#205 Mais de 8.5 Total de Games no Set (Set 1) [Enzo Aguiard v Hayato Matsuoka] // Menos de 22.5 Games [Federico Iannaccone v Juan Estevez]` · stake **1u assumida** (legenda vazia — o caminho do `legendaOpcional`, que sem o fix teria morrido calado) · odd **2,48**, que é `1,38 × 1,8` · `aberta` · tipster `RogerinComeuMeuSaldo`. **E o código saiu exatamente onde a semente previa** (204 → 205), o que valida a numeração contra a série do import. **Único ajuste pedido: o formato do post.** O negrito passou da SELEÇÃO para o EVENTO — `🎾 <b>Enzo Aguiard v Hayato Matsuoka</b>` numa linha e `Mais de 8.5 Total de Games no Set (Set 1) @ 1.38` na seguinte —, porque quem lê o canal procura o jogo primeiro, não o mercado. O confronto sai **uma vez por jogo**: num bet builder as N pernas são do mesmo confronto e repetir o cabeçalho encheria o post com a mesma linha. **Nada muda na planilha** — descrição, esporte, categoria, stake e odd são os mesmos; é só o post. **Mutação: 4 de 4** (incluindo a que devolve o formato antigo), e o teste trava os DOIS lados da troca — o evento em negrito **e** a seleção fora dele —, mais a ordem entre as duas linhas e a deduplicação do confronto. Regressão do perfil segue **22 de 22**. **O `#205` ficou no formato ANTIGO no canal:** o `scripts/rerender_canal.js` é da era mono-tenant (aponta para o `CANAL_ID` e para o `bilhetes.json` solto, não para o storage namespaced no volume), então re-renderizar exigiria adaptá-lo e rodar contra o volume — não vale por um post, e do #206 em diante já sai certo. `app/static/landing.html` seguiu FORA do commit, como na s302/s304. Backups em `Backups/s306-tipster-rogerin/` (Planilhador) e `sharpen-bot/Backups/s306-perfil-rogerin/`. **Sem mudança no SharpenUp.**)_

_Anterior: 2026-08-31 (sessão 305 — **A SportingBet devolvia 0 bilhetes porque esperava uma requisição que a casa muitas vezes NÃO faz. O replay agora arranca A FRIO.** O gatilho foi do grupo: o Gabriel com o print do toast (*"Sportingbet insiste nesse erro mesmo eu indo na página de liquidadas"*) e o 1Tonelada confirmando (*"Aq tb"* · *"N processa"*). **Diagnosticado no navegador do Feca, com sonda no mundo MAIN da casa logada — não por dedução.** A minha 1ª hipótese (inject gritando dentro de iframe, como bet365/Betfair/Tivo/Bolsa) estava **errada**: a requisição sai no frame do TOPO. **DUAS causas, as duas medidas, e cada uma sozinha já produz o sintoma.** (1) **A página pode não fazer requisição nenhuma:** carga direta ou F5 de `/pt-br/sports/minhas-apostas/liquidada` renderiza a lista inteira **pelo servidor**, com ZERO chamadas a `betslips` — o POST só sai na *primeira* vez que cada aba é aberta dentro daquela carga, e reabrir a mesma aba não dispara nada. Sem requisição, `reqCtx` fica nulo e o `arrancarReplay()` antigo voltava na 1ª linha. E é o **F5** — o conselho padrão para extensão travada — que garante o cenário. (2) **A leitura passiva é impossível aqui:** a SPA dispara o `fetch` com `AbortSignal` e aborta assim que consome a resposta, então `r.clone().text()` **rejeita** com `AbortError` (medido 2 de 2, status 200 nas duas). Como o `.then` não tinha 2º argumento, isso morria como *unhandled rejection*: `respostas` em 0 **sem uma linha no console**. É a 3ª casa com esse comportamento (Pitaco, Novibet) e a 1ª em que ele ficou mudo. **A CORREÇÃO é montar a requisição sozinho.** Medido na conta, com os cabeçalhos do motor como CONSTANTES (`x-bwin-sports-api: prod`, `Sports-Api-Version: SportsAPIv2`, `X-From-Product: host-app`, `X-Device-Type`, `x-bwin-browser-url`) + os cookies da sessão: **`Settled` p1 = 33 bilhetes, p2 = 0 · `Open` p1 = 4, p2 = 0**, sem aprender nada da página. O `X-XSRF-TOKEN` **não é exigido** (mandei vazio e passou; nem existe cookie de XSRF na sessão), então ficou fora das constantes. A requisição real continua sendo aprendida quando aparece — ela traz campos que não conhecemos (`openEventIds`, `liveEventIds`, `summaryBetNumbers`) e preferimos preservá-los —, mas virou **melhoria, não pré-requisito**; e os headers aprendidos só são aceitos se trouxerem o do motor, senão um molde incompleto levaria o replay direto para o **HTML da SPA com status 200** (135 KB, a armadilha que a s289 já tinha documentado). **GATES:** o `sandbox.mjs` ganhou duas peças **aditivas** — `cloneAbortado(corpo)`, que faz o `clone().text()` rejeitar com `AbortError` como o navegador faz, e `semRequisicaoInicial`, que roda o inject com a página **muda**; sem as duas o harness leria o clone de boa vontade e um inject que dependesse do passivo passaria **verde** (falso verde do tipo 2 do `CLAUDE.md`). O servidor de mentira do caso passou a devolver **HTML com status 200** para quem chamar sem o cabeçalho do motor, que é o que a casa faz. **Provado por mutação: 3 de 3 detectadas** — restaurar `if (!reqCtx) return` reproduz o sintoma dos testers *exatamente* (respostas 0, 0 bilhetes); esvaziar os cabeçalhos constantes dá 0; e remover o handler de rejeição **derruba o harness** com a rejeição não tratada. Regressão inteira verde: **23 casos, 369 bilhetes** · `audit_sharpenup` e `audit_casas` sem FAIL · `node --check` nos 2 JS · manifest 0.7.4 → **0.7.5**. **O toast mudou de conselho:** "troque de aba" saiu (deixou de ser necessário) e `respostas: 0` agora só sobra para sessão caída ou endpoint mudado. O `abortos` entrou no autodiagnóstico para o log não sugerir falha onde não há. Armadilha registrada no `docs/GUIA_CASA_SHARPENUP.md` com a prova barata: **com o hook instalado, dê F5 na tela de histórico e conte as requisições — se der zero, o passivo e o replay-aprendido estão os dois fora.** **O QUE NÃO FOI VALIDADO AO VIVO:** o replay a frio foi provado **na casa logada**, mas com sonda minha; a extensão recarregada injetando de verdade e o robô do `content.js` dirigindo o lote ainda não foram exercidos. **Erro meu de método, registrado:** varri as `Secure Preferences` dos 12 perfis do Chrome e concluí que o SharpenUp não estava instalado — **extensão desempacotada não aparece lá**, e o Feca me corrigiu com o print. O ID que eu mesmo tinha calculado da pasta (`fegjbaijnpbibkpnllfmhllapedglkda`) já provava o contrário. E `window.fetch.__suSPBW` dá `false` na casa mesmo com o hook ativo, porque o **Datadog RUM da SportingBet embrulha o `fetch` depois do nosso** — ausência do marcador não é ausência do hook. Backup em `Backups/s305-sportingbet-arranque-frio/`.)_

_Anterior: 2026-08-31 (sessão 304 — **O CSV exportado passa a levar o P/L; o TSV segue em 10 colunas.** Pedido do Gabriel no grupo de testers: *"quando a gente exporta em CSV puxa a coluna de stake, de odd mas não puxa a coluna de profit — como às vezes dá meio green/red não tem como calcular na mão"*. Meio green/red é **HW/HL**, onde o retorno é de MEIA aposta (`(stake/2)×odd + stake/2`) e ninguém refaz a conta na planilha a partir de stake e odd. **A coluna não existia porque o P/L não existe no banco:** é derivado na leitura (`repository.calcular_pl`), então o `SELECT *` do `export_bilhetes` jamais o traria. **Dois exports, uma decisão do Feca:** o CSV da Extração (`montarCSV`, `index.html`) e o `Baixar base (CSV)` (`/exportar.csv`) ganham a coluna; **o TSV NÃO** — ele é colado direto na planilha do usuário, e uma 11ª coluna não daria erro, cairia em cima do que já existe ao lado do `Resultado`. **O front não recalcula nada:** a rota `/bilhetes` já devolve `pl` pronto (`repository.py`), e um segundo cálculo em JS divergiria do banco no dia em que a regra mudasse. **Formato de arquivo, não de tela:** decimal vírgula, 2 casas, **hífen comum** — o minus U+2212 do padrão monetário é lido como TEXTO pelo Excel, e a coluna apareceria sem somar, que é a queixa original de volta. **Célula VAZIA quando o P/L não é calculável** (aposta aberta, ou vitória sem odd legível): zero ali seria "empatou", mentira diferente e pior, porque soma. Registrado no `MASTER_OUTPUT §2.1`, que é onde a próxima sessão iria conferir se a coluna extra é bug. **GATES:** `tests/test_export_pl.py` (backend, com `export_bilhetes` dublado) + `tests/js/export_csv_pl.mjs`, que **recorta** o `montarCSV`/`montarTSV` reais do `index.html` e os executa · **provado por mutação: 9 de 9 detectadas** — e a 1ª rodada teve uma mutação **mal aplicada** (o `replace` pegou o `_fmtOddDisplay`, que tem a mesma linha de `toFixed(2)`, em vez do `_plExport`): ela "escapou" sem que houvesse buraco nenhum, e refeita no alvo certo foi detectada por 3 asserções · **586 passed, 23 skipped** · `check-tokens` OK · `node --check` nos 3 blocos de script do `index.html`. **O que os testes NÃO cobrem** está no cabeçalho de cada um: o download no navegador (Blob/anchor) e o valor do P/L em si, que é `calcular_pl` e vive em `tests/test_formulas.py`. `app/static/landing.html` seguiu FORA do commit — já estava modificado quando a sessão abriu, como na s302. Backup em `Backups/csv-coluna-pl-2026-08-31/`. **Sem mudança no SharpenUp** (nada para o tester atualizar — é mudança de app, que sobe no push). **GRUPO DE TESTERS AVISADO** com o "manda" do Feca: `message_id 2376`, destino conferido por `getChat` (`Sharpen - Testers` · `-5172183099` · type `group`), nota `sharpen-exportar-csv-agora-traz-o-lucro` na home pelo mesmo ato — entrada de **novidade do painel**, sem versão de SharpenUp.)_

_Anterior: 2026-08-30 (sessão 303 — **Estrela Bet entra na captura: 5ª casa Altenar, zero linha de inject novo — e mesmo assim ela achou DOIS defeitos que nenhuma das quatro irmãs tinha mostrado.** O motor foi provado **sem credencial e sem clicar em nada**: a seção de esportes carrega `sb2frontend-altenar2.biahosted.com` com **`integration=estrelabet`**. A grafia foi **medida no banco ANTES do registro** (o defeito que matou a Jonbet na s249): `Estrela Bet` é grafia **única** — 41 bilhetes (26 do `passapano`, 15 do `Feca`), 3 contas, 1 `casas_meta`, 1 `casa_config`, **zero variantes**; round-trip nas 69 grafias de `parceiros`, 0 quebradas. A casa **já era de print**, então isto é upgrade de print para API. **Prova do motor pela UNIÃO DE CHAVES** (o método barato da Faz1bet): as **60 chaves** dos 12 bilhetes reais são subconjunto exato das **77** das quatro irmãs — **zero campo novo**. **A SUPERFÍCIE é a mais LISA das cinco**: "Ver minhas apostas" abre a tela cheia, que dispara o `widgetExpandedBetHistory` sozinha, na window de **topo** (não em iframe), com o clone passivo resolvendo — nem o molde do compacto (Betpix365) nem ensinar o operador a achar outra tela (Jogo de Ouro). **DEFEITO 1 — o que ela muda não está na tela, está no CORS.** O gateway responde `Access-Control-Allow-Origin: *` para este tenant e o navegador **recusa a chamada com `credentials:"include"` antes de ela sair**: `TypeError: Failed to fetch`, **3 de 3**, com a MESMA requisição voltando **200** sem credencial, também 3 de 3 (o XHR com `withCredentials` falha igual). **A falha é TOTAL, não parcial** — o replay inteiro passa por ali, e a mutação que restaura o código antigo mostra **8 de 12** bilhetes chegando: as resolvidas vêm pelo passivo e **as 4 abertas somem em silêncio**, porque só o replay pede a aba Aberto. Perder a credencial **não custa autenticação** (quem autentica é o `Authorization: Bearer` dos headers aprendidos, não cookie). O `pedirPagina` tenta `include` **primeiro** — o que as 4 irmãs usam hoje — e cai para a chamada sem credencial em quem for recusado, memorizando a escolha: **mudança ADITIVA, nenhuma irmã teve comportamento alterado por dedução** (não temos conta nas quatro para medir o CORS de cada tenant). **DEFEITO 2 — o dicionário deste tenant tem TAB LITERAL dentro do nome do time**: `"Real Sociedad vs. RCD Espanyol		"` e `"RCD Espanyol		"`, mais `"Mirassol  vs. Palmeiras"` com espaço duplo (o próprio menu da casa traz `"E-sports +		"`). **TAB é o separador de coluna do TSV** e a IA copia nome próprio verbatim — é a premissa do gate de fidelidade da s302. Copiado para a Descrição, empurra Stake/Odd/Resultado uma casa à direita e o `parse_tsv` lê o código do bilhete no lugar do resultado (família do bug da s193). **Nenhum gate existente pegaria:** `checar_descricao` olha forma, `checar_fidelidade` confere por substring (e o nome COM tab contém o nome sem tab) e o financeiro fica certo, porque stake/odd/resultado são copiados. Correção: `_limpoVB` no `content.js`, higienizando na FRONTEIRA. As 4 irmãs tinham nome com espaço final (`"Náutico vs. Ceará "`) e passam a sair aparadas. **ENUM NOVO: `sportTypeId 12` = `Basquete`**, provado por dois eixos independentes — todo `12` traz `sportId:67`, e o `GetHighlights` da própria casa devolve `{"id":67,"name":"Basquete"}` (com 66=Futebol e 76=Beisebol batendo com os `sportTypeId` 1 e 13 já mapeados) — mais 8 seleções de basquete real (WNBA, LNBP, CIBACOPA, FIBA Asia). **`bonus` = "SuperMúltipla"**: bônus de múltipla pago **por fora da odd**, o mesmo campo que a Betpix365 estampa como "Ganhos extra" (**o nome do selo é da marca, o campo é do motor**). No único W, `150 × 11,015269 = 1.652,29 + 75,11 = 1.727,40` exato — a odd declarada NÃO explica o retorno e a régua do dinheiro dá **11,516**. **GATES:** `casos/estrelabet.mjs` novo, com valores lidos do CARD · **provado por mutação: 14 de 14 detectadas** (incluindo a que restaura o `include` fixo e a que remove o `_limpoVB`) · regressão inteira verde: **23 casos, 367 bilhetes** · `audit_sharpenup` e `audit_casas` sem FAIL · `audit_changelog` sem FAIL · **575 passed, 23 skipped** · `check-tokens` OK · manifest 0.7.3 → **0.7.4**. O `sandbox.mjs` ganhou a sentinela **`FALHA_DE_REDE`** (aditiva) porque `null` já significa 404, e 404 é uma resposta — sem poder REJEITAR, o teste do fallback provaria só que o código compila. **VALIDADO AO VIVO com o código de produção recortado do arquivo**: a 1ª chamada é recusada (o log sai exatamente como escrito), `semCredencial` vira `true`, a 2ª volta **200**, e as duas abas fecham em `isLastPage:true` — 9 resolvidas + 3 abertas. Repare: o `5351868810` **liquidou durante a sessão** (estava `status:0` no recon e voltou `status:2`), que é a prova ao vivo do "resolvida vence aberta". **O QUE NÃO FOI VALIDADO AO VIVO:** a extensão injetando de verdade em `document_start` neste host e o robô do `content.js` dirigindo — isso exige recarregar a extensão + Ctrl+Shift+R, que é do operador. **PENDÊNCIA DE MASTER (decisão do Feca):** `Hits Mais de/Menos de (incluindo innings extra)` (baseball, total do time) **não tem gaveta** no `MASTER_APOSTAS §Baseball`, que só prevê `Corridas` (runs) e `Player Props` — hoje cai em `Outros`; criar categoria dispara a regra de propagação, que é decisão, não conserto. **Sem amostra nesta casa:** anulada (`8`), cashout executado, bet builder, boost, paginação > 1 página e eBasket — a conta tem 12 bilhetes. Backup em `Backups/s303-casa-estrelabet/`. **GRUPO DE TESTERS AVISADO** com o "pode mandar" do Feca: `message_id 2242`, destino conferido por `getChat` (`Sharpen - Testers` · `-5172183099` · type `group`), nota `su-074` na home pelo mesmo ato. **Isso encerra na prática a pendência herdada da s299d** — as notas de 0.7.0 a 0.7.3 seguem na home e nunca foram enviadas ao grupo, mas quem atualizar agora pula direto para a 0.7.4, que as contém.)_

_Anterior: 2026-08-29 (sessão 302 — **A descrição de um bilhete pode pertencer a OUTRO bilhete, e nenhum gate do sistema enxergava isso.** O Feca abriu com "problemas na extração betfair" e o print de 5 apostas em aberto. O robô mandou `Norwich x Burnley · Mais/Menos de 3,5 Cartões`; o banco tinha `Matthew Dennant [Norwich v Burnley]`, esporte **Dardos**, categoria **ML** — a seleção do bilhete VIZINHO no mesmo chunk. **Os três gates que existiam deram verde:** cobertura 65 de 65, `checar_descricao` limpo (a forma é impecável: separador certo, confronto bem formado, sem conteúdo proibido) e o financeiro correto, porque stake/odd/resultado são COPIADOS do bloco — o que viaja para o bilhete errado é só a classificação, que é o que a IA decide. **A medição do lote inteiro (65 bilhetes, nada perdido) achou 7 linhas erradas, todas da IA, nenhuma do robô:** 2 de carryover (o `1938` recebeu `Under 1.5 Rounds` de `Vai até o Final? · Não`, e o `1.5` veio do `1936`), 3 de período perdido (`Vence o 3º Set` virando ML de partida; `Total de Pontos no 3º Set` e `Total de pontos no 1º quarto` virando total do jogo) e 1 de separador decimal. **O ACHADO QUE MUDOU A CONVERSA: a IA já se corrige sozinha e o banco joga a correção fora.** A sombra registra as três leituras do `1941` na MESMA extração — a 1ª errada, as duas seguintes CERTAS — e o banco ficou com a primeira, porque o `ON CONFLICT` (`repository.py`) nunca atualiza `esporte`/`aposta`/`descricao` fora de `origem='sync'`, **nem com a linha `aberta`**, ao contrário de odd/data/stake. Recapturar não conserta; só edição à mão. **E não é da Betfair.** Rodei a conferência sobre a sombra inteira (1.337 leituras, 11 casas): os piores são **Betfast** (`301490938` e `301491163` receberam a MESMA descrição fabricada — Charlotte FC / Cruzeiro / Gold Coast — quando o bloco diz Blackburn–Middlesbrough / Inter Miami–Toronto / Internacional–Atlético-MG) e **Betnacional** (duas múltiplas **trocaram de descrição entre si** às 14:53; às 19:24 a IA acertou as duas e o banco ficou com a troca). **O GATE NOVO — `checar_fidelidade` em `app/descricao_check.py`:** a tradução não inventa NOME (traduz rótulo, canoniza separador, escolhe categoria; time/jogador/competição são cópia), então todo nome próprio da descrição tem de existir no bloco cru daquele código, e todo DECIMAL também (é a linha da aposta). Função pura, sem I/O, sem IA, microssegundos. **Precisão medida com o código que subiu, contra a sombra inteira: 1.327 de 1.337 passam (99,25 %); das 10 reprovações, 9 são erro real** — o único falso positivo é `Team Props` na 1xBet. Três tolerâncias são load-bearing e nasceram de falso positivo medido: acento agudo tipográfico (`St Patrick´s` × `St Patrick's`, Pinnacle), hífen com espaços (`Ararat - Armênia` × `Ararat-Armênia`, 1xBet) e plural (`Tiro de meta` × `Tiros de Meta`, 1xBet). **A REPESCAGEM É A CORREÇÃO, não só o aviso** (`_garantir_fidelidade` em `main.py`, espelhando o `_garantir_cobertura`): o bloco suspeito volta ao modelo SOZINHO, e bilhete sem vizinho no chunk não tem de quem copiar. **Conservadora por desenho: a linha nova só entra se ELA passar no gate** — nunca troca uma que passa por outra que passa (seria o ruído de estilo que o congelamento existe para barrar) nem certo por errado. Lote limpo não chama o modelo, então o gate é de graça no caso normal. **A 2ª CAUSA virou regra: `MASTER_DESCRICAO §12.10 — Recorte de Período`**, com o vocabulário canônico (`3º Set`, nunca `Set 3`) e a metade que carrega a regra escrita em negrito: **ausência de sufixo significa PARTIDA INTEIRA**. Sem isso, `Total de Pontos no 3º Set` e `Total de Pontos` produzem a mesma descrição. Entraram também os itens 13 e 14 na validação final do §19. O MASTER inteiro já vai no prompt de sistema, então a regra chega ao modelo sem fiação nova. **DADOS: 12 linhas corrigidas em produção** (`scripts/corrigir_descricoes_infieis_s302.py`, ensaio por padrão, snapshot ANTES em JSON no backup), pelo caminho sancionado `atualizar_bilhete` — que registra em `correcoes` e recalcularia a assinatura; ela ficou intacta nas 12, e está certo: com código a assinatura é `ID|casa|parceiro|codigo` e a descrição não entra. **7 são do Feca (Betfair/Duka) e 5 são do Gabriel (Betfast e Betnacional).** Uma armadilha evitada no ensaio: eu ia trocar `esporte = Múltiplos` por `Futebol` nos dois Betfast, e o `MASTER_ESPORTES §2.2` manda `Múltiplos` em acumulada de 3+ jogos diferentes ainda que do mesmo esporte — o ensaio pegou antes de gravar. **GATES:** `tests/test_fidelidade.py`, 19 casos, blocos **verbatim da sombra de produção** · **provado por mutação: 11 de 13**, e as 2 que escaparam foram investigadas e são **inócuas** (guarda redundante em `_garantir_fidelidade` e em `_linhas_infieis` — o código segue correto sem elas), registradas no cabeçalho do arquivo em vez de virarem asserção inventada. **A 3ª que escapou na 1ª rodada era defeito do TESTE:** a mutação que passava a cobrar número inteiro passou verde porque a conferência é por SUBSTRING e o `2` de `2º Tempo` é achado dentro de `Odd total: 2,05` — entrou um caso travando o contrato do `_RE_DECIMAL` direto. **575 passed, 23 skipped** · `check-tokens` sem FAIL · `audit_casas` sem FAIL. **O que o teste NÃO cobre está no cabeçalho dele:** a chamada real ao modelo (a repescagem é substituída por roteiro — o que se prova é a DECISÃO de trocar, não que o modelo acerta na 2ª vez, que está medido na sombra); troca entre bilhetes que compartilham os mesmos nomes (passa no gate, e é limitação declarada); e rótulo traduzido para a categoria errada, onde nenhum token é estranho ao bloco. **PENDENTE, decisão do Feca:** sobraram 2 linhas reprovando, as duas da mesma família — Bet365 `KS5481466811I` (`Menos de 4.0,4.5` virou `Under 4,25`) e `GS1351447551I` (virou `-0,25`): a IA calcula a MÉDIA de uma linha asiática PARTIDA. Não corrigi porque escrever `Under 4.0,4.5` exige um template novo no `MASTER_DESCRICAO`, e formato é decisão, não conserto. **Não mexi no congelamento do UPSERT** — com a repescagem consertando antes de salvar, deixar a re-leitura sobrescrever virou opcional, e é mudança de outra natureza. **`app/static/landing.html` ficou FORA do commit: já estava modificado quando a sessão abriu, 569 linhas que não são minhas.** Backup em `Backups/s302-fidelidade-descricao/`. **Sem mudança no SharpenUp; grupo de testers não avisado.**)_

_Anterior: 2026-08-28 (sessão 301 — **Fase 1 do tradutor determinístico entregue, DESLIGADA, e a primeira medição diz que ele erra menos que a IA.** O Feca: *"se tiver base, manda a ver no plano, vamos seguir"*. A base existia: a sombra da s297 juntou **877 linhas / 2.407 pares** (linha bruta → descrição canônica) em 2 dias, 10 casas, com pareamento de 96–100 %. O custo dos últimos 30 dias confirma a ordem do plano — **Bet365 = 38,4 %** (US$ 88,37 de US$ 230,25); seis casas cobrem 80 %. **Nasce `app/tradutor.py`:** motor puro, sem I/O, que traduz o bloco do inject nas três decisões que hoje custam IA (esporte, categoria, descrição) e copia o resto. **Invariante única: nunca inventa** — na dúvida devolve `ok=False` com o motivo e AQUELA linha vai para a IA. **Não está ligado em lugar nenhum**; a virada é a Fase 3, com gate de < 1 % em ≥ 500 bilhetes. **Medição contra a sombra inteira** (`scripts/diff_tradutor.py`, leitura pura, zero chamada de API): cobertura **84,1 %** (58 de 69) e, dos traduzidos, **esporte 0,0 % · aposta 1,7 % · descrição 12,1 %** de divergência. **As 8 divergências foram lidas uma a uma na linha crua e NENHUMA é defeito do tradutor.** Cinco são a IA escrevendo `Mais de 85.5 Pontos` em eBasket, violando o `MASTER_DESCRICAO §11` (converter para inglês é **obrigatório**); duas são localização de nome de time (`USA (W)` × `EUA (F)`) que **a própria IA faz de dois jeitos no mesmo dia** — o tradutor copia verbatim e a decisão é humana; e a de categoria é `Partida - Handicap (Pontos)` saindo `Pontos` em 1 de 4 amostras idênticas, contra `Handicap` nas outras 3 e contra o `§9` da casa. **Duas rodadas de diff consertaram o que era nosso:** handicap de Sets/Games leva a unidade no texto (`EUA -1.5 Sets` — `MASTER_DESCRICAO §12.6` e `§13.4`) e mercado ao vivo prefixa a seleção com o placar (`(0-0) Time -0.5`), que é estado do jogo e sai fora — a descrição caiu de 20,7 % para 12,1 %. **LIMITE MEDIDO, e ele muda a projeção: as 58 traduzidas são TODAS de perna única.** Nenhuma múltipla passou — rótulo genérico (`Totais do Jogo`) precisa do esporte para decidir o objeto, e numa múltipla de esportes misturados o inject não emite `Esporte (casa)`; deduzir pela linha do total (`154.5` "parece" basquete) seria exatamente o que este módulo não faz. Na Bet365 o preço disso é baixo (61 dos 69 são de perna única), mas **a economia projetada vale hoje para o bilhete simples, não para a múltipla**. **GATES:** `tests/test_tradutor.py`, 16 casos, blocos **verbatim da sombra de produção** — inclusive o espaço duplo de `Mais de  2.5` e o placar ao vivo · **provado por mutação: 10 de 10 detectadas** em duas rodadas, e a 1ª rodada achou um buraco real (contar pernas em vez de confrontos distintos passava **verde**, porque não havia bet builder na suíte; entrou o caso, e ele é o **único construído** do arquivo, marcado como tal, porque a sombra ainda não capturou um `Criar Aposta` de Bet365) · **553 passed, 23 skipped** na suíte inteira. **O que o teste NÃO cobre está escrito no cabeçalho dele:** não prova concordância com a IA (isso é o `diff_tradutor.py`, medição contínua), não cobre odd/stake/data além da cópia literal — onde a odd exige produto ou `Retorno ÷ Stake` o bilhete cai no fallback de propósito — e não conhece casa além da Bet365. **PENDENTE, decisão do Feca:** (1) localizar nome de time na descrição ou copiar verbatim, já que a IA faz os dois; (2) 9 rótulos que a sombra viu e o `CASA_BET365 §9` não lista entraram no mapa marcados `# sombra` e querem virar linha do §9; (3) a Fase 3 pede 500 bilhetes de Bet365 e a sombra tem 69 — a ~35/dia, o gate fecha em ~2 semanas. **ADENDO (mesma sessão, sombra 4× maior):** a sombra pulou de 69 para **284** bilhetes de Bet365 enquanto a sessão rodava, e tudo melhorou — cobertura **94,7 %** (era 84,1 %), esporte **0,0 %**, aposta **0,7 %**, descrição 15,6 %. **E a classificação das 42 divergências de descrição derruba o gate como o plano o escreveu:** 19 são a IA trocando ponto por vírgula no número (`Over 2,5 Gols`), 13 são a IA não normalizando `Mais de` → `Over`, 1 é a IA **calculando a média** de uma linha asiática partida (`4.0,4.5` → `4,25`), 2 são o hífen no nome do time (`PSV - Reservas` → `PSV Reservas`) e **só 2 são localização de nome** (`USA (W)` → `EUA (F)`). O golden set decide ponto × vírgula **7 a 0** e o `MASTER_DESCRICAO §11` obriga o `Over`. **Logo, "divergência < 1 % contra a IA" é inatingível por construção: a IA diverge do MASTER em ~13 % dos bilhetes.** O gate precisa passar a medir contra o MASTER/golden set, ou por triagem das divergências — decisão do Feca. Entrou a primeira família de rótulo **parametrizado** (`Jogador - <objeto> - Alternativas` → Player Props, objeto saindo do próprio rótulo, autorizado pelo §9); ela ainda não move a cobertura porque o único bilhete que a contém traz junto um rótulo desconhecido — fallback é por bilhete, não por perna. **Achado que vira pendência de MASTER: o sufixo de período na descrição (`… Cartões 2º Tempo`) não existe em nenhum dos 6 MASTERs** — a IA o escreve num bilhete e come o `Prorrogação` em outro. **Mutações: 13 de 13** no total da sessão · **556 passed, 23 skipped**. **Betano avaliada e NÃO iniciada:** 87 rótulos distintos em 493 pernas (contra 20 em 79 da Bet365), com estado embutido no rótulo (`Handicap Asiático (Resultado atual 0 - 0)`), número de set, nome de time dentro do rótulo e um `Criar Aposta` aninhado que o parser nem lê — é **gramática de rótulo, não tabela de-para**, e merece incremento próprio. Backup em `Backups/s301-tradutor-fase1/`. **Sem mudança no SharpenUp; grupo de testers não avisado.**)_

_Anterior: 2026-08-27 (sessão 300 — **Nenhuma coluna de Fornecedores & Parceiros ordenava certo, e eram TRÊS causas independentes — todas mudas.** O Feca: *"nenhum desses filtros tá funcionando direito... não ordena nada da forma correta, nem datas, nem financeiro, ROI, nada"*. O sintoma engana porque **a tabela reordena** — só que errado; nada aparece no console. **(1) O menos do padrão monetário é U+2212 (`−`), não hífen ASCII.** `fmtPL` e `fmtPct` o emitem por regra de marca (UI_REFERENCE §5), o `parseNum` mandava direto ao `parseFloat`, que devolvia `NaN` → 0 — então **todo P/L e todo ROI negativo era ordenado como zero** e empilhava num bloco no meio da lista, com o mais negativo indistinguível do zerado. **(2) `fmtR` imprime inteiro sem decimal (`R$ 5.180`), e a regra antiga de milhar só tirava o ponto quando vinha vírgula depois** (`/\.(?=\d{3}[,\.])/`). Sem vírgula, `5.180` virava **5,18** — e a conta de **R$ 80 subia ao topo do Turnover**. Ordenar o resto "quase funcionava" por acaso: todo valor com um grupo de milhar era dividido por mil na mesma proporção, então o defeito só aparecia contra números pequenos. **(3) As duas colunas de data saem em `dd/mm/aa` e não eram numéricas — ordenavam como TEXTO, ou seja, pelo DIA DO MÊS.** `24/05/26` vinha depois de `09/08/26`. **As correções:** `parseNum` limpa a moeda **por subtração** (sobra dígito, ponto, vírgula e sinal) e decide o papel do ponto **pela FORMA do número** (`^\d{1,3}(\.\d{3})+$`), nunca pelo que vem depois dele · as datas passam a mandar por `data-sort` em ISO, que o `sortTable` já lia antes do `textContent` · a Casa ganhou `data-sort` também, porque o chip de inicial injeta uma letra a mais no `textContent` das casas sem favicon (`R7` virava `RR7`) · e o `localeCompare` do texto virou `pt-BR` com `sensitivity:'base'` e `numeric:true`, senão a caixa parte a lista em dois blocos (`MichelCleiton` longe de `maysacarol01`) e `conta10` vem antes de `conta2`. **O `parseNum` é compartilhado: o conserto vale para as 17 tabelas ordenáveis do dash**, não só esta — qualquer coluna de P/L, ROI ou Turnover em Esportes, Tipsters, Bookies e nos drills estava com o mesmo defeito. **GATES:** `tests/js/sort_tabelas.mjs` novo, recortando `parseNum`, `sortTable` e o construtor de linhas dos arquivos de PRODUÇÃO (teste que reimplementa não detecta a mutação que o quebra) · **provado por mutação: 11 de 11 detectadas** — menos tipográfico, milhar sem decimal, sinal perdido no retorno, `data-sort` ignorado, `localeCompare` sensível a caixa, `total-row` fora do fim, seta em todas as colunas, `data-sort` ausente na data e na casa, 1ª Aposta com a data errada, colunas numéricas trocadas · `tests/test_sort_tabelas.py` amarra o gate no CI · **532 passed, 23 skipped** · `check-tokens` sem FAIL · cache-bust `app.js?v=39` e `gestao.js?v=35`. **E a tela foi ABERTA NO CHROME antes do commit** (a regra da s296): puppeteer contra o `servidor_demo.py`, clicando os cabeçalhos de verdade — 9 de 9 conferências verdes em Turnover asc/desc, Profit desc com o mais negativo por último, ROI, as duas datas, Período e Conta. **O que o teste dublado NÃO cobre está escrito no cabeçalho do `.mjs`:** o `onclick` real, o resize de coluna e o CSS da seta. **Achado de lambuja, NÃO corrigido (uma mudança por vez):** no `servidor_demo`, o primeiro `location.hash` para `dash/parceiros` roda `renderParceiros` **antes** de a página montar e estoura `Cannot set properties of null` no `#fornTable` — medido idêntico com o `gestao.js` do backup, então é **pré-existente e não veio desta sessão**. No demo o bounce disfarça; em produção vale investigar se a corrida existe. Junto disso: o `makeSortable` instala o `onclick` num `setTimeout` de 100 ms, então há uma janela curta em que o cabeçalho está na tela e não é clicável — foi o que fez a primeira rodada do harness reprovar só na primeira coluna. Backup em `Backups/s300-sort-tabelas/`. **Sem mudança no SharpenUp; grupo de testers não avisado** — aguarda decisão do Feca.)_

---

## Sessão 335 — três casas novas na captura

### Três casas novas no SharpenUp, e um motor novo: **Rogue**

Betão, R7 e 7Games são espelho de verdade. Rodam a mesma plataforma, servida do **próprio
domínio da casa** em `/api/sportsbook/rogue/…`, como a Novibet. Não é Altenar, não é BetBy,
não é Kambi, não é BetConstruct. Um `rg_inject.js` e um `formatTicketRG` servem às três.

A irmandade foi medida antes de escrever código: mesma stack Next.js, mesmo conjunto de
hosts, mesmo mapa de endpoints extraído dos bundles das três, mesma rota de histórico
(`/account/sports-history`), mesmos campos.

**O contrato:**

```
GET /api/sportsbook/rogue/v1/betsreporting/purchases
    ?status=all&take=<1..100>&skip=<n>&locale=br-pt&fromDate=<ISO>&toDate=<ISO>
    header: authorization: Bearer <JWT da sessão>
→ {"Purchases":[…], "PurchasesCount": <total da janela>}
```

`take` tem teto de 100 e a casa **diz** o limite (`ErrorCode 2003`) em vez de truncar calada.
`PurchasesCount` é o fim autoritativo da paginação por `skip`.

### A semântica saiu do dinheiro, não do rótulo

A API manda enum numérico puro. O de-para foi provado em **27 de 27** bilhetes das três
contas:

| `BetStatusId` | `CurrentBetBalance` | → |
|---|---|---|
| 0 | `0` e sem `Result` | aberta |
| 1 | `0` | L |
| 2 | `= stake × odd` | W |
| 4 | `= stake` exato | V |

**A armadilha central é o `Gain`:** ele é o retorno POTENCIAL e vale `stake × odd` em 27/27,
inclusive em perdida e em aberta. O realizado é `CurrentBetBalance`. Quem lê o campo óbvio
marca toda perda como ganho: é o `totalWin` da VaideBet (s210) e o `finalFinancials.payout`
da Novibet (s271), com o terceiro nome de campo.

### Dois achados que mudaram o código

**A tela é ESTREITA.** O histórico abre em "Últ. 24 horas" com `take=10`. No dia do recon, o
filtro de 30 dias do Betão devolvia `PurchasesCount: 0` numa conta com 9 bilhetes. Um
passivo puro pareceria funcionar (hook ativo, respostas > 0) e entregaria quase nada. O
replay alarga para 36 meses e pede `status=all`.

**O Bearer EXPIRA.** Achado testando o inject contra a casa real: token de ~1h responde
**401**, não 403. A primeira versão guardava só a PRIMEIRA requisição, então numa aba aberta
desde a manhã o replay sairia com token vencido e voltaria vazio, com 401 e "endpoint mudou"
lendo igual no painel. Agora o contexto é renovado a cada busca da página, e há gate travando
isso nos dois sentidos (sobrescrever com token melhor, nunca com token nenhum).

### A gêmea `r7.bet` foi unificada ANTES do registro

A base decidiu, não a marca: `R7` tinha 40 bilhetes de 2 donos, 3 contas e 17 correções,
contra 1 bilhete e 2 contas em `r7.bet`, que é um domínio cadastrado à mão. Na ordem inversa,
o bilhete do Jaao26 ficaria numa casa que a conta dele não enxerga: grade vazia, sem erro
nenhum, o defeito da s249. Aplicado com `--somente r7.bet`, 1 bilhete e 1 assinatura
recalculada, 10 outras linhas, zero colisão. Round-trip nas 94 grafias de `parceiros`: 0
quebradas antes e depois.

### O gate pegou um defeito meu antes de subir

`_casaConectavel()` normalizava espaço mas não ACENTO, e a chave é `BETAO` enquanto o display
é `Betão`. O botão "Conectar" nasceria desabilitado: o bug da s191 na terceira encarnação
(s256 foi o espaço). Corrigido na raiz com `normalize('NFD')`, medido antes de mudar: nas 31
grafias de display conhecidas, zero mudança de comportamento.

### Gates

Harness **26 casos / 428 bilhetes**, `audit_sharpenup` 31 casas sem FAIL nem WARN,
`audit_casas` limpo, `check_docs` sem âncora quebrada, check-tokens verde, **772 passed**.

**Mutação: 12 de 12 detectadas.** Duas escaparam de primeira e as duas eram buraco de TESTE,
não de código: a regra "data da perna mais recente" não é exercível por fixture nenhuma
(todos os 27 bilhetes são de uma perna só) e nada disparava requisição sem `authorization`.
As duas viraram caso próprio.

### O que NÃO foi coberto

As 27 apostas são **todas simples**. Sem múltipla, sistema, cashout, freebet, bet builder ou
meia-liquidação: `BetTypeId` 1, `ComboSize` 0 e `NumberOfLines` 1 em 27/27, `AdditionalTickets`
vazio em todos, `PromotionIds` vazio em todos. Os endpoints `/v1/cashout/*` existem no bundle
e nenhum bilhete passou por eles. Está registrado como **não medido** nos três `CASA_*.md`,
não como resolvido.

### Próximo passo

**Fase 7, que só o operador faz.** Recarregar a extensão, dar Ctrl+Shift+R na aba de cada
casa, F5 no dashboard, conectar e conferir contagem, datas, odds e código. A validação ponta
a ponta com a extensão carregada é a única coisa que o harness não alcança: o hook precisa
rodar em `document_start`, antes de o bundle capturar o `fetch`.

Quando aparecer a primeira múltipla ou o primeiro cashout numa das três, a fixture volta para
`extensor/harness/fixtures/` e o caso trava a leitura nova.

---

---

---

_Anterior: 2026-09-09 (sessao 336: **Fase 0 da BARREIRA DE RECAPTURA no ar, e o estudo de custo remedido por usuario e por casa.** Origem: pergunta do Feca — extrair as ultimas 48h e repetir 2h depois paga hoje pelos MESMOS bilhetes, porque toda captura vai inteira para a IA e a dedup so acontece DEPOIS, no upsert. **Medido sobre 15.318 blocos reais da sombra (13 dias, 21 casas): 32,5% de tudo que pagamos e releitura de bloco IDENTICO**; na Bet365 e 39,9%. Alcance quase total: 99,3% dos bilhetes de extracao tem codigo. **A chave e o HASH DO BLOCO, nao o par (codigo, resultado) que seria o obvio:** as duas decidem igual em 97,7% dos casos e nos 2,3% restantes o bloco mudou COM o `Status:` igual, entao a chave por rotulo pularia e perderia a mudanca. Alem disso o texto de status nao e fonte confiavel de estado (`_resultadoB3` escreve `Ganho → W` para QUALQUER retorno maior que a stake, meia vitoria inclusive) — comparar bytes nao herda esse defeito porque nao interpreta nada. E liquidar nao mexe so no status: a odd muda junto, de potencial para `Retorno ÷ Stake`. **Simulado lote a lote e VALIDADO contra a conta real (erro +4,5%): −29,3% da conta, R$ 0,092 → R$ 0,065 por bilhete.** **Velocidade quase nao muda** e isso esta escrito no plano para ninguem prometer o que nao vai acontecer: a mediana fica em 30,5s (os pedacos ja correm em paralelo, o relogio e UM pedaco vezes o numero de ondas), so o p99 cai 43,7%; o ganho de verdade e a extracao que fica VAZIA, 30s viram menos de 1. **Esta fase NAO FILTRA NADA** — tabela `bloco_visto`, gravacao do hash no `done` e um log dizendo quantos blocos SERIAM pulados, para conferir o numero em producao antes de qualquer byte deixar de ser processado. **O custo remedido por usuario e por casa mostrou o driver unico:** o custo por bilhete e quase inteiramente funcao de BILHETES POR CHAMADA, porque o manual de 48k tokens e relido a cada pedaco. perereca faz 55,9 bilhetes/chamada e paga R$ 0,037; Marques19981 faz 2,4 e paga R$ 0,414. **E a Bet365 NAO e cara, ela e grande:** R$ 0,080/bilhete, ABAIXO da media de R$ 0,092 e a mais barata entre as casas de volume. A cara e a KTO, R$ 0,429 com 1,7 bilhete por chamada. **Gates:** 11 testes novos, 783 passed / 30 skipped, mutacao provada por fora (hash constante derruba 4 casos, restaurar devolve o verde) e uma mutacao INOCUA registrada como tal em vez de disfarcada. A s335 rodou em PARALELO, noutra sessao.)
