"""Renomear conta tem de RECALCULAR a assinatura dos bilhetes que move.

O `parceiro` entra no hash de `_assinatura` (com ou sem código de bilhete). Até a s198 o
`renomear_parceiro` só trocava o texto da coluna: os bilhetes ficavam com o hash do nome
ANTIGO, então a próxima captura da mesma conta calculava uma assinatura nova, não colidia
com nada, o UPSERT não dedupava e o histórico inteiro DUPLICAVA.

Irmão de `test_assinatura_edicao.py` (s145, mesma falha pelo lápis do editor). Roda sem
Postgres: o conftest stuba asyncpg/database e o pool aqui é de mentira.
"""
import asyncio
from unittest.mock import patch

import repository

_A = repository._assinatura


class _FakeConn:
    """Conn de mentira com o mínimo que `renomear_parceiro` usa."""

    def __init__(self, conta, bilhetes, outras=()):
        self.conta = conta                 # {"casa": ..., "nome": ...}
        self.bilhetes = bilhetes           # lista de dicts (colunas do SELECT)
        self.outras = set(outras)          # {(casa, nome)} de OUTRAS contas do dono
        self.execs = []

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
    async def fetchrow(self, _sql, *_a):
        return self.conta

    async def fetchval(self, sql, *a):
        if "FROM parceiros" in sql:
            # Colisão de nome: (dono, casa, nome, id≠self). A casa consultada é a de
            # DESTINO — conferir na de origem deixaria passar um nome já ocupado lá.
            _dono, casa, nome, _id = a
            return 1 if (casa, nome) in self.outras else None
        # NOT EXISTS da colisão de assinatura: (dono, casa, parceiro, sig, id)
        dono, casa, parceiro, sig, bid = a
        return not any(
            b.get("_dono", dono) == dono and b["casa"] == casa
            and b["parceiro"] == parceiro and b["assinatura"] == sig and b["id"] != bid
            for b in self.bilhetes
        )

    async def fetch(self, _sql, *_a):
        return [dict(b) for b in self.bilhetes]

    async def execute(self, sql, *a):
        self.execs.append((sql, a))
        if "UPDATE bilhetes SET casa" in sql:
            casa, novo = a[0], a[1]
            for b in self.bilhetes:
                b["casa"], b["parceiro"] = casa, novo
            return f"UPDATE {len(self.bilhetes)}"
        if "UPDATE bilhetes SET assinatura" in sql:
            nova, bid, _dono = a
            for b in self.bilhetes:
                if b["id"] == bid:
                    b["assinatura"] = nova
            return "UPDATE 1"
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


def _bilhete(bid, **kw):
    b = dict(id=bid, casa="Tivo", parceiro="Feca [[Eu]]", data="26/07/2026",
             aposta="Múltipla", descricao="Karmine Corp [Team Heretics v Karmine Corp]",
             stake="51,00", odd="27,55", codigo_bilhete=None)
    b.update(kw)
    b["assinatura"] = _A({**b, "codigo_bilhete": b["codigo_bilhete"] or ""})
    return b


def _renomear(bilhetes, novo="Feca [Eu]", casa=None, outras=()):
    conn = _FakeConn({"casa": "Tivo", "nome": "Feca [[Eu]]"}, bilhetes, outras)
    # patch como CONTEXTO (não atribuição solta): no CI, com TEST_DATABASE_URL, o
    # `test_repository_db.py` usa o `get_pool` de verdade — um stub vazado o derrubaria.
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))):
        res = asyncio.run(repository.editar_parceiro(351, novo, casa, "Feca"))
    return res, conn


def test_assinatura_segue_o_nome_novo():
    b = _bilhete(1)
    velha = b["assinatura"]
    res, conn = _renomear([b])
    esperada = _A({**b, "parceiro": "Feca [Eu]", "codigo_bilhete": ""})
    assert conn.bilhetes[0]["assinatura"] == esperada
    assert conn.bilhetes[0]["assinatura"] != velha
    assert res["bilhetes_atualizados"] == 1
    assert res["assinaturas_recalculadas"] == 1


def test_bilhete_com_codigo_tambem_muda():
    # Com código o hash é "ID|casa|parceiro|código" — o parceiro está lá do mesmo jeito.
    b = _bilhete(1, codigo_bilhete="298782220")
    _renomear([b])
    assert b["assinatura"] == _A({**b, "parceiro": "Feca [Eu]",
                                  "codigo_bilhete": "298782220"})


def test_duas_linhas_de_conteudo_identico_nao_colidem():
    # Sem código e com stake/odd/descrição iguais, o hash base é o mesmo: a segunda tem de
    # escalar o _counter, como o upsert já faz para bilhetes distintos de conteúdo igual.
    a, b = _bilhete(1), _bilhete(2)
    res, conn = _renomear([a, b])
    assinaturas = {x["assinatura"] for x in conn.bilhetes}
    assert len(assinaturas) == 2, "duas linhas ficaram com a MESMA assinatura"
    assert res["assinaturas_recalculadas"] == 2


def test_nome_igual_nao_mexe_em_nada():
    b = _bilhete(1)
    velha = b["assinatura"]
    res, conn = _renomear([b], novo="Feca [[Eu]]")
    assert res["bilhetes_atualizados"] == 0
    assert res["assinaturas_recalculadas"] == 0
    assert conn.bilhetes[0]["assinatura"] == velha
    assert conn.execs == []


# ── Mover de casa (s312) ─────────────────────────────────────────────────────
# O modal de edição passou a oferecer a CASA, não só o nome. `casa` está no hash de
# `_assinatura` lado a lado com `parceiro`: uma conta movida sem recálculo ficaria com o
# hash da casa velha e a próxima captura duplicaria o histórico inteiro — a mesma falha da
# s198, com a outra metade da chave.

def test_mover_de_casa_recalcula_assinatura():
    b = _bilhete(1)
    velha = b["assinatura"]
    res, conn = _renomear([b], novo="Feca [[Eu]]", casa="Betano")
    esperada = _A({**b, "casa": "Betano", "codigo_bilhete": ""})
    assert conn.bilhetes[0]["casa"] == "Betano", "o bilhete não seguiu a conta"
    assert conn.bilhetes[0]["assinatura"] == esperada
    assert conn.bilhetes[0]["assinatura"] != velha
    assert res["casa"] == "Betano"
    assert res["bilhetes_atualizados"] == 1
    assert res["assinaturas_recalculadas"] == 1


def test_mover_e_renomear_de_uma_vez():
    # Os dois campos entram no MESMO hash: mudar um de cada vez gravaria uma assinatura
    # intermediária que não corresponde a bilhete nenhum.
    b = _bilhete(1, codigo_bilhete="298782220")
    _renomear([b], novo="Feca [Eu]", casa="Betano")
    assert b["casa"] == "Betano" and b["parceiro"] == "Feca [Eu]"
    assert b["assinatura"] == _A({**b, "casa": "Betano", "parceiro": "Feca [Eu]",
                                  "codigo_bilhete": "298782220"})


def test_casa_none_mantem_a_atual():
    # É o caminho do /renomear de sempre: sem casa no corpo, a conta não sai do lugar.
    b = _bilhete(1)
    res, conn = _renomear([b], novo="Feca [Eu]", casa=None)
    assert conn.bilhetes[0]["casa"] == "Tivo"
    assert res["casa"] == "Tivo"


def test_nada_muda_nao_mexe_em_nada():
    # Nome igual E casa igual à atual (o operador abriu o modal e salvou sem editar).
    b = _bilhete(1)
    velha = b["assinatura"]
    res, conn = _renomear([b], novo="Feca [[Eu]]", casa="Tivo")
    assert res["bilhetes_atualizados"] == 0
    assert res["assinaturas_recalculadas"] == 0
    assert conn.bilhetes[0]["assinatura"] == velha
    assert conn.execs == []


def test_colisao_conferida_na_casa_de_DESTINO():
    # O nome está livre na Tivo (origem) e OCUPADO na Betano (destino): mover tem de
    # falhar. Conferir a colisão na casa de origem passaria batido e o UPDATE violaria o
    # UNIQUE (dono, casa, nome) — erro de banco no meio da transação, não recusa limpa.
    b = _bilhete(1)
    res, conn = _renomear([b], novo="Feca [Eu]", casa="Betano",
                          outras={("Betano", "Feca [Eu]")})
    assert res["ok"] is False
    assert "Já existe" in res["motivo"]
    assert conn.execs == [], "recusou mas mexeu no banco"


def test_mesmo_nome_livre_no_destino_move():
    # Contraprova da anterior: o nome ocupado na ORIGEM não pode barrar a mudança —
    # senão nenhuma conta conseguiria mudar só de casa, mantendo o nome.
    b = _bilhete(1)
    res, _ = _renomear([b], novo="Feca [[Eu]]", casa="Betano",
                       outras={("Tivo", "Feca [[Eu]]")})
    assert res["ok"] is True and res["casa"] == "Betano"
