# -*- coding: utf-8 -*-
"""Grava o BÔNUS DE ODD da MyStake na odd das ganhas já liquidadas (s422).

O QUE ACONTECEU
---------------
O card da MyStake mostra "+5%" (ou "+3%") ao lado da Quantia: é bônus de odd da múltipla,
pago sobre o LUCRO da ganha. A API (`gethistory`) traz o percentual em `RiskBonusPercent` e
o `WinAmount` SEM o bônus. A captura lia só o `WinAmount`, então a odd foi para a planilha
sem o bônus e a Caixa da conta Ellen [Eu] acusou R$ 297,75 a menos que a casa:

    4 ganhas com bônus (5%, 5%, 5%, 3%)        248,04
    "Bonus Activation" de 11/10 (extrato)        49,71
                                               ------
                                                297,75   = a divergência da conferência

A captura nova já soma o bônus (`adaptadores/tv.py` e `formatTicketTV`). As linhas já
LIQUIDADAS não se corrigem sozinhas: o UPSERT congela a odd quando a aposta resolve.

O QUE ESTE SCRIPT FAZ
---------------------
Para cada ganha da MyStake cujo cru mais recente traz `RiskBonusPercent` > 0:

    bônus  = (WinAmount − Amount) × pct, ao centavo, metade para cima
    odd    = (WinAmount + bônus) ÷ Amount            (Retorno ÷ Stake, a régua da W)

Só escreve se a odd do banco AINDA é a da API sem bônus (`Amount × odd == WinAmount` ao
centavo, na moeda da conta). Odd que alguém já mexeu fica como está, e odd/resultado com
registro em `correcoes` também (correção humana manda). Cashout e não-ganha: fora.

    python scripts/corrigir_bonus_odd_mystake_s422.py            # ensaio
    python scripts/corrigir_bonus_odd_mystake_s422.py --aplicar --dono Feca

`--dono` restringe a um dono. Aplicado na s422 aos dois donos com ganha bonificada:
Feca (Ellen [Eu], 4 odds) e Gabriel (gfatuch [Fatuch], 8 odds, USDT). As outras contas
MyStake medidas (LavaPessoal, WilliamOliveira) só têm o campo em perdida; Tivo, Betfast e
Faz1bet não têm cru nenhum. Ensaio depois disso: nada a corrigir.

⚠️ CONFERÊNCIA QUE JÁ ABSORVEU O BÔNUS. A Caixa do Gabriel tinha conferido em 13/10 com
+51,97 e um Ajuste do mesmo valor, que já continha o bônus da 307606028 (22,78, liquidada
em 12/10, antes da conferência). Corrigir a odd sem mexer no Ajuste contaria os 22,78 duas
vezes, e por isso o Ajuste baixou para 29,19 (`caixa_editar_mov`, valor antigo em
`Backups/s422_bonus_odd_mystake_gabriel/`). Antes de rodar em conta com Caixa, compare o
instante de cada ganha bonificada com as conferências que têm Ajuste depois.
"""
import argparse
import asyncio
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

from database import get_pool  # noqa: E402
from repository import _num, atualizar_bilhete  # noqa: E402

DESTINO = ROOT / "Backups" / "s422_bonus_odd_mystake" / "bilhetes_antes.json"
CENTAVO = Decimal("0.01")


def _dec(v) -> Decimal:
    return Decimal(str(v))


def _odd_br(d: Decimal) -> str:
    d = d.quantize(Decimal("1e-10")).normalize()
    return format(d, "f").replace(".", ",")


async def main(aplicar: bool, dono: str | None) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        crus = await conn.fetch("""
            SELECT DISTINCT ON (dono, parceiro, codigo) dono, parceiro, codigo, cru
              FROM captura_crua
             WHERE casa = 'MYSTAKE'
             ORDER BY dono, parceiro, codigo, recebido_em DESC""")
        travados = {(r["bilhete_id"], r["campo"]) for r in await conn.fetch(
            "SELECT bilhete_id, campo FROM correcoes WHERE campo IN ('odd', 'resultado')")}

        snapshot, pulados = [], []
        for c in crus:
            if dono and c["dono"] != dono:
                continue
            t = json.loads(c["cru"]) if isinstance(c["cru"], str) else c["cru"]
            pct = _dec(t.get("RiskBonusPercent") or 0)
            if pct <= 0 or t.get("Status") != 10 or t.get("Result") != 2 or t.get("CashOut"):
                continue
            amount, win = _dec(t["Amount"]), _dec(t["WinAmount"])
            if win - amount < CENTAVO:
                continue
            bonus = ((win - amount) * pct).quantize(CENTAVO, rounding=ROUND_HALF_UP)
            odd_nova = _odd_br((win + bonus) / amount)
            b = await conn.fetchrow(
                """SELECT id, casa, parceiro, stake, stake_orig, odd, resultado, descricao
                     FROM bilhetes
                    WHERE dono = $1 AND parceiro = $2 AND codigo_bilhete = $3
                      AND lower(casa) = 'mystake'""",
                c["dono"], c["parceiro"], c["codigo"])
            if not b:
                pulados.append((c["dono"], c["codigo"], "sem linha no banco"))
                continue
            if b["resultado"] != "W":
                pulados.append((c["dono"], c["codigo"], f"resultado {b['resultado']} no banco"))
                continue
            odd_db = _num(b["odd"])
            if abs(Decimal(str(round(odd_db, 10))) * amount - win) > CENTAVO:
                pulados.append((c["dono"], c["codigo"], f"odd {b['odd']} já não é a da API"))
                continue
            if (b["id"], "odd") in travados or (b["id"], "resultado") in travados:
                pulados.append((c["dono"], c["codigo"], "corrigida à mão (correcoes)"))
                continue
            snapshot.append({**{k: b[k] for k in ("id", "casa", "parceiro", "stake", "odd",
                                                   "resultado", "descricao")},
                             "stake_orig": None if b["stake_orig"] is None else str(b["stake_orig"]),
                             "dono": c["dono"], "codigo": c["codigo"], "pct": str(pct),
                             "win_api": str(win), "bonus": str(bonus), "odd_nova": odd_nova})
            print(f'{b["id"]:>7} {c["dono"]:<16} {c["parceiro"][:20]:<20} {c["codigo"]} '
                  f'{t.get("CurrencySTR", ""):<4} {amount:>7} × pct {pct} · bônus {bonus:>7} · '
                  f'odd {b["odd"]} → {odd_nova}')

    print(f"\na corrigir: {len(snapshot)} · pulados: {len(pulados)}")
    for p in pulados:
        print("  pulado:", *p)
    if not aplicar:
        print("\nENSAIO — nada gravado. Rode com --aplicar.")
        return
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1, default=str),
                       encoding="utf-8")
    for s in snapshot:
        ok = await atualizar_bilhete(s["id"], {"odd": s["odd_nova"]}, s["dono"])
        if not ok:
            print(f'  ⚠ UPDATE não aplicou no bilhete {s["id"]}')
    print(f"aplicado. Snapshot de antes em {DESTINO}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--dono")
    a = ap.parse_args()
    asyncio.run(main(a.aplicar, a.dono))
