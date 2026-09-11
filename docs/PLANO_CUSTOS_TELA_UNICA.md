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
- As três telas antigas **ficam no menu até a Fatia 5**, porque a prévia não grava.

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

## ⚠️ Duas réguas de custo convivem hoje

| Onde | Régua | Responde |
|---|---|---|
| Visão Geral (`calcCostFiltered`) | **janela de vida** | quanto de custo está VIVO no recorte |
| Custos (`charts/custos2.js`) | **lançamento** | quanto eu PAGUEI no recorte |

As duas estão certas. Sem rótulo, uma parece defeito da outra — é o caso
[os dois números certos que pareciam defeito](CASOS.md#os-dois-números-certos-que-pareciam-defeito),
e a saída foi a mesma: a tela **diz o corte** (`.c2-corte`). **Qual vira a régua única é
decisão da Fatia 2**, e é decisão do Feca, não de implementação.

## Fatias

| # | O que é | Estado |
|---|---|---|
| **0** | **Prévia só-leitura**: a tela montada de verdade, lendo `custoData`, `ctData`/`cgData` e `_contasVida`. Zero escrita, zero estrutura nova. | **no ar (s348)** |
| **1** | Tabela de preços do fornecedor: fornecedor × casa × valor × `vigente_desde`. Conta nova nasce com o preço vigente. Nada é apagado. | aberta |
| **2** | Custo sai do par `fornecedor\|\|casa` e vai para a **conta**. Migração com backup, script com ensaio por padrão, e prova de que o total do KPI não se move. Aqui se decide a régua única. | aberta |
| **3** | Tipster ganha **tipo de cobrança** e o arrasto por tipo. A grade de 6 meses sai. | aberta |
| **4** | Gerais ganha **categoria** (três de fábrica mais as que o Feca criar) e recorrência. | aberta |
| **5** | **Bookies** recebe custo e P/L líquido por casa. As três telas antigas saem do menu. | aberta |

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

## Fonte canônica

`app/static/dash/assets/js/charts/custos2.js` (render e regras do recorte) ·
`app/static/dash/assets/css/components.css` (bloco `.c2-*`) · registro da página em
`app/static/dash/assets/js/app.js` **e** `app/static/app.html`, que são as duas cascas.
