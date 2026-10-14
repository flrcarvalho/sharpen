"""Semeia o dicionário de termos (`04_DICIONARIO §3`; s411) a partir dos pares que já existem.

Para cada aposta com cru (o mais recente dela em `captura_crua`), o adaptador monta a Ficha e o
termo da casa (`esporte_casa`, `mercado_casa`) é pareado com o esporte e a categoria que a IA
gravou para o MESMO código na MESMA conta (`bilhetes`). Onde o código não tem bilhete, completa
com a decisão mais recente da IA em `sombra_rotulos`. Entra no dicionário só o termo UNÂNIME
(`dicionario.votar`); o que a IA decidiu de mais de um jeito sai na lista para o Feca e fica de
fora, ou seja, vai para a IA.

Desde a s413 também o dicionário de DESCRIÇÃO (`app/descricao_ficha.py`: o mercado da casa →
o nome do mercado que a IA escreveu, perna a perna). Desde a s416 (D29) a descrição nunca fica
contradita: a regra decide (`descricao_ficha.decidir`) e só a mais votada vai para a revisão;
categoria e esporte seguem com a maioria de 90%. Depois de gravar, a semente regrava a descrição das apostas da Ficha do
mês corrente (`dicionario.regravar_mes`).

Idempotente: refaz a semente inteira a cada rodada. O servidor roda a mesma semente
sozinho uma vez por dia (`dicionario.diario`, 04h de Brasília); este script é para rodar na hora. Linha `origem = 'feca'` nunca é tocada.
Semente que deixou de ser unânime é apagada (a aposta volta para a IA).

    python scripts/semear_dicionario.py              # ensaio, nada escrito
    python scripts/semear_dicionario.py --aplicar    # grava em dicionario_termos
"""
from __future__ import annotations

import asyncio
import collections
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
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        p, texto, fontes = await dicionario.pares(conn)
        print("pares:", fontes)
        unanimes, contraditos, revisao = dicionario.votar(p, texto)
        por_casa = collections.Counter((c, t) for c, t, _ in unanimes)
        for (c, t), n in sorted(por_casa.items()):
            print(f"{c:11} {t:9} {n:4} termos unânimes")
        print(f"\n{len(contraditos)} termos em que a IA decidiu de mais de um jeito (ficam com a IA):")
        for (c, t, termo), cnt in sorted(contraditos.items()):
            if t == "descricao" or dicionario.SEP not in termo:
                print(f"  {c:11} {t:9} {termo!r}: " + ", ".join(f"{k} ×{v}" for k, v in cnt.most_common()))
        print(f"\n{len(revisao)} termos decididos pela maioria de 90% (o voto isolado, para revisão):")
        for x in revisao:
            print(f"  {x['casa']:11} {x['tipo']:9} {x['termo']!r}: fica {x['fica']!r}; votos {x['votos']}")
        if not aplicar:
            print("\nensaio: nada gravado (use --aplicar)")
            return
        r = await dicionario.semear(conn, "manual")       # grava e registra no semente_log
        print("novos nesta rodada:", r["novos"], "· apostas da Ficha do mês com a descrição "
              "regravada:", r["regravadas"])
        total = await conn.fetchval("SELECT count(*) FROM dicionario_termos")
        print(f"\ngravado: {r['termos']} termos de semente; {total} no dicionário")


if __name__ == "__main__":
    asyncio.run(main())
