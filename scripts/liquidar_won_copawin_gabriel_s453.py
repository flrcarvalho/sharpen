"""Liquida as 2 múltiplas GANHAS da CopaWin do Gabriel que a IA gravou abertas (s453, 14/11/2026).

Por quê: até a 0.7.80 o formatador da CopaWin só escrevia `Ganhou → W` quando o retorno fechava
`stake × total_odds` no centavo. As duas não fecham por motivos legítimos, e o bloco dizia "a
conferir — não liquidar"; a IA obedeceu e as deixou abertas (R$ 600 a mais "em aberto" na Caixa,
e R$ 5.235,60 de lucro fora da banca):

  • 713692: múltipla com perna anulada (`has_void_leg`); odd 16,98 → 8,71, retorno 2.613,00.
  • 713707: `total_odds` vem com 2 casas (10.74); a odd é 10,742, retorno 3.222,60.

A 0.7.81 conserta o formatador (`CASA_COPAWIN §5`). Este script conserta as duas linhas.
Antes de escrever, confere: a linha está ABERTA na conta, com stake 300; o cru mais recente da
casa diz `won`; e o `actual_return` é exatamente stake × a odd já gravada na linha. Qualquer
divergência: não escreve nada. A odd não muda (ela já é retorno ÷ stake); só o resultado.

    python scripts/liquidar_won_copawin_gabriel_s453.py            # ensaio, nada escrito
    python scripts/liquidar_won_copawin_gabriel_s453.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

DONO = "Gabriel"
RASTRO = "script_s453"
CODIGOS = ["713692", "713707"]


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _j(v):
    return json.loads(v) if isinstance(v, str) else v


def _dec(txt) -> Decimal:
    return Decimal(str(txt).replace(".", "").replace(",", ".")) if "," in str(txt) else Decimal(str(txt))


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = {r["codigo_bilhete"]: r for r in await conn.fetch(
            "SELECT id, codigo_bilhete, parceiro, resultado, extraction_state, stake, odd "
            "FROM bilhetes WHERE dono = $1 AND casa = 'CopaWin' AND codigo_bilhete = ANY($2::text[])",
            DONO, CODIGOS)}
        n_linhas = await conn.fetchval(
            "SELECT count(*) FROM bilhetes WHERE dono = $1 AND casa = 'CopaWin' "
            "AND codigo_bilhete = ANY($2::text[])", DONO, CODIGOS)
        crus = {r["codigo"]: _j(r["cru"]) for r in await conn.fetch(
            "SELECT DISTINCT ON (codigo) codigo, cru FROM captura_crua WHERE dono = $1 "
            "AND upper(casa) = 'COPAWIN' AND codigo = ANY($2::text[]) ORDER BY codigo, recebido_em DESC",
            DONO, CODIGOS)}
    erros, plano = [], []
    if n_linhas != len(linhas) or len({r["parceiro"] for r in linhas.values()}) > 1:
        erros.append(f"{n_linhas} linha(s) para {len(CODIGOS)} códigos, ou em mais de uma conta")
    for cod in CODIGOS:
        r, c = linhas.get(cod), crus.get(cod)
        if r is None or c is None:
            erros.append(f"{cod}: linha {'ok' if r else 'AUSENTE'}, cru {'ok' if c else 'AUSENTE'}")
            continue
        if r["extraction_state"] != "aberta" or r["resultado"]:
            erros.append(f"{cod}: a linha não está aberta ({r['extraction_state']}, {r['resultado']!r})")
            continue
        stake, odd = _dec(r["stake"]), _dec(r["odd"])
        ret = Decimal(str(c.get("actual_return")))
        if c.get("status") != "won" or Decimal(str(c.get("stake"))) != stake or stake != Decimal("300"):
            erros.append(f"{cod}: cru {c.get('status')} stake {c.get('stake')} × linha {stake}")
            continue
        if abs(stake * odd - ret) > Decimal("0.01"):
            erros.append(f"{cod}: stake {stake} × odd {odd} = {stake * odd} ≠ retorno {ret}")
            continue
        plano.append((r["id"], cod, odd, ret))
    if erros:
        print("NADA ESCRITO:\n  " + "\n  ".join(erros))
        return
    for i, cod, odd, ret in plano:
        print(f"{cod} (id {i}): aberta → W @ {odd} (retorno {ret}, P/L {ret - 300})")
    if not aplicar:
        print("\nENSAIO: nada escrito (use --aplicar).")
        return
    for i, cod, _odd, _ret in plano:
        ok = await atualizar_bilhete(i, {"resultado": "W"}, DONO, rastro=RASTRO)
        print(f"{cod}: {'W gravado' if ok else 'atualizar_bilhete RECUSOU'}")


if __name__ == "__main__":
    asyncio.run(main())
