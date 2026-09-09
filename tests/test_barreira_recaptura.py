"""Gate da barreira de recaptura (`docs/PLANO_BARREIRA_RECAPTURA.md`, Fase 0).

Os blocos abaixo são **capturas reais** da `sombra_rotulos` de produção, inclusive o
par antes/depois de uma liquidação da Novibet — que é o caso que a barreira EXISTE
para deixar passar.

O QUE ESTES TESTES **NÃO** COBREM, e é bom saber antes de confiar no verde:

  • **Não tocam o banco.** `blocos_conhecidos` e `registrar_blocos_vistos` são I/O e
    ficam de fora; aqui só a camada pura (`blocos_por_codigo`, `hash_bloco`,
    `triar_blocos`), que é onde mora a decisão.
  • **Não provam que filtrar é seguro** — na Fase 0 nada é filtrado. As três costuras
    do §6 do plano (cobertura, órfãs, lote vazio) só existem na Fase 1 e terão gate
    próprio.
  • **Não medem economia.** Isso é simulação e medição em produção, não teste.

`test_mutacao_*` é a prova exigida pelo CLAUDE.md: quebrar o código de propósito tem
de derrubar o caso.
"""
import sys

sys.path.insert(0, "app")

import repository  # noqa: E402

# ── Blocos reais (sombra de produção) ─────────────────────────────────────────

# O MESMO bilhete da Novibet, antes e depois de liquidar. Repare que não muda só o
# Status: a odd vai de potencial para `Retorno ÷ Stake`. É por isso que a chave é o
# bloco inteiro, e não o par (código, resultado).
NOVIBET_ABERTA = """[Código: 475962111]
Data: 27/08/2026
Stake: 162,50
Status: Em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd: 4,59666667
Retorno potencial: R$ 746,91 (POTENCIAL — a aposta não liquidou)
"""

NOVIBET_LIQUIDADA = """[Código: 475962111]
Data: 27/08/2026
Stake: 162,50
Status: Ganhou → W
Odd: 2,89666667 (= Retorno ÷ Stake)
Retorno: R$ 746,91
Liquidado em: 27/08/2026 10:10:57
"""

DOIS_BILHETES = """[Código: AAA111]
Stake: 100,00
Status: Ganho → W (retorno R$ 180,00)

[Código: BBB222]
Stake: 50,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
"""

SEM_CODIGO = """Stake: 100,00
Status: Ganho → W (retorno R$ 180,00)
"""


def _hashes(texto):
    return {c: repository.hash_bloco(b)
            for c, b in repository.blocos_por_codigo(texto).items()}


# ── Recorte dos blocos ───────────────────────────────────────────────────────


def test_recorta_um_bloco_por_codigo():
    blocos = repository.blocos_por_codigo(DOIS_BILHETES)
    assert set(blocos) == {"AAA111", "BBB222"}
    assert "180,00" in blocos["AAA111"]
    assert "180,00" not in blocos["BBB222"], "bloco vazou para o vizinho"


def test_texto_sem_codigo_nao_produz_bloco():
    """Print e casa sem marcador não têm chave. A barreira não os alcança, e é
    melhor devolver vazio do que inventar uma chave."""
    assert repository.blocos_por_codigo(SEM_CODIGO) == {}
    assert repository.blocos_por_codigo(None) == {}
    assert repository.blocos_por_codigo("") == {}


def test_teto_corta_o_bloco_mas_a_barreira_nao_usa_teto():
    """A sombra corta em 4000 para não guardar bilhete-monstro. A barreira NÃO corta:
    um byte diferente depois do teto é uma mudança que ela precisa enxergar."""
    longo = "[Código: X1]\n" + ("a" * 5000) + "FIM\n"
    assert len(repository.blocos_por_codigo(longo, teto=100)["X1"]) == 100
    assert repository.blocos_por_codigo(longo)["X1"].endswith("FIM\n")


# ── A decisão ────────────────────────────────────────────────────────────────


def test_bloco_identico_e_pulado():
    a_proc, ja_vistos = repository.triar_blocos(NOVIBET_ABERTA, _hashes(NOVIBET_ABERTA))
    assert not a_proc
    assert set(ja_vistos) == {"475962111"}


def test_bilhete_que_liquidou_volta_para_a_ia():
    """O caso de uso inteiro: extraí às 10h com a aposta aberta, extraio de novo às
    12h e ela liquidou. Tem de reprocessar."""
    a_proc, ja_vistos = repository.triar_blocos(
        NOVIBET_LIQUIDADA, _hashes(NOVIBET_ABERTA))
    assert set(a_proc) == {"475962111"}
    assert not ja_vistos


def test_codigo_nunca_visto_vai_para_a_ia():
    a_proc, ja_vistos = repository.triar_blocos(DOIS_BILHETES, {})
    assert set(a_proc) == {"AAA111", "BBB222"}
    assert not ja_vistos


def test_lote_misto_separa_os_dois_lados():
    """O caso do Feca: extração 1 com N bilhetes, extração 2 com os mesmos N mais os
    novos. Só os novos podem custar."""
    conhecidos = {"AAA111": _hashes(DOIS_BILHETES)["AAA111"]}
    a_proc, ja_vistos = repository.triar_blocos(DOIS_BILHETES, conhecidos)
    assert set(a_proc) == {"BBB222"}
    assert set(ja_vistos) == {"AAA111"}


def test_um_byte_diferente_ja_reprocessa():
    """Na dúvida, processa. O modo de falha aceitável é 'custou dinheiro'; o
    inaceitável é 'deixou de gravar mudança'."""
    mudado = NOVIBET_ABERTA.replace("Stake: 162,50", "Stake: 162,51")
    a_proc, _ = repository.triar_blocos(mudado, _hashes(NOVIBET_ABERTA))
    assert set(a_proc) == {"475962111"}


def test_hash_nao_levanta_em_bloco_estranho():
    """A barreira roda no caminho da extração: bloco com byte solto tem de gerar UM
    hash estável, nunca uma exceção."""
    assert repository.hash_bloco(None) == repository.hash_bloco("")
    assert len(repository.hash_bloco("\udcff bloco torto")) == 40


# ── Prova por mutação ────────────────────────────────────────────────────────


def test_liquidar_mexe_em_mais_de_um_campo_mutacao_inocua_registrada():
    """**Mutação INÓCUA, registrada em vez de disfarçada** (CLAUDE.md manda registrar a
    diferença, não inventar asserção para ela).

    Cegar o hash à linha de `Status:` — que é o que uma chave por (código, resultado)
    faz implicitamente quando o rótulo não muda — **não** derruba este caso. E o
    motivo é o argumento central do plano: liquidar não mexe só no status, mexe na odd
    junto (potencial → `Retorno ÷ Stake`). O caso fica aqui para que ninguém conclua,
    do verde, que normalizar o bloco antes de hashear é seguro: é seguro NESTE
    bilhete, e os 154 blocos medidos na s334 que mudaram com o `Status:` igual provam
    que não é seguro no geral."""
    import re
    original = repository.hash_bloco
    try:
        repository.hash_bloco = lambda b: original(
            re.sub(r"(?m)^Status:.*$", "", b or ""))
        a_proc, ja_vistos = repository.triar_blocos(
            NOVIBET_LIQUIDADA, {"475962111": repository.hash_bloco(
                repository.blocos_por_codigo(NOVIBET_ABERTA)["475962111"])})
        # Mesmo cego ao Status ele ainda pega, porque a ODD mudou junto — e é
        # exatamente esse o argumento do plano: liquidar mexe em mais de um campo.
        assert set(a_proc) == {"475962111"}, (
            "com a odd mudando junto, nem o hash cego ao Status deveria pular")
    finally:
        repository.hash_bloco = original
    # restaurado = a triagem normal volta a funcionar
    assert repository.triar_blocos(NOVIBET_ABERTA, _hashes(NOVIBET_ABERTA))[1]


def test_mutacao_recorte_sem_marcador_derruba_tudo():
    """O recorte por `[Código: …]` é o que dá a chave. Sem ele não há barreira: todo
    bloco vira desconhecido e nada é pulado — caro, mas nunca errado."""
    import re
    original = repository._ID_MARCADOR_RE
    try:
        repository._ID_MARCADOR_RE = re.compile(r"^\[NADA:\s*([^\]]+?)\s*\]", re.M)
        assert repository.blocos_por_codigo(DOIS_BILHETES) == {}
        a_proc, ja_vistos = repository.triar_blocos(DOIS_BILHETES, {})
        assert not a_proc and not ja_vistos
    finally:
        repository._ID_MARCADOR_RE = original
    assert set(repository.blocos_por_codigo(DOIS_BILHETES)) == {"AAA111", "BBB222"}
