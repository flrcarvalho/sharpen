# CASA_BET365
## Camada de tradução — Bet365 → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Bet365.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Bet365`
- Locale: pt-BR · Moeda: R$ (prefixo: `R$250,00`) · Decimal: vírgula
- `Parceiro` / `Tipster`: não preenchidos na extração (vêm da app).

---

## 2. Modo de ingestão e layout

- **Modo de ingestão: visão (screenshot). Sem export estruturado.**
- **Feed contínuo:** múltiplos prints = mesmo scroll. 1º print = mais recente; dentro do print, topo = mais recente.
- **Ordenação de output:** última aposta da última imagem = 1ª linha no TSV (mais antiga); 1ª aposta da 1ª imagem = última linha no TSV (mais recente). Processar de baixo para cima dentro de cada imagem, das imagens da última para a primeira.
- Abas: `Em Aberto` · `Encerrar Aposta` (cashout) · `Ao Vivo` · `Resolvidas`.

**Sinal visual de esporte:** A Bet365 exibe ícone de camisa colorida (jersey icon) ao lado de **times** e nenhum ícone (ou foto pequena) ao lado de **jogadores individuais**.

| Sinal visual | Participantes | Esporte provável |
|---|---|---|
| Jersey icon visível | Nomes de times/países | Futebol, Basquete… (esporte de equipe) |
| Sem jersey icon | Nomes de **pessoa** | Tênis, Dardos… (esporte individual) |
| **Sem jersey icon** | Nomes de **países/seleções** | **Vôlei** (ou outro esporte coletivo sem jersey na Bet365) |

> **Futebol entre seleções → jersey icon presente.** Bélgica, Brasil, Alemanha em partidas de Futebol aparecem com o ícone de camisa colorida ao lado.
>
> **Vôlei entre seleções → sem jersey icon.** Canadá, Turquia, Bulgária, Sérvia em partidas de Vôlei aparecem apenas com o nome do país em texto, sem ícone. Confirme pelo placar: 2–3 ou 0–3 indica sets de Vôlei, não gols.

> **Nota §12:** o jersey icon é ruído para extração de dados (mercado, seleção, odd), mas **não é ruído para classificação de esporte**. Leia a presença/ausência do ícone para determinar o esporte; ignore o ícone ao montar a Descrição. São usos distintos da mesma informação visual.

Anatomia de um bilhete:

1. **Cabeçalho verde (sup. esq.):** `R$<stake> <Tipo>` (em sistema: `N x R$<stake-por-linha> <Tipo>`). Marca o início do bilhete **e** define a estrutura: `Simples` · `Dupla` · `Tripla` · `Triplas` · `Múltiplas` · `Criar Aposta` · `3 x Duplas` · `Trixie` · `Yankee`… O Tipo determina a categoria `Aposta` (Simples → categoria do mercado; o resto → `Múltipla`) e, em sistema, **qual fórmula de odd** usar (`MASTER_RESULTADO_2026 §7`).
2. **Rótulo de status (sup. dir.):** `Perdida` / `Anulado` / `Reembolso(Push)` / vazio (= ganho).
3. **Seleções (meio):** negrito = seleção + linha; sublinha = mercado; tags por perna (`Anulado`, `½ Ganho`, `½ Perdido`, `½ Anulado`, `SUBSTITUIÇÃO+`); confronto com placar; ✓/✗; barras de progresso com número = stat ao vivo (ignorar).
4. **Bloco financeiro final:** `Aposta` · `Retorno Total` · `Retorno Obtido`.

---

## 3. ID do bilhete (deduplicação)

- A Bet365 **não expõe ID de bilhete** no recorte → dedup por **assinatura derivada** = `data + Aposta (stake) + Retorno Obtido + confronto(s)`.
- Contagem = nº de cabeçalhos verdes (1 cabeçalho = 1 bilhete = 1 linha).

---

## 4. Data

A Bet365 **não expõe a data do evento** no bilhete (confirmado). Como é a casa mais usada, a data segue uma cadeia de duas opções:

1. **Data informada pela operação** — você passa a data do lote no momento da extração (a app fornece ao extrator). Fonte primária.
2. **Fallback:** na ausência de data informada, usar a **data atual no fuso de Brasília** (`America/Sao_Paulo`, UTC−3).

> ⚠️ O fallback é fixado no fuso de Brasília **de propósito**: o sistema roda em servidor (Railway, provável UTC). Sem fixar o fuso, à noite a data sairia um dia adiantada.

Nunca usar data de colocação/registro. Formato final: `DD/MM/AAAA`.

---

## 5. Status e Resultado

Resultado do bilhete (rótulo sup. dir. + bloco financeiro):

| Bet365 exibe | Código |
|---|---|
| ✓ verde / sem "Perdida" + Retorno Obtido > 0 | W |
| `Perdida` no cabeçalho (qualquer RO) | L |
| Retorno Obtido `R$0,00` (qualquer rótulo) | L |
| `Anulado` / `Anulada` / `Reembolso(Push)` / `Void` | V |

> ⚠️ **Rótulo "Perdida" tem prioridade absoluta:** se o cabeçalho diz `Perdida`, o resultado é L MESMO QUE o campo `Retorno Obtido` pareça mostrar valor > R$0,00. Isso indica erro de leitura OCR (símbolo `$` confundido com o dígito `5`, e.g. "R$0,00" lido como "R50"). O valor real é sempre R$0,00 quando o bilhete está marcado como `Perdida`. Não calcule `RO ÷ Stake` neste caso.

**Meia-liquidação (HW/HL) — gatilho confirmado:** a Bet365 não usa um rótulo "Half Win" inteiro; ela marca as **metades como tags na seleção**. O líquido é a soma:

| Tags na seleção | Código |
|---|---|
| `½ Ganho` (+ `½ Anulado`) | HW |
| `½ Perdido` (+ `½ Anulado`) | HL |

- Gatilho primário = a tag `½`. Conferência = assinatura financeira (exata): `HW → RO = (Stake/2)·(Odd+1)`; `HL → RO = Stake/2`.
- Só ocorre em linha asiática que meio-liquida (`.25`/`.75` ou linha dividida `-1.0,-1.5`).
- **`Anulado`** (cheio) numa perna = perna totalmente void; **`½ Anulado`** = metade do bilhete devolvida (parte da meia-liquidação). Não confundir.

Aba `Em Aberto` → `extraction_state = aberta` (fora da fila). Códigos e regra de odd: `MASTER_RESULTADO_2026`.

---

## 6. Boost / promoção

A Bet365 tem boost/promo. Quando houver, o **Retorno Obtido já reflete o valor final** → em W, `Odd = Retorno Obtido ÷ Aposta` captura o boost naturalmente (global).

<!-- TODO: confirmar o rótulo visual do boost (ex.: "Bet Boost" / "Aumento"). Sem amostra ainda. -->

---

## 7. Cashout

- Localizador: aba `Encerrar Aposta` / rótulo `Cash Out`.
- Encerrado → **Retorno Obtido = valor do cashout** → `Resultado = W`, `Odd = Retorno Obtido ÷ Aposta` (global, §5.6).
- Exceção: se `Retorno Obtido = Aposta` → `Resultado = V`, odd exibida (sem ganho nem perda).
- Distinguir de meia-liquidação: cashout dá um RO parcial **arbitrário** que NÃO casa com `Stake/2` nem `(Stake/2)(Odd+1)`; meia-liquidação casa exato (ver §5).

> **O `Retorno Obtido` é a fonte financeira única da Bet365:** resolve W, L, V, HW/HL, cashout e boost. Por isso tem prioridade máxima (§10).

<!-- TODO: confirmar o rótulo visual num bilhete encerrado real. Sem amostra ainda. -->

---

## 8. Bônus

<!-- TODO: confirmar se a casa opera com bônus/freebets e qual a política de tratamento (excluir / marcar / incluir). Sem amostra ainda. -->

---

## 9. Mapa de mercados (Bet365 → `Aposta` global)

| Bet365 exibe | Aposta global |
|---|---|
| Para Ganhar a Partida / Para Vencer a Partida | ML |
| Handicap Asiático ("Ao-Vivo - …" = só ao vivo, ignorar p/ categoria) | Handicap |
| Handicap Asiático - Cartões | Cartões |
| Total de Escanteios (Asiáticos) / "Total de Escanteios - 3 Opções" | Escanteios |
| Total de cartões asiáticos | Cartões |
| Para o Jogador Receber Cartão | Cartões |
| Para Marcar a Qualquer Momento | Anytime |
| Para Marcar 2 ou Mais / dois ou mais Gols | Anytime (descr. `- 2+ Gols`) |
| Para Marcar um Hat-trick / três ou mais Gols | Anytime (descr. `- Hat-trick`) |
| Jogador a Dar Assistência | Assistência |
| Total de Hits, Runs e RBIs (Baseball) / Lançador - Strikeouts | Player Props |
| Pontos / Rebotes / Assistências / Cestas de 3 Convertidas / Pontuação Alta (NBA/WNBA) | Player Props |
| Total de Kills / Total de Dragons / Total de Torres ("Mapa N - …") | E-Sports Props |
| Partida - Vencedor | ML |
| Para Sofrer Falta / Para Dar Passe / outros props estatísticos individuais de jogador (Futebol) | Player Props |
| **Mais 180's** (Dardos — comparativo entre dois jogadores) | **H2H** |
| **Criar Aposta** (container) | **Múltipla** |

Notas de reconstrução:
- **Mais 180's (H2H Dardos):** o bilhete exibe dois nomes de jogadores sem o formato `A v B` explícito. O primeiro nome (em negrito / topo) = jogador apostado; o segundo nome (abaixo) = adversário. Reconstruir confronto: `[apostado v adversário]`. Descrição: `Jogador - Mais 180's [Jogador A v Jogador B]`.
- **Criar Aposta** → sempre `Múltipla`, UMA linha por bilhete, mesmo com seleções do mesmo jogo e mesmo **cruzando vários confrontos** (junta tudo com ` // `).
- Mesmo jogador, vários mercados → `Jogador - Mercado A / Mercado B [Confronto]` (`MASTER_DESCRICAO_2026 §12.4`).
- **Marcador com limiar (2+/3+/hat-trick):** categoria sempre `Anytime`; o limiar vai na descrição (`- 2+ Gols` / `- Hat-trick`, ver `MASTER_DESCRICAO_2026 §12.1`). O sinal é a **linha "Para Marcar…"** (presente em todo card); o parêntese ao lado do nome (`(2 ou Mais)`, `(A Qualquer Altura)`) é inconsistente / qualificador — não usar como fonte. Sem o limiar, uma série 1+/2+/3+ do mesmo jogador vira linhas idênticas.
- `Mais de` / `Menos de` → Over / Under.
- **Handicap de objeto estatístico:** a categoria segue o **objeto** (`MASTER_APOSTAS §1`). `Handicap Asiático - Cartões` → `Cartões`; a linha de handicap (`+/-N`) vai só na descrição. Handicap sobre o resultado/gols continua `Handicap`.
- Handicap asiático **split** aparece como linha dupla (`-1.0,-1.5`, `0.0,+0.5`) → manter a linha como exibida; pode gerar HW/HL/V (ver §5).
- "Mapa N - …" / "Time Visitante - …" são qualificadores de contexto; entram na descrição conforme o master, mas não mudam a categoria.

---

## 10. Stake

- Campo `Aposta` no bloco financeiro final = stake **total** do bilhete (em sistema, é o total, não o `R$ por linha` do cabeçalho verde). `R$900,00` → `900,00`.
- Normalização = global (`MASTER_OUTPUT_2026 §11/§16`).

---

## 11. Odds

`Retorno Obtido` é a fonte do **valor** financeiro — não confundir com `Retorno Total` (potencial/bruto); usar sempre o **Obtido**. A odd só é **derivada** do RO quando há retorno positivo real:

- `W` (e cashout / boost) → `Odd = Retorno Obtido ÷ Aposta`

> ⚠️ **Para W: a odd exibida no cabeçalho do bilhete (ex: `1,83`) é a odd de colocação — IGNORAR.** Ela pode diferir do cálculo real por boost, arredondamento ou promoção. Usar SEMPRE `Retorno Obtido ÷ Aposta` com precisão total; nunca a odd do cabeçalho.

- `L` → **odd EXIBIDA no bilhete** (RO = R$0,00). NUNCA derivar do RO — daria `0,00`.
- `HL` → **odd EXIBIDA**. NUNCA usar metade nem derivar do RO.
- `HW` → odd EXIBIDA.
- `V` → RO = Aposta → odd exibida.

**Sistemas (Duplas/Triplas/Trixie/Yankee…):**
- Ganho (RO > 0), inclusive **com perna anulada** → `Odd = Retorno Obtido ÷ Aposta`. O colapso da perna void já está embutido no RO; não recalcular fórmula. (Ex.: 3x Duplas, stake 900, perna anulada, RO 2940 → odd `3,2667`.)
- Perdido inteiro (RO = 0) → odd **estrutural** pela fórmula do `MASTER_RESULTADO_2026 §7`, preservando a perna anulada como odd `1,00` na estrutura. (Caso mais complexo — ex.: Trixie com perna anulada + demais perdidas.)

> ⚠️ Regra crítica (global): em `L` a odd nunca vira `0,00`; em `HL` nunca vira `0,50`/metade; em `V` nunca vira `1,00`. A odd original é **preservada**. `RO ÷ Aposta` vale só para W / cashout / boost / sistema ganho.

Precisão da odd calculada: preservar (global).

---

## 12. Ruído a ignorar

Barras de progresso com número (stat ao vivo) · placares e scoreboards ao vivo · ícones de camisa/play · `Reutilizar Seleções` · `Líder por X` · prefixos de placar `(1-0)` · `Ao-Vivo` · badge `SUBSTITUIÇÃO+` — layout visual obrigatório (leia com atenção):
  ```
  ▲ Danilo dos Santos   ← SUBSTITUTO (entrou em campo) → IGNORAR
  ▼ Bruno Guimarães     ← ORIGINAL apostado (tachado/strikethrough) → USAR NA DESCRIÇÃO
  ```
  - Linha **superior** (nome em negrito, ícone ▲, pode ter ✕ vermelho): substituto → **IGNORAR**
  - Linha **inferior** (nome em **tachado/strikethrough**, ícone ▼): jogador original → **USAR**
  - ⚠️ O tachado/strikethrough **NÃO significa "ignorar"** — é o oposto: é o nome que deve ser preservado na Descrição.
  - ⚠️ O nome em negrito no topo é visualmente mais chamativo mas é o **substituto** — não usar.
(As tags `Anulado` / `½ Ganho` / `½ Perdido` / `½ Anulado` **não** são ruído — são sinais de resultado, ver §5.)

---

## 13. Pegadinhas (resumo rápido)

- O **tipo** do bilhete (Simples/Múltipla/Sistema) está no **cabeçalho verde** → define categoria e fórmula de odd.
- **`Retorno Obtido`** (não `Retorno Total`) é a verdade financeira; resolve todos os desfechos.
- HW/HL vêm como tags `½ Ganho` / `½ Perdido` (+ `½ Anulado`), não como rótulo único.
- Perna `Anulado` em sistema/múltipla: preservar na descrição; se o bilhete ganhou, `RO ÷ Aposta` já embute o void.
- `Criar Aposta` = 1 linha `Múltipla`, pode cruzar vários jogos.
- NBA / WNBA → **Basquete** (regra liga≠esporte).
- Data: a Bet365 não expõe — usar data informada; fallback Brasília do dia (ver §4).
- Sem ID visível → dedup por assinatura.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

- 1 cabeçalho verde = 1 bilhete = 1 linha.
- `Retorno Obtido` usado, nunca `Retorno Total`.
- Todo `Criar Aposta` colapsado em 1 linha; pernas anuladas preservadas.

---

## 15. Exemplos golden (bilhetes reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`
(Sem data informada nos exemplos → fallback Brasília do dia, 12/06/2026, conforme §4.)

**#1 — W, Simples ML Tênis:**
```
12/06/2026	Tênis		Bet365		ML	Mary Stoiana [Mary Stoiana v Tatiana Prozorova]	250,00	2,25	W
```

**#2 — L, Simples ML Tênis (odd do bilhete, RO 0):**
```
12/06/2026	Tênis		Bet365		ML	Dmitry Popko [Dmitry Popko v Enzo Aguiard]	250,00	2,10	L
```

**#3 — V, Criar Aposta anulado, mesmo jogador / WNBA→Basquete:**
```
12/06/2026	Basquete		Bet365		Múltipla	Kiki Iriafen - 10+ Pontos / 10+ Rebotes [TOR Tempo v WAS Mystics]	201,00	3,00	V
```

**#4 — W, Criar Aposta NBA→Basquete, dois jogadores (odd = RO ÷ Aposta):**
```
12/06/2026	Basquete		Bet365		Múltipla	De'Aaron Fox - 1+ Cestas de 3 [SA Spurs v NY Knicks] // Mitchell Robinson - Under 3.5 Pontos [SA Spurs v NY Knicks]	151,00	2,45	W
```

**#5 — HW, Handicap asiático split, `½ Ganho ½ Anulado` (odd exibida; RO = (S/2)(O+1)):**
```
12/06/2026	Futebol		Bet365		Handicap	Canadá (F) -1.5,-2.0 [Canadá (F) v Coreia do Sul (F)]	250,00	1,875	HW
```

**#6 — HL, Handicap asiático split, `½ Perdido ½ Anulado` (odd exibida; RO = S/2):**
```
12/06/2026	Futebol		Bet365		Handicap	Macarthur Rams (F) -1.0,-1.5 [Macarthur Rams (F) v Illawarra Stingrays (F)]	265,15	1,825	HL
```

**#7 — W, sistema 3x Duplas com perna anulada (odd = RO ÷ Aposta = 2940/900):**
```
12/06/2026	Futebol		Bet365		Múltipla	Carlos Chupete [Real Zaragoza v Málaga] // Giorgi Guliashvili [Racing Santander v Cadiz] // Nikolai Hristov [Strommen v Sogndal]	900,00	3,2667	W
```

**#8 — W, Simples E-Sports Props (Total de Torres, mapa):**
```
12/06/2026	E-Sports		Bet365		E-Sports Props	Under 11.5 Torres [Team Secret Whales v Deep Cross Gaming]	303,00	1,80	W
```

**#9 — L, Simples Anytime com SUBSTITUIÇÃO+ (usar nome tachado = original):**
```
13/06/2026	Futebol		Bet365		Anytime	Bruno Guimarães [Brasil v Marrocos]	300,00	7,00	L
```
> Layout do bilhete: `▲ Danilo dos Santos 7.00` (substituto, negrito, topo) / `▼ Bruno Guimarães` (original, tachado, abaixo). Usar "Bruno Guimarães" — o tachado é o original apostado.

**#10 — Série marcador com limiar (mesmo jogador, mercados distintos → limiar na descrição; SUBSTITUIÇÃO+ usa nome tachado):**
```
13/06/2026	Futebol		Bet365		Anytime	Daniel Rios [Vancouver FC v CF Montreal]	8,44	2,75	W
13/06/2026	Futebol		Bet365		Anytime	Daniel Rios - 2+ Gols [Vancouver FC v CF Montreal]	50,60	13,00	L
13/06/2026	Futebol		Bet365		Anytime	Daniel Rios - Hat-trick [Vancouver FC v CF Montreal]	13,26	67,00	L
```
> Três mercados do mesmo jogador: "Para Marcar a Qualquer Momento" (1+, sem sufixo), "Para Marcar 2 ou Mais" (`- 2+ Gols`) e "Hat-trick / três ou mais Gols" (`- Hat-trick`). Sem o limiar na descrição as três linhas ficariam idênticas. Nome = tachado (original `Daniel Rios`), não o substituto Prince Osei Owusu.

---

## Feedback para a camada global / MODELO (passe de revisão)

1. **Modo de ingestão (primário + fallback):** Bet365 = visão única; Pinnacle = export primário + visão fallback. O campo do MODELO precisa dos dois slots.
2. **Padrão "tipo do bilhete no cabeçalho":** rótulo fixo declara simples/múltipla/sistema → define categoria e fórmula de odd. Registrar no §2 do MODELO.
3. **Padrão "campo financeiro único":** Bet365 `Retorno Obtido`, Superbet `PRÊMIO`/`REEMBOLSO` resolvem todos os desfechos (incl. classificar HW/HL pela assinatura exata). Conceituar no §10 do MODELO.
4. **Data — DECIDIDO:** cadeia `evento → informada → Brasília-hoje` (colocação nunca). Vira adição ao `MASTER_OUTPUT_2026 §4`.
5. **HW/HL — gatilho:** alguns layouts mostram a meia-liquidação como tags de metade (`½ Ganho`/`½ Perdido`/`½ Anulado`), não como rótulo único; a assinatura financeira (`RO = S/2` / `(S/2)(O+1)`) confirma e separa de cashout. Útil no §5 do MODELO.

---

VERSÃO: 2026
STATUS: QUASE COMPLETO (pendências: §6 rótulo boost, §7 rótulo cashout)
CASA: Bet365
