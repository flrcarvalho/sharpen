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


def _esporte(cab: dict, pernas: list) -> str:
    """`Múltiplos` quando a acumulada tem 3+ confrontos distintos (`MASTER_ESPORTES §2`);
    senão o esporte que a casa declarou. `None` = não sei, vai para a IA.

    Bet builder (mesmo confronto em todas as pernas) NUNCA é `Múltiplos` — por isso a
    conta é de confrontos DISTINTOS, não de pernas."""
    confrontos = {p.confronto for p in pernas}
    if len(pernas) >= 3 and len(confrontos) >= 3:
        return "Múltiplos"
    m = _CL_NOME.search(cab.get("Esporte (casa)", ""))
    if not m:
        # Sem CL nomeado não há de onde tirar. E numa múltipla de 2 pernas o inject
        # omite a linha quando os esportes DIVERGEM — mas "omitiu porque divergem" e
        # "omitiu porque o CL é desconhecido" são indistinguíveis daqui.
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


_RESULTADO = re.compile(r"→\s*(HW|HL|W|L|V)\b")


def _resultado(status: str) -> str:
    """O inject já escreve a conclusão (`Ganho -> W`). Copiamos; não reinterpretamos.
    Aberta não tem seta e sai vazio — que é o código de "não liquidada"."""
    m = _RESULTADO.search(status or "")
    return m.group(1) if m else ""


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
    esporte = _esporte(cab, pernas)
    if not esporte:
        return Traducao(False, "esporte não declarado pela casa", pernas=tuple(pernas))

    # O esporte que resolve o rótulo genérico é o do JOGO, não `Múltiplos` — numa
    # acumulada o objeto de cada perna segue o esporte dela, e daqui só se vê um CL.
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
