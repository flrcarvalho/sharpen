# -*- coding: utf-8 -*-
"""
corrigir_fornecedor_sujo_s369.py — duas contas cujo FORNECEDOR está escrito errado.

O fornecedor mora DENTRO do nome da conta (modelo `Parceiro [Fornecedor]`), então uma
grafia torta ali cria um fornecedor paralelo que a tela mostra como se fosse outra
pessoa. As duas apareceram na medição da s366, ao levantar o universo de fornecedores
para a aba Contas:

  id 321 · Superbet · `arthurbarbosabets [[JC]]`        → `arthurbarbosabets [JC]`
      Colchete duplo. O regex `^(.+?)\\s*\\[(.+?)\\]$` captura `[JC]` como se fosse o
      nome do fornecedor, então ele vira um 15º fornecedor com 1 conta, ao lado do `JC`
      de verdade, que tem 33.

  id 514 · Betano   · `Sem dono [Sem fornecedor - Ago 2026]` → `Sem dono [Eu]`
      **Decisão do Feca, com a origem assumida como desconhecida:** *"essa segunda eu
      nao achei a origem dela, nao sei qual foi, mas tava misturada, entao joguei pra Eu
      e deixei as apostas contarem no resultado, pois nao havia nenhuma conta com os
      mesmos resultados. ela existiu, so nao sei a origem, entao planilhar assim ta ok."*
      São **207 bilhetes**, e a consequência é real e querida: eles passam a contar como
      conta PRÓPRIA (custo zero declarado) na aba Contas e no custo × retorno.

POR QUE NÃO É UM `UPDATE`: `casa` e `parceiro` entram JUNTOS no hash de `_assinatura`.
Trocar o nome sem recalcular deixa a linha com o hash antigo, a próxima captura gera uma
assinatura nova, não colide com nada, o UPSERT não dedupa e **o histórico duplica
inteiro** (CLAUDE.md, "Mexeu em `casa` ou `parceiro`? Recalcule a assinatura"). Quem já
faz isso certo é `repository.editar_parceiro()`, numa transação só — é ele que este
script chama.

ENSAIO é o padrão. `--aplicar` escreve.

    python scripts/corrigir_fornecedor_sujo_s369.py            # ensaio
    python scripts/corrigir_fornecedor_sujo_s369.py --aplicar  # vale
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "app"))

import asyncpg  # noqa: E402

DONO = "Feca"
# (id, nome atual, nome novo) — o id é conferido contra o nome antes de qualquer escrita:
# id errado não dá erro, renomeia a conta de outra pessoa.
ALVOS = [
    (321, "arthurbarbosabets [[JC]]", "arthurbarbosabets [JC]"),
    (514, "Sem dono [Sem fornecedor - Ago 2026]", "Sem dono [Eu]"),
]


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        env = RAIZ / ".env"
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                url = linha.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not url:
        print("DATABASE_URL ausente.", file=sys.stderr)
        raise SystemExit(2)
    return url.replace("postgres://", "postgresql://", 1)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true", help="escreve (sem isto, só ensaia)")
    args = ap.parse_args()

    conn = await asyncpg.connect(_database_url())
    try:
        # ── 1) confere que o id É a conta esperada ────────────────────────────
        planejado = []
        for pid, antigo, novo in ALVOS:
            row = await conn.fetchrow(
                "SELECT id, casa, nome FROM parceiros WHERE id = $1 AND dono = $2", pid, DONO)
            if not row:
                print(f"  ABORTA: id {pid} não existe para o dono {DONO}.")
                return
            if row["nome"] != antigo:
                print(f"  ABORTA: id {pid} tem nome {row['nome']!r}, esperado {antigo!r}.")
                return
            n = await conn.fetchval(
                "SELECT count(*) FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3",
                DONO, row["casa"], antigo)
            colide = await conn.fetchval(
                "SELECT id FROM parceiros WHERE dono = $1 AND casa = $2 AND nome = $3 AND id <> $4",
                DONO, row["casa"], novo, pid)
            if colide:
                print(f"  ABORTA: já existe conta {novo!r} na {row['casa']} (id {colide}).")
                return
            planejado.append({"id": pid, "casa": row["casa"], "de": antigo, "para": novo, "bilhetes": n})
            print(f"  {row['casa']:<10} id {pid:>4}  {antigo!r}")
            print(f"  {'':<10} {'':>7}  -> {novo!r}   ({n} bilhetes)")

        # ── 2) BACKUP antes de escrever, e RELIDO ─────────────────────────────
        # Dump que ninguém releu é promessa, não backup (a lição do zerar_base da s364).
        if args.aplicar:
            carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
            destino = RAIZ / "Backups" / "s369-fornecedor-sujo"
            destino.mkdir(parents=True, exist_ok=True)
            dump = {"quando": carimbo, "dono": DONO, "alvos": planejado, "parceiros": [], "bilhetes": []}
            for p in planejado:
                pr = await conn.fetchrow(
                    "SELECT to_jsonb(p.*) AS j FROM parceiros p WHERE id = $1", p["id"])
                dump["parceiros"].append(json.loads(pr["j"]))
                bs = await conn.fetch(
                    "SELECT to_jsonb(b.*) AS j FROM bilhetes b "
                    "WHERE dono = $1 AND casa = $2 AND parceiro = $3",
                    DONO, p["casa"], p["de"])
                dump["bilhetes"].extend(json.loads(b["j"]) for b in bs)
            arq = destino / f"fornecedor_sujo_{carimbo}.json"
            arq.write_text(json.dumps(dump, ensure_ascii=False, indent=1, default=str),
                           encoding="utf-8", newline="")
            relido = json.loads(arq.read_text(encoding="utf-8"))
            esperado = sum(p["bilhetes"] for p in planejado)
            if len(relido["bilhetes"]) != esperado or len(relido["parceiros"]) != len(planejado):
                print(f"  ABORTA: o backup não confere ({len(relido['bilhetes'])} de {esperado} "
                      f"bilhetes). Nada foi escrito.")
                return
            print(f"\n  backup relido e conferido: {arq.name} "
                  f"({len(relido['parceiros'])} contas, {len(relido['bilhetes'])} bilhetes)")
    finally:
        await conn.close()

    if not args.aplicar:
        print("\n  ENSAIO — nada foi escrito. Rode com --aplicar para valer.")
        return

    # ── 3) a escrita passa pelo `editar_parceiro`, que recalcula a assinatura ──
    os.environ["DATABASE_URL"] = _database_url()
    from repository import editar_parceiro  # noqa: E402

    print()
    for p in planejado:
        r = await editar_parceiro(p["id"], p["para"], None, DONO)
        if not r.get("ok"):
            print(f"  FALHOU id {p['id']}: {r.get('motivo')}")
            continue
        print(f"  id {p['id']:>4}  ok · {r['bilhetes_atualizados']} bilhetes, "
              f"{r['assinaturas_recalculadas']} assinaturas recalculadas")

    # ── 4) confere o RESULTADO, não a intenção ────────────────────────────────
    conn = await asyncpg.connect(_database_url())
    try:
        print()
        sobra = await conn.fetch(
            "SELECT id, casa, nome FROM parceiros WHERE dono = $1 "
            "AND (nome LIKE '%[[%' OR nome ILIKE '%Sem fornecedor%')", DONO)
        print(f"  contas com fornecedor torto restantes: {len(sobra)}")
        for p in planejado:
            n_novo = await conn.fetchval(
                "SELECT count(*) FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3",
                DONO, p["casa"], p["para"])
            n_velho = await conn.fetchval(
                "SELECT count(*) FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3",
                DONO, p["casa"], p["de"])
            sinal = "ok" if (n_novo == p["bilhetes"] and n_velho == 0) else "CONFERIR"
            print(f"  {p['casa']:<10} {p['para']!r}: {n_novo} bilhetes "
                  f"(sobrou {n_velho} no nome antigo) · {sinal}")
        # Assinatura duplicada é o modo de falha que este script existe para evitar.
        dup = await conn.fetchval(
            "SELECT count(*) FROM (SELECT casa, parceiro, assinatura FROM bilhetes "
            "WHERE dono = $1 GROUP BY 1,2,3 HAVING count(*) > 1) t", DONO)
        print(f"  assinaturas duplicadas na base: {dup}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
