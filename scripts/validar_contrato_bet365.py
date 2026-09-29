"""Validação REAL do contrato de 4 campos (Bet365): caminho ATUAL x caminho NOVO sobre os
MESMOS blocos, congelados. s386. Produção continua desligada: este script nunca liga nada
no ar e nunca escreve no banco de produção.

COMANDOS

  congelar   grátis, SÓ LEITURA no banco de produção. Lotes REAIS (blocos consecutivos de
             uma mesma extração), com hash por bloco e manifesto sha256 do conjunto.
  executar   PAGO. Confere os hashes; cada lote passa pelo `/extrair` REAL duas vezes,
             DESLIGADO (caminho atual, "A") e LIGADO (contrato + encaminhados + sombra, "B"),
             em ordem alternada. `DATABASE_URL` é apagado antes de tudo. Roda UMA vez por
             amostra: a pasta da execução é a trava.
  simular    grátis: o MESMO harness com IA falsa, inclusive falhas programadas.
  relatar    grátis: refaz o relatório SÓ a partir do que a execução gravou.

GARANTIA DO TETO (não é estimativa):
  • ENTRADA: o tokenizador é de bytes — todo token cobre >= 1 byte do texto. Então os
    tokens de entrada cobrados (entrada + leitura + escrita de cache, somados) são no
    máximo os BYTES UTF-8 do prompt + `FOLGA_FORMATO` tokens de marcação de papel/sistema.
    E todos são reservados ao preço MAIS CARO dos três (escrita de cache de 1h).
  • SAÍDA: no máximo `max_tokens`, que a API impõe e que inclui o pensamento. O harness
    limita `max_tokens` a `--max-saida` (as duas pontas têm continuação quando corta).
  • A reserva de TODA chamada (inclusive tentativa repetida e continuação) entra antes
    dela abrir; a chamada é recusada se gasto + reservas em andamento + esta passar de
    `teto - margem`. Chamada que termina SEM consumo informado (erro, corte, cancelamento)
    NÃO devolve a reserva: ela vira gasto, inteira.
  • VIGIA: depois de cada chamada, o consumo real é comparado ao limite de bytes. Se o
    real passar do limite, a premissa caiu: nenhuma chamada nova abre e a execução para.

REGISTROS (tudo em `_backups/validacao_contrato_s386/<execução>/`, ignorado pelo git):
  chamadas.jsonl  uma linha por chamada: lote, lado, fase, modelo, reserva, limite,
                  entrada completa (o system por hash em `prompts/<hash>.txt`), resposta
                  completa, mensagem final da API, consumo, custo, erro.
  lotes.jsonl     uma linha por lote: os dois `done` completos, erros, interrupção.
  relatorio.json  refeito pelo `relatar` a partir desses arquivos, sem pagar de novo.

CUSTO: o total inclui TUDO (lotes interrompidos, erros, sombra). A economia usa SÓ pares
completos: A e B com `done`, sem erro, sem interrupção e com consumo informado em todas as
chamadas do lote. Meta de 50%; a economia medida é relatada mesmo menor.

PARA NA HORA: perda/duplicação/código inventado no caminho novo; orçamento; >15% de
rejeitados depois de 60 blocos; saída média do contrato > 4.000 por chamada; erro de API
em > 2 lotes; consumo real acima do limite (garantia violada).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import pathlib
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# `_backups/` é ignorado pelo git: a amostra e os registros têm DADO REAL de aposta.
SAIDA = RAIZ / "_backups" / "validacao_contrato_s386"
COD = re.compile(r"(?m)^\[Código:\s*([^\]\r\n]*?)\s*\]")
PRECO = {  # US$/MTok: entrada, saída, leitura de cache, escrita de cache (1h)
    "claude-sonnet-5": (2.0, 10.0, 0.20, 4.00),
    "claude-haiku-4-5": (1.0, 5.0, 0.10, 2.00),
}
FOLGA_FORMATO = 1000     # tokens de marcação (papéis, separação de blocos) por chamada


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _custo(modelo, i, o, cr, cw) -> float:
    p = PRECO[modelo]
    return (i * p[0] + o * p[1] + cr * p[2] + cw * p[3]) / 1e6


# ── congelar ──────────────────────────────────────────────────────────────────

async def congelar(blocos_alvo: int, dias: int) -> None:
    import asyncpg
    from repository import hash_bloco
    dsn = (os.environ.get("DATABASE_PUBLIC_URL") or os.environ["DATABASE_URL"]).replace(
        "postgres://", "postgresql://", 1)
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            """SELECT s.dono, s.criado_em, s.codigo, s.bruto, s.ia_esporte, s.ia_aposta,
                      s.ia_descricao, b.data AS b_data, b.esporte AS b_esporte,
                      b.aposta AS b_aposta, b.descricao AS b_descricao, b.stake AS b_stake,
                      b.odd AS b_odd, b.resultado AS b_resultado
                 FROM sombra_rotulos s
                 LEFT JOIN LATERAL (SELECT * FROM bilhetes x
                                     WHERE x.dono = s.dono AND x.codigo_bilhete = s.codigo
                                     ORDER BY x.id DESC LIMIT 1) b ON TRUE
                WHERE s.casa = 'Bet365' AND s.codigo <> '' AND s.criado_em >= $1
                ORDER BY s.criado_em, s.id""", datetime.now() - timedelta(days=dias))
    finally:
        await conn.close()
    por_ext = defaultdict(list)
    for r in rows:
        por_ext[(r["dono"], r["criado_em"])].append(dict(r))
    donos, lotes, usados = {}, [], set()
    total = lambda: sum(len(l["blocos"]) for l in lotes)
    for (dono, _t), g in sorted(por_ext.items(), key=lambda kv: kv[0][1], reverse=True):
        vistos, limpo = set(), []
        for r in g:
            if r["codigo"] in vistos or r["codigo"] in usados:
                continue
            vistos.add(r["codigo"])
            limpo.append(r)
        for i in range(0, len(limpo) - 5, 6):
            if total() >= blocos_alvo:
                break
            anon = donos.setdefault(dono, f"dono{len(donos) + 1}")
            bl = []
            for r in limpo[i:i + 6]:
                usados.add(r["codigo"])
                bl.append({"codigo": r["codigo"], "bruto": r["bruto"], "hash": hash_bloco(r["bruto"]),
                           "producao_ia": {"esporte": r["ia_esporte"], "aposta": r["ia_aposta"],
                                           "descricao": r["ia_descricao"]},
                           "banco": {k[2:]: (str(r[k]) if r[k] is not None else None)
                                     for k in r if k.startswith("b_")}})
            lotes.append({"dono": anon, "blocos": bl})
        if total() >= blocos_alvo:
            break
    corpo = {"criado_em": datetime.now().isoformat(timespec="seconds"), "dias": dias, "lotes": lotes}
    corpo["manifesto"] = _sha(json.dumps(lotes, ensure_ascii=False, sort_keys=True))
    SAIDA.mkdir(parents=True, exist_ok=True)
    p = SAIDA / f"amostra_{corpo['manifesto'][:12]}.json"
    p.write_text(json.dumps(corpo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"congelada: {len(lotes)} lotes, {total()} blocos, {len(donos)} dono(s)\n"
          f"manifesto sha256: {corpo['manifesto']}\narquivo: {p}")


def carregar_amostra(p: pathlib.Path) -> dict:
    from repository import hash_bloco
    corpo = json.loads(p.read_text(encoding="utf-8"))
    if _sha(json.dumps(corpo["lotes"], ensure_ascii=False, sort_keys=True)) != corpo["manifesto"]:
        raise SystemExit("AMOSTRA ALTERADA: o manifesto não confere. Nada foi executado.")
    for l in corpo["lotes"]:
        for b in l["blocos"]:
            if hash_bloco(b["bruto"]) != b["hash"]:
                raise SystemExit(f"BLOCO ALTERADO: {b['codigo']}. Nada foi executado.")
    return corpo


# ── medidor: garantia do teto + registro de cada chamada ──────────────────────

class OrcamentoEsgotado(Exception):
    pass


class GarantiaViolada(Exception):
    pass


class _Medidor:
    def __init__(self, cliente, teto, margem, max_saida, pasta: pathlib.Path):
        self.c, self.teto, self.margem, self.max_saida = cliente, teto, margem, max_saida
        self.pasta = pasta
        (pasta / "prompts").mkdir(parents=True, exist_ok=True)
        self.arq = open(pasta / "chamadas.jsonl", "a", encoding="utf-8")
        self.lock = threading.Lock()
        self.gasto = self.reservado = 0.0
        self.pico = 0.0                # maior (gasto + reservado) já visto
        self.em_andamento = 0
        self.recusas = 0
        self.violacoes = []
        self.lote, self.lado = 0, "?"
        self.n = 0
        self.messages = self

    def _limite(self, modelo, system, messages, max_tokens):
        txt = "".join(b.get("text", "") for b in (system or []))
        for m in messages:
            c = m["content"]
            txt += c if isinstance(c, str) else "".join(b.get("text", "") for b in c)
        tok_in = len(txt.encode("utf-8")) + FOLGA_FORMATO
        p = PRECO[modelo]
        return tok_in, (tok_in * max(p[0], p[2], p[3]) + max_tokens * p[1]) / 1e6

    def _gravar(self, reg):
        self.arq.write(json.dumps(reg, ensure_ascii=False, default=str) + "\n")
        self.arq.flush()

    async def create(self, **kw):          # o aquecedor não roda no harness
        raise OrcamentoEsgotado("aquecedor desligado na validação")

    def stream(self, model, max_tokens, system, messages, **kw):
        max_tokens = min(max_tokens, self.max_saida)
        tok_in, reserva = self._limite(model, system, messages, max_tokens)
        sis = "\n\n".join(b.get("text", "") for b in (system or []))
        h = _sha(sis)[:16]
        pp = self.pasta / "prompts" / f"{h}.txt"
        if not pp.exists():
            pp.write_text(sis, encoding="utf-8")
        eh_sombra = model.startswith("claude-haiku")
        enxuto = sis.startswith("# MASTER_ESPORTES")
        fase = ("sombra" if eh_sombra else "A" if self.lado == "A"
                else "B_contrato" if enxuto else "B_encaminhados")
        with self.lock:
            self.n += 1
            nid = self.n
            if self.violacoes:
                raise GarantiaViolada("garantia do teto violada antes; nenhuma chamada nova")
            if self.gasto + self.reservado + reserva > self.teto - self.margem:
                self.recusas += 1
                self._gravar({"id": nid, "lote": self.lote, "lado": self.lado, "fase": fase,
                              "modelo": model, "recusada": True, "reserva": reserva,
                              "gasto_antes": self.gasto, "reservado_antes": self.reservado})
                raise OrcamentoEsgotado(
                    f"gasto {self.gasto:.4f} + reservado {self.reservado:.4f} + {reserva:.4f} "
                    f"> teto {self.teto:.2f} - margem {self.margem:.2f}")
            self.reservado += reserva
            self.em_andamento += 1
            self.pico = max(self.pico, self.gasto + self.reservado)
        reg = {"id": nid, "lote": self.lote, "lado": self.lado, "fase": fase, "modelo": model,
               "max_tokens": max_tokens, "limite_tokens_entrada": tok_in, "reserva": reserva,
               "system_sha": h, "messages": messages, "t0": time.time()}
        interno = self.c.messages.stream(model=model, max_tokens=max_tokens, system=system,
                                         messages=messages, **kw)
        med = self

        class _Ctx:
            def __init__(s):
                s.texto = []
                s.fin = None

            async def __aenter__(s):
                try:
                    s.s = await interno.__aenter__()
                except BaseException as e:
                    med._fechar(reg, reserva, None, "", repr(e))
                    raise
                return s

            async def __aexit__(s, et, ev, tb):
                erro = repr(ev) if ev is not None else None
                if s.fin is None and ev is None:
                    try:
                        s.fin = await s.s.get_final_message()
                    except Exception as e:
                        erro = repr(e)
                try:
                    r = await interno.__aexit__(et, ev, tb)
                finally:
                    med._fechar(reg, reserva, s.fin, "".join(s.texto), erro)
                return r

            @property
            async def text_stream(s):
                async for pedaco in s.s.text_stream:
                    s.texto.append(pedaco)
                    yield pedaco

            async def get_final_message(s):
                s.fin = await s.s.get_final_message()
                return s.fin

        return _Ctx()

    def _fechar(self, reg, reserva, fin, texto, erro):
        uso = getattr(fin, "usage", None) if fin is not None else None
        with self.lock:
            self.reservado -= reserva
            self.em_andamento -= 1
            reg.update({"t1": time.time(), "resposta_texto": texto, "erro": erro})
            if uso is None:
                # SEM consumo informado: a reserva inteira vira gasto (nunca se devolve)
                self.gasto += reserva
                reg.update({"consumo": None, "custo": reserva, "custo_e_reserva": True})
            else:
                i, o = uso.input_tokens, uso.output_tokens
                cr = getattr(uso, "cache_read_input_tokens", 0) or 0
                cw = getattr(uso, "cache_creation_input_tokens", 0) or 0
                c = _custo(reg["modelo"], i, o, cr, cw)
                self.gasto += c
                reg.update({"consumo": {"input": i, "output": o, "cache_read": cr, "cache_write": cw},
                            "custo": c, "custo_e_reserva": False,
                            "stop_reason": getattr(fin, "stop_reason", None)})
                try:
                    reg["mensagem_final"] = fin.model_dump(mode="json")
                except Exception:
                    reg["mensagem_final"] = {"content": [getattr(b, "type", "?")
                                                         for b in getattr(fin, "content", [])]}
                if i + cr + cw > reg["limite_tokens_entrada"] or o > reg["max_tokens"]:
                    self.violacoes.append(reg["id"])
                    reg["GARANTIA_VIOLADA"] = True
            self._gravar(reg)


# ── executar / simular ────────────────────────────────────────────────────────

def executar(amostra: pathlib.Path, teto, margem, max_saida, simular, falhas=None,
             transporte: str = "uvicorn") -> pathlib.Path:
    corpo = carregar_amostra(amostra)
    pasta = SAIDA / (("simulada_" if simular else "real_") + corpo["manifesto"][:12])
    trava = pasta / "INICIADA"
    if trava.exists():
        raise SystemExit(f"Esta amostra JÁ foi executada ({pasta}). Não repito: use `relatar`.")
    pasta.mkdir(parents=True, exist_ok=True)
    trava.write_text(datetime.now().isoformat(), encoding="utf-8")
    (pasta / "parametros.json").write_text(json.dumps(
        {"amostra": str(amostra), "manifesto": corpo["manifesto"], "teto": teto, "margem": margem,
         "max_saida": max_saida, "simulada": simular, "folga_formato": FOLGA_FORMATO,
         "falhas": falhas or {}, "transporte": transporte}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    os.environ.pop("DATABASE_URL", None)              # produção nunca é tocada
    os.environ.pop("DATABASE_PUBLIC_URL", None)
    os.environ.setdefault("SESSION_SECRET", "validacao-local-s386")
    import logging
    import main
    logging.disable(logging.INFO)
    from fastapi.testclient import TestClient

    if simular:
        cliente = _IAFalsa(corpo, falhas or {})
    else:
        from anthropic import AsyncAnthropic
        cliente = AsyncAnthropic()
    med = _Medidor(cliente, teto, margem, max_saida, pasta)
    main._client = med
    main._MAX_CONCURRENT = 2
    # a sombra e o titular não podem depender de variável do ambiente de produção
    main._SOMBRA_MODELO = "claude-haiku-4-5"
    if main.DEFAULT_MODEL not in PRECO:
        raise SystemExit(f"modelo titular {main.DEFAULT_MODEL} sem preço conhecido — não executo.")

    async def _nada(*a, **k):
        return None

    async def _dedup(texto, *a, **k):
        return texto, 0

    sombras = []

    async def _reg_sombra(*a, **k):
        sombras.append({"lote": med.lote, "placar": a[7], "erro": a[8] if len(a) > 8 else None,
                        "contrato": k.get("contrato")})

    _sombra_real = main._sombra_modelo

    async def _sombra_so_do_contrato(*a, **k):
        if k.get("contrato"):             # a sombra do caminho de hoje fica de fora
            await _sombra_real(*a, **k)

    main.registrar_uso = _nada
    main.registrar_sombra = _nada
    main._barreira_lembrar = _nada
    main.registrar_sombra_modelo = _reg_sombra
    main._sombra_modelo = _sombra_so_do_contrato
    main._dedup_superbet_text = _dedup
    main._sombra_vale_agora = lambda: True
    main.app.dependency_overrides[main.usuario_atual] = lambda: "Validacao"
    # TRANSPORTE. O `TestClient` CANCELA as tarefas de fundo quando a requisição termina, e
    # a sombra do Haiku roda depois do `done`, em fundo: na execução de 24/09 as 16 sombras
    # morreram com `CancelledError` e não mediram nada. Com um uvicorn DE VERDADE numa
    # thread (como a produção), a tarefa sobrevive à resposta. `testclient` fica só para
    # reproduzir o defeito na demonstração.
    srv = th = None
    if transporte == "uvicorn":
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
        t0 = time.time()
        while not srv.started:
            if time.time() - t0 > 30:
                raise SystemExit("servidor local não subiu")
            time.sleep(0.1)
        _post = lambda data: httpx.post(f"http://127.0.0.1:{porta}/extrair", data=data, timeout=3600)
    else:
        cli = TestClient(main.app)
        _post = lambda data: cli.post("/extrair", data=data)
    arq_lotes = open(pasta / "lotes.jsonl", "a", encoding="utf-8")

    def _extrair(texto, ligado):
        if ligado:
            os.environ["CONTRATO_TEXTO_CASAS"] = "BET365"
        else:
            os.environ.pop("CONTRATO_TEXTO_CASAS", None)
        r = _post({"casa": "Bet365", "parceiro": "Conta Validacao", "texto": texto})
        evs = [json.loads(l[6:]) for l in r.text.split("\n") if l.startswith("data: ")]
        return (next((e for e in evs if e.get("done")), None),
                next((e.get("error") for e in evs if e.get("error")), None))

    def _esperar_fundo():
        t0 = time.time()
        while time.time() - t0 < 900:
            if med.em_andamento == 0 and not main._bg_tasks:
                time.sleep(1.0)
                if med.em_andamento == 0 and not main._bg_tasks:
                    return
            time.sleep(0.5)

    paradas, erros_api, blocos_b, rej_b = [], 0, 0, 0
    try:
        for n, lote in enumerate(corpo["lotes"], start=1):
            texto = "\n\n".join(f"[Código: {b['codigo']}]\n{b['bruto']}" for b in lote["blocos"])
            cods = COD.findall(texto)
            ordem = ("A", "B") if n % 2 else ("B", "A")
            saida, recusas0, viol0 = {}, med.recusas, len(med.violacoes)
            for lado in ordem:
                med.lote, med.lado = n, lado
                try:
                    done, erro = _extrair(texto, ligado=(lado == "B"))
                except (OrcamentoEsgotado, GarantiaViolada) as e:
                    done, erro = None, repr(e)
                _esperar_fundo()
                saida[lado] = {"done": done, "erro": erro}
                if med.recusas > recusas0 or len(med.violacoes) > viol0:
                    break
            interrompido = ("orçamento" if med.recusas > recusas0 else
                            "garantia violada" if len(med.violacoes) > viol0 else None)
            reg = {"lote": n, "cods": cods, "ordem": list(ordem), "interrompido": interrompido,
                   **{f"{k}_done": v["done"] for k, v in saida.items()},
                   **{f"{k}_erro": v["erro"] for k, v in saida.items()}}
            arq_lotes.write(json.dumps(reg, ensure_ascii=False, default=str) + "\n")
            arq_lotes.flush()
            print(f"lote {n}/{len(corpo['lotes'])} · gasto US$ {med.gasto:.4f} · pico "
                  f"comprometido US$ {med.pico:.4f} de {teto - margem:.2f}", flush=True)
            if interrompido:
                paradas.append(f"lote {n}: {interrompido}")
                break
            if saida.get("A", {}).get("erro") or saida.get("B", {}).get("erro"):
                erros_api += 1
            b = saida.get("B", {})
            if b.get("done") and not b.get("erro"):
                lb = _linhas(b["done"])
                if sorted(c for c in lb for _ in lb[c]) != sorted(cods):
                    paradas.append(f"lote {n}: PERDA/DUPLICAÇÃO/CÓDIGO INVENTADO no caminho novo")
                    break
                info = b["done"].get("contrato") or {}
                blocos_b += len(cods)
                rej_b += info.get("rejeitados_depois", 0)
            if erros_api > 2:
                paradas.append(f"erro de API em {erros_api} lotes")
                break
            if blocos_b >= 60 and rej_b > 0.15 * blocos_b:
                paradas.append(f"rejeitados depois da IA {rej_b}/{blocos_b} > 15%")
                break
            f4 = [json.loads(l) for l in open(pasta / "chamadas.jsonl", encoding="utf-8")]
            f4 = [c for c in f4 if c.get("fase") == "B_contrato" and c.get("consumo")]
            if f4 and sum(c["consumo"]["output"] for c in f4) / len(f4) > 4000:
                paradas.append("saída média do contrato > 4.000 tokens por chamada")
                break
    finally:
        _esperar_fundo()
        if srv is not None:
            srv.should_exit = True
            th.join(15)
        arq_lotes.close()
        med.arq.close()
        (pasta / "sombras.json").write_text(json.dumps(sombras, ensure_ascii=False, default=str),
                                            encoding="utf-8")
        (pasta / "fim.json").write_text(json.dumps(
            {"gasto": med.gasto, "pico_comprometido": med.pico, "recusas": med.recusas,
             "violacoes": med.violacoes, "em_andamento_no_fim": med.em_andamento,
             "paradas": paradas}, ensure_ascii=False, indent=1), encoding="utf-8")
    relatar(pasta, amostra)
    return pasta


def _linhas(done):
    if not done:
        return {}
    m = re.search(r"```tsv\n(.*?)\n```", done.get("resultado") or "", re.S)
    out = defaultdict(list)
    for l in (m.group(1) if m else "").splitlines():
        c = l.split("\t")
        if len(c) >= 11 and not l.startswith("Data\t"):
            out[c[10]].append(l)
    return out


# ── relatar (só a partir do que foi gravado) ──────────────────────────────────

def relatar(pasta: pathlib.Path, amostra: pathlib.Path | None = None) -> dict:
    import logging
    logging.disable(logging.INFO)
    import contrato_texto as ct
    import repository as repo
    from descricao_check import checar_descricao, checar_fidelidade
    par = json.loads((pasta / "parametros.json").read_text(encoding="utf-8"))
    corpo = carregar_amostra(pathlib.Path(amostra or par["amostra"]))
    blocos = {b["codigo"]: b for l in corpo["lotes"] for b in l["blocos"]}
    chamadas = [json.loads(l) for l in open(pasta / "chamadas.jsonl", encoding="utf-8")]
    lotes = [json.loads(l) for l in open(pasta / "lotes.jsonl", encoding="utf-8")]
    fim = json.loads((pasta / "fim.json").read_text(encoding="utf-8"))

    # custo por lote e por caminho: TUDO (interrompido, erro e sombra inclusive)
    por_lote = defaultdict(lambda: defaultdict(float))
    sem_consumo = defaultdict(int)          # só A/B: é o que entra na comparação
    sem_consumo_sombra = defaultdict(int)   # a sombra fica fora do custo de A e de B
    for c in chamadas:
        if c.get("recusada"):
            continue
        por_lote[c["lote"]][c["fase"]] += c["custo"]
        if c.get("custo_e_reserva"):
            (sem_consumo_sombra if c["fase"] == "sombra" else sem_consumo)[c["lote"]] += 1
    total = sum(sum(v.values()) for v in por_lote.values())

    completos = [l for l in lotes
                 if not l.get("interrompido") and l.get("A_done") and l.get("B_done")
                 and not l.get("A_erro") and not l.get("B_erro") and sem_consumo[l["lote"]] == 0]
    ids_c = {l["lote"] for l in completos}
    nb = sum(len(l["cods"]) for l in completos)
    soma = lambda fase: sum(por_lote[l].get(fase, 0.0) for l in ids_c)
    esc = lambda fase: sum(c["consumo"]["cache_write"] * PRECO[c["modelo"]][3] / 1e6
                           for c in chamadas if c.get("consumo") and c["fase"] == fase
                           and c["lote"] in ids_c)
    a_usd = soma("A")
    b_usd = soma("B_contrato") + soma("B_encaminhados")
    a_q = a_usd - esc("A")
    b_q = b_usd - esc("B_contrato") - esc("B_encaminhados")

    C = Counter()
    divergencias = []
    for l in completos:
        la, lb = _linhas(l["A_done"]), _linhas(l["B_done"])
        info = l["B_done"].get("contrato") or {}
        C["B_cobertos"] += info.get("cobertos", 0)
        C["B_encaminhados_antes"] += info.get("encaminhados_antes", 0)
        C["B_rejeitados_depois"] += info.get("rejeitados_depois", 0)
        for cod in l["cods"]:
            C[f"A_linhas_por_codigo={len(la.get(cod, []))}"] += 1
            C[f"B_linhas_por_codigo={len(lb.get(cod, []))}"] += 1
            a, b = (la.get(cod) or [None])[0], (lb.get(cod) or [None])[0]
            if a is None or b is None:
                continue
            ca, cb = a.split("\t"), b.split("\t")
            bl = blocos[cod]
            lt = ct.ler_numeros(cod, bl["bruto"])
            for lado, cols in (("A", ca), ("B", cb)):
                if cols[9] and lt.retorno is not None:
                    pl = repo.calcular_pl(cols[7], cols[8], cols[9])
                    esp = lt.retorno - (repo._num_or_none(cols[7]) or 0)
                    ok = pl is not None and abs(pl - esp) <= 0.01
                    C[f"{lado}_pl_{'confere' if ok else 'NAO_confere'}_com_o_texto"] += 1
                if [p for p in checar_descricao(cols[5], cols[6]) if p[0] == "erro"]:
                    C[f"{lado}_desc_fora_do_master"] += 1
                if [p for p in checar_fidelidade(cols[6], bl["bruto"]) if p[0] == "erro"]:
                    C[f"{lado}_desc_infiel"] += 1
            for i, campo in ((0, "data"), (1, "esporte"), (5, "aposta"), (6, "descricao"),
                             (7, "stake"), (8, "odd"), (9, "resultado")):
                if ca[i] == cb[i]:
                    C[f"{campo}_igual"] += 1
                    continue
                if campo in ("stake", "odd"):
                    x, y = repo._num_or_none(ca[i]), repo._num_or_none(cb[i])
                    if x is not None and y is not None and abs(x - y) < 1e-9:
                        C[f"{campo}_mesmo_valor_grafia_diferente"] += 1
                        continue
                if campo in ("data", "stake", "odd", "resultado"):
                    ref = lt.campos.get(campo) or {}
                    fonte = ref.get("texto") if campo in ("stake", "odd") else ref.get("valor")
                    if fonte is None:
                        veredito = "fonte não publica: " + "; ".join(lt.motivos)[:90]
                    elif str(fonte) == cb[i]:
                        veredito = "novo = fonte"
                    elif str(fonte) == ca[i]:
                        veredito = "atual = fonte"
                    else:
                        veredito = f"nenhum = fonte ({fonte})"
                    if campo == "odd" and lt.retorno is not None and ca[9] == "W" and cb[9] == "W":
                        sa = repo._num_or_none(ca[7]) or 0
                        ea = abs(sa * (repo._num_or_none(ca[8]) or 0) - lt.retorno)
                        eb = abs(sa * (repo._num_or_none(cb[8]) or 0) - lt.retorno)
                        veredito += f" · |stake×odd − retorno|: atual {ea:.3f}, novo {eb:.3f}"
                else:
                    prod = (bl.get("producao_ia") or {}).get(campo)
                    ajuste = any(a2[0] == cod and a2[1] == campo for a2 in (info.get("ajustes") or []))
                    veredito = ("ajuste estrutural do código (MASTER)" if ajuste else
                                "novo = produção" if cb[i] == prod else
                                "atual = produção" if ca[i] == prod else "nenhum = produção")
                    if campo == "descricao":
                        g = []
                        for lado, cols in (("atual", ca), ("novo", cb)):
                            e = [p for p in checar_descricao(cols[5], cols[6]) if p[0] == "erro"]
                            e += [p for p in checar_fidelidade(cols[6], bl["bruto"]) if p[0] == "erro"]
                            g.append(f"{lado} {'reprova' if e else 'passa'}")
                        veredito += " · gates: " + ", ".join(g)
                C[f"{campo}_difere"] += 1
                divergencias.append({"lote": l["lote"], "codigo": cod, "campo": campo,
                                     "atual": ca[i], "novo": cb[i], "veredito": veredito})

    rel = {
        "modo": "SIMULADO (IA falsa, custo fictício)" if par["simulada"] else "REAL",
        "manifesto": corpo["manifesto"], "teto": par["teto"], "margem": par["margem"],
        "max_saida": par["max_saida"], "folga_formato": par["folga_formato"],
        "gasto_total_usd": round(total, 6),
        "gasto_total_confere_com_o_medidor": abs(total - fim["gasto"]) < 1e-6,
        "pico_comprometido_usd": round(fim["pico_comprometido"], 6),
        "recusas_de_orcamento": fim["recusas"], "garantia_violada_em": fim["violacoes"],
        "chamadas": len([c for c in chamadas if not c.get("recusada")]),
        "chamadas_sem_consumo_informado": sum(sem_consumo.values()),
        "chamadas_sem_consumo_informado_sombra": sum(sem_consumo_sombra.values()),
        "custo_por_lote": {str(k): {f: round(v2, 6) for f, v2 in v.items()}
                           for k, v in sorted(por_lote.items())},
        "lotes_executados": len(lotes), "pares_completos": len(completos), "blocos_nos_pares": nb,
        "paradas": fim["paradas"],
        "comparacao_pares_completos": {
            "atual_usd": round(a_usd, 6), "novo_usd": round(b_usd, 6),
            "atual_por_bilhete": round(a_usd / nb, 6) if nb else None,
            "novo_por_bilhete": round(b_usd / nb, 6) if nb else None,
            "economia_medida": round(1 - b_usd / a_usd, 4) if a_usd else None,
            "economia_medida_sem_escrita_de_cache": round(1 - b_q / a_q, 4) if a_q else None,
            "sombra_haiku_usd_a_parte": round(sum(por_lote[l].get("sombra", 0.0) for l in ids_c), 6),
        },
        "contagens": dict(sorted(C.items())),
        "divergencias": divergencias,
    }
    (pasta / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    resumo = {k: rel[k] for k in ("modo", "gasto_total_usd", "gasto_total_confere_com_o_medidor",
                                  "pico_comprometido_usd", "recusas_de_orcamento",
                                  "garantia_violada_em", "chamadas", "chamadas_sem_consumo_informado",
                                  "lotes_executados", "pares_completos", "blocos_nos_pares",
                                  "paradas", "comparacao_pares_completos")}
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    print("divergências:", len(divergencias), "| relatório:", pasta / "relatorio.json")
    return rel


# ── IA falsa (simular) ────────────────────────────────────────────────────────

class _IAFalsa:
    """Responde como a produção respondeu (decisão gravada + números do bloco), com
    consumo fictício DENTRO do limite. `falhas` programa defeitos pelo nº da chamada:
      {"sem_consumo": [n, ...]}  a chamada n quebra no meio do stream, sem `usage`
      {"estoura_limite": [n]}    a chamada n informa consumo acima do limite de bytes
      {"atraso": s, "atraso_sombra": s}  latência no meio do stream (a da sombra à parte)
    """

    def __init__(self, corpo, falhas):
        self.b = {b["codigo"]: b for l in corpo["lotes"] for b in l["blocos"]}
        self.falhas = falhas
        self.n = 0
        self.messages = self

    def stream(self, model, max_tokens, system, messages, **kw):
        import types
        import contrato_texto as ct
        self.n += 1
        n = self.n
        txt = messages[0]["content"][0]["text"]
        enxuto = system and str(system[0].get("text", "")).startswith("# MASTER_ESPORTES")
        ls = []
        for p in re.split(r"(?m)(?=^\[Código:\s)", txt):
            m = COD.match(p)
            if not m or m.group(1) not in self.b:
                continue
            c, b = m.group(1), self.b[m.group(1)]
            ia = b["producao_ia"]
            if enxuto:
                ls.append(f"{c}\t{ia['esporte']}\t{ia['aposta']}\t{ia['descricao']}")
            else:
                lt = ct.ler_numeros(c, p[m.end():])
                g = lambda k, t="texto": (lt.campos.get(k) or {}).get(t) or ""
                res = ((lt.campos.get("resultado") or {}).get("valor")
                       if lt.campos.get("resultado") else (b["banco"].get("resultado") or ""))
                ls.append("\t".join([g("data", "valor") or (b["banco"].get("data") or ""),
                                     ia["esporte"] or "", "", "Bet365", "Conta Validacao",
                                     ia["aposta"] or "", ia["descricao"] or "",
                                     g("stake") or (b["banco"].get("stake") or ""),
                                     g("odd") or (b["banco"].get("odd") or ""), res or "", c]))
        corpo = "```tsv\n" + "\n".join(ls) + "\n```"
        grande = 10 ** 9 if n in self.falhas.get("estoura_limite", []) else 0
        uso = types.SimpleNamespace(input_tokens=1000 + grande, output_tokens=300 if enxuto else 1200,
                                    cache_read_input_tokens=20000 if enxuto else 40000,
                                    cache_creation_input_tokens=0)
        quebra = n in self.falhas.get("sem_consumo", [])
        atraso = float(self.falhas.get("atraso", 0))
        if model.startswith("claude-haiku"):
            # a sombra real (Haiku, pensando) sobrevive à resposta por segundos
            atraso = float(self.falhas.get("atraso_sombra", atraso))

        class _S:
            async def __aenter__(s):
                return s

            async def __aexit__(s, *a):
                return False

            @property
            async def text_stream(s):
                yield corpo[: len(corpo) // 2]
                if atraso:
                    await asyncio.sleep(atraso)
                if quebra:
                    raise ConnectionError("simulada: conexão caiu no meio, sem usage")
                yield corpo[len(corpo) // 2:]

            async def get_final_message(s):
                if quebra:
                    raise ConnectionError("simulada: sem mensagem final")
                return types.SimpleNamespace(stop_reason="end_turn", usage=uso,
                                             content=[types.SimpleNamespace(type="text", text=corpo)])
        return _S()


def main_cli():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("congelar")
    c.add_argument("--blocos", type=int, default=150)
    c.add_argument("--dias", type=int, default=7)
    for nome in ("executar", "simular"):
        e = sub.add_parser(nome)
        e.add_argument("--amostra", required=True)
        e.add_argument("--teto", type=float, default=8.0)
        e.add_argument("--margem", type=float, default=0.25)
        e.add_argument("--max-saida", type=int, default=16000)
        e.add_argument("--transporte", choices=("uvicorn", "testclient"), default="uvicorn")
        if nome == "simular":
            e.add_argument("--falhas", default="{}", help='JSON, ex.: {"sem_consumo":[3], "atraso": 0.5}')
    r = sub.add_parser("relatar")
    r.add_argument("--pasta", required=True)
    a = ap.parse_args()
    if a.cmd == "congelar":
        asyncio.run(congelar(a.blocos, a.dias))
    elif a.cmd == "relatar":
        relatar(pathlib.Path(a.pasta))
    else:
        if a.cmd == "executar":
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise SystemExit("ANTHROPIC_API_KEY ausente (rode dentro do railway run -s extrator).")
            if a.teto > 8.0:
                raise SystemExit("teto acima de US$ 8 não é permitido.")
        executar(pathlib.Path(a.amostra), a.teto, a.margem, a.max_saida,
                 simular=(a.cmd == "simular"), falhas=json.loads(getattr(a, "falhas", "{}")),
                 transporte=a.transporte)


if __name__ == "__main__":
    main_cli()
