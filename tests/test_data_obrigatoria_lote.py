"""Edição não apaga a `data` de aposta: nem em lote, nem uma por uma (s466).

O caso: o modal "Editar em massa" trata "tique ligado com o campo vazio" como LIMPAR, e o
tique da Data liga sem querer (clique no rótulo, digitar e apagar, "Limpar" do calendário).
Nos dois únicos eventos do histórico, a pessoa aplicou só TIPSTER em lote e a data foi junto:
Jaao26 em 28/09 (7 linhas) e Jonathan em 24/11 (100 linhas, Stake.com). Aposta sem data some
de toda tela com período, e recapturar não devolve (a linha resolvida congela a `data`).

O que se trava aqui:
  • servidor: `POST /bilhetes/lote` e `PATCH /bilhetes/{id}` recusam `data` vazia ou só
    espaço com 400, ANTES de qualquer escrita (o dublê da escrita registra se foi chamado);
  • servidor: data preenchida e edição sem `data` continuam passando (a recusa não engole
    o resto);
  • front: `data` está no mapa de obrigatórios dos DOIS modais de lote (tela de Extração e
    dashboard), recortado do arquivo real. É esse mapa que trava o botão "Aplicar" e escreve
    "Data não pode ficar em branco".

NÃO cobre: o clique de verdade no modal (o botão desabilitado é lido do mapa, não renderizado
num navegador); o bot de tipster, que usa o mesmo PATCH e nunca manda data vazia.
"""
import pathlib
import re
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import main  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DONO = "donoteste"


@pytest.fixture
def cliente(monkeypatch):
    """Rotas com o dono resolvido e a escrita no banco trocada por um registro de chamadas."""
    chamadas = []

    async def _lote(ids, campos, dono):
        chamadas.append(("lote", dict(campos)))
        return {"atualizados": len(ids), "ignorados": [], "total": len(ids)}

    async def _um(bilhete_id, campos, dono, rastro=None):
        chamadas.append(("patch", dict(campos)))
        return True

    async def _flags_lote(ids, dono, campos):
        return {}

    async def _flags(bilhete_id, dono, campos):
        return {}

    monkeypatch.setattr(main, "atualizar_bilhetes_lote", _lote)
    monkeypatch.setattr(main, "atualizar_bilhete", _um)
    monkeypatch.setattr(main, "flags_pos_edicao_lote", _flags_lote)
    monkeypatch.setattr(main, "flags_pos_edicao", _flags)
    monkeypatch.setattr(main.matcher, "invalidar", lambda dono: None)
    main.app.dependency_overrides[main.dono_efetivo] = lambda: DONO
    main.app.dependency_overrides[main.dono_efetivo_ou_bot] = lambda: DONO
    try:
        yield TestClient(main.app), chamadas
    finally:
        main.app.dependency_overrides.pop(main.dono_efetivo, None)
        main.app.dependency_overrides.pop(main.dono_efetivo_ou_bot, None)


# ── servidor: lote ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("vazia", ["", "   "])
def test_lote_recusa_data_vazia_sem_escrever(cliente, vazia):
    c, chamadas = cliente
    r = c.post("/bilhetes/lote", json={"ids": [1, 2], "tipster": "AutoTrack", "data": vazia})
    assert r.status_code == 400
    assert "data" in r.json()["detail"].lower()
    assert chamadas == []          # nem o tipster entra: o lote inteiro é recusado


def test_lote_com_data_preenchida_passa(cliente):
    c, chamadas = cliente
    r = c.post("/bilhetes/lote", json={"ids": [1], "data": "19/11/2026"})
    assert r.status_code == 200
    assert chamadas == [("lote", {"data": "19/11/2026"})]


def test_lote_sem_data_passa(cliente):
    """O caso do Jonathan feito certo: só tipster, data fora do patch."""
    c, chamadas = cliente
    r = c.post("/bilhetes/lote", json={"ids": [1, 2], "tipster": "AutoTrack"})
    assert r.status_code == 200
    assert chamadas == [("lote", {"tipster": "AutoTrack"})]


# ── servidor: PATCH de uma aposta ─────────────────────────────────────────────

@pytest.mark.parametrize("vazia", ["", "   "])
def test_patch_recusa_data_vazia_sem_escrever(cliente, vazia):
    c, chamadas = cliente
    r = c.patch("/bilhetes/7", json={"data": vazia})
    assert r.status_code == 400
    assert chamadas == []


def test_patch_com_data_preenchida_passa(cliente):
    c, chamadas = cliente
    r = c.patch("/bilhetes/7", json={"data": "20/11/2026"})
    assert r.status_code == 200
    assert chamadas == [("patch", {"data": "20/11/2026"})]


def test_patch_sem_data_passa(cliente):
    c, chamadas = cliente
    r = c.patch("/bilhetes/7", json={"tipster": "AutoTrack"})
    assert r.status_code == 200
    assert chamadas == [("patch", {"tipster": "AutoTrack"})]


# ── front: o mapa de obrigatórios dos dois modais de lote ─────────────────────

def _obrigatorios(arquivo: str, nome: str) -> set[str]:
    texto = (RAIZ / arquivo).read_text(encoding="utf-8")
    m = re.search(rf"const {nome} = \{{([^}}]*)\}};", texto)
    assert m, f"{nome} não encontrado em {arquivo}"
    return set(re.findall(r"(\w+)\s*:", m.group(1)))


@pytest.mark.parametrize("arquivo,nome", [
    ("app/static/index.html", "LOTE_OBRIGATORIOS"),
    ("app/static/dash/assets/js/charts/apostas.js", "AP_LOTE_OBRIG"),
])
def test_front_data_e_obrigatoria_no_lote(arquivo, nome):
    assert {"data", "casa", "parceiro"} <= _obrigatorios(arquivo, nome)
