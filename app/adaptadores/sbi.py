"""Adaptador da Sportsbet.io (família `sbi`, plataforma própria GraphQL; s428).

O cru é o `node` de `data.sportsbetTickets.myBettingHistory` / `myActiveTickets` (`POST
/graphql`), o mesmo que o `sbi_inject.js` escuta (`parseTicket`). A leitura de cada campo é a do
`formatTicketSBI` do `content.js` e da `CASA_SPORTSBETIO.md`; escrito das fixtures da bancada
(`extensor/harness/fixtures/sportsbetio.*.json`, 17 liquidadas e 14 abertas, conta do Feca em
USDT, recon de 25/10/2026), cada valor cruzado com o card.

  • CÓDIGO: o `id` é base64 de `SportsbetTicketsTicket:<ObjectId>`; o código é o ObjectId (24
    hex), o que o botão "ID" do card copia e o inject põe no `[Código: …]` do texto.
  • DINHEIRO em 1e8: `stakeAmount` 2500000000 = 25 USDT. ⚠ Escala medida SÓ em USDT: outra
    moeda RECUSA (o texto leva à IA, que lê o número já dividido) até alguém medir.
  • `wonAmount` é o RETORNO (60,01 × 1,77 = 106,2177) e é null na perdida.
  • ODD da casa: `boostedOdds` do bilhete, a do card (5,83 no turbinado, onde `odds` = 5,71).
  • status: `ACTIVE` aberta · retorno = stake anulada (o dinheiro decide) · sem retorno com
    perna perdida (status 2 e `voidFactor` ≠ 1) perdida · retorno = stake × odd ao meio centavo
    ganha. O resto, RECUSA.
  • PERNA: `status` 0 aberta · 1 ganha · 2 perdida; `voidFactor` 1 é anulada (cinza no card),
    qualquer que seja o `status`. A odd da perna é a turbinada quando houver.
  • ESPORTE: só o `sport.slug` (`soccer`, `ice-hockey`); vai em inglês para o dicionário `*`
    traduzir. Slug fora do mapa vai VAZIO.
  • Sem amostra, RECUSA: freebet, cashout (`cashout.instances`), mais de uma aposta no bilhete
    (sistema) e Bet Builder (perna única `Bet Builder` com as seleções juntas por ";"; a Ficha
    precisa de uma perna por seleção). O texto continua levando esses bilhetes à IA.
"""
from __future__ import annotations

import base64
import binascii
import re
from decimal import Decimal

from . import Recusa, iso_de_epoch, numero

_ESCALA = Decimal(100_000_000)
_MOEDAS_MEDIDAS = {"USDT"}
_MEIO_CENTAVO = Decimal("0.005")
_PERNA = {0: "aberta", 1: "ganha", 2: "perdida"}
_ESPORTE = {"soccer": "Soccer", "basketball": "Basketball", "tennis": "Tennis",
            "ice-hockey": "Ice Hockey", "american-football": "American Football",
            "handball": "Handball"}
_HEX = re.compile(r"^[0-9a-f]{24}$", re.I)
_LINHA = re.compile(r"^(?:Mais|Menos) de (\d+(?:\.\d+)?)$")


def _conexao(resposta):
    st = ((resposta or {}).get("data") or {}).get("sportsbetTickets") if isinstance(resposta, dict) else None
    if not isinstance(st, dict):
        return None
    return st.get("myBettingHistory") or st.get("myActiveTickets")


def bilhetes_da_resposta(resposta) -> list:
    """A resposta da casa (`edges[].node`) ou a mensagem do inject (`[{codigo, cru}]`)."""
    if isinstance(resposta, list):
        return [x["cru"] for x in resposta if isinstance(x, dict) and isinstance(x.get("cru"), dict)]
    con = _conexao(resposta)
    if not isinstance(con, dict) or not isinstance(con.get("edges"), list):
        return []
    return [e["node"] for e in con["edges"] if isinstance(e, dict) and isinstance(e.get("node"), dict)]


def codigo(cru) -> str:
    if not isinstance(cru, dict) or cru.get("id") in (None, ""):
        return ""
    s = str(cru["id"])
    try:
        t = base64.b64decode(s, validate=True).decode("latin1")
    except (binascii.Error, ValueError):
        return s
    h = t.rsplit(":", 1)[-1]
    return h.lower() if ":" in t and _HEX.match(h) else s


def _din(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) / _ESCALA if n is not None else None


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _odd(o) -> str | None:
    return numero(o.get("boostedOdds")) if o.get("boostedOdds") not in (None, "") else numero(o.get("odds"))


def _estado_perna(s: dict) -> str | None:
    if _int(s.get("voidFactor")) == 1:
        return "anulada"
    return _PERNA.get(_int(s.get("status")))


def _status(t: dict, sels: list) -> str:
    if t.get("status") == "ACTIVE":
        return "aberta"
    stake, ret, odd = _din(t.get("stakeAmount")), _din(t.get("wonAmount")), _odd(t)
    if stake is None or stake <= 0:
        raise Recusa(f"status {t.get('status')!r} sem stakeAmount")
    if ret is not None and abs(ret - stake) <= _MEIO_CENTAVO:
        return "anulada"              # o dinheiro decide: P/L zero, qualquer que seja o rótulo
    if ret is None or ret == 0:
        if any(_estado_perna(s) == "perdida" for s in sels):
            return "perdida"
        raise Recusa(f"status {t.get('status')!r} sem retorno e sem perna perdida (a conferir)")
    if odd and abs(ret - stake * Decimal(odd)) <= _MEIO_CENTAVO:
        return "ganha"
    raise Recusa(f"status {t.get('status')!r} com wonAmount {t.get('wonAmount')!r} sobre stakeAmount "
                 f"{t.get('stakeAmount')!r} e odd {odd!r} (sem amostra; a conferir)")


def _perna(s: dict) -> dict:
    jogo = _limpo(s.get("eventName"))
    partes = re.split(r"\s+(?:-|vs)\s+", jogo, maxsplit=1)
    casa, fora = (partes + [""])[:2] if len(partes) == 2 else ("", "")
    sel = _limpo(s.get("name"))
    m = _LINHA.match(sel)
    return {
        "esporte_casa": _ESPORTE.get(str((s.get("sport") or {}).get("slug") or "")),
        "liga_casa": None,
        "evento": jogo,
        "mandante": casa or None,
        "visitante": fora or None,
        "mercado_casa": _limpo(s.get("marketName")),
        "selecao_casa": sel,
        "linha": numero(m.group(1)) if m else None,
        "odd": _odd(s),
        "inicio": iso_de_epoch(_int(s.get("eventStartTime"))),
        "status_perna": _estado_perna(s),
    }


def adaptar(t: dict, casa_key: str) -> dict:
    cod = codigo(t)
    if not cod:
        raise Recusa("bilhete sem id")
    moeda = _limpo(t.get("currencyCode")).upper()
    if moeda not in _MOEDAS_MEDIDAS:
        raise Recusa(f"moeda {moeda or '(vazia)'!r}: a escala 1e8 só foi medida em USDT")
    bets = t.get("bets") or []
    if len(bets) != 1:
        raise Recusa(f"{len(bets)} apostas no bilhete (sistema, sem amostra)")
    if bets[0].get("freeBet") is True:
        raise Recusa("freeBet sem amostra (o texto leva à IA)")
    if ((t.get("cashout") or {}).get("instances") or []):
        raise Recusa("cashout sem amostra (o texto leva à IA)")
    sels = bets[0].get("selections") or []
    if not sels:
        raise Recusa("bilhete sem selections")
    if any(_limpo(s.get("marketName")).lower() == "bet builder" for s in sels):
        raise Recusa("Bet Builder: as seleções vêm juntas numa perna só (o texto leva à IA)")
    status = _status(t, sels)
    pernas = [_perna(s) for s in sels]
    ret = _din(t.get("wonAmount"))
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": iso_de_epoch(_int(t.get("placedAt"))),
        "liquidada_em": None,
        "status": status,
        "status_casa": f"status {t.get('status')} · betType {t.get('betType')} · "
                       f"boosted {t.get('boosterTicket')}",
        "moeda": moeda,
        "stake": numero(_din(t.get("stakeAmount"))),
        "stake_freebet": None,
        "odd": _odd(t),
        "odd_calculada": False,
        "retorno": (None if status == "aberta" else "0" if status == "perdida" else numero(ret)),
        "tipo": "multipla" if len(pernas) > 1 else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_sbi",
    }
