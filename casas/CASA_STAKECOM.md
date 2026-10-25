# CASA_STAKECOM
## Camada de tradução — Stake.com → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Stake.com.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).
>
> ⚠️ **Não é a `Stake`** ([`CASA_STAKE.md`](CASA_STAKE.md), `stake.bet.br`, Kambi atrás de REST
> próprio). A Stake.com é a Stake **internacional**: outro motor, outro id, conta em cripto, outro
> histórico. No sistema são casas diferentes (`STAKE` × `STAKECOM`).

---

## 1. Identidade

- Casa canônica: `Stake.com` · site: `stake.com` · histórico em **Minhas Apostas → Esportes**
  (`/pt/my-bets/sports`, abas **Ativo** e **Definido**).
- Locale: `pt`. Mercado e seleção da aposta comum vêm em português da casa; na props de jogador
  (`SwishBet`) a estatística vem em inglês (`rebounds`, `points+assists+rebounds`).
- Moeda: a da **conta** (`currency: "usdt"`, minúsculo na casa). Dinheiro e odd em número, sem
  escala.
- Plataforma **PRÓPRIA**, GraphQL (`/_api/v1/graphql`, Cosmo Router). Família `stc`
  (`extensor/stc_inject.js`; `stk_` já é a Stake .bet.br).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s428):** `Stake.com`, a da BASE, com o ponto. Medido em 25/10/2026: `Stake.com` em
> `parceiros` (1 conta do Jaao26), `bilhetes` (288, de import), `casas_meta`, `correcoes` e
> `uso_tokens`. Chave `STAKECOM` (as chaves são alfanuméricas; o front e o `content.js` tiram o
> ponto ao comparar, desde a Sportsbet.io).

### 1.1 A moeda é da conta

Cadastre a conta **na moeda da carteira** (USDT no recon). O bloco leva `Moeda: USDT` e o carimbo
de colocação; o `/salvar` converte para R$ pela cotação do dia.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/stc_inject.js`).

```
POST https://stake.com/_api/v1/graphql
     x-access-token: <cookie `session`> · content-type: application/json
     { "query": "query SportSportList(…) { user { sportBetList(limit, offset, status) { id iid bet { … } } } }", … }
     { "query": "query ActiveBets_User(…) { user { activeSportBets … activeSwishBetList … activeRacingBets …
                 activeSportsbookXMultiBetList … } }", … }
```

Medido com a sessão do Feca (25/10/2026):

- **Auth:** `x-access-token` = o cookie `session` (96 caracteres, **não** é HttpOnly). O inject parte
  dele a frio, ou aprende o header de qualquer chamada `/_api/v1/graphql` da página.
- **A tela certa** é `/pt/my-bets/sports`. A `/pt/sports/my-bets` do sportsbook diz "Nenhum
  resultado encontrado" com a conta cheia de aposta.
- **`limit` acima de 50 devolve a lista VAZIA, sem erro** (51, 100 e 500 medidos, nas duas listas).
  O replay pede o que a página pede: 20 no histórico, 50 nas abertas. Não há total nem `hasNext`:
  fim = página menor que o pedido.
- **Histórico**: `sportBetList` com os status da página (`settled`, `settledManual`,
  `settledPending`, `cancelPending`, `cancelled`, `cashout`, `cashoutPending`). **Abertas**: quatro
  listas (`activeSportBets`, `activeSwishBetList`, `activeRacingBets`,
  `activeSportsbookXMultiBetList`), uma por tipo.
- **Introspecção desligada**; a página compila as queries em AST. O inject usa a **cópia literal**
  das duas queries da página.

### 2.3 Layout do bilhete (card)

Card por aposta: título da seleção (`Acima 2.5 Rebotes`), jogador, valor da estatística, estado
(`Derrota`, `Retirado`…), data e hora do jogo, times com placar, `Probabilidades 2,27`,
`Aposta 75.00000000`, `Pagamento 0.00000000`. O modal (clique no card) mostra `Colocado por …`,
a colocação em São Paulo e **`ID da Aposta: 676.297.455`**.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Stake.com |
|---|---|
| `iid` (histórico) / `bet.iid` (aberta) | `sport:676297455` — o número é o "ID da Aposta" do modal, o `[Código:]` e a chave de dedup |
| `bet.__typename` | `SportBet` (aposta comum) · `SwishBet` (props de jogador) · `RacingBet` · `SportsbookXMultiBet` |
| `bet.status` | `confirmed` (aberta) · `settled` · `cashout` (o "Retirado" do card) · os outros do filtro |
| `bet.amount` | stake (`75`) |
| `bet.payout` | o **retorno** (`44.943819` = 30 × 1,4981273); `0` na perdida |
| `bet.odds` (props) · `potentialMultiplier` (comum) | a odd do bilhete; o card arredonda a 2 casas (`2.2716947` → `2,27`) |
| `bet.customBet` | `true` em Criar Aposta, **inclusive** dentro de múltipla de 2 jogos (674778558) |
| `bet.createdAt` | colocação, `Fri, 23 Oct 2026 15:58:11 GMT` (= 12:58 em São Paulo no modal) |
| `bet.user` | ⚠️ **id e nome da conta**: o inject tira do cru e do lote |
| `outcomes[]` (comum) | `status` pending/won/lost, `odds`, `outcome.name` (seleção), `outcome.voidFactor`, `market.name`, `fixture` (nome, `data.startTime`, `data.teams` com `qualifier`, torneio e esporte) |
| `outcomes[]` (props) | `odds`, `lineType` (over/under), `cancel`, `outcome.line`, `outcome.name` (estatística, inglês), `outcome.competitor.name` (jogador), `outcome.market.game.fixture` (o jogo) |

**Ficha:** adaptador `app/adaptadores/stc.py` (família nova). O cru é `{iid, bet}`: o `iid` vai ao
lado porque no histórico ele mora fora da aposta e a props não o repete. Aceita perdida, ganha,
anulada pelo dinheiro e aberta, na comum e na props; recusa corrida, XMulti, promoção/boost,
cashout parcial e cashout com retorno ≠ stake.

---

## 3. ID do bilhete

- **Numérico de 9 dígitos** (`676297455`), o "ID da Aposta" do modal (`676.297.455`).
- Os 288 bilhetes `Stake.com` da base (import do Jaao26) têm códigos de import (`0`…`7`), sem
  relação com o id da casa.

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente): `fixture.data.startTime` em São Paulo. A
colocação (`createdAt`) sai no bloco e no carimbo de colocação.

---

## 5. Status e Resultado

| `status` · dinheiro | Leitura | Código |
|---|---|---|
| `confirmed` / `active` | Em aberto | *(vazio — não liquidar)* |
| qualquer · `payout` = stake (inclui o "Retirado" medido) | P/L zero | `V` |
| `cancelled` / `cancelPending` | Anulada | `V` |
| `settled*` · `payout` 0 | Perdeu | `L` |
| `settled*` · `payout` = stake × odd | Ganhou | `W` |
| `cashout` · `payout` ≠ stake | Cashout | `W`, odd = retorno ÷ stake (`MASTER_RESULTADO §5.6`) |
| corrida, XMulti, promoção, cashout parcial, retorno que não fecha | sobe cru | *(a conferir)* |

Medido no recon: 7 ganhas, 7 perdidas e 1 retirada (= stake) em props, 3 abertas comuns.

---

## 6. Boost / promoção

`promotionBet`, `customPrices` (odd turbinada) e `adjustments` vazios em toda a amostra. Se vierem,
o bloco diz "a conferir" e a Ficha recusa.

---

## 7. Cashout

"Retirado" no card = `status: cashout`. O medido devolveu a stake (60,01 → 60,01): `V` pela régua
do dinheiro. Cashout com outro valor vira `W` pela regra global (`MASTER_RESULTADO §5.6`), sem
amostra ainda. Cashout parcial (`cashouts[]`) sobe "a conferir".

---

## 8. Bônus

Sem amostra.

---

## 9. Mapa de mercados (Stake.com → `Aposta` global)

Só os confirmados no dado real:

| Stake.com exibe (mercado) | Aposta global |
|---|---|
| props `points` (jogador) | Pontos |
| props `assists` (jogador) | Assistência |
| props `rebounds` / `threesmade` / `points+assists+rebounds` | Player Props |

> As props de jogador vêm com a estatística em inglês (`points+assists+rebounds`,
> `threesmade`). Fórmula 1 (`Primeiro Piloto a Efetuar uma Pit Stop`, `Winner of Group 4`)
> segue o `MASTER_APOSTAS` pelo objeto medido.

---

## 10. Stake

Campo `amount`, na moeda da conta.

---

## 11. Odds

- Odd do bilhete: `odds` na props, `potentialMultiplier` na comum. **Nunca truncada** (o card
  mostra 2 casas; o bloco leva todas).
- **W:** `retorno ÷ stake`. **L e aberta:** a odd do bilhete.

---

## 12. Ruído a ignorar

- `user` (id e nome da conta), `qrCodeUrl`, `cashoutMultiplier`, `cashoutDisabled`,
  `outcome.competitor.stats[]`, `market.game.cashoutConfiguration`, `eventStatus` (placar ao vivo).
- Chamadas de `/_api/v1/graphql` que não são as listas (banners, menus, "Grandes Apostadores" da
  página, que lista apostas de OUTROS usuários): o inject só aprende o token delas.

---

## 13. Pegadinhas (resumo rápido)

1. **Não é a Stake .bet.br** (§1).
2. **`limit` > 50 = lista vazia, sem erro** (§2.1).
3. **A tela de apostas do sportsbook mente** ("Nenhum resultado"); a certa é `/pt/my-bets/sports`.
4. **`iid` fora da aposta no histórico**; a props não o repete (§2.5).
5. **`customBet` true em múltipla de 2 jogos** (§2.5).
6. **Ponto no nome** da casa: chave `STAKECOM` (§1).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada em **USDT** antes da 1ª captura.
- [ ] Contagem capturada == Ativo + Definido de `/pt/my-bets/sports`.
- [ ] **1ª aposta comum liquidada:** conferir o `status` das pernas e o `payout`.
- [ ] **1º cashout ≠ stake / boost:** salvar o JSON como fixture.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 25/10/2026 (**15 liquidadas + 3 abertas**, USDT): `extensor/harness/fixtures/stakecom.
settled.json` e `stakecom.active.json`.

| ID | Tipo | Status | Stake | Odd (card) | Pagamento | Fonte |
|---|---|---|---|---|---|---|
| 676297455 | Props simples (Matisse Thybulle acima 2.5 rebotes) | Derrota | 75 | 2,27 | 0 | card + modal |
| 676299526 | Props simples (Collin Sexton acima 0.5 três) | Vitória | 30 | 1,50 | 44,94 | JSON |
| 675668548 | Props simples (Aaron Gordon acima 21.5 PAR) | Retirado | 60,01 | 1,00 | 60,01 | card |
| 674734395 | Múltipla de 2 jogos | Vitória | 80 | 2,23 | 178,73 | card |
| 674775479 | Multi de Mesmo Jogo com 2 seleções | Derrota | 40,01 | 2,45 | 0 | card |
| 678433549 | F1, primeiro a fazer pit stop (Hamilton) | Ativo | 30 | 21 | — | JSON |

**Sem amostra:** aposta comum liquidada · cashout ≠ stake · cancelada · corrida · XMulti · boost.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão e dar **Ctrl+Shift+R** na aba da Stake.com.
2. Conectar → Copiar bilhetes (o inject parte do cookie da sessão).
3. Conferir no dashboard: contagem, código de 9 dígitos, colocação, odd e moeda.

---

## Feedback para a camada global / MODELO

1. **Limite que devolve vazio em vez de erro** (`limit` > 50): quem pagina pedindo "o máximo"
   lê conta vazia. Peça o que a página pede.
2. **A página certa não é a óbvia.** Antes de concluir que a conta não tem aposta, pergunte à API.
