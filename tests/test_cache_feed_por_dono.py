"""O cache do feed no navegador é de UMA identidade (s459, auditoria de 17/11, NAVEGADOR C3/M3).

A prova de COMPORTAMENTO roda em `tests/js/cache_feed_por_dono.mjs`, que executa as
funções RECORTADAS do `app.js` de produção. Aqui ela roda, e cada mutação abaixo estraga
uma cópia do `app.js` e exige que o .mjs fique VERMELHO.

O que NÃO está coberto: o IndexedDB de verdade e a ordem de pintura do `loadData`.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"
MJS = RAIZ / "tests" / "js" / "cache_feed_por_dono.mjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")


def _roda(env=None):
    return subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                          encoding="utf-8", cwd=str(RAIZ), env=env)


def test_prova_por_execucao():
    r = _roda()
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# Mutações INÓCUAS, medidas e registradas (não são buraco de teste):
# - tirar o usuário real da chave: o dado é o MESMO quando o supervisor vê o operador e
#   quando o operador vê a própria base (o dono efetivo é quem decide o conteúdo). Ele
#   fica na chave por defesa, não por regra.
# - tirar o `if(!r.ok)return null;`: a resposta de erro não traz `usuario`, e a linha
#   seguinte já devolve null.
MUTACOES = [
    ("a chave perde o dono efetivo",
     "return 'dados_v2::'+m.usuario+'>'+(m.dono_efetivo||m.usuario);",
     "return 'dados_v2::'+m.usuario;"),
    ("o cache de outra identidade volta a pintar",
     "c.chave===chave&&", ""),
    ("o esquema deixa de ser conferido",
     "c.schema===_IDB_SCHEMA&&", ""),
    ("cache de meses atras volta a pintar",
     "&&(agora-c.savedAt)<_IDB_MAX_IDADE_MS", ""),
]


@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    src = APP.read_text(encoding="utf-8")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única ({src.count(de)})"
    estragado = tmp_path / "app.js"
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    r = _roda({**os.environ, "ALVO_APP": str(estragado)})
    assert r.returncode != 0, f"a mutação «{titulo}» passou despercebida.\n" + (r.stdout or "")
