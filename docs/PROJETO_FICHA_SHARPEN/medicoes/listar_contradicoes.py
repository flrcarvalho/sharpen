"""Lista as contradições de uma rodada da semente (`semente_log.contraditos`) por tipo, com os
votos, sem consertar nada (s415, T4: "o consultor revisa"). Só SELECT.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/listar_contradicoes.py [ID] [--md ARQUIVO]

Sem ID = a última rodada. A FORMA da divergência é um palpite para agrupar a leitura, não um
veredito: compara os valores tirando as marcas (`{ou}`, `{ent}`...).
  • objeto omitido   = um valor é o outro sem palavra(s) (`{ou}` × `{ou} Pontos`);
  • palavra trocada  = mesma forma, uma palavra diferente (`Rebotes` × `Rebounds` × `Ressaltos`);
  • só a seleção     = um valor é só a seleção e o outro diz o mercado (`{ent}` × `Ambas
                       Marcam - {ent}`);
  • outra            = o resto.
"""
import asyncio
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _env():
    for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith("DATABASE_URL=") and "DATABASE_URL" not in os.environ:
            os.environ["DATABASE_URL"] = l.split("=", 1)[1].strip().strip('"').strip("'")


def _palavras(v):
    return re.sub(r"\{[a-z0-9]+\}", " ", v).replace("-", " ").split()


def forma(tipo, votos: dict) -> str:
    if tipo != "descricao":
        return "decisão diferente"
    vs = list(votos)
    ps = [_palavras(v) for v in vs]
    if any(not p for p in ps) and any(p for p in ps):
        return "só a seleção" if all("{ent}" in v or "{time}" in v for v in vs) and \
            any(not p for p in ps) and not all("{ou}" in v for v in vs) else "objeto omitido"
    conj = [set(p) for p in ps]
    if any(a < b or b < a for i, a in enumerate(conj) for b in conj[i + 1:]):
        return "objeto omitido"
    esq = [re.sub(r"[^\s{}]+", "W", v) for v in vs]
    if len(set(len(p) for p in ps)) == 1 and len(set(esq)) == 1:
        return "palavra trocada"
    return "outra"


async def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(ROOT / "app"))
    _env()
    from database import get_pool
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    md = sys.argv[sys.argv.index("--md") + 1] if "--md" in sys.argv else ""
    if md in args:
        args.remove(md)
    pool = await get_pool()
    async with pool.acquire() as c:
        r = await c.fetchrow("SELECT * FROM semente_log WHERE id = $1", int(args[0])) if args \
            else await c.fetchrow("SELECT * FROM semente_log ORDER BY id DESC LIMIT 1")
    contra = json.loads(r["contraditos"])
    grupos = defaultdict(list)
    for x in contra:
        grupos[(x["tipo"], forma(x["tipo"], x["votos"]))].append(x)
    linhas = [f"# Contradições da semente (semente_log id {r['id']}, {str(r['criado_em'])[:19]} UTC, "
              f"gatilho {r['gatilho']})", "",
              f"{len(contra)} termos contraditos (nenhum voto com 90% ou mais). Nada aqui foi "
              "consertado: a aposta com esses termos vai para a IA até alguém decidir "
              "(`scripts/corrigir_termo.py`, D24).", ""]
    for (tipo, f), xs in sorted(grupos.items(), key=lambda g: (g[0][0], -len(g[1]))):
        linhas += [f"## {tipo} · {f} ({len(xs)})", "", "| casa | termo | votos |", "|---|---|---|"]
        for x in sorted(xs, key=lambda x: (x["casa"], x["termo"])):
            v = " · ".join(f"`{k}` {n}" for k, n in sorted(x["votos"].items(), key=lambda kv: -kv[1]))
            linhas.append(f"| {x['casa']} | `{x['termo']}` | {v} |")
        linhas.append("")
    out = "\n".join(linhas)
    if md:
        Path(md).write_text(out, encoding="utf-8", newline="\n")
        print(f"gravado em {md}")
    print(out)


if __name__ == "__main__":
    asyncio.run(main())
