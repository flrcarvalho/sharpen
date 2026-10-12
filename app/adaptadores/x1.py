"""Adaptador da família 1xBet (`x1`: 1xBet, Megapari, PariPesa, SapphireBet, 1xBit; s409).

O cru é um item de `BetInfos` do `GetBetInfoHistoryWithSummaryByDates`, o mesmo que o
`x1_inject.js` escuta (`parseBet`). A leitura de cada campo é a do `formatTicket1X` do
`content.js` e da `CASA_1XBET.md`; escrito a partir das fixtures da bancada
(`extensor/harness/fixtures/*.bethistory.json`, 5 casas, 119 bilhetes distintos), ANTES do 1º
cru real chegar ao banco. Régua no mesmo dia em que o cru do Gabriel chegar.

  • `BetSum` é a stake; `WinSum` o retorno (só existe na resolvida); `PossibleWinSum` é só
    potencial e nunca vira retorno. Datas em epoch SEGUNDOS (`BetDate`, `BetSettlingDate`,
    `StartDate` da perna).
  • `BetStatus` 1 aberta · 2 perdida (retorno zero) · 4 ganha. **A anulada não tem status
    próprio:** vem como 4 com `WinSum == BetSum` (16001193: apostou 10, recebeu 10), e é o
    dinheiro que separa V de W. No SISTEMA, 4 com retorno abaixo da stake é ganha parcial
    (W = retorno ÷ stake, `MASTER_RESULTADO §7.1`). Qualquer outro status, RECUSA.
  • odd da casa: `Coef` (precisão completa; o `CoefView` é truncado, é o do card). **Na
    perdida com perna anulada o `Coef` está velho** (a casa só recalcula quando ganha: 9 de 9
    perdidas ficam pré-anulação, 16101007 diz 8,607956 onde a estrutura é 4,5787). Ali a odd é
    o produto das pernas com a anulada valendo 1, como o `_oddEstruturalX1`, e
    `odd_calculada` = true.
  • SISTEMA (`BetTypeId` 2, SapphireBet): o `Coef` dele não é o produto das pernas, e o
    sistema perdido vem SEM `Coef`. Sem a odd da casa, RECUSA (a IA lê pelo texto, que diz
    "deixe a odd vazia"): o produto das pernas ali seria conta inventada.
  • perna: `Coef == 1` é a perna ANULADA (o texto `ReturnedBetEventReasonName` só vem em 6
    de 18). `EventResult` é 0 em todas as 329 pernas das fixtures: não diz se a perna ganhou
    ou perdeu, e por isso o status das outras pernas vai vazio (ausência, não palpite).
"""
from __future__ import annotations

from decimal import Decimal

from . import Recusa, iso_de_epoch, numero

_CENTAVO = Decimal("0.005")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict) and isinstance(resposta.get("BetInfos"), list):
        return resposta["BetInfos"]
    return resposta if isinstance(resposta, list) else []


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _status(t: dict, sistema: bool) -> str:
    st = t.get("BetStatus")
    if st == 1:
        return "aberta"
    stake, ret = _d(t.get("BetSum")), _d(t.get("WinSum"))
    if stake is None or stake <= 0:
        raise Recusa(f"BetStatus {st!r} sem BetSum")
    if st == 2:
        if ret not in (None, Decimal(0)):
            raise Recusa(f"perdida com WinSum {ret} (a conferir)")
        return "perdida"
    if st == 4 and ret is not None:
        if abs(ret - stake) <= _CENTAVO:
            return "anulada"          # a casa não tem status de anulada: o dinheiro decide
        if ret > stake or (sistema and ret > 0):
            return "ganha"
    raise Recusa(f"BetStatus {st!r} com WinSum {t.get('WinSum')!r} sobre {stake} (a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or t.get("BetId") in (None, ""):
        raise Recusa("bilhete sem BetId")
    evs = t.get("Events") or []
    if not evs:
        raise Recusa("bilhete sem Events")
    sistema = t.get("BetTypeId") == 2
    status = _status(t, sistema)
    pernas, produto, tem_anulada = [], Decimal(1), False
    for e in evs:
        c = _d(e.get("Coef"))
        if c is None or c <= 0:
            raise Recusa("perna sem Coef")
        produto *= c
        anulada = c == 1
        tem_anulada = tem_anulada or anulada
        jogo = e.get("GameName") or " x ".join(x for x in (e.get("Opp1Name"), e.get("Opp2Name")) if x)
        pernas.append({
            "esporte_casa": " ".join(str(e.get("SportName") or "").split()) or None,
            "evento": " ".join(str(jogo or "").split()),
            "mercado_casa": " ".join(str(e.get("EventTypeName") or "").split()),
            "selecao_casa": None,         # a 1xBet escreve a seleção dentro do mercado
            "odd": numero(e.get("Coef")),
            "inicio": iso_de_epoch(e.get("StartDate")),
            "status_perna": "anulada" if anulada else None,
        })
    decl = _d(t.get("Coef"))
    if decl is not None and decl <= 0:
        decl = None
    if sistema:
        if decl is None:
            raise Recusa("sistema sem Coef: a casa não informa a cotação (a IA deixa a odd vazia)")
        odd, calculada = numero(t.get("Coef")), False
    elif decl is None:
        odd, calculada = numero(str(produto)), True
    elif tem_anulada and abs(decl - produto) / produto > Decimal("0.01"):
        # Perdida com perna anulada: o `Coef` é o de antes da anulação.
        odd, calculada = numero(str(produto)), True
    else:
        odd, calculada = numero(t.get("Coef")), False
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["BetId"]),
        "colocada_em": iso_de_epoch(t.get("BetDate")),
        "liquidada_em": iso_de_epoch(t.get("BetSettlingDate")) if status != "aberta" else None,
        "status": status,
        "status_casa": (f"BetStatus {t.get('BetStatus')} · BetTypeId {t.get('BetTypeId')} · "
                        f"BetSystemType {t.get('BetSystemType')}"),
        "moeda": (t.get("CurrencyCode") or "").upper() or None,
        "stake": numero(t.get("BetSum")),
        "stake_freebet": None,
        "odd": odd,
        "odd_calculada": calculada,
        "retorno": (None if status == "aberta" else
                    "0" if status == "perdida" else numero(t.get("WinSum"))),
        "tipo": "sistema" if sistema else ("multipla" if len(pernas) > 1 else "simples"),
        "sistema": (f"{t.get('BetTypeName') or ''} · BetSystemType {t.get('BetSystemType')}".strip()
                    if sistema else None),
        "pernas": pernas,
        "origem": "servidor:adaptador_x1",
    }
