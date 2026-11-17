import os
import asyncio, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prodq import _url
SQL = """
select fv.dono, fv.casa, fv.codigo, fv.estado, fv.motivo, fv.aviso, fv.atualizado_em,
  (select row_to_json(c) from (select cc.id, cc.recebido_em, cc.casa casa_key, cc.parceiro, cc.familia, cc.versao_ext, cc.cru
     from captura_crua cc where cc.dono=fv.dono and cc.casa=fv.casa and cc.codigo=fv.codigo order by cc.recebido_em desc limit 1) c) cru_ult,
  exists(select 1 from lixeira_bilhetes l where l.dono=fv.dono and l.snapshot->>'codigo_bilhete'=fv.codigo) na_lixeira
from ficha_virada fv
where not exists (select 1 from bilhetes b where b.dono=fv.dono and b.codigo_bilhete=fv.codigo)
"""
async def main():
    import asyncpg
    conn = await asyncpg.connect(_url(), server_settings={"default_transaction_read_only": "on"}, timeout=30)
    try:
        async with conn.transaction(readonly=True):
            cols = [r[0] for r in await conn.fetch("select column_name from information_schema.columns where table_name='lixeira_bilhetes'")]
            print("lixeira cols:", cols)
            sql = SQL
            if "snapshot" not in cols:
                sql = SQL.replace("l.snapshot->>'codigo_bilhete'", "l.%s->>'codigo_bilhete'" % next(c for c in cols if c in ("dados","linha","bilhete","snap")))
            rows = await conn.fetch(sql)
    finally:
        await conn.close()
    out = []
    for r in rows:
        d = dict(r); d["cru_ult"] = json.loads(d["cru_ult"]) if d["cru_ult"] else None; out.append(d)
    json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), default=str, ensure_ascii=False)
    print(len(out), "codigos da ficha_virada sem linha;", sum(1 for d in out if d["na_lixeira"]), "na lixeira")
asyncio.run(main())
