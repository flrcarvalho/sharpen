# -*- coding: utf-8 -*-
"""Gate das regras novas do Painel de Contas (s333, Fases 7 e 8).

A lógica vive no `index.html`. `tests/js/contas_status.mjs` RECORTA as funções do
arquivo de produção e as executa — nunca reescreve o trecho, senão o teste passa a
provar a cópia (s286).

Aqui em cima ficam as MUTAÇÕES: cada uma quebra o código de propósito, numa cópia, e
exige o gate vermelho. Verde sem essa prova não prova nada.

O que este arquivo NÃO cobre: a grade em px e os degraus de container (isso é render
e se mede no headless), o `ultima_captura` do `/caixa/visao` (esse é
`test_caixa.py`/`repository`) e o clique dos filtros, que é DOM.
"""
import io
import os
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "app" / "static" / "index.html"
MJS = RAIZ / "tests" / "js" / "contas_status.mjs"


def _node(alvo=None):
    env = dict(os.environ, ALVO_INDEX=str(alvo)) if alvo else None
    return subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                          encoding="utf-8", cwd=str(RAIZ), env=env)


def _mutar(tmp_path, alvo, troca):
    """Copia o index.html trocando `alvo` por `troca`. Falha se o alvo sumiu do
    arquivo — mutação que não encontra o que mutar roda contra o código intacto e
    devolve verde, que é o falso verde mais silencioso que existe."""
    src = INDEX.read_text(encoding="utf-8")
    assert src.count(alvo) == 1, f"o trecho mudou de forma — reveja esta mutação: {alvo!r}"
    destino = tmp_path / "index_mutante.html"
    io.open(destino, "w", encoding="utf-8", newline="").write(src.replace(alvo, troca))
    return destino


def test_prova_por_execucao():
    r = _node()
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def test_detecta_parada_subindo_na_precedencia(tmp_path):
    """`Parada` acima de `Aguardando tipster` esconderia a espera por terceiro atrás
    do abandono — a conta parada com bilhete sem tipster pararia de pedir ação."""
    alvo = "  if (semTipster > 0) return ['tipster', semTipster];"
    m = _mutar(tmp_path, alvo, "")
    assert _node(m).returncode != 0, "o gate passou com a precedência invertida"


def test_detecta_o_corte_de_30_dias_virando_inclusivo(tmp_path):
    """`>=` marcaria como abandonada a conta usada uma vez por mês, no dia exato."""
    alvo = "if (dias !== null && dias > _PARADA_DIAS) return ['parada', dias];"
    m = _mutar(tmp_path, alvo, "if (dias !== null && dias >= _PARADA_DIAS) return ['parada', dias];")
    assert _node(m).returncode != 0, "o gate passou com o corte inclusivo"


def test_detecta_conta_sem_captura_virando_parada(tmp_path):
    """Conta que nunca capturou nada não parou: nunca começou. Sem a guarda de
    `null`, toda conta recém-criada nasceria com a tag de abandono."""
    alvo = "if (dias !== null && dias > _PARADA_DIAS) return ['parada', dias];"
    m = _mutar(tmp_path, alvo, "if (dias === null || dias > _PARADA_DIAS) return ['parada', dias];")
    assert _node(m).returncode != 0, "o gate passou marcando conta sem captura como parada"


def test_detecta_dias_negativos(tmp_path):
    """Relógio adiantado dando 'há -3 dias' — e um negativo nunca cruza o corte."""
    alvo = "  return Math.max(0, Math.floor((Date.now() - t) / 86400000));"
    m = _mutar(tmp_path, alvo, "  return Math.floor((Date.now() - t) / 86400000);")
    assert _node(m).returncode != 0, "o gate passou com contagem negativa de dias"


def test_detecta_fornecedor_ordenado_por_nome(tmp_path):
    """A zona ordena por CAIXA decrescente: é o risco que ela mede. Por nome, o
    fornecedor que guarda metade do dinheiro pode aparecer por último."""
    alvo = "sort((a, b) => b.caixa - a.caixa || a.nome.localeCompare(b.nome))"
    m = _mutar(tmp_path, alvo, "sort((a, b) => a.nome.localeCompare(b.nome))")
    assert _node(m).returncode != 0, "o gate passou com a zona ordenada por nome"


def test_detecta_conta_sem_caixa_entrando_na_soma(tmp_path):
    """Conta sem a Caixa ligada não vira zero nem entra na soma: total que engole
    conta desconhecida mente com cara de exatidão."""
    alvo = "      if (cx && cx.ligada && cx.banca) a.caixa += cx.banca;"
    m = _mutar(tmp_path, alvo, "      if (cx) a.caixa += cx.banca;")
    assert _node(m).returncode != 0, "o gate passou somando conta sem caixa ligada"


def test_detecta_numero_fora_do_b_na_pilula(tmp_path):
    """O número é o DADO; o resto é rótulo. Fora do <b> ele perde a cor forte e some
    dentro do texto em caixa alta."""
    alvo = "  parada:     { cls: 'parada', txt: (n) => 'Parada há <b>' + n + '</b> dias' },"
    m = _mutar(tmp_path, alvo, "  parada:     { cls: 'parada', txt: (n) => 'Parada há ' + n + ' dias' },")
    assert _node(m).returncode != 0, "o gate passou com o número fora do <b>"


def test_detecta_o_proprio_usuario_contado_como_fornecedor(tmp_path):
    """`Eu` é o contraponto do risco, não mais um fornecedor: contá-lo inflaria o
    'N fornecedores' do KPI e o 'em contas de terceiros' passaria a incluir o caixa
    que está na mão do próprio dono."""
    alvo = "  const terceiros = linhas.filter(l => !l.eu).reduce((s, l) => s + l.caixa, 0);"
    m = _mutar(tmp_path, alvo, "  const terceiros = linhas.reduce((s, l) => s + l.caixa, 0);")
    assert _node(m).returncode != 0, "o gate passou contando o caixa próprio como de terceiros"
