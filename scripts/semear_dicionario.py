"""Semeia o dicionário de termos (`04_DICIONARIO §3`; s411) a partir dos pares que já existem.

Para cada aposta com cru (o mais recente dela em `captura_crua`), o adaptador monta a Ficha e o
termo da casa (`esporte_casa`, `mercado_casa`) é pareado com o esporte e a categoria que a IA
gravou para o MESMO código na MESMA conta (`bilhetes`). Onde o código não tem bilhete, completa
com a decisão mais recente da IA em `sombra_rotulos`. Entra no dicionário só o termo UNÂNIME
(`dicionario.votar`); o que a IA decidiu de mais de um jeito sai na lista para o Feca e fica de
fora, ou seja, vai para a IA.

Idempotente: refaz a semente inteira a cada rodada. Linha `origem = 'feca'` nunca é tocada.
Semente que deixou de ser unânime é apagada (a aposta volta para a IA).

    python scripts/semear_dicionario.py              # ensaio, nada escrito
    python scripts/semear_dicionario.py --aplicar    # grava em dicionario_termos
"""
from __future__ import annotations

import asyncio
import collections
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import dicionario  # noqa: E402
import ficha  # noqa: E402
from database import get_pool  # noqa: E402


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


async def pares(conn) -> tuple[list, list]:
    """([(casa_key, Ficha, esporte da IA, categoria da IA)], um por aposta com cru;
    [(casa_key, termos de esporte do texto, esporte da IA)], um por bilhete da sombra)."""
    ultimo = {}
    for r in await conn.fetch("SELECT dono, casa, parceiro, familia, codigo, cru::text AS cru "
                              "FROM captura_crua ORDER BY id"):
        ultimo[(r["dono"], r["casa"], r["parceiro"], r["codigo"])] = r
    codigos = [k[3] for k in ultimo]
    nomes = {r["k"]: r["casa"] for r in await conn.fetch(
        "SELECT DISTINCT upper(replace(casa, ' ', '')) AS k, casa FROM bilhetes")}
    bil = {(b["dono"], b["casa"], b["parceiro"], b["codigo_bilhete"]): b for b in await conn.fetch(
        "SELECT dono, casa, parceiro, codigo_bilhete, esporte, aposta FROM bilhetes "
        "WHERE codigo_bilhete = ANY($1::text[])", codigos)}
    sombra = {(s["dono"], s["codigo"]): s for s in await conn.fetch(
        "SELECT DISTINCT ON (dono, codigo) dono, codigo, ia_esporte, ia_aposta "
        "FROM sombra_rotulos WHERE codigo = ANY($1::text[]) ORDER BY dono, codigo, criado_em DESC",
        codigos)}
    out, fontes = [], collections.Counter()
    for (dono, casa, parceiro, codigo), r in ultimo.items():
        f, motivos = ficha.montar_ficha(r["familia"], json.loads(r["cru"]), casa)
        if f is None or motivos:
            continue
        b = bil.get((dono, nomes.get(casa, casa), parceiro, codigo))
        if b:
            out.append((casa, f, b["esporte"], b["aposta"]))
            fontes["bilhetes"] += 1
        elif (s := sombra.get((dono, codigo))):
            out.append((casa, f, s["ia_esporte"], s["ia_aposta"]))
            fontes["sombra_rotulos"] += 1
        else:
            fontes["sem par"] += 1
    # Complemento de ESPORTE: o texto do SharpenUp em `sombra_rotulos` escreve o termo da casa
    # por perna (`Esporte: tennis`), desde antes do cru existir. Só onde dá para dizer de qual
    # perna é o termo (`dicionario.esportes_do_texto`).
    texto = []
    for s in await conn.fetch(
            "SELECT DISTINCT ON (dono, casa, codigo) casa, bruto, ia_esporte FROM sombra_rotulos "
            "WHERE codigo IS NOT NULL ORDER BY dono, casa, codigo, criado_em DESC"):
        termos = dicionario.esportes_do_texto(s["bruto"])
        if termos:
            texto.append(((s["casa"] or "").replace(" ", "").upper(), termos, s["ia_esporte"]))
    fontes["texto (esporte)"] = len(texto)
    print("pares:", dict(fontes))
    return out, texto


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        unanimes, contraditos = dicionario.votar(*await pares(conn))
        por_casa = collections.Counter((c, t) for c, t, _ in unanimes)
        for (c, t), n in sorted(por_casa.items()):
            print(f"{c:11} {t:9} {n:4} termos unânimes")
        print(f"\n{len(contraditos)} termos em que a IA decidiu de mais de um jeito (ficam com a IA):")
        for (c, t, termo), cnt in sorted(contraditos.items()):
            if dicionario.SEP not in termo:
                print(f"  {c:11} {t:9} {termo!r}: " + ", ".join(f"{k} ×{v}" for k, v in cnt.most_common()))
        if not aplicar:
            print("\nensaio: nada gravado (use --aplicar)")
            return
        async with conn.transaction():
            await conn.execute("DELETE FROM dicionario_termos WHERE origem = 'semente'")
            for (c, t, termo), (sharpen, n) in unanimes.items():
                await conn.execute(
                    """INSERT INTO dicionario_termos (casa, tipo, termo_casa, termo_sharpen,
                                                      origem, ocorrencias)
                       VALUES ($1, $2, $3, $4, 'semente', $5)
                       ON CONFLICT (casa, tipo, termo_casa) DO NOTHING""", c, t, termo, sharpen, n)
        total = await conn.fetchval("SELECT count(*) FROM dicionario_termos")
        print(f"\ngravado: {len(unanimes)} termos de semente; {total} no dicionário")


if __name__ == "__main__":
    asyncio.run(main())
