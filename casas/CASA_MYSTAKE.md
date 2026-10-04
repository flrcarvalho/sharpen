# CASA_MYSTAKE
## Camada de tradução — MyStake → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da MyStake.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `MyStake` · site: `mystake.bet` (sportsbook em `/br/sportsbook/mybets`)
- Domínios registrados: `mystake.bet` (**provado logado**, s392), `mystake.com` e `mystake2.com` (mesma marca, atrás do mesmo desafio Cloudflare; **não** provados logados).
- **Fora do `.bet.br`**: a casa não é regulada no Brasil.
- Locale: pt-BR · Moeda: R$ (BRL) — `CurrencySTR: "BRL"` nos 9 de 9.
- **Decimal exibido na tela: PONTO** (`29.76`, `45.00`) → normalizar para vírgula.
- Motor: **BetConstruct** (sportsbook v4) — o mesmo da [`CASA_TIVO`](CASA_TIVO.md), [`CASA_BETFAST`](CASA_BETFAST.md) e [`CASA_FAZ1BET`](CASA_FAZ1BET.md).
- ⚠ **Não confundir com a `Stake`** ([`CASA_STAKE`](CASA_STAKE.md)): outra casa, outro motor (Kambi), 643 bilhetes na base. "my**stake**" contém "stake", mas host e nome são comparados **exatos** (`captura.casa_de_host`, `main._casa_registrada`) — nenhum casamento por substring.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

### 1.1 Quarta casa do mesmo motor — e a review pública estava errada ⭐

Fontes públicas (reviews da rede Santeda — Velobet, Rolletto, GoldenBet…) atribuíam o sportsbook da MyStake à **Upgaming**. O **F12 logado desmentiu** (s392, 03/10/2026):

| Prova | MyStake |
|---|---|
| pedido do histórico | `POST /api/game/p/messagetosport` · `{"name":"gethistory","message":"{\"countOnly\":false,\"language\":33,\"from\":\"\",\"to\":\"\"}"}` — idêntico às irmãs |
| quem dispara | `helpers.js?v=2.4.0` |
| resposta | `{Error, Tickets, Count}` com o **mesmo conjunto de chaves** das fixtures tivo/betfast/faz1bet |
| `Company` | **28** (Tivo 291 · Betfast 99 · Faz1bet 223) — o id da casa **dentro do motor** |

> **Vale o tráfego, não a review.** E o `Company` é o detalhe que importa para o futuro: nesta família, a própria resposta diz qual casa é, independente do domínio.

Consequência de engenharia: **mesmo `extensor/tv_inject.js`, mesmo `formatTicketTV`**. O harness roda a fixture pelos hosts da MyStake e da Tivo e compara os blocos byte a byte (`extensor/harness/casos/mystake.mjs`).

> **Ao mexer numa das quatro, confira as outras.** O que esta casa provou (`Result 6`, `TicketType 3`) vale para as irmãs.

---

## 2. Modo de ingestão e layout ⭐

### 2.1 Modo de ingestão

**Captura por API** (SharpenUp · `tv_inject.js`). Mesmo proxy genérico das irmãs (`CASA_FAZ1BET §2.1`).

1. **A mesma URL serve polling.** Na tela de apostas, `messagetosport` de **0,7 kB** dispara a cada ~5 s (saldo/notificação). Quem separa o histórico é a **forma da resposta** (`Tickets` em array) — o polling é ignorado em silêncio.
2. **Sem paginação.** `Count: 9` na amostra, longe do `TETO_ALERTA` de 50 (varredura retroativa não dispara — travado no harness).

> ⚠ `from`/`to` são epoch em **milissegundos** (armadilha do motor: em segundos, `Count: 0` com `Error: null`). Não foi re-medido nesta casa; vale a medição das irmãs.

### 2.2 Tipo do bilhete declarado

A coluna "Tipo" do card diz **`Expresso`** para múltipla. O nº de seleções vem de `Items.length`.

### 2.3 Layout do bilhete

Lista tabular: `Status · ID · Data · Tipo · Valor Apostado · Probabilidades · Quantia`, abas `Tudo · Ativa · Ganhas · Perdidas`. Clicar no bilhete abre o detalhe por perna (data, jogo, placar, mercado, `Escolher: <seleção> (<linha>)`, odd colorida pelo resultado da perna). Sem linha em branco entre bilhetes — nunca robô de texto.

---

## 2.5 Campos da API (o que o inject entrega)

Idênticos aos da `CASA_BETFAST §2.5`. O que **esta** amostra acrescentou:

| Campo (API) | Nesta casa |
|---|---|
| `TicketType` | **0** normal · **3 = FREEBET** (§8). O inject repassa cru como `tipoBilhete` (s392) |
| `Items[].Result` | 0 · 1 · 2 · 3 · **6 = meia derrota** (§5.2) |
| `Items[].FinalPosition.hisminus` | `true` em 4 pernas — **o sinal exibido é o oposto do `h`** (§12) |
| `Company` | 28 |
| `euba` / `eubs` | presentes em 6 dos 9 bilhetes, ausentes em 3 — internos, ignorados |

---

## 3. ID do bilhete

- Formato: **numérico, 9 dígitos** (ex.: `306558258`), exibido como `# 306558258`.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`).
- Espaço de IDs do motor (`306…`), na mesma faixa das irmãs; a dedup é por (casa, parceiro, código).

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da perna mais recente** (`MASTER_OUTPUT §4`).

- colocação — `ActionTime`: é a coluna "Data" do card (`2 Outubro 23:11`).
- evento — `Items[].Game.StartTime`: **usar a mais recente**.

> Na amostra, **9 de 9** foram colocados em 02/10 à noite para jogos de 03/10. Usar a colocação gravaria **todos** no dia errado.

---

## 5. Status e Resultado

De-para do bilhete — o mesmo das irmãs (`CASA_FAZ1BET §5`). Amostra: **9 `L`** (`Status 10 · Result 3`), "Quantia 0.00".

### 5.1 `Result` por perna

| `Items[].Result` | Leitura | Cor no card |
|---|---|---|
| 0 | pendente | — |
| 1 | anulada / devolvida (void) | **amarela** |
| 2 | ganhou | verde |
| 3 | perdeu | vermelha |
| **6** | **meia derrota** | **vermelha** (igual à derrota cheia) |

### 5.2 ⭐ `Result 6` = meia derrota — a tela não distingue, a API sim

Provado por duas pernas de handicap asiático **partido**, contra o placar:

| bilhete | jogo | placar | seleção | leitura |
|---|---|---|---|---|
| `306558636` | Macclesfield × Scarborough | 2:2 | fora −0,25 | metade perde (−0,5), metade devolve (0) |
| `306558758` | Dorking × Chatam | 1:0 | fora +0,75 | metade perde (+0,5), metade devolve (+1) |

E o controle: no mesmo `306558758`, Macclesfield **handicap 0** no 2:2 saiu `Result 1` (amarela) — a devolução inteira tem enum próprio.

O P/L vem do **bilhete** (múltipla perdida), então o `6` mexe só na descrição da perna. Numa **simples** com meia derrota, quem decide `HL` continua sendo o dinheiro (`retorno = stake/2`, `MASTER_RESULTADO`), nunca o enum.

---

## 6. Boost / promoção

Sem amostra. Nenhum `W`, nenhum `ItemType 6`.

---

## 7. Cashout

`CashOut: false` em 9 de 9. Vale a regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`).

---

## 8. Bônus e FREEBET ⭐

**`TicketType: 3` = aposta feita INTEIRA com freebet.** Bilhete `306558902` (R$ 45,00, badge **"F" vermelho** ao lado do valor no card), confirmado pelo dono. `IsBonus` continua `false` nele — **não** é esse o campo. Também `RiskBonusMaxWin: null` só nele.

Controle: o `306558885` tem **as mesmas três pernas e o mesmo `Koef` 29,7667**, com `TicketType 0` — e sai **sem** a marca.

O bloco capturado emite:

```
Freebet incluído: 45,00 (dinheiro real = stake − freebet)
```

— o **mesmo rótulo** que a Superbet já emite para freebet parcial. O `Stake:` continua **cheio** (R$ 45,00): quem desconta é a regra, nunca a IA.

> **Decisão do Feca (03/10/2026, todas as casas):** freebet é dinheiro da casa — perda = 0, ganho = lucro sem o stake (a casa paga só o lucro). **A regra global ainda não está implementada** (P/L, Caixa, turnover): está no `BACKLOG.md`. Até lá esta linha é só marca, e o bilhete conta como perda cheia.

Sem amostra de **freebet ganha**: o `WinAmount` nesse caso não foi conferido campo a campo.

---

## 9. Mapa de mercados (MyStake → `Aposta` global)

Só os mercados **confirmados no dado real desta casa** (27 pernas, 17 rótulos):

| MyStake exibe | Aposta global |
|---|---|
| `Handicap` (futebol, asiático) · `{p1_r} quarto - Handicap` | Handicap |
| `Time de casa total de escanteios` · `Time de Fora total de escanteios` · `2ª metade - Time de casa total de escanteios` | Escanteios |
| `Time de fora total de cartões` · `2ª metade - Total de cartões do time de fora` · `1ª metade - Time de casa total de cartões` | Cartões |
| `Mais cartões` | H2H |
| `Dupla Chance` | Dupla Chance |
| `1ª metade - Total de pontos` · `1ª metade - Time de fora total de pontos` · `{p1_r} quarto - Time de casa total de pontos` · `{p1_r} set - Total de pontos` | Pontos |
| `{p1_r} quarto - Resultado` (Futebol Americano) | ML |
| `1º mapa - Total de mortes` (League of Legends) | E-Sports Props |
| `2nd map - Hometeam total rounds` (Counter-Strike) | E-Sports Props |

**Notas de decisão:**

- **`Mais cartões` → `H2H`**: quem faz **mais** no confronto (precedente `CASA_BETFAST §9`).
- **`{p1_r} quarto - Resultado` → `ML`**: o recorte de tempo não muda a categoria (`MASTER_APOSTAS §1`); é o vencedor (do quarto).
- **`mortes` → `E-Sports Props`**: sinônimo de kills/abates (precedente `CASA_BETFAST §9`, `1º Mapa - Total de Abates`).
- **`total rounds` de CS → `E-Sports Props`, não `Rounds`**: `Rounds` é a categoria de luta (MMA, Boxe); em e-sport, estatística vai para `E-Sports Props`.
- ⚠ **Rótulo em INGLÊS** (`2nd map - Hometeam total rounds`) mesmo com `language: 33`: o dicionário do tenant não traduz tudo.
- Recorte desta casa: **`1ª/2ª metade`** (feminino), diferente do `1º/2º metade` da Faz1bet e do `Tempo` da Betfast — espelho compartilha código, não dicionário.

---

## 10. Stake

- Origem: `Amount` (= `SystemBet`), unidade normal. Em freebet, `Amount` é o valor da freebet (§8).
- ⚠ **Não** usar `CalculatedBetAmount` (rateio por perna).

---

## 11. Odds

- Origem: `Koef`, **precisão completa**. **A tela trunca** em 2 casas: `39,1813 → 39.18`, `12,288 → 12.28`, `14,6475 → 14.64`, `29,7667 → 29.76`. Nunca ler a odd do card.

---

## 12. Ruído a ignorar

Mesmo conjunto das irmãs (`CASA_BETFAST §12`): placeholder `{p1_r}` (resolver com `FinalPosition.p1`), `Team1Score`/`Team2Score` (estatística, não placar), `CalculatedBetAmount`, `Price`, `Company`, `Player.*`.

⚠ **`hisminus: true` inverte o sinal da linha.** A tela mostra `Escolher: 2 (0.75)` para `h: -0.75, hisminus: true`, e `Escolher: 1 (-0.75)` para `h: -0.75, hisminus: false`. Desde a 0.7.40 o formatador emite a linha **com o sinal da tela** (`(linha 0,75)` no Dorking), travado no harness com o controle `hisminus:false`. Além da tela, o resultado da casa prova a leitura em três pernas que a linha crua não explica (meia derrota em −0,25 no 2:2; meia derrota em +0,75 perdendo por 1; vitória da BetFast em +3,5 com 7×8 faltas). Não afeta P/L. **Linha gravada antes da 0.7.40 continua com o sinal trocado** (o UPSERT congela `descricao`): `BACKLOG 4.0b`.

---

## 13. Pegadinhas (resumo rápido)

- Fontes públicas dizem Upgaming; o tráfego diz **BetConstruct**.
- **"F" vermelho = freebet = `TicketType 3`**, e `IsBonus` continua `false`.
- **`Result 6` = meia derrota**, pintada de vermelho como derrota cheia.
- `hisminus: true` → sinal da linha invertido na tela (§12).
- Odd: a tela trunca → sempre `Koef`.
- Data: todos os 9 mudam de dia entre colocação e evento.
- `messagetosport` de 0,7 kB a cada ~5 s é polling, não histórico.
- **MyStake ≠ Stake.**

---

## 14. Validações específicas

> **Transversais:** `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`.

- Coluna Data = evento mais recente.
- Odd com precisão completa, decimal com vírgula.
- `Freebet incluído:` só em `TicketType 3` — travado no harness, com controle negativo.

---

## 15. Exemplos golden (bilhetes reais)

<!-- TODO: a casa entrou na s392 e a captura ponta a ponta pela extensão ainda NÃO rodou ao vivo.
     A regressão da captura (9 bilhetes reais, 27 conferências: data do evento, odd completa,
     freebet com controle negativo, meia derrota, espelho pelo host da Tivo) está travada em
     `extensor/harness/casos/mystake.mjs`. Preencher com o primeiro lote conferido. -->

---

## Feedback para a camada global / MODELO

1. **Regra global de freebet** — decidida pelo Feca em 03/10/2026, não implementada (`BACKLOG.md`).
2. **`hisminus`** inverte o sinal em toda a família BetConstruct (§12) — corrigido na captura (0.7.40); o histórico gravado antes segue no `BACKLOG 4.0b`.
3. **`Company` identifica a casa dentro do motor** — é o sinal que um detector automático de casa espelho usaria.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA (4ª casa do motor BetConstruct) · **captura ponta a ponta pela extensão ainda não rodada** · golden a preencher (§15) · sem amostra de aberta, W, simples, sistema, cashout, `ItemType 6` e freebet ganha
CASA: MyStake
