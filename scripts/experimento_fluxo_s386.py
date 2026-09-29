"""Validação do FLUXO COMPLETO, Sonnet COM x SEM pensamento (s386, 24/09). PAGO.

Por grupo real de captura, os dois braços na MESMA ordem alternada:
  1. tradutor (código, custo zero) resolve o que sabe;
  2. o resto vai ao `/extrair` REAL, com o contrato de texto LIGADO: leitor de números,
     4 campos pelo Sonnet (lotes de 6, max_tokens 64.000 e continuação, como a produção),
     portão `aceitar_4campos`, e os recusados pelo CAMINHO ATUAL de verdade (repescagem,
     fidelidade, correções). Nada de custo projetado aqui: toda chamada é medida.
A ÚNICA diferença entre os braços: `main._CONTRATO_KW` = {} (produção: o Sonnet 5 pensa por
padrão) ou {"thinking": {"type": "disabled"}}. O caminho atual fica igual nos dois.

Os blocos são NOVOS (nenhum dos 942 usados para ajustar regra ou juiz) e do formato atual.
O teto é garantido pelo `_Medidor` (reserva por bytes + max_tokens); uma chamada que não
cabe ESPERA as reservas em andamento, e só é orçamento esgotado sem nada em andamento.

COMANDOS: executar | simular | relatar
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from experimento_s386 import SAIDA, carregar, _cp, _veredito, _boot_dif  # noqa: E402

BRACOS = {"com_pensamento": {}, "sem_pensamento": {"thinking": {"type": "disabled"}}}
CRITERIOS = {
    "pergunta": "desligar o pensamento do Sonnet no contrato de 4 campos mantém a qualidade "
                "do FLUXO COMPLETO e quanto economiza, medido",
    "metrica_qualidade": "blocos com erro de SIGNIFICADO confirmado à mão contra o texto; "
                         "divergência de classificação pendente e não verificável relatados à parte",
    "decisao": "sem pensamento é ACEITÁVEL se a diferença pareada de erro (sem − com) tiver teto "
               "de 95% <= 1 p.p. no fluxo inteiro; INACEITÁVEL se o piso > 1 p.p.; senão "
               "INCONCLUSIVO (amostra insuficiente, nunca reprovação)",
    "barras": [0.01, 0.02, 0.05],
    "economia": "custo MEDIDO de cada braço (contrato + caminho atual que ele acionou), sem projeção",
    "paradas": ["orçamento (teto garantido)", "garantia do medidor violada",
                "erro de API em 3 grupos seguidos"],
    "falso_negativo": "30 blocos 'sem erro detectado' sorteados por braço, revisados contra o texto",
}


def _medidor_que_espera(base_cls):
    class _Espera(base_cls):
        """Não recusa por reserva EM ANDAMENTO: espera ela voltar. Só recusa (e para) quando
        não cabe e não há nada no ar — aí o orçamento acabou de verdade."""
        def stream(self, **kw):
            fora = self

            class _W:
                async def __aenter__(s):
                    mx = min(kw.get("max_tokens", fora.max_saida), fora.max_saida)
                    _, reserva = fora._limite(kw["model"], kw.get("system"), kw["messages"], mx)
                    while True:
                        with fora.lock:
                            cabe = fora.gasto + fora.reservado + reserva <= fora.teto - fora.margem
                            andando = fora.em_andamento
                        if cabe or not andando:
                            break
                        await asyncio.sleep(1.0)
                    s.dentro = base_cls.stream(fora, **kw)
                    return await s.dentro.__aenter__()

                async def __aexit__(s, *a):
                    return await s.dentro.__aexit__(*a)
            return _W()
    return _Espera


def executar(amostra: pathlib.Path, teto: float, margem: float, simular: bool):
    corpo = carregar(amostra)
    pasta = SAIDA / (("sim_" if simular else "") + "fluxo_" + corpo["manifesto"][:12])
    trava = pasta / "INICIADA"
    if trava.exists():
        raise SystemExit(f"Já executado ({pasta}). Não repito: use `relatar`.")
    pasta.mkdir(parents=True, exist_ok=True)
    trava.write_text(datetime.now().isoformat(), encoding="utf-8")
    (pasta / "criterios.json").write_text(json.dumps(
        {"criterios": CRITERIOS, "teto": teto, "margem": margem, "simulada": simular,
         "amostra": str(amostra), "registrado_em": datetime.now().isoformat()},
        ensure_ascii=False, indent=1), encoding="utf-8")
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("DATABASE_PUBLIC_URL", None)
    os.environ.setdefault("SESSION_SECRET", "validacao-local-s386")
    os.environ["CONTRATO_TEXTO_CASAS"] = "BET365"
    import logging
    import main
    import tradutor as trad
    import validar_contrato_bet365 as V
    logging.disable(logging.INFO)
    if simular:
        cliente = V._IAFalsa({"lotes": [{"blocos": g["blocos"]} for g in corpo["grupos"]]}, {})
    else:
        from anthropic import AsyncAnthropic
        cliente = AsyncAnthropic()
    med = _medidor_que_espera(V._Medidor)(cliente, teto, margem, 64000, pasta)
    main._client = med
    main._MAX_CONCURRENT = 3

    async def _nada(*a, **k):
        return None

    async def _dedup(texto, *a, **k):
        return texto, 0
    main.registrar_uso = _nada
    main.registrar_sombra = _nada
    main._barreira_lembrar = _nada
    main.registrar_sombra_modelo = _nada
    main._sombra_vale_agora = lambda: False           # sem sombra: só o que se mede
    main._dedup_superbet_text = _dedup
    main.app.dependency_overrides[main.usuario_atual] = lambda: "Validacao"
    import socket
    import httpx
    import uvicorn
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        porta = sk.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=porta,
                                        log_level="warning", lifespan="off"))
    th = threading.Thread(target=srv.run, daemon=True)
    th.start()
    while not srv.started:
        time.sleep(0.1)

    def _extrair(texto):
        r = httpx.post(f"http://127.0.0.1:{porta}/extrair",
                       data={"casa": "Bet365", "parceiro": "Conta Validacao", "texto": texto},
                       timeout=3600)
        evs = [json.loads(l[6:]) for l in r.text.split("\n") if l.startswith("data: ")]
        return (next((e for e in evs if e.get("done")), None),
                next((e.get("error") for e in evs if e.get("error")), None))

    arq = open(pasta / "grupos.jsonl", "a", encoding="utf-8")
    parada, erros_seguidos = None, 0
    try:
        for gi, g in enumerate(corpo["grupos"]):
            trad_ok = {b["codigo"]: trad.traduzir("BET365", b["bruto"]) for b in g["blocos"]}
            resto = [b for b in g["blocos"] if not trad_ok[b["codigo"]].ok]
            reg = {"grupo": gi, "cods": [b["codigo"] for b in g["blocos"]],
                   "tradutor": {c: [t.esporte, t.aposta, t.descricao] for c, t in trad_ok.items() if t.ok},
                   "resto": [b["codigo"] for b in resto]}
            if resto:
                texto = "\n\n".join(f"[Código: {b['codigo']}]\n{b['bruto']}" for b in resto)
                ordem = list(BRACOS) if gi % 2 == 0 else list(BRACOS)[::-1]
                erro_grupo = False
                for braco in ordem:
                    main._CONTRATO_KW = BRACOS[braco]
                    med.lote, med.lado = f"{braco}:{gi}", braco
                    v0 = len(med.violacoes)
                    done, erro = _extrair(texto)
                    reg[braco] = {"done": done, "erro": erro}
                    erro_grupo |= bool(erro) or done is None
                    if len(med.violacoes) > v0:
                        parada = "garantia do medidor violada"
                    if med.gasto + 0.5 > med.teto - med.margem and med.em_andamento == 0 and erro:
                        parada = parada or f"orçamento: {erro}"
                main._CONTRATO_KW = {}
                erros_seguidos = erros_seguidos + 1 if erro_grupo else 0
                if erros_seguidos >= 3:
                    parada = parada or "erro em 3 grupos seguidos"
            arq.write(json.dumps(reg, ensure_ascii=False, default=str) + "\n")
            arq.flush()
            print(f"grupo {gi + 1}/{len(corpo['grupos'])} · resto {len(resto)} · gasto US$ {med.gasto:.4f}"
                  f" · pico {med.pico:.4f}", flush=True)
            if parada:
                print("PARADA:", parada, flush=True)
                break
    finally:
        t0 = time.time()
        while med.em_andamento and time.time() - t0 < 600:
            time.sleep(1)
        srv.should_exit = True
        th.join(15)
        arq.close()
        (pasta / "fim.json").write_text(json.dumps(
            {"gasto": med.gasto, "pico": med.pico, "violacoes": med.violacoes,
             "recusas": med.recusas, "parada": parada}, indent=1), encoding="utf-8")
        med.arq.close()
    print("pasta:", pasta)


def relatar(pasta: pathlib.Path, portao_atual: bool = False):
    import logging
    logging.disable(logging.WARNING)
    import contrato_texto as ct
    import taxonomia
    import juiz_fonte_bet365 as J
    from reavaliar_s386 import _classe
    crit = json.loads((pasta / "criterios.json").read_text(encoding="utf-8"))
    corpo = json.loads(pathlib.Path(crit["amostra"]).read_text(encoding="utf-8"))
    blocos = {b["codigo"]: b for g in corpo["grupos"] for b in g["blocos"]}
    grupos = [json.loads(l) for l in open(pasta / "grupos.jsonl", encoding="utf-8")]
    cham = [json.loads(l) for l in open(pasta / "chamadas.jsonl", encoding="utf-8")]
    rp = pasta / "revisao.json"
    revisao = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else {}
    esp, cat = set(taxonomia.esportes_canonicos()), set(taxonomia.categorias_canonicas())
    custo = defaultdict(lambda: defaultdict(float))
    ncham = defaultdict(Counter)
    resp4 = defaultdict(str)
    for c in cham:
        if c.get("recusada"):
            continue
        braco = str(c["lote"]).split(":")[0]
        fase = "contrato" if c["fase"] == "B_contrato" else "caminho atual"
        custo[braco][fase] += c.get("custo", 0.0)
        ncham[braco][fase] += 1
        ncham[braco]["sem consumo"] += bool(c.get("custo_e_reserva"))
        if fase == "contrato":
            resp4[c["lote"]] += "\n" + (c.get("resposta_texto") or "")
    fim = {b: {} for b in BRACOS}
    grupos_ok = [g for g in grupos if all(g.get(b, {}).get("done") for b in BRACOS) or not g["resto"]]
    for g in grupos_ok:
        for braco in BRACOS:
            for c, s in g["tradutor"].items():
                fim[braco][c] = ("tradutor", tuple(s))
            if not g["resto"]:
                continue
            done = g[braco]["done"]
            m = re.search(r"```tsv\n(.*?)\n```", done.get("resultado") or "", re.S)
            final = {}
            for l in (m.group(1) if m else "").splitlines():
                cols = l.split("\t")
                if len(cols) >= 11:
                    final[cols[10]] = (cols[1], cols[5], cols[6])
            aceitos = set()
            linhas = defaultdict(list)
            for l in ct._linhas_resposta(resp4[f"{braco}:{g['grupo']}"]):
                cols = [x.strip() for x in l.split("\t")]
                if len(cols) == 4:
                    linhas[cols[0]].append(cols)
            for c in g["resto"]:
                saida4 = None
                if len(linhas.get(c, [])) == 1:
                    lt = ct.ler_numeros(c, blocos[c]["bruto"])
                    e2, a2, aj, mot = ct.aceitar_4campos(lt, *linhas[c][0][1:], esp, cat)
                    if lt.rota == "coberto" and not mot:
                        aceitos.add(c)
                        d2 = next((x[2] for x in aj if x[0] == "descricao"), linhas[c][0][3])
                        saida4 = (e2, a2, d2)
                # PROJEÇÃO (--portao-atual): o que o portão ATUAL aceita usa a resposta de 4
                # campos gravada; o resto, o resultado REAL do caminho atual daquele braço
                if portao_atual and c in aceitos:
                    fim[braco][c] = ("Sonnet (4 campos)", saida4)
                else:
                    fim[braco][c] = (("Sonnet (4 campos)" if c in aceitos else "caminho atual"),
                                     final.get(c))
    n_bl = len(fim["com_pensamento"])
    out = {"blocos_avaliados": n_bl, "grupos_completos": len(grupos_ok), "grupos": len(grupos),
           "bracos": {}, "comparacao": {}}
    classe = {b: {} for b in BRACOS}
    pend = {}
    for braco in BRACOS:
        cls, etapas, sem_linha = Counter(), Counter(), 0
        for c, (et, s) in fim[braco].items():
            etapas[et] += 1
            if s is None:
                sem_linha += 1
                classe[braco][c] = "erro de significado"   # bilhete PERDIDO no fluxo
                cls["erro de significado"] += 1
                pend.setdefault(f"{c}|PERDIDO", {"bracos": [], "motivos": ["sem linha no done"]})["bracos"].append(braco)
                continue
            r = J.julgar(blocos[c]["bruto"], *s)
            chave = "|".join([c, *s])
            k, motivos, rv = _classe(r["achados"], revisao, chave)
            classe[braco][c] = k
            cls[k] += 1
            if k == "erro de significado":
                pend.setdefault(chave, {"bracos": [], "motivos": motivos, "revisao": rv,
                                        "etapa": et, "fonte": [l.strip() for l in blocos[c]["bruto"].splitlines()
                                                               if l.strip()[:1] in "•–"]})["bracos"].append(braco)
        k = cls["erro de significado"]
        tot = custo[braco]["contrato"] + custo[braco]["caminho atual"]
        if portao_atual:
            # retorno evitado: sai o custo MÉDIO medido por bloco de retorno deste braço
            med_ret = [g for g in grupos_ok if g["resto"]]
            n_ret_medido = sum((g[braco]["done"].get("contrato") or {}).get("rejeitados_depois", 0)
                               + (g[braco]["done"].get("contrato") or {}).get("encaminhados_antes", 0)
                               for g in med_ret)
            n_ret_agora = etapas["caminho atual"]
            por_bloco = custo[braco]["caminho atual"] / max(1, n_ret_medido)
            tot = custo[braco]["contrato"] + por_bloco * n_ret_agora
        out["bracos"][braco] = {
            "etapas": dict(etapas), "classes": dict(cls), "blocos_sem_linha": sem_linha,
            "erro_significado": k, "taxa": k / n_bl, "ic95": _cp(k, n_bl),
            "veredito": {str(b): _veredito(k, n_bl, b) for b in CRITERIOS["barras"]},
            "custo_contrato_usd": custo[braco]["contrato"], "custo_caminho_atual_usd": custo[braco]["caminho atual"],
            "chamadas": dict(ncham[braco]), "usd_por_bloco": tot / n_bl}
    pares = [int(classe["sem_pensamento"][c] == "erro de significado") -
             int(classe["com_pensamento"][c] == "erro de significado") for c in classe["com_pensamento"]]
    dif, lo, hi = _boot_dif(pares)
    out["comparacao"] = {"dif_pareada_sem_menos_com": dif, "ic95": [lo, hi],
                         "veredito": ("ACEITÁVEL" if hi <= 0.01 else "INACEITÁVEL" if lo > 0.01 else "INCONCLUSIVO"),
                         "economia_medida_usd_por_bloco": out["bracos"]["com_pensamento"]["usd_por_bloco"]
                         - out["bracos"]["sem_pensamento"]["usd_por_bloco"]}
    suf = "_portao_atual" if portao_atual else ""
    (pasta / f"achados_para_revisao{suf}.json").write_text(json.dumps(pend, ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / f"relatorio{suf}.json").write_text(json.dumps(
        {**out, "_fim": {b: {c: [v[0], list(v[1]) if v[1] else None, classe[b][c]] for c, v in fim[b].items()}
                         for b in BRACOS}}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"blocos {n_bl} · grupos completos {len(grupos_ok)}/{len(grupos)}")
    for b, v in out["bracos"].items():
        lo_, hi_ = v["ic95"]
        print(f"\n{b}: etapas {v['etapas']} · chamadas {v['chamadas']}\n   classes {v['classes']}\n"
              f"   erro de significado {v['erro_significado']}/{n_bl} = {100 * v['taxa']:.1f}% "
              f"[IC95 {100 * lo_:.1f}–{100 * hi_:.1f}] {v['veredito']}\n   US$ contrato {v['custo_contrato_usd']:.4f}"
              f" + caminho atual {v['custo_caminho_atual_usd']:.4f} = {v['usd_por_bloco']:.5f}/bloco")
    print("\ncomparação:", out["comparacao"])
    print("achados de erro para revisão:", len(pend))


def main_cli():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    rl = sub.add_parser("relatar")
    rl.add_argument("--pasta", required=True)
    rl.add_argument("--portao-atual", action="store_true",
                    help="PROJEÇÃO: reaplica o portão atual às respostas gravadas")
    for nome in ("executar", "simular"):
        e = sub.add_parser(nome)
        e.add_argument("--amostra", required=True)
        e.add_argument("--teto", type=float, required=True)
        e.add_argument("--margem", type=float, default=0.25)
    a = ap.parse_args()
    if a.cmd == "relatar":
        relatar(pathlib.Path(a.pasta), a.portao_atual)
    else:
        executar(pathlib.Path(a.amostra), a.teto, a.margem, a.cmd == "simular")


if __name__ == "__main__":
    main_cli()
