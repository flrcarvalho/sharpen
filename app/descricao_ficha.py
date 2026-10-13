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
Ressaltos`) quando a IA escreveu esse mesmo nome. O voto vale também na chave do próprio
jogador (com o nome, como antes): a de qualquer jogador é consultada primeiro, e a dele só
entra quando a de qualquer um está contradita.
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
                       "prorrogação", "bookings", "booking", "offsides", "fouls", "shots"})
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
    for m in _FIM_JOGADOR.finditer(merc or ""):
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
    return "{jogador}" + merc[len(nome):] if nome else None


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
        if m and (m.group("num") or linha):
            num = m.group("num") or linha
            d["ou"] = f"{_LADO[m.group('lado').lower()]} {_num(num.lstrip('+'))}"
            d["ent"] = _PARENS_COD.sub("", m.group("ent")).strip()
        elif h:
            d["ent"], d["hc"] = h.group("ent").strip(), _num(h.group("hc"))
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
    if jogador and d["jogador"] and s.startswith(d["jogador"]):
        s = "{jogador}" + s[len(d["jogador"]):]
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
    time e a linha, e `1ª Metade` × `1º Tempo` (`MASTER_DESCRICAO §12.10`)."""
    s = _ENT_LINHA.sub(r"\1 \2", valor)
    return re.sub(r"(\{n\d+\}|\d+)ª Metade", r"\1º Tempo", s)


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
        # s415: o mercado de QUALQUER jogador vem primeiro (é o que a maioria decidiu; a chave
        # deste jogador guarda só o voto dele, e entra quando a de qualquer um está contradita)
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
            # s415: a IA escreveu o jogador do cru. O voto vai para a chave de QUALQUER jogador
            # e também para a deste jogador, com o nome no valor, como antes: a de qualquer
            # jogador pode ficar contradita (a IA escreve `Ressaltos`, `Rebotes` e `Rebounds`
            # para o mesmo mercado), e aí a deste jogador ainda o descreve.
            out.append((k, v.replace("{jogador}", d["jogador"])))
            k = chave(p, d, jogador=True)
        # mercado do LADO sem o time: errado (o do NOME do time já cai no `aprender`, que exige
        # o `{time}` que o cru tem)
        if _DO_TIME.search(k) and not _MARCA_TIME.search(v):
            continue
        out.append((k, v))
    return out
