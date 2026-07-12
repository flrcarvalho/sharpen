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

labels = (AQUI / "labels_input.tsv").read_text(encoding="utf-8")
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

client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4000,
    system=system,
    messages=[{"role": "user", "content": instrucao}],
)
texto = "".join(b.text for b in resp.content if b.type == "text")
# mantém só linhas que começam com "indice<TAB>"
linhas = [l for l in texto.splitlines() if "\t" in l and l.split("\t", 1)[0].strip().isdigit()]
(AQUI / "preds.tsv").write_text("\n".join(linhas) + "\n", encoding="utf-8")

u = resp.usage
print(f"Sonnet 4.6 modo cego: {len(linhas)}/{n} predições -> preds.tsv | "
      f"tokens in={u.input_tokens} out={u.output_tokens}")
