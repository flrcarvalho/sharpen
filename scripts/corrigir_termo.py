"""Corrige um termo do dicionário (D24, s412): grava a correção do Feca (`origem = 'feca'`, que a
semente nunca sobrescreve) e regrava as apostas DA FICHA do MÊS CORRENTE que usaram o termo
(esporte, categoria e descrição). Mês passado não é tocado (D10, D23), nem campo editado à mão.

    python scripts/corrigir_termo.py CASA TIPO "TERMO" "PARA"            # ensaio, nada escrito
    python scripts/corrigir_termo.py CASA TIPO "TERMO" "PARA" --aplicar

CASA = casa_key (`DEXSPORT`) ou `*` (todas). TIPO = `esporte`, `categoria` ou `descricao`. TERMO
como a casa escreve (é normalizado: número vira `{n}` na categoria). PARA = valor do Master.
`descricao` (s413): TERMO = a chave `<esporte da casa> | <mercado>` (como o `semente_log` mostra) e
PARA = o valor com as marcas (`{ou} Escanteios {n1}º Tempo`; `app/descricao_ficha.py`).
Regra em `app/dicionario.py` (`corrigir_termo`).
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import dicionario  # noqa: E402
from database import get_pool  # noqa: E402


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 4:
        print(__doc__)
        sys.exit(2)
    casa, tipo, termo, para = args
    aplicar = "--aplicar" in sys.argv
    _carregar_env()
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            mudancas = await dicionario.corrigir_termo(conn, casa, tipo, termo, para,
                                                       aplicar=aplicar)
    chave = (" ".join(termo.casefold().split()) if tipo == "descricao"
             else dicionario.normalizar(termo, numeros=(tipo == "categoria")))
    print(f"{casa.upper()} {tipo} {chave!r} → {para!r}: "
          f"{len(mudancas)} aposta(s) da Ficha do mês corrente a regravar")
    for m in mudancas:
        print(f"  {m['dono']} {m['codigo']}: {m['antes']} → {m['depois']}")
    print("gravado" if aplicar else "ensaio: nada gravado (use --aplicar)")


if __name__ == "__main__":
    asyncio.run(main())
