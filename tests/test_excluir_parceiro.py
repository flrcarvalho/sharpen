"""Excluir conta: apaga a conta + SÓ as apostas dela, e só com o nome conferido.

É a única operação do sistema que destrói histórico. Dois riscos, um teste cada:

  · **Vazar escopo** — o DELETE varre `bilhetes` por (dono, casa, parceiro). Errar
    qualquer um dos três apaga aposta de outra conta, de outra casa ou — pior — de
    outro usuário, e a lixeira nem registraria o que sumiu.
  · **Disparar sem confirmação** — a UI trava o botão até o nome exato ser digitado,
    mas a rota é DELETE e não pode confiar só no cliente: um `DELETE /parceiros/7`
    por engano (histórico do navegador, script, curl) não pode apagar nada.

Roda sem Postgres: o conftest stuba asyncpg/database e o pool aqui é de mentira.
Irmão de `test_renomear_parceiro_assinatura.py` (mesmo molde de _FakeConn).
"""
import asyncio
import json
from unittest.mock import patch

import repository


class _FakeConn:
    """Conn de mentira com o mínimo que `excluir_parceiro` usa.

    `bilhetes` é a base inteira (de todos os donos/casas); o DELETE do repositório
    é reproduzido aqui filtrando pelos MESMOS três parâmetros que ele passa — é o
    que faz o teste de escopo valer alguma coisa.
    """

    def __init__(self, conta, bilhetes, caixa=None):
        self.conta = conta                 # None = conta inexistente
        self.bilhetes = bilhetes
        self.caixa = caixa if caixa is not None else []   # lançamentos da Caixa (s314)
        self.execs = []
        self.lixeira = []

    def transaction(self):
        conn = self

        class _T:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _T()

    async def fetchrow(self, _sql, *_a):
        return self.conta

    async def fetch(self, sql, *a):
        # Duas varreduras destrutivas, cada uma devolvendo o próprio snapshot: as
        # apostas e (s314) os lançamentos da Caixa, que sairiam sozinhos pelo CASCADE.
        if "DELETE FROM caixa_mov" in sql:
            dono, pid = a
            fica, sai = [], []
            for m in self.caixa:
                (sai if (m["dono"] == dono and m["parceiro_id"] == pid) else fica).append(m)
            self.caixa[:] = fica
            return [{"linha": json.dumps(m)} for m in sai]
        assert "DELETE FROM bilhetes" in sql
        dono, casa, parceiro = a
        fica, sai = [], []
        for b in self.bilhetes:
            alvo = (b["dono"] == dono and b["casa"] == casa and b["parceiro"] == parceiro)
            (sai if alvo else fica).append(b)
        self.bilhetes[:] = fica
        return [{"linha": json.dumps(b)} for b in sai]

    async def execute(self, sql, *a):
        self.execs.append((sql, a))
        if "INSERT INTO lixeira_contas" in sql:
            self.lixeira.append(a)
        return "DELETE 1"


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


def _bilhete(bid, dono="Feca", casa="Tivo", parceiro="Feca [Eu]"):
    return {"id": bid, "dono": dono, "casa": casa, "parceiro": parceiro,
            "stake": "51,00", "odd": "27,55", "resultado": "W"}


def _mov(mid, tipo="deposito", dono="Feca", parceiro_id=351, valor=500.0):
    return {"id": mid, "dono": dono, "parceiro_id": parceiro_id, "tipo": tipo,
            "data": "2026-08-01", "valor": valor, "obs": "PIX"}


def _excluir(conta, bilhetes, confirmar="Feca [Eu]", dono="Feca", caixa=None):
    conn = _FakeConn(conta, bilhetes, caixa)
    # patch como CONTEXTO (não atribuição solta): no CI, com TEST_DATABASE_URL, o
    # `test_repository_db.py` usa o `get_pool` de verdade — um stub vazado o derrubaria.
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))):
        res = asyncio.run(repository.excluir_parceiro(351, dono, confirmar))
    return res, conn


_CONTA = {"casa": "Tivo", "nome": "Feca [Eu]", "arquivado": False}


def test_apaga_a_conta_e_as_apostas_dela():
    base = [_bilhete(1), _bilhete(2)]
    res, conn = _excluir(_CONTA, base)
    assert res["ok"] is True
    assert res["bilhetes_excluidos"] == 2
    assert base == []
    assert any("DELETE FROM parceiros" in s for s, _ in conn.execs)


def test_nao_toca_em_aposta_de_outra_conta_casa_ou_dono():
    minha = _bilhete(1)
    base = [
        minha,
        _bilhete(2, parceiro="LavaFeca"),      # outra conta, mesma casa
        _bilhete(3, casa="Bet365"),            # mesma conta, outra casa
        _bilhete(4, dono="Jonathan"),          # outro usuário — o pior vazamento
    ]
    res, conn = _excluir(_CONTA, base)
    assert res["bilhetes_excluidos"] == 1
    assert minha not in base
    assert [b["id"] for b in base] == [2, 3, 4], "vazou escopo do DELETE"


def test_snapshot_da_lixeira_bate_com_o_que_saiu():
    base = [_bilhete(1), _bilhete(2)]
    res, conn = _excluir(_CONTA, base)
    assert len(conn.lixeira) == 1
    dono, casa, parceiro, arquivado, n, payload, caixa_payload = conn.lixeira[0]
    assert (dono, casa, parceiro, n) == ("Feca", "Tivo", "Feca [Eu]", 2)
    assert arquivado is False
    linhas = json.loads(payload)          # tem de ser JSON válido p/ o cast ::jsonb
    assert [x["id"] for x in linhas] == [1, 2]
    assert linhas[0]["odd"] == "27,55", "snapshot perdeu coluna da linha original"
    assert json.loads(caixa_payload) == []
    assert res["lixeira_dias"] == repository.LIXEIRA_DIAS


# ── Caixa (s314) ──────────────────────────────────────────────────────────────
# Os lançamentos da conta sairiam sozinhos pelo ON DELETE CASCADE de `parceiros`.
# Se não entrarem no MESMO snapshot, restaurar a conta devolve as apostas e perde o
# dinheiro — a lixeira meio-cheia, irmã do UPSERT meio-atualizado.

def test_lixeira_leva_junto_os_lancamentos_da_caixa():
    caixa = [_mov(1, "inicial", valor=3000.0), _mov(2, "deposito")]
    _, conn = _excluir(_CONTA, [_bilhete(1)], caixa=caixa)
    payload = conn.lixeira[0][6]
    linhas = json.loads(payload)
    assert [x["id"] for x in linhas] == [1, 2]
    assert linhas[0]["valor"] == 3000.0, "snapshot perdeu campo do lançamento"
    assert caixa == [], "a caixa da conta não foi apagada junto"


def test_nao_apaga_caixa_de_outra_conta_ou_de_outro_dono():
    minha = _mov(1)
    caixa = [minha, _mov(2, parceiro_id=999), _mov(3, dono="Jonathan")]
    _, conn = _excluir(_CONTA, [_bilhete(1)], caixa=caixa)
    assert [m["id"] for m in caixa] == [2, 3], "vazou escopo do DELETE da caixa"
    assert [x["id"] for x in json.loads(conn.lixeira[0][6])] == [1]


def test_purga_o_vencido_antes_de_gravar():
    _, conn = _excluir(_CONTA, [_bilhete(1)])
    purgas = [a for s, a in conn.execs if "DELETE FROM lixeira_contas" in s]
    assert purgas, "lixeira nunca é podada — cresceria sem limite"
    assert purgas[0] == (str(repository.LIXEIRA_DIAS),)


def test_nome_errado_nao_apaga_nada():
    base = [_bilhete(1)]
    res, conn = _excluir(_CONTA, base, confirmar="Feca")   # prefixo do nome certo
    assert res["ok"] is False
    assert base == [_bilhete(1)]
    assert conn.execs == [], "escreveu algo mesmo sem a confirmação bater"


def test_nome_vazio_nao_apaga_nada():
    base = [_bilhete(1)]
    res, conn = _excluir(_CONTA, base, confirmar="")
    assert res["ok"] is False
    assert base == [_bilhete(1)]


def test_conta_de_outro_dono_nao_existe():
    # O SELECT filtra por (id, dono); dono errado não acha a linha e nada acontece.
    base = [_bilhete(1)]
    res, conn = _excluir(None, base, dono="Jonathan")
    assert res["ok"] is False
    assert "não encontrada" in res["motivo"]
    assert base == [_bilhete(1)]
    assert conn.execs == []
