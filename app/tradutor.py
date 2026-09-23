"""Tradutor determinístico — Fase 1 do `docs/PLANO_TRADUTOR_DETERMINISTICO.md`.

Traduz o bloco de texto que o robô do SharpenUp emite (`extensor/content.js`) para as
três decisões que hoje custam uma chamada de IA: **esporte canônico**, **categoria de
aposta** e **descrição**. Os demais campos (código, data, stake, odd, resultado) já vêm
decididos pela casa e são cópia — este módulo os recorta junto para quem precisar.

    payload da casa -> inject -> bloco de texto -> TRADUTOR -> linha       [R$ 0]
                                                        \\- não sei -> IA  [pago]

INVARIANTE ÚNICA, e ela manda em todo o resto: **o tradutor nunca inventa.** Na dúvida
ele devolve `ok=False` com o motivo, e o chamador manda AQUELA linha para a IA. O modo de
falha aceitável é "custou dinheiro"; o inaceitável é "gravou errado em silêncio".

O QUE ESTE MÓDULO **NÃO** FAZ, de propósito:

  • **Não está ligado em lugar nenhum.** A Fase 1 entrega o motor desligado; a virada por
    casa é a Fase 3, e só depois do gate de divergência (< 1% em >= 500 bilhetes).
  • **Não calcula odd.** Onde a casa entrega a odd numa linha própria, copiamos; onde ela
    exige o produto das pernas ou `Retorno ÷ Stake`, o bilhete cai no fallback. Aritmética
    de odd é conta com consequência (s265: `3 x Duplas` herdando a odd da tripla) e entra
    num incremento próprio, com gate próprio.
  • **Não traduz nome de time.** A casa manda `USA (W)` na seleção e `EUA (F)` no
    confronto; a IA às vezes localiza e às vezes não (medido na sombra: o MESMO mercado,
    no mesmo dia, saiu dos dois jeitos). Aqui a seleção é copiada **verbatim**. Onde isso
    diverge da IA, o relatório de diff mostra — e localizar ou não é decisão humana.
  • **Não conhece casa além da Bet365.** Casa não portada devolve fallback com motivo.

DE ONDE VEM O MAPA: `casas/CASA_BET365.md §9` (a tabela curada por humano) mais os
rótulos que a sombra (`sombra_rotulos`) mediu em produção. Quando os dois divergem, o §9
manda — ele é a decisão, a sombra é a observação. Rótulo que a sombra viu e o §9 não
lista entra aqui marcado `# sombra`, e vira proposta de linha nova no §9.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, localcontext

# ── Estruturas ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Perna:
    """Uma seleção do bilhete, já recortada do bloco (ainda sem tradução)."""

    jogo: str        # como a casa escreveu: "Franca x Mogi das Cruzes"
    mercado: str     # rótulo bruto da casa: "Para Vencer a Partida"
    selecao: str     # "Mogi das Cruzes", "Mais de 2.5", "Fulano - Menos de 15.5"
    odd: str         # verbatim, precisão completa
    liga: str        # marcador da casa: "B-BRFPB" — contexto, não entra na saída

    @property
    def confronto(self) -> str:
        """`A v B` — a forma canônica do `MASTER_DESCRICAO`. O separador da casa varia
        (` x `, ` vs `, ` @ `) e nenhum deles é o nosso."""
        return _CONFRONTO_SEP.sub(" v ", self.jogo).strip()


@dataclass
class Traducao:
    """`ok=False` é resposta legítima, não erro: significa "manda esta para a IA"."""

    ok: bool
    motivo: str = ""            # por que caiu no fallback (vazio quando ok)
    esporte: str = ""
    aposta: str = ""
    descricao: str = ""
    codigo: str = ""
    data: str = ""
    stake: str = ""
    odd: str = ""
    resultado: str = ""
    pernas: tuple = field(default_factory=tuple)


# ── Mapa de mercados: rótulo da casa -> categoria + objeto do total ───────────
# `objeto` só existe em mercado contínuo (Over/Under): é a palavra que fecha a descrição
# (`Over 2.5 Gols`). `None` = a descrição é a própria seleção (ML, handicap).
# `por_esporte` = rótulo genérico cuja categoria segue o OBJETO, não o rótulo
# (`CASA_BET365 §9`: `Totais do Jogo` é Pontos no basquete e Gols no futebol).

_GOLS = {"cat": "Gols", "objeto": "Gols"}
_ESCANTEIOS = {"cat": "Escanteios", "objeto": "Escanteios"}
_PONTOS = {"cat": "Pontos", "objeto": "Pontos"}
_CARTOES = {"cat": "Cartões", "objeto": "Cartões"}
_ML = {"cat": "ML", "objeto": None}
_HANDICAP = {"cat": "Handicap", "objeto": None}
_ANYTIME = {"cat": "Anytime", "objeto": None}
_FALTAS = {"cat": "Faltas", "objeto": "Faltas"}

# Handicap carrega a UNIDADE no texto quando ela não é o placar do jogo:
# `Alcaraz -2.5 Games` (`MASTER_DESCRICAO §12.6`) e `Shi Yuqi -1.5 Sets` (§13.4, que diz
# "Handicap traz a unidade no texto"). O sufixo é por RÓTULO, nunca por esporte:
# no vôlei, `Partida - Handicap (Pontos)` sai sem unidade nas três amostras da sombra, e
# deduzir "handicap de pontos leva Pontos" a partir do handicap de sets seria inventar.
_HANDICAP_SETS = {"cat": "Handicap", "objeto": None, "sufixo": "Sets"}
_HANDICAP_GAMES = {"cat": "Handicap", "objeto": None, "sufixo": "Games"}

_TOTAL_GENERICO = {"por_esporte": {
    "Basquete": _PONTOS, "eBasket": _PONTOS, "Vôlei": _PONTOS,
    "Futebol": _GOLS, "eSoccer": _GOLS,
}}

_MERCADOS_BET365: dict = {
    # ── vindos do §9 da casa ──────────────────────────────────────────────────
    "para ganhar a partida": _ML,
    "para vencer a partida": _ML,
    "partida - vencedor": _ML,
    "handicap asiático": _HANDICAP,
    "handicap asiático - cartões": _CARTOES,
    "total de escanteios": _ESCANTEIOS,
    "total de escanteios asiáticos": _ESCANTEIOS,
    "total de escanteios - 3 opções": _ESCANTEIOS,
    "escanteios asiáticos": _ESCANTEIOS,
    "total de cartões asiáticos": _CARTOES,
    "totais do jogo": _TOTAL_GENERICO,
    "total - 2 opções": _TOTAL_GENERICO,
    "partida - total": _TOTAL_GENERICO,
    # ── vistos pela sombra (s301); propor como linha nova no §9 ───────────────
    "vencedor da partida": _ML,                                        # sombra
    "resultado final": _ML,                                            # sombra
    "gols + -": _GOLS,                                                 # sombra
    "total de gols": _GOLS,                                            # sombra
    "partida - gols": _GOLS,                                           # sombra
    "partida - handicap (pontos)": _HANDICAP,                          # sombra
    "handicap de pontos": _HANDICAP,                                   # sombra
    "handicap do jogo (sets)": _HANDICAP_SETS,                         # sombra
    "handicap - games ganhos - 2 opções": _HANDICAP_GAMES,             # sombra
    "pontos (mais de/menos de)": {"cat": "Player Props", "objeto": "Pontos"},
    # ── medidos na sombra em 09/09 (s333), 9.641 blocos ───────────────────────
    # DUAS RÉGUAS, e a segunda foi aprendida aqui. A primeira: entra rótulo cuja
    # maioria do que a IA decidiu seja >= 95%, com >= 5 casos de bilhete de UMA
    # seleção (na múltipla a categoria é `Múltipla`, estrutural, e não diz nada sobre
    # o rótulo). A segunda: **acertar a categoria não basta — a entrada só fica se a
    # DESCRIÇÃO dela também bater.** Dezessete rótulos passaram na primeira régua e
    # dez foram removidos pela segunda; ver a nota `PROPS DE SIM/NÃO` abaixo.
    # Abaixo das duas o rótulo fica de fora DE PROPÓSITO e o bilhete cai no fallback:
    # fallback custa dinheiro, chute grava errado.
    "para marcar a qualquer momento": _ANYTIME,                        # sombra 831
    "escanteios": _ESCANTEIOS,                                         # sombra 194
    "total de pontos - 2 opções": _PONTOS,                             # sombra  63
    "para ganhar a luta": _ML,                                         # sombra  26
    "para sofrer falta": _FALTAS,                                      # sombra  25
    "total de 180s": {"cat": "Player Props", "objeto": "180s"},        # sombra  11
    "total de jogos": {"cat": "Legs", "objeto": "Legs"},               # sombra  11
    # ── ABSOLVIDOS na s336, depois que a régua deixou de ser "concorda com a IA" ──
    # Os dois foram podados na s334 por divergirem 50% e 64% da IA. Relidos com o gate
    # novo, **as duas divergências inteiras são ruído da IA** e o tradutor está conforme
    # o MASTER em 100% dos casos:
    #   · `total de pontos` — a IA alterna `181,5` (vírgula, agora ERRO pelo §10.1) e
    #     localiza nome de país (`Sérbia` do bloco vira `Sérvia`). Nome é a limitação
    #     declarada no cabeçalho deste módulo, não defeito.
    #   · `corrida - handicap` — o tradutor copia `(Tempo de Finalização Menos 0 min 18
    #     segs)` verbatim e a IA abrevia de TRÊS jeitos (`-0:18`, `-0min18segs`,
    #     e o verbatim). Verboso do nosso lado, mas correto e estável.
    "total de pontos": _PONTOS,                                        # sombra  16
    "corrida - handicap": _HANDICAP,                                   # sombra  11
}

# ── PROPS DE SIM/NÃO E ESCOPO DE TEMPO: por que dez rótulos NÃO entraram ──────
# Medido na sombra em 09/09 (s333). Os dez abaixo têm categoria estável (maioria de
# 95% a 100%) e mesmo assim ficaram de fora, porque **a descrição deles não sai da
# seleção**. Duas famílias, e as duas pedem código, não linha de tabela:
#
#  1. **Prop de SIM/NÃO.** A seleção é `Sim`, e quem carrega a aposta é o RÓTULO:
#     `Terminar com Pontos` (52 casos, 98% de divergência na descrição) sai daqui
#     como `Franco Colapinto - Sim` e a IA escreve `Franco Colapinto - Terminar com
#     Pontos`. Mesma coisa em `Classificatórias - Para o Piloto Alcançar o Q3` (19),
#     `Finalização no Pódio` (22) e `Para marcar dois ou mais Gols` (19, onde o
#     rótulo vira `2+ Gols`). Falta ao motor um campo "o rótulo entra na descrição".
#
#  2. **Escopo de tempo.** `1º Tempo - Escanteios Asiáticos` (41, 98% de divergência)
#     sai `Over 3.5 Escanteios` e a IA escreve `Over 3.5 Escanteios 1º Tempo`. O
#     período NÃO é qualificador descartável como `Time da Casa -`: ele muda a aposta
#     e precisa aparecer. Enquanto `_QUALIFICADORES` só sabe descartar, período fica
#     de fora.
#
# ── REAVALIADOS na s336, com o gate novo (conformidade com o MASTER) ─────────
# Dois voltaram e estão no mapa acima (`total de pontos`, `corrida - handicap`).
# Os QUATRO abaixo continuam de fora, e agora cada um tem um motivo próprio e nomeado
# em vez do genérico "diverge da IA":
#
#  · **`Handicap - 2 Opções`** (55 casos, o maior). A IA escreve `Andy Hamilton -1.5
#    Legs` e o tradutor `-1.5`. **A IA está certa:** handicap carrega a UNIDADE quando
#    ela não é o placar (`MASTER_DESCRICAO §12.6/§13.4`), e em dardos a unidade é
#    `Legs`. Só que o mesmo rótulo aparece em outros esportes com outra unidade, e o
#    sufixo aqui é **por RÓTULO, nunca por esporte** (ver `_HANDICAP_SETS` acima).
#    Fazer sufixo por esporte é mudança de desenho, não linha de tabela.
#
#  · **`Primeiro Set - Vencedor`** (12). A IA acrescenta `1º Set` e o tradutor não.
#    Depende da **decisão D** (escopo de tempo), ainda aberta no `BACKLOG §3.8`.
#
#  · **`Qualificação - Apostas Comparativas`** e **`Corrida - Apostas Comparativas
#    (Equipe)`** (29 juntos). O tradutor escreve `George Russell (v Kimi Antonelli)`; a
#    IA move o adversário para o confronto. **A IA está estruturalmente certa:** H2H é
#    um confronto entre dois, e o adversário pertence ao `[A v B]`. Entrar exige montar
#    o confronto a partir da seleção, que é código novo.
#
# Os de prop de SIM/NÃO e escopo de tempo seguem na nota anterior: dependem de C e D.

# Famílias de rótulo PARAMETRIZADO — o que a tabela plana não alcança. Aqui a categoria
# vem do §9 ("outros props estatísticos individuais de jogador (Futebol) → Player Props")
# e o objeto vem do PRÓPRIO rótulo, verbatim: `Jogador - Faltas Cometidas - Alternativas`
# entrega `Faltas Cometidas`. Sem isso, cada estatística nova de jogador que a casa
# inventa (faltas, passes, desarmes…) seria uma linha nova de tabela — e uma chamada de
# IA até alguém notar. Regra só entra aqui quando o §9 já decide a categoria da família;
# adivinhar a categoria a partir do formato do rótulo seria inventar.
_REGRAS_BET365 = [
    (re.compile(r"^Jogador - (.+?)(?: - Alternativas)?$", re.I),
     lambda m: {"cat": "Player Props", "objeto": m.group(1).strip()}),
]

# Qualificadores de contexto: mudam QUANDO/ONDE a aposta vale, nunca a categoria
# (`CASA_BET365 §9`). Saem antes da consulta ao mapa.
_QUALIFICADORES = ("ao-vivo - ", "prorrogação - ", "time visitante - ", "time da casa - ")
_QUALIF_MAPA = re.compile(r"^mapa \d+ - ", re.I)
# Sufixo de CONTAGEM DE SAÍDAS (`- 2 Opções` = sem empate, `- 3 Opções` = com empate).
# Diz quantos resultados o mercado tem, não de que ele trata.
_OPCOES = re.compile(r"\s*-\s*\d+\s*op[çc][õo]es\s*$", re.I)

_MAPAS: dict = {"BET365": _MERCADOS_BET365}

# ── `Tipo: Múltipla` como VEREDITO de esporte — só onde a casa o emite assim ───
#
# A Bet365 não escreve `Esporte (casa):` em múltipla, porque não existe um esporte só, e
# o tradutor recusava o bilhete inteiro por "esporte não declarado" — 2.949 blocos de
# 28.473 na sombra de 23/09, 81,4% de todo aquele balde.
#
# A resposta estava no bloco, noutra linha. Quem escreve `Tipo: Múltipla` no bet365 é o
# `formatTicketB3` (`extensor/content.js`), e ele a escreve sob
# `multiplo = jogos.size >= 3 || cls.length > 1` — que É a regra do `MASTER_ESPORTES §2`
# (3+ confrontos DIFERENTES **ou** mistura de esportes). A mesma condição suprime a linha
# do esporte. Ou seja: a regra já tinha sido aplicada e nós é que não líamos a resposta.
#
# ⚠️ **O SINAL É DA CASA, NUNCA GLOBAL.** `formatTicketNV`, `formatTicketRG`,
# `formatTicket1X` e `formatTicketPN` também emitem `Tipo: Múltipla`, mas por `n > 1` —
# CONTAGEM DE PERNAS, não a regra do MASTER. Ler a linha como veredito numa dessas
# marcaria dupla de 2 jogos do MESMO esporte como `Múltiplos`, que o §2 proíbe. Casa nova
# só entra neste conjunto depois que alguém abrir o formatador dela e conferir a condição.
#
# DUAS PROVAS, e a segunda não passa pela IA (medição de 23/09, s383):
#  1. **Código.** Com 2 pernas, `jogos.size <= 2`, então a marca só pode ter vindo de
#     `cls.length > 1` = a casa viu mais de um CL = mistura de esportes.
#  2. **Empírica.** Mapa liga→esporte montado a partir dos blocos em que a casa DECLARA o
#     esporte (713 ligas, 713 resolvidas com >= 95% num esporte só) e aplicado aos 2.949:
#     nos 1.295 julgáveis, **1.295 têm as duas ligas em esportes diferentes — 100,00%,
#     zero contraexemplo.** Os 1.654 restantes são liga que nunca apareceu com esporte
#     declarado, dominados por `MLB` (799) e `NFL` (489) — beisebol e futebol americano
#     não têm CL no `_CL_B3`, e é por isso que eles nunca aparecem sozinhos.
#
# A IA discorda em 62 (2,1%) e está errada nos 62 — em vários o MESMO código foi lido
# duas vezes, uma dizendo `Futebol` e outra `Múltiplos` (a instabilidade do §II.9).
#
# ⚠️ **ISTO NÃO ENTREGA COBERTURA SOZINHO, e é bom saber antes de medir.** Os 2.949 só
# trocam de parede: 89,1% caem em seguida por rótulo fora do mapa, 10,0% pela odd
# combinada. A cobertura de uma múltipla é o E LÓGICO das pernas, e os esportes que só
# aparecem em múltipla (MLB, NFL) nunca tiveram o vocabulário aprendido. O que esta
# entrada compra é o balde parar de MENTIR: "esporte não declarado" era motivo falso para
# 2.949 bilhetes cujo esporte o tradutor sabe decidir.
_TIPO_MULTIPLA_E_VEREDITO = frozenset({"BET365"})
_TIPO_MULTIPLA = re.compile(r"^M[úu]ltipla\b", re.I)


# ── Recorte do bloco ──────────────────────────────────────────────────────────

_CONFRONTO_SEP = re.compile(r"\s+(?:x|vs|@|v)\s+", re.I)
_LINHA_SEL = re.compile(r"^\s*•\s+(.*)$")
_CAMPO = re.compile(r"^([^:]+):\s*(.*)$")
_SEL_ODD = re.compile(r"^(.*?)\s+@\s+([\d.,]+)\s*$")
_OVER_UNDER = re.compile(r"^(mais de|menos de)\s+(.+)$", re.I)
_JOGADOR_OU = re.compile(r"^(.+?)\s+-\s+(mais de|menos de)\s+(.+)$", re.I)
_HANDLE = re.compile(r"\([A-Z0-9][A-Z0-9 _.-]*\)\s*$")
_CL_NOME = re.compile(r"CL=\d+\s*\((.+?)\)")
_PLACAR_AO_VIVO = re.compile(r"^\(\d+\s*[-x:]\s*\d+\)\s*")
# Linha asiática partida — ver `_quarto_de_linha`. Gêmeos dos de `descricao_check`.
#
# TRÊS padrões, um por separador, e o motivo é que dois caracteres acumulam papéis:
#   `/`  separador limpo   → sinal permitido dos dois lados (`-0.5/-1.0`)
#   `,`  separador OU decimal → só conta como separador com decimais em PONTO
#   `-`  separador OU sinal   → só sem sinal, senão `-0.5-1.0` é indecifrável
# Handicap partido com sinal existe e é raro: 3 ocorrências (`-0.5,-1.0`) em 15.907
# blocos, todas Bet365. Raro não é inexistente, e o custo de cobrir é um regex.
_PARTIDA_BARRA = re.compile(r"([-+]?\d+[.,]\d+)\s*/\s*([-+]?\d+[.,]\d+)")
_PARTIDA_HIFEN = re.compile(r"(?<![-+\d])(\d+[.,]\d+)\s*-\s*(\d+[.,]\d+)")
_PARTIDA_VIRG = re.compile(r"([-+]?\d+\.\d+)\s*,\s*([-+]?\d+\.\d+)")
_ODD_LINHA = re.compile(r"^Odd(?:\s+total)?(?:\s+\(estrutural do sistema\))?$", re.I)


def _cabecalho(bloco: str) -> dict:
    """Campos `Rótulo: valor` do topo do bloco. Só a PRIMEIRA ocorrência de cada rótulo
    vale — o corpo da seleção repete rótulos (`Odd da perna:`) em outras casas."""
    campos: dict = {}
    for linha in bloco.splitlines():
        if _LINHA_SEL.match(linha) or linha.startswith(("  ", "\t", "- ")):
            continue
        m = _CAMPO.match(linha.strip())
        if m:
            campos.setdefault(m.group(1).strip(), m.group(2).strip())
    return campos


def _pernas(bloco: str) -> list:
    """Linhas de seleção da Bet365: `jogo · mercado · seleção @ odd · liga`.

    Linha com menos de 3 campos não é seleção reconhecível — devolvemos `[]` para o
    bilhete INTEIRO cair no fallback, em vez de traduzir metade dele."""
    out: list = []
    for linha in bloco.splitlines():
        m = _LINHA_SEL.match(linha)
        if not m:
            continue
        campos = [c.strip() for c in m.group(1).split(" · ")]
        if len(campos) < 3:
            return []
        jogo, mercado, resto = campos[0], campos[1], campos[2]
        liga = campos[3] if len(campos) > 3 else ""
        mo = _SEL_ODD.match(resto)
        selecao, odd = (mo.group(1).strip(), mo.group(2)) if mo else (resto, "")
        out.append(Perna(jogo=jogo, mercado=mercado, selecao=selecao, odd=odd, liga=liga))
    return out


def _sem_qualificador(rotulo: str) -> str:
    """Espaço colapsado e sem qualificador de contexto, **preservando a caixa** — as
    regras parametrizadas abaixo recortam o objeto do próprio rótulo e ele vai para a
    descrição do jeito que a casa escreveu."""
    r = re.sub(r"\s+", " ", (rotulo or "").strip())
    r = _QUALIF_MAPA.sub("", r)
    mudou = True
    while mudou:
        mudou = False
        for q in _QUALIFICADORES:
            if r.lower().startswith(q):
                r, mudou = r[len(q):].strip(), True
    return r


def _norm_mercado(rotulo: str) -> str:
    """A chave do mapa: `_sem_qualificador` em minúscula."""
    return _sem_qualificador(rotulo).lower()


def _spec(mapa: dict, mercado: str, esporte: str) -> dict:
    """Resolve o rótulo: primeiro a tabela, depois as famílias parametrizadas. Rótulo
    genérico exige o esporte para decidir o objeto — sem esporte conhecido devolve
    `None` (fallback), nunca um chute."""
    spec = mapa.get(_norm_mercado(mercado))
    if spec is None:
        for regra, monta in _REGRAS_BET365 if mapa is _MERCADOS_BET365 else ():
            m = regra.match(_sem_qualificador(mercado))
            if m:
                return monta(m)
        # `- N Opções` conta as SAÍDAS do mercado (com ou sem o empate), nunca muda a
        # categoria: `Total de Gols - 3 Opções` é Gols do mesmo jeito. É a última
        # tentativa, nunca a primeira — `Total - 2 Opções` está no mapa por inteiro, e
        # cortar o sufixo antes deixaria a chave em `total`, que não existe.
        sem_op = _OPCOES.sub("", _norm_mercado(mercado)).strip()
        if sem_op != _norm_mercado(mercado):
            spec = mapa.get(sem_op)
        if spec is None:
            return None
    if "por_esporte" in spec:
        return spec["por_esporte"].get(esporte or "")
    return spec


# ── Tradução das três decisões ────────────────────────────────────────────────


def _e_ebasket(pernas: list) -> bool:
    """eBasket = basquete virtual: os DOIS lados do confronto carregam o handle do gamer
    entre parênteses (`CASA_BET365 §9`). Exigir os dois lados é o que separa
    `DEN Nuggets (KOBRA) v ORL Magic (INVINCIBLE)` de `Canadá (F) v EUA (F)`."""
    if not pernas:
        return False
    for p in pernas:
        lados = _CONFRONTO_SEP.split(p.jogo)
        if len(lados) != 2 or not all(_HANDLE.search(lado.strip()) for lado in lados):
            return False
    return True


def _esporte(casa: str, cab: dict, pernas: list) -> str:
    """`Múltiplos` quando a acumulada tem 3+ confrontos distintos (`MASTER_ESPORTES §2`);
    senão o esporte que a casa declarou. `None` = não sei, vai para a IA.

    Bet builder (mesmo confronto em todas as pernas) NUNCA é `Múltiplos` — por isso a
    conta é de confrontos DISTINTOS, não de pernas.

    A OUTRA METADE DO §2 — a mistura de esportes — não é visível daqui: com o esporte
    suprimido, nada no bloco diz de que esporte é cada perna. Quem a enxergou foi a
    extensão, e em casa cujo formatador aplica o §2 ela deixa a resposta em
    `Tipo: Múltipla`. Ver `_TIPO_MULTIPLA_E_VEREDITO`, que é onde mora o porquê e o
    aviso de que essa linha significa outra coisa nas demais casas."""
    confrontos = {p.confronto for p in pernas}
    if len(pernas) >= 3 and len(confrontos) >= 3:
        return "Múltiplos"
    m = _CL_NOME.search(cab.get("Esporte (casa)", ""))
    if not m:
        if ((casa or "").upper() in _TIPO_MULTIPLA_E_VEREDITO
                and _TIPO_MULTIPLA.match((cab.get("Tipo") or "").strip())):
            return "Múltiplos"
        # Sem CL nomeado e sem o veredito da casa não há de onde tirar: bilhete de uma
        # seleção num esporte que o `_CL_B3` não mapeia (NFL e MLB são 672 dos blocos
        # medidos em 23/09) cai aqui e vai para a IA, que é o certo.
        return None
    nome = m.group(1).strip()
    if nome == "Basquete" and _e_ebasket(pernas):
        return "eBasket"
    return nome


def _quarto_de_linha(texto: str) -> str:
    """Troca toda linha asiática PARTIDA pelo quarto de linha. `MASTER_DESCRICAO §10.1.1`.

    `Mais de 2.0,2.5` → `Mais de 2.25` · `Menos de 2,5/3,0` → `Menos de 2.75`

    Fechado pelo Feca na s336, e o motivo é medição: **a Bet365 é a única casa que manda
    as duas linhas** (2.207 blocos); as outras 21 já mandam `2,25` direto. Sem converter,
    a MESMA aposta sairia descrita de dois jeitos conforme a casa.

    ⚠️ São DOIS padrões porque a vírgula acumula os papéis de decimal e de separador.
    Quando ela separa (`2.0,2.5`), o decimal é ponto; quando o separador é `/` ou `-`, o
    decimal pode ser vírgula (`2,5/3,0`). Um padrão só, com `[.,]` dos dois lados, leria
    `1,5` sozinho como um par. É a armadilha do `_num_bloco` do `repository`, e a gêmea
    desta função vive no `descricao_check._quartos_de_linha` — **as duas têm de andar
    juntas**: uma converte, a outra é o gate que aceita o convertido.
    """
    def troca(m):
        try:
            a = float(m.group(1).replace(",", "."))
            b = float(m.group(2).replace(",", "."))
        except ValueError:
            return m.group(0)
        return f"{(a + b) / 2:g}"

    for regra in (_PARTIDA_BARRA, _PARTIDA_HIFEN, _PARTIDA_VIRG):
        texto = regra.sub(troca, texto)
    return texto


def _descricao_perna(p, spec: dict) -> str:
    """Descrição de UMA perna, no formato do `MASTER_DESCRICAO`. `None` = não sei."""
    objeto = spec.get("objeto")
    # Mercado ao vivo prefixa a seleção com o placar do momento (`(0-0) Time -0.5`). É
    # estado do jogo, não parte da aposta: sai antes de qualquer template.
    sel = _PLACAR_AO_VIVO.sub("", re.sub(r"\s+", " ", p.selecao).strip()).strip()
    # §10.1.1: o quarto de linha vale nos DOIS ramos abaixo — o handicap (sem objeto)
    # também vem partido em algumas casas (`Time -0.0,-0.5`).
    sel = _quarto_de_linha(sel)
    if objeto:
        # Player prop: "Fulano - Menos de 15.5" -> "Fulano - Under 15.5 Pontos"
        mj = _JOGADOR_OU.match(sel)
        if mj:
            lado = "Over" if mj.group(2).lower() == "mais de" else "Under"
            return f"{mj.group(1).strip()} - {lado} {mj.group(3).strip()} {objeto} [{p.confronto}]"
        mo = _OVER_UNDER.match(sel)
        if mo:
            lado = "Over" if mo.group(1).lower() == "mais de" else "Under"
            return f"{lado} {mo.group(2).strip()} {objeto} [{p.confronto}]"
        # Mercado contínuo cuja seleção não é Mais/Menos (ex.: "3 Opções", com empate):
        # o template não se aplica, e adivinhar seria inventar.
        return None
    sufixo = spec.get("sufixo")
    return f"{sel}{' ' + sufixo if sufixo else ''} [{p.confronto}]"


# ── Número lido do BLOCO CRU ──────────────────────────────────────────────────
#
# Veio do `repository` na s386, quando ganhou um segundo chamador (a odd estrutural
# abaixo, que precisa de `Decimal`). A régua é UMA e mora aqui; o `repository` reexporta.


def _sep_bloco(s) -> tuple:
    """`(texto, decimal, milhar)` do número como o bloco o escreve. `None` se ilegível.

    O ÚLTIMO separador é o decimal, decidido por TOKEN — a **Betfair mistura as duas
    convenções no mesmo bloco**: stake e odd em BR (`300,00`, `5,4746`) e o retorno em EN
    (`Retorno 1,642.38`). Uma régua BR-first leria 1,64238 e o gate "corrigiria" a odd
    5,4746 para 0,0054, destruindo cinco linhas certas (medido na s321).

    Um separador só é SEMPRE decimal, mesmo com 3 dígitos depois: a regra "3 dígitos =
    milhar" serve a dinheiro e destrói ODD (`1,775` viraria 1775). Não há ambiguidade a
    perder — todo valor monetário nos blocos sai do `_brl`, que sempre imprime 2 casas.

    NÃO substitui o `_num_or_none` do `repository`: aquele é a convenção do BANCO e do TSV.
    """
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    i_ponto, i_virg = s.rfind("."), s.rfind(",")
    if i_ponto >= 0 and i_virg >= 0:
        return (s, ".", ",") if i_ponto > i_virg else (s, ",", ".")
    if i_virg >= 0:
        return s, ",", "."
    if i_ponto >= 0:
        return s, ".", ","
    return s, None, None


def _limpo_bloco(s) -> str:
    """O número do bloco com o decimal em ponto e sem milhar — a forma que `float` e
    `Decimal` leem igual."""
    partes = _sep_bloco(s)
    if partes is None:
        return None
    texto, dec, mil = partes
    return texto if dec is None else texto.replace(mil, "").replace(dec, ".")


def _num_bloco(s) -> float | None:
    """Número lido do BLOCO CRU, em BR (`1.642,38`) ou EN (`1,642.38`). Ver `_sep_bloco`."""
    t = _limpo_bloco(s)
    if t is None:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _dec_bloco(s):
    """O mesmo, em `Decimal`. Existe porque a odd estrutural é uma MULTIPLICAÇÃO, e em
    `float` ela devolve lixo binário (`1.95 * 1.8 = 3.5100000000000002`) onde a conta
    exata é `3,51`. Mesma régua de separador, nunca uma segunda."""
    t = _limpo_bloco(s)
    if t is None:
        return None
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


_RESULTADO = re.compile(r"→\s*(HW|HL|W|L|V)\b")


def _resultado(status: str) -> str:
    """O inject já escreve a conclusão (`Ganho -> W`). Copiamos; não reinterpretamos.
    Aberta não tem seta e sai vazio — que é o código de "não liquidada"."""
    m = _RESULTADO.search(status or "")
    return m.group(1) if m else ""


# ── A odd da MÚLTIPLA COMUM: o produto das pernas (s386) ─────────────────────
#
# A Bet365 NÃO entrega a odd combinada: medido em 23/09, **zero de 3.442 blocos
# `Tipo: Múltipla` traz linha de odd** (o `formatTicketB3` só imprime `Odd:` quando
# `nSel === 1`, e `Odd total`/`Odd (estrutural do sistema)` só em SISTEMA). Sem isto o
# guard da odd recusava TODA múltipla da casa — e recusava por último, depois do rótulo,
# então a parede ficava escondida atrás do vocabulário.
#
# O `MASTER_RESULTADO §7.1` decide quando a odd estrutural é a resposta, e o §7.2 diz o
# que ela é numa múltipla comum: **o produto das odds das pernas**. Só entram as três
# linhas em que o §7.1 manda usá-la; `W` fica de FORA de propósito (ver abaixo).
#
# ⚠️ **SISTEMA NÃO É MÚLTIPLA, e confundir os dois é o caso da s265** (`3 x Duplas` lida
# como tripla: odd 5,81 no lugar de 3,282, retorno potencial R$ 1.762 no lugar de R$ 994).
# Aqui a confusão é impossível por construção: bloco de sistema TRAZ linha de odd (a média
# das linhas, já calculada pela casa), então nunca chega a este caminho.
#
# A PROVA, e ela é do DINHEIRO, não da IA (23/09, sombra da Bet365): nas múltiplas GANHAS
# a casa publica o retorno, e `stake × produto` bate o retorno **ao centavo em 479 de 529
# (90,5%)**. Os 50 que não batem são perna ANULADA (`GT8020619111I`: duas pernas @ 2,2 e
# retorno = 2,2 × stake — a outra virou 1,00) e meia vitória de linha asiática. Os dois
# casos só se conhecem pelo dinheiro, e os dois são `W`.
#
# **Por que `W` fica de fora.** Ali o §7.1 manda `Retorno ÷ Stake`, e essa conta é
# justamente a que ESCONDE meia vitória: o `_resultadoB3` escreve `Ganho → W` para
# qualquer retorno maior que a stake, e fechar a conta por `retorno ÷ stake` deixa o
# bilhete internamente consistente — `stake × odd` bate exato — sem nunca chegar a `HW`
# (`CLAUDE.md`, o caso da s356). Quem separa os dois é o `_veredito_do_retorno`, no
# servidor, e não este módulo. Então `W`, `HW` e `HL` continuam indo para a IA.
#
# **O que o produto NÃO enxerga, e a IA também não:** perna anulada em bilhete `L` ou
# ABERTO. O bloco imprime a odd original de toda perna e não marca void, então a odd
# estrutural sai alta. Em `L` isso não move dinheiro nenhum (P/L de `L` é −stake); em
# aberto ele infla o retorno potencial da tela. Fica registrado porque é o limite honesto
# da regra, não porque haja o que fazer com o dado de hoje.
_ODD_E_O_PRODUTO_DAS_PERNAS = frozenset({"BET365"})
# Os DOIS ramos do `formatTicketB3` que declaram "a odd é o produto das odds abaixo":
# `Tipo: Múltipla (N seleções)` (múltipla pelo §2) e `Tipo: N seleções` (a dupla de mesmo
# esporte, que é múltipla comum pelo §7.2 mesmo sem ser `Múltiplos` pelo §2).
_TIPO_MULTIPLA_COMUM = re.compile(r"^(?:M[úu]ltipla\b|\d+\s+sele)", re.I)
# `MASTER_RESULTADO §7.1`: L sem cashout, V e aberta usam a odd ESTRUTURAL.
_RESULTADO_COM_ODD_ESTRUTURAL = frozenset({"", "L", "V"})
# Precisão, em DUAS etapas, e a segunda existe por medição.
#
# A odd da perna chega como renderização de `float64` da fração da casa: 23/15 vira
# `1,5333333333333332`. Multiplicar isso EXATO propaga o ruído — `1,5 × 1,5333333333333332`
# dá `2,2999999999999998`, e a odd da casa é `2,3` (bilhete real `LP2437618471I`).
#
# Então: multiplica com folga (34 dígitos, para o produto de doze pernas não perder nada
# no caminho) e **corta o resultado em 15 dígitos significativos, que é o piso de ruído do
# `float64` da entrada**. Abaixo dali não há informação, só artefato binário.
#
# 15 dígitos é ordens de grandeza acima do que o `MASTER_RESULTADO §7.2` exige: o que ele
# proíbe é arredondar para 2 casas, porque aí a planilha pt-BR corrompe a odd.
_PRECISAO_PRODUTO = 34
_PRECISAO_ODD = 15


def _odd_estrutural(casa: str, cab: dict, pernas: list) -> str:
    """O produto das odds das pernas, em vírgula decimal. `""` = não sei, vai para a IA.

    Recusa em silêncio (devolvendo `""`) é o comportamento certo: o chamador transforma
    isso no fallback nomeado. Perna sem odd legível, ou com odd <= 1, derruba o bilhete
    INTEIRO — meia conta é pior que conta nenhuma."""
    if (casa or "").upper() not in _ODD_E_O_PRODUTO_DAS_PERNAS:
        return ""
    if not _TIPO_MULTIPLA_COMUM.match((cab.get("Tipo") or "").strip()):
        return ""
    if _resultado(cab.get("Status", "")) not in _RESULTADO_COM_ODD_ESTRUTURAL:
        return ""
    with localcontext() as ctx:
        ctx.prec = _PRECISAO_PRODUTO
        produto = Decimal(1)
        for p in pernas:
            d = _dec_bloco(p.odd)
            if d is None or d <= 1:
                return ""
            produto *= d
    with localcontext() as ctx:
        ctx.prec = _PRECISAO_ODD
        produto = +produto          # `+` é o que aplica o corte do contexto
    return _odd_br(produto)


def _odd_br(valor) -> str:
    """`Decimal` → o texto que o resto do sistema espera: vírgula decimal, sem expoente e
    sem zero à toa. `MASTER_RESULTADO §7.2` — a planilha pt-BR lê o ponto como milhar e
    corrompe a odd (`8.580978` viraria `8.580.978`)."""
    n = valor.normalize()
    if n == n.to_integral_value():
        n = n.quantize(Decimal(1))
    return format(n, "f").replace(".", ",")


def traduzir(casa: str, bloco: str) -> Traducao:
    """Traduz um bloco de bilhete. Nunca levanta; nunca chuta.

    `casa` é a CHAVE da casa (`BET365`), não o nome de exibição."""
    mapa = _MAPAS.get((casa or "").upper())
    if mapa is None:
        return Traducao(False, f"casa não portada: {casa}")

    pernas = _pernas(bloco)
    if not pernas:
        return Traducao(False, "nenhuma linha de seleção reconhecida")

    cab = _cabecalho(bloco)
    esporte = _esporte(casa, cab, pernas)
    if not esporte:
        return Traducao(False, "esporte não declarado pela casa", pernas=tuple(pernas))

    # O esporte que resolve o rótulo genérico é o do JOGO, não `Múltiplos` — numa
    # acumulada o objeto de cada perna segue o esporte dela, e daqui só se vê um CL.
    # Na múltipla decidida por `Tipo: Múltipla` não se vê nem isso: `esporte_obj` fica
    # vazio e todo rótulo genérico cai no fallback, de propósito. Deduzir o objeto pela
    # grandeza da linha (`154.5` "parece" basquete) é o que este módulo não faz.
    esporte_obj = esporte
    if esporte == "Múltiplos":
        m = _CL_NOME.search(cab.get("Esporte (casa)", ""))
        esporte_obj = m.group(1).strip() if m else ""

    descricoes: list = []
    cat_perna = ""
    for p in pernas:
        spec = _spec(mapa, p.mercado, esporte_obj)
        if spec is None:
            return Traducao(False, f"mercado desconhecido: {p.mercado!r}", pernas=tuple(pernas))
        d = _descricao_perna(p, spec)
        if d is None:
            return Traducao(False, f"seleção fora do template: {p.selecao!r}", pernas=tuple(pernas))
        descricoes.append(d)
        cat_perna = spec["cat"]

    aposta = "Múltipla" if len(pernas) > 1 else cat_perna

    odd = ""
    for rotulo, valor in cab.items():
        if _ODD_LINHA.match(rotulo.strip()):
            odd = valor.split()[0] if valor else ""
            break
    if not odd and len(pernas) > 1:
        # A casa não publicou a combinada. Onde o `MASTER_RESULTADO §7.1` manda usar a
        # odd ESTRUTURAL, ela é o produto das pernas e sai daqui — ver `_odd_estrutural`,
        # que é quem conhece as três condições e recusa em todo o resto.
        odd = _odd_estrutural(casa, cab, pernas)
    if not odd and len(pernas) > 1:
        return Traducao(False, "odd combinada não entregue pela casa", pernas=tuple(pernas))

    return Traducao(
        True,
        esporte=esporte,
        aposta=aposta,
        descricao=" // ".join(descricoes),
        codigo=cab.get("Código", ""),
        data=next((v for k, v in cab.items() if k.startswith("Data")), ""),
        stake=cab.get("Stake", ""),
        odd=odd,
        resultado=_resultado(cab.get("Status", "")),
        pernas=tuple(pernas),
    )
