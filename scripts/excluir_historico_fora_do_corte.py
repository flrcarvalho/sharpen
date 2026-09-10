# -*- coding: utf-8 -*-
"""Move para a lixeira o histórico anterior ao corte declarado da casa (s344).

CONTEXTO. Casa que exporta o histórico inteiro traz junto o que o dono não quer na base.
Na Betbra (s343) a 1ª captura gravou 411 bilhetes de uma vez, 298 deles de 01/06/2025 a
31/10/2025 — e a Betbra é a única casa daquele dono com bilhete de 2025, toda a base dele
começa em 2026.

⚠️ **Rode este script só DEPOIS de o corte estar no ar.** A régua vive em
`main._CORTE_HISTORICO` e é lida daqui, então este script não inventa data nenhuma: ele
apaga exatamente o que o `/extrair` passou a recusar. Sem o corte em produção, a captura
seguinte reencontra os mesmos códigos e regrava tudo — exclusão que dura até a próxima
varredura. É por isso que o par (corte, exclusão) anda junto e nesta ordem.

Exclusão é MOVIMENTO, nunca soft-delete (`CLAUDE.md`): o `DELETE … RETURNING to_jsonb(b.*)`
é uma operação só (ler antes e apagar depois abre janela para gravar uma lixeira que não
corresponde ao que saiu) e o snapshot vai inteiro, em JSONB, para `lixeira_bilhetes`.

A DATA. `bilhetes.data` guarda `DD/MM/YYYY` e ISO na MESMA coluna, e o filtro precisa dos
dois ramos: ler só um deles acha quase nada e dá um ensaio tranquilizador que não
corresponde ao que existe. Linha sem data legível **fica** — mesmo fail-open do corte.

USO (ensaio é o padrão — só mexe no banco com --aplicar):
    python scripts/excluir_historico_fora_do_corte.py
    python scripts/excluir_historico_fora_do_corte.py --dono Feca --casa Betbra
    python scripts/excluir_historico_fora_do_corte.py --dono Feca --casa Betbra --aplicar
"""
import argparse
import asyncio
import json
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from main import _CORTE_HISTORICO  # noqa: E402  (a régua tem UMA fonte)
from repository import calcular_pl  # noqa: E402

# O console do Windows abre em cp1252 e derruba o script no primeiro caractere fora da
# tabela — erro de ENCODING mascarado de erro de medição.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip()
    print("DATABASE_URL ausente (nem no ambiente nem no .env).", file=sys.stderr)
    raise SystemExit(2)


def _data_da_linha(txt: str | None) -> date | None:
    """`DD/MM/YYYY` ou ISO → date. `None` quando não dá para ler (a linha FICA)."""
    s = (txt or "").strip()[:10]
    if len(s) != 10:
        return None
    try:
        if s[2] == "/" and s[5] == "/":
            return date(int(s[6:]), int(s[3:5]), int(s[:2]))
        if s[4] == "-" and s[7] == "-":
            return date(int(s[:4]), int(s[5:7]), int(s[8:]))
    except (ValueError, IndexError):
        return None
    return None


def _num(v) -> float:
    try:
        return float(str(v).replace(".", "").replace(",", ".")) if v not in (None, "") else 0.0
    except (TypeError, ValueError):
        return 0.0


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dono", help="limita a um dono (default: todos os pares declarados)")
    ap.add_argument("--casa", help="limita a uma casa")
    ap.add_argument("--aplicar", action="store_true",
                    help="move de verdade; sem isto é só ensaio")
    args = ap.parse_args()

    pares = [(d, c, corte) for (d, c), corte in _CORTE_HISTORICO.items()
             if (not args.dono or d == args.dono.strip().lower())
             and (not args.casa or c == args.casa.strip().lower())]
    if not pares:
        print("Nenhum par (dono, casa) com corte declarado bate com o filtro.")
        print("A régua vive em `main._CORTE_HISTORICO` — declare lá antes de apagar aqui.")
        return 1

    conn = await asyncpg.connect(_database_url())
    try:
        total_alvo = 0
        por_par: list[tuple[str, str, date, list]] = []

        for dono_k, casa_k, corte in pares:
            linhas = await conn.fetch(
                """SELECT id, dono, casa, data, parceiro, codigo_bilhete, stake, odd,
                          resultado, extraction_state, origem, descricao
                     FROM bilhetes
                    WHERE lower(dono) = $1 AND lower(casa) = $2
                 ORDER BY data""", dono_k, casa_k)
            alvo = [r for r in linhas
                    if (d := _data_da_linha(r["data"])) is not None and d < corte]
            por_par.append((dono_k, casa_k, corte, alvo))
            total_alvo += len(alvo)

            print(f"\n── {dono_k}/{casa_k} · corte {corte.strftime('%d/%m/%Y')} ──────────────")
            print(f"   {len(linhas)} linha(s) na casa · {len(alvo)} anterior(es) ao corte")
            if not alvo:
                continue

            sem_data = sum(1 for r in linhas if _data_da_linha(r["data"]) is None)
            if sem_data:
                print(f"   {sem_data} linha(s) sem data legível FICAM (fail-open).")

            anos = Counter((_data_da_linha(r["data"]) or corte).year for r in alvo)
            print("   por ano: " + " · ".join(f"{a}: {n}" for a, n in sorted(anos.items())))

            estados = Counter(r["extraction_state"] or "?" for r in alvo)
            print("   por estado: " + " · ".join(f"{e}: {n}" for e, n in estados.most_common()))

            pl = sum(calcular_pl(_num(r["stake"]), _num(r["odd"]), r["resultado"]) or 0
                     for r in alvo)
            turnover = sum(_num(r["stake"]) for r in alvo)
            print(f"   sai da base: turnover R$ {turnover:,.2f} · P/L R$ {pl:,.2f}"
                  .replace(",", "~").replace(".", ",").replace("~", "."))

            print("   amostra (5 primeiras):")
            for r in alvo[:5]:
                print(f"     #{r['id']} · {r['data']} · {r['parceiro']} · "
                      f"cod {r['codigo_bilhete']} · {r['resultado'] or '(aberta)'} · "
                      f"{(r['descricao'] or '')[:48]}")

        if not total_alvo:
            print("\nNada a mover.")
            return 0

        if not args.aplicar:
            print(f"\nENSAIO: {total_alvo} linha(s) seriam movidas para `lixeira_bilhetes`.")
            print("Confira a amostra acima e rode de novo com --aplicar.")
            return 0

        movidas = 0
        for dono_k, casa_k, corte, alvo in por_par:
            if not alvo:
                continue
            motivo = (f"histórico anterior ao corte da casa "
                      f"({casa_k} · {corte.strftime('%d/%m/%Y')} · s344)")
            async with conn.transaction():
                for r in alvo:
                    snap = await conn.fetchval(
                        "DELETE FROM bilhetes WHERE id = $1 RETURNING to_jsonb(bilhetes.*)",
                        r["id"])
                    if snap is None:            # já saiu por outro caminho
                        continue
                    await conn.execute(
                        """INSERT INTO lixeira_bilhetes (dono, motivo, mantido_id, bilhete)
                           VALUES ($1, $2, NULL, $3::jsonb)""",
                        json.loads(snap)["dono"], motivo, snap)
                    movidas += 1

        print(f"\n{movidas} linha(s) movida(s) para `lixeira_bilhetes`.")
        print("O snapshot é JSONB e nada mais no sistema lê essa tabela — voltar é decisão "
              "humana, por script.")
        print("A captura seguinte NÃO as traz de volta: o corte no `/extrair` descarta os "
              "mesmos blocos antes da IA. Se voltarem, o corte não está no ar.")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
