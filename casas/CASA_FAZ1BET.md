# CASA_FAZ1BET
## Camada de tradução — Faz1bet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Faz1bet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Faz1bet` · site: `faz1.bet.br` (o domínio **não** traz o "bet" do nome)
- Locale: pt-BR · Moeda: R$ (BRL)
- **Decimal exibido na tela: PONTO** (`13.25`, `1,028.48`) → normalizar para vírgula.
- Motor: **BetConstruct** (sportsbook v4) — o mesmo da [`CASA_TIVO`](CASA_TIVO.md) e da [`CASA_BETFAST`](CASA_BETFAST.md).
- ⚠ Ao contrário das irmãs, o sportsbook **não** vive num iframe: a tela de apostas é a própria página (`/br/sportsbook/prematch#/mybets`). Isso não muda nada no código — o `all_frames: true` do manifest cobre os dois arranjos.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

### 1.1 Terceira casa do mesmo motor — o que isso significa na prática ⭐

A Faz1bet é a **mesma casa técnica** que a Tivo e a Betfast: mesmo motor, mesmo caminho de API, mesmos nomes de campo, mesmas armadilhas. Muda o domínio, a cor e — só — a **tradução de alguns rótulos de mercado** (§9).

Não foi assumido pela aparência. Foi **provado antes de escrever código** (s284):

| Prova | Faz1bet | Betfast / Tivo |
|---|---|---|
| `/sportsbookv4/sbloader.js` | **200 · application/javascript** | 200 |
| `POST /api/game/p/messagetosport` | **401** (existe, exige sessão) | 401 |
| rota inexistente no mesmo prefixo (controle) | **404** | 400 |
| corpo do pedido `gethistory` | `{"countOnly":false,"language":33,"from":"","to":""}` | idêntico |
| **campos do payload real** | **118, todos já existentes nas irmãs** | superconjunto |

A última linha é a prova que vale: a união de chaves da resposta logada é **subconjunto exato** das de `betfast.gethistory.json` + `tivo.gethistory.json` — **zero campo novo**. Não há nada nesta casa que o formatador das irmãs não saiba ler.

Consequência de engenharia: a captura usa o **mesmo `extensor/tv_inject.js`** e o **mesmo formatador**, sem uma linha duplicada. O harness roda a fixture desta casa pelos **três** domínios e compara os blocos byte a byte (`extensor/harness/casos/faz1bet.mjs`) — se alguém amarrar o código a um host, fica vermelho.

> **Ao mexer numa das três, confira as outras.** Toda armadilha registrada aqui vale para as irmãs e vice-versa.

### 1.2 ⚠ A grafia da casa mudou no banco quando ela foi registrada (s284)

`Faz1bet` e `Faz1Bet` conviviam no banco — 107 bilhetes na primeira (imports do arrudex e do LavaPessoal) e 26 na segunda (Lava, Feca, Jonathan). Enquanto a casa **não** estava no `_CASA_DISPLAY`, as duas grafias sobreviviam intactas: o round-trip `_casa_display(_display_to_key(x))` caía no ramo verbatim.

**Registrar a casa é uma mudança retroativa** — a partir do registro o `/salvar` impõe a grafia registrada, e conta que ficasse na outra passaria a gravar bilhete numa casa que a grade dela não enxerga (o bug da Jonbet, s249). Por isso a unificação veio **antes** do registro, não depois.

Canônica escolhida: **`Faz1bet`**, por três critérios independentes — a marca escreve minúsculo (`faz1bet` no HTML do site, 7 ocorrências, nenhuma com `B` maiúsculo), é a maioria dos bilhetes, e mover as 26 linhas de Lava/Feca/Jonathan toca menos base de terceiro do que mover as 107 de arrudex/LavaPessoal. Isso **inverteu** a decisão da s199, e a entrada do `MAPA` em `scripts/unificar_casas.py` foi invertida junto.

---

## 2. Modo de ingestão e layout ⭐

### 2.1 Modo de ingestão

**Captura por API** (SharpenUp · `extensor/tv_inject.js`, compartilhado com Tivo e Betfast). O histórico não tem endpoint próprio: sai de um proxy genérico do site, que encaminha mensagens ao motor da casa.

```
POST https://faz1.bet.br/api/game/p/messagetosport
{"name":"gethistory","message":"{\"countOnly\":false,\"language\":33,\"from\":…,\"to\":…}"}
→ {"Error":null,"Tickets":[…],"Count":9}
```

1. **A mesma URL serve dezenas de mensagens.** Quem separa o histórico é a **forma da resposta**: só vale o que vier com `Tickets` em array — nunca a URL nem o corpo.
2. **Sem paginação.** Uma chamada devolve a lista e a casa carimba `Count`.

> ⚠ **`from`/`to` são epoch em MILISSEGUNDOS.** Confirmado nesta casa: em segundos a API devolve `Count: 0` com `Error: null` — some tudo sem erro nenhum.

### 2.1.1 Os controles do filtro, rodados antes de acreditar no vazio

"0 resultados" pode ser o parâmetro quebrando a consulta em vez de ausência de dado (lição do `to`, s211). Medido nesta conta:

| consulta | resposta |
|---|---|
| sem filtro | 9 |
| `from`/`to` em **ms**, últimos 30 dias | 9 |
| `from`/`to` em **segundos** | **0**, `Error: null` — a armadilha |
| `to` no futuro (controle positivo) | 9 |
| `to` = ontem | **7** — subconjunto, o filtro age |
| `to` = 30 dias atrás | 0 — o vazio é real |

### 2.1.2 A varredura do teto NÃO dispara aqui (e isso é o certo)

O `Count` desta conta é **9**, muito abaixo do `TETO_ALERTA` de 50. A varredura retroativa por `to` (§2.1.1 da `CASA_BETFAST`) existe para quando a lista **para no teto e não tem "mostrar mais"** — disparar sem teto tocado só gastaria uma requisição por captura. O harness trava isso: `tetoSuspeito` tem de vir **falso** com esta fixture.

> Quando uma conta desta casa passar de 50 bilhetes, o comportamento a esperar é o da Betfast — e o mecanismo já está pronto e validado lá contra o servidor real.

### 2.2 Tipo do bilhete declarado

A coluna "Tipo" do card diz `Simples` / `Múltipla`. O nº de seleções vem de `Items.length`.

### 2.3 Layout do bilhete

Lista tabular: `Status · Id · Data · Tipo · Valor Apostado · ODDS · Quantia`, com abas `Tudo · Ativa · Ganhas · Perdidas`. **Não** há linha em branco entre bilhetes — por isso a casa nunca pode cair no robô de texto genérico (`roboScroll`), que parte o `innerText` por linha em branco (lição da KTO, s192).

⚠ O card estampa o status da aberta como **`CURRENT`** — em inglês, cru, enquanto o resto da tela está em pt-BR. É rótulo da casa, não estado novo: corresponde a `Status 5 · Result 0`.

---

## 2.5 Campos da API (o que o inject entrega)

Idênticos aos da `CASA_BETFAST §2.5` — a tabela não é repetida aqui de propósito (camada fina). O que **esta** amostra confirmou campo a campo:

| Campo (API) | Confirmado nesta casa |
|---|---|
| `ID` | numérico de 9 dígitos, é o `# 301526505` do card |
| `ActionTime` | colocação, epoch ms UTC · **não** é a coluna Data (§4) |
| `Items[].Game.StartTime` | início do evento, epoch ms UTC |
| `Amount` (= `SystemBet`) | stake em unidade normal (`100.0` = R$ 100,00) |
| `Koef` | odd total, precisão completa — **a tela trunca** (§11) |
| `PossibleWin` | retorno **potencial** da aberta — é a coluna "Quantia" do card (§5.1) |
| `WinAmount` | 0 nas perdidas **e** nas abertas |
| `Status` / `Result` | 5/0 aberta · 10/3 perdida |
| `Items[].Result` | 0 pendente · 2 ganhou · 3 perdeu (o `1` = anulada não apareceu, ver §5.2) |
| `Items[].Market.Name` | pt-BR, com placeholder `{p1_r}` em 1 perna (§12) |
| `Items[].FinalPosition.h` | linha do mercado (`1.5`, `27.5`, `9.5`) |

---

## 3. ID do bilhete

- Formato: **numérico, 9 dígitos** (ex.: `301526505`), exibido no card como `# 301526505`.
- Sempre visível → **dedup forte por ID**.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.
- O espaço de IDs é **do motor**, não da casa: os números da Faz1bet (`301…`) convivem na mesma faixa dos da Tivo e da Betfast (`29…`). Não é problema — a dedup é por (casa, parceiro, código).

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da perna mais recente** (`MASTER_OUTPUT §4`).

- **colocação** — `ActionTime`. É o que a coluna "Data" do **card** mostra. Serve de contexto e de ordem; **não** é a coluna Data.
- **evento** — `Items[].Game.StartTime`. **Usar a mais recente.**

> Não é detalhe: em **2 dos 9** bilhetes da amostra o evento cai em **dia diferente** da colocação — as duas abertas, colocadas em 22/08 à noite para jogos de 23/08. Usar a colocação gravaria as duas no dia errado.

Fuso: epoch ms **UTC** → converter para America/Sao_Paulo. Confirmado contra o card (`ActionTime` 17:35:14Z aparece como `14:35`).

---

## 5. Status e Resultado

De-para do par `Status` + `Result` (bilhete) — o mesmo das irmãs:

| `Status` | `Result` | Leitura | Código |
|---|---|---|---|
| 5 | 0 | Em aberto (o card diz **`CURRENT`**) | *(vazio — não liquidar)* |
| 10 | 3 | Perdeu | `L` |
| 10 | 2 | Ganhou — conferir o dinheiro | `W` |
| 10 | 2 | Retorno **igual** à stake | `V` |
| 10 | *outro* | **Desconhecido** — sobe cru, não liquidar automaticamente | — |

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho.

> Nos 9 bilhetes da amostra: **7 `L` e 2 abertas**. Nenhuma ganha, nenhuma anulada, nenhum cashout, bônus, sistema ou outright — ver §7, §8 e §15.

### 5.1 ⭐ A coluna "Quantia" de bilhete ABERTO é potencial, não retorno

O card mostra `1,028.48 BRL` na coluna Quantia de uma aposta **ainda em jogo**. É o `PossibleWin` (97,00 × 10,6029 = 1.028,48), não dinheiro pago — `WinAmount` é `0.0`.

Tratar isso como retorno é a **vitória fantasma** da VaideBet (s210): o bilhete sairia liquidado como `W` antes de o jogo acabar. O bloco capturado rotula explicitamente como `Retorno potencial:` e o status como *"em aberto (aguardando resultado — NÃO liquidar; sem resultado)"*. As duas leituras estão travadas no harness.

### 5.2 `Result` por perna

| `Items[].Result` | Leitura |
|---|---|
| 0 | pendente |
| **1** | **anulada / devolvida (void)** |
| 2 | ganhou |
| 3 | perdeu |

O `1` **não apareceu** nesta amostra (só 0, 2 e 3). Vale a prova aritmética feita na conta da Betfast (`CASA_BETFAST §5.2`), no mesmo motor: quando uma perna é anulada, a casa **recalcula o bilhete sem ela** e o `Koef` — que continua sendo o produto de todas — **mente**. Em `W` vale a régua global `Retorno ÷ Stake`.

---

## 6. Boost / promoção

Sem amostra. Nos 7 `L` não há retorno para conferir, e não houve `W`.
A `ItemType: 6` (odd oferecida — bet builder promocional da casa) **não apareceu** nesta conta, mas o motor é o mesmo e o formatador já a trata (`CASA_BETFAST §12.1`), inclusive o aviso de que os rótulos dela vêm em inglês.

<!-- TODO: conferir se a Faz1bet opera odd turbinada e ItemType 6. Sem amostra. -->

---

## 7. Cashout

`CashOut: false` e `PossibleCashout: null` em 9 de 9 — **nenhum caso na amostra**. Quando aparecer, vale a regra global: cashout **=** stake → `V`; cashout **≠** stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

<!-- TODO: capturar um bilhete com cashout real e travar no harness. -->

---

## 8. Bônus

`IsBonus` existe no payload; sem caso na amostra. `IsSystem` **`false` em 9 de 9** — nenhuma aposta de sistema.

---

## 9. Mapa de mercados (Faz1bet → `Aposta` global)

Só os mercados **confirmados no dado real desta casa** (camada fina): 15 rótulos distintos em 26 pernas.

> ⚠ **Esta casa NÃO traduz igual às irmãs.** Onde a Betfast escreve `2º Tempo - Total de escanteios`, a Faz1bet escreve **`2º metade - Total de escanteios`** — mesmo motor, mesmo `language: 33`, dicionário de tenant diferente. Por isso o §9 é por casa: copiar o da Betfast deixaria estes rótulos sem correspondência.

| Faz1bet exibe | Aposta global |
|---|---|
| `Total de finalizações` | Chutes |
| `Chutes a gol total` | Chutes no Gol |
| `Total de escanteios` variantes: `Time de Fora total de escanteios` · `2º metade - Total de escanteios` · `1º metade - Time de casa total de escanteios` · `2º metade - Time de fora total de escanteios` | Escanteios |
| `Total de cartões` · `Time de casa total de cartões` · `2º metade - Total de cartões do time de casa` | Cartões |
| `Total de de impedimentos` *(sic — a casa duplica o "de")* | Impedimentos |
| `Total de faltas` | Faltas |
| `Mais cartões` | H2H |
| `1º metade - Time de fora total de pontos` · `{p1_r} set - Total de pontos` | Pontos |

**Notas de decisão:**

- **`Total de de impedimentos` tem erro de digitação NA CASA** (o "de" repetido, com espaço à direita) e aparece assim nas 4 pernas. Registrado verbatim de propósito: é por este texto que o matcher compara, e "corrigir" aqui faria o mapa não casar com o dado real.
- **`Mais cartões` → `H2H`**, não `Cartões`: é quem faz **mais** no confronto, não quantos saem. Mesma régua da `CASA_BETFAST §9` e precedente `Maioria de 180's` na `CASA_BETANO §9`.
- **`Total de faltas` → `Faltas`**: categoria própria desde a s272.
- **`{p1_r} set - Total de pontos` → `Pontos`**: o placeholder é resolvido com `FinalPosition.p1` antes de virar descrição (§12).
- **`1º metade` / `2º metade`** são o recorte de tempo desta casa. O recorte **não muda a categoria** (`MASTER_APOSTAS §1`): quem manda é o objeto contado.

**Pendente de decisão** — aparece no dado real e **não** tem categoria óbvia. Fica fora da tabela de propósito:

- ⚠ `Total de defesas do goleiro` (1 ocorrência) — `CASA_BETNACIONAL §9` e `CASA_LOTTU` mapeiam defesas **de jogador nomeado** para `Player Props`, mas aqui o mercado é do jogo, sem jogador. **A mesma dúvida já está aberta na `CASA_TIVO §9` e na `CASA_BETFAST §9`** — agora nas três casas do motor. Decidir uma vez, valer para as três.

---

## 10. Stake

- Origem: `Amount` (unidade normal, sem milésimos). Normalização de moeda/milhar = global.
- ⚠ **Não** usar `CalculatedBetAmount`: é o rateio da stake entre as pernas.

---

## 11. Odds

- Origem: `Koef` (bilhete) e `Items[].Value` (perna), **precisão completa**.
- ⚠ **A tela trunca (floor) em 2 casas.** Medido nos 9 bilhetes conferidos contra o card, **7 divergem**:

  | `Koef` | a tela mostra | arredondar daria |
  |---|---|---|
  | 10.143 | `10.14` | 10.14 |
  | 10.1493 | `10.14` | 10.15 |
  | 10.6029 | `10.60` | 10.60 |
  | 10.971 | `10.97` | 10.97 |
  | 11.7157 | `11.71` | 11.72 |
  | 12.5235 | `12.52` | 12.52 |
  | 13.8928 | `13.89` | 13.89 |

  **O par de cima é o que dói:** dois bilhetes **diferentes** (`301527216` e `301479429`) aparecem no card com a **mesma** odd `10.14`. Ler a odd da tela funde dois bilhetes distintos no mesmo número. **Nunca ler a odd do card.**
- O produto das pernas confere com o `Koef` (2,0 × 2,07 × 2,45 = 10,143 no `301527216`).
- ⚠ **Com perna anulada o `Koef` NÃO vale** — ver §5.2. Vale `Retorno ÷ Stake`.

---

## 12. Ruído a ignorar

Mesmo conjunto das irmãs (`CASA_BETFAST §12`). Confirmado nesta amostra:

- `Market.Name` com **placeholder** `{p1_r}`: preencher com `FinalPosition.p1`. Sem isso vaza template cru para a IA.
- `Team1Score`/`Team2Score` — estatística do mercado, **não** placar (o placar é `LiveScore`).
- `CalculatedBetAmount` — rateio, não stake.
- `Price`, `BlockID`, `RakeBack`, `Company`, `Player.ExternalID` — internos do motor.

---

## 13. Pegadinhas (resumo rápido)

- Odd: **a tela trunca** (7 de 9), e dois bilhetes distintos exibem `10.14` → sempre `Koef`.
- **"Quantia" de bilhete aberto é POTENCIAL**, não retorno (§5.1) — tratar como retorno inventa vitória.
- Data: card mostra colocação; o TSV quer o **evento mais recente** (2 em 9 mudam de dia).
- O card diz **`CURRENT`** (em inglês) para aberta — é rótulo, não estado novo.
- `from`/`to` em **segundos** devolvem 0 bilhetes **sem erro**.
- Os rótulos de mercado usam **"metade"** onde as irmãs usam "Tempo" (§9), e um deles tem "de" duplicado.
- `Count == Tickets.length` não prova conta inteira quando o `Count` chega a 50 — ver `CASA_BETFAST §2.1.1`.
- Perna `Result: 1` = anulada → em `W` vale `Retorno ÷ Stake` (§5.2).
- Bloco `SEM DETALHE` (só o identificador) **não vira linha** — ver `CASA_BETFAST §5.3`.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

- Coluna Data = evento mais recente (não a colocação).
- Odd com precisão completa, decimal com vírgula.
- Bilhete aberto sai **sem** resultado (`extraction_state = aberta`) e com o potencial rotulado como potencial.
- Placeholder `{p1_r}` resolvido antes de montar a descrição.

---

## 15. Exemplos golden (bilhetes reais)

<!-- TODO: a casa entrou na s284 e ainda NÃO houve extração real validada ponta a ponta
     (payload conferido contra o card, mas o robô não rodou ao vivo pela extensão).
     Preencher com o primeiro lote conferido. A regressão da CAPTURA (campos, data do
     evento, odd completa, potencial da aberta, espelho pelos três hosts) já está travada
     em `extensor/harness/casos/faz1bet.mjs`, com 9 bilhetes reais e 19 conferências. -->

---

## Feedback para a camada global / MODELO

1. **`Total de defesas do goleiro` sem categoria** — agora nas **três** casas do motor BetConstruct (Tivo, Betfast, Faz1bet). O mercado é do jogo, sem jogador nomeado, então `Player Props` não serve. Decidir uma vez.
2. **O §9 é por casa mesmo quando o motor é o mesmo.** Esta casa provou que duas casas do mesmo motor, com o mesmo `language`, entregam rótulos diferentes (`metade` × `Tempo`). Vale registrar isso no guia de casa espelho: espelho compartilha *código*, não *dicionário*.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA (3ª casa do motor BetConstruct, espelho de Tivo/Betfast) · **captura ponta a ponta pela extensão ainda não rodada** · 1 mercado pendente (§9) · golden a preencher (§15) · sem amostra de W, anulada, cashout, bônus, sistema e `ItemType 6`
CASA: Faz1bet
