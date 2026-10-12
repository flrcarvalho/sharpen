"""Passa o filtro ATUAL do `app/cru.py` sobre o cru já guardado em `captura_crua` (s409).

Por quê: o filtro ganhou nome novo (`Player` da MyStake e `nickname` da DEX, Feca 12/10), e o
cru que chegou antes ficou com o dado de pessoa. Este script tira esses campos, acrescenta os
caminhos em `removidos` e recalcula o `hash` sobre o cru filtrado, o mesmo que a rota calcula
hoje. Sem o hash novo, o próximo envio da mesma aposta não cairia em "cru igual" e entraria
como linha nova.

Cópia antes de mudar (CLAUDE.md, "mova para tabela isolada"): cada linha alterada vai inteira
para `captura_crua_copia_filtro`, e as Fichas que apontam para ela, para
`ficha_sombra_copia_filtro`. Nada mais no sistema lê essas tabelas.

As Fichas dessas linhas SAEM de `ficha_sombra`: a `impressao` delas é o hash antigo. O
`reprocessar_ficha_cru.py` monta de novo, com o mesmo adaptador, sobre o cru limpo.

Se a aposta já chegou de novo depois do deploy do filtro, existe linha com o hash novo: a
antiga sai (com cópia) em vez de virar duplicata.

Tudo numa transação. Idempotente: na 2ª rodada o filtro não tira mais nada.

    python scripts/limpar_cru_filtro.py            # ensaio, nada escrito
    python scripts/limpar_cru_filtro.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import cru as _cru  # noqa: E402
from database import get_pool  # noqa: E402


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def plano(linhas) -> list[dict]:
    """Por linha que o filtro de hoje ainda corta: o cru limpo, os caminhos e o hash novo.
    PURA: recebe as linhas já lidas de `captura_crua`. Usa o MESMO filtro e hash da rota."""
    saida = []
    for r in linhas:
        cru = r["cru"] if isinstance(r["cru"], dict) else json.loads(r["cru"])
        filtrado, removidos = _cru.filtrar(cru)
        if not removidos:
            continue
        saida.append({"id": r["id"], "casa": r["casa"], "chave": (r["dono"], r["casa"], r["parceiro"], r["codigo"]),
                      "cru": _cru.canonico(filtrado), "hash": _cru.impressao(filtrado),
                      "removidos": list(r["removidos"] or []) + removidos})
    return saida


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch("SELECT id, dono, casa, parceiro, codigo, cru::text AS cru, removidos "
                                  "FROM captura_crua ORDER BY id")
        alvo = plano(linhas)
        ids = [a["id"] for a in alvo]
        hashes = {r["id"]: r for r in await conn.fetch(
            "SELECT id, dono, casa, parceiro, codigo, hash FROM captura_crua")}
        existentes = {(r["dono"], r["casa"], r["parceiro"], r["codigo"], r["hash"]): i for i, r in hashes.items()}
        fichas = await conn.fetchval("SELECT count(*) FROM ficha_sombra WHERE cru_id = ANY($1::bigint[])", ids)
        colide = [a for a in alvo if existentes.get(a["chave"] + (a["hash"],), a["id"]) != a["id"]]
        print(f"crus a limpar: {len(alvo)} · por casa: {dict(Counter(a['casa'] for a in alvo))}")
        print(f"caminhos cortados: {dict(Counter(c for a in alvo for c in a['removidos']))}")
        print(f"Fichas que saem (com cópia) e voltam pelo reprocesso: {fichas}")
        print(f"já chegaram de novo com o hash novo (a antiga sai, com cópia): {len(colide)}")
        if not aplicar:
            print("ensaio: nada escrito. Rode com --aplicar.")
            return
        async with conn.transaction():
            await conn.execute("CREATE TABLE IF NOT EXISTS captura_crua_copia_filtro "
                               "(LIKE captura_crua, copiado_em TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            await conn.execute("CREATE TABLE IF NOT EXISTS ficha_sombra_copia_filtro "
                               "(LIKE ficha_sombra, copiado_em TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cols_c = [r["column_name"] for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name='captura_crua' "
                "ORDER BY ordinal_position")]
            cols_f = [r["column_name"] for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns WHERE table_name='ficha_sombra' "
                "ORDER BY ordinal_position")]
            n_c = await conn.execute(
                f"INSERT INTO captura_crua_copia_filtro ({', '.join(cols_c)}) "
                f"SELECT {', '.join(cols_c)} FROM captura_crua WHERE id = ANY($1::bigint[])", ids)
            n_f = await conn.execute(
                f"INSERT INTO ficha_sombra_copia_filtro ({', '.join(cols_f)}) "
                f"SELECT {', '.join(cols_f)} FROM ficha_sombra WHERE cru_id = ANY($1::bigint[])", ids)
            await conn.execute("DELETE FROM ficha_sombra WHERE cru_id = ANY($1::bigint[])", ids)
            ids_colide = [a["id"] for a in colide]
            await conn.execute("DELETE FROM captura_crua WHERE id = ANY($1::bigint[])", ids_colide)
            for a in alvo:
                if a["id"] in ids_colide:
                    continue
                await conn.execute("UPDATE captura_crua SET cru = $2::jsonb, hash = $3, removidos = $4 "
                                   "WHERE id = $1", a["id"], a["cru"], a["hash"], a["removidos"])
        print(f"copiadas: {n_c} (cru) · {n_f} (Ficha). Limpos: {len(alvo) - len(colide)}; "
              f"removidos por já existir com o hash novo: {len(colide)}.")
        print("Agora: python scripts/reprocessar_ficha_cru.py --casa <CASA> --aplicar")


if __name__ == "__main__":
    asyncio.run(main())
