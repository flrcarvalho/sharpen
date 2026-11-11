"""Adaptador da 3et (família `et`, plataforma própria, só o sportsbook; s441).

O cru é um item de `content` de `GET /betting/v3/eurasian/statement/reports/betsByDate`
(liquidada, PLANA) ou de `GET /betting/v3/eurasian/reports/bets/current/normal` (aberta,
EMBRULHADA em `{bet:{…}, betType, translatedBetType}`), o mesmo que o `et_inject.js` escuta
(`parseBet`), mais `moeda_conta`, que o inject anexa (o bilhete não diz a moeda). A leitura de
cada campo é a do `formatTicketET` do `content.js` e da `CASA_3ET.md`; escrito das fixtures da
bancada (`extensor/harness/fixtures/3et.*.json`, 13 liquidadas e 4 abertas, conta do Feca, USD).

  • CÓDIGO = `betId` do bilhete (8 dígitos). As pernas têm `betId` de outra série: não é código.
  • STATUS da liquidada é `status.result` (Win · Lose); da aberta, `status` "Open".
  • ⚠ DINHEIRO: `profit` (e `payout`) é o LUCRO. O retorno é `stake + profit` (22 + 127,908 =
    149,908): é a única conta que o adaptador faz, porque a casa não publica o retorno bruto.
  • ganha só se o retorno fecha com stake × `odds` em 1 centavo; retorno = stake é anulada,
    qualquer rótulo; perdida só com retorno 0. O resto, RECUSA.
  • odd da casa: `odds`, a do card (na dupla ganha, 6,814; o produto das pernas, 6,815, não fecha).
  • data: a casa não publica início de evento. As pernas vão sem `inicio`, e o `ficha.derivar`
    usa a colocação (`datePlaced`, ISO UTC).
  • JOGO: a casa escreve `A vs B` ou, no esporte americano, `A at B` (visitante em casa do
    mandante). Os dois viram `A vs B`, na ORDEM da casa, para o `descricao_ficha._times` achar os
    times (o `{time}` do mercado `Team Points <time>`). Mandante e visitante ficam VAZIOS: nada
    aqui decide quem é a casa.
  • MERCADO: `marketName`, mais o período entre parênteses quando não é o jogo inteiro e o
    mercado ainda não o diz (`Moneyline First Half` já diz).
  • SIMPLES (s443, conta do Gabriel, `3et.simples.*.json`): a casa não manda `legs`, e a seleção
    vem solta no bilhete. Liquidada: `selection.event/competition`, `betType.sport/period`,
    `marketName`, `runnerName`. Aberta: plana no `bet`, com a liga no EMBRULHO (`competition`) e o
    `runnerName` repetindo o mercado (`Total Touchdowns  (Over 5.5)`); a repetição sai e fica o que
    a liquidada do mesmo bilhete diz (`Over 5.5`). O `eventStartDate` do embrulho NÃO vira
    `inicio`: a liquidada não o traz, e a data da aposta mudaria ao liquidar.
  • PUSH numa perna de múltipla é a perna anulada (52019175, DNB empatado). O bilhete continua
    decidido pelo dinheiro.
  • Sem amostra, RECUSA: `freeBetStake` > 0, `trueStake` ≠ `stake`, `isExchange`, e qualquer
    `status.result` além de Win/Lose (no bilhete) ou Win/Lose/Push (na perna). O texto continua
    levando esses bilhetes à IA.
"""
from __future__ import annotations

import re
from decimal import Decimal

from . import Recusa, numero

_PERNA = {"Win": "ganha", "Lose": "perdida", "Push": "anulada"}
_MEIO_CENTAVO = Decimal("0.005")
_UM_CENTAVO = Decimal("0.01")
_LINHA = re.compile(r"\s([+-]?\d+(?:\.\d+)?)$")
_JOGO_INTEIRO = {"full time", "match", "game", ""}


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict) and isinstance(resposta.get("content"), list):
        return resposta["content"]
    return resposta if isinstance(resposta, list) else []


def _bet(cru) -> dict:
    if isinstance(cru, dict) and isinstance(cru.get("bet"), dict):
        return cru["bet"]
    return cru if isinstance(cru, dict) else {}


def codigo(cru) -> str:
    """`betId` do bilhete, embrulhado (aberta) ou plano (liquidada)."""
    b = _bet(cru)
    return "" if b.get("betId") in (None, "") else str(b["betId"])


def _dec(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _aberta(b: dict) -> bool:
    return b.get("status") == "Open"


def _resultado(b: dict) -> str:
    st = b.get("status")
    return st.get("result") if isinstance(st, dict) else ""


def _status(b: dict) -> tuple[str, Decimal | None]:
    """(status da Ficha, retorno)."""
    if _aberta(b):
        return "aberta", None
    stake, lucro, odd = _dec(b.get("stake")), _dec(b.get("profit")), _dec(b.get("odds"))
    res = _resultado(b)
    if stake is None or stake <= 0 or lucro is None:
        raise Recusa(f"result {res!r} sem stake ou sem profit")
    ret = stake + lucro
    if abs(ret - stake) <= _MEIO_CENTAVO:
        return "anulada", ret         # o dinheiro decide: P/L zero, qualquer que seja o rótulo
    if res == "Lose":
        if abs(ret) <= _MEIO_CENTAVO:
            return "perdida", Decimal(0)
        raise Recusa(f"Lose com profit {b.get('profit')!r} sobre stake {b.get('stake')!r} (a conferir)")
    if res == "Win" and odd and abs(ret - stake * odd) <= _UM_CENTAVO:
        return "ganha", ret
    raise Recusa(f"result {res!r} com profit {b.get('profit')!r} sobre stake {b.get('stake')!r} "
                 f"e odds {b.get('odds')!r} (sem amostra; a conferir)")


def _evento(nome: str) -> str:
    """`A at B` → `A vs B`, na ordem da casa. Mais de um ` at ` não se parte (fica como veio)."""
    return nome.replace(" at ", " vs ") if nome.count(" at ") == 1 and " vs " not in nome else nome


def _mercado(p: dict) -> str:
    m, per = _limpo(p.get("marketName")), _limpo(p.get("periodName"))
    if per.casefold() in _JOGO_INTEIRO or per.casefold() in m.casefold():
        return m
    return f"{m} ({per})"


def _sem_mercado_repetido(sel: str, mercado: str) -> str:
    """`Total Touchdowns  (Over 5.5)` com mercado `Total Touchdowns` → `Over 5.5` (o que a
    liquidada do mesmo bilhete diz). Qualquer outra forma fica como veio."""
    m = re.fullmatch(re.escape(mercado) + r"\s*\((.+)\)", sel) if mercado else None
    return _limpo(m.group(1)) if m else sel


def _perna_simples(cru, b: dict) -> dict:
    """A simples não tem `legs`: monta a perna com os campos soltos do bilhete."""
    if _aberta(b):
        p = {k: b.get(k) for k in ("odds", "eventName", "sportName", "marketName", "periodName")}
        p["competition"] = b.get("competition") or (cru.get("competition") if isinstance(cru, dict) else None)
        p["runnerName"] = _sem_mercado_repetido(_limpo(b.get("runnerName")), _limpo(b.get("marketName")))
        return p
    sel = b.get("selection") if isinstance(b.get("selection"), dict) else {}
    bt = b.get("betType") if isinstance(b.get("betType"), dict) else {}
    return {"odds": b.get("odds"), "eventName": sel.get("event"), "competition": sel.get("competition"),
            "sportName": bt.get("sport"), "marketName": b.get("marketName") or bt.get("marketType"),
            "runnerName": b.get("runnerName") or sel.get("runner"), "periodName": bt.get("period")}


def _perna(p: dict, estado) -> dict:
    sel = _limpo(p.get("runnerName"))
    ml = _LINHA.search(sel)
    return {
        "esporte_casa": _limpo(p.get("sportName")) or None,
        "liga_casa": _limpo(p.get("competition")) or None,
        "evento": _evento(_limpo(p.get("eventName"))),
        "mandante": None,
        "visitante": None,
        "mercado_casa": _mercado(p),
        "selecao_casa": sel,
        "linha": numero(ml.group(1)) if ml else None,
        "odd": numero(p.get("odds")),
        "inicio": None,               # a casa não publica o início do evento
        # "" = bilhete aberto (a perna só diz o andamento, `finished`/`graded`, que não é
        # resultado); rótulo fora de Win/Lose/Push (simples com rótulo novo) = None, nunca palpite.
        "status_perna": "aberta" if estado == "" else _PERNA.get(estado),
    }


def adaptar(cru: dict, casa_key: str) -> dict:
    b = _bet(cru)
    cod = codigo(cru)
    if not cod:
        raise Recusa("bilhete sem betId")
    if b.get("isExchange") is True:
        raise Recusa("aposta da exchange (fora da captura: só o sportsbook)")
    fb = _dec(b.get("freeBetStake"))
    if fb is not None and fb != 0:
        raise Recusa(f"freeBetStake {b.get('freeBetStake')!r} sem amostra (o texto leva à IA)")
    stake, real = _dec(b.get("stake")), _dec(b.get("trueStake"))
    if real is not None and stake is not None and abs(real - stake) > _MEIO_CENTAVO:
        raise Recusa(f"trueStake {b.get('trueStake')!r} ≠ stake {b.get('stake')!r} sem amostra")
    status, ret = _status(b)
    legs = b.get("legs") or []
    if not legs and (b.get("marketName") or b.get("selection") or b.get("eventName")):
        legs = [_perna_simples(cru, b)]
    if not legs:
        raise Recusa("bilhete sem legs")
    multipla = len(legs) > 1
    pernas = []
    for p in legs:
        if status == "aberta":
            est = ""
        elif multipla:
            st = p.get("status")
            est = st.get("result") if isinstance(st, dict) else None
            if est not in _PERNA:
                raise Recusa(f"perna com result {est!r} sem amostra")
        else:
            est = _resultado(b)
        pernas.append(_perna(p, est))
    moeda = cru.get("moeda_conta") if isinstance(cru, dict) else None
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": b.get("datePlaced") or None,
        "liquidada_em": (b.get("dateSettled") or None) if status != "aberta" else None,
        "status": status,
        "status_casa": f"result {_resultado(b) or b.get('status')} · betStatus {b.get('betStatus')} · "
                       f"multiplier {b.get('multiplierName')}",
        "moeda": moeda if isinstance(moeda, str) and moeda.strip() else None,
        "stake": numero(stake),
        "stake_freebet": None,
        "odd": numero(b.get("odds")),
        "odd_calculada": False,
        "retorno": None if ret is None else numero(ret),
        "tipo": "multipla" if multipla else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_et",
    }
