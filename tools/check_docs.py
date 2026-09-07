#!/usr/bin/env python3
"""Gate de documentacao — falha quando o repo volta a inchar.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
O invariante #4 do CLAUDE.md ("podar snapshots... nunca copiar o HISTORICO")
estava escrito, era claro, e foi ignorado ate `Backups/` chegar a 551 pastas e
128 MB, com 165 copias de STATUS.md/HISTORICO.md dentro. O ritual /encerrar
mandava manter 3 sessoes no STATUS.md; o arquivo chegou a 187 KB.

Regra sem gate nao e cumprida neste repo — isso esta medido, nao suposto.
Este script e o gate.

O QUE ELE CHECA
---------------
  1. STATUS.md nao passa de STATUS_MAX_KB.
  2. Backups/ nao guarda copia de STATUS.md nem de HISTORICO.md (o git ja tem).
  3. Nenhum link markdown relativo aponta para arquivo inexistente.

O QUE ELE **NAO** CHECA (limite declarado, para o verde nao virar promessa falsa)
--------------------------------------------------------------------------------
  * Nao le CONTEUDO: um STATUS.md de 39 KB cheio de historia passa.
  * Nao valida ancora (`#secao`) — so a existencia do arquivo alvo.
  * A checagem (2) e VAZIA no CI: `Backups/` e gitignored, entao a pasta nem
    existe no checkout. Ela so tem efeito rodando local. Quando a pasta falta,
    o script DIZ que nao exerceu a checagem, em vez de contar como verde.

USO
---
    python tools/check_docs.py            # 0 = ok, 1 = FAIL
"""

from __future__ import annotations

import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS_MAX_KB = 40
ARQUIVOS_PROIBIDOS_EM_BACKUPS = ("STATUS.md", "HISTORICO.md")
IGNORAR = {"node_modules", "Backups", ".git", ".pytest_cache", "_backups", "__pycache__", "venv", ".venv"}

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

falhas: list[str] = []
avisos: list[str] = []


def _kb(caminho: str) -> float:
    return os.path.getsize(caminho) / 1024


def checar_tamanho_status() -> None:
    caminho = os.path.join(RAIZ, "STATUS.md")
    if not os.path.exists(caminho):
        falhas.append("STATUS.md nao existe na raiz.")
        return
    kb = _kb(caminho)
    if kb > STATUS_MAX_KB:
        falhas.append(
            f"STATUS.md tem {kb:.1f} KB — o teto e {STATUS_MAX_KB} KB.\n"
            f"       O changelog do topo guarda no maximo as 3 ultimas sessoes;\n"
            f"       o resto vai para docs/historico/ (ver /encerrar e CLAUDE.md #10)."
        )
    else:
        print(f"  OK   STATUS.md: {kb:.1f} KB (teto {STATUS_MAX_KB} KB)")


def checar_backups() -> None:
    pasta = os.path.join(RAIZ, "Backups")
    if not os.path.isdir(pasta):
        # Nao e verde: e checagem nao exercida. Dizer isso e o ponto.
        avisos.append(
            "Backups/ nao existe neste checkout (a pasta e gitignored, entao no CI "
            "ela nunca esta la). A checagem de copias NAO foi exercida aqui."
        )
        return
    achados: list[str] = []
    for dp, dns, fns in os.walk(pasta):
        for fn in fns:
            if fn in ARQUIVOS_PROIBIDOS_EM_BACKUPS:
                achados.append(os.path.relpath(os.path.join(dp, fn), RAIZ).replace(os.sep, "/"))
    if achados:
        total = sum(os.path.getsize(os.path.join(RAIZ, a)) for a in achados) / 1024 / 1024
        amostra = "\n".join(f"         {a}" for a in achados[:5])
        falhas.append(
            f"Backups/ guarda {len(achados)} copia(s) de STATUS.md/HISTORICO.md "
            f"({total:.1f} MB).\n"
            f"       O git ja versiona os dois — copiar de novo e peso puro "
            f"(invariante #4).\n{amostra}"
            + (f"\n         ... e mais {len(achados) - 5}" if len(achados) > 5 else "")
        )
    else:
        print(f"  OK   Backups/: nenhuma copia de {' / '.join(ARQUIVOS_PROIBIDOS_EM_BACKUPS)}")


def checar_links() -> None:
    mds: list[str] = []
    for dp, dns, fns in os.walk(RAIZ):
        dns[:] = [d for d in dns if d not in IGNORAR]
        mds.extend(os.path.join(dp, fn) for fn in fns if fn.endswith(".md"))

    quebrados: list[str] = []
    for caminho in mds:
        try:
            txt = open(caminho, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for _rotulo, alvo in LINK_RE.findall(txt):
            destino = alvo.split("#")[0].strip()
            if not destino or destino.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            absoluto = os.path.normpath(os.path.join(os.path.dirname(caminho), destino))
            if not os.path.exists(absoluto):
                origem = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
                quebrados.append(f"{origem} -> {alvo}")

    if quebrados:
        lista = "\n".join(f"         {q}" for q in quebrados)
        falhas.append(f"{len(quebrados)} link(s) markdown quebrado(s):\n{lista}")
    else:
        print(f"  OK   links markdown: {len(mds)} arquivos varridos, nenhum quebrado")


def main() -> int:
    print("check_docs — gate de documentacao\n")
    checar_tamanho_status()
    checar_backups()
    checar_links()

    for a in avisos:
        print(f"\n  AVISO  {a}")

    if falhas:
        print()
        for f in falhas:
            print(f"  FAIL  {f}")
        print(f"\nRESULTADO: {len(falhas)} FAIL.")
        return 1

    print("\nRESULTADO: sem FAILs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
