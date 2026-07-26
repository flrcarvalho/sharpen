"""O pré-dedup por código enxerga a CONTA, não só o dono.

O UPSERT trata conta como espaço separado (`UNIQUE (dono, casa, parceiro, assinatura)`),
mas o pré-dedup filtrava só por `dono`: um bilhete que já existisse em QUALQUER conta do
dono era descartado ANTES de chegar na IA e nunca entrava na conta que estava sendo
extraída. Foi o que fez a 2ª extração da Tivo (s198) trazer 2 de 25 — os outros 20 estavam
na conta órfã, e repetir a extração não adiantava nada.

Aqui trava a numeração dos placeholders (é onde um filtro dinâmico quebra) e o fallback
sem conta, que os chamadores antigos usam.
"""
import asyncio
from unittest.mock import patch

import repository


class _Conn:
    def __init__(self):
        self.sql = None
        self.params = None

    async def fetch(self, sql, *params):
        self.sql, self.params = sql, list(params)
        return []


class _Pool:
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


def _chamar(fn, *args, **kw):
    conn = _Conn()
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_Pool(conn))):
        asyncio.run(fn(*args, **kw))
    return conn


def test_sem_conta_mantem_o_filtro_antigo():
    c = _chamar(repository.get_codigos_resolvidos, ["A1"], "Feca")
    assert "casa =" not in c.sql and "parceiro =" not in c.sql
    assert c.params == [["A1"], "Feca"]


def test_com_conta_filtra_casa_e_parceiro():
    c = _chamar(repository.get_codigos_resolvidos, ["A1"], "Feca", "Tivo", "Feca [Eu]")
    assert "AND casa = $3" in c.sql
    assert "AND parceiro = $4" in c.sql
    assert c.params == [["A1"], "Feca", "Tivo", "Feca [Eu]"]


def test_so_casa_numera_certo():
    # Parceiro vazio (chamador que só sabe a casa) não pode deixar um $4 órfão no SQL.
    c = _chamar(repository.get_codigos_resolvidos, ["A1"], "Feca", "Tivo", "")
    assert "AND casa = $3" in c.sql and "$4" not in c.sql
    assert c.params == [["A1"], "Feca", "Tivo"]


def test_codigos_existentes_tambem_escopa():
    c = _chamar(repository.get_codigos_existentes, ["A1"], "Feca", "Tivo", "Feca [Eu]")
    assert "AND casa = $3" in c.sql and "AND parceiro = $4" in c.sql


def test_lista_vazia_nao_consulta():
    c = _chamar(repository.get_codigos_resolvidos, [], "Feca", "Tivo", "Feca [Eu]")
    assert c.sql is None
