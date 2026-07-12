"""Harness de regressão — extração zero-shot (modo cego).

Extrai pares (casa, rótulo_cru -> categoria_global) do §9 "Mapa de mercados"
de cada casas/CASA_*.md. Esses pares são o gabarito da avaliação: mede quanto
o modelo acerta a categoria SEM ver o arquivo de tradução da casa.

Uso:
    python tools/eval_zeroshot/extrair_pares.py
Gera, ao lado deste script:
    - pares.json        (gabarito: [{casa, rotulo, gold}, ...])
    - labels_input.tsv  (entrada p/ o modelo: `indice <TAB> [CASA] <TAB> rotulo`)

Depois: rodar um modelo sobre labels_input.tsv em MODO CEGO (só os
global/MASTER_*.md, proibido abrir casas/), salvar a saída como preds.tsv
(`indice <TAB> categoria`) e rodar pontuar.py.

Contexto e resultado da 1ª rodada: docs/PLANO_EXTRACAO_WORLDWIDE.md §6.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASAS = ROOT / "casas"
AQUI = Path(__file__).resolve().parent

RE_SEC9 = re.compile(r"^##\s*9\.\s", re.I)      # início da §9
RE_ANY_H2 = re.compile(r"^##\s")                 # qualquer ## (fim da §9)

pares = []
por_casa = {}

for f in sorted(CASAS.glob("CASA_*.md")):
    if f.stem == "CASA_MODELO":
        continue
    dentro = False
    casa = f.stem.replace("CASA_", "")
    n = 0
    for ln in f.read_text(encoding="utf-8").splitlines():
        if RE_SEC9.match(ln):
            dentro = True
            continue
        if dentro and RE_ANY_H2.match(ln) and not RE_SEC9.match(ln):
            dentro = False
            continue
        if not dentro:
            continue
        # linha de tabela markdown: | a | b |
        if ln.strip().startswith("|") and ln.count("|") >= 3:
            cols = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cols) < 2:
                continue
            esq, dir_ = cols[0], cols[1]
            if not esq or set(esq) <= set("-: "):          # separador ---
                continue
            if "exibe" in esq.lower():                      # header
                continue
            if dir_.lower() in ("aposta global", "global", "categoria"):
                continue
            esq = esq.replace("`", "").replace("**", "").strip()
            dir_ = dir_.replace("`", "").replace("**", "").strip()
            if not dir_ or len(dir_) > 40 or "→" in dir_:   # nota, não categoria
                continue
            if len(esq) > 70:                                # rótulo virou nota
                continue
            pares.append({"casa": casa, "rotulo": esq, "gold": dir_})
            n += 1
    por_casa[casa] = n

(AQUI / "pares.json").write_text(
    json.dumps(pares, ensure_ascii=False, indent=2), encoding="utf-8"
)

labels = [f"{i}\t[{p['casa']}]\t{p['rotulo']}" for i, p in enumerate(pares)]
(AQUI / "labels_input.tsv").write_text("\n".join(labels), encoding="utf-8")

# resumo ASCII-safe (Windows console pode ser cp1252)
print(f"TOTAL de pares: {len(pares)}")
print("Por casa:", {c: n for c, n in sorted(por_casa.items(), key=lambda x: -x[1])})
print("Categorias-gold distintas:", len(Counter(p["gold"] for p in pares)))
print("Gerados: pares.json, labels_input.tsv")
