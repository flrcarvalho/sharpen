"""D50 (Feca, 11/11/2026): "nada pode ser gasto sem ser medido". O `uso_tokens.caminho` diz de
que tipo foi o lote de cada extração: 'print' (imagem colada), 'pdf' (página de PDF), vazio no
texto. E o aquecedor de cache grava o próprio uso, com caminho 'aquecedor'.

Estes testes rodam o `/extrair` REAL (a função `main.extrair`) até a porta da IA: os dois
geradores (`_stream_sequential` e `_stream_parallel`) são dublês que só guardam o `caminho`
que receberam. O aquecedor roda a rodada real (`_aquecer_uma_vez`) com o cliente da Anthropic
dublado.

O QUE NÃO COBREM: a chamada à IA de verdade e o INSERT em `uso_tokens` (o `registrar_uso` é o
de sempre, coberto pelo harness de banco); que os geradores repassam o `caminho` ao
`registrar_uso` (é a mesma linha de antes, que o vigia e o contrato já usam).
Mutações (s449, detectadas): U1 sem o ramo do print, U2 o PDF não marca `_tem_pdf`, U3 o texto
ganha caminho, U4 o aquecedor sem registro.
"""
import asyncio
import io
import sys
from types import SimpleNamespace

sys.path.insert(0, "app")

import pytest  # noqa: E402
from starlette.datastructures import Headers, UploadFile  # noqa: E402

import main  # noqa: E402

_PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
_IMG = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AA=="}}


def _arquivo(nome, tipo, dados=_PNG):
    return UploadFile(file=io.BytesIO(dados), filename=nome,
                      headers=Headers({"content-type": tipo}))


@pytest.fixture
def geradores(monkeypatch):
    recebidos = []

    def _duble(*a, **kw):
        recebidos.append(kw.get("caminho"))

        async def _vazio():
            yield "data: {}\n\n"
        return _vazio()
    monkeypatch.setattr(main, "_stream_sequential", _duble)
    monkeypatch.setattr(main, "_stream_parallel", _duble)
    monkeypatch.setattr(main.auth_mod, "eh_trial", lambda d: False)
    monkeypatch.setattr(main, "_pdf_para_blocos_imagem", lambda raw, nome: [dict(_IMG)])
    return recebidos


def _extrair(**kw):
    args = dict(casa="GiroCerto", parceiro="conta [Op]", modelo=main.DEFAULT_MODEL, texto=None,
                csv_content=None, imagens=[], pdfs=[], xls_file=None, data_referencia=None,
                dono="TDonoUso")
    args.update(kw)
    return asyncio.run(main.extrair(**args))


def test_lote_com_imagem_grava_print(geradores):
    _extrair(imagens=[_arquivo("a.png", "image/png")])
    assert geradores == ["print"]


def test_lote_com_pdf_grava_pdf(geradores):
    _extrair(pdfs=[_arquivo("extrato.pdf", "application/pdf", b"%PDF-1.4")])
    assert geradores == ["pdf"]


def test_lote_misto_de_imagem_e_pdf_conta_como_pdf(geradores):
    _extrair(imagens=[_arquivo("a.png", "image/png")],
             pdfs=[_arquivo("extrato.pdf", "application/pdf", b"%PDF-1.4")])
    assert geradores == ["pdf"]


def test_lote_de_texto_continua_sem_caminho(geradores):
    _extrair(texto="Aposta simples\nStake 10\nOdd 2,00\nGanhou")
    assert geradores == [None]


def test_caminho_que_ja_vinha_nao_e_trocado():
    """O contrato de texto chama o gerador com 'contrato4'/'atual_pos_contrato': fica."""
    assert main._caminho_do_lote([{"type": "text", "text": "x"}], False, "contrato4") == \
        "contrato4"


def test_aquecedor_grava_o_uso_com_caminho_aquecedor(monkeypatch):
    usos = []

    async def _criar(**kw):
        return SimpleNamespace(usage=SimpleNamespace(
            input_tokens=3, output_tokens=0, cache_read_input_tokens=0,
            cache_creation_input_tokens=41000))

    async def _registrar(dono, casa, modelo, chunks, n_itens, tokens, caminho=None):
        usos.append((dono, caminho, tokens))
    monkeypatch.setattr(main, "_client",
                        SimpleNamespace(messages=SimpleNamespace(create=_criar)))
    monkeypatch.setattr(main, "registrar_uso", _registrar)
    monkeypatch.setattr(main, "build_system", lambda k: [])
    monkeypatch.setattr(main, "_variantes_do_aquecedor", lambda: [{}, {"thinking": "x"}])

    async def rodar():
        await main._aquecer_uma_vez()
        await asyncio.sleep(0.01)                 # o registro vai por `_fire`
    asyncio.run(rodar())
    tk = {"input": 3, "output": 0, "cache_read": 0, "cache_write": 41000}
    assert usos == [(main.AQUECEDOR_DONO, "aquecedor", tk)] * 2
