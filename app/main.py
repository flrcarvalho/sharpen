import asyncio
import base64
import csv
import io
import json
import logging
import math
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import xlrd

from anthropic import (
    APIConnectionError, APIStatusError, AsyncAnthropic, RateLimitError,
)
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import (
    COOKIE_NAME, SESSION_MAX_AGE, VER_COMO_COOKIE, criar_token, dono_efetivo,
    operadores_de, pode_ver_como, usuario_atual, usuario_do_request,
    verificar_credenciais,
)
from config import ALLOWED_MODELS, CASAS_DIR, DEFAULT_MODEL
from database import init_db
from polymarket import CambioIndisponivel, coletar_bilhetes, coletar_dashboard
from prompts import build_system
from repository import (
    analisar_extracao,
    arquivar_parceiro, atualizar_bilhete, auto_arquivar, contar_arquivados,
    casas_com_parceiros, contar_bilhetes, contar_incompletos,
    criar_parceiro, dashboard_rows, deletar_bilhetes,
    export_bilhetes, get_ativos_tipster, get_codigos_existentes,
    get_codigos_resolvidos, limpar_ativos_tipster, list_bilhetes, list_esportes, list_tipsters,
    set_ativo_tipster, set_tipster_bulk,
    list_parceiros, parse_tsv,
    reativar_parceiro, renomear_parceiro, resumo_conta, upsert_bilhetes,
)

logger = logging.getLogger("scanner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

_client = AsyncAnthropic()

_MAX_CHUNKS = 4
_MAX_CONCURRENT = 4

# Limites de upload (validados no servidor — o teto do front é contornável).
_MAX_IMGS = 15
_MAX_IMG_BYTES = 12 * 1024 * 1024     # 12 MB por imagem
_MAX_TOTAL_BYTES = 60 * 1024 * 1024   # 60 MB somando todas as imagens
_MAX_XLS_BYTES = 20 * 1024 * 1024     # 20 MB para o XLS
_ALLOWED_IMG_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}

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
    "BETFAIR":        "Betfair",
    "BETNACIONAL":    "Betnacional",
    "BOLSADEAPOSTA":  "Bolsa de Aposta",
    "JOGODEOURO":     "Jogo de Ouro",
    "KINGPANDA":      "KingPanda",
    "KTO":            "KTO",
    "LOTTU":          "Lottu",
    "PINNACLE":       "Pinnacle",
    "POLYMARKET":     "Polymarket",
    "SUPERBET":       "Superbet",
}


def _casa_display(key: str) -> str:
    return _CASA_DISPLAY.get(key.upper(), key.title())


def _display_to_key(name: str) -> str:
    """Converte display name ou chave para a chave canônica (ex: 'Bolsa de Aposta' → 'BOLSADEAPOSTA')."""
    upper = name.upper()
    if upper in _CASA_DISPLAY:
        return upper
    for key, display in _CASA_DISPLAY.items():
        if display.upper() == upper:
            return key
    return upper.replace(" ", "")


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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    asyncio.create_task(_cache_warmer())
    yield


app = FastAPI(title="Sharpen — Scanner de Bets", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


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


async def _parse_xls(raw: bytes, dono: str) -> tuple[str, int]:
    rows = _xls_parse_rows(raw)
    if not rows:
        return "", 0
    all_ids = [r["id"] for r in rows if r["id"]]
    known_ids = await get_codigos_existentes(all_ids, dono)
    new_rows = [r for r in rows if r["id"] not in known_ids]
    skipped = len(rows) - len(new_rows)
    new_rows_oldest_first = list(reversed(new_rows))
    if not new_rows_oldest_first:
        return "", skipped
    return _format_xls_rows(new_rows_oldest_first), skipped


# ── Betano: split por bilhete + pré-dedup por ID ───────────────────────────────

# Cada bilhete Betano (texto copiado) começa com uma linha-tipo isolada
# (Simples / Dupla / Tripla / N-seleções) e termina no rodapé ID:/data/Ganhos.
# A linha-tipo é o separador confiável — equivalente ao "=== Aposta ID" da Pinnacle.
_BETANO_SPLIT_RE = re.compile(r'(?m)(?=^(?:Simples|Dupla|Tripla|\d+-seleções)\s*$)')
_BETANO_ID_RE = re.compile(r'^ID:\s*(\d+)', re.MULTILINE)


def _split_betano_bilhetes(text: str) -> list[str]:
    """Divide o texto colado da Betano em blocos de 1 bilhete cada."""
    return [b.strip() for b in _BETANO_SPLIT_RE.split(text) if b.strip()]


async def _dedup_betano_text(text: str, dono: str) -> tuple[str, int]:
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

    ja_resolvidos = await get_codigos_resolvidos([i for i in ids if i], dono)

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
    "  • Esporte: mesmo esporte em todas → esse esporte; misto → 'Múltiplos'.\n\n"
    "RESULTADO — LEITURA OBRIGATÓRIA ANTES DA ODD:\n"
    "  Leia o RÓTULO do bilhete (canto superior direito) ANTES de ler qualquer campo financeiro.\n"
    "  'Perdida' → resultado = L. ENCERRE aqui: não leia RO, não calcule RO ÷ Stake.\n"
    "  'Anulado' / 'Void' / 'Reembolso' → resultado = V. Use odd exibida.\n"
    "  Sem rótulo (verde / em aberto) + RO > 0 → resultado = W.\n"
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

    # Caso 1: múltiplas imagens → divide por imagem
    if len(images) >= 2:
        n = min(_MAX_CHUNKS, len(images))
        size = math.ceil(len(images) / n)
        return [images[i:i+size] + [instrucao_block] for i in range(0, len(images), size)]

    # Caso 2: só texto → divide por blocos de apostas
    if not images and texts:
        full_text = "\n\n".join(b["text"] for b in texts)
        # CSV+texto precisam ficar juntos (a IA faz o join bilhete↔extrato)
        if "DADOS CSV:" in full_text:
            return [base_content + [instrucao_block]]
        if "=== Aposta ID" in full_text:
            blocks = re.split(r'(?=^=== Aposta ID)', full_text, flags=re.MULTILINE)
        elif casa_key.upper() == "BETANO":
            # Split na linha-tipo (Simples/Dupla/Tripla/N-seleções) = fronteira do bilhete
            blocks = _BETANO_SPLIT_RE.split(full_text)
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


def _combine_parallel_results(results: list[tuple[int, str, dict]]) -> tuple[str, dict, list[int]]:
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

async def _stream_sequential(system: list[dict], content: list[dict], modelo: str, xls_skipped: int):
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
        yield f"data: {json.dumps({'done': True, 'resultado': accumulated, 'stop_reason': msg.stop_reason, 'modelo': modelo, 'xls_skipped': xls_skipped, 'tokens': total_tokens})}\n\n"
    except Exception:
        logger.exception("Erro no stream sequencial")
        yield f"data: {json.dumps({'error': 'Erro ao processar a extração. Tente novamente.'})}\n\n"


async def _stream_parallel(system: list[dict], chunks: list[list[dict]], modelo: str, xls_skipped: int, casa_key: str = ""):
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
        # Regras de ordenação por casa:
        # - Pinnacle XLS: texto pré-invertido pelo parser → chunk 0 = mais antigo → reverse=False
        # - Superbet: usuário cola na ordem certa → chunk 0 = primeira bet → reverse=False
        # - Todo o resto: scroll de cima p/ baixo = mais recentes primeiro → reverse=True
        is_xls_mode = any(
            isinstance(b, dict) and b.get("type") == "text" and "=== Aposta ID" in b.get("text", "")
            for b in chunks[0]
        )
        reverse_chunks = not (is_xls_mode or casa_key.upper() == "SUPERBET")
        completed.sort(key=lambda x: x[0], reverse=reverse_chunks)
        resultado, total_tokens, scroll_overlap_indices = _combine_parallel_results(completed)
        logger.info("par total: %.1fs | chunks=%d | out=%d",
                    time.perf_counter() - t_start, n_chunks, total_tokens["output"])
        yield f"data: {json.dumps({'done': True, 'resultado': resultado, 'stop_reason': 'end_turn', 'modelo': modelo, 'xls_skipped': xls_skipped, 'tokens': total_tokens, 'scroll_overlap_indices': scroll_overlap_indices})}\n\n"
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


# ── Autenticação ──────────────────────────────────────────────────────────────

@app.get("/login")
async def login_page(request: Request):
    # Já logado → vai direto para a casca única.
    if usuario_do_request(request):
        return RedirectResponse("/app", status_code=303)
    content = (Path(__file__).parent / "static" / "login.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


class LoginRequest(BaseModel):
    usuario: str
    senha: str


# Rate limit de login em memória (reseta no reinício). Tolerante: não tranca
# usuário legítimo, só desacelera brute-force dos 2 usuários conhecidos.
_LOGIN_WINDOW = 300        # janela de 5 min
_LOGIN_MAX_FAILS = 10      # falhas permitidas por IP na janela
_login_fails: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")  # Railway fica atrás de proxy
    if xff:
        return xff.split(",")[0].strip()
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
    if not verificar_credenciais(usuario, body.senha):
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
    }


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
    return {"casas": sorted(manuais | com_dados)}


@app.post("/extrair")
async def extrair(
    casa: str = Form(...),
    parceiro: str = Form(""),
    modelo: str = Form(DEFAULT_MODEL),
    texto: Optional[str] = Form(None),
    csv_content: Optional[str] = Form(None),
    imagens: list[UploadFile] = File(default=[]),
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
    if not (CASAS_DIR / f"CASA_{casa_key}.md").exists():
        raise HTTPException(400, f"Casa desconhecida: {casa}")

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

    xls_skipped = 0

    if texto:
        # Betano (texto): pré-dedup por ID antes de chamar o modelo — descarta
        # bilhetes já liquidados no banco e duplicatas de scroll dentro do colar.
        if casa_key.upper() == "BETANO":
            texto, n_skip = await _dedup_betano_text(texto, dono)
            xls_skipped += n_skip
        if texto:
            base_content.append({"type": "text", "text": texto})

    if csv_content:
        base_content.append({"type": "text", "text": f"DADOS CSV:\n{csv_content}"})

    if xls_file:
        raw = await xls_file.read()
        if len(raw) > _MAX_XLS_BYTES:
            raise HTTPException(413, "Arquivo XLS excede o limite de 20 MB.")
        xls_text, n_skip = await _parse_xls(raw, dono)
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

    if use_parallel:
        generator = _stream_parallel(system, chunks, modelo, xls_skipped, casa_key)
    else:
        generator = _stream_sequential(system, base_content + [instrucao_block], modelo, xls_skipped)

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


# Criação de dado NOVO → dono REAL (ver nota em /extrair): salva sempre na base de
# quem está logado, mesmo em modo "ver como operador". Decisão do Feca, sessão 82.
@app.post("/salvar")
async def salvar(body: SalvarRequest, dono: str = Depends(usuario_atual)):
    rows = parse_tsv(body.tsv)
    if not rows:
        raise HTTPException(400, "Nenhuma linha válida encontrada no TSV.")
    casa_key = _display_to_key(body.casa) if body.casa else None
    for row in rows:
        if casa_key:
            row["casa"] = _casa_display(casa_key)
        if body.parceiro:
            row["parceiro"] = body.parceiro
        row["tipster"] = ""
    inseridos, atualizados, ids, alertas, duplicatas = await upsert_bilhetes(rows, dono, confianca=body.confianca)

    arquivados = 0
    if ids and (body.casa or rows):
        # Usa o MESMO display name com que as linhas foram gravadas (acima), senão
        # o filtro do auto_arquivar não casa. Antes: _casa_display(body.casa.upper())
        # transformava "Bolsa de Aposta" em "Bolsa De Aposta" (D maiúsculo) e o
        # arquivamento silenciosamente não ocorria para casas multi-palavra.
        casa_display = _casa_display(casa_key) if casa_key else rows[0].get("casa", "")
        parceiro_nome = body.parceiro or (rows[0].get("parceiro", "") if rows else "")
        arquivados = await auto_arquivar(casa_display, parceiro_nome, len(ids), dono)

    # Resumo do rail "Análise IA": confiança (heurística sobre as linhas) + KPIs +
    # notas estruturadas (só problemas reais). Não toca na IA de extração.
    analise = analisar_extracao(rows, duplicatas)

    return {"salvos": inseridos + atualizados, "inseridos": inseridos, "atualizados": atualizados,
            "ids": ids, "alertas": alertas, "duplicatas": duplicatas, "arquivados": arquivados,
            "analise": analise}


class PolymarketSyncRequest(BaseModel):
    wallet: str
    parceiro: str


_WALLET_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


@app.post("/polymarket/sync")
async def polymarket_sync(body: PolymarketSyncRequest, dono: str = Depends(dono_efetivo)):
    """Coleta o histórico resolvido de uma carteira Polymarket via API e salva na
    grade (casa='Polymarket'). Reusa upsert/auto-arquivar — mesma resposta do /salvar."""
    wallet = (body.wallet or "").strip()
    if not _WALLET_RE.match(wallet):
        raise HTTPException(400, "Carteira inválida — informe um endereço 0x… (42 caracteres).")
    parceiro = (body.parceiro or "").strip()
    if not parceiro:
        raise HTTPException(400, "Selecione um parceiro antes de sincronizar.")

    try:
        rows = await coletar_bilhetes(wallet, parceiro)
    except CambioIndisponivel as exc:
        # Mensagem controlada por nós (não vaza internals); 503 = tente de novo depois.
        raise HTTPException(503, str(exc))
    except Exception:
        logger.exception("Falha na coleta Polymarket")
        raise HTTPException(502, "Erro ao consultar a Polymarket. Tente novamente.")

    if not rows:
        return {"salvos": 0, "inseridos": 0, "atualizados": 0, "ids": [],
                "alertas": ["Nenhum bilhete resolvido encontrado para esta carteira."],
                "duplicatas": {}, "arquivados": 0, "coletados": 0}

    # Carry-over: o tipster atribuído à posição enquanto ativa (dashboard) acompanha
    # o bilhete quando ele resolve. O upsert preserva tipster não-vazio.
    codigos = [r["codigo_bilhete"] for r in rows if r.get("codigo_bilhete")]
    salvos = await get_ativos_tipster(dono, codigos)
    for r in rows:
        t = salvos.get(r.get("codigo_bilhete", ""))
        if t:
            r["tipster"] = t

    inseridos, atualizados, ids, alertas, duplicatas = await upsert_bilhetes(rows, dono, origem="sync")
    # As posições que resolveram migraram o tipster para `bilhetes`: apaga as linhas
    # de ativa correspondentes para não reinjetar (e sobrescrever) no próximo re-sync.
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


@app.get("/dashboard/data")
async def dashboard_data(dono: str = Depends(dono_efetivo)):
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
    rows = await dashboard_rows(escopo)
    return {
        "ok": True,
        "data": rows,
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "operadores": escopo,
    }


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
    nome = f"planilhador_base_{dono}_{_dt.now().strftime('%Y-%m-%d_%H%M')}.csv"
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


class DeletarRequest(BaseModel):
    ids: list[int]


@app.delete("/bilhetes")
async def deletar_bilhetes_route(body: DeletarRequest, dono: str = Depends(dono_efetivo)):
    if not body.ids:
        raise HTTPException(400, "Lista de IDs vazia.")
    deletados = await deletar_bilhetes(body.ids, dono)
    return {"deletados": deletados}


@app.delete("/bilhetes/{bilhete_id}")
async def deletar_bilhete_route(bilhete_id: int, dono: str = Depends(dono_efetivo)):
    deletados = await deletar_bilhetes([bilhete_id], dono)
    if not deletados:
        raise HTTPException(404, "Bilhete não encontrado.")
    return {"deletado": True}


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


@app.get("/bilhetes")
async def listar_bilhetes(
    casa: Optional[str] = None,
    parceiro: Optional[str] = None,
    extraction_state: Optional[str] = None,
    archived: str = "false",
    order: str = "asc",
    limit: int = 500,
    offset: int = 0,
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
    )
    total = await contar_bilhetes(
        dono,
        casa=casa or None,
        parceiro=parceiro or None,
        extraction_state=extraction_state or None,
        archived=archived,
    )
    arquivados_count = 0
    if archived != "true" and (casa or parceiro):
        arquivados_count = await contar_arquivados(casa or "", parceiro or "", dono)
    return {
        "bilhetes": rows, "total": total, "arquivados": arquivados_count,
        "limit": limit, "offset": offset,
    }


class BilheteManualRequest(BaseModel):
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
async def informar_tipster_lote(body: TipsterLoteRequest, dono: str = Depends(dono_efetivo)):
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
    if not (CASAS_DIR / f"CASA_{casa_key}.md").exists():
        raise HTTPException(400, f"Casa desconhecida: {body.casa}")
    row = await criar_parceiro(_casa_display(casa_key), nome, dono)
    return row


@app.post("/parceiros/{parceiro_id}/arquivar")
async def arquivar_parceiro_route(parceiro_id: int, dono: str = Depends(dono_efetivo)):
    ok = await arquivar_parceiro(parceiro_id, dono)
    if not ok:
        raise HTTPException(404, "Parceiro não encontrado.")
    return {"arquivado": True}


class AtualizarBilheteRequest(BaseModel):
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


@app.patch("/bilhetes/{bilhete_id}")
async def atualizar_bilhete_route(bilhete_id: int, body: AtualizarBilheteRequest,
                                  dono: str = Depends(dono_efetivo)):
    campos = {k: v for k, v in body.model_dump().items() if v is not None}
    ok = await atualizar_bilhete(bilhete_id, campos, dono)
    if not ok:
        raise HTTPException(404, "Bilhete não encontrado ou sem campos válidos.")
    return {"atualizado": True}


@app.post("/parceiros/{parceiro_id}/reativar")
async def reativar_parceiro_route(parceiro_id: int, dono: str = Depends(dono_efetivo)):
    ok = await reativar_parceiro(parceiro_id, dono)
    if not ok:
        raise HTTPException(404, "Parceiro não encontrado.")
    return {"arquivado": False}


class ParceiroRenomearRequest(BaseModel):
    nome: str


@app.post("/parceiros/{parceiro_id}/renomear")
async def renomear_parceiro_route(parceiro_id: int, body: ParceiroRenomearRequest,
                                  dono: str = Depends(dono_efetivo)):
    res = await renomear_parceiro(parceiro_id, body.nome, dono)
    if not res.get("ok"):
        raise HTTPException(400, res.get("motivo", "Não foi possível renomear."))
    return res


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

