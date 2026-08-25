# -*- coding: utf-8 -*-
"""Base de DEMONSTRACAO para print de marketing -- nomes e numeros ficticios.

Por que existe: a pagina de vendas precisa de print real do sistema, e o unico
banco alcancavel desta maquina e' o de PRODUCAO. Escrever aposta de mentira em
producao para tirar foto seria pessimo. Entao o front-end real e' alimentado por
este feed, servido pelo `servidor_demo.py`.

Nada aqui toca banco, rede ou producao. E' um gerador puro.

DETERMINISTICO (`random.Random(SEMENTE)`): o mesmo comando gera exatamente o
mesmo conjunto, entao regerar o print seis meses depois nao muda os numeros da
landing. Trocar a semente troca a base inteira.

Consistencia do dinheiro: `lucro` segue a MESMA regra do `repository.calcular_pl`
  W  -> stake x odd - stake        HW -> (stake/2) x odd - stake/2
  L  -> -stake                     HL -> -stake/2
  V  -> 0
Se essa regra mudar no app, mudar aqui tambem -- senao o print mostra conta que
nao fecha, que e' o unico jeito de um print de vendas virar prejuizo.
"""
import random
from datetime import date, timedelta

# ── Calibragem ───────────────────────────────────────────────────────────────
# Os numeros abaixo NAO sao chute: sairam de `perfil_producao.py` rodado contra
# a base real em 27/07/2026 (somente leitura, so agregacao). O que atravessa e'
# a FORMA da operacao -- volume, faixa de stake, cauda da odd, mix de resultado.
# Nenhuma linha real e' copiada; nenhum nome real aparece.
#
# Medido:  27.433 apostas · 43 casas · 102 contas · 65 tipsters · 19 esportes
#          stake  p10 47,50  ·  mediana 187,50  ·  p90 450,00
#          odd    p10  1,78  ·  mediana   2,80  ·  p90  17,00   (cauda longa)
#          result L 62,1% · W 31,7% · V 5,8% · HL 0,2% · HW 0,2%
#          ritmo  130,6 apostas por dia ativo (pico 330), 210 dias com aposta
#
# O acerto de 31,7% NAO e' operacao ruim: com odd mediana 2,80 e cauda ate 17, a
# probabilidade implicita media ja fica nessa casa. Quem olha "31% de acerto"
# sem olhar a odd le errado -- e e' por isso que a pagina mostra as duas coisas.
# ATENCAO ao trocar: a SEMENTE manda no numero de capa, mais que o EDGE.
#
# Medido na s294, varrendo 30 sementes com o EDGE fixo em 0.045 (esperanca de ROI
# 4,24%): o ROI realizado variou de **-0,03% a +9,60%**. Com odd media 7,6 e cauda
# ate 60, 24 mil apostas ainda sao poucas para a media convergir -- a variancia da
# operacao e' o fenomeno dominante, nao o parametro.
#
# Consequencia pratica, que custou uma rodada inteira de calibragem: mexer em
# QUALQUER coisa que consuma numero aleatorio (foi o `CASA_FEUDO`) reordena o
# fluxo e joga o ROI para outro ponto dessa faixa. Depois de mexer no gerador,
# SEMPRE remedir Solidez -- ela pulou de Media para Baixa sem ninguem tocar no EDGE.
#
# 20260706 foi escolhida por ser a realizacao TIPICA: ROI 4,28% contra os 4,24%
# esperados. Nao e' a melhor da varredura (havia 9,60%) -- e' a mais honesta, que
# e' o criterio aqui. Escolher a de cima seria vender sorte como metodo.
SEMENTE = 20260706
DONO = "Ricardo"          # persona da demonstracao, nao e' usuario real
N_APOSTAS = 24000
DIAS = 210                 # dias com aposta na base real

# Vantagem sobre a probabilidade implicita da odd. NAO e' cosmetico: e' o unico
# parametro que move o "Nivel de Solidez" da tela de Metricas.
#
# MEDIDO na s294 contra a regua REAL (`calcSolidez` do app.js + `mc-core.js`,
# 24.000 apostas, 2.000 simulacoes). A varredura abaixo rodou com a semente
# ANTERIOR (20260727); com a semente atual o edge 0.045 da ROI 4,55% e folga
# 2,91x -- mesma faixa (Media), numero um pouco diferente. O que a tabela prova
# nao e' o valor exato e sim a FORMA da regua, e essa nao muda com a semente:
#
#   edge    ROI     p-value   folga (P/L / xmdd)   Solidez
#   0.045   4,63%   0,021     2,87x                Media       (0,60)
#   0.065   6,29%   0,005     4,74x                Media       (0,60)
#   0.070   7,10%   0,001     5,66x                Muito Alta  (0,90)
#   0.080   8,16%   0,0005    7,19x                Muito Alta  (0,90)
#
# Duas coisas que essa tabela ensina e que nao estavam escritas em lugar nenhum:
#
# 1) NAO EXISTE patamar "Alta" nesta base. Os cortes de `pValue` (<0,001) e de
#    `folga` (>5) cruzam praticamente juntos, entao o score pula 0,60 -> 0,90
#    entre 0.065 e 0.070. Mirar em "Alta" seria calibrar em cima de um fio: a
#    faixa mudaria de print para print. Nao se persegue.
# 2) O `sVar` esta TRAVADO em 0,5 e nenhum edge o destrava -- ele olha odd media
#    (<=3 pontua cheio) e a nossa e' 7,71, que veio da base real. Ou seja: o teto
#    desta operacao na nossa propria regua e' 0,90, por desenho.
#
# FICA EM 0.045 (decisao do Feca, s294). ROI de 4,63% em 24 mil apostas e' o
# numero que um apostador metodico acredita; 8,16% e' numero de elite mundial e
# o publico desconfia -- e desconfianca no print contamina a pagina inteira.
# "Media" no print nao e' defeito, e' o argumento: a regua nao existe para
# elogiar o dono dela. Ver o README de docs/marketing (regra 2: todo comparativo
# nosso tem de perder pelo menos uma linha).
#
# O STATUS da s214 dizia "Solidez Baixa, Recovery Factor 0,94x". Esta DESATUALIZADO
# em duas frentes: hoje a faixa e' Media, e o 0,94x era o `calcRecoveryFactor`
# (drawdown REALIZADO), que nao e' o numero que a regua usa -- ela usa
# `profitXmdd`, o drawdown do Monte Carlo. Sao grandezas diferentes.
EDGE = 0.045

# Percentis medidos. `_quantil` interpola entre eles em escala log, o que
# reproduz a cauda sem precisar assumir uma distribuicao teorica.
ODD_Q = [(0.00, 1.20), (0.10, 1.78), (0.50, 2.80), (0.90, 17.00), (1.00, 60.00)]
STAKE_Q = [(0.00, 10.00), (0.10, 47.50), (0.50, 187.50), (0.90, 450.00), (1.00, 1800.00)]

# Casas REAIS com a concentracao medida: nome de operadora nao e' dado
# sensivel, e reconhecimento ajuda a venda. Ficticio e' tudo que identifica
# PESSOA e VALOR. A cauda importa: o print tem de mostrar que o sistema aguenta
# dezenas de casas, nao cinco.
CASAS = [
    ("Bet365", 0.564), ("Betano", 0.177), ("Superbet", 0.094), ("Betfair", 0.043),
    ("Pinnacle", 0.018), ("Novibet", 0.016), ("Polymarket", 0.014),
    ("Bolsa de Aposta", 0.009), ("KTO", 0.006), ("Betboom", 0.006),
    ("BETesporte", 0.006), ("Betnacional", 0.005), ("Lottu", 0.005),
    ("Jogo de Ouro", 0.003), ("Tivo", 0.003), ("VaideBet", 0.003),
    ("Betfast", 0.003), ("Estrela Bet", 0.003), ("PixBet", 0.002),
    ("Esportes da Sorte", 0.002), ("7K", 0.002), ("Betão", 0.002),
    ("Vitória Bet", 0.002), ("KingPanda", 0.002), ("Aposta1", 0.002),
    ("Faz1Bet", 0.001), ("Liderbet", 0.001), ("Bateu", 0.001), ("MultiBet", 0.001),
]
# 65 tipsters na base real -- aqui 24 ficticios, que ja enche a tela de Tipsters
# e o leaderboard da home sem virar lista infinita no print.
TIPSTERS = [
    ("Linha Fria", 0.108), ("Corner Value", 0.092), ("Método Ártico", 0.081),
    ("NBA Edge", 0.074), ("Sala 7", 0.066), ("Contra-Ataque", 0.058),
    ("Régua", 0.052), ("Pivô Alto", 0.047), ("Quadra Rápida", 0.042),
    ("Bloco Norte", 0.038), ("Fator K", 0.034), ("Grid 12", 0.030),
    ("Saque Curto", 0.027), ("Terceiro Tempo", 0.024), ("Modelo 9", 0.021),
    ("Cauda Longa", 0.019), ("Pressão Alta", 0.017), ("Zona 14", 0.015),
    ("Duplo Pivô", 0.013), ("Escanteio Sul", 0.011), ("Base Fria", 0.010),
    ("Marca Curta", 0.009), ("Ritmo", 0.008), ("", 0.104),
]
# 102 contas na base real: 17 operadores x 6 fornecedores.
_NOMES = ["Marlon", "Bruno", "Caio", "Diego", "Otávio", "Renan", "Tiago",
          "Vitor", "Luan", "Igor", "Rafa", "Léo", "Murilo", "Enzo", "Davi",
          "Artur", "Nuno"]
_FORNECEDORES = ["Vega", "Norte", "Sul", "Âncora", "Trilho", "Pauta"]
N_CONTAS = 102          # medido na base real


def _montar_elenco(semente=SEMENTE, n_contas=N_CONTAS):
    """Elenco FIXO de contas -- cada conta pertence a UMA casa, como na producao.

    Por que isto existe (s294): `gerar()` sorteava `parceiro` e `casa` de forma
    INDEPENDENTE, entao no limite cada pessoa apostava em cada casa e a tela de
    Fornecedores nascia com 102 x 29 = 1.830 contas, contra as 102 reais. Nao era
    numero feio: era um MODELO errado -- na tabela `parceiros` a conta e' a dupla
    (nome, casa), e um cadastro por par visto no feed inventa conta que ninguem
    abriu. Com o elenco a direcao se inverte: a casa vem DA CONTA.

    Distribuicao: cada casa recebe pelo menos 1 conta (senao a casa aparece no
    feed sem cadastro, que e' o bug oposto), e as restantes vao por peso -- a
    casa de maior volume e' tambem onde se abre mais conta, que e' o que o
    operador faz de verdade.
    """
    rng = random.Random(semente ^ 0x5E1E)      # fluxo proprio: nao desloca o das apostas
    piso = {casa: 1 for casa, _ in CASAS}
    sobra = n_contas - len(piso)
    for casa, peso in CASAS:
        piso[casa] += int(round(sobra * peso))
    # Ajuste fino ate bater exatamente n_contas (o round acima erra por 1-2).
    ordem = [c for c, _ in CASAS]
    i = 0
    while sum(piso.values()) != n_contas:
        casa = ordem[i % len(ordem)]
        delta = 1 if sum(piso.values()) < n_contas else -1
        if piso[casa] + delta >= 1:
            piso[casa] += delta
        i += 1

    combos = [f"{n} [{f}]" for f in _FORNECEDORES for n in _NOMES]
    elenco = []
    for casa, _ in CASAS:
        # `sample` garante que a mesma pessoa nao tenha duas contas na MESMA casa.
        # Entre casas ela pode repetir -- e' assim que o operador opera.
        for parceiro in rng.sample(combos, piso[casa]):
            conta, _, forn = parceiro.partition(" [")
            elenco.append({
                "parceiro": parceiro,
                "conta": conta.strip(),
                "fornecedor": forn.rstrip("]").strip(),
                "casa": casa,
            })
    return elenco


ELENCO = _montar_elenco()
# Indice casa -> contas daquela casa. `gerar()` sorteia a CASA pelo peso medido e
# so entao a conta, o que preserva a distribuicao de casa exatamente como estava.
POR_CASA = {}
for _c in ELENCO:
    POR_CASA.setdefault(_c["casa"], []).append(_c)

# Casa-feudo: casa de nicho costuma ser de UM tipster so. E' um padrao real da
# operacao (a tela de Atribuicao por Casa existe exatamente por causa dele) e a
# base precisa CONTE-LO, senao a demonstracao mostra o recurso sem o fenomeno --
# 29 casas todas compartilhadas, e o botao "Aplicar sugestoes" sem nada para
# sugerir de interessante.
#
# NAO cravamos o rotulo na tela: injetamos o fenomeno no dado e deixamos a regra
# de `casas_visao` (share >=10%, cobertura >=85%) descobrir sozinha. Marcar a
# casa como dedicada sem o dado sustentar seria print mentiroso.
CASA_FEUDO = {"BETesporte": "Sala 7", "Bolsa de Aposta": "Corner Value", "KTO": "Fator K"}
_FEUDO_PUREZA = 0.96      # 4% de ruido: feudo real nao e' 100%, tem a aposta avulsa

ESPORTES = [
    ("Futebol", 0.487), ("Basquete", 0.249), ("Múltiplos", 0.117),
    ("Tênis", 0.055), ("E-Sports", 0.035), ("Dardos", 0.016),
    ("Baseball", 0.016), ("eBasket", 0.008), ("Vôlei", 0.007),
    ("F1", 0.006), ("MMA", 0.002), ("Futebol Americano", 0.001),
]
# Categorias do vocabulario fechado, com o peso medido na base real. Player
# Props e Multipla dominam -- e' operacao de prop, nao de resultado seco.
MERCADOS = {
    "Futebol": [("Múltipla", 0.30), ("Player Props", 0.14), ("Anytime", 0.11),
                ("Escanteios", 0.10), ("Gols", 0.08), ("Cartões", 0.07),
                ("ML", 0.06), ("Chutes", 0.05), ("Handicap", 0.04),
                ("Desarmes", 0.03), ("Chutes no Gol", 0.02)],
    "Basquete": [("Player Props", 0.42), ("Assistência", 0.24), ("Múltipla", 0.14),
                 ("Pontos", 0.08), ("ML", 0.06), ("Handicap", 0.06)],
    "Múltiplos": [("Múltipla", 1.00)],
    "Tênis": [("ML", 0.34), ("Handicap", 0.24), ("Múltipla", 0.18),
              ("Sets", 0.14), ("Outros", 0.10)],
    "E-Sports": [("E-Sports Props", 0.38), ("ML", 0.30), ("Handicap", 0.20),
                 ("Múltipla", 0.12)],
    "Dardos": [("H2H", 0.44), ("ML", 0.30), ("Outros", 0.26)],
    "Baseball": [("ML", 0.40), ("Corridas", 0.32), ("Handicap", 0.28)],
    "eBasket": [("Pontos", 0.46), ("ML", 0.32), ("Handicap", 0.22)],
    "Vôlei": [("ML", 0.42), ("Handicap", 0.32), ("Pontos", 0.26)],
    "F1": [("H2H", 0.52), ("Outros", 0.48)],
    "MMA": [("ML", 0.60), ("Outros", 0.40)],
    "Futebol Americano": [("Player Props", 0.40), ("ML", 0.34), ("Handicap", 0.26)],
}
TIMES = {
    "Futebol": ["Palmeiras", "Flamengo", "Corinthians", "Grêmio", "Fluminense",
                "Internacional", "Athletico-PR", "São Paulo", "Bahia", "Botafogo",
                "Arsenal", "Chelsea", "Liverpool", "Real Madrid", "Barcelona",
                "Inter de Milão", "Napoli", "Bayern", "Dortmund", "PSG"],
    "Basquete": ["Lakers", "Celtics", "Nuggets", "Bucks", "Suns", "Heat",
                 "Warriors", "Knicks", "Mavericks", "76ers"],
    "Tênis": ["Alcaraz", "Sinner", "Djokovic", "Zverev", "Medvedev", "Rune",
              "Ruud", "De Minaur", "Fritz", "Tsitsipas"],
    "NFL": ["Chiefs", "Eagles", "49ers", "Bills", "Ravens", "Lions", "Cowboys", "Dolphins"],
    "MMA": ["Silva", "Oliveira", "Pantoja", "Almeida", "Nunes", "Barboza", "Dariush", "Gamrot"],
    "Vôlei": ["Sada Cruzeiro", "Praia Clube", "Minas", "Itambé", "Suzano", "Campinas"],
    "E-Sports": ["FURIA", "LOUD", "MIBR", "paiN", "Team Liquid", "NAVI", "G2", "FaZe"],
    "Baseball": ["Yankees", "Dodgers", "Astros", "Braves", "Mets", "Padres"],
    "Múltiplos": ["Palmeiras", "Flamengo", "Lakers", "Celtics", "Arsenal",
                  "Bayern", "Nuggets", "Real Madrid", "Bucks", "Liverpool"],
    "Dardos": ["Humphries", "Littler", "Price", "Van Gerwen", "Aspinall", "Smith"],
    "eBasket": ["Lakers (kayn)", "Celtics (vzr)", "Heat (dko)", "Suns (mrq)",
                "Bucks (tlv)", "Knicks (pxa)"],
    "F1": ["Verstappen", "Norris", "Leclerc", "Piastri", "Russell", "Hamilton"],
    "Futebol Americano": ["Chiefs", "Eagles", "49ers", "Bills", "Ravens", "Lions"],
}


def _sorteia(rng, pares):
    """Escolhe um item de [(valor, peso), ...]."""
    r, acc = rng.random(), 0.0
    for valor, peso in pares:
        acc += peso
        if r <= acc:
            return valor
    return pares[-1][0]


def _quantil(rng, tabela):
    """Amostra interpolando os percentis MEDIDOS, em escala log.

    Escala log porque a cauda da odd e' longa (mediana 2,80, p90 17): interpolar
    linearmente achataria a cauda e a tela de Distribuicao de Odds sairia com
    cara de operacao que nao existe.
    """
    import math
    u = rng.random()
    for i in range(1, len(tabela)):
        q0, v0 = tabela[i - 1]
        q1, v1 = tabela[i]
        if u <= q1:
            t = 0.0 if q1 == q0 else (u - q0) / (q1 - q0)
            return math.exp(math.log(v0) + t * (math.log(v1) - math.log(v0)))
    return tabela[-1][1]


def _odd(rng, esporte):
    return round(_quantil(rng, ODD_Q), 2)


def _stake(rng):
    """Stake na faixa medida, arredondada como operador arredonda de verdade."""
    v = _quantil(rng, STAKE_Q)
    passo = 5 if v < 100 else (10 if v < 500 else 50)
    return float(max(passo, round(v / passo) * passo))


def _resultado(rng, odd):
    """Resultado com edge LEVE e positivo sobre a probabilidade implicita.

    p = (1/odd) x (1 + edge). Com a odd calibrada pelos percentis reais, o
    acerto CAI NATURALMENTE em ~32% -- que e' o da base medida (31,7%). Ou
    seja: nao forcamos a taxa de acerto, ela emerge da distribuicao de odd,
    que e' o unico jeito de os dois numeros ficarem coerentes no print.

    Nao inflamos o edge: a pagina de vendas nao pode mostrar operacao irreal,
    e ela mesma diz que a maioria das pessoas perde dinheiro apostando.
    """
    p = min(0.93, (1.0 / odd) * (1.0 + EDGE))
    r = rng.random()
    if r < 0.058:
        return "V"                                 # anulada / cashout = stake
    if r < 0.062:
        return "HW" if rng.random() < p else "HL"  # meia-liquidacao (asiatico)
    return "W" if rng.random() < p else "L"


def _pl(stake, odd, resultado):
    """Espelha repository.calcular_pl -- ver docstring do modulo."""
    if resultado == "W":
        return round(stake * odd - stake, 2)
    if resultado == "L":
        return round(-stake, 2)
    if resultado == "V":
        return 0.0
    if resultado == "HW":
        return round((stake / 2) * odd - stake / 2, 2)
    if resultado == "HL":
        return round(-stake / 2, 2)
    return 0.0


def _descricao(rng, esporte, mercado):
    times = TIMES[esporte]
    a, b = rng.sample(times, 2)
    jogo = f"{a} x {b}"
    if mercado == "Múltipla":
        c, d = rng.sample(times, 2)
        return f"{jogo} — Mais de 2.5 Gols // {c} x {d} — Ambas Marcam Sim"
    detalhe = {
        "ML": f"{a} vencer",
        "Handicap Asiático": f"{a} {rng.choice(['-0.5', '-1', '+0.25', '-0.75'])}",
        "Handicap": f"{a} {rng.choice(['-3.5', '-6.5', '+4.5'])}",
        "Handicap de Games": f"{a} {rng.choice(['-3.5', '+2.5'])}",
        "Handicap de Sets": f"{a} -1.5",
        "Handicap de Mapas": f"{a} -1.5",
        "Total de Gols": f"{rng.choice(['Mais', 'Menos'])} de {rng.choice(['1.5', '2.5', '3.5'])} Gols",
        "Total de Games": f"{rng.choice(['Mais', 'Menos'])} de {rng.choice(['21.5', '22.5'])} Games",
        "Total de Rounds": f"{rng.choice(['Mais', 'Menos'])} de 1.5 Rounds",
        "Ambas Marcam": "Sim",
        "Escanteios": f"Mais de {rng.choice(['8.5', '9.5', '10.5'])} Escanteios",
        "Cartões": f"Mais de {rng.choice(['3.5', '4.5'])} Cartões",
        "Dupla Chance": f"{a} ou Empate",
        "Pontos": f"{rng.choice(['Mais', 'Menos'])} de {rng.choice(['210.5', '221.5', '44.5'])} Pontos",
        "Sets": f"{a} 2-0",
        "Corridas": f"{rng.choice(['Mais', 'Menos'])} de 8.5 Corridas",
        "Método de Vitória": f"{a} por decisão",
        "Player Props": f"{rng.choice(times)} — mais de {rng.choice(['1.5', '2.5', '24.5'])}",
        "E-Sports Props": f"{a} — mais de 1.5 mapas",
        "Anytime": f"{rng.choice(times)} — marcar a qualquer momento",
        "Assistência": f"{rng.choice(times)} — mais de {rng.choice(['3.5', '5.5', '7.5'])} assistências",
        "Chutes": f"{rng.choice(times)} — mais de {rng.choice(['1.5', '2.5', '3.5'])} chutes",
        "Chutes no Gol": f"{rng.choice(times)} — mais de {rng.choice(['0.5', '1.5'])} chutes no gol",
        "Desarmes": f"{rng.choice(times)} — mais de {rng.choice(['2.5', '3.5'])} desarmes",
        "Gols": f"{rng.choice(['Mais', 'Menos'])} de {rng.choice(['1.5', '2.5', '3.5'])} Gols",
        "H2H": f"{a} vencer {b}",
        "Outros": f"{a} x {b} — mercado combinado",
    }.get(mercado, mercado)
    return f"{jogo} — {detalhe}"


def gerar(semente=SEMENTE, n=N_APOSTAS, dias=DIAS, ate=None):
    """Devolve a lista de linhas no contrato de `repository.dashboard_rows`."""
    rng = random.Random(semente)
    fim = ate or date.today()
    linhas = []
    for i in range(n):
        # Distribuicao no tempo levemente crescente: a operacao "cresce" ao
        # longo do historico, o que da uma curva de P/L com cara de real.
        pos = rng.random() ** 0.85
        dia = fim - timedelta(days=int(pos * dias))
        esporte = _sorteia(rng, ESPORTES)
        mercado = _sorteia(rng, MERCADOS[esporte])
        casa = _sorteia(rng, CASAS)
        odd = _odd(rng, esporte)
        stake = _stake(rng)
        res = _resultado(rng, odd)
        # A conta sai do ELENCO daquela casa -- nunca de um sorteio independente,
        # que inventaria conta inexistente (ver `_montar_elenco`).
        cad = rng.choice(POR_CASA[casa])
        parceiro, conta, forn = cad["parceiro"], cad["conta"], cad["fornecedor"]
        tipster = _sorteia(rng, TIPSTERS)
        # Casa de nicho -> quase sempre o mesmo tipster (ver CASA_FEUDO).
        if casa in CASA_FEUDO and rng.random() < _FEUDO_PUREZA:
            tipster = CASA_FEUDO[casa]
        linhas.append({
            "id": 100000 + i,
            "data": dia.isoformat(),
            "esporte": esporte,
            "tipster": tipster,
            "casa": casa,
            "parceiro": parceiro,
            "conta": conta.strip(),
            "fornecedor": forn.rstrip("]").strip(),
            "aposta": mercado,
            "descricao": _descricao(rng, esporte, mercado),
            "stake": stake,
            "odd": odd,
            "resultado": res,
            "lucro": _pl(stake, odd, res),
            "operador": DONO,
        })
    linhas.sort(key=lambda r: r["data"])
    return linhas


def _meses(n=6, ate=None):
    """Os N meses que a tela de Custos mostra -- espelha `ctGetMonths` (app.js):
    os 6 ultimos TERMINANDO no mes corrente. Se o front mudar a janela, o print
    sai com coluna vazia; e' o unico acoplamento desta funcao."""
    fim = ate or date.today()
    saida, y, m = [], fim.year, fim.month
    for _ in range(n):
        saida.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(saida))


# Assinaturas ativas: nem todo tipster e' pago (varios sao proprios / gratuitos).
# Valor mensal ficticio, na faixa de mercado brasileiro (R$ 150 a R$ 900).
_ASSINATURAS = [
    ("Linha Fria", 690), ("Corner Value", 450), ("Método Ártico", 890),
    ("NBA Edge", 520), ("Sala 7", 380), ("Contra-Ataque", 250),
    ("Régua", 300), ("Pivô Alto", 180), ("Quadra Rápida", 150),
    ("Bloco Norte", 420),
]
_CUSTOS_GERAIS = [
    ("VPN & proxies", 340), ("Servidor / automação", 260),
    ("Assinatura de dados", 580), ("Contabilidade", 450),
]
# Custo de AQUISICAO por conta, por casa. Casa grande e' mais cara e mais dificil
# de abrir -- e' o que o operador paga de verdade ao fornecedor.
_CUSTO_CASA_PADRAO = 120
_CUSTO_CASA = {
    "Bet365": 380, "Betano": 260, "Superbet": 210, "Betfair": 300,
    "Pinnacle": 340, "Novibet": 180, "Polymarket": 90, "Bolsa de Aposta": 150,
    "KTO": 160, "Betboom": 140, "BETesporte": 130, "Betnacional": 130,
}


def custos(semente=SEMENTE, ate=None):
    """Custos da demonstracao nos 3 contratos que o front consome.

    Existe porque sem eles o "P/L Liquido" sai IDENTICO ao bruto e as abas
    `Custos de Contas` e `Custo de Tipsters` saem vazias -- justamente a camada
    de operacao que separa o Sharpen de um tracker de apostador individual. Um
    print com R$ 0 ali nao mostra o recurso, esconde.

    Formatos (ver app.js `loadCT`/`loadCusto` e main.py):
      custo_conta   {"Fornecedor||Casa": numero}          -- por conta daquele par
      custo_tipster {"Tipster": {"AAAA-MM": "450,00"}}    -- string BR
      custo_geral   [{id, tipo, values:{"AAAA-MM": "..."}}]
    """
    rng = random.Random(semente ^ 0xC0570)
    meses = _meses(ate=ate)

    custo_conta = {}
    for c in ELENCO:
        chave = f"{c['fornecedor']}||{c['casa']}"
        if chave in custo_conta:
            continue
        base = _CUSTO_CASA.get(c["casa"], _CUSTO_CASA_PADRAO)
        # +-15%: fornecedor diferente cobra preco diferente pela mesma casa.
        custo_conta[chave] = float(round(base * rng.uniform(0.85, 1.15) / 10) * 10)

    custo_tipster = {}
    for nome, valor in _ASSINATURAS:
        # Nem toda assinatura corre os 6 meses: algumas comecam no meio, que e'
        # o normal (e faz a tela mostrar celula vazia, que tambem e' um estado).
        inicio = rng.choice([0, 0, 0, 1, 2])
        custo_tipster[nome] = {
            m: f"{valor:.2f}".replace(".", ",") for m in meses[inicio:]
        }

    custo_geral = [
        {"id": 1700000000000 + i, "tipo": tipo,
         "values": {m: f"{valor:.2f}".replace(".", ",") for m in meses}}
        for i, (tipo, valor) in enumerate(_CUSTOS_GERAIS)
    ]
    return custo_conta, custo_tipster, custo_geral


# ── Perfis de tipster (aba Tipster / Metodo) ─────────────────────────────────
# Contrato de `repository.list_tipsters_cadastro`. `completo` = tem ao menos um
# campo de info; a tela conta os incompletos num selo "N sem info", entao alguns
# ficam vazios DE PROPOSITO -- print com 100% preenchido esconde o onboarding.
_PERFIS = {
    "Linha Fria":     ("Bet365, Pinnacle", "ML, Handicap", "Futebol", "Fecha linha cedo; stake sobe quando a linha se move a favor."),
    "Corner Value":   ("Bet365, Betano", "Escanteios", "Futebol", "Só escanteios asiáticos, sempre ao vivo."),
    "Método Ártico":  ("Pinnacle, Betfair", "ML, Handicap", "Futebol, Tênis", "Modelo próprio de xG; opera pré-jogo."),
    "NBA Edge":       ("Bet365, Superbet", "Player Props, Assistência", "Basquete", "Props de armador; evita back-to-back."),
    "Sala 7":         ("Betano", "Múltipla", "Múltiplos", ""),
    "Contra-Ataque":  ("Bet365", "Anytime, Gols", "Futebol", "Marcador a qualquer momento em jogo de favorito."),
    "Régua":          ("Superbet, Betano", "Handicap", "Basquete", ""),
    "Pivô Alto":      ("Bet365", "Player Props, Pontos", "Basquete", "Rebotes e pontos de pivô."),
    "Quadra Rápida":  ("Betfair", "ML, Sets", "Tênis", ""),
    "Bloco Norte":    ("Bet365, Novibet", "Cartões, Escanteios", "Futebol", ""),
}


def cadastro_tipsters(semente=SEMENTE):
    """Lista no contrato de `/tipsters/cadastro`. Todo tipster do feed aparece --
    na producao a linha nasce sozinha quando um nome e' atribuido na extracao."""
    rng = random.Random(semente ^ 0x71B5)
    nomes = sorted({n for n, _ in TIPSTERS if n})
    saida = []
    for i, nome in enumerate(nomes, start=1):
        casas, mercados, esportes, obs = _PERFIS.get(nome, ("", "", "", ""))
        completo = bool(casas or mercados or esportes or obs)
        saida.append({
            "id": i, "nome": nome,
            "casas": casas or None, "mercados": mercados or None,
            "obs": obs or None,
            "stake_min": float(rng.choice([50, 100, 150])) if completo else None,
            "stake_max": float(rng.choice([400, 600, 900])) if completo else None,
            "apelidos": None, "dica_stake": None,
            "esportes": esportes or None,
            "arquivado": False,
            "criado_em": (date.today() - timedelta(days=180 + i)).isoformat(),
            "completo": completo,
        })
    return saida


def resumo(linhas):
    """Numeros de conferencia -- o print so vale se a base fizer sentido."""
    pl = sum(r["lucro"] for r in linhas)
    turnover = sum(r["stake"] for r in linhas)
    ganhas = sum(1 for r in linhas if r["resultado"] in ("W", "HW"))
    return {
        "apostas": len(linhas),
        "pl": round(pl, 2),
        "turnover": round(turnover, 2),
        "roi_pct": round(pl / turnover * 100, 2) if turnover else 0.0,
        "win_rate_pct": round(ganhas / len(linhas) * 100, 1) if linhas else 0.0,
        "odd_media": round(sum(r["odd"] for r in linhas) / len(linhas), 2) if linhas else 0,
        "de": linhas[0]["data"] if linhas else "",
        "ate": linhas[-1]["data"] if linhas else "",
    }


if __name__ == "__main__":
    import json
    dados = gerar()
    print(json.dumps(resumo(dados), indent=2, ensure_ascii=False))
