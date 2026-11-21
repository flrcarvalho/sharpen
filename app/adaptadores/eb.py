"""Adaptador da EpicBet (família `eb`, plataforma própria `epicbet.com`, API tRPC; s462).

O cru é um item de `result.data.tickets` de `GET /s/sport-bet/user/ticket.listWithMatchInfo`,
o mesmo que o `eb_inject.js` busca, e chega VERBATIM (o inject não o normaliza). A leitura de
cada campo é a do `formatTicketEB` do `content.js` e da `CASA_EPICBET.md`, validada contra o
card no recon de 21/11/2026 (`extensor/harness/casos/epicbet.mjs`, fixtures
`epicbet.pending.json` e `epicbet.settled.json`: 13 múltiplas de 3 pernas em USDT, 2 abertas,
2 ganhas, 9 perdidas). Escrito ANTES do 1º cru real chegar ao banco.

  • NÃO HÁ CAMPO DE RETORNO. O "Payout" do card é `stake × odds` (40 × 7,14 = 285,6 no ID 11;
    0 na perdida). O retorno da ganha é esse produto, o número que o card mostra, e só com as
    provas: status `won`, TODA perna `won`, sem cashout e sem boost. Perdida: `lost` com ao
    menos uma perna `lost`/`half_lost`, retorno 0.
  • `bet.odds` já é a odd EFETIVA, a do card: perna `pushed` e `half_won` entram recalculadas
    pela casa (ID 12: card 6.14, produto 12,10; ID 7: card 5.87, produto 8,42). Nunca o produto.
  • código = `sequence`, o "ID" do card (1, 2, 3… por conta). É o que a base já tinha por
    print (10 bilhetes do Gabriel, códigos 1 a 10). O `bet.id` é interno e não entra.
  • datas em ISO UTC com `Z` (`createdAt`, `selections[].selectionInfo.matchStart`). A casa
    não publica a hora da liquidação.
  • moeda: `bet.currency` (USDT na conta do recon).
  • Sem amostra, RECUSA: cashout (`cashouts[]`), boost (`oddsBoost`), bet builder, ganha com
    perna que não seja `won`, e todo status fora de `pending`/`won`/`lost`
    (`void`, `cashed out`, `partially_won`, `campaign settled`...).
"""
from __future__ import annotations

from decimal import Decimal

from . import Recusa, numero

_PERNA = {"pending": "aberta", "won": "ganha", "lost": "perdida", "pushed": "anulada",
          "half_won": "meio_ganha", "half_lost": "meio_perdida"}


def bilhetes_da_resposta(resposta) -> list:
    d = ((resposta or {}).get("result") or {}).get("data") if isinstance(resposta, dict) else None
    t = (d or {}).get("tickets") if isinstance(d, dict) else None
    return t if isinstance(t, list) else []


def codigo(cru) -> str:
    if not isinstance(cru, dict) or cru.get("sequence") is None or isinstance(cru.get("sequence"), bool):
        return ""
    try:
        return str(int(cru["sequence"]))
    except (TypeError, ValueError):
        return ""


def _dec(v) -> Decimal | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _status(b: dict, pst: list) -> str:
    st = b.get("status")
    cru = f"status {st!r}"
    if b.get("cashouts"):
        raise Recusa(f"{cru}: cashout sem amostra (a conferir)")
    if b.get("oddsBoost") is not None:
        raise Recusa(f"{cru}: boost de odd sem amostra (a conferir)")
    if st == "pending":
        return "aberta"
    if st == "won":
        if pst and all(p == "won" for p in pst):
            return "ganha"
        raise Recusa(f"{cru} com pernas {pst!r}: sem amostra liquidada (a conferir)")
    if st == "lost":
        if any(p in ("lost", "half_lost") for p in pst):
            return "perdida"
        raise Recusa(f"{cru} sem perna perdida ({pst!r})")
    raise Recusa(f"{cru} sem amostra (a conferir)")


def _juntar(*partes) -> str:
    return " ".join(str(p) for p in partes if p not in (None, ""))


def adaptar(t: dict, casa_key: str) -> dict:
    cod = codigo(t)
    if not cod:
        raise Recusa("ticket sem sequence")
    b = t.get("bet") if isinstance(t.get("bet"), dict) else None
    if not b:
        raise Recusa("ticket sem bet")
    sels = [s if isinstance(s, dict) else {} for s in (b.get("selections") or [])]
    if not sels:
        raise Recusa("bilhete sem seleção")
    for s in sels:
        if s.get("status") not in _PERNA:
            raise Recusa(f"perna com status {s.get('status')!r} não mapeado")
        info = s.get("selectionInfo") or {}
        extra = s.get("selectionExtra") or {}
        if info.get("betBuilderSelectionInfo") or extra.get("betbuilderInfo"):
            raise Recusa("bet builder sem amostra (a conferir)")
    stake, odd = _dec(b.get("stake")), _dec(b.get("odds"))
    if stake is None or stake <= 0 or odd is None or odd <= 1:
        raise Recusa(f"stake {b.get('stake')!r} ou odd {b.get('odds')!r} inválida")
    status = _status(b, [s.get("status") for s in sels])
    retorno = None
    if status == "ganha":
        retorno = numero(str(stake * odd))           # o Payout do card (a casa não publica retorno)
    elif status == "perdida":
        retorno = "0"
    pernas = []
    for s in sels:
        info, msi = s.get("selectionInfo") or {}, s.get("matchScoreInfo") or {}
        pernas.append({
            "esporte_casa": msi.get("sportEntityName") or None,
            "evento": info.get("matchName") or "",
            "mercado_casa": _juntar(info.get("marketName"), info.get("marketLine")),
            "selecao_casa": _juntar(info.get("outcomeName"), info.get("outcomeLine")),
            "odd": numero(s.get("odds")),
            "inicio": info.get("matchStart") or None,
            "status_perna": _PERNA[s["status"]],
        })
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": t.get("createdAt") or None,
        "liquidada_em": None,
        "status": status,
        "status_casa": f"status {b.get('status')} · type {t.get('type')}",
        "moeda": (b.get("currency") or "").upper() or None,
        "stake": numero(b.get("stake")),
        "stake_freebet": None,
        "odd": numero(b.get("odds")),
        "odd_calculada": False,
        "retorno": retorno,
        "tipo": "simples" if len(sels) == 1 else "multipla",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_eb",
    }
