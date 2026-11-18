"""Corrige a data de 2 apostas da GiroCerto (Jonathan e Gabriel) que a IA gravou no dia errado (s461, 18/11/2026).

Por quê: a data da planilha é a do EVENTO em Brasília (MASTER_OUTPUT §4; múltipla = perna mais
recente, salvo a perdida do §4.0.1), e a IA errou duas, ambas resolvidas (o UPSERT congela `data`
depois de resolvida: recapturar não conserta):
  • LWYRMHXJ4Z, Jonathan (Wembanyama 5+ Bloqueios, simples W): evento `2026-11-15T22:00:00Z` = 15/11 19:00;
    o bloco dizia `Data (evento mais recente): 15/11/2026 19:00:00`, a IA gravou 16/11.
  • Q6GEKXMSRV, Gabriel (múltipla W de 3, 2 pernas anuladas): perna mais recente `2026-11-17T19:00:00Z`
    = 17/11 16:00; a IA gravou 16/11, o dia da COLOCAÇÃO.

Antes de escrever, confere por código: UMA linha do dono, com a data errada; o cru
mais recente da casa tem o mesmo início mais recente das pernas, e ele cai na data certa em
Brasília. Qualquer divergência: nada escrito (nem nos outros). A edição passa por `atualizar_bilhete` (recalcula a assinatura e grava em `correcoes`
com o rastro `script_s461`).

    python scripts/corrigir_data_girocerto_s461.py            # ensaio, nada escrito
    python scripts/corrigir_data_girocerto_s461.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

# código → (dono, início mais recente das pernas, data errada, data certa)
ALVOS = {
    "LWYRMHXJ4Z": ("Jonathan", "2026-11-15T22:00:00.000Z", "16/11/2026", "15/11/2026"),
    "Q6GEKXMSRV": ("Gabriel", "2026-11-17T19:00:00.000Z", "16/11/2026", "17/11/2026"),
}
RASTRO = "script_s461"


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    erros, plano = [], []
    async with pool.acquire() as conn:
        for cod, (dono, inicio, errada, certa) in ALVOS.items():
            linhas = await conn.fetch(
                "SELECT id, data, resultado, extraction_state FROM bilhetes "
                "WHERE dono = $1 AND casa = 'GiroCerto' AND codigo_bilhete = $2", dono, cod)
            cru = await conn.fetchval(
                "SELECT cru FROM captura_crua WHERE dono = $1 AND upper(casa) = 'GIROCERTO' "
                "AND codigo = $2 ORDER BY recebido_em DESC LIMIT 1", dono, cod)
            cru = json.loads(cru) if isinstance(cru, str) else cru
            if len(linhas) != 1:
                erros.append(f"{cod}: {len(linhas)} linha(s) com o código (esperava 1)")
                continue
            if linhas[0]["data"] == certa:
                print(f"{cod}: já está em {certa}, nada a fazer")
                continue
            if linhas[0]["data"] != errada:
                erros.append(f"{cod}: a linha está com {linhas[0]['data']!r}, não {errada!r}")
                continue
            inicios = [l.get("startsAt") for l in (cru or {}).get("legs") or []]
            if not inicios or max(inicios) != inicio:
                erros.append(f"{cod}: cru com início mais recente {max(inicios) if inicios else None!r}")
                continue
            sp = datetime.fromisoformat(inicio.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Sao_Paulo"))
            if sp.strftime("%d/%m/%Y") != certa:
                erros.append(f"{cod}: o início em Brasília é {sp:%d/%m/%Y %H:%M}, não {certa}")
                continue
            r = linhas[0]
            plano.append((r["id"], dono, cod, certa))
            print(f"{cod} (id {r['id']}, {r['resultado']}, {r['extraction_state']}): data {errada} → {certa}")
    if erros:
        print("NADA ESCRITO:\n  " + "\n  ".join(erros))
        return
    if not aplicar:
        print("\nENSAIO: nada escrito (use --aplicar).")
        return
    for i, dono, cod, certa in plano:
        ok = await atualizar_bilhete(i, {"data": certa}, dono, rastro=RASTRO)
        print(f"{cod}: {'gravado' if ok else 'atualizar_bilhete RECUSOU'}")


if __name__ == "__main__":
    asyncio.run(main())
