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
    import database  # noqa: E402
    import repository  # noqa: E402
    from database import get_pool, init_db  # noqa: E402

    # UM único event loop para todo o módulo. O pool asyncpg é cacheado num global
    # (`database._pool`) e fica PRESO ao loop onde nasceu. Se cada teste usasse seu próprio
    # `asyncio.run()` (loop novo), o 2º teste reusaria o pool preso ao loop já fechado —
    # "got Future attached to a different loop". E fechar/terminar o pool de outro loop também
    # falha ("Event loop is closed"), porque o abort agenda um call_soon no loop antigo. Um
    # loop compartilhado resolve os dois: pool nasce e morre no mesmo loop.
    _LOOP = asyncio.new_event_loop()


def _run(coro):
    """Roda a corrotina no loop compartilhado do módulo (ver bloco acima)."""
    return _LOOP.run_until_complete(coro)


@pytest.fixture(scope="module", autouse=True)
def _fecha_pool_e_loop():
    """Fecha o pool DENTRO do loop que o criou (senão o abort bate em loop já fechado) e só
    então fecha o loop. Roda uma vez ao fim do módulo."""
    yield
    if getattr(database, "_pool", None) is not None:
        _run(database._pool.close())
        database._pool = None
    _LOOP.close()


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
    _run(body())


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
    _run(body())


def test_upsert_canoniza_resultado_minusculo():
    """Lado da ESCRITA do bug case-sensitive (#179): 'w'/'v' minúsculo entra e é gravado
    canônico ('W'/'V') via .strip().upper() no upsert — senão ficava 'aberta' (parecia
    resolvido mas contava como aguardando). A regressão existente só cobria a leitura."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(codigo_bilhete="C1", resultado="  w ")], "TDonoA")
        r = await _get("TDonoA", "C1")
        assert r["resultado"] == "W"
        assert r["extraction_state"] != "aberta"
    _run(body())


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
    _run(body())


# ── Conta em outra moeda (s390, `app/cambio.py`) ─────────────────────────────
#
# A stake vai ao banco SEMPRE em R$; `moeda`/`stake_orig`/`cotacao` guardam a origem. A
# regra que só o Postgres prova: a origem ANDA JUNTO com a stake, na mesma condição do
# congelamento. Atualizar uma sem as outras deixaria `stake ≠ stake_orig × cotacao`.

def _usdt(**kw):
    base = dict(casa="Dex Sport", moeda="USDT", stake="130,00", stake_orig=25.0, cotacao=5.2)
    base.update(kw)
    return _row(**base)


def test_moeda_grava_a_origem_da_stake_com_os_tipos_da_coluna():
    """NUMERIC exige Decimal no asyncpg: um float aqui estoura DataError no driver."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_usdt()], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["stake"] == "130,00"
        assert r["moeda"] == "USDT"
        assert str(r["stake_orig"]) == "25.00"
        assert str(r["cotacao"]) == "5.200000"
    _run(body())


def test_moeda_segue_a_stake_ao_liquidar_e_congela_depois():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_usdt(resultado="", stake_orig=20.0,
                                                stake="104,00")], "TDonoA")
        # Liquida: a linha estava 'aberta', stake e origem refrescam JUNTAS.
        await repository.upsert_bilhetes([_usdt(resultado="W")], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert (r["stake"], str(r["stake_orig"])) == ("130,00", "25.00")
        # Resolvida: re-leitura com outra cotação não mexe em NENHUMA das quatro.
        await repository.upsert_bilhetes([_usdt(resultado="W", stake="250,00",
                                                stake_orig=50.0, cotacao=5.0)], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert (r["stake"], str(r["stake_orig"]), str(r["cotacao"])) == \
            ("130,00", "25.00", "5.200000")
    _run(body())


def test_lote_em_reais_numa_aberta_larga_a_origem_velha():
    """Conta que deixou de ser USDT: a stake nova está em R$, e a origem USDT não pode
    ficar ao lado dela dizendo outra coisa."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_usdt(resultado="")], "TDonoA")
        await repository.upsert_bilhetes([_row(casa="Dex Sport", resultado="",
                                               stake="90,00")], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["stake"] == "90,00"
        assert r["moeda"] is None and r["stake_orig"] is None and r["cotacao"] is None
    _run(body())


def test_moeda_da_conta_vem_do_cadastro_e_o_padrao_e_real():
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoA'")
            await conn.execute(
                "INSERT INTO parceiros (dono, casa, nome, moeda) VALUES "
                "('TDonoA', 'Dex Sport', 'Feca', 'USDT'), ('TDonoA', 'Betano', 'Feca', DEFAULT)")
        assert await repository.moeda_da_conta("TDonoA", "Dex Sport", "Feca") == "USDT"
        assert await repository.moeda_da_conta("TDonoA", "Betano", "Feca") == "BRL"
        assert await repository.moeda_da_conta("TDonoA", "Nenhuma", "Feca") == "BRL"
        # Isolamento por dono: a conta USDT de um não vale para o outro.
        assert await repository.moeda_da_conta("TDonoB", "Dex Sport", "Feca") == "BRL"
    _run(body())


def test_polymarket_conta_passa_a_usd_so_a_dela():
    """s397: o sync põe em USD a conta Polymarket que gravou; nenhuma outra conta muda."""
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono IN ('TDonoA', 'TDonoB')")
            await conn.execute(
                "INSERT INTO parceiros (dono, casa, nome) VALUES "
                "('TDonoA', 'Polymarket', 'Feca [Eu]'), ('TDonoA', 'Betano', 'Feca [Eu]'), "
                "('TDonoB', 'Polymarket', 'Feca [Eu]')")
        assert await repository.polymarket_conta_em_usd("TDonoA", "Feca [Eu]") is True
        assert await repository.polymarket_conta_em_usd("TDonoA", "Feca [Eu]") is False
        assert await repository.moeda_da_conta("TDonoA", "Polymarket", "Feca [Eu]") == "USD"
        assert await repository.moeda_da_conta("TDonoA", "Betano", "Feca [Eu]") == "BRL"
        assert await repository.moeda_da_conta("TDonoB", "Polymarket", "Feca [Eu]") == "BRL"
    _run(body())


def test_caixa_polymarket_lanca_confere_e_nao_duplica():
    """s397: o sync grava depósitos/ajustes da blockchain (um por hash), o inicial
    automático e a conferência; rodar de novo não duplica nada. Trava aberta: grava os
    movimentos (são reais), mas não confere."""
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            # TDonoB também: outro teste deste módulo cria conta Polymarket para ele, e a
            # asserção "dono sem conta não grava" dependeria da ordem dos testes.
            await conn.execute("DELETE FROM parceiros WHERE dono IN ('TDonoA', 'TDonoB')")
            await conn.execute("INSERT INTO parceiros (dono, casa, nome, moeda) VALUES "
                               "('TDonoA', 'Polymarket', 'Feca [Eu]', 'USD')")
        await repository.upsert_bilhetes([_poly(
            codigo_bilhete="0xL", resultado="L", stake="500,00", odd="2,00", data="07/05/2026",
            moeda="USD", stake_orig=100.0, cotacao=5.0)], "TDonoA", origem="sync")
        dados = {
            "movimentos": [
                {"ref": "0xdep", "tipo": "deposito", "valor": 300.0, "data": "2026-05-06", "obs": "Depósito"},
                {"ref": "0xreb", "tipo": "ajuste", "valor": 2.5, "data": "2026-05-08", "obs": "Rebate"},
            ],
            "saldo": 202.5, "inicio": "2026-05-06", "trava": {"ok": True, "diferenca": 0.0},
        }
        r1 = await repository.caixa_polymarket_sync("TDonoA", "Feca [Eu]", dados)
        assert r1["ok"] and r1["novos"] == 2
        cx = r1["caixa"]
        # 0 + 300 + 2,5 − 100 (a L em DÓLAR, pela stake_orig) = 202,5 → confere
        assert cx["ligada"] and cx["moeda"] == "USD" and cx["disponivel"] == 202.5
        assert cx["estado"] == "confere" and cx["data_corte"] == "2026-05-06"
        r2 = await repository.caixa_polymarket_sync("TDonoA", "Feca [Eu]", dados)
        assert r2["novos"] == 0
        async with pool.acquire() as conn:
            n = await conn.fetch("SELECT tipo, count(*) c FROM caixa_mov WHERE dono = 'TDonoA' GROUP BY tipo")
        assert {x["tipo"]: x["c"] for x in n} == {"inicial": 1, "deposito": 1, "ajuste": 1, "conferencia": 1}
        trava_aberta = {**dados, "movimentos": [], "trava": {"ok": False, "diferenca": 281.82}}
        r3 = await repository.caixa_polymarket_sync("TDonoA", "Feca [Eu]", trava_aberta)
        assert not r3["ok"] and "não fechou" in r3["motivo"]
        sem_conta = await repository.caixa_polymarket_sync("TDonoB", "Feca [Eu]", dados)
        assert not sem_conta["ok"]
    _run(body())


def test_cambio_corretora_transferencia_venda_e_bolso():
    """s398 (passo 6): a corretora, o saque com destino e taxa, a venda que realiza e o
    bolso pelo `cambio_visao`, no SQL de verdade. Cotação fixa (5,00 em todo dia, 4,50
    hoje) para o teste não depender da Binance."""
    from unittest.mock import patch
    import cambio

    async def _nada(*a, **k):
        return None

    async def _hoje(moedas):
        return {"BRL": 1.0, **{m: 4.5 for m in moedas if m != "BRL"}}

    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM caixa_mov WHERE dono = 'TDonoC'")
            await conn.execute("DELETE FROM corretoras WHERE dono = 'TDonoC'")
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoC'")
        await repository.criar_parceiro("Betpanda", "Feca", "TDonoC", "USDT")
        async with pool.acquire() as conn:
            pid = await conn.fetchval("SELECT id FROM parceiros WHERE dono = 'TDonoC'")
        assert (await repository.caixa_lancar("TDonoC", pid, "inicial", "2026-10-01", 200.0))["ok"]
        cr = await repository.corretora_criar("TDonoC", "Binance")
        assert cr["ok"]
        assert not (await repository.corretora_criar("TDonoC", "binance"))["ok"], "nome único sem caixa"
        cid = cr["id"]
        r = await repository.caixa_lancar("TDonoC", pid, "saque", "2026-10-03", 50.0, "",
                                          cid, 1.0)
        assert r["ok"]
        assert (await repository.corretora_lancar("TDonoC", cid, "venda", "2026-10-04", "USDT",
                                                  49.0, 230.0))["ok"]
        with patch.object(cambio, "carregar", _nada), \
             patch.object(cambio, "cotacao", lambda m, iso: 5.0), \
             patch.object(repository, "_caixa_taxas_hoje", _hoje):
            v = await repository.cambio_visao("TDonoC")
            b = v["bolsos"]["USDT"]
            assert b["qtd"] == 150.0 and b["custo_brl"] == 750.0
            assert b["taxas_brl"] == 5.0 and b["realizado_brl"] == -15.0
            assert b["papel_brl"] == -75.0 and b["fecha"]
            corr = v["corretoras"][0]
            assert corr["nome"] == "Binance" and corr["saldos"] == {"USDT": 0.0}
            assert not (await repository.corretora_excluir("TDonoC", cid))["ok"], \
                "com lançamento a corretora não se apaga"
            assert (await repository.corretora_arquivar("TDonoC", cid, True))["ok"]
            async with pool.acquire() as conn:
                mid = await conn.fetchval(
                    "SELECT id FROM caixa_mov WHERE dono = 'TDonoC' AND tipo = 'saque'")
            # Editar a data sem `transferencia` não apaga o destino…
            assert (await repository.caixa_editar_mov("TDonoC", mid, "2026-10-03", 50.0))["ok"]
            assert (await repository.cambio_visao("TDonoC"))["bolsos"]["USDT"]["n_sem_destino"] == 0
            # …e com `transferencia` sem corretora, o saque passa a não ter destino.
            assert (await repository.caixa_editar_mov("TDonoC", mid, "2026-10-03", 50.0, "",
                                                      True, None, None))["ok"]
            assert (await repository.cambio_visao("TDonoC"))["bolsos"]["USDT"]["n_sem_destino"] == 1
    _run(body())


def test_moeda_no_cadastro_cria_lista_edita_e_reativa_sem_perder():
    """Passo 2 da moeda (s391): o cadastro grava, a listagem devolve e a edição troca.

    As duas regras que só o Postgres prova: `None` NÃO MEXE (na edição e na reativação de
    conta arquivada pelo ON CONFLICT do `criar_parceiro`) e a moeda é escrita ANTES do
    atalho de "nada mudou" (trocar só a moeda é edição legítima). Sem o COALESCE, recriar
    pelo campo inline uma conta USDT arquivada a devolveria em BRL."""
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoMoeda'")

        c = await repository.criar_parceiro("Dex Sport", "Feca", "TDonoMoeda", "USDT")
        assert c["moeda"] == "USDT"
        b = await repository.criar_parceiro("Betano", "Feca", "TDonoMoeda")
        assert b["moeda"] == "BRL", "conta sem moeda escolhida nasce em real"
        lista = {p["casa"]: p["moeda"] for p in await repository.list_parceiros("TDonoMoeda")}
        assert lista == {"Dex Sport": "USDT", "Betano": "BRL"}

        # Só a moeda muda: nome e casa iguais, e mesmo assim grava.
        assert (await repository.editar_parceiro(b["id"], "Feca", None, "TDonoMoeda",
                                                 None, "USD"))["ok"]
        assert await repository.moeda_da_conta("TDonoMoeda", "Betano", "Feca") == "USD"
        # None = não mexe.
        assert (await repository.editar_parceiro(b["id"], "Feca", None, "TDonoMoeda"))["ok"]
        assert await repository.moeda_da_conta("TDonoMoeda", "Betano", "Feca") == "USD"

        # Reativação pelo ON CONFLICT sem moeda: mantém a que a conta tinha.
        async with pool.acquire() as conn:
            await conn.execute("UPDATE parceiros SET arquivado = TRUE WHERE id = $1", c["id"])
        r = await repository.criar_parceiro("Dex Sport", "Feca", "TDonoMoeda")
        assert r["id"] == c["id"] and r["moeda"] == "USDT", "a reativação apagou a moeda"
        # Com moeda escolhida, a reativação adota a escolhida.
        r = await repository.criar_parceiro("Dex Sport", "Feca", "TDonoMoeda", "USD")
        assert r["moeda"] == "USD"
    _run(body())


def test_moeda_original_no_feed_e_a_edicao_que_limpa():
    """Passo 3 da moeda (s391). O feed do dashboard leva `moeda`/`stake_orig` SÓ na linha
    convertida, e a listagem da grade traz o `pl_orig`. s398 (passo 6.1): a edição à mão da
    stake RECALCULA a origem pela cotação da linha em vez de apagá-la, e a stake digitada
    na moeda refaz o R$. Regravar o mesmo número (o modal reenvia tudo) não mexe."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_usdt(), _row(codigo_bilhete="BET2", casa="Betano")],
                                         "TDonoA")
        feed = {l["casa"]: l for l in await repository.dashboard_rows(["TDonoA"])}
        assert feed["Dex Sport"]["moeda"] == "USDT" and feed["Dex Sport"]["stake_orig"] == 25.0
        assert feed["Dex Sport"]["lucro_orig"] is not None
        assert "moeda" not in feed["Betano"] and "stake_orig" not in feed["Betano"]
        assert "lucro_orig" not in feed["Betano"]

        grade = {l["codigo_bilhete"]: l for l in await repository.list_bilhetes("TDonoA")}
        assert grade["BET1"]["pl_orig"] is not None
        assert grade["BET2"]["pl_orig"] is None

        bid = grade["BET1"]["id"]
        assert await repository.atualizar_bilhete(bid, {"stake": "130"}, "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["moeda"] == "USDT", "regravar o mesmo número não pode apagar a origem"
        assert await repository.atualizar_bilhete(bid, {"stake": "156,00"}, "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["stake"] == "156,00"
        assert r["moeda"] == "USDT" and float(r["stake_orig"]) == 30.0
        assert float(r["cotacao"]) == 5.2, "a cotação é a do dia da aposta e não muda"
        assert await repository.atualizar_bilhete(bid, {"stake_orig": "40,00"}, "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["stake"] == "208,00" and float(r["stake_orig"]) == 40.0
        bet2 = grade["BET2"]["id"]
        assert not await repository.atualizar_bilhete(bet2, {"stake_orig": "40,00"}, "TDonoA"), \
            "linha em real não aceita stake em moeda: não há cotação para converter"
    _run(body())


# ── Fantasma do código cru (Polymarket: mercado ganha a 2ª compra) ────────────
#
# O código do bilhete depende de QUANTAS compras o mercado tem: 1 compra grava
# `cid`, e quando entra a 2ª o coletor passa a emitir `cid__0`/`cid__1`. A linha
# antiga some do radar do UPSERT e fica congelada em "aberta", esperando um
# resultado que nunca chega (caso real: 1 linha na base do Feca, s200).

def _poly(**kw):
    """Linha Polymarket em aberto. Os padrões entram por dict (não como keyword fixa),
    senão um `_poly(resultado=...)` colidiria com o padrão homônimo."""
    base = dict(casa="Polymarket", parceiro="Feca [Eu]", resultado="", odd="2,50")
    base.update(kw)
    return _row(**base)


def test_remove_codigo_cru_quando_mercado_vira_fatiado():
    """Código cru sai quando as fatias irmãs existem; o resto da conta não é tocado."""
    async def body():
        await _reset()
        # 1º sync: uma compra só → código CRU, aposta em aberto.
        await repository.upsert_bilhetes([_poly(codigo_bilhete="0xCID")], "TDonoA")
        # 2º sync: entrou a 2ª compra → o coletor passa a emitir as fatias.
        await repository.upsert_bilhetes([
            _poly(codigo_bilhete="0xCID__0", descricao="M [1/2]", resultado="L"),
            _poly(codigo_bilhete="0xCID__1", descricao="M [2/2]", resultado="W"),
        ], "TDonoA")
        # Um mercado de compra única, que NÃO pode ser afetado.
        await repository.upsert_bilhetes([_poly(codigo_bilhete="0xOUTRO",
                                                descricao="Outro")], "TDonoA")
        assert await _count("TDonoA") == 4          # o fantasma ainda está lá

        apagadas = await repository.remover_bilhetes_supersedidos(
            "TDonoA", "Polymarket", "Feca [Eu]", ["0xCID", "0xOUTRO"])
        assert len(apagadas) == 1
        assert apagadas[0]["codigo_bilhete"] == "0xCID"
        assert await _count("TDonoA") == 3
        assert await _get("TDonoA", "0xCID") is None       # fantasma removido
        assert await _get("TDonoA", "0xCID__0") is not None  # fatias intactas
        assert await _get("TDonoA", "0xCID__1") is not None
        assert await _get("TDonoA", "0xOUTRO") is not None   # compra única preservada
    _run(body())


def test_nao_remove_codigo_cru_sem_fatias_irmas():
    """Guarda auto-verificável: sem as fatias no banco (upsert falhou), nada é apagado."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_poly(codigo_bilhete="0xCID")], "TDonoA")
        apagadas = await repository.remover_bilhetes_supersedidos(
            "TDonoA", "Polymarket", "Feca [Eu]", ["0xCID"])
        assert apagadas == []
        assert await _get("TDonoA", "0xCID") is not None
    _run(body())


def test_remove_codigo_cru_respeita_dono_e_conta():
    """A remoção é escopada: não alcança outro dono nem outra conta da mesma casa."""
    async def body():
        await _reset()
        for dono in ("TDonoA", "TDonoB"):
            await repository.upsert_bilhetes([_poly(codigo_bilhete="0xCID")], dono)
            await repository.upsert_bilhetes([
                _poly(codigo_bilhete="0xCID__0", descricao="M [1/2]"),
                _poly(codigo_bilhete="0xCID__1", descricao="M [2/2]"),
            ], dono)
        # Outra conta do MESMO dono, com o mesmo código cru.
        await repository.upsert_bilhetes([_poly(codigo_bilhete="0xCID",
                                                parceiro="Feca [Outra]")], "TDonoA")

        apagadas = await repository.remover_bilhetes_supersedidos(
            "TDonoA", "Polymarket", "Feca [Eu]", ["0xCID"])
        assert len(apagadas) == 1
        assert await _count("TDonoB") == 3          # outro dono intocado
        pool = await get_pool()
        async with pool.acquire() as conn:
            outra = await conn.fetchval(
                "SELECT COUNT(*) FROM bilhetes WHERE dono='TDonoA' AND parceiro='Feca [Outra]'")
        assert outra == 1                            # outra conta intocada
    _run(body())


def test_get_tipster_por_codigo_so_traz_preenchido():
    """Carry-over do tipster: só devolve o que foi de fato atribuído."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([
            _poly(codigo_bilhete="0xCID", tipster="Nomade"),
            _poly(codigo_bilhete="0xVAZIO", descricao="Sem tipster", tipster=""),
        ], "TDonoA")
        got = await repository.get_tipster_por_codigo(
            "TDonoA", "Polymarket", "Feca [Eu]", ["0xCID", "0xVAZIO"])
        assert got == {"0xCID": "Nomade"}
    _run(body())


# ── Fonte determinística manda; fonte de IA continua blindada (s204) ─────────
#
# A blindagem congela odd/data/stake ao resolver, para a re-leitura ruidosa da IA não
# estragar a linha. Mas com fonte determinística ela impede que uma CORREÇÃO DE CÁLCULO
# alcance a linha antiga — e como `resultado` nunca foi blindado, o resultado novo
# convivia com a odd velha (28 linhas Polymarket com lucro fantasma).

def test_sync_refresca_financeiro_de_linha_ja_resolvida():
    """origem='sync': a fonte manda em odd/data/stake mesmo na linha já resolvida."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_row(casa="Polymarket", resultado="W", odd="1,96", stake="601,92",
                  data="02/06/2026")], "TDonoA", origem="sync")
        # O cálculo do coletor foi corrigido: mesma aposta, odd na metade.
        await repository.upsert_bilhetes(
            [_row(casa="Polymarket", resultado="W", odd="0,98", stake="601,92",
                  data="03/06/2026")], "TDonoA", origem="sync")
        r = await _get("TDonoA", "BET1")
        assert r["odd"] == "0,98"            # correção chegou
        assert r["data"] == "03/06/2026"
        assert (r["resultado"] or "").upper() == "W"
        assert await _count("TDonoA") == 1   # nunca duplicou
    _run(body())


def test_extracao_ia_continua_blindada_em_linha_resolvida():
    """origem='extracao' (IA): resolvida segue congelada — a blindagem original vale."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(resultado="W", odd="1,90")], "TDonoA")
        await repository.upsert_bilhetes([_row(resultado="W", odd="9,99",
                                               stake="777,00")], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["odd"] == "1,90"             # re-leitura da IA NÃO sobrescreve
        assert r["stake"] == "100,00"
    _run(body())


def test_sync_preserva_tipster_ao_refrescar():
    """A fonte manda no dinheiro, mas não apaga o tipster atribuído na grade."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_row(casa="Polymarket", tipster="Nomade", odd="1,96")], "TDonoA", origem="sync")
        await repository.upsert_bilhetes(
            [_row(casa="Polymarket", tipster="", odd="0,98")], "TDonoA", origem="sync")
        r = await _get("TDonoA", "BET1")
        assert r["odd"] == "0,98" and r["tipster"] == "Nomade"
    _run(body())


def test_sync_refresca_classificacao_de_linha_ja_resolvida():
    """esporte/aposta/descricao nunca eram atualizados (só no INSERT) — com fonte
    determinística isso trancava a correção do classificador fora do banco."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_row(casa="Polymarket", esporte="Outro", aposta="Player Props",
                  descricao="O/U 1.5 Rounds")], "TDonoA", origem="sync")
        await repository.upsert_bilhetes(
            [_row(casa="Polymarket", esporte="MMA", aposta="Rounds",
                  descricao="O/U 1.5 Rounds")], "TDonoA", origem="sync")
        r = await _get("TDonoA", "BET1")
        assert r["esporte"] == "MMA" and r["aposta"] == "Rounds"
        assert await _count("TDonoA") == 1
    _run(body())


def test_extracao_ia_nao_sobrescreve_classificacao():
    """Fora do sync a classificação segue intocada: a IA relê com ruído e o operador
    corrige na grade — uma re-extração não pode desfazer a correção dele."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(esporte="Futebol", aposta="Escanteios")], "TDonoA")
        await repository.upsert_bilhetes([_row(esporte="Outro", aposta="Outros")], "TDonoA")
        r = await _get("TDonoA", "BET1")
        assert r["esporte"] == "Futebol" and r["aposta"] == "Escanteios"
    _run(body())


# ── Pendências da grade (s258) ────────────────────────────────────────────────
#
# O predicado roda no Postgres: só um banco de verdade prova que a regex classifica
# como o rail conta. O caso que motivou tudo é o 1º: múltipla PERDIDA da Betfair que
# chegou sem odd (o P/L está certo — perda é −stake — mas a linha é invisível na
# grade paginada). O `stake` em pt-BR com ponto de milhar é o outro: ele derrubaria
# a query se o predicado fizesse cast para numeric.

def test_contar_pendencias_e_filtro_de_listagem():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([
            _row(codigo_bilhete="P1", odd="", resultado="L"),              # sem odd
            _row(codigo_bilhete="P2", odd="0,00"),                         # odd zerada
            _row(codigo_bilhete="P3", stake="", odd="2,10"),               # sem stake
            _row(codigo_bilhete="P4", aposta="Outros ⚠️", odd="2,10"),     # categoria incerta
            _row(codigo_bilhete="P5", stake="1.914,56", odd="1,90",
                 tipster="Peixe"),                                         # completa (milhar pt-BR)
        ], "TDonoA")

        p = await repository.contar_pendencias("TDonoA")
        assert p["sem_odd"] == 2          # P1 e P2 (vazia e zerada)
        assert p["sem_stake"] == 1        # P3
        assert p["categoria"] == 1        # P4
        assert p["sem_tipster"] == 4      # todas menos P5

        # A listagem filtrada devolve exatamente as mesmas linhas que o chip conta.
        linhas = await repository.list_bilhetes("TDonoA", archived="all", pendencia="sem_odd")
        assert {r["codigo_bilhete"] for r in linhas} == {"P1", "P2"}
        assert await repository.contar_bilhetes("TDonoA", archived="all", pendencia="sem_odd") == 2

        # Stake pt-BR com ponto de milhar NÃO é pendência (nem quebra a query).
        semstake = await repository.list_bilhetes("TDonoA", archived="all", pendencia="sem_stake")
        assert {r["codigo_bilhete"] for r in semstake} == {"P3"}
    _run(body())


def test_pendencia_desconhecida_nao_filtra_nada():
    """Querystring adulterada não vira SQL: o nome fora do dicionário é ignorado e a
    listagem volta completa (falha ABERTA, nunca com fragmento interpolado)."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(codigo_bilhete="Q1")], "TDonoA")
        linhas = await repository.list_bilhetes(
            "TDonoA", archived="all", pendencia="odd IS NULL) OR (1=1")
        assert len(linhas) == 1
    _run(body())


def test_pendencia_isolada_por_dono():
    """O contador é da conta do dono — nunca conta pendência do vizinho."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(codigo_bilhete="R1", odd="")], "TDonoA")
        await repository.upsert_bilhetes([_row(codigo_bilhete="R2", odd="")], "TDonoB")
        assert (await repository.contar_pendencias("TDonoA"))["sem_odd"] == 1
        assert (await repository.contar_pendencias("TDonoB"))["sem_odd"] == 1
    _run(body())


def test_perda_sem_odd_grava_resolvida():
    """s259 — o lado da ESCRITA do alinhamento `estado_extracao` × `calcular_pl`.
    Perda sem odd (múltipla que a casa entregou sem `combinedOdds`) tem P/L completo
    (−stake) e não pode nascer 'aberta': ficaria no badge âmbar para sempre. Já a
    VITÓRIA sem odd continua 'aberta' — ali o P/L é não-calculável."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([
            _row(codigo_bilhete="S1", resultado="L", odd=""),
            _row(codigo_bilhete="S2", resultado="V", odd=""),
            _row(codigo_bilhete="S3", resultado="W", odd=""),
        ], "TDonoA")
        assert (await _get("TDonoA", "S1"))["extraction_state"] == "resolvida"
        assert (await _get("TDonoA", "S2"))["extraction_state"] == "resolvida"
        assert (await _get("TDonoA", "S3"))["extraction_state"] == "aberta"

        # E o chip "Sem odd" continua enxergando as três — a pendência de campo vazio
        # não depende do estado (é isso que mantém a linha achável na grade).
        assert (await repository.contar_pendencias("TDonoA"))["sem_odd"] == 3
    _run(body())


# ── flags_pos_edicao: os dois avisos que a tela dá depois de salvar (s286) ─────────
# São AVISOS, não bloqueios — mas cada um cobre um jeito de a edição do usuário morrer em
# silêncio, e a condição de cada um mora no banco (código do bilhete, estado, origem).
# Por isso valem um teste contra Postgres REAL: a regra é uma leitura de linha, e um stub
# só provaria que o `if` do Python funciona.


def test_flags_sem_codigo_so_em_bilhete_sem_codigo():
    """`aposta` está em `_SIG_COLS` quando não há código: renomear o mercado muda a
    assinatura e a próxima captura INSERE em vez de deduplicar. Com código, o hash é
    ID|casa|parceiro|codigo — a aposta não entra, e nenhum aviso deve aparecer."""
    async def body():
        await _reset()
        _i, _u, ids_com, _a, _d = await repository.upsert_bilhetes([_row()], "TDonoA")
        _i2, _u2, ids_sem, _a2, _d2 = await repository.upsert_bilhetes(
            [_row(codigo_bilhete="", descricao="Sem codigo", stake="55,00")], "TDonoA")

        f = await repository.flags_pos_edicao(ids_com[0], "TDonoA", {"aposta"})
        assert f["sem_codigo"] is False
        f = await repository.flags_pos_edicao(ids_sem[0], "TDonoA", {"aposta"})
        assert f["sem_codigo"] is True
    _run(body())


def test_flags_volatil_so_enquanto_a_aposta_esta_aberta():
    """Enquanto `extraction_state='aberta'`, o `ON CONFLICT` refresca data/odd/stake a cada
    reenvio: a edição manual é DESFEITA sem aviso. Depois de resolver, o congelamento
    começa e a edição passa a valer — o aviso não pode aparecer aí, ou vira ruído."""
    async def body():
        await _reset()
        _i, _u, abertos, _a, _d = await repository.upsert_bilhetes(
            [_row(codigo_bilhete="AB1", resultado="", odd="")], "TDonoA")
        _i2, _u2, resolvidos, _a2, _d2 = await repository.upsert_bilhetes(
            [_row(codigo_bilhete="RS1")], "TDonoA")

        f = await repository.flags_pos_edicao(abertos[0], "TDonoA", {"stake"})
        assert f["volatil"] is True
        f = await repository.flags_pos_edicao(resolvidos[0], "TDonoA", {"odd", "data"})
        assert f["volatil"] is False
    _run(body())


def test_flags_volatil_nao_acusa_linha_lancada_a_mao():
    """Aposta `manual` não tem robô por trás — ninguém vai reenviá-la, então editar
    stake/odd/data nela vale, mesmo em aberto. Avisar ali seria alarme falso."""
    async def body():
        await _reset()
        _i, _u, ids, _a, _d = await repository.upsert_bilhetes(
            [_row(codigo_bilhete="MAN1", resultado="", odd="")], "TDonoA", origem="manual")
        f = await repository.flags_pos_edicao(ids[0], "TDonoA", {"stake"})
        assert f["volatil"] is False
    _run(body())


def test_flags_so_consulta_o_que_foi_editado_e_respeita_o_dono():
    """Campo sem armadilha → `{}` (nem consulta). Linha de OUTRO dono → `{}`, para a tela
    nunca inventar aviso sobre bilhete que não é dela — mesmo isolamento do resto."""
    async def body():
        await _reset()
        _i, _u, ids, _a, _d = await repository.upsert_bilhetes(
            [_row(codigo_bilhete="", resultado="", odd="")], "TDonoA")
        assert await repository.flags_pos_edicao(ids[0], "TDonoA", {"tipster"}) == {}
        assert await repository.flags_pos_edicao(ids[0], "TDonoA", set()) == {}
        assert await repository.flags_pos_edicao(ids[0], "TDonoB", {"aposta", "stake"}) == {}
        # e o caminho feliz continua devolvendo as duas juntas quando as duas se aplicam
        f = await repository.flags_pos_edicao(ids[0], "TDonoA", {"aposta", "stake"})
        assert f == {"sem_codigo": True, "volatil": True}
    _run(body())


# ── Modo sombra (Fase 0 do tradutor, s297) ───────────────────────────────────
# Estes dois exercem a camada que `tests/test_sombra.py` declara NÃO cobrir: o
# INSERT em lote e a PURGA por retenção. Existem porque o defeito real da s297 só
# aparecia com Postgres de verdade — o intervalo ia como `$1::interval` e o asyncpg
# recusa string crua nesse tipo. Como o INSERT já tinha commitado, a função devolvia
# 0 com as 4 linhas gravadas: erro invisível, do tipo meio-atualizado.

def test_sombra_grava_e_pareia_no_banco():
    """O corpo de treino chega ao banco com o bloco colado na decisão certa."""
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE sombra_rotulos RESTART IDENTITY")
        texto = ("[Código: AAA1]\nEsporte (casa): Soccer\nSeleções:\n  • Time A\n\n"
                 "[Código: BBB2]\nEsporte (casa): Tennis\nSeleções:\n  • Sinner\n")
        tsv = ("01/07/2026\tFutebol\t\tPinnacle\tc1\tML\tTime A\t10,00\t1,50\tW\tAAA1\n"
               "01/07/2026\tTênis\t\tPinnacle\tc1\tML\tSinner\t10,00\t1,75\tW\tBBB2")
        n = await repository.registrar_sombra("TDonoA", "Pinnacle", texto, tsv)
        assert n == 2, "o INSERT precisa relatar o que gravou (a purga não pode zerar isso)"
        async with pool.acquire() as conn:
            linhas = await conn.fetch(
                "SELECT codigo, bruto, ia_esporte FROM sombra_rotulos "
                "WHERE dono='TDonoA' ORDER BY id")
        assert [l["codigo"] for l in linhas] == ["AAA1", "BBB2"]
        # cada bloco é o do próprio bilhete — cruzar aqui envenena o corpo de treino
        assert "Time A" in linhas[0]["bruto"] and "Sinner" not in linhas[0]["bruto"]
        assert "Sinner" in linhas[1]["bruto"] and "Time A" not in linhas[1]["bruto"]
        assert [l["ia_esporte"] for l in linhas] == ["Futebol", "Tênis"]
    _run(body())


def test_sombra_purga_o_velho_e_preserva_o_novo():
    """A purga por retenção roda de verdade (o bug da s297 era exatamente ela)."""
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE sombra_rotulos RESTART IDENTITY")
            # linha plantada ALÉM da janela de retenção
            await conn.execute(
                "INSERT INTO sombra_rotulos (criado_em, dono, casa, codigo, bruto) "
                "VALUES (NOW() - ($1 || ' days')::interval, 'TDonoA', 'Pinnacle', 'VELHO', 'x')",
                str(repository._SOMBRA_DIAS + 5))
        texto = "[Código: NOVO1]\nSeleções:\n  • Time A\n"
        tsv = "01/07/2026\tFutebol\t\tPinnacle\tc1\tML\tTime A\t10,00\t1,50\tW\tNOVO1"
        assert await repository.registrar_sombra("TDonoA", "Pinnacle", texto, tsv) == 1
        async with pool.acquire() as conn:
            codigos = [r["codigo"] for r in await conn.fetch(
                "SELECT codigo FROM sombra_rotulos WHERE dono='TDonoA'")]
        assert "NOVO1" in codigos, "a linha nova tem de sobreviver à própria purga"
        assert "VELHO" not in codigos, "a purga por retenção não rodou"
    _run(body())


# ── Barreira de recaptura: o JOIN, que é SQL e só o banco prova (s376) ───────
#
# `tests/test_barreira_recaptura.py` declara no cabeçalho que NÃO toca o banco e que o
# JOIN de `blocos_conhecidos` "tem de ser conferido contra o Postgres real antes de a
# barreira valer em produção". Ninguém foi conferir, e o limite declarado virou o buraco:
# o `_filtro_conta` acrescentava ` AND casa = $3` sem qualificar a tabela, as DUAS do JOIN
# têm essa coluna, e o `AmbiguousColumnError` caía no `except` que devolve `{}`. Resultado
# medido em produção: de 09/09 a 20/09 a barreira NÃO pulou um bloco sequer, com o CI
# verde o tempo todo, porque o modo de falha dela é economia que não acontece.
#
# Estes dois exercem `registrar_blocos_vistos` + `blocos_conhecidos` de ponta a ponta.

async def _reset_barreira():
    await _reset()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE bloco_visto")


def test_blocos_conhecidos_filtra_por_conta_no_banco():
    """O caso que estava quebrado: COM casa e parceiro, o JOIN tem de devolver o hash.

    Antes do conserto esta chamada levantava `AmbiguousColumnError` lá dentro e a função
    devolvia `{}` — verde em teste de unidade, morta em produção."""
    async def body():
        await _reset_barreira()
        texto = "[Código: BAR1]\nStake: R$ 10,00\nSeleções:\n  • Time A\n"
        await repository.upsert_bilhetes(
            [_row(casa="Bet365", parceiro="Feca [Eu]", codigo_bilhete="BAR1")], "TDonoA")
        assert await repository.registrar_blocos_vistos("TDonoA", "Bet365", texto) == 1

        esperado = repository.hash_bloco(repository.blocos_por_codigo(texto)["BAR1"])
        # sem escopo de conta (comportamento antigo dos chamadores que não têm a conta)
        assert await repository.blocos_conhecidos("TDonoA", None, ["BAR1"]) == {"BAR1": esperado}
        # COM escopo de conta — é esta que a barreira usa, e é esta que morria
        assert await repository.blocos_conhecidos(
            "TDonoA", "Bet365", ["BAR1"], "Feca [Eu]") == {"BAR1": esperado}
        # conta errada não pode entregar o hash: "já tenho" significa "nesta conta"
        assert await repository.blocos_conhecidos(
            "TDonoA", "Bet365", ["BAR1"], "Outra [Conta]") == {}
        # dono errado idem (tenancy)
        assert await repository.blocos_conhecidos(
            "TDonoB", "Bet365", ["BAR1"], "Feca [Eu]") == {}
    _run(body())


def test_hash_sem_bilhete_no_banco_nao_e_conhecido():
    """Costura 3 contra o banco: `/extrair` e `/salvar` são endpoints separados, então o
    hash pode existir para bilhete que nunca chegou à tabela. Sem o JOIN ele ficaria
    invisível para sempre — a barreira o pularia e a aposta nunca entraria."""
    async def body():
        await _reset_barreira()
        texto = "[Código: ORFAO1]\nStake: R$ 10,00\nSeleções:\n  • Time A\n"
        assert await repository.registrar_blocos_vistos("TDonoA", "Bet365", texto) == 1
        assert await repository.blocos_conhecidos(
            "TDonoA", "Bet365", ["ORFAO1"], "Feca [Eu]") == {}
    _run(body())


# ── Janela de vida da conta (s322/s323) ──────────────────────────────────────
# Estes três exercem o SCHEMA_SQL de verdade. Sem eles o job de banco só provava que a
# migração NÃO EXPLODE: o backfill roda dentro de um `DO ... EXCEPTION WHEN others` (um erro
# ali faria rollback do schema inteiro), então uma falha sairia como WARNING e o CI ficaria
# verde com a coluna vazia. Engolir a exceção transforma falha em dado ausente — a mesma
# armadilha do `_ptax` da s247; a saída é medir o RESULTADO, não a ausência de erro.

def test_backfill_de_adquirida_em_le_a_data_no_formato_do_BANCO():
    """`bilhetes.data` é TEXT e guarda DD/MM/YYYY (ISO também passa direto — as duas formas
    convivem na coluna). Ler só ISO faria o backfill não achar quase nada e toda conta antiga
    nascer com a janela começando no `criado_em`, que em base importada é a data do IMPORT."""
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoJanela'")
            # Cadastro criado HOJE (como num import), com apostas bem anteriores.
            await conn.execute(
                "INSERT INTO parceiros (dono, casa, nome, adquirida_em) "
                "VALUES ('TDonoJanela', 'Betano', 'Velha [Eu]', NULL)")
            for data in ("15/03/2026", "20/04/2026"):          # formato do banco
                await conn.execute(
                    "INSERT INTO bilhetes (dono, casa, parceiro, assinatura, data, stake, odd, resultado) "
                    "VALUES ('TDonoJanela', 'Betano', 'Velha [Eu]', $1, $2, '10,00', '1,50', 'W')",
                    "sigjanela" + data, data)
            # Conta ISO, para provar que o outro ramo do CASE também é lido.
            await conn.execute(
                "INSERT INTO parceiros (dono, casa, nome, adquirida_em) "
                "VALUES ('TDonoJanela', 'Bet365', 'Iso [Eu]', NULL)")
            await conn.execute(
                "INSERT INTO bilhetes (dono, casa, parceiro, assinatura, data, stake, odd, resultado) "
                "VALUES ('TDonoJanela', 'Bet365', 'Iso [Eu]', 'sigjaneliso', '2026-02-09', '10,00', '1,50', 'W')")
            # Conta que nunca apostou: a janela começa no cadastro.
            await conn.execute(
                "INSERT INTO parceiros (dono, casa, nome, adquirida_em) "
                "VALUES ('TDonoJanela', 'Superbet', 'SemAposta [Eu]', NULL)")

        await init_db()   # é aqui que o backfill roda

        async with pool.acquire() as conn:
            linhas = {r["nome"]: r for r in await conn.fetch(
                "SELECT nome, adquirida_em, criado_em::date AS cad FROM parceiros "
                "WHERE dono = 'TDonoJanela'")}
        assert str(linhas["Velha [Eu]"]["adquirida_em"]) == "2026-03-15", (
            "o backfill não leu DD/MM/YYYY — toda conta antiga nasceria com a janela "
            "começando na data do import")
        assert str(linhas["Iso [Eu]"]["adquirida_em"]) == "2026-02-09", "o ramo ISO não foi lido"
        assert linhas["SemAposta [Eu]"]["adquirida_em"] == linhas["SemAposta [Eu]"]["cad"], (
            "conta sem aposta nenhuma deveria cair no criado_em")
    _run(body())


def test_renovacao_entra_na_lista_da_conta_e_sai_pelo_id():
    """Renovação (s381) é valor + DATA do pagamento, anexada à conta. Cobre o que só o
    banco prova: o JSONB volta como str e a listagem entrega lista, o `||` anexa sem
    apagar a anterior, o DELETE tira só o item do id, e nada disso cruza dono."""
    from datetime import date

    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono IN ('TDonoRen', 'TOutroRen')")
            pid = await conn.fetchval(
                "INSERT INTO parceiros (dono, casa, nome, adquirida_em) "
                "VALUES ('TDonoRen', 'Superbet', 'c1 [Richard]', CURRENT_DATE) RETURNING id")

        antes = await repository.list_parceiros("TDonoRen")
        assert antes[0]["renovacoes"] == [], "conta nova tem de nascer com lista vazia"

        a = await repository.adicionar_renovacao(pid, "TDonoRen", "350.00", "2026-09-10")
        b = await repository.adicionar_renovacao(pid, "TDonoRen", 90, date(2026, 8, 1).isoformat())
        assert a and b and a["id"] != b["id"]
        assert a == {"id": a["id"], "valor": 350.0, "data": "2026-09-10"}

        ren = (await repository.list_parceiros("TDonoRen"))[0]["renovacoes"]
        assert [r["data"] for r in ren] == ["2026-08-01", "2026-09-10"], "a lista volta ordenada pela data"

        # Outro dono não anexa nem apaga na conta alheia.
        assert await repository.adicionar_renovacao(pid, "TOutroRen", 10, "2026-09-10") is None
        assert not await repository.remover_renovacao(pid, "TOutroRen", a["id"])

        assert await repository.remover_renovacao(pid, "TDonoRen", a["id"])
        ren = (await repository.list_parceiros("TDonoRen"))[0]["renovacoes"]
        assert [r["id"] for r in ren] == [b["id"]], "apagar tirou mais (ou menos) que o item"
        assert not await repository.remover_renovacao(pid, "TDonoRen", a["id"]), \
            "apagar o que já não existe não é sucesso"

        assert await repository.remover_renovacao(pid, "TDonoRen", b["id"])
        ren = (await repository.list_parceiros("TDonoRen"))[0]["renovacoes"]
        assert ren == [], "a lista vazia tem de voltar como [], nunca NULL"

        for ruim in [(0, "2026-09-10"), ("-5", "2026-09-10"), ("abc", "2026-09-10"), (10, "10/09/2026")]:
            with pytest.raises(ValueError):
                await repository.adicionar_renovacao(pid, "TDonoRen", *ruim)
    _run(body())


def test_arquivar_carimba_o_fim_da_janela_e_reativar_apaga():
    """O carimbo é o que faz o custo parar nos períodos seguintes. Arquivar duas vezes não
    pode empurrar o fim para a frente (COALESCE), e reativar tem de reabrir a janela — senão
    a conta volta a ser usada com o custo sumido dos dias em que ela já está em uso."""
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoJanela2'")
            pid = await conn.fetchval(
                "INSERT INTO parceiros (dono, casa, nome, adquirida_em) "
                "VALUES ('TDonoJanela2', 'Betano', 'Conta [Eu]', CURRENT_DATE) RETURNING id")

        assert await repository.arquivar_parceiro(pid, "TDonoJanela2")
        async with pool.acquire() as conn:
            r = await conn.fetchrow("SELECT arquivado, arquivada_em FROM parceiros WHERE id=$1", pid)
        assert r["arquivado"] and r["arquivada_em"] is not None, "arquivar não carimbou o fim"
        primeiro = r["arquivada_em"]

        # Recuar o carimbo e arquivar de novo: o COALESCE tem de PRESERVAR o original.
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE parceiros SET arquivada_em = DATE '2026-01-05' WHERE id=$1", pid)
        assert await repository.arquivar_parceiro(pid, "TDonoJanela2")
        async with pool.acquire() as conn:
            de_novo = await conn.fetchval("SELECT arquivada_em FROM parceiros WHERE id=$1", pid)
        assert str(de_novo) == "2026-01-05", "arquivar de novo empurrou o fim da janela"

        assert await repository.reativar_parceiro(pid, "TDonoJanela2")
        async with pool.acquire() as conn:
            r = await conn.fetchrow("SELECT arquivado, arquivada_em FROM parceiros WHERE id=$1", pid)
        assert not r["arquivado"] and r["arquivada_em"] is None, "reativar não reabriu a janela"
        assert primeiro is not None
    _run(body())


def test_editar_parceiro_grava_a_data_de_compra_sem_mexer_em_nada_mais():
    """A data entra como `datetime.date`: coluna DATE + asyncpg que não converte tipo, então
    string crua estouraria DENTRO do driver e viraria 500 na rota (s314). E a escrita mora
    ANTES do atalho de "nada mudou" — trocar só a data é uma edição legítima."""
    from datetime import date

    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoJanela3'")
            pid = await conn.fetchval(
                "INSERT INTO parceiros (dono, casa, nome, adquirida_em) "
                "VALUES ('TDonoJanela3', 'Betano', 'Conta [Eu]', CURRENT_DATE) RETURNING id")

        res = await repository.editar_parceiro(pid, "Conta [Eu]", None, "TDonoJanela3", date(2026, 2, 1))
        assert res["ok"], res
        async with pool.acquire() as conn:
            r = await conn.fetchrow("SELECT nome, casa, adquirida_em FROM parceiros WHERE id=$1", pid)
        assert str(r["adquirida_em"]) == "2026-02-01", "a data de compra não foi gravada"
        assert r["nome"] == "Conta [Eu]" and r["casa"] == "Betano", "a edição mexeu no que não devia"

        # None = não mexe (é o que a rota manda quando o campo vem vazio).
        assert (await repository.editar_parceiro(pid, "Conta [Eu]", None, "TDonoJanela3", None))["ok"]
        async with pool.acquire() as conn:
            mantida = await conn.fetchval("SELECT adquirida_em FROM parceiros WHERE id=$1", pid)
        assert str(mantida) == "2026-02-01", "None deveria PRESERVAR a data, não apagá-la"
    _run(body())


def test_migracao_b_adota_orfa_quando_a_odd_so_muda_de_FORMATO():
    """s327 — o fantasma da Betnacional, ponta a ponta.

    A captura de 05/09 perdeu a 11ª coluna e gravou a múltipla do Falkirk SEM código,
    `aberta`, com `odd = "14"`. Em 06/09 o MESMO bilhete voltou liquidado, agora com
    código e `odd = "14,00"`. A Migração B comparava a odd como string CRUA, não adotou
    a órfã, e o bilhete entrou como linha NOVA — a velha ficou `aberta` para sempre.
    """
    async def body():
        await _reset()
        orfa = dict(codigo_bilhete="", resultado="", odd="14",
                    descricao="Falkirk // Wycombe // Preston")
        await repository.upsert_bilhetes([_row(**orfa)], "TDonoOrfa")
        assert await _count("TDonoOrfa") == 1

        # Mesmo bilhete, agora COM código e a odd escrita noutro formato.
        liquidado = dict(codigo_bilhete="NXBNAC1", resultado="L", odd="14,00",
                         descricao="Falkirk // Wycombe // Preston")
        await repository.upsert_bilhetes([_row(**liquidado)], "TDonoOrfa")

        assert await _count("TDonoOrfa") == 1, "duplicou: a órfã não foi adotada"
        r = await _get("TDonoOrfa", "NXBNAC1")
        assert r["resultado"] == "L"
        assert r["extraction_state"] != "aberta", "sobrou fantasma aberto"
    _run(body())


def test_migracao_b_nao_deixa_dois_bilhetes_adotarem_a_mesma_orfa():
    """Uma órfã só pode ser adotada UMA vez (o `pop` do índice).

    Sem isso, dois bilhetes do mesmo lote com data+aposta+stake+odd iguais reivindicariam
    a MESMA linha antiga: a segunda adoção reescreveria a assinatura recém-gravada pela
    primeira. A Migração B não duplica quando erra — ela sequestra.
    """
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_row(codigo_bilhete="", resultado="", odd="14", descricao="Órfã única")],
            "TDonoOrfa2")
        assert await _count("TDonoOrfa2") == 1

        # Dois bilhetes COM código, indistinguíveis pela chave da Migração B.
        await repository.upsert_bilhetes([
            _row(codigo_bilhete="COD-A", resultado="L", odd="14,00", descricao="Bilhete A"),
            _row(codigo_bilhete="COD-B", resultado="W", odd="14,00", descricao="Bilhete B"),
        ], "TDonoOrfa2")

        assert await _count("TDonoOrfa2") == 2, "um adota a órfã, o outro insere"
        pool = await get_pool()
        async with pool.acquire() as conn:
            sem_codigo = await conn.fetchval(
                "SELECT COUNT(*) FROM bilhetes WHERE dono='TDonoOrfa2' AND codigo_bilhete IS NULL")
            assinaturas = await conn.fetchval(
                "SELECT COUNT(DISTINCT assinatura) FROM bilhetes WHERE dono='TDonoOrfa2'")
        assert sem_codigo == 0, "sobrou linha sem código — o fantasma que a s327 caçou"
        assert assinaturas == 2, "as duas linhas colidiram na mesma assinatura"
    _run(body())


def test_upsert_adota_aberta_que_chegou_depois_da_caixa_ligada():
    """s327 — a LIGAÇÃO: `upsert_bilhetes` chama `_caixa_adotar_abertas_tardias`.

    A decisão de quem entra é testada com dublê em `tests/test_caixa_abertas_tardias.py`;
    o que só este harness pega é o fio solto — se alguém remover a chamada do
    `upsert_bilhetes`, lá tudo continua verde e a Caixa volta a nascer torta.

    Cenário medido: Caixa ligada às 03:17:32 com o banco ainda sem aberta nenhuma; o
    `/salvar` das 03:18:19 grava uma aposta capturada às 03:17:27 — antes da ativação.
    """
    from datetime import datetime, timedelta, timezone

    async def body():
        await _reset()
        pool = await get_pool()
        agora = datetime.now(timezone.utc)
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoTardia'")
            pid = await conn.fetchval(
                "INSERT INTO parceiros (dono, casa, nome) "
                "VALUES ('TDonoTardia', 'Betnacional', 'Conta [Eu]') RETURNING id")
            # Caixa ligada AGORA, sem nenhuma aberta no banco → abertas_corte vazio.
            mov = await conn.fetchval(
                "INSERT INTO caixa_mov (dono, parceiro_id, tipo, data, valor, abertas_corte) "
                "VALUES ('TDonoTardia', $1, 'inicial', CURRENT_DATE, 1, '{}') RETURNING id", pid)

        # A captura é ANTERIOR à ativação; o /salvar chega depois.
        ins, _upd, ids, _a, _d = await repository.upsert_bilhetes(
            [_row(casa="Betnacional", parceiro="Conta [Eu]", codigo_bilhete="TARDIA1",
                  resultado="", odd="14")],
            "TDonoTardia", criado_base=agora - timedelta(seconds=5))
        assert ins == 1

        async with pool.acquire() as conn:
            lista = await conn.fetchval("SELECT abertas_corte FROM caixa_mov WHERE id=$1", mov)
        assert list(lista or []) == ids, (
            "a aberta que já estava viva no corte não entrou no abertas_corte")

    _run(body())


def test_upsert_nao_adota_aberta_feita_DEPOIS_da_caixa_ligada():
    """O simétrico, e é ele que impede a correção de virar outro erro: o stake dessa
    saiu depois da leitura do saldo, então ela entra pelo P/L — adotá-la faria a
    projeção nascer alta em exatamente um stake."""
    from datetime import datetime, timedelta, timezone

    async def body():
        await _reset()
        pool = await get_pool()
        agora = datetime.now(timezone.utc)
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM parceiros WHERE dono = 'TDonoTardia2'")
            pid = await conn.fetchval(
                "INSERT INTO parceiros (dono, casa, nome) "
                "VALUES ('TDonoTardia2', 'Betnacional', 'Conta [Eu]') RETURNING id")
            mov = await conn.fetchval(
                "INSERT INTO caixa_mov (dono, parceiro_id, tipo, data, valor, abertas_corte) "
                "VALUES ('TDonoTardia2', $1, 'inicial', CURRENT_DATE, 1, '{}') RETURNING id", pid)

        await repository.upsert_bilhetes(
            [_row(casa="Betnacional", parceiro="Conta [Eu]", codigo_bilhete="TARDIA2",
                  resultado="", odd="14")],
            "TDonoTardia2", criado_base=agora + timedelta(minutes=5))

        async with pool.acquire() as conn:
            lista = await conn.fetchval("SELECT abertas_corte FROM caixa_mov WHERE id=$1", mov)
        assert list(lista or []) == [], "adotou aposta feita depois da leitura do saldo"

    _run(body())


# ── Migração B' (s338): o código lido de IMAGEM é adotado pelo código da captura ────
# O caso que abriu a regra: a Blaze do Jonathan. O card estampa um id de 19 dígitos, a
# IA lendo o PRINT erra quase sempre (53 de 55 códigos com comprimento errado) e erra
# DIFERENTE a cada leitura. Como o código entra na assinatura, o mesmo bilhete virou
# 5 linhas. Quando a captura chegou, com o código verdadeiro, ia virar a 6ª.

def _blaze(**kw):
    """Bilhete da Blaze — o formato do caso real (id numérico longo).

    Os campos entram por `dict.update` e não por `**kw` direto: passar `data=` no teste
    colidiria com o `data=` do default (`got multiple values`), e é justamente `data` que
    um dos casos precisa mudar para provar que a adoção não atravessa bilhetes.
    """
    base = dict(casa="Blaze", parceiro="jonathan@x [Pessoal]",
                data="31/08/2026", esporte="Badminton", aposta="ML",
                descricao="Susanto, Yulia Yosephine [Susanto v Pancasari]",
                stake="200,00", odd="1,85", resultado="W")
    base.update(kw)
    return _row(**base)


def test_captura_adota_a_linha_cujo_codigo_veio_de_print():
    """Print grava `codigo_ocr=TRUE` com o código torto; a captura chega com o código
    verdadeiro e ADOTA a linha — uma linha só, agora com o código certo e confiável."""
    async def body():
        await _reset()
        ins, _u, ids, _a, _d = await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="27062531440244968824")], "TOcrA", codigo_ocr=True)
        assert ins == 1
        r = await _get("TOcrA", "27062531440244968824")
        assert r["codigo_ocr"] is True, "print tem de gravar a procedência do código"

        ins2, upd2, ids2, _a2, _d2 = await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="2706253144924490123")], "TOcrA")
        assert (ins2, upd2) == (0, 1), "a captura inseriu de novo em vez de adotar"
        assert ids2 == ids, "adotou outra linha física"
        assert await _count("TOcrA") == 1
        novo = await _get("TOcrA", "2706253144924490123")
        assert novo is not None and novo["id"] == ids[0]
        assert novo["codigo_ocr"] is False, "código confirmado pela captura continua suspeito"
    _run(body())


def test_print_nao_adota_print():
    """Duas leituras de imagem são duas incertezas: trocar um código duvidoso por outro
    não torna nenhum dos dois verdadeiro, e escolheria no escuro qual é o dono da linha.
    Aqui as duas linhas coexistem — é o `reparar_duplicatas_codigo_ocr.py` que resolve,
    com olho humano."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="27062531440244968824")], "TOcrB", codigo_ocr=True)
        await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="2706253144924498034")], "TOcrB", codigo_ocr=True)
        assert await _count("TOcrB") == 2
    _run(body())


def test_captura_nao_adota_quando_ha_dois_candidatos():
    """Ambíguo não vira chute. Duas linhas de print com o mesmo data+aposta+stake+odd não
    dizem qual delas é este bilhete, e adotar a errada não duplica: SEQUESTRA a identidade
    de outro bilhete (o UPDATE reescreve código e assinatura de uma linha existente)."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="27062531440244968824")], "TOcrC", codigo_ocr=True)
        await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="2706253144924498034")], "TOcrC", codigo_ocr=True)
        ins, _u, _i, _a, _d = await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="2706253144924490123")], "TOcrC")
        assert ins == 1, "adotou uma das duas candidatas no escuro"
        assert await _count("TOcrC") == 3
    _run(body())


def test_captura_nao_adota_linha_de_outro_bilhete():
    """A chave da adoção é `chave_orfa` (casa+conta+data+aposta+stake+odd). Bilhete de
    outro dia, ou de outra stake, não é este — e adotá-lo apagaria o código de uma linha
    que não tem nada a ver."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="27062531440244968824", data="30/08/2026")],
            "TOcrD", codigo_ocr=True)
        ins, _u, _i, _a, _d = await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="2706253144924490123")], "TOcrD")
        assert ins == 1
        assert await _count("TOcrD") == 2
        velha = await _get("TOcrD", "27062531440244968824")
        assert velha is not None, "a linha do outro dia perdeu o código"
    _run(body())


def test_linha_sem_codigo_nao_e_marcada_como_ocr():
    """Casa sem marcador grava linha SEM código; ela já é da Migração B. Marcá-la aqui
    encheria o índice da B' de linha que ela nunca vai adotar."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes(
            [_blaze(codigo_bilhete="")], "TOcrE", codigo_ocr=True)
        pool = await get_pool()
        async with pool.acquire() as conn:
            r = await conn.fetchrow("SELECT * FROM bilhetes WHERE dono='TOcrE'")
        assert r["codigo_bilhete"] is None and r["codigo_ocr"] is False
    _run(body())


def test_confianca_do_codigo_so_desce():
    """Linha confirmada pela captura não volta a ser suspeita porque alguém colou um print
    depois. A fórmula é um AND das duas pontas, não um COALESCE."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_blaze(codigo_bilhete="COD9")], "TOcrF")
        await repository.upsert_bilhetes([_blaze(codigo_bilhete="COD9")], "TOcrF",
                                         codigo_ocr=True)
        r = await _get("TOcrF", "COD9")
        assert r["codigo_ocr"] is False
    _run(body())


def test_codigos_em_outra_conta_so_conta_o_que_esta_la_e_nao_aqui():
    """A consulta da trava de conta errada (s388), contra o Postgres.

    Três fronteiras: o código tem de estar noutra conta do MESMO dono e casa; código que
    também está nesta conta não conta (herança de captura errada antiga, senão a
    recaptura certa seria recusada); e casa/dono diferentes não se misturam."""
    async def body():
        await _reset()
        await repository.upsert_bilhetes([
            _row(casa="Superbet", parceiro="erick [A]", codigo_bilhete="SB1"),
            _row(casa="Superbet", parceiro="erick [A]", codigo_bilhete="SB2"),
            _row(casa="Superbet", parceiro="erick [A]", codigo_bilhete="SB3"),
            # SB3 também mora na conta que captura: não pode contar contra ela
            _row(casa="Superbet", parceiro="mama [R]", codigo_bilhete="SB3"),
            # mesmo código noutra CASA não é a mesma aposta
            _row(casa="Betano", parceiro="erick [A]", codigo_bilhete="SB4"),
        ], "TDonoA")
        # mesmo código noutro DONO: tenancy
        await repository.upsert_bilhetes(
            [_row(casa="Superbet", parceiro="erick [A]", codigo_bilhete="SB5")], "TDonoB")

        lote = ["SB1", "SB2", "SB3", "SB4", "SB5", "NOVO"]
        assert await repository.codigos_em_outra_conta(
            lote, "TDonoA", "Superbet", "mama [R]") == {"erick [A]": 2}
        # da própria conta que tem os códigos, nada é "de outra conta"
        assert await repository.codigos_em_outra_conta(
            ["SB1", "SB2"], "TDonoA", "Superbet", "erick [A]") == {}
        assert await repository.codigos_em_outra_conta(
            [], "TDonoA", "Superbet", "mama [R]") == {}
    _run(body())


# ── Freebet (s392, `MASTER_RESULTADO §5.8`) ───────────────────────────────────
#
# A coluna `stake_freebet` só PREENCHE: a parte da casa numa aposta não muda depois de feita.
# Duas coisas que só o Postgres prova: o NUMERIC aceita o que o `_freebet_da_linha` manda
# (Decimal), e o COALESCE vale em linha JÁ RESOLVIDA — é assim que a recaptura marca o
# histórico — sem que uma recaptura sem a marca (extensão velha, print) a apague.

def test_freebet_grava_e_recaptura_sem_marca_nao_apaga():
    async def body():
        await _reset()
        fb = {"FB1": "45,00"}
        await repository.upsert_bilhetes([_row(codigo_bilhete="FB1", stake="45,00",
                                               resultado="L")], "TDonoA", freebets=fb)
        r = await _get("TDonoA", "FB1")
        assert str(r["stake_freebet"]) == "45.00"
        await repository.upsert_bilhetes([_row(codigo_bilhete="FB1", stake="45,00",
                                               resultado="L")], "TDonoA")
        r = await _get("TDonoA", "FB1")
        assert str(r["stake_freebet"]) == "45.00"
        assert r["stake"] == "45,00"                        # o stake continua CHEIO
    _run(body())


def test_freebet_marca_linha_ja_resolvida_na_recaptura():
    async def body():
        await _reset()
        await repository.upsert_bilhetes([_row(codigo_bilhete="FB2", stake="45,00",
                                               resultado="L")], "TDonoA")
        assert (await _get("TDonoA", "FB2"))["stake_freebet"] is None
        await repository.upsert_bilhetes([_row(codigo_bilhete="FB2", stake="45,00",
                                               resultado="L")], "TDonoA",
                                         freebets={"FB2": "45,00"})
        assert str((await _get("TDonoA", "FB2"))["stake_freebet"]) == "45.00"
        assert await _count("TDonoA") == 1
    _run(body())


def test_ficha_sombra_grava_aceita_e_recusada_e_nao_duplica():
    """Ficha Sharpen em modo sombra (s409): o INSERT real, com os tipos que o asyncpg exige
    (`TEXT[]` como lista, `JSONB` como texto). Mesma Ficha duas vezes não duplica; impressão
    nova entra como linha nova; recusada fica gravada com o motivo e também não duplica."""
    import ficha

    async def body():
        await init_db()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE ficha_sombra RESTART IDENTITY")
        boa = {"codigo": "C1", "impressao": "i1", "status": "ganha"}
        ruim = {"codigo": "C2", "status": "won"}
        regs = [ficha._registro(boa, []), ficha._registro(ruim, ["status desconhecido: 'won'"])]
        assert await ficha.gravar("TDonoA", "DEXSPORT", "conta [Op]", "0.7.51", "dexsport.io",
                                  regs) == 2
        assert await ficha.gravar("TDonoA", "DEXSPORT", "conta [Op]", "0.7.51", "dexsport.io",
                                  regs) == 0
        nova = ficha._registro(dict(boa, impressao="i2"), [])
        assert await ficha.gravar("TDonoA", "DEXSPORT", "conta [Op]", "", "", [nova]) == 1
        async with pool.acquire() as conn:
            linhas = await conn.fetch(
                "SELECT casa, parceiro, codigo, aceita, motivos, ficha->>'status' st "
                "FROM ficha_sombra ORDER BY id")
        assert [(l["codigo"], l["aceita"]) for l in linhas] == [("C1", True), ("C2", False),
                                                                ("C1", True)]
        assert linhas[1]["motivos"] == ["status desconhecido: 'won'"]
        assert linhas[1]["st"] == "won" and linhas[0]["parceiro"] == "conta [Op]"
    _run(body())


def test_captura_crua_grava_uma_vez_e_cru_mudado_vira_linha_nova():
    """O cru da casa (s409): JSONB como texto, `removidos` como lista; cru igual não grava de
    novo (devolve None), cru mudado entra como linha nova, e a Ficha aponta o `cru_id`."""
    import cru as _cru
    import ficha

    async def body():
        await init_db()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE captura_crua RESTART IDENTITY")
            await conn.execute("TRUNCATE ficha_sombra RESTART IDENTITY")
        bilhete = {"id": "1d15646f-c666", "amount": 40, "payout": 158.8}
        item = {"codigo": bilhete["id"], "cru": bilhete, "hash": _cru.impressao(bilhete),
                "removidos": ["user"]}
        ids = await ficha.gravar_cru("TDonoA", "DEXSPORT", "conta [Op]", "dx", "0.7.52",
                                     "dexsport.io", [item])
        assert ids[0] is not None
        assert await ficha.gravar_cru("TDonoA", "DEXSPORT", "conta [Op]", "dx", "", "",
                                      [item]) == [None]
        mudado = dict(bilhete, payout=0)
        ids2 = await ficha.gravar_cru("TDonoA", "DEXSPORT", "conta [Op]", "dx", "", "",
                                      [dict(item, cru=mudado, hash=_cru.impressao(mudado))])
        assert ids2[0] is not None and ids2[0] != ids[0]
        reg = ficha._registro({"codigo": bilhete["id"], "impressao": "i"}, [], ids[0])
        assert await ficha.gravar("TDonoA", "DEXSPORT", "conta [Op]", "", "", [reg]) == 1
        async with pool.acquire() as conn:
            linhas = await conn.fetch("SELECT codigo, removidos, cru->>'payout' p "
                                      "FROM captura_crua ORDER BY id")
            cru_id = await conn.fetchval("SELECT cru_id FROM ficha_sombra")
        assert [(l["codigo"], l["p"]) for l in linhas] == [("1d15646f-c666", "158.8"),
                                                          ("1d15646f-c666", "0")]
        assert linhas[0]["removidos"] == ["user"] and cru_id == ids[0]
    _run(body())


# ── Virada da Ficha (`03_REGUA_NUMEROS §7`, s409): os 3 bilhetes chegam ao banco ──────────
# Mutações provadas contra este harness (Postgres local de teste, 12/10/2026; ver o
# cabeçalho de `tests/test_virada.py`):
#   A. a virada não grava a aceita (`gravar_aceitas` devolve 0)  → tres_bilhetes vermelho
#   B. a rota só monta a Ficha com a sombra ligada (sem o `or`)  → tres_bilhetes vermelho
#   C. o `/salvar` sem a `origem` da Ficha                        → tres_bilhetes vermelho
#   D. a virada ignora a chave (grava sempre)                     → desligada[VAVADA] vermelho
#      (escapava enquanto o caso "desligada" rodava com a sombra também desligada: a Ficha
#      nem era montada. O estado de produção é sombra LIGADA e virada desligada.)
#   s411 (dicionário e D10, mesmo Postgres local):
#   E. a virada grava mesmo com termo fora do dicionário          → termo_fora vermelho
#   s411, 2ª rodada (a aposta sai da IA na origem, enquanto aberta; D10 = não reescrever a
#   LIQUIDADA):
#   G. sem o filtro de liquidada (`_liquidados` vazio)            → d10_liquidada vermelho
#   H. o pré-dedup não corta o que a Ficha resolveu               → aberta_sai_da_ia vermelho
#   I. o /extrair não lê o cru guardado (só a rota grava)         → cru_guardado vermelho
#   O. a semente vota na linha gravada pela Ficha                 → virada_semente_nao_vota vermelho
#   s412 (furo N3, motivos, dicionário; 13/10/2026). O teste do N3 foi escrito ANTES da correção
#   e falhava (a IA recebia `[]`):
#   P. sem a checagem do cru velho (N3)                         → n3_texto_mudou vermelho
#   Q. a Ficha não grava o `bloco_visto` do que resolveu        → n3_texto_igual vermelho
#   S. o motivo não vai ao `virada_log`                         → n3_texto_mudou vermelho
#   Y. a aposta editada à mão vota                              → semente_ignora_aposta_editada vermelho
#   AH. o texto (`sombra_rotulos`) da aposta editada vota       → semente_ignora_aposta_editada vermelho
#   AA. o conserto mexe no mês passado                          → corrigir_termo vermelho
#   AB. o conserto passa por cima da correção manual            → corrigir_termo vermelho
#   AC. o conserto aceita valor fora do Master                  → corrigir_termo vermelho
#   AD. a semente não roda depois da IA                         → semente_roda_logo_depois vermelho
#   AE. sem `semente_log`                                       → semente_ignora + semente_roda vermelhos
#   s413 (dicionário de descrição; 13/10/2026):
#   D3. a semente não aprende a descrição da IA                 → virada_descricao_nova vermelho
#   D4. a semente não regrava a descrição do mês corrente       → semente_regrava_a_descricao vermelho
#   D5. a regravação mexe no mês passado                        → semente_regrava_a_descricao vermelho
#   D6. o motivo `descrição fora do dicionário` não vai ao log   → virada_descricao_nova vermelho

_VIRADA = ("5508528206", "5504514128", "5500000003")     # aceita, recusada, sem cru


def _virada_cenario(monkeypatch, chave, sombra="", termos=True, aberta=False):
    import json as _json
    from pathlib import Path
    from types import SimpleNamespace

    import ficha
    import main

    crus = _json.loads((Path(__file__).resolve().parent / "ficha_crus_familias.json")
                       .read_text(encoding="utf-8"))
    sess = SimpleNamespace(dono="TDonoV", casa_key="VAVADA", casa=main._casa_display("VAVADA"),
                           parceiro="conta [Op]")
    monkeypatch.setattr(ficha._captura, "sessao_por_token", lambda t: sess)
    monkeypatch.setattr(ficha._captura, "registrar_versao", lambda s, v: None)
    monkeypatch.setenv("FICHA_SOMBRA_CASAS", sombra)
    monkeypatch.delenv("CRU_CAPTURA_DESLIGADA", raising=False)
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", chave)
    aceita, recusada, _ = _VIRADA
    cru_aceita = dict(crus[aceita], status=0) if aberta else crus[aceita]
    payload = {"token": "t", "versao": "0.7.51", "familia": "vb", "itens": [
        {"codigo": aceita, "cru": cru_aceita},
        {"codigo": recusada, "cru": dict(crus[recusada], status=7)}]}   # status 7: recusa
    # O lote de TEXTO da mesma captura: os 3 bilhetes, como o SharpenUp manda sempre.
    texto = "\n\n".join(f"[Código: {c}]\nStake: 10\nStatus: Perdido\n" for c in _VIRADA)
    # Dicionário (s411): os termos da aceita, com o par que a semente daria. Sem eles, a
    # aceita vai para a IA (termo fora do dicionário).
    import dicionario
    from adaptadores import vb
    chaves = dicionario.chaves(vb.adaptar(crus[aceita], "VAVADA")) if termos else []
    sess.termos = [("VAVADA", t, k, "Futebol" if t == "esporte" else "Total de Escanteios")
                   for t, k in chaves]
    # s413: o dicionário de DESCRIÇÃO das duas pernas da aceita (o que a IA ensinou)
    if termos:
        sess.termos += [("VAVADA", "descricao", k, v) for k, v in _DESC_ACEITA.items()]
    return sess, payload, texto


_DESC_ACEITA = {"sporttypeid 1 | total cantos": "{ou} Escanteios",
                "sporttypeid 19 | handicap de sets": "{ent} {hc} Sets"}
_IA_ACEITA = ("Over 11.5 Escanteios [Vicenza v Pisa] // "
              "Haro Rioja (F) +1.5 Sets [Haro Rioja (F) v Haris (F)]")


async def _virada_ponta_a_ponta(sess, payload, texto, antes=None, virar_no_extrair=None):
    """Rota da Ficha → `/extrair` (o pré-dedup de sempre) → IA dublê → `/salvar`.
    `antes` = linha que a IA já tinha gravado (código, resultado). `virar_no_extrair` = a
    chave passa a valer só DEPOIS da rota (o cru chegou antes da virada)."""
    import os
    import ficha
    import main

    await _reset()
    pool = await get_pool()
    async with pool.acquire() as conn:
        for t in ("captura_crua", "ficha_sombra", "bloco_visto", "dicionario_termos",
                  "ficha_virada", "virada_log", "sombra_rotulos"):
            await conn.execute(f"TRUNCATE {t}")
        for casa, tipo, termo, sharpen in getattr(sess, "termos", []):
            await conn.execute("INSERT INTO dicionario_termos (casa, tipo, termo_casa, "
                               "termo_sharpen) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                               casa, tipo, termo, sharpen)
    if antes:
        cod, res = antes
        await main.gravar_tsv(main.SalvarRequest(
            tsv=f"10/10/2026\tFutebol\t\t{sess.casa}\t{sess.parceiro}\tML\tTime A [A vs B]"
                f"\t10\t2\t{res}\t{cod}", casa=sess.casa, parceiro=sess.parceiro),
            sess.dono, sess.dono)
    resp = await ficha.receber(payload)
    if virar_no_extrair is not None:
        os.environ["FICHA_CASAS_VIRADAS"] = virar_no_extrair
    para_ia, cortados = await main._dedup_superbet_text(texto, sess.dono, sess.casa,
                                                        sess.parceiro)
    lidos = repository.codigos_do_texto(para_ia)
    tsv = "\n".join(f"10/10/2026\tFutebol\t\t{sess.casa}\t{sess.parceiro}\tML\t"
                    f"Time A [A vs B]\t10\t2\tL\t{c}" for c in lidos)
    await main.gravar_tsv(main.SalvarRequest(tsv=tsv, casa=sess.casa, parceiro=sess.parceiro),
                          sess.dono, sess.dono)
    await asyncio.sleep(0.1)          # a métrica vai por `_fire`
    async with pool.acquire() as conn:
        banco = {r["codigo_bilhete"]: (r["origem"], r["resultado"]) for r in await conn.fetch(
            "SELECT codigo_bilhete, origem, resultado FROM bilhetes WHERE dono = $1", sess.dono)}
        sess.log = [dict(r) for r in await conn.fetch(
            "SELECT capturadas, ja_no_banco, pela_ficha, para_ia FROM virada_log")]
    return resp, sorted(lidos), cortados, banco


def test_virada_tres_bilhetes_chegam_ao_banco(monkeypatch):
    """Casa virada: a Ficha aceita grava pela Ficha e SAI do lote da IA; a recusada e a sem
    cru vão para a IA pelo texto. Os três terminam em `bilhetes`, nenhum some."""
    aceita, recusada, sem_cru = _VIRADA
    resp, lidos, cortados, banco = _run(_virada_ponta_a_ponta(
        *_virada_cenario(monkeypatch, "VAVADA")))
    assert resp["fichas"] == {"aceitas": 1, "recusadas": 1} and resp["na_planilha"] == 1
    assert (lidos, cortados) == (sorted([recusada, sem_cru]), 1)
    assert banco == {aceita: ("ficha", "W"), recusada: ("extracao", "L"),
                     sem_cru: ("extracao", "L")}


def test_virada_semente_nao_vota_na_linha_da_propria_ficha(monkeypatch):
    """O esporte da linha `origem='ficha'` saiu do dicionário: votar nela seria o dicionário
    votando em si mesmo. A aceita gravada pela Ficha fica sem par; a linha da IA vota."""
    import dicionario
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA")
    _run(_virada_ponta_a_ponta(sess, payload, texto))

    async def fontes():
        pool = await get_pool()
        async with pool.acquire() as conn:
            return (await dicionario.pares(conn))[2]
    assert _run(fontes()) == {"sem par": 1, "texto (esporte)": 0}


def test_virada_metrica_por_captura(monkeypatch):
    """Métrica de cada virada (Feca, 12/10): capturadas, quantas a IA não leu, quantas foram."""
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA")
    _run(_virada_ponta_a_ponta(sess, payload, texto))
    assert sess.log == [{"capturadas": 3, "ja_no_banco": 1, "pela_ficha": 0, "para_ia": 2}]


def test_virada_aberta_sai_da_ia_na_origem(monkeypatch):
    """A Ficha aceita grava a aposta ABERTA, e o pré-dedup a tira do lote da IA."""
    aceita, recusada, sem_cru = _VIRADA
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA", aberta=True)
    resp, lidos, cortados, banco = _run(_virada_ponta_a_ponta(sess, payload, texto))
    assert resp["na_planilha"] == 1 and banco[aceita] == ("ficha", None)
    assert (lidos, cortados) == (sorted([recusada, sem_cru]), 1)
    assert sess.log == [{"capturadas": 3, "ja_no_banco": 0, "pela_ficha": 1, "para_ia": 2}]


def test_virada_cru_guardado_antes_da_virada(monkeypatch):
    """A extensão não reenvia cru igual: o cru que chegou ANTES da virada (só sombra) é lido
    no `/extrair` e a Ficha grava a aposta. Sem isso a aberta antiga ficaria com a IA."""
    aceita, recusada, sem_cru = _VIRADA
    sess, payload, texto = _virada_cenario(monkeypatch, "", sombra="VAVADA")
    resp, lidos, cortados, banco = _run(_virada_ponta_a_ponta(
        sess, payload, texto, virar_no_extrair="VAVADA"))
    assert resp["na_planilha"] == 0
    assert banco[aceita] == ("ficha", "W") and (lidos, cortados) == (sorted([recusada, sem_cru]), 1)


def test_virada_termo_fora_do_dicionario_vai_para_a_ia(monkeypatch):
    """Regra do Feca (12/10): termo sem par conhecido vai para a IA, como hoje. A Ficha é
    aceita e guardada, mas não vai à planilha; a IA lê os três."""
    resp, lidos, cortados, banco = _run(_virada_ponta_a_ponta(
        *_virada_cenario(monkeypatch, "VAVADA", termos=False)))
    assert resp["fichas"] == {"aceitas": 1, "recusadas": 1} and resp["na_planilha"] == 0
    assert (lidos, cortados) == (sorted(_VIRADA), 0)
    assert {o for o, _ in banco.values()} == {"extracao"} and len(banco) == 3


def test_virada_aberta_da_ia_passa_para_a_ficha(monkeypatch):
    """Aposta ABERTA que a IA gravou antes da virada passa para a Ficha na próxima captura: a
    Ficha grava o resultado (a linha mantém a origem de quem a criou) e o código sai do lote."""
    aceita, recusada, sem_cru = _VIRADA
    resp, lidos, cortados, banco = _run(_virada_ponta_a_ponta(
        *_virada_cenario(monkeypatch, "VAVADA"), antes=(aceita, "")))
    assert resp["na_planilha"] == 1
    assert (lidos, cortados) == (sorted([recusada, sem_cru]), 1)
    assert banco[aceita] == ("extracao", "W") and len(banco) == 3


def test_virada_d10_liquidada_nao_e_reescrita(monkeypatch):
    """D10 (Feca, 12/10): "não mexer no passado é não ir futricar as apostas de mês passado".
    A LIQUIDADA no banco fica como está (aqui L, que a Ficha diria W), e a IA não a lê."""
    aceita, recusada, sem_cru = _VIRADA
    resp, lidos, cortados, banco = _run(_virada_ponta_a_ponta(
        *_virada_cenario(monkeypatch, "VAVADA"), antes=(aceita, "L")))
    assert resp["na_planilha"] == 0
    assert (lidos, cortados) == (sorted([recusada, sem_cru]), 1)
    assert banco[aceita] == ("extracao", "L")


async def _virada_segunda_captura(sess, texto, envelhecer=True):
    """2ª captura da mesma casa SEM cru novo (a extensão recarregada sem F5 na aba da casa:
    o texto chega, o cru não). `envelhecer` = o cru guardado é de uma captura anterior."""
    import main
    await asyncio.sleep(0.1)          # o `bloco_visto` da 1ª vai por `_fire`
    pool = await get_pool()
    if envelhecer:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE captura_crua SET recebido_em = recebido_em - "
                               "interval '1 hour'")
    para_ia, _ = await main._dedup_superbet_text(texto, sess.dono, sess.casa, sess.parceiro)
    await asyncio.sleep(0.1)
    async with pool.acquire() as conn:
        log = await conn.fetchrow("SELECT pela_ficha, para_ia, sem_cru_novo FROM virada_log "
                                  "ORDER BY id DESC LIMIT 1")
    return repository.codigos_do_texto(para_ia), dict(log)


def test_virada_n3_texto_mudou_sem_cru_novo_vai_para_a_ia(monkeypatch):
    """Furo N3 (parecer 012): aposta aberta com Ficha; o texto chega RESOLVIDO e nenhum cru
    novo chega. O cru guardado (aberto) não pode esconder a liquidação: a IA lê o bloco."""
    aceita, recusada, sem_cru = _VIRADA
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA", aberta=True)
    _run(_virada_ponta_a_ponta(sess, payload, texto))
    mudou = texto.replace(f"[Código: {aceita}]\nStake: 10\nStatus: Perdido",
                          f"[Código: {aceita}]\nStake: 10\nStatus: Ganho")
    assert mudou != texto
    lidos, log = _run(_virada_segunda_captura(sess, mudou))
    assert aceita in lidos
    assert log == {"pela_ficha": 0, "para_ia": 1, "sem_cru_novo": 1}


def test_virada_n3_texto_igual_sem_cru_novo_fica_com_a_ficha(monkeypatch):
    """A outra metade da regra: bloco igual ao da última leitura, cru antigo → a Ficha segura
    o código (é a barreira de hoje). Prova também que a Ficha grava o `bloco_visto` do que
    resolveu: sem ele, toda captura seguinte mandaria a aberta de volta à IA."""
    aceita, recusada, sem_cru = _VIRADA
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA", aberta=True)
    _run(_virada_ponta_a_ponta(sess, payload, texto))
    lidos, log = _run(_virada_segunda_captura(sess, texto))
    assert aceita not in lidos
    assert log["sem_cru_novo"] == 0


from pathlib import Path  # noqa: E402

_SIMPLES = "CfqYSukd8DqCGMcrVfm4x"     # Shuffle real: simples, BADMINTON, `Handicap pontos`


async def _simples_no_banco(conn, sess, pela_ficha=False):
    """Põe o cru simples real em `captura_crua` e a aposta em `bilhetes`: pela IA (Badminton,
    Handicap) ou, com `pela_ficha`, pela virada (`aplicar`, com os termos no dicionário)."""
    import json as _json

    import ficha
    import main
    import virada
    crus = _json.loads((Path(__file__).resolve().parent / "ficha_crus_familias.json")
                       .read_text(encoding="utf-8"))
    await conn.execute("INSERT INTO captura_crua (dono, casa, parceiro, familia, codigo, hash, cru) "
                       "VALUES ($1, 'VAVADA', $2, 'shf', $3, 'h', $4::jsonb)", sess.dono,
                       sess.parceiro, _SIMPLES, _json.dumps(crus[_SIMPLES]))
    if pela_ficha:
        for t, k, v in (("esporte", "badminton", "Badminton"),
                        ("categoria", "handicap pontos", "Handicap"),
                        ("descricao", "badminton | handicap pontos", "{ent} {hc} Pontos")):
            await conn.execute("INSERT INTO dicionario_termos (casa, tipo, termo_casa, "
                               "termo_sharpen) VALUES ('VAVADA', $1, $2, $3) "
                               "ON CONFLICT DO NOTHING", t, k, v)
        f = ficha.montar_ficha("shf", crus[_SIMPLES], "VAVADA")
        feitos, fica = await virada.aplicar(conn, sess.dono, "VAVADA", sess.casa, sess.parceiro,
                                            {_SIMPLES: f})
        assert feitos == {_SIMPLES}, fica
    else:
        await main.gravar_tsv(main.SalvarRequest(
            tsv=f"10/10/2026\tBadminton\t\t{sess.casa}\t{sess.parceiro}\tHandicap\t"
                f"A +2.5 [A v B]\t10\t2\tL\t{_SIMPLES}", casa=sess.casa,
            parceiro=sess.parceiro), sess.dono, sess.dono)


def test_semente_ignora_aposta_editada_a_mao_e_grava_o_log(monkeypatch):
    """R27: com 1 voto, uma edição manual viraria regra para todos os usuários da casa. A
    aposta com `correcoes` em `esporte`/`aposta` não vota; cada rodada vai ao `semente_log`."""
    import dicionario
    sess, payload, texto = _virada_cenario(monkeypatch, "", sombra="VAVADA")
    _run(_virada_ponta_a_ponta(sess, payload, texto))
    termo = "badminton"

    async def rodar():
        pool = await get_pool()
        async with pool.acquire() as conn:
            await _simples_no_banco(conn, sess)
            # o texto do SharpenUp também vota no esporte (`sombra_rotulos`): a edição à mão
            # tira os DOIS votos, senão o texto reporia o termo sozinho
            await conn.execute(
                "INSERT INTO sombra_rotulos (dono, casa, codigo, bruto, ia_esporte, ia_aposta) "
                "VALUES ($1, 'Vavada', $2, $3, 'Badminton', 'Handicap')", sess.dono, _SIMPLES,
                "Tipo: Simples\nSeleções:\n- X\n    Jogo: A vs B · Esporte: badminton · Início: x\n")
            await conn.execute("TRUNCATE semente_log")
            r1 = await dicionario.semear(conn, "teste")
            d1 = await conn.fetchval("SELECT termo_sharpen FROM dicionario_termos WHERE "
                                     "casa = 'VAVADA' AND tipo = 'esporte' AND termo_casa = $1", termo)
            bid = await conn.fetchval("SELECT id FROM bilhetes WHERE codigo_bilhete = $1", _SIMPLES)
            await conn.execute("INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, "
                               "valor_novo) VALUES ($1, 'TDonoV', 'Vavada', 'esporte', 'Futebol', "
                               "'Futebol')", bid)
            r2 = await dicionario.semear(conn, "teste")
            d2 = await conn.fetchval("SELECT termo_sharpen FROM dicionario_termos WHERE "
                                     "casa = 'VAVADA' AND tipo = 'esporte' AND termo_casa = $1", termo)
            await conn.execute("TRUNCATE captura_crua")
            log = [dict(r) for r in await conn.fetch(
                "SELECT gatilho, termos, novos, fontes FROM semente_log ORDER BY id")]
            await conn.execute("TRUNCATE correcoes")
            return r1, d1, r2, d2, log
    r1, d1, r2, d2, log = _run(rodar())
    assert d1 == "Badminton" and d2 is None
    assert r2["fontes"].get("editada à mão") == 1
    assert [l["gatilho"] for l in log] == ["teste", "teste"]
    import json as _json
    assert {"casa": "VAVADA", "tipo": "esporte", "termo": termo, "para": "Badminton"} \
        in _json.loads(log[0]["novos"])


def test_semente_roda_logo_depois_da_ia_quando_o_termo_era_novo(monkeypatch):
    """s412: `/extrair` de casa virada que mandou termo fora do dicionário à IA → a semente
    roda logo depois de a decisão da IA ser gravada (`_sombra_e_semente`), não só às 04h."""
    import main
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA", termos=False)
    _run(_virada_ponta_a_ponta(sess, payload, texto))
    tsv = "\n".join(f"10/10/2026\tFutebol\t\t{sess.casa}\t{sess.parceiro}\tML\t"
                    f"Time A [A vs B]\t10\t2\tL\t{c}" for c in _VIRADA)

    async def rodar():
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE semente_log")
        await main._sombra_e_semente(sess.dono, sess.casa, texto, tsv)
        await main._sombra_e_semente(sess.dono, sess.casa, texto, tsv)   # só a 1ª semeia
        async with pool.acquire() as conn:
            g = [r["gatilho"] for r in await conn.fetch("SELECT gatilho FROM semente_log")]
            n = await conn.fetchval("SELECT count(*) FROM sombra_rotulos")
        return g, n
    g, n = _run(rodar())
    assert g == ["extrair"] and n > 0


def test_corrigir_termo_regrava_so_a_ficha_do_mes_corrente(monkeypatch):
    """D24: a correção do Feca (`origem='feca'`) regrava as apostas da Ficha do MÊS CORRENTE
    que usaram o termo. Mês passado (D10/D23) e campo editado à mão ficam como estão."""
    from datetime import datetime

    import dicionario
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA")
    _run(_virada_ponta_a_ponta(sess, payload, texto))
    termo, cod = "handicap pontos", _SIMPLES

    async def rodar():
        pool = await get_pool()
        async with pool.acquire() as conn:
            await _simples_no_banco(conn, sess, pela_ficha=True)
            data = await conn.fetchval("SELECT data FROM bilhetes WHERE codigo_bilhete = $1", cod)
            d, m, a = (data.split("/") if "/" in data else data[:10].split("-")[::-1])
            mes = datetime(int(a), int(m), 15)
            fora = datetime(int(a) + 1, int(m), 15)
            ensaio = await dicionario.corrigir_termo(conn, "VAVADA", "categoria", termo, "Pontos",
                                                     hoje=mes)
            nada = await dicionario.corrigir_termo(conn, "VAVADA", "categoria", termo, "Pontos",
                                                   aplicar=True, hoje=fora)
            esp_fora = await conn.fetchval("SELECT aposta FROM bilhetes WHERE codigo_bilhete = $1",
                                           cod)
            feito = await dicionario.corrigir_termo(conn, "VAVADA", "categoria", termo, "Pontos",
                                                    aplicar=True, hoje=mes)
            linha = await conn.fetchrow("SELECT aposta, origem FROM bilhetes WHERE "
                                        "codigo_bilhete = $1", cod)
            dic = await conn.fetchrow("SELECT termo_sharpen, origem FROM dicionario_termos WHERE "
                                      "casa = 'VAVADA' AND tipo = 'categoria' AND termo_casa = $1", termo)
            # campo editado à mão não é tocado
            bid = await conn.fetchval("SELECT id FROM bilhetes WHERE codigo_bilhete = $1", cod)
            await conn.execute("INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, "
                               "valor_novo) VALUES ($1, 'TDonoV', 'Vavada', 'aposta', 'x', 'y')", bid)
            editada = await dicionario.corrigir_termo(conn, "VAVADA", "categoria", termo, "Gols",
                                                      aplicar=True, hoje=mes)
            await conn.execute("TRUNCATE correcoes")
            outra = await conn.fetchval("SELECT count(*) FROM bilhetes WHERE codigo_bilhete "
                                        "<> $1 AND aposta = 'Pontos'", cod)
        return ensaio, nada, esp_fora, feito, dict(linha), dict(dic), editada, outra
    ensaio, nada, esp_fora, feito, linha, dic, editada, outra = _run(rodar())
    assert [m["depois"]["aposta"] for m in ensaio] == ["Pontos"]
    assert nada == [] and esp_fora == "Handicap"
    assert [m["depois"] for m in feito] == [{"aposta": "Pontos"}]
    assert linha == {"aposta": "Pontos", "origem": "ficha"}
    assert dic == {"termo_sharpen": "Pontos", "origem": "feca"}
    assert editada == [] and outra == 0
    with pytest.raises(ValueError):
        _run(_corrigir_fora_do_master())


def test_virada_descricao_nova_vai_a_ia_uma_vez_e_depois_nao(monkeypatch):
    """s413 (Feca: chamada extra à IA só para a descrição, nunca). Mercado sem par de descrição:
    a aposta vai para a IA com o motivo próprio (`descricao_fora`); a IA escreve a descrição; a
    semente roda logo depois e aprende o mercado com 1 voto (D24); a aposta seguinte do MESMO
    mercado, com outra linha e outro lado, fica com a Ficha e não vai à IA."""
    import json as _json

    import ficha
    import main
    aceita, recusada, sem_cru = _VIRADA
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA", aberta=True)
    sess.termos = [t for t in sess.termos if t[2] != "sporttypeid 1 | total cantos"]

    async def rodar():
        pool = await get_pool()
        resp, lidos, _, _ = await _virada_ponta_a_ponta(sess, payload, texto)
        async with pool.acquire() as conn:
            log1 = dict(await conn.fetchrow("SELECT pela_ficha, descricao_fora FROM virada_log"))
            # os termos de esporte/categoria do teste são do Feca: a semente só refaz a dela
            await conn.execute("UPDATE dicionario_termos SET origem = 'feca'")
            await conn.execute("TRUNCATE semente_log")
            await conn.execute("UPDATE bilhetes SET descricao = $1 WHERE codigo_bilhete = $2",
                               _IA_ACEITA, aceita)
        tsv = f"10/10/2026\tMúltiplos\t\t{sess.casa}\t{sess.parceiro}\tMúltipla\t{_IA_ACEITA}" \
              f"\t25\t7,6\t\t{aceita}"
        await main._sombra_e_semente(sess.dono, sess.casa, texto, tsv)
        async with pool.acquire() as conn:
            aprendeu = await conn.fetchval(
                "SELECT termo_sharpen FROM dicionario_termos WHERE casa = 'VAVADA' AND "
                "tipo = 'descricao' AND termo_casa = 'sporttypeid 1 | total cantos'")
            gat = [r["gatilho"] for r in await conn.fetch("SELECT gatilho FROM semente_log")]
        # a aposta seguinte do mesmo mercado: outro código, outra linha, outro lado
        crus = _json.loads((Path(__file__).resolve().parent / "ficha_crus_familias.json")
                           .read_text(encoding="utf-8"))
        novo = _json.loads(_json.dumps(crus[aceita]))
        novo.update(id=5508528299, status=0)
        novo["selections"][0]["name"] = "Menos de 9.5"
        await ficha.receber(dict(payload, itens=[{"codigo": "5508528299", "cru": novo}]))
        texto2 = "[Código: 5508528299]\nStake: 10\nStatus: Aberto\n"
        para_ia, _ = await main._dedup_superbet_text(texto2, sess.dono, sess.casa, sess.parceiro)
        await asyncio.sleep(0.1)
        async with pool.acquire() as conn:
            linha = dict(await conn.fetchrow(
                "SELECT origem, descricao FROM bilhetes WHERE codigo_bilhete = '5508528299'"))
            log2 = dict(await conn.fetchrow("SELECT pela_ficha, para_ia, descricao_fora FROM "
                                            "virada_log ORDER BY id DESC LIMIT 1"))
        return lidos, log1, aprendeu, gat, repository.codigos_do_texto(para_ia), linha, log2
    lidos, log1, aprendeu, gat, lidos2, linha, log2 = _run(rodar())
    assert aceita in lidos and log1 == {"pela_ficha": 0, "descricao_fora": 1}
    assert aprendeu == "{ou} Escanteios" and gat == ["extrair"]
    assert lidos2 == [] and log2 == {"pela_ficha": 1, "para_ia": 0, "descricao_fora": 0}
    assert linha == {"origem": "ficha", "descricao": "Under 9.5 Escanteios [Vicenza v Pisa] // "
                                                     "Haro Rioja (F) +1.5 Sets [Haro Rioja (F) v Haris (F)]"}


def test_semente_regrava_a_descricao_da_ficha_do_mes_corrente(monkeypatch):
    """s413, item 5: quando o mercado é aprendido (ou muda), a semente regrava a descrição das
    linhas da Ficha DESTE mês. Mês passado não é tocado (D10, D23), nem a linha editada à mão."""
    from datetime import datetime

    import dicionario
    sess, payload, texto = _virada_cenario(monkeypatch, "VAVADA")
    _run(_virada_ponta_a_ponta(sess, payload, texto))
    cod = _SIMPLES

    async def rodar():
        pool = await get_pool()
        async with pool.acquire() as conn:
            await _simples_no_banco(conn, sess, pela_ficha=True)
            antes = await conn.fetchval("SELECT descricao FROM bilhetes WHERE codigo_bilhete = $1", cod)
            data = await conn.fetchval("SELECT data FROM bilhetes WHERE codigo_bilhete = $1", cod)
            d, m, a = (data.split("/") if "/" in data else data[:10].split("-")[::-1])
            mes, fora = datetime(int(a), int(m), 15), datetime(int(a) + 1, int(m), 15)
            # o mercado passa a ter outro valor no dicionário (a correção do Feca, D24); os
            # termos do teste viram `feca` para a semente não os apagar ao refazer a dela
            await conn.execute("UPDATE dicionario_termos SET origem = 'feca'")
            await conn.execute("UPDATE dicionario_termos SET termo_sharpen = '{ent} {hc} Pontos HC' "
                               "WHERE tipo = 'descricao' AND termo_casa = 'badminton | handicap pontos'")
            await conn.execute("TRUNCATE semente_log")
            nada = await dicionario.semear(conn, "teste", hoje=fora)
            feito = await dicionario.regravar_mes(conn, hoje=mes, campos=("descricao",))
            r = await dicionario.semear(conn, "teste", hoje=mes)          # a semente regrava
            log = [x["regravadas"] for x in await conn.fetch(
                "SELECT regravadas FROM semente_log ORDER BY id")]
            depois = await conn.fetchval("SELECT descricao FROM bilhetes WHERE codigo_bilhete = $1", cod)
            bid = await conn.fetchval("SELECT id FROM bilhetes WHERE codigo_bilhete = $1", cod)
            await conn.execute("INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, "
                               "valor_novo) VALUES ($1, 'TDonoV', 'Vavada', 'descricao', 'x', 'y')", bid)
            await conn.execute("UPDATE dicionario_termos SET termo_sharpen = '{ent} {hc} Pontos' "
                               "WHERE tipo = 'descricao' AND termo_casa = 'badminton | handicap pontos'")
            editada = await dicionario.regravar_mes(conn, aplicar=True, hoje=mes,
                                                    campos=("descricao",))
            await conn.execute("TRUNCATE correcoes")
        return antes, (nada, r, log), feito, depois, editada
    antes, (nada, r, log), feito, depois, editada = _run(rodar())
    assert antes == "Golubeva, Mariia +12.5 Pontos [Golubeva, Mariia v Ryberg, Anna Siess]"
    assert nada["regravadas"] == 0 and r["regravadas"] == 1 and log == [0, 1]
    assert [m["depois"] for m in feito] == [{"descricao": antes.replace("Pontos", "Pontos HC")}]
    assert depois == antes.replace("Pontos", "Pontos HC") and editada == []


async def _corrigir_fora_do_master():
    import dicionario
    pool = await get_pool()
    async with pool.acquire() as conn:
        await dicionario.corrigir_termo(conn, "VAVADA", "categoria", "x", "Especiais")


@pytest.mark.parametrize("sombra", ["VAVADA", ""])
def test_virada_desligada_e_o_caminho_de_hoje(monkeypatch, sombra):
    """Chave vazia, com a sombra ligada (o estado de produção em 12/10) ou não: a Ficha só
    vai à `ficha_sombra`, nada vai à planilha por ela, e a IA lê os três bilhetes."""
    resp, lidos, cortados, banco = _run(_virada_ponta_a_ponta(
        *_virada_cenario(monkeypatch, "", sombra)))
    assert resp["fichas"]["aceitas"] == (1 if sombra else 0) and resp["na_planilha"] == 0
    assert (lidos, cortados) == (sorted(_VIRADA), 0)
    assert {o for o, _ in banco.values()} == {"extracao"} and len(banco) == 3
