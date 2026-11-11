"""Corrige as 2 simples da 3et do Gabriel gravadas como "Mercado Especial - REVISAR" (s443).

Por quê: até a 0.7.73 a SIMPLES da 3et ia à IA com "Seleções:" vazio (a casa não manda `legs`;
a seleção vem solta no bilhete, `casas/CASA_3ET.md §2.5`). A IA, sem nada para ler, gravou o
fallback. Recapturar NÃO conserta: o UPSERT nunca regrava esporte/aposta/descrição de linha
`origem='extracao'` (CLAUDE.md, "Recapturar a casa NÃO conserta linha assim").

Os valores vêm do CRU da casa em `captura_crua` (o mesmo de `3et.simples.settled.json`), lidos
pelas regras do MASTER, e o script CONFERE o cru antes de escrever: se o mercado, a seleção ou o
jogo do cru não forem os esperados, não escreve nada.

  • 51666575 — `Kobi Simmons - Assists`, `Under (+2.5)`, Fenerbahce vs Cazoo Baskonia Vitoria
    Gasteiz, Basketball. Estatística individual de basquete = `Player Props`
    (`MASTER_APOSTAS`, Basquete, "assistências").
  • 51851882 — `Total Touchdowns`, `Over 5.5`, Tampa Bay Buccaneers at Chicago Bears, American
    Football. Total do JOGO, sem categoria própria no MASTER (a seção NFL só tem Jardas,
    Touchdown de jogador e resultado) = `Outros`.

Só esporte, aposta e descrição. Stake, odd, resultado, data e TIPSTER ficam como estão. A
escrita é a da grade (`repository.atualizar_bilhete`, assinatura e `correcoes` incluídas), com
`rastro='script_s443'`.

    python scripts/corrigir_3et_simples_s443.py            # ensaio, nada escrito
    python scripts/corrigir_3et_simples_s443.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

DONO = "Gabriel"
RASTRO = "script_s443"
# código → (o que o cru tem de dizer, o que a linha passa a dizer)
ALVOS = {
    "51666575": (
        {"marketName": "Kobi Simmons - Assists", "runnerName": "Under (+2.5)",
         "event": "Fenerbahce vs Cazoo Baskonia Vitoria Gasteiz", "sport": "Basketball"},
        {"esporte": "Basquete", "aposta": "Player Props",
         "descricao": "Kobi Simmons - Under 2.5 Assistências [Fenerbahce v Cazoo Baskonia Vitoria Gasteiz]"},
    ),
    "51851882": (
        {"marketName": "Total Touchdowns", "runnerName": "Over 5.5",
         "event": "Tampa Bay Buccaneers at Chicago Bears", "sport": "American Football"},
        {"esporte": "Futebol Americano", "aposta": "Outros",
         "descricao": "Over 5.5 Touchdowns [Tampa Bay Buccaneers v Chicago Bears]"},
    ),
}


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _do_cru(cru: dict) -> dict:
    """Os 4 campos conferidos, da simples LIQUIDADA (plana)."""
    sel = cru.get("selection") if isinstance(cru.get("selection"), dict) else {}
    bt = cru.get("betType") if isinstance(cru.get("betType"), dict) else {}
    return {"marketName": cru.get("marketName"), "runnerName": cru.get("runnerName"),
            "event": sel.get("event"), "sport": bt.get("sport")}


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    planos = []
    async with pool.acquire() as conn:
        for cod, (cru_esperado, novo) in ALVOS.items():
            linhas = await conn.fetch(
                "SELECT id, esporte, aposta, descricao, resultado, stake, odd, tipster FROM bilhetes "
                "WHERE dono = $1 AND casa ILIKE '3et' AND codigo_bilhete = $2", DONO, cod)
            if len(linhas) != 1:
                print(f"{cod}: {len(linhas)} linha(s) no banco, esperava 1 — PULADO")
                continue
            r = linhas[0]
            cru_txt = await conn.fetchval(
                "SELECT cru FROM captura_crua WHERE dono = $1 AND upper(casa) = '3ET' AND codigo = $2 "
                "AND cru ? 'selection' ORDER BY id DESC LIMIT 1", DONO, cod)
            if cru_txt is None:
                print(f"{cod}: sem cru liquidado em captura_crua — PULADO")
                continue
            cru = cru_txt if isinstance(cru_txt, dict) else json.loads(cru_txt)
            if _do_cru(cru) != cru_esperado:
                print(f"{cod}: o cru não é o esperado ({_do_cru(cru)}) — PULADO")
                continue
            if "REVISAR" not in (r["descricao"] or ""):
                print(f"{cod}: a descrição já não é o fallback ({r['descricao']!r}) — PULADO")
                continue
            print(f"{cod} (id {r['id']}, tipster {r['tipster']!r}, {r['resultado']} {r['stake']} @ {r['odd']})")
            for k, v in novo.items():
                print(f"    {k}: {r[k]!r} → {v!r}")
            planos.append((r["id"], novo))
    if not aplicar:
        print(f"\nENSAIO: {len(planos)} linha(s) seriam corrigidas. Nada escrito (use --aplicar).")
        return
    n = 0
    for bid, novo in planos:
        if await atualizar_bilhete(bid, novo, DONO, rastro=RASTRO):
            n += 1
        else:
            print(f"id {bid}: atualizar_bilhete recusou")
    print(f"\nAPLICADO: {n} de {len(planos)} linha(s).")


if __name__ == "__main__":
    asyncio.run(main())
