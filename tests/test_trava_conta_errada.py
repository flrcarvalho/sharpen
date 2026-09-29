"""Trava de captura na conta ERRADA (s388) — `/captura/enviar` recusa lote de outra conta.

Capturar com a conta X pareada e a casa logada na Y gravava o histórico de Y dentro de X,
sem erro. Quatro vezes medidas (s266, s267, s370, s388), sempre consertadas à mão. O sinal
é o código, único na casa: se a MAIORIA dos códigos do lote já mora noutra conta do mesmo
dono e casa, o lote é daquela conta.

Aqui a rota roda de verdade (TestClient) e só a consulta ao banco é dublada. A SQL em si é
testada contra o Postgres em `test_repository_db.py`
(`test_codigos_em_outra_conta_so_conta_o_que_esta_la_e_nao_aqui`).

O QUE ESTE ARQUIVO NÃO COBRE:
  · a 1ª captura da conta Y (Y sem nada gravado) — limite do desenho, não do teste;
  · o que a extensão MOSTRA no 409: até a 0.7.33 ela exibe texto fixo e ignora o detalhe.
"""
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import main  # noqa: E402

cliente = TestClient(main.app)


def _lote(*codigos):
    return "\n\n".join(f"[Código: {c}]\nStake: 10,00\nStatus: lost" for c in codigos)


@pytest.fixture
def sessao():
    s = main._captura.criar_sessao("Feca", "Superbet", "SUPERBET", "mamapaul03 [Richard]")
    main._captura.conectar(s.codigo)
    yield s
    main._captura._SESSOES.pop(s.sessao_id, None)


@pytest.fixture
def consulta(monkeypatch):
    """Duble da consulta ao banco: devolve `resposta` e guarda os argumentos."""
    estado = {"resposta": {}, "chamadas": [], "explode": False}

    async def fake(codigos, dono, casa, parceiro):
        estado["chamadas"].append((list(codigos), dono, casa, parceiro))
        if estado["explode"]:
            raise RuntimeError("banco fora")
        return estado["resposta"]

    monkeypatch.setattr(main, "codigos_em_outra_conta", fake)
    return estado


def _enviar(sess, texto, **extra):
    return cliente.post("/captura/enviar", data={
        "token": sess.token_ext, "tipo": "texto", "texto": texto, **extra})


# ── a regra ───────────────────────────────────────────────────────────────────

def test_regra_recusa_quando_a_maioria_e_de_outra_conta():
    assert main._conta_errada(73, {"erick_vilanova [Annderson]": 73}) == (
        "erick_vilanova [Annderson]", 73)                        # s388
    assert main._conta_errada(235, {"BrunnoAD [Fatuch]": 229}) == ("BrunnoAD [Fatuch]", 229)


def test_regra_minoria_passa():
    # germano/Bet365 (28/09): 4 de 11 num lote, herança de captura errada antiga. Ali o lote
    # é da conta que capturou; recusar impediria justamente a captura certa.
    assert main._conta_errada(11, {"Pkessia [Gustavo]": 4}) is None
    # metade exata não é maioria
    assert main._conta_errada(10, {"Y": 5}) is None
    assert main._conta_errada(0, {"Y": 5}) is None
    assert main._conta_errada(10, {}) is None


def test_regra_nomeia_a_conta_com_mais_codigos():
    assert main._conta_errada(10, {"A": 2, "B": 7, "C": 1}) == ("B", 7)


# ── a rota ────────────────────────────────────────────────────────────────────

def test_lote_de_outra_conta_e_recusado_e_nao_entra_na_fila(sessao, consulta):
    consulta["resposta"] = {"erick_vilanova [Annderson]": 3}
    r = _enviar(sessao, _lote("8901-QI5X14", "8903-QIOGN6", "890C-QDA7XO"))
    assert r.status_code == 409
    detalhe = r.json()["detail"]
    assert "erick_vilanova [Annderson]" in detalhe and "3 de 3" in detalhe
    assert sessao.capturas == []              # nada foi para a fila do dashboard


def test_a_consulta_usa_a_conta_da_SESSAO_e_os_codigos_do_texto(sessao, consulta):
    _enviar(sessao, _lote("AAA-1", "BBB-2"))
    assert consulta["chamadas"] == [
        (["AAA-1", "BBB-2"], "Feca", "Superbet", "mamapaul03 [Richard]")]


def test_lote_da_propria_conta_entra(sessao, consulta):
    consulta["resposta"] = {"erick_vilanova [Annderson]": 1}   # minoria
    r = _enviar(sessao, _lote("A-1", "A-2", "A-3"))
    assert r.status_code == 200
    assert len(sessao.capturas) == 1


def test_consulta_que_falha_nao_derruba_a_captura(sessao, consulta):
    consulta["explode"] = True
    r = _enviar(sessao, _lote("A-1"))
    assert r.status_code == 200
    assert len(sessao.capturas) == 1


def test_texto_sem_marcador_nem_consulta_o_banco(sessao, consulta):
    r = _enviar(sessao, "bilhete colado à mão, sem código")
    assert r.status_code == 200
    assert consulta["chamadas"] == []
