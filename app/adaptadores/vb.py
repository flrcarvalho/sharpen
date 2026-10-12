"""Adaptador da família Altenar (`vb`: VaideBet, Esportiva, Estrela Bet, Vavada e espelhos; s409).

O cru é um item de `GetBets`/`GetBetsHistory` da Altenar, o mesmo que o `vb_inject.js`
escuta. A leitura de cada campo é a do `formatTicketVB` do `content.js` e da
`CASA_VAIDEBET.md`:

  • `totalStake` é a stake (no sistema, o TOTAL das linhas); `totalWin` é o retorno no
    bilhete processado e o POTENCIAL no aberto, onde não vira retorno.
  • `status` 0 aberta · 2 perdida (retorno zero) · 1 ganha (retorno acima da stake; igual =
    anulada; no SISTEMA também abaixo da stake, quando só parte das linhas paga: BetMartini
    5501637823, 39,27 em 3 duplas, uma paga 13,09 × 2,2 = 28,79) · 8 anulada (retorno = stake, s285) · 4 e 18 cashout (o valor encerrado mora no
    `totalWin`, s310; o dinheiro decide W/V no `derivar`). Qualquer outro, RECUSA.
  • odd da casa: `totalOdds`, que na múltipla é o produto EXATO das pernas (49 de 49 crus de
    12/10). No SISTEMA (`type` 2) a casa manda a média das linhas ARREDONDADA em 2 casas
    (5,12 contra 5,118436): a odd sai da média exata das linhas (`MASTER_RESULTADO §7.3`),
    `combLength` = tamanho de cada linha, e `odd_calculada` = true. Linha com DUAS pernas do
    mesmo jogo (`eventId`) não existe: a casa não combina seleções do mesmo jogo, e o
    `linesCount` confirma (BetMartini 5501645421: duplas de 4 pernas com um jogo repetido =
    5 linhas, não 6; 5501645422: triplas = 2, não 4).
  • perna: `price` é a odd; `status` 0 aberta · 1 ganha · 2 perdida · 8 anulada. O esporte vem
    só como id (`sportTypeId`), e vai assim: traduzir é do dicionário, não do adaptador.
  • Bet builder (`isBetBuilder`), bônus (`bonusPart`), cashout parcial (`partialCashouts`) e
    `finalStake` diferente da stake não estão medidos nos 49 crus: RECUSA com o motivo.
"""
from __future__ import annotations

from decimal import Decimal
from itertools import combinations

from . import Recusa, numero

_PERNA = {0: "aberta", 1: "ganha", 2: "perdida", 8: "anulada"}
_CASHOUT = {4, 18}
_CENTAVO = Decimal("0.005")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict):
        for k in ("bets", "Bets", "data"):
            if isinstance(resposta.get(k), list):
                return resposta[k]
    return resposta if isinstance(resposta, list) else []


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _status(t: dict) -> str:
    st = t.get("status")
    if st == 0:
        return "aberta"
    stake, ret = _d(t.get("totalStake")), _d(t.get("totalWin"))
    if stake is None or ret is None:
        raise Recusa(f"status {st!r} sem totalStake ou sem totalWin")
    igual = abs(ret - stake) <= _CENTAVO
    if st == 2 and ret == 0:
        return "perdida"
    if st == 1 and igual:
        return "anulada"
    if st == 1 and ret > stake:
        return "ganha"
    if st == 1 and 0 < ret < stake and t.get("type") == 2:
        return "ganha"          # sistema em que só parte das linhas pagou (W = retorno ÷ stake)
    if st == 8 and igual:
        return "anulada"
    if st in _CASHOUT:
        if (_d(t.get("cashOutValue")) or 0) > 0 or (_d(t.get("partialCashOut")) or 0) > 0:
            raise Recusa(f"cashout com cashOutValue/partialCashOut preenchido (nunca medido)")
        return "cashout"
    raise Recusa(f"status {st!r} com retorno {ret} sobre stake {stake} (a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or not t.get("id"):
        raise Recusa("bilhete sem id")
    if (_d(t.get("bonusPart")) or 0) != 0 or t.get("partialCashouts"):
        raise Recusa("bônus ou cashout parcial ainda não medido na Altenar (a conferir)")
    if _d(t.get("finalStake")) not in (None, _d(t.get("totalStake"))):
        raise Recusa(f"finalStake {t.get('finalStake')} difere de totalStake {t.get('totalStake')}")
    status = _status(t)
    sels = t.get("selections") or []
    if not sels:
        raise Recusa("bilhete sem selections")
    pernas, precos, jogos = [], [], []
    for s in sels:
        if s.get("isBetBuilder"):
            raise Recusa("bet builder ainda não medido na Altenar (a conferir)")
        if s.get("status") not in _PERNA:
            raise Recusa(f"perna com status {s.get('status')!r} não mapeado")
        p = _d(s.get("price"))
        if p is None or p <= 0:
            raise Recusa("perna sem price")
        precos.append(p)
        jogos.append(s.get("eventId"))
        pernas.append({
            "esporte_casa": f"sportTypeId {s.get('sportTypeId')}" if s.get("sportTypeId") is not None else None,
            "evento": " ".join(str(s.get("eventName") or "").split()),
            "mercado_casa": " ".join(str(s.get("marketName") or "").split()),
            "selecao_casa": " ".join(str(s.get("name") or "").split()),
            "odd": numero(s.get("price")),
            "inicio": s.get("eventDate") or None,
            "status_perna": _PERNA[s.get("status")],
        })
    sistema = t.get("type") == 2
    if sistema:
        k = t.get("combLength")
        if not isinstance(k, int) or not 1 <= k < len(precos):
            raise Recusa(f"sistema com combLength {k!r} ilegível")
        linhas = []
        for c in combinations(range(len(precos)), k):
            ids = [jogos[i] for i in c if jogos[i] is not None]
            if len(set(ids)) < len(ids):
                continue        # duas pernas do mesmo jogo: a casa não monta essa linha
            x = Decimal(1)
            for i in c:
                x *= precos[i]
            linhas.append(x)
        if not linhas or t.get("linesCount") not in (None, len(linhas)):
            raise Recusa(f"sistema com linesCount {t.get('linesCount')} ≠ {len(linhas)} combinações")
        odd, calculada = numero(str(sum(linhas) / len(linhas))), True
        rotulo = f"{len(linhas)} x {k} de {len(precos)}"
    else:
        odd, calculada, rotulo = numero(t.get("totalOdds")), False, None
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["id"]),
        "colocada_em": t.get("createdDate") or None,
        "liquidada_em": None,              # a Altenar não manda o instante da liquidação
        "status": status,
        "status_casa": f"status {t.get('status')} · type {t.get('type')}",
        "moeda": (t.get("currency") or "").upper() or None,
        "stake": numero(t.get("totalStake")),
        "stake_freebet": None,
        "odd": odd,
        "odd_calculada": calculada,
        "retorno": numero(t.get("totalWin")) if status != "aberta" else None,
        "tipo": "sistema" if sistema else ("multipla" if len(pernas) > 1 else "simples"),
        "sistema": rotulo,
        "pernas": pernas,
        "origem": "servidor:adaptador_vb",
    }
