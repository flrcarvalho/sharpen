"""Menu de mercados da coluna `Aposta` (s286) — o que quebra em SILÊNCIO.

Pedido do Feca: tipster que não planilha "Múltipla" e sim "Cartões" precisa trocar o
mercado sem digitar tudo à mão. Duplo-clique abre os favoritos (os mais usados dele);
o botão ✎ abre a lista completa (MASTER_APOSTAS §3 ∪ a base dele).

Os gates aqui existem porque as três formas de esse recurso morrer não dão erro nenhum:

  1. `.btbl-tipo` perder o `data-field="aposta"` — a célula volta a ser texto morto e o
     duplo-clique simplesmente não faz nada. Nenhum log, nenhuma exceção;
  2. o campo do modal perder a classe do menu — o input continua funcionando, digitável,
     e só o menu some. Parece "o dropdown ainda não carregou";
  3. a contagem cair para `--ink-mute` — mede 2,86:1 sobre `--elevated` (#1A2029), abaixo
     do piso de 3:1 do papel "metadado secundário" da Escada de Tinta. Continua legível
     no monitor de quem escreveu, e reprova para quem lê.

A prova de COMPORTAMENTO (união das listas, corte dos favoritos, fav↔todos, render do
item) roda em `tests/js/menu_mercados.mjs`, que executa o código recortado do próprio
`index.html`. Este arquivo o invoca — ver `test_prova_por_execucao_do_menu`.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "app" / "static" / "index.html"
MAIN = RAIZ / "app" / "main.py"
REPO = RAIZ / "app" / "repository.py"
DASH_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "apostas.js"
DASH_CSS = RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css"
DASH_HTML = RAIZ / "app" / "static" / "dash" / "index.html"
ABERTAS_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "abertas.js"


@pytest.fixture(scope="module")
def index() -> str:
    return INDEX.read_text(encoding="utf-8")


def test_celula_de_categoria_e_editavel(index: str):
    """Sem `data-field`, o duplo-clique não abre nada — e não avisa que não abriu."""
    assert 'class="btbl-tipo ap-edit' in index, "a célula da categoria perdeu a classe de edição"
    assert 'data-field="aposta"' in index, "a célula da categoria perdeu o data-field"


def test_glifo_de_incerteza_nao_briga_com_o_duplo_clique(index: str):
    """O `onclick` que abre o modal vive no GLIFO, nunca na célula.

    Na célula, os dois cliques do duplo-clique disparam `click` antes do `dblclick`: o
    modal abria por cima da edição inline. O `stopPropagation` mantém os dois gestos
    convivendo — clique no glifo abre o modal, duplo-clique na célula abre o menu.
    """
    assert 'class="btbl-tipo ap-edit${tipoIncerta ? \' incerta\' : \'\'}" data-field="aposta"' in index
    assert "event.stopPropagation();abrirEdicao(" in index, "o glifo perdeu o stopPropagation"


def test_os_dois_menus_estao_ligados(index: str):
    """Duplo-clique → favoritos; modal → lista completa. Classes distintas de propósito."""
    assert "'ap-inline-inp' + (field === 'aposta' ? ' js-ac-mercado' : '')" in index, \
        "o editor inline não liga mais o menu de mercado"
    assert 'id="ed-aposta" class="js-ac-mercado-todos"' in index, \
        "o campo Aposta do modal perdeu o menu completo"


def test_contagem_nao_usa_ink_mute(index: str):
    """Escada de Tinta: `--ink-mute` mede 2,86:1 sobre `--elevated`, abaixo do piso de 3:1.

    A hierarquia do item de mercado sai por TAMANHO (10px contra 12/13px) e por tom
    (`--ink` no nome, `--ink-soft` na contagem), os dois acima do piso do papel.
    """
    bloco = index[index.index(".ac-count {"):]
    bloco = bloco[:bloco.index("}")]
    assert "--ink-soft" in bloco, "a contagem saiu de --ink-soft"
    assert "--ink-mute" not in bloco, "a contagem caiu para --ink-mute (2,86:1 — reprova)"
    assert "font-size: 10px" in bloco, "a contagem saiu do piso de 10px"


def test_contagem_nao_abrevia_milhar(index: str):
    """`toLocaleString('pt-BR')`, nunca `k`/`M` — a regra de milhar do check-tokens §d."""
    assert "n.toLocaleString('pt-BR')" in index
    assert "ac-count\">${n}" not in index, "a contagem virou número cru (sem separador pt-BR)"


def test_uniao_com_a_taxonomia_do_master(index: str):
    """O menu completo lê o MASTER pela rota, não por lista copiada.

    Copiar as categorias no cliente adicionaria mais uma linha à regra de propagação do
    CLAUDE.md — e regra escrita sem gate é regra pulada.
    """
    assert "fetch('/taxonomia')" in index, "o menu parou de ler a taxonomia canônica"
    assert "fetch('/mercados')" in index, "o menu parou de ler os mercados do dono"


def test_rota_de_mercados_existe():
    main = MAIN.read_text(encoding="utf-8")
    repo = REPO.read_text(encoding="utf-8")
    assert '@app.get("/mercados")' in main
    assert "list_mercados" in main and "async def list_mercados" in repo
    assert "GROUP BY aposta ORDER BY n DESC" in repo, "os favoritos deixaram de sair por frequência"


def test_aviso_de_duplicata_chega_a_quem_edita():
    """`aposta` está em `_SIG_COLS`: renomear bilhete SEM código muda a assinatura, e a
    próxima captura da casa insere linha nova em vez de deduplicar. O aviso sai na hora
    porque a duplicata só apareceria dias depois, longe da causa."""
    main = MAIN.read_text(encoding="utf-8")
    repo = REPO.read_text(encoding="utf-8")
    index_txt = INDEX.read_text(encoding="utf-8")
    assert "async def flags_pos_edicao" in repo
    assert "extra = await flags_pos_edicao(bilhete_id, dono, set(campos))" in main
    assert '"aposta" in campos' in repo, "o aviso deixou de depender do campo editado"
    assert "resp.sem_codigo" in index_txt, "a tela não usa mais o aviso do servidor"
    assert "aposta" in repo[repo.index("_SIG_COLS = frozenset"):repo.index("_SIG_COLS = frozenset") + 200], \
        "se `aposta` saiu da assinatura, este aviso virou mentira — reveja o texto"


# ── Dashboard: Minha Base e Em Aberto ──────────────────────────────────────────


def test_dash_liga_os_dois_menus():
    """Duplo-clique → favoritos (`AC_MKT`); modal ✎ → lista completa (`AC_MKT_TODOS`)."""
    js = DASH_JS.read_text(encoding="utf-8")
    assert "if(field==='aposta'){_acLigar(editor,()=>finish(true),AC_MKT);" in js,         "a edição inline não liga mais o menu de mercado"
    assert "_acLigar(elMkt,null,AC_MKT_TODOS)" in js, "o modal perdeu o menu completo"


def test_dash_conta_pela_tela_e_nao_pela_rota():
    """A frequência sai de `DADOS ∪ DADOS_ABERTAS`, nunca de /mercados.

    Para um supervisor o feed inclui a base dos operadores; contar no servidor daria um
    menu que não corresponde à tela que ele está olhando. E `DADOS` sozinho repetiria o
    ponto cego da s239 — quem só tem aposta em aberto sumiria do próprio menu.
    """
    js = DASH_JS.read_text(encoding="utf-8")
    bloco = js[js.index("function _apMercadoCont()"):js.index("function _apMercadoFav()")]
    assert "DADOS_ABERTAS" in bloco, "a contagem parou de somar as apostas em aberto"
    assert "fetch('/mercados')" not in js, "o dashboard passou a contar pela rota da Extração"


def test_dash_avisa_sem_esconder_o_aviso_atras_do_modal():
    """O toast vive no `body` e dura 10s — o modal fecha logo depois de salvar, então um
    aviso preso a ele desapareceria junto com a causa."""
    js = DASH_JS.read_text(encoding="utf-8")
    css = DASH_CSS.read_text(encoding="utf-8")
    assert "function apAviso(" in js and "document.body.appendChild(el)" in js
    assert "resp.sem_codigo" in js, "a tela não usa mais o aviso do servidor"
    assert ".ap-aviso {" in css
    bloco = css[css.index(".ap-aviso {"):css.index(".ap-aviso__ico")]
    assert "#" not in bloco, "o aviso ganhou cor literal — o _errBanner é desvio, não modelo"


def test_dash_contagem_respeita_a_escada(index: str):
    css = DASH_CSS.read_text(encoding="utf-8")
    bloco = css[css.index(".ac-count {"):]
    bloco = bloco[:bloco.index("}")]
    assert "--ink-soft" in bloco and "--ink-mute" not in bloco
    assert "font-size: 10px" in bloco
    js = DASH_JS.read_text(encoding="utf-8")
    assert "n.toLocaleString('pt-BR')" in js, "a contagem do dash abreviou ou virou número cru"


@pytest.mark.parametrize("arquivo,piso", [
    ("assets/js/charts/apostas.js", 19),
    ("assets/js/charts/abertas.js", 3),
    ("assets/css/components.css", 25),
])
def test_cache_bust_nao_regride(arquivo: str, piso: int):
    """JS/CSS do dash editados sem bump de `?v=` chegam ao tester como versão VELHA — o
    recurso "não funciona" e nada no console diz por quê.

    PISO, não valor exato: travar o número faria este teste quebrar em toda edição futura
    dos mesmos arquivos, e teste que grita sem motivo é teste que se aprende a ignorar. Ele
    pega o que interessa — alguém REMOVER o `?v=` ou fazer o número andar para trás.
    """
    html = DASH_HTML.read_text(encoding="utf-8")
    m = re.search(re.escape(arquivo) + r"\?v=(\d+)", html)
    assert m, f"{arquivo} perdeu o ?v= — o cache do navegador passa a mandar"
    assert int(m.group(1)) >= piso, f"{arquivo}?v= regrediu (é {m.group(1)}, piso {piso})"


# ── Em Aberto: edição inline inteira (etapa 3) ─────────────────────────────────


def test_abertas_liga_a_edicao_inline():
    """A aba nunca teve edição inline; agora tem, reusando o motor da Minha Base.

    Três peças, e nenhuma delas avisa se sumir: a linha precisa do `data-id` (é por ele que
    `_apInlineStart` acha o bilhete), as células precisam do `data-field`, e o listener
    precisa incluir `#page-abertas` — sem ele o duplo-clique não faz nada, calado.
    """
    js = ABERTAS_JS.read_text(encoding="utf-8")
    ap = DASH_JS.read_text(encoding="utf-8")
    assert 'data-id="${r.id}"' in js, "a linha da aba perdeu o data-id"
    assert "#page-abertas [data-field]" in ap, "o listener parou de cobrir a aba Em Aberto"
    assert "cell.closest('[data-id]')" in ap,         "o motor voltou a procurar .btbl-data-row — a linha da aba Em Aberto não é essa"
    for campo in ("data", "aposta", "descricao", "esporte", "tipster", "casa", "parceiro",
                  "stake", "odd"):
        assert "df('%s')" % campo in js, f"campo {campo} não é editável na aba Em Aberto"


def test_abertas_nao_edita_o_que_nao_tem_destino():
    """Retorno é DERIVADO (stake × odd) e Resultado não existe como coluna nesta tela.

    Uma célula que aceita duplo-clique e não tem onde gravar é pior que uma que não aceita:
    o usuário digita, o valor some no re-render, e nada explica por quê.
    """
    js = ABERTAS_JS.read_text(encoding="utf-8")
    ini = js.index("const df = f => editavel")
    linha = js[ini:js.index("}).join('');", ini)]
    assert "df('retorno')" not in linha and "df('resultado')" not in linha
    assert 'abrt-ret' in linha and 'data-field' not in linha[linha.index('abrt-ret'):linha.index('abrt-acts')],         "a célula de Retorno virou editável — ela é derivada, não tem destino no banco"


def test_abertas_nao_repinta_por_cima_da_edicao():
    """`loadData` revalida em 2º plano e reconstrói a tela: no meio de uma edição isso
    mataria o input com o texto já digitado dentro. A guarda fica na ENTRADA do render —
    repintar KPI e calendário com a lista congelada deixaria a tela contando uma coisa e
    mostrando outra."""
    js = ABERTAS_JS.read_text(encoding="utf-8")
    corpo = js[js.index("function renderAbertas()"):js.index("// ── 1) KPIs")]
    assert "if (_apInlineEditing) return;" in corpo


def test_categoria_da_aba_em_aberto_respeita_a_escada():
    """`.abrt-tipo` é a coluna Aposta da aba Em Aberto — e o alvo do duplo-clique.

    Era `--ink-mute` em `--text-nano` (9px): 3,17:1 sobre `--surface` e 3,03:1 no hover,
    com papel de LABEL (piso 4,5:1). A Escada de Tinta proíbe `--ink-mute` abaixo de 10px
    em qualquer superfície — é o mesmo defeito que originou a regra. Em `--ink-soft` a
    10px dá 6,9:1. Este gate existe porque o grep de px literal é CEGO aqui: o tamanho
    vinha de token, não de número.
    """
    css = DASH_CSS.read_text(encoding="utf-8")
    bloco = css[css.index(".abrt-tipo {"):]
    bloco = bloco[:bloco.index("}")]
    assert "--ink-mute" not in bloco, "a categoria voltou para --ink-mute (3,17:1 — reprova)"
    assert "--text-nano" not in bloco, "a categoria voltou para 9px (abaixo do piso da Escada)"
    assert "--ink-soft" in bloco and "--text-xxs" in bloco


def test_aviso_de_edicao_volatil_existe_nos_dois_fronts():
    """Editar data/odd/stake de aposta ABERTA de fonte automática é DESFEITO pelo próximo
    envio do robô (o `ON CONFLICT` refresca esses campos enquanto a linha não resolve).

    É o modo de falha mais traiçoeiro desta etapa: a tela aceita, salva, mostra o valor
    novo — e horas depois ele volta ao que era. A aba Em Aberto, por definição, só tem
    linhas nesse estado, então o aviso não é opcional lá.
    """
    repo = REPO.read_text(encoding="utf-8")
    assert '_CAMPOS_VOLATEIS = frozenset({"data", "odd", "stake"})' in repo
    assert 'row["extraction_state"] == "aberta"' in repo and '!= "manual"' in repo,         "o aviso deixou de checar estado/origem — passaria a acusar linha que não corre risco"
    assert "AVISO_VOLATIL" in DASH_JS.read_text(encoding="utf-8")
    assert "resp.volatil" in INDEX.read_text(encoding="utf-8"),         "a Extração parou de avisar (a grade dela também edita stake/odd de aposta aberta)"


def test_rolar_dentro_do_menu_nao_fecha_o_menu():
    """Bug do tester Marlon (s287): "o scroll/barra lateral não estão funcionando".

    O handler de scroll é registrado em CAPTURA no `window` — obrigatório, porque scroll
    não borbulha —, então ele recebia também o scroll de DENTRO do `.ac-menu`: rolar a
    lista para achar um mercado fechava o menu. Latente desde sempre; o menu de tipster
    cabia na tela, o de mercado tem 27+ itens e sempre precisa rolar.
    """
    js = DASH_JS.read_text(encoding="utf-8")
    idx = INDEX.read_text(encoding="utf-8")
    assert "if(!_acRolagemInterna(e))_acScrollFora()" in js,         "o handler do dash voltou a fechar o menu em qualquer scroll"
    assert "'.ac-menu,.shcal'" in js, "o guard perdeu o menu ou o calendário"
    assert "closest('.ac-menu, .shcal')" in idx,         "a Extração voltou a fechar o menu ao rolar dentro dele"


def test_rolar_encerra_a_edicao_para_a_tabela_voltar_a_rolar():
    """O segundo bug da mesma queixa, e o que parecia pane geral: com a edição inline
    aberta, `renderApostasVirt` volta cedo, então rolar movia a barra e não redesenhava
    linha nenhuma. Encerrar com COMMIT ao rolar devolve o scroll na hora — mesma semântica
    do blur, que já salva ao clicar fora. `fim(false)` aqui descartaria o que foi digitado.
    """
    js = DASH_JS.read_text(encoding="utf-8")
    assert "let _apInlineFim=null;" in js
    assert "if(fim){_apInlineFim=null;fim(true);}" in js,         "rolar deixou de encerrar a edição, ou passou a encerrar descartando"
    assert "_apInlineFim=finish;" in js, "a edição não registra mais o seu finish"
    # A flag cai antes de SharpenCal.fechar(): presa em true, congela a tabela para sempre.
    corpo = js[js.index("const finish=async(commit)=>{"):]
    corpo = corpo[:corpo.index("editor.addEventListener('keydown'")]
    assert corpo.index("_apInlineEditing=false;") < corpo.index("SharpenCal.fechar()"),         "a flag que congela a tabela caiu depois de uma chamada que pode lançar"


def test_menu_nao_atravessa_a_tela():
    """O editor inline ocupa a CÉLULA, e na Minha Base ela chega a ~1700px: sem teto, o
    menu virava uma faixa atravessando a tela com a contagem no outro extremo do olho."""
    js = DASH_JS.read_text(encoding="utf-8")
    assert "Math.min(Math.max(r.width,160),AC_MAX_W)" in js
    assert "const AC_MAX_W=360;" in js


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_scroll():
    """12 asserções sobre o roteamento do scroll, com a LIGAÇÃO recortada do arquivo.

    Provado por mutação: 7/7 detectadas, incluindo a que reintroduz o bug original. Duas
    escaparam na 1ª versão e o teste foi refeito por isso: ele reimplementava o
    `if (!interna) fora()` em vez de usar o listener real, e o dublê do finish ignorava o
    argumento — então "encerrar descartando o que foi digitado" passava verde.
    """
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "menu_scroll.mjs")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_menu_no_dash():
    """23 asserções sobre as fontes do dashboard. Provado por mutação: 10/10 detectadas.

    Três mutações ESCAPARAM na primeira versão e o teste foi reforçado por causa disso:
    o feed sintético não tinha mercados suficientes para o corte de 12 ser exercido, não
    havia empate real para o desempate alfabético decidir, e o mercado "só da base"
    também estava na taxonomia. Teste verde não é teste que detecta.
    """
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "menu_mercados_dash.mjs")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_menu():
    """Roda o código RECORTADO do index.html contra listas sintéticas (23 asserções).

    Provado por mutação: 7/7 detectadas. Ver o cabeçalho de tests/js/menu_mercados.mjs.
    """
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "menu_mercados.mjs")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert r.returncode == 0, r.stdout + r.stderr
