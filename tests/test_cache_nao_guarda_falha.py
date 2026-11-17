"""Cache não guarda o ramo de ERRO (s459, auditoria de 17/11, SERVIDOR P5).

`categorias_do_dono` guardava por 10 min o conjunto montado quando o banco falhou (só o
Master), e o leitor recusava as categorias da base do dono (Especiais, Aumentadas) muito
depois de o banco ter voltado. Roteiro do auditor: banco cai, banco volta, a categoria da
base tem de aparecer na chamada seguinte.
"""
import asyncio

import repository as R


class _Conn:
    async def fetch(self, *_a):
        return [{"aposta": "Especiais"}]


class _Acq:
    async def __aenter__(self):
        return _Conn()

    async def __aexit__(self, *a):
        return False


class _Pool:
    def acquire(self):
        return _Acq()


def test_falha_do_banco_nao_fica_no_cache(monkeypatch):
    R._CATEGORIAS_DONO.clear()
    estado = {"fora": True}

    async def get_pool():
        if estado["fora"]:
            raise RuntimeError("banco fora")
        return _Pool()

    monkeypatch.setattr(R, "get_pool", get_pool)
    assert "Especiais" not in asyncio.run(R.categorias_do_dono("TDonoCat"))
    estado["fora"] = False
    assert "Especiais" in asyncio.run(R.categorias_do_dono("TDonoCat")), \
        "o resultado da falha ficou no cache depois de o banco voltar"
    R._CATEGORIAS_DONO.clear()
