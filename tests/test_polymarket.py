"""Polymarket — confiabilidade de saldo (#47) e cálculo de odd.

Guarda o fix: quando TODOS os RPCs públicos caem, `_rpc_balance` devolve None
(indisponível), NUNCA 0.0 (que mentiria "carteira vazia"). polymarket.py só usa
stdlib + httpx (sem asyncpg/database), então importa direto.
"""
import asyncio

import polymarket


class _Down:
    async def post(self, *a, **k):
        raise Exception("rpc down")


class _Ok:
    async def post(self, *a, **k):
        class R:
            def json(self_inner):
                return {"result": "0x" + format(5_000_000, "x").rjust(64, "0")}
        return R()


def test_rpc_balance_none_quando_todos_rpcs_caem():
    got = asyncio.run(polymarket._rpc_balance(_Down(), polymarket._PUSD, "0x" + "0" * 40))
    assert got is None   # indisponível — NÃO 0.0


def test_rpc_balance_valor_quando_responde():
    got = asyncio.run(polymarket._rpc_balance(_Ok(), polymarket._PUSD, "0x" + "0" * 40))
    assert got == 5.0    # 5_000_000 / 1e6 (6 casas)


def test_calc_odd_e_sempre_payout_ratio():
    # Uma odd pra tudo = 1/preço (retorno/investimento), independente de ganhar/perder
    # e IGNORANDO o cashPnl (que carrega taxa). Preço 0,40 → 2,5.
    assert abs(polymarket._calc_odd({"avgPrice": 0.40, "cashPnl": 60.0}) - 2.5) < 1e-9    # vencedora
    assert abs(polymarket._calc_odd({"avgPrice": 0.40, "cashPnl": -40.0}) - 2.5) < 1e-9   # perdedora
    # Lucro com taxa (55, não 60) NÃO altera a odd — é a limpa 1/preço:
    assert abs(polymarket._calc_odd({"initialValue": 40.0, "cashPnl": 55.0, "avgPrice": 0.40}) - 2.5) < 1e-9


def test_calc_odd_sem_preco_valido_cai_em_1():
    assert polymarket._calc_odd({"avgPrice": 0}) == 1.0
    assert polymarket._calc_odd({"avgPrice": 1.5}) == 1.0
