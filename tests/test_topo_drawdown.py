"""Topo Histórico e Drawdown Atual (s313) — o KPI que mentia em silêncio.

Relato do tester Gabriel, com print: *"quando um grupo/método começa o primeiro dia
negativo, ele desconsidera esse negativo no cálculo de drawdown. nesse exemplo aí o
segundo dia tá positivo mas valor menor que o primeiro e o DD tá 0"*. A carteira dele
mostrava **Topo Histórico −R$ 1.605,30** e **Drawdown Atual R$ 0,00** com o Max
Drawdown ao lado, correto, em −R$ 2.514,00.

Duas funções descrevem a MESMA curva e discordavam de onde ela começa:

  · `calcDrawdownReal` (Max Drawdown) partia de `peak = 0` — a banca no zero, antes da
    primeira aposta. Certo: contava o mergulho inicial;
  · `calcTopoDrawdown` (Topo + DD Atual) partia de `peak = -Infinity` — então o PRIMEIRO
    dia virava o topo fosse ele qual fosse. Numa série que só sobe depois do mergulho, o
    topo passava a ser o último ponto e `dd = peak - acc` dava **0 por construção**.

Daí o topo negativo (impossível: o topo nunca esteve abaixo do início) e o DD zerado com
a banca no vermelho. O alcance era maior que o relato: não dependia de "começar negativo",
bastava o acumulado atual ser o máximo da série e ainda estar abaixo de zero — ou seja,
qualquer carteira/casa/esporte no vermelho vindo de recuperação, em 4 renders (Visão Geral
e as três telas de Performance).

A prova de COMPORTAMENTO roda em `tests/js/topo_drawdown.mjs`, que executa as funções
RECORTADAS do `app.js` de produção — ver `test_prova_por_execucao`.

Provado por mutação: 7/8 detectadas (peak=-Infinity nas duas funções, denominador antigo
`dd/peak`, subtítulo do topo=início, data invertida, `>` virando `>=` no empate de topo,
topoData virando o último dia). A 8ª — trocar `dd=peak-acc` por `Math.max(0,peak-acc)` —
é **inócua**: `peak` é o máximo da série e inclui o `acc` atual, então a diferença nunca é
negativa e o clamp é redundante. Não é buraco de teste.
"""
import io
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"
MJS = RAIZ / "tests" / "js" / "topo_drawdown.mjs"
RENDERS = [
    RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "overview.js",
    RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "performance.js",
]


def _sem_comentarios(codigo: str) -> str:
    """Tira comentários antes de auditar: o gate tem de ler o CÓDIGO, não a prosa sobre o
    código. Mesmo falso positivo do `test_monte_carlo_worker.py` — aqui o comentário que
    explica *por que* não se volta ao `-Infinity` reprovava a função que já foi corrigida."""
    codigo = re.sub(r"/\*.*?\*/", "", codigo, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", codigo, flags=re.MULTILINE)


def _corpo(nome: str) -> str:
    src = APP_JS.read_text(encoding="utf-8")
    m = re.search(r"^function " + nome + r"\([^)]*\)\{.*?^\}", src, re.S | re.M)
    assert m, f"{nome} sumiu do app.js"
    return _sem_comentarios(m.group(0))


def test_as_duas_curvas_partem_do_mesmo_zero():
    """O gate barato de leitura: nenhuma das duas funções pode voltar a `-Infinity`.
    A prova de comportamento é o .mjs; esta aqui aponta a linha exata se alguém reverter."""
    for nome in ("calcTopoDrawdown", "calcDrawdownReal"):
        corpo = _corpo(nome)
        assert "-Infinity" not in corpo, (
            f"{nome} voltou a partir de -Infinity: o primeiro dia vira o topo e o "
            "Drawdown Atual zera com a banca no vermelho (s313)"
        )
        assert re.search(r"peak\s*=\s*0", corpo), f"{nome} não parte mais de peak=0"


def test_percentual_do_dd_atual_usa_a_regua_do_mdd():
    """Os dois cards ficam lado a lado. Se o DD Atual voltar a dividir pelo lucro do topo
    (`dd/peak`) e o MDD seguir dividindo pela banca (`BASE_BANK+peak`), as duas
    porcentagens deixam de ser comparáveis — e `dd/peak` ainda divide por zero no caso
    corrigido (topo = início da série)."""
    corpo = _corpo("calcTopoDrawdown")
    assert "ddAtualPct:dd/(BASE_BANK+peak)" in corpo.replace(" ", ""), (
        "ddAtualPct não usa mais o mesmo denominador do mddPct em calcDrawdownReal"
    )


def test_nenhum_render_inventa_data_de_topo():
    """`topoData` é null quando o topo é o próprio início da série. Os 4 renders têm de
    passar pelo `topoSub` — quem interpolar `_fmtD(_td.topoData)` direto imprime
    "atingido em —", que o leitor lê como dado faltando."""
    for arq in RENDERS:
        src = arq.read_text(encoding="utf-8")
        assert "_fmtD(_td.topoData)" not in src, (
            f"{arq.name} formata topoData sem passar pelo topoSub — some o "
            '"no início da série" e vira "atingido em —"'
        )
    total = sum(a.read_text(encoding="utf-8").count("topoSub(_td)") for a in RENDERS)
    assert total == 4, f"esperava 4 renders do Topo Histórico usando topoSub, achei {total}"


def test_topo_zerado_nao_pinta_de_verde():
    """UI_REFERENCE §5.1: zero é neutro. O card do Topo carrega `data-state="pos"`, que
    pinta o valor de mint por CSS — e o `fmtPL(0)` não tem classe própria para revidar,
    então R$ 0,00 herdaria o verde. O atributo agora é condicional ao topo > 0."""
    vistos = 0
    for arq in RENDERS:
        for linha in arq.read_text(encoding="utf-8").splitlines():
            # A linha do valor do Topo é a que interpola `fmtPL(_td.topo)`; nas telas de
            # Performance ela carrega o card inteiro, na Visão Geral é só o <div> do valor.
            if "fmtPL(_td.topo)" not in linha:
                continue
            vistos += 1
            assert 'data-state="pos"' not in linha or "_td.topo>0" in linha, (
                f"{arq.name}: Topo Histórico com data-state=pos fixo — zero sairia verde"
            )
    assert vistos == 4, f"esperava 4 renders do valor do Topo Histórico, achei {vistos}"


def test_prova_por_execucao():
    """`tests/js/topo_drawdown.mjs` recorta `calcDrawdownReal`, `calcTopoDrawdown` e
    `topoSub` REAIS e os executa. O que ele NÃO cobre está no cabeçalho do .mjs: o render
    (cor do KPI e Escada de Tinta ficam para o headless) e a agregação vinda do feed."""
    r = subprocess.run(
        ["node", str(MJS)],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def test_o_gate_detecta_o_bug_original(tmp_path):
    """Mutação automatizada do caso que abriu a s313: devolver o `peak=-Infinity` tem de
    deixar o .mjs VERMELHO. Teste verde que não detecta não prova nada (CLAUDE.md)."""
    src = APP_JS.read_text(encoding="utf-8")
    alvo = "var acc=0,peak=0,peakDate=null;"
    assert src.count(alvo) == 1, "a linha do peak mudou de forma — reveja esta mutação"
    mutante = tmp_path / "app_mutante.js"
    io.open(mutante, "w", encoding="utf-8").write(
        src.replace(alvo, "var acc=0,peak=-Infinity,peakDate=null;")
    )
    r = subprocess.run(
        ["node", str(MJS)],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
        env={**__import__("os").environ, "ALVO_APP": str(mutante)},
    )
    assert r.returncode != 0, "o gate passou com o bug de volta — ele não detecta nada"
