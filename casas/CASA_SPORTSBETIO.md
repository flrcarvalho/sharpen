# CASA_SPORTSBETIO
## Camada de tradução — Sportsbet.io → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Sportsbet.io.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Sportsbet.io` · site: `sportsbet.io` · histórico em **Minhas Apostas**
  (`/pt/user/my-bets/active` e `/pt/user/my-bets/settled`).
- Locale: `pt`. Mercado, seleção e jogo vêm em **português** da própria casa
  (`1º tempo - Cadiz CF total de escanteios`, `Menos de 1.5`); o esporte vem só como `slug` em
  inglês (`soccer`, `ice-hockey`).
- Moeda: a da **conta** (`currencyCode: "USDT"` no recon; casa cripto). O card escreve
  `Aposta USDT 25,00`.
- **Dinheiro em 1e8** (`2500000000` = 25,00) e odd em número (`11.64`).
- Plataforma **PRÓPRIA** (GraphQL do grupo Yolo, Apollo no mesmo domínio). Família `sbi`
  (inject `sbi_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s428):** `Sportsbet.io`, a da BASE, com o ponto. Medido em 25/10/2026:
> `Sportsbet.io` em `parceiros` (2 contas: Gabriel e Jaao26), `bilhetes` (6, de print, sem
> código), `casas_meta`, `correcoes` e `uso_tokens`. É a **1ª casa com ponto no nome**: a chave
> do registro é `SPORTSBETIO` (as chaves são alfanuméricas), e o front (`_casaConectavel`) e o
> `content.js` tiram ponto e espaço ao comparar.

### 1.1 A moeda é da conta

Cadastre a conta **na moeda da carteira** (USDT no recon). O bloco leva `Moeda: USDT` e o
carimbo de colocação; o `/salvar` converte para R$ pela cotação do dia.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/sbi_inject.js`).

```
POST https://sportsbet.io/graphql
     authorization: Bearer <JWT do cookie `token`> · content-type: application/json
     { "operationName": "SettledTicketsQuery" | "ActiveTicketsQuery",
       "variables": { "first": 100, "after": "<cursor>", "language": "pt" }, "query": "…" }
→ { "data": { "sportsbetTickets": { "myBettingHistory" | "myActiveTickets":
      { "edges": [ { "node": { …bilhete… } } ], "pageInfo": { "hasNextPage", "endCursor" } } } } }
```

Medido com a sessão do Feca (25/10/2026):

- **Auth por `authorization: Bearer <JWT>`**. O JWT é o cookie `token` (legível, não é
  HttpOnly): o inject parte dele a frio. Sem o header a resposta é **HTTP 200** com a lista
  **`null`** e sem `errors`; o JWT sem o prefixo `Bearer` também dá `null`.
- A tela pede `first: 5` e depois `first: 20` com `after`. `first` 100, 500 e 1000 aceitos.
  O cursor é base64 de `mongodbconnection:N`. Fim autoritativo: `pageInfo.hasNextPage: false`.
  Provado: `first: 5` + cursor dá 16 únicos de 16, o mesmo que `first: 100`.
- **As abertas também paginam.** A tela as pede com `myActiveTickets(first: 100)` sem
  `pageInfo`; o replay pede com `pageInfo` e cursor.
- O WebSocket da página (`/graphql`, protocolo próprio `{eventName, eventData, token}`) só leva
  PING/PONG e as assinaturas de bilhete novo. A lista vem por fetch.
- A troca de aba (Ativas ↔ Finalizadas) recarrega a página inteira.

### 2.3 Layout do bilhete (card)

Selo de estado (`PERDEU`, `GANHOU`) + selo de tipo (`MÚLTIPLA 3`, `INVENTOR` = Bet Builder,
`TURBINADO`), tempo relativo (`5h`, `1d`), pernas com um quadradinho de cor (verde ganha,
vermelha perdida, cinza anulada, relógio pendente), placar azul ao lado, e o rodapé
`Odds · Aposta USDT · Perdeu/Ganhou USDT`. Botão `ID` copia o código. Card de múltipla antiga
vem fechado (pernas atrás da seta). **Texto por DOM não serve; por isso API.**

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Sportsbet.io |
|---|---|
| `node.id` | base64 de `SportsbetTicketsTicket:<ObjectId>`; o ObjectId (24 hex) é o que o botão `ID` copia — chave de dedup e `[Código:]` |
| `node.status` | `ACTIVE` (aberta) · `SETTLED` (liquidada recente) · `ARCHIVED` (liquidada antiga) |
| `node.stakeAmount` | stake em **1e8** (`2500000000` = 25,00). ⚠ escala medida só em USDT |
| `node.wonAmount` | o **retorno** em 1e8 (`10621770000` = 106,2177 = 60,01 × 1,77); **null** na perdida e na aberta |
| `node.maxWin` | potencial (stake × odd), 1e8 |
| `node.boostedOdds` · `odds` | a odd do **card** é `boostedOdds`; `odds` é a sem turbo (5,83 × 5,71 no turbinado) |
| `node.boosterTicket` | `true` no `TURBINADO` |
| `node.betType` | `"0"` simples · `"1"` múltipla |
| `node.placedAt` | colocação, **unix em SEGUNDOS** |
| `node.currencyCode` | moeda da conta (`USDT`) |
| `node.cashBackStake` · `insuranceActive` | `cashBackStake` = stake na maioria, metade em 2 bilhetes; **significado não medido**, fora do bloco |
| `node.cashout.instances` | `null` em toda a amostra |
| `bets[]` | **1** por bilhete em toda a amostra; `bets[0].totalOdds` **não** é a do card no turbinado (5,91) |
| `bets[0].freeBet` | `false` em toda a amostra |
| `selections[].status` | `"0"` pendente · `"1"` ganha · `"2"` perdida (cor no card) |
| `selections[].voidFactor` | `1` = **anulada** (cinza no card), mesmo com `status` 2; `null` na pendente |
| `selections[].odds` · `boostedOdds` | odd da perna; a turbinada quando o bilhete é `TURBINADO` |
| `selections[].name` · `marketName` · `eventName` | seleção, mercado e jogo, em pt, verbatim |
| `selections[].sport.slug` | esporte em slug inglês (`soccer`, `basketball`, `tennis`, `ice-hockey`, `american-football`, `handball`) |
| `selections[].eventStartTime` | início, unix em segundos |
| `selections[].eventScore` | placar, quase sempre `null` |

**Bet Builder** (`INVENTOR` no card): uma perna só, `marketName: "Bet Builder"`, com as seleções
do cupom juntas por `;` em `name` (`Rebotes do jogador - P.J. Washington 10+ (Partida);Pontos do
jogador - …`). O bloco as escreve uma por linha.

**Ficha:** adaptador `app/adaptadores/sbi.py`. Aceita perdida, ganha (retorno = stake × odd do
card), anulada pelo dinheiro e aberta; **recusa** Bet Builder (perna única com seleções juntas),
freebet, cashout, sistema e moeda fora de USDT (escala não medida): esses vão à IA pelo texto.

---

## 3. ID do bilhete

- **ObjectId de 24 hex, minúsculo** (`6addf2d1bf9e9d0001d7fda3`), o que o botão `ID` copia.
- Dedup forte por ID. Os 6 bilhetes `Sportsbet.io` que já estavam na base (print) não têm código.

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente): `eventStartTime` (unix) em São Paulo. A
colocação (`placedAt`) sai em São Paulo no bloco e no carimbo de colocação.

> Múltipla perdida com perna ainda por jogar (comum aqui: a casa liquida a múltipla na 1ª perna
> perdida): o servidor puxa a data para a perna perdida (`repository.data_da_perna_perdida`,
> pelo rótulo `[perna perdida]`).

---

## 5. Status e Resultado

Só o **dinheiro** decide, com o status cru ao lado.

| `status` · dinheiro | Leitura | Código |
|---|---|---|
| `ACTIVE` | Em aberto | *(vazio — não liquidar)* |
| qualquer · `wonAmount` = stake | P/L zero | `V` |
| liquidada · `wonAmount` null/0 · alguma perna perdida (status 2, `voidFactor` ≠ 1) | Perdeu | `L` |
| liquidada · `wonAmount` = stake × `boostedOdds` | Ganhou | `W` |
| múltipla com perna anulada · `wonAmount` = stake × produto das pernas que valeram | Ganhou | `W` (odd = retorno ÷ stake) |
| freebet, cashout, retorno que não fecha, sem retorno e sem perna perdida | sobe cru | *(a conferir)* |

Medido: 13 perdidas e 2 ganhas (uma TURBINADA) no recon, todas com o número fechando. O bloco
sempre leva `Status (API): status=… · betType=…` (e `TURBINADO`).

---

## 6. Boost / promoção

**TURBINADO** (`boosterTicket: true`, `boostType: BET_BOOST`): a odd do card e a que paga é
`boostedOdds` (25 × 13,15 = 328,75 no 6adc8eef, onde `odds` = 12,71). O bloco leva `Odd:` com a
turbinada e `Odd sem o turbo:` à parte; a odd de cada perna sai turbinada.

---

## 7. Cashout

`cashout.instances` = `null` em toda a amostra (e a escala do valor não é conhecida). Se vier, o
bloco sobe os valores crus e diz "a conferir". Regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`)
quando for medido.

---

## 8. Bônus

`bets[0].freeBet` = `false` em toda a amostra. Se vier `true`, o bloco diz "a conferir".

---

## 9. Mapa de mercados (Sportsbet.io → `Aposta` global)

Só os confirmados no dado real, com o nome que a casa escreve:

| Sportsbet.io exibe (mercado) | Aposta global |
|---|---|
| `<time> total de escanteios` / `Escanteios 1x2` | Escanteios |
| `Total de cartões` | Cartões |
| `Handicap Asiático` / `Handicap (incluindo prorrogação)` | Handicap |
| `3º quarto - total` (basquete) | Pontos |

> `1º tempo` / `3º quarto` são **recorte**, não mercado novo. Mercado de jogador vem com o nome
> na frente (`Darius Acuff Jr. Assistências (inc. prorrogação)`). Bet Builder: as seleções vêm
> prontas (§2.5).

---

## 10. Stake

Campo `stakeAmount` ÷ 1e8, na moeda da conta. O card corta em 2 casas (`11,34`); o bloco leva
todas (`11,3418`).

---

## 11. Odds

- **A odd do bilhete é `boostedOdds`**, a do card; sem turbo, igual a `odds`.
- **W:** `retorno ÷ stake` (regra global). **L e aberta:** `boostedOdds` (não zera na perdida).
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `cashoutOffer`, `cashoutAllowed`, `giveaways`, `racingMeta`, `multiboost`, `cashBackStake`,
  `insuranceActive`, `bets[].cashbackPercent`.
- `selections[].market.selections` (as outras opções do mercado), `deductions`, `enName`,
  `provider_product_id`, `selectionId`, `eventId`.
- Chamadas de `/graphql` que não são a lista (`GetUserPendingEventsQuery`,
  `SportcastMarketQuery`, analytics): o inject só aprende o Bearer delas.

---

## 13. Pegadinhas (resumo rápido)

1. **Dinheiro em 1e8** (§2.5), medido só em USDT.
2. **Erro com HTTP 200**: sem sessão, a lista volta `null`, sem `errors` (§2.1).
3. **Odd do card = `boostedOdds`**, não `odds` nem `bets[].totalOdds` (§6).
4. **`voidFactor` 1 é anulada** mesmo com `status` 2 (§2.5).
5. **Ponto no nome** da casa: chave `SPORTSBETIO` (§1).
6. **Bet Builder** em perna única com `;` (§2.5).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada em **USDT** antes da 1ª captura.
- [ ] Contagem capturada == Ativas + Finalizadas.
- [ ] Coluna Data = evento em São Paulo (a perdida, pela perna perdida).
- [ ] **Conta em outra moeda (BRL):** medir a escala do `stakeAmount` antes de virar a Ficha.
- [ ] **1º cashout / freebet:** salvar o JSON como fixture e trocar o clone do harness.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 25/10/2026 — conta inteira (**17 liquidadas + 14 abertas**, USDT):
`extensor/harness/fixtures/sportsbetio.settled.json` e `sportsbetio.active.json`.

| ID | Tipo | Status | Stake | Odd | Retorno | Fonte |
|---|---|---|---|---|---|---|
| 6addf2d1bf9e9d0001d7fda3 | Múltipla 3 (verde · vermelha · pendente) | PERDEU | 25 | 11,64 | — | card |
| 6add828bbf9e9d0001c921a7 | Múltipla 3 (vermelha · cinza · vermelha) | PERDEU | 25 | 5,07 | — | card |
| 6add45c3bf9e9d0001114d46 | Simples | GANHOU | 60,01 | 1,77 | 106,2177 | card |
| 6adc8eefbf9e9d00016fa2ac | Múltipla 3 TURBINADO | GANHOU | 25 | 13,15 | 328,75 | card |
| 6adbc55dbf9e9d0001c75309 | Múltipla 3 TURBINADO | PERDEU | 25 | 5,83 | — | card |
| 6add3525bf9e9d0001ae48c4 | INVENTOR (Bet Builder, 2 seleções) | PERDEU | 30,01 | 4,75 | — | card |

**Sem amostra:** anulada inteira · cashout · freebet · sistema · outra moeda.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão e dar **Ctrl+Shift+R** na aba da Sportsbet.io.
2. Conectar → Copiar bilhetes (o inject parte do cookie da sessão; não precisa abrir Minhas Apostas).
3. Conferir no dashboard: contagem, código de 24 hex, colocação, odd (turbinada) e moeda.

---

## Feedback para a camada global / MODELO

1. **Nome de casa com ponto.** As chaves do sistema e os regex dos audits assumem nome
   alfanumérico; `Sportsbet.io` exigiu tirar o ponto em `_casaConectavel` e no `content.js`.
2. **Erro com 200 e lista `null`.** Quem confia no status ou em `errors` conta sessão vencida
   como "conta vazia".
