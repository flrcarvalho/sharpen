# CASA_SPORTAZA
## Camada de tradução — Sportaza → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Sportaza.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Sportaza` · marca `sportaza.com` (cassino internacional, Rockstahp Ventures,
  licença de Anjouan). **Opera em espelho NUMERADO**: em 30/10/2026 o Feca usa
  `sportaza-5178.com`. O sportsbook fica em `/pt/sports` e o histórico em
  `/pt/sports?page=betHistory` (ícone "Minhas apostas" na fila de esportes).
- Motor: **Altenar / BIA**, cluster `altenar2`. O `altenarWSDK` monta na própria página (window
  de topo), com `integration=sportaza`, `culture=pt-PT`.
- Moeda: **da conta**. A conta do Feca é em **USD** (`currency: "USD"` em todo bilhete, card em
  `$`). Quem converte é o servidor, pela moeda do CADASTRO
  ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)): **cadastre a conta em
  USD antes da 1ª captura**.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s434):** a da **marca** (`Sportaza`). Medido em 30/10/2026: nenhuma linha em
> `parceiros`, `bilhetes`, `casas_meta`, `correcoes` ou `uso_tokens` com `sportaza` (sem caixa,
> sem espaço). O pedido chegou como "Sportazza"; o site escreve `Sportaza`.

### 1.1 Espelho da VaideBet/Esportiva/Jogo de Ouro/Betpix365/Estrela Bet/Betrebels/BetMartini/Vavada/Kikobet/Tornadobet

Décima primeira casa do mesmo motor, provada no recon de 30/10/2026 (Chrome do Feca, LOGADO):

| Prova | Sportaza | Vavada |
|---|---|---|
| SDK | `sb2wsdk-altenar2.biahosted.com` na página | idem |
| `integration` | `sportaza` | `vavada` |
| cluster | `altenar2` | `altenar2` |
| `culture` | `pt-PT` | `pt-br` (pela URL) |
| a tela chama | **só o compacto** (`widgetBetHistory`) | não medido |

O `vb_inject.js` **aprende** do compacto (url + `Authorization: Bearer` + corpo) e **consome**
só o expandido, que ele mesmo pede — o caso da Betpix365. O que separa as marcas é o
`integration` do corpo aprendido, preservado no replay. Harness: `casos/sportaza.mjs`, com
fixture **real** desta conta.

> **Ao mexer numa das Altenar, confira as outras.**

> ⚠️ **Espelho numerado.** Registrados: `sportaza.com` e `sportaza-5178.com` (manifest,
> `popup.js`, `_HOSTS_POR_CASA`). O match do Chrome **não aceita curinga no meio do domínio**:
> quando o número trocar, a extensão **não engancha** até o domínio novo entrar nos três lugares
> e sair versão nova. Sintoma: "0 bilhetes" com a aba aberta no histórico. Confira o host da aba.

---

## 2. Modo de ingestão e layout

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js`, compartilhado). Endpoint,
abas (`statuses`), paginação (`pageNumber` até `isLastPage`) e autenticação (Bearer) idênticos à
[`CASA_ESTRELABET`](CASA_ESTRELABET.md) §2. Medido nesta casa (30/10/2026):

- **A tela só chama o COMPACTO** (`POST …/WidgetReports/widgetBetHistory`, sem `selections`).
  O expandido responde 200 com o mesmo Bearer e é de onde saem pernas, mercado e data.
- **Abertas com janela de 730 dias voltam VAZIAS** (`200 · {"isLastPage":true,"bets":[]}`); com
  365 dias vêm as 9. É o gateway da [`CASA_BETREBELS`](CASA_BETREBELS.md) §2.1, e o recuo do
  inject cobre.
- `credentials:"include"` aceito (o 1º ramo do `pedirPagina`).
- A tela pede as processadas com `statuses:[1,8,21,2,4,18]`; o inject usa `[1,8,2,4,18,7]`. Nesta
  conta, zero aposta no 21 e no 7 em 365 dias (as duas listas trazem as mesmas 18). **O
  significado do 21 não foi medido** (BACKLOG).

### 2.5 Campos da API (expandido)

| Campo | Uso |
|---|---|
| `id` | código (10 dígitos), o "Identificação" do card |
| `type` | 0 simples · 1 múltipla (sistema não medido) |
| `status` | §5 |
| `totalStake` | stake (= `finalStake` em toda a amostra) |
| `totalWin` | retorno na processada; **potencial** na aberta (`remainingTotalWin` igual) |
| `totalOdds` | odd exata (o card mostra 2 casas, truncada: 8,697344 → 8.69) |
| `bonus` | **bônus de acumulada**, já DENTRO do `totalWin`: 30 × 8,697344 = 260,92 + 6,92 = 267,84 |
| `createdDate` | colocação (UTC; o card mostra em SP) |
| `currency` | moeda da conta (`USD`) |
| `selections[]` | pernas: `price`, `status`, `marketName`, `name`, `eventName`, `eventDate` (UTC), `eventScore`, `sportTypeId` |

---

## 3. ID do bilhete

- **Numérico, 10 dígitos**, como em toda Altenar → **dedup forte por ID**. Código real em
  `CODIGO_EXEMPLO`: `5590494619`.

---

## 4. Data

**A coluna Data é a do EVENTO** (`MASTER_OUTPUT §4`), em Brasília, como nas irmãs. `eventDate`
vem em UTC: `2026-10-30T02:00:00Z` é 29/10 23:00 em SP.

---

## 5. Status e Resultado

Enum do motor, regra da [`CASA_ESPORTIVA`](CASA_ESPORTIVA.md) §5. Medido nesta conta:

| `status` | Card | Resultado |
|---|---|---|
| 0 | ABERTO | em aberto (retorno = potencial) |
| 1 | GANHOU / VENCIDO | W, odd = retorno ÷ stake |
| 2 | PERDIDO | L |

Cashout, anulada (`8`) e o `21` sem amostra: status desconhecido sobe cru e "a conferir".

---

## 6 a 8. Boost, cashout e bônus

Regras das irmãs ([`CASA_ESTRELABET`](CASA_ESTRELABET.md) §6-§8 e
[`CASA_VAIDEBET`](CASA_VAIDEBET.md)). **Bônus de acumulada medido:** o `bonus` é pago por fora da
odd e já entra no `totalWin`; o bloco escreve "aposta com bônus (R$ x)" e a odd de W sai de
retorno ÷ stake (8,928 na `5589842458`, card 8.69). A aberta também traz `bonus` (o que pagaria).

---

## 9. Mapa de mercados (Sportaza → `Aposta` global)

Segue o global e o vocabulário Altenar já mapeado nas irmãs. ⚠️ `culture=pt-PT`: os mercados
chegam em **português de Portugal** (`TOTAL DE GOLOS`, `1ª parte - empate devolve aposta`,
`Primeiro set - vencedor`, `Reb.-Ast (incluindo Prorrogação)`). Entra aqui só o que for
**confirmado** no dado real desta casa.

---

## 10. Stake

`totalStake`, número. ⚠️ **O `formatTicketVB` rotula todo dinheiro como `R$`** e não escreve a
linha `Moeda:`. A conta em USD chega com o valor certo (o servidor converte pela moeda do
cadastro), mas **conta cadastrada em BRL converte errado em silêncio**.

---

## 11. Odds

Regra das irmãs: odd **nunca** truncada; W = `retorno ÷ stake`.

---

## 12. Pegadinhas (resumo rápido)

1. **Espelho numerado** — o domínio troca; só os registrados engancham (§1.1).
2. **Conta em USD** — cadastre a conta em USD antes da 1ª captura (§10).
3. **A tela só chama o compacto** — normal; o inject pede o expandido sozinho (§2).
4. **Bônus de acumulada** dentro do retorno — a odd de W não é a do card (§6).
5. **Data do EVENTO, não da colocação** (§4).

---

## 13. Validações específicas

- [ ] O host da aba é um dos registrados (§1.1).
- [ ] A conta foi cadastrada em USD **antes** da 1ª captura.
- [ ] Contagem capturada == o que as abas do histórico mostram (em 30/10/2026: 9 abertas, 18
      processadas em 10 dias).
- [ ] Código de 10 dígitos presente em todo bilhete.

---

## 14. Exemplos golden (bilhetes reais, conta do Feca, 30/10/2026)

| Código | Card | Stake | Odd card | Ganho total | Resultado esperado |
|---|---|---|---|---|---|
| 5590494619 | simples, GANHOU | 75,00 | 1.83 | 137,50 | W @ 1,8334 · 30/10/2026 |
| 5590485064 | simples, PERDIDO | 90,00 | 1.83 | — | L @ 1,8334 · 30/10/2026 |
| 5589842458 | múltipla (3), GANHOU, bônus 6,92 | 30,00 | 8.69 | 267,84 | W @ 8,928 · 29/10/2026 |
| 5590902372 | múltipla (3), PERDIDO | 30,00 | 21.48 | — | L @ 21,483 · 30/10/2026 |
| 5590916289 | múltipla (3), ABERTO | 30,00 | 10.97 | 338,12 (potencial) | aberta · 31/10/2026 |
| 5588982337 | múltipla (3), ABERTO | 30,00 | 6.82 | 210,03 (potencial) | aberta · 30/10/2026 |

Travados em `extensor/harness/casos/sportaza.mjs` (bloco) e `tests/test_adaptador_vb_sportaza.py`
(Ficha).

---

## Feedback para a camada global / MODELO

1. 11ª Altenar registrada sem linha nova de captura, e a 1ª internacional com fixture real.
2. 3ª casa da captura em espelho numerado (Kikobet, Tornadobet): a discussão de declarar a
   família de domínios ficou mais forte.
3. A tela pede o `status 21` nas processadas e o inject não; sem amostra, não mexi no inject
   compartilhado.
