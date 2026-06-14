import base64
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from config import ALLOWED_MODELS, CASAS_DIR, DEFAULT_MODEL
from prompts import build_system

app = FastAPI(title="Scanner de Bets — FDC Capital")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

_client = Anthropic()  # lê ANTHROPIC_API_KEY do ambiente automaticamente

_INSTRUCAO = (
    "Extraia os bilhetes acima para TSV no padrão FDC Capital.\n"
    "Parceiro: {parceiro}\n\n"
    "Retorne o TSV em bloco ```tsv e, após ele, a confiança (0–100%) de cada linha "
    "com o motivo quando < 100%."
)


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
