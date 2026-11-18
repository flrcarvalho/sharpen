# CASA_GIROCERTO
## Camada de tradução — GiroCerto → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da GiroCerto.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `GiroCerto` · site: `girocerto.fun` · apostas em **Esportes → Minhas apostas**
  (`/esportes?aba=apostas`, abas **Em aberto** e **Encerradas**).
- Locale: pt-BR. Mercado e seleção vêm em **português** (`1º tempo - handicap 0.0, -0.5`,
  `Chance dupla`, `Empate devolve aposta`); o esporte vem em **inglês** (`football`,
  `basketball`, `tennis`); times verbatim.
- Moeda: **real**. A API não manda campo de moeda; a casa só opera em R$.
- **Dinheiro em CENTAVOS inteiros** (`stakeCents: 75000` = R$ 750,00). Odd em número.
- Plataforma **PRÓPRIA**: site Next.js, API `/api/esportes/*` no mesmo domínio. Não é Altenar,
  Kambi, BetBy nem BetConstruct. Família `gc` (inject `gc_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s455):** `GiroCerto`, a da base. Medido em 15/11/2026: 107 bilhetes (Jaao26, por
> print), 1 conta, 1 `casas_meta`, 241 `correcoes`, 11 `uso_tokens`, uma grafia só.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API, busca ativa** (SharpenUp · `extensor/gc_inject.js`).

```
GET https://girocerto.fun/api/esportes/bets          (só o cookie)
→ [ { "id", "code", "kind", "status", "stakeCents", "odds", "originalOdds", … }, … ]
```

Medido no recon de 15/11/2026 (Chrome do Feca):

- **Só o cookie da sessão basta**: `fetch` cru, sem header, devolve 200. Não há token.
- **A lista vem DENTRO DO HTML** (Next.js RSC, `self.__next_f`, prop `tickets` do `MyBets`).
  Abrir a tela não dispara chamada de lista: o inject pede a API ele mesmo.
- **Sem paginação: são os 50 mais recentes.** Nenhum parâmetro muda isso (`limit`, `offset`,
  `page`, `cursor`, `before`, `take/skip` devolvem os mesmos 50), e a tela também só mostra 50.
  O fim é a 1ª resposta. Quem não captura com frequência perde o que passou do 50º: **o que
  saiu da janela da API só entra por print**, e por isso o print desta casa segue aceito
  (`captura.PRINT_LIBERADO`, decisão do Feca de 16/11/2026), ao contrário das outras casas da Ficha.
- ⚠️ **`POST` na mesma URL FAZ APOSTA.** O inject só manda `GET` e só lê resposta em array.
- `GET /api/esportes/bets/<uuid>` (detalhe) e `POST /api/esportes/bets/cashout/quotes`
  (cotação de cashout) existem e não são usados: a lista já traz as pernas.
- A CSP não restringe `connect-src`: no recon, o JSON saiu por receptor local (127.0.0.1).

### 2.3 Layout do bilhete (card)

Card com `Simples · dd/mm, hh:mm` (colocação, Brasília), rótulo **GANHOU / PERDEU / ANULADA**,
seleção, mercado (com "· meio ganha/meio perdida (metade devolvida)" e "· anulada"), jogo,
cotação, **Valor apostado** e **Valor recebido** (ganha/anulada) ou **Ganho potencial**
(perdida), e o código no rodapé.

- ⚠️ A **perdida** mostra o **potencial**, nunca dinheiro recebido.
- ⚠️ A **meia derrota** diz "PERDEU" e mostra só o potencial, mas **metade voltou**
  (`creditedCents` = stake ÷ 2).
- Na anulada e nas meias, a cotação aparece **dupla**: a original e a efetiva (`1.76 1.00`,
  `1.825 1.413`).

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na GiroCerto |
|---|---|
| `code` | 10 caracteres `[A-Z0-9]` (`ZHUUMZ423Z`), o rodapé do card → `[Código:]` |
| `id` | UUID interno. **Nunca** vai para o marcador |
| `kind` | `single` no recon; `multiple` medido na s461 (2 do Gabriel). O `builder` não foi medido |
| `status` | `won` · `lost` · `void` na amostra; o JS da casa conhece `accepted`, `pending`, `placing`, `cashing`, `voiding` (em aberto), `cashed_out` e `rejected` |
| `stakeCents` / `originalStakeCents` | stake em centavos (iguais na amostra) |
| `originalOdds` | **a odd da aposta**, a da colocação |
| `odds` | ⚠️ **reescrita na liquidação**: anulada e meia derrota → `1`; meia vitória → a efetiva (`1.413`). Nunca entra |
| `payoutCents` | stake × odd, o **potencial**, até na perdida. Nunca entra |
| `creditedCents` | **o dinheiro que voltou**: 0 na perdida, a stake na anulada, metade na meia derrota |
| `cashedCents` · `lastCashout` | 0 / `null` em toda a amostra |
| `freebet` | `false` em toda a amostra |
| `placedAt` · `settledAt` · `decidedAt` · `acceptAt` | ISO **UTC** com `Z` |
| `legs[]` | `sport`, `event`, `market`, `pick`, `odds` (a da colocação, **não** é reescrita), `startsAt` (UTC), `status`, `live`, `earlyPayout`, `paidEarly` |
| `legs[].status` | `won` · `lost` · `void` · `half_won` · `half_lost`; o JS conhece `open` |

**Ficha (s455):** adaptador `app/adaptadores/gc.py`, gate `tests/test_adaptador_gc.py`. A Ficha
aceita as simples cujo dinheiro fecha (§5), meias inclusive, e recusa o resto, que vai à IA pelo
texto: aberta, `rejected`, cashout, freebet, múltipla e status desconhecido. Medido na fixture:
**50 de 50 aceitas**.

---

## 3. ID do bilhete

`code` do bilhete (`ZHUUMZ423Z`). Uma série só, sem prefixo de tipo. Os 107 bilhetes que a
base já tinha (por print) usam o mesmo `code`: 106 com 10 caracteres e 1 com 9 (erro de
leitura do print).

---

## 4. Data

- **Coluna Data = dia do EVENTO em Brasília** (`legs[].startsAt` UTC → São Paulo).
  `2026-11-02T01:30:00Z` é **01/11** às 22:30.
- O bloco também leva a colocação (`placedAt`, que o card mostra em Brasília).

---

## 5. Status e Resultado

| `status` · perna · dinheiro (`creditedCents`) | Leitura | Código |
|---|---|---|
| `accepted` / `pending` / `placing` / `cashing` / `voiding` | Em aberto | *(vazio — não liquidar)* |
| `lost` · crédito 0 | Perdeu | `L` |
| `void` · crédito = stake | Devolvida | `V`, odd original |
| `won` · crédito = stake × `originalOdds` (± 1 centavo: a casa corta para baixo) | Ganhou | `W` |
| `won` · perna `half_won` · crédito = stake ÷ 2 × odd + stake ÷ 2 | Meia vitória | `HW`, odd original |
| `lost` · perna `half_lost` · crédito = stake ÷ 2 | Meia derrota | `HL`, odd original |
| múltipla `lost` · crédito 0 | Perdeu | `L`, odd original; data = início da perna perdida mais cedo |
| múltipla `won` · pernas `won`/`void` · crédito = stake × produto das pernas GANHAS | Ganhou com perna anulada | `W`, odd = retorno ÷ stake |
| `rejected` | a casa recusou: **não é aposta** | *(o robô pula; nunca sobe)* |
| `cashed_out`, crédito que não fecha, freebet, status novo | sobe cru | *(a conferir)* |

O bloco sempre leva `Status (API): status … · kind …`. Medido: `won` 27 (1 meia vitória),
`lost` 16 (2 meias derrotas), `void` 7.

---

## 6. Boost / promoção

A home anuncia "Super Odds" e "Golden Boost". Nenhuma aposta da amostra é turbinada, e a API
não tem campo de boost no bilhete. ⚠️ A diferença `odds` × `originalOdds` da amostra **não é
boost**: é a reescrita da liquidação (§2.5). Turbinada real: salvar o JSON como fixture antes
de liberar.

---

## 7. Cashout

Sem amostra. O JS da casa tem `cashed_out`, `cashing`, `cashedCents` e `lastCashout`, e cota
o cashout em `POST /api/esportes/bets/cashout/quotes`. Até haver amostra, `cashed_out` ou
`cashedCents` > 0 sobe **a conferir** (formatador) e a Ficha **recusa**.

---

## 8. Bônus

`freebet` no bilhete (`false` na amostra). Freebet real sobe a conferir até ser medida
(`MASTER_RESULTADO §5.8` decide o resto).

---

## 9. Mapa de mercados (GiroCerto → `Aposta` global)

Mercados vistos na amostra (`1x2`, `Chance dupla`, `Empate devolve aposta`, `Handicap`,
`Total asiático`, `Total de escanteios`, `Escanteios handicap asiático`, `Gols por equipe`,
`Cartões por equipe`, `Vencedor` no tênis e `Handicap, total e vencedor (incluindo
Prorrogação)` no basquete): a categoria sai do `MASTER_APOSTAS` pelo objeto medido, sem atalho
aqui. Os prefixos `1º tempo -` e `- outras linhas` são do período/variação, não de categoria.

---

## 10. Stake

`stakeCents ÷ 100`, em R$.

---

## 11. Odds

- **A odd da aposta é `originalOdds`**. A `odds` do bilhete é reescrita ao liquidar e nunca entra.
- **W:** `creditedCents ÷ stakeCents` conciliado com `originalOdds`: a odd da casa vence se
  fecha o retorno em 1 centavo (a casa paga cortando o centavo: 336,08 × 3,45 = 1.159,476 →
  1.159,47).
- ⚠️ **Ficha × IA no corte do centavo:** a Ficha deriva `W` com a régua global (fecha em meio
  centavo; senão retorno ÷ stake). No HMD2Y7X9E9 ela dá 3,44998… e o texto dá 3,45. O P/L é o
  mesmo; a odd segue a régua da Ficha.
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `id` (UUID), `selectionId`, `eventId`, `marketId`, `reason`, `acceptAt`, `decidedAt`.
- `odds` do bilhete (reescrita) e `payoutCents` (potencial).
- `legs[].earlyPayout` (mercado com pagamento antecipado): só informa; `paidEarly` `false` em toda a amostra.

---

## 13. Pegadinhas (resumo rápido)

1. **`odds` reescrita na liquidação** (anulada → 1): a odd é `originalOdds` (§2.5).
2. **Perdida mostra o potencial**; meia derrota diz "PERDEU" com metade devolvida (§2.3).
3. **Pagamento cortado no centavo** (§11).
4. **Só os 50 mais recentes** pela API (§2.1).
5. **POST na mesma URL faz aposta** (§2.1).

---

## 14. Validações específicas

- [ ] Nenhuma perdida com o potencial como retorno; nenhuma aberta liquidada.
- [ ] Coluna Data = evento em São Paulo.
- [ ] Meias derrotas como `HL` com metade da stake (GGGT2EW6RZ, TJLVHW8CG7).
- [ ] **Aberta real:** conferir o `status` (`accepted`?) e o texto "em aberto" no bloco.
- [x] **Múltipla** (s461, `girocerto.multiplas.json`, Gabriel 16-17/11/2026): GRSQYRB7FZ perdida
      e Q6GEKXMSRV ganha com 2 pernas anuladas (a casa grava `odds` 2.5, a efetiva). Até a 0.7.90
      o bloco dizia "a conferir" e a Ficha recusava; a IA acertou o resultado e errou a data da
      Q6GEKXMSRV (16/11, a colocação), corrigida por `scripts/corrigir_data_girocerto_s461.py`.
- [ ] **Builder, múltipla com meia, cashout, freebet, turbinada:** salvar o JSON como fixture,
      trocar o clone do harness e liberar na Ficha.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 15/11/2026 (**50 bilhetes**, todos liquidados, todos simples):
`extensor/harness/fixtures/girocerto.bets.json`. Fonte = card (rótulo, cotação, valores, hora).

| Código | Mercado | Estado | Stake (R$) | Odd | Retorno (R$) | Colocação | Evento (SP) |
|---|---|---|---|---|---|---|---|
| ZHUUMZ423Z | 1º tempo - total asiático 1.0, 1.5 | `won` | 750,00 | 2,02 | 1.515,00 | 01/11/2026 21:54 | 01/11/2026 22:30 |
| HMD2Y7X9E9 | Handicap - outras linhas 0.0, +0.5 | `won` | 336,08 | 3,45 | 1.159,47 | 01/11/2026 13:45 | 01/11/2026 19:00 |
| QTPTYJD9Z3 | Handicap, total e vencedor (incl. Prorrogação) 1 | `lost` | 750,00 | 2,50 | 0 (card: potencial 1.875,00) | 01/11/2026 21:24 | 02/11/2026 12:00 |
| P4YT7HM9MW | Empate devolve aposta | `void` | 1.500,00 | 1,76 (card 1.76 1.00) | 1.500,00 | 01/11/2026 20:54 | 01/11/2026 21:00 |
| 6M3YQUCREG | Handicap +1.0,+1.5 | `won` · `half_won` → HW | 300,00 | 1,825 | 423,75 | 01/11/2026 13:38 | 01/11/2026 14:00 |
| GGGT2EW6RZ | 1º tempo - handicap 0.0, -0.5 | `lost` · `half_lost` → HL | 525,00 | 2,025 | 262,50 (o card não mostra) | 01/11/2026 16:25 | 01/11/2026 23:00 |

Múltiplas (s461): **GRSQYRB7FZ** L @ 7,252 (3 pernas, data 17/11) e **Q6GEKXMSRV** W @ 2,5 (R$ 300 → R$ 750,
2 pernas anuladas, odd cheia 14,795, data 17/11), em `extensor/harness/fixtures/girocerto.multiplas.json`.

**Sem amostra:** aberta · builder · múltipla com meia · cashout · freebet · turbinada.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão (**SharpenUp 0.7.84**) e dar **Ctrl+Shift+R** na aba da GiroCerto
   **e** na aba do painel.
2. Abrir `girocerto.fun` logado (a tela "Minhas apostas" não é obrigatória: o inject busca a
   lista só com o cookie).
3. Conectar → Copiar bilhetes. O toast diz `respostas` e `vistos`; zero respostas = sessão
   caída.
4. Conferir no dashboard: contagem, código de 10 caracteres, data do evento, odd das
   anuladas (a original, nunca 1) e as meias derrotas como `HL`.
5. Na 1ª aberta/múltipla/cashout, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

1. **Odd reescrita na liquidação.** 1ª casa em que o campo `odds` do bilhete muda depois de
   liquidar (vira 1 na anulada). Toda leitura de "odd" de API precisa conferir a anulada.
2. **API com janela fixa (50) e sem paginação.** O histórico além da janela não se captura:
   captura frequente ou print.
