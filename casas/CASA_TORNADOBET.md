# CASA_TORNADOBET
## Camada de tradução — Tornadobet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Tornadobet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Tornadobet` · site canônico: `tornadobet.com`, que **redireciona para um espelho
  NUMERADO**. Em 25/10/2026 o Feca usava `www.tornadobet82.com` e `tornadobet.com` mandava para
  `www.tornadobet34.com`: o número muda por pessoa e por dia. O sportsbook fica em `/sportsbook`.
- Motor: **Altenar / BIA**, cluster `altenar2`. O `altenarWSDK` monta na própria página (window
  de topo, sem iframe), com `integration=tornadobet` e `culture=en-GB`.
- Moeda: **da conta**, como nas Altenar internacionais. Quem converte é o servidor, pela moeda do
  CADASTRO ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)). **Não medido**
  qual moeda as contas usam.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s428):** `Tornadobet`, a da BASE. Medido em 25/10/2026: `Tornadobet` em `parceiros`
> (1 conta do Gabriel), `bilhetes` (25, de print), `casas_meta`, `correcoes` e `uso_tokens`. Os
> bilhetes de print têm código numérico de 10 dígitos (`5558042202`), o formato do motor: a
> captura dedupa com eles.

### 1.1 Espelho da BetMartini (e das outras Altenar)

Décima casa do mesmo motor, provada no recon de 25/10/2026 (Chrome do Feca, **sem login**):

| Prova | Tornadobet | BetMartini |
|---|---|---|
| SDK | `sb2wsdk-altenar2.biahosted.com` na página | idem |
| `integration` | `tornadobet` | `betmartini` |
| cluster | `altenar2` | `altenar2` |
| `culture` do widget | `en-GB` | `en-gb` (pela URL) |

O gateway de histórico responde **403** sem sessão na rota real e numa falsa, então a prova
"401 contra 404" da s392 não separa nada aqui. O `vb_inject.js` casa por **PATH**
(`widgetExpandedBetHistory`), então o host não importa; o que separa as marcas é o `integration`
do corpo aprendido, preservado no replay. Harness: `casos/tornadobet.mjs`.

> **Ao mexer numa das Altenar, confira as outras.**

> ⚠️ **Espelho numerado.** Registrados: `tornadobet.com`, `tornadobet82.com` e
> `tornadobet34.com` (manifest, `popup.js`, `_HOSTS_POR_CASA`). O match do Chrome **não aceita
> curinga no meio do domínio**: num número novo a extensão **não engancha** até o domínio entrar
> nos três lugares e sair versão nova. Sintoma: "0 bilhetes" com a aba aberta no histórico.
> Confira primeiro o host da aba.

---

## 2. Modo de ingestão e layout

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js`, compartilhado). Endpoint,
abas (`statuses`), paginação (`pageNumber` até `isLastPage`) e autenticação (Bearer) idênticos à
[`CASA_ESTRELABET`](CASA_ESTRELABET.md) §2. **Não medido:** se o histórico desta casa dispara o
widget expandido ou só o compacto, se o gateway aceita `credentials:"include"` para este tenant
e se ele devolve vazio para janela larga ([`CASA_BETREBELS`](CASA_BETREBELS.md) §2.1). O inject
cobre os três casos.

**Ficha:** família `vb` (`app/adaptadores/vb.py`), a mesma da BetMartini. `TORNADOBET` está nas
3 listas da Railway desde a 1ª versão.

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

## 6. Boost / promoção

Regras das irmãs ([`CASA_ESTRELABET`](CASA_ESTRELABET.md) §6). Retorno de aberta é **potencial**.

---

## 7. Cashout

Regra das irmãs ([`CASA_ESTRELABET`](CASA_ESTRELABET.md) §7). `cashOutValue` em aberta é oferta,
nunca liquidação.

---

## 8. Bônus

Regra das irmãs ([`CASA_ESTRELABET`](CASA_ESTRELABET.md) §8 e [`CASA_VAIDEBET`](CASA_VAIDEBET.md)).

---

## 9. Mapa de mercados (Tornadobet → `Aposta` global)

Sem amostra própria ainda: segue o global e o vocabulário Altenar já mapeado nas irmãs. O widget
pediu `culture=en-GB`, então os nomes de mercado devem chegar em **inglês**, como na BetMartini.
Entra aqui só o que for **confirmado** no dado real desta casa.

---

## 10. Stake

`totalStake`, número. ⚠️ **O `formatTicketVB` rotula todo dinheiro como `R$`** e não escreve a
linha `Moeda:`. Numa conta em outra moeda o servidor converte pela moeda do cadastro, mas o aviso
de moeda divergente **não dispara**: conta cadastrada na moeda errada converte errado em silêncio.

---

## 11. Odds

Regra das irmãs: odd **nunca** truncada; W = `retorno ÷ stake` (bônus pago por fora da odd).

---

## 12. Ruído a ignorar

O mesmo das irmãs Altenar ([`CASA_ESTRELABET`](CASA_ESTRELABET.md)).

---

## 13. Pegadinhas (resumo rápido)

1. **Espelho numerado** — o domínio troca por pessoa e por dia; só os registrados engancham (§1.1).
2. **Moeda da CONTA** — confira o cadastro antes da 1ª captura (§10).
3. **Idioma** — mercados possivelmente em inglês (§9).
4. **Sem fixture própria** — o harness serve bilhetes da Estrela Bet no host desta casa.

---

## 14. Validações específicas

- [ ] O host da aba é um dos registrados (§1.1).
- [ ] A conta foi cadastrada com a moeda certa **antes** da 1ª captura.
- [ ] Contagem capturada == o que as abas do histórico mostram (abertas inclusive).
- [ ] Os 25 bilhetes de print do Gabriel dedupam com a captura (mesmo código de 10 dígitos).
- [ ] Na 1ª captura real: fixture da conta no harness, cards lidos na tela e corpo real
      (`culture`, `countryCode`, `timezoneOffset`) conferido.

---

## 15. Exemplos golden (bilhetes reais)

**Sem amostra de captura** (a casa entrou sem conta de teste, s428). O código `5558042202` é de
um bilhete de print real da base (Gabriel, 21/10/2026). A tabela golden entra na 1ª captura.

---

## Feedback para a camada global / MODELO

1. 10ª Altenar registrada sem linha nova de captura, como a Kikobet.
2. Segunda casa em espelho numerado no motor (depois da Kikobet), e aqui o número difere entre
   pessoas no MESMO dia. Reforça a pendência de declarar a família de domínios.
