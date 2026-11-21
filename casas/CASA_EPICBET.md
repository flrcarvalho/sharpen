# CASA_EPICBET
## Camada de tradução — Epicbet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Epicbet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Epicbet` · site: `epicbet.com` · apostas no painel **My Bets** (botão
  "MY BETS" no rodapé, abas **Pending** e **Settled**).
- Locale: o site em inglês (`/en/`). Mercado, seleção e esporte vêm em **inglês**
  (`Goals Handicap`, `Match Total Points`, `Football`); times verbatim.
- Moeda: **a da conta** (`bet.currency`). A conta do recon é **USDT**; o bloco leva
  `Moeda: USDT` e o carimbo de colocação, e quem converte é o servidor.
- Plataforma **PRÓPRIA**, API **tRPC** em `/s/sport-bet/user/*` no mesmo domínio. Não é Altenar,
  Kambi, BetBy nem BetConstruct. Família `eb` (inject `eb_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s462):** `Epicbet`, a da base. Medido em 21/11/2026: 10 bilhetes (Gabriel, por
> print), 1 conta, 10 `correcoes`, 4 `uso_tokens`, uma grafia só em `bilhetes`/`parceiros`.
> O `casas_meta` tem também uma linha `Epic` (domínio `epicbet.com`), que não grava bilhete.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API, busca ativa** (SharpenUp · `extensor/eb_inject.js`).

```
GET https://epicbet.com/s/sport-bet/user/ticket.listWithMatchInfo?input=<JSON>   (só o cookie)
    input = {"limit": 25, "offset": N, "language": "en", "filter": "pending" | "settled"}
→ { "result": { "data": { "tickets": [ … ], "count": N } } }
```

Medido no recon de 21/11/2026 (Chrome do Feca):

- **Só o cookie da sessão basta**: `fetch` cru, sem header, devolve 200.
- O painel pede **3 por página** e anda por botões (1-2-3-4): ele nunca baixa a lista inteira.
  O inject pede as duas listas de 25 em 25.
- ⚠️ **`limit` máximo 25** (com 50 a API devolve 400 `too_big`).
- ⚠️ **`filter` obrigatório**, só `pending` ou `settled` (sem ele, ou com `all`, 400
  `invalid_union`).
- **Fim = `count`.** Offset além do fim devolve `tickets: []` (não repete a página 1).
- Ordem: da colocação mais nova para a mais velha.
- A CSP não restringe `connect-src`: no recon, o JSON saiu por receptor local (127.0.0.1).

### 2.3 Layout do bilhete (card)

Card com `EPIC · ID: <n>`, tipo (`COMBO 3`) e rótulo **WON / LOST** (pendente sem rótulo); cada
perna com seleção + linha, odd, mercado + linha, jogo, `Mmm dd, hh:mm / Liga` (Brasília) e o
placar; no rodapé **Odds**, **Stake** e **Payout**. O agrupamento é pelo dia da colocação
(Brasília). Perna com marca própria: "Half Won", "Pushed".

- ⚠️ **Payout = stake × Odds** em toda situação: o potencial na aberta, o pago na ganha, 0 na perdida.
- ⚠️ A **Odds** do card já é a efetiva (§11).

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Epicbet |
|---|---|
| `sequence` | o **"ID" do card** (1, 2, 3… por conta) → `[Código:]` |
| `bet.id` | id interno (8 dígitos, `39939822`). Sobe como `ID interno (bet.id)`, nunca no marcador |
| `type` | `combo` em toda a amostra |
| `createdAt` | colocação, ISO **UTC** |
| `bet.status` | `pending` · `won` · `lost` na amostra. O filtro da casa lista também `partially_won`, `cashed out`, `campaign settled` |
| `bet.stake` · `bet.odds` | número, sem milésimos. **`odds` é a efetiva** (§11) |
| `bet.currency` | `USDT` |
| `bet.oddsBoost` | `null` em toda a amostra |
| `bet.cashouts[]` | vazio em toda a amostra; `ticket.cashout` traz a cotação ao vivo da aberta (não entra) |
| `bet.walletTransactions[].walletId` | identificador da carteira: **anonimizado** na fixture; não entra |
| `bet.selections[]` | `status`, `odds`, `product` (`pre_match`), `selectionInfo` (`matchName`, `leagueName`, `marketName`, `marketLine`, `outcomeName`, `outcomeLine`, `matchStart` UTC, `betBuilderSelectionInfo`), `matchScoreInfo.sportEntityName` |
| `selections[].status` | `pending` · `won` · `lost` · `pushed` · `half_won` |
| retorno | **não existe campo**. O Payout do card é `stake × odds` |

**Ficha (s462):** adaptador `app/adaptadores/eb.py`, gate `tests/test_adaptador_eb.py`. A Ficha
aceita aberta, ganha (toda perna `won`) e perdida (com perna perdida), e recusa o resto, que vai à
IA pelo texto. Medido na fixture: **13 de 13 aceitas** (2 abertas, 2 ganhas, 9 perdidas).

---

## 3. ID do bilhete

`sequence` (o "ID" do card), numérico curto, por conta. Os 10 bilhetes que a base já tinha (por
print, Gabriel) usam o mesmo número (códigos 1 a 10); com o `bet.id` cada um deles viraria
duplicata. Não colide entre contas: a assinatura leva `casa` e `parceiro`.

---

## 4. Data

- **Coluna Data = dia do EVENTO em Brasília** (`matchStart` UTC → São Paulo). O card mostra
  as pernas em Brasília: `2026-11-20T02:00:00Z` aparece como "Nov 19, 23:00".
- O bloco também leva a colocação (`createdAt`); o card só mostra o dia dela.

---

## 5. Status e Resultado

| `bet.status` · pernas | Leitura | Código |
|---|---|---|
| `pending` | Em aberto | *(vazio — não liquidar)* |
| `won` · toda perna `won` · sem cashout/boost | Ganhou, retorno = stake × odd (o Payout do card) | `W` |
| `lost` · ao menos uma perna `lost`/`half_lost` | Perdeu | `L`, odd do card |
| `won` com perna `pushed`/`half_won` | sem amostra liquidada | *(a conferir)* |
| cashout, boost, `void`, `cashed out`, `partially_won`, `campaign settled`, status novo | sobe cru | *(a conferir)* |

O bloco sempre leva `Status (API): status … · type …`. Medido: `pending` 2, `won` 2, `lost` 9.

---

## 6. Boost / promoção

Campo `bet.oddsBoost` (`null` na amostra). Turbinada sobe **a conferir** com a linha `Boost:` e a
Ficha recusa, até haver fixture.

---

## 7. Cashout

O painel mostra "Available Cashout" e cada aberta tem a cotação (`ticket.cashout`). Nenhuma
aposta encerrada por cashout na amostra: `bet.cashouts[]` não vazio sobe **a conferir** e a Ficha
recusa.

---

## 8. Bônus

Sem campo de freebet medido. O filtro "campaign settled" sugere liquidação por campanha: sobe a
conferir (`MASTER_RESULTADO §5.8` decide o resto quando houver amostra).

---

## 9. Mapa de mercados (Epicbet → `Aposta` global)

Mercados vistos na amostra (`Money Line`, `1x2`, `1X2 (60min)`, `Goals Handicap`, `Match
Handicap`, `Point Spread`, `Puck Line (60min)`, `Match Total Goals`, `Match Total Points`,
`Total Goals (60min)`, `1. Set Total Games`, `Match Set Handicap`, `Corners 1x2`, `Player Shots
on Goal`, `Draw No Bet`): a categoria sai do `MASTER_APOSTAS` pelo objeto medido, sem atalho
aqui. `(60min)` = tempo regulamentar do hóquei.

---

## 10. Stake

`bet.stake`, na moeda da conta.

---

## 11. Odds

- **A odd é `bet.odds`, a do card, já EFETIVA.** Perna `pushed` e `half_won` entram
  recalculadas pela casa: ID 12 (aberta, perna pushed @1,97) card **6.14**, produto das pernas
  12,10; ID 7 (perdida, perna half_won @2,53) card **5.87** = (2,53+1)/2 × 1,87 × 1,78.
  **Nunca** o produto das pernas.
- **W:** retorno = stake × odd (não há outro retorno publicado).
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `bet.id` (sobe só para conferência), `matchId`, `marketId`, `outcomeId`, `leagueId`,
  `homeTeamId`/`awayTeamId`, `walletTransactions`, `ticketExtras`, `statProgress`,
  `streamingPermissions`, `marketInfo` (texto de regra do mercado), `ticket.cashout` (cotação ao vivo).

---

## 13. Pegadinhas (resumo rápido)

1. **Sem campo de retorno**: Payout = stake × Odds (§2.3).
2. **`odds` já efetiva** com push/meia (§11).
3. **O código é o `sequence`**, não o `bet.id` (§3).
4. **`limit` ≤ 25 e `filter` obrigatório** (§2.1).
5. **Moeda da conta** (USDT), não real (§1).

---

## 14. Validações específicas

- [ ] Nenhuma aberta liquidada; potencial só na aberta.
- [ ] Coluna Data = evento em São Paulo.
- [ ] Odd do ID 7 = 5,87 (nunca 8,42).
- [ ] **1ª captura do Gabriel:** os códigos 1 a 10 da base casam (sem duplicata).
- [ ] **Simples, cashout, boost, bet builder, anulada, ganha com perna pushed/meia:** salvar o
      JSON como fixture, trocar o clone do harness e liberar na Ficha.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 21/11/2026 (**13 bilhetes**, todos múltiplas de 3 pernas, USDT):
`extensor/harness/fixtures/epicbet.pending.json` e `epicbet.settled.json`. Fonte = card.

| ID (código) | bet.id | Estado | Stake | Odd | Payout | Colocação (SP) | Evento (SP) |
|---|---|---|---|---|---|---|---|
| 11 | 39939822 | `won` → W | 40 | 7,14 | 285,6 | 20/11/2026 18:33 | 21/11/2026 09:00 |
| 6 | 39895669 | `won` → W | 40 | 8,09 | 323,6 | 20/11/2026 10:55 | 21/11/2026 10:30 |
| 10 | 39935760 | `lost` → L | 40 | 12,41 | 0 | 20/11/2026 17:46 | 20/11/2026 23:00 |
| 7 | 39895999 | `lost` (perna half_won) → L | 40 | 5,87 | 0 | 20/11/2026 10:58 | 20/11/2026 13:30 |
| 13 | 40014621 | `pending` | 10 | 13,28 | 132,8 (potencial) | 21/11/2026 13:11 | 21/11/2026 16:00 |
| 12 | 39939954 | `pending` (perna pushed) | 40 | 6,14 | 245,6 (potencial) | 20/11/2026 18:35 | 21/11/2026 16:00 |

**Sem amostra:** simples · cashout · boost · bet builder · anulada · ganha com perna pushed/meia.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão (**SharpenUp 0.7.91**) e dar **Ctrl+Shift+R** na aba da Epicbet **e**
   na aba do painel.
2. Abrir `epicbet.com` logado (o painel My Bets não precisa estar aberto: o inject busca as
   listas só com o cookie).
3. Conectar → Copiar bilhetes. Zero respostas = sessão caída.
4. Conferir no dashboard: contagem, código = ID do card, moeda, data do evento e a odd do card.
5. Na 1ª simples/cashout/boost, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

- 1ª casa sem campo de retorno nenhum: o W vem de stake × odd com as provas de forma (status e
  pernas). Se a casa um dia mandar o retorno, ele passa a mandar.
