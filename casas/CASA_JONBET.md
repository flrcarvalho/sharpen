# CASA_JONBET
## Camada de tradução — Jonbet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Jonbet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Jonbet` · site: `jonbet.bet.br`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `currency: "R$"` e a query pede `currency=BRL`
- **Decimal na API: PONTO** (`"333.16"`, `"1.87"`) → normalizar para vírgula.
- Motor: **BetBy** (`sptpub.com`). ⚠️ **Não é iframe** — o `bt-renderer.min.js` monta o app na
  **própria página** de `jonbet.bet.br`, então o `content.js` alcança tudo e o inject engancha o
  `fetch` da página (nada do problema do iframe de membros da bet365).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **BetBy é plataforma, não casa.** Qualquer outra casa que carregue `sptpub.com` é **casa
> espelho**: mesmo endpoint, mesmo inject, mesmo formatador — como a Betfast é da Tivo.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/jb_inject.js`).

```
GET https://api-31-sp-c7818b61-584.sptpub.com/api/v1/my_bets/list
    ?lang=pt-BR&skip=0&limit=15&status=<enum|vazio>&timestamp_from=&timestamp_to=&currency=BRL
    Authorization: Bearer <token da sessão BetBy>
→ { "count": <total do filtro>, "results": [ … ] }
```

Cinco consequências que mandam no desenho:

1. **O endpoint é de OUTRA origem** (`api-NN-sp-<hash>.sptpub.com`) e autentica por
   **`Authorization: Bearer`**, não por cookie. O replay reusa os headers da requisição real.
   O host **não pode ser hardcodado**: o `31` é o cluster e a base vem da config da marca.
2. ⚠️ **A 1ª requisição da página sai SEM token e volta 401.** O corpo do erro é
   `{"description":"Unauthorized","status":401,"message":"Unauthorized"}` — repare que ele **tem
   uma chave `status`**, que não é status de bilhete. Aprender essa requisição para o replay faz
   o robô repaginar deslogado e reportar `hook:true` + `respostas>0` + 0 bilhetes, que é o mesmo
   sintoma de "formato mudou". O inject só aprende requisição **com `Authorization`** e só
   processa corpo com `results` array.
3. **A lista NÃO carrega sozinha:** vem de 15 em 15. O robô pagina por `skip` na própria API.
4. **As abas são o parâmetro `status`**, mesma URL. **`status` vazio = todas as abas** — é o
   superconjunto, e é o que o replay usa para garantir o que o operador não clicou.
5. **Fim autoritativo: `count`.** É o total do filtro e é constante entre páginas
   (`skip >= count` → fim). Como rede de segurança, passar do fim devolve **200 com lista
   vazia** — nunca erro, nunca repetição da última página.

> **Por que o F12 parece vazio:** o tráfego útil sai em `sptpub.com`, não em `jonbet.bet.br`, e
> fica soterrado sob um long-poll que dispara `api/v4/live/...` **a cada ~2 s**. Filtre o Network
> pelo **path** (`my_bets`), nunca pelo domínio da casa.

### 2.2 Tipo do bilhete declarado

O campo `type` traz a combinação da casa (`"1/1"` = simples). O tipo do bloco sai da estrutura:

- `combinations` preenchido → **Sistema**;
- `is_bet_builder` (bilhete ou seleção) → **Bet Builder**;
- `selections.length ≥ 2` → **Múltipla**;
- 1 seleção → **Simples**.

> A conta do reconhecimento (s248) só tinha **simples**. Múltipla, bet builder e sistema estão
> cobertos no formato, mas **nunca foram vistos ao vivo** nesta casa.

### 2.3 Layout do bilhete

Cards em **grid de 3 colunas**. Cabeçalho com `SIMPLES` + data/hora **da colocação** + selo de
status (`ABERTA` / `GANHA` / `PERDIDA`). Bloco branco com data/hora **do evento** em linguagem
relativa (`Hoje, 01:05` · `Ontem, 01:35` · `Anteontem, 22:40`), liga e confronto. Depois
`ID da aposta:`, a seleção, `Total de odds`, `Aposta` (= stake) e `Ganho potencial` / `Você
ganhou`. **Não** há linha em branco entre bilhetes — por isso a casa nunca pode cair no robô de
texto genérico (`roboScroll`), que parte o `innerText` por linha em branco (lição da KTO, s192).

---

## 2.5 Campos da API (o que o inject entrega)

| Campo (API) | Significado | Observação |
|---|---|---|
| `id` | ID do bilhete | é o `ID da aposta:` do card · chave de dedup e do `[Código:]` |
| `status` | estado do bilhete | enum bruto em **string** — ver §5 |
| `type` | combinação da casa | `"1/1"` = simples |
| `sum` | **stake** | ⚠️ é `sum`, **não** `stake`. String com ponto (`"333.16"`), em reais |
| `total_k` | **odd total** | ⚠️ **vem `"0"` em TODA perdida** — ver §11 |
| `k` | odd do bilhete | é o fallback quando `total_k` zera; é a odd que o card mostra |
| `result_k` | odd liquidada | acompanha o `total_k`: **também zera na perdida**, não serve de fallback |
| `result_sum` | **retorno realizado** | `"0"` na perdida · **ausente** na aberta |
| `potential_win` | retorno **potencial** | só na aberta — nunca é ganho (§5) |
| `timestamp` | **colocação**, epoch em **SEGUNDOS** (float) | ⚠️ não é ms · ver §4 |
| `selections[].desc.scheduled` | início do evento, epoch em segundos | a **mais recente** vira a coluna Data |
| `selections[].k` | odd da seleção | |
| `selections[].market_name` | mercado, em pt-BR | ver §9 |
| `selections[].outcome_name` | seleção (`Kharb, Anmol (-3.5)`) | |
| `selections[].specifiers` | linha/handicap (`hcp=3.5` · `total=71.5`) | a linha já vem legível no `outcome_name` |
| `selections[].desc.sport.name` | **esporte por extenso** (`Badminton`) | ver §12 |
| `selections[].desc.competitors[]` | confronto | `name` de cada lado |
| `selections[].desc.category.name` / `.tournament.name` | país/região e liga | `International` / `Korea Masters, WS` |
| `cashout_amount` / `cashout.amount_net` / `.amount_gross` | cashout | ⚠️ **preenchido na ABERTA** = oferta de venda, não retorno — ver §7 |
| `cashout.payout_tax` / `.payout_tax_rate` | imposto sobre prêmio | **`"0"` em toda a amostra** — ver §7 |
| `taxes.final_payout` | retorno líquido de imposto | **ausente** em toda a amostra; existe na estrutura do motor |
| `freebet_data` / `bonus` / `bonus_id` | freebet e bônus | sem caso na amostra (§8) |
| `count` (raiz) | **fim autoritativo** da paginação | total do filtro, constante entre páginas |

---

## 3. ID do bilhete

- Formato: **numérico, 19 dígitos** (ex.: `2696533322854707365`), exibido no card como
  `ID da aposta: 2696533322854707365`.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.

> ⚠️ **Os ids da Jonbet são quase idênticos entre si** — `…168314475463` e `…168314475401`
> diferem em **3 caracteres**. Por isso a casa fica **fora do snap por edit-distance** do
> `repository.corrigir_codigos_tsv`: nenhuma das três regexes de lá casa 19 dígitos, e é assim
> que deve continuar. Um snap por semelhança trocaria o código de um bilhete pelo do vizinho —
> o mesmo motivo pelo qual a bet365 (ids sequenciais) foi deixada de fora. A conferência de
> cobertura continua ligada pelo marcador genérico `[Código: …]`.

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da seleção mais recente**
(`MASTER_OUTPUT §4`: *"em apostas múltiplas: usar a data da perna mais recente"*).

A Jonbet expõe as duas, e elas **divergem na maioria dos bilhetes**:

- **colocação** — `timestamp`. É o que o **cabeçalho do card** mostra (`5 de ago. de 2026, 18:00`).
  Serve de contexto e de ordem; **não** é a coluna Data.
- **evento** — `selections[].desc.scheduled`, mostrado no bloco branco em linguagem relativa
  (`Hoje, 01:05`). **Usar a mais recente.**

> **Não é detalhe: 7 dos 10 bilhetes da amostra mudam de dia.** É casa de badminton asiático —
> jogo de madrugada apostado na tarde anterior (colocação `05/08 18:00` → evento `06/08 01:05`).
> Usar a colocação gravaria **70% da base no dia errado**. O harness
> (`extensor/harness/casos/jonbet.mjs`) trava as duas leituras, bilhete a bilhete.

**Fuso:** os dois campos são epoch em **segundos** (float, ex.: `1785963619.595635`) →
`× 1000` e formatar em `America/Sao_Paulo`, como todas as outras casas. Ler como milissegundos
joga a data para 1970.

---

## 5. Status e Resultado

De-para do `status` do bilhete (enum em **string**, extraído do bundle do motor):

| `status` | Leitura | Código |
|---|---|---|
| `open` | Em aberto (selo `ABERTA`) | *(vazio — não liquidar)* |
| `won` | Ganhou (selo `GANHA`) — conferir o dinheiro | `W` |
| `lost` | Perdeu (selo `PERDIDA`) | `L` |
| `half-won` | Meio ganha | `HW` |
| `half-lost` | Meio perdida | `HL` |
| `cashed out` ¹ | Cashout executado | regra global (§7) |
| `canceled` · `refund` · `void` | Anulada / devolvida | `V` |
| `rejected` · `useless` · `vip-stake-requested` | **Não liquidar** — sobem crus | — |

¹ **com espaço**, não hífen nem underscore.

Só `open`, `won` e `lost` apareceram em bilhete real. Os demais vêm do enum do motor
(`48535` do bundle) e **nenhum foi cruzado com a tela** — enquanto isso não acontecer, sobem
crus.

> ⚠️ **Retorno zero só vira `L` quando o status cru concorda.** Um `canceled`/`refund` que
> devolva zero jamais pode virar derrota por dedução — o bloco capturado escreve
> `retorno zero com status "<cru>" (a conferir — não liquidar automaticamente)`.

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho.

---

## 6. Boost / promoção

Existe `boost` por seleção no payload (**`false` em toda a amostra**) e não houve bilhete
turbinado para cruzar com a tela. Se aparecer, vale a regra global do `W`
(`retorno ÷ stake`), que absorve boost de odd e de lucro sem precisar conhecer o campo.

---

## 7. Cashout

A casa **tem** cashout — as abertas mostram botão `CASH OUT R$ 184,46`.

⚠️ **`cashout_amount` vem PREENCHIDO em bilhete ABERTO** (é a oferta de venda antecipada, o
valor do botão). Lê-lo como retorno transforma toda aposta em aberto numa vitória fantasma — a
mesma armadilha do `totalWin` da VaideBet. Por isso o bloco capturado **só emite a linha
`Cashout executado:` quando o bilhete está resolvido**; na aberta o campo é omitido de propósito.

Quando um cashout real aparecer, vale a regra global: cashout **=** stake → `V`; cashout **≠**
stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`). A leitura derivada
do dinheiro já resolve os dois casos sozinha.

**Imposto:** `payout_tax` e `payout_tax_rate` vieram **`"0"`** em toda a amostra, e `taxes`
(com `final_payout`) está **ausente**. A estrutura existe no motor; se um dia vier preenchida,
o líquido manda — é o que o jogador recebe e o que o card estampa.

<!-- TODO: capturar um bilhete com cashout executado e um com imposto > 0, e travar no harness. -->

---

## 8. Bônus

`freebet_data`, `bonus` e `bonus_id` existem no payload; **sem caso na amostra**. O bloco
capturado emite `Freebet:` / `Bônus aplicado:` quando vierem, para a IA decidir pelo global.

---

## 9. Mapa de mercados (Jonbet → `Aposta` global)

Só os mercados **confirmados** no dado real (camada fina — mercado nunca visto não entra aqui):

| Jonbet exibe | Aposta global |
|---|---|
| `Vencedor` | ML |
| `Handicap pontos` | Handicap |
| `Total pontos` | Pontos |

> Os três são de **badminton**, e seguem o `MASTER_APOSTAS §Badminton`: resultado sem handicap
> → `ML`; com handicap → `Handicap`; total de **pontos** → `Pontos`. Atenção à fronteira: total
> de **parciais** (games/sets) é `Sets`, não `Pontos` (§9 da validação, item 18).

---

## 10. Stake

- Origem: `sum` (**não** `stake`), string com ponto decimal, em reais (`"333.16"` = R$ 333,16).
- Sem milésimos. Normalização de moeda/milhar = global.

---

## 11. Odds

- Origem: `total_k` (bilhete) e `selections[].k` (seleção), **precisão completa**.
- ⚠️ **`total_k` vem `"0"` em TODA aposta PERDIDA** — 6 de 6 na amostra. O card mostra a odd
  real (`1.87`), que está em **`k`**. A regra é a do próprio app da casa:

  ```
  odd = parseFloat(total_k) === 0 ? k : total_k
  ```

  Ler `total_k` cru grava **odd zero em 100% das perdas** — é o `betOdds` da KTO em outra roupa.
  `result_k` acompanha o zero e **não** serve de fallback.
- No `W`, a odd declarada explica o retorno ao centavo nos 2 casos da amostra
  (`333,16 × 1,87 = 623,0092 → 623,01` · `338,82 × 2,22 = 752,18`), então as duas fontes
  concordam. A regra global do `W` (`retorno ÷ stake`) continua valendo.
- Bilhete **aberto** usa `potential_win ÷ sum`; `potential_win` **não** pode virar retorno.

---

## 12. Ruído a ignorar

- `event_id`, `market_id`, `outcome_id`, `sport_id`, `desc.id` — ids internos do motor. O
  **nome** do esporte vem por extenso em `desc.sport.name`, então não há mapa de id aqui
  (diferente da VaideBet, que só entrega número).
- `specifiers` (`hcp=3.5`, `total=71.5`) — a linha já vem legível no `outcome_name`.
- `currency_details` (`sign_before_value`, `cents`) — formatação da UI.
- `virtual`, `live`, `type: "match"` em `desc` — contexto do evento, não dado do bilhete.
- `combinations` vazio em bilhete simples.
- O long-poll `api/v4/live|prematch/...` e o WebSocket `api/v1/ws_new` (eventos
  `my_bets:update`, `cashout:update`) — só empurram deltas; a lista REST é completa e o robô
  não depende deles.

---

## 13. Pegadinhas (resumo rápido)

- **`total_k` = 0 em toda PERDIDA** → a odd sai de `k` (§11). É a armadilha central da casa.
- **`timestamp` em SEGUNDOS**, não ms → `× 1000` antes de virar data (§4).
- **Stake é `sum`**, não `stake` (§10).
- **Data: 7 de 10 bilhetes mudam de dia** entre colocação e evento → a coluna Data é a do
  **evento** (§4).
- **`cashout_amount` vem preenchido na ABERTA** — é oferta de venda, não retorno (§7).
- **A 1ª requisição da página toma 401** e o corpo dela tem uma chave `status` (§2.1).
- **`cashed out` tem espaço** no enum (§5).
- **A base da API é config da marca** (`api-31-…`) — aprender em runtime, nunca hardcodar.
- **Ids quase idênticos entre si** → fora do snap por edit-distance, de propósito (§3).
- A lista **não** carrega sozinha (15 por página) → só API paginada resolve.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

- **Coluna Data = a linha `Data (evento mais recente):` do bloco, copiada literalmente.** Nunca
  a `Data (colocação):`, nunca inferir da vizinhança nem da ordem da lista. Nesta casa as duas
  divergem em 70% dos bilhetes.
- Odd com precisão completa, decimal com vírgula, e **nunca zero numa perdida** — odd zerada é
  sintoma de leitura de `total_k` cru.
- Bilhete aberto sai **sem** resultado (`extraction_state = aberta`) e **sem** retorno realizado
  (o `Retorno potencial:` do bloco não é ganho).
- Status fora de `{open, won, lost}` nunca vira W/L por dedução (§5).
- Esporte: copiar o valor do bloco (`Badminton`), que já vem por extenso e oficial.

---

## 15. Exemplos golden (bilhetes reais)

Amostra do reconhecimento (s248 · 10 bilhetes · conferida card a card):

```text
05/08/2026	Badminton		Jonbet		Pontos	Menos de 71,5 Pontos [Lock T / Hoang C v Wang Y H / Lam C W]	333,16	1,87	W	2696533322854707365
05/08/2026	Badminton		Jonbet		Pontos	Menos de 77,5 Pontos [Chaliha, Ashmita v Hiramoto, Ririna]	333,16	1,87	L	2696531434088309374
04/08/2026	Badminton		Jonbet		ML	Kim, Ga Ram [Park, Ga Eun v Kim, Ga Ram]	338,82	2,22	W	2696529775920550060
04/08/2026	Badminton		Jonbet		Handicap	Pai, Yu Po +1,5 [Valishetty, Shriyanshi v Pai, Yu Po]	138,35	2,49	L	2696530168314475463
06/08/2026	Badminton		Jonbet		Handicap	Kharb, Anmol -3,5 [Vu, Thi Trang v Kharb, Anmol]	200,00	1,87		2696892252130783466
```

Por que estes cinco: um `W` cuja odd declarada explica o retorno ao centavo · uma **perdida com
`total_k: "0"`** (a odd `1,87` sai de `k`, e o card confirma) · o `ML` · o `Handicap` de pontos ·
e uma **aberta**, com Resultado **vazio** apesar de o payload trazer `potential_win: 374` e
`cashout_amount: 184.46`. Repare que **as cinco datas são do evento**, e quatro delas caem no dia
seguinte ao da colocação.

A regressão da CAPTURA (campos, as duas datas, odd, status, aberta × potencial, guarda do token,
paginação por `skip`) está travada em `extensor/harness/casos/jonbet.mjs`: 10 bilhetes reais.

---

## Feedback para a camada global / MODELO

1. **A tabela do `SHARPENUP_ARQUITETURA §4` mostra que a coluna Data não é uniforme** entre as
   casas: umas gravam colocação (KTO, Betano), outras evento (Superbet, Pinnacle, VaideBet,
   Tivo, Jonbet). O `MASTER_OUTPUT §4` só fala explicitamente do caso de múltipla ("perna mais
   recente"). Vale escrever a regra para **simples** também — hoje cada casa decide, e a
   diferença muda o dia do bilhete no painel.
2. **`payout_tax` / `final_payout` (imposto sobre prêmio) não tem regra global.** Está zerado
   nesta casa hoje, mas a estrutura existe no motor BetBy e o tema é regulatório brasileiro:
   quando aparecer, é preciso decidir de uma vez se o `W` usa o retorno **bruto** ou o
   **líquido** — a escolha muda odd e P/L de toda a base.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA (harness verde, 10 bilhetes) · mapa de mercados **parcial** (§9 — só badminton) · ⚠️ **NÃO validada ao vivo** (nenhum lote passou pela extensão ainda)
CASA: Jonbet
