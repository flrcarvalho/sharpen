# CASA_BETAO
## Camada de tradução — Betão → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades do Betão.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betão` · site: `betao.bet.br`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `CustomerCurrencyCode: "BRL"`
- **Decimal na API: PONTO** (`"3.29"`, `1375`) → normalizar para vírgula na saída.
- Motor: **Rogue** — plataforma própria, servida do **próprio domínio da casa** em `/api/sportsbook/rogue/…`. Não é Altenar/BIA, não é BetBy, não é Kambi, não é BetConstruct.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> A grafia canônica é `Betão`, **com til**, e foi MEDIDA antes de registrar (s335): 44 bilhetes, 5 contas, 3 `casas_meta`, 1 `casa_config` e 17 correções, **todos em `Betão`**, sem nenhuma variante. O round-trip `_casa_display(_display_to_key("Betão"))` fecha em identidade.
>
> ⚠️ A **chave** do `_CASA_DISPLAY` é `BETAO` (sem til) e o **display** é `Betão` (com til). O `content.js` compara o display em minúsculas, então o ramo do robô aceita `"betão"` **e** `"betao"` — aceitar só um lado é o defeito silencioso da Jogo de Ouro (s256), em que a casa não casava ramo nenhum e o robô genérico raspava o rodapé institucional do site como se fossem bilhetes.

### 1.1 Três casas espelho

O Betão é a **mesma casa técnica** que a [`CASA_R7`](CASA_R7.md) e a [`CASA_7GAMES`](CASA_7GAMES.md): mesmo motor, mesmo caminho de API, mesmos nomes de campo, mesmos enums. A prova da irmandade e a consequência de engenharia (um inject, um formatador) estão em [`CASA_R7 §1.1`](CASA_R7.md#11-três-casas-espelho--o-que-isso-significa-na-prática).

> **Ao mexer numa das três, confira as outras.** As amostras se completam: esta conta trouxe o **outright de F1** e o **futebol**; a R7 trouxe a anulada, a aberta, o handicap e o ao vivo.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** captura por **API** (SharpenUp, `rg_inject.js` + `formatTicketRG`) — modo `texto` no `_MODO_POR_CASA`.

  ```
  GET https://betao.bet.br/api/sportsbook/rogue/v1/betsreporting/purchases
      ?status=all&take=<1..100>&skip=<n>&locale=br-pt&fromDate=<ISO>&toDate=<ISO>
      header: authorization: Bearer <JWT da sessão>
  → {"Purchases":[…], "PurchasesCount": <total da janela>}
  ```

- **FALLBACK:** print da tela `Perfil › Histórico de Esportes`.

**O que o operador precisa fazer uma vez por aba:** abrir `Perfil › Histórico de Esportes` e clicar num filtro de período — é essa busca que o robô aprende. Sem ela não há `authorization` para reusar, e a API responde **403**.

### 2.2 Tipo do bilhete declarado

- Localização do rótulo: `BetName` (`"Single"`), espelhado no card como "Simples".
- Regra: Simples → categoria do mercado da seleção; múltipla → `Múltipla`. Fórmula de odd: `MASTER_RESULTADO_2026 §7`.

> Nesta conta (9 bilhetes) só houve `Single`. Ver [`CASA_R7 §16`](CASA_R7.md#16-o-que-esta-doc-não-cobre-medido-não-esquecido) para a lista completa do que as três amostras não cobrem.

### 2.3 Layout do bilhete

Idêntico ao da R7 — ver [`CASA_R7 §2.3`](CASA_R7.md#23-layout-do-bilhete-o-card). O `ID:` do card é o `PurchaseTicketId`; o `Retorno:` é o `CurrentBetBalance`.

### 2.4 A tela é ESTREITA

Abre em **"Últ. 24 horas"** com `take=10`. Foi **nesta conta** que isso ficou visível no recon: o filtro de 30 dias devolvia `{"Purchases":[],"PurchasesCount":0}` numa conta com 9 bilhetes. O `rg_inject` alarga para 36 meses e pede `status=all`.

---

## 3. ID do bilhete

- Caso: **visível**. Numérico de 18 dígitos (`872581186613731328`), campo `PurchaseTicketId`, exibido como `ID:` no card.
- Reconhecido pela regex **genérica** do `repository.py`.
- Nunca vai no output do usuário (11ª coluna interna).

---

## 4. Data

- Fonte primária: `Selections[].StartEventDate` (evento, ISO com `Z` = **UTC**).
- Fallback: `CreationDate` (colocação), também UTC.
- Conversão obrigatória para `America/Sao_Paulo`.
- Múltipla: evento da **perna mais recente** (global).

> ⚠️ O outright de F1 desta conta (`867076991768911872`) tem `StartEventDate` **quatro dias depois** da colocação (colocada 20/07, evento 24/07). Aposta de futuro alarga muito essa distância — e a aposta ao vivo a **inverte** (ver [`CASA_R7 §4`](CASA_R7.md#4-data)).

---

## 5. Status e Resultado

Idêntico às irmãs — o de-para completo, provado pelo dinheiro em 27 de 27, está em [`CASA_R7 §5`](CASA_R7.md#5-status-e-resultado). Resumo:

| `BetStatusId` | `CurrentBetBalance` | Nosso código |
|---|---|---|
| 0 | `0`, sem `Result` | *(vazio — aberta)* |
| 1 | `0` | L |
| 2 | `= stake × odd` | W |
| 4 | `= stake` exato | V |

Esta conta exercitou **só `1` e `2`** (nenhuma aberta, nenhuma anulada no dia do recon).

Apostas abertas → `extraction_state = aberta` (fora da fila de cópia).

---

## 6. Boost / promoção

Não observado — `PromotionIds` vazio em todos os 9 bilhetes. Ver [`CASA_R7 §6`](CASA_R7.md#6-boost--promoção).

---

## 7. Cashout

Endpoints existem no bundle; nenhum cashout na amostra. Ver [`CASA_R7 §7`](CASA_R7.md#7-cashout).

---

## 8. Bônus

Não observado; não há campo de bônus no payload de `purchases`. Ver [`CASA_R7 §8`](CASA_R7.md#8-bônus).

---

## 9. Mapa de mercados (Betão → `Aposta` global)

| Betão exibe (`MarketName` · `EnMarketName`) | Aposta global |
|---|---|
| Vencedor · `FT Winner` | ML |
| Resultado Final · `FT 1X2` | ML |

> Mercado que apareça e **não** tenha categoria adequada no `MASTER_APOSTAS §3` → `Outros` ⚠️ + registrar no §Feedback. Mercados ainda não vistos **não entram nesta tabela**.

**Notas de reconstrução:**
- O payload traz tudo em duas versões (localizada e inglesa) — ver [`CASA_R7 §9`](CASA_R7.md#9-mapa-de-mercados-r7--aposta-global).
- Confronto: `EventName` já vem `Time A vs Time B` → `[Time A v Time B]`.

### 9.1 ⭐ OUTRIGHT / FUTURO — a armadilha desta conta

O bilhete `867076991768911872` (Fórmula 1) é o único da amostra das três casas com `EventTypeId: 8`. Três coisas mudam nele, e as três quebram quem assume o formato do confronto:

- **`EventName` é a PROVA, não um duelo:** `"Formula 1 Hungarian GP 2026 - Podium Finish"`. O recorte real da aposta está aí ("Podium Finish"), não no `MarketName`, que segue dizendo só `"Vencedor"`.
- **`Team1name` / `Team2name` NÃO são adversários.** Vêm `Kimi Antonelli` e `Lewis Hamilton` — dois pilotos quaisquer do grid, e a seleção apostada (`Lando Norris`) não é nenhum dos dois. Montar `[Kimi Antonelli v Lewis Hamilton]` inventaria um confronto que não existe.
- **`Result` é FRASE, não placar:** `"Winner Kimi Antonelli, Max Verstappen, Lando Norris"` — os três do pódio. É ela que explica por que a aposta ganhou.

Regra: com `EventTypeId: 8`, a descrição usa o **nome do evento** e a **seleção**, e nunca um confronto derivado dos dois "times". O `formatTicketRG` marca esses bilhetes com `outright (não é confronto entre dois times)`.

---

## 10. Stake

`TotalStake` (número, em reais, ponto decimal) — o "Total aposta:" do card. Ver [`CASA_R7 §10`](CASA_R7.md#10-stake).

---

## 11. Odds

Regra idêntica à das irmãs — ver [`CASA_R7 §11`](CASA_R7.md#11-odds). Resumo do que não pode ser esquecido:

- **`Gain` é o retorno POTENCIAL**, inclusive em perdida. O realizado é `CurrentBetBalance`.
- W → `CurrentBetBalance ÷ Stake`. L, V e aberta → odd **exibida** (`BetClientOdds`), nunca do dinheiro.

> Foi **nesta conta** que a divisão se provou exata ao centavo: o bilhete `872134288308391936` tem stake 598,00, odd `"1.68"` e `CurrentBetBalance` `"1004.64"` — e `1004,64 ÷ 598 = 1,68` sem sobra.

---

## 12. Ruído a ignorar

Idêntico ao da R7 — ver [`CASA_R7 §12`](CASA_R7.md#12-ruído-a-ignorar).

---

## 13. Pegadinhas (resumo rápido)

- **`Gain` é potencial, sempre.** O retorno real é `CurrentBetBalance`.
- **O status é enum**, e `bal = 0` é igual em aberta e em perdida.
- **A tela pede 24h e `take=10`** — foi aqui que isso apareceu: 30 dias devolviam 0 numa conta com 9 bilhetes.
- **`take` tem teto de 100**; acima disso vem corpo de erro, não lista.
- **Cookie não basta** — sem o Bearer da sessão, 403.
- **Outright quebra o confronto** (§9.1): `Team1name`/`Team2name` não são adversários e `Result` é frase.
- **A chave é `BETAO` mas o display é `Betão`** — o ramo do robô tem de aceitar as duas formas (§1).

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18`. Cobrem: resultado oficial (`W/L/V/HW/HL`), odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes. **Não duplicar aqui.**

**Específicas desta casa:**
- Bilhete com `EventTypeId: 8` não pode gerar descrição no formato `[A v B]` a partir de `Team1name`/`Team2name`.
- Odd `0,00` ou `1,00` numa linha `L`/`V` é defeito (a odd vem de `BetClientOdds`).
- Nenhuma linha `W` pode ter retorno igual ao `Gain` de um bilhete perdido.

---

## 15. Exemplos golden (bilhetes reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**W — futebol, divisão exata ao centavo** (`872134288308391936`)

```
03/08/2026	Futebol	 	Betão	 	ML	[Ferrovalvulas v CD Semillas de Vida y Paz] Ferrovalvulas	598,00	1,68	W
```

**W — outright de F1: o evento é a prova, não um duelo** (`867076991768911872`)

```
24/07/2026	Automobilismo	 	Betão	 	ML	Formula 1 Hungarian GP 2026 - Podium Finish - Lando Norris	399,00	3,5	W
```

**L — a odd vem da casa** (`872581186613731328`)

```
05/08/2026	Badminton	 	Betão	 	ML	[Matsukawa / Nakade v Wong / Cheng] Matsukawa / Nakade	150,00	3,29	L
```

---

## 16. O que esta doc NÃO cobre

Ver [`CASA_R7 §16`](CASA_R7.md#16-o-que-esta-doc-não-cobre-medido-não-esquecido) — a lista vale para as três casas. Nesta conta, além disso, não houve **aberta** nem **anulada**.

---

## Feedback para a camada global / MODELO

1. Nada a propor. Todos os mercados observados casaram com categoria existente do `MASTER_APOSTAS §3`.

---

VERSÃO: 2026
STATUS: ATIVA
CASA: Betão
