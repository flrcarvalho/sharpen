"""Feed do Betting Dashboard a partir de uma planilha Google AO VIVO (Apps Script /exec).

Fase 1 do onboarding de um cliente: em vez de importar a base para o Postgres, o
dashboard lê a planilha dele em tempo real. O Apps Script (Code.gs) já devolve o
MESMO contrato de `repository.dashboard_rows` — menos o campo `operador`, que é
carimbado aqui. Assim, o `/dashboard/data` consolida sem enxergar a diferença
entre uma base do Postgres e uma planilha ao vivo.

Cache curto em memória (por dono) evita marretar o Apps Script a cada carga do
dashboard; o próprio Apps Script já reconstrói o cache dele a cada 30 min, então
alguns minutos de TTL aqui são inofensivos. Em falha de rede, servimos o último
feed conhecido (mesmo vencido) em vez de derrubar o dashboard.
"""
import logging
import time

import httpx

logger = logging.getLogger("planilha_viva")

# TTL do cache local (s). O Apps Script reconstrói a cada 30 min; 2 min basta
# para absorver recargas de página sem atrasar demais a atualização.
_TTL_SEGUNDOS = 120

# dono → (instante_monotonico, linhas)
_cache: dict[str, tuple[float, list[dict]]] = {}

# Normalização mínima de casa no feed ao vivo (Fase 1): a planilha do cliente usa
# rótulos próprios que divergem do canônico do dashboard (que casa ícone/domínio em
# `dash/data.js`). Sem isso, "365" apareceria como casa separada e sem ícone. A
# normalização completa (esporte/tipster/mercado) fica para o import da Fase 2.
# Chave comparada em minúsculas e sem espaços nas bordas.
_CASA_CANON: dict[str, str] = {
    "365": "Bet365",
}


def _norm_casa(casa: str) -> str:
    return _CASA_CANON.get((casa or "").strip().lower(), casa)


async def dashboard_rows_ao_vivo(dono: str, url: str, refresh: bool = False) -> list[dict]:
    """Busca o feed da planilha ao vivo do `dono` e carimba `operador=dono`.

    Usa cache local por TTL. Segue redirecionamento (o /exec do Apps Script
    faz 302 para googleusercontent.com). Em falha, cai no último feed em cache
    (stale) se houver; senão, propaga a exceção.

    Com `refresh=True` (clique manual em "Atualizar dados"): ignora o cache
    local de TTL e pede ao Apps Script uma RECONSTRUÇÃO AO VIVO (`?refresh=1`),
    em vez do cache do Drive (até 30 min velho). É o único caminho que faz o
    dado da planilha subir na hora — sem isso o botão "Atualizar" não fura os
    caches empilhados (120s local + Drive de 30 min).
    """
    agora = time.monotonic()
    em_cache = _cache.get(dono)
    if not refresh and em_cache and (agora - em_cache[0]) < _TTL_SEGUNDOS:
        return em_cache[1]

    fetch_url = url
    if refresh:
        fetch_url = url + ("&" if "?" in url else "?") + "refresh=1"

    try:
        # rebuildCache do Apps Script é mais lento que servir o cache do Drive;
        # dá mais folga no timeout quando forçamos refresh.
        timeout = 60.0 if refresh else 30.0
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(fetch_url)
            resp.raise_for_status()
            payload = resp.json()
        if not payload.get("ok"):
            raise ValueError(f"feed retornou ok=false: {payload.get('error')}")
        linhas = payload.get("data") or []
        for linha in linhas:
            linha["operador"] = dono
            linha["casa"] = _norm_casa(linha.get("casa", ""))
        _cache[dono] = (agora, linhas)
        return linhas
    except Exception as e:
        if em_cache:
            logger.warning(
                "planilha ao vivo de %s falhou (%s) — servindo feed em cache (stale)",
                dono, e,
            )
            return em_cache[1]
        logger.error("planilha ao vivo de %s falhou e não há cache: %s", dono, e)
        raise
