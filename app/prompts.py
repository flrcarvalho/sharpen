import logging
import time
from pathlib import Path

from config import CASAS_DIR, GLOBAL_DIR, GLOBAL_MASTERS

logger = logging.getLogger("scanner")

# cache: Path -> (conteúdo, mtime); invalida automaticamente se o arquivo mudar
_file_cache: dict[Path, tuple[str, float]] = {}


def _read(path: Path) -> str:
    mtime = path.stat().st_mtime
    cached = _file_cache.get(path)
    if cached is None or cached[1] != mtime:
        _file_cache[path] = (path.read_text(encoding="utf-8"), mtime)
        logger.debug("cache miss: %s", path.name)
    return _file_cache[path][0]


def reload_masters() -> None:
    """Força releitura de todos os masters na próxima chamada."""
    _file_cache.clear()
    logger.info("cache de masters limpo")


# TTL do cache dos masters. Medido na s295: o prompt de sistema são 44.593 tokens de
# masters + 5k–11k do arquivo da casa, relidos UMA VEZ POR CHUNK — 46% da fatura da API
# era o manual sendo relido/regravado, não o bilhete.
#
# Por que 1h e não o padrão de 5 min: o intervalo entre extrações consecutivas, medido em
# 30 dias, é 61,2% abaixo de 5 min · 26,6% entre 5 min e 1 h · 12,1% acima de 1 h. Com TTL
# de 5 min, mais de um terço das chamadas chegava com o cache frio e pagava a escrita dos
# masters (44.593 × 1,25× a base). Com 1 h, 87,8% chegam quentes.
#
# A escrita a 1h custa 2× a base (contra 1,25× do 5m) — por isso `_PRECOS["cache_write"]`
# em `repository.py` foi ajustado junto. As duas coisas TÊM de andar juntas: TTL sem preço
# faz o log de custo mentir para baixo.
#
# A leitura RENOVA o prazo sem custo adicional ("The cache is refreshed for no additional
# cost each time the cached content is used" — docs oficiais), então o tráfego real mantém
# a entrada viva sozinho e o `_cache_warmer` só cobre os vãos longos.
_CACHE_TTL = {"type": "ephemeral", "ttl": "1h"}


def build_system(casa: str) -> list[dict]:
    """
    Monta 7 blocos de sistema com 2 breakpoints de cache (TTL de 1h, ver `_CACHE_TTL`):
      - Bloco 6 (último master global): cacheia os 6 masters para qualquer casa
      - Bloco 7 (arquivo da casa): cache adicional para chamadas da mesma casa
    """
    t0 = time.perf_counter()
    blocks: list[dict] = []
    last_global = len(GLOBAL_MASTERS) - 1

    for i, filename in enumerate(GLOBAL_MASTERS):
        block: dict = {"type": "text", "text": _read(GLOBAL_DIR / filename)}
        if i == last_global:
            block["cache_control"] = dict(_CACHE_TTL)
        blocks.append(block)

    casa_path = CASAS_DIR / f"CASA_{casa}.md"
    if casa_path.exists():
        blocks.append({
            "type": "text",
            "text": _read(casa_path),
            "cache_control": dict(_CACHE_TTL),
        })
        modo = "casa"
    else:
        # Modo cego (Fase 2 worldwide): casa sem manual → só os 6 masters globais.
        # A extração zero-shot mapeia os rótulos direto pela taxonomia (§3); o
        # breakpoint de cache do 6º master já cobre esse caso.
        modo = "cego"

    logger.info("build_system(%s): %s, %.1fms", casa, modo, (time.perf_counter() - t0) * 1000)
    return blocks
