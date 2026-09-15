# PLANO — Custos numa tela única

> Substitui `Custos de Contas`, `Custo de Tipsters` e `Fornecedores & Parceiros` por uma
> tela só. Nasceu do relato do Feca na s348: *"todas essas páginas eu como dono do site
> não tô usando, e isso significa q elas são péssimas. Desorganizadas, difíceis de
> preencher os dados (…) falta ela entregar oq realmente ela foi feita pra fazer"*.
>
> Estado atual → [`../STATUS.md`](../STATUS.md) · o que está aberto →
> [`../BACKLOG.md`](../BACKLOG.md) · regras → [`../CLAUDE.md`](../CLAUDE.md).

---

## A forma, cravada pelo Feca

Uma tela, `Custos`. **Topo fixo**: a barra de filtros do sistema (Período composto com as
peças do `filters.js`, mais Casa e Fornecedor), quatro KPIs com o selo de cada bloco, a
cascata do bruto ao líquido em fita, e o aviso do que falta **dizendo de qual mês**.
**Quatro abas** por baixo: `Contas · Tipsters · Gerais · Raio-X`.

Decisões que vieram junto e não se rediscutem sem ele:

- **A decisão sobre a casa não mora aqui.** *"A operação na Super vale a pena?"* é pergunta
  de casa e vai para **Bookies**, que já é por casa. Custos lança e confere, não julga.
- **Não se compara durabilidade entre fornecedores.** *"bet365 eh bet365 e super eh super,
  não faz sentido comparar a durabilidade entre os fornecedores (…) nós não somos quem vai
  falar q joão dura mais q francisco."* A informação aparece; o veredito não.
- **`% do lucro` e staking são RÓTULO, não motor.** *"o usuário apenas imputa o valor."* O
  percentual combinado fica registrado para a tela lembrar; o valor do mês é digitado.
- **Contas e assinaturas nunca lado a lado**, mesmo na mesma página.
- O antigo "Extrato da operação" chama-se **Raio-X**, no vocabulário da marca.
- As três telas antigas **saíram do menu na s358** (decisão do Feca em 14/09/2026). Saíram
  do MENU, não do código: seguem alcançáveis por hash direto (`#dash/custos`), o que mantém
  a volta a uma linha. Remover o código é passo seguinte, quando ele confirmar que não
  sentiu falta — e exige cuidado, porque `_ctTipsters`, `_ctSituacao`, `_ctSugestao` e
  `buildCostState` são lidos pela tela nova.
- **A tela nova deixou de se chamar "Custos (prévia)"**: com as outras fora do menu, ela é
  a única de custo, e o rótulo "prévia" passaria a descrever o produto inteiro.

## Como o custo se comporta, por família

| Família | Natureza | Repete no mês seguinte? |
|---|---|---|
| Conta | valor único, pago na compra | não |
| Tipster · mensalidade | recorrente | **sim**, traz o mês anterior para aceitar num clique |
| Tipster · staking (% do lucro ou R$/unidade) | variável | **não**, o campo nasce vazio |
| Tipster · temporada | valor único que cobre um período | não pede nada até vencer |
| Geral · mensal | recorrente | sim |
| Geral · variável ou avulso | variável | não |

**Fornecedor tem tabela de preço com vigência.** Preço por fornecedor e casa, com a data em
que passou a valer (*"em agosto subiu o preço, ou fiz um deal melhor"*). Conta nova nasce
com o preço vigente na data da compra; **editar o valor de uma conta vale só para ela**, e
a conta fica marcada como editada. Conta já comprada mantém o preço que tinha.

## ✅ A régua única foi decidida: LANÇAMENTO (s358)

Decisão do Feca, com os números na mesa: *"não posso pagar uma conta duas vezes; se paguei
em agosto, ela pertence a agosto"*. **As duas telas medem a mesma coisa desde a s358** — o
que saiu do bolso no recorte. A janela de vida não morreu: ela virou o **parque**, número
de ESTOQUE que aparece na Visão Geral com rótulo próprio e **fora do P/L**.

| Onde | Régua | Responde |
|---|---|---|
| Visão Geral (`calcCostFiltered`) | **lançamento** | quanto eu PAGUEI no recorte |
| Custos (`charts/custos2.js`) | **lançamento** | idem |
| Parque (`calcParqueFiltered`) | **janela de vida**, sempre HOJE | quanto vale o que está rodando |

O que fez a decisão: a régua de vida **não somava**. Na base do Jonathan, os meses de maio a
setembro davam R$ 39.800 contra R$ 28.400 realmente pagos — e setembro cobrava 10 contas
tendo ele comprado uma. Detalhe no `CLAUDE.md` ("Custo pertence ao dia em que o DINHEIRO
SAIU") e o caso em [CASOS.md](CASOS.md#as-10-contas-que-cobraram-em-setembro-e-uma-foi-comprada--jonathan-s358).

## Fatias

| # | O que é | Estado |
|---|---|---|
| **0** | **Prévia só-leitura**: a tela montada de verdade, lendo `custoData`, `ctData`/`cgData` e `_contasVida`. Zero escrita, zero estrutura nova. | **no ar (s348)** |
| **1** | Tabela de preços do fornecedor: fornecedor × casa × valor × `vigente_desde`, em `fornecedor_preco`. Espelhada em `custo_conta` a cada escrita, para as telas antigas seguirem certas. Sem backfill: preço herdado lê como "sem data". | **no ar (s348)** |
| **2** | Custo sai do par `fornecedor\|\|casa` e vai para a **conta**: `parceiros.custo`, NULL = herda do fornecedor. Sem backfill, então o total não se move por construção (medido: 29.400 antes e depois). A derivação de três camadas mora no `gestao.js`. | **no ar (s352)** |
| **3** | Tipster ganha **tipo de cobrança** (`custo_store.custo_tipster_meta`) e o arrasto por tipo; a aba passa a gravar o valor do mês. Temporada tem prazo (`ate`). | **no ar (s352)** |
| **4** | Gerais ganha **categoria** (três de fábrica mais as do dono, derivadas das próprias linhas) e **recorrência**, que decide o arrasto pela mesma `_arrasta` do tipster. A aba passa a gravar. | **no ar (s352)** |
| **5** | **Bookies** recebe custo e P/L líquido por casa. As três telas antigas saem do menu. | **menu feito (s358)**; Bookies aberta |

## O que a Fatia 0 já ensinou

- **O screenshot headless com `--virtual-time-budget` dá falso vazio.** Ele dispara antes do
  encadeamento `contasLoad + ctLoad + tipstersCadastroLoad`, e a primeira foto mostrou a
  página em branco com o código certo. A prova válida é no Chrome de verdade, medindo
  `getComputedStyle` e os totais dentro do **iframe** do dash (a casca redireciona `/` para
  `/app`, então o contexto que interessa nunca é o do topo).
- **Três defeitos passaram pelo `node --check` e pelo `check-tokens` e só a tela aberta
  pegou:** o `.money` é largura de coluna e quebra a linha quando posto dentro de uma frase;
  dinheiro dentro de um eyebrow de 9,5px joga o `.money-sign` para 7,2px, abaixo do piso da
  Escada; e um rodapé que somava o período enquanto a tabela mostrava o mês.

## O que a Fatia 1 ensinou

- **Duas formas do mesmo dado, nunca duas fontes.** `fornecedor_preco` é a fonte;
  `custo_store.custo_conta` virou vista derivada, reespelhada na mesma transação. Foi o
  que permitiu a tela nova escrever sem quebrar as três antigas, que seguem no ar.
- **Não se inventa data para preço antigo.** O `custo_conta` que já existia não tem
  vigência, e carimbar uma seria dado derivado por estimativa. Preço herdado lê como
  "sem data" até o dono registrar o primeiro degrau.
- **O rótulo tem de sair da mesma régua que decide o número.** Com um preço agendado para
  o futuro, derivar "vigente" de *tem alguém mais novo na lista* marcava o preço atual
  como encerrado. Duas réguas para a mesma pergunta divergem no primeiro caso de borda.

## O que a Fatia 2 ensinou

- **Sem backfill não é preguiça, é o conserto.** Preencher toda conta com o preço de hoje
  transformaria cada uma em exceção e congelaria a herança: no dia do reajuste nenhuma
  acompanharia. `NULL = herda` mantém o total parado e a herança viva.
- **A derivação mora junto do consumidor canônico.** `_custoDaConta` vive no `gestao.js`,
  ao lado do `_custoNaJanela`, e o histórico de preço desceu junto para o feed. Régua na
  tela faria a Visão Geral medir por outra.
- **Recorte por âncora: a âncora de FIM tem de ser a função seguinte.** Usar um comentário
  de seção lá adiante engoliu quatro funções, com sintaxe válida e erro só no navegador.
- **Função com o mesmo nome em dois arquivos não dá erro em JS**: o último declarado vence,
  em silêncio. Ao mover uma função de casa, grepe o nome antes de terminar.

## O que a Fatia 3 ensinou

- **Vazio não é um tipo, é a ausência de resposta.** "A definir" não pode arrastar como
  mensalidade, senão a tela preenche sozinha o mês de um tipster que ninguém classificou.
  É a mesma família do `else` que vira "a conferir" no de-para de rótulo.
- **Estado que cobre o futuro precisa de prazo.** Marcar "temporada" sem `ate` cobria o
  tipster para sempre depois do primeiro pagamento, em silêncio. Sem o campo na tela, a
  decisão não era do dono: era efeito de não haver onde digitar.
- **A mesma coluna pode ter papéis diferentes por linha.** O mês anterior é uma oferta
  clicável na mensalidade e só referência no staking, e dizer isso na própria célula
  ("não repete") é o que impede o clique errado.
- **Gate estrutural para o "outro lugar".** O tipo mora na chave-nome, então o rename tem
  de movê-lo. Um teste que lê o corpo de `renomear_tipster` custa nada e pega a regressão
  que não dá erro.

## ⚠️ «Tudo» tem de significar tudo

Defeito **medido**, comparando a tela antiga com a nova sobre o mesmo dado: com
«Tudo» ativo a aba Contas somava R$ 0 e a antiga somava R$ 29.400. A causa não era o
dado, era o recorte —  caía no mês corrente quando  devolve
, e  é justamente o que «Tudo» devolve. O rótulo prometia a série inteira
e o número entregava um mês, sem erro nenhum.

Agora «Tudo» começa no **primeiro custo que existe** (compra de conta, mês de custo de
tipster ou de geral) e vai até hoje. Gate: , 8 de 8
mutações detectadas.

**Sintoma para reconhecer isto noutra tela:** um botão de período ativo cujo número não
muda ao alternar com o vizinho. É a mesma família do selo do degrau e da máscara do
P/L: rótulo e número discordando em silêncio.

## O que a Fatia 4 ensinou

- **Regra com dois donos se escreve uma vez.** O arrasto passou a valer para tipster e
  para custo geral, então virou `_arrasta(tipo)`. Dois `if` com a mesma regra divergem no
  dia em que um terceiro tipo aparecer, e ninguém descobre pelo erro: descobre pelo número
  preenchido sozinho.
- **Lista derivada não tem órfão.** Uma categoria existe porque alguma linha a usa. Não há
  cadastro para manter, nem categoria vazia sobrando depois que a última linha sai.
- **Linha nova nasce sem classificação, de propósito.** Um default `mensal` faria a linha
  começar a arrastar um valor que ninguém classificou — a mesma armadilha do "a definir"
  da Fatia 3.
- **Mutação inócua existe e se registra.** A guarda `typeof cgData !== 'undefined'` em
  `_cgLinha` sobrevive à mutação porque o código segue correto sem ela. Está anotada no
  gate como redundância medida, não como buraco de teste.

## Fonte canônica

`app/database.py` (`fornecedor_preco`, `parceiros.custo`, `custo_store.custo_tipster_meta`) · `app/repository.py` (`_preco_vigente_em`, `registrar_preco_fornecedor`, `_espelhar_custo_conta`) · `app/main.py` (rotas `/custos/fornecedor`) · `tests/test_fornecedor_preco.py` (gate, 10/10 mutações) ·
`app/static/dash/assets/js/charts/gestao.js` (`_custoDaConta`, `_precoVigenteEm`, `_custoNaJanela` — a derivação canônica do custo; `_arrasta` — a regra do arrasto, compartilhada; `_ctSugestao`/`_ctSituacao` e `_cgSugestao`/`_cgSituacao`/`_cgCategorias`) ·
`app/static/dash/assets/js/charts/custos2.js` (render e regras do recorte) ·
`app/static/dash/assets/css/components.css` (bloco `.c2-*`) · registro da página em
`app/static/dash/assets/js/app.js` **e** `app/static/app.html`, que são as duas cascas.
