"""Adaptador da Vave (família `vv`, plataforma própria `softlabs`; s427).

O cru é o objeto que o `vv_inject.js` monta (`_montarCru` + `_dicDe`): o bilhete da casa
(`bet`, sem o `userId`), as linhas das tabelas irmãs do mesmo lote que ele usa (`events`,
`competitors`, `leagues`, `sportCategories`, `sports`, `results`) e, desde a 0.7.63, o
`dicionario` com o TEMPLATE de mercado e de seleção de cada perna, verbatim. A leitura de cada
campo é a do `formatTicketVV` (`content.js`) e da `CASA_VAVE.md`; escrito da fixture
`extensor/harness/fixtures/vave.cru.json` (11 perdidas da conta do Feca, gerada pelo inject
real) e conferido nos 35 crus reais do banco (Feca e Gabriel, 23/10/2026).

  • CÓDIGO: `bet.id`, o `#` do card (7 dígitos na Vave, 8 na 20bet).
  • 20bet (s428) é ESPELHO: o mesmo app, a mesma API, 167 chaves e zero nova. Fixture
    `20bet.cru.json` (12 bilhetes, USD, 2 abertas, 3 bet builders, perna devolvida). O dicionário
    `/pt` dela vem em português (o da Vave vinha em inglês); o adaptador copia o que vier.
  • MOEDA da conta: `bet.currency` (USDT, USDC). Quem converte é o servidor.
  • ODD da casa: `bet.value`, a do card; na múltipla já é o produto das pernas.
  • `bet.status`: `0` aberta · `1` perdida só com `win` e `winFull` zerados · `2` ganha se
    `winFull` fecha com stake × odd ao meio centavo (medido em 23/10/2026 nos 6 ganhos reais:
    `win` = `winFull` = o RETORNO, 33 × 1,9 = 62,7). `winFull` = stake é anulada, qualquer
    rótulo (o dinheiro decide). O resto, RECUSA.
  • MERCADO e SELEÇÃO não vêm no histórico: saem do `dicionario` do cru, template Sportradar
    resolvido aqui como o inject resolve (`{$competitor1}`, `{!x}` ordinal, `{+x}` com sinal,
    `{-x}` com o sinal invertido, `{x}`). Placeholder sem valor, RECUSA: a perna sairia com
    `{total}` no nome. Cru sem `dicionario` (anterior à 0.7.63, ou o dicionário não carregou),
    RECUSA, e o texto leva o bilhete à IA.
  • ESPORTE: `sports[].name`, em inglês (`Football`), que o dicionário `*` traduz.
  • DATA da perna: `events[].ts`, unix UTC. `finishedAt` fica fora: o fuso não foi provado.
  • Sem amostra, RECUSA: `system` ≠ 0, `betBetBuilderId`, `bonusAmount`, `freebetAmount`,
    `betCashoutAmount` e status 3/8/outro com dinheiro que não é a stake.
"""
from __future__ import annotations

import re
from decimal import Decimal

from . import Recusa, iso_de_epoch, numero

# Perna: 1 e 2 medidos na Vave (s425); 0 "Pending" e 3 "Returned" medidos no card da 20bet (s428,
# espelho: o mesmo motor). Status de perna fora daqui sobe vazio, nunca chutado.
_PERNA = {0: "aberta", 1: "perdida", 2: "ganha", 3: "anulada"}
_MEIO_CENTAVO = Decimal("0.005")
_TEMPLATE = re.compile(r"\{([!+\-$%]?)([^}]+)\}")


def bilhetes_da_resposta(resposta) -> list:
    """A mensagem do inject: `[{codigo, cru}]` (a fixture `vave.cru.json`)."""
    if isinstance(resposta, list):
        return [x["cru"] for x in resposta if isinstance(x, dict) and isinstance(x.get("cru"), dict)]
    return []


def codigo(cru) -> str:
    b = cru.get("bet") if isinstance(cru, dict) else None
    if not isinstance(b, dict) or b.get("id") in (None, ""):
        return ""
    return str(b["id"])


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _por_id(lista) -> dict:
    return {str(x["id"]): x for x in (lista or []) if isinstance(x, dict) and x.get("id") is not None}


def _spec(txt) -> dict:
    o = {}
    for par in str(txt or "").split("|"):
        k, sep, v = par.partition("=")
        if sep and k.strip():
            o[k.strip()] = v.strip()
    return o


def _ordinal(v: str) -> str:
    try:
        n = int(v)
    except ValueError:
        return v
    r = n % 100
    return f"{n}{'th' if 11 <= r <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _sinal(v: str, inverte: bool) -> str:
    t = v.strip()
    try:
        x = float(t)
    except ValueError:
        return t
    if x == 0:
        return "0"
    neg = t.startswith("-")
    return ("-" if neg != inverte else "+") + t.lstrip("+-")


def _resolver(tpl: str, spec: dict, c1: str, c2: str) -> str:
    """O template da casa → o nome que o card mostra. Placeholder sem valor, RECUSA."""
    def troca(m):
        op, k = m.group(1), m.group(2)
        if op == "$":
            v = {"competitor1": c1, "competitor2": c2,
                 "event": f"{c1} - {c2}" if c1 and c2 else ""}.get(k, "")
        else:
            v = spec.get(k, "")
            if v and op == "!":
                v = _ordinal(v)
            elif v and op in ("+", "-"):
                v = _sinal(v, op == "-")
        if not v:
            raise Recusa(f"template {tpl!r} sem valor para {m.group(0)}")
        return v
    return _limpo(_TEMPLATE.sub(troca, tpl))


def _status(b: dict) -> str:
    st = b.get("status")
    if st == 0:
        return "aberta"
    stake, odd = _d(b.get("amount")), _d(b.get("value"))
    win, cheio = _d(b.get("win")), _d(b.get("winFull"))
    if stake is None or stake <= 0:
        raise Recusa(f"status {st!r} sem amount")
    if st == 1:
        if win == 0 and cheio == 0:
            return "perdida"
        raise Recusa(f"perdida com win {b.get('win')!r} / winFull {b.get('winFull')!r} (a conferir)")
    if cheio is not None and abs(cheio - stake) <= _MEIO_CENTAVO:
        return "anulada"              # o dinheiro decide: P/L zero, qualquer que seja o rótulo
    if st == 2 and odd and cheio is not None and abs(cheio - stake * odd) <= _MEIO_CENTAVO:
        return "ganha"
    raise Recusa(f"status {st!r} com winFull {b.get('winFull')!r} sobre amount {b.get('amount')!r} "
                 f"e odd {b.get('value')!r} (sem amostra; a conferir)")


def _perna(d: dict, ix: dict, dic: dict) -> dict:
    ev = ix["eventos"].get(str(d.get("event_id")))
    if not ev:
        raise Recusa(f"perna sem o evento {d.get('event_id')!r} no cru")
    c1 = _limpo((ix["times"].get(str(ev.get("competitor1Id"))) or {}).get("name")) or _limpo(ev.get("team1"))
    c2 = _limpo((ix["times"].get(str(ev.get("competitor2Id"))) or {}).get("name")) or _limpo(ev.get("team2"))
    liga = ix["ligas"].get(str(d.get("league_id") or ev.get("league_id"))) or {}
    pais = ix["paises"].get(str(liga.get("sportCategoryId"))) or {}
    esp = ix["esportes"].get(str(ev.get("sport_id") or liga.get("sport_id"))) or {}
    m_tpl = (dic.get("mercados") or {}).get(str(d.get("marketId")))
    s_tpl = (dic.get("selecoes") or {}).get(str(d.get("outcomeId")))
    if m_tpl is None or s_tpl is None:
        raise Recusa(f"dicionário sem o mercado {d.get('marketId')!r} ou a seleção {d.get('outcomeId')!r}")
    spec = _spec(d.get("specifiers"))
    liga_txt = " · ".join(x for x in (_limpo(pais.get("name")), _limpo(liga.get("name"))) if x)
    return {
        "esporte_casa": _limpo(esp.get("name")) or None,
        "liga_casa": liga_txt or None,
        "evento": f"{c1} - {c2}" if c1 and c2 else _limpo(ev.get("name")),
        "mandante": c1 or None,
        "visitante": c2 or None,
        "mercado_casa": _resolver(m_tpl, spec, c1, c2),
        "selecao_casa": _resolver(s_tpl, spec, c1, c2),
        "linha": numero(spec["total"]) if spec.get("total") else None,
        "odd": numero(d.get("value") if d.get("value") is not None else d.get("odds")),
        "inicio": iso_de_epoch(ev.get("ts")),
        "status_perna": _PERNA.get(d.get("status")),
    }


def adaptar(cru: dict, casa_key: str) -> dict:
    cod = codigo(cru)
    if not cod:
        raise Recusa("bilhete sem id")
    b = cru["bet"]
    if not isinstance(cru.get("dicionario"), dict):
        raise Recusa("cru sem dicionario (SharpenUp anterior à 0.7.63, ou o dicionário não carregou)")
    if b.get("system") not in (None, 0):
        raise Recusa(f"system {b.get('system')!r} sem amostra")
    for campo in ("betBetBuilderId", "betCashoutAmount"):
        if b.get(campo) is not None:
            raise Recusa(f"{campo} {b.get(campo)!r} sem amostra (o texto leva à IA)")
    for campo in ("bonusAmount", "freebetAmount"):
        if b.get(campo) not in (None, 0):
            raise Recusa(f"{campo} {b.get(campo)!r} sem amostra (o texto leva à IA)")
    status = _status(b)
    det = b.get("details") or []
    if not det:
        raise Recusa("bilhete sem details")
    ix = {"eventos": _por_id(cru.get("events")), "times": _por_id(cru.get("competitors")),
          "ligas": _por_id(cru.get("leagues")), "paises": _por_id(cru.get("sportCategories")),
          "esportes": _por_id(cru.get("sports"))}
    pernas = [_perna(d, ix, cru["dicionario"]) for d in det]
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": cod,
        "colocada_em": iso_de_epoch(b.get("ts")),
        "liquidada_em": None,
        "status": status,
        "status_casa": f"status {b.get('status')} · typeName {b.get('typeName')} · system {b.get('system')}",
        "moeda": _limpo(b.get("currency")).upper() or None,
        "stake": numero(b.get("amount")),
        "stake_freebet": None,
        "odd": numero(b.get("value")),
        "odd_calculada": False,
        "retorno": (None if status == "aberta" else "0" if status == "perdida"
                    else numero(b.get("winFull"))),
        "tipo": "multipla" if len(pernas) > 1 else "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_vv",
    }
