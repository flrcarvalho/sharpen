"""Adaptadores do cru da casa para a Ficha Sharpen, um por FAMÍLIA (Projeto Ficha Sharpen, s409).

A `impressao` NÃO é do adaptador: o servidor a calcula sobre o cru guardado.

A família é o prefixo do inject que escutou a casa (`dx` = `dx_inject.js`). Cada adaptador
expõe `adaptar(cru, casa_key) -> dict` (a Ficha, `01_FICHA_SHARPEN.md §2`) e levanta
`Recusa(motivo)` quando o cru não permite montar uma Ficha sem chutar. Também expõe
`bilhetes_da_resposta(resposta) -> list` (onde a lista mora na resposta da API), que o teste
usa para ler as fixtures da bancada do mesmo jeito que o inject lê a casa. Onde o código não
mora em `cru.id` (a 1win o guarda em `cru.bet.id`), expõe também `codigo(cru) -> str`, que a
recusa usa: sem ele a Ficha recusada seria gravada sem código.

Regra de todos: o adaptador COPIA. Valor, data e status vêm como a casa escreveu; o que a
planilha mostra é o `ficha.derivar` que decide. Número de ponto flutuante vira texto pelo
`numero()`, que corta o ruído binário em 15 dígitos (a mesma régua da odd no `tradutor`).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, localcontext

from tradutor import _PRECISAO_ODD


class Recusa(Exception):
    """O cru não monta uma Ficha sem chute. O motivo vai gravado na `ficha_sombra`."""


def numero(v) -> str | None:
    """Número da casa (int/float/texto) → texto com ponto, sem ruído de float.
    `123.50000000000001` vira `123.5`; `25` vira `25`. None/vazio = None."""
    if v is None or v == "" or isinstance(v, bool):
        return None
    try:
        with localcontext() as ctx:
            ctx.prec = _PRECISAO_ODD
            d = +Decimal(repr(v) if isinstance(v, float) else str(v))
    except Exception:
        return None
    d = d.normalize()
    if d == d.to_integral_value():
        d = d.quantize(Decimal(1))
    return format(d, "f")


def iso_de_epoch(s) -> str | None:
    """Epoch em SEGUNDOS → ISO em UTC (com fuso, como a Ficha exige)."""
    if s is None or isinstance(s, bool):
        return None
    try:
        return datetime.fromtimestamp(float(s), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


from . import dx, jb, shf, tp, tv, vb, x1  # noqa: E402  (depois dos helpers que eles usam)

ADAPTADORES = {"dx": dx, "jb": jb, "shf": shf, "tp": tp, "tv": tv, "vb": vb, "x1": x1}


def adaptador(familia: str):
    return ADAPTADORES.get((familia or "").strip().lower())
