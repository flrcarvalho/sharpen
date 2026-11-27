"""E1.4 (s465): perna da Cloudbet SEM nome de mercado monta o nome pela tabela da casa.

A posição só traz `marketName`/`outcomeName` em prop de jogador. Mercado de jogo chega só com
`marketKey`, `outcome` e `params`, e a Ficha recusava o bilhete inteiro; o texto ia à IA, que
chutava ("Mercado sem nome", "REVISAR", nome de time num total). O nome agora vem da tabela da
própria casa, copiada em `app/adaptadores/cb_mercados.json` (28 marketKey, data e URL no
cabeçalho).

As regras foram conferidas na casa; os nomes vêm da tabela da casa. Conferência da consultoria
em 27/11/2026, navegando jogos abertos (`1st half - handicap` = "NY Knicks -2.5" / "MIA Heat
+2.5": o `{{-x}}` e o "+" da linha positiva; "Veronika Erjavec Total Games": o `{{team}}`).
O quarter total não foi visto na tela: o nome dele é o da tabela.

Fixture `tests/fixtures/cb_mercado_sem_nome_s465.json`: os crus de produção, como chegaram,
  • eb753f0d (Richard, 20/11/2026): dois `american_football.quarter_total` sem nome;
  • 706e1899 (Ellen, 17/11/2026): `basketball.handicap_period_first_half` away com handicap
    -11.5, que a casa escreve "Lipscomb +11.5".
O código de antes da s465 recusa os dois ("perna 2: sem mercado nem seleção").

Mutações provadas (aplicadas ao `cb.py`, teste ao lado vermelho):
  1. sem o "+" da linha positiva                       → test_706e1899…, test_sinal_da_linha…
  2. `{{-handicap}}` sem trocar o sinal                → test_706e1899…, test_sinal_da_linha…
  3. params só precisam CONTER as variáveis            → test_variavel_a_mais_recusa
  4. `{{team}}` aceita qualquer valor (cai no home)    → test_team_fora_de_home_away_recusa
  5. o nome que a casa manda perde para a tabela       → test_nome_da_casa_manda_sobre_a_tabela

O QUE NÃO COBRE: marketKey fora das 28 (recusa, como antes), as `optional.*` (fora por decisão
da consultoria, 26/11/2026), Criar Aposta com perna sem nome (o mesmo `_perna`, sem amostra), e
se a tabela da casa mudar depois de 26/11/2026: a cópia não se atualiza sozinha.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import Recusa, cb  # noqa: E402

_RAIZ = Path(__file__).resolve().parent.parent
_FIX = json.loads((_RAIZ / "tests" / "fixtures" / "cb_mercado_sem_nome_s465.json").read_text(encoding="utf-8"))
CRUS = {cb.codigo(c)[:8]: c for c in _FIX}


def _pernas(cru):
    f, motivos = ficha.montar_ficha("cb", cru, "CLOUDBET")
    assert not motivos, motivos
    return {p["evento"]: (p["mercado_casa"], p["selecao_casa"]) for p in f["pernas"]}


# A perna é o evento: a eb753f0d tem dois `quarter_total`, em ordem diferente na aposta e na posição.
_HC = "37299665"   # Purdue v Lipscomb, basketball.handicap_period_first_half
_QT = "37230648"   # Tennessee v LSU, american_football.quarter_total (Q2, under 13.5)


def _sel(cru, ev):
    return next(s for s in cru["aposta"]["selections"] if s["eventId"] == ev)


def _sem_nome(cru, ev):
    return next(s for p in cru["posicao"]["positions"] for s in p["selections"] if s["eventId"] == ev)


def _troca(cru, ev, **campos):
    """Muda a perna do evento `ev` na aposta E na posição (as duas precisam continuar casando)."""
    c = copy.deepcopy(cru)
    for s in (_sel(c, ev), _sem_nome(c, ev)):
        s.update(campos)
    return c


def test_eb753f0d_quarter_total():
    p = _pernas(CRUS["eb753f0d"])
    assert p["Tennessee v LSU"] == ("Quarter 2 - total", "Under 13.5")
    assert p["Illinois v Iowa"] == ("Quarter 3 - total", "Over 7.5")
    assert p["CLE Cavaliers v IND Pacers"] == ("Kelly Oubre Jr. Total 3-Pointers Made", "Under 1.5")


def test_706e1899_away_com_a_linha_positiva_de_sinal():
    p = _pernas(CRUS["706e1899"])
    assert p["Purdue v Lipscomb"] == ("1st half - handicap", "Lipscomb +11.5")
    assert p["TOR Raptors v NY Knicks"] == ("Mikal Bridges Total Assists", "Over 2.5")


@pytest.mark.parametrize("outcome,handicap,esperado", [
    ("away", "-11.5", "Lipscomb +11.5"),
    ("away", "11.5", "Lipscomb -11.5"),
    ("away", "0", "Lipscomb 0"),
    ("home", "-2.5", "Purdue -2.5"),
    ("home", "2.5", "Purdue +2.5"),
    ("home", "0", "Purdue 0"),
])
def test_sinal_da_linha_de_handicap(outcome, handicap, esperado):
    c = _troca(CRUS["706e1899"], _HC, outcome=outcome, params=f"handicap={handicap}")
    assert _pernas(c)["Purdue v Lipscomb"][1] == esperado


def test_team_home_e_away_vem_do_evento():
    for time, nome in (("home", "Tennessee"), ("away", "LSU")):
        c = _troca(CRUS["eb753f0d"], _QT, marketKey="soccer.team_total_goals",
                   params=f"team={time}&total=13.5")
        assert _pernas(c)["Tennessee v LSU"] == (f"{nome} Total Goals", "Under 13.5")


def _recusa(c):
    with pytest.raises(Recusa) as e:
        cb.adaptar(c, "CLOUDBET")
    _, motivos = ficha.montar_ficha("cb", c, "CLOUDBET")
    assert motivos, "a Ficha aceitou"
    return str(e.value)


def test_team_fora_de_home_away_recusa():
    c = _troca(CRUS["eb753f0d"], _QT, marketKey="soccer.team_total_goals", params="team=draw&total=13.5")
    assert "team=" in _recusa(c)


def test_variavel_a_mais_recusa():
    c = _troca(CRUS["eb753f0d"], _QT, params="quarter=2&total=13.5&optional.extra=1")
    assert "variáveis" in _recusa(c)


def test_variavel_faltando_recusa():
    c = _troca(CRUS["eb753f0d"], _QT, params="total=13.5")
    assert "variáveis" in _recusa(c)


def test_marketkey_fora_da_tabela_recusa():
    c = _troca(CRUS["eb753f0d"], _QT, marketKey="american_football.qualquer_coisa")
    assert "fora da tabela" in _recusa(c)


def test_outcome_fora_da_tabela_recusa():
    c = _troca(CRUS["eb753f0d"], _QT, outcome="exact")
    assert "outcome" in _recusa(c)


def test_handicap_que_nao_e_numero_recusa():
    c = _troca(CRUS["706e1899"], _HC, params="handicap=abc")
    assert "não é número" in _recusa(c)


def test_evento_sem_o_time_recusa():
    c = copy.deepcopy(CRUS["706e1899"])
    c["eventos"]["37299665"]["away"] = {}
    assert "away" in _recusa(c)


def test_nome_da_casa_manda_sobre_a_tabela():
    c = copy.deepcopy(CRUS["706e1899"])
    _sem_nome(c, _HC).update(marketName="1st Half Spread", outcomeName="Lipscomb Bisons +11.5")
    assert _pernas(c)["Purdue v Lipscomb"] == ("1st Half Spread", "Lipscomb Bisons +11.5")


def test_tabela_tem_as_28_sem_optional_e_com_fonte():
    t = json.loads((_RAIZ / "app" / "adaptadores" / "cb_mercados.json").read_text(encoding="utf-8"))
    assert len(t["mercados"]) == 28
    assert "kubershmuber-dev-sports-asia/market-translations-gz" in t["_cabecalho"]["fonte"]
    assert t["_cabecalho"]["baixado_em"].startswith("26/11/2026")
    for mk, e in t["mercados"].items():
        assert set(e) == {"Name", "Variables", "Outcomes"}, mk
        assert not any(v.startswith("optional.") for v in e["Variables"]), mk


def test_recusa_e_recusa_do_adaptador():
    s = _sel(CRUS["eb753f0d"], _QT)
    with pytest.raises(Recusa):
        cb._nome_da_tabela({**s, "marketKey": "x.y"}, {})
