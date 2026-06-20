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


def build_system(casa: str) -> list[dict]:
    """
    Monta 7 blocos de sistema com 2 breakpoints de cache:
      - Bloco 6 (último master global): cacheia os 6 masters para qualquer casa
      - Bloco 7 (arquivo da casa): cache adicional para chamadas da mesma casa
    """
    t0 = time.perf_counter()
    blocks: list[dict] = []
    last_global = len(GLOBAL_MASTERS) - 1

    for i, filename in enumerate(GLOBAL_MASTERS):
        block: dict = {"type": "text", "text": _read(GLOBAL_DIR / filename)}
        if i == last_global:
            block["cache_control"] = {"type": "ephemeral"}
        blocks.append(block)

    blocks.append({
        "type": "text",
        "text": _read(CASAS_DIR / f"CASA_{casa}.md"),
        "cache_control": {"type": "ephemeral"},
    })

    logger.info("build_system(%s): %.1fms", casa, (time.perf_counter() - t0) * 1000)
    return blocks
