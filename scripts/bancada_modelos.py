"""Bancada de modelos: replay sobre a sombra, com juiz DETERMINISTICO.

    python scripts/bancada_modelos.py     # precisa do .env (DATABASE_URL + ANTHROPIC_API_KEY)

Compara modelos sobre blocos REAIS ja gravados na `sombra_rotulos`, pelo caminho de
producao (mesmo `build_system`, mesma `_INSTRUCAO`, mesmo fatiamento de 6 por chamada).
Nao toca producao: le a sombra, chama a API, imprime e grava um json ao lado.

**CUSTA DINHEIRO** (uns US$ 10 com a amostra padrao) e leva uns 10 minutos. O juiz nunca e'
a IA: sao `checar_descricao`, `checar_fidelidade` e `codigos_do_texto`, os mesmos que rodam
em producao.

CORRIGE DOIS DEFEITOS DA 1a BANCADA (s377), que produziram DOIS numeros falsos e
reprovaram um modelo por engano — ver `docs/CASOS.md`, "a bancada que condenou o modelo
errado":

  1. **Lotes reais, nao sorteados.** Antes eu montava o lote com 6 bilhetes sorteados
     de dias diferentes; bilhete parecido lado a lado e' o que faz um modelo fundir
     dois num so. Agora sao 6 blocos CONSECUTIVOS de uma extracao real.
  2. **Parceiro real, nao "(nao informado)".** Com a coluna 5 vazia o modelo perde a
     conta das colunas e come a coluna vazia seguinte. Producao sempre manda o nome
     da conta.

O estrago dos dois: o Haiku foi reprovado por "19 codigos inventados" e "8,7% de
bilhetes perdidos". Com a bancada corrigida ele inventa ZERO e perde ZERO (180 blocos
-> 180 linhas). **Os dois numeros eram meus, nao dele.**

LICAO, e ela vale mais que a tabela: eu construi uma bancada e confiei nela sem
valida-la contra um caso conhecido. A pista existia — a producao mostra 0,2% de orfas
e a bancada dizia 3,6% — e eu usei essa pista so para absolver o Sonnet 5, sem voltar
para reexaminar a condenacao do Haiku com a mesma desconfianca.
"""
import asyncio
import json
import os
import sys
from collections import defaultdict
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "app"))

import asyncpg
from anthropic import AsyncAnthropic

import main as appmain
from prompts import build_system
from repository import parse_tsv, codigos_do_texto
from descricao_check import checar_descricao, checar_fidelidade

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODELOS = ["claude-sonnet-5", "claude-haiku-4-5", "claude-sonnet-4-6"]
PRECO = {
    "claude-sonnet-5":   (2.0, 10.0, 0.20, 4.00),
    "claude-haiku-4-5":  (1.0,  5.0, 0.10, 2.00),
    "claude-sonnet-4-6": (3.0, 15.0, 0.30, 6.00),
}
ALVO = {"Bet365": 24, "Betano": 12, "Superbet": 6, "Novibet": 4, "Betfair": 4}
POR_CHUNK = 6
PARCEIRO = "Feca [Eu]"

cliente = AsyncAnthropic()
sem = asyncio.Semaphore(6)
DIR = os.path.dirname(os.path.abspath(__file__))


async def montar(conn):
    lotes = []
    for casa, quantos in ALVO.items():
        rows = await conn.fetch(
            """SELECT dono, criado_em, codigo, bruto FROM sombra_rotulos
                WHERE casa=$1 AND criado_em >= $2 AND codigo <> ''
                ORDER BY criado_em, id""", casa, date(2026, 9, 10))
        porext = defaultdict(list)
        for r in rows:
            porext[(r["dono"], r["criado_em"])].append((r["codigo"], r["bruto"]))
        feitos = 0
        for g in sorted(porext.values(), key=len, reverse=True):
            vistos, limpo = set(), []
            for cod, b in g:
                if cod in vistos:
                    continue
                vistos.add(cod)
                limpo.append((cod, b))
            for i in range(0, len(limpo) - POR_CHUNK + 1, POR_CHUNK):
                if feitos >= quantos:
                    break
                lotes.append((casa, appmain._display_to_key(casa), limpo[i:i + POR_CHUNK]))
                feitos += 1
            if feitos >= quantos:
                break
    return lotes


async def chamar(modelo, casa_key, casa_disp, texto):
    system = build_system(casa_key)
    instr = {"type": "text", "text": appmain._INSTRUCAO.format(
        casa=casa_disp, parceiro=PARCEIRO,
        data_referencia=date.today().strftime("%d/%m/%Y"))}
    async with sem:
        for tent in range(3):
            try:
                async with cliente.messages.stream(
                    model=modelo, max_tokens=16000, system=system,
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": texto}, instr]}],
                ) as st:
                    async for _ in st.text_stream:
                        pass
                    fin = await st.get_final_message()
                u = fin.usage
                return ("".join(b.text for b in fin.content if b.type == "text"),
                        {"i": u.input_tokens, "o": u.output_tokens,
                         "cr": getattr(u, "cache_read_input_tokens", 0),
                         "cw": getattr(u, "cache_creation_input_tokens", 0)})
            except Exception as e:
                if tent == 2:
                    return "__ERRO__ %s" % e, None
                await asyncio.sleep(3 * (tent + 1))


async def main():
    dsn = os.environ["DATABASE_URL"].replace("postgres://", "postgresql://", 1)
    c = await asyncpg.connect(dsn)
    lotes = await montar(c)
    await c.close()
    print("%d lotes, %d blocos, parceiro=%r" % (
        len(lotes), sum(len(l) for _c, _k, l in lotes), PARCEIRO), flush=True)

    placar = {m: defaultdict(int) for m in MODELOS}
    custo = {m: 0.0 for m in MODELOS}

    for modelo in MODELOS:
        async def um(casa, casa_key, lote, modelo=modelo):
            texto = "\n\n".join("[C\u00f3digo: %s]\n%s" % (cod, b) for cod, b in lote)
            saida, tk = await chamar(modelo, casa_key, casa, texto)
            p = placar[modelo]
            p["blocos"] += len(lote)
            if tk:
                pi, po, pr, pw = PRECO[modelo]
                custo[modelo] += (tk["i"] * pi + tk["o"] * po
                                  + tk["cr"] * pr + tk["cw"] * pw) / 1e6
            if saida.startswith("__ERRO__"):
                p["erro"] += 1
                return
            linhas = appmain._extract_tsv_rows(saida)
            if not linhas:
                p["sem_tsv"] += 1
                return
            p["linhas"] += len(linhas)
            for l in linhas:
                if len(l.split("\t")) < 11:
                    p["coluna_comida"] += 1
            enviados = set(codigos_do_texto(texto))
            bruto_por_cod = dict(lote)
            devolvidos = set()
            for row in parse_tsv("\n".join(linhas)):
                cod = (row.get("codigo_bilhete") or "").strip()
                desc = row.get("descricao") or ""
                ap = row.get("aposta") or ""
                if cod and cod not in enviados:
                    p["codigo_inventado"] += 1
                    continue
                if cod:
                    devolvidos.add(cod)
                if not desc.strip():
                    continue
                p["descricoes"] += 1
                if [x for x in checar_descricao(ap, desc) if x[0] == "erro"]:
                    p["fora_do_master"] += 1
                bruto = bruto_por_cod.get(cod, "")
                if bruto and [x for x in checar_fidelidade(desc, bruto) if x[0] == "erro"]:
                    p["infiel"] += 1
            p["sem_codigo"] += len(enviados - devolvidos)

        await asyncio.gather(*(um(*l) for l in lotes))
        print("%s pronto - US$ %.2f" % (modelo, custo[modelo]), flush=True)

    print("\n" + "=" * 80)
    print("%-26s" % "" + "".join("%18s" % m.replace("claude-", "") for m in MODELOS))

    def linha(rot, f):
        print("%-26s" % rot + "".join("%18s" % f(placar[m]) for m in MODELOS))

    linha("blocos enviados", lambda p: p["blocos"])
    linha("LINHAS devolvidas", lambda p: p["linhas"])
    linha("bilhete PERDIDO", lambda p: p["blocos"] - p["linhas"])
    linha("codigo inventado", lambda p: p["codigo_inventado"])
    linha("coluna comida", lambda p: "%d (%.1f%%)" % (
        p["coluna_comida"], 100 * p["coluna_comida"] / max(p["linhas"], 1)))
    linha("desc fora do MASTER", lambda p: "%d (%.1f%%)" % (
        p["fora_do_master"], 100 * p["fora_do_master"] / max(p["descricoes"], 1)))
    linha("desc INFIEL", lambda p: "%d (%.1f%%)" % (
        p["infiel"], 100 * p["infiel"] / max(p["descricoes"], 1)))
    linha("sem bloco tsv", lambda p: p["sem_tsv"])
    print("%-26s" % "custo do teste US$" + "".join("%18.2f" % custo[m] for m in MODELOS))

    json.dump({"placar": {m: dict(placar[m]) for m in MODELOS}, "custo": custo},
              open(os.path.join(DIR, "bancada_modelos.json"), "w"), indent=2)


asyncio.run(main())
