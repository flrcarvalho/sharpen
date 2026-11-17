"""Blocos do harness para o contrato de liquidação (plano de confiabilidade 8.1, s460).

O contrato (`tests/test_contrato_liquidacao.py`) roda as funções REAIS do servidor sobre
os blocos que os formatadores REAIS do `content.js` imprimem no harness. O harness leva
~3 min, então o pytest não o roda: lê um snapshot, e é este script que o mantém.

    # 1. fotografar o harness (grava a saída de todo `format*`)
    SHARPENUP_FOTO=/tmp/foto.json node extensor/harness/run.mjs
    # 2a. regravar o snapshot (depois de mudar formatador ou fixture)
    python tools/contrato_liquidacao.py gravar /tmp/foto.json
    # 2b. conferir se o snapshot está em dia (o CI faz isto)
    python tools/contrato_liquidacao.py conferir /tmp/foto.json

A conferência compara só as linhas que decidem dinheiro (Stake, Odd, Status, Retorno, P/L):
data depende do fuso da máquina (o CI roda em UTC) e não entra no contrato.
"""
from __future__ import annotations

import gzip
import json
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(RAIZ, "app"))

SNAPSHOT = os.path.join(RAIZ, "tests", "fixtures", "contrato_liquidacao", "blocos.json.gz")

# A MESMA fronteira de bloco que o servidor usa (`repository._ID_MARCADOR_RE`).
from repository import _ID_MARCADOR_RE  # noqa: E402

_LINHA_DINHEIRO = re.compile(r"^[ \t]*(?:Stake|Odd[^:\n]*|Status|Retorno[^:\n]*|P/L)[ \t]*:.*$",
                             re.MULTILINE)


def blocos_da_foto(caminho: str) -> dict[str, list[str]]:
    """{caso: [bloco, …]} com cada bloco DISTINTO que um `format*` imprimiu. O mesmo código
    pode aparecer em vários estados no mesmo caso (aberto e depois liquidado): os dois ficam."""
    foto = json.load(open(caminho, encoding="utf-8"))
    out: dict[str, list[str]] = {}
    vistos: set = set()
    for f in foto:
        if not str(f.get("tipo", "")).startswith("format"):
            continue
        v = json.loads(f["v"])
        if not isinstance(v, str):
            continue
        partes = _ID_MARCADOR_RE.split(v)
        for i in range(1, len(partes) - 1, 2):
            cod = (partes[i] or "").strip()
            if not cod:
                continue
            bloco = "[Código: %s]%s" % (cod, partes[i + 1].rstrip())
            chave = (f["caso"], bloco)
            if chave in vistos:
                continue
            vistos.add(chave)
            out.setdefault(f["caso"], []).append(bloco)
    return {k: out[k] for k in sorted(out)}


def projecao(blocos: dict[str, list[str]]) -> dict[str, list[str]]:
    """O que o contrato lê de cada bloco, sem data: {caso: [linhas de dinheiro, ordenadas]}."""
    proj = {}
    for caso, lista in blocos.items():
        itens = set()
        for b in lista:
            cod = _ID_MARCADOR_RE.search(b).group(1)
            itens.add(cod + " | " + " | ".join(m.group(0).strip() for m in _LINHA_DINHEIRO.finditer(b)))
        proj[caso] = sorted(itens)
    return proj


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("gravar", "conferir"):
        print(__doc__)
        return 2
    novo = blocos_da_foto(argv[2])
    if not novo:
        print("nenhum bloco na fotografia: rode o harness com SHARPENUP_FOTO=<arquivo>")
        return 1
    if argv[1] == "gravar":
        os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
        # mtime=0: o mesmo conteúdo gera o mesmo arquivo, sem diff falso no git.
        bruto = json.dumps(novo, ensure_ascii=False, indent=0, sort_keys=True).encode("utf-8")
        with open(SNAPSHOT, "wb") as fh:
            fh.write(gzip.compress(bruto, mtime=0))
        print(f"snapshot: {sum(map(len, novo.values()))} bloco(s) de {len(novo)} caso(s) em {SNAPSHOT}")
        return 0
    velho = json.loads(gzip.decompress(open(SNAPSHOT, "rb").read()).decode("utf-8"))
    pn, pv = projecao(novo), projecao(velho)
    difs = []
    for caso in sorted(set(pn) | set(pv)):
        a, b = set(pv.get(caso, [])), set(pn.get(caso, []))
        for x in sorted(b - a)[:3]:
            difs.append(f"  + {caso}: {x[:160]}")
        for x in sorted(a - b)[:3]:
            difs.append(f"  - {caso}: {x[:160]}")
    if difs:
        print("Snapshot do contrato de liquidação DESATUALIZADO (formatador ou fixture mudou):")
        print("\n".join(difs[:40]))
        print("Regrave: SHARPENUP_FOTO=/tmp/foto.json node extensor/harness/run.mjs && "
              "python tools/contrato_liquidacao.py gravar /tmp/foto.json  — e rode "
              "pytest tests/test_contrato_liquidacao.py")
        return 1
    print(f"snapshot do contrato em dia: {sum(map(len, pn.values()))} bloco(s), {len(pn)} caso(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
