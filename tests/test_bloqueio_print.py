"""s450: casa com Ficha recusa print e PDF no `/extrair`, antes de qualquer chamada à IA (relatório
`custo_print_2026-11-10` §6, decisão do Feca de 11/11/2026). Texto colado continua; as `.bet.br`
ficam fora; casa sem Ficha segue aceitando print.

Rodam o `main.extrair` REAL. Os dois geradores (`_stream_sequential`/`_stream_parallel`) são
dublês que contam se a IA teria sido chamada; o pré-dedup do texto é dublado (ele vai ao banco).

O gate da lista refaz `captura.CASAS_COM_FICHA` a partir do manifesto da extensão (família do
inject com adaptador em `app/adaptadores`, host fora de `.bet.br`, casa por `_HOSTS_POR_CASA`):
casa nova com adaptador quebra o teste até entrar na lista.

O QUE NÃO COBREM: a tela (medida em headless na s450, fora do pytest) e a extensão.
Mutações (s450, detectadas): B1 sem a recusa no servidor, B2 a recusa vale para toda casa,
B3 só imagem é recusada (PDF passa), B4 a lista perde uma casa (Cloudbet), B5 a rota `/casas`
sem o campo `ficha`.
"""
import asyncio
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from starlette.datastructures import Headers, UploadFile  # noqa: E402

import captura  # noqa: E402
import main  # noqa: E402

_RAIZ = Path(__file__).resolve().parents[1]
_PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
_IMG = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AA=="}}
MSG = "Esta casa é extraída pela extensão SharpenUp. Abra a aba da casa e capture por ela."


def _img():
    return UploadFile(file=io.BytesIO(_PNG), filename="a.png",
                      headers=Headers({"content-type": "image/png"}))


def _pdf():
    return UploadFile(file=io.BytesIO(b"%PDF-1.4"), filename="extrato.pdf",
                      headers=Headers({"content-type": "application/pdf"}))


@pytest.fixture
def ia(monkeypatch):
    chamadas = []

    def _duble(*a, **kw):
        chamadas.append(kw.get("caminho"))

        async def _vazio():
            yield "data: {}\n\n"
        return _vazio()

    async def _predup(texto, *a, **kw):
        return texto, 0
    monkeypatch.setattr(main, "_stream_sequential", _duble)
    monkeypatch.setattr(main, "_stream_parallel", _duble)
    monkeypatch.setattr(main, "_dedup_superbet_text", _predup)
    monkeypatch.setattr(main.auth_mod, "eh_trial", lambda d: False)
    monkeypatch.setattr(main, "_pdf_para_blocos_imagem", lambda raw, nome: [dict(_IMG)])
    return chamadas


def _extrair(casa, **kw):
    args = dict(casa=casa, parceiro="conta [Op]", modelo=main.DEFAULT_MODEL, texto=None,
                csv_content=None, imagens=[], pdfs=[], xls_file=None, data_referencia=None,
                dono="TDonoBloq")
    args.update(kw)
    return asyncio.run(main.extrair(**args))


@pytest.mark.parametrize("casa", ["Thunderpick", "Cloudbet", "Vavada", "1win"])
def test_casa_com_ficha_recusa_print_antes_da_ia(ia, casa):
    with pytest.raises(HTTPException) as e:
        _extrair(casa, imagens=[_img()])
    assert e.value.status_code == 400 and e.value.detail == MSG
    assert ia == [], "a IA não pode ser chamada"


def test_casa_com_ficha_recusa_pdf(ia):
    with pytest.raises(HTTPException) as e:
        _extrair("Cloudbet", pdfs=[_pdf()])
    assert e.value.detail == MSG and ia == []


def test_casa_com_ficha_aceita_texto_colado(ia):
    _extrair("Thunderpick", texto="[Código: 123]\nStake: 10\nStatus: Perdido\n")
    assert ia == [None]


@pytest.mark.parametrize("casa", ["GiroCerto", "Vaidebet", "Bet365"])
def test_casa_sem_ficha_e_bet_br_aceitam_print(ia, casa):
    """GiroCerto não tem captura; VaideBet tem adaptador (família vb), mas é `.bet.br`."""
    _extrair(casa, imagens=[_img()])
    assert ia == ["print"]


def _derivar_casas_com_ficha() -> set:
    from adaptadores import ADAPTADORES
    manifesto = json.loads((_RAIZ / "extensor" / "manifest.json").read_text(encoding="utf-8"))
    hosts = {h: k for k, hs in captura._HOSTS_POR_CASA.items() for h in hs}
    casas, sem_casa = set(), set()
    for cs in manifesto["content_scripts"]:
        for js in cs.get("js", []):
            nome = js.split("/")[-1]
            if not nome.endswith("_inject.js") or nome[:-len("_inject.js")] not in ADAPTADORES:
                continue
            for m in cs["matches"]:
                host = re.sub(r"^\*://(\*\.)?", "", m).rstrip("/*")
                if host.endswith(".bet.br"):
                    continue
                (casas.add(hosts[host]) if host in hosts else sem_casa.add(host))
    assert not sem_casa, f"host de casa com adaptador fora do `_HOSTS_POR_CASA`: {sem_casa}"
    return casas


def test_a_lista_e_a_do_manifesto():
    assert set(captura.CASAS_COM_FICHA) == _derivar_casas_com_ficha()
    assert not any(c in captura.CASAS_COM_FICHA for c in ("VAIDEBET", "BET365", "BETANO"))


def test_rota_casas_manda_a_lista_ficha(monkeypatch):
    async def _com_dados(dono):
        return ["Thunderpick", "GiroCerto", "Vaidebet"]

    async def _dominios(dono):
        return {}
    monkeypatch.setattr(main, "casas_com_parceiros", _com_dados)
    monkeypatch.setattr(main, "get_casas_dominios", _dominios)
    r = asyncio.run(main.listar_casas(dono="TDonoBloq"))
    assert "Thunderpick" in r["ficha"]
    assert "GiroCerto" not in r["ficha"] and "Vaidebet" not in r["ficha"]
    assert set(r["ficha"]) <= set(r["casas"])
