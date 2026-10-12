"""Qualidade e custo por casa, ANTES × DEPOIS da chave `EXTRACAO_SEM_PENSAMENTO` (s409).

Ligada em 11/10/2026 21:10:40 (-03) para as 15 casas de outubro. Por casa e por janela:

  • `uso_tokens`  (desde 7 dias antes): extrações, saída e escrita/leitura de cache por
    extração, US$ por extração. A escrita de cache é o sinal do aquecedor (item 1 do
    D1): se ela SOBE depois da chave, o prefixo dos manuais gerais está esfriando.
  • `sombra_tsv`  (existe desde 11/10 19:57): % de extrações com repescagem (cobertura ou
    fidelidade; custo total > custo da leitura principal).
  • `sombra_numeros`: apostas em que os fiscais mexeram em stake, odd ou resultado
    (bruto ≠ final), separando LIQUIDADAS de ABERTAS (aberta compara vazio com vazio).

Banco: só leitura.   python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_qualidade_por_casa.py
"""
import asyncio, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for linha in open(os.path.join(RAIZ, ".env"), encoding="utf-8"):
    if "=" in linha:
        k, v = linha.strip().split("=", 1)
        if k and v:
            os.environ.setdefault(k, v.strip().strip('"'))

import asyncpg

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VIRADA = "2026-10-11 21:10:40-03"
CASAS = ["DEX Sport", "Megapari", "MyStake", "Shuffle", "Betrebels", "Duel", "Betpanda",
         "BetMartini", "Betfury", "Vavada", "Betcoin", "PariPesa", "SapphireBet", "1xBit",
         "Kikobet"]


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
    await c.execute("SET default_transaction_read_only = on")
    uso = await c.fetch(f"""
        SELECT casa, criado_em >= '{VIRADA}' AS depois, count(*) n,
               round(avg(output)) saida, round(avg(cache_write)) cw, round(avg(cache_read)) cr,
               round(avg(custo_usd)::numeric, 3) usd
          FROM uso_tokens
         WHERE casa = ANY($1) AND criado_em >= timestamptz '{VIRADA}' - interval '7 days'
         GROUP BY 1, 2""", CASAS)
    tsv = await c.fetch(f"""
        SELECT casa, criado_em >= '{VIRADA}' AS depois, count(*) n,
               count(*) FILTER (WHERE titular_custo_total > titular_custo_base + 0.0001) rep
          FROM sombra_tsv WHERE casa = ANY($1) GROUP BY 1, 2""", CASAS)
    num = await c.fetch(f"""
        SELECT casa, criado_em >= '{VIRADA}' AS depois,
               count(*) FILTER (WHERE res_tf IS NOT NULL) liq,
               count(*) FILTER (WHERE res_tf IS NOT NULL AND (stake_tb IS DISTINCT FROM stake_tf
                    OR odd_tb IS DISTINCT FROM odd_tf OR res_tb IS DISTINCT FROM res_tf)) liq_fiscal,
               count(*) FILTER (WHERE res_tf IS NULL) abertas
          FROM sombra_numeros WHERE casa = ANY($1) GROUP BY 1, 2""", CASAS)
    await c.close()

    idx = {}
    for nome, rows in (("uso", uso), ("tsv", tsv), ("num", num)):
        for r in rows:
            idx[(nome, r["casa"], r["depois"])] = r
    print(f"virada da chave: {VIRADA}\n")
    cab = (f"{'casa':<12}{'janela':<8}{'extr.':>6}{'saída':>8}{'cache esc.':>11}{'cache lido':>11}"
           f"{'US$/extr':>9}{'repesca':>9}{'liq.':>6}{'fiscal':>7}{'abertas':>8}")
    print(cab)
    for casa in CASAS:
        for depois in (False, True):
            u, t, n = (idx.get((k, casa, depois)) for k in ("uso", "tsv", "num"))
            if not (u or t or n):
                continue
            rep = f"{t['rep']}/{t['n']}" if t else "-"
            print(f"{casa:<12}{'depois' if depois else 'antes':<8}"
                  f"{(u['n'] if u else 0):>6}{(u['saida'] if u else '-'):>8}"
                  f"{(u['cw'] if u else '-'):>11}{(u['cr'] if u else '-'):>11}"
                  f"{(u['usd'] if u else '-'):>9}{rep:>9}"
                  f"{(n['liq'] if n else 0):>6}{(n['liq_fiscal'] if n else 0):>7}"
                  f"{(n['abertas'] if n else 0):>8}")


asyncio.run(main())
