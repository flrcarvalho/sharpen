# Pesquisa — BADMINTON para o Sharpen/Planilhador

> **Status:** RELATÓRIO DE PESQUISA (não aplicado). Nada foi escrito nos MASTERs.
> Montado por um esquadrão de 4 agentes + captura ao vivo da bet365 em **21/07/2026**.
> Objetivo: dar tudo o que você precisa pra, amanhã, cadastrar **Badminton** como esporte
> novo e mapear os mercados das casas. As edições reais aguardam seu OK (regra: propor → confirmar → executar).

---

## 0. TL;DR — o que decidir amanhã

1. **Badminton NÃO exige categoria nova.** Reaproveita `ML / Handicap / Sets / Pontos / Player Props / H2H / Múltipla`. O Tênis é o esqueleto exato.
2. **Trabalho = 3 MASTERs globais + mapa de emoji (3 espelhos).** Casas (`§9`) só sob demanda, quando um bilhete real aparecer. Nenhum código Python a tocar (casas e esportes são auto-descobertos dos `.md`).
3. **3 decisões suas** (detalhadas no §6): (a) o parcial do badminton mapeia para `Sets` ou `Games`? (b) "total/handicap de pontos" entra em `Pontos` (estendendo a categoria) ou fica em `Outros`? (c) padronizar o parcial internamente como **"game"** ou **"set"** na descrição?
4. **Armadilha nº 1 — nomenclatura:** o parcial do badminton é o **"game"** (= o "set" do tênis). Mas **Betano chama de "set"**, **bet365 chama de "jogo/game"**, **Superbet mistura**. Logo `set ≡ game ≡ jogo` viram sinônimos do MESMO objeto.
5. **Armadilha nº 2 — pontuação vai mudar:** 2026 é **3×21** (teto 30). A BWF troca para **3×15** (teto 21) em **04/01/2027**; torneios domésticos na Índia já usam 3×15 desde jul/2026. **Não fixar 21** em nenhuma regra — o constante é "melhor de 3 games + vantagem de 2".

---

## 1. O esporte em 2 minutos

**Hierarquia (essencial pro mapeamento):**
- **Ponto** (rally point) — unidade marcada a cada troca de bolas.
- **Game** — bloco de pontos até o alvo (21 em 2026). **O "game" do badminton = o "set" do tênis.**
- **Partida (match)** — o confronto inteiro, **melhor de 3 games** (vence quem faz 2 games).

**Sistema 3×21 (vigente em TODO o BWF World Tour de 2026):**
- Melhor de 3 games; cada game até **21 pontos**, com **2 de vantagem**.
- **Deuce (20-20):** precisa abrir 2 (22-20, 23-21…). **Teto (cap) em 30** (30-29 encerra).
- Placar da partida só pode ser **2-0** ou **2-1** (nunca há empate — badminton **não tem "X"/draw**).

**Mudança futura 3×15 (a partir de 04/01/2027):** games até 15, teto 21, mesma lógica de "melhor de 3 + vantagem de 2". Índia (torneios domésticos) já usa desde jul/2026.

**5 disciplinas:** Simples Masculino (MS), Simples Feminino (WS), Duplas Masculinas (MD), Duplas Femininas (WD), Duplas Mistas (XD). Regras de pontuação idênticas nas cinco.

**Formato de placar num print:**
- Placar da partida em games: **2-1** ou **2-0** (aparece grande).
- Detalhe por game em pontos: `21-18 19-21 21-15` (menor, ao lado/embaixo).
- Deuce: `24-22`; cap: `30-29`.
- Nomes: `Jogador A - Jogador B` (simples) ou `A/B - C/D` (duplas). Nomes asiáticos costumam vir com **sobrenome primeiro** e às vezes em CAIXA ALTA.

---

## 2. Terminologia — REGRA DE OURO (colar no MASTER)

| Conceito | Badminton PT-BR | Badminton EN | Tênis (falso amigo) |
|---|---|---|---|
| Unidade do rally | **ponto** | point / rally point | ponto |
| Bloco até 21 pts | **game** (casas dizem "set" ou "jogo") | **game** | **set** ⚠️ |
| Confronto inteiro | **partida** | match | partida |

> **Nunca** traduzir "game" de badminton como "game" de tênis. No tênis, "game" é a subunidade **dentro** do set — esse nível **não existe** no badminton. O parcial do badminton corresponde ao **set** do tênis.
> `set ≡ game ≡ jogo` = o MESMO parcial. Betano="set", bet365="jogo/game", Superbet mistura → cadastrar os três como sinônimos.

---

## 3. Mercados — bet365 (CAPTURADO AO VIVO 21/07, China Open)

Fonte primária: naveguei a página `bet365.bet.br/#/AS/B94/` (B94 = ID do esporte). **Sem login.** Torneio em cartaz: China Open (Super 1000). A página do jogo tem 3 abas: **Principais · Partida · Game**. Rótulos exatos em PT-BR abaixo.

### Nível PARTIDA
| Rótulo bet365 (verbatim) | O que é | Exemplo capturado |
|---|---|---|
| **Para Ganhar** | Vencedor da partida (moneyline, 2-way) | 1.071 / 7.50 |
| **Handicap** (na tabela "Linhas da Partida") | Handicap de **GAMES** — sempre −1.5 / +1.5 | -1.5 (1.33) / +1.5 (3.25) |
| **Total** | Total de **PONTOS** somados na partida (O/U) | O 72.5 (1.80) / U 72.5 (1.90) |
| **Partida - Handicap (Pontos)** | Handicap de **PONTOS** (escada larga) | -22.5, -17.5, -12.5, -7.5, -2.5 … +22.5 |
| **Total da Partida - Mais Alternativas** | Totais de pontos alternativos (O/U) | 62.5, 67.5, 77.5, 82.5 |
| **Partida - Resultado Correto** | Placar exato em **GAMES** | 2-0 / 2-1 (por lado → 4 resultados) |
| **Dupla Resultado e Total** | Combo resultado + total | — |
| **Resultado Duplo** · **Jogador - Totais** · **Total da Partida - Ímpar/Par** | Resultado duplo · total de pontos por jogador · par/ímpar | (colapsados) |

### Nível GAME (pré-jogo oferece só o 1º game)
| Rótulo bet365 | O que é |
|---|---|
| **1º Game - Para Ganhar** | Vencedor do 1º game |
| **1º Game - Total** | Total de pontos no 1º game (O/U 35.5) |
| **1º Game - Handicap** | Handicap de **pontos** dentro do game (−5.5/+5.5) |
| **1º Game - Vencedor e Total Duplo** | Combo |
| **1º Game - Resultado Correto** | Placar exato de pontos do game |
| **1º Game - Margem de Vitória** | Margem de pontos |
| **1º Game - Primeiro a Marcar** | Primeiro a chegar a 5 / 10 / 15 pontos |
| **1º Game - Líder Após** | Quem lidera após N pontos |
| **1º Game - Para Ir a Pontos Extra** | Se o game vai a deuce (passa de 20-20) |
| **1º Game - Total - Ímpar/Par** | Par/ímpar dos pontos do game |

---

## 4. Mercados — taxonomia internacional consolidada (bet365 ≈ SkyBet ≈ 1xBet)

Confirma e detalha a captura acima. Definições precisas dos dois handicaps (a parte confusa):

- **Handicap de GAMES** (Match Handicap, sempre **±1.5**): conta **games ganhos**. `-1.5` = favorito tem de vencer **2-0**. `+1.5` = azarão cobre se vencer OU perder só por 1-2 (só não cobre no 0-2). A margem de pontos é irrelevante. É o "handicap asiático" padrão do badminton.
- **Handicap de PONTOS** (Match/Game Point Handicap, valores quebrados grandes tipo −17.5): conta **soma de pontos**. Um favorito pode vencer 2-0 e **não cobrir** −6.5 se os games foram apertados (21-19, 21-18). É o "spread fino".
- **Total de Pontos** (partida ou game): O/U sobre a soma de pontos.
- **Total de Games** (O/U 2.5): existe mas é raro/redundante — `Over 2.5 = partida vai a 3 games (2-1)`, `Under 2.5 = 2-0`.
- **Placar Exato / Correct Score:** 4 resultados possíveis — **2-0, 2-1, 1-2, 0-2**.
- **Outright:** vencedor do torneio / chegar à final.
- **Settlement (regra de anulação bet365):** se o 1º game não é completado → aposta de vencedor anulada; se muda o nº de games a jogar → placar exato/handicap anulados; abandono após 1º game completo → vencedor vale.

**Fontes:** regras oficiais SkyBet (espelha bet365), bet365 News (badminton betting odds), 1xBet, Oddspedia, Dabble. *(help.bet365 bloqueia fetch automatizado — 403; a captura ao vivo do §3 é a confirmação primária.)*

---

## 5. Dicionário do tradutor — rótulos por casa BR

| Padrão único (sugerido) | Betano | Superbet [proxy tênis] | bet365 (confirmado) |
|---|---|---|---|
| Vencedor da Partida | **Vencedor** | Vencedor do jogo | **Para Ganhar** |
| Vencedor do 1º Game | **Vencedor de cada set** | Vencedor do set | **1º Game - Para Ganhar** |
| Total de Games | **Mais do que 3 sets / Total de sets** | Total de Games | Total Games |
| Handicap de Games | Handicap de sets | Handicap de Games | **Handicap** (−1.5/+1.5) |
| Total de Pontos | Total de Pontos | Total de Pontos | **Total** / **Total de Pontos na Partida** |
| Handicap de Pontos | Handicap de Pontos | Handicap | **Partida - Handicap (Pontos)** |
| Placar em Games | Resultado exato | Placar exato em sets | **Partida - Resultado Correto** |

**Quem tem badminton hoje:**
- **bet365** — ✅ confirmado (China Open ao vivo, taxonomia completa acima).
- **Betano** — ✅ confirmado (BWF World Tour Finals etc.; usa "set" pro parcial).
- **Superbet** — ✅ oferece badminton (catálogo de mercados só inferido do tênis dela).
- **Esportiva, Betão, Multi, Jogo de Ouro** — ❌ provavelmente **não têm badminton** hoje (catálogos não listam; Esportiva/Jogo de Ouro têm só Tênis de Mesa como raquete). Confirmar manualmente no site logado antes de cadastrar qualquer `§9`.

> **Regra de sinônimo obrigatória:** no badminton, `set ≡ game ≡ jogo` = mesmo parcial. Cadastrar os três apontando pro mesmo objeto no tradutor.

---

## 6. Mapeamento para a taxonomia do Sharpen — RECOMENDAÇÃO + decisões

Badminton **não cria categoria nova**. Segue o molde do Tênis (`MASTER_APOSTAS §6`). Mapa proposto:

| Mercado badminton | Categoria Sharpen | Observação |
|---|---|---|
| Vencedor da partida (sem handicap) | **`ML`** | igual Tênis |
| Qualquer handicap (games OU pontos) | **`Handicap`** | a unidade vai na **descrição** (regra existente: handicap é handicap independentemente da unidade) |
| Total de parciais / placar em games (2-0, 2-1) | **`Sets`** ⚠️ *(decisão A)* | o parcial do badminton = "set" do tênis → categoria `Sets` (top-level). **Não** `Games` (que no Sharpen é a subunidade do tênis, inexistente no badminton) |
| Total/soma de pontos, handicap de pontos | **`Pontos`** ⚠️ *(decisão B)* | hoje `Pontos` diz "Basquete, eBasket, Vôlei" — precisa **estender a menção** pra incluir Badminton; senão cai em `Outros` |
| Total de pontos de UM jogador | **`Player Props`** | estatística individual |
| Comparativo entre 2 jogadores | **`H2H`** | igual Tênis |
| Cupom combinado / bet builder | **`Múltipla`** | regra geral |

### As 3 decisões que preciso de você
- **(A) Parcial → `Sets` ou `Games`?** Recomendo **`Sets`** (o parcial do badminton corresponde ao *set* do tênis; `Games` no Sharpen é a subunidade do tênis que o badminton não tem). Mas a bet365 rotula "Total **Games**" — daí a dúvida. *Não inventei uma terceira; decisão sua.*
- **(B) Pontos → estender `Pontos` ou usar `Outros`?** Recomendo **estender `Pontos`** pra citar Badminton (é literalmente aposta no objeto "ponto"), evitando lixo em `Outros`.
- **(C) Descrição do parcial: "game" ou "set"?** Recomendo **"game"** (termo oficial BWF) com "set" como sinônimo de entrada — mas se você preferir "set" pra alinhar com a Betano (maior volume BR), tudo bem. Afeta só o texto da descrição.

---

## 7. Reconhecimento em prints — jogadores e países (2026)

**Simples M:** Shi Yuqi (CHN), Kunlavut Vitidsarn (THA), Anders Antonsen (DEN), Jonatan Christie (INA), Christo Popov (FRA), Chou Tien-chen / Lin Chun-yi (TPE), Kodai Naraoka (JPN), Alex Lanier (FRA).
**Simples F:** An Se-young (KOR, nº1), Wang Zhiyi / Chen Yufei / Han Yue (CHN), Akane Yamaguchi (JPN).
**Duplas M:** Kim Won-ho/Seo Seung-jae (KOR), Fajar Alfian/Shohibul Fikri (INA), Chia/Soh (MAS), Satwik/Chirag (IND).
**Duplas F:** Liu Shengshu/Tan Ning (CHN), Baek Ha-na/Lee So-hee (KOR), Pearly Tan/Thinaah (MAS).
**Duplas Mistas:** Feng Yanzhe/Huang Dongping (CHN), Christiansen/Bøje (DEN), Chen Tang Jie/Toh Ee Wei (MAS), Dechapol/Supissara (THA).
**Países dominantes:** China, Coreia do Sul, Indonésia, Japão, Dinamarca, Malásia, Índia, Tailândia, Taiwan (TPE), França (em ascensão).

---

## 8. Calendário 2026 + sites de resultado (liquidação)

**Torneios de maior liquidez (ordem prática):** Super 1000 (Malaysia jan, All England mar, **China jul**, Indonesia) > Mundial (Nova Délhi, 17-23 ago) > Super 750 > Thomas/Uber Cup > Super 500 > World Tour Finals. **Sem Olimpíadas e sem Sudirman Cup em 2026.**

**Sites p/ conferir liquidação (ordem de confiança):**
1. **BWF oficial / tournamentsoftware** — `bwfbadminton.com`, `bwf.tournamentsoftware.com` — canônico, placar game-a-game (inclui deuce/cap). *(bloqueia fetch automatizado; abre no navegador.)*
2. **Flashscore** — `flashscore.com/badminton/` — ao vivo, placar por game, histórico.
3. **Sofascore** — `sofascore.com/badminton` — ao vivo, stats, histórico por jogador.
- Apoio: AiScore, Livesport.

---

## 9. Plano de propagação (arquivos a tocar) — PROPOSTAS prontas pra colar

> Tudo abaixo é **proposta** — aguarda seu OK. Aplicar uma por vez.

### 9.1 `global/MASTER_ESPORTES_2026.md`
- **§4** — adicionar `Badminton` aos exemplos válidos.
- **§7** — nova sub-seção (molde do Tênis):
  ```markdown
  ## Badminton

  Valor oficial:

  ```text
  Badminton
  ```

  Sinônimos:
  - BADMINTON
  - BWF
  - BWF WORLD TOUR
  - ALL ENGLAND
  - THOMAS CUP
  - UBER CUP
  - SUDIRMAN CUP
  ```
- **§7 → Referências auxiliares — Badminton** (atletas do §7 deste relatório) pra desambiguar ML/H2H.
- **Regra Crítica — Badminton vs Tênis:** ambos são raquete e usam "sets"/parciais; o discriminante é **liga BWF + atletas de badminton**. Badminton usa "pontos"/"rally"; tênis usa "games"/"ace"/"break". `set ≡ game ≡ jogo` no badminton.
- Estender a desambiguação de `Sets` (Vôlei↔Tênis) pra citar Badminton (jogador individual + parciais, distinto do Tênis pela liga/atleta).

### 9.2 `global/MASTER_APOSTAS_2026.md`
- **§6** — nova sub-seção `## Badminton` (molde exato do Tênis, linhas 932-997):
  ```markdown
  ## Badminton

  ### Resultado principal
  Sem handicap:  ML
  Com handicap:  Handicap

  ### Total de parciais (games/sets)
  Sets            ← decisão A

  ### Total de pontos
  Pontos          ← decisão B (estender a categoria)

  ### Estatísticas individuais
  Player Props

  ### Regras Críticas — Badminton
  Badminton utiliza: pontos, games (= sets)
  Nunca utilizar: legs, frames, aces
  set ≡ game ≡ jogo (mesmo parcial; casas divergem no rótulo)
  ```
- Se **decisão B = sim**: ajustar §3/§5/§7 da categoria `Pontos` pra incluir Badminton na lista de esportes de "objeto ponto".

### 9.3 `global/MASTER_DESCRICAO_2026.md`
- **§13** — nova sub-seção (molde do §13.1 Tênis):
  ```markdown
  ## 13.x Badminton

  ### ML
  Viktor Axelsen [Axelsen v Vitidsarn]

  ### Sets
  Under 2.5 Games [Axelsen v Vitidsarn]     ← "Games" ou "Sets" conforme decisão C

  ### Handicap
  Axelsen -1.5 Games [Axelsen v Vitidsarn]
  Axelsen -6.5 Pontos [Axelsen v Vitidsarn]

  ### Pontos
  Over 41.5 Pontos [Axelsen v Vitidsarn]

  ### Player Props
  Axelsen - Over 21.5 Pontos [Axelsen v Vitidsarn]
  ```

### 9.4 Emoji/UI — 🏸 nos 3 espelhos (senão renderiza com o fallback 🏅)
- `app/static/index.html` (~4387) · `app/static/dash/assets/js/data.js` (~149) · `docs/REFERENCIA_EMOJIS_ESPORTES.md`.

### 9.5 Casas (`casas/CASA_*.md §9`) — **só sob demanda**
- Quando um bilhete real de badminton aparecer numa casa, adicionar 1-3 linhas no `§9` dela usando o dicionário do §5. Começar por **bet365** e **Betano** (as que confirmadamente têm). Nada mais; casas são auto-descobertas.

---

## 10. Riscos / pontos de atenção

1. **Não hardcodar 21 pontos** — 3×21 em 2026, 3×15 a partir de 04/01/2027 (Índia doméstica já em jul/2026). Constante: melhor de 3 + vantagem de 2.
2. **`set`/`game`/`jogo` são o mesmo parcial** — divergência entre casas é só rótulo.
3. **Badminton não tem empate** — mercados sempre 2-way; nunca esperar "X".
4. **Placar tem 2 níveis** — games (2-0/2-1, máx 3) vs pontos (até 21/30). Vencedor depende só dos games.
5. **Dois handicaps distintos** — games (±1.5) vs pontos (spread largo). A unidade tem de ir na descrição pra não confundir na hora de liquidar.
6. **Casas pequenas** (Esportiva, Betão, Multi, Jogo de Ouro) — confirmar se têm badminton antes de cadastrar `§9`.

---

*Documento gerado por pesquisa automatizada + captura ao vivo. Fontes citadas ao longo das seções. Nenhuma edição foi aplicada aos MASTERs — aguardando revisão do Feca.*
