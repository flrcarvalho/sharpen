"""Renomear tipster tem de propagar a TODAS as referências por nome — não só aos bilhetes.

O tipster não tem id em lugar nenhum: seis lugares o referenciam pelo NOME (a lista e o
porquê estão em `repository._TIPSTER_REFS_TEXTO`). Até a s341 o rename tocava três deles
(`tipsters`, `bilhetes`, `tipster_unidade`) e deixava três para trás:

  · `casa_config.tipsters` — CSV da atribuição por casa. A casa dedicada passa a apontar
    para um nome que não existe e o matcher para de cravar, SEM erro nenhum.
  · `custo_store.custo_tipster` — o nome é CHAVE de um blob JSONB. O custo continua sendo
    cobrado no KPI e some da tabela onde se lança: a família do "tipster cobrado e
    ineditável" (s274).
  · `polymarket_ativos_tipster.tipster`.

Irmão de `test_renomear_parceiro_assinatura.py` (mesma classe de defeito, outro campo).
Roda sem Postgres: o conftest stuba asyncpg/database e o pool aqui é de mentira.

NÃO cobre (e não tem como, com conn dublada): que o UNIQUE (dono, nome) do Postgres
exista de fato, que a transação faça rollback de verdade, nem o `matcher.invalidar` —
esse vive na ROTA (`app/main.py`), não no repository, e é a 7ª ponta da propagação.
"""
import asyncio
import json
from unittest.mock import patch

import repository


class _FakeConn:
    """Conn de mentira com o mínimo que `renomear_tipster` / `resumo_tipster` usam."""

    def __init__(self, *, nome, colide=False, casas=(), custo=None,
                 n_bilhetes=1234, n_unidades=0, n_poly=0, escada_destino=()):
        self.nome = nome
        self.colide = colide
        self.casas = [dict(c) for c in casas]        # [{"casa":..., "tipsters": "a,b"}]
        self.custo = custo                           # dict do blob, ou None (sem registro)
        self.n_bilhetes = n_bilhetes
        self.n_unidades = n_unidades
        self.n_poly = n_poly
        self.escada_destino = list(escada_destino)   # datas já gravadas sob o nome NOVO
        self.execs = []                              # [(sql, args)] na ORDEM

    # --- transação ---------------------------------------------------------
    def transaction(self):
        conn = self

        class _T:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _T()

    # --- queries -----------------------------------------------------------
    async def fetchrow(self, sql, *_a):
        if "FROM tipsters" in sql and "arquivado" in sql:
            return {"id": 7, "nome": self.nome, "arquivado": False}
        if "FROM tipsters" in sql:
            return {"nome": self.nome}
        return None

    async def fetchval(self, sql, *_a):
        if "SELECT 1 FROM tipsters" in sql:
            return 1 if self.colide else None
        if "FROM custo_store" in sql:
            return None if self.custo is None else json.dumps(self.custo)
        if "FROM bilhetes" in sql:
            return self.n_bilhetes
        if "FROM tipster_unidade" in sql:
            return self.n_unidades
        if "FROM polymarket_ativos_tipster" in sql:
            return self.n_poly
        return None

    async def fetch(self, sql, *_a):
        if "FROM casa_config" in sql:
            return [dict(c) for c in self.casas]
        return []

    async def execute(self, sql, *a):
        self.execs.append((" ".join(sql.split()), a))
        if "UPDATE casa_config" in sql:
            csv, _dono, casa = a
            for c in self.casas:
                if c["casa"] == casa:
                    c["tipsters"] = csv
            return "UPDATE 1"
        if "UPDATE custo_store" in sql:
            self.custo = json.loads(a[0])
            return "UPDATE 1"
        if "DELETE FROM tipster_unidade" in sql:
            n = len(self.escada_destino)
            self.escada_destino = []
            return f"DELETE {n}"
        if "UPDATE bilhetes" in sql:
            return f"UPDATE {self.n_bilhetes}"
        if "UPDATE tipster_unidade" in sql:
            return f"UPDATE {self.n_unidades}"
        if "UPDATE polymarket_ativos_tipster" in sql:
            return f"UPDATE {self.n_poly}"
        return "UPDATE 1"


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


def _rodar(coro_factory, conn):
    # patch como CONTEXTO (não atribuição solta): no CI, com TEST_DATABASE_URL, o
    # `test_repository_db.py` usa o `get_pool` de verdade — um stub vazado o derrubaria.
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))):
        return asyncio.run(coro_factory())


def _renomear(conn, novo="Peixe Sharp"):
    return _rodar(lambda: repository.renomear_tipster(7, novo, "Feca"), conn)


def _sqls(conn):
    return [s for s, _ in conn.execs]


def _upd(conn, tabela):
    """Args do UPDATE daquela tabela (None se ela nunca foi tocada)."""
    for sql, args in conn.execs:
        if sql.startswith(f"UPDATE {tabela} SET"):
            return args
    return None


# ── As três referências de texto direto ──────────────────────────────────────

def test_bilhetes_escada_e_polymarket_recebem_o_nome_novo():
    conn = _FakeConn(nome="Peixe", n_unidades=3, n_poly=2)
    res = _renomear(conn)
    assert res["ok"]
    for tabela in ("bilhetes", "tipster_unidade", "polymarket_ativos_tipster"):
        args = _upd(conn, tabela)
        assert args is not None, f"{tabela} ficou para trás no rename"
        assert args == ("Peixe Sharp", "Feca", "Peixe")
    assert res["bilhetes_atualizados"] == 1234
    assert res["unidades"] == 3
    assert res["polymarket"] == 2


def test_o_cadastro_muda_por_id_e_nao_por_nome():
    conn = _FakeConn(nome="Peixe")
    _renomear(conn)
    args = _upd(conn, "tipsters")
    assert args == ("Peixe Sharp", 7, "Feca")


# ── casa_config: CSV, elemento a elemento ────────────────────────────────────

def test_casa_config_troca_o_ELEMENTO_e_nao_a_substring():
    # A armadilha: um `replace` cru no CSV transformaria "Zé Turbo" em "Zé Sharp Turbo".
    # O outro nome da lista tem de sair intacto.
    conn = _FakeConn(nome="Zé", casas=[{"casa": "BETesporte", "tipsters": "Zé,Zé Turbo"}])
    res = _renomear(conn, novo="Zé Sharp")
    assert conn.casas[0]["tipsters"] == "Zé Sharp,Zé Turbo"
    assert res["casas_config"] == 1


def test_casa_config_nao_duplica_quando_o_nome_novo_ja_esta_na_lista():
    # Curadoria feita com os DOIS nomes do mesmo tipster: depois do rename vira um só.
    conn = _FakeConn(nome="Peixe", casas=[{"casa": "Stake", "tipsters": "Peixe,Peixe Sharp"}])
    _renomear(conn)
    assert conn.casas[0]["tipsters"] == "Peixe Sharp"


def test_casa_config_que_nao_cita_o_tipster_nao_e_tocada():
    conn = _FakeConn(nome="Peixe", casas=[{"casa": "Betano", "tipsters": "Arrudex"}])
    res = _renomear(conn)
    assert conn.casas[0]["tipsters"] == "Arrudex"
    assert res["casas_config"] == 0
    assert not any(s.startswith("UPDATE casa_config") for s in _sqls(conn))


# ── custo_store: o nome é CHAVE de um blob JSONB ─────────────────────────────

def test_custo_mensal_segue_o_nome_novo():
    conn = _FakeConn(nome="Peixe", custo={"Peixe": {"2026-08": "300"}, "Outro": {"2026-08": "50"}})
    res = _renomear(conn)
    assert conn.custo == {"Outro": {"2026-08": "50"}, "Peixe Sharp": {"2026-08": "300"}}
    assert res["custo_movido"] is True


def test_custo_com_chave_orfa_no_destino_funde_e_a_ORIGEM_vence():
    # Chave com o nome NOVO só pode ser órfã (nenhum tipster se chamava assim — é UNIQUE).
    # Os meses se juntam; onde os dois têm valor, vale o do tipster que existe de verdade.
    conn = _FakeConn(nome="Peixe", custo={"Peixe": {"2026-08": "300"},
                                          "Peixe Sharp": {"2026-07": "90", "2026-08": "1"}})
    _renomear(conn)
    assert conn.custo == {"Peixe Sharp": {"2026-07": "90", "2026-08": "300"}}


def test_dono_sem_registro_de_custo_nao_cria_um():
    conn = _FakeConn(nome="Peixe", custo=None)
    res = _renomear(conn)
    assert res["custo_movido"] is False
    assert not any(s.startswith("UPDATE custo_store") for s in _sqls(conn))


def test_tipster_sem_custo_lancado_nao_mexe_no_blob_dos_outros():
    conn = _FakeConn(nome="Peixe", custo={"Arrudex": {"2026-08": "70"}})
    res = _renomear(conn)
    assert conn.custo == {"Arrudex": {"2026-08": "70"}}
    assert res["custo_movido"] is False


# ── Ordem e travas ───────────────────────────────────────────────────────────

def test_o_delete_da_escada_vem_ANTES_do_update_da_escada():
    # `tipster_unidade` é UNIQUE (dono, tipster, vigente_desde). Degrau já gravado sob o
    # nome novo é órfão e travaria o UPDATE com UniqueViolation → 500 na rota.
    conn = _FakeConn(nome="Peixe", n_unidades=2, escada_destino=["2026-01-01"])
    _renomear(conn)
    sqls = _sqls(conn)
    i_del = next(i for i, s in enumerate(sqls) if s.startswith("DELETE FROM tipster_unidade"))
    i_upd = next(i for i, s in enumerate(sqls) if s.startswith("UPDATE tipster_unidade SET"))
    assert i_del < i_upd


def test_nome_ja_usado_recusa_e_nao_escreve_NADA():
    conn = _FakeConn(nome="Peixe", colide=True,
                     casas=[{"casa": "Stake", "tipsters": "Peixe"}],
                     custo={"Peixe": {"2026-08": "300"}})
    res = _renomear(conn)
    assert res["ok"] is False
    assert "esse nome" in res["motivo"]
    assert conn.execs == []
    assert conn.casas[0]["tipsters"] == "Peixe"
    assert conn.custo == {"Peixe": {"2026-08": "300"}}


def test_nome_vazio_recusa_antes_de_abrir_conexao():
    conn = _FakeConn(nome="Peixe")
    res = _renomear(conn, novo="   ")
    assert res["ok"] is False
    assert conn.execs == []


def test_mesmo_nome_e_no_op():
    conn = _FakeConn(nome="Peixe", casas=[{"casa": "Stake", "tipsters": "Peixe"}],
                     custo={"Peixe": {"2026-08": "300"}})
    res = _renomear(conn, novo="Peixe")
    assert res["ok"] is True
    assert res["bilhetes_atualizados"] == 0
    assert conn.execs == []


def test_espaco_nas_pontas_do_nome_novo_e_aparado():
    conn = _FakeConn(nome="Peixe")
    res = _renomear(conn, novo="  Peixe Sharp  ")
    assert res["nome"] == "Peixe Sharp"
    assert _upd(conn, "bilhetes") == ("Peixe Sharp", "Feca", "Peixe")


# ── resumo_tipster: o número que a tela promete ──────────────────────────────

def test_resumo_conta_as_casas_pelo_ELEMENTO_do_csv():
    # A 2ª casa é de OUTRO tipster, "Peixe Turbo", que CONTÉM "Peixe" no meio do nome.
    # Contar por substring diria 2 e a tela prometeria uma casa que o UPDATE não toca.
    # (o par tem de conter mesmo um ao outro: "Peixinho" não serve, é Peix-I-nho — foi
    # exatamente esse dado frouxo que deixou a mutação #10 escapar na 1ª rodada)
    conn = _FakeConn(nome="Peixe", n_bilhetes=1234, n_unidades=3, n_poly=1,
                     custo={"Peixe": {"2026-08": "300"}},
                     casas=[{"casa": "Stake", "tipsters": "Peixe,Arrudex"},
                            {"casa": "Betano", "tipsters": "Peixe Turbo"}])
    res = _rodar(lambda: repository.resumo_tipster(7, "Feca"), conn)
    assert res["n_bilhetes"] == 1234
    assert res["n_unidades"] == 3
    assert res["n_polymarket"] == 1
    assert res["n_casas_config"] == 1
    assert res["tem_custo"] is True


def test_resumo_de_tipster_inexistente_e_None():
    conn = _FakeConn(nome="Peixe")
    conn.fetchrow = lambda *a, **k: asyncio.sleep(0, result=None)
    assert _rodar(lambda: repository.resumo_tipster(9, "Feca"), conn) is None
