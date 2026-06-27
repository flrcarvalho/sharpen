"""
Coletor Polymarket — ingestão automática via API (sem IA de visão).

A Polymarket é uma casa cuja porta de entrada NÃO é screenshot+Claude, e sim a
própria API da carteira. Este módulo traduz posições/atividade on-chain para a
língua global do Planilhador: as 10 colunas do TSV + a 11ª coluna interna
`Código` (= conditionId / _splitId), que alimenta a dedup por ID do repositório.

Decisões (sessão Polymarket-1):
- Reusa o Worker Cloudflare que já destrava a API no Brasil (mesma URL do app
  Polymarket standalone). Do lado do servidor não há CORS; a chamada é direta.
- Converte USD→BRL pela PTAX (BCB) do dia da aposta; cai na cotação de hoje
  quando o dia não tem boletim (fim de semana/feriado).
- Ingere apenas posições RESOLVIDAS (W/L) — espelha o `getOrderedFechados` do
  app antigo e cobre o pedido "migrar todo o histórico". Posições abertas
  (transitórias) ficam para uma fase futura, evitando a borda de dedup
  aberta→resolvida em compras múltiplas.
- Paginação SEM teto fixo (corrige o achado #4 da auditoria do Polymarket):
  busca até a página vir vazia, garantindo histórico desde a 1ª aposta.

A detecção de esporte/categoria é determinística (regex sobre o título), depois
normalizada para a taxonomia global. É menos completa que a IA dos masters;
casos de cauda longa caem em `Outro`/`ML` e são triviais de ajustar na grade.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone, timedelta

import httpx

POLY_BASE = "https://polymarket-proxy.flrcarvalho.workers.dev"
BCB_PTAX = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoDolarDia(dataCotacao=@dataCotacao)"
)
BRT = timezone(timedelta(hours=-3))

_PAGE = 500          # tamanho de página (API aceita até 1000; 500 é o usado pelo app)
_SIZE_THRESHOLD = ".1"


# ── HTTP ────────────────────────────────────────────────────────────────────

async def _get_json(client: httpx.AsyncClient, url: str, params: dict) -> list:
    r = await client.get(url, params=params, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else []


async def _paginate(client: httpx.AsyncClient, path: str, wallet: str, extra: dict) -> list:
    """Busca todas as páginas de um endpoint da carteira até esgotar (sem teto)."""
    out: list = []
    offset = 0
    while True:
        params = {"user": wallet, "limit": _PAGE, "offset": offset, **extra}
        page = await _get_json(client, f"{POLY_BASE}/{path}", params)
        if not page:
            break
        out.extend(page)
        if len(page) < _PAGE:
            break
        offset += _PAGE
    return out


# ── Cotação USD→BRL (PTAX/BCB) ──────────────────────────────────────────────

async def _ptax(client: httpx.AsyncClient, dia: datetime) -> float | None:
    """cotacaoVenda do dia (M-D-Y). Retorna None se não houver boletim."""
    mdy = f"{dia.month:02d}-{dia.day:02d}-{dia.year:04d}"
    params = {"@dataCotacao": f"'{mdy}'", "$top": "1", "$format": "json"}
    try:
        r = await client.get(BCB_PTAX, params=params, headers={"Accept": "application/json"})
        r.raise_for_status()
        vals = r.json().get("value", [])
        return float(vals[0]["cotacaoVenda"]) if vals else None
    except Exception:
        return None


async def _cotacao_para(client: httpx.AsyncClient, iso: str, cache: dict, hoje: float | None) -> float | None:
    """Cotação do dia da aposta, com fallback de até 4 dias atrás (fim de semana)
    e, por fim, a cotação de hoje. Memoiza por data ISO."""
    if not iso:
        return hoje
    if iso in cache:
        return cache[iso]
    base = datetime.strptime(iso, "%Y-%m-%d")
    val = None
    for back in range(0, 5):
        val = await _ptax(client, base - timedelta(days=back))
        if val:
            break
    val = val or hoje
    cache[iso] = val
    return val


# ── Datas ───────────────────────────────────────────────────────────────────

def _build_redeem_cache(activity: list) -> dict:
    """conditionId → maior timestamp de REDEEM (data em que a vitória foi resgatada)."""
    cache: dict = {}
    for a in activity:
        if a.get("type") == "REDEEM" or a.get("side") == "REDEEM":
            cid = a.get("conditionId")
            if not cid:
                continue
            ts = int(a.get("timestamp") or 0)
            cache[cid] = max(cache.get(cid, 0), ts)
    return cache


def _data_iso(pos: dict, redeem_cache: dict) -> str:
    """Hierarquia de data para posição resolvida:
    1) timestamp do REDEEM (BRT)  2) data no eventSlug  3) startDate/createdAt/endDate."""
    redeem_ts = pos.get("_redeemTs") or redeem_cache.get(pos.get("conditionId"))
    if redeem_ts:
        d = datetime.fromtimestamp(int(redeem_ts), BRT)
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    slug = pos.get("eventSlug") or pos.get("slug") or ""
    matches = re.findall(r"\d{4}-\d{2}-\d{2}", slug)
    if matches:
        y, m, day = map(int, matches[-1].split("-"))
        if y > 2000 and 1 <= m <= 12 and 1 <= day <= 31:
            return f"{y:04d}-{m:02d}-{day:02d}"
    ts = pos.get("startDate") or pos.get("createdAt") or pos.get("endDate")
    if not ts:
        return ""
    if isinstance(ts, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", ts):
        return ts
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    except Exception:
        return ""


def _iso_to_br(iso: str) -> str:
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


# ── Esporte / Categoria ─────────────────────────────────────────────────────

def _detes_raw(title: str) -> str:
    """Detecção de esporte a partir do título (en-US da Polymarket). Granular o
    suficiente para a categoria; a coluna usa a versão normalizada (_norm_esporte)."""
    if not title:
        return "Outro"
    s = title.lower()

    # E-Sports (prefixo de jogo ou sinais de mapa/série) — todos colapsam no global
    if re.search(r"\b(dota 2|counter.strike|cs2|csgo|league of legends|\blol\b|valorant|"
                 r"call of duty|rocket league|overwatch|rainbow six|\br6\b|\bpubg\b|"
                 r"starcraft|apex legends|fortnite)\b", s):
        return "E-Sports"
    if re.search(r"\bmap handicap\b|\bgame handicap\b|\besports\b|\be-sports\b|"
                 r"\bmap \d\b|\bbo\d\b|^map total|^series total", s):
        return "E-Sports"

    if re.match(r"^(roland garros|atp|wta)\b", s):
        return "Tênis"
    # NBA / basquete
    if re.search(r"\b(lakers|celtics|warriors|nets|knicks|bulls|heat|spurs|nuggets|clippers|"
                 r"suns|mavericks|thunder|bucks|raptors|pistons|pacers|cavaliers|76ers|sixers|"
                 r"wizards|hawks|hornets|pelicans|grizzlies|jazz|timberwolves|blazers|trail blazers|"
                 r"kings|rockets|magic)\b", s) or re.search(r"\bnba\b|\beuroleague\b|basquete|basketball", s):
        return "Basquete"
    if re.search(r"\bnfl\b", s):
        return "Futebol Americano"
    if re.search(r"\bnhl\b", s):
        return "Hóquei"
    if re.search(r"premier league|champions league|bundesliga|serie a|la liga|brasileirao|"
                 r"copa do brasil|copa america|\beuro\b|ligue 1|eredivisie|primeira liga|\bmls\b", s):
        return "Futebol"
    if re.search(r"\bf1\b|formula.?1|formula one|grand prix", s):
        return "F1"
    if re.search(r"\bmma\b|\bufc\b|bellator|one championship", s):
        return "MMA"
    if re.search(r"\bgolf\b|\bgolfe\b|pga tour|liv golf|\bmasters\b|the open|ryder cup", s):
        return "Golf"
    if re.search(r"\blegs\b|\b180s\b|\bcheckout\b|\bdarts\b|\bdardos\b", s):
        return "Dardos"
    if re.search(r"\bframes\b|\bcentury\b|\bsnooker\b", s):
        return "Snooker"
    if re.search(r"\bgames\b|\bsets\b|\baces\b", s) and not re.search(r"\blegs\b|\bframes\b", s):
        return "Tênis"
    if re.search(r"baseball|beisebol|\bmlb\b", s):
        return "Baseball"
    if re.search(r"volei|vôlei|volleyball", s):
        return "Vôlei"
    if re.search(r"\brugby\b", s):
        return "Rugby"
    return "Outro"


# Polymarket (granular) → taxonomia oficial do MASTER_ESPORTES.
# Snooker não é canônico (candidato a cadastro futuro) → cai em Outro.
_NORM_ESPORTE = {
    "Futebol": "Futebol", "Basquete": "Basquete", "Futebol Americano": "Futebol Americano",
    "Hóquei": "Hóquei", "F1": "F1", "MMA": "MMA", "Golf": "Golf", "Dardos": "Dardos",
    "Tênis": "Tênis", "Baseball": "Baseball", "Vôlei": "Vôlei", "Rugby": "Rugby",
    "E-Sports": "E-Sports", "Snooker": "Outro", "Outro": "Outro",
}


def _norm_esporte(raw: str) -> str:
    return _NORM_ESPORTE.get(raw, "Outro")


def _categoria(title: str, raw_sport: str) -> str:
    t = (title or "").lower()
    if re.search(r"handicap|spread|\(-\d|\(\+\d|[-+]\d+\.5\s|game handicap|map handicap", t):
        return "Handicap"
    if re.search(r"over|under|mais de|menos de|total.*gol|total.*point|o/u", t):
        return "Player Props"
    if raw_sport == "Tênis":
        if "games" in t:
            return "Games"
        if "sets" in t:
            return "Sets"
        return "ML"
    if raw_sport == "Dardos":
        return "Legs" if "legs" in t else "ML"
    if raw_sport == "Futebol":
        if re.search(r"both teams|btts|ambas marcam", t):
            return "Ambas Marcam"
        if re.search(r"corner|escanteio", t):
            return "Escanteios"
        if re.search(r"card|cartão|cartao", t):
            return "Cartões"
        if re.search(r"\bgol\b|\bgols\b|goal", t):
            return "Gols"
        return "ML"
    return "ML"


# ── Reconstrução de posições (espelha o app standalone) ─────────────────────

def _f(d: dict, *keys: str) -> float:
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            try:
                return float(v)
            except (ValueError, TypeError):
                continue
    return 0.0


def _reconciliar_redeems(fechados: list, activity: list, active_cids: set) -> list:
    """Recupera vitórias já resgatadas (somem de /positions, vivem só na activity)."""
    closed_ids = {p.get("conditionId") for p in fechados if p.get("conditionId")}
    act_map: dict = {}
    for a in activity:
        cid = a.get("conditionId")
        if not cid:
            continue
        slot = act_map.setdefault(cid, {"buys": [], "redeems": []})
        if a.get("type") == "REDEEM" or a.get("side") == "REDEEM":
            slot["redeems"].append(a)
        elif a.get("type") == "BUY" or a.get("side") == "BUY":
            slot["buys"].append(a)

    extras = []
    for cid, mov in act_map.items():
        buys, redeems = mov["buys"], mov["redeems"]
        if not redeems or cid in closed_ids or cid in active_cids:
            continue
        total_bought = sum(_f(b, "size") * _f(b, "price") for b in buys)
        total_redeemed = sum(_f(r, "size", "usdcSize") for r in redeems)
        total_shares = sum(_f(b, "size") for b in buys)
        avg_price = (sum(_f(b, "price") * _f(b, "size") for b in buys) / total_shares) if total_shares else 0.0
        meta = redeems[0] if redeems else (buys[0] if buys else {})
        redeem_ts = max((int(r.get("timestamp") or 0) for r in redeems), default=0)
        extras.append({
            "conditionId": cid,
            "_splitId": cid,
            "_splitTotal": 1,
            "title": meta.get("title") or meta.get("market") or "",
            "asset": meta.get("asset") or "",
            "avgPrice": avg_price,
            "initialValue": total_bought,
            "cashPnl": total_redeemed - total_bought,
            "startDate": (datetime.fromtimestamp(int(buys[0]["timestamp"]), timezone.utc).isoformat()
                          if buys and buys[0].get("timestamp") else None),
            "_redeemTs": redeem_ts or None,
        })
    return fechados + extras


def _split_multibuys(fechados: list, activity: list) -> list:
    """Expande posições com várias compras em entradas individuais (uma por BUY),
    preservando o stake e a odd de cada compra."""
    buy_map: dict = {}
    for a in activity:
        if a.get("type") != "BUY" and a.get("side") != "BUY":
            continue
        cid = a.get("conditionId")
        if not cid:
            continue
        buy_map.setdefault(cid, []).append(a)
    for arr in buy_map.values():
        arr.sort(key=lambda x: int(x.get("timestamp") or 0))

    result = []
    for pos in fechados:
        cid = pos.get("conditionId") or ""
        buys = buy_map.get(cid, [])
        match = [b for b in buys if not (pos.get("asset") and b.get("asset") and pos["asset"] != b["asset"])]

        if len(match) <= 1:
            pos["_splitId"] = cid
            pos["_splitTotal"] = 1
            if len(match) == 1:
                bp = _f(match[0], "price")
                if 0 < bp < 1:
                    pos["avgPrice"] = bp
            result.append(pos)
            continue

        is_win = _f(pos, "cashPnl") > 0
        for i, buy in enumerate(match):
            price = _f(buy, "price")
            shares = _f(buy, "size")
            this_stake = shares * price
            this_pnl = (shares - this_stake) if price > 0 else (_f(pos, "cashPnl") / len(match))
            split = dict(pos)
            split.update({
                "_splitId": f"{cid}__{i}",
                "_splitIndex": i,
                "_splitTotal": len(match),
                "_buyTimestamp": int(buy.get("timestamp") or 0),
                "initialValue": this_stake,
                "avgPrice": price,
                "cashPnl": this_pnl if is_win else -this_stake,
                "conditionId": cid,
            })
            result.append(split)
    return result


# ── Formatação de números (regra global: vírgula, precisão preservada) ──────

def _fmt_money(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def _fmt_odd(x: float) -> str:
    s = f"{x:.12f}".rstrip("0").rstrip(".")
    return s.replace(".", ",") if s else "1"


def _calc_odd(pos: dict) -> float:
    s = _f(pos, "initialValue", "size")
    p = _f(pos, "cashPnl")
    if s > 0 and p > 0:
        return (s + p) / s
    pr = _f(pos, "avgPrice", "price")
    return (1 / pr) if 0 < pr < 1 else 1.0


# ── Pipeline público ────────────────────────────────────────────────────────

async def coletar_bilhetes(wallet: str, parceiro: str) -> list[dict]:
    """Coleta o histórico resolvido da carteira e devolve linhas prontas para o
    `upsert_bilhetes` (dicts com as chaves de _COLS + codigo_bilhete), ordenadas
    da mais antiga para a mais nova (= ordem cronológica de inserção na grade)."""
    wallet = wallet.strip().lower()
    async with httpx.AsyncClient(timeout=30.0) as client:
        positions = await _paginate(client, "positions", wallet, {"sizeThreshold": _SIZE_THRESHOLD})
        activity = await _paginate(client, "activity", wallet, {})

        active_cids = {p.get("conditionId") for p in positions if p.get("conditionId")}
        fechados = [p for p in positions
                    if p.get("redeemable") is True and _f(p, "currentValue") < 0.01]
        fechados = _reconciliar_redeems(fechados, activity, active_cids)
        fechados = _split_multibuys(fechados, activity)

        redeem_cache = _build_redeem_cache(activity)
        hoje = await _ptax(client, datetime.now(BRT))

        linhas = []
        cot_cache: dict = {}
        for pos in fechados:
            title = pos.get("title") or ""
            iso = _data_iso(pos, redeem_cache)
            raw_sport = _detes_raw(title)
            stake_usd = _f(pos, "initialValue", "size")
            cotacao = await _cotacao_para(client, iso, cot_cache, hoje)
            stake_brl = stake_usd * cotacao if cotacao else stake_usd
            pnl = _f(pos, "cashPnl")
            split_total = int(pos.get("_splitTotal") or 1)
            desc = title
            if split_total > 1:
                desc = f"{title} [{int(pos.get('_splitIndex', 0)) + 1}/{split_total}]"
            linhas.append({
                # Ordena por (data, timestamp da compra). O timestamp só existe em
                # compras múltiplas (splits); compra única cai na data → sem ele,
                # todas as únicas empilhavam com chave 0 e a ordem saía embaralhada.
                "_sort": (iso or "9999-12-31", int(pos.get("_buyTimestamp") or 0)),
                "data": _iso_to_br(iso),
                "esporte": _norm_esporte(raw_sport),
                "tipster": "",
                "casa": "Polymarket",
                "parceiro": parceiro,
                "aposta": _categoria(title, raw_sport),
                "descricao": desc,
                "stake": _fmt_money(stake_brl),
                "odd": _fmt_odd(_calc_odd(pos)),
                "resultado": "W" if pnl > 0 else "L",
                "codigo_bilhete": pos.get("_splitId") or pos.get("conditionId") or "",
            })

    linhas.sort(key=lambda r: r["_sort"])
    for r in linhas:
        r.pop("_sort", None)
    return linhas


# ── Dry-run de verificação (não toca em banco) ──────────────────────────────

if __name__ == "__main__":
    import sys

    wallet = sys.argv[1] if len(sys.argv) > 1 else "0x2b3cf54201a00def81ec5d840da7d58fc37e9f22"
    rows = asyncio.run(coletar_bilhetes(wallet, "Feca [Eu]"))
    print(f"# {len(rows)} bilhetes resolvidos coletados\n")
    cols = ["data", "esporte", "tipster", "casa", "parceiro", "aposta",
            "descricao", "stake", "odd", "resultado", "codigo_bilhete"]
    for r in rows[:8]:
        print("\t".join(str(r.get(c, "")) for c in cols))
    if len(rows) > 8:
        print("...")
        for r in rows[-3:]:
            print("\t".join(str(r.get(c, "")) for c in cols))
    # Sanidade
    esportes: dict = {}
    res = {"W": 0, "L": 0}
    for r in rows:
        esportes[r["esporte"]] = esportes.get(r["esporte"], 0) + 1
        res[r["resultado"]] = res.get(r["resultado"], 0) + 1
    print(f"\n# Esportes: {esportes}")
    print(f"# Resultados: {res}")
