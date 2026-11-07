# -*- coding: utf-8 -*-
"""Desfaz a edição em massa de DATA do Feca de 07/11/2026, 11:14 (s440).

O QUE ACONTECEU
---------------
O Feca queria mover para 31/10/2026 só as apostas de NOVEMBRO dos tipsters que deixou de
seguir (NBA Tom, NBA Zora, NBA Gabriel, F1DP), para fechar o resultado deles em outubro.
A seleção da grade pegou o histórico inteiro: um `/bilhetes/lote` gravou 31/10/2026 em
2.272 apostas, de 14:14:10 a 14:14:27 UTC. Dessas, só 20 eram de novembro
(NBA Gabriel 17, F1DP 3); NBA Tom não tinha novembro e NBA Zora ficou fora do lote.

O QUE ESTE SCRIPT FAZ
---------------------
Lê o lote em `correcoes` (dono Feca, campo `data`, origem humana, naquela janela) e, para
cada linha que NÃO seja de novembro de um dos quatro tipsters, devolve a `valor_anterior`
pelo `atualizar_bilhete` (recalcula a assinatura; `data` está em `_SIG_COLS`), com
`rastro='script_s440'` em `correcoes`.

Só escreve se a data do banco AINDA é 31/10/2026: linha que alguém mexeu depois fica.

    python scripts/reverter_data_lote_feca_s440.py            # ensaio
    python scripts/reverter_data_lote_feca_s440.py --aplicar

Antes de aplicar, grava o snapshot (id, data atual, data de volta, assinatura) em
`Backups/s440_reverter_data_lote_feca/`.

Aplicado em 07/11/2026: 2.252 gravadas, 0 falhas; 31/10 do Feca ficou com 138 apostas.

NBA Zora não entrou no lote e FICA em novembro (decisão do Feca, 07/11): as 3 liquidadas
de novembro dela são Kalshi, `origem='sync'`, e o próximo Sincronizar regravaria a data.
"""
import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"')

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

DONO = "Feca"
DATA_LOTE = "31/10/2026"
JANELA_INI = datetime(2026, 11, 7, 14, 14, tzinfo=timezone.utc)
JANELA_FIM = datetime(2026, 11, 7, 14, 15, tzinfo=timezone.utc)
# O que era para ter ido para 31/10: novembro destes tipsters. Fica como está.
TIPSTERS_ALVO = ("NBA Tom", "NBA Zora", "NBA Gabriel", "F1DP")
MES_ALVO = "11/2026"
RASTRO = "script_s440"
BACKUP = ROOT / "Backups" / "s440_reverter_data_lote_feca"


async def main(aplicar: bool) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch(
            """SELECT c.bilhete_id AS id, c.valor_anterior, c.valor_novo,
                      b.data AS data_atual, b.tipster, b.casa, b.assinatura
                 FROM correcoes c JOIN bilhetes b ON b.id = c.bilhete_id AND b.dono = c.dono
                WHERE c.dono = $1 AND c.campo = 'data' AND c.origem IS NULL
                  AND c.criado_em >= $2 AND c.criado_em < $3
                ORDER BY c.bilhete_id""",
            DONO, JANELA_INI, JANELA_FIM)

    fica, volta, mexida = [], [], []
    for r in linhas:
        if r["valor_novo"] != DATA_LOTE:
            mexida.append(r)
        elif r["tipster"] in TIPSTERS_ALVO and (r["valor_anterior"] or "").endswith(MES_ALVO):
            fica.append(r)
        elif r["data_atual"] != DATA_LOTE:
            mexida.append(r)  # alguém mexeu depois do lote: não toco
        else:
            volta.append(r)

    print(f"Lote lido: {len(linhas)} linhas")
    print(f"  ficam em {DATA_LOTE} (novembro dos 4 tipsters): {len(fica)}")
    print(f"     {dict(Counter(r['tipster'] for r in fica))}")
    print(f"  voltam para a data anterior: {len(volta)}")
    print(f"     por tipster: {dict(Counter(r['tipster'] for r in volta))}")
    print(f"     por mês: {dict(sorted(Counter((r['valor_anterior'] or '')[-7:] for r in volta).items(), key=lambda kv: kv[0][-4:] + kv[0][:2]))}")
    print(f"  fora (mexidas depois do lote / inesperadas): {len(mexida)}")
    for r in volta[:5]:
        print(f"     ex.: #{r['id']} {r['casa']} {r['tipster']}: {r['data_atual']} -> {r['valor_anterior']}")

    if not aplicar:
        print("\nENSAIO: nada gravado. Rode com --aplicar para gravar.")
        return

    BACKUP.mkdir(parents=True, exist_ok=True)
    snap = BACKUP / f"snapshot_{datetime.now():%Y%m%d_%H%M%S}.json"
    snap.write_text(json.dumps([{k: r[k] for k in ("id", "data_atual", "valor_anterior",
                                                   "tipster", "casa", "assinatura")}
                                for r in volta], ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"\nSnapshot: {snap}")

    ok = falha = 0
    for i, r in enumerate(volta, 1):
        if await atualizar_bilhete(r["id"], {"data": r["valor_anterior"]}, DONO, rastro=RASTRO):
            ok += 1
        else:
            falha += 1
            print(f"  falhou: #{r['id']}")
        if i % 250 == 0:
            print(f"  {i}/{len(volta)}")
    print(f"\nGravadas: {ok} · falharam: {falha} · de {len(volta)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    asyncio.run(main(ap.parse_args().aplicar))
