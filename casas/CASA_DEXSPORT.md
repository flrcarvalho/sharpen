# CASA_DEXSPORT
## Camada de tradução — DEX Sport → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Dexsport.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

> ⚠️ **SIGILO (decisão do Feca, 02/10/2026):** casa normal no seletor, mas **fora** de aviso
> ao grupo de testers, do `changelog.json` e da home. Nenhum passo desta casa roda
> `scripts/avisar_testers.py` com `--enviar` sem o `--so-changelog` e nota genérica.

---

## 1. Identidade

- Casa canônica: `DEX Sport` · site: `dexsport.io` · esportes em `/pt/sports/`
- Locale: pt-BR no SDK de esportes (`locale=pt`) · Moeda: **USDT** (`currency: "usdt"`, minúsculo)
- **Números JSON** (`25`, `93.75`, `3.76`) — nada de string, nada de milésimos.
- Plataforma **PRÓPRIA** (primeira casa do motor). O SDK de esportes (`sportsbook.…`) roda num
  **shadow DOM na própria página**, sem iframe, e fala com `prod.dexsport.work`.
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s391, decisão do Feca):** `DEX Sport`, a da conta que ele criou em 03/10/2026. A 1ª
> versão registrou a da marca (`Dexsport`) e a conta caiu em **modo print** (o Snap abriu na
> casa): o round-trip `_display_to_key` compara a caixa, mas **não ignora espaço**, então
> `DEX Sport` não casava com `Dexsport`. E o `casa_canonica` só reconhece grafia que **já existe
> em `parceiros`** — com a base vazia, o que se digita entra verbatim. **A base manda.**

### 1.1 A moeda é da conta

Cadastre a conta em **USDT**. O `/salvar` converte a stake para R$ pela cotação do dia da
aposta; a tela mostra o original embaixo ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).
O bloco capturado leva `Moeda: usdt` e o dinheiro rotulado nela. **Os números do TSV são os
da casa, em USDT**; quem converte é o servidor.

### 1.2 Esporte: o SDK manda um ID, não um nome

| `disciplineId` | Esporte canônico |
|---|---|
| `football` | Futebol |
| `basketball` | Basquete |
| `formula1` | F1 |
| `baseball` | Baseball |
| `tennis` | Tênis |
| `hockey` | Hóquei |
| `volleyball` | Vôlei |
| `rugby-union` | Rugby |
| `american-football` | Futebol Americano |

Só os ids vistos na amostra. Id novo: traduzir pelo `MASTER_ESPORTES`, nunca verbatim.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/dx_inject.js`).

```
GET https://prod.dexsport.work//api/sportsbook/history/tickets?status=<placed|finished>&page=N&locale=pt
    Accept: application/json · Authorization: <token da sessão do SDK>
→ { "data": [ … ], "meta": { pageNumber, pageSize: 25, totalPages, totalRows } }
```

- A **barra dupla** no caminho é da casa (medido).
- A lista sai por **XHR**. O inject aprende a URL e o `Authorization` da chamada real e
  repagina `placed` e `finished` por `page` até `meta.totalPages`. O replay também vai por XHR.
- Painel: **Esportes → "Minhas apostas"** (dentro do SDK), abas `Abertas` (`placed`) e
  `Concluídas` (`finished`). A rolagem real pede `page=2`; o replay não depende dela.
- Medido na conta do Feca: `placed` 12 (1 página), `finished` 29 (25 + 4) = **41**.

### 2.2 ⚠️ A OUTRA lista — nunca usar

O perfil do site (`/pt/profile/#history`) tem um histórico próprio, `POST dexsport.io/api/v3/
txs_list` (`{offset, limit, game-type: "SB", order_by: "-id"}`; o "Mostrar mais" aumenta o
`limit` de 7 em 7). Ele é **inadequado para captura**:

- carrega, dentro de cada bilhete (`arguments`), um **`token` de 57 caracteres, o `ip` e o
  `userId`** — credencial na resposta;
- lê o retorno de `reserve`, que **na perdida guarda o potencial**;
- data em texto `"03.10.26"` + hora **em UTC**; mercados em inglês.

O `RX` do inject só casa o caminho do SDK.

### 2.3 Layout do bilhete (SDK)

Card com data/hora **da colocação** em São Paulo ("1 de out. · 15:16"), `ID da aposta` com o
UUID inteiro e botão "Copiar ID"; tipo (`Múltipla` / `Simples`) e nº de apostas; `Odd`,
`Aposta … USDT`; selo `WIN` / `LOST`; `Vitória possível … USDT`.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Dexsport |
|---|---|
| `id` | UUID — bate com `ID da aposta` do card |
| `number` | sequencial da conta (não é ID de dedup) |
| `amount` | stake, número, em USDT |
| `coefficient` | odd da **colocação** (produto das pernas); é a do card na perdida e na aberta |
| `payoutCoefficient` | odd **liquidada**: 0 na perdida e na aberta, 3,75 no `b4836669` (perna anulada) |
| `payout` | retorno liquidado; **0 também na aberta** |
| `possiblePayout` | retorno potencial |
| `result` | 0 aberta · 1 ganha · 2 perdida (cru) |
| `status` | 2 aberta · 3 concluída (cru) |
| `settlementStatus` | acompanha o `result` |
| `ticketType` | 0 simples · 1 múltipla |
| `placedAt` / `finishedAt` | epoch em segundos |
| `boosterCoefficient` / `payoutBoosterCoefficient` | 1 em toda a amostra |
| `bonusType` | 0 em toda a amostra |
| `nickname` | **removido da fixture** (identidade) |
| `bets[].status` | 0 não decidida · 1 ganha · 2 perdida · **6 anulada** |
| `bets[].coefficient` / `payoutCoefficient` | odd da perna; a anulada paga 1 |
| `bets[].eventDate` | ISO em **UTC** (`…T14:00:00.000Z`) |
| `bets[].eventMarket.name` · `outcomeName` · `event.name` | mercado, seleção e confronto em pt-BR |
| `bets[].disciplineId` | id do esporte (§1.2) |

---

## 3. ID do bilhete

- **UUID** (ex.: `3345134c-ef5a-4dac-a4cd-1c4344961467`), estampado inteiro no card.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`).

---

## 4. Data

**A coluna Data é a do EVENTO** (perna mais recente). `eventDate` vem em **UTC** e o inject o
converte em epoch; o bloco sai em São Paulo. A diferença muda o dia: jogo às 02:05 UTC de 03/10
é 23:05 de 02/10 em São Paulo. A colocação (`placedAt`) também sai em São Paulo e bate com o
card ao minuto.

---

## 5. Status e Resultado

| `status` · `result` | Leitura | Código |
|---|---|---|
| `2` · `0` | Em aberto | *(vazio — não liquidar)* |
| `3` · `1` | Ganhou — conferir o dinheiro | `W` |
| `3` · `2` | Perdeu (`payout` 0) | `L` |
| `3` · outro, ou `payout` = `amount` | sem caso na amostra | regra global; o bloco sobe "a conferir" |

Medido: `result` 1 (6) · 2 (23) · 0 (12) em 41. **Sem amostra:** devolvida, cancelada,
cashout executado, meio ganho/perdido.

> ⚠️ **Retorno zero não é derrota sozinho**: a aberta também vem com `payout` 0. Só `result` 2
> numa concluída é `L`; qualquer outra combinação sobe "a conferir".

> Perna `status: 0` dentro de bilhete **concluído** (`603158df`) é a casa encerrando a múltipla
> na primeira perna perdida. Não reabre o bilhete.

---

## 6. Boost / promoção

`boosterCoefficient` = 1 em toda a amostra. Se vier ≠ 1, o bloco emite `Boost: ×N` e vale a
regra global do `W` (`retorno ÷ stake`).

---

## 7. Cashout

O SDK consulta a **oferta** de cashout por bilhete aberto em `GET prod.dexsport.work/api/
sportsbook/cashout/tickets/<uuid>`. É oferta, não retorno: o inject ignora. Nenhum cashout
executado na amostra; quando houver, vale a regra global (`MASTER_RESULTADO §5.1.2` e `§5.6`).

---

## 8. Bônus

`bonusType` = 0 em toda a amostra. Se vier ≠ 0, o bloco emite `Bônus: tipo N` para a IA decidir
pelo global.

---

## 9. Mapa de mercados (Dexsport → `Aposta` global)

Só os mercados **confirmados** no dado real, e só onde a tradução é direta (camada fina):

| Dexsport exibe | Aposta global |
|---|---|
| `Vencedor` · `Vencedor. Set 1` · `Vencedor. 1ª metade` · `Vencedor. Tempo principal` | ML |
| `Handicap` · `Handicap. Com prorrogação` · `Handicap. 1º tempo` · `Handicap. Set 1` | Handicap |
| `O empate anula a aposta` | DNB |
| `Chance dupla` | Dupla Chance |
| `Ambas as equipes vão marcar` | Ambas Marcam |
| `Escanteios. Handicap 1º tempo` · `Escanteios. Total 2º tempo` | Escanteios |
| `<jogador>. Ressaltos` · `<jogador> Total de pontos` · `<jogador>. Total de assistências` | Player Props |

> O sufixo (`Com prorrogação`, `1º tempo`, `Set 1`) é **recorte**, não mercado novo. Totais de
> jogo e de time (`Total`, `Total de <time>`) e os de F1 (`Top 3`, `Top 10`) seguem o global sem
> tradução fina aqui.

---

## 10. Stake

Campo `amount`, número, **em USDT**. A conversão para R$ é do `/salvar`, pela moeda da conta.

---

## 11. Odds

- **W:** `retorno ÷ stake`, conciliado com o `payoutCoefficient`. Na perna anulada isso dá 3,75
  (`b4836669`), não os 12,56 do `coefficient`.
- **L e aberta:** o `coefficient`, que é a odd do card. Nunca o `payoutCoefficient` (zero).
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `cashout/tickets/<uuid>` — oferta de cashout (§7).
- `public/api/profile` · `profile-balance` — saldo e perfil.
- Toda a família `dexsport.io/api/v1|v2|v3/…` do site (bônus, avatares, notificações,
  `txs_list` do §2.2).
- `nickname`, `number`, `cashoutDelay`.

---

## 13. Pegadinhas (resumo rápido)

1. **Duas listas: use a do SDK, nunca o `txs_list`** (§2.2).
2. **Perna anulada: `coefficient` ≠ `payoutCoefficient`** — no W manda o dinheiro (§11).
3. **`payout` 0 na aberta** — só `result` 2 é derrota (§5).
4. **`eventDate` em UTC** (§4).
5. **Esporte é um id** (`football`), não um nome (§1.2).
6. **Moeda `usdt` minúscula, conta em USDT** (§1.1).
7. **Barra dupla no caminho** (`//api/…`) — é da casa (§2.1).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada em USDT **antes** da 1ª captura.
- [ ] Nenhum `W` com odd 12,56 no `b4836669` (deve ser 3,75).
- [ ] Nenhuma aberta liquidada; nenhuma perdida com odd zero.
- [ ] Coluna Data = evento em São Paulo.
- [ ] Contagem capturada == `totalRows` de `placed` + `finished`.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 03/10/2026 — conta inteira (**41 bilhetes**): `extensor/harness/fixtures/dexsport.tickets.json`.

| ID (início) | Tipo | Status | Stake | Odd | Colocação (SP) | Evento (SP) | Retorno | Fonte |
|---|---|---|---|---|---|---|---|---|
| 3345134c | 2 pernas | WIN | 25,00 | 5,03 | 01/10 15:16 | 02/10 11:00 | **125,75** | card |
| b4836669 | 2 pernas, 1 anulada | WIN | 25,00 | 3,75 | 03/10 01:02 | 03/10 11:00 | **93,75** | card |
| b2e1c15c | Simples | WIN | 25,00 | 4,3 | 02/10 21:30 | 03/10 08:30 | 107,50 | json |
| 6836ecd1 | 2 pernas | LOST | 24,50 | 3,77 | 01/10 15:19 | 02/10 14:30 | 0 | card |
| c43f1040 | 3 pernas | LOST | 25,00 | 5,06 | 02/10 13:01 | 03/10 15:45 | 0 | card |
| 603158df | 2 pernas (1 não decidida) | LOST | 25,00 | 4,94 | 02/10 17:19 | 03/10 15:45 | 0 | json |
| bf7feb3c | 2 pernas | ABERTA | 25,00 | 6,86 | 03/10 14:57 | 04/10 11:30 | (171,50 pot.) | card |

**Sem amostra:** devolvida · cancelada · cashout executado · boost · bônus · meio ganho/perdido.

---

## Feedback para a camada global / MODELO

1. **Primeira casa com duas APIs de histórico**, uma delas carregando credencial no corpo. O
   recon tem de comparar as fontes antes de escolher, não pegar a primeira que aparece.
2. **Odd da colocação × odd liquidada** em campos separados é o desenho mais honesto que uma
   casa já entregou; a perna anulada só se lê certo por causa disso.
3. **O recon de 02/10 tinha o endpoint certo** (`history/tickets`); o de 03/10 primeiro achou o
   `txs_list` do perfil. Os dois existem: o caminho para o certo é Esportes → Minhas apostas.
