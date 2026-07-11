"""
Coletor Polymarket — ingestão automática via API (sem IA de visão).

A Polymarket é uma casa cuja porta de entrada NÃO é screenshot+Claude, e sim a
própria API da carteira. Este módulo traduz posições/atividade on-chain para a
língua global do Planilhador: as 10 colunas do TSV + a 11ª coluna interna
`Código` (= conditionId / _splitId), que alimenta a dedup por ID do repositório.

Decisões (sessão Polymarket-1):
- Reusa o Worker Cloudflare que já destrava a API no Brasil (mesma URL do app
  Polymarket standalone). Do lado do servidor não há CORS; a chamada é direta.
- Converte USD→BRL pela PTAX (BCB) do dia da aposta, recuando até 10 dias para
  atravessar feriados. Para aposta ANTIGA sem PTAX na janela, aborta o sync em vez
  de usar a cotação de hoje (que corromperia o histórico em BRL); só aposta recente
  (≤7 dias) usa hoje como proxy. Ver `_cotacao_para`.
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

# Tamanho de página POR endpoint — espelha o app standalone (index_proxy.html).
# /positions é limitado pela API a páginas pequenas → pedir 100 (igual ao app).
# Pedir 500 aqui faria a 1ª página vir com ~100 itens e a parada `len < 500`
# truncar o histórico em silêncio. /activity aceita páginas de 500.
_PAGE_POSITIONS = 100
_PAGE_ACTIVITY = 500
_SIZE_THRESHOLD = ".1"

# Retry/backoff para soluços transitórios do proxy/PTAX (429/5xx/timeout/conexão).
_RETRY_ATTEMPTS = 3
_RETRY_BASE = 1.0   # espera = base * 2**tentativa → 1s, 2s


class CambioIndisponivel(RuntimeError):
    """PTAX/BCB não retornou cotação — abortamos para NÃO gravar USD como se fosse R$."""


class PolymarketRespostaInesperada(RuntimeError):
    """Endpoint respondeu 200 mas não com uma lista — falha em vez de truncar o histórico em silêncio."""


# ── HTTP ────────────────────────────────────────────────────────────────────

async def _get_retry(client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
    """GET com retry/backoff em erros transitórios (timeout, conexão, 429/5xx)."""
    last_exc: Exception | None = None
    for attempt in range(_RETRY_ATTEMPTS):
        ultima = attempt == _RETRY_ATTEMPTS - 1
        try:
            r = await client.get(url, params=params, headers={"Accept": "application/json"})
            if r.status_code in (429, 500, 502, 503, 504) and not ultima:
                await asyncio.sleep(_RETRY_BASE * (2 ** attempt))
                continue
            r.raise_for_status()
            return r
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_exc = e
            if ultima:
                raise
            await asyncio.sleep(_RETRY_BASE * (2 ** attempt))
    if last_exc:
        raise last_exc
    raise RuntimeError("retry exauriu sem resposta")  # inalcançável


async def _get_json(client: httpx.AsyncClient, url: str, params: dict) -> list:
    r = await _get_retry(client, url, params)
    data = r.json()
    if not isinstance(data, list):
        # 200 com objeto de erro vinha sendo tratado como página vazia → o loop de
        # paginação parava e cortava o histórico sem avisar. Falha alto em vez disso.
        raise PolymarketRespostaInesperada(f"Resposta inesperada (não-lista) de {url}")
    return data


async def _paginate(client: httpx.AsyncClient, path: str, wallet: str,
                    extra: dict, page_size: int) -> list:
    """Busca todas as páginas de um endpoint da carteira até esgotar (sem teto)."""
    out: list = []
    offset = 0
    while True:
        params = {"user": wallet, "limit": page_size, "offset": offset, **extra}
        page = await _get_json(client, f"{POLY_BASE}/{path}", params)
        if not page:
            break
        out.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return out


# ── Cotação USD→BRL (PTAX/BCB) ──────────────────────────────────────────────

async def _ptax(client: httpx.AsyncClient, dia: datetime) -> float | None:
    """cotacaoVenda do dia (M-D-Y). Retorna None se não houver boletim."""
    mdy = f"{dia.month:02d}-{dia.day:02d}-{dia.year:04d}"
    params = {"@dataCotacao": f"'{mdy}'", "$top": "1", "$format": "json"}
    try:
        r = await _get_retry(client, BCB_PTAX, params)
        vals = r.json().get("value", [])
        return float(vals[0]["cotacaoVenda"]) if vals else None
    except Exception:
        return None


_COTACAO_FALLBACK_DIAS = 7   # aposta "recente": usar hoje como proxy é desprezível


async def _cotacao_para(client: httpx.AsyncClient, iso: str, cache: dict, hoje: float | None) -> float | None:
    """Cotação PTAX do dia da aposta, recuando até 10 dias para atravessar feriados
    longos. Memoiza por data ISO.

    Fallback para a cotação de HOJE só quando a aposta é recente (≤ 7 dias): aí a
    variação cambial é desprezível. Para uma aposta ANTIGA sem PTAX na janela,
    devolve None em vez de usar o câmbio de hoje — usar a cotação atual num bilhete
    de 1-2 anos atrás escalaria stake E P/L em BRL para um valor historicamente
    errado (e não-determinístico entre re-syncs). O chamador então aborta o sync
    com `CambioIndisponivel` — melhor recusar do que gravar histórico corrompido.
    """
    if not iso:
        return hoje
    if iso in cache:
        return cache[iso]
    base = datetime.strptime(iso, "%Y-%m-%d")
    val = None
    for back in range(0, 10):   # janela ampla: PTAX tem décadas de histórico, achar a data é regra
        val = await _ptax(client, base - timedelta(days=back))
        if val:
            break
    if not val:
        # Sem PTAX na janela: só cai para "hoje" se a aposta for recente o bastante
        # para a diferença ser irrelevante; senão devolve None (chamador aborta).
        idade_dias = (datetime.now(BRT).date() - base.date()).days
        if idade_dias <= _COTACAO_FALLBACK_DIAS:
            val = hoje
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

# Prefixo do slug do evento (ex.: "mlb-chc-stl-2026-05-31" → "mlb") → esporte
# granular. O slug é MUITO mais confiável que o título: esportes tradicionais na
# Polymarket são titulados por nome de time/jogador (ex.: "Yankees vs Red Sox",
# "Sinner vs Ruud"), que o regex de título não pega; mas o slug é sempre prefixado
# pela liga/esporte. Validado contra a carteira real: derruba os "Outro" a zero.
_SLUG_SPORT = {
    # e-sports (todos colapsam em "E-Sports" no _norm_esporte)
    "lol": "E-Sports", "lpl": "E-Sports", "lck": "E-Sports", "lec": "E-Sports",
    "lcs": "E-Sports", "cs2": "E-Sports", "csgo": "E-Sports", "cs": "E-Sports",
    "val": "E-Sports", "valorant": "E-Sports", "vct": "E-Sports", "dota2": "E-Sports",
    "dota": "E-Sports", "cod": "E-Sports", "codmw": "E-Sports", "cdl": "E-Sports",
    "rl": "E-Sports", "rlcs": "E-Sports", "ow": "E-Sports", "ow2": "E-Sports",
    "r6": "E-Sports", "pubg": "E-Sports", "sc2": "E-Sports", "apex": "E-Sports",
    "mlbb": "E-Sports", "kog": "E-Sports", "honor": "E-Sports",
    # tênis
    "atp": "Tênis", "wta": "Tênis", "itf": "Tênis", "tennis": "Tênis",
    # basquete
    "nba": "Basquete", "wnba": "Basquete", "euroleague": "Basquete",
    "ncaab": "Basquete", "basketball": "Basquete",
    # baseball
    "mlb": "Baseball", "npb": "Baseball", "kbo": "Baseball", "baseball": "Baseball",
    # futebol americano
    "nfl": "Futebol Americano", "ncaaf": "Futebol Americano", "cfb": "Futebol Americano",
    # hóquei
    "nhl": "Hóquei", "hockey": "Hóquei",
    # futebol
    "epl": "Futebol", "ucl": "Futebol", "uel": "Futebol", "uecl": "Futebol",
    "uclq": "Futebol", "laliga": "Futebol", "seriea": "Futebol", "bundesliga": "Futebol",
    "ligue1": "Futebol", "eredivisie": "Futebol", "mls": "Futebol", "fif": "Futebol",
    "fifwc": "Futebol", "wc": "Futebol", "copa": "Futebol", "brasileirao": "Futebol",
    "libertadores": "Futebol", "soccer": "Futebol",
    # mma
    "ufc": "MMA", "mma": "MMA", "bellator": "MMA", "pfl": "MMA",
    # dardos / f1 / golf / vôlei / rugby / snooker (snooker → Outro no _norm_esporte)
    "pdc": "Dardos", "darts": "Dardos", "f1": "F1", "formula1": "F1",
    "pga": "Golf", "golf": "Golf", "liv": "Golf", "volleyball": "Vôlei",
    "vnl": "Vôlei", "rugby": "Rugby", "snooker": "Snooker",
}


def _detes_from_slug(slug: str) -> str | None:
    """Esporte a partir do prefixo do slug do evento. None se ausente/desconhecido."""
    if not slug:
        return None
    return _SLUG_SPORT.get(slug.lower().split("-")[0])


def _detes_raw(title: str, slug: str = "") -> str:
    """Detecção de esporte. Tenta o prefixo do slug do evento primeiro (sinal forte
    e confiável); só cai no regex do título (en-US) quando o slug está ausente ou
    com prefixo desconhecido. Granular o suficiente para a categoria; a coluna usa
    a versão normalizada (_norm_esporte)."""
    by_slug = _detes_from_slug(slug)
    if by_slug:
        return by_slug
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
        # invariante global: estatística de E-Sports é E-Sports Props, nunca Player Props
        return "E-Sports Props" if raw_sport == "E-Sports" else "Player Props"
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
        # fallback alinhado ao app standalone (size ‖ amount); usdcSize não existe na activity
        total_redeemed = sum(_f(r, "size", "amount") for r in redeems)
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
        # Distribui o valor de mercado da posição-mãe proporcional ao stake de cada
        # compra (espelha o splitMultiBuys do app). Sem isto, cada split herdaria o
        # currentValue cheio → o dashboard somava N× em posições ativas multi-compra.
        total_stake = sum(_f(b, "size") * _f(b, "price") for b in match)
        pos_cv = _f(pos, "currentValue")
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
                "currentValue": (pos_cv * this_stake / total_stake) if total_stake else pos_cv,
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
    """Odd = retorno/investimento (payout ratio) = 1/preço médio de compra. UMA odd
    para tudo — resultado E indicadores (odd média): a odd do resultado se ganhou, ou
    do POSSÍVEL resultado se perdeu/ativa (decisão do Feca). Não usa (stake+lucro)/stake:
    o cashPnl carrega taxa/slippage, e a odd da planilha é a limpa (1/preço). Como cada
    cota paga $1 no acerto, 1/preço é exatamente retorno÷investimento se vencer."""
    pr = _f(pos, "avgPrice", "price")
    return (1 / pr) if 0 < pr < 1 else 1.0


# ── Pipeline público ────────────────────────────────────────────────────────

async def coletar_bilhetes(wallet: str, parceiro: str) -> list[dict]:
    """Coleta o histórico resolvido da carteira e devolve linhas prontas para o
    `upsert_bilhetes` (dicts com as chaves de _COLS + codigo_bilhete), ordenadas
    da mais antiga para a mais nova (= ordem cronológica de inserção na grade)."""
    wallet = wallet.strip().lower()
    async with httpx.AsyncClient(timeout=30.0) as client:
        positions = await _paginate(client, "positions", wallet,
                                    {"sizeThreshold": _SIZE_THRESHOLD}, _PAGE_POSITIONS)
        activity = await _paginate(client, "activity", wallet, {}, _PAGE_ACTIVITY)

        active_cids = {p.get("conditionId") for p in positions if p.get("conditionId")}
        fechados = [p for p in positions
                    if p.get("redeemable") is True and _f(p, "currentValue") < 0.01]
        fechados = _reconciliar_redeems(fechados, activity, active_cids)
        fechados = _split_multibuys(fechados, activity)

        redeem_cache = _build_redeem_cache(activity)
        hoje = None
        for _back in range(0, 6):   # PTAX não publica fim de semana/feriado → recua
            hoje = await _ptax(client, datetime.now(BRT) - timedelta(days=_back))
            if hoje:
                break

        linhas = []
        cot_cache: dict = {}
        for pos in fechados:
            title = pos.get("title") or ""
            iso = _data_iso(pos, redeem_cache)
            raw_sport = _detes_raw(title, pos.get("eventSlug") or pos.get("slug") or "")
            stake_usd = _f(pos, "initialValue", "size")
            cotacao = await _cotacao_para(client, iso, cot_cache, hoje)
            if not cotacao:
                # Sem cotação NÃO gravamos USD como se fosse R$ (corromperia stake e P/L).
                raise CambioIndisponivel(
                    "Câmbio (PTAX/BCB) indisponível agora — não foi possível converter "
                    "USD→BRL. Tente sincronizar novamente em alguns minutos."
                )
            stake_brl = stake_usd * cotacao
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
                "stake_usd": round(stake_usd, 2),   # valor original (saiu da conta) p/ referência na grade
                "odd": _fmt_odd(_calc_odd(pos)),
                # pnl exatamente zero = retornou o stake → V (P/L 0), não L (que daria -stake).
                "resultado": "W" if pnl > 0.005 else ("L" if pnl < -0.005 else "V"),
                "codigo_bilhete": pos.get("_splitId") or pos.get("conditionId") or "",
            })

    linhas.sort(key=lambda r: r["_sort"])
    for r in linhas:
        r.pop("_sort", None)
    return linhas


# ── Dashboard ao vivo: posições ativas + saldos da carteira ─────────────────

# Tokens de colateral na Polygon (ERC-20, 6 casas decimais)
_PUSD = "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"   # pUSD (colateral atual)
_USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC.e (legado)
_POLYGON_RPCS = [
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon.llamarpc.com",
    "https://rpc.ankr.com/polygon",
    "https://polygon-rpc.com",
    "https://polygon.drpc.org",
    "https://1rpc.io/matic",
]


async def _rpc_balance(client: httpx.AsyncClient, token: str, wallet: str) -> float | None:
    """Saldo ERC-20 (balanceOf) on-chain, em unidades (6 casas). Tenta os RPCs em ordem.

    Devolve `None` quando TODOS os RPCs falham — distinto de `0.0` (saldo genuinamente
    zero). Sem essa distinção, uma queda dos RPCs públicos mostrava "cash = R$0" como se
    a carteira estivesse vazia (achado #47). O chamador trata o None como "indisponível".
    """
    data = "0x70a08231" + wallet.replace("0x", "").lower().rjust(64, "0")
    payload = {"jsonrpc": "2.0", "method": "eth_call",
               "params": [{"to": token, "data": data}, "latest"], "id": 1}
    for rpc in _POLYGON_RPCS:
        try:
            r = await client.post(rpc, json=payload, timeout=15.0)
            res = r.json().get("result")
            if res and len(res) > 2:
                return int(res, 16) / 1e6
        except Exception:
            continue
    return None


async def _portfolio(client: httpx.AsyncClient, wallet: str) -> float:
    """Valor de mercado das posições ativas, via endpoint /value do Worker."""
    try:
        r = await client.get(f"{POLY_BASE}/value", params={"user": wallet},
                             headers={"Accept": "application/json"})
        data = r.json()
        if isinstance(data, list) and data:
            return float(data[0].get("value") or 0)
        if isinstance(data, dict) and data.get("value") is not None:
            return float(data["value"])
    except Exception:
        pass
    return 0.0


def _rotulo_relativo(iso: str) -> str:
    """'hoje' / 'amanhã' / 'ontem' para a data do evento; '' fora dessa janela."""
    if not iso:
        return ""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
    except Exception:
        return ""
    hoje = datetime.now(BRT).date()
    delta = (d - hoje).days
    return {0: "hoje", 1: "amanhã", -1: "ontem"}.get(delta, "")


async def coletar_dashboard(wallet: str) -> dict:
    """Estado ao vivo da carteira: contagem/portfólio/cash/total + lista de posições
    ativas (com colunas do dashboard). NÃO toca no banco; o tipster é mesclado pela rota."""
    wallet = wallet.strip().lower()
    async with httpx.AsyncClient(timeout=30.0) as client:
        positions = await _paginate(client, "positions", wallet,
                                    {"sizeThreshold": _SIZE_THRESHOLD}, _PAGE_POSITIONS)
        activity = await _paginate(client, "activity", wallet, {}, _PAGE_ACTIVITY)

        # Carteira proxy real (pode diferir do endereço informado) para o saldo on-chain
        proxy = wallet
        for fonte in (positions, activity):
            if fonte and fonte[0].get("proxyWallet"):
                proxy = str(fonte[0]["proxyWallet"]).lower()
                break

        ativas_raw = [p for p in positions
                      if not (p.get("redeemable") is True and _f(p, "currentValue") < 0.01)]
        ativas_raw = _split_multibuys(ativas_raw, activity)

        pusd = await _rpc_balance(client, _PUSD, proxy)
        usdce = await _rpc_balance(client, _USDC_E, proxy)
        # Ao menos um RPC respondeu → cash confiável. Nenhum respondeu → indisponível
        # (None), NÃO zero — senão "cash R$0" mente sobre a carteira (#47).
        saldo_ok = (pusd is not None) or (usdce is not None)
        cash = (pusd or 0.0) + (usdce or 0.0)
        portfolio = await _portfolio(client, wallet)
        if portfolio <= 0:
            portfolio = sum(_f(p, "currentValue") for p in ativas_raw)
        hoje = None
        for _back in range(0, 6):   # PTAX não publica fim de semana/feriado → recua
            hoje = await _ptax(client, datetime.now(BRT) - timedelta(days=_back))
            if hoje:
                break

    ativas = []
    for pos in ativas_raw:
        title = pos.get("title") or ""
        raw_sport = _detes_raw(title, pos.get("eventSlug") or pos.get("slug") or "")  # mesma detecção do coletar_bilhetes
        split_total = int(pos.get("_splitTotal") or 1)
        mercado = title
        if split_total > 1:
            mercado = f"{title} [{int(pos.get('_splitIndex', 0)) + 1}/{split_total}]"
        stake_usd = _f(pos, "initialValue", "size")
        valor_atual = _f(pos, "currentValue")
        pnl_pct = ((valor_atual - stake_usd) / stake_usd * 100) if stake_usd else 0.0
        # Odd da ativa = SEMPRE a odd de entrada (1/preço de compra). Não usar _calc_odd:
        # com P&L não-realizado positivo ele daria o valor de mercado, não a odd apostada.
        _pr = _f(pos, "avgPrice", "price")
        odd_entrada = (1 / _pr) if 0 < _pr < 1 else 1.0
        end_iso = ""
        ed = pos.get("endDate")
        if isinstance(ed, str):
            m = re.match(r"(\d{4}-\d{2}-\d{2})", ed)
            if m:
                end_iso = m.group(1)
        ativas.append({
            "codigo": pos.get("_splitId") or pos.get("conditionId") or "",
            "mercado": mercado,
            "esporte": _norm_esporte(raw_sport),
            "aposta": _categoria(title, raw_sport),
            "data": _iso_to_br(end_iso),
            "data_rel": _rotulo_relativo(end_iso),
            "stake_usd": round(stake_usd, 2),
            "valor_atual": round(valor_atual, 2),
            "pnl_pct": round(pnl_pct, 1),
            "odd": _fmt_odd(odd_entrada),
            "status": "ativa",
        })
    ativas.sort(key=lambda a: (a["data"] or "9999"))

    total = cash + portfolio
    return {
        "count": len(ativas),
        "portfolio": round(portfolio, 2),
        # Saldo indisponível → cash/total viram None (a UI mostra "—", não R$0).
        # Portfólio segue vindo do Worker /value (não depende dos RPCs).
        "cash": round(cash, 2) if saldo_ok else None,
        "total": round(total, 2) if saldo_ok else None,
        "saldo_indisponivel": not saldo_ok,
        "cotacao": round(hoje, 4) if hoje else None,
        "ativas": ativas,
    }


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
