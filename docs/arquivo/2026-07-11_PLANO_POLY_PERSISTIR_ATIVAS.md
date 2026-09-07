# Plano — Persistir posições ativas do Polymarket (frente A da sessão Poly)

> **Autossuficiente:** retome por este arquivo em qualquer chat novo. Contexto, decisões e
> passos exatos estão aqui. Criado em 2026-07-11 ao fim de uma sessão longa, para executar
> com contexto folgado.

## Objetivo (decisão do Feca)
As apostas do Polymarket devem **vir todas juntas** na tabela **Apostas**. As posições **ativas**
aparecem como **aposta aberta** (tem `stake`, tem `odd`, **sem resultado → sem P/L**) até liquidarem.
A seção separada **"Posições Ativas"** deixa de existir. Os 3 KPIs de saldo (Saldo em Aberto /
Disponível / Total) **permanecem** — são da carteira.

## Estado atual (rastreado no código, 2026-07-11)
- `/polymarket/sync` (`main.py:1455`) chama `coletar_bilhetes` → **só posições RESOLVIDAS** (W/L/V) viram bilhete.
- As **ativas NÃO são persistidas**: vivem só no dashboard ao vivo (`coletar_dashboard`, `polymarket.py:616`) e na seção "Posições Ativas" do front.
- Das ativas, hoje só o **tipster** é guardado, na tabela à parte `polymarket_ativos_tipster` (carrega pro bilhete quando resolve; `sync` faz `get_ativos_tipster` → merge → `limpar_ativos_tipster`).
- O **"N aguardando resultado"** de uma conta Polymarket é só um **badge de contagem**, vindo de `polyAtivasLive[nome]` (= `d.count` do dashboard), via `abertasDe()` (`index.html:1732`). **Não** são linhas na grade.
- Dedup: `upsert_bilhetes` / `_assinatura` (`repository.py`) por **código** quando presente. O código do Poly é `conditionId` (compra única) ou `conditionId__i` (split de compra múltipla) — **estável** entre syncs → serve para a transição aberta→resolvida.

## Decisões travadas
1. **Odd** = `1/preço` (retorno/investimento), uma só pra tudo. **Já implementado** (`_calc_odd`, commit `1d95972`).
2. **Aberta** = `resultado` vazio + `extraction_state='aberta'`; **sem P/L** (P/L é derivado só p/ resolvidas).
3. **Data + câmbio da aberta** = **data da COMPRA** (buy timestamp) e PTAX **daquele dia** (igual às resolvidas). Usar `_cotacao_para` com o ISO da compra.
4. Remover a seção "Posições Ativas" do front; manter os 3 KPIs de saldo.

## Passos de implementação
### 1. `polymarket.py` — emitir ativas como bilhete aberto
- Hoje `coletar_bilhetes` filtra `fechados` (resolvidas). Adicionar a coleta das **ativas** (as que `coletar_dashboard` monta em `ativas_raw`) e emiti-las no MESMO formato de linha de `coletar_bilhetes`, com:
  - `data` = data da compra (ver abaixo), `esporte`/`aposta`/`descricao` = mesma detecção, `casa='Polymarket'`, `parceiro`.
  - `stake` = `stake_usd × cotacao(data_compra)` (BRL), `stake_usd` = valor original.
  - `odd` = `_fmt_odd(_calc_odd(pos))` (= 1/preço).
  - `resultado` = `""` (aberto). `codigo_bilhete` = `_splitId`/`conditionId`.
  - `extraction_state` = `"aberta"` (verificar como o upsert/coletar seta isso hoje; resolvidas entram como `resolvida`).
- **Data da compra da ativa:** o `_split_multibuys` já guarda `_buyTimestamp` nos splits; para compra única, pegar o timestamp da 1ª BUY da `activity` daquele `conditionId` (construir um `buy_cache: cid → menor timestamp de BUY`). Converter p/ ISO BRT.
- Decidir a forma: (a) uma função nova `coletar_ativas(wallet, parceiro)` que espelha `coletar_bilhetes` para ativas, ou (b) um parâmetro em `coletar_bilhetes` para incluir ativas. Preferir (a) para não tocar no caminho já testado das resolvidas.

### 2. `main.py` `/polymarket/sync` — persistir ativas junto
- Coletar resolvidas (como hoje) **+** ativas; concatenar e `upsert_bilhetes(rows, dono, origem="sync")`.
- O carry-over de tipster via `polymarket_ativos_tipster` pode ser **simplificado/aposentado** depois (o tipster passa a viver no próprio bilhete aberto) — mas na 1ª versão, manter compatível para não perder tipsters já atribuídos.
- **Transição:** uma ativa que resolveu deixa de vir em "ativas" e passa a vir em "resolvidas" com o MESMO `codigo` → `upsert` **atualiza** a linha (resultado + `extraction_state` 'aberta'→'resolvida'). **Verificar** que `upsert_bilhetes` atualiza o `extraction_state` e o `resultado` no UPSERT por código (pode precisar ajuste).

### 3. Borda de compras múltiplas (o alerta do código)
- Splits usam `conditionId__i`. Se entre syncs o nº de splits mudar (nova compra na mesma posição antes de resolver), os códigos `__i` podem remapear. **Testar**: uma posição multi-buy que ganha 1 compra a mais entre syncs não deve duplicar nem órfãos deixar. Estratégia segura: código do split determinístico pelo **timestamp da compra** (`conditionId__<buyTs>`) em vez do índice `__i`, para ser estável mesmo com novas compras. **Avaliar essa troca** (afeta também as resolvidas — cuidado com dado já salvo).

### 4. Front (`index.html`) — remover a seção "Posições Ativas"
- Remover o bloco `#polymarket-dashboard` da parte da **tabela** de ativas (`pm-ativas`, `renderPolymarket…`, `pm-ativas-status`) — manter os 3 KPIs de saldo (`pm-k-portfolio`→Saldo em Aberto, `pm-k-cash`→Disponível, `pm-k-total`→Total) e o `pm-k-count`.
- Como as ativas viram bilhete aberto real, o `abertas` por parceiro passa a vir do backend (`por_parceiro.abertas`) naturalmente → **remover o special-case** `polyAtivasLive`/`abertasDe` para Polymarket (`index.html:1732`, `2767`).
- As abertas aparecem na grade com badge âmbar "aguardando resultado" (já existe: `.s-result`, `abertasDe`).

### 5. Testes + dry-run (OBRIGATÓRIO antes de tocar dado real)
- Testes: emissão de ativa (formato correto, resultado vazio, odd=1/preço, stake BRL pela data da compra); transição aberta→resolvida via upsert (mesmo código atualiza, não duplica); borda multi-buy.
- **Dry-run** contra a carteira real (`polymarket.py __main__` já roda dry-run das resolvidas) — estender para listar as ativas que seriam persistidas e conferir contagem vs. o dashboard (deve bater com os "10 ATIVAS").
- Só então rodar o sync real. Backup antes: `Planilhador/Backups/poly-persistir-ativas_<data>/`.

## Verificação final
`pytest` verde · `audit_casas` · `check-tokens` · dry-run confere contagem de ativas · sync real com 1 carteira e conferir na grade que as abertas aparecem e que uma que resolveu **virou** resolvida (não duplicou).

## Já feito nesta sessão (não refazer)
- ✅ Confiabilidade de saldo (RPCs → None quando caem, não R$0) — `b6b0a41`.
- ✅ Odd única = 1/preço + KPIs renomeados (Saldo em Aberto/Disponível/Total) — `1d95972`.

VERSÃO: 2026-07-11 · frente A da sessão Polymarket
