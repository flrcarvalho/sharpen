"""O Monte Carlo tem de rodar FORA da thread principal — e continuar rodando.

Incidente da s217. O dashboard tinha um Web Worker justamente para o bootstrap de
Monte Carlo (~300 milhões de iterações com a base cheia) não congelar a tela. Ele
parou de funcionar em produção **no dia seguinte ao que nasceu** e ninguém viu:

  · 29/06 (408255f) — worker criado com `new Worker(URL.createObjectURL(blob))`;
  · 03/07 (2e835ed) — entra a CSP: `default-src 'self'`, sem `worker-src`.
    Worker de `blob:` cai no default-src → construtor BLOQUEADO.

O código tinha fallback: worker falhou, calcula síncrono. Ou seja, o número saía
certo — só que travando a aba. Medido na base do Feca (30.851 apostas): long tasks
de 52,7 s no boot do dashboard e 40 s na tela Métricas, com o Chrome oferecendo
"aguardar ou fechar a aba". Vinte e seis dias de regressão silenciosa porque a
falha era *invisível*: nada quebrava, só ficava lento.

Daí estes gates. São três regras, e cada uma pega uma forma diferente de o bug voltar:

  1. o worker é carregado de MESMA ORIGEM — ou, se um dia voltar a ser gerado em
     runtime (`blob:`), a CSP tem de declarar `worker-src` com `blob:` na MESMA
     mudança. É a implicação que estava quebrada em produção;
  2. nenhuma TELA chama o Monte Carlo síncrono (só o fallback interno do app.js pode);
  3. a matemática vive num arquivo só (mc-core.js), que a página e o worker carregam —
     duas cópias divergem, e aí "worker" e "síncrono" passam a dar números diferentes.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "app")
import main  # noqa: E402

DASH_JS = Path("app/static/dash/assets/js")
APP_JS = DASH_JS / "app.js"
MC_CORE = DASH_JS / "mc-core.js"
MC_WORKER = DASH_JS / "mc-worker.js"
DASH_HTML = Path("app/static/dash/index.html")

# As 3 funções puras do Monte Carlo: nome → onde é LEGÍTIMO defini-las.
FUNCOES_NUCLEO = ["mulberry32", "_calcMCdrawdownRaw", "_calcPValueMCraw"]


def _ler(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _sem_comentarios(codigo: str) -> str:
    """Tira comentários antes de auditar: o gate tem de ler o CÓDIGO, não a prosa
    sobre o código. Na primeira rodada este teste reprovou o app.js por causa do
    próprio comentário que diz "NUNCA VOLTAR PARA new Worker(...blob...)" — o mesmo
    falso positivo que o build das páginas de marketing deu na s214."""
    codigo = re.sub(r"/\*.*?\*/", "", codigo, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", codigo, flags=re.MULTILINE)


# ── 1) O worker precisa caber na CSP que o app realmente envia ────────────────

def test_worker_e_de_mesma_origem_ou_a_csp_permite_blob():
    """A regra que estava quebrada: worker de `blob:` exige `worker-src` na CSP.

    Não basta olhar o `new Worker(...)`: o que decide é a combinação dele com a CSP.
    Este teste lê as duas coisas e reprova a combinação impossível — que é exatamente
    a que rodou em produção por 26 dias.
    """
    app_js = _sem_comentarios(_ler(APP_JS))
    m = re.search(r"new Worker\(([^)]*)\)", app_js)
    assert m, "app.js não cria mais nenhum Worker — o Monte Carlo voltou a ser só síncrono?"
    alvo = m.group(1)

    usa_blob = "createObjectURL" in alvo or "blob" in alvo.lower()
    csp = main._CSP
    csp_permite_worker_blob = bool(re.search(r"worker-src[^;]*blob:", csp))

    if usa_blob:
        assert csp_permite_worker_blob, (
            "o worker é criado a partir de um blob, mas a CSP não declara "
            "`worker-src ... blob:` — o navegador vai BLOQUEAR o construtor e o "
            "cálculo cai calado na thread principal (regressão da s217). "
            f"CSP atual: {csp}"
        )
    else:
        assert "mc-worker.js" in alvo, (
            "o Worker deveria apontar para o arquivo de mesma origem "
            f"assets/js/mc-worker.js — veio: {alvo}"
        )
        assert MC_WORKER.exists(), "app.js aponta para mc-worker.js, que não existe"


def test_csp_nao_precisa_de_frouxidao_para_o_worker_funcionar():
    """Worker de mesma origem cabe em `script-src 'self'` — a CSP fica restrita.

    Guarda o outro lado: se alguém afrouxar a CSP "para o worker funcionar" sem
    precisar, este teste lembra que o caminho de mesma origem já resolve.
    """
    csp = main._CSP
    assert "script-src 'self'" in csp, "script-src deixou de permitir 'self'"
    assert "worker-src" not in csp, (
        "apareceu um `worker-src` na CSP — se foi para liberar blob:, prefira o "
        "worker como arquivo de mesma origem (assets/js/mc-worker.js), que não "
        "exige afrouxar nada"
    )


# ── 2) Nenhuma tela pode travar a thread principal com o Monte Carlo ──────────

@pytest.mark.parametrize("arquivo", sorted((DASH_JS / "charts").glob("*.js")), ids=lambda p: p.name)
def test_telas_nao_chamam_monte_carlo_sincrono(arquivo):
    """`calcMCdrawdown`/`calcPValueMC` bloqueiam; as telas usam `mcComputeAsync`.

    Foi assim que Métricas e o drill de tipster ficaram de fora quando a Visão Geral
    migrou para o worker: as duas seguiram chamando a versão síncrona, e cada clique
    num tipster congelava a aba por ~12 s.
    """
    codigo = _sem_comentarios(_ler(arquivo))
    for fn in ("calcMCdrawdown", "calcPValueMC"):
        assert not re.search(rf"\b{fn}\s*\(", codigo), (
            f"{arquivo.name} chama {fn}() — versão SÍNCRONA, trava a tela. "
            f"Use mcComputeAsync(rows, sims).then(...), como a Visão Geral."
        )


def test_mccomputeasync_existe_e_e_o_caminho_das_telas():
    app_js = _ler(APP_JS)
    assert "function mcComputeAsync(" in app_js
    usos = sum("mcComputeAsync(" in _ler(p) for p in (DASH_JS / "charts").glob("*.js"))
    assert usos >= 3, (
        "esperava Visão Geral, Métricas e drill de tipster pelo caminho assíncrono; "
        f"achei {usos} tela(s)"
    )


# ── 3) Uma fórmula só, carregada pelos dois caminhos ──────────────────────────

@pytest.mark.parametrize("fn", FUNCOES_NUCLEO)
def test_matematica_definida_uma_vez_so(fn):
    """Página e worker leem o MESMO arquivo — duas cópias divergem com o tempo."""
    definem = [
        p for p in DASH_JS.rglob("*.js")
        if re.search(rf"^function {re.escape(fn)}\s*\(", _ler(p), flags=re.MULTILINE)
    ]
    assert definem == [MC_CORE], (
        f"{fn} deveria ser definida só em mc-core.js; achei em "
        f"{[p.name for p in definem] or 'lugar nenhum'}"
    )


def test_worker_importa_o_nucleo_e_carrega_a_mesma_versao():
    worker = _ler(MC_WORKER)
    assert "importScripts('mc-core.js' + location.search)" in worker, (
        "o worker tem de importar mc-core.js repassando o ?v= (location.search): "
        "sem isso o worker pode rodar um núcleo velho enquanto a página roda o novo"
    )
    for fn in FUNCOES_NUCLEO:
        assert f"function {fn}" not in worker, f"{fn} foi copiada para dentro do worker"


def test_pagina_carrega_o_nucleo_antes_do_app():
    html = _ler(DASH_HTML)
    pos_core = html.find("assets/js/mc-core.js")
    pos_app = html.find("assets/js/app.js")
    assert pos_core != -1, "index.html do dashboard não carrega mc-core.js"
    assert pos_core < pos_app, "mc-core.js precisa vir antes de app.js"


def test_worker_e_nucleo_sao_servidos_como_javascript():
    """Não adianta existir no disco: o StaticFiles tem de entregar os dois."""
    from fastapi.testclient import TestClient
    cliente = TestClient(main.app)
    for rota in ("/dashboard/assets/js/mc-core.js", "/dashboard/assets/js/mc-worker.js"):
        r = cliente.get(rota)
        assert r.status_code == 200, f"{rota} não é servido ({r.status_code})"
        assert "javascript" in r.headers.get("content-type", ""), (
            f"{rota} servido como {r.headers.get('content-type')} — o navegador "
            f"recusa executar worker que não chega como JavaScript"
        )
