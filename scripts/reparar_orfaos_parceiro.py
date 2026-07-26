"""Repara bilhetes ÓRFÃOS de conta: linhas cujo (dono, casa, parceiro) não existe
mais na tabela `parceiros` — logo nenhuma tela do sistema as alcança.

Como um bilhete vira órfão (sessão 195, Tivo · Feca): a conta foi renomeada
ENQUANTO um lote de extração estava em voo. O `renomear_parceiro` propaga o novo
nome aos bilhetes que já existem, mas o card em processamento carrega uma cópia
rasa do parceiro (nome congelado no clique) e grava com o nome VELHO quando a IA
termina. A grade consulta pelo nome NOVO → 0 linhas, sem erro visível.

Uso:

    python scripts/reparar_orfaos_parceiro.py
        → só RELATÓRIO: lista todo (dono, casa, parceiro) órfão do banco.

    python scripts/reparar_orfaos_parceiro.py --aplicar \
        --dono Feca --casa Tivo --de "Feca [[Eu]]" --para "Feca [Eu]"
        → move SÓ o grupo pedido, numa transação, e recalcula a assinatura.

Por que recalcular a assinatura: `_assinatura` inclui o `parceiro` no hash (com ou
sem código de bilhete). Trocar o parceiro sem recalcular deixaria a assinatura
velha — a próxima captura da mesma conta geraria uma assinatura nova, o UPSERT não
dedupava e o lote inteiro DUPLICAVA. Mesma família do fix de `_assinatura_pos_edicao`.

Idempotente: rodar de novo depois de aplicado não encontra mais o grupo.
"""
import argparse
import asyncio
import csv
import os
import sys
from datetime import datetime, timezone

import asyncpg
from dotenv import load_dotenv

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_RAIZ, ".env"))
# `app/repository.py` importa os vizinhos de forma flat (`from database import ...`),
# então quem entra no path é a pasta `app/`, não a raiz.
sys.path.insert(0, os.path.join(_RAIZ, "app"))

from repository import _assinatura  # noqa: E402  (precisa do .env carregado antes)

_BACKUP_DIR = os.path.join(_RAIZ, "Backups", "s195-orfaos-parceiro")

_SQL_ORFAOS = """
SELECT b.dono, b.casa, b.parceiro, COUNT(*) AS n,
       MIN(b.criado_em) AS ini, MAX(b.criado_em) AS fim
  FROM bilhetes b
  LEFT JOIN parceiros p
         ON p.dono = b.dono AND p.casa = b.casa AND p.nome = b.parceiro
 WHERE p.id IS NULL
 GROUP BY 1, 2, 3
 ORDER BY fim DESC
"""


async def relatorio(conn) -> list[dict]:
    rows = [dict(r) for r in await conn.fetch(_SQL_ORFAOS)]
    if not rows:
        print("Nenhum bilhete órfão. Nada a reparar.")
        return rows
    print(f"== BILHETES ÓRFÃOS == {len(rows)} grupo(s)\n")
    for r in rows:
        print(f"  {r['dono']:<10} | {r['casa']:<12} | {r['parceiro']:<32} | "
              f"{r['n']:>4} bilhete(s) | último {r['fim']:%d/%m/%Y %H:%M}")
    print("\nPara mover um grupo:\n"
          "  python scripts/reparar_orfaos_parceiro.py --aplicar "
          '--dono <D> --casa <C> --de "<nome órfão>" --para "<conta existente>"')
    return rows


def _dump_backup(rows: list[dict], dono: str, casa: str, de: str) -> str:
    os.makedirs(_BACKUP_DIR, exist_ok=True)
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    alvo = os.path.join(_BACKUP_DIR, f"{carimbo}-{dono}-{casa}.csv")
    with open(alvo, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "dono", "casa", "parceiro", "assinatura", "codigo_bilhete",
                    "data", "aposta", "descricao", "stake", "odd", "resultado"])
        for r in rows:
            w.writerow([r["id"], dono, casa, de, r["assinatura"], r["codigo_bilhete"],
                        r["data"], r["aposta"], r["descricao"], r["stake"], r["odd"],
                        r["resultado"]])
    return alvo


async def aplicar(conn, dono: str, casa: str, de: str, para: str) -> None:
    destino = await conn.fetchrow(
        "SELECT id, arquivado FROM parceiros WHERE dono = $1 AND casa = $2 AND nome = $3",
        dono, casa, para,
    )
    if not destino:
        print(f"ABORTADO: não existe a conta destino {casa} / {para} (dono {dono}).")
        return

    rows = [dict(r) for r in await conn.fetch(
        """SELECT id, assinatura, codigo_bilhete, data, aposta, descricao, stake, odd, resultado
             FROM bilhetes
            WHERE dono = $1 AND casa = $2 AND parceiro = $3
            ORDER BY id""",
        dono, casa, de,
    )]
    if not rows:
        print(f"Nada encontrado em {casa} / {de} (dono {dono}). Nada a fazer.")
        return

    # Sem seta unicode nos prints: o console do Windows roda em cp1252 e estoura.
    print(f"== MOVER == {len(rows)} bilhete(s): {casa} / '{de}' -> '{para}' (dono {dono})")
    bkp = _dump_backup(rows, dono, casa, de)
    print(f"backup: {bkp}")

    movidos = 0
    colisoes = []
    async with conn.transaction():
        for r in rows:
            final = {
                "casa": casa, "parceiro": para,
                "data": r["data"] or "", "aposta": r["aposta"] or "",
                "descricao": r["descricao"] or "", "stake": r["stake"] or "",
                "odd": r["odd"] or "", "codigo_bilhete": r["codigo_bilhete"] or "",
            }
            tem_codigo = bool(final["codigo_bilhete"].strip())
            nova = None
            # Mesmo laço de counter do `_assinatura_pos_edicao`: se o conteúdo colidir
            # com outra linha JÁ existente na conta destino, escala o _counter (regra do
            # Feca para bilhetes distintos de conteúdo idêntico). Com código, o hash
            # ignora o counter → escalar não sai do lugar, então aborta o grupo.
            for cnt in range(1, 51):
                sig = _assinatura(final, _counter=cnt)
                livre = await conn.fetchval(
                    """SELECT NOT EXISTS (
                           SELECT 1 FROM bilhetes
                            WHERE dono = $1 AND casa = $2 AND parceiro = $3
                              AND assinatura = $4 AND id <> $5)""",
                    dono, casa, para, sig, r["id"],
                )
                if livre:
                    nova = sig
                    break
                if tem_codigo:
                    break
            if nova is None:
                colisoes.append(r["id"])
                continue
            await conn.execute(
                "UPDATE bilhetes SET parceiro = $1, assinatura = $2, atualizado_em = NOW() "
                "WHERE id = $3 AND dono = $4",
                para, nova, r["id"], dono,
            )
            movidos += 1

    print(f"movidos: {movidos}")
    if colisoes:
        print(f"NÃO movidos (assinatura colide no destino): {colisoes}")
    resto = await conn.fetchval(
        "SELECT COUNT(*) FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3",
        dono, casa, de,
    )
    print(f"residual em '{de}': {resto}")


async def main() -> None:
    # description ASCII de proposito: o --help no console cp1252 estoura com acento.
    ap = argparse.ArgumentParser(
        description="Repara bilhetes orfaos de conta (ver docstring do arquivo).")
    ap.add_argument("--aplicar", action="store_true", help="executa a movimentação")
    ap.add_argument("--dono")
    ap.add_argument("--casa")
    ap.add_argument("--de", help="nome órfão gravado nos bilhetes")
    ap.add_argument("--para", help="nome da conta que deve receber os bilhetes")
    a = ap.parse_args()

    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        await relatorio(conn)
        if not a.aplicar:
            return
        if not all([a.dono, a.casa, a.de, a.para]):
            print("\n--aplicar exige --dono, --casa, --de e --para.")
            return
        print()
        await aplicar(conn, a.dono, a.casa, a.de, a.para)
        print("\n== RELATÓRIO PÓS-REPARO ==")
        await relatorio(conn)
    finally:
        await conn.close()


asyncio.run(main())
