"""Escopo do calendário da Visão Geral (s319) — dois P/L na mesma tela, sem explicação.

Reclamação do Feca, com print: com o período em MTD (01/09 → 05/09) o KPI dizia
`P/L Bruto +R$ 12.033,68 · 483 apostas` e o calendário logo abaixo dizia
`P/L do mês +R$ 11.833 · 487 apostas`. Os dois números estavam certos e mediam coisas
diferentes: o cartão soma o MÊS fechado, os KPIs somam o PERÍODO. A diferença eram
4 bilhetes com data de EVENTO depois do corte — três voids da Bet365 (P/L 0, mas contam)
e uma perdida de R$ 201 no GP da Itália, resolvidos antes do jogo acontecer.

Duas correções, e é o que este arquivo trava:

  1. o calendário recebia `DADOS` **cru** e por isso ignorava também Esporte, Casa,
     Tipster e Operador — escolher um tipster mudava os KPIs de cima e não mudava nada
     no cartão. Agora ele recebe `filtrarSemData('overview')`: os quatro filtros valem,
     só o corte por data não (o cartão é um calendário de mês, com nav própria — mesmo
     motivo do ROI Mensal);
  2. quando o período selecionado não cobre o mês inteiro, o cartão **diz** o que ficou
     de fora, no molde da nota que a página Apostas já usava para os KPIs que não seguem
     o filtro de resultado (a `.apf-nota` virou a `.nota-escopo` compartilhada).

A prova de COMPORTAMENTO roda em `tests/js/calendario_escopo.mjs`, que executa o
`mkCalendarHeatmap` e o `filtrarSemData` RECORTADOS dos arquivos de produção. Este
arquivo o invoca — ver `test_prova_por_execucao_do_escopo`.

Provado por mutação: 9/9 detectadas (nota nunca aparece, comparação de faixa invertida,
P/L da nota em `fmtR` em vez de `fmtPL`, plural cravado, mês selecionado fora da lista
de meses, calendário de volta em `DADOS`, `_ovCalRows` sem filtro, `filtrarSemData`
cortando por data e `filtrarSemData` ignorando o tipster).
"""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
OVERVIEW_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "overview.js"
SHARED_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "shared.js"
APOSTAS_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "apostas.js"
COMPONENTS_CSS = RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css"


def test_calendario_da_visao_geral_nao_recebe_a_base_crua():
    """Regressão direta: `DADOS` ali dentro faz o cartão ignorar os quatro filtros."""
    src = OVERVIEW_JS.read_text(encoding="utf-8")
    assert "mkCalendarHeatmap(window._ovHeatMonth,rows," in src, (
        "o calendário da Visão Geral parou de receber as linhas filtradas"
    )
    assert "mkCalendarHeatmap(window._ovHeatMonth,DADOS," not in src, (
        "o calendário da Visão Geral voltou a receber DADOS cru — os filtros de "
        "esporte/casa/tipster/operador deixam de valer nele"
    )


def test_a_nota_de_escopo_e_uma_so_para_as_duas_telas():
    """Dois estilos para o mesmo papel é o sintoma de 'fora do padrão' (CLAUDE.md §8).
    A nota da página Apostas e a do calendário são a mesma `.nota-escopo`."""
    css = COMPONENTS_CSS.read_text(encoding="utf-8")
    assert ".nota-escopo {" in css, "a .nota-escopo sumiu do components.css"
    assert "\n.apf-nota {" not in css, "a .apf-nota voltou — são dois estilos para o mesmo papel"
    for js in (SHARED_JS, APOSTAS_JS):
        texto = js.read_text(encoding="utf-8")
        assert 'class="nota-escopo"' in texto, f"{js.name} não usa a nota compartilhada"
        assert "apf-nota" not in texto, f"{js.name} voltou à classe antiga"


def test_a_nota_usa_o_fmt_pl_do_padrao_monetario():
    """P/L é `fmtPL` (2 casas, R$ menor/neutro, minus U+2212) — UI_REFERENCE §5.1.
    Formatador caseiro aqui é exatamente o desvio da s83."""
    src = SHARED_JS.read_text(encoding="utf-8")
    assert "${fmtPL(foraPL)}" in src, "o P/L da nota de escopo saiu do fmtPL"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_escopo():
    """`tests/js/calendario_escopo.mjs` executa o `mkCalendarHeatmap` e o
    `filtrarSemData` reais. O que ele NÃO cobre está no cabeçalho do .mjs: o CSS que
    posiciona a nota, o clique das setas ‹ › e o modo público."""
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "calendario_escopo.mjs")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
