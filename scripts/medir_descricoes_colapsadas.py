"""
medir_descricoes_colapsadas.py — DIAGNÓSTICO READ-ONLY (só SELECT, nunca escreve).

Mede a pendência (II) da recuperação pós-SharpenUp: quantas linhas de marcador/props
estão com a descrição "colapsada" — isto é, SEM o confronto `[A v B]` e/ou SEM o sufixo
que distingue o mercado (Primeiro / Último Marcador / 2+ / Hat-trick). Descrição colapsada
contamina a dedup (Primeiro vs Último Marcador viram texto igual) — ver MASTER_DESCRICAO §12.1.

Uso (precisa da env DATABASE_URL, a mesma que o app usa):
    DATABASE_URL="postgresql://..." python scripts/medir_descricoes_colapsadas.py
    # opcional: filtrar por dono e/ou casa
    python scripts/medir_descricoes_colapsadas.py --dono Feca --casa Bet365
    # mostrar N linhas de amostra por grupo (default 15)
    python scripts/medir_descricoes_colapsadas.py --amostra 30

NÃO deleta nem altera nada. Serve só para MEDIR e você conferir a olho antes de qualquer
limpeza. A limpeza real de duplicatas é por RE-EXTRAÇÃO (código já corrigido), nunca delete
às cegas — régua: sem ID, só é duplicata se stake+odd+descrição baterem os três.
"""
import argparse
import asyncio
import os
import re

import asyncpg

# Confronto oficial (MASTER_DESCRICAO §4/§5): [Entidade A v Entidade B]  (separador " v ")
RE_CONFRONTO = re.compile(r"\[.+ v .+\]")
# Sufixos que distinguem o mercado de marcador (MASTER_DESCRICAO §12.1)
RE_SUFIXO = re.compile(
    r" - (Primeiro Marcador|Último Marcador|Ultimo Marcador|Hat-trick|\d+\+ Gols)"
)
# Famílias afetadas: Anytime (jogador para marcar) e qualquer coisa com "Marcador".
FILTRO_MARCADOR = "(aposta ILIKE '%Anytime%' OR aposta ILIKE '%Marcador%' OR descricao ILIKE '%Marcador%')"


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dono", default=None, help="filtrar por dono (ex.: Feca)")
    ap.add_argument("--casa", default=None, help="filtrar por casa (ex.: Bet365)")
    ap.add_argument("--amostra", type=int, default=15, help="linhas de amostra por grupo")
    args = ap.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("ERRO: defina a env DATABASE_URL (a mesma do app).")
    url = url.replace("postgres://", "postgresql://", 1)

    where = [FILTRO_MARCADOR]
    params: list = []
    if args.dono:
        params.append(args.dono)
        where.append(f"dono = ${len(params)}")
    if args.casa:
        params.append(args.casa)
        where.append(f"casa = ${len(params)}")
    where_sql = " AND ".join(where)

    conn = await asyncpg.connect(url)
    try:
        rows = await conn.fetch(
            f"SELECT id, dono, casa, parceiro, aposta, descricao, stake, odd, resultado, "
            f"codigo_bilhete FROM bilhetes WHERE {where_sql} ORDER BY casa, descricao",
            *params,
        )
    finally:
        await conn.close()

    total = len(rows)
    sem_confronto, sem_sufixo, colapsadas = [], [], []
    for r in rows:
        d = r["descricao"] or ""
        tem_conf = bool(RE_CONFRONTO.search(d))
        tem_suf = bool(RE_SUFIXO.search(d))
        if not tem_conf:
            sem_confronto.append(r)
        if not tem_suf:
            sem_sufixo.append(r)
        if not tem_conf or not tem_suf:
            colapsadas.append(r)

    def pct(n: int) -> str:
        return f"{(100 * n / total):.1f}%" if total else "—"

    print("=" * 72)
    print("DIAGNÓSTICO — descrições de marcador/props colapsadas (READ-ONLY)")
    filtro = " · ".join(x for x in [args.dono and f"dono={args.dono}", args.casa and f"casa={args.casa}"] if x)
    print(f"Filtro: {filtro or 'toda a base'}")
    print("=" * 72)
    print(f"Linhas de marcador/props analisadas : {total}")
    print(f"  sem confronto [A v B]             : {len(sem_confronto):>5}  ({pct(len(sem_confronto))})")
    print(f"  sem sufixo (Primeiro/Último/2+/…) : {len(sem_sufixo):>5}  ({pct(len(sem_sufixo))})")
    print(f"  COLAPSADAS (falta um ou outro)    : {len(colapsadas):>5}  ({pct(len(colapsadas))})")
    print("=" * 72)

    # Nota: "sem sufixo" inclui os 1+ legítimos (marcar a qualquer momento não tem sufixo).
    # O sinal forte de colapso é SEM CONFRONTO — mostramos amostra dessas para conferência.
    amostra = sem_confronto[: args.amostra]
    if amostra:
        print(f"\nAmostra de {len(amostra)} linha(s) SEM CONFRONTO (candidatas a re-extração):")
        print("-" * 72)
        for r in amostra:
            cod = r["codigo_bilhete"] or "—"
            print(f"  #{r['id']:<7} {r['casa']:<9} [{r['aposta']}] cod={cod}")
            print(f"          descr: {r['descricao']!r}")
    else:
        print("\nNenhuma linha sem confronto — nada a re-extrair por esse critério. ✓")

    print("\n> Lembrete: NÃO delete às cegas. Limpeza = re-extrair os lotes afetados")
    print(">           (código já corrigido) e deixar a dedup (stake+odd+descrição) agir.")


if __name__ == "__main__":
    asyncio.run(main())
