import base64
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from anthropic import AsyncAnthropic
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import ALLOWED_MODELS, CASAS_DIR, DEFAULT_MODEL
from database import init_db
from prompts import build_system
from repository import (
    arquivar_parceiro, atualizar_bilhete, criar_parceiro, deletar_bilhetes,
    list_bilhetes, list_parceiros, marcar_copiada, marcar_pendente,
    parse_tsv, reativar_parceiro, upsert_bilhetes,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Scanner de Bets — FDC Capital", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
    )


_client = AsyncAnthropic()

# Nome de exibição canônico por casa (chave = uppercase do arquivo)
_CASA_DISPLAY: dict[str, str] = {
    "BET365":   "Bet365",
    "BETANO":   "Betano",
    "BETFAIR":  "Betfair",
    "PINNACLE": "Pinnacle",
    "SUPERBET": "Superbet",
}


def _casa_display(key: str) -> str:
    return _CASA_DISPLAY.get(key.upper(), key.title())


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
    "## Confiança\n"
    "Para cada linha: `N. XX%` — motivo se < 100%\n\n"
    "## Notas Críticas\n"
    "Alertas sobre campos ambíguos, dados faltantes ou decisões não óbvias "
    "observados NESTAS imagens de {casa}. Nunca mencione outras casas.\n"
    "Se nenhum, escreva: Nenhuma.\n\n"
    "## Recomendações\n"
    "Sugestões específicas para {casa} com base no que foi visto nesta sessão.\n"
    "Se nenhuma, escreva: Nenhuma."
)


# ── Rotas existentes ──────────────────────────────────────────────────────────

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
    data_referencia: Optional[str] = Form(None),
):
    if modelo not in ALLOWED_MODELS:
        raise HTTPException(400, f"Modelo não permitido. Opções: {ALLOWED_MODELS}")

    _HAIKU = "claude-haiku-4-5-20251001"

    casa_key = casa.upper()
    if not (CASAS_DIR / f"CASA_{casa_key}.md").exists():
        raise HTTPException(400, f"Casa desconhecida: {casa}")

    content: list[dict] = []

    for img in imagens:
        raw = await img.read()
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img.content_type or "image/jpeg",
                "data": base64.standard_b64encode(raw).decode(),
            },
        })

    if texto:
        content.append({"type": "text", "text": texto})

    if csv_content:
        content.append({"type": "text", "text": f"DADOS CSV:\n{csv_content}"})

    if not content:
        raise HTTPException(400, "Envie pelo menos uma imagem ou texto.")

    tem_imagens = any(item.get("type") == "image" for item in content)
    if tem_imagens and modelo == _HAIKU:
        raise HTTPException(400, "Haiku não processa imagens. Selecione Sonnet ou Opus.")

    from datetime import date as _date
    ref = data_referencia or _date.today().strftime("%d/%m/%Y")
    content.append({
        "type": "text",
        "text": _INSTRUCAO.format(
            casa=_casa_display(casa_key),
            parceiro=parceiro or "(não informado)",
            data_referencia=ref,
        ),
    })

    system = build_system(casa_key)

    async def _stream():
        try:
            async with _client.messages.stream(
                model=modelo,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": content}],
            ) as stream:
                async for chunk in stream.text_stream:
                    yield f"data: {json.dumps({'t': chunk})}\n\n"
                msg = await stream.get_final_message()
                u = msg.usage
                yield f"data: {json.dumps({'done': True, 'resultado': msg.content[0].text, 'modelo': modelo, 'tokens': {'input': u.input_tokens, 'output': u.output_tokens, 'cache_read': getattr(u, 'cache_read_input_tokens', 0), 'cache_write': getattr(u, 'cache_creation_input_tokens', 0)}})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': f'{type(exc).__name__}: {exc}'})}\n\n"

    return StreamingResponse(
        _stream(),
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
    """Recebe TSV extraído, faz parse e upsert no banco."""
    rows = parse_tsv(body.tsv)
    if not rows:
        raise HTTPException(400, "Nenhuma linha válida encontrada no TSV.")
    casa_key = (body.casa or "").upper() or None
    for row in rows:
        if casa_key:
            row["casa"] = _casa_display(casa_key)
        if body.parceiro:
            row["parceiro"] = body.parceiro
        row["tipster"] = ""  # sempre vazio; vem da camada de app, não do bilhete
    count, ids, alertas = await upsert_bilhetes(rows, confianca=body.confianca)
    return {"salvos": count, "ids": ids, "alertas": alertas}


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
    order: str = "asc",
):
    """Lista bilhetes. Por padrão retorna todos, ordenados do mais antigo."""
    rows = await list_bilhetes(
        casa=casa or None,
        parceiro=parceiro or None,
        copy_state=copy_state or None,
        extraction_state=extraction_state or None,
        order=order,
    )
    return {"bilhetes": rows, "total": len(rows)}


class CopiarRequest(BaseModel):
    ids: list[int]


@app.post("/bilhetes/copiar")
async def marcar_bilhetes_copiados(body: CopiarRequest):
    """Marca bilhetes como copiados para a planilha."""
    if not body.ids:
        raise HTTPException(400, "Lista de IDs vazia.")
    atualizados = await marcar_copiada(body.ids)
    return {"atualizados": atualizados}


@app.post("/bilhetes/desmarcar")
async def desmarcar_bilhetes(body: CopiarRequest):
    """Volta bilhetes para estado pendente."""
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
    casa_key = body.casa.upper()
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
