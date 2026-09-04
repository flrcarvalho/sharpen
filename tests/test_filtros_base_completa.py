"""Filtros da Base Completa (s317) — o que quebra em SILÊNCIO.

Pedido do tester João Henrique (03/09): *"uma sugestão seria um filtro de resultado
aqui na tela Base Completa. Ajuda bastante para conferir e corrigir valores"*. O Feca
ampliou: os filtros da tela eram pobres — a barra da página (período/esporte/casa/
tipster) mais seis caixas de texto, três delas duplicando com casamento por substring
o multiselect que já existia 20px acima.

A decisão que este arquivo existe para travar não é o filtro, é a régua:

  **O DESFECHO CORTA A TABELA, NÃO A RÉGUA.** Os filtros de texto já mexiam nos KPIs
  (filtrar "Bet365" muda P/L e ROI, e está certo — é recorte de carteira). Fazer o
  mesmo com o resultado seria diferente em natureza: filtrar `W` daria **Win Rate
  100%** e ROI positivo, números certos pela conta e mentirosos pela leitura. Por isso
  os KPIs leem `apostasKpiRows` (o recorte da tela sem o corte por desfecho) e a tabela
  lê `apostasFiltered` — e a tela **diz** isso, numa nota, enquanto o filtro está ligado.
  Trocar uma variável pela outra não gera erro nenhum: só passa a mentir.

Faixa de stake/odd/P/L é recorte como qualquer outro e entra nos KPIs normalmente. A
exceção é a aposta ABERTA numa faixa de P/L: ela não tem P/L, e o zero que o feed traz
a colocaria dentro de toda faixa que cruze o zero.

A prova de COMPORTAMENTO roda em `tests/js/filtros_base_completa.mjs`, que executa o
`parseNum`, os cinco matches, o comparador e o bloco de repartição RECORTADOS dos
arquivos de produção — ver `test_prova_por_execucao_dos_filtros`. O que ele não cobre
está no cabeçalho do .mjs (o DOM dos chips, o debounce, o ICU).

Provado por mutação: 17/17 detectadas (resultado não cortando a tabela, KPI seguindo o
resultado, aberta entrando em faixa de P/L, `>` no lugar de `>=`, teto de faixa perdido,
`parseFloat` no lugar de `parseNum`, faixa vazia virando corte, ordem alfabética do
resultado, `localeCompare` sem opções, coluna numérica caindo no ramo textual, abertas
fora do recorte, multi-seleção virando seleção única, busca textual e multiselect de
conta fora do recorte, conta vazia deixando de significar "todas", abertas sumindo do
topo da tabela).
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
APOSTAS_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "apostas.js"
APP_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"
CSS = RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css"


def test_kpi_le_o_recorte_sem_desfecho():
    """Os oito KPIs da tela saem de `apostasKpiRows`. Se algum voltar a ler
    `apostasFiltered`, ele passa a seguir o filtro de resultado — e um Win Rate de 100%
    aparece sem que nada na tela diga que é recorte."""
    src = APOSTAS_JS.read_text(encoding="utf-8")
    # A fatia vai da montagem da tabela até os chips: é TODO o cálculo dos KPIs, incluindo
    # o P/L e o turnover, que ficam antes do `kpiEl`. Fatia curta demais aqui deixou passar
    # a mutação que trocava justamente a primeira linha (o P/L).
    bloco = src[src.index("apostasTabela=apostasAbertasFiltered.concat(apostasFiltered);")
                + len("apostasTabela=apostasAbertasFiltered.concat(apostasFiltered);")
                :src.index("renderApostasResChips(")]
    # Sem os comentários: o próprio aviso no código cita `apostasFiltered` para dizer que
    # NÃO é ele que os KPIs leem, e prosa não é código.
    codigo = "\n".join(l for l in bloco.split("\n") if not l.strip().startswith("//"))
    assert "apostasFiltered" not in codigo, (
        "um KPI voltou a ler apostasFiltered — o filtro de resultado ia recortar a régua"
    )
    assert codigo.count("apostasKpiRows") >= 6, (
        f"os KPIs pararam de ler apostasKpiRows (só {codigo.count('apostasKpiRows')} usos)"
    )


def test_tela_avisa_quando_os_kpis_nao_seguem_o_filtro():
    """A nota é a metade humana da decisão: sem ela, filtrar L e ler P/L positivo parece
    defeito. É o mesmo princípio do aviso que tem de apontar a linha."""
    src = APOSTAS_JS.read_text(encoding="utf-8")
    assert "apf-nota" in src, "a nota dos KPIs sumiu do render"
    assert "apostasResSel.size" in src[src.index("const nota="):src.index("kpiEl.innerHTML=")], (
        "a nota deixou de ser condicionada ao filtro de resultado ativo"
    )
    assert ".apf-nota" in CSS.read_text(encoding="utf-8"), "a nota ficou sem estilo"


def test_chip_usa_o_codigo_canonico_do_resultado():
    """Badge/chip mostra W/HW/L/HL/V cru — nunca um apelido cosmético. O nome humano
    ('Green', 'Red') vive no title, que é onde ele não vira um segundo vocabulário."""
    src = APOSTAS_JS.read_text(encoding="utf-8")
    m = re.search(r"const APOSTAS_RES=\[(.+?)\];", src)
    assert m, "APOSTAS_RES sumiu"
    codigos = re.findall(r"\['(\w+)',", m.group(1))
    assert codigos == ["W", "HW", "L", "HL", "V", "ABERTA"], f"vocabulário mudou: {codigos}"


def test_faixa_reusa_o_parse_numerico_da_tela():
    """O limite é DIGITADO em pt-BR ("1.250,50") e pode chegar com o minus U+2212 vindo
    de um copiar/colar da própria tela. Reescrever um segundo parser aqui repetiria o
    bug da s300 — a faixa passa pelo `parseNum` do app.js."""
    corpo = re.search(r"function _apFaixa\(k\)\{.*?\}", APOSTAS_JS.read_text(encoding="utf-8"), re.S)
    assert corpo, "_apFaixa sumiu"
    assert "parseNum(" in corpo.group(0), "a faixa deixou de usar parseNum — '1.250,50' vira 1"
    assert "parseFloat" not in corpo.group(0), "parseFloat na faixa: pt-BR e U+2212 se perdem"


def test_a_tela_tem_UMA_barra_de_filtros():
    """Os filtros nasceram em DUAS caixas — a da página em cima, a nova embaixo dos KPIs —
    e o Feca leu a tela: *"alguns filtros ficaram lá no topo, bem confuso"*. Filtro é uma
    superfície só: partido em dois cartões, o de cima sai do campo de visão de quem mexe
    no de baixo e a tela parece não ter o filtro que tem.

    A página de apostas NÃO pode voltar a chamar `buildFilters` — quem monta a barra dela
    é o `buildFiltrosApostas`, com as mesmas peças (`_grupoPeriodo` e cia.)."""
    src = APP_JS.read_text(encoding="utf-8")
    pagina = src[src.index('<div class="page" id="page-apostas">'):src.index("<!-- EM ABERTO")]
    assert "buildFilters('apostas'" not in pagina, "voltou a segunda barra de filtros na tela"
    assert "buildFiltrosApostas(" in pagina, "a barra única sumiu da página"

    barra = APOSTAS_JS.read_text(encoding="utf-8")
    corpo = barra[barra.index("function buildFiltrosApostas("):barra.index("// Match dos filtros de coluna")]
    for peca in ("_grupoPeriodo(", "_grupoEsporte(", "_grupoCasa(", "_grupoTipster(", "_grupoOperador("):
        assert peca in corpo, f"{peca} saiu da barra — o eixo sumiu ou o markup foi copiado"


def test_a_barra_nao_duplica_os_eixos_da_pagina():
    """Esporte, Tipster e Casa são multiselect na barra. As caixas de texto que os
    repetiam casavam por substring ("Vinicius" pegava "Vinicius2") e ocupavam metade da
    barra entregando menos. A busca textual ficou só onde não há multiselect."""
    src = APOSTAS_JS.read_text(encoding="utf-8")
    barra = src[src.index("function buildFiltrosApostas("):src.index("// Match dos filtros de coluna")]
    # O índice é o que amarra cada input à coluna de APOSTAS_COLS — é ele que o teste
    # confere, não o rótulo.
    colunas = sorted(int(n) for n in re.findall(r"apostasFilter\((\d+),", barra))
    assert colunas == [5, 6], (
        f"a busca textual mudou de colunas: {colunas}. 5=aposta e 6=descrição são as duas "
        "sem multiselect na barra; 1/2/3 (esporte/tipster/casa) duplicariam o seletor"
    )
    # Conta é o único multiselect montado aqui; os outros quatro vêm das peças
    # compartilhadas, e quem confere que eles estão na barra é o teste da barra única.
    assert "buildMS('pa_" in barra, "o multiselect de conta sumiu da barra"


def test_csv_diz_que_baixa_a_base_inteira():
    """`/exportar.csv` é backup do dono, não o recorte da tela. O botão fica ao lado de
    filtros que acabaram de recortar 400 linhas em 12 — o rótulo é o que impede a
    leitura errada."""
    src = APOSTAS_JS.read_text(encoding="utf-8")
    # O rótulo VISÍVEL, não o title: quem lê o botão no meio de um recorte não passa o
    # mouse nele. Texto do <a>, tudo que vem depois do </svg>.
    trecho = src[src.index('class="apf-csv"'):src.index('class="apf-csv"') + 900]
    rotulo = trecho[trecho.index("</svg>") + 6:trecho.index("</a>")]
    assert "completa" in rotulo.lower(), (
        f"o rótulo do CSV deixou de dizer que baixa a base inteira: {rotulo!r}"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_dos_filtros():
    """`tests/js/filtros_base_completa.mjs` recorta e EXECUTA o código real: parseNum, os
    matches de texto/conta/faixa/resultado, o comparador e a repartição KPI × tabela."""
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "filtros_base_completa.mjs")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
