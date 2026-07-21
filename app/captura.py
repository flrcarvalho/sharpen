"""Ponte de captura — pareamento efêmero extensão ⇄ dashboard.

Modelo de dispositivo (igual parear WhatsApp Web / Chromecast): uma SESSÃO liga
uma instância da extensão a um slot (dono, casa, parceiro) por um código curto.

Fluxo:
  1. Dashboard chama `criar_sessao` → devolve um `codigo` legível (copiado p/ o
     usuário) e um `sessao_id` secreto (o dashboard faz poll com ele).
  2. Extensão chama `conectar(codigo)` → recebe um `token_ext` longo (usado só
     para enviar capturas; o código curto sozinho não envia nada).
  3. Extensão manda prints/texto via `adicionar_captura` (autenticada pelo token).
  4. Dashboard faz poll e `drenar_capturas` injeta na área de colar.

Registro EM MEMÓRIA — processo único, como o cache dos masters e o cache_warmer.
Reinício do servidor derruba as pontes ativas (o usuário só reconecta: gera novo
código). É efêmero por natureza, então isso é aceitável. Sem dependências novas.
"""
import secrets
import threading
import time
from dataclasses import dataclass, field

# Alfabeto sem caracteres ambíguos (0/O, 1/I/L) — o código é digitado/colado à mão.
_CODIGO_ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODIGO_LEN = 8                     # 8 chars de 31 símbolos ≈ 8.5e11 combinações

SESSAO_TTL = 6 * 60 * 60           # sessão viva por até 6h sem atividade
CODIGO_TTL = 15 * 60               # código válido p/ CONECTAR por 15 min
MAX_CAPTURAS = 60                  # fila máxima por sessão (anti-OOM)
MAX_SESSOES = 300                  # teto global de sessões vivas

# Modo de captura por casa. Betano, Superbet, Bet365, BETesporte, Betfair e Pinnacle = texto
# (robô); Pinnacle: o robô lê a RESPOSTA da API POST /member-service/v2/wager-filter (array
# posicional convertido em objeto pelo pn_inject: id, odd, stake, status, datas, seleção,
# pernas) e RE-EMITE a busca das duas abas (Decidido + Não decidido) — abertas e encerradas
# numa rodada, sem OCR e sem trocar aba na tela.
# o resto = print (moldura + Snap). Superbet: cada card tem o CÓDIGO no atributo `id`
# (exato, sem OCR). Bet365: sem ID nem data, mas o texto do card vem completo no DOM
# (mesmo recolhido) → robô lê tudo sem clicar. BETesporte: o robô lê a RESPOSTA da API
# /api/bet/RequestUserTickets (JSON exato: id, odd, value, status, date) — resolve o ID
# que não aparece na lista (só no "Ver Cupom") → dedup passa a funcionar. Betfair: o robô
# lê a RESPOSTA da API POST /activity/sportsbook (JSON exato: betId O/…, settledDate,
# status WON/LOST/VOID, stake, odd) — data de resolução de TODO bilhete, perda inclusive
# (o extrato CSV não tinha linha p/ perda). Substitui o fluxo texto+extrato com join no código.
_MODO_POR_CASA = {"BETANO": "texto", "SUPERBET": "texto", "BET365": "texto", "BETESPORTE": "texto", "BETFAIR": "texto", "PINNACLE": "texto"}


def modo_da_casa(casa_key: str) -> str:
    return _MODO_POR_CASA.get((casa_key or "").upper(), "print")


# Domínios operacionais (BR) por casa — amarração casa↔site: uma captura vinda do site
# de uma casa CONHECIDA não pode ser gravada no slot de OUTRA casa (ex.: conectar código
# de Betfair e capturar na Superbet). Só as casas de robô estão aqui (é onde flui dado
# estruturado e onde o engano dói); casa de print com domínio desconhecido → None → passa
# (não bloqueia captura legítima que não temos como verificar).
_HOSTS_POR_CASA = {
    "SUPERBET":   ("superbet.bet.br", "superbet.com"),
    "BETANO":     ("betano.bet.br",),
    "BET365":     ("bet365.com", "bet365.bet.br"),
    "BETESPORTE": ("betesporte.bet.br",),
    "BETFAIR":    ("betfair.bet.br",),
    "PINNACLE":   ("pinnacle.bet.br",),
}


def casa_de_host(host: str) -> str | None:
    """casa_key da casa CONHECIDA dona do domínio, ou None se não reconhecido.
    Casa o host exato ou subdomínio (ex.: myactivity.betfair.bet.br → BETFAIR)."""
    h = (host or "").strip().lower()
    if not h:
        return None
    for casa_key, hosts in _HOSTS_POR_CASA.items():
        if any(h == x or h.endswith("." + x) for x in hosts):
            return casa_key
    return None


@dataclass
class Captura:
    id: str
    tipo: str            # "imagem" | "texto"
    media_type: str      # ex.: "image/png" (vazio p/ texto)
    data: str            # imagem em base64 OU o texto puro
    recebido: float


@dataclass
class Sessao:
    sessao_id: str
    codigo: str
    dono: str
    casa: str
    casa_key: str
    parceiro: str
    modo: str
    criado: float
    atividade: float
    token_ext: str = ""
    conectado: bool = False
    versao_ext: str = ""          # versão da extensão pareada (p/ sinalizar desatualizado)
    capturas: list = field(default_factory=list)


_LOCK = threading.Lock()
_SESSOES: dict[str, Sessao] = {}   # sessao_id -> Sessao


def _agora() -> float:
    return time.time()


def _prune(agora: float) -> None:
    """Remove sessões inativas há mais que SESSAO_TTL. Chamar sob _LOCK."""
    mortas = [sid for sid, s in _SESSOES.items() if agora - s.atividade > SESSAO_TTL]
    for sid in mortas:
        _SESSOES.pop(sid, None)


def _novo_codigo() -> str:
    """Código único entre as sessões vivas, no formato ABCD-EFGH."""
    ativos = {s.codigo for s in _SESSOES.values()}
    while True:
        bruto = "".join(secrets.choice(_CODIGO_ALFABETO) for _ in range(_CODIGO_LEN))
        codigo = f"{bruto[:4]}-{bruto[4:]}"
        if codigo not in ativos:
            return codigo


def criar_sessao(dono: str, casa: str, casa_key: str, parceiro: str) -> Sessao:
    """Cria uma sessão de pareamento para o dashboard. Devolve a Sessao."""
    agora = _agora()
    with _LOCK:
        _prune(agora)
        # Teto global: se estourar, derruba a sessão mais antiga inativa.
        if len(_SESSOES) >= MAX_SESSOES:
            mais_velha = min(_SESSOES.values(), key=lambda s: s.atividade)
            _SESSOES.pop(mais_velha.sessao_id, None)
        sess = Sessao(
            sessao_id=secrets.token_urlsafe(24),
            codigo=_novo_codigo(),
            dono=dono,
            casa=casa,
            casa_key=casa_key,
            parceiro=parceiro,
            modo=modo_da_casa(casa_key),
            criado=agora,
            atividade=agora,
        )
        _SESSOES[sess.sessao_id] = sess
        return sess


def sessao_por_id(sessao_id: str) -> Sessao | None:
    with _LOCK:
        return _SESSOES.get(sessao_id)


def conectar(codigo: str) -> Sessao | None:
    """A extensão troca o código curto por um token de envio. O código só vale
    para conectar dentro de CODIGO_TTL; depois disso, gere outro no dashboard."""
    agora = _agora()
    alvo = (codigo or "").strip().upper()
    with _LOCK:
        _prune(agora)
        for sess in _SESSOES.values():
            if sess.codigo == alvo:
                if agora - sess.criado > CODIGO_TTL:
                    return None      # código expirado para conexão
                if not sess.token_ext:
                    sess.token_ext = secrets.token_urlsafe(32)
                sess.conectado = True
                sess.atividade = agora
                return sess
        return None


def registrar_versao(sess: Sessao, versao: str) -> None:
    """Guarda a versão reportada pela extensão nos handshakes (conectar/validar/enviar).
    Insumo do sinal de 'desatualizada' que o popup e o extrator mostram. Vazio = ignora
    (extensão antiga que ainda não reporta versão — tratada como desatualizada na leitura)."""
    v = (versao or "").strip()
    if not v:
        return
    with _LOCK:
        sess.versao_ext = v


def sessao_por_token(token: str) -> Sessao | None:
    if not token:
        return None
    with _LOCK:
        for sess in _SESSOES.values():
            if sess.token_ext and secrets.compare_digest(sess.token_ext, token):
                sess.atividade = _agora()
                return sess
        return None


def adicionar_captura(sess: Sessao, tipo: str, media_type: str, data: str) -> bool:
    """Enfileira uma captura. False se a fila está cheia (o dashboard precisa
    drenar antes)."""
    with _LOCK:
        if len(sess.capturas) >= MAX_CAPTURAS:
            return False
        sess.capturas.append(Captura(
            id=secrets.token_hex(6),
            tipo=tipo,
            media_type=media_type,
            data=data,
            recebido=_agora(),
        ))
        sess.atividade = _agora()
        return True


def drenar_capturas(sess: Sessao) -> list[Captura]:
    """Devolve as capturas pendentes e esvazia a fila (entrega única)."""
    with _LOCK:
        pendentes = sess.capturas
        sess.capturas = []
        sess.atividade = _agora()
        return pendentes


def encerrar(sessao_id: str) -> None:
    with _LOCK:
        _SESSOES.pop(sessao_id, None)
