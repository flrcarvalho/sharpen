"""A sidebar (`resumo_perfil`) lê a freebet como o feed lê (s405).

O defeito: o SELECT de `resumo_perfil` não trazia `stake_freebet`, então a sidebar
cobrava cada freebet perdida inteira enquanto o feed ao lado dava 0 (`MASTER_RESULTADO
§5.8`). Medido em outubro/2026: −R$ 668,78 no Feca e −R$ 271,83 no Gabriel.

O banco é dublado por uma conexão que devolve SÓ as colunas que o SELECT pediu: é isso
que reproduz o defeito. Uma dublê que devolvesse o dict inteiro passaria verde com a
coluna fora da query.

Prova por mutação (s405): tirar `stake_freebet` do SELECT derruba os dois testes.

O que NÃO cobre: o recorte do mês por data do evento (múltipla liquidada antes da última
perna fica datada no futuro; é outra frente) e o SQL rodando de verdade no Postgres.
"""
import asyncio
import re
import sys
from datetime import date

sys.path.insert(0, "app")
import repository  # noqa: E402

_LINHAS = [
    # freebet INTEIRA perdida: P/L 0 e fora do turnover (§5.8)
    {"stake": "45,00", "odd": "10,0", "resultado": "L", "data": "07/10/2026", "stake_freebet": 45},
    # aposta comum ganha
    {"stake": "100,00", "odd": "2,0", "resultado": "W", "data": "2026-10-05", "stake_freebet": None},
]


class _Conn:
    async def fetch(self, sql, *args):
        cols = [c.strip() for c in re.search(r"SELECT (.*?) FROM", sql, re.S).group(1).split(",")]
        return [{c: l.get(c) for c in cols} for l in _LINHAS]


class _Acq:
    async def __aenter__(self):
        return _Conn()

    async def __aexit__(self, *a):
        return False


class _Pool:
    def acquire(self):
        return _Acq()


def _resumo(monkeypatch):
    async def _pool():
        return _Pool()
    monkeypatch.setattr(repository, "get_pool", _pool)
    return asyncio.run(repository.resumo_perfil(["x"], hoje=date(2026, 10, 9)))


def test_freebet_perdida_nao_custa_nada_na_sidebar(monkeypatch):
    r = _resumo(monkeypatch)
    assert r["mes"]["pl"] == 100.0          # sem a coluna: 100 − 45 = 55
    assert r["historico"]["pl"] == 100.0


def test_freebet_fica_fora_do_turnover_da_sidebar(monkeypatch):
    r = _resumo(monkeypatch)
    assert r["mes"]["turnover"] == 100.0    # sem a coluna: 145
    assert r["mes"]["roi"] == 100.0
