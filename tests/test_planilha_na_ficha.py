"""s450: casa com Ficha recusa print e PDF, mas a PLANILHA (.csv/.xls) continua pela caixa da
tela (Feca, 12/11/2026: "a planilha NÃO entra no bloqueio. O pedido é só print e PDF").

Gates:

1. `tests/js/planilha_na_ficha.mjs` por execução: `aplicarBloqueioPrint`, `ehPlanilha`,
   `separarPelaFicha` e `receberArquivos`, recortados do `index.html`.
2. Os ouvintes da caixa (clique, arrasto, seletor) passam pelo `receberArquivos` e o clique
   não é mais barrado: conferido por presença, porque o `.mjs` não monta o DOM inteiro.
3. O servidor aceita planilha na casa com Ficha (o `/extrair` REAL, com a IA dublada).
4. Mutações sobre cópia do `index.html`, todas detectadas.

O QUE NÃO COBREM: o arrasto e o seletor de arquivo de verdade (medidos em headless na s450) e
o desenho.
"""
import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
MJS = RAIZ / "tests" / "js" / "planilha_na_ficha.mjs"
INDEX = RAIZ / "app" / "static" / "index.html"


def _idx():
    return INDEX.read_text(encoding="utf-8").replace("\r\n", "\n")


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_front_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


OUVINTES = [
    "dropZone.addEventListener('click', () => fileInput.click());",
    "dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag'); });",
    "  receberArquivos([...e.dataTransfer.files]);\n",
    "fileInput.addEventListener('change', () => { receberArquivos([...fileInput.files]); fileInput.value = ''; });",
]


def _checar_ouvintes(src):
    for o in OUVINTES:
        assert src.count(o) == 1, f"ouvinte fora do lugar: {o!r}"
    assert "adicionarArquivos([...e.dataTransfer.files])" not in src
    assert "adicionarArquivos([...fileInput.files])" not in src


def test_os_ouvintes_da_caixa_passam_pelo_filtro_da_ficha():
    _checar_ouvintes(_idx())


def test_o_servidor_aceita_planilha_na_casa_com_ficha(monkeypatch):
    """O `/extrair` não barra CSV na casa com Ficha: a planilha segue para a leitura."""
    import main
    chamadas = []

    def _duble(*a, **kw):
        chamadas.append(kw.get("caminho"))

        async def _vazio():
            yield "data: {}\n\n"
        return _vazio()

    async def _predup(texto, *a, **kw):
        return texto, 0
    monkeypatch.setattr(main, "_stream_sequential", _duble)
    monkeypatch.setattr(main, "_stream_parallel", _duble)
    monkeypatch.setattr(main, "_dedup_superbet_text", _predup)
    monkeypatch.setattr(main.auth_mod, "eh_trial", lambda d: False)
    asyncio.run(main.extrair(
        casa="Thunderpick", parceiro="conta [Op]", modelo=main.DEFAULT_MODEL, texto=None,
        csv_content="Data,Evento,Stake,Odd,Resultado\n10/11/2026,A x B,10,2.00,Ganhou\n",
        imagens=[], pdfs=[], xls_file=None, data_referencia=None, dono="TDonoPlan"))
    assert chamadas, "a planilha não chegou à leitura"


MUTACOES = [
    ("a planilha volta a ser barrada",
     "  const aceitos = files.filter(ehPlanilha);", "  const aceitos = [];"),
    ("o .xls deixa de contar como planilha",
     "/\\.(csv|xls|xlsx)$/i.test(f.name)", "/\\.(csv)$/i.test(f.name)"),
    ("a casa com Ficha aceita tudo",
     "  if (!printBloqueado()) return { aceitos: files, recusados: 0 };",
     "  if (true) return { aceitos: files, recusados: 0 };"),
    ("o seletor segue oferecendo print",
     "  fi.accept = trava ? ACCEPT_PLANILHA : fi.dataset.orig;",
     "  fi.accept = fi.dataset.orig;"),
    ("a recusa não avisa",
     "  if (recusados) setStatus(MSG_PRINT_BLOQUEADO, 'warn');", ""),
    ("o clique volta a ser barrado",
     "dropZone.addEventListener('click', () => fileInput.click());",
     "dropZone.addEventListener('click', () => { if (!printBloqueado()) fileInput.click(); });"),
    ("o arrasto pula o filtro",
     "  receberArquivos([...e.dataTransfer.files]);\n",
     "  adicionarArquivos([...e.dataTransfer.files]);\n"),
]


def _detecta(tmp_path, src_mutado):
    estragado = tmp_path / "index.html"
    estragado.write_text(src_mutado, encoding="utf-8")
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
                       cwd=str(RAIZ), env={**os.environ, "ALVO_INDEX": str(estragado)})
    if r.returncode != 0:
        return True
    try:
        _checar_ouvintes(src_mutado)
        return False
    except AssertionError:
        return True


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    src = _idx()
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única ({src.count(de)})"
    assert _detecta(tmp_path, src.replace(de, para, 1)), f"a mutação «{titulo}» passou despercebida"
