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


def test_gabarito_cobre_os_formatos_reais_de_cada_casa():
    """Formatos conferidos contra os códigos que estão no banco em produção.

    A bet365 ficava de fora desde a s178 ("robô em obra") — e continuou fora depois que as
    s182→s189 estabilizaram o `[Código: BR…]`, deixando a conferência de cobertura DESLIGADA
    justamente na casa de maior lote. Desde a s194 o gabarito é uma regex genérica de marcador,
    então toda casa entra sem regex própria."""
    reais = {
        "Superbet":   "891L-YJ3VAH",
        "Betano":     "20675937607",
        "Pinnacle":   "3089350167",
        "BETesporte": "190989817",
        "Betfair":    "O/25146258/0001775",
        "KTO":        "12939510404",
        "Bet365":     "JR8714690761I",
    }
    for casa, cod in reais.items():
        assert codigos_do_texto(f"[Código: {cod}]\nData: 21/07/2026") == [cod], casa


def test_gabarito_ignora_marcador_vazio():
    """`[Código: ]` vazio é real: a bet365 emite assim quando o detalhe do bilhete não chegou.

    Ele NÃO pode virar gabarito — viraria um "faltante" que nunca volta, disparando repescagem
    à toa e reinserindo a linha (duplicata). Sem código, o bilhete simplesmente não é cobrado.
    """
    assert codigos_do_texto("[Código: ]\nData: 21/07/2026") == []
    assert codigos_do_texto("[Código:]\nData: 21/07/2026") == []
    assert codigos_do_texto("[Código: JR8714690761I]\n[Código: ]") == ["JR8714690761I"]


def test_gabarito_so_reconhece_marcador_em_inicio_de_linha():
    """A fronteira é a mesma do chunker (`_SUPERBET_SPLIT_RE`, início de linha). Marcador no
    meio de uma linha de descrição não é bilhete e não pode ser cobrado."""
    assert codigos_do_texto("Seleções: algo [Código: FALSO123] mais texto") == []


def test_codigos_do_texto_sem_marcador_e_vazio():
    # Prints / texto colado à mão: sem [Código:] não há gabarito → a conferência vira no-op.
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


# ── bet365 ponta a ponta (s194) ───────────────────────────────────────────────
# A bet365 ficou FORA da conferência da s179 até a s194: nenhuma regex reconhecia
# `JR8714690761I`, então o guarda contra chunk-que-some estava desligado na casa de maior
# lote (~110 bilhetes = 4 chunks; um chunk mudo levaria ~28 bilhetes em silêncio).
# Este teste trava a cadeia inteira com o texto REAL que o `formatTicketB3` emite —
# inclusive o `[Código: ]` VAZIO, que a bet365 produz quando o detalhe do bilhete não
# chegou e que NÃO pode virar faltante (viraria repescagem à toa + linha duplicada).

_B3_TEXTO = "\n\n".join([
    "[Código: JR8714690761I]\nData (encerramento): 21/07/2026\nStake: 50,00\nStatus: Ganho → W",
    "[Código: JR8714690762K]\nData (encerramento): 21/07/2026\nStake: 30,00\nStatus: Perdeu → L",
    "[Código: ]\nData (encerramento): 22/07/2026\nStake: 10,00\nStatus: Perdeu → L",
    "[Código: QR1560103381I]\nData (encerramento): 22/07/2026\nStake: 20,00\nStatus: Ganho → W",
])


def _tsv_b3(cods):
    linhas = [main._TSV_HEADER]
    for c in cods:
        linhas.append(f"21/07/2026\tFutebol\t\tBet365\tconta\tML\tdesc\t50,00\t2,00\tW\t{c}")
    return "```tsv\n" + "\n".join(linhas) + "\n```"


def test_cobertura_bet365_detecta_bilhete_que_sumiu():
    c = conferir_cobertura(_tsv_b3(["JR8714690761I", "QR1560103381I"]), _B3_TEXTO)
    # 3 esperados: o `[Código: ]` vazio não conta (não há o que cobrar sem código)
    assert c["esperados"] == 3
    assert c["faltantes"] == ["JR8714690762K"]


def test_cobertura_bet365_completa_nao_acusa_falta():
    c = conferir_cobertura(
        _tsv_b3(["JR8714690761I", "JR8714690762K", "QR1560103381I"]), _B3_TEXTO)
    assert c["esperados"] == 3 and c["faltantes"] == []


def test_repescagem_bet365_recorta_o_bloco_certo():
    recorte = main._blocos_dos_codigos(_B3_TEXTO, ["JR8714690762K"])
    assert recorte.count("[Código:") == 1
    assert "JR8714690762K" in recorte and "Stake: 30,00" in recorte
    assert "JR8714690761I" not in recorte


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
