"""A coluna de P/L nos exports em CSV (s303).

Pedido do grupo de testers: o CSV trazia stake e odd, mas não o lucro — *"como às vezes dá
meio green/red não tem como calcular na mão"*. Meio green/red é HW/HL, onde o retorno é de
MEIA aposta e ninguém refaz a conta na planilha a partir de stake e odd.

O P/L não existe no banco: é DERIVADO na leitura (`repository.calcular_pl`), então o
`SELECT *` de `export_bilhetes` jamais o traria — a coluna é montada na hora de gerar o
arquivo. Isso é o que estes testes travam, e cada um cobre um jeito de a coluna reaparecer
quebrada sem ninguém perceber:

  1. a coluna existe no cabeçalho e no corpo — um refactor que volte a escrever só
     `r.items()` some com ela sem erro nenhum;
  2. HW/HL saem com o P/L de meia aposta (o caso que originou o pedido);
  3. decimal VÍRGULA e hífen comum. O minus do padrão de tela é U+2212 e o Excel pt-BR o lê
     como TEXTO: a coluna apareceria e mesmo assim não somaria;
  4. sem P/L calculável (aberta, ou vitória sem odd legível) a célula fica VAZIA. Zero ali
     seria "empatou" — mentira diferente, e pior, porque soma.

A metade do front (menu Exportar da tela de Extração) roda em `tests/js/export_csv_pl.mjs`,
invocado no fim deste arquivo.

Provado por mutação: 9/9 detectadas. No backend (5): remover a coluna do `fieldnames`, não
preencher `linha["pl"]`, trocar a vírgula pelo ponto, usar U+2212 e devolver "0,00" no lugar
do vazio. No front (4, via `ALVO_INDEX` apontando para uma cópia mutada): acrescentar a 11ª
coluna também no TSV, tirá-la do CSV, usar U+2212 e devolver "0,00" no lugar do vazio.

NÃO cobre: o valor do P/L em si (é `calcular_pl`, em `tests/test_formulas.py`) nem o
download no navegador.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import auth  # noqa: E402
import main  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
cliente = TestClient(main.app)


def _linha(**kw):
    """Linha crua do Postgres, no formato que `export_bilhetes` devolve."""
    base = dict(
        id=1, casa="Bet365", parceiro="Conta 1", assinatura="abc", data="31/08/2026",
        esporte="Futebol", tipster="LBB", aposta="Handicap Asiático",
        descricao="Norwich x Burnley", stake="100,00", odd="2,50", resultado="W",
        extraction_state="resolvida", codigo_bilhete="0001941", archived=False,
    )
    base.update(kw)
    return base


def _csv(linhas, monkeypatch) -> list[list[str]]:
    async def _fake_export(dono):
        return list(linhas)

    monkeypatch.setattr(main, "export_bilhetes", _fake_export)
    r = cliente.get("/exportar.csv", cookies={auth.COOKIE_NAME: auth.criar_token("Feca")})
    assert r.status_code == 200, r.text
    texto = r.content.decode("utf-8").lstrip("﻿")
    return [l.split(";") for l in texto.strip().split("\r\n")]


def test_a_coluna_pl_existe_no_cabecalho_e_no_corpo(monkeypatch):
    linhas = _csv([_linha()], monkeypatch)
    assert linhas[0][-1] == "pl", f"cabeçalho sem a coluna pl: {linhas[0]}"
    assert len(linhas[1]) == len(linhas[0]), "corpo e cabeçalho com número de colunas diferente"


@pytest.mark.parametrize("resultado,esperado", [
    ("W", "150,00"),
    ("HW", "75,00"),    # meio green: (50 × 2,5) + 50 − 100
    ("HL", "-50,00"),   # meio red: 50 − 100
    ("L", "-100,00"),
    ("V", "0,00"),      # void empata: zero é um VALOR, não um vazio
])
def test_pl_por_resultado(resultado, esperado, monkeypatch):
    linhas = _csv([_linha(resultado=resultado)], monkeypatch)
    assert linhas[1][-1] == esperado, f"{resultado}: veio {linhas[1][-1]}"


def test_negativo_sai_com_hifen_comum_e_decimal_virgula(monkeypatch):
    """O minus U+2212 é do padrão de TELA. Num arquivo ele vira texto no Excel."""
    bruto = "\n".join(";".join(l) for l in _csv([_linha(resultado="HL")], monkeypatch))
    assert "−" not in bruto, "o CSV levou o minus U+2212 — o Excel lê a coluna como texto"
    assert "-50,00" in bruto and "-50.00" not in bruto, "P/L fora do decimal-vírgula"


@pytest.mark.parametrize("linha,motivo", [
    (dict(resultado=""), "aposta aberta"),
    (dict(resultado="W", odd=""), "vitória sem odd legível"),
])
def test_sem_pl_calculavel_a_celula_fica_vazia(linha, motivo, monkeypatch):
    """Zero ali seria 'empatou' — e soma. Vazio é o mesmo `None` de `calcular_pl`."""
    linhas = _csv([_linha(**linha)], monkeypatch)
    assert linhas[1][-1] == "", f"{motivo}: esperado vazio, veio {linhas[1][-1]!r}"


def test_base_vazia_nao_quebra(monkeypatch):
    """Dono sem nenhuma aposta: o arquivo sai vazio (sem cabeçalho), como antes."""
    async def _fake_export(dono):
        return []

    monkeypatch.setattr(main, "export_bilhetes", _fake_export)
    r = cliente.get("/exportar.csv", cookies={auth.COOKIE_NAME: auth.criar_token("Feca")})
    assert r.status_code == 200
    assert r.content.decode("utf-8").lstrip("﻿") == ""


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_do_export_do_front():
    """`tests/js/export_csv_pl.mjs` recorta o `montarCSV`/`montarTSV` REAIS do
    `index.html` e os executa. Prova as duas metades: o CSV ganhou a coluna e o TSV
    continua em 10 colunas (ele é colado direto na planilha do usuário)."""
    r = subprocess.run(
        ["node", str(RAIZ / "tests" / "js" / "export_csv_pl.mjs")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
