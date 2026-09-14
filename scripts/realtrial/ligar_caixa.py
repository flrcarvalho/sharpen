# -*- coding: utf-8 -*-
"""Liga a Caixa Inteligente na base de demonstração (`/realtrial`).

ENSAIO É O PADRÃO. Sem `--gravar`, só mostra o que faria.

    python scripts/realtrial/ligar_caixa.py            # ensaio
    python scripts/realtrial/ligar_caixa.py --gravar

POR QUE ESTE SCRIPT EXISTE, e por que ele NÃO escreve em `caixa_mov`
--------------------------------------------------------------------
A Caixa é a única tela da demonstração que exige INVENTAR número: o saldo
inicial de cada conta não existe no dado importado. Mas o saldo em si é
derivado, e o que o banco guarda é o LANÇAMENTO — inclusive `abertas_corte`,
a lista de ids dos bilhetes que já estavam abertos no instante do corte.

Por isso tudo aqui passa por `repository.caixa_lancar`, o mesmo caminho do
botão do app. Escrever direto na tabela obrigaria a reconstruir `abertas_corte`
à mão, que é exatamente o caso do script que inflou a projeção em R$ 10.477
(CLAUDE.md). Aqui não há reconstrução nenhuma: a ativação é NOVA, com corte
HOJE, e nesse caso a regra é exata — se a aposta está aberta agora, o stake
dela saiu da conta antes de agora.

O QUE É INVENTADO, declarado
----------------------------
· o saldo inicial de cada conta (derivado do porte dela, para ficar plausível);
· quais contas ficam SEM caixa (a tela precisa mostrar o "faltam N");
· quais contas têm conferência batendo e quais divergem (é a divergência que
  mostra o recurso funcionando; uma tela toda verde não ensina nada).

Determinístico pela semente: rodar de novo dá os mesmos números.
"""
import argparse
import asyncio
import io
import pathlib
import random
import sys
from datetime import date

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "scripts" / "realtrial"))

import os  # noqa: E402
import exportar as ex  # noqa: E402

# `database.get_pool` le a DATABASE_URL do AMBIENTE, nao do .env (o app roda no
# Railway, onde ela e' env var). Rodando daqui, o .env e' a fonte -- sem isto o
# script morre em KeyError antes de tocar em qualquer coisa.
os.environ.setdefault("DATABASE_URL", ex._database_url())

import repository as repo  # noqa: E402

DONO = "realtrial"
SEMENTE = 20260914

# Proporções da encenação. Nenhuma é neutra: cada uma existe para que um estado
# da tela apareça no vídeo.
FRACAO_SEM_CAIXA = 0.18     # o box "N contas ainda sem caixa"
FRACAO_CONFERIDA = 0.55     # das ligadas, quantas o operador já conferiu
FRACAO_DIVERGENTE = 0.22    # das conferidas, quantas não batem


async def _contas(conn) -> list[dict]:
    """Contas da demonstração com o porte de cada uma (para o saldo ficar
    plausível: conta que gira R$ 200 não tem R$ 30 mil em caixa)."""
    linhas = await conn.fetch(
        """
        SELECT p.id, p.casa, p.nome,
               COALESCE(SUM(CASE WHEN b.stake ~ '^[0-9]+([.,][0-9]+)?$'
                                 THEN replace(b.stake, ',', '.')::numeric END), 0) AS turnover,
               COUNT(b.id) AS apostas
        FROM parceiros p
        LEFT JOIN bilhetes b
               ON b.dono = p.dono AND b.casa = p.casa AND b.parceiro = p.nome
        WHERE p.dono = $1
        GROUP BY p.id, p.casa, p.nome
        ORDER BY p.id
        """, DONO)
    return [dict(r) for r in linhas]


def _plano(contas: list[dict], semente: int) -> list[dict]:
    rng = random.Random(semente)
    plano = []
    for c in contas:
        if c["apostas"] == 0:
            continue                      # conta sem aposta fica sem caixa
        if rng.random() < FRACAO_SEM_CAIXA:
            continue
        # Saldo inicial ~ 6% do turnover da conta, com piso e teto, arredondado
        # para dezena. Não é uma conta financeira, é ordem de grandeza.
        base = float(c["turnover"]) * 0.06
        saldo = max(120.0, min(base, 18_000.0))
        saldo = round(saldo * rng.uniform(0.7, 1.4), -1)
        item = {"id": c["id"], "casa": c["casa"], "nome": c["nome"],
                "saldo": round(saldo, 2), "conferir": False, "divergir": 0.0}
        if rng.random() < FRACAO_CONFERIDA:
            item["conferir"] = True
            if rng.random() < FRACAO_DIVERGENTE:
                # Divergência de verdade: alguns por cento para cima ou para
                # baixo. É ela que faz o box de conferência acusar.
                item["divergir"] = round(saldo * rng.uniform(-0.09, 0.09), 2)
        plano.append(item)
    return plano


async def principal(gravar: bool, semente: int) -> None:
    pool = await repo.get_pool()
    async with pool.acquire() as conn:
        contas = await _contas(conn)
        ja = await conn.fetchval(
            "SELECT count(*) FROM caixa_mov WHERE dono = $1", DONO)

    plano = _plano(contas, semente)
    n_conf = sum(1 for p in plano if p["conferir"])
    n_div = sum(1 for p in plano if p["divergir"])
    print(f"# ligar Caixa -> {DONO}   (modo: {'GRAVAR' if gravar else 'ENSAIO'})")
    print(f"   contas cadastradas : {len(contas)}")
    print(f"   vão ganhar caixa   : {len(plano)}")
    print(f"   ficam sem caixa    : {len(contas) - len(plano)}")
    print(f"   com conferência    : {n_conf}  (divergentes: {n_div})")
    print(f"   já existe em caixa_mov: {ja}")
    print(f"   saldo inicial total: R$ {sum(p['saldo'] for p in plano):,.2f}"
          .replace(",", "·").replace(".", ",").replace("·", "."))

    if not gravar:
        print("\n## amostra do plano")
        for p in plano[:12]:
            extra = ""
            if p["conferir"]:
                extra = ("  conferência BATE" if not p["divergir"]
                         else f"  conferência DIVERGE em {p['divergir']:+.2f}")
            print(f"   {p['nome'][:26]:<26} {p['casa'][:14]:<14} "
                  f"R$ {p['saldo']:>10,.2f}{extra}")
        print("\nENSAIO: nada foi gravado. Use --gravar para valer.")
        return

    if ja:
        raise SystemExit(f"RECUSADO: já há {ja} lançamento(s) em caixa_mov de '{DONO}'.")

    hoje = date.today().isoformat()
    ok = falhas = 0
    for i, p in enumerate(plano, 1):
        # Caminho do app, nunca INSERT cru: é `caixa_lancar` que grava o
        # `abertas_corte` (os ids abertos no corte) e o `projetado` da conferência.
        r = await repo.caixa_lancar(DONO, p["id"], "inicial", hoje, p["saldo"],
                                    "Saldo inicial da demonstração")
        if not r.get("ok", True) and r.get("motivo"):
            print(f"   !! {p['nome']}: {r['motivo']}")
            falhas += 1
            continue
        ok += 1

        if p["conferir"]:
            # A conferência REGISTRA o projetado daquele instante; o valor
            # informado é o que o operador diz ter visto na casa.
            visao = await repo.caixa_conta(DONO, p["id"]) if hasattr(repo, "caixa_conta") else None
            projetado = (visao or {}).get("disponivel")
            informado = (projetado if projetado is not None else p["saldo"]) + p["divergir"]
            await repo.caixa_lancar(DONO, p["id"], "conferencia", hoje,
                                    round(max(0.0, informado), 2),
                                    "Conferência da demonstração")
        if i % 25 == 0:
            print(f"   {i}/{len(plano)}...")

    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT count(*) FROM caixa_mov WHERE dono = $1", DONO)
    print(f"\n   ativadas: {ok} · falhas: {falhas} · lançamentos em caixa_mov: {total}")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--semente", type=int, default=SEMENTE)
    a = ap.parse_args()
    asyncio.run(principal(a.gravar, a.semente))
