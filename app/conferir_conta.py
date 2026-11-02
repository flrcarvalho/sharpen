"""D44 (Feca, 01/11/2026): "Conferir conta com a casa". LOCAL, sem commit (limite do Feca).

Por que existe: a tela não tinha como corrigir base já gravada. Recapturar não conserta linha
resolvida (o UPSERT congela stake/odd), então quem via a Caixa divergir só tinha uma saída:
apagar e recapturar (o Gabriel, Shuffle, 31/10). Aqui a conta inteira é conferida contra o
cru que a casa mandou, sem IA, e o usuário corrige com um clique, sem apagar nada.

A régua é a do vigia (`virada.vigia_comparar`), as duas pontas na moeda da CASA:
  · stake, resultado, e a odd só onde ela muda o dinheiro (P/L na liquidada; a odd na aberta);
  · moeda diferente é divergência que NÃO se oferece: trocar a moeda de uma linha é decisão
    de câmbio (a cotação do dia), não de leitura.

Três regras que decidem escrita:
  1. Correção humana manda (CLAUDE.md, "os 3 bilhetes Betano"): linha com `correcoes` HUMANA
     em stake/odd/resultado aparece, mas não é oferecida. A correção deste botão grava
     `origem='conferir'` e não trava nada (Feca, 02/11/2026): se a casa reliquidar, a linha
     volta a ser oferecida; a da Ficha (`'ficha'`) também é robô (`ORIGENS_DE_ROBO`).
  2. O servidor RECALCULA na hora de aplicar: o cliente manda só ids, nunca valores.
  3. A escrita é a edição de sempre (`repository.atualizar_bilhete`): rastro em `correcoes`,
     estado derivado do resultado, stake de conta em moeda estrangeira pela `stake_orig` (a
     cotação gravada refaz o R$).

Cru ABERTO não desmente linha liquidada (é de antes da liquidação): conta em `cru_aberto`.
BÔNUS NÃO É ODD (Feca, 02/11/2026): ganha, a linha com a odd da casa, e a casa pagou MAIS que
stake × odd (Vavada `bonus`, MyStake `RiskBonusPercent`): a divergência é o bônus, e vai para
`bonus`, fora da lista. Cashout nunca cai aqui: ele paga menos que stake × odd.
A divergência só de odd abaixo de `PISO_PL` no P/L não aparece.

O que NÃO faz: aposta sem cru guardado (casa por print, texto colado, ou captura anterior ao
cru) não tem com o que comparar e só entra na contagem `sem_cru`; descrição, esporte e
categoria ficam de fora (não mudam dinheiro, e o dicionário já regrava o mês corrente).
"""
from __future__ import annotations

import json
import logging

import cambio as _cambio
import casa_chave as _cc
import ficha as _ficha
import virada as _virada
from repository import ORIGENS_DE_ROBO, _ORIGEM_CONFERIR

logger = logging.getLogger("scanner")

CAMPOS_DINHEIRO = ("stake", "odd", "resultado")
# Só a odd diverge e o P/L muda menos que isto (na moeda da casa): não é divergência. É o piso do
# CLAUDE.md ("o piso de R$ 1,00"): abaixo dele a "correção" troca centavo por dízima. Medido
# na produção (02/11): Shuffle e Sportsbet.io guardam a stake com 7 a 8 casas (18,8662713) e
# a linha tem 18,87; o P/L difere em R$ 0,01 a 0,03.
PISO_PL = 1.0
_K = _cc.sql("casa")


def lado_da_casa(f: dict, moeda: str) -> dict | None:
    """A linha que o cru manda gravar, no formato da planilha e na moeda da casa. None quando
    o status do cru não se deriva (não é prova de nada)."""
    try:
        d = _ficha.derivar(f)
    except ValueError:
        return None
    return {"stake": d["stake"], "odd": d["odd"], "resultado": d["resultado"] or "",
            "moeda": moeda}


def e_so_bonus(f: dict, b: dict) -> bool:
    """A Ficha ganhou, a linha do banco tem a odd da casa (`f["odd"]`) e o retorno da casa passa
    de stake × odd: o que sobra é bônus, não odd."""
    if f.get("status") != "ganha":
        return False
    banco = _virada._na_moeda_da_casa(b)
    stake, odd, ret = _virada._f(f.get("stake")), _virada._f(f.get("odd")), _virada._f(f.get("retorno"))
    odd_b = _virada._f(banco.get("odd"))
    if None in (stake, odd, ret, odd_b) or abs(odd_b - odd) > 0.005:
        return False
    return ret - stake * odd > 0.005


def comparar_linha(b: dict, casa: dict, corrigidos: set) -> dict | None:
    """Uma divergência (ou None) entre a linha do banco `b` e o que a casa manda `casa`.
    `corrigidos` = campos de dinheiro desta linha que alguém já corrigiu à mão."""
    banco = _virada._na_moeda_da_casa(b)
    campos = _virada.vigia_comparar(casa, banco)        # o banco sempre tem linha: nunca "linha"
    if not campos:
        return None
    if campos == ["odd"]:
        pc = _virada._pl(_virada._f(casa.get("stake")), _virada._f(casa.get("odd")),
                         casa.get("resultado"))
        pb = _virada._pl(_virada._f(banco.get("stake")), _virada._f(banco.get("odd")),
                         banco.get("resultado"))
        if pc is not None and pb is not None and abs(pc - pb) < PISO_PL:
            return None
    motivo = None
    if "moeda" in campos:
        motivo = "moeda diferente"
    elif corrigidos & set(campos):
        motivo = "corrigida à mão"
    return {"id": b["id"], "codigo": b["codigo_bilhete"], "campos": campos,
            "banco": {k: banco.get(k) for k in (*CAMPOS_DINHEIRO, "moeda")},
            "casa": {k: casa.get(k) for k in (*CAMPOS_DINHEIRO, "moeda")},
            "descricao": b.get("descricao"), "data": b.get("data"),
            "oferecida": motivo is None, "motivo": motivo}


def patch_da_correcao(b: dict, casa: dict, campos: list[str]) -> dict:
    """O patch da edição de sempre para levar a linha ao que a casa manda. Só os campos que
    divergem; a odd vai junto do resultado (W→L muda a régua do P/L)."""
    patch = {}
    if "resultado" in campos or "odd" in campos:
        patch["resultado"] = casa["resultado"]
        if casa.get("odd"):
            patch["odd"] = casa["odd"]
    if "stake" in campos:
        if b.get("moeda") and b.get("stake_orig") is not None:
            patch["stake_orig"] = casa["stake"]        # a cotação gravada refaz o R$
        else:
            patch["stake"] = casa["stake"]
    return patch


def conferir(linhas: list[dict], crus: dict, corrigidos: dict, conta: str, ck: str) -> dict:
    """O miolo, sem banco: `linhas` = apostas da conta; `crus` = {código: (família, cru)} com o
    cru mais recente de cada código; `corrigidos` = {id: campos com correção humana}; `conta` =
    a moeda da conta; `ck` = chave da casa. A medição na produção roda ESTA função sobre o
    resultado dos mesmos SELECTs."""
    out = {"conferidas": 0, "sem_cru": 0, "cru_recusado": 0, "cru_aberto": 0, "bonus": 0,
           "divergentes": []}
    for b in linhas:
        cru = crus.get(b["codigo_bilhete"])
        if not cru:
            out["sem_cru"] += 1
            continue
        f, motivos = _ficha.montar_ficha(cru[0], cru[1], ck)
        if f is None or motivos:
            out["cru_recusado"] += 1
            continue
        moeda = _cambio.moeda_do_cru(conta, str(f.get("moeda") or "").upper() or None) or conta
        lado = lado_da_casa(f, moeda)
        if lado is None:
            out["cru_recusado"] += 1
            continue
        if not lado["resultado"] and (b.get("resultado") or "").strip():
            # o cru guardado é de ANTES da liquidação (a casa não mandou cru novo): não desmente
            # a linha liquidada. Medido (02/11): 21 linhas L/V/W contra cru aberto.
            out["cru_aberto"] += 1
            continue
        d = comparar_linha(dict(b), lado, corrigidos.get(b["id"], set()))
        if d and d["campos"] == ["odd"] and e_so_bonus(f, b):
            out["bonus"] += 1                  # bônus não é odd (Feca, 02/11)
            continue
        out["conferidas"] += 1
        if d:
            out["divergentes"].append(d)
    return out


SQL_LINHAS = (
    "SELECT id, codigo_bilhete, stake, odd, resultado, moeda, stake_orig, descricao, data "
    f"FROM bilhetes WHERE dono = $1 AND {_K} = $2 AND parceiro = $3 "
    "AND COALESCE(codigo_bilhete, '') <> '' ORDER BY id")
# o cru mais recente de cada código, na mesma ordem do `ficha.moedas_do_cru_conn`
SQL_CRUS = (
    "SELECT DISTINCT ON (codigo) codigo, familia, cru::text AS cru FROM captura_crua "
    "WHERE dono = $1 AND casa = $2 AND parceiro = $3 AND codigo = ANY($4::text[]) "
    "ORDER BY codigo, recebido_em DESC, id DESC")
SQL_CORRIGIDOS = (
    "SELECT bilhete_id, campo FROM correcoes WHERE dono = $1 "
    "AND bilhete_id = ANY($2::bigint[]) AND campo = ANY($3::text[]) "
    "AND COALESCE(origem, '') <> ALL($4::text[])")


async def divergencias(conn, dono: str, casa: str, parceiro: str) -> dict:
    """Confere toda aposta da conta que tem cru guardado. Devolve contagens e a lista."""
    ck = _virada.chave_da_casa(casa)
    linhas = [dict(r) for r in await conn.fetch(SQL_LINHAS, dono, ck, parceiro)]
    codigos = [r["codigo_bilhete"] for r in linhas]
    crus = {r["codigo"]: (r["familia"], json.loads(r["cru"]))
            for r in await conn.fetch(SQL_CRUS, dono, ck, parceiro, codigos)} if codigos else {}
    corrigidos: dict = {}
    for r in await conn.fetch(SQL_CORRIGIDOS, dono, [r["id"] for r in linhas],
                              list(CAMPOS_DINHEIRO), list(ORIGENS_DE_ROBO)):
        corrigidos.setdefault(r["bilhete_id"], set()).add(r["campo"])
    conta = await conn.fetchval(
        f"SELECT moeda FROM parceiros WHERE dono = $1 AND {_K} = $2 AND nome = $3 LIMIT 1",
        dono, ck, parceiro) or _cambio.BRL
    return conferir(linhas, crus, corrigidos, conta, ck)


async def aplicar(dono: str, casa: str, parceiro: str, ids: list[int]) -> dict:
    """Corrige as divergências OFERECIDAS cujos ids o usuário marcou, recalculando tudo aqui
    (o cliente nunca manda valor). Devolve quantas corrigiu e as que recusou, com o porquê."""
    import repository
    from database import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        atual = await divergencias(conn, dono, casa, parceiro)
        linhas = {r["id"]: dict(r) for r in await conn.fetch(
            "SELECT id, moeda, stake_orig FROM bilhetes WHERE dono = $1 "
            "AND id = ANY($2::bigint[])", dono, list(ids))}
    por_id = {d["id"]: d for d in atual["divergentes"]}
    feitas, recusadas = 0, []
    for i in ids:
        d = por_id.get(i)
        if d is None:
            recusadas.append({"id": i, "motivo": "já confere com a casa"})
            continue
        if not d["oferecida"]:
            recusadas.append({"id": i, "motivo": d["motivo"]})
            continue
        patch = patch_da_correcao(linhas[i], d["casa"], d["campos"])
        if await repository.atualizar_bilhete(i, patch, dono, rastro=_ORIGEM_CONFERIR):
            feitas += 1
        else:
            recusadas.append({"id": i, "motivo": "a edição foi recusada"})
    logger.info("conferir conta: %s %s %s · %d corrigidas, %d recusadas",
                dono, casa, parceiro, feitas, len(recusadas))
    return {"corrigidas": feitas, "recusadas": recusadas}
