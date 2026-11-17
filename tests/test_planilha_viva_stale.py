"""Planilha ao vivo fora do ar não vira número velho com cara de atual (s459, SERVIDOR P9).

O cache velho cobria a queda para sempre: 3 dias depois, fonte fora, `refresh=1` ainda devolvia
o feed antigo sem erro, e a tela carimbava "último sync" de agora. Agora ele cobre só uma queda
curta (`_STALE_MAX_SEGUNDOS`); depois disso a falha sobe.
"""
import asyncio

import pytest

import planilha_viva as pv


class _Cliente:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, url):
        raise RuntimeError("planilha fora do ar")


def test_queda_curta_usa_o_cache_e_longa_aparece(monkeypatch):
    relogio = {"t": 10_000.0}
    monkeypatch.setattr(pv.time, "monotonic", lambda: relogio["t"])
    monkeypatch.setattr(pv.httpx, "AsyncClient", _Cliente)
    pv._cache["TDonoPV"] = (relogio["t"], [{"id": 1}])
    relogio["t"] += 600                                        # 10 min: cobre
    assert asyncio.run(pv.dashboard_rows_ao_vivo("TDonoPV", "http://x", refresh=True)) == [{"id": 1}]
    relogio["t"] += 3 * 86400                                  # 3 dias: não cobre mais
    with pytest.raises(RuntimeError):
        asyncio.run(pv.dashboard_rows_ao_vivo("TDonoPV", "http://x", refresh=True))
    pv._cache.pop("TDonoPV", None)
