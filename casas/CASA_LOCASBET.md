# CASA_LOCASBET
## Camada de tradução — Locasbet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Locasbet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> ⚠ **Corpo HERDADO da [`CASA_MYSTAKE`](CASA_MYSTAKE.md)** (s437, 01/11/2026). A Locasbet entrou
> sem conta na nossa mão, como a [`CASA_JACK`](CASA_JACK.md): tudo abaixo que não está em §1 é a
> leitura da MyStake, que roda o mesmo motor. A 1ª captura real é o recon (§16): o que ela
> desmentir sai daqui.

---

## 1. Identidade

- Casa canônica: `Locasbet` (grafia decidida pelo Feca, s437) · marca na tela: "Locasbet".
- Grafia **medida na base** antes do registro: `Locas.bet` em `parceiros` e `casas_meta` (1 conta
  do Gabriel, `gfatuch@gmail.com [Fatuch]`, criada em 29/10/2026, moeda `USDT`, nenhum bilhete).
  O `_norm_casa` **não** tira o ponto, então `Locas.bet` e `Locasbet` seriam duas casas: a linha
  `"Locas.bet": "Locasbet"` foi acrescentada ao `scripts/unificar_casas.py` (relatório: 1 conta,
  1 `casas_meta`, 0 bilhetes, 0 colisão). **Rodar `--aplicar` é o que liga a conta à captura.**
- **Domínios.** `locas.bet` é o fixo da marca (200, o domínio que o Gabriel cadastrou). O espelho
  `locasbetNN.com` **troca o número**: em 01/11/2026 o link do Feca era `locasbet12.com`, e
  responderam também `13`, `14` e a raiz `locasbet.com` (403 de fora). Do 1 ao 11 e do 15 ao 20,
  nada. Registrados: `locas.bet`, `locasbet.com` e `locasbet12.com` a `locasbet20.com` (o 15 ao
  20 adiantados). **Número novo fora da lista:** acrescentar em `app/captura.py`
  (`_HOSTS_POR_CASA`), `extensor/manifest.json` e `extensor/popup.js` (`CASA_HOSTS`), e subir
  a versão. Sem isso a extensão não injeta e o popup diz "hook não rodou", sem outro erro.
- Sportsbook em `/en/sportsbook` pela navegação do site. Carregado direto, o `/en/sportsbook`
  responde 404 do IIS: a rota é do aplicativo, não do servidor. Abrir pela home.
- **Fora do `.bet.br`**: a casa não é regulada no Brasil.
- Moeda: **não medida** no bilhete. A conta do Gabriel está cadastrada em `USDT`; a família manda
  `CurrencySTR` por bilhete e o `formatTicketTV` já respeita moeda fora do real (s436, GoldenBet).
- Motor: **BetConstruct** (sportsbook v4) — o mesmo da [`CASA_MYSTAKE`](CASA_MYSTAKE.md),
  [`CASA_GOLDENBET`](CASA_GOLDENBET.md), [`CASA_JACK`](CASA_JACK.md), [`CASA_TIVO`](CASA_TIVO.md),
  [`CASA_BETFAST`](CASA_BETFAST.md) e [`CASA_FAZ1BET`](CASA_FAZ1BET.md).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

### 1.1 Sétima casa do mesmo motor — provado por fora, sem conta

| Prova (Chrome na aba de `locasbet12.com` e curl em `locas.bet`, 01/11/2026) | Resultado |
|---|---|
| `POST /api/game/p/messagetosport` | **401** nos dois (a rota existe e pede sessão) |
| `POST /api/game/p/<rota falsa>` | **404** nos dois |
| `scripts/common/helpers.js` (quem dispara o histórico na MyStake, `CASA_MYSTAKE §1`) | presente, **mesmo hash de versão** nos dois domínios |

É a mesma prova que registrou a MyStake (s392) e a Jack (s424). **Não provado:** o `gethistory`
logado, o `Company` (id da casa dentro do motor) e o conjunto de chaves da resposta.
Consequência de engenharia: **mesmo `extensor/tv_inject.js`, mesmo `formatTicketTV`**.

> **Ao mexer numa das sete, confira as outras.**

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
`FinalPosition.hisminus`, `RiskBonusPercent`, `CurrencySTR`). Conferir na 1ª captura (§16).

---

## 3. ID do bilhete

- Esperado: **numérico, 9 dígitos**, como as irmãs. O `CODIGO_EXEMPLO` do `audit_sharpenup` usa
  um id **emprestado** da MyStake até o 1º id real da Locasbet.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`). A dedup é por (casa, parceiro, código).

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da perna mais recente** (`MASTER_OUTPUT §4`):
`Items[].Game.StartTime`, a mais recente; nunca o `ActionTime` (colocação). Em conta fora do
real, o `ActionTime` só entra como carimbo de colocação (dia da cotação), como na GoldenBet.

---

## 5. Status e Resultado

De-para do bilhete herdado das irmãs (`CASA_FAZ1BET §5`, `CASA_MYSTAKE §5`). `Result 6` da perna
= meia derrota; o P/L vem do bilhete, e em simples quem decide `HL` é o dinheiro.

---

## 6. Boost / promoção

Herdado da `CASA_MYSTAKE §6`: `RiskBonusPercent` é bônus de odd pago sobre o LUCRO da ganha,
fora do `WinAmount`. `retorno = WinAmount + (WinAmount − Amount) × pct`, ao centavo, metade
para cima; `odd = retorno ÷ Amount`. **Sem amostra na Locasbet.**

---

## 7. Cashout

Vale a regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`). Sem amostra.

---

## 8. Bônus e FREEBET

Herdado da `CASA_MYSTAKE §8`: `TicketType 3` = aposta inteira com freebet, o bloco emite
`Freebet incluído: <valor>` e o `Stake:` continua cheio. `IsBonus` não é freebet.

---

## 9. Mapa de mercados (Locasbet → `Aposta` global)

Sem mercado confirmado no dado desta casa. Até a 1ª captura vale o `CASA_MYSTAKE §9` (espelho
compartilha código, **não** dicionário).

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

## 13. Pegadinhas (resumo rápido)

- **Domínio que roda o número** (§1): casa que "parou de capturar" depois de trocar de link é,
  antes de tudo, número fora do manifest.
- **"F" = freebet = `TicketType 3`**, e `IsBonus` continua `false`.
- **`Result 6` = meia derrota.**
- `hisminus: true` → sinal da linha invertido na tela.
- Odd: a tela trunca → sempre `Koef`.
- `messagetosport` pequeno a cada poucos segundos é polling, não histórico.

---

## 14. Validações específicas

> **Transversais:** `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`.

- Coluna Data = evento mais recente.
- Odd com precisão completa, decimal com vírgula.

---

## 15. Exemplos golden (bilhetes reais)

<!-- TODO: a Locasbet entrou na s437 sem conta. A regressão da captura roda a fixture EMPRESTADA
     da MyStake pelos hosts da Locasbet (`extensor/harness/casos/locasbet.mjs`). Preencher com o
     1º lote. -->

---

## 16. O que falta medir (a 1ª captura real é o recon)

0. **Antes:** `python scripts/unificar_casas.py --aplicar` (conta `Locas.bet` → `Locasbet`) e
   Ctrl+Shift+R no painel e na aba da casa.
1. **O `gethistory` logado:** mesma forma `{Error, Tickets, Count}` e o `Company` da Locasbet.
2. **A moeda** (`CurrencySTR`): a conta está cadastrada em `USDT`; conferir se o bilhete diz o mesmo.
3. **O código** (9 dígitos?) e o card: trocar o `CODIGO_EXEMPLO` emprestado pelo id real.
4. **Os rótulos de mercado** do tenant, para o §9 e o dicionário da Ficha.
5. Conferir contagem, datas, odds e código do lote contra o card.
6. Se o popup disser "hook ATIVO · respostas 0" com o histórico aberto, o caminho da API é outro.

---

VERSÃO: 2026
STATUS: REGISTRADA SEM CONTA (7ª casa do motor BetConstruct, espelho da MyStake) · **captura ponta a ponta não rodada** · corpo herdado da MyStake · golden a preencher (§15)
CASA: Locasbet
