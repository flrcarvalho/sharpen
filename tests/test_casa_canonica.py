"""Casa nova não pode nascer gêmea de uma que já existe (s199).

`casa` é TEXTO em todas as tabelas, então cada grafia vira uma casa DIFERENTE — contas,
KPIs, filtros e favicon separados. "PixBet" (Feca) e "Pixbet" (Jonathan) conviveram meses
como duas casas, e ninguém via a divisão porque cada dono só enxerga a própria: foram 8
grupos e 358 bilhetes para unificar.

A trava casa por caixa/espaço com o que já existe e REUSA aquela grafia. O que ela NÃO
pode fazer é mexer em casa nova de verdade: title-casear ou comer espaço foi o bug da s141
("Rei do Pitaco" → "Rei Do Pitaco", "Esportiva Bet" → "Esportivabet"), que criava conta
paralela justamente por mutilar o nome.
"""
import asyncio
from unittest.mock import patch

import repository


class _Conn:
    def __init__(self, existentes):
        self.existentes = existentes      # grafias já no banco
        self.sql = None

    async def fetchrow(self, sql, nome):
        self.sql = sql
        chave = nome.lower().replace(" ", "")
        for c in self.existentes:
            if c.lower().replace(" ", "") == chave:
                return {"casa": c}
        return None


class _Pool:
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        conn = self.conn

        class _A:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _A()


def _canonica(nome, existentes=("PixBet", "Bet365", "Rei do Pitaco", "Bolsa de Aposta")):
    conn = _Conn(list(existentes))
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_Pool(conn))):
        return asyncio.run(repository.casa_canonica(nome))


def test_reusa_a_grafia_existente():
    assert _canonica("Pixbet") == "PixBet"
    assert _canonica("PIXBET") == "PixBet"
    assert _canonica("pixbet") == "PixBet"


def test_casa_nova_entra_verbatim():
    # Nada de title-case nem de comer espaço — esse foi o bug da s141.
    assert _canonica("Rei do Pitaco") == "Rei do Pitaco"
    assert _canonica("Casa Nova de Aposta") == "Casa Nova de Aposta"
    assert _canonica("beGamble") == "beGamble"


def test_espaco_nao_separa_a_mesma_casa():
    assert _canonica("bolsadeaposta") == "Bolsa de Aposta"
    assert _canonica("Bolsa De Aposta") == "Bolsa de Aposta"


def test_sufixo_diferente_continua_sendo_outra_casa():
    # "Esportiva" × "Esportiva Bet" só um humano decide — a trava não adivinha.
    assert _canonica("Esportiva Bet", existentes=("Esportiva",)) == "Esportiva Bet"


def test_vazio_e_espaco_nao_quebram():
    assert _canonica("") == ""
    assert _canonica("   ") == ""
