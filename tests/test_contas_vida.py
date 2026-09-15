"""Aba CONTAS (s365) — a unidade é a CONTA, e as réguas que quebram em silêncio.

A aba responde "quanto dura, quanto gira e quanto devolve uma conta nesta casa?". A
fronteira com Bookies é a UNIDADE: Bookies mede a APOSTA e não sabe quantas contas
geraram aquele P/L nem quanto tempo elas viveram.

Medido na base real do Feca antes de desenhar, e cada número mudou o desenho:

* **59 das 182 contas são PRÓPRIAS** (fornecedor `Eu`, 58 escritas e 1 sem colchete).
  Delas saem 59 das 69 contas sem preço — ou seja, o que parecia buraco de dado é, na
  esmagadora maioria, custo zero DECLARADO. Por isso "própria" e "sem preço lançado" são
  estados diferentes na tela, e só o segundo fica fora do múltiplo.
* **Duração de conta ATIVA e de conta ENCERRADA diferem 5x** (103d contra 20d de média).
  Contar as vivas junto responderia "quanto uma conta aguenta" com um número 60% maior
  do que a verdade — daí o segmentado de População.
* **A mediana é ~metade da média em TODA casa** (Superbet 5d contra 11d, Betano 8d
  contra 14d, Bet365 10d contra 19d): poucas contas longevas puxam a média. Por isso a
  mediana é coluna, não detalhe.

A prova de COMPORTAMENTO roda em `tests/js/contas_vida.mjs`, que executa `_cnBase`,
`_cnPorCasa` e `_cnMediana` RECORTADAS do `contas.js` de produção, com o
`_buildContaVida`/`_custoDaConta` REAIS do `gestao.js` e o `_selRange`/`msGet` REAIS do
`filters.js`. Nenhuma régua é reimplementada. **8 de 8 mutações detectadas.**

O que NÃO está coberto aqui: a máscara do múltiplo, a cor, a Escada de Tinta, o layout,
o tooltip da mediana e a corrida de boot — tudo isso foi medido no Chrome, dentro do
iframe do dash, por `scripts/demo/medir_aba_contas.mjs`. Um dublê de DOM aceitaria
qualquer um deles calado, e foi medindo que a corrida de boot apareceu.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "app" / "static" / "dash" / "assets" / "js"
CONTAS = JS / "charts" / "contas.js"
APP_JS = JS / "app.js"
MJS = RAIZ / "tests" / "js" / "contas_vida.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_das_reguas_de_vida():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def test_o_custo_total_sai_da_funcao_canonica_e_nao_de_uma_soma_propria():
    """UMA régua de custo: `_custoNaJanela`, a mesma de `calcCostFiltered` e do drill.

    Somar `_custoDaConta` linha a linha daria HOJE o mesmo número, por um caminho novo —
    e duas derivações para a mesma pergunta divergem no primeiro caso de borda. É o
    padrão que a s362 desfez no `_c2contas` e que a s364 travou em Bookies; este teste
    existe para a aba nova não o reintroduzir numa quarta tela.

    Gate de FORMA, de propósito: o de comportamento não distingue os dois caminhos
    enquanto eles concordam, que é justamente quando o defeito entra.
    """
    src = CONTAS.read_text(encoding="utf-8")
    m = re.search(r"^function _cnCustoCard\(.*?^\}", src, re.S | re.M)
    assert m, "não achei a função _cnCustoCard no contas.js"
    corpo = m.group(0)
    assert "_custoNaJanela(" in corpo, (
        "o custo total do card tem de sair do `_custoNaJanela` — a mesma função que "
        "`calcCostFiltered` usa"
    )


def test_esporte_e_tipster_nao_recortam_a_aba_contas():
    """Eles descrevem a APOSTA, não a conta.

    A Bet365 custou o que custou e durou o que durou, olhe-se tênis ou futebol. Oferecer
    esses eixos aqui faria o número mudar por um recorte que não descreve a unidade da
    tela — o mesmo motivo pelo qual `calcCostFiltered` não recebe `rows`.

    Por isso a barra é montada por `buildFiltrosContas` e não pelo `buildFilters`
    genérico, que traz os cinco eixos.
    """
    src = CONTAS.read_text(encoding="utf-8")
    m = re.search(r"^function buildFiltrosContas\(.*?^\}", src, re.S | re.M)
    assert m, "não achei a função buildFiltrosContas no contas.js"
    corpo = m.group(0)
    assert "_grupoEsporte" not in corpo, "Esporte não pode recortar a aba Contas"
    assert "_grupoTipster" not in corpo, "Tipster não pode recortar a aba Contas"
    assert "_grupoPeriodo" in corpo and "_grupoCasa" in corpo, (
        "Período e Casa são as peças COMPARTILHADAS do filters.js — copiar o markup "
        "criaria dois Períodos que divergem no primeiro ajuste (s317)"
    )
    # E a página não pode montar a barra genérica por fora.
    app = APP_JS.read_text(encoding="utf-8")
    pagina = re.search(r'<div class="page" id="page-contas">.*?</div>\s*$', app, re.S | re.M)
    if pagina:
        assert "buildFilters(" not in pagina.group(0)


def test_a_carga_da_aba_nao_pode_deixar_a_tela_em_branco_quando_uma_rota_falha():
    """Medido no headless: sem `.catch` em CADA carga, um 404 rejeita o `Promise.all`,
    o `.then` nunca roda e a aba fica em branco para sempre, sem erro na tela.

    Mesma família do "aguardando que nunca resolve": o dado da vida vem de `DADOS` /
    `DADOS_ABERTAS`, que já estão em memória, então a tela tem o que mostrar mesmo
    quando o cadastro ou os preços não chegam.
    """
    app = APP_JS.read_text(encoding="utf-8")
    m = re.search(r"else if\(id==='contas'\)\{[^\n]*", app)
    assert m, "não achei o ramo 'contas' no renderPage"
    ramo = m.group(0)
    assert ramo.count(".catch(") >= 2, (
        "cada carga do ramo precisa do próprio `.catch`: com um `Promise.all` cru, "
        "uma rota que falha deixa a aba em branco"
    )


def test_a_aba_espera_o_dom_antes_de_pintar():
    """A corrida que deixava a aba em branco de forma INTERMITENTE.

    O boot do dashboard é assíncrono e a casca (`app.html`) chama `showPage` no evento
    `load` do iframe, que dispara antes de o `buildHTML` montar o `#contasContent`. O
    `renderPage` prematuro escreve no vazio E MARCA a assinatura da página; o `showPage`
    seguinte é então engolido pelo guard `id===_lastPage&&sig===_lastPageSig`.

    O guard é defeito COMPARTILHADO e anterior a esta aba — consertá-lo é mudança
    própria. Aqui a aba só garante a si mesma.
    """
    src = CONTAS.read_text(encoding="utf-8")
    assert "_cnPintarQuandoPronto" in src
    app = APP_JS.read_text(encoding="utf-8")
    m = re.search(r"else if\(id==='contas'\)\{[^\n]*", app)
    assert "_cnPintarQuandoPronto" in m.group(0), (
        "o ramo tem de pintar pelo `_cnPintarQuandoPronto`, que espera o DOM existir"
    )


def test_a_aba_nao_abrevia_dinheiro_nem_inventa_formatador():
    """§5 do UI_REFERENCE: todo R$ passa por `fmtR`/`fmtPL`, nunca por string crua.

    O MÚLTIPLO é a exceção declarada — não é R$, nem %, nem odd, nem saldo. Ele espelha
    a gramática do `.money` (mono, 2 casas, o `×` neutro e menor como o `R$`) em vez de
    inventar uma quinta máscara, e tem função própria (`_cnMult`).
    """
    src = CONTAS.read_text(encoding="utf-8")
    assert "fmtR(" in src and "fmtPL(" in src
    assert "'R$ '+" not in src and '"R$ "+' not in src, (
        "R$ montado como string crua fora do `.money` — ver UI_REFERENCE §5.4"
    )
    assert ".toFixed(" not in src, "R$ nunca usa .toFixed (UI_REFERENCE §5.3)"
