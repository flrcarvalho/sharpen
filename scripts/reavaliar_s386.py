"""Reavaliação GRÁTIS das respostas gravadas no experimento s386, com o roteamento REAL.

ROTEAMENTO (o do contrato de texto, sem atalho):
  1. o leitor de números cobre o bloco?   não → caminho atual
  2. o tradutor resolve o significado?     sim → tradutor (custo zero)
  3. a resposta de 4 campos do Sonnet passa no portão (`aceitar_4campos`)? sim → Sonnet
  4. senão → caminho atual
  "Caminho atual": qualidade = a decisão que a PRODUÇÃO gravou para aquele mesmo bloco
  (sombra_rotulos); custo = US$ 0,0221/bloco MEDIDO na validação de 24/09 (Bet365). Isso é
  projeção de custo, e o relatório diz.

CENÁRIOS: "amostra como veio" (720 blocos, capturas de 01 a 24/09, metade com a data
estimada da extensão antiga) e "formato atual" (os 361 com `Data (evento)`/`(colocação)`,
que é 100% do que chegou de 21/09 em diante).

CLASSES por bloco (a pior vence): erro de significado > divergência de classificação
pendente de decisão > não verificável > verificado sem erro detectado. "Verificado sem
erro detectado" NÃO é taxa de acerto: é o que as checagens deste juiz não acusaram.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CUSTO_ATUAL = 0.0221
PENDENTE = ("categoria", "lacuna")                  # classes do juiz que são decisão pendente
_ESPORTE_2 = re.compile(r"^esporte '(Múltiplos|[^']+)', a casa diz '(Múltiplos|[^']+)'")


def _classe(achados, revisao, chave):
    rv = revisao.get(chave)
    erros = [m for c, m in achados if c == "erro_real"]
    pend = [m for c, m in achados if c in PENDENTE]
    # §2 (Múltiplos x esporte único): regra do MASTER em conflito com as correções do dono
    for m in list(erros):
        if _ESPORTE_2.match(m) and "Múltiplos" in m:
            erros.remove(m)
            pend.append(m)
    pend += [m for c, m in achados if c == "permitida" and "conflito" in m]
    if erros and rv in ("alarme_falso", "forma", "nao_verificavel", "artefato_corte"):
        erros = []
    if erros:
        return "erro de significado", erros, rv or "NÃO REVISADO"
    if pend:
        return "divergência pendente de decisão", pend, rv
    if any(c == "nao_verificavel" for c, _ in achados):
        return "não verificável", [m for c, m in achados if c == "nao_verificavel"], rv
    return "verificado sem erro detectado", [], rv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", required=True)
    ap.add_argument("--amostra", required=True)
    ap.add_argument("--rodada", default="R3", help="respostas de 4 campos do Sonnet a usar")
    ap.add_argument("--saida")
    a = ap.parse_args()
    import logging
    logging.disable(logging.WARNING)
    import contrato_texto as ct
    import taxonomia
    import tradutor as trad
    import juiz_fonte_bet365 as J
    pasta = pathlib.Path(a.pasta)
    corpo = json.loads(pathlib.Path(a.amostra).read_text(encoding="utf-8"))
    blocos = [b for g in corpo["grupos"] for b in g["blocos"]]
    rod = json.loads((pasta / "rodadas.json").read_text(encoding="utf-8"))
    rp = pasta / "revisao.json"
    revisao = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else {}
    cham = [json.loads(l) for l in open(pasta / "chamadas.jsonl", encoding="utf-8")]
    custo_lote = {c["lote"]: c["custo"] for c in cham if c.get("consumo")}
    dec, custo_bloco = {}, {}
    for l in rod["rodadas"].get(a.rodada, []):
        k = f"{a.rodada}:{l['i']}"
        for c in l["cods"]:
            custo_bloco[c] = custo_lote.get(k, 0.0) / len(l["cods"])
        dec.update(l["decisoes"])
    esp, cat = set(taxonomia.esportes_canonicos()), set(taxonomia.categorias_canonicas())

    linhas = []
    for atualizada in (False, True):
      for b in blocos:
          c, bruto = b["codigo"], b["bruto"]
          novo = bool(re.search(r"(?m)^Data \((evento|coloca)", bruto))
          lt = ct.ler_numeros(c, bruto)
          custo, etapa, saida = 0.0, None, None
          # CENÁRIO "extensões atualizadas": a extensão nova publica a data; o SIGNIFICADO
          # não depende dela. Para rotear, o bloco antigo é tratado como coberto, e o
          # tradutor lê a linha de data estimada como se fosse a publicada — a data NÃO
          # entra em nada que é julgado ou gravado aqui. Bloco SEM data nenhuma não ganha
          # data: se o tradutor recusar por isso, vai para o Sonnet (conservador).
          bruto_t = bruto
          if atualizada and not novo:
              bruto_t = bruto.replace("Data (encerramento)", "Data (evento)")
          if lt.rota != "coberto" and not (atualizada and not novo):
              etapa = "caminho atual (sem leitura de número)"
          else:
              t = trad.traduzir("BET365", bruto_t)
              if t.ok:
                  etapa, saida = "tradutor", (t.esporte, t.aposta, t.descricao)
              else:
                  custo += custo_bloco.get(c, 0.0)
                  d = dec.get(c)
                  if d and d.get("cru"):
                      e2, a2, _aj, mot = ct.aceitar_4campos(lt, *d["cru"], esp, cat)
                      if not mot:
                          etapa, saida = "Sonnet", (e2, a2, d["cru"][2])
                  if etapa is None:
                      etapa = "caminho atual (recusado/sem linha)"
          if saida is None:
              ia = b["producao_ia"]
              saida = (ia["esporte"] or "", ia["aposta"] or "", ia["descricao"] or "")
              custo += CUSTO_ATUAL
          r = J.julgar(bruto, *saida)
          chave = "|".join([c, *saida])
          cls, motivos, rv = _classe(r["achados"], revisao, chave)
          linhas.append({"codigo": c, "novo": novo, "etapa": etapa, "saida": saida, "classe": cls,
                         "motivos": motivos, "revisao": rv, "custo": custo,
                         "atual_projetado": "caminho atual" in etapa, "atualizada": atualizada})

    out = {}
    for nome, filtro in (("A. amostra como veio (720)", lambda x: not x["atualizada"]),
                         ("B. só o formato atual (361, outros donos)", lambda x: x["novo"] and not x["atualizada"]),
                         ("C. os 720 com a extensão atualizada", lambda x: x["atualizada"])):
        ls = [x for x in linhas if filtro(x)]
        n = len(ls)
        med = sum(x["custo"] - (CUSTO_ATUAL if x["atual_projetado"] else 0) for x in ls)
        proj = sum(CUSTO_ATUAL for x in ls if x["atual_projetado"])
        cls = Counter(x["classe"] for x in ls)
        out[nome] = {"blocos": n, "etapas": dict(Counter(x["etapa"] for x in ls)),
                     "classes": dict(cls),
                     "custo_medido_usd": med, "custo_atual_projetado_usd": proj,
                     "usd_por_bloco": (med + proj) / n,
                     "nao_revisados": sum(1 for x in ls if x["revisao"] == "NÃO REVISADO"),
                     "erros_por_etapa": dict(Counter(x["etapa"] for x in ls if x["classe"] == "erro de significado"))}
        print(f"\n=== {nome}: {n} blocos")
        print("   etapas:", out[nome]["etapas"])
        for k in ("erro de significado", "divergência pendente de decisão", "não verificável",
                  "verificado sem erro detectado"):
            print(f"   {k:34s} {cls.get(k, 0):4d}  ({100 * cls.get(k, 0) / n:4.1f}%)")
        print(f"   erros por etapa: {out[nome]['erros_por_etapa']} · não revisados: {out[nome]['nao_revisados']}")
        print(f"   custo: medido US$ {med:.3f} + caminho atual projetado US$ {proj:.3f} "
              f"= US$ {(med + proj) / n:.5f}/bloco")
    if a.saida:
        pathlib.Path(a.saida).write_text(json.dumps({"cenarios": out, "linhas": linhas},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
