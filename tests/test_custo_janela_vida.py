"""As DUAS réguas do custo de conta (s322 + s358).

Este arquivo nasceu na s322 provando a JANELA DE VIDA. Na s358 a régua do P/L virou
CAIXA e a janela de vida continuou existindo para outra pergunta — as duas são
provadas aqui.

    modo 'pago' (o P/L)  → o que saiu do bolso no recorte. Cada conta cobra UMA vez,
        no dia do pagamento, e a régua SOMA: os 12 meses dão o ano.
    modo 'vivo' (parque) → o que está rodando. Toda conta viva no recorte cobra cheio,
        e a régua NÃO soma — por isso ela nunca entra no P/L.

O caso que virou a régua do P/L (Jonathan, em áudio, 14/09/2026): *"ele só esse mês
está puxando com o custo contando 12 e foi uma só"*. Medido na base dele: setembro
cobrava R$ 6.400 de 10 contas tendo ele comprado UMA, de R$ 400; e a soma dos meses
dava R$ 39.800 contra R$ 28.400 realmente pagos. "Não posso pagar uma conta duas
vezes: se paguei em agosto, ela pertence a agosto" (Feca).

A data do pagamento, na ordem decidida pelo Feca: `adquirida_em` DIGITADA quando é
anterior à 1ª aposta; senão a 1ª aposta (piso medido, e o que vale para toda conta
migrada, cujo `adquirida_em` foi DEDUZIDO pelo backfill); senão o cadastro.

O caso que criou a janela de vida (Jaao26, em vídeo) não sumiu: filtrar um dia dava
R$ 0 com o parque em uso. Esse número deixou de ser custo e virou ESTOQUE.

A prova de COMPORTAMENTO roda em `tests/js/custo_janela_vida.mjs`, que executa as
funções RECORTADAS do arquivo de produção, mais o `_selRange` real do `filters.js`.
Este arquivo o invoca e, em seguida, o prova por MUTAÇÃO — ver
`test_mutacoes_sao_detectadas`.

O que NÃO está coberto: o render (a legenda "N contas compradas no período", a cor do
card e a Escada de Tinta ficam para o render headless), o `contasLoad` (fetch, dublado
no .mjs) e o backfill SQL de `adquirida_em`, que só roda contra Postgres.

Os três gates da etapa 5 (painel morto, custo do drill de tipster e rótulo das Métricas)
são de RENDER e por isso provados por LEITURA de fonte, não por execução: o `.mjs` não
monta DOM. Leitura de fonte pega a reversão, não pega o comportamento — o que confere o
comportamento ali é o render headless contra o `servidor_demo`.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GESTAO = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "gestao.js"
OVERVIEW = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "overview.js"
PERFORMANCE = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "performance.js"
MJS = RAIZ / "tests" / "js" / "custo_janela_vida.mjs"


def _sem_comentarios(codigo: str) -> str:
    """O gate lê o CÓDIGO, não a prosa sobre o código — o comentário desta mudança cita
    justamente os termos que os asserts procuram."""
    codigo = re.sub(r"/\*.*?\*/", "", codigo, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", codigo, flags=re.MULTILINE)


# ── Gates baratos de leitura: apontam a linha exata se alguém reverter ────────

def test_o_mapa_de_primeira_aposta_nao_voltou():
    """`_firstBetMap` guardava só a 1ª aposta LIQUIDADA e lançava o custo naquele dia.
    A régua de caixa data o pagamento pela 1ª aposta de QUALQUER estado (`v.pa`, que lê
    `DADOS_ABERTAS` junto) e pela compra declarada — reintroduzir o mapa antigo devolveria
    o ponto cego da s239 por baixo de uma régua que hoje parece a mesma coisa."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    assert "_firstBetMap" not in src, (
        "_firstBetMap voltou ao gestao.js: o custo volta a ser lançado no DIA da 1ª "
        "aposta e filtrar qualquer outro dia devolve R$ 0 (s322)"
    )


def test_a_data_de_pagamento_tem_as_tres_camadas():
    """Compra declarada ANTES da 1ª aposta manda; senão a 1ª aposta; senão o cadastro.
    A ordem é a decisão do Feca (s358) e é o que impede base importada de datar o custo
    inteiro no dia do import."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function _dataPagamento\([^)]*\)\{.*?^\}", src, re.S | re.M)
    assert m, "_dataPagamento sumiu do gestao.js — o custo perdeu a régua de caixa"
    corpo = m.group(0)
    assert "v.adq" in corpo and "v.pa" in corpo, (
        "_dataPagamento parou de olhar a compra declarada ou a 1ª aposta"
    )
    assert "v.adq<v.pa" in corpo, (
        "a compra declarada voltou a mandar SEM ser comparada com a 1ª aposta: o "
        "`adquirida_em` deduzido pelo backfill passa a datar o custo (s358)"
    )


def test_o_pl_usa_a_regua_de_caixa_e_nao_a_de_vida():
    """As duas réguas convivem, e a de vida NÃO pode voltar ao P/L: é ela que cobrava a
    mesma conta todo mês (10 contas em setembro, uma comprada — caso Jonathan)."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    for nome in ("calcCostFiltered", "calcCasaCost"):
        m = re.search(r"^function " + nome + r"\([^)]*\)\{.*?^\}", src, re.S | re.M)
        assert m, f"{nome} sumiu do gestao.js"
        assert "'pago'" in m.group(0), (
            f"{nome} parou de pedir o modo 'pago': o custo volta a ser cobrado em todo "
            "mês em que a conta estiver viva (s358)"
        )


def test_o_custo_de_tipster_recorta_por_tipster_e_por_periodo():
    """Pedido do tester Germano. `ctData` é chaveado pelo NOME do tipster, a mesma chave
    do filtro — aqui o tipster recorta de verdade, ao contrário do custo de conta."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function calcCustoTipsterFiltrado\([^)]*\)\{.*?^\}", src, re.S | re.M)
    assert m, "calcCustoTipsterFiltrado sumiu do gestao.js"
    corpo = m.group(0)
    assert "'ti_'" in corpo, "o custo de tipster parou de respeitar o filtro de tipster"
    assert "'ca_'" not in corpo and "'sp_'" not in corpo and "'op_'" not in corpo, (
        "casa/esporte/operador voltaram a recortar a assinatura: ela não é de casa nenhuma"
    )
    assert "_selRange" in corpo, (
        "a janela do custo de tipster voltou a sair das LINHAS em vez do período (s358)"
    )
    assert "parseNum" in corpo, (
        "o custo de tipster deixou de usar o parseNum: valor gravado como '179.90' passa a "
        "ser lido como 17.990 por um parser que apaga o ponto (CLAUDE.md §6 da regra de UI)"
    )


def test_o_renderkpi_nao_reimplementa_a_regua_de_custo():
    """O cálculo mora no gestao.js, junto do custo de conta. Uma segunda cópia inline no
    overview.js divergiria no primeiro ajuste — foi assim que este card ficou duas
    sessões medindo diferente do vizinho."""
    ov = _sem_comentarios(OVERVIEW.read_text(encoding="utf-8"))
    assert "calcCustoTipsterFiltrado" in ov, "renderKPI parou de usar a régua canônica"
    assert "_ymMin" not in ov and "_ymMax" not in ov, (
        "o span de meses tirado das LINHAS voltou ao renderKPI (s358)"
    )
    assert "replace(',','.')" not in ov.replace(" ", ""), (
        "voltou um parser de número caseiro ao renderKPI — o do projeto é o parseNum"
    )


def test_o_bloco_de_contas_segue_a_referencia_visual():
    """Segunda iteração do desenho ("Visão Geral 172px"). Três coisas que ela mudou e que
    reprovam na revisão se voltarem:

    * o bloco é DUAS CÉLULAS com divisor (`.kpi__duo`), não pares empilhados;
    * **sem badge de escopo** — a 1ª célula já declara (`Deste tipster`), e o badge
      repetiria a mesma informação em outro canto do mesmo cartão;
    * sem conta com custo, o bloco **não aparece**: nunca `0 contas · R$ 0`, que é ruído
      em vez de informação.

    Prova por LEITURA: o `.mjs` não monta DOM. Quem confere o comportamento é o render
    headless — inclusive a altura igual dos oito cartões, que leitura não alcança."""
    ov = _sem_comentarios(OVERVIEW.read_text(encoding="utf-8"))
    css = (RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css").read_text(encoding="utf-8")
    assert "kpi__duo" in ov and "kpi__cell" in ov, "o bloco deixou de ser duas células"
    assert "kpi__chip" not in ov and "kpi__head" not in ov, (
        "o badge de escopo voltou: a 1ª célula já declara o escopo (2ª iteração do desenho)"
    )
    assert "Deste tipster" in ov and "Em operação" in ov, "os rótulos das células mudaram"
    # estado 4: a função devolve null e o cartão cai na legenda simples
    assert "return null;" in ov, (
        "o bloco parou de sumir quando não há conta com custo — o desenho proíbe `0 contas · R$ 0`"
    )
    assert "nenhuma conta com custo cadastrado" in ov, "sumiu a legenda do estado vazio"
    # a altura vale para os OITO, não só para o cartão de custo
    # O NÚMERO é de desenho e muda (180 → 156 quando o Feca pediu cartões menores); o que
    # o gate trava é a REGRA: existe um piso, e ele vale para todos os cartões do grid.
    assert re.search(r"#kpiGrid \.kpi \{[^}]*min-height:\s*\d+px", css), (
        "o `min-height` dos cartões da Visão Geral saiu do CSS: altura solta só no cartão "
        "de custo estica a fileira inteira (o desenho reprova)"
    )
    assert "kpi__link" not in css and "kpi__link" not in ov, (
        "o bloco voltou a ser clicável dentro do cartão — o Feca reprovou o hover ali "
        "('não precisa linkar dentro do card, não ficou legal')"
    )
    assert "is-cost { color: var(--neg-2)" in css, (
        "o custo do bloco voltou ao `--neg`: ele competiria com o número do topo, e o "
        "acumulado é secundário"
    )


def test_o_vocabulario_proibido_nao_volta_ao_produto():
    """O desenho tirou "parque" do produto inteiro: é jargão de frota, e não diz que o
    número é custo JÁ PAGO. Junto saíram "investido", "imobilizado" e "0 contas · R$ 0",
    que é ruído em vez de informação (o estado vazio tem copy própria).

    Cobre o CÓDIGO servido (js/css/html do dash), não os docs: histórico registra o que
    aconteceu, e lá a palavra é o nome do que existiu."""
    import os as _os
    proibidas = ("parque", "investido", "imobilizado")
    base = RAIZ / "app" / "static"
    achados = []
    for dp, _dns, fns in _os.walk(base):
        for fn in fns:
            if not fn.endswith((".js", ".css", ".html")):
                continue
            caminho = Path(dp) / fn
            txt = caminho.read_text(encoding="utf-8", errors="ignore").lower()
            for palavra in proibidas:
                if palavra in txt:
                    achados.append(f"{caminho.relative_to(RAIZ)}: {palavra}")
    assert not achados, (
        "vocabulário proibido pelo desenho voltou ao produto:\n  " + "\n  ".join(achados[:8])
    )


def test_nao_sobrou_painel_de_custo_morto_na_visao_geral():
    """`renderOvCusto` pintava `#ovCustoContent`, que saiu do HTML no commit 6e0399b e
    nunca voltou: a função inteira (92 linhas, na régua velha `custoData × contagem`)
    saía na primeira linha desde então, e três chamadas a mantinham viva no grep.

    Código morto que CALCULA dinheiro é pior que código morto qualquer: ele aparece em
    toda auditoria de custo como se fosse uma tela que discorda das outras."""
    ov = OVERVIEW.read_text(encoding="utf-8")
    ges = GESTAO.read_text(encoding="utf-8")
    assert "ovCustoContent" not in ov, (
        "voltou o `renderOvCusto`: ele pinta um elemento que não existe em HTML nenhum "
        "e calcula custo pela régua velha (s358)"
    )
    assert "renderOvCusto()" not in ges, "sobrou chamada ao renderOvCusto no gestao.js"


def test_o_custo_do_drill_de_tipster_respeita_o_periodo_do_drill():
    """O card somava TODOS os meses lançados enquanto o resto do drill mudava com o
    filtro de período logo acima dele. Dois números da mesma tela medindo recortes
    diferentes, sem dizer qual é qual."""
    perf = _sem_comentarios(PERFORMANCE.read_text(encoding="utf-8"))
    m = re.search(r"^async function renderGestaoTipster\([^)]*\)\{.*?^\}", perf, re.S | re.M)
    assert m, "renderGestaoTipster sumiu do performance.js"
    corpo = m.group(0)
    assert "_rangeDoPeriodo" in corpo, (
        "o card de custo do drill voltou a ignorar o período do drill (s358)"
    )
    assert "parseNum" in corpo, (
        "o card de custo do drill voltou a reparsear número por conta própria"
    )
    assert "_drillPeriodSt" in corpo, "o card não lê mais o período do drill"
    # E a régua do período é UMA só: o slice das linhas usa a mesma função.
    assert "_rangeDoPeriodo(st)" in perf, (
        "o `_sliceByPeriod` parou de usar a mesma tradução de período do card de custo — "
        "duas cópias divergem no primeiro atalho novo"
    )


def test_metricas_nao_chama_de_liquido_um_pl_sem_custo():
    """A tela Métricas rotulava de "P/L Líquido" a soma do lucro das apostas, que não
    desconta custo nenhum; o card de mesmo nome na Visão Geral desconta os três. Mesmo
    nome com números diferentes em telas vizinhas é defeito de leitura, ainda que os dois
    números estejam certos. O número não mudou — mudou o nome."""
    ges = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function renderMetrics\([^)]*\)\{.*?^\}", ges, re.S | re.M)
    assert m, "renderMetrics sumiu do gestao.js"
    assert "'P/L Líquido'" not in m.group(0), (
        "a tela Métricas voltou a chamar de 'P/L Líquido' um número que não desconta "
        "custo nenhum (s358)"
    )
    app = (RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    assert "mkCard('m_pl','P/L Líquido'" not in app.replace(" ", ""), (
        "o card da base de conhecimento voltou ao rótulo antigo"
    )


def test_o_custo_repinta_a_visao_geral_quando_chega_do_servidor():
    """`ctLoad` é fetch e chega DEPOIS do primeiro render. Sem repintar, quem abre a Visão
    Geral vê `Custo de Tipsters R$ 0` com tipsters lançados e um P/L Líquido inflado, até
    mexer em algum filtro. Medido na demo antes do conserto.

    O flag é o que impede o laço: `renderKPI` chama `ctLoad`, e sem ele o repaint chamaria
    `renderKPI` de novo, para sempre. NÃO é coberto por execução (o .mjs não monta DOM)."""
    app = (RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    src = _sem_comentarios(app)
    m = re.search(r"^async function ctLoad\(\)\{.*?^\}", src, re.S | re.M)
    assert m, "ctLoad sumiu do app.js"
    corpo = m.group(0)
    assert "renderKPI" in corpo, (
        "ctLoad parou de repintar a Visão Geral: o custo chega depois do 1º render e o "
        "P/L Líquido fica inflado até o usuário mexer num filtro (s358)"
    )
    assert "_ctRepintou" in corpo, (
        "sumiu o flag que impede o laço renderKPI → ctLoad → renderKPI (s358)"
    )


def test_contas_em_operacao_perguntam_por_hoje_e_nao_pelo_periodo():
    """Contas em operação é ESTOQUE: o que o dono tem agora. Deixá-lo seguir o filtro o faria variar
    como se fosse gasto, que é a confusão que a s358 desfez."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function calcContasEmOperacao\([^)]*\)\{.*?^\}", src, re.S | re.M)
    assert m, "calcContasEmOperacao sumiu do gestao.js"
    corpo = m.group(0)
    assert "'vivo'" in corpo, "as contas em operação pararam de usar a janela de vida"
    assert "_selRange" not in corpo, (
        "as contas em operação voltaram a olhar o período da tela: é estoque de HOJE (s358)"
    )
    assert "'ca_'" in corpo and "'op_'" in corpo, "parou de respeitar casa/operador"
    assert "'ti_'" in corpo, (
        "o filtro de tipster parou de recortar as contas em operação (desenho §6.4)"
    )


def test_a_janela_de_vida_le_liquidadas_e_abertas():
    """Só `DADOS` deixaria de fora a conta que tem aposta viva e nenhuma encerrada: ela
    leria como morta. É o ponto cego da s239 numa roupa nova."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function _buildContaVida\(\)\{.*?^\}", src, re.S | re.M)
    assert m, "_buildContaVida sumiu do gestao.js"
    assert "DADOS_ABERTAS" in m.group(0), (
        "_buildContaVida parou de ler DADOS_ABERTAS: conta com aposta só em aberto "
        "passa a ler como morta e perde o custo"
    )


def test_o_custo_nao_deriva_mais_das_linhas_filtradas():
    """As duas telas de custo têm de perguntar o PERÍODO ao `_selRange`. Derivar do
    intervalo das linhas era o que encolhia um mês filtrado até a última aposta dele e
    zerava o custo em recorte sem aposta nenhuma."""
    for arq in (GESTAO, PERFORMANCE):
        src = _sem_comentarios(arq.read_text(encoding="utf-8"))
        assert "_selRange" in src, f"{arq.name} não consulta mais o período selecionado"
    ov = _sem_comentarios(OVERVIEW.read_text(encoding="utf-8"))
    assert "calcCostFiltered(rows)" not in ov, (
        "renderKPI voltou a passar `rows` ao calcCostFiltered — a janela é do PERÍODO, "
        "não do intervalo das linhas (s322)"
    )


def test_escopo_do_custo_ignora_esporte_e_tipster():
    """Casa e Operador descrevem a CONTA e recortam; Esporte e Tipster descrevem a
    APOSTA e não. A conta Bet365 custou R$ 900 quer se olhe tênis ou futebol."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function calcCostFiltered\([^)]*\)\{.*?^\}", src, re.S | re.M)
    assert m, "calcCostFiltered sumiu do gestao.js"
    corpo = m.group(0)
    assert "'ca_'" in corpo and "'op_'" in corpo, "o custo parou de respeitar casa/operador"
    assert "'sp_'" not in corpo and "'ti_'" not in corpo, (
        "esporte/tipster voltaram a recortar o custo de contas: filtrar 'Tênis' faz a "
        "conta deixar de custar (s322)"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_da_janela():
    r = subprocess.run(
        ["node", str(MJS)], capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# ── Prova por MUTAÇÃO: quebra o código de propósito e exige vermelho ─────────
# Cada par (de, para) é uma reversão plausível da mudança. Verde aqui sem esta lista
# não provaria nada — foi assim que a s286/s287 pegaram dois falsos verdes.
MUTACOES = [
    # ── s358 etapa 4: os custos GERAIS ──────────────────────────────────────
    (
        "o mes fora do recorte passa a contar no custo geral",
        "    Object.entries((linha&&linha.values)||{}).forEach(([m,v])=>{if(m>=deM&&m<=ateM)t+=num(v);});",
        "    Object.entries((linha&&linha.values)||{}).forEach(([m,v])=>{t+=num(v);});",
    ),
    (
        "a janela do custo geral deixa de vir do periodo",
        "  const ateM=range?range.to.slice(0,7):'9999-99';\n  const num=(typeof parseNum==='function')?parseNum:(v=>parseFloat(v)||0);\n  let total=0,nLinhas=0;",
        "  const ateM='9999-99';\n  const num=(typeof parseNum==='function')?parseNum:(v=>parseFloat(v)||0);\n  let total=0,nLinhas=0;",
    ),
    (
        "linha sem valor passa a contar como categoria",
        "    if(t>0){total+=t;nLinhas++;}",
        "    total+=t;nLinhas++;",
    ),
    (
        "o custo geral sai do P/L Liquido (volta ao estado anterior a s358)",
        "  const totalCost=costConta+costTipster+costGeral;",
        "  const totalCost=costConta+costTipster;",
    ),
    # ── s358 etapa 3: o custo de TIPSTER ────────────────────────────────────
    (
        "o custo de tipster volta a somar TODO tipster (ignora o filtro)",
        "    if(tipsSel&&tipsSel.size&&!tipsSel.has(nome))return;",
        "",
    ),
    (
        "a janela do custo de tipster deixa de vir do periodo",
        "  const deM=range?range.from.slice(0,7):'0000-00';\n"
        "  const ateM=range?range.to.slice(0,7):'9999-99';\n"
        "  const tipsSel=(typeof msGet==='function')?msGet('ti_'+pag):null;",
        "  const deM='0000-00';\n"
        "  const ateM=range?range.to.slice(0,7):'9999-99';\n"
        "  const tipsSel=(typeof msGet==='function')?msGet('ti_'+pag):null;",
    ),
    (
        "o mes fora do recorte passa a contar",
        "    Object.entries(meses||{}).forEach(([m,v])=>{if(m>=deM&&m<=ateM)t+=num(v);});",
        "    Object.entries(meses||{}).forEach(([m,v])=>{t+=num(v);});",
    ),
    (
        "casa ou operador passam a recortar a assinatura",
        "  const tipsSel=(typeof msGet==='function')?msGet('ti_'+pag):null;\n"
        "  const num=(typeof parseNum==='function')?parseNum:(v=>parseFloat(v)||0);",
        "  const tipsSel=(typeof msGet==='function')?msGet('ca_'+pag):null;\n"
        "  const num=(typeof parseNum==='function')?parseNum:(v=>parseFloat(v)||0);",
    ),
    (
        "o parser caseiro volta no lugar do parseNum (179.90 vira 17.990)",
        "  const tipsSel=(typeof msGet==='function')?msGet('ti_'+pag):null;\n"
        "  const num=(typeof parseNum==='function')?parseNum:(v=>parseFloat(v)||0);",
        "  const tipsSel=(typeof msGet==='function')?msGet('ti_'+pag):null;\n"
        r"  const num=(v=>parseFloat(String(v).replace(/\./g,'').replace(',','.'))||0);",
    ),
    # ── s358: o PARQUE (estoque, fora do P/L) ───────────────────────────────
    (
        "as contas em operacao passam a seguir o periodo da tela",
        "  return _custoNaJanela(hoje,hoje,casasSel,opsSel,'','vivo',contasOk);",
        "  const r=(typeof _selRange==='function')?_selRange(pag):null;\n"
        "  return _custoNaJanela(r?r.from:'0000-01-01',r?r.to:'9999-12-31',casasSel,opsSel,'','vivo',contasOk);",
    ),
    (
        "as contas em operacao passam a medir PAGAMENTO em vez de estoque",
        "  return _custoNaJanela(hoje,hoje,casasSel,opsSel,'','vivo',contasOk);",
        "  return _custoNaJanela(hoje,hoje,casasSel,opsSel,'','pago');",
    ),
    (
        "as contas em operacao deixam de respeitar casa e operador",
        "  return _custoNaJanela(hoje,hoje,casasSel,opsSel,'','vivo',contasOk);",
        "  return _custoNaJanela(hoje,hoje,null,null,'','vivo');",
    ),
    (
        "conta cadastrada e ativa volta a morrer na ultima aposta",
        "    else if(!p.arquivado)v.fim=hoje;",
        "    else if(!p.arquivado&&!v.fim)v.fim=hoje;",
    ),
    (
        "arquivada SEM carimbo volta a ficar viva por aposta de evento futuro",
        "    else if(p.arquivado){if(!v.fim||v.fim>ontem)v.fim=ontem;}",
        "",
    ),
    # ── s358: a régua de CAIXA (o que o P/L cobra) ──────────────────────────
    (
        "o P/L volta a cobrar toda conta VIVA (a regua ate a s358)",
        "        const pago=_dataPagamento(v);",
        "        const pago=(v.fim<de||v.ini>ate)?'':de;",
    ),
    (
        "a compra declarada deixa de mandar sobre a 1a aposta",
        "  if(v.adq&&(!v.pa||v.adq<v.pa))return v.adq;",
        "",
    ),
    (
        "a compra DEDUZIDA passa a mandar (base importada data no dia do import)",
        "  if(v.adq&&(!v.pa||v.adq<v.pa))return v.adq;",
        "  if(v.adq)return v.adq;",
    ),
    (
        "a 1a aposta deixa de datar o pagamento",
        "  return v.pa||v.adq||'';",
        "  return v.adq||'';",
    ),
    (
        "o slot para de guardar a 1a aposta pura",
        "    if(!v.pa||r.data<v.pa)v.pa=r.data;",
        "",
    ),
    (
        # s381: a compra deixou de ser `return` (a renovação cobra independente dela) e
        # virou condição da própria compra. Os dois defeitos são os MESMOS de antes.
        "a conta paga fora do recorte passa a entrar",
        "        if(pago&&pago>=de&&pago<=ate)c=_custoDaConta(forn,casa,nome);",
        "        c=_custoDaConta(forn,casa,nome);",
    ),
    (
        "conta sem data de pagamento nenhuma passa a cobrar",
        "        if(pago&&pago>=de&&pago<=ate)c=_custoDaConta(forn,casa,nome);",
        "        if(!pago||(pago>=de&&pago<=ate))c=_custoDaConta(forn,casa,nome);",
    ),
    (
        "o KPI da Visao Geral volta para o modo 'vivo'",
        "range?range.from:'0000-01-01', range?range.to:'9999-12-31', casasSel, opsSel, '', 'pago');",
        "range?range.from:'0000-01-01', range?range.to:'9999-12-31', casasSel, opsSel, '', 'vivo');",
    ),
    (
        "o drill de casa fica com regua diferente do KPI",
        "  return _custoNaJanela(de||'0000-01-01',ate||'9999-12-31',null,null,nomeCasa,'pago');",
        "  return _custoNaJanela(de||'0000-01-01',ate||'9999-12-31',null,null,nomeCasa,'vivo');",
    ),
    (
        "o modo 'vivo' (parque) passa a medir pagamento — as duas reguas viram uma so",
        "  const vivo=(modo==='vivo');",
        "  const vivo=false;",
    ),
    # ── s322: a janela de vida, que hoje sustenta o parque ──────────────────
    (
        "janela vira 'só o INÍCIO dentro do período' (a régua velha)",
        "if(v.fim<de||v.ini>ate)return;",
        "if(v.ini<de||v.ini>ate)return;",
    ),
    (
        "para de ler as apostas em aberto",
        "  const bilhetes=[].concat(\n"
        "    (typeof DADOS!=='undefined'&&DADOS)?DADOS:[],\n"
        "    (typeof DADOS_ABERTAS!=='undefined'&&DADOS_ABERTAS)?DADOS_ABERTAS:[]);",
        "  const bilhetes=[].concat(\n"
        "    (typeof DADOS!=='undefined'&&DADOS)?DADOS:[],\n"
        "    []);",
    ),
    (
        "ignora a data de compra do cadastro",
        "if(p.adquirida_em&&(!v.ini||p.adquirida_em<v.ini))v.ini=p.adquirida_em;",
        "",
    ),
    (
        "ignora o carimbo de arquivamento",
        "if(p.arquivada_em){if(!v.fim||p.arquivada_em>v.fim)v.fim=p.arquivada_em;}",
        "if(false){}",
    ),
    (
        "conta ativa e ainda sem aposta deixa de valer até hoje",
        "    else if(!p.arquivado)v.fim=hoje;",
        "",
    ),
    (
        "o filtro de casa deixa de recortar o custo",
        "if(casasSel&&casasSel.size&&!casasSel.has(casa))return;",
        "",
    ),
    (
        "o filtro de operador deixa de recortar o custo",
        "if(opsSel&&opsSel.size&&v.op&&!opsSel.has(v.op))return;",
        "",
    ),
    (
        "conta sem custo cadastrado passa a entrar na contagem",
        "      if(!(c>0))return;",
        "",
    ),
    (
        "'Tudo' deixa de significar o parque inteiro (janela nasce vazia)",
        "range?range.from:'0000-01-01', range?range.to:'9999-12-31'",
        "range?range.from:'9999-12-31', range?range.to:'0000-01-01'",
    ),
    # ── Fatia 2: as tres camadas do custo da conta ───────────────────────────
    (
        "o custo PROPRIO da conta deixa de vencer o preco do par",
        "  if(v&&v.custo!=null)return v.custo;",
        "",
    ),
    (
        "o preco do fornecedor passa a ser o de HOJE, e nao o da data de compra",
        # A expressao saiu do corpo do `_custoDaConta` e virou `_dataDoPreco` (s362),
        # para a tela de Custos exibir o MESMO degrau que entrou no numero.
        "  return (v&&(v.adq||v.ini))||'';",
        "  return '';",
    ),
    (
        "a regua do vigente pega o PRIMEIRO degrau em vez do ultimo",
        "  return validos.reduce((a,b)=>a.vigente_desde>=b.vigente_desde?a:b);",
        "  return validos.reduce((a,b)=>a.vigente_desde<=b.vigente_desde?a:b);",
    ),
    (
        "o vigente ignora a data e aceita degrau do futuro",
        "  const validos=degraus.filter(p=>p.vigente_desde<=quando);",
        "  const validos=degraus.slice();",
    ),
    (
        "some a camada herdada (o preco do par), que e o que segura a migracao",
        "  return (typeof custoData!=='undefined'&&custoData[k])||0;",
        "  return 0;",
    ),
    # ── Renovações (s381) ────────────────────────────────────────────────────
    ("a renovacao deixa de cobrar no P/L",
     "        c+=_renovacoesNaJanela(v,de,ate).total;",
     ""),
    ("a renovacao cobra em TODO recorte, e nao so no mes dela",
     "        c+=_renovacoesNaJanela(v,de,ate).total;",
     "        c+=_renovacoesNaJanela(v,'0000-01-01',ate).total;"),
    ("a compra volta a condicionar a renovacao (mes so de renovacao zera)",
     "        if(pago&&pago>=de&&pago<=ate)c=_custoDaConta(forn,casa,nome);",
     "        if(!pago||pago<de||pago>ate)return;c=_custoDaConta(forn,casa,nome);"),
    ("o estoque ignora as renovacoes",
     "c=_custoDaConta(forn,casa,nome)+_renovacoesNaJanela(v,'0000-01-01',ate).total;",
     "c=_custoDaConta(forn,casa,nome);"),
    ("o estoque conta renovacao que ainda nao foi paga",
     "c=_custoDaConta(forn,casa,nome)+_renovacoesNaJanela(v,'0000-01-01',ate).total;",
     "c=_custoDaConta(forn,casa,nome)+_renovacoesNaJanela(v,'0000-01-01','9999-12-31').total;"),
    ("a borda inicial do recorte perde a renovacao do dia 1",
     "if(r.data>=de&&r.data<=ate)",
     "if(r.data>de&&r.data<=ate)"),
    ("a borda final do recorte perde a renovacao do ultimo dia",
     "if(r.data>=de&&r.data<=ate)",
     "if(r.data>=de&&r.data<ate)"),
    ("a janela de vida deixa de carregar as renovacoes do cadastro",
     "    if(p.ren&&p.ren.length)v.ren=p.ren;",
     ""),
    ("a carga aceita renovacao sem data ou sem valor",
     "    .filter(r=>r.data&&r.valor>0);",
     ";"),
    ("a carga le valor em string com parser caseiro (1.200 vira 1,2)",
     "valor:(typeof(r&&r.valor)==='number')?r.valor:num(r&&r.valor)",
     "valor:(typeof(r&&r.valor)==='number')?r.valor:parseFloat(r&&r.valor)"),
]


# Mutações que moram no `overview.js` (render), não no `gestao.js` (régua). O `.mjs` não
# monta DOM, então elas são provadas por LEITURA no teste logo abaixo — registrar aqui em
# vez de inventar asserção é a regra do CLAUDE.md sobre mutação que o harness não alcança.
MUTACOES_DE_RENDER = {
    "o custo geral sai do P/L Liquido (volta ao estado anterior a s358)",
}
MUTACOES = [m for m in MUTACOES if m[0] not in MUTACOES_DE_RENDER]


def test_o_pl_liquido_desconta_os_TRES_custos():
    """Conta, tipster e geral. O geral ficou de fora até a s358: lançado e invisível, que
    é a família de "cobrado e ineditável" ao contrário — as duas erram o resultado final.
    E o card tem de APARECER quando há valor: KPI que desconta o que não está na tela é
    inauditável."""
    ov = _sem_comentarios(OVERVIEW.read_text(encoding="utf-8"))
    assert "costConta+costTipster+costGeral" in ov.replace(" ", ""), (
        "o P/L Líquido parou de descontar algum dos três custos (s358)"
    )
    assert "calcCustoGeralFiltrado" in ov, "renderKPI não lê mais o custo geral"
    assert "Custos Gerais" in ov, (
        "o card de Custos Gerais sumiu do render: o P/L desconta um valor que não está "
        "na tela, e o leitor não tem como conferir a conta"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    """Quebra o gestao.js de propósito e exige que o .mjs fique VERMELHO.

    A cópia estragada entra pelo `ALVO_GESTAO` — o .mjs recorta dela em vez do arquivo de
    produção, então a mutação é exercida pelo código real, não por uma reimplementação."""
    src = GESTAO.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no gestao.js "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    alvo = tmp_path / "gestao.js"
    alvo.write_text(src.replace(de, para), encoding="utf-8")
    r = subprocess.run(
        ["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
        cwd=str(RAIZ), env={**__import__("os").environ, "ALVO_GESTAO": str(alvo)},
    )
    assert r.returncode != 0, (
        f"mutação «{titulo}» passou VERDE — o teste não detecta o que ele promete "
        "detectar. O defeito está no teste, não no código."
    )
