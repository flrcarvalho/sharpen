"""Coletor da Kalshi (s435): a conta do usuário pela API, sem IA no caminho.

Irmã da Polymarket (`polymarket.py`), com uma diferença que muda o desenho: a conta é
PRIVADA. Toda chamada vai assinada com a chave do usuário (Ed25519 ou RSA-PSS sobre
`timestamp + MÉTODO + caminho sem query`), e a chave só é aceita com escopo SÓ LEITURA
(`GET /api_keys` → `scopes: ["read"]`). Chave que pode operar movimenta dinheiro do
usuário, e o Sharpen não precisa disso para nada.

As regras de tradução estão em `casas/CASA_KALSHI.md`. Em resumo:
  - uma ORDEM é uma aposta; código = `order_id` (estável: não muda quando entra outra
    ordem no mesmo mercado, ao contrário do `__i` da Polymarket);
  - stake = custo das cotas + TAXA (a régua da Polymarket, decisão do Feca de 30/10);
    a taxa viaja à parte em `taxa_orig`, só como informação;
  - resultado pelo DINHEIRO da liquidação (cotas × US$ 1,00 do lado certo), com a régua
    global de cashout: 0 → L; = stake → V; ≠ → W com odd = retorno ÷ stake;
  - data = a do evento, pelo ticker (`…-26OCT29…`); esporte pelo `tags` da série;
    categoria pelo `product_metadata.scope` da série.

O que a amostra de 30/10/2026 NÃO cobriu (venda antes de liquidar, mercado anulado ou
escalar) não é adivinhado: a ordem fica fora do lote e o sync AVISA, nomeando o mercado.
"""
from __future__ import annotations

import asyncio
import base64
import re
import time
from datetime import datetime, timedelta, timezone

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

import cambio

KALSHI_BASE = "https://external-api.kalshi.com"
PREFIXO = "/trade-api/v2"
CASA = "Kalshi"
BRT = timezone(timedelta(hours=-3))

_PAGINA = 200
_MAX_PAGINAS = 500              # teto de sanidade (anti loop de cursor preso)
_RETRY = 3
_RETRY_BASE = 1.0               # 1 s, 2 s
_EPS_USD = 0.005                # banda neutra em USD: abaixo disso é arredondamento


class KalshiErro(Exception):
    """Falha de leitura da Kalshi com mensagem que pode ir para a tela."""


class KalshiChaveInvalida(KalshiErro):
    """A chave não carrega, não autentica ou não é só de leitura."""


# ── Chave e assinatura ──────────────────────────────────────────────────────

def carregar_chave(pem: str):
    """A chave privada colada pelo usuário. O PEM não diz o tipo (PKCS#8 RSA também abre
    com `BEGIN PRIVATE KEY`): ele sai da chave carregada. Aceita o bloco em UMA linha só,
    que é como a tela da Kalshi entrega quando se copia o texto."""
    texto = _normalizar_pem(pem)
    try:
        chave = serialization.load_pem_private_key(texto.encode(), password=None)
    except Exception as exc:
        raise KalshiChaveInvalida("A chave privada não é válida. Copie o bloco inteiro, "
                                  "de -----BEGIN PRIVATE KEY----- até -----END PRIVATE KEY-----.") from exc
    if not isinstance(chave, (ed25519.Ed25519PrivateKey, rsa.RSAPrivateKey)):
        raise KalshiChaveInvalida("Tipo de chave não suportado (use Ed25519 ou RSA).")
    return chave


_RE_PEM = re.compile(r"-----BEGIN ([A-Z ]+)-----(.*?)-----END \1-----", re.S)


def _normalizar_pem(pem: str) -> str:
    """Remonta o PEM com quebras de linha. A cópia da tela pode vir numa linha só, com
    espaços no lugar das quebras, e o parser exige o corpo em linhas próprias."""
    m = _RE_PEM.search(pem or "")
    if not m:
        return pem or ""
    corpo = re.sub(r"\s+", "", m.group(2))
    linhas = [corpo[i:i + 64] for i in range(0, len(corpo), 64)]
    return f"-----BEGIN {m.group(1)}-----\n" + "\n".join(linhas) + f"\n-----END {m.group(1)}-----\n"


def _assinar(chave, ts: str, metodo: str, caminho: str) -> str:
    msg = (ts + metodo.upper() + caminho).encode()
    if isinstance(chave, ed25519.Ed25519PrivateKey):
        sig = chave.sign(msg)
    else:
        sig = chave.sign(msg, padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                          salt_length=padding.PSS.DIGEST_LENGTH),
                         hashes.SHA256())
    return base64.b64encode(sig).decode()


class Credencial:
    """Key ID + chave carregada. Nunca vai para log nem para resposta."""

    def __init__(self, key_id: str, pem: str):
        self.key_id = (key_id or "").strip()
        if not re.fullmatch(r"[0-9a-fA-F-]{20,64}", self.key_id):
            raise KalshiChaveInvalida("O API key id não é válido (é o código no formato "
                                      "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx).")
        self.chave = carregar_chave(pem)

    def __repr__(self) -> str:   # nada de chave em traceback
        return f"Credencial(key_id={self.key_id[:8]}…)"


# ── HTTP ────────────────────────────────────────────────────────────────────

async def _get(client: httpx.AsyncClient, cred: Credencial, rota: str, params: dict | None = None) -> dict:
    caminho = f"{PREFIXO}/{rota}"
    ultimo = None
    for tentativa in range(_RETRY):
        ts = str(int(time.time() * 1000))
        headers = {"KALSHI-ACCESS-KEY": cred.key_id, "KALSHI-ACCESS-TIMESTAMP": ts,
                   "KALSHI-ACCESS-SIGNATURE": _assinar(cred.chave, ts, "GET", caminho)}
        try:
            r = await client.get(KALSHI_BASE + caminho, params=params or {}, headers=headers)
        except httpx.HTTPError as exc:
            ultimo = exc
        else:
            if r.status_code == 401:
                raise KalshiChaveInvalida("A Kalshi recusou a chave. Confira o API key id e a "
                                          "chave privada, ou crie uma chave nova.")
            if r.status_code == 200:
                return r.json()
            if r.status_code not in (429, 500, 502, 503, 504):
                raise KalshiErro(f"A Kalshi respondeu {r.status_code} em /{rota}.")
            ultimo = KalshiErro(f"A Kalshi respondeu {r.status_code} em /{rota}.")
        if tentativa < _RETRY - 1:
            await asyncio.sleep(_RETRY_BASE * 2 ** tentativa)
    raise KalshiErro(f"A Kalshi não respondeu em /{rota}. Tente de novo em alguns minutos.") from ultimo


async def _paginar(client: httpx.AsyncClient, cred: Credencial, rota: str, chave_lista: str,
                   params: dict | None = None) -> list[dict]:
    """Lista inteira por cursor. Falha ALTO se o formato mudar: lista truncada em
    silêncio é aposta sumida."""
    out: list[dict] = []
    cursor = None
    for _ in range(_MAX_PAGINAS):
        p = {"limit": _PAGINA, **(params or {})}
        if cursor:
            p["cursor"] = cursor
        data = await _get(client, cred, rota, p)
        if not isinstance(data, dict) or not isinstance(data.get(chave_lista), list):
            raise KalshiErro(f"Resposta inesperada de /{rota}.")
        out.extend(data[chave_lista])
        cursor = data.get("cursor")
        if not cursor:
            return out
    raise KalshiErro(f"A paginação de /{rota} não terminou.")


async def conferir_chave(client: httpx.AsyncClient, cred: Credencial) -> None:
    """A chave autentica E é só de leitura. A lista de chaves da conta traz os escopos;
    a nossa tem de ter `read` e nada mais."""
    data = await _get(client, cred, "api_keys")
    minha = next((k for k in data.get("api_keys") or [] if k.get("api_key_id") == cred.key_id), None)
    if minha is None:
        raise KalshiChaveInvalida("A Kalshi não listou esta chave na conta.")
    escopos = set(minha.get("scopes") or [])
    if escopos != {"read"}:
        raise KalshiChaveInvalida("Esta chave pode operar na sua conta. O Sharpen só aceita "
                                  "chave SÓ LEITURA: crie outra marcando apenas \"Read all data\".")


# ── Metadados (fixos depois de criados: cache de módulo entre syncs) ─────────

_CACHE_MERCADO: dict[str, dict] = {}
_CACHE_EVENTO: dict[str, dict] = {}
_CACHE_SERIE: dict[str, dict] = {}


async def _mercado(client, cred, ticker: str) -> dict:
    if ticker not in _CACHE_MERCADO:
        _CACHE_MERCADO[ticker] = (await _get(client, cred, f"markets/{ticker}")).get("market") or {}
    return _CACHE_MERCADO[ticker]


async def _evento(client, cred, ev: str) -> dict:
    if ev not in _CACHE_EVENTO:
        data = await _get(client, cred, f"events/{ev}", {"with_nested_markets": "false"})
        _CACHE_EVENTO[ev] = data.get("event") or {}
    return _CACHE_EVENTO[ev]


async def _serie(client, cred, s: str) -> dict:
    if s not in _CACHE_SERIE:
        _CACHE_SERIE[s] = (await _get(client, cred, f"series/{s}")).get("series") or {}
    return _CACHE_SERIE[s]


def _serie_do_evento(ev: str) -> str:
    return (ev or "").split("-")[0]


# ── Tradução (PURA) ─────────────────────────────────────────────────────────

# `tags` da série → esporte canônico (os mesmos nomes da Polymarket, `_NORM_ESPORTE`).
# Só o medido entra aqui; tag desconhecida cai em `Outro` e o ensaio lista qual foi.
ESPORTE_POR_TAG = {
    "Basketball": "Basquete",
}

# `product_metadata.scope` da série → categoria do `MASTER_APOSTAS §3`. Só o medido.
CATEGORIA_POR_ESCOPO = {
    "Double Double": "Double-Double",
    "Player Assists": "Assistência",
}

_MESES = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
_RE_DATA_TICKER = re.compile(r"-(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})")


def data_do_ticker(ticker: str) -> str:
    """`KXNBA2D-26OCT29MEMPOR` → `2026-10-29`. É a data do jogo como a Kalshi publica;
    sem ela, '' (o chamador cai no fallback)."""
    m = _RE_DATA_TICKER.search(ticker or "")
    if not m:
        return ""
    try:
        return datetime(2000 + int(m.group(1)), _MESES[m.group(2)], int(m.group(3))).date().isoformat()
    except ValueError:
        return ""


def _iso_brt(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return dt.astimezone(BRT).date().isoformat()


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _fmt_money(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def _fmt_odd(x: float) -> str:
    s = f"{x:.12f}".rstrip("0").rstrip(".")
    return s.replace(".", ",") if s else "1"


def _iso_to_br(iso: str) -> str:
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def agrupar_ordens(fills: list[dict]) -> tuple[dict[str, dict], list[str]]:
    """Os fills somados por `order_id`: cotas, custo (cotas × preço do lado) e taxa.

    Devolve (ordens de COMPRA, tickers com VENDA). Venda antes de liquidar é cashout,
    que a amostra não cobriu: o mercado inteiro fica fora do lote, nomeado no aviso,
    em vez de virar um resultado chutado."""
    ordens: dict[str, dict] = {}
    vendas: set[str] = set()
    vistos: set[str] = set()
    for f in fills:
        # O mesmo fill pode estar no live e no arquivado perto do corte: conta uma vez.
        fid = f.get("fill_id") or f.get("trade_id")
        if fid:
            if fid in vistos:
                continue
            vistos.add(fid)
        ticker = f.get("ticker") or f.get("market_ticker") or ""
        if (f.get("action") or "").lower() != "buy":
            vendas.add(ticker)
            continue
        lado = (f.get("side") or "").lower()
        preco = _f(f.get(f"{lado}_price_dollars"))
        cotas = _f(f.get("count_fp"))
        o = ordens.setdefault(f["order_id"], {
            "order_id": f["order_id"], "ticker": ticker, "lado": lado,
            "cotas": 0.0, "custo": 0.0, "taxa": 0.0, "criada": f.get("created_time") or ""})
        o["cotas"] += cotas
        o["custo"] += cotas * preco
        o["taxa"] += _f(f.get("fee_cost"))
        o["criada"] = min(o["criada"], f.get("created_time") or o["criada"])
    for t in vendas:
        for oid in [k for k, o in ordens.items() if o["ticker"] == t]:
            del ordens[oid]
    return ordens, sorted(vendas)


def liquidacao(ordem: dict, settlement: dict | None) -> tuple[str, float] | None:
    """(resultado, odd) pelo DINHEIRO da liquidação; None = ainda aberta.

    O contrato paga US$ 1,00 por cota do lado certo. Resultado que não é `yes`/`no`
    (anulado, escalar) não foi medido: levanta, para o chamador avisar em vez de gravar."""
    stake = ordem["custo"] + ordem["taxa"]
    if settlement is None:
        return None
    res = (settlement.get("market_result") or "").lower()
    if res not in ("yes", "no"):
        raise KalshiErro(f"liquidação '{res or 'vazia'}' não medida")
    retorno = ordem["cotas"] * (1.0 if res == ordem["lado"] else 0.0)
    if retorno <= _EPS_USD:
        return "L", ordem["cotas"] / stake
    if abs(retorno - stake) <= _EPS_USD:
        return "V", retorno / stake
    return "W", retorno / stake


def esporte_e_jogo(series: list[dict], eventos: list[str]) -> str:
    """Esporte de uma aposta pelas séries das pernas (`MASTER_ESPORTES §2`): um só
    esporte e menos de 3 jogos → ele; senão `Múltiplos`. Sem tag conhecida → `Outro`."""
    esportes = {ESPORTE_POR_TAG.get(t) for s in series for t in (s.get("tags") or [])} - {None}
    jogos = {ev.split("-", 1)[1] if "-" in ev else ev for ev in eventos}
    if len(esportes) > 1 or (len(esportes) == 1 and len(jogos) >= 3):
        return "Múltiplos"
    return esportes.pop() if esportes else "Outro"


def _jogo(evento: dict) -> str:
    """`Memphis vs Portland: Double Double` → `Memphis vs Portland`."""
    return (evento.get("title") or "").split(":")[0].strip()


def descricao_perna(mercado: dict, lado: str) -> str:
    titulo = (mercado.get("title") or "").strip()
    return f"Não: {titulo}" if lado == "no" else titulo


def montar_linha(ordem: dict, parceiro: str, *, esporte: str, aposta: str, descricao: str,
                 iso: str, cotacao: float, resultado: str, odd: float) -> dict:
    stake_usd = ordem["custo"] + ordem["taxa"]
    return {
        "_sort": (iso or "9999-12-31", ordem["criada"]),
        "data": _iso_to_br(iso),
        "esporte": esporte,
        "tipster": "",
        "casa": CASA,
        "parceiro": parceiro,
        "aposta": aposta,
        "descricao": descricao,
        "stake": _fmt_money(stake_usd * cotacao),
        "stake_usd": round(stake_usd, 2),
        "moeda": "USD",
        "stake_orig": round(stake_usd, 2),
        "cotacao": round(cotacao, 6),
        "taxa_orig": round(ordem["taxa"], 6),   # informação: a taxa JÁ está na stake
        "odd": _fmt_odd(odd),
        "resultado": resultado,
        "codigo_bilhete": ordem["order_id"],
    }


# ── Coleta ──────────────────────────────────────────────────────────────────

async def _descrever(client, cred, ticker: str, lado: str) -> dict:
    """Esporte, categoria, descrição e data de UM mercado (simples ou combo)."""
    m = await _mercado(client, cred, ticker)
    pernas = m.get("mve_selected_legs") or []
    if pernas:
        mercados = [await _mercado(client, cred, p["market_ticker"]) for p in pernas]
        evs = [p["event_ticker"] for p in pernas]
        eventos = [await _evento(client, cred, ev) for ev in evs]
        series = [await _serie(client, cred, _serie_do_evento(ev)) for ev in evs]
        jogos = list(dict.fromkeys(_jogo(e) for e in eventos))
        textos = [descricao_perna(mk, p.get("side", "yes")) for mk, p in zip(mercados, pernas)]
        if len(jogos) == 1:
            desc = f"{jogos[0]} - " + " // ".join(textos)
        else:
            desc = " // ".join(f"{_jogo(e)} - {t}" for e, t in zip(eventos, textos))
        datas = [d for d in (data_do_ticker(ev) for ev in evs) if d]
        escopos = [((s.get("product_metadata") or {}).get("scope") or "") for s in series]
        return {"esporte": esporte_e_jogo(series, evs), "aposta": "Múltipla", "descricao": desc,
                "iso": max(datas) if datas else "", "escopos": escopos,
                "tags": [t for s in series for t in (s.get("tags") or [])]}
    ev = m.get("event_ticker") or ""
    evento = await _evento(client, cred, ev)
    serie = await _serie(client, cred, _serie_do_evento(ev))
    escopo = (serie.get("product_metadata") or {}).get("scope") or ""
    titulo = descricao_perna(m, lado)
    jogo = _jogo(evento)
    desc = titulo if not jogo or titulo.startswith(jogo) else f"{jogo} - {titulo}"
    return {"esporte": esporte_e_jogo([serie], [ev]), "descricao": desc,
            "aposta": CATEGORIA_POR_ESCOPO.get(escopo, "Outros"),
            "iso": data_do_ticker(ev), "escopos": [escopo], "tags": serie.get("tags") or []}


async def coletar(cred: Credencial, parceiro: str) -> dict:
    """Lê a conta inteira e devolve as linhas prontas para o `upsert_bilhetes`.

    `{"linhas": [...], "alertas": [...], "nao_mapeado": {...}, "caixa": {...}}`. Não grava
    nada: quem grava é a rota, e o ensaio usa isto puro."""
    alertas: list[str] = []
    nao_mapeado = {"tags": set(), "escopos": set()}
    async with httpx.AsyncClient(timeout=30.0) as client:
        await conferir_chave(client, cred)
        fills = (await _paginar(client, cred, "portfolio/fills", "fills")
                 + await _paginar(client, cred, "historical/fills", "fills"))
        settlements = await _paginar(client, cred, "portfolio/settlements", "settlements")
        hist_pos = await _paginar(client, cred, "historical/positions", "market_positions")
        if hist_pos:
            # Liquidação arquivada não vem em /portfolio/settlements; sem amostra do formato
            # dela, avisamos em vez de tratar a ordem como aberta para sempre.
            alertas.append(f"{len(hist_pos)} posição(ões) no histórico arquivado da Kalshi ainda "
                           "não são lidas pelo Sharpen.")
        por_ticker = {s["ticker"]: s for s in settlements}

        ordens, vendas = agrupar_ordens(fills)
        if vendas:
            alertas.append("Venda antes da liquidação ainda não é lida (fora do lote): "
                           + ", ".join(vendas))

        linhas, isos = [], []
        brutas = []
        for o in ordens.values():
            try:
                liq = liquidacao(o, por_ticker.get(o["ticker"]))
            except KalshiErro as exc:
                alertas.append(f"Mercado {o['ticker']} fora do lote: {exc}.")
                continue
            d = await _descrever(client, cred, o["ticker"], o["lado"])
            for t in d["tags"]:
                if t not in ESPORTE_POR_TAG:
                    nao_mapeado["tags"].add(t)
            for e in d["escopos"]:
                if e and e not in CATEGORIA_POR_ESCOPO:
                    nao_mapeado["escopos"].add(e)
            s = por_ticker.get(o["ticker"]) or {}
            iso = d["iso"] or _iso_brt(s.get("settled_time") or "") or _iso_brt(o["criada"])
            brutas.append((o, d, iso, liq))
            isos.append(iso)

        await cambio.carregar("USD", isos)
        for o, d, iso, liq in brutas:
            cot = cambio.cotacao("USD", iso)
            if not cot:
                raise KalshiErro(f"Sem cotação do dólar para {_iso_to_br(iso)}. Tente de novo mais tarde.")
            resultado, odd = liq if liq else ("", o["cotas"] / (o["custo"] + o["taxa"]))
            linhas.append(montar_linha(o, parceiro, esporte=d["esporte"], aposta=d["aposta"],
                                       descricao=d["descricao"], iso=iso, cotacao=cot,
                                       resultado=resultado, odd=odd))
        linhas.sort(key=lambda r: r["_sort"])

        caixa = await _coletar_caixa(client, cred)
    return {"linhas": linhas, "alertas": alertas, "caixa": caixa,
            "nao_mapeado": {k: sorted(v) for k, v in nao_mapeado.items()}}


async def _coletar_caixa(client, cred) -> dict:
    """Saldo e movimentos da conta (etapa 4 usa; aqui só lê). Nunca derruba as apostas."""
    try:
        bal = await _get(client, cred, "portfolio/balance")
        dep = await _paginar(client, cred, "portfolio/deposits", "deposits")
        saq = await _paginar(client, cred, "portfolio/withdrawals", "withdrawals")
    except KalshiErro as exc:
        return {"erro": str(exc)}
    return {"saldo": _f(bal.get("balance_dollars")),
            "depositos": [d for d in dep if d.get("status") == "applied"],
            "saques": [w for w in saq if w.get("status") == "applied"]}
