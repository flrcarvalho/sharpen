"""Virada da Ficha (`03_REGUA_NUMEROS §7`; s409 construída desligada, s411 ligada casa a casa).

Regra do Feca: **recusada nunca pode significar aposta perdida.** Por isso a virada é feita
de duas metades, e a segunda já existia:

  1. **Aqui:** na casa VIRADA, a Ficha ACEITA vira linha da planilha pelo MESMO `/salvar` de
     hoje (mesmo `validar_linhas`, mesma conversão de moeda, mesmo UPSERT e mesma dedup), com
     `origem = 'ficha'`. Ficha recusada não grava nada: o bilhete dela segue pelo texto.
  2. **No `/extrair`, sem código novo:** o pré-dedup por código (`main._dedup_superbet_text`)
     já tira do lote, antes da IA, o bloco cujo código está RESOLVIDO no banco naquela conta.
     A aposta que a Ficha gravou liquidada sai dali sozinha, e a IA não paga por ela. Todo o
     resto vai para a IA como hoje: Ficha recusada, cru que não chegou ou chegou depois do
     `/extrair`, e aposta ABERTA (que a IA relê até liquidar, como sempre). Não existe um
     caminho em que o bilhete fica sem nenhum dos dois.

`FICHA_CASAS_VIRADAS` = lista de casas (`DEXSPORT,MYSTAKE`). **Vazia = nada vira**, e a rota da
Ficha faz só o que fazia. `*` NÃO vale: cada casa vira por nome. Desligar a chave volta a casa
ao caminho de hoje na hora, sem deploy.

Três coisas a Ficha NÃO grava, e a aposta segue para a IA pelo texto (s411, regras do Feca de
12/10):
  • **termo sem par no dicionário** (`app/dicionario.py`): esporte ou categoria que a tabela
    `dicionario_termos` não traduz. A IA classifica como hoje, e a próxima semente aprende;
  • **código que já está no banco por OUTRO caminho** (D10, o histórico não é reescrito pela
    Ficha): linha gravada pela IA, por import ou à mão fica com quem a gravou. A Ficha só
    escreve aposta nova e as que ela mesma gravou (aberta que liquidou);
  • Ficha recusada (adaptador ou validação), como sempre.

Falha ao gravar NUNCA derruba a rota: o cru e a Ficha já estão guardados, a aposta não entra
em `bilhetes`, o pré-dedup não a encontra e ela vai para a IA pelo texto.
"""
from __future__ import annotations

import json
import logging
import os
import re

import dicionario as _dic
import ficha as _ficha

logger = logging.getLogger("scanner")

ORIGEM = "ficha"
# Sistema uniforme (`MASTER_RESULTADO §7.3`): `k` = tamanho de cada linha.
_NOME_K = {1: "Simples", 2: "Duplas", 3: "Triplas", 4: "Quádruplas", 5: "Quíntuplas",
           6: "Sêxtuplas"}
_SISTEMA_VB = re.compile(r"^(\d+) x (\d+) de (\d+)$")


def casas_viradas() -> frozenset:
    brutas = os.environ.get("FICHA_CASAS_VIRADAS", "")
    return frozenset(c.strip().upper() for c in brutas.split(",") if c.strip() and c.strip() != "*")


def virada(casa_key: str) -> bool:
    return (casa_key or "").upper() in casas_viradas()


def _limpo(v) -> str:
    """Texto de campo de TSV: TAB e quebra de linha deslocariam as colunas."""
    return " ".join(str(v or "").split())


def _descricao(f: dict) -> str:
    """`<seleção> <linha> <mercado> [<jogo>]` (`01_FICHA §3`), pernas unidas por ` // `. Fica
    com o termo da casa. A linha (handicap/total) entra quando a casa a manda em campo
    próprio e ela ainda não está no texto: sem ela, `Acima` não diz acima de quê."""
    partes = []
    for p in f.get("pernas") or []:
        sel, merc, ev = (_limpo(p.get(k)) for k in ("selecao_casa", "mercado_casa", "evento"))
        linha = _limpo(p.get("linha"))
        if linha and linha in f"{sel} {merc}":
            linha = ""
        rotulo = " ".join(x for x in (sel, linha, merc) if x)
        partes.append(f"{rotulo} [{ev}]" if ev else rotulo)
    return " // ".join(partes)


def _sistema(f: dict) -> str:
    """12ª coluna (`N x Rótulo`, a do `anexar_sistema_tsv`), quando a Ficha diz a estrutura.
    Hoje a Altenar (`vb`: `3 x 2 de 3`). Formato que não se lê = vazio, nunca um palpite."""
    if f.get("tipo") != "sistema":
        return ""
    m = _SISTEMA_VB.match(_limpo(f.get("sistema")))
    if not m:
        return ""
    linhas, k = int(m.group(1)), int(m.group(2))
    return f"{linhas}x {_NOME_K[k]}" if k in _NOME_K else ""


def _carimbo(f: dict) -> str | None:
    """`colocada_em` no formato do `carimbos_do_texto` (14 dígitos), no fuso de Brasília: é a
    data em que o dinheiro saiu, e a cotação da conta em outra moeda sai dela."""
    d = _ficha._instante(f.get("colocada_em"))
    return d.astimezone(_ficha._BRT).strftime("%Y%m%d%H%M%S") if d else None


def linha_tsv(f: dict, casa: str, parceiro: str, esporte: str, categoria: str) -> str:
    """A linha da planilha (`MASTER_OUTPUT §2`, 10 colunas + código + sistema) de uma Ficha
    ACEITA, com esporte e categoria JÁ traduzidos (`dicionario.traduzir`)."""
    d = _ficha.derivar(f)
    col = [
        d["data"], _limpo(esporte), "", _limpo(casa), _limpo(parceiro), _limpo(categoria),
        _descricao(f), d["stake"], d["odd"] or "", d["resultado"], _limpo(f.get("codigo")),
    ]
    if (s := _sistema(f)):
        col.append(s)
    return "\t".join(col)


async def gravar_na_planilha(dono: str, casa: str, parceiro: str, itens: list[tuple]) -> dict:
    """Grava Fichas ACEITAS em `bilhetes` pelo `/salvar`. `itens` = [(Ficha, esporte, categoria)].
    Devolve a resposta dele."""
    if not itens:
        return {"salvos": 0, "rejeitados": [], "alertas": []}
    import main as _main          # tardio: o `main` inclui o router da Ficha
    linhas, carimbos, freebets, moedas = [], {}, {}, set()
    for f, esporte, categoria in itens:
        linhas.append(linha_tsv(f, casa, parceiro, esporte, categoria))
        cod = _limpo(f.get("codigo"))
        if (c := _carimbo(f)):
            carimbos[cod] = c
        fb = _ficha._dec(f.get("stake_freebet"))
        if fb is not None and fb > 0:
            freebets[cod] = _ficha._odd_br(fb)
        if f.get("moeda"):
            moedas.add(str(f["moeda"]).upper())
    corpo = _main.SalvarRequest(tsv="\n".join(linhas), casa=casa, parceiro=parceiro,
                                carimbos=carimbos, freebets=freebets, moedas=sorted(moedas))
    r = await _main.gravar_tsv(corpo, dono, dono, origem=ORIGEM)
    if r.get("rejeitados"):
        logger.warning("virada: %s %s · %d linha(s) da Ficha recusada(s) no /salvar: %s",
                       dono, casa, len(r["rejeitados"]), r["rejeitados"][:2])
    return r


async def _de_outro_caminho(conn, dono: str, codigos: list[str]) -> set[str]:
    """Códigos que o banco já tem por outro caminho (IA, import, mão): a Ficha não os
    reescreve (D10). Olha o dono inteiro, não só a conta: na dúvida, fica com quem gravou."""
    rows = await conn.fetch(
        "SELECT DISTINCT codigo_bilhete FROM bilhetes WHERE dono = $1 "
        "AND codigo_bilhete = ANY($2::text[]) AND origem IS DISTINCT FROM $3",
        dono, codigos, ORIGEM)
    return {r["codigo_bilhete"] for r in rows}


async def separar(conn, casa_key: str, dono: str, aceitas: list[dict]) -> tuple[list, dict]:
    """([(Ficha, esporte, categoria)] que a Ficha grava, {motivo: n} das que vão para a IA)."""
    termos = await _dic.carregar(conn, casa_key)
    outro = await _de_outro_caminho(conn, dono, [_limpo(f.get("codigo")) for f in aceitas])
    vai, fica = [], {}
    for f in aceitas:
        if _limpo(f.get("codigo")) in outro:
            fica["já no banco por outro caminho"] = fica.get("já no banco por outro caminho", 0) + 1
            continue
        esporte, categoria, faltam = _dic.traduzir(f, termos)
        if faltam:
            fica["termo fora do dicionário"] = fica.get("termo fora do dicionário", 0) + 1
            continue
        vai.append((f, esporte, categoria))
    return vai, fica


async def _separar_no_banco(casa_key: str, dono: str, aceitas: list[dict]) -> tuple[list, dict]:
    from database import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await separar(conn, casa_key, dono, aceitas)


async def gravar_aceitas(sess, registros: list[dict]) -> int:
    """Chamado pela rota da Ficha. Nunca levanta: falha aqui = a aposta vai pela IA."""
    if not virada(sess.casa_key):
        return 0
    aceitas = [json.loads(r["ficha"]) for r in registros if r.get("aceita")]
    if not aceitas:
        return 0
    try:
        vai, fica = await _separar_no_banco(sess.casa_key, sess.dono, aceitas)
        if fica:
            logger.info("virada: %s %s · %s ficam com a IA", sess.dono, sess.casa_key, fica)
        r = await gravar_na_planilha(sess.dono, sess.casa, sess.parceiro, vai)
    except Exception:  # noqa: BLE001 — o texto cobre; derrubar a rota perderia o cru seguinte
        logger.exception("virada: falha ao gravar %d Ficha(s) de %s/%s; vão pela IA",
                         len(aceitas), sess.dono, sess.casa_key)
        return 0
    return int(r.get("salvos") or 0)
