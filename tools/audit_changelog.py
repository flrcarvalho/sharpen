#!/usr/bin/env python3
"""Auditoria do CHANGELOG da home (FDC Capital / Planilhador).

O que este gate impede
----------------------
A caixa "SharpenUp — versão a versão" do `/inicio` já ficou 8 versões atrás DUAS vezes
(s254 e s292). O motivo é sempre o mesmo: bumpar o `manifest.json` é obrigatório para a
extensão funcionar, e escrever a nota não era obrigatório para nada. Um dos dois atos
tem consequência imediata, o outro não — então só o primeiro sobrevive à pressa.

Aqui o segundo ganha consequência: versão publicada sem nota **quebra o CI**.

Uso:
    python tools/audit_changelog.py
Saída: relatório legível + exit code 1 se houver qualquer FAIL.

Limite conhecido: este gate NÃO sabe se a nota é boa, se foi ao grupo, nem se o texto
descreve a mudança certa. Ele prova que existe nota para a versão publicada, que as
entradas têm forma válida e que nenhuma nota está adiantada em relação ao manifest.
"""
import datetime
import json
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CHANGELOG = RAIZ / "app" / "changelog.json"
MANIFEST = RAIZ / "extensor" / "manifest.json"
INICIO = RAIZ / "app" / "static" / "inicio.html"

RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_VERSAO = re.compile(r"^v\d+\.\d+\.\d+$")
# Asterisco solto: o render da home só faz **negrito**. `*assim*` sai literal na tela,
# com os asteriscos à mostra — foi o que aconteceu com a nota da 0.6.41.
RE_ASTERISCO_SOLTO = re.compile(r"(?<!\*)\*(?!\*)")


def tupla(v: str) -> tuple:
    return tuple(int(x) for x in v.lstrip("v").split("."))


def textos(entrada: dict):
    """Todo campo de texto de uma entrada, para as checagens de forma."""
    for chave in ("titulo", "texto", "fecho"):
        if entrada.get(chave):
            yield chave, entrada[chave]
    for i, item in enumerate(entrada.get("itens") or []):
        yield f"itens[{i}]", item


def auditar() -> list[str]:
    """Devolve a lista de FAILs (vazia = tudo certo). Imprime o relatório."""
    falhas: list[str] = []

    def ok(msg):
        print(f"  OK   {msg}")

    def fail(msg):
        print(f"  FAIL {msg}")
        falhas.append(msg)

    print("── changelog.json ──")
    try:
        dados = json.loads(CHANGELOG.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"changelog.json ilegível: {e}")
        return falhas
    ok(f"{CHANGELOG.relative_to(RAIZ)} parseia")

    novidades = dados.get("novidades") or []
    sharpenup = dados.get("sharpenup") or []
    sem_nota = dados.get("sharpenup_sem_nota") or {}

    # ── forma das entradas ──
    print("── forma das entradas ──")
    vistos: dict[str, str] = {}
    for nome, lista in (("novidades", novidades), ("sharpenup", sharpenup)):
        for entrada in lista:
            eid = entrada.get("id") or "<sem id>"
            if eid in vistos:
                fail(f"id duplicado: {eid} (em {vistos[eid]} e em {nome})")
            vistos[eid] = nome
            if not RE_DATA.match(entrada.get("data") or ""):
                fail(f"{eid}: data {entrada.get('data')!r} não é AAAA-MM-DD")
            if not entrada.get("texto") and not entrada.get("itens"):
                fail(f"{eid}: nota vazia (sem texto e sem itens)")
            for campo, txt in textos(entrada):
                if RE_ASTERISCO_SOLTO.search(txt):
                    fail(f"{eid}: asterisco solto em {campo} — o render só faz **negrito**")
                if "<" in txt and ">" in txt:
                    fail(f"{eid}: HTML em {campo} — o render escapa, sairia literal")
    ok(f"{len(novidades)} novidades e {len(sharpenup)} versões com forma válida"
       if not falhas else "forma conferida (com falhas acima)")

    # ── versões ──
    print("── versões ──")
    for entrada in sharpenup:
        if not RE_VERSAO.match(entrada.get("v") or ""):
            fail(f"{entrada.get('id')}: v={entrada.get('v')!r} não é vX.Y.Z")
    vs = [e["v"] for e in sharpenup if RE_VERSAO.match(e.get("v") or "")]
    if vs != sorted(vs, key=tupla, reverse=True):
        fail("a lista sharpenup não está em ordem decrescente de versão (a nova vai no TOPO)")
    else:
        ok("lista em ordem decrescente")

    manifesto = json.loads(MANIFEST.read_text(encoding="utf-8")).get("version", "")
    anotadas = {v.lstrip("v") for v in vs}
    if manifesto in anotadas:
        ok(f"a versão publicada ({manifesto}) tem nota na home")
    elif manifesto in sem_nota:
        ok(f"a versão publicada ({manifesto}) está dispensada: {sem_nota[manifesto]}")
    else:
        fail(f"o manifest.json está em {manifesto} e NÃO existe nota para ela — "
             f"rode `python scripts/avisar_testers.py --versao {manifesto} ...`")

    adiantadas = [v for v in vs if tupla(v) > tupla(manifesto)]
    if adiantadas:
        fail(f"nota de versão que ninguém pode baixar (manifest={manifesto}): {adiantadas}")
    else:
        ok("nenhuma nota adiantada em relação ao manifest")

    # ── datas ──
    print("── datas ──")
    amanha = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    futuras = [e["id"] for e in novidades + sharpenup if (e.get("data") or "") > amanha]
    if futuras:
        fail(f"data no futuro (a home ordena e corta por data): {futuras}")
    else:
        ok("nenhuma data no futuro")

    # ── a home lê daqui, e só daqui ──
    print("── acoplamento com a home ──")
    html = INICIO.read_text(encoding="utf-8")
    if re.search(r"^const (NOVIDADES|SHARPENUP)\s*=", html, re.M):
        fail("inicio.html voltou a ter array de changelog embutido — a fonte é o changelog.json")
    elif "/changelog" not in html:
        fail("inicio.html não busca /changelog — as caixas ficariam vazias")
    else:
        ok("inicio.html lê GET /changelog, sem array embutido")

    return falhas


def main() -> int:
    falhas = auditar()
    print()
    if falhas:
        print(f"RESULTADO: {len(falhas)} FAIL")
        return 1
    print("RESULTADO: sem FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
