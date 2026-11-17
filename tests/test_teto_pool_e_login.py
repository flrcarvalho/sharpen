"""Tetos de espera e CPU fora do event loop (s459, auditoria de 17/11, ESCALA A3 e A5).

1. Toda espera por conexão do pool tem prazo (`database._PoolComTeto`). Sem prazo, uma
   consulta parada num lock prendia as 5 conexões e o Sharpen inteiro girava sem fim, com
   o `/healthz` respondendo 200.
2. O bcrypt do login roda numa thread. No event loop, cada login (~0,4 s de CPU) travava
   todos os outros usuários.

Prova de comportamento, sem banco: o pool é dublado (só registra o prazo que recebeu) e o
`resultado_login` é trocado por um espião que diz se rodou dentro de um event loop.

O que NÃO está coberto: os valores de `statement_timeout`/`lock_timeout` no servidor, que
o harness de DB (`tests/test_repository_db.py`) mede contra um Postgres real.
"""
import asyncio
import importlib.util
from pathlib import Path

# O conftest troca `database` por um dublê quando não há Postgres de teste; aqui carregamos o
# arquivo REAL sob outro nome, sem passar pelo sys.modules dele.
_SPEC = importlib.util.spec_from_file_location(
    "database_real_s459", Path(__file__).resolve().parent.parent / "app" / "database.py")
database = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(database)


class _PoolDublado:
    def __init__(self):
        self.prazos = []

    def acquire(self, *, timeout=None):
        self.prazos.append(timeout)
        return "ctx"

    def get_size(self):
        return 5


def test_acquire_sem_prazo_ganha_o_teto():
    dub = _PoolDublado()
    p = database._PoolComTeto(dub)
    p.acquire()
    assert dub.prazos == [database.POOL_ACQUIRE_TIMEOUT]
    assert database.POOL_ACQUIRE_TIMEOUT and database.POOL_ACQUIRE_TIMEOUT > 0


def test_prazo_explicito_manda():
    dub = _PoolDublado()
    database._PoolComTeto(dub).acquire(timeout=3)
    assert dub.prazos == [3]


def test_o_resto_do_pool_continua_acessivel():
    assert database._PoolComTeto(_PoolDublado()).get_size() == 5


def test_servidor_recebe_teto_de_comando_e_de_lock():
    s = database.POOL_SERVER_SETTINGS
    assert s.get("statement_timeout") and s.get("lock_timeout")


def test_login_roda_o_bcrypt_fora_do_event_loop(monkeypatch):
    from fastapi.testclient import TestClient
    import main

    rodou = {}

    def espiao(usuario, senha):
        try:
            asyncio.get_running_loop()
            rodou["no_loop"] = True
        except RuntimeError:
            rodou["no_loop"] = False
        return "invalido"

    monkeypatch.setattr(main, "resultado_login", espiao)
    main._login_fails.clear()
    r = TestClient(main.app).post("/login", json={"usuario": "x", "senha": "y"})
    assert r.status_code == 401
    assert rodou == {"no_loop": False}, "o bcrypt do login voltou para dentro do event loop"
