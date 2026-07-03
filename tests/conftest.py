"""Configuração dos testes de fórmula.

Torna o pacote `app/` importável e evita depender de Postgres/asyncpg só para
testar as fórmulas PURAS: injeta stubs de `asyncpg` e `database` antes de importar
`repository` (que faz `import asyncpg` e `from database import get_pool` no topo).
Nenhuma função testada abre conexão — os stubs nunca são exercidos de fato.
"""
import pathlib
import sys
import types

APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

# Stub de asyncpg: só precisamos do nome do módulo e de UniqueViolationError
# (referenciado em repository.upsert_bilhetes, não exercido nos testes de fórmula).
if "asyncpg" not in sys.modules:
    _fake_pg = types.ModuleType("asyncpg")

    class _UniqueViolationError(Exception):
        pass

    _fake_pg.UniqueViolationError = _UniqueViolationError
    sys.modules["asyncpg"] = _fake_pg

# Stub de database: repository importa get_pool no topo; nenhum teste de fórmula o chama.
if "database" not in sys.modules:
    _fake_db = types.ModuleType("database")

    async def get_pool():  # pragma: no cover - nunca chamado nos testes de fórmula
        raise RuntimeError("DB indisponível nos testes de fórmula")

    _fake_db.get_pool = get_pool
    sys.modules["database"] = _fake_db
