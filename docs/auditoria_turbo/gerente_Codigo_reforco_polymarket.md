# Reforço — Polymarket / Captura / Planilha Viva (2ª passada)

Escopo: `app/polymarket.py` (865), `app/captura.py` (211), `app/planilha_viva.py` (88).

## Achados

**[ALTA] Odd de entrada gravada, mas consumida como odd realizada no P/L** — `polymarket.py:529-536` (`_calc_odd`) + `casas/CASA_POLYMARKET.md §11`
A odd de toda linha (inclusive `W`) é `1 / preço médio de compra` (ENTRADA). O P/L do dashboard deriva de `stake × odd`; como a odd é de entrada e não realizada, para um `W` o retorno reconstruído ignora taxa/slippage on-chain que o `cashPnl` real carrega → **P/L agregado da Polymarket superestima as vitórias**. Para `L` fica correto (−stake). A `CASA_POLYMARKET §11` afirma o oposto ("W: odd = (stake + cashPnl) ÷ stake") — contradição doc↔código. É a dívida conhecida entry vs realized (#32).
→ Decidir semântica única: (a) manter odd de entrada e **corrigir §11**; ou (b) persistir P/L realizado (`cashPnl` em BRL) separado para os agregados. Esforço: baixo (doc) / médio (P/L separado).

**[MÉDIA] Paginação sem teto → loop infinito com proxy defeituoso** — `polymarket.py:97-111` (`_paginate`)
Só termina em página vazia ou `len(page) < page_size`. Proxy devolvendo sempre página cheia (cache preso) → `offset` cresce pra sempre, coleta nunca retorna. Trocou truncamento silencioso (fix #4) por travamento silencioso. → Guarda de sanidade (teto alto de páginas/itens, aborta com exceção controlada). Esforço: baixo.

**[MÉDIA] `_portfolio` engole exceção e devolve 0.0** — `polymarket.py:714-726`
Falha de rede/JSON em `/value` → `except Exception: pass → return 0.0`. Mitigado pelo chamador, mas se a API de posições também degradar, portfólio vira R$0 silencioso (o "total" mente). → Alinhar ao `_rpc_balance`: retornar `None` e propagar "—" na UI. Esforço: baixo.

**[BAIXA] `cash` subestima quando um token responde e o outro cai** — `polymarket.py:762-767`
`saldo_ok=True` se qualquer RPC responder; token indisponível vira 0 → saldo exibido como certo omitindo o desconhecido (USDC.e legado, impacto pequeno). → `saldo_ok` só com ambos os tokens. Esforço: baixo.

**[BAIXA] Sessão expirada ainda aceita capturas** — `captura.py:107-111,172-197`
`_prune` só roda em criar/conectar; `sessao_por_token`/`adicionar_captura` não checam TTL. Sessão inativa >6h continua válida por token. → Validar TTL no caminho de envio. Esforço: baixo.

**[BAIXA] Cache da planilha viva sem lock + mutação in-place do objeto cacheado** — `planilha_viva.py:74-79`
Mesma lista mutada é guardada e devolvida; hoje idempotente, frágil se o carimbo virar por-requisição. → Cópia defensiva ou documentar idempotência. Esforço: baixo.

**[BAIXA] `r.json()` sem tratamento** — `polymarket.py:87-94` · 200 não-JSON (HTML de erro do Worker) sobe cru. → Envolver em `PolymarketRespostaInesperada`. Esforço: baixo.

**[BAIXA] Data por slug pega última ocorrência** — `polymarket.py:217-222` (`_data_iso`) · slug com 2 datas (janela de torneio) pega a errada (fallback). → Comentar heurística/validar contra `endDate`. Esforço: baixo.

## Positivos
1. **Guarda de câmbio (`CambioIndisponivel`)** — recusa gravar USD como BRL sem PTAX do dia da aposta antiga (falha em vez de mentir). Integridade exemplar.
2. **`None` vs `0.0` no saldo on-chain (fix #47)** — só `None` quando todos os 6 RPCs falham → UI mostra "—", não "carteira vazia".
3. **Falha alto em vez de truncar** — `PolymarketRespostaInesperada`, retry/backoff, pareamento com código curto + `compare_digest`, stale-serve na planilha viva.
