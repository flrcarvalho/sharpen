"""Adaptador da Stake.com (família `stc`, a Stake INTERNACIONAL, plataforma própria GraphQL; s428).

⚠ Não é a `STAKE` (stake.bet.br, Kambi atrás de REST, sem adaptador). Casas e famílias diferentes.

O cru é o que o `stc_inject.js` monta: `{iid, bet}`, com `bet` = o objeto da aposta como a casa
mandou (sem o `user`, que traz o nome da conta) e `iid` ao lado, porque no histórico ele mora fora
da aposta e a props (`SwishBet`) não o repete. A leitura de cada campo é a do `formatTicketSTC`
(`content.js`) e da `CASA_STAKECOM.md`; escrito das fixtures `extensor/harness/fixtures/stakecom.
*.json` (15 props liquidadas e 3 abertas de Fórmula 1, conta do Feca em USDT, 25/10/2026),
cruzadas com os cards de `/pt/my-bets/sports`.

  • CÓDIGO: o número do `iid` (`sport:676297455` → `676297455`, o "ID da Aposta" do modal).
  • DINHEIRO em número, na moeda da conta (`currency`, minúsculo na casa). `payout` é o RETORNO.
  • ODD da casa: `odds` na props, `potentialMultiplier` na aposta comum (o card arredonda a 2).
  • status: `active` / `confirmed` aberta · retorno = stake anulada (o dinheiro decide; é o caso do
    "Retirado" medido) · `settled*` com retorno 0 perdida · retorno = stake × odd ao meio centavo
    ganha. O resto, RECUSA.
  • PERNA comum (`SportBet`): `status` pending/won/lost; `voidFactor` 1 anulada. PROPS (`SwishBet`):
    a perna não diz o resultado; na simples, ela herda o do bilhete.
  • MERCADO da props: `<jogador> <estatística>` ("Matisse Thybulle rebounds"), com o nome na
    frente para a chave `{jogador}` do dicionário generalizar; seleção `<over|under> <linha>`.
  • Sem amostra, RECUSA: corrida, XMulti, promoção/boost (`promotionBet`, `customPrices`,
    `adjustments`), cashout parcial (`cashouts`) e cashout com retorno ≠ stake.
"""
from __future__ import annotations

import re
from decimal import Decimal
from email.utils import parsedate_to_datetime

from . import Recusa, numero

_MEIO_CENTAVO = Decimal("0.005")
_PERNA = {"pending": "aberta", "won": "ganha", "lost": "perdida", "void": "anulada", "cancelled": "anulada"}
_LISTAS_ABERTAS = ("activeSportBets", "activeSwishBetList", "activeRacingBets", "activeSportsbookXMultiBetList")
_IID = re.compile(r"^sport:(\d+)$")


def bilhetes_da_resposta(resposta) -> list:
    """A mensagem do inject (`[{codigo, cru}]`) ou a resposta da casa às duas queries."""
    if isinstance(resposta, list):
        return [x["cru"] for x in resposta if isinstance(x, dict) and isinstance(x.get("cru"), dict)]
    u = ((resposta or {}).get("data") or {}).get("user") if isinstance(resposta, dict) else None
    if not isinstance(u, dict):
        return []
    out = [{"iid": x.get("iid"), "bet": x.get("bet")} for x in (u.get("sportBetList") or [])
           if isinstance(x, dict) and isinstance(x.get("bet"), dict)]
    for k in _LISTAS_ABERTAS:
        for b in u.get(k) or []:
            if isinstance(b, dict):
                out.append({"iid": (b.get("bet") or {}).get("iid"), "bet": b})
    return out


def codigo(cru) -> str:
    if not isinstance(cru, dict):
        return ""
    m = _IID.match(str(cru.get("iid") or ""))
    return m.group(1) if m else ""


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _iso(v) -> str | None:
    try:
        return parsedate_to_datetime(str(v)).isoformat() if v else None
    except (TypeError, ValueError):
        return None


def _odd(b: dict):
    return b.get("odds") if b.get("__typename") == "SwishBet" and b.get("odds") is not None else b.get("potentialMultiplier")


def _status(b: dict) -> str:
    st = b.get("status")
    if b.get("active") is True or st in ("confirmed", "pending"):
        return "aberta"
    stake, ret, odd = _d(b.get("amount")), _d(b.get("payout")), _d(_odd(b))
    if stake is None or stake <= 0 or ret is None:
        raise Recusa(f"status {st!r} sem amount ou sem payout")
    if abs(ret - stake) <= _MEIO_CENTAVO:
        return "anulada"              # o dinheiro decide: P/L zero, qualquer que seja o rótulo
    if st == "cashout" or st == "cashoutPending":
        raise Recusa(f"cashout com payout {b.get('payout')!r} ≠ stake (sem amostra; a conferir)")
    if str(st or "").startswith("settled"):
        if ret == 0:
            return "perdida"
        if odd and abs(ret - stake * odd) <= _MEIO_CENTAVO:
            return "ganha"
    raise Recusa(f"status {st!r} com payout {b.get('payout')!r} sobre amount {b.get('amount')!r} "
                 f"e odd {_odd(b)!r} (sem amostra; a conferir)")


def _fixture(fx: dict) -> dict:
    fx = fx or {}
    tor = fx.get("tournament") or {}
    sp = ((tor.get("category") or {}).get("sport")) or {}
    dados = fx.get("data") or {}
    # `teams` diz quem é mandante (`qualifier`); corrida e outright não têm times.
    times = {t.get("qualifier"): _limpo(t.get("name")) for t in (dados.get("teams") or []) if isinstance(t, dict)}
    casa, fora = times.get("home"), times.get("away")
    return {"evento": _limpo(fx.get("name") or dados.get("name")), "liga_casa": _limpo(tor.get("name")) or None,
            "esporte_casa": _limpo(sp.get("name")) or None, "inicio": _iso(dados.get("startTime")),
            "mandante": casa or None, "visitante": fora or None}


def _perna_sport(o: dict) -> dict:
    fx = _fixture(o.get("fixture"))
    out = o.get("outcome") or {}
    estado = "anulada" if numero(out.get("voidFactor")) == "1" else _PERNA.get(str(o.get("status") or ""))
    return dict(fx, mercado_casa=_limpo((o.get("market") or {}).get("name")), selecao_casa=_limpo(out.get("name")),
                linha=None, odd=numero(o.get("odds")), status_perna=estado)


def _perna_swish(o: dict, herdado) -> dict:
    out = o.get("outcome") or {}
    game = ((out.get("market") or {}).get("game")) or {}
    fx = _fixture(game.get("fixture"))
    if not fx["evento"]:
        fx["evento"] = " - ".join(x for x in (game.get("homeTeam"), game.get("awayTeam")) if x)
    jogador = _limpo((out.get("competitor") or {}).get("name"))
    linha = numero(out.get("line"))
    return dict(fx, mercado_casa=f"{jogador} {_limpo(out.get('name'))}".strip(),
                selecao_casa=f"{_limpo(o.get('lineType'))} {linha or ''}".strip(), linha=linha,
                odd=numero(o.get("odds")), status_perna="anulada" if o.get("cancel") else herdado)


def adaptar(cru: dict, casa_key: str) -> dict:
    cod = codigo(cru)
    if not cod:
        raise Recusa("bilhete sem iid")
    b = cru.get("bet") or {}
    tipo = b.get("__typename")
    if tipo not in ("SportBet", "SwishBet"):
        raise Recusa(f"tipo {tipo!r} sem amostra (o texto leva à IA)")
    for campo in ("promotionBet",):
        if b.get(campo):
            raise Recusa(f"{campo} sem amostra (o texto leva à IA)")
    for campo in ("customPrices", "adjustments", "cashouts"):
        if b.get(campo):
            raise Recusa(f"{campo} preenchido sem amostra (o texto leva à IA)")
    status = _status(b)
    outs = b.get("outcomes") or []
    if not outs:
        raise Recusa("bilhete sem outcomes")
    if tipo == "SportBet":
        pernas = [_perna_sport(o) for o in outs]
    else:
        herdado = status if len(outs) == 1 and status in ("aberta", "ganha", "perdida") else None
        pernas = [_perna_swish(o, herdado) for o in outs]
    ret = numero(b.get("payout"))
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": _iso(b.get("createdAt")),
        "liquidada_em": None,
        "status": status,
        "status_casa": f"{tipo} · status {b.get('status')} · customBet {b.get('customBet')}",
        "moeda": _limpo(b.get("currency")).upper() or None,
        "stake": numero(b.get("amount")),
        "stake_freebet": None,
        "odd": numero(_odd(b)),
        "odd_calculada": False,
        "retorno": None if status == "aberta" else "0" if status == "perdida" else ret,
        "tipo": "multipla" if len(pernas) > 1 else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_stc",
    }
