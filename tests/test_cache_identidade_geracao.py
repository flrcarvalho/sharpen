"""O refresher de identidade não grava retrato velho por cima de recarga nova (s459, SERVIDOR P1).

Roteiro do auditor: o refresher começa a ler o banco; no meio, a troca de senha grava e recarrega
o cache; o refresher termina depois com o retrato de ANTES. Sem a geração, a senha nova dava
"inválida" por até 60 s e o trial nascia morto. Código real do `auth` e do `main._usuarios_refresher`.
"""
import asyncio

import auth
import main


def test_retrato_velho_do_refresher_nao_desfaz_a_recarga(monkeypatch):
    original = dict(auth._usuarios_cache)
    velho = [{"username": "fulano", "status": "ativo", "senha_hash": "VELHO"}]
    novo = [{"username": "fulano", "status": "ativo", "senha_hash": "NOVO"}]
    auth.atualizar_cache_usuarios(velho)

    async def carregar_lento():
        # enquanto o SELECT do refresher "corre", a rota de senha recarrega o cache
        auth.atualizar_cache_usuarios(novo)
        return velho

    async def dorme(_s):
        if dorme.n:
            raise asyncio.CancelledError
        dorme.n += 1
    dorme.n = 0
    monkeypatch.setattr(main, "carregar_usuarios", carregar_lento)
    monkeypatch.setattr(main.asyncio, "sleep", dorme)
    try:
        asyncio.run(main._usuarios_refresher())
    except asyncio.CancelledError:
        pass
    assert auth._usuarios_cache["fulano"]["senha_hash"] == "NOVO", \
        "o retrato velho do refresher desfez a troca de senha"
    auth._usuarios_cache = original


def test_refresher_sem_concorrencia_continua_atualizando():
    original = dict(auth._usuarios_cache)
    g = auth.geracao_cache_usuarios()
    auth.atualizar_cache_usuarios([{"username": "x", "status": "ativo"}], geracao_lida=g)
    assert "x" in auth._usuarios_cache
    auth._usuarios_cache = original
