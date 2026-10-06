# CASA_BETREBELS
## Camada de tradução — Betrebels → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betrebels.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betrebels` · site: `betrebels.gr` (grega) · sportsbook em `/sports`
- Motor: **Altenar / BIA**, cluster `altenar2`. O `altenarWSDK` monta na própria página (window
  de topo, sem iframe), com `integration=betrebels`.
- Moeda: **da conta.** Medido em 05/10/2026: há conta em **real** (Feca) e em **USDT**
  (Gabriel). Quem converte é o servidor, pela moeda do CADASTRO
  ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s395):** a da **base**. Medido em 05/10/2026: 1 conta `Betrebels` em `parceiros` e
> em `casas_meta`, zero bilhete. A marca escreve `BetRebels`.

### 1.1 Espelho da VaideBet/Esportiva/Jogo de Ouro/Betpix365/Estrela Bet

Sexta casa do mesmo motor, provada no recon de 05/10/2026 (Chrome, sem login):

| Prova | Betrebels | Estrela Bet |
|---|---|---|
| SDK | `sb2wsdk-altenar2.biahosted.com` na página | idem |
| `integration` | `betrebels` | `estrelabet` |
| cluster | `altenar2` | `altenar2` |

O `vb_inject.js` casa por **PATH** (`widgetExpandedBetHistory`), então o host não importa; o que
separa as marcas é o `integration` do corpo aprendido, preservado no replay. Harness:
`casos/betrebels.mjs`.

> **Ao mexer numa das Altenar, confira as outras.**

---

## 2. Modo de ingestão e layout

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js`, compartilhado). Endpoint,
abas (`statuses`), paginação (`pageNumber` até `isLastPage`) e autenticação (Bearer) idênticos à
[`CASA_ESTRELABET`](CASA_ESTRELABET.md) §2. **Não medido:** se o histórico desta casa dispara o
widget expandido ou só o compacto, e se o gateway aceita `credentials:"include"` para este
tenant. O inject cobre os dois casos (molde do compacto e fallback sem credencial).

---

## 3. ID do bilhete

- **Numérico, 10 dígitos**, como em toda Altenar → **dedup forte por ID**.

---

## 4. Data

**A coluna Data é a do EVENTO** (`MASTER_OUTPUT §4`), em Brasília, como nas irmãs.

---

## 5. Status e Resultado

Enum do motor, regra da [`CASA_ESPORTIVA`](CASA_ESPORTIVA.md) §5 (inclusive `status 8` = anulada).
Status desconhecido sobe cru e "a conferir".

---

## 6 a 8. Boost, cashout e bônus

Regras das irmãs ([`CASA_ESTRELABET`](CASA_ESTRELABET.md) §6-§8 e
[`CASA_VAIDEBET`](CASA_VAIDEBET.md)). Retorno de aberta é **potencial**; `cashOutValue` em
aberta é oferta, nunca liquidação.

---

## 9. Mapa de mercados (Betrebels → `Aposta` global)

Sem amostra própria ainda: segue o global e o vocabulário Altenar já mapeado nas irmãs. Entra
aqui só o que for **confirmado** no dado real desta casa (inclusive se a conta exibe mercado em
inglês ou grego).

---

## 10. Stake

`totalStake`, número. ⚠️ **O `formatTicketVB` rotula todo dinheiro como `R$`** e não escreve a
linha `Moeda:`. Numa conta em USDT o valor chega certo (o servidor converte pela moeda do
cadastro), mas o aviso de moeda divergente **não dispara** — conta cadastrada na moeda errada
converte errado em silêncio.

---

## 11. Odds

Regra das irmãs: odd **nunca** truncada; W = `retorno ÷ stake` (bônus pago por fora da odd).

---

## 12. Pegadinhas (resumo rápido)

1. **Moeda da CONTA** — confira o cadastro antes da 1ª captura (§10).
2. **Sem fixture própria** — o harness serve bilhetes da Estrela Bet no host desta casa.
3. **Data do EVENTO, não da colocação** (§4).

---

## 13. Validações específicas

- [ ] A conta foi cadastrada com a moeda certa **antes** da 1ª captura.
- [ ] Contagem capturada == o que as abas do histórico mostram.
- [ ] Código de 10 dígitos presente em todo bilhete.
- [ ] Na 1ª captura real: fixture da conta no harness, cards lidos na tela, corpo real
      (`culture`, `countryCode`, `timezoneOffset`) conferido.

---

## 14. Exemplos golden (bilhetes reais)

**Sem amostra própria** (a casa entrou sem conta de teste, s395). A tabela golden entra na 1ª
captura real.

---

## Feedback para a camada global / MODELO

1. 6ª Altenar registrada sem linha nova de captura: casar por PATH e preservar o `integration`
   do corpo aprendido segue pagando.
