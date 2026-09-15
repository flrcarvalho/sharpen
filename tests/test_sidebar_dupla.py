"""As DUAS sidebars têm de oferecer as MESMAS telas (s358).

O usuário navega pela casca `app/static/app.html`, que tem a própria sidebar hardcoded;
o `dash/assets/js/app.js` monta OUTRA, que só aparece no `/dashboard/` standalone. São
duas listas escritas à mão, e nada as ligava.

O preço já foi pago duas vezes:

* **s144** — a tela "Tipster / Método" entrou só no `dash/app.js`. O Feca não achou o item
  nem em aba anônima, porque a sidebar que ele vê é a do `app.html`.
* **s358** — a Fatia 5 tirou `Custos de Contas`, `Custos de Tipsters` e
  `Fornecedores & Parceiros` do menu. Tirar de uma só teria deixado o produto com dois
  menus discordando, e o sintoma seria "sumiu para mim e não sumiu para ele".

Este teste compara as duas listas e falha na diferença, em qualquer direção. Ele não julga
QUAIS telas existem — só exige que as duas cascas concordem.

O que NÃO cobre: a ORDEM dos itens e os grupos (`nav-group`), que são de desenho e podem
divergir de propósito; e o roteamento — item no menu não prova que a página abre. Isso é
render headless.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CASCA = RAIZ / "app" / "static" / "app.html"
DASH = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"


def _telas_da_casca() -> set[str]:
    """`<div class="nav-item" data-key="dash:<id>" …>` — só as rotas do dashboard.

    Itens sem `data-key` ficam de fora de propósito: "Minha conta" é AÇÃO (abre modal e
    não mexe no hash, s288), e item que não é rota não tem par do outro lado."""
    html = CASCA.read_text(encoding="utf-8")
    return set(re.findall(r'data-key="dash:([a-z0-9_]+)"', html))


def _telas_do_dash() -> set[str]:
    """Os arrays `['<id>','<Rótulo>','<svg>']` que o `buildHTML` transforma em nav-item."""
    js = DASH.read_text(encoding="utf-8")
    # O bloco da sidebar vai do primeiro `nav-group` até o fim do `buildHTML`; fora dele
    # há outros arrays de 3 strings (PAGE_META e afins) que não são menu.
    ini = js.index('<div class="nav-group">')
    fim = js.index('_PAGS_FILTRO') if '_PAGS_FILTRO' in js[ini:] else len(js)
    bloco = js[ini:ini + 12000]
    return set(re.findall(r"^\s*\['([a-z0-9_]+)','[^']+','", bloco, re.M))


def test_as_duas_sidebars_oferecem_as_mesmas_telas():
    casca, dash = _telas_da_casca(), _telas_do_dash()
    assert casca, "não achei nav-item nenhum no app.html — o regex ficou para trás"
    assert dash, "não achei item de nav no dash/app.js — o regex ficou para trás"
    so_casca = sorted(casca - dash)
    so_dash = sorted(dash - casca)
    assert not so_casca and not so_dash, (
        "as duas sidebars discordam e o usuário vê só a da casca (memória da s144):\n"
        f"  só em app.html:        {so_casca or '—'}\n"
        f"  só em dash/app.js:     {so_dash or '—'}\n"
        "Adicionar ou remover tela exige mexer NOS DOIS."
    )


def test_as_tres_telas_de_custo_antigas_sairam_do_menu():
    """Fatia 5 do PLANO_CUSTOS_TELA_UNICA, decisão do Feca em 14/09/2026. Elas seguem no
    CÓDIGO, alcançáveis por hash direto — o que saiu foi o menu."""
    fora = {"custos", "custos_tipster", "parceiros"}
    for nome, telas in (("app.html", _telas_da_casca()), ("dash/app.js", _telas_do_dash())):
        voltou = sorted(fora & telas)
        assert not voltou, (
            f"{nome}: {voltou} voltou ao menu. As três telas antigas de custo saíram na "
            "Fatia 5; a tela única `custos_v2` as substitui (s358)"
        )
    assert "custos_v2" in _telas_da_casca(), "a tela de Custos sumiu do menu da casca"
    assert "custos_v2" in _telas_do_dash(), "a tela de Custos sumiu do menu do dash"
