"""Autenticação multiusuário — login por cookie assinado (HMAC, stdlib).

Isolamento lógico: cada rota recupera o `dono` (username) do cookie de sessão
e o repassa ao repositório, que filtra TODA query por dono. Sem cookie válido,
nenhuma rota de dados responde.

Fonte de verdade da identidade (Fase 1 do PLANO_MULTIUSUARIO_2026): a tabela
`usuarios` no Postgres, espelhada aqui no `_usuarios_cache` em memória — o
hot-path do auth continua I/O-zero. Os dicts USUARIOS/OPERADORES/
PLANILHAS_AO_VIVO viraram SEMENTE: populam o cache no import (testes/dev sem
banco) e a tabela via seed; no boot o banco sobrescreve o cache e o refresher
do main o renova a cada ~60s. Sessão/login exigem `status='ativo'` — suspender
um usuário no banco revoga o cookie dele em ≤60s (C3 da auditoria).
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
# Em PRODUÇÃO (Railway) o SESSION_SECRET é OBRIGATÓRIO: sem ele o app NÃO sobe
# (fail-closed). Antes gerava um segredo efêmero que derrubava TODOS os logins a
# cada reinício e mascarava a env faltando — falha silenciosa. Em dev (fora do
# Railway) mantém o fallback aleatório + aviso, para não travar o local.
_EM_PRODUCAO = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("RAILWAY_PROJECT_ID"))
_secret_env = os.environ.get("SESSION_SECRET")
if not _secret_env and _EM_PRODUCAO:
    raise RuntimeError(
        "SESSION_SECRET ausente em produção — defina a variável no Railway. "
        "Fail-closed: o app não sobe sem segredo persistente (as sessões cairiam a cada restart)."
    )
SESSION_SECRET = _secret_env or secrets.token_hex(32)
if not _secret_env:
    logger.warning(
        "SESSION_SECRET não definido (ambiente de dev) — usando segredo efêmero aleatório. "
        "Sessões cairão a cada reinício. Defina SESSION_SECRET para persistir os logins."
    )


# SEMENTE (desde o Deploy B da Fase 1, quem manda é a tabela `usuarios` via
# _usuarios_cache — estes dicts só semeiam o cache no import e a tabela no seed).
# usuário → hash bcrypt da senha, vindo SEMPRE das env vars do Railway
# (SENHA_<USER>_HASH). SEM default no código: se a env faltar, o login falha
# (fail-closed) em vez de cair num hash hardcoded. Os hashes SHA-256 versionados
# foram removidos na migração bcrypt (fase 2 — ver STATUS "Hash de senha").
USUARIOS: dict[str, str] = {
    "Feca": os.environ.get("SENHA_FECA_HASH", ""),
    "Diogo": os.environ.get("SENHA_DIOGO_HASH", ""),
    "Primo": os.environ.get("SENHA_PRIMO_HASH", ""),
    "Lava": os.environ.get("SENHA_LAVA_HASH", ""),
    "Fatuch": os.environ.get("SENHA_FATUCH_HASH", ""),
    "LavaFatuch": os.environ.get("SENHA_LAVAFATUCH_HASH", ""),
    "Jonathan": os.environ.get("SENHA_JONATHAN_HASH", ""),
    "Gabriel": os.environ.get("SENHA_GABRIEL_HASH", ""),
    "LavaPessoal": os.environ.get("SENHA_LAVAPESSOAL_HASH", ""),
    "WilliamOliveira": os.environ.get("SENHA_WILLIAMOLIVEIRA_HASH", ""),
    "ViniciusOliveira": os.environ.get("SENHA_VINICIUSOLIVEIRA_HASH", ""),
    "SoChutes": os.environ.get("SENHA_SOCHUTES_HASH", ""),
    "ZoraEsports": os.environ.get("SENHA_ZORAESPORTS_HASH", ""),
}


# Hierarquia dono → operadores. Cada DONO (conta completa, par dos outros donos)
# pode "ver como" os próprios operadores — visualizar e operar a base deles sem
# deslogar. Donos NÃO se veem entre si (Feca não vê Diogo). Operadores não veem
# ninguém além de si mesmos (lista vazia). Lava é operador do Feca; Primo é
# operador do Diogo (mesmo modelo: Diogo tem base própria + vê a do Primo).
#
# ATENÇÃO ao parecido de nome: `LavaPessoal` é DONO SOLO — base pessoal, isolada,
# NÃO é operador do Feca (decisão do Feca ao criar a conta). Ninguém "vê como"
# LavaPessoal e ele não vê ninguém; `coproprietarios` = [] → sem dedup cruzada.
# Não o pendure em OPERADORES por semelhança com `Lava`.
OPERADORES: dict[str, list[str]] = {
    "Feca": ["Lava"],
    "Diogo": ["Primo"],
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


def linhas_seed_usuarios() -> list[tuple]:
    """Linhas de seed da tabela `usuarios` (Fase 1 do PLANO_MULTIUSUARIO_2026).

    Deriva dos dicts acima — que seguem sendo a fonte de verdade do auth até o
    Deploy B. Os usuários atuais entram `status='ativo'`; Feca é `admin`;
    operador ganha `parent_owner`; planilha viva vira `planilha_url`. Hash
    vazio (env ausente) vira NULL, nunca string vazia — NULL é o marcador de
    "sem senha local" (contas futuras só-social).

    Pura (sem banco) de propósito: quem toca o Postgres é
    `database.seed_usuarios()`; a montagem das linhas é testável em
    tests/test_seed_usuarios.py sem stub de asyncpg.
    """
    pai = {op: dono for dono, ops in OPERADORES.items() for op in ops}
    return [
        (
            username,
            senha_hash or None,
            "ativo",
            "admin" if username == "Feca" else "user",
            pai.get(username),
            PLANILHAS_AO_VIVO.get(username) or None,
        )
        for username, senha_hash in USUARIOS.items()
    ]


# ── Cache de identidade lastreado no banco (Fase 1 / Deploy B) ────────────────
# username → {senha_hash, status, role, parent_owner, planilha_url} — o formato
# das linhas de `database.carregar_usuarios()`. Substituído INTEIRO a cada
# carga (nunca mutado item a item): leitura sem lock, porque a troca do dict é
# atômica no CPython. Nasce da semente (dicts acima) para testes/dev sem banco;
# em produção o lifespan o sobrescreve com o banco antes da primeira request.
def _cache_da_semente() -> dict[str, dict]:
    return {
        username: {
            "senha_hash": senha_hash,
            "status": status,
            "role": role,
            "parent_owner": parent_owner,
            "planilha_url": planilha_url,
        }
        for (username, senha_hash, status, role, parent_owner, planilha_url) in linhas_seed_usuarios()
    }


_usuarios_cache: dict[str, dict] = _cache_da_semente()


def atualizar_cache_usuarios(linhas: list[dict]) -> None:
    """Substitui o cache inteiro pelo estado do banco (startup + refresher de 60s
    do main; a Fase 2 chama após aprovar/suspender). Lista vazia é IGNORADA —
    fail-safe: uma leitura quebrada nunca troca um cache bom por "ninguém loga"."""
    global _usuarios_cache
    if linhas:
        _usuarios_cache = {l["username"]: dict(l) for l in linhas}


def _usuario_ativo(usuario: str) -> bool:
    entrada = _usuarios_cache.get(usuario)
    return bool(entrada and entrada.get("status") == "ativo")


def eh_admin(usuario: str) -> bool:
    """Papel de admin (vê o agregado de custo; na Fase 2, aprova cadastros)."""
    entrada = _usuarios_cache.get(usuario)
    return bool(entrada and entrada.get("role") == "admin")


def operadores_de(usuario: str) -> list[str]:
    """Operadores que este usuário (dono) pode visualizar. Vazio = não é dono.

    Independe de status: suspender um operador corta o ACESSO dele (login e
    cookie morrem no gate de 'ativo'), mas não esconde a base dele do
    supervisor — dado não some junto com o acesso.
    """
    return sorted(
        u for u, e in _usuarios_cache.items() if e.get("parent_owner") == usuario
    )


def coproprietarios(usuario: str) -> list[str]:
    """Outros donos da MESMA linhagem supervisor↔operadores (exclui o próprio).

    Contas físicas são compartilhadas dentro da linhagem: um supervisor pode
    repassar uma conta que usou para um operador seu. Um bilhete cuja assinatura
    já existe sob um co-proprietário (mesma casa+parceiro) é a MESMA aposta física
    recapturada do histórico compartilhado — a dedup cruzada em `upsert_bilhetes`
    a barra para não contar duas vezes no painel do supervisor.

    Ex.: coproprietarios('Lava') -> ['Feca']; coproprietarios('Feca') -> ['Lava'].
    Dono solo (sem parent_owner e sem operadores) -> [] (nenhuma checagem cruzada).
    """
    entrada = _usuarios_cache.get(usuario)
    if not entrada:
        return []
    raiz = entrada.get("parent_owner") or usuario
    grupo = {
        u for u, e in _usuarios_cache.items() if (e.get("parent_owner") or u) == raiz
    }
    grupo.discard(usuario)
    return sorted(grupo)


def planilha_ao_vivo(dono: str) -> str:
    """URL do Apps Script /exec da planilha ao vivo deste dono, ou "" se ele lê
    do Postgres (o caso normal)."""
    entrada = _usuarios_cache.get(dono)
    return (entrada or {}).get("planilha_url") or ""


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


def resultado_login(usuario: str, senha: str) -> str:
    """Resultado do login: 'ok' | 'pendente' | 'suspenso' | 'invalido'.

    O status só é revelado quando a SENHA CONFERE — senha errada e usuário
    inexistente são o mesmo 'invalido' (não dá para enumerar contas nem
    descobrir o status de um cadastro alheio chutando senhas).
    """
    entrada = _usuarios_cache.get(usuario)
    if not entrada or not _verifica_hash(senha, entrada.get("senha_hash") or ""):
        return "invalido"
    status = entrada.get("status")
    if status == "ativo":
        return "ok"
    return status if status in ("pendente", "suspenso") else "invalido"


def verificar_credenciais(usuario: str, senha: str) -> bool:
    """Senha confere E o usuário está ativo. Pendente/suspenso não loga —
    mesmo com a senha certa (modelo "aberto com aprovação")."""
    return resultado_login(usuario, senha) == "ok"


def gerar_hash_senha(senha: str) -> str:
    """Hash bcrypt de um cadastro novo (Fase 2). CPU-bound (~100ms por desenho
    do bcrypt) — o chamador async deve rodar via asyncio.to_thread."""
    if bcrypt is None:
        raise RuntimeError("bcrypt indisponível — cadastro exige bcrypt instalado")
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def criar_token(usuario: str) -> str:
    exp = int(time.time()) + SESSION_MAX_AGE
    payload = base64.urlsafe_b64encode(
        json.dumps({"u": usuario, "exp": exp}).encode()
    ).decode()
    assinatura = hmac.new(
        SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{assinatura}"


def criar_token_curto(proposito: str, ttl: int = 600) -> str:
    """Token assinado de curta duração para fluxos de uma via — ex.: o `state`
    anti-CSRF do OAuth (Fase 3). Mesmo formato do cookie de sessão, mas com um
    PROPÓSITO no payload: um token de um fluxo nunca serve em outro."""
    exp = int(time.time()) + ttl
    payload = base64.urlsafe_b64encode(
        json.dumps({"p": proposito, "exp": exp}).encode()
    ).decode()
    assinatura = hmac.new(
        SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{assinatura}"


def validar_token_curto(token: str | None, proposito: str) -> bool:
    """True se o token curto é bem-assinado, do propósito certo e não expirou."""
    if not token:
        return False
    try:
        payload, assinatura = token.rsplit(".", 1)
        esperado = hmac.new(
            SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(assinatura, esperado):
            return False
        dados = json.loads(base64.urlsafe_b64decode(payload.encode()))
        return dados.get("p") == proposito and int(dados.get("exp", 0)) >= int(time.time())
    except Exception:
        return False


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
        # Gate de status a CADA request (C3 da auditoria): cookie bem-assinado
        # de usuário suspenso/removido morre aqui — desativar no banco revoga a
        # sessão em ≤60s (TTL do cache), sem esperar os 30 dias do cookie.
        return usuario if _usuario_ativo(usuario) else None
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
