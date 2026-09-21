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
    m = re.search(r"^function _cnCustoTotal\(.*?^\}", src, re.S | re.M)
    assert m, "não achei a função _cnCustoTotal no contas.js"
    corpo = m.group(0)
    assert "_custoNaJanela(" in corpo, (
        "o custo total tem de sair do `_custoNaJanela` — a mesma função que "
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


def test_o_drill_lista_TODAS_as_contas_da_casa():
    """Recorte que não vem do filtro faz a tabela contradizer o próprio total.

    O corte antigo em 12 linhas por turnover escondia a única conta **ativa** da Betano
    (`cleisonglsports [Gustavo]`), que não estava entre as de maior giro: o cabeçalho
    dizia `1 ativa` e a lista abaixo mostrava 12 encerradas. A tela parecia contar
    errado, e não estava — o Feca leu isso como defeito na primeira vez que abriu.

    O único recorte legítimo desta tela é o da barra de filtros.
    """
    src = CONTAS.read_text(encoding="utf-8")
    m = re.search(r"^function _cnDrill\(.*?^\}", src, re.S | re.M)
    assert m, "não achei a função _cnDrill no contas.js"
    corpo = m.group(0)
    assert ".slice(0," not in corpo, (
        "o drill não pode truncar a lista: recorte que não é do filtro faz a sub-tabela "
        "contradizer a contagem do cabeçalho da casa"
    )


def test_as_duas_tabelas_ordenam_por_estados_separados():
    """A sub-tabela tem colunas que a de cima não tem (Conta, Fornecedor, Custo, Estado).

    Com um estado de ordenação só, ordenar a de baixo por `Custo` deixaria a de cima com
    uma chave inexistente — e `undefined` ordena tudo como zero, calado.
    """
    src = CONTAS.read_text(encoding="utf-8")
    assert "_cnDrillCol" in src and "_cnDrillDir" in src
    m = re.search(r"^function _cnDrill\(.*?^\}", src, re.S | re.M)
    corpo = m.group(0)
    assert "_cnSortCol" not in corpo, "o drill não pode ler o estado de ordenação da tabela de casas"
    # E o clique no cabeçalho não pode fechar o painel: a linha da casa é o gatilho do toggle.
    assert corpo.count("event.stopPropagation()") >= 2, (
        "o `<th>` do drill e o `<td>` que o hospeda precisam de stopPropagation, senão "
        "ordenar a sub-tabela fecha o drill"
    )


def test_toda_classe_cn_usada_no_js_existe_no_css():
    """Classe escrita com DOIS nomes não quebra nada — ela só não tem estilo.

    Aconteceu na v4: o botão do estado vazio saiu como `cn-vazio__btn` no JS e
    `cn-empty__btn` no CSS. O `node --check` passa, o `check-tokens` passa, a suíte
    passa, e o botão aparece na tela com a cara nativa do navegador, no meio de uma
    superfície inteira estilizada. Só quem ABRE a tela vê — e foi o medidor headless,
    procurando a classe, que acusou.

    É gate de FORMA e custa um `grep`: o de comportamento nunca vai olhar para CSS.
    """
    js = CONTAS.read_text(encoding="utf-8")
    css = (RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css").read_text(
        encoding="utf-8")
    nomes = set()
    for grupo in re.findall(r'class="([^"]*\bcn-[^"]*)"', js):
        for n in grupo.split():
            if n.startswith("cn-") and "${" not in n:
                nomes.add(n)
    assert len(nomes) > 30, "o recorte das classes falhou — esperava dezenas, achou poucas"
    orfas = sorted(n for n in nomes if ("." + n) not in css)
    assert not orfas, "classe usada no JS e sem regra no CSS: " + ", ".join(orfas)


def test_a_tela_nao_aconselha_o_usuario():
    """O produto INFORMA; quem conclui é o dono.

    Regra do Feca, dada quando um rodapé meu terminou em *"Para estimar a próxima
    compra, use 12, não 34"*: **"acho q não deveríamos sugerir ou concluir para o
    cliente"**. É a mesma régua que ele já tinha cravado no handoff de design sobre não
    comparar durabilidade entre fornecedores — *"nós não somos quem vai falar q joão
    dura mais q francisco"*: a informação aparece, o veredito não.

    A fronteira é útil e não é sutil: descrever o que o número MEDE é informação
    ("abaixo de 1,00× a conta não devolveu o que custou" é definição da métrica);
    dizer o que FAZER com ele é conselho.

    O gate pega o verbo, que é onde o conselho se materializa em português. Ele não
    cobre conselho escrito sem imperativo — para isso não há grep, só leitura.
    """
    src = CONTAS.read_text(encoding="utf-8")
    verbos = re.compile(
        r"\b(use|prefira|evite|considere|recomend\w*|sugerimos|deveria|aposte|compre|"
        r"escolha|opte|invista|priorize)\b", re.I)
    ruins = []
    for n, linha in enumerate(src.splitlines(), 1):
        s = linha.strip()
        if s.startswith("//") or s.startswith("*") or s.startswith("/*"):
            continue
        for m in re.finditer(r"`([^`]*)`|'([^']*)'", linha):
            txt = m.group(1) or m.group(2) or ""
            if verbos.search(txt):
                ruins.append(f"L{n}: {txt.strip()[:90]}")
    assert not ruins, (
        "texto de tela aconselhando o usuário (o produto informa, quem conclui é o "
        "dono): " + " | ".join(ruins)
    )


def test_nenhum_travessao_no_texto_que_vai_para_a_tela():
    """Regra de escrita do Feca: travessão em frase é assinatura de IA, e não se usa.

    Vale para o texto que o usuário LÊ (o `metric-tip` da mediana, a régua, as notas),
    não para os comentários do código, que são para quem edita.
    """
    src = CONTAS.read_text(encoding="utf-8")
    ruins = []
    for n, linha in enumerate(src.split("\n"), 1):
        s = linha.strip()
        if s.startswith("//") or s.startswith("*") or s.startswith("/*"):
            continue
        for m in re.finditer(r"`([^`]*)`|'([^']*)'", linha):
            txt = m.group(1) or m.group(2) or ""
            if "—" in txt or "–" in txt:
                ruins.append(f"L{n}: {txt[:80]}")
    assert not ruins, "travessão em texto de tela:\n" + "\n".join(ruins)


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
    # `.toFixed` é proibido em DINHEIRO (§5.3), não em largura de CSS: a v4 tem barras
    # cuja largura é `width:${pct.toFixed(1)}%`, que não passa nem perto do `.money`.
    # O gate olha a LINHA: se ela tem `.toFixed` e não é uma largura/posição em `%`,
    # reprova. Um gate cego ao contexto reprovaria a régua de duração inteira.
    ruins = []
    for n, linha in enumerate(src.splitlines(), 1):
        if ".toFixed(" not in linha:
            continue
        if "%" in linha and ("width:" in linha or "left:" in linha):
            continue
        ruins.append(f"L{n}: {linha.strip()[:90]}")
    assert not ruins, "`.toFixed` fora de largura de CSS (UI_REFERENCE §5.3): " + " | ".join(ruins)


def test_a_regua_de_escopo_fica_FORA_do_que_o_bloco_Geral_recolhe():
    """O aviso nao pode sumir junto com a resposta.

    A `_cnRegua` diz que Duracao e dias ativos ignoram o filtro de periodo, e a tabela
    "Por casa" logo abaixo TAMBEM tem coluna de duracao. Recolher o bloco Geral serve
    justamente para ler casa a casa; se a regua se recolhesse junto, o aviso sumiria
    exatamente no momento para o qual ele foi escrito, e a tela passaria a mentir sobre
    o que o periodo corta sem erro nenhum.

    E facil de desfazer sem perceber: basta mover uma linha para dentro do template do
    corpo. Dai o gate ler a ORDEM do markup, e nao a existencia das duas pecas.
    """
    src = CONTAS.read_text(encoding="utf-8")
    m = re.search(r"function _cnBlocoGeral\(.*?\n}", src, re.S)
    assert m, "_cnBlocoGeral sumiu ou mudou de forma"
    corpo = m.group(0)

    i_regua = corpo.find("_cnRegua(")
    i_corpo = corpo.find('id="cnGeralCorpo"')
    assert i_regua > 0, "o bloco Geral parou de montar a regua"
    assert i_corpo > 0, "o container recolhivel perdeu o id cnGeralCorpo"
    assert i_regua < i_corpo, (
        "a regua passou a ser montada DENTRO do container recolhivel: ao recolher o "
        "bloco Geral o aviso de escopo some, e a tabela por casa fica sem ele"
    )

    css = (RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css").read_text(encoding="utf-8")
    # E o CSS nao pode esconder a regua por dentro do bloco fechado.
    assert ".cn-geral__corpo           { display: none;" in css, (
        "quem esconde o conteudo recolhido deixou de ser o .cn-geral__corpo; confira se "
        "a regra nova nao pega a regua junto"
    )


def test_recolher_o_bloco_Geral_nao_repinta_a_tela():
    """Trocar a classe, nunca chamar o render.

    `renderContas` recalcula os agregados todos e reescreve o `innerHTML` do container.
    Chama-lo para mudar um `display` jogaria fora o drill que estivesse aberto embaixo,
    junto com a ordenacao da sub-tabela, e o usuario veria a tela piscar e voltar ao
    inicio por ter clicado em "recolher".
    """
    src = CONTAS.read_text(encoding="utf-8")
    m = re.search(r"window\.cnGeralToggle\s*=\s*function\(\)\{.*?\n\};", src, re.S)
    assert m, "cnGeralToggle sumiu ou mudou de forma"
    corpo = m.group(0)
    assert "classList.toggle" in corpo, "o toggle deixou de trabalhar pela classe"
    for proibido in ("renderContas(", "innerHTML"):
        assert proibido not in corpo, (
            f"cnGeralToggle passou a usar `{proibido}`: recolher deixou de ser uma troca "
            "de classe e virou repintura, perdendo o drill aberto e a ordenacao"
        )
    # A preferencia e do NAVEGADOR, e o acessor lanca em janela anonima.
    assert corpo.count("try{") >= 1 and "catch" in corpo, (
        "escrita em localStorage sem try/catch: lanca em janela anonima e derruba o clique"
    )
