# CASA_VAVADA
## Camada de tradução — Vavada → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Vavada.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Vavada` · site: `vavada.com` (cassino cripto internacional, Bitcoin e USDT) ·
  a raiz redireciona para `/pt-br` e o sportsbook fica em `/pt-br/sports`
- Motor: **Altenar / BIA**, cluster `altenar2`. O `altenarWSDK` monta na própria página (window
  de topo), com `integration=vavada`.
- Moeda: **da conta**, como na Betrebels e na BetMartini. Quem converte é o servidor, pela moeda
  do CADASTRO ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)). **Não
  medido** qual moeda as contas usam (o site anuncia cripto).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s403):** a da **marca** em title case (`Vavada`; o site escreve `VAVADA`). Nenhuma
> menção a `vavada` no repo. **A base NÃO foi medida** nesta sessão: antes da 1ª conta, rode
> `select casa, count(*) from parceiros where lower(casa) like '%vavada%' group by 1` (e o
> mesmo em `bilhetes` e `casas_meta`); grafia diferente lá manda sobre esta.

### 1.1 Espelho da VaideBet/Esportiva/Jogo de Ouro/Betpix365/Estrela Bet/Betrebels/BetMartini

Oitava casa do mesmo motor, provada no recon de 08/10/2026 (Chrome, sem login):

| Prova | Vavada | BetMartini |
|---|---|---|
| SDK | `sb2wsdk-altenar2.biahosted.com` na página | idem |
| `integration` | `vavada` | `betmartini` |
| cluster | `altenar2` | `altenar2` |
| idioma | `pt-br` | `en-gb` |

O `vb_inject.js` casa por **PATH** (`widgetExpandedBetHistory`), então o host não importa; o que
separa as marcas é o `integration` do corpo aprendido, preservado no replay. Harness:
`casos/vavada.mjs`.

> **Ao mexer numa das Altenar, confira as outras.**

> ⚠️ **Espelhos de domínio.** Cassino desse tipo costuma operar domínios espelho quando o
> principal é bloqueado. Só `vavada.com` está registrado (manifest, `popup.js`,
> `_HOSTS_POR_CASA`). Se a captura não enganchar, confira primeiro o host da aba.

---

## 2. Modo de ingestão e layout

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js`, compartilhado). Endpoint,
abas (`statuses`), paginação (`pageNumber` até `isLastPage`) e autenticação (Bearer) idênticos à
[`CASA_ESTRELABET`](CASA_ESTRELABET.md) §2. **Não medido:** se o histórico desta casa dispara o
widget expandido ou só o compacto, se o gateway aceita `credentials:"include"` para este tenant
e se ele devolve vazio para janela larga, como o da Betrebels
([`CASA_BETREBELS`](CASA_BETREBELS.md) §2.1). O inject cobre os três casos.

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

## 9. Mapa de mercados (Vavada → `Aposta` global)

Sem amostra própria ainda: segue o global e o vocabulário Altenar já mapeado nas irmãs. O site
abre em **pt-br** para quem vem do Brasil, então os nomes de mercado devem chegar como nas irmãs
brasileiras (não medido). Entra aqui só o que for **confirmado** no dado real desta casa.

---

## 10. Stake

`totalStake`, número. ⚠️ **O `formatTicketVB` rotula todo dinheiro como `R$`** e não escreve a
linha `Moeda:`. Numa conta em outra moeda (USDT, por exemplo) o valor chega certo (o servidor
converte pela moeda do cadastro), mas o aviso de moeda divergente **não dispara** — conta
cadastrada na moeda errada converte errado em silêncio.

---

## 11. Odds

Regra das irmãs: odd **nunca** truncada; W = `retorno ÷ stake` (bônus pago por fora da odd).

---

## 12. Pegadinhas (resumo rápido)

1. **Moeda da CONTA** — casa cripto: confira o cadastro antes da 1ª captura (§10).
2. **Domínio espelho** — só `vavada.com` engancha (§1.1).
3. **Sem fixture própria** — o harness serve bilhetes da Estrela Bet no host desta casa.
4. **Data do EVENTO, não da colocação** (§4).

---

## 13. Validações específicas

- [ ] A conta foi cadastrada com a moeda certa **antes** da 1ª captura.
- [ ] Contagem capturada == o que as abas do histórico mostram (abertas inclusive: §2).
- [ ] Código de 10 dígitos presente em todo bilhete.
- [ ] Na 1ª captura real: fixture da conta no harness, cards lidos na tela, corpo real
      (`culture`, `countryCode`, `timezoneOffset`) conferido e `CODIGO_EXEMPLO` trocado.

---

## 14. Exemplos golden (bilhetes reais)

**Sem amostra própria** (a casa entrou sem conta de teste, s403). A tabela golden entra na 1ª
captura real.

---

## Feedback para a camada global / MODELO

1. 8ª Altenar registrada sem linha nova de captura, como a BetMartini.
