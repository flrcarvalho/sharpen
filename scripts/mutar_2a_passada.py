# -*- coding: utf-8 -*-
"""Prova por MUTACAO da 2a passada do perfil declarado (s310).

Front: quebra o `index.html` numa COPIA e roda `tests/js/sugerir_2a_passada.mjs`
contra ela via ALVO_INDEX. Rota: quebra `app/matcher.py` e roda o pytest do
contrato. Producao nunca e' tocada.

    python scripts/mutar_2a_passada.py
"""
import os, pathlib, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = pathlib.Path(__file__).resolve().parent.parent
INDEX = RAIZ / "app" / "static" / "index.html"
TJS = RAIZ / "tests" / "js" / "sugerir_2a_passada.mjs"
TPY = RAIZ / "tests" / "test_rota_sugerir.py"
MATCHER = RAIZ / "app" / "matcher.py"

MUT_FRONT = [
    ("folga volta a ser o 7 fixo (parametro ignorado)",
     "return (top - second >= folga) ? ranked[0].nome : null;",
     "return (top - second >= 7) ? ranked[0].nome : null;"),
    ("_sugParaBilhete nao repassa a folga ao ranqueador",
     "return _sugRanqueia(b, idx, null, folga);",
     "return _sugRanqueia(b, idx, null);"),
    ("default deixa de ser 7 (caminho principal muda de comportamento)",
     "function _sugRanqueia(b, idx, allowed, folga = 7) {",
     "function _sugRanqueia(b, idx, allowed, folga = 25) {"),
    ("casa dedicada deixa de cravar",
     "if (ded.length === 1) return ded[0];",
     "if (ded.length === 1 && false) return ded[0];"),
]
MUT_ROTA = [
    ("novatos passa a incluir TODO MUNDO",
     "return [n for n in ativos if m.cls.get(n, 0) < NOVATO_MAX]",
     "return list(ativos)"),
    ("novatos volta vazio (2a passada morre em silencio)",
     "return [n for n in ativos if m.cls.get(n, 0) < NOVATO_MAX]",
     "return []"),
    ("folga declarada cai para a do caminho principal",
     "FOLGA_DECLARADA = 25", "FOLGA_DECLARADA = 7"),
]

def roda(cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=RAIZ,
                          env={**os.environ, **(env or {})}).returncode

print("BASE front:", "VERDE" if roda(["node", str(TJS)]) == 0 else "VERMELHO")
print("BASE rota :", "VERDE" if roda([sys.executable, "-m", "pytest", str(TPY), "-q"]) == 0 else "VERMELHO")

pegas = tot = 0
orig_i = INDEX.read_text(encoding="utf-8")
tmpdir = pathlib.Path(tempfile.mkdtemp())
print("\n-- front (tests/js/sugerir_2a_passada.mjs) --")
for nome, de, para in MUT_FRONT:
    tot += 1
    if de not in orig_i:
        print(f"  ?? {nome}: ancora nao encontrada"); continue
    alvo = tmpdir / "index.html"
    alvo.write_text(orig_i.replace(de, para, 1), encoding="utf-8")
    morreu = roda(["node", str(TJS)], {"ALVO_INDEX": str(alvo)}) != 0
    pegas += morreu
    print(f"  {'PEGA   ' if morreu else 'ESCAPOU'} {nome}")

orig_m = MATCHER.read_text(encoding="utf-8")
print("\n-- rota (tests/test_rota_sugerir.py) --")
try:
    for nome, de, para in MUT_ROTA:
        tot += 1
        if de not in orig_m:
            print(f"  ?? {nome}: ancora nao encontrada"); continue
        MATCHER.write_text(orig_m.replace(de, para, 1), encoding="utf-8")
        morreu = roda([sys.executable, "-m", "pytest", str(TPY), "-q"]) != 0
        pegas += morreu
        print(f"  {'PEGA   ' if morreu else 'ESCAPOU'} {nome}")
finally:
    MATCHER.write_text(orig_m, encoding="utf-8")   # SEMPRE restaura

print(f"\n{pegas} de {tot} mutacoes pegas")
sys.exit(0 if pegas == tot else 1)
