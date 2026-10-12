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
