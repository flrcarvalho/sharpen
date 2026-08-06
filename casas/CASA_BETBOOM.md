# CASA_BETBOOM
## Camada de tradução — Betboom → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betboom.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betboom` · site: `betboom.bet.br`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `currency: "R$"` e a query pede `currency=BRL`
- **Decimal na API: PONTO** (`"350"`, `"1.87"`) → normalizar para vírgula.
- Motor: **BetBy** (`sptpub.com`), tenant `betboombr`. ⚠️ **Não é iframe** — o
  `bt-renderer.min.js` monta o app na **própria página**, então o `content.js` alcança tudo.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> ⚠️ **A MARCA escreve "BetBoom"; a canônica do sistema é `Betboom`.** Não é descuido — foi
> **medido antes de registrar** (s250): a base já tinha **172 bilhetes**, 3 contas (Feca,
> Jonathan, Diogo) e 3 perfis de tipster nessa grafia. Registrar uma casa no `_CASA_DISPLAY`
> é mudança **retroativa** — ela reinterpreta toda conta que já existe na grafia gêmea, e foi
> exatamente assim que a Jonbet quebrou na s249 (conta `JonBet`, bilhete `Jonbet`, grade
> vazia). Adotar a grafia da marca aqui custaria 172 recálculos de assinatura em duas bases.

### 1.1 Espelho da Jonbet — o que isso significa na prática  ⭐

A Betboom é a **mesma casa técnica** que a [`CASA_JONBET`](CASA_JONBET.md): mesmo motor, mesmo
endpoint, mesmos nomes de campo, mesmas armadilhas. Muda o domínio, o cluster e a cor.

Não foi assumido — foi **provado no reconhecimento, antes de escrever código**:

| Prova | Betboom | Jonbet |
|---|---|---|
| `bt-renderer.min.js` na própria página | `betboombr.sptpub.com` | `jonbet.sptpub.com` |
| bundle do motor | `start32.sptpub.com` | `start31.sptpub.com` |
| host da API | `api-32-sp-c7818b61-598` | `api-31-sp-c7818b61-584` |
| **hash do operador** | `c7818b61` | `c7818b61` — **o mesmo** |
| `GET /api/v1/my_bets/list` | idêntico | idêntico |
| topo da resposta | `{results, count}` | `{results, count}` |
| `status` vazio = todas as abas | confirmado (`count: 7`) | confirmado |
| paginação por `skip`, fim por `count` + lista vazia | provado ao vivo | provado ao vivo |

Consequência de engenharia: a captura usa o **mesmo `extensor/jb_inject.js`**, o mesmo
`formatTicketJB` e o mesmo `roboJBPassive`, sem uma linha duplicada — o `RX` do inject casa por
**PATH** (`/my_bets/list`), nunca por host, e é isso que permite o compartilhamento. O harness
tem caso próprio (`casos/betboom.mjs`) rodando a fixture **da Betboom** contra o card **da
Betboom**: se alguém amarrar o código a um host ou a um cluster, fica vermelho.

> **Ao mexer numa das duas, confira a outra.** Toda armadilha registrada aqui vale para a
> Jonbet e vice-versa. **BetBy é plataforma, não casa:** qualquer outra casa que carregue
> `sptpub.com` entra pelo mesmo caminho, como a Betfast é da Tivo.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/jb_inject.js`, compartilhado com a Jonbet).

```
GET https://api-32-sp-c7818b61-598.sptpub.com/api/v1/my_bets/list
    ?currency=BRL&lang=pt-BR&limit=15&skip=0&status=<enum|vazio>&timestamp_from&timestamp_to
    Authorization: Bearer <token da sessão BetBy>
→ { "results": [ … ], "count": <total do filtro> }
```

A lista vive em `betboom.bet.br/sport/bets` (4º ícone da barra lateral do sportsbook).

As cinco consequências de desenho são as da [`CASA_JONBET §2.1`](CASA_JONBET.md) — host de
outra origem, 401 antes do token, lista de 15 em 15, abas no parâmetro `status`, fim por
`count`. **Repetidas aqui só onde a medição da Betboom acrescenta algo:**

- **Paginação provada nesta casa**, forçando `limit=3` sobre os 7 bilhetes: `skip` 0/3/6 →
  3, 3, 1 (soma exata de `count`, sem id repetido nem pulado), `count` constante entre
  páginas, e **`skip=9` devolve 200 com lista VAZIA** — nunca erro, nunca repetição.
- **`status` vazio = todas as abas**, confirmado ao vivo (`count: 7` com as 7 linhas).

> **Por que o F12 parece vazio:** o tráfego útil sai em `sptpub.com`, não em `betboom.bet.br`,
> e fica soterrado sob um long-poll `api/v4/live|prematch` que dispara a cada ~2 s. Filtre o
> Network pelo **path** (`my_bets`), nunca pelo domínio da casa.

### 2.2 Abas da tela (e o que elas revelam do enum)

`Todas · Apostas abertas · Ganhas · Perdidas · Cashout efetuado · Canceladas · Reembolsadas`.

A tela da Betboom **nomeia em pt-BR** estados que na Jonbet só existiam no enum do bundle —
`cashed out`, `canceled` e `refund` têm rótulo visível aqui. Isso **corrobora** o de-para do
§5, mas não o confirma: as três abas vieram **vazias** nesta conta.

### 2.3 Layout do bilhete

Cards em grid de 3 colunas. Cabeçalho com `SIMPLES` + data/hora **da colocação** + selo
(`ABERTA` / `GANHA` / `PERDIDA`). Abaixo, a data/hora **do evento** em linguagem relativa
(`Amanhã, 01:40` · `Hoje, 01:05`), liga e confronto; depois seleção, `Total de odds`, `Aposta`
e `Ganho potencial` / `Você ganhou`, e o `ID da aposta:`. **Não** há linha em branco entre
bilhetes — por isso a casa nunca pode cair no robô de texto genérico (lição da KTO, s192).

---

## 2.5 Campos da API (o que o inject entrega)

Idênticos aos da [`CASA_JONBET §2.5`](CASA_JONBET.md) — mesma tabela, campo a campo. O que a
amostra da Betboom **confirmou por medição própria**:

| Campo | Confirmado na Betboom |
|---|---|
| `sum` (stake, string com ponto) | `"350"`, `"100"`, `"700"` — bate com `Aposta R$ …` do card |
| `total_k` | **`"0"` em 2 de 2 perdidas**, com o card estampando 1.87 e 1.71 |
| `k` | guarda a odd do card quando `total_k` zera |
| `result_k` | **também zera** na perdida — não serve de fallback |
| `result_sum` | `"0"` na perdida · `"906"` / `"1060"` nas ganhas · **ausente** na aberta |
| `potential_win` | só na aberta |
| `timestamp` | epoch em **SEGUNDOS**, float (`1786038358.121739`) |
| `desc.scheduled` | epoch em segundos — vira a coluna Data (§4) |
| `cashout_amount` + `cashout{}` | **preenchidos em bilhete ABERTO** (§7) |
| `cashout.payout_tax` | `"0"` · `taxes` **ausente** |
| `boost` | `false` em toda a amostra |
| `count` (raiz) | fim autoritativo da paginação |

---

## 3. ID do bilhete

- Formato: **numérico, 19 dígitos** (ex.: `2696881722674520125`), exibido no card como
  `ID da aposta: …`.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.

> ⚠️ Como a Jonbet, a Betboom fica **fora do snap por edit-distance** do
> `repository.corrigir_codigos_tsv` — nenhuma das três regexes de lá casa 19 dígitos, e é
> assim que deve continuar: os ids do BetBy são quase idênticos entre si, e um snap por
> semelhança trocaria o código de um bilhete pelo do vizinho. A conferência de cobertura
> continua ligada pelo marcador genérico `[Código: …]`.

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente), como manda o `MASTER_OUTPUT §4` — e é a
que o card estampa no bloco branco.

> ⚠️ **Nesta casa a colocação e o evento caem em dias diferentes em 7 de 7 bilhetes.** Não é
> exceção, é o padrão: badminton coreano de madrugada apostado na tarde anterior (colocada
> `06/08 14:45` → jogo `07/08 01:40`). Na Jonbet a divergência já era de 7 em 10; aqui é
> **total**. Emitir a data de colocação poria a base **inteira** no dia errado — o defeito que
> a VaideBet levou a produção na s210.

O bloco capturado emite **as duas**, com `Data (evento mais recente):` primeiro. `timestamp` e
`scheduled` são epoch em **segundos** e já saem em horário de Brasília — multiplicar por 1000 e
mais nada; converter fuso aqui pula um dia.

---

## 5. Status e Resultado

De-para idêntico ao da [`CASA_JONBET §5`](CASA_JONBET.md):

| `status` | Leitura | Código |
|---|---|---|
| `open` | Em aberto (selo `ABERTA`) | *(vazio — não liquidar)* |
| `won` | Ganhou (selo `GANHA`) — conferir o dinheiro | `W` |
| `lost` | Perdeu (selo `PERDIDA`) | `L` |
| `half-won` | Meio ganha | `HW` |
| `half-lost` | Meio perdida | `HL` |
| `cashed out` ¹ | Cashout executado (aba `Cashout efetuado`) | regra global (§7) |
| `canceled` · `refund` · `void` | Anulada / devolvida (abas `Canceladas` / `Reembolsadas`) | `V` |
| `rejected` · `useless` · `vip-stake-requested` | **Não liquidar** — sobem crus | — |

¹ **com espaço**, não hífen nem underscore.

Na amostra real da Betboom apareceram **só** `open`, `won` e `lost`. Os demais vêm do enum do
motor; as abas da tela dão nome em pt-BR a três deles (§2.2), mas **nenhum bilhete foi cruzado
com a tela** — enquanto isso não acontecer, sobem crus.

> ⚠️ **Retorno zero só vira `L` quando o status cru concorda.** Um `canceled`/`refund` que
> devolva zero jamais pode virar derrota por dedução.

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho.

---

## 6. Boost / promoção

`boost` existe por seleção e veio **`false` em toda a amostra**. Sem bilhete turbinado para
cruzar com a tela. Se aparecer, vale a regra global do `W` (`retorno ÷ stake`), que absorve
boost de odd e de lucro sem precisar conhecer o campo.

---

## 7. Cashout

A casa **tem** cashout, e a tela tem aba própria (`Cashout efetuado`) — vazia nesta conta.

⚠️ **`cashout_amount` vem PREENCHIDO em bilhete ABERTO.** Medido: o bilhete
`2697202108746305608` está `open` e traz `cashout_amount: "270"` com
`cashout{amount_gross:"270", amount_net:"270", payout_tax:"0"}` — e o card mostra o botão
`CASH OUT R$ 270,00`. **É oferta de venda antecipada, não retorno.** Lê-lo como retorno
transforma toda aposta em aberto numa vitória fantasma (a armadilha do `totalWin` da VaideBet).
Por isso o bloco capturado **só emite `Cashout executado:` em bilhete resolvido** — e o caso do
harness trava exatamente isso neste bilhete.

Quando um cashout real aparecer, vale a regra global: cashout **=** stake → `V`; cashout **≠**
stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

**Imposto:** `payout_tax` veio `"0"` e `taxes` está **ausente** em toda a amostra.

<!-- TODO: capturar um bilhete com cashout executado, um anulado e um com imposto > 0. -->

---

## 8. Bônus

`freebet_data`, `bonus` e `bonus_id` existem no payload; **sem caso na amostra**. O bloco
capturado emite `Freebet:` / `Bônus aplicado:` quando vierem, para a IA decidir pelo global.

---

## 9. Mapa de mercados (Betboom → `Aposta` global)

Só os mercados **confirmados** no dado real (camada fina — mercado nunca visto não entra):

| Betboom exibe | Aposta global |
|---|---|
| `Vencedor` | ML |
| `Handicap pontos` | Handicap |

> Os dois são de **badminton** e seguem o `MASTER_APOSTAS §Badminton`: resultado sem handicap
> → `ML`; com handicap → `Handicap`. A Jonbet já confirmou também `Total pontos` → `Pontos`;
> ele **não** entra aqui porque não apareceu em bilhete da Betboom. Atenção à fronteira: total
> de **parciais** (games/sets) é `Sets`, não `Pontos`.

---

## 10. Stake

Campo `sum` (⚠️ **não** `stake`), string com **ponto** decimal, em reais. Nunca passar pelo
parser de dinheiro BR — `"350"` viraria 350 mil. O card mostra em `Aposta R$ 350,00`.

---

## 11. Odds

⚠️ **`total_k` vem `"0"` em toda perdida** — 2 de 2 na amostra, com o card estampando
`Total de odds 1.87` e `1.71`. `result_k` acompanha o zero e **não** serve de resgate. A odd
real está em `k`.

Regra (a mesma que o app da própria casa aplica):

```
odd = parseFloat(total_k) === 0 ? k : total_k
```

Ler `total_k` cru gravaria **odd zero em 100% das perdas** — é o `betOdds` da KTO em outra
roupa. O caso do harness tem controle negativo para isso.

Na ganha, a régua global manda: `Odd = Retorno ÷ Stake`. Confere nas duas
(`300 × 3,02 = 906` · `500 × 2,12 = 1060`). Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- Long-poll `api/v4/live|prematch/...` a cada ~2 s — não é bilhete.
- `currency_details` (`sign_before_value`, `cents`) — formatação de exibição.
- `market_id` / `outcome_id` / `sport_id` — ids internos do motor; o que vale é o nome.
- `specifiers` (`hcp=0.5`) — a linha já vem legível no `outcome_name`.
- Banner de cookies, portão de idade e o painel `Cupom` da direita.

---

## 13. Pegadinhas (resumo rápido)

1. **`total_k` = 0 em toda perdida** — use `k` (§11).
2. **`timestamp` em SEGUNDOS**, não ms (§4).
3. **Stake é `sum`**, string com ponto (§10).
4. **`cashout_amount` preenchido na ABERTA** — é oferta, não retorno (§7).
5. **Data do EVENTO, não da colocação** — divergem em 7 de 7 (§4).
6. **Grafia `Betboom`**, não `BetBoom` (§1).
7. A 1ª chamada da página sai **sem token** e volta 401 com um corpo que **tem** uma chave
   `status` — que não é status de bilhete.

---

## 14. Validações específicas

- [ ] Nenhuma perdida com odd zerada (se houver, leu `total_k` cru).
- [ ] Coluna Data = data do **evento**; conferir contra o `Amanhã/Hoje, HH:MM` do card.
- [ ] `Odd × Stake` explica o `Você ganhou` do card, ao centavo, em todo `W`.
- [ ] Bilhete `open` nunca sai com `Cashout executado:`.
- [ ] Contagem capturada == `count` da API (e == o que a aba `Todas` mostra).
- [ ] Código de 19 dígitos presente em todo bilhete.

---

## 15. Exemplos golden (bilhetes reais)

Amostra do reconhecimento (06/08/2026, conta do Feca, 7 bilhetes — todos **simples**, todos
badminton do Korea Masters). Fixture: `extensor/harness/fixtures/betboom.my_bets_all.json`.

| ID (final) | Status | Stake | Odd | Colocação | Evento | Retorno |
|---|---|---|---|---|---|---|
| …395133 | ABERTA | 350,00 | 1,87 | 06/08 14:45 | 07/08 01:40 | — |
| …400179 | ABERTA | 100,00 | 5 | 06/08 14:30 | 07/08 05:00 | — |
| …305608 | ABERTA | 300,00 | 2,72 | 06/08 14:29 | 07/08 01:40 | oferta de cashout R$ 270 |
| …663332 | PERDIDA | 500,00 | 1,87 | 05/08 18:02 | 06/08 01:05 | 0 |
| …883758 | PERDIDA | 700,00 | 1,71 | 05/08 17:18 | 06/08 01:30 | 0 |
| …520125 | GANHA | 300,00 | 3,02 | 05/08 17:16 | 06/08 02:30 | **906,00** |
| …138910 | GANHA | 500,00 | 2,12 | 05/08 17:10 | 06/08 01:55 | **1.060,00** |

**Sem amostra** (herdado da Jonbet, e a Betboom **não** fechou nenhum): cashout executado ·
múltipla · bet builder · sistema · `half-won`/`half-lost` · `void`/`refund`/`rejected` · boost ·
imposto > 0.

---

## Feedback para a camada global / MODELO

1. **BetBy é plataforma, não casa.** Jonbet e Betboom já são duas; a terceira que aparecer
   deve entrar por este mesmo caminho, sem código novo. O critério de detecção é o
   `bt-renderer.min.js` de `*.sptpub.com` carregado na própria página.
2. **Registrar casa no `_CASA_DISPLAY` é mudança retroativa.** Medir a grafia que já existe no
   banco tem de ser passo obrigatório do cadastro, não zelo opcional (§1). A s249 pagou essa
   conta na Jonbet; a Betboom só não pagou porque foi medida antes.
3. **Imposto continua indefinido nas duas casas.** Quando `payout_tax > 0` aparecer, decidir de
   uma vez se o `W` usa retorno **bruto** ou **líquido** — e valer para Jonbet e Betboom juntas.
