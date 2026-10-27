"""Adaptador da 1win (família `tp`, plataforma própria `top-parser`; s413).

O cru é um item de `result.items` do `POST api-gateway.top-parser.com/bets/history/get-many`,
o mesmo que o `tp_inject.js` escuta: `{bet: {...}, selections: [...]}`. O código mora em
`bet.id` (por isso o `codigo(cru)` abaixo, que a recusa usa). A leitura de cada campo é a do
`formatTicketTP` do `content.js` e da `CASA_1WIN.md`; escrito das fixtures da bancada
(`extensor/harness/fixtures/1win.*.json`, 5 bilhetes: 4 múltiplas abertas e 1 perdida), ANTES
do 1º cru real chegar ao banco.

  • `amount` é a stake. `profitAmount` é o RETORNO, não o lucro: na aberta é o potencial
    (25 × 5,73 = 143,25) e nunca vira retorno; na perdida, 0. `possibleProfitAmount` idem.
  • odd da casa: `bet.cf`, CORTADA em 2 casas, e é ela que paga (337817372: pernas 1,79 × 2,75
    = 4,9225, a casa paga 25 × 4,92 = 123). Nunca o produto das pernas.
  • `bet.status` 0 aberta · 1 perdida (só com retorno zero). Só o dinheiro decide o resto.
    Retorno = stake é anulada, qualquer status; status 2 com retorno = stake × `cf` ao centavo
    é ganha. Status 2 com perna ANULADA (s419): a casa paga pelo produto das pernas ganhas, e
    esse número fechando ao centavo também é ganha (odd = retorno ÷ stake, a Ficha deriva).
    Status 4 é CASHOUT (s431): o bilhete E toda perna vêm `4`, até perna já finalizada, e
    `profitAmount` é o valor recebido (o `derivar` decide W ou V). Qualquer outro número,
    RECUSA.
  • perna: `status` 0 pendente · 1 perdida · 2 ganha · 3 anulada (s419) · 4 encerrada pelo
    cashout (s431); o resto vai vazio (ausência, não palpite). A perdida pode ter perna ainda
    pendente: a casa liquida pela perna que perdeu.
  • Sem amostra, RECUSA: sistema, bônus de múltipla (`bonusAmount`), freebet
    (`freebetAmount`), carteira que não seja `real` e perna com meio retorno (`isHalfReturn`).
    O texto continua levando esses bilhetes à IA, que lê o rótulo certo.
  • `createdAt` e `closeAt` em ISO UTC; `match.startAt` em epoch SEGUNDOS.
  • `refundInfo.refundAmount` é a OFERTA de cashout da tela e nunca entra.
"""
from __future__ import annotations

from decimal import Decimal

from . import Recusa, iso_de_epoch, numero

# Perna 2 = ganha e 3 = anulada medidos na s419 (344388133 e 344381942, conta do Feca): a perna
# 3 não entrou no retorno (25 × 1,54 = 38,50 com a outra perna anulada). Perna 4 = cashout
# (s431, 5 bilhetes do Feca em `1win.cashout.json`): vem 4 até com o jogo já finalizado.
_PERNA = {0: "aberta", 1: "perdida", 2: "ganha", 3: "anulada", 4: "cashout"}
_CENTAVO = Decimal("0.005")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict):
        r = resposta.get("result")
        if isinstance(r, dict) and isinstance(r.get("items"), list):
            return r["items"]
    return resposta if isinstance(resposta, list) else []


def codigo(cru) -> str:
    """O código do bilhete no cru (a recusa precisa dele, e ele não mora em `cru.id`)."""
    b = cru.get("bet") if isinstance(cru, dict) else None
    return str((b or {}).get("id") or "") if isinstance(b, dict) else ""


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _paga_sem_anuladas(sels: list, stake: Decimal, ret: Decimal) -> bool:
    """Múltipla ganha com perna anulada (s419): a casa paga pelo produto das pernas GANHAS.
    Só vale com toda perna ganha ou anulada, pelo menos uma de cada, e o retorno fechando ao
    centavo com o produto exato ou cortado em 2 casas (a 1win corta a odd do bilhete)."""
    sts = [s.get("status") for s in sels]
    if not sts or any(st not in (2, 3) for st in sts) or 2 not in sts or 3 not in sts:
        return False
    prod = Decimal(1)
    for s in sels:
        if s.get("status") == 2:
            o = _d((s.get("odd") or {}).get("cf"))
            if o is None or o <= 1:
                return False
            prod *= o
    cortado = prod.quantize(Decimal("0.01"), rounding="ROUND_DOWN")
    return any(abs(ret - stake * p) <= _CENTAVO for p in (prod, cortado))


def _status(b: dict, sels: list) -> str:
    st = b.get("status")
    if st == 0:
        return "aberta"
    stake, ret, odd = _d(b.get("amount")), _d(b.get("profitAmount")), _d(b.get("cf"))
    if stake is None or stake <= 0 or ret is None:
        raise Recusa(f"status {st!r} sem amount ou sem profitAmount")
    if st == 1:
        if ret == 0:
            return "perdida"
        raise Recusa(f"perdida com profitAmount {ret} (a conferir)")
    if abs(ret - stake) <= _CENTAVO:
        return "anulada"              # o dinheiro decide: P/L zero, qualquer que seja o rótulo
    if st == 2 and odd and abs(ret - stake * odd) <= _CENTAVO:
        return "ganha"
    if st == 2 and _paga_sem_anuladas(sels, stake, ret):
        return "ganha"                # a Ficha deriva a odd: retorno ÷ stake
    # Cashout (s431): só no formato medido, bilhete e TODA perna em 4, com dinheiro recebido.
    if st == 4 and ret > 0 and sels and all(s.get("status") == 4 for s in sels):
        return "cashout"              # o `derivar` decide: ≠ stake → W, odd = retorno ÷ stake
    raise Recusa(f"status {st!r} com profitAmount {ret} sobre amount {stake} "
                 f"e cf {b.get('cf')!r} (sem amostra; a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    b = t.get("bet") if isinstance(t, dict) else None
    if not isinstance(b, dict) or b.get("id") in (None, ""):
        raise Recusa("bilhete sem bet.id")
    sels = t.get("selections") or []
    if not sels:
        raise Recusa("bilhete sem selections")
    if "system" in str(b.get("betType") or "").lower():
        raise Recusa(f"sistema (betType {b.get('betType')!r}) sem amostra")
    for campo in ("bonusAmount", "freebetAmount"):
        v = _d(b.get(campo))
        if v is not None and v != 0:
            raise Recusa(f"{campo} {v} sem amostra (o texto leva à IA)")
    if (b.get("wallet") or "real") != "real":
        raise Recusa(f"carteira {b.get('wallet')!r} sem amostra")
    status = _status(b, sels)
    pernas = []
    for s in sels:
        if s.get("isHalfReturn"):
            raise Recusa("perna com meio retorno (isHalfReturn) sem amostra")
        m, o = s.get("match") or {}, s.get("odd") or {}
        casa = _limpo((m.get("homeTeam") or {}).get("name"))
        fora = _limpo((m.get("awayTeam") or {}).get("name"))
        trn = s.get("tournament") or {}
        pernas.append({
            "esporte_casa": _limpo((s.get("sport") or {}).get("name")) or None,
            "liga_casa": _limpo(trn.get("name")) or None,
            "evento": f"{casa} - {fora}" if casa and fora else (casa or fora),
            "mercado_casa": _limpo(o.get("groupName") or (s.get("oddGroup") or {}).get("name")),
            "selecao_casa": _limpo(o.get("name")),
            "odd": numero(o.get("cf")),
            "inicio": iso_de_epoch(m.get("startAt")),
            "status_perna": _PERNA.get(s.get("status")),
        })
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(b["id"]),
        "colocada_em": b.get("createdAt") or None,
        "liquidada_em": (b.get("closeAt") or None) if status != "aberta" else None,
        "status": status,
        "status_casa": f"status {b.get('status')} · betType {b.get('betType')}",
        "moeda": (b.get("currencyCode") or "").upper() or None,
        "stake": numero(b.get("amount")),
        "stake_freebet": None,
        "odd": numero(b.get("cf")),
        "odd_calculada": False,
        "retorno": (None if status == "aberta" else
                    "0" if status == "perdida" else numero(b.get("profitAmount"))),
        "tipo": "multipla" if len(pernas) > 1 else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_tp",
    }
