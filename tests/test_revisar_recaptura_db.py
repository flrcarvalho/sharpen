"""Exceção "REVISAR" ao congelamento do UPSERT (s460, decisão do Feca em 18/11/2026).

`Mercado Especial - REVISAR` é o marcador que a IA grava quando não soube ler o mercado. Com o
congelamento, a recaptura nunca o trocava e o usuário apagava a aposta para recapturar (o
Gabriel, 06 a 16/11: 1.126 exclusões, 471 voltaram com outra descrição). Agora:

  1. a linha com REVISAR aceita a leitura que chega SEM ele, nos três campos juntos;
  2. a leitura que ainda diz REVISAR não muda nada;
  3. a linha limpa segue congelada (regressão do congelamento);
  4. o pré-dedup (`get_codigos_resolvidos`) não pula a liquidada com REVISAR;
  5. a barreira (`blocos_conhecidos(gravados=True)`) não a dá por lida;
  6. a Ficha (`virada._liquidados`) não a dá por liquidada.

Mutações provadas à mão em 18/11/2026 (cada uma deixou vermelho o teste indicado):
  · tirar o `OR __TROCA_REVISAR__` da descrição no ON CONFLICT → 1;
  · trocar `AND NOT {sql_a_revisar(*novo)}` por nada → 2;
  · trocar o `_TROCA_REVISAR_UPSERT` por `TRUE` → 3;
  · tirar a linha do `sql_a_revisar` em `get_codigos_resolvidos` → 4;
  · tirar a linha do `sql_a_revisar` em `blocos_conhecidos` → 5;
  · tirar o `AND NOT` em `virada._liquidados` → 6.

NÃO cobre: o fallback do `UniqueViolationError` (só dispara em corrida entre dois /salvar; usa a
mesma função `_troca_revisar`) e o custo de a IA reler, a cada captura, a aposta cuja leitura
continua saindo com REVISAR (limitado ao número dessas linhas).
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
    import virada  # noqa: E402
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


DONO = "TRevisar"
REV = "Mercado Especial - REVISAR"


def _row(**kw):
    base = dict(casa="Betano", parceiro="Gabriel", codigo_bilhete="R1", data="01/11/2026",
                esporte="Basquete", tipster="", aposta="REVISAR", descricao=REV,
                stake="100,00", odd="1,90", resultado="W", stake_usd=None)
    base.update(kw)
    return base


async def _reset():
    await init_db()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM bilhetes WHERE dono = $1", DONO)
        await conn.execute("DELETE FROM bloco_visto WHERE dono = $1", DONO)


async def _linha(codigo="R1"):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM bilhetes WHERE dono = $1 AND codigo_bilhete = $2", DONO, codigo)


def test_1_leitura_limpa_troca_os_tres_campos_e_nada_mais():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row()], DONO)
        await repository.upsert_bilhetes([_row(
            esporte="Basquete", aposta="Pontos", descricao="Lakers vs Celtics - Over 210,5",
            odd="5,00", stake="999,00")], DONO)
        r = await _linha()
        assert (r["descricao"], r["aposta"], r["esporte"]) == \
            ("Lakers vs Celtics - Over 210,5", "Pontos", "Basquete")
        # o resto do congelamento não muda: odd e stake da liquidada ficam
        assert (r["odd"], r["stake"]) == ("1,90", "100,00")
    _run(body())


def test_2_leitura_que_ainda_diz_revisar_nao_muda_nada():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(aposta="ML")], DONO)
        await repository.upsert_bilhetes([_row(aposta="Pontos", esporte="Futebol",
                                               descricao="Outra - REVISAR")], DONO)
        r = await _linha()
        assert (r["descricao"], r["aposta"], r["esporte"]) == (REV, "ML", "Basquete")
    _run(body())


def test_3_linha_limpa_segue_congelada():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(aposta="ML", descricao="A vs B - A")], DONO)
        await repository.upsert_bilhetes([_row(aposta="Pontos", descricao="A vs B - outra")],
                                         DONO)
        r = await _linha()
        assert (r["descricao"], r["aposta"]) == ("A vs B - A", "ML")
    _run(body())


def test_4_pre_dedup_nao_pula_a_liquidada_com_revisar():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(codigo_bilhete="R1"),
                                          _row(codigo_bilhete="L1", aposta="ML",
                                               descricao="A vs B - A")], DONO)
        res = await repository.get_codigos_resolvidos(["R1", "L1"], DONO, "Betano", "Gabriel")
        assert res == {"L1"}
    _run(body())


def test_5_barreira_nao_da_por_lida_a_linha_com_revisar():
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO bloco_visto (dono, casa, codigo, bloco_hash, atualizado_em) VALUES "
                "($1, 'Betano', 'R1', 'h1', NOW() - interval '1 hour'), "
                "($1, 'Betano', 'L1', 'h2', NOW() - interval '1 hour')", DONO)
        await repository.upsert_bilhetes([_row(codigo_bilhete="R1"),
                                          _row(codigo_bilhete="L1", aposta="ML",
                                               descricao="A vs B - A")], DONO)
        conh = await repository.blocos_conhecidos(DONO, "Betano", ["R1", "L1"], "Gabriel",
                                                  gravados=True)
        assert conh == {"L1": "h2"}
    _run(body())


def test_6_ficha_nao_da_por_liquidada_a_linha_com_revisar():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(codigo_bilhete="R1"),
                                          _row(codigo_bilhete="L1", aposta="ML",
                                               descricao="A vs B - A")], DONO)
        pool = await get_pool()
        async with pool.acquire() as conn:
            liq = await virada._liquidados(conn, DONO, "BETANO", ["R1", "L1"], "Gabriel")
        assert liq == {"L1"}
    _run(body())
