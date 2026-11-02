"""Kalshi (s439): a chave cifrada, a tradução da Caixa e as rotas, sem Postgres.

Fixture da Caixa: o depósito REAL do recon de 30/10/2026 (`/portfolio/deposits` da conta do
Feca), byte a byte: `amount_cents` 29963, `created_ts` 1793298479, `fee_cents` 0.

As rotas rodam com um pool DUBLÊ (`_Pool`) que registra cada SQL: o que se confere aqui é
o que a rota MANDA ao banco e o que ela DEVOLVE à tela, nunca o efeito no banco. O efeito
(Caixa projetada contra o saldo, índice de `ref`, CASCADE) está em `test_repository_db.py`.

Não cobre: a Kalshi de verdade (a rede é dublada), o formato do saque (nunca visto; a
regra é levantar sem os campos do depósito) e taxa de depósito diferente de zero (o sync
só avisa). A tela está em `index.html` e foi conferida por render, não por teste.

Mutação (01/11/2026, junto com o teste de banco): 11 aplicadas, 11 detectadas. A do fuso
(data em UTC) escapou na 1ª rodada: o depósito real cai às 15:27 de Brasília, mesmo dia nos
dois fusos. Daí o caso que cruza a meia-noite.
"""
import asyncio
from datetime import datetime, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient

import kalshi
import kalshi_rotas as kr

PEM_FALSO = "-----BEGIN PRIVATE KEY-----\nMC4CAQAwBQYDK2VwBCIEIA==\n-----END PRIVATE KEY-----\n"
KEY_ID = "55bd53ea-6b28-4d31-b9a1-0d8c52eb45d6"
DEPOSITO_REAL = {"amount_cents": 29963, "created_ts": 1793298479, "fee_cents": 0,
                 "finalized_ts": 1793298479, "id": "01a188eb-6066-7116-8f93-37fdfa2b842e",
                 "status": "applied", "type": "crypto"}


# ── Cifra ────────────────────────────────────────────────────────────────────

def test_cifra_ida_e_volta_e_o_texto_cifrado_nao_contem_a_chave():
    seg = Fernet.generate_key().decode()
    tok = kr.cifrar(PEM_FALSO, seg)
    assert "PRIVATE KEY" not in tok
    assert kr.decifrar(tok, seg) == PEM_FALSO


@pytest.mark.parametrize("seg", [None, "", "   ", "nao-e-uma-chave-fernet"])
def test_sem_segredo_valido_nada_entra(seg):
    with pytest.raises(kr.CifraAusente):
        kr.cifrar(PEM_FALSO, seg)


def test_segredo_trocado_nao_abre_a_chave_guardada():
    tok = kr.cifrar(PEM_FALSO, Fernet.generate_key().decode())
    with pytest.raises(kr.CifraAusente):
        kr.decifrar(tok, Fernet.generate_key().decode())


def test_a_tela_so_ve_o_comeco_do_id():
    assert kr.prefixo_key_id(KEY_ID) == "55bd53ea…"
    assert KEY_ID not in kr.prefixo_key_id(KEY_ID)


# ── Caixa: depósitos e saques ────────────────────────────────────────────────

def test_deposito_real_vira_lancamento_em_dolar_com_ref_estavel():
    movs, alertas = kalshi.movimentos_caixa([DEPOSITO_REAL], [])
    assert alertas == []
    # 1793298479 = 29/10/2026 18:27:59 UTC = 15:27:59 em Brasília.
    assert movs == [{"tipo": "deposito", "data": "2026-10-29", "valor": 299.63,
                     "ref": "kalshi:deposito:01a188eb-6066-7116-8f93-37fdfa2b842e",
                     "obs": "Automático: depósito lido da conta Kalshi"}]


def test_data_do_movimento_e_a_de_brasilia_mesmo_cruzando_a_meia_noite():
    # 1793325600 = 30/10/2026 02:00 UTC = 29/10/2026 23:00 em Brasília.
    movs, _ = kalshi.movimentos_caixa([{**DEPOSITO_REAL, "created_ts": 1793325600}], [])
    assert movs[0]["data"] == "2026-10-29"


def test_so_movimento_aplicado_entra():
    pend = {**DEPOSITO_REAL, "status": "pending", "id": "x"}
    movs, _ = kalshi.movimentos_caixa([DEPOSITO_REAL, pend], [])
    assert [m["ref"] for m in movs] == ["kalshi:deposito:" + DEPOSITO_REAL["id"]]


def test_saque_usa_o_mesmo_formato_e_sai_como_saque():
    saq = {**DEPOSITO_REAL, "id": "s1", "amount_cents": 5000}
    movs, _ = kalshi.movimentos_caixa([], [saq])
    assert movs[0]["tipo"] == "saque" and movs[0]["valor"] == 50.0
    assert movs[0]["ref"] == "kalshi:saque:s1"


@pytest.mark.parametrize("falta", ["amount_cents", "created_ts", "id"])
def test_formato_nao_medido_levanta_em_vez_de_chutar_a_unidade(falta):
    saq = {k: v for k, v in DEPOSITO_REAL.items() if k != falta}
    with pytest.raises(kalshi.KalshiErro):
        kalshi.movimentos_caixa([], [saq])


def test_valor_em_dolar_string_nao_e_lido_como_centavos():
    """`amount` em dólar (string) é outra unidade: sem `amount_cents` inteiro, levanta."""
    dep = {k: v for k, v in DEPOSITO_REAL.items() if k != "amount_cents"}
    dep["amount_cents"] = "299.63"
    with pytest.raises(kalshi.KalshiErro):
        kalshi.movimentos_caixa([dep], [])


def test_taxa_de_deposito_nao_medida_avisa():
    movs, alertas = kalshi.movimentos_caixa([{**DEPOSITO_REAL, "fee_cents": 150}], [])
    assert movs[0]["valor"] == 299.63
    assert len(alertas) == 1 and "1,50" in alertas[0]


# ── Aviso de tradução faltando ───────────────────────────────────────────────

def test_aviso_nomeia_tag_e_escopo_sem_mapa():
    assert kr.alerta_nao_mapeado({"tags": [], "escopos": []}) is None
    a = kr.alerta_nao_mapeado({"tags": ["Hockey"], "escopos": ["Player Points"]})
    assert "Hockey" in a and "Player Points" in a


# ── Rotas, com pool dublê ────────────────────────────────────────────────────

class _Conn:
    def __init__(self, pool):
        self.pool = pool

    async def fetchrow(self, sql, *a):
        self.pool.sql.append(sql)
        if "FROM parceiros" in sql:
            return self.pool.conta
        if "FROM kalshi_chave" in sql:
            return self.pool.chave
        return None

    async def execute(self, sql, *a):
        self.pool.sql.append(sql)
        self.pool.args.append(a)
        return "UPDATE 0"


class _Acq:
    def __init__(self, pool):
        self.pool = pool

    async def __aenter__(self):
        return _Conn(self.pool)

    async def __aexit__(self, *e):
        return False


class _Pool:
    def __init__(self, conta=None, chave=None):
        self.conta, self.chave, self.sql, self.args = conta, chave, [], []

    def acquire(self):
        return _Acq(self)


CONTA = {"id": 7, "casa": "Kalshi", "nome": "Feca [Eu]", "moeda": "BRL"}


@pytest.fixture
def cliente(monkeypatch):
    pool = _Pool(conta=CONTA)

    async def _gp():
        return pool

    monkeypatch.setattr(kr, "get_pool", _gp)
    app = FastAPI()
    app.include_router(kr.router)
    app.dependency_overrides[kr.usuario_atual] = lambda: "Feca"
    return TestClient(app), pool


def test_get_da_chave_nunca_devolve_a_chave(cliente):
    tc, pool = cliente
    pool.chave = {"key_id": KEY_ID, "pem_cifrado": "SEGREDO-CIFRADO",
                  "conferida_em": datetime(2026, 11, 1, tzinfo=timezone.utc), "ultimo_sync": None}
    r = tc.get("/kalshi/chave", params={"parceiro": "Feca [Eu]"})
    assert r.status_code == 200
    corpo = r.text
    assert KEY_ID not in corpo and "SEGREDO-CIFRADO" not in corpo and "pem" not in corpo
    assert r.json()["tem"] is True and r.json()["key_id"] == "55bd53ea…"
    # A consulta nem lê a coluna cifrada.
    assert not any("pem_cifrado" in s for s in pool.sql if "SELECT" in s)


def test_conta_sem_chave(cliente):
    tc, pool = cliente
    assert tc.get("/kalshi/chave", params={"parceiro": "Feca [Eu]"}).json() == {"tem": False}


def test_conta_de_outra_casa_ou_inexistente_e_404(cliente):
    tc, pool = cliente
    pool.conta = None
    assert tc.get("/kalshi/chave", params={"parceiro": "x"}).status_code == 404


def test_chave_que_pode_operar_e_recusada_e_nao_e_gravada(cliente, monkeypatch):
    tc, pool = cliente
    monkeypatch.setenv(kr.ENV_CIFRA, Fernet.generate_key().decode())
    monkeypatch.setattr(kr.kalshi, "Credencial", lambda k, p: type("C", (), {"key_id": k})())

    async def _recusa(client, cred):
        raise kalshi.KalshiChaveInvalida("Esta chave pode operar na sua conta.")

    monkeypatch.setattr(kr.kalshi, "conferir_chave", _recusa)
    r = tc.post("/kalshi/chave", json={"parceiro": "Feca [Eu]", "key_id": KEY_ID, "pem": PEM_FALSO})
    assert r.status_code == 400 and "operar" in r.json()["detail"]
    assert not any("INSERT" in s for s in pool.sql)


def test_chave_aceita_vai_cifrada_ao_banco(cliente, monkeypatch):
    tc, pool = cliente
    seg = Fernet.generate_key().decode()
    monkeypatch.setenv(kr.ENV_CIFRA, seg)
    monkeypatch.setattr(kr.kalshi, "Credencial", lambda k, p: type("C", (), {"key_id": k})())

    async def _ok(client, cred):
        return None

    monkeypatch.setattr(kr.kalshi, "conferir_chave", _ok)
    r = tc.post("/kalshi/chave", json={"parceiro": "Feca [Eu]", "key_id": KEY_ID, "pem": PEM_FALSO})
    assert r.status_code == 200 and r.json() == {"tem": True, "key_id": "55bd53ea…"}
    (args,) = pool.args                      # um execute só: o INSERT da chave
    pid, dono, key_id, cifrado = args
    assert (pid, dono, key_id) == (7, "Feca", KEY_ID)
    assert "PRIVATE KEY" not in cifrado and kr.decifrar(cifrado, seg) == PEM_FALSO


def test_sem_segredo_no_servidor_a_chave_nao_entra(cliente, monkeypatch):
    tc, pool = cliente
    monkeypatch.delenv(kr.ENV_CIFRA, raising=False)
    monkeypatch.setattr(kr.kalshi, "Credencial", lambda k, p: type("C", (), {"key_id": k})())

    async def _ok(client, cred):
        return None

    monkeypatch.setattr(kr.kalshi, "conferir_chave", _ok)
    r = tc.post("/kalshi/chave", json={"parceiro": "Feca [Eu]", "key_id": KEY_ID, "pem": PEM_FALSO})
    assert r.status_code == 503
    assert not any("INSERT" in s for s in pool.sql)


def test_sync_sem_chave_pede_para_conectar(cliente):
    tc, pool = cliente
    r = tc.post("/kalshi/sync", json={"parceiro": "Feca [Eu]"})
    assert r.status_code == 409 and "Conecte" in r.json()["detail"]


def test_ensaio_le_e_nao_grava_nada(cliente, monkeypatch):
    tc, pool = cliente
    seg = Fernet.generate_key().decode()
    monkeypatch.setenv(kr.ENV_CIFRA, seg)
    pool.chave = {"key_id": KEY_ID, "pem_cifrado": kr.cifrar(PEM_FALSO, seg)}
    monkeypatch.setattr(kr.kalshi, "Credencial", lambda k, p: object())
    linha = {"_sort": ("2026-10-29", ""), "codigo_bilhete": "o1", "stake": "100,00"}

    async def _coletar(cred, parceiro):
        return {"linhas": [linha], "alertas": [], "nao_mapeado": {"tags": [], "escopos": []},
                "caixa": {"saldo": 279.6515, "inicio": "2026-10-29", "movimentos": [{}]}}

    async def _nunca(*a, **k):
        raise AssertionError("o ensaio não pode gravar")

    monkeypatch.setattr(kr.kalshi, "coletar", _coletar)
    monkeypatch.setattr(kr, "upsert_bilhetes", _nunca)
    monkeypatch.setattr(kr, "caixa_kalshi_sync", _nunca)
    r = tc.post("/kalshi/sync", json={"parceiro": "Feca [Eu]", "ensaio": True})
    assert r.status_code == 200
    d = r.json()
    assert d["ensaio"] is True and d["coletados"] == 1
    assert d["linhas"] == [{"codigo_bilhete": "o1", "stake": "100,00"}]   # sem o `_sort`
    assert d["caixa"]["movimentos"] == 1
    assert not any(s.lstrip().startswith(("INSERT", "UPDATE", "DELETE")) for s in pool.sql)
