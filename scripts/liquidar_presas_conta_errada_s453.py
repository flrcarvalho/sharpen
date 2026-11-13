"""Liquida as 4 apostas da 1win `Ellen [Eu]` que a captura na conta errada deixou presas (s453).

Por quê: em 13/11/2026 19:43 a extensão capturou a 1win do Feca na conta ARQUIVADA `Feca [Eu]`.
A Ficha gravou 13 apostas lá (já liquidadas na casa) e marcou o código no `ficha_virada` e no
`bloco_visto`, que são chaveados por dono + casa + código, SEM a conta. Às 19:44 as 13 foram
excluídas pela tela de Extração; às 19:44:34 a captura certa, na `Ellen [Eu]`, achou o código
"já lido" e não aplicou a liquidação. Recapturar não conserta pelo mesmo motivo.

Resultado: 4 apostas liquidadas na casa seguem abertas na Ellen, e a Caixa diverge R$ 1.199,95
(o retorno da W). O valor certo de cada uma é o que a Ficha derivou do cru liquidado às 19:43 e
que está no snapshot da `lixeira_bilhetes`.

O script só escreve com TRÊS fontes concordando, código a código:
  1. a linha da Ellen existe, é única, está `aberta`, com a stake e a odd esperadas;
  2. o snapshot da lixeira (parceiro `Feca [Eu]`) tem o mesmo código, o resultado esperado e a
     mesma stake e odd;
  3. há cru do mesmo código recebido sob `Feca [Eu]` em 13/11 com `status` diferente de 0
     (0 = aberta na 1win, medido nos crus de 12/11).
Qualquer divergência PULA o código. Só o `resultado` muda; a escrita é a da grade
(`repository.atualizar_bilhete`: extraction_state, assinatura e `correcoes`), com
`rastro='script_s453'`.

    python scripts/liquidar_presas_conta_errada_s453.py            # ensaio, nada escrito
    python scripts/liquidar_presas_conta_errada_s453.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

DONO = "Feca"
CASA = "1win"
CONTA_CERTA = "Ellen [Eu]"
CONTA_ERRADA = "Feca [Eu]"
RASTRO = "script_s453"
# código → (resultado, stake, odd), como a Ficha derivou do cru liquidado (snapshot da lixeira)
ALVOS = {
    "391795485": ("W", "278,41", "4,31"),
    "391795006": ("L", "278,41", "6,54"),
    "391794301": ("L", "278,41", "4,22"),
    "391792399": ("L", "278,41", "4,32"),
}


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
    planos = []
    async with pool.acquire() as conn:
        for cod, (res, stake, odd) in ALVOS.items():
            linhas = await conn.fetch(
                "SELECT id, resultado, extraction_state, stake, odd FROM bilhetes "
                "WHERE dono = $1 AND casa = $2 AND parceiro = $3 AND codigo_bilhete = $4",
                DONO, CASA, CONTA_CERTA, cod)
            if len(linhas) != 1:
                print(f"{cod}: {len(linhas)} linha(s) na {CONTA_CERTA}, esperava 1 — PULADO")
                continue
            r = linhas[0]
            if r["extraction_state"] != "aberta" or (r["resultado"] or "").strip():
                print(f"{cod}: já não está aberta ({r['resultado']!r}, {r['extraction_state']}) — PULADO")
                continue
            if (r["stake"], r["odd"]) != (stake, odd):
                print(f"{cod}: stake/odd na linha {r['stake']} @ {r['odd']} ≠ {stake} @ {odd} — PULADO")
                continue
            lix = await conn.fetchrow(
                "SELECT bilhete->>'resultado' AS res, bilhete->>'stake' AS stake, "
                "bilhete->>'odd' AS odd FROM lixeira_bilhetes WHERE dono = $1 "
                "AND bilhete->>'casa' = $2 AND bilhete->>'parceiro' = $3 "
                "AND bilhete->>'codigo_bilhete' = $4 ORDER BY id DESC LIMIT 1",
                DONO, CASA, CONTA_ERRADA, cod)
            if lix is None or (lix["res"], lix["stake"], lix["odd"]) != (res, stake, odd):
                print(f"{cod}: snapshot da lixeira não confirma ({dict(lix) if lix else None}) — PULADO")
                continue
            cru = await conn.fetchval(
                "SELECT cru FROM captura_crua WHERE dono = $1 AND upper(casa) = '1WIN' "
                "AND parceiro = $2 AND codigo = $3 AND recebido_em >= '2026-11-13' "
                "ORDER BY recebido_em DESC LIMIT 1", DONO, CONTA_ERRADA, cod)
            cru = json.loads(cru) if isinstance(cru, str) else cru
            status = _status(cru)
            if status in (None, 0):
                print(f"{cod}: cru da conta errada não mostra liquidada (status {status}) — PULADO")
                continue
            print(f"{cod} (id {r['id']}): aberta → {res}  ({stake} @ {odd}; lixeira {lix['res']}, "
                  f"cru status {status})")
            planos.append((r["id"], res))
    if not aplicar:
        print(f"\nENSAIO: {len(planos)} de {len(ALVOS)} linha(s) seriam liquidadas. Nada escrito "
              f"(use --aplicar).")
        return
    n = 0
    for bid, res in planos:
        if await atualizar_bilhete(bid, {"resultado": res}, DONO, rastro=RASTRO):
            n += 1
        else:
            print(f"id {bid}: atualizar_bilhete recusou")
    print(f"\nAPLICADO: {n} de {len(planos)} linha(s).")


def _status(cru):
    """O `status` numérico do bilhete da 1win, onde quer que ele esteja no topo do cru."""
    if not isinstance(cru, dict):
        return None
    for v in [cru, *[x for x in cru.values() if isinstance(x, dict)]]:
        if isinstance(v.get("status"), int):
            return v["status"]
    return None


if __name__ == "__main__":
    asyncio.run(main())
