# CASA_BETPANDA
## Camada de tradução — Betpanda → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betpanda.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> ⚠️ **SIGILO (decisão do Feca, 02/10/2026):** casa normal no seletor, mas **fora** de aviso
> ao grupo de testers, do `changelog.json` e da home. Nenhum passo desta casa roda
> `scripts/avisar_testers.py`.

---

## 1. Identidade

- Casa canônica: `Betpanda` · site: `betpandacasino.io` · sportsbook em `/pt/sportsbook/`
- Locale: **pt-PT** misturado com inglês (§9) · Moeda: **dólar** na API (`currency: "$"`), carteira em **Tether**
- **Decimal na API: PONTO** (`"70.18"`, `"1.83"`) → normalizar para vírgula.
- Motor: **BetBy** (`sptpub.com`), tenant `betpanda`. ⚠️ **Não é iframe** — o `bt-renderer` monta o
  app na própria página (`betpanda.sptpub.com/bt-renderer.min.js`), dentro de shadow DOM.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s391):** a base não tinha nenhuma (medido em 03/10/2026: zero conta e zero bilhete
> com `panda` fora a KingPanda), então vale a da **marca**, que o site escreve `Betpanda` no logo
> e no título. ⚠️ **Quem digitar "Bet Panda" (com espaço) cria uma casa à parte, sem captura**:
> o `casa_canonica` só reconhece grafia que já existe em `parceiros`, e o `_display_to_key`
> compara a caixa mas não ignora espaço. Foi o que aconteceu com a DEX Sport
> ([`CASA_DEXSPORT §1`](CASA_DEXSPORT.md)). Escolha a casa na lista.

### 1.1 A MOEDA é da conta, não da casa  ⭐

A API diz `currency: "$"` e a URL pede `currency=USD`, mas a carteira da conta é **Tether**. A
API não distingue USD de USDT; o **cadastro da conta** distingue
([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).

- Cadastre a conta com a moeda que ela usa (USDT no caso do Feca). O `/salvar` converte a stake
  para R$ pela cotação do dia da aposta; a tela mostra o valor original embaixo.
- O bloco capturado leva `Moeda: $` e os rótulos de dinheiro na moeda da casa
  (`retorno 126,00 $`). `$`, USD e USDT não se contradizem (decisão do Feca, 04/10/2026): não gera aviso.
- **Os números do TSV são os da casa, em dólar.** Quem converte é o servidor, nunca a IA.

### 1.2 Espelho da Jonbet/Betboom/Blaze

Quarta casa técnica do mesmo motor, provada no recon de 03/10/2026, antes de qualquer código:

| Prova | Betpanda | Blaze |
|---|---|---|
| `bt-renderer` na própria página | `betpanda.sptpub.com` | `blaze.sptpub.com` |
| host da API | `api-a-c7818b61-600` ⚠️ fora do padrão `api-NN-sp-…` | `api-31-sp-c7818b61-584` |
| **hash do operador** | `c7818b61` | `c7818b61` |
| `GET /api/v1/my_bets/list` · `{results, count}` · `status` vazio = todas | idêntico | idêntico |

O `jb_inject.js` casa por **PATH**, então o host diferente não importa. A captura usa o mesmo
inject, o mesmo `formatTicketJB` e o mesmo `roboJBPassive`. O harness tem caso próprio
(`casos/betpanda.mjs`), com a fixture **desta** casa contra o card **desta** casa.

> **Ao mexer numa das quatro, confira as outras três.**

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/jb_inject.js`, compartilhado).

```
GET https://api-a-c7818b61-600.sptpub.com/api/v1/my_bets/list
    ?currency=USD&lang=pt&limit=15&skip=0&status=<enum|vazio>&timestamp_from=&timestamp_to=
    Authorization: Bearer <token da sessão BetBy>
→ { "results": [ … ], "count": <total do filtro> }
```

A lista vive em `betpandacasino.io/pt/sportsbook/?bt-path=%2Fbets` (menu **Esportes →
Minhas Apostas**). ⚠️ `/sports` dá **404**: o caminho é `/sportsbook/`.

Paginação medida ao vivo: `limit=15`, `count: 45` constante, "Mostrar mais" pede `skip` 15 e 30;
a última página veio cheia (45 = 3 × 15). O inject avança pelo tamanho que **voltou**.

### 2.2 Abas da tela

`Todas · Pendentes · Ganhas · Perdidas · Cash Out · Canceladas · Devolvidas`, que mandam
`status` = vazio · `open` · `won` · `lost` · `cashed_out` · `canceled` · `refund`. As três
últimas voltaram `count: 0` nesta conta.

### 2.3 Layout do bilhete

Cards em grid de 3 colunas. Cabeçalho com `SIMPLES` / `MÚLTIPLA` / `SISTEMA` + data/hora **da
colocação** + selo (`GANHA` / `PERDIDA`); selo extra **`MÚLTIPLA BOOST`** na múltipla com boost.
Abaixo, data/hora **do evento** ("Hoje, 06:30"), liga e confronto; depois `Odd total`,
`Valor da aposta`, `Ganhaste` / `Ganhos possíveis`, e `ID da aposta:`. O dinheiro aparece com o
símbolo **depois** do número (`70.00 $`, `sign_before_value: false`).

---

## 2.5 Campos da API (o que o inject entrega)

Mesma tabela da [`CASA_JONBET §2.5`](CASA_JONBET.md). Confirmado na Betpanda (45 bilhetes, 10
cards lidos na tela):

| Campo | Confirmado na Betpanda |
|---|---|
| `id` | 19 dígitos, string — bate com `ID da aposta` |
| `sum` (stake) | `"70"`, `"70.18"`, `"2.66"` — bate com `Valor da aposta` |
| `k` | odd do card, **com** boost |
| `total_k` | `"0"` nas **perdidas simples**; nas **múltiplas** perdidas às vezes `0`, às vezes a odd (§11) |
| `result_k` | `0` na perdida; **sem** boost na ganha com boost (§6) |
| `result_sum` | retorno liquidado — bate com `Ganhaste` |
| `potential_win` | só na aberta — retorno **potencial** |
| `cashout_amount` | preenchido em 5 abertas: **oferta**, não retorno (§7) |
| `timestamp` | epoch em segundos **com fração** (`1790983719.876…`), horário de São Paulo |
| `desc.scheduled` | epoch em segundos — vira a coluna Data (§4) |
| `currency` / `currency_details` | `"$"` · `{sign_before_value: false, cents: 2}` (§1.1) |
| `bonus` | `{type: "comboboost", name: "ComboBOOST-BP", total_multiplier}` (§6) |
| `combinations` | presente no sistema 2/3 (§11) |
| `count` (raiz) | fim autoritativo da paginação |

---

## 3. ID do bilhete

- **Numérico, 19 dígitos** (ex.: `2717948654752248251`), no card como `ID da aposta: …`.
- Sempre visível → **dedup forte por ID**.
- Fora do snap por edit-distance do `corrigir_codigos_tsv`, como as outras BetBy (ids quase
  idênticos entre si; um snap trocaria o código pelo do vizinho).

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente), `MASTER_OUTPUT §4`. O bloco emite as duas,
`Data (evento mais recente):` primeiro. Exemplo do recon: colocada **02/10 20:28**, jogo **03/10
06:30**. `timestamp` tem fração de segundo; o `_dhJB` multiplica por 1000 e trunca na exibição.

---

## 5. Status e Resultado

| `status` | Leitura | Código |
|---|---|---|
| `open` | Em aberto (selo nenhum, `Ganhos possíveis`) | *(vazio — não liquidar)* |
| `won` | Ganhou (selo `GANHA`) — conferir o dinheiro | `W` |
| `lost` | Perdeu (selo `PERDIDA`) | `L` |
| `refund` | Devolvida | `V` (pela régua do dinheiro) |
| `canceled` | Cancelada | `V` (pela régua do dinheiro) |
| `cashed_out` | Cashout executado | regra global (§7) |

Medido: **`won` (12) · `lost` (21) · `open` (12)** em 45. `refund`, `canceled` e `cashed_out`
**sem caso** nesta conta: rótulo que ninguém cruzou com a tela sobe como "a conferir".

> ⚠️ Retorno zero só vira `L` quando o status cru concorda (`lost`).

---

## 6. Boost / promoção  ⭐

**ComboBOOST-BP**: multiplicador sobre a odd da múltipla (`bonus.total_multiplier`, 1,05 na
amostra), com selo `MÚLTIPLA BOOST` no card.

- **Ganha** (`…8141`): `k` = `total_k` = **9,004** (com boost); `result_k` = 8,575 (produto das
  pernas, sem boost). A casa pagou 2,66 × 9,004 = **23,95**. A odd do `W` é `retorno ÷ stake`, e
  o `result_k` **nunca** é a odd.
- **Perdida** (`…4829`): `k` = 10,781, `total_k` = **10,268** e `bonus.total_multiplier` = **`"1"`**.
  O card estampa **10.268**: na perdida o boost não valeu, e a casa registra isso no multiplicador.
- **Aberta** (`…4380`): `k` = 12,285 com multiplicador 1,05 — o potencial (307,13) já inclui o boost.

O bloco emite `Bônus aplicado: {…}` para a IA saber que a odd tem boost.

---

## 7. Cashout

A casa tem cashout e aba própria (`count: 0` nesta conta). ⚠️ **`cashout_amount` vem preenchido
em bilhete ABERTO** (`…9072`: 48 sobre aposta de 50) e é **oferta de venda**, não retorno; o
bloco só emite `Cashout executado:` em bilhete resolvido. Quando um cashout real aparecer, vale a
regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`).

---

## 8. Bônus

`bonus` = ComboBOOST (§6). `freebet_data` **sem caso** na amostra; se vier, o bloco emite
`Freebet:` para a IA decidir pelo global.

---

## 9. Mapa de mercados (Betpanda → `Aposta` global)

⚠️ **O dicionário do tenant é PORTUGUÊS DE PORTUGAL, parcial, e o resto chega em INGLÊS**, no
mesmo lote: `1ª parte - handicap`, `remate à baliza`, `Hipótese dupla`, `Basquetebol`, `Andebol`
ao lado de `1st half - total`, `Basketball`, `Ice Hockey`. Traduza o termo, nunca a grafia de
nome próprio.

Só os mercados **confirmados** no dado real (camada fina):

| Betpanda exibe | Aposta global |
|---|---|
| `Vencedor` · `1x2` | ML |
| `Handicap` · `Handicap pontos` · `Handicap (incl. prolongamento)` · `Handicap de jogos` | Handicap |
| `Total pontos` (badminton) | Pontos |
| `Hipótese dupla` | Dupla Chance |
| `Empate anula aposta` | DNB |
| `… Qualifying H2H <piloto> vs <piloto>` (F1) | H2H |
| `<jogador> total points + rebounds + assists` · `total bases` · `total receções` · `total de remates à baliza` | Player Props |

> Badminton domina a amostra (22 de 69 pernas) e segue o `MASTER_APOSTAS §Badminton`, como na
> [`CASA_JONBET §9`](CASA_JONBET.md). Os demais (totais de time, de quarto, de parte, cartões e
> cantos) seguem o global sem tradução fina aqui.

---

## 10. Stake

Campo `sum` (⚠️ **não** `stake`), string com **ponto** decimal, **em dólar**. Nunca passar pelo
parser de dinheiro BR. A conversão para R$ é do `/salvar`, pela moeda da conta (§1.1).

---

## 11. Odds

- **Perdida simples:** `total_k` = `"0"`, a odd do card está em `k` (6,80 ⇄ `k` 6.8).
- **Perdida múltipla:** `total_k` às vezes zera (`…4089`: 0, card 3.422 = `k`) e às vezes não
  (`…1085`: 7.59, card 7.59). A regra de três degraus do `_oddDeclJB`
  ([`CASA_BLAZE §11.1`](CASA_BLAZE.md)) cobre os dois: `total_k` se ≠ 0, senão `k`.
- **Sistema 2/3** (`…5814`): `k` = 12,608 é a **soma** das 3 combinações e `total_k` = 37,825 o
  produto das pernas; stake 36 ÷ 3 = 12 por combinação × 12,608 = **151,30**, o retorno do card.
  A odd do `W` é `retorno ÷ stake`.
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- Long-poll `api/v4/live|prematch/...` e `auth_side` a cada ~2 s — não é bilhete.
- `bet-builder/brand/.../sport/31` voltando 404 — é o widget de criar aposta, não a lista.
- `currency_details`, `market_id`, `outcome_id`, `sport_id`, `specifiers`.
- Contador de cashback semanal, banners e o painel `Boletim`.

---

## 13. Pegadinhas (resumo rápido)

1. **A moeda é da CONTA** — a API diz `$` para carteira Tether (§1.1).
2. **`total_k` zera na perdida simples, mas não sempre na múltipla** (§11).
3. **Boost: `k` com boost, `result_k` sem; na perdida vale o `total_k` do card** (§6).
4. **`cashout_amount` em aberta é oferta** (§7).
5. **`timestamp` em segundos e com fração** (§4).
6. **Stake é `sum`, em dólar** (§10).
7. **Data do EVENTO, não da colocação** (§4).
8. **Mercado em pt-PT e em inglês no mesmo lote** (§9).
9. **`/sports` é 404**: o sportsbook mora em `/sportsbook/` (§2.1).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada com a moeda certa (USD ou USDT) **antes** da 1ª captura.
- [ ] Nenhuma perdida com odd zerada.
- [ ] Na múltipla com boost, a odd do `W` explica o `Ganhaste` (com boost), nunca o `result_k`.
- [ ] Coluna Data = data do **evento**.
- [ ] Contagem capturada == `count` da API (== o que a aba `Todas` mostra).
- [ ] Código de 19 dígitos presente em todo bilhete.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 03/10/2026 — conta inteira (**45 bilhetes**, `status` vazio, 3 páginas):
`extensor/harness/fixtures/betpanda.my_bets.json`.

| ID (final) | Tipo | Status | Stake ($) | Odd | Colocação | Evento | Retorno ($) | Fonte |
|---|---|---|---|---|---|---|---|---|
| …248251 | Simples | GANHA | 70,00 | 1,8 | 02/10 20:28 | 03/10 06:30 | **126,00** | card |
| …066843 | Simples | GANHA | 70,18 | 1,9 | 01/10 22:53 | 02/10 11:55 | **133,34** | card |
| …651739 | 2/2 | GANHA | 25,00 | 1,83 | 01/10 13:14 | 02/10 13:00 | **45,75** | card |
| …308141 | 3/3 boost | GANHA | 2,66 | 9,004 | 01/10 12:23 | 01/10 23:00 | 23,95 | card + json |
| …615814 | Sistema 2/3 | GANHA | 36,00 | 151,30 ÷ 36 | 01/10 12:22 | 01/10 23:00 | **151,30** | card |
| …802582 | Simples | PERDIDA | 15,00 | 6,8 | 03/10 01:29 | 03/10 01:30 | 0 | card |
| …834099 | 2/2 | PERDIDA | 25,00 | 3,422 | 02/10 23:18 | 03/10 12:00 | 0 | card |
| …673908 | 2/2 | PERDIDA | 25,00 | 7,59 | 02/10 21:37 | 03/10 02:00 | 0 | card |
| …074829 | 3/3 boost | PERDIDA | 25,00 | 10,268 | 01/10 15:52 | 02/10 15:45 | 0 | card |
| …109072 | Simples | ABERTA | 50,00 | 2 | 03/10 10:03 | 03/10 10:30 | (100,00 pot.) | json |

**Sem amostra:** cashout executado · devolvida · cancelada · freebet · `half-won`/`half-lost` ·
imposto > 0.

---

## Feedback para a camada global / MODELO

1. **A quarta casa BetBy entrou sem uma linha de captura nova** — o host fora do padrão
   (`api-a-…`) confirmou o acerto de casar por PATH.
2. **Primeira casa de captura em outra moeda.** O rótulo de dinheiro do formatador deixou de ser
   "R$" fixo (`_dinJB`), sem mudar um byte das casas em real.
3. **Boost com multiplicador gravado no bilhete** (`bonus.total_multiplier`): `"1"` na perdida
   diz que o boost não valeu. Vale olhar se outros motores registram isso.
