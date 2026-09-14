# -*- coding: utf-8 -*-
"""Remove a linha duplicada nascida de CÓDIGO inventado pela IA e de ÓRFÃ cópia (s356).

POR QUE EXISTE
--------------
O `codigo_bilhete` entra na assinatura, mas quem escreve essa coluna é a IA, copiando o
`[Código: …]` do bloco. Um caractere trocado é um bilhete NOVO para o sistema — e como
o código falso ainda faz `conferir_cobertura` achar que o bilhete verdadeiro não voltou,
a repescagem entrega a segunda linha do par no MESMO lote.

Medido na s356 contra `bloco_visto` e `sombra_rotulos`, que guardam o código que o robô
REALMENTE emitiu: `TQ8770485441I` apareceu nas seis capturas do bilhete e
`TQ8770485441W` em nenhuma. As duas linhas estão no banco, a `…I` resolvida `L` e a
`…W` aberta para sempre — foi o que apareceu na grade da conta marloncezar01.

O `_corrigir_codigos_fantasma` (app/main.py) fecha a torneira. Este script seca o chão:
as 126 linhas que já entraram, em três famílias, todas provadas por conteúdo idêntico
(mesma conta, mesma data, mesma descrição, mesma stake, mesma odd):

  · código que difere só no último caractere (bet365 `F`/`I`/`W`)
  · linha SEM código duplicando linha COM código (órfã)
  · nenhuma das duas com código

O QUE ELE NÃO TOCA, de propósito
--------------------------------
· **Códigos totalmente diferentes, os dois vindos do robô.** São 412 linhas, 166 grupos
  delas na mesma extração: é gente apostando a mesma coisa duas vezes, e a régua de
  dedup está certa em mantê-las (CLAUDE.md: "ID disponível e diferente → sempre INSERT").
· **Repetição vinda da planilha de origem** (`origem='import'` nos dois lados): dado de
  origem, não defeito do sistema.
· **Descrição curta demais** (< 22 caracteres normalizados): "Dupla", "Multipla",
  "Napoli" não provam nada.
· **A conta de demonstração** (`realtrial`), fora por padrão: lá o export anonimizado
  randomiza o código, então limpar o banco sem corrigir o export é enxugar gelo. Use
  `--incluir-demo` se quiser assim mesmo.
· **Grupos cujo resultado DIVERGE entre as linhas.** Aí não é só duplicata, é decisão
  sobre qual leitura vale: saem no relatório com ⚠ e só são removidos com `--manter <id>`.

COMO ESCOLHE QUAL FICA
----------------------
Nesta ordem, e a primeira regra é a que importa:

1. `--manter <id>` manda.
2. A linha cujo código é **comprovadamente real** — existe em `bloco_visto` ou
   `sombra_rotulos` para aquele dono+casa, isto é, o robô o emitiu de fato.
3. A linha que TEM código, contra a que não tem: é ela que dedupa nas capturas
   seguintes; a órfã nunca dedupa, e o bilhete voltaria como linha nova outra vez.
4. A mais ANTIGA. Importa porque o UPSERT congela stake/odd em linha resolvida: o valor
   da linha que fica é o valor que permanece.

Exclusão é MOVIMENTO, nunca soft-delete: `DELETE … RETURNING to_jsonb(b.*)` numa
operação só, e o snapshot vai para `lixeira_bilhetes`.

USO (ensaio é o padrão — só mexe no banco com --aplicar):
    python scripts/reparar_duplicatas_codigo_fantasma.py
    python scripts/reparar_duplicatas_codigo_fantasma.py --dono Feca
    python scripts/reparar_duplicatas_codigo_fantasma.py --dono Feca --aplicar
    python scripts/reparar_duplicatas_codigo_fantasma.py --manter 265341 --aplicar
"""
import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
from repository import calcular_pl  # noqa: E402

# O console do Windows abre em cp1252 e derruba o script no primeiro caractere fora da
# tabela — erro de ENCODING mascarado de erro de medição.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

MOTIVO = "duplicata por código inventado pela IA / órfã cópia (s356)"
DESC_MINIMA = 22          # abaixo disto a descrição não identifica o bilhete
DEMO = "realtrial"        # conta de demonstração: código anonimizado, fora por padrão


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


def _chave_desc(desc: str) -> str:
    """Descrição normalizada. Acento e pontuação saem; NOME e NÚMERO ficam, porque é
    neles que dois bilhetes DIFERENTES se separam (`Under 74,5` × `Under 78,5`)."""
    s = unicodedata.normalize("NFKD", desc or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def _num(v: str | None) -> str:
    """Stake/odd comparáveis: `14` e `14,00` são o mesmo número (régua do `_norm_odd`)."""
    if not v:
        return ""
    try:
        return f"{float(str(v).replace('.', '').replace(',', '.')):.4f}"
    except ValueError:
        return str(v)


def _pl(l) -> float | None:
    return calcular_pl(l["stake"], l["odd"], l["resultado"])


def _familia(grupo: list, reais: set) -> str | None:
    """Qual defeito explica este grupo? None = não é defeito, não tocar."""
    cods = [(l["codigo_bilhete"] or "").strip() for l in grupo]
    com = [c for c in cods if c]
    if {l["origem"] for l in grupo} == {"import"}:
        return None
    if not com:
        return "sem código dos dois lados"
    if len(com) < len(cods):
        return "órfã sem código"
    if len(set(com)) == 1:
        return None                       # mesmo código: o UPSERT já trata
    raizes = {c[:-1] for c in com}
    if len(raizes) == 1 and all(re.fullmatch(r"[A-Z]{2}\d{10}[A-Z]", c) for c in com):
        return "código com o último caractere trocado"
    # Códigos distintos e os DOIS comprovados no texto do robô: apostas de verdade.
    if sum(1 for c in com if c in reais) >= 2:
        return None
    if len(raizes) == 1:
        return None                       # série de importador (`-S1`/`-S2`), não é isto
    return None


def _escolher(grupo: list, reais: set) -> int:
    for criterio in (
        lambda l: (l["codigo_bilhete"] or "").strip() in reais,
        lambda l: bool((l["codigo_bilhete"] or "").strip()),
        lambda l: True,
    ):
        candidatas = [l for l in grupo if criterio(l)]
        if candidatas:
            return candidatas[0]["id"]     # o grupo chega ordenado por criado_em
    return grupo[0]["id"]


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dono", default=None, help="restringe a um dono (ex.: Feca)")
    ap.add_argument("--casa", default=None, help="restringe a uma casa (ex.: Bet365)")
    ap.add_argument("--manter", type=int, action="append", default=[],
                    help="força manter este id (pode repetir); o resto do grupo dele sai")
    ap.add_argument("--incluir-demo", action="store_true",
                    help=f"inclui a conta de demonstração ({DEMO}), fora por padrão")
    ap.add_argument("--aplicar", action="store_true",
                    help="executa; sem isto é ENSAIO e nada no banco muda")
    args = ap.parse_args()

    conn = await asyncpg.connect(_database_url())
    try:
        # Códigos que o robô comprovadamente emitiu. `bloco_visto` guarda TODO código do
        # texto; a sombra só guarda os que a IA acertou — juntas, cobrem o período retido.
        reais: dict[tuple, set] = defaultdict(set)
        for r in await conn.fetch("SELECT dono, casa, codigo FROM bloco_visto"):
            reais[(r["dono"], r["casa"])].add(r["codigo"])
        for r in await conn.fetch("SELECT DISTINCT dono, casa, codigo FROM sombra_rotulos"):
            reais[(r["dono"], r["casa"])].add(r["codigo"])

        filtros, params = [], []
        if args.dono:
            params.append(args.dono)
            filtros.append(f"dono = ${len(params)}")
        if args.casa:
            params.append(args.casa)
            filtros.append(f"casa = ${len(params)}")
        if not args.incluir_demo:
            params.append(DEMO)
            filtros.append(f"dono <> ${len(params)}")
        where = ("WHERE " + " AND ".join(filtros)) if filtros else ""
        linhas = await conn.fetch(
            f"""SELECT id, dono, casa, parceiro, data, esporte, aposta, descricao,
                       stake, odd, resultado, codigo_bilhete, codigo_ocr, origem,
                       extraction_state, archived, criado_em
                  FROM bilhetes {where}
                 ORDER BY criado_em, id""", *params)

        grupos: dict[tuple, list] = defaultdict(list)
        for l in linhas:
            d = _chave_desc(l["descricao"])
            if len(d) < DESC_MINIMA:
                continue
            grupos[(l["dono"], l["casa"], l["parceiro"], l["data"] or "",
                    d, _num(l["stake"]), _num(l["odd"]))].append(l)

        forcados = set(args.manter)
        a_remover: list[tuple[int, int]] = []
        divergentes, pl_total, n_grupos = 0, 0.0, 0
        saida = []
        for k, grupo in sorted(grupos.items()):
            if len(grupo) < 2:
                continue
            fam = _familia(grupo, reais[(k[0], k[1])])
            if not fam:
                continue
            manter_ids = forcados.intersection({l["id"] for l in grupo})
            if len(manter_ids) > 1:
                saida.append(f"\n!! --manter aponta 2+ linhas do mesmo grupo "
                             f"({sorted(manter_ids)}) — grupo PULADO")
                continue
            resolvidas = [l for l in grupo if l["extraction_state"] == "resolvida"]
            diverge = len({l["resultado"] for l in resolvidas}) > 1
            if diverge and not manter_ids:
                divergentes += 1
                saida.append(f"\n⚠ {k[1]} · {k[0]} · {k[2]} · {k[3]} · [{fam}]")
                saida.append(f"  {(grupo[0]['descricao'] or '')[:88]}")
                for l in grupo:
                    saida.append(f"  PULADO  #{l['id']:>7} res={str(l['resultado']):<7} "
                                 f"cod={l['codigo_bilhete']!r} ({l['criado_em']:%d/%m %H:%M})")
                saida.append("  as leituras discordam no RESULTADO — não é só duplicata. "
                             "Escolha com --manter <id>.")
                continue
            escolhido = manter_ids.pop() if manter_ids else _escolher(grupo, reais[(k[0], k[1])])
            n_grupos += 1
            saida.append(f"\n{k[1]} · {k[0]} · {k[2]} · {k[3]} · [{fam}]")
            saida.append(f"  {(grupo[0]['descricao'] or '')[:88]}")
            for l in grupo:
                pl = _pl(l)
                marca = "MANTÉM " if l["id"] == escolhido else "remove "
                real = " (código do robô)" if (l["codigo_bilhete"] or "").strip() in reais[(k[0], k[1])] else ""
                saida.append(
                    f"  {marca}#{l['id']:>7} {l['extraction_state']:<9} res={str(l['resultado'] or '—'):<4} "
                    f"stake={str(l['stake']):>10} P/L={('%.2f' % pl) if pl is not None else '—':>10} "
                    f"cod={l['codigo_bilhete']!r}{real} ({l['criado_em']:%d/%m %H:%M})")
                if l["id"] != escolhido:
                    a_remover.append((l["id"], escolhido))
                    pl_total += pl or 0.0

        print("=" * 78)
        print(f"{n_grupos} grupo(s) de defeito · {len(a_remover)} linha(s) a remover · "
              f"P/L que sai do total: R$ {pl_total:,.2f}")
        if divergentes:
            print(f"{divergentes} grupo(s) PULADO(s) por resultado divergente — precisam de --manter")
        print("=" * 78)
        print("\n".join(saida))
        if not a_remover:
            print("\nNada a fazer.")
            return 0

        print()
        if not args.aplicar:
            print(f"ENSAIO — nada foi alterado. {len(a_remover)} linha(s) sairiam. "
                  "Rode de novo com --aplicar.")
            return 0

        movidas = 0
        async with conn.transaction():
            for rid, mantido in a_remover:
                snap = await conn.fetchval(
                    "DELETE FROM bilhetes WHERE id = $1 RETURNING to_jsonb(bilhetes.*)", rid)
                if snap is None:
                    continue
                await conn.execute(
                    """INSERT INTO lixeira_bilhetes (dono, motivo, mantido_id, bilhete)
                       VALUES ($1, $2, $3, $4::jsonb)""",
                    json.loads(snap)["dono"], MOTIVO, mantido, snap)
                movidas += 1
        print(f"{movidas} linha(s) movida(s) para `lixeira_bilhetes` (motivo: {MOTIVO}).")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
