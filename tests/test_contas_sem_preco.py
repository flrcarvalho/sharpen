"""Aba Contas: conta SEM PREÇO diz isso na linha e no rodapé (s381, tester Gabriel).

Conta sem custo lançado fica FORA do ROI líquido e do bruto do painel 2 (ausência não
é zero). A linha mostrava um "·" mudo, e o Gabriel leu duas contas arquivadas com P/L
certo como "não puxou o P/L". Agora a linha diz "sem preço" e o rodapé diz quantas
ficaram fora dos dois ROIs.

O que este teste NÃO cobre: a conta (quem tem preço) é do `contas_vida.mjs`, e o
alinhamento do rótulo foi medido no demo em headless — o `inline-block` da
`.vv--conta` existe porque, em flex, o grid espremia o último item em 6px.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTAS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "contas.js"
CSS = RAIZ / "app" / "static" / "dash" / "assets" / "css" / "components.css"


def test_a_linha_da_conta_sem_preco_diz_sem_preco():
    src = CONTAS.read_text(encoding="utf-8")
    assert "const semPreco=!_cnTemPreco(c);" in src
    assert "const roiC=c.turn>0&&!semPreco?" in src, "o ROI voltou a ser calculado sem olhar o preço"
    assert "</b> · ${semPreco\n            ?'<span class=\"cn-sem cn-warnc\"" in src, (
        "o rótulo deixou de depender de semPreco (texto presente não prova que ele aparece)")
    assert ">sem preço</span>'\n            :_cnPctTxt(roiC)}" in src, (
        "a linha sem preço voltou a cair no '·' mudo do _cnPctTxt")


def test_o_rodape_do_painel_2_conta_quem_ficou_fora_dos_dois_rois():
    src = CONTAS.read_text(encoding="utf-8")
    assert "sem preço</span> ficam fora dos dois ROIs." in src
    assert "+(G.nSemPreco\n" in src, "o aviso do rodapé deixou de depender do nSemPreco"


def test_a_linha_da_conta_nao_espreme_o_rotulo():
    assert '<span class="vv vv--conta">' in CONTAS.read_text(encoding="utf-8")
    assert ".cn-mrow .vv.vv--conta     { display: inline-block; }" in CSS.read_text(encoding="utf-8")
