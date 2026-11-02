"""A lixeira para os scripts (Fase 7, s438; Feca, 01/11/2026): toda exclusão de aposta em
`scripts/` passa por `repository._mover_para_lixeira`, a mesma função do app.

Uso, num script de `scripts/` (rodado como `python scripts/x.py`, este diretório já está no path):

    from _lixeira import mover_para_lixeira
    n = len(await mover_para_lixeira(conn, "dono = $1 AND origem = $2", [dono, origem],
                                     "reimport: import_x.py"))

`conn` é qualquer conexão asyncpg (do pool ou `asyncpg.connect`), inclusive dentro de uma
transação aberta pelo script: a exclusão e o snapshot entram nela. O `where` vale sobre
`bilhetes b` (coluna sem prefixo também funciona). Gate: `tests/test_lixeira_sempre.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

_APP = Path(__file__).resolve().parents[1] / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from repository import _mover_para_lixeira as mover_para_lixeira  # noqa: E402,F401
