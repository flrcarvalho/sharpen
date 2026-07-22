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

- **Modo de ingestão primário: TEXTO via API de Histórico (SharpenUp `b3_inject`).** O robô lê
  as respostas de `/sportshistoryapi/summary` + `/confirmation` (formato `F|00;…`) do
  **Histórico** (Resolvidas + Pendentes) — dado exato: código estável `BR`, resultado, stake,
  odd, jogo/mercado, e **data de encerramento** (kickoff + folga por esporte, UK→Brasília).
  Detalhes em `docs/PLANO_BET365_CAPTURA_API.md`.
- **Fallback: visão (screenshot) / DOM.** Se a API não responder (token do replay recusado, ou
  a aba do Histórico não foi aberta), o robô raspa os cards `.myb-SettledBetItem` (texto do DOM),
  e o print manual continua valendo. As regras de layout abaixo valem para esse caminho.
- **Feed contínuo:** múltiplos prints = mesmo scroll. 1º print = mais recente; dentro do print, topo = mais recente.
- **Ordenação de output:** emita os bilhetes na **ORDEM NATURAL DE LEITURA** — de cima para baixo dentro de cada imagem, e da 1ª imagem para a última (no modo texto do robô, na ordem em que aparecem, marcados por `[Bilhete Bet365]`). **NÃO inverta você mesmo.** O **sistema** reordena automaticamente para mais-antigo→mais-recente (a planilha exige essa ordem). O resultado final salvo fica: última aposta da última imagem = 1ª linha (mais antiga); 1ª aposta da 1ª imagem = última linha (mais recente) — mas isso é responsabilidade do sistema, não sua.
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

1. **Cabeçalho verde (sup. esq.):** `R$<stake> <Tipo>` (em sistema: `N x R$<stake-por-linha> <Tipo>`). Marca o início do bilhete **e** define a estrutura: `Simples` · `Dupla` · `Tripla` · `Triplas` · `Múltiplas` · `Criar Aposta` · `Criar Aposta +` · `3 x Duplas` · `Trixie` · `Yankee`… O Tipo determina a categoria `Aposta` (Simples → categoria do mercado; o resto → `Múltipla`) e, em sistema, **qual fórmula de odd** usar (`MASTER_RESULTADO_2026 §7`).
   - ⚠️ **Só conta como bilhete o cabeçalho com prefixo `R$<stake>`.** Os sub-rótulos internos `CRIAR APOSTA <odd>` (verde/cinza, **sem `R$`**, ex.: `CRIAR APOSTA 4.50`) **não são cabeçalhos** — são **pernas** (cada uma um Bet Builder) dentro de uma super múltipla `Criar Aposta +`. Confirme pela **contagem de blocos financeiros no rodapé**: um só `Aposta / Retorno Obtido` = um só bilhete, por mais pernas `CRIAR APOSTA` que existam (ver §9, super múltipla).
2. **Rótulo de status (sup. dir.):** `Perdida` / `Anulado` / `Reembolso(Push)` / vazio (= ganho).
3. **Seleções (meio):** negrito = seleção + linha; sublinha = mercado; tags por perna (`Anulado`, `½ Ganho`, `½ Perdido`, `½ Anulado`, `SUBSTITUIÇÃO+`); confronto com placar; ✓/✗; barras de progresso com número = stat ao vivo (ignorar).
4. **Bloco financeiro final:** `Aposta` · `Retorno Total` · `Retorno Obtido`.

---

## 3. ID do bilhete (deduplicação)

- A Bet365 **não expõe ID de bilhete** no recorte → sem código, a dedup cai na **assinatura de conteúdo**.
- **Assinatura real (fonte da verdade: `app/repository.py::_assinatura`, ramo sem código):** `casa | parceiro | data | aposta (categoria) | descrição | odd` (odd normalizada a 2 casas). **Stake e Retorno Obtido NÃO entram.** Se este arquivo divergir do código, **o código vence** — atualize o texto aqui.
- ⚠️ **Consequência (limitação conhecida):** como a `descrição` (nomes lidos por OCR) e a `data` (informada por fora) compõem a identidade, qualquer variação nesses campos entre dois envios do MESMO bilhete gera **linha nova em vez de dedup** — um erro de OCR no nome é, ao mesmo tempo, um dado errado E uma duplicata. Reprocessar em outro dia também duplica (a `data` muda). Mitigações: fidelidade de nome (§12) + rede de segurança por `(casa, parceiro, stake, odd)` em `upsert_bilhetes` (avisa, não funde).
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
| Para Marcar Primeiro / Primeiro Marcador de Gol | Anytime (descr. `- Primeiro Marcador`) |
| Para Marcar Por Último / Último Marcador de Gol | Anytime (descr. `- Último Marcador`) |
| Jogador a Dar Assistência | Assistência |
| Total de Hits, Runs e RBIs (Baseball) / Lançador - Strikeouts | Player Props |
| Pontos / Rebotes / Assistências / Cestas de 3 Convertidas / Pontuação Alta (NBA/WNBA) — **de jogador** | Player Props |
| **Totais do Jogo** / **Total - 2 Opções** (Basquete / eBasket — total do jogo) | **Pontos** |
| Total de Kills / Total de Dragons / Total de Torres ("Mapa N - …") | E-Sports Props |
| Partida - Vencedor | ML |
| Para Sofrer Falta / Para Dar Passe / outros props estatísticos individuais de jogador (Futebol) | Player Props |
| **Mais 180's** (Dardos — comparativo entre dois jogadores) | **H2H** |
| **Criar Aposta** (container) | **Múltipla** |

Notas de reconstrução:
- **Mais 180's (H2H Dardos):** o bilhete exibe dois nomes de jogadores sem o formato `A v B` explícito. O primeiro nome (em negrito / topo) = jogador apostado; o segundo nome (abaixo) = adversário. Reconstruir confronto: `[apostado v adversário]`. Descrição: `Jogador - Mais 180's [Jogador A v Jogador B]`.
- **Criar Aposta** → sempre `Múltipla`, UMA linha por bilhete, mesmo com seleções do mesmo jogo e mesmo **cruzando vários confrontos** (junta tudo com ` // `).
- **Criar Aposta + (super múltipla) → ainda UMA linha.** Quando o cabeçalho verde é `Criar Aposta +` e o corpo traz **vários blocos `CRIAR APOSTA <odd>`** (cada bloco = um Bet Builder, com sua própria odd), é **um único bilhete** (um só `R$<stake>` no topo, um só bloco financeiro no rodapé). NÃO quebrar em uma linha por bloco. Regras:
  - **Contagem:** 1 bilhete = 1 linha. Nº de blocos `CRIAR APOSTA` é irrelevante para a contagem.
  - **Odd:** **produto** das odds dos blocos (ex.: `4.50 × 5.50 × 6.00 × 6.00 = 891,00`). Em `L` (RO = 0) essa é a **odd estrutural** exibida — mesma lógica de sistema perdido do §11; nunca `0,00`. Em `W`/cashout, vale a regra global `Odd = Retorno Obtido ÷ Aposta` (§11).
  - **Descrição:** junta **todas** as seleções de **todos** os blocos com ` // `, na ordem de leitura, cada uma com seu `[Confronto]` (§12.4 do MASTER_DESCRICAO). Pernas com `SUBSTITUIÇÃO+` usam o nome **original tachado** (§12).
- Mesmo jogador, vários mercados → `Jogador - Mercado A / Mercado B [Confronto]` (`MASTER_DESCRICAO_2026 §12.4`).
- **Marcador — sufixo OBRIGATÓRIO (2+/3+/hat-trick/Primeiro/Último):** categoria sempre `Anytime`; o mercado vai na descrição (`- 2+ Gols` / `- Hat-trick` / `- Primeiro Marcador` / `- Último Marcador`, ver `MASTER_DESCRICAO_2026 §12.1`). O sinal é a **linha "Para Marcar…"** (presente em todo card); o parêntese ao lado do nome (`(2 ou Mais)`, `(A Qualquer Altura)`) é inconsistente / qualificador — não usar como fonte. ⚠️ **Sem o sufixo, bilhetes DISTINTOS colapsam numa descrição idêntica** e são confundidos com duplicata — ex. real: Mbappé `Primeiro Marcador` (W) e `Último Marcador` (L), mesma stake e odd, viravam ambos `Kylian Mbappe [França v Marrocos]`. O `[Confronto]` é igualmente obrigatório em todo bilhete de jogador/props: sem ele, o mesmo mercado em jogos diferentes também colapsa (ex.: `De'Aaron Fox - 7+ Assistências` sem confronto, dois jogos distintos).
- `Mais de` / `Menos de` → Over / Under.
- **`Totais do Jogo` / `Total - 2 Opções` são rótulos genéricos — a categoria segue o objeto (`MASTER_APOSTAS §1`), não o rótulo.** Em Basquete / eBasket / Vôlei o objeto é ponto → `Pontos`. Em Futebol o mesmo tipo de mercado aparece como `Gols + -` → `Gols`. Nunca classificar total de jogo como `Team Props` (é a soma dos dois times, não estatística de equipe), `Games` (unidade do Tênis) nem `Handicap`.
- **eBasket (basquete virtual):** times da NBA com **handle do gamer entre parênteses** — `OKC Thunder (BRAZEN) v NY Knicks (EQUALIZER)` → Esporte `eBasket`, nunca `Basquete` nem `E-Sports` (`MASTER_ESPORTES_2026` — Regra Crítica Basquete vs eBasket). Confirmação: linha de pontos na faixa ~80–130 (NBA real ~220). ⚠️ **O handle é OBRIGATÓRIO na descrição** (`MASTER_DESCRICAO_2026 §13.3`): sem ele, `DAL Mavericks (TD24) v CHA Hornets (HYPER)` e `CHA Hornets (PROTOTYPE) v DAL Mavericks (GALAXY)` colapsam no mesmo confronto e bilhetes distintos viram duplicata.
- **Placar do eBasket confirma o resultado:** os números à direita de cada time são pontos; a soma deve bater com a badge da barra de progresso (`OKC 49 + NY 52 = 101` vs `Mais de 92.5` → W).
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

> ⚠️ **Fidelidade de nome (a dedup depende disto):** transcreva nomes de jogador, time e confronto **exatamente como aparecem**, letra por letra — não normalize, não traduza, não "corrija" a grafia. A identidade do bilhete Bet365 é reconstruída da descrição (§3); um único caractere trocado por OCR gera uma **duplicata** (e um dado errado). Na dúvida entre duas leituras, prefira a que está visualmente mais nítida; nunca invente.

---

## 13. Pegadinhas (resumo rápido)

- O **tipo** do bilhete (Simples/Múltipla/Sistema) está no **cabeçalho verde** → define categoria e fórmula de odd.
- **`Retorno Obtido`** (não `Retorno Total`) é a verdade financeira; resolve todos os desfechos.
- HW/HL vêm como tags `½ Ganho` / `½ Perdido` (+ `½ Anulado`), não como rótulo único.
- Perna `Anulado` em sistema/múltipla: preservar na descrição; se o bilhete ganhou, `RO ÷ Aposta` já embute o void.
- `Criar Aposta` = 1 linha `Múltipla`, pode cruzar vários jogos.
- `Criar Aposta +` (super múltipla) = **ainda 1 linha**; os blocos internos `CRIAR APOSTA <odd>` (sem `R$`) são pernas, não bilhetes. Odd = **produto** das odds dos blocos.
- NBA / WNBA → **Basquete** (regra liga≠esporte).
- Data: a Bet365 não expõe — usar data informada; fallback Brasília do dia (ver §4).
- Sem ID visível → dedup por assinatura.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

- 1 cabeçalho verde = 1 bilhete = 1 linha.
- `Retorno Obtido` usado, nunca `Retorno Total`.
- Todo `Criar Aposta` colapsado em 1 linha; pernas anuladas preservadas.
- `Criar Aposta +` com N blocos `CRIAR APOSTA <odd>` = 1 linha, odd = produto das odds dos blocos (não N linhas de stake cheia).

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

**#11 — L, `Criar Aposta +` super múltipla, 4 Bet Builders num só bilhete (odd = produto = 4,50×5,50×6,00×6,00):**
```
11/07/2026	Futebol		Bet365		Múltipla	Harry Kane - 2+ Chutes ao Gol [Noruega v Inglaterra] // Erling Haaland - 2+ Chutes ao Gol [Noruega v Inglaterra] // Ambos os Times Marcam [Noruega v Inglaterra] // Mikel Oyarzabal - 2+ Chutes ao Gol [Espanha v Bélgica] // Lamine Yamal - 2+ Chutes ao Gol [Espanha v Bélgica] // Espanha para se Classificar [Espanha v Bélgica] // França para se Classificar [França v Marrocos] // Kylian Mbappe - 2+ Chutes ao Gol [França v Marrocos] // Michael Olise - 2+ Chutes ao Gol [França v Marrocos] // Argentina - Intervalo/Final do Jogo [Argentina v Suíça] // Argentina - Maior Número de Chutes ao Gol [Argentina v Suíça] // Argentina - Maior Número de Escanteios [Argentina v Suíça]	20,00	891,00	L
```
> Cabeçalho `R$20,00 Criar Aposta +`, quatro blocos `CRIAR APOSTA 4.50 / 5.50 / 6.00 / 6.00`, um só rodapé (`Aposta R$20,00 · Retorno Obtido R$0,00`). É **1 bilhete**, não 4. Odd = produto dos blocos = `891,00`. `Erling Haaland` e `Mikel Oyarzabal` = originais tachados sob `SUBSTITUIÇÃO+` (não os substitutos Jorgen Larsen / Nico Williams).

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
