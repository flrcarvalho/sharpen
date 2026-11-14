# CASA_COPAWIN
## Camada de tradução — CopaWin → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da CopaWin.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `CopaWin` · site: `wncopa.com` · apostas em **Minhas Apostas** (`/my-bets`,
  filtros Todas · Ativas · Ganhas · Perdidas · Cash Out).
- Locale: pt-BR. Mercado, seleção e esporte vêm em **português** (`Chance Dupla`,
  `Nautico ou Empate`, `futebol`, `basquete`); times verbatim.
- Moeda: **real**. A API não manda campo de moeda; a casa só opera em R$ (card e carteira).
- **Dinheiro e odd em TEXTO com ponto decimal** (`"750.00"`, `"1.73"`).
- Plataforma **PRÓPRIA**: JS da casa (`/js/app.js`, `ticket.js`, `betslip.js`), API `/api/*`
  no mesmo domínio. Não é Altenar, Kambi, BetBy, BetConstruct nem softlabs. Família `cw`
  (inject `cw_inject.js`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s451):** `CopaWin`, a da base. Medido em 12/11/2026: 303 bilhetes (Jaao26 por
> print, sohprops e gregozxrd pelo bot), 1 conta, 1 `casas_meta`, 199 `correcoes`, 13
> `uso_tokens`, uma grafia só.
>
> **Domínio:** os mapas de favicon apontavam `copawnbr.com`; o recon mediu a casa em
> `wncopa.com` e os três mapas passaram a ele.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API, busca ativa** (SharpenUp · `extensor/cw_inject.js`).

```
GET https://wncopa.com/api/bet/my-bets[?status=<filtro>][&page=N]     (só o cookie)
→ { "success": true, "bets": [ … ], "pagination": { "current_page", "total_pages", "total" } }
```

Medido com a conta do Jaao26 (12/11/2026):

- **Só o cookie da sessão basta**: `fetch` cru, sem header, devolve 200. Não há token.
- **A 1ª página vem RENDERIZADA NO HTML.** Abrir `/my-bets` não dispara chamada de lista;
  só o "carregar mais" chama a API. Hook passivo entregaria zero: o inject pede as páginas
  ele mesmo, **sem `status`** (= Todas: abertas e liquidadas), até `total_pages`.
- **Página além do fim devolve a PÁGINA 1** (`page=2` com `total_pages: 1` respondeu
  `current_page: 1` e os mesmos bilhetes). O fim é `total_pages`, e página que volta com
  `current_page` diferente da pedida também encerra. Lista vazia nunca chega.
- Tamanho da página **≥ 15** (a conta tinha 15 e veio tudo numa página); `per_page`/`limit`
  são ignorados.
- Detalhe `GET /api/bet/{id}` existe e não é usado: a lista já traz as pernas.
- A CSP da página bloqueia `connect-src` para fora (inclusive 127.0.0.1): no recon pelo
  Chrome, o JSON sai lido em fatias, não por receptor local.

### 2.3 Layout do bilhete (card)

Card com rótulo (ANULADA/GANHA/PERDIDA), data-hora de colocação, tipo, mercado, seleção,
jogo, recado da casa e, no rodapé, **APOSTA** e **RETORNO**. ⚠️ O "RETORNO" do card é o
**potencial** até na perdida (Náutico 660703: R$ 2.247,00, perdeu). Texto por DOM não serve:
a IA leria derrota como ganho.

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na CopaWin |
|---|---|
| `id` | numérico de 6 dígitos (`660753`), o `data-bet-id` do card → `[Código:]` |
| `status` | `won` · `lost` · `void` na amostra do recon; `cashout` medido na s454 (3 reais); a tela também conhece `pending`/`active` (Ativa) |
| `type` | `single` em toda a amostra; a tela conhece `multiple` |
| `stake` | texto, R$ |
| `total_odds` | odd do bilhete, **cheia em todo status** (inclusive perdida) |
| `potential_return` | stake × odd, o "RETORNO" do card. **Nunca entra** |
| `actual_return` | o dinheiro que voltou: 0 na perdida, a stake na anulada |
| `cashout_*` | `cashout_used` 0 e `cashout_value` "0.00" fora do cashout; no cashout, `cashout_used` 1 e `cashout_value` = `actual_return` (§7) |
| `created_at` / `updated_at` | **horário de Brasília** (o card mostra o `created_at` verbatim) |
| `items[]` | pernas: `sport`, `match_name`, `market_name`, `selection_name`, `odds`, `result`, `event_starts_at`, `last_event_at`, `boost_pct` |
| `items[].event_starts_at` | **UTC** (prova: em 6 bilhetes a liquidação vem ~1h ANTES do evento lido como Brasília) |
| `items[].result_note` · `player_note` · `live_description` | recado da casa ("LIQUIDAR MANUALMENTE…", "GANHANDO"). **Nunca é fonte** |
| `items[].leg_statuses` · `leg_descriptions` · `leg_matches` | só na **Odd Turbinada** (§6) |
| `has_void_leg` | `true` nas duas anuladas |

**Ficha (s451):** adaptador `app/adaptadores/cw.py`, gate `tests/test_adaptador_cw.py`. A
Ficha aceita simples `won`/`lost`/`void` cujo dinheiro fecha (§5) e recusa o resto, que vai à
IA pelo texto: aberta, múltipla, cashout sem as três provas da §7, boost e a Odd Turbinada (sem odd por seleção).

---

## 3. ID do bilhete

`id` do bilhete (`660730`). O `id` de cada item (7 dígitos, `3997750`) é da perna e nunca vai
para o marcador. Prefixo de tipo não é preciso: uma série só.

---

## 4. Data

- **Coluna Data = dia do EVENTO em Brasília** (`event_starts_at` UTC → São Paulo). Náutico x
  CRB `2026-11-08 00:30:00` é **07/11**.
- Odd Turbinada: o evento mais recente é `last_event_at` (o último jogo do pacote).
- O bloco também leva a colocação (`created_at`, já em Brasília).

---

## 5. Status e Resultado

| `status` · dinheiro (`actual_return`) | Leitura | Código |
|---|---|---|
| `pending` / `active` | Em aberto | *(vazio — não liquidar)* |
| `lost` · retorno 0 | Perdeu | `L` |
| `void` · retorno = stake | Devolvida | `V` |
| `won` · retorno = stake × `total_odds` (± 1 centavo) | Ganhou | `W` |
| `cashout` + `cashout_used` 1 + retorno = `cashout_value` ≠ stake | Cashout | `W`, odd = retorno ÷ stake (§7) |
| o mesmo, com retorno = stake | Cashout na stake | `V`, odd da casa |
| cashout sem as três provas, `lost` com dinheiro, `won` que não fecha, `void` sem devolver, status novo | sobe cru | *(a conferir)* |

Meia vitória/derrota **não têm status próprio**: a casa escreve "meia-vitória" na nota e
devolve `won`/`lost`. O retorno não fecha com stake × odd e o bilhete sobe a conferir (o gate
do retorno no servidor decide pelo número). Medido: `won` 5, `lost` 8, `void` 2. O bloco
sempre leva `Status (API): status … · type …`.

---

## 6. Boost / promoção

**Odd Turbinada** (652529): 4 seleções de 4 jogos vendidas como `type: "single"` com UM item
(`market_key: "combined"`, `market_name: "Odd Turbinada"`), seleções juntadas por `||`,
**sem odd por seleção** (`leg_odds: null`) e o resultado de cada uma em `leg_statuses`. A odd
é a do conjunto (`total_odds`). O bloco a escreve como
`Tipo: Odd Turbinada (combo da casa · 4 seleções · odd do conjunto, sem odd por seleção)`,
uma linha por seleção com o jogo e o resultado. A Ficha recusa (exige odd por perna).

`boost_pct` = `null` em toda a amostra: com número, a Ficha recusa até ser medido.

---

## 7. Cashout

**Medido na s454 (14/11/2026)**, 3 cashouts reais da conta do Feca, feitos em 13/11
(`extensor/harness/fixtures/copawin.cashout.json`, lidos na aba logada, SHA-256 conferido).
Stake 200, cashout 180 em cada:

| Campo | No cashout |
|---|---|
| `status` | `cashout` |
| `cashout_used` | `1` |
| `cashout_value` | `"180.00"` = `actual_return` |
| `cashout_datetime` | = `updated_at` (Brasília) |
| `cashout_odd` | a odd da colocação (`"9.000"`), **não** a do cashout |
| `items[].result` | o que o jogo deu DEPOIS: `pending` (2) e `won` (1, Caernarfon). **Não é fonte** |

**As três provas juntas** (`status cashout` + `cashout_used` + `actual_return = cashout_value`)
liquidam pela regra global: diferente da stake → `W` com odd = retorno ÷ stake
(`MASTER_RESULTADO §5.6`, 180 ÷ 200 = 0,9); igual à stake → `V` com a odd da casa
(`§5.1.2`). Faltando uma, sobe a conferir. O `cashout_odd` não é a odd do cashout e nunca
entra. Antes da 0.7.80 o bloco dizia "a conferir, não liquidar" e a IA gravava os 3 **abertos**.

---

## 8. Bônus

Nenhum campo de bônus ou freebet no bilhete. A roleta diária da casa não é aposta.

---

## 9. Mapa de mercados (CopaWin → `Aposta` global)

Mercados vistos na amostra (`Vencedor (sem empate)`, `Total de Gols — <time>`,
`Vencedor do 1º Tempo`, `Chance Dupla`, `Total de Pontos`, `Mais/Menos Escanteios`,
`Handicap Asiático`): a categoria sai do `MASTER_APOSTAS` pelo objeto medido, sem atalho aqui.
`market_key` (`List`, `Goals Over/Under`, `asianhandicap`…) é chave interna e não entra.

---

## 10. Stake

Campo `stake`, texto em R$.

---

## 11. Odds

- **A odd do bilhete é `total_odds`**, a da colocação; cheia na perdida e na anulada.
- **W:** `actual_return ÷ stake` conciliado com `total_odds` (na amostra, iguais).
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `player_note`, `live_description`, `result_note` (recado da casa).
- `tg_stuck_alerted_at`, `match_ended_seen_at`, `audited`, `reconciled`, `live_settled`,
  `current_odds`, `market_key`, `selection` (`opt_…`, `under_1.5`), `event_id`, `match_id`.
- `user_id` (identidade; trocado por marcador na fixture).

---

## 13. Pegadinhas (resumo rápido)

1. **Card mostra o potencial como RETORNO até na perdida** (§2.3).
2. **Dois fusos**: colocação em Brasília, evento em UTC (§2.5, §4).
3. **Página além do fim volta a página 1** (§2.1).
4. **1ª página no HTML**: hook passivo não vê nada (§2.1).
5. **Odd Turbinada** = combo num item só, sem odd por seleção (§6).

---

## 14. Validações específicas

- [ ] Nenhuma perdida com o potencial como retorno; nenhuma aberta liquidada.
- [ ] Coluna Data = evento em São Paulo (Náutico 660703 → 07/11).
- [ ] Contagem capturada == total da casa (`pagination.total`).
- [x] **Cashout** (s454, `copawin.cashout.json`, §7).
- [ ] **1ª aberta / múltipla / meia vitória / boost:** salvar o JSON como fixture,
      trocar o clone do harness e liberar na Ficha.
- [ ] **Mais de uma página:** conferir que o inject parou em `total_pages` e não repetiu a 1ª.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 12/11/2026, conta inteira (**15 bilhetes**, todos liquidados, todos simples):
`extensor/harness/fixtures/copawin.my-bets.json`.

| Código | Mercado | Estado | Stake (R$) | Odd | Retorno (R$) | Colocação | Evento (SP) | Fonte |
|---|---|---|---|---|---|---|---|---|
| 660753 | Vencedor (sem empate) | `void` | 750,00 | 1,73 | 750,00 | 07/11/2026 14:44:34 | 07/11/2026 15:00 | card |
| 660730 | Total de Gols — GV San Jose | `won` | 825,00 | 2,20 | 1.815,00 | 07/11/2026 14:43:20 | 07/11/2026 16:00 | card |
| 660725 | Vencedor do 1º Tempo | `lost` | 975,00 | 2,62 | 0 | 07/11/2026 14:42:55 | 08/11/2026 02:00 | card |
| 660703 | Chance Dupla | `lost` | 525,00 | 4,28 | 0 (card: 2.247,00) | 07/11/2026 14:41:45 | 07/11/2026 21:30 | card |
| 660701 | Total de Pontos — Colorado | `won` | 1.875,00 | 3,15 | 5.906,25 | 07/11/2026 14:41:32 | 07/11/2026 17:30 | JSON |
| 652529 | Odd Turbinada (4 jogos) | `lost` | 15,00 | 2,64 | 0 | 07/11/2026 08:10:02 | 07/11/2026 17:05 | card |

Cashout (s454, 14/11/2026, conta do Feca): **718108, 718109, 718110**, stake 200, cashout 180 → `W` @ 0,9, em
`extensor/harness/fixtures/copawin.cashout.json`.

**Sem amostra:** aberta · múltipla · meia vitória/derrota · boost por `boost_pct`.

---

## 16. Roteiro da 1ª captura

1. Atualizar a extensão (**SharpenUp 0.7.77**) e dar **Ctrl+Shift+R** na aba da CopaWin
   **e** na aba do painel.
2. Abrir `wncopa.com` logado (a tela "Minhas Apostas" não é obrigatória: o inject busca a
   lista só com o cookie).
3. Conectar → Copiar bilhetes. O toast diz `respostas` e `vistos`; zero respostas = sessão
   caída.
4. Conferir no dashboard: contagem, código de 6 dígitos, data do evento e odd.
5. Na 1ª aberta/múltipla, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

1. **Paginação que não esvazia.** Primeira casa em que pedir além do fim devolve a página 1
   em vez de lista vazia. O freio "página vazia = acabou" dos outros injects aqui é laço.
2. **Card que estampa o potencial como retorno.** Ler a tela por texto ou print erra o
   resultado de toda perdida; vale para o prompt de visão também.
