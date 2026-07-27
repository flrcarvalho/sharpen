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
SEMENTE = 20260727
DONO = "Ricardo"          # persona da demonstracao, nao e' usuario real
N_APOSTAS = 24000
DIAS = 210                 # dias com aposta na base real

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
CONTAS = [f"{n} [{f}]" for f in _FORNECEDORES for n in _NOMES]

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
    p = min(0.93, (1.0 / odd) * 1.045)
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
        parceiro = rng.choice(CONTAS)
        conta, _, forn = parceiro.partition(" [")
        linhas.append({
            "id": 100000 + i,
            "data": dia.isoformat(),
            "esporte": esporte,
            "tipster": _sorteia(rng, TIPSTERS),
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
