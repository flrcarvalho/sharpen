"""Contrato de 4 campos x o MESMO /salvar — contra um Postgres REAL (s386).

A linha do contrato não tem caminho de gravação próprio: ela entra pelo `main.salvar`
(`parse_tsv` → `validar_linhas` → `upsert_bilhetes`). Este teste prova o que isso quer
dizer para as correções que já existem no banco, comparando DOIS mundos que só diferem
na linha que chega na recaptura:

    controle:  salvar(linha de hoje) → corrigir à mão → salvar(linha de hoje)
    contrato:  salvar(linha de hoje) → corrigir à mão → salvar(linha do CONTRATO)

Os dois bancos têm de terminar IGUAIS. É isso que "preserva as alterações aplicáveis"
significa: o contrato não muda nenhuma regra do UPSERT — nem as boas (classificação
congelada em linha resolvida), nem a conhecida (`resultado` não é congelado; CLAUDE.md,
"Correção humana MANDA sobre a captura").

Mantém o MASTER vigente para leitura NOVA: banco vazio + linha do contrato de uma
múltipla grava `Múltiplos`, mesmo que alguém tenha corrigido um bilhete parecido para o
esporte único (7 de 7 correções de esporte na amostra da s386 foram nesse sentido — é
decisão do Feca em aberto, não deste módulo).

Só roda com `TEST_DATABASE_URL` (Postgres de TESTE local). Sem ela, é PULADO.
"""
import asyncio
import json
import os
import pathlib

import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DB,
    reason="sem TEST_DATABASE_URL — harness de DB só roda com Postgres de teste",
)

if TEST_DB and not ("localhost" in TEST_DB or "127.0.0.1" in TEST_DB):
    raise RuntimeError("TEST_DATABASE_URL deve ser um Postgres de teste local — recusando.")

if TEST_DB:
    os.environ["DATABASE_URL"] = TEST_DB
    import database  # noqa: E402
    import repository  # noqa: E402
    import contrato_texto as ct  # noqa: E402
    import main  # noqa: E402
    from database import get_pool, init_db  # noqa: E402
    _LOOP = asyncio.new_event_loop()

_G = json.loads((pathlib.Path(__file__).resolve().parents[1] / "golden_set"
                 / "contrato_bet365.json").read_text(encoding="utf-8"))
CASA, PARCEIRO, DONO = "Bet365", "Conta Teste", "TDonoContrato"
CAMPOS = ("data", "esporte", "aposta", "descricao", "stake", "odd", "resultado",
          "extraction_state", "tipster")


def _run(coro):
    return _LOOP.run_until_complete(coro)


@pytest.fixture(scope="module", autouse=True)
def _fecha_pool_e_loop():
    yield
    if getattr(database, "_pool", None) is not None:
        _run(database._pool.close())
        database._pool = None
    _LOOP.close()


async def _reset():
    await init_db()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE bilhetes, correcoes RESTART IDENTITY CASCADE")


async def _estado():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT codigo_bilhete, %s FROM bilhetes WHERE dono=$1 ORDER BY codigo_bilhete"
            % ", ".join(CAMPOS), DONO)
    return [dict(r) for r in rows]


async def _salvar(tsv):
    req = main.SalvarRequest(tsv=tsv, casa=CASA, parceiro=PARCEIRO)
    return await main.salvar(req, dono=DONO, dono_view=DONO)


def _linha_hoje(it):
    """A linha que o caminho de hoje gravou: rótulos da IA de produção, números do banco."""
    b, ia = it["banco"], it["ia"]
    return "\t".join([b["data"], ia["esporte"], "", CASA, PARCEIRO, ia["aposta"],
                      ia["descricao"], b["stake"], b["odd"], b["resultado"], it["codigo"]])


def _linha_contrato(it):
    p = ct.particionar(f"[Código: {it['codigo']}]\n{it['bruto']}")
    resp = "```tsv\n%s\t%s\t%s\t%s\n```" % (it["codigo"], it["ia"]["esporte"],
                                             it["ia"]["aposta"], it["ia"]["descricao"])
    mt = ct.montar(p, resp, CASA, PARCEIRO)
    assert it["codigo"] in mt.linhas, mt.rejeitados
    return mt.linhas[it["codigo"]]


def _itens_resolvidos():
    return [i for i in _G["itens"]
            if not i["tipo"].startswith(("antes:", "depois:")) and i["banco"].get("resultado")]


async def _mundo(it, correcao, recaptura):
    await _reset()
    r = await _salvar(_linha_hoje(it))
    assert r["inseridos"] == 1, r
    await repository.atualizar_bilhete(r["ids"][0], correcao, DONO)
    await _salvar(recaptura)
    return await _estado()


@pytest.mark.parametrize("campo,valor", [
    ("aposta", "Outros"), ("descricao", "Corrigida à mão"), ("esporte", "MMA"),
    ("odd", "3,33"), ("stake", "12,34"), ("resultado", "V"),
])
def test_recaptura_pelo_contrato_termina_igual_a_recaptura_de_hoje(campo, valor):
    for it in _itens_resolvidos()[:6]:
        async def body():
            controle = await _mundo(it, {campo: valor}, _linha_hoje(it))
            contrato = await _mundo(it, {campo: valor}, _linha_contrato(it))
            assert contrato == controle, (it["codigo"], campo)
            assert len(contrato) == 1, "nunca duplica"
        _run(body())


def test_classificacao_corrigida_a_mao_sobrevive_a_linha_do_contrato():
    """O caso real da amostra: múltipla de lutas corrigida de `Múltiplos` para `MMA`."""
    it = next(i for i in _G["itens"] if i["codigo"] == "AA8674581941I")

    async def body():
        estado = await _mundo(it, {"esporte": "MMA", "aposta": "Múltipla"}, _linha_contrato(it))
        assert estado[0]["esporte"] == "MMA", "a linha resolvida congela a classificação"
    _run(body())


def test_leitura_nova_segue_o_master_vigente():
    """Banco vazio: a múltipla lida pelo contrato grava `Múltiplos` (MASTER_ESPORTES §2)."""
    it = next(i for i in _G["itens"] if i["codigo"] == "AA8674581941I")

    async def body():
        await _reset()
        r = await _salvar(_linha_contrato(it))
        assert r["inseridos"] == 1 and not r["rejeitados"]
        assert (await _estado())[0]["esporte"] == "Múltiplos"
    _run(body())


def test_custo_do_contrato_fica_separavel_e_o_de_hoje_continua_null():
    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            # a migração tem de CRIAR as colunas: derruba e deixa o `init_db` refazer.
            # Sem isto, um banco de teste que já as tem esconde um ALTER apagado.
            await conn.execute("ALTER TABLE uso_tokens DROP COLUMN IF EXISTS caminho")
            await conn.execute("ALTER TABLE sombra_modelo DROP COLUMN IF EXISTS contrato")
        await init_db()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE uso_tokens, sombra_modelo")
        tk = {"input": 1, "output": 2, "cache_read": 3, "cache_write": 4}
        await repository.registrar_uso(DONO, CASA, "claude-sonnet-5", 1, 1, tk)
        await repository.registrar_uso(DONO, CASA, "claude-sonnet-5", 2, 6, tk, caminho="contrato4")
        await repository.registrar_uso(DONO, CASA, "claude-sonnet-5", 1, 1, tk,
                                       caminho="atual_pos_contrato")
        placar = {"blocos": 6, "linhas": 6}
        await repository.registrar_sombra_modelo(DONO, CASA, "claude-haiku-4-5", "claude-sonnet-5",
                                                 1, False, tk, placar)
        await repository.registrar_sombra_modelo(DONO, CASA, "claude-haiku-4-5", "claude-sonnet-5",
                                                 1, False, tk, placar, contrato="contrato4")
        async with pool.acquire() as conn:
            uso = [r["caminho"] for r in await conn.fetch(
                "SELECT caminho FROM uso_tokens ORDER BY id")]
            som = [r["contrato"] for r in await conn.fetch(
                "SELECT contrato FROM sombra_modelo ORDER BY id")]
            custos = await conn.fetch("SELECT custo_usd FROM uso_tokens")
        assert uso == [None, "contrato4", "atual_pos_contrato"]
        assert som == [None, "contrato4"]
        assert all(c["custo_usd"] > 0 for c in custos)
    _run(body())


# ── Barreira de recaptura x falha da outra metade (s386) ───────────────────────
#
# O caso: bilhete JÁ no banco como aberto; a captura traz o bloco LIQUIDADO (hash novo).
# 1ª tentativa: o contrato aceita o bloco, mas o caminho de hoje (a outra metade do lote)
# falha → nada é entregue nem salvo. 2ª tentativa: a liquidação TEM de ser processada.
# Se a barreira tivesse gravado o hash do bloco liquidado na 1ª, o pré-dedup o pularia
# na 2ª (o bilhete existe, então o JOIN do `blocos_conhecidos` casa) e ele ficaria
# aberto para sempre, sem erro nenhum.
#
# Roda o pré-dedup REAL (`_dedup_superbet_text`, é ele que aplica a barreira) e o
# `_stream_contrato` REAL no MESMO loop do pool. Via TestClient o pool ficaria preso a
# outro loop, a consulta da barreira falharia, devolveria `{}` — e o teste passaria
# por engano.

_ABERTO = "Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)"


class _Fin:
    def __init__(self, t):
        import types
        self.stop_reason = "end_turn"
        self.usage = types.SimpleNamespace(input_tokens=1, output_tokens=1,
                                           cache_read_input_tokens=0, cache_creation_input_tokens=0)
        self.content = [types.SimpleNamespace(type="text", text=t)]


class _Stream:
    def __init__(self, t):
        self._t = t

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    @property
    async def text_stream(self):
        yield self._t

    async def get_final_message(self):
        return _Fin(self._t)


class _IA:
    def __init__(self, respostas):
        self.respostas, self.messages = respostas, self

    def stream(self, model, max_tokens, system, messages, **kw):
        import re as _re
        cods = _re.findall(r"(?m)^\[Código:\s*([^\]\r\n]*?)\s*\]", messages[0]["content"][0]["text"])
        return _Stream("```tsv\n" + "\n".join(self.respostas[c] for c in cods) + "\n```")


def _hoje_que(falha: bool):
    """O caminho de hoje (falso): falha na 1ª tentativa, entrega na 2ª."""
    def ger(texto, caminho):
        async def _g():
            import re as _re
            if falha:
                yield 'data: {"error": "caminho de hoje caiu"}\n\n'
                return
            cods = _re.findall(r"(?m)^\[Código:\s*([^\]\r\n]*?)\s*\]", texto)
            linhas = [f"01/09/2026\tFutebol\t\t{CASA}\t{PARCEIRO}\tML\thoje {c}\t10,00\t2\tL\t{c}"
                      for c in reversed(cods)]
            yield "data: " + json.dumps({"done": True, "tokens": {}, "resultado":
                                         "```tsv\n" + main._TSV_HEADER + "\n" + "\n".join(linhas)
                                         + "\n```"}) + "\n\n"
        return _g()
    return ger


async def _tentativa(texto, falha):
    texto2, _skip = await main._dedup_superbet_text(texto, DONO, CASA, PARCEIRO)
    eventos = []
    if texto2:
        async for ev in main._stream_contrato(texto2, "BET365", CASA, PARCEIRO, "claude-sonnet-5",
                                              DONO, 0, 0, _hoje_que(falha)):
            eventos.append(json.loads(ev[6:]))
    # os `_fire` (barreira, sombra, uso) terminam antes de olhar o banco
    while main._bg_tasks:
        await asyncio.gather(*list(main._bg_tasks), return_exceptions=True)
    return texto2, eventos


async def _hash_visto(cod):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT bloco_hash FROM bloco_visto WHERE dono=$1 AND codigo=$2", DONO, cod)


def test_falha_da_outra_metade_nao_marca_a_liquidacao_como_lida(monkeypatch):
    liq = next(i for i in _itens_resolvidos() if i["tipo"] == "simples W")
    antigo = next(i for i in _G["itens"] if i["tipo"] == "antes: Data (encerramento)")
    aberto = liq["bruto"].replace(next(l for l in liq["bruto"].splitlines()
                                       if l.startswith("Status:")), _ABERTO)
    assert aberto != liq["bruto"]
    monkeypatch.setattr(main, "_client", _IA({liq["codigo"]: "%s\t%s\t%s\t%s" % (
        liq["codigo"], liq["ia"]["esporte"], liq["ia"]["aposta"], liq["ia"]["descricao"])}))
    monkeypatch.setattr(main, "_sombra_vale_agora", lambda: False)
    texto = (f"[Código: {liq['codigo']}]\n{liq['bruto']}\n\n"
             f"[Código: {antigo['codigo']}]\n{antigo['bruto']}")

    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE bloco_visto")
        # ANTES: o bilhete existe ABERTO, e a barreira conhece o bloco aberto
        r = await _salvar(_linha_contrato(dict(liq, bruto=aberto)))
        assert r["inseridos"] == 1
        await repository.registrar_blocos_vistos(DONO, CASA, f"[Código: {liq['codigo']}]\n{aberto}")
        h_aberto = await _hash_visto(liq["codigo"])
        assert (await _estado())[0]["extraction_state"] == "aberta"

        # 1ª tentativa: o contrato aceita, a outra metade cai → erro, nada entregue
        t1, ev1 = await _tentativa(texto, falha=True)
        assert liq["codigo"] in t1, "a liquidação chegou ao contrato"
        assert ev1 and ev1[-1].get("error") and not any(e.get("done") for e in ev1)
        assert await _hash_visto(liq["codigo"]) == h_aberto, \
            "a barreira NÃO pode ter gravado o bloco liquidado sem o lote ter sido entregue"

        # 2ª tentativa: o pré-dedup deixa passar, o lote é entregue e salvo
        t2, ev2 = await _tentativa(texto, falha=False)
        assert liq["codigo"] in t2, "a 2ª tentativa tem de PROCESSAR a liquidação"
        done = ev2[-1]
        assert done.get("done"), ev2[-1]
        await _salvar(done["resultado"].split("```tsv\n", 1)[1].split("\n```", 1)[0])
        est = {e["codigo_bilhete"]: e for e in await _estado()}
        assert est[liq["codigo"]]["resultado"] == "W"
        assert est[liq["codigo"]]["extraction_state"] == "resolvida"
        assert await _hash_visto(liq["codigo"]) != h_aberto, "agora sim, entregue: lembrado"
    _run(body())


@pytest.mark.xfail(strict=True, reason=(
    "LACUNA PRÉ-EXISTENTE do caminho de hoje (não é do contrato): a barreira é gravada no "
    "fim do /extrair e o /salvar é outra chamada. Bilhete que JÁ existe, cuja extração é "
    "entregue mas não salva (aba fechada, rede), tem a atualização pulada na próxima "
    "captura. Quando for corrigido, este teste passa e o strict o denuncia."))
def test_lacuna_preexistente_entregue_mas_nao_salvo_ainda_perde_a_atualizacao():
    liq = next(i for i in _itens_resolvidos() if i["tipo"] == "simples W")
    outro = next(i for i in _itens_resolvidos() if i["codigo"] != liq["codigo"])
    aberto = liq["bruto"].replace(next(l for l in liq["bruto"].splitlines()
                                       if l.startswith("Status:")), _ABERTO)
    texto = (f"[Código: {liq['codigo']}]\n{liq['bruto']}\n\n"
             f"[Código: {outro['codigo']}]\n{outro['bruto']}")

    async def body():
        await _reset()
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("TRUNCATE bloco_visto")
        await _salvar(_linha_contrato(dict(liq, bruto=aberto)))
        # a extração de hoje ENTREGOU (é no `done` que ela grava a barreira)...
        await main._barreira_lembrar(DONO, CASA, texto)
        # ...e o /salvar nunca aconteceu. A próxima captura:
        t2, _ = await main._dedup_superbet_text(texto, DONO, CASA, PARCEIRO)
        assert liq["codigo"] in t2, "a atualização deveria voltar a ser processada"
    _run(body())


def test_lote_inteiro_do_contrato_passa_no_salvar_sem_rejeicao():
    itens = _itens_resolvidos()

    async def body():
        await _reset()
        texto = "\n\n".join(f"[Código: {i['codigo']}]\n{i['bruto']}" for i in itens)
        p = ct.particionar(texto)
        resp = "```tsv\n" + "\n".join(
            f"{i['codigo']}\t{i['ia']['esporte']}\t{i['ia']['aposta']}\t{i['ia']['descricao']}"
            for i in itens) + "\n```"
        mt = ct.montar(p, resp, CASA, PARCEIRO)
        r = await _salvar(mt.tsv)
        assert not r["rejeitados"] and r["inseridos"] == len(mt.linhas)
        est = {e["codigo_bilhete"]: e for e in await _estado()}
        for cod, linha in mt.linhas.items():
            col = linha.split("\t")
            assert est[cod]["stake"] == col[7] and est[cod]["odd"] == col[8]
            assert (est[cod]["resultado"] or "") == col[9]
    _run(body())
