"""Fase 2 do `docs/PLANO_TRADUTOR_DETERMINISTICO.md` — o relatório de divergência.

Roda o tradutor determinístico contra o que a sombra (`sombra_rotulos`) já gravou e
compara, campo a campo, com o que a IA decidiu para a MESMA entrada. Leitura pura: não
escreve nada, não chama a API, não toca no caminho de extração.

    python scripts/diff_tradutor.py [CASA] [--exemplos N]

DUAS MÉTRICAS, e confundir as duas é o jeito fácil de se enganar aqui:

  • **Cobertura** = quantos bilhetes o tradutor aceitou traduzir. O resto foi para o
    fallback de propósito, e fallback custa dinheiro, não erro.
  • **Divergência** = dos que ele traduziu, em quantos ele discorda da IA. É esta que o
    gate da Fase 3 cobra (< 1% em >= 500 bilhetes, medida por campo).

Cobertura baixa com divergência zero é um tradutor tímido — seguro e caro. Cobertura alta
com divergência alta é o modo de falha que este projeto existe para não ter.

⚠️ **Divergir da IA não é errar.** A IA é a referência disponível, não a verdade: a
sombra já flagrou ela descrevendo a MESMA perna de dois jeitos no mesmo dia. Cada
divergência é para ler à mão e classificar em erro do tradutor, erro da IA ou empate
legítimo — nunca somar como se fosse defeito nosso.
"""
from __future__ import annotations

import asyncio
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg  # noqa: E402

from app.tradutor import traduzir  # noqa: E402

CAMPOS = ("esporte", "aposta", "descricao")


def _dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise SystemExit("DATABASE_URL ausente. Rode com o .env do projeto carregado.")
    return url.replace("postgres://", "postgresql://", 1)


async def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    casa = args[0] if args else "Bet365"
    n_ex = 6
    for a in sys.argv[1:]:
        if a.startswith("--exemplos"):
            n_ex = int(a.split("=")[1]) if "=" in a else 6

    conn = await asyncpg.connect(_dsn())
    linhas = await conn.fetch(
        """SELECT codigo, bruto, ia_esporte, ia_aposta, ia_descricao
           FROM sombra_rotulos WHERE casa = $1 ORDER BY criado_em""", casa)
    await conn.close()

    if not linhas:
        raise SystemExit(f"Sombra vazia para {casa!r}.")

    motivos: Counter = Counter()
    divergencias: Counter = Counter()
    exemplos: dict = {c: [] for c in CAMPOS}
    ok = iguais = 0

    for r in linhas:
        t = traduzir(casa, r["bruto"])
        if not t.ok:
            # O motivo carrega o rótulo cru; agrupamos pelo prefixo para o relatório
            # não virar uma lista de mil linhas únicas.
            motivos[t.motivo.split(":")[0]] += 1
            motivos[t.motivo] += 0  # mantém o detalhe disponível abaixo
            continue
        ok += 1
        ia = {"esporte": r["ia_esporte"] or "", "aposta": r["ia_aposta"] or "",
              "descricao": r["ia_descricao"] or ""}
        nosso = {"esporte": t.esporte, "aposta": t.aposta, "descricao": t.descricao}
        bateu = True
        for c in CAMPOS:
            if nosso[c].strip() != ia[c].strip():
                bateu = False
                divergencias[c] += 1
                if len(exemplos[c]) < n_ex:
                    exemplos[c].append((r["codigo"], ia[c], nosso[c]))
        iguais += bateu

    total = len(linhas)
    print(f"=== {casa} · {total} bilhetes na sombra ===\n")
    print(f"Cobertura   : {ok}/{total} = {100*ok/total:.1f}% traduzidos "
          f"({total-ok} para a IA)")
    if ok:
        print(f"Bateu tudo  : {iguais}/{ok} = {100*iguais/ok:.1f}% dos traduzidos\n")
        print("Divergência por campo (dos traduzidos):")
        for c in CAMPOS:
            d = divergencias[c]
            print(f"  {c:<11}{d:>5}  {100*d/ok:>6.1f}%")

    print("\nPor que caiu no fallback:")
    for motivo, n in motivos.most_common(12):
        if n:
            print(f"  {n:>4}x  {motivo}")

    for c in CAMPOS:
        if not exemplos[c]:
            continue
        print(f"\n--- exemplos de divergência em {c} ---")
        for cod, ia_v, nosso_v in exemplos[c]:
            print(f"  [{cod}]\n    IA    : {ia_v}\n    nosso : {nosso_v}")


if __name__ == "__main__":
    asyncio.run(main())
