"""Minha conta (s275) — trocar a senha, trocar o e-mail e revogar sessão.

O que estes testes travam:

1. **A senha ATUAL é exigida** mesmo com sessão válida. O cookie dura 30 dias;
   sessão prova "entrou um dia", não "é a pessoa agora".
2. **Trocar a senha derruba as outras sessões.** É o ponto da fatia: o cookie
   roubado morre na request seguinte. O mecanismo é a impressão do `senha_hash`
   no payload do token (`auth.impressao_senha`), comparada a cada `ler_token`.
3. **Quem troca continua dentro** — a rota reemite o cookie com a impressão
   nova. Sem isso o usuário se deslogaria ao trocar a própria senha.
4. **"Ver como" não vaza privilégio.** Operador visualizando a base do
   supervisor troca a senha DELE PRÓPRIO, nunca a do supervisor: as rotas usam
   `usuario_atual` (identidade real), não `dono_efetivo`.
5. **Token do formato antigo (sem "s") é recusado** — aceitá-lo por
   compatibilidade manteria aberto o buraco que o gate veio fechar.

Tudo sem banco: as rotas são monkeypatchadas no ponto de escrita (o stub de
`database` do conftest explodiria se fosse alcançado de verdade).
"""
import base64
import json
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import auth  # noqa: E402
import main  # noqa: E402

cliente = TestClient(main.app)

SENHA_ATUAL = "senha-atual-1"
SENHA_NOVA = "senha-nova-forte-2"


@pytest.fixture(autouse=True)
def _limpa_rate_limit():
    """O rate-limit é dict de módulo: sem isto um teste envenena o seguinte."""
    main._senha_hits.clear()
    yield
    main._senha_hits.clear()


def _hash(senha: str) -> str:
    if auth.bcrypt is None:
        pytest.skip("bcrypt não instalado neste ambiente")
    return auth.bcrypt.hashpw(senha.encode(), auth.bcrypt.gensalt()).decode()


def _com_conta(monkeypatch, username="Testador", senha=SENHA_ATUAL,
               status="ativo", parent_owner=None, email=None):
    """Põe uma conta no cache de auth (a fonte que o hot-path consulta)."""
    monkeypatch.setitem(
        auth._usuarios_cache, username,
        {"senha_hash": _hash(senha) if senha else None, "email": email,
         "status": status, "role": "user", "parent_owner": parent_owner,
         "planilha_url": None},
    )


def _grava_no_cache(monkeypatch, username):
    """Substitui a dupla (grava no banco → recarrega cache) por uma escrita
    direta no cache. Devolve a lista de hashes gravados, para inspeção."""
    gravados = []

    async def _atualizar(user, senha_hash):
        assert user == username
        gravados.append(senha_hash)
        auth._usuarios_cache[user] = {**auth._usuarios_cache[user], "senha_hash": senha_hash}
        return True

    async def _carregar():
        # A rota chama carregar_usuarios() logo após gravar; devolver o cache
        # atual mantém o efeito real (cache já contém o hash novo).
        return [{"username": u, **e} for u, e in auth._usuarios_cache.items()]

    monkeypatch.setattr(main, "atualizar_senha_usuario", _atualizar)
    monkeypatch.setattr(main, "carregar_usuarios", _carregar)
    return gravados


def _cookie(usuario):
    return {auth.COOKIE_NAME: auth.criar_token(usuario)}


def _cookie_da_resposta(r):
    """Valor do cookie de sessão devolvido pela rota.

    Vem entre aspas: o `=` do padding base64 faz o `SimpleCookie` citar o valor
    ao serializar o header. É como o /login sempre respondeu — o navegador
    desfaz a citação sozinho —, mas quem lê o header cru precisa tirá-las.
    """
    return (r.cookies.get(auth.COOKIE_NAME) or "").strip('"')


# ── A senha atual é exigida ───────────────────────────────────────────────────

def test_senha_atual_errada_da_401(monkeypatch):
    _com_conta(monkeypatch)
    _grava_no_cache(monkeypatch, "Testador")
    r = cliente.post("/conta/senha", cookies=_cookie("Testador"),
                     json={"senha_atual": "chute-errado", "senha_nova": SENHA_NOVA})
    assert r.status_code == 401


def test_sem_sessao_da_401(monkeypatch):
    _com_conta(monkeypatch)
    r = cliente.post("/conta/senha",
                     json={"senha_atual": SENHA_ATUAL, "senha_nova": SENHA_NOVA})
    assert r.status_code == 401


def test_senha_nova_curta_da_400_sem_gravar(monkeypatch):
    _com_conta(monkeypatch)
    gravados = _grava_no_cache(monkeypatch, "Testador")
    r = cliente.post("/conta/senha", cookies=_cookie("Testador"),
                     json={"senha_atual": SENHA_ATUAL, "senha_nova": "curta"})
    assert r.status_code == 400
    assert gravados == []


def test_senha_nova_igual_a_atual_da_400(monkeypatch):
    _com_conta(monkeypatch)
    gravados = _grava_no_cache(monkeypatch, "Testador")
    r = cliente.post("/conta/senha", cookies=_cookie("Testador"),
                     json={"senha_atual": SENHA_ATUAL, "senha_nova": SENHA_ATUAL})
    assert r.status_code == 400
    assert gravados == []


def test_conta_so_social_nao_troca_senha(monkeypatch):
    _com_conta(monkeypatch, username="SoSocial", senha=None)
    r = cliente.post("/conta/senha", cookies=_cookie("SoSocial"),
                     json={"senha_atual": "x" * 8, "senha_nova": SENHA_NOVA})
    # 401: sem senha local a sessão nem se forma (impressao_senha = "social",
    # e o cookie é legítimo) — mas a rota também barraria com 400. O que não
    # pode é gravar senha numa conta que não tem senha.
    assert r.status_code in (400, 401)


# ── Troca bem-sucedida: revoga as outras sessões, mantém a desta ─────────────

def test_troca_ok_grava_hash_novo_e_reemite_cookie(monkeypatch):
    _com_conta(monkeypatch)
    gravados = _grava_no_cache(monkeypatch, "Testador")
    r = cliente.post("/conta/senha", cookies=_cookie("Testador"),
                     json={"senha_atual": SENHA_ATUAL, "senha_nova": SENHA_NOVA})
    assert r.status_code == 200
    assert len(gravados) == 1
    # O hash gravado é o da senha NOVA (e não o da antiga por engano).
    assert auth.bcrypt.checkpw(SENHA_NOVA.encode(), gravados[0].encode())
    # E a resposta traz um cookie de sessão novo, válido com a senha nova.
    novo = _cookie_da_resposta(r)
    assert novo and auth.ler_token(novo) == "Testador"


def test_cookie_antigo_morre_apos_a_troca(monkeypatch):
    """O coração da fatia: sessão emitida ANTES da troca para de valer."""
    _com_conta(monkeypatch)
    _grava_no_cache(monkeypatch, "Testador")
    antigo = auth.criar_token("Testador")
    assert auth.ler_token(antigo) == "Testador"          # valia antes

    r = cliente.post("/conta/senha", cookies={auth.COOKIE_NAME: antigo},
                     json={"senha_atual": SENHA_ATUAL, "senha_nova": SENHA_NOVA})
    assert r.status_code == 200
    assert auth.ler_token(antigo) is None                # não vale depois

    # E o cookie devolvido pela própria rota continua valendo — quem trocou
    # não pode ser deslogado pela troca.
    assert auth.ler_token(_cookie_da_resposta(r)) == "Testador"


def test_token_do_formato_antigo_sem_impressao_e_recusado(monkeypatch):
    """Cookie anterior ao deploy (payload sem "s") não passa no gate."""
    _com_conta(monkeypatch)
    payload = base64.urlsafe_b64encode(
        json.dumps({"u": "Testador", "exp": 2 ** 31}).encode()
    ).decode()
    import hashlib
    import hmac
    assinatura = hmac.new(
        auth.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    assert auth.ler_token(f"{payload}.{assinatura}") is None


def test_impressao_muda_com_o_hash(monkeypatch):
    _com_conta(monkeypatch)
    antes = auth.impressao_senha("Testador")
    _com_conta(monkeypatch, senha="outra-senha-9")
    assert auth.impressao_senha("Testador") != antes
    # Conta sem senha local tem impressão constante (não quebra o cookie dela).
    _com_conta(monkeypatch, username="SoSocial", senha=None)
    assert auth.impressao_senha("SoSocial") == auth._IMPRESSAO_SEM_SENHA


# ── "Ver como" não escala privilégio ─────────────────────────────────────────

def test_operador_em_ver_como_troca_a_propria_senha(monkeypatch):
    """Operador vendo a base do supervisor troca a senha DELE, não a do chefe.

    Se a rota usasse `dono_efetivo` (como fazem as rotas de dados), este teste
    gravaria no supervisor — elevação de privilégio silenciosa.
    """
    _com_conta(monkeypatch, username="Chefe")
    _com_conta(monkeypatch, username="Operador", parent_owner="Chefe")
    alvo = []

    async def _atualizar(user, senha_hash):
        alvo.append(user)
        auth._usuarios_cache[user] = {**auth._usuarios_cache[user], "senha_hash": senha_hash}
        return True

    async def _carregar():
        return [{"username": u, **e} for u, e in auth._usuarios_cache.items()]

    monkeypatch.setattr(main, "atualizar_senha_usuario", _atualizar)
    monkeypatch.setattr(main, "carregar_usuarios", _carregar)

    # Chefe não é operador de ninguém; quem "vê como" é o dono. Montamos o par
    # do jeito que o app monta: sessão do Chefe + cookie ver-como do Operador.
    r = cliente.post(
        "/conta/senha",
        cookies={auth.COOKIE_NAME: auth.criar_token("Chefe"),
                 auth.VER_COMO_COOKIE: auth.criar_token("Operador")},
        json={"senha_atual": SENHA_ATUAL, "senha_nova": SENHA_NOVA},
    )
    assert r.status_code == 200
    assert alvo == ["Chefe"]        # a senha trocada é a de quem está logado


# ── E-mail do perfil ─────────────────────────────────────────────────────────

def test_email_invalido_da_400_sem_tocar_banco(monkeypatch):
    _com_conta(monkeypatch)
    r = cliente.post("/conta/email", cookies=_cookie("Testador"),
                     json={"email": "sem-arroba"})
    assert r.status_code == 400


def test_email_em_uso_por_outro_da_409(monkeypatch):
    _com_conta(monkeypatch)

    async def _atualizar(user, email):
        return "email"

    monkeypatch.setattr(main, "atualizar_email_usuario", _atualizar)
    r = cliente.post("/conta/email", cookies=_cookie("Testador"),
                     json={"email": "ja@existe.com"})
    assert r.status_code == 409


def test_email_ok_grava_e_volta_no_me(monkeypatch):
    _com_conta(monkeypatch)

    async def _atualizar(user, email):
        auth._usuarios_cache[user] = {**auth._usuarios_cache[user], "email": email}
        return None

    async def _carregar():
        return [{"username": u, **e} for u, e in auth._usuarios_cache.items()]

    monkeypatch.setattr(main, "atualizar_email_usuario", _atualizar)
    monkeypatch.setattr(main, "carregar_usuarios", _carregar)

    r = cliente.post("/conta/email", cookies=_cookie("Testador"),
                     json={"email": "novo@exemplo.com"})
    assert r.status_code == 200
    me = cliente.get("/me", cookies=_cookie("Testador")).json()
    assert me["email"] == "novo@exemplo.com"
    assert me["tem_senha"] is True


# ── Rate limit ───────────────────────────────────────────────────────────────

def test_rate_limit_fecha_o_brute_force_da_senha_atual(monkeypatch):
    _com_conta(monkeypatch)
    _grava_no_cache(monkeypatch, "Testador")
    for _ in range(main._SENHA_MAX):
        cliente.post("/conta/senha", cookies=_cookie("Testador"),
                     json={"senha_atual": "errada", "senha_nova": SENHA_NOVA})
    r = cliente.post("/conta/senha", cookies=_cookie("Testador"),
                     json={"senha_atual": "errada", "senha_nova": SENHA_NOVA})
    assert r.status_code == 429
