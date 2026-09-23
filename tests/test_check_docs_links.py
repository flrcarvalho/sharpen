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

**A regra que ficou:** link que sai da raiz do repo **nunca reprova, e sempre é RELATADO**.
Resolve nesta máquina ⇒ conferido. Não resolve ⇒ sai NOMEADO na lista de "não conferíveis
daqui". O gate deixa de depender de onde roda, e quem lê a saída vê quais links aquela
máquina não pôde julgar.

⚠️ **Duas tentativas mais espertas falharam antes desta, e as duas estão travadas aqui:**

  1. Olhar só o ARQUIVO: ausente virava "fora de escopo" sempre, e um `../pack/CLAUDEE.md`
     escrito errado passava em silêncio em toda máquina. Trocar um alarme que toca sempre
     por um alarme mudo não é conserto.
  2. Olhar a PASTA do alvo ("se a pasta existe, dá para julgar"): parece certo e quebra no
     caso mais simples. `CLAUDE.md -> ../CLAUDE.md` tem como pasta o **diretório acima do
     repo**, que existe em toda máquina, inclusive no runner do CI. O gate julgou, não
     achou o arquivo e reprovou, que é exatamente o falso vermelho que ele existe para
     acabar. **Foi este arquivo de teste que pegou, no CI, na primeira execução.**

Detectar erro de digitação FORA do repo exige saber que aquela pasta irmã deveria estar
ali, e isso o repo não sabe de dentro. Fica relatado, não adivinhado.

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
    ("link interno certo", "./X.md", False, False),
    ("externo, pasta irmã AUSENTE (o caso do CI)", "../../pack/CLAUDE.md", False, False),
    ("externo, pasta irmã PRESENTE, arquivo errado", "../../pack/CLAUDEE.md", True, False),
    ("externo, pasta irmã PRESENTE, arquivo certo", "../../pack/CLAUDE.md", True, False),
    # O caso que derrubou o CI na 1a versão: a pasta do alvo é o diretório ACIMA do repo,
    # que existe em TODA máquina. Qualquer heurística baseada na pasta reprova aqui.
    ("externo um nível acima, arquivo ausente", "../../CLAUDE.md", False, False),
])
def test_as_situacoes_de_link(tmp_path, capsys, nome, alvo, com_irma, reprova):
    mod, md = _montar(tmp_path, alvo, com_irma)
    mod.checar_links([md])
    capsys.readouterr()
    assert bool(mod.falhas) is reprova, (
        f"{nome}: esperava reprovar={reprova}, veio {bool(mod.falhas)}. "
        f"Falhas: {mod.falhas}"
    )


def test_link_de_fora_que_nao_resolve_sai_NOMEADO(tmp_path, capsys):
    """Não reprovar não pode virar ignorar em silêncio.

    O nome do link é a única pista que alguém tem de um `../pack/CLAUDEE.md` escrito
    errado. Sem ele o conserto teria trocado o falso vermelho por um ponto cego.
    """
    mod, md = _montar(tmp_path, "../../pack/CLAUDEE.md", com_irma=True)
    mod.checar_links([md])
    saida = capsys.readouterr().out
    assert not mod.falhas, "link de fora não pode reprovar o gate"
    assert "CLAUDEE.md" in saida, (
        "o link de fora que não resolve precisa aparecer NOMEADO na saída; "
        "contagem sozinha vira ignorado em silêncio."
    )


def test_o_tamanho_nao_muda_com_a_quebra_de_linha(tmp_path):
    """O mesmo arquivo tem de dar o MESMO tamanho no Windows e no runner do CI.

    Medido na s385: o `CLAUDE.md` dava **64,03 KB no disco do Feca** (LF) e **65,04 KB no
    checkout do CI** (CRLF), diferença de 1.035 bytes, exatamente um por linha. O teto é
    65 KB, então o mesmo arquivo passava aqui e reprovava lá.

    O efeito é o pior possível para um teto: quem edita local lê "sobra 1 KB" e não sobra.
    O CI reprova depois, longe de quem escreveu, e a leitura natural é "o gate está maluco".
    """
    mod = _carregar(tmp_path)
    corpo = "linha de exemplo\n" * 500
    lf = tmp_path / "lf.md"
    crlf = tmp_path / "crlf.md"
    lf.write_bytes(corpo.encode("utf-8"))
    crlf.write_bytes(corpo.replace("\n", "\r\n").encode("utf-8"))

    assert crlf.stat().st_size > lf.stat().st_size, (
        "o caso não foi montado: os dois arquivos precisam diferir em BYTES crus, "
        "senão o teste passa sem exercer nada."
    )
    assert mod._kb(lf) == mod._kb(crlf), (
        f"o gate mede {mod._kb(lf):.3f} KB com LF e {mod._kb(crlf):.3f} KB com CRLF. "
        "O mesmo arquivo passa numa máquina e reprova na outra."
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
