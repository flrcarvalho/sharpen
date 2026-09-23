"""O conferidor de links deixava o CI cronicamente VERMELHO por link legítimo (s385).

`check_docs.py` acusava 5 links quebrados no CI e **nenhum deles era quebrado**: apontam
para `../pack/…`, a pasta IRMÃ, que existe na máquina do Feca e **nunca** existe no
checkout, porque o repo publicado é só o `Planilhador/`. A falha era a mesma em toda
execução, de sessões diferentes (era o item 1.7 do BACKLOG).

O custo não era cosmético. **CI cronicamente vermelho não é gate:** ninguém distingue a
falha nova da de sempre, e uma quebra REAL (um kwarg colidindo num teste) já passou
despercebida até alguém abrir o log à mão. Foi por isso que consertar isto virou o passo
seguinte a ligar os dois gates da captura no CI: alarme novo num painel que já pisca
vermelho não alerta ninguém.

**A regra que ficou, e ela tem duas metades:** link que sai da raiz do repo só é julgado
quando dá para julgar, e o critério é a PASTA do alvo, não o arquivo.

  · pasta existe aqui (dev)  ⇒ dá para julgar; arquivo ausente é erro de digitação e REPROVA
  · pasta não existe (CI)    ⇒ não dá para julgar nada; entra como fora de escopo

A segunda metade é o que impede o conserto de virar o defeito oposto. A primeira versão
olhava só o ARQUIVO, e com ela um `../pack/CLAUDEE.md` escrito errado passava em silêncio
em toda máquina. **Ajustar um gate para parar de gritar não pode transformá-lo em gate que
nunca fala** — e este teste existe porque essa troca é fácil de fazer sem perceber.

**O que este teste NÃO cobre:** as âncoras (`#secao`), que têm checagem própria; os tetos
de tamanho; e a varredura de `Backups/`.
"""
import importlib.util
import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CHECK_DOCS = RAIZ / "tools" / "check_docs.py"


def _carregar(raiz_falsa: Path):
    """Importa o `check_docs` apontando o RAIZ para um repo de mentira.

    Cada caso recebe a sua própria instância: o módulo guarda as falhas numa lista de
    nível de módulo, e reaproveitá-la faria um caso enxergar a falha do anterior.
    """
    spec = importlib.util.spec_from_file_location(f"check_docs_{raiz_falsa.name}", CHECK_DOCS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.RAIZ = str(raiz_falsa.resolve())
    mod.falhas = []
    return mod


def _montar(tmp_path: Path, alvo: str, com_irma: bool) -> tuple:
    """Monta a MESMA forma do real: raiz `Planilhador/` e pasta irmã `pack/` ao lado."""
    raiz = tmp_path / "Planilhador"
    (raiz / "docs").mkdir(parents=True)
    if com_irma:
        (tmp_path / "pack").mkdir()
        (tmp_path / "pack" / "CLAUDE.md").write_text("# irma", encoding="utf-8")
    md = raiz / "docs" / "X.md"
    md.write_text(f"veja [isto]({alvo})\n", encoding="utf-8")
    return _carregar(raiz), str(md)


@pytest.mark.parametrize("nome,alvo,com_irma,reprova", [
    ("link interno quebrado", "./naoexiste.md", False, True),
    ("externo, pasta irmã AUSENTE (o caso do CI)", "../../pack/CLAUDE.md", False, False),
    ("externo, pasta irmã PRESENTE, arquivo errado", "../../pack/CLAUDEE.md", True, True),
    ("externo, pasta irmã PRESENTE, arquivo certo", "../../pack/CLAUDE.md", True, False),
])
def test_as_quatro_situacoes_de_link(tmp_path, capsys, nome, alvo, com_irma, reprova):
    mod, md = _montar(tmp_path, alvo, com_irma)
    mod.checar_links([md])
    capsys.readouterr()
    assert bool(mod.falhas) is reprova, (
        f"{nome}: esperava reprovar={reprova}, veio {bool(mod.falhas)}. "
        f"Falhas: {mod.falhas}"
    )


def test_o_repo_de_verdade_passa_e_conta_os_links_de_fora(capsys):
    """No repo real, nenhum link quebrado, e os de fora aparecem NOMEADOS.

    A contagem separada é o que impede o conserto de virar "ignorar silenciosamente":
    quem lê a saída precisa saber que existem links que aquela máquina não conferiu.
    """
    mod = _carregar(RAIZ)
    mds = mod.listar_mds() if hasattr(mod, "listar_mds") else None
    if mds is None:  # varredura própria, se o helper mudar de nome
        mds = [str(p) for p in RAIZ.rglob("*.md")
               if "Backups" not in p.parts and "node_modules" not in p.parts]
    mod.checar_links(mds)
    saida = capsys.readouterr().out
    assert not mod.falhas, f"o repo tem link quebrado de verdade: {mod.falhas}"
    assert "fora da raiz do repo" in saida, (
        "a saída deixou de informar os links que saem da raiz. Contagem escondida vira "
        "'ignorado em silêncio', que é o defeito oposto ao que este conserto resolveu."
    )
