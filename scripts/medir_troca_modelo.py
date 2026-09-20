"""Mede o efeito da troca de modelo no custo. Leitura pura: não escreve nada.

    python scripts/medir_troca_modelo.py [--dias 7]

Nasceu da s377, quando o `DEFAULT_MODEL` saiu do Sonnet 4.6 para o Sonnet 5. O pedido
do Feca foi literal: *"garanta que os custos continuam a ser medidos após a troca"*.

**Por que um script e não uma consulta de uma vez:** o defeito que esta frente inteira
persegue é sempre o mesmo — a mudança sobe, ninguém volta para medir, e o CI verde faz
as vezes de prova. Deixar a medição escrita e nomeada é o que a transforma de intenção
em passo. Ver `docs/CASOS.md`, "o limite que o teste declarou e ninguém foi fechar".

**Duas armadilhas que este script evita, e que já morderam antes:**

  • **Comparar DINHEIRO entre janelas mistura preço com quantidade.** A barreira de
    recaptura (s376) mexe na QUANTIDADE de token e a troca de modelo no PREÇO. Por isso
    a tabela traz as duas unidades: tokens por bilhete isola a barreira, US$ por bilhete
    isola a troca. Quem olhar só o dinheiro vai atribuir um efeito ao outro.
  • **O denominador não é `count(*)` de bilhetes.** Bot de tipster e a base `realtrial`
    gravam com `origem='extracao'` sem passar por modelo nenhum; contá-los derruba o
    custo por bilhete sozinho. Só entra bilhete que teve chamada no mesmo
    (dono, casa, dia) — a mesma régua do `ESTUDO_PRECIFICACAO §7`.
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, timedelta

import asyncpg

if hasattr(sys.stdout, "reconfigure"):   # console do Windows e cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PTAX = 5.1253      # PTAX de venda de 04/09/2026, o mesmo do ESTUDO §7, para comparar
TROCA = date(2026, 9, 20)   # dia do deploy do Sonnet 5


def _dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise SystemExit("DATABASE_URL ausente. Rode com o .env do projeto carregado.")
    return url.replace("postgres://", "postgresql://", 1)


async def _janela(conn, ini: date, fim: date) -> dict:
    r = await conn.fetchrow(
        """SELECT count(*) n, coalesce(sum(custo_usd),0) usd,
                  coalesce(sum(input),0) i, coalesce(sum(output),0) o,
                  coalesce(sum(cache_read),0) cr, coalesce(sum(cache_write),0) cw,
                  coalesce(sum(chunks),0) ch
             FROM uso_tokens WHERE criado_em >= $1 AND criado_em < $2""", ini, fim)
    bil = await conn.fetchval(
        """SELECT count(*) FROM bilhetes b
            WHERE b.origem='extracao' AND b.criado_em >= $1 AND b.criado_em < $2
              AND EXISTS (SELECT 1 FROM uso_tokens u
                           WHERE u.dono=b.dono AND u.casa=b.casa
                             AND u.criado_em::date = b.criado_em::date)""", ini, fim)
    modelos = await conn.fetch(
        """SELECT modelo, count(*) n FROM uso_tokens
            WHERE criado_em >= $1 AND criado_em < $2 GROUP BY 1 ORDER BY 2 DESC""", ini, fim)
    tok = sum(float(r[k]) for k in ("i", "o", "cr", "cw"))
    dias = max((fim - ini).days, 1)
    return {
        "chamadas": r["n"], "bilhetes": bil, "dias": dias,
        "usd_mes": float(r["usd"]) / dias * 30,
        "usd_bilhete": float(r["usd"]) / bil if bil else 0.0,
        "tok_bilhete": tok / bil if bil else 0.0,
        "chunks": float(r["ch"]) / r["n"] if r["n"] else 0.0,
        "modelos": {m["modelo"]: m["n"] for m in modelos},
    }


async def main() -> None:
    dias = 7
    for i, a in enumerate(sys.argv):
        if a == "--dias" and i + 1 < len(sys.argv):
            dias = int(sys.argv[i + 1])

    conn = await asyncpg.connect(_dsn())
    antes = await _janela(conn, TROCA - timedelta(days=dias), TROCA)
    depois = await _janela(conn, TROCA, min(TROCA + timedelta(days=dias), date.today() + timedelta(days=1)))

    print("=== Troca de modelo em %s · janelas de %d dias ===\n" % (TROCA, dias))
    if depois["chamadas"] == 0:
        print("Ainda não há chamadas depois da troca. Rode de novo daqui a alguns dias.")
        await conn.close()
        return

    print("%-26s%16s%16s%12s" % ("", "ANTES", "DEPOIS", "variação"))

    def linha(rot, chave, fmt="%.4f", inverter=False):
        a, d = antes[chave], depois[chave]
        var = ("%+.1f%%" % (100 * (d - a) / a)) if a else "—"
        print("%-26s%16s%16s%12s" % (rot, fmt % a, fmt % d, var))

    linha("chamadas", "chamadas", "%d")
    linha("bilhetes por IA", "bilhetes", "%d")
    linha("pedaços por chamada", "chunks", "%.2f")
    print("%-26s%16s%16s%12s" % ("-" * 20, "", "", ""))
    print("  o que a BARREIRA move (quantidade), imune ao preço:")
    linha("  tokens por bilhete", "tok_bilhete", "%.0f")
    print("  o que a TROCA move (preço), imune à quantidade:")
    linha("  US$ por bilhete", "usd_bilhete", "%.4f")
    linha("  US$/mês (ritmo)", "usd_mes", "%.0f")
    print("\n  R$ por bilhete: %.4f  →  %.4f" % (
        antes["usd_bilhete"] * PTAX, depois["usd_bilhete"] * PTAX))
    print("\n  modelos ANTES : %s" % antes["modelos"])
    print("  modelos DEPOIS: %s" % depois["modelos"])
    if any(m != "claude-sonnet-5" for m in depois["modelos"]):
        print("\n  ⚠️  há chamada em outro modelo depois da troca — confira se é print,")
        print("     escolha manual na tela, ou deploy que ainda não subiu.")

    print("\n--- as 5 abertas sem código que a troca podia desgarrar (s377) ---")
    ids = [227068, 312031, 313752, 337987, 341273]
    for r in await conn.fetch(
            """SELECT id, casa, dono, extraction_state, assinatura
                 FROM bilhetes WHERE id = ANY($1::bigint[]) ORDER BY id""", ids):
        print("   id=%-8s%-12s%-12s%-11s%s" % (
            r["id"], r["casa"], r["dono"], r["extraction_state"], r["assinatura"]))
    print("   (a foto de antes está em Backups/s377_sonnet5/)")
    print("   assinatura mudada + linha nova na mesma conta = desgarrou; conferir à mão.")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
