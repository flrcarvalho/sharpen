"""Gate do tradutor determinístico (`app/tradutor.py`, Fase 1 do plano).

Os blocos abaixo são **capturas reais**, copiadas verbatim da `sombra_rotulos` de
produção (28/08/2026) — inclusive os defeitos de forma que a casa entrega, como o espaço
duplo em `Mais de  2.5` e o placar ao vivo prefixando a seleção. Sintetizar bloco aqui
seria testar o que eu imagino que a casa manda, não o que ela manda.

O QUE ESTES TESTES **NÃO** COBREM, e é bom saber antes de confiar no verde:

  • **Não provam que o tradutor concorda com a IA.** Isso é medição contínua, não teste:
    `python scripts/diff_tradutor.py Bet365` roda contra a sombra inteira e é o que
    alimenta o gate da Fase 3 (< 1% de divergência em >= 500 bilhetes).
  • **Não cobrem odd, stake, data nem resultado além da cópia literal.** Onde a odd exige
    aritmética, o tradutor cai no fallback de propósito (ver o cabeçalho do módulo).
  • **Não cobrem casa nenhuma além da Bet365** — não há outra portada.

`test_mutacao_*` é a prova exigida pelo CLAUDE.md ("teste verde não é teste que detecta"):
tirar a entrada do mapa tem de derrubar o caso, e não derrubar nada é o defeito.
"""
import copy
import sys

sys.path.insert(0, "app")

import tradutor  # noqa: E402

# ── Blocos reais (sombra de produção, 28/08/2026) ─────────────────────────────

SIMPLES_ML = """
Data (encerramento): 27/08/2026
Stake: 300,00
Status: Perdeu → L
Odd: 1,9090909090909092
Esporte (casa): CL=1 (Futebol)
Seleções:
  • Estudiantes x Barracas Central · Resultado Final · Estudiantes @ 1,9090909090909092 · ARG-CUP
"""

SIMPLES_TOTAL_GOLS = """
Data (encerramento): 27/08/2026
Stake: 150,00
Status: Ganho → W (retorno R$ 262,50)
Odd: 1,75
Esporte (casa): CL=1 (Futebol)
Seleções:
  • Alajuelense x Plaza Amador · Total de Gols · Mais de  2.5 @ 1,75 · CONCACAFAC
"""

EBASKET = """
Data (encerramento): 27/08/2026
Stake: 200,87
Status: Perdeu → L
Odd: 1,8333333333333335
Esporte (casa): CL=18 (Basquete)
Seleções:
  • DEN Nuggets (KOBRA) @ ORL Magic (INVINCIBLE) · Total - 2 Opções · Mais de 98.5 @ 1,8333333333333335 · B-EBASKBLITZ4X5
"""

HANDICAP_AO_VIVO = """
Data (encerramento): 27/08/2026
Stake: 100,00
Status: Ganho → W (retorno R$ 177,50)
Odd: 1,775
Esporte (casa): CL=1 (Futebol)
Seleções:
  • Aldosivi x Independiente Rivadavia · Ao-Vivo - Handicap Asiático · (0-0) Independiente Rivadavia -0.5,-1.0 @ 1,775 · ARG-CUP
"""

HANDICAP_SETS = """
Data (encerramento): 27/08/2026
Stake: 120,00
Status: Perdeu → L
Odd: 2,25
Esporte (casa): CL=91 (Vôlei)
Seleções:
  • EUA vs República Dominicana · Handicap do Jogo (Sets) · EUA -1.5 @ 2,25 · VB-NORCECAFSCM
"""

PLAYER_PROP = """
Data (encerramento): 27/08/2026
Stake: 80,00
Status: Perdeu → L
Odd: 1,6896551724137931
Esporte (casa): CL=18 (Basquete)
Seleções:
  • TOR Tempo @ SEA Storm · Pontos (Mais de/Menos de) · Isabelle Harrison - Menos de 15.5 @ 1,6896551724137931 · WNBA
"""

SISTEMA_3_JOGOS = """
Data (encerramento): 27/08/2026
Stake: 90,36
Status: Ganho → W (retorno R$ 94,88)
Tipo: SISTEMA Duplas — 3 apostas de 2 seleção(ões), sobre 3 seleções · aposta unitária R$ 30,12 · total R$ 90,36 (a Stake acima é o TOTAL — é ela que vale)
Odd (estrutural do sistema): 3,2194444444444446  ← JÁ CALCULADA (média das 3 linhas).
Seleções:
  • Paulistano x Osasco · Totais do Jogo · Mais de 154.5 @ 1,8333333333333335 · B-BRFPB
  • Herediano x Antigua GFC · Gols + - · Mais de 2.0,2.5 @ 1,8 · CONCACAFAC
  • Alajuelense x Plaza Amador · Total de Gols · Mais de  2.5 @ 1,75 · CONCACAFAC
"""

# Cai no fallback de propósito: `Apostas no Set` não está no mapa. É o caso exigido pela
# regra "todo caso de casa portada precisa de uma linha que exercite o fallback".
MERCADO_DESCONHECIDO = """
Data (encerramento): 27/08/2026
Stake: 500,00
Status: Perdeu → L
Odd: 1,3
Esporte (casa): CL=13 (Tênis)
Seleções:
  • Cabezas Dominguez/Candiotto x Vidal/Mendonca · Apostas no Set · Para Cabezas Dominguez/Candiotto Ganhar 2 - 0 @ 1,3 · IWSWD-R2
"""


# ── Tradução ──────────────────────────────────────────────────────────────────


def test_ml_simples():
    t = tradutor.traduzir("BET365", SIMPLES_ML)
    assert t.ok, t.motivo
    assert t.esporte == "Futebol"
    assert t.aposta == "ML"
    assert t.descricao == "Estudiantes [Estudiantes v Barracas Central]"
    assert t.resultado == "L"
    assert t.stake == "300,00"
    assert t.odd == "1,9090909090909092"   # precisão completa, verbatim


def test_total_de_gols_normaliza_over_e_espaco_duplo():
    # `Mais de  2.5` (dois espaços) é como a casa manda. A normalização Over/Under é
    # OBRIGATÓRIA (`MASTER_DESCRICAO §11`) — e é justamente onde a sombra flagrou a IA
    # deixando `Mais de` em 5 bilhetes de eBasket.
    t = tradutor.traduzir("BET365", SIMPLES_TOTAL_GOLS)
    assert t.ok, t.motivo
    assert t.aposta == "Gols"
    assert t.descricao == "Over 2.5 Gols [Alajuelense v Plaza Amador]"


def test_ebasket_pelo_handle_dos_dois_lados():
    t = tradutor.traduzir("BET365", EBASKET)
    assert t.ok, t.motivo
    assert t.esporte == "eBasket", "handle do gamer nos dois lados = basquete virtual"
    assert t.aposta == "Pontos", "rótulo genérico segue o OBJETO do esporte"
    assert t.descricao == "Over 98.5 Pontos [DEN Nuggets (KOBRA) v ORL Magic (INVINCIBLE)]"


def test_handicap_ao_vivo_descarta_o_placar():
    t = tradutor.traduzir("BET365", HANDICAP_AO_VIVO)
    assert t.ok, t.motivo
    assert t.aposta == "Handicap", "`Ao-Vivo - ` é qualificador, não muda a categoria"
    assert t.descricao == (
        "Independiente Rivadavia -0.5,-1.0 [Aldosivi v Independiente Rivadavia]")


def test_handicap_de_sets_leva_a_unidade():
    t = tradutor.traduzir("BET365", HANDICAP_SETS)
    assert t.ok, t.motivo
    assert t.descricao == "EUA -1.5 Sets [EUA v República Dominicana]"


def test_player_prop_separa_jogador_do_mercado():
    t = tradutor.traduzir("BET365", PLAYER_PROP)
    assert t.ok, t.motivo
    assert t.aposta == "Player Props"
    assert t.descricao == "Isabelle Harrison - Under 15.5 Pontos [TOR Tempo v SEA Storm]"


def test_multipla_de_esportes_mistos_com_rotulo_generico_vai_para_a_ia():
    """O limite REAL do motor hoje, e ele é por desenho.

    `Totais do Jogo` é rótulo genérico: a categoria segue o objeto, e o objeto vem do
    esporte. Numa múltipla de esportes misturados o inject não emite `Esporte (casa)` —
    não há de onde tirar o objeto de CADA perna, e adivinhar pela linha do total
    (`154.5` "parece" basquete) seria exatamente o que este módulo não faz.

    Medido na sombra: das 69 capturas de Bet365, **nenhuma múltipla foi traduzida**. A
    cobertura de 84% é toda de bilhete de perna única."""
    t = tradutor.traduzir("BET365", SISTEMA_3_JOGOS)
    assert not t.ok
    assert "Totais do Jogo" in t.motivo


def test_tres_jogos_distintos_viram_multiplos():
    """A decisão de `Múltiplos` isolada, sobre as pernas REAIS do bilhete acima.

    Testada aqui na unidade porque ponta a ponta ela é inalcançável com a sombra de
    hoje (ver o teste anterior). Quando a primeira múltipla de rótulos mapeados
    aparecer, este teste vira ponta a ponta e o de cima muda de motivo."""
    pernas = tradutor._pernas(SISTEMA_3_JOGOS)
    assert len(pernas) == 3
    assert tradutor._esporte({}, pernas) == "Múltiplos", "MASTER_ESPORTES §2"


def test_familia_parametrizada_de_prop_de_jogador():
    """`Jogador - <objeto> - Alternativas` é FAMÍLIA, não linha de tabela: a categoria
    vem do §9 e o objeto sai do próprio rótulo, verbatim e com a caixa da casa. Perna
    real (`Nico O'Reilly`, Crystal Palace × Man City, 28/08).

    Ela ainda não aparece na cobertura: o único bilhete que a contém traz junto um
    `2º Tempo - Cartões - 3 Opções`, que segue desconhecido, e o bilhete inteiro cai no
    fallback — que é o comportamento certo (fallback é por bilhete, não por perna)."""
    p = tradutor.Perna("Crystal Palace x Man City",
                       "Jogador - Faltas Cometidas - Alternativas",
                       "Nico O'Reilly - Mais de 0.5", "1,90", "ENG-PREM")
    spec = tradutor._spec(tradutor._MERCADOS_BET365, p.mercado, "Futebol")
    assert spec is not None and spec["cat"] == "Player Props"
    assert tradutor._descricao_perna(p, spec) == (
        "Nico O'Reilly - Over 0.5 Faltas Cometidas [Crystal Palace v Man City]")


def test_familia_parametrizada_depois_do_qualificador():
    """Qualificador sai ANTES da família, não só antes da tabela. Sem isso, o mesmo
    prop de jogador ao vivo cairia na IA e o de pré-jogo não — mesma aposta, custo
    diferente conforme a hora. (Rótulo composto CONSTRUÍDO: a sombra ainda não trouxe
    um prop de jogador ao vivo; os dois pedaços são reais e o §9 lista os dois.)"""
    spec = tradutor._spec(tradutor._MERCADOS_BET365,
                          "Ao-Vivo - Jogador - Faltas Cometidas - Alternativas", "Futebol")
    assert spec is not None and spec["objeto"] == "Faltas Cometidas"


def test_familia_parametrizada_nao_engole_rotulo_de_outra_casa():
    """A regra é do mapa da Bet365 e não pode vazar para casa nenhuma — `_spec` só
    consulta as famílias quando o mapa É o da Bet365."""
    assert tradutor._spec({}, "Jogador - Faltas Cometidas", "Futebol") is None


def test_bet_builder_nao_e_multiplos():
    """A outra metade da regra, e a que a mutação pegou faltando: 3+ pernas do MESMO
    confronto é bet builder, e bet builder usa o esporte do jogo, NUNCA `Múltiplos`
    (`MASTER_ESPORTES §2` e §16). Contar pernas em vez de confrontos distintos passava
    verde na suíte inteira até este caso existir.

    ⚠️ ÚNICO caso CONSTRUÍDO deste arquivo. A sombra ainda não capturou um bet builder
    de Bet365 (`Criar Aposta`) e o golden set também não tem — inventar o bloco inteiro
    seria testar a casa que eu imagino. Aqui só as três pernas são montadas, com jogo e
    rótulos que existem no mapa; troque por captura real assim que houver uma."""
    jogo = "Estudiantes x Barracas Central"
    pernas = [
        tradutor.Perna(jogo, "Resultado Final", "Estudiantes", "1,90", "ARG-CUP"),
        tradutor.Perna(jogo, "Total de Gols", "Mais de 2.5", "1,75", "ARG-CUP"),
        tradutor.Perna(jogo, "Escanteios Asiáticos", "Menos de 7.5", "1,67", "ARG-CUP"),
    ]
    cab = {"Esporte (casa)": "CL=1 (Futebol)"}
    assert tradutor._esporte(cab, pernas) == "Futebol"


def test_multipla_traduz_quando_todos_os_rotulos_sao_conhecidos():
    """Mesmo bilhete real, com o rótulo genérico resolvido à mão para o que ele
    significa NAQUELA perna (`Totais do Jogo` de basquete = Pontos). Isso alcança o
    caminho da múltipla — junção por ` // `, categoria `Múltipla` e a odd do SISTEMA,
    que é a MÉDIA das linhas e vem pronta da casa (s265)."""
    original = copy.deepcopy(tradutor._MERCADOS_BET365)
    try:
        tradutor._MERCADOS_BET365["totais do jogo"] = {"cat": "Pontos", "objeto": "Pontos"}
        t = tradutor.traduzir("BET365", SISTEMA_3_JOGOS)
        assert t.ok, t.motivo
        assert t.esporte == "Múltiplos"
        assert t.aposta == "Múltipla"
        assert t.descricao == (
            "Over 154.5 Pontos [Paulistano v Osasco] // "
            "Over 2.0,2.5 Gols [Herediano v Antigua GFC] // "
            "Over 2.5 Gols [Alajuelense v Plaza Amador]")
        assert t.odd == "3,2194444444444446"
    finally:
        tradutor._MERCADOS_BET365.clear()
        tradutor._MERCADOS_BET365.update(original)


# ── Fallback: recusar é resposta certa, não falha ─────────────────────────────


def test_mercado_fora_do_mapa_vai_para_a_ia():
    t = tradutor.traduzir("BET365", MERCADO_DESCONHECIDO)
    assert not t.ok
    assert "Apostas no Set" in t.motivo, "o motivo tem de nomear o rótulo, não só contar"


def test_casa_nao_portada_vai_para_a_ia():
    t = tradutor.traduzir("BETANO", SIMPLES_ML)
    assert not t.ok and "não portada" in t.motivo


def test_sem_esporte_declarado_vai_para_a_ia():
    bloco = SIMPLES_ML.replace("Esporte (casa): CL=1 (Futebol)\n", "")
    t = tradutor.traduzir("BET365", bloco)
    assert not t.ok and "esporte" in t.motivo


def test_multipla_sem_odd_combinada_vai_para_a_ia():
    """Múltipla sem linha de odd: a casa não entrega a combinada e o tradutor NÃO
    multiplica as pernas (cabeçalho do módulo — aritmética de odd é outro incremento,
    com gate próprio). O rótulo genérico é resolvido como no teste acima, senão o
    bilhete cairia antes, por outro motivo, e este guard nunca seria exercido."""
    original = copy.deepcopy(tradutor._MERCADOS_BET365)
    try:
        tradutor._MERCADOS_BET365["totais do jogo"] = {"cat": "Pontos", "objeto": "Pontos"}
        bloco = SISTEMA_3_JOGOS.replace(
            "Odd (estrutural do sistema): 3,2194444444444446"
            "  ← JÁ CALCULADA (média das 3 linhas).\n", "")
        t = tradutor.traduzir("BET365", bloco)
        assert not t.ok and "odd" in t.motivo
    finally:
        tradutor._MERCADOS_BET365.clear()
        tradutor._MERCADOS_BET365.update(original)


# ── Prova por mutação ────────────────────────────────────────────────────────


def test_mutacao_remover_entrada_do_mapa_derruba_o_caso():
    """Tirar `total de gols` do mapa tem de mandar o bilhete para a IA. Se este teste
    passar verde com a entrada removida, o mapa não é o que decide — e todo o resto da
    suíte estaria medindo outra coisa."""
    original = copy.deepcopy(tradutor._MERCADOS_BET365)
    try:
        del tradutor._MERCADOS_BET365["total de gols"]
        t = tradutor.traduzir("BET365", SIMPLES_TOTAL_GOLS)
        assert not t.ok, "mapa mutilado e o tradutor traduziu assim mesmo"
        assert "Total de Gols" in t.motivo
    finally:
        tradutor._MERCADOS_BET365.clear()
        tradutor._MERCADOS_BET365.update(original)
    # restaurado = verde de novo (a outra metade da prova)
    assert tradutor.traduzir("BET365", SIMPLES_TOTAL_GOLS).ok


def test_mutacao_handle_de_um_lado_so_nao_e_ebasket():
    """O eBasket exige handle nos DOIS lados. Tirando o de um lado, o bilhete tem de
    voltar a ser Basquete — senão `Canadá (F) v EUA (F)` viraria eBasket."""
    bloco = EBASKET.replace("ORL Magic (INVINCIBLE)", "ORL Magic")
    t = tradutor.traduzir("BET365", bloco)
    assert t.ok, t.motivo
    assert t.esporte == "Basquete"
