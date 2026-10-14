"""Adaptador da família BetBy (`jb`: Jonbet, Betboom, Blaze, Bet Panda, Betfury, Duel, Betcoin; s409).

O cru é um item de `GET …/bets` da BetBy, o mesmo que o `jb_inject.js` escuta (`parseBet`).
A leitura de cada campo é a do `formatTicketJB` do `content.js`:

  • `sum` é a stake (não existe `stake`). `result_sum` é o retorno LIQUIDADO (0 na perdida,
    ausente na aberta); `potential_win` é só potencial e nunca vira retorno.
  • `status` do bilhete: `open` aberta · `lost` perdida (só com retorno zero) · `won` ganha
    (só com retorno acima da stake) · `refund` e `canceled` anulada (só com retorno = stake) ·
    `cashed out` cashout (o dinheiro decide W/V no `derivar`). Qualquer outro enum, ou um
    enum conhecido com o dinheiro dizendo outra coisa, RECUSA: nunca chute.
  • odd da casa: **o produto das pernas**, não o `k`/`total_k`. Medido nos 232 crus de
    12/10 (Bet Panda e Duel): o `k` é o produto TRUNCADO em 3 casas (2,22 × 1,92 = 4,2624 →
    `k` 4,262), e a casa paga e mostra o potencial pelo produto inteiro (51 de 51 ganhas e 9
    de 9 abertas no centavo; pelo `k`, 4,367 × 25 "fecha" 109,18 só na borda da folga e
    grava a odd errada). `total_k` zera em toda perdida e vale a soma das linhas no sistema.
    - ComboBOOST: × `bonus.total_multiplier` (9,004 = 8,575344 × 1,05; retorno 23,95).
    - Perna `refund`: vale 1,00 na aberta e na ganha (é como a casa paga); na perdida e na
      anulada fica a odd ORIGINAL, sem tirar a perna (`MASTER_RESULTADO §5.1.1` e `§5.5.1`).
    - `odd_calculada` = true sempre que houve multiplicação (mais de uma perna ou boost).
  • sistema: `combinations` não vazio; `type` (`2/3`) é a estrutura; a odd é a MÉDIA das
    linhas (`MASTER_RESULTADO §7.3`), cada linha pelo produto das pernas do `combo`. O `k`
    do sistema liquidado é a soma das linhas GANHAS, e não serve de odd.
  • `currency` `$` não distingue USD de USDT (`CASA_BETPANDA.md`): moeda ausente, vale a
    da conta (decisão do Feca, D0 pergunta 5). Outra moeda vai como veio.
  • perna: `desc.scheduled` em epoch (s) é o início; `status` da perna `useless` (a casa
    não precisou decidir) fica sem status de perna.
"""
from __future__ import annotations

from decimal import Decimal

from . import Recusa, iso_de_epoch, numero

_PERNA = {"open": "aberta", "won": "ganha", "lost": "perdida", "refund": "anulada",
          "canceled": "anulada", "useless": None}
_SEM_MOEDA = {"$", ""}
_CENTAVO = Decimal("0.005")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict):
        for k in ("results", "bets", "items", "data"):
            if isinstance(resposta.get(k), list):
                return resposta[k]
    return resposta if isinstance(resposta, list) else []


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _status(t: dict) -> str:
    st = t.get("status")
    stake, ret = _d(t.get("sum")), _d(t.get("result_sum"))
    if st == "open":
        return "aberta"
    if st == "cashed out":
        if ret is None:
            raise Recusa("cashed out sem result_sum")
        return "cashout"
    if st not in ("lost", "won", "refund", "canceled"):
        raise Recusa(f"status {st!r} não mapeado (a conferir)")
    if ret is None or stake is None:
        raise Recusa(f"status {st!r} sem result_sum ou sem sum")
    if st == "lost" and ret == 0:
        return "perdida"
    # `canceled` (D31, s417): a casa cancelou e DEVOLVEU. Só é anulada com o dinheiro dizendo
    # isso (retorno = stake, como o `refund`); cancelada com outro retorno segue recusada.
    if st in ("refund", "canceled") and abs(ret - stake) <= _CENTAVO:
        return "anulada"
    if st == "won" and ret > stake:
        return "ganha"
    raise Recusa(f"status {st!r} com retorno {ret} sobre stake {stake} (a conferir)")


def _produto(odds: list[Decimal]) -> Decimal:
    p = Decimal(1)
    for o in odds:
        p *= o
    return p


def _odd_casa(t: dict, status: str, sels: list, sistema: bool) -> tuple[str | None, bool]:
    """(odd da casa, calculada?). Ver o cabeçalho: produto das pernas, nunca o `k` truncado."""
    odds = [_d(s.get("k")) for s in sels]
    if any(o is None or o <= 0 for o in odds):
        raise Recusa("perna sem odd (k)")
    if sistema:
        linhas = []
        for c in t["combinations"]:
            idx = c.get("combo") if isinstance(c, dict) else None
            if not idx or any(not isinstance(i, int) or not 1 <= i <= len(odds) for i in idx):
                raise Recusa(f"combinação do sistema ilegível: {c!r}")
            linhas.append(_produto([odds[i - 1] for i in idx]))
        return numero(str(sum(linhas) / len(linhas))), True
    if status in ("aberta", "ganha", "cashout"):
        odds = [Decimal(1) if s.get("status") in ("refund", "canceled") else o
                for s, o in zip(sels, odds)]
    bonus = t.get("bonus") or {}
    mult = _d(bonus.get("total_multiplier")) if isinstance(bonus, dict) else None
    mult = mult if mult and mult > 0 else Decimal(1)
    return numero(str(_produto(odds) * mult)), (len(odds) > 1 or mult != 1)


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or not t.get("id"):
        raise Recusa("bilhete sem id")
    if t.get("freebet_data"):
        raise Recusa("freebet ainda não mapeada na BetBy (a conferir)")
    status = _status(t)
    sistema = isinstance(t.get("combinations"), list) and len(t["combinations"]) > 0
    sels = t.get("selections") or []
    if not sels:
        raise Recusa("bilhete sem selections")
    pernas = []
    for s in sels:
        d = s.get("desc") or {}
        if s.get("status") not in _PERNA:
            raise Recusa(f"perna com status {s.get('status')!r} não mapeado")
        comp = [c.get("name") for c in (d.get("competitors") or []) if c and c.get("name")]
        ligas = [x.get("name") for x in (d.get("category"), d.get("tournament")) if x and x.get("name")]
        pernas.append({
            "esporte_casa": (d.get("sport") or {}).get("name") or None,
            "liga_casa": " / ".join(ligas) or None,
            "evento": " vs ".join(comp),
            "mercado_casa": s.get("market_name") or "",
            "selecao_casa": s.get("outcome_name") or "",
            "odd": numero(s.get("k")),
            "inicio": iso_de_epoch(d.get("scheduled")),
            "status_perna": _PERNA[s.get("status")],
        })
    odd, calculada = _odd_casa(t, status, sels, sistema)
    moeda = (t.get("currency") or "").strip()
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["id"]),
        "colocada_em": iso_de_epoch(t.get("timestamp")),
        "liquidada_em": None,              # a BetBy não manda o instante da liquidação
        "status": status,
        "status_casa": f"status {t.get('status')} · type {t.get('type')}",
        "moeda": None if moeda in _SEM_MOEDA else moeda.upper(),
        "stake": numero(t.get("sum")),
        "stake_freebet": None,
        "odd": odd,
        "odd_calculada": calculada,
        "retorno": numero(t.get("result_sum")) if status != "aberta" else None,
        "tipo": "sistema" if sistema else ("multipla" if len(pernas) > 1 else "simples"),
        "sistema": t.get("type") if sistema else None,
        "pernas": pernas,
        "origem": "servidor:adaptador_jb",
    }
