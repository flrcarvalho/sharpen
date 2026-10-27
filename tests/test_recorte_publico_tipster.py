"""Duas vitrines públicas na MESMA conta: o recorte por tipster (26/10/2026).

O Soh Props - Vip e o Soh Props - Nômade são grupos diferentes dos mesmos donos e
moram na conta `sohprops`. Os donos veem as duas carteiras juntas; os clientes de
cada grupo têm o link do seu. Sem o recorte, `/tipsters/sohpropsvips` passaria a
mostrar as apostas do Nômade no dia em que o bot dele planilhasse a primeira, sem
erro nenhum: a página só ficaria com o P/L de outra carteira somado.

Os testes passam pela ROTA de verdade (`/tipsters/<slug>/data`); só a leitura do
banco (`dashboard_rows`) é trocada por linhas fixas.

O que este arquivo NÃO cobre: a grafia que o bot grava na coluna `tipster` (ela vem
do `config.js` do sharpen-bot). Se o bot gravar outro nome, a página do Nômade fica
vazia e a do Vip passa a mostrar o Nômade, e nenhum teste daqui percebe.
"""
import json
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import main  # noqa: E402

cliente = TestClient(main.app)

LINHAS = [
    {"id": 1, "tipster": "Soh Props - Vip", "resultado": "W", "lucro": 1.0},
    {"id": 2, "tipster": "Lucas", "resultado": "L", "lucro": -1.0},
    {"id": 3, "tipster": "Rafael", "resultado": "W", "lucro": 0.5},
    {"id": 4, "tipster": "Soh Props - Nômade", "resultado": "W", "lucro": 2.0},
    # o mesmo nome com o `Ô` DECOMPOSTO (O + acento combinante) e espaço sobrando
    {"id": 5, "tipster": " Soh Props - Nômade", "resultado": "L", "lucro": -0.3},
]


@pytest.fixture(autouse=True)
def _feed(monkeypatch):
    pedidos = []

    async def _rows(donos):
        pedidos.append(list(donos))
        return [dict(l) for l in LINHAS]

    monkeypatch.setattr(main, "dashboard_rows", _rows)
    main._publico_data_cache.clear()
    yield pedidos
    main._publico_data_cache.clear()


def _ids(slug):
    r = cliente.get(f"/tipsters/{slug}/data")
    assert r.status_code == 200, r.text
    j = json.loads(r.content)
    assert j["count"] == len(j["data"])
    return sorted(l["id"] for l in j["data"])


def test_a_pagina_do_nomade_mostra_so_o_nomade(_feed):
    assert _ids("sohpropsnomade") == [4, 5]
    assert _feed == [["sohprops"]], "o Nômade lê a conta dos donos, não uma conta nova"


def test_a_pagina_do_vip_nao_mostra_o_nomade_e_guarda_lucas_e_rafael():
    assert _ids("sohpropsvips") == [1, 2, 3]


def test_slug_sem_recorte_continua_mostrando_a_conta_inteira():
    assert _ids("gregotipsvip") == [1, 2, 3, 4, 5]


def test_o_cache_e_por_slug_e_um_recorte_nao_vaza_no_outro():
    """O cache guarda o feed JÁ recortado. Com a mesma conta atrás das duas páginas,
    um cache chaveado pelo dono serviria a carteira de uma na outra."""
    assert _ids("sohpropsvips") == [1, 2, 3]
    assert _ids("sohpropsnomade") == [4, 5]
    assert _ids("sohpropsvips") == [1, 2, 3]


def test_a_sidebar_dos_donos_continua_sendo_a_do_vip():
    assert main.perfil_publico_do_dono("sohprops")["slug"] == "sohpropsvips"
