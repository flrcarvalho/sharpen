"""Backfill único: canoniza resultados minúsculos ('v'/'w') para maiúsculo e
recalcula extraction_state. Corrige bilhetes que pareciam resolvidos (badge/PL
já upperam) mas ficaram 'aberta' — contando como "aguardando resultado".

Seguro e idempotente: só toca linhas cujo resultado NÃO é canônico mas vira
canônico com UPPER(TRIM(...)). Rodar uma vez; rodar de novo não faz nada.
"""
import asyncio, os, asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"])
    filtro = ("resultado NOT IN ('W','L','V','HW','HL') "
              "AND UPPER(TRIM(resultado)) IN ('W','L','V','HW','HL')")
    pre = await c.fetch(
        f"SELECT id, dono, casa, parceiro, resultado, extraction_state "
        f"FROM bilhetes WHERE {filtro} ORDER BY dono, id")
    print(f"== ALVO (antes) == {len(pre)} linha(s)")
    for r in pre:
        print(dict(r))
    if not pre:
        print("Nada a corrigir.")
        await c.close()
        return
    res = await c.execute(
        f"UPDATE bilhetes SET resultado = UPPER(TRIM(resultado)), "
        f"extraction_state = 'resolvida', atualizado_em = NOW() WHERE {filtro}")
    print(f"\nUPDATE -> {res}")
    resto = await c.fetchval(f"SELECT COUNT(*) FROM bilhetes WHERE {filtro}")
    print(f"residual recuperável restante: {resto}")
    await c.close()


asyncio.run(main())
