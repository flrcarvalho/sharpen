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
    assert "async def bilhete_sem_codigo" in repo
    assert 'extra["sem_codigo"] = await bilhete_sem_codigo' in main
    assert '"aposta" in campos' in main, "o aviso passou a consultar em toda edição"
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


def test_cache_bust_subiu():
    """JS/CSS do dash editados sem bump de `?v=` chegam ao tester como versão velha —
    o recurso 'não funciona' e nada no console diz por quê."""
    html = DASH_HTML.read_text(encoding="utf-8")
    assert "assets/js/charts/apostas.js?v=17" in html, "bumpe o ?v= do apostas.js"
    assert "assets/css/components.css?v=24" in html, "bumpe o ?v= do components.css"


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
