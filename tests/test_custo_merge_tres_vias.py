"""Duas abas não apagam o custo uma da outra (s459, auditoria de 17/11 — NAVEGADOR A1, ESCALA A11).

O caso: o front manda o estado INTEIRO e o servidor substituía. A aba aberta antes gravava o
estado velho dela e o lançamento da outra sumia (medido: "Tip Dois R$ 250" apagado). Agora o
front manda a `base` (o que leu) e o servidor aplica só a diferença base → novo.

Funções puras do `repository` (o conftest dubla o banco). A gravação em transação com
`FOR UPDATE` é provada no harness de DB (`test_s459_custos_duas_abas`).
"""
import repository as R


def test_duas_abas_no_custo_de_tipster():
    servidor = {"Tip Um": {"2026-11": "100"}}
    base = {"Tip Um": {"2026-11": "100"}}
    # Aba 1 lança um tipster novo
    servidor = R._diff_custo_tipster(servidor, base, {"Tip Um": {"2026-11": "100"},
                                                      "Tip Dois": {"2026-11": "250"}})
    # Aba 2, aberta antes, corrige o Tip Um com a base velha
    servidor = R._diff_custo_tipster(servidor, base, {"Tip Um": {"2026-11": "120"}})
    assert servidor == {"Tip Um": {"2026-11": "120"}, "Tip Dois": {"2026-11": "250"}}


def test_apagar_continua_apagando():
    servidor = {"Tip Um": {"2026-10": "90", "2026-11": "100"}, "Tip Dois": {"2026-11": "250"}}
    base = dict(servidor)
    out = R._diff_custo_tipster(servidor, base, {"Tip Um": {"2026-10": "90"},
                                                 "Tip Dois": {"2026-11": "250"}})
    assert out == {"Tip Um": {"2026-10": "90"}, "Tip Dois": {"2026-11": "250"}}
    out = R._diff_custo_tipster(out, out, {"Tip Dois": {"2026-11": "250"}})
    assert out == {"Tip Dois": {"2026-11": "250"}}, "tirar o tipster inteiro tem de valer"


def test_mes_que_a_outra_aba_mexeu_nao_e_desfeito():
    servidor = {"Tip Um": {"2026-10": "90", "2026-11": "999"}}   # aba 1 já mudou novembro
    base = {"Tip Um": {"2026-10": "90", "2026-11": "100"}}
    out = R._diff_custo_tipster(servidor, base, {"Tip Um": {"2026-10": "95", "2026-11": "100"}})
    assert out == {"Tip Um": {"2026-10": "95", "2026-11": "999"}}


def test_custo_geral_por_id():
    base = [{"id": 1, "tipo": "VPS", "values": {"2026-11": "50"}}]
    servidor = [{"id": 1, "tipo": "VPS", "values": {"2026-11": "50"}},
                {"id": 2, "tipo": "Proxy", "values": {"2026-11": "30"}}]   # aba 1 criou o id 2
    out = R._diff_custo_geral(servidor, base, [{"id": 1, "tipo": "VPS", "values": {"2026-11": "60"}}])
    assert {l["id"]: l["values"]["2026-11"] for l in out} == {1: "60", 2: "30"}
    out2 = R._diff_custo_geral(out, out, [l for l in out if l["id"] != 1])
    assert [l["id"] for l in out2] == [2], "apagar a linha tem de valer"


def test_custo_por_conta():
    servidor = {"Move||Bet365": 950, "JC||Betano": 600}   # aba 1 lançou a Betano
    base = {"Move||Bet365": 950}
    out = R._diff_dict(servidor, base, {"Move||Bet365": 900})
    assert out == {"Move||Bet365": 900, "JC||Betano": 600}
    assert R._diff_dict(out, out, {"JC||Betano": 600}) == {"JC||Betano": 600}
