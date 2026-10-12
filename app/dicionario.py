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
"""
from __future__ import annotations

import re

_NUM = re.compile(r"\d+(?:[.,]\d+)*")
MULTIPLOS = "Múltiplos"
MULTIPLA = "Múltipla"
SEP = " | "                      # chave mercado + seleção


def normalizar(termo, numeros: bool = True) -> str:
    """Minúsculo, sem espaço sobrando, número trocado por `{n}` (`04 §2`). No ESPORTE o número
    fica (`numeros=False`): a Altenar escreve `sportTypeId 4`, e o número É o esporte."""
    s = " ".join(str(termo or "").lower().split())
    return _NUM.sub("{n}", s) if numeros else s


def _esp(p: dict) -> str:
    return normalizar(p.get("esporte_casa"), numeros=False)


def _limpo(v) -> str:
    return " ".join(str(v or "").split())


def chaves(f: dict) -> list[tuple[str, str]]:
    """As chaves (tipo, termo normalizado) que a tradução desta Ficha consulta, na ordem."""
    out = []
    pernas = f.get("pernas") or []
    for p in pernas:
        out.append(("esporte", _esp(p)))
    if f.get("tipo") == "simples" and len(pernas) == 1:
        p = pernas[0]
        out.append(("categoria", normalizar(p.get("mercado_casa"))))
        out.append(("categoria", normalizar(p.get("mercado_casa")) + SEP
                    + normalizar(p.get("selecao_casa"), numeros=False)))
    return out


def traduzir(f: dict, termos: dict) -> tuple[str | None, str | None, list[tuple[str, str]]]:
    """(esporte, categoria, faltam). `termos` = {(tipo, termo normalizado): termo Sharpen}.
    Se `faltam` não está vazio, esporte ou categoria é None e a aposta vai para a IA."""
    pernas = f.get("pernas") or []
    faltam: list[tuple[str, str]] = []
    esportes = set()
    for p in pernas:
        k = ("esporte", _esp(p))
        if k[1] and k in termos:
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
        par = merc + SEP + normalizar(pernas[0].get("selecao_casa"), numeros=False)
        categoria = termos.get(("categoria", merc)) or termos.get(("categoria", par))
        if categoria is None:
            faltam.append(("categoria", merc))
    return esporte, categoria, faltam


async def carregar(conn, casa_key: str) -> dict:
    """Os termos da casa e os que valem para todas (`*`). O da casa vence o geral."""
    termos: dict = {}
    for r in await conn.fetch(
            "SELECT casa, tipo, termo_casa, termo_sharpen FROM dicionario_termos "
            "WHERE casa = ANY($1::text[]) ORDER BY (casa = '*') DESC",
            ["*", (casa_key or "").upper()]):
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


def votar(pares, votos_texto=()) -> tuple[dict, dict]:
    """Semente (`04 §3`). `pares` = [(casa, Ficha, esporte da IA, categoria da IA)];
    `votos_texto` = [(casa, termos de esporte do texto, esporte da IA)], o complemento do
    `sombra_rotulos` (só esporte: no texto o mercado vem colado à seleção).
    Devolve ({(casa, tipo, termo): (termo Sharpen, ocorrências)} só com os UNÂNIMES,
    {(casa, tipo, termo): Counter} com os que a IA decidiu de mais de um jeito).

    Só vota o que a Ficha isola sem ambiguidade: esporte de bilhete de UM esporte (a IA
    escreve `Múltiplos` também para 3 jogos do mesmo esporte, e aí o voto não diz nada do
    termo) e categoria de SIMPLES de uma perna."""
    from collections import Counter, defaultdict
    votos: dict = defaultdict(Counter)
    for casa, f, esp_ia, cat_ia in pares:
        casa = (casa or "").upper()
        pernas = f.get("pernas") or []
        termos_esp = {_esp(p) for p in pernas} - {""}
        esp_ia, cat_ia = _limpo(esp_ia), _limpo(cat_ia)
        if len(termos_esp) == 1 and esp_ia and esp_ia != MULTIPLOS:
            votos[(casa, "esporte", next(iter(termos_esp)))][esp_ia] += 1
        if f.get("tipo") == "simples" and len(pernas) == 1 and cat_ia and cat_ia != MULTIPLA:
            p = pernas[0]
            merc = normalizar(p.get("mercado_casa"))
            if merc:
                votos[(casa, "categoria", merc)][cat_ia] += 1
                votos[(casa, "categoria", merc + SEP + normalizar(p.get("selecao_casa"), numeros=False))][cat_ia] += 1
    for casa, termos_txt, esp_ia in votos_texto:
        termos_esp = {normalizar(t, numeros=False) for t in termos_txt} - {""}
        esp_ia = _limpo(esp_ia)
        if len(termos_esp) == 1 and esp_ia and esp_ia != MULTIPLOS:
            votos[((casa or "").upper(), "esporte", next(iter(termos_esp)))][esp_ia] += 1
    unanimes, contraditos = {}, {}
    for k, c in votos.items():
        if len(c) == 1:
            termo, n = next(iter(c.items()))
            unanimes[k] = (termo, n)
        else:
            contraditos[k] = c
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
    return unanimes, contraditos


# ── semente (`04 §3`): os pares que já existem ─────────────────────────────────────────

async def pares(conn) -> tuple[list, list, dict]:
    """([(casa_key, Ficha, esporte da IA, categoria da IA)], um por aposta com cru;
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
    bil = {(b["dono"], b["casa"], b["parceiro"], b["codigo_bilhete"]): b for b in await conn.fetch(
        "SELECT dono, casa, parceiro, codigo_bilhete, esporte, aposta FROM bilhetes "
        "WHERE codigo_bilhete = ANY($1::text[]) AND origem IS DISTINCT FROM 'ficha'", codigos)}
    sombra = {(s["dono"], s["codigo"]): s for s in await conn.fetch(
        "SELECT DISTINCT ON (dono, codigo) dono, codigo, ia_esporte, ia_aposta "
        "FROM sombra_rotulos WHERE codigo = ANY($1::text[]) ORDER BY dono, codigo, criado_em DESC",
        codigos)}
    out, fontes = [], Counter()
    for (dono, casa, parceiro, codigo), r in ultimo.items():
        f, motivos = ficha.montar_ficha(r["familia"], json.loads(r["cru"]), casa)
        if f is None or motivos:
            continue
        b = bil.get((dono, nomes.get(casa, casa), parceiro, codigo))
        if b:
            out.append((casa, f, b["esporte"], b["aposta"]))
            fontes["bilhetes"] += 1
        elif (s := sombra.get((dono, codigo))):
            out.append((casa, f, s["ia_esporte"], s["ia_aposta"]))
            fontes["sombra_rotulos"] += 1
        else:
            fontes["sem par"] += 1
    # Complemento de ESPORTE: o texto do SharpenUp em `sombra_rotulos` escreve o termo da casa
    # por perna (`Esporte: tennis`), desde antes do cru existir. Só onde dá para dizer de qual
    # perna é o termo (`esportes_do_texto`).
    texto = []
    for s in await conn.fetch(
            "SELECT DISTINCT ON (dono, casa, codigo) casa, bruto, ia_esporte FROM sombra_rotulos "
            "WHERE codigo IS NOT NULL ORDER BY dono, casa, codigo, criado_em DESC"):
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


async def semear(conn) -> dict:
    p, texto, fontes = await pares(conn)
    unanimes, contraditos = votar(p, texto)
    n = await gravar_semente(conn, unanimes)
    return {"termos": n, "contraditos": len(contraditos), "fontes": fontes}


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
                r = await semear(conn)
            log.info("dicionário: semente diária, %s", r)
        except Exception:  # noqa: BLE001
            log.exception("dicionário: a semente diária falhou; vale a de ontem")
