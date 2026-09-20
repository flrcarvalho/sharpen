# -*- coding: utf-8 -*-
"""Gera `src/dados.json` a partir do Postgres. LEITURA PURA: só SELECT.

Por que existe: o cartão de prova do vídeo mostra o número REAL da base do depoente.
Digitar esse número à mão é como reimplementar o código dentro do teste — no dia em
que a base muda, a peça mente com cara de exatidão. Aqui o número vem do banco, e
re-renderizar o vídeo é um comando.

Uso (precisa da env DATABASE_URL, a mesma que o app usa; o .env do repo serve):
    python gerar_dados.py

O que NÃO sai daqui, de propósito: e-mail, valor de custo em R$, nome de fornecedor,
nome de tipster e qualquer coisa que identifique terceiro. O cartão é do depoente, com
autorização dele, e mais ninguém.
"""
import asyncio
import json
import os
import re
from datetime import date
from pathlib import Path

import asyncpg

RAIZ = Path(__file__).resolve().parents[3]          # .../Planilhador
SAIDA = Path(__file__).parent / "src" / "dados.json"

MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")

# Falas que vêm do DEPOIMENTO, não do banco. Ficam aqui com a fonte anotada para
# ninguém confundir número medido com número declarado.
FRASES = {
    # docs/marketing/depoimentos/transcricoes/jonathan-2026-09-19.txt, 00:26
    "Jonathan": {"antes": "Antes: 1 hora por dia.", "depois": "Hoje: 15 a 20 minutos."},
    # germano-2026-09-20.txt, audio 1 (00:10) e audio 2 (00:16)
    "germano": {"antes": "Nenhum planilhador durou 3 dias.",
                "depois": "Este durou 3 semanas, com 13 casas."},
}

DONOS = ["Jonathan", "germano"]

# O `dono` é o USERNAME; o cartão mostra o nome como a pessoa escreve o próprio nome.
# Title-case automático mutilaria nome de marca, então isto é um mapa, não uma regra.
NOMES = {"germano": "Germano"}


def carregar_env() -> None:
    if os.environ.get("DATABASE_URL"):
        return
    env = RAIZ / ".env"
    for linha in env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def num(s) -> float:
    """Stake é TEXT e mistura convenção BR e EN na mesma coluna.

    Régua do projeto (`parseNum`): o ÚLTIMO separador é o decimal, e um separador só é
    sempre decimal. A regra "3 dígitos = milhar" está certa para dinheiro digitado e
    erra feio aqui, então não é usada.
    """
    if not s:
        return 0.0
    t = re.sub(r"[^0-9,.\-]", "", str(s))
    if not t:
        return 0.0
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


async def do_dono(con, dono: str) -> dict:
    async def val(q):
        return await con.fetchval(q, dono)

    primeira = await val("select min(criado_em)::date from bilhetes where dono = $1")
    stakes = await con.fetch("select stake from bilhetes where dono = $1", dono)

    return {
        "nome": NOMES.get(dono, dono),
        "desde": f"usa o Sharpen desde {MESES[primeira.month - 1]} de {primeira.year}",
        "medido_em": date.today().strftime("%d/%m/%Y"),
        "apostas": await val("select count(*) from bilhetes where dono = $1"),
        "apostas_30d": await val(
            "select count(*) from bilhetes where dono = $1 "
            "and criado_em > now() - interval '30 days'"),
        "casas": await val("select count(distinct casa) from bilhetes where dono = $1"),
        "contas": await val("select count(*) from parceiros where dono = $1"),
        "tipsters": await val(
            "select count(*) from tipsters where dono = $1 and not arquivado"),
        "dias_90": await val(
            "select count(distinct criado_em::date) from bilhetes where dono = $1 "
            "and criado_em > now() - interval '90 days'"),
        "turnover": round(sum(num(r["stake"]) for r in stakes)),
        **FRASES.get(dono, {"antes": "", "depois": ""}),
    }


async def main() -> None:
    con = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        dados = {d.lower(): await do_dono(con, d) for d in DONOS}
    finally:
        await con.close()

    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8", newline="\n")
    for chave, d in dados.items():
        print(f"{chave}: {d['apostas']} apostas, {d['casas']} casas, "
              f"{d['contas']} contas, turnover {d['turnover']}")
    print(f"-> {SAIDA}")


carregar_env()
asyncio.run(main())
