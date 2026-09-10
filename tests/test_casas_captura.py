"""Gate do selo de captura (s344): `GET /casas` → `captura`.

O selo "esta casa tem extração automática" é aceso no dashboard por este campo. Ele
existe para NÃO haver uma segunda lista de casas no front — a verdade é o
`_HOSTS_POR_CASA` do `captura.py`, e o campo é uma vista dela.

Os testes exercem a ROTA (`main.listar_casas`), não uma cópia da linha que monta o
campo: teste que reimplementa o código sob teste fica verde com o código quebrado. Só
as duas leituras de banco são dubladas — o de-para de grafia e o filtro são os reais.

O que cobrem:
  · `CASAS_COM_CAPTURA` é a MESMA coisa que o mapa de hosts (não uma cópia que envelhece);
  · `captura` é subconjunto de `casas`, na grafia EXATA em que `casas` vai (o front
    compara por igualdade e não normaliza — `casa` é TEXTO no sistema);
  · casa sem captura não entra;
  · o de-para display → chave funciona nos nomes que divergem (`Bolsa de Aposta`,
    `BETesporte`, `Betão`), que é onde uma comparação ingênua quebraria em silêncio.

O que NÃO cobrem: se o SharpenUp de fato consegue capturar naquela casa hoje. Isto é um
gate de TRANSPORTE — que o front receba a mesma lista que o servidor tem. A captura em
si é medida pelo harness (`node extensor/harness/run.mjs`). Também não cobrem o render
do selo, que é JS no `index.html`.
"""
import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import captura as _captura  # noqa: E402
import main as _main  # noqa: E402


def chamar_rota(monkeypatch, com_dados=(), dominios=None, casas_dir=None):
    """Roda a rota REAL. Duplica só o banco: `casas_com_parceiros` (casas importadas
    sem manual) e `get_casas_dominios` (favicon). Sem `casas_dir`, as casas de manual
    vêm do filesystem de verdade e a lista é a do repo; passando um diretório vazio
    (`tmp_path`), o teste fica com exatamente as casas que ele declarou."""
    async def _com_dados(dono):
        return list(com_dados)

    async def _dominios(dono):
        return dict(dominios or {})

    monkeypatch.setattr(_main, "casas_com_parceiros", _com_dados)
    monkeypatch.setattr(_main, "get_casas_dominios", _dominios)
    if casas_dir is not None:
        monkeypatch.setattr(_main, "CASAS_DIR", casas_dir)
    return asyncio.run(_main.listar_casas(dono="feca"))


def test_casas_com_captura_e_o_proprio_mapa_de_hosts():
    """Vista, não cópia. Se alguém criar uma segunda lista à mão, isto fica vermelho."""
    assert _captura.CASAS_COM_CAPTURA == frozenset(_captura._HOSTS_POR_CASA)
    assert len(_captura.CASAS_COM_CAPTURA) >= 30, "casa sumiu do mapa de hosts?"


@pytest.mark.parametrize("display", ["Bet365", "Betano", "Superbet", "Pinnacle", "KTO"])
def test_casa_com_captura_entra(monkeypatch, tmp_path, display):
    r = chamar_rota(monkeypatch, com_dados=[display], casas_dir=tmp_path)
    assert r["captura"] == [display]


@pytest.mark.parametrize("display", ["KingPanda", "Polymarket", "Casa Que Nao Existe"])
def test_casa_sem_captura_fica_de_fora(monkeypatch, tmp_path, display):
    r = chamar_rota(monkeypatch, com_dados=[display], casas_dir=tmp_path)
    assert r["casas"] == [display]
    assert r["captura"] == []


@pytest.mark.parametrize(
    "display, chave",
    [
        ("Bolsa de Aposta", "BOLSADEAPOSTA"),  # espaços: o de-para tem de achar
        ("BETesporte", "BETESPORTE"),          # caixa mista da marca
        ("Estrela Bet", "ESTRELABET"),
        ("Jogo de Ouro", "JOGODEOURO"),
        ("Betão", "BETAO"),                    # a chave não tem til, o display tem
        ("7Games", "7GAMES"),                  # começa com dígito
    ],
)
def test_display_que_diverge_da_chave_ainda_acha_a_captura(monkeypatch, tmp_path, display, chave):
    """Estes são os nomes em que comparar a string crua contra a chave falharia — e
    falharia SEM ERRO, só com o selo apagado numa casa que tem captura."""
    assert chave in _captura.CASAS_COM_CAPTURA
    r = chamar_rota(monkeypatch, com_dados=[display], casas_dir=tmp_path)
    assert r["captura"] == [display]


def test_captura_e_subconjunto_de_casas_e_preserva_a_grafia(monkeypatch, tmp_path):
    """O front faz `Set(captura).has(casa)`: qualquer normalização aqui apagaria o selo."""
    casas = ["Bet365", "KingPanda", "Bolsa de Aposta", "Betano", "Polymarket"]
    r = chamar_rota(monkeypatch, com_dados=casas, casas_dir=tmp_path)
    # A rota devolve `casas` ordenada, e `captura` sai na mesma ordem.
    assert r["casas"] == ["Bet365", "Betano", "Bolsa de Aposta", "KingPanda", "Polymarket"]
    assert r["captura"] == ["Bet365", "Betano", "Bolsa de Aposta"]
    assert set(r["captura"]) <= set(r["casas"])
    # Mesma ordem de `casas` — o front itera por `casas` e consulta o Set.
    assert r["captura"] == [c for c in r["casas"] if c in set(r["captura"])]


def test_rota_real_com_os_manuais_do_repo(monkeypatch):
    """Sem dublar o filesystem: as casas de `casas/CASA_*.md` entram, e as que têm
    captura são marcadas. Prova que o campo funciona com o dado real do repo."""
    r = chamar_rota(monkeypatch)
    assert "Bet365" in r["casas"] and "Bet365" in r["captura"]
    assert set(r["captura"]) <= set(r["casas"])
    # Toda casa do mapa de hosts que tem manual no repo tem de estar marcada.
    for display in r["casas"]:
        esperado = _main._display_to_key(display) in _captura.CASAS_COM_CAPTURA
        assert (display in r["captura"]) is esperado, display


def test_casa_tem_captura_aceita_chave_em_qualquer_caixa():
    assert _captura.casa_tem_captura("bet365")
    assert _captura.casa_tem_captura("  BET365  ")
    assert not _captura.casa_tem_captura("")
    assert not _captura.casa_tem_captura(None)
