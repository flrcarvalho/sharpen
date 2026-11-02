"""Limpeza única (Bolsa de Aposta / Feca) — sessão 133.

Apaga 3 registros-lixo confirmados, mostrando cada um antes:
  - 54127: "Over 2,5 [France v Morocco]" SEM odd, SEM código — duplicata superada
           pela gêmea COM código 48575 ("Under 2,5 @2,04", cod 105194045).
  - 54131: "Over 2,5 [Norway v England]" SEM odd, SEM código — duplicata superada
           pela gêmea COM código 53295 ("Over 2,5 @1,75", cod 105783621).
  - 17979: "Saque R$ 674,48" (stake 0,00) — movimento de banca, não é aposta.

Seguro: só toca esses 3 ids. Idempotente (rodar de novo não acha nada).
NÃO mexe na 3351 (Folarin 25/06, arquivada, V, sem odd) — arquivada e inócua.
"""
import asyncio, os, asyncpg
from dotenv import load_dotenv
from _lixeira import mover_para_lixeira  # Fase 7 (s438): aposta sai pela lixeira

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
IDS = [54127, 54131, 17979]


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"])
    pre = await c.fetch(
        "SELECT id, data, casa, parceiro, LEFT(descricao,34) d, stake, odd, "
        "resultado, extraction_state, codigo_bilhete, archived "
        "FROM bilhetes WHERE id = ANY($1) ORDER BY id", IDS)
    print(f"== A APAGAR == {len(pre)} linha(s)")
    for r in pre:
        print(f"  id={r['id']} | {r['data']} | {r['casa']}/{r['parceiro']} | "
              f"stake={r['stake']!r} odd={r['odd']!r} res={r['resultado']!r} "
              f"est={r['extraction_state']} cod={r['codigo_bilhete']} arch={r['archived']} | {r['d']}")
    if not pre:
        print("Nada a apagar (já limpo).")
        await c.close()
        return
    res = len(await mover_para_lixeira(c, "id = ANY($1)", [IDS], "órfãs da Bolsa (12/07/2026)"))
    print(f"\nDELETE -> {res}")
    await c.close()


asyncio.run(main())
