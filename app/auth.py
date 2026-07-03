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
VER_COMO_COOKIE = "fdc_ver_como"     # cookie do "ver como" (operador sendo visualizado)
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


# usuário → hash bcrypt da senha, vindo SEMPRE das env vars do Railway
# (SENHA_<USER>_HASH). SEM default no código: se a env faltar, o login falha
# (fail-closed) em vez de cair num hash hardcoded. Os hashes SHA-256 versionados
# foram removidos na migração bcrypt (fase 2 — ver STATUS "Hash de senha").
USUARIOS: dict[str, str] = {
    "Feca": os.environ.get("SENHA_FECA_HASH", ""),
    "Diogo": os.environ.get("SENHA_DIOGO_HASH", ""),
    "Lava": os.environ.get("SENHA_LAVA_HASH", ""),
    "Fatuch": os.environ.get("SENHA_FATUCH_HASH", ""),
    "LavaFatuch": os.environ.get("SENHA_LAVAFATUCH_HASH", ""),
}


# Hierarquia dono → operadores. Cada DONO (conta completa, par dos outros donos)
# pode "ver como" os próprios operadores — visualizar e operar a base deles sem
# deslogar. Donos NÃO se veem entre si (Feca não vê Diogo). Operadores não veem
# ninguém além de si mesmos (lista vazia). Lava é operador do Feca; o(s)
# operador(es) do Diogo entram aqui quando forem cadastrados.
OPERADORES: dict[str, list[str]] = {
    "Feca": ["Lava"],
    "Diogo": [],
    "Fatuch": ["LavaFatuch"],
}


# Donos cuja base é uma planilha Google AO VIVO (Apps Script /exec) em vez do
# Postgres — Fase 1 do onboarding de um cliente: o dashboard lê a planilha dele
# em tempo real (o cliente segue lançando na própria planilha) até a migração
# para o banco (Fase 2). A URL vem de env var; ausente/vazia → cai no Postgres
# (fail-safe: nunca quebra quem não tem planilha viva). LavaFatuch é o operador
# do cliente Fatuch; toda a base dele mora na planilha ao vivo.
PLANILHAS_AO_VIVO: dict[str, str] = {
    "LavaFatuch": os.environ.get("PLANILHA_LAVAFATUCH_URL", ""),
}


def operadores_de(usuario: str) -> list[str]:
    """Operadores que este usuário (dono) pode visualizar. Vazio = não é dono."""
    return OPERADORES.get(usuario, [])


def planilha_ao_vivo(dono: str) -> str:
    """URL do Apps Script /exec da planilha ao vivo deste dono, ou "" se ele lê
    do Postgres (o caso normal)."""
    return PLANILHAS_AO_VIVO.get(dono) or ""


def pode_ver_como(real: str, alvo: str) -> bool:
    """O usuário logado `real` pode assumir a visão de `alvo`?

    Verdadeiro se `alvo` é ele mesmo ou um operador seu. Toda decisão de
    autorização passa por aqui, sempre contra o usuário REAL da sessão —
    nunca contra o cookie de "ver como" (que é só uma preferência assinada).
    """
    return alvo == real or alvo in operadores_de(real)


def _verifica_hash(senha: str, hash_guardado: str) -> bool:
    """Compara a senha com o hash bcrypt guardado (com salt + stretching)."""
    if not hash_guardado or bcrypt is None:
        return False
    try:
        return bcrypt.checkpw(senha.encode(), hash_guardado.encode())
    except (ValueError, TypeError):
        return False


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
    """Dependency FastAPI: exige sessão válida; senão 401.

    Retorna o usuário REAL da sessão (identidade) — usado por /me e /ver-como.
    As rotas de DADOS usam `dono_efetivo` (que pode ser um operador visualizado).
    """
    usuario = usuario_do_request(request)
    if not usuario:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return usuario


def dono_efetivo(request: Request) -> str:
    """Dependency das rotas de DADOS: o dono cujos dados a requisição enxerga.

    Em geral é o próprio usuário logado. Se houver um cookie de "ver como"
    válido E o usuário real estiver autorizado a ver aquele operador
    (`pode_ver_como`), retorna o operador — todas as queries (ler E escrever)
    passam a operar sobre a base dele. A autorização é SEMPRE reavaliada aqui
    contra a sessão real: um cookie de "ver como" forjado/obsoleto cai no
    fallback para o próprio usuário, nunca escala privilégio.
    """
    real = usuario_do_request(request)
    if not real:
        raise HTTPException(status_code=401, detail="Não autenticado")
    alvo = ler_token(request.cookies.get(VER_COMO_COOKIE))
    if alvo and alvo != real and pode_ver_como(real, alvo):
        return alvo
    return real
