"""O bloco de tipster da sidebar tem de REPINTAR quando a base muda (s366).

A casca (`app/static/app.html`) é feita para nunca recarregar: navegar é mostrar e
esconder iframe. O dashboard, que vive num deles, se atualiza sozinho por três gatilhos
(SSE `/eventos`, botão ↻ e volta de aba), todos desembocando em `executarRefresh`, que
só falava com os iframes. O `fetch('/conta/perfil')` do bloco rodava UMA vez, no load.

O preço, medido na base do Gabriel: a sidebar mostrava `+R$ 48.614,76 / +3,57%` e o KPI
do dashboard `+R$ 50.782,00 / +3,72%` na mesma tela. Reconstruindo a base por
`atualizado_em`, os números da sidebar eram exatamente o estado de 15/09/2026 14:00:45
UTC — o instante do login. Régua igual, instante diferente: nenhum dos dois estava
errado, e é justamente isso que faz o certo parecer defeito.

A ponte é o evento `base-recarregada`, disparado por `executarRefresh` e escutado pelo
IIFE do bloco. Este arquivo trava as duas pontas e o efeito colateral que a repintura
criou na logo.

O que NÃO cobre: que a repintura ACONTEÇA no navegador (isto é leitura de texto, não
render — o `recarregarPerfil` pode estar escrito e nunca ser chamado se o IIFE do bloco
morrer antes por outro erro), nem os números que o `/conta/perfil` devolve, que são do
`repository.resumo_perfil` e têm gate próprio.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CASCA = RAIZ / "app" / "static" / "app.html"
BLOCO = RAIZ / "app" / "static" / "sb-tipster.js"

EVENTO = "base-recarregada"


def _corpo(texto: str, inicio: str, fim: str) -> str:
    """Fatia entre dois marcos, com mensagem útil quando um deles sai do lugar: um
    regex que não acha nada passaria como verde silencioso, que é o falso verde nº 2
    do CLAUDE.md (o dado sintético que não exerce a regra)."""
    i = texto.find(inicio)
    assert i >= 0, f"não achei {inicio!r} — o marco do teste ficou para trás"
    j = texto.find(fim, i)
    assert j > i, f"não achei {fim!r} depois de {inicio!r} — o marco ficou para trás"
    return texto[i:j]


def test_executar_refresh_avisa_que_a_base_mudou():
    """Os três gatilhos de recarga passam por aqui; é o único ponto que os cobre de
    uma vez."""
    corpo = _corpo(CASCA.read_text(encoding="utf-8"),
                   "function executarRefresh(forcar){",
                   "if (refreshBtn) refreshBtn.addEventListener")
    assert f"dispatchEvent(new Event('{EVENTO}'))" in corpo, (
        "executarRefresh parou de avisar a casca. Sem o evento, a sidebar volta a "
        "congelar no instante do login enquanto os KPIs sobem a cada captura (s366)"
    )


def test_o_aviso_vem_antes_do_early_return_da_fila():
    """`if (!fila.length) return` dispara quando nenhum iframe tem base carregada (o
    usuário só abriu a Extração). O perfil é agregado no SERVIDOR e não depende de
    iframe nenhum: avisar depois do return deixaria justamente essa sessão parada."""
    corpo = _corpo(CASCA.read_text(encoding="utf-8"),
                   "function executarRefresh(forcar){",
                   "if (refreshBtn) refreshBtn.addEventListener")
    aviso = corpo.find(f"dispatchEvent(new Event('{EVENTO}'))")
    early = corpo.find("if (!fila.length) return")
    assert aviso >= 0 and early >= 0, "um dos dois marcos sumiu de executarRefresh"
    assert aviso < early, (
        "o aviso caiu depois do early-return: sessão sem iframe com base (só a "
        "Extração aberta) não repinta mais a sidebar"
    )


def test_o_bloco_escuta_o_aviso_e_rebusca_o_perfil():
    html = CASCA.read_text(encoding="utf-8")
    assert re.search(
        rf"addEventListener\('{EVENTO}'\s*,\s*function\(\)\{{\s*recarregarPerfil\(\)",
        html,
    ), (
        "ninguém escuta o `base-recarregada` no app.html — o evento é disparado e cai "
        "no vazio, que é pior que não existir: parece coberto"
    )


def test_a_busca_do_perfil_mora_numa_funcao_reusavel():
    """A correção inteira depende de haver UM caminho para buscar o perfil. Uma segunda
    chamada solta a `/conta/perfil` seria a de sempre: roda no load, some do evento."""
    html = CASCA.read_text(encoding="utf-8")
    assert html.count("fetch('/conta/perfil')") == 1, (
        "há mais de uma chamada a /conta/perfil no app.html — a busca voltou a ser "
        "código solto em vez do `recarregarPerfil`"
    )
    corpo = _corpo(html, "function recarregarPerfil(){", "\n  recarregarPerfil();")
    assert "fetch('/conta/perfil')" in corpo, (
        "a chamada saiu de dentro do recarregarPerfil: o evento passaria a repintar "
        "com o estado antigo"
    )


def test_a_logo_nao_ganha_url_nova_a_cada_repintura():
    """Efeito colateral que a repintura criou: `aplicar` agora roda a cada recarga da
    base, e o cache-bust por `Date.now()` dava à logo uma URL inédita toda vez — request
    novo e piscada, sem a imagem ter mudado. O carimbo é memorizado; quem precisa furar
    o cache (o upload) passa a versão explícita."""
    js = BLOCO.read_text(encoding="utf-8")
    corpo = _corpo(js, "function pintarLogo(temLogo, versao) {", "function pintarStats")
    assert "img.src = cfg.logoUrl + '?v=' + logoVersao;" in corpo, (
        "pintarLogo voltou a montar a URL sem o carimbo memorizado"
    )
    assert "Date.now()" not in corpo.split("img.src")[1], (
        "sobrou um Date.now() depois da montagem da URL — o cache-bust voltou a ser "
        "por repintura"
    )
    assert "pintarLogo(true, Date.now())" in js, (
        "o UPLOAD perdeu o cache-bust explícito: a logo nova ficaria escondida atrás "
        "da antiga, que é o defeito que o carimbo existe para evitar"
    )
