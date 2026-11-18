"""Processar automático da captura (s460, plano 6.6, pedido do Feca em 18/11/2026).

A prova de COMPORTAMENTO roda em `tests/js/processar_auto_captura.mjs`, que executa o trecho
real do `index.html` (fila de confirmação, Processar automático e poll). Aqui: o .mjs fica
verde no código de hoje, e VERMELHO em cada mutação (aplicada numa cópia; o arquivo real não
é tocado).

NÃO cobre: o `runExtractionCard` (o clique é dublado) e a aparência do `#ext-status`.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
MJS = RAIZ / "tests" / "js" / "processar_auto_captura.mjs"
INDEX = RAIZ / "app" / "static" / "index.html"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")


def _rodar(env_extra=None):
    env = dict(os.environ, **(env_extra or {}))
    return subprocess.run(["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
                          env=env, timeout=60)


def test_prova_por_execucao():
    r = _rodar()
    assert r.returncode == 0, r.stdout + r.stderr


MUTACOES = [
    ("nunca dispara", "  document.getElementById('btn-extrair').click();\n}", "}"),
    ("ignora a conta da conexão",
     "if (e.selecionado !== e.sessao || e.lote.parceiro_id !== e.sessao) return 'outra-conta';", ""),
    ("ignora o que o usuário mexeu",
     "if (e.texto !== e.lote.texto || e.n_arquivos !== e.lote.n_arquivos || e.outros > 0) return 'mexeu';", ""),
    ("não espera o processamento anterior", "  if (e.processando) return 'esperar';\n", ""),
    ("texto colado antes conta como captura", "const eraSoCaptura = !_lotePrevio.temAlgo",
     "const eraSoCaptura = true"),
    ("cada captura agenda sem cancelar a anterior",
     "  clearTimeout(_extAutoTimer);\n  _extAutoTimer = setTimeout", "  _extAutoTimer = setTimeout"),
    ("a tela não pede o clique quando não dispara",
     "if (v === 'mexeu' || v === 'outra-conta') extStatus(", "if (false) extStatus("),
]


@pytest.mark.parametrize("nome,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacao_deixa_vermelho(tmp_path, nome, de, para):
    txt = INDEX.read_text(encoding="utf-8")
    assert txt.count(de) == 1, f"alvo da mutação não achado: {de!r}"
    copia = tmp_path / "index.html"
    copia.write_text(txt.replace(de, para), encoding="utf-8")
    r = _rodar({"ALVO_INDEX": str(copia)})
    assert r.returncode != 0, f"mutação '{nome}' passou verde:\n{r.stdout}"
