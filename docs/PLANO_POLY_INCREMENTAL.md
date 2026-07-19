# PLANO — Sync incremental da Polymarket (marca d'água)

> Objetivo: parar de re-escanear o histórico **imutável** a cada sync. Hoje o sync é
> O(histórico inteiro); a meta é O(novidades + posições ativas).
> **Status:** desenho pronto, ancorado em sondagem REAL da API. **Execução aguarda validação
> na carteira do Feca** (é caminho de dinheiro — não subir sem paridade antes/depois).
> Criado na sessão 158 (19/07/2026). Pré-requisitos já no ar: teto de paginação (`771aea3`),
> auto-sync com throttle (`efbd55f`), **fetch consolidado 1×** (`c749056`).

---

## 1. Por que o sync é lento (medido, não achismo)

Sondagem read-only do proxy (`polymarket-proxy...workers.dev`) numa carteira real:

| Endpoint | Comportamento observado |
|---|---|
| `/positions` | **172 posições no total; 165 são resolvidas-resgatadas** (`redeemable:true`, `currentValue≈0`) e **7 ativas**. As resolvidas **PERMANECEM na lista pra sempre** → o `/positions` **cresce sem parar**. |
| `/activity` | Log **append-only**, ordem **DESC (mais novo → mais velho)**, cada item tem **`timestamp`** e **`transactionHash`**. É o maior gerador (cada trade/redeem = 1 linha) e **cresce ilimitadamente**. |

**Diagnóstico:** todo sync re-baixa e re-deriva as **165 resolvidas imutáveis** (que já estão no
Postgres) + re-baixa **todo** o `/activity`. Em 2 anos isso vira minutos. As resolvidas nunca
mudam — re-processá-las é desperdício puro.

---

## 2. Desenho proposto

**Marca d'água** = maior `timestamp` de `/activity` processado no último sync, guardada por
carteira (tabela `polymarket_sync_state(dono, wallet, watermark_ts, atualizado_em)` ou similar).

**No sync incremental:**
1. **`/activity`** — paginar (DESC) e **parar cedo** assim que bater `timestamp ≤ watermark`
   (já vimos tudo mais velho). → busca só a atividade **nova**. **É o maior ganho** (o `/activity`
   é o grower ilimitado).
2. **`/positions`** — ainda buscar completo (a API **não** filtra por "mudou desde X"), MAS
   **pular a derivação** das posições cujo `codigo_bilhete` já está salvo como **resolvido** no
   Postgres (imutável). Deriva só as **7 ativas** + qualquer **nova resolução**.
3. **Upsert** — inalterado (idempotente/dedup por código). O incremental só muda o que se
   **busca/deriva**, nunca a gravação.

**Auto-cura:** manter um **full-scan** de fallback — periódico (ex.: a cada N syncs ou 1×/dia) e
sob demanda (botão "ressincronizar tudo"). Se o incremental algum dia perder algo, o full-scan
reconcilia. Assim o pior caso é **atraso**, nunca **corrupção**.

---

## 3. ⚠️ Risco de corretude (o motivo de validar ao vivo)

`_split_multibuys(positions, activity)` divide uma posição com **múltiplas compras** em splits
`conditionId__i`, e a estabilidade do índice `__i` depende de ver o **histórico de compras
COMPLETO** da posição (ordenado por timestamp). Se a marca d'água cortar o `/activity` no **meio
das compras** de uma posição ainda ativa, o cálculo do split pode **mudar o código** → o
`upsert` não casa a linha antiga → **duplica** (o mesmo bug estrutural de dedup já conhecido).

**Mitigações a validar:**
- Buscar `/activity` incremental **só para detectar novidades/resoluções**, mas, para as posições
  **ativas** (poucas — 7 na amostra), buscar/garantir o **histórico completo de compras** delas
  (ex.: `/activity` filtrado por `conditionId`, se o proxy suportar — **investigar**).
- Ou: nunca aplicar split incremental a uma posição ativa com compras que cruzem a marca; cair no
  full-scan para essas.
- **Teste de paridade obrigatório:** rodar incremental e full-scan na MESMA carteira e exigir
  **saída idêntica** (mesmos códigos, stakes, odds, resultados) antes de confiar em produção.

---

## 4. Plano de execução (quando o Feca puder validar)

1. **Investigar** se o proxy/`/activity` aceita filtro por `conditionId` e/ou `start`/`end` de
   tempo (o `?start=1` respondeu 200 mas não filtrou na sondagem — confirmar semântica).
2. Criar a tabela/estado de marca d'água.
3. Implementar `coletar_tudo_incremental(wallet, parceiro, watermark)` **ao lado** de
   `coletar_tudo` (não substituir): early-stop no `/activity`, skip de resolvidos já salvos.
4. **Test harness de paridade** (cliente-fake) + **validação ao vivo na carteira do Feca**:
   incremental == full-scan, byte a byte nas linhas.
5. Ligar por trás de um gate; full-scan de fallback periódico + botão manual.
6. Medir o ganho real (tempo de sync antes/depois) e registrar.

---

## 5. O que já está feito (reduziu a dor sem tocar na corretude)

- **Fetch consolidado** (`c749056`): `/positions`+`/activity` buscados **1×** (era 2×) → ~2× mais rápido, saída provada idêntica por teste de paridade.
- **Auto-sync com throttle** (`efbd55f`): não precisa mais clicar; sincroniza ao entrar/voltar, 5 min, pausa se aba oculta.
- **Teto de paginação** (`771aea3`): proxy preso não trava mais o sync.

> Ver [[polymarket_sessao_2026]] · [[pl_calculo_derivado]] · `docs/AUDITORIA_TURBO_2026-07-19.md`.
