# CASA_BETFAIR
## Camada de tradução — Betfair (Sportsbook) → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betfair **Sportsbook** (odds fixas — NÃO a Exchange).
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betfair`
- Produto: **Sportsbook** (`myactivity.betfair.bet.br/sportsbook`). A Exchange (back/lay) não está em uso — sem liability nem comissão.
- Locale: pt-BR, mas **números no bilhete vêm em formato en-US** (`R$1,050.00` = mil e cinquenta) → normalizar (ver §10).
- `Parceiro` = `Duka [Eu]` (preenchido pela app via workspace; extrator deixa vazio). `Tipster`: vazio.

---

## 2. Modo de ingestão e layout (DUAS fontes + join)

A Betfair precisa de **duas fontes casadas pelo ID** `O/25146258/XXXX`:

**Fonte A — bilhetes** ("Minhas apostas → Resolvida", print ou texto colado). Tem: tipo, código visual (`V`/`P`/`N`), confronto, mercado, seleção, odd, `Valor Apostado`, `Ganhos`, `ID da aposta`. **Não tem data.**

**Fonte B — extrato** ("Transações", export CSV `AccountStatement`, estruturado). Colunas: `Data · Descrição · Entrada de Dinheiro · Entrada de bônus · Saída de Dinheiro · Saída de bônus · Saldos`. Linhas relevantes:
- `Sportsbook: Bet Settled (Bet Ref: O/…XXXX)` → liquidação com retorno (ganho/cashout) + **data**.
- `Sportsbook: Voided Bet Refund (Bet Ref: O/…XXXX)` → void + **data**.
- `Sportsbook: Bet Placed (Transaction ID: S/…)` → colocação. **ID diferente (`S/`), não casa com o bilhete** → ignorar pro join.
- `Sports Bonus Awarded` → crédito de bônus.

**Join:** `ID da aposta` (A) = `Bet Ref O/…` (B). O extrato é estruturado/exportável (como a Pinnacle) → data e bônus saem dele de forma determinística.

**Ordenação de output — REGRA ABSOLUTA (Fonte A manda):**
A ordem do TSV segue **exclusivamente a Fonte A** (prints/imagens/texto dos bilhetes).
O extrato (Fonte B / CSV) é usado **apenas para buscar data e dados financeiros** via join — **nunca para reordenar**.

| Posição na Fonte A | Posição no TSV |
|---|---|
| 1ª aposta (topo do print / início do texto) | **última linha** (mais recente) |
| Última aposta (fim do print / fim do texto) | **1ª linha** (mais antiga) |

> Regra mnemônica: inverter a Fonte A → gerar TSV. Nunca ordenar por data do extrato.

---

## 3. ID do bilhete

- Formato: `O/25146258/XXXX` (sequencial por bilhete). É a **chave do join** (com o extrato) e do **dedup**.
- Nunca vai no output.
- O `Transaction ID: S/…` das colocações é outro id — não usar pro join.

---

## 4. Data (via join com o extrato)

Regra global: data = **data do resultado**. Na Betfair ela vem do **extrato**, não do bilhete:

- **Ganho / Cashout** → data da linha `Bet Settled (Bet Ref: O/…)` casada por ID.
- **Void** → data da linha `Voided Bet Refund (Bet Ref: O/…)`.
- **Perda** → ⚠️ **não gera linha no extrato** (perda não devolve dinheiro). Datar por **interpolação**: a lista "Resolvida" está em ordem de ID (cronológica); a perda herda a data dos bilhetes datados que a cercam. Ambíguo só na virada de dia → marcar pra revisar.

Formato fonte: `DD-mmm-YY HH:MM:SS` (ex.: `12-jun-26 20:47:03`) → `DD/MM/AAAA`. Nunca usar data de colocação (`Bet Placed`).

---

## 5. Status e Resultado  ⚠️ (COLISÃO DE CÓDIGO — a maior pegadinha)

A Betfair usa um código visual de uma letra que **colide** com o nosso:

| Betfair (visual) | Significado Betfair | **Nosso código** |
|---|---|---|
| `V` (verde, "Você ganhou") | **Vitória** | **W** |
| `P` (vermelho) | Perdida | **L** |
| `N` | Nulo / Anulado | **V** |

> ⚠️ NUNCA copiar o código visual direto. O `V` da Betfair é **vitória → W**; o nosso `V` (void) é o `N` da Betfair.

Conferência financeira (decide em caso de dúvida): `Ganhos = 0` → L · `Ganhos = Valor Apostado` → V · `Ganhos > Valor Apostado` → W. Aba "Aberta" → `extraction_state = aberta`.

---

## 6. Boost / promoção

**A Betfair Sportsbook não tem boost/promoção de odds.** Por isso a odd exibida é autoritativa para W — não há boost a capturar. *(É o oposto da Superbet, onde o boost obriga a usar Retorno÷Stake.)*

---

## 7. Cashout

- Localizador: campo `Total de Cash Out: R$X` (+ ícone de cash out nas seleções).
- Encerrado com valor diferente do apostado → `Resultado = W`, `Odd = Cash Out ÷ Valor Apostado` (global, §5.6).
- `Cash Out = Valor Apostado` → `Resultado = V`, odd exibida/estrutural. (Ex.: Dupla `0001532`, apostado R$300, cash out R$300 → V; odd estrutural `2,87 × 2,30`.)

---

## 8. Bônus

**Decisão:** apostas com bônus são **incluídas** no fluxo normal.

- Stake registrado = valor do bônus usado (campo `Bônus usado:` / `Total Apostado:`).
- Localizadores de bilhete com bônus: `Bônus usado:` · `Total Apostado:` · texto "Retorno com bônus. Ver detalhes".
- O extrato identifica o bônus pelas colunas `Entrada de bônus` / `Saída de bônus` — útil para filtros futuros no dashboard.
- ⚠️ O valor de bônus superestima o volume de capital próprio em risco; interpretar com cautela em análises de P&L.

---

## 9. Mapa de mercados (Betfair → `Aposta` global)

| Betfair exibe | Aposta global |
|---|---|
| Resultado da partida | ML |
| Handicap / Handicap no escanteio / Handicap nos pontos da partida | Handicap |
| Marcador a qualquer momento | Anytime |
| Marca X+ Pontos / Anota X+ rebotes / Registra X+ Assistências (NBA/WNBA) | Player Props |
| Escanteios do time da casa / "N ou mais escanteios" | Escanteios |
| Total de cartões do time da casa | Cartões |
| Total de Inibidores/Torres/objetivos no Mapa N (E-Sports) | E-Sports Props |
| Maioria de 180's (Dardos) | H2H |
| Criar Aposta / Múltiplas do Criar Aposta | Múltipla |

Notas de reconstrução:
- **CORREÇÃO do esboço antigo:** "Registra X+ Assistências" em basquete (NBA/WNBA) é **Player Props**, **NÃO** `Assistência`. A categoria `Assistência` é exclusiva de Futebol (`MASTER_APOSTAS_2026`).
- Confronto Betfair vem como `Time A x Time B` **ou** `Time A @ Time B` → `[Time A v Time B]`.
- `Criar Aposta (xN)` = mesmo jogo; `Múltiplas do Criar Aposta` = vários jogos. Ambos → `Múltipla`, **uma linha**, juntando seleções com ` // `. Mesmo jogador, vários mercados → `Jogador - Mercado A / Mercado B [Confronto]`.
- "Maioria de 180's": comparativo de quem faz mais 180s → `H2H` (mercado comparativo entre duas entidades, conforme `MASTER_APOSTAS_2026`). Layout: dois nomes de jogadores exibidos sem `A v B` explícito; primeiro nome = apostado, segundo = adversário. Confronto: `[apostado v adversário]`. Descrição: `Jogador - Mais 180's [Jogador A v Jogador B]`.
- "Substituição Segura" / ícone de cash out = feature, ruído pra categoria.

---

## 10. Stake

- Campo `Valor Apostado:` (ou `Total Apostado:` quando bônus).
- **Formato en-US:** `R$1,050.00` → `1050,00` · `R$300.00` → `300,00`. Remover a vírgula de milhar e trocar ponto decimal por vírgula. (Cuidado: aqui a vírgula é milhar, não decimal.)
- **`Mais de X` / `Menos de X` / `N ou mais X` → `Over X` / `Under X`**: padrão global — ver `MASTER_DESCRICAO_2026 §11`. A Betfair exibe em português; a saída TSV é sempre em inglês.

---

## 11. Odds

`Ganhos` é a verdade financeira (como o `Retorno Obtido` da Bet365):

- `W` (visual `V`) → `Odd = Ganhos ÷ Valor Apostado`
- `L` (visual `P`) → `Ganhos = 0` → **odd exibida** no bilhete (nunca derivar do Ganhos — daria 0,00)
- `V` (visual `N`) → `Ganhos = Valor Apostado` → odd exibida / estrutural
- Cashout → `Cash Out ÷ Valor Apostado` (ver §7)
- Múltipla / Criar Aposta → a odd estrutural é o campo `Cotações combinadas`. Em W, `Ganhos ÷ Valor Apostado`.

> ⚠️ Em L/V a odd é preservada (nunca 0,00 / 1,00). `Ganhos ÷ Stake` vale só p/ W e cashout. Precisão: preservar (global).

---

## 12. Ruído a ignorar

Ícone de cash out · `Substituição Segura` (produto de seguro — não é substituição de jogador durante o jogo; ruído para categoria) · `Adicionar seleções restantes ao cupom` · `Retorno com bônus. Ver detalhes` · no extrato: linhas `Bet Placed` (só `Bet Settled`/`Voided Bet Refund` importam pro join) e o `Transaction ID: S/…` · se a Betfair exibir substituição durante o jogo com nome tachado: aplicar regra global — nome tachado = jogador original (usar), nome em destaque = substituto (ignorar).

---

## 13. Pegadinhas (resumo rápido)

- **Código visual `V` = Vitória → W; `N` = Nulo → V.** Nunca copiar direto.
- Data só via **join com o extrato** pelo ID `O/`; perdas por interpolação.
- Bônus incluído com stake do bônus como valor (ver §8).
- Assistências de basquete = **Player Props**, não Assistência.
- Números em en-US (`R$1,050.00`).
- Cashout em `Total de Cash Out`.
- ML/H2H com nomes de jogador (dardos) cai na desambiguação Dardos×Tênis do global — confiar nas listas de participantes.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

- Código traduzido (nunca o `V`/`P`/`N` visual cru no output).
- Toda data veio do extrato (retorno/void) ou de interpolação (perda) — nunca de colocação.
- Stake normalizada de en-US.
- 1 `O/` ref = 1 linha; `Criar Aposta`/`Múltiplas do Criar Aposta` colapsados em 1 linha.

---

## 15. Exemplos golden (bilhetes + extrato reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`
(Parceiro deixado vazio na extração; a app preenche `Duka [Eu]`.)

**#1 — W (visual `V`), ML Dardos (`0001517`, data do extrato 11-jun):**
```
11/06/2026	Dardos		Betfair		ML	Danny Ayres [Radek Szaganski v Danny Ayres]	400,00	1,9091	W
```

**#2 — W, Handicap no escanteio, Futebol (`0001525`, extrato 12-jun):**
```
12/06/2026	Futebol		Betfair		Handicap	Canadá -2.0 [Canadá v Bósnia]	301,00	2,30	W
```

**#3 — V (visual `N`), E-Sports Props, void via "Voided Bet Refund" (`0001512`, extrato 07-jun):**
```
07/06/2026	E-Sports		Betfair		E-Sports Props	Under 1.5 Inibidores [Cloud9 v Lyon]	303,00	1,83	V
```

**#4 — L, Criar Aposta WNBA→Basquete, Player Props (`0001503`, data por interpolação):**
```
12/06/2026	Basquete		Betfair		Múltipla	Megan Gustafson - 15+ Pontos / 8+ Rebotes [Portland Fire v Golden State Valkyries]	60,00	39,37	L
```

---

## Feedback para a camada global / MODELO

1. **Ingestão por join multi-fonte:** o MODELO precisa prever casas cujo dado vem de **duas fontes casadas por ID** (detalhe + extrato financeiro). Generaliza o "modo de ingestão".
2. **Datação por extrato/posição:** quando a data não está no detalhe, fonte = extrato (por ID) com fallback de interpolação por ordem da lista. Engrossa a cadeia de data do `MASTER_OUTPUT_2026 §4`.
3. **Bônus — DECIDIDO:** incluir com stake do bônus. O extrato separa as colunas de bônus, permitindo filtro posterior.
4. **Colisão de código:** reforça por que o §5 de cada casa é tradução, não cópia (o `V` da Betfair seria catastrófico se copiado).

---

VERSÃO: 2026
STATUS: QUASE COMPLETO
CASA: Betfair
