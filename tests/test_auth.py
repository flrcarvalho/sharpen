"""Autenticação e isolamento multi-tenant — a fronteira entre inquilinos.

`auth.py` é 100% função pura (sem banco) e guarda QUEM vê/opera a base de QUEM.
Um bug aqui = um dono alcançar dados de outro, ou um cookie forjado escalar
privilégio. Estes testes travam:

- round-trip do token HMAC + rejeição de token adulterado/de-outro-segredo/expirado
  /de-usuário-fantasma;
- a matriz `pode_ver_como` (dono vê próprio operador; operador não vê ninguém;
  dono não vê outro dono);
- `dono_efetivo` — o cookie "ver como" forjado/não-autorizado SEMPRE cai no usuário
  real, nunca escala privilégio;
- `coproprietarios` (simetria da linhagem, usada na dedup cruzada) e `operadores_de`;
- o guard fail-closed do `SESSION_SECRET` em produção (regressão via subprocess).
"""
import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time

import pytest
from fastapi import HTTPException

import auth  # conftest põe app/ no sys.path


class _FakeRequest:
    """Stub mínimo: usuario_do_request/dono_efetivo só leem request.cookies.get(nome)."""

    def __init__(self, **cookies):
        self.cookies = dict(cookies)


def _token_assinado(usuario: str, exp: int, segredo: str | bytes) -> str:
    """Monta um token no formato de auth (payload.assinatura) com um segredo qualquer."""
    payload = base64.urlsafe_b64encode(
        json.dumps({"u": usuario, "exp": exp}).encode()
    ).decode()
    chave = segredo.encode() if isinstance(segredo, str) else segredo
    sig = hmac.new(chave, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


# ── Token: round-trip, HMAC, expiração, usuário fora de USUARIOS ──────────────

def test_token_roundtrip_valido():
    assert auth.ler_token(auth.criar_token("Feca")) == "Feca"


def test_token_none_ou_lixo():
    assert auth.ler_token(None) is None
    assert auth.ler_token("") is None
    assert auth.ler_token("sem-ponto-nenhum") is None


def test_token_hmac_adulterado_rejeitado():
    tok = auth.criar_token("Feca")
    payload, _sig = tok.rsplit(".", 1)
    assert auth.ler_token(payload + "." + ("0" * 64)) is None       # assinatura falsa
    # trocar o payload mantendo a assinatura antiga também não passa
    outro = base64.urlsafe_b64encode(
        json.dumps({"u": "Feca", "exp": int(time.time()) + 999}).encode()
    ).decode()
    assert auth.ler_token(outro + "." + _sig) is None


def test_token_assinado_com_outro_segredo_rejeitado():
    # Cookie forjado por quem NÃO tem o SESSION_SECRET não passa.
    tok = _token_assinado("Feca", int(time.time()) + 3600, "segredo-do-atacante")
    assert auth.ler_token(tok) is None


def test_token_expirado_rejeitado():
    tok = _token_assinado("Feca", int(time.time()) - 1, auth.SESSION_SECRET)
    assert auth.ler_token(tok) is None


def test_token_usuario_fantasma_rejeitado():
    # Bem-assinado, mas de usuário que não existe em USUARIOS → None.
    tok = _token_assinado("Hacker", int(time.time()) + 3600, auth.SESSION_SECRET)
    assert auth.ler_token(tok) is None


# ── pode_ver_como: matriz de privilégio ──────────────────────────────────────

def test_pode_ver_como_dono_ve_proprio_operador():
    assert auth.pode_ver_como("Feca", "Lava") is True
    assert auth.pode_ver_como("Diogo", "Primo") is True
    assert auth.pode_ver_como("Fatuch", "LavaFatuch") is True


def test_pode_ver_como_a_si_mesmo():
    assert auth.pode_ver_como("Feca", "Feca") is True
    assert auth.pode_ver_como("Lava", "Lava") is True


def test_pode_ver_como_dono_nao_ve_outro_dono():
    assert auth.pode_ver_como("Feca", "Diogo") is False
    assert auth.pode_ver_como("Diogo", "Feca") is False


def test_pode_ver_como_operador_nao_ve_ninguem_alem_de_si():
    assert auth.pode_ver_como("Lava", "Feca") is False       # operador não sobe pro dono
    assert auth.pode_ver_como("Primo", "Diogo") is False
    assert auth.pode_ver_como("Lava", "Primo") is False      # nem operador de outro dono


# ── operadores_de / coproprietarios ──────────────────────────────────────────

def test_operadores_de():
    assert auth.operadores_de("Feca") == ["Lava"]
    assert auth.operadores_de("Diogo") == ["Primo"]
    assert auth.operadores_de("Lava") == []                  # operador não tem operadores
    assert auth.operadores_de("Jonathan") == []              # dono solo


def test_coproprietarios_simetrico_na_linhagem():
    assert auth.coproprietarios("Lava") == ["Feca"]
    assert auth.coproprietarios("Feca") == ["Lava"]
    assert auth.coproprietarios("Diogo") == ["Primo"]
    assert auth.coproprietarios("Primo") == ["Diogo"]


def test_coproprietarios_dono_solo_ou_inexistente_vazio():
    assert auth.coproprietarios("Jonathan") == []            # solo → sem checagem cruzada
    assert auth.coproprietarios("WilliamOliveira") == []     # solo (s218)
    assert auth.coproprietarios("Naoexiste") == []


def test_lavapessoal_e_dono_solo_isolado_do_feca():
    # Nome parecido com `Lava` (operador do Feca), natureza OPOSTA: LavaPessoal é
    # DONO SOLO. Base pessoal isolada — o Feca não a alcança nem por "ver como"
    # nem pela dedup cruzada. Trava a decisão de criação da conta (s216).
    assert "LavaPessoal" in auth.USUARIOS
    assert auth.operadores_de("LavaPessoal") == []
    assert auth.coproprietarios("LavaPessoal") == []
    assert auth.pode_ver_como("Feca", "LavaPessoal") is False
    assert auth.pode_ver_como("LavaPessoal", "Feca") is False
    assert auth.pode_ver_como("LavaPessoal", "Lava") is False
    assert auth.pode_ver_como("LavaPessoal", "LavaPessoal") is True


# ── dono_efetivo: o coração do isolamento em modo "ver como" ──────────────────

def test_dono_efetivo_sem_ver_como_retorna_proprio():
    req = _FakeRequest(**{auth.COOKIE_NAME: auth.criar_token("Feca")})
    assert auth.dono_efetivo(req) == "Feca"


def test_dono_efetivo_ver_como_autorizado_retorna_alvo():
    req = _FakeRequest(**{
        auth.COOKIE_NAME: auth.criar_token("Feca"),
        auth.VER_COMO_COOKIE: auth.criar_token("Lava"),      # Feca PODE ver Lava
    })
    assert auth.dono_efetivo(req) == "Lava"


def test_dono_efetivo_ver_como_nao_autorizado_cai_no_real():
    # Feca tenta "ver como" Diogo (outro dono) — não autorizado → volta pra Feca.
    req = _FakeRequest(**{
        auth.COOKIE_NAME: auth.criar_token("Feca"),
        auth.VER_COMO_COOKIE: auth.criar_token("Diogo"),
    })
    assert auth.dono_efetivo(req) == "Feca"


def test_dono_efetivo_ver_como_forjado_cai_no_real():
    # Cookie "ver como" assinado com outro segredo → ler_token=None → usuário real.
    forjado = _token_assinado("Lava", int(time.time()) + 3600, "atacante")
    req = _FakeRequest(**{
        auth.COOKIE_NAME: auth.criar_token("Feca"),
        auth.VER_COMO_COOKIE: forjado,
    })
    assert auth.dono_efetivo(req) == "Feca"


def test_dono_efetivo_operador_nao_escala_para_o_dono():
    # Lava (operador) com cookie ver-como VÁLIDO apontando pro Feca → NÃO vira Feca,
    # porque pode_ver_como("Lava","Feca") é False (reavaliado contra a sessão real).
    req = _FakeRequest(**{
        auth.COOKIE_NAME: auth.criar_token("Lava"),
        auth.VER_COMO_COOKIE: auth.criar_token("Feca"),
    })
    assert auth.dono_efetivo(req) == "Lava"


def test_dono_efetivo_sem_sessao_levanta_401():
    with pytest.raises(HTTPException) as ei:
        auth.dono_efetivo(_FakeRequest())
    assert ei.value.status_code == 401


# ── usuario_atual ────────────────────────────────────────────────────────────

def test_usuario_atual_valido():
    req = _FakeRequest(**{auth.COOKIE_NAME: auth.criar_token("Jonathan")})
    assert auth.usuario_atual(req) == "Jonathan"


def test_usuario_atual_sem_sessao_levanta_401():
    with pytest.raises(HTTPException) as ei:
        auth.usuario_atual(_FakeRequest())
    assert ei.value.status_code == 401


# ── verificar_credenciais / _verifica_hash ───────────────────────────────────

def test_verifica_hash_vazio_ou_ausente_e_false():
    # Hash vazio (env de senha faltando) → False, fail-closed. Nunca "senha vazia passa".
    assert auth._verifica_hash("qualquer", "") is False
    assert auth.verificar_credenciais("Feca", "qualquer") is False  # USUARIOS[Feca]="" nos testes


def test_verifica_hash_bcrypt_confere():
    if auth.bcrypt is None:
        pytest.skip("bcrypt não instalado neste ambiente")
    h = auth.bcrypt.hashpw(b"minhasenha", auth.bcrypt.gensalt()).decode()
    assert auth._verifica_hash("minhasenha", h) is True
    assert auth._verifica_hash("errada", h) is False


# ── planilha_ao_vivo (fail-safe: sem env → cai no Postgres) ───────────────────

def test_planilha_ao_vivo_padrao_vazio():
    assert auth.planilha_ao_vivo("Feca") == ""
    assert auth.planilha_ao_vivo("Jonathan") == ""
    assert auth.planilha_ao_vivo("LavaFatuch") == ""   # env PLANILHA_LAVAFATUCH_URL vazia nos testes


# ── SESSION_SECRET fail-closed em produção (guard de boot) ────────────────────
# Roda num subprocesso porque a decisão acontece no IMPORT de auth.

def _import_auth_com_env(**overrides):
    app_dir = os.path.dirname(auth.__file__)
    env = {k: v for k, v in os.environ.items() if k != "SESSION_SECRET"}
    env.pop("RAILWAY_PROJECT_ID", None)  # garante que só o override decide "produção"
    env["PYTHONPATH"] = app_dir + os.pathsep + env.get("PYTHONPATH", "")
    env.update(overrides)
    return subprocess.run(
        [sys.executable, "-c", "import auth"], env=env, capture_output=True, text=True
    )


def test_session_secret_fail_closed_em_producao_sem_segredo():
    r = _import_auth_com_env(RAILWAY_ENVIRONMENT="production")
    assert r.returncode != 0                       # o app NÃO sobe
    assert "SESSION_SECRET" in r.stderr            # falha explícita, não silenciosa


def test_session_secret_ok_em_producao_com_segredo():
    r = _import_auth_com_env(RAILWAY_ENVIRONMENT="production", SESSION_SECRET="x" * 64)
    assert r.returncode == 0                       # com segredo, sobe normal


def test_session_secret_dev_sem_segredo_nao_trava():
    r = _import_auth_com_env()                     # sem RAILWAY_* → é dev
    assert r.returncode == 0                       # fallback efêmero, não derruba o local
