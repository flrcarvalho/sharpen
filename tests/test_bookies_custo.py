"""BOOKIES com custo e P/L Líquido (s364, Fatia 5) — a MESMA régua das outras telas.

A lista de Bookies só tinha P/L bruto, ROI, Casas Positivas e Turnover. O drill de uma
casa já trazia Custo / P/L Líquido / ROI Líquido desde a s358; a LISTA, que é onde se
decide "a operação nesta casa vale a pena", não trazia nada.

Medido na base real do Feca antes de desenhar: **48 casas com aposta, 3 com custo > 0**
(Superbet R$ 21.500, Betano R$ 20.300, Bet365 R$ 17.800 — os R$ 59.600 inteiros). Foi
essa medição que manteve os CARDS intactos (decisão do Feca): um stat de custo em cada
card sairia `R$ 0` em 45 deles, e ali zero não quer dizer "de graça", quer dizer "não há
preço lançado" — o zero se disfarçando de conta feita.

A prova de COMPORTAMENTO roda em `tests/js/bookies_custo.mjs`, que executa `renderCasa`
RECORTADA do `performance.js` de produção com o `calcCostFiltered` REAL do `gestao.js` e
os `fmtPL`/`fmtR`/`fmtPct` REAIS do `app.js`. Nenhuma regra é reimplementada.

O que NÃO está coberto: os cards por casa (intactos por decisão), o LAYOUT (o grid de 3
colunas e a ausência de truncamento foram medidos no Chrome, dentro do iframe do dash —
o dublê de DOM daqui aceitaria qualquer largura) e o drill, que tem régua própria.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "app" / "static" / "dash" / "assets" / "js"
PERF = JS / "charts" / "performance.js"
GESTAO = JS / "charts" / "gestao.js"
MJS = RAIZ / "tests" / "js" / "bookies_custo.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_portfolio():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def test_o_custo_do_portfolio_sai_da_funcao_canonica_e_nao_de_uma_soma_propria():
    """UMA régua: o custo vem do `calcCostFiltered`, a mesma função do KPI da Visão Geral.

    Somar `calcCasaCost` casa a casa daria HOJE o mesmo número, por um caminho novo — e
    duas derivações para a mesma pergunta divergem no primeiro caso de borda. Foi
    exatamente isso que a s362 desfez no `_c2contas`, e este teste existe para a Fatia 5
    não reintroduzir o padrão numa terceira tela.

    É gate de FORMA, de propósito: o de comportamento não distingue os dois caminhos
    enquanto eles concordam, que é justamente quando o defeito entra sem ser notado."""
    src = PERF.read_text(encoding="utf-8")
    m = re.search(r"^function renderCasa\(.*?^\}", src, re.S | re.M)
    assert m, "não achei a função renderCasa no performance.js"
    corpo = m.group(0)
    assert "calcCostFiltered('casas')" in corpo, (
        "o custo do portfólio de Bookies tem de sair do `calcCostFiltered('casas')` — "
        "a mesma função do KPI da Visão Geral"
    )
    # A CHAMADA, não a menção: o comentário que explica por que não se usa `calcCasaCost`
    # aqui cita o nome, e uma checagem por substring simples reprovaria o próprio texto
    # que documenta a regra.
    assert "calcCasaCost(" not in corpo, (
        "`calcCasaCost` é do DRILL (uma casa por vez). Somá-lo aqui criaria uma segunda "
        "derivação para o mesmo número — ver s362 e o `_c2contas`"
    )


# (título, arquivo, trecho original, trecho estragado)
MUTACOES = [
    # ── A CASCATA ───────────────────────────────────────────────────────────
    (
        "o custo SOMA no lugar de descontar",
        "perf",
        "  const portLiq=portPL-costConta;",
        "  const portLiq=portPL+costConta;",
    ),
    (
        "o P/L Liquido vira o bruto (o custo deixa de descer)",
        "perf",
        "  const portLiq=portPL-costConta;",
        "  const portLiq=portPL;",
    ),
    # ── A REGUA: pagina errada = filtros errados ────────────────────────────
    (
        "o custo passa a ler os filtros da Visao Geral, nao os de Bookies",
        "perf",
        "    ?calcCostFiltered('casas'):{costConta:0,nContas:0};",
        "    ?calcCostFiltered('overview'):{costConta:0,nContas:0};",
    ),
    # ── A MASCARA ───────────────────────────────────────────────────────────
    (
        "o custo perde o sinal negativo e a cor (volta para fmtR)",
        "perf",
        "  const _custoValP=costConta>0?fmtPL(-costConta):fmtR(0);",
        "  const _custoValP=fmtR(costConta);",
    ),
    (
        "o custo aparece POSITIVO, como se fosse ganho",
        "perf",
        "  const _custoValP=costConta>0?fmtPL(-costConta):fmtR(0);",
        "  const _custoValP=costConta>0?fmtPL(costConta):fmtR(0);",
    ),
    (
        "custo ZERO deixa de ser neutro e nasce vermelho",
        "perf",
        "  const _custoClsP=costConta>0?'neg':'neu';",
        "  const _custoClsP='neg';",
    ),
    # ── O AVISO: esporte e tipster NAO recortam, e a tela DIZ ───────────────
    (
        "o aviso de que o custo nao recorta some da tela",
        "perf",
        "  const _apFiltroP=[",
        "  const _apFiltroP=''&&[",
    ),
    # As duas ancoras abaixo levam o `const _apFiltroP=[` junto: as MESMAS linhas
    # existem no `renderCasaDrill` (o `_apFiltro` dele), e sem o prefixo o trecho
    # aparece duas vezes no arquivo.
    (
        "o aviso passa a olhar o filtro de ESPORTE da pagina errada",
        "perf",
        "  const _apFiltroP=[\n"
        "    (typeof msGet==='function'&&msGet('sp_casas').size)?'esporte':'',",
        "  const _apFiltroP=[\n"
        "    (typeof msGet==='function'&&msGet('sp_overview').size)?'esporte':'',",
    ),
    (
        "o aviso esquece o filtro de TIPSTER",
        "perf",
        "  const _apFiltroP=[\n"
        "    (typeof msGet==='function'&&msGet('sp_casas').size)?'esporte':'',\n"
        "    (typeof msGet==='function'&&msGet('ti_casas').size)?'tipster':'',",
        "  const _apFiltroP=[\n"
        "    (typeof msGet==='function'&&msGet('sp_casas').size)?'esporte':'',\n"
        "    '',",
    ),
    (
        "o sub do P/L Liquido deixa de avisar o corte",
        "perf",
        "`<div class=\"kpi-sub\">${_apFiltroP?'P/L do recorte − custo das casas':'após o custo de contas'}</div>`",
        "`<div class=\"kpi-sub\">após o custo de contas</div>`",
    ),
    # ── A CONTAGEM ──────────────────────────────────────────────────────────
    (
        "o sub do custo conta as CASAS no lugar das contas compradas",
        "perf",
        "        ? `${nContasCusto} conta${nContasCusto!==1?'s':''} comprada${nContasCusto!==1?'s':''} no período`",
        "        ? `${totalC} conta${totalC!==1?'s':''} comprada${totalC!==1?'s':''} no período`",
    ),
    # ── A REGUA DE LANCAMENTO, la embaixo no gestao.js ─────────────────────
    (
        "o custo volta a cobrar toda conta VIVA no periodo, nao a paga",
        "gestao",
        "    range?range.from:'0000-01-01', range?range.to:'9999-12-31', casasSel, opsSel, '', 'pago');",
        "    range?range.from:'0000-01-01', range?range.to:'9999-12-31', casasSel, opsSel, '', 'vivo');",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,arq,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, arq, de, para):
    """Quebra o código de propósito e exige que o .mjs fique VERMELHO."""
    alvo = PERF if arq == "perf" else GESTAO
    src = alvo.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no {alvo.name} "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    estragado = tmp_path / alvo.name
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")

    env = {**os.environ, ("ALVO_PERF" if arq == "perf" else "ALVO_GESTAO"): str(estragado)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida — o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )
