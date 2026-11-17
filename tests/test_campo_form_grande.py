"""Captura grande não morre no limite de 1 MB do formulário (s459, auditoria EXTENSÃO A4).

O Starlette recusava com 400 todo campo de texto acima de 1 MB, antes de a rota rodar. A
captura inteira vai num campo só, então quem voltava depois de meses (milhares de bilhetes)
tomava "Erro ao enviar (400)" para sempre. Aqui um texto de 3 MB chega à rota: sem sessão
válida ela responde 401, que é a prova de que o corpo foi lido.

O que NÃO está coberto: o proxy da Railway, que pode ter limite próprio de corpo.
"""
from fastapi.testclient import TestClient

import main


def test_texto_de_3mb_passa_pelo_formulario():
    texto = ("Bilhete [Código: X123] Stake: 10,00 Odd: 1,90 Ganho\n" * 60000)[: 3 * 1024 * 1024]
    assert len(texto.encode()) > 1024 * 1024 * 2
    r = TestClient(main.app).post(
        "/captura/enviar",
        data={"token": "inexistente", "tipo": "texto", "texto": texto},
        files={"_": ("", b"", "application/octet-stream")},
    )
    assert r.status_code == 401, (r.status_code, r.text[:200])


def test_o_teto_continua_existindo():
    assert main._MAX_CAMPO_FORM >= 8 * 1024 * 1024
