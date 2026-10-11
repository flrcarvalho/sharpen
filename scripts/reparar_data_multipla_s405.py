"""Redata a múltipla PERDIDA já gravada pelo início da perna perdida (sessão 405).

NASCEU DE: a sidebar ("MÊS" = mês inteiro) não batia com o MTD da tela. Parte da
diferença eram múltiplas que a casa liquidou assim que a 1ª perna perdeu, mas que
ficaram datadas pelo jogo mais tarde (`MASTER_OUTPUT §4`): nasciam resolvidas no futuro,
saíam do MTD e entravam na sidebar. Regra nova em `MASTER_OUTPUT §4.0.1` (decisão do
Feca, 09/10/2026), aplicada na extração por `repository.corrigir_data_tsv`.

POR QUE UM SCRIPT: o UPSERT congela `data` quando a linha resolve. A regra nova pega a
captura nova e a linha que liquida depois de gravada aberta; o que JÁ está gravado
resolvido só muda por aqui.

O QUE ELE USA: o bloco cru da `sombra_rotulos` (120 dias de retenção), casado por
(dono, casa, código), e a MESMA função da extração (`data_da_perna_perdida`). Nada é
reimplementado aqui.

TRAVAS:
  1. Só `L`, só linha com código, só para TRÁS (a perna perdida antes da data gravada).
  2. Correção humana manda: bilhete com registro de `data` em `correcoes` é pulado.
  3. O UPDATE confere a data antiga no WHERE: se alguém mexeu entre o ensaio e a escrita,
     a linha não é tocada.
  4. `data` não entra na assinatura de linha COM código (`_assinatura`), então redatar não
     duplica nada na próxima captura.

FORA DE ALCANCE: Bet365, Superbet, Pinnacle, Megapari, 1xBet e PariPesa (o bloco não traz
a perna perdida com início; BACKLOG 1.17) e linha cujo bloco já saiu da sombra.

Uso:
    python scripts/reparar_data_multipla_s405.py              # ensaio (não escreve)
    python scripts/reparar_data_multipla_s405.py --dono Feca  # ensaio de um dono
    python scripts/reparar_data_multipla_s405.py --aplicar
"""
import asyncio
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

from database import get_pool  # noqa: E402
from repository import _data_iso, calcular_pl, data_da_perna_perdida  # noqa: E402

DESTINO = ROOT / "Backups" / "s405-data-multipla" / "bilhetes_antes.json"


def _arg(nome: str) -> str | None:
    if nome in sys.argv:
        i = sys.argv.index(nome)
        return sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    return None


def candidatos(linhas, travados) -> tuple[list[dict], list[dict]]:
    """(a redatar, pulados por correção humana). PURA: recebe as linhas já lidas."""
    mudar, pulados = [], []
    for r in linhas:
        if (r["resultado"] or "").strip().upper() != "L":
            continue
        red = data_da_perna_perdida(r["bruto"])
        atual = _data_iso(r["data"])
        if not red or not atual or red >= atual:
            continue
        item = {
            "id": r["id"], "dono": r["dono"], "casa": r["casa"], "codigo": r["codigo"],
            "data_antes": r["data"], "data_depois": f"{red[8:10]}/{red[5:7]}/{red[0:4]}",
            "iso_antes": atual, "iso_depois": red,
            "pl": calcular_pl(r["stake"], r["odd"], "L", r["stake_freebet"]),
        }
        (pulados if r["id"] in travados else mudar).append(item)
    return mudar, pulados


async def main() -> None:
    aplicar = "--aplicar" in sys.argv
    dono = _arg("--dono")
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch("""
            SELECT DISTINCT ON (b.id)
                   b.id, b.dono, b.casa, b.codigo_bilhete AS codigo, b.data, b.resultado,
                   b.stake, b.odd, b.stake_freebet, s.bruto
              FROM bilhetes b
              JOIN sombra_rotulos s
                ON s.dono = b.dono AND s.casa = b.casa AND s.codigo = b.codigo_bilhete
             WHERE b.codigo_bilhete <> '' AND b.resultado = 'L'
               AND ($1::text IS NULL OR b.dono = $1)
             ORDER BY b.id, s.criado_em DESC
        """, dono)
        travados = {r["bilhete_id"] for r in await conn.fetch(
            "SELECT DISTINCT bilhete_id FROM correcoes WHERE campo = 'data' "
            "AND bilhete_id IS NOT NULL")}

        mudar, pulados = candidatos([dict(r) for r in linhas], travados)

        por_casa, por_mes = defaultdict(int), defaultdict(float)
        for m in sorted(mudar, key=lambda x: (x["dono"], x["iso_antes"])):
            por_casa[m["casa"]] += 1
            if m["iso_antes"][:7] != m["iso_depois"][:7]:
                pl = m["pl"] or 0.0
                por_mes[(m["dono"], m["iso_antes"][:7])] -= pl
                por_mes[(m["dono"], m["iso_depois"][:7])] += pl
            print(f'{m["id"]:>7} {m["dono"]:<12} {m["casa"]:<12} {m["codigo"][:22]:<22} '
                  f'{m["data_antes"]} → {m["data_depois"]}  P/L {m["pl"] or 0:>9,.2f}')
            if aplicar:
                r = await conn.execute(
                    "UPDATE bilhetes SET data = $1, atualizado_em = NOW() "
                    "WHERE id = $2 AND dono = $3 AND data = $4 AND resultado = 'L'",
                    m["data_depois"], m["id"], m["dono"], m["data_antes"])
                if r.split()[-1] != "1":
                    print(f'        ⚠ UPDATE não aplicou no bilhete {m["id"]} (mudou desde a leitura)')

    print("\n" + "=" * 96)
    print(f"conferidos (L com bloco na sombra): {len(linhas)} · a redatar: {len(mudar)} · "
          f"pulados por correção humana: {len(pulados)}")
    print("por casa:", dict(sorted(por_casa.items(), key=lambda x: -x[1])))
    if por_mes:
        print("P/L que troca de MÊS (dono, mês): " + ", ".join(
            f"{d} {m}: {v:+,.2f}" for (d, m), v in sorted(por_mes.items())))
    for p in pulados:
        print(f'  PULADO (data editada à mão): {p["id"]} {p["dono"]} {p["casa"]} '
              f'{p["data_antes"]} → seria {p["data_depois"]}')

    if aplicar:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        anterior = []
        if DESTINO.exists():
            try:
                anterior = json.loads(DESTINO.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                print("⚠ snapshot anterior ilegível — o novo NÃO será gravado por cima")
                anterior = None
        if anterior is not None:
            carimbo = datetime.now(timezone.utc).isoformat()
            DESTINO.write_text(json.dumps(
                anterior + [dict(m, aplicado_em=carimbo) for m in mudar],
                ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"\n✔ aplicado. Snapshot do ANTES em {DESTINO}")
    else:
        print("\nENSAIO — nada foi escrito. Rode com --aplicar para gravar.")


if __name__ == "__main__":
    asyncio.run(main())
