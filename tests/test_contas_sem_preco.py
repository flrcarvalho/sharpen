"""Aba Contas: conta SEM PREÇO entra no ROI e é AVISADA (s381, decisão do Feca).

Regra: "zero é preço; sem custo lançado é sem preço. Em ambos os casos não tiraremos do
PL e o ROI deve contá-las, mesmo que infle — porém deve-se informar o usuário que tem X
contas sem preço lançado e que ele pode lançar ZERO para elas."

Então a linha da conta mostra o ROI SEMPRE (com custo zero para a sem preço), a sem
preço ganha a tag "sem preço" ao lado do nome, e os rodapés dos painéis 2 e 3 dizem
quantas são e o que fazer, pela MESMA função.

O que este teste NÃO cobre: a aritmética (quem entra no ROI, zero vencendo a tabela) é do
`contas_vida.mjs`, seções 10, 13 e 17; o alinhamento foi medido no demo em headless.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTAS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "contas.js"
CSS = RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css"


def _src():
    return CONTAS.read_text(encoding="utf-8")


def test_a_linha_mostra_o_roi_mesmo_sem_preco():
    src = _src()
    assert "const roiC=c.turn>0?((c.pl-c.custo)/c.turn*100):null;" in src, (
        "o ROI da linha voltou a depender do preço: a sem preço sai do número")
    assert "<b>${fmtR(c.turn)}</b> · ${_cnPctTxt(roiC)}</span></div>`;" in src


def test_a_conta_sem_preco_ganha_a_tag_ao_lado_do_nome():
    src = _src()
    assert "const semPreco=!_cnTemPreco(c);" in src
    assert "<span class=\"nm\">${esc(c.conta)}${semPreco\n            ?' <span class=\"cn-sem cn-warnc\"" in src, (
        "a tag deixou de depender de semPreco (texto presente não prova que ele aparece)")
    assert ">sem preço</span>'\n            :''}</span>`" in src


def test_os_dois_rodapes_avisam_pela_mesma_funcao():
    src = _src()
    assert "entram com custo zero, e o retorno pode estar otimista." in src
    assert "(R$ 0 se foi grátis)" in src, "o aviso deixou de dizer que dá para lançar zero"
    assert "+_cnAvisoSemPreco(G.nSemPreco));" in src, "o rodapé do painel 2 perdeu o aviso"
    assert "const notaSem=G.nSemPreco?_cnAvisoSemPreco(G.nSemPreco):" in src, (
        "o painel 3 voltou a ter texto próprio (duas cópias divergem)")


def test_a_linha_da_conta_nao_espreme_o_valor():
    assert '<span class="vv vv--conta">' in _src()
    assert ".cn-mrow .vv.vv--conta     { display: inline-block; }" in CSS.read_text(encoding="utf-8")
