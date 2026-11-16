"""Adaptador da GiroCerto (família `gc`, plataforma própria `girocerto.fun`; s455).

O cru é um item do ARRAY de `GET /api/esportes/bets`, o mesmo que o `gc_inject.js` busca, e
chega VERBATIM (o inject não o normaliza). A leitura de cada campo é a do `formatTicketGC` do
`content.js` e da `CASA_GIROCERTO.md`, validada contra o card no recon de 15/11/2026
(`extensor/harness/casos/girocerto.mjs`, fixture `girocerto.bets.json`: 50 simples
liquidadas, 27 ganhas com 1 meia vitória, 16 perdidas com 2 meias derrotas, 7 anuladas).
Escrito ANTES do 1º cru real chegar ao banco.

  • dinheiro em CENTAVOS inteiros (`stakeCents`, `creditedCents`). `creditedCents` é o dinheiro
    que voltou; `payoutCents` é o potencial, que o card da PERDIDA estampa, e nunca entra.
  • a odd da aposta é `originalOdds`. A `odds` é REESCRITA na liquidação (anulada e meia
    derrota viram 1; meia vitória vira a efetiva, 1.413 = 423,75 ÷ 300) e nunca entra.
  • status pelo DINHEIRO, com o enum cru concordando, e a meia pela PERNA:
      `lost` + crédito 0 = perdida · `void` + crédito = stake = anulada ·
      `won` + crédito = stake × odd (1 centavo: a casa arredonda o pagamento para BAIXO) = ganha ·
      `won` + perna `half_won` + crédito = stake ÷ 2 × odd + stake ÷ 2 = meio_ganha ·
      `lost` + perna `half_lost` + crédito = stake ÷ 2 = meio_perdida.
    Qualquer outra combinação RECUSA (o texto leva à IA, que lê o bloco "a conferir").
  • datas em ISO UTC com `Z` (`placedAt`, `settledAt`, `legs[].startsAt`).
  • código = `code` (10 caracteres, o do card e do print), nunca o `id` UUID.
  • moeda: a API não manda. Vale a da conta (decisão do Feca, D0 pergunta 5); a casa só
    opera em real.
  • Sem amostra, RECUSA: aberta (`accepted`/`pending`/`placing`/`cashing`/`voiding`),
    `rejected` (não é aposta), cashout (`cashed_out` ou `cashedCents` > 0), freebet,
    múltipla (`kind` ≠ `single` ou mais de uma perna) e status desconhecido.
"""
from __future__ import annotations

from decimal import Decimal

from . import Recusa, numero

_PERNA = {"open": "aberta", "won": "ganha", "lost": "perdida", "void": "anulada",
          "half_won": "meio_ganha", "half_lost": "meio_perdida"}
_ABERTA = frozenset({"accepted", "pending", "placing", "cashing", "voiding"})
_CENTAVO = Decimal(1)          # em CENTAVOS: a casa corta o pagamento no centavo (para baixo)


def bilhetes_da_resposta(resposta) -> list:
    return resposta if isinstance(resposta, list) else []


def codigo(cru) -> str:
    return str((cru or {}).get("code") or "") if isinstance(cru, dict) else ""


def _cents(v) -> Decimal | None:
    if v is None or isinstance(v, bool):
        return None
    try:
        return Decimal(str(v))
    except Exception:
        return None


def _reais(c: Decimal | None) -> str | None:
    return None if c is None else numero(str(c / 100))


def _status(t: dict, perna: str) -> str:
    st = t.get("status")
    cru = f"status {st!r}"
    if st in _ABERTA:
        raise Recusa(f"{cru}: aberta sem amostra (a conferir)")
    if st == "rejected":
        raise Recusa(f"{cru}: a casa recusou a aposta, não é bilhete")
    stake, cred = _cents(t.get("stakeCents")), _cents(t.get("creditedCents"))
    if st == "cashed_out" or (_cents(t.get("cashedCents")) or 0) > 0 or t.get("lastCashout"):
        raise Recusa(f"{cru}: cashout sem amostra (a conferir)")
    if t.get("freebet"):
        raise Recusa(f"{cru}: freebet sem amostra (a conferir)")
    odd = _cents(t.get("originalOdds"))
    if stake is None or stake <= 0 or cred is None:
        raise Recusa(f"{cru}: sem stakeCents ou sem creditedCents")
    if st == "lost" and cred == 0:
        return "perdida"
    if st == "void" and cred == stake:
        return "anulada"
    if odd is not None and odd > 1:
        if st == "won" and perna == "half_won" and abs(cred - (stake / 2 * odd + stake / 2)) <= _CENTAVO:
            return "meio_ganha"
        if st == "lost" and perna == "half_lost" and abs(cred - stake / 2) <= _CENTAVO:
            return "meio_perdida"
        if st == "won" and perna != "half_won" and abs(cred - stake * odd) <= _CENTAVO:
            return "ganha"
    raise Recusa(f"{cru}: crédito {cred} centavos sobre stake {stake} @ {odd} com perna {perna!r} "
                 "não fecha (a conferir)")


def adaptar(t: dict, casa_key: str) -> dict:
    if not isinstance(t, dict) or not t.get("code"):
        raise Recusa("bilhete sem code")
    if t.get("kind") != "single":
        raise Recusa(f"kind {t.get('kind')!r} sem amostra (só `single` medido)")
    legs = t.get("legs") or []
    if len(legs) != 1:
        raise Recusa(f"simples com {len(legs)} perna(s)")
    l0 = legs[0] if isinstance(legs[0], dict) else {}
    if l0.get("status") not in _PERNA:
        raise Recusa(f"perna com status {l0.get('status')!r} não mapeado")
    status = _status(t, l0.get("status"))
    pernas = [{
        "esporte_casa": l0.get("sport") or None,
        "evento": l0.get("event") or "",
        "mercado_casa": l0.get("market") or "",
        "selecao_casa": l0.get("pick") or "",
        "odd": numero(l0.get("odds")),
        "inicio": l0.get("startsAt") or None,
        "status_perna": _PERNA[l0["status"]],
    }]
    return {
        "versao": "ficha/1",
        "casa": casa_key,
        "codigo": str(t["code"]),
        "colocada_em": t.get("placedAt") or None,
        "liquidada_em": t.get("settledAt") or None,
        "status": status,
        "status_casa": f"status {t.get('status')} · kind {t.get('kind')}",
        "moeda": None,
        "stake": _reais(_cents(t.get("stakeCents"))),
        "stake_freebet": None,
        "odd": numero(t.get("originalOdds")),
        "odd_calculada": False,
        "retorno": _reais(_cents(t.get("creditedCents"))),
        "tipo": "simples",
        "sistema": None,
        "pernas": pernas,
        "origem": "servidor:adaptador_gc",
    }
