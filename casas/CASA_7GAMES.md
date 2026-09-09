# CASA_7GAMES
## Camada de tradução — 7Games → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da 7Games.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `7Games` · site: `7games.bet.br`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `CustomerCurrencyCode: "BRL"`
- **Decimal na API: PONTO** (`"1.84"`, `368`) → normalizar para vírgula na saída.
- Motor: **Rogue** — plataforma própria, servida do **próprio domínio da casa** em `/api/sportsbook/rogue/…`. Não é Altenar/BIA, não é BetBy, não é Kambi, não é BetConstruct.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> A grafia canônica é `7Games` e foi MEDIDA antes de registrar (s335): 7 bilhetes (donos `sohprops` e `Jaao26`), 2 contas, 1 `casas_meta` e 2 correções, **todos em `7Games`**, sem nenhuma variante.
>
> ⚠️ **O nome começa com dígito**, e isso importa em dois lugares: a chave do `_CASA_DISPLAY` é `7GAMES` (válida, mas o mapa de autodiagnóstico do `content.js` precisa dela **entre aspas** — `"7games":`, como já acontece com `"1xbet"`), e o slug em minúsculas é `7games`.

### 1.1 Três casas espelho

A 7Games é a **mesma casa técnica** que a [`CASA_R7`](CASA_R7.md) e o [`CASA_BETAO`](CASA_BETAO.md): mesmo motor, mesmo caminho de API, mesmos nomes de campo, mesmos enums. A prova da irmandade e a consequência de engenharia (um inject, um formatador) estão em [`CASA_R7 §1.1`](CASA_R7.md#11-três-casas-espelho--o-que-isso-significa-na-prática).

Esta é a conta **menor** das três (3 bilhetes), e o caso dela no harness existe justamente por isso: é a **prova do espelho**. Os três bilhetes passam pelo mesmo inject e pelo mesmo formatador das irmãs, com o host como única diferença — é essa passagem que impede alguém de "ajustar" o código para uma casa e quebrar as outras duas sem perceber.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** captura por **API** (SharpenUp, `rg_inject.js` + `formatTicketRG`) — modo `texto` no `_MODO_POR_CASA`.

  ```
  GET https://7games.bet.br/api/sportsbook/rogue/v1/betsreporting/purchases
      ?status=all&take=<1..100>&skip=<n>&locale=br-pt&fromDate=<ISO>&toDate=<ISO>
      header: authorization: Bearer <JWT da sessão>
  → {"Purchases":[…], "PurchasesCount": <total da janela>}
  ```

- **FALLBACK:** print da tela `Perfil › Histórico de Esportes`.

**O que o operador precisa fazer uma vez por aba:** abrir `Perfil › Histórico de Esportes` e clicar num filtro de período — é essa busca que o robô aprende. Sem ela não há `authorization` para reusar, e a API responde **403**.

### 2.2 Tipo do bilhete declarado

- Localização do rótulo: `BetName` (`"Single"`).
- Regra: Simples → categoria do mercado da seleção; múltipla → `Múltipla`. Fórmula de odd: `MASTER_RESULTADO_2026 §7`.

> Nesta conta (3 bilhetes) só houve `Single`. Ver [`CASA_R7 §16`](CASA_R7.md#16-o-que-esta-doc-não-cobre-medido-não-esquecido).

### 2.3 Layout do bilhete

Idêntico ao das irmãs — ver [`CASA_R7 §2.3`](CASA_R7.md#23-layout-do-bilhete-o-card).

### 2.4 A tela é ESTREITA

Abre em **"Últ. 24 horas"** com `take=10`. O `rg_inject` alarga para 36 meses e pede `status=all`. Ver [`CASA_R7 §2.4`](CASA_R7.md#24-a-tela-é-estreita--e-é-por-isso-que-a-captura-tem-replay).

---

## 3. ID do bilhete

- Caso: **visível**. Numérico de 18 dígitos (`885255718436737024`), campo `PurchaseTicketId`, exibido como `ID:` no card.
- Reconhecido pela regex **genérica** do `repository.py`.
- Nunca vai no output do usuário (11ª coluna interna).

> ⚠️ **O espaço de IDs é COMPARTILHADO entre as três casas espelho** — os ids são sequenciais por instante de criação no motor, não por casa. O bilhete `885255718436737024` desta conta e o `885255808819798016` da R7 nasceram com 22 segundos de diferença. Isso **não** cria colisão de dedup (`casa` entra na assinatura, `repository._assinatura`), mas significa que um id sozinho **não identifica a casa** — nunca deduzir a casa a partir do código.

---

## 4. Data

- Fonte primária: `Selections[].StartEventDate` (evento, ISO com `Z` = **UTC**).
- Fallback: `CreationDate` (colocação), também UTC.
- Conversão obrigatória para `America/Sao_Paulo`.
- Múltipla: evento da **perna mais recente** (global).

---

## 5. Status e Resultado

Idêntico às irmãs — o de-para completo, provado pelo dinheiro em 27 de 27, está em [`CASA_R7 §5`](CASA_R7.md#5-status-e-resultado). Resumo:

| `BetStatusId` | `CurrentBetBalance` | Nosso código |
|---|---|---|
| 0 | `0`, sem `Result` | *(vazio — aberta)* |
| 1 | `0` | L |
| 2 | `= stake × odd` | W |
| 4 | `= stake` exato | V |

Esta conta exercitou `0`, `1` e `2` — um de cada. Não houve anulada.

Apostas abertas → `extraction_state = aberta` (fora da fila de cópia).

---

## 6. Boost / promoção

Não observado — `PromotionIds` vazio nos 3 bilhetes. Ver [`CASA_R7 §6`](CASA_R7.md#6-boost--promoção).

---

## 7. Cashout

Endpoints existem no bundle; nenhum cashout na amostra. Ver [`CASA_R7 §7`](CASA_R7.md#7-cashout).

---

## 8. Bônus

Não observado; não há campo de bônus no payload de `purchases`. Ver [`CASA_R7 §8`](CASA_R7.md#8-bônus).

---

## 9. Mapa de mercados (7Games → `Aposta` global)

| 7Games exibe (`MarketName` · `EnMarketName`) | Aposta global |
|---|---|
| Vencedor · `FT Winner` | ML |

> Mercado que apareça e **não** tenha categoria adequada no `MASTER_APOSTAS §3` → `Outros` ⚠️ + registrar no §Feedback. Mercados ainda não vistos **não entram nesta tabela**.

**Notas de reconstrução:**
- O payload traz tudo em duas versões (localizada e inglesa) — ver [`CASA_R7 §9`](CASA_R7.md#9-mapa-de-mercados-r7--aposta-global).
- Confronto: `EventName` já vem `Time A vs Time B` → `[Time A v Time B]`.
- Handicap e outright não apareceram nesta conta; as regras estão em [`CASA_R7 §9`](CASA_R7.md#9-mapa-de-mercados-r7--aposta-global) e [`CASA_BETAO §9.1`](CASA_BETAO.md#91--outright--futuro--a-armadilha-desta-conta).

---

## 10. Stake

`TotalStake` (número, em reais, ponto decimal) — o "Total aposta:" do card. Ver [`CASA_R7 §10`](CASA_R7.md#10-stake).

---

## 11. Odds

Regra idêntica à das irmãs — ver [`CASA_R7 §11`](CASA_R7.md#11-odds). O que não pode ser esquecido:

- **`Gain` é o retorno POTENCIAL**, inclusive em perdida e em aberta. O realizado é `CurrentBetBalance`.
- W → `CurrentBetBalance ÷ Stake`. L, V e aberta → odd **exibida** (`BetClientOdds`), nunca do dinheiro.

> A aberta desta conta (`885232553773772800`) é o exemplar mais limpo da armadilha: `Gain` diz **518,00** e `CurrentBetBalance` diz **"0"**. Emitir o primeiro como retorno liquidaria uma aposta que ainda está correndo.

---

## 12. Ruído a ignorar

Idêntico ao das irmãs — ver [`CASA_R7 §12`](CASA_R7.md#12-ruído-a-ignorar).

---

## 13. Pegadinhas (resumo rápido)

- **`Gain` é potencial, sempre** — e é aqui que a aberta mostra isso mais claramente (§11).
- **O status é enum**, e `bal = 0` é igual em aberta e em perdida.
- **A tela pede 24h e `take=10`**; `take` tem teto de 100.
- **Cookie não basta** — sem o Bearer da sessão, 403.
- **O id NÃO identifica a casa** (§3): as três espelho compartilham o espaço de ids.
- **O nome começa com dígito** — a chave precisa de aspas no mapa de autodiagnóstico (§1).

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18`. Cobrem: resultado oficial (`W/L/V/HW/HL`), odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes. **Não duplicar aqui.**

**Específicas desta casa:**
- Nenhuma linha de bilhete aberto pode trazer `Retorno` preenchido — o campo que existe ali é o potencial.
- Odd `0,00` ou `1,00` numa linha `L`/`V` é defeito (a odd vem de `BetClientOdds`).
- A casa de um bilhete nunca pode ser inferida do `codigo_bilhete` (§3).

---

## 15. Exemplos golden (bilhetes reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**W — simples de badminton** (`885255718436737024`)

```
09/09/2026	Badminton	 	7Games	 	ML	[Ching Ping Huang v Ciou-Tong Tung] Ching Ping Huang	200,00	1,84	W
```

**L — a odd vem da casa** (`885232207148290048`)

```
09/09/2026	Badminton	 	7Games	 	ML	[Harper / Tang v Axelsson / Hallberg] Axelsson / Hallberg	200,00	1,9	L
```

**Aberta — o `Gain` de 518,00 é POTENCIAL e não vira retorno** (`885232553773772800`)

```
09/09/2026	Badminton	 	7Games	 	ML	[Panev / Stoyanov v Kenny / Taylor] Kenny / Taylor	200,00	2,59	
```

---

## 16. O que esta doc NÃO cobre

Ver [`CASA_R7 §16`](CASA_R7.md#16-o-que-esta-doc-não-cobre-medido-não-esquecido) — a lista vale para as três casas. Nesta conta, além disso, não houve **anulada**, **handicap** nem **outright**.

---

## Feedback para a camada global / MODELO

1. Nada a propor. Todos os mercados observados casaram com categoria existente do `MASTER_APOSTAS §3`.

---

VERSÃO: 2026
STATUS: ATIVA
CASA: 7Games
