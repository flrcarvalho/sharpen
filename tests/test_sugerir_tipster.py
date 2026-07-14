"""Testes do ESQUELETO da auto-atribuição (Perfil de Tipster, Fase B) — função PURA.

Cobre o ranqueamento de candidatos por apelido/marca d'água, casa e faixa de stake,
sem tocar no banco. A função é de gaveta (ainda não plugada na extração). Ver
repository.sugerir_tipster e docs/PLANO_TIPSTER.md.
"""
from repository import sugerir_tipster


TIPS = [
    {"nome": "SóChutes", "casas": "Bet365, Betano",
     "stake_min": 50.0, "stake_max": 500.0, "apelidos": "@sochutes, SÓ CHUTES"},
    {"nome": "Zé das Odds", "casas": "Superbet",
     "stake_min": None, "stake_max": None, "apelidos": ""},
    {"nome": "Arrudex", "casas": "",
     "stake_min": 100.0, "stake_max": None, "apelidos": None},
]


def test_apelido_e_o_sinal_mais_forte():
    r = sugerir_tipster({"casa": "", "stake": None, "texto": "veio do @SoChutes hoje"}, TIPS)
    assert r[0]["nome"] == "SóChutes"
    assert r[0]["score"] == 100
    assert "apelido" in r[0]["motivos"]


def test_casa_pontua_dez():
    r = sugerir_tipster({"casa": "Betano", "stake": None, "texto": ""}, TIPS)
    assert r[0]["nome"] == "SóChutes"
    assert r[0]["score"] == 10
    assert r[0]["motivos"] == ["casa"]


def test_casa_ignora_espaco_e_caixa():
    # "BET 365" → slug bet365 casa com "Bet365" do cadastro.
    r = sugerir_tipster({"casa": "BET 365", "stake": None, "texto": ""}, TIPS)
    assert r and r[0]["nome"] == "SóChutes" and "casa" in r[0]["motivos"]


def test_stake_dentro_da_faixa_pontua_cinco():
    r = sugerir_tipster({"casa": "", "stake": 200, "texto": ""}, TIPS)
    nomes = {x["nome"] for x in r}
    assert "SóChutes" in nomes    # 200 ∈ [50, 500]
    assert "Arrudex" in nomes     # 200 ≥ 100 (só mínima definida)
    assert "Zé das Odds" not in nomes  # sem faixa → não pontua stake
    assert all(x["score"] == 5 for x in r)


def test_stake_fora_da_faixa_nao_pontua():
    # 1000 > max 500 do SóChutes → sem ponto; Arrudex (só min 100) 1000 ≥ 100 → pontua.
    r = sugerir_tipster({"casa": "", "stake": 1000, "texto": ""}, TIPS)
    assert [x["nome"] for x in r] == ["Arrudex"]


def test_stake_string_br_e_aceita():
    r = sugerir_tipster({"casa": "", "stake": "1.234,50", "texto": ""}, TIPS)
    # 1234,50 > 500 (SóChutes fora) e ≥ 100 (Arrudex dentro)
    assert [x["nome"] for x in r] == ["Arrudex"]


def test_sinais_somam():
    r = sugerir_tipster({"casa": "Bet365", "stake": 100, "texto": "aposta @sochutes"}, TIPS)
    assert r[0]["nome"] == "SóChutes"
    assert r[0]["score"] == 115   # 100 apelido + 10 casa + 5 stake
    assert set(r[0]["motivos"]) == {"apelido", "casa", "stake"}


def test_sem_sinal_lista_vazia():
    # Casa desconhecida, sem stake (não dispara faixa) e texto sem apelido → nada.
    r = sugerir_tipster({"casa": "KTO", "stake": None, "texto": "nada aqui"}, TIPS)
    assert r == []


def test_ranqueia_do_maior_pro_menor():
    # SóChutes casa+stake (15) vs Arrudex stake (5) → SóChutes primeiro.
    r = sugerir_tipster({"casa": "Bet365", "stake": 150, "texto": ""}, TIPS)
    assert [x["nome"] for x in r] == ["SóChutes", "Arrudex"]
    assert r[0]["score"] == 15 and r[1]["score"] == 5


def test_limite_corta_o_ranking():
    r = sugerir_tipster({"casa": "", "stake": 200, "texto": ""}, TIPS, limite=1)
    assert len(r) == 1


def test_apelido_vazio_nao_casa_com_texto_vazio():
    # Zé das Odds tem apelidos="" — não deve casar com um texto qualquer.
    r = sugerir_tipster({"casa": "", "stake": None, "texto": "qualquer coisa"}, TIPS)
    assert r == []
