"""Fase 0B — backtest holdout do matcher v4 de auto-atribuição (READ-ONLY).

Porta fiel de _sugParaBilhete/_stakeSignal/_parseStakeSig/_parseCentavos do
app/static/index.html. v4 = código de centavos EXPLÍCITO ("Os centavos (21)" nas obs) tem
prioridade e vira match nível-ID; quem não declara código cai na lógica antiga (finais/quebrada).
Para cada dono: pega os bilhetes recentes JÁ atribuídos (excluindo os de procedência
'sugerido', que são chute do próprio sistema — ver Fase 0A), esconde o tipster, roda o
matcher contra o cadastro ATUAL e mede cobertura × precisão + as maiores confusões.

NADA é gravado — só SELECT. Uso:
    cd app && python ../scripts/backtest_matcher.py [DIAS]   (default 14)

⚠️ CAVEAT (holdout temporal): usa `criado_em` como eixo de tempo. Isso vale para bases
NATIVAS (extraídas ao longo do tempo, ex.: Feca). Para bases IMPORTADAS de uma vez
(ex.: Jonathan, Lava), `criado_em` = data do import (todas iguais) → o holdout degenera;
nessas, o split temporal correto usa a coluna `data` (data do evento). Refino pendente.
"""
import asyncio, asyncpg, pathlib, sys, re, math
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
env = (ROOT / ".env").read_text(encoding="utf-8")
DB = next(l.split("=", 1)[1].strip().strip('"').strip("'") for l in env.splitlines() if l.strip().startswith("DATABASE_URL"))
DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 14
FOLGA = 7   # idêntico ao runtime (index.html)

def _norm(s): return ("" if s is None else str(s)).strip().lower()
def _slug(s): return re.sub(r"\s+", "", _norm(s))
def _split(s): return [x.strip() for x in ("" if s is None else str(s)).split(",") if x.strip()]
def _num_br(v):
    if isinstance(v, (int, float)): return float(v)
    s = re.sub(r"[^\d.,-]", "", "" if v is None else str(v))
    if not s: return 0.0
    t = s.replace(".", "").replace(",", ".") if "," in s else s
    try: return float(t)
    except Exception: return 0.0
def _parse_sig(dica):
    finais, valores = set(), set()
    s = _norm(dica)
    for m in re.finditer(r"final\s+(\d)\b", s):
        d = int(m.group(1))
        if d: finais.add(d)
    for m in re.finditer(r"\b\d{2,}(?:[.,]\d+)?\b", s):
        v = round(float(m.group(0).replace(",", ".")))
        if v >= 20:
            valores.add(v)
            if v % 10 != 0: finais.add(v % 10)
    return {"finais": finais, "valores": valores, "quebrado": bool(re.search(r"quebrad|centavo|cents", s)), "quebradoCasa": None}
def _parse_centavos(dica, obs):
    # Código de centavos EXPLÍCITO (carteira do Jonathan): "(21)" / "21 centavos". Lê dica + obs.
    codes = set()
    txt = f"{dica or ''}\n{obs or ''}".lower()
    for m in re.finditer(r"\((\d{2})\)", txt):        codes.add(int(m.group(1)))
    for m in re.finditer(r"(\d{2})\s*centavos", txt):  codes.add(int(m.group(1)))
    return codes
def _stake_signal(S, sig, casaK):
    n = _num_br(S)
    if not n or not sig: return (0.0, False)
    if sig.get("centavos"):   # código explícito tem prioridade — centavo é a identidade do tipster
        cents = round(n * 100) % 100
        return (50.0, False) if cents in sig["centavos"] else (0.0, True)
    quebrada = round(n * 100) % 100 != 0
    hasFinal = len(sig["finais"]) > 0
    if quebrada:
        if sig["quebrado"]:
            return (25.0, False) if (not sig["quebradoCasa"] or _slug(sig["quebradoCasa"]) == casaK) else (0.0, False)
        if hasFinal: return (0.0, True)
        return (0.0, False)
    I = round(n); d = I % 10
    if hasFinal:
        if d != 0 and d in sig["finais"]: return (25.0 / math.sqrt(len(sig["finais"])), False)
        if I in sig["valores"]: return (25.0, False)
        return (0.0, True)
    if I in sig["valores"]: return (25.0 if len(sig["valores"]) == 1 else 0.0, False)   # valor exato = fingerprint só se assinatura única
    return (0.0, False)
def _declara_stake(S, sig, casaK):
    # Membership: o tipster DECLARA esta stake? (mede distintividade, ignora tamanho de lista).
    n = _num_br(S)
    if not n or not sig: return False
    if sig.get("centavos"): return (round(n * 100) % 100) in sig["centavos"]
    quebrada = round(n * 100) % 100 != 0
    if quebrada: return bool(sig["quebrado"]) and (not sig["quebradoCasa"] or _slug(sig["quebradoCasa"]) == casaK)
    I = round(n); d = I % 10
    return (d != 0 and d in sig["finais"]) or (I in sig["valores"])
def build_index(profs):
    ownCasa, ownEsp, ownMkt, sig, esp = defaultdict(set), defaultdict(set), defaultdict(set), {}, {}
    for p in profs:
        nome = p["nome"]
        for c in _split(p["casas"]): ownCasa[_slug(c)].add(nome)
        for e in _split(p["esportes"]): ownEsp[_norm(e)].add(nome)
        for mk in _split(p["mercados"]): ownMkt[_norm(mk)].add(nome)
        ss = _parse_sig(p["dica_stake"])
        if ss["quebrado"]:
            dl = _norm(p["dica_stake"])
            ss["quebradoCasa"] = next((c for c in _split(p["casas"]) if _slug(c) in dl), None)
        ss["centavos"] = _parse_centavos(p["dica_stake"], p.get("obs"))
        sig[nome] = ss
        esp[nome] = set(_norm(e) for e in _split(p["esportes"]))
    return {"ownCasa": ownCasa, "ownEsp": ownEsp, "ownMkt": ownMkt, "sig": sig, "esp": esp}
def _ranqueia(b, idx, profs, allowed=None):
    casaK, espK, mktK = _slug(b["casa"]), _norm(b["esporte"]), _norm(b["aposta"])
    wOf = lambda s, excl: excl if (s and len(s) == 1) else 1
    pool = [p for p in profs if allowed is None or p["nome"] in allowed]
    # Sobreviventes do filtro duro de esporte.
    survivors = [p for p in pool
                 if not (espK and idx["esp"].get(p["nome"]) and len(idx["esp"][p["nome"]]) and espK not in idx["esp"][p["nome"]])]
    # Distintividade CONTEXTUAL: conta quantos sobreviventes DECLARAM este stake (o "≤2 donos").
    # Valor redondo comum (300 = 8 donos) vira ruído entre os de Futebol → 0; 250 do Robotenis só
    # colide com outros esportes (fora dos sobreviventes) → segue distintiva. Mede por DECLARAÇÃO,
    # não por pontuação: senão um valor comum de vários donos passaria batido.
    claimants = sum(1 for p in survivors if _declara_stake(b["stake"], idx["sig"][p["nome"]], casaK))
    stake_distinta = claimants <= 2
    ranked = []
    for p in survivors:
        nome = p["nome"]
        w_add, veto = _stake_signal(b["stake"], idx["sig"][nome], casaK)
        if veto: continue
        w = w_add if stake_distinta else 0.0
        oe = idx["ownEsp"].get(espK);  w += wOf(oe, 10) if (oe and nome in oe) else 0
        om = idx["ownMkt"].get(mktK);  w += wOf(om, 10) if (om and nome in om) else 0
        oc = idx["ownCasa"].get(casaK); w += wOf(oc, 5) if (oc and nome in oc) else 0
        if w > 0: ranked.append((nome, w))
    ranked.sort(key=lambda x: -x[1])
    if not ranked: return None
    # Dono único do esporte, sobrevivente sozinho → sugere sem exigir folga (não há concorrente).
    if len(ranked) == 1:
        oe = idx["ownEsp"].get(espK)
        if oe and ranked[0][0] in oe: return ranked[0][0]
    top = ranked[0][1]; second = ranked[1][1] if len(ranked) > 1 else 0
    return ranked[0][0] if (top - second >= FOLGA) else None

def suggest(b, idx, profs, dedicadas):
    # Casa-feudo (curadoria em casa_config): 1 dono CRAVA; 2 RESTRINGE o pool e o stake desempata;
    # ADITIVO (não suprime → cai no baseline). Espelha _sugParaBilhete do index.html (Etapa 2).
    ded = [n for n in dedicadas.get(_slug(b["casa"]), []) if n in idx["sig"]]
    if len(ded) == 1: return ded[0]
    if len(ded) == 2:
        r = _ranqueia(b, idx, profs, set(ded))
        if r is not None: return r
    return _ranqueia(b, idx, profs, None)

async def main():
    conn = await asyncpg.connect(DB)
    try:
        donos = [r["dono"] for r in await conn.fetch("SELECT DISTINCT dono FROM tipsters ORDER BY dono")]
        print(f"janela de teste: últimos {DIAS} dias · folga {FOLGA}\n")
        print(f"{'dono':<12}{'N':>6}{'c/perfil':>9}{'cobertura':>11}{'precisão':>10}{'feudos':>8}   confusões (real→sugerido)")
        for dono in donos:
            profs = [dict(r) for r in await conn.fetch(
                "SELECT nome, casas, esportes, mercados, dica_stake, obs FROM tipsters "
                "WHERE dono=$1 AND arquivado IS NOT TRUE", dono)]
            if not profs: continue
            ativos = set(p["nome"] for p in profs)
            idx = build_index(profs)
            # Casa-feudo: curadoria do Feca (casa_config, modo='dedicada'). Vazio → dormente.
            ded_rows = await conn.fetch(
                "SELECT casa, tipsters FROM casa_config WHERE dono=$1 AND modo='dedicada'", dono)
            dedicadas = {}
            for r in ded_rows:
                tips = [t.strip() for t in (r["tipsters"] or "").split(",") if t.strip()][:2]
                if tips: dedicadas[_slug(r["casa"])] = tips
            bilhetes = await conn.fetch(
                "SELECT casa, esporte, aposta, stake, tipster FROM bilhetes "
                "WHERE dono=$1 AND tipster IS NOT NULL AND tipster <> '' "
                "AND (origem_tipster IS DISTINCT FROM 'sugerido') "
                "AND criado_em >= NOW() - ($2 || ' days')::interval", dono, str(DIAS))
            N = len(bilhetes)
            if N == 0: continue
            com_perfil = sug = acerto = 0
            conf = Counter()
            for b in bilhetes:
                real = b["tipster"].strip()
                if real in ativos: com_perfil += 1
                pred = suggest(b, idx, profs, dedicadas)
                if pred is not None:
                    sug += 1
                    if pred == real: acerto += 1
                    else: conf[(real, pred)] += 1
            cob = f"{100*sug/N:.0f}%"
            prec = f"{100*acerto/sug:.0f}%" if sug else "—"
            top_conf = " · ".join(f"{r}→{p}({n})" for (r, p), n in conf.most_common(3))
            print(f"{dono:<12}{N:>6}{com_perfil:>9}{cob:>11}{prec:>10}{len(dedicadas):>8}   {top_conf}")
    finally:
        await conn.close()

asyncio.run(main())
