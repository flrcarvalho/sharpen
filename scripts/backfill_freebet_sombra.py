"""Marca a FREEBET dos bilhetes já gravados, lendo o BLOCO CRU da sombra (s392).

NASCEU DE: `MASTER_RESULTADO §5.8` (decisão do Feca, 03-04/10/2026) — freebet é dinheiro da
casa, e o P/L é `retorno − (stake − freebet)`. Desde o passo 2a a captura grava a coluna
`bilhetes.stake_freebet` a partir do bloco, e a recaptura marca o histórico que a casa ainda
devolve. Este script cobre o RESTO: bilhete cuja casa já não devolve aquele histórico, mas
cujo bloco ficou guardado em `sombra_rotulos` (desde 26/08/2026).

COMO: a sombra guarda o bloco SEM a linha `[Código: …]`; o script a recoloca e passa pelo
MESMO leitor da captura (`repository.freebets_do_texto`) — não há segunda régua. O valor vai
para a coluna pela MESMA conversão do `/salvar` (`repository._freebet_da_linha`: R$ pela
cotação da stake; freebet maior que a stake fica nula).

O QUE ELE NÃO FAZ:
  • só PREENCHE: linha que já tem `stake_freebet` não é tocada (o UPSERT faz o mesmo);
  • não mexe em stake, odd nem resultado — o P/L muda porque é derivado na leitura;
  • print não tem bloco: fica de fora por construção;
  • Betbra e BetBy marcam freebet SEM valor e o leitor não os lê (BACKLOG 4.0a).

Medido em 04/10/2026 (ensaio, só leitura): ver a saída do próprio script. O leitor deu 20 de
20 nos blocos com freebet e 0 falso positivo em 3.000 blocos sem freebet.

Uso:
    python scripts/backfill_freebet_sombra.py             # ensaio (não escreve)
    python scripts/backfill_freebet_sombra.py --aplicar
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
os.environ.setdefault("SESSION_SECRET", "backfill-freebet")

import asyncpg  # noqa: E402

from repository import _freebet_da_linha, calcular_pl, freebets_do_texto  # noqa: E402

_SQL_SOMBRA = """
    SELECT DISTINCT ON (dono, casa, codigo) dono, casa, codigo, bruto
      FROM sombra_rotulos
     WHERE codigo IS NOT NULL AND codigo <> ''
       AND (bruto ILIKE '%Freebet inclu%' OR bruto ILIKE '%aposta grátis (freebet)%')
     ORDER BY dono, casa, codigo, criado_em DESC
"""


async def main(aplicar: bool) -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        blocos = await conn.fetch(_SQL_SOMBRA)
        plano, sem_linha, ja_tem, recusados = [], 0, 0, 0
        for b in blocos:
            fb = freebets_do_texto(f"[Código: {b['codigo']}]\n{b['bruto']}").get(b["codigo"])
            if not fb:
                recusados += 1           # rótulo sem valor (Betbra/BetBy) ou ambíguo
                continue
            linhas = await conn.fetch(
                "SELECT id, parceiro, stake, odd, resultado, cotacao, stake_freebet "
                "FROM bilhetes WHERE dono = $1 AND casa = $2 AND codigo_bilhete = $3",
                b["dono"], b["casa"], b["codigo"])
            if not linhas:
                sem_linha += 1
                continue
            for r in linhas:
                if r["stake_freebet"] is not None:
                    ja_tem += 1
                    continue
                valor = _freebet_da_linha(dict(r), b["codigo"], {b["codigo"]: fb})
                if valor is None:
                    recusados += 1
                    continue
                antes = calcular_pl(r["stake"], r["odd"], r["resultado"])
                depois = calcular_pl(r["stake"], r["odd"], r["resultado"], valor)
                plano.append((r["id"], b["dono"], b["casa"], b["codigo"], r["stake"],
                              r["resultado"], valor, antes, depois))

        print(f"blocos com freebet na sombra: {len(blocos)}")
        print(f"  sem linha no banco: {sem_linha} · já marcados: {ja_tem} · recusados: {recusados}")
        print(f"  a marcar: {len(plano)}\n")
        delta = 0.0
        for (i, dono, casa, cod, stake, res, valor, antes, depois) in plano:
            d = (depois or 0) - (antes or 0) if antes is not None and depois is not None else 0
            delta += d
            print(f"  #{i:<8} {dono:<10} {casa:<12} {cod:<16} stake {stake:>9} "
                  f"{res or 'aberta':<6} freebet {valor!s:>8}  P/L {antes!s:>9} -> {depois!s:>9}")
        print(f"\nvariação total de P/L: {delta:+.2f}")

        if not aplicar:
            print("\nENSAIO: nada foi escrito. Rode com --aplicar para gravar.")
            return
        async with conn.transaction():
            for (i, *_resto) in plano:
                valor = _resto[5]
                await conn.execute(
                    "UPDATE bilhetes SET stake_freebet = $1, atualizado_em = NOW() "
                    "WHERE id = $2 AND stake_freebet IS NULL", valor, i)
        print(f"\nAPLICADO: {len(plano)} linha(s) marcadas.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main("--aplicar" in sys.argv))
