"""Harness de camada-DB (#11 da auditoria turbo) — exerce `upsert_bilhetes` e o escopo por
`dono` contra um Postgres REAL. Cobre o caminho de ESCRITA de dinheiro que o conftest normal
stuba (~50 funções async sem teste: dinheiro, dedup, tenancy).

Só roda quando `TEST_DATABASE_URL` aponta para um Postgres de TESTE local (CI). Sem essa var
(dev local, ambiente do Feca), a suíte inteira é PULADA — nunca toca o banco de produção.
O CI sobe um serviço `postgres:16` em localhost e seta a var. Ver `tests/conftest.py`.
"""
import asyncio
import os

import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DB,
    reason="sem TEST_DATABASE_URL — harness de DB só roda no CI (Postgres de teste)",
)

# Trava de segurança: recusa qualquer URL que não seja um Postgres local de teste. Impede,
# por construção, apontar o harness (que faz TRUNCATE) para o banco de produção.
if TEST_DB and not ("localhost" in TEST_DB or "127.0.0.1" in TEST_DB):
    raise RuntimeError(
        "TEST_DATABASE_URL deve ser um Postgres de teste local (localhost/127.0.0.1) — "
        "recusando por segurança para nunca tocar produção."
    )

if TEST_DB:
    # get_pool() lê DATABASE_URL; apontamos para o banco de teste ANTES de importar o
    # repository/database reais (o conftest já pulou os stubs por causa de TEST_DATABASE_URL).
    os.environ["DATABASE_URL"] = TEST_DB
    import repository  # noqa: E402
    from database import get_pool, init_db  # noqa: E402


def _row(**kw):
    """Linha mínima válida para `upsert_bilhetes` (Betano resolvida, com código)."""
    base = dict(
        casa="Betano", parceiro="Feca [Eu]", codigo_bilhete="BET1",
        data="01/07/2026", esporte="Futebol", tipster="",
        aposta="ML", descricao="Time A vs Time B", stake="100,00",
        odd="1,90", resultado="W", stake_usd=None,
    )
    base.update(kw)
    return base


async def _reset():
    """Schema idempotente + tabela `bilhetes` limpa antes de cada teste."""
    await init_db()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE bilhetes RESTART IDENTITY CASCADE")


async def _count(dono):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM bilhetes WHERE dono=$1", dono)


async def _get(dono, codigo):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM bilhetes WHERE dono=$1 AND codigo_bilhete=$2", dono, codigo
        )


def test_upsert_insere_depois_atualiza():
    """Mesmo código reprocessado → INSERT na 1ª, UPDATE na 2ª (dedup por ID, nunca duplica)."""
    async def body():
        await _reset()
        ins, upd, ids, _alertas, _dup = await repository.upsert_bilhetes([_row()], "TDonoA")
        assert (ins, upd) == (1, 0)
        assert len(ids) == 1
        ins2, upd2, ids2, _a2, _d2 = await repository.upsert_bilhetes([_row()], "TDonoA")
        assert (ins2, upd2) == (0, 1)
        assert ids2 == ids                      # mesma linha física
        assert await _count("TDonoA") == 1
    asyncio.run(body())


def test_upsert_isola_por_dono():
    """Mesmo código sob donos diferentes = linhas distintas; um dono nunca vê a do outro."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row()], "TDonoA")
        await repository.upsert_bilhetes([_row()], "TDonoB")   # mesmo código, outro dono
        assert await _count("TDonoA") == 1
        assert await _count("TDonoB") == 1
        ra = await _get("TDonoA", "BET1")
        rb = await _get("TDonoB", "BET1")
        assert ra["dono"] == "TDonoA" and rb["dono"] == "TDonoB"
        assert ra["id"] != rb["id"]            # duas linhas físicas separadas
    asyncio.run(body())


def test_upsert_aberta_para_resolvida_nao_rebaixa():
    """Bilhete ABERTO (sem resultado/odd) que resolve depois: as 2 blindagens do ON CONFLICT.
    (1) resolve preenche resultado e refresca odd (era 'aberta'); (2) uma re-leitura tardia
    'aberta' (sem resultado) NÃO rebaixa a linha já resolvida nem apaga a odd."""
    async def body():
        await _reset()
        # Aberto: sem resultado e sem odd → extraction_state 'aberta'.
        await repository.upsert_bilhetes([_row(resultado="", odd="")], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["extraction_state"] == "aberta"
        assert (r["resultado"] or "") == ""

        # Resolve: mesmo código → mesma assinatura → UPDATE. odd é refrescada (era 'aberta').
        await repository.upsert_bilhetes([_row(resultado="W", odd="1,90")], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert (r["resultado"] or "").upper() == "W"
        assert r["extraction_state"] != "aberta"
        assert r["odd"] == "1,90"

        # Blindagem 1: re-leitura tardia 'aberta' (sem resultado) não rebaixa a resolvida.
        await repository.upsert_bilhetes([_row(resultado="", odd="")], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert (r["resultado"] or "").upper() == "W"      # continua resolvida
        assert r["odd"] == "1,90"                          # odd preservada
        assert await _count("TDonoA") == 1                 # nunca duplicou
    asyncio.run(body())
