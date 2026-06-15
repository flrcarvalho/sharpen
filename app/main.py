import base64
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
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


_client = Anthropic()

_INSTRUCAO = (
    "Extraia os bilhetes acima para TSV no padrão FDC Capital.\n"
    "Parceiro: {parceiro}\n"
    "Data de referência da captura (quando os prints foram tirados): {data_referencia}\n"
    "  → Hoje = {data_referencia} · Ontem = dia anterior · Amanhã = dia seguinte\n"
    "  → NUNCA usar o horário de processamento para resolver Hoje/Ontem/Amanhã\n\n"
    "Responda EXATAMENTE neste formato (sem variações de estrutura):\n\n"
    "```tsv\n"
    "Data\tEsporte\tTipster\tCasa\tParceiro\tAposta\tDescrição\tStake\tOdd\tResultado\n"
    "[uma linha TSV por bilhete]\n"
    "```\n\n"
    "REGRAS INVIOLÁVEIS DA ODD (aplicar nesta ordem):\n"
    "1. W com PRÊMIO/retorno visível → Odd = PRÊMIO ÷ Stake. SEMPRE. "
    "   A odd exibida no bilhete (ex: ODDS TOTAIS da Superbet) é IGNORADA quando há PRÊMIO visível. "
    "   Boost/SUPERMÚLTIPLA: o PRÊMIO já inclui o boost → usar PRÊMIO ÷ Stake, nunca ODDS TOTAIS. "
    "   Exemplo: ODDS TOTAIS 10,88; SUPERMÚLTIPLA 5%; PRÊMIO 1.706,41; Stake 150 → "
    "   Odd = 1.706,41 ÷ 150 = 11,37606666666667 (não 10,88).\n"
    "2. Precisão: use o valor EXATO da divisão — nunca arredonde, ajuste ou modifique casas decimais. "
    "   Máximo 12 casas. Exemplo: 473,46 ÷ 50 = 9,4692 → não 9,47 nem 9,4728.\n\n"
    "## Confiança\n"
    "Para cada linha: `N. XX%` — motivo se < 100%\n\n"
    "## Notas Críticas\n"
    "Alertas sobre campos ambíguos, dados faltantes ou decisões não óbvias. "
    "Se nenhum, escreva: Nenhuma.\n\n"
    "## Recomendações\n"
    "Sugestões para melhorar a qualidade da extração futura. "
    "Se nenhuma, escreva: Nenhuma."
)


# ── Rotas existentes ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/casas")
async def listar_casas():
    casas = sorted(
        p.stem.removeprefix("CASA_")
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
    imagens: list[UploadFile] = File(default=[]),
    data_referencia: Optional[str] = Form(None),
):
    if modelo not in ALLOWED_MODELS:
        raise HTTPException(400, f"Modelo não permitido. Opções: {ALLOWED_MODELS}")

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

    if not content:
        raise HTTPException(400, "Envie pelo menos uma imagem ou texto.")

    from datetime import date as _date
    ref = data_referencia or _date.today().strftime("%d/%m/%Y")
    content.append({
        "type": "text",
        "text": _INSTRUCAO.format(parceiro=parceiro or "(não informado)", data_referencia=ref),
    })

    resp = _client.messages.create(
        model=modelo,
        max_tokens=4096,
        system=build_system(casa_key),
        messages=[{"role": "user", "content": content}],
    )

    u = resp.usage
    return {
        "resultado": resp.content[0].text,
        "modelo": modelo,
        "casa": casa_key,
        "parceiro": parceiro,
        "tokens": {
            "input": u.input_tokens,
            "output": u.output_tokens,
            "cache_read": getattr(u, "cache_read_input_tokens", 0),
            "cache_write": getattr(u, "cache_creation_input_tokens", 0),
        },
    }


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
            row["casa"] = casa_key
        if body.parceiro:
            row["parceiro"] = body.parceiro
    count, ids = await upsert_bilhetes(rows, confianca=body.confianca)
    return {"salvos": count, "ids": ids}


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
    row = await criar_parceiro(casa_key, nome)
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
