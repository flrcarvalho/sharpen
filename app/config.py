from pathlib import Path

# Raiz do Planilhador (um nível acima de app/)
ROOT = Path(__file__).resolve().parent.parent

GLOBAL_DIR = ROOT / "global"
CASAS_DIR  = ROOT / "casas"

# Trocar modelo é decisão humana — altere aqui e reinicie o servidor.
#
# s377 (20/09/2026): Sonnet 4.6 → Sonnet 5, decisão do Feca, por medição própria.
# O 4.6 é geração ANTERIOR e custa 1,5x o atual da mesma linha (3/15 contra 2/10):
# ficar nele custou **R$ 1.496 medidos** desde julho, a R$ 761/mês no ritmo atual.
# Não foi só preço — o Sonnet 5 ganhou em tudo que deu para medir, sobre blocos
# REAIS da `sombra_rotulos` com os verificadores determinísticos do próprio repo:
#
#   descrição fora do MASTER   13,9% → 0,0%   (253 blocos, 10 casas)
#   código inventado                1 → 0     (600 blocos, Bet365+Betano)
#   coluna comida em aberta         3 → 0     (84 blocos, todos abertos)
#   stake / resultado errados       1 → 0     em cada
#
# Haiku 4.5 vetado por decisão do Feca (jun/2026), testado no pipeline
# de print+texto daquela data. Veto segue valendo por padrão.
# Os números 8,7% / 19 códigos em 253 blocos que já estiveram aqui vieram
# de bancada defeituosa (s378) e não sustentam nada.
# O pipeline mudou desde jun/2026. Para reabrir, rodar
# tools/eval_zeroshot/ CEGO, sem informar o veto ao avaliador.
DEFAULT_MODEL = "claude-sonnet-5"

# IDs válidos e atuais. Removido "claude-sonnet-4-5-20251001" (não existe:
# o snapshot real do Sonnet 4.5 é -20250929; -20251001 é a data do Haiku 4.5).
# Selecioná-lo causava 404 na API.
#
# ⚠️ **Todo ID aqui PRECISA de linha em `repository._PRECOS`.** Sem ela o cálculo cai
# no `_PRECO_PADRAO` e o `uso_tokens` passa a registrar o preço do modelo ERRADO — a
# economia da troca simplesmente não apareceria, e a conclusão seria "não adiantou".
# Gate: `tests/test_modelo_e_preco.py`.
ALLOWED_MODELS = [
    "claude-sonnet-5",
    "claude-opus-5",
]

# Data da última revisão humana da escolha de modelo.
#
# ⚠️ **Isto é um prazo de validade, não um carimbo.** O `test_a_escolha_de_modelo_tem_validade`
# quebra o CI 90 dias depois desta data. Existe porque o defeito que ele previne já
# aconteceu: a lista acima foi curada quando o Sonnet 4.6 era o atual e ninguém voltou
# nela, então rodamos meses na geração anterior pagando 50% a mais.
#
# É a mesma família de "assinatura tem ERA" e "casa dedicada é retrato datado": decisão
# certa na data, congelada, nunca remedida. Ao revisar, conferir os IDs e os preços
# contra a tabela oficial (o endpoint `GET /v1/models` lista o que existe) e mover a data.
MODELO_REVISADO_EM = "2026-09-20"
MODELO_VALIDADE_DIAS = 90

# Ordem obrigatória dos masters no system prompt (blocos 1–6)
GLOBAL_MASTERS = [
    "MASTER_PIPELINE_2026.md",
    "MASTER_ESPORTES_2026.md",
    "MASTER_APOSTAS_2026.md",
    "MASTER_DESCRICAO_2026.md",
    "MASTER_RESULTADO_2026.md",
    "MASTER_OUTPUT_2026.md",  # breakpoint de cache aqui (bloco 6)
]
