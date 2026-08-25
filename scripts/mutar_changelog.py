#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prova por MUTAÇÃO os gates do changelog da home (s292).

"Teste verde não é teste que detecta" (CLAUDE.md): gate novo só vale depois de quebrar o
código de propósito e ver o teste ficar vermelho. Este script faz isso — 8 mutações no
gate/rota/script Python e 6 no render do `inicio.html` —, restaurando o arquivo original
no `finally` mesmo se algo explodir no meio.

    python scripts/mutar_changelog.py

Saída: uma linha por mutação (OK = detectada, ESCAPOU = buraco de teste) + o resumo.
Exit code 1 se alguma escapar.

Mutação que escapa quase sempre denuncia o TESTE, não o código: a N6 escapou na primeira
rodada porque o dado sintético punha as novidades velhas no fim da lista, onde o teto de
itens já as escondia — o corte de idade nunca chegava a ser exercido.
"""
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
INICIO = RAIZ / "app" / "static" / "inicio.html"
RENDER_MJS = RAIZ / "tests" / "js" / "novidades_render.mjs"

NOV_RICH = (
    "function novRich(s){return esc(s||'').replace(/\\*\\*(.+?)\\*\\*/g,'<b>$1</b>');}"
)

# (nome, arquivo, trecho original, trecho mutado, teste que TEM de ficar vermelho)
MUT_PY = [
    ("M1 manifest sem nota", "tools/audit_changelog.py",
     'fail(f"o manifest.json está em {manifesto} e NÃO existe nota para ela — "\n'
     '             f"rode `python scripts/avisar_testers.py --versao {manifesto} ...`")',
     'ok("(mutado) nao confere o manifest")',
     "tests/test_changelog.py::test_versao_publicada_sem_nota_falha"),
    ("M2 ordem decrescente", "tools/audit_changelog.py",
     'fail("a lista sharpenup não está em ordem decrescente de versão (a nova vai no TOPO)")',
     'ok("(mutado) nao confere ordem")',
     "tests/test_changelog.py::test_fora_de_ordem_falha"),
    ("M3 asterisco solto", "tools/audit_changelog.py",
     "if RE_ASTERISCO_SOLTO.search(txt):", "if False:",
     "tests/test_changelog.py::test_asterisco_solto_falha"),
    ("M4 id duplicado", "tools/audit_changelog.py",
     "if eid in vistos:", "if False:",
     "tests/test_changelog.py::test_id_duplicado_falha"),
    ("M5 array de volta no html", "tools/audit_changelog.py",
     'if re.search(r"^const (NOVIDADES|SHARPENUP)\\s*=", html, re.M):', "if False:",
     "tests/test_changelog.py::test_array_de_volta_no_html_falha"),
    ("M6 rota sem auth", "app/main.py",
     '    if not usuario_do_request(request):\n        raise HTTPException(401, "Não autenticado.")\n    return JSONResponse(',
     "    return JSONResponse(",
     "tests/test_changelog.py::test_rota_exige_sessao"),
    ("M7 grava antes do ok", "scripts/avisar_testers.py",
     '        if not r.get("ok"):',
     '        gravar(entrada, a.versao)\n        if not r.get("ok"):',
     "tests/test_changelog.py::test_envio_falho_nao_grava_no_changelog"),
    ("M8 nota adiantada", "tools/audit_changelog.py",
     'fail(f"nota de versão que ninguém pode baixar (manifest={manifesto}): {adiantadas}")',
     'ok("(mutado) aceita nota adiantada")',
     "tests/test_changelog.py::test_nota_adiantada_falha"),
]

# Mutações no render da home — todas conferidas contra tests/js/novidades_render.mjs.
MUT_JS = [
    ("N1 sem corte NOV_MAX", ".slice(0,NOV_MAX);", ";"),
    ("N2 SU_MAX volta a 9", "const SU_MAX=12;", "const SU_MAX=9;"),
    ("N3 negrito não converte", NOV_RICH, "function novRich(s){return esc(s||'');}"),
    ("N4 texto cru na tela (XSS)", NOV_RICH, "function novRich(s){return String(s||'');}"),
    ("N5 resposta ruim não é checada",
     "const NOVIDADES=Array.isArray(cl.novidades)?cl.novidades:[];",
     "const NOVIDADES=cl.novidades||[];"),
    ("N6 sem corte de idade",
     "const t=Date.parse(n.data);return isNaN(t)||t>=lim;", "return true;"),
]


def rodar(cmd):
    return subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True).returncode != 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    escaparam = []

    print("── gate, rota e script (pytest) ──")
    for nome, arq, velho, novo, teste in MUT_PY:
        p = RAIZ / arq
        orig = p.read_text(encoding="utf-8")
        if velho not in orig:
            print(f"[?      ] {nome}: alvo não encontrado em {arq}")
            escaparam.append(nome)
            continue
        p.write_text(orig.replace(velho, novo, 1), encoding="utf-8")
        try:
            det = rodar([sys.executable, "-m", "pytest", teste, "-q"])
        finally:
            p.write_text(orig, encoding="utf-8")
        print(f"[{'OK     ' if det else 'ESCAPOU'}] {nome} → {teste.split('::')[1]}")
        if not det:
            escaparam.append(nome)

    print("── render da home (node) ──")
    orig = INICIO.read_text(encoding="utf-8")
    for nome, velho, novo in MUT_JS:
        if velho not in orig:
            print(f"[?      ] {nome}: alvo não encontrado em inicio.html")
            escaparam.append(nome)
            continue
        INICIO.write_text(orig.replace(velho, novo, 1), encoding="utf-8")
        try:
            det = rodar(["node", str(RENDER_MJS)])
        finally:
            INICIO.write_text(orig, encoding="utf-8")
        print(f"[{'OK     ' if det else 'ESCAPOU'}] {nome}")
        if not det:
            escaparam.append(nome)

    print()
    print("mutações que escaparam:", escaparam or "nenhuma")
    return 1 if escaparam else 0


if __name__ == "__main__":
    raise SystemExit(main())
