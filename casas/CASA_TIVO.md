# CASA_TIVO
## Camada de tradução — Tivo → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Tivo.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Tivo` · site: `tivo.bet.br`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `CurrencySTR: "BRL"`
- **Decimal exibido na tela: PONTO** (`354.13`, `51.00`) → normalizar para vírgula.
- Motor: **BetConstruct** (sportsbook v4), servido num **iframe de mesma origem** dentro do site.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API** (SharpenUp · `extensor/tv_inject.js`). O histórico não tem endpoint próprio: sai de um proxy genérico do site, que encaminha mensagens ao motor da casa.

```
POST https://tivo.bet.br/api/game/p/messagetosport
{"name":"gethistory","message":"{\"countOnly\":false,\"language\":33,\"from\":…,\"to\":…}"}
→ {"Error":null,"Tickets":[…],"Count":24}
```

Duas consequências que mandam no desenho:

1. **A mesma URL serve dezenas de mensagens** (saldo, notificações, tradução). Quem separa o histórico é a **forma da resposta**: só vale o que vier com `Tickets` em array.
2. **Não há paginação.** Uma chamada devolve a conta inteira e a casa carimba `Count` — provado: `from` de 2020 devolve exatamente os mesmos bilhetes que `from` vazio. O **fim autoritativo** é `Error:null` + `Tickets.length === Count`.

Filtro de aba (`result` na mensagem): omitido = tudo · `0` aberta · `2` ganha · `3` perdida. O robô **não** usa o filtro: pede tudo de uma vez.

> ⚠ **`from`/`to` são epoch em MILISSEGUNDOS.** Em segundos a API devolve `Count: 0` com `Error: null` — some tudo sem erro nenhum.

### 2.2 Tipo do bilhete declarado

A coluna "Tipo" do card diz `Simples` / `Múltipla`. O nº de seleções vem de `Items.length`.
Quando **todas** as pernas são do mesmo evento, o bloco capturado acrescenta a linha `Mesmo jogo: …` — sinal para a IA classificar Múltipla × Bet Builder pelo `MASTER_ESPORTES`, sem que o rótulo da casa decida sozinho.

### 2.3 Layout do bilhete

Lista tabular: `Status · Id · Data · Tipo · Valor apostado · ODDS · Quantia`. **Não** há linha em branco entre bilhetes — por isso a casa nunca pode cair no robô de texto genérico (`roboScroll`), que parte o `innerText` por linha em branco.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo (API) | Significado | Observação |
|---|---|---|
| `ID` | ID do bilhete | é o `# 298710215` do card · chave de dedup e do `[Código:]` |
| `ActionTime` | **colocação**, epoch ms **UTC** | converter para America/Sao_Paulo · NÃO é a coluna Data (ver §4) |
| `Items[].Game.StartTime` | início do evento, epoch ms UTC | a **mais recente** entre as pernas vira a coluna Data |
| `Amount` (= `SystemBet`) | **stake** | unidade normal (`150.0` = R$ 150,00) — **não** há milésimos |
| `Koef` | **odd total**, precisão completa | a tela trunca em 2 casas; o Koef é o valor real |
| `WinKoef` / `WinAmount` | odd e retorno realizados | ambos zerados/nulos em aberta e perdida |
| `PossibleWin` | retorno **potencial** | só faz sentido em aberta — nunca chamar de "retorno" |
| `Status` | 5 = em aberto · 10 = liquidado | enum bruto, ver §5 |
| `Result` | 0 pendente · 2 ganha · 3 perdida | enum bruto, ver §5 |
| `Items[].Value` | odd da perna | o produto das pernas == `Koef` (conferido) |
| `Items[].Market.Name` | mercado, já em pt-BR | pode conter placeholder `{p1_r}` (ver §12) |
| `Items[].Position.Name` | seleção (`Mais de`, `Menos de`, `Casa`, `Sim`) | |
| `Items[].FinalPosition.h` | linha do mercado | `-1.5` com `hisminus:true` em handicap |
| `Items[].LiveScore` | **placar** do jogo (`"4:2"`) | |
| `Items[].Team1Score/Team2Score` | ⚠ **estatística do mercado**, não placar | `9.0` = 9 escanteios |
| `Items[].CalculatedBetAmount` | ⚠ **rateio** da stake por perna | não é stake |
| `CashOut` / `PossibleCashout` | flags de cashout | sem caso na amostra (§7) |
| `IsBonus` / `IsSystem` | bônus / aposta de sistema | sem caso na amostra (§8) |
| `Count` | total de bilhetes da consulta | é o **fim autoritativo** |

---

## 3. ID do bilhete

- Formato: **numérico, 9 dígitos** (ex.: `298710215`), exibido no card como `# 298710215`.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da perna mais recente** (`MASTER_OUTPUT §4`).

A Tivo expõe as duas, e elas divergem:

- **colocação** — `ActionTime`. É o que a coluna "Data" do **card** mostra. Serve de contexto e de ordem; **não** é a coluna Data.
- **evento** — `Items[].Game.StartTime` (ou `OutrightGame.StartTime` no outright). **Usar a mais recente.**

> Não é detalhe: na amostra real de 24 bilhetes, **2 caem em dia diferente** — o outright de F1 é colocado em 22/07 para um evento em 25/07, e um de tênis é colocado em 17/05 para 18/05. Usar a colocação gravaria os dois no dia errado. O harness (`extensor/harness/casos/tivo.mjs`) trava as duas leituras para impedir a regressão.

Fuso: os dois campos são **epoch ms UTC** → converter para America/Sao_Paulo. Sem converter, o bilhete das 17:00Z pula para o dia seguinte.

---

## 5. Status e Resultado

De-para do par `Status` + `Result`:

| `Status` | `Result` | Leitura | Código |
|---|---|---|---|
| 5 | 0 | Em aberto (o card diz "Em andamento") | *(vazio — não liquidar)* |
| 10 | 3 | Perdeu | `L` |
| 10 | 2 | Ganhou — conferir o dinheiro (abaixo) | `W` |
| 10 | 2 | Retorno **igual** à stake | `V` |
| 10 | *outro* | **Desconhecido** — sobe cru, não liquidar automaticamente | — |

- O `Result` também existe **por perna** (`Items[].Result`), com os mesmos valores. Na amostra apareceu um `Result: 1` numa perna (bilhete `298710215`) cuja natureza **ainda não foi confirmada** — provável devolvida/void. Enquanto não houver um bilhete inteiro nesse estado para cruzar com a tela, ele sobe cru.
- Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho.

---

## 6. Boost / promoção

**Sem evidência de boost na amostra.** Em 100% das ganhas, `WinKoef == Koef` e `Koef × Amount` explica o `WinAmount` até o centavo. O bloco capturado usa `Koef`; se um boost aparecer no futuro, o dinheiro (`retorno ÷ stake`) passa a mandar automaticamente — a conciliação já está no formatador.

<!-- TODO: confirmar se a Tivo opera boost/odd turbinada e qual campo carrega. Sem amostra. -->

---

## 7. Cashout

Os campos existem (`CashOut: false`, `PossibleCashout: null`) mas **nenhum bilhete da amostra teve cashout**. Quando aparecer, vale a regra global: cashout **=** stake → `V`; cashout **≠** stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

<!-- TODO: capturar um bilhete com cashout real e travar no harness. -->

---

## 8. Bônus

`IsBonus` existe no payload; **sem caso na amostra**. O bloco capturado emite `Marcação da casa: aposta com bônus` quando a flag vier true, para a IA decidir pelo global.

---

## 9. Mapa de mercados (Tivo → `Aposta` global)

Só os mercados **confirmados** no dado real (camada fina — mercado nunca visto não entra aqui):

| Tivo exibe | Aposta global |
|---|---|
| `Time de casa total de escanteios` · `Time de Fora total de escanteios` · `2º Tempo - Total de escanteios` · `1º Tempo - Time de casa total de escanteios` · `1° Tempo - Time de fora total de escanteios` · `2º Tempo - Time de fora total de escanteios` | Escanteios |
| `Quem marca 5 escanteios primeiro` | Escanteios *(`MASTER_APOSTAS`: "primeiro a marcar X escanteios")* |
| `Total de cartões` · `Time de casa total de cartões` · `Time de fora total de cartões` · `1º Tempo - Time de casa total de cartões` · `1º Tempo - Time de fora total de cartões` · `1ªº Tempo - Total de cartões` · `2º Tempo - Total de cartões` · `2º Tempo - Total de cartões do time de fora` | Cartões |
| `Handicap de cartões` | Cartões *(handicap sobre estatística-prop segue o objeto — `MASTER_APOSTAS §1`)* |
| `Total de Finalizações` | Chutes |
| `Chutes a gol total` | Chutes no Gol |
| `Total de de impedimentos` *(sic — a casa duplica o "de")* | Impedimentos |
| `Total de Gols do Time de Casa` | Gols |
| `{p1_r} quarto - Total de pontos` · `2ª metade - Total de pontos (incl. prorrogação)` | Pontos |
| `Vencedor da partida` | ML |
| `Handicap de set` | Sets *(unidade contada = sets — `MASTER_APOSTAS`, tabela "unidade contada")* |

**Pendentes de decisão** — aparecem no dado real e **não** têm categoria óbvia. Ficam fora da
tabela acima de propósito: só entra no mapa o que está decidido.

- ⚠ `Total de faltas` — não existe categoria "Faltas" no `MASTER_APOSTAS §3`. Provável `Outros`.
  **Confirmar antes do 1º lote grande**: é dos mercados mais frequentes desta conta (8 dos 24).
- ⚠ `Total de defesas do goleiro` — idem. Provável `Outros` ou `Player Props` (a defesa é do
  goleiro, mas o mercado é do jogo).
- ⚠ `Free text multiwinner market` — rótulo interno do motor em **outright**. O mercado real é o
  `Outright.Name` (ex.: "Grande Prêmio da Hungria Qualificação - Top 3"); categoria a confirmar.

---

## 10. Stake

- Origem: `Amount` (unidade normal, sem milésimos). Normalização de moeda/milhar = global.
- ⚠ **Não** usar `CalculatedBetAmount`: é o rateio da stake entre as pernas.

---

## 11. Odds

- Origem: `Koef` (bilhete) e `Items[].Value` (perna), **precisão completa**.
- ⚠ **A tela trunca (floor) em 2 casas.** `208.4854` aparece como `208.48` e `16.047` como `16.04` — arredondar daria `208.49`/`16.05`, então é truncamento mesmo. **Nunca ler a odd do card.**
- Divergência conhecida: no bilhete `298394294` a tela mostra `4.34` e o `Koef` diz `4.35`. Fica com o `Koef` (campo estrutural). Como o bilhete é `L`, o P/L é −stake e a diferença não afeta nada.
- No `W`, o dinheiro confirma: `Koef × stake == WinAmount` ao centavo.

---

## 12. Ruído a ignorar

- `Market.Name` com **placeholder** `{p1_r}`: preencher com `FinalPosition.p1` (`{p1_r} quarto` + `p1:3` → "3º quarto"). Sem isso vaza template cru.
- `Team1Score`/`Team2Score` — estatística do mercado, **não** placar.
- `ResultUrl` (`SCOUT_DATA`, `whoscored.com`) — link de conferência da casa, não é dado do bilhete.
- `Price`, `BlockID`, `eubu`, `RakeBack`, `RiskBonusMaxWin` — internos do motor.

---

## 13. Pegadinhas (resumo rápido)

- Odd: **a tela trunca**, o `Koef` não → sempre `Koef`.
- Data: card mostra colocação; o TSV quer o **evento mais recente** (2 em 24 mudam de dia).
- `from`/`to` em **segundos** devolvem 0 bilhetes **sem erro**.
- `CalculatedBetAmount` ≠ stake · `Team1Score` ≠ placar.
- Outright tem `Game: null` e `Market.Name` inútil — usar `Outright` + `OutrightGame`.
- O sportsbook vive num **iframe**: o inject roda com `all_frames: true` e repassa ao topo.
- `Result` fora de {0,2,3} nunca vira W/L por dedução.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

- Coluna Data = evento mais recente (não a colocação).
- Odd com precisão completa, decimal com vírgula.
- Placeholder `{p1_r}` resolvido antes de montar a descrição.
- Bilhete aberto sai **sem** resultado (`extraction_state = aberta`).

---

## 15. Exemplos golden (bilhetes reais)

<!-- TODO: a casa acabou de entrar (s196) e ainda NÃO houve extração real validada ponta a
     ponta. Preencher com o primeiro lote conferido contra a planilha — sem isso, exemplo
     aqui seria chute com cara de gabarito. A regressão da CAPTURA (campos, data, odd,
     status) já está travada em `extensor/harness/casos/tivo.mjs`, com 21 bilhetes. -->

---

## Feedback para a camada global / MODELO

1. **`Total de faltas` e `Total de defesas do goleiro` não têm categoria** no `MASTER_APOSTAS §3`. São mercados frequentes nesta conta (faltas aparece em 8 dos 24 bilhetes). Decidir entre criar categoria nova ou mandar para `Outros` — se criar, roda `/propagar-categoria`.
2. **Handicap sobre unidade de pontuação:** a tabela "unidade contada" do `MASTER_APOSTAS` manda `Brasil -1.5 Sets` → `Sets`, enquanto a `CASA_PINNACLE §9` diz que handicap sobre a unidade do esporte é `Handicap`. Segui o MASTER (autoridade), mas as duas fontes se contradizem — vale alinhar.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA · tradução com 3 mercados pendentes (§9) e golden a preencher (§15)
CASA: Tivo
