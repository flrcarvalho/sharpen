"""Testes do motor de unidades (Perfil de Tipster, Fatia 1) — funções PURAS.

Cobre a matemática que preserva o resultado real em "u" ao longo do tempo (o degrau
da escada), sem tocar no banco. Ver docs/PLANO_TIPSTER.md §P1.
"""
from repository import unidade_vigente, pl_em_unidades


# Escada do exemplo do plano: março 1u=R$100, abril em diante 1u=R$200.
ESCADA = [
    {"vigente_desde": "2026-03-01", "valor": 100.0},
    {"vigente_desde": "2026-04-01", "valor": 200.0},
]


def test_unidade_vigente_vazia_ou_data_ilegivel():
    assert unidade_vigente([], "2026-03-15") is None
    assert unidade_vigente(ESCADA, None) is None


def test_unidade_vigente_clamp_esquerda():
    # Antes do 1º degrau usa o 1º valor (sem buraco de "sem stake").
    assert unidade_vigente(ESCADA, "2026-02-10") == 100.0


def test_unidade_vigente_degrau():
    assert unidade_vigente(ESCADA, "2026-03-01") == 100.0   # borda: dia da vigência
    assert unidade_vigente(ESCADA, "2026-03-31") == 100.0
    assert unidade_vigente(ESCADA, "2026-04-01") == 200.0   # borda: troca de degrau
    assert unidade_vigente(ESCADA, "2026-05-20") == 200.0


def test_unidade_vigente_ordem_embaralhada():
    # A função ordena sozinha; não depende da ordem de entrada.
    bagunca = [ESCADA[1], ESCADA[0]]
    assert unidade_vigente(bagunca, "2026-03-15") == 100.0


def test_pl_em_unidades_exemplo_135u():
    # O exemplo do PLANO_TIPSTER: 9000 em março (u=100) + 9000 em abril (u=200).
    linhas = [
        {"pl": 9000.0, "data": "2026-03-15"},
        {"pl": 9000.0, "data": "2026-04-15"},
    ]
    r = pl_em_unidades(linhas, ESCADA)
    assert r["u"] == 135.0          # 90u + 45u — o degrau preserva o real
    assert r["u"] != 90.0           # NÃO é 18000/200 (dividir tudo pela unidade atual)
    assert r["sem_unidade"] == 0
    assert r["usou_fallback"] is False
    assert r["n"] == 2


def test_pl_em_unidades_fallback():
    linhas = [{"pl": 500.0, "data": "2026-03-15"}]
    r = pl_em_unidades(linhas, [], unidade_fallback=250.0)
    assert r["u"] == 2.0
    assert r["usou_fallback"] is True
    assert r["sem_unidade"] == 0


def test_pl_em_unidades_sem_escada_sem_fallback():
    linhas = [{"pl": 500.0, "data": "2026-03-15"}]
    r = pl_em_unidades(linhas, [])
    assert r["sem_unidade"] == 1
    assert r["n"] == 0
    assert r["u"] == 0.0


def test_pl_em_unidades_pl_none_ignorado():
    # Aposta aberta (pl None) não entra na soma nem em sem_unidade.
    linhas = [{"pl": None, "data": "2026-03-15"}, {"pl": 100.0, "data": "2026-03-15"}]
    r = pl_em_unidades(linhas, ESCADA)
    assert r["n"] == 1
    assert r["u"] == 1.0


def test_pl_em_unidades_prejuizo():
    # P/L negativo em u preserva o sinal.
    linhas = [{"pl": -300.0, "data": "2026-04-10"}]
    r = pl_em_unidades(linhas, ESCADA)
    assert r["u"] == -1.5           # -300 / 200
