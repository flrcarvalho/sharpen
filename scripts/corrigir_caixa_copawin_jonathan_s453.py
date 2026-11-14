"""Tira da Caixa da CopaWin do Jonathan a contagem dupla criada pelo `liquidar_presas_copawin_s453`.

Por quê (s453, 14/11/2026). A Caixa foi ligada em 12/11 às 16:33 (Brasília) com saldo 2.668,00, e o
`abertas_corte` gravou o que estava ABERTO NO SHARPEN, não na casa. Seis apostas já tinham sido
pagas pela CopaWin entre 07/11 e 12/11 00:07, mas estavam presas abertas no Sharpen (o formatador
mandava "a conferir"). O retorno delas (R$ 722,50) já estava dentro dos 2.668,00. Quando o script
da s453 as liquidou, a projeção passou a somar esse retorno DE NOVO (regra do `abertas_corte`: quem
estava lá volta stake + P/L ao liquidar).

    655775 (HL 87,50) · 662233 (HL 25,00) · 662066 (HL 50,00) · 672724 (HW 435,00)
    666355 (HL 75,00) · 698917 (HL 50,00)

A sétima, 705748 (HL, retorno 75,00, paga às 18:29 de 12/11, depois da ativação), entrou certa no
`abertas_corte`; mas a conferência das 23:57 viu os 75 a mais na casa e o Jonathan lançou o Ajuste
de +75,00 por causa dela. Com a aposta liquidada, os 75 contam duas vezes: o Ajuste sai.

O que faz: (1) tira os 6 ids do `abertas_corte` do inicial 2954, onde passam a valer como apostas
anteriores ao corte (o dinheiro delas já está no saldo informado); (2) apaga o Ajuste 2975, e
imprime a linha inteira antes, para poder ser relançado à mão. Confere antes: o inicial e o ajuste
são os medidos, as 6 estão liquidadas, e a projeção cai exatamente 797,50.

    python scripts/corrigir_caixa_copawin_jonathan_s453.py            # ensaio, nada escrito
    python scripts/corrigir_caixa_copawin_jonathan_s453.py --aplicar
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import _caixa_mov_dict, _caixa_projetar, _moeda_conta  # noqa: E402

DONO, CASA = "Jonathan", "CopaWin"
INICIAL, AJUSTE = 2954, 2975
TIRAR = {435593, 435618, 435619, 435627, 435653, 435788}
QUEDA = 797.50


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
        ini = await conn.fetchrow("SELECT * FROM caixa_mov WHERE id = $1 AND dono = $2 AND tipo = 'inicial'",
                                  INICIAL, DONO)
        aj = await conn.fetchrow("SELECT * FROM caixa_mov WHERE id = $1 AND dono = $2 AND tipo = 'ajuste'",
                                 AJUSTE, DONO)
        if not ini or not aj or ini["parceiro_id"] != aj["parceiro_id"] or float(aj["valor"]) != 75.0:
            print("NADA ESCRITO: inicial ou ajuste não são os medidos")
            return
        p = await conn.fetchrow("SELECT id, casa, nome, arquivado, moeda FROM parceiros WHERE id = $1",
                                ini["parceiro_id"])
        if p["casa"] != CASA or not TIRAR <= set(ini["abertas_corte"] or []):
            print("NADA ESCRITO: conta ou abertas_corte diferente do medido")
            return
        res = {r["id"]: r["resultado"] for r in await conn.fetch(
            "SELECT id, resultado FROM bilhetes WHERE id = ANY($1::int[])", list(TIRAR))}
        if len(res) != 6 or not all(res.values()):
            print(f"NADA ESCRITO: as 6 não estão todas liquidadas ({res})")
            return
        movs = [_caixa_mov_dict(r) for r in await conn.fetch(
            "SELECT * FROM caixa_mov WHERE parceiro_id = $1 ORDER BY data, id", p["id"])]
        apostas = [dict(r) for r in await conn.fetch(
            "SELECT id, casa, parceiro, stake, odd, resultado, data, criado_em, stake_orig, moeda, cotacao, "
            "stake_freebet FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3", DONO, CASA, p["nome"])]
    moeda = _moeda_conta(p)
    antes = _caixa_projetar(movs, apostas, moeda, CASA)
    novos = []
    for m in movs:
        if m["id"] == AJUSTE:
            continue
        if m["id"] == INICIAL:
            m = dict(m, abertas_corte=[i for i in m["abertas_corte"] if i not in TIRAR])
        novos.append(m)
    depois = _caixa_projetar(novos, apostas, moeda, CASA)
    queda = round(antes["disponivel"] - depois["disponivel"], 2)
    print(f"disponível {antes['disponivel']:.2f} → {depois['disponivel']:.2f} (queda {queda:.2f}); "
          f"banca {antes['banca']:.2f} → {depois['banca']:.2f}; em aberto {depois['aberto']:.2f}")
    print(f"Ajuste a apagar: {dict(aj)}")
    if abs(queda - QUEDA) > 0.005:
        print(f"NADA ESCRITO: a queda devia ser {QUEDA:.2f}")
        return
    if not aplicar:
        print("\nENSAIO: nada escrito (use --aplicar).")
        return
    async with pool.acquire() as conn:
        async with conn.transaction():
            novo = [i for i in ini["abertas_corte"] if i not in TIRAR]
            await conn.execute("UPDATE caixa_mov SET abertas_corte = $1 WHERE id = $2", novo, INICIAL)
            await conn.execute("DELETE FROM caixa_mov WHERE id = $1 AND dono = $2", AJUSTE, DONO)
    print("gravado: 6 ids fora do abertas_corte, ajuste 2975 apagado")


if __name__ == "__main__":
    asyncio.run(main())
