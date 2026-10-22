# CASA_VAVE
## Camada de tradução — Vave → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Vave.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Vave` · sites: roda em **domínio numerado** (`34evav91.com` no recon de
  21/10/2026, logado) e `vave.com` serve o mesmo app · esportes em `/pt/prematch`, histórico
  em **Perfil → Histórico de apostas** (`/pt/cabinet/betting-history`).
- Locale: `pt` na interface, mas **mercado e seleção vêm em INGLÊS** (template Sportradar,
  §2.5). Times e ligas também em inglês (`Spain. La Liga`, `Clube Atletico Mineiro`).
- Moeda: a da **conta** (`currency: "USDT"` na amostra; casa cripto). O card escreve só o
  número (`30`) com o ícone da moeda.
- **Dinheiro e odd em NÚMERO** (`30`, `9.19`), sem milésimos.
- Plataforma **PRÓPRIA** (`softlabs`, app `vavemain`). O layout lembra a 1xBet, mas bundle e
  API não têm nada a ver com ela. A API mora em `platform.<host da casa>`. Família `vv`
  (inject `vv_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s425):** `Vave`, a da BASE. Medido em 21/10/2026: `Vave` em `parceiros`,
> `bilhetes`, `casas_meta` e `correcoes` (1 conta do Gabriel, 6 bilhetes de print, sem
> código). ⚠️ **`Vavada` é outra casa**, com uma letra a mais.

### 1.1 A moeda é da conta

Cadastre a conta **na moeda da carteira usada na casa** (USDT na amostra). O `/salvar` converte
para R$ pela cotação do dia da aposta ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).
O bloco leva `Moeda: USDT`, `Carimbo de colocação:` (dia da cotação) e o dinheiro sem `R$`.
**Os números do TSV são os da casa**; quem converte é o servidor.

### 1.2 Esporte: a API manda o nome em inglês

`sports[].name` vem em inglês (`Football`, `Basketball`). Traduzir pelo `MASTER_ESPORTES`
(`Football` = Futebol, `Basketball` = Basquete), nunca verbatim.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/vv_inject.js`).

```
GET https://platform.<host>/api/v2/bet/history?page=1&from=AAAA-MM-DD&till=AAAA-MM-DD&limit=100&lang=pt
    authorization: Bearer <sessão> · client-timezone · x-requested-with
→ { "status":"ok", "code":200, "data": { "bets": { "bets":[…], "events":[…], "competitors":[…],
    "leagues":[…], "sportCategories":[…], "sports":[…], "results":[…], … }, "page", "limit", "total" } }
```

Medido com a sessão do Feca (21/10/2026):

- **Auth por `authorization: Bearer`** (+ `client-timezone`), por **XHR**. Sem o header, a
  resposta é **HTTP 200** com `code: 401` no corpo. O token também fica em
  `localStorage.customer.token`, e o inject parte dele a frio (domínio novo, aba já aberta).
- **`limit` tem teto 100** (1000 → `code: 400`).
- **`total` é o número de PÁGINAS**, não de bilhetes (limit 5 sobre 11 → `total: 3`).
  Fim autoritativo: `page >= total`.
- **Sem `status`** vem tudo (aba `Todos`). O filtro da tela usa `0` Pendentes · `1` Perdidas ·
  `2` Ganhou · `3` Devolvidas · `8` Pagamento (cashout).
- `from` de 2020 é aceito. O replay pede 3 anos, até amanhã.
- **Mercado e seleção não vêm no histórico.** Saem de dois dicionários públicos
  (`/api/market-descriptions/get-all-markets/pt`, 1,4 MB, e `…/get-all-outcomes/pt`, 100 KB,
  sem auth), que o inject baixa uma vez e resolve (§2.5).

### 2.3 Layout do bilhete (card)

Linha por bilhete: `CARTÃO DE CIDADÃO #5435097` (o código), `DATA 20.10.2026 10:18`
(colocação, São Paulo), `Aposta Múltipla` / `Single Bet` com `N Resultados` e uma barrinha
colorida por perna (vermelha = perdida, verde = ganha), `ODDS 9.19`, `VALOR DE APOSTA 30`,
`ESTADO` (`PERDIDAS`). As pernas ficam num **carrossel horizontal**: o `innerText` não traz os
mercados e não há linha em branco entre bilhetes. **Texto por DOM não serve; por isso API.**

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Vave |
|---|---|
| `bets[].id` | numérico de **7 dígitos** (`5435097`) — o `#` do card, chave de dedup e `[Código:]` |
| `bets[].couponId` · `bet_id` · `number` | outros ids (`couponId` ≠ `id`; `bet_id` = `id` em string). **Não** vão para o marcador |
| `bets[].currency` | moeda da conta (`USDT`) |
| `bets[].amount` | stake (o "Valor de aposta" do card). `fullAmount` = `amount` na amostra |
| `bets[].value` | odd do bilhete, a do card, **já é o produto das pernas** (15,7 = 3,29 × 2,13 × 2,24) |
| `bets[].status` | `1` perdida (11 de 11 medidos). `0`/`2`/`3`/`8` só pelo filtro da tela (§5) |
| `bets[].win` · `winFull` | `0` nas 11 perdidas. ⚠️ **Em ganha NÃO MEDIDO** (retorno ou lucro?) |
| `bets[].betCashoutAmount` | `null` na amostra |
| `bets[].taxesData.potentialWinAmount` | stake × odd (30 × 9,19 = 275,70) — o retorno potencial |
| `bets[].ts` | colocação, **unix em SEGUNDOS** (o card a mostra em São Paulo) |
| `bets[].finishedAt` | liquidação, `AAAA-MM-DD hh:mm:ss`, ⚠️ fuso **não provado** — fora do bloco |
| `bets[].typeName` | `sports_._platform_._accumulator` / `…_single bet` |
| `bets[].system` · `count_bets` | `0` em toda a amostra · nº de pernas |
| `bets[].bonusAmount` · `freebetAmount` | `0` em toda a amostra |
| `bets[].betBetBuilderId` | `null` em toda a amostra |
| `bets[].cashout` | `{amount:null, errorMessage:"Bet cashout is not available"}` — oferta, não dinheiro |
| `bets[].userId` | ⚠️ **identifica a conta**: o inject tira do cru |
| `details[].status` | `1` perdida · `2` ganha (cor da perna no card) |
| `details[].value` / `odds` | odd da perna (`3.78` / `"3.7800"`) |
| `details[].event_id` → `events[]` | `competitor1Id`/`competitor2Id` → `competitors[].name`; `ts` = início em **unix UTC** (`time` = o mesmo em UTC) |
| `details[].league_id` → `leagues[]` | `name` da liga; `sportCategoryId` → `sportCategories[].name` (país) |
| `events[].sport_id` → `sports[]` | `name` do esporte, em inglês |
| `details[].marketId` / `outcomeId` / `specifiers` | ids do dicionário + parâmetros (`hcp=1`, `quarternr=1\|total=42.5`) |

**O template (Sportradar), resolvido pelo inject:** `{$competitor1}`/`{$competitor2}` = os times
do evento · `{!x}` = ordinal (`1st`) · `{+x}` = valor com sinal · `{-x}` = valor com o sinal
**invertido** · `{x}` = valor. Medido: `{$competitor2} ({-hcp})` com `hcp=1` →
`Cruzeiro Basquete (-1)`; `{$competitor1} ({+hcp})` com `hcp=-2.5` → `Roma (-2.5)`. O bloco
leva o `specifiers` cru ao lado (`Especificadores (cru da casa):`). Placeholder sem valor fica
como veio; dicionário fora do ar sai `(mercado id N, sem nome)` e a captura segue.

**Ficha:** a família `vv` ainda **não tem adaptador** (`app/adaptadores/`). O cru (bilhete +
as linhas de `events`/`competitors`/`leagues`/`sportCategories`/`sports`/`results` que ele
usa, sem `userId`) é só guardado; o bilhete vai pela IA.

---

## 3. ID do bilhete

- **Numérico de 7 dígitos** (`5435097`), o mesmo que o card estampa como `#5435097`.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`).
- Os 6 bilhetes `Vave` que já estavam na base (print, de outro dono) não têm código.

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente): `events[].ts` (unix UTC) convertido para
São Paulo. A colocação (`ts` do bilhete) sai em São Paulo no bloco e no carimbo de colocação:
`1792502331` é o `20.10.2026 10:18` do card.

> Múltipla perdida com perna ainda por jogar: a perna mais recente pode ser **depois** da
> liquidação. O servidor puxa a data para a perna perdida
> (`repository.data_da_perna_perdida`, pelo rótulo `[perna perdida]`).

---

## 5. Status e Resultado

Só o **dinheiro** decide onde a amostra não alcança. Nenhum campo de retorno foi medido em
ganha, então `W` exige que o número **feche com stake × odd ao centavo** por uma das duas
leituras possíveis: `winFull` = retorno, ou `win` = lucro (retorno = stake + `win`).

| `status` · dinheiro | Leitura | Código |
|---|---|---|
| `0` | Em aberto | *(vazio — não liquidar)* |
| `1` · `win` = `winFull` = 0 | Perdeu | `L` |
| qualquer · `winFull` = stake (ou `8` com `betCashoutAmount` = stake) | P/L zero | `V` |
| `2` · `winFull` = stake × odd, ou `win` = stake × (odd − 1) | Ganhou | `W` |
| `1` com dinheiro, `2` que não fecha, `3` com retorno ≠ stake, `8` ≠ stake, enum novo | sobe cru | *(a conferir)* |

Medido: `1` 11 em 11. O resto é a régua acima, travada por clone no harness, **não** por
amostra real. O bloco sempre leva `Status (API): status=N · tipo=… · system=…`.

---

## 6. Boost / promoção

`bonusAmount` = `0` em toda a amostra. Se vier, o bloco escreve `Bônus da casa: X USDT` e vale
a regra global do `W` (`retorno ÷ stake`).

---

## 7. Cashout

O filtro da tela tem `Pagamento` (`status=8`). Sem amostra: o bloco sobe o `cashout` e o
`winFull` crus e diz "a conferir"; só `cashout` = stake vira `V` (rede do dinheiro). A regra
global (`MASTER_RESULTADO §5.1.2` e `§5.6`) se aplica quando o campo for medido. O objeto
`cashout` da lista (`errorMessage: "Bet cashout is not available"`) é a **oferta**, não
dinheiro, e não entra no bloco.

---

## 8. Bônus

`freebetAmount` = `0` em toda a amostra. Se vier, o bloco escreve `Freebet incluído: X USDT`,
o rótulo que o servidor lê (`freebets_do_texto`, `MASTER_RESULTADO §5.8`).

---

## 9. Mapa de mercados (Vave → `Aposta` global)

Só os mercados **confirmados** no dado real, e só onde a tradução é direta (camada fina). O
nome é o do dicionário da casa, **em inglês**, já com o template resolvido:

| Vave exibe (mercado) | Aposta global |
|---|---|
| `1st half - total` (futebol) | Gols |
| `1st half - handicap` (basquete) | Handicap |
| `1st half - corner handicap` | Escanteios |
| `1st quarter - total` (basquete) | Pontos |

> `1st half` / `1st quarter` são **recorte**, não mercado novo. `<time> clean sheet` e
> `<time> total` também aparecem na amostra: a categoria sai do `MASTER_APOSTAS` pelo objeto
> medido, sem atalho aqui. A descrição segue o `MASTER_DESCRICAO` em pt-BR.

---

## 10. Stake

Campo `amount`, na moeda da conta; a conversão para R$ é do `/salvar`.

---

## 11. Odds

- **A odd do bilhete é `value`**, a mesma do card, e já é o produto das pernas.
- **W:** `retorno ÷ stake` (regra global); com retorno = stake × `value` as duas coincidem.
- **L e aberta:** `value`. Na perdida ela **não** zera (9,19 no 5435097).
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `cashout` (oferta), `info.falseCashOut`, `taxesData` (exceto o potencial), `shareable`,
  `isVip`, `currencyIconUrl`, `betMaker`.
- `results[]` — placar por período.
- `leagues[].flagURL`, `translationSlug`, `defaultSlug`, `top`.
- Chamadas de `platform.<host>` que não são a lista (`user/is-auth`, `v2/user-activity`,
  `v4/coupon/get`, `web-socket/subscribe/cashouts`…): o inject só aprende o Bearer delas.

---

## 13. Pegadinhas (resumo rápido)

1. **Mercado e seleção fora do histórico**, em template inglês (§2.5).
2. **`{-hcp}` inverte o sinal** do `hcp` (§2.5).
3. **`total` é páginas, não bilhetes** (§2.1).
4. **Erro com HTTP 200** e teto de 100 no `limit` (§2.1).
5. **Domínio numerado**: a API é `platform.` do host da aba (§1).
6. **`userId` no bilhete** identifica a conta (§2.5).
7. **Retorno em ganha não medido** (§5).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada na moeda da carteira (USDT) **antes** da 1ª captura.
- [ ] Nenhuma aberta liquidada; nenhuma perdida com odd zero.
- [ ] Coluna Data = evento em São Paulo (a perdida, pela perna perdida).
- [ ] Contagem capturada == total da aba `Todos` no período.
- [ ] **1ª ganha:** conferir `win`/`winFull` contra o card e registrar aqui qual é o retorno (§5).
- [ ] **1º cashout / devolvida / aberta:** salvar o JSON como fixture e trocar o clone do harness.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 21/10/2026 — conta inteira (**11 bilhetes**, todos perdidos):
`extensor/harness/fixtures/vave.history.json` (a resposta da casa, só o `userId` zerado) e
`vave.dicionarios.json` (recorte dos dicionários).

| ID | Tipo | Status | Stake | Odd | Colocação (SP) | Evento (SP) | Fonte |
|---|---|---|---|---|---|---|---|
| 5435097 | Múltipla 2 | `1` | 30 | 9,19 | 20/10 10:18 | 21/10 15:00 | card |
| 5433760 | Simples | `1` | 30 | 4,2 | 20/10 00:09 | 21/10 19:00 | card |
| 5433248 | Múltipla 3 (vermelha · verde · vermelha) | `1` | 30 | 15,7 | 19/10 18:27 | 20/10 16:00 | card |
| 5432746 | Múltipla 2 | `1` | 30 | 10,77 | 19/10 15:28 | — | card |
| 5432723 | Múltipla 2 | `1` | 5 | 9,75 | 19/10 | — | JSON |

**Sem amostra:** ganha · aberta · devolvida · cashout · freebet · bônus · bet builder · sistema.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão (**SharpenUp 0.7.60**) e dar **Ctrl+Shift+R** na aba da Vave.
2. Abrir **Perfil → Histórico de apostas** logado (não é obrigatório: o inject parte do token
   do `localStorage`, mas é onde a casa mostra o que conferir).
3. Conectar → Copiar bilhetes. O toast diz `respostas` e `vistos`; com `semToken` a sessão
   não está logada.
4. Conferir no dashboard: contagem, código de 7 dígitos, colocação, odd e moeda.
5. Na 1ª ganha/aberta/cashout, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

1. **Payload normalizado.** Primeira casa em que o histórico só traz ids: os nomes vêm das
   tabelas irmãs do mesmo lote e de dicionários à parte. O cru precisa levar as linhas
   irmãs, senão o adaptador futuro não tem o que ler.
2. **Template Sportradar no dicionário.** Qualquer casa que sirva o UOF cru vai repetir os
   operadores `{$…}`, `{!…}`, `{+…}`, `{-…}`; o `_template` do `vv_inject` é reaproveitável.
