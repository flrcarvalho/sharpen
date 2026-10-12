"""Adaptador da Shuffle (família `shf`, plataforma própria em GraphQL; s409).

O cru é um item de `sportsBetsV3`, o mesmo que o `shf_inject.js` escuta (`parseTicket`).
A leitura de cada campo é a do `formatTicketSHF` do `content.js` (recon s401, 31 bilhetes):

  • `amount` é a stake TOTAL (no sistema, a soma das linhas). `settlement.payout` é o
    retorno; `settlement` só existe depois de liquidar.
  • `status`: `PENDING` aberta · `LOST` perdida (só com retorno zero) · `WON` ganha, mas o
    dinheiro decide: retorno = stake é anulada, e sistema pode vir `WON` pagando MENOS que a
    stake (54,996 sobre 60), que segue ganha com P/L negativo · `VOIDED`/`CANCELLED`
    anulada (só com retorno = stake) · `CASHED_OUT` cashout. Qualquer outro, RECUSA.
  • odd da casa: `totalOddsDecimal` (a da colocação, a do card; no sistema já é a MÉDIA das
    linhas, `MASTER_RESULTADO §7.3`). Na ganha e no cashout, `settlement.payoutOddsDecimal`,
    a LIQUIDADA: com perna `PUSHED` a da colocação não muda (11,5182 × paga 5,1192).
  • TRÊS odds por seleção: a da perna é `legs[].oddsDecimal` (a apostada). A do
    `marketSelection` é a ATUAL do mercado e nunca entra.
  • `originalAmount` veio nulo nos 72 crus; se vier diferente da stake, RECUSA.
"""
from __future__ import annotations

from decimal import Decimal

from . import Recusa, numero

_PERNA = {"WON": "ganha", "LOST": "perdida", "PUSHED": "anulada", "PENDING": "aberta"}
_CENTAVO = Decimal("0.005")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict):
        d = resposta.get("data") or {}
        sb = d.get("sportsBets") if isinstance(d, dict) else None
        if isinstance(sb, list):
            return sb
        if isinstance(sb, dict) and isinstance(sb.get("nodes"), list):
            return sb["nodes"]
    return resposta if isinstance(resposta, list) else []


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _status(t: dict) -> str:
    st = t.get("status")
    if st == "PENDING":
        return "aberta"
    sett = t.get("settlement") or {}
    stake, ret = _d(t.get("amount")), _d(sett.get("payout"))
    if ret is None or stake is None:
        raise Recusa(f"status {st!r} sem settlement.payout ou sem amount")
    igual = abs(ret - stake) <= _CENTAVO
    if st == "LOST" and ret == 0:
        return "perdida"
    if st == "WON" and igual:
        return "anulada"
    if st == "WON" and ret > 0:
        return "ganha"
    if st in ("VOIDED", "CANCELLED") and igual:
        return "anulada"
    if st == "CASHED_OUT":
        return "cashout"
    raise Recusa(f"status {st!r} com retorno {ret} sobre stake {stake} (a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or not t.get("id"):
        raise Recusa("bilhete sem id")
    orig = _d(t.get("originalAmount"))
    if orig is not None and orig != _d(t.get("amount")):
        raise Recusa(f"originalAmount {orig} difere de amount {t.get('amount')} (a conferir)")
    status = _status(t)
    legs = t.get("legs") or []
    if not legs:
        raise Recusa("bilhete sem legs")
    pernas = []
    for l in legs:
        sels = l.get("selections") or []
        if len(sels) != 1:
            raise Recusa(f"perna com {len(sels)} seleções (só 1 por perna foi medido)")
        s = sels[0]
        if l.get("displayStatus") not in _PERNA:
            raise Recusa(f"perna com status {l.get('displayStatus')!r} não mapeado")
        fx, mk, ms = s.get("fixture") or {}, s.get("market") or {}, s.get("marketSelection") or {}
        pernas.append({
            "esporte_casa": s.get("sports") or None,
            "liga_casa": (s.get("competition") or {}).get("name") or None,
            "evento": fx.get("name") or "",
            "mercado_casa": mk.get("name") or "",
            "selecao_casa": ms.get("formattedName") or "",
            "linha": numero(mk.get("lineValue")),
            "odd": numero(l.get("oddsDecimal")),
            "inicio": fx.get("startTime") or None,
            "status_perna": _PERNA[l.get("displayStatus")],
        })
    sett = t.get("settlement") or {}
    paga = _d(sett.get("payoutOddsDecimal"))
    odd = (numero(sett.get("payoutOddsDecimal")) if status in ("ganha", "cashout") and paga
           else numero(t.get("totalOddsDecimal")))
    sistema = t.get("type") == "SYSTEM_BET"
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["id"]),
        "colocada_em": t.get("createdAt") or None,
        "liquidada_em": sett.get("createdAt") or None,
        "status": status,
        "status_casa": f"status {t.get('status')} · type {t.get('type')}",
        "moeda": (t.get("currency") or "").upper() or None,
        "stake": numero(t.get("amount")),
        "stake_freebet": None,
        "odd": odd,
        "odd_calculada": False,
        "retorno": numero(sett.get("payout")) if status != "aberta" else None,
        "tipo": "sistema" if sistema else ("multipla" if len(pernas) > 1 else "simples"),
        "sistema": t.get("systemBetType") if sistema else None,
        "pernas": pernas,
        "origem": "servidor:adaptador_shf",
    }
