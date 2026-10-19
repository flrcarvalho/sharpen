"""A linha de `correcoes` que a Ficha não deixou (s423, A3): DEX Sport 850e48f2 (id 383282).

A Ficha gravou a aposta ABERTA com odd 6,05 (`coefficient` do cru, os três crus de 14/10); a perna
DNB anulou, e a captura das 23:40 de 14/10 a liquidou W com 2,48 (payout 124 ÷ stake 50, a odd da
ganha). A mudança está certa; o UPSERT é que não deixava rastro (hoje deixa: `_rastro_ficha`).
Aqui só o registro, no instante da mudança (o `atualizado_em` daquela captura). A aposta não muda.
Idempotente: se a linha já existe, nada é gravado.

    python scripts/rastro_retroativo_383282_s423.py            # ensaio
    python scripts/rastro_retroativo_383282_s423.py --aplicar
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

from database import get_pool  # noqa: E402
from limpar_cru_filtro import _carregar_env  # noqa: E402

ID, CODIGO = 383282, "850e48f2-34ef-412b-80df-cd2ae6899b79"
ANTES, DEPOIS = "6,05", "2,48"
QUANDO = datetime(2026, 10, 14, 23, 41, 21, 965060, tzinfo=timezone.utc)


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        b = await conn.fetchrow("SELECT id, dono, casa, odd, resultado, origem, descricao "
                                "FROM bilhetes WHERE id = $1 AND codigo_bilhete = $2", ID, CODIGO)
        if not b or b["odd"] != DEPOIS or b["origem"] != "ficha":
            print(f"PARADO: a aposta não está como medida: {dict(b) if b else None}")
            return
        ja = await conn.fetchval("SELECT count(*) FROM correcoes WHERE bilhete_id = $1 AND "
                                 "campo = 'odd' AND origem = 'ficha'", ID)
        print(f"aposta {ID} ({b['dono']}, {b['casa']}): odd {b['odd']}, {b['resultado']} · "
              f"rastro de odd da Ficha já gravado: {ja}")
        if ja:
            print("nada a fazer.")
            return
        print(f"a gravar: odd {ANTES} → {DEPOIS}, origem 'ficha', em {QUANDO.isoformat()}")
        if not aplicar:
            print("ensaio: nada escrito. Rode com --aplicar.")
            return
        await conn.execute(
            "INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, valor_novo, "
            "descricao, criado_em, origem) VALUES ($1, $2, $3, 'odd', $4, $5, $6, $7, 'ficha')",
            ID, b["dono"], b["casa"], ANTES, DEPOIS, b["descricao"], QUANDO)
        print("gravado.")


if __name__ == "__main__":
    asyncio.run(main())
