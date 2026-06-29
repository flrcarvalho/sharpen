"""Autenticação multiusuário — login por cookie assinado (HMAC, stdlib).

Isolamento lógico: cada rota recupera o `dono` (username) do cookie de sessão
e o repassa ao repositório, que filtra TODA query por dono. Sem cookie válido,
nenhuma rota de dados responde.

Sem dependências novas — apenas stdlib. As senhas ficam em hash SHA-256;
podem ser sobrescritas por variável de ambiente em produção.
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time

from fastapi import HTTPException, Request

try:
    import bcrypt
except ImportError:          # defensivo: se a lib faltar, o caminho legado ainda funciona
    bcrypt = None

logger = logging.getLogger("auth")

COOKIE_NAME = "fdc_sessao"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 dias

# Segredo de assinatura do cookie.
# Em produção, defina SESSION_SECRET no Railway (persiste sessões entre reinícios).
# Se ausente, gera um segredo ALEATÓRIO no boot: ninguém consegue forjar cookies
# (não há mais default conhecido), ao custo de as sessões caírem a cada reinício.
# Nunca derruba o app — falha-fechado seguro em vez de falha-aberto.
SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
if not os.environ.get("SESSION_SECRET"):
    logger.warning(
        "SESSION_SECRET não definido — usando segredo efêmero aleatório. "
        "Sessões cairão a cada reinício do servidor. "
        "Defina SESSION_SECRET no Railway para persistir os logins."
    )


# usuário → hash da senha. Sobrescrevível por env (SENHA_<USER>_HASH) sem expor texto.
# Aceita bcrypt (novo, com salt — hash começa com "$2") OU SHA-256 hex (legado).
# Os defaults SHA-256 abaixo são de TRANSIÇÃO: assim que os hashes bcrypt forem
# definidos nas env vars do Railway, removê-los daqui (ver STATUS "Hash de senha").
USUARIOS: dict[str, str] = {
    "Feca": os.environ.get(
        "SENHA_FECA_HASH",
        "21a9201f1f1554b9647d573514007b0dd03870abf0c8e014d12dc961213dec31",
    ),
    "Diogo": os.environ.get(
        "SENHA_DIOGO_HASH",
        "4b7c2caf9b963b6530e3ff5245c84122fde9bb017a04e925b0516ed4c3e26266",
    ),
}


def _verifica_hash(senha: str, hash_guardado: str) -> bool:
    """Compara a senha com o hash, detectando o formato automaticamente."""
    if not hash_guardado:
        return False
    if hash_guardado.startswith("$2"):          # bcrypt (com salt + stretching)
        if bcrypt is None:
            return False
        try:
            return bcrypt.checkpw(senha.encode(), hash_guardado.encode())
        except (ValueError, TypeError):
            return False
    # legado: SHA-256 hex, sem salt (comparação em tempo constante)
    return hmac.compare_digest(hash_guardado, hashlib.sha256(senha.encode()).hexdigest())


def verificar_credenciais(usuario: str, senha: str) -> bool:
    return _verifica_hash(senha, USUARIOS.get(usuario) or "")


def criar_token(usuario: str) -> str:
    exp = int(time.time()) + SESSION_MAX_AGE
    payload = base64.urlsafe_b64encode(
        json.dumps({"u": usuario, "exp": exp}).encode()
    ).decode()
    assinatura = hmac.new(
        SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{assinatura}"


def ler_token(token: str | None) -> str | None:
    """Retorna o usuário se o token for válido e não expirado; senão None."""
    if not token:
        return None
    try:
        payload, assinatura = token.rsplit(".", 1)
        esperado = hmac.new(
            SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(assinatura, esperado):
            return None
        dados = json.loads(base64.urlsafe_b64decode(payload.encode()))
        if int(dados.get("exp", 0)) < int(time.time()):
            return None
        usuario = dados.get("u")
        return usuario if usuario in USUARIOS else None
    except Exception:
        return None


def usuario_do_request(request: Request) -> str | None:
    """Lê o cookie e retorna o usuário (ou None). Não levanta exceção."""
    return ler_token(request.cookies.get(COOKIE_NAME))


def usuario_atual(request: Request) -> str:
    """Dependency FastAPI: exige sessão válida; senão 401."""
    usuario = usuario_do_request(request)
    if not usuario:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return usuario
