"""Edição em massa: o lote passa pelo MESMO miolo de uma edição só.

O atalho tentador é um `UPDATE bilhetes SET ... WHERE id = ANY($ids)`. Ele pula tudo o
que a edição de uma linha faz e que ninguém vê faltar:

  · a ASSINATURA (`casa`, `parceiro`, `data` e `aposta` estão em `_SIG_COLS`) — assinatura
    velha não dá erro, só faz a próxima captura da casa não deduplicar e duplicar o
    histórico inteiro (s198/s312). Num lote de 300 linhas é 300 vezes o mesmo defeito;
  · o `extraction_state` (resultado/odd mudam o estado da linha);
  · o `origem_tipster` (procedência do rótulo, Fase 0);
  · o registro em `correcoes`.

Guarda também a distinção que "campo vazio" sozinho não faz: campo AUSENTE = não mexe,
string VAZIA = limpa. Sem ela não há como apagar um tipster errado em massa, e um patch
com o campo presente e vazio apagaria dado que ninguém pediu para apagar.

NÃO cobre: que o Postgres aceite os tipos (conn é dublada — o asyncpg exige o tipo da
COLUNA, ver CLAUDE.md), nem concorrência real de assinatura. O caminho de uma linha só
já é coberto por `test_assinatura_edicao.py`; aqui o que se prova é que o lote NÃO
inventou um segundo caminho.
"""
import asyncio
from unittest.mock import patch

import repository

_A = repository._assinatura


class _FakeConn:
    """Conn de mentira com o mínimo que `_atualizar_bilhete_conn` usa."""

    def __init__(self, linhas):
        self.linhas = {l["id"]: dict(l) for l in linhas}
        self.updates = []      # [(id, {coluna: valor})] na ORDEM
        self.correcoes = []    # [(id, campo, antigo, novo)]

    async def fetchrow(self, _sql, bid, dono):
        linha = self.linhas.get(bid)
        if linha is None or linha.get("dono", dono) != dono:
            return None
        # CÓPIA, como o Record imutável do asyncpg. Devolver a referência viva faria o
        # UPDATE alterar o próprio snapshot "antes" — e `_correcoes_diff`, que compara os
        # dois, passaria a ver "nada mudou" em toda edição. O dublê mentiria sobre o
        # código, que é o modo de falso vermelho irmão do falso verde.
        return dict(linha)

    async def fetchval(self, sql, *a):
        if "NOT EXISTS" in sql:
            dono, casa, parceiro, sig, bid = a
            return not any(
                l["casa"] == casa and l["parceiro"] == parceiro
                and l["assinatura"] == sig and l["id"] != bid
                for l in self.linhas.values())
        if "flags" in sql:
            return None
        return None

    async def execute(self, sql, *a):
        if sql.startswith("INSERT INTO correcoes"):
            self.correcoes.append((a[0], a[3], a[4], a[5]))
            return "INSERT 0 1"
        # UPDATE bilhetes SET c1 = $1, c2 = $2, ..., atualizado_em = NOW()
        #        WHERE id = $n AND dono = $n+1
        cols = [p.split(" = ")[0].strip()
                for p in sql.split(" SET ", 1)[1].split(" WHERE ")[0].split(", ")
                if " = $" in p]
        bid, dono = a[-2], a[-1]
        linha = self.linhas.get(bid)
        if linha is None or linha.get("dono", dono) != dono:
            return "UPDATE 0"
        for col, val in zip(cols, a[:len(cols)]):
            linha[col] = val
        self.updates.append((bid, dict(zip(cols, a[:len(cols)]))))
        return "UPDATE 1"


class _FakePool:
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        conn = self.conn

        class _A_:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _A_()


def _linha(bid, **kw):
    b = dict(id=bid, casa="Bet365", parceiro="Feca [[Eu]]", data="14/07/2026",
             aposta="Gols", descricao=f"Over 2.5 [Jogo {bid}]", stake="210,00",
             odd="1,83", resultado="W", tipster="Peixe", esporte="Futebol",
             codigo_bilhete=None, extraction_state="resolvida", origem="captura")
    b.update(kw)
    b["assinatura"] = _A({**b, "codigo_bilhete": b["codigo_bilhete"] or ""})
    return b


def _lote(linhas, ids, campos, dono="Feca"):
    conn = _FakeConn(linhas)
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))), \
         patch.object(repository, "garantir_tipster",
                      lambda *a, **k: asyncio.sleep(0)):
        res = asyncio.run(repository.atualizar_bilhetes_lote(ids, campos, dono))
    return res, conn


# ── O lote toca TODAS as linhas, e cada uma pelo caminho completo ────────────

def test_aplica_o_mesmo_valor_a_todas():
    ls = [_linha(1), _linha(2), _linha(3)]
    res, conn = _lote(ls, [1, 2, 3], {"tipster": "Arrudex"})
    assert res["atualizados"] == 3 and res["ignorados"] == []
    assert all(conn.linhas[i]["tipster"] == "Arrudex" for i in (1, 2, 3))


def test_campo_fora_do_patch_nao_e_tocado():
    ls = [_linha(1, esporte="Tênis")]
    _, conn = _lote(ls, [1], {"tipster": "Arrudex"})
    assert conn.linhas[1]["esporte"] == "Tênis"
    assert "esporte" not in conn.updates[0][1]


def test_string_vazia_LIMPA_o_campo():
    # A distinção que o modal precisa ter: ausente = não mexe, vazio = apaga.
    ls = [_linha(1, tipster="Peixe")]
    _, conn = _lote(ls, [1], {"tipster": ""})
    assert conn.linhas[1]["tipster"] == ""
    # e a procedência do rótulo some junto: sem tipster não há rótulo humano.
    assert conn.updates[0][1]["origem_tipster"] is None


def test_linha_de_outro_dono_entra_em_ignorados_sem_derrubar_o_lote():
    # Tudo-ou-nada aqui trocaria 2 edições boas por zero. A resposta DIZ quem ficou fora.
    ls = [_linha(1), _linha(9, dono="Outro"), _linha(3)]
    res, conn = _lote(ls, [1, 9, 3], {"tipster": "Arrudex"})
    assert res["atualizados"] == 2 and res["ignorados"] == [9]
    assert res["total"] == 3
    assert conn.linhas[9]["tipster"] == "Peixe"


def test_id_inexistente_e_ignorado():
    res, _ = _lote([_linha(1)], [1, 404], {"esporte": "Tênis"})
    assert res["atualizados"] == 1 and res["ignorados"] == [404]


def test_sem_ids_ou_sem_campos_nao_escreve_nada():
    res, conn = _lote([_linha(1)], [], {"tipster": "X"})
    assert res["atualizados"] == 0 and conn.updates == []
    # `stake` não está na lista do lote, mas mesmo se chegasse seria filtrado por
    # `_campos_editaveis` — aqui o patch é inteiro de campo inválido.
    res2, conn2 = _lote([_linha(1)], [1], {"nao_existe": "x"})
    assert res2["atualizados"] == 0 and conn2.updates == []


# ── O que o UPDATE cru pularia ──────────────────────────────────────────────

def test_recalcula_a_ASSINATURA_de_cada_linha_do_lote():
    ls = [_linha(1), _linha(2)]
    velhas = {l["id"]: l["assinatura"] for l in ls}
    _, conn = _lote(ls, [1, 2], {"aposta": "Pontos"})
    for i in (1, 2):
        assert "assinatura" in conn.updates[i - 1][1], "assinatura ficou para trás no lote"
        assert conn.linhas[i]["assinatura"] != velhas[i]
        esperada = _A({**conn.linhas[i], "codigo_bilhete": ""})
        assert conn.linhas[i]["assinatura"] == esperada


def test_campo_fora_do_hash_nao_recalcula_assinatura():
    ls = [_linha(1)]
    velha = ls[0]["assinatura"]
    _, conn = _lote(ls, [1], {"tipster": "Arrudex"})
    assert conn.linhas[1]["assinatura"] == velha
    assert "assinatura" not in conn.updates[0][1]


def test_recalcula_o_extraction_state_quando_o_resultado_muda():
    ls = [_linha(1, resultado="", extraction_state="aberta")]
    _, conn = _lote(ls, [1], {"resultado": "W"})
    assert conn.linhas[1]["extraction_state"] == "resolvida"


def test_resultado_minusculo_vira_MAIUSCULO():
    # 'v' gravado assim ficava 'aberta' e a linha contava como "aguardando resultado".
    ls = [_linha(1, resultado="", extraction_state="aberta")]
    _, conn = _lote(ls, [1], {"resultado": "v"})
    assert conn.linhas[1]["resultado"] == "V"
    assert conn.linhas[1]["extraction_state"] == "resolvida"


def test_grava_origem_tipster_humano_no_lote():
    ls = [_linha(1)]
    _, conn = _lote(ls, [1], {"tipster": "Arrudex"})
    assert conn.updates[0][1]["origem_tipster"] == "humano"


def test_registra_correcoes_de_cada_linha():
    ls = [_linha(1), _linha(2)]
    _, conn = _lote(ls, [1, 2], {"tipster": "Arrudex"})
    campos = [(bid, campo, ant, novo) for bid, campo, ant, novo in conn.correcoes]
    assert (1, "tipster", "Peixe", "Arrudex") in campos
    assert (2, "tipster", "Peixe", "Arrudex") in campos


# ── flags_pos_edicao_lote: CONTAGEM, não booleano ───────────────────────────

class _FlagsConn:
    def __init__(self, sem_codigo, volatil):
        self.row = {"sem_codigo": sem_codigo, "volatil": volatil}
        self.chamadas = 0

    async def fetchrow(self, _sql, *_a):
        self.chamadas += 1
        return self.row


def _flags(ids, campos, sem_codigo=0, volatil=0):
    conn = _FlagsConn(sem_codigo, volatil)
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_FakePool(conn))):
        out = asyncio.run(repository.flags_pos_edicao_lote(ids, "Feca", campos))
    return out, conn


def test_flags_lote_devolve_quantas_e_nao_um_booleano():
    # "algumas podem ser desfeitas" sem dizer QUANTAS vira caça manual numa seleção
    # de 300 linhas — o mesmo defeito do contador sem ponte para a linha.
    out, _ = _flags([1, 2, 3], {"data"}, volatil=2)
    assert out == {"volatil": 2}
    out2, _ = _flags([1, 2, 3], {"aposta"}, sem_codigo=3)
    assert out2 == {"sem_codigo": 3}


def test_flags_lote_nao_consulta_quando_o_campo_nao_interessa():
    out, conn = _flags([1, 2], {"tipster", "esporte"}, volatil=9)
    assert out == {} and conn.chamadas == 0


def test_flags_lote_sem_ids_nao_consulta():
    out, conn = _flags([], {"data"}, volatil=9)
    assert out == {} and conn.chamadas == 0


def test_campos_volateis_incluem_a_data():
    # É o campo que o lote existe para mudar, e é justamente o que o robô desfaz em
    # linha ainda aberta. Se alguém tirar `data` daqui, o aviso some sem quebrar nada.
    assert "data" in repository._CAMPOS_VOLATEIS
