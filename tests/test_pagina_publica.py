"""Vitrine pública de tipster (/tipsters/<slug>) — o Betting Dashboard em modo
público, sem auth, somente leitura (s226).

O que estes testes travam:
  1. VAZAMENTO: só slugs do registro TIPSTERS_PUBLICOS existem — qualquer outro
     valor é 404, nas DUAS rotas (casca e feed). Nenhum dono vira público por
     acidente.
  2. ORDEM DE ROTA: as rotas dinâmicas são registradas por ÚLTIMO. Se um refactor
     as mover para cima, engolem /tipsters/cadastro (API autenticada) — o teste
     de precedência reprova na hora.
  3. INJEÇÃO: a casca só recebe valores do REGISTRO (slug/nome) — nunca dado do
     banco; o feed é JSON puro. A flag precisa vir ANTES do script de guarda
     (senão o navegador redireciona para /app e a vitrine nunca abre).
  4. CACHE: o feed público é cacheado 5 min em memória — visitante anônimo não
     martela o Postgres nem fura o cache com ?refresh=1.
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
        "aposta": "Múltipla", "descricao": "Jabir Ali [Ostersunds FK v Osters IF]",
        "stake": 1.0, "odd": 5.33, "resultado": "W", "lucro": 4.33, "operador": "SoChutes",
    },
    {
        "id": 2, "data": "2026-07-31", "esporte": "Futebol", "tipster": "Só Chutes",
        "casa": "Bet365", "parceiro": "Padrão", "conta": "Padrão", "fornecedor": "",
        "aposta": "Múltipla", "descricao": "Tripla", "stake": 0.25, "odd": 10.68,
        "resultado": "ABERTA", "lucro": 0.0, "operador": "SoChutes",
    },
]


def _com_amostra(monkeypatch):
    chamadas = {"n": 0}

    async def fake(donos):
        assert donos == ["SoChutes"], "feed público só pode ler o dono do registro"
        chamadas["n"] += 1
        return [dict(r) for r in AMOSTRA]

    monkeypatch.setattr(main, "dashboard_rows", fake)
    main._publico_data_cache.clear()
    return chamadas


# ── Casca (shell do dashboard com MODO_PUBLICO injetado) ──────────────────────

def test_casca_responde_sem_auth_e_injeta_flag():
    r = cliente.get("/tipsters/sochutes")  # nenhum cookie
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert '"slug": "sochutes"' in r.text
    assert '"nome": "Só Chutes"' in r.text
    assert '<base href="/dashboard/">' in r.text
    # a flag PRECISA vir antes do script de guarda, senão o redirect ganha
    assert r.text.index("window.MODO_PUBLICO") < r.text.index("location.replace")


def test_casca_e_o_shell_do_dashboard():
    r = cliente.get("/tipsters/sochutes")
    # é o shell real do dash (mesmos assets versionados), não uma página paralela
    assert "assets/js/app.js" in r.text
    assert "assets/js/charts/performance.js" in r.text


# ── Feed público (/tipsters/<slug>/data) ─────────────────────────────────────

def test_feed_mesmo_contrato_do_dashboard_data(monkeypatch):
    _com_amostra(monkeypatch)
    r = cliente.get("/tipsters/sochutes/data")
    assert r.status_code == 200
    body = r.json()  # httpx descomprime o gzip transparentemente
    assert body["ok"] is True
    assert body["count"] == 2
    assert body["dono"] == "SoChutes"
    assert body["operadores"] == ["SoChutes"]
    assert body["data"][0]["lucro"] == 4.33


def test_cache_de_5_min_e_refresh_ignorado(monkeypatch):
    chamadas = _com_amostra(monkeypatch)
    cliente.get("/tipsters/sochutes/data")
    cliente.get("/tipsters/sochutes/data")
    cliente.get("/tipsters/sochutes/data?refresh=1")  # botão "Atualizar dados"
    assert chamadas["n"] == 1, "anônimo não fura o cache — nem com ?refresh=1"


# ── Registro e precedência ───────────────────────────────────────────────────

def test_slug_fora_do_registro_e_404(monkeypatch):
    _com_amostra(monkeypatch)
    for rota in ("/tipsters/naoexiste", "/tipsters/feca", "/tipsters/naoexiste/data"):
        assert cliente.get(rota).status_code == 404, rota


def test_precedencia_das_rotas_de_api(monkeypatch):
    # /tipsters/cadastro e /tipsters/unidades são API autenticada, registradas
    # ANTES das dinâmicas: sem cookie respondem 401 — nunca 404 nem 200 público.
    _com_amostra(monkeypatch)
    assert cliente.get("/tipsters/cadastro").status_code == 401
    assert cliente.get("/tipsters/unidades?tipster=x").status_code == 401
