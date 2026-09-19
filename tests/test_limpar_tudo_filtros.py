"""O "Limpar tudo" em TODA barra de filtros (s374).

Sugestão do tester João: *"adicionar o botão de 'limpar tudo' existente no BASE
COMPLETA nos demais módulos de relatório"*. O Feca ampliou: onde não existir, inserir.

Ele virou peça da barra (`_grupoLimpar`, em `filters.js`), então as telas que montam
barra o ganham juntas: Visão Geral, Resultados, Esportes, Bookies, Tipsters,
Fornecedores, Métricas (via `buildFilters`), Em Aberto (`buildFiltersSemData`), Custos
(`buildFiltersCustos`) e Painel de Contas (`buildFiltrosContas`). A Base Completa mantém
o dela, na faixa de filtros ativos: dois botões do mesmo papel na mesma tela é o sintoma
de "fora do padrão" que o item 8 do `/nova-ui` manda evitar.

A prova de COMPORTAMENTO roda em `tests/js/limpar_tudo_filtros.mjs`, que executa as
funções RECORTADAS do `filters.js` de produção. Este arquivo a invoca e depois a prova
por MUTAÇÃO (ver `test_mutacoes_sao_detectadas`).

O que NÃO está coberto aqui:
  · a POSIÇÃO do botão e o CSS. O `[hidden]` explícito só é exercido no navegador
    (`display:flex` do `.filter-group` vence o atributo), e isso foi medido em headless
    nas 10 telas contra o `servidor_demo`: escondido na tela limpa, aceso com filtro,
    e o clique devolvendo período e eixos ao estado inicial;
  · o repaint real: `renderPage` é dublado no .mjs, então o que se conta ali é quantas
    vezes a tela SERIA repintada, não o que aparece nela.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
DASH = RAIZ / "app" / "static" / "dash"
FILTERS = DASH / "assets" / "js" / "filters.js"
MJS = RAIZ / "tests" / "js" / "limpar_tudo_filtros.mjs"


def _node(env_extra=None):
    return subprocess.run(
        ["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
        cwd=str(RAIZ), env={**os.environ, **(env_extra or {})},
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_limpar_tudo():
    r = _node()
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES = [
    (
        "os eixos voltam a ser casados por sufixo (a pagina vizinha e' limpa junto)",
        "function _eixosDaPagina(p){const re=new RegExp('^[a-z]{2}_'+p+'$');return Object.keys(MSS).filter(id=>re.test(id));}",
        "function _eixosDaPagina(p){return Object.keys(MSS).filter(id=>id.endsWith('_'+p));}",
    ),
    (
        "eixo selecionado deixa de acender o botao",
        "  if(_eixosDaPagina(p).some(id=>MSS[id]&&MSS[id].size>0))return true;",
        "",
    ),
    (
        "periodo deixa de acender o botao",
        "  if(_periodoLigado(p))return true;",
        "",
    ),
    (
        "o filtro LOCAL da tela deixa de contar",
        "  const ex=LIMPAR_EXTRA[p];\n  return !!(ex&&ex.ativo&&ex.ativo());",
        "  return false;",
    ),
    (
        "o periodo PADRAO da tela passa a contar como filtro ligado",
        "  if(padrao)return st.qt!==padrao||st.qd>0||(st.monthOff||0)!==0;",
        "",
    ),
    (
        "limpar deixa de zerar o filtro LOCAL da tela",
        "  const ex=LIMPAR_EXTRA[p];\n  if(ex&&ex.limpar)ex.limpar();",
        "",
    ),
    (
        "limpar leva a tela de Custos para o vazio em vez do mes",
        "  if(padrao)setQuickType(p,padrao);else clearDate(p);",
        "  clearDate(p);",
    ),
    (
        "limpar deixa de zerar os eixos",
        "    msToggle(id,'__all__');\n    refreshMS(id);",
        "",
    ),
    (
        "cada eixo limpo repinta a tela (a tela pisca com o recorte pela metade)",
        "    refreshMS(id);\n  });",
        "    refreshMS(id);renderPage(p);\n  });",
    ),
    (
        "o botao nasce sempre visivel, mesmo com a tela limpa",
        "${temFiltroAtivo(p)?'':' hidden'}",
        "",
    ),
    (
        "o sync para de mexer no botao",
        "  if(el)el.hidden=!temFiltroAtivo(p);",
        "",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    """Quebra o filters.js de propósito e exige que o .mjs fique VERMELHO."""
    src = FILTERS.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no filters.js "
        f"({src.count(de)} ocorrência(s)); atualize a lista MUTACOES"
    )
    estragado = tmp_path / "filters.js"
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")

    r = _node({"ALVO_FILTERS": str(estragado)})
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida: o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )


def test_toda_barra_de_filtros_oferece_o_botao():
    """FORMA: as quatro funções que montam barra chamam a peça.

    É o que impede a próxima tela de nascer sem o botão, que era exatamente a queixa
    do tester. Um grep pega a REMOÇÃO; não prova comportamento.
    """
    src = FILTERS.read_text(encoding="utf-8")
    assert src.count("${_grupoLimpar(p)}") == 2, (
        "buildFilters e buildFiltersSemData precisam da peça"
    )
    custos = (DASH / "assets" / "js" / "charts" / "custos2.js").read_text(encoding="utf-8")
    assert "${_grupoLimpar(p)}" in custos, "a barra da tela de Custos perdeu o botão"
    contas = (DASH / "assets" / "js" / "charts" / "contas.js").read_text(encoding="utf-8")
    assert "${_grupoLimpar('contas')}" in contas, "a barra do Painel de Contas perdeu o botão"
    assert "LIMPAR_EXTRA.contas" in contas, (
        "sem o registro do seg de População, o botão limparia metade da tela de Contas"
    )
    apostas = (DASH / "assets" / "js" / "charts" / "apostas.js").read_text(encoding="utf-8")
    assert "clearApostasFilters()" in apostas and "_grupoLimpar" not in apostas, (
        "a Base Completa mantém o botão dela (na faixa de filtros ativos); dois botões do "
        "mesmo papel na mesma tela é o que o item 8 do /nova-ui manda evitar"
    )


def test_o_estado_do_botao_e_sincronizado_nos_dois_caminhos():
    """Período e multiselect são as DUAS portas que mudam filtro.

    Pendurar o sync em cada setter deixaria o próximo de fora, calado: ele mora no
    `rqb` (por onde todo setter de período passa) e no `refreshMS` (por onde toda
    mudança de seleção passa, inclusive a das telas com `cb` próprio).
    """
    src = FILTERS.read_text(encoding="utf-8")
    rqb = src[src.index("function rqb(p){"):]
    rqb = rqb[:rqb.index("\n}\n")]
    assert "_syncLimparTudo(p)" in rqb, "o rqb parou de sincronizar o botão"
    refresh = src[src.index("function refreshMS(id){"):]
    refresh = refresh[:refresh.index("\n}\n")]
    assert "_syncLimparTudo(pg)" in refresh, "o refreshMS parou de sincronizar o botão"


def test_o_hidden_do_botao_tem_display_none_explicito():
    """`display:flex` vence o atributo `hidden` (CLAUDE.md).

    O wrapper é `.filter-group`, que é `display:flex`. Sem esta regra o botão ficaria
    visível o tempo todo, e o `hidden` do markup não diria nada.
    """
    css = (DASH / "assets" / "css" / "components.css").read_text(encoding="utf-8")
    assert ".filters__limpar[hidden] { display: none; }" in css
    assert ".filters__limpar { margin-left: auto;" in css
