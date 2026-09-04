"""Gravação da Caixa Inteligente (s314) — o que vai para o banco, e em que TIPO.

Este arquivo nasceu de um defeito de produção que aconteceu DUAS vezes, com dois
argumentos diferentes do MESMO INSERT: o "Ativar" do Feca não fazia nada.

  1ª — `valor`/`projetado` são `NUMERIC`, e o asyncpg recusa `float` (exige `Decimal`).
  2ª — `data` é `DATE`, e ele recusa `str` (exige `datetime.date`).

Nas duas o 500 acontecia **dentro do driver**, antes de qualquer SQL rodar; a
matemática (`test_caixa.py`) estava certa o tempo todo. E na 1ª rodada este arquivo
até olhou o tipo de `valor` — mas afirmava a STRING como o certo para `data`, ou
seja, gravou o segundo defeito como se fosse a regra. Por isso agora existe **um
teste que percorre os 8 argumentos de uma vez**: gate por lista, não por lembrança.

Roda sem Postgres: o conftest stuba asyncpg/database e o pool aqui é de mentira —
mesmo molde de `test_excluir_parceiro.py`. O que este teste NÃO cobre: o SQL de
verdade (o índice único do `inicial`, a FK e o CASCADE), que só o CI com banco
exercita. Os tipos acima foram **medidos** contra o Postgres de produção numa
transação com ROLLBACK: `date`+`Decimal` passa, `str` em `data` levanta
`DataError: 'str' object has no attribute 'toordinal'`.
"""
import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import repository


class _FakeConn:
    def __init__(self, conta, bilhetes=None, movs=None):
        self.conta = conta
        self.bilhetes = bilhetes or []
        self.movs = movs or []
        self.inserts = []      # (sql, args) de cada INSERT
        self.execs = []

    def transaction(self):
        conn = self

        class _T:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _T()

    async def fetchrow(self, sql, *a):
        if "FROM parceiros" in sql:
            return self.conta
        return None

    async def fetch(self, sql, *a):
        if "FROM bilhetes" in sql:
            return self.bilhetes
        if "FROM caixa_mov" in sql:
            return self.movs
        return []

    async def execute(self, sql, *a):
        self.execs.append((sql, a))
        if sql.strip().upper().startswith("INSERT"):
            self.inserts.append((sql, a))
        return "INSERT 1"


class _FakePool:
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        conn = self.conn

        class _A:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _A()


CONTA = {"id": 7, "casa": "Superbet", "nome": "nicoleel01 [Richard]", "arquivado": False}


def _lancar(conn, **kw):
    args = dict(dono="Feca", parceiro_id=7, tipo="deposito",
                data="02/09/2026", valor=1950.0, obs="")
    args.update(kw)
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))), \
         patch.object(repository, "caixa_conta",
                      lambda *a, **k: asyncio.sleep(0, result={"ok": "stub"})):
        return asyncio.run(repository.caixa_lancar(**args))


def _mov(tipo, data, valor, **kw):
    return {"id": kw.get("id", 1), "tipo": tipo, "data": data, "valor": valor,
            "obs": "", "projetado": kw.get("projetado"), "abertas_corte": kw.get("abertas_corte"),
            "criado_em": "2026-09-01T10:00:00"}


# ── O tipo do argumento (o defeito que abriu este arquivo) ────────────────────

def test_valor_vai_como_decimal_nunca_float():
    """NUMERIC no asyncpg é Decimal. Float aqui = DataError = 500 = 'não acontece nada'."""
    conn = _FakeConn(CONTA)
    res = _lancar(conn)
    assert res["ok"] is True
    sql, args = conn.inserts[0]
    assert "INSERT INTO caixa_mov" in sql
    valor = args[4]
    assert isinstance(valor, Decimal), f"valor foi {type(valor).__name__}, não Decimal"
    assert valor == Decimal("1950.00")


def test_decimal_nasce_da_STRING_e_nao_do_float():
    """`Decimal(1950.1)` carrega o lixo binário do float; `Decimal("1950.10")` não.
    Como o valor já vem arredondado em 2 casas, a string é a conversão fiel."""
    conn = _FakeConn(CONTA)
    _lancar(conn, valor=1950.1)
    assert conn.inserts[0][1][4] == Decimal("1950.10")


def test_projetado_da_conferencia_tambem_e_decimal():
    conn = _FakeConn(CONTA, movs=[_mov("inicial", "2026-08-01", Decimal("1000"))])
    _lancar(conn, tipo="conferencia", valor=900.0)
    proj = conn.inserts[0][1][6]
    assert isinstance(proj, Decimal), f"projetado foi {type(proj).__name__}, não Decimal"
    assert proj == Decimal("1000.00")


def test_lancamento_comum_grava_projetado_nulo():
    conn = _FakeConn(CONTA)
    _lancar(conn)
    assert conn.inserts[0][1][6] is None
    assert conn.inserts[0][1][7] is None    # abertas_corte só existe no `inicial`


def test_cada_argumento_do_insert_vai_no_tipo_da_coluna():
    """O gate por LISTA. Duas vezes um argumento saiu no tipo errado e o driver
    derrubou a rota antes de qualquer SQL; olhar um argumento por vez foi o que
    deixou o segundo passar. Aqui a tabela inteira é conferida de uma vez.

    Ordem do INSERT: dono, parceiro_id, tipo, data, valor, obs, projetado, abertas_corte.
    """
    esperado = [
        ("dono", str), ("parceiro_id", int), ("tipo", str), ("data", date),
        ("valor", Decimal), ("obs", str),
        ("projetado", (Decimal, type(None))), ("abertas_corte", (list, type(None))),
    ]
    conn = _FakeConn(CONTA, movs=[_mov("inicial", "2026-08-01", Decimal("1000"))])
    _lancar(conn, tipo="conferencia", valor=900.0)          # preenche `projetado`
    conn2 = _FakeConn(CONTA, bilhetes=[
        {"id": 11, "data": "28/07/2026", "stake": "400,00", "odd": None, "resultado": ""}])
    _lancar(conn2, tipo="inicial", data="01/08/2026", valor=3000.0)   # preenche `abertas_corte`

    for args in (conn.inserts[0][1], conn2.inserts[0][1]):
        assert len(args) == len(esperado), "o INSERT mudou de forma — reveja esta lista"
        for valor_arg, (nome, tipo_ok) in zip(args, esperado):
            assert isinstance(valor_arg, tipo_ok), (
                f"{nome} foi {type(valor_arg).__name__}; a coluna exige "
                f"{getattr(tipo_ok, '__name__', tipo_ok)}")
    # bool é subclasse de int: parceiro_id nunca pode chegar como True/False
    assert not isinstance(conn.inserts[0][1][1], bool)


# ── Regras de gravação ────────────────────────────────────────────────────────

def test_data_br_vira_date():
    """dd/mm/aaaa (o que a tela manda) → `datetime.date` (o que a coluna exige)."""
    conn = _FakeConn(CONTA)
    _lancar(conn, data="02/09/2026")
    assert conn.inserts[0][1][3] == date(2026, 9, 2)


def test_inicial_apaga_o_anterior_antes_de_gravar():
    """Um saldo inicial por conta. Sem o DELETE, o índice único derrubaria a
    transação — e reconfigurar o corte é operação legítima."""
    conn = _FakeConn(CONTA)
    _lancar(conn, tipo="inicial", valor=3000.0)
    apagou = [s for s, _ in conn.execs if "DELETE FROM caixa_mov" in s]
    assert apagou, "gravou o inicial sem apagar o anterior"
    assert "tipo = 'inicial'" in apagou[0]


def test_inicial_guarda_as_apostas_ja_abertas_antes_do_corte():
    """O stake delas saiu ANTES do corte e volta inteiro ao liquidar. Sem esta lista
    a conta nasce com divergência permanente (ver test_caixa.py)."""
    conn = _FakeConn(CONTA, bilhetes=[
        {"id": 11, "data": "28/07/2026", "stake": "400,00", "odd": None, "resultado": ""},
        {"id": 12, "data": "10/08/2026", "stake": "100,00", "odd": None, "resultado": ""},
        {"id": 13, "data": "20/07/2026", "stake": "50,00", "odd": "2,00", "resultado": "W"},
        {"id": 14, "data": "25/07/2026", "stake": "0", "odd": None, "resultado": ""},
    ])
    _lancar(conn, tipo="inicial", data="01/08/2026", valor=3000.0)
    assert conn.inserts[0][1][7] == [11], "só a aposta ABERTA e ANTERIOR ao corte entra"


def test_conferencia_exige_saldo_inicial():
    conn = _FakeConn(CONTA, movs=[])
    res = _lancar(conn, tipo="conferencia", valor=900.0)
    assert res["ok"] is False and "saldo inicial" in res["motivo"]
    assert not conn.inserts


# ── Fronteira de entrada ──────────────────────────────────────────────────────

def test_conta_de_outro_dono_nao_grava_nada():
    conn = _FakeConn(None)
    res = _lancar(conn)
    assert res["ok"] is False and "não encontrada" in res["motivo"]
    assert not conn.inserts


def test_tipo_invalido_recusado():
    conn = _FakeConn(CONTA)
    assert _lancar(conn, tipo="pix")["ok"] is False
    assert not conn.inserts


def test_data_invalida_recusada():
    conn = _FakeConn(CONTA)
    assert _lancar(conn, data="ontem")["ok"] is False
    assert not conn.inserts


def test_deposito_negativo_ou_zero_recusado():
    """Sinal mora no TIPO. Depósito negativo seria o mesmo fato com duas grafias."""
    conn = _FakeConn(CONTA)
    assert _lancar(conn, valor=-10.0)["ok"] is False
    assert _lancar(conn, valor=0.0)["ok"] is False
    assert not conn.inserts


def test_ajuste_negativo_e_legitimo():
    conn = _FakeConn(CONTA)
    assert _lancar(conn, tipo="ajuste", valor=-120.0)["ok"] is True
    assert conn.inserts[0][1][4] == Decimal("-120.00")


def test_observacao_e_truncada_e_nao_vaza_espaco():
    conn = _FakeConn(CONTA)
    _lancar(conn, obs="  " + "x" * 400 + "  ")
    assert len(conn.inserts[0][1][5]) == 280


# ── Quais apostas já tinham tirado o stake da conta no corte ──────────────────
# A regra ingênua (só `data < corte`) está errada porque `data` é a data do EVENTO.
# Aposta feita ontem para um jogo da próxima semana tem data DEPOIS do corte, e o
# stake dela já saiu — descontá-lo de novo faz a conta nascer com divergência, no
# fluxo que a própria tela recomenda ("informe o saldo de hoje").
from datetime import datetime

from repository import _caixa_abertas_ids

HOJE = "2026-09-03"


def _ap(id_, data, criado, resultado="", stake="151,00"):
    return {"id": id_, "data": data, "stake": stake, "resultado": resultado,
            "criado_em": datetime.fromisoformat(criado)}


def test_corte_hoje_pega_TODA_aposta_aberta_inclusive_a_de_evento_futuro():
    """O saldo foi lido AGORA: se a aposta está aberta agora, o stake já saiu.
    Vale para evento de amanhã, da semana que vem ou de ontem — sem exceção."""
    ids = _caixa_abertas_ids([
        _ap(1, "10/09/2026", "2026-09-02T10:00:00"),   # evento na semana que vem
        _ap(2, "03/09/2026", "2026-09-03T09:00:00"),   # evento hoje
        _ap(3, "01/09/2026", "2026-09-01T09:00:00"),   # evento anterior, ainda aberta
    ], HOJE, HOJE)
    assert ids == [1, 2, 3]


def test_corte_hoje_ignora_liquidada_e_stake_zero():
    ids = _caixa_abertas_ids([
        _ap(1, "10/09/2026", "2026-09-02T10:00:00", resultado="W"),
        _ap(2, "10/09/2026", "2026-09-02T10:00:00", stake="0"),
        _ap(3, "10/09/2026", "2026-09-02T10:00:00"),
    ], HOJE, HOJE)
    assert ids == [3]


def test_corte_no_passado_usa_o_que_PROVADAMENTE_ja_existia():
    """Sem reconstruir o passado: entra o que tem evento anterior ao corte ou linha
    que o Sharpen já tinha antes dele. O resto fica de fora — é um piso, não o exato."""
    ids = _caixa_abertas_ids([
        _ap(1, "28/08/2026", "2026-09-03T10:00:00"),   # evento antes do corte → entra
        _ap(2, "10/09/2026", "2026-08-30T10:00:00"),   # Sharpen já tinha antes → entra
        _ap(3, "10/09/2026", "2026-09-02T10:00:00"),   # nasceu depois do corte → fica fora
    ], "2026-09-01", HOJE)
    assert ids == [1, 2]


def test_a_regra_ingenua_deixaria_a_aposta_futura_de_fora():
    """Contraprova do defeito: com corte = hoje, filtrar por `data < corte` devolveria
    lista VAZIA para uma conta que tem aposta futura aberta — e o stake dela seria
    descontado duas vezes."""
    abertas = [_ap(1, "10/09/2026", "2026-09-02T10:00:00")]
    ingenua = [a["id"] for a in abertas
               if (repository._data_iso(a["data"]) or "") < HOJE]   # a regra antiga
    assert ingenua == []
    assert _caixa_abertas_ids(abertas, HOJE, HOJE) == [1]


def test_backfill_nao_adota_aposta_nascida_DEPOIS_da_leitura_do_saldo():
    """O `ate` é o instante em que o saldo foi lido. Rodando o backfill mais tarde no
    mesmo dia, sem esse corte ele adotaria apostas feitas DEPOIS — cujo stake saiu
    depois da leitura — e inflaria a projeção. Medido em produção antes de existir:
    3 contas do Gabriel, +R$ 10.477 de saldo que não existia."""
    ativacao = datetime.fromisoformat("2026-09-03T10:00:00")
    abertas = [
        _ap(1, "10/09/2026", "2026-09-03T09:00:00"),   # existia na ativação → entra
        _ap(2, "10/09/2026", "2026-09-03T15:00:00"),   # nasceu depois → NÃO entra
    ]
    assert _caixa_abertas_ids(abertas, HOJE, HOJE, ate=ativacao) == [1]
    # sem o `ate` (o caminho da ativação, onde "agora" é o limite) as duas entram
    assert _caixa_abertas_ids(abertas, HOJE, HOJE) == [1, 2]
