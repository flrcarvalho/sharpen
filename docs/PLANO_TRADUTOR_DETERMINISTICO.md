# PLANO — Tradutor determinístico + estudo de custo e viabilidade

> **Status:** plano proposto em 2026-08-25 (sessão 295).
> **As correções A e C do §V já foram APLICADAS nesta sessão** (TTL de cache de 1h + aquecedor
> a cada 55 min + preço do `cache_write` ajustado; escalonamento do 1º chunk). **A correção B
> está BLOQUEADA** por um achado — ver §IV.6. As fases do tradutor (§II.4) seguem **não
> iniciadas**.
> Todos os números vêm de medição direta: Postgres de produção (`uso_tokens`, `bilhetes`,
> `correcoes`), `messages.count_tokens` da API Anthropic, e `git log` do repositório.
> Janela de custo: 30 dias (25/07–24/08/2026) · janela de casa: 60 dias · PTAX 24/08 = **R$ 5,1512**.
>
> **Decisão que este plano sustenta:** tirar a IA do caminho principal da captura, para que o
> custo pare de depender de como o usuário usa o produto.
>
> Companheiro: [`ESTUDO_PRECIFICACAO_2026.md`](ESTUDO_PRECIFICACAO_2026.md) (a escada de preço) ·
> [`SHARPENUP_ARQUITETURA.md`](SHARPENUP_ARQUITETURA.md) (o mapa do sistema atual).

---

## PARTE I — O diagnóstico, em uma página

### I.1 O problema não é o preço da IA, é onde ela está

Hoje toda captura passa por aqui:

```
extensão lê a API da casa → monta um bloco de texto → IA → tabela TSV → banco
```

Custo medido de uma leitura: **R$ 0,66 de pedágio fixo + R$ 0,03 por aposta**. O pedágio é o
prompt de sistema — 44.593 tokens de masters mais 5.000–11.000 do arquivo da casa — sendo
carregado **uma vez por pedaço**, com média de 3,1 pedaços por leitura.

Isso cria um produto que fica mais caro quanto mais o cliente usa. É o defeito estrutural: não
existe forma de vender assinatura de um serviço cujo custo marginal sobe com o engajamento.

### I.2 O robô já resolveu quase tudo antes da IA entrar

Bloco real que o `content.js` emite hoje (Pinnacle, `formatTicketPN`):

```
[Código: 3088982702]
Data: 14/08/2026
Apostado em: 13/08/2026
Stake: R$ 250,00
Status: Ganho (WON) → W · P/L R$ 187,50
Odd total: 1,75
Esporte (casa): Tennis · ATP Cincinnati
Seleções:
  • Tennis · ATP Cincinnati · Sinner · Sinner v Alcaraz @ 1,75 · 14/08/2026
```

**Código, data, stake, odd e resultado já vêm decididos.** O inject até escreve a conclusão
(`"Ganho (WON) → W"`). Sobram **duas** perguntas para a IA:

1. `Tennis` → `Tênis` (esporte canônico)
2. `Sinner` num mercado de vencedor → categoria `ML` + descrição `Sinner [Sinner v Alcaraz]`

Estamos pagando inferência para copiar cinco campos e responder duas perguntas de tabela.

### I.3 E a IA erra justamente no que já vinha pronto

Correções feitas à mão desde 12/07 (fora `tipster`, que é rotulagem e não erro de extração):

| Campo | Correções | O campo vem pronto da casa? |
|---|---|---|
| resultado | 401 | **sim** |
| esporte | 205 | parcial (precisa localizar) |
| data | 202 | **sim** |
| aposta (categoria) | 135 | não — é a pergunta legítima |
| descrição | 104 | não — é a pergunta legítima |
| odd | 39 | **sim** |
| stake | 30 | **sim** |
| **Total** | **1.116** | **672 (60%) em campos que a casa já entregou** |

Um tradutor não erra `odd` porque ele não lê `odd` — ele copia. **60% das correções manuais
desaparecem por construção.**

---

## PARTE II — O plano

### II.1 A arquitetura proposta

```
extensão lê a API da casa
        │
        ├─► TRADUTOR (determinístico, roda no backend)
        │      ├─ linha resolvida  ──────────────────► TSV → banco     [R$ 0]
        │      └─ linha com rótulo desconhecido ──┐
        │                                          │
   print / casa sem captura ──────────────────────►├─► IA ─► TSV → banco   [pago]
                                                   │
                                     rótulo novo ──┴─► fila de mapeamento
```

Três invariantes de desenho:

1. **O fallback é por LINHA, não por casa.** Um mercado que a casa inventou ontem manda **aquele
   bilhete** para a IA; os outros 49 do lote passam direto. Sem isso, um rótulo novo derrubaria a
   economia da casa inteira.
2. **Rótulo desconhecido é evento, não silêncio.** Ele entra numa fila (`mapa_pendente`) com casa,
   rótulo bruto e contagem. É o mesmo princípio do `avisarEnumNaoMapeadoVB()` da s285: contar sem
   dizer *qual* transforma conferência em caça manual.
3. **O tradutor nunca inventa.** Na dúvida, ele não chuta uma categoria — devolve a linha para a
   IA. O modo de falha aceitável é "custou dinheiro"; o inaceitável é "gravou errado em silêncio".

### II.2 De onde vem o mapa — e por que não dá para copiar o `§9`

O `casas/CASA_*.md §9` **não serve como tabela de-para completa**. Por decisão da s49 (camada
fina), ele lista só os mercados que alguém confirmou: medido agora, são de **4 a 35 linhas** por
casa (Betboom 4, BETesporte 4, Jonbet 5, KTO 8, Pinnacle 8, Bet365 22, Betfast 22, Novibet 35).
Não cobre o mundo real.

O banco também não serve: ele guarda a categoria **canônica**, nunca o rótulo bruto da casa. O par
que o tradutor precisa não está gravado em lugar nenhum hoje.

**Solução: modo sombra.** Antes de traduzir nada, passamos a registrar o par:

```
(casa, rótulo bruto da casa, esporte bruto)  →  (categoria, esporte que a IA decidiu)
```

O rótulo bruto já viaja no bloco de texto (`Esporte (casa): Tennis · ATP Cincinnati`, a linha de
seleção com o mercado). O que falta é gravá-lo junto da decisão. Isso é **uma tabela nova e um
gancho no `done`** de cada extração — o mesmo lugar onde `registrar_uso` já grava hoje.

Em duas a quatro semanas de tráfego real o mapa se escreve sozinho, **com contagem de frequência**,
que é justamente o que diz quando uma casa está pronta para virar a chave.

> **A IA vira compilador, não motor.** Ela é paga uma vez para construir a tabela, e a tabela roda
> de graça para sempre. É a inversão que torna o negócio escalável.

### II.3 O que fica com a IA — para sempre, e sem culpa

| Caso | Por quê | Volume medido (60 d) |
|---|---|---|
| Print / foto de bilhete | não há payload para ler | 47 leituras · US$ 35,21 |
| Casa sem captura na extensão | idem | 23 casas · **US$ 10,71 no total** |
| Mercado novo que a casa inventou | só a IA classifica sem tabela | vira fila de mapeamento |
| Casa ainda não portada | transição | encolhe a cada fase |

**A cauda de casas sem suporte não é um problema de custo.** As 23 casas somadas custaram
US$ 10,71 em 60 dias — 3% da conta. A maior delas (Bolsa de Aposta, 28 leituras, US$ 3,30) é
candidata natural a ganhar captura, não a justificar um projeto.

### II.4 As fases

| Fase | O que entrega | Como se prova pronta |
|---|---|---|
| **0 · Sombra** | tabela `mapa_rotulos` + gancho no `done`; nada muda para o usuário | o mapa existe e tem contagem por casa |
| **1 · Tradutor** | motor de tradução + fallback por linha, **desligado** | roda em paralelo à IA; grava só o diff |
| **2 · Diff** | relatório casa a casa: em quantas linhas tradutor ≠ IA, e em qual campo | **taxa de divergência < 1% em ≥ 500 bilhetes** daquela casa |
| **3 · Virada** | flag por casa: tradutor manda, IA vira fallback | custo da casa cai a zero no `uso_tokens` |
| **4 · Repete** | próxima casa da fila | — |

**A Fase 2 é a que torna isto seguro.** O tradutor roda contra a mesma entrada que a IA, e a IA
continua sendo a verdade gravada até o diff provar que dá para trocar. Nada é apostado.

### II.5 A ordem das casas — por custo, não por simpatia

| # | Casa | US$ 60 d | % acumulado | Fixture no harness? |
|---|---|---|---|---|
| 1 | **Bet365** | 143,33 | 43 % | sim (`bet365.confirmation/summary`) |
| 2 | **Betano** | 56,91 | 61 % | sim (3 fixtures) |
| 3 | **Superbet** | 22,10 | 67 % | sim |
| 4 | **Pinnacle** | 20,13 | 73 % | sim (2) |
| 5 | **Betfair** | 15,83 | 78 % | sim (4) |
| 6 | **Betfast** | 13,41 | 82 % | sim |
| 7–21 | resto | ~59 | 100 % | sim, 20 casos no total |

**Seis casas cobrem 82% do custo.** E todas as 21 já têm payload real congelado em
`extensor/harness/fixtures/` — a bancada de teste do tradutor **já existe**, com 20 casos e 304
bilhetes.

### II.6 Como o harness prova cada casa

O `extensor/harness/run.mjs` hoje prova que o **inject** produz o bloco de texto certo a partir do
payload congelado. O tradutor entra no mesmo lugar, com uma asserção a mais por caso:

```
payload congelado → inject → bloco de texto → TRADUTOR → linha TSV esperada
```

Duas regras vindas da regra "teste verde não é teste que detecta" (`CLAUDE.md`):

- **Recortar o código real, nunca reimplementar.** O caso importa o tradutor do arquivo, como já
  faz com o inject.
- **Provar por mutação.** Cada casa portada entra com uma mutação registrada: remover a entrada do
  mapa daquele mercado tem de deixar o caso **vermelho**, e restaurar tem de deixar verde. Sem
  isso, o verde não prova nada.

E uma terceira, específica deste projeto: **o caso tem de conter pelo menos uma linha que cai no
fallback**, senão nunca se prova que o fallback funciona.

---

## PARTE III — Estudo de custo

### III.1 O que compõe uma leitura, hoje (medido, 60 dias)

| | Captura pela extensão | Print / foto |
|---|---|---|
| Leituras | 1.003 | 47 |
| **Custo médio** | **US$ 0,199 = R$ 1,03** | **US$ 0,749 = R$ 3,86** |
| Resposta da IA (output) | US$ 0,0839 · **42 %** | US$ 0,5209 · **70 %** |
| Manual relido (cache read) | US$ 0,0410 · 21 % | US$ 0,0530 · 7 % |
| Manual regravado (cache write) | US$ 0,0445 · 22 % | US$ 0,0650 · 9 % |
| A entrada em si (input) | US$ 0,0295 · 15 % | US$ 0,1104 · 15 % |
| Pedaços por leitura | 3,1 | 3,7 |

> **Duas leituras diferentes desta tabela.** Na **captura**, manual + resposta são 85% — e o
> tradutor elimina os dois de uma vez, porque não há chamada nenhuma. No **print**, 70% é a IA
> escrevendo: ali o manual quase não importa, e nenhuma otimização de cache resolve. **Print é
> irredutível enquanto houver IA.**
>
> ⚠️ A separação print × captura usa `input > 25.000 tokens` como aproximação (imagem consome
> muito input). Não há campo de modo em `uso_tokens` — vale como ordem de grandeza, não como
> contagem exata.

### III.2 Custo por usuário — os três cenários

Base do cálculo, medida na nossa própria carteira: **20 leituras de captura + 3 prints por
usuário/mês** (média dos 14 donos ativos, excluindo Feca e Gabriel, que são operadores).

| Cenário | Captura | Print | **Total/mês** | O que mudou |
|---|---|---|---|---|
| **Hoje** | 20 × R$ 1,03 = R$ 20,60 | 3 × R$ 3,86 = R$ 11,58 | **R$ 32,18** | — |
| **Só cache (A+B+C)** | 20 × R$ 0,59 = R$ 11,80 | 3 × R$ 3,24 = R$ 9,72 | **R$ 21,52** | −33 % |
| **Com tradutor** | **R$ 0** | 3 × R$ 3,24 = R$ 9,72 | **R$ 9,72** | **−70 %** |

E o número que importa mais que a média — o **usuário pesado**:

| Perfil | Leituras/mês | Hoje | Com tradutor |
|---|---|---|---|
| Comum (Lava, Tonelada) | 2–14 | R$ 11–21 | **~R$ 0** |
| Ativo (William) | 26 | R$ 73 | **~R$ 21** (só prints) |
| Operador (Jonathan) | 78 | R$ 146 | **~R$ 25** |
| **Extremo (Feca)** | **437** | **R$ 428** | **~R$ 33** |

**É esta linha que decide o negócio.** Hoje o pior usuário custa 40× o comum. Com o tradutor ele
custa o preço dos prints dele — e mais nada.

### III.3 Escala

Receita a R$ 99 médio por assinante:

| Assinantes | Custo hoje | Custo c/ tradutor | Receita | COGS hoje | COGS c/ tradutor |
|---|---|---|---|---|---|
| 100 | R$ 3.218 | R$ 972 | R$ 9.900 | **32,5 %** | **9,8 %** |
| 500 | R$ 16.090 | R$ 4.860 | R$ 49.500 | 32,5 % | 9,8 % |
| 1.000 | R$ 32.180 | R$ 9.720 | R$ 99.000 | 32,5 % | 9,8 % |

> **Repare que continua linear nos dois casos.** O tradutor derruba o patamar de 32,5% para 9,8%,
> mas **não quebra a linearidade** — porque o que sobra é print, e print é por usuário. Quebrar a
> linearidade exige a franquia da §III.4.
>
> Sem o tradutor, 1.000 usuários com o perfil do Feca custariam **R$ 428.000/mês**. Com ele,
> R$ 33.000. Essa é a diferença entre um produto e um problema.

### III.4 O que isso faz com os planos

Com o tradutor, **captura vira ilimitada de verdade** — não é promessa de marketing, é o custo
sendo zero. O que precisa de franquia é o print, porque é o único item que ainda custa por uso.

| Plano | Preço | Contas | Captura | Franquia de print | Custo | Margem |
|---|---|---|---|---|---|---|
| **Solo** | R$ 49 | 3 | ilimitada | 3/mês | R$ 9,72 | **80 %** |
| **Pro** | R$ 99 | 10 | ilimitada | 10/mês | R$ 32,40 | **67 %** |
| **Operação** | R$ 149 | 20 | ilimitada | 20/mês | R$ 64,80 | **57 %** |

Print excedente: R$ 5,00 cada (≈ 1,5× o custo), ou o usuário pede a captura da casa — o que é
exatamente o incentivo certo, porque **cada casa portada tira prints do sistema**.

E some-se o argumento comercial: **"captura ilimitada" é uma frase que nenhum concorrente que paga
IA por leitura consegue escrever.**

---

## PARTE IV — Viabilidade e riscos

### IV.1 Manutenção — o medo principal, medido

A objeção óbvia é "parser quebra quando a casa muda". Fui ao `git log` dos 16 injects:

| Inject | Commits (6 meses) | Desde |
|---|---|---|
| `b3_inject.js` (Bet365) | 13 | 22/07 |
| `bf_inject.js` (Betfair) | 8 | 13/07 |
| `sb_inject.js` (Superbet) | 6 | 05/07 |
| `vb_inject.js`, `tv_inject.js` | 4 cada | 25–26/07 |
| os outros 11 | 1 a 3 | — |

**Li as 21 mensagens de commit da Bet365 e da Betfair — as duas mais mexidas. Nenhuma é "a casa
mudou o formato e quebrou".** São todas construção: captura passiva por API, paginação ativa,
driver de UI, rota derivada do `PD`, `BC`/`BT` do sistema, "Mostrar Mais" automático, cashout.

**Duas ressalvas honestas:** a janela é de ~6 semanas de operação real, curta demais para virar
lei; e o inject sobrevive a mudança de layout porque lê a **API** da casa, que muda muito menos
que a tela. Essa é a razão estrutural para o otimismo — mas é otimismo, não garantia.

O que reduz o risco de verdade: **o tradutor mora na mesma camada que já é mantida e já tem
harness.** Não é uma camada frágil nova; é o último passo de uma que já existe e já é testada com
payload real congelado.

### IV.2 A descrição é o risco real — e o golden set é magro

Classificar mercado é tabela. **Compor descrição é julgamento**, e é onde o tradutor pode ficar
pior que a IA: sufixo de player prop, separador ` // ` de bet builder, confronto omitido quando
todas as pernas são do mesmo jogo (`MASTER_DESCRICAO §16`), caixa do nome próprio.

E a rede de proteção é fina: **`golden_set/descricoes.jsonl` tem 23 linhas.** Para comparação, a
base tem 24.222 bilhetes extraídos e 104 correções manuais de descrição.

**Mitigação, e ela é obrigatória:** a Fase 2 (diff contra a IA) trata a descrição como campo de
primeira classe — a taxa de divergência é medida **por campo**, e a descrição tem gate próprio.
Se uma casa passar em tudo menos em descrição, a saída é traduzir os outros campos e **deixar a
descrição com a IA naquela casa** — o custo cai menos, mas nada regride.

### IV.3 Print é o custo que sobra, e ele é irredutível

70% do custo de um print é a IA escrevendo. Não há cache, chunk ou tabela que resolva. As opções
reais são três, e nenhuma é técnica: franquia por plano (§III.4), portar a casa que gerou o print,
ou aceitar o custo.

### IV.4 O que não foi medido

- **Infra (Railway: app + Postgres + `sharpen-bot`).** Nenhum número deste documento a inclui. É
  custo fixo, então dilui com escala — mas define o piso do plano de entrada e **precisa ser
  medido antes de publicar preço**.
- **Disposição a pagar.** R$ 49/99/149 é o que o custo permite, não o que o mercado aceita.
- **Esforço de engenharia por casa.** Não estimei horas: a Fase 1 numa casa é o que vai calibrar
  isso, e estimar antes seria chute.

### IV.6 A correção B está bloqueada: os dois caminhos de extração discordam sobre a ORDEM

Ao implementar a correção B (não fatiar lote pequeno em 4 pedaços), a medição parou o trabalho.

O agrupamento decide **qual caminho de código roda**: lote com 2+ blocos vai para
`_stream_parallel`; lote de 1 bloco vai para `_stream_sequential`. Um piso de bilhetes passaria a
mandar **lote pequeno para o sequencial** — e os dois caminhos **não aplicam a mesma regra de
inversão de linhas**:

| Caminho | Inverte quando |
|---|---|
| `_stream_parallel` | `casa ∈ {BET365, BETANO, BETFAIR}` **ou Superbet-TEXTO** |
| `_stream_sequential` | `casa ∈ {BET365, BETANO, BETFAIR}` — **sem a Superbet** |

Hoje a divergência é invisível porque lote com 2+ bilhetes **sempre** cai no paralelo, e com 1
bilhete inverter é no-op. Com o piso, um lote de 2 a 12 bilhetes da Superbet-texto passaria a sair
**na ordem trocada, sem erro nenhum** — exatamente o modo de falha que este projeto mais teme.

**O conserto certo não é ajustar o `seq_reverse`: é ter UMA regra.** Regra duplicada é regra que
diverge — foi o que já aconteceu com a lista de casas do chunking e a do pré-dedup (s194, e a
Pinnacle ficou de fora das duas). Extrair `_deve_inverter_linhas(casa_key, content)` e chamar dos
dois lados fecha a classe do defeito, não só a instância.

**Por que não foi feito agora:** mexer na ordem de gravação exige verificar com uma captura real
de Superbet-texto, que esta sessão não tinha. Vale **US$ 34/mês** — não justifica arriscar ordem
de bilhete sem prova. O aviso ficou no código, junto de `_STAGGER_TIMEOUT` em `app/main.py`.

### IV.5 Critérios de aborto

O plano deve ser interrompido, não empurrado, se:

- a taxa de divergência da Bet365 (a casa mais rica em formatos) **não** cair abaixo de 1% em
  500 bilhetes depois de duas rodadas de ajuste de mapa;
- a fila de rótulos desconhecidos **não saturar** — se cada semana traz rótulos novos na mesma
  taxa, o mundo não é fechado e a premissa está errada;
- alguma casa quebrar o tradutor por mudança de payload **mais de uma vez** no primeiro trimestre.

Os três são mensuráveis, e o modo sombra os revela **antes** de qualquer virada de chave.

---

## PARTE V — Decisões

| # | Decisão | Recomendação |
|---|---|---|
| 1 | Fase 0 (modo sombra) entra agora? | **Sim.** É uma tabela e um gancho; nada muda para o usuário e é o que produz o mapa. |
| 2 | As correções de cache (A+B+C) entram junto? | **Sim, em paralelo.** São analgésico, mas valem enquanto a IA seguir no caminho — e barateiam o print, que nunca sai dele. |
| 3 | Primeira casa a portar | **Bet365** — 43% do custo, 4 das suas contas, fixture pronta. |
| 4 | Gate de virada por casa | divergência **< 1% em ≥ 500 bilhetes**, medida por campo, com a descrição gateada à parte. |
| 5 | Medir a conta do Railway | pendente — bloqueia o preço final, não o plano. |

---

VERSÃO: 2026
ATUALIZADO: 2026-08-25 (sessão 295 — plano criado; nenhuma alteração de código)
