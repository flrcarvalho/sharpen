"""Aposta MANUAL em conta de outra moeda (s404): `/bilhetes/manual` converte como o `/salvar`.

O QUE ABRIU A REGRA: a Kiko lançava à mão as apostas de uma conta cadastrada em EUR e
elas entravam como R$. A rota manual mandava a stake digitada direto ao `upsert_bilhetes`,
sem passar pelo `cambio.converter_linhas` que o `/salvar` usa: 40 € viravam R$ 40,00, sem
`moeda` e sem `cotacao`.

Estes testes chamam a ROTA REAL (`main.inserir_bilhete_manual`). Só o banco (moeda da
conta e o UPSERT) e a rede (`cambio.carregar`) são dublados; a conversão é o código real.

MUTAÇÕES QUE ESTES TESTES PEGAM (rodadas uma a uma contra o código real):
  • bloco de conversão removido da rota            → stake sai em EUR, sem moeda
  • `if recusadas:` removido (grava sem cotação)    → euro gravado como real
  • `except CambioIndisponivel` removido            → 500 cru em vez do aviso de câmbio

O QUE ESTES TESTES **NÃO** COBREM:
  • o SQL do UPSERT gravando `moeda`/`stake_orig`/`cotacao` (coberto em
    `tests/test_repository_db.py`, só no CI);
  • o rótulo `Stake (EUR)` do modal (é tela; conferido no navegador).
"""
import asyncio
import sys

import pytest
from fastapi import HTTPException

sys.path.insert(0, "app")

import cambio as C  # noqa: E402
import main  # noqa: E402
import polymarket as P  # noqa: E402


def _body(**kw):
    base = dict(casa="Kikobet", parceiro="Kiko", data="08/10/2026", esporte="Futebol",
                aposta="Resultado Final", descricao="Time A x Time B", stake="40,00",
                odd="2,10", resultado="")
    base.update(kw)
    return main.BilheteManualRequest(**base)


def _prepara(monkeypatch, moeda, cotacoes=None, carregar_falha=False):
    """Dubla banco e rede. Devolve a lista onde o UPSERT dublado guarda o que recebeu."""
    C._PTAX_MOEDA_MAPA.clear()
    C._PTAX_MOEDA_MAPA[moeda] = dict(cotacoes or {})
    gravadas = []

    async def _moeda(dono, casa, nome):
        return moeda

    async def _carregar(m, isos):
        if carregar_falha:
            raise P.CambioIndisponivel(f"Câmbio {m}→BRL indisponível agora.")

    async def _upsert(rows, dono, **kw):
        gravadas.extend(rows)
        return 1, 0, [123], [], {}

    monkeypatch.setattr(main, "moeda_da_conta", _moeda)
    monkeypatch.setattr(main._cambio, "carregar", _carregar)
    monkeypatch.setattr(main, "upsert_bilhetes", _upsert)
    return gravadas


def test_conta_em_eur_grava_em_reais_com_a_origem_ao_lado(monkeypatch):
    gravadas = _prepara(monkeypatch, "EUR", {"2026-10-08": 6.2})
    res = asyncio.run(main.inserir_bilhete_manual(_body(), dono="Feca"))
    assert res["id"] == 123
    row = gravadas[0]
    assert row["moeda"] == "EUR"
    assert row["stake_orig"] == 40.0
    assert row["cotacao"] == 6.2
    assert row["stake"] == "248,00"


def test_conta_em_brl_grava_a_stake_como_digitada(monkeypatch):
    gravadas = _prepara(monkeypatch, "BRL")
    asyncio.run(main.inserir_bilhete_manual(_body(), dono="Feca"))
    row = gravadas[0]
    assert row["stake"] == "40,00"
    assert "moeda" not in row


def test_sem_cotacao_a_aposta_nao_entra(monkeypatch):
    gravadas = _prepara(monkeypatch, "EUR", {})
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.inserir_bilhete_manual(_body(), dono="Feca"))
    assert exc.value.status_code == 422
    assert "sem cotação EUR" in exc.value.detail
    assert gravadas == []


def test_cambio_fora_do_ar_avisa_e_nao_grava(monkeypatch):
    gravadas = _prepara(monkeypatch, "EUR", carregar_falha=True)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.inserir_bilhete_manual(_body(), dono="Feca"))
    assert exc.value.status_code == 503
    assert gravadas == []
