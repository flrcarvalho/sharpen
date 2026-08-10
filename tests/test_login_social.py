"""Fase 3 do multiusuário — login social Google (OIDC) + Telegram.

O que estes testes travam:

1. FAIL-SAFE: sem env vars, /auth/metodos nega tudo e TODAS as rotas sociais
   dão 404 — o deploy dormente não abre nenhuma porta.
2. `_telegram_dados_validos` — HMAC da spec oficial (chave = SHA256(bot_token))
   + anti-replay por auth_date; payload adulterado/velho não loga.
3. `_claims_do_id_token` — iss/aud/exp/sub validados; e-mail não-verificado é
   descartado (nunca casar conta por e-mail que a Google não confirmou).
4. `derivar_username` — sanitização para a régua do `dono` + colisão com sufixo.
5. `_resolver_social` ponta a ponta via POST /auth/telegram (DB falso):
   vínculo existente ativo → cookie; pendente/suspenso → sem cookie; conta
   desconhecida → nasce pendente, NUNCA entra direto.
"""
import base64
import hashlib
import hmac
import json
import sys
import time

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import auth  # noqa: E402
import main  # noqa: E402

cliente = TestClient(main.app)

BOT_TOKEN_FALSO = "12345678:AAFakeTokenParaTestes"


def _payload_telegram(bot_token=BOT_TOKEN_FALSO, agora=None, **extras):
    dados = {"id": 987654321, "first_name": "Fulano", "auth_date": int(agora or time.time())}
    dados.update(extras)
    pares = sorted(f"{k}={v}" for k, v in dados.items())
    chave = hashlib.sha256(bot_token.encode()).digest()
    dados["hash"] = hmac.new(chave, "\n".join(pares).encode(), hashlib.sha256).hexdigest()
    return dados


def _id_token(claims):
    corpo = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return f"cabecalho.{corpo}.assinatura"


# ── Fail-safe: sem env vars, tudo dormente ────────────────────────────────────

def test_metodos_negam_tudo_sem_env():
    r = cliente.get("/auth/metodos")
    assert r.status_code == 200
    assert r.json() == {"google": False, "telegram": False}


def test_rotas_sociais_404_sem_env():
    assert cliente.get("/auth/google", follow_redirects=False).status_code == 404
    assert cliente.get("/auth/google/callback", follow_redirects=False).status_code == 404
    assert cliente.get("/auth/telegram/ir", follow_redirects=False).status_code == 404
    assert cliente.get("/auth/telegram/retorno").status_code == 404
    assert cliente.post("/auth/telegram", json={}).status_code == 404


# ── _telegram_dados_validos ───────────────────────────────────────────────────

def test_telegram_payload_valido_passa():
    assert main._telegram_dados_validos(_payload_telegram(), BOT_TOKEN_FALSO) is True


def test_telegram_hash_errado_reprova():
    dados = _payload_telegram()
    dados["hash"] = "0" * 64
    assert main._telegram_dados_validos(dados, BOT_TOKEN_FALSO) is False


def test_telegram_campo_adulterado_reprova():
    dados = _payload_telegram()
    dados["id"] = 111  # muda o id mantendo o hash antigo
    assert main._telegram_dados_validos(dados, BOT_TOKEN_FALSO) is False


def test_telegram_token_de_outro_bot_reprova():
    dados = _payload_telegram(bot_token="99999:OutroBot")
    assert main._telegram_dados_validos(dados, BOT_TOKEN_FALSO) is False


def test_telegram_payload_velho_reprova():
    dados = _payload_telegram(agora=time.time() - 3600)  # 1h atrás
    assert main._telegram_dados_validos(dados, BOT_TOKEN_FALSO) is False


def test_telegram_sem_campos_minimos_reprova():
    assert main._telegram_dados_validos({}, BOT_TOKEN_FALSO) is False
    assert main._telegram_dados_validos({"hash": "x"}, BOT_TOKEN_FALSO) is False


# ── _claims_do_id_token ───────────────────────────────────────────────────────

def _claims_ok(**extras):
    c = {
        "iss": "https://accounts.google.com", "aud": "cliente-teste",
        "sub": "sub-123", "exp": int(time.time()) + 3600,
        "email": "pessoa@gmail.com", "email_verified": True, "name": "Pessoa",
    }
    c.update(extras)
    return c


def test_id_token_valido(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "cliente-teste")
    claims = main._claims_do_id_token(_id_token(_claims_ok()))
    assert claims and claims["sub"] == "sub-123" and claims["email"] == "pessoa@gmail.com"


def test_id_token_aud_ou_iss_errados_reprovam(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "cliente-teste")
    assert main._claims_do_id_token(_id_token(_claims_ok(aud="outro-app"))) is None
    assert main._claims_do_id_token(_id_token(_claims_ok(iss="https://malicioso.com"))) is None
    assert main._claims_do_id_token(_id_token(_claims_ok(exp=int(time.time()) - 10))) is None
    assert main._claims_do_id_token("lixo-sem-pontos") is None


def test_id_token_email_nao_verificado_e_descartado(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "cliente-teste")
    claims = main._claims_do_id_token(_id_token(_claims_ok(email_verified=False)))
    assert claims is not None and claims["email"] is None  # sub vale, e-mail não


# ── derivar_username ──────────────────────────────────────────────────────────

def test_derivar_username_sanitiza_e_valida():
    assert main.derivar_username("joao.silva", set()) == "joao.silva"
    assert main.derivar_username("9joão da silva!", set()) == "joodasilva"
    assert main.derivar_username("", set()) == "usuario"
    assert main.validar_cadastro(main.derivar_username("日本語", set()), "a@b.co", "12345678") is None


def test_derivar_username_colisao_ganha_sufixo():
    em_uso = {"feca", "feca2"}
    assert main.derivar_username("Feca", em_uso) == "Feca3"


def test_derivar_username_longo_e_truncado_e_valido():
    nome = "a" * 40
    r = main.derivar_username(nome, {("a" * 24).lower()})
    assert len(r) <= 24
    assert main.validar_cadastro(r, "a@b.co", "12345678") is None


# ── POST /auth/telegram ponta a ponta (DB falso) ──────────────────────────────

@pytest.fixture
def telegram_ligado(monkeypatch):
    monkeypatch.setattr(main, "TELEGRAM_BOT_TOKEN", BOT_TOKEN_FALSO)

    async def sem_refresh():
        return []          # atualizar_cache_usuarios ignora lista vazia
    monkeypatch.setattr(main, "carregar_usuarios", sem_refresh)
    return monkeypatch


def _com_vinculo(monkeypatch, status):
    async def fake(campo, valor):
        if campo == "telegram_id" and valor == "987654321":
            return {"username": "ContaTg", "status": status, "role": "user"}
        return None
    monkeypatch.setattr(main, "buscar_usuario_social", fake)


def test_telegram_vinculado_ativo_loga_com_cookie(telegram_ligado):
    _com_vinculo(telegram_ligado, "ativo")
    r = cliente.post("/auth/telegram", json=_payload_telegram())
    assert r.status_code == 200 and r.json()["destino"] == "/app"
    assert auth.ler_token(r.cookies.get(auth.COOKIE_NAME)) is None  # 'ContaTg' não está no cache → sem sessão indevida no teste
    assert auth.COOKIE_NAME in r.cookies                            # mas o cookie foi emitido


def test_telegram_vinculado_pendente_nao_ganha_cookie(telegram_ligado):
    _com_vinculo(telegram_ligado, "pendente")
    r = cliente.post("/auth/telegram", json=_payload_telegram())
    assert r.status_code == 200 and r.json()["destino"] == "/login?social=pendente"
    assert auth.COOKIE_NAME not in r.cookies


def test_telegram_vinculado_suspenso_nao_ganha_cookie(telegram_ligado):
    _com_vinculo(telegram_ligado, "suspenso")
    r = cliente.post("/auth/telegram", json=_payload_telegram())
    assert r.status_code == 200 and r.json()["destino"] == "/login?social=suspenso"
    assert auth.COOKIE_NAME not in r.cookies


def test_telegram_desconhecido_cria_pendente_e_nao_loga(telegram_ligado):
    criados = []

    async def nada(campo, valor):
        return None

    async def em_uso():
        return {"feca"}

    async def criar(username, email, **kw):
        criados.append({"username": username, "email": email, **kw})

    telegram_ligado.setattr(main, "buscar_usuario_social", nada)
    telegram_ligado.setattr(main, "usernames_em_uso", em_uso)
    telegram_ligado.setattr(main, "criar_usuario_social", criar)
    r = cliente.post("/auth/telegram", json=_payload_telegram(username="fulano_tg"))
    assert r.status_code == 200 and r.json()["destino"] == "/login?social=pendente"
    assert auth.COOKIE_NAME not in r.cookies
    assert len(criados) == 1
    assert criados[0]["telegram_id"] == "987654321"
    assert criados[0]["username"] == "fulano_tg"    # derivado do username do Telegram


def test_telegram_hash_invalido_da_401(telegram_ligado):
    dados = _payload_telegram()
    dados["hash"] = "f" * 64
    r = cliente.post("/auth/telegram", json=dados)
    assert r.status_code == 401


# ── Página-ponte: o fragmento tem de chegar ao POST em UTF-8 ──────────────────
# O payload vem no FRAGMENTO (#tgAuthResult), que nunca chega ao servidor — quem
# o decodifica é o JS da ponte, antes do POST. `atob` devolve binary string (1
# char por BYTE): JSON.parse(atob(...)) entrega "FernÃ£o" onde foi assinado
# "Fernão", o data-check-string muda e o HMAC reprova. O usuário levaria 401 com
# sintoma IDÊNTICO ao de token errado / setdomain faltando.
#
# ⚠️ Limite honesto: não está medido se o Telegram serializa o JSON com UTF-8
# cru ou com escapes \uXXXX (sem bot no ar não dá para ver). Estes testes cobrem
# o caso RUIM — se vier escapado, o caminho UTF-8 dá exatamente o mesmo
# resultado, então o fix é correto nos dois cenários e o custo é zero.

def _ponte_navegador(dados_assinados, *, utf8=True):
    """Repete o caminho da página-ponte: JSON → base64url no fragmento → dict do
    POST. `utf8=False` reproduz o `atob` cru (o defeito), como controle."""
    fragmento = base64.urlsafe_b64encode(
        json.dumps(dados_assinados, ensure_ascii=False).encode("utf-8")
    ).decode()
    brutos = base64.b64decode(fragmento.replace("-", "+").replace("_", "/"))
    return json.loads(brutos.decode("utf-8" if utf8 else "latin-1"))


def test_ponte_telegram_serve_o_caminho_utf8():
    # Sem os comentários: o bloco EXPLICA o defeito citando `JSON.parse(atob(…))`,
    # e um guard ingênuo casaria com a prosa em vez do código.
    codigo = "\n".join(
        l for l in main._TELEGRAM_RETORNO_HTML.splitlines() if not l.strip().startswith("//")
    )
    assert "JSON.parse(new TextDecoder().decode(" in codigo   # decodifica como UTF-8
    assert "JSON.parse(atob(" not in codigo                   # nunca o caminho que mutila
    assert "A-Za-z0-9_+" in codigo                            # charset aceita base64 padrão (+/)


def test_telegram_nome_com_acento_loga(telegram_ligado):
    _com_vinculo(telegram_ligado, "ativo")
    dados = _payload_telegram(first_name="Fernão", last_name="Conceição")
    r = cliente.post("/auth/telegram", json=_ponte_navegador(dados))
    assert r.status_code == 200 and r.json()["destino"] == "/app"


def test_telegram_nome_com_emoji_loga(telegram_ligado):
    _com_vinculo(telegram_ligado, "ativo")
    dados = _payload_telegram(first_name="Ana ⚽", username="ana_bet")
    r = cliente.post("/auth/telegram", json=_ponte_navegador(dados))
    assert r.status_code == 200 and r.json()["destino"] == "/app"


def test_controle_negativo_ponte_sem_utf8_reprova(telegram_ligado):
    """Controle: pelo caminho ANTIGO (atob cru) o mesmo payload dá 401. Sem isto
    os dois testes acima passariam mesmo com o defeito de volta no JS."""
    _com_vinculo(telegram_ligado, "ativo")
    dados = _payload_telegram(first_name="Fernão", last_name="Conceição")
    r = cliente.post("/auth/telegram", json=_ponte_navegador(dados, utf8=False))
    assert r.status_code == 401


def test_ascii_passa_nos_dois_caminhos(telegram_ligado):
    """Por que o defeito passaria despercebido num teste manual: nome sem acento
    valida igual pelos dois caminhos — quem testa com 'Fernando' não vê nada."""
    _com_vinculo(telegram_ligado, "ativo")
    dados = _payload_telegram(first_name="Fernando")
    for modo in (True, False):
        r = cliente.post("/auth/telegram", json=_ponte_navegador(dados, utf8=modo))
        assert r.status_code == 200


# ── Fail-safe visual: `hidden` tem de ESCONDER de verdade ─────────────────────
# O JS marca `hidden` nos botões que o servidor não confirmou, mas `.btn-social`
# declara `display` — e declaração do autor VENCE a regra `[hidden]{display:none}`
# do navegador. Sem a regra explícita o fail-safe roda e não esconde nada: o
# botão do Google apareceu em produção assim que o Telegram acendeu, e
# `/auth/google` responde 404 sem credencial (clique = erro cru).

def _login_html():
    from pathlib import Path
    return Path("app/static/login.html").read_text(encoding="utf-8")


def test_btn_social_hidden_esconde_de_verdade():
    css = _login_html()
    assert ".btn-social[hidden]" in css, "sem a regra, `hidden` não esconde o botão social"
    trecho = css.split(".btn-social[hidden]", 1)[1].split("}", 1)[0]
    assert "display: none" in trecho or "display:none" in trecho


def test_botoes_sociais_nascem_escondidos_no_markup():
    """Fail-safe também no HTML: se o fetch de /auth/metodos falhar, nada aparece."""
    html = _login_html()
    for alvo in ('id="btn-google"', 'id="btn-telegram"'):
        tag = html.split(alvo, 1)[1].split(">", 1)[0]
        assert "hidden" in tag, f"{alvo} tem de nascer hidden no markup"


# ── Callback do Google: guards antes de qualquer rede ─────────────────────────

def test_google_callback_state_invalido_vira_erro(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "cliente-teste")
    monkeypatch.setattr(main, "GOOGLE_CLIENT_SECRET", "segredo")
    r = cliente.get("/auth/google/callback?code=abc&state=forjado", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login?social=erro"
    r = cliente.get("/auth/google/callback?error=access_denied", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login?social=erro"


def test_google_redirect_carrega_state_assinado(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "cliente-teste")
    monkeypatch.setattr(main, "GOOGLE_CLIENT_SECRET", "segredo")
    r = cliente.get("/auth/google", follow_redirects=False)
    assert r.status_code == 302
    destino = r.headers["location"]
    assert destino.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "state=" in destino and "client_id=cliente-teste" in destino
