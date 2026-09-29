"""Juiz PELA FONTE da Bet365 (s386): confere o SIGNIFICADO de uma linha contra o bloco cru.

Concordar com o Sonnet, com a produção ou com o banco não prova acerto — os três já
erraram medidamente (odd com dígitos trocados, descrição sem o objeto). Este juiz lê o
bloco e pergunta, seleção a seleção: o time/jogador está lá? a direção (Over/Under)? a
linha? o objeto do mercado? o período? o time do total de time? toda perna apareceu?

REAPROVEITA, NÃO REIMPLEMENTA (coordenação com a frente do tradutor): o recorte da
perna (`tradutor._pernas`), o mapa CURADO de rótulo → categoria/objeto
(`tradutor._spec` sobre `_MERCADOS_BET365`, que nasce do `CASA_BET365 §9`), o esporte
(`tradutor._esporte`) e o quarto de linha (`tradutor._quarto_de_linha`). O único recorte
próprio é o da perna de Criar Aposta (sub-linhas `–`), que o tradutor recusa de propósito.

CLASSES (cada achado tem uma):
  erro_real        o SENTIDO está errado ou falta: time, jogador, direção, linha, sinal
                   de handicap, objeto, período, time do total de time, perna.
  forma            o sentido está certo e a forma fere o MASTER (Over/Under em português,
                   vírgula decimal na descrição).
  permitida        mesmo sentido, grafia diferente (10 x 10.0; nome com acento).
  categoria        a categoria diverge do mapa curado (regra de produto, não de sentido;
                   relatada à parte).
  nao_verificavel  o juiz não sabe decidir (rótulo fora do mapa curado, formato que ele
                   não lê). NUNCA conta como acerto nem como erro.
Categoria e esporte: esperados pelo mapa curado quando o rótulo é conhecido; senão,
`nao_verificavel`.

LIMITES DECLARADOS: só Bet365; nome traduzido (USA→EUA) sai como erro_real de time e
precisa de revisão humana (é a medida das FALHAS DO JUIZ, feita por amostra).
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app"))
import tradutor as trad  # noqa: E402

_SUB = re.compile(r"^\s+–\s+(.*)$")
_PERNA = re.compile(r"^\s*•\s+(.*)$")
_SEP_JOGO = re.compile(r"\s+(x|@|vs|v)\s+", re.I)
_DIR = re.compile(r"\b(mais de|menos de|over|under)\b", re.I)
_NUM = re.compile(r"[-+]?\d+(?:[.,]\d+)?")
_PERIODO = re.compile(r"\b(1º|2º|1ª|2ª|primeiro|segundo)\s+(tempo|set|metade|quarto|per[ií]odo|mapa)\b", re.I)


# rótulo (normalizado) -> alguma destas raízes tem de estar na descrição (fora do confronto)
_PROP_SIM = [("marcar ou dar", ("assist", "ou dar", "g+a", "gol ou")),
             ("dar assist", ("assist",)),
             ("receber cart", ("cart",)),
             ("de cabeca", ("cabeca",)),
             ("fora da area", ("fora da",))]


# rótulo/seleção (normalizado) -> alguma raiz tem de estar na descrição; nome do qualificador
_QUALIF_SENTIDO = [("sofrer falta", ("sofr",), "falta SOFRIDA (Faltas = cometida)"),
                   ("primeiros 10 minutos", ("10",), "primeiros 10 minutos"),
                   ("jardas de recepcao", ("recep",), "jardas de RECEPÇÃO"),
                   ("jardas de corrida", ("corrida", "rush"), "jardas de CORRIDA"),
                   ("jardas de passe", ("passe", "pass"), "jardas de PASSE"),
                   ("sera expulso", ("expul", "vermelho"), "expulsão (não cartão comum)"),
                   ("significativos", ("signific",), "golpes SIGNIFICATIVOS")]


def _f(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9.+\- ]", " ", s)


def _tokens(nome: str) -> list:
    return [t for t in _f(nome).split() if len(t) >= 3 and not t.isdigit()]


def _tem_nome(nome: str, desc_f: str) -> str:
    """'todo' | 'parte' | 'nada' — quantos tokens significativos do nome estão na descrição."""
    ts = _tokens(nome)
    if not ts:
        return "todo"
    achou = sum(1 for t in ts if re.search(r"\b" + re.escape(t) + r"\b", desc_f))
    return "todo" if achou == len(ts) else "parte" if achou else "nada"


def unidades(bruto: str) -> list:
    """Cada SELEÇÃO do bloco: {jogo, times, casa_idx, mercado, selecao}. Perna de Criar
    Aposta vira uma unidade por sub-linha, com o jogo do cabeçalho."""
    out, jogo_bb = [], None
    linhas = (bruto or "").split("Seleções:", 1)[-1].splitlines()
    for ln in linhas:
        m = _PERNA.match(ln)
        if m:
            corpo = m.group(1)
            campos = [c.strip() for c in corpo.split(" · ")]
            if len(campos) >= 3:
                jogo_bb = None
                sel = re.sub(r"\s+@\s+[\d.,]+\s*$", "", campos[2]).strip()
                # mercado COMBINADO ("Dupla Resultado e Total"): cada condição é uma unidade
                conds = [c.strip() for c in sel.split(" & ")] or [sel]
                for cond in conds:
                    u = _unid(campos[0], campos[1], cond)
                    u["combo"] = len(conds) > 1
                    out.append(u)
            else:                                   # cabeçalho de Criar Aposta
                jogo_bb = re.sub(r"\s+@\s+[\d.,]+.*$", "", campos[0]).strip()
            continue
        s = _SUB.match(ln)
        if s and jogo_bb:
            partes = [c.strip() for c in s.group(1).split(" · ")]
            if len(partes) >= 2:
                out.append(_unid(jogo_bb, partes[0], partes[1]))
    return out


def _unid(jogo, mercado, selecao):
    m = _SEP_JOGO.search(jogo)
    if m:
        a, b = jogo[:m.start()].strip(), jogo[m.end():].strip()
        casa_idx = 1 if m.group(1) == "@" else 0     # "A @ B": B é o mandante
    else:
        a, b, casa_idx = jogo.strip(), "", 0
    return {"jogo": jogo, "times": (a, b), "casa_idx": casa_idx, "mercado": mercado,
            "selecao": trad._PLACAR_AO_VIVO.sub("", selecao).strip()}


def _linha_esperada(sel: str):
    """Número da linha na seleção, como VALOR. Linha partida → o quarto (§10.1.1)."""
    q = trad._quarto_de_linha(sel)
    nums = _NUM.findall(q)
    if not nums:
        return None
    return nums[-1].replace(",", ".")


def julgar_unidade(u: dict, parte: str, esporte: str) -> list:
    """Achados [(classe, motivo)] de UMA seleção contra o trecho da descrição dela."""
    achados = []
    pf = _f(parte)
    # fora do confronto: o `[A v B]` sai ANTES de normalizar (o `_f` apaga os colchetes)
    pf_fora = _f(re.sub(r"\[.*?\]", " ", parte))
    mercado_f = _f(u["mercado"])
    sel = u["selecao"]

    # confronto
    for i, t in enumerate(u["times"]):
        if not t:
            continue
        r = _tem_nome(t, pf)
        if r == "nada":
            achados.append(("erro_real", f"time ausente: {t}"))
        elif r == "parte":
            achados.append(("permitida", f"time abreviado: {t}"))

    # total de TIME: o time certo tem de aparecer fora do confronto
    for qual, idx in (("time da casa", u["casa_idx"]), ("time visitante", 1 - u["casa_idx"])):
        if mercado_f.startswith(qual) and u["times"][idx]:
            if _tem_nome(u["times"][idx], pf_fora) != "nada":
                continue
            outro = u["times"][1 - idx]
            if outro and _tem_nome(outro, pf_fora) != "nada":
                achados.append(("erro_real", f"total de time com o time TROCADO ({outro} no lugar de {u['times'][idx]})"))
            elif qual in pf_fora:
                # o rótulo da casa preservado (§12.5.1 prefere o nome quando o confronto
                # o permite): a aposta está certa, a forma não é a preferida
                achados.append(("forma", f"escopo '{qual}' literal, com o nome disponível ({u['times'][idx]})"))
            else:
                achados.append(("erro_real", f"total de time sem o time ({u['times'][idx]})"))

    # direção
    d = _DIR.search(sel)
    if d:
        quer_over = d.group(1).lower() in ("mais de", "over")
        tem_over, tem_under = " over " in f" {pf} ", " under " in f" {pf} "
        tem_mais, tem_menos = "mais de" in pf, "menos de" in pf
        if (quer_over and (tem_under or tem_menos)) or (not quer_over and (tem_over or tem_mais)):
            achados.append(("erro_real", "direção invertida"))
        elif not (tem_over or tem_under):
            achados.append(("forma" if (tem_mais or tem_menos) else "erro_real",
                            "Over/Under em português" if (tem_mais or tem_menos) else "direção ausente"))

    # linha
    lin = _linha_esperada(sel)
    if lin is not None and (d or re.search(r"[-+]\d", sel)):
        fora = re.sub(r"\[.*?\]", " ", parte)
        nums = [n.replace(",", ".") for n in _NUM.findall(fora)]
        if not any(abs(float(n) - float(lin)) < 1e-9 for n in nums if _num_ok(n)):
            achados.append(("erro_real", f"linha {lin} ausente ou diferente ({nums[:4]})"))
        else:
            exato = any(n == lin for n in nums)
            if not exato:
                achados.append(("permitida", f"linha {lin} escrita de outro jeito"))
            if not d:     # handicap: o SINAL decide o lado
                sinal = "-" if lin.startswith("-") else "+"
                if not any(n.startswith(sinal) or (sinal == "+" and not n.startswith("-"))
                           for n in nums if _num_ok(n) and abs(abs(float(n)) - abs(float(lin))) < 1e-9):
                    achados.append(("erro_real", "sinal do handicap invertido"))
        if re.search(r"\d,\d", fora):
            achados.append(("forma", "vírgula decimal na descrição"))

    # jogador (seleção "Nome - Mais de X" / sub "Nome: 1+ ...")
    mj = re.match(r"^(.+?)\s+-\s+(mais de|menos de)\b", sel, re.I) or re.match(r"^([^:]+):\s*\d", sel)
    if mj and re.search(r"\bqualquer\b|\s-\s", mj.group(1), re.I):
        # "Qualquer um dos Lutadores: 25+…" / "Partida - Intervalo de Gol: 1-5": não é nome
        achados.append(("nao_verificavel", f"sujeito genérico: {mj.group(1)}"))
    elif mj:
        if _tem_nome(mj.group(1), pf) == "nada":
            achados.append(("erro_real", f"jogador ausente: {mj.group(1)}"))
    elif not d and not re.search(r"[-+]\d", sel) and sel.lower() not in ("sim", "não", "nao", "empate"):
        # ML / marcador: a seleção É o nome apostado. Seleção "Para …" é SIM/NÃO descrito
        # pelo próprio mercado (`Para Ambos os Times Marcarem` → `Ambas Marcam`): o juiz
        # não tem template para conferir, e não chuta.
        if re.match(r"^para\b", sel.strip(), re.I):
            achados.append(("nao_verificavel", f"seleção sim/não pelo mercado: {sel}"))
        elif _tem_nome(sel, pf_fora) == "nada":
            achados.append(("erro_real", f"seleção ausente: {sel}"))
        else:
            # PROP DE JOGADOR de sim/não que NÃO é gol a qualquer momento: sem o mercado na
            # descrição, `Fulano [A v B]` lê como Anytime — outra aposta. Achado na revisão de
            # falso negativo do experimento s386 (5 de 30 "limpos" do Sonnet enxuto).
            mk = _f(u["mercado"])
            for chave, exige in _PROP_SIM:
                if chave in mk and not any(e in pf_fora for e in exige):
                    achados.append(("erro_real", f"mercado do jogador ausente: {u['mercado']}"))
                    break

    # QUALIFICADOR que muda a aposta e está no rótulo ou na seleção (revisão de falso
    # negativo da s386): sem ele a descrição vira OUTRA aposta que existe.
    fonte_f = _f(u["mercado"] + " " + sel)
    for chave, exige, nome in _QUALIF_SENTIDO:
        if chave in fonte_f and not any(e in pf for e in exige):
            achados.append(("erro_real", f"qualificador ausente: {nome}"))

    # período
    per = _PERIODO.search(u["mercado"])
    if per and _f(per.group(0)).split()[-1][:4] not in pf:
        achados.append(("erro_real", f"escopo de tempo ausente: {per.group(0)}"))

    # objeto do mercado: pelo mapa curado; senão, pela FORMA do rótulo "X (Mais de/Menos de)",
    # em que o objeto é o próprio X (regra SÓ do juiz — proposta para o mapa do tradutor)
    spec = trad._spec(trad._MAPAS["BET365"], u["mercado"], esporte)
    objeto = spec.get("objeto") if spec else None
    if not objeto and d:
        mo = re.match(r"^(?:.*? - )?(?:Total de )?(.+?)\s*\(Mais de/Menos de\)\s*$", u["mercado"], re.I)
        objeto = mo.group(1) if mo else None
    if objeto:
        desc_tok = set(re.split(r"[\s+]+", pf_fora))
        obj_tok = [t for t in _f(objeto).split() if len(t) >= 3]
        if obj_tok and not any(any(dt.startswith(t[:3]) for dt in desc_tok) for t in obj_tok):
            achados.append(("erro_real", f"objeto ausente: {objeto}"))
    elif d:
        achados.append(("nao_verificavel", f"objeto: rótulo fora do mapa ({u['mercado']})"))
    return achados


def _num_ok(n):
    try:
        float(n)
        return True
    except ValueError:
        return False


_CL = re.compile(r"CL=(\d+)\s*\(([^)]+)\)")
# nomes da casa -> canônico do MASTER_ESPORTES §7 (só os que a casa escreve diferente)
_CANON = {"Beisebol": "Baseball", "Tênis de Mesa": "Tênis de Mesa"}


def _esporte_declarado(cab: dict, us: list) -> str:
    """O esporte que a CASA declara (`Esporte (casa): CL=18 (Basquete)`), e não o que o
    tradutor deduz — o tradutor lê `(F)` de time feminino como apelido de eBasket
    (achado s386). Múltipla: `Tipo: Múltipla` (3+ jogos ou esportes misturados) é
    `Múltiplos` (MASTER_ESPORTES §2); dupla do mesmo esporte fica no esporte."""
    m = _CL.search(cab.get("Esporte (casa)", "") or "")
    jogos = {_f(u["jogo"]) for u in us}
    num = trad._CL_NUM.match(cab.get("Esporte (casa)", "") or "")
    # MASTER_ESPORTES §2: 3+ jogos DIFERENTES, ou esportes misturados. A casa declara um
    # CL só quando o cupom é de um esporte; `Tipo: Múltipla` sem CL = misturado.
    if len(jogos) >= 3 or (trad._TIPO_MULTIPLA.match((cab.get("Tipo") or "").strip()) and not m):
        return "Múltiplos"
    if not m:
        return trad._CL_SEM_NOME.get(num.group(1), "") if num else ""
    nome = _CANON.get(m.group(2).strip(), m.group(2).strip())
    # A Bet365 marca o basquete VIRTUAL com o mesmo CL do real; o que o separa é o
    # apelido do jogador no nome do time (MASTER_ESPORTES, eBasket). Apelido tem 2+
    # letras — "(F)"/"(W)"/"(M)" é gênero e "U21" é categoria, nunca apelido.
    if nome == "Basquete":
        apelidos = [p for u in us for t in u["times"] if t
                    for p in re.findall(r"\(([A-Z0-9][A-Z0-9 _.-]*)\)\s*$", t)
                    if len(p) >= 2 and not re.fullmatch(r"U\d{2}", p)]
        if apelidos:
            return "eBasket"
    return nome


def julgar(bruto: str, esporte: str, aposta: str, descricao: str) -> dict:
    """Julga a linha inteira. Devolve {'achados': [...], 'categoria': ..., 'esporte': ...}."""
    us = unidades(bruto)
    cab = trad._cabecalho(bruto or "")
    partes = [p.strip() for p in (descricao or "").split(" // ")] if descricao else []
    achados = []
    if not us:
        return {"achados": [("nao_verificavel", "bloco sem seleção legível")], "categoria": None,
                "esporte": None}
    combo = any(u.get("combo") for u in us)
    if combo and len(partes) == 1:
        # mercado combinado numa parte só: todas as condições contra a MESMA parte
        partes = partes * len(us)
    # casa cada seleção com a parte que tem mais tokens do jogo e da seleção dela. Uma parte
    # pode cobrir VÁRIAS seleções do MESMO jogo (`Jogador - A / B [Confronto]`, §12.4):
    # reusar só é permitido quando o jogo é o mesmo da seleção que já a usou.
    usadas = {}
    esp_esperado = _esporte_declarado(cab, us)
    esp_obj = esp_esperado if esp_esperado and esp_esperado != "Múltiplos" else (esporte or "")
    for u in us:
        score = lambda i: (sum(t in _f(partes[i]) for t in _tokens(u["jogo"]))
                           + sum(t in _f(partes[i]) for t in _tokens(u["selecao"])))
        cand = [i for i in range(len(partes)) if i not in usadas]
        cand += [i for i, j in usadas.items() if j == _f(u["jogo"]) and " / " in partes[i]]
        if not cand:
            achados.append(("erro_real", f"seleção sem parte na descrição: {u['jogo']}"))
            continue
        melhor = max(cand, key=score)
        usadas.setdefault(melhor, _f(u["jogo"]))
        achados += julgar_unidade(u, partes[melhor], esp_obj)
    sobra = [i for i in range(len(partes)) if i not in usadas]
    if sobra and not combo:
        achados.append(("erro_real", f"{len(sobra)} parte(s) da descrição sem seleção na fonte"))

    # Prop de jogador sem o mercado na descrição: em SIMPLES com a categoria do próprio
    # mercado (`Assistência`, `Cartões`) é o template do §12.2 (a categoria carrega o
    # sentido). Dentro de MÚLTIPLA a categoria vira `Múltipla` e o mercado some — o MASTER
    # não tem template para a perna: é LACUNA DE REGRA, relatada à parte.
    novos = []
    for cls, m in achados:
        if m.startswith("mercado do jogador ausente"):
            mk = _f(m)
            if len(us) == 1 and ((aposta == "Assistência" and "dar assist" in mk)
                                 or (aposta == "Cartões" and "receber cart" in mk)):
                continue
            if len(us) > 1 and ("dar assist" in mk or "receber cart" in mk):
                novos.append(("lacuna", m + " (perna de múltipla: MASTER sem template)"))
                continue
        novos.append((cls, m))
    achados = novos

    # categoria esperada (mercado combinado: o MASTER não decide — não verificável)
    if combo:
        achados.append(("nao_verificavel", "categoria de mercado combinado"))
        return {"achados": achados, "categoria": None, "esporte": esp_esperado or None}
    if len(us) > 1:
        cat = "Múltipla"
    else:
        spec = trad._spec(trad._MAPAS["BET365"], us[0]["mercado"], esp_obj)
        cat = spec.get("cat") if spec else None
    if cat is None:
        achados.append(("nao_verificavel", f"categoria: rótulo fora do mapa ({us[0]['mercado']})"))
    elif aposta != cat:
        if cat == "Player Props" and re.match(r"^\s*jogador\b", us[0]["mercado"], re.I):
            # MASTER_APOSTAS §3 tem categoria PRÓPRIA (Chutes no Gol, Desarmes, Faltas…) e
            # o CASA_BET365 §9 manda "props de jogador" para Player Props: regra em conflito
            achados.append(("permitida", f"categoria {aposta!r} x {cat!r}: MASTER e CASA em conflito"))
        else:
            achados.append(("categoria", f"categoria {aposta!r}, o mapa curado diz {cat!r}"))
    if esp_esperado:
        if esporte != esp_esperado:
            achados.append(("erro_real", f"esporte {esporte!r}, a casa diz {esp_esperado!r}"))
    else:
        achados.append(("nao_verificavel", "esporte: a casa não declarou"))
    return {"achados": achados, "categoria": cat, "esporte": esp_esperado or None}
