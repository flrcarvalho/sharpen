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

<!-- TODO: a Betano tem boost? Como sinaliza? Sem amostra nos bilhetes enviados. -->

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
| Handicap / Handicap - Resultado Final / Handicap de Games (Set N) / Handicap - Cartões / Handicap de sets / Tiros de meta Handicap 2-Way | Handicap |
| Receber um cartão | Cartões |
| Total de Cartões / Asiático (Mais/Menos) Total de Cartões | Cartões |
| Total de escanteios / Escanteios Mais/Menos / 1.º Tempo Escanteios | Escanteios |
| Total de chutes | Chutes |
| Total de Games no Set (Set N) | Games |
| Total de Pontos e Rebotes / Arremessos de três pontos convertidos / Total de Rebotes e Assistências `[Jogador]` (NBA/EuroLeague) | Player Props |
| Chance Dupla / `X2` | Dupla Chance |
| Total de tiros de meta (goal kicks) | **Outras** ⚠️ (nicho) |
| Total de Faltas | **Outras** ⚠️ (nicho) |
| Tie Breaks | **Outras** ⚠️ (nicho tênis) |
| 1º Quarto - Total de pontos | **Outras** ⚠️ (total de período — avaliar Team Props) |
| Total de 180s / Mais/Menos 180s / H2H 180s (Dardos) | **Legs** |
| Criar Aposta / N-seleções / Dupla / Tripla | Múltipla |

Notas de reconstrução:
- **Jogador vem entre `[colchetes]` no fim do mercado:** `Total de Pontos e Rebotes [Victor Wembanyama]` → descrição `Victor Wembanyama - Under 39.5 Pontos+Rebotes [confronto]`.
- Confronto `A - B` → `[A v B]`.
- `Mais de` / `Menos de` → Over / Under.
- `Tripla` / `Dupla` / `N-seleções` / `Criar Aposta` → `Múltipla`, uma linha, seleções com ` // `.

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
- `Chance Dupla`/`X2` → **Dupla Chance** (mapeado em §9; nunca usar `Outras`).
- NBA / EuroLeague → **Basquete** (regra liga≠esporte).
- Números em pt-BR (`R$1.914,56`).
- Abertas têm data do jogo; resolvidas não.

---

## 14. Validações específicas

- Resultado traduzido (Ganhou→W, Perdida→L, Cash out=stake→V).
- Múltipla: odd estrutural = produto das seleções.
- Jogador extraído dos `[colchetes]`.
- Liga não usada como Esporte.
- 1 ID = 1 linha; Tripla/N-seleções/Criar Aposta colapsados em 1 linha.

---

## 15. Exemplos golden (bilhetes reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**#1 — W, Player Props NBA→Basquete (`20368123343`):**
```
10/06/2026	Basquete		Betano		Player Props	Victor Wembanyama - Under 39.5 Pontos+Rebotes [New York Knicks v San Antonio Spurs]	301,00	1,83	W
```

**#2 — W, Handicap em cartões, Futebol (`20366550663`):**
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
2. **Mercados nicho sem categoria global:** Dupla Chance (recorrente — Superbet + Betano), Tiros de meta, Faltas, Tie Breaks, total de período. Decidir o que vira categoria nova vs fica em `Outras`.
3. **Esporte ausente no global:** apareceu polo aquático (CN Barceloneta v Ferencvaros) — hoje cai em `Outro`. Avaliar adicionar.
4. **Data colocação-como-proxy:** mais um padrão pra cadeia de data do `MASTER_OUTPUT §4` (evento → informada → extrato/join → colocação-proxy → Brasília).

---

VERSÃO: 2026
ATUALIZADO: 2026-06-20 (sessão 29) — §12 seleção dupla = 1 bilhete · §9 180s → Legs
STATUS: QUASE COMPLETO (pendências: §5 rótulo void/anulada, §6 boost — aguardam amostra)
CASA: Betano
