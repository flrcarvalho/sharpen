"""Semeia o dicionário de termos (`04_DICIONARIO §3`; s411) a partir dos pares que já existem.

Para cada aposta com cru (o mais recente dela em `captura_crua`), o adaptador monta a Ficha e o
termo da casa (`esporte_casa`, `mercado_casa`) é pareado com o esporte e a categoria que a IA
gravou para o MESMO código na MESMA conta (`bilhetes`). Onde o código não tem bilhete, completa
com a decisão mais recente da IA em `sombra_rotulos`. Entra no dicionário só o termo UNÂNIME
(`dicionario.votar`); o que a IA decidiu de mais de um jeito sai na lista para o Feca e fica de
fora, ou seja, vai para a IA.

Idempotente: refaz a semente inteira a cada rodada. O servidor roda a mesma semente
sozinho uma vez por dia (`dicionario.diario`, 04h de Brasília); este script é para rodar na hora. Linha `origem = 'feca'` nunca é tocada.
Semente que deixou de ser unânime é apagada (a aposta volta para a IA).

    python scripts/semear_dicionario.py              # ensaio, nada escrito
    python scripts/semear_dicionario.py --aplicar    # grava em dicionario_termos
"""
from __future__ import annotations

import asyncio
import collections
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import dicionario  # noqa: E402
from database import get_pool  # noqa: E402


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        p, texto, fontes = await dicionario.pares(conn)
        print("pares:", fontes)
        unanimes, contraditos = dicionario.votar(p, texto)
        por_casa = collections.Counter((c, t) for c, t, _ in unanimes)
        for (c, t), n in sorted(por_casa.items()):
            print(f"{c:11} {t:9} {n:4} termos unânimes")
        print(f"\n{len(contraditos)} termos em que a IA decidiu de mais de um jeito (ficam com a IA):")
        for (c, t, termo), cnt in sorted(contraditos.items()):
            if dicionario.SEP not in termo:
                print(f"  {c:11} {t:9} {termo!r}: " + ", ".join(f"{k} ×{v}" for k, v in cnt.most_common()))
        if not aplicar:
            print("\nensaio: nada gravado (use --aplicar)")
            return
        await dicionario.gravar_semente(conn, unanimes)
        total = await conn.fetchval("SELECT count(*) FROM dicionario_termos")
        print(f"\ngravado: {len(unanimes)} termos de semente; {total} no dicionário")


if __name__ == "__main__":
    asyncio.run(main())
