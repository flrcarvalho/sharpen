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
}

# Qualificadores de contexto: mudam QUANDO/ONDE a aposta vale, nunca a categoria
# (`CASA_BET365 §9`). Saem antes da consulta ao mapa.
_QUALIFICADORES = ("ao-vivo - ", "prorrogação - ", "time visitante - ", "time da casa - ")
_QUALIF_MAPA = re.compile(r"^mapa \d+ - ", re.I)

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


def _norm_mercado(rotulo: str) -> str:
    """Minúscula, espaço colapsado e sem qualificador de contexto."""
    r = re.sub(r"\s+", " ", (rotulo or "").strip()).lower()
    r = _QUALIF_MAPA.sub("", r)
    mudou = True
    while mudou:
        mudou = False
        for q in _QUALIFICADORES:
            if r.startswith(q):
                r, mudou = r[len(q):].strip(), True
    return r


def _spec(mapa: dict, mercado: str, esporte: str) -> dict:
    """Resolve o rótulo no mapa. Rótulo genérico exige o esporte para decidir o objeto —
    sem esporte conhecido devolve `None` (fallback), nunca um chute."""
    spec = mapa.get(_norm_mercado(mercado))
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


def _descricao_perna(p, spec: dict) -> str:
    """Descrição de UMA perna, no formato do `MASTER_DESCRICAO`. `None` = não sei."""
    objeto = spec.get("objeto")
    # Mercado ao vivo prefixa a seleção com o placar do momento (`(0-0) Time -0.5`). É
    # estado do jogo, não parte da aposta: sai antes de qualquer template.
    sel = _PLACAR_AO_VIVO.sub("", re.sub(r"\s+", " ", p.selecao).strip()).strip()
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
