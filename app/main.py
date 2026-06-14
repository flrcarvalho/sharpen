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
from repository import list_bilhetes, marcar_copiada, parse_tsv, upsert_bilhetes


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
    "Parceiro: {parceiro}\n\n"
    "Retorne o TSV em bloco ```tsv e, após ele, a confiança (0–100%) de cada linha "
    "com o motivo quando < 100%."
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

    content.append({
        "type": "text",
        "text": _INSTRUCAO.format(parceiro=parceiro or "(não informado)"),
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


@app.post("/salvar")
async def salvar(body: SalvarRequest):
    """Recebe TSV extraído, faz parse e upsert no banco."""
    rows = parse_tsv(body.tsv)
    if not rows:
        raise HTTPException(400, "Nenhuma linha válida encontrada no TSV.")
    count = await upsert_bilhetes(rows, confianca=body.confianca)
    return {"salvos": count}


@app.get("/bilhetes")
async def listar_bilhetes(
    casa: Optional[str] = None,
    parceiro: Optional[str] = None,
    copy_state: Optional[str] = "pendente",
    extraction_state: Optional[str] = None,
):
    """Lista bilhetes. Por padrão retorna apenas os pendentes de cópia."""
    rows = await list_bilhetes(
        casa=casa,
        parceiro=parceiro,
        copy_state=copy_state,
        extraction_state=extraction_state,
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
