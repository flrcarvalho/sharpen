"""
semear_ptax.py — grava o PTAX (USD, EUR, AUD) na tabela `cotacao_ptax` (s458).

POR QUE EXISTE: desde 17/11/2026 o firewall do BCB recusa o IP de saída da Railway
(`200 text/html` "Request Rejected", em `olinda` e em `api.bcb.gov.br`). Sem cotação, o
`/salvar` recusa toda linha de conta em USD/EUR/AUD. O servidor, quando o BCB recusa, lê o
PTAX gravado no Postgres; este script roda de uma máquina que ALCANÇA o BCB e grava lá.

MESMO NÚMERO: a carga usa as funções do próprio servidor (`polymarket._carregar_periodo` e
`cambio._carregar_ptax_moeda`), com as mesmas escolhas (venda; no EUR/AUD o boletim de
Fechamento; o 1º registro do dia), e elas mesmas gravam pelo `_ptax_banco_gravar`. Dia já
gravado não é tocado (`ON CONFLICT DO NOTHING`): cotação de dia passado não muda.

Escreve só na `cotacao_ptax` (tabela nova, só lida pelo câmbio). Nada em `bilhetes`.

Uso (DATABASE_URL = a URL pública do Postgres):
    python scripts/semear_ptax.py              # desde 01/01/2023 até hoje
    python scripts/semear_ptax.py 2026-10-01   # desde a data
"""
from __future__ import annotations

import asyncio
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "app"))

import httpx  # noqa: E402

import cambio as C  # noqa: E402
import polymarket as P  # noqa: E402


async def main(de_iso: str) -> None:
    if not os.environ.get("DATABASE_URL"):
        sys.exit("DATABASE_URL ausente")
    hoje = P._hoje_iso()
    async with httpx.AsyncClient(timeout=60.0) as client:
        await P._carregar_periodo(client, de_iso, hoje)
        for moeda in C._PTAX_MOEDAS:
            await C._carregar_ptax_moeda(client, moeda, de_iso)
    from database import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        for r in await conn.fetch(
                "SELECT moeda, count(*) n, min(data) de, max(data) ate FROM cotacao_ptax "
                "GROUP BY moeda ORDER BY moeda"):
            print(f"{r['moeda']}: {r['n']} dias gravados, {r['de']} a {r['ate']}")
        for moeda in ("USD", *C._PTAX_MOEDAS):
            v = await conn.fetchval("SELECT venda FROM cotacao_ptax WHERE moeda = $1 "
                                    "ORDER BY data DESC LIMIT 1", moeda)
            print(f"  última {moeda}: {v}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"))
