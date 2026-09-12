"""Preço do fornecedor com DATA DE VIGÊNCIA (s348, Fatia 1).

O preço que um fornecedor cobra por conta **muda com o tempo** ("em agosto subiu o
preço, ou fiz um deal melhor" — Feca). Um campo único não sabe disso: registrar
R$ 950 a partir de agosto não pode reescrever o que as contas de janeiro custaram.

Duas coisas precisam de gate aqui, e elas falham de jeitos diferentes:

  1. **A RÉGUA** (`_preco_vigente_em`) — qual preço valia numa data. Errar aqui não
     dá erro nenhum: dá o número errado, com cara de número certo.
  2. **O TIPO do argumento** — `valor` é `NUMERIC` (asyncpg exige `Decimal`) e
     `vigente_desde` é `DATE` (exige `datetime.date`). Errar aqui levanta `DataError`
     DENTRO do driver, antes de qualquer SQL rodar, e vira 500 na rota. É o mesmo
     defeito que derrubou o "Ativar" da Caixa duas vezes (`test_caixa_lancar.py`).

E uma terceira, que é de ARQUITETURA: `custo_store.custo_conta` deixou de ser fonte
e virou VISTA. Toda escrita aqui tem de reespelhar o vigente de hoje lá, senão as
telas antigas (que seguem no ar até a Fatia 5) mostram um preço que já não existe.

Roda sem Postgres: o conftest stuba asyncpg/database e o pool aqui é de mentira —
mesmo molde de `test_caixa_lancar.py`. O que este arquivo **NÃO** cobre: o SQL de
verdade (o índice único de `(dono, fornecedor, casa, vigente_desde)` e o `ON
CONFLICT` que o usa), que só o CI com banco exercita.
"""
import asyncio
import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

import repository


# ── Pool de mentira ──────────────────────────────────────────────────────────

class _FakeConn:
    def __init__(self, precos=None, custo_conta=None):
        self.precos = precos or []          # linhas de fornecedor_preco
        self.custo_conta = custo_conta or {}
        self.inserts = []                   # (sql, args) de todo INSERT
        self.execs = []

    def transaction(self):
        conn = self

        class _T:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _T()

    async def fetch(self, sql, *a):
        if "FROM fornecedor_preco" in sql:
            return list(self.precos)
        return []

    async def fetchrow(self, sql, *a):
        if "INSERT INTO fornecedor_preco" in sql:
            self.inserts.append((sql, a))
            return {"id": 42}
        if "DELETE FROM fornecedor_preco" in sql:
            self.execs.append((sql, a))
            return self._alvo_delete
        if "custo_conta FROM custo_store" in sql:
            return {"custo_conta": json.dumps(self.custo_conta)}
        return None

    async def execute(self, sql, *a):
        self.execs.append((sql, a))
        if "INSERT INTO custo_store" in sql:
            self.inserts.append((sql, a))
            self.custo_conta = json.loads(a[1])
        return "OK"

    _alvo_delete = None


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


def _com_pool(conn, coro):
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))):
        return asyncio.run(coro())


def _linha(valor, desde):
    return {"valor": Decimal(str(valor)), "vigente_desde": date.fromisoformat(desde)}


# ── 1. A RÉGUA: qual preço valia quando ──────────────────────────────────────

def test_preco_vigente_e_o_ultimo_degrau_que_ja_comecou():
    """Dois degraus, e a data pedida cai depois do segundo: vale o segundo."""
    linhas = [_linha(850, "2026-01-01"), _linha(950, "2026-08-01")]
    assert repository._preco_vigente_em(linhas, date(2026, 9, 12)) == 950.0


def test_preco_vigente_ignora_degrau_que_ainda_nao_comecou():
    """A conta comprada em MARÇO custou o preço de março, não o de agosto. É o
    ponto inteiro de a tabela ter data: o preço novo não é retroativo."""
    linhas = [_linha(850, "2026-01-01"), _linha(950, "2026-08-01")]
    assert repository._preco_vigente_em(linhas, date(2026, 3, 15)) == 850.0


def test_preco_vigente_no_dia_exato_ja_vale():
    """`vigente_desde` é INCLUSIVO: comprou no dia 01/08, pagou o preço de 01/08."""
    linhas = [_linha(850, "2026-01-01"), _linha(950, "2026-08-01")]
    assert repository._preco_vigente_em(linhas, date(2026, 8, 1)) == 950.0


def test_preco_vigente_antes_do_primeiro_degrau_e_none():
    """Antes de existir preço não há preço — e `None` é diferente de zero. Zero
    seria uma conta de graça, que é exatamente o tipo de número inventado que o
    CLAUDE.md barra ('zero não é ausência')."""
    assert repository._preco_vigente_em([_linha(850, "2026-01-01")], date(2025, 12, 31)) is None


def test_preco_vigente_sem_degrau_nenhum_e_none():
    assert repository._preco_vigente_em([], date(2026, 9, 12)) is None


def test_preco_vigente_nao_depende_da_ordem_das_linhas():
    """A régua escolhe pelo MAIOR `vigente_desde`, não pela posição na lista — quem
    confiar na ordem do SELECT quebra no dia em que alguém mudar o ORDER BY."""
    fora_de_ordem = [_linha(950, "2026-08-01"), _linha(700, "2025-05-01"), _linha(850, "2026-01-01")]
    assert repository._preco_vigente_em(fora_de_ordem, date(2026, 9, 12)) == 950.0
    assert repository._preco_vigente_em(fora_de_ordem, date(2025, 6, 1)) == 700.0


# ── 2. O TIPO do argumento (o driver recusa antes do SQL) ────────────────────

def test_valor_vai_como_decimal_e_data_como_date():
    """NUMERIC exige Decimal e DATE exige datetime.date. Float ou str aqui =
    DataError dentro do asyncpg = 500 na rota = 'não acontece nada' na tela."""
    conn = _FakeConn()
    _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
        "Feca", "Move", "Bet365", "950,00".replace(",", "."), "2026-08-01"))
    sql, args = next(i for i in conn.inserts if "INSERT INTO fornecedor_preco" in i[0])
    assert isinstance(args[3], Decimal), f"valor foi como {type(args[3]).__name__}"
    assert isinstance(args[4], date), f"vigente_desde foi como {type(args[4]).__name__}"


def test_sem_cast_de_tipo_no_sql_do_preco():
    """Com `::numeric`/`::date` o tipo do parâmetro fica ambíguo; sem eles vem da
    coluna e não há dúvida sobre o que o driver espera. Ver CLAUDE.md."""
    conn = _FakeConn()
    _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
        "Feca", "Move", "Bet365", 950, "2026-08-01"))
    sql = next(i[0] for i in conn.inserts if "INSERT INTO fornecedor_preco" in i[0])
    assert "::date" not in sql and "::numeric" not in sql


# ── 3. Validação: o que a rota tem de recusar ────────────────────────────────

@pytest.mark.parametrize("valor", [0, -100, "0", "abc", None])
def test_preco_nao_positivo_ou_ilegivel_e_recusado(valor):
    """Preço zero seria conta de graça e preço negativo não existe. Recusar na
    fronteira é mais barato que descobrir depois, no meio de um KPI."""
    conn = _FakeConn()
    with pytest.raises(ValueError):
        _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
            "Feca", "Move", "Bet365", valor, "2026-08-01"))
    assert not conn.inserts, "recusou mas escreveu assim mesmo"


@pytest.mark.parametrize("forn,casa", [("", "Bet365"), ("Move", ""), ("  ", "Bet365")])
def test_fornecedor_ou_casa_vazio_e_recusado(forn, casa):
    conn = _FakeConn()
    with pytest.raises(ValueError):
        _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
            "Feca", forn, casa, 950, "2026-08-01"))
    assert not conn.inserts


def test_data_ilegivel_e_recusada():
    conn = _FakeConn()
    with pytest.raises(ValueError):
        _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
            "Feca", "Move", "Bet365", 950, "01/08/2026"))
    assert not conn.inserts


# ── 4. O espelho: custo_conta virou VISTA, não fonte ────────────────────────

def test_escrever_preco_espelha_o_vigente_de_hoje_no_custo_conta():
    """As telas antigas leem `custo_conta[fornecedor||casa]` como um número e seguem
    no ar até a Fatia 5. Se o espelho não for refeito, elas mostram um preço que já
    não existe — duas fontes de verdade, que é o invariante nº 1 do projeto."""
    hoje = date.today().isoformat()
    conn = _FakeConn(precos=[_linha(950, hoje)], custo_conta={"Move||Bet365": 850.0})
    _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
        "Feca", "Move", "Bet365", 950, hoje))
    assert conn.custo_conta["Move||Bet365"] == 950.0


def test_espelho_nao_mexe_nos_outros_pares():
    """Escrever o preço da Bet365 do Move não pode encostar no par do JC."""
    hoje = date.today().isoformat()
    conn = _FakeConn(precos=[_linha(950, hoje)],
                     custo_conta={"Move||Bet365": 850.0, "JC||Betano": 550.0})
    _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
        "Feca", "Move", "Bet365", 950, hoje))
    assert conn.custo_conta["JC||Betano"] == 550.0


def test_preco_futuro_nao_entra_no_espelho_de_hoje():
    """Registrar hoje um preço que só passa a valer em NOVEMBRO não pode mudar o
    que a tela antiga cobra agora. O espelho é do vigente HOJE, não do último
    registrado — e essa diferença é a razão de a tabela existir."""
    futuro = date(date.today().year + 1, 1, 1)
    conn = _FakeConn(precos=[_linha(850, "2026-01-01"),
                             {"valor": Decimal("1200"), "vigente_desde": futuro}],
                     custo_conta={"Move||Bet365": 850.0})
    _com_pool(conn, lambda: repository.registrar_preco_fornecedor(
        "Feca", "Move", "Bet365", 1200, futuro.isoformat()))
    assert conn.custo_conta["Move||Bet365"] == 850.0


def test_par_que_ficou_sem_preco_sai_do_espelho():
    """Apagar o único degrau tira a chave do JSONB. Deixar o valor velho lá faria a
    tela antiga cobrar um preço que o dono acabou de remover."""
    conn = _FakeConn(precos=[], custo_conta={"Move||Bet365": 850.0})
    conn._alvo_delete = {"fornecedor": "Move", "casa": "Bet365"}
    ok = _com_pool(conn, lambda: repository.remover_preco_fornecedor("Feca", 42))
    assert ok is True
    assert "Move||Bet365" not in conn.custo_conta


def test_remover_preco_inexistente_nao_toca_no_espelho():
    conn = _FakeConn(custo_conta={"Move||Bet365": 850.0})
    conn._alvo_delete = None
    ok = _com_pool(conn, lambda: repository.remover_preco_fornecedor("Feca", 999))
    assert ok is False
    assert conn.custo_conta == {"Move||Bet365": 850.0}


# ── 5. A chave do JSONB tem de bater com a que o dashboard monta ────────────

def test_chave_do_espelho_e_fornecedor_pipe_pipe_casa():
    """`custoData` no dashboard é indexado por `fornecedor||casa`. Uma chave com
    espaço a mais aqui não dá erro: dá um preço que a tela antiga nunca acha."""
    assert repository._preco_chave("Move", "Bet365") == "Move||Bet365"
    assert repository._preco_chave("  Move  ", " Bet365 ") == "Move||Bet365"
