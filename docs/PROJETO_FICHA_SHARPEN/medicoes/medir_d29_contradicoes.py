"""s416 (D29): a contradição de DESCRIÇÃO decidida por regra. Só SELECT.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_d29_contradicoes.py [ID] [--s414 DIR] [--s415 DIR]

1. Roda `descricao_ficha.decidir` sobre os votos dos termos de descrição contraditos do
   `semente_log` ID (padrão 17, os 46 de `contradicoes_semente_17.md`) e conta por regra (a, b,
   c, unico = o estilo juntou tudo, e = a mais votada, e-empate = empate exato no topo; os
   dois `e` vão para a revisão).
2. Com `--s414 DIR --s415 DIR` (cópias de `descricao_ficha.py` e `dicionario.py` daquelas
   versões): as pernas que tinham cada uma das chaves na s414 (a versão da semente 17), as
   chaves que elas têm hoje, e a situação de cada uma na s415 (maioria de 90%) e com `app/`
   (D29). `*` marca os casos da Megapari com `{t1}`/`{t2}` ou `{n1}`/`{n2}` nos votos (o
   conserto do `Individual Total 1/2` e do handicap, s415).
3. A semente inteira de hoje com `app/`: quantos termos de descrição vão para a revisão.
"""
import argparse
import asyncio
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _env():
    for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith("DATABASE_URL=") and "DATABASE_URL" not in os.environ:
            os.environ["DATABASE_URL"] = l.split("=", 1)[1].strip().strip('"').strip("'")


def _carregar(pasta, sufixo):
    """`descricao_ficha` e `dicionario` de uma pasta (o `dicionario` importa o
    `descricao_ficha` pelo nome, dentro das funções: quem chama acerta o `sys.modules`)."""
    mods = {}
    for nome in ("descricao_ficha", "dicionario"):
        spec = importlib.util.spec_from_file_location(f"{nome}_{sufixo}",
                                                      Path(pasta) / f"{nome}.py")
        mods[nome] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mods[nome])
    return mods["descricao_ficha"], mods["dicionario"]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id", nargs="?", type=int, default=17)
    ap.add_argument("--s414", default="")
    ap.add_argument("--s415", default="")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(ROOT / "app"))
    _env()
    from database import get_pool
    import descricao_ficha as D
    import dicionario as DIC
    pool = await get_pool()
    async with pool.acquire() as c:
        r = await c.fetchrow("SELECT criado_em, contraditos FROM semente_log WHERE id = $1", a.id)
        contra = [x for x in json.loads(r["contraditos"]) if x["tipo"] == "descricao"]
        pares, texto, _ = await DIC.pares(c)
    print(f"semente_log {a.id} ({r['criado_em']:%d/%m %H:%M} UTC): {len(contra)} contradições de "
          f"descrição, decididas pelo D29 com os votos daquela rodada")
    por = Counter()
    for x in contra:
        v, regra = D.decidir(x["termo"], x["votos"])
        por[regra] += 1
        print(f"  [{regra}] {x['casa']} {x['termo']} → {v}")
    print("por regra:", dict(por), f"· sobram em revisão: {por['e'] + por['e-empate']}")

    if a.s414 and a.s415:
        mega = {(x["casa"], x["termo"]) for x in contra if x["casa"] == "MEGAPARI"
                and any(re.search(r"\{t[12]\}|\{n[12]\}", v) for v in x["votos"])}
        print(f"\nAs {len(contra)} nas chaves de hoje (* = Megapari com {{t1}}/{{t2}} ou "
              f"{{n1}}/{{n2}} nos votos: {len(mega)})")
        D14, _ = _carregar(a.s414, "s414")
        D15, DIC15 = _carregar(a.s415, "s415")
        alvo = {(x["casa"], x["termo"]) for x in contra}
        novas = defaultdict(set)
        for casa, f, *_ in pares:
            for p in f.get("pernas") or []:
                k14 = D14.chave(p)
                if (casa, k14) in alvo:
                    d15 = D15.decompor(p)
                    novas[(casa, k14)].add(D15.chave(p, d15, jogador=bool(d15["jogador"])))
        sys.modules["descricao_ficha"] = D15
        u15, c15, _ = DIC15.votar(pares)
        sys.modules["descricao_ficha"] = D
        u16, _, rev16 = DIC.votar(pares)
        rv16 = {(x["casa"], x["termo"]): x for x in rev16 if x["tipo"] == "descricao"}
        conta, vistas = Counter(), set()
        for casa, k14 in sorted(alvo):
            print(f"  {'*' if (casa, k14) in mega else ' '} {casa} {k14}")
            if not novas.get((casa, k14)):
                print("       → (nenhuma perna com essa chave no par cru × IA de hoje)")
            for k in sorted(novas.get((casa, k14), ())):
                kk = (casa, "descricao", k)
                s15 = ("contradita" if kk in c15 else f"resolvida → {u15[kk][0]}" if kk in u15
                       else "sem voto")
                rv = rv16.get((casa, k))
                s16 = (u16[kk][0] + (" (revisão, empate)" if rv and rv.get("empate") else
                                     " (revisão)" if rv else "") if kk in u16 else "sem voto")
                if (casa, k) not in vistas:
                    vistas.add((casa, k))
                    conta["s415 " + s15.split(" ")[0]] += 1
                    conta["D29 " + ("revisão" if rv else "decidida" if kk in u16
                                    else "sem voto")] += 1
                print(f"       → {k}\n           s415: {s15}\n           D29:  {s16}")
        print("chaves de hoje vindas das 46:", dict(conta))

    u, cc, rev = DIC.votar(pares, texto)
    rd = [x for x in rev if x["tipo"] == "descricao"]
    print(f"\nsemente de hoje (app/): {sum(1 for k in u if k[1] == 'descricao')} termos de "
          f"descrição, {sum(1 for k in cc if k[1] == 'descricao')} contraditos, {len(rd)} na "
          f"revisão ({sum(1 for x in rd if x.get('empate'))} por empate exato)")
    for x in sorted(rd, key=lambda x: (not x.get("empate"), x["casa"], x["termo"])):
        print(f"  {'EMPATE ' if x.get('empate') else ''}{x['casa']} {x['termo']} → {x['fica']}  "
              f"{x['votos']}")


if __name__ == "__main__":
    asyncio.run(main())
