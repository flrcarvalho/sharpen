"""Página pública de tipster (/tipsters/<slug>) — sem auth, somente leitura.

Três riscos que estes testes travam:
  1. VAZAMENTO: só slugs do registro TIPSTERS_PUBLICOS existem — qualquer outro
     valor é 404. Nenhum dono do sistema vira página pública por acidente.
  2. ORDEM DE ROTA: /tipsters/{slug} é dinâmica e registrada por ÚLTIMO. Se algum
     refactor a mover para cima, ela engole /tipsters/cadastro (API autenticada)
     — o teste de precedência reprova na hora.
  3. INJEÇÃO: o JSON entra inline num <script>; uma descrição vinda do banco com
     "</script>" não pode fechar a tag (escape `</` → `<\\/`).
"""
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import main  # noqa: E402

cliente = TestClient(main.app)

AMOSTRA = [
    {
        "id": 1, "data": "2026-07-31", "esporte": "Futebol", "tipster": "Só Chutes",
        "casa": "Bet365", "parceiro": "Padrão", "conta": "Padrão", "fornecedor": "",
        "aposta": "Múltipla", "descricao": "Jabir Ali [Ostersunds FK v Osters IF] // Christian Wagner [Sandvikens IF v GIF Sundsvall]",
        "stake": 1.0, "odd": 5.33, "resultado": "W", "lucro": 4.33, "operador": "SoChutes",
    },
    {
        "id": 2, "data": "2026-07-30", "esporte": "Futebol", "tipster": "Só Chutes",
        "casa": "Bet365", "parceiro": "Padrão", "conta": "Padrão", "fornecedor": "",
        "aposta": "Múltipla", "descricao": "descrição maliciosa </script><script>alert(1)</script>",
        "stake": 1.0, "odd": 4.5, "resultado": "L", "lucro": -1.0, "operador": "SoChutes",
    },
    {
        "id": 3, "data": "2026-07-31", "esporte": "Futebol", "tipster": "Só Chutes",
        "casa": "Bet365", "parceiro": "Padrão", "conta": "Padrão", "fornecedor": "",
        "aposta": "Anytime", "descricao": "Gustav Lindgren [BK Hacken v Kalmar FF]",
        "stake": 0.25, "odd": 10.68, "resultado": "ABERTA", "lucro": 0.0, "operador": "SoChutes",
    },
]


def _com_amostra(monkeypatch):
    chamadas = {"n": 0}

    async def fake(donos):
        assert donos == ["SoChutes"], "página pública só pode ler o dono do registro"
        chamadas["n"] += 1
        return [dict(r) for r in AMOSTRA]

    monkeypatch.setattr(main, "dashboard_rows", fake)
    main._publico_cache.clear()
    return chamadas


def test_pagina_publica_responde_sem_auth(monkeypatch):
    _com_amostra(monkeypatch)
    r = cliente.get("/tipsters/sochutes")  # nenhum cookie
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "Só Chutes" in r.text
    assert "__DADOS__" not in r.text and "__NOME__" not in r.text
    # agregação: 2 resolvidas (W 4.33, L −1.0) → profit 3.33 no JSON injetado
    assert '"profit": 3.33' in r.text
    assert '"apostas": 2' in r.text


def test_slug_fora_do_registro_e_404(monkeypatch):
    _com_amostra(monkeypatch)
    for slug in ("naoexiste", "feca", "SoChutes-outro"):
        assert cliente.get(f"/tipsters/{slug}").status_code == 404


def test_precedencia_das_rotas_de_api(monkeypatch):
    # /tipsters/cadastro é API autenticada e está registrada ANTES da dinâmica:
    # sem cookie ela responde 401 — nunca 404 (slug inexistente) nem 200 (página).
    _com_amostra(monkeypatch)
    r = cliente.get("/tipsters/cadastro")
    assert r.status_code == 401


def test_cache_de_5_min_evita_martelar_o_banco(monkeypatch):
    chamadas = _com_amostra(monkeypatch)
    cliente.get("/tipsters/sochutes")
    cliente.get("/tipsters/sochutes")
    assert chamadas["n"] == 1, "segunda visita dentro do TTL deve sair do cache em memória"
    # HTML segue a regra da casa (s215): no-cache no navegador; o servidor é que
    # segura o público com o cache em memória de 5 min testado acima.
    assert "no-cache" in cliente.get("/tipsters/sochutes").headers.get("cache-control", "")


def test_descricao_nao_fecha_o_script(monkeypatch):
    _com_amostra(monkeypatch)
    r = cliente.get("/tipsters/sochutes")
    assert "</script><script>alert(1)</script>" not in r.text
    assert "<\\/script>" in r.text
