"""Configuração dos testes.

Por padrão (sem TEST_DATABASE_URL) torna o pacote `app/` importável e injeta stubs de
`asyncpg` e `database` antes de importar `repository` (que faz `import asyncpg` e
`from database import get_pool` no topo). Assim os testes de fórmula PURA não dependem de
Postgres — nenhuma função pura abre conexão; os stubs nunca são exercidos de fato.

Quando `TEST_DATABASE_URL` está setado (só no CI, contra um Postgres de TESTE local —
NUNCA produção), os stubs são PULADOS: `asyncpg`/`database` reais carregam e o harness de
camada-DB (`tests/test_repository_db.py`) exerce `upsert_bilhetes` + queries por dono de
verdade. Gatear em `TEST_DATABASE_URL` (e não em `DATABASE_URL`) é deliberado: o ambiente do
Feca tem `DATABASE_URL` de produção no `.env`, então gatear ali arriscaria rodar TRUNCATE em
prod. `TEST_DATABASE_URL` nunca existe fora do CI.
"""
import os
import pathlib
import sys
import types

APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

if not os.environ.get("TEST_DATABASE_URL"):
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

        async def init_db():  # pragma: no cover - importado por main, nunca chamado nos testes
            raise RuntimeError("DB indisponível nos testes de fórmula")

        _fake_db.get_pool = get_pool
        _fake_db.init_db = init_db
        sys.modules["database"] = _fake_db
