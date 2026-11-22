"""Poda de órfãos do cadastro de tipsters poupa o ARQUIVADO (s463).

`list_tipsters_cadastro` apaga o tipster sem bilhete e sem info, mas o "sem bilhete" só olha a
base do PRÓPRIO dono. O supervisor vê na tela os tipsters dos operadores (feed consolidado), e
o Deano, que só existe na base do Lava, era arquivado pelo Feca e apagado na listagem seguinte:
voltava como ativo pela união com os bilhetes, e o "inativo" parecia não pegar.

  1. arquivado sem bilhete e sem info sobrevive à listagem;
  2. ativo sem bilhete e sem info continua sendo podado (o typo corrigido some, como antes);
  3. com bilhete do próprio dono, ativo fica (regressão do NOT EXISTS).

Mutação provada à mão em 22/11/2026: tirar o `AND t.arquivado = FALSE` do DELETE deixa o 1
vermelho.

NÃO cobre: a poda continua sem olhar a base dos operadores; um ativo sem info de tipster que
só existe na base do operador segue sendo apagado (o box o mostra de novo pela união, sem perda).
"""
import asyncio
import os

import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DB, reason="sem TEST_DATABASE_URL — harness de DB só roda com Postgres de teste")

if TEST_DB and not ("localhost" in TEST_DB or "127.0.0.1" in TEST_DB):
    raise RuntimeError("TEST_DATABASE_URL deve ser um Postgres de teste local.")

if TEST_DB:
    os.environ["DATABASE_URL"] = TEST_DB
    import database  # noqa: E402
    import repository  # noqa: E402
    from database import get_pool, init_db  # noqa: E402
    _LOOP = asyncio.new_event_loop()


def _run(coro):
    return _LOOP.run_until_complete(coro)


@pytest.fixture(scope="module", autouse=True)
def _fecha_pool_e_loop():
    yield
    if getattr(database, "_pool", None) is not None:
        _run(database._pool.close())
        database._pool = None
    _LOOP.close()


DONO = "TPodaTipster"


async def _reset():
    await init_db()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM bilhetes WHERE dono = $1", DONO)
        await conn.execute("DELETE FROM tipsters WHERE dono = $1", DONO)


async def _nomes():
    rows = await repository.list_tipsters_cadastro(DONO, incluir_arquivados=True)
    return {r["nome"]: r["arquivado"] for r in rows}


def test_1_arquivado_sem_bilhete_sobrevive_a_listagem():
    async def body():
        await _reset()
        t = await repository.criar_tipster("Deano", DONO)
        assert await repository.arquivar_tipster(t["id"], DONO)
        assert (await _nomes()).get("Deano") is True
        assert (await _nomes()).get("Deano") is True   # e na listagem seguinte também
    _run(body())


def test_2_ativo_sem_bilhete_e_sem_info_continua_podado():
    async def body():
        await _reset()
        await repository.criar_tipster("Typo", DONO)
        assert "Typo" not in await _nomes()
    _run(body())


def test_3_ativo_com_bilhete_do_dono_fica():
    async def body():
        await _reset()
        await repository.criar_tipster("Real", DONO)
        await repository.upsert_bilhetes([dict(
            casa="Betano", parceiro="P", codigo_bilhete="PT1", data="01/11/2026",
            esporte="Futebol", tipster="Real", aposta="ML", descricao="A vs B",
            stake="10,00", odd="2,00", resultado="W", stake_usd=None)], DONO)
        assert (await _nomes()).get("Real") is False
    _run(body())
