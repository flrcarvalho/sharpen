"""Quantas apostas de OUTUBRO das 15 casas mudariam de odd com a regra proposta? (s409)

Regra, como chegou ao Feca em 11/10 (decidido + ajustes da consultoria, a confirmar):
  • aberta                  → odd calculada pelas pernas (produto; simples = a perna)
  • W / HW (resolvida)      → (a) a odd que FECHA o retorno no centavo, pela fórmula do
                              resultado; candidatas: a calculada e a da casa (`Odd:`);
                              se as duas fecham, vale a calculada; se nenhuma, retorno ÷ stake
  • L / V                   → (b) a regra da aberta
  • cashout                 → (c) a regra da aberta  [W cujo retorno nenhuma odd fecha]

Compara com a odd GRAVADA em `bilhetes` (régua do `/salvar`, `sombra_numeros.norm_numero`,
igualdade exata). O bloco é o mais recente daquele dono+casa+código na `sombra_rotulos`.
Sistema fica de fora (a odd de um sistema é a MÉDIA, outra régua). Banco: só leitura.
A diferença de P/L usa a stake GRAVADA (em real), então vale também em casa de USDT: a
odd é razão e não tem moeda.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_regra_odd.py
"""
import asyncio, os, re, sys
from collections import Counter, defaultdict
from decimal import Decimal, localcontext

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(RAIZ, "app"))
for linha in open(os.path.join(RAIZ, ".env"), encoding="utf-8"):
    if "=" in linha:
        k, v = linha.strip().split("=", 1)
        if k and v:
            os.environ.setdefault(k, v.strip().strip('"'))

import asyncpg
import repository as R
import tradutor as T
from sombra_numeros import norm_numero

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CASAS = ["DEX Sport", "Megapari", "MyStake", "Shuffle", "Betrebels", "Duel", "Betpanda",
         "BetMartini", "Betfury", "Vavada", "Betcoin", "PariPesa", "SapphireBet", "1xBit",
         "Kikobet"]
# Odd de cada perna, nos três formatos das 6 famílias de outubro.
_PERNA = re.compile(r"^\s*(?:Odd da (?:sele[çc][ãa]o|perna):\s*([\d.,]+)"
                    r"|\d+\.\s.*@\s*([\d.,]+)\s*\[)", re.M)
_ODD_CASA = re.compile(r"^Odd:\s*([\d.,]+)", re.M)
_STAKE = re.compile(r"^Stake:\s*(?:R\$\s*)?([\d.,]+)", re.M)
# Retorno REALIZADO: no Status ("(retorno 158,80 usdt)") ou numa linha própria ("Retorno:").
_RET_STATUS = re.compile(r"^Status:.*?\bretorno\s*(?:R\$\s*)?([\d.,]+)", re.M | re.I)
_RET_LINHA = re.compile(r"^Retorno:\s*(?:R\$\s*)?([\d.,]+)", re.M)
_JOGO = re.compile(r"^\s*(?:Jogo:\s*([^·\n]+)|\d+\.\s*([^/\n]+?)\s*//)", re.M)
_ANULADA = re.compile(r"\[(?:perna )?(?:anulad|void|devolvid|cancel|refund|returned|reembols)", re.I)
_SISTEMA = re.compile(r"^Tipo:\s*Sistema|BetTypeId 2|Sistema \(", re.M | re.I)


def _dec(s):
    return T._dec_bloco(s) if s else None


def _produto(pernas):
    if not pernas or any(p is None or p <= 1 for p in pernas):
        return None
    with localcontext() as ctx:
        ctx.prec = T._PRECISAO_PRODUTO
        prod = Decimal(1)
        for p in pernas:
            prod *= p
    with localcontext() as ctx:
        ctx.prec = T._PRECISAO_ODD
        return +prod


def _fecha(stake, odd, retorno, res):
    if odd is None:
        return False
    paga = stake * odd if res == "W" else (stake / 2) * odd + stake / 2
    return abs(paga - retorno) <= Decimal("0.005")


def _regra(res, stake, retorno, calc, casa):
    """(odd nova como Decimal ou None, rótulo do ramo)."""
    if res in ("", "L", "V"):
        return calc, ("aberta" if res == "" else res)
    if retorno is None or stake is None or stake <= 0:
        return None, f"{res} sem retorno no bloco"
    fc, fk = _fecha(stake, calc, retorno, res), _fecha(stake, casa, retorno, res)
    if fc:
        return calc, f"{res} fecha (calculada)"
    if fk:
        return casa, f"{res} fecha (da casa)"
    return calc, f"{res} cashout → regra da aberta"


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1))
    await c.execute("SET default_transaction_read_only = on")
    rows = await c.fetch("""
        WITH ult AS (
          SELECT DISTINCT ON (dono, casa, codigo) dono, casa, codigo, bruto
            FROM sombra_rotulos WHERE codigo <> '' AND casa = ANY($1)
           ORDER BY dono, casa, codigo, criado_em DESC, id DESC)
        SELECT b.id, b.dono, b.casa, b.stake, b.odd, COALESCE(b.resultado, '') AS res,
               u.bruto IS NOT NULL AS tem_bloco, u.bruto
          FROM bilhetes b LEFT JOIN ult u
            ON u.dono = b.dono AND u.casa = b.casa AND u.codigo = b.codigo_bilhete
         WHERE b.casa = ANY($1) AND b.criado_em >= '2026-10-01'""", CASAS)
    await c.close()

    tot = defaultdict(Counter)       # casa → contadores
    ramos = Counter()                # ramo → mudou
    ramos_n = Counter()
    exemplos = defaultdict(list)
    dpl = defaultdict(Decimal)
    sem_ret_linha_no_status = Counter()
    causas, ex_outra = Counter(), []
    for r in rows:
        casa, res = r["casa"], (r["res"] or "").strip().upper()
        t = tot[casa]
        t["apostas"] += 1
        if not r["tem_bloco"]:
            t["sem bloco"] += 1
            continue
        b = r["bruto"]
        if _SISTEMA.search(b):
            t["sistema (fora)"] += 1
            continue
        pernas = [_dec(m.group(1) or m.group(2)) for m in _PERNA.finditer(b)]
        calc = _produto(pernas)
        mk, ms = _ODD_CASA.search(b), _STAKE.search(b)
        casa_odd = _dec(mk.group(1)) if mk else None
        stake = _dec(ms.group(1)) if ms else None
        mr = _RET_STATUS.search(b) or _RET_LINHA.search(b)
        retorno = _dec(mr.group(1)) if mr else None
        if _RET_LINHA.search(b) and not _RET_STATUS.search(b):
            sem_ret_linha_no_status[casa] += 1
        if res not in ("", "W", "L", "V", "HW", "HL"):
            t["resultado fora"] += 1
            continue
        if res == "HL":
            t["HL (fora)"] += 1
            continue
        nova, ramo = _regra(res, stake, retorno, calc, casa_odd)
        if nova is None:
            t["não calculável"] += 1
            ramos_n[ramo if "retorno" in ramo else ramo + " sem pernas"] += 1
            continue
        t["comparadas"] += 1
        ramos_n[ramo] += 1
        g = norm_numero(r["odd"])
        n = norm_numero(T._odd_br(nova))
        if g == n:
            continue
        t["mudaria"] += 1
        ramos[ramo] += 1
        sg = R._num_or_none(r["stake"])
        og = R._num_or_none(r["odd"])
        pl_g = R.calcular_pl(r["stake"], r["odd"], res) if res else None
        pl_n = R.calcular_pl(r["stake"], T._odd_br(nova), res) if res else None
        if pl_g is not None and pl_n is not None:
            dpl[casa] += Decimal(str(round(pl_n - pl_g, 2)))
            if abs(pl_n - pl_g) >= 0.01:
                t["mudaria o P/L"] += 1
        dif = abs(nova - Decimal(str(og))) / Decimal(str(og)) if og else Decimal(1)
        if dif < Decimal("0.005"):
            causa = "precisão (< 0,5%)"
        else:
            jogos = [(m.group(1) or m.group(2) or "").strip() for m in _JOGO.finditer(b)]
            if _ANULADA.search(b):
                causa = "perna anulada"
            elif len(pernas) > 1 and len(set(jogos)) < len(jogos):
                causa = "mesmo jogo (Bet Builder)"
            elif (calc is not None and casa_odd is not None
                  and abs(calc - casa_odd) / casa_odd < Decimal("0.005")):
                causa = "gravada ≠ casa (calc ≈ casa)"
            else:
                causa = "outra"
        causas[(ramo.split(" ")[0], causa)] += 1
        if causa == "outra" and len(ex_outra) < 8:
            ex_outra.append((r["id"], casa, res or "aberta", r["odd"], T._odd_br(nova),
                             str(casa_odd) if casa_odd else "-", len(pernas)))
        if len(exemplos[ramo]) < 4:
            exemplos[ramo].append((r["id"], casa, res or "aberta", r["odd"], T._odd_br(nova),
                                   str(casa_odd) if casa_odd else "-", str(retorno) if retorno else "-",
                                   r["stake"]))

    print(f"{len(rows)} apostas de outubro nas 15 casas\n")
    cols = ["apostas", "sem bloco", "sistema (fora)", "HL (fora)", "não calculável",
            "comparadas", "mudaria", "mudaria o P/L"]
    print(f"{'casa':<12}" + "".join(f"{k[:14]:>15}" for k in cols) + f"{'Δ P/L R$':>12}")
    soma = Counter()
    for casa in sorted(tot, key=lambda k: -tot[k]["apostas"]):
        t = tot[casa]
        soma.update(t)
        print(f"{casa:<12}" + "".join(f"{t[k]:>15}" for k in cols) + f"{dpl[casa]:>12.2f}")
    print(f"{'TOTAL':<12}" + "".join(f"{soma[k]:>15}" for k in cols) + f"{sum(dpl.values()):>12.2f}")
    print("\npor ramo da regra: mudaria / comparadas")
    for k in sorted(ramos_n, key=lambda k: -ramos_n[k]):
        print(f"  {k:<36} {ramos[k]:>5} / {ramos_n[k]}")
    print("\ncausa das mudanças (ramo, causa): quantas")
    for k in sorted(causas, key=lambda k: -causas[k]):
        print(f"  {k[0]:<8} {k[1]:<34} {causas[k]}")
    print("  exemplos de 'outra' (id, casa, res, gravada, nova, casa, n pernas):")
    for e in ex_outra:
        print("    ", e)
    print("\nretorno só em linha `Retorno:` (fora do `Status:`, o fiscal não vê):",
          dict(sem_ret_linha_no_status))
    print("\nexemplos (id, casa, res, odd gravada, odd nova, odd da casa, retorno, stake):")
    for k, v in exemplos.items():
        print(" ", k)
        for e in v:
            print("    ", e)


asyncio.run(main())
