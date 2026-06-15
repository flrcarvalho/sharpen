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
- **Feed contínuo:** múltiplos prints = mesmo scroll. 1º print = mais recente; dentro do print, topo = mais recente. Processar **baixo → cima**; output **antigo → recente** (inversão = global, `MASTER_OUTPUT_2026 §15`).
- Abas: `Em Aberto` · `Encerrar Aposta` (cashout) · `Ao Vivo` · `Resolvidas`.

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
| `Perdida` / Retorno Obtido `R$0,00` | L |
| `Anulado` / `Anulada` / `Reembolso(Push)` / `Void` | V |

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
| Handicap Asiático (incl. "- Cartões", "Ao-Vivo - …") | Handicap |
| Total de Escanteios (Asiáticos) / "Total de Escanteios - 3 Opções" | Escanteios |
| Total de cartões asiáticos | Cartões |
| Para o Jogador Receber Cartão | Cartões |
| Para Marcar a Qualquer Momento | Anytime |
| Jogador a Dar Assistência | Assistência |
| Total de Hits, Runs e RBIs (Baseball) / Lançador - Strikeouts | Player Props |
| Pontos / Rebotes / Assistências / Cestas de 3 Convertidas / Pontuação Alta (NBA/WNBA) | Player Props |
| Total de Kills / Total de Dragons / Total de Torres ("Mapa N - …") | E-Sports Props |
| **Criar Aposta** (container) | **Múltipla** |

Notas de reconstrução:
- **Criar Aposta** → sempre `Múltipla`, UMA linha por bilhete, mesmo com seleções do mesmo jogo e mesmo **cruzando vários confrontos** (junta tudo com ` // `).
- Mesmo jogador, vários mercados → `Jogador - Mercado A / Mercado B [Confronto]` (`MASTER_DESCRICAO_2026 §12.4`).
- `Mais de` / `Menos de` → Over / Under.
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

Barras de progresso com número (stat ao vivo) · placares e scoreboards ao vivo · ícones de camisa/play · `Reutilizar Seleções` · `Líder por X` · prefixos de placar `(1-0)` · `Ao-Vivo` · tag promocional `SUBSTITUIÇÃO+`.
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

- 1 cabeçalho verde = 1 bilhete = 1 linha.
- `Retorno Obtido` usado, nunca `Retorno Total`.
- Em L/HL/V a odd é a exibida (nunca 0,00 / metade / 1,00).
- Todo `Criar Aposta` colapsado em 1 linha; pernas anuladas preservadas.
- Liga (NBA/WNBA) não usada como Esporte.

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
