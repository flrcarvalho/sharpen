# CASA_GOLDENBET
## Camada de tradução — GoldenBet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da GoldenBet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> Espelho da [`CASA_MYSTAKE`](CASA_MYSTAKE.md): mesmo motor, mesmo inject, mesmo formatador.
> Aqui fica só o que a GoldenBet **mediu diferente** (s436, 30/10/2026, conta logada). O que
> não está escrito abaixo vale como na MyStake.

---

## 1. Identidade

- Casa canônica: `GoldenBet` · site: `goldenbet.com`. Marca na tela: "Goldenbet".
- Sportsbook em **`/eng/sportsbook/prematch`** (o `/br/sportsbook` da MyStake dá **404** aqui). "My Bets" é um painel do cupom, sem rota própria.
- Domínio registrado: `goldenbet.com`.
- Grafia **medida na base** antes do registro: nenhuma variante de GoldenBet em base nenhuma (`tools/audit_grafias.py`, s436).
- **Fora do `.bet.br`**: a casa não é regulada no Brasil. Rede Santeda (a mesma da MyStake).
- **Moeda: USD** — `CurrencySTR: "USD"` nos 15 de 15, saldo e cards em "USD" (§10).
- Motor: **BetConstruct** (sportsbook v4) — o mesmo da [`CASA_MYSTAKE`](CASA_MYSTAKE.md), [`CASA_TIVO`](CASA_TIVO.md), [`CASA_BETFAST`](CASA_BETFAST.md), [`CASA_FAZ1BET`](CASA_FAZ1BET.md) e [`CASA_JACK`](CASA_JACK.md).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

### 1.1 Sexta casa do mesmo motor — provado LOGADO

| Prova (conta logada, Chrome, 30/10/2026) | GoldenBet |
|---|---|
| pedido do histórico | `POST goldenbet.com/api/game/p/messagetosport` · `{"name":"gethistory","message":"{\"countOnly\":false,\"language\":0,\"from\":\"\",\"to\":null}"}` |
| quem dispara | `scripts/common/helpers.js` |
| resposta | `{Error, Tickets, Count}`, as chaves das irmãs |
| `Company` | **73** (MyStake 28 · Tivo 291 · Betfast 99 · Faz1bet 223) |

Consequência de engenharia: **mesmo `extensor/tv_inject.js`, mesmo `formatTicketTV`**. O harness roda a fixture pelos hosts da GoldenBet e da MyStake e compara os blocos byte a byte (`extensor/harness/casos/goldenbet.mjs`).

> **Ao mexer numa das seis, confira as outras.**

---

## 2. Modo de ingestão e layout ⭐

### 2.1 Modo de ingestão

**Captura por API** (SharpenUp · `tv_inject.js`), igual à MyStake (`CASA_MYSTAKE §2.1`): o histórico vem inteiro, com `Count`, sem paginação. `Count: 15` na amostra.

- `from`/`to` em **milissegundos**. Em segundos: `Count: 0` com `Error: null` (re-medido aqui).
- A aba "Lost" do painel manda o mesmo pedido com `"result":3`. O inject não copia o filtro: pede tudo.

### 2.2 Idioma ⚠

O pedido carrega o **idioma da página** (`language`), e o inject o repassa. A conta medida navega em **ENG** (`language: 0`): esporte, região e mercado chegam **em inglês** ("Point handicap", "International", "Hometeam total cards"). Com `language: 33` a mesma conta devolve português ("Handicap de pontos"). O texto lido pela IA segue o que o operador escolheu no site; o §9 cobre o inglês.

### 2.3 Layout do bilhete

Painel "My Bets": `ID · Date · Amount · Possible Win · Win Amount · Type · Cashout · Status`, filtros `All · Active · Won · Lost` e faixa `From/To`. `Type` diz **`Express`** para múltipla e **`Single`** para simples. Clicar abre o detalhe por perna (`# · Date · Match · Result · Odd · Status`, `Pick: <seleção> (<linha>)`, rodapé `Bet · Type · Total Odds`). Sem linha em branco entre bilhetes — nunca robô de texto.

---

## 2.5 Campos da API (o que o inject entrega)

Idênticos aos da `CASA_MYSTAKE §2.5`. O que **esta** amostra acrescentou:

| Campo (API) | Nesta casa |
|---|---|
| `CurrencySTR` | **`USD`** (as irmãs medidas são `BRL`) |
| `Company` | 73 |
| `ActionTime` | epoch ms UTC; o card mostra em horário de Brasília (`16:52:06` = `19:52:06Z`) |
| `PossibleWin` | 3 casas (`355.815`); o card arredonda ao centavo |

---

## 3. ID do bilhete

- Formato: **numérico, 9 dígitos** (ex.: `309877580`), igual ao card.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`). A dedup é por (casa, parceiro, código).

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da perna mais recente** (`MASTER_OUTPUT §4`): `Items[].Game.StartTime`, a mais recente; nunca o `ActionTime` (colocação, a coluna "Date" do card).

---

## 5. Status e Resultado

De-para do bilhete — o mesmo das irmãs (`CASA_FAZ1BET §5`, `CASA_MYSTAKE §5`). Amostra:

| `Status` · `Result` | Card | Leitura | Na amostra |
|---|---|---|---|
| 5 · 0 | `Current` (botão Cashout) | aberta | 7 |
| 10 · 3 | `LOST` | `L` | 8 |

Perna: `Result` 0 pendente · 2 ganhou · 3 perdeu (vistos aqui); 1 e 6 como na MyStake. **Sem ganha (W) na amostra.**

---

## 6. Boost / promoção

Herdado da `CASA_MYSTAKE §6` (`RiskBonusPercent`). Na amostra o campo é `0` nos 15.

---

## 7. Cashout

O card oferece Cashout nas abertas. Vale a regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`). Sem bilhete com cashout feito.

---

## 8. Bônus e FREEBET

A conta recebeu **freebet de 6 USD** em 30/10/2026 (aviso na tela), ainda não usada: nenhum `TicketType 3` na amostra. Leitura esperada = `CASA_MYSTAKE §8`.

---

## 9. Mapa de mercados (GoldenBet → `Aposta` global)

Com o site em inglês, os nomes chegam em inglês. Leitura para a IA:

- ⚠ **`Football` = FUTEBOL** (soccer). Futebol americano vem como **`American Football`**. Nunca traduzir `Football` como futebol americano.
- `Total` / `Total corners` / `Total cards` / `Total shots` / `Hometeam …` / `Awayteam …` + `Over`/`Under` = Acima/Abaixo da linha.
- `Corner handicap` / `Cards handicap` / `Point handicap` + `1`/`2` = handicap do time 1/2 na linha.
- `1st half` / `2nd half` / `{p1_r} quarter` / `1st map` = recorte do período (o `{p1_r}` é preenchido pelo `FinalPosition.p1`, como nas irmãs).

O resto segue o `CASA_MYSTAKE §9` (espelho compartilha código, **não** dicionário).

---

## 10. Stake e moeda ⭐

- Origem: `Amount`, **em dólar**. O bloco diz `Stake: 30,00 USD` + `Moeda: USD` + `Carimbo de colocação: <AAAAMMDDhhmmss>` (s436). Nas irmãs em real nada disso muda: `Stake: R$ …`, sem `Moeda` nem carimbo.
- A conta da GoldenBet tem de ser cadastrada **em USD** no Sharpen. A conversão é do servidor (`cambio`), pelo dia do carimbo.
- ⚠ **Não** usar `CalculatedBetAmount` (rateio por perna).

---

## 11. Odds

- Origem: `Koef`, **precisão completa** (na ganha, `WinKoef`). O card não mostra a odd na lista; o detalhe mostra "Total Odds" arredondado.

---

## 12. Ruído a ignorar

Mesmo conjunto das irmãs (`CASA_MYSTAKE §12`): `Team1Score`/`Team2Score`, `CalculatedBetAmount`, `Price`, `Company`, `Player.*`. ⚠ `hisminus: true` inverte o sinal da linha.

---

## 13. Pegadinhas (resumo rápido)

- **Conta em USD** — nunca ler o stake como real.
- **Nomes em inglês** quando o site está em ENG; `Football` é futebol.
- `/br/sportsbook` dá 404: a casa mora em `/eng/sportsbook`.
- Odd: a tela arredonda → sempre `Koef`.

---

## 14. Validações específicas

> **Transversais:** `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`.

- Coluna Data = evento mais recente.
- Odd com precisão completa, decimal com vírgula.
- Moeda do bilhete = `USD`; stake nunca rotulada `R$`.

---

## 15. Exemplos golden (bilhetes reais)

Conferidos no card em 30/10/2026; a regressão é `extensor/harness/casos/goldenbet.mjs` (15 bilhetes).

| Código | Colocação (card) | Evento (Data do TSV) | Stake | Odd | Tipo | Resultado |
|---|---|---|---|---|---|---|
| `309877580` | 29/10/2026 23:48:31 | 30/10/2026 | 75,00 USD | 1,95 | Simples — badminton, Point handicap `1 (11.5)` | L |
| `309985237` | 30/10/2026 16:52:06 | 31/10/2026 | 30,00 USD | 16,5182 | Múltipla (3) | aberta (potencial 495,55 USD) |
| `309981356` | 30/10/2026 16:32:38 | 30/10/2026 | 30,00 USD | 17,1 | Múltipla (3) | L |

---

## 16. O que falta medir

1. **Uma ganha (W)** em dólar: `WinAmount`, `WinKoef` e a odd do bloco.
2. **A freebet** de 6 USD usada: `TicketType 3` e o `WinAmount` da freebet ganha.
3. **A 1ª captura ponta a ponta** pelo botão Conectar, com a conta em USD no Sharpen.
4. Os termos em inglês na semente do dicionário da Ficha.

---

VERSÃO: 2026
STATUS: REGISTRADA E PROVADA LOGADA (6ª casa do motor BetConstruct, espelho da MyStake, conta em USD) · harness com 15 bilhetes reais · **captura ponta a ponta não rodada**
CASA: GoldenBet
