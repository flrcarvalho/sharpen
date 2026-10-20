# CASA_JACK
## Camada de tradução — Jack → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Jack.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> ⚠ **Corpo HERDADO da [`CASA_MYSTAKE`](CASA_MYSTAKE.md)** (s424, 20/10/2026). A Jack entrou
> sem conta e sem bilhete: tudo abaixo que não está em §1 é a leitura da MyStake, que roda o
> mesmo motor. A 1ª captura real é o recon (§16): o que ela desmentir sai daqui.

---

## 1. Identidade

- Casa canônica: `Jack` · site: `jack.com` (sportsbook em `/br/sportsbook`, o mesmo caminho da MyStake). Marca na tela: "Jack Casino".
- Domínio registrado: `jack.com`. `www.jack.com` responde 301 para a raiz.
- Grafia **medida na base** antes do registro: `Jack` em `parceiros` e `casas_meta` (1 conta do Gabriel, nenhum bilhete), nenhuma variante.
- **Fora do `.bet.br`**: a casa não é regulada no Brasil. Site atrás do desafio Cloudflare (curl recebe 403 `cf-mitigated: challenge`).
- Locale: pt-BR (`/br`). Moeda: **não medida** (cassino cripto; a MyStake manda `CurrencySTR` por bilhete, e a Ficha lê a moeda do cru).
- Motor: **BetConstruct** (sportsbook v4) — o mesmo da [`CASA_MYSTAKE`](CASA_MYSTAKE.md), [`CASA_TIVO`](CASA_TIVO.md), [`CASA_BETFAST`](CASA_BETFAST.md) e [`CASA_FAZ1BET`](CASA_FAZ1BET.md).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

### 1.1 Quinta casa do mesmo motor — provado por fora, sem conta

| Prova (aba de `jack.com`, Chrome, 20/10/2026) | Resultado |
|---|---|
| `POST /api/game/p/messagetosport` | **401** (a rota existe e pede sessão) |
| `POST /api/game/p/<rota falsa>` | **404** |
| `/br/sportsbook` | 200 |

É a mesma prova que registrou a MyStake na s392 (401 contra 404 no gateway). **Não provado:**
o `gethistory` logado, o `Company` (id da casa dentro do motor) e o conjunto de chaves da
resposta. Consequência de engenharia: **mesmo `extensor/tv_inject.js`, mesmo `formatTicketTV`**.

> **Ao mexer numa das cinco, confira as outras.**

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

**Captura por API** (SharpenUp · `tv_inject.js`), herdada da MyStake (`CASA_MYSTAKE §2.1`):
a mesma URL serve polling (o `messagetosport` pequeno de saldo é ignorado pela forma da
resposta) e o histórico vem inteiro, com `Count`, sem paginação.

### 2.2 Tipo do bilhete declarado

Herdado: a coluna "Tipo" diz `Expresso` para múltipla; o nº de seleções vem de `Items.length`.

### 2.3 Layout do bilhete

Não medido. Na MyStake é lista tabular sem linha em branco entre bilhetes: **nunca robô de texto**.

---

## 2.5 Campos da API (o que o inject entrega)

Herdados da `CASA_MYSTAKE §2.5` (`TicketType` 3 = freebet, `Items[].Result` 6 = meia derrota,
`FinalPosition.hisminus`, `RiskBonusPercent`). Conferir na 1ª captura (§16).

---

## 3. ID do bilhete

- Esperado: **numérico, 9 dígitos**, como as irmãs. O `CODIGO_EXEMPLO` do `audit_sharpenup` usa
  um id **emprestado** da MyStake até o 1º id real da Jack.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`). A dedup é por (casa, parceiro, código).

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da perna mais recente** (`MASTER_OUTPUT §4`):
`Items[].Game.StartTime`, a mais recente; nunca o `ActionTime` (colocação).

---

## 5. Status e Resultado

De-para do bilhete herdado das irmãs (`CASA_FAZ1BET §5`, `CASA_MYSTAKE §5`). `Result 6` da perna
= meia derrota; o P/L vem do bilhete, e em simples quem decide `HL` é o dinheiro.

---

## 6. Boost / promoção

Herdado da `CASA_MYSTAKE §6`: `RiskBonusPercent` é bônus de odd pago sobre o LUCRO da ganha,
fora do `WinAmount`. `retorno = WinAmount + (WinAmount − Amount) × pct`, ao centavo, metade
para cima; `odd = retorno ÷ Amount`. **Sem amostra na Jack.**

---

## 7. Cashout

Vale a regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`). Sem amostra.

---

## 8. Bônus e FREEBET

Herdado da `CASA_MYSTAKE §8`: `TicketType 3` = aposta inteira com freebet, o bloco emite
`Freebet incluído: <valor>` e o `Stake:` continua cheio. Na MyStake o `WinAmount` da freebet
ganha já é só o lucro (s424: 45 × 9,54 − 45 = 384,30). `IsBonus` não é freebet.

---

## 9. Mapa de mercados (Jack → `Aposta` global)

Sem mercado confirmado no dado desta casa. Até a 1ª captura vale o `CASA_MYSTAKE §9` (espelho
compartilha código, **não** dicionário: o recorte `1ª metade` da MyStake não é o `1º metade`
da Faz1bet).

---

## 10. Stake

- Origem: `Amount`. Em freebet, `Amount` é o valor da freebet (§8).
- ⚠ **Não** usar `CalculatedBetAmount` (rateio por perna).

---

## 11. Odds

- Origem: `Koef`, **precisão completa** (na ganha, `WinKoef`). A tela das irmãs trunca em 2 casas: nunca ler a odd do card.

---

## 12. Ruído a ignorar

Mesmo conjunto das irmãs (`CASA_MYSTAKE §12`): placeholder `{p1_r}`, `Team1Score`/`Team2Score`, `CalculatedBetAmount`, `Price`, `Company`, `Player.*`. ⚠ `hisminus: true` inverte o sinal da linha.

---

## 13. Pegadinhas (resumo rápido, herdadas das irmãs)

- **"F" = freebet = `TicketType 3`**, e `IsBonus` continua `false`.
- **`Result 6` = meia derrota.**
- `hisminus: true` → sinal da linha invertido na tela.
- Odd: a tela trunca → sempre `Koef`.
- **"+N%" na Quantia = `RiskBonusPercent`**, fora do `WinAmount`.
- `messagetosport` pequeno a cada poucos segundos é polling, não histórico.

---

## 14. Validações específicas

> **Transversais:** `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`.

- Coluna Data = evento mais recente.
- Odd com precisão completa, decimal com vírgula.

---

## 15. Exemplos golden (bilhetes reais)

<!-- TODO: a Jack entrou na s424 sem conta. A regressão da captura roda a fixture EMPRESTADA da
     MyStake pelo host da Jack (`extensor/harness/casos/jack.mjs`). Preencher com o 1º lote. -->

---

## 16. O que falta medir (a 1ª captura real é o recon)

1. **O `gethistory` logado:** mesma forma `{Error, Tickets, Count}` e o `Company` da Jack.
2. **A moeda** (`CurrencySTR`) e se a conta é BRL ou cripto: a Caixa e o P/L seguem a moeda do cru.
3. **O código** (9 dígitos?) e o card: trocar o `CODIGO_EXEMPLO` emprestado pelo id real.
4. **Os rótulos de mercado** do tenant, para o §9 e o dicionário da Ficha.
5. Conferir contagem, datas, odds e código do lote contra o card.

---

VERSÃO: 2026
STATUS: REGISTRADA SEM CONTA (5ª casa do motor BetConstruct, espelho da MyStake) · **captura ponta a ponta não rodada** · corpo herdado da MyStake · golden a preencher (§15)
CASA: Jack
