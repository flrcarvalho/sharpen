"""Corrige o 1º cashout da Cloudbet, na conta `Ellen [Eu]` do Feca (s453).

Por quê: até a 0.7.78 a captura lia a aposta de cashout da casa (`side: LAY`,
`isCashoutBet: true`, 3.129,82 USDT @ 1,043) como uma aposta, e a original (`CASHED_OUT`) ficava
aberta. A Caixa da Cloudbet mostrava −3.101,53 USDT disponível. A 0.7.79 conserta a captura
(`CASA_CLOUDBET §7`); este script conserta as duas linhas já gravadas.

  • a LAY (de512916-…) vai para a `lixeira_bilhetes` (`mantido_id` = a original);
  • a original (942c19e8-…) vira W @ 0,33645: cashout 134,58 ÷ stake 400 (MASTER_RESULTADO
    §5.6). Card do Feca: "Aposta (2 aposta(s)) $0.00", "L/P −$265,42" = 400 × (0,33645 − 1).

Antes de escrever, confere no CRU da casa (`captura_crua`): a LAY é `isCashoutBet` da mesma
sub-posição da original, a original é `CASHED_OUT`, e a soma dos `returnAmount` bate com o
`portfolio` da sub-posição. Confere também que as duas linhas estão como a captura antiga as
gravou (abertas, stakes 3129.82 e 400). Qualquer divergência: não escreve nada.

    python scripts/corrigir_cashout_cloudbet_s453.py            # ensaio, nada escrito
    python scripts/corrigir_cashout_cloudbet_s453.py --aplicar
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
sys.path.insert(0, str(ROOT / "scripts"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402
from _lixeira import mover_para_lixeira  # noqa: E402

DONO = "Feca"
CONTA = "Ellen [Eu]"
RASTRO = "script_s453"
BACK = "942c19e8-da04-484e-bbcd-9654e7b394d3"
LAY = "de512916-8fb8-4883-b951-8cbc9beb1eb8"


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _j(v):
    return json.loads(v) if isinstance(v, str) else v


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = {r["codigo_bilhete"]: r for r in await conn.fetch(
            "SELECT id, codigo_bilhete, resultado, extraction_state, stake_orig, odd FROM bilhetes "
            "WHERE dono = $1 AND casa = 'Cloudbet' AND parceiro = $2 AND codigo_bilhete = ANY($3::text[])",
            DONO, CONTA, [BACK, LAY])}
        crus = {r["codigo"]: _j(r["cru"]) for r in await conn.fetch(
            "SELECT DISTINCT ON (codigo) codigo, cru FROM captura_crua WHERE dono = $1 "
            "AND upper(casa) = 'CLOUDBET' AND codigo = ANY($2::text[]) ORDER BY codigo, recebido_em DESC",
            DONO, [BACK, LAY])}
        erros = []
        if set(linhas) != {BACK, LAY}:
            erros.append(f"linhas no banco: {sorted(linhas)}")
        else:
            if linhas[LAY]["extraction_state"] != "aberta" or str(linhas[LAY]["stake_orig"]) != "3129.82":
                erros.append(f"LAY não está como a captura antiga gravou: {dict(linhas[LAY])}")
            if linhas[BACK]["extraction_state"] != "aberta" or str(linhas[BACK]["stake_orig"]) != "400.00":
                erros.append(f"original não está como a captura antiga gravou: {dict(linhas[BACK])}")
        if set(crus) != {BACK, LAY}:
            erros.append(f"crus: {sorted(crus)}")
        else:
            a, lay = crus[BACK]["aposta"], crus[LAY]["aposta"]
            leg = a.get("betLegsIdentifier")
            if lay.get("isCashoutBet") is not True or lay.get("side") != "LAY" or lay.get("betLegsIdentifier") != leg:
                erros.append("o cru da LAY não é a aposta de cashout da mesma sub-posição")
            if a.get("result") != "CASHED_OUT" or a.get("isCashoutBet") is True:
                erros.append(f"a original não está CASHED_OUT: {a.get('result')}")
            sub = next((p for p in crus[BACK]["posicao"]["positions"] if p.get("betLegIdentifier") == leg), {})
            port = Decimal(str(((sub.get("portfolio") or {}).get("USDT") or {}).get("returnAmount")))
            lucro = Decimal(str(a["returnAmount"])) + Decimal(str(lay["returnAmount"]))
            cashout = Decimal(str(a["stake"])) + lucro
            if port != lucro or cashout != Decimal("134.58"):
                erros.append(f"dinheiro: lucro {lucro}, portfolio {port}, cashout {cashout}")
        if erros:
            print("NADA ESCRITO:\n  " + "\n  ".join(erros))
            return
        odd = (cashout / Decimal(str(a["stake"]))).normalize()
        print(f"LAY  {LAY} (id {linhas[LAY]['id']}): 3129.82 @ {linhas[LAY]['odd']} aberta → lixeira")
        print(f"BACK {BACK} (id {linhas[BACK]['id']}): aberta → W @ {odd} "
              f"(cashout {cashout} ÷ 400; P/L {lucro})")
        if not aplicar:
            print("\nENSAIO: nada escrito (use --aplicar).")
            return
        async with conn.transaction():
            saiu = await mover_para_lixeira(
                conn, "b.id = $1 AND b.dono = $2", [linhas[LAY]["id"], DONO],
                "aposta de cashout da Cloudbet (LAY, isCashoutBet) gravada como aposta pela "
                "captura antiga; o cashout é da original (s453)", mantido_id=linhas[BACK]["id"])
        print(f"lixeira: {len(saiu)} linha(s)")
    ok = await atualizar_bilhete(linhas[BACK]["id"], {"resultado": "W", "odd": str(odd).replace(".", ",")},
                                 DONO, rastro=RASTRO)
    print(f"original: {'W gravado' if ok else 'atualizar_bilhete RECUSOU'}")


if __name__ == "__main__":
    asyncio.run(main())
