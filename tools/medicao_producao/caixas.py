# SO LEITURA: estado da Caixa de cada conta ligada, pela funcao pura do servidor (_caixa_projetar).
import os
import asyncio, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app"))
from prodq import _url
import repository as R

async def main():
    import asyncpg
    conn = await asyncpg.connect(_url(), server_settings={"default_transaction_read_only": "on"}, timeout=30)
    try:
        async with conn.transaction(readonly=True):
            donos = [r["dono"] for r in await conn.fetch("SELECT DISTINCT dono FROM caixa_mov")]
            saida = []
            for dono in donos:
                parceiros = await conn.fetch("SELECT id, casa, nome, arquivado, moeda FROM parceiros WHERE dono = $1", dono)
                movs = {}
                for r in await conn.fetch("SELECT * FROM caixa_mov WHERE dono = $1 ORDER BY data, id", dono):
                    movs.setdefault(r["parceiro_id"], []).append(R._caixa_mov_dict(r))
                ap = {}
                for a in await conn.fetch("SELECT id, casa, parceiro, stake, odd, resultado, data, criado_em, stake_orig, moeda, "
                                          "cotacao, stake_freebet FROM bilhetes WHERE dono = $1", dono):
                    ap.setdefault((a["casa"], a["parceiro"]), []).append(dict(a))
                for p in parceiros:
                    if p["id"] not in movs: continue
                    moeda = R._moeda_conta(p)
                    res = R._caixa_projetar(movs[p["id"]], ap.get((p["casa"], p["nome"]), []), moeda, p["casa"])
                    ult_conf = max((m for m in movs[p["id"]] if m.get("tipo") == "conferencia"),
                                   key=lambda m: (m.get("criado_em") or "", m.get("id") or 0), default=None)
                    saida.append({"dono": dono, "casa": p["casa"], "parceiro": p["nome"], "arquivado": p["arquivado"],
                                  "moeda": moeda, "estado": res["estado"], "divergencia": res["divergencia"],
                                  "tolerancia": res.get("tolerancia"), "conf": res["conferencia"],
                                  "conf_em": (ult_conf or {}).get("criado_em"), "banca": res["banca"],
                                  "disponivel": res["disponivel"], "aberto": res["aberto"], "ligada": res["ligada"]})
    finally:
        await conn.close()
    json.dump(saida, open(sys.argv[1], "w", encoding="utf-8"), default=str, ensure_ascii=False, indent=0)
    import collections
    print(collections.Counter((s["estado"]) for s in saida))
    for s in sorted(saida, key=lambda s: (s["estado"], s["dono"])):
        if s["estado"] in ("divergente", "reconferir"):
            print(s["estado"], s["dono"], s["casa"], s["parceiro"], s["moeda"], "div", s["divergencia"],
                  "conf", (s["conf"] or {}).get("data"), "em", str(s["conf_em"])[:16], "arq" if s["arquivado"] else "")

asyncio.run(main())
