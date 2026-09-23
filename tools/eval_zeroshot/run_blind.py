"""Roda a categorização em MODO CEGO com o Sonnet de produção (forma (a) do README).

Carrega ANTHROPIC_API_KEY do .env da raiz (nunca imprime a chave), monta o system
com os 6 global/MASTER_*.md (SEM nenhum casas/CASA_*.md) e pede a categoria de cada
rótulo de labels_input.tsv. Escreve preds.tsv (indice <TAB> categoria).

    python tools/eval_zeroshot/run_blind.py
Depois: python tools/eval_zeroshot/pontuar.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "app"))
from config import GLOBAL_DIR, GLOBAL_MASTERS  # ordem canônica dos masters

# --- chave do .env, sem exibir ---
if not os.environ.get("ANTHROPIC_API_KEY"):
    for ln in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if ln.startswith("ANTHROPIC_API_KEY="):
            os.environ["ANTHROPIC_API_KEY"] = ln.split("=", 1)[1].strip()
            break
assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY ausente no .env"

import anthropic

# system = os 6 masters globais (modo cego: nenhuma casa)
system = [{"type": "text", "text": (GLOBAL_DIR / f).read_text(encoding="utf-8")}
          for f in GLOBAL_MASTERS]

SUFIXO = os.environ.get("EVAL_SUFIXO", "")
labels = (AQUI / f"labels_input{SUFIXO}.tsv").read_text(encoding="utf-8")
n = labels.count("\n") + 1

instrucao = (
    "Você é o motor de categorização do Planilhador em MODO CEGO (sem arquivo de "
    "tradução por casa). Para cada rótulo cru abaixo, decida a categoria canônica "
    "ÚNICA da lista oficial §3 do MASTER_APOSTAS (grafia exata). Se genuinamente "
    "ambíguo, use `Outros` (é o sinal de incerteza do sistema).\n"
    "O nome entre [ ] é só contexto de locale; categorize o rótulo.\n\n"
    f"Retorne SOMENTE {n} linhas `indice<TAB>categoria` (TAB real), índices 0..{n-1}, "
    "em ordem. Sem cabeçalho, sem texto extra.\n\n"
    "RÓTULOS:\n" + labels
)

# Modelo: `EVAL_MODEL` no ambiente, ou o Sonnet 4.6 que gravou o baseline de 2026-07-12.
# O default fica CRAVADO no 4.6 de propósito: `python run_blind.py` sem env reproduz a
# rodada registrada no README, e comparar baseline com baseline continua sendo de graça.
MODELO = os.environ.get("EVAL_MODEL", "claude-sonnet-4-6")

# ⚠️ **A bancada roda com THINKING DESLIGADO, e isso é o REGIME dela.** Medido na s384: o
# `run_blind.py` de julho nunca passou `thinking`, porque o modelo da época não pensava. O
# Sonnet 5 pensa por padrão, e `max_tokens` é o teto TOTAL — ele gastou 4000 (e depois
# 16000) inteiros raciocinando, devolveu `stop_reason=max_tokens` com `content=['thinking']`
# e **zero bloco de texto**. O filtro não achou linha nenhuma, o `pontuar.py` leu 282
# `<VAZIO>` e cuspiria **0% com 282 alucinações**. Subir o teto NÃO conserta: o pensamento
# adaptativo preenche o que houver.
#
# **Por que desligado e não `effort: low`:** o que se compara aqui são MODELOS na mesma
# tarefa. Com o 4.6 sem pensar e o 5 pensando, toda diferença de acerto fica inseparável de
# "um pensou e o outro não" — viram dois regimes, não dois modelos. Desligado é o único
# regime que os três aceitam igual (medido: Sonnet 4.6, Sonnet 5 e Opus 5, 282/282 linhas).
#
# ⚠️ **`temperature` NÃO é o caminho para determinismo:** foi REMOVIDO no Sonnet 5 e no Opus
# 5 (400 `invalid_request_error`), e só a geração anterior aceita. A dispersão desta bancada
# se MEDE com N amostras, não se elimina com um parâmetro. Ver o README.
THINKING = os.environ.get("EVAL_THINKING", "disabled")   # "disabled" | "adaptive"
# Com thinking desligado a resposta cabe em ~800 tokens; 4000 é folga, não trava.
MAX_TOKENS = int(os.environ.get("EVAL_MAX_TOKENS", "4000"))

kw = {}
if THINKING == "disabled":
    kw["thinking"] = {"type": "disabled"}
elif THINKING == "adaptive":
    kw["thinking"] = {"type": "adaptive"}
if os.environ.get("EVAL_TEMPERATURE"):    # só onde a API aceita (≤ Sonnet 4.6)
    kw["temperature"] = float(os.environ["EVAL_TEMPERATURE"])

# ⚠️ **Streaming é obrigatório acima de ~16k de saída, e por isso a bancada streama SEMPRE.**
# Medido na s384: com `EVAL_THINKING=adaptive` e teto de 32000, o SDK recusa antes de sair da
# máquina — `ValueError: Streaming is required for operations that may take longer than 10
# minutes`. A bancada de julho era `messages.create` puro, então ela **não conseguia medir um
# modelo que pensa**: ou o teto é baixo e o pensamento trunca a resposta, ou é alto e o SDK
# recusa. Um caminho só (`stream` + `get_final_message`) atende os dois regimes e devolve o
# mesmo objeto `Message` de antes.
client = anthropic.Anthropic()
with client.messages.stream(
    model=MODELO,
    max_tokens=MAX_TOKENS,
    system=system,
    messages=[{"role": "user", "content": instrucao}],
    **kw,
) as _s:
    resp = _s.get_final_message()
texto = "".join(b.text for b in resp.content if b.type == "text")
# mantém só linhas que começam com "indice<TAB>"
linhas = [l for l in texto.splitlines() if "\t" in l and l.split("\t", 1)[0].strip().isdigit()]
(AQUI / f"preds{SUFIXO}.tsv").write_text("\n".join(linhas) + "\n", encoding="utf-8")

# ⚠️ **O filtro acima DESCARTA em silêncio, e foi isso que escondeu o defeito do teto.**
# Com `content=['thinking']` ele guardava um arquivo vazio e ninguém via a diferença entre
# "o modelo errou tudo" e "o modelo não respondeu". O cru fica gravado ao lado para que a
# discordância entre o que veio e o que foi pontuado seja SEMPRE conferível (s384).
_descartadas = [l for l in texto.splitlines() if l.strip() and l not in linhas]
(AQUI / f"preds{SUFIXO}.raw.txt").write_text(
    f"# modelo={MODELO} thinking={THINKING} stop={resp.stop_reason} "
    f"blocos={[b.type for b in resp.content]}\n"
    f"# linhas aceitas={len(linhas)}/{n}  descartadas={len(_descartadas)}\n"
    f"# --- DESCARTADAS (o que o filtro jogou fora) ---\n"
    + "\n".join(_descartadas)
    + "\n# --- TEXTO CRU COMPLETO ---\n" + texto, encoding="utf-8")

u = resp.usage
# Preço pela tabela canônica do repo (`repository._PRECOS`), nunca por conta própria:
# modelo fora dela cai no `_PRECO_PADRAO` e o custo sai do modelo ERRADO, em silêncio.
from repository import custo_usd  # noqa: E402  (depende do sys.path montado acima)
tk = {"input": u.input_tokens, "output": u.output_tokens,
      "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
      "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0}
print(f"{MODELO} modo cego: {len(linhas)}/{n} predições -> preds{SUFIXO}.tsv | "
      f"tokens in={u.input_tokens} out={u.output_tokens} | "
      f"US$ {custo_usd(MODELO, tk):.4f}")
