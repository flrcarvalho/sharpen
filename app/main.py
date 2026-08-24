import asyncio
import base64
import csv
import gzip
import hashlib
import hmac
import io
import json
import logging
import math
import os
import re
import time
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urlsplit

import httpx

import xlrd

from anthropic import (
    APIConnectionError, APIStatusError, AsyncAnthropic, RateLimitError,
)
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from auth import (
    COOKIE_NAME, SESSION_MAX_AGE, VER_COMO_COOKIE, atualizar_cache_usuarios,
    coproprietarios, criar_token, criar_token_curto, dono_efetivo,
    dono_efetivo_ou_bot, eh_admin, email_de, gerar_hash_senha, operadores_de,
    planilha_ao_vivo, pode_ver_como, resultado_login, tem_senha, usuario_atual,
    usuario_atual_ou_bot, usuario_ativo, usuario_do_request, validar_token_curto,
    verificar_credenciais,
)
import captura as _captura
import eventos as _eventos
from planilha_viva import dashboard_rows_ao_vivo
from config import ALLOWED_MODELS, CASAS_DIR, DEFAULT_MODEL
from taxonomia import categorias_canonicas, esportes_canonicos
from database import (
    atualizar_email_usuario, atualizar_senha_usuario,
    buscar_usuario_social, carregar_usuarios, criar_usuario,
    criar_usuario_social, definir_bot_habilitado, definir_status_usuario,
    init_db, listar_usuarios, seed_usuarios, usernames_em_uso, vincular_social,
)
from polymarket import CambioIndisponivel, coletar_dashboard, coletar_tudo
from prompts import build_system
from repository import (
    analisar_extracao,
    arquivar_parceiro, atualizar_bilhete, auto_arquivar, contar_arquivados,
    casas_com_parceiros, contar_bilhetes, contar_incompletos, contar_pendencias,
    anexar_sistema_tsv,
    corrigir_codigos_tsv,
    set_casa_dominio, get_casas_dominios,
    get_custo_store, salvar_custo_store,
    get_custo_conta, salvar_custo_conta,
    criar_parceiro, dashboard_rows, data_valida, deletar_bilhetes,
    export_bilhetes, get_ativos_tipster, get_codigos_existentes,
    get_codigos_resolvidos, get_tipster_por_codigo, remover_bilhetes_supersedidos,
    flags_pos_edicao, limpar_ativos_tipster, list_bilhetes, list_esportes,
    list_mercados, list_tipsters,
    criar_tipster, list_tipsters_cadastro, arquivar_tipster, reativar_tipster,
    atualizar_tipster_info, renomear_tipster,
    casas_visao, salvar_casa_config,
    get_escada_unidade, set_unidade, remover_unidade, resultado_em_unidades,
    get_escadas_todas, sugerir_tipster,
    resultado_valido, set_ativo_tipster, set_tipster_bulk,
    casa_canonica, excluir_parceiro, get_parceiro, list_parceiros, parse_tsv,
    reativar_parceiro, renomear_parceiro, restaurar_bilhetes, resumo_conta,
    resumo_parceiro, upsert_bilhetes,
    validar_linhas, valor_monetario_valido,
    registrar_uso, uso_resumo,
    conferir_cobertura, codigos_do_texto,
)

logger = logging.getLogger("scanner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

_client = AsyncAnthropic()

# Tarefas fire-and-forget (ex.: gravar uso de tokens sem bloquear o stream). Guarda
# uma referência forte até concluir — senão o GC pode matar a task antes da hora.
_bg_tasks: set = set()
def _fire(coro):
    t = asyncio.create_task(coro)
    _bg_tasks.add(t)
    t.add_done_callback(_bg_tasks.discard)

_MAX_CHUNKS = 4
_MAX_CONCURRENT = 8      # requests simultâneos à API (semáforo). Subiu de 4 p/ 8 para PDF
                        # grande: mais chunks pequenos em paralelo → o chunk mais lento
                        # termina antes e a extração não estoura o timeout de borda.
_IMGS_POR_CHUNK = 3     # páginas de PDF / imagens por chunk. Chunk enxuto = resposta rápida;
                        # 50 páginas viram ~17 chunks pequenos (concorrência limitada pelo
                        # semáforo) em vez de 4 chunks gordos de ~13 páginas que travavam.

# Limites de upload (validados no servidor — o teto do front é contornável).
_MAX_IMGS = 15
_MAX_IMG_BYTES = 12 * 1024 * 1024     # 12 MB por imagem
_MAX_TOTAL_BYTES = 60 * 1024 * 1024   # 60 MB somando todas as imagens
_MAX_XLS_BYTES = 20 * 1024 * 1024     # 20 MB para o XLS
_ALLOWED_IMG_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
# PDF (ex.: extrato "Apostas Resolvidas" da Bet365 salvo como PDF): convertido no
# servidor para 1 PNG por página, injetado no MESMO caminho de imagem da extração
# (chunking, ordem newest-first e detecção de sobreposição reaproveitados). Cada
# página conta como 1 imagem no teto _MAX_IMGS.
_MAX_PDF_BYTES = 25 * 1024 * 1024     # 25 MB por PDF
_MAX_PDF_PAGES = 50                   # páginas por PDF (extrato de semana/mês tem muitas).
                                     # Também é o teto COMBINADO de blocos de imagem
                                     # (imagens coladas + páginas de PDF) num envio. Colagem
                                     # avulsa de imagens segue limitada a _MAX_IMGS (15).
_PDF_RENDER_ZOOM = 2.0                # zoom-alvo (~150 dpi) para página tamanho carta/A4
_PDF_MAX_LONG_PX = 2400              # teto do lado maior do PNG: página gigante (pôster,
                                     # export largo) NÃO é renderizada a 2.0x — o zoom cai
                                     # para caber aqui. Evita bitmap gigante que trava/estoura
                                     # memória e derrubava o request com 500.

# Retry com backoff exponencial para picos da API Anthropic (overloaded 529 / rate-limit 429).
_RETRY_MAX = 4          # tentativas extras além da primeira
_RETRY_BASE = 1.0       # segundos: espera = base * 2**(tentativa-1) → 1s, 2s, 4s, 8s


def _is_retryable(exc: Exception) -> bool:
    """True para erros transitórios que valem nova tentativa (sobrecarga/limite/conexão)."""
    if isinstance(exc, (APIConnectionError, RateLimitError)):
        return True
    if isinstance(exc, APIStatusError):
        if getattr(exc, "status_code", None) in (429, 500, 502, 503, 529):
            return True
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            tipo = (body.get("error") or {}).get("type")
            if tipo in ("overloaded_error", "rate_limit_error", "api_error"):
                return True
    return False
_TSV_HEADER = "Data\tEsporte\tTipster\tCasa\tParceiro\tAposta\tDescrição\tStake\tOdd\tResultado\tCódigo"

_CASA_DISPLAY: dict[str, str] = {
    "BET365":         "Bet365",
    "BETANO":         "Betano",
    # ⚠ A MARCA escreve "BetBoom", mas a canônica aqui é "Betboom" — medido antes de
    # registrar (s250): a base já tem 172 bilhetes, 3 contas e 3 perfis de tipster nessa
    # grafia. Registrar uma casa neste mapa é mudança RETROATIVA (reinterpreta toda conta
    # que já existe na grafia gêmea); foi assim que a Jonbet quebrou na s249. Aqui o
    # round-trip `_casa_display(_display_to_key("Betboom"))` fecha em identidade.
    "BETBOOM":        "Betboom",
    "BETESPORTE":     "BETesporte",
    "BETFAIR":        "Betfair",
    "BETFAST":        "Betfast",
    "FAZ1BET":        "Faz1bet",
    "BETNACIONAL":    "Betnacional",
    # ⚠ NÃO confundir com `PixBet`, que é OUTRA casa e tem 56 bilhetes na base (medido s258).
    # `PIXBET` não está neste mapa, então o round-trip dela segue verbatim e nada é
    # reinterpretado. A grafia canônica aqui foi MEDIDA antes de registrar: já existiam
    # 1 conta em `parceiros` e 1 linha em `casas_meta` exatamente como `Betpix365`
    # (0 bilhetes — a conta nasceu sem captura). Ver o aviso de mudança RETROATIVA em
    # docs/SHARPENUP_ARQUITETURA.md §5.
    "BETPIX365":      "Betpix365",
    "BOLSADEAPOSTA":  "Bolsa de Aposta",
    # ⚠ A MARCA escreve "EsportivaBet" (logo) / "Esportiva Bet" (título), mas a canônica
    # aqui é "Esportiva" — MEDIDO antes de registrar (s254): a base já tinha 351 bilhetes,
    # 2 contas e 4 perfis de tipster nessa grafia, e nenhuma linha em "Esportiva Bet".
    # (Há resquício de `Esportivabet` em casas_meta/correcoes/uso_tokens, do bug antigo de
    # title-case descrito acima; ele NÃO entra no mapa, então o round-trip das duas grafias
    # fecha em identidade e nenhuma conta existente é reinterpretada.)
    "ESPORTIVA":      "Esportiva",
    "JOGODEOURO":     "Jogo de Ouro",
    "JONBET":         "Jonbet",
    "KINGPANDA":      "KingPanda",
    "KTO":            "KTO",
    "LOTTU":          "Lottu",
    "PINNACLE":       "Pinnacle",
    # A antiga "Rei do Pitaco" (`pitaco.bet.br`). **`Pitaco` é o nome padrão desde a s270** —
    # a grafia velha foi unificada no banco na mesma sessão (`scripts/unificar_casas.py
    # --somente "Rei do Pitaco"`): 54 bilhetes de 2 donos movidos, 54 assinaturas
    # recalculadas, resíduo ZERO nas 7 tabelas onde `casa` é texto. Não recriar a chave
    # `REIDOPITACO`: ela deixaria de casar com qualquer linha do banco.
    "PITACO":         "Pitaco",
    # A base já usava esta grafia MUITO antes do registro: 849 bilhetes de 4 donos, 9 contas,
    # 2 `casas_meta`, 109 `correcoes` e 4 `tipsters.casas` — todos em `Novibet`, sem nenhuma
    # variante (medido na s271, `ilike '%novi%'` nas 7 tabelas). Round-trip conferido antes de
    # registrar: 59 grafias distintas em `parceiros`, 0 quebradas. Ver o aviso de mudança
    # RETROATIVA em docs/SHARPENUP_ARQUITETURA.md §5 — é o defeito que matou a Jonbet na s249.
    "NOVIBET":        "Novibet",
    "POLYMARKET":     "Polymarket",
    # A base já usava esta grafia antes do registro (1 conta e 8 bilhetes do LavaPessoal,
    # medidos na s257) — então o round-trip `_casa_display(_display_to_key("Stake"))` continua
    # identidade e nenhuma conta existente deixa de casar com os bilhetes. Ver o aviso de
    # mudança RETROATIVA em docs/SHARPENUP_ARQUITETURA.md §5.
    "STAKE":          "Stake",
    # A base já usava esta grafia muito antes do registro, e a MEDIÇÃO decidiu (s289):
    # `SportingBet` tinha 119 bilhetes / 5 contas / 4 donos (Feca, Tonelada, Jonathan,
    # LavaPessoal) contra 4 bilhetes / 1 conta em `Sportingbet` (Diogo). A gêmea foi
    # unificada ANTES desta linha entrar — `scripts/unificar_casas.py --somente Sportingbet
    # --aplicar`, 4 bilhetes movidos e 4 assinaturas recalculadas, zero colisão. Na ordem
    # inversa, os 4 bilhetes do Diogo ficariam numa casa que a conta dele não enxerga:
    # grade vazia, sem erro nenhum — o defeito que matou a Jonbet na s249 (ver o aviso de
    # mudança RETROATIVA em docs/SHARPENUP_ARQUITETURA.md §5).
    "SPORTINGBET":    "SportingBet",
    "SUPERBET":       "Superbet",
    "TIVO":           "Tivo",
    "VAIDEBET":       "VaideBet",
    "VITORIABET":     "Vitória Bet",
}


def _casa_display(key: str) -> str:
    # Casa MAPEADA → nome oficial. Casa fora do mapa (modo cego / worldwide): a
    # "chave" JÁ É o próprio display verbatim (ver _display_to_key), então devolve
    # como está — NUNCA .title(). Title-casear destruía nomes de casa cega:
    # "Rei do Pitaco" virava "Rei Do Pitaco"; combinado com o replace de espaço do
    # _display_to_key, "Esportiva Bet" virava "Esportivabet" e criava conta paralela.
    return _CASA_DISPLAY.get(key.upper(), key)


def _display_to_key(name: str) -> str:
    """Converte display name ou chave para a chave canônica (ex: 'Bolsa de Aposta' → 'BOLSADEAPOSTA').

    Para casa FORA do mapa (modo cego), a chave é o próprio nome preservado verbatim
    (apenas trim) — assim o round-trip _casa_display(_display_to_key(x)) == x e o nome
    de casas de 2+ palavras não é mais mutilado (espaço/caixa preservados)."""
    upper = name.upper()
    if upper in _CASA_DISPLAY:
        return upper
    for key, display in _CASA_DISPLAY.items():
        if display.upper() == upper:
            return key
    return name.strip()


# ── Cache warmer ──────────────────────────────────────────────────────────────

async def _cache_warmer():
    """Mantém o cache ephemeral dos masters vivo com ping a cada 4 min (TTL Anthropic = 5 min)."""
    await asyncio.sleep(30)
    while True:
        try:
            await _client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1,
                system=build_system("SUPERBET"),
                messages=[{"role": "user", "content": "ping"}],
            )
        except Exception:
            pass
        await asyncio.sleep(240)


async def _usuarios_refresher():
    """Recarrega o cache de identidade do banco a cada 60s (TTL defensivo do
    PLANO_MULTIUSUARIO §1.2): aprovar/suspender usuário propaga a todos os
    workers em ≤60s sem custo no hot-path. Falha mantém o último cache bom."""
    while True:
        await asyncio.sleep(60)
        try:
            atualizar_cache_usuarios(await carregar_usuarios())
        except Exception:
            logger.exception("refresh do cache de usuarios falhou — mantendo o último estado bom")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    # Fase 1 (PLANO_MULTIUSUARIO_2026): semeia a tabela `usuarios` (idempotente,
    # ON CONFLICT DO NOTHING) e carrega o cache de identidade do banco — a
    # tabela é a fonte de verdade desde o Deploy B. Falha aqui NÃO derruba o
    # boot: o cache segue com a semente dos dicts de auth.py (comportamento
    # idêntico ao pré-Deploy B) e o refresher tenta de novo a cada 60s.
    try:
        await seed_usuarios()
        atualizar_cache_usuarios(await carregar_usuarios())
    except Exception:
        logger.exception("seed/carga inicial de usuarios falhou — cache segue na semente; refresher reitera")
    asyncio.create_task(_cache_warmer())
    asyncio.create_task(_usuarios_refresher())
    # Tempo real (s241): LISTEN base_mudou numa conexão dedicada; alimenta /eventos.
    asyncio.create_task(_eventos.escutar_banco())
    yield


app = FastAPI(title="Sharpen — Scanner de Bets", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


# ── Cabeçalhos de segurança (CSP + hardening) ─────────────────────────────────
# Defesa em profundidade junto do escaping do frontend. A CSP restringe as origens
# às realmente usadas e bloqueia o resto. Chart.js/html2canvas agora são VENDORIZADOS
# (app/static/dash/vendor/) → script-src não precisa mais de CDN externo, só 'self'.
# 'unsafe-inline' segue necessário enquanto o front usa handlers/estilos inline
# (removê-los é o próximo passo para dropar o 'unsafe-inline' e travar em 'self' puro).
# frame-ancestors 'self' preserva os iframes da casca (/app). connect-src 'self': o
# front só fala com a própria origem (a Polymarket é chamada server-side).
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "  # fontes agora são SELF-HOST (/static/fonts.css) — sem Google Fonts
    "font-src 'self'; "  # woff2 servidos de /static/fonts/ (mesma origem)
    "img-src 'self' data: blob: https:; "  # favicons das casas: o s2/favicons do Google redireciona p/ gstatic → libera imagem https (não executa script)
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'self'"
)


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("Content-Security-Policy", _CSP)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # ── HTML nunca fica preso no cache do navegador (s215) ────────────────────
    # Os assets levam `?v=` no src, então bumpar a versão os renova. Mas o `?v=`
    # vive DENTRO do HTML — e o HTML não tinha `Cache-Control` nenhum, o que faz
    # o navegador escolher sozinho por quanto tempo não perguntar ao servidor
    # (heurística de ~10% da idade do arquivo: horas ou dias).
    #
    # O efeito é pior do que "dado velho": o navegador serve a casca ANTIGA e ela
    # referencia os assets pelas URLs antigas — que hoje devolvem o conteúdo NOVO.
    # Tela nova aparece, script novo não, porque a tag que o chama só existe na
    # casca nova. Foi exatamente o que aconteceu com a tela "Em Aberto": a página
    # montou vazia porque o `<script src="charts/abertas.js">` nunca foi pedido.
    #
    # `no-cache` NÃO proíbe guardar — obriga a REVALIDAR. Com o ETag que o
    # StaticFiles já manda, o custo normal é um 304 sem corpo. Só HTML: JS/CSS
    # seguem cacheáveis, senão o `?v=` perderia a razão de existir.
    # Travado em tests/test_cache_headers.py (os dois lados da regra).
    if resp.headers.get("content-type", "").startswith("text/html"):
        resp.headers["Cache-Control"] = "no-cache, must-revalidate"
    return resp


# ── Proteção CSRF leve: checagem de Origin/Referer ────────────────────────────
# Cookie de sessão + dados financeiros → validamos a origem das requisições que
# MUTAM estado (POST/PUT/PATCH/DELETE). SameSite=Lax já barra o CSRF clássico;
# isto é o cinto adicional. Regra: havendo Origin (ou, na falta, Referer), o host
# tem de bater com o host da própria requisição (Railway encaminha em
# X-Forwarded-Host) ou com um host extra em ALLOWED_ORIGIN_HOSTS. Sem Origin nem
# Referer (cliente não-browser) não há o que verificar → passa. Métodos seguros
# (GET/HEAD/OPTIONS) são isentos. Registrado como middleware DEPOIS de
# _security_headers → roda ANTES dele (outermost), rejeitando cedo.
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Rotas da EXTENSÃO de captura: chegam com Origin da casa (superbet.com) ou da
# própria extensão (chrome-extension://…), nunca do sharpen.bet, então bateriam
# no guarda de origem. São isentas do guarda porque fazem a PRÓPRIA autenticação
# — /conectar exige um código válido e curto; /enviar e /validar exigem o token de sessão.
_CAPTURA_ISENTAS = {"/captura/conectar", "/captura/enviar", "/captura/validar"}
_ALLOWED_ORIGIN_HOSTS = {
    h.strip().lower()
    for h in os.environ.get("ALLOWED_ORIGIN_HOSTS", "").split(",")
    if h.strip()
}


def _host_de(valor: str) -> str:
    """Host (minúsculo, sem esquema nem porta) de uma URL de Origin/Referer ou de um Host."""
    if not valor:
        return ""
    if "://" in valor:
        return (urlsplit(valor).hostname or "").lower()
    return valor.split(":")[0].strip().lower()


@app.middleware("http")
async def _csrf_origin_guard(request: Request, call_next):
    if request.method in _UNSAFE_METHODS and request.url.path not in _CAPTURA_ISENTAS:
        fonte = request.headers.get("origin") or request.headers.get("referer")
        if fonte:
            proprio = _host_de(request.headers.get("x-forwarded-host")
                               or request.headers.get("host") or "")
            permitidos = {h for h in ({proprio} | _ALLOWED_ORIGIN_HOSTS) if h}
            if _host_de(fonte) not in permitidos:
                logger.warning("Origem bloqueada em %s %s: %s",
                               request.method, request.url.path, fonte)
                return JSONResponse(status_code=403, content={"detail": "Origem não autorizada."})
    return await call_next(request)


@app.get("/healthz")
async def healthz():
    """Liveness para o HEALTHCHECK do container — sem auth, sem tocar o banco."""
    return {"ok": True}


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    # Loga o detalhe internamente; ao cliente vai só uma mensagem genérica
    # (não vazar tipo/mensagem da exceção, que pode revelar schema/caminhos).
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno. Tente novamente."},
    )


# ── Helpers XLS ──────────────────────────────────────────────────────────────

def _xls_sel_labels(sel: list[str]) -> list[str]:
    l1 = sel[1].strip() if len(sel) > 1 else ""
    l2 = sel[2].strip() if len(sel) > 2 else ""
    l3 = sel[3].strip() if len(sel) > 3 else ""
    if "-vs-" in l1:
        return ["Seleção", "Confronto", "Mercado", "Competição"]
    if "-vs-" in l2:
        if "Props de Jogadores" in l3:
            return ["Mercado seleção", "Jogador", "Confronto", "Tipo de mercado"]
        return ["Seleção", "Mercado específico", "Confronto", "Tipo de mercado"]
    return ["Seleção", "Linha 2", "Mercado", "Competição"]


def _xls_parse_rows(raw: bytes) -> list[dict]:
    wb = xlrd.open_workbook(file_contents=raw)
    ws = wb.sheet_by_index(0)
    rows = []
    for r in range(1, ws.nrows):
        det = str(ws.cell_value(r, 1)).strip().split("\n")
        sel = str(ws.cell_value(r, 2)).strip().split("\n")
        odd_raw = str(ws.cell_value(r, 3)).split("\n")[0].strip()
        stake_raw = str(ws.cell_value(r, 4)).split("\n")[0].replace("Risco:", "").strip()
        vd = ws.cell_value(r, 5)
        pl = f"{vd:+.2f}" if isinstance(vd, float) else str(vd)
        status_raw = str(ws.cell_value(r, 6)).strip().replace("\n", " | ")
        bet_id = det[0].strip() if det else ""
        rows.append({
            "id": bet_id, "det": det, "sel": sel,
            "odd": odd_raw, "stake": stake_raw, "pl": pl, "status": status_raw,
        })
    return rows


def _format_xls_rows(rows: list[dict]) -> str:
    parts = ["ARQUIVO XLS PINNACLE:\n"]
    for row in rows:
        det, sel = row["det"], row["sel"]
        labels = _xls_sel_labels(sel)
        block = [f"=== Aposta ID {row['id']} ==="]
        if len(det) > 1: block.append(f"Esporte: {det[1].strip()}")
        if len(det) > 2: block.append(f"Colocada: {det[2].strip()}")
        if len(det) > 3: block.append(f"Liquidada: {det[3].strip()}")
        for i, line in enumerate(sel):
            line = line.strip()
            if line:
                label = labels[i] if i < len(labels) else f"Info {i+1}"
                block.append(f"{label}: {line}")
        block += [f"Odd: {row['odd']}", f"Stake: {row['stake']}",
                  f"P&L: {row['pl']}", f"Status: {row['status']}"]
        parts.append("\n".join(block))
    return "\n\n".join(parts)


async def _parse_xls(raw: bytes, dono: str, casa: str = "", parceiro: str = "") -> tuple[str, int]:
    rows = _xls_parse_rows(raw)
    if not rows:
        return "", 0
    all_ids = [r["id"] for r in rows if r["id"]]
    # "Já tenho" = já tenho NESTA CONTA (ver a nota de escopo em `repository.py`).
    known_ids = await get_codigos_existentes(all_ids, dono, casa, parceiro)
    new_rows = [r for r in rows if r["id"] not in known_ids]
    skipped = len(rows) - len(new_rows)
    new_rows_oldest_first = list(reversed(new_rows))
    if not new_rows_oldest_first:
        return "", skipped
    return _format_xls_rows(new_rows_oldest_first), skipped


# ── Betano LEGADO: split por bilhete + pré-dedup por ID (formato antigo de scraping) ──
# ⚠️ NÃO é mais o caminho da Betano. Desde a migração p/ ingestão por API (bn_inject), a
# Betano emite o marcador [Código: ...] e é roteada como Superbet/BETesporte (ver
# _build_chunks e o dispatch de pré-dedup). Estas funções cobrem só o formato ANTIGO
# (linha-tipo Simples/Dupla + rodapé ID:), hoje inalcançável exceto pelo fallback de texto
# — mantidas como referência histórica; podem ser removidas quando o fallback sair.
_BETANO_SPLIT_RE = re.compile(r'(?m)(?=^(?:Simples|Dupla|Tripla|\d+-seleções)\s*$)')
_BETANO_ID_RE = re.compile(r'^ID:\s*(\d+)', re.MULTILINE)


def _split_betano_bilhetes(text: str) -> list[str]:
    """Divide o texto colado da Betano em blocos de 1 bilhete cada."""
    return [b.strip() for b in _BETANO_SPLIT_RE.split(text) if b.strip()]


async def _dedup_betano_text(text: str, dono: str, casa: str = "",
                             parceiro: str = "") -> tuple[str, int]:
    """Remove bilhetes já liquidados no banco + duplicatas de scroll dentro do colar.

    Retorna (texto_filtrado, qtd_ignorada). Mantém a ordem original (mais recente no topo).
    Bilhetes sem ID legível são sempre mantidos.
    """
    blocks = _split_betano_bilhetes(text)
    if len(blocks) < 2:
        return text, 0

    ids = []
    for b in blocks:
        m = _BETANO_ID_RE.search(b)
        ids.append(m.group(1) if m else None)

    # Escopado na CONTA: bilhete que já existe em OUTRA conta do mesmo dono não pode
    # sumir do lote desta aqui (ver a nota em `repository.py`).
    ja_resolvidos = await get_codigos_resolvidos([i for i in ids if i], dono, casa, parceiro)

    mantidos: list[str] = []
    vistos: set[str] = set()
    skipped = 0
    for block, bid in zip(blocks, ids):
        if bid:
            if bid in vistos or bid in ja_resolvidos:
                skipped += 1
                continue
            vistos.add(bid)
        mantidos.append(block)

    if not mantidos:
        return "", skipped
    return "\n\n".join(mantidos), skipped


# ── Superbet: split por bilhete + pré-dedup por ID ─────────────────────────────

# Cada bilhete Superbet (texto do robô) começa com o marcador "[Código: XXXX-XXXXXX]".
# O robô lê o código exato do atributo `id` do DOM (sem OCR) → o marcador é a fronteira
# 100% confiável do bilhete, equivalente à linha-tipo do Betano.
_SUPERBET_SPLIT_RE = re.compile(r'(?m)(?=^\[Código:\s)')
_SUPERBET_ID_RE = re.compile(r'^\[Código:\s*([^\]\r\n]+?)\s*\]', re.MULTILINE)
# A Bet365 (robô b3_inject) emite o MESMO marcador `[Código: BR…]` como 1ª linha de cada
# bilhete → usa este mesmo split/ID. Antes havia um `_BET365_SPLIT_RE` por `[Bilhete Bet365]`,
# marcador que o `formatTicketB3` NUNCA emitiu → o chunk nunca dividia e o lote inteiro ia num
# request só (sem paralelismo), e a bet365 ficava fora do pré-dedup. Corrigido: cai no split das
# demais.

# LISTA ÚNICA das casas cujo robô emite `[Código: …]` como 1ª linha de cada bilhete. Ela governa
# DUAS coisas que precisam andar juntas: o chunking (fatiar pelo marcador, não pelo frágil
# "\n\n") e o pré-dedup (descartar, ANTES da IA, o que já está resolvido no banco).
#
# Existia como duas tuplas literais repetidas a ~1100 linhas de distância — e a Pinnacle entrou
# na captura (s170) sem ser somada a nenhuma das duas: ficou 5 dias re-enviando à IA todos os
# bilhetes já resolvidos (456 no banco em 25/07) a cada recaptura, e fatiando pelo fallback.
# Uma lista só é o que impede a próxima casa de repetir isso — `tools/audit_sharpenup.py` confere.
#
# A BETFAIR fica de fora de propósito: ela tem duas ingestões (captura com marcador e o legado
# texto+extrato sem marcador) e é roteada POR CONTEÚDO (`"[Código:" in texto`), não por casa.
_CASAS_MARCADOR_CODIGO = frozenset({
    "SUPERBET", "BETESPORTE", "BETANO", "BET365", "KTO", "PINNACLE", "TIVO", "VAIDEBET",
    "BETFAST", "FAZ1BET", "BETNACIONAL", "JONBET", "BETBOOM", "ESPORTIVA", "JOGODEOURO", "STAKE",
    "BETPIX365",
    "PITACO",
    "NOVIBET",
    "SPORTINGBET",
})


def _split_superbet_bilhetes(text: str) -> list[str]:
    """Divide o texto colado da Superbet em blocos de 1 bilhete cada."""
    return [b.strip() for b in _SUPERBET_SPLIT_RE.split(text) if b.strip()]


# ── Betfair: join determinístico bilhete↔extrato pelo ID O/… ────────────────────
# O bilhete traz o ID (O/25146258/XXXX) mas NÃO a data; o extrato CSV traz a data de
# liquidação por ID. Antes o CSV INTEIRO ia pro modelo fazer o join → chamada única
# gigante, sem paralelismo, e `network error` em conta grande (Duka ~1044). Agora o
# código monta o mapa ID→data e preenche depois: os bilhetes viram texto normal,
# fatiado e paralelo, e o CSV nunca vai pro modelo.
_BETFAIR_SETTLED_RE = re.compile(r'(?:Bet Settled|Voided Bet Refund)\s*\(Bet Ref:\s*(O/\d+/\d+)\)')
_BETFAIR_ID_LINE_RE = re.compile(r'ID da aposta:\s*(O/\d+/\d+)')
_MESES_PT = {"jan": "01", "fev": "02", "mar": "03", "abr": "04", "mai": "05", "jun": "06",
             "jul": "07", "ago": "08", "set": "09", "out": "10", "nov": "11", "dez": "12"}


def _betfair_data(fonte: str) -> str:
    """'10-jul-26 17:26:50' → '10/07/2026'. Vazio se não parsear.

    O PONTO da abreviação é opcional (`\\.?`): em 25/07/2026 a Betfair passou a emitir
    '10-jul.-26'. Gêmeo do `_dbrBF` do `extensor/content.js` — se um mudar, mude o outro.
    """
    m = re.match(r'\s*(\d{1,2})-([a-zç]{3})\.?-(\d{2})', (fonte or "").strip().lower())
    if not m:
        return ""
    mes = _MESES_PT.get(m.group(2), "")
    return f"{m.group(1).zfill(2)}/{mes}/20{m.group(3)}" if mes else ""


def _parse_betfair_csv(csv_content: str) -> dict[str, str]:
    """Mapa {ID O/… : DD/MM/AAAA} das linhas `Bet Settled` / `Voided Bet Refund` do
    extrato. Colocação (`Transaction ID: S/…`) é ignorada — o S/ não casa com o bilhete."""
    mapa: dict[str, str] = {}
    try:
        rows = list(csv.reader(io.StringIO(csv_content or "")))
    except Exception:
        return mapa
    for row in rows:
        if len(row) < 2:
            continue
        hit = _BETFAIR_SETTLED_RE.search(row[1])
        if hit:
            data = _betfair_data(row[0])
            if data:
                mapa[hit.group(1)] = data
    return mapa


def _split_betfair_bilhetes(text: str) -> list[str]:
    """Divide o texto colado da Betfair em blocos de 1 bilhete. Fronteira = a linha
    'ID da aposta: O/…' que FECHA cada bilhete (o header 'Você ganhou R$…' e o tipo
    Simples/Dupla ficam junto do bilhete seguinte, o que é indiferente pro modelo)."""
    blocos: list[str] = []
    atual: list[str] = []
    for ln in (text or "").splitlines():
        atual.append(ln)
        if _BETFAIR_ID_LINE_RE.search(ln):
            bloco = "\n".join(atual).strip()
            if bloco:
                blocos.append(bloco)
            atual = []
    resto = "\n".join(atual).strip()
    if resto:
        blocos.append(resto)
    return blocos


async def _dedup_superbet_text(text: str, dono: str, casa: str = "",
                               parceiro: str = "") -> tuple[str, int]:
    """Espelha `_dedup_betano_text` para a Superbet.

    Remove bilhetes já liquidados no banco + duplicatas dentro do colar. A chave é o
    código do marcador `[Código: ...]`, que vem exato do DOM (sem OCR). Mantém a ordem
    original. Bilhetes sem marcador legível são sempre mantidos.
    """
    blocks = _split_superbet_bilhetes(text)
    if len(blocks) < 2:
        return text, 0

    ids = []
    for b in blocks:
        m = _SUPERBET_ID_RE.search(b)
        ids.append(m.group(1).strip().upper() if m else None)

    # Escopado na CONTA: bilhete que já existe em OUTRA conta do mesmo dono não pode
    # sumir do lote desta aqui (ver a nota em `repository.py`).
    ja_resolvidos = await get_codigos_resolvidos([i for i in ids if i], dono, casa, parceiro)

    mantidos: list[str] = []
    vistos: set[str] = set()
    skipped = 0
    for block, bid in zip(blocks, ids):
        if bid:
            if bid in vistos or bid in ja_resolvidos:
                skipped += 1
                continue
            vistos.add(bid)
        mantidos.append(block)

    if not mantidos:
        return "", skipped
    return "\n\n".join(mantidos), skipped


# ── Instrução ─────────────────────────────────────────────────────────────────

_INSTRUCAO = (
    "Extraia os bilhetes das imagens para TSV no padrão Sharpen.\n"
    "Casa analisada: {casa}\n"
    "Parceiro: {parceiro}\n"
    "Data de referência da captura: {data_referencia}\n"
    "  → Hoje = {data_referencia} · Ontem = dia anterior · Amanhã = dia seguinte\n"
    "  → NUNCA usar o horário de processamento para resolver datas relativas\n"
    "Tipster: SEMPRE VAZIO. Campo vazio = TAB extra.\n\n"
    "LEITURA DAS IMAGENS — REGRAS OBRIGATÓRIAS:\n"
    "  1. Leia cada imagem INTEIRAMENTE, de cima até o final. Os campos financeiros\n"
    "     aparecem APÓS as seleções — leia-os também.\n"
    "     Não gere output de uma imagem antes de terminar de lê-la por completo.\n"
    "  2. Bilhetes podem estar LADO A LADO (layout horizontal) OU empilhados. Em\n"
    "     ambos os casos: CONTE todos os bilhetes distintos visíveis, depois extraia\n"
    "     EXATAMENTE esse número de linhas TSV. Nenhum bilhete pode ser omitido.\n"
    "  3. O ID/código do bilhete é a IDENTIDADE da aposta. Dois bilhetes com IDs\n"
    "     DIFERENTES são SEMPRE apostas distintas → extraia AMBOS, uma linha para cada,\n"
    "     mesmo que TODO o resto seja idêntico (mesmas seleções, odd, stake, data e até\n"
    "     o mesmo confronto). Ex.: duas apostas iguais feitas com 1 min de diferença têm\n"
    "     IDs distintos = 2 linhas. NUNCA funda, agrupe ou descarte um bilhete como\n"
    "     'repetido' quando os IDs diferem. Só trate como o MESMO bilhete se o ID for\n"
    "     idêntico (ex.: o mesmo print aparecendo duas vezes por sobreposição de scroll).\n\n"
    "MÚLTIPLA — 1 bilhete = 1 linha no TSV:\n"
    "  • Aposta (col 6): 'Múltipla' — palavra-chave fixa, NUNCA o texto das seleções.\n"
    "  • Descrição (col 7): TODAS as N seleções concatenadas com ' // '.\n"
    "  • Stake (col 8): valor apostado em R$ — consulte o arquivo da casa para o rótulo exato.\n"
    "  • Odd (col 9): multiplicador — consulte o arquivo da casa para o rótulo exato.\n"
    "  • Esporte (regra de Múltiplos, MASTER_ESPORTES §2): 'Múltiplos' quando houver mistura\n"
    "     de esportes OU acumulada de 3+ confrontos [A v B] DIFERENTES entre as pernas (mesmo\n"
    "     sendo tudo do MESMO esporte, ex.: 3 jogos de Futebol → 'Múltiplos'). NÃO usar\n"
    "     'Múltiplos' em 1–2 seleções, nem em bet builder (MESMO confronto em todas as pernas,\n"
    "     qualquer nº de mercados) → nesses casos, o esporte do jogo.\n\n"
    "RESULTADO — LEITURA OBRIGATÓRIA ANTES DA ODD:\n"
    "  Leia o RÓTULO/STATUS do bilhete ANTES de ler qualquer campo financeiro.\n"
    "  'Perdida' / 'Perdido' → resultado = L. ENCERRE aqui: não leia RO, não calcule RO ÷ Stake.\n"
    "  'Anulado' / 'Void' / 'Reembolso' → resultado = V. Use odd exibida.\n"
    "  'Ganha' / 'Ganho' / verde com Retorno REALIZADO > 0 → resultado = W.\n"
    "  ⚠️ ABERTA / NÃO LIQUIDADA → coluna Resultado VAZIA (TAB extra), JAMAIS W/L/V:\n"
    "     status 'em aberto', 'não liquidado', 'a conferir', 'aguardando', 'pendente', 'open'\n"
    "     — OU retorno rotulado como POTENCIAL/possível (= Stake × Odd, ainda NÃO realizado).\n"
    "     Retorno potencial NUNCA decide W: um bilhete aberto tem retorno potencial > 0 e mesmo\n"
    "     assim fica SEM resultado (fora do P/L). Use a odd exibida na coluna Odd. Só existe\n"
    "     W/L/V quando o bilhete está LIQUIDADO — nunca chute o resultado de uma aposta aberta.\n"
    "  ⚠️ ALERTA OCR: 'R$0,00' pode ser lido erroneamente como 'R50' ou 'R$50' ($ confundido com 5).\n"
    "     Se rótulo = 'Perdida', o RO real é sempre R$0,00 — qualquer leitura de RO > 0 é erro de OCR.\n\n"
    "ODD — REGRAS INVIOLÁVEIS (aplicar em ordem):\n"
    "  1. W (sem rótulo 'Perdida', RO > 0) → Odd = Retorno Obtido ÷ Stake.\n"
    "     Boost incluído no retorno: use o retorno final, ignore o campo de odd.\n"
    "  2. L (rótulo 'Perdida') → Odd = odd combinada exibida no bilhete.\n"
    "     Se a casa NÃO exibe odd combinada (ex.: Betano múltiplas, só odds por perna)\n"
    "     → Odd = produto das odds das seleções. NUNCA calcule RO ÷ Stake (RO = R$0,00 em 'Perdida').\n"
    "  3. V (void/reembolso) → Odd = odd combinada do bilhete (ou produto das pernas se não exibida).\n"
    "  PRECISÃO (INQUEBRÁVEL): exata, SEM arredondamento, JAMAIS truncar para 2 casas.\n"
    "     Use quantas casas decimais forem necessárias (máx. 12). NUNCA reticências (... ou …).\n"
    "     Ex: 1,90917218543046 · 8,580978 · 75,26066666666666\n"
    "  SEPARADOR DECIMAL (INQUEBRÁVEL): odd SEMPRE com VÍRGULA, JAMAIS com ponto.\n"
    "     Todo cálculo (÷ ou ×) produz resultado com ponto — CONVERTA o ponto em vírgula ANTES de escrever.\n"
    "     CORRETO: 75,26066666666666 · 127,672839    ERRADO: 75.26066666666666 · 127.672839\n"
    "     Motivo: a planilha (pt-BR) lê o ponto como separador de milhar e corrompe a odd "
    "(8.580978 vira 8.580.978).\n\n"
    "COLUNAS — NUNCA INVERTER:\n"
    "  Col 6 (Aposta)    = categoria CURTA ('Múltipla', 'ML', 'Gols'...) — NUNCA o texto das seleções\n"
    "  Col 7 (Descrição) = texto LONGO das seleções\n"
    "  Col 8 (Stake)     = valor monetário apostado (ex: 200,00) — NUNCA a odd\n"
    "  Col 9 (Odd)       = multiplicador/cotação (ex: 37,86) — NUNCA o valor apostado\n\n"
    "Responda EXATAMENTE neste formato:\n\n"
    "```tsv\n"
    "Data\tEsporte\tTipster\tCasa\tParceiro\tAposta\tDescrição\tStake\tOdd\tResultado\tCódigo\n"
    "[uma linha por bilhete]\n"
    "```\n\n"
    "Código (11ª coluna, sempre presente): ID/código do bilhete (ex: '890J-QD71FJ').\n"
    "Se não houver ID visível: TAB extra ao final. Nunca omita a coluna.\n\n"
    "## Notas Críticas\n"
    "Somente se houver campo genuinamente ambíguo, dado faltante ou decisão não óbvia "
    "nestes bilhetes de {casa}. Máximo 5 itens concisos.\n"
    "Se nenhum: escreva apenas a palavra Nenhuma."
)


# ── Helpers de paralelismo ────────────────────────────────────────────────────

def _build_chunks(base_content: list[dict], instrucao_block: dict, casa_key: str = "") -> list[list[dict]]:
    """
    Divide base_content em chunks para processamento paralelo.
    Cada chunk recebe instrucao_block no final.
    Retorna lista com 1 elemento quando não vale paralelizar.
    """
    images = [b for b in base_content if b.get("type") == "image"]
    texts  = [b for b in base_content if b.get("type") == "text"]

    # Caso 1: múltiplas imagens → divide em chunks pequenos (_IMGS_POR_CHUNK páginas
    # cada). Chunk enxuto = resposta rápida; a concorrência é limitada pelo semáforo
    # (_MAX_CONCURRENT), então muitos chunks NÃO viram muitos requests simultâneos.
    # Antes o teto era 4 chunks → 50 páginas viravam 4 chunks de ~13 páginas, lentos
    # demais, e a extração estourava o timeout de borda (stream cortado sem "done").
    if len(images) >= 2:
        size = max(1, _IMGS_POR_CHUNK)
        chunks = [images[i:i+size] + [instrucao_block] for i in range(0, len(images), size)]
        if len(chunks) > 1:
            return chunks
        # 1 só chunk (≤ _IMGS_POR_CHUNK imagens) → deixa cair no sequencial (return final)

    # Caso 2: só texto → divide por blocos de apostas
    if not images and texts:
        full_text = "\n\n".join(b["text"] for b in texts)
        # CSV+texto (Betfair): a IA faz o join bilhete↔extrato pelo ID `O/…`. Vai numa
        # ÚNICA chamada sequencial (atômica). NÃO fatiar duplicando o CSV por chunk: em
        # paralelo isso manda o extrato inteiro 4× ao mesmo tempo (pesado) e, se um chunk
        # falha, o modo paralelo descarta os bilhetes dele EM SILÊNCIO (perda parcial).
        # O "network error" de conta muito grande é problema separado — a resolver com
        # filtragem do CSV por ID do bilhete (chunk pequeno), não com CSV duplicado.
        if "DADOS CSV:" in full_text:
            return [base_content + [instrucao_block]]
        if "=== Aposta ID" in full_text:
            blocks = re.split(r'(?=^=== Aposta ID)', full_text, flags=re.MULTILINE)
        elif casa_key.upper() in _CASAS_MARCADOR_CODIGO:
            # Split no marcador [Código: ...] = fronteira do bilhete (exato do DOM/API). Betano
            # (bn_inject), Bet365 (b3_inject) e KTO (kto_inject) emitem o mesmo marcador → todas
            # fatiam igual. A Bet365 antes caía num `[Bilhete Bet365]` inexistente → não dividia,
            # ia tudo num request só; agora fatia e paraleliza como as demais.
            blocks = _SUPERBET_SPLIT_RE.split(full_text)
        elif casa_key.upper() == "BETFAIR":
            # Betfair tem DUAS ingestões:
            #   • CAPTURA (bf_inject, atual): bloco traz o marcador [Código: O/…] + a Data
            #     já resolvida (settledDate do JSON) → fatia como Superbet/Betano.
            #   • LEGADO texto+extrato: sem [Código:], a Data vem do join no código →
            #     fronteira = a linha "ID da aposta: O/…".
            if "[Código:" in full_text:
                blocks = _SUPERBET_SPLIT_RE.split(full_text)
            else:
                blocks = _split_betfair_bilhetes(full_text)
        else:
            blocks = full_text.split("\n\n")
        blocks = [b.strip() for b in blocks if b.strip()]
        if len(blocks) >= 2:
            n = min(_MAX_CHUNKS, len(blocks))
            size = math.ceil(len(blocks) / n)
            return [
                [{"type": "text", "text": "\n\n".join(blocks[i:i+size])}, instrucao_block]
                for i in range(0, len(blocks), size)
            ]

    return [base_content + [instrucao_block]]


def _extract_tsv_rows(text: str) -> list[str]:
    m = re.search(r'```tsv\n(.*?)\n```', text, re.DOTALL)
    if not m:
        return []
    lines = [l for l in m.group(1).split('\n') if l.strip()]
    if lines and lines[0].startswith("Data\t"):
        lines = lines[1:]
    return lines


def _reverse_tsv_rows(text: str) -> str:
    """Inverte a ordem das linhas de dados dentro do bloco ```tsv (preserva header e o
    resto do texto, ex.: ## Notas Críticas). Usado no caminho SEQUENCIAL das casas de feed
    newest-first (Bet365): o modelo emite em ordem natural de leitura; a planilha exige
    mais-antigo→mais-recente. O caminho paralelo já faz isso via
    _combine_parallel_results(reverse_rows=True)."""
    m = re.search(r'```tsv\n(.*?)\n```', text, re.DOTALL)
    if not m:
        return text
    lines = m.group(1).split('\n')
    header: list[str] = []
    if lines and lines[0].startswith("Data\t"):
        header = [lines[0]]
        rows = lines[1:]
    else:
        rows = lines
    rows = [r for r in rows if r.strip()]
    rows.reverse()
    novo = "```tsv\n" + "\n".join(header + rows) + "\n```"
    return text[:m.start()] + novo + text[m.end():]


def _set_tsv_rows(text: str, rows: list[str]) -> str:
    """Troca as linhas de dados do bloco ```tsv preservando header e o resto do texto.
    Espelha `_reverse_tsv_rows`, que faz o mesmo com a lista invertida."""
    m = re.search(r'```tsv\n(.*?)\n```', text, re.DOTALL)
    if not m:
        return text
    linhas = m.group(1).split('\n')
    header = [linhas[0]] if (linhas and linhas[0].startswith("Data\t")) else []
    novo = "```tsv\n" + "\n".join(header + rows) + "\n```"
    return text[:m.start()] + novo + text[m.end():]


def _blocos_dos_codigos(texto: str, codigos: list[str]) -> str:
    """Recorta do texto-fonte só os blocos dos códigos pedidos, na ordem do texto.

    Fronteira de bloco = o mesmo marcador que `_build_chunks` usa para fatiar
    (`[Código: …]` / `=== Aposta ID`). Cada bloco fica INTEIRO — o modelo relê o
    bilhete completo, não um fragmento."""
    if "=== Aposta ID" in texto:
        blocos = re.split(r'(?=^=== Aposta ID)', texto, flags=re.MULTILINE)
    else:
        blocos = _SUPERBET_SPLIT_RE.split(texto)
    alvo = set(codigos)
    escolhidos = []
    for b in blocos:
        if not b.strip():
            continue
        if any(c in b for c in alvo):
            escolhidos.append(b.strip())
    return "\n\n".join(escolhidos)


async def _repescar_faltantes(system: list[dict], texto: str, faltantes: list[str],
                              modelo: str, instrucao_block: dict) -> tuple[list[str], dict]:
    """Reprocessa SÓ os bilhetes que não voltaram, num chunk único.

    Barato por construção: manda apenas os blocos faltantes (o system, que é o caro,
    vem do cache). Qualquer erro aqui é engolido — a repescagem é uma segunda chance,
    nunca pode derrubar a extração que já deu certo."""
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    recorte = _blocos_dos_codigos(texto, faltantes)
    if not recorte:
        return [], tokens
    conteudo = [{"type": "text", "text": recorte}, instrucao_block]
    try:
        acc = ""
        async with _client.messages.stream(
            model=modelo, max_tokens=64000, system=system,
            messages=[{"role": "user", "content": conteudo}],
        ) as stream:
            async for pedaco in stream.text_stream:
                acc += pedaco
            fin = await stream.get_final_message()
        u = fin.usage
        tokens["input"]       += u.input_tokens
        tokens["output"]      += u.output_tokens
        tokens["cache_read"]  += getattr(u, "cache_read_input_tokens", 0)
        tokens["cache_write"] += getattr(u, "cache_creation_input_tokens", 0)
        return _extract_tsv_rows(acc), tokens
    except Exception as e:
        logger.error("repescagem falhou: %s", e)
        return [], tokens


async def _garantir_cobertura(system: list[dict], resultado: str, texto: str | None,
                              modelo: str, instrucao_block: dict | None,
                              reverse_rows: bool) -> tuple[str, dict, dict]:
    """Confere se todo bilhete do texto-fonte virou linha; repesca o que faltou.

    Sessão 179: um chunk que responde SEM o bloco ```tsv contribui com zero linhas e
    `chunks_falhos` (que só conta exceção) não acusa — 39 de 61 bilhetes da Superbet
    sumiram e a tela disse "✓ 22 novo(s)". Aqui a perda é detectada pelo gabarito de
    códigos (determinístico, vem do DOM) e corrigida com uma segunda chamada só do que
    faltou. O que ainda assim não voltar sobe como aviso ALTO para o operador.

    Casa sem marcador de código (Bet365, prints) → `esperados` = 0 → no-op integral.
    Retorna (resultado, cobertura, tokens_extras).
    """
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    cobertura = conferir_cobertura(resultado, texto)
    faltantes = cobertura["faltantes"]
    if not faltantes or not texto or instrucao_block is None:
        return resultado, {**cobertura, "recuperados": 0}, tokens

    logger.warning("cobertura: %d de %d bilhete(s) não voltaram — repescando: %s",
                   len(faltantes), cobertura["esperados"], ", ".join(faltantes[:10]))
    novas, tokens = await _repescar_faltantes(system, texto, faltantes, modelo, instrucao_block)
    if not novas:
        return resultado, {**cobertura, "recuperados": 0}, tokens

    # Ordem: o texto-fonte vem newest-first e a planilha exige oldest→newest — a mesma
    # inversão que o combine já aplicou às linhas originais.
    if reverse_rows:
        novas = list(reversed(novas))
    todas = _extract_tsv_rows(resultado) + novas
    # Reordena pela posição no texto-fonte, mas SÓ quando toda linha tem código
    # conhecido (caso das casas com marcador). Se alguma linha não tem, mantém a ordem
    # de chegada e deixa as repescadas no fim — nunca embaralha o que já estava certo.
    ordem = {c: i for i, c in enumerate(codigos_do_texto(texto))}
    def _pos(linha: str):
        parts = linha.split("\t")
        return ordem.get(parts[10].strip()) if len(parts) > 10 else None
    if all(_pos(l) is not None for l in todas):
        todas.sort(key=lambda l: -_pos(l) if reverse_rows else _pos(l))

    resultado = _set_tsv_rows(resultado, todas)
    cobertura = conferir_cobertura(resultado, texto)
    recuperados = len(faltantes) - len(cobertura["faltantes"])
    logger.info("cobertura: %d recuperado(s) na repescagem · %d ainda faltando",
                recuperados, len(cobertura["faltantes"]))
    return resultado, {**cobertura, "recuperados": recuperados}, tokens


def _apply_betfair_dates(tsv: str, date_map: dict) -> str:
    """Preenche a coluna Data (col 0) de cada linha pelo Código = ID `O/…` (data de
    liquidação do extrato, `date_map`). Perda (que não gera linha no extrato) → interpola
    pela data do bilhete de ID mais próximo (a lista é sequencial por ID). Determinístico;
    substitui o join que o modelo fazia lendo o CSV. Opera dentro do bloco ```tsv."""
    if not date_map:
        return tsv
    m = re.search(r'```tsv\n(.*?)\n```', tsv, re.DOTALL)
    if not m:
        return tsv
    linhas = m.group(1).split('\n')
    header = [linhas[0]] if (linhas and linhas[0].startswith("Data\t")) else []
    corpo = linhas[len(header):]
    rows = [ln.split('\t') for ln in corpo if ln.strip()]

    def _idnum(cells):
        cod = cells[10] if len(cells) > 10 else ""
        mm = re.search(r'O/\d+/(\d+)', cod)
        return int(mm.group(1)) if mm else None

    # 1) data AUTORITATIVA do extrato pelo ID (sobrescreve o que o modelo tenha posto);
    #    marca as demais (perdas, sem linha no extrato) p/ interpolar.
    conhecidos: list[tuple] = []   # (idnum, data) das que casaram no extrato
    faltantes: list = []           # cells sem match (perdas)
    for cells in rows:
        cod = cells[10].strip() if len(cells) > 10 else ""
        if cod in date_map:
            cells[0] = date_map[cod]
            idn = _idnum(cells)
            if idn is not None:
                conhecidos.append((idn, date_map[cod]))
        else:
            faltantes.append(cells)
    # 2) perdas → data do bilhete de ID mais próximo entre os que casaram (sempre
    #    recalculada, nunca confia na data que o modelo eventualmente escreveu).
    if conhecidos:
        for cells in faltantes:
            idn = _idnum(cells)
            if idn is None:
                continue
            cells[0] = min(conhecidos, key=lambda kv: abs(kv[0] - idn))[1]

    novas = ["\t".join(c) for c in rows]
    bloco = "```tsv\n" + "\n".join(header + novas) + "\n```"
    return tsv[:m.start()] + bloco + tsv[m.end():]


def _combine_parallel_results(results: list[tuple[int, str, dict]], reverse_rows: bool = False) -> tuple[str, dict, list[int]]:
    all_rows: list[str] = []
    total_tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    notes: list[str] = []

    for idx, text, tokens in results:
        for k in total_tokens:
            total_tokens[k] += tokens.get(k, 0)
        all_rows.extend(_extract_tsv_rows(text))
        m = re.search(r'## Notas Críticas\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
        if m:
            nota = m.group(1).strip()
            if nota and nota.lower() != "nenhuma":
                notes.append(f"[Chunk {idx + 1}] {nota}")

    # Inversão no nível de LINHA (Superbet texto): o modelo emitiu em ordem de captura
    # (newest-first); a planilha exige oldest→newest. Reverter aqui — ANTES da detecção
    # de scroll — garante que os índices sinalizados batam com a ordem final salva.
    if reverse_rows:
        all_rows.reverse()

    # Detecta suspeitos de sobreposição de scroll (linhas adjacentes, mesma chave invariante)
    # NÃO remove — apenas sinaliza os índices para o frontend mostrar badge azul
    def _scroll_key(row_str: str):
        parts = row_str.split('\t')
        if len(parts) < 9:
            return None
        # Código (11ª coluna) presente e não-vazio → identidade única do bilhete: NUNCA é
        # sobreposição de scroll. Espelha a regra de dedup do banco (código diferente →
        # bilhetes distintos, sempre INSERT). Sem isto, dois bilhetes reais de conteúdo
        # idêntico mas IDs diferentes (ex.: duas apostas iguais feitas com 1 min de
        # diferença na Superbet) eram falsamente marcados como duplicata de scroll.
        codigo = parts[10].strip() if len(parts) > 10 else ""
        if codigo:
            return ("COD", codigo)
        # Sem ID visível (ex.: Bet365): heurística por conteúdo. Normaliza odd para 2
        # casas decimais para absorver diferenças de precisão entre chunks (ex: um chunk lê
        # "1,83" e outro calcula "1,8331168..." — mesma aposta, string diferente).
        try:
            odd_norm = round(float(parts[8].replace(',', '.')), 2)
        except (ValueError, IndexError):
            odd_norm = parts[8]
        return (parts[0], parts[3], parts[4], parts[7], odd_norm)  # data, casa, parceiro, stake, odd(normalizado)

    scroll_overlap_indices: list[int] = []
    prev_key = None
    for i, row in enumerate(all_rows):
        k = _scroll_key(row)
        if k is not None and k == prev_key:
            scroll_overlap_indices.append(i)
        prev_key = k

    if scroll_overlap_indices:
        notes.insert(0,
            f"⚠️ {len(scroll_overlap_indices)} aposta(s) com suspeita de sobreposição de scroll "
            "sinalizadas com badge azul na grade — verifique e delete se necessário."
        )

    tsv_block = f"```tsv\n{_TSV_HEADER}\n" + "\n".join(all_rows) + "\n```"
    notes_section = "\n\n## Notas Críticas\n" + ("\n".join(notes) if notes else "Nenhuma")
    return tsv_block + notes_section, total_tokens, scroll_overlap_indices


# ── Stream functions ──────────────────────────────────────────────────────────

async def _stream_sequential(system: list[dict], content: list[dict], modelo: str, xls_skipped: int, texto: str | None = None,
                             dono: str = "", casa: str = "", n_itens: int = 0, reverse_rows: bool = False,
                             betfair_dates: dict | None = None):
    t_start = time.perf_counter()
    try:
        accumulated = ""
        total_tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
        part = 0
        messages = [{"role": "user", "content": content}]

        while True:
            part += 1
            t_chunk = time.perf_counter()
            if part > 1:
                yield f"data: {json.dumps({'continuation': part})}\n\n"
                messages = [
                    {"role": "user", "content": content},
                    {"role": "assistant", "content": accumulated},
                    {"role": "user", "content": "Continue a extração de onde parou."},
                ]

            q: asyncio.Queue = asyncio.Queue()
            _msgs = messages

            async def _call(_m=_msgs):
                emitted = False   # uma vez que um token foi enviado, não dá pra re-tentar sem duplicar
                attempt = 0
                while True:
                    try:
                        async with _client.messages.stream(
                            model=modelo, max_tokens=64000,
                            system=system, messages=_m,
                        ) as stream:
                            async for chunk in stream.text_stream:
                                emitted = True
                                await q.put(("t", chunk))
                            fin = await stream.get_final_message()
                        await q.put(("done", fin))
                        return
                    except Exception as e:
                        if _is_retryable(e) and not emitted and attempt < _RETRY_MAX:
                            attempt += 1
                            await asyncio.sleep(_RETRY_BASE * (2 ** (attempt - 1)))
                            continue
                        await q.put(("err", e))
                        return

            task = asyncio.create_task(_call())
            msg = None
            try:
                while True:
                    try:
                        kind, val = await asyncio.wait_for(q.get(), timeout=20)
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'keepalive': True})}\n\n"
                        continue
                    if kind == "t":
                        accumulated += val
                        yield f"data: {json.dumps({'t': val})}\n\n"
                    elif kind == "done":
                        msg = val
                        break
                    else:
                        raise val
            finally:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except (asyncio.CancelledError, Exception):
                        pass
                else:
                    await task

            u = msg.usage
            total_tokens["input"]       += u.input_tokens
            total_tokens["output"]      += u.output_tokens
            total_tokens["cache_read"]  += getattr(u, "cache_read_input_tokens", 0)
            total_tokens["cache_write"] += getattr(u, "cache_creation_input_tokens", 0)
            logger.info("seq chunk %d: %.1fs | in=%d out=%d cache_read=%d stop=%s",
                        part, time.perf_counter() - t_chunk,
                        u.input_tokens, u.output_tokens,
                        getattr(u, "cache_read_input_tokens", 0), msg.stop_reason)

            if msg.stop_reason != "max_tokens":
                break

        logger.info("seq total: %.1fs | parts=%d | out=%d",
                    time.perf_counter() - t_start, part, total_tokens["output"])
        # Correção determinística do ID contra o texto colado (o ID é a identidade;
        # a IA não copia números de 18 dígitos com fidelidade). No-op sem texto.
        accumulated, id_fix = corrigir_codigos_tsv(accumulated, texto)
        if id_fix["corrigidos"] or id_fix["incertos"]:
            logger.info("seq id-fix: corrigidos=%d incertos=%d", id_fix["corrigidos"], id_fix["incertos"])
        # Feed newest-first (Bet365) num único chunk: inverte as linhas p/ oldest→newest,
        # espelhando o que o paralelo faz. O modelo emitiu em ordem natural de leitura.
        if reverse_rows:
            accumulated = _reverse_tsv_rows(accumulated)
        # Cobertura: todo bilhete do texto virou linha? Roda DEPOIS da inversão para as
        # linhas repescadas entrarem na mesma ordem final.
        accumulated, cobertura, tk_extra = await _garantir_cobertura(
            system, accumulated, texto, modelo, content[-1] if content else None, reverse_rows)
        for k in total_tokens:
            total_tokens[k] += tk_extra.get(k, 0)
        # Betfair: preenche a Data pelo ID (join com o extrato, feito no código).
        if betfair_dates:
            accumulated = _apply_betfair_dates(accumulated, betfair_dates)
        # 12ª coluna (estrutura de SISTEMA) — determinística, lida do texto do robô e casada
        # pelo código. POR ÚLTIMO de propósito: depois da repesca de cobertura e da inversão,
        # senão linha nascida ali ficaria sem a coluna, em silêncio.
        accumulated, sis_fix = anexar_sistema_tsv(accumulated, texto)
        if sis_fix["sistemas"]:
            logger.info("seq sistema: %d linha(s) marcada(s) como sistema", sis_fix["sistemas"])
        _fire(registrar_uso(dono, casa, modelo, part, n_itens, total_tokens))
        yield f"data: {json.dumps({'done': True, 'resultado': accumulated, 'stop_reason': msg.stop_reason, 'modelo': modelo, 'xls_skipped': xls_skipped, 'tokens': total_tokens, 'id_fix': id_fix, 'cobertura': cobertura})}\n\n"
    except Exception:
        logger.exception("Erro no stream sequencial")
        yield f"data: {json.dumps({'error': 'Erro ao processar a extração. Tente novamente.'})}\n\n"


async def _stream_parallel(system: list[dict], chunks: list[list[dict]], modelo: str, xls_skipped: int, casa_key: str = "", texto: str | None = None,
                           dono: str = "", casa: str = "", n_itens: int = 0, betfair_dates: dict | None = None):
    n_chunks = len(chunks)
    t_start = time.perf_counter()
    sem = asyncio.Semaphore(_MAX_CONCURRENT)
    result_queue: asyncio.Queue = asyncio.Queue()

    async def _call_chunk(idx: int, chunk_content: list[dict]):
        async with sem:
            t0 = time.perf_counter()
            accumulated = ""
            tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
            try:
                messages = [{"role": "user", "content": chunk_content}]
                while True:
                    # Retry com backoff por tentativa: acumula em buffer local e só
                    # comita em `accumulated` no sucesso (evita duplicar em re-tentativa).
                    attempt = 0
                    while True:
                        attempt_text = ""
                        try:
                            async with _client.messages.stream(
                                model=modelo, max_tokens=64000,
                                system=system, messages=messages,
                            ) as stream:
                                async for chunk in stream.text_stream:
                                    attempt_text += chunk
                                fin = await stream.get_final_message()
                            break
                        except Exception as e:
                            if _is_retryable(e) and not attempt_text and attempt < _RETRY_MAX:
                                attempt += 1
                                logger.warning("par chunk %d/%d retry %d (%s)",
                                               idx + 1, n_chunks, attempt, type(e).__name__)
                                await asyncio.sleep(_RETRY_BASE * (2 ** (attempt - 1)))
                                continue
                            raise
                    accumulated += attempt_text

                    u = fin.usage
                    tokens["input"]       += u.input_tokens
                    tokens["output"]      += u.output_tokens
                    tokens["cache_read"]  += getattr(u, "cache_read_input_tokens", 0)
                    tokens["cache_write"] += getattr(u, "cache_creation_input_tokens", 0)

                    if fin.stop_reason != "max_tokens":
                        break
                    messages = [
                        {"role": "user", "content": chunk_content},
                        {"role": "assistant", "content": accumulated},
                        {"role": "user", "content": "Continue a extração de onde parou."},
                    ]

                logger.info("par chunk %d/%d: %.1fs | out=%d",
                            idx + 1, n_chunks, time.perf_counter() - t0, tokens["output"])
                await result_queue.put((idx, accumulated, tokens, None))
            except Exception as e:
                logger.error("par chunk %d/%d erro: %s", idx + 1, n_chunks, e)
                await result_queue.put((idx, "", tokens, e))

    tasks = [asyncio.create_task(_call_chunk(i, chunks[i])) for i in range(n_chunks)]
    completed = []
    chunks_falhos = 0   # chunk que falhou = bilhetes daquele pedaço NÃO extraídos (aviso visível)

    try:
        for _ in range(n_chunks):
            while True:
                try:
                    idx, text, tokens, err = await asyncio.wait_for(result_queue.get(), timeout=20)
                    break
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'keepalive': True})}\n\n"
            if err:
                logger.error("par chunk %d falhou (continuando): %s", idx + 1, err)
                completed.append((idx, "", tokens))
                chunks_falhos += 1
            else:
                completed.append((idx, text, tokens))
            yield f"data: {json.dumps({'chunk_progress': idx + 1, 'of': n_chunks})}\n\n"
    except Exception:
        logger.exception("Erro no stream paralelo")
        await asyncio.gather(*tasks, return_exceptions=True)
        yield f"data: {json.dumps({'error': 'Erro ao processar a extração. Tente novamente.'})}\n\n"
        return

    await asyncio.gather(*tasks, return_exceptions=True)
    try:
        # Regras de ordenação por casa (a grade exibe o último inserido no topo →
        # p/ a bet mais nova ficar no topo, o TSV tem de ser salvo do mais ANTIGO p/ o
        # mais novo, i.e. inverter quando a entrada vem newest-first):
        # - Pinnacle XLS: texto pré-invertido pelo parser → chunk 0 = mais antigo → reverse=False
        # - Superbet PRINT: usuário cola na ordem certa → reverse=False
        # - Superbet TEXTO (scanner) e todo o resto: entrada newest-first → reverse=True
        is_xls_mode = any(
            isinstance(b, dict) and b.get("type") == "text" and "=== Aposta ID" in b.get("text", "")
            for b in chunks[0]
        )
        superbet_print = casa_key.upper() == "SUPERBET" and any(
            isinstance(b, dict) and b.get("type") == "image" for b in chunks[0]
        )
        # Casas de feed newest-first (Bet365, Superbet-texto): o modelo emite em ordem de
        # CAPTURA/leitura natural (§2 "não inverter"). A inversão p/ oldest→newest tem de
        # ser no nível de LINHA, não de chunk: com >_MAX_CHUNKS bilhetes os chunks têm 2+
        # cada e inverter só a ORDEM DOS CHUNKS embaralha em blocos (o bug de ordem que a
        # Bet365 apresentava — ex.: 6 bilhetes T1..T6 saíam T5,T6,T3,T4,T1,T2). Inverter as
        # LINHAS finais é determinístico e não depende de o modelo obedecer a instrução.
        superbet_text = casa_key.upper() == "SUPERBET" and not superbet_print
        # Betfair (texto dos bilhetes em ordem da Fonte A, newest-first) entra no reverse
        # por LINHA como a Bet365 — agora que é paralela, não dá p/ depender do modelo.
        reverse_rows_casa = casa_key.upper() in ("BET365", "BETANO", "BETFAIR") or superbet_text
        if reverse_rows_casa:
            completed.sort(key=lambda x: x[0])   # ordem de captura (idx crescente)
            resultado, total_tokens, scroll_overlap_indices = _combine_parallel_results(completed, reverse_rows=True)
        else:
            reverse_chunks = not (is_xls_mode or superbet_print)
            completed.sort(key=lambda x: x[0], reverse=reverse_chunks)
            resultado, total_tokens, scroll_overlap_indices = _combine_parallel_results(completed)
        logger.info("par total: %.1fs | chunks=%d | out=%d",
                    time.perf_counter() - t_start, n_chunks, total_tokens["output"])
        # Correção determinística do ID contra o texto colado (ver nota no seq).
        resultado, id_fix = corrigir_codigos_tsv(resultado, texto)
        if id_fix["corrigidos"] or id_fix["incertos"]:
            logger.info("par id-fix: corrigidos=%d incertos=%d", id_fix["corrigidos"], id_fix["incertos"])
        # Cobertura: chunk que responde sem o bloco ```tsv some em silêncio (o
        # `chunks_falhos` só conta exceção). Confere pelo gabarito de códigos e repesca.
        resultado, cobertura, tk_extra = await _garantir_cobertura(
            system, resultado, texto, modelo,
            chunks[0][-1] if chunks and chunks[0] else None, reverse_rows_casa)
        for k in total_tokens:
            total_tokens[k] += tk_extra.get(k, 0)
        if cobertura.get("recuperados"):
            # A lista de linhas mudou → os índices de sobreposição de scroll não valem
            # mais. São só um badge azul de dica; descartar é seguro (e casa com código
            # nunca é marcada como sobreposição — ver `_scroll_key`).
            scroll_overlap_indices = []
        # Betfair: preenche a Data pelo ID (join com o extrato, feito no código).
        if betfair_dates:
            resultado = _apply_betfair_dates(resultado, betfair_dates)
        # 12ª coluna (estrutura de SISTEMA) — ver nota no caminho sequencial.
        resultado, sis_fix = anexar_sistema_tsv(resultado, texto)
        if sis_fix["sistemas"]:
            logger.info("par sistema: %d linha(s) marcada(s) como sistema", sis_fix["sistemas"])
        _fire(registrar_uso(dono, casa, modelo, n_chunks, n_itens, total_tokens))
        yield f"data: {json.dumps({'done': True, 'resultado': resultado, 'stop_reason': 'end_turn', 'modelo': modelo, 'xls_skipped': xls_skipped, 'tokens': total_tokens, 'scroll_overlap_indices': scroll_overlap_indices, 'id_fix': id_fix, 'chunks_falhos': chunks_falhos, 'cobertura': cobertura})}\n\n"
    except Exception:
        logger.exception("par-final error")
        yield f"data: {json.dumps({'error': 'Erro ao consolidar a extração. Tente novamente.'})}\n\n"


# ── Rotas ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root(request: Request):
    # Sem sessão válida → tela de login.
    if not usuario_do_request(request):
        return RedirectResponse("/login", status_code=303)
    content = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/app")
async def app_shell(request: Request):
    # Casca única (Fatia 2): sidebar persistente + Planilhador e Dashboard em iframes.
    # Porta de entrada padrão; '/' e '/dashboard/' redirecionam pra cá quando abertos
    # fora de um iframe (ver os scripts de "embedded" nos dois apps).
    if not usuario_do_request(request):
        return RedirectResponse("/login", status_code=303)
    content = (Path(__file__).parent / "static" / "app.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/inicio")
async def inicio_page(request: Request):
    # Home pós-login (SPEC "Pagina Inicio"): carregada como iframe da casca (/app).
    # Todos os números vêm dos mesmos endpoints dos dashboards (/dashboard/data,
    # /bilhetes, /parceiros, /incompletos) + histórico RAIO-X em localStorage.
    if not usuario_do_request(request):
        return RedirectResponse("/login", status_code=303)
    content = (Path(__file__).parent / "static" / "inicio.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


# ── Autenticação ──────────────────────────────────────────────────────────────

@app.get("/login")
async def login_page(request: Request):
    # Já logado → vai direto para a casca única.
    if usuario_do_request(request):
        return RedirectResponse("/app", status_code=303)
    content = (Path(__file__).parent / "static" / "login.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/privacidade")
async def privacidade_page():
    # Pública (sem login): política de privacidade da extensão SharpenUp, exigida pela
    # Chrome Web Store. URL estável p/ o formulário de privacidade da loja.
    content = (Path(__file__).parent / "static" / "privacidade.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache"})


# ── Extensão SharpenUp: versão, página de download e .zip ─────────────────────
# A extensão NÃO está na Chrome Web Store (rejeitada pela política de jogos de azar)
# e é instalada como "unpacked" — que não tem auto-update. A distribuição é um link
# fixo (sharpen.bet/extensao) que serve SEMPRE a última versão + detecção de quem
# está velho (a extensão reporta a própria versão nos handshakes de captura).
#
# Fonte ÚNICA da versão publicada = extensor/manifest.json no deploy. Bumpar a
# versão lá é o gesto que faz o sistema detectar e avisar os instalados antigos.
_EXTENSOR_DIR = Path(__file__).parent.parent / "extensor"


def _versao_extensao() -> str:
    """Versão publicada, lida do manifest da extensão no deploy. '' se ausente/ilegível."""
    try:
        manifest = json.loads((_EXTENSOR_DIR / "manifest.json").read_text(encoding="utf-8"))
        return str(manifest.get("version", "")).strip()
    except Exception:
        return ""


def _versao_tupla(v: str) -> tuple:
    """'0.3.8' -> (0, 3, 8) para comparação numérica. Partes não-numéricas viram 0."""
    partes = []
    for p in (v or "").split("."):
        try:
            partes.append(int(p))
        except ValueError:
            partes.append(0)
    return tuple(partes)


def versao_desatualizada(v_ext: str) -> bool:
    """True se a versão instalada é menor que a publicada — OU ausente (extensão antiga
    que ainda não reporta versão). Sem referência publicada → nunca afirma desatualizado."""
    atual = _versao_extensao()
    if not atual:
        return False
    if not (v_ext or "").strip():
        return True
    return _versao_tupla(v_ext) < _versao_tupla(atual)


@app.get("/extensao")
async def extensao_page():
    # Pública (sem login): página de instalação/atualização do SharpenUp. É o único
    # canal de distribuição — o link fixo sempre serve a última versão. O botão
    # "Atualizar" do popup abre aqui com ?v=<versão instalada> para mostrar o status.
    content = (Path(__file__).parent / "static" / "extensao.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache"})


@app.get("/extensao/versao")
async def extensao_versao():
    # Versão publicada — a página /extensao e a extensão comparam contra a instalada.
    return {"versao": _versao_extensao()}


@app.get("/extensao/download")
async def extensao_download():
    # .zip da extensão gerado on-the-fly a partir de extensor/ no deploy → é sempre,
    # automaticamente, a versão publicada. O usuário descompacta e faz no navegador
    # "Carregar sem compactação" apontando para a pasta. Sem passo de build manual.
    if not _EXTENSOR_DIR.is_dir():
        raise HTTPException(404, "Pacote da extensão indisponível.")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for caminho in sorted(_EXTENSOR_DIR.rglob("*")):
            if caminho.is_file():
                zf.write(caminho, caminho.relative_to(_EXTENSOR_DIR).as_posix())
    ver = _versao_extensao() or "0"
    nome = f"sharpenup-{ver}.zip"
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


class LoginRequest(BaseModel):
    usuario: str
    senha: str


# Rate limit de login em memória (reseta no reinício). Tolerante: não tranca
# usuário legítimo, só desacelera brute-force dos 2 usuários conhecidos.
_LOGIN_WINDOW = 300        # janela de 5 min
_LOGIN_MAX_FAILS = 10      # falhas permitidas por IP na janela
_login_fails: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    # Atrás do proxy do Railway (1 hop confiável). O cliente PODE forjar o X-Forwarded-For,
    # mas o proxy ANEXA o IP real de quem conectou como ÚLTIMO valor da lista. Pegar o
    # leftmost (o que o cliente alega) deixaria um brute-force trocar a chave de rate-limit
    # a cada tentativa (basta mandar um XFF diferente). Pegamos o ÚLTIMO valor = o IP que
    # o Railway de fato viu — não spoofável pelo cliente.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[-1].strip()
    return request.client.host if request.client else "?"


@app.post("/login")
async def login(body: LoginRequest, request: Request):
    ip = _client_ip(request)
    now = time.time()
    fails = [t for t in _login_fails.get(ip, []) if now - t < _LOGIN_WINDOW]
    if len(fails) >= _LOGIN_MAX_FAILS:
        _login_fails[ip] = fails
        raise HTTPException(429, "Muitas tentativas. Aguarde alguns minutos e tente novamente.")

    usuario = body.usuario.strip()
    veredito = resultado_login(usuario, body.senha)
    if veredito != "ok":
        # Mensagem específica SÓ com a senha certa (resultado_login devolve
        # 'invalido' para senha errada — sem enumeração de contas/status).
        if veredito == "pendente":
            raise HTTPException(403, "Cadastro em análise — você será liberado assim que for aprovado.")
        if veredito == "suspenso":
            raise HTTPException(403, "Conta suspensa. Fale com o administrador.")
        fails.append(now)
        _login_fails[ip] = fails
        await asyncio.sleep(0.5)  # atraso constante desacelera brute-force
        raise HTTPException(401, "Usuário ou senha inválidos.")

    _login_fails.pop(ip, None)  # sucesso limpa o contador do IP
    resp = JSONResponse({"ok": True, "usuario": usuario})
    resp.set_cookie(
        key=COOKIE_NAME,
        value=criar_token(usuario),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return resp


@app.post("/logout")
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(COOKIE_NAME)
    resp.delete_cookie(VER_COMO_COOKIE)   # sai limpo: encerra também o "ver como"
    return resp


# ── Aviso ao admin (canal de SAÍDA do app) ────────────────────────────────────
# O cadastro nascia mudo: a conta ficava `pendente` no /admin e NADA avisava
# ninguém. Na prática o dono só descobria abrindo a tela por acaso — um cadastro
# chegou a esperar 2 dias, e três de um mesmo dia só foram vistos porque alguém
# perguntou "chegou mais alguém?". Tela que depende de ser lembrada não é aviso.
#
# ⚠️ Variáveis PRÓPRIAS, deliberadamente separadas do TELEGRAM_BOT_TOKEN do
# login social: aquela é o interruptor do botão "Entrar com Telegram", e apagá-la
# para desligar o botão NÃO pode calar o aviso de cadastro. Um canal, um
# interruptor. Mesmo fail-safe do resto: sem env var, vira no-op silencioso.
TELEGRAM_ALERTA_TOKEN = os.environ.get("TELEGRAM_ALERTA_TOKEN", "")
TELEGRAM_ALERTA_CHAT_ID = os.environ.get("TELEGRAM_ALERTA_CHAT_ID", "")

# Referência forte às tarefas em voo: o asyncio só guarda weakref das tasks, e
# sem isto o coletor pode matar o aviso no meio do caminho (falha silenciosa e
# intermitente, a pior de diagnosticar).
_tarefas_aviso: set[asyncio.Task] = set()


def _alerta_configurado() -> bool:
    return bool(TELEGRAM_ALERTA_TOKEN and ":" in TELEGRAM_ALERTA_TOKEN and TELEGRAM_ALERTA_CHAT_ID)


async def avisar_admin(texto: str) -> bool:
    """Manda um aviso ao admin pelo Telegram. NUNCA levanta.

    O aviso é efeito colateral de uma ação do usuário (cadastrar-se). Deixar a
    exceção subir trocaria um problema pequeno ("o dono não foi avisado") por um
    grande ("a pessoa não conseguiu se cadastrar porque o Telegram caiu").
    Devolve True só quando o Telegram confirmou a entrega.
    """
    if not _alerta_configurado():
        return False
    try:
        async with httpx.AsyncClient(timeout=8) as cli:
            r = await cli.post(
                f"https://api.telegram.org/bot{TELEGRAM_ALERTA_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_ALERTA_CHAT_ID,
                    "text": texto,
                    "disable_web_page_preview": True,
                },
            )
        r.raise_for_status()
        return True
    except Exception:
        # sem parse_mode no envio: texto cru não tem escaping para errar, e um
        # nome com _ ou * não pode ser o motivo de um aviso não sair.
        logger.exception("aviso admin: envio falhou (a ação do usuário segue normal)")
        return False


def disparar_aviso(texto: str) -> None:
    """Fire-and-forget: o aviso não segura a resposta ao usuário nem por 1s.

    O try/except cobre o AGENDAMENTO, não só o envio: `avisar_admin` já engole
    tudo por dentro, mas se o `create_task` falhasse (loop fechado, por exemplo)
    a exceção subiria pelo `/signup` e derrubaria o cadastro — justamente o que
    esta função existe para impedir. Sem o guard, o aviso vira um jeito NOVO de
    o cadastro falhar.
    """
    if not _alerta_configurado():
        return
    try:
        tarefa = asyncio.create_task(avisar_admin(texto))
        _tarefas_aviso.add(tarefa)
        tarefa.add_done_callback(_tarefas_aviso.discard)
    except Exception:
        logger.exception("aviso admin: agendamento falhou (a ação do usuário segue normal)")


def _texto_cadastro_novo(usuario: str, email: str | None, via: str) -> str:
    return (
        "🔔 Novo cadastro no Sharpen\n\n"
        f"Usuário: {usuario}\n"
        f"E-mail: {email or '—'}\n"
        f"Entrou por: {via}\n\n"
        f"Aprovar em {BASE_URL_PUBLICA}/admin"
    )


# ── Cadastro self-service (Fase 2 — "aberto com aprovação") ───────────────────
# Qualquer um se cadastra; a conta nasce `pendente` e só loga depois que um
# admin aprovar no /admin. Ver docs/PLANO_MULTIUSUARIO_2026.md §Fase 2.

_USUARIO_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.\-]{2,23}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_senha(senha: str) -> str | None:
    """Regra ÚNICA de senha aceitável — cadastro, troca no perfil e redefinição.

    Extraída do `validar_cadastro` na s275, quando a troca de senha virou uma
    segunda porta de entrada para o mesmo campo: com a regra copiada, apertar o
    mínimo num lugar deixaria o outro frouxo em silêncio.
    """
    if len(senha) < 8:
        return "A senha precisa de pelo menos 8 caracteres."
    if len(senha) > 128:
        return "Senha longa demais (máximo 128 caracteres)."
    return None


def validar_email(email: str) -> str | None:
    """Regra única de e-mail — cadastro e troca no perfil."""
    if len(email) > 254 or not _EMAIL_RE.fullmatch(email):
        return "E-mail inválido."
    return None


def validar_cadastro(usuario: str, email: str, senha: str) -> str | None:
    """Valida os campos do cadastro. Retorna a mensagem de erro, ou None se ok.

    O username vira a coluna `dono` de TODAS as tabelas de dados (texto usado
    verbatim no sistema inteiro) — por isso o formato é restrito: 3–24 chars,
    começa com letra, sem espaço/acento (grafia é identidade; ver CLAUDE.md
    "casa é texto").
    """
    if not _USUARIO_RE.fullmatch(usuario):
        return ("Usuário inválido: 3 a 24 caracteres, começando com letra, "
                "só letras, números, ponto, hífen ou _ (sem espaços/acentos).")
    return validar_email(email) or validar_senha(senha)


class SignupRequest(BaseModel):
    usuario: str
    email: str
    senha: str


# Rate limit próprio do cadastro (mais apertado que o do login: criar conta é
# raro; 5/h por IP segura spam de cadastros pendentes sem atrapalhar ninguém).
_SIGNUP_WINDOW = 3600
_SIGNUP_MAX = 5
_signup_hits: dict[str, list[float]] = {}


@app.post("/signup")
async def signup(body: SignupRequest, request: Request):
    ip = _client_ip(request)
    now = time.time()
    hits = [t for t in _signup_hits.get(ip, []) if now - t < _SIGNUP_WINDOW]
    if len(hits) >= _SIGNUP_MAX:
        raise HTTPException(429, "Muitos cadastros deste endereço. Tente novamente mais tarde.")

    usuario = body.usuario.strip()
    email = body.email.strip()
    erro = validar_cadastro(usuario, email, body.senha)
    if erro:
        raise HTTPException(400, erro)

    hits.append(now)
    _signup_hits[ip] = hits
    senha_hash = await asyncio.to_thread(gerar_hash_senha, body.senha)
    conflito = await criar_usuario(usuario, email, senha_hash)
    if conflito == "usuario":
        raise HTTPException(409, "Este nome de usuário já existe.")
    if conflito == "email":
        raise HTTPException(409, "Este e-mail já tem cadastro.")

    # Recarrega o cache JÁ (sem esperar o refresher): o login deste usuário
    # passa a responder "cadastro em análise" imediatamente.
    atualizar_cache_usuarios(await carregar_usuarios())
    logger.info("signup: cadastro pendente criado — usuario=%s email=%s", usuario, email)
    disparar_aviso(_texto_cadastro_novo(usuario, email, "formulário de senha"))
    return {"ok": True, "mensagem": "Cadastro recebido! Sua conta está em análise — você poderá entrar assim que for aprovada."}


# ── Painel de admin (aprovação de cadastros) ──────────────────────────────────

def _exigir_admin(usuario: str) -> None:
    """Gate das rotas /admin/*: papel `admin` na tabela usuarios (via cache)."""
    if not eh_admin(usuario):
        raise HTTPException(403, "Acesso restrito ao administrador.")


@app.get("/admin")
async def admin_page(request: Request):
    # Página fora da casca (/app): só o admin a usa. Não-admin não descobre
    # nada — cai no /app como se a rota não existisse para ele.
    usuario = usuario_do_request(request)
    if not usuario:
        return RedirectResponse("/login", status_code=303)
    if not eh_admin(usuario):
        return RedirectResponse("/app", status_code=303)
    content = (Path(__file__).parent / "static" / "admin.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/admin/usuarios")
async def admin_listar_usuarios(usuario: str = Depends(usuario_atual)):
    _exigir_admin(usuario)
    return {"usuarios": await listar_usuarios(), "eu": usuario}


@app.post("/admin/usuarios/{username}/aprovar")
async def admin_aprovar(username: str, usuario: str = Depends(usuario_atual)):
    """Aprova um cadastro pendente (ou reativa um suspenso) — status='ativo'."""
    _exigir_admin(usuario)
    if not await definir_status_usuario(username, "ativo"):
        raise HTTPException(404, "Usuário não encontrado.")
    atualizar_cache_usuarios(await carregar_usuarios())
    logger.info("admin: %s aprovou/reativou %s", usuario, username)
    return {"ok": True}


@app.post("/admin/usuarios/{username}/suspender")
async def admin_suspender(username: str, usuario: str = Depends(usuario_atual)):
    """Suspende um usuário: login barrado E sessão revogada em ≤60s (C3)."""
    _exigir_admin(usuario)
    if username == usuario:
        raise HTTPException(400, "Não dá para suspender a própria conta de admin.")
    if not await definir_status_usuario(username, "suspenso"):
        raise HTTPException(404, "Usuário não encontrado.")
    atualizar_cache_usuarios(await carregar_usuarios())
    logger.info("admin: %s suspendeu %s", usuario, username)
    return {"ok": True}


class BotHabilitadoRequest(BaseModel):
    habilitado: bool


@app.post("/admin/usuarios/{username}/bot")
async def admin_bot_habilitado(username: str, body: BotHabilitadoRequest,
                               usuario: str = Depends(usuario_atual)):
    """Liga/desliga o planilhamento pelo bot de tipster na base deste usuário.

    É a autorização do token de serviço (s273): sem este flag o `SHARPEN_BOT_TOKEN`
    não escreve nada no dono, mesmo válido. Existir como BOTÃO é o ponto — antes
    disso, pôr um tipster novo no bot exigia guardar a senha dele numa env var e
    subir deploy; agora é aprovar a conta e ligar aqui.

    Só faz sentido em conta ATIVA: o gate de identidade do bot exige 'ativo'
    também, então ligar para um pendente/suspenso não daria acesso nenhum e só
    criaria a impressão de que deu.
    """
    _exigir_admin(usuario)
    if body.habilitado and not usuario_ativo(username):
        raise HTTPException(400, "Aprove a conta antes de liberar o bot.")
    if not await definir_bot_habilitado(username, body.habilitado):
        raise HTTPException(404, "Usuário não encontrado.")
    atualizar_cache_usuarios(await carregar_usuarios())
    logger.info("admin: %s %s o bot para %s", usuario,
                "habilitou" if body.habilitado else "desabilitou", username)
    return {"ok": True, "bot_habilitado": body.habilitado}


# ── Login social (Fase 3 — Google OIDC + Telegram) ────────────────────────────
# FAIL-SAFE por env var: sem credenciais, /auth/metodos responde tudo False, os
# botões nem aparecem no login.html e as rotas dão 404 — deployável dormente.
# Os DOIS fluxos são 100% por redirect de navegador (nenhum script externo — a
# CSP fica intacta) e convergem em _resolver_social → criar_token + cookie, o
# mesmo ponto de sessão do login por senha. Conta desconhecida NUNCA entra
# direto: nasce `pendente` no mesmo funil de aprovação do /signup.
# Ver docs/PLANO_MULTIUSUARIO_2026.md §Fase 3.

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# Base pública dos redirects de OAuth (callback registrado no Google Console).
BASE_URL_PUBLICA = os.environ.get("PUBLIC_BASE_URL", "https://www.sharpen.bet")


def _google_configurado() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def _telegram_configurado() -> bool:
    # O bot_id (metade numérica do token) monta a URL do oauth.telegram.org.
    return bool(TELEGRAM_BOT_TOKEN and ":" in TELEGRAM_BOT_TOKEN)


def derivar_username(base: str, em_uso: set[str]) -> str:
    """Deriva um username válido (mesma régua do validar_cadastro) a partir do
    e-mail/nome vindo do provedor social. Sanitiza para o charset permitido,
    garante 1ª letra e 3–24 chars; colisão (case-insensitive, contra
    usernames_em_uso) ganha sufixo numérico crescente."""
    limpo = re.sub(r"[^A-Za-z0-9_.\-]", "", base or "")
    limpo = re.sub(r"^[^A-Za-z]+", "", limpo)[:24] or "usuario"
    if len(limpo) < 3:
        limpo = (limpo + "000")[:3]
    candidato, i = limpo, 2
    while candidato.lower() in em_uso:
        sufixo = str(i)
        candidato = limpo[: 24 - len(sufixo)] + sufixo
        i += 1
    return candidato


def _claims_do_id_token(id_token: str) -> dict | None:
    """Extrai e valida os claims do id_token da Google.

    A assinatura NÃO é verificada de propósito: o token acabou de chegar da
    própria Google (endpoint /token, TLS + client_secret) — não é um token
    apresentado pelo cliente. Validamos iss, aud (nosso client_id), exp e sub.
    E-mail não-verificado é descartado (nunca casar conta por e-mail que a
    Google não confirmou — vetor clássico de account takeover)."""
    try:
        parte = id_token.split(".")[1]
        parte += "=" * (-len(parte) % 4)
        claims = json.loads(base64.urlsafe_b64decode(parte))
    except Exception:
        return None
    if claims.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
        return None
    if claims.get("aud") != GOOGLE_CLIENT_ID:
        return None
    if int(claims.get("exp", 0)) < time.time():
        return None
    if not claims.get("sub"):
        return None
    if claims.get("email") and not claims.get("email_verified"):
        claims = dict(claims, email=None)
    return claims


def _telegram_dados_validos(dados: dict, bot_token: str, agora: float | None = None) -> bool:
    """Valida o payload do Login do Telegram (spec oficial): HMAC-SHA256 do
    data-check-string (campos ordenados, sem o `hash`) com chave
    SHA256(bot_token), + frescor de `auth_date` ≤ 10 min (payload velho não
    loga — anti-replay)."""
    recebido = dados.get("hash", "")
    if not recebido or not dados.get("id") or not dados.get("auth_date"):
        return False
    pares = sorted(f"{k}={v}" for k, v in dados.items() if k != "hash")
    chave = hashlib.sha256(bot_token.encode()).digest()
    esperado = hmac.new(chave, "\n".join(pares).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(esperado, recebido):
        return False
    try:
        idade = (agora if agora is not None else time.time()) - int(dados["auth_date"])
    except (TypeError, ValueError):
        return False
    return -60 <= idade <= 600  # -60 tolera clock skew


async def _resolver_social(
    *,
    google_sub: str | None = None,
    telegram_id: str | None = None,
    email: str | None = None,
    nome: str | None = None,
) -> tuple[str, str | None]:
    """Converge os dois provedores: acha o usuário pelo vínculo, ou vincula pela
    1ª vez via e-mail verificado, ou cria a conta pendente. Retorna
    (destino_do_redirect, username_para_cookie|None) — cookie só quando ativo."""
    campo, valor = ("google_sub", google_sub) if google_sub else ("telegram_id", telegram_id)
    u = await buscar_usuario_social(campo, valor)
    if u is None and email:
        # 1º login social de uma conta que já existia (e-mail VERIFICADO pela
        # Google — _claims_do_id_token já descartou os não-verificados).
        u = await buscar_usuario_social("email", email)
        if u is not None:
            await vincular_social(u["username"], campo, valor)
            logger.info("social: %s vinculado a %s via e-mail", campo, u["username"])
    if u is None:
        base = (email or "").split("@")[0] or (nome or "")
        username = derivar_username(base, await usernames_em_uso())
        await criar_usuario_social(
            username, email, google_sub=google_sub, telegram_id=telegram_id, nome=nome
        )
        atualizar_cache_usuarios(await carregar_usuarios())
        logger.info("social: cadastro pendente criado via %s — %s", campo, username)
        # Mesmo aviso do /signup: conta pendente nasce nestes DOIS pontos, e
        # cobrir só um recria em silêncio o buraco que este aviso veio fechar.
        disparar_aviso(_texto_cadastro_novo(
            username, email, "Google" if google_sub else "Telegram"))
        return "/login?social=pendente", None
    if u["status"] == "pendente":
        return "/login?social=pendente", None
    if u["status"] != "ativo":
        return "/login?social=suspenso", None
    logger.info("social: login de %s via %s", u["username"], campo)
    return "/app", u["username"]


def _com_cookie_de_sessao(resp: Response, username: str) -> Response:
    resp.set_cookie(
        key=COOKIE_NAME,
        value=criar_token(username),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return resp


@app.get("/auth/metodos")
async def auth_metodos():
    """Diz ao login.html quais botões sociais mostrar (fail-safe por env var)."""
    return {"google": _google_configurado(), "telegram": _telegram_configurado()}


@app.get("/auth/google")
async def auth_google():
    if not _google_configurado():
        raise HTTPException(404, "Login Google não configurado.")
    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{BASE_URL_PUBLICA}/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": criar_token_curto("oauth-google"),
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}", status_code=302)


@app.get("/auth/google/callback")
async def auth_google_callback(code: str = "", state: str = "", error: str = ""):
    if not _google_configurado():
        raise HTTPException(404, "Login Google não configurado.")
    if error or not code or not validar_token_curto(state, "oauth-google"):
        return RedirectResponse("/login?social=erro", status_code=303)
    try:
        async with httpx.AsyncClient(timeout=15) as cli:
            r = await cli.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{BASE_URL_PUBLICA}/auth/google/callback",
                "grant_type": "authorization_code",
            })
        r.raise_for_status()
        claims = _claims_do_id_token(r.json().get("id_token", ""))
    except Exception:
        logger.exception("oauth google: troca de código falhou")
        return RedirectResponse("/login?social=erro", status_code=303)
    if not claims:
        return RedirectResponse("/login?social=erro", status_code=303)
    try:
        destino, username = await _resolver_social(
            google_sub=str(claims["sub"]), email=claims.get("email"), nome=claims.get("name"),
        )
    except Exception:
        logger.exception("oauth google: resolução do usuário falhou")
        return RedirectResponse("/login?social=erro", status_code=303)
    resp = RedirectResponse(destino, status_code=303)
    return _com_cookie_de_sessao(resp, username) if username else resp


@app.get("/auth/telegram/ir")
async def auth_telegram_ir():
    """Manda o navegador para a página de autorização do Telegram (fluxo SEM
    widget embarcado — a CSP do app não abre para scripts externos). O retorno
    vem no fragmento #tgAuthResult da página /auth/telegram/retorno."""
    if not _telegram_configurado():
        raise HTTPException(404, "Login Telegram não configurado.")
    bot_id = TELEGRAM_BOT_TOKEN.split(":", 1)[0]
    params = urlencode({
        "bot_id": bot_id,
        "origin": BASE_URL_PUBLICA,
        "return_to": f"{BASE_URL_PUBLICA}/auth/telegram/retorno",
    })
    return RedirectResponse(f"https://oauth.telegram.org/auth?{params}", status_code=302)


# Página-ponte do retorno do Telegram: o oauth.telegram.org devolve os dados no
# FRAGMENTO da URL (#tgAuthResult=<base64url>), que nunca chega ao servidor —
# este HTML mínimo lê o fragmento e o entrega ao POST /auth/telegram, que aí sim
# valida o HMAC e decide. Sem script externo (CSP intacta).
_TELEGRAM_RETORNO_HTML = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>Entrando… — Sharpen</title></head>
<body style="background:#0A0D12;color:#95A1B0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0">
<p>Concluindo login…</p>
<script>
(async () => {
  // Aceita base64url (-_) E base64 padrão (+/): o alfabeto que o Telegram usa
  // no fragmento não está medido contra o serviço real, e um charset apertado
  // truncaria o payload em silêncio — o usuário só veria "?social=erro".
  const m = location.hash.match(/tgAuthResult=([A-Za-z0-9_+\\/\\-=]+)/);
  if (!m) { location.replace('/login?social=erro'); return; }
  try {
    const b64 = m[1].replace(/-/g, '+').replace(/_/g, '/');
    // ⚠️ UTF-8 é LOAD-BEARING aqui, não estética. `atob` devolve binary string
    // (1 char por BYTE), então JSON.parse(atob(...)) entrega "FernÃ£o" onde o
    // Telegram assinou "Fernão" — o data-check-string muda, o HMAC do servidor
    // deixa de bater e o login morre em 401 para todo nome com acento ou emoji.
    // O sintoma é idêntico ao de token errado / setdomain faltando, então o
    // defeito se disfarça de erro de configuração. Travado em
    // tests/test_login_social.py (ponte + acento).
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const dados = JSON.parse(new TextDecoder().decode(bytes));
    const r = await fetch('/auth/telegram', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    });
    const j = await r.json().catch(() => ({}));
    location.replace(j.destino || '/login?social=erro');
  } catch (_) { location.replace('/login?social=erro'); }
})();
</script></body></html>"""


@app.get("/auth/telegram/retorno")
async def auth_telegram_retorno():
    if not _telegram_configurado():
        raise HTTPException(404, "Login Telegram não configurado.")
    return HTMLResponse(_TELEGRAM_RETORNO_HTML, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.post("/auth/telegram")
async def auth_telegram(request: Request):
    if not _telegram_configurado():
        raise HTTPException(404, "Login Telegram não configurado.")
    try:
        dados = await request.json()
    except Exception:
        raise HTTPException(400, "Payload inválido.")
    if not isinstance(dados, dict) or not _telegram_dados_validos(dados, TELEGRAM_BOT_TOKEN):
        raise HTTPException(401, "Dados de login do Telegram inválidos ou expirados.")
    try:
        destino, username = await _resolver_social(
            telegram_id=str(dados["id"]),
            nome=dados.get("username") or dados.get("first_name"),
        )
    except Exception:
        logger.exception("telegram: resolução do usuário falhou")
        raise HTTPException(500, "Falha ao concluir o login. Tente novamente.")
    resp = JSONResponse({"destino": destino})
    return _com_cookie_de_sessao(resp, username) if username else resp


@app.get("/me")
async def me(request: Request):
    """Identidade da sessão + estado de 'ver como'.

    `usuario` = quem está logado (real). `dono_efetivo` = base sendo visualizada
    (igual a `usuario`, ou um operador). `operadores` = operadores que este
    usuário pode visualizar (vazio para quem não é dono)."""
    real = usuario_atual(request)
    return {
        "usuario": real,
        "dono_efetivo": dono_efetivo(request),
        "operadores": operadores_de(real),
        # Perfil (s275): alimentam o modal "Minha conta". `tem_senha` False =
        # conta só-social, que não tem senha para trocar — o formulário some.
        "email": email_de(real),
        "tem_senha": tem_senha(real),
    }


# ── Minha conta: senha e e-mail do próprio usuário (s275) ────────────────────
# As DUAS rotas usam `usuario_atual` (identidade REAL da sessão) e nunca
# `dono_efetivo`: um operador em "ver como" enxerga a base do supervisor, e se
# a credencial saísse do dono efetivo ele trocaria a SENHA DO SUPERVISOR. É a
# mesma distinção que o /me expõe, e aqui ela é a fronteira de privilégio.

class TrocarSenhaRequest(BaseModel):
    senha_atual: str
    senha_nova: str


class TrocarEmailRequest(BaseModel):
    email: str


# Rate limit da troca de senha: a rota é autenticada, mas confere a senha atual
# — logo é um oráculo para chutá-la a partir de uma sessão roubada. 10/h por IP
# não atrapalha ninguém (trocar senha é raro) e fecha o brute-force.
_SENHA_WINDOW = 3600
_SENHA_MAX = 10
_senha_hits: dict[str, list[float]] = {}


@app.post("/conta/senha")
async def trocar_senha(body: TrocarSenhaRequest, request: Request):
    usuario = usuario_atual(request)
    ip = _client_ip(request)
    now = time.time()
    hits = [t for t in _senha_hits.get(ip, []) if now - t < _SENHA_WINDOW]
    if len(hits) >= _SENHA_MAX:
        raise HTTPException(429, "Muitas tentativas. Aguarde alguns minutos e tente novamente.")

    if not tem_senha(usuario):
        raise HTTPException(400, "Esta conta entra por login social e não tem senha.")
    erro = validar_senha(body.senha_nova)
    if erro:
        raise HTTPException(400, erro)

    # A senha ATUAL é exigida mesmo com sessão válida: o cookie dura 30 dias e
    # pode estar numa máquina emprestada. Sessão prova "entrou um dia", não
    # "é a pessoa agora".
    hits.append(now)
    _senha_hits[ip] = hits
    if not await asyncio.to_thread(verificar_credenciais, usuario, body.senha_atual):
        await asyncio.sleep(0.5)   # mesmo atraso constante do /login
        raise HTTPException(401, "Senha atual incorreta.")
    if body.senha_nova == body.senha_atual:
        raise HTTPException(400, "A senha nova precisa ser diferente da atual.")

    senha_hash = await asyncio.to_thread(gerar_hash_senha, body.senha_nova)
    if not await atualizar_senha_usuario(usuario, senha_hash):
        raise HTTPException(404, "Usuário não encontrado.")
    # Recarga IMEDIATA, sem esperar o refresher de 60s: a impressão do hash no
    # cookie é lida DESTE cache, então sem isto o token novo emitido logo abaixo
    # nasceria inválido e o usuário cairia no /login com a senha certa.
    atualizar_cache_usuarios(await carregar_usuarios())
    _senha_hits.pop(ip, None)      # sucesso limpa o contador do IP
    logger.info("conta: senha trocada — usuario=%s", usuario)

    # Cookie novo com a impressão nova. As OUTRAS sessões deste usuário morrem
    # aqui (é o ponto da fatia): quem trocou a senha continua dentro, quem
    # estava com o cookie antigo — inclusive um roubado — cai na próxima request.
    resp = JSONResponse({"ok": True, "mensagem": "Senha alterada. As outras sessões foram encerradas."})
    resp.set_cookie(
        key=COOKIE_NAME,
        value=criar_token(usuario),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    # O "ver como" também é assinado com a impressão do ALVO e segue válido;
    # só o cookie de sessão precisava ser reemitido.
    return resp


@app.post("/conta/email")
async def trocar_email(body: TrocarEmailRequest, request: Request):
    """Define/troca o e-mail da própria conta.

    Existe para as contas anteriores ao autosserviço (13 das 24 na s275, todas
    sem e-mail): é o que vai permitir a elas recuperar a senha sozinhas quando
    o envio por e-mail subir. Não há verificação de posse ainda — o próprio
    fluxo de recuperação a fará, ao exigir que o link chegue na caixa.
    """
    usuario = usuario_atual(request)
    email = body.email.strip()
    erro = validar_email(email)
    if erro:
        raise HTTPException(400, erro)
    if await atualizar_email_usuario(usuario, email) == "email":
        raise HTTPException(409, "Este e-mail já está em uso por outra conta.")
    atualizar_cache_usuarios(await carregar_usuarios())
    logger.info("conta: e-mail atualizado — usuario=%s", usuario)
    return {"ok": True, "email": email}


class VerComoRequest(BaseModel):
    alvo: str | None = None     # operador a visualizar; vazio/None = voltar a si


@app.post("/ver-como")
async def ver_como(body: VerComoRequest, request: Request):
    """Define (ou limpa) o operador que o dono está visualizando.

    Só donos podem assumir a visão dos próprios operadores (`pode_ver_como`).
    Grava um cookie assinado; as rotas de dados leem o dono efetivo dele."""
    real = usuario_atual(request)
    alvo = (body.alvo or "").strip()
    if not alvo or alvo == real:
        resp = JSONResponse({"ok": True, "dono_efetivo": real})
        resp.delete_cookie(VER_COMO_COOKIE)
        return resp
    if not pode_ver_como(real, alvo):
        raise HTTPException(403, "Sem permissão para visualizar este operador.")
    resp = JSONResponse({"ok": True, "dono_efetivo": alvo})
    resp.set_cookie(
        key=VER_COMO_COOKIE,
        value=criar_token(alvo),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    return resp


@app.get("/casas")
async def listar_casas(dono: str = Depends(dono_efetivo)):
    manuais = {
        _casa_display(p.stem.removeprefix("CASA_"))
        for p in CASAS_DIR.glob("CASA_*.md")
        if p.stem != "CASA_MODELO"
    }
    # inclui casas inativas importadas (têm parceiros/dados, mas não têm manual)
    com_dados = set(await casas_com_parceiros(dono))
    dominios = await get_casas_dominios(dono)
    return {"casas": sorted(manuais | com_dados), "dominios": dominios}


class CasaMetaRequest(BaseModel):
    casa: str
    dominio: str = ""


@app.post("/casas/meta")
async def salvar_casa_meta(body: CasaMetaRequest, dono: str = Depends(dono_efetivo)):
    """Salva o domínio de uma casa (por dono) para o favicon (Fase 2)."""
    await set_casa_dominio(dono, body.casa.strip(), body.dominio.strip())
    return {"ok": True}


@app.get("/uso/tokens")
async def uso_tokens_endpoint(dias: int = 30, dono: str = Depends(usuario_atual)):
    """Resumo de uso/custo de tokens dos últimos `dias`. Admin (`usuarios.role`)
    vê a carteira inteira (todos os donos, com quebra por dono); os demais veem só
    o próprio uso. Base p/ afiar o custo e priorizar parsers determinísticos."""
    dias = max(1, min(365, dias))
    return await uso_resumo(dono, dias, todos=eh_admin(dono))


# ── Ponte de captura (extensão ⇄ dashboard) ───────────────────────────────────
# Modelo de pareamento: o dashboard gera um código curto ligado a (dono, casa,
# parceiro); a extensão troca o código por um token e passa a enviar capturas;
# o dashboard faz poll e injeta na área de colar. Lógica/registro em captura.py.

class ParearRequest(BaseModel):
    casa: str
    parceiro: str = ""


@app.post("/captura/parear")
async def captura_parear(req: ParearRequest, dono: str = Depends(usuario_atual)):
    """Dashboard cria a sessão de pareamento. Usa o dono REAL (dado novo vai para
    quem está logado — mesma regra de /extrair)."""
    casa_key = _display_to_key(req.casa)
    sess = _captura.criar_sessao(dono, _casa_display(casa_key), casa_key, (req.parceiro or "").strip())
    return {"sessao_id": sess.sessao_id, "codigo": sess.codigo, "modo": sess.modo,
            "casa": sess.casa, "parceiro": sess.parceiro}


@app.get("/captura/sessao/{sessao_id}")
async def captura_poll(sessao_id: str, dono: str = Depends(usuario_atual)):
    """Poll do dashboard: estado da conexão + capturas pendentes (entrega única)."""
    sess = _captura.sessao_por_id(sessao_id)
    if not sess or sess.dono != dono:
        raise HTTPException(404, "Sessão de captura não encontrada.")
    pend = _captura.drenar_capturas(sess)
    return {
        "conectado": sess.conectado,
        "modo": sess.modo, "casa": sess.casa, "parceiro": sess.parceiro,
        # Sinal de versão para o extrator marcar "ponte desatualizada". Só afirma
        # desatualizado depois que a extensão conectou (senão o slot recém-criado,
        # ainda sem ponte, apareceria falsamente velho).
        "versao_ext": sess.versao_ext,
        "versao_atual": _versao_extensao(),
        "desatualizada": versao_desatualizada(sess.versao_ext) if sess.conectado else False,
        "capturas": [
            {"id": c.id, "tipo": c.tipo, "media_type": c.media_type, "data": c.data}
            for c in pend
        ],
    }


@app.post("/captura/sessao/{sessao_id}/encerrar")
async def captura_encerrar(sessao_id: str, dono: str = Depends(usuario_atual)):
    sess = _captura.sessao_por_id(sessao_id)
    if sess and sess.dono == dono:
        _captura.encerrar(sessao_id)
    return {"ok": True}


class ConectarRequest(BaseModel):
    codigo: str
    versao: str = ""              # versão da extensão (p/ detectar instalação antiga)


@app.post("/captura/conectar")
async def captura_conectar(req: ConectarRequest):
    """Extensão troca o código curto pelo token de envio + metadados do slot.
    Isenta do guarda CSRF (Origin da casa/extensão); autentica pelo código."""
    sess = _captura.conectar(req.codigo)
    if not sess:
        raise HTTPException(404, "Código inválido ou expirado.")
    _captura.registrar_versao(sess, req.versao)
    return {"token": sess.token_ext, "casa": sess.casa, "parceiro": sess.parceiro,
            "modo": sess.modo, "dono": sess.dono,
            "versao_atual": _versao_extensao(), "desatualizada": versao_desatualizada(req.versao)}


class ValidarRequest(BaseModel):
    token: str
    versao: str = ""              # versão da extensão (p/ detectar instalação antiga)


@app.post("/captura/validar")
async def captura_validar(req: ValidarRequest):
    """Extensão valida o token AO ABRIR o popup: a sessão vive em memória (TTL + some no
    restart do servidor), mas o token fica salvo na extensão → sem isto o popup mostrava
    'conectado' com a sessão já morta. 401 = sessão inexistente/expirada (o popup limpa o
    token órfão e volta a parear). Isenta do guarda CSRF; autentica pelo token."""
    sess = _captura.sessao_por_token(req.token)
    if not sess:
        raise HTTPException(401, "Sessão de captura expirada.")
    _captura.registrar_versao(sess, req.versao)
    return {"ok": True, "casa": sess.casa, "parceiro": sess.parceiro,
            "modo": sess.modo, "dono": sess.dono,
            "versao_atual": _versao_extensao(), "desatualizada": versao_desatualizada(req.versao)}


@app.post("/captura/enviar")
async def captura_enviar(
    token: str = Form(...),
    tipo: str = Form("imagem"),
    texto: Optional[str] = Form(None),
    imagem: Optional[UploadFile] = File(default=None),
    origem: Optional[str] = Form(None),
    versao: str = Form(""),
):
    """Extensão envia uma captura (print ou texto). Autentica pelo token de sessão.
    Isenta do guarda CSRF."""
    sess = _captura.sessao_por_token(token)
    if not sess:
        raise HTTPException(401, "Token de captura inválido ou expirado.")
    _captura.registrar_versao(sess, versao)

    # Amarração casa↔site (backstop do servidor): se a captura veio do site de uma casa
    # CONHECIDA diferente da casa da sessão, rejeita — impede gravar (ex.) Superbet no slot
    # da Betfair, mesmo com o cliente adulterado. Origem desconhecida (casa de print) → passa.
    if origem:
        casa_origem = _captura.casa_de_host(origem)
        # ⚠ Comparação EXATA — só funciona porque cada casa tem UMA chave. Se um dia duas
        # chaves apontarem para o mesmo host (foi o caso da Pitaco na s270, enquanto as
        # grafias `PITACO` e `REIDOPITACO` conviviam), `casa_de_host` devolve sempre a
        # primeira e este `!=` rejeita com 409 quem capturou do site CERTO — erro impossível
        # de entender para o operador. Naquele caso a saída foi unificar a grafia; se
        # reaparecer, a alternativa é uma tabela de equivalência aqui.
        if casa_origem and casa_origem != (sess.casa_key or "").upper():
            raise HTTPException(
                409,
                f"Casa incompatível: a captura veio de {origem}, mas a conexão é "
                f"{sess.casa}. Gere um código de pareamento para a casa certa.",
            )

    if tipo == "texto":
        if not (texto and texto.strip()):
            raise HTTPException(400, "Texto vazio.")
        ok = _captura.adicionar_captura(sess, "texto", "", texto)
    else:
        if imagem is None:
            raise HTTPException(400, "Imagem ausente.")
        ctype = (imagem.content_type or "").lower()
        if ctype not in _ALLOWED_IMG_TYPES:
            raise HTTPException(400, f"Tipo de imagem não suportado: {ctype or 'desconhecido'}.")
        raw = await imagem.read()
        if len(raw) > _MAX_IMG_BYTES:
            raise HTTPException(413, "Imagem excede o limite de 12 MB.")
        ok = _captura.adicionar_captura(
            sess, "imagem", ctype, base64.standard_b64encode(raw).decode())

    if not ok:
        raise HTTPException(429, "Fila de capturas cheia — processe no dashboard antes de enviar mais.")
    return {"ok": True}


def _pdf_para_blocos_imagem(raw: bytes, nome: str) -> list[dict]:
    """Renderiza cada página de um PDF em PNG e devolve blocos de imagem no formato
    do payload da Anthropic (base64). Reaproveita todo o pipeline de imagem: cada
    página vira um "screenshot" como se tivesse sido colado. Import de fitz (PyMuPDF)
    é preguiçoso — se a lib faltar, o erro é claro em vez de derrubar o boot do app.

    Blindagem (uma página ruim NÃO pode derrubar o request com 500):
    - zoom adaptativo: página grande (pôster/export largo) cai de resolução para caber
      em _PDF_MAX_LONG_PX — sem isso o bitmap explode e trava/estoura memória;
    - cada página é renderizada em try/except: página que falha é pulada, não aborta;
    - se NENHUMA página rende, devolve 400 limpo em vez de estourar."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise HTTPException(500, "Suporte a PDF indisponível no servidor (PyMuPDF ausente).")

    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception:
        raise HTTPException(400, f"PDF ilegível ou corrompido: '{nome}'.")

    # PDF com senha: tenta abrir sem senha; se exigir, erro claro (não 500).
    if getattr(doc, "needs_pass", False):
        if not doc.authenticate(""):
            doc.close()
            raise HTTPException(400, f"PDF '{nome}' está protegido por senha — remova a proteção e reenvie.")

    if doc.page_count > _MAX_PDF_PAGES:
        n = doc.page_count
        doc.close()
        raise HTTPException(413, f"PDF '{nome}' tem {n} páginas; máximo de {_MAX_PDF_PAGES} por envio. Divida o extrato em partes menores.")

    blocos: list[dict] = []
    falhas = 0
    try:
        for i in range(doc.page_count):
            try:
                pagina = doc[i]
                rect = pagina.rect
                lado_maior_pt = max(rect.width, rect.height) or 1.0
                # zoom-alvo 2.0x, mas nunca a ponto de o lado maior passar de _PDF_MAX_LONG_PX.
                zoom = min(_PDF_RENDER_ZOOM, _PDF_MAX_LONG_PX / lado_maior_pt)
                zoom = max(zoom, 0.5)  # piso: página gigantesca ainda sai legível
                pix = pagina.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                png = pix.tobytes("png")
                blocos.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.standard_b64encode(png).decode(),
                    },
                })
            except Exception:
                falhas += 1
                logger.exception("pdf '%s': falha ao renderizar página %d (pulada)", nome, i + 1)
    finally:
        doc.close()

    if not blocos:
        raise HTTPException(400, f"Não foi possível renderizar nenhuma página do PDF '{nome}'.")
    if falhas:
        logger.warning("pdf '%s': %d página(s) pulada(s) por erro de renderização", nome, falhas)
    return blocos


@app.post("/extrair")
async def extrair(
    casa: str = Form(...),
    parceiro: str = Form(""),
    modelo: str = Form(DEFAULT_MODEL),
    texto: Optional[str] = Form(None),
    csv_content: Optional[str] = Form(None),
    imagens: list[UploadFile] = File(default=[]),
    pdfs: list[UploadFile] = File(default=[]),
    xls_file: Optional[UploadFile] = File(default=None),
    data_referencia: Optional[str] = Form(None),
    # Criação de dado NOVO usa o dono REAL (usuario_atual), não dono_efetivo: em
    # modo "ver como operador", uma extração nova vai para a base de quem está
    # LOGADO, nunca para a do operador visualizado — evita poluir a base alheia por
    # engano (o cookie de "ver como" dura 30 dias). Gestão de dado existente
    # (deletar/editar/listar) segue em dono_efetivo. Decisão do Feca, sessão 82.
    dono: str = Depends(usuario_atual),
):
    if modelo not in ALLOWED_MODELS:
        raise HTTPException(400, f"Modelo não permitido. Opções: {ALLOWED_MODELS}")

    casa_key = _display_to_key(casa)
    if not casa_key.strip():
        raise HTTPException(400, "Casa não informada.")
    # Modo cego (Fase 2 worldwide): casa sem CASA_*.md NÃO é mais rejeitada —
    # a extração roda só com os masters globais e o sistema aprende pelo uso.
    # (build_system já lida com a ausência do manual.)

    base_content: list[dict] = []

    if len(imagens) > _MAX_IMGS:
        raise HTTPException(413, f"Máximo de {_MAX_IMGS} imagens por envio.")

    total_bytes = 0
    for img in imagens:
        ctype = (img.content_type or "").lower()
        if ctype not in _ALLOWED_IMG_TYPES:
            raise HTTPException(400, f"Tipo de imagem não suportado: {ctype or 'desconhecido'}.")
        raw = await img.read()
        total_bytes += len(raw)
        if len(raw) > _MAX_IMG_BYTES:
            raise HTTPException(413, f"Imagem '{img.filename}' excede o limite de 12 MB.")
        if total_bytes > _MAX_TOTAL_BYTES:
            raise HTTPException(413, "Tamanho total das imagens excede 60 MB.")
        base_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": ctype,
                "data": base64.standard_b64encode(raw).decode(),
            },
        })

    # PDFs → cada página vira um bloco de imagem, no mesmo caminho das colagens.
    # A renderização é CPU-bound (síncrona); roda em thread para NÃO travar o event
    # loop enquanto converte um extrato de muitas páginas (seguraria os outros requests).
    for pdf in pdfs:
        raw = await pdf.read()
        if not raw:
            continue
        if len(raw) > _MAX_PDF_BYTES:
            raise HTTPException(413, f"PDF '{pdf.filename}' excede o limite de 25 MB.")
        blocos = await asyncio.to_thread(_pdf_para_blocos_imagem, raw, pdf.filename or "arquivo.pdf")
        for b in blocos:
            total_bytes += (len(b["source"]["data"]) * 3) // 4  # tamanho aprox. do PNG decodificado
            if total_bytes > _MAX_TOTAL_BYTES:
                raise HTTPException(413, "Tamanho total das imagens excede 60 MB.")
        base_content.extend(blocos)

    # Teto combinado: imagens coladas + páginas de PDF não passam de _MAX_PDF_PAGES
    # (cada uma vira um chunk potencial na extração).
    _n_imgs = sum(1 for b in base_content if b.get("type") == "image")
    if _n_imgs > _MAX_PDF_PAGES:
        raise HTTPException(413, f"Máximo de {_MAX_PDF_PAGES} imagens/páginas por envio (recebidas {_n_imgs}).")

    xls_skipped = 0

    if texto:
        # Betano (texto): pré-dedup por ID antes de chamar o modelo — descarta
        # bilhetes já liquidados no banco e duplicatas de scroll dentro do colar.
        # Betfair via CAPTURA (bf_inject) usa o mesmo marcador [Código: O/…] → entra na
        # pré-dedup. A Bet365 (b3_inject) também emite [Código: BR…] → entra (descarta os já
        # RESOLVIDOS no banco antes de gastar IA; abertos sem código são sempre mantidos). A KTO
        # (kto_inject, API Kambi) emite [Código: <couponRef>] → entra pelo mesmo caminho. O
        # legado texto+extrato (sem [Código:]) fica de fora (é dedupado depois). A lista de
        # casas é a MESMA do chunking (`_CASAS_MARCADOR_CODIGO`) — as duas andam juntas, e
        # mantê-las como tuplas separadas foi o que deixou a Pinnacle fora das duas.
        # Só descarta o que está `resolvida` no banco: bilhete ABERTO segue sendo reprocessado,
        # senão nunca seria atualizado ao liquidar (ver `get_codigos_resolvidos`).
        if casa_key.upper() in _CASAS_MARCADOR_CODIGO or \
           (casa_key.upper() == "BETFAIR" and "[Código:" in texto):
            # Mesmo marcador [Código: ...] → pré-dedup por ID (descarta bilhetes já
            # liquidados no banco + duplicatas de scroll dentro do colar). A Betano migrou
            # p/ ingestão por API (bn_inject) e passou a usar o mesmo marcador das outras.
            # A conta entra no filtro: "já resolvido" passa a valer só NESTA conta. O nome
            # vem do formulário e pode estar velho se a conta foi renomeada no meio do
            # caminho — o pior caso é não pular nada (a IA reprocessa e o UPSERT dedupa),
            # nunca esconder bilhete, que era o modo de falha antigo.
            texto, n_skip = await _dedup_superbet_text(
                texto, dono, _casa_display(casa_key), parceiro)
            xls_skipped += n_skip
        if texto:
            base_content.append({"type": "text", "text": texto})

    betfair_dates: dict | None = None
    if csv_content:
        if casa_key.upper() == "BETFAIR":
            # Join determinístico no CÓDIGO: parseia o extrato → mapa ID→data. O CSV NÃO
            # vai pro modelo (fim do payload gigante + network error); os bilhetes viram
            # texto normal, fatiado/paralelo, e a data é preenchida depois pelo ID.
            betfair_dates = _parse_betfair_csv(csv_content)
            logger.info("betfair: extrato com %d datas (join por ID no codigo)", len(betfair_dates))
        else:
            base_content.append({"type": "text", "text": f"DADOS CSV:\n{csv_content}"})

    if xls_file:
        raw = await xls_file.read()
        if len(raw) > _MAX_XLS_BYTES:
            raise HTTPException(413, "Arquivo XLS excede o limite de 20 MB.")
        xls_text, n_skip = await _parse_xls(raw, dono, _casa_display(casa_key), parceiro)
        xls_skipped += n_skip
        if xls_text:
            base_content.append({"type": "text", "text": xls_text})

    if not base_content:
        if xls_skipped > 0:
            _payload = json.dumps({"done": True, "resultado": "", "modelo": modelo,
                                   "xls_skipped": xls_skipped,
                                   "tokens": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}})
            async def _only_skipped():
                yield f"data: {_payload}\n\n"
            return StreamingResponse(_only_skipped(), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
        raise HTTPException(400, "Envie pelo menos uma imagem ou texto.")

    from datetime import date as _date
    ref = data_referencia or _date.today().strftime("%d/%m/%Y")
    instrucao_block = {
        "type": "text",
        "text": _INSTRUCAO.format(
            casa=_casa_display(casa_key),
            parceiro=parceiro or "(não informado)",
            data_referencia=ref,
        ),
    }

    system = build_system(casa_key)
    chunks = _build_chunks(base_content, instrucao_block, casa_key)
    use_parallel = len(chunks) > 1

    logger.info("extrair: casa=%s modelo=%s imgs=%d texts=%d chunks=%d parallel=%s",
                casa_key, modelo,
                sum(1 for b in base_content if b.get("type") == "image"),
                sum(1 for b in base_content if b.get("type") == "text"),
                len(chunks), use_parallel)

    _casa_disp = _casa_display(casa_key)
    _n_itens = len(base_content)   # imagens + blocos de texto (proxy de itens do lote)
    if use_parallel:
        generator = _stream_parallel(system, chunks, modelo, xls_skipped, casa_key, texto,
                                     dono=dono, casa=_casa_disp, n_itens=_n_itens, betfair_dates=betfair_dates)
    else:
        # Bet365/Betano/Betfair são feed newest-first: no chunk único, o sistema inverte p/
        # oldest→newest (ex.: 1 bilhete só, ou o fallback de texto antigo em bloco único).
        seq_reverse = casa_key.upper() in ("BET365", "BETANO", "BETFAIR")
        generator = _stream_sequential(system, base_content + [instrucao_block], modelo, xls_skipped, texto,
                                       dono=dono, casa=_casa_disp, n_itens=_n_itens, reverse_rows=seq_reverse,
                                       betfair_dates=betfair_dates)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Fase 2: banco de dados ────────────────────────────────────────────────────

class SalvarRequest(BaseModel):
    tsv: str
    confianca: Optional[float] = None
    casa: Optional[str] = None
    parceiro: Optional[str] = None
    # ID da conta (tabela `parceiros`). Quando vem, MANDA sobre casa/parceiro-texto: o
    # nome é lido do banco no instante da gravação. Sem isto, um rename de conta com o
    # lote em voo gravava o nome VELHO (o card carrega uma cópia rasa do parceiro, com o
    # nome congelado no clique) e os bilhetes viravam órfãos — invisíveis em todas as
    # telas, sem erro nenhum (sessão 195, Tivo: 22 bilhetes). Opcional: extensão, import,
    # Polymarket e /bilhetes/manual seguem mandando só o texto.
    parceiro_id: Optional[int] = None
    # Instante do ENVIO (clique em Extrair), ISO 8601 do cliente. Vira o criado_em do
    # lote para o feed respeitar a ordem de envio, e não a de conclusão do processamento
    # (extrações paralelas: a mais lenta salvava por último e furava a fila). Ausente/
    # inválido → fallback NOW() no banco (sync/import/extensão seguem como antes).
    submitted_at: Optional[str] = None


# Criação de dado NOVO → dono REAL (ver nota em /extrair): salva sempre na base de
# quem está logado, mesmo em modo "ver como operador". Decisão do Feca, sessão 82.
@app.post("/salvar")
async def salvar(body: SalvarRequest, dono: str = Depends(usuario_atual_ou_bot),
                 dono_view: str = Depends(dono_efetivo_ou_bot)):
    rows = parse_tsv(body.tsv)
    if not rows:
        raise HTTPException(400, "Nenhuma linha válida encontrada no TSV.")

    # Conta pelo ID = fonte de verdade (ver nota no SalvarRequest). Busca no dono
    # EFETIVO porque é por ele que as contas são listadas ("ver como"); a gravação
    # do bilhete segue no dono REAL, como antes. Sem match, nada muda.
    casa_txt, parceiro_txt = body.casa, body.parceiro
    if body.parceiro_id:
        conta = await get_parceiro(body.parceiro_id, dono_view)
        if conta:
            casa_txt, parceiro_txt = conta["casa"], conta["nome"]
    elif casa_txt:
        # Sem conta pela qual resolver (extensão, import, /salvar direto): pelo menos não
        # deixa nascer uma gêmea por caixa/espaço de uma casa já existente.
        casa_txt = await casa_canonica(casa_txt)

    casa_key = _display_to_key(casa_txt) if casa_txt else None
    for row in rows:
        if casa_key:
            row["casa"] = _casa_display(casa_key)
        if parceiro_txt:
            row["parceiro"] = parceiro_txt
        row["tipster"] = ""

    # Validação de fronteira: grava só as linhas com campo financeiro válido; as
    # malformadas (stake/odd/resultado/data presentes e ilegíveis) voltam à UI para
    # correção, sem bloquear as boas nem contaminar o P/L. Incompleta (campo vazio)
    # NÃO é rejeitada — é aposta aberta/leitura parcial, tratada como aviso.
    rows, rejeitadas = validar_linhas(rows)

    # Converte o instante de envio do cliente em datetime aware. `fromisoformat` de
    # versões antigas não aceita o sufixo 'Z' → normaliza para +00:00. Qualquer falha
    # cai em None (o banco usa NOW()).
    criado_base = None
    if body.submitted_at:
        try:
            criado_base = datetime.fromisoformat(body.submitted_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            criado_base = None

    if rows:
        inseridos, atualizados, ids, alertas, duplicatas = await upsert_bilhetes(
            rows, dono, confianca=body.confianca, criado_base=criado_base,
            coproprietarios=coproprietarios(dono),
        )
    else:
        inseridos, atualizados, ids, alertas, duplicatas = 0, 0, [], [], {}

    for r in rejeitadas:
        detalhe = f" · {r['resumo']}" if r["resumo"] else ""
        alertas.append(
            f"Linha {r['linha']} não salva — {r['erro']} (valor: '{r['valor']}'){detalhe}. "
            "Corrija no bilhete e reenvie."
        )

    arquivados = 0
    if ids and (casa_txt or rows):
        # Usa o MESMO display name com que as linhas foram gravadas (acima), senão
        # o filtro do auto_arquivar não casa. Antes: _casa_display(body.casa.upper())
        # transformava "Bolsa de Aposta" em "Bolsa De Aposta" (D maiúsculo) e o
        # arquivamento silenciosamente não ocorria para casas multi-palavra.
        casa_display = _casa_display(casa_key) if casa_key else rows[0].get("casa", "")
        parceiro_nome = parceiro_txt or (rows[0].get("parceiro", "") if rows else "")
        arquivados = await auto_arquivar(casa_display, parceiro_nome, len(ids), dono)

    # Resumo do rail "Análise IA": confiança (heurística sobre as linhas) + KPIs +
    # notas estruturadas (só problemas reais). Não toca na IA de extração.
    analise = analisar_extracao(rows, duplicatas)

    # Conta em que as linhas REALMENTE caíram. O front compara com a conta ativa e grita
    # quando diverge — antes, "salvei 22" e "a grade voltou 0" conviviam sem ninguém notar.
    gravado_casa = _casa_display(casa_key) if casa_key else (rows[0].get("casa", "") if rows else "")
    gravado_parceiro = parceiro_txt or (rows[0].get("parceiro", "") if rows else "")

    return {"salvos": inseridos + atualizados, "inseridos": inseridos, "atualizados": atualizados,
            "ids": ids, "alertas": alertas, "duplicatas": duplicatas, "arquivados": arquivados,
            "analise": analise, "rejeitados": rejeitadas,
            "casa": gravado_casa, "parceiro": gravado_parceiro}


class PolymarketSyncRequest(BaseModel):
    wallet: str
    parceiro: str


_WALLET_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


@app.post("/polymarket/sync")
async def polymarket_sync(body: PolymarketSyncRequest, dono: str = Depends(usuario_atual)):
    """Sincroniza uma carteira Polymarket via API e salva na grade (casa='Polymarket'):
    Rota de CRIAÇÃO → usa usuario_atual (não dono_efetivo): dado novo vai para a base de
    quem está LOGADO mesmo em modo "ver como" (igual /extrair, /salvar, /bilhetes/manual),
    para não poluir a base do operador visualizado (regra da sessão 82).
    posições RESOLVIDAS (W/L/V) + posições ATIVAS como bilhete ABERTO (resultado vazio,
    sem P/L, até liquidarem). Reusa upsert/auto-arquivar — mesma resposta do /salvar."""
    wallet = (body.wallet or "").strip()
    if not _WALLET_RE.match(wallet):
        raise HTTPException(400, "Carteira inválida — informe um endereço 0x… (42 caracteres).")
    parceiro = (body.parceiro or "").strip()
    if not parceiro:
        raise HTTPException(400, "Selecione um parceiro antes de sincronizar.")

    try:
        resolvidas, ativas = await coletar_tudo(wallet, parceiro)
    except CambioIndisponivel as exc:
        # Mensagem controlada por nós (não vaza internals); 503 = tente de novo depois.
        raise HTTPException(503, str(exc))
    except Exception:
        logger.exception("Falha na coleta Polymarket")
        raise HTTPException(502, "Erro ao consultar a Polymarket. Tente novamente.")

    # Uma posição é OU ativa OU resolvida no mesmo snapshot, mas resolvidas vêm PRIMEIRO e
    # removemos das ativas qualquer código já resolvido: garante que uma ativa processada
    # depois nunca reseta (resultado→'') uma resolvida por coincidência de código no lote.
    cods_resolvidos = {r["codigo_bilhete"] for r in resolvidas if r.get("codigo_bilhete")}
    ativas = [a for a in ativas if a.get("codigo_bilhete") not in cods_resolvidos]
    rows = resolvidas + ativas

    if not rows:
        return {"salvos": 0, "inseridos": 0, "atualizados": 0, "ids": [],
                "alertas": ["Nenhum bilhete encontrado para esta carteira."],
                "duplicatas": {}, "arquivados": 0, "coletados": 0}

    # Carry-over: tipster atribuído a uma ativa ANTES desta feature (via a tabela
    # polymarket_ativos_tipster) acompanha o bilhete. Agora a ativa já é um bilhete aberto
    # com coluna tipster própria; manter o carry-over migra os tipsters legados para
    # `bilhetes` (a tabela é aposentada aos poucos). O upsert preserva tipster não-vazio.
    codigos = [r["codigo_bilhete"] for r in rows if r.get("codigo_bilhete")]
    salvos = await get_ativos_tipster(dono, codigos)
    for r in rows:
        t = salvos.get(r.get("codigo_bilhete", ""))
        if t:
            r["tipster"] = t

    # Mercado que ganhou uma 2ª compra: o código migra de `cid` para `cid__i` e a linha
    # antiga (código cru) some do radar do UPSERT — vira fantasma presa em "aberta".
    # Antes de gravar, herdamos o tipster dela; depois de gravar, ela é removida.
    cids_fatiados = sorted({r["codigo_bilhete"].split("__")[0] for r in rows
                            if "__" in (r.get("codigo_bilhete") or "")})
    if cids_fatiados:
        tipster_cru = await get_tipster_por_codigo(dono, "Polymarket", parceiro, cids_fatiados)
        for r in rows:
            cid = (r.get("codigo_bilhete") or "").split("__")[0]
            if not r.get("tipster") and tipster_cru.get(cid):
                r["tipster"] = tipster_cru[cid]

    inseridos, atualizados, ids, alertas, duplicatas = await upsert_bilhetes(rows, dono, origem="sync")
    # Só agora (upsert concluído) a linha de código cru pode sair: o SQL exige que as
    # fatias irmãs já existam, então um upsert que tenha falhado não apaga nada.
    fantasmas = await remover_bilhetes_supersedidos(dono, "Polymarket", parceiro, cids_fatiados)
    if fantasmas:
        alertas.append(
            f"{len(fantasmas)} linha(s) duplicada(s) removida(s): o mercado ganhou uma "
            "compra nova e a linha antiga ficou órfã do código do bilhete."
        )
    # Tipster migrado da tabela de ativas para `bilhetes`: apaga as linhas correspondentes
    # para não reinjetar (e sobrescrever uma edição da grade) no próximo re-sync.
    if salvos:
        await limpar_ativos_tipster(dono, list(salvos.keys()))
    arquivados = await auto_arquivar("Polymarket", parceiro, len(ids), dono)

    return {"salvos": inseridos + atualizados, "inseridos": inseridos, "atualizados": atualizados,
            "ids": ids, "alertas": alertas, "duplicatas": duplicatas, "arquivados": arquivados,
            "coletados": len(rows)}


@app.get("/polymarket/dashboard")
async def polymarket_dashboard(wallet: str, dono: str = Depends(dono_efetivo)):
    """Estado ao vivo da carteira Polymarket: KPIs (posições ativas, portfólio, cash,
    total) + tabela de posições ativas, com o tipster salvo de cada uma mesclado."""
    wallet = (wallet or "").strip()
    if not _WALLET_RE.match(wallet):
        raise HTTPException(400, "Carteira inválida — informe um endereço 0x… (42 caracteres).")
    try:
        dash = await coletar_dashboard(wallet)
    except Exception as exc:
        logger.exception("Falha no dashboard Polymarket")
        raise HTTPException(502, "Erro ao consultar a Polymarket. Tente novamente.")
    codigos = [a["codigo"] for a in dash["ativas"] if a.get("codigo")]
    salvos = await get_ativos_tipster(dono, codigos)
    for a in dash["ativas"]:
        a["tipster"] = salvos.get(a["codigo"], "")
    return dash


class AtivoTipsterRequest(BaseModel):
    codigo: str
    tipster: str = ""


@app.post("/polymarket/ativo-tipster")
async def polymarket_ativo_tipster(body: AtivoTipsterRequest, dono: str = Depends(dono_efetivo)):
    """Salva o tipster de uma posição ativa (persistido até a aposta resolver e migrar)."""
    codigo = (body.codigo or "").strip()
    if not codigo:
        raise HTTPException(400, "Código da posição ausente.")
    await set_ativo_tipster(dono, codigo, (body.tipster or "").strip())
    return {"ok": True}


@app.get("/eventos")
async def eventos_sse(dono: str = Depends(dono_efetivo)):
    """Canal de tempo real (SSE): avisa "sua base mudou" para a tela recarregar
    sozinha — a casca (/app) assina UMA conexão e propaga ao loadData() dos
    iframes (s241). A fonte é o trigger `trg_bilhetes_base_mudou` no Postgres,
    então extração, captura da extensão, sync, edição, exclusão e até script de
    import contam — sem instrumentar rota por rota.

    O escopo é o MESMO do /dashboard/data: dono efetivo + operadores dele — a
    captura de um operador reflete na tela do supervisor na hora. O evento não
    carrega dado (só o dono que mudou); quem busca o dado é o loadData.
    """
    entrada = _eventos.assinar([dono] + operadores_de(dono))
    fila = entrada[1]

    async def gen():
        try:
            # Handshake: destrava proxies que só liberam o stream após o 1º byte
            # e dá à casca a confirmação de canal aberto.
            yield f"data: {json.dumps({'ok': True})}\n\n"
            while True:
                try:
                    mudou = await asyncio.wait_for(fila.get(), timeout=20)
                except asyncio.TimeoutError:
                    # Keepalive: mantém proxies acordados e faz o servidor
                    # descobrir cliente desconectado (a escrita falha → finally).
                    yield f"data: {json.dumps({'keepalive': True})}\n\n"
                    continue
                # Coalesce: rajada de avisos (lote em vários COMMITs) vira um só.
                while not fila.empty():
                    fila.get_nowait()
                yield f"data: {json.dumps({'base_mudou': mudou})}\n\n"
        finally:
            _eventos.cancelar(entrada)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/dashboard/data")
async def dashboard_data(request: Request, dono: str = Depends(dono_efetivo), refresh: bool = False):
    """Fonte de dados do Betting Dashboard (mesmo contrato do Code.gs/Apps Script),
    montada do Postgres e filtrada pelo dono logado — substitui a planilha. O
    dashboard client-side faz toda a matemática; aqui só servimos o array cru.

    Para um DONO supervisor, o feed é CONSOLIDADO: a base dele + a dos seus
    operadores num só array (cada linha marcada com `operador`); o front soma
    tudo e oferece um filtro por operador. Operador comum vê só a própria base.

    NOTA: esta rota é registrada ANTES do StaticFiles montado em /dashboard (no fim
    do arquivo), então o Starlette a resolve primeiro — /dashboard/data nunca cai
    no servidor de estáticos.
    """
    escopo = [dono] + operadores_de(dono)   # dono + operadores dele (vazio p/ operador)
    # Cada dono do escopo lê da sua fonte: planilha AO VIVO (Apps Script /exec,
    # Fase 1) quando registrada, senão Postgres. O contrato de linha é idêntico
    # nos dois casos (o Code.gs espelha `dashboard_rows`), então o feed sai
    # consolidado e transparente para o front.
    rows: list[dict] = []
    donos_postgres: list[str] = []
    for d in escopo:
        url = planilha_ao_vivo(d)
        if url:
            # refresh=1 (clique manual em "Atualizar dados") força reconstrução
            # ao vivo da planilha; sem isso o botão não fura os caches do feed.
            rows += await dashboard_rows_ao_vivo(d, url, refresh=refresh)
        else:
            donos_postgres.append(d)
    if donos_postgres:
        rows += await dashboard_rows(donos_postgres)
    payload = {
        "ok": True,
        "data": rows,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "operadores": escopo,
        "dono": dono,          # dono efetivo — o front escopa o store de custos por ele
    }
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    # Compressão DIRECIONADA (só esta rota): o feed é um JSON grande (~toda a base) e
    # altamente compressível → gzip corta ~85-90% da transferência, que é o gargalo
    # da 1ª carga sem cache (#17). Não usamos GZipMiddleware global de propósito: ele
    # bufferizaria os streams SSE da extração (keepalive). Aqui é uma resposta única.
    aceita_gzip = "gzip" in request.headers.get("accept-encoding", "").lower()
    if aceita_gzip and len(body) > 1024:
        comprimido = gzip.compress(body, compresslevel=6)
        return Response(
            content=comprimido,
            media_type="application/json",
            headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
        )
    return Response(content=body, media_type="application/json")


@app.get("/exportar.csv")
async def exportar_csv(dono: str = Depends(dono_efetivo)):
    """Backup completo da base do dono: todas as linhas, todas as colunas, em CSV
    (separador ';' + BOM → abre limpo no Excel pt-BR, decimal vírgula preservado)."""
    rows = await export_bilhetes(dono)
    buf = io.StringIO()
    buf.write("﻿")  # BOM p/ Excel reconhecer UTF-8
    if rows:
        campos = list(rows[0].keys())
        w = csv.DictWriter(buf, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else str(v)) for k, v in r.items()})
    from datetime import datetime as _dt
    nome = f"sharpen_base_{dono}_{_dt.now().strftime('%Y-%m-%d_%H%M')}.csv"
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


class DeletarRequest(BaseModel):
    ids: list[int]


@app.delete("/bilhetes")
async def deletar_bilhetes_route(body: DeletarRequest, dono: str = Depends(dono_efetivo_ou_bot)):
    if not body.ids:
        raise HTTPException(400, "Lista de IDs vazia.")
    linhas = await deletar_bilhetes(body.ids, dono)
    # `linhas` volta ao cliente para o undo por toast (Desfazer → POST /bilhetes/restaurar).
    return {"deletados": len(linhas), "linhas": linhas}


@app.delete("/bilhetes/{bilhete_id}")
async def deletar_bilhete_route(bilhete_id: int, dono: str = Depends(dono_efetivo)):
    linhas = await deletar_bilhetes([bilhete_id], dono)
    if not linhas:
        raise HTTPException(404, "Bilhete não encontrado.")
    return {"deletado": True, "linhas": linhas}


class RestaurarRequest(BaseModel):
    linhas: list[dict]


@app.post("/bilhetes/restaurar")
async def restaurar_bilhetes_route(body: RestaurarRequest, dono: str = Depends(dono_efetivo)):
    """Undo da exclusão: re-insere as linhas capturadas no DELETE. `dono` vem da
    sessão (o cliente não injeta), igual ao delete."""
    restaurados = await restaurar_bilhetes(body.linhas, dono)
    return {"restaurados": restaurados}


@app.get("/conta/resumo")
async def resumo_da_conta(
    casa: str, parceiro: str, dono: str = Depends(dono_efetivo)
):
    """KPIs agregados de UMA conta (casa+parceiro), para a faixa no topo do
    extrator: P/L, turnover, apostas, ROI, win rate, duração e dias ativos.
    Números batem com o card da casa no Dashboard (mesmos filtros)."""
    return await resumo_conta(dono, casa, parceiro)


@app.get("/incompletos")
async def listar_incompletos(dono: str = Depends(dono_efetivo)):
    """Contagem de bilhetes INCOMPLETOS por parceiro/casa, para os badges da sidebar:
    azul = sem tipster; âmbar = abertos (sem resultado)."""
    linhas = await contar_incompletos(dono)
    por_parceiro = [
        {"casa": r["casa"], "parceiro": r["parceiro"],
         "sem_tipster": r["sem_tipster"], "abertas": r["abertas"]}
        for r in linhas
    ]
    por_casa_tipster: dict[str, int] = {}
    por_casa_aberta: dict[str, int] = {}
    for r in linhas:
        por_casa_tipster[r["casa"]] = por_casa_tipster.get(r["casa"], 0) + r["sem_tipster"]
        por_casa_aberta[r["casa"]] = por_casa_aberta.get(r["casa"], 0) + r["abertas"]
    return {
        "por_parceiro": por_parceiro,
        "por_casa_tipster": por_casa_tipster,
        "por_casa_aberta": por_casa_aberta,
    }


@app.get("/pendencias")
async def listar_pendencias(
    casa: Optional[str] = None,
    parceiro: Optional[str] = None,
    archived: str = "all",
    dono: str = Depends(dono_efetivo),
):
    """Contadores dos chips de pendência da conta ativa (sem odd / sem stake /
    categoria a confirmar / sem tipster). É a ponte do aviso do RAIO-X, que conta o
    LOTE, para a GRADE, que é paginada: sem isto o usuário sabe que há 4 bilhetes
    sem odd e não tem como achá-los."""
    return await contar_pendencias(
        dono, casa=casa or None, parceiro=parceiro or None, archived=archived,
    )


@app.get("/bilhetes")
async def listar_bilhetes(
    casa: Optional[str] = None,
    parceiro: Optional[str] = None,
    extraction_state: Optional[str] = None,
    archived: str = "false",
    order: str = "asc",
    limit: int = 500,
    offset: int = 0,
    pendencia: Optional[str] = None,
    dono: str = Depends(dono_efetivo),
):
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)
    rows = await list_bilhetes(
        dono,
        casa=casa or None,
        parceiro=parceiro or None,
        extraction_state=extraction_state or None,
        archived=archived,
        limit=limit,
        offset=offset,
        order=order,
        pendencia=pendencia or None,
    )
    total = await contar_bilhetes(
        dono,
        casa=casa or None,
        parceiro=parceiro or None,
        extraction_state=extraction_state or None,
        archived=archived,
        pendencia=pendencia or None,
    )
    arquivados_count = 0
    if archived != "true" and (casa or parceiro):
        arquivados_count = await contar_arquivados(casa or "", parceiro or "", dono)
    return {
        "bilhetes": rows, "total": total, "arquivados": arquivados_count,
        "limit": limit, "offset": offset,
    }


class _BilheteFinanceiroBase(BaseModel):
    """Validação de fronteira dos campos financeiros (stake/odd/resultado/data) nas
    rotas de escrita: barra valor inválido ANTES de tocar o banco, para não
    contaminar o P/L derivado (odd×stake). Vazio/ausente é permitido (campo
    opcional ou "limpar"); quando preenchido, tem de ser válido. Erro → 422.
    `check_fields=False`: os campos vivem nas subclasses."""

    @field_validator("stake", "odd", check_fields=False)
    @classmethod
    def _valida_monetario(cls, v, info):
        if not valor_monetario_valido(v):
            raise ValueError(f"{info.field_name} inválido: informe um número maior que zero.")
        return v

    @field_validator("resultado", check_fields=False)
    @classmethod
    def _valida_resultado(cls, v):
        if not resultado_valido(v):
            raise ValueError("resultado deve ser W, L, V, HW, HL ou vazio.")
        return v

    @field_validator("data", check_fields=False)
    @classmethod
    def _valida_data(cls, v):
        if not data_valida(v):
            raise ValueError("data inválida: use DD/MM/AAAA.")
        return v


class BilheteManualRequest(_BilheteFinanceiroBase):
    casa: str
    parceiro: str
    data: Optional[str] = ""
    esporte: Optional[str] = ""
    tipster: Optional[str] = ""
    aposta: Optional[str] = ""
    descricao: Optional[str] = ""
    stake: Optional[str] = ""
    odd: Optional[str] = ""
    resultado: Optional[str] = ""


# Criação de dado NOVO → dono REAL (mesma regra de /extrair e /salvar, sessão 82):
# a aposta manual vai sempre para a base de quem está logado.
@app.post("/bilhetes/manual")
async def inserir_bilhete_manual(body: BilheteManualRequest, dono: str = Depends(usuario_atual)):
    if not (body.casa or "").strip() or not (body.parceiro or "").strip():
        raise HTTPException(400, "Casa e parceiro são obrigatórios.")
    resultado = (body.resultado or "").strip().upper()
    if resultado and resultado not in {"W", "L", "V", "HW", "HL"}:
        raise HTTPException(400, "Resultado deve ser W, L, V, HW, HL ou vazio.")
    row = {
        "casa": body.casa.strip(), "parceiro": body.parceiro.strip(),
        "data": (body.data or "").strip(),
        "esporte": (body.esporte or "").strip(),
        "tipster": (body.tipster or "").strip(),
        "aposta": (body.aposta or "").strip(),
        "descricao": (body.descricao or "").strip(),
        "stake": (body.stake or "").strip(),
        "odd": (body.odd or "").strip(),
        "resultado": resultado,
        "codigo_bilhete": "",
    }
    inseridos, atualizados, ids, _alertas, _dup = await upsert_bilhetes(
        [row], dono, origem="manual",
    )
    if not ids:
        raise HTTPException(500, "Não foi possível inserir a aposta.")
    return {"id": ids[0], "inserido": inseridos > 0, "atualizado": atualizados > 0}


class TipsterLoteRequest(BaseModel):
    ids: list[int]
    tipster: str


# Edição de dado existente → dono EFETIVO (mesma regra do PATCH single): atua sobre
# as apostas que estão sendo vistas na grade.
@app.post("/bilhetes/tipster")
async def informar_tipster_lote(body: TipsterLoteRequest, dono: str = Depends(dono_efetivo_ou_bot)):
    if not body.ids:
        raise HTTPException(400, "Nenhuma aposta selecionada.")
    tip = (body.tipster or "").strip()
    if not tip:
        raise HTTPException(400, "Informe o tipster.")
    atualizados = await set_tipster_bulk(body.ids, tip, dono)
    return {"atualizados": atualizados}


@app.get("/tipsters")
async def listar_tipsters(dono: str = Depends(dono_efetivo)):
    return {"tipsters": await list_tipsters(dono)}


@app.get("/esportes")
async def listar_esportes(dono: str = Depends(dono_efetivo)):
    return {"esportes": await list_esportes(dono)}


@app.get("/mercados")
async def listar_mercados(dono: str = Depends(dono_efetivo)):
    """Mercados já usados por este dono, do mais para o menos frequente (com contagem).

    Alimenta o menu de duplo-clique da coluna `Aposta` na grade da Extração — ali o
    cliente só tem a PÁGINA de bilhetes da conta aberta, então a frequência não pode
    ser contada no navegador. O dashboard não consome esta rota de propósito: lá os
    favoritos saem de `DADOS ∪ DADOS_ABERTAS`, que para um supervisor inclui a base
    dos operadores — contar aqui daria um menu que não corresponde à tela.

    O menu COMPLETO (botão ✎) é esta lista ∪ `/taxonomia`, unida no cliente.
    """
    return {"mercados": await list_mercados(dono)}


@app.get("/taxonomia")
async def taxonomia(dono: str = Depends(dono_efetivo)):
    """Esportes e categorias VÁLIDOS, lidos dos MASTERs (`app/taxonomia.py`).

    Complementa `/esportes`, que só devolve o que o dono já apostou: quem ainda não tem
    base precisa dos valores canônicos para preencher o perfil do tipster à mão. A tela
    usa a UNIÃO das duas — o canônico oferece o que ele ainda não apostou, a base
    preserva a grafia herdada de import antigo (`Fórmula 1`, `Esoccer`) que o canônico
    não tem e que os bilhetes dele realmente usam.
    """
    return {"esportes": list(esportes_canonicos()), "categorias": list(categorias_canonicas())}


# ── Fase 4: parceiros persistidos ─────────────────────────────────────────────

class ParceiroCriarRequest(BaseModel):
    casa: str
    nome: str


@app.get("/parceiros")
async def listar_parceiros(casa: Optional[str] = None, arquivados: bool = False,
                           dono: str = Depends(dono_efetivo)):
    rows = await list_parceiros(dono, casa=casa or None, incluir_arquivados=arquivados)
    return {"parceiros": rows}


@app.post("/parceiros")
async def criar_parceiro_route(body: ParceiroCriarRequest, dono: str = Depends(dono_efetivo)):
    casa_key = _display_to_key(body.casa)
    nome = body.nome.strip()
    if not nome:
        raise HTTPException(400, "Nome do parceiro não pode ser vazio.")
    if not casa_key.strip():
        raise HTTPException(400, "Casa não informada.")
    # Casa nova (Fase 2 worldwide): não exige mais CASA_*.md. A casa passa a
    # existir pelo uso (parceiro + bilhetes) e a extração roda em modo cego.
    # A casa NASCE aqui — é o ponto certo para impedir uma gêmea por caixa/espaço de uma
    # casa que já existe ("Pixbet" quando o sistema já tem "PixBet"). Casa realmente nova
    # segue entrando verbatim (ver `casa_canonica`).
    row = await criar_parceiro(await casa_canonica(_casa_display(casa_key)), nome, dono)
    return row


@app.post("/parceiros/{parceiro_id}/arquivar")
async def arquivar_parceiro_route(parceiro_id: int, dono: str = Depends(dono_efetivo)):
    ok = await arquivar_parceiro(parceiro_id, dono)
    if not ok:
        raise HTTPException(404, "Parceiro não encontrado.")
    return {"arquivado": True}


class AtualizarBilheteRequest(_BilheteFinanceiroBase):
    data: Optional[str] = None
    esporte: Optional[str] = None
    tipster: Optional[str] = None
    casa: Optional[str] = None
    parceiro: Optional[str] = None
    aposta: Optional[str] = None
    descricao: Optional[str] = None
    stake: Optional[str] = None
    odd: Optional[str] = None
    resultado: Optional[str] = None
    # Procedência do rótulo de tipster (Fase 0). O front manda 'sugerido' quando vem do
    # botão de auto-atribuição; ausência num set de tipster → 'humano' (default no repo).
    origem_tipster: Optional[str] = None


@app.patch("/bilhetes/{bilhete_id}")
async def atualizar_bilhete_route(bilhete_id: int, body: AtualizarBilheteRequest,
                                  dono: str = Depends(dono_efetivo_ou_bot)):
    campos = {k: v for k, v in body.model_dump().items() if v is not None}
    ok = await atualizar_bilhete(bilhete_id, campos, dono)
    if not ok:
        raise HTTPException(404, "Bilhete não encontrado ou sem campos válidos.")
    # Avisos que só o banco sabe (ver `flags_pos_edicao`): mercado trocado em bilhete sem
    # código duplica na próxima captura; data/odd/stake editados em aposta ainda ABERTA de
    # fonte automática são desfeitos pelo próximo envio do robô. Os dois falham em
    # silêncio — a tela aceita e salva —, então o aviso é na hora, para quem está olhando.
    # Uma consulta só, e apenas quando os campos editados interessam.
    extra = await flags_pos_edicao(bilhete_id, dono, set(campos))
    return {"atualizado": True, **extra}


@app.post("/parceiros/{parceiro_id}/reativar")
async def reativar_parceiro_route(parceiro_id: int, dono: str = Depends(dono_efetivo)):
    ok = await reativar_parceiro(parceiro_id, dono)
    if not ok:
        raise HTTPException(404, "Parceiro não encontrado.")
    return {"arquivado": False}


class ParceiroRenomearRequest(BaseModel):
    nome: str


@app.get("/parceiros/{parceiro_id}/resumo")
async def resumo_parceiro_route(parceiro_id: int, dono: str = Depends(dono_efetivo)):
    """Identidade + nº de apostas da conta. Só o modal de exclusão consome: o número
    que a tela promete apagar tem de vir da mesma consulta que o DELETE usa."""
    res = await resumo_parceiro(parceiro_id, dono)
    if not res:
        raise HTTPException(404, "Conta não encontrada.")
    return res


class ParceiroExcluirRequest(BaseModel):
    # Nome exato da conta, digitado pelo operador no modal. Conferido no repositório
    # — a rota é destrutiva e não pode confiar só no cliente para a confirmação.
    confirmar: str


@app.delete("/parceiros/{parceiro_id}")
async def excluir_parceiro_route(parceiro_id: int, body: ParceiroExcluirRequest,
                                 dono: str = Depends(dono_efetivo)):
    """Exclui a conta e TODAS as apostas dela. Snapshot fica em `lixeira_contas`
    por LIXEIRA_DIAS (restauração manual: scripts/restaurar_conta_lixeira.py)."""
    res = await excluir_parceiro(parceiro_id, dono, body.confirmar)
    if not res.get("ok"):
        motivo = res.get("motivo", "Não foi possível excluir.")
        raise HTTPException(404 if "não encontrada" in motivo else 400, motivo)
    return res


@app.post("/parceiros/{parceiro_id}/renomear")
async def renomear_parceiro_route(parceiro_id: int, body: ParceiroRenomearRequest,
                                  dono: str = Depends(dono_efetivo)):
    res = await renomear_parceiro(parceiro_id, body.nome, dono)
    if not res.get("ok"):
        raise HTTPException(400, res.get("motivo", "Não foi possível renomear."))
    return res


# ── Fatia 0: cadastro de tipster (Perfil de Tipster) ──────────────────────────
# NÃO confundir com GET /tipsters acima (autocomplete dos nomes já usados). Estas
# rotas gerem a TABELA `tipsters`. Espelham o CRUD de /parceiros, com dono_efetivo.
# Ver docs/PLANO_TIPSTER.md.

class TipsterCriarRequest(BaseModel):
    nome: str


class TipsterInfoRequest(BaseModel):
    casas: Optional[str] = None
    mercados: Optional[str] = None
    obs: Optional[str] = None
    # Fase B (detecção): faixa de stake típica (aceita número ou "1.234,50") e apelidos/
    # marca d'água (CSV). None = não mexe; "" = limpa. Ver repository.sugerir_tipster.
    stake_min: Optional[float | str] = None
    stake_max: Optional[float | str] = None
    apelidos: Optional[str] = None
    dica_stake: Optional[str] = None
    esportes: Optional[str] = None


class TipsterRenomearRequest(BaseModel):
    nome: str


@app.get("/tipsters/cadastro")
async def listar_tipsters_cadastro(arquivados: bool = False, dono: str = Depends(dono_efetivo)):
    rows = await list_tipsters_cadastro(dono, incluir_arquivados=arquivados)
    return {"tipsters": rows}


@app.post("/tipsters/cadastro")
async def criar_tipster_route(body: TipsterCriarRequest, dono: str = Depends(dono_efetivo)):
    nome = body.nome.strip()
    if not nome:
        raise HTTPException(400, "Nome do tipster não pode ser vazio.")
    return await criar_tipster(nome, dono)


@app.patch("/tipsters/{tipster_id}/info")
async def atualizar_tipster_info_route(tipster_id: int, body: TipsterInfoRequest,
                                       dono: str = Depends(dono_efetivo)):
    ok = await atualizar_tipster_info(tipster_id, dono, body.casas, body.mercados, body.obs,
                                      stake_min=body.stake_min, stake_max=body.stake_max,
                                      apelidos=body.apelidos, dica_stake=body.dica_stake,
                                      esportes=body.esportes)
    if not ok:
        raise HTTPException(404, "Tipster não encontrado ou sem campos válidos.")
    return {"atualizado": True}


class CasaConfigRequest(BaseModel):
    """Curadoria de uma casa: modo 'dedicada' (1-2 tipsters) ou 'multi' (compartilhada).
    `origem` = 'sharpen' (aplicada da sugestão) | 'custom' (editada à mão)."""
    casa: str
    modo: str
    tipsters: Optional[str] = ""
    origem: Optional[str] = "custom"


@app.get("/casas/config")
async def listar_casas_config(dono: str = Depends(dono_efetivo)):
    """Registro de Casas: evidência de pureza + sugestão de casa-feudo + config atual."""
    return {"casas": await casas_visao(dono)}


@app.post("/casas/config")
async def salvar_casa_config_route(body: CasaConfigRequest, dono: str = Depends(dono_efetivo)):
    ok = await salvar_casa_config(dono, body.casa, body.modo, body.tipsters or "", body.origem or "custom")
    if not ok:
        raise HTTPException(400, "Config de casa inválida (modo 'dedicada' com 1-2 tipsters ou 'multi'; origem 'sharpen'/'custom').")
    return {"salvo": True}


# ── Custos por dono (Custo por Tipster + Custos Gerais) ───────────────────────
# Persistem os custos da tela Gestão › Custos no Postgres, por dono (antes só em
# localStorage global → sumiam ao trocar de aparelho). Semeados uma vez pela
# página /dashboard/importar-custos.html. Ver database.custo_store / STATUS s165.
class CustoStoreRequest(BaseModel):
    """Blob de custos do dono: custo_tipster = {tipster:{"YYYY-MM": valor}},
    custo_geral = [{id, tipo, values}]. O front manda sempre o estado completo."""
    custo_tipster: dict = {}
    custo_geral: list = []


@app.get("/custos/store")
async def get_custo_store_route(dono: str = Depends(dono_efetivo)):
    """Custos do dono. `existe=False` = servidor ainda vazio p/ este dono → o front
    usa o cache local e a página de importação oferece semear a partir do navegador."""
    dados = await get_custo_store(dono)
    if dados is None:
        return {"existe": False, "custo_tipster": {}, "custo_geral": []}
    return {"existe": True, **dados}


@app.post("/custos/store")
async def salvar_custo_store_route(body: CustoStoreRequest, dono: str = Depends(dono_efetivo)):
    await salvar_custo_store(dono, body.custo_tipster or {}, body.custo_geral or [])
    return {"salvo": True}


# Custo por conta/fornecedor ({fornecedor||casa: numero}) — antes só no localStorage
# dash_custos_v2::<dono> (dashboard gestao.js + extrator index.html). Coluna custo_conta
# de custo_store; endpoint PRÓPRIO p/ não colidir com o blob tipster/geral acima.
class CustoContaRequest(BaseModel):
    custo_conta: dict = {}


@app.get("/custos/conta")
async def get_custo_conta_route(dono: str = Depends(dono_efetivo)):
    """`existe` = há custo por-conta de verdade no servidor (dict não-vazio). Uma linha
    criada só pelo import de tipster/geral tem custo_conta vazio → existe=False (o front
    ainda oferece importar o por-conta)."""
    dados = await get_custo_conta(dono)
    conta = (dados or {}).get("custo_conta") or {}
    return {"existe": bool(conta), "custo_conta": conta}


@app.post("/custos/conta")
async def salvar_custo_conta_route(body: CustoContaRequest, dono: str = Depends(dono_efetivo)):
    await salvar_custo_conta(dono, body.custo_conta or {})
    return {"salvo": True}


class SugerirTipsterRequest(BaseModel):
    """Entrada da auto-atribuição (esqueleto). `texto` = marca d'água/apelido lido do
    print — hoje a extração ainda não devolve isso, então a rota é de gaveta/teste."""
    casa: Optional[str] = ""
    stake: Optional[float | str] = None
    texto: Optional[str] = ""


@app.post("/tipsters/sugerir")
async def sugerir_tipster_route(body: SugerirTipsterRequest, dono: str = Depends(dono_efetivo)):
    tipsters = await list_tipsters_cadastro(dono, incluir_arquivados=False)
    sugestoes = sugerir_tipster(
        {"casa": body.casa, "stake": body.stake, "texto": body.texto}, tipsters
    )
    return {"sugestoes": sugestoes}


@app.post("/tipsters/{tipster_id}/arquivar")
async def arquivar_tipster_route(tipster_id: int, dono: str = Depends(dono_efetivo)):
    ok = await arquivar_tipster(tipster_id, dono)
    if not ok:
        raise HTTPException(404, "Tipster não encontrado.")
    return {"arquivado": True}


@app.post("/tipsters/{tipster_id}/reativar")
async def reativar_tipster_route(tipster_id: int, dono: str = Depends(dono_efetivo)):
    ok = await reativar_tipster(tipster_id, dono)
    if not ok:
        raise HTTPException(404, "Tipster não encontrado.")
    return {"arquivado": False}


@app.post("/tipsters/{tipster_id}/renomear")
async def renomear_tipster_route(tipster_id: int, body: TipsterRenomearRequest,
                                 dono: str = Depends(dono_efetivo)):
    res = await renomear_tipster(tipster_id, body.nome, dono)
    if not res.get("ok"):
        raise HTTPException(400, res.get("motivo", "Não foi possível renomear."))
    return res


# ── Fatia 1: escada de unidade + resultado em "u" (motor, sem UI ainda) ────────
# O tipster é referenciado por NOME (query param) — evita encoding no path. O render
# de "u" (switch R$⇄u, fmtU) é UI e passa pelo /nova-ui na fatia da interface.

class UnidadeSegmentoRequest(BaseModel):
    tipster: str
    vigente_desde: str
    # float | str: aceita número ou string BR ("1.234,50"); set_unidade normaliza
    # via _num_or_none (mesma máquina de número do resto do sistema).
    valor: float | str


@app.get("/tipsters/unidades")
async def get_escada_route(tipster: str, dono: str = Depends(dono_efetivo)):
    return {"escada": await get_escada_unidade(dono, tipster)}


@app.post("/tipsters/unidades")
async def set_unidade_route(body: UnidadeSegmentoRequest, dono: str = Depends(dono_efetivo)):
    res = await set_unidade(dono, body.tipster, body.vigente_desde, body.valor)
    if not res.get("ok"):
        raise HTTPException(400, res.get("motivo", "Não foi possível salvar o valor da unidade."))
    return res


@app.delete("/tipsters/unidades/{unidade_id}")
async def remover_unidade_route(unidade_id: int, dono: str = Depends(dono_efetivo)):
    ok = await remover_unidade(unidade_id, dono)
    if not ok:
        raise HTTPException(404, "Degrau da escada não encontrado.")
    return {"removido": True}


@app.get("/tipsters/resultado-unidades")
async def resultado_unidades_route(tipster: str, dono: str = Depends(dono_efetivo)):
    return await resultado_em_unidades(dono, tipster)


@app.get("/tipsters/escadas")
async def escadas_todas_route(dono: str = Depends(dono_efetivo)):
    return {"escadas": await get_escadas_todas(dono)}


# ── Vitrine pública de tipster (sem auth, somente leitura) ────────────────────
# sharpen.bet/tipsters/<slug> — o PRÓPRIO Betting Dashboard servido em modo
# público (decisão do Feca, s226: o cliente do tipster navega, filtra e analisa
# como se fosse a base dele — a "experiência Sharpen" — 100% em UNIDADES).
# Duas rotas: a casca (shell do dash + window.MODO_PUBLICO injetado) e o feed
# (/tipsters/<slug>/data, mesmo contrato de /dashboard/data, cache de 5 min).
# SÓ slugs do registro abaixo existem (o resto é 404: nenhum dono vira público
# por acidente). ORDEM IMPORTA: rotas de path dinâmico registradas DEPOIS de
# todas as /tipsters/* de API (o Starlette casa na ordem de registro), e
# /tipsters/{slug}/data ANTES de /tipsters/{slug} (mais específica primeiro).
TIPSTERS_PUBLICOS: dict[str, dict] = {
    "sochutes": {"dono": "SoChutes", "nome": "Só Chutes"},
    "zoraesports": {"dono": "ZoraEsports", "nome": "Zora eSports"},
    # 3º tipster (s260). O slug é o nome de MARCA (`fleury`); o dono é o username
    # com que ele se cadastrou no site (`Flurray`) — os dois divergem de propósito
    # e é o registro que faz a ponte. Base 100 % em unidades, como o modo pede.
    "fleury": {"dono": "Flurray", "nome": "Fleury"},
    # 4º tipster (s264). Aqui marca e username COINCIDEM — conferido na tabela
    # `usuarios` (ativo, cadastro em autosserviço), não deduzido do nome da
    # planilha. Base multiesporte em unidades: escanteios, props e múltiplas.
    "reidocriquete": {"dono": "reidocriquete", "nome": "Rei do Criquete"},
    # 5º tipster (s272). Marca e username DIVERGEM de novo, como no Fleury: a
    # marca é `PassaTips VIP` e o username é `passapano` (conferido na tabela
    # `usuarios` — ativo, cadastro em autosserviço em 17/08/2026). Base
    # MULTIESPORTE em unidades: 911 apostas em 20 esportes, 02/06 → 17/08/2026.
    "passatipsvip": {"dono": "passapano", "nome": "PassaTips VIP"},
}

_PUBLICO_TTL = 300  # 5 min — feed é público; o cache em memória protege o Postgres
_publico_data_cache: dict[str, tuple[float, bytes, bytes]] = {}  # slug → (ts, json, gzip)
_DASH_SHELL = Path(__file__).parent / "static" / "dash" / "index.html"


@app.get("/tipsters/{slug}/data")
async def dados_publicos_tipster(slug: str, request: Request, refresh: bool = False):
    """Feed do modo público — mesmo contrato de /dashboard/data (o front é o
    mesmo), montado por dashboard_rows (mesmo P/L derivado; nunca 2ª fórmula).
    `refresh` é aceito e IGNORADO: o botão "Atualizar dados" do dash manda
    ?refresh=1, mas visitante anônimo não fura o cache de 5 min."""
    cfg = TIPSTERS_PUBLICOS.get(slug.lower())
    if not cfg:
        raise HTTPException(404, "Página não encontrada.")
    agora = time.time()
    hit = _publico_data_cache.get(slug.lower())
    if not hit or agora - hit[0] >= _PUBLICO_TTL:
        rows = await dashboard_rows([cfg["dono"]])
        payload = {
            "ok": True,
            "data": rows,
            "builtAt": datetime.now(timezone.utc).isoformat(),
            "count": len(rows),
            "operadores": [cfg["dono"]],
            "dono": cfg["dono"],
        }
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        hit = (agora, body, gzip.compress(body, compresslevel=6))
        _publico_data_cache[slug.lower()] = hit
    if "gzip" in request.headers.get("accept-encoding", "").lower():
        return Response(
            content=hit[2],
            media_type="application/json",
            headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"},
        )
    return Response(content=hit[1], media_type="application/json")


@app.get("/tipsters/{slug}")
async def pagina_publica_tipster(slug: str):
    cfg = TIPSTERS_PUBLICOS.get(slug.lower())
    if not cfg:
        raise HTTPException(404, "Página não encontrada.")
    html = _DASH_SHELL.read_text(encoding="utf-8")
    # Injeção ANTES do script de guarda do shell (que redirecionaria para /app):
    # a flag ativa o modo público no front; o <base> resolve os assets relativos
    # (assets/js/…) para /dashboard/, onde o StaticFiles já os serve. Só valores
    # do REGISTRO entram no HTML — nada vindo de fora da caixa.
    inj = (
        "<script>window.MODO_PUBLICO="
        + json.dumps({"slug": slug.lower(), "nome": cfg["nome"]}, ensure_ascii=False)
        + ';</script>\n  <base href="/dashboard/">'
    )
    html = html.replace("<head>", "<head>\n  " + inj, 1)
    # HTML segue a regra da casa (middleware força no-cache — s215); o custo real
    # está no feed, que tem o cache de 5 min acima.
    return HTMLResponse(html)


# ── Betting Dashboard (mesma origem) ──────────────────────────────────────────
# Serve o front do dashboard (cópia viva em static/dash/) que lê /dashboard/data,
# filtrado pelo login. A planilha/Apps Script no GitHub Pages segue como backup
# congelado. Montado por ÚLTIMO de propósito: o Starlette casa rotas na ordem de
# registro, então /dashboard/data (definida acima) resolve antes deste StaticFiles;
# só /dashboard/ e /dashboard/assets|brand/... caem aqui. O shell é estático e não
# sensível (o dado é que exige cookie em /dashboard/data); abrir sem login carrega
# a casca mas a chamada de dados retorna 401.
app.mount(
    "/dashboard",
    StaticFiles(directory=str(Path(__file__).parent / "static" / "dash"), html=True),
    name="dashboard",
)

