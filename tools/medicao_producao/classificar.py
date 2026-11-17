# Classifica as abertas pelo cru mais recente, usando os adaptadores e o derivar() DO SERVIDOR.
import os
import json, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "app"))
import ficha

dados = json.load(open(sys.argv[1], encoding="utf-8"))
res = []
for d in dados:
    c = d["cru_ult"]
    item = {k: d[k] for k in ("id", "dono", "casa", "parceiro", "codigo_bilhete", "stake", "odd", "data",
                              "resultado", "atualizado_em", "lido_em", "origem")}
    item["virada"] = d["virada"]
    if not c:
        item["veredito"] = "sem_cru"; res.append(item); continue
    item.update(cru_em=c["recebido_em"], familia=c["familia"], casa_key=c["casa_key"],
                versao_ext=c["versao_ext"], processado_em=c["processado_em"])
    f, motivos = ficha.montar_ficha(c["familia"], c["cru"], c["casa_key"])
    if f is None:
        item["veredito"] = "sem_adaptador"
    elif f.get("cru_recusado"):
        item["veredito"] = "cru_recusado"; item["motivos"] = motivos
    else:
        st = f.get("status")
        try:
            der = ficha.derivar(f)
            item["cru_resultado"] = der["resultado"]; item["cru_odd"] = der["odd"]
            item["cru_stake"] = der["stake"]; item["cru_data"] = der["data"]
            # derivar() devolve resultado "" para status `aberta`: aberta na casa também.
            base = "LIQUIDADA_NO_CRU" if der["resultado"] else "aberta_no_cru"
            item["veredito"] = base + ("" if not motivos else "_ficha_invalida")
            item["motivos"] = motivos
        except ValueError:
            item["veredito"] = f"aberta_no_cru({st})"; item["motivos"] = motivos
    res.append(item)

json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), default=str, ensure_ascii=False, indent=0)
cont = collections.Counter(r["veredito"] for r in res)
print(cont)
liq = [r for r in res if r["veredito"].startswith("LIQUIDADA")]
por = collections.Counter((r["dono"], r["casa"], r["veredito"]) for r in liq)
for k, v in sorted(por.items(), key=lambda x: -x[1]): print(v, *k)
