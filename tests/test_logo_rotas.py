"""Rotas da logo da conta e do perfil da sidebar (s362).

Sem banco: `logo_salvar`/`logo_ler`/`logo_apagar`/`logo_donos` e `resumo_perfil` são
monkeypatchados no ponto de escrita (o stub de `database` do conftest explodiria se
fosse alcançado de verdade). O que se prova aqui é a FRONTEIRA — o que a rota aceita,
o que recusa, e com que cabeçalhos devolve —, não a persistência.

O que NÃO está coberto: o UPSERT em `conta_logo` (precisa do Postgres do CI) e o
comportamento real do navegador diante do SVG servido.
"""
import io
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import auth  # noqa: E402
import main  # noqa: E402

cliente = TestClient(main.app)

# PNG de verdade, gerado na hora: byte a byte à mão é fácil de errar, e um PNG
# corrompido faria a rota recusar por MOTIVO CERTO e o teste falhar por motivo errado.
Image = pytest.importorskip("PIL.Image", reason="Pillow ausente neste ambiente")


def _png(largura=64, altura=64):
    buf = io.BytesIO()
    Image.new("RGBA", (largura, altura), (255, 0, 0, 255)).save(buf, "PNG")
    return buf.getvalue()


PNG = _png()


def _cookie(usuario="Testador"):
    return {auth.COOKIE_NAME: auth.criar_token(usuario)}


@pytest.fixture
def conta(monkeypatch):
    monkeypatch.setitem(
        auth._usuarios_cache, "Testador",
        {"senha_hash": "x", "email": None, "status": "ativo", "role": "user",
         "parent_owner": None, "planilha_url": None},
    )


@pytest.fixture
def grava(monkeypatch):
    """Captura o que a rota MANDARIA gravar."""
    salvos = []

    async def _salvar(dono, mime, dados):
        salvos.append({"dono": dono, "mime": mime, "bytes": dados})

    monkeypatch.setattr(main, "logo_salvar", _salvar)
    return salvos


# ── Upload ───────────────────────────────────────────────────────────────────

def test_png_valido_e_gravado_como_png_normalizado(conta, grava):
    r = cliente.post("/conta/logo", cookies=_cookie(),
                     files={"arquivo": ("logo.png", PNG, "image/png")})
    assert r.status_code == 200, r.text
    assert r.json()["tem_logo"] is True
    assert len(grava) == 1
    assert grava[0]["dono"] == "Testador"
    assert grava[0]["mime"] == "image/png"


def test_o_content_type_do_cliente_nao_decide_o_mime_gravado(conta, grava):
    """Um SVG anunciado como `image/png` continua sendo SVG. O cabeçalho do multipart
    é dado do remetente e vira o Content-Type com que servimos o arquivo de volta —
    aceitá-lo seria deixar quem envia escolher como o navegador lê os bytes."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="4" height="4"/></svg>'
    r = cliente.post("/conta/logo", cookies=_cookie(),
                     files={"arquivo": ("logo.png", svg, "image/png")})
    assert r.status_code == 200, r.text
    assert grava[0]["mime"] == "image/svg+xml"


def test_arquivo_que_nao_e_imagem_da_400_com_mensagem_em_ptbr(conta, grava):
    r = cliente.post("/conta/logo", cookies=_cookie(),
                     files={"arquivo": ("x.png", b"MZ\x90\x00" + b"\x00" * 40, "image/png")})
    assert r.status_code == 400
    assert "PNG" in r.json()["detail"]
    assert grava == []          # nada chegou ao banco


def test_arquivo_gordo_da_400_e_nao_grava(conta, grava):
    gordo = PNG + b"\x00" * (logo_limite := main.logo_imagem.LIMITE_BYTES)
    r = cliente.post("/conta/logo", cookies=_cookie(),
                     files={"arquivo": ("logo.png", gordo, "image/png")})
    assert r.status_code == 400
    assert grava == []
    assert logo_limite == 2 * 1024 * 1024


def test_upload_sem_sessao_nao_passa(grava):
    r = cliente.post("/conta/logo", files={"arquivo": ("logo.png", PNG, "image/png")})
    assert r.status_code in (401, 403)
    assert grava == []


# ── Leitura ──────────────────────────────────────────────────────────────────

def test_conta_sem_logo_da_404_para_a_tela_cair_no_monograma(conta, monkeypatch):
    async def _ler(dono):
        return None
    monkeypatch.setattr(main, "logo_ler", _ler)
    r = cliente.get("/conta/logo", cookies=_cookie())
    assert r.status_code == 404


def test_logo_servida_com_nosniff_csp_e_etag(conta, monkeypatch):
    async def _ler(dono):
        return "image/svg+xml", b"<svg/>", 'W/"123"'
    monkeypatch.setattr(main, "logo_ler", _ler)
    r = cliente.get("/conta/logo", cookies=_cookie())
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["etag"] == 'W/"123"'


def test_etag_igual_devolve_304_sem_corpo(conta, monkeypatch):
    async def _ler(dono):
        return "image/png", PNG, 'W/"abc"'
    monkeypatch.setattr(main, "logo_ler", _ler)
    r = cliente.get("/conta/logo", cookies=_cookie(), headers={"If-None-Match": 'W/"abc"'})
    assert r.status_code == 304
    assert not r.content


def test_logo_publica_so_existe_para_slug_do_registro(monkeypatch):
    """O dono NUNCA vem da URL. Sem isto, `/tipsters/<username>/logo` serviria a logo
    de qualquer conta para quem soubesse o nome de usuário."""
    async def _ler(dono):
        return "image/png", PNG, 'W/"1"'
    monkeypatch.setattr(main, "logo_ler", _ler)
    assert cliente.get("/tipsters/sohpropsvips/logo").status_code == 200
    assert cliente.get("/tipsters/Feca/logo").status_code == 404
    assert cliente.get("/tipsters/naoexiste/logo").status_code == 404


# ── Perfil ───────────────────────────────────────────────────────────────────

def test_perfil_junta_registro_publico_agregado_e_flag_da_logo(conta, monkeypatch):
    async def _resumo(donos, hoje=None):
        assert donos == ["sohprops"]        # escopo de leitura, não um dono cru
        return {"mes": {"apostas": 3, "pl": 1.0, "roi": 2.0},
                "historico": {"apostas": 9, "pl": 5.0, "roi": 4.0}}

    async def _donos(donos):
        return {"sohprops"}

    monkeypatch.setitem(
        auth._usuarios_cache, "sohprops",
        {"senha_hash": "x", "email": None, "status": "ativo", "role": "user",
         "parent_owner": None, "planilha_url": None},
    )
    monkeypatch.setattr(main, "resumo_perfil", _resumo)
    monkeypatch.setattr(main, "logo_donos", _donos)
    r = cliente.get("/conta/perfil", cookies=_cookie("sohprops"))
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["nome"] == "Soh Props" and j["plano"] == "VIP" and j["slug"] == "sohpropsvips"
    assert j["tem_logo"] is True
    assert j["mes"]["apostas"] == 3 and j["historico"]["roi"] == 4.0


def test_perfil_de_quem_nao_tem_vitrine_usa_o_username_e_fica_sem_plano(conta, monkeypatch):
    async def _resumo(donos, hoje=None):
        return {"mes": {"apostas": 0}, "historico": {"apostas": 0}}

    async def _donos(donos):
        return set()

    monkeypatch.setattr(main, "resumo_perfil", _resumo)
    monkeypatch.setattr(main, "logo_donos", _donos)
    j = cliente.get("/conta/perfil", cookies=_cookie()).json()
    assert j["nome"] == "Testador"
    assert j["plano"] is None       # a tela mostra o badge "Tester", nunca um selo vazio
    assert j["tem_logo"] is False
