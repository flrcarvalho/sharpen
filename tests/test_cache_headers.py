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


def test_rota_que_pede_no_store_nao_e_rebaixada():
    """s459 (auditoria NAVEGADOR M2): o `/login` declara `no-store`, e o middleware o
    sobrescrevia por `no-cache` — a página voltava inteira da memória pelo Voltar."""
    r = cliente.get("/login")
    assert "no-store" in r.headers.get("cache-control", ""), r.headers.get("cache-control")


def test_json_de_api_nunca_e_guardado():
    """s459 (auditoria SERVIDOR P8): resposta JSON sem `Cache-Control` podia ser guardada
    por um proxy/CDN no caminho. Uma rota JSON qualquer, aqui a que recusa sem sessão."""
    r = cliente.get("/me")
    assert r.headers.get("content-type", "").startswith("application/json")
    assert "no-store" in r.headers.get("cache-control", ""), r.headers.get("cache-control")


# ── s459 (auditoria de 17/11, NAVEGADOR C2): versão do asset pelo CONTEÚDO ─────────────
# Até a s458 o lado "asset" desta regra era "sem no-cache, porque o ?v= manual renova". O
# ?v= manual foi esquecido em 20 % das mudanças, e sem `Cache-Control` o navegador nem
# pedia o arquivo de novo (F5 não resolvia). Agora o servidor escreve o ?v= (hash do
# conteúdo) em todo HTML; com o hash certo o asset é `immutable`, com qualquer outro ele
# revalida. Ver `app/ativos.py`.
import re  # noqa: E402

import ativos  # noqa: E402

ASSET = "/dashboard/assets/js/app.js"


def test_html_servido_aponta_para_o_hash_do_conteudo():
    html = cliente.get("/dashboard/").text
    h = ativos.hash_da_url(ASSET)
    assert h and f'assets/js/app.js?v={h}"' in html


def test_nenhum_asset_local_sai_com_versao_que_nao_e_o_hash():
    for rota in ("/dashboard/", "/static/app.html", "/login", "/static/index.html"):
        html = cliente.get(rota).text
        for ref, v in re.findall(r'(?:src|href)="([^"]+\.(?:js|css))\?v=([^"]+)"', html):
            if ref.startswith(("http", "//")):
                continue
            url = ref if ref.startswith("/") else "/dashboard/" + ref
            assert v == ativos.hash_da_url(url), f"{rota}: {ref}?v={v} não é o hash do conteúdo"


def test_asset_com_hash_certo_e_imutavel_e_o_resto_revalida():
    h = ativos.hash_da_url(ASSET)
    certo = cliente.get(f"{ASSET}?v={h}").headers.get("cache-control", "")
    assert "immutable" in certo and "max-age=31536000" in certo
    for q in ("", "?v=70", "?v=velho"):
        cc = cliente.get(ASSET + q).headers.get("cache-control", "")
        assert cc == "no-cache", f"{ASSET}{q} -> {cc!r}: sem o hash certo, tem de revalidar"


def test_etag_da_pagina_muda_quando_um_asset_muda(monkeypatch):
    r1 = cliente.get("/dashboard/")
    etag = r1.headers.get("etag")
    assert etag
    assert cliente.get("/dashboard/", headers={"If-None-Match": etag}).status_code == 304
    real = ativos.hash_da_url
    monkeypatch.setattr(ativos, "hash_da_url", lambda u: "outro" + (real(u) or ""))
    r3 = cliente.get("/dashboard/", headers={"If-None-Match": etag})
    assert r3.status_code == 200, "asset novo com a página igual tem de devolver a página nova"
    assert r3.headers.get("etag") != etag


def test_casca_nasce_carimbada_com_a_identidade_do_codigo():
    """3.1: a casca compara o carimbo com `/versao` para saber que saiu código novo."""
    html = cliente.get("/static/app.html").text
    assert "__SHARPEN_BUILD__" not in html
    assert f"var buildCarregado = '{ativos.build_id()}'" in html


def test_versao_do_codigo_e_header_de_build():
    r = cliente.get("/versao")
    assert r.json()["build"] == ativos.build_id()
    assert cliente.get("/healthz").headers.get("x-sharpen-build") == ativos.build_id()
