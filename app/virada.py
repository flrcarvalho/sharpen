"""Virada da Ficha (`03_REGUA_NUMEROS §7`; s409, construída DESLIGADA em 12/10/2026).

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
Ficha faz só o que fazia. `*` NÃO vale: cada casa vira com o "pode" do Feca, uma por vez.
Desligar a chave volta a casa ao caminho de hoje na hora, sem deploy.

Esporte e categoria vão com o TERMO DA CASA (`04_DICIONARIO §4.1`): o dicionário ainda não
existe, e é ele que traduz. Antes da 1ª virada, o termo de cada casa precisa estar no
dicionário, ou a grade mostra `football` e `sportTypeId 4` onde hoje mostra Futebol e Tênis.

Falha ao gravar NUNCA derruba a rota: o cru e a Ficha já estão guardados, a aposta não entra
em `bilhetes`, o pré-dedup não a encontra e ela vai para a IA pelo texto.
"""
from __future__ import annotations

import json
import logging
import os

import ficha as _ficha

logger = logging.getLogger("scanner")

ORIGEM = "ficha"


def casas_viradas() -> frozenset:
    brutas = os.environ.get("FICHA_CASAS_VIRADAS", "")
    return frozenset(c.strip().upper() for c in brutas.split(",") if c.strip() and c.strip() != "*")


def virada(casa_key: str) -> bool:
    return (casa_key or "").upper() in casas_viradas()


def _limpo(v) -> str:
    """Texto de campo de TSV: TAB e quebra de linha deslocariam as colunas."""
    return " ".join(str(v or "").split())


def _esporte(f: dict) -> str:
    """Termo da casa (`04_DICIONARIO §4.1`). Mistura de esportes, ou 3+ jogos diferentes,
    é `Múltiplos` (`MASTER_ESPORTES §2`)."""
    pernas = f.get("pernas") or []
    termos = {_limpo(p.get("esporte_casa")) for p in pernas} - {""}
    jogos = {_limpo(p.get("evento")) for p in pernas} - {""}
    if len(termos) > 1 or len(jogos) >= 3:
        return "Múltiplos"
    return next(iter(termos), "")


def _aposta(f: dict) -> str:
    pernas = f.get("pernas") or []
    if f.get("tipo") != "simples" or len(pernas) > 1:
        return "Múltipla"
    return _limpo(pernas[0].get("mercado_casa")) if pernas else ""


def _descricao(f: dict) -> str:
    partes = []
    for p in f.get("pernas") or []:
        sel, merc, ev = (_limpo(p.get(k)) for k in ("selecao_casa", "mercado_casa", "evento"))
        rotulo = " · ".join(x for x in (merc, sel) if x)
        partes.append(f"{rotulo} [{ev}]" if ev else rotulo)
    return " // ".join(partes)


def _carimbo(f: dict) -> str | None:
    """`colocada_em` no formato do `carimbos_do_texto` (14 dígitos), no fuso de Brasília: é a
    data em que o dinheiro saiu, e a cotação da conta em outra moeda sai dela."""
    d = _ficha._instante(f.get("colocada_em"))
    return d.astimezone(_ficha._BRT).strftime("%Y%m%d%H%M%S") if d else None


def linha_tsv(f: dict, casa: str, parceiro: str) -> str:
    """A linha da planilha (`MASTER_OUTPUT §2`, 10 colunas + código) de uma Ficha ACEITA."""
    d = _ficha.derivar(f)
    return "\t".join([
        d["data"], _esporte(f), "", _limpo(casa), _limpo(parceiro), _aposta(f), _descricao(f),
        d["stake"], d["odd"] or "", d["resultado"], _limpo(f.get("codigo")),
    ])


async def gravar_na_planilha(dono: str, casa: str, parceiro: str, fichas: list[dict]) -> dict:
    """Grava Fichas ACEITAS em `bilhetes` pelo `/salvar`. Devolve a resposta dele."""
    if not fichas:
        return {"salvos": 0, "rejeitados": [], "alertas": []}
    import main as _main          # tardio: o `main` inclui o router da Ficha
    linhas, carimbos, freebets, moedas = [], {}, {}, set()
    for f in fichas:
        linhas.append(linha_tsv(f, casa, parceiro))
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


async def gravar_aceitas(sess, registros: list[dict]) -> int:
    """Chamado pela rota da Ficha. Nunca levanta: falha aqui = a aposta vai pela IA."""
    if not virada(sess.casa_key):
        return 0
    aceitas = [json.loads(r["ficha"]) for r in registros if r.get("aceita")]
    if not aceitas:
        return 0
    try:
        r = await gravar_na_planilha(sess.dono, sess.casa, sess.parceiro, aceitas)
    except Exception:  # noqa: BLE001 — o texto cobre; derrubar a rota perderia o cru seguinte
        logger.exception("virada: falha ao gravar %d Ficha(s) de %s/%s; vão pela IA",
                         len(aceitas), sess.dono, sess.casa_key)
        return 0
    return int(r.get("salvos") or 0)
