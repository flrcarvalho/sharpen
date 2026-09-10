# -*- coding: utf-8 -*-
"""Une as linhas que são o MESMO bilhete lido várias vezes por print (s338).

POR QUE EXISTE
--------------
O `codigo_bilhete` entra na assinatura, então um dígito trocado é um bilhete NOVO. Quando
o código é lido de IMAGEM, a IA erra quase sempre em id longo — e erra DIFERENTE a cada
leitura. Medido na Blaze: 53 dos 55 códigos gravados por print têm comprimento errado, e
o mesmo bilhete do Jonathan (Susanto, 31/08) estava CINCO vezes na base, com cinco códigos
diferentes, um deles gravado como `270625314492244...`.

A Migração B' (`repository.upsert_bilhetes`) impede que isso continue crescendo: quando a
captura chega com o código verdadeiro, ela ADOTA a linha em vez de inserir outra. Mas ela
exige candidato ÚNICO — de propósito, porque adotar a linha errada não duplica, SEQUESTRA
a identidade de outro bilhete. Onde já há duas ou mais, quem desempata é este script, com
olho humano.

O QUE ELE NÃO FAZ
-----------------
Não conserta o código: o valor certo não está no banco, ele está na casa. A linha mantida
segue com o código torto e `codigo_ocr = TRUE` até a captura passar por ela e adotá-la.
Este script só garante que exista UMA linha para a captura adotar.

COMO ESCOLHE QUAL FICA
----------------------
Pelo valor MODAL de stake e odd — com N leituras independentes do mesmo card, o valor em
que a maioria concorda é a melhor estimativa que o banco tem —, desempatando pela mais
ANTIGA. Isso importa: o UPSERT congela stake/odd em linha resolvida, então o valor da
linha que fica é o valor que permanece. Divergência aparece no relatório, por linha, com o
P/L de cada uma. Para forçar outra escolha: `--manter <id>`.

Exclusão é MOVIMENTO, nunca soft-delete: o `DELETE … RETURNING to_jsonb(b.*)` é uma
operação só (ler antes e apagar depois abre janela para gravar uma lixeira que não
corresponde ao que saiu) e o snapshot vai para `lixeira_bilhetes`.

USO (ensaio é o padrão — só mexe no banco com --aplicar):
    python scripts/reparar_duplicatas_codigo_ocr.py
    python scripts/reparar_duplicatas_codigo_ocr.py --dono Jonathan
    python scripts/reparar_duplicatas_codigo_ocr.py --dono Jonathan --aplicar
    python scripts/reparar_duplicatas_codigo_ocr.py --dono Jonathan --manter 212907 --aplicar
"""
import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from collections import Counter
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

MOTIVO = "duplicata por código lido de OCR (s338)"


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
    """Descrição normalizada para agrupar leituras diferentes do MESMO texto.

    Duas leituras do mesmo card divergem em pontuação e caixa — `Li Michelle` de uma vez,
    `Li, Michelle` de outra —, e comparar verbatim deixaria o par escapar. Acento, vírgula
    e espaço saem; NOME e NÚMERO ficam, porque é neles que dois bilhetes DIFERENTES se
    separam (`Under 74,5` × `Under 78,5` continuam distintos: o 745 e o 785 sobrevivem).
    """
    s = unicodedata.normalize("NFKD", desc or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def _pl(linha) -> float | None:
    return calcular_pl(linha["stake"], linha["odd"], linha["resultado"])


def _modal(valores: list[str]) -> str:
    """O valor em que a maioria das leituras concorda (empate → o 1º, que vem da mais
    antiga, porque a lista chega ordenada por `criado_em`)."""
    return Counter(valores).most_common(1)[0][0]


def _escolher(linhas: list) -> tuple[int, bool]:
    """(id da linha que fica, houve divergência de dinheiro?).

    A linha que fica é a mais ANTIGA entre as que carregam os valores modais de stake e
    odd. Se nenhuma tiver os dois, a mais antiga com a stake modal — a stake é o que sai
    da conta, e é ela que manda no turnover e na assinatura de stake do matcher.
    """
    stake_m = _modal([l["stake"] or "" for l in linhas])
    odd_m = _modal([l["odd"] or "" for l in linhas])
    divergiu = len({l["stake"] or "" for l in linhas}) > 1 or len({l["odd"] or "" for l in linhas}) > 1
    for criterio in (lambda l: (l["stake"] or "") == stake_m and (l["odd"] or "") == odd_m,
                     lambda l: (l["stake"] or "") == stake_m,
                     lambda l: True):
        candidatas = [l for l in linhas if criterio(l)]
        if candidatas:
            return candidatas[0]["id"], divergiu
    return linhas[0]["id"], divergiu


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dono", default=None, help="restringe a um dono (ex.: Jonathan)")
    ap.add_argument("--casa", default=None, help="restringe a uma casa (ex.: Blaze)")
    ap.add_argument("--manter", type=int, action="append", default=[],
                    help="força manter este id (pode repetir); o resto do grupo dele sai")
    ap.add_argument("--aplicar", action="store_true",
                    help="executa; sem isto é ENSAIO e nada no banco muda")
    args = ap.parse_args()

    conn = await asyncpg.connect(_database_url())
    try:
        filtros = ["codigo_ocr = TRUE", "archived = FALSE"]
        params = []
        if args.dono:
            params.append(args.dono)
            filtros.append(f"dono = ${len(params)}")
        if args.casa:
            params.append(args.casa)
            filtros.append(f"casa = ${len(params)}")
        linhas = await conn.fetch(
            f"""SELECT id, dono, casa, parceiro, data, esporte, aposta, descricao,
                       stake, odd, resultado, codigo_bilhete, extraction_state, criado_em
                  FROM bilhetes WHERE {' AND '.join(filtros)}
                 ORDER BY criado_em""", *params)

        grupos: dict[tuple, list] = {}
        for l in linhas:
            k = (l["dono"], l["casa"], l["parceiro"], l["data"] or "",
                 _chave_desc(l["descricao"]), (l["resultado"] or "").upper())
            grupos.setdefault(k, []).append(l)
        dups = {k: v for k, v in grupos.items() if len(v) > 1}

        print("=" * 78)
        print(f"{len(linhas)} linha(s) com código de OCR · {len(dups)} grupo(s) duplicado(s)"
              f" · {sum(len(v) - 1 for v in dups.values())} linha(s) a remover")
        print("=" * 78)
        if not dups:
            print("Nada a fazer.")
            return 0

        forcados = set(args.manter)
        a_remover: list[tuple[int, int]] = []   # (id_removido, id_mantido)
        for (dono, casa, parceiro, data, _d, res), grupo in sorted(dups.items()):
            manter_ids = forcados.intersection({l["id"] for l in grupo})
            if len(manter_ids) > 1:
                print(f"\n!! --manter aponta 2+ linhas do mesmo grupo ({sorted(manter_ids)}) — "
                      "grupo PULADO")
                continue
            escolhido, divergiu = _escolher(grupo)
            if manter_ids:
                escolhido = manter_ids.pop()
            print(f"\n{casa} · {parceiro} · {data} · {res or '(aberta)'}")
            print(f"  {grupo[0]['descricao'][:88]}")
            for l in grupo:
                pl = _pl(l)
                marca = "MANTÉM " if l["id"] == escolhido else "remove "
                print(f"  {marca}#{l['id']:>7} stake={l['stake']:>10} odd={str(l['odd'])[:10]:>10} "
                      f"P/L={('%.2f' % pl) if pl is not None else '  —':>10} "
                      f"cod={l['codigo_bilhete']!r} ({l['criado_em']:%d/%m %H:%M})")
                if l["id"] != escolhido:
                    a_remover.append((l["id"], escolhido))
            if divergiu:
                print("  ⚠ as leituras discordam no dinheiro — o valor MODAL foi mantido; "
                      "confira antes de aplicar (--manter <id> força outra)")

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
        print("A linha que ficou segue com o código torto até a captura passar por ela — "
              "é a Migração B' que o corrige, e agora ela tem candidato único.")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
