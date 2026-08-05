"""Corrige a coluna `esporte` de bilhetes específicos, por id.

Nasceu na s245: dois bilhetes de badminton da Superbet ficaram em `Outro` porque o
texto da casa não traz liga nem esporte e o nome do atleta é de circuito secundário
(ver `MASTER_ESPORTES §7` → Referências auxiliares — Badminton (circuito secundário)).

**Por que um script e não UPDATE na mão:** `atualizar_bilhete` já faz as três coisas
que um UPDATE cru esquece — recalcula a assinatura quando a edição toca o hash,
registra a correção em `correcoes` (trilha de auditoria) e carimba `atualizado_em`.
Aqui a coluna editada é `esporte`, que **não** entra em `_SIG_COLS` (`repository.py`),
então a assinatura não muda e a próxima captura do mesmo bilhete segue deduplicando.

**Não é backfill heurístico.** Recebe ids explícitos, conferidos por um humano — não
sai varrendo a base atrás de "parece badminton". Padrão é RELATÓRIO; só `--aplicar`
escreve.

Uso:
    python scripts/corrigir_esporte_bilhete.py --dono Feca --esporte Badminton --ids 125105,125106
    python scripts/corrigir_esporte_bilhete.py --dono Feca --esporte Badminton --ids 125105,125106 --aplicar
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))

# `database.dsn()` lê da env; fora do Railway o DSN vive no .env da raiz (mesmo
# carregamento do `scripts/limpar_bet365_sem_confirmation.py`).
if not os.environ.get("DATABASE_URL"):
    _env = RAIZ / ".env"
    if _env.exists():
        for _linha in _env.read_text(encoding="utf-8").splitlines():
            if _linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = _linha.split("=", 1)[1].strip().strip('"').strip("'")
                break
if not os.environ.get("DATABASE_URL"):
    sys.exit("DATABASE_URL ausente (env ou .env na raiz do Planilhador).")

# Console do Windows abre em cp1252 e mata o script no primeiro caractere fora da
# tabela (lição da s244: script destrutivo não pode depender da codificação do
# terminal). `errors="replace"` degrada o caractere em vez de abortar.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(errors="replace")
    except Exception:
        pass

import database  # noqa: E402
import repository  # noqa: E402


async def main(dono: str, esporte: str, ids: list[int], aplicar: bool) -> int:
    pool = await repository.get_pool()
    async with pool.acquire() as conn:
        linhas = await conn.fetch(
            """SELECT id, data, casa, parceiro, coalesce(tipster,'') tipster, esporte,
                      aposta, descricao, stake, odd, resultado
                 FROM bilhetes WHERE dono = $1 AND id = ANY($2::int[]) ORDER BY id""",
            dono, ids)

    achados = {r["id"] for r in linhas}
    faltando = [i for i in ids if i not in achados]
    if faltando:
        print(f"[AVISO] ids fora da base do dono {dono}: {faltando}")

    print(f"\n{len(linhas)} bilhete(s) de {dono} — esporte -> {esporte}\n")
    mudam = []
    for r in linhas:
        marca = "=" if r["esporte"] == esporte else "->"
        print(f"  {r['id']:>7} {r['data']} {r['casa']:<10} {r['parceiro'][:24]:<24} "
              f"{r['tipster'][:14]:<14} {r['esporte']:<10} {marca} {esporte:<10} "
              f"{r['aposta']:<12} {r['descricao'][:60]}")
        if r["esporte"] != esporte:
            mudam.append(r["id"])

    if not mudam:
        print("\nNada a fazer: todos já estão no esporte pedido.")
        return 0
    if not aplicar:
        print(f"\nRELATORIO — {len(mudam)} linha(s) mudariam. Rode com --aplicar para gravar.")
        return 0

    ok, falhou = [], []
    for bid in mudam:
        if await repository.atualizar_bilhete(bid, {"esporte": esporte}, dono):
            ok.append(bid)
        else:
            falhou.append(bid)
    print(f"\nAPLICADO: {len(ok)} atualizado(s) {ok}" + (f" · FALHOU {falhou}" if falhou else ""))

    async with pool.acquire() as conn:
        conf = await conn.fetch(
            "SELECT id, esporte FROM bilhetes WHERE dono = $1 AND id = ANY($2::int[]) ORDER BY id",
            dono, mudam)
    print("Conferencia pos-escrita: " + ", ".join(f"{r['id']}={r['esporte']}" for r in conf))
    return 0 if not falhou else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Corrige o esporte de bilhetes por id.")
    p.add_argument("--dono", required=True)
    p.add_argument("--esporte", required=True)
    p.add_argument("--ids", required=True, help="ids separados por virgula")
    p.add_argument("--aplicar", action="store_true", help="sem isto, so relatorio")
    a = p.parse_args()
    ids = [int(x) for x in a.ids.replace(" ", "").split(",") if x]
    try:
        sys.exit(asyncio.run(main(a.dono, a.esporte, ids, a.aplicar)))
    finally:
        pass
