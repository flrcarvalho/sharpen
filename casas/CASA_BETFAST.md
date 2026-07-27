# CASA_BETFAST
## Camada de tradução — Betfast → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betfast.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betfast` · site: `betfast.bet.br` (serve também em `www.betfast.bet.br`; as duas respondem 200, sem redirecionar)
- **Duas contas conhecidas** (= dois `Parceiro` no sistema): `fecanario` (50 bilhetes, a do payload de referência) e `flrcarvalho` (32, a que loga no navegador do dev). Os achados desta doc foram confirmados **nas duas** — ver §5.2 e §12.1.
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `CurrencySTR: "BRL"`
- **Decimal exibido na tela: PONTO** (`24.28`, `1,604.28`) → normalizar para vírgula.
- Motor: **BetConstruct** (sportsbook v4), servido num **iframe de mesma origem** dentro do site.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

### 1.1 Espelho da Tivo — o que isso significa na prática  ⭐

A Betfast é a **mesma casa técnica** que a [`CASA_TIVO`](CASA_TIVO.md): mesmo motor, mesmo caminho de API, mesmos nomes de campo, mesmas armadilhas. Muda o domínio e a cor.

Não foi assumido — foi **provado antes de escrever código**:

| Prova | Betfast | Tivo |
|---|---|---|
| `/sportsbookv4/sbloader.js` no HTML | sim | sim (carregado por JS) |
| `POST /api/game/p/messagetosport` | **401** (existe, exige sessão) | **401** |
| rota inexistente (controle) | 400 | — |
| corpo do pedido `gethistory` | `{"countOnly":false,"language":33,"from":"","to":""}` | idêntico |
| campos de bilhete e de perna | idênticos | idênticos |

Consequência de engenharia: a captura usa o **mesmo `extensor/tv_inject.js`** e o **mesmo formatador**, sem uma linha duplicada. O harness roda a mesma fixture pelos dois domínios e compara os blocos **byte a byte** (`extensor/harness/casos/betfast.mjs`) — se alguém amarrar o código a um host, fica vermelho.

> **Ao mexer numa das duas, confira a outra.** Toda armadilha registrada aqui vale para a Tivo e vice-versa. As duas amostras se completam: a Tivo trouxe o outright de F1 e o bloco `SEM DETALHE`; a Betfast trouxe a perna anulada e a odd oferecida (§5.2 e §12.1).

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API** (SharpenUp · `extensor/tv_inject.js`, compartilhado com a Tivo). O histórico não tem endpoint próprio: sai de um proxy genérico do site, que encaminha mensagens ao motor da casa.

```
POST https://betfast.bet.br/api/game/p/messagetosport
{"name":"gethistory","message":"{\"countOnly\":false,\"language\":33,\"from\":…,\"to\":…}"}
→ {"Error":null,"Tickets":[…],"Count":50}
```

1. **A mesma URL serve dezenas de mensagens** (saldo, notificações, tradução). Quem separa o histórico é a **forma da resposta**: só vale o que vier com `Tickets` em array.
2. **Sem paginação conhecida.** Uma chamada devolve a lista e a casa carimba `Count`. Fim declarado: `Error:null` + `Tickets.length === Count`.

Filtro de aba (`result` na mensagem): omitido = tudo · `0` aberta · `2` ganha · `3` perdida. O robô **não** usa o filtro: pede tudo de uma vez.

> ⚠ **`from`/`to` são epoch em MILISSEGUNDOS.** Em segundos a API devolve `Count: 0` com `Error: null` — some tudo sem erro nenhum.

### 2.1.1 ⭐ `Count: 50` é TETO DA CONSULTA, não fim de conta — e a varredura fura

A primeira coleta real (27/07/2026) respondeu **`Count: 50` com exatamente 50 bilhetes**. Na Tivo o `Count` era 24, então esse limite **nunca tinha sido exercitado**.

**Confirmado pelo operador:** a lista da Betfast **para nesse limite e não tem "mostrar mais" nem carregamento automático**. Ou seja, `Tickets.length === Count` significa **"a consulta encheu"**, não "a conta acabou". Um bilhete mais antigo que o teto seria **invisível para sempre, sem erro nenhum** — a mesma família de falha que custou 39 de 61 bilhetes na s179.

**A tela não mostra, mas a API entrega.** O `gethistory` aceita `to`, então o robô não aposta numa leitura: ao tocar o teto ele **pergunta** — pede tudo anterior ao bilhete mais antigo que já tem e repete até uma janela voltar sem novidade.

| desfecho | o que significa | o que o operador vê |
|---|---|---|
| 1ª janela volta vazia | o teto era mesmo o total | nada (custou 1 requisição) |
| janelas trazem bilhetes | havia histórico escondido | *"a captura foi além do teto: N bilhetes, mais do que a tela mostra"* |
| varredura não concluiu | rede caiu / teto de 40 janelas | aviso para rodar de novo antes de considerar o período fechado |

A varredura **só roda quando o teto foi tocado** e **não roda com janela de dias pedida** (aí o corte é intencional do operador). A Tivo, com `Count 24`, nunca entra nesse ramo — o caminho provado dela segue intacto. Os dois desfechos estão travados em `casos/betfast.mjs`, inclusive com uma "página 2" sintética que só existe pela API.

#### ✅ Validado contra o servidor real (s211, conta `flrcarvalho`)

O harness prova o algoritmo; isto prova que **a casa colabora**. Três medições ao vivo:

| teste | resultado |
|---|---|
| `to` no futuro | devolve os 32 da conta — o parâmetro não quebra a consulta |
| `to` no meio da faixa | devolve 26, **todos anteriores ao corte** e subconjunto do total |
| `to` = mais antigo − 1 | `Count: 0`, `Error: null` — não há nada antes |

E o laço completo, com o teto **simulado** (1ª consulta limitada aos 6 mais recentes, fingindo uma lista cheia):

```
inicial (teto fingido) →  6 bilhetes
to < 17/06 12:31       → 26 novos → 32
to < 08/05 13:10       →  0 novos → para sozinha
```

Recuperou **32 de 32**, nenhum faltando. É a prova que a fixture não pode dar: **a casa respeita o `to`**, então a varredura recupera de fato o histórico que a tela esconde.

> ⚠ O que isso **não** prova: o teto de 50 em si. Esta conta tem 32 bilhetes e nunca o toca — quem tocou foi a `fecanario`, com 50. O mecanismo está validado; o gatilho, não.

### 2.2 Tipo do bilhete declarado

A coluna "Tipo" do card diz `Simples` / `Múltipla`. O nº de seleções vem de `Items.length` — **exceto na odd oferecida** (§12.1), onde a casa conta 1 perna e por dentro são várias.
Quando **todas** as pernas são do mesmo evento, o bloco capturado acrescenta a linha `Mesmo jogo: …` — sinal para a IA classificar Múltipla × Bet Builder pelo `MASTER_ESPORTES`, sem que o rótulo da casa decida sozinho.

### 2.3 Layout do bilhete

Lista tabular: `Status · Id · Data · Tipo · Valor apostado · ODDS · Quantia`, com abas `Tudo · Ativa · Ganha · Perdidas`. **Não** há linha em branco entre bilhetes — por isso a casa nunca pode cair no robô de texto genérico (`roboScroll`), que parte o `innerText` por linha em branco.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo (API) | Significado | Observação |
|---|---|---|
| `ID` | ID do bilhete | é o `# 298388575` do card · chave de dedup e do `[Código:]` |
| `ActionTime` | **colocação**, epoch ms **UTC** | converter para America/Sao_Paulo · NÃO é a coluna Data (ver §4) |
| `Items[].Game.StartTime` | início do evento, epoch ms UTC | a **mais recente** entre as pernas vira a coluna Data |
| `Amount` (= `SystemBet`) | **stake** | unidade normal (`151.0` = R$ 151,00) — **não** há milésimos |
| `Koef` | **odd total** do bilhete, precisão completa | a tela trunca em 2 casas; o Koef é o valor real (§11) |
| `WinKoef` | odd **realizada** | ⚠ difere do `Koef` quando há perna anulada (§5.2) |
| `WinAmount` | retorno realizado | 0 nas perdidas E nas abertas |
| `PossibleWin` | retorno **potencial** | só faz sentido em aberta — nunca chamar de "retorno" |
| `Status` | 5 = em aberto · 10 = liquidado | enum bruto, ver §5 |
| `Result` | 0 pendente · 2 ganha · 3 perdida | enum bruto, ver §5 |
| `Items[].Value` | odd da perna | o produto das pernas == `Koef` (conferido) |
| `Items[].Result` | resultado da perna | **0 pendente · 1 ANULADA · 2 ganhou · 3 perdeu** (§5.2) |
| `Items[].ItemType` | 0 = normal · 3 = outright · **6 = odd oferecida** | o `6` exige leitura especial (§12.1) |
| `Items[].OfferedOddObject` | conteúdo real da odd oferecida | só no `ItemType 6` · rótulos **em inglês** |
| `Items[].Market.Name` | mercado, já em pt-BR | pode conter placeholder `{p1_r}` (ver §12) |
| `Items[].Position.Name` | seleção (`Mais de`, `Abaixo`, `Casa`, `Sim`) | |
| `Items[].FinalPosition.h` | linha do mercado | `-1.5` com `hisminus:true` em handicap |
| `Items[].LiveScore` | **placar** do jogo (`"4:2"`) | |
| `Items[].Team1Score/Team2Score` | ⚠ **estatística do mercado**, não placar | `9.0` = 9 escanteios |
| `Items[].CalculatedBetAmount` | ⚠ **rateio** da stake por perna | não é stake |
| `CashOut` / `PossibleCashout` | flags de cashout | sem caso na amostra (§7) |
| `IsBonus` / `IsSystem` | bônus / aposta de sistema | sem caso na amostra (§8) |
| `Count` | bilhetes **desta consulta** | ⚠ é teto, não total da conta — ver §2.1.1 |

---

## 3. ID do bilhete

- Formato: **numérico, 9 dígitos** (ex.: `298388575`), exibido no card como `# 298388575`.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.
- O espaço de IDs é **do motor**, não da casa: os números da Betfast e da Tivo convivem na mesma faixa (`29xxxxxxx`). Isso não é problema — a dedup é por (casa, parceiro, código), não pelo número solto.

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da perna mais recente** (`MASTER_OUTPUT §4`).

A Betfast expõe as duas, e elas divergem:

- **colocação** — `ActionTime`. É o que a coluna "Data" do **card** mostra. Serve de contexto e de ordem; **não** é a coluna Data.
- **evento** — `Items[].Game.StartTime` (ou `OutrightGame.StartTime`, ou `OfferedOddObject.StartTime` na odd oferecida). **Usar a mais recente.**

> Não é detalhe: em **8 dos 50** bilhetes da amostra o evento cai em **dia diferente** da colocação (contra 2 em 24 na Tivo). Usar a colocação gravaria esses 8 no dia errado. O harness trava as duas leituras.

Fuso: `ActionTime` e `Game.StartTime` são **epoch ms UTC** → converter para America/Sao_Paulo. Confirmado contra o card: `ActionTime 15:22:02Z` aparece como `12:22`.

### 4.1 A exceção da odd oferecida — string sem fuso, lida como horário do Brasil

O `OfferedOddObject.StartTime` é **string ISO sem offset** (`"2026-07-02T00:00:00"`), enquanto todo o resto do motor é epoch ms UTC.

**Decisão do Feca (s211): tratar como horário do Brasil** — o valor literal da string é a hora local. O inject carimba `-03:00` explicitamente, e não deixa o JS resolver: `new Date("2026-07-02T00:00:00")` usa o fuso **da máquina**, então o mesmo bilhete daria data diferente num operador fora do país. Offset fixo (não `America/Sao_Paulo`) porque o Brasil não opera horário de verão desde 2019 e todo histórico aqui é posterior; string que já traga offset ou `Z` é respeitada como veio.

Efeito nos 4 bilhetes: em 3 muda só a hora; no `296275825` (USA x Bósnia) muda o **dia** — fica **02/07**, não 01/07. É a linha do harness que acusa se alguém reverter o offset.

---

## 5. Status e Resultado

De-para do par `Status` + `Result` (bilhete):

| `Status` | `Result` | Leitura | Código |
|---|---|---|---|
| 5 | 0 | Em aberto (o card diz "Ativa") | *(vazio — não liquidar)* |
| 10 | 3 | Perdeu | `L` |
| 10 | 2 | Ganhou — conferir o dinheiro (abaixo) | `W` |
| 10 | 2 | Retorno **igual** à stake | `V` |
| 10 | *outro* | **Desconhecido** — sobe cru, não liquidar automaticamente | — |

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho.

> Nos 50 bilhetes da `fecanario`: 45 `L` e 5 `W`. Nos 32 da `flrcarvalho`: 27 `L` e 5 `W`. **Nenhuma aberta em 82 bilhetes, nas duas contas** — e nenhum cashout, bônus, aposta de sistema ou outright. Essas pendências (§7, §8) não são falta de procura: são estados que estas contas não produziram.

### 5.1 `Result` por perna

| `Items[].Result` | Leitura |
|---|---|
| 0 | pendente |
| **1** | **anulada / devolvida (void)** |
| 2 | ganhou |
| 3 | perdeu |

### 5.2 ⭐ Perna anulada (`Result: 1`) — a casa recalcula o bilhete

**Este é o caso em que a odd do card mente sobre o P/L.** Quando uma perna é anulada, ela sai do cálculo e a casa liquida o bilhete pelo produto das pernas restantes. O `Koef` **continua sendo o produto de TODAS** — inclusive a void.

Prova aritmética, bilhete `295698756` (stake R$ 151,00):

| perna | odd | `Result` | |
|---|---|---|---|
| `Innings 1 até 5 - Total do time de casa`, Abaixo 1.5 | 1.95 | **1** | anulada — fora do cálculo |
| `Innings 1 até 5 - Total do time de fora`, Abaixo 0.5 | 2.67 | 2 | ganhou |

`Koef` = **5,2065** (1,95 × 2,67) · `WinKoef` = **2,67** · `WinAmount` = **403,17** = 151 × 2,67, **ao centavo**.

Ler o `Koef` daria retorno de R$ 786,18 — quase o **dobro** do que a casa pagou.

**Regra:** vale a régua global (`MASTER_RESULTADO`) — em `W` a odd é **`Retorno ÷ Stake`**, sempre. O formatador já concilia: só usa o `Koef` quando ele explica o retorno até o centavo. Em `L` não há retorno para recalcular, então a odd segue sendo o `Koef` cheio (o bilhete `298710145` tem uma perna void e é `L`).

> Isso **fecha a pendência aberta da Tivo**: a `CASA_TIVO §5` carregava o `Result: 1` como "natureza ainda não confirmada" desde a s196. Mesmo motor, mesma resposta.

> **Confirmado nas duas contas:** `fecanario` tem 3 pernas `Result: 1` (uma delas no `295698756`, que é o W onde o dinheiro prova a regra) e `flrcarvalho` tem 1 (`293761188`, perna de odd 3,35 anulada num bilhete que perdeu por outra perna). Não é anomalia de uma conta.

### 5.3 Bloco `SEM DETALHE` — não extrair

Às vezes o motor devolve o bilhete **só com o identificador** (aconteceu na Tivo, s198; não apareceu na amostra da Betfast, mas o código é o mesmo). O bloco chega assim:

```
[Código: 291115424]
SEM DETALHE — a casa devolveu só o identificador deste bilhete.
NÃO extraia esta aposta: recapture. Não invente stake, odd, data nem resultado.
```

**Não gere linha** para esse bloco — nem vazia, nem "aberta". Ele existe para a conferência de cobertura cobrar o bilhete de volta e pedir reprocessamento; qualquer linha inventada aqui vira aposta fantasma no banco.

---

## 6. Boost / promoção

**Boost de odd não aparece na amostra.** Nos 4 `W` sem perna anulada, `Koef × Amount` explica o `WinAmount` até o centavo.

O que a casa **tem** é a **odd oferecida** (`ItemType 6`, §12.1): um bet builder pré-montado com preço negociado pela casa. Não é boost sobre uma odd base — é um produto próprio, e o `Koef` já é o preço final. Os campos `RealPrice` (6.17) e `CalcPrice` (7.1) do objeto interno **divergem entre si e do `Koef`** (9.51) e **não** devem ser usados: só o `Koef` é a odd do bilhete.

<!-- TODO: confirmar se a Betfast opera odd turbinada sobre seleção avulsa e qual campo carrega. Sem amostra. -->

---

## 7. Cashout

Os campos existem (`CashOut: false`, `PossibleCashout: null` em 50 de 50) mas **nenhum bilhete da amostra teve cashout**. Quando aparecer, vale a regra global: cashout **=** stake → `V`; cashout **≠** stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

<!-- TODO: capturar um bilhete com cashout real e travar no harness. -->

---

## 8. Bônus

`IsBonus` existe no payload; **`false` em 50 de 50**. O bloco capturado emite `Marcação da casa: aposta com bônus` quando a flag vier true, para a IA decidir pelo global.
`IsSystem` idem — nenhuma aposta de sistema na amostra.

---

## 9. Mapa de mercados (Betfast → `Aposta` global)

Só os mercados **confirmados no dado real desta casa** (camada fina). São 64 rótulos distintos em 50 bilhetes — amostra bem mais rica que a da Tivo, e por isso este §9 é maior que o dela.

| Betfast exibe | Aposta global |
|---|---|
| `Total de finalizações` · `Total de finalizações do time de casa` · `Total de finalizações do time de fora` | Chutes |
| `Total de Chutes ao gol` · `Chutes ao gol` · `Time de casa chutes a gol` · `Time de fora chutes a gol` | Chutes no Gol |
| `Total de escanteios` · `Total de escanteios time da casa` · `Total de escanteios time de fora` · `2º Tempo - Total de escanteios` · `1º Tempo - Time de casa total de escanteios` · `1° Tempo - Time de fora total de escanteios` · `2º Tempo - Time de casa total de escanteios` | Escanteios |
| `Primeiro Escanteio` · `Quem marca 5 escanteios primeiro` · `Quem marca 7 escanteios primeiro` | Escanteios |
| `Total de cartões` · `Time de casa total de cartões` · `Time de fora total de cartões` · `1º Tempo - Time de casa total de cartões` · `1º Tempo - Time de fora total de cartões` · `1º Tempo - Total de cartões` · `2º Tempo - Total de cartões do time de fora` | Cartões |
| `Mais escanteios` · `1º Tempo - Mais escanteios` · `2º Tempo - Mais escanteios` · `Mais cartões` · `Mais finalizações` | H2H |
| `Total de impedimentos` · `Time de casa total de impedimentos` · `Time de fora total de impedimentos` | Impedimentos |
| `Total de Gols` · `Total de Gols do Time de Casa` · `Total de Gols do time de Fora` | Gols |
| `Total de desarmes` | Desarmes |
| `Total de tiros de meta` · `Time de fora total de tiro de meta` | Team Props |
| `Vencedor da partida` · `Vencedor da partida (incl. prorrogação)` · `Resultado da Partida` | ML |
| `Dupla Chance` | Dupla Chance |
| `1ª Tempo - Para ganhar  - Empate não tem aposta` | DNB |
| `Handicap (incl. prorrogação)` · `1º Tempo - Handicap` | Handicap |
| `Handicap de set` | Sets |
| `{p1_r} set - Total de pontos` · `1º set - Total de pontos` · `{p1_r} quarto - Total de pontos` · `Total de pontos` · `Total de pontos (incl. prorrogação)` | Pontos |
| `Innings 1 até 5 - Total` · `Innings 1 até 5 - Total do time de casa` · `Innings 1 até 5 - Total do time de fora` | Corridas |
| `1º Mapa - Total de Abates` | E-Sports Props |
| `Total de faltas` · `Time da casa Total de faltas` · `Time de fora Total de faltas` · `Handicap Asiático de faltas` | Outros |
| `Total de cobranças de lateral` · `1° Tempo  - Total de cobranças de lateral` | Outros |

**Notas de decisão** (por que cada um caiu onde caiu):

- **`Mais X` → `H2H`, não a categoria do objeto.** O `MASTER_APOSTAS §H2H` define "mercado comparativo entre duas entidades" e lista literalmente *"mais rebotes · mais assistências · mais kills · mais pontos"*. `Mais escanteios` é quem faz **mais** no confronto, não quantos saem. Precedente: `Maioria de 180's` → `H2H` na `CASA_BETANO §9`.
- **`Quem marca X escanteios primeiro` → `Escanteios`** (não H2H): o `§4` lista *"Primeiro a marcar X escanteios (race / corrida)"* como sinônimo de `Escanteios`. É corrida contra uma linha, não comparativo entre times.
- **`Tiros de meta` → `Team Props`**: sinônimo oficial no `MASTER_APOSTAS §4` (*"Tiros de Meta · Total de Tiros de Meta"*), já aplicado em `CASA_BETANO §9`.
- **`Abates` → `E-Sports Props`**: sinônimo oficial (*"Total de Kills / Abates"*), e o §E-Sports manda usar `E-Sports Props` e **nunca** `Player Props` quando o objeto é estatística de e-sport.
- **`Handicap de set` → `Sets`**: handicap sobre a unidade contada segue o objeto (tabela "unidade contada" do `MASTER_APOSTAS`), mesmo caminho da `CASA_TIVO §9`.
- **`Innings 1 até 5 - …` → `Corridas`**: beisebol, o objeto contado é corrida. Precedente firmado na `CASA_VAIDEBET §9` (s210).
- **`Total de faltas` → `Outros`**: não existe categoria "Faltas" no `§3`. Precedente explícito em `CASA_BETANO §9` (`Total de Faltas → Outros ⚠️ nicho`). Aplicado também a `Handicap Asiático de faltas` — handicap segue o objeto.
- **`Total de cobranças de lateral` → `Outros`**: mesmo caso das faltas (estatística de jogo sem categoria própria). Sem precedente direto; segue a régua das faltas por analogia.

**Pendentes de decisão** — aparecem no dado real e **não** têm categoria óbvia. Ficam fora da tabela de propósito: só entra no mapa o que está decidido.

- ⚠ `Total de defesas do goleiro` (2 ocorrências) — `CASA_BETNACIONAL §9` e `CASA_LOTTU` mapeiam defesas **de jogador nomeado** para `Player Props`, mas aqui o mercado é do jogo, sem jogador. A mesma dúvida está aberta na `CASA_TIVO §9`. Decidir uma vez, valer para as duas.
- ⚠ `Handicap de mapas` · `Map Advantage` (1 cada, CS2) — a unidade contada em e-sports é o **mapa**, que não tem categoria própria. Entre `Handicap` (é handicap sobre a unidade) e `E-Sports Props` (o §E-Sports puxa tudo de e-sport para lá) as duas leituras têm apoio no MASTER. Não decidi sozinho.

---

## 10. Stake

- Origem: `Amount` (unidade normal, sem milésimos). Normalização de moeda/milhar = global.
- ⚠ **Não** usar `CalculatedBetAmount`: é o rateio da stake entre as pernas.

---

## 11. Odds

- Origem: `Koef` (bilhete) e `Items[].Value` (perna), **precisão completa**.
- ⚠ **A tela trunca (floor) em 2 casas.** Medido em 17 bilhetes conferidos contra o card, **7 divergem**:

  | `Koef` | a tela mostra | arredondar daria |
  |---|---|---|
  | 2.058 | `2.05` | 2.06 |
  | 7.215 | `7.21` | 7.22 |
  | 15.6087 | `15.60` | 15.61 |
  | 3.3874 | `3.38` | 3.39 |
  | 18.3698 | `18.36` | 18.37 |
  | 23.9456 | `23.94` | 23.95 |
  | 93.3987 | `93.39` | 93.40 |

  É truncamento, não arredondamento. **Nunca ler a odd do card.**
- No `W` sem perna anulada, o dinheiro confirma: `Koef × stake == WinAmount` ao centavo (101 × 15,884 = 1.604,28).
- ⚠ **Com perna anulada o `Koef` NÃO vale** — ver §5.2. Vale `Retorno ÷ Stake`.

---

## 12. Ruído a ignorar

- `Market.Name` com **placeholder** `{p1_r}`: preencher com `FinalPosition.p1` (`{p1_r} set` + `p1:3` → "3º set"). Sem isso vaza template cru. Aparece em 6 bilhetes desta amostra.
- `Team1Score`/`Team2Score` — estatística do mercado, **não** placar.
- `ResultUrl` (`SCOUT_DATA`, `whoscored.com`) — link de conferência da casa, não é dado do bilhete.
- `Price`, `BlockID`, `eubu`, `RakeBack`, `RiskBonusMaxWin` — internos do motor.
- `OfferedOddObject.RealPrice` / `.CalcPrice` — preços internos da oferta; **não** são a odd (§6).
- `OfferedOddObject…SubItems[].PriceResult` — enum **diferente** do `Items[].Result` (aparecem `3` e `4`, onde o outro usa `2` e `3`) e **nunca cruzado com a tela**. Não traduzir; o resultado que vale é o do bilhete.

### 12.1 ⭐ `ItemType: 6` — odd oferecida (bet builder promocional)

**4 dos 50 bilhetes (8%).** A perna vem com `Game`, `Market`, `Position` e `Sport` **todos `null`** — sem tratamento, o bloco sairia mudo (`- [perdeu]`) e a IA teria de inventar esporte e descrição.

Todo o conteúdo está em `Items[].OfferedOddObject`:

```
Norway - England · World Cup / Quarter-finals · StartTime 2026-07-11T21:00:00
  ├ Match result → "2"                              1.81
  ├ Kane, Harry shots on target → "2 and more"      1.95
  └ Haaland, Erling shots on target → "2 and more"  1.82
```

Três coisas a saber:

1. **Os rótulos vêm em INGLÊS** (`Soccer`, `Match result`, `shots on target`, `Total corners`) — o `language: 33` do pedido **não alcança** este objeto. O bloco capturado avisa a IA disso explicitamente. Traduzir é trabalho da IA com o `MASTER_APOSTAS`, não da extensão.
2. **A casa conta como `Simples`** (`Items.length === 1`), mas são N seleções do **mesmo evento**: é bet builder. O bloco emite `Tipo: Aposta turbinada da casa (bet builder — 3 seleções do mesmo evento)` para a IA não classificar como simples e perder as outras seleções da descrição.
3. **A odd é o `Koef` do bilhete**, não o produto das sub-seleções (6,4237 contra 9,51) nem os preços internos. A oferta tem preço negociado pela casa.

Data do evento: `OfferedOddObject.StartTime`, lido como horário do Brasil (§4.1).

Na amostra da `fecanario`, os 4 são de futebol (Copa do Mundo). Esporte declarado: `Soccer` → `Futebol` pelo `MASTER_ESPORTES`.

> **Confirmado na segunda conta:** a `flrcarvalho` tem mais **2** `ItemType 6` entre 32 bilhetes. O tipo é recorrente na casa, não um acidente do lote de referência — e nas duas contas o `Sport` da perna vem `null`, que é exatamente o que deixaria o bloco mudo.

---

## 13. Pegadinhas (resumo rápido)

- Odd: **a tela trunca** (7 de 17 conferidos), o `Koef` não → sempre `Koef`.
- **Perna `Result: 1` = anulada** → o `Koef` inclui ela e superestima o retorno; em `W` vale `Retorno ÷ Stake` (§5.2).
- Data: card mostra colocação; o TSV quer o **evento mais recente** (8 em 50 mudam de dia).
- `ItemType: 6` sai mudo se não ler o `OfferedOddObject` (§12.1) — e os rótulos vêm em inglês.
- `Count == Tickets.length` **não prova** conta inteira: é o teto da consulta, e a lista não tem "mostrar mais". A varredura retroativa por `to` é que fecha a cobertura (§2.1.1).
- `from`/`to` em **segundos** devolvem 0 bilhetes **sem erro**.
- `CalculatedBetAmount` ≠ stake · `Team1Score` ≠ placar.
- Outright tem `Game: null` e `Market.Name` inútil — usar `Outright` + `OutrightGame`.
- O sportsbook vive num **iframe**: o inject roda com `all_frames: true` e repassa ao topo.
- `Result` do bilhete fora de {0,2,3} nunca vira W/L por dedução.
- Bloco `SEM DETALHE` (só o identificador) **não vira linha** — ver §5.3.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

- Coluna Data = evento mais recente (não a colocação).
- Odd com precisão completa, decimal com vírgula.
- Em bilhete com perna anulada e resultado `W`: odd == `Retorno ÷ Stake`.
- Placeholder `{p1_r}` resolvido antes de montar a descrição.
- Bilhete de odd oferecida (`ItemType 6`) sai com jogo, esporte, liga e todas as sub-seleções.
- Bilhete aberto sai **sem** resultado (`extraction_state = aberta`).

---

## 15. Exemplos golden (bilhetes reais)

<!-- TODO: a casa entrou na s211 e ainda NÃO houve extração real validada ponta a ponta
     (payload conferido contra o card, mas o robô não rodou ao vivo). Preencher com o
     primeiro lote conferido contra a planilha — sem isso, exemplo aqui seria chute com
     cara de gabarito. A regressão da CAPTURA (campos, data, odd, perna anulada, odd
     oferecida, espelho) já está travada em `extensor/harness/casos/betfast.mjs`, com 50
     bilhetes reais e 39 conferências. -->

---

## Feedback para a camada global / MODELO

1. **`Faltas` é frequente demais para ficar em `Outros`.** Nesta conta aparece em **11 pernas** (`Total de faltas`, por time, e `Handicap Asiático de faltas`) — mais que `Gols`. O precedente da `CASA_BETANO` manda `Outros ⚠️ (nicho)`, e foi o que apliquei, mas "nicho" já não descreve o volume. Candidato a categoria própria via `/propagar-categoria`.
2. **`Cobranças de lateral` e `Tiro de meta` são a mesma família de `Faltas`** (estatística de jogo sem categoria), mas hoje caem em lugares diferentes: lateral em `Outros` e tiro de meta em `Team Props` (por sinônimo explícito do §4). Vale alinhar a régua — ou as três viram categoria, ou as três viram `Outros`.
3. **Unidade contada em e-sports.** O MASTER resolve `Sets` e `Games`, mas não diz onde cai handicap/total de **mapas**. Ver os pendentes do §9.
4. **`Result: 1` = anulada** (§5.2) foi confirmado aqui e vale para a `CASA_TIVO`, que registrava o enum como não confirmado desde a s196.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA (espelho da Tivo) · varredura do teto **validada contra o servidor real** (§2.1.1) · **captura ponta a ponta pela extensão ainda não rodada** · 2 mercados pendentes (§9) · golden a preencher (§15)
CASA: Betfast
