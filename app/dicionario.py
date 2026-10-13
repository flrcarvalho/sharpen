"""Dicionário de termos da casa (`04_DICIONARIO.md`; s411, 12/10/2026).

A Ficha traz esporte e mercado como a CASA escreve (`esporte_casa`, `mercado_casa`). A planilha
precisa do esporte e da categoria do Sharpen. Este módulo traduz um pelo outro, sem IA, pela
tabela `dicionario_termos`, que nasce dos PARES que já existem: para o mesmo código, o termo do
cru contra o esporte e a categoria que a IA gravou em `bilhetes` (`04 §3`, semente automática;
quem semeia é `scripts/semear_dicionario.py`).

Regra do Feca (12/10): **termo sem par conhecido vai para a IA, como hoje.** `traduzir` devolve
o que faltou, e a virada (`app/virada.py`) não grava aquela aposta: o texto dela segue para a
IA. Nada aqui inventa categoria.

Como a linha da planilha sai da Ficha (as regras são as que a IA segue hoje, medidas contra o
banco pela régua antes de cada virada):
  • esporte: cada perna traduzida; esportes diferentes, ou 3+ jogos diferentes, = `Múltiplos`
    (`MASTER_ESPORTES §2`);
  • categoria: múltipla e sistema = `Múltipla`; simples = o mercado traduzido. Mercado com
    duas decisões da IA no banco não entra pelo mercado sozinho: entra pelo par mercado +
    seleção, quando ESSE par é unânime.

D24 (s412): **o termo entra com 1 voto e o erro se conserta depois** (`corrigir_termo`, origem
`feca`, que regrava as apostas da Ficha do mês corrente; o passado não, D10/D23). Por isso a
semente tem proteções (R27, pesquisa 001): só aprende valor que está no Master
(`app/taxonomia.py`), ignora aposta editada à mão (`correcoes` com campo `esporte`, `aposta` ou
`descricao`) e nunca aprende termo VAGO (`VAGOS`). E `Total` sem qualificador não é termo, é regra
(`categoria_do_total`): a categoria principal do esporte.

s413 (Feca, 12/10): **chamada extra à IA só para a descrição, nunca.** O dicionário tem um terceiro
tipo, `descricao`: o mercado da casa (sem lado, sem linha) → o nome do mercado no padrão do
Sharpen, aprendido da descrição que a IA escreveu, perna a perna (`app/descricao_ficha.py`).
E a semente decide pela MAIORIA quando ela tem 90% ou mais dos votos (P7 do parecer 013): o voto
isolado vai para a lista de revisão (`semente_log.revisao`), não derruba o termo.
"""
from __future__ import annotations

import re

_NUM = re.compile(r"\d+(?:[.,]\d+)*")
MULTIPLOS = "Múltiplos"
MULTIPLA = "Múltipla"
SEP = " | "                      # chave mercado + seleção

# Termos VAGOS (s412): nunca entram no dicionário e sempre vão para a IA. `especiais` virou
# `Futebol` para todas as casas com 1 voto (7Games, bet de Futebol e Tênis juntos).
VAGOS = frozenset({"especiais"})

# `Total` SEM qualificador (s412, Feca): a categoria principal do esporte. Esporte fora daqui:
# a IA decide. Tênis e Vôlei dependem da linha: até 4,5 é Sets.
TOTAL = "total"
_TOTAL_POR_ESPORTE = {"Futebol": "Gols", "Hóquei": "Gols", "Handebol": "Gols",
                      "Basquete": "Pontos", "Futebol Americano": "Pontos"}
_TOTAL_POR_LINHA = {"Tênis": ("Sets", "Games"), "Vôlei": ("Sets", "Pontos")}
_OVER_UNDER = re.compile(r"^(over|under|acima|abaixo|mais|menos)(?:\s+de)?\s*([\d.,]+)?$", re.I)
_LADO = {"over": "Over", "acima": "Over", "mais": "Over",
         "under": "Under", "abaixo": "Under", "menos": "Under"}


def _linha_num(p: dict) -> float | None:
    for v in (p.get("linha"), p.get("selecao_casa")):
        m = _NUM.search(str(v or ""))
        if m:
            try:
                return float(m.group(0).replace(",", "."))
            except ValueError:
                return None
    return None


def categoria_do_total(esporte: str | None, p: dict) -> str | None:
    """A categoria do `Total` sem qualificador. None = a IA decide."""
    if esporte in _TOTAL_POR_ESPORTE:
        return _TOTAL_POR_ESPORTE[esporte]
    if esporte in _TOTAL_POR_LINHA:
        linha = _linha_num(p)
        if linha is None:
            return None
        ate, acima = _TOTAL_POR_LINHA[esporte]
        return ate if linha <= 4.5 else acima
    return None


def _jogo_v(ev: str) -> str:
    """`A vs B` / `A vs. B` → `A v B` (o separador do `MASTER_OUTPUT`)."""
    return re.sub(r"\s+vs\.?\s+", " v ", ev or "")


def descricao_perna(p: dict) -> str | None:
    """Descrição de perna com forma própria (s412, Feca). None = a forma geral da virada.
      • `Total` sem qualificador: `Over X.X [A v B]`;
      • `Winner. Quarter N` (DEX): `Time X - NQ [A v B]` (é ML);
      • volta mais rápida (`fastest lap`): `<piloto> volta mais rápida [<prova>]`."""
    merc = normalizar(p.get("mercado_casa"))
    sel, ev = _limpo(p.get("selecao_casa")), _limpo(p.get("evento"))
    fim = f" [{_jogo_v(ev)}]" if ev else ""
    if merc == TOTAL:
        m = _OVER_UNDER.match(sel)
        if m:
            linha = m.group(2) or _limpo(p.get("linha"))
            if linha:
                return f"{_LADO[m.group(1).lower()]} {linha}{fim}"
        return None
    if merc == "winner. quarter {n}":
        n = re.search(r"(\d+)", str(p.get("mercado_casa") or ""))
        return f"{sel} - {n.group(1)}Q{fim}" if sel and n else None
    if merc in ("fastest lap", "volta mais rápida"):
        return f"{sel} volta mais rápida [{ev}]" if sel and ev else None
    return None


def normalizar(termo, numeros: bool = True) -> str:
    """Minúsculo, sem espaço sobrando, número trocado por `{n}` (`04 §2`). No ESPORTE o número
    fica (`numeros=False`): a Altenar escreve `sportTypeId 4`, e o número É o esporte."""
    s = " ".join(str(termo or "").lower().split())
    return _NUM.sub("{n}", s) if numeros else s


def _esp(p: dict) -> str:
    return normalizar(p.get("esporte_casa"), numeros=False)


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


# Seleção que é CÓDIGO: `1` e `2` são seleções diferentes, o número não é linha.
_SEL_CODIGO = frozenset({"1", "2", "x", "1x", "x2", "12"})


def sel_chave(sel, evento=None) -> str:
    """A seleção na chave do par mercado + seleção (s413, P6 do parecer 013): número vira `{n}`
    também nela (`total pontos | menos de 71.5` até `80.5` eram 10 termos), menos na seleção
    que é código (`1`, `2`, `X`, `1X`...). s415 (T1): o time ou jogador do jogo (`evento`) vira
    `{ent}`: `resultado da partida | ng ka long angus` era um termo por jogador."""
    import descricao_ficha
    s = normalizar(sel, numeros=False)
    if s in _SEL_CODIGO:
        return s
    s = _limpo(sel)
    t1, t2, _, _ = descricao_ficha._times(evento)
    for t in sorted((t1, t2), key=len, reverse=True):
        i, n = descricao_ficha._achar(s, t) if t else (-1, 0)
        if i >= 0:
            s = s[:i] + "{ent}" + s[i + n:]
    return normalizar(s)


def _par(p: dict) -> str:
    return normalizar(p.get("mercado_casa")) + SEP + sel_chave(p.get("selecao_casa"),
                                                               p.get("evento"))


def _merc_jogador(p: dict) -> str | None:
    """A chave de categoria com o jogador trocado por `{jogador}` (s415), ou None."""
    import descricao_ficha
    m = descricao_ficha.mercado_com_jogador(p)
    return normalizar(m) if m else None


def chaves(f: dict) -> list[tuple[str, str]]:
    """As chaves (tipo, termo normalizado) que a tradução desta Ficha consulta, na ordem."""
    out = []
    pernas = f.get("pernas") or []
    for p in pernas:
        out.append(("esporte", _esp(p)))
    if f.get("tipo") == "simples" and len(pernas) == 1:
        p = pernas[0]
        out.append(("categoria", normalizar(p.get("mercado_casa"))))
        out.append(("categoria", _par(p)))
        if (mj := _merc_jogador(p)):
            out.append(("categoria", mj))
    return out


def traduzir(f: dict, termos: dict) -> tuple[str | None, str | None, list[tuple[str, str]]]:
    """(esporte, categoria, faltam). `termos` = {(tipo, termo normalizado): termo Sharpen}.
    Se `faltam` não está vazio, esporte ou categoria é None e a aposta vai para a IA."""
    pernas = f.get("pernas") or []
    faltam: list[tuple[str, str]] = []
    esportes = set()
    for p in pernas:
        k = ("esporte", _esp(p))
        if k[1] and k[1] not in VAGOS and k in termos:
            esportes.add(termos[k])
        else:
            faltam.append(k)
    jogos = {_limpo(p.get("evento")) for p in pernas} - {""}
    esporte = None
    if not faltam and esportes:
        esporte = MULTIPLOS if len(esportes) > 1 or len(jogos) >= 3 else next(iter(esportes))
    if f.get("tipo") != "simples" or len(pernas) != 1:
        categoria = MULTIPLA if pernas else None
    else:
        merc = normalizar(pernas[0].get("mercado_casa"))
        par = _par(pernas[0])
        mj = _merc_jogador(pernas[0])
        if merc in VAGOS:
            categoria = None
        elif merc == TOTAL:
            categoria = categoria_do_total(esporte, pernas[0])
        else:
            categoria = termos.get(("categoria", merc)) or termos.get(("categoria", par)) \
                or (termos.get(("categoria", mj)) if mj else None)
        if categoria is None:
            faltam.append(("categoria", merc))
    return esporte, categoria, faltam


async def carregar(conn, casa_key: str) -> dict:
    """Os termos da casa e os que valem para todas (`*`). A correção do Feca vence a semente
    (inclusive a semente da casa contra a correção geral); dentro de cada origem, a casa
    vence o geral. Termo VAGO nunca sai daqui."""
    termos: dict = {}
    for r in await conn.fetch(
            "SELECT casa, tipo, termo_casa, termo_sharpen FROM dicionario_termos "
            "WHERE casa = ANY($1::text[]) ORDER BY (origem = 'feca'), (casa <> '*')",
            ["*", (casa_key or "").upper()]):
        if r["termo_casa"] not in VAGOS:
            termos[(r["tipo"], r["termo_casa"])] = r["termo_sharpen"]
    return termos


_ESPORTE_TXT = re.compile(r"Esporte:\s*([^·\r\n(]+)")
_TIPO_SIMPLES = re.compile(r"^Tipo:\s*Simples\b", re.MULTILINE)
_PERNA_TXT = re.compile(r"^\s*Jogo:", re.MULTILINE)


def esportes_do_texto(bruto: str) -> list[str] | None:
    """Os termos de esporte que o texto do SharpenUp escreveu num bloco (`sombra_rotulos`),
    no MESMO vocabulário do cru (o texto é montado da mesma API). Só quando dá para dizer de
    qual perna é cada um: bilhete simples, ou um `Esporte:` por perna. Senão, None."""
    termos = [t.strip() for t in _ESPORTE_TXT.findall(bruto or "")]
    if not termos:
        return None
    if _TIPO_SIMPLES.search(bruto) and len(termos) == 1:
        return termos
    if len(termos) == len(_PERNA_TXT.findall(bruto)) >= 2:
        return termos
    return None


def _master() -> tuple[frozenset, frozenset]:
    import taxonomia
    return frozenset(taxonomia.esportes_canonicos()), frozenset(taxonomia.categorias_canonicas())


MAIORIA = 0.9                    # P7: com 90% ou mais dos votos, fica a maioria


def votar(pares, votos_texto=()) -> tuple[dict, dict, list]:
    """Semente (`04 §3`). `pares` = [(casa, Ficha, esporte da IA, categoria da IA[, descrição
    da IA])];
    `votos_texto` = [(casa, termos de esporte do texto, esporte da IA)], o complemento do
    `sombra_rotulos` (só esporte: no texto o mercado vem colado à seleção).
    Devolve ({(casa, tipo, termo): (termo Sharpen, ocorrências)} com os decididos,
    {(casa, tipo, termo): Counter} com os que a IA decidiu de mais de um jeito sem maioria,
    [revisão]: os votos isolados que a maioria de 90% venceu, para o Feca olhar).

    Só vota o que a Ficha isola sem ambiguidade: esporte de bilhete de UM esporte (a IA
    escreve `Múltiplos` também para 3 jogos do mesmo esporte, e aí o voto não diz nada do
    termo) e categoria de SIMPLES de uma perna.

    Proteções (s412, R27): voto com valor FORA do Master não conta (a IA às vezes escreve
    categoria que não existe); termo VAGO não vota; `Total` sem qualificador não vota (é regra,
    `categoria_do_total`).

    DESCRIÇÃO (s413): cada perna vota `chave do mercado → valor` (`descricao_ficha.votos`), e as
    variantes de escrita da IA para o mesmo mercado contam como um voto só (`canonico`); o valor
    guardado é a variante mais votada."""
    from collections import Counter, defaultdict

    import descricao_ficha
    esportes_m, categorias_m = _master()
    votos: dict = defaultdict(Counter)
    for casa, f, esp_ia, cat_ia, *resto in pares:
        casa = (casa or "").upper()
        if resto and resto[0]:
            for k, v in descricao_ficha.votos(f, resto[0]):
                votos[(casa, "descricao", k)][v] += 1
        pernas = f.get("pernas") or []
        termos_esp = {_esp(p) for p in pernas} - {""}
        esp_ia, cat_ia = _limpo(esp_ia), _limpo(cat_ia)
        if len(termos_esp) == 1 and esp_ia and esp_ia != MULTIPLOS and esp_ia in esportes_m \
                and not termos_esp & VAGOS:
            votos[(casa, "esporte", next(iter(termos_esp)))][esp_ia] += 1
        if f.get("tipo") == "simples" and len(pernas) == 1 and cat_ia and cat_ia != MULTIPLA \
                and cat_ia in categorias_m:
            p = pernas[0]
            merc = normalizar(p.get("mercado_casa"))
            if merc and merc not in VAGOS and merc != TOTAL:
                votos[(casa, "categoria", merc)][cat_ia] += 1
                votos[(casa, "categoria", _par(p))][cat_ia] += 1
                if (mj := _merc_jogador(p)):          # s415: o mercado de qualquer jogador
                    votos[(casa, "categoria", mj)][cat_ia] += 1
    for casa, termos_txt, esp_ia in votos_texto:
        termos_esp = {normalizar(t, numeros=False) for t in termos_txt} - {""}
        esp_ia = _limpo(esp_ia)
        if len(termos_esp) == 1 and esp_ia and esp_ia != MULTIPLOS and esp_ia in esportes_m \
                and not termos_esp & VAGOS:
            votos[((casa or "").upper(), "esporte", next(iter(termos_esp)))][esp_ia] += 1
    unanimes, contraditos, revisao = {}, {}, []
    for k, c in votos.items():
        grupo = Counter()
        for v, n in c.items():
            grupo[descricao_ficha.canonico(v) if k[1] == "descricao" else v] += n
        topo, n_topo = grupo.most_common(1)[0]
        total = sum(c.values())
        if len(grupo) > 1 and n_topo / total < MAIORIA:
            contraditos[k] = c
            continue
        dentro = [v for v in c if (descricao_ficha.canonico(v) if k[1] == "descricao" else v)
                  == topo]
        termo = max(dentro, key=lambda v: (c[v], v))
        unanimes[k] = (termo, n_topo)
        if len(grupo) > 1:
            revisao.append({"casa": k[0], "tipo": k[1], "termo": k[2], "fica": termo,
                            "votos": dict(c)})
    # ESPORTE vale para todas as casas (`*`): o nome de um esporte não muda de casa para casa,
    # e a Altenar numera os esportes na plataforma (`sportTypeId 4` é o mesmo em toda casa
    # dela). É o que traduz o esporte que numa casa só apareceu em múltipla mista (`basquete`
    # na MyStake). Entra quando a decisão MAIS VOTADA é a mesma em todas as casas que viram o
    # termo; categoria não, porque o mercado é vocabulário de cada casa.
    por_termo: dict = defaultdict(dict)
    for (casa, tipo, termo), c in votos.items():
        if tipo == "esporte" and casa != "*":
            por_termo[termo][casa] = c
    for termo, casas in por_termo.items():
        topo = {c.most_common(1)[0][0] for c in casas.values()}
        if len(topo) == 1:
            unanimes[("*", "esporte", termo)] = (next(iter(topo)),
                                                 sum(sum(c.values()) for c in casas.values()))
    return unanimes, contraditos, revisao


# ── semente (`04 §3`): os pares que já existem ─────────────────────────────────────────

async def pares(conn) -> tuple[list, list, dict]:
    """([(casa_key, Ficha, esporte da IA, categoria da IA, descrição da IA)], um por aposta com cru;
    [(casa_key, termos de esporte do texto, esporte da IA)], um por bilhete da sombra;
    contagem por fonte). Linha gravada pela própria Ficha (`origem = 'ficha'`) NÃO vota: o
    esporte dela saiu deste dicionário, e votar nela seria o dicionário votando em si mesmo."""
    import json
    from collections import Counter

    import ficha
    ultimo = {}
    for r in await conn.fetch("SELECT dono, casa, parceiro, familia, codigo, cru::text AS cru "
                              "FROM captura_crua ORDER BY id"):
        ultimo[(r["dono"], r["casa"], r["parceiro"], r["codigo"])] = r
    codigos = [k[3] for k in ultimo]
    nomes = {r["k"]: r["casa"] for r in await conn.fetch(
        "SELECT DISTINCT upper(replace(casa, ' ', '')) AS k, casa FROM bilhetes")}
    # Aposta editada à mão (`correcoes` com `esporte`, `aposta` ou `descricao`) não vota (R27): o dicionário
    # vale para todos os usuários da casa, e com 1 voto uma edição viraria regra para todos.
    # Também não cai para a `sombra_rotulos`: a decisão da IA ali é a que alguém corrigiu.
    bil = {(b["dono"], b["casa"], b["parceiro"], b["codigo_bilhete"]): b for b in await conn.fetch(
        "SELECT b.dono, b.casa, b.parceiro, b.codigo_bilhete, b.esporte, b.aposta, b.descricao, "
        "EXISTS (SELECT 1 FROM correcoes c WHERE c.bilhete_id = b.id "
        "        AND c.campo IN ('esporte', 'aposta', 'descricao') "
        "        AND c.origem IS DISTINCT FROM 'ficha') AS editada FROM bilhetes b "
        "WHERE b.codigo_bilhete = ANY($1::text[]) AND b.origem IS DISTINCT FROM 'ficha'", codigos)}
    sombra = {(s["dono"], s["codigo"]): s for s in await conn.fetch(
        "SELECT DISTINCT ON (dono, codigo) dono, codigo, ia_esporte, ia_aposta, ia_descricao "
        "FROM sombra_rotulos WHERE codigo = ANY($1::text[]) ORDER BY dono, codigo, criado_em DESC",
        codigos)}
    out, fontes = [], Counter()
    for (dono, casa, parceiro, codigo), r in ultimo.items():
        f, motivos = ficha.montar_ficha(r["familia"], json.loads(r["cru"]), casa)
        if f is None or motivos:
            continue
        b = bil.get((dono, nomes.get(casa, casa), parceiro, codigo))
        if b and b["editada"]:
            fontes["editada à mão"] += 1
        elif b:
            out.append((casa, f, b["esporte"], b["aposta"], b["descricao"]))
            fontes["bilhetes"] += 1
        elif (s := sombra.get((dono, codigo))):
            out.append((casa, f, s["ia_esporte"], s["ia_aposta"], s["ia_descricao"]))
            fontes["sombra_rotulos"] += 1
        else:
            fontes["sem par"] += 1
    # Complemento de ESPORTE: o texto do SharpenUp em `sombra_rotulos` escreve o termo da casa
    # por perna (`Esporte: tennis`), desde antes do cru existir. Só onde dá para dizer de qual
    # perna é o termo (`esportes_do_texto`).
    editadas = {(r["dono"], r["codigo_bilhete"]) for r in await conn.fetch(
        "SELECT DISTINCT b.dono, b.codigo_bilhete FROM bilhetes b JOIN correcoes c "
        "ON c.bilhete_id = b.id WHERE c.campo IN ('esporte', 'aposta', 'descricao') "
        "AND c.origem IS DISTINCT FROM 'ficha' "
        "AND b.codigo_bilhete IS NOT NULL")}
    texto = []
    for s in await conn.fetch(
            "SELECT DISTINCT ON (dono, casa, codigo) dono, casa, codigo, bruto, ia_esporte "
            "FROM sombra_rotulos WHERE codigo IS NOT NULL ORDER BY dono, casa, codigo, "
            "criado_em DESC"):
        if (s["dono"], s["codigo"]) in editadas:
            continue
        termos = esportes_do_texto(s["bruto"])
        if termos:
            texto.append(((s["casa"] or "").replace(" ", "").upper(), termos, s["ia_esporte"]))
    fontes["texto (esporte)"] = len(texto)
    return out, texto, dict(fontes)


async def gravar_semente(conn, unanimes: dict) -> int:
    """Refaz a semente inteira numa transação. Linha `origem = 'feca'` nunca é tocada; semente
    que deixou de ser unânime some (a aposta volta para a IA)."""
    async with conn.transaction():
        await conn.execute("DELETE FROM dicionario_termos WHERE origem = 'semente'")
        for (c, t, termo), (sharpen, n) in unanimes.items():
            await conn.execute(
                """INSERT INTO dicionario_termos (casa, tipo, termo_casa, termo_sharpen,
                                                  origem, ocorrencias)
                   VALUES ($1, $2, $3, $4, 'semente', $5)
                   ON CONFLICT (casa, tipo, termo_casa) DO NOTHING""", c, t, termo, sharpen, n)
    return len(unanimes)


def coberto_pelo_feca(feca, casa: str, tipo: str, termo: str) -> bool:
    """A correção do Feca vence a semente no termo E nas chaves mais específicas do mesmo
    mercado (`mercado | seleção`), na casa dela ou em todas (`*`). P5 do parecer 013: sem isso
    `winner. quarter {n} | <time>` voltava como "novo → Player Props" a cada rodada."""
    for c, t, ft in feca:
        if t == tipo and c in (casa, "*") and (termo == ft or termo.startswith(ft + SEP)):
            return True
    return False


async def semear(conn, gatilho: str = "manual", hoje=None) -> dict:
    """Refaz a semente e grava o resultado em `semente_log` (s412): termos por casa, termos
    contraditos e termos NOVOS desta rodada (que não estavam na semente anterior). Desde a
    s413 também a lista de revisão (o voto isolado que a maioria de 90% venceu) e, depois de
    gravar, regrava a DESCRIÇÃO das apostas da Ficha do mês corrente (`regravar_mes`)."""
    import json
    from collections import Counter
    p, texto, fontes = await pares(conn)
    unanimes, contraditos, revisao = votar(p, texto)
    feca = [(r["casa"], r["tipo"], r["termo_casa"]) for r in await conn.fetch(
        "SELECT casa, tipo, termo_casa FROM dicionario_termos WHERE origem = 'feca'")]
    unanimes = {k: v for k, v in unanimes.items() if not coberto_pelo_feca(feca, *k)}
    revisao = [r for r in revisao if not coberto_pelo_feca(feca, r["casa"], r["tipo"], r["termo"])]
    antes = {(r["casa"], r["tipo"], r["termo_casa"]): r["termo_sharpen"] for r in await conn.fetch(
        "SELECT casa, tipo, termo_casa, termo_sharpen FROM dicionario_termos "
        "WHERE origem = 'semente'")}
    n = await gravar_semente(conn, unanimes)
    por_casa = Counter(c for c, _, _ in unanimes)
    novos = [{"casa": c, "tipo": t, "termo": k, "para": v}
             for (c, t, k), (v, _) in sorted(unanimes.items()) if antes.get((c, t, k)) != v]
    contra = [{"casa": c, "tipo": t, "termo": k, "votos": dict(cnt)}
              for (c, t, k), cnt in sorted(contraditos.items())
              if t == "descricao" or SEP not in k]          # a chave de descrição tem ` | `
    regravadas = await regravar_mes(conn, aplicar=True, hoje=hoje, campos=("descricao",))
    await conn.execute(
        """INSERT INTO semente_log (gatilho, termos, termos_por_casa, contraditos, novos, fontes,
                                    revisao, regravadas)
           VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb, $8)""",
        gatilho, n, json.dumps(por_casa, ensure_ascii=False),
        json.dumps(contra, ensure_ascii=False), json.dumps(novos, ensure_ascii=False),
        json.dumps(fontes, ensure_ascii=False), json.dumps(revisao, ensure_ascii=False),
        len(regravadas))
    return {"termos": n, "contraditos": len(contraditos), "novos": len(novos),
            "revisao": len(revisao), "regravadas": len(regravadas), "fontes": fontes}


# ── logo depois de um `/extrair` de casa virada que mandou termo novo à IA (s412) ─────────
_semeando = None
_de_novo = False


async def semear_agora(gatilho: str = "extrair") -> None:
    """Roda a semente já (fire-and-forget). Se uma estiver rodando, roda mais UMA depois dela:
    o termo que chegou durante a rodada não espera até as 04h."""
    import asyncio
    import logging

    from database import get_pool
    global _semeando, _de_novo
    if _semeando is not None:
        _de_novo = True
        return
    _semeando = asyncio.current_task()
    try:
        while True:
            _de_novo = False
            try:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    r = await semear(conn, gatilho)
                logging.getLogger("scanner").info("dicionário: semente (%s), %s", gatilho, r)
            except Exception:  # noqa: BLE001
                logging.getLogger("scanner").exception("dicionário: a semente (%s) falhou", gatilho)
            if not _de_novo:
                break
    finally:
        _semeando = None


# ── conserto de um termo (D24): a correção do Feca regrava o mês corrente ───────────────

def _mes(data: str) -> tuple[int, int] | None:
    """`bilhetes.data` guarda DD/MM/YYYY e ISO na mesma coluna."""
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})", data or "") or None
    if m:
        return int(m.group(3)), int(m.group(2))
    m = re.match(r"^(\d{4})-(\d{2})-\d{2}", data or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


async def corrigir_termo(conn, casa: str, tipo: str, termo: str, para: str,
                         aplicar: bool = False, hoje=None) -> list[dict]:
    """Grava a correção do Feca (`origem = 'feca'`, a semente nunca a sobrescreve) e regrava as
    apostas DA FICHA (`origem = 'ficha'`) do MÊS CORRENTE que usaram o termo: esporte,
    categoria e descrição. Mês passado não é tocado (D10, D23), nem campo que alguém editou à
    mão (`correcoes`). Devolve as mudanças; `aplicar=False` só mostra.

    `descricao` (s413): TERMO = a chave (`<esporte da casa> | <mercado>`, como o `semente_log`
    mostra) e PARA = o valor com as marcas (`{ou} Escanteios {n1}º Tempo`)."""
    import descricao_ficha
    casa, tipo = (casa or "").upper(), tipo
    if tipo not in ("esporte", "categoria", "descricao"):
        raise ValueError(f"tipo {tipo!r}: esporte, categoria ou descricao")
    if tipo == "descricao":
        termo = " ".join(str(termo or "").casefold().split())
        estranhas = set(re.findall(r"\{[a-z0-9]+\}", para)) - set(descricao_ficha.MARCAS) \
            - {"{n%d}" % i for i in range(1, 10)}
        if not para.strip() or estranhas or descricao_ficha.SEP not in termo:
            raise ValueError(f"{termo!r} → {para!r}: chave `esporte | mercado` e valor com as "
                             f"marcas {descricao_ficha.MARCAS} e {{n1}}…")
    else:
        termo = normalizar(termo, numeros=(tipo == "categoria"))
        esportes_m, categorias_m = _master()
        if para not in (esportes_m if tipo == "esporte" else categorias_m):
            raise ValueError(f"{para!r} não está no Master")
        if termo in VAGOS:
            raise ValueError(f"{termo!r} é vago: vai sempre para a IA")
    if aplicar:
        await conn.execute(
            """INSERT INTO dicionario_termos (casa, tipo, termo_casa, termo_sharpen, origem,
                                              confirmado)
               VALUES ($1, $2, $3, $4, 'feca', TRUE)
               ON CONFLICT (casa, tipo, termo_casa) DO UPDATE SET termo_sharpen = $4,
                 origem = 'feca', confirmado = TRUE, atualizado_em = NOW()""",
            casa, tipo, termo, para)

    def usa(f):
        if tipo == "descricao":
            return any(termo in descricao_ficha.chaves_da_perna(p) for p in f.get("pernas") or [])
        return termo in {k[1] if SEP not in k[1] else k[1].split(SEP)[0] for k in chaves(f)
                         if k[0] == tipo}
    return await regravar_mes(conn, casa, aplicar, hoje, usa, {(tipo, termo): para})


async def regravar_mes(conn, casa: str = "*", aplicar: bool = False, hoje=None, usa=None,
                       por_cima: dict | None = None,
                       campos=("esporte", "aposta", "descricao")) -> list[dict]:
    """Regrava as apostas DA FICHA do MÊS CORRENTE pelo dicionário de hoje (D24): `campos` de
    cada linha, quando o dicionário sabe o valor e ele mudou. Mês passado não é tocado (D10,
    D23), nem campo editado à mão. `usa(Ficha)` filtra; `por_cima` = termos que valem também no
    ensaio (a correção ainda não gravada). Devolve as mudanças.

    A semente chama com `campos=("descricao",)` depois de cada rodada (s413, item 5): o mercado
    aprendido conserta a descrição das linhas deste mês, e só ela."""
    import json
    from datetime import datetime, timedelta, timezone

    import ficha
    import virada
    hoje = hoje or datetime.now(timezone.utc) - timedelta(hours=3)
    mes = (hoje.year, hoje.month)
    casa = (casa or "*").upper()
    feitas = await conn.fetch(
        "SELECT dono, casa, codigo FROM ficha_virada WHERE estado = 'ficha' "
        "AND ($1 = '*' OR casa = $1)", casa)
    mudancas, cache = [], {}
    for fv in feitas:
        cru = await conn.fetchrow(
            "SELECT familia, cru::text AS cru FROM captura_crua WHERE dono = $1 AND casa = $2 "
            "AND codigo = $3 ORDER BY id DESC LIMIT 1", fv["dono"], fv["casa"], fv["codigo"])
        if not cru:
            continue
        f, motivos = ficha.montar_ficha(cru["familia"], json.loads(cru["cru"]), fv["casa"])
        if f is None or motivos or (usa and not usa(f)):
            continue
        if fv["casa"] not in cache:
            cache[fv["casa"]] = await carregar(conn, fv["casa"])
        termos = {**cache[fv["casa"]], **(por_cima or {})}
        novo = {}
        if "esporte" in campos or "aposta" in campos:
            esporte, categoria, faltam = traduzir(f, termos)
            if not faltam and esporte and categoria:
                novo.update({k: v for k, v in (("esporte", esporte), ("aposta", categoria))
                             if k in campos})
        if "descricao" in campos and (d := virada.descricao(f, termos)):
            novo["descricao"] = d
        if not novo:
            continue
        for b in await conn.fetch(
                "SELECT b.id, b.casa, b.data, b.esporte, b.aposta, b.descricao, "
                "ARRAY(SELECT DISTINCT c.campo FROM correcoes c WHERE c.bilhete_id = b.id "
                "      AND c.origem IS DISTINCT FROM 'ficha') AS ed "
                "FROM bilhetes b WHERE b.dono = $1 AND b.codigo_bilhete = $2 "
                "AND upper(replace(b.casa, ' ', '')) = $3 AND b.origem = 'ficha'",
                fv["dono"], fv["codigo"], fv["casa"]):
            if _mes(b["data"]) != mes:
                continue
            muda = {k: v for k, v in novo.items() if v != b[k] and k not in (b["ed"] or [])}
            if not muda:
                continue
            mudancas.append({"id": b["id"], "dono": fv["dono"], "codigo": fv["codigo"],
                             "antes": {k: b[k] for k in muda}, "depois": muda})
            if aplicar:
                # s415 (RC34, R29): o antes e o depois ficam em `correcoes` (`origem = 'ficha'`,
                # que NÃO conta como edição à mão) e a linha renova o `atualizado_em`
                sets = ", ".join(f"{k} = ${i}" for i, k in enumerate(muda, 2))
                async with conn.transaction():
                    await conn.execute(f"UPDATE bilhetes SET {sets}, atualizado_em = NOW() "
                                       "WHERE id = $1", b["id"], *muda.values())
                    for k, v in muda.items():
                        await conn.execute(
                            "INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, "
                            "valor_novo, descricao, origem) VALUES ($1, $2, $3, $4, $5, $6, $7, "
                            "'ficha')", b["id"], fv["dono"], b["casa"], k, b[k], v,
                            b["descricao"])
    return mudancas


# ── uma vez por dia (Feca, 12/10: "o dicionário aprende sozinho uma vez por dia") ─────────

HORA_UTC = 7                     # 04h de Brasília, fora do horário de captura


def segundos_ate(hora_utc: int, agora=None) -> float:
    from datetime import datetime, timedelta, timezone
    agora = agora or datetime.now(timezone.utc)
    alvo = agora.replace(hour=hora_utc, minute=0, second=0, microsecond=0)
    if alvo <= agora:
        alvo += timedelta(days=1)
    return (alvo - agora).total_seconds()


async def diario() -> None:
    """Tarefa do `lifespan`: refaz a semente todo dia às `HORA_UTC`. Falha numa rodada só
    registra no log; o dicionário de ontem continua valendo."""
    import asyncio
    import logging

    from database import get_pool
    log = logging.getLogger("scanner")
    while True:
        await asyncio.sleep(segundos_ate(HORA_UTC))
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                r = await semear(conn, "diaria")
            log.info("dicionário: semente diária, %s", r)
        except Exception:  # noqa: BLE001
            log.exception("dicionário: a semente diária falhou; vale a de ontem")
