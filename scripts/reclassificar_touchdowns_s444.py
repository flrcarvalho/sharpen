"""Reclassifica o total de touchdowns do jogo para a categoria nova `Touchdowns` (s444).

Por quê: até a s444 o `MASTER_APOSTAS` não tinha categoria para o total de touchdowns do
jogo ou de um time (a seção NFL só cobria Jardas, touchdown de jogador e resultado). As 3
linhas desse mercado na base caíram em `Gols` (2, Bolsa de Aposta) e `Outros` (1, 3et, a do
script s443). A categoria nasceu na s444 (`MASTER_APOSTAS §3/§5 Touchdowns`).

Recapturar NÃO conserta: o UPSERT nunca regrava `aposta` de linha `origem='extracao'`.

Só a coluna `aposta`, e só se ela ainda for a esperada E a descrição for a esperada. Nenhuma
das 3 tem correção humana de `aposta` em `correcoes` (conferido em 11/11/2026); o script
confere de novo e pula se tiver. Escrita pela grade (`repository.atualizar_bilhete`, com
`correcoes`), `rastro='script_s444'`.

    python scripts/reclassificar_touchdowns_s444.py            # ensaio, nada escrito
    python scripts/reclassificar_touchdowns_s444.py --aplicar
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

RASTRO = "script_s444"
NOVA = "Touchdowns"
# id → (dono, aposta atual esperada, descrição esperada)
ALVOS = {
    266278: ("Feca", "Gols", "Over 9,5 Touchdowns [Seattle Seahawks v New Inglaterra Patriots]"),
    312172: ("realtrial", "Gols", "Over 9,5 Touchdowns [Seattle Seahawks v New Inglaterra Patriots]"),
    431169: ("Gabriel", "Outros", "Over 5.5 Touchdowns [Tampa Bay Buccaneers v Chicago Bears]"),
}


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
    planos = []
    async with pool.acquire() as conn:
        for bid, (dono, aposta, desc) in ALVOS.items():
            r = await conn.fetchrow(
                "SELECT dono, aposta, descricao, esporte FROM bilhetes WHERE id = $1", bid)
            if r is None:
                print(f"id {bid}: não existe mais — PULADO")
                continue
            if (r["dono"], r["aposta"], r["descricao"]) != (dono, aposta, desc):
                print(f"id {bid}: não é o esperado ({r['dono']}, {r['aposta']!r}, {r['descricao']!r}) — PULADO")
                continue
            humana = await conn.fetchval(
                "SELECT count(*) FROM correcoes WHERE bilhete_id = $1 AND campo = 'aposta' "
                "AND origem IS NULL", bid)
            if humana:
                print(f"id {bid}: tem correção humana de aposta — PULADO (decisão do dono)")
                continue
            print(f"id {bid} ({dono}): aposta {aposta!r} → {NOVA!r}  | {desc}")
            planos.append((bid, dono))
    if not aplicar:
        print(f"\nENSAIO: {len(planos)} linha(s) seriam reclassificadas. Nada escrito (use --aplicar).")
        return
    n = 0
    for bid, dono in planos:
        if await atualizar_bilhete(bid, {"aposta": NOVA}, dono, rastro=RASTRO):
            n += 1
        else:
            print(f"id {bid}: atualizar_bilhete recusou")
    print(f"\nAPLICADO: {n} de {len(planos)} linha(s).")


if __name__ == "__main__":
    asyncio.run(main())
