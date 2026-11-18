"""Aposta EXCLUÍDA que volta pela captura (s460, proposta do Feca aprovada em 18/11/2026).

A captura varre o histórico da casa, e a aposta apagada pelo usuário voltava calada na varredura
seguinte. Agora:

  1. a linha que volta com código que o usuário excluiu (lixeira, motivo da TELA) nasce marcada
     (`voltou_excluida`) e o lote ganha um alerta;
  2. a exclusão automática (Juntadas, duplicata de script) NÃO marca: não foi decisão do usuário;
  3. a aposta que nunca foi excluída nasce sem marca, e a mesma aposta em OUTRA casa também;
  4. "Manter" tira a marca, e só das linhas do dono;
  5. "Excluir de vez" leva a linha à lixeira e bloqueia o código: a captura seguinte não grava;
  6. o bloqueio vale só para aquele dono e aquela casa;
  7. o pré-dedup do /extrair enxerga o bloqueio (`codigos_excluidos_de_vez`), sem custo de IA;
  8. "Liberar" desfaz o bloqueio, e a aposta volta na captura seguinte;
  9. o contador da conta (`contar_incompletos`) e o filtro da grade (`pendencia=voltou`) usam o
     MESMO predicado.

Mutações provadas à mão em 18/11/2026: ver o STATUS da sessão 460.

NÃO cobre: a tela (selo amarelo e botões; ver `tests/js/excluida_que_volta.mjs`) e as rotas
HTTP (casca fina sobre estas funções, com o `dono` da sessão).
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


DONO, OUTRO = "TVolta", "TVoltaB"


def _row(**kw):
    base = dict(casa="Stake.com", parceiro="Gabriel", codigo_bilhete="V1", data="01/11/2026",
                esporte="Futebol", tipster="", aposta="ML", descricao="A vs B - A",
                stake="100,00", odd="1,90", resultado="W", stake_usd=None)
    base.update(kw)
    return base


async def _reset():
    await init_db()
    pool = await get_pool()
    async with pool.acquire() as conn:
        for t in ("bilhetes", "lixeira_bilhetes", "exclusao_confirmada"):
            await conn.execute(f"DELETE FROM {t} WHERE dono = ANY($1)", [DONO, OUTRO])


async def _linha(codigo="V1", dono=DONO):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM bilhetes WHERE dono = $1 AND codigo_bilhete = $2", dono, codigo)


async def _apagar_pela_tela(codigo="V1", dono=DONO):
    r = await _linha(codigo, dono)
    await repository.deletar_bilhetes([r["id"]], dono, "selecionadas")


async def _voltou(codigo="V1", dono=DONO, **kw):
    """O ciclo real: grava, o usuário exclui pela tela, a captura traz de volta (marcada)."""
    await repository.upsert_bilhetes([_row(codigo_bilhete=codigo, **kw)], dono)
    await _apagar_pela_tela(codigo, dono)
    await repository.upsert_bilhetes([_row(codigo_bilhete=codigo, **kw)], dono)
    return await _linha(codigo, dono)


def test_1_volta_marcada_e_com_alerta():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row()], DONO)
        await _apagar_pela_tela()
        _i, _u, _ids, alertas, _d = await repository.upsert_bilhetes([_row()], DONO)
        assert (await _linha())["voltou_excluida"] is not None
        assert any("excluído" in a for a in alertas)
    _run(body())


def test_2_exclusao_automatica_nao_marca():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row()], DONO)
        r = await _linha()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await repository._mover_para_lixeira(
                conn, "b.id = ANY($1) AND b.dono = $2", [[r["id"]], DONO],
                "Juntadas no bilhete X (mesma posição da casa, 1 aposta(s))")
        _i, _u, _ids, alertas, _d = await repository.upsert_bilhetes([_row()], DONO)
        assert (await _linha())["voltou_excluida"] is None
        assert not any("excluído" in a for a in alertas)
    _run(body())


def test_3_nunca_excluida_e_outra_casa_nascem_sem_marca():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row()], DONO)
        await _apagar_pela_tela()
        await repository.upsert_bilhetes([_row(codigo_bilhete="V2"),
                                          _row(casa="Betano")], DONO)
        assert (await _linha("V2"))["voltou_excluida"] is None
        pool = await get_pool()
        async with pool.acquire() as conn:
            r = await conn.fetchrow("SELECT voltou_excluida FROM bilhetes WHERE dono = $1 "
                                    "AND casa = 'Betano' AND codigo_bilhete = 'V1'", DONO)
        assert r["voltou_excluida"] is None
    _run(body())


def test_4_manter_tira_a_marca_so_do_dono():
    async def body():
        await _reset()
        for d in (DONO, OUTRO):
            await repository.upsert_bilhetes([_row()], d)
            await _apagar_pela_tela(dono=d)
            await repository.upsert_bilhetes([_row()], d)
        meu, dele = await _linha(), await _linha(dono=OUTRO)
        n = await repository.manter_voltaram([meu["id"], dele["id"]], DONO)
        assert n == 1
        assert (await _linha())["voltou_excluida"] is None
        assert (await _linha(dono=OUTRO))["voltou_excluida"] is not None
    _run(body())


def test_5_excluir_de_vez_bloqueia_a_captura_seguinte():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row()], DONO)
        await _apagar_pela_tela()
        await repository.upsert_bilhetes([_row()], DONO)
        r = await repository.excluir_de_vez([(await _linha())["id"]], DONO)
        assert r["excluidas"] == 1
        assert await _linha() is None
        ins, _u, ids, _a, _d = await repository.upsert_bilhetes([_row()], DONO)
        assert ins == 0 and ids == []
        assert await _linha() is None
    _run(body())


def test_5b_linha_nunca_marcada_nao_e_excluida_de_vez():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row()], DONO)
        r = await repository.excluir_de_vez([(await _linha())["id"]], DONO)
        assert r["excluidas"] == 0 and await _linha() is not None
    _run(body())


def test_6_bloqueio_e_do_dono_e_da_casa():
    async def body():
        await _reset()
        await repository.excluir_de_vez([(await _voltou())["id"]], DONO)
        await repository.upsert_bilhetes([_row()], OUTRO)
        await repository.upsert_bilhetes([_row(casa="Betano")], DONO)
        assert await _linha(dono=OUTRO) is not None
        assert await _linha() is not None          # a da Betano
        # outra grafia da MESMA casa continua bloqueada (chave da casa)
        await repository.upsert_bilhetes([_row(casa="stake.com", parceiro="Gabriel")], DONO)
        pool = await get_pool()
        async with pool.acquire() as conn:
            n = await conn.fetchval("SELECT count(*) FROM bilhetes WHERE dono = $1 "
                                    "AND codigo_bilhete = 'V1' AND casa <> 'Betano'", DONO)
        assert n == 0
    _run(body())


def test_7_pre_dedup_enxerga_o_bloqueio():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(codigo_bilhete="V2")], DONO)
        await repository.excluir_de_vez([(await _voltou())["id"]], DONO)
        assert await repository.codigos_excluidos_de_vez(["V1", "V2"], DONO, "Stake.com") == {"V1"}
        assert await repository.codigos_excluidos_de_vez(["V1"], DONO, "Betano") == set()
        assert await repository.codigos_excluidos_de_vez(["V1"], OUTRO, "Stake.com") == set()
    _run(body())


def test_8_liberar_desfaz_o_bloqueio():
    async def body():
        await _reset()
        await repository.excluir_de_vez([(await _voltou())["id"]], DONO)
        lista = await repository.listar_excluidas_de_vez(DONO)
        assert [(x["casa"], x["codigo"]) for x in lista] == [("STAKECOM", "V1")]
        assert lista[0]["casa_nome"] == "Stake.com" and lista[0]["descricao"] == "A vs B - A"
        assert await repository.liberar_excluidas_de_vez([["STAKECOM", "V1"]], OUTRO) == 0
        assert await repository.liberar_excluidas_de_vez([["STAKECOM", "V1"]], DONO) == 1
        await repository.upsert_bilhetes([_row()], DONO)
        assert await _linha() is not None
    _run(body())


def test_9_contador_e_filtro_com_o_mesmo_predicado():
    async def body():
        await _reset()
        # Com tipster e liquidadas: só a VOLTA pode pôr a conta no contador (sem isso o
        # "sem tipster" a punha lá e a falta do `voltaram` no HAVING passava verde).
        await repository.upsert_bilhetes([_row(tipster="T"), _row(codigo_bilhete="V2", tipster="T")], DONO)
        await _apagar_pela_tela()
        await repository.upsert_bilhetes([_row(tipster="T")], DONO)
        inc = await repository.contar_incompletos(DONO)
        assert [(x["casa"], x["parceiro"], x["voltaram"]) for x in inc] == \
            [("Stake.com", "Gabriel", 1)]
        lst = await repository.list_bilhetes(DONO, "Stake.com", "Gabriel", archived="all",
                                             pendencia="voltou")
        assert [b["codigo_bilhete"] for b in lst] == ["V1"]
        assert await repository.contar_bilhetes(DONO, "Stake.com", "Gabriel", archived="all",
                                                pendencia="voltou") == 1
    _run(body())
