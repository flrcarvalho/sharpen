# CASA_20BET
## Camada de tradução — 20bet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da 20bet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).
>
> **A 20bet é ESPELHO da Vave** (mesma plataforma `softlabs`, mesma API, mesmo inject e mesmo
> formatador). O que é do motor está em [`CASA_VAVE.md`](CASA_VAVE.md); aqui fica o que a 20bet
> mostrou de diferente e o que foi medido nela.

---

## 1. Identidade

- Casa canônica: `20bet` · site: roda em **domínio numerado** (`20betz0ne1.com` no recon de
  25/10/2026, logado) · histórico em **My Account → Betting history** (`/cabinet/betting-history`).
- Locale da interface: inglês na conta do recon. **O dicionário `/pt` vem em PORTUGUÊS**
  (`Handicap`, `{!quarternr} quarto - 1x2`, `Vencedor (incluindo prolongamento)`), ao contrário
  do da Vave, que vinha em inglês. Os nomes de time e liga continuam em inglês.
- Moeda: a da **conta** (`currency: "USD"` no recon). O card escreve `$ 25`.
- **Dinheiro e odd em NÚMERO** (`25`, `7.36`), sem milésimos.
- Plataforma **PRÓPRIA** `softlabs`, a mesma da Vave. API em `platform.<host da casa>`. Família
  `vv` (inject `vv_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s428):** `20bet`, a da BASE. Medido em 25/10/2026: `20bet` em `parceiros` (1 conta
> do Gabriel), `bilhetes` (57, de print, com o código numérico de 8 dígitos do card),
> `casas_meta`, `correcoes` e `uso_tokens`. A marca escreve `20Bet`; a base manda.

### 1.1 A moeda é da conta

Cadastre a conta **na moeda da carteira** (USD no recon). O bloco leva `Moeda: USD` e o
carimbo de colocação; o `/salvar` converte para R$ pela cotação do dia.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/vv_inject.js`), o mesmo da Vave
([`CASA_VAVE §2.1`](CASA_VAVE.md#21-modo-de-ingestão)): `GET platform.<host>/api/v2/bet/history`,
`authorization: Bearer` (também em `localStorage.customer.token`, partida a frio), `limit` 100,
`total` = páginas.

**Prova do motor (s428):** a home carrega `platform.20betz0ne1.com/api/v2/…`; o histórico
respondeu ao Bearer do `localStorage` com HTTP 200; a **união de chaves** do payload real deu
**167 chaves, zero nova** contra a fixture da Vave.

### 2.3 Layout do bilhete (card)

Tabela `BET · DATE · TYPE · ODDS · STAKE · WIN AMOUNT · STATUS`: `#68651106`, `23.10.2026, 19:41`
(colocação, São Paulo), `Multi bet` / `Single bet` (com o selo `Bet builder`), `7.36`, `$ 25`, o
potencial em cinza na aberta, `Lost`/`Pending`. A seta abre as pernas: liga, data do evento, times,
`PICK`, `RESULT` (placar) e o estado da perna (`Lost`, `Won`, `Returned`, `Pending`).

---

## 2.5 Campos da API (o que o inject entrega)

Os campos são os da [`CASA_VAVE §2.5`](CASA_VAVE.md#25-campos-da-api-o-que-o-inject-entrega).
O que a 20bet mediu além:

| Campo | Medido na 20bet |
|---|---|
| `bets[].id` | numérico de **8 dígitos** (`68651106`) — o `#` do card |
| `bets[].status` | `0` Pending (2) · `1` Lost (10) |
| `details[].status` | `0` Pending · `1` Lost · `2` Won · `3` **Returned** (devolvida), lidos no card |
| `bets[].taxesData.potentialWinAmount` | o "Win amount" cinza da aberta (25 × 10,19 = 254,75) |
| `bets[].betBetBuilderId` · `betBetBuilderLegs` | Bet Builder: **uma** perna só (mercado `BetBuilder`), e as seleções do cupom como texto pronto da casa (`["Pontos do jogador - Josh Hart 10+ (Partida)", …]`) |
| `bets[].currency` | `USD` |

**Ficha:** adaptador `vv` (`app/adaptadores/vv.py`). Aceita perdida e aberta; **Bet Builder é
recusado** (a casa só manda as seleções como texto, e a Ficha precisa de uma perna por seleção):
vai à IA pelo texto, que leva `Seleções do Criar Aposta (texto da casa):`.

---

## 3. ID do bilhete

- **Numérico de 8 dígitos** (`68651106`), o que o card estampa como `#68651106`.
- É o mesmo número dos 57 bilhetes que a base já tinha por print: captura e print dedupam.

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente), como na Vave: `events[].ts` (unix UTC) em
São Paulo. A colocação (`ts`) é a do card: `1792795306` = `23.10.2026, 19:41`.

---

## 5. Status e Resultado

A régua é a da [`CASA_VAVE §5`](CASA_VAVE.md#5-status-e-resultado) (o dinheiro decide).

| `status` · dinheiro | Leitura | Código |
|---|---|---|
| `0` | Em aberto | *(vazio — não liquidar)* |
| `1` · `win` = `winFull` = 0 | Perdeu | `L` |
| qualquer · `winFull` = stake | P/L zero | `V` |
| `2` · `winFull` = stake × odd | Ganhou | `W` |
| o resto | sobe cru | *(a conferir)* |

**Perna devolvida (`3`) numa múltipla:** o card mantém a odd cheia do bilhete (7,36 =
1,63 × 2,15 × 2,1 no 68651106, perdido). Numa múltipla GANHA com perna devolvida a odd que vale
é `retorno ÷ stake` (regra global).

**Medido na ganha (s429, conta do Gabriel, 25/10/2026):** a casa paga MENOS que stake × odd do
card em dois casos. `68703441`: 30 @ 7,29, perna 1,71 devolvida, pagou **127,8** (W @ 4,26).
`68684132`: três pernas ganhas, 30 @ 11,25, pagou **337,2** (W @ 11,24). A Ficha aceita
`status 2` com `winFull` > stake quando **toda perna está ganha (`2`) ou devolvida (`3`)**, e a
odd sai do dinheiro. Antes disso ela recusava e a IA lia a odd do card numa captura e o retorno
noutra: o P/L do dono mudava a cada recaptura (+91 USD nessa aposta).
Fixture: `extensor/harness/fixtures/20bet.ganhas.cru.json`.

**Print da LISTA não serve:** a tabela do Betting history só mostra o resumo (ID, odd, stake,
status), sem as pernas. Subido por print, a IA grava `Mercado Especial - REVISAR` em tudo (s429,
65 de 65). A fonte é a captura pela extensão; print, só do bilhete ABERTO com as pernas.

---

## 6. Boost / promoção

A home oferece "20bet boost" (`x1.05`, `x1.1`) em combos prontos. Sem amostra no histórico:
`bonusAmount` = 0 nos 12. Se vier, `Bônus da casa:` no bloco e a regra global do `W`.

---

## 7. Cashout

Sem amostra (o objeto `cashout` da lista é a **oferta**: `errorMessage: "Odds disabled"` /
`"This bet already settled"`). Régua da `CASA_VAVE §7`.

---

## 8. Bônus

`freebetAmount` = 0 nos 12. Se vier, `Freebet incluído:` no bloco (o rótulo que o servidor lê).

---

## 9. Mapa de mercados (20bet → `Aposta` global)

Só os confirmados no dado real, com o nome do dicionário `/pt` da casa já resolvido:

| 20bet exibe (mercado) | Aposta global |
|---|---|
| `Handicap` (futebol) | Handicap |
| `Handicap pontos` (badminton) | Handicap |
| `1º parte - total cantos` | Escanteios |

> `<time> total`, `{!quarternr} quarto - 1x2` e `Vencedor` também aparecem: a categoria sai do
> `MASTER_APOSTAS` pelo objeto medido. Bet Builder: as seleções vêm prontas (§2.5).

---

## 10. Stake

Campo `amount`, na moeda da conta.

---

## 11. Odds

- **A odd do bilhete é `value`**, a do card, já o produto das pernas.
- **W:** `retorno ÷ stake`. **L e aberta:** `value` (não zera na perdida).
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

O mesmo da [`CASA_VAVE §12`](CASA_VAVE.md#12-ruído-a-ignorar), mais `betBetBuilderStatus` e
`vendorId`.

---

## 13. Pegadinhas (resumo rápido)

1. **Espelho da Vave**: o que mudar no motor muda nas duas (`vv_inject.js`, `formatTicketVV`).
2. **Dicionário em português** na rota `/pt` (a Vave servia inglês).
3. **Bet Builder em perna única** com as seleções em texto (`betBetBuilderLegs`).
4. **Domínio numerado**: a API é `platform.` do host da aba.

---

## 14. Validações específicas

- [ ] A conta foi cadastrada em **USD** antes da 1ª captura.
- [ ] Contagem capturada == total da lista `All` no período.
- [ ] **1ª ganha:** conferir `win`/`winFull` contra o card.
- [ ] **1º Bet Builder liquidado:** conferir o resultado da IA contra o card.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 25/10/2026 — conta inteira (**12 bilhetes**, 10 perdidos e 2 abertos, USD):
`extensor/harness/fixtures/20bet.history.json` (só o `userId` zerado), `20bet.dicionarios.json`
(recorte) e `20bet.cru.json` (o cru que o inject real monta).

| ID | Tipo | Status | Stake | Odd | Colocação (SP) | Fonte |
|---|---|---|---|---|---|---|
| 68724463 | Simples · Bet builder (2 seleções) | `0` Pending | 20,01 | 4,33 | 25/10 13:21 | card |
| 68722991 | Múltipla 3 | `0` Pending | 25 | 10,19 | 25/10 12:56 | card |
| 68718582 | Múltipla 3 | `1` Lost | 25 | 11,25 | 25/10 11:17 | card |
| 68651558 | Simples · Bet builder | `1` Lost | 100 | 2,5 | 23/10 19:57 | card |
| 68651106 | Múltipla 3 (Lost · Returned · Won) | `1` Lost | 25 | 7,36 | 23/10 19:41 | card |

**Sem amostra:** devolvida no bilhete inteiro · cashout · freebet · bônus · sistema.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão e dar **Ctrl+Shift+R** na aba da 20bet.
2. Conectar → Copiar bilhetes (o inject parte do token do `localStorage`).
3. Conferir no dashboard: contagem, código de 8 dígitos, colocação, odd e moeda (USD).

---

## Feedback para a camada global / MODELO

1. **Espelho com dicionário em outro idioma.** O mesmo motor serve o dicionário em inglês numa
   casa e em português noutra, na mesma rota `/pt`. A família `{time}`/`{jogador}` do dicionário
   da Ficha precisa das duas grafias.
