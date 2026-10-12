"""Adaptador da família Tivo (`tv`: Tivo, Betfast, MyStake; s409).

O cru é um item de `gethistory`, o mesmo que o `tv_inject.js` escuta (`parseTicket`). A
leitura de cada campo é a do `formatTicketTV` do `content.js` e da `CASA_TIVO.md`:

  • `Amount` é a stake; `WinAmount` o retorno (0 na perdida E na aberta); `PossibleWin` é
    só potencial. `ActionTime` e `Game.StartTime` em epoch MILISSEGUNDOS, UTC.
  • `Status` 5 + `Result` 0 = aberta. `Status` 10: `Result` 3 perdida (retorno zero);
    `Result` 2 com retorno acima da stake = ganha, igual à stake = anulada. `CashOut`
    marcado = cashout (o dinheiro decide W/V). Qualquer outra combinação, RECUSA.
  • odd da casa: `Koef`, precisão completa (a tela trunca em 2 casas). Na ganha, `WinKoef`,
    a LIQUIDADA: com perna anulada a casa recalcula sem ela (`Koef` 9,0288 × `WinKoef`
    4,104, retorno 410,40 sobre 100). Na perdida fica o `Koef`, sem tirar a perna
    (`MASTER_RESULTADO §5.5.1`).
  • `TicketType` 3 = FREEBET (badge "F" da MyStake, s392): a stake inteira é dinheiro da
    casa, `stake_freebet` = `Amount` (`MASTER_RESULTADO §5.8`). Outro `TicketType` que não
    0 ou 3, RECUSA.
  • perna (`Items[]`): `Result` 0 aberta · 1 anulada (provado pelo dinheiro, s211) · 2 ganha
    · 3 perdida · 6 meia derrota (s392). Mercado pode trazer `{p1_r}`, preenchido pelo
    `FinalPosition.p1` como o content faz; placeholder desconhecido fica como veio.
  • Sistema (`IsSystem`) e odd oferecida (`ItemType` 6, `OfferedOddObject`) não estão nos
    137 crus medidos (12/10): RECUSA com o motivo até haver amostra.
"""
from __future__ import annotations

import re
from decimal import Decimal

from . import Recusa, iso_de_epoch, numero

_PERNA = {0: "aberta", 1: "anulada", 2: "ganha", 3: "perdida", 6: "meio_perdida"}
_CENTAVO = Decimal("0.005")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict):
        for k in ("Tickets", "tickets", "Data", "data"):
            if isinstance(resposta.get(k), list):
                return resposta[k]
    return resposta if isinstance(resposta, list) else []


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _ms(v) -> str | None:
    return iso_de_epoch(v / 1000) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _nome(o) -> str:
    return str(o.get("Name") or "") if isinstance(o, dict) else ""


def _status(t: dict) -> str:
    st, res = t.get("Status"), t.get("Result")
    cru = f"Status {st} · Result {res}"
    if st == 5 and res == 0:
        return "aberta"
    if st != 10:
        raise Recusa(f"{cru}: combinação não mapeada (a conferir)")
    stake, ret = _d(t.get("Amount")), _d(t.get("WinAmount"))
    if stake is None or ret is None:
        raise Recusa(f"{cru}: liquidada sem Amount ou sem WinAmount")
    if t.get("CashOut"):
        return "cashout"
    if res == 3 and ret == 0:
        return "perdida"
    if res == 2 and abs(ret - stake) <= _CENTAVO:
        return "anulada"
    if res == 2 and ret > stake:
        return "ganha"
    raise Recusa(f"{cru}: retorno {ret} sobre stake {stake} (a conferir)")


def _mercado(it: dict) -> str:
    m = _nome(it.get("Market"))
    fp = it.get("FinalPosition") or {}
    if fp.get("p1") is not None:
        m = m.replace("{p1_r}", f"{fp['p1']}º")
    return re.sub(r"\s+", " ", m).strip()


def _linha(fp: dict) -> str | None:
    """`hisminus: true` INVERTE o sinal da linha (s392, provado na tela da MyStake: `h: -0.75,
    hisminus: true` aparece como `2 (0.75)`), a mesma regra do `_textoTV` da extensão. Sem
    isto a descrição da casa virada gravaria o handicap de sinal trocado."""
    h = fp.get("h")
    if isinstance(h, (int, float)) and not isinstance(h, bool) and h and fp.get("hisminus"):
        h = -h
    return numero(h)


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or t.get("ID") is None:
        raise Recusa("bilhete sem ID")
    if t.get("IsSystem"):
        raise Recusa("sistema da Tivo ainda não medido (a conferir)")
    tt = t.get("TicketType")
    if tt not in (0, 3, None):
        raise Recusa(f"TicketType {tt!r} não mapeado")
    status = _status(t)
    itens = t.get("Items") or []
    if not itens:
        raise Recusa("bilhete sem Items")
    pernas = []
    for it in itens:
        if it.get("ItemType") == 6 or it.get("OfferedOddObject"):
            raise Recusa("odd oferecida (ItemType 6) ainda não medida (a conferir)")
        if it.get("Result") not in _PERNA:
            raise Recusa(f"perna com Result {it.get('Result')!r} não mapeado")
        g, og = it.get("Game") or {}, it.get("OutrightGame") or {}
        if g:
            evento = " vs ".join(x for x in (_nome(g.get("Team1")), _nome(g.get("Team2"))) if x)
            inicio = _ms(g.get("StartTime"))
        else:
            evento = _nome(it.get("Outright")) if isinstance(it.get("Outright"), dict) else str(it.get("Outright") or "")
            inicio = _ms(og.get("StartTime"))
        fp = it.get("FinalPosition") or {}
        ligas = [x for x in (_nome(it.get("Region")), _nome(it.get("Champ"))) if x]
        pernas.append({
            "esporte_casa": _nome(it.get("Sport")) or None,
            "liga_casa": " / ".join(ligas) or None,
            "evento": evento,
            "mercado_casa": _mercado(it),
            "selecao_casa": _nome(it.get("Position")) or _nome(og.get("Team1")),
            "linha": _linha(fp),
            "odd": numero(it.get("Value")),
            "inicio": inicio,
            "status_perna": _PERNA[it.get("Result")],
        })
    win = _d(t.get("WinKoef"))
    odd = numero(t.get("WinKoef")) if status in ("ganha", "cashout") and win else numero(t.get("Koef"))
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["ID"]),
        "colocada_em": _ms(t.get("ActionTime")),
        "liquidada_em": None,              # `LastEditTime` não é liquidação garantida
        "status": status,
        "status_casa": f"Status {t.get('Status')} · Result {t.get('Result')} · TicketType {tt}",
        "moeda": (t.get("CurrencySTR") or "").upper() or None,
        "stake": numero(t.get("Amount")),
        "stake_freebet": numero(t.get("Amount")) if tt == 3 else None,
        "odd": odd,
        "odd_calculada": False,
        "retorno": numero(t.get("WinAmount")) if status != "aberta" else None,
        "tipo": "multipla" if len(pernas) > 1 else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_tv",
    }
