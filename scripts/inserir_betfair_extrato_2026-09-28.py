"""Repõe na conta Betfair `Duka [Eu]` do Feca as apostas que a casa apagou do site (28/09/2026).

O QUE ACONTECEU
---------------
A Betfair sumiu com o histórico de apostas do site, e a captura parou de achar qualquer
coisa. A última captura boa foi em 21/09 02:59 (ref `O/25146258/0002062`). A única fonte
que sobrou é o extrato `AccountStatement_ (20).csv`.

COMO O EXTRATO FOI LIGADO À BASE
--------------------------------
O extrato identifica a COLOCAÇÃO pelo `Transaction ID S/…` e a LIQUIDAÇÃO pelo
`Bet Ref O/…`, então não há chave comum. Mas o número do `O/25146258/000NNNN` cresce na
ordem de colocação: alinhando as duas sequências, as stakes batem uma a uma contra a base
(1650..2062 sem buraco). Os 13 `Bet Placed` depois do ref 2062 são os refs 2063..2075, e
as liquidações com retorno redondo (2072 = 301 × 2,20; 2074 = 500 × 2,00;
2075 = 83,38 × 2,00) confirmam o alinhamento.

- Liquidada: `W`, odd = Retorno ÷ Stake (MASTER_RESULTADO §7.1), data = da liquidação.
- Sem liquidação: `L` (perda não gera linha no extrato). Decisão do Feca em 28/09/2026:
  odd 2 como valor padrão, porque a odd real não existe em lugar nenhum; data = da
  colocação, porque a de liquidação também não existe. A descrição avisa a odd.
- Descrição `Aposta Betfair #NN`; mercado `Aposta Betfair`, sem número (13 categorias
  diferentes poluiriam o recorte por mercado). Tipster e esporte ficam vazios: o Feca
  preenche pela stake.

AS DUAS QUE JÁ ESTAVAM ERRADAS
------------------------------
2061 e 2062 foram capturadas como `L` às 02:59 de 21/09 e a Betfair pagou as duas às
06:14 (R$ 632,10 e R$ 191,50, esta uma freebet de 50 @ 4,83). Viram `W` pelo
`atualizar_bilhete`, que registra em `correcoes` e recalcula assinatura.

Uso:
    python scripts/inserir_betfair_extrato_2026-09-28.py            # ensaio
    python scripts/inserir_betfair_extrato_2026-09-28.py --aplicar
"""
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

import asyncpg  # noqa: E402
from database import dsn  # noqa: E402
from repository import atualizar_bilhete, upsert_bilhetes, validar_linhas  # noqa: E402

DONO, CASA, PARCEIRO = "Feca", "Betfair", "Duka [Eu]"
PREFIXO = "O/25146258/"
DESTINO = ROOT / "Backups" / "betfair-extrato-2026-09-28" / "bilhetes_antes.json"

# (ref, data, stake, retorno ou None) — lidos do extrato. None = sem liquidação.
APOSTAS = [
    ("0002063", "22/09/2026", "309,00", "589,91"),
    ("0002064", "21/09/2026", "176,00", None),
    ("0002065", "22/09/2026", "304,00", None),
    ("0002066", "22/09/2026", "56,00", None),
    ("0002067", "23/09/2026", "156,00", None),
    ("0002068", "23/09/2026", "500,00", None),
    ("0002069", "24/09/2026", "206,00", None),
    ("0002070", "24/09/2026", "206,00", None),
    ("0002071", "28/09/2026", "202,00", "479,75"),
    ("0002072", "24/09/2026", "301,00", "662,20"),
    ("0002073", "24/09/2026", "286,00", None),
    ("0002074", "25/09/2026", "500,00", "1000,00"),
    ("0002075", "26/09/2026", "83,38", "166,76"),
]
# (ref, retorno do extrato) das linhas gravadas L que a Betfair pagou.
VIRAR_W = [("0002061", "632,10"), ("0002062", "191,50")]
ODD_PADRAO_PERDA = "2"


def _f(s: str) -> float:
    return float(s.replace(",", "."))


def _odd(stake: str, retorno: str) -> str:
    odd = _f(retorno) / _f(stake)
    txt = f"{odd:.10f}".rstrip("0").rstrip(".")
    return txt.replace(".", ",")


def montar_linhas() -> list[dict]:
    rows = []
    for n, (ref, data, stake, retorno) in enumerate(APOSTAS, start=1):
        rotulo = f"Aposta Betfair #{n:02d}"
        rows.append({
            "data": data, "esporte": "", "tipster": "", "casa": CASA, "parceiro": PARCEIRO,
            "aposta": "Aposta Betfair",
            "descricao": rotulo if retorno else f"{rotulo} (odd desconhecida)",
            "stake": stake,
            "odd": _odd(stake, retorno) if retorno else ODD_PADRAO_PERDA,
            "resultado": "W" if retorno else "L",
            "codigo_bilhete": PREFIXO + ref,
        })
    return rows


async def main(aplicar: bool) -> None:
    rows = montar_linhas()
    boas, rejeitadas = validar_linhas(rows)
    if rejeitadas:
        sys.exit(f"validar_linhas recusou: {rejeitadas}")

    conn = await asyncpg.connect(dsn())
    codigos = [r["codigo_bilhete"] for r in rows]
    ja = await conn.fetch(
        "SELECT codigo_bilhete FROM bilhetes WHERE dono=$1 AND casa=$2 AND parceiro=$3 "
        "AND codigo_bilhete = ANY($4::text[])", DONO, CASA, PARCEIRO, codigos)
    if ja:
        sys.exit(f"já existem na base, nada gravado: {[r['codigo_bilhete'] for r in ja]}")

    alvo = await conn.fetch(
        "SELECT id, codigo_bilhete, to_jsonb(b.*) AS snap, stake, odd, resultado "
        "FROM bilhetes b WHERE dono=$1 AND casa=$2 AND parceiro=$3 "
        "AND codigo_bilhete = ANY($4::text[])",
        DONO, CASA, PARCEIRO, [PREFIXO + r for r, _ in VIRAR_W])
    await conn.close()
    por_cod = {r["codigo_bilhete"]: r for r in alvo}
    for ref, retorno in VIRAR_W:
        r = por_cod.get(PREFIXO + ref)
        if not r or r["resultado"] != "L":
            sys.exit(f"{ref}: esperado L na base, achei {r and r['resultado']}")
        pl = _f(r["stake"]) * (_f(r["odd"]) - 1)
        # freebet (2062) não devolve a stake: o extrato paga só o lucro
        if abs(pl - _f(retorno)) > 0.01 and abs(pl + _f(r["stake"]) - _f(retorno)) > 0.01:
            sys.exit(f"{ref}: retorno {retorno} não fecha com {r['stake']} @ {r['odd']}")

    print(f"{'código':<20} {'data':<11} {'stake':>8} {'odd':>12} res  descrição")
    for r in rows:
        print(f"{r['codigo_bilhete']:<20} {r['data']:<11} {r['stake']:>8} {r['odd']:>12} "
              f"{r['resultado']:<4} {r['descricao']}")
    for ref, _ in VIRAR_W:
        print(f"corrigir {PREFIXO + ref}: L -> W (id {por_cod[PREFIXO + ref]['id']})")

    if not aplicar:
        print("\nensaio: nada gravado. Rode com --aplicar.")
        return

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps([json.loads(r["snap"]) for r in alvo],
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    relido = json.loads(DESTINO.read_text(encoding="utf-8"))
    if len(relido) != len(VIRAR_W):
        sys.exit("backup relido não confere")

    ins, atu, ids, alertas, _dup = await upsert_bilhetes(boas, DONO, origem="manual")
    print(f"\ninseridos={ins} atualizados={atu} ids={ids}")
    for a in alertas:
        print("alerta:", a)
    if ins != len(rows):
        print(f"ATENÇÃO: mandei {len(rows)}, entraram {ins}")

    for ref, _ in VIRAR_W:
        ok = await atualizar_bilhete(por_cod[PREFIXO + ref]["id"], {"resultado": "W"}, DONO)
        print(f"{ref} -> W: {'ok' if ok else 'FALHOU'}")


if __name__ == "__main__":
    asyncio.run(main("--aplicar" in sys.argv))
