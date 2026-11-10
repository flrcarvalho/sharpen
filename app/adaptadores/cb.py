"""Adaptador da Cloudbet (família `cb`, plataforma própria, só o sportsbook; s442).

O cru é o que o `cb_inject.js` monta por aposta: `{aposta, posicao, eventos}`.
  • `aposta`: um item de `bets` de `GET /sports-betting/v4/bets/positions/{positionId}` (o
    detalhe, pedido na moeda NATIVA da aposta);
  • `posicao`: o item de `GET /sports-betting/v4/bets/positions` de onde ela saiu. Os nomes de
    mercado (`marketName`) e de seleção (`outcomeName`) só existem aqui;
  • `eventos`: `{eventId: evento}` das pernas, de `GET /sports-api/v6/sports/events/{id}`, só os
    campos do jogo (nome, esporte, liga, `cutoffTime`, mandante e visitante).
A leitura de cada campo é a do `formatTicketCB` do `content.js` e da `CASA_CLOUDBET.md`; escrito
da fixture da bancada (`extensor/harness/fixtures/cloudbet.recon.json`, 10/11/2026, conta em
USDT: 15 abertas e 4 perdidas, todas múltiplas de 3).

  • CÓDIGO = `uuid` da aposta, o "ID:" do card expandido. O `positionId` não é código.
  • STATUS: `state` ACCEPTED é aberta. Liquidada pelo DINHEIRO: retorno = stake é anulada,
    qualquer rótulo; perdida só com `result` LOSS e retorno 0; ganha com `result` WIN e retorno
    que fecha com stake × `price` em 1 centavo, ou com perna PUSH (a casa refaz a odd sem ela;
    o `ficha.derivar` chega a retorno ÷ stake). O resto, RECUSA.
  • ⚠ DINHEIRO: `returnAmount` é o LUCRO (−30 na perdida de 30). O retorno é stake +
    returnAmount: é a única conta que o adaptador faz.
  • odd da casa: `price` (o "@ 6.93" do card, 6,934). A da lista é 0 nas perdidas.
  • BET BUILDER (`SAME_GAME_PARLAY`): cada perna leva a odd do Criar Aposta do SEU jogo, e a
    odd do bilhete é o produto dos jogos (3,52 × 1,97 = 6,934). As seleções de um mesmo jogo
    viram UMA perna `Bet Builder` (D43, como o `sbi`), seleções juntas por `;`, odd do grupo.
  • data: `cutoffTime` do evento é o início (o `ficha.derivar` escolhe a perna). A aberta traz
    `completeTime` 0001-01-01: data sentinela não vira liquidação.
  • Sem amostra, RECUSA: cashout (`isCashoutBet`), posição com mais de uma aposta, perna sem
    evento. O texto continua levando esses bilhetes à IA.
"""
from __future__ import annotations

import re
from decimal import Decimal

from . import Recusa, numero

_PERNA = {"WIN": "ganha", "LOSS": "perdida", "PUSH": "anulada"}
_MEIO_CENTAVO = Decimal("0.005")
_UM_CENTAVO = Decimal("0.01")
_LINHA = re.compile(r"\s([+-]?\d+(?:\.\d+)?)$")


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _dec(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _chave(s: dict) -> tuple:
    return tuple(str(s.get(k) if s.get(k) is not None else "") for k in ("eventId", "marketKey", "outcome", "params"))


def bilhetes_da_resposta(resposta) -> list:
    """Os crus por aposta. Aceita a lista de crus ou a fixture da bancada, que guarda as quatro
    respostas da casa juntas (`lista_abertas`, `lista_liquidadas`, `detalhes`, `eventos`) e é
    montada aqui do mesmo jeito que o `cb_inject.js` monta (a liquidada vence a aberta)."""
    if isinstance(resposta, list):
        return resposta
    if not isinstance(resposta, dict) or not isinstance(resposta.get("detalhes"), dict):
        return []
    itens = {}
    for lista in ("lista_abertas", "lista_liquidadas"):
        for it in (resposta.get(lista) or {}).get("items") or []:
            ex = itens.get(it.get("positionId"))
            if not ex or ex.get("positionStatus") != "COMPLETED":
                itens[it.get("positionId")] = it
    eventos = resposta.get("eventos") or {}
    out = []
    for pid, det in resposta["detalhes"].items():
        it = itens.get(pid)
        if not it:
            continue
        for bet in det.get("bets") or []:
            ids = {str(s.get("eventId")) for s in bet.get("selections") or []}
            out.append({"aposta": bet, "posicao": it,
                        "eventos": {i: eventos[i] for i in ids if i in eventos}})
    return out


def codigo(cru) -> str:
    a = (cru or {}).get("aposta") if isinstance(cru, dict) else None
    return "" if not isinstance(a, dict) or not a.get("uuid") else str(a["uuid"])


def _iso(v) -> str | None:
    """ISO da casa, ou None para vazio e para a sentinela `0001-01-01` (aberta)."""
    s = _limpo(v)
    return None if not s or s.startswith("0001-") else s


def _status(a: dict) -> tuple[str, Decimal | None]:
    """(status da Ficha, retorno)."""
    if a.get("state") == "ACCEPTED":
        return "aberta", None
    res = a.get("result")
    stake, lucro, odd = _dec(a.get("stake")), _dec(a.get("returnAmount")), _dec(a.get("price"))
    if stake is None or stake <= 0 or lucro is None:
        raise Recusa(f"state {a.get('state')!r} result {res!r} sem stake ou sem returnAmount")
    ret = stake + lucro
    if abs(ret - stake) <= _MEIO_CENTAVO:
        return "anulada", ret          # o dinheiro decide: P/L zero, qualquer que seja o rótulo
    if res == "LOSS":
        if abs(ret) <= _MEIO_CENTAVO:
            return "perdida", Decimal(0)
        raise Recusa(f"LOSS com returnAmount {a.get('returnAmount')!r} sobre stake {a.get('stake')!r} (a conferir)")
    if res == "WIN" and ret > stake:
        if odd and abs(ret - stake * odd) <= _UM_CENTAVO:
            return "ganha", ret
        if any(s.get("result") == "PUSH" for s in a.get("selections") or []):
            return "ganha", ret        # perna anulada: a casa refaz a odd, o retorno manda
    raise Recusa(f"state {a.get('state')!r} result {res!r} com returnAmount {a.get('returnAmount')!r} "
                 f"sobre stake {a.get('stake')!r} e price {a.get('price')!r} (sem amostra; a conferir)")


def _estado_grupo(sels: list, aberta: bool) -> str | None:
    if aberta:
        return "aberta"
    rs = {s.get("result") for s in sels}
    if "LOSS" in rs:
        return "perdida"
    if rs == {"WIN"}:
        return "ganha"
    if len(sels) == 1:
        return _PERNA.get(sels[0].get("result"))   # PENDING de bilhete liquidado: None
    return None                                    # Criar Aposta com PUSH/PENDING: sem amostra


def _perna(sels: list, nomes: dict, ev: dict, bb: bool, aberta: bool) -> dict:
    partes = []
    for s in sels:
        n = nomes.get(_chave(s)) or {}
        partes.append((_limpo(n.get("marketName")), _limpo(n.get("outcomeName") or n.get("name"))))
    if bb:
        mercado = "Bet Builder"
        selecao = "; ".join(f"{m}: {o}" for m, o in partes)
        linha = None
    else:
        mercado, selecao = partes[0]
        ml = _LINHA.search(selecao)
        linha = numero(ml.group(1)) if ml else None
    comp = ev.get("competition") or {}
    return {
        "esporte_casa": _limpo((ev.get("sport") or {}).get("name")) or None,
        "liga_casa": _limpo(comp.get("name")) or None,
        "evento": _limpo(ev.get("name")),
        "mandante": _limpo((ev.get("home") or {}).get("name")) or None,
        "visitante": _limpo((ev.get("away") or {}).get("name")) or None,
        "mercado_casa": mercado,
        "selecao_casa": selecao,
        "linha": linha,
        "odd": numero(sels[0].get("price")),   # no Criar Aposta, a odd do grupo (todas iguais)
        "inicio": _iso(ev.get("cutoffTime")),
        "status_perna": _estado_grupo(sels, aberta),
    }


def adaptar(cru: dict, casa_key: str) -> dict:
    a = (cru or {}).get("aposta") if isinstance(cru, dict) else None
    if not isinstance(a, dict):
        raise Recusa("cru sem a aposta do detalhe")
    cod = codigo(cru)
    if not cod:
        raise Recusa("aposta sem uuid")
    if a.get("isCashoutBet") is True:
        raise Recusa("cashout sem amostra (o texto leva à IA)")
    pos = cru.get("posicao") or {}
    if (_dec(pos.get("betCount")) or 1) > 1:
        raise Recusa(f"posição com {pos.get('betCount')} apostas, sem amostra")
    status, ret = _status(a)
    sels = a.get("selections") or []
    if not sels:
        raise Recusa("aposta sem selections")
    nomes = {_chave(s): s for p in pos.get("positions") or [] for s in p.get("selections") or []}
    eventos = cru.get("eventos") or {}
    # Grupos por jogo, na ordem da casa.
    grupos: dict[str, list] = {}
    for s in sels:
        grupos.setdefault(str(s.get("eventId")), []).append(s)
    bb_tipo = a.get("type") == "SAME_GAME_PARLAY"
    pernas = []
    for eid, g in grupos.items():
        ev = eventos.get(eid)
        if not isinstance(ev, dict) or not _limpo(ev.get("name")):
            raise Recusa(f"perna sem o evento {eid} (jogo e início vêm dele)")
        if any(_chave(s) not in nomes for s in g):
            raise Recusa(f"perna do evento {eid} sem nome de mercado na posição")
        if len(g) > 1 and not bb_tipo:
            raise Recusa(f"{len(g)} seleções do mesmo jogo fora de Bet Builder, sem amostra")
        if len({str(s.get("price")) for s in g}) > 1:
            raise Recusa(f"Bet Builder do evento {eid} com odds diferentes por perna, sem amostra")
        pernas.append(_perna(g, nomes, ev, len(g) > 1, status == "aberta"))
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": _iso(a.get("createTime")),
        "liquidada_em": _iso(a.get("completeTime")) if status != "aberta" else None,
        "status": status,
        "status_casa": f"state {a.get('state')} · result {a.get('result')} · type {a.get('type')}",
        "moeda": _limpo(a.get("baseCurrency")).upper() or None,
        "stake": numero(_dec(a.get("stake"))),
        "stake_freebet": None,
        "odd": numero(a.get("price")),
        "odd_calculada": False,
        "retorno": None if ret is None else numero(ret),
        "tipo": "multipla" if len(pernas) > 1 else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_cb",
    }
