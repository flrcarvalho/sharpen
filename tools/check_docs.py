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
  0. docs/CASOS.md nao passa de CASOS_MAX_KB.
  1. STATUS.md nao passa de STATUS_MAX_KB.
  2. STATUS.md nao tem mais de MAX_BLOCOS_SESSAO blocos "## Sessao".
  3. STATUS.md nao tem mais de MAX_ANTERIOR paragrafos "_Anterior:".
  4. Backups/ nao guarda arquivo que comece com STATUS ou HISTORICO.
  5. Nenhum link markdown relativo aponta para arquivo inexistente.
  6. Toda ANCORA (`arquivo.md#secao`) resolve contra um titulo real do alvo.

Por que (2) e (3) existem, se ja ha (1): **byte sozinho e gate fraco.** Um
STATUS de 49 KB so de historia passa no teto e ja perdeu o proposito. As duas
checagens estruturais medem a FORMA que o /encerrar manda (estado atual + no
maximo 3 sessoes), e um STATUS que volte a crescer estoura elas antes do byte.

Por que (4) e por PREFIXO e nao por nome exato: uma copia renomeada
(`STATUS.md-antes-do-corte`) e a mesma copia. Backup deliberado de cirurgia
tambem reprova, e isso e o comportamento certo — o invariante #4 manda nunca
copiar estes dois para `Backups/`, e o git guarda o estado anterior.

O QUE ELE **NAO** CHECA (limite declarado, para o verde nao virar promessa falsa)
--------------------------------------------------------------------------------
  * Nao le CONTEUDO: 3 blocos de sessao gigantes dentro do teto passam.
  * A checagem de ancora cobre so os .md vivos; ancora para fora do repo nao e vista.
  * Nao olha o BACKLOG.md: nada aqui percebe pendencia que sumiu dele.
  * A checagem (4) e VAZIA no CI: `Backups/` e gitignored, entao a pasta nem
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
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATUS_MAX_KB = 50
CASOS_MAX_KB = 60
MAX_BLOCOS_SESSAO = 3
MAX_ANTERIOR = 2
PREFIXOS_PROIBIDOS_EM_BACKUPS = ("STATUS", "HISTORICO")
IGNORAR = {"node_modules", "Backups", ".git", ".pytest_cache", "_backups", "__pycache__", "venv", ".venv"}

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BLOCO_SESSAO_RE = re.compile(r"(?m)^## Sess[aã]o\b")
ANTERIOR_RE = re.compile(r"(?m)^_Anterior:")

falhas: list[str] = []
avisos: list[str] = []


def _status() -> str | None:
    caminho = os.path.join(RAIZ, "STATUS.md")
    if not os.path.exists(caminho):
        falhas.append("STATUS.md nao existe na raiz.")
        return None
    return open(caminho, encoding="utf-8", errors="replace").read()


def checar_tamanho_casos() -> None:
    """docs/CASOS.md — o deposito de casos que o CLAUDE.md deixou de carregar.

    Ele nasceu com ~26 KB no Lote E da faxina. O teto existe para avisar quando ele
    virar o proximo HISTORICO e precisar de particao — nao para impedir que cresca.
    Ele NAO e auto-carregado em sessao nenhuma; ler e ato deliberado.
    """
    caminho = os.path.join(RAIZ, "docs", "CASOS.md")
    if not os.path.exists(caminho):
        avisos.append("docs/CASOS.md ainda nao existe — checagem de tamanho NAO exercida.")
        return
    kb = os.path.getsize(caminho) / 1024
    if kb > CASOS_MAX_KB:
        falhas.append(
            f"docs/CASOS.md tem {kb:.1f} KB — o teto e {CASOS_MAX_KB} KB.\n"
            f"       Hora de partir por assunto, como o docs/historico/ ja foi partido.\n"
            f"       O teto e sinal de particao, nao de excesso: caso nao se apaga."
        )
    else:
        print(f"  OK   docs/CASOS.md: {kb:.1f} KB (teto {CASOS_MAX_KB} KB)")


def checar_tamanho_status(txt: str) -> None:
    kb = len(txt.encode("utf-8")) / 1024
    if kb > STATUS_MAX_KB:
        falhas.append(
            f"STATUS.md tem {kb:.1f} KB — o teto e {STATUS_MAX_KB} KB.\n"
            f"       O changelog do topo guarda no maximo as 3 ultimas sessoes;\n"
            f"       o resto vai para docs/historico/ (ver /encerrar e CLAUDE.md #10)."
        )
    else:
        print(f"  OK   STATUS.md: {kb:.1f} KB (teto {STATUS_MAX_KB} KB)")


def checar_forma_status(txt: str) -> None:
    """As duas checagens ESTRUTURAIS. Byte sozinho e gate fraco."""
    blocos = len(BLOCO_SESSAO_RE.findall(txt))
    if blocos > MAX_BLOCOS_SESSAO:
        falhas.append(
            f"STATUS.md tem {blocos} blocos '## Sessao' — o maximo e {MAX_BLOCOS_SESSAO}.\n"
            f"       Mova o mais antigo para docs/historico/, preservando o texto integral."
        )
    else:
        print(f"  OK   STATUS.md: {blocos} bloco(s) '## Sessao' (maximo {MAX_BLOCOS_SESSAO})")

    anteriores = len(ANTERIOR_RE.findall(txt))
    if anteriores > MAX_ANTERIOR:
        falhas.append(
            f"STATUS.md tem {anteriores} paragrafos '_Anterior:' — o maximo e {MAX_ANTERIOR}.\n"
            f"       A cadeia '_Anterior:' cobre a sessao que NAO tem mais bloco proprio;\n"
            f"       o excedente vai para a cadeia do docs/historico/."
        )
    else:
        print(f"  OK   STATUS.md: {anteriores} paragrafo(s) '_Anterior:' (maximo {MAX_ANTERIOR})")


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
            if fn.startswith(PREFIXOS_PROIBIDOS_EM_BACKUPS):
                achados.append(os.path.relpath(os.path.join(dp, fn), RAIZ).replace(os.sep, "/"))
    if achados:
        total = sum(os.path.getsize(os.path.join(RAIZ, a)) for a in achados) / 1024 / 1024
        amostra = "\n".join(f"         {a}" for a in achados[:5])
        falhas.append(
            f"Backups/ guarda {len(achados)} arquivo(s) comecando por "
            f"{' / '.join(PREFIXOS_PROIBIDOS_EM_BACKUPS)} ({total:.1f} MB).\n"
            f"       O git ja versiona os dois — copiar de novo e peso puro "
            f"(invariante #4).\n{amostra}"
            + (f"\n         ... e mais {len(achados) - 5}" if len(achados) > 5 else "")
        )
    else:
        print(f"  OK   Backups/: nada comecando por {' / '.join(PREFIXOS_PROIBIDOS_EM_BACKUPS)}")


def _slug(titulo: str) -> str:
    """Ancora no estilo GitHub: minusculas, remove o que nao e letra/digito/espaco/hifen,
    e troca CADA espaco por UM hifen.

    ⚠️ Nao colapse espacos. O caractere removido que estava ENTRE dois espacos deixa os
    dois para tras, e eles viram `--`:

        "5. Superficie de registro — os 12 pontos"  ->  5-superficie-de-registro--os-12-pontos
        "3. Contrato de mensagens (inject ⇄ content)" -> 3-contrato-de-mensagens-inject--content

    Colapsar com `\\s+` gera `-` onde o GitHub gera `--`, e o gate passa a REPROVAR ancora
    correta e APROVAR ancora quebrada. Foi o que aconteceu no bloco 1 do Lote E: eu
    "consertei" 5 ancoras que estavam certas.
    """
    s = re.sub(r"[`*_]", "", titulo.strip().lower())
    s = "".join(c for c in s if unicodedata.category(c)[0] in "LNZ" or c in "- ")
    return s.strip().replace(" ", "-")


_TITULO_RE = re.compile(r"(?m)^#{1,6}\s+(.*?)\s*$")


def checar_ancoras(mds: list[str]) -> None:
    """Link `alvo.md#ancora` tem de casar um titulo real do alvo.

    Sem isto, renomear um titulo do CASOS.md quebra a navegacao do CLAUDE.md sem
    ninguem perceber — o mesmo defeito (#24 da auditoria de 19/07) que esta faxina
    fechou no HISTORICO.
    """
    cache: dict[str, set[str]] = {}

    def ancoras_de(caminho: str) -> set[str]:
        if caminho not in cache:
            try:
                txt = open(caminho, encoding="utf-8", errors="replace").read()
            except OSError:
                cache[caminho] = set()
            else:
                cache[caminho] = {_slug(t) for t in _TITULO_RE.findall(txt)}
        return cache[caminho]

    quebradas: list[str] = []
    total = 0
    for caminho in mds:
        try:
            txt = open(caminho, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for _rotulo, alvo in LINK_RE.findall(txt):
            if "#" not in alvo:
                continue
            destino, _, ancora = alvo.partition("#")
            destino, ancora = destino.strip(), ancora.strip()
            if not destino or not ancora:
                continue
            if destino.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            absoluto = os.path.normpath(os.path.join(os.path.dirname(caminho), destino))
            if not absoluto.endswith(".md") or not os.path.exists(absoluto):
                continue          # arquivo inexistente ja e pego por checar_links
            total += 1
            if ancora not in ancoras_de(absoluto):
                origem = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
                quebradas.append(f"{origem} -> {alvo}")

    if quebradas:
        lista = "\n".join(f"         {q}" for q in quebradas)
        falhas.append(
            f"{len(quebradas)} de {total} ancora(s) nao resolvem contra um titulo do alvo:\n"
            f"{lista}"
        )
    else:
        print(f"  OK   ancoras: {total} conferidas contra os titulos do alvo")


def _todos_md() -> list[str]:
    mds: list[str] = []
    for dp, dns, fns in os.walk(RAIZ):
        dns[:] = [d for d in dns if d not in IGNORAR]
        mds.extend(os.path.join(dp, fn) for fn in fns if fn.endswith(".md"))
    return mds


def checar_links(mds: list[str]) -> None:
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
    checar_tamanho_casos()
    txt = _status()
    if txt is not None:
        checar_tamanho_status(txt)
        checar_forma_status(txt)
    checar_backups()
    mds = _todos_md()
    checar_links(mds)
    checar_ancoras(mds)

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
