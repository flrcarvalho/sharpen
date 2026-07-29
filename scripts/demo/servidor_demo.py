# -*- coding: utf-8 -*-
"""Servidor de DEMONSTRACAO -- serve o front-end REAL com a base ficticia.

Para que serve: tirar print do sistema funcionando, para material de venda, sem
tocar em producao e sem expor numero ou nome de cliente.

Como funciona: o painel do Sharpen e' 100% client-side -- ele busca JSON em umas
poucas rotas e faz toda a matematica no navegador. Entao servimos os MESMOS
arquivos estaticos de `app/static` e trocamos so o backend por estes mocks. O
que aparece no print e' o codigo de producao renderizando dado de mentira: nao
e' maquete, e' o produto.

    python scripts/demo/servidor_demo.py          # http://127.0.0.1:8010
    python scripts/demo/servidor_demo.py 8020

NAO importa `app.main`: nada de banco, de chave de API ou de sessao. Nao ha
autenticacao aqui porque nao ha o que proteger -- o dado e' inventado. Por isso
mesmo: e' um servidor LOCAL de captura, nunca para expor na rede.
"""
import pathlib
import sys
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dados_demo  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parents[2]
ESTATICO = RAIZ / "app" / "static"

LINHAS = dados_demo.gerar()
RESUMO = dados_demo.resumo(LINHAS)

app = FastAPI(title="Sharpen — servidor de demonstração", docs_url=None, redoc_url=None)


# ── Contas ficticias, derivadas do proprio feed para nao divergir dele ────────
def _parceiros():
    vistos, saida, i = set(), [], 1
    for r in LINHAS:
        chave = (r["parceiro"], r["casa"])
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append({"id": i, "nome": r["parceiro"], "casa": r["casa"], "arquivado": False})
        i += 1
    return saida


PARCEIROS = _parceiros()

# ── Apostas em aberto: painel da tela inicial + tela "Em Aberto" do dash ─────
# Desde a s215 elas saem NO FEED (resultado='ABERTA', lucro=0), igual em producao
# (repository.dashboard_rows) -- e' o que alimenta a tela "Em Aberto". A rota
# /bilhetes?extraction_state=aberta devolve AS MESMAS linhas, tambem como em
# producao; quem consome as duas dedupa por `id` (ver inicio.html).
# `data` = data do EVENTO, espalhada pelos proximos dias (o calendario da tela
# mede exatamente isso), com duas atrasadas para o print mostrar esse estado.
_ABRT_OFFSETS = [-2, -1, 0, 0, 1, 1, 2, 3, 4, 6, 9, 13]


def _abertas():
    agora = datetime.now()
    hoje = agora.date()
    base = [r for r in LINHAS[-600:] if r["esporte"] in ("Futebol", "Basquete", "Tênis")][:len(_ABRT_OFFSETS)]
    saida = []
    for k, r in enumerate(base):
        linha = dict(r)
        linha.update({
            "id": 900000 + k,
            "data": (hoje + timedelta(days=_ABRT_OFFSETS[k])).isoformat(),
            "resultado": "ABERTA",
            "lucro": 0.0,
            "criado_em": (agora - timedelta(hours=3 + k * 7)).isoformat(),
        })
        saida.append(linha)
    return saida


ABERTAS = _abertas()
# O feed consolida resolvidas + abertas, exatamente como o `dashboard_rows`.
LINHAS_FEED = LINHAS + ABERTAS
# Contrato de /bilhetes (grade do extrator): stake em texto pt-BR.
ABERTAS_BILHETES = [dict(r, stake=f"{r['stake']:.2f}".replace(".", ",")) for r in ABERTAS]


@app.get("/me")
def me():
    return {"usuario": dados_demo.DONO, "dono_efetivo": dados_demo.DONO, "operadores": []}


@app.get("/dashboard/data")
def dashboard_data(refresh: bool = False):
    # Contrato do Code.gs/Apps Script, que o dash herdou: {ok, data, builtAt,
    # count}. O `ok` NAO e' decorativo -- `app.js:1120` faz
    # `if(!json.ok) throw new Error(json.error || 'Erro desconhecido')`, entao
    # sem ele a tela inteira cai no estado de erro com o feed correto na mao.
    # `dono` escopa o store de custos no front (isolamento entre usuarios).
    return {
        "ok": True,
        "data": LINHAS_FEED,
        "count": len(LINHAS_FEED),
        "builtAt": datetime.now().isoformat(),
        "dono": dados_demo.DONO,
        "operadores": [dados_demo.DONO],
    }


@app.get("/bilhetes")
def bilhetes(extraction_state: str = "", archived: str = "", limit: int = 100, order: str = "desc"):
    if extraction_state == "aberta":
        return {"bilhetes": ABERTAS_BILHETES, "total": len(ABERTAS_BILHETES)}
    return {"bilhetes": [], "total": 0}


@app.get("/parceiros")
def parceiros(arquivados: bool = False):
    return {"parceiros": PARCEIROS}


@app.get("/incompletos")
def incompletos():
    # Duas pendencias, de proposito: a tela inicial tem um painel "Precisa de
    # voce" e um print com ele VAZIO esconderia um recurso do produto.
    return {"por_casa_tipster": {"bet365": 2, "Betano": 1}}


@app.get("/casas")
def casas():
    return {"casas": sorted({r["casa"] for r in LINHAS})}


@app.get("/esportes")
def esportes():
    return {"esportes": sorted({r["esporte"] for r in LINHAS})}


@app.get("/tipsters")
def tipsters():
    return {"tipsters": sorted({r["tipster"] for r in LINHAS if r["tipster"]})}


# ── Rotas de gestao: forma valida e vazia. Nao entram nos prints escolhidos,
#    mas se o front pedir e receber 404 ele quebra a tela inteira. ────────────
@app.get("/casas/config")
def casas_config():
    return {"config": {}}


@app.get("/casas/meta")
def casas_meta():
    return {"meta": {}}


@app.get("/custos/conta")
def custos_conta():
    return {"custos": {}}


@app.get("/custos/store")
def custos_store():
    return {"custos": {}}


@app.get("/tipsters/cadastro")
def tipsters_cadastro():
    return {"tipsters": []}


@app.get("/tipsters/unidades")
def tipsters_unidades():
    return {"unidades": {}}


@app.get("/tipsters/escadas")
def tipsters_escadas():
    return {"escadas": {}}


@app.get("/conta/resumo")
def conta_resumo():
    return {"resumo": {}}


@app.get("/polymarket/dashboard")
def poly():
    return {"data": []}


# ── Paginas ──────────────────────────────────────────────────────────────────
@app.get("/")
def raiz():
    return FileResponse(ESTATICO / "index.html")


@app.get("/inicio")
def inicio():
    return FileResponse(ESTATICO / "inicio.html")


@app.get("/app")
def casca():
    return FileResponse(ESTATICO / "app.html")


@app.get("/login")
def login():
    return FileResponse(ESTATICO / "login.html")


@app.get("/_resumo")
def resumo_demo():
    """Conferencia rapida da base servida (nao e' rota do produto)."""
    return JSONResponse(RESUMO)


# StaticFiles por ULTIMO: `/dashboard/data` acima precisa vencer o mount de
# `/dashboard`, exatamente como no main.py de producao.
app.mount("/static", StaticFiles(directory=ESTATICO), name="static")
app.mount("/dashboard", StaticFiles(directory=ESTATICO / "dash", html=True), name="dash")


if __name__ == "__main__":
    import uvicorn

    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8010
    print("base de demonstração:", RESUMO)
    uvicorn.run(app, host="127.0.0.1", port=porta, log_level="warning")
