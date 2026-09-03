# -*- coding: utf-8 -*-
"""Refaz o `abertas_corte` das caixas JÁ LIGADAS com a regra corrigida (s314).

POR QUE
-------
`bilhetes.data` é a data do EVENTO, não a da aposta. Aposta feita ontem para um jogo
da próxima semana tem `data` DEPOIS do corte — e mesmo assim o stake dela já saiu da
conta, logo já está descontado do saldo que o operador acabou de ler. A regra antiga
só reconhecia `data < corte`, então essa aposta ficava de fora e a projeção descontava
o stake DUAS vezes: divergência de nascença, justo no fluxo que a tela recomenda
("informe o saldo de hoje").

A regra nova vive em `repository._caixa_abertas_ids` — este script NÃO a reimplementa,
chama ela. Um segundo cálculo do mesmo fato divergiria em silêncio.

O QUE ELE FAZ
-------------
Para cada lançamento `inicial`, recalcula a lista e mostra o efeito no saldo projetado.
`--aplicar` grava; sem ele é ENSAIO. Idempotente: rodar duas vezes não muda nada.

    python scripts/recalcular_abertas_corte_s314.py            # ensaio
    python scripts/recalcular_abertas_corte_s314.py --aplicar

CUIDADO DELIBERADO: a lista é um retrato do momento da ativação. Para corte no PASSADO
a regra nova continua sendo um PISO (só entra o que provadamente já existia), então
recalcular hoje pode incluir apostas que nasceram depois — por isso o corte antigo só
é recalculado quando a lista MUDA para MAIOR, nunca para menor: nunca tiramos uma
aposta que a ativação original reconheceu.
"""
import argparse
import asyncio
import io
import os
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _l in io.open(RAIZ / ".env", encoding="utf-8").read().splitlines():
    if _l.startswith("DATABASE_URL="):
        os.environ.setdefault("DATABASE_URL", _l.split("=", 1)[1].strip().strip('"').strip("'"))
sys.path.insert(0, str(RAIZ / "app"))

import asyncpg  # noqa: E402
import repository  # noqa: E402


def _proj(movs, apostas):
    return repository._caixa_projetar(
        [{"id": m["id"], "tipo": m["tipo"], "data": m["data"].isoformat(),
          "valor": float(m["valor"]), "obs": m["obs"] or "",
          "projetado": None if m["projetado"] is None else float(m["projetado"]),
          "abertas_corte": list(m["abertas_corte"] or []),
          "criado_em": m["criado_em"].isoformat()} for m in movs],
        apostas)


async def main(aplicar: bool) -> int:
    dsn = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
    conn = await asyncpg.connect(dsn)
    hoje = date.today().isoformat()
    mudou = 0
    try:
        iniciais = await conn.fetch(
            "SELECT c.id, c.parceiro_id, c.dono, c.data, c.abertas_corte, "
            "p.casa, p.nome FROM caixa_mov c JOIN parceiros p ON p.id = c.parceiro_id "
            "WHERE c.tipo = 'inicial' ORDER BY c.id")
        print(f"{len(iniciais)} caixa(s) ligada(s)\n")
        for ini in iniciais:
            corte = ini["data"].isoformat()
            apostas = await repository._caixa_apostas(
                conn, ini["dono"], ini["casa"], ini["nome"])
            antes = sorted(ini["abertas_corte"] or [])
            novo = sorted(repository._caixa_abertas_ids(apostas, corte, hoje))
            # nunca REMOVE: a ativação original reconheceu aquelas apostas e o saldo
            # informado foi lido com elas já descontadas.
            final = sorted(set(antes) | set(novo))

            movs = await conn.fetch(
                "SELECT * FROM caixa_mov WHERE parceiro_id = $1 ORDER BY id", ini["parceiro_id"])
            antes_proj = _proj(movs, apostas)["disponivel"]
            simulado = [dict(m) for m in movs]
            for m in simulado:
                if m["tipo"] == "inicial":
                    m["abertas_corte"] = final
            depois_proj = _proj(simulado, apostas)["disponivel"]

            marca = "=" if final == antes else "MUDA"
            print(f"[{marca}] #{ini['parceiro_id']} {ini['casa']} · {ini['nome']} "
                  f"(dono {ini['dono']}, corte {corte})")
            print(f"        abertas_corte: {antes} -> {final}")
            print(f"        disponível:    {antes_proj} -> {depois_proj} "
                  f"(delta {round(depois_proj - antes_proj, 2)})")
            if final == antes:
                continue
            mudou += 1
            if aplicar:
                await conn.execute(
                    "UPDATE caixa_mov SET abertas_corte = $1::int[] WHERE id = $2 AND tipo = 'inicial'",
                    final, ini["id"])
                print("        gravado.")
        print(f"\n{mudou} caixa(s) a corrigir." + ("" if aplicar else "  ENSAIO — nada gravado."))
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true", help="grava (sem isto é ensaio)")
    raise SystemExit(asyncio.run(main(ap.parse_args().aplicar)))
