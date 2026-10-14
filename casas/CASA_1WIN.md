# CASA_1WIN
## Camada de tradução — 1win → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da 1win.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `1win` · sites: `1win.io` e o espelho `1win.com` (mesmo gateway, medido em
  14/10; SharpenUp 0.7.54) · esportes em `/betting`, histórico em
  `/betting/bets-history`
- Locale: `pt` (`x-lang`), texto dos mercados em pt-BR com caixa de título (`Acima De 2.5`,
  `Empate Ou Fulham U-21`). Moeda: a da **conta** (`currencyCode: "USDT"` na amostra); o card
  escreve `USDT 25,00`.
- **Dinheiro e odd em NÚMERO** (`25`, `143.25`, `4.87`), sem milésimos.
- Plataforma **PRÓPRIA** (`top-parser`). A página é da 1win, mas o sportsbook fala com um
  gateway em OUTRO host, `api-gateway.top-parser.com`. Não é DEX, BetBy, Altenar, Kambi,
  BetConstruct nem 1xBet. Família `tp` (inject `tp_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s413):** `1win`, a da marca, em caixa baixa. Medido em 12/10/2026
> (`tools/audit_grafias.py`): nenhuma ocorrência na base.

### 1.1 A moeda é da conta

Cadastre a conta **na moeda da carteira usada na casa** (USDT na amostra). O `/salvar` converte
para R$ pela cotação do dia da aposta ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).
O bloco leva `Moeda: USDT`, `Carimbo de colocação:` (dia da cotação) e o dinheiro rotulado na
moeda. **Os números do TSV são os da casa**; quem converte é o servidor.

### 1.2 Esporte: a API manda o nome em pt

`selections[].sport.name` já vem traduzido (`Futebol`, `Basquete`, `Tênis de Mesa`), com o enum
ao lado em `sportTagKey` (`football`, `basketball`, `table_tennis`). eSports vem na mesma lista,
marcado em `tournament.isEsport`; o bloco escreve `(eSports)` ao lado do esporte. Esporte fora
do `MASTER_ESPORTES`: traduzir por ele, nunca verbatim.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/tp_inject.js`).

```
POST https://api-gateway.top-parser.com/bets/history/get-many
     Content-Type: application/json · token: <sessão> · x-lang · x-user-location · x-external-partner-id
     { "limit": 150, "offset": 0, "sportType": "all" }
→ { "result": { "items": [ { "bet": {…}, "selections": [ … ] } ], "meta": { "total": N } } }
```

Medido no gateway com a sessão do Feca (12/10/2026):

- **Auth por header `token`**, não cookie (a página nem manda cookie para o gateway). O
  `token` sai em **toda** chamada autenticada da tela de Esportes (`freebets/get-many`,
  `bonuses/get-many`, `b/get-many`…), então o replay arranca sem abrir o histórico.
- **Erro volta com HTTP 200** e `{"errors":[{"code":"…"}]}`.
- **`limit` tem teto 150** (151 → `bad_request_error`).
- **Paginação por `offset`**, fim autoritativo `offset >= meta.total` (com `limit: 2` sobre 5
  bilhetes: 2 + 2 + 1).
- **Sem `statuses`** a lista traz abertas e liquidadas juntas (aba `Todos`). A tela usa
  `[0]` (`Aberto`) e `[1,2,4,3]` (`Liquidadas`); `statuses` aceita só 0 a 4.
- **`sportType`** aceita só `sport`, `all` e `polybet` (mercados de previsão). O replay pede
  `all`. `esport`, `cyber` e `racing` → `validation_error`: eSports não tem filtro próprio.
- Painel: **Esportes → Histórico de apostas**, abas `Todos` / `Aberto` / `Liquidadas`.

### 2.3 Layout do bilhete (card)

Cabeçalho com a data (`12 de outubro de 2026 às 18:44`, hora de São Paulo) e `ID 337819068`;
selo `Aberto` / `Perdido` + `Múltipla`; a odd do bilhete em destaque (`4.87`); `N eventos`;
`Aposta / Ganhos USDT 25,00 » USDT 0,00` (liquidada) ou `Aposta / Possível vitória` (aberta);
botão `Cash out de USDT 24,46` na aberta.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na 1win |
|---|---|
| `bet.id` | numérico de 9 dígitos, em string (`"337819068"`) — chave de dedup e `[Código:]`; o card estampa como `ID` |
| `bet.currencyCode` | moeda da conta (`USDT`) |
| `bet.amount` | stake |
| `bet.cf` | odd do bilhete, ⚠️ **cortada em 2 casas** e é a que paga (§11) |
| `bet.profitAmount` | ⚠️ **RETORNO, não lucro**: na aberta é o potencial (25 × 5,73 = 143,25), na perdida 0 |
| `bet.possibleProfitAmount` | retorno potencial (= `profitAmount` na aberta) |
| `bet.status` | `0` aberta · `1` perdida (vistos) · `2`, `3`, `4` sem amostra (§5) |
| `bet.betType` | `express` (múltipla, visto) |
| `bet.createdAt` | colocação, ISO **UTC** |
| `bet.closeAt` | liquidação, ISO **UTC** (só na liquidada) |
| `bet.bonusAmount` · `bonusPercent` | `0` em toda a amostra (bônus de múltipla) |
| `bet.freebetAmount` | `0` em toda a amostra |
| `bet.wallet` | `real` em toda a amostra |
| `bet.refundInfo.refundAmount` | **oferta** de cashout da aberta — não é retorno; o inject ignora |
| `selections[].status` | `0` pendente · `1` perdida (vistos) |
| `selections[].isHalfReturn` | `false` em toda a amostra (meio retorno, asiática) |
| `selections[].odd.cf` | odd **apostada** da perna |
| `selections[].odd.groupName` · `odd.name` | mercado (`Total. 2 Parte`) e seleção (`Acima De 2.5`) |
| `selections[].match.homeTeam.name` · `awayTeam.name` | confronto |
| `selections[].match.startAt` | início, **unix em SEGUNDOS** |
| `selections[].sport.name` · `category.name` · `tournament.name` | esporte, país e liga |
| `selections[].matchResult` | placar por período (ruído, §12) |

Nenhum campo identifica a conta (nome, e-mail, id de usuário, saldo): o cru sobe inteiro.

**Ficha (s413):** o cru é lido no servidor pelo `app/adaptadores/tp.py`, com a mesma leitura
desta seção e da §5: stake = `amount`, odd = `bet.cf` (nunca o produto), retorno =
`profitAmount` só na liquidada, código em `bet.id`. Sem amostra, a Ficha é RECUSADA com o
motivo (sistema, bônus, freebet, carteira que não seja `real`, meio retorno, status 2/3/4 cujo
dinheiro não prove ganha ou anulada) e o bilhete segue pela IA. Gate:
`tests/test_adaptador_tp.py` (8 mutações, 8 detectadas).

---

## 3. ID do bilhete

- **Numérico de 9 dígitos** (`337819068`), o mesmo que o card estampa como `ID`.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`).

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente), `startAt` (unix em segundos) convertido
para São Paulo. A colocação (`createdAt`, UTC) sai em São Paulo no bloco e no carimbo de
colocação: 21:44Z é o `18:44` do card.

> Múltipla perdida com perna ainda por jogar: a perna mais recente pode ser **depois** da
> liquidação (337819068: perdeu no basquete de 12/10, perna do tênis de mesa em 13/10). O
> servidor puxa a data para a perna perdida (`repository.data_da_perna_perdida`, pelo rótulo
> `[perna perdida]`): **12/10**.

---

## 5. Status e Resultado

Só o **dinheiro** decide onde a amostra não alcança. Retorno = `profitAmount`.

| `bet.status` · dinheiro | Leitura | Código |
|---|---|---|
| `0` | Em aberto | *(vazio — não liquidar)* |
| `1` · retorno 0 | Perdeu | `L` |
| qualquer · retorno = stake | P/L zero | `V` |
| `2` · retorno = stake × `cf` (ao centavo) | Ganhou | `W` |
| `1` com retorno > 0, `2` que não fecha com a odd, `3`, `4`, enum novo | sobe cru | *(a conferir)* |

Medido: `0` 4 · `1` 1 em 5.

> ⚠️ **NÃO VALIDADO AO VIVO:** os status `2`, `3` e `4`. Pela ordem da aba `Liquidadas`
> (`[1,2,4,3]`) o `2` deve ser ganha e `3`/`4` anulada/cashout, mas isso é palpite e não entra
> no código: quem decide é o número. A 1ª ganha que aparecer confirma também que
> `profitAmount` segue sendo o retorno (e não o lucro) depois de liquidar.

---

## 6. Boost / promoção

`bonusAmount`/`bonusPercent` = `0` em toda a amostra. Se vierem preenchidos, o bloco escreve
`Bônus da casa: X USDT (N%)` e vale a regra global do `W` (`retorno ÷ stake`).

---

## 7. Cashout

A aberta traz `refundInfo: { allowed, refundAmount }` — a **oferta** (ex.: 24,46 sobre 25), que
muda a cada minuto e não é retorno: o inject ignora e o bloco não a imprime (senão a mesma
aberta viraria texto novo a cada captura). Cashout executado sem amostra: sobe "a conferir"
até ser medido; a regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`) se aplica quando for.

---

## 8. Bônus

`freebetAmount` = `0` em toda a amostra. Se vier, o bloco escreve `Freebet incluído: X USDT`,
o rótulo que o servidor lê (`freebets_do_texto`, `MASTER_RESULTADO §5.8`).

---

## 9. Mapa de mercados (1win → `Aposta` global)

Só os mercados **confirmados** no dado real, e só onde a tradução é direta (camada fina):

| 1win exibe (`groupName`) | Aposta global |
|---|---|
| `Vencedor` | ML |
| `Dupla Chance` | Dupla Chance |
| `Ambos os times marcarão` | Ambas Marcam |
| `Total. 2 Parte` (futebol) | Gols |
| `Total. 1 Quarto` (basquete) | Pontos |
| `Escanteios. <time> total` | Escanteios |

> `2 Parte` / `1 Quarto` são **recorte**, não mercado novo. A seleção vem em caixa de título
> (`Acima De 2.5`, `Abaixo De 55.5`); a descrição segue o `MASTER_DESCRICAO` em pt-BR.

---

## 10. Stake

Campo `amount`, na moeda da conta; a conversão para R$ é do `/salvar`.

---

## 11. Odds

- **A odd do bilhete é a `cf`, cortada em 2 casas, e é ela que paga.** 337817372: pernas
  1,79 × 2,75 = 4,9225, card `4.92`, potencial 25 × 4,92 = 123,00. **Nunca** o produto das
  pernas.
- **W:** `retorno ÷ stake` (regra global); com retorno = stake × `cf` as duas coincidem.
- **L e aberta:** `cf`. Na perdida ela **não** zera (4,87 no 337819068).
- Odd **nunca** truncada além do que a casa mandou; decimal com vírgula.

---

## 12. Ruído a ignorar

- `refundInfo` — oferta de cashout (§7).
- `matchResult.periodsScore` / `matchScore` — placar.
- `odd.id` / `oddId`, `match.slug`, `competitors[]`, `serviceV2`, `canShare`.
- Chamadas do gateway que não são a lista: `matches/get-many`, `sports/get`, `categories/get`,
  `tournaments/get`, `freebets/get-many`, `bonuses/get-many`, `feature-flags/get-many`,
  `highlights/get-many`, `bets/get-auto-bet-amount-v2` (o inject só aprende o `token` delas).

---

## 13. Pegadinhas (resumo rápido)

1. **`profitAmount` é o retorno**, não o lucro (§2.5).
2. **Odd do bilhete cortada em 2 casas** — é a que paga, não o produto das pernas (§11).
3. **Perdida com perna ainda pendente** (§4).
4. **Oferta de cashout na aberta** não é dinheiro (§7).
5. **Erro com HTTP 200** e teto de 150 no `limit` (§2.1).
6. **`startAt` em segundos, `createdAt` em ISO UTC** (§4).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada na moeda da carteira (USDT) **antes** da 1ª captura.
- [ ] A odd de múltipla é a `cf` da casa, nunca o produto das pernas.
- [ ] Nenhuma aberta liquidada; nenhuma perdida com odd zero.
- [ ] Coluna Data = evento em São Paulo (a perdida, pela perna perdida).
- [ ] Contagem capturada == total da aba `Todos`.
- [ ] 1ª ganha: `profitAmount` = stake × `cf` (confirma §5).

---

## 15. Exemplos golden (bilhetes reais)

Recon de 12/10/2026 — conta inteira (**5 bilhetes**, todas múltiplas de 2):
`extensor/harness/fixtures/1win.settled.json` e `1win.open.json` (as respostas da casa, byte a
byte).

| ID | Tipo | Status | Stake | Odd | Evento (SP) | Retorno | Fonte |
|---|---|---|---|---|---|---|---|
| 337819068 | Múltipla 2 (1 perna pendente) | `1` | 25,00 | 4,87 | 13/10 01:30 (perna perdida: 12/10) | 0 | card |
| 338019158 | Múltipla 2 | `0` | 25,00 | 5,73 | 13/10 15:00 | potencial 143,25 | card |
| 337940634 | Múltipla 2 | `0` | 25,00 | 4,2 | 13/10 08:15 | potencial 105,00 | card |
| 337817372 | Múltipla 2 | `0` | 25,00 | **4,92** (pernas 4,9225) | 14/10 16:00 | potencial 123,00 | card |
| 337815546 | Múltipla 2 | `0` | 25,00 | 9 | 13/10 15:00 | potencial 225,00 | card |

**Sem amostra:** ganha · simples · cashout executado · anulada · sistema · bônus de múltipla ·
freebet · polybet · status `2`/`3`/`4`.

---

## Feedback para a camada global / MODELO

1. **Gateway em outro host, token em header.** O padrão é o da Shuffle (token de qualquer
   chamada autenticada), mas aqui o gateway é de outro domínio: o inject casa pelo host da
   API, e a página pode trocar de espelho sem mexer na captura.
2. **Erro com HTTP 200.** Casa nova com gateway próprio: conferir a FORMA da resposta, nunca
   só o status HTTP.
