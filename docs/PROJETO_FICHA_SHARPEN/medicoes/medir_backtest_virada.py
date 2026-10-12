"""Backtest da virada (critério do Feca, 12/10/2026; s411). Banco: só SELECT. Sem IA, sem custo.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_backtest_virada.py [CASA ...]

O critério que substituiu as 30 liquidadas (D12) e a proposta das 10 ganhas: **a casa vira se
nenhum dinheiro (stake, resultado, retorno) divergir sem explicação**, comparando a Ficha com o
banco em TODAS as apostas que têm cru. As capturas do Feca já mandam o histórico que a casa
mostra, então o backtest é o próprio cru guardado. O Gabriel é só usuário: entra na conta se
tiver cru, mas não é critério de nada.

Uma linha por casa:
  comparadas   apostas (o cru mais recente de cada uma) com Ficha aceita E bilhete no banco
  dinheiro     divergências de stake, resultado, retorno ou freebet (`medir_regua_adaptadores.
               comparar`, estado `diverge`); odd diferente com P/L igual NÃO conta
  IA ainda aberta  a casa liquidou e a linha da IA ainda está aberta (explicada: é o tempo)
  recusadas    Ficha recusada pelo adaptador (vai para a IA: não é divergência, é cobertura)
  cobertura    apostas do dono com cru ÷ apostas daquela casa no banco (informativo, não trava)
  dicionário   Fichas aceitas com esporte E categoria traduzidos ÷ Fichas aceitas, e quantas
               dessas traduções dão o MESMO esporte e a MESMA categoria que a IA gravou

O dicionário é o da tabela `dicionario_termos` (semeado por `scripts/semear_dicionario.py`).
Como a semente nasce destes mesmos pares, a cobertura e a concordância aqui são IN-SAMPLE: o
que elas provam é a regra de montagem (Múltiplos, Múltipla, mercado + seleção), não o termo
que ainda não apareceu. Termo novo vai para a IA, e é isso que a cobertura mede depois.
"""
import asyncio
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medir_regua_adaptadores as regua  # noqa: E402  (também põe app/ no sys.path)

import dicionario  # noqa: E402
import ficha  # noqa: E402
from database import get_pool  # noqa: E402


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    regua._carregar_env()
    so = {a.upper() for a in sys.argv[1:]}
    pool = await get_pool()
    async with pool.acquire() as conn:
        crus = [dict(r) for r in await conn.fetch(
            "SELECT id, familia, casa, dono, parceiro, codigo, cru::text AS cru "
            "FROM captura_crua ORDER BY id")]
        nomes = {r["k"]: r["casa"] for r in await conn.fetch(
            "SELECT DISTINCT upper(replace(casa, ' ', '')) AS k, casa FROM bilhetes")}
        bil = collections.defaultdict(list)
        for b in await conn.fetch(
                "SELECT dono, casa, parceiro, codigo_bilhete, stake, odd, resultado, esporte, "
                "aposta, stake_orig::text, stake_freebet::text FROM bilhetes "
                "WHERE codigo_bilhete = ANY($1::text[])", [c["codigo"] for c in crus]):
            bil[(b["dono"], b["casa"], b["parceiro"], b["codigo_bilhete"])].append(dict(b))
        no_banco = {(r["dono"], r["casa"]): r["n"] for r in await conn.fetch(
            "SELECT dono, casa, count(*) AS n FROM bilhetes GROUP BY 1, 2")}
        termos = {}
        for casa in {c["casa"] for c in crus}:
            termos[casa] = await dicionario.carregar(conn, casa)
    ultimo = {}
    for c in crus:
        ultimo[(c["dono"], c["casa"], c["parceiro"], c["codigo"])] = c
    tab = collections.defaultdict(collections.Counter)
    listas = collections.defaultdict(list)
    com_cru = collections.defaultdict(set)
    for (dono, casa, parceiro, cod), c in ultimo.items():
        if so and casa not in so:
            continue
        c["cru"] = json.loads(c["cru"])
        nome = nomes.get(casa, casa)
        com_cru[(dono, casa, nome)].add(cod)
        bs = bil.get((dono, nome, parceiro, cod), [])
        r = regua.comparar(c, bs)
        t = tab[casa]
        t["crus"] += 1
        if r["estado"] == "recusada":
            t["recusadas"] += 1
            listas[casa].append(("recusada", cod, r.get("motivos")))
            continue
        if r["estado"] == "sem bilhete":
            t["sem bilhete"] += 1
            continue
        t["comparadas"] += 1
        t["liquidadas"] += bool(r.get("liq"))
        if r["estado"] == "diverge" and all(
                d.startswith(("resultado F=", "retorno F=")) and (d.endswith("IA=-")
                                                                  or d.endswith("IA=None"))
                for d in r["dif"]):
            # A casa já liquidou e a linha da IA ainda está aberta: a próxima leitura do texto
            # a liquida. Explicada (é o tempo, não o número).
            t["IA ainda aberta"] += 1
        elif r["estado"] == "diverge":
            t["dinheiro"] += 1
            listas[casa].append(("diverge", cod, r.get("dif"), "PL", r.get("pl")))
        elif r["estado"] == "odd sem dinheiro":
            t["só odd"] += 1
        f, _ = ficha.montar_ficha(c["familia"], c["cru"], casa)
        esp, cat, faltam = dicionario.traduzir(f, termos[casa])
        if not faltam:
            t["traduzidas"] += 1
            b = bs[0]
            if esp == (b["esporte"] or "").strip() and cat == (b["aposta"] or "").strip():
                t["concordam"] += 1
            else:
                listas[casa].append(("dicionário", cod, f"F={esp} | {cat}",
                                     f"IA={b['esporte']} | {b['aposta']}"))
    for casa in sorted(tab):
        t = tab[casa]
        cob = []
        for (dono, k, nome), cods in sorted(com_cru.items()):
            if k == casa:
                cob.append(f"{dono} {len(cods)}/{no_banco.get((dono, nome), 0)}")
        print(f"{casa:11} comparadas {t['comparadas']:4} (liquidadas {t['liquidadas']}) · "
              f"dinheiro diverge {t['dinheiro']} · IA ainda aberta {t['IA ainda aberta']} · "
              f"só odd {t['só odd']} · recusadas "
              f"{t['recusadas']} · sem bilhete {t['sem bilhete']} · cobertura {', '.join(cob)} · "
              f"dicionário {t['traduzidas']}/{t['comparadas']} traduzidas, "
              f"{t['concordam']} iguais à IA")
    for casa in sorted(listas):
        for x in listas[casa]:
            print(" ", casa, *x)


if __name__ == "__main__":
    asyncio.run(main())
