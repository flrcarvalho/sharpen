# HISTÓRICO — índice

> **Este arquivo é um índice.** O histórico em si vive em `docs/historico/`, partido por
> faixa de sessão. Antes da faxina de 2026-09-07 tudo isto era um único arquivo de
> **1,21 MB em 2.020 linhas**, sem índice — só consultável por `grep`.
>
> Estado atual do projeto → [`STATUS.md`](../STATUS.md) · o que está aberto →
> [`BACKLOG.md`](../BACKLOG.md) · regras → [`CLAUDE.md`](../CLAUDE.md).

---

## Partições

| Faixa | Arquivo | Tamanho | O que tem dentro |
|---|---|---|---|
| **Sessões 339 → 300** | [`historico/HISTORICO_s300-s327.md`](historico/HISTORICO_s300-s327.md) | 246 KB | Os blocos completos que saíram do `STATUS.md` (339 e 336 → 317), a Sessão 315 e a cadeia `_Anterior_` de 339 até 300. |
| **Sessões 299 → 243** | [`historico/HISTORICO_s243-s299.md`](historico/HISTORICO_s243-s299.md) | 304 KB | Cadeia `_Anterior_`. Inclui a entrada da Bolsa de Aposta (s299) e a da Jonbet (s249). |
| **Sessões 242 → 150** | [`historico/HISTORICO_s150-s242.md`](historico/HISTORICO_s150-s242.md) | 298 KB | Cadeia `_Anterior_`. Inclui a paginação da Betfair (s199) e a Polymarket (s200). |
| **Sessões 149 → 61** | [`historico/HISTORICO_s061-s149.md`](historico/HISTORICO_s061-s149.md) | 371 KB | Cadeia `_Anterior_`. Inclui a dedup da conta KingPanda (s100) e a moldura da marca (s99). |
| **Sessões 62 → 14 (log de “Estado atual”)** | [`historico/HISTORICO_s014-s062_estado.md`](historico/HISTORICO_s014-s062_estado.md) | 75 KB | **Log paralelo**, não a continuação da cadeia acima: é o antigo §4 “Estado atual” do STATUS, com a sua própria numeração. |
| **Sessões 43 → 24 (log de “Próxima sessão”)** | [`historico/HISTORICO_s024-s043_proximo.md`](historico/HISTORICO_s024-s043_proximo.md) | 34 KB | **Log paralelo**, não a continuação da cadeia acima: é o antigo §6 “Próxima sessão” do STATUS, com a sua própria numeração. |

---

## Como este histórico é organizado

Três formatos convivem aqui, e a diferença importa na hora de procurar:

1. **Bloco completo de sessão** (`## Sessão N — …`) — o texto integral, como foi escrito
   no `STATUS.md`. Só as sessões mais recentes têm isso; é o que o `/encerrar` move
   quando a janela deslizante do STATUS avança.
2. **Cadeia `_Anterior_`** — um parágrafo por sessão, que é o resumo que vivia no
   cabeçalho do `STATUS.md`. Cobre a maior parte da história.
3. **Logs paralelos** (`s62 → 14` e `s43 → 24`) — vieram do antigo §4 “Estado atual” e do
   antigo §6 “Próxima sessão”. **Não são a continuação da cadeia**: têm numeração
   própria e se sobrepõem no tempo com ela. Fundi-los inventaria uma ordem que não
   existe, então ficaram separados de propósito.

## Procurar aqui dentro

```bash
grep -rn "termo" docs/historico/
```

---

_Índice criado em 2026-09-07 (faxina de documentação, Lote C). Nenhuma linha do histórico
foi reescrita — o conteúdo foi partido por número de linha e conferido linha a linha._
