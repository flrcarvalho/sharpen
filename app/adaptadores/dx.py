"""Adaptador da DEX Sport (família `dx`, plataforma própria; s409).

O cru é um item de `GET …/api/sportsbook/history/tickets` (`data[]`), o mesmo que o
`dx_inject.js` escuta. A leitura de cada campo é a que o `formatTicketDX` do `content.js`
já usa e que o recon de 03/10/2026 validou contra o card (`extensor/harness/casos/dexsport.mjs`):

  • `status` 2 + `result` 0 = aberta; `status` 3 = concluída. Qualquer outra combinação
    RECUSA: status desconhecido nunca vira resultado por chute.
  • `payout` vem 0 na perdida E na aberta: retorno zero só é perdida com `result` 2.
  • `payout` = `amount` (no centavo) = anulada; `payout` > `amount` com `result` 1 = ganha.
    Qualquer outro retorno (meia vitória, meia derrota, cashout) RECUSA com o motivo, como o
    bloco de hoje sobe "a conferir".
  • odd: `payoutCoefficient` (a LIQUIDADA) na ganha; `coefficient` (a da colocação, a do
    card) no resto. Na perna anulada as duas divergem (`b4836669`: 12,56 × 3,75).
  • datas: `placedAt` e `finishedAt` em epoch (s); `eventDate` em ISO UTC.
  • `currency` minúsculo (`usdt`): a Ficha leva maiúsculo.
"""
from __future__ import annotations

from . import Recusa, iso_de_epoch, numero

_PERNA = {0: "aberta", 1: "ganha", 2: "perdida", 6: "anulada"}
_TIPO = {0: "simples", 1: "multipla"}


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict) and isinstance(resposta.get("data"), list):
        return resposta["data"]
    return []


def _status(t: dict) -> str:
    st, res = t.get("status"), t.get("result")
    cru = f"status {st} · result {res}"
    if st == 2 and res == 0:
        return "aberta"
    if st != 3:
        raise Recusa(f"{cru}: combinação não mapeada (a conferir)")
    amount, payout = t.get("amount"), t.get("payout")
    if payout is None or amount is None:
        raise Recusa(f"{cru}: concluída sem payout ou sem amount")
    if payout == 0:
        if res == 2:
            return "perdida"
        raise Recusa(f"{cru}: retorno zero sem result 2 (a conferir)")
    if abs(float(payout) - float(amount)) < 0.005:
        return "anulada"
    if payout > amount and res == 1:
        return "ganha"
    raise Recusa(f"{cru}: retorno {payout} sobre stake {amount} (HW/HL ou cashout, a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or not t.get("id"):
        raise Recusa("bilhete sem id")
    status = _status(t)
    tipo = _TIPO.get(t.get("ticketType"))
    if tipo is None:
        raise Recusa(f"ticketType {t.get('ticketType')!r} não mapeado")
    pago = t.get("payoutCoefficient")
    odd = pago if (status == "ganha" and pago) else t.get("coefficient")
    pernas = []
    for b in t.get("bets") or []:
        ev, mk = b.get("event") or {}, b.get("eventMarket") or {}
        if b.get("status") not in _PERNA:
            raise Recusa(f"perna com status {b.get('status')!r} não mapeado")
        pernas.append({
            "esporte_casa": b.get("disciplineId") or None,
            "evento": ev.get("name") or "",
            "mercado_casa": mk.get("name") or "",
            "selecao_casa": b.get("outcomeName") or "",
            "odd": numero(b.get("coefficient")),
            "inicio": b.get("eventDate") or None,
            "status_perna": _PERNA[b.get("status")],
        })
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["id"]),
        "colocada_em": iso_de_epoch(t.get("placedAt")),
        "liquidada_em": iso_de_epoch(t.get("finishedAt")) if t.get("status") == 3 else None,
        "status": status,
        "status_casa": (f"result {t.get('result')} · status {t.get('status')} · "
                        f"settlementStatus {t.get('settlementStatus')}"),
        "moeda": (t.get("currency") or "").upper() or None,
        "stake": numero(t.get("amount")),
        "stake_freebet": None,
        "odd": numero(odd),
        "odd_calculada": False,
        "retorno": numero(t.get("payout")) if status != "aberta" else None,
        "tipo": tipo,
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_dx",
    }
