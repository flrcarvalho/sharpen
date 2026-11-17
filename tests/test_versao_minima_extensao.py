"""Versão MÍNIMA da extensão cobrada pelo servidor (s459, auditoria EXTENSÃO A3).

O servidor anotava a versão e nunca a usava: a extensão anterior à 0.7.84 na GiroCerto não
tem o ramo da casa e manda o texto da página como bilhetes, aceito. Agora, abaixo da mínima
da casa, conectar/validar/enviar respondem 426 com o motivo. As rotas rodam de verdade.

O que NÃO está coberto: o que a extensão ANTIGA mostra ao receber o 426 (ela é anterior à
0.7.87 e mostra só o código HTTP); a dica de atualizar também aparece no painel.
"""
import pytest
from fastapi.testclient import TestClient

import main

cliente = TestClient(main.app)


@pytest.fixture
def sessao():
    s = main._captura.criar_sessao("Feca", "GiroCerto", "GIROCERTO", "conta [X]")
    main._captura.conectar(s.codigo)
    yield s
    main._captura._SESSOES.pop(s.sessao_id, None)


def test_versao_abaixo_da_minima_da_casa_e_recusada_com_motivo(sessao):
    r = cliente.post("/captura/validar", json={"token": sessao.token_ext, "versao": "0.7.83"})
    assert r.status_code == 426 and "0.7.84" in r.json()["detail"]
    r = cliente.post("/captura/enviar", data={"token": sessao.token_ext, "tipo": "texto",
                                              "texto": "x", "versao": "0.7.83"})
    assert r.status_code == 426


def test_versao_vazia_conta_como_antiga(sessao):
    r = cliente.post("/captura/validar", json={"token": sessao.token_ext, "versao": ""})
    assert r.status_code == 426


def test_versao_suficiente_passa(sessao):
    r = cliente.post("/captura/validar", json={"token": sessao.token_ext, "versao": "0.7.84"})
    assert r.status_code == 200


def test_casa_sem_minima_nao_e_afetada():
    s = main._captura.criar_sessao("Feca", "Superbet", "SUPERBET", "conta [Y]")
    main._captura.conectar(s.codigo)
    try:
        r = cliente.post("/captura/validar", json={"token": s.token_ext, "versao": "0.5.0"})
        assert r.status_code == 200
    finally:
        main._captura._SESSOES.pop(s.sessao_id, None)


def test_minima_geral_por_env(monkeypatch):
    monkeypatch.setenv("EXT_VERSAO_MINIMA", "0.9.0")
    assert main._versao_minima("SUPERBET") == "0.9.0"
    assert main._versao_minima("GIROCERTO") == "0.9.0"
