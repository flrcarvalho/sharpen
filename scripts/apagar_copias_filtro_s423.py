"""Apaga as cópias com dado pessoal da limpeza de 12/10 (s409), em 19/10 (s423).

`captura_crua_copia_filtro` (192) e `ficha_sombra_copia_filtro` (55) foram o seguro do
`limpar_cru_filtro.py`: o cru antes do filtro, ainda com `Player` da MyStake e `nickname` da DEX.
Decisão do Feca (12/10, BACKLOG §1): em 19/10, se nada tiver dado errado, `DROP TABLE` nas duas.
Antes, as duas conferências que o BACKLOG pede, sobre a `captura_crua` de hoje:

  1. o filtro de hoje não corta mais nada (`limpar_cru_filtro.plano` vazio = sem `Player` nem
     `nickname`);
  2. o `hash` de toda linha é `cru.impressao` do cru filtrado, o mesmo que a rota calcula.

Qualquer uma falhando, nada é apagado. As contagens saem antes e depois.

    python scripts/apagar_copias_filtro_s423.py            # ensaio, nada escrito
    python scripts/apagar_copias_filtro_s423.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import cru as _cru  # noqa: E402
from database import get_pool  # noqa: E402
from limpar_cru_filtro import _carregar_env, plano  # noqa: E402

COPIAS = ("captura_crua_copia_filtro", "ficha_sombra_copia_filtro")
ESPERADO = {"captura_crua_copia_filtro": 192, "ficha_sombra_copia_filtro": 55}


async def contar(conn) -> dict:
    out = {}
    for t in COPIAS:
        existe = await conn.fetchval("SELECT to_regclass($1) IS NOT NULL", t)
        out[t] = await conn.fetchval(f"SELECT count(*) FROM {t}") if existe else None
    return out


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        antes = await contar(conn)
        print(f"antes: {antes} (esperado {ESPERADO})")
        linhas = await conn.fetch("SELECT id, dono, casa, parceiro, codigo, cru::text AS cru, "
                                  "removidos, hash FROM captura_crua ORDER BY id")
        a_cortar = plano(linhas)
        hash_errado = [r["id"] for r in linhas
                       if _cru.impressao(_cru.filtrar(json.loads(r["cru"]))[0]) != r["hash"]]
        print(f"captura_crua: {len(linhas)} linhas · ainda com dado que o filtro corta: "
              f"{len(a_cortar)} · hash diferente da impressão: {len(hash_errado)}"
              + (f" (ids {hash_errado[:10]})" if hash_errado else ""))
        if a_cortar or hash_errado:
            print("PARADO: a limpeza de 12/10 não se sustenta; as cópias ficam.")
            return
        if antes != ESPERADO:
            print("PARADO: as cópias não têm o tamanho registrado em 12/10; as cópias ficam.")
            return
        if not aplicar:
            print("ensaio: nada apagado. Rode com --aplicar.")
            return
        async with conn.transaction():
            for t in COPIAS:
                await conn.execute(f"DROP TABLE {t}")
        print(f"depois: {await contar(conn)} (None = a tabela não existe mais)")


if __name__ == "__main__":
    asyncio.run(main())
