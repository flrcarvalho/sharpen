"""Relatório da sombra de NÚMEROS (s407). SÓ LEITURA.

Responde à pergunta do Feca: *"se eu trocar o Sonnet pelo Haiku, o que vai para o banco
continua certo?"* Critério dele: stake, odd e resultado 100% iguais; descrição não conta.

Para cada casa e no total, desde uma data:
  • apostas comparadas e % com stake / odd / resultado idênticos, e % com OS TRÊS;
  • apostas que o candidato não devolveu, que só ele devolveu, códigos inventados,
    linhas sem código (não pareáveis) e repescagens que a cobertura teria feito;
  • custo do candidato × custo do titular NAS MESMAS extrações;
  • a lista das divergências de número, com a marca de qual fiscal mexeu.

"Igual" é depois dos MESMOS fiscais determinísticos dos dois lados (`candidato final ×
titular final`). Os brutos aparecem na lista só para dizer quem errou e quem salvou.

O QUE ELE NÃO DIZ:
  • Linha sem código não é comparada (não há chave). Ela aparece contada, e um volume
    alto dela numa casa quer dizer que a resposta para aquela casa está incompleta.
  • O custo do titular vem em duas réguas: `base` (só a leitura principal) e `total`
    (com a repescagem de cobertura e fidelidade). A sombra não repesca; trocar de
    modelo traria a repescagem junto, então o custo real do candidato fica entre o dele
    e o dele mais a repescagem.

Uso:
    python scripts/relatorio_sombra_numeros.py --desde 2026-10-12
    python scripts/relatorio_sombra_numeros.py --desde 2026-10-12 --casa Bet365 --limite 200
"""
import argparse
import asyncio
import os
import sys
from collections import defaultdict
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
os.environ.setdefault("SESSION_SECRET", "relatorio-sombra-numeros")

import asyncpg  # noqa: E402

import sombra_numeros  # noqa: E402

CAMPOS = (("stake", "stake"), ("odd", "odd"), ("res", "resultado"))

_SQL_NUMEROS = """
    SELECT n.*, t.modelo, t.modelo_titular
      FROM sombra_numeros n
      JOIN sombra_tsv t USING (extracao_id)
     WHERE n.criado_em >= $1 AND ($2::text IS NULL OR n.casa = $2)
     ORDER BY n.criado_em, n.id
"""
_SQL_TSV = """
    SELECT extracao_id, dono, casa, modelo, modelo_titular, titular_final, candidato_final,
           titular_custo_base, titular_custo_total, candidato_custo, candidato_stop,
           candidato_repescaria, titular_continuou
      FROM sombra_tsv
     WHERE criado_em >= $1 AND ($2::text IS NULL OR casa = $2)
"""


def _pct(n: int, d: int) -> str:
    return "—" if not d else f"{100 * n / d:.2f}".replace(".", ",") + "%"


def _usd(v: float) -> str:
    return f"US$ {v:.4f}".replace(".", ",")


def _num_br(v: str | None) -> str | None:
    """Só para LER: o valor gravado é o canônico (`1.85`); a tela de quem lê é BR."""
    return v if v is None or v.startswith("!") or not v[:1].replace("-", "").isdigit()         else v.replace(".", ",")


def _vazio():
    return {"extracoes": 0, "comparadas": 0, "stake": 0, "odd": 0, "res": 0, "tres": 0,
            "faltou": 0, "sobrou": 0, "inventado": 0, "sem_chave_t": 0, "sem_chave_c": 0,
            "repescaria": 0, "recusas": 0, "continuou": 0,
            "custo_c": 0.0, "custo_tb": 0.0, "custo_tt": 0.0}


async def main(desde: date, casa: str | None, limite: int) -> None:
    # `criado_em` é TIMESTAMPTZ e o asyncpg não converte: `date` levantaria dentro do
    # driver. Meia-noite de Brasília, que é o "dia" de quem lê o relatório.
    inicio = datetime.combine(desde, time.min, tzinfo=ZoneInfo("America/Sao_Paulo"))
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        async with conn.transaction(readonly=True):
            numeros = await conn.fetch(_SQL_NUMEROS, inicio, casa)
            tsvs = await conn.fetch(_SQL_TSV, inicio, casa)
    finally:
        await conn.close()

    por_casa = defaultdict(_vazio)
    modelos = set()
    for t in tsvs:
        modelos.add((t["modelo"], t["modelo_titular"]))
        for k in (t["casa"] or "?", "TOTAL"):
            a = por_casa[k]
            a["extracoes"] += 1
            a["repescaria"] += t["candidato_repescaria"]
            a["recusas"] += int("refusal" in (t["candidato_stop"] or ""))
            a["continuou"] += int(t["titular_continuou"])
            a["custo_c"] += t["candidato_custo"]
            a["custo_tb"] += t["titular_custo_base"]
            a["custo_tt"] += t["titular_custo_total"]
            # Linha sem código não foi gravada em `sombra_numeros` (não tem chave): conta
            # aqui, relendo os TSVs guardados pela MESMA função que compara.
            r = sombra_numeros.comparar(None, t["titular_final"], None, t["candidato_final"], None)
            a["sem_chave_t"] += r["resumo"]["sem_chave_titular"]
            a["sem_chave_c"] += r["resumo"]["sem_chave_candidato"]

    divergencias = []
    for n in numeros:
        par = not (n["faltou"] or n["sobrou"] or n["inventado"])
        for k in (n["casa"] or "?", "TOTAL"):
            a = por_casa[k]
            a["faltou"] += n["faltou"]
            a["sobrou"] += n["sobrou"]
            a["inventado"] += n["inventado"]
            if par:
                a["comparadas"] += 1
                a["stake"] += bool(n["igual_stake"])
                a["odd"] += bool(n["igual_odd"])
                a["res"] += bool(n["igual_res"])
                a["tres"] += bool(n["igual_stake"] and n["igual_odd"] and n["igual_res"])
        if not par:
            continue
        for c, nome in CAMPOS:
            if n[f"igual_{c}"]:
                continue
            mexeu = []
            for quem, b, f in (("titular", n[f"{c}_tb"], n[f"{c}_tf"]),
                               ("candidato", n[f"{c}_cb"], n[f"{c}_cf"])):
                if b is None and f is not None:
                    # O bruto não tinha a aposta com ESTE código: foi o fiscal de código
                    # (fantasma/órfã) que a trouxe, não um fiscal de número.
                    mexeu.append(f"{quem} (código)")
                elif b != f:
                    mexeu.append(quem)
            divergencias.append((n["criado_em"], n["dono"], n["casa"], n["codigo"], nome,
                                 _num_br(n[f"{c}_tf"]), _num_br(n[f"{c}_cf"]),
                                 ", ".join(mexeu) or "nenhum"))

    print(f"Sombra de números desde {desde.isoformat()}" + (f" · casa {casa}" if casa else ""))
    for m, t in sorted(modelos, key=str):
        print(f"  candidato {m} × titular {t}")
    if not tsvs:
        print("\nNenhuma extração gravada no período.")
        return

    print()
    cab = ("casa", "extr", "comparadas", "stake", "odd", "result", "OS TRÊS", "faltou",
           "sobrou", "invent", "s/cód T/C", "repesc", "recusa", "custo cand", "titular base",
           "cand/base", "titular total")
    print(" | ".join(cab))
    chaves = sorted(k for k in por_casa if k != "TOTAL") + ["TOTAL"]
    for k in chaves:
        a = por_casa[k]
        print(" | ".join(str(x) for x in (
            k, a["extracoes"], a["comparadas"],
            _pct(a["stake"], a["comparadas"]), _pct(a["odd"], a["comparadas"]),
            _pct(a["res"], a["comparadas"]), _pct(a["tres"], a["comparadas"]),
            a["faltou"], a["sobrou"], a["inventado"],
            f"{a['sem_chave_t']}/{a['sem_chave_c']}", a["repescaria"], a["recusas"],
            _usd(a["custo_c"]), _usd(a["custo_tb"]),
            _pct(round(a["custo_c"] * 1e6), round(a["custo_tb"] * 1e6)),
            _usd(a["custo_tt"]))))
    tot = por_casa["TOTAL"]
    if tot["continuou"]:
        print(f"\n⚠ {tot['continuou']} extração(ões) sequenciais em que o titular precisou de "
              "continuação e a sombra leu uma vez só: falta ali pode ser corte, não erro.")

    print(f"\nDivergências de número: {len(divergencias)}"
          + (f" (mostrando {limite})" if len(divergencias) > limite else ""))
    if divergencias:
        print("quando | dono | casa | código | campo | titular | candidato | fiscal mexeu em")
        for d in divergencias[:limite]:
            print(" | ".join([d[0].strftime("%d/%m %H:%M")] + [str(x) if x is not None else "∅"
                                                            for x in d[1:]]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--desde", type=date.fromisoformat, required=True)
    ap.add_argument("--casa", default=None)
    ap.add_argument("--limite", type=int, default=100)
    a = ap.parse_args()
    asyncio.run(main(a.desde, a.casa, a.limite))
