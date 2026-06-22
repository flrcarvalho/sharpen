import asyncio
import base64
import json
import logging
import math
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import xlrd

from anthropic import AsyncAnthropic
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import ALLOWED_MODELS, CASAS_DIR, DEFAULT_MODEL
from database import init_db
from prompts import build_system
from repository import (
    arquivar_parceiro, atualizar_bilhete, auto_arquivar, contar_arquivados,
    criar_parceiro, deletar_bilhetes, get_codigos_existentes, list_bilhetes,
    list_parceiros, marcar_copiada, marcar_pendente, parse_tsv,
    reativar_parceiro, upsert_bilhetes,
)

logger = logging.getLogger("scanner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

_client = AsyncAnthropic()

_MAX_CHUNKS = 4
_MAX_CONCURRENT = 4
_TSV_HEADER = "Data\tEsporte\tTipster\tCasa\tParceiro\tAposta\tDescrição\tStake\tOdd\tResultado\tCódigo"

_CASA_DISPLAY: dict[str, str] = {
    "BET365":         "Bet365",
    "BETANO":         "Betano",
    "BETFAIR":        "Betfair",
    "BETNACIONAL":    "Betnacional",
    "BOLSADEAPOSTA":  "Bolsa de Aposta",
    "KINGPANDA":      "KingPanda",
    "PINNACLE":       "Pinnacle",
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


app = FastAPI(title="Scanner de Bets — FDC Capital", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
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


async def _parse_xls(raw: bytes) -> tuple[str, int]:
    rows = _xls_parse_rows(raw)
    if not rows:
        return "", 0
    all_ids = [r["id"] for r in rows if r["id"]]
    known_ids = await get_codigos_existentes(all_ids)
    new_rows = [r for r in rows if r["id"] not in known_ids]
    skipped = len(rows) - len(new_rows)
    new_rows_oldest_first = list(reversed(new_rows))
    if not new_rows_oldest_first:
        return "", skipped
    return _format_xls_rows(new_rows_oldest_first), skipped


# ── Instrução ─────────────────────────────────────────────────────────────────

_INSTRUCAO = (
    "Extraia os bilhetes das imagens para TSV no padrão FDC Capital.\n"
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
    "  2. Para cada imagem, extraia TODOS os bilhetes visíveis. Não pule nenhuma imagem.\n\n"
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
    "  2. L (rótulo 'Perdida') → Odd = campo de odd lido diretamente do bilhete.\n"
    "     NUNCA calcule o produto das odds das seleções individuais.\n"
    "     NUNCA calcule RO ÷ Stake (RO = R$0,00 sempre que 'Perdida').\n"
    "  3. V (void/reembolso) → Odd = campo de odd do bilhete.\n"
    "  Precisão: exata, máximo 12 casas decimais, sem arredondamento.\n"
    "  NUNCA use reticências (... ou …) em odds. Escreva o número completo e pare — ex: 1,90917218543046\n\n"
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

def _build_chunks(base_content: list[dict], instrucao_block: dict) -> list[list[dict]]:
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
        # Normaliza odd para 2 casas decimais para absorver diferenças de precisão entre chunks
        # (ex: um chunk lê "1,83" e outro calcula "1,8331168..." — mesma aposta, string diferente)
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
                try:
                    async with _client.messages.stream(
                        model=modelo, max_tokens=64000,
                        system=system, messages=_m,
                    ) as stream:
                        async for chunk in stream.text_stream:
                            await q.put(("t", chunk))
                        fin = await stream.get_final_message()
                    await q.put(("done", fin))
                except Exception as e:
                    await q.put(("err", e))

            task = asyncio.create_task(_call())
            msg = None
            try:
                while True:
                    try:
                        kind, val = await asyncio.wait_for(q.get(), timeout=20)
                    except asyncio.TimeoutError:
                        yield ": keepalive\n\n"
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
    except Exception as exc:
        yield f"data: {json.dumps({'error': f'{type(exc).__name__}: {exc}'})}\n\n"


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
                    async with _client.messages.stream(
                        model=modelo, max_tokens=64000,
                        system=system, messages=messages,
                    ) as stream:
                        async for chunk in stream.text_stream:
                            accumulated += chunk
                        fin = await stream.get_final_message()

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
                    yield ": keepalive\n\n"
            if err:
                logger.error("par chunk %d falhou (continuando): %s", idx + 1, err)
                completed.append((idx, "", tokens))
            else:
                completed.append((idx, text, tokens))
            yield f"data: {json.dumps({'chunk_progress': idx + 1, 'of': n_chunks})}\n\n"
    except Exception as exc:
        await asyncio.gather(*tasks, return_exceptions=True)
        yield f"data: {json.dumps({'error': f'{type(exc).__name__}: {exc}'})}\n\n"
        return

    await asyncio.gather(*tasks, return_exceptions=True)
    # Regras de ordenação por casa:
    # - Pinnacle XLS: texto pré-invertido pelo parser → chunk 0 = mais antigo → reverse=False
    # - Superbet: usuário cola uma aposta por imagem na ordem certa → chunk 0 = primeira bet → reverse=False
    # - Todo o resto (Betano texto, BET365, Betano imgs, KingPanda, Betfair): scroll de cima p/ baixo =
    #   mais recentes primeiro → chunk N = mais antigas → vir antes → reverse=True
    is_xls_mode = any(
        isinstance(b, dict) and b.get("type") == "text" and "=== Aposta ID" in b.get("text", "")
        for b in chunks[0]
    )
    reverse_chunks = not (is_xls_mode or casa_key.upper() == "SUPERBET")
    completed.sort(key=lambda x: x[0], reverse=reverse_chunks)
    try:
        resultado, total_tokens, scroll_overlap_indices = _combine_parallel_results(completed)
    except Exception as exc:
        yield f"data: {json.dumps({'error': f'{type(exc).__name__}: {exc}'})}\n\n"
        return

    logger.info("par total: %.1fs | chunks=%d | out=%d",
                time.perf_counter() - t_start, n_chunks, total_tokens["output"])
    yield f"data: {json.dumps({'done': True, 'resultado': resultado, 'stop_reason': 'end_turn', 'modelo': modelo, 'xls_skipped': xls_skipped, 'tokens': total_tokens, 'scroll_overlap_indices': scroll_overlap_indices})}\n\n"


# ── Rotas ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    content = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/casas")
async def listar_casas():
    casas = sorted(
        _casa_display(p.stem.removeprefix("CASA_"))
        for p in CASAS_DIR.glob("CASA_*.md")
        if p.stem != "CASA_MODELO"
    )
    return {"casas": casas}


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
):
    if modelo not in ALLOWED_MODELS:
        raise HTTPException(400, f"Modelo não permitido. Opções: {ALLOWED_MODELS}")

    casa_key = _display_to_key(casa)
    if not (CASAS_DIR / f"CASA_{casa_key}.md").exists():
        raise HTTPException(400, f"Casa desconhecida: {casa}")

    base_content: list[dict] = []

    for img in imagens:
        raw = await img.read()
        base_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img.content_type or "image/jpeg",
                "data": base64.standard_b64encode(raw).decode(),
            },
        })

    if texto:
        base_content.append({"type": "text", "text": texto})

    if csv_content:
        base_content.append({"type": "text", "text": f"DADOS CSV:\n{csv_content}"})

    xls_skipped = 0
    if xls_file:
        raw = await xls_file.read()
        xls_text, xls_skipped = await _parse_xls(raw)
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
    chunks = _build_chunks(base_content, instrucao_block)
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


@app.post("/salvar")
async def salvar(body: SalvarRequest):
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
    inseridos, atualizados, ids, alertas, duplicatas = await upsert_bilhetes(rows, confianca=body.confianca)

    arquivados = 0
    if ids and (body.casa or rows):
        casa_display = _casa_display((body.casa or rows[0].get("casa", "")).upper())
        parceiro_nome = body.parceiro or (rows[0].get("parceiro", "") if rows else "")
        arquivados = await auto_arquivar(casa_display, parceiro_nome, len(ids))

    return {"salvos": inseridos + atualizados, "inseridos": inseridos, "atualizados": atualizados,
            "ids": ids, "alertas": alertas, "duplicatas": duplicatas, "arquivados": arquivados}


class DeletarRequest(BaseModel):
    ids: list[int]


@app.delete("/bilhetes")
async def deletar_bilhetes_route(body: DeletarRequest):
    if not body.ids:
        raise HTTPException(400, "Lista de IDs vazia.")
    deletados = await deletar_bilhetes(body.ids)
    return {"deletados": deletados}


@app.delete("/bilhetes/{bilhete_id}")
async def deletar_bilhete_route(bilhete_id: int):
    deletados = await deletar_bilhetes([bilhete_id])
    if not deletados:
        raise HTTPException(404, "Bilhete não encontrado.")
    return {"deletado": True}


@app.get("/bilhetes")
async def listar_bilhetes(
    casa: Optional[str] = None,
    parceiro: Optional[str] = None,
    copy_state: Optional[str] = None,
    extraction_state: Optional[str] = None,
    archived: str = "false",
    order: str = "asc",
):
    rows = await list_bilhetes(
        casa=casa or None,
        parceiro=parceiro or None,
        copy_state=copy_state or None,
        extraction_state=extraction_state or None,
        archived=archived,
        order=order,
    )
    arquivados_count = 0
    if archived != "true" and (casa or parceiro):
        arquivados_count = await contar_arquivados(casa or "", parceiro or "")
    return {"bilhetes": rows, "total": len(rows), "arquivados": arquivados_count}


class CopiarRequest(BaseModel):
    ids: list[int]


@app.post("/bilhetes/copiar")
async def marcar_bilhetes_copiados(body: CopiarRequest):
    if not body.ids:
        raise HTTPException(400, "Lista de IDs vazia.")
    atualizados = await marcar_copiada(body.ids)
    return {"atualizados": atualizados}


@app.post("/bilhetes/desmarcar")
async def desmarcar_bilhetes(body: CopiarRequest):
    if not body.ids:
        raise HTTPException(400, "Lista de IDs vazia.")
    atualizados = await marcar_pendente(body.ids)
    return {"atualizados": atualizados}


# ── Fase 4: parceiros persistidos ─────────────────────────────────────────────

class ParceiroCriarRequest(BaseModel):
    casa: str
    nome: str


@app.get("/parceiros")
async def listar_parceiros(casa: Optional[str] = None, arquivados: bool = False):
    rows = await list_parceiros(casa=casa or None, incluir_arquivados=arquivados)
    return {"parceiros": rows}


@app.post("/parceiros")
async def criar_parceiro_route(body: ParceiroCriarRequest):
    casa_key = _display_to_key(body.casa)
    nome = body.nome.strip()
    if not nome:
        raise HTTPException(400, "Nome do parceiro não pode ser vazio.")
    if not (CASAS_DIR / f"CASA_{casa_key}.md").exists():
        raise HTTPException(400, f"Casa desconhecida: {body.casa}")
    row = await criar_parceiro(_casa_display(casa_key), nome)
    return row


@app.post("/parceiros/{parceiro_id}/arquivar")
async def arquivar_parceiro_route(parceiro_id: int):
    ok = await arquivar_parceiro(parceiro_id)
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
async def atualizar_bilhete_route(bilhete_id: int, body: AtualizarBilheteRequest):
    campos = {k: v for k, v in body.model_dump().items() if v is not None}
    ok = await atualizar_bilhete(bilhete_id, campos)
    if not ok:
        raise HTTPException(404, "Bilhete não encontrado ou sem campos válidos.")
    return {"atualizado": True}


@app.post("/parceiros/{parceiro_id}/reativar")
async def reativar_parceiro_route(parceiro_id: int):
    ok = await reativar_parceiro(parceiro_id)
    if not ok:
        raise HTTPException(404, "Parceiro não encontrado.")
    return {"arquivado": False}

