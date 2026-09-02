"""Backtest holdout dos DOIS matchers de auto-atribuição, lado a lado (READ-ONLY).

  · declarativo — o que o dono DECLARA no perfil de Tipster / Método (casas, esportes,
    mercados, dica de stake). Porta fiel de `_sugParaBilhete` & cia. do `app/static/index.html`,
    onde ele ainda vive como rede de segurança para dono sem histórico rotulado.
  · evidência   — o que o dono JÁ ROTULOU à mão. Importa `app/matcher.py` DIRETO: o backtest
    mede o código de produção, não uma cópia dele (cópia diverge em silêncio e o placar passa
    a medir outra coisa).

Para cada dono: pega os bilhetes da janela JÁ atribuídos (excluindo os de procedência
'sugerido', que são chute do próprio sistema), esconde o tipster, roda os dois matchers e mede
cobertura × precisão + as maiores confusões. O modelo de evidência treina só no que veio ANTES
da janela — holdout temporal, senão o placar é in-sample e mente para cima.

NADA é gravado — só SELECT. Uso:
    cd app && python ../scripts/backtest_matcher.py [DIAS]   (default 14)

Placar de referência (s289, janela de 30 dias, base real):

    dono        declarativo      evidência
    Feca        47 % / 74 %      61 % / 89 %
    Gabriel     12 % / 99 %      46 % / 88 %
    Jonathan    10 % / 41 %      28 % / 96 %

Leia a precisão junto da cobertura: apertar um matcher até ele quase não sugerir sobe a
precisão sem servir para nada. E leia o placar sabendo que **assinatura tem ERA** — o `199`
foi do SóTudo até junho e virou do LBB em julho.

⚠️ CAVEAT (holdout temporal): usa `criado_em` como eixo de tempo. Isso vale para bases
NATIVAS (extraídas ao longo do tempo, ex.: Feca). Para bases IMPORTADAS de uma vez
(ex.: Jonathan, Lava), `criado_em` = data do import (todas iguais) → o holdout degenera;
nessas, o split temporal correto usa a coluna `data` (data do evento). Refino pendente.
"""
import asyncio, asyncpg, pathlib, sys, re, math
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
import matcher   # o matcher de PRODUÇÃO, não uma porta dele

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

def _placar(rows, prever):
    """(cobertura %, precisão %, confusões) de um matcher sobre um lote rotulado."""
    sug = acerto = 0
    conf = Counter()
    for b in rows:
        real = (b["tipster"] or "").strip()
        pred = prever(b)
        if pred is not None:
            sug += 1
            if pred == real:
                acerto += 1
            else:
                conf[(real, pred)] += 1
    cob = 100 * sug / len(rows) if rows else 0
    prec = 100 * acerto / sug if sug else 0
    return cob, prec, sug, acerto, conf


def _linha(rot, cob, prec, sug, acerto, conf, extra=""):
    top = " · ".join(f"{r}→{p}({n})" for (r, p), n in conf.most_common(3))
    marca = f"{cob:.0f}%" if sug else "—"
    pmarca = f"{prec:.0f}%" if sug else "—"
    print(f"   {rot:<14}{marca:>10}{pmarca:>10}  ({acerto}/{sug}){extra}   {top}")


async def main():
    conn = await asyncpg.connect(DB)
    try:
        donos = [r["dono"] for r in await conn.fetch("SELECT DISTINCT dono FROM tipsters ORDER BY dono")]
        print(f"janela de teste: últimos {DIAS} dias · folga declarativa {FOLGA} · "
              f"margem de evidência {matcher.MARGEM} · inéditas ≤ {matcher.MAX_INEDITAS}\n")
        for dono in donos:
            profs = [dict(r) for r in await conn.fetch(
                "SELECT nome, casas, esportes, mercados, dica_stake, obs FROM tipsters "
                "WHERE dono=$1 AND arquivado IS NOT TRUE", dono)]
            if not profs: continue
            ativos = [p["nome"] for p in profs]
            idx = build_index(profs)
            # Casa-feudo: curadoria do dono (casa_config, modo='dedicada'). Vazio → dormente.
            ded_rows = await conn.fetch(
                "SELECT casa, tipsters FROM casa_config WHERE dono=$1 AND modo='dedicada'", dono)
            dedicadas = {}
            for r in ded_rows:
                tips = [t.strip() for t in (r["tipsters"] or "").split(",") if t.strip()][:2]
                if tips: dedicadas[_slug(r["casa"])] = tips
            campos = "casa, esporte, aposta, stake, descricao, tipster"
            filtro = ("WHERE dono=$1 AND tipster IS NOT NULL AND tipster <> '' "
                      "AND (origem_tipster IS DISTINCT FROM 'sugerido') ")
            bilhetes = await conn.fetch(
                f"SELECT {campos} FROM bilhetes " + filtro +
                "AND criado_em >= NOW() - ($2 || ' days')::interval", dono, str(DIAS))
            if not bilhetes: continue
            # Treino = TUDO que veio antes da janela de teste. Holdout temporal: sem este corte
            # o modelo já viu a resposta e o placar vira propaganda.
            antes = await conn.fetch(
                f"SELECT {campos} FROM bilhetes " + filtro +
                "AND criado_em < NOW() - ($2 || ' days')::interval", dono, str(DIAS))
            modelo = matcher.treinar([dict(r) for r in antes])
            # Domínio de esporte: quem manda em cada esporte, contando TODOS os rótulos ANTES da
            # janela (inclusive os sugeridos — ver repository.dominio_esportes). Computar sobre a
            # janela de teste seria vazamento: a resposta estaria dentro da pergunta.
            dom_rows = await conn.fetch(
                "SELECT lower(btrim(esporte)) AS esp, btrim(tipster) AS tip, COUNT(*) AS n "
                "FROM bilhetes WHERE dono=$1 AND tipster IS NOT NULL AND btrim(tipster) <> '' "
                "AND esporte IS NOT NULL AND btrim(esporte) <> '' "
                "AND criado_em < NOW() - ($2 || ' days')::interval GROUP BY 1, 2", dono, str(DIAS))
            tot_esp, top_esp = {}, {}
            for r in dom_rows:
                tot_esp[r["esp"]] = tot_esp.get(r["esp"], 0) + r["n"]
                if r["n"] > top_esp.get(r["esp"], ("", 0))[1]:
                    top_esp[r["esp"]] = (r["tip"], r["n"])
            dominio = {e: (top_esp[e][0], top_esp[e][1], tot_esp[e]) for e in tot_esp}
            com_perfil = sum(1 for b in bilhetes if (b["tipster"] or "").strip() in set(ativos))
            print(f"── {dono} · {len(bilhetes)} bilhetes na janela ({com_perfil} com perfil ativo) · "
                  f"treino {modelo.treino} · {len(dedicadas)} casa(s) dedicada(s)")
            print(f"   {'matcher':<14}{'cobertura':>10}{'precisão':>10}            confusões (real→sugerido)")
            _linha("declarativo", *_placar(bilhetes, lambda b: suggest(b, idx, profs, dedicadas)))
            if modelo.treino < matcher.MIN_TREINO:
                print(f"   {'evidência':<14}{'—':>10}{'—':>10}  (treino abaixo de {matcher.MIN_TREINO} → o app usa o declarativo)")
            else:
                def _evid(b):
                    return matcher.sugerir(modelo, ativos, b["casa"], b["esporte"], b["aposta"],
                                           b["stake"], b["descricao"], dominio=dominio)
                _linha("evidência", *_placar(bilhetes, _evid))

                # PRODUÇÃO (s310) = evidência + 2ª passada do declarado. Sem esta linha o backtest
                # mediria duas metades que o app não usa isoladamente, e o placar passaria a
                # descrever outra coisa. A folga alta e o corte de novato vêm do `matcher`, os
                # mesmos que a rota manda para a tela — nenhum número é redigitado aqui.
                novos = set(matcher.novatos(modelo, ativos))

                def _hibrido(b):
                    nome = _evid(b)
                    if nome:
                        return nome
                    global FOLGA
                    antes, FOLGA = FOLGA, matcher.FOLGA_DECLARADA
                    try:
                        d = suggest(b, idx, profs, dedicadas)
                    finally:
                        FOLGA = antes
                    return d if (d in novos) else None
                _linha("PRODUÇÃO", *_placar(bilhetes, _hibrido))
            print()
    finally:
        await conn.close()

asyncio.run(main())
