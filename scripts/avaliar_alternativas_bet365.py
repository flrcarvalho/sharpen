"""Avalia as alternativas de arquitetura da Bet365 PELA FONTE, sem gastar (s386).

Usa só o que já foi medido e gravado:
  • validação real (`_backups/validacao_contrato_s386/real_*`): caminho ATUAL e contrato
    Sonnet 5 enxuto sobre os mesmos 90 blocos (pares completos);
  • protótipo de 23/09 (`--prototipo`): respostas de 4 campos do Sonnet 5 (regime de
    produção), Sonnet 5 esforço baixo e Haiku 4.5, com o prompt enxuto, em 72 blocos Bet365
    (`--dados` traz o bloco cru e a decisão de produção deles);
  • o tradutor (`app/tradutor.py`), rodado agora sobre os mesmos blocos;
  • a decisão que a produção gravou (sombra) para cada bloco.
Todas passam pelo MESMO juiz (`juiz_fonte_bet365.julgar`). Números (código, data, stake,
odd, resultado, P/L) do contrato vêm do código e já foram conferidos contra o dinheiro do
texto na validação; aqui o foco é o SIGNIFICADO (esporte, categoria, descrição).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from collections import Counter, defaultdict

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import logging  # noqa: E402
logging.disable(logging.WARNING)
import contrato_texto as ct  # noqa: E402
import tradutor as trad  # noqa: E402
import juiz_fonte_bet365 as J  # noqa: E402

COD = re.compile(r"(?m)^\[Código:\s*([^\]\r\n]*?)\s*\]")


def _linhas_done(done):
    m = re.search(r"```tsv\n(.*?)\n```", (done or {}).get("resultado") or "", re.S)
    out = {}
    for l in (m.group(1) if m else "").splitlines():
        c = l.split("\t")
        if len(c) >= 11 and not l.startswith("Data\t"):
            out[c[10]] = c
    return out


def _resposta4(texto):
    out = {}
    for b in re.findall(r"```tsv\s*\n(.*?)```", texto or "", re.S) or [texto or ""]:
        for l in b.splitlines():
            c = [x.strip() for x in l.split("\t")]
            if len(c) == 4:
                out[c[0]] = c
    return out


def carregar(val_dir: pathlib.Path, prototipo: pathlib.Path, dados: pathlib.Path):
    """{conjunto: {codigo: {'bruto':..., 'alternativas': {nome: (esporte, aposta, desc)}}}}"""
    conj = {}
    # ── validação real
    par = json.loads((val_dir / "parametros.json").read_text(encoding="utf-8"))
    am = json.loads(pathlib.Path(par["amostra"]).read_text(encoding="utf-8"))
    blocos = {b["codigo"]: b for l in am["lotes"] for b in l["blocos"]}
    chamadas = [json.loads(l) for l in open(val_dir / "chamadas.jsonl", encoding="utf-8")]
    sem = {c["lote"] for c in chamadas if c.get("custo_e_reserva") and c["fase"] != "sombra"}
    V = {}
    for l in (json.loads(x) for x in open(val_dir / "lotes.jsonl", encoding="utf-8")):
        if l.get("interrompido") or not l.get("A_done") or not l.get("B_done") or l["lote"] in sem:
            continue
        la, lb = _linhas_done(l["A_done"]), _linhas_done(l["B_done"])
        for cod in l["cods"]:
            b = blocos[cod]
            alt = {}
            if cod in la:
                alt["atual (Sonnet 5, manual completo)"] = (la[cod][1], la[cod][5], la[cod][6])
            if cod in lb:
                alt["contrato Sonnet 5 enxuto"] = (lb[cod][1], lb[cod][5], lb[cod][6])
            pi = b.get("producao_ia") or {}
            alt["produção (decisão gravada)"] = (pi.get("esporte") or "", pi.get("aposta") or "",
                                                 pi.get("descricao") or "")
            V[cod] = {"bruto": b["bruto"], "alt": alt}
    conj["validacao_90"] = V
    # ── protótipo (Bet365)
    P = json.loads(prototipo.read_text(encoding="utf-8"))
    D = json.loads(dados.read_text(encoding="utf-8"))
    A = {x["sombra"]["codigo"]: x for x in D["A"]}
    nomes = {"s5 (como producao)": "contrato Sonnet 5 enxuto",
             "s5 effort low": "contrato Sonnet 5 enxuto, esforço baixo",
             "haiku-4-5": "contrato Haiku 4.5 enxuto"}
    Pr = {}
    for chave, nome in nomes.items():
        for s in P["saidas"][chave]:
            if s.get("casa") != "Bet365":
                continue
            for cod, c in _resposta4(s.get("saida", "")).items():
                if cod not in A:
                    continue
                d = Pr.setdefault(cod, {"bruto": A[cod]["sombra"]["bruto"], "alt": {}})
                d["alt"][nome] = (c[1], c[2], c[3])
    for cod, d in Pr.items():
        s = A[cod]["sombra"]
        d["alt"]["produção (decisão gravada)"] = (s["ia_esporte"] or "", s["ia_aposta"] or "",
                                                 s["ia_descricao"] or "")
    conj["prototipo_72"] = Pr
    # ── tradutor sobre TODOS os blocos
    for nome_c, C in conj.items():
        for cod, d in C.items():
            t = trad.traduzir("BET365", d["bruto"])
            d["tradutor"] = {"ok": t.ok, "motivo": t.motivo}
            if t.ok:
                d["alt"]["tradutor (só código)"] = (t.esporte, t.aposta, t.descricao)
    return conj


def ajustar(bruto, esporte, aposta):
    """Os ajustes ESTRUTURAIS que o contrato faz por código (MASTER), para julgar uma
    resposta crua de 4 campos como a arquitetura a gravaria."""
    lt = ct.ler_numeros("X", bruto)
    if trad._TIPO_MULTIPLA.match(lt.tipo or ""):
        esporte = "Múltiplos"
    if lt.n_pernas > 1 or lt.forma == "bet builder":
        aposta = "Múltipla"
    return esporte, aposta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validacao", required=True)
    ap.add_argument("--prototipo", required=True)
    ap.add_argument("--dados", required=True)
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    conj = carregar(pathlib.Path(a.validacao), pathlib.Path(a.prototipo), pathlib.Path(a.dados))
    resultado = {}
    erros = []
    for nome_c, C in conj.items():
        por_alt = defaultdict(Counter)
        cobertura = Counter()
        for cod, d in C.items():
            cobertura["blocos"] += 1
            cobertura["tradutor_resolve"] += d["tradutor"]["ok"]
            for alt, (esp, ap_, desc) in d["alt"].items():
                if alt.startswith("contrato"):
                    esp, ap_ = ajustar(d["bruto"], esp, ap_)
                r = J.julgar(d["bruto"], esp, ap_, desc)
                cls = Counter(x[0] for x in r["achados"])
                P = por_alt[alt]
                P["julgados"] += 1
                P["com_erro_real"] += bool(cls["erro_real"])
                P["com_forma"] += bool(cls["forma"])
                P["so_permitida"] += bool(cls["permitida"]) and not cls["erro_real"] and not cls["forma"]
                P["com_nao_verificavel"] += bool(cls["nao_verificavel"])
                P["limpo_verificado"] += not r["achados"]
                for x in r["achados"]:
                    if x[0] == "erro_real":
                        P["erro:" + re.sub(r":.*|\(.*|\d.*", "", x[1]).strip()] += 1
                        erros.append({"conjunto": nome_c, "alternativa": alt, "codigo": cod,
                                      "motivo": x[1], "esporte": esp, "aposta": ap_,
                                      "descricao": desc})
        resultado[nome_c] = {"cobertura": dict(cobertura),
                             "alternativas": {k: dict(v) for k, v in por_alt.items()}}
    pathlib.Path(a.saida).write_text(json.dumps({"resultado": resultado, "erros": erros},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    for nome_c, r in resultado.items():
        print(f"\n=== {nome_c}: {r['cobertura']}")
        print(f"   {'alternativa':42s} {'julg':>5s} {'erro real':>10s} {'forma':>6s} {'só perm.':>9s} {'ñ verif.':>9s}")
        for alt, v in sorted(r["alternativas"].items()):
            print(f"   {alt:42s} {v['julgados']:5d} {v['com_erro_real']:6d} ({100*v['com_erro_real']/v['julgados']:4.1f}%)"
                  f" {v['com_forma']:6d} {v['so_permitida']:9d} {v['com_nao_verificavel']:9d}")
    print("\nerros reais (para revisão):", len(erros), "->", a.saida)


if __name__ == "__main__":
    main()
