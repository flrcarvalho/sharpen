"""Cache dos documentos HTML — a casca nunca pode ficar presa no navegador.

Por que isto merece teste (incidente da s215): os assets levam `?v=` no `src`, então
bumpar a versão os renova. Mas o `?v=` mora DENTRO do HTML, e o HTML não tinha
`Cache-Control` nenhum — o navegador então escolhe sozinho por quanto tempo não
perguntar ao servidor (heurística de ~10% da idade do arquivo: horas ou dias).

O efeito é pior que "dado velho": o navegador serve a casca ANTIGA, que referencia
os assets pelas URLs antigas — e essas URLs devolvem o conteúdo NOVO. Resultado: a
tela nova aparece (veio no `app.js`) mas o arquivo novo NÃO é carregado, porque a
tag `<script>` que o chama só existe na casca nova. Foi assim que a tela "Em Aberto"
montou vazia em produção.

A regra tem dois lados, e os dois estão travados aqui:
  · HTML  → `no-cache` (guardar pode; revalidar é obrigatório — custa um 304);
  · JS/CSS → SEM `no-cache`, senão o `?v=` perderia a razão de existir.
"""
import sys

import pytest

from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import main  # noqa: E402

cliente = TestClient(main.app)


@pytest.mark.parametrize("rota", [
    "/login",
    "/dashboard/",                    # StaticFiles(html=True) — a casca do dashboard
    "/static/dash/index.html",
    "/static/app.html",
    "/static/inicio.html",
])
def test_html_sempre_revalida(rota):
    r = cliente.get(rota, follow_redirects=False)
    assert r.status_code == 200, f"{rota} não respondeu 200"
    assert r.headers.get("content-type", "").startswith("text/html")
    assert "no-cache" in r.headers.get("cache-control", ""), (
        f"{rota} sem no-cache: uma casca velha em cache deixaria de pedir os "
        f"arquivos novos que ela mesma referencia"
    )


@pytest.mark.parametrize("rota", [
    "/static/dash/assets/js/app.js",
    "/static/dash/assets/js/charts/abertas.js",
    "/static/dash/assets/css/components.css",
])
def test_asset_continua_cacheavel(rota):
    """O contrário do teste acima: asset com `no-cache` seria re-baixado a cada
    navegação e o `?v=` (que é o mecanismo de renovação) viraria enfeite."""
    r = cliente.get(rota)
    assert r.status_code == 200, f"{rota} não respondeu 200"
    assert "no-cache" not in r.headers.get("cache-control", ""), (
        f"{rota} ganhou no-cache — o cache-busting por ?v= deixa de fazer sentido"
    )
