"""Ordenação das tabelas do dashboard (s300) — o que quebra em SILÊNCIO.

Reclamação do Feca em Fornecedores & Parceiros: *"nenhum desses filtros tá funcionando
direito, não ordena nada da forma correta, nem datas, nem financeiro, ROI, nada"*.

Eram três causas independentes, e nenhuma delas dá erro: a tabela reordena, só que errado.

  1. O menos do padrão monetário é **U+2212** (−), não hífen ASCII. O `parseNum` mandava
     isso pro `parseFloat`, que devolvia `NaN` → 0 — então **todo P/L e ROI negativo era
     ordenado como zero** e empilhava num bloco no meio da tabela;
  2. `fmtR` imprime inteiro sem decimal ("R$ 5.180"), e a regra antiga de milhar só tirava
     o ponto quando vinha vírgula depois. "5.180" virava 5,18 e a conta de **R$ 80 subia ao
     topo do Turnover**;
  3. as colunas de data saem em `dd/mm/aa` e não eram numéricas — ordenavam como texto, ou
     seja, **pelo dia do mês**. Hoje quem manda é um `data-sort` em ISO.

A prova de COMPORTAMENTO (as cinco colunas ordenadas de verdade, a linha de Total no fim,
a seta no <th>) roda em `tests/js/sort_tabelas.mjs`, que executa o `parseNum`, o
`sortTable` e o construtor de linhas RECORTADOS dos arquivos de produção. Este arquivo o
invoca — ver `test_prova_por_execucao_do_sort`.

Provado por mutação: 11/11 detectadas (menos U+2212, milhar sem decimal, sinal perdido no
retorno, `data-sort` ignorado no sort, `localeCompare` sensível a caixa, total-row fora do
fim, seta em todas as colunas, `data-sort` ausente nas datas e na casa, 1ª Aposta levando a
data errada, colunas numéricas trocadas).
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
APP_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"
GESTAO_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "gestao.js"

MENOS = "−"


def test_parse_num_trata_o_menos_tipografico():
    """O `−` (U+2212) é obrigatório no padrão monetário (UI_REFERENCE §5) e vem de `fmtPL`
    e `fmtPct`. Se o `parseNum` não o converter, negativo vira 0 e some da ordenação."""
    src = APP_JS.read_text(encoding="utf-8")
    corpo = re.search(r"function parseNum\(raw\)\{.*?\n\}", src, re.S)
    assert corpo, "parseNum sumiu do app.js"
    assert MENOS in corpo.group(0), "parseNum não normaliza o menos U+2212 — negativo vira 0"


def test_parse_num_desfaz_milhar_sem_decimal():
    """`fmtR` imprime "R$ 5.180" — sem vírgula. A regra de milhar tem de reconhecer o
    número pela FORMA (grupos de 3), não pelo que vem depois do ponto."""
    corpo = re.search(r"function parseNum\(raw\)\{.*?\n\}", APP_JS.read_text(encoding="utf-8"), re.S)
    assert r"^\d{1,3}(\.\d{3})+$" in corpo.group(0), (
        "parseNum perdeu a regra de milhar por forma — 'R$ 5.180' volta a valer 5,18"
    )


def test_contas_individuais_ordena_data_por_iso():
    """As duas colunas de data mostram dd/mm/aa e ordenam pelo `data-sort` ISO. Sem ele o
    sort cai no textContent e ordena pelo dia do mês."""
    src = GESTAO_JS.read_text(encoding="utf-8")
    assert 'data-sort="${iso1}"' in src, "1ª Aposta sem data-sort — volta a ordenar pelo dia"
    assert 'data-sort="${iso2}"' in src, "Última sem data-sort — volta a ordenar pelo dia"
    assert "makeSortable('tblParc',[3,4,5,6,9])" in src, (
        "as colunas numéricas do tblParc mudaram; datas (7,8) ordenam por data-sort, não por número"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_sort():
    """`tests/js/sort_tabelas.mjs` recorta o parseNum, o sortTable e o construtor de linhas
    REAIS e os executa contra um DOM dublado. O que ele NÃO cobre está no cabeçalho do
    .mjs: o clique de verdade, o resize de coluna e o CSS da seta."""
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "sort_tabelas.mjs")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
