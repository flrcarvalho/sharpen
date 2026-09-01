# CASA_BETANO
## Camada de tradução — Betano → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betano.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betano`
- Locale: pt-BR · Moeda: R$ (prefixo) · **Decimal vírgula, milhar com ponto** (`R$1.914,56` = mil novecentos e quatorze)
- `Parceiro` / `Tipster`: não preenchidos na extração (vêm da app).

---

## 2. Modo de ingestão e layout

### 2.0 Captura (SharpenUp) — uma aba por rodada

O robô lê a API da casa (`GET /api/ma/bet/bet-history-v3?settled=true|false`) e **exporta só a
lista da aba que está na tela**: em `Histórico → Apostas → Em aberto` saem só as abertas; em
`Liquidada`, só as liquidadas. Para capturar tudo, **rode nas duas abas** (duas rodadas).

Motivo (s209): a Betano é SPA — trocar de aba **não** recarrega a página, então o interceptador
acumula as duas listas na memória da aba. Antes desta regra, rodar em `Em aberto` depois de ter
passado pela `Liquidada` exportava as duas juntas. Além do token gasto à toa, o campo "parar no
ID" preenchido com um bilhete **liquidado** interrompia a varredura **antes** das abertas e elas
não saíam, sem erro na tela.

### 2.1 Modos legados (print / texto)

Dois modos:

- **Resolvidas → TEXTO** (copiar). É a fonte de gravação principal.
- **Abertas → screenshot** (telas). Ficam em `extraction_state = aberta` (fora da fila de cópia).

**Anatomia do bilhete resolvido (texto):**
1. Tipo + stake (`Tripla` / `Simples` / `Dupla` / `4-seleções` / `6-seleções` / `Criar Aposta`) + `R$51,00`
2. Linha-resumo das seleções
3. Resultado (`Perdida` / `Ganhou` / `Cash out`)
4. Por seleção: `seleção + odd` · mercado · confronto (`A - B`) · `Pontuação: X-Y`
5. `ID: <numérico>`
6. Data `DD/MM/AAAA - HH:MM`
7. `Ganhos: R$X`

**Tela de aberta:** tipo+stake · seleção+odd · mercado · confronto · **data do jogo** (`Esta noite 22:00` / `Amanhã 21:30`) · `Ganhos Potenciais` · botão `CASH OUT R$X`.

**Ordenação de output (texto copiado):** fim do texto = 1ª linha no TSV (mais antiga); início do texto = última linha no TSV (mais recente). Processar do fim para o início do texto colado.

---

## 3. ID do bilhete

- Formato: `ID: 20376457083` (numérico). Chave de dedup. Nunca vai no output.

---

## 4. Data  ⚠️ (limitação documentada)

Regra global: data = **data do resultado / evento**.

- **Resolvidas (texto):** trazem **uma** data `DD/MM/AAAA - HH:MM` que é a **data de colocação** (confirmado: bilhetes distintos com o mesmo timestamp exato — é o momento da aposta, não da liquidação). O texto resolvido **não expõe a data do evento**.
  - Como a maioria das apostas é colocada e resolvida no **mesmo dia**, a colocação coincide com o evento em granularidade diária → usar a data da colocação como **proxy do evento**.
  - ⚠️ Exceção: aposta colocada para jogo de **outro dia** (ex.: "Amanhã" na tela de aberta) sai com a data um dia adiantada. Marcar pra revisar quando o tipo de mercado indicar evento futuro.
- **Abertas (tela):** mostram a **data do jogo** (`Esta noite`/`Amanhã`, relativa à captura) — mas abertas não são gravadas. Algumas abertas só mostram a data de colocação (sem a do jogo).

Nunca usar a data de colocação quando a do evento estiver disponível. Formato final: `DD/MM/AAAA`.

---

## 5. Status e Resultado

| Betano exibe | Nosso código |
|---|---|
| Ganhou | W |
| Perdida | L |
| Cash out (Ganhos = stake) | V (ver §7) |

Conferência financeira: `Ganhos = 0` → L · `Ganhos = Aposta` → V · `Ganhos > Aposta` → W.

<!-- TODO: rótulo de void/anulada da Betano. Só apareceu "Anulado se o jogador não iniciar" como CONDIÇÃO de uma seleção, não como resultado liquidado. -->

---

## 6. Boost / promoção

Tem. Chama-se **`Criar Aposta Turbinada +N%`** e aparece como **rodapé** do card,
abaixo das seleções, só em bilhete `Criar Aposta` (bet builder). Valores vistos:
`+25%` e `+50%`.

> ⚠️ **O bônus é pago POR FORA da odd exibida.** A odd grande do topo do card é a
> odd SEM o bônus, e o card mostra os dois valores separados. A odd real é:
>
> ```
> odd_real = 1 + (odd_exibida − 1) × (1 + N/100)
> ```
>
> O bônus incide sobre o **lucro**, não sobre o retorno.

**Medido no card com valor em R$ (31/08/2026):**

| campo do card | valor |
|---|---|
| Aposta | R$557,00 |
| Ganhos Potenciais | R$1.364,65 (= 557 × 2,45) |
| Criar Aposta Turbinada +50% | **+R$403,83** |
| retorno real | R$1.768,48 → odd **3,175** |

`403,83` é exatamente 50 % do lucro de `807,65`. Confirmado por outros dois
bilhetes, contra o que o próprio apostador registrou: `2,18 +25% → 2,475` (ele
anotou 2,47) e `2,60 +25% → 3,00` (anotou 3,00).

**Consequência prática:** planilhar a odd do card num bilhete turbinado
subestima toda vitória. É a mesma família do `SuperMúltipla` da Estrela Bet
(`CASA_ESTRELABET §Bônus`) — o selo é da marca, o mecanismo é o mesmo.

Isso **não** contradiz o `§11`: em `W` a regra continua sendo `Ganhos ÷ Aposta`,
e ela já resolve o boost sozinha quando o card traz os valores em R$. A fórmula
acima é para o caso em que o card mostra **só a odd e o `+N%`**, sem dinheiro —
que é como o bilhete aparece quando a stake está oculta.

Em `L` a odd não entra no P/L, então recalcular é indiferente.

---

## 7. Cashout

- Resolvido: rótulo `Cash out` + `Ganhos` = valor encerrado. Aberto: botão `CASH OUT R$X`.
- `Ganhos ≠ Aposta` → `Resultado = W`, `Odd = Ganhos ÷ Aposta` (global, §5.6).
- `Ganhos = Aposta` → `Resultado = V`, odd exibida/estrutural. (Ex.: `0367361033`, Argentina −1.5, aposta R$209, cash out R$209 → V, odd 2,02.)

---

## 8. Bônus

<!-- TODO: confirmar se a casa opera com bônus/freebets e qual a política de tratamento (excluir / marcar / incluir). Sem amostra ainda. -->

---

## 9. Mapa de mercados (Betano → `Aposta` global)

| Betano exibe | Aposta global |
|---|---|
| Vencedor | ML |
| Handicap / Handicap - Resultado Final / Handicap de Games (Set N) / Handicap de sets | Handicap |
| Handicap - Cartões | Cartões |
| Tiros de meta Handicap 2-Way | Team Props |
| Receber um cartão | Cartões |
| Total de Cartões / Asiático (Mais/Menos) Total de Cartões | Cartões |
| Total de escanteios / Escanteios Mais/Menos / 1.º Tempo Escanteios | Escanteios |
| Total de chutes | Chutes |
| Total de Games no Set (Set N) | Games |
| Total de Pontos e Rebotes / Arremessos de três pontos convertidos / Total de Rebotes e Assistências `[Jogador]` (NBA/EuroLeague) | Player Props |
| Chance Dupla / `X2` | Dupla Chance |
| Total de tiros de meta (goal kicks) | Team Props |
| Total de Faltas | Faltas |
| Tie Breaks | **Outros** ⚠️ (nicho tênis) |
| 1º Quarto - Total de pontos | **Outros** ⚠️ (total de período — avaliar Team Props) |
| Total de 180's / Mais de–Menos de N 180's (Over/Under de **um** jogador) | Player Props |
| Maioria de 180's / H2H 180's (comparativo: quem faz **mais** no confronto) | H2H |
| Criar Aposta / N-seleções / Dupla / Tripla | Múltipla |

Notas de reconstrução:
- **Jogador vem entre `[colchetes]` no fim do mercado:** `Total de Pontos e Rebotes [Victor Wembanyama]` → descrição `Victor Wembanyama - Under 39.5 Pontos+Rebotes [confronto]`.
- Confronto `A - B` → `[A v B]`.
- `Mais de` / `Menos de` → Over / Under.
- **Handicap de objeto estatístico:** a categoria segue o **objeto**, não o tipo de mercado (`MASTER_APOSTAS §1`). `Handicap - Cartões` → `Cartões`; `Tiros de meta Handicap` → `Team Props`. A linha de handicap (`+/-N`) vai só na **descrição**. Handicap sobre unidade de pontuação (gols/games/sets) continua `Handicap`.
- `Tripla` / `Dupla` / `N-seleções` / `Criar Aposta` → `Múltipla`, uma linha, seleções com ` // `.
- **Maioria de 180's / H2H 180's (Dardos):** comparativo de quem faz mais 180s → `H2H` (nunca `Legs`/`Player Props`). Layout com dois nomes sem `A v B` explícito: primeiro nome (topo) = apostado, segundo = adversário. Descrição: `Jogador - Maioria de 180's [Jogador A v Jogador B]` (espelha Bet365/Betfair · `MASTER_APOSTAS §6`).

---

## 10. Stake

- Header (`R$51,00`) ou `Aposta: R$300,00`. Formato pt-BR: `R$1.914,56` → `1914,56` (remover ponto de milhar, manter vírgula). Normalização = global.

---

## 11. Odds

`Ganhos` é a verdade financeira:

- `W` (`Ganhou`) → `Odd = Ganhos ÷ Aposta`

> ⚠️ **Para W: ignorar a odd exibida por seleção no bilhete** — pode não refletir boost/promoção. Usar SEMPRE `Ganhos ÷ Aposta` com precisão total; nunca a odd do texto da seleção.

- `L` (`Perdida`) → **odd exibida** (single) / **odd estrutural** (múltipla); nunca derivar do Ganhos (= 0)
- `V` / cashout = stake → odd exibida / estrutural
- Cashout ≠ stake → resultado `W`, `Odd = Cash out ÷ Aposta`

**Múltiplas:** a Betano **não mostra odd combinada** no texto resolvido — só as odds por seleção. Logo, em L/V a odd estrutural = **produto das odds das seleções** (`MASTER_RESULTADO_2026 §7`). Em W, `Ganhos ÷ Aposta`.

> ⚠️ Em L/V a odd é preservada (nunca 0,00 / 1,00). `Ganhos ÷ Aposta` só p/ W e cashout. Precisão: preservar (global).
> ⚠️ **Vírgula, nunca ponto:** o produto/divisão sai com ponto — converta para vírgula e preserve a precisão (`8,580978`, nunca `8.580978`, nunca arredondar p/ 2 casas). Ponto vira separador de milhar na planilha e corrompe a odd. Ver `MASTER_OUTPUT_2026 §12.1`.

---

## 12. Ruído a ignorar

`sport-icon` · `copy icon` · `Pontuação: X-Y` (placar) · `Ganhos Potenciais` (tela aberta = potencial, não real) · botões `Reapostar`/`Compartilhar`/`CASH OUT` · `Anulado se o jogador não iniciar` (condição, não resultado) · quando houver badge ou indicação de substituição: o nome tachado/riscado = jogador original (usar), o nome em destaque acima = substituto (ignorar).

**Seleção repetida em bilhetes simples:** no texto copiado de um bilhete simples, a seleção aparece **duas vezes** — uma como linha de resumo (antes de `sport-icon`) e outra como linha de detalhe com odd, mercado e confronto. São a **mesma seleção do mesmo bilhete**, nunca dois bilhetes distintos. Exemplo:
```
REKONIX -1.5          ← linha de resumo (ignorar, é repetição)
sport-icon
REKONIX -1.5          ← linha de detalhe (usar esta)
2.20
Handicap do Jogo
REKONIX - Grind Back
```
→ 1 bilhete, não 2.

---

## 13. Pegadinhas (resumo rápido)

- Data do resolvido é **colocação** (proxy do evento p/ mesmo-dia; off em jogo de outro dia) — ver §4.
- Múltipla sem odd combinada → **produto** das seleções.
- Jogador vem entre `[colchetes]` no fim do mercado.
- `Chance Dupla`/`X2` → **Dupla Chance** (mapeado em §9; nunca usar `Outros`).
- NBA / EuroLeague → **Basquete** (regra liga≠esporte).
- Números em pt-BR (`R$1.914,56`).
- Abertas têm data do jogo; resolvidas não.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

- Resultado traduzido (Ganhou→W, Perdida→L, Cash out=stake→V).
- Múltipla: odd estrutural = produto das seleções.
- Jogador extraído dos `[colchetes]`.
- 1 ID = 1 linha; Tripla/N-seleções/Criar Aposta colapsados em 1 linha.

---

## 15. Exemplos golden (bilhetes reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**#1 — W, Player Props NBA→Basquete (`20368123343`):**
```
10/06/2026	Basquete		Betano		Player Props	Victor Wembanyama - Under 39.5 Pontos+Rebotes [New York Knicks v San Antonio Spurs]	301,00	1,83	W
```

**#2 — W, Handicap de resultado (+0,5 gols), Futebol (`20366550663`):**
```
10/06/2026	Futebol		Betano		Handicap	Coréia do Sul +0.5 [Coréia do Sul v Tchéquia]	200,00	1,70	W
```

**#3 — W, ML E-Sports (`20362840043`):**
```
09/06/2026	E-Sports		Betano		ML	Rune Eaters [Rune Eaters v Nemiga]	992,00	1,93	W
```

**#4 — V, cashout = stake, Vôlei (`20367361033`):**
```
10/06/2026	Vôlei		Betano		Handicap	Argentina -1.5 [Sérvia v Argentina]	209,00	2,02	V
```

**#5 — L, Tripla multi-esporte, odd estrutural = produto (`20376457083`):**
```
12/06/2026	Múltiplos		Betano		Múltipla	EUA +2.5 [EUA v Paraguai] // Sporting CP -1.5 [SL Benfica v Sporting CP] // Wojciech Tobiasz [Wojciech Tobiasz v Mariusz Adamus]	51,00	11,2924	L
```

---

## Feedback para a camada global / MODELO

1. **Múltipla sem odd combinada exibida** → calcular odd estrutural por produto (já no `MASTER_RESULTADO §7`); reforça que a casa pode não dar a odd total.
2. **Mercados nicho sem categoria global:** ~~Faltas~~, Tie Breaks, total de período. Decidir o que vira categoria nova vs fica em `Outros`. (Dupla Chance → `Dupla Chance` e Tiros de meta → `Team Props` já foram resolvidos como categoria. **`Faltas` virou categoria própria na s272** — o volume real na `CASA_BETFAST` já era maior que o de `Gols`, e "nicho" tinha deixado de descrever o caso.)
3. **Esporte ausente no global:** apareceu polo aquático (CN Barceloneta v Ferencvaros) — hoje cai em `Outro`. Avaliar adicionar.
4. **Data colocação-como-proxy:** mais um padrão pra cadeia de data do `MASTER_OUTPUT §4` (evento → informada → extrato/join → colocação-proxy → Brasília).

---

VERSÃO: 2026
ATUALIZADO: 2026-09-01 (sessão 306) — §6 boost preenchido: `Criar Aposta Turbinada +N%` paga por fora da odd exibida
STATUS: QUASE COMPLETO (pendência: §5 rótulo void/anulada — aguarda amostra)
CASA: Betano
