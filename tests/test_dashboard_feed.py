"""Contrato do feed do dashboard (`repository.dashboard_rows`).

O feed é a única fonte do Betting Dashboard: o front baixa este array e faz toda a
matemática em cima dele. Uma linha a mais ou a menos aqui muda P/L, ROI e turnover
de todas as telas — então o formato merece rede de regressão própria.

O que estes testes travam (sessão 215, quando as ABERTAS passaram a entrar):
  · aposta sem resultado sai marcada `resultado='ABERTA'` com `lucro=0`;
  · aposta aberta NUNCA se disfarça de encerrada (o marcador é o que mantém
    `aplicarFeed` no front separando métrica de listagem);
  · `resultado` fora de {W,L,V,HW,HL} continua sendo lixo descartado — não pode
    virar "aberta" pela porta dos fundos;
  · `criado_em` só viaja nas abertas (nas encerradas seria ~1MB de feed sem consumidor).

Sem DB: `dashboard_rows` só depende de `export_bilhetes`, que é substituído aqui.
"""
import asyncio

import pytest

import repository as R


def _linha(**kw):
    """Linha crua do Postgres, no formato que `export_bilhetes` devolve."""
    base = dict(
        id=1, data="01/07/2026", esporte="Futebol", tipster="Peixe",
        casa="Betano", parceiro="Feca [Eu]", aposta="ML",
        descricao="Time A vs Time B", stake="100,00", odd="2,50",
        resultado="W", criado_em="2026-07-01T10:00:00",
    )
    base.update(kw)
    return base


def _feed(linhas, monkeypatch):
    async def _fake_export(dono):
        return list(linhas)
    monkeypatch.setattr(R, "export_bilhetes", _fake_export)
    return asyncio.run(R.dashboard_rows(["Feca"]))


def test_aberta_entra_marcada_com_lucro_zero(monkeypatch):
    rows = _feed([_linha(id=7, resultado="")], monkeypatch)
    assert len(rows) == 1
    r = rows[0]
    assert r["resultado"] == "ABERTA"
    assert r["lucro"] == 0.0          # nunca odd × stake: não ganhou nada ainda
    assert r["stake"] == 100.0 and r["odd"] == 2.5
    assert r["id"] == 7


def test_aberta_e_encerrada_convivem(monkeypatch):
    rows = _feed([
        _linha(id=1, resultado=""),
        _linha(id=2, resultado="W"),
    ], monkeypatch)
    assert {r["resultado"] for r in rows} == {"ABERTA", "W"}
    ganha = next(r for r in rows if r["resultado"] == "W")
    assert ganha["lucro"] == 150.0    # (2,50 − 1) × 100 — inalterado pela mudança


def test_resultado_invalido_continua_descartado(monkeypatch):
    """Só resultado VAZIO é aberta. Código desconhecido é lixo e some do feed."""
    assert _feed([_linha(resultado="XX")], monkeypatch) == []
    assert _feed([_linha(resultado="  ")], monkeypatch)[0]["resultado"] == "ABERTA"


def test_criado_em_so_nas_abertas(monkeypatch):
    rows = _feed([
        _linha(id=1, resultado=""),
        _linha(id=2, resultado="L"),
    ], monkeypatch)
    aberta = next(r for r in rows if r["resultado"] == "ABERTA")
    encerrada = next(r for r in rows if r["resultado"] == "L")
    assert aberta["criado_em"] == "2026-07-01T10:00:00"
    assert "criado_em" not in encerrada


def test_aberta_sem_stake_fica_de_fora(monkeypatch):
    """stake > 0 vale para as duas: sem valor, a linha não é exposição de nada."""
    assert _feed([_linha(resultado="", stake="0")], monkeypatch) == []


def test_aberta_sem_odd_entra(monkeypatch):
    """A casa nem sempre publica a odd de uma aposta ainda aberta. A linha continua
    valendo (é dinheiro exposto); o front trata odd=0 no Retorno Potencial."""
    rows = _feed([_linha(resultado="", odd="")], monkeypatch)
    assert len(rows) == 1
    assert rows[0]["odd"] == 0 and rows[0]["stake"] == 100.0


def test_aberta_com_data_ilegivel_fica_de_fora(monkeypatch):
    """Mesma régua das encerradas: sem data ISO não há como posicionar a linha
    (e o calendário de "para quando são as apostas" depende dela)."""
    assert _feed([_linha(resultado="", data="sem data")], monkeypatch) == []
