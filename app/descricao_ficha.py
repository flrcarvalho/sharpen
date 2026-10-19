"""Dicionário de DESCRIÇÃO da Ficha (Feca, 12/10/2026; s413).

Regra do Feca: **chamada extra à IA só para a descrição, nunca.** O mercado é aprendido UMA vez,
sem lado e sem linha: `1-st half corner over 4.5`, `over 3.5` e `under 5.5` são o mesmo mercado,
e depois de aprendido nenhuma variação dele vai à IA.

  • chave (`chave`) = `<esporte da casa> | <mercado da casa normalizado>`: minúsculo, número vira
    `{n}`, o lado colado à linha sai (`acima de (2.5)` → `({n})`), o time do jogo vira `{time}`.
    Sem a seleção. O ESPORTE entra porque o mesmo mercado da casa se escreve diferente por
    esporte: `1st half - total` é `Gols 1º Tempo` no futebol e `Pontos 1ª Metade` no basquete
    (medido: sem o esporte, 62 mercados se contradiziam; `MASTER_DESCRICAO §12.10`).
  • valor = o nome do mercado no padrão do Sharpen (`MASTER_DESCRICAO`), tirado da descrição que
    a IA escreveu para a mesma perna (`aprender`): sem lado, linha, time e `[jogo]`. Onde eles
    estavam ficam marcas, para a Ficha montar na MESMA posição em que a IA monta:
        `Over 4.5 Escanteios 1º Tempo`        → `{ou} Escanteios {n1}º Tempo`
        `Patrick Queen - Under 3.5 Desarmes`  → `{ent} - {ou} Desarmes`
        `Bayern de Munique -3.5 Escanteios`   → `{ent} {hc} Escanteios`
        `Shelbayh Abedallah 1º Set` (`Winner. Set 1`) → `{ent} {n1}º Set`
    `{ent}` = a seleção (`1`/`2`/`X` viram o nome do time ou `Empate`), `{ou}` = `Over/Under X.X`,
    `{hc}` = a linha com sinal, `{mais}` = `N+`, `{time}` = o time escrito no mercado, `{t1}`/`{t2}`
    = os times do jogo, `{nK}` = o K-ésimo número do mercado (o `1` do `Set 1`: o número do
    período não é a linha, e por isso não fica fixo no valor). `nome_do_mercado` tira as marcas
    para mostrar ao Feca (`Escanteios 1º Tempo`).
  • montagem (`montar`): perna por perna, `<valor> [A v B]`, unidas por ` // `. Mercado sem
    valor, valor que pede uma marca que a perna não tem, ou número do cru (a linha) que não
    chegou à descrição: None, e a aposta vai para a IA (`descrição fora do dicionário`).

Voto (`votos`, a semente em `dicionario.votar`): a descrição da IA só ensina quando FECHA com o
cru: o mesmo jogo, a mesma linha, o mesmo lado, a mesma seleção. A IA escreve o MESMO mercado de
jeitos diferentes (`Time - Over 4.5` e `Time Over 4.5`; `1º Tempo` e `1ª Metade`): `canonico`
junta essas variantes num voto só, e o valor guardado é a variante mais votada dentro dele.

Nomes vêm como o cru manda (`Leclerc, Charles`), sem reordenar (`MASTER_DESCRICAO §9`); para
ACHAR o nome na descrição da IA, que às vezes reordena, valem as variantes (`_variantes`).
O separador do jogo é sempre ` v ` (`MASTER_DESCRICAO §5`), nunca `vs`/`vs.`/` - `.

s415 (T1): **o nome do jogador também sai da chave**, como o número virou `{n}`. A DEX escreve o
jogador DENTRO do mercado (`Alec Peters. Ressaltos. Com prorrogação`), e cada jogador novo era
uma chave nova, indo para a IA. `_jogador` acha o nome no começo do mercado; ele vira
`{jogador}` na chave e no valor (`{jogador}. ressaltos. com prorrogação` → `{jogador} - {ou}
Rebotes`) quando a IA escreveu esse mesmo nome.

s416 (D29, Feca, 14/10/2026): a contradição de DESCRIÇÃO se decide por regra (`decidir`) e
nunca manda a aposta à IA; o estilo (minuto, `Ressaltos`/`Rebounds`, `PRA`) é um voto só
(`estilo`, D27).
E o handicap da 1xBet (`Handicap 1 (-1.5)`, `Handicap 2 (1.5)`) é um mercado só: o lado vira o
`{time}` e o sinal com a linha vira `{hc}`.
"""
from __future__ import annotations

import re
import unicodedata

PERNAS = " // "
SEP = " | "                      # esporte da casa | mercado da casa
_NUM = re.compile(r"\d+(?:[.,]\d+)*")
_LADO = {"over": "Over", "acima": "Over", "mais": "Over", ">": "Over",
         "under": "Under", "abaixo": "Under", "menos": "Under", "<": "Under"}
_PAL_LADO = r"over|under|acima|abaixo|mais|menos"
# seleção com lado: `Over 92.5`, `mais de 6.5`, `Patrick Queen (PIT) under 3.5`, `Abaixo` (+ linha)
_SEL_LADO = re.compile(rf"^(?P<ent>.*?)\s*\b(?P<lado>{_PAL_LADO})\b(?:\s+de)?\s*"
                       r"(?P<num>[+-]?\d+(?:[.,]\d+)*)?$", re.I)
# seleção de handicap: `Peristeri (+6)`, `PSV U19 +0.5`, `Colorado Avalanche (-2.5)`
_SEL_HC = re.compile(r"^(?P<ent>.+?)\s*\(?(?P<hc>[+-]\d+(?:\.\d+)?)\)?$")
# s416: a 1win escreve o handicap POSITIVO sem sinal (`FC Slavia Mozyr 1.5`): só em mercado de
# handicap, o número no fim da seleção é a linha, com `+`
_SEL_HC_SEM_SINAL = re.compile(r"^(?P<ent>.+?)\s+\(?(?P<hc>\d+(?:\.\d+)?)\)?$")
_SEL_MAIS = re.compile(r"^(?P<num>\d+)\+$")
# o lado dentro do MERCADO (a 1xBet escreve a seleção ali): `Total acima de (2.5)`, `Total < (78.5)`
_MERC_LADO = re.compile(rf"\b(?P<lado>{_PAL_LADO})\b(?:\s+de)?\s*\(?(?P<num>\d+(?:[.,]\d+)*)\)?|"
                        r"(?P<sinal>[<>])\s*\(?(?P<num2>\d+(?:[.,]\d+)*)\)?", re.I)
# seleção que é CÓDIGO (Feca, s413): `1`/`2` viram o nome do time, `X` vira `Empate`
_CODIGO = {"1": 0, "2": 1, "w1": 0, "w2": 1, "v1": 0, "v2": 1, "p1": 0, "p2": 1}
_EMPATE = {"x", "empate", "draw"}
_SEP_JOGO = (" vs. ", " vs ", " v ", " - ")
_SUFIXO = re.compile(r"\s+(\d+\.[ªº]\s+\w+)$")          # `1.ª parte`, `3.º quarto` (1xBet)
# s415: `Individual Total 1 (0.5)` (Megapari) também diz QUAL time
_INDICE = re.compile(r"\b(equipa|team|time|individual total|individual|handicap)\s+([12])\b",
                     re.I)
_PARENS_COD = re.compile(r"\s*\([A-Z]{2,4}\)\s*$")      # `Patrick Queen (PIT)`
MARCAS = ("{ent}", "{ou}", "{hc}", "{mais}", "{time}", "{t1}", "{t2}", "{jogador}")
# s415: o handicap da 1xBet no mercado (`Handicap 1 (-1.5)`, `Handicap 2 (1.5) Sets`,
# `Handicap 2 -1 In 10 Minute`): o índice diz o time e o número (com sinal) é a linha
_HC_MERC = re.compile(r"\bhandicap\s+([12])\s*(?:\(\s*([+-]?\d+(?:[.,]\d+)?)\s*\)|([+-]\d+(?:[.,]\d+)?))",
                      re.I)
# s415 (T1): o jogador no começo do mercado (DEX): `Alec Peters. Ressaltos. Com prorrogação`,
# `Jerian Grant Total de pontos. Com prorrogação`. Duas palavras ou mais, cada uma com
# maiúscula (partícula de nome no meio vale), antes do primeiro `. ` ou de um `Total`. O ponto
# de abreviação é do nome (`Kyle Pitts Sr. Total receções`).
_FIM_JOGADOR = re.compile(r"\.(?=\s)|\s+(?=[Tt]otal\b)")      # Bet Panda: `… total de remates`
_ABREV = frozenset({"jr", "sr", "st", "ii", "iii", "iv"})
_PARTICULA = frozenset({"de", "da", "do", "dos", "das", "van", "von", "der", "den", "di", "del",
                        "la", "le", "du", "bin", "al", "e"})
# Palavra de MERCADO não é nome: `Double Chance. 1st Half` não tem jogador
_NAO_NOME = frozenset({"total", "totals", "winner", "vencedor", "handicap", "match", "partida",
                       "double", "chance", "dupla", "corners", "escanteios", "cantos", "cards",
                       "cartões", "both", "ambas", "draw", "empate", "result", "resultado",
                       "half", "tempo", "set", "quarter", "quarto", "period", "período", "game",
                       "jogo", "map", "mapa", "race", "odd", "even", "exact", "correct", "score",
                       "placar", "asian", "european", "europeu", "team", "equipa", "equipe",
                       "player", "jogador", "goals", "gols", "points", "pontos", "first", "last",
                       "next", "to", "win", "over", "under", "mais", "menos", "yes", "no",
                       "sim", "não", "and", "or", "ou", "with", "com", "overtime",
                       "prorrogação", "bookings", "booking", "offsides", "fouls", "shots",
                       # s416: o LADO do jogo não é jogador (`Time de Fora total de escanteios`)
                       "time", "fora", "casa", "home", "away", "hometeam", "awayteam",
                       "visitante", "mandante"})
# Letra cirílica no lugar da latina (a Megapari escreve `Handiсap` com o `с` cirílico)
_HOMOGLIFOS = str.maketrans({"с": "c", "а": "a", "е": "e", "о": "o", "р": "p", "х": "x"})
_MARCA = re.compile(r"\{[a-z0-9]+\}")
# O recorte de período por esporte (`MASTER_DESCRICAO §12.10`): a IA escreve `1º Tempo` e
# `1ª Metade` no basquete quase meio a meio, e o Master decide. Esporte do Sharpen (o que o
# dicionário traduziu), não o da casa.
_METADE = frozenset({"Basquete", "Futebol Americano"})
_TEMPO = frozenset({"Futebol", "Handebol", "Futsal"})
_ENT_LINHA = re.compile(r"(\{(?:ent|time|t1|t2)\}) - (\{(?:ou|hc|mais)\})")
# Mercado de UM time (o nome dele no mercado, ou o lado: `Time de casa total de cartões`): a
# descrição da IA sem o time é erro dela (o total do time vira o total do jogo) e não vota.
# Medido (s413): na MyStake esse voto derrubava os mercados de cartões e chutes por time.
_DO_TIME = re.compile(r"\b(time de casa|time de fora|hometeam|awayteam|home team|away team|"
                      r"equipa [12]|individual [12]|individual total [12]|do time de casa|"
                      r"do time de fora)\b")
_MARCA_TIME = re.compile(r"\{(?:time|t1|t2|ent)\}")


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def _sem_acento(s: str) -> str:
    """Mesmo comprimento do original (um caractere por caractere): o índice vale nos dois."""
    return "".join(unicodedata.normalize("NFKD", c)[0] for c in s).casefold()


def _variantes(nome: str) -> list[str]:
    """O nome como veio e como a IA às vezes o reescreve: `Leclerc, Charles` → `Charles
    Leclerc`; `Wang Y H / Xie Z` → `Wang Y H/Xie Z`."""
    out = [nome]
    partes = [p.strip() for p in re.split(r"\s*/\s*", nome)]
    vira = [" ".join(reversed([x.strip() for x in p.split(",", 1)])) if p.count(",") == 1 else p
            for p in partes]
    for v in ("/".join(partes), " / ".join(vira), "/".join(vira)):
        if v not in out:
            out.append(v)
    return out


def _achar(texto: str, alvo: str) -> tuple[int, int]:
    """(início, comprimento) do nome no texto, por qualquer variante; (-1, 0) se não achou."""
    if not alvo:
        return -1, 0
    t = _sem_acento(texto)
    for v in sorted(_variantes(alvo), key=len, reverse=True):
        a = _sem_acento(v)
        # palavra inteira: o time `A` não está dentro de `total`
        m = re.search(rf"(?<!\w){re.escape(a)}(?!\w)", t)
        if m:
            return m.start(), len(v)
    return -1, 0


def _canon_nome(nome: str) -> str:
    """Para comparar o jogo do cru com o da IA: sem acento, sem vírgula, palavras em ordem."""
    return " ".join(sorted(re.sub(r"[,/]", " ", _sem_acento(nome)).split()))


def _times(evento: str) -> tuple[str, str, str, str]:
    """(time 1, time 2, prefixo do subjogo, sufixo do subjogo). A 1xBet escreve o subjogo no
    nome do jogo (`Cantos A - Cantos B 1.ª parte`): o prefixo comum e o sufixo de período saem
    dos times e entram no mercado. Só no jogo com ` - `, o separador dela."""
    ev = _limpo(evento)
    for sep in _SEP_JOGO:
        if sep in ev:
            a, b = ev.split(sep, 1)
            break
    else:
        return "", "", "", ""
    pre = suf = ""
    if sep == " - ":
        m = _SUFIXO.search(b)
        if m:
            suf, b = m.group(1), b[:m.start()]
        wa, wb = a.split(), b.split()
        n = 0
        while n < min(len(wa), len(wb)) - 1 and wa[n] == wb[n]:
            n += 1
        if n:
            pre, a, b = " ".join(wa[:n]), " ".join(wa[n:]), " ".join(wb[n:])
    return a.strip(), b.strip(), pre, suf


def jogo(evento: str) -> str:
    """`A v B` sem o subjogo; evento que não é um confronto (prova, torneio) não vira jogo:
    a descrição fica sem colchete (`MASTER_DESCRICAO §8`). O nome fica como o cru manda: a IA
    vira `Leclerc, Charles` em metade das vezes e na outra não (medido, s413), e o
    `MASTER_DESCRICAO §9` manda não mexer em entidade."""
    t1, t2, _, _ = _times(evento)
    return f"{t1} v {t2}" if t1 and t2 else ""


def _mesmo_jogo(a: str, b: str) -> bool:
    pa, pb = re.split(r"\s+v\s+", a), re.split(r"\s+v\s+", b)
    return len(pa) == len(pb) and all(_canon_nome(x) == _canon_nome(y) for x, y in zip(pa, pb))


def _num(s: str) -> str:
    return s.replace(",", ".")


def _forma_num(n: str) -> str:
    return n.rstrip("0").rstrip(".") if "." in n else n


def _jogador(merc: str, times=()) -> str:
    """O nome do jogador no começo do mercado, ou `""`. Time do jogo não é jogador (ele já vira
    `{time}`), nem trecho com palavra de mercado (`_NAO_NOME`)."""
    nome = ""
    merc = merc or ""
    for m in _FIM_JOGADOR.finditer(merc):
        antes = merc[:m.start()].split()
        if m.group(0).startswith(".") and antes and antes[-1].casefold() in _ABREV:
            continue                                   # o ponto é do nome
        nome = merc[:m.start()].strip()               # `Kyle Pitts Sr.` leva o ponto junto
        break
    ws = nome.split()
    if len(ws) < 2:
        return ""
    for i, w in enumerate(ws):
        if w.casefold() in _NAO_NOME or any(c.isdigit() for c in w):
            return ""
        if 0 < i < len(ws) - 1 and w.casefold() in _PARTICULA:
            continue
        if not w[0].isupper():
            return ""
    for t in times:
        if t and (_achar(nome, t)[0] >= 0 or _achar(t, nome)[0] >= 0):
            return ""
    return nome


def mercado_com_jogador(p: dict) -> str | None:
    """O mercado da casa com o jogador trocado por `{jogador}` (a chave de CATEGORIA do
    `dicionario`), ou None quando o mercado não começa por um jogador."""
    merc = _limpo(p.get("mercado_casa")).translate(_HOMOGLIFOS)
    t1, t2, _, _ = _times(p.get("evento"))
    nome = _jogador(merc, (t1, t2))
    i = merc.find(nome) if nome else -1
    return merc[:i] + "{jogador}" + merc[i + len(nome):] if i >= 0 else None


def decompor(p: dict) -> dict:
    """As peças de uma perna, sem IA: seleção, lado e linha, handicap, `N+`, times, jogador, e
    o mercado efetivo (com o subjogo da 1xBet) de onde saem a chave e os `{nK}`."""
    t1, t2, pre, suf = _times(p.get("evento"))
    sel = _limpo(p.get("selecao_casa"))
    merc = _limpo(p.get("mercado_casa")).translate(_HOMOGLIFOS)
    linha = _limpo(p.get("linha"))
    d = {"t1": t1, "t2": t2, "ent": "", "ou": "", "hc": "", "mais": "", "time": "",
         "codigo": False, "jogador": _jogador(merc, (t1, t2))}
    alvo = sel or merc                                # 1xBet: a seleção mora no mercado
    sn = alvo.casefold()
    if sn in _CODIGO or sn in _EMPATE:
        d["codigo"] = True
        d["ent"] = "Empate" if sn in _EMPATE else (t1, t2)[_CODIGO[sn]]
        if linha and linha[0] in "+-":
            d["hc"] = _num(linha)
    elif sel:
        m, h, n = _SEL_LADO.match(sel), _SEL_HC.match(sel), _SEL_MAIS.match(sel)
        hs = (_SEL_HC_SEM_SINAL.match(sel)
              if not h and "handicap" in merc.casefold() else None)
        if m and (m.group("num") or linha):
            num = m.group("num") or linha
            d["ou"] = f"{_LADO[m.group('lado').lower()]} {_num(num.lstrip('+'))}"
            d["ent"] = _PARENS_COD.sub("", m.group("ent")).strip()
        elif h:
            d["ent"], d["hc"] = h.group("ent").strip(), _num(h.group("hc"))
        elif hs:
            n0 = _num(hs.group("hc"))
            d["ent"], d["hc"] = hs.group("ent").strip(), n0 if float(n0) == 0 else "+" + n0
        elif n:
            d["mais"] = f"{n.group('num')}+"
        else:
            d["ent"] = sel
    else:
        m = _MERC_LADO.search(merc)
        if m:
            lado = (m.group("lado") or m.group("sinal")).lower()
            d["ou"] = f"{_LADO[lado]} {_num(m.group('num') or m.group('num2'))}"
        mi = _INDICE.search(merc)
        if mi:
            d["time"] = (t1, t2)[int(mi.group(2)) - 1]
        mh = _HC_MERC.search(merc)
        if mh and not d["ou"]:
            n = _num(mh.group(2) or mh.group(3))
            d["hc"] = n if n[0] in "+-" or float(n) == 0 else "+" + n
    if not d["time"]:
        for t in (t1, t2):
            if t and _achar(merc, t)[0] >= 0:
                d["time"] = t
                break
    d["efetivo"] = " ".join(x for x in (pre, merc, suf) if x)
    d["nums"] = [_num(x) for x in _NUM.findall(d["efetivo"])]
    d["fieis"] = _fieis(sel, linha, merc, d)
    return d


def _fieis(sel: str, linha: str, merc: str, d: dict) -> list[str]:
    """Os números do cru que a descrição TEM de trazer (a linha, o `N+`): número que não chega
    à descrição é aposta descrita errado, e aí ela vai para a IA."""
    out = []
    if sel and not d["codigo"]:
        out += _NUM.findall(sel)
    if linha:
        out += _NUM.findall(linha)
    if not sel and merc:                               # 1xBet: a linha está no mercado
        m = _MERC_LADO.search(merc)
        if m:
            out.append(m.group("num") or m.group("num2"))
        elif d["hc"]:
            out.append(d["hc"].lstrip("+-"))
    return [_num(x) for x in out]


def chave(p: dict, d: dict | None = None, jogador: bool = False) -> str:
    """`<esporte da casa> | <mercado>`: sem lado, sem linha, sem seleção e sem o time do jogo.
    `jogador=True`: o jogador do começo do mercado vira `{jogador}` (s415)."""
    d = d or decompor(p)
    esporte = " ".join(str(p.get("esporte_casa") or "").casefold().split())
    s = d["efetivo"]
    # o nome pode vir depois do subjogo da 1xBet (`players' stats Breanna Stewart total …`)
    if jogador and d["jogador"] and (i := s.find(d["jogador"])) >= 0:
        s = s[:i] + "{jogador}" + s[i + len(d["jogador"]):]
    if d["hc"] and not _limpo(p.get("selecao_casa")):
        s = _HC_MERC.sub("handicap {hc}", s, count=1)      # o lado e o sinal saem (s415)
    for t in (d["t1"], d["t2"]):
        i, n = _achar(s, t) if t else (-1, 0)
        if i >= 0:
            s = s[:i] + "{time}" + s[i + n:]
    # `Equipa 1` / `Equipa 2` dizem QUAL time: o número fica (é seleção, não linha)
    s = _INDICE.sub(lambda m: f"{m.group(1)} §{'ab'[int(m.group(2)) - 1]}", s)
    s = " ".join(s.casefold().split())
    s = re.sub(rf"\b({_PAL_LADO})\b(\s+de)?\s*(\(?){_NUM.pattern}(\)?)", r"\3{n}\4", s)
    s = re.sub(rf"[<>]\s*(\(?){_NUM.pattern}(\)?)", r"\1{n}\2", s)
    s = _NUM.sub("{n}", s)
    return esporte + SEP + s.replace("§a", "1").replace("§b", "2")


def chaves_da_perna(p: dict) -> set[str]:
    """As chaves que a montagem desta perna consulta: a do mercado e, com jogador, a de
    `{jogador}` (s415)."""
    d = decompor(p)
    return {chave(p, d), chave(p, d, jogador=True)}


def aprender(p: dict, desc_perna: str, d: dict | None = None, k: str | None = None) -> str | None:
    """O valor que a descrição da IA ensina para a chave desta perna, ou None quando a
    descrição não fecha com o cru (jogo, lado, linha ou seleção diferentes: o voto não vale)."""
    d = d or decompor(p)
    s = _limpo(desc_perna)
    m = re.search(r"\s*\[([^\[\]]*)\]$", s)
    if m:
        if not _mesmo_jogo(_limpo(m.group(1)), jogo(p.get("evento"))):
            return None
        s = s[:m.start()]
    elif d["t1"]:
        return None                                   # jogo no cru e não na descrição
    usados = set()
    for marca, valor in (("{ou}", d["ou"]), ("{hc}", d["hc"]), ("{mais}", d["mais"]),
                         ("{jogador}", d["jogador"]), ("{ent}", d["ent"]), ("{time}", d["time"]),
                         ("{t1}", d["t1"]), ("{t2}", d["t2"])):
        if not valor or valor in usados:
            continue
        i, n = _achar(s, valor)
        if i < 0:
            if marca in ("{ou}", "{hc}", "{mais}", "{ent}", "{time}"):
                return None                           # a IA não escreveu o que o cru diz
            continue
        s = s[:i] + marca + s[i + n:]
        usados.add(valor)
    # o jogo fora dos colchetes não é mercado (`MASTER_DESCRICAO §4`)
    if "{t1} v {t2}" in s or "{t1} v {ent}" in s or "{ent} v {t2}" in s:
        return None
    # número que sobrou tem de ser um número do mercado (o período: `Set 1` → `{n1}`)
    nums = [_forma_num(x) for x in d["nums"]]

    def trocar(mm):
        x = _forma_num(_num(mm.group(0)))
        if x in nums:
            return "{n%d}" % (nums.index(x) + 1)
        raise ValueError(x)
    try:
        s = "".join(x if _MARCA.fullmatch(x) else _NUM.sub(trocar, x)
                    for x in re.split(r"(\{[a-z0-9]+\})", s))
    except ValueError:
        return None
    s = " ".join(s.split())
    # nome próprio do jogo que sobrou no valor: aposta de outro jogo ou leitura errada
    resto = _sem_acento(_MARCA.sub(" ", s))
    for t in (d["t1"], d["t2"], d["ent"]):
        for w in re.findall(r"[^\W\d_]{4,}", t or ""):
            if re.search(rf"\b{re.escape(_sem_acento(w))}\b", resto):
                return None
    return s or None


def canonico(valor: str) -> str:
    """As variantes que a IA escreve para o MESMO mercado viram um voto só: o ` - ` entre o
    time e a linha, `1ª Metade` × `1º Tempo` (`MASTER_DESCRICAO §12.10`) e, desde o D29, o
    ESTILO (`estilo`: minuto, nome da estatística do jogador)."""
    s = _ENT_LINHA.sub(r"\1 \2", estilo(valor))
    s = re.sub(r"(\{[a-z0-9]+\}) - ", r"\1 ", s)
    return re.sub(r"(\{n\d+\}|\d+)ª Metade", r"\1º Tempo", s)


# ── D29 (Feca, 14/10/2026): a contradição de DESCRIÇÃO se decide por regra ─────────────────
# Mercado de descrição nunca vai à IA por contradição. Ordem (`decidir`): a. total puro → só
# `{ou}`; b. a forma escrita com palavras do Master; c. a forma que escreve o mercado vence a
# que traz só o time; d. estilo não é voto diferente (`estilo`, já no agrupamento); e. a mais
# votada, e o termo vai para a revisão. A categoria e o esporte seguem com a maioria de 90%.

# d. o minuto: `{n}min`, `{n} Min`, `({n} min)`, `{n}º Minuto`, `no/até o {n}º Minuto`,
# `até {n}'`, `(até Min {n})`, `In {n} Minute`, `{n} Minutos`, `Primeiros {n} Minutos` são o
# mesmo recorte. O Master não tem forma para ele: fica `{n}min`.
_MINUTO = (
    (re.compile(r"\(\s*até\s+min\.?\s+(\{n\d+\})\s*\)", re.I), r"\1min"),
    (re.compile(r"(?:\bprimeiros\s+)?(?:\b(?:até|no|in)\s+(?:o\s+)?)?(\{n\d+\})\s*(?:º\s*minuto|"
                r"minutos|minute|min)\b\.?", re.I), r"\1min"),
    (re.compile(r"\(\s*(\{n\d+\}min)\s*\)"), r"\1"),
)
_ATE_APOS = re.compile(r"\baté\s+(\{n\d+\})'", re.I)
# d. (D27) as estatísticas do jogador: `Ressaltos` e `Rebounds` são `Rebotes`, `Assists` é
# `Assistências`, e `PRA` (em qualquer ordem e grafia) é `Pontos + Assistências + Rebotes`.
# D31 (s417): `Pontos + Rebotes` e `Rebotes + Assistências`, nessa ordem, em qualquer ordem e
# grafia de entrada. Outra combinação fica como veio (só a grafia): não decidida.
_ESTAT = {"rebotes": "Rebotes", "ressaltos": "Rebotes", "rebounds": "Rebotes",
          "assistências": "Assistências", "assistencias": "Assistências",
          "assists": "Assistências", "pontos": "Pontos", "points": "Pontos"}
_COMBO = re.compile(r"\b(pontos|points|rebotes|ressaltos|rebounds|assist[eê]ncias|assists)"
                    r"(?:\s*\+\s*(pontos|points|rebotes|ressaltos|rebounds|assist[eê]ncias|"
                    r"assists))+\b|\bPRA\b", re.I)
_PRA = "Pontos + Assistências + Rebotes"
_PA = "Pontos + Assistências"
_PR = "Pontos + Rebotes"
_RA = "Rebotes + Assistências"


def _combo(m) -> str:
    t = m.group(0)
    if t.upper() == "PRA":
        return _PRA
    nomes = [_ESTAT[x.casefold()] for x in re.split(r"\s*\+\s*", t)]
    if len(set(nomes)) != len(nomes):
        return t
    if set(nomes) == {"Pontos", "Assistências", "Rebotes"}:
        return _PRA
    if set(nomes) == {"Pontos", "Assistências"}:
        return _PA
    if set(nomes) == {"Pontos", "Rebotes"}:
        return _PR
    if set(nomes) == {"Rebotes", "Assistências"}:
        return _RA
    return " + ".join(nomes)                          # combinação não decidida: só a grafia


def estilo(valor: str) -> str:
    """A forma única do ESTILO (D29 d, D27): o minuto e o nome da estatística do jogador."""
    s = _ATE_APOS.sub(r"\1min", valor or "")
    for rx, novo in _MINUTO:
        s = rx.sub(novo, s)
    s = _COMBO.sub(_combo, s)
    s = re.sub(r"\b(Ressaltos|Rebounds)\b", "Rebotes", s)
    s = re.sub(r"\bAssists\b", "Assistências", s)
    # D35 (Feca, 19/10): `Mortes`, `kills` e `Abates` são `Kills`, em todas as casas
    s = re.sub(r"\b(?:mortes|kills|abates)\b", "Kills", s, flags=re.I)
    return " ".join(s.split())


# a. o total PURO: sem objeto (D24), só `{ou}`
_TOTAL_PURO = re.compile(r"^total(?: jogos)?(?:\.? com prorrogação| \(incl\. (?:ot|overtime|"
                         r"prorrogação)\)| \(incluindo (?:prolongamento|prorrogação)"
                         r"(?: e penalties)?\))?$")


def _palavras(valor: str) -> list[str]:
    s = _MARCA.sub(" ", re.sub(r"\{n\d+\}", " ", valor or "")).replace("º", " ").replace("ª", " ")
    return re.findall(r"[^\W\d_]+", s)


_VOCAB_MASTER: frozenset | None = None


def vocab_master() -> frozenset:
    """As palavras com que o Master escreve uma descrição: os exemplos (` ```text `) do
    `MASTER_DESCRICAO`, mais os nomes das categorias e dos esportes. Lido, nunca copiado."""
    global _VOCAB_MASTER
    if _VOCAB_MASTER is None:
        import taxonomia
        t = taxonomia._ler("MASTER_DESCRICAO_2026.md")
        txt = " ".join(re.sub(r"\[[^\]]*\]", " ", b) for b in re.findall(r"```text\n(.*?)```", t,
                                                                          re.S))
        txt += " " + " ".join(taxonomia.categorias_canonicas()) + " " + \
            " ".join(taxonomia.esportes_canonicos())
        _VOCAB_MASTER = frozenset(w.casefold() for w in re.findall(r"[^\W\d_]+", txt))
    return _VOCAB_MASTER


def decidir(chave_desc: str, votos) -> tuple[str, str]:
    """(valor, regra) de uma chave de descrição com os votos `{valor: n}` (D29). `regra` =
    `unico` (um grupo só), `a`, `b`, `c`, `e` (a mais votada; vai para a revisão) ou
    `e-empate` (empate exato no topo, decidido pela ordem alfabética; revisão também). Nunca
    devolve contradição: a descrição não vai à IA por isso."""
    from collections import Counter
    grupos: dict = {}
    for v, n in votos.items():
        grupos.setdefault(canonico(v), Counter())[v] += n

    def forma(g):                                    # a variante mais votada, no estilo único
        c = grupos[g]
        return estilo(max(c, key=lambda v: (c[v], v)))

    def peso(g):
        return sum(grupos[g].values())
    if len(grupos) == 1:
        return forma(next(iter(grupos))), "unico"
    merc = chave_desc.split(SEP, 1)[-1]
    if _TOTAL_PURO.match(merc) and all("{ou}" in g for g in grupos):
        return "{ou}", "a"
    vocab = vocab_master()

    def fora(g):                                     # palavras que o Master não usa
        return sum(1 for w in _palavras(g) if w.casefold() not in vocab and w != "min")

    def esqueleto(g):                                # as marcas e quantas palavras
        return tuple(_MARCA.findall(re.sub(r"\{n\d+\}", "{n}", g))), len(_palavras(g))
    # b. só entre formas do MESMO esqueleto (a IA TROCOU uma palavra: `Rebounds` × `Rebotes`,
    # `Most Hits` × `Mais Hits`): fica a com menos palavras fora do Master. Forma que OMITE
    # parte do mercado (`{time} {ou} Gols` sem o minuto) não é troca de palavra, e não ganha aqui.
    restam = [g for g in grupos
              if fora(g) == min(fora(h) for h in grupos if esqueleto(h) == esqueleto(g))]
    if len(restam) == 1:
        return forma(restam[0]), "b"
    # c. escreve o mercado = tem palavra de verdade (do Master ou de 4 letras ou mais): `VFL`
    # não é mercado
    c = [g for g in restam if any(w.casefold() in vocab or len(w) >= 4 for w in _palavras(g))]
    if len(c) == 1 and len(c) < len(restam):
        return forma(c[0]), "c"
    if c:
        restam = c
    topo = max(restam, key=lambda g: (peso(g), g))
    # empate EXATO no topo: não há "mais votada", e quem decide é a ordem alfabética. Vai para
    # a revisão marcado, para o consultor olhar primeiro
    empate = sum(1 for g in restam if peso(g) == peso(topo)) > 1
    return forma(topo), "e-empate" if empate else "e"


def nome_do_mercado(valor: str) -> str:
    """O nome do mercado sem as marcas, para mostrar (`{ou} Escanteios {n1}º Tempo` →
    `Escanteios Nº Tempo`)."""
    s = re.sub(r"\{n\d+\}", "N", valor or "")
    return " ".join(_MARCA.sub(" ", s).replace(" - ", " ").split()) or "(só a seleção)"


def montar_perna(p: dict, valor: str, d: dict | None = None,
                 esporte: str | None = None) -> str | None:
    """A descrição de UMA perna pelo valor do dicionário. `esporte` = o esporte do Sharpen da
    perna, para o recorte de período do Master (§12.10)."""
    d = d or decompor(p)
    out = valor
    for marca in MARCAS:
        if marca in out:
            v = d[marca[1:-1]]
            if not v:
                return None                           # o valor pede o que a perna não tem
            out = out.replace(marca, v)
    for k, n in enumerate(d["nums"], 1):
        out = out.replace("{n%d}" % k, _forma_num(n))
    if _MARCA.search(out):
        return None
    out = " ".join(out.split())
    if esporte in _METADE:
        out = re.sub(r"(\d+)º Tempo\b", r"\1ª Metade", out)
    elif esporte in _TEMPO:
        out = re.sub(r"(\d+)ª Metade\b", r"\1º Tempo", out)
    for n in d["fieis"]:
        if n not in out and _forma_num(n) not in out:
            return None
    j = jogo(p.get("evento"))
    return f"{out} [{j}]" if j else out


def montar(f: dict, termos: dict, propria=None) -> tuple[str | None, list[str]]:
    """(descrição, chaves que faltam). `termos` = o dicionário da casa ({("descricao", chave):
    valor}). `propria(perna)` = a forma fixada pelo Feca (`dicionario.descricao_perna`), que
    vence o dicionário."""
    partes, faltam = [], []
    for p in f.get("pernas") or []:
        if propria and (x := propria(p)):
            partes.append(x)
            continue
        d = decompor(p)
        # s415: o mercado de QUALQUER jogador vem primeiro; a chave com o nome dele é a do
        # Feca, se um dia ele corrigir um jogador só (a semente não vota mais nela, D29)
        ks = [chave(p, d, jogador=True)] if d["jogador"] else []
        ks.append(chave(p, d))
        valor = None
        for k in ks:
            if (valor := termos.get(("descricao", k))) is not None:
                break
        k = ks[0] if valor is None else k
        esporte = termos.get(("esporte", " ".join(str(p.get("esporte_casa") or "").lower().split())))
        x = montar_perna(p, valor, d, esporte) if valor is not None else None
        if x is None:
            faltam.append(k)
        else:
            partes.append(x)
    if faltam or not partes:
        return None, faltam
    return PERNAS.join(partes), []


def alinhar(pernas: list[dict], descricao: str) -> list[tuple[dict, str]]:
    """Pareia cada perna com o trecho da descrição da IA do MESMO jogo (a IA nem sempre segue a
    ordem do cru). Trecho ou perna sem par único fica de fora."""
    trechos = [t.strip() for t in (descricao or "").split(PERNAS) if t.strip()]
    if len(pernas) == 1 and len(trechos) == 1:
        return [(pernas[0], trechos[0])]
    out = []
    for p in pernas:
        j = jogo(p.get("evento"))
        mesmos = [p2 for p2 in pernas if _mesmo_jogo(jogo(p2.get("evento")), j)]
        ts = [t for t in trechos
              if (m := re.search(r"\[([^\[\]]*)\]$", t)) and _mesmo_jogo(_limpo(m.group(1)), j)]
        if len(mesmos) == 1 and len(ts) == 1:
            out.append((p, ts[0]))
    return out


def votos(f: dict, descricao: str) -> list[tuple[str, str]]:
    """[(chave, valor)] que uma descrição da IA ensina, perna a perna. Só vota o que, montado
    de volta, dá uma descrição (o valor não pede o que a perna não tem)."""
    out = []
    for p, t in alinhar(f.get("pernas") or [], descricao):
        d = decompor(p)
        k = chave(p, d)
        v = aprender(p, t, d, k)
        if v is None or montar_perna(p, v, d) is None:
            continue
        if "{jogador}" in v:
            # s415: a IA escreveu o jogador do cru, e o voto vai para a chave de QUALQUER
            # jogador. (Na s415 ia também para a chave DESTE jogador, para quando a de qualquer
            # um ficasse contradita; desde o D29, s416, a descrição nunca fica contradita.)
            k = chave(p, d, jogador=True)
        # mercado do LADO sem o time: errado (o do NOME do time já cai no `aprender`, que exige
        # o `{time}` que o cru tem)
        if _DO_TIME.search(k) and not _MARCA_TIME.search(v):
            continue
        out.append((k, v))
    return out
