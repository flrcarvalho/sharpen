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


# ── Contas: vem do ELENCO, nunca derivadas do feed ───────────────────────────
# Ate a s294 esta funcao varria as apostas e criava uma conta para cada par
# (parceiro, casa) que aparecesse. Como o gerador sorteava pessoa e casa de forma
# independente, o resultado eram 1.830 contas contra as 102 reais -- e a tela de
# Fornecedores repetia essa lista embaixo de cada casa. O erro nao era de contagem,
# era de DIRECAO: na producao a conta e' uma linha de `parceiros` e a aposta aponta
# para ela; aqui a aposta estava inventando a conta. Agora o cadastro e' a fonte,
# como no sistema de verdade (ver o comentario de `_contasCadastro` no gestao.js).
PARCEIROS = [
    {"id": i, "nome": c["parceiro"], "casa": c["casa"], "arquivado": False}
    for i, c in enumerate(dados_demo.ELENCO, start=1)
]

CUSTO_CONTA, CUSTO_TIPSTER, CUSTO_GERAL = dados_demo.custos()
CADASTRO_TIPSTERS = dados_demo.cadastro_tipsters()


# ── Atribuicao por casa (tela Bookies; era aba do Tipster / Metodo) ─────────────────────
# Espelha `repository.casas_visao`, que na producao roda em SQL sobre `bilhetes`.
# Reimplementar aqui e' inevitavel (nao ha banco) -- e por isso as constantes
# abaixo sao copiadas com o nome original: se a regra mudar la, procure por elas.
_CASA_MIN_VOL, _CASA_SHARE, _CASA_COVER = 8, 0.10, 0.85


def _casas_visao():
    ativos = {t["nome"] for t in CADASTRO_TIPSTERS if not t["arquivado"]}
    por_casa = {}
    for r in LINHAS:
        if not r["tipster"]:
            continue
        d = por_casa.setdefault(r["casa"], {"total": 0, "dist": {}})
        d["total"] += 1
        d["dist"][r["tipster"]] = d["dist"].get(r["tipster"], 0) + 1
    saida = []
    for casa, d in por_casa.items():
        total = d["total"]
        dist = sorted(d["dist"].items(), key=lambda x: -x[1])
        top_nome, top_n = dist[0]
        donos = [n for n, k in dist if n in ativos and k / total >= _CASA_SHARE][:2]
        cobertura = sum(d["dist"][n] for n in donos) / total if donos else 0
        if total < _CASA_MIN_VOL:
            sug_modo, sug_tipsters = None, []
        elif donos and cobertura >= _CASA_COVER:
            sug_modo, sug_tipsters = "dedicada", donos
        else:
            sug_modo, sug_tipsters = "multi", []
        saida.append({
            "casa": casa, "total": total, "n_tipsters": len(d["dist"]),
            "top": top_nome, "top_share": round(100 * top_n / total),
            "sugestao_modo": sug_modo, "sugestao_tipsters": sug_tipsters,
            # `modo=None` = casa ainda NAO curada. Deixamos a maioria assim de
            # proposito: a tela tem um botao "Aplicar N sugestoes" que so aparece
            # com pendencia, e print sem ele esconderia o recurso.
            "modo": None, "tipsters": "", "origem": None,
        })
    saida.sort(key=lambda x: -x["total"])
    # Duas casas ja CURADAS, para o print mostrar os tres estados (dedicada,
    # compartilhada, a definir) em vez de uma coluna so. A curadoria copia a
    # sugestao que a regra acima produziu -- nunca inventa um modo que o dado
    # nao sustenta, que seria print mentiroso.
    for c in saida:
        if c["casa"] == "BETesporte" and c["sugestao_modo"] == "dedicada":
            c.update({"modo": "dedicada", "tipsters": ", ".join(c["sugestao_tipsters"]),
                      "origem": "sharpen"})
        elif c["casa"] == "Bet365" and c["sugestao_modo"] == "multi":
            c.update({"modo": "multi", "tipsters": "", "origem": "custom"})
    return saida


CASAS_VISAO = _casas_visao()

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
def parceiros(casa: str = None, arquivados: bool = False):
    """`casa` FILTRA -- e ignorar isso foi o bug das 2.958 contas (s294).

    A rota de producao e' `list_parceiros(dono, casa=casa or None, ...)`: o Painel
    de Contas pede uma vez POR CASA e conta o que volta. O mock devolvia a lista
    inteira em toda chamada, entao cada uma das 29 casas exibia as 102 contas e o
    total virava 102 x 29. O STATUS registrava esse numero como "medido, nao
    diagnosticado" e mandava conferir a forma do payload antes de mexer no front
    -- estava certo: o front nunca teve defeito nenhum aqui.
    """
    if casa:
        return {"parceiros": [p for p in PARCEIROS if p["casa"] == casa]}
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


# ── Camada de OPERACAO: custos, cadastro de tipster e atribuicao por casa ────
# Ate a s294 este bloco devolvia forma valida e VAZIA. Funcionava para nao quebrar
# a tela, mas custo R$ 0 deixa o "P/L Liquido" identico ao bruto e as abas de custo
# em branco -- ou seja, o print escondia exatamente a camada que separa o Sharpen
# de um app de apostador individual. Agora tudo aqui vem do `dados_demo`.
@app.get("/casas/config")
def casas_config():
    return {"casas": CASAS_VISAO}


@app.get("/casas/meta")
def casas_meta():
    return {"meta": {}}


@app.get("/custos/conta")
def custos_conta():
    # `existe` False faz o front cair no cache do navegador e ignorar o servidor.
    return {"existe": True, "custo_conta": CUSTO_CONTA}


@app.get("/custos/store")
def custos_store():
    return {"existe": True, "custo_tipster": CUSTO_TIPSTER, "custo_geral": CUSTO_GERAL}


@app.get("/tipsters/cadastro")
def tipsters_cadastro(arquivados: bool = False):
    return {"tipsters": CADASTRO_TIPSTERS}


@app.get("/tipsters/unidades")
def tipsters_unidades(tipster: str = ""):
    return {"escada": []}


@app.get("/tipsters/escadas")
def tipsters_escadas():
    return {"escadas": {}}


@app.get("/taxonomia")
def taxonomia():
    # Esportes e categorias canonicos. Na producao saem dos MASTER via
    # `app/taxonomia.py`; aqui bastam os do feed -- a tela usa a UNIAO dos dois e
    # o que importa no print e' o menu ter conteudo, nao ser a lista inteira.
    return {
        "esportes": sorted({r["esporte"] for r in LINHAS}),
        "categorias": sorted({r["aposta"] for r in LINHAS}),
    }


@app.get("/mercados")
def mercados():
    return {"mercados": sorted({r["aposta"] for r in LINHAS})}


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
