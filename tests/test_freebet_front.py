"""FREEBET no dashboard (s392, passo 2c) — roda `tests/js/freebet_front.mjs` e o prova por
MUTAÇÃO automática sobre cópias dos arquivos de produção (variáveis `ALVO_*`).

O cabeçalho do `.mjs` diz o que é coberto e o que não é. Aqui, além do verde, cada mutação
abaixo tem de deixá-lo VERMELHO; a que passar é buraco de teste, não código redundante.

E o feed do servidor: `dashboard_rows` manda `stake_freebet` só nas linhas que têm (por
leitura do fonte; a função toca o banco).
"""
import os
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
MJS = RAIZ / "tests" / "js" / "freebet_front.mjs"
DASH = RAIZ / "app" / "static" / "dash" / "assets" / "js"
ARQS = {
    "app": DASH / "app.js",
    "apostas": DASH / "charts" / "apostas.js",
    "abertas": DASH / "charts" / "abertas.js",
    "gestao": DASH / "charts" / "gestao.js",
}


def test_front_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES = [
    ("o feed não aplica a freebet", "app",
     "const norm=normalizeDados(dados).map(_aplicarFreebet);", "const norm=normalizeDados(dados);"),
    ("a freebet não desconta do stake", "app",
     "r.stake=Math.round((s-fb)*100)/100;", "r.stake=s;"),
    ("freebet maior que a stake é aceita", "app",
     "if(fb>0&&fb<=s+0.005){", "if(fb>0){"),
    ("o stakeCheio ignora o apostado", "app",
     "function stakeCheio(r){return r.stake_cheio!=null?r.stake_cheio:r.stake;}",
     "function stakeCheio(r){return r.stake;}"),
    ("a edição volta a mostrar o dinheiro real", "apostas",
     "  if(c==='stake')return String(stakeCheio(r));\n", ""),
    ("a Base Completa exibe o dinheiro real", "apostas",
     "${df('stake')}>${fmtR(stakeCheio(r))}", "${df('stake')}>${fmtR(r.stake)}"),
    ("Em Aberto exibe o dinheiro real", "abertas",
     "${df('stake')}>${fmtR(stakeCheio(r))}</div>", "${df('stake')}>${fmtR(r.stake)}</div>"),
    ("a assinatura de stakes usa o dinheiro real", "gestao",
     "a.stakes[stakeCheio(r)]=(a.stakes[stakeCheio(r)]||0)+1;", "a.stakes[r.stake]=(a.stakes[r.stake]||0)+1;"),
]


@pytest.mark.parametrize("titulo,arq,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_do_front_sao_detectadas(tmp_path, titulo, arq, de, para):
    alvo = ARQS[arq]
    src = alvo.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única no {alvo.name} ({src.count(de)})"
    estragado = tmp_path / alvo.name
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    env = {**os.environ, f"ALVO_{arq.upper()}": str(estragado)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, f"a mutação «{titulo}» passou despercebida\n" + (r.stdout or "")


def test_o_feed_manda_a_freebet_so_nas_linhas_que_tem():
    repo = (RAIZ / "app" / "repository.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert ('            _fb = _freebet_valida(r.get("stake_freebet"), stake)\n'
            '            if _fb:\n'
            '                linha["stake_freebet"] = _fb\n') in repo


def test_o_cache_dos_scripts_foi_renovado():
    """Sem o `?v=` novo, o navegador segue com o app.js velho e a freebet não chega à tela."""
    import re
    html = (RAIZ / "app" / "static" / "dash" / "index.html").read_text(encoding="utf-8")
    # PELO MENOS a versão da s392: um bump posterior (s398 subiu o gestao.js) também serve.
    for arq, minimo in (("charts/gestao.js", 55), ("charts/apostas.js", 28),
                        ("charts/abertas.js", 5), ("assets/js/app.js", 67)):
        m = re.search(re.escape(arq) + r"\?v=(\d+)", html)
        assert m and int(m.group(1)) >= minimo, f"{arq} abaixo de ?v={minimo}"
