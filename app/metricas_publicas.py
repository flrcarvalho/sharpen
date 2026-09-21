# -*- coding: utf-8 -*-
"""Números públicos do Sharpen — o que a landing mostra no contador ao vivo.

LEITURA PURA: só SELECT, e nada aqui depende de sessão. É a única consulta do
sistema que roda para quem **não** está logado, e por isso ela tem três travas.

**1. A base de demonstração NÃO conta.** `realtrial` e os `trial_*` são dado
sintético (export anonimizado) e visitante de passagem. Somá-los infla o número
com apostas que ninguém fez — e seria a mesma família do `CUSTO_SEED`, que
mascarou por meses uma base sem custo nenhum: valor de exemplo que se disfarça
de valor real.

**2. Cache de 30 s, com trava.** A landing é pública e o contador consulta em
laço; sem cache, cada aba aberta viraria uma consulta ao Postgres a cada 15 s.
O `Lock` existe para o cache vencido não disparar N consultas ao mesmo tempo.

**3. Nada aqui identifica ninguém.** Contagem agregada, sem nome de dono, de
casa, de conta ou de tipster. O que sai daqui vai para uma página pública.
"""
import asyncio
import logging
import time

from database import get_pool

logger = logging.getLogger(__name__)

TTL_S = 30.0
_cache: dict | None = None
_cache_em = 0.0
_lock = asyncio.Lock()

# Fora da conta: a base de demonstração e todo visitante efêmero. O `LIKE` usa
# escape porque `_` é curinga de um caractere no SQL — sem ele, `trial_%` também
# casaria com qualquer dono de cinco letras começando em "trial".
_FORA = r"dono <> 'realtrial' AND dono NOT LIKE 'trial\_%'"

_SQL = f"""
SELECT
  (SELECT count(*)          FROM bilhetes  WHERE {_FORA})                        AS apostas,
  (SELECT count(DISTINCT casa) FROM bilhetes WHERE {_FORA})                      AS casas,
  (SELECT count(*)          FROM parceiros WHERE {_FORA})                        AS contas,
  (SELECT count(*)          FROM bilhetes  WHERE {_FORA}
       AND criado_em > now() - interval '7 days')                                AS ultimos_7d
"""


async def metricas_publicas() -> dict:
    """Devolve os agregados públicos, servindo do cache quando ele está quente.

    Nunca levanta para o chamador: se o banco falhar, devolve o último valor bom
    (ou zeros). O contador da landing parado é um detalhe; a landing fora do ar
    por causa do contador é um problema.
    """
    global _cache, _cache_em

    agora = time.monotonic()
    if _cache is not None and (agora - _cache_em) < TTL_S:
        return _cache

    async with _lock:
        # Outro pedido pode ter renovado enquanto este esperava a trava.
        agora = time.monotonic()
        if _cache is not None and (agora - _cache_em) < TTL_S:
            return _cache
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                r = await conn.fetchrow(_SQL)
            _cache = {
                "apostas": r["apostas"] or 0,
                "casas": r["casas"] or 0,
                "contas": r["contas"] or 0,
                # Média diária da última semana, para a página poder dizer o
                # ritmo sem fingir tempo real que não temos.
                "por_dia": round((r["ultimos_7d"] or 0) / 7),
                "ttl": int(TTL_S),
            }
            _cache_em = time.monotonic()
        except Exception:                                    # noqa: BLE001
            logger.exception("metricas_publicas: consulta falhou")
            if _cache is None:
                _cache = {"apostas": 0, "casas": 0, "contas": 0,
                          "por_dia": 0, "ttl": int(TTL_S)}
    return _cache
