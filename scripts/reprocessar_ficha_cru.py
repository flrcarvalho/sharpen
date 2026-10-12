"""Monta a Ficha dos crus já guardados em `captura_crua` que ainda não têm Ficha (s409).

Por quê: o cru de toda casa é guardado desde o 1º dia, mas a Ficha só é montada na chegada,
e só onde `FICHA_SOMBRA_CASAS` liga a casa. O cru que chegou antes da chave (ou antes de um
adaptador corrigido) fica sem Ficha, e o reenvio não ajuda: ele cai em "cru igual".

Idempotente: só pega cru sem NENHUMA linha em `ficha_sombra` apontando para ele (`cru_id`).
Rodar duas vezes não duplica. Não toca em `bilhetes`.

Ordem certa: ligar `FICHA_SOMBRA_CASAS` PRIMEIRO e rodar isto depois. Assim o cru que chegar
no meio já ganha Ficha na rota, e este script pega o resto.

    python scripts/reprocessar_ficha_cru.py --casa DEXSPORT            # ensaio, nada escrito
    python scripts/reprocessar_ficha_cru.py --casa DEXSPORT --aplicar  # grava em ficha_sombra
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import ficha  # noqa: E402
from database import get_pool  # noqa: E402


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _arg(nome: str) -> str | None:
    if nome in sys.argv:
        i = sys.argv.index(nome)
        return sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    return None


def registros_por_lote(linhas) -> tuple[dict, int]:
    """{(dono, casa, parceiro, versao, origem): [registros]} e quantos crus ficaram sem adaptador.
    PURA: recebe as linhas já lidas de `captura_crua`. Usa o MESMO `montar_ficha` da rota."""
    lotes: dict[tuple, list] = defaultdict(list)
    sem_adaptador = 0
    for r in linhas:
        cru = r["cru"] if isinstance(r["cru"], dict) else json.loads(r["cru"])
        f, motivos = ficha.montar_ficha(r["familia"], cru, r["casa"])
        if f is None:
            sem_adaptador += 1
            continue
        chave = (r["dono"], r["casa"], r["parceiro"], r["versao_ext"], r["origem"])
        lotes[chave].append(ficha._registro(f, motivos, r["id"]))
    return lotes, sem_adaptador


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    casa = (_arg("--casa") or "").strip().upper()
    if not casa:
        sys.exit("Informe --casa (ex.: --casa DEXSPORT).")
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch("""
            SELECT c.id, c.dono, c.casa, c.parceiro, c.familia, c.cru, c.versao_ext, c.origem
              FROM captura_crua c
             WHERE c.casa = $1
               AND NOT EXISTS (SELECT 1 FROM ficha_sombra f WHERE f.cru_id = c.id)
             ORDER BY c.id
        """, casa)
    lotes, sem_adaptador = registros_por_lote(linhas)
    regs = [r for rs in lotes.values() for r in rs]
    aceitas = sum(1 for r in regs if r["aceita"])
    print(f"{casa}: {len(linhas)} cru(s) sem Ficha · {aceitas} aceita(s) · "
          f"{len(regs) - aceitas} recusada(s) · {sem_adaptador} sem adaptador")
    for motivo, n in Counter(m for r in regs if not r["aceita"] for m in r["motivos"]).most_common(10):
        print(f"  recusa ×{n}: {motivo}")
    if not aplicar:
        print("\nENSAIO — nada foi escrito. Rode com --aplicar para gravar.")
        return
    novas = 0
    for (dono, c, parceiro, versao, origem), rs in lotes.items():
        novas += await ficha.gravar(dono, c, parceiro, versao, origem, rs)
    print(f"\nGRAVADO: {novas} linha(s) nova(s) em ficha_sombra "
          f"({len(regs) - novas} já existiam por conteúdo igual).")


if __name__ == "__main__":
    asyncio.run(main())
