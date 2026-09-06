"""O multiselect tem de INVALIDAR o recorte cacheado (s322).

Sintoma medido pelo Feca na Base Completa: selecionar `Tipster: Fatuch` deixava o chip
"TIPSTER Fatuch" em Filtros ativos, o contador seguia em "336 de 336" e a tabela
continuava listando MarcoF1, LBB e F1DP. Nenhum erro, nenhum aviso — o filtro
simplesmente não filtrava.

A causa é de forma, não de regra. O `_filterCache` (filters.js) é indexado por página,
mas as entradas dele — o `gfs` do período e os Sets do `MSS` — mudam por fora dele. Até
a s317 isso nunca aparecia porque o único caminho de volta era o `renderPage`, que zera o
cache na primeira linha: todo multiselect caía no `_renderPageDebounced`. A s317 deu à
Base Completa uma barra própria, cujos multiselects repintam só aquela tela (`cb`), e
`applyMS → renderApostas` passou a ler o recorte anterior à seleção.

A correção mora no MUTADOR do estado (`msToggle`), não em cada chamador: quem escrever a
próxima tela com `cb` próprio não precisa saber que existe cache. É a mesma família de
"blindar metade dos campos é pior que blindar todos ou nenhum" — o `apostasTirarMS` já
contornava o problema chamando `renderPage`, e foi justamente o caminho SEM contorno (o
botão OK do dropdown) que mentiu.

A prova de COMPORTAMENTO roda em `tests/js/filtro_multiselect_cache.mjs`, que recorta e
executa o `filtrarPagina`, o `MSS` e o `msToggle` reais. O que ele não cobre está no
cabeçalho do .mjs (o DOM, o debounce, a escolha de quem repinta).

Provado por mutação: 3/3 detectadas — invalidação removida (reproduz o sintoma exato:
5 de 5 linhas, todos os tipsters), invalidação depois do `return` do `__all__` (o
"Limpar" para de voltar atrás) e cache removido de vez (some a garantia de reuso).
"""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FILTERS_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "filters.js"
APOSTAS_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "apostas.js"


def test_msToggle_invalida_o_cache_antes_de_qualquer_ramo():
    """A linha tem de ser a PRIMEIRA do corpo: o ramo do `__all__` sai por um `return`
    mais cedo, e invalidar depois dele deixaria o "Limpar" sem efeito."""
    corpo = ""
    for linha in FILTERS_JS.read_text(encoding="utf-8").split("\n"):
        if linha.startswith("function msToggle("):
            corpo = linha
            break
    assert corpo, "msToggle sumiu do filters.js"
    abre = corpo.index("{") + 1
    assert corpo[abre:].lstrip().startswith("_filterCache={}"), (
        "msToggle deixou de zerar o _filterCache logo na entrada — selecionar no "
        f"multiselect volta a não filtrar nada. Corpo: {corpo[abre:abre + 60]!r}"
    )


def test_a_tela_nao_precisa_mais_contornar_o_cache():
    """O `apostasTirarMS` mantinha DOIS caminhos de repintura só por causa do cache
    (`renderPage` para os eixos da página, `renderApostas` para o eixo local). Contorno
    em um chamador é o que esconde o defeito no outro — foi o caminho sem contorno (o
    botão OK do dropdown) que mentiu na tela."""
    src = APOSTAS_JS.read_text(encoding="utf-8")
    corpo = src[src.index("function apostasTirarMS("):src.index("function apostasTirarTexto(")]
    codigo = "\n".join(l for l in corpo.split("\n") if not l.strip().startswith("//"))
    assert "renderPage(" not in codigo, (
        "voltou o contorno por renderPage no apostasTirarMS — sinal de que a "
        "invalidação saiu do msToggle"
    )
    assert "renderApostas()" in codigo, "o apostasTirarMS parou de repintar a tela"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_da_invalidacao():
    """`tests/js/filtro_multiselect_cache.mjs` executa o código real de filters.js:
    seleciona um tipster sem passar pelo `renderPage` e confere que o recorte muda."""
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "filtro_multiselect_cache.mjs")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
