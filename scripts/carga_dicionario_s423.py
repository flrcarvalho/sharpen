"""Carga do dicionário, parecer 021 da consultoria, com as decisões D33 a D36 do Feca (s423).

Etapa 1 (correções que vão antes) e etapa 2 (esporte por tradução direta), todas pelo
`dicionario.corrigir_termo`, `origem = 'feca'`: a semente nunca as sobrescreve, e a correção
regrava só as apostas DA FICHA do mês corrente (D10: mês passado não é tocado). D36 apaga o
`sporttypeid 300` do `*` e da ESPORTIVA (ele entrou em `VAGOS`, no código).

Sem `--aplicar`, a sessão é SÓ LEITURA no banco (`default_transaction_read_only`) e o script
mostra: o "teste antes" do anexo (a a d), o que cada correção mudaria e a cobertura simulada.
Com `--aplicar`, grava e mede de novo, e mostra os `novos` que a PRÓXIMA semente gravaria (a
mesma conta do `dicionario.semear`, sem gravar nada). D37 (Feca, 18/10): `sporttypeid 34` e
`31` não são esporte; estão em `VAGOS` com o 300 e não são traduzidos aqui.

    python scripts/carga_dicionario_s423.py                 # ensaio
    python scripts/carga_dicionario_s423.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

import asyncpg  # noqa: E402

import dicionario  # noqa: E402
import ficha  # noqa: E402
import virada  # noqa: E402
from limpar_cru_filtro import _carregar_env  # noqa: E402

COMANDO_S = 60                   # sem resposta do banco em 60 s, o script para
CASAS9 = ("SHUFFLE", "DEXSPORT", "MEGAPARI", "MYSTAKE", "DUEL", "BETMARTINI", "BETPANDA",
          "VAVADA", "1WIN")

# Etapa 1 (parecer 021 §6, D31, D24, D34, D35)
ETAPA1 = [
    ("DEXSPORT", "descricao", "football | ganador sin empate", "DNB {ent}"),          # D31
    ("DEXSPORT", "categoria", "ganador sin empate", "DNB"),                           # D31
    ("BETMARTINI", "descricao", "sporttypeid 1 | total", "{ou}"),                      # D24
    ("DEXSPORT", "descricao", "basketball | total. half {n}", "{ou} Pontos {n1}ª Metade"),  # D34
    ("DEXSPORT", "descricao", "basketball | total. quarter {n}", "{ou} Pontos {n1}º Quarto"),  # D34
    ("MYSTAKE", "descricao", "league of legends | {n}º mapa - total de mortes",
     "{ou} Kills {n1}º Mapa"),                                                        # D35
    ("MYSTAKE", "categoria", "{n}º mapa - total de mortes", "E-Sports Props"),        # D35
    ("MYSTAKE", "descricao", "league of legends | {n}° mapa - vantagem de morte",
     "{ent} {hc} Kills {n1}º Mapa"),                                                  # D35 (Kills)
]
# Etapa 2 (parecer 021, anexo; D33). Os `sporttypeid` vêm do `_ESPORTE_VB` (`content.js`).
_ESP = {
    "andebol": "Handebol", "sporttypeid 19": "Vôlei", "sporttypeid 13": "Baseball",
    "basebol": "Baseball", "mixed martial arts": "MMA", "ufc": "MMA", "sporttypeid 40": "MMA",
    "cs2": "E-Sports", "dota 2": "E-Sports", "rainbow6": "E-Sports",
    "american-football": "Futebol Americano", "ténis de mesa": "Tênis de Mesa",
    "rugby-union": "Rugby", "rugby_union": "Rugby", "rugby de 15": "Rugby",
    "sporttypeid 5": "Rugby", "voleibol": "Vôlei", "sporttypeid 9": "Dardos",
    "hôquei no gelo": "Hóquei",
    # D33
    "boxing": "Boxe", "cricket": "Críquete", "martial arts": "MMA", "water polo": "Polo Aquático",
    "futsal": "Futsal", "australian football": "Futebol Australiano",
    "futebol australiano": "Futebol Australiano", "bandy": "Bandy", "floorball": "Floorball",
}
D36 = [("*", "esporte", "sporttypeid 300"), ("ESPORTIVA", "esporte", "sporttypeid 300")]


def correcoes() -> list[tuple]:
    return ETAPA1 + [("*", "esporte", k, v) for k, v in _ESP.items()]


async def teste(conn) -> dict:
    """a. dicionário por casa/tipo/origem; b. último semente_log; d. agosto e setembro."""
    a = [dict(r) for r in await conn.fetch(
        "SELECT casa, tipo, origem, count(*) n FROM dicionario_termos WHERE casa = ANY($1::text[]) "
        "GROUP BY 1, 2, 3 ORDER BY 1, 2, 3", list(CASAS9) + ["*", "ESPORTIVA"])]
    b = dict(await conn.fetchrow(
        "SELECT id, criado_em::text, termos, jsonb_array_length(novos) novos, regravadas "
        "FROM semente_log ORDER BY id DESC LIMIT 1"))
    d = [dict(r) for r in await conn.fetch(
        "SELECT casa, count(*) n, max(atualizado_em)::text ultimo FROM bilhetes "
        "WHERE data ~ '^\\d{2}/0[89]/2026' OR data ~ '^2026-0[89]-' GROUP BY 1 ORDER BY 1")]
    return {"a": a, "b": b, "d": d}


async def cobertura(conn, extra=None) -> dict:
    """c. As Fichas do último cru de cada código das 9 casas por `traduzir` + `virada.descricao`.
    `extra` = {(casa, tipo, termo): valor}, as correções ainda não gravadas (a do Feca vence)."""
    crus = await conn.fetch(
        "SELECT DISTINCT ON (dono, casa, codigo) casa, familia, cru::text AS cru FROM captura_crua "
        "WHERE casa = ANY($1::text[]) ORDER BY dono, casa, codigo, id DESC", list(CASAS9))
    cache, n, ok, motivos = {}, 0, Counter(), Counter()
    for c in crus:
        f, mot = ficha.montar_ficha(c["familia"], json.loads(c["cru"]), c["casa"])
        n += 1
        if f is None or mot:
            motivos["ficha recusada"] += 1
            continue
        if c["casa"] not in cache:
            t = await dicionario.carregar(conn, c["casa"])
            for (cs, tp, k), v in (extra or {}).items():
                if cs in ("*", c["casa"]):
                    t[(tp, k)] = v
            cache[c["casa"]] = t
        termos = cache[c["casa"]]
        esporte, categoria, faltam = dicionario.traduzir(f, termos)
        if faltam:
            motivos["termo fora"] += 1
        elif not virada.no_master(esporte, categoria):
            motivos["fora do Master"] += 1
        elif not virada.descricao(f, termos):
            motivos["descrição fora"] += 1
        else:
            ok[c["casa"]] += 1
    return {"total": n, "pela_ficha": sum(ok.values()), "por_casa": dict(ok),
            "motivos": dict(motivos)}


async def novos_previstos(conn) -> list[dict]:
    """Os `novos` da próxima semente: a conta do `dicionario.semear` (pares, voto, o que o Feca
    já cobre, o que a semente tem hoje), sem gravar nada."""
    p, texto, _ = await dicionario.pares(conn)
    unanimes, _, _ = dicionario.votar(p, texto)
    feca = [(r["casa"], r["tipo"], r["termo_casa"]) for r in await conn.fetch(
        "SELECT casa, tipo, termo_casa FROM dicionario_termos WHERE origem = 'feca'")]
    unanimes = {k: v for k, v in unanimes.items() if not dicionario.coberto_pelo_feca(feca, *k)}
    antes = {(r["casa"], r["tipo"], r["termo_casa"]): r["termo_sharpen"] for r in await conn.fetch(
        "SELECT casa, tipo, termo_casa, termo_sharpen FROM dicionario_termos "
        "WHERE origem = 'semente'")}
    return [{"casa": c, "tipo": t, "termo": k, "para": v, "hoje": antes.get((c, t, k))}
            for (c, t, k), (v, _) in sorted(unanimes.items()) if antes.get((c, t, k)) != v]


_SQL_CRU = ("SELECT familia, cru::text AS cru FROM captura_crua WHERE dono = $1 AND casa = $2 "
            "AND codigo = $3 ORDER BY id DESC LIMIT 1")


class _Conn:
    """A conexão de verdade, com UMA consulta servida de cache: o cru mais recente de cada código
    que o `regravar_mes` lê um a um (milhares de idas ao banco por correção). O resto passa
    direto, o código do `dicionario` é o mesmo."""

    def __init__(self, conn, crus: dict):
        self._c, self._crus = conn, crus

    async def fetchrow(self, sql, *a):
        if sql == _SQL_CRU:
            return self._crus.get(a)
        return await self._c.fetchrow(sql, *a)

    def __getattr__(self, nome):
        return getattr(self._c, nome)


async def _com_cache(conn) -> _Conn:
    crus = {(r["dono"], r["casa"], r["codigo"]): {"familia": r["familia"], "cru": r["cru"]}
            for r in await conn.fetch(
                "SELECT DISTINCT ON (c.dono, c.casa, c.codigo) c.dono, c.casa, c.codigo, "
                "c.familia, c.cru::text AS cru FROM captura_crua c JOIN ficha_virada f "
                "ON f.dono = c.dono AND f.casa = c.casa AND f.codigo = c.codigo "
                "WHERE f.estado = 'ficha' ORDER BY c.dono, c.casa, c.codigo, c.id DESC")}
    return _Conn(conn, crus)


def _chave(tipo, termo):
    if tipo == "descricao":
        return " ".join(termo.casefold().split())
    return dicionario.normalizar(termo, numeros=(tipo == "categoria"))


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    lista = correcoes()
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], command_timeout=COMANDO_S)
    try:
        if not aplicar:
            await conn.execute("SET default_transaction_read_only = on")
        antes = await teste(conn)
        print("TESTE ANTES")
        print(" a. dicionário:", json.dumps(antes["a"], ensure_ascii=False))
        print(" b. último semente_log:", antes["b"])
        print(" d. agosto/setembro:", json.dumps(antes["d"], ensure_ascii=False))
        cob0 = await cobertura(conn)
        print(" c. cobertura hoje:", cob0, flush=True)
        atuais = {(r["casa"], r["tipo"], r["termo_casa"]): (r["termo_sharpen"], r["origem"])
                  for r in await conn.fetch("SELECT casa, tipo, termo_casa, termo_sharpen, origem "
                                            "FROM dicionario_termos")}
        # o `regravar_mes` lê o cru de cada código da Ficha um a um: com o cache, uma ida só
        cc = await _com_cache(conn)
        print(f"\nCORREÇÕES ({len(lista)}) e D36 ({len(D36)}) · cache de {len(cc._crus)} crus",
              flush=True)
        regravar = []
        for casa, tipo, termo, para in lista:
            k = (casa, tipo, _chave(tipo, termo))
            hoje = atuais.get(k)
            mud = await dicionario.corrigir_termo(cc, casa, tipo, termo, para, aplicar=aplicar)
            regravar += mud
            print(f"  {casa:10} {tipo:9} {k[2]!r:55} {hoje} -> {para!r} · regrava {len(mud)}",
                  flush=True)
        for casa, tipo, termo in D36:
            print(f"  D36 {casa} {tipo} {termo!r}: hoje {atuais.get((casa, tipo, termo))}; "
                  f"{'apagado' if aplicar else 'a apagar'} (está em VAGOS: "
                  f"{termo in dicionario.VAGOS})")
            if aplicar:
                await conn.execute("DELETE FROM dicionario_termos WHERE casa = $1 AND tipo = $2 "
                                   "AND termo_casa = $3", casa, tipo, termo)
        print(f"\napostas da Ficha do mês regravadas: {len(regravar)}")
        for m in regravar:
            print(f"   id {m['id']} {m['dono']} {m['codigo']}: {m['antes']} -> {m['depois']}")
        extra = {} if aplicar else {(c, t, _chave(t, k)): v for c, t, k, v in lista}
        cob1 = await cobertura(conn, extra)
        print("\nCOBERTURA depois:", cob1)
        if aplicar:
            print("\nTESTE DEPOIS")
            depois = await teste(conn)
            print(" a. dicionário:", json.dumps(depois["a"], ensure_ascii=False))
            print(" b. último semente_log:", depois["b"])
            print(" d. agosto/setembro:", json.dumps(depois["d"], ensure_ascii=False))
            print(" d. agosto/setembro igual ao antes:", depois["d"] == antes["d"])
            await conn.execute("SET default_transaction_read_only = on")
            nv = await novos_previstos(conn)
            print(f"\nNOVOS DA PRÓXIMA SEMENTE ({len(nv)}), para o consultor revisar:")
            for x in nv:
                print(f"   {x['casa']:10} {x['tipo']:9} {x['termo']!r} -> {x['para']!r} "
                      f"(hoje {x['hoje']!r})")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
