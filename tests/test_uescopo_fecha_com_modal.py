"""O escopo de unidade é do MODAL do tipster e morre junto com ele (s383).

Relato do Ewanderson1, sobre o calendário da aba Resultados: *"Era p ser, mas eu n fiz
2.041u no dia 15"*. A base dele é em R$ (1u = R$ 50) e o número era R$ 2.041 com um "u"
colado. O `renderTipsterDrill` liga `_uEscopo` com o switch da tela Tipsters em u; a
linha que o desligava estava no `closeCasaDrill`, que nunca liga nada. Fechado o modal,
todo componente compartilhado que pergunta `emUnidades()` (calendário, Dia da Semana)
seguia escrevendo "u" sobre valor em reais, até recarregar a página.

A prova de COMPORTAMENTO roda em `tests/js/uescopo_fecha_com_modal.mjs`, sobre o código
RECORTADO do `app.js` e do `performance.js` de produção. Este arquivo a invoca e depois
a prova por MUTAÇÃO.

O que NÃO está coberto: o `renderTipsterDrill` ligando o escopo (preso ao DOM; no .mjs o
"aberto em u" é estado de partida) e o render real no navegador.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"
PERF = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "performance.js"
MJS = RAIZ / "tests" / "js" / "uescopo_fecha_com_modal.mjs"


def _node(env_extra=None):
    return subprocess.run(
        ["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
        cwd=str(RAIZ), env={**os.environ, **(env_extra or {})},
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_escopo_de_unidade():
    r = _node()
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


REDE = "  if(!_tdo||_tdo.style.display!=='flex')_uEscopo=false;"

# (arquivo, título, de, para). A âncora é conferida como ÚNICA antes de mutar: mutação
# que não acerta o alvo passa verde com razão, e o verde é falso.
MUTACOES = [
    (
        "performance.js",
        "fechar o modal do tipster volta a nao desligar o escopo (o defeito original)",
        "  _uEscopo=false;\n  if(_drillEscHandler)",
        "  if(_drillEscHandler)",
    ),
    (
        "app.js",
        "a rede do renderPage deixa de existir",
        REDE,
        "  if(false)_uEscopo=false;",
    ),
    (
        "app.js",
        "a rede desliga o escopo mesmo com o modal ABERTO",
        REDE,
        "  _uEscopo=false;",
    ),
    (
        "app.js",
        "pagina sem o overlay no DOM mantem o escopo ligado",
        REDE,
        "  if(_tdo&&_tdo.style.display!=='flex')_uEscopo=false;",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("arquivo,titulo,de,para", MUTACOES, ids=[m[1] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, arquivo, titulo, de, para):
    """Quebra o código de propósito e exige que o .mjs fique VERMELHO."""
    origem = APP if arquivo == "app.js" else PERF
    src = origem.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no {arquivo} "
        f"({src.count(de)} ocorrência(s)); atualize a lista MUTACOES"
    )
    estragado = tmp_path / arquivo
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    chave = "ALVO_APP" if arquivo == "app.js" else "ALVO_PERF"

    r = _node({chave: str(estragado)})
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida: o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )
