"""SharpenUp 0.7.89 (s460): fila de envios pendentes (plano 7.2), janela da captura pelo
servidor (7.6) e rodada parcial declarada (6.5).

A prova de COMPORTAMENTO roda em `tests/js/fila_pendente_extensao.mjs`, que executa os trechos
reais do `content.js` e do `popup.js`. Aqui: o .mjs fica verde no código de hoje, e VERMELHO em
cada mutação (aplicada numa cópia, o arquivo real não é tocado).

NÃO cobre: o fluxo da página e o HTML do popup (ver o cabeçalho do .mjs).
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
MJS = RAIZ / "tests" / "js" / "fila_pendente_extensao.mjs"
CONTENT = RAIZ / "extensor" / "content.js"
POPUP = RAIZ / "extensor" / "popup.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")


def _rodar(env_extra=None):
    env = dict(os.environ, **(env_extra or {}))
    return subprocess.run(["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
                          env=env, timeout=60)


def test_prova_por_execucao():
    r = _rodar()
    assert r.returncode == 0, r.stdout + r.stderr


MUTACOES = [
    ("slot único: a 2ª rodada apaga a 1ª", "CONTENT",
     "      fila.push(item);\n", "      fila.length = 0; fila.push(item);\n"),
    ("descartado pelo teto some calado", "CONTENT",
     "      if (descartados) novo.pendDescartados", "      if (false) novo.pendDescartados"),
    ("janela ignora o servidor", "CONTENT",
     "Number(cfg.lookbackDias) || 30, hzDias);", "Number(cfg.lookbackDias) || 30);"),
    ("janela aceita horizonte de outra conta", "CONTENT",
     "hz.casa === cfg.casa && hz.parceiro === cfg.parceiro &&", "hz.casa === cfg.casa &&"),
    ("dica de login vira parcial", "CONTENT",
     "!/fa[çc]a login|recarregue|abra |espere a p[áa]gina/i.test(diag.extra))",
     "true)"),
    ("Reenviar ignora a conta", "POPUP",
     "(!p.parceiro || p.parceiro === (st.parceiro || \"\"))", "true"),
    ("vencida some sem contar", "POPUP",
     "(raw.pendDescartados || 0) + vencidas.length", "(raw.pendDescartados || 0)"),
]


@pytest.mark.parametrize("nome,alvo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacao_deixa_vermelho(tmp_path, nome, alvo, de, para):
    fonte = CONTENT if alvo == "CONTENT" else POPUP
    txt = fonte.read_text(encoding="utf-8")
    assert txt.count(de) == 1, f"alvo da mutação não achado: {de!r}"
    copia = tmp_path / fonte.name
    copia.write_text(txt.replace(de, para), encoding="utf-8")
    r = _rodar({f"ALVO_{alvo}": str(copia)})
    assert r.returncode != 0, f"mutação '{nome}' passou verde:\n{r.stdout}"
