# PLANO — Perfil de Tipster (unidades, atribuição e Telegram)

> Objetivo do Feca (2026-07-11): dar ao tipster uma existência de verdade dentro do Sharpen —
> hoje `tipster` é só **texto livre** numa coluna de `bilhetes`, carimbado à mão. Três frentes que
> compartilham a **mesma espinha** (o *Perfil de Tipster*): (1) medir resultado **em unidades** ao
> longo do tempo, (2) **atribuir** apostas ao tipster automaticamente, (3) puxar tips direto do
> **Telegram**. Tudo sob uma restrição que governa o módulo: **o Sharpen quer ser a base dos
> tipsters, então jamais pode virar ferramenta de repasse.**
>
> Fontes vizinhas: `PLANO_MULTIUSUARIO_2026.md` (auth/SaaS — de onde vem o login e o combate a
> senha compartilhada), `Ideias/README.md` (§1.1 Fase 3 e §4.1 Fase 5 — as sementes de Telegram
> que este doc funde), `docs/UI_REFERENCE.md §5` (padrão monetário — obrigatório antes de qualquer
> render de "u"). Estudo de negócio: `Ideias/Estudo_Assinatura_Tipsters_Sharpen.pdf`.

---

## Invariante #0 — anti-repasse (governa todo o módulo Telegram)

> **Sharpen quer ser a base dos tipsters → Sharpen jamais pode ser ferramenta de repasse.**

Se o sistema deixa um não-pagante ver a tip **a tempo de apostá-la**, ele destrói o tipster que a
gente quer ter como cliente. Isso **não é uma feature com delay** — é uma **restrição** acima de
P1/P2/P3. Caso concreto que o Feca levantou: um assinante com 7 amigos usando a mesma senha para
ver a tip "online" sem seguir/pagar o tipster.

**Distinção que resolve metade do problema.** Duas coisas entram pelo Telegram; só uma é perigosa:

| O que entra | Valor de repasse | Perigo |
|---|---|---|
| A **tip crua** (o pick, antes de você apostar) | **Alto** enquanto a linha está viva | 🔴 é isto que vaza |
| O **bilhete que você já fez** (planilhamento) | **Zero** — a ação já aconteceu | 🟢 é só registro |

Regra de ouro: **o Sharpen nunca surfa uma tip que o usuário ainda não consumiu legitimamente.**

**Política de liberação (o "delay" ancorado, não chutado).** Delay fixo é a ferramenta errada:
o tempo de vida de uma tip varia demais (3 dias antes do jogo vs. 5 min antes). O que se
autocalibra:

1. **Alvo (política-norte):** revelar a tip no Sharpen só depois do **início do evento** (kickoff)
   **e/ou** depois que o **bilhete casado** foi registrado (prova de consumo legítimo). Depois do
   kickoff a tip pré-jogo não vale mais como aposta → repasse sem valor.
2. **Rede (v1):** um **delay fixo** simples como implementação inicial, enquanto o ancorado-no-evento
   não está pronto — e para tips sem horário de evento parseável (ex.: futuros).
3. **Governança:** a **política é definível pelo tipster** ("minhas tips liberam no kickoff"). Isso
   transforma a restrição em **argumento de venda**: *"o Sharpen não te repassa; só planilha depois
   que a tip já não vale como aposta."*

**Senha compartilhada é problema à parte.** O delay cuida do *frescor* da tip; "7 amigos, 1 login"
é **abuso de licença** e se resolve na **camada de auth** (limite de sessão/dispositivo, detecção de
login concorrente) — ver `PLANO_MULTIUSUARIO_2026.md`. Mesmo com delay perfeito, senha
compartilhada vaza; não se resolve no Telegram.

---

## A espinha — Perfil de Tipster + resolvedor de atribuição

Os três projetos são facetas de **um objeto novo**: o **Perfil de Tipster**, por `(dono, tipster)`,
espelhando a tabela que já existe `parceiros (dono, casa, nome)`.

- **P1** = a faceta *stake/unidade no tempo*.
- **P2** = a faceta *características + regra de atribuição*.
- **P3** = a faceta *fonte externa (Telegram)*.

**Passo zero de tudo:** criar o **cadastro de tipster** (tabela `tipsters` escopada por `dono`). Sem
ele, nenhuma das três frentes tem onde morar. Com ele, viram "abas" do mesmo cadastro.

**Atribuição como resolvedor com procedência.** Toda aposta ganha `tipster` por **uma de N
estradas**, cada uma com **confiança** e um **"por quê"** guardado:

| Estrada | Entrada | A fonte é conhecida? |
|---|---|---|
| Carimbo manual | usuário digita | — |
| Regra / watermark (P2) | print/bilhete sem fonte | inferida por sinais |
| Canal do Telegram (P3) | texto do canal | **nativa** (o canal é o tipster) |

Isso faz P2 e P3 serem **a mesma meta por caminhos diferentes**, não features concorrentes: o
watermark existe porque no print **não se sabe a fonte**; o Telegram **já sabe de graça**.

---

## Onboarding — o tipster nasce sozinho, incompleto

Fluxo desenhado pelo Feca (adotado como está):

1. Usuário extrai apostas (ex.: Betano) e digita "Joao" no campo tipster.
2. **João é cadastrado automaticamente** na base de tipster — o registro **nasce do próprio campo
   de texto**. Não há seed manual: no primeiro deploy, faz-se **backfill dos tipsters distintos**
   já existentes nos bilhetes do dono, todos nascendo **incompletos**.
3. João aparece com um **`(i)`** = "sem informações cadastradas".
4. **`(i)` clicável** → popup de cadastro final (stake inicial, casas, mercados, regra de
   atribuição).
5. Se o usuário pular → no **próximo login, o popup de boas-vindas vira a lista de pendências**
   ("2 tipsters sem cadastro completo").

---

## P1 — Resultado em unidades ao longo do tempo

### O problema e a matemática certa

Tipster manda a tip em **unidades** (0,25u · 0,5u · 1u · 3u…). O apostador tem uma **stake por
unidade** que **muda no tempo**. Para ler resultado "em u" — a métrica que compara tipster
independentemente da banca — divide-se cada aposta pelo valor-da-unidade **vigente na data dela**.

> **Unidade é uma view derivada**, exatamente como o P/L já é hoje (`calcular_pl`, odd =
> Resultado/Stake, nada persistido). **Não se guarda "quantas u tinha a aposta"** — guarda-se só a
> **escada de valor-da-unidade no tempo** (função-degrau). u da aposta = `stake_R$ ÷
> valor_unidade_na_data`. Calculado na hora, nunca salvo → **editar/corrigir stake retroativa
> recalcula todo o histórico de graça.**

**Fórmula:** `P/L em u = Σ (P/L_R$ da aposta ÷ unidade vigente na data da aposta)`.

O **segredo** é nunca reprocessar o passado com a unidade nova. Exemplo do Feca:

| Período | Unidade | Lucro R$ | Lucro em u |
|---|---|---|---|
| Março | 100 | 9.000 | **90u** |
| Abril | 200 | 9.000 | **45u** |
| **Total** | — | 18.000 | **135u** ✅ |

O resultado **irreal (90u)** só apareceria dividindo **tudo pela unidade atual (200)** — que é
justamente o que **não** se faz. O degrau no tempo preserva o real (135u).

### Regras decididas

- **Data que manda na busca da unidade:** default = **data da aposta resolvida** (o que o Feca usa);
  vira **preferência por cliente** (quem quiser, usa data de postagem). Para apostador de longo
  prazo — o público — é **indiferente**; é config de baixa importância, não bloqueio.
- **1ª entrada de stake** vale **da primeira aposta pra frente**, até a próxima alteração. Sem
  buraco de "sem stake".
- **Tipster sem escada não é excluído.** Usa-se a **stake média do cliente** como unidade-fallback
  e **avisa**: *"3 tipsters sem stake definida — usando sua média (R$ 250). O u total pode ficar
  impreciso."* (Refino futuro a considerar: usar a média **daquele tipster** em vez da global.)

### 1a — "u total da carteira" (decidido: existe, com ressalva)

Existe um **u total da carteira** = `Σ P/L ÷ unidade-do-tipster-na-data`, somando entre tipsters.
Ao passar o mouse, **tooltip** explica: *"cada tipster tem um valor de unidade próprio"*. É soma de
u heterogêneos — legítima como número de carteira **desde que rotulada**. Só fica **completo**
quando todo tipster tiver escada (ou cai no fallback de média, sempre com o aviso visível).

### UI

- **Editor da escada:** timeline de segmentos (período → valor), botão **"inserir alteração de
  stake"** (data + novo valor), mini-gráfico **degrau** da evolução, validação (datas crescentes,
  valor > 0, aviso em sobreposição).
- **Toggle R$ ⇄ u** no painel do tipster: troca toda a leitura entre reais e unidades.
- **⚠️ Marca:** "u" é uma **convenção monetária nova** (sufixo, casas, cor). Pelo `CLAUDE.md` isso
  **tem que passar pelo `/nova-ui` e pelo Feca** — não inventar um terceiro formato. Proposta de
  partida (a confirmar): `+3,25u` / `−1,50u`, 2 casas, mesma regra do `fmtPL` (cor só no número,
  minus U+2212, zero neutro), "u" em `--ink-soft`.
- **Amarração:** o número em u é **o insumo honesto dos Relatórios de Solidez** já existentes — yield
  e ROI de tipster em u são a métrica de verdade. A escada de stake alimenta direto aquilo.

---

## P2 — Características + auto-preenchimento por assinatura

### A ideia

No cadastro do tipster, além da stake: **casas principais**, **mercados que atua** (ex.: under/over
gols), e **regra de atribuição**. O truque do Feca: o tipster manda 1u, a stake é 200, mas ele
aposta **199** em cada uma para **marcar** que aquela aposta é daquele tipster. O sistema aprende:
apostas under/over gols com stake 199 na casa X → **sugere** aquele tipster no preenchimento.

### Custo — reenquadrado (corrigido pela estrutura real da tabela)

**Descoberta (2026-07-11):** a tabela `bilhetes` **não tem coluna de mercado/categoria**. Os campos
são `casa, parceiro, data, esporte, tipster, aposta, descricao, stake, odd, resultado,
codigo_bilhete, confianca…`. **`stake` e `casa` são estruturados** (match exato, grátis); **"mercado"
(under/over gols) só existe como texto livre** em `aposta`/`descricao` — há um heurístico em
`repository.py` que *infere* categoria e cai em "Outros ⚠️" quando não tem certeza (reusável).

Isso move o corte "grátis vs pago" — mas **não quebra o v1 grátis**, porque o watermark
`stake exato + casa` já discrimina sozinho (ex. NBA: `401 + Bet365`):

- **Camada A (determinística, sempre, custo ≈ zero):** `stake exato` + `casa ∈ conjunto`
  [+ faixa de odd] → sugere tipster. **É o núcleo do v1.**
- **Camada B (heurístico/IA, opt-in):** filtro por **mercado**, que exige classificar o texto livre
  de `aposta`/`descricao`. Refinamento **opcional**, não pré-requisito — começa reusando o
  heurístico de categoria existente; só vira IA se precisar de fuzzy. É o "2º passo" que custa.

### Regras decididas

- **Combo de sinais, não só o 199.** Pessoas assinam de formas diferentes; a regra **não pode ser
  hardcoded no valor**. Precisa de um **schema flexível** (stake, casas, mercados, odd). O
  **chatbot que conversa com o usuário para montar a regra** é a estrela-guia; MVP = formulário
  simples. **Esta sub-frente nasce em BETA** até ser construída em detalhe.
- **Stake EXATO, não "≈".** Exemplo do Feca (NBA player props, 4–6 tipsters marcando 400/401/402/
  403/404/405): 401 ≠ 402, senão os tipsters se misturam. O casamento tem que ser **exato** nos
  dígitos que codificam a identidade.
- **Distorção aceita.** 199 em vez de 200 mexe (pouco) no stake/P/L reportado — é **o preço da
  facilidade** de apontar tipster em operação grande. Watermark vive nos **dígitos baixos**.
- **Sempre sugestão, nunca escrita silenciosa.** Saída = **popup agrupado por tipster** ("23
  apostas → tipster X · stake 401 + player props Bet365 · confiança alta") com aceitar/rejeitar por
  grupo. A **ordem da extração segue a ordem normal** do sistema.

---

## P3 — Telegram como base

> STATUS: 🔵 grande-mas-viável. Funde as duas sementes do `Ideias/README.md`: §1.1 Fase 3 (login
> Telegram) + §4.1 Fase 5 ("Telegram → tipster automático — a maior lacuna aberta").

### Viabilidade

1. **Login** — Telegram Login Widget, padrão. Já contemplado no SaaS.
2. **Ler as mensagens é o coração.** Duas vias:
   - **Bot API:** um bot só lê canal/grupo em que **foi adicionado**. Canal de tipster pago, você é
     *membro*, não admin → bot não entra. **Insuficiente** para ler os canais do cliente.
   - **User API (MTProto, ex. Telethon):** loga **como o próprio usuário** → lê **todos os canais que
     ele já segue**, inclusive pagos. É a via que faz "ler meus canais de tipster" **funcionar de
     verdade**. É o pedaço "gigante": **gestão de sessão MTProto** + é ToS-sensível (userbot é
     permitido, mas delicado).
3. **Parsear a tip → aposta** = o **mesmo motor de extração que já existe**, sobre **texto** em vez
   de OCR → **mais fácil** que print.

### As sacadas

- **Atribuição de graça.** Quando a tip vem **do canal**, o tipster já é **conhecido** — sem
  watermark. Telegram é o mesmo objetivo de P2 por outra estrada (ver "resolvedor com procedência").
- **Tip e bilhete são duas metades.** A tip do Telegram é a **recomendação**; o print/bilhete é a
  **aposta que você fez**. Casando as duas (por data±janela, jogo, mercado, odd~) nasce o registro
  mais rico possível **e** duas métricas novas que ninguém tem:
  - **Taxa de adesão** ("segui X% das tips do tipster");
  - **Quanto deixei na mesa** (tips que não apostei).
- **Gargalo real** não é a extração (já temos) — é a **sessão MTProto** e o **casamento
  tip↔bilhete**.

### Pré-condição inegociável

P3 **só existe carregando a Invariante #0** (política de liberação anti-repasse). Ingestão pode ser
instantânea (para casar e não perder precisão), mas a **visibilidade é comportada** pelo mais tardar
entre `{início do evento}` e `{bilhete casado registrado}`, com delay-fixo só de rede,
**configurável pelo tipster**.

---

## Ordem de execução sugerida

| # | Etapa | Horizonte |
|---|---|---|
| 0 | **Cadastro de tipster** (tabela `tipsters` + backfill + onboarding `(i)`) — a espinha barata, pré-requisito dos três | ✅ **backend feito (sessão 142, `26b72f1`)** · UI pendente |
| 1 | **P1 — unidades** (escada + fallback de média + toggle R$/u via `/nova-ui`) | ✅ **backend feito (sessão 142, `8150ed2`)** · UI pendente |
| 2 | **P2 — watermark** (schema de regra + popup por tipster; chatbot fica beta) | 🟡 |
| 3 | **P3 — Telegram** (MTProto + casamento + política de liberação) | 🔵 grande/condicional |

> **Estado (2026-07-14):** todo o BACKEND das etapas 0 e 1 está no ar e testado (116 verdes).
> Falta só a **UI** — especificada e auditada abaixo, aguardando (a) o editor de apostas do
> dashboard mergear (evitar colisão em `dash/app.js`) e (b) a validação visual do `/nova-ui`.

---

## UI — spec auditado pelo `/nova-ui` (pronto p/ executar)

> Escrito na sessão 142 rodando o checklist `/nova-ui` inteiro (não só o §5 monetário —
> ver [[feedback_nova_ui_gate_total]]). Objetivo: quando o editor de apostas do dashboard
> mergear, a construção vira execução mecânica, sem inventar convenção nova nem colidir.
> **Toda classe abaixo já EXISTE** no `index.html` / dashboard — reuso, não crio.

### Surface A — Painel de Tipsters (no extrator, `index.html`)

Onde: **novo `nav-item` "Tipsters"** na sidebar do extrator, espelhando `#nav-contas`
(`index.html:1526`), abrindo uma view via `mostrarView('tipsters')`. Coleta de dados:
`GET /tipsters/cadastro`. É um arquivo **diferente** do que o editor de apostas mexe
(`dash/app.js`) → sem colisão.

Layout — **espelha o Painel de Contas** (mesmas classes, tipster não tem casa → lista
plana, sem o agrupamento `.contas-casa`):
- Contêiner `.painel` + `.painel-hero` (eyebrow mono `.painel-hero-eyebrow`).
- Abas **Ativos / Inativos** = `.contas-tabs`/`button.on` (`index.html:1484`).
- Busca = `.contas-search` (`:1487`).
- Cada tipster = `.conta-row` com `.conta-nome` (nome), `.conta-badges` (o `(i)`) e
  `.conta-acoes` com `.conta-act` ("Editar info", "Renomear") + `.conta-act.danger`
  ("Arquivar"). Endpoints: `PATCH /tipsters/{id}/info`, `POST /tipsters/{id}/renomear`,
  `/arquivar`, `/reativar`.
- Vazio = `.contas-empty`.

**Badge `(i)` de incompleto:** reusar o visual do `.pend-badge` (`index.html:247-255`) —
pill azul (`--accent`), mono 10px, `#fff`, com o mesmo halo. Conteúdo `i`. Semântica:
"sem info cadastrada" (`completo === false` vindo de `list_tipsters_cadastro`). Idêntico
ao badge que já sinaliza conta sem tipster → **consistência total**, zero classe nova.

### Surface B — Modal de info do tipster (`index.html`)

Espelha o modal de edição (`.modal-field` + `<label>` + input, `index.html:1856`). Campos:
- **Casas principais** — input texto (`atualizar_tipster_info` grava em `casas`).
- **Mercados** — input texto (`mercados`).
- **Observações** — `<textarea>` (`obs`).

Nenhum campo monetário aqui → **§5 não se aplica**. Regras que se aplicam: inputs
`--field`/`--surface-2` + `1px var(--line)` + `--r-sm`, foco borda `--accent` + `--glow`
(§4); labels Manrope; nada de cor literal.

### Surface C — Unidades + switch R$ ⇄ u (dashboard, `performance.js`) — **espera o merge**

Vive na página **Tipsters** do dashboard (`renderTipsters` / `renderTipsterDrill`) — mesmo
bundle do editor de apostas → **construir SÓ depois do merge**. Dados: `GET
/tipsters/resultado-unidades?tipster=…` e `/tipsters/unidades` (escada).

**Helper novo `fmtU(v)` — espelha `fmtPL` VERBATIM** (é o único jeito §5.1-compatível de um
valor com sinal+magnitude que **não é R$**; o "u" entra como as exceções §5.3, mas mantendo
o componente `.money`):
- Componente `.money` + `.money-sign`/`.money-val` (herda cor-só-no-número, mono,
  tabular-nums, **sem CSS novo**).
- **2 casas**, decimal vírgula. **Minus U+2212** (não `-`). **Zero neutro** = `0,00u`
  sem sinal/cor. `.money-val` colorido `--pos`/`--neg`; **`u` no `.money-sign`** (papel do
  `R$`, neutro/menor `--ink-soft`). Ex.: `+3,25u` / `−1,50u` / `0,00u`.
- **Nunca abreviar** (barrado pelo `check-tokens §d`). Proposta a **confirmar com o Feca no
  commit da UI** (é convenção monetária nova): posição do `u` (sufixo, como acima) vs. papel
  de "sign". Para **eixos/tooltips** de Chart.js, espelhar `fmtK` (`app.js:244`).

**Switch R$ ⇄ u:** pill toggle (§4, `--r-pill`, ativo `--accent`, inativo `--ink-mute`) no
cabeçalho da página Tipsters; alterna a máscara aplicada em `#tipsterPortfolioKPIs`,
`#tblTipComp` e nos cards/drill. Estado por dono (localStorage, como o resto). `usou_fallback`
/`sem_unidade` do backend viram **aviso** (`--warn`) com tooltip ("cada tipster tem unidade
própria" / "3 tipsters sem stake — usando sua média").

**Editor da escada:** modal com timeline de segmentos (`get_escada_unidade`); botão "inserir
alteração de stake" (data + valor via `moneyStake`); `POST /tipsters/unidades` grava, `DELETE
/tipsters/unidades/{id}` remove; mini-gráfico degrau (opcional, fase 2).

### Auditoria `/nova-ui` desta spec

- **§1 cor:** tudo via `var(--token)`; azul = único acento; verde/vermelho só no P/L em u
  (semântica); âmbar só no aviso de fallback. ✅
- **§2 tipografia:** nomes Manrope; badges/eyebrows mono uppercase; números tabular-nums. ✅
- **§4 componentes:** inputs, pills, `.conta-*`, `.pend-badge` reusados verbatim; zero classe
  nova até Surface C (que só adiciona o `fmtU`, espelhando `fmtPL`). ✅
- **§5 monetário:** Surfaces A/B **não renderizam dinheiro** (N/A). Surface C usa **só**
  `fmtU` (espelho de `fmtPL`) — nunca `.toFixed`/`.replace` em "u", nunca abreviar. ⚠️ o
  formato final do "u" **passa pelo Feca** no commit da UI (convenção nova).
- **Passo 4 (verificação visual):** exige subir o app com o Postgres → é POR ISSO que a UI
  não foi construída às cegas nesta sessão; fica para a fatia de interface, com render
  headless conferido antes do commit.

---

## Decisões registradas (desta conversa de planejamento)

- Anti-repasse é **Invariante #0**, acima de tudo. Política **ancorada no evento** (alvo) + **delay
  fixo** (rede v1), **definível pelo tipster**.
- Unidade = **view derivada**; guarda-se a **escada no tempo**, nunca o u da aposta.
- **u total da carteira** existe, com tooltip; tipster sem escada usa **média do cliente** + aviso.
- Data da unidade = **data resolvida** por default, **preferência do cliente**, indiferente na
  prática.
- P2 = **combo de sinais**, **stake exato**, **sempre sugestão** (popup por tipster), chatbot
  **beta**. v1 grátis = `stake + casa` (estruturados); **mercado é texto livre** → Camada B opcional.
- P3 = Telegram **viável via MTProto**; atribuição nativa; métricas de **adesão** e **deixado na
  mesa**; **só existe** sob a Invariante #0.
- Senha compartilhada = problema de **auth**, não de Telegram (ver SaaS).

---

VERSÃO: 2026
CRIADO: 2026-07-11 (conversa de planejamento — sem código ainda; doc-fonte para o `Ideias/README.md`)
