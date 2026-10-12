"""Régua Ficha × IA sobre o cru guardado (s409): o adaptador monta a Ficha de cada linha de
`captura_crua`, offline, e compara com o bilhete que a IA gravou para o MESMO código na
MESMA conta: stake, odd, resultado, retorno e freebet. Banco: só SELECT. Sem IA, sem custo.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_regua_adaptadores.py [familia]

Estados por cru:
  bate              os cinco campos iguais (stake e retorno no centavo; odd idêntica)
  odd sem dinheiro  só a odd difere, e o P/L das duas leituras difere menos de 0,01
  diverge           qualquer outra diferença (o P/L de cada lado sai na coluna PL)
  recusada          o adaptador ou a validação recusou (motivo ao lado)
  sem bilhete       a IA não gravou bilhete com aquele código naquela conta

P/L em moeda da CONTA (stake_orig quando a conta não é em real). Retorno da IA derivado
de stake × odd pela fórmula do resultado, como o `calcular_pl`.

Liquidadas comparadas (D12, decisão do Feca de 11/10: a casa só vira com 30 por casa):
aposta (código distinto) em que a Ficha E a IA têm resultado liquidado (W, L, V, HW, HL).
Aberta de qualquer lado não conta. Sai por casa e por DONO (Feca e Gabriel separados,
sempre listados, mesmo sem cru), com quantas delas batem, só a odd ou divergem.
"""
import asyncio
import collections
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "app"))

import ficha  # noqa: E402
from database import get_pool  # noqa: E402

C = Decimal("0.005")
LIQUIDADO = {"W", "L", "V", "HW", "HL"}
DONOS_SEMPRE = ("Feca", "Gabriel")   # D12 conta por dono; quem não mandou cru aparece com 0
VIRADA = 30


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def br(v):
    if v in (None, ""):
        return None
    s = str(v).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return Decimal(s)


def retorno(res, stake, odd):
    if stake is None:
        return None
    if res == "W":
        return stake * odd if odd is not None else None
    if res == "HW":
        return (stake / 2) * odd + stake / 2 if odd is not None else None
    return {"L": Decimal(0), "V": stake, "HL": stake / 2 if stake else None}.get(res)


def comparar(c: dict, bilhetes: list) -> dict:
    r = {"casa": c["casa"], "familia": c["familia"], "codigo": c["codigo"], "dono": c["dono"]}
    f, motivos = ficha.montar_ficha(c["familia"], c["cru"], c["casa"])
    if f is None:
        return dict(r, estado="sem adaptador")
    if motivos:
        return dict(r, estado="recusada", motivos=motivos)
    d = ficha.derivar(f)
    if not bilhetes:
        return dict(r, estado="sem bilhete")
    b = bilhetes[0]
    s_ia = br(b["stake_orig"]) if b["stake_orig"] is not None else br(b["stake"])
    o_ia, res_ia = br(b["odd"]), (b["resultado"] or "").strip()
    s_f, o_f = br(d["stake"]), br(d["odd"])
    ret_f = Decimal(f["retorno"]) if f.get("retorno") and d["resultado"] else None
    ret_ia = retorno(res_ia, s_ia, o_ia)
    dif = []
    if s_f is None or s_ia is None or abs(s_f - s_ia) > C:   # Shuffle: 59,56171948 × IA 59,56
        dif.append(f"stake F={s_f} IA={s_ia}")
    if o_f != o_ia:
        dif.append(f"odd F={o_f} IA={o_ia}")
    fb_f = Decimal(f["stake_freebet"]) if f.get("stake_freebet") else None
    fb_ia = br(b["stake_freebet"]) if b["stake_freebet"] not in (None, "", "0", "0.00") else None
    if fb_f != fb_ia and not (fb_f is not None and fb_ia is not None and abs(fb_f - fb_ia) <= C):
        dif.append(f"freebet F={fb_f} IA={fb_ia}")
    if d["resultado"] != res_ia:
        dif.append(f"resultado F={d['resultado'] or '-'} IA={res_ia or '-'}")
    if (ret_f is None) != (ret_ia is None) or (ret_f is not None and abs(ret_f - ret_ia) > C):
        dif.append(f"retorno F={ret_f} IA={ret_ia if ret_ia is None else round(ret_ia, 4)}")
    pl_f, pl_ia = retorno(d["resultado"], s_f, o_f), retorno(res_ia, s_ia, o_ia)
    pl = None if pl_f is None or pl_ia is None else (pl_f - s_f) - (pl_ia - s_ia)
    so_odd = bool(dif) and all(x.startswith("odd") for x in dif)
    estado = ("bate" if not dif else
              "odd sem dinheiro" if so_odd and (pl is None or abs(pl) < Decimal("0.01")) else
              "diverge")
    liq = d["resultado"] in LIQUIDADO and res_ia in LIQUIDADO
    return dict(r, estado=estado, dif=dif, status=f["status"], fonte_odd=d["fonte_odd"], liq=liq,
                stake_pedida=f.get("stake_pedida"),
                pl=None if pl is None else str(round(pl, 4)), n_bilhetes=len(bilhetes))


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    so = sys.argv[1] if len(sys.argv) > 1 else None
    pool = await get_pool()
    async with pool.acquire() as conn:
        crus = [dict(r) for r in await conn.fetch(
            "SELECT id, familia, casa, dono, parceiro, codigo, cru::text AS cru "
            "FROM captura_crua WHERE ($1::text IS NULL OR familia = $1) ORDER BY id", so)]
        # casa da Ficha (chave) → casa gravada em `bilhetes` (nome de exibição)
        nomes = {r["k"]: r["casa"] for r in await conn.fetch(
            "SELECT DISTINCT upper(replace(casa, ' ', '')) AS k, casa FROM bilhetes")}
        bil = collections.defaultdict(list)
        for b in await conn.fetch(
                "SELECT dono, casa, parceiro, codigo_bilhete, stake, odd, resultado, "
                "stake_orig::text, stake_freebet::text FROM bilhetes "
                "WHERE codigo_bilhete = ANY($1::text[])", [c["codigo"] for c in crus]):
            bil[(b["dono"], b["casa"], b["parceiro"], b["codigo_bilhete"])].append(dict(b))
    linhas = []
    for c in crus:
        c["cru"] = json.loads(c["cru"])
        chave = (c["dono"], nomes.get(c["casa"], c["casa"]), c["parceiro"], c["codigo"])
        linhas.append(comparar(c, bil.get(chave, [])))
    tab = collections.defaultdict(collections.Counter)
    for r in linhas:
        tab[r["casa"]][r["estado"]] += 1
    for casa, cnt in sorted(tab.items()):
        print(f"{casa:10} {sum(cnt.values()):4} crus · " +
              " · ".join(f"{k} {v}" for k, v in sorted(cnt.items())))
    # liquidadas comparadas por casa × dono, contando a APOSTA (código), não o cru
    liq = collections.defaultdict(dict)
    for r in linhas:
        if r.get("liq"):
            liq[(r["casa"], r["dono"])][r["codigo"]] = r["estado"]
    donos = sorted({r["dono"] for r in linhas} | set(DONOS_SEMPRE))
    print()
    print(f"Liquidadas comparadas (virada: {VIRADA} por casa, aberta não conta)")
    for casa in sorted(tab):
        total = 0
        for dono in donos:
            est = collections.Counter(liq.get((casa, dono), {}).values())
            n = sum(est.values())
            total += n
            print(f"{casa:10} {dono:10} {n:4} liquidadas · bate {est['bate']} · "
                  f"odd sem dinheiro {est['odd sem dinheiro']} · diverge {est['diverge']}")
        # o número só diz se a casa ATINGE o piso; a virada continua sendo o "pode" do Feca
        print(f"{casa:10} {'casa':10} {total:4} liquidadas · "
              + (f"atinge {VIRADA}" if total >= VIRADA else f"faltam {VIRADA - total}"))
    for r in linhas:
        if r["estado"] in ("diverge", "recusada", "sem bilhete") or r.get("stake_pedida"):
            print(" ", r["casa"], r["codigo"], r["estado"], r.get("dif") or r.get("motivos") or "",
                  "PL", r.get("pl"), r.get("fonte_odd") or "",
                  f"pedida {r['stake_pedida']}" if r.get("stake_pedida") else "")


if __name__ == "__main__":
    asyncio.run(main())
