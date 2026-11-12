"""Adaptador da CopaWin (família `cw`, plataforma própria `wncopa.com`; s451).

O cru é um item de `bets[]` do `GET /api/bet/my-bets`, o mesmo que o `cw_inject.js` busca, e
chega VERBATIM (o inject não o normaliza). A leitura de cada campo é a do `formatTicketCW` do
`content.js` e da `CASA_COPAWIN.md`, validada contra o card no recon de 12/11/2026
(`extensor/harness/casos/copawin.mjs`, fixture `copawin.my-bets.json`: 15 simples
liquidadas, 5 ganhas, 8 perdidas, 2 anuladas). Escrito ANTES do 1º cru real chegar ao banco.

  • dinheiro e odd em TEXTO com ponto (`"750.00"`, `"1.73"`). `actual_return` é o dinheiro que
    voltou; `potential_return` é o que o card estampa até na PERDIDA e nunca entra.
  • status pelo DINHEIRO, com o enum cru concordando: `lost` + retorno 0 = perdida; `void` +
    retorno = stake = anulada; `won` + retorno = stake × `total_odds` no centavo = ganha.
    Qualquer outra combinação RECUSA (o texto leva à IA, que lê o bloco "a conferir").
  • `created_at`/`updated_at` em horário de BRASÍLIA (o card mostra igual);
    `event_starts_at` em UTC (prova: a liquidação vem ~1h ANTES do evento em 6 bilhetes).
  • moeda: a API não manda. Vale a da conta (decisão do Feca, D0 pergunta 5); a casa só
    opera em real.
  • Sem amostra, RECUSA: aberta (`pending`/`active`), múltipla (`type` ≠ `single`), cashout
    (status `cashout` ou `cashout_used`), boost (`boost_pct`) e a ODD TURBINADA
    (`market_key: "combined"`: 4 seleções num item só, sem odd por seleção — a Ficha exige
    odd em cada perna e inventá-la seria chute).
"""
from __future__ import annotations

from decimal import Decimal

from . import Recusa, numero

_PERNA = {"won": "ganha", "lost": "perdida", "void": "anulada",
          "pending": "aberta", "active": "aberta"}
_CENTAVO = Decimal("0.01")


def bilhetes_da_resposta(resposta) -> list:
    if isinstance(resposta, dict) and isinstance(resposta.get("bets"), list):
        return resposta["bets"]
    return []


def _d(v) -> Decimal | None:
    n = numero(v)
    return Decimal(n) if n is not None else None


def _iso(s, fuso: str) -> str | None:
    """"AAAA-MM-DD HH:MM:SS" sem fuso → ISO com o fuso DECLARADO pelo chamador."""
    s = str(s or "").strip()
    if len(s) < 19 or s[4] != "-" or s[10] not in " T":
        return None
    return s[:10] + "T" + s[11:19] + fuso


def _status(t: dict) -> str:
    st = t.get("status")
    stake, ret, odd = _d(t.get("stake")), _d(t.get("actual_return")), _d(t.get("total_odds"))
    cru = f"status {st!r}"
    if st in ("pending", "active"):
        raise Recusa(f"{cru}: aberta sem amostra (a conferir)")
    if st == "cashout" or str(t.get("cashout_used") or "0") not in ("0", "False", "false"):
        raise Recusa(f"{cru}: cashout sem amostra (cashout_used {t.get('cashout_used')!r})")
    if stake is None or stake <= 0 or ret is None:
        raise Recusa(f"{cru}: sem stake ou sem actual_return")
    if st == "lost" and ret == 0:
        return "perdida"
    if st == "void" and abs(ret - stake) < _CENTAVO:
        return "anulada"
    if st == "won" and odd is not None and abs(ret - stake * odd) <= _CENTAVO:
        return "ganha"
    raise Recusa(f"{cru}: retorno {ret} sobre stake {stake} @ {odd} não fecha "
                 "(HW/HL, boost ou status não mapeado, a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or t.get("id") in (None, ""):
        raise Recusa("bilhete sem id")
    if t.get("type") != "single":
        raise Recusa(f"type {t.get('type')!r} sem amostra (só `single` medido)")
    itens = t.get("items") or []
    if len(itens) != 1:
        raise Recusa(f"simples com {len(itens)} item(ns)")
    status = _status(t)
    pernas = []
    for it in itens:
        if it.get("market_key") == "combined" or it.get("leg_statuses"):
            raise Recusa("Odd Turbinada (combo da casa sem odd por seleção)")
        if it.get("boost_pct") not in (None, "", 0, "0"):
            raise Recusa(f"boost_pct {it.get('boost_pct')!r} sem amostra")
        if it.get("result") not in _PERNA:
            raise Recusa(f"perna com result {it.get('result')!r} não mapeado")
        pernas.append({
            "esporte_casa": it.get("sport") or None,
            "evento": it.get("match_name") or "",
            "mercado_casa": it.get("market_name") or "",
            "selecao_casa": it.get("selection_name") or "",
            "odd": numero(it.get("odds")),
            "inicio": _iso(it.get("event_starts_at"), "Z"),
            "status_perna": _PERNA[it["result"]],
        })
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["id"]),
        "colocada_em": _iso(t.get("created_at"), "-03:00"),
        "liquidada_em": _iso(t.get("updated_at"), "-03:00"),
        "status": status,
        "status_casa": f"status {t.get('status')} · type {t.get('type')}",
        "moeda": None,
        "stake": numero(t.get("stake")),
        "stake_freebet": None,
        "odd": numero(t.get("total_odds")),
        "odd_calculada": False,
        "retorno": numero(t.get("actual_return")),
        "tipo": "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_cw",
    }
