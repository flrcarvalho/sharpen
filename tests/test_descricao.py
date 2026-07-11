"""Backtest de conformidade da coluna Descrição (indo pra frente).

Roda o checador determinístico (`app/descricao_check.py`) contra os casos reais em
`golden_set/descricoes.jsonl` (corpus que cresce conforme aparecem casos novos) +
casos unitários por regra. É a rede que garante que a QUALIDADE da descrição não
regride — sem IA, sem custo, no CI.

conftest.py põe app/ no sys.path; descricao_check só usa stdlib (re), então importa direto.
"""
import json
import pathlib

import descricao_check
from descricao_check import checar_descricao, resumo_lote

_GOLDEN = pathlib.Path(__file__).resolve().parents[1] / "golden_set" / "descricoes.jsonl"


def _casos():
    linhas = _GOLDEN.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in linhas if l.strip()]


def test_golden_set_existe_e_tem_casos():
    casos = _casos()
    assert len(casos) >= 20, "golden set de descrições ficou pequeno demais"


def test_golden_descricoes_conformes_passam():
    """Todo caso ok=true não pode gerar NENHUM problema."""
    for c in _casos():
        if not c.get("ok"):
            continue
        probs = checar_descricao(c["aposta"], c["descricao"])
        assert probs == [], f"falso positivo em {c['descricao']!r}: {[p.msg for p in probs]}"


def test_golden_descricoes_nao_conformes_sao_pegas():
    """Todo caso ok=false tem de gerar problema; se 'regra' foi declarada, tem de bater."""
    for c in _casos():
        if c.get("ok"):
            continue
        probs = checar_descricao(c["aposta"], c["descricao"])
        assert probs, f"deixou passar descrição inválida: {c['descricao']!r}"
        if "regra" in c:
            regras = {p.regra for p in probs}
            assert c["regra"] in regras, f"{c['descricao']!r}: esperava regra {c['regra']}, veio {regras}"


# ── Casos unitários por regra (documentam o comportamento exato) ──────────────

def test_confronto_valido_nao_reclama():
    assert checar_descricao("ML", "Sinner [Sinner v Alcaraz]") == []


def test_separador_errado_x():
    probs = checar_descricao("ML", "Lakers [LAL Lakers x CHI Bulls]")
    assert any(p.regra == "confronto-separador" and p.nivel == "erro" for p in probs)


def test_over_under_portugues_e_erro():
    probs = checar_descricao("Gols", "Menos de 2.5 Gols [Parma v Fiorentina]")
    assert any(p.regra == "over-under-pt" and p.nivel == "erro" for p in probs)


def test_marcador_sem_confronto_e_aviso_nao_erro():
    probs = checar_descricao("Anytime", "Kylian Mbappe - Primeiro Marcador")
    assert len(probs) == 1
    assert probs[0].regra == "sem-confronto"
    assert probs[0].nivel == "aviso"   # permitido como fallback → aviso, não erro


def test_ml_sem_confronto_nao_avisa():
    # ML/totais fora da família marcador/props: sem confronto é fallback aceitável, sem ruído.
    assert checar_descricao("ML", "Lakers") == []


def test_descricao_vazia_nao_reclama():
    assert checar_descricao("Anytime", "") == []
    assert checar_descricao("Anytime", None) == []


def test_multipla_dois_confrontos_ok():
    d = "Ja Morant - Over 7.5 Assistências [MEM Grizzlies v PHI 76ers] // Over 2.5 Gols [Parma v Fiorentina]"
    assert checar_descricao("Múltipla", d) == []


def test_analisar_extracao_sinaliza_descricao_ruim():
    """Item 3 ponta-a-ponta: o rail de avisos ganha uma nota DESCRIÇÃO quando há
    descrição fora do padrão — e nenhuma quando o lote está limpo (warn-only)."""
    import repository  # conftest stuba asyncpg/database
    campos = dict(data="08/07/2026", esporte="Basquete", odd="1,90", stake="10", resultado="W")

    limpo = [dict(aposta="ML", descricao="Lakers [LAL Lakers v CHI Bulls]", **campos)]
    a = repository.analisar_extracao(limpo)
    assert not any(n["n"] == "DESCRIÇÃO" for n in a["notas"])

    ruim = [dict(aposta="ML", descricao="Lakers [LAL Lakers vs CHI Bulls]", **campos)]
    a2 = repository.analisar_extracao(ruim)
    assert any(n["n"] == "DESCRIÇÃO" and n["tipo"] == "warn" for n in a2["notas"])


def test_resumo_lote_conta_erros_e_avisos():
    rows = [
        {"aposta": "ML", "descricao": "Lakers [LAL Lakers v CHI Bulls]"},          # ok
        {"aposta": "ML", "descricao": "Lakers [LAL Lakers vs CHI Bulls]"},         # erro
        {"aposta": "Anytime", "descricao": "Mbappe - Primeiro Marcador"},          # aviso
    ]
    r = resumo_lote(rows)
    assert r["com_erro"] == 1
    assert r["com_aviso"] == 1
    assert len(r["exemplos"]) == 2
