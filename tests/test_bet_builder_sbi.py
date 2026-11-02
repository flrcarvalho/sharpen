"""D43 (Feca, 01/11/2026): Bet Builder pela Ficha, começando pela Sportsbet.io.

Dinheiro e categoria pelos 11 Bet Builders da fixture do harness (`extensor/harness/fixtures/
sportsbetio.*.json`, recon de 25/10 na conta do Feca, já no repositório): o adaptador só deixou de
recusar, e o dinheiro sai do bilhete pelo caminho que já existia. O `6add3525` (30,01 @ 4,75,
perdido) é uma das linhas que a IA tinha gravado: `P.J. Washington - 10+ Rebotes / 10+ Pontos
[Dallas Mavericks v San Antonio Spurs]`, a mesma descrição.

As 5 descrições que o Feca aprovou são conferidas com pernas montadas só com a seleção e o jogo
(dado público de esporte): os crus de produção daqueles bilhetes NÃO vão para o repositório.

Formato (aprovado): esporte do jogo, categoria `Múltipla` (`MASTER_APOSTAS`, "Bet Builder / Criar
Aposta"), o mesmo jogador junta os mercados com ` / ` na ordem da casa, jogadores ou jogos
diferentes com ` // `, um colchete só.

Mutações provadas (aplicadas, teste ao lado vermelho):
  B1. o `sbi` volta a recusar o Bet Builder               → os_11_do_harness_pela_ficha
  B2. sem a regra de categoria (vai pelo dicionário)      → os_11_do_harness_pela_ficha
  B3. sem juntar o mesmo jogador com ` / `                → as_5_aprovadas
  B4. jogadores diferentes juntos com ` / `               → jogadores_diferentes_vao_com_barra_dupla
  B5. estatística fora da lista aceita                    → selecao_fora_do_padrao_vai_com_o_texto_da_casa
  B6. o Bet Builder volta a votar categoria na semente    → semente_nao_aprende_com_o_bet_builder
  B7. o Bet Builder volta a passar pelo voto de descrição → semente_nao_aprende_com_o_bet_builder
      (o voto em si já não sairia; o que pega é a recusa falsa na `semente_recusa`)

O QUE NÃO COBRE: Bet Builder da 20bet e da Altenar (3 e 1 recusas no histórico, ficam recusando);
período diferente de "Partida" e estatística fora de Pontos/Rebotes/Assistências (não medidos nos 52
bilhetes de 25 a 31/10: gravam com o texto da casa, nunca vão à IA por isso).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import descricao_ficha  # noqa: E402
import dicionario  # noqa: E402
import ficha  # noqa: E402
import virada  # noqa: E402
from adaptadores import sbi  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {}
for _nome in ("sportsbetio.settled.json", "sportsbetio.active.json"):
    for _c in sbi.bilhetes_da_resposta(json.loads((_FIX / _nome).read_text(encoding="utf-8"))):
        CRUS[sbi.codigo(_c)] = _c
BB = {k: c for k, c in CRUS.items()
      if any(s.get("marketName") == "Bet Builder" for s in c["bets"][0]["selections"])}
TERMOS = {("esporte", "basketball"): "Basquete"}


def _ficha(cod):
    f, motivos = ficha.montar_ficha("sbi", CRUS[cod], "SPORTSBETIO")
    assert motivos == [], motivos
    return f


def test_os_11_do_harness_pela_ficha():
    assert len(BB) == 11
    for cod in BB:
        f = _ficha(cod)
        # 3+ jogos diferentes é `Múltiplos` pela regra global de esporte, não pela D43
        esporte = "Múltiplos" if len({p["evento"] for p in f["pernas"]}) >= 3 else "Basquete"
        assert dicionario.traduzir(f, TERMOS) == (esporte, "Múltipla", []), cod
        assert virada.descricao_para_gravar(f, TERMOS) == virada.descricao(f, TERMOS), cod
    f = _ficha("6add3525bf9e9d0001ae48c4")                  # a linha que a IA tinha gravado
    d = ficha.derivar(f)
    assert (d["stake"], d["odd"], d["resultado"]) == ("30,01", "4,75", "L")
    assert virada.descricao_para_gravar(f, TERMOS) == \
        "P.J. Washington - 10+ Rebotes / 10+ Pontos [Dallas Mavericks v San Antonio Spurs]"
    f = _ficha("6adbd1f9bf9e9d00010157de")                  # dois Bet Builders numa múltipla
    assert ficha.derivar(f)["odd"] == "59,5"
    assert virada.descricao_para_gravar(f, TERMOS) == (
        "A. Drummond - 10+ Rebotes / 10+ Pontos [Boston Celtics v NY Knicks] // "
        "Moussa Diabate - 10+ Rebotes / 10+ Pontos [Charlotte Hornets v Atlanta Hawks]")


def _perna(sel, evento="A - B"):
    return {"esporte_casa": "Basketball", "evento": evento, "mercado_casa": "Bet Builder",
            "selecao_casa": sel}


def _bb(jog, *itens):
    return ";".join(f"{stat} do jogador - {jog} {n} (Partida)" for stat, n in itens)


def test_as_5_aprovadas():
    casos = [
        (_perna(_bb("Amen Thompson", ("Rebotes", "10+"), ("Pontos", "10+")),
                "Houston Rockets - Oklahoma City Thunder"),
         "Amen Thompson - 10+ Rebotes / 10+ Pontos [Houston Rockets v Oklahoma City Thunder]"),
        (_perna(_bb("N. Reid", ("Rebotes", "10+"), ("Pontos", "12+")),
                "Charlotte Hornets - Washington Wizards"),
         "N. Reid - 10+ Rebotes / 12+ Pontos [Charlotte Hornets v Washington Wizards]"),
        (_perna(_bb("J. Smith", ("Rebotes", "10+"), ("Pontos", "10+")),
                "Boston Celtics - Chicago Bulls"),
         "J. Smith - 10+ Rebotes / 10+ Pontos [Boston Celtics v Chicago Bulls]"),
        (_perna(_bb("Zach Edey", ("Rebotes", "10+"), ("Pontos", "10+")),
                "Memphis Grizzlies - Sacramento Kings"),
         "Zach Edey - 10+ Rebotes / 10+ Pontos [Memphis Grizzlies v Sacramento Kings]"),
    ]
    for p, esperado in casos:
        assert dicionario.descricao_bet_builder(p) == esperado
        assert dicionario.traduzir({"tipo": "simples", "pernas": [p]}, TERMOS)[1] == "Múltipla"
    # o 5º: dois Bet Builders numa múltipla, cada um com o seu colchete, unidos por ` // `
    m = {"tipo": "multipla", "pernas": [
        _perna(_bb("N. Reid", ("Rebotes", "10+"), ("Pontos", "12+")),
               "Washington Wizards - Charlotte Hornets"),
        _perna(_bb("J. Smith", ("Rebotes", "10+"), ("Pontos", "10+")), "Boston Celtics - Chicago Bulls")]}
    assert virada.descricao_para_gravar(m, TERMOS) == (
        "N. Reid - 10+ Rebotes / 12+ Pontos [Washington Wizards v Charlotte Hornets] // "
        "J. Smith - 10+ Rebotes / 10+ Pontos [Boston Celtics v Chicago Bulls]")


def test_jogadores_diferentes_vao_com_barra_dupla():
    p = _perna("Pontos do jogador - X 20+ (Partida);Rebotes do jogador - Y 8+ (Partida);"
               "Assistências do jogador - Y 5+ (Partida)")
    assert dicionario.descricao_bet_builder(p) == "X - 20+ Pontos // Y - 8+ Rebotes / 5+ Assistências [A v B]"


def test_selecao_fora_do_padrao_vai_com_o_texto_da_casa():
    p = _perna("Roubos do jogador - X 2+ (Partida);Pontos do jogador - X 10+ (Partida)")
    assert dicionario.descricao_bet_builder(p) is None
    f = {"tipo": "simples", "pernas": [p]}
    assert virada.descricao_para_gravar(f, TERMOS).startswith("Bet Builder - Roubos do jogador")


def test_semente_nao_aprende_com_o_bet_builder():
    """A IA escreve o Bet Builder de vários jeitos (Múltipla, Player Props; ` / ` e ` // `): o voto
    dela não ensina categoria nem descrição, que vêm de regra, e não vira recusa falsa."""
    f = _ficha("6add3525bf9e9d0001ae48c4")
    desc = "P.J. Washington - 10+ Rebotes / 10+ Pontos [Dallas Mavericks v San Antonio Spurs]"
    unanimes, _, _ = dicionario.votar([("SPORTSBETIO", f, "Basquete", "Player Props", desc)])
    assert not [k for k in unanimes if k[1] in ("categoria", "descricao")]
    rec = []
    descricao_ficha.votos(f, desc, rec)
    assert rec == []
