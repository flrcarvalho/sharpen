"""s415 (T1): o jogador fora da chave. Mede, SÓ COM SELECT, a cobertura da Ficha na captura de
13/10/2026 (virada_log ids 14 a 21) com o dicionário que existia ANTES dela, e quantas chaves
atuais se fundem.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_jogador_chave.py [--app DIR] [--fusoes OLD]

`--app DIR` = a pasta de onde vêm `descricao_ficha.py` e `dicionario.py` (padrão: `app/`); rode
uma vez com a cópia da versão anterior e outra com a atual, e compare. `--fusoes OLD` = a pasta
da versão anterior: conta as chaves dela que viram UMA chave na versão de `--app`.
`--decidir-fundidas` = simula as chaves fundidas que ficaram contraditas decididas pela mais
votada (quem decide de verdade é o Feca, por `corrigir_termo`).

Resultado em 13/10/2026 (s415), 154 códigos: 59 pela Ficha com a s414, 65 com a s415, 77 com as
3 fundidas contraditas decididas (`Ressaltos`/`Rebotes`/`Rebounds` na DEX é a maior).

Treino = os pares (cru × decisão da IA) com o bilhete criado ANTES de `CORTE` (o começo da
captura). Teste = os códigos que a virada processou nas capturas 14 a 21 (`ficha_virada`
atualizada na janela de cada uma), cada um com o cru mais recente até aquela captura. Resolvido
= esporte e categoria traduzidos, no Master, e descrição montada (`virada.aplicar`, sem gravar).
Limite: treina com a decisão da IA que JÁ estava no banco antes do corte; o que a semente
aprendeu durante a própria captura (a rodada depois de cada `/extrair`) não entra, e por isso
a medição é a de "o que a Ficha teria feito naquela hora".
"""
import argparse
import asyncio
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORTE = datetime(2026, 10, 13, 15, 50, tzinfo=timezone.utc)
LOGS = range(14, 22)


def _carregar_env():
    for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith("DATABASE_URL=") and "DATABASE_URL" not in os.environ:
            os.environ["DATABASE_URL"] = l.split("=", 1)[1].strip().strip('"').strip("'")


def _modulo(nome, pasta):
    spec = importlib.util.spec_from_file_location(nome, Path(pasta) / "descricao_ficha.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _termos(unanimes, feca, casa):
    """Como `dicionario.carregar`: semente `*` < semente da casa < Feca `*` < Feca da casa."""
    t = {}
    for c in ("*", casa):
        for (cc, tipo, termo), (v, _) in unanimes.items():
            if cc == c:
                t[(tipo, termo)] = v
    for c in ("*", casa):
        for (cc, tipo, termo), v in feca.items():
            if cc == c:
                t[(tipo, termo)] = v
    return t


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default=str(ROOT / "app"))
    ap.add_argument("--fusoes", default="")
    ap.add_argument("--decidir-fundidas", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(ROOT / "app"))
    sys.path.insert(0, a.app)
    _carregar_env()
    import dicionario
    import ficha
    import virada
    from database import get_pool
    print("módulos de:", Path(dicionario.__file__).parent)
    pool = await get_pool()
    async with pool.acquire() as c:
        tem_origem = await c.fetchval(
            "SELECT count(*) FROM information_schema.columns WHERE table_name = 'correcoes' "
            "AND column_name = 'origem'")

        class _Antes:
            """Antes do deploy da s415 a coluna `correcoes.origem` não existe: tira o filtro
            dela (sem ela, nenhuma linha é automática, e o resultado é o mesmo)."""
            async def fetch(self, sql, *a):
                return await c.fetch(sql.replace("AND c.origem IS DISTINCT FROM 'ficha'", ""), *a)
        pares, texto, _ = await dicionario.pares(c if tem_origem else _Antes())
        depois = {r["codigo_bilhete"] for r in await c.fetch(
            "SELECT codigo_bilhete FROM bilhetes WHERE criado_em >= $1 "
            "AND codigo_bilhete IS NOT NULL", CORTE)}
        treino = [x for x in pares if x[1].get("codigo") not in depois]
        unanimes, contraditos, _ = dicionario.votar(treino, texto)
        feca = {(r["casa"], r["tipo"], r["termo_casa"]): r["termo_sharpen"] for r in await c.fetch(
            "SELECT casa, tipo, termo_casa, termo_sharpen FROM dicionario_termos "
            "WHERE origem = 'feca'")}
        fk = [(cc, t, k) for cc, t, k in feca]
        unanimes = {k: v for k, v in unanimes.items() if not dicionario.coberto_pelo_feca(fk, *k)}
        fundidas = {k: c_ for k, c_ in contraditos.items() if "{jogador}" in k[2] or "{hc}" in k[2]}
        if fundidas:
            print(f"chaves fundidas CONTRADITAS (a IA escreve o mesmo mercado de jeitos "
                  f"diferentes): {len(fundidas)}")
            for k, c_ in sorted(fundidas.items()):
                print(f"   {k[0]} {k[2]}: {dict(c_)}")
        if a.decidir_fundidas:
            # o que a cobertura seria se cada uma fosse decidida (a mais votada; quem decide de
            # verdade é o Feca, por `corrigir_termo`)
            for k, c_ in fundidas.items():
                unanimes[k] = (c_.most_common(1)[0][0], sum(c_.values()))
            print("(simulação: as fundidas contraditas decididas pela mais votada)")
        por_tipo = Counter(t for _, t, _ in unanimes)
        print(f"treino: {len(treino)} pares (de {len(pares)}); termos {dict(por_tipo)}; "
              f"contraditos {dict(Counter(t for _, t, _ in contraditos))}")
        # o teste: os códigos de cada captura 14..21
        res = defaultdict(Counter)
        exemplos = defaultdict(list)
        for lg in await c.fetch("SELECT * FROM virada_log WHERE id = ANY($1::bigint[]) ORDER BY id",
                                list(LOGS)):
            casa, dono, t = lg["casa"], lg["dono"], lg["criado_em"]
            cods = await c.fetch(
                "SELECT codigo, estado, motivo FROM ficha_virada WHERE dono = $1 AND casa = $2 "
                "AND atualizado_em BETWEEN $3::timestamptz - interval '3 minutes' AND $3::timestamptz + interval '5 seconds'",
                dono, casa, t)
            termos = _termos(unanimes, feca, casa)
            for r in cods:
                cru = await c.fetchrow(
                    "SELECT familia, cru::text AS cru FROM captura_crua WHERE dono = $1 AND casa = $2 "
                    "AND codigo = $3 AND recebido_em <= $4::timestamptz + interval '5 seconds' "
                    "ORDER BY id DESC LIMIT 1", dono, casa, r["codigo"], t)
                if not cru:
                    res[casa]["sem cru"] += 1
                    continue
                f, motivos = ficha.montar_ficha(cru["familia"], json.loads(cru["cru"]), casa)
                res[casa]["códigos"] += 1
                if f is None or motivos:
                    res[casa]["Ficha recusada"] += 1
                    continue
                esp, cat, faltam = dicionario.traduzir(f, termos)
                if faltam:
                    res[casa]["termo fora"] += 1
                    exemplos[(casa, "termo")].append(faltam[-1][1])
                    continue
                if not virada.no_master(esp, cat):
                    res[casa]["fora do Master"] += 1
                    continue
                d = virada.descricao(f, termos)
                if not d:
                    res[casa]["descrição fora"] += 1
                    import descricao_ficha
                    exemplos[(casa, "desc")] += descricao_ficha.montar(f, termos, None)[1][:1]
                    continue
                res[casa]["pela Ficha"] += 1
        tot = Counter()
        print(f"\n{'casa':<11} {'códigos':>7} {'pela Ficha':>10} {'termo fora':>10} "
              f"{'descr. fora':>11} {'recusada':>8}")
        for casa in sorted(res):
            r = res[casa]
            tot.update(r)
            print(f"{casa:<11} {r['códigos']:>7} {r['pela Ficha']:>10} {r['termo fora']:>10} "
                  f"{r['descrição fora']:>11} {r['Ficha recusada']:>8}")
        print(f"{'TOTAL':<11} {tot['códigos']:>7} {tot['pela Ficha']:>10} {tot['termo fora']:>10} "
              f"{tot['descrição fora']:>11} {tot['Ficha recusada']:>8}")
        print("\nchaves que faltaram (amostra):")
        for (casa, tipo), ks in sorted(exemplos.items()):
            for k, n in Counter(ks).most_common(6):
                print(f"   {casa} {tipo}: {n}× {k}")
        if a.fusoes:
            velho = _modulo("descricao_ficha_velho", a.fusoes)
            import descricao_ficha as novo
            grupos = defaultdict(set)
            for casa, f, *_ in pares:
                for p in f.get("pernas") or []:
                    kv = velho.chave(p)
                    dn = novo.decompor(p)
                    kn = novo.chave(p, dn, jogador=bool(dn["jogador"]))
                    grupos[(casa, kn)].add(kv)
            fund = {k: v for k, v in grupos.items() if len(v) > 1}
            print(f"\nfusões de DESCRIÇÃO: {sum(len(v) for v in fund.values())} chaves antigas "
                  f"viram {len(fund)} chaves novas")
            por_casa = Counter()
            for (casa, kn), v in fund.items():
                por_casa[casa] += len(v)
            print("   por casa:", dict(por_casa))
            for (casa, kn), v in sorted(fund.items(), key=lambda x: -len(x[1]))[:12]:
                print(f"   {casa} {kn}  ← {len(v)}")
            # categoria: o par mercado | seleção e o mercado com jogador
            gc = defaultdict(set)
            spec = importlib.util.spec_from_file_location("dicionario_velho",
                                                          Path(a.fusoes) / "dicionario.py")
            dv = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dv)
            for casa, f, *_ in pares:
                ps = f.get("pernas") or []
                if f.get("tipo") != "simples" or len(ps) != 1:
                    continue
                p = ps[0]
                kv = dv.normalizar(p.get("mercado_casa")) + dv.SEP + dv.sel_chave(p.get("selecao_casa"))
                gc[(casa, dicionario._par(p))].add(kv)
                if (mj := dicionario._merc_jogador(p)):
                    gc[(casa, mj)].add(dv.normalizar(p.get("mercado_casa")))
            fc = {k: v for k, v in gc.items() if len(v) > 1}
            print(f"fusões de CATEGORIA: {sum(len(v) for v in fc.values())} chaves antigas viram "
                  f"{len(fc)} chaves novas")
            for (casa, kn), v in sorted(fc.items(), key=lambda x: -len(x[1]))[:8]:
                print(f"   {casa} {kn}  ← {len(v)}")


if __name__ == "__main__":
    asyncio.run(main())
