"""Testes do modo cego (Fase 2 — casa sem manual extrai só com os masters globais).

build_system deve devolver os 6 masters + 1 bloco de casa QUANDO o CASA_*.md existe,
e só os 6 masters quando não existe (casa nova, desconhecida).
"""
from prompts import build_system, _CACHE_TTL


def test_casa_conhecida_inclui_manual():
    blocks = build_system("BET365")   # casas/CASA_BET365.md existe
    assert len(blocks) == 7           # 6 masters globais + 1 casa


def test_casa_desconhecida_modo_cego():
    blocks = build_system("OIOIOIBET_INEXISTENTE_123")
    assert len(blocks) == 6           # só os 6 masters — sem bloco de casa
    # O breakpoint de cache continua no último master global. Compara com `_CACHE_TTL`,
    # a ÚNICA declaração do TTL — literal aqui duplicaria a fonte de verdade e faria este
    # teste (que fala de modo cego) quebrar toda vez que o TTL mudasse. Que o TTL seja o
    # certo é assunto do `test_cache_ttl_e_preco_andam_juntos` abaixo.
    assert blocks[-1].get("cache_control") == _CACHE_TTL
    assert all(b["type"] == "text" for b in blocks)


# ── TTL do cache e preço do cache_write são UM par (s295) ────────────────────
# O prompt de sistema (44.593 tokens de masters + o arquivo da casa) é relido uma vez por
# chunk: era 46% da fatura da API. O TTL passou de 5 min para 1h, e a escrita a 1h custa
# 2× a base em vez de 1,25×. Se alguém mexer num sem mexer no outro, o log de custo mente
# — e é ele que decide a fila de casas do tradutor determinístico. Este teste é o que
# impede a dupla de se separar em silêncio.
from repository import _PRECOS   # noqa: E402


def test_cache_ttl_e_preco_andam_juntos():
    assert _CACHE_TTL == {"type": "ephemeral", "ttl": "1h"}, (
        "TTL mudou: revise _PRECOS['cache_write'] junto (5m = 1,25× a base, 1h = 2×)"
    )
    for modelo, p in _PRECOS.items():
        assert p["cache_write"] == p["input"] * 2, (
            f"{modelo}: cache_write deve ser 2× o input (TTL de 1h), não "
            f"{p['cache_write']} para input {p['input']}"
        )
        # A leitura é 0,1× a base nos dois TTLs — não se move com esta mudança.
        assert abs(p["cache_read"] - p["input"] * 0.1) < 1e-9


def test_todo_breakpoint_de_cache_usa_o_mesmo_ttl():
    """Nenhum bloco pode ficar com o TTL padrão de 5 min por esquecimento.

    Vale para os dois modos: com manual de casa (2 breakpoints) e cego (1).
    """
    for casa in ("BET365", "SUPERBET", "OIOIOIBET_INEXISTENTE_123"):
        marcados = [b for b in build_system(casa) if "cache_control" in b]
        assert marcados, f"{casa}: nenhum breakpoint de cache"
        for b in marcados:
            assert b["cache_control"] == _CACHE_TTL, f"{casa}: breakpoint fora do TTL único"


# ── Nome de casa de modo cego não pode ser mutilado ──────────────────────────
# Regressão (sessão 141): "Esportiva Bet" (casa cega, 2 palavras, sem CASA_*.md)
# tinha o espaço removido e era title-caseada no round-trip de nome de casa do
# /salvar → virava "Esportivabet" e caía numa CONTA PARALELA. O lote extraído
# "sumia" (ficava numa casa com grafia diferente da que o operador vê).
from main import _casa_display, _display_to_key   # noqa: E402


def test_roundtrip_casa_cega_preserva_nome_verbatim():
    # O round-trip _casa_display(_display_to_key(x)) tem de ser IDENTIDADE para
    # qualquer casa fora do mapa canônico — espaço e caixa intactos.
    for nome in [
        "Esportiva Bet",   # 2 palavras: o espaço não pode sumir
        "Rei do Pitaco",   # 3 palavras: o "do" não pode virar "Do"
        "Faz1 Bet",
        "Multibet",
        "beGamble",        # caixa intencional preservada
    ]:
        assert _casa_display(_display_to_key(nome)) == nome, nome


def test_roundtrip_casa_mapeada_canonicaliza():
    # Casas do mapa continuam normalizando p/ a grafia oficial, venha como vier.
    assert _casa_display(_display_to_key("bolsa de aposta")) == "Bolsa de Aposta"
    assert _casa_display(_display_to_key("BETESPORTE")) == "BETesporte"
    assert _casa_display(_display_to_key("betano")) == "Betano"


def test_roundtrip_idempotente():
    # Aplicar o round-trip 2x não pode mudar mais nada (sem deriva de grafia).
    for nome in ["Esportiva Bet", "Rei do Pitaco", "Betano", "Bolsa de Aposta"]:
        uma = _casa_display(_display_to_key(nome))
        duas = _casa_display(_display_to_key(uma))
        assert uma == duas, nome
