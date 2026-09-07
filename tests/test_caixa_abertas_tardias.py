# -*- coding: utf-8 -*-
"""Caixa (s327) — a aposta que já estava viva no corte e só CHEGOU ao banco depois.

`abertas_corte` mede o que o SHARPEN SABIA no instante da ativação, não o que a CASA
TINHA. Entre a captura começar e o `/salvar` gravar existe uma janela de ~1 minuto;
ligar a Caixa dentro dela grava uma lista VAZIA que nunca mais se revisita. Medido na
`Betnacional / renanfernando01 [Richard]`:

    03:17:32  Caixa ligada     → abertas_corte = []   (o banco não tinha aberta ainda)
    03:18:19  /salvar grava    → 3 apostas nascem ABERTAS: R$ 600,00
    03:18:35  Conferência      → projetado −599,00, e o Ajuste CIMENTOU os R$ 600,00

A conta ficou R$ 1.362,26 abaixo da casa e a divergência era da própria auditoria.

O QUE ESTE ARQUIVO **NÃO** COBRE
--------------------------------
O `conn` aqui é dublê: ele devolve o lançamento `inicial` que o teste mandou e guarda
os UPDATEs, mas não valida SQL, não tem tabela e nunca falha por tipo. O que se testa é
a DECISÃO (quem entra, quem fica de fora, e que a lista só cresce). O caminho real de
banco vive no harness de `tests/test_repository_db.py`, que só roda no CI.
"""
import asyncio
from datetime import date, datetime, timedelta, timezone

import pytest

from repository import _caixa_adotar_abertas_tardias

CASA, PARC = "Betnacional", "renanfernando01 [Richard]"
ATIVACAO = datetime(2026, 9, 5, 3, 17, 32, tzinfo=timezone.utc)
CORTE = date(2026, 9, 5)


class ConnDuble:
    """Devolve sempre o mesmo lançamento `inicial` e registra os UPDATEs."""

    def __init__(self, inicial):
        self.inicial = inicial
        self.updates = []

    async def fetchrow(self, _sql, *_args):
        return self.inicial

    async def execute(self, _sql, *args):
        self.updates.append(args)


def _inicial(abertas_corte=(), criado_em=ATIVACAO, corte=CORTE):
    return {"id": 140, "data": corte, "criado_em": criado_em,
            "abertas_corte": list(abertas_corte)}


def _aposta(bid, criado_em, data="05/09/2026", stake="150,00"):
    return (CASA, PARC, {"id": bid, "stake": stake, "resultado": "",
                         "data": data, "criado_em": criado_em})


def _rodar(conn, novas, monkeypatch):
    # `hoje` é lido de `date.today()`; fixamos para o dia do corte (o cenário medido).
    import repository
    class _Data(date):
        @classmethod
        def today(cls):
            return CORTE
    monkeypatch.setattr(repository, "date", _Data)
    return asyncio.run(_caixa_adotar_abertas_tardias(conn, "Feca", novas))


def test_caso_medido_as_tres_abertas_que_chegaram_atrasadas_entram(monkeypatch):
    """O cenário da Betnacional: Caixa ligada 03:17:32, as 3 abertas capturadas 03:17:27
    só chegaram ao banco no /salvar das 03:18:19."""
    captura = ATIVACAO - timedelta(seconds=5)
    conn = ConnDuble(_inicial())
    n = _rodar(conn, [_aposta(243665, captura, stake="300,00"),
                      _aposta(243666, captura, data="04/09/2026"),
                      _aposta(243667, captura)], monkeypatch)
    assert n == 3
    assert len(conn.updates) == 1
    assert conn.updates[0][0] == [243665, 243666, 243667]


def test_aposta_feita_depois_da_ativacao_nao_entra(monkeypatch):
    """O stake dela saiu DEPOIS da leitura do saldo — entra pelo P/L, não pelo corte.
    Adotá-la faria a projeção nascer alta em exatamente um stake."""
    conn = ConnDuble(_inicial())
    n = _rodar(conn, [_aposta(300, ATIVACAO + timedelta(minutes=5))], monkeypatch)
    assert n == 0
    assert conn.updates == []


def test_a_lista_so_cresce(monkeypatch):
    """Quem já estava no `abertas_corte` foi reconhecido na ativação. Removê-lo
    descontaria o stake duas vezes."""
    conn = ConnDuble(_inicial(abertas_corte=[99]))
    n = _rodar(conn, [_aposta(243667, ATIVACAO - timedelta(seconds=5))], monkeypatch)
    assert n == 1
    assert conn.updates[0][0] == [99, 243667], "a lista perdeu um id que já estava lá"


def test_id_ja_presente_nao_duplica_nem_regrava(monkeypatch):
    """Idempotente: reprocessar o mesmo lote não mexe na lista."""
    conn = ConnDuble(_inicial(abertas_corte=[243667]))
    n = _rodar(conn, [_aposta(243667, ATIVACAO - timedelta(seconds=5))], monkeypatch)
    assert n == 0
    assert conn.updates == []


def test_conta_sem_caixa_ligada_nao_e_tocada(monkeypatch):
    conn = ConnDuble(None)
    n = _rodar(conn, [_aposta(243667, ATIVACAO - timedelta(seconds=5))], monkeypatch)
    assert n == 0
    assert conn.updates == []


@pytest.mark.parametrize("criado_em", [
    None,                                        # import/sync: cai no NOW() do INSERT
    datetime(2026, 9, 5, 3, 17, 27),             # naive: comparar levantaria TypeError
])
def test_criado_em_incomparavel_fica_de_fora(monkeypatch, criado_em):
    """Sem `criado_em` com fuso não há prova de que a aposta antecede a leitura do saldo.
    E a comparação de um naive com o instante da ativação estouraria DENTRO do /salvar,
    derrubando a gravação inteira por causa de uma linha de caixa."""
    conn = ConnDuble(_inicial())
    n = _rodar(conn, [_aposta(243667, criado_em)], monkeypatch)
    assert n == 0
    assert conn.updates == []


def test_lote_sem_aberta_nova_nao_consulta_nada(monkeypatch):
    conn = ConnDuble(_inicial())
    assert _rodar(conn, [], monkeypatch) == 0
    assert conn.updates == []
