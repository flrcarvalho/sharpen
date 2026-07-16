# PLANO — Inteligência de atribuição de tipster (o resolvedor)

> **Status:** rascunho para revisão conjunta (Feca + Claude), 2026-07-15 (sessão 146). **Sem código.**
>
> Este documento aprofunda o **resolvedor de atribuição** — a P2 do [`PLANO_TIPSTER.md`](PLANO_TIPSTER.md),
> que já estabeleceu a espinha (Perfil de Tipster), o **Invariante #0 anti-repasse** e a tese de que
> "P2 (watermark) e P3 (Telegram) são a mesma meta por estradas diferentes". Nada aqui revoga aquele
> doc; isto é o miolo do motor que ele previu.
>
> Origem: o botão **"✨ Sugerir tipsters"** (sessão 145, matcher v5) funciona na carteira do Feca e
> **não generaliza**. O Feca levantou a bandeira certa: *"estamos ajustando conforme minha carteira,
> porém a ideia é que essa funcionalidade sirva para todo mundo."*

---

## 1. O diagnóstico — por que o v5 não escala

O matcher de hoje pontua com constantes: `esporte exclusivo = 10`, `casa = 5`,
`stake final = 25/√n`, `folga ≥ 7`. **Nenhuma delas veio de um princípio** — cada uma foi escolhida
para fazer os casos reais do Feca (Robotenis, Caçador, Peixe≠M&M) passarem. É a carteira do Feca
compilada dentro do `if`.

Três consequências, todas estruturais:

**(a) A escala está amarrada ao N da carteira.** "Exclusivo" foi calibrado com 32 tipsters. Com 5,
quase todo esporte é exclusivo → tudo pontua 10 → tudo passa a folga de 7 → sugere com confiança
onde não deveria. Com 150, quase nada é exclusivo → tudo pesa 1 → nada atinge 7 → **o botão não faz
nada**. O v5 só está afinado na vizinhança de 32.

**(b) Exige declaração, e declaração diverge do comportamento.** O Feca preencheu 32 perfis à mão e
**ainda assim** foi preciso corrigir a base via SQL, porque Fezinha e Arrudex declaravam
Tênis/Basquete sendo ~96% múltipla. Um cliente novo abre a tela, vê boxes vazios, clica no botão e
nada acontece: **a funcionalidade nasce morta para quem não é o Feca**.

**(c) A verdade já está no banco e o matcher a ignora.** Existem milhares de bilhetes **já
atribuídos** — dado rotulado, de graça, por carteira. O `_tmBuildAgg` do painel "Sharpen sugere"
**já faz essa passada**; o resultado vira chip na tela e o matcher nunca olha.

### 1.1. O erro da primeira proposta (registrado de propósito)

A primeira contraproposta foi **substituir** declaração por histórico (Naive Bayes puro). O Feca
recusou, e estava certo — por um motivo mais fundo que "somar é melhor que trocar":

| Fonte | O que ela sabe | O que ela **nunca** sabe |
|---|---|---|
| **Histórico** | o passado, com precisão estatística | tipster novo; mudança de unidade que vai acontecer; que dois padrões idênticos são duas pessoas |
| **Declaração** | intenção e futuro; a existência do tipster | se o que foi declarado é o que de fato acontece |

Não é "uma limpa e outra suja": são **domínios distintos**. Descartar a declaração joga fora
exatamente a informação que o dado jamais terá. As duas entram na conta.

---

## 2. Princípios (decididos na conversa de 15/07)

1. **Somar, nunca escolher.** Declaração + base + (futuro) Telegram são termos da mesma conta, em
   posições diferentes — não caminhos concorrentes.
2. **O sistema não adivinha o que não tem sinal — ele pede.** Quando dois tipsters são idênticos em
   tudo, a informação **não existe no mundo**; nenhuma esperteza a cria. O sistema diz isso e ensina
   como criá-la.
3. **Procedência antes de aprendizado.** Aprender de sugestão não revisada = aprender da própria
   opinião.
4. **Sem régua não há excelência.** Toda mudança do resolvedor se mede em **várias carteiras**.
5. **Sugestão nunca é verdade.** O humano revisa antes de exportar (já é assim; continua).

---

## 3. A arquitetura — camada de evidência

Cada fonte produz evidência sobre *"quem é o dono deste bilhete"*, com peso proporcional à sua
**procedência**:

| Fonte | Papel na conta | Força |
|---|---|---|
| **Telegram** (P3, futuro) | **rótulo verdadeiro** — não participa da adivinhação; **treina** o resto | ground truth |
| **Marca d'água / apelido** no print | quase-rótulo, quando existir | muito alta |
| **Histórico observado** | o corpo do sinal; cresce sozinho; corrige a declaração errada | cresce com o volume |
| **Declaração do usuário** | ponto de partida; única fonte de intenção e de tipster novo | decai conforme o histórico chega |

### 3.1. Como declaração e base se somam de verdade

A implementação da soma é a peça central. **A declaração entra como votos iniciais nas contagens do
histórico** (formalmente: um prior de Dirichlet; na prática: pseudo-contagens).

Para cada tipster, o sistema mantém contagens observadas por sinal — casa, esporte, mercado, valor
de stake, final da stake. Declarar *"João faz Basquete"* **adiciona α observações virtuais** de
Basquete para o João. Daí sai, sozinho, o comportamento que queremos:

- **Usuário novo (João do Basquete, Joaquim do Vôlei):** histórico = 0. Só existem os votos
  declarados → **a declaração decide, e acerta.**
- **Carteira madura (Fezinha):** declarou Tênis (α votos) mas o histórico tem centenas de múltipla e
  um punhado de Tênis → **a observação esmaga a declaração**, sem ninguém ir de SQL na base.
- **Tipster novo dentro de carteira madura:** volta a valer a declaração, só para ele.

**Não há "modo cold start" e "modo maduro" no código.** É a mesma fórmula; o peso se move sozinho
conforme o dado aparece. Isso é literalmente *"utiliza a própria base e se soma ao que o usuário
registra no detalhe"*.

> **Honestidade sobre parâmetros:** isto **não elimina** todo ajuste — sobra o **α** ("quanto vale a
> palavra do usuário, medida em bilhetes equivalentes"). Mas trocamos **seis constantes sem
> significado** (10/5/25/√n/1/7) por **um número com significado**, e que é **calibrado por medição
> em várias carteiras**, não pelo meu olho na carteira do Feca.

### 3.2. O que isso apaga do código atual

Cada peça abaixo some **sozinha**, sem regra escrita — é o teste de que a forma está certa:

| Hack de hoje | Por que some |
|---|---|
| `exclusivo=10 / compartilhado=1` | se só o Regista faz Games/Sets, a frequência é alta nele e ~0 nos outros; a razão explode sem ninguém digitar "10" |
| **filtro duro de esporte** | tipster de e-sports recebendo Futebol tem frequência ~0 ali → já é eliminado |
| **assinatura de stake declarada** (`_parseStakeSig`) | vira frequência observada — **imune ao super-declarado** |
| `25/√finais.size` | especificidade emerge da distribuição |
| word-boundary `\b` do **365** de "bet365" | não se parseia mais texto livre à cata de número |
| `folga ≥ 7` | vira **"só sugere acima de 90% de confiança"** — interpretável, comparável entre carteiras |

---

## 4. O conselho de detectabilidade (a peça do Feca)

> *"Você opera dois tipsters no mesmo mercado com a mesma stake e eu não consigo definir quem é
> quem. Porém, se você passar a colocar um real a mais num deles — de 500 para 501 — o sistema
> passa a detectar automaticamente."*

Isto **inverte o problema** e é a parte que ninguém tem. Todo matcher é passivo: recebe os sinais que
existem e tenta arrancar certeza deles. Aqui o sistema **diagnostica a própria cegueira e pede a
informação mínima que a cura**. A assimetria é o que o torna forte: **custa R$1 e o ganho é
permanente.**

É também o **antídoto real do overfitting**: em vez de eu apertar constantes até arrancar sinal de
dado ambíguo, o sistema **pede o sinal que falta**. Ele só afirma quando a evidência existe.

**Não precisa de matemática nova — o backtest já o entrega:**

1. A **matriz de confusão** do backtest (§5) É o detector de colisão: onde `ti` é confundido com
   `tj`, está o par colidido, **com número real**.
2. O **conselho** sai de simular intervenções candidatas sobre o histórico: *se `ti` passasse a usar
   stake com final 1, quantos dos bilhetes hoje confundidos seriam resolvidos?* Rankeia por
   **ganho ÷ custo** — e mudar a stake em R$1 é o de custo praticamente zero.
3. O **número** vem junto: *"isso destrava 47 bilhetes/mês que hoje ficam vazios"*. Sem simular
   contra o histórico esse número seria chute — e **conselho sem número é palpite pedindo R$1 do
   bolso do usuário**.

Vira uma tela: **"Onde eu sou cego"** — os pares colididos, o conserto e quanto ele vale.

**Honestidade obrigatória na UI:** o conselho **só vale para frente**. Mudar 500→501 hoje não
conserta o passado, e o sinal novo leva tempo para acumular. A tela precisa dizer isso.

**Efeito de segunda ordem:** o usuário vira **colaborador** do sistema em vez de vítima dele — segue
o conselho → a carteira fica legível → a IA acerta mais → ele segue mais conselhos.

---

## 5. A régua — backtest holdout multi-carteira

Sem isto, "excelência" é fé. Com isto, **o overfitting fica visível**: se eu calibrar no Feca, a
linha do Diogo afunda e aparece na tabela.

**Método:** pegar os bilhetes já atribuídos, **esconder o tipster**, rodar o resolvedor, comparar com
o real.

> ⚠️ **Holdout TEMPORAL, nunca aleatório.** Tipsters mudam de comportamento no tempo (é para isso que
> existe a *escada de unidade*). Split aleatório deixa o modelo ver o futuro e **infla a métrica**.
> Treina no passado, testa no depois.

**Saída:**

| Carteira | Cobertura | Precisão |
|---|---|---|
| Feca (32 tipsters) | ? | ? |
| Diogo | ? | ? |
| Jonathan | ? | ? |
| Lava | ? | ? |

- **Cobertura** = % dos bilhetes que receberam sugestão. **Precisão** = % de acerto entre os
  sugeridos.
- As duas são um **dial que o usuário escolhe**: corte alto sugere pouco e quase nunca erra; corte
  baixo cobre mais e erra às vezes.
- Fatuch fica de fora (base vive na planilha, não no Postgres).
- **O v5 atual também é medido** → linha de base. Se ele já for bom em todas as carteiras,
  descobrimos barato e não reescrevemos nada.

---

## 6. Fases

| # | Fase | Entrega | Depende de |
|---|---|---|---|
| **0** | **Procedência + linha de base** | coluna de origem da atribuição (`humano` / `telegram` / `sugerido` / `importado`) + backtest do **v5** rodando nas carteiras | — |
| **1** | **Camada de evidência** | contagens por tipster + declaração como pseudo-contagem; rota de sugestão em lote; corte por confiança | 0 |
| **2** | **Onde eu sou cego** | matriz de confusão → pares colididos → conselho com número | 1 |
| **3** | **Telegram** | rótulo-ouro que treina tudo (sob o **Invariante #0** do `PLANO_TIPSTER.md`) | 1 |

**Por que a Fase 0 é primeiro e é urgente:** o botão do v5 **já está gravando sugestões hoje**, e
elas ficam **indistinguíveis de atribuição humana**. Cada lote sugerido aumenta a contaminação. A
coluna de origem é barata agora e **impossível depois** — sem ela, daqui a seis meses não há como
separar o que foi o Feca do que fui eu, e o treino apodrece.

**Por que o conselho (Fase 2) não é primeiro,** apesar de ser a joia: ele é **derivado**. Para saber
que dois tipsters colidem é preciso ter as distribuições; para saber que 501 resolve é preciso
simular. Ele é o presente que a camada de evidência dá assim que existe.

**Nota:** a Fase 3 já prevista no `PLANO_TIPSTER.md` é o que muda o jogo — o Telegram não é "mais um
sinal fraco na soma", é **rótulo**. Por isso a coluna de procedência da Fase 0 **já precisa prever
`telegram` hoje**.

---

## 7. Riscos e o que pode dar errado

| Risco | Mitigação |
|---|---|
| **Auto-envenenamento** — o sistema aprende da própria sugestão e fica confiante no próprio erro | treinar **só** em rótulo de procedência confiável (`humano`, `telegram`, `importado`). `sugerido` não revisado **nunca** treina |
| **Base errada envenena o treino** | é exatamente o caso **Fezinha/Arrudex** (múltiplas gravadas como Tênis/Futebol) — corrigir a base é **pré-requisito**, não tarefa paralela |
| **Independência é falsa** (casa e mercado são correlacionados) → probabilidades super-confiantes (0.999) | o corte de confiança é **calibrado pelo backtest**, não pela teoria; se preciso, calibração explícita |
| **Deriva temporal** — o tipster muda de unidade | janela/decaimento nas contagens; a **escada de unidade** que o Feca já cadastra é a informação dessa mudança |
| **Carteira grande e homogênea** — muitos tipsters idênticos | é aqui que a Fase 2 justifica sua existência: o sistema **assume a cegueira** e pede o conserto |
| **α mal escolhido** — declaração pesa demais (repete o Fezinha) ou de menos (mata o cold start) | é **um** parâmetro, medido por backtest nas duas pontas (carteira nova e madura) |

---

## 8. Não-objetivos

- **Não é IA/LLM.** É contagem — barata, explicável, roda em milissegundos, sem custo de token. A IA
  extrai o bilhete; **atribuir tipster é estatística da carteira**.
- **Não substitui revisão humana.** Continua sugestão; o Feca revisa antes de exportar.
- **Não adivinha sem sinal.** Quando não há evidência, o certo é **deixar vazio e pedir** — não
  chutar.
- **Não reescreve o v5 antes de medi-lo.** Ele vira a linha de base e, no cold start, continua sendo
  o ponto de partida.

---

## 9. Questões abertas para a revisão

1. **α (força da declaração):** começar medindo (ex.: equivalente a 5, 20, 50 bilhetes) e deixar o
   backtest escolher — ou fixar por decisão de produto?
2. **Corte de confiança:** único e global (ex.: 90%), ou **o usuário escolhe** o dial
   precisão × cobertura por carteira?
3. **Backfill de procedência:** as linhas de hoje viram `importado`/`humano` em bloco? As sugestões
   que o v5 já gravou nos últimos lotes são recuperáveis (por janela de tempo) ou entram como
   `humano` e aceitamos a contaminação inicial?
4. **Onde roda:** pontuar no backend (rota de lote) ou servir o modelo compacto de contagens e
   pontuar no front (como hoje)?
5. **Quem vê a tela "Onde eu sou cego"** — todo dono, ou é feature de plano pago (o
   `PLANO_TIPSTER.md` já discute o corte grátis × pago)?

---

---

## 10. Fase 0 — spec executável (aprovada 16/07, "vamo pra cima")

Duas peças independentes. **0A** planta a verdade (produção); **0B** mede o ponto de partida (offline).

### 10A. Coluna de procedência — `bilhetes.origem_tipster`

**Valores:** `humano` · `sugerido` · `telegram` · `importado` · `extracao` · **NULL = legado** (linha anterior ao rastreio).

**Decisão de backfill:** *nenhum*. A coluna nasce NULL; as linhas de hoje ficam `legado` (honesto — não afirmam ser verificadas). Só as escritas NOVAS recebem rótulo. Zero risco, zero migração pesada.

**Princípio de wiring — default `humano`:** instrumenta-se **um** ponto (`atualizar_bilhete`) com a regra: tipster sendo gravado **sem** origem declarada → `humano`; com origem → usa a declarada. Assim **só o botão** precisa se identificar (`sugerido`); todo caminho manual (grid da extração, editor do dashboard, bulk) cai no default `humano` sem precisar ser tocado. Tipster **limpo** (vazio) → `origem_tipster = NULL`.

**Pontos de escrita:**
| Caminho | Arquivo | origem |
|---|---|---|
| PATCH `/bilhetes/{id}` (grid + editor) | `repository.atualizar_bilhete` | `humano` (default) |
| Botão "✨ Sugerir tipsters" | `index.html salvarTipsterVal(id, nome, 'sugerido')` | `sugerido` |
| Bulk set | `repository.set_tipster_bulk` | `humano` |
| Import de planilha | `import_*_xlsx.py` | `importado` |
| Telegram (futuro P3) | — | `telegram` |

**`origem_tipster` ∉ `_SIG_COLS`** → gravá-la nunca recalcula assinatura (mesma garantia do `esporte`).

**Regra de ouro do treino (Fase 1+):** treinar/aprender **só** em `humano` · `importado` · `telegram` · `legado`. **Nunca** em `sugerido` não revisado — senão o modelo aprende do próprio chute.

### 10B. Backtest holdout temporal — script offline, read-only

**Não toca produção.** Um script (`scripts/backtest_matcher.py`, fora do app) que, por dono:
1. Puxa os bilhetes atribuídos (once 0A existir: exclui `sugerido`; por ora usa todos os atribuídos como verdade).
2. **Split TEMPORAL:** ordena por `criado_em`; treina no passado, testa no bloco recente (ex.: últimos 30 dias). **Nunca aleatório** — a assinatura tem era ([[assinatura_tem_era]]).
3. Esconde o tipster no teste, roda **o matcher v3 de hoje** (o mesmo `_stakeSignal`/veto do `index.html`, portado fiel), compara com o real.
4. Emite por carteira: **cobertura** (% sugerido) × **precisão** (% acerto entre sugeridos) + **matriz de confusão** (quem é confundido com quem — semente da Fase 2 "onde eu sou cego").

**Entrega:** a tabela Feca/Diogo/Jonathan/Lava + os pares de maior confusão. É a linha de base contra a qual qualquer reconstrução futura se compara — e já mede o Fix 1/2/v3 desta sessão.

**Decisão:** roda como **script de scratch primeiro** (medir é urgente); produtizar como página é depois.

---

VERSÃO: 2026 · CRIADO: 2026-07-15 (sessão 146) · ATUALIZADO: 2026-07-16 (Fase 0 aprovada) · STATUS: **Fase 0 em execução**
