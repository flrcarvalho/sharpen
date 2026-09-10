"""Fase 2 do `docs/PLANO_TRADUTOR_DETERMINISTICO.md` — o relatório de divergência.

Roda o tradutor determinístico contra o que a sombra (`sombra_rotulos`) já gravou e
compara, campo a campo, com o que a IA decidiu para a MESMA entrada. Leitura pura: não
escreve nada, não chama a API, não toca no caminho de extração.

    python scripts/diff_tradutor.py [CASA] [--exemplos N]

TRÊS MÉTRICAS, e a ordem de importância mudou na s336:

  • **Cobertura** = quantos bilhetes o tradutor aceitou traduzir. O resto foi para o
    fallback de propósito, e fallback custa dinheiro, não erro.
  • **Conformidade com o MASTER** = o GATE QUE VALE. Mede os dois lados com a mesma
    régua (`checar_descricao`), e é ela que autoriza a virada da Fase 3.
  • **Divergência contra a IA** = distância até o que a IA escreveu. Continua no
    relatório porque é útil para achar rótulo mal mapeado, **mas não é gate.**

⚠️ **O gate original deste arquivo estava errado, e o erro era estrutural.** Ele cobrava
"< 1% de divergência contra a IA". Medido na s336 sobre 8.255 releituras: **em 76,7%
delas a IA descreveu de forma DIFERENTE algo que ela mesma já tinha descrito** — no maior
mercado da base (`Gols + -`) a mesma seleção saiu de doze jeitos. O teto de acerto de
qualquer tradutor determinístico contra esse juiz é **~23%**. Ninguém casa com um alvo
que se mexe, e quem usar aquele número para decidir vai adiar para sempre uma virada que
já está pronta.

A prova de que o juiz é o problema está no próprio relatório: quando as decisões A e B do
`BACKLOG §3.8` fecharam, a divergência contra a IA **subiu** (o tradutor passou a emitir
`Over 2.25` e a IA continua nos doze formatos) enquanto a conformidade com o MASTER foi a
**100%**. As duas linhas se movendo em direções opostas é o teste de qual delas mede
qualidade.

Cobertura baixa com conformidade alta é um tradutor tímido — seguro e caro. Cobertura
alta com conformidade baixa é o modo de falha que este projeto existe para não ter.
"""
from __future__ import annotations

import asyncio
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg  # noqa: E402

from app.tradutor import traduzir  # noqa: E402
from app.descricao_check import checar_descricao  # noqa: E402

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

    # ── O GATE CERTO (s336): conformidade com o MASTER, dos DOIS lados ──────────
    #
    # A divergência acima mede distância até a IA, e a IA **não é um alvo**: medido na
    # s336, em 76,7% das releituras ela descreveu de forma diferente algo que ela mesma
    # já tinha descrito. O teto de acerto contra esse juiz é ~23%. Quem usar só o número
    # de cima para decidir a virada vai adiar para sempre uma coisa que já está boa.
    #
    # A régua que vale é o MASTER, e ela se aplica igual aos dois. `checar_descricao`
    # cobra as regras fechadas: Over/Under em inglês (§11), quarto de linha (§10.1.1) e
    # decimal com ponto (§10.1).
    conf = {"IA": [0, 0, Counter()], "tradutor": [0, 0, Counter()]}
    for r in linhas:
        t = traduzir(casa, r["bruto"])
        if not t.ok:
            continue
        for rot, ap, de in (("IA", r["ia_aposta"] or "", r["ia_descricao"] or ""),
                            ("tradutor", t.aposta, t.descricao)):
            if not de.strip():
                continue
            conf[rot][0] += 1
            probs = [p for p in checar_descricao(ap, de) if p[0] == "erro"]
            if probs:
                conf[rot][1] += 1
                for p in probs:
                    conf[rot][2][p[1]] += 1

    print("\n" + "=" * 62)
    print("CONFORMIDADE COM O MASTER — o gate que vale (ver §II.9 do plano)")
    print("=" * 62)
    for rot, (n, ruins, quais) in conf.items():
        if not n:
            continue
        print(f"  {rot:<10} {n-ruins}/{n} conformes = {100*(n-ruins)/n:5.1f}%")
        for regra, q in quais.most_common(5):
            print(f"     {q:>5}x  {regra}")

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
