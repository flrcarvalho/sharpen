# -*- coding: utf-8 -*-
"""Prova por MUTACAO do aviso de curadoria vencida (s310).

Teste verde nao e' teste que detecta (CLAUDE.md). Aqui cada mutacao quebra o
`gestao.js` de proposito, numa COPIA, e roda `tests/js/casas_curadoria.mjs`
contra ela via `ALVO_GESTAO`. Producao nunca e' tocada.

    python scripts/mutar_casas_curadoria.py
"""
import pathlib, shutil, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding="utf-8")

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "gestao.js"
TESTE = RAIZ / "tests" / "js" / "casas_curadoria.mjs"

MUTACOES = [
    ("aviso nunca renderiza",
     "const alerta=c.curadoria_vencida", "const alerta=false&&c.curadoria_vencida"),
    ("aviso renderiza SEMPRE (casa sadia tambem acende)",
     "const alerta=c.curadoria_vencida", "const alerta=true||c.curadoria_vencida"),
    ("linha perde a marca 'vencida'",
     "+(c.curadoria_vencida?' vencida':'')", "+''"),
    ("aviso deixa de nomear o custo em apostas",
     "'evidência mudou · <b>'+fmt(c.fora_do_pool,0)+'</b> de <b>'+fmt(c.total,0)+'</b> apostas são de fora",
     "'evidência mudou · curadoria desatualizada"),
    ("cabecalho para de contar as vencidas",
     "+(nVenc?(' · <span class=\"w\">'+nVenc+' a revisar</span>'):'')", "+''"),
    ("cabecalho conta, mas fora da classe de warn",
     "' · <span class=\"w\">'+nVenc+' a revisar</span>'", "' · <span>'+nVenc+' a revisar</span>'"),
]

orig = ALVO.read_text(encoding="utf-8")
base = subprocess.run(["node", str(TESTE)], capture_output=True, text=True, cwd=RAIZ)
print(f"BASE (sem mutacao): {'VERDE' if base.returncode == 0 else 'VERMELHO'}")
if base.returncode != 0:
    print(base.stdout[-800:]); sys.exit(1)

pegas = 0
tmp = pathlib.Path(tempfile.mkdtemp()) / "gestao.js"
for nome, de, para in MUTACOES:
    if de not in orig:
        print(f"  ?? {nome}: ancora nao encontrada — mutacao INVALIDA"); continue
    tmp.write_text(orig.replace(de, para, 1), encoding="utf-8")
    r = subprocess.run(["node", str(TESTE)], capture_output=True, text=True, cwd=RAIZ,
                       env={**__import__("os").environ, "ALVO_GESTAO": str(tmp)})
    morreu = r.returncode != 0
    pegas += morreu
    print(f"  {'PEGA   ' if morreu else 'ESCAPOU'} {nome}")
    if not morreu:
        print("     ^ o teste segue verde sem essa linha: ou e' redundante, ou falta asserção")
print(f"\n{pegas} de {len(MUTACOES)} mutacoes pegas")
sys.exit(0 if pegas == len(MUTACOES) else 1)
