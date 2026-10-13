"""Cobertura do dicionário de DESCRIÇÃO por casa (s413, 12/10/2026): o que a semente aprenderia
hoje do histórico, e quantas apostas com cru a Ficha descreveria sem a IA.
Banco: só SELECT. Sem IA, sem custo. Mesmo código da semente (`dicionario.pares` e `votar`).

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_descricao_cobertura.py [--holdout] [--difs]

Por casa:
  mercados    chaves de descrição que a semente grava (maioria de 90%); contraditos; revisão
  com cru     apostas com cru, Ficha aceita, par da IA (`bilhetes`, senão `sombra_rotulos`)
  descritas   a Ficha monta a descrição de todas as pernas (o resto vai para a IA com o motivo
              `descrição fora do dicionário`)
  = IA        a descrição montada é IGUAL à da IA, letra a letra (perna a perna, em qualquer
              ordem); a diferença que sobra é de estilo da própria IA (`Sobrenome, Nome`
              virado em metade das vezes, ` - ` entre time e linha, `1º Tempo` × `1ª Metade`)
              ou erro dela (time omitido no total do time, lado trocado), e `--difs` lista
  Ficha hoje  das apostas que a Ficha já resolve (esporte e categoria no dicionário), quantas
              ela continua resolvendo com a descrição (o resto passa a ir para a IA)

`--holdout`: aprende nos 70% mais antigos (pela ordem do cru) e mede nos 30% finais: o mercado
que só apareceu depois não está no dicionário, e é isso que a semente logo depois da IA cobre.
"""
import asyncio
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "app"))

import descricao_ficha  # noqa: E402
import dicionario  # noqa: E402
from database import get_pool  # noqa: E402


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _termos(unanimes: dict, feca: dict) -> dict:
    por_casa: dict = defaultdict(dict)
    for (c, t, k), (v, _) in unanimes.items():
        por_casa[c][(t, k)] = v
    for (c, t, k), v in feca.items():
        por_casa[c][(t, k)] = v
    return por_casa


def _medir(itens, por_casa, difs) -> dict:
    out: dict = defaultdict(Counter)
    for casa, f, _, _, desc_ia in itens:
        s = out[casa]
        termos = {**por_casa.get("*", {}), **por_casa.get(casa, {})}
        s["com cru"] += 1
        d, _ = descricao_ficha.montar(f, termos, dicionario.descricao_perna)
        _, _, faltam = dicionario.traduzir(f, termos)
        if not faltam:
            s["ficha hoje"] += 1
            s["ficha com descricao"] += bool(d)
        if not d:
            continue
        s["descritas"] += 1
        if sorted(d.split(" // ")) == sorted((desc_ia or "").split(" // ")):
            s["= IA"] += 1
        elif difs:
            print(f"  {casa}\n    Ficha: {d}\n    IA:    {desc_ia}")
    return out


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    holdout, difs = "--holdout" in sys.argv, "--difs" in sys.argv
    pool = await get_pool()
    async with pool.acquire() as conn:
        pares, texto, fontes = await dicionario.pares(conn)
        feca = {(r["casa"], r["tipo"], r["termo_casa"]): r["termo_sharpen"] for r in await conn.fetch(
            "SELECT casa, tipo, termo_casa, termo_sharpen FROM dicionario_termos "
            "WHERE origem = 'feca'")}
    itens = [x for x in pares if len(x) > 4 and x[4]]
    print(f"apostas com cru e par da IA: {len(itens)} (fontes: {fontes})\n")
    treino = itens[:int(len(itens) * 0.7)] if holdout else itens
    medido = itens[int(len(itens) * 0.7):] if holdout else itens
    unanimes, contraditos, revisao = dicionario.votar(treino, texto)
    por_casa = _termos(unanimes, feca)
    r = _medir(medido, por_casa, difs)
    n_desc = Counter(c for c, t, _ in unanimes if t == "descricao")
    n_contra = Counter(c for c, t, _ in contraditos if t == "descricao")
    n_rev = Counter(x["casa"] for x in revisao if x["tipo"] == "descricao")
    print(("HOLDOUT (aprende nos 70% mais antigos, mede nos 30% finais)\n" if holdout else "")
          + f"{'casa':11} {'mercados':>8} {'contra':>6} {'revisão':>7} {'com cru':>7} "
          f"{'descritas':>13} {'= IA':>11} {'Ficha hoje → com descrição':>28}")
    for casa in sorted(r):
        s = r[casa]
        pc = lambda a, b: f"{a} ({a / b:.0%})" if b else "0"  # noqa: E731
        print(f"{casa:11} {n_desc[casa]:>8} {n_contra[casa]:>6} {n_rev[casa]:>7} "
              f"{s['com cru']:>7} {pc(s['descritas'], s['com cru']):>13} "
              f"{pc(s['= IA'], s['descritas']):>11} "
              f"{s['ficha hoje']:>13} → {pc(s['ficha com descricao'], s['ficha hoje'])}")


if __name__ == "__main__":
    asyncio.run(main())
