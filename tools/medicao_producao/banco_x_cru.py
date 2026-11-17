# SO LEITURA: compara cada aposta do banco com o cru mais recente da casa (adaptador do servidor).
# Uso: python banco_x_cru.py dono "Casa" "parceiro" [CASA_KEY]
import os
import asyncio, json, sys, collections
from decimal import Decimal as D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app"))
from prodq import _url
import ficha

def n(s):
    s = str(s or "").strip()
    if not s: return None
    if "," in s: s = s.replace(".", "").replace(",", ".")
    try: return D(s)
    except Exception: return None

def pl(res, st, od):
    if st is None: return D(0)
    if res == "W": return st * ((od or D(1)) - 1)
    if res == "L": return -st
    if res == "HW": return st / 2 * ((od or D(1)) - 1)
    if res == "HL": return -st / 2
    return D(0)

async def main(dono, casa, parceiro):
    import asyncpg
    conn = await asyncpg.connect(_url(), server_settings={"default_transaction_read_only": "on"}, timeout=30)
    async with conn.transaction(readonly=True):
        bs = await conn.fetch("select id, codigo_bilhete, data, stake, stake_orig, odd, resultado, extraction_state, origem, moeda, criado_em "
                              "from bilhetes where dono=$1 and casa=$2 and parceiro=$3", dono, casa, parceiro)
        crus = await conn.fetch("select distinct on (codigo) codigo, familia, casa, cru, recebido_em from captura_crua "
                                "where dono=$1 and parceiro=$2 order by codigo, recebido_em desc", dono, parceiro)
    await conn.close()
    cru = {c["codigo"]: c for c in crus}
    out = collections.Counter(); difs = []
    pl_banco = pl_cru = D(0)
    cods = collections.Counter(b["codigo_bilhete"] for b in bs)
    for b in bs:
        st = n(b["stake_orig"]) or n(b["stake"]); od = n(b["odd"])
        pb = pl(b["resultado"], st, od); pl_banco += pb
        c = cru.get(b["codigo_bilhete"])
        if cods[b["codigo_bilhete"]] > 1: out["codigo_duplicado"] += 1
        if not c: out["sem_cru"] += 1; pl_cru += pb; continue
        f, m = ficha.montar_ficha(c["familia"], json.loads(c["cru"]) if isinstance(c["cru"], str) else c["cru"], c["casa"])
        if f is None or f.get("cru_recusado"):
            out["cru_recusado"] += 1; pl_cru += pb; continue
        try: d = ficha.derivar(f)
        except ValueError: out["status?"] += 1; pl_cru += pb; continue
        sc, oc = n(d["stake"]), n(d["odd"])
        pc = pl(d["resultado"], sc, oc); pl_cru += pc
        k = []
        if (b["resultado"] or "") != d["resultado"]: k.append("resultado")
        if sc is not None and st is not None and abs(sc - st) > D("0.01"): k.append("stake")
        if oc is not None and od is not None and abs(oc - od) > D("0.01") and d["resultado"] in ("W", "HW"): k.append("odd")
        out["+".join(k) or "igual"] += 1
        if k: difs.append((b["id"], b["codigo_bilhete"], b["data"], str(st), b["odd"], b["resultado"] or "-", d["stake"], d["odd"], d["resultado"] or "-", str(round(pc - pb, 2))))
    print(dono, casa, parceiro, "apostas", len(bs), dict(out))
    print("P/L banco", round(pl_banco, 2), "| P/L pelo cru", round(pl_cru, 2), "| diferenca", round(pl_cru - pl_banco, 2))
    for x in sorted(difs, key=lambda x: -abs(D(x[-1])))[:25]: print("  ", *x)

asyncio.run(main(*sys.argv[1:4]))
