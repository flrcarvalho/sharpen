from pathlib import Path
from config import CASAS_DIR, GLOBAL_DIR, GLOBAL_MASTERS

_file_cache: dict[Path, str] = {}


def _read(path: Path) -> str:
    if path not in _file_cache:
        _file_cache[path] = path.read_text(encoding="utf-8")
    return _file_cache[path]


def build_system(casa: str) -> list[dict]:
    """
    Monta 7 blocos de sistema com 2 breakpoints de cache:
      - Bloco 6 (último master global): caches os 6 masters para qualquer casa
      - Bloco 7 (arquivo da casa): cache adicional para chamadas da mesma casa
    """
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

    return blocks
