"""Medição D1 (Projeto Ficha Sharpen): o excesso de escrita do Sonnet 5 é pensamento?

Dois regimes do MESMO modelo (claude-sonnet-5), mesmos lotes reais da DEX Sport
(sombra_rotulos), caminho de produção (build_system + _INSTRUCAO, 6 blocos por chamada):
  A = como a produção chama hoje (sem parâmetro de thinking)
  B = thinking desligado
Mede tokens, tipos de bloco da resposta e compara stake/odd/resultado com a régua
de números da s407 (sombra_numeros.comparar), bruto e depois do corrigir_stake_tsv.
Banco: só leitura.
"""
import asyncio, json, os, sys
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "app"))
for linha in open(os.path.join(RAIZ, ".env"), encoding="utf-8"):
    if "=" in linha:
        k, v = linha.strip().split("=", 1)
        if k and v:
            os.environ.setdefault(k, v.strip().strip('"'))

import asyncpg
from anthropic import AsyncAnthropic
import main as appmain
from prompts import build_system
from repository import corrigir_stake_tsv
from sombra_numeros import comparar

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODELO = "claude-sonnet-5"
CASA = "DEX Sport"
N_LOTES = int(os.environ.get("N_LOTES", "5"))
POR_CHUNK = 6
PARCEIRO = "Feca [Eu]"
PRECO = (2.0, 10.0, 0.20, 4.00)   # in, out, cache read, cache write (1h) por MTok
cli = AsyncAnthropic()
OUT = os.environ.get("OUT_DIR", __import__("tempfile").gettempdir())   # a saída tem bilhetes reais: fora do repo


async def lotes():
    c = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
    rows = await c.fetch("""SELECT dono, criado_em, codigo, bruto FROM sombra_rotulos
                             WHERE casa=$1 AND codigo <> '' AND criado_em >= '2026-10-01'
                             ORDER BY criado_em DESC, id""", CASA)
    await c.close()
    por = defaultdict(list)
    for r in rows:
        por[(r["dono"], r["criado_em"])].append((r["codigo"], r["bruto"]))
    out = []
    for g in sorted(por.values(), key=len, reverse=True):
        vistos, limpo = set(), []
        for cod, b in g:
            if cod not in vistos:
                vistos.add(cod); limpo.append((cod, b))
        for i in range(0, len(limpo) - POR_CHUNK + 1, POR_CHUNK):
            if len(out) < N_LOTES:
                out.append(limpo[i:i + POR_CHUNK])
    return out


async def chamar(texto, regime):
    system = build_system(appmain._display_to_key(CASA))
    instr = {"type": "text", "text": appmain._INSTRUCAO.format(
        casa=CASA, parceiro=PARCEIRO, data_referencia="11/10/2026")}
    kw = {}
    if regime == "B":
        kw["thinking"] = {"type": "disabled"}
    async with cli.messages.stream(model=MODELO, max_tokens=64000, system=system,
                                   messages=[{"role": "user", "content": [
                                       {"type": "text", "text": texto}, instr]}], **kw) as st:
        fin = await st.get_final_message()
    u = fin.usage
    tk = {"i": u.input_tokens, "o": u.output_tokens,
          "cr": u.cache_read_input_tokens or 0, "cw": u.cache_creation_input_tokens or 0}
    tipos = [b.type for b in fin.content]
    pens = sum(len(getattr(b, "thinking", "") or "") for b in fin.content if b.type == "thinking")
    txt = "".join(b.text for b in fin.content if b.type == "text")
    return txt, tk, tipos, fin.stop_reason, pens


def custo(tk):
    pi, po, pr, pw = PRECO
    return (tk["i"] * pi + tk["o"] * po + tk["cr"] * pr + tk["cw"] * pw) / 1e6


async def main():
    ls = await lotes()
    print(f"{len(ls)} lotes de {POR_CHUNK} blocos da {CASA}", flush=True)
    textos = ["\n\n".join("[C\u00f3digo: %s]\n%s" % (c, b) for c, b in l) for l in ls]
    res = {"A": [None] * len(ls), "B": [None] * len(ls)}
    # 1ª chamada sozinha: escreve o cache do manual, as outras leem.
    res["A"][0] = await chamar(textos[0], "A")
    jobs = [(r, i) for r in "AB" for i in range(len(ls)) if not (r == "A" and i == 0)]
    feitos = await asyncio.gather(*(chamar(textos[i], r) for r, i in jobs))
    for (r, i), x in zip(jobs, feitos):
        res[r][i] = x

    tot = {"A": defaultdict(float), "B": defaultdict(float)}
    resumo_bruto, resumo_final = defaultdict(int), defaultdict(int)
    divergencias = []
    for i, texto in enumerate(textos):
        for r in "AB":
            txt, tk, tipos, stop, pens = res[r][i]
            for k, v in tk.items():
                tot[r][k] += v
            tot[r]["usd"] += custo(tk)
            tot[r]["chars_pensamento"] += pens
            tot[r]["com_bloco_thinking"] += ("thinking" in tipos) or ("redacted_thinking" in tipos)
            print(f"lote {i} {r}: out={tk['o']:>6} tipos={tipos} stop={stop} pensamento={pens} chars")
        ta = "\n".join(appmain._extract_tsv_rows(res["A"][i][0]))
        tb = "\n".join(appmain._extract_tsv_rows(res["B"][i][0]))
        fa, _ = corrigir_stake_tsv(ta, texto)
        fb, _ = corrigir_stake_tsv(tb, texto)
        cmp_ = comparar(ta, fa, tb, fb, texto)
        cmp_b = comparar(ta, ta, tb, tb, texto)
        for k, v in cmp_["resumo"].items():
            resumo_final[k] += v
        for k, v in cmp_b["resumo"].items():
            resumo_bruto[k] += v
        for l in cmp_["linhas"]:
            if l["faltou"] or l["sobrou"] or l["inventado"] or not all(l[f"igual_{c}"] for c in ("stake", "odd", "res")):
                divergencias.append({"lote": i, **l})

    n = len(ls)
    print("\n=== por chamada (média) ===")
    for r in "AB":
        t = tot[r]
        print(f"{r}: saída {t['o']/n:,.0f} tok · entrada {t['i']/n:,.0f} · cache lido {t['cr']/n:,.0f}"
              f" · cache escrito {t['cw']/n:,.0f} · US$ {t['usd']/n:.4f}/chamada"
              f" · respostas com bloco de pensamento {int(t['com_bloco_thinking'])}/{n}")
    print("\n=== números, A (hoje) × B (sem pensamento) ===")
    print("bruto:", dict(resumo_bruto))
    print("final (após corrigir_stake_tsv):", dict(resumo_final))
    print("divergências:", len(divergencias))
    for d in divergencias:
        print(json.dumps(d, ensure_ascii=False))
    json.dump({"tot": tot, "bruto": resumo_bruto, "final": resumo_final, "div": divergencias,
               "saidas": {r: [x[0] for x in res[r]] for r in "AB"}, "textos": textos},
              open(os.path.join(OUT, "medir_pensamento.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, default=float)


asyncio.run(main())
