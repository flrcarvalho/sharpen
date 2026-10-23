"""Gate do adaptador `thp` (Thunderpick, plataforma própria), s426.

Os crus são as fixtures da bancada, byte a byte da casa (`extensor/harness/fixtures/
thunderpick.*.json`, recon de 22/10/2026, conta do Feca: 29 liquidadas e 13 abertas, `uuid`
zerado). Devolvida, cashout e freebet não têm amostra: os testes deles clonam a perdida e trocam
só o campo, e cada valor esperado vem da `CASA_THUNDERPICK.md §5` e do card da casa (exibição em
EUR), nunca do que o código produz.

Conferido antes de ligar, nos 152 crus reais da `captura_crua` (23/10/2026, só leitura): 147
Fichas aceitas e 5 recusadas (3 `cancelReason` "Cancelled by player", 1 perna "Technical lose",
1 `cashOutOdds`); nas 43 que têm linha no banco, resultado, data e odd iguais aos da IA, e a odd
da IA nas ganhas fecha o retorno em EUR.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. código sem o prefixo de tipo                          → test_codigo_tem_o_prefixo_do_tipo
  2. stake e retorno sem ÷ 100                             → test_ganha_simples_bate_com_o_card
  3. tolerância da ganha em meio centavo, não um           → test_ganha_com_retorno_truncado_ou_arredondado
  4. anulada pelo rótulo, não pelo dinheiro                → test_retorno_igual_a_stake_e_anulada
  5. perdida aceita com retorno                            → test_perdida_com_retorno_recusa
  6. `cancelReason`/`cashOutOdds`/`freeBet` deixam de recusar → test_sem_amostra_recusa
  7. perna da múltipla pelo estado do bilhete              → test_aberta_com_perna_ja_ganha
  8. gameId fora do mapa vira um esporte                    → test_esporte_pelo_gameid
  9. recusa sem o código prefixado                         → test_recusa_grava_o_codigo_prefixado
 10. mercado de jogador como a casa escreve (com ` - `)     → test_mercado_de_jogador_vira_chave…
 11. nome sem inverter (sobrenome primeiro)                → test_mercado_de_jogador_vira_chave…

Medido antes de ligar (23/10/2026, "deixa um de fora" nos 43 pares cru × IA da conta do Feca):
26 resolveriam esporte, categoria e descrição sem a IA num bilhete nunca visto, e em nenhuma o
esporte ou a categoria diferiu da IA. O resto é mercado visto uma vez só, que a semente aprende.

O QUE NÃO COBRE: boost, bet builder e sistema (a casa não mostrou nenhum), e qualquer forma de
`freeBet` além de "preenchido = recusa".
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, thp  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {thp.codigo(w): w
        for nome in ("thunderpick.resolved.json", "thunderpick.pending.json")
        for w in thp.bilhetes_da_resposta(json.loads((_FIX / nome).read_text(encoding="utf-8")))}
PERDIDA = "S10286602"      # 22,27 EUR @ 2,24


def _montar(cru, casa="THUNDERPICK"):
    f, motivos = ficha.montar_ficha("thp", cru, casa)
    assert motivos == [], motivos
    return f, ficha.derivar(f)


def _clone(cod=PERDIDA, **campos):
    c = copy.deepcopy(CRUS[cod])
    c.update(campos)
    return c


def test_familia_registrada_e_toda_fixture_monta():
    assert ADAPTADORES["thp"] is thp
    assert len(CRUS) == 42
    for cod, cru in CRUS.items():
        f, _ = _montar(cru)
        assert f["codigo"] == cod and f["moeda"] == "EUR"


def test_codigo_tem_o_prefixo_do_tipo():
    """As duas séries de `wagerId` (múltipla ~2,2M, simples 4,9M–10,3M) e o código do texto."""
    assert _montar(CRUS["C2225866"])[0]["codigo"] == "C2225866"
    assert _montar(CRUS["S10277912"])[0]["codigo"] == "S10277912"
    assert _montar(CRUS["S4988241"])[0]["codigo"] == "S4988241"          # InPlays também é S


def test_ganha_simples_bate_com_o_card():
    """Card em EUR: 43,83 @ 1,62, retorno 71,00 (43,83 × 1,62 = 71,0046)."""
    f, d = _montar(CRUS["S4965610"])
    assert (f["stake"], f["odd"], f["retorno"], f["status"]) == ("43.83", "1.62", "71", "ganha")
    assert (d["resultado"], d["odd"], d["data"]) == ("W", "1,62", "30/04/2025")
    assert f["colocada_em"].startswith("2025-04-25T22:19:35")


def test_ganha_com_retorno_truncado_ou_arredondado():
    """A casa arredonda sem regra fixa: 2226 × 8,41 = 18720,66 → 18720; 2196 × 1,8 = 3952,8 → 3953.
    As duas são ganhas; a odd da planilha é a que fecha o retorno (regra global do `derivar`)."""
    f, d = _montar(CRUS["C2225866"])
    assert (f["status"], f["retorno"], f["tipo"]) == ("ganha", "187.2", "multipla")
    assert d["resultado"] == "W" and d["data"] == "21/10/2026"     # 02:30 UTC de 22/10 = 23:30 SP
    odd = float(d["odd"].replace(",", "."))
    assert abs(22.26 * odd - 187.20) < 0.005
    assert _montar(CRUS["S4956054"])[0]["status"] == "ganha"
    with pytest.raises(Recusa):                                     # 2 centavos: já não fecha
        thp.adaptar(_clone(wagerUIState="won", outcome=4986), "THUNDERPICK")


def test_perdida_e_odd_da_casa():
    f, d = _montar(CRUS["C2225863"])
    assert (f["status"], f["retorno"]) == ("perdida", "0")
    assert (d["resultado"], d["odd"]) == ("L", "13,38")
    assert [p["status_perna"] for p in f["pernas"]] == ["perdida"] * 3


def test_retorno_igual_a_stake_e_anulada():
    for estado in ("won", "lost", "refunded"):
        f, d = _montar(_clone(wagerUIState=estado, outcome=2227))
        assert (f["status"], d["resultado"]) == ("anulada", "V")


def test_perdida_com_retorno_recusa():
    with pytest.raises(Recusa):
        thp.adaptar(_clone(outcome=1200), "THUNDERPICK")
    with pytest.raises(Recusa):                                     # estado novo, sem amostra
        thp.adaptar(_clone(wagerUIState="halfwon", outcome=3000), "THUNDERPICK")


@pytest.mark.parametrize("campos", [
    {"cancelReason": "Cancelled by player"},
    {"cashOutOdds": 1.86},
    {"freeBet": {"amount": 2227}},
])
def test_sem_amostra_recusa(campos):
    with pytest.raises(Recusa):
        thp.adaptar(_clone(**campos), "THUNDERPICK")


def test_perna_cancelada_recusa():
    c = copy.deepcopy(CRUS["C2225863"])
    c["subWagers"][0]["cancelReason"] = "Technical lose"
    with pytest.raises(Recusa):
        thp.adaptar(c, "THUNDERPICK")


def test_aberta_com_perna_ja_ganha():
    """C2225869: múltipla aberta, a 1ª perna já ganha. O bilhete segue aberto, sem retorno."""
    f, d = _montar(CRUS["C2225869"])
    assert (f["status"], f["retorno"], f["liquidada_em"]) == ("aberta", None, None)
    assert [p["status_perna"] for p in f["pernas"]] == ["ganha", "aberta", "aberta"]
    assert d["resultado"] == ""
    p = f["pernas"][0]
    assert p["selecao_casa"] == "Over 6.5" and p["linha"] == "6.5"
    assert p["evento"] == "Anadolu Efes - Besiktas" and p["liga_casa"] == "Euroleague"


def test_esporte_pelo_gameid():
    assert _montar(CRUS["S4965610"])[0]["pernas"][0]["esporte_casa"] == "Counter-Strike"
    assert _montar(CRUS["C2225866"])[0]["pernas"][0]["esporte_casa"] == "Basketball"
    f, _ = _montar(_clone(gameId=99))
    assert f["pernas"][0]["esporte_casa"] is None                   # ausência, não palpite


def test_mercado_de_jogador_vira_chave_de_qualquer_jogador():
    """`Player Green Jalen - total assists and rebounds (incl. overtime)`: a casa escreve
    sobrenome e nome, e o ` - ` esconderia o jogador do dicionário. A Ficha leva o nome na ordem
    da IA (`Jalen Green`), e a chave de categoria troca o nome por `{jogador}`."""
    import dicionario
    import descricao_ficha
    p = _montar(CRUS["C2225866"])[0]["pernas"][0]
    assert p["mercado_casa"] == "Jalen Green total assists and rebounds (incl. overtime)"
    assert descricao_ficha.mercado_com_jogador(p) == "{jogador} total assists and rebounds (incl. overtime)"
    assert dicionario.normalizar(descricao_ficha.mercado_com_jogador(p)) == \
        dicionario.normalizar(descricao_ficha.mercado_com_jogador(
            dict(p, mercado_casa="Nigel Hayes total assists and rebounds (incl. overtime)")))
    # mercado sem jogador fica como a casa escreve
    assert _montar(CRUS["S4965610"])[0]["pernas"][0]["mercado_casa"] == "Round Handicap - Map 2"


def test_badminton_pelo_gameid_43():
    assert _montar(_clone(gameId=43))[0]["pernas"][0]["esporte_casa"] == "Badminton"


def test_recusa_grava_o_codigo_prefixado():
    f, motivos = ficha.montar_ficha("thp", _clone(cashOutOdds=1.5), "THUNDERPICK")
    assert motivos and f["cru_recusado"] and f["codigo"] == PERDIDA
