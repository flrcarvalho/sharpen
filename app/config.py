from pathlib import Path

# Raiz do Planilhador (um nível acima de app/)
ROOT = Path(__file__).resolve().parent.parent

GLOBAL_DIR = ROOT / "global"
CASAS_DIR  = ROOT / "casas"

# Trocar modelo é decisão humana — altere aqui e reinicie o servidor
DEFAULT_MODEL = "claude-sonnet-4-6"

ALLOWED_MODELS = [
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6",
    "claude-opus-4-8",
]

# Ordem obrigatória dos masters no system prompt (blocos 1–6)
GLOBAL_MASTERS = [
    "MASTER_PIPELINE_2026.md",
    "MASTER_ESPORTES_2026.md",
    "MASTER_APOSTAS_2026.md",
    "MASTER_DESCRICAO_2026.md",
    "MASTER_RESULTADO_2026.md",
    "MASTER_OUTPUT_2026.md",  # breakpoint de cache aqui (bloco 6)
]
