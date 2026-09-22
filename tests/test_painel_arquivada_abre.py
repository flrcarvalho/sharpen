"""Conta ARQUIVADA também abre na Extração (s381, pedido do Feca).

No Painel de Contas a linha inteira abre a conta na Extração. Até a s381 isso valia só
na aba Ativas (`clic = contasTab === 'ativas'` decidia o clique E a ação), e a conta
arquivada ficava sem caminho para conferir custo, renovação e histórico.

O que este teste NÃO cobre: o clique de verdade (o render foi medido em headless no
demo) e o comportamento da Extração com a conta aberta, que é o mesmo da ativa.
"""
import re
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "app" / "static" / "index.html"


def _src():
    return INDEX.read_text(encoding="utf-8")


def test_a_linha_do_painel_e_clicavel_nas_duas_abas():
    src = _src()
    m = re.search(r"html \+= '<div class=\"conta-row([^\"']*)", src)
    assert m, "não achei a montagem da linha de conta do Painel"
    assert m.group(1) == " clickable", (
        "a classe da linha voltou a depender da aba: conta arquivada perde o clique")
    assert "' onclick=\"contasAbrir(' + p.id + ',this.dataset.casa)\" title=\"Abrir na Extração\"'" in src, (
        "o onclick da linha voltou a ser condicional (ou sumiu)")


def test_as_acoes_param_a_propagacao_nas_duas_abas():
    """Com a linha clicável nas duas abas, Reativar/Editar/Excluir sem stopPropagation
    abririam a Extração junto com a ação."""
    assert "const stop = 'event.stopPropagation();';" in _src()


def test_abrir_procura_tambem_entre_as_arquivadas():
    src = _src()
    m = re.search(r"function contasAbrir\(id, casa\) \{([\s\S]*?)\n\}", src)
    assert m and "parceirosArquivadosCache" in m.group(1), (
        "contasAbrir não procura mais a conta entre as arquivadas")
