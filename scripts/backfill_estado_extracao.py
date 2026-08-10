"""Backfill do `extraction_state` — s259.

`estado_extracao` passou a exigir odd apenas onde o P/L depende dela (W/HW). As linhas
JÁ gravadas seguem com o estado antigo até alguém tocá-las: uma perda sem odd continuaria
contando como "aguardando resultado" no badge âmbar para sempre. Este script recalcula o
estado de quem diverge, usando a MESMA função do app (nunca uma cópia do critério).

Escopo deliberadamente amplo (todas as linhas, todos os donos): a divergência é medida,
não presumida — o dry-run lista uma a uma antes de qualquer escrita.

Não toca em nenhuma coluna da assinatura (`_SIG_COLS`), então não há risco de duplicar
histórico na próxima captura; e não mexe em `atualizado_em`, porque o conteúdo do bilhete
não mudou — só a derivação do estado.

    python scripts/backfill_estado_extracao.py            # dry-run (não escreve nada)
    python scripts/backfill_estado_extracao.py --apply    # aplica
"""
import asyncio
import os
import pathlib
import sys

APP = pathlib.Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP))

# O console do Windows é cp1252 e engasga com '→'/'—' — sem isto o script morre no meio
# do relatório (e num script de escrita, morrer no meio do relatório é pior que feio).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

if not os.environ.get("DATABASE_URL"):
    env = APP.parent / ".env"
    if env.exists():
        for ln in env.read_text(encoding="utf-8").splitlines():
            if ln.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = ln.split("=", 1)[1].strip().strip('"')

import database  # noqa: E402
import repository as R  # noqa: E402


async def main(aplicar: bool) -> None:
    pool = await database.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, dono, casa, parceiro, data, resultado, odd, archived, extraction_state "
            "FROM bilhetes ORDER BY id"
        )

    divergentes = []
    for r in rows:
        novo = R.estado_extracao(r["resultado"], r["odd"])
        if novo != r["extraction_state"]:
            divergentes.append((r, novo))

    print(f"{len(rows)} bilhete(s) lidos · {len(divergentes)} com estado divergente\n")
    if not divergentes:
        print("nada a fazer.")
        await pool.close()
        return

    por_dono: dict[str, int] = {}
    for r, novo in divergentes:
        por_dono[r["dono"]] = por_dono.get(r["dono"], 0) + 1
        print(f"  #{r['id']:<8} {r['dono']:<18} {r['casa']:<14} {r['data'] or '—':<11} "
              f"res={(r['resultado'] or '')!r:<5} odd={(r['odd'] or '')!r:<8} "
              f"arch={r['archived']!s:<5} {r['extraction_state']} → {novo}")
    print("\npor dono:", ", ".join(f"{k}={v}" for k, v in sorted(por_dono.items())))

    if not aplicar:
        print("\n[dry-run] nada foi escrito. Rode com --apply para aplicar.")
        await pool.close()
        return

    async with pool.acquire() as conn:
        async with conn.transaction():
            for r, novo in divergentes:
                await conn.execute(
                    "UPDATE bilhetes SET extraction_state = $1 WHERE id = $2", novo, r["id"],
                )
    print(f"\n✓ {len(divergentes)} linha(s) atualizadas.")

    # Confere o resultado LENDO de volta (o UPDATE pode ter passado e o critério, não).
    async with pool.acquire() as conn:
        restantes = await conn.fetch(
            "SELECT id, resultado, odd, extraction_state FROM bilhetes "
            "WHERE id = ANY($1::int[])", [r["id"] for r, _ in divergentes],
        )
    ruins = [x["id"] for x in restantes
             if R.estado_extracao(x["resultado"], x["odd"]) != x["extraction_state"]]
    print("verificação pós-escrita:", "ok" if not ruins else f"AINDA divergentes: {ruins}")
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main("--apply" in sys.argv))
