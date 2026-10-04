"""Uma regra só para o nome da casa (s391, Megapari).

O caso: criar/editar conta usava a grafia da BASE (`casa_canonica`) e o `/salvar` usava a do
REGISTRO (`_casa_display`). A Megapari foi registrada como `MegaPari`, a base já tinha
`Megapari`: a conta nasceu numa grafia e os 20 bilhetes da 1ª captura foram gravados na
outra, invisíveis na conta, sem erro nenhum.

Gates:
1. `_casa_registrada` (recortada do `main.py` real, nunca copiada): sem caixa e sem espaço,
   casa fora do registro devolve None.
2. Os TRÊS caminhos que gravam casa passam pela mesma regra: `POST /parceiros`,
   `/parceiros/{id}/editar` e o `/salvar` sem conta. O `/salvar` COM conta grava na casa da
   conta, verbatim: impor o registro ali deixaria o bilhete invisível numa conta variante.
   Conferido no texto das funções, com mutação.

O que NÃO está coberto: a base em produção. Quem confere base × registro é o
`tools/audit_grafias.py` (precisa do banco), e importadores por script que gravam `casa`
direto no SQL não passam por aqui; o audit os pega depois.
"""
import re
from pathlib import Path

import pytest

MAIN = Path(__file__).resolve().parent.parent / "app" / "main.py"


def _src() -> str:
    return MAIN.read_text(encoding="utf-8").replace("\r\n", "\n")


def _funcao(src: str, assinatura: str) -> str:
    i = src.index(assinatura)
    m = re.search(r"\n(?=@app\.|def |async def |class |# ── )", src[i + len(assinatura):])
    return src[i: i + len(assinatura) + (m.start() if m else len(src))]


def _registrada(src: str):
    ns = {"_CASA_DISPLAY": {"MEGAPARI": "Megapari", "DEXSPORT": "DEX Sport", "BET365": "Bet365"}}
    exec(_funcao(src, "def _norm_casa(") + "\n" + _funcao(src, "def _casa_registrada("), ns)
    return ns["_casa_registrada"]


def _falhas(src: str) -> list[str]:
    f = []
    reg = _registrada(src)
    casos = {"MegaPari": "Megapari", "megapari": "Megapari", "Mega Pari": "Megapari",
             "dexsport": "DEX Sport", "DEX Sport": "DEX Sport", "bet 365": "Bet365",
             "Bingoplus": None, "": None}
    for nome, esperado in casos.items():
        if reg(nome) != esperado:
            f.append(f"_casa_registrada({nome!r}) devolveu {reg(nome)!r}, esperado {esperado!r}")

    criar = _funcao(src, "async def criar_parceiro_route(")
    if "casa_oficial(" not in criar or "_casa_display(" in criar:
        f.append("POST /parceiros não usa `casa_oficial`")
    editar = _funcao(src, "async def editar_parceiro_route(")
    if "casa_oficial(" not in editar or "_casa_display(" in editar:
        f.append("/parceiros/{id}/editar não usa `casa_oficial`")
    salvar = _funcao(src, "async def salvar(")
    if "casa_txt = await casa_oficial(casa_txt)" not in salvar:
        f.append("/salvar sem conta não passa a casa pela regra única")
    if "_casa_registrada(" in salvar:
        f.append("/salvar com conta troca a grafia DA CONTA pela do registro (bilhete invisível)")
    if 'row["casa"] = casa_txt' not in salvar or "row[\"casa\"] = _casa_display(" in salvar:
        f.append("/salvar grava a casa por outro caminho que não a regra única")
    oficial = _funcao(src, "async def casa_oficial(")
    if "_casa_registrada(nome) or await casa_canonica(nome)" not in oficial:
        f.append("`casa_oficial` não põe o registro antes da base")
    return f


def test_uma_regra_so():
    assert _falhas(_src()) == []


MUTACOES = [
    ("compara com caixa", "    return \"\".join(str(nome or \"\").split()).lower()", "    return \"\".join(str(nome or \"\").split())"),
    ("compara com espaço", "    return \"\".join(str(nome or \"\").split()).lower()", "    return str(nome or \"\").lower()"),
    ("criar volta à base", "    row = await criar_parceiro(await casa_oficial(body.casa), nome, dono, moeda)",
     "    row = await criar_parceiro(await casa_canonica(_casa_display(casa_key)), nome, dono, moeda)"),
    ("editar volta à base", "        casa = await casa_oficial(casa)",
     "        casa = await casa_canonica(_casa_display(_display_to_key(casa)))"),
    ("salvar sem conta volta à base", "        casa_txt = await casa_oficial(casa_txt)",
     "        casa_txt = await casa_canonica(casa_txt)"),
    ("salvar com conta impõe o registro", "    casa_key = _display_to_key(casa_txt) if casa_txt else None",
     "    casa_txt = _casa_registrada(casa_txt) or casa_txt\n    casa_key = _display_to_key(casa_txt) if casa_txt else None"),
    ("salvar volta ao round-trip", '            row["casa"] = casa_txt', '            row["casa"] = _casa_display(casa_key)'),
    ("base antes do registro", "    return _casa_registrada(nome) or await casa_canonica(nome)",
     "    return await casa_canonica(nome) or _casa_registrada(nome)"),
]


@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes(titulo, de, para):
    src = _src()
    assert src.count(de) == 1, f"âncora «{titulo}» não é única ({src.count(de)})"
    assert _falhas(src.replace(de, para, 1)), f"a mutação «{titulo}» passou despercebida"
