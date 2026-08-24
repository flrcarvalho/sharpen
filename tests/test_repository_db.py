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
