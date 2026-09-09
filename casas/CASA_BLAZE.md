# CASA_BLAZE
## Camada de tradução — Blaze → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Blaze.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Blaze` · site: `blaze.bet.br` · sportsbook em `/pt/sports`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `currency: "R$"` e a query pede `currency=BRL`
- **Decimal na API: PONTO** (`"10.03"`, `"1.96"`) → normalizar para vírgula.
- Motor: **BetBy** (`sptpub.com`), tenant `blaze`. ⚠️ **Não é iframe** — o `bt-renderer` monta
  o app na própria página; mas aqui ele monta **dentro de um shadow root** (§2.3).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia medida antes de registrar (s336), como manda a regra retroativa do
> `_CASA_DISPLAY`.** A base já usava a casa por print e a grafia é **única** em toda parte:
> `Blaze` em `bilhetes` (86), `parceiros` (3), `casas_meta` (4), `correcoes` (92),
> `uso_tokens` (10) e `tipsters.casas`. Round-trip fecha em identidade — este registro não
> move conta nenhuma de lugar, ao contrário do que a Jonbet pagou na s249.

### 1.1 Espelho da Jonbet/Betboom — o que isso significa na prática  ⭐

A Blaze é a **terceira casa técnica** do mesmo motor: mesmo endpoint, mesmos nomes de campo,
mesmas armadilhas. Muda o domínio, a cor — e nem o cluster, desta vez.

Não foi assumido — foi **provado no reconhecimento, antes de escrever código**:

| Prova | Blaze | Jonbet | Betboom |
|---|---|---|---|
| `bt-renderer` na própria página | `blaze.sptpub.com` | `jonbet.sptpub.com` | `betboombr.sptpub.com` |
| bundle do motor | `start31.sptpub.com` | `start31.sptpub.com` | `start32.sptpub.com` |
| host da API | `api-31-sp-c7818b61-584` | `api-31-sp-c7818b61-584` | `api-32-sp-c7818b61-598` |
| **hash do operador** | `c7818b61` | `c7818b61` | `c7818b61` — **o mesmo nos três** |
| `GET /api/v1/my_bets/list` | idêntico | idêntico | idêntico |
| topo da resposta | `{results, count}` | idem | idem |
| `status` vazio = todas as abas | confirmado (`count: 165`) | confirmado | confirmado |
| paginação por `skip`, fim por `count` + lista vazia | provado ao vivo | provado ao vivo | provado ao vivo |

> ⚠️ **A Blaze divide cluster E host de API com a Jonbet** (`api-31-…-584`). Isso reforça o
> desenho, não o quebra: o `RX` do inject casa por **PATH** (`/my_bets/list`) e o arquivo não
> cita host nenhum — quem separa uma casa da outra é a ABA em que o operador está, não a URL.

Consequência de engenharia: a captura usa o **mesmo `extensor/jb_inject.js`**, o mesmo
`formatTicketJB` e o mesmo `roboJBPassive`, sem uma linha duplicada. O harness tem caso
próprio (`casos/blaze.mjs`) rodando a fixture **da Blaze** contra o card **da Blaze**.

> **Ao mexer numa das três, confira as outras duas.** Toda armadilha registrada aqui vale para
> Jonbet e Betboom, e vice-versa — a do §11.1 nasceu aqui e conserta as três.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/jb_inject.js`, compartilhado).

```
GET https://api-31-sp-c7818b61-584.sptpub.com/api/v1/my_bets/list
    ?currency=BRL&lang=pt-BR&limit=15&skip=0&status=<enum|vazio>&timestamp_from&timestamp_to
    Authorization: Bearer <token da sessão BetBy>
→ { "results": [ … ], "count": <total do filtro> }
```

A lista vive em `blaze.bet.br/pt/sports?bt-path=/bets` — sidebar **"As Minhas Apostas"**.

As consequências de desenho são as da [`CASA_JONBET §2.1`](CASA_JONBET.md). **Repetidas aqui só
onde a medição da Blaze acrescenta algo:**

- ⚠️ **A casa IGNORA o `limit` pedido.** Varredura ao vivo com `limit=100` sobre 165 bilhetes:
  vieram **21 por página**, oito páginas (21×7 + 18), `count` constante em 165, sem id repetido
  nem pulado. Quem avançar o `skip` pelo `limit` **pedido** pula 79 bilhetes por página. O
  `jb_inject` avança pelo tamanho que **voltou** — é por isso que ele se autocorrige.
- **`status` vazio = todas as abas**, confirmado ao vivo (`count: 165`).
- A 1ª chamada sem token (401) **não foi capturada** aqui — o gancho do recon entrou depois do
  load. A guarda existe no inject e é compartilhada.

> **Por que o F12 parece vazio:** o tráfego útil sai em `sptpub.com`, não em `blaze.bet.br`, e
> fica soterrado sob um long-poll `api/v4/live|prematch` a cada ~2 s. Filtre o Network pelo
> **path** (`my_bets`), nunca pelo domínio da casa.

### 2.2 Abas da tela (e o que elas revelam do enum)

`Todas · Apostas abertas · Ganhas · Perdidas · Cashout efetuado · Canceladas · Reembolsadas`.

⚠️ **O filtro da aba "Cashout efetuado" manda `status=cashed_out` — com UNDERSCORE**, medido no
recon. A [`CASA_JONBET §5`](CASA_JONBET.md) registra o valor do enum do bilhete como
`cashed out`, **com espaço**. São dois vocabulários possivelmente distintos (filtro de query ×
campo do registro) e **nenhum bilhete de cashout foi cruzado com a tela aqui** — por isso o §5
lista as duas formas. Rótulo que ninguém cadastrou não vira resultado: sobe como "a conferir".

Há ainda um filtro de período (`Hoje · Semana passada · Últimos 30 dias · Últimas Apostas ·
Personalizado`) que alimenta `timestamp_from`/`timestamp_to`. **O "Personalizado" travou
carregando** nas duas tentativas do recon — não é caminho confiável para achar bilhete antigo.

### 2.3 Layout do bilhete

⚠️ **O app do BetBy vive dentro de um SHADOW ROOT nesta casa** — `document.body.innerText` traz
~2,9 KB de casca e **nenhum bilhete**. Isso não atrapalha a captura (o inject engancha
`window.fetch` no mundo MAIN, antes do DOM), mas **mata qualquer leitura por texto**: aqui o
robô genérico não degradaria, ele mandaria a casca para a IA. É mais um motivo para esta casa
nunca ter fallback de texto.

Cards em grid de 3 colunas. Cabeçalho com `SIMPLES` + data/hora **da colocação** + selo
(`GANHA` / `PERDIDA` / `CANCELADA` / `REEMBOLSADA`). Abaixo, data/hora **do evento**, liga e
confronto; depois seleção, `Total de odds`, `Aposta`, `Você ganhou` / `Reembolso`, e o
`ID da aposta:`.

---

## 2.5 Campos da API (o que o inject entrega)

Mesma tabela da [`CASA_JONBET §2.5`](CASA_JONBET.md). O que a amostra da Blaze **confirmou por
medição própria** (165 bilhetes varridos, 5 cards lidos verbatim na tela):

| Campo | Confirmado na Blaze |
|---|---|
| `sum` (stake, string com ponto) | `"3"`, `"10.03"`, `"132"` — bate com `Aposta R$ …` do card |
| `total_k` | **`"0"` em 86 de 86 perdidas** (100%) |
| `k` | guarda a odd do card quando `total_k` zera — **exceto em 4 bilhetes (§11.1)** |
| `result_k` | **também zera** na perdida — não serve de fallback |
| `result_sum` | `"0"` na perdida · `"5.88"` / `"639.48"` nas ganhas · `= sum` em refund/canceled |
| `timestamp` | epoch em **SEGUNDOS**, float, já local de São Paulo (bate ao minuto com o card) |
| `desc.scheduled` | epoch em segundos — vira a coluna Data (§4) |
| `currency_details` | `{sign_before_value, cents}` — formatação, ignorar |
| `is_bet_builder` | `true` em 1 de 165 |
| `count` (raiz) | fim autoritativo da paginação |

**Ausentes em toda a amostra** (a conta não tinha o caso): `potential_win`, `cashout_amount`,
`cashout{}`, `taxes`, `freebet_data`, `bonus`, `boost`, `combinations`.

---

## 3. ID do bilhete

- Formato: **numérico, 19 dígitos** (ex.: `2550618250014765290`), exibido no card como
  `ID da aposta: …`.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.

> ⚠️ Como Jonbet e Betboom, a Blaze fica **fora do snap por edit-distance** do
> `repository.corrigir_codigos_tsv` — nenhuma das três regexes de lá casa 19 dígitos, e é assim
> que deve continuar: os ids do BetBy são quase idênticos entre si, e um snap por semelhança
> trocaria o código de um bilhete pelo do vizinho. A conferência de cobertura continua ligada
> pelo marcador genérico `[Código: …]`.

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente), como manda o `MASTER_OUTPUT §4`.

Nesta casa a divergência entre colocação e evento aparece **nos dois sentidos**, e é isso que a
torna instrutiva:

- `…968006`: colocada **01/04 12:41**, jogo em **06/04 06:00** — cinco dias depois;
- `…767391`: colocada **19/04 14:30**, jogo em **19/04 13:30** — uma hora **antes**, porque é
  aposta ao vivo.

O bloco capturado emite **as duas**, com `Data (evento mais recente):` primeiro. `timestamp` e
`scheduled` são epoch em **segundos** e já saem em horário de Brasília — multiplicar por 1000 e
mais nada; converter fuso aqui pula um dia.

---

## 5. Status e Resultado

| `status` | Leitura | Código |
|---|---|---|
| `open` | Em aberto | *(vazio — não liquidar)* |
| `won` | Ganhou (selo `GANHA`) — conferir o dinheiro | `W` |
| `lost` | Perdeu (selo `PERDIDA`) | `L` |
| `refund` | Reembolsada (selo `REEMBOLSADA`) — `result_sum` = `sum` | `V` |
| `canceled` | Cancelada (selo `CANCELADA`) — `result_sum` = `sum` | `V` |
| `half-won` · `half-lost` | Meio ganha / meio perdida | `HW` / `HL` |
| `cashed out` · `cashed_out` ¹ | Cashout executado | regra global (§7) |
| `rejected` · `useless` · `vip-stake-requested` | **Não liquidar** — sobem crus | — |

¹ As duas formas estão listadas de propósito: a Jonbet registrou `cashed out` (espaço) como
valor do enum e a Blaze mostrou `cashed_out` (underscore) como valor do **filtro de query**.
Nenhum bilhete de cashout foi cruzado com a tela em nenhuma das três casas.

Medido na Blaze: **`won` (75) · `lost` (86) · `refund` (1) · `canceled` (3)** em 165. As abas
`Apostas abertas` e `Cashout efetuado` voltaram `count: 0`.

> ⚠️ **Retorno zero só vira `L` quando o status cru concorda.** Um `canceled`/`refund` que
> devolva zero jamais pode virar derrota por dedução.

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho — e
aqui ela fecha sozinha nos dois `V`: `result_sum` = `sum` ⇒ retorno igual à stake ⇒ `V`.

---

## 6. Boost / promoção

`boost` veio **ausente ou `false` em toda a amostra**. Sem bilhete turbinado para cruzar com a
tela. Se aparecer, vale a regra global do `W` (`retorno ÷ stake`), que absorve boost de odd e
de lucro sem precisar conhecer o campo.

---

## 7. Cashout

A casa **tem** cashout e a tela tem aba própria — que voltou **`count: 0`** nesta conta. Nenhum
campo de cashout apareceu no payload dos 165 bilhetes.

⚠️ Vale a lição medida na Betboom: **`cashout_amount` vem preenchido em bilhete ABERTO** e é
**oferta de venda antecipada, não retorno**. O bloco capturado só emite `Cashout executado:` em
bilhete resolvido — o caso do harness da Betboom trava isso, e o código é o mesmo.

Quando um cashout real aparecer, vale a regra global: cashout **=** stake → `V`; cashout **≠**
stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

<!-- TODO: capturar na Blaze um cashout executado, um bilhete aberto, um boost e um sistema. -->

---

## 8. Bônus

`freebet_data` e `bonus` existem no payload do motor; **sem caso na amostra da Blaze**. O bloco
capturado emite `Freebet:` / `Bônus aplicado:` quando vierem, para a IA decidir pelo global.

---

## 9. Mapa de mercados (Blaze → `Aposta` global)

⚠️ **O dicionário do tenant é PARCIAL: mercado sem tradução chega em INGLÊS, mesmo com
`lang=pt-BR`** — e as duas grafias convivem na mesma conta, às vezes na mesma semana. Não é
recorte de data: `Vencedor` aparece em 15/03 e `2 map - 1x2` em 28/03. O mesmo vale para o
esporte (`Soccer`, `Basketball` crus; `Valorant` e `Counter-Strike` são nome próprio).

Só os mercados **confirmados** no dado real (camada fina — mercado nunca visto não entra):

| Blaze exibe | Aposta global |
|---|---|
| `Vencedor` · `Winner` | ML |
| `Handicap` · `Handicap (incl. prorrogação)` | Handicap |
| `Handicap mapas` · `Map handicap` | Handicap |
| `1 map - round handicap` · `2 map - round handicap` | Handicap |
| `2 map - 1x2` | ML |
| `Placar exato (em mapas)` · `Correct score (in maps)` | Outros ⚠️ |

> Os mercados de mapa (`1 map -…`, `2 map -…`) são **recorte de parcial** do mesmo confronto e
> seguem o `MASTER_APOSTAS §Esports`: o objeto é o mapa, não a partida. `2 map - 1x2` é ML do
> mapa 2, não do jogo.

> ⚠️ **`Placar exato` cai em `Outros` porque a taxonomia não tem gaveta para placar
> exato** — nem de mapas, nem de gols. Não inventei categoria aqui: criar uma é decisão do
> Feca e arrasta a propagação inteira do `MASTER_APOSTAS` (§3, §4, §5, §7, §9 e o
> `MASTER_DESCRICAO`). Está levantado no rodapé deste arquivo.

---

## 10. Stake

Campo `sum` (⚠️ **não** `stake`), string com **ponto** decimal, em reais. Nunca passar pelo
parser de dinheiro BR — `"132"` viraria 132 mil. O card mostra em `Aposta R$ 132.00`.

---

## 11. Odds

⚠️ **`total_k` vem `"0"` em toda perdida** — **86 de 86** na amostra, com o card estampando o
valor certo (`Total de odds 1.75` para `total_k: "0"` / `k: "1.75"`). `result_k` acompanha o
zero e **não** serve de resgate. A odd real está em `k`.

### 11.1 ⚠️ Quando `k` TAMBÉM vem zero — a odd que não existe

**Em 4 das 86 perdidas os DOIS campos do topo vêm zerados ao mesmo tempo.** A odd sobrevive
apenas dentro da seleção (`selections[].k`). E o card concorda com a API: a linha
**"Total de odds" aparece VAZIA** — a casa também não tem o número e **não escreve zero
nenhum**.

Parar no `k` gravaria `0` numa coluna Odd. É a família do *"zero não é ausência"*: o `0` passa
em toda checagem de forma porque tem cara de conta feita — e num bilhete **ganho** faria
`stake × (0 − 1)` virar `−1u`. Aqui os quatro são `L`, então o P/L não se move; mas a linha
nasceria mentindo.

Regra (três degraus, `_oddDeclJB` no `content.js`):

```
odd = total_k, se ≠ 0
    → k, se ≠ 0
    → produto das odds das seleções, se TODAS > 0
    → null   (nunca 0)
```

> **O terceiro degrau só pode disparar com os dois primeiros zerados** — e é isso que o separa
> do `refund`/`canceled`, onde a casa achata `k`/`total_k` para **`1`** e o card estampa `1`.
> Ali o produto das seleções (2,5 e 1,5 na fixture) seria invenção nossa por cima da tela. O
> caso do harness trava **os dois lados**: a mutação que faz o produto vencer sempre acende
> sete falhas, duas delas exatamente nos `V`.

### 11.2 Múltipla: a declarada é truncada

`k` vem **truncado em 3 casas** na múltipla — `1.598` para `1,12 × 1,22 × 1,17 = 1,5987` — e o
dinheiro guarda o valor cheio (`result_sum` 639,48 sobre stake 400). Na ganha, a régua global
manda: `Odd = Retorno ÷ Stake`. Gravar a declarada perderia R$ 0,28 de retorno na conta.

Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- Long-poll `api/v4/live|prematch/...` a cada ~2 s — não é bilhete.
- `currency_details` (`sign_before_value`, `cents`) — formatação de exibição.
- `market_id` / `outcome_id` / `sport_id` — ids internos do motor; o que vale é o nome.
- `specifiers` (`hcp=3.5`, `total=71.5`) — a linha já vem legível no `outcome_name`.
- Linha **"Reembolso parcial"** no card dos bilhetes do §11.1: vem **sem valor**, com
  `result_sum: "0"`. É rótulo de template, não dinheiro.
- Portão de idade, banner de cookies e o painel `Cupom` da direita.

---

## 13. Pegadinhas (resumo rápido)

1. **`total_k` = 0 em toda perdida** — use `k` (§11).
2. **`k` também pode ser 0** — aí a odd vem das seleções, e nunca `0` (§11.1).
3. **`refund`/`canceled` achatam a odd para `1`** — e `1` ali é a verdade da tela (§11.1).
4. **A casa ignora o `limit` pedido** — devolve 21 por página (§2.1).
5. **`timestamp` em SEGUNDOS**, não ms (§4).
6. **Stake é `sum`**, string com ponto (§10).
7. **Data do EVENTO, não da colocação** — divergem nos dois sentidos (§4).
8. **O app vive num shadow root** — leitura por texto não enxerga bilhete nenhum (§2.3).
9. **Mercado e esporte podem vir em inglês** no mesmo lote (§9).

---

## 14. Validações específicas

- [ ] Nenhuma perdida com odd zerada (se houver, leu `total_k` ou `k` cru).
- [ ] Nenhum bilhete com `Odd: 0` — ausência sobe vazia, nunca zero.
- [ ] `refund`/`canceled` saem com a odd que o card estampa (`1`), não com o produto das pernas.
- [ ] Coluna Data = data do **evento**; conferir contra a 2ª linha de data do card.
- [ ] `Odd × Stake` explica o `Você ganhou` do card, ao centavo, em todo `W`.
- [ ] Contagem capturada == `count` da API (e == o que a aba `Todas` mostra).
- [ ] Código de 19 dígitos presente em todo bilhete.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 09/09/2026 — varredura completa de **165 bilhetes** (`status` vazio). Fixture com os 8
que cobrem as armadilhas: `extensor/harness/fixtures/blaze.my_bets.json`.

| ID (final) | Tipo | Status | Stake | Odd | Colocação | Evento | Retorno |
|---|---|---|---|---|---|---|---|
| …765290 | Simples | GANHA | 3,00 | 1,96 | 28/06 02:41 | 28/06 15:00 | **5,88** |
| …331668 | 3/3 | GANHA | 400,00 | 1,5987 | 28/03 14:50 | 28/03 23:00 | **639,48** |
| …767391 | Simples | PERDIDA | 132,00 | 1,75 | 19/04 14:30 | 19/04 13:30 | 0 |
| …968006 | Simples | PERDIDA | 10,03 | 1,92 ¹ | 01/04 12:41 | 06/04 06:00 | 0 |
| …964347 | Simples | REEMBOLSADA | 111,00 | 1 | 19/04 13:43 | 19/04 12:00 | 111,00 |
| …249307 | Simples | CANCELADA | 156,00 | 1 | 15/03 19:13 | 16/03 16:00 | 156,00 |
| …729604 | 4/4 | PERDIDA | 15,27 | 10,841 | 08/03 12:29 | 08/03 22:00 | 0 |
| …559611 | 6/6 · bet builder | PERDIDA | 200,00 | 7,572 | 01/03 18:53 | 02/03 11:30 | 0 |

¹ **Odd derivada da seleção** — `total_k` e `k` vieram `"0"` e o card mostra o campo vazio
(§11.1).

**Procedência:** cinco cards foram lidos verbatim na tela. Os três de março (`…331668`,
`…729604`, `…559611`) estão ~100 posições abaixo na lista e o filtro "Personalizado" da casa
travou — para eles o esperado veio do próprio corpo da resposta, que nos cinco lidos bateu com
o card ao centavo. Está declarado no cabeçalho de `casos/blaze.mjs` em vez de fingir leitura.

**Sem amostra:** aposta **aberta** · **cashout** executado · **boost** · **freebet** · bilhete
de **sistema** (`combinations` vazio em 165 de 165) · `half-won`/`half-lost` · imposto > 0.

---

## Feedback para a camada global / MODELO

1. **A terceira casa BetBy entrou sem uma linha de captura nova**, como previa a
   [`CASA_BETBOOM`](CASA_BETBOOM.md). O critério de detecção (`bt-renderer` de `*.sptpub.com`
   na própria página) funcionou **sem login e sem clicar em nada** — vale manter como primeiro
   passo de todo recon.
2. **O degrau que faltava na odd nasceu aqui e conserta as três casas.** A Jonbet e a Betboom
   nunca tiveram bilhete com `k` e `total_k` zerados juntos nas fixtures delas — a mutação que
   prova o gate da Blaze passa **inócua** nas duas. Espelho compartilha o conserto; não
   compartilha a prova.
3. **Shadow root muda o custo do fallback, não da captura.** Vale registrar no guia: casa cujo
   motor renderiza em shadow DOM **nunca** pode ter fallback de texto, porque o robô genérico
   não falha — ele manda a casca para a IA.
4. **`Placar exato` não tem gaveta na taxonomia.** Nem de mapas (e-sports), nem de gols
   (futebol) — hoje cai em `Outros`, que é último recurso, e some das análises por mercado.
   É um mercado comum em toda casa; vale decidir se merece categoria própria antes que o
   `Outros` engorde. **Não criei nada aqui** — categoria nova é decisão com propagação.
5. **Imposto continua indefinido nas três casas.** Quando `payout_tax > 0` aparecer, decidir de
   uma vez se o `W` usa retorno **bruto** ou **líquido**, valendo para Jonbet, Betboom e Blaze.
