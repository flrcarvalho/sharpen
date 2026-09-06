# -*- coding: utf-8 -*-
"""Conserta a Caixa da conta renanfernando01 [Richard] / Betnacional (s327).

O QUE ACONTECEU
---------------
A Caixa foi ligada NO MEIO da captura. Cronologia medida no banco:

    03:17:32  Caixa ligada     -> abertas_corte = []   (o banco ainda nao tinha aberta)
    03:17:59  IA termina       (uso_tokens id 2163)
    03:18:19  /salvar grava    -> 3 apostas nascem ABERTAS: R$ 600,00
    03:18:35  Conferencia      -> projetado -599,00 · saldo real 2.379,87
                               -> Ajuste +2.978,87  (R$ 600,00 a mais do que devia)

`abertas_corte` e um retrato do que o SHARPEN SABIA naquele segundo -- nao do que a
CASA TINHA. O dinheiro das 3 abertas ja tinha saido da conta; o Sharpen so nao sabia
ainda. O Ajuste da conferencia entao cimentou o erro.

Junto veio um segundo defeito, independente: a captura de 05/09 devolveu a multipla do
Falkirk SEM a 11a coluna (o codigo). Sem codigo a dedup cai na assinatura por conteudo,
e a "Migracao B" do UPSERT (que adota linha sem codigo) exige `odd` identica -- "14" nao
e "14,00". Quando o bilhete liquidou em 06/09, entrou linha NOVA (246454) em vez de
atualizar a velha (243667), que ficou aberta para sempre.

O ESTRAGO, CONFERIDO CONTRA A CASA
----------------------------------
    Saldo no corte (05/09)                              2.379,87
    + retorno das 3 abertas no corte                    1.662,26
        243665  R$300 @2,834    L  ->        0,00
        243666  R$150 @11,08173 W  ->    1.662,26   (card da casa: "Retorno R$ 1.662,26")
        243667  R$150 @14       L  ->        0,00
    + liquido das 8 apostadas depois do corte             515,96
                                                     ----------
    = saldo esperado hoje                               4.558,09   <- bate com a casa

A Caixa projetava 3.195,83. A diferenca de 1.362,26 e exatamente
+1.662,26 (retorno que ela nao conta) - 300,00 (Falkirk descontado duas vezes).

O QUE ESTE SCRIPT FAZ
---------------------
1. Apaga a linha fantasma (243667). A casa confirma "Sem apostas pendentes".
2. Grava `abertas_corte` no lancamento `inicial` com as 3 que estavam vivas no corte --
   usando o id que carrega cada bilhete HOJE (a do Falkirk e a 246454, nao a apagada).
3. Baixa o `ajuste` da conferencia em exatamente o `preso_corte` que faltava.

NAO mexe no lancamento `conferencia`: ele e a medicao daquele momento e nao se
recalcula (`repository._caixa_projetar`). O que ele registrou aconteceu de verdade.

    python scripts/corrigir_caixa_fantasma_s327.py            # ensaio
    python scripts/corrigir_caixa_fantasma_s327.py --aplicar
"""
import argparse
import asyncio
import io
import os
import sys
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _l in io.open(RAIZ / ".env", encoding="utf-8").read().splitlines():
    if _l.startswith("DATABASE_URL="):
        os.environ.setdefault("DATABASE_URL", _l.split("=", 1)[1].strip().strip('"').strip("'"))
sys.path.insert(0, str(RAIZ / "app"))

import asyncpg      # noqa: E402
import repository   # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DONO = "Feca"
PARCEIRO_ID = 17
FANTASMA = 243667                          # linha aberta sem codigo, gemea da 246454
ABERTAS_NO_CORTE = [243665, 243666, 246454]  # ids que carregam HOJE as 3 vivas no corte
SALDO_NA_CASA = 4558.09                    # lido na Betnacional em 06/09/2026


def _projetar(movs, apostas):
    return repository._caixa_projetar(
        [{"id": m["id"], "tipo": m["tipo"], "data": m["data"].isoformat(),
          "valor": float(m["valor"]), "obs": m["obs"] or "",
          "projetado": None if m["projetado"] is None else float(m["projetado"]),
          "abertas_corte": list(m["abertas_corte"] or []),
          "criado_em": m["criado_em"].isoformat()} for m in movs],
        apostas)


async def _ler(conn):
    p = await conn.fetchrow("SELECT casa, nome FROM parceiros WHERE id = $1", PARCEIRO_ID)
    apostas = [dict(r) for r in await conn.fetch(
        """SELECT id, stake, odd, resultado, data, criado_em FROM bilhetes
           WHERE dono = $1 AND casa = $2 AND parceiro = $3 AND NOT archived""",
        DONO, p["casa"], p["nome"])]
    movs = await conn.fetch(
        "SELECT * FROM caixa_mov WHERE parceiro_id = $1 ORDER BY criado_em", PARCEIRO_ID)
    return p, apostas, movs


def _linha(res):
    return (f"  inicial {res['inicial']:>10,.2f} · preso_corte {res['preso_corte']:>9,.2f} "
            f"({res['n_preso_corte']}) · ajustes {res['ajustes']:>10,.2f}\n"
            f"  P/L {res['pl']:>14,.2f} ({res['n_liquidadas']}) · em aberto {res['aberto']:>9,.2f} "
            f"({res['n_abertas']})\n"
            f"  banca {res['banca']:>12,.2f} · DISPONIVEL {res['disponivel']:>10,.2f}")


async def main(aplicar: bool) -> int:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
    try:
        p, apostas, movs = await _ler(conn)
        print(f"Conta: {p['nome']} / {p['casa']} (id {PARCEIRO_ID}, dono {DONO})\n")

        antes = _projetar(movs, apostas)
        print("ANTES")
        print(_linha(antes))
        print(f"  divergencia contra a casa ({SALDO_NA_CASA:,.2f}): "
              f"{SALDO_NA_CASA - antes['disponivel']:+,.2f}\n")

        ini = next(m for m in movs if m["tipo"] == "inicial")
        aj = next(m for m in movs if m["tipo"] == "ajuste")
        if list(ini["abertas_corte"] or []):
            print("abertas_corte JA preenchido — nada a fazer (idempotente).")
            return 0

        # O ajuste errou em exatamente o `preso_corte` que a ativacao nao enxergou.
        preso = sum(repository._num(a["stake"]) for a in apostas if a["id"] in ABERTAS_NO_CORTE)
        novo_ajuste = round(float(aj["valor"]) - preso, 2)
        print(f"preso_corte que faltou: {preso:,.2f}")
        print(f"ajuste {float(aj['valor']):,.2f} -> {novo_ajuste:,.2f}\n")

        # Simula o depois SEM gravar: tira o fantasma, poe abertas_corte, baixa o ajuste.
        ap2 = [a for a in apostas if a["id"] != FANTASMA]
        movs2 = []
        for m in movs:
            d = dict(m)
            if m["id"] == ini["id"]:
                d["abertas_corte"] = ABERTAS_NO_CORTE
            if m["id"] == aj["id"]:
                d["valor"] = novo_ajuste
            movs2.append(d)
        depois = _projetar(movs2, ap2)
        print("DEPOIS")
        print(_linha(depois))
        div = SALDO_NA_CASA - depois["disponivel"]
        print(f"  divergencia contra a casa ({SALDO_NA_CASA:,.2f}): {div:+,.2f}\n")

        if abs(div) > repository.CAIXA_TOL:
            print("ABORTADO: a projecao corrigida nao fecha com o saldo da casa.")
            return 1

        if not aplicar:
            print("ENSAIO — nada gravado. Rode com --aplicar para valer.")
            return 0

        async with conn.transaction():
            n = await conn.execute(
                "DELETE FROM bilhetes WHERE id = $1 AND dono = $2 AND extraction_state = 'aberta'"
                " AND codigo_bilhete IS NULL", FANTASMA, DONO)
            print(f"bilhete fantasma {FANTASMA}: {n}")
            await conn.execute(
                "UPDATE caixa_mov SET abertas_corte = $1 WHERE id = $2",
                ABERTAS_NO_CORTE, ini["id"])
            await conn.execute(
                "UPDATE caixa_mov SET valor = $1, obs = $2 WHERE id = $3",
                Decimal(str(novo_ajuste)),
                "Ajuste da conferencia de 05/09/26 (corrigido na s327: a Caixa foi ligada "
                "antes de a captura salvar as 3 apostas abertas, R$ 600,00)",
                aj["id"])

        _, apostas3, movs3 = await _ler(conn)
        final = _projetar(movs3, apostas3)
        print("\nGRAVADO — releitura do banco:")
        print(_linha(final))
        print(f"  divergencia contra a casa: {SALDO_NA_CASA - final['disponivel']:+,.2f}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    raise SystemExit(asyncio.run(main(ap.parse_args().aplicar)))
