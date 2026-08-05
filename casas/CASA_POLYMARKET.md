# CASA_POLYMARKET — Tradução da casa para a língua global

> Casa **atípica**: a porta de entrada **não é screenshot + IA**, e sim a **API
> da carteira** (on-chain Polygon, via Worker Cloudflare). A extração é
> determinística, feita por `app/polymarket.py` — não passa pelo modelo de visão.
> Este arquivo documenta a tradução; o cálculo continua sendo global.

---

## 1. Identidade

- **Nome de exibição:** Polymarket
- **Chave:** `POLYMARKET`
- **Natureza:** mercado de predição (prediction market), apostas em USDC on-chain.
- **Moeda nativa:** USD/USDC → convertida para **BRL** na ingestão (PTAX/BCB do dia).
- **Parceiro:** a carteira pertence ao próprio usuário; o parceiro é escolhido na
  sidebar (ex.: `Feca [Eu]`), igual às demais casas.

---

## 2. Modo de ingestão e layout

- **Fonte:** API da carteira via Worker Cloudflare `polymarket-proxy.flrcarvalho.workers.dev`
  (a peça que destrava a API no Brasil; reusada intacta do app Polymarket standalone).
- **Endpoints:** `/positions` (posições) e `/activity` (compras/resgates), ambos
  paginados **sem teto** até a página vir vazia → histórico desde a 1ª aposta.
  Tamanho de página **por endpoint** (espelha o app standalone): `/positions` pede
  `limit=100` (a API limita a página deste endpoint — pedir mais faria a parada
  `len < limit` truncar o histórico em silêncio); `/activity` pede `limit=500`.
- **Cotação USD→BRL:** `olinda.bcb.gov.br` (PTAX, `cotacaoVenda`), pela data da
  aposta, recuando até **10 dias** para atravessar fim de semana/feriado. Cai para a
  cotação de hoje **só** se a aposta tiver ≤ 7 dias; aposta antiga sem PTAX na janela
  aborta o sync (`CambioIndisponivel`) em vez de gravar histórico com câmbio errado.
  A faixa inteira vem em **uma** chamada (`CotacaoDolarPeriodo`) e fica num mapa de
  módulo — nunca uma chamada por data (s247; ver `CLAUDE.md`, "API externa por item").
- **Sem upload:** o painel da casa troca o drag-and-drop por **carteira + Sincronizar**.

---

## 3. Código do bilhete e deduplicação

- **Código** (11ª coluna interna) = `conditionId` da posição. Compras múltiplas no
  mesmo mercado viram entradas individuais com sufixo `__i` (`conditionId__0`, `__1`…).
- O índice `__i` é numerado sobre **todas as compras do `conditionId`** em ordem
  cronológica — não sobre as compras de um lado. Isso mantém o código estável quando a
  carteira compra os **dois lados** do mesmo mercado (cada lado é aposta própria e os
  dois precisam de códigos diferentes, senão colidem na dedup).
- A dedup global por ID (`repository._assinatura`) usa esse Código → **reprocessar a
  mesma carteira é UPSERT limpo**, sem duplicar. Sincronizar de novo só atualiza.

> ⚠️ **O código depende de QUANTAS compras o mercado tem.** Com 1 compra é `cid` cru;
> quando entra a 2ª, o coletor passa a emitir `cid__0`/`cid__1` e a linha antiga **nunca
> mais é alcançada por um UPSERT** — vira fantasma, congelada no estado em que estava
> (tipicamente "aberta", esperando um resultado que jamais chega) e contando como aposta
> a mais. O `/polymarket/sync` fecha isso: herda o tipster da linha crua e a remove
> **depois** do upsert, via `remover_bilhetes_supersedidos`, que só apaga se as fatias
> irmãs já existirem na mesma conta.

---

## 4. Ordem das linhas

- Inserção da **mais antiga → mais nova** (ordenado por timestamp da compra), para
  que a ordem cronológica da grade (por `criado_em`) bata com a realidade.

---

## 5. Resultado (W / L / V / HW / HL)

Tudo sai de **quanto cada cota pagou na liquidação** (`payout`), não de um P/L
agregado. Um mercado da Polymarket liquida a cota em exatamente três valores:

| `payout` | significado |
|---|---|
| **1,0** | o lado acertou |
| **0,0** | o lado errou |
| **0,5** | mercado **ANULADO** — evento cancelado/indefinido, devolve metade aos dois lados |

Com o `payout` na mão, o resultado é a régua global de cashout
(`MASTER_RESULTADO §5.1.2` e `§5.6`) aplicada ao **retorno real** da linha:

- **L** — retorno zero.
- **V** — retorno igual ao stake (P/L zero) → anulada, não perda.
- **W** — retorno diferente do stake, com **odd = retorno ÷ stake**. Na vitória cheia
  isso é exatamente `1/preço` (a odd de entrada), então o histórico não muda; no
  mercado anulado é `0,5 ÷ preço`, que pode dar **odd menor que 1** quando a cota foi
  comprada acima de 0,50 — é o previsto para cashout abaixo do stake.

**Como saber que liquidou:** `redeemable: true` **sozinho** já significa resolvido; o
preço só confirma que é de liquidação. Ler `currentValue < 0,01` como sinal de
resolução era o bug da sessão 195 — só vale para a DERROTA, então **anulada** e
**vitória ainda não resgatada** (que continuam valendo dinheiro) viravam bilhete
ABERTO para sempre.

**Posição que saiu da carteira** (o resgate esvazia a posição) é reconstruída da
`activity`, agrupando por **`conditionId` + `asset`** — nunca só por `conditionId`:
comprar os dois lados do mesmo mercado são **duas apostas independentes** (podem até
vir de tipsters diferentes) e uma ganha enquanto a outra perde.

> ⚠️ `outcomeIndex: 999` no `REDEEM` = índice **não informado**, e **não** é sinônimo
> de anulado: a Polymarket usa o mesmo marcador no resgate via adaptador de
> *negative-risk* (o `conditionId` sai com uma longa fila de zeros), onde a cota pagou
> $1 cheio. Quem desempata é o **valor pago**: metade das cotas → anulado; o total de
> um lado → aquele lado ganhou.

- **HW / HL** não se aplicam ao modelo binário da Polymarket (sem meia-aposta).
  Aguardam amostra caso algum mercado novo exija.

---

## 6. Boost / promoção

- Não há boost. O retorno é o resgate on-chain real (USDC recebido).

---

## 7. Cashout

- Venda antecipada (`SELL`) é tratada como cashout: **W** com `odd = valor da venda ÷
  stake`. Antes a venda era ignorada pelo módulo inteiro e a aposta **não gerava linha
  nenhuma** na planilha.
- Sobra de arredondamento na venda total (ex.: comprou 352,941175 e vendeu 352,94) é
  **pó**, não posição viva — o limiar é o mesmo `sizeThreshold` que faz a API parar de
  listar a posição.

---

## 8. Bônus

- Não se aplica. Todo stake é USDC próprio.

---

## 9. Mapa de mercados (apenas o confirmado)

> Camada fina: lista só o que a Polymarket confirma. As 27 categorias vivem no
> `MASTER_APOSTAS §3` — não reescrever aqui.

> **O `O/U` não decide categoria — o OBJETO contado decide** (`MASTER_APOSTAS §1`).
> A Polymarket escreve quase tudo como `O/U X`, então classificar pelo `over/under`
> jogava escanteio, gol, ponto e round todos em `Player Props`: eram **35 linhas**
> erradas na carteira de referência, e nenhuma era de jogador.

| Mercado no título Polymarket | Aposta global |
|---|---|
| Vencedor da partida / outcome simples | ML |
| `Will X win by KO or TKO?` (método de vitória, MMA) | ML |
| `Game Handicap` / `Map Handicap` / spread | Handicap |
| `Corners` / escanteios (Futebol) | Escanteios |
| `Goals` / gols / `O/U 2.5` de gols (Futebol) | Gols |
| `Cards` / cartões (Futebol) | Cartões |
| `Both teams to score` / BTTS (Futebol) | Ambas Marcam |
| `O/U 179.5` — total do jogo/time (Basquete) | Pontos |
| `O/U 1.5 Rounds` (MMA / Boxe) | Rounds |
| `O/U 8.5` — corridas (Baseball) | Corridas |
| `Strikeouts O/U` — estatística do arremessador | Player Props |
| `Games Total` (Tênis) | Games |
| `Sets` (Tênis) | Sets |
| `Legs` (Dardos) | Legs |
| `Total Kills` / `Map X Total Rounds` / `Games Total` (E-Sports) | E-Sports Props |
| Estatística individual de jogador, sem categoria própria | Player Props |

> Mercados sem sinal claro no título caem em `ML` e são ajustáveis na grade.

---

## 10. Estrutura de mercado (contínuo / discreto / race)

- Segue o global (`MASTER_DESCRICAO §10`). A Polymarket expõe o alvo no próprio
  título (ex.: `O/U 2.5`), preservado na Descrição.

---

## 11. Odd

- **Vírgula, nunca ponto; precisão preservada** (regra global, sessão 50).
- **W:** `odd = retorno ÷ stake = (stake + cashPnl) ÷ stake`.
- **L / posição sem lucro:** `odd = 1 ÷ preço de compra` (preço on-chain < 1).
- Sem arredondamento; a grade recebe a precisão cheia.

---

## 12. Descrição / Player Props

- **Descrição = título do mercado** como vem da API (en-US), com sufixo `[i/N]`
  quando a posição foi comprada em várias parcelas.
- Não há tachado/substituição de jogador (não é screenshot).

---

## 13. Pegadinhas

- `type:"TRADE"` + `side:"BUY"` na activity — tratar `type` **ou** `side`.
- `startDate`/`createdAt` **não existem** em `/positions`; a data vem do `REDEEM`
  (BRT) → `eventSlug` → `endDate`, nessa ordem.
- **Esporte detectado pelo prefixo do slug do evento** (`mlb-…`→Baseball,
  `atp-`/`wta-`→Tênis, `nba-`/`wnba-`→Basquete, `ucl-`/`fifwc-`→Futebol,
  `lol-`/`cs2-`/`val-`→E-Sports, `ufc-`→MMA, `nfl-`→Futebol Americano…). É o sinal
  **primário e confiável**; o regex do título é só fallback quando o slug falta ou
  tem prefixo desconhecido. Sem isso, mercados titulados por participante
  (`Yankees vs Red Sox`, `Sinner vs Ruud`, `O/U 1.5 Rounds`) caíam em `Outro`.
- E-Sports vem granular (CS2, LoL, Dota 2…) → **colapsa para `E-Sports`** no global;
  over/under de estatística de E-Sports vira `E-Sports Props` (nunca `Player Props`).
- **Snooker** não é esporte canônico → cai em `Outro` (candidato a cadastro futuro).
- A API ordena resolvidas/`redeemable` primeiro — por isso a paginação é obrigatória.

> **Exceção arquitetural consciente:** esta é a única casa que classifica
> **esporte e categoria em código** (`app/polymarket.py`, regex determinístico),
> e não pela IA guiada pelos masters. Os masters são markdown para a IA de visão —
> o coletor Python não os consulta. Logo, a Polymarket **não** herda as listas
> auxiliares do `MASTER_ESPORTES` (centenas de jogadores de Tênis/Dardos, armadilha
> LYON, desambiguação Tênis vs Padel) nem a prioridade semântica do `MASTER_APOSTAS`.
> A cobertura é deliberadamente um subconjunto: cauda longa sem prefixo de liga
> conhecido no slug nem sinal no título cai em `Outro`/`ML` e é ajustada na grade.
> Não esperar paridade com a IA aqui.

---

## 14. Validações

> **Transversais (todas as casas):** ver `MASTER_PIPELINE §8` + `MASTER_OUTPUT §17–§18`.**

- Específica: toda linha tem Código (`conditionId`/`__i`) — sem Código indica falha
  de coleta, não bilhete válido.
- Específica: `Stake` já convertido para BRL; nunca emitir valor em USD.

---

## 15. Exemplos golden

> Validado contra a carteira real `0x2b3c…9f22` (202 bilhetes resolvidos, 83 W / 119 L).

| Data | Esporte | Aposta | Descrição | Stake | Odd | Res | Código |
|---|---|---|---|---|---|---|---|
| 28/05/2026 | E-Sports | ML | LoL: Galions vs TLN Pirates (BO5) - LFL Playoffs | 409,19 | 5,2631… | L | 0x317b…83b0c |
| 16/06/2026 | E-Sports | Handicap | Game Handicap: TR (-1.5) vs Team Refuser (+1.5) [1/2] | 264,06 | 3,0303… | W | 0xf4a3…7da84__0 |
| 11/06/2026 | Tênis | Player Props | Games Total: O/U 2.5 | 617,73 | 2,2727… | L | 0x9986…3009b |
