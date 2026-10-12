"""O fiscal (e8ce01f) acha o retorno nas apostas GANHAS de uma casa? Replay, só leitura (s409).

Pré-condição para a casa voltar à `EXTRACAO_SEM_PENSAMENTO` (decisão do Feca, 12/10): sem o
retorno, o gate da odd não roda e o erro que a medição da DEX achou passaria direto.

Para cada aposta W ou HW gravada, pega o bloco cru mais recente do código na `sombra_rotulos`
(desde 01/10) e passa pelo código REAL do fiscal:
  • achou     `_retorno_do_bloco(_financeiro_do_texto(...))` devolve número;
  • confere   esse retorno é o dinheiro da linha gravada (`stake do bloco × odd`, W; HW pela
              fórmula da meia), com folga de 1 centavo por unidade de odd arredondada;
  • mudaria   o `corrigir_stake_tsv` inteiro reescreveria a linha (resultado ou odd).

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_fiscal_acha_retorno.py [CASA ...]

Sem argumento: as 8 casas 1xBet e Altenar que saíram da chave em 11/10.
"""
import asyncio
import os
import sys
from collections import Counter, defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RAIZ, "app"))
for linha in open(os.path.join(RAIZ, ".env"), encoding="utf-8"):
    if "=" in linha:
        k, v = linha.strip().split("=", 1)
        if k and v:
            os.environ.setdefault(k, v.strip().strip('"'))

import asyncpg  # noqa: E402

import repository as R  # noqa: E402

OITO = ["MEGAPARI", "PARIPESA", "SAPPHIREBET", "1XBIT", "BETMARTINI", "BETREBELS", "VAVADA",
        "KIKOBET"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    casas = [c.upper() for c in sys.argv[1:]] or OITO
    c = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
    await c.execute("SET default_transaction_read_only = on")
    rows = await c.fetch(r"""
        WITH ult AS (
          SELECT DISTINCT ON (dono, casa, codigo) dono, casa, codigo, bruto, criado_em
            FROM sombra_rotulos
           WHERE codigo <> '' AND criado_em >= '2026-10-01'
             AND upper(replace(casa, ' ', '')) = ANY($1::text[])
           ORDER BY dono, casa, codigo, criado_em DESC, id DESC)
        SELECT b.id, b.dono, b.casa, b.data, b.esporte, b.parceiro, b.aposta, b.descricao,
               b.stake, b.odd, b.resultado, b.codigo_bilhete, u.bruto, u.criado_em
          FROM bilhetes b JOIN ult u
            ON u.dono = b.dono AND u.casa = b.casa AND u.codigo = b.codigo_bilhete
         WHERE b.resultado IN ('W', 'HW')""", casas)
    await c.close()
    t = defaultdict(Counter)
    ex = defaultdict(list)
    for r in rows:
        casa = r["casa"].upper().replace(" ", "")
        k = (casa, r["dono"])
        cod = r["codigo_bilhete"]
        texto = f"[Código: {cod}]\n{r['bruto']}"
        info = R._financeiro_do_texto(texto).get(cod)
        t[k]["ganhas"] += 1
        if info is None:
            t[k]["bloco sem Stake único"] += 1
            if len(ex[k]) < 3:
                ex[k].append((cod, "sem Stake único"))
            continue
        stake = R._num_bloco(info["stake"])
        ret = R._retorno_do_bloco(info, stake) if stake else None
        if ret is None:
            if len(ex[k]) < 3:
                ex[k].append((cod, "sem retorno", [l for l in r["bruto"].splitlines()
                                                   if l.startswith(("Status:", "Retorno"))]))
            continue
        t[k]["achou"] += 1
        odd = R._num_bloco(r["odd"])
        if odd:
            pago = stake * odd if r["resultado"] == "W" else stake / 2 * odd + stake / 2
            if abs(pago - ret) <= 0.01 + stake * 0.00005:
                t[k]["confere"] += 1
            elif len(ex[k]) < 3:
                ex[k].append((cod, "não confere", r["resultado"], stake, r["odd"], ret))
        cols = [r["data"] or "", r["esporte"] or "", "", r["casa"], r["parceiro"] or "",
                r["aposta"] or "", (r["descricao"] or "").replace("\t", " "),
                r["stake"] or "", r["odd"] or "", r["resultado"], cod]
        tsv = "\t".join(cols)
        novo, _ = R.corrigir_stake_tsv(tsv, texto)
        if novo != tsv:
            pv, pn = tsv.split("\t"), novo.split("\t")
            if (pv[8], pv[9]) != (pn[8], pn[9]):
                t[k]["mudaria"] += 1
                if len(ex[k]) < 3:
                    ex[k].append((cod, "mudaria", pv[8], pv[9], "→", pn[8], pn[9]))
    print("Ganhas (W/HW) de outubro com bloco na sombra_rotulos, o mais recente de cada código\n")
    for casa in casas:
        linhas = [(k, v) for k, v in sorted(t.items()) if k[0] == casa]
        if not linhas:
            print(f"{casa:<12} sem ganha com bloco desde 01/10")
            continue
        for (cs, dono), v in linhas:
            print(f"{cs:<12} {dono:<16} ganhas {v['ganhas']:>4} · achou {v['achou']:>4} · "
                  f"confere {v['confere']:>4} · mudaria {v['mudaria']:>3}"
                  + (f" · bloco sem Stake único {v['bloco sem Stake único']}"
                     if v["bloco sem Stake único"] else ""))
            for e in ex[(cs, dono)]:
                print("     ", e)


asyncio.run(main())
