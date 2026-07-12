"""Harness de regressão — pontua a categorização zero-shot.

Compara preds.tsv (saída do modelo em modo cego) contra pares.json (gabarito).
Emite acurácia + a lista de erros, separando erro silencioso de falha segura
(modelo respondeu `Outros` = sinal de incerteza, cairia no amarelo).

Uso:
    python tools/eval_zeroshot/pontuar.py
Requer, ao lado deste script: pares.json (de extrair_pares.py) e preds.tsv.
Grava RESULTADO.txt e imprime o resumo.
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]


def carregar_oficiais() -> set:
    """Lê a §3 (Tabela Oficial de Categorias) do MASTER_APOSTAS — fonte única.
    Evita que a lista do harness desatualize em relação ao master."""
    txt = (ROOT / "global" / "MASTER_APOSTAS_2026.md").read_text(encoding="utf-8")
    cats, dentro = set(), False
    for ln in txt.splitlines():
        if re.match(r"^#+\s*3\.\s", ln):
            dentro = True
            continue
        if dentro and re.match(r"^#+\s*4\.\s", ln):
            break
        if dentro and ln.strip().startswith("|"):
            c = ln.strip().strip("|").split("|")[0].strip()
            if c and c.lower() != "categoria" and not set(c) <= set("-: "):
                cats.add(c)
    return cats


# Categorias canônicas oficiais (§3). Predição fora daqui = alucinação de verdade.
OFICIAIS = carregar_oficiais()

def norm(cat: str) -> str:
    """Categoria nua: tira anotação entre parênteses e o marcador ⚠️.
    Ex.: 'Anytime (descr. - 2+ Gols)' -> 'Anytime'; 'Outros ⚠️ (nicho)' -> 'Outros'.
    O que importa é a CATEGORIA, não a anotação de descrição do §9."""
    return cat.split("(")[0].replace("⚠️", "").strip()


pares = json.loads((AQUI / "pares.json").read_text(encoding="utf-8"))
preds = {}
for ln in (AQUI / "preds.tsv").read_text(encoding="utf-8").splitlines():
    if "\t" in ln:
        i, cat = ln.split("\t", 1)
        preds[int(i)] = cat.strip()

acertos_cru = 0          # match exato de string (métrica objetiva, secundária)
acertos_cat = 0          # match de categoria normalizada (métrica-alvo)
erros, alucinacoes, seguras = [], [], []
for i, p in enumerate(pares):
    gold, pred = p["gold"], preds.get(i, "<VAZIO>")
    if pred == gold:
        acertos_cru += 1
    if norm(pred) == norm(gold):
        acertos_cat += 1
        continue
    erros.append((i, p["casa"], p["rotulo"], gold, pred))
    if norm(pred) not in OFICIAIS:
        alucinacoes.append(i)
    if norm(pred) == "Outros":       # modelo sinalizou incerteza -> não é silencioso
        seguras.append(i)

total = len(pares)
silenciosos = [e for e in erros if e[0] not in seguras]

L = [
    f"TOTAL: {total}",
    f"ACERTO de CATEGORIA (métrica-alvo): {acertos_cat} ({100*acertos_cat/total:.1f}%)",
    f"  match exato de string (cru): {acertos_cru} ({100*acertos_cru/total:.1f}%)",
    f"ERROS de categoria: {len(erros)} ({100*len(erros)/total:.1f}%)",
    f"  dos quais falhas SEGURAS (pred=Outros, cai no amarelo): {len(seguras)}",
    f"  dos quais erros SILENCIOSOS: {len(silenciosos)} ({100*len(silenciosos)/total:.1f}%)",
    f"  alucinações (fora da §3): {len(alucinacoes)}",
    "",
    "=== ERROS DE CATEGORIA ===",
]
for i, casa, rot, gold, pred in erros:
    tag = " [SEGURO]" if i in seguras else (" [ALUCINA]" if i in alucinacoes else "")
    L.append(f"  #{i:3d} [{casa}] {rot!r}  gold={gold!r} pred={pred!r}{tag}")

(AQUI / "RESULTADO.txt").write_text("\n".join(L), encoding="utf-8")
print(f"CATEGORIA {acertos_cat}/{total} = {100*acertos_cat/total:.1f}% "
      f"(cru {100*acertos_cru/total:.1f}%) | silenciosos {len(silenciosos)} | "
      f"seguras {len(seguras)} | alucina {len(alucinacoes)} -> RESULTADO.txt")
