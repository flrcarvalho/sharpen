"""Regra de deduplicação (Feca): casa SEM ID → duplicata só quando stake + odd + descrição
batem os TRÊS. Qualquer divergência = bilhetes distintos.

Guarda o bug em que `stake` NÃO entrava na assinatura: dois bilhetes reais do mesmo
mercado com stakes diferentes colidiam e um sobrescrevia o outro (perda silenciosa) —
foi o que gerou os falsos "duplicados" do marcador Daniel Rios.

conftest.py stuba asyncpg/database, então `import repository` funciona sem Postgres.
"""
import repository  # noqa: E402  (stubs vêm do conftest)

_A = repository._assinatura


def _row(**kw):
    base = dict(casa="Bet365", parceiro="conta1", data="08/07/2026",
                aposta="Anytime", descricao="Daniel Rios [Vancouver FC v CF Montreal]",
                stake="8,44", odd="2,75", codigo_bilhete="")
    base.update(kw)
    return base


# ── SEM ID: os 3 campos importam ───────────────────────────────────────────────

def test_stake_diferente_nao_e_duplicata():
    # Mesmo mercado, mesma odd, MESMA descrição, stake diferente → bilhetes distintos.
    assert _A(_row(stake="8,44")) != _A(_row(stake="50,00"))


def test_odd_diferente_nao_e_duplicata():
    assert _A(_row(odd="2,75")) != _A(_row(odd="13,00"))


def test_descricao_diferente_nao_e_duplicata():
    assert _A(_row(descricao="Daniel Rios - 2+ Gols [Vancouver FC v CF Montreal]")) != \
           _A(_row(descricao="Daniel Rios [Vancouver FC v CF Montreal]"))


def test_os_tres_identicos_e_duplicata():
    # stake + odd + descrição idênticos → mesma assinatura (duplicata verdadeira).
    assert _A(_row()) == _A(_row())


def test_odd_precisao_absorvida_mesmo_stake():
    # Mesma aposta lida com precisões diferentes (header vs cálculo), MESMO stake →
    # _norm_odd absorve a 2 casas → mesma assinatura (não vira duplicata falsa).
    assert _A(_row(odd="2,75")) == _A(_row(odd="2,7501483"))


# ── COM ID: o código manda (stake irrelevante) ────────────────────────────────

def test_com_codigo_usa_id_ignora_stake():
    a = _A(_row(codigo_bilhete="890J-QD71FJ", stake="8,44"))
    b = _A(_row(codigo_bilhete="890J-QD71FJ", stake="999,99", descricao="qualquer outra"))
    assert a == b   # mesmo código = mesmo bilhete, resto ignorado


def test_codigos_diferentes_sao_distintos():
    assert _A(_row(codigo_bilhete="AAA")) != _A(_row(codigo_bilhete="BBB"))
