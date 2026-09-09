# CASA_R7
## Camada de tradução — R7 → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da R7.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `R7` · site: `r7.bet.br`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `CustomerCurrencyCode: "BRL"`
- **Decimal na API: PONTO** (`"2.45"`, `612.5`) → normalizar para vírgula na saída.
- Motor: **Rogue** — plataforma própria, servida do **próprio domínio da casa** em `/api/sportsbook/rogue/…`, como a Novibet. Não é Altenar/BIA, não é BetBy, não é Kambi, não é BetConstruct.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> ⚠️ **A grafia canônica é `R7`, e isso foi MEDIDO antes de registrar** (s335), nas tabelas onde `casa` é texto: 40 bilhetes (arrudex 25, Feca 15), 3 contas e 17 correções em `R7`, contra **1 bilhete e 2 contas** na gêmea `r7.bet` — que é um domínio, não um nome de casa, e nasceu de cadastro à mão. A gêmea foi unificada com `scripts/unificar_casas.py --somente r7.bet` **antes** desta casa entrar no `_CASA_DISPLAY`. Na ordem inversa, o bilhete do outro dono ficaria numa casa que a conta dele não enxerga — grade vazia, sem erro nenhum, o defeito que matou a Jonbet na s249.

### 1.1 Três casas espelho — o que isso significa na prática ⭐

A R7 é a **mesma casa técnica** que a [`CASA_BETAO`](CASA_BETAO.md) e a [`CASA_7GAMES`](CASA_7GAMES.md): mesmo motor, mesmo caminho de API, mesmos nomes de campo, mesmos enums, mesmas armadilhas. Muda o domínio e a cor.

Não foi assumido — foi **medido antes de escrever código** (s335):

| Prova | Betão | R7 | 7Games |
|---|---|---|---|
| stack da página | Next.js (`__next_f`) | idem | idem |
| conjunto de hosts carregados | idêntico nas três (inclusive o `gtm.<casa>` por subdomínio) | idem | idem |
| `/api/sportsbook/rogue` no bundle | sim | sim | sim |
| mapa de endpoints `v1/betting/*` extraído do bundle | idêntico | idêntico | idêntico |
| rota da tela de histórico | `/account/sports-history` | idem | idem |
| campos do bilhete e da seleção | idênticos | idênticos | idênticos |

Consequência de engenharia: a captura usa o **mesmo `extensor/rg_inject.js`** e o **mesmo `formatTicketRG`**, sem uma linha duplicada. O harness roda as três fixtures pelo mesmo código (`extensor/harness/casos/{r7,betao,7games}.mjs` sobre `harness/rogue.mjs`) — se alguém amarrar o código a um host, fica vermelho.

> **Ao mexer numa das três, confira as outras.** Toda armadilha registrada aqui vale para as irmãs. As amostras se completam: a R7 trouxe a anulada, a aberta, o handicap e o ao vivo; o Betão trouxe o outright de F1 e o futebol.

---

## 2. Modo de ingestão e layout ⭐

### 2.1 Modo de ingestão

- **PRIMÁRIO:** captura por **API** (SharpenUp, `rg_inject.js` + `formatTicketRG`) — modo `texto` no `_MODO_POR_CASA`. A extensão entrega blocos de texto já normalizados a partir do JSON da casa; a IA lê os blocos, não a tela.

  ```
  GET https://r7.bet.br/api/sportsbook/rogue/v1/betsreporting/purchases
      ?status=all&take=<1..100>&skip=<n>&locale=br-pt&fromDate=<ISO>&toDate=<ISO>
      header: authorization: Bearer <JWT da sessão>
  → {"Purchases":[…], "PurchasesCount": <total da janela>}
  ```

- **FALLBACK:** print da tela `Perfil › Histórico de Esportes`. Funciona, e é o que vale para quem não usa a extensão.

**O que o operador precisa fazer uma vez por aba:** abrir `Perfil › Histórico de Esportes` e clicar num filtro de período. É essa busca que o robô aprende — ver §2.4.

### 2.2 Tipo do bilhete declarado

- Localização do rótulo: campo `BetName` do payload (`"Single"`), espelhado no card como "Simples".
- Regra: Simples → categoria do mercado da seleção; múltipla → `Múltipla`. Fórmula de odd: `MASTER_RESULTADO_2026 §7`.

> Na amostra do recon (15 bilhetes desta conta, 27 somando as três casas) **só houve `Single`**: `BetTypeId` 1, `ComboSize` 0 e `NumberOfLines` 1 em 27 de 27, com `AdditionalTickets` vazio em todos. Múltipla, sistema, cashout, freebet e bet builder **não foram observados** — os campos existem no payload, mas nenhum foi exercido. Ver §16.

### 2.3 Layout do bilhete (o card)

De cima para baixo: `Simples` + valor · nome da seleção · badge com a odd + o rótulo do resultado (`GANHA`) · bloco da seleção (mercado, confronto, horário) · `ID:` · `Total aposta:` · `Retorno:` · `Compartilhar`.

O `ID:` do card é o `PurchaseTicketId` e o `Retorno:` é o `CurrentBetBalance` — conferido em 3 cards contra o payload no dia do recon.

### 2.4 A tela é ESTREITA — e é por isso que a captura tem replay ⭐

O histórico abre em **"Últ. 24 horas"** com `take=10`. Os filtros são `Últ. 24 horas · Hoje · Últ. 7 dias · Últ. 30 dias · Personalizado`, e as abas são `Tudo · Apostas Abertas · Apostas Liquidadas`.

Um robô puramente passivo pareceria funcionar (hook ativo, respostas > 0) e entregaria quase nada: no dia do recon, o filtro de 30 dias do Betão devolvia `PurchasesCount: 0` numa conta com 9 bilhetes. O `rg_inject` alarga a janela para 36 meses e pede `status=all`.

---

## 3. ID do bilhete

- Caso: **visível**.
- Formato: numérico de 18 dígitos (`885258522240761856`). Reconhecido pela regex **genérica** do `repository.py` — não precisa de regex por casa.
- Localização: `PurchaseTicketId` no payload; `ID:` no card.
- Nunca vai no output do usuário (é a 11ª coluna interna) — serve para contar, validar e deduplicar.

> `BetTicketId` é sempre `PurchaseTicketId + 1` nos 27 medidos. **A chave é o `PurchaseTicketId`** — é ele que o card mostra e o que o operador consegue conferir.

---

## 4. Data

- Fonte primária: `Selections[].StartEventDate` — a data do **evento**, ISO com `Z` (**UTC**).
- Fallback: `CreationDate` (colocação), também ISO com `Z`.
- Conversão obrigatória para `America/Sao_Paulo` antes de formatar. Sem isso, toda aposta feita depois das 21h sai um dia adiantada.
- Múltipla: data = evento da **perna mais recente** (regra global, `MASTER_OUTPUT_2026 §4`).

> ⚠️ **Em aposta AO VIVO o evento é ANTERIOR à colocação.** Medido no bilhete `874070447485673472` (vôlei): evento 08/08 19:58, colocada 08/08 20:23. Nenhuma checagem pode assumir que a data do evento vem depois da colocação.

---

## 5. Status e Resultado ⭐

> ⚠️ **Esta casa não tem rótulo na API — tem ENUM NUMÉRICO.** O card mostra "GANHA"/"PERDIDA", mas o payload manda só `BetStatusId`. O de-para abaixo foi **provado pelo dinheiro** em 27 de 27 bilhetes das três casas, nunca por leitura de rótulo.

| `BetStatusId` | `CurrentBetBalance` | Card | Nosso código |
|---|---|---|---|
| 0 | `0` — e **sem** `Result` | "Em aberto" | *(vazio — aposta aberta)* |
| 1 | `0` | "PERDIDA" | L |
| 2 | `= stake × odd` | "GANHA" | W |
| 4 | `= stake` exato, `Result: ""` | devolvida | V |

`PurchaseStatusId` acompanha `BetStatusId` em 27/27, mas **os dois sobem crus** no bloco (`Status (API):`) — o dia em que divergirem é exatamente o dia em que isso vai importar.

Conferência financeira (segunda linha de defesa, `MASTER_RESULTADO §5`): `Retorno = 0` → L · `Retorno = Stake` → V · `Retorno > Stake` → W.

**Enum desconhecido não vira W/L por chute.** Sobe como *"a conferir — não liquidar automaticamente"*. Há uma rede por baixo, feita do dinheiro: resolvido + enum desconhecido + retorno **igual à stake** ⇒ devolução ⇒ V. Isso fecha a família inteira em vez de um enum de cada vez; com retorno diferente da stake o desconhecido continua subindo para conferência.

**Gatilho de meia-liquidação (HW/HL):** não observado nesta casa. Não há rótulo nem enum conhecido para meia-liquidação; se aparecer, cairá no ramo "a conferir" e a assinatura financeira exata (`HL → retorno = stake/2` · `HW → retorno = (stake/2) × (odd + 1)`) é quem decide.

Apostas abertas → `extraction_state = aberta` (fora da fila de cópia).

---

## 6. Boost / promoção

- Tem boost: **não observado**. `PromotionIds` vem `[]` em 27 de 27 e `BetOriginalTrueOdds` é igual a `BetTrueOdds` em todos.
- Localizador: `PromotionIds` (lista) e a divergência entre `BetOriginalTrueOdds` e `BetTrueOdds`.
- Comportamento esperado: como a odd de W sai de `Retorno ÷ Stake` (regra global), qualquer boost que apareça é absorvido de graça, sem mudança de código.

<!-- TODO: confirmar o rótulo visual quando houver um bilhete com PromotionIds preenchido. -->

---

## 7. Cashout

- Tem cashout: **sim** — o bundle da casa publica `/v1/cashout/get-info`, `/v1/cashout/place`, `/v1/cashout/get-updates` e `/v1/cashout/place-new-offer`.
- **Nenhum cashout apareceu na amostra**, então não se sabe qual `BetStatusId` ele produz nem em que campo o valor encerrado chega.
- Regra global (vale assim que houver amostra): `Odd = Cashout ÷ Stake`, resultado `W`; se `Cashout = Stake` → `V`, preservando a odd exibida.
- **Distinção de meia-liquidação:** cashout produz retorno arbitrário; HW/HL casam exato com as fórmulas do §5.

<!-- TODO: capturar um cashout e registrar o BetStatusId que ele produz. -->

---

## 8. Bônus

- Tem bônus: **não observado** na amostra. Não há campo de bônus/freebet no payload de `purchases`.
- **Política:** enquanto não houver amostra, nada a tratar — o stake que chega é `TotalStake`, sem distinção de origem.

<!-- TODO: verificar se aposta com bônus muda algum campo do payload. -->

---

## 9. Mapa de mercados (R7 → `Aposta` global)

| R7 exibe (`MarketName` · `EnMarketName`) | Aposta global |
|---|---|
| Vencedor · `FT Winner` | ML |
| Vencedor 2 Vias · `FT Winner 2 Way` | ML |
| Resultado Final · `FT 1X2` | ML |
| Handicap · `FT Spread` | Handicap |
| Handicap de total de pontos - Set 2 Apostas ao Vivo · `2nd Set HC` | Handicap |

> Mercado que apareça e **não** tenha categoria adequada no `MASTER_APOSTAS §3` → `Outros` ⚠️ + registrar no §Feedback. Mercados ainda não vistos **não entram nesta tabela**.

**Notas de reconstrução:**
- O payload traz **duas versões de tudo**: localizada (`MarketName`, `SportName`, `LeagueName`, `EventName`, `SelectionName`) e inglesa (`EnMarketName`, `EnSportName`, …). A localizada é a que o card mostra e a que o `MASTER_APOSTAS` casa; **a inglesa é a chave estável do motor** e sobe junto quando difere — é ela que reconhece o mercado quando a casa muda a tradução.
- Confronto: `EventName` já vem no formato `Time A vs Time B` → `[Time A v Time B]` (padrão global).
- Handicap: a linha já vem **embutida no nome da seleção** (`"Joo Eun Kim -1.5"`) **e** separada em `Points` (`-1.5`). Os dois sobem. ⚠️ `Points: 0` é linha legítima (handicap zero) — testar contra `null`, nunca por *truthy*.
- **Outright/futuro** (`EventTypeId: 8`): `Team1name`/`Team2name` **não são adversários** e montar "A vs B" com eles inventaria um confronto que não existe. Ver `CASA_BETAO §9`, onde há a amostra.

---

## 10. Stake

- Localização: `TotalStake` (número) — é o "Total aposta:" do card. `Stake` traz o mesmo valor como string.
- Formato: número em **reais**, com ponto decimal (`250`, `304`). Não há milésimos (ao contrário da KTO).
- `UnitStake` é o valor **por linha**; igual ao total enquanto não houver sistema.
- Normalização final = global (`MASTER_OUTPUT §11/§16`).

---

## 11. Odds ⭐

- Campo financeiro principal: **`CurrentBetBalance`** — o retorno **realizado**. É o "Retorno:" do card.

> ⚠️ **`Gain` NÃO é o retorno.** É o retorno **POTENCIAL**, e vale `stake × odd` em **27 de 27** bilhetes — inclusive em **perdida** e em **aberta**. O bilhete `885232207148290048` perdeu e o campo segue dizendo 380,00. Quem ler o campo óbvio marca toda perda como ganho: é a vitória fantasma do `totalWin` da VaideBet (s210) e do `finalFinancials.payout` da Novibet (s271), com o terceiro nome de campo. O mesmo vale para `AmountToWin` (o lucro potencial).

| Resultado | Regra da odd |
|---|---|
| W | `CurrentBetBalance ÷ Stake` |
| L | odd **exibida** (`BetClientOdds`) — nunca `0,00` |
| V | odd **exibida** — nunca `1,00` |
| aberta | odd **exibida** |
| Cashout (≠ stake) | `Cashout ÷ Stake` |

> ⚠️ **Aqui isso não é preferência, é a diferença entre a odd certa e lixo.** Em `L` o retorno é 0 e a divisão daria **odd 0** — o zero que faz um bilhete ganho virar −1u (`CLAUDE.md`, "Zero não é ausência"). Em `V` o retorno é a própria stake e a divisão daria **1,00**, apagando a odd real.

- `BetClientOdds` é **string** (`"2.50"`) e preserva a precisão que a casa escreveu; `BetTrueOdds` é o mesmo valor como número. A string é a fonte.
- A divisão reproduz a odd declarada **ao centavo** nesta casa: `1004,64 ÷ 598 = 1,68` exato (bilhete do Betão). Ainda assim a regra do W é global e não se negocia por casa.
- Precisão: preservar — não truncar nem arredondar (global).
- `BetOriginalTrueOdds` ≠ `BetTrueOdds` significa que a casa **revisou** a odd (perna anulada dentro de múltipla, p.ex.). Não observado na amostra; sobe como aviso quando divergir.

---

## 12. Ruído a ignorar

Botão `Compartilhar` · banner de cookies · toast "Bônus disponível" · badge de contagem de mensagens · cronômetro de sessão no topo · sidebar de cassino (`Mais Pagou Hoje`, `Slots`, `Roleta Mágica`, `Cofrinho`) · rodapé institucional.

---

## 13. Pegadinhas (resumo rápido)

- **`Gain` é potencial, sempre.** O retorno real é `CurrentBetBalance`. (§11)
- **O status é enum, não rótulo** — e `bal = 0` é igual em **aberta** e em **perdida**. Só o enum separa os dois. (§5)
- **A tela pede 24h e `take=10`** — captura sem replay nasce quase vazia. (§2.4)
- **`take` tem teto de 100.** Pedir mais devolve corpo de erro (`ErrorCode 2003`), não lista truncada.
- **Cookie não basta:** sem o `authorization: Bearer` da sessão a API responde **403**.
- **Em aposta ao vivo o evento vem ANTES da colocação.** (§4)
- **`Result` tem quatro formas:** ausente (aberta), string vazia (anulada), placar `"0 : 2"` (resolvida) e frase (outright). Nunca assumir formato.
- **`Score1`/`Score2` é o placar NA HORA DA APOSTA** (ao vivo), não o resultado.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18`. Cobrem: resultado oficial (`W/L/V/HW/HL`), odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes. **Não duplicar aqui.**

**Específicas desta casa:**
- Nenhuma linha com `Resultado = W` pode ter `Retorno` igual ao `Gain` de um bilhete cujo `BetStatusId` seja 1 ou 4 — é o sintoma da confusão potencial × realizado.
- Odd `0,00` ou `1,00` numa linha `L`/`V` é defeito: a odd de L e V vem de `BetClientOdds`.
- Bilhete com `BetStatusId` fora de `{0,1,2,4}` não pode sair liquidado sem conferência humana.

---

## 15. Exemplos golden (bilhetes reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**W — simples de badminton** (`885258522240761856`; card: R$250,00 · 2.45 · GANHA · Retorno R$612,50)

```
09/09/2026	Badminton	 	R7	 	ML	[Shogo Ogawa v Rounak Chouhan] Rounak Chouhan	250,00	2,45	W
```

**L — a odd vem da casa, nunca do retorno zero** (`873256991194910720`)

```
07/08/2026	Badminton	 	R7	 	ML	[Y Luo / T G Wang v C-C Lin / C Y Yang] C-C Lin / C Y Yang	200,00	4,57	L
```

**V — anulada: retorno = stake, odd exibida preservada** (`884899595909234688`)

```
08/09/2026	Badminton	 	R7	 	ML	[Mark Shelley Alcala v Ping-Hsien Huang] Mark Shelley Alcala	300,00	3,57	V
```

**Handicap** (`884898849281044480`; `Points: -1.5`)

```
08/09/2026	Badminton	 	R7	 	Handicap	[Yu Chen Han v Joo Eun Kim] Joo Eun Kim -1,5	250,00	1,86	W
```

**Aberta — sem resultado, e o retorno potencial NÃO vira retorno** (`885226164280238080`)

```
09/09/2026	Badminton	 	R7	 	ML	[K Z Pang / Z H Chong v Andersson / Jessen] K Z Pang / Z H Chong	200,00	3,24	
```

---

## 16. O que esta doc NÃO cobre (medido, não esquecido)

A amostra do recon são 15 bilhetes desta conta (27 somando as três casas espelho), e **todos são simples**. Não há, em nenhuma das três:

- múltipla, sistema ou bet builder (`BetTypeId` 1, `ComboSize` 0, `NumberOfLines` 1 em 27/27);
- cashout executado (os endpoints existem; nenhum bilhete passou por eles);
- freebet / bônus;
- meia-liquidação (HW/HL);
- boost (`PromotionIds` vazio em 27/27);
- `BetStatusId` fora de `{0, 1, 2, 4}`.

Quando qualquer um aparecer, a fixture volta para `extensor/harness/fixtures/` e o caso correspondente trava a leitura nova.

---

## Feedback para a camada global / MODELO

1. Nada a propor. Todos os mercados observados casaram com categoria existente do `MASTER_APOSTAS §3`.

---

VERSÃO: 2026
STATUS: ATIVA
CASA: R7
