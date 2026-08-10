"""Fase 2 do multiusuário — cadastro self-service + painel de aprovação.

O que estes testes travam (tudo SEM banco — validação e gates rodam antes
de qualquer query; o DB stub do conftest explodiria se fossem alcançados):

1. `validar_cadastro` — o username vira a coluna `dono` verbatim no sistema
   inteiro; formato frouxo aqui = conta com espaço/acento envenenando dedup,
   grafia e assinaturas para sempre.
2. `resultado_login` — pendente/suspenso só são revelados com a SENHA CERTA
   (sem enumeração de contas); senha errada é sempre 'invalido'.
3. Gates das rotas: /signup valida antes do DB; /admin/* exige sessão (401)
   e papel admin (403); a página /admin redireciona em vez de vazar.
"""
import asyncio
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import auth  # noqa: E402
import main  # noqa: E402

cliente = TestClient(main.app)


# ── validar_cadastro (pura) ───────────────────────────────────────────────────

def test_cadastro_valido_passa():
    assert main.validar_cadastro("NovoUsuario", "novo@exemplo.com", "senha-forte-1") is None
    assert main.validar_cadastro("Ana.B-2_c", "a@b.co", "12345678") is None


@pytest.mark.parametrize("usuario", [
    "ab",                    # curto demais
    "a" * 25,                # longo demais
    "1comeca-com-numero",
    "_comeca-com-underscore",
    "com espaco",
    "acentuadoJosé",
    "",                      # vazio
])
def test_cadastro_usuario_invalido(usuario):
    assert main.validar_cadastro(usuario, "ok@exemplo.com", "12345678") is not None


@pytest.mark.parametrize("email", ["semarroba", "a@b", "a b@c.d", "@x.com", "a@@b.com", ""])
def test_cadastro_email_invalido(email):
    assert main.validar_cadastro("UsuarioOk", email, "12345678") is not None


def test_cadastro_senha_curta_ou_gigante():
    assert main.validar_cadastro("UsuarioOk", "a@b.co", "1234567") is not None
    assert main.validar_cadastro("UsuarioOk", "a@b.co", "x" * 129) is not None


# ── resultado_login: status só com senha certa ────────────────────────────────

def _com_usuario(monkeypatch, username, status):
    if auth.bcrypt is None:
        pytest.skip("bcrypt não instalado neste ambiente")
    h = auth.bcrypt.hashpw(b"senha-certa", auth.bcrypt.gensalt()).decode()
    monkeypatch.setitem(
        auth._usuarios_cache, username,
        {"senha_hash": h, "status": status, "role": "user",
         "parent_owner": None, "planilha_url": None},
    )


def test_resultado_login_ok_pendente_suspenso(monkeypatch):
    for status, esperado in (("ativo", "ok"), ("pendente", "pendente"), ("suspenso", "suspenso")):
        _com_usuario(monkeypatch, "TesteStatus", status)
        assert auth.resultado_login("TesteStatus", "senha-certa") == esperado


def test_resultado_login_senha_errada_nunca_revela_status(monkeypatch):
    # A resposta para senha errada é IDÊNTICA para conta pendente, suspensa e
    # inexistente — quem não tem a senha não descobre nem que a conta existe.
    for status in ("ativo", "pendente", "suspenso"):
        _com_usuario(monkeypatch, "TesteStatus", status)
        assert auth.resultado_login("TesteStatus", "senha-errada") == "invalido"
    assert auth.resultado_login("NaoExiste", "qualquer") == "invalido"


# ── /signup: validação roda antes do banco ────────────────────────────────────

def test_signup_usuario_invalido_da_400_sem_tocar_banco():
    r = cliente.post("/signup", json={"usuario": "a b", "email": "x@y.co", "senha": "12345678"})
    assert r.status_code == 400
    assert "Usuário inválido" in r.json()["detail"]


def test_signup_senha_curta_da_400():
    r = cliente.post("/signup", json={"usuario": "UsuarioOk", "email": "x@y.co", "senha": "curta"})
    assert r.status_code == 400


# ── Aviso ao admin: o cadastro deixou de ser mudo ─────────────────────────────
# A conta pendente ficava só no /admin, e nada avisava ninguém: um cadastro
# esperou 2 dias e três de um mesmo dia só foram vistos porque alguém perguntou.
# O que estes testes travam: o fail-safe (sem env var, nada acontece), o payload,
# e — o mais importante — que o aviso NUNCA vira um jeito novo de o cadastro
# falhar. Ele é efeito colateral; a ação do usuário tem precedência sempre.

@pytest.fixture
def alerta_ligado(monkeypatch):
    monkeypatch.setattr(main, "TELEGRAM_ALERTA_TOKEN", "111:AAtokenDeAviso")
    monkeypatch.setattr(main, "TELEGRAM_ALERTA_CHAT_ID", "42")
    return monkeypatch


class _RespFake:
    def raise_for_status(self):
        pass


def _cliente_fake(capturado):
    class Cli:
        def __init__(self, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None):
            capturado["url"], capturado["json"] = url, json
            return _RespFake()
    return Cli


def test_alerta_desligado_sem_env():
    assert main._alerta_configurado() is False


def test_alerta_desligado_e_no_op():
    # Sem env var não pode nem tentar agendar (não há loop rodando aqui: se
    # `disparar_aviso` chamasse create_task, este teste explodiria).
    assert main.disparar_aviso("qualquer coisa") is None


def test_alerta_exige_token_e_chat(monkeypatch):
    monkeypatch.setattr(main, "TELEGRAM_ALERTA_TOKEN", "111:AAtoken")
    monkeypatch.setattr(main, "TELEGRAM_ALERTA_CHAT_ID", "")
    assert main._alerta_configurado() is False        # token sem destino não serve
    monkeypatch.setattr(main, "TELEGRAM_ALERTA_CHAT_ID", "42")
    monkeypatch.setattr(main, "TELEGRAM_ALERTA_TOKEN", "sem-dois-pontos")
    assert main._alerta_configurado() is False        # token malformado


def test_avisar_admin_envia_payload_certo(alerta_ligado):
    capturado = {}
    alerta_ligado.setattr(main.httpx, "AsyncClient", _cliente_fake(capturado))
    assert asyncio.run(main.avisar_admin("oi")) is True
    assert capturado["url"].endswith("/bot111:AAtokenDeAviso/sendMessage")
    assert capturado["json"]["chat_id"] == "42"
    assert capturado["json"]["text"] == "oi"


def test_avisar_admin_engole_falha_do_telegram(alerta_ligado):
    class Explode:
        def __init__(self, **k):
            pass

        async def __aenter__(self):
            raise RuntimeError("telegram fora do ar")

        async def __aexit__(self, *a):
            return False

    alerta_ligado.setattr(main.httpx, "AsyncClient", Explode)
    assert asyncio.run(main.avisar_admin("oi")) is False   # devolve, não levanta


def test_disparar_aviso_engole_falha_de_agendamento(alerta_ligado):
    """Guard do AGENDAMENTO: sem ele, o aviso derrubaria o /signup que o chamou."""
    def create_task_quebrado(_):
        raise RuntimeError("sem event loop")

    alerta_ligado.setattr(main.asyncio, "create_task", create_task_quebrado)
    assert main.disparar_aviso("oi") is None              # não propaga


def test_texto_do_aviso_tem_o_essencial():
    t = main._texto_cadastro_novo("Fulano", "f@x.com", "formulário de senha")
    for pedaco in ("Fulano", "f@x.com", "/admin", "formulário de senha"):
        assert pedaco in t
    # Login pelo Telegram NÃO fornece e-mail — o aviso não pode quebrar nem
    # sair com "None" no lugar do endereço.
    sem_email = main._texto_cadastro_novo("Fulano", None, "Telegram")
    assert "None" not in sem_email and "—" in sem_email


# ── /login: mensagens de pendente/suspenso ────────────────────────────────────

def test_login_pendente_recebe_mensagem_de_analise(monkeypatch):
    _com_usuario(monkeypatch, "AguardandoOk", "pendente")
    r = cliente.post("/login", json={"usuario": "AguardandoOk", "senha": "senha-certa"})
    assert r.status_code == 403
    assert "análise" in r.json()["detail"]
    # e NÃO ganhou cookie de sessão
    assert auth.COOKIE_NAME not in r.cookies


def test_login_suspenso_recebe_mensagem_de_suspensao(monkeypatch):
    _com_usuario(monkeypatch, "Suspenso1", "suspenso")
    r = cliente.post("/login", json={"usuario": "Suspenso1", "senha": "senha-certa"})
    assert r.status_code == 403
    assert "suspensa" in r.json()["detail"].lower()


# ── Gates do /admin ───────────────────────────────────────────────────────────

def _cookie(usuario):
    return {auth.COOKIE_NAME: auth.criar_token(usuario)}


def test_admin_api_sem_sessao_401():
    assert cliente.get("/admin/usuarios").status_code == 401
    assert cliente.post("/admin/usuarios/X/aprovar").status_code == 401


def test_admin_api_nao_admin_403():
    r = cliente.get("/admin/usuarios", cookies=_cookie("Jonathan"))
    assert r.status_code == 403
    r = cliente.post("/admin/usuarios/X/aprovar", cookies=_cookie("Jonathan"))
    assert r.status_code == 403
    r = cliente.post("/admin/usuarios/X/suspender", cookies=_cookie("Jonathan"))
    assert r.status_code == 403


def test_admin_nao_suspende_a_si_mesmo():
    # Feca é admin na semente; o guard roda ANTES do DB (senão o stub explode).
    r = cliente.post("/admin/usuarios/Feca/suspender", cookies=_cookie("Feca"))
    assert r.status_code == 400


def test_admin_page_redireciona_sem_vazar():
    r = cliente.get("/admin", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    r = cliente.get("/admin", cookies=_cookie("Jonathan"), follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/app"


def test_admin_page_para_admin_serve_html():
    r = cliente.get("/admin", cookies=_cookie("Feca"), follow_redirects=False)
    assert r.status_code == 200
    assert "Admin · Usuários" in r.text
