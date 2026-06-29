from pathlib import Path

# Raiz do Planilhador (um nível acima de app/)
ROOT = Path(__file__).resolve().parent.parent

GLOBAL_DIR = ROOT / "global"
CASAS_DIR  = ROOT / "casas"

# Trocar modelo é decisão humana — altere aqui e reinicie o servidor
DEFAULT_MODEL = "claude-sonnet-4-6"

# IDs válidos e atuais. Removido "claude-sonnet-4-5-20251001" (não existe:
# o snapshot real do Sonnet 4.5 é -20250929; -20251001 é a data do Haiku 4.5).
# Selecioná-lo causava 404 na API. O Sonnet 4.6 já cobre o caso do 4.5.
ALLOWED_MODELS = [
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
