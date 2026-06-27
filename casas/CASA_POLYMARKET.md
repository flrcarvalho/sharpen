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
  aposta, com fallback de até 4 dias (fim de semana/feriado) e, por fim, hoje.
- **Sem upload:** o painel da casa troca o drag-and-drop por **carteira + Sincronizar**.

---

## 3. Código do bilhete e deduplicação

- **Código** (11ª coluna interna) = `conditionId` da posição. Compras múltiplas no
  mesmo mercado viram entradas individuais com sufixo `__i` (`conditionId__0`, `__1`…).
- A dedup global por ID (`repository._assinatura`) usa esse Código → **reprocessar a
  mesma carteira é UPSERT limpo**, sem duplicar. Sincronizar de novo só atualiza.

---

## 4. Ordem das linhas

- Inserção da **mais antiga → mais nova** (ordenado por timestamp da compra), para
  que a ordem cronológica da grade (por `criado_em`) bata com a realidade.

---

## 5. Resultado (W / L / V / HW / HL)

- **W** quando `cashPnl > 0` (a posição pagou mais que o stake).
- **L** quando `cashPnl ≤ 0`.
- Vitórias **já resgatadas** somem de `/positions` e são reconstruídas a partir da
  `activity` (eventos `REDEEM`) — classificam corretamente como **W**.
- **V / HW / HL** não se aplicam ao modelo binário da Polymarket (sem cashout
  parcial nem meia-aposta). Aguardam amostra caso algum mercado novo exija.

---

## 6. Boost / promoção

- Não há boost. O retorno é o resgate on-chain real (USDC recebido).

---

## 7. Cashout

- Venda antecipada de posição (`SELL`) existe, mas é rara (1 caso na carteira de
  referência). **Não tratada** no MVP: o stake do split pode ficar superestimado.
  Aguarda amostra para política definitiva.

---

## 8. Bônus

- Não se aplica. Todo stake é USDC próprio.

---

## 9. Mapa de mercados (apenas o confirmado)

> Camada fina: lista só o que a Polymarket confirma. As 27 categorias vivem no
> `MASTER_APOSTAS §3` — não reescrever aqui.

| Mercado no título Polymarket | Aposta global |
|---|---|
| Vencedor da partida / outcome simples | ML |
| `Game Handicap` / `Map Handicap` / spread | Handicap |
| `Total: O/U X` / `over` / `under` | Player Props |
| `Games Total` (Tênis) | Games |
| `Sets` (Tênis) | Sets |
| `Legs` (Dardos) | Legs |
| `Both teams to score` / BTTS (Futebol) | Ambas Marcam |
| `Corners` / escanteios (Futebol) | Escanteios |
| `Cards` / cartões (Futebol) | Cartões |
| `Goals` / gols (Futebol) | Gols |

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
> A cobertura é deliberadamente um subconjunto: cauda longa sem liga/sinal no título
> cai em `Outro`/`ML` e é ajustada na grade. Não esperar paridade com a IA aqui.

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
