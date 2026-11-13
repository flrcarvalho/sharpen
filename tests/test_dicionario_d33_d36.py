"""As decisões D33, D35 e D36 do Feca (19/10/2026) que vivem no CÓDIGO e no Master (s423).

  · D33: Boxe, Críquete, Futsal, Polo Aquático, Futebol Australiano, Bandy e Floorball são
    esportes do `MASTER_ESPORTES §7` (o `corrigir_termo` recusa valor fora do Master, e a Ficha
    manda à IA o que sai do Master);
  · D35: `Mortes`, `kills` e `Abates` são `Kills` no estilo da descrição, em todas as casas
    (`descricao_ficha.estilo`, que decide a forma do voto e da regravação);
  · D36: `sporttypeid 300` é vago (gaveta de especiais da Altenar), nunca traduzido;
  · D37 (`sporttypeid 34` e `31` vagos) foi REVOGADA pela D49 (11/11/2026): o gate dela é
    `tests/test_dicionario_d49.py`.

Não cobre: o termo vago que já estivesse gravado no banco (o 300 foi apagado pelo script).

As correções de dado (os termos `origem='feca'`) estão em `scripts/carga_dicionario_s423.py`.

Mutações (s423), cada uma derrubou ao menos um teste daqui:
  K1. sem a regra do Kills no `estilo`                 → test_d35_kills
  K2. a regra só em minúsculas (sem `re.I`)            → test_d35_kills
  V1. `sporttypeid 300` fora do `VAGOS`                → test_d36_d37_sporttypeid_e_vago[300]
  (V2 e V3, o 34 e o 31 fora do `VAGOS`, deixaram de ser mutação com a D49.)
  E1. um esporte novo tirado do Master                 → test_d33_esportes_no_master
"""
import asyncio

import pytest

import dicionario
import descricao_ficha
import taxonomia


def test_d33_esportes_no_master():
    esp = taxonomia.esportes_canonicos()
    for nome in ("Boxe", "Críquete", "Futsal", "Polo Aquático", "Futebol Australiano", "Bandy",
                 "Floorball", "MMA"):
        assert nome in esp, nome
    assert esp[-1] == "Outro"


def test_d35_kills():
    e = descricao_ficha.estilo
    assert e("{ou} Mortes {n1}º Mapa") == "{ou} Kills {n1}º Mapa"
    assert e("{ent} {hc} mortes {n1}º Mapa") == "{ent} {hc} Kills {n1}º Mapa"
    assert e("{ou} Total de Abates") == "{ou} Total de Kills"
    assert e("{ou} kills") == "{ou} Kills"
    # duas formas do mesmo mercado viram UM voto
    assert descricao_ficha.canonico("{ou} Mortes {n1}º Mapa") == \
        descricao_ficha.canonico("{ou} Kills {n1}º Mapa")
    # palavra que só contém o termo não muda
    assert e("{ent} Mortensen") == "{ent} Mortensen"


@pytest.mark.parametrize("sid", ["300"])
def test_d36_d37_sporttypeid_e_vago(sid):
    """D36 (300): nunca traduzido, mesmo com o termo no dicionário (o 34 e o 31 da D37 saíram
    com a D49)."""
    termo = f"sporttypeid {sid}"
    assert termo in dicionario.VAGOS
    f = {"tipo": "simples", "pernas": [{"esporte_casa": f"sportTypeId {sid}", "mercado_casa": "x",
                                         "selecao_casa": "y", "evento": "A vs. B"}]}
    termos = {("esporte", termo): "Tênis de Mesa", ("categoria", "x"): "ML"}
    esporte, _, faltam = dicionario.traduzir(f, termos)
    assert esporte is None and ("esporte", termo) in faltam
    # e a correção à mão também é recusada (nunca entra no dicionário)
    with pytest.raises(ValueError, match="vago"):
        asyncio.run(dicionario.corrigir_termo(None, "*", "esporte", termo, "Críquete"))
