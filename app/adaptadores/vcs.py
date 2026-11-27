"""Adaptador da Vem com Sorte (família `vcs`, plataforma própria `vemcomsorte.com`; s467).

O cru é um item de `data` de `POST /api/bettor/bet:history`, o mesmo que o `vcs_inject.js`
busca, e chega VERBATIM (o inject não o normaliza). A leitura de cada campo é a do
`formatTicketVCS` do `content.js` e da `CASA_VEMCOMSORTE.md`, validada contra o card no recon
de 26/11/2026 (`extensor/harness/casos/vemcomsorte.mjs`, fixture
`vemcomsorte.bet_history.json`: 7 múltiplas de 3 pernas em BRL, 2 abertas, 1 ganha, 4
perdidas). Escrito ANTES do 1º cru real chegar ao banco.

  • DINHEIRO EM CENTAVOS: `money.amount` 25000 com `money.multiplier` 100 = 250. Sem o
    `multiplier` da casa, recusa (nunca chuta 100).
  • `money.payout` é o retorno (o "Saque" do card): 164895 = 1648,95 na ganha, 0 na perdida e
    na aberta. Já inclui o Combo Boost (`money.bonus`).
  • odd = `initialOdds`, completa (o card mostra `odds`, truncada em 2 casas). Ela já tem o
    boost: na ganha fecha o retorno no meio centavo (250 × 6,595784 = 1648,946). Na perdida o
    `possiblePayout` perde o boost e vira o produto das pernas, mas o card segue com a odd
    boostada (6.56): a odd é a do card, nunca o produto.
  • código = `id` da aposta (7 dígitos). As pernas têm `id` próprio, de outra série.
  • datas em epoch MILISSEGUNDOS (`createTime`, `outcomes[].event.startTime`). `updateTime`
    não é provadamente a liquidação: não entra.
  • status pelo DINHEIRO: ganha só com `WIN`, toda perna `WIN` e retorno fechando stake × odd
    no centavo; perdida só com `LOSE`, retorno 0 e ao menos uma perna `LOSE`/`HALF_LOSE`.
  • Ganha com perna `VOID` (s468, 1º cru real: Gabriel 6442644, 27/11/2026): a anulada sai da
    conta e o boost cai junto. Aceita só com o retorno fechando stake × produto das pernas
    GANHAS no centavo (300 × 1,90 × 1,70 = 969,00); a odd sai por retorno ÷ stake na Ficha.
  • Sem amostra, RECUSA: `VOID`, `CASHOUT`, `HALF_WIN`, `HALF_LOSE` no bilhete, tipos
    `SYSTEM`/`FLEXIBLE`/`ONE_CUT`, ganha com perna que não seja `WIN`/`VOID`, ganha só de anuladas.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from . import Recusa, numero

_PERNA = {"UNSETTLED": "aberta", "WIN": "ganha", "LOSE": "perdida", "VOID": "anulada",
          "HALF_WIN": "meio_ganha", "HALF_LOSE": "meio_perdida"}
_TIPO = {"SINGLE": "simples", "MULTIPLE": "multipla"}
_CENTAVO = Decimal("0.01")


def bilhetes_da_resposta(resposta) -> list:
    d = resposta.get("data") if isinstance(resposta, dict) else None
    return d if isinstance(d, list) else []       # `data: null` = lista vazia (medido)


def codigo(cru) -> str:
    if not isinstance(cru, dict):
        return ""
    v = cru.get("id")
    if v is None or isinstance(v, bool) or str(v).strip() == "":
        return ""
    return str(v).strip()


def _dec(v) -> Decimal | None:
    if v is None or isinstance(v, bool) or v == "":
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _iso_ms(ms) -> str | None:
    d = _dec(ms)
    if d is None:
        return None
    try:
        return datetime.fromtimestamp(float(d) / 1000, tz=timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def _juntar(*partes) -> str:
    return " ".join(str(p) for p in partes if p is not None and str(p) != "")


def _status(t: dict, stake: Decimal, odd: Decimal, retorno: Decimal | None, pst: list,
            odds_ganhas: list | None = None) -> str:
    odds_ganhas = odds_ganhas or []
    st = t.get("status")
    cru = f"status {st!r}"
    if st == "UNSETTLED":
        return "aberta"
    if retorno is None:
        raise Recusa(f"{cru} sem payout")
    if st == "WIN":
        if not pst or not all(p in ("WIN", "VOID") for p in pst) or "WIN" not in pst:
            raise Recusa(f"{cru} com pernas {pst!r}: sem amostra liquidada (a conferir)")
        if retorno <= stake:
            raise Recusa(f"{cru}: retorno {retorno} não passa da stake {stake}")
        if "VOID" not in pst:
            if abs(retorno - stake * odd) > _CENTAVO:
                raise Recusa(f"{cru}: retorno {retorno} não fecha stake {stake} × odd {odd}")
            return "ganha"
        # s468 (Gabriel, 6442644): perna anulada sai da conta e o boost cai junto. A casa
        # pagou stake × produto das pernas GANHAS, sem boost (300 × 1,90 × 1,70 = 969,00), e a
        # Ficha deriva a odd por retorno ÷ stake (`ficha._odd`, nenhuma outra fecha).
        # Só com o retorno fechando essa conta no centavo; boost sobrevivendo, recusa.
        prod = Decimal(1)
        for o in odds_ganhas:
            if o is None or o <= 1:
                raise Recusa(f"{cru}: perna ganha sem odd")
            prod *= o
        if abs(retorno - stake * prod) > _CENTAVO:
            raise Recusa(f"{cru} com perna anulada: retorno {retorno} não fecha stake {stake} "
                         f"× pernas ganhas {prod}")
        return "ganha"
    if st == "LOSE":
        if retorno == 0 and any(p in ("LOSE", "HALF_LOSE") for p in pst):
            return "perdida"
        raise Recusa(f"{cru} com retorno {retorno} e pernas {pst!r}")
    raise Recusa(f"{cru} sem amostra (a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    cod = codigo(t)
    if not cod:
        raise Recusa("aposta sem id")
    tipo = _TIPO.get(t.get("type"))
    if not tipo:
        raise Recusa(f"type {t.get('type')!r} sem amostra (a conferir)")
    outs = [o if isinstance(o, dict) else {} for o in (t.get("outcomes") or [])]
    if not outs:
        raise Recusa("aposta sem outcome")
    for o in outs:
        if o.get("status") not in _PERNA:
            raise Recusa(f"perna com status {o.get('status')!r} não mapeado")
    m = t.get("money") if isinstance(t.get("money"), dict) else {}
    mult = _dec(m.get("multiplier"))
    if mult is None or mult <= 0:
        raise Recusa(f"money.multiplier {m.get('multiplier')!r}: sem a escala do dinheiro")
    amount = _dec(m.get("amount"))
    stake = amount / mult if amount is not None else None
    odd = _dec(t.get("initialOdds"))
    if odd is None:
        odd = _dec(t.get("odds"))
    if stake is None or stake <= 0 or odd is None or odd <= 1:
        raise Recusa(f"stake {m.get('amount')!r} ou odd {t.get('initialOdds')!r} inválida")
    payout = _dec(m.get("payout"))
    retorno = payout / mult if payout is not None else None
    status = _status(t, stake, odd, retorno, [o.get("status") for o in outs],
                     [_dec(o.get("odds")) for o in outs if o.get("status") == "WIN"])
    pernas = []
    for o in outs:
        ev, mk, sp = o.get("event") or {}, o.get("market") or {}, o.get("sport") or {}
        pernas.append({
            "esporte_casa": sp.get("name") or None,
            "evento": ev.get("name") or "",
            "mercado_casa": mk.get("name") or "",
            "selecao_casa": _juntar(o.get("name"), o.get("parameters")),
            "odd": numero(o.get("odds")),
            "inicio": _iso_ms(ev.get("startTime")),
            "status_perna": _PERNA[o["status"]],
        })
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": _iso_ms(t.get("createTime")),
        "liquidada_em": None,
        "status": status,
        "status_casa": f"status {t.get('status')} · type {t.get('type')}",
        "moeda": (m.get("currency") or "").upper() or None,
        "stake": numero(str(stake)),
        "stake_freebet": None,
        "odd": numero(t.get("initialOdds") if t.get("initialOdds") is not None else t.get("odds")),
        "odd_calculada": False,
        "retorno": numero(str(retorno)) if status in ("ganha", "perdida") else None,
        "tipo": tipo,
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_vcs",
    }
