"""Quantas apostas JÁ GRAVADAS caíram no furo da folga de 0,005 da odd (s409)?

Para cada bilhete W/HW resolvido que tem bloco cru na `sombra_rotulos` (o mais recente
daquele dono+casa+código), roda o `_veredito_do_retorno` de HOJE com a odd gravada e
conta onde a versão NOVA decide diferente da ANTIGA (backup) e o P/L muda ≥ R$ 0,01 —
exatamente a porta que o conserto abriu. Stake = a do bloco, como no fiscal. Banco: só leitura.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_furo_folga_odd.py
"""
import asyncio, os, sys
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RAIZ, "app"))
for linha in open(os.path.join(RAIZ, ".env"), encoding="utf-8"):
    if "=" in linha:
        k, v = linha.strip().split("=", 1)
        if k and v:
            os.environ.setdefault(k, v.strip().strip('"'))

import importlib.util
import asyncpg
import repository as R

# A versão de ANTES do conserto (backup da s409), para comparar as duas lado a lado.
_spec = importlib.util.spec_from_file_location(
    "repo_antigo", os.path.join(RAIZ, "Backups", "s409_fiscal_odd_fecha_no_centavo", "app", "repository.py"))
R0 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(R0)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
    await c.execute("SET default_transaction_read_only = on")
    rows = await c.fetch("""
        WITH ult AS (
          SELECT DISTINCT ON (dono, casa, codigo) dono, casa, codigo, bruto
            FROM sombra_rotulos WHERE codigo <> ''
           ORDER BY dono, casa, codigo, criado_em DESC, id DESC)
        SELECT b.id, b.dono, b.casa, b.codigo_bilhete, b.stake, b.odd, b.resultado,
               b.descricao, b.data, u.bruto
          FROM bilhetes b JOIN ult u
            ON u.dono = b.dono AND u.casa = b.casa AND u.codigo = b.codigo_bilhete
         WHERE b.resultado IN ('W', 'HW')""")
    await c.close()
    print(f"{len(rows)} bilhetes W/HW com bloco cru na sombra")
    furo, por_casa, exemplos, total_pl, pulou_moeda = 0, Counter(), [], 0.0, 0
    bruto_pl, maior, por_mes = 0.0, 0.0, Counter()
    for r in rows:
        texto = f"[Código: {r['codigo_bilhete']}]\n{r['bruto']}"
        info = R._financeiro_do_texto(texto).get(r["codigo_bilhete"])
        if not info or info.get("sistema") or not info.get("odd_total"):
            continue
        # A stake é a do BLOCO, como no fiscal. Onde ela difere da gravada (moeda convertida,
        # edição manual) o retorno do bloco não fala a língua da linha: fica de fora.
        stake = R._num_bloco(info["stake"]); odd = R._num_or_none(r["odd"])
        if not stake or stake <= 0 or not odd:
            continue
        if abs(stake - (R._num_or_none(r["stake"]) or 0)) > 0.005:
            pulou_moeda += 1
            continue
        retorno = R._retorno_do_bloco(info, stake)
        if retorno is None:
            continue
        args = (stake, odd, retorno, r["descricao"] or "", info["odd_total"])
        res, odd_nova = R._veredito_do_retorno(*args)
        if (res, odd_nova) == R0._veredito_do_retorno(*args) or not odd_nova:
            continue
        pl_g = R.calcular_pl(r["stake"], r["odd"], r["resultado"])
        pl_n = R.calcular_pl(r["stake"], odd_nova, res)
        if pl_g is None or pl_n is None or abs(pl_n - pl_g) < 0.01:
            continue
        furo += 1
        por_casa[(r["dono"], r["casa"])] += 1
        total_pl += pl_n - pl_g
        bruto_pl += abs(pl_n - pl_g); maior = max(maior, abs(pl_n - pl_g))
        por_mes[str(r['data'] or '')[-7:] if '/' in str(r['data'] or '') else str(r['data'] or '')[:7]] += 1
        if len(exemplos) < 15:
            exemplos.append((r["id"], r["dono"], r["casa"], r["stake"], r["odd"], odd_nova,
                             r["resultado"], res, round(pl_n - pl_g, 2)))
    print(f"fora por stake do bloco != gravada (moeda/edição): {pulou_moeda}")
    print(f"no furo: {furo} · soma da diferença de P/L: R$ {total_pl:.2f}")
    print(f"soma em módulo: R$ {bruto_pl:.2f} · maior diferença numa aposta: R$ {maior:.2f}")
    print("por mês do evento:", sorted(por_mes.items()))
    for k, v in por_casa.most_common():
        print(f"  {k[0]:<14} {k[1]:<14} {v}")
    print("exemplos (id, dono, casa, stake, odd gravada, odd que fecha, res, res novo, ΔP/L):")
    for e in exemplos:
        print("  ", e)


asyncio.run(main())
