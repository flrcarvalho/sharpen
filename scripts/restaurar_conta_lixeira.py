"""Restaura uma conta excluída a partir da lixeira (`lixeira_contas`).

O botão Excluir do Painel de Contas é HARD DELETE: apaga a linha em `parceiros` e
TODOS os bilhetes da conta. Antes de apagar, ele grava um snapshot em
`lixeira_contas` que vive **7 dias** (`repository.LIXEIRA_DIAS`). Este script é o
único caminho de volta — a UI não expõe restauração de propósito: prometer "dá pra
desfazer" na tela convidaria ao clique fácil, que é o que o modal existe pra impedir.

Uso:
    python scripts/restaurar_conta_lixeira.py                 → lista o que há na lixeira
    python scripts/restaurar_conta_lixeira.py 42              → prévia da restauração do id 42
    python scripts/restaurar_conta_lixeira.py 42 --aplicar    → restaura numa transação

O que a restauração faz, nesta ordem e numa transação só:
  1. recria a linha em `parceiros` (com o `arquivado` que a conta tinha ao ser excluída);
  2. reinsere os bilhetes do snapshot, coluna a coluna, pelo que a tabela `bilhetes`
     tem HOJE — coluna que sumiu do schema é ignorada, coluna nova fica no default.
     `id` e `criado_em` do snapshot são preservados quando ainda estão livres.

`ON CONFLICT DO NOTHING` nos dois passos, porque nada garante que o espaço continue
vazio: entre a exclusão e a restauração o operador pode ter criado outra conta com o
mesmo nome na mesma casa, e a captura pode já ter regravado bilhetes com a mesma
assinatura (`UNIQUE (dono, casa, parceiro, assinatura)`). Nesse caso o que já existe
manda — restaurar nunca sobrescreve dado novo. O relatório final diz quantos dos
bilhetes do snapshot de fato voltaram e quantos foram descartados por já existirem.

A linha da lixeira **não é apagada** após restaurar: se a restauração parcial não for
o que se queria, o snapshot continua lá até vencer os 7 dias.
"""
import asyncio
import json
import os
import sys

import asyncpg
from dotenv import load_dotenv

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_RAIZ, ".env"))


async def _colunas_bilhetes(conn) -> set[str]:
    """Colunas que `bilhetes` tem AGORA. O snapshot é um JSONB da linha inteira no
    momento da exclusão; casar com o schema atual em vez de assumir que é o mesmo
    é o que faz a restauração sobreviver a um ALTER TABLE no meio dos 7 dias."""
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'bilhetes'"
    )
    return {r["column_name"] for r in rows}


async def listar(conn) -> None:
    rows = await conn.fetch(
        "SELECT id, dono, casa, parceiro, arquivado, n_bilhetes, excluido_em, "
        "       EXTRACT(DAY FROM NOW() - excluido_em)::int AS dias "
        "FROM lixeira_contas ORDER BY excluido_em DESC"
    )
    if not rows:
        print("Lixeira vazia — nenhuma conta excluída nos últimos 7 dias.")
        return
    print(f"{'id':>5}  {'dono':<14} {'casa':<18} {'conta':<28} {'apostas':>8}  excluída")
    print("-" * 96)
    for r in rows:
        resta = max(0, 7 - r["dias"])
        quando = r["excluido_em"].strftime("%d/%m/%Y %H:%M")
        print(f"{r['id']:>5}  {r['dono']:<14} {r['casa']:<18} {r['parceiro']:<28} "
              f"{r['n_bilhetes']:>8}  {quando} (some em {resta}d)")
    print(f"\n{len(rows)} conta(s) na lixeira. "
          f"Para restaurar:  python scripts/restaurar_conta_lixeira.py <id> --aplicar")


async def restaurar(conn, lixeira_id: int, aplicar: bool) -> int:
    row = await conn.fetchrow(
        "SELECT dono, casa, parceiro, arquivado, n_bilhetes, bilhetes "
        "FROM lixeira_contas WHERE id = $1", lixeira_id)
    if not row:
        print(f"Nada na lixeira com id {lixeira_id}. Rode sem argumentos para listar.")
        return 1

    dono, casa, parceiro = row["dono"], row["casa"], row["parceiro"]
    # asyncpg devolve jsonb como str (sem codec global registrado neste script).
    snap = row["bilhetes"]
    linhas = json.loads(snap) if isinstance(snap, str) else (snap or [])

    print(f"Conta:    {casa} · {parceiro}  (dono: {dono})")
    print(f"Snapshot: {len(linhas)} aposta(s)")

    ja_conta = await conn.fetchval(
        "SELECT 1 FROM parceiros WHERE dono = $1 AND casa = $2 AND nome = $3",
        dono, casa, parceiro)
    if ja_conta:
        print("Aviso:    já existe uma conta com esse nome nesta casa — ela será mantida "
              "como está; só as apostas que faltam serão reinseridas.")

    if not aplicar:
        print("\nPRÉVIA — nada foi escrito. Repita com --aplicar para restaurar.")
        return 0

    async with conn.transaction():
        await conn.execute(
            "INSERT INTO parceiros (dono, casa, nome, arquivado) VALUES ($1,$2,$3,$4) "
            "ON CONFLICT (dono, casa, nome) DO NOTHING",
            dono, casa, parceiro, row["arquivado"])

        cols_hoje = await _colunas_bilhetes(conn)
        repostos = 0
        for linha in linhas:
            # Só as colunas que existem hoje E vieram preenchidas no snapshot. `id` e
            # `criado_em` entram junto: preservam a posição da aposta no feed (que ordena
            # por `criado_em`) quando o valor ainda está livre.
            campos = {k: v for k, v in linha.items() if k in cols_hoje and v is not None}
            if not campos:
                continue
            nomes = list(campos)
            ph = ", ".join(f"${i}" for i in range(1, len(nomes) + 1))
            res = await conn.execute(
                f"INSERT INTO bilhetes ({', '.join(nomes)}) VALUES ({ph}) "
                f"ON CONFLICT DO NOTHING",
                *[campos[n] for n in nomes])
            repostos += int(res.split()[-1])

        # `id` veio do snapshot → a sequence do SERIAL ficou atrás dos ids reinseridos e
        # o próximo INSERT normal colidiria. Realinha com o maior id que existe agora.
        await conn.execute(
            "SELECT setval(pg_get_serial_sequence('bilhetes','id'), "
            "               COALESCE((SELECT MAX(id) FROM bilhetes), 1))")

    descartados = len(linhas) - repostos
    print(f"\nRestaurado: {repostos} aposta(s).")
    if descartados:
        print(f"Descartadas: {descartados} — já existiam no banco (o dado novo mandou).")
    print("A linha da lixeira foi mantida; ela vence sozinha em 7 dias.")
    return 0


async def main() -> int:
    url = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
    if not url:
        print("DATABASE_URL não definida (confira o .env).")
        return 1
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    aplicar = "--aplicar" in sys.argv

    conn = await asyncpg.connect(url)
    try:
        if not args:
            await listar(conn)
            return 0
        return await restaurar(conn, int(args[0]), aplicar)
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
