"""Excluir em massa (s432): a seleção da Base Completa sai INTEIRA para a lixeira, e só ela.

Pedido de tester (Gabriel, Los Panas): apagar a base de tipsters importada e ficar só com os
próprios dados. A seleção chega a dezenas de milhares de linhas com um clique no
"selecionar todas", então são três riscos, um grupo de teste cada:

  · **Vazar escopo** — id de OUTRO dono na lista não pode sair. O WHERE filtra por `dono`
    da sessão; o id alheio volta em `ignorados`.
  · **Disparar sem confirmação** — a UI só libera o botão com o número digitado, mas a
    rota é destrutiva e reconfere no servidor (mesma régua do Excluir conta).
  · **Lixeira que não corresponde ao que saiu** — snapshot e DELETE são UMA instrução
    (`WITH sai AS (DELETE … RETURNING to_jsonb) INSERT INTO lixeira_bilhetes`).

Roda sem Postgres: o conftest stuba asyncpg/database e o pool aqui é de mentira. O
`_FakeConn.execute` reproduz o CTE filtrando pelos MESMOS parâmetros que o repositório passa.

MUTAÇÕES QUE ESTES TESTES PEGAM (rodadas uma a uma contra o código real):
  • `AND b.dono = $2` removido do DELETE            → apaga aposta de outro dono
  • `if confirmar != len(alvo)` removido            → apaga com o número errado
  • dedup dos ids (`set`) removido                  → id repetido exige número inflado
  • INSERT na lixeira trocado por DELETE puro       → nada vai para a lixeira
  • `raise HTTPException` da rota removido          → recusa vira 200 silencioso

O QUE ESTES TESTES **NÃO** COBREM:
  • o SQL real no Postgres (CTE com DELETE + INSERT; coberto pela forma, não executado);
  • o modal `shConfirm` e o botão da barra (tela; conferidos no navegador).
"""
import asyncio
import json
import sys
from unittest.mock import patch

import pytest
from fastapi import HTTPException

sys.path.insert(0, "app")

import main  # noqa: E402
import repository  # noqa: E402


class _FakeConn:
    def __init__(self, bilhetes):
        self.bilhetes = bilhetes
        self.lixeira = []
        self.execs = []

    async def execute(self, sql, *a):
        self.execs.append((sql, a))
        assert "DELETE FROM bilhetes" in sql and "INSERT INTO lixeira_bilhetes" in sql, \
            "snapshot e DELETE precisam ser a MESMA instrução"
        assert "to_jsonb" in sql
        ids, dono, motivo = a
        filtra_dono = "b.dono = $2" in sql
        fica, sai = [], []
        for b in self.bilhetes:
            alvo = b["id"] in ids and (b["dono"] == dono or not filtra_dono)
            (sai if alvo else fica).append(b)
        self.bilhetes[:] = fica
        for b in sai:
            self.lixeira.append({"dono": b["dono"], "motivo": motivo,
                                 "bilhete": json.loads(json.dumps(b))})
        return f"INSERT 0 {len(sai)}"


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


def _bilhete(bid, dono="Gabriel", tipster="Araujo"):
    return {"id": bid, "dono": dono, "casa": "Bet365", "parceiro": "Gabriel [Eu]",
            "tipster": tipster, "stake": "100,00", "odd": "1,90", "resultado": "W"}


def _excluir(bilhetes, ids, confirmar, dono="Gabriel"):
    conn = _FakeConn(bilhetes)
    # patch como CONTEXTO: no CI o `test_repository_db.py` usa o `get_pool` de verdade.
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))):
        res = asyncio.run(repository.excluir_bilhetes_lote(ids, dono, confirmar))
    return res, conn


# ── Escopo ────────────────────────────────────────────────────────────────────

def test_move_a_selecao_para_a_lixeira():
    base = [_bilhete(1), _bilhete(2), _bilhete(3, tipster="")]
    res, conn = _excluir(base, [1, 2], 2)
    assert res == {"ok": True, "excluidos": 2, "ignorados": 0, "total": 2}
    assert [b["id"] for b in base] == [3], "ficou o que não foi selecionado"
    assert [x["bilhete"]["id"] for x in conn.lixeira] == [1, 2]
    assert conn.lixeira[0]["bilhete"]["odd"] == "1,90", "snapshot perdeu coluna"
    assert "exclusão em massa" in conn.lixeira[0]["motivo"]


def test_id_de_outro_dono_nao_sai_e_volta_em_ignorados():
    alheia = _bilhete(9, dono="Feca")
    base = [_bilhete(1), alheia]
    res, conn = _excluir(base, [1, 9], 2)
    assert res["excluidos"] == 1 and res["ignorados"] == 1
    assert alheia in base, "vazou escopo: apagou aposta de outro dono"
    assert all(x["dono"] == "Gabriel" for x in conn.lixeira)


# ── Confirmação ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("confirmar", [0, 1, 3, 42045])
def test_numero_errado_nao_apaga_nada(confirmar):
    base = [_bilhete(1), _bilhete(2)]
    res, conn = _excluir(base, [1, 2], confirmar)
    assert res["ok"] is False
    assert len(base) == 2
    assert conn.execs == [], "escreveu mesmo sem a confirmação bater"


def test_id_repetido_conta_uma_vez():
    # O número que o usuário vê é o de APOSTAS, não o de entradas na lista.
    base = [_bilhete(1), _bilhete(2)]
    res, _ = _excluir(base, [1, 2, 2, 1], 2)
    assert res["ok"] is True and res["excluidos"] == 2


def test_lista_vazia_nao_apaga_nada():
    base = [_bilhete(1)]
    res, conn = _excluir(base, [], 0)
    assert res["ok"] is False
    assert conn.execs == []


# ── Rota ──────────────────────────────────────────────────────────────────────

def _rota(ids, confirmar, retorno):
    chamadas = []

    async def _fake(i, d, c):
        chamadas.append((i, d, c))
        return retorno

    with patch.object(main, "excluir_bilhetes_lote", _fake), \
         patch.object(main.matcher, "invalidar", lambda d: chamadas.append(("inv", d))):
        body = main.ExcluirLoteRequest(ids=ids, confirmar=confirmar)
        res = asyncio.run(main.excluir_bilhetes_lote_route(body, dono="Gabriel"))
    return res, chamadas


def test_rota_recusa_com_400_quando_o_repositorio_recusa():
    with pytest.raises(HTTPException) as e:
        _rota([1, 2], 3, {"ok": False, "motivo": "O número digitado não confere."})
    assert e.value.status_code == 400


def test_rota_passa_o_dono_da_sessao_e_invalida_o_matcher():
    res, chamadas = _rota([1, 2], 2, {"ok": True, "excluidos": 2, "ignorados": 0, "total": 2})
    assert chamadas[0] == ([1, 2], "Gabriel", 2)
    assert ("inv", "Gabriel") in chamadas
    assert res["excluidos"] == 2
