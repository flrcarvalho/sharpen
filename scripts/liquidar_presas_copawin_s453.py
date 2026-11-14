"""Liquida as apostas da CopaWin que ficaram ABERTAS com o resultado provado no cru (s453, 14/11/2026).

Por quê: até a 0.7.81 o formatador da CopaWin mandava "a conferir — não liquidar" em dois casos
que o dinheiro prova, e a IA gravava a aposta aberta (a Caixa contava a stake "em aberto"):

  • Jonathan, 7 simples de Handicap Asiático com linha PARTIDA (.25/.75) que a casa devolve
    `won`: 6 meias derrotas (retorno = stake ÷ 2 → HL) e 1 meia vitória (retorno = stake ÷ 2 ×
    odd + stake ÷ 2 → HW). A odd é a da casa; a linha guardava retorno ÷ stake (0,5 e 1,74).
  • Feca, 3 cashouts de 200 por 180 (a s454 consertou o formatador na 0.7.80; as linhas são de
    antes): W @ 0,9 = cashout ÷ stake (MASTER_RESULTADO §5.6), com as três provas da `CASA_COPAWIN
    §7` (status `cashout`, `cashout_used`, retorno = `cashout_value`).

Para cada código: a linha está ABERTA, sem correção humana de resultado (`correcoes`, origem
NULL), e o cru mais recente da casa prova o resultado pela regra do formatador (`_meiaCW` e
`_cashoutCW`, `extensor/content.js`). Qualquer divergência: aquele dono inteiro fica sem escrita.

    python scripts/liquidar_presas_copawin_s453.py            # ensaio, nada escrito
    python scripts/liquidar_presas_copawin_s453.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

RASTRO = "script_s453"
ALVOS = {
    "Jonathan": ["655775", "662066", "662233", "666355", "672724", "698917", "705748"],
    "Feca": ["718108", "718109", "718110"],
}
CENTAVO = Decimal("0.01")
_LINHA_PARTIDA = re.compile(r"(?:^|[\s(])([+-]?\d+\.(?:25|75))(?=$|[\s)])")


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _j(v):
    return json.loads(v) if isinstance(v, str) else v


def _dec(txt) -> Decimal:
    s = str(txt)
    return Decimal(s.replace(".", "").replace(",", ".")) if "," in s else Decimal(s)


def _br(d: Decimal) -> str:
    return format(d.normalize(), "f").replace(".", ",")


def veredito(cru: dict) -> tuple[str, Decimal] | None:
    """(resultado, odd) que o cru PROVA, pela regra do formatador; None = não prova."""
    st, ret, odd = _dec(cru["stake"]), _dec(cru["actual_return"]), _dec(cru["total_odds"])
    itens = cru.get("items") or []
    if (cru.get("status") == "cashout" and str(cru.get("cashout_used")) in ("1", "True", "true")
            and abs(ret - _dec(cru.get("cashout_value") or "-1")) < CENTAVO and abs(ret - st) >= CENTAVO):
        return "W", ret / st
    if len(itens) != 1 or itens[0].get("market_key") == "combined" or odd <= 1:
        return None
    if not _LINHA_PARTIDA.search(str(itens[0].get("selection_name") or "")):
        return None
    if cru.get("status") == "won" and abs(ret - (st / 2 * odd + st / 2)) <= CENTAVO:
        return "HW", odd
    if cru.get("status") in ("won", "lost") and abs(ret - st / 2) <= CENTAVO:
        return "HL", odd
    return None


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    planos = []
    async with pool.acquire() as conn:
        for dono, cods in ALVOS.items():
            linhas = await conn.fetch(
                "SELECT b.id, b.codigo_bilhete, b.resultado, b.extraction_state, b.stake, b.odd, "
                "EXISTS (SELECT 1 FROM correcoes c WHERE c.bilhete_id = b.id AND c.dono = b.dono "
                "AND c.campo = 'resultado' AND c.origem IS NULL) AS humano "
                "FROM bilhetes b WHERE b.dono = $1 AND b.casa = 'CopaWin' "
                "AND b.codigo_bilhete = ANY($2::text[])", dono, cods)
            crus = {r["codigo"]: _j(r["cru"]) for r in await conn.fetch(
                "SELECT DISTINCT ON (codigo) codigo, cru FROM captura_crua WHERE dono = $1 "
                "AND upper(casa) = 'COPAWIN' AND codigo = ANY($2::text[]) "
                "ORDER BY codigo, recebido_em DESC", dono, cods)}
            erros, plano = [], []
            por_cod = {}
            for r in linhas:
                por_cod.setdefault(r["codigo_bilhete"], []).append(r)
            for cod in cods:
                rs, cru = por_cod.get(cod, []), crus.get(cod)
                if len(rs) != 1 or cru is None:
                    erros.append(f"{cod}: {len(rs)} linha(s), cru {'ok' if cru else 'AUSENTE'}")
                    continue
                r = rs[0]
                if r["extraction_state"] != "aberta" or r["resultado"] or r["humano"]:
                    erros.append(f"{cod}: linha não está aberta sem correção humana")
                    continue
                if _dec(r["stake"]) != _dec(cru["stake"]):
                    erros.append(f"{cod}: stake da linha {r['stake']} × cru {cru['stake']}")
                    continue
                v = veredito(cru)
                if v is None:
                    erros.append(f"{cod}: o cru não prova o resultado ({cru.get('status')})")
                    continue
                plano.append((r["id"], cod, r["odd"], v[0], _br(v[1].quantize(Decimal("0.00000001")))))
            if erros:
                print(f"{dono}: NADA SERÁ ESCRITO\n  " + "\n  ".join(erros))
                continue
            for i, cod, odd_antes, res, odd in plano:
                print(f"{dono} {cod} (id {i}): aberta, odd {odd_antes} → {res} @ {odd}")
            planos.append((dono, plano))
    if not aplicar:
        print("\nENSAIO: nada escrito (use --aplicar).")
        return
    for dono, plano in planos:
        for i, cod, _antes, res, odd in plano:
            ok = await atualizar_bilhete(i, {"resultado": res, "odd": odd}, dono, rastro=RASTRO)
            print(f"{dono} {cod}: {'gravado' if ok else 'atualizar_bilhete RECUSOU'}")


if __name__ == "__main__":
    asyncio.run(main())
