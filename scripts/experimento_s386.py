"""Experimento s386 (24/09): Haiku x Sonnet no contrato de 4 campos, e o FLUXO COMPLETO
tradutor → modelo → escalonamento, na Bet365. Roda no worktree isolado
`exp/s386-custo-haiku`, com as instruções corrigidas (MASTER_DESCRICAO §10.1 e §12.5.1,
CASA_BET365 §9) e o tradutor corrigido ((F) e escopo de time). Nunca escreve no banco
e nunca liga nada em produção.

COMANDOS
  congelar  grátis, SÓ LEITURA. Grupos REAIS de captura (dono + instante), Bet365, sem
            nenhum código já usado para AJUSTAR as instruções (`--excluir`). Manifesto sha256.
  ajuste    PAGO, pequeno. Roda Sonnet e Haiku nos blocos de AJUSTE (os 222 já vistos),
            para conferir que a instrução corrigida faz o que promete ANTES de gastar o
            conjunto de teste. Resultado disto NÃO entra em conclusão nenhuma.
  executar  PAGO. As rodadas R1..R5 sobre o conjunto de TESTE congelado (ver CRITERIOS).
  relatar   grátis: tudo a partir do que foi gravado.

O teto é garantido pelo mesmo `_Medidor` da validação (reserva por bytes + max_tokens,
chamada sem consumo vira gasto inteiro, vigia de violação).
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
import time
from collections import defaultdict
from datetime import datetime, timedelta

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SAIDA = pathlib.Path(r"C:/Users/Fernando/Downloads/FDC Capital/Planilhador/_backups/experimento_s386")
COD = re.compile(r"(?m)^\[Código:\s*([^\]\r\n]*?)\s*\]")
SONNET, HAIKU = "claude-sonnet-5", "claude-haiku-4-5"
POR_LOTE = 6            # = main._BILHETES_POR_CHUNK

# ── CRITÉRIOS, registrados ANTES da execução (vão para `criterios.json` na pasta) ─────
CRITERIOS = {
    "metrica": "fração de BLOCOS com >= 1 erro real de significado CONFIRMADO contra o texto "
               "original (juiz pela fonte + revisão de cada achado; alarme falso do juiz sai)",
    "barras": [0.01, 0.02, 0.05],
    "veredito_por_barra": "intervalo exato (Clopper-Pearson) de 95%: APROVADO se o teto < barra; "
                          "REPROVADO se o piso > barra; senão INCONCLUSIVO (amostra insuficiente). "
                          "Amostra pequena NUNCA vira reprovação.",
    "haiku_serve_num_papel_se": "no papel testado, a diferença PAREADA de erro (Haiku - Sonnet, mesmos "
                                "blocos) tem teto de 95% <= 1 ponto percentual E o custo do resultado "
                                "correto (incluindo escalonamento ao Sonnet) é menor. Se o piso da "
                                "diferença > 1 p.p., o Haiku está ENCERRADO naquele papel.",
    "paradas": ["orçamento (teto garantido)", "garantia do medidor violada",
                "erro de API em > 3 lotes seguidos"],
    "sem_parada_por_qualidade": "não há espiada intermediária: a execução roda inteira ou para por "
                                "orçamento, e o que faltar é relatado como NÃO MEDIDO",
    "falso_negativo": "30 blocos 'limpos' sorteados por braço, revisados contra o texto",
}


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── congelar ──────────────────────────────────────────────────────────────────

async def congelar(alvo: int, dias: int, excluir: pathlib.Path, teto_dono: float,
                   formato_novo: bool = False, prefixo: str = "teste") -> None:
    import asyncpg
    from repository import hash_bloco
    fora = set(json.loads(excluir.read_text(encoding="utf-8")))
    dsn = (os.environ.get("DATABASE_PUBLIC_URL") or os.environ["DATABASE_URL"]).replace(
        "postgres://", "postgresql://", 1)
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute("SET default_transaction_read_only = on")
        rows = await conn.fetch(
            """SELECT s.dono, s.criado_em, s.codigo, s.bruto, s.ia_esporte, s.ia_aposta,
                      s.ia_descricao
                 FROM sombra_rotulos s
                WHERE s.casa = 'Bet365' AND s.codigo <> '' AND s.criado_em >= $1
                ORDER BY s.criado_em, s.id""", datetime.now() - timedelta(days=dias))
    finally:
        await conn.close()
    grupos = defaultdict(list)
    for r in rows:
        grupos[(r["dono"], r["criado_em"])].append(dict(r))
    # os grupos de cada dono, do mais recente para o mais antigo; round-robin entre donos
    por_dono = defaultdict(list)
    for (dono, t), g in sorted(grupos.items(), key=lambda kv: kv[0][1], reverse=True):
        por_dono[dono].append(g)
    usados, lotes, anon, cont = set(), [], {}, defaultdict(int)
    total = 0
    ativos = list(por_dono)
    while total < alvo and ativos:
        for dono in list(ativos):
            if not por_dono[dono] or cont[dono] >= teto_dono * alvo:
                ativos.remove(dono)
                continue
            g = por_dono[dono].pop(0)
            bl = []
            for r in g:
                c = r["codigo"]
                if c in usados or c in fora:
                    continue
                # só a data que a casa PUBLICA (formato da extensão atual, s339/s373)
                if formato_novo and not re.search(r"(?m)^Data \((evento|coloca)", r["bruto"]):
                    continue
                usados.add(c)
                bl.append({"codigo": c, "bruto": r["bruto"], "hash": hash_bloco(r["bruto"]),
                           "producao_ia": {"esporte": r["ia_esporte"], "aposta": r["ia_aposta"],
                                           "descricao": r["ia_descricao"]}})
            if not bl:
                continue
            a = anon.setdefault(dono, f"dono{len(anon) + 1}")
            lotes.append({"dono": a, "captura": g[0]["criado_em"].isoformat(), "blocos": bl})
            cont[dono] += len(bl)
            total += len(bl)
            if total >= alvo:
                break
    corpo = {"criado_em": datetime.now().isoformat(timespec="seconds"), "dias": dias,
             "excluidos_por_ajuste": len(fora), "grupos": lotes}
    corpo["manifesto"] = _sha(json.dumps(lotes, ensure_ascii=False, sort_keys=True))
    SAIDA.mkdir(parents=True, exist_ok=True)
    corpo["formato_novo"] = formato_novo
    p = SAIDA / f"{prefixo}_{corpo['manifesto'][:12]}.json"
    p.write_text(json.dumps(corpo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"congelado: {len(lotes)} grupos de captura, {total} blocos, {len(anon)} dono(s) "
          f"{dict((anon[d], n) for d, n in cont.items() if d in anon)}\nmanifesto {corpo['manifesto']}\n{p}")


def carregar(p: pathlib.Path) -> dict:
    from repository import hash_bloco
    corpo = json.loads(p.read_text(encoding="utf-8"))
    if _sha(json.dumps(corpo["grupos"], ensure_ascii=False, sort_keys=True)) != corpo["manifesto"]:
        raise SystemExit("AMOSTRA ALTERADA: manifesto não confere.")
    for g in corpo["grupos"]:
        for b in g["blocos"]:
            if hash_bloco(b["bruto"]) != b["hash"]:
                raise SystemExit(f"BLOCO ALTERADO: {b['codigo']}")
    return corpo


# ── rodadas ───────────────────────────────────────────────────────────────────

def _texto(blocos):
    return "\n\n".join(f"[Código: {b['codigo']}]\n{b['bruto']}" for b in blocos)


def _em_lotes(grupos, filtro):
    """Lotes de até POR_LOTE, SEM misturar grupos de captura (é o que a produção faz: um
    `/extrair` por captura). `filtro(bloco)` escolhe quem vai para esta rodada."""
    out = []
    for g in grupos:
        sel = [b for b in g["blocos"] if filtro(b)]
        out += [sel[i:i + POR_LOTE] for i in range(0, len(sel), POR_LOTE)]
    return out


class _Rodadas:
    def __init__(self, med, system, concorrencia=3):
        import contrato_texto as ct
        import taxonomia
        self.ct, self.med, self.system = ct, med, system
        self.sem = asyncio.Semaphore(concorrencia)
        self.esportes = set(taxonomia.esportes_canonicos())
        self.categorias = set(taxonomia.categorias_canonicas())
        self.erros_api_seguidos = 0
        self.parar = None

    async def _chamar(self, rotulo, modelo, texto, kw=None):
        from validar_contrato_bet365 import OrcamentoEsgotado, GarantiaViolada
        instr = {"type": "text", "text": self.ct.INSTRUCAO.format(casa="Bet365")}
        msgs = [{"role": "user", "content": [{"type": "text", "text": texto}, instr]}]
        for tentativa in (1, 2):
            async with self.sem:
                # CABE NO TETO? Se não cabe por causa de reservas EM ANDAMENTO, espera elas
                # voltarem (a reserva é o pior caso; o real costuma ser uma fração). Só é
                # "orçamento esgotado" quando não cabe e não há nada em andamento. A 1ª
                # versão recusava e abortava com chamadas no ar (ajuste_971577a9).
                _, reserva = self.med._limite(modelo, self.system, msgs, self.med.max_saida)
                while True:
                    if self.parar:
                        raise OrcamentoEsgotado(f"parada já decidida: {self.parar}")
                    with self.med.lock:
                        cabe = self.med.gasto + self.med.reservado + reserva <= self.med.teto - self.med.margem
                        andando = self.med.em_andamento
                    if cabe:
                        break
                    if not andando:
                        self.parar = (f"orçamento: gasto {self.med.gasto:.4f} + reserva {reserva:.4f} "
                                      f"> teto {self.med.teto:.2f} - margem {self.med.margem:.2f}")
                        raise OrcamentoEsgotado(self.parar)
                    await asyncio.sleep(1.0)
                self.med.lote, self.med.lado = rotulo, rotulo.split(":")[0]
                try:
                    async with self.med.stream(model=modelo, max_tokens=self.med.max_saida,
                                               system=self.system, messages=msgs,
                                               **(kw or {})) as s:
                        async for _ in s.text_stream:
                            pass
                        fin = await s.get_final_message()
                    self.erros_api_seguidos = 0
                    txt = "".join(getattr(b, "text", "") for b in fin.content
                                  if getattr(b, "type", "") == "text")
                    return txt, getattr(fin, "stop_reason", None), None
                except (OrcamentoEsgotado, GarantiaViolada) as e:
                    self.parar = self.parar or repr(e)
                    raise
                except Exception as e:           # noqa: BLE001 — registrado, e conta p/ parada
                    self.erros_api_seguidos += 1
                    if self.erros_api_seguidos > 3:
                        self.parar = f"erro de API em > 3 chamadas seguidas: {e!r}"
                        raise RuntimeError(self.parar)
                    if tentativa == 2:
                        return "", None, repr(e)
                    await asyncio.sleep(5)

    def _avaliar(self, lote, resposta):
        """Uma decisão por bloco: aceita pelo portão do contrato, ou recusada com motivo.
        A resposta CRUA também fica (a comparação de modelo julga as duas)."""
        linhas = {}
        for ln in self.ct._linhas_resposta(resposta):
            cols = [c.strip() for c in ln.split("\t")]
            if len(cols) == 4:
                linhas.setdefault(cols[0], []).append(cols)
        out = {}
        for b in lote:
            lt = self.ct.ler_numeros(b["codigo"], b["bruto"])
            ach = linhas.get(b["codigo"], [])
            if len(ach) != 1:
                out[b["codigo"]] = {"cru": None, "motivo": "sem linha" if not ach else "linha repetida"}
                continue
            _, e, a, d = ach[0]
            e2, a2, _aj, motivo = self.ct.aceitar_4campos(lt, e, a, d, self.esportes, self.categorias)
            out[b["codigo"]] = {"cru": [e, a, d], "final": [e2, a2, d], "motivo": motivo}
        return out

    async def rodada(self, nome, modelo, lotes, kw=None):
        async def um(i, lote):
            txt, stop, erro = await self._chamar(f"{nome}:{i}", modelo, _texto(lote), kw)
            r = self._avaliar(lote, txt)
            return {"i": i, "cods": [b["codigo"] for b in lote], "stop": stop, "erro": erro,
                    "resposta": txt, "decisoes": r}
        # TODAS terminam antes de qualquer decisão: sem isso, uma parada fechava o registro
        # com chamadas no ar e o consumo delas se perdia.
        rs = await asyncio.gather(*(um(i, l) for i, l in enumerate(lotes)), return_exceptions=True)
        feitos = [r for r in rs if isinstance(r, dict)]
        if self.parar:
            self.parcial = feitos
            raise RuntimeError(self.parar)
        erros = [r for r in rs if isinstance(r, BaseException)]
        if erros:
            self.parcial = feitos
            raise RuntimeError(f"falha inesperada: {erros[0]!r}")
        return feitos


async def _executar(amostra, teto, margem, pasta, simular, ajuste_cods=None, plano_nome=None):
    import logging
    logging.disable(logging.WARNING)
    import contrato_texto as ct
    import tradutor as trad
    from validar_contrato_bet365 import _Medidor, OrcamentoEsgotado, GarantiaViolada
    corpo = carregar(amostra) if ajuste_cods is None else amostra
    grupos = corpo["grupos"]
    if simular:
        cliente = _IAFalsa(grupos)
    else:
        from anthropic import AsyncAnthropic
        cliente = AsyncAnthropic()
    med = _Medidor(cliente, teto, margem, 16000 if plano_nome in ("pensamento", "sem_pensamento") else 8000, pasta)
    system = ct.build_system_enxuto("BET365")
    (pasta / "system_sha.txt").write_text(_sha("\n\n".join(b["text"] for b in system)), encoding="utf-8")
    R = _Rodadas(med, system)
    trad_ok = {b["codigo"]: trad.traduzir("BET365", b["bruto"]).ok
               for g in grupos for b in g["blocos"]}
    res, parada = {}, None
    # ORDEM = PRIORIDADE (se o orçamento acabar, o que ficou para trás é o menos decisivo):
    # 1º o resíduo do tradutor com os dois modelos e o escalonamento (fluxos A3/A4, o
    # papel do Haiku onde o código não resolve); depois os modelos em TUDO (A1/A2).
    def recusados(origem):
        rec = {c for l in res.get(origem, []) for c, d in l["decisoes"].items() if d["motivo"]}
        return lambda b: b["codigo"] in rec
    plano = ([("R1", SONNET, lambda b: True), ("R2", HAIKU, lambda b: True)] if ajuste_cods is not None
             else [("R3", SONNET, lambda b: not trad_ok[b["codigo"]]),
                   ("R4", HAIKU, lambda b: not trad_ok[b["codigo"]]),
                   ("R5", SONNET, "R4"),
                   ("R1", SONNET, lambda b: True), ("R2", HAIKU, lambda b: True),
                   ("R6", SONNET, "R2")])
    SEM_PENSAR = {"thinking": {"type": "disabled"}}
    if plano_nome == "pensamento":       # AJUSTE 2: o mesmo Sonnet, com e sem pensamento
        plano = [("S", SONNET, lambda b: True, {}), ("Sn", SONNET, lambda b: True, SEM_PENSAR)]
    if plano_nome == "sem_pensamento":   # AJUSTE 2b: só o braço sem pensamento
        plano = [("Sn", SONNET, lambda b: True, SEM_PENSAR)]
    plano = [p if len(p) == 4 else (*p, {}) for p in plano]
    try:
        for nome, modelo, filtro, kw in plano:
            if isinstance(filtro, str):          # escalonamento: os recusados daquela rodada
                filtro = recusados(filtro)
            t0 = time.time()
            res[nome] = await R.rodada(nome, modelo, _em_lotes(grupos, filtro), kw)
            print(f"{nome} {modelo}: {len(res[nome])} chamadas em {time.time() - t0:.0f}s · "
                  f"gasto US$ {med.gasto:.4f} · pico {med.pico:.4f}", flush=True)
    except (OrcamentoEsgotado, GarantiaViolada, RuntimeError) as e:
        parada = repr(e)
        res[nome] = getattr(R, "parcial", [])
        print(f"PARADA em {nome}: {parada} ({len(res[nome])} chamadas desta rodada guardadas)", flush=True)
    (pasta / "rodadas.json").write_text(json.dumps(
        {"parada": parada, "trad_ok": trad_ok, "rodadas": res, "gasto": med.gasto,
         "pico": med.pico, "violacoes": med.violacoes, "recusas": med.recusas},
        ensure_ascii=False, indent=1), encoding="utf-8")
    med.arq.close()


class _IAFalsa:
    """Para a demonstração grátis: responde a decisão gravada da produção, com consumo
    fictício dentro do limite. Prova a contabilidade e o relatório, não a qualidade."""

    def __init__(self, grupos):
        self.b = {b["codigo"]: b for g in grupos for b in g["blocos"]}
        self.messages = self

    def stream(self, model, max_tokens, system, messages, **kw):
        import types
        txt = messages[0]["content"][0]["text"]
        ls = []
        for c in COD.findall(txt):
            ia = self.b[c]["producao_ia"]
            ls.append(f"{c}\t{ia['esporte']}\t{ia['aposta']}\t{ia['descricao']}")
        corpo = "```tsv\n" + "\n".join(ls) + "\n```"
        uso = types.SimpleNamespace(input_tokens=1500, output_tokens=200 * len(ls),
                                    cache_read_input_tokens=36000, cache_creation_input_tokens=0)

        class _S:
            async def __aenter__(s):
                return s

            async def __aexit__(s, *a):
                return False

            @property
            async def text_stream(s):
                yield corpo

            async def get_final_message(s):
                return types.SimpleNamespace(stop_reason="end_turn", usage=uso,
                                             content=[types.SimpleNamespace(type="text", text=corpo)])
        return _S()


def executar(amostra, teto, margem, simular, ajuste=None, plano_nome=None):
    if ajuste:
        cods = json.loads(pathlib.Path(ajuste).read_text(encoding="utf-8"))
        corpo = {"grupos": cods["grupos"], "manifesto": _sha(json.dumps(cods["grupos"], sort_keys=True))}
        pasta = SAIDA / (("sim_" if simular else "") + (plano_nome or "ajuste") + "_" + corpo["manifesto"][:8])
    else:
        corpo = carregar(pathlib.Path(amostra))
        pasta = SAIDA / (("sim_" if simular else "") + "teste_" + corpo["manifesto"][:12])
    trava = pasta / "INICIADA"
    if trava.exists():
        raise SystemExit(f"Já executado ({pasta}). Não repito: use `relatar`.")
    pasta.mkdir(parents=True, exist_ok=True)
    trava.write_text(datetime.now().isoformat(), encoding="utf-8")
    (pasta / "criterios.json").write_text(json.dumps(
        {"criterios": CRITERIOS, "teto": teto, "margem": margem, "simulada": simular,
         "amostra": str(amostra or ajuste), "registrado_em": datetime.now().isoformat()},
        ensure_ascii=False, indent=1), encoding="utf-8")
    os.environ.pop("DATABASE_URL", None)
    os.environ.pop("DATABASE_PUBLIC_URL", None)
    asyncio.run(_executar(corpo if ajuste else pathlib.Path(amostra), teto, margem, pasta, simular,
                          ajuste_cods=True if ajuste else None, plano_nome=plano_nome))
    print("pasta:", pasta)


# ── relatar ───────────────────────────────────────────────────────────────────

CUSTO_ATUAL_MEDIDO = 0.0221   # US$/bloco do caminho atual, MEDIDO na validação de 24/09 (Bet365)


def _cp(k, n, conf=0.95):
    from scipy.stats import beta
    if n == 0:
        return (0.0, 1.0)
    a = (1 - conf) / 2
    lo = 0.0 if k == 0 else beta.ppf(a, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a, k + 1, n - k)
    return (float(lo), float(hi))


def _veredito(k, n, barra):
    lo, hi = _cp(k, n)
    return "APROVADO" if hi < barra else "REPROVADO" if lo > barra else "INCONCLUSIVO"


def _boot_dif(pares, it=10000):
    """IC 95% da diferença pareada (A errado − B errado)/n por bootstrap dos blocos."""
    import random
    rnd = random.Random(386)
    n = len(pares)
    if not n:
        return (0.0, 0.0, 0.0)
    ds = []
    for _ in range(it):
        s = sum(pares[rnd.randrange(n)] for _ in range(n))
        ds.append(s / n)
    ds.sort()
    return (sum(pares) / n, ds[int(0.025 * it)], ds[int(0.975 * it)])


def relatar(pasta: pathlib.Path, amostra: pathlib.Path | None, reaplicar: bool = False):
    import logging
    logging.disable(logging.WARNING)
    import tradutor as trad
    import juiz_fonte_bet365 as J
    rod = json.loads((pasta / "rodadas.json").read_text(encoding="utf-8"))
    crit = json.loads((pasta / "criterios.json").read_text(encoding="utf-8"))
    if amostra is None:
        amostra = pathlib.Path(crit["amostra"])
    corpo = json.loads(amostra.read_text(encoding="utf-8"))
    blocos = {b["codigo"]: b for g in corpo["grupos"] for b in g["blocos"]}
    revisao = {}
    rp = pasta / "revisao.json"
    if rp.exists():
        revisao = json.loads(rp.read_text(encoding="utf-8"))
    chamadas = [json.loads(l) for l in open(pasta / "chamadas.jsonl", encoding="utf-8")]
    custo_r, cham_r, sem_uso = defaultdict(float), defaultdict(int), defaultdict(int)
    for c in chamadas:
        r = str(c.get("lote", "")).split(":")[0]
        custo_r[r] += c.get("custo", 0.0) if not c.get("recusada") else 0.0
        cham_r[r] += 0 if c.get("recusada") else 1
        sem_uso[r] += bool(c.get("custo_e_reserva"))
    dec = {r: {c: d for l in v for c, d in l["decisoes"].items()} for r, v in rod["rodadas"].items()}
    sufixo = ""
    if reaplicar:
        # Reaplica o portão ATUAL do contrato às respostas CRUAS gravadas (sem chamada nova):
        # mede o efeito de uma regra de CÓDIGO sobre as mesmas respostas, igual para todos.
        import contrato_texto as ct
        import taxonomia
        esp, cat = set(taxonomia.esportes_canonicos()), set(taxonomia.categorias_canonicas())
        for r, dd in dec.items():
            for c, d in dd.items():
                if d.get("cru"):
                    lt = ct.ler_numeros(c, blocos[c]["bruto"])
                    e2, a2, _aj, mot = ct.aceitar_4campos(lt, *d["cru"], esp, cat)
                    d["final"], d["motivo"] = [e2, a2, d["cru"][2]], mot
        sufixo = "_portao_atual"

    def aceito(r, c):
        d = dec.get(r, {}).get(c)
        return d if d and not d["motivo"] else None

    trad_cache = {c: trad.traduzir("BET365", b["bruto"]) for c, b in blocos.items()}
    julg_cache = {}

    def julgar(c, esp, ap, desc):
        k = (c, esp, ap, desc)
        if k not in julg_cache:
            r = J.julgar(blocos[c]["bruto"], esp, ap, desc)
            achados = r["achados"]
            erro = [x for x in achados if x[0] == "erro_real"]
            chave = "|".join(k)
            rv = revisao.get(chave)
            if erro and rv in ("alarme_falso", "forma", "nao_verificavel", "artefato_corte"):
                erro = []
            julg_cache[k] = {"erro": bool(erro), "motivos": [x[1] for x in erro],
                             "nao_verif": any(x[0] == "nao_verificavel" for x in achados),
                             "revisado": rv}
        return julg_cache[k]

    def fluxo(nome, etapas):
        """etapas: lista de (rótulo, função c -> (esp, ap, desc) ou None)."""
        por_etapa, erros, nv, fim = defaultdict(int), [], 0, {}
        for c in blocos:
            for rot, f in etapas:
                r = f(c)
                if r:
                    break
            else:
                rot = "caminho atual"
                ia = blocos[c]["producao_ia"]
                r = (ia["esporte"] or "", ia["aposta"] or "", ia["descricao"] or "")
            por_etapa[rot] += 1
            j = julgar(c, *r)
            fim[c] = (rot, r, j)
            if j["erro"]:
                erros.append({"codigo": c, "etapa": rot, "saida": r, "motivos": j["motivos"],
                              "revisado": j["revisado"]})
            elif j["nao_verif"]:
                nv += 1
        return {"por_etapa": dict(por_etapa), "erros": erros, "nao_verificaveis": nv, "fim": fim}

    T = lambda c: ((trad_cache[c].esporte, trad_cache[c].aposta, trad_cache[c].descricao)
                   if trad_cache[c].ok else None)
    M = lambda r: (lambda c: tuple(aceito(r, c)["final"]) if aceito(r, c) else None)
    FLUXOS = {
        "A0 caminho atual (produção hoje)": [],
        "A1 Sonnet enxuto em tudo": [("Sonnet", M("R1"))],
        "A2 Haiku enxuto em tudo + Sonnet nos recusados": [("Haiku", M("R2")), ("Sonnet (escalado)", M("R6"))],
        "A3 tradutor + Sonnet no resto": [("tradutor", T), ("Sonnet", M("R3"))],
        "A4 tradutor + Haiku no resto + Sonnet nos recusados": [("tradutor", T), ("Haiku", M("R4")),
                                                                ("Sonnet (escalado)", M("R5"))]}
    CUSTO_RODADAS = {"A0 caminho atual (produção hoje)": [], "A1 Sonnet enxuto em tudo": ["R1"],
                     "A2 Haiku enxuto em tudo + Sonnet nos recusados": ["R2", "R6"],
                     "A3 tradutor + Sonnet no resto": ["R3"],
                     "A4 tradutor + Haiku no resto + Sonnet nos recusados": ["R4", "R5"]}
    n = len(blocos)
    out = {"parada": rod["parada"], "gasto_total_medido": rod["gasto"], "pico": rod["pico"],
           "violacoes": rod["violacoes"], "custo_por_rodada": dict(custo_r),
           "chamadas_por_rodada": dict(cham_r), "chamadas_sem_consumo": dict(sem_uso),
           "blocos": n, "fluxos": {}, "comparacoes": {}}
    for nome, etapas in FLUXOS.items():
        f = fluxo(nome, etapas)
        k = len(f["erros"])
        n_atual = f["por_etapa"].get("caminho atual", 0)
        medido = sum(custo_r[r] for r in CUSTO_RODADAS[nome])
        projetado = n_atual * CUSTO_ATUAL_MEDIDO
        corretos = n - k
        out["fluxos"][nome] = {
            "por_etapa": f["por_etapa"], "blocos_com_erro": k, "taxa_erro": k / n,
            "ic95": _cp(k, n), "veredito": {str(b): _veredito(k, n, b) for b in CRITERIOS["barras"]},
            "nao_verificaveis_sem_erro": f["nao_verificaveis"],
            "chamadas": sum(cham_r[r] for r in CUSTO_RODADAS[nome]),
            "custo_medido_usd": medido, "custo_caminho_atual_projetado_usd": projetado,
            "usd_por_bloco": (medido + projetado) / n,
            "usd_por_bloco_correto": (medido + projetado) / corretos if corretos else None,
            "erros": f["erros"]}
        out["fluxos"][nome]["_fim"] = {c: [v[0], list(v[1]), v[2]["erro"]] for c, v in f["fim"].items()}

    def comparar(ra, rb, filtro, rotulo):
        pares, ka, kb, nn = [], 0, 0, 0
        for c in blocos:
            if not filtro(c):
                continue
            da, db = dec.get(ra, {}).get(c), dec.get(rb, {}).get(c)
            if da is None or db is None:
                continue
            nn += 1
            ea = (not da.get("final")) or julgar(c, *da["final"])["erro"]
            eb = (not db.get("final")) or julgar(c, *db["final"])["erro"]
            ka += ea
            kb += eb
            pares.append(int(ea) - int(eb))
        dif, lo, hi = _boot_dif(pares)
        out["comparacoes"][rotulo] = {
            "blocos": nn, ra + "_erro_ou_sem_linha": ka, rb + "_erro_ou_sem_linha": kb,
            "dif_pareada": dif, "ic95_dif": [lo, hi],
            "haiku_encerrado_neste_papel": lo > 0.01, "haiku_nao_inferior_1pp": hi <= 0.01}
    comparar("R2", "R1", lambda c: True, "Haiku x Sonnet, TODOS os blocos (R2 x R1)")
    comparar("R4", "R3", lambda c: not trad_cache[c].ok, "Haiku x Sonnet, só o que o tradutor NÃO resolve (R4 x R3)")
    comparar("R1", "R3", lambda c: not trad_cache[c].ok, "Sonnet em lote cheio x Sonnet só no resíduo (R1 x R3)")
    # a revisão: todo achado de erro real, único, com a seleção da fonte ao lado
    pend = {}
    for nome, f in out["fluxos"].items():
        for e in f["erros"]:
            chave = "|".join([e["codigo"], *e["saida"]])
            pend.setdefault(chave, {"fluxos": [], "motivos": e["motivos"], "revisado": e["revisado"],
                                    "fonte": [l.strip() for l in blocos[e["codigo"]]["bruto"].splitlines()
                                              if l.strip().startswith("•") or l.strip().startswith("–")]})
            pend[chave]["fluxos"].append(nome[:2] + ":" + e["etapa"])
    for r in ("R1", "R2", "R3", "R4"):
        for c, d in dec.get(r, {}).items():
            if d.get("final"):
                j = julgar(c, *d["final"])
                if j["erro"]:
                    chave = "|".join([c, *d["final"]])
                    pend.setdefault(chave, {"fluxos": [], "motivos": j["motivos"], "revisado": j["revisado"],
                                            "fonte": [l.strip() for l in blocos[c]["bruto"].splitlines()
                                                      if l.strip().startswith("•") or l.strip().startswith("–")]})
                    pend[chave]["fluxos"].append(r)
    (pasta / f"achados_para_revisao{sufixo}.json").write_text(json.dumps(pend, ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / f"relatorio{sufixo}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gasto medido US$ {rod['gasto']:.4f} · parada {rod['parada']} · por rodada "
          f"{ {k: round(v, 4) for k, v in custo_r.items()} } · sem consumo {dict(sem_uso)}")
    for nome, f in out["fluxos"].items():
        lo, hi = f["ic95"]
        print(f"\n{nome}\n   etapas {f['por_etapa']} · chamadas {f['chamadas']}\n   erro {f['blocos_com_erro']}/{n} = "
              f"{100 * f['taxa_erro']:.1f}% [IC95 {100 * lo:.1f}–{100 * hi:.1f}] · não verificável {f['nao_verificaveis_sem_erro']}"
              f" · {f['veredito']}\n   US$ medido {f['custo_medido_usd']:.4f} + atual projetado "
              f"{f['custo_caminho_atual_projetado_usd']:.4f} = {f['usd_por_bloco']:.5f}/bloco")
    for k, v in out["comparacoes"].items():
        print(f"\n{k}: {v}")
    rev = sum(1 for v in pend.values() if v["revisado"])
    print(f"\nachados de erro real únicos: {len(pend)} (revisados {rev}) -> achados_para_revisao.json")


def main_cli():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("congelar")
    c.add_argument("--alvo", type=int, default=720)
    c.add_argument("--dias", type=int, default=30)
    c.add_argument("--excluir", required=True, help="JSON com a lista de códigos de AJUSTE")
    c.add_argument("--teto-dono", type=float, default=0.35)
    c.add_argument("--formato-novo", action="store_true")
    c.add_argument("--prefixo", default="teste")
    for nome in ("executar", "simular"):
        e = sub.add_parser(nome)
        e.add_argument("--amostra")
        e.add_argument("--ajuste", help="JSON {'grupos': [...]} com blocos de AJUSTE")
        e.add_argument("--teto", type=float, required=True)
        e.add_argument("--margem", type=float, default=0.25)
        e.add_argument("--plano", default=None, help="pensamento = Sonnet com e sem pensamento")
    rl = sub.add_parser("relatar")
    rl.add_argument("--pasta", required=True)
    rl.add_argument("--amostra")
    rl.add_argument("--reaplicar-portao", action="store_true")
    a = ap.parse_args()
    if a.cmd == "relatar":
        relatar(pathlib.Path(a.pasta), pathlib.Path(a.amostra) if a.amostra else None,
                a.reaplicar_portao)
    elif a.cmd == "congelar":
        asyncio.run(congelar(a.alvo, a.dias, pathlib.Path(a.excluir), a.teto_dono,
                             a.formato_novo, a.prefixo))
    else:
        executar(a.amostra, a.teto, a.margem, a.cmd == "simular", a.ajuste, a.plano)


if __name__ == "__main__":
    main_cli()
