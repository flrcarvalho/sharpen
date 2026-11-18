"""Tela da aposta excluída que volta pela captura (s460, Feca 18/11/2026).

A prova de COMPORTAMENTO roda em `tests/js/excluida_que_volta.mjs`, que executa o trecho real
do `index.html`. Aqui: o .mjs fica verde no código de hoje e VERMELHO em cada mutação (numa
cópia; o arquivo real não é tocado). E a fiação da pílula: o filtro dela é o mesmo predicado
do número (`voltou`), e a barra de decisão existe.

NÃO cobre: o desenho do selo e da barra (conferido em headless) e o modal de liberar.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
MJS = RAIZ / "tests" / "js" / "excluida_que_volta.mjs"
INDEX = RAIZ / "app" / "static" / "index.html"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")


def _rodar(env_extra=None):
    env = dict(os.environ, **(env_extra or {}))
    return subprocess.run(["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
                          env=env, timeout=60)


def test_prova_por_execucao():
    r = _rodar()
    assert r.returncode == 0, r.stdout + r.stderr


def test_pilula_filtra_pelo_mesmo_predicado_do_numero():
    txt = INDEX.read_text(encoding="utf-8")
    assert "'s-voltou': 'voltou'" in txt
    assert "_statBadge('s-voltou', (voltaramPorParceiro[casa] || {})[nome] || 0, filtroGrade === 'voltou')" in txt
    assert 'id="voltou-barra"' in txt and 'id="devez-modal"' in txt


MUTACOES = [
    ("manter não manda os ids", "    : { ids };", "    : {};"),
    ("todas não manda a conta", "? { casa: parceiroSelecionado.casa, parceiro: parceiroSelecionado.nome }",
     "? { ids: [] }"),
    ("excluir de vez sem perguntar",
     "  if (!confirm(`Excluir de vez ${qual}?", "  if (false && !confirm(`Excluir de vez ${qual}?"),
    ("não recarrega depois de excluir",
     "excluída${d.excluidas === 1 ? '' : 's'} de vez`, 'ok');\n    await carregarGrade();",
     "excluída${d.excluidas === 1 ? '' : 's'} de vez`, 'ok');\n    await 0;"),
    ("erro engolido", "  if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`);\n  return d;", "  return d;"),
]


@pytest.mark.parametrize("nome,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacao_deixa_vermelho(tmp_path, nome, de, para):
    txt = INDEX.read_text(encoding="utf-8")
    assert txt.count(de) == 1, f"alvo da mutação não achado: {de!r}"
    copia = tmp_path / "index.html"
    copia.write_text(txt.replace(de, para), encoding="utf-8")
    r = _rodar({"ALVO_INDEX": str(copia)})
    assert r.returncode != 0, f"mutação '{nome}' passou verde:\n{r.stdout}"
