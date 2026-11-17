# SO LEITURA: baixa as apostas abertas e o cru mais recente de cada uma para JSON local.
import os
import asyncio, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prodq import _url

SQL = """
with ab as (
  select id, dono, casa, parceiro, data, stake, odd, resultado, extraction_state, codigo_bilhete,
         criado_em, atualizado_em, lido_em, origem
  from bilhetes where extraction_state = 'aberta' or coalesce(resultado,'') not in ('W','L','V','HW','HL')
)
select ab.*,
  (select row_to_json(c) from (
     select cc.id, cc.recebido_em, cc.casa casa_key, cc.familia, cc.versao_ext, cc.processado_em, cc.cru
     from captura_crua cc where cc.dono = ab.dono and cc.codigo = ab.codigo_bilhete
     order by cc.recebido_em desc limit 1) c) as cru_ult,
  (select row_to_json(v) from (select bv.casa, bv.atualizado_em from bloco_visto bv
     where bv.dono = ab.dono and bv.codigo = ab.codigo_bilhete order by bv.atualizado_em desc limit 1) v) as bloco,
  (select row_to_json(f) from (select fv.casa, fv.estado, fv.motivo, fv.atualizado_em, fv.pendente_desde, fv.aviso from ficha_virada fv
     where fv.dono = ab.dono and fv.codigo = ab.codigo_bilhete order by fv.atualizado_em desc limit 1) f) as virada
from ab
"""

async def main():
    import asyncpg
    conn = await asyncpg.connect(_url(), server_settings={"default_transaction_read_only": "on"}, timeout=30)
    try:
        async with conn.transaction(readonly=True):
            cols = {r["column_name"] for r in await conn.fetch(
                "select column_name from information_schema.columns where table_name='bilhetes'")}
            sql = SQL if "origem" in cols else SQL.replace(", origem\n", "\n")
            rows = await conn.fetch(sql)
    finally:
        await conn.close()
    out = []
    for r in rows:
        d = dict(r)
        for k in ("cru_ult", "bloco", "virada"):
            if d[k]: d[k] = json.loads(d[k])
        out.append(d)
    json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), default=str, ensure_ascii=False)
    print(len(out), "abertas;", sum(1 for d in out if d["cru_ult"]), "com cru;",
          sum(1 for d in out if d["bloco"]), "com bloco_visto;", sum(1 for d in out if d["virada"]), "com ficha_virada")

asyncio.run(main())
