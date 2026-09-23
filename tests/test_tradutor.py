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


SIMPLES_TOTAL_GOLS_PARTIDA = """
Data (encerramento): 05/09/2026
Stake: 99,00
Status: em aberto (aguardando resultado)
Odd: 1,8
Esporte (casa): CL=1 (Futebol)
Seleções:
  • Auckland United (F) x Fencibles United (F) · Gols + - · Mais de 4.0,4.5 @ 1,8 · NZL
"""


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
    # `-0.5,-1.0` é handicap asiático PARTIDO, e vira o quarto de linha `-0.75`
    # (`MASTER_DESCRICAO §10.1.1`, s336). **Esta linha do teste mudou junto com a regra.**
    # Este bloco é a prova de que o caso com SINAL não é hipotético: ele é uma captura
    # real, e há 3 dele em 15.907 blocos da sombra.
    assert t.descricao == (
        "Independiente Rivadavia -0.75 [Aldosivi v Independiente Rivadavia]")


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
    assert tradutor._esporte("BET365", {}, pernas) == "Múltiplos", "MASTER_ESPORTES §2"


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
    assert tradutor._esporte("BET365", cab, pernas) == "Futebol"


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
        # A 2ª perna vem do bloco como `Mais de 2.0,2.5` e sai como `Over 2.25`:
        # `MASTER_DESCRICAO §10.1.1`, fechado na s336. **Esta linha do teste mudou junto
        # com a regra** — antes ela cobrava `Over 2.0,2.5 Gols`. Motivo medido: a Bet365
        # é a única casa que manda as duas linhas; as outras 21 já mandam `2,25`.
        assert t.descricao == (
            "Over 154.5 Pontos [Paulistano v Osasco] // "
            "Over 2.25 Gols [Herediano v Antigua GFC] // "
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


# ── Sufixo `- N Opções` e os rótulos medidos na sombra de 09/09 (s333) ────────
#
# Blocos reais da `sombra_rotulos`, como os de cima. O `\r\n` original é artefato de
# transporte e `splitlines()` o normaliza, então aqui vão com `\n` só.

ESCANTEIOS_2_OPCOES = """
Data (encerramento): 05/09/2026
Stake: 300,00
Status: Devolvida/void (retorno = stake) → V
Odd: 1,8
Esporte (casa): CL=1 (Futebol)
Seleções:
  • Deutschlandsberger SC x LASK Linz · Escanteios - 2 Opções · Menos de 10.5 @ 1,8 · Austrian Cup
"""

TOTAL_2_OPCOES_EBASKET = """
Data (encerramento): 26/08/2026
Stake: 200,87
Status: Ganho → W (retorno R$ 368,27)
Odd: 1,8333333333333335
Esporte (casa): CL=18 (Basquete)
Seleções:
  • NY Knicks (JACKAL) @ OKC Thunder (CURSE) · Total - 2 Opções · Mais de 105.5 @ 1,8333333333333335 · B-EBASKBLITZ4X5
"""

FALTA_DO_JOGADOR = """
Data (encerramento): 01/09/2026
Stake: 200,00
Status: Devolvida/void (retorno = stake) → V
Odd: 4,5
Esporte (casa): CL=1 (Futebol)
Seleções:
  • Atlético-MG x Cruzeiro · Para Sofrer Falta · Maycon Barberan - Mais de 1.5 @ 4,5 · Copa do Brasil
"""


def test_sufixo_opcoes_nao_muda_a_categoria():
    """`- 2 Opções` conta as SAÍDAS do mercado (com ou sem empate), não do que ele
    trata. `Escanteios - 2 Opções` tem de resolver pela entrada `escanteios`."""
    t = tradutor.traduzir("BET365", ESCANTEIOS_2_OPCOES)
    assert t.ok, t.motivo
    assert t.aposta == "Escanteios"
    assert t.descricao == "Under 10.5 Escanteios [Deutschlandsberger SC v LASK Linz]"


def test_rotulo_inteiro_vence_o_corte_do_sufixo():
    """`Total - 2 Opções` está no mapa POR INTEIRO. Se o corte do sufixo rodasse antes
    da consulta, a chave viraria `total`, que não existe, e este bilhete cairia no
    fallback — 498 blocos da sombra de uma vez. O corte é a última tentativa.

    De quebra este bloco cobre a arroba no NOME do jogo (`NY Knicks (JACKAL) @ OKC
    Thunder (CURSE)`, formato americano) junto com a arroba da odd."""
    t = tradutor.traduzir("BET365", TOTAL_2_OPCOES_EBASKET)
    assert t.ok, t.motivo
    assert t.esporte == "eBasket"
    assert t.aposta == "Pontos"
    assert t.descricao == "Over 105.5 Pontos [NY Knicks (JACKAL) v OKC Thunder (CURSE)]"


def test_falta_sofrida_e_prop_com_objeto():
    """`Para Sofrer Falta` traz jogador e linha na mesma seleção; o objeto `Faltas`
    fecha a descrição."""
    t = tradutor.traduzir("BET365", FALTA_DO_JOGADOR)
    assert t.ok, t.motivo
    assert t.aposta == "Faltas"
    assert t.descricao == "Maycon Barberan - Over 1.5 Faltas [Atlético-MG v Cruzeiro]"


def test_mutacao_o_corte_do_sufixo_e_o_ultimo_recurso():
    """A prova da ORDEM, que nenhum dos testes acima sozinho dá: sem a entrada inteira
    `total - 2 opções`, o corte do sufixo não salva o bilhete (a chave `total` não
    existe no mapa). Verde aqui com a entrada removida significaria que quem resolve é
    o corte, e aí `Total - 2 Opções` viraria refém de uma entrada que ninguém escreveu."""
    original = copy.deepcopy(tradutor._MERCADOS_BET365)
    try:
        del tradutor._MERCADOS_BET365["total - 2 opções"]
        t = tradutor.traduzir("BET365", TOTAL_2_OPCOES_EBASKET)
        assert not t.ok, "mapa mutilado e o corte do sufixo traduziu assim mesmo"
        assert "Total - 2 Opções" in t.motivo
    finally:
        tradutor._MERCADOS_BET365.clear()
        tradutor._MERCADOS_BET365.update(original)
    assert tradutor.traduzir("BET365", TOTAL_2_OPCOES_EBASKET).ok


def test_mutacao_remover_escanteios_derruba_o_sufixo_opcoes():
    """O espelho do de cima: aqui quem resolve É o corte do sufixo, então tirar a
    entrada-base `escanteios` tem de derrubar `Escanteios - 2 Opções` junto."""
    original = copy.deepcopy(tradutor._MERCADOS_BET365)
    try:
        del tradutor._MERCADOS_BET365["escanteios"]
        t = tradutor.traduzir("BET365", ESCANTEIOS_2_OPCOES)
        assert not t.ok, "entrada-base removida e o tradutor traduziu assim mesmo"
    finally:
        tradutor._MERCADOS_BET365.clear()
        tradutor._MERCADOS_BET365.update(original)
    assert tradutor.traduzir("BET365", ESCANTEIOS_2_OPCOES).ok


# ── A múltipla de 2 pernas: o esporte vem do `Tipo:` (s383) ──────────────────
#
# Blocos reais da sombra (23/09/2026). A Bet365 não escreve `Esporte (casa):` em
# múltipla, e o veredito do `MASTER_ESPORTES §2` fica na linha `Tipo: Múltipla`, que o
# `formatTicketB3` só emite sob `jogos.size >= 3 || cls.length > 1`.

MULTIPLA_DOIS_ESPORTES = """
Data (encerramento): 03/09/2026
Stake: 201,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Tipo: Múltipla (2 seleções)
Seleções:
  • Puerto Montt x CSD Colo Colo · Para Ganhar · CSD Colo Colo @ 2,85 · B-CHLNBM
  • Al Feiha x Al Kholood · 1° Tempo - Escanteios · Mais de 4.0 @ 2,5 · SAUDI-PREM
"""

# `RT7832775711I`, o ramo `else if (nSel > 1)` do `formatTicketB3`: a casa diz
# explicitamente que NÃO é múltipla pelo §2 (2 jogos, 1 CL só). São dois jogos de MLB —
# mesmo esporte —, e o `CL=16` não tem nome no `_CL_B3` (é basquete não mapeado, ver o
# comentário lá), então o esporte fica indecidível e o bilhete vai para a IA. Marcar
# `Múltiplos` aqui seria o erro que o conjunto por casa existe para evitar.
DUAS_SELECOES_SEM_VEREDITO = """
Data (encerramento): 03/09/2026
Stake: 201,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Tipo: 2 seleções — a odd do bilhete é o PRODUTO das odds abaixo (a casa não entrega a odd combinada). Em bilhete ganho vale Retorno ÷ Aposta (MASTER_RESULTADO §7.1).
Esporte (casa): CL=16
Seleções:
  • SF Giants @ PIT Pirates · Lançador - Strikeouts · Lake Bachar: 3+ Strikeouts @ 2,9 · MLB
  • BOS Red Sox @ BAL Orioles · Total de Bases · Caleb Durbin: 2+ Total de Bases @ 2,85 · MLB
"""


def test_multipla_de_2_pernas_tira_o_esporte_do_tipo():
    """A decisão isolada. Duas pernas, dois confrontos: a regra dos 3+ NÃO alcança, e
    quem responde é o `Tipo: Múltipla` — que nesta casa só existe quando a extensão já
    aplicou o §2. Medido em 23/09 sobre 1.295 blocos julgáveis por um mapa liga→esporte
    independente da IA: 1.295 de 1.295 têm as duas pernas em esportes diferentes."""
    cab = tradutor._cabecalho(MULTIPLA_DOIS_ESPORTES)
    pernas = tradutor._pernas(MULTIPLA_DOIS_ESPORTES)
    assert len(pernas) == 2 and len({p.confronto for p in pernas}) == 2
    assert tradutor._esporte("BET365", cab, pernas) == "Múltiplos"


def test_o_veredito_do_tipo_e_por_CASA_nunca_global():
    """`formatTicketNV`, `formatTicketRG`, `formatTicket1X` e `formatTicketPN` também
    escrevem `Tipo: Múltipla`, mas por `n > 1` — contagem de pernas, não o §2. Numa
    dessas, a mesma linha num bilhete de 2 jogos do MESMO esporte viraria `Múltiplos`,
    que o §2 proíbe. O conjunto é a trava, e este teste é o que impede alguém de
    'simplificar' tirando a checagem de casa."""
    cab = tradutor._cabecalho(MULTIPLA_DOIS_ESPORTES)
    pernas = tradutor._pernas(MULTIPLA_DOIS_ESPORTES)
    assert tradutor._esporte("NOVIBET", cab, pernas) is None
    assert tradutor._esporte("PINNACLE", cab, pernas) is None


def test_tipo_N_selecoes_nao_e_veredito_de_multiplos():
    """A outra metade, e a que separa o veredito da CONTAGEM: `Tipo: 2 seleções` é o
    ramo em que a extensão diz explicitamente que não é múltipla pelo §2. Bloco real
    com dois jogos de MLB — mesmo esporte — e `CL=16` sem nome. Tem de ir para a IA."""
    cab = tradutor._cabecalho(DUAS_SELECOES_SEM_VEREDITO)
    pernas = tradutor._pernas(DUAS_SELECOES_SEM_VEREDITO)
    assert len(pernas) == 2
    assert tradutor._esporte("BET365", cab, pernas) is None
    t = tradutor.traduzir("BET365", DUAS_SELECOES_SEM_VEREDITO)
    assert not t.ok and "esporte" in t.motivo


def test_o_motivo_do_fallback_passa_a_ser_o_VERDADEIRO():
    """Ponta a ponta, e é o que esta mudança realmente entrega. O bilhete continua indo
    para a IA — `Para Ganhar` não está no mapa —, mas deixa de ir com o motivo FALSO
    'esporte não declarado' para um bilhete cujo esporte o tradutor sabe decidir.

    Era esse rótulo errado que fazia a múltipla parecer um problema de formato: medido
    em 23/09, dos 2.949 blocos que ele libertava, 89,1% param no rótulo seguinte."""
    t = tradutor.traduzir("BET365", MULTIPLA_DOIS_ESPORTES)
    assert not t.ok
    assert "esporte" not in t.motivo, "o motivo antigo era falso e não pode voltar"
    assert "Para Ganhar" in t.motivo


def test_mutacao_tirar_a_bet365_do_conjunto_devolve_o_motivo_falso():
    """A prova exigida pelo CLAUDE.md. Sem a casa no conjunto, o bloco tem de voltar a
    cair por 'esporte não declarado' — verde aqui com o conjunto vazio significaria que
    quem decide é outra coisa, e a entrada não estaria sustentando nada."""
    original = frozenset(tradutor._TIPO_MULTIPLA_E_VEREDITO)
    try:
        tradutor._TIPO_MULTIPLA_E_VEREDITO = frozenset()
        t = tradutor.traduzir("BET365", MULTIPLA_DOIS_ESPORTES)
        assert not t.ok, "conjunto vazio e o tradutor decidiu o esporte assim mesmo"
        assert "esporte não declarado" in t.motivo
    finally:
        tradutor._TIPO_MULTIPLA_E_VEREDITO = original
    assert "Para Ganhar" in tradutor.traduzir("BET365", MULTIPLA_DOIS_ESPORTES).motivo


def test_mutacao_o_veredito_nao_atropela_o_esporte_declarado():
    """A ordem é load-bearing: o `Esporte (casa):` da casa manda, e o `Tipo:` só entra
    quando ele falta. Um bloco com os dois (não existe na Bet365, mas o código não
    sabe disso) tem de sair com o esporte declarado, nunca com `Múltiplos`."""
    cab = tradutor._cabecalho(MULTIPLA_DOIS_ESPORTES)
    cab["Esporte (casa)"] = "CL=1 (Futebol)"
    pernas = tradutor._pernas(MULTIPLA_DOIS_ESPORTES)
    assert tradutor._esporte("BET365", cab, pernas) == "Futebol"


# ── A odd estrutural da múltipla comum: o produto das pernas (s386) ──────────
#
# A Bet365 não publica a odd combinada — ZERO de 3.442 blocos `Tipo: Múltipla` traz
# linha de odd (medido em 23/09). O `MASTER_RESULTADO §7.1` diz quando a resposta é a odd
# ESTRUTURAL e o §7.2 diz o que ela é: o produto. Blocos reais da sombra.

MULTIPLA_L_TRES_PERNAS = """
Data (evento): 13/09/2026
Stake: 30,32
Status: Perdeu → L
Tipo: Múltipla (3 seleções)
Seleções:
  • RAMS Village Superstars x Cayon · Gols + - · Menos de 2.5,3.0 @ 1,8 · SKITTS-NEV-PREM
  • Cieza x Elche Ilicitano · Gols + - · Mais de 2.0,2.5 @ 1,775 · Spain Seg B G3
  • Pontevedra B x Gran Pena · Total de Gols · Mais de  2.5 @ 1,7 · Spain Ter Grp1
"""

DUPLA_L_MESMO_ESPORTE = """
Data (encerramento): 27/08/2026
Stake: 750,00
Status: Perdeu → L
Tipo: 2 seleções — a odd do bilhete é o PRODUTO das odds abaixo (a casa não entrega a odd combinada). Em bilhete ganho vale Retorno ÷ Aposta (MASTER_RESULTADO §7.1).
Esporte (casa): CL=13 (Tênis)
Seleções:
  • Yunchaokete Bu x Federico Cina · Para Ganhar a Partida · Yunchaokete Bu @ 1,5 · Slam M Q-R3
  • Francesca Jones x Joanna Garland · Para Ganhar a Partida · Francesca Jones @ 1,5 · Slam W Q-R3
"""

# O MESMO par de jogadores no dia seguinte, com a 2ª perna a `1,5333333333333332` — a
# renderização `float64` de 23/15. O produto EXATO daria `2,2999999999999998`.
DUPLA_COM_RUIDO_DE_FLOAT = """
Data (encerramento): 27/08/2026
Stake: 120,14
Status: Perdeu → L
Tipo: 2 seleções — a odd do bilhete é o PRODUTO das odds abaixo (a casa não entrega a odd combinada). Em bilhete ganho vale Retorno ÷ Aposta (MASTER_RESULTADO §7.1).
Esporte (casa): CL=13 (Tênis)
Seleções:
  • Yunchaokete Bu x Federico Cina · Para Ganhar a Partida · Yunchaokete Bu @ 1,5 · Slam M Q-R3
  • Francesca Jones x Joanna Garland · Para Ganhar a Partida · Francesca Jones @ 1,5333333333333332 · Slam W Q-R3
"""

# `W`, e por isso fica FORA. De quebra é meia vitória disfarçada: stake 35,36, retorno
# 35,81 — as duas pernas são linha asiática partida.
MULTIPLA_W_FICA_FORA = """
Data (encerramento): 26/08/2026
Stake: 35,36
Status: Ganho → W (retorno R$ 35,81)
Tipo: 2 seleções — a odd do bilhete é o PRODUTO das odds abaixo (a casa não entrega a odd combinada). Em bilhete ganho vale Retorno ÷ Aposta (MASTER_RESULTADO §7.1).
Esporte (casa): CL=1 (Futebol)
Seleções:
  • Omiya Ardija x Vanraure Hachinohe · Gols + - · Mais de 2.0,2.5 @ 1,95 · SOC-JAP-CUP
  • Ruch Radzionkow x GKS Katowice II · Gols + - · Menos de 2.5,3.0 @ 2,025 · POLAND-IV-LIGA
"""


def test_multipla_perdida_fecha_com_o_produto_das_pernas():
    """`1,8 × 1,775 × 1,7 = 5,4315`. Bilhete real, e ele é tambem o retrato do defeito
    que esta entrada conserta: **a IA gravou `1,8` nele** — a odd de UMA perna."""
    t = tradutor.traduzir("BET365", MULTIPLA_L_TRES_PERNAS)
    assert t.ok, t.motivo
    assert t.esporte == "Múltiplos" and t.aposta == "Múltipla"
    assert t.odd == "5,4315"


def test_dupla_de_mesmo_esporte_tambem_e_multipla_comum():
    """O §7.2 é sobre a FORMA da aposta, não sobre a categoria: uma dupla de dois jogos
    de tênis não é `Múltiplos` pelo §2 (o esporte segue sendo Tênis) e a odd dela é o
    produto do mesmo jeito. `1,5 × 1,5 = 2,25`."""
    t = tradutor.traduzir("BET365", DUPLA_L_MESMO_ESPORTE)
    assert t.ok, t.motivo
    assert t.esporte == "Tênis", "dois jogos do mesmo esporte não são Múltiplos"
    assert t.aposta == "Múltipla" and t.odd == "2,25"


def test_o_ruido_do_float_da_perna_nao_vaza_para_a_odd():
    """A perna chega como `1,5333333333333332`, que é 23/15 em `float64`. O produto
    EXATO seria `2,2999999999999998`; a odd da casa é `2,3`. O corte em 15 dígitos
    significativos é o piso de ruído da entrada — abaixo dele não há informação."""
    t = tradutor.traduzir("BET365", DUPLA_COM_RUIDO_DE_FLOAT)
    assert t.ok, t.motivo
    assert t.odd == "2,3"


def test_multipla_ganha_continua_indo_para_a_ia():
    """`W` fica de fora de propósito. Ali o §7.1 manda `Retorno ÷ Stake`, e é exatamente
    essa conta que ESCONDE meia vitória — o bilhete fecha internamente consistente e
    nunca chega a `HW` (o caso da s356). Quem separa os dois é o `_veredito_do_retorno`,
    no servidor. Este bloco é um desses: stake 35,36 e retorno 35,81."""
    t = tradutor.traduzir("BET365", MULTIPLA_W_FICA_FORA)
    assert not t.ok and "odd combinada" in t.motivo


# Bloco real de SISTEMA, perdido. A odd dele é a MÉDIA das 3 linhas (3,7347916666666667);
# o produto das pernas daria 7,20875 — quase o dobro. É o caso da s265 inteiro.
SISTEMA_PERDIDO = """
Data (encerramento): 30/08/2026
Stake: 90,36
Status: Perdeu → L
Tipo: SISTEMA Duplas — 3 apostas de 2 seleção(ões), sobre 3 seleções · aposta unitária R$ 30,12 · total R$ 90,36 (a Stake acima é o TOTAL — é ela que vale)
Odd (estrutural do sistema): 3,7347916666666667  ← JÁ CALCULADA (média das 3 linhas). Use esta odd; NÃO multiplique as odds das seleções — o produto é a odd da múltipla cheia, que este bilhete NÃO é. Em bilhete ganho vale Retorno ÷ Aposta (MASTER_RESULTADO §7.1).
Seleções:
  • Lions FC x Peninsula Power · Gols + - · Menos de 3.0 @ 1,975 · AUS-NPL-QUEENSL
  • El Paso Locomotive FC x Loudoun United FC · Gols + - · Menos de 2.5,3.0 @ 2 · USA-USL-PRO
  • Heidelberg United (F) x Bentleigh Greens (F) · Gols + - · Menos de 3.5 @ 1,825 · AUSNPLVICW
"""


def test_sistema_usa_a_media_da_casa_e_nunca_o_produto():
    """SISTEMA não é múltipla, e trocar um pelo outro é a s265 (`3 x Duplas` lida como
    tripla: retorno potencial R$ 1.762 no lugar de R$ 994). Aqui a média é
    3,7347916666666667 e o produto seria 7,20875 — quase o dobro."""
    t = tradutor.traduzir("BET365", SISTEMA_PERDIDO)
    assert t.ok, t.motivo
    assert t.odd == "3,7347916666666667", "a odd é a que a casa calculou, copiada"


def test_sistema_sem_a_linha_de_odd_NAO_cai_no_produto():
    """A trava que o `Tipo:` segura, e ela é a última linha de defesa contra a s265.

    Hoje o sistema nunca chega ao produto porque TRAZ linha de odd — mas isso é defesa
    de segunda mão: no dia em que o `Odd (estrutural do sistema)` faltar, é o `Tipo:`
    que impede o produto de sobrescrever a média. Sem este caso a mutação
    `_TIPO_MULTIPLA_COMUM = r""` passava verde (medido)."""
    bloco = "\n".join(l for l in SISTEMA_PERDIDO.splitlines()
                      if not l.startswith("Odd (estrutural do sistema):"))
    assert "Odd (estrutural" not in bloco
    t = tradutor.traduzir("BET365", bloco)
    assert not t.ok and "odd combinada" in t.motivo, (
        "sistema sem odd tem de ir para a IA, NUNCA receber o produto das pernas")


def test_a_odd_estrutural_e_por_CASA():
    """Mesma trava do veredito de esporte: a régua vale onde a casa imprime UMA odd por
    perna e nenhuma combinada. Casa fora do conjunto não recebe conta nenhuma."""
    cab = tradutor._cabecalho(MULTIPLA_L_TRES_PERNAS)
    pernas = tradutor._pernas(MULTIPLA_L_TRES_PERNAS)
    assert tradutor._odd_estrutural("BET365", cab, pernas) == "5,4315"
    assert tradutor._odd_estrutural("NOVIBET", cab, pernas) == ""


def test_perna_sem_odd_derruba_o_bilhete_inteiro():
    """Meia conta é pior que conta nenhuma: sem a odd de UMA perna o produto está errado
    e não há como saber para que lado. O bilhete inteiro vai para a IA."""
    bloco = MULTIPLA_L_TRES_PERNAS.replace(" @ 1,775", "")
    t = tradutor.traduzir("BET365", bloco)
    assert not t.ok and "odd combinada" in t.motivo


def test_mutacao_sem_o_produto_a_multipla_volta_para_a_ia():
    """Prova por mutação: desligando a odd estrutural, os três bilhetes que ela libera
    têm de voltar ao fallback. Verde aqui significaria que a cobertura veio de outro
    lugar."""
    original = tradutor._odd_estrutural
    try:
        tradutor._odd_estrutural = lambda casa, cab, pernas: ""
        for bloco in (MULTIPLA_L_TRES_PERNAS, DUPLA_L_MESMO_ESPORTE,
                      DUPLA_COM_RUIDO_DE_FLOAT):
            t = tradutor.traduzir("BET365", bloco)
            assert not t.ok and "odd combinada" in t.motivo
    finally:
        tradutor._odd_estrutural = original
    assert tradutor.traduzir("BET365", MULTIPLA_L_TRES_PERNAS).ok


def test_mutacao_o_corte_de_precisao_e_o_que_tira_o_ruido():
    """A outra metade: com o corte em 34 dígitos (a precisão da multiplicação), o ruído
    do `float64` da perna atravessa e a odd sai `2,2999999999999998`. Este teste é o que
    impede alguém de 'simplificar' as duas etapas numa só."""
    original = tradutor._PRECISAO_ODD
    try:
        tradutor._PRECISAO_ODD = tradutor._PRECISAO_PRODUTO
        t = tradutor.traduzir("BET365", DUPLA_COM_RUIDO_DE_FLOAT)
        assert t.odd == "2,2999999999999998", (
            "sem o corte o ruido tinha de aparecer; se nao aparece, o corte nao e o que decide")
    finally:
        tradutor._PRECISAO_ODD = original
    assert tradutor.traduzir("BET365", DUPLA_COM_RUIDO_DE_FLOAT).odd == "2,3"


def test_a_regua_do_separador_e_UMA_e_mora_aqui():
    """`_num_bloco` mudou de casa na s386 (veio do `repository`, que agora o reexporta)
    porque ganhou um irmão em `Decimal`. Os dois leem o MESMO separador — e o caso que
    obriga isso é a Betfair, que mistura BR e EN no mesmo bloco (s321)."""
    import repository
    assert repository._num_bloco is tradutor._num_bloco
    assert tradutor._num_bloco("1,642.38") == 1642.38
    assert tradutor._num_bloco("1.642,38") == 1642.38
    assert tradutor._num_bloco("1,775") == 1.775, "um separador só é SEMPRE decimal"
    assert str(tradutor._dec_bloco("1,775")) == "1.775"
    assert str(tradutor._dec_bloco("1,642.38")) == "1642.38"
    assert tradutor._dec_bloco("") is None and tradutor._num_bloco("") is None


# ── Linha asiática: o quarto de linha (MASTER_DESCRICAO §10.1.1, s336) ───────


def test_quarto_de_linha_nos_quatro_separadores():
    """A casa escreve o par de quatro jeitos, e a vírgula acumula os papéis de decimal
    e de separador. Um padrão só leria `1,5` sozinho como um par."""
    q = tradutor._quarto_de_linha
    assert q("Mais de 2.0,2.5") == "Mais de 2.25"
    assert q("Menos de 2,5/3,0") == "Menos de 2.75"
    assert q("Mais de 3.5-4.0") == "Mais de 3.75"
    assert q("Time -0.5,-1.0") == "Time -0.75", "handicap partido com sinal (3 na base)"


def test_quarto_de_linha_nao_toca_no_que_nao_e_par():
    """O que NÃO pode mexer é o que faz a função ser segura no caminho quente."""
    for intocado in ("Mais de 2.5", "Danny van Trijp -1.5", "Set 1-0", "odd 1,5"):
        assert tradutor._quarto_de_linha(intocado) == intocado


def test_mutacao_sem_a_conversao_a_descricao_sai_fora_do_MASTER():
    """Prova por mutação, e ela fecha o ciclo com o gate: desligando a conversão, a
    descrição que o tradutor produz passa a ser REPROVADA pelo `checar_descricao` com
    `linha-partida-nao-convertida`. Verde aqui com a conversão desligada significaria
    que a decisão da s336 não está sendo sustentada por código nenhum."""
    import descricao_check
    original = tradutor._quarto_de_linha
    try:
        tradutor._quarto_de_linha = lambda t: t
        t = tradutor.traduzir("BET365", SIMPLES_TOTAL_GOLS_PARTIDA)
        assert t.ok, t.motivo
        regras = [p[1] for p in descricao_check.checar_descricao("Gols", t.descricao)]
        assert "linha-partida-nao-convertida" in regras
    finally:
        tradutor._quarto_de_linha = original
    t = tradutor.traduzir("BET365", SIMPLES_TOTAL_GOLS_PARTIDA)
    assert descricao_check.checar_descricao("Gols", t.descricao) == []
    assert "Over 4.25 Gols" in t.descricao
