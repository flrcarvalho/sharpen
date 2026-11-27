"""Corrige a múltipla da Vem com Sorte do Gabriel que a IA gravou V (s468, 27/11/2026).

Por quê: o bilhete 6442644 (conta `gfatuch [Fatuch]`, R$ 300, 3 pernas) ganhou com uma perna
anulada. A casa pagou R$ 969,00 = 300 × 1,90 × 1,70 (a perna de 1,80 saiu da conta, e o boost
junto). O adaptador `vcs` da s467 só aceitava ganha com TODA perna WIN, recusou, o bilhete foi
à IA com "a conferir — não liquidar automaticamente" e a IA gravou V @ 5,95842. P/L 0 no lugar
de +669,00: o tester viu a conta em +259,59 e a casa em +928,59.

O valor certo NÃO é escrito à mão: sai do cru gravado (`captura_crua`, o mais novo do código)
passado pelo adaptador CORRIGIDO e pela `ficha.derivar` — a mesma régua que a próxima captura
usaria. Antes de escrever, confere (qualquer falha e nada é escrito):
  • exatamente uma linha do código na conta, do dono, e ela ainda está V @ 5,95842, stake 300;
  • nenhuma edição humana de `resultado`/`odd` nela (correção humana manda);
  • a Ficha do cru deriva W, stake 300, e o retorno fecha stake × odd no centavo.
A escrita passa por `atualizar_bilhete` (assinatura recalculada, `correcoes` com `script_s468`).

    python scripts/corrigir_vcs_perna_anulada_s468.py            # ensaio (conexão só-leitura)
    python scripts/corrigir_vcs_perna_anulada_s468.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import asyncpg  # noqa: E402

import ficha  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

DONO, CASA, CASA_KEY, PARCEIRO = "Gabriel", "Vem com Sorte", "VEMCOMSORTE", "gfatuch [Fatuch]"
CODIGO = "6442644"
ANTES = {"resultado": "V", "odd": "5,95842", "stake": 300}
RASTRO = "script_s468"


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _dec_br(v) -> Decimal:
    return Decimal(str(v).replace(".", "").replace(",", ".")) if "," in str(v) else Decimal(str(v))


async def _planejar(conn) -> tuple[dict | None, list[str]]:
    erros: list[str] = []
    linhas = await conn.fetch(
        "SELECT id, resultado, odd, stake, extraction_state FROM bilhetes "
        "WHERE dono = $1 AND casa = $2 AND parceiro = $3 AND codigo_bilhete = $4",
        DONO, CASA, PARCEIRO, CODIGO)
    if len(linhas) != 1:
        return None, [f"{len(linhas)} linha(s) com o código {CODIGO} (esperava 1)"]
    b = linhas[0]
    if (b["resultado"] or "") != ANTES["resultado"] or (b["odd"] or "") != ANTES["odd"] \
            or _dec_br(b["stake"]) != ANTES["stake"]:
        erros.append(f"a linha mudou desde a medição: {dict(b)}")
    humanas = await conn.fetchval(
        "SELECT count(*) FROM correcoes WHERE bilhete_id = $1 AND campo IN ('resultado', 'odd') "
        "AND origem IS NULL", b["id"])
    if humanas:
        erros.append(f"{humanas} edição(ões) humana(s) de resultado/odd: a mão do dono manda")
    cru = await conn.fetchval(
        "SELECT cru FROM captura_crua WHERE dono = $1 AND casa = $2 AND parceiro = $3 "
        "AND codigo = $4 ORDER BY id DESC LIMIT 1", DONO, CASA_KEY, PARCEIRO, CODIGO)
    if cru is None:
        return None, erros + ["sem cru gravado do código"]
    cru = json.loads(cru) if isinstance(cru, str) else cru
    f, motivos = ficha.montar_ficha("vcs", cru, CASA_KEY)
    if motivos:
        return None, erros + [f"a Ficha ainda recusa: {motivos}"]
    d = ficha.derivar(f)
    stake, odd, retorno = _dec_br(d["stake"]), _dec_br(d["odd"]), Decimal(f["retorno"])
    if d["resultado"] != "W" or stake != ANTES["stake"]:
        erros.append(f"a Ficha derivou {d}")
    if abs(stake * odd - retorno) > Decimal("0.01"):
        erros.append(f"stake {stake} × odd {odd} não fecha o retorno {retorno}")
    return {"id": b["id"], "antes": dict(b), "novo": {"resultado": "W", "odd": d["odd"]},
            "retorno": str(retorno), "pl": str(retorno - stake), "fonte_odd": d["fonte_odd"]}, erros


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], timeout=30,
                                 server_settings={"default_transaction_read_only": "on"})
    try:
        plano, erros = await _planejar(conn)
    finally:
        await conn.close()
    print(json.dumps(plano, ensure_ascii=False, default=str, indent=1))
    if erros or plano is None:
        print("NADA ESCRITO:\n  " + "\n  ".join(erros))
        return
    if "--aplicar" not in sys.argv:
        print("ENSAIO: nada escrito (use --aplicar).")
        return
    ok = await atualizar_bilhete(plano["id"], plano["novo"], DONO, rastro=RASTRO)
    print("gravado" if ok else "atualizar_bilhete RECUSOU")


if __name__ == "__main__":
    asyncio.run(main())
