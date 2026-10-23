"""Adaptador da Thunderpick (família `thp`, plataforma própria; s426).

O cru é um item de `data.wagers` de `GET /api/wagers/v2/resolved` ou `/pending`, o mesmo que o
`thp_inject.js` escuta (`parseWager`). A leitura de cada campo é a do `formatTicketTHP` do
`content.js` e da `CASA_THUNDERPICK.md`; escrito das fixtures da bancada
(`extensor/harness/fixtures/thunderpick.*.json`, 29 liquidadas e 13 abertas, conta do Feca).

  • CÓDIGO com prefixo de tipo: `wagerId` tem duas séries (múltipla ~2,2M, simples 4,9M–10,3M),
    e o código é `C<wagerId>` na múltipla e `S<wagerId>` na simples (PreMatch e InPlays) — o
    mesmo que o inject põe no `[Código: …]` do texto, senão Ficha e IA gravariam dois bilhetes.
  • DINHEIRO em CENTAVOS DE EURO: `amount` 4383 = 43,83; `outcome` 7100 = 71,00. A conta é
    sempre em euro (a API não manda moeda; a tela em outra moeda é só exibição pelo câmbio do
    dia), então a moeda é `EUR`.
  • `wagerUIState`: `open` aberta · `lost` perdida (só com `outcome` 0) · `won` ganha, se o
    retorno fecha com stake × `odds` em 1 centavo (a casa arredonda sem regra fixa: 18720,66 →
    18720, 3952,8 → 3953). Retorno = stake é anulada, qualquer rótulo. O resto, RECUSA.
  • odd da casa: `odds`, a do card; na múltipla já é o produto das pernas. Quem decide a odd da
    planilha é o `ficha.derivar` (fecha no meio centavo ou retorno ÷ stake).
  • perna: `subWagers[]` na múltipla, com `subWagerUIState` próprio; na simples, o próprio
    bilhete.
  • esporte: a casa só manda `gameId`. O nome sai do mapa medido pela liga de cada bilhete
    (`CASA_THUNDERPICK §1.2`), escrito em inglês para o dicionário `*` traduzir; id fora do mapa
    vai VAZIO (ausência, não palpite), e o dicionário manda a aposta à IA.
  • MERCADO DE JOGADOR: a casa escreve `Player <Sobrenome> <Nome> - <mercado>` (`Player Doncic
    Luka - total points (incl. overtime)`). A Ficha leva `<Nome> <Sobrenome> <mercado>`: o
    último pedaço é sempre o primeiro nome (medido em 23/10/2026 contra a descrição da IA nos
    crus reais: `Doncic Luka` = `Luka Doncic`, `Lawson A.J.` = `A.J. Lawson`), e sem o ` - ` o
    `descricao_ficha._jogador` acha o nome e a chave vira `{jogador}`. Como a casa escreve, a
    chave seria uma POR JOGADOR, e todo jogador novo iria à IA. Só a forma do texto muda; número
    nenhum passa por aqui.
  • Sem amostra, RECUSA: `cancelReason`, `cashOutOdds` e `freeBet` preenchidos. O texto continua
    levando esses bilhetes à IA.
  • Datas em ISO UTC com 6 ou 7 casas de fração: cortadas em 6 (o `fromisoformat` não lê 7).
"""
from __future__ import annotations

import re
from decimal import Decimal

from . import Recusa, numero

# 43 = badminton, medido em 23/10/2026 (BWF World Tour; a IA leu Badminton). 23 ("Challenger
# League") e 31 ("Liga Pro") só apareceram dentro de múltipla, sem prova do esporte: ficam fora.
_ESPORTE = {6: "Counter-Strike", 10: "Soccer", 11: "Basketball", 14: "Ice Hockey", 15: "Tennis",
            43: "Badminton"}
_PERNA = {"won": "ganha", "lost": "perdida", "open": "aberta"}
_MEIO_CENTAVO = Decimal("0.005")
_UM_CENTAVO = Decimal("0.01")
_FRACAO = re.compile(r"(\.\d{6})\d+")
_JOGADOR = re.compile(r"^Player\s+(.+?)\s+(\S+)\s+-\s+(.+)$")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict):
        d = resposta.get("data")
        if isinstance(d, dict) and isinstance(d.get("wagers"), list):
            return d["wagers"]
    return resposta if isinstance(resposta, list) else []


def codigo(cru) -> str:
    """`C<wagerId>` / `S<wagerId>`, o código do texto (a recusa também precisa dele)."""
    if not isinstance(cru, dict) or cru.get("wagerId") in (None, ""):
        return ""
    return ("C" if cru.get("wagerType") == "Combo" else "S") + str(cru["wagerId"])


def _cent(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) / 100 if n is not None else None


def _iso(v) -> str | None:
    s = str(v or "").strip()
    return _FRACAO.sub(r"\1", s) if s else None


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _mercado(v) -> str:
    """`Player Doncic Luka - total points` → `Luka Doncic total points` (ver o cabeçalho)."""
    m = _limpo(v)
    j = _JOGADOR.match(m)
    return f"{j.group(2)} {j.group(1)} {j.group(3)}" if j else m


def _status(w: dict) -> str:
    st = w.get("wagerUIState")
    if st == "open":
        return "aberta"
    stake, ret, odd = _cent(w.get("amount")), _cent(w.get("outcome")), numero(w.get("odds"))
    if stake is None or stake <= 0 or ret is None:
        raise Recusa(f"wagerUIState {st!r} sem amount ou sem outcome")
    if abs(ret - stake) <= _MEIO_CENTAVO:
        return "anulada"              # o dinheiro decide: P/L zero, qualquer que seja o rótulo
    if st == "lost":
        if ret == 0:
            return "perdida"
        raise Recusa(f"perdida com outcome {w.get('outcome')!r} (a conferir)")
    if st == "won" and odd and abs(ret - stake * Decimal(odd)) <= _UM_CENTAVO:
        return "ganha"
    raise Recusa(f"wagerUIState {st!r} com outcome {w.get('outcome')!r} sobre amount "
                 f"{w.get('amount')!r} e odds {w.get('odds')!r} (sem amostra; a conferir)")


def _perna(p: dict, estado) -> dict:
    casa = _limpo((p.get("homeCompetitor") or {}).get("name"))
    fora = _limpo((p.get("awayCompetitor") or {}).get("name"))
    sel, linha = _limpo(p.get("selectionName")), _limpo(p.get("selectionTotal"))
    gid = p.get("gameId")
    return {
        "esporte_casa": _ESPORTE.get(gid) if isinstance(gid, int) else None,
        "liga_casa": _limpo((p.get("competition") or {}).get("name")) or None,
        "evento": f"{casa} - {fora}" if casa and fora else _limpo(p.get("eventName")),
        "mandante": casa or None,
        "visitante": fora or None,
        "mercado_casa": _mercado(p.get("marketName")),
        "selecao_casa": f"{sel} {linha}".strip(),
        "linha": numero(linha) if linha else None,
        "odd": numero(p.get("odds")),
        "inicio": _iso(p.get("eventStartTime")),
        "status_perna": _PERNA.get(estado),
    }


def adaptar(w: dict, casa_key: str) -> dict:
    cod = codigo(w)
    if not cod:
        raise Recusa("bilhete sem wagerId")
    for campo in ("cancelReason", "cashOutOdds", "freeBet"):
        if w.get(campo) not in (None, "", 0):
            raise Recusa(f"{campo} {w.get(campo)!r} sem amostra (o texto leva à IA)")
    status = _status(w)
    if w.get("wagerType") == "Combo":
        subs = w.get("subWagers") or []
        if not subs:
            raise Recusa("múltipla sem subWagers")
        for s in subs:
            if s.get("cancelReason") not in (None, ""):
                raise Recusa(f"perna com cancelReason {s.get('cancelReason')!r} sem amostra")
        pernas = [_perna(s, s.get("subWagerUIState")) for s in subs]
    else:
        pernas = [_perna(w, w.get("wagerUIState"))]
    ret = _cent(w.get("outcome"))
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": _iso(w.get("createTime")),
        "liquidada_em": _iso(w.get("finishTime")) if status != "aberta" else None,
        "status": status,
        "status_casa": f"wagerUIState {w.get('wagerUIState')} · state {w.get('state')} · "
                       f"wagerType {w.get('wagerType')}",
        "moeda": "EUR",
        "stake": numero(_cent(w.get("amount"))),
        "stake_freebet": None,
        "odd": numero(w.get("odds")),
        "odd_calculada": False,
        "retorno": (None if status == "aberta" else "0" if status == "perdida" else numero(ret)),
        "tipo": "multipla" if len(pernas) > 1 else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_thp",
    }
