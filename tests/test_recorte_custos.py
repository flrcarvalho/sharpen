"""O RECORTE da tela de Custos (s348) — "Tudo" tem de significar tudo.

Nasceu de um defeito **medido**, não previsto: comparando a tela antiga com a nova
sobre o MESMO dado, com «Tudo» ativo a aba Contas somava R$ 0 e a antiga somava
R$ 29.400. A causa não era o dado — era o recorte. `_c2range` caía no mês corrente
quando `_selRange` devolve `null`, e `null` é justamente o que "Tudo" devolve.

O rótulo prometia a série inteira e o número entregava um mês, sem erro nenhum. É a
mesma família dos outros defeitos desta frente (o selo do degrau, a máscara do P/L,
o rodapé que somava o período com a tabela mostrando o mês): rótulo e número
discordando em silêncio.

A prova de COMPORTAMENTO roda em `tests/js/recorte_custos.mjs`, que executa
`_c2range`/`_c2primeiraData` RECORTADAS do `custos2.js` de produção mais o
`_selRange` REAL do `filters.js` — dublá-lo esconderia a metade que traduz o botão
escolhido em `{from,to}`, que é onde o defeito morava.

O que NÃO está coberto: o render (o rótulo do período no card, que a tela monta a
partir deste mesmo intervalo).
"""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CUSTOS2 = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "custos2.js"
MJS = RAIZ / "tests" / "js" / "recorte_custos.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_recorte():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES = [
    (
        "«Tudo» volta a cair no mes corrente (o defeito original)",
        "  const de = r ? r.from : (_c2primeiraData() || mesCorrente);",
        "  const de = r ? r.from : mesCorrente;",
    ),
    (
        "o periodo escolhido para de mandar e o dado velho puxa o recorte",
        "  const de = r ? r.from : (_c2primeiraData() || mesCorrente);",
        "  const de = _c2primeiraData() || mesCorrente;",
    ),
    (
        "a compra de conta deixa de abrir o periodo",
        "    .forEach(p => marca(p.adquirida_em));",
        "    .forEach(p => p);",
    ),
    (
        "o mes de custo de tipster deixa de abrir o periodo",
        "    .forEach(m => Object.keys(m || {}).forEach(ym => marca(ym + '-01')));",
        "    .forEach(m => m);",
    ),
    (
        "o mes de custo geral deixa de abrir o periodo",
        "    .forEach(r => Object.keys((r && r.values) || {}).forEach(ym => marca(ym + '-01')));",
        "    .forEach(r => r);",
    ),
    (
        "a primeira data pega a MAIOR em vez da menor",
        "  const marca = (d) => { if (d && (!min || d < min)) min = d; };",
        "  const marca = (d) => { if (d && (!min || d > min)) min = d; };",
    ),
    (
        "o fim do recorte deixa de ser hoje",
        "  const ate = r ? r.to : hoje;",
        "  const ate = r ? r.to : mesCorrente;",
    ),
    (
        "mesRef passa a ser o PRIMEIRO mes do recorte",
        "  return { de: de, ate: ate, meses: meses, mesRef: meses[meses.length - 1] || hoje.slice(0, 7) };",
        "  return { de: de, ate: ate, meses: meses, mesRef: meses[0] || hoje.slice(0, 7) };",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    """Quebra o custos2.js de propósito e exige que o .mjs fique VERMELHO."""
    src = CUSTOS2.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no custos2.js "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    estragado = tmp_path / "custos2.js"
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")

    import os
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ),
                       env={**os.environ, "ALVO_CUSTOS2": str(estragado)})
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida — o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )
