# CASA_DUEL
## Camada de tradução — Duel → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Duel.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> ⚠️ **Casa cripto, sem aviso:** fora de aviso ao grupo de testers (pedido do Feca, 04/10/2026,
> como a Betpanda). Nenhum passo desta casa roda `scripts/avisar_testers.py`.

---

## 1. Identidade

- Casa canônica: `Duel` · site: `duel.com` · sportsbook em `/sports`
- Motor: **BetBy** (`sptpub.com`). ⚠️ **Não é iframe** — o `bt-renderer` monta o app na própria
  página (`duel.sptpub.com/bt-renderer.min.js`), dentro de shadow DOM.
- Moeda: **da conta** (casa cripto). A API manda `currency`; o bloco leva `Moeda: X` quando não é
  real, e quem converte é o servidor ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s393):** a da **base**. Medido em 04/10/2026: já havia 1 conta `Duel` em
> `parceiros` e zero bilhete. É também a grafia da marca.

### 1.1 Espelho da Jonbet/Betboom/Blaze/Betpanda

Sexta casa técnica do mesmo motor, provada no recon de 04/10/2026 (Chrome, sem login):

| Prova | Duel | Betpanda |
|---|---|---|
| `bt-renderer` na própria página | `duel.sptpub.com` | `betpanda.sptpub.com` |
| host da API | `api-a-c7818b61-600 (o mesmo da Betpanda)` | `api-a-c7818b61-600` |
| **hash do operador** | `c7818b61` | `c7818b61` |

O `jb_inject.js` casa por **PATH** (`/my_bets/list`), então o host não importa. A captura usa o
mesmo inject, o mesmo `formatTicketJB` e o mesmo `roboJBPassive`. Harness: `casos/duel.mjs`.

> **Ao mexer numa das BetBy, confira as outras.**

---

## 2. Modo de ingestão e layout

**Captura por API + replay** (SharpenUp · `extensor/jb_inject.js`, compartilhado). Endpoint,
paginação (`skip`/`limit` até `count`) e enum de `status` idênticos à
[`CASA_BETPANDA §2`](CASA_BETPANDA.md). A lista vive no menu de apostas do sportsbook
(`/sports`, rota `bt-path=/bets`).

---

## 2.5 Campos da API

Mesma tabela da [`CASA_JONBET §2.5`](CASA_JONBET.md), conferida na Betpanda.

---

## 3. ID do bilhete

- **Numérico, 19 dígitos**, no card como `ID da aposta` → **dedup forte por ID**.
- Fora do snap por edit-distance do `corrigir_codigos_tsv`, como as outras BetBy.

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente), `MASTER_OUTPUT §4`, como em toda BetBy.

---

## 5. Status e Resultado

Regra da [`CASA_BETPANDA §5`](CASA_BETPANDA.md): `won → W`, `lost → L`, `open` não liquida,
`refund`/`canceled` pela régua do dinheiro. Retorno zero só vira `L` com status cru `lost`.

---

## 6. Boost / promoção

Sem amostra própria. O formatador emite `Bônus aplicado: {…}`; a leitura do ComboBOOST está na
[`CASA_BETPANDA §6`](CASA_BETPANDA.md).

---

## 7. Cashout

Regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`). `cashout_amount` em bilhete **aberto** é
oferta, nunca retorno (o bloco só emite `Cashout executado:` em bilhete resolvido).

---

## 8. Bônus

`freebet_data`, se vier, sai como `Freebet:` para a IA decidir pelo global (`MASTER_RESULTADO §5.8`).

---

## 9. Mapa de mercados (Duel → `Aposta` global)

Sem amostra própria ainda: os mercados seguem o global e o vocabulário BetBy já mapeado na
[`CASA_BETPANDA §9`](CASA_BETPANDA.md) e na [`CASA_JONBET §9`](CASA_JONBET.md). Entra aqui só o
que for **confirmado** no dado real desta casa.

---

## 10. Stake

Campo `sum` (⚠️ **não** `stake`), string com **ponto** decimal, na moeda da conta. Nunca passar
pelo parser de dinheiro BR. A conversão para R$ é do `/salvar`.

---

## 11. Odds

Regra de três degraus do `_oddDeclJB` ([`CASA_BLAZE §11.1`](CASA_BLAZE.md)): `total_k` se ≠ 0,
senão `k`. Sistema: a odd do `W` é `retorno ÷ stake`. Odd **nunca** truncada.

---

## 12. Ruído a ignorar

Long-poll `api/v4/live|prematch/...`, `auth_side`, `promo/widget`, `top/events` — não é bilhete.

---

## 13. Pegadinhas (resumo rápido)

1. **Moeda da CONTA** — cadastre a conta na moeda que ela usa antes da 1ª captura (§1).
   Conta em cripto que não seja USD/USDT (BTC, ETH…) **não tem conversão** no `cambio.py`.
2. **Sem fixture própria** — o harness serve bilhetes da Betpanda no host desta casa (§15).
3. **Data do EVENTO, não da colocação** (§4).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada com a moeda certa **antes** da 1ª captura.
- [ ] Contagem capturada == `count` da API (== o que a aba de todas as apostas mostra).
- [ ] Código de 19 dígitos presente em todo bilhete.
- [ ] Na 1ª captura real: fixture da conta no harness e cards lidos na tela.

---

## 15. Exemplos golden (bilhetes reais)

**Sem amostra própria** (a casa entrou sem conta de teste, s393). O harness prova o espelho com
a fixture da Betpanda; a tabela golden entra na 1ª captura real.

---

## Feedback para a camada global / MODELO

1. Espelho BetBy registrado sem linha nova de captura: casar por PATH segue pagando.
