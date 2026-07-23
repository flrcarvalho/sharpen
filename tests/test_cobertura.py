"""Regressão de COBERTURA da extração (sessão 179).

O bug real: `_extract_tsv_rows` devolve [] quando um chunk responde sem o bloco
```tsv. O pedaço inteiro some SEM erro e `chunks_falhos` (que só conta exceção) não
acusa. Numa extração Superbet de 61 bilhetes, 39 evaporaram e a tela mostrou
"✓ 22 novo(s)" — inclusive dois bilhetes abertos que já tinham liquidado e por isso
nunca foram atualizados.

O gabarito é determinístico: cada `[Código: …]` do texto-fonte vem do DOM/API, não da
IA. Estes testes travam a conferência (`conferir_cobertura`), o recorte dos blocos
faltantes (`_blocos_dos_codigos`) e a costura do TSV (`_set_tsv_rows`).

Mesmo boilerplate do test_ordem_bet365 (stub de `database` + chave dummy).
"""
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")

import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover - nunca chamado nos testes
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

import main  # noqa: E402
from repository import codigos_do_texto, codigos_do_tsv, conferir_cobertura  # noqa: E402


CODS = ["8901-QI2OFU", "890Q-QD7TUP", "891F-YWE4RL", "891J-YNUVM0"]


def _texto(cods=CODS):
    """Texto-fonte no formato que o robô da Superbet injeta (marcador no início da linha)."""
    blocos = []
    for c in cods:
        blocos.append(
            f"[Código: {c}]\nData: 21/07/2026\nStake: 800,00\nOdd total: 1,87\n"
            f"Status: win · retorno 1496,00\nSeleções (1):\n  • 21/07/2026 · A — B · ML @ 1,87"
        )
    return "\n\n".join(blocos)


def _tsv(cods):
    linhas = [main._TSV_HEADER]
    for c in cods:
        linhas.append(f"21/07/2026\tTênis\t\tSuperbet\tconta\tML\tdesc {c}\t800,00\t1,87\tW\t{c}")
    return "```tsv\n" + "\n".join(linhas) + "\n```\n\n## Notas Críticas\nNenhuma"


def _cods_do(text):
    return [r.split("\t")[10] for r in main._extract_tsv_rows(text)]


# ── gabarito de códigos ───────────────────────────────────────────────────────

def test_codigos_do_texto_em_ordem_sem_repetir():
    assert codigos_do_texto(_texto()) == CODS


def test_codigos_do_texto_sem_marcador_e_vazio():
    # Bet365 / prints: sem [Código:] não há gabarito → a conferência vira no-op.
    assert codigos_do_texto("[Bilhete Bet365]\nalgo aqui") == []
    assert codigos_do_texto(None) == []


def test_codigos_do_tsv_ignora_notas_e_linhas_curtas():
    assert codigos_do_tsv(_tsv(CODS)) == set(CODS)


# ── conferência ───────────────────────────────────────────────────────────────

def test_cobertura_completa_nao_acusa_falta():
    c = conferir_cobertura(_tsv(CODS), _texto())
    assert c["esperados"] == 4 and c["faltantes"] == []


def test_cobertura_pega_chunk_que_sumiu():
    """O caso real: metade dos bilhetes não voltou, sem nenhum erro no caminho."""
    c = conferir_cobertura(_tsv(CODS[:2]), _texto())
    assert c["esperados"] == 4
    assert c["faltantes"] == ["891F-YWE4RL", "891J-YNUVM0"]


def test_cobertura_sem_gabarito_e_no_op():
    c = conferir_cobertura(_tsv([]), "[Bilhete Bet365]\nsem codigo")
    assert c["esperados"] == 0 and c["faltantes"] == []


# ── recorte dos faltantes ─────────────────────────────────────────────────────

def test_blocos_dos_codigos_recorta_so_os_pedidos_inteiros():
    recorte = main._blocos_dos_codigos(_texto(), ["891J-YNUVM0"])
    assert "891J-YNUVM0" in recorte
    assert "8901-QI2OFU" not in recorte
    # bloco inteiro, não um fragmento
    assert "Seleções (1):" in recorte and "Stake: 800,00" in recorte


def test_blocos_dos_codigos_preserva_ordem_do_texto():
    recorte = main._blocos_dos_codigos(_texto(), ["891J-YNUVM0", "8901-QI2OFU"])
    assert recorte.index("8901-QI2OFU") < recorte.index("891J-YNUVM0")


# ── costura do TSV ────────────────────────────────────────────────────────────

def test_set_tsv_rows_troca_linhas_preservando_header_e_notas():
    novo = main._set_tsv_rows(_tsv(CODS[:1]), [
        f"21/07/2026\tTênis\t\tSuperbet\tconta\tML\tx\t800,00\t1,87\tW\t{c}" for c in CODS
    ])
    assert _cods_do(novo) == CODS
    assert "Data\tEsporte" in novo and "## Notas Críticas" in novo
    assert conferir_cobertura(novo, _texto())["faltantes"] == []


def test_set_tsv_rows_sem_bloco_tsv_no_op():
    assert main._set_tsv_rows("nada aqui", ["x"]) == "nada aqui"


# ── repescagem ponta a ponta (com a chamada ao modelo dublada) ────────────────

def _linha(c):
    return f"21/07/2026\tTênis\t\tSuperbet\tconta\tML\tdesc {c}\t800,00\t1,87\tW\t{c}"


def _dublar_repescagem(monkeypatch, devolve):
    async def _fake(system, texto, faltantes, modelo, instrucao_block):
        # o recorte tem de conter só os faltantes — o barato da repescagem depende disso
        recorte = main._blocos_dos_codigos(texto, faltantes)
        assert all(c in recorte for c in faltantes)
        assert not any(c in recorte for c in CODS if c not in faltantes)
        return [_linha(c) for c in devolve], {"input": 1, "output": 1, "cache_read": 0, "cache_write": 0}
    monkeypatch.setattr(main, "_repescar_faltantes", _fake)


def test_garantir_cobertura_repesca_e_ordena_oldest_first(monkeypatch):
    """Superbet (feed newest-first): o TSV final vai do mais ANTIGO para o mais NOVO.
    As linhas repescadas entram na posição certa, não empilhadas no fim."""
    import asyncio
    _dublar_repescagem(monkeypatch, CODS[2:])
    # o que sobreviveu ao combine: blocos 1 e 2, já invertidos (oldest→newest)
    parcial = main._set_tsv_rows(_tsv(CODS), [_linha(CODS[1]), _linha(CODS[0])])
    saida, cob, _ = asyncio.run(main._garantir_cobertura(
        [], parcial, _texto(), "modelo", {"type": "text", "text": "instrucao"}, True))
    assert cob["recuperados"] == 2 and cob["faltantes"] == []
    assert _cods_do(saida) == list(reversed(CODS))


def test_garantir_cobertura_no_op_quando_nada_falta(monkeypatch):
    import asyncio
    async def _nunca(*a, **k):  # pragma: no cover - garante que não repesca à toa
        raise AssertionError("não devia repescar com cobertura completa")
    monkeypatch.setattr(main, "_repescar_faltantes", _nunca)
    entrada = _tsv(CODS)
    saida, cob, _ = asyncio.run(main._garantir_cobertura(
        [], entrada, _texto(), "modelo", {"type": "text", "text": "i"}, True))
    assert saida == entrada and cob["faltantes"] == [] and cob["recuperados"] == 0


def test_garantir_cobertura_avisa_quando_repescagem_nao_traz_tudo(monkeypatch):
    """Repescagem é segunda chance, não garantia: o que não voltar tem de sair como falta."""
    import asyncio
    _dublar_repescagem(monkeypatch, [CODS[2]])   # devolve só um dos dois
    parcial = main._set_tsv_rows(_tsv(CODS), [_linha(CODS[1]), _linha(CODS[0])])
    _, cob, _ = asyncio.run(main._garantir_cobertura(
        [], parcial, _texto(), "modelo", {"type": "text", "text": "i"}, True))
    assert cob["recuperados"] == 1 and cob["faltantes"] == ["891J-YNUVM0"]
