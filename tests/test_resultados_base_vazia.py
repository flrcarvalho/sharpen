"""A aba Resultados dizia "Carregando dados…" para sempre a quem acabou de chegar (s374).

`aplicarFeed` (`dash/assets/js/app.js`) parte o feed em dois: `DADOS` recebe só
W/L/V/HW/HL e `DADOS_ABERTAS` recebe o resto. Quem se cadastra, instala o SharpenUp e
captura hoje só tem aposta EM ABERTO, então `DADOS` nasce vazio — e o
`renderResultados` tratava "vazio" e "ainda carregando" com a MESMA frase. A tela
afirmava estar buscando algo que nunca chegaria, e não havia erro nem aviso em lugar
nenhum. É o caso do Diogo (`docs/CASOS.md#a-tela-em-branco-do-diogo--s239`), que
continuava vivo.

Medido antes de propor, em Chrome headless, com o front REAL e dois feeds sintéticos:
base ZERO (cadastrou, não capturou) e base SÓ-ABERTAS (capturou hoje, nada liquidado).
Nos dois a aba parava em `chars=133`, sem KPI, sem tabela e sem gráfico. As outras dez
abas do dash renderizaram estado vazio honesto nos dois cenários.

A correção separa as DUAS causas de `DADOS` vazio por `window._dataBuiltMs`, gravado
logo depois de `aplicarFeed` nos dois caminhos de carga (cache local, `app.js:1599`;
rede, `app.js:1644`). Truthy ⇒ o feed já chegou ⇒ vazio é ausência, não espera.

**Limite conhecido, de propósito:** fetch que FALHA sem cache deixa `_dataBuiltMs` nulo
e continua caindo em "Carregando dados…". O erro de conexão tem canal próprio
(`_errBanner`, `app.js:1679`); trocar a frase ali por "não há aposta encerrada" seria a
mentira inversa, culpando a base do usuário por uma falha de rede.

A prova de COMPORTAMENTO roda em `tests/js/resultados_base_vazia.mjs`, que executa o
`renderResultados` e o `mkEmpty` RECORTADOS dos arquivos de produção — ver
`test_prova_por_execucao_do_estado_vazio`.

Provado por mutação: **6/6 detectadas** (volta da mentira original, `_dataBuiltMs`
ignorado, mensagem genérica que não nomeia "encerrada", mensagem que constata o vazio
sem dizer o que vem depois, abandono do `mkEmpty` por `<p>` com style inline, e ramos do
ternário invertidos). As mutações rodaram sobre CÓPIAS, via `ALVO_TEMPORAL`, com aborto
se o trecho alvo não for encontrado — mutação que não acerta o alvo passa verde com razão.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
TEMPORAL_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "temporal.js"
SHARED_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "shared.js"
APP_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"


def test_o_render_usa_o_discriminador_de_feed_carregado():
    """O early return de `DADOS` vazio precisa olhar `_dataBuiltMs`.

    Sem ele as duas causas voltam a ser indistinguíveis, que é o defeito inteiro.
    """
    fonte = TEMPORAL_JS.read_text(encoding="utf-8")
    inicio = fonte.index("function renderResultados()")
    trecho = fonte[inicio:inicio + 2000]
    assert "_dataBuiltMs" in trecho, (
        "renderResultados voltou a tratar 'DADOS vazio' sem distinguir "
        "'feed não chegou' de 'não há aposta encerrada'."
    )


def test_o_discriminador_e_gravado_depois_do_aplicarFeed():
    """`_dataBuiltMs` só serve de discriminador se for escrito DEPOIS do feed entrar.

    Se um dia ele passar a ser gravado ANTES de `aplicarFeed`, ou no boot, vira truthy
    com `DADOS` ainda vazio e a aba volta a mentir — desta vez na direção oposta,
    dizendo "não há aposta encerrada" antes de o feed chegar. O gate é a ORDEM.
    """
    fonte = APP_JS.read_text(encoding="utf-8")
    for caminho in ("aplicarFeed(cached.data)", "aplicarFeed(json.data)"):
        i = fonte.index(caminho)
        depois = fonte[i:i + 1200]
        assert "window._dataBuiltMs=" in depois, (
            f"`window._dataBuiltMs` deixou de ser gravado logo depois de {caminho}. "
            "O estado vazio da aba Resultados depende dessa ordem."
        )


def test_nao_ha_style_inline_de_cor_no_estado_vazio():
    """O estado vazio usa o componente `mkEmpty`, não um `<p>` com style inline.

    O código anterior cravava `style="color:var(--ink-mute);padding:2rem"` na mão. A cor
    era token, mas o componente não: duas formas para o mesmo papel é o item 8 do
    checklist de UI (`/nova-ui`).
    """
    fonte = TEMPORAL_JS.read_text(encoding="utf-8")
    assert 'Carregando dados…</p>' not in fonte, (
        "o estado vazio da aba Resultados voltou ao <p> com style inline; "
        "use mkEmpty (charts/shared.js)."
    )
    assert "function mkEmpty(" in SHARED_JS.read_text(encoding="utf-8"), (
        "mkEmpty sumiu do shared.js — o recorte do gate em .mjs depende dele."
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_estado_vazio():
    """`tests/js/resultados_base_vazia.mjs` executa o `renderResultados` real.

    O que ele NÃO cobre está no cabeçalho do .mjs: o CSS do `.empty-state-msg`, o
    caminho de fetch que falha sem cache, e o corpo do render depois dos early returns.
    """
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "resultados_base_vazia.mjs")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
