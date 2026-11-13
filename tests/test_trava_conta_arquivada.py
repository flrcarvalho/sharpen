"""s453: conta ARQUIVADA não recebe aposta nova sem o dono confirmar (pedido do Feca, 13/11/2026).

O caso: a captura da 1win caiu na `Feca [Eu]`, arquivada desde 28/10, e a Ficha gravou 13 apostas
lá; a marca de "já lido" (dono + casa + código) deixou 4 liquidações presas na conta certa.

Rodam as rotas REAIS (`main.captura_parear` e `main.extrair`) com o cadastro dublado
(`main.conta_arquivada`) e a IA dublada: a trava tem de recusar ANTES de criar sessão e antes de
chamar a IA, e deixar passar com a confirmação e em conta ativa.

O QUE NÃO COBREM: a consulta ao cadastro (`repository.conta_arquivada`, SQL no Postgres; coberta
pelo harness de banco quando houver) e a tela (`_confirmarContaArquivada`, medida em headless).
Mutações (13/11/2026), cada uma com um teste vermelho:
  T1 sem a trava no pareamento            → test_parear_em_arquivada_recusa_sem_criar_sessao
  T2 sem a trava no /extrair              → test_extrair_em_arquivada_recusa_antes_da_ia
  T3 a confirmação não libera             → test_confirmado_passa
  T4 a mensagem sem a data                → test_parear_em_arquivada_recusa_sem_criar_sessao
"""
import asyncio
import datetime as dt
import sys

sys.path.insert(0, "app")

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402

import main  # noqa: E402

ARQ = {("TDonoArq", "Feca [Eu]"): {"arquivada_em": dt.date(2026, 10, 28)}}


@pytest.fixture
def cadastro(monkeypatch):
    perguntas = []

    async def _duble(dono, casa, parceiro):
        perguntas.append((dono, casa, parceiro))
        return ARQ.get((dono, parceiro))
    monkeypatch.setattr(main, "conta_arquivada", _duble)
    return perguntas


@pytest.fixture
def sessoes(monkeypatch):
    criadas = []

    class _S:
        sessao_id, codigo, modo, casa, parceiro = "s1", "ABCD-EFGH", "texto", "1win", "x"

    def _criar(*a):
        criadas.append(a)
        return _S()
    monkeypatch.setattr(main._captura, "criar_sessao", _criar)
    return criadas


@pytest.fixture
def ia(monkeypatch):
    chamadas = []

    def _duble(*a, **kw):
        chamadas.append(1)

        async def _vazio():
            yield "data: {}\n\n"
        return _vazio()

    async def _predup(texto, *a, **kw):
        return texto, 0
    monkeypatch.setattr(main, "_stream_sequential", _duble)
    monkeypatch.setattr(main, "_stream_parallel", _duble)
    monkeypatch.setattr(main, "_dedup_superbet_text", _predup)
    monkeypatch.setattr(main.auth_mod, "eh_trial", lambda d: False)
    return chamadas


def _parear(parceiro, confirmar=False):
    req = main.ParearRequest(casa="1win", parceiro=parceiro, confirmar_arquivada=confirmar)
    return asyncio.run(main.captura_parear(req, dono="TDonoArq"))


def _extrair(parceiro, confirmar=""):
    return asyncio.run(main.extrair(
        casa="Bet365", parceiro=parceiro, modelo=main.DEFAULT_MODEL, texto="[Código: 1] bilhete",
        csv_content=None, imagens=[], pdfs=[], xls_file=None, data_referencia=None,
        confirmar_arquivada=confirmar, dono="TDonoArq"))


def test_parear_em_arquivada_recusa_sem_criar_sessao(cadastro, sessoes):
    with pytest.raises(HTTPException) as e:
        _parear("Feca [Eu]")
    assert e.value.status_code == 409
    assert "Feca [Eu]" in e.value.detail and "desde 28/10/2026" in e.value.detail
    assert sessoes == []


def test_extrair_em_arquivada_recusa_antes_da_ia(cadastro, ia):
    with pytest.raises(HTTPException) as e:
        _extrair("Feca [Eu]")
    assert e.value.status_code == 409
    assert ia == []


def test_confirmado_passa(cadastro, sessoes, ia):
    assert _parear("Feca [Eu]", confirmar=True)["codigo"] == "ABCD-EFGH"
    assert len(sessoes) == 1
    _extrair("Feca [Eu]", confirmar="1")
    assert ia


def test_conta_ativa_passa_sem_perguntar_nada_a_tela(cadastro, sessoes, ia):
    assert _parear("Ellen [Eu]")["codigo"] == "ABCD-EFGH"
    _extrair("Ellen [Eu]")
    assert ia
    assert ("TDonoArq", "1WIN", "Ellen [Eu]") in cadastro       # perguntou pela CHAVE da casa


def test_arquivada_sem_data_diz_so_arquivada(cadastro, sessoes, monkeypatch):
    async def _sem_data(dono, casa, parceiro):
        return {"arquivada_em": None}
    monkeypatch.setattr(main, "conta_arquivada", _sem_data)
    with pytest.raises(HTTPException) as e:
        _parear("Velha")
    assert "está arquivada." in e.value.detail and "desde" not in e.value.detail
