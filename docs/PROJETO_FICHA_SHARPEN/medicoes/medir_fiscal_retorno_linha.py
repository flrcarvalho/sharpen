"""O que o fiscal passa a mexer quando lê a linha `Retorno:` (s409)? Replay, só leitura.

Para cada aposta resolvida dos últimos 60 dias cujo bloco cru (o mais recente na
`sombra_rotulos`) tem `Retorno:` no início de linha, monta a linha TSV como está gravada e
passa pelo `corrigir_stake_tsv` de ANTES (backup) e de AGORA. Conta, por casa, onde o
resultado ou a odd sairiam diferentes e quanto o P/L mudaria. A stake é a gravada; onde o
bloco está em outra moeda, os dois lados trocam a stake igual e a comparação segue valendo.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_fiscal_retorno_linha.py
"""
import asyncio, importlib.util, os, sys
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RAIZ, "app"))
for linha in open(os.path.join(RAIZ, ".env"), encoding="utf-8"):
    if "=" in linha:
        k, v = linha.strip().split("=", 1)
        if k and v:
            os.environ.setdefault(k, v.strip().strip('"'))

import asyncpg
import repository as R

_spec = importlib.util.spec_from_file_location(
    "repo_antigo", os.path.join(RAIZ, "Backups", "s409b_fiscal_retorno_e_aquecedor", "app", "repository.py"))
R0 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(R0)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
    await c.execute("SET default_transaction_read_only = on")
    rows = await c.fetch(r"""
        WITH ult AS (
          SELECT DISTINCT ON (dono, casa, codigo) dono, casa, codigo, bruto
            FROM sombra_rotulos
           WHERE codigo <> '' AND criado_em >= now() - interval '60 days'
           ORDER BY dono, casa, codigo, criado_em DESC, id DESC)
        SELECT b.id, b.dono, b.casa, b.data, b.esporte, b.parceiro, b.aposta, b.descricao,
               b.stake, b.odd, b.resultado, b.codigo_bilhete, u.bruto
          FROM bilhetes b JOIN ult u
            ON u.dono = b.dono AND u.casa = b.casa AND u.codigo = b.codigo_bilhete
         WHERE b.resultado IN ('W', 'L', 'V', 'HW', 'HL') AND u.bruto ~ '(?n)^Retorno:'""")
    await c.close()
    por_casa = defaultdict(Counter)
    dpl = defaultdict(float)
    exemplos = defaultdict(list)
    for r in rows:
        cols = [r["data"] or "", r["esporte"] or "", "", r["casa"], r["parceiro"] or "",
                r["aposta"] or "", (r["descricao"] or "").replace("\t", " "),
                r["stake"] or "", r["odd"] or "", r["resultado"], r["codigo_bilhete"]]
        tsv = "\t".join(cols)
        texto = f"[Código: {r['codigo_bilhete']}]\n{r['bruto']}"
        velho, _ = R0.corrigir_stake_tsv(tsv, texto)
        novo, info = R.corrigir_stake_tsv(tsv, texto)
        t = por_casa[r["casa"]]
        t["resolvidas"] += 1
        if velho == novo:
            continue
        pv, pn = velho.split("\t"), novo.split("\t")
        t["mudaria"] += 1
        t[f"{pv[9]}→{pn[9]}" if pv[9] != pn[9] else "só a odd"] += 1
        a = R.calcular_pl(pv[7], pv[8], pv[9]); b = R.calcular_pl(pn[7], pn[8], pn[9])
        if a is not None and b is not None:
            dpl[r["casa"]] += b - a
        if len(exemplos[r["casa"]]) < 4:
            exemplos[r["casa"]].append((r["id"], pv[7], pv[8], pv[9], "→", pn[8], pn[9],
                                        [l for l in r["bruto"].splitlines()
                                         if l.startswith(("Status:", "Retorno:", "Odd"))]))
    print(f"{len(rows)} apostas resolvidas com `Retorno:` em linha própria (60 dias)\n")
    for casa in sorted(por_casa, key=lambda k: -por_casa[k]["mudaria"]):
        t = por_casa[casa]
        extra = {k: v for k, v in t.items() if k not in ("resolvidas", "mudaria")}
        print(f"{casa:<16} resolvidas {t['resolvidas']:>5} · mudaria {t['mudaria']:>4} · "
              f"Δ P/L {dpl[casa]:>10.2f} · {extra}")
    print()
    for casa, ex in exemplos.items():
        print(casa)
        for e in ex:
            print("   ", e)


asyncio.run(main())
