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
import os
import pathlib
import re
import sys
import time
from datetime import datetime, timedelta

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dados_demo  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parents[2]
ESTATICO = RAIZ / "app" / "static"

LINHAS = dados_demo.gerar()
RESUMO = dados_demo.resumo(LINHAS)

# Latencia simulada do PATCH de bilhete (ver `patch_bilhete`). 70 ms e' a faixa do
# round-trip real em producao; em localhost seria ~2 ms.
LATENCIA_PATCH_S = int(os.environ.get("DEMO_LATENCIA_PATCH_MS", "70")) / 1000.0

app = FastAPI(title="Sharpen — servidor de demonstração", docs_url=None, redoc_url=None)


# ── Contas: vem do ELENCO, nunca derivadas do feed ───────────────────────────
# Ate a s294 esta funcao varria as apostas e criava uma conta para cada par
# (parceiro, casa) que aparecesse. Como o gerador sorteava pessoa e casa de forma
# independente, o resultado eram 1.830 contas contra as 102 reais -- e a tela de
# Fornecedores repetia essa lista embaixo de cada casa. O erro nao era de contagem,
# era de DIRECAO: na producao a conta e' uma linha de `parceiros` e a aposta aponta
# para ela; aqui a aposta estava inventando a conta. Agora o cadastro e' a fonte,
# como no sistema de verdade (ver o comentario de `_contasCadastro` no gestao.js).
# Janela de vida da conta (s322): a rota de producao devolve `adquirida_em` e
# `arquivada_em`, e e' delas que sai o Custo de Contas de cada periodo filtrado. O mock
# precisa das duas -- sem `adquirida_em` o front cai no comeco de janela inferido (a 1a
# aposta) e a demo passa a mostrar um custo diferente do que a producao mostraria.
# A demo compra a conta 30 dias antes da 1a aposta dela; nenhuma conta e' arquivada.
_1A_APOSTA = {}
# Ultima captura da conta (s333): na producao e' o maior `criado_em` dos bilhetes
# daquela conta, e e' dela que sai a tag `Parada ha N dias` e a coluna do degrau de
# 32". Aqui usamos a data da aposta -- a demo nao tem `criado_em`, e para o efeito
# que a tela mostra (conta ativa que parou de produzir) as duas contam a mesma
# historia.
_ULT_APOSTA = {}
for _l in LINHAS:
    _k = (_l["casa"], _l["parceiro"])
    _d = _l.get("data") or ""
    if _d and (_k not in _1A_APOSTA or _d < _1A_APOSTA[_k]):
        _1A_APOSTA[_k] = _d
    if _d and (_k not in _ULT_APOSTA or _d > _ULT_APOSTA[_k]):
        _ULT_APOSTA[_k] = _d


def _comprada_em(casa, parceiro):
    d = _1A_APOSTA.get((casa, parceiro))
    if not d:
        return None
    return (datetime.strptime(d, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")


PARCEIROS = [
    {"id": i, "nome": c["parceiro"], "casa": c["casa"], "arquivado": False,
     "adquirida_em": _comprada_em(c["casa"], c["parceiro"]), "arquivada_em": None}
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
    # Curadoria vencida (s310) — espelha `repository.casas_visao`. Aqui dá SEMPRE falso, porque a
    # curadoria acima copia a sugestão que a própria regra produziu; o campo existe para a tela
    # não receber `undefined` e para o print continuar mostrando o produto, não uma maquete.
    for c in saida:
        curados = [t.strip() for t in (c["tipsters"] or "").split(",") if t.strip()]
        c["curadoria_vencida"] = bool(c["modo"] == "dedicada" and c["sugestao_modo"] == "multi")
        c["fora_do_pool"] = (sum(n for nm, n in por_casa[c["casa"]]["dist"].items()
                                 if nm not in curados) if c["curadoria_vencida"] else 0)
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


# ── Grade da Extração (s331) ─────────────────────────────────────────────────
# Ate aqui `/bilhetes` devolvia lista VAZIA para qualquer conta: so respondia ao
# filtro `extraction_state=aberta`. A tela de Extracao ficava com a grade em
# "Nenhum bilhete salvo", os KPIs da conta zerados e o botao "Sugerir tipsters"
# sem nada para sugerir -- ou seja, o print/clipe mostrava a moldura do produto e
# escondia o produto. Este bloco monta o MESMO contrato de `list_bilhetes`
# (repository.py) sobre a base ficticia, por conta.
#
# Tres diferencas de forma em relacao ao feed, e as tres importam para a tela:
#   · `data` em DD/MM/AAAA -- e' assim que a coluna `bilhetes.data` guarda em
#     producao, e o `_dataRevisao` do front so reconhece esse formato;
#   · `stake`/`odd` em texto pt-BR (virgula decimal) -- o front parseia com
#     `_numBR`; numero cru viraria NaN na assinatura de stake do matcher;
#   · `pl` derivado (nunca persistido) e `resultado` VAZIO na aposta aberta,
#     com `extraction_state='aberta'` -- e' esse par que alimenta o badge ambar.
sys.path.insert(0, str(RAIZ / "app"))
from repository import _caixa_projetar, _resumir_apostas  # noqa: E402


def _br(v, casas=2):
    """Numero -> texto pt-BR (virgula decimal), como o banco guarda."""
    return f"{float(v):.{casas}f}".replace(".", ",")


def _data_br(iso):
    a, m, d = (iso or "0000-00-00").split("-")
    return f"{d}/{m}/{a}"


def _linha_grade(r):
    aberta = r["resultado"] == "ABERTA"
    return {
        "id": r["id"],
        "data": _data_br(r["data"]),
        "esporte": r["esporte"],
        "tipster": r["tipster"] or "",
        "casa": r["casa"],
        "parceiro": r["parceiro"],
        "aposta": r["aposta"],
        "descricao": r["descricao"],
        "stake": _br(r["stake"]),
        "odd": _br(r["odd"], 3),
        "resultado": "" if aberta else r["resultado"],
        "pl": None if aberta else round(r["lucro"], 2),
        "extraction_state": "aberta" if aberta else "resolvida",
        "arquivado": False,
        "codigo_bilhete": f"DM{r['id']}",
        "origem": "demo",
    }


GRADE = [_linha_grade(r) for r in LINHAS_FEED]
# Indice por conta: a grade SEMPRE pergunta por (casa, parceiro), nunca pela base
# inteira -- e' o isolamento por conta que a tela de Extracao assume.
GRADE_POR_CONTA = {}
for _g in GRADE:
    GRADE_POR_CONTA.setdefault((_g["casa"], _g["parceiro"]), []).append(_g)
GRADE_POR_ID = {g["id"]: g for g in GRADE}


def _sem_tipster(b):
    return not (b.get("tipster") or "").strip()


# ── Matcher por evidencia (espelha `main.sugerir_tipsters_route`) ────────────
# O modelo e' treinado sobre os rotulos HUMANOS da base ficticia (aqui: tudo que
# nao veio do proprio botao, isto e' `origem_tipster != 'sugerido'`) -- mesma
# regra do `repository.rotulos_humanos`, e pelo mesmo motivo: treinar no proprio
# chute ensina o sistema a repetir o erro dele.
import matcher  # noqa: E402

# `dominio_esportes` sem SQL: para cada esporte, quem e' o maior tipster nele,
# quantos sao dele e quantos o esporte tem (contrato de `matcher.dono_do_esporte`).
_tot_esp, _cont_esp = {}, {}
for _g in GRADE:
    _e, _t = (_g["esporte"] or "").strip().lower(), (_g["tipster"] or "").strip()
    if not _e or not _t:
        continue
    _tot_esp[_e] = _tot_esp.get(_e, 0) + 1
    _cont_esp[(_e, _t)] = _cont_esp.get((_e, _t), 0) + 1
_melhor_esp = {}
for (_e, _t), _n in _cont_esp.items():
    if _n > _melhor_esp.get(_e, ("", 0))[1]:
        _melhor_esp[_e] = (_t, _n)
_DOMINIO_ESPORTES = {e: (_melhor_esp[e][0], _melhor_esp[e][1], _tot_esp[e]) for e in _tot_esp}

# Casas curadas como DEDICADA (slug -> tipsters). Curadoria humana crava antes do
# modelo, igual em producao (`repository.casas_dedicadas`).
_CASAS_DEDICADAS = {
    re.sub(r"\s+", "", c["casa"].strip().lower()):
        [t.strip() for t in (c["tipsters"] or "").split(",") if t.strip()][:2]
    for c in CASAS_VISAO if c["modo"] == "dedicada" and c["tipsters"]
}


def _modelo_matcher():
    """Modelo treinado, com o cache de 5 min do proprio `matcher` (TTL_MODELO).
    O PATCH invalida (`matcher.invalidar`) para o rotulo novo entrar no lote
    seguinte -- e' o comportamento de producao, nao um atalho da demo."""
    m = matcher.modelo_em_cache(dados_demo.DONO)
    if m is None:
        m = matcher.treinar([g for g in GRADE if g.get("origem_tipster") != "sugerido"])
        matcher.guardar_modelo(dados_demo.DONO, m)
    return m


def _aaaammdd(b):
    """DD/MM/AAAA -> inteiro AAAAMMDD (comparavel). Data malformada vai para o fim."""
    d = b["data"]
    try:
        return int(f"{d[6:10]}{d[3:5]}{d[0:2]}")
    except ValueError:
        return 0


def _ordenar_grade(linhas, order):
    """Espelha o ORDER BY de `list_bilhetes`. `data_desc` = grade da Extracao:
    ABERTAS no topo, depois resolvidas por data do EVENTO desc, id desc no empate.
    O menos no numero e' o que faz o desc -- ordenar string de data por reverse
    inverteria tambem o grupo das abertas, que tem de ficar em cima."""
    if order == "data_desc":
        return sorted(linhas, key=lambda b: (0 if not b["resultado"] else 1,
                                             -_aaaammdd(b), -b["id"]))
    return sorted(linhas, key=lambda b: b["id"], reverse=(order != "asc"))


@app.get("/me")
def me():
    """Dono COM operadores (s331).

    Estava `operadores: []`, e com a lista vazia a casca nao desenha o trocador
    "Ver base de" no rodape da sidebar. A landing precisa mostrar operacao em
    equipe, e nao da para fotografar um controle que nasce escondido.

    Os nomes sao ficticios, como o resto da base."""
    return {"usuario": dados_demo.DONO, "dono_efetivo": dados_demo.DONO,
            "operadores": [dados_demo.DONO, "Marina", "Téo"]}


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
def bilhetes(casa: str = "", parceiro: str = "", extraction_state: str = "",
             archived: str = "", limit: int = 100, offset: int = 0,
             order: str = "desc", pendencia: str = ""):
    """Espelha `list_bilhetes` + `contar_bilhetes` sobre a base ficticia.

    Sem `casa`/`parceiro` a resposta continua sendo a lista de ABERTAS (e' o que a
    tela inicial pede, com `extraction_state=aberta` e sem conta): o painel "Em
    aberto" da home nao filtra por conta e regredi-lo quebraria o print da home.
    """
    if not casa and not parceiro:
        if extraction_state == "aberta":
            return {"bilhetes": ABERTAS_BILHETES, "total": len(ABERTAS_BILHETES)}
        return {"bilhetes": [], "total": 0, "arquivados": 0}

    linhas = GRADE_POR_CONTA.get((casa, parceiro), [])
    if extraction_state:
        linhas = [b for b in linhas if b["extraction_state"] == extraction_state]
    # `pendencia` usa o MESMO predicado que produz o numero do badge (ver
    # `/incompletos`): badge dizendo 7 com a grade mostrando 5 e' o defeito que a
    # s262 registrou, e ele nasce justamente de dois predicados diferentes.
    if pendencia == "sem_tipster":
        linhas = [b for b in linhas if _sem_tipster(b)]
    total = len(linhas)
    linhas = _ordenar_grade(linhas, order)[offset:offset + max(1, min(limit, 1000))]
    return {"bilhetes": linhas, "total": total, "arquivados": 0,
            "limit": limit, "offset": offset}


class _PatchBilhete(BaseModel):
    tipster: str | None = None
    origem_tipster: str | None = None
    esporte: str | None = None
    aposta: str | None = None
    descricao: str | None = None
    data: str | None = None
    stake: str | None = None
    odd: str | None = None
    resultado: str | None = None
    casa: str | None = None
    parceiro: str | None = None


@app.patch("/bilhetes/{bid}")
def patch_bilhete(bid: int, body: _PatchBilhete):
    """Edicao de campo na grade -- grava EM MEMORIA (o demo nao tem banco).

    Existe pelo botao "Sugerir tipsters": ele chama `salvarTipsterVal` uma vez por
    bilhete e faz ROLLBACK visual quando o PATCH falha. Sem esta rota o clipe
    mostraria a coluna preenchendo e voltando a vazio, que e' pior que nao mostrar.
    """
    # Latencia deliberada. Em producao cada PATCH e' um round-trip HTTP + Postgres
    # (dezenas de ms); em 127.0.0.1 sao ~2 ms, e as 30 linhas do "Sugerir tipsters"
    # preenchiam num piscar -- o clipe mostrava a coluna cheia sem mostrar o
    # preenchimento. Nao e' enfeite: e' o tempo que a rota REALMENTE leva no ar.
    # Zere com DEMO_LATENCIA_PATCH_MS=0 se estiver depurando outra coisa.
    if LATENCIA_PATCH_S:
        time.sleep(LATENCIA_PATCH_S)
    b = GRADE_POR_ID.get(bid)
    if not b:
        return JSONResponse({"detail": "Bilhete não encontrado."}, status_code=404)
    for campo, valor in body.model_dump(exclude_none=True).items():
        b[campo] = valor
    if body.tipster is not None:
        # Rotulo novo invalida o modelo, como em producao: a proxima chamada
        # retreina ja com a correcao humana dentro.
        matcher.invalidar(dados_demo.DONO)
    return {"ok": True, "bilhete": b}


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
    """Espelha `contar_incompletos`: pendencia por casa+parceiro.

    `por_parceiro` faltava, e sem ele o badge azul "Aguardando tipster" da barra da
    conta nascia com 0 e ficava `hidden` -- ou seja, o filtro que existe justamente
    para achar as linhas sem tipster nao aparecia na tela.
    """
    por_parceiro, por_casa_t, por_casa_a = [], {}, {}
    for (casa, parceiro), linhas in GRADE_POR_CONTA.items():
        sem_tip = sum(1 for b in linhas if _sem_tipster(b))
        abertas = sum(1 for b in linhas if b["extraction_state"] == "aberta")
        if not sem_tip and not abertas:
            continue
        por_parceiro.append({"casa": casa, "parceiro": parceiro,
                             "sem_tipster": sem_tip, "abertas": abertas})
        por_casa_t[casa] = por_casa_t.get(casa, 0) + sem_tip
        por_casa_a[casa] = por_casa_a.get(casa, 0) + abertas
    return {"por_parceiro": por_parceiro, "por_casa_tipster": por_casa_t,
            "por_casa_aberta": por_casa_a}


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


# ── Preco do fornecedor com vigencia (s348, Fatia 1) ─────────────────────────
# Em memoria, porque o demo nao tem banco. A regra de qual preco vale numa data e
# a MESMA do repositorio: o ultimo degrau que ja comecou.
_PRECOS = []
_PRECO_SEQ = [0]


def _preco_vigente_demo(fornecedor, casa, quando):
    validos = [p for p in _PRECOS
               if p["fornecedor"] == fornecedor and p["casa"] == casa
               and p["vigente_desde"] <= quando]
    if not validos:
        return None
    return max(validos, key=lambda p: p["vigente_desde"])["valor"]


def _espelhar_demo(fornecedor, casa):
    hoje = datetime.now().date().isoformat()
    v = _preco_vigente_demo(fornecedor, casa, hoje)
    k = f"{fornecedor}||{casa}"
    if v is None:
        CUSTO_CONTA.pop(k, None)
    else:
        CUSTO_CONTA[k] = v
    return v


@app.get("/custos/fornecedor")
def listar_precos_fornecedor_demo():
    return {"precos": sorted(_PRECOS, key=lambda p: (p["fornecedor"], p["casa"],
                                                     p["vigente_desde"]), reverse=False)}


class PrecoFornecedorDemo(BaseModel):
    fornecedor: str
    casa: str
    valor: float | str
    vigente_desde: str


@app.post("/custos/fornecedor")
def registrar_preco_fornecedor_demo(body: PrecoFornecedorDemo):
    forn = (body.fornecedor or "").strip()
    casa = (body.casa or "").strip()
    if not forn or not casa:
        return JSONResponse({"detail": "fornecedor e casa sao obrigatorios"}, status_code=400)
    try:
        v = float(str(body.valor).replace(",", "."))
    except ValueError:
        return JSONResponse({"detail": "valor invalido"}, status_code=400)
    if v <= 0:
        return JSONResponse({"detail": "o preco tem de ser maior que zero"}, status_code=400)
    try:
        datetime.strptime(body.vigente_desde, "%Y-%m-%d")
    except ValueError:
        return JSONResponse({"detail": "data invalida"}, status_code=400)

    for p in _PRECOS:
        if (p["fornecedor"], p["casa"], p["vigente_desde"]) == (forn, casa, body.vigente_desde):
            p["valor"] = v
            break
    else:
        _PRECO_SEQ[0] += 1
        _PRECOS.append({"id": _PRECO_SEQ[0], "fornecedor": forn, "casa": casa,
                        "valor": v, "vigente_desde": body.vigente_desde})
    return {"fornecedor": forn, "casa": casa, "valor": v,
            "vigente_desde": body.vigente_desde, "vigente_hoje": _espelhar_demo(forn, casa)}


@app.delete("/custos/fornecedor/{preco_id}")
def remover_preco_fornecedor_demo(preco_id: int):
    alvo = next((p for p in _PRECOS if p["id"] == preco_id), None)
    if alvo is None:
        return JSONResponse({"detail": "preco nao encontrado"}, status_code=404)
    _PRECOS.remove(alvo)
    _espelhar_demo(alvo["fornecedor"], alvo["casa"])
    return {"removido": True}


@app.get("/tipsters/cadastro")
def tipsters_cadastro(arquivados: bool = False):
    return {"tipsters": CADASTRO_TIPSTERS}


@app.post("/bilhetes/lote")
def bilhetes_lote_demo(body: dict = None):
    """Espelha `main.editar_bilhetes_lote`. Demo nao escreve: devolve o FORMATO da
    resposta (contagem + avisos) para o front seguir o fluxo inteiro na captura."""
    ids = (body or {}).get("ids") or []
    return {"atualizados": len(ids), "ignorados": [], "total": len(ids)}


@app.get("/tipsters/{tipster_id}/resumo")
def tipster_resumo_demo(tipster_id: int):
    """Espelha `main.resumo_tipster_route`: o que o rename vai tocar, contado na base.

    Existe aqui porque o modal de confirmacao ABRE com este numero -- sem a rota ele
    cairia no ramo "nao consegui contar" e o print sairia mostrando o caso de erro."""
    t = next((x for x in CADASTRO_TIPSTERS if x["id"] == tipster_id), None)
    if not t:
        return JSONResponse({"detail": "Tipster nao encontrado."}, status_code=404)
    nome = t["nome"]
    n = sum(1 for l in LINHAS if l.get("tipster") == nome)
    return {"id": tipster_id, "nome": nome, "arquivado": bool(t.get("arquivado")),
            "n_bilhetes": n, "n_unidades": 2, "n_polymarket": 0,
            "n_casas_config": 1, "tem_custo": True}


@app.post("/tipsters/{tipster_id}/renomear")
def tipster_renomear_demo(tipster_id: int):
    """Demo nao escreve: devolve o formato da resposta para o front seguir o fluxo."""
    return {"ok": True, "nome": "", "bilhetes_atualizados": 0, "unidades": 0,
            "polymarket": 0, "casas_config": 0, "custo_movido": False}


class _SugBilhete(BaseModel):
    id: str
    casa: str = ""
    esporte: str = ""
    aposta: str = ""
    stake: str = ""
    descricao: str = ""


class _SugRequest(BaseModel):
    bilhetes: list[_SugBilhete] = []


@app.post("/tipsters/sugerir")
def sugerir_tipsters_demo(body: _SugRequest):
    """Espelha a rota de producao (`main.sugerir_tipsters_route`) chamando o MESMO
    `app/matcher.py` -- Naive-Bayes treinado no que o dono ja rotulou.

    Sem esta rota o `fetch` do front dava 405, `_sugPeloServidor` devolvia `null` e
    a tela caia no matcher DECLARATIVO do `index.html`. O declarativo e' a rede de
    segurança para dono novo, nao o caminho principal: ele so decide quando o
    perfil e' exclusivo no mercado, o que aqui cobria 9 de 30 linhas. A demo
    mostrava o botao rodando o caminho de fallback.

    READ-ONLY, como em producao: quem grava e' o PATCH de cada bilhete.
    """
    if not body.bilhetes:
        return {"sugestoes": {}, "fonte": "evidencia", "treino": 0}
    modelo = _modelo_matcher()
    ativos = [t["nome"] for t in CADASTRO_TIPSTERS if not t["arquivado"]]
    ativos_set = set(ativos)
    fonte = "evidencia" if modelo.treino >= matcher.MIN_TREINO else "declarativo"
    sugestoes = {}
    for b in body.bilhetes:
        dono_casa = _CASAS_DEDICADAS.get(re.sub(r"\s+", "", b.casa.strip().lower()), [])
        if len(dono_casa) == 1 and dono_casa[0] in ativos_set:
            sugestoes[b.id] = dono_casa[0]
            continue
        if fonte != "evidencia":
            dono_esp = matcher.dono_do_esporte(_DOMINIO_ESPORTES, b.esporte, ativos)
            if dono_esp:
                sugestoes[b.id] = dono_esp
            continue
        pool = [n for n in dono_casa if n in ativos_set] if len(dono_casa) == 2 else ativos
        nome = matcher.sugerir(modelo, pool, b.casa, b.esporte, b.aposta, b.stake,
                               b.descricao, dominio=_DOMINIO_ESPORTES)
        if nome:
            sugestoes[b.id] = nome
    return {"sugestoes": sugestoes, "fonte": fonte, "treino": modelo.treino,
            "novatos": matcher.novatos(modelo, ativos) if fonte == "evidencia" else [],
            "folga_declarada": matcher.FOLGA_DECLARADA}


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
def conta_resumo(casa: str = "", parceiro: str = ""):
    """Faixa de KPIs da conta ativa (P/L, turnover, apostas, win rate, ROI…).

    A matematica NAO e' reimplementada: `_resumir_apostas` e' o mesmo codigo de
    producao (`repository.resumo_conta` so busca as linhas e delega). Antes daqui a
    rota devolvia `{"resumo": {}}` e a faixa saia com tudo zerado -- oito tiles
    dizendo 0 em cima de uma conta com centenas de apostas.
    """
    return _resumir_apostas(GRADE_POR_CONTA.get((casa, parceiro), []))


@app.get("/polymarket/dashboard")
def poly():
    return {"data": []}


# ── Caixa (s314) ─────────────────────────────────────────────────────────────
# Aqui a matematica NAO e' reimplementada: importamos o `_caixa_projetar` de
# producao e so inventamos os lancamentos. E' a parte do arquivo que mais correria
# risco de divergir em silencio -- projecao de saldo errada num print de venda e'
# pior que print nenhum.
# (`_caixa_projetar` e' importado la em cima, junto com `_resumir_apostas`.)
_HOJE = datetime.now().date()


def _d(dias):
    return (_HOJE - timedelta(days=dias)).isoformat()


def _mov(mid, tipo, dias, valor, **kw):
    return {"id": mid, "tipo": tipo, "data": _d(dias), "valor": valor,
            "obs": kw.get("obs", ""), "projetado": kw.get("projetado"),
            "abertas_corte": None,
            "criado_em": (datetime.now() - timedelta(days=dias)).isoformat()}


# Tres contas com caixa: uma que confere, uma nunca conferida e uma com divergencia
# ABERTA -- um print com tudo verde esconderia o recurso que a Caixa existe para dar.
CAIXA_DEMO = {
    1: [_mov(1, "inicial", 32, 3000.0), _mov(2, "deposito", 27, 1500.0, obs="PIX"),
        _mov(3, "saque", 19, 800.0), _mov(4, "ajuste", 13, 50.0, obs="bônus de recarga")],
    2: [_mov(6, "inicial", 24, 1800.0), _mov(7, "deposito", 11, 700.0, obs="PIX")],
    3: [_mov(8, "inicial", 40, 5000.0), _mov(9, "saque", 21, 1200.0)],
}
# A conferencia entra DEPOIS, com o numero que a propria projecao produziu (ver
# `_semear_conferencias`). Cravar `valor`/`projetado` a mao dava um box verde
# dizendo "diferenca R$ 0,00" ao lado de um "Saldo disponivel projetado" de outro
# valor: a base ficticia e' gerada relativa a HOJE, entao qualquer numero fixo
# aqui envelhece em um dia. Print de tela de CONFERENCIA que nao confere consigo
# mesma e' o pior lugar possivel para um numero desencontrado.
_CONFERENCIAS = [(1, 0, 0.0), (3, 2, -850.0)]   # (parceiro_id, dias atras, divergencia)


def _espalhar_caixa():
    """Liga a Caixa em mais contas, distribuidas entre as casas (s331).

    Escolhe ATE 2 contas por casa, nas casas com mais contas, e pula as quatro
    que ja tem semente propria. O saldo inicial vem do id da conta para ficar
    estavel entre execucoes: base de demonstracao que muda de numero a cada boot
    torna print antigo e print novo incomparaveis.

    A cada tres contas ligadas, uma fica sem conferencia (estado `nunca`) e uma
    fica divergente. Sem essa mistura o Painel sai com uma tag so repetida em
    todas as linhas, que e' o defeito que o redesenho da s330 existiu para matar.
    """
    ja = set(CAIXA_DEMO)
    por_casa = {}
    for p in PARCEIROS:
        por_casa.setdefault(p["casa"], []).append(p)
    casas = sorted(por_casa.values(), key=len, reverse=True)

    mid = 300
    novos = []
    for contas in casas:
        for p in contas[:2]:
            if p["id"] in ja or len(novos) >= 22:
                continue
            novos.append(p["id"])
    for n, pid in enumerate(novos):
        inicial = 1200.0 + (pid % 17) * 250.0
        movs = [_mov(mid, "inicial", 45, inicial)]
        mid += 1
        if pid % 3 == 0:
            movs.append(_mov(mid, "deposito", 20, 500.0 + (pid % 7) * 100.0, obs="PIX"))
            mid += 1
        CAIXA_DEMO[pid] = movs
        # 1 em 3 fica sem conferencia; 1 em 7 diverge. O resto confere.
        if n % 3 == 1:
            continue
        div = -120.0 - (pid % 5) * 40.0 if n % 7 == 3 else 0.0
        _CONFERENCIAS.append((pid, n % 4, div))


_espalhar_caixa()


# Caso REAL da conta #748 (s314), remontado aqui: 12 perdas de ontem, corte de hoje
# e uma aposta que estava ABERTA no corte e liquidou W. E' o caso que fez o Feca dizer
# "o resultado nao esta sendo contabilizado" -- e o unico jeito de ver a tela explicar
# isso e' ter o caso na bancada.
_ONTEM = _d(1)
CAIXA_FIXTURE = {
    4: [{"id": 90001, "data": _ONTEM, "stake": "100,00", "odd": "12,28684", "resultado": "W"}]
       + [{"id": 90002 + i, "data": _ONTEM, "stake": "200,00", "odd": "27,45", "resultado": "L"}
          for i in range(12)],
}
CAIXA_DEMO[4] = [_mov(20, "inicial", 0, 1950.0, obs="Deposito Inicial")]
CAIXA_DEMO[4][0]["abertas_corte"] = [90001]


def _apostas_da_conta(pid):
    if pid in CAIXA_FIXTURE:
        return CAIXA_FIXTURE[pid]
    p = next((x for x in PARCEIROS if x["id"] == pid), None)
    if not p:
        return []
    return [{"id": 10_000 + i, "data": r["data"], "stake": r["stake"],
             "odd": r.get("odd"), "resultado": "" if r["resultado"] == "ABERTA" else r["resultado"]}
            for i, r in enumerate(LINHAS)
            if r["casa"] == p["casa"] and r["parceiro"] == p["nome"]]


def _caixa_de(pid):
    res = _caixa_projetar(CAIXA_DEMO.get(pid, []), _apostas_da_conta(pid))
    p = next((x for x in PARCEIROS if x["id"] == pid), None)
    res.update({"parceiro_id": pid, "casa": p["casa"] if p else "",
                "parceiro": p["nome"] if p else "", "movimentos": CAIXA_DEMO.get(pid, [])})
    return res


def _semear_conferencias():
    """Fecha a conferencia de cada conta com o `disponivel` que a projecao acabou
    de calcular, mais a divergencia desejada. Roda uma vez, no boot."""
    for pid, dias, div in _CONFERENCIAS:
        projetado = round(_caixa_de(pid)["disponivel"], 2)
        CAIXA_DEMO[pid].append(_mov(900 + pid, "conferencia", dias,
                                    round(projetado + div, 2), projetado=projetado))


_semear_conferencias()


@app.get("/caixa/conta")
def caixa_conta_demo(parceiro_id: int):
    return _caixa_de(parceiro_id)


class _CaixaLancar(BaseModel):
    parceiro_id: int
    tipo: str
    data: str
    valor: float
    obs: str | None = None


@app.post("/caixa/lancar")
def caixa_lancar_demo(body: _CaixaLancar):
    """Grava EM MEMORIA (o demo nao tem banco). Existe para o fluxo de ativar/lancar
    poder ser exercido num navegador de verdade antes do commit -- foi um clique que
    "nao fazia nada" em producao que abriu esta rota."""
    iso = body.data if len(body.data) == 10 and body.data[4] == "-" else (
        f"{body.data[6:10]}-{body.data[3:5]}-{body.data[0:2]}" if "/" in body.data else body.data)
    movs = CAIXA_DEMO.setdefault(body.parceiro_id, [])
    novo = {"id": 900 + len(movs), "tipo": body.tipo, "data": iso, "valor": round(body.valor, 2),
            "obs": (body.obs or "").strip(), "projetado": None, "abertas_corte": None,
            "criado_em": datetime.now().isoformat()}
    if body.tipo == "inicial":
        movs[:] = [m for m in movs if m["tipo"] != "inicial"]
    elif body.tipo == "conferencia":
        novo["projetado"] = _caixa_de(body.parceiro_id)["disponivel"]
    movs.append(novo)
    return {"ok": True, "caixa": _caixa_de(body.parceiro_id)}


class _CaixaEditar(BaseModel):
    data: str
    valor: float
    obs: str | None = None


@app.patch("/caixa/movimento/{mov_id}")
def caixa_editar_demo(mov_id: int, body: _CaixaEditar):
    for pid, movs in CAIXA_DEMO.items():
        for m in movs:
            if m["id"] == mov_id:
                d = body.data
                m["data"] = d if (len(d) == 10 and d[4] == "-") else (
                    f"{d[6:10]}-{d[3:5]}-{d[0:2]}" if "/" in d else d)
                m["valor"] = round(body.valor, 2)
                m["obs"] = (body.obs or "").strip()
                return {"ok": True, "tipo": m["tipo"], "caixa": _caixa_de(pid)}
    return JSONResponse({"detail": "Lançamento não encontrado."}, status_code=404)


@app.delete("/caixa/movimento/{mov_id}")
def caixa_excluir_demo(mov_id: int):
    for pid, movs in CAIXA_DEMO.items():
        if any(m["id"] == mov_id for m in movs):
            movs[:] = [m for m in movs if m["id"] != mov_id]
            return {"ok": True, "caixa": _caixa_de(pid)}
    return JSONResponse({"detail": "Lançamento não encontrado."}, status_code=404)


@app.get("/caixa/visao")
def caixa_visao_demo():
    contas, casas = [], {}
    tot = {"banca": 0.0, "disponivel": 0.0, "aberto": 0.0,
           "contas": 0, "ligadas": 0, "sem_caixa": 0, "a_conferir": 0}
    for p in PARCEIROS:
        r = _caixa_de(p["id"])
        contas.append({"parceiro_id": p["id"], "casa": p["casa"], "parceiro": p["nome"],
                       "arquivado": False, "ligada": r["ligada"], "estado": r["estado"],
                       "banca": r["banca"], "disponivel": r["disponivel"],
                       "aberto": r["aberto"], "divergencia": r["divergencia"],
                       "conferencia": r["conferencia"],
                       "ultima_captura": _ULT_APOSTA.get((p["casa"], p["nome"]))})
        c = casas.setdefault(p["casa"], {"casa": p["casa"], "contas": 0, "ligadas": 0,
                                         "sem_caixa": 0, "banca": 0.0, "disponivel": 0.0,
                                         "aberto": 0.0, "a_conferir": 0, "conferencia": None})
        c["contas"] += 1
        tot["contas"] += 1
        if not r["ligada"]:
            c["sem_caixa"] += 1
            tot["sem_caixa"] += 1
            continue
        c["ligadas"] += 1
        tot["ligadas"] += 1
        for k in ("banca", "disponivel", "aberto"):
            c[k] += r[k]
            tot[k] += r[k]
        if r["estado"] == "divergente":
            c["a_conferir"] += 1
            tot["a_conferir"] += 1
        if r["conferencia"]:
            c["conferencia"] = r["conferencia"]["data"]
    for c in casas.values():
        for k in ("banca", "disponivel", "aberto"):
            c[k] = round(c[k], 2)
    for k in ("banca", "disponivel", "aberto"):
        tot[k] = round(tot[k], 2)
    return {"casas": sorted(casas.values(), key=lambda c: (-c["banca"], c["casa"])),
            "contas": contas, "totais": tot}


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
