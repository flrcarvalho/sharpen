"""Testes do modo cego (Fase 2 — casa sem manual extrai só com os masters globais).

build_system deve devolver os 6 masters + 1 bloco de casa QUANDO o CASA_*.md existe,
e só os 6 masters quando não existe (casa nova, desconhecida).
"""
from prompts import build_system


def test_casa_conhecida_inclui_manual():
    blocks = build_system("BET365")   # casas/CASA_BET365.md existe
    assert len(blocks) == 7           # 6 masters globais + 1 casa


def test_casa_desconhecida_modo_cego():
    blocks = build_system("OIOIOIBET_INEXISTENTE_123")
    assert len(blocks) == 6           # só os 6 masters — sem bloco de casa
    # o breakpoint de cache continua no último master global
    assert blocks[-1].get("cache_control") == {"type": "ephemeral"}
    assert all(b["type"] == "text" for b in blocks)


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
