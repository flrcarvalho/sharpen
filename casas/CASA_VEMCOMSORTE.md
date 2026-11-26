# CASA_VEMCOMSORTE
## Camada de tradução — Vem com Sorte → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Vem com Sorte.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Vem com Sorte` · site: `vemcomsorte.com` (esportes em `/sport`) · apostas no
  painel **Minhas Apostas** (gaveta lateral, aberta pelo "Bilhete" no rodapé), com filtro
  Todas / VENCEU / Anulada / Perdeu / Meia vitória / Meia derrota / Não resolvida / Encerrar aposta.
- Locale: o site em português, mas a **API manda em inglês** (`Asian Handicap Games`,
  `Under/Over`, `Tennis`, `Ice Hockey`); a tela traduz por um dicionário à parte. Times e
  jogadores verbatim.
- Moeda: **BRL** (`money.currency`). O bloco não leva linha `Moeda:` (casa em real).
- Plataforma **PRÓPRIA** (app Vue, API no mesmo domínio: `/api/bettor/*`, `/api/sportsbook/public/v2/*`,
  `/api/client/client:getProfile`, `/api/wallet/wallet:listWallets`). Não é Altenar, Kambi,
  BetBy, BetConstruct nem Rogue. Família `vcs` (inject `vcs_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s467):** `Vem com Sorte`, a da marca. A base não tinha a casa em grafia nenhuma
> (medido em 26/11/2026 em `parceiros`, `bilhetes`, `casas_meta`, `correcoes` e `uso_tokens`,
> procurando "sorte" sem caixa e sem espaço: só Esportes da Sorte, Lance de Sorte, Viva Sorte e afins).

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API, replay a frio** (SharpenUp · `extensor/vcs_inject.js`).

```
POST https://vemcomsorte.com/api/bettor/bet:history
     Authorization: <localStorage.authToken>          (UUID cru, sem "Bearer")
     {"ascending": false, "limit": 100,
      "filter": {"dateRange": {"from": <ms>, "to": <ms>}, "statuses": []},
      "token": "<nextToken da página anterior>"}       (só a partir da 2ª página)
→ {"data": [ … ] | null, "hasMore": bool, "nextToken": "…", "metadata": {"eventsData", "eventsStatuses"}}
```

Medido no recon de 26/11/2026 (Chrome do Feca):

- **A tela é estreita:** o painel pede 90 dias, `limit` 20, e **só quando abre**. O inject
  pede 120 dias, 100 por vez, e não depende de o painel ser aberto.
- **Auth:** o token mora em `localStorage.authToken`. O app manda `Authorization` e
  `x-session-token` com o mesmo valor, mais `x-project-id` (331), `x-language`, `x-currency`;
  **só o `Authorization` basta** (sozinho 200; só `x-session-token` 401; nada 401).
- **Paginação por `token` no corpo** (o `nextToken` anterior). `nextToken` no corpo é
  ignorado (devolve a 1ª página de novo). **Fim = `hasMore: false`**, e aí não vem `nextToken`.
- ⚠️ **Janela máxima ~123 dias:** `from` mais antigo dá 400 `PRECONDITION_FAILED` dizendo o
  piso (`Field 'from'=… must be greater or equal to <ms>`). Sem `filter.dateRange`, 400.
  Bilhete colocado há mais de ~4 meses não é alcançável pela API.
- ⚠️ **Lista vazia = `data: null`**, não `[]`.
- `statuses: []` traz abertas e liquidadas juntas. O enum (do bundle): `UNSETTLED`, `WIN`,
  `LOSE`, `VOID`, `CASHOUT`, `HALF_WIN`, `HALF_LOSE`.
- `limit` 1000 foi aceito (a conta tinha 7). O inject pede 100.
- A CSP não declara `connect-src`. O JSON do recon saiu da aba em fatias, conferido por SHA-256.

### 2.3 Layout do bilhete (card)

`Múltipla: <rótulo>` (VENCEU / Perdeu / Não resolvida) · **Valor da aposta** · **Saque** (liquidada)
ou **Ganho possível** (aberta) · cada perna com `<seleção> (<linha>)`, odd, mercado traduzido
(`Handicap (Jogos)`, `Vencedor 2 vias`, `Total`), placar e o resultado da perna · **Odds totais**.

- ⚠️ O card **não mostra data nem hora** (nem da colocação, nem do evento).
- ⚠️ **"Odds totais" é TRUNCADA em 2 casas** (6.59 para 6,595784).

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Vem com Sorte |
|---|---|
| `id` | o **ID da aposta** (7 dígitos, `3602620`) → `[Código:]` |
| `billingTransactionId`, `requestId` | internos; não entram |
| `type` | `MULTIPLE` na amostra (enum: `SINGLE`, `MULTIPLE`, `SYSTEM`, `FLEXIBLE`, `ONE_CUT`) |
| `status` | `UNSETTLED` · `WIN` · `LOSE` na amostra |
| `createTime` · `updateTime` | epoch **milissegundos**. `createTime` = colocação. `updateTime` não é provadamente a liquidação |
| `money.amount` · `money.multiplier` | ⚠️ **centavos**: 25000 ÷ 100 = R$ 250,00 |
| `money.payout` | o **"Saque"** do card (retorno; 0 na perdida e na aberta), já com o boost |
| `money.possiblePayout` | o **"Ganho possível"** da aberta, já com o boost |
| `money.bonus` · `possibleBonus` | a parte do retorno que é o Combo Boost (4075 = R$ 40,75) |
| `odds` | a odd do card, **truncada** em 2 casas |
| `initialOdds` | a odd **completa**, já com o Combo Boost (6,595784) |
| `bonuses[]` | `Combo Boost — Até +100% em apostas múltiplas!`; `options[].active` diz o % aplicado |
| `cashoutEligible` · `cutPercentage` · `boostxStatus` | `false` / 0 / `UNAVAILABLE` na amostra |
| `outcomes[]` | `status`, `odds`, `name` (seleção), `parameters` (a linha: `+6.5`, `21.5`, `0`, vazio), `market.name`, `event.name`, `event.startTime` (ms), `tournament.name`, `region.name`, `sport.name`, `sportService` (`PREMATCH`/`LIVE`) |

**Ficha (s467):** adaptador `app/adaptadores/vcs.py`, gate `tests/test_adaptador_vcs.py`. O
bilhete da API basta sozinho para a Ficha (esporte, liga, evento, mercado e seleção dentro de
cada `outcome`). A Ficha aceita aberta, ganha (toda perna `WIN`, retorno fechando stake × odd)
e perdida (retorno 0 com perna perdida), e recusa o resto, que vai à IA pelo texto. Medido na
fixture: **7 de 7 aceitas** (2 abertas, 1 ganha, 4 perdidas).

---

## 3. ID do bilhete

`id` da aposta, numérico de 7 dígitos. As pernas têm `id` próprio (10 dígitos), de outra série:
não é código.

---

## 4. Data

- **Coluna Data = dia do EVENTO em Brasília** (`event.startTime`, epoch ms UTC → São Paulo),
  pela régua global (perna mais recente; na perdida, `MASTER_OUTPUT §4.0.1`).
- O bloco também leva a colocação (`createTime`). O card não mostra nenhuma das duas.

---

## 5. Status e Resultado

| `status` · pernas · dinheiro | Leitura | Código |
|---|---|---|
| `UNSETTLED` | Em aberto | *(vazio — não liquidar)* |
| `WIN` · toda perna `WIN` · `payout` fecha stake × odd no centavo | Ganhou | `W` |
| `LOSE` · `payout` 0 · ao menos uma perna `LOSE`/`HALF_LOSE` | Perdeu | `L`, odd do card |
| qualquer liquidada com `payout` = stake | retorno = stake (rede do dinheiro) | `V` |
| `VOID`, `CASHOUT`, `HALF_WIN`, `HALF_LOSE`, `WIN` com perna não-`WIN`, tipo `SYSTEM`/`FLEXIBLE`/`ONE_CUT`, status novo | sobe cru | *(a conferir)* |

O bloco sempre leva `Status (API): status … · type … · id …`. Medido: `UNSETTLED` 2, `WIN` 1, `LOSE` 4.

Perna: `UNSETTLED` = em aberto (aparece também em múltipla já perdida), `WIN` = ganha, `LOSE` = perdida.

---

## 6. Boost / promoção

**Combo Boost** automático em múltipla (3% com 3 seleções de odd ≥ 1,4, subindo com o número de
seleções). Ele aumenta o **lucro**: na ganha 3602620, 3% de (250 × 6,4328 − 250) = R$ 40,75 de
`bonus`, dentro do `payout` (1.648,95). A `initialOdds` já vem com ele (6,595784), e é ela que o
card mostra. Na perdida o boost é desligado do `possiblePayout` (vira o produto das pernas), mas
a odd do card segue a boostada. O bloco leva a linha `Boost:` quando há opção ativa.

---

## 7. Cashout

O filtro "Encerrar aposta" existe; nenhuma aposta encerrada na amostra (`cashoutEligible` falso
em todas). `CASHOUT` sobe **a conferir** e a Ficha recusa.

---

## 8. Bônus

Sem freebet medida. O que aparecer sobe a conferir (`MASTER_RESULTADO §5.8` decide quando houver amostra).

---

## 9. Mapa de mercados (Vem com Sorte → `Aposta` global)

Mercados vistos (nome da API): `Asian Handicap`, `Asian Handicap Games`, `Asian Handicap
Including Overtime`, `Under/Over`, `Under/Over Games`, `Under/Over Including Overtime`,
`Under/Over Halftime`, `Double Chance`, `1X2`, `12`. A categoria sai do `MASTER_APOSTAS` pelo
objeto medido, sem atalho aqui. `12` = vencedor em 2 vias; `Games` = games (tênis).

---

## 10. Stake

`money.amount ÷ money.multiplier`, em real.

---

## 11. Odds

- **Aberta e perdida:** `initialOdds`, completa (o card mostra truncada). **Nunca** o produto
  das pernas nem `possiblePayout ÷ stake` (na perdida ele perde o boost).
- **Ganha:** a `initialOdds` quando fecha o retorno no meio centavo (250 × 6,595784 = 1.648,946 →
  1.648,95), senão retorno ÷ stake — a mesma régua da Ficha.
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

`billingTransactionId`, `requestId`, `locale`, `boostxStatus`, `boostxable`, `vipBettingEligible`,
`earlyPayout*`, `imageUrlPath`, `statistic*`, `matchClock`, `metadata.eventsData` (placar ao vivo),
`money.*Gross/*Net/*Tax`, `money.rate`.

---

## 13. Pegadinhas (resumo rápido)

1. **Dinheiro em centavos** (§2.5).
2. **Card trunca a odd** (§11).
3. **Boost dentro do retorno e da `initialOdds`; some do `possiblePayout` na perdida** (§6).
4. **Janela máxima ~123 dias; vazio = `data: null`; página pelo `token`** (§2.1).
5. **API em inglês, tela em português** (§1).

---

## 14. Validações específicas

- [ ] Nenhuma aberta liquidada; potencial só na aberta (= `possiblePayout`).
- [ ] Coluna Data = evento em São Paulo.
- [ ] Odd da perdida 3420609 = 6,56303 (nunca 6,401).
- [ ] **Simples, anulada, cashout, meia, sistema, ao vivo:** salvar o JSON como fixture, trocar o
      clone do harness e liberar na Ficha.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 26/11/2026 (**7 bilhetes**, todos múltiplas de 3 pernas, R$ 250):
`extensor/harness/fixtures/vemcomsorte.bet_history.json`. Fonte = card (odd, valor, saque/ganho
possível, rótulo); datas do JSON em Brasília.

| ID (código) | Estado | Odd (card → completa) | Saque / Ganho possível | Colocação (SP) | Evento mais recente (SP) |
|---|---|---|---|---|---|
| 3602620 | `WIN` → W (Combo Boost +3%) | 6.59 → 6,595784 | 1.648,95 | 25/11/2026 20:28 | 26/11/2026 07:00 |
| 4826593 | `LOSE` → L | 7.21 → 7,2109 | 0 | 25/11/2026 20:27 | 26/11/2026 04:30 |
| 3420609 | `LOSE` (perna em aberto) → L | 6.56 → 6,56303 | 0 | 25/11/2026 20:33 | 26/11/2026 17:00 |
| 8282618 | `LOSE` → L | 72.69 → 72,69006 | 0 | 25/11/2026 20:30 | 26/11/2026 11:00 |
| 5258640 | `LOSE` → L | 10.62 → 10,621745 | 0 | 25/11/2026 20:26 | 25/11/2026 21:30 |
| 5898642 | `UNSETTLED` | 32.55 → 32,55405 | 8.138,51 (potencial) | 26/11/2026 10:30 | 26/11/2026 15:00 |
| 1324669 | `UNSETTLED` (perna ganha) | 10.48 → 10,48169075 | 2.620,42 (potencial) | 25/11/2026 20:32 | 26/11/2026 15:00 |

**Sem amostra:** simples · anulada · cashout · meia vitória/derrota · sistema · ao vivo.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão (**SharpenUp 0.7.93**) e dar **Ctrl+Shift+R** na aba da Vem com Sorte
   **e** na aba do painel.
2. Abrir `vemcomsorte.com` logado (o painel Minhas Apostas não precisa estar aberto).
3. Conectar → Copiar bilhetes. `semToken` = aba deslogada; HTTP 401 = sessão caída.
4. Conferir no dashboard: contagem, código = ID da aposta, data do evento e a odd completa.
5. Na 1ª simples/anulada/cashout, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

- 1ª casa com boost de lucro embutido na odd "inicial" e **desligado** só do potencial da perdida:
  a odd do card não é `possiblePayout ÷ stake` na perdida.
