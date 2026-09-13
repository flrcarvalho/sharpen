# -*- coding: utf-8 -*-
"""Importa o export anonimizado para a conta de demonstracao `/realtrial`.

ENSAIO E O PADRAO. Sem `--gravar` ele so conta o que faria e imprime uma
amostra para leitura humana; nada toca o banco.

    python scripts/realtrial/importar.py                 # ensaio
    python scripts/realtrial/importar.py --amostra 40    # ensaio com mais linhas
    python scripts/realtrial/importar.py --gravar        # grava de verdade
    python scripts/realtrial/importar.py --gravar --recriar   # apaga antes

TRES TRAVAS, porque isto escreve em PRODUCAO:
  1. o dono de destino tem de ser exatamente `realtrial` -- apontar para um
     dono real despejaria 48 mil bilhetes ficticios na base de alguem;
  2. recusa gravar se ja houver dado sob `realtrial`, a menos que `--recriar`;
  3. tudo numa transacao so: ou entra inteiro, ou nao entra nada.

O QUE **NAO** ENTRA, de proposito:
  · `caixa_mov`. A Caixa guarda em `abertas_corte` os IDS dos bilhetes abertos
    no instante da ativacao, e os ids mudam no import -- reconstruir isso e'
    exatamente o caso do script que inflou a projecao em R$ 10.477 (CLAUDE.md).
    Se a demo precisar de Caixa, liga-se pelo fluxo normal do app, que ja e' o
    caminho testado.
  · a linha em `usuarios`. Sessao e login sao da Fatia 3; criar conta logavel
    antes da hora so aumenta a superficie.
"""
import argparse
import asyncio
import io
import json
import pathlib
import random
import sys
from datetime import date, datetime, timezone

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "scripts" / "realtrial"))

import exportar as ex  # noqa: E402

DONO = ex.DONO_DESTINO
PADRAO = RAIZ / "Backups" / "realtrial" / "export.json"

COLS_BILHETE = [
    "casa", "parceiro", "assinatura", "data", "esporte", "tipster", "aposta",
    "descricao", "stake", "odd", "resultado", "extraction_state",
    "codigo_bilhete", "archived", "sistema", "sistema_linhas", "criado_em",
    "dono", "origem",
]

INSERT_BILHETE = f"""
    INSERT INTO bilhetes ({', '.join(COLS_BILHETE)})
    VALUES ({', '.join(f'${i}' for i in range(1, len(COLS_BILHETE) + 1))})
    -- A constraint REAL inclui o dono: `UNIQUE (dono, casa, parceiro,
    -- assinatura)`. O `database.py` mostra o CREATE TABLE original, sem ele;
    -- quem tem a verdade e' o banco (`pg_indexes`). Supor pelo arquivo deu
    -- InvalidColumnReferenceError no meio da gravacao.
    ON CONFLICT (dono, casa, parceiro, assinatura) DO NOTHING
"""
INSERT_PARCEIRO = """
    INSERT INTO parceiros (casa, nome, arquivado, adquirida_em, arquivada_em, dono)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (dono, casa, nome) DO NOTHING
"""
INSERT_TIPSTER = """
    INSERT INTO tipsters (nome, dono, casas, mercados, arquivado, stake_min, stake_max)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    ON CONFLICT (dono, nome) DO NOTHING
"""
INSERT_CUSTO = """
    INSERT INTO custo_store (dono, custo_tipster, custo_geral, custo_conta)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (dono) DO UPDATE SET
        custo_tipster = EXCLUDED.custo_tipster,
        custo_geral   = EXCLUDED.custo_geral,
        custo_conta   = EXCLUDED.custo_conta
"""


# ── conversao de tipo ────────────────────────────────────────────────────────
# O asyncpg NAO converte: o argumento vai no TIPO DA COLUNA (CLAUDE.md).
# DATE exige `datetime.date`, TIMESTAMPTZ exige `datetime`, INTEGER exige int.
# String levanta erro DENTRO do driver, antes de qualquer SQL rodar.
def _data(v) -> date | None:
    if not v:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    return date.fromisoformat(str(v)[:10])


def _instante(v) -> datetime:
    if not v:
        return datetime.now(timezone.utc)
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    d = datetime.fromisoformat(str(v))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _int(v) -> int | None:
    return None if v is None else int(v)


def linha_bilhete(b: dict) -> tuple:
    return (
        b["casa"], b["parceiro"], b["assinatura"], b["data"], b["esporte"],
        b["tipster"], b["aposta"], b["descricao"], b["stake"], b["odd"],
        b["resultado"], b["extraction_state"] or "aberta", b["codigo_bilhete"],
        bool(b["archived"]), b["sistema"], _int(b["sistema_linhas"]),
        _instante(b.get("criado_em")), DONO, "extracao",
    )


# ── ensaio ───────────────────────────────────────────────────────────────────
def amostra(dados: dict, n: int, semente: int = 7) -> str:
    """Linhas ao acaso, no formato da grade, para leitura humana.

    O ponto NAO e' conferir 48 mil bilhetes -- ninguem le isso, e a demo nao
    precisa ser perfeita para ensinar o sistema. E' bater o olho e ver se algo
    soa reconhecivel.
    """
    rng = random.Random(semente)
    escolhidas = rng.sample(dados["bilhetes"], min(n, len(dados["bilhetes"])))
    largura = (12, 22, 16, 14, 46, 9, 7, 4)
    cab = ("DATA", "CONTA", "CASA", "TIPSTER", "DESCRICAO", "STAKE", "ODD", "R")
    linhas = ["  ".join(c.ljust(w)[:w] for c, w in zip(cab, largura))]
    linhas.append("-" * (sum(largura) + 2 * (len(largura) - 1)))
    for b in escolhidas:
        vals = (b["data"] or "", b["parceiro"] or "", b["casa"] or "",
                b["tipster"] or "-", (b["descricao"] or "").replace("\n", " "),
                b["stake"] or "", b["odd"] or "", b["resultado"] or "-")
        linhas.append("  ".join(str(v).ljust(w)[:w] for v, w in zip(vals, largura)))
    return "\n".join(linhas)


async def _conectar(tentativas: int = 4):
    """Conexao com retry: o Railway oscila e a 1a tentativa estoura o timeout
    com frequencia (medido: falhou em 25s, conectou em 3,9s na seguinte).
    Sem isto, uma gravacao de 48 mil linhas morre por hipo de rede."""
    import asyncpg
    ultimo = None
    for i in range(1, tentativas + 1):
        try:
            return await asyncpg.connect(ex._database_url(), timeout=30)
        except Exception as e:                    # noqa: BLE001
            ultimo = e
            print(f"   conexao falhou ({type(e).__name__}), tentativa {i}/{tentativas}")
            await asyncio.sleep(2 * i)
    raise SystemExit(f"nao consegui conectar: {type(ultimo).__name__}: {ultimo}")


async def principal(caminho: pathlib.Path, gravar: bool, recriar: bool,
                    n_amostra: int) -> None:
    if DONO != "realtrial":
        raise SystemExit(f"TRAVA: dono de destino e' '{DONO}', nao 'realtrial'")

    dados = json.loads(caminho.read_text(encoding="utf-8"))
    print(f"# import -> {DONO}   (modo: {'GRAVAR' if gravar else 'ENSAIO'})")
    print(f"  arquivo: {caminho}")
    for k in ("bilhetes", "parceiros", "tipsters", "custos"):
        print(f"   {k}: {len(dados.get(k, [])):,}".replace(",", "."))

    conn = await _conectar()
    try:
        ja = {t: await conn.fetchval(f"SELECT count(*) FROM {t} WHERE dono = $1",
                                     DONO)
              for t in ("bilhetes", "parceiros", "tipsters", "custo_store")}
        print(f"\n  ja existe sob {DONO}: " +
              " · ".join(f"{k}={v}" for k, v in ja.items()))

        if not gravar:
            print(f"\n## amostra de {n_amostra} linhas (leitura humana)\n")
            print(amostra(dados, n_amostra))
            print("\nENSAIO: nada foi gravado. Use --gravar para valer.")
            return

        if any(ja.values()) and not recriar:
            raise SystemExit(
                f"\nRECUSADO: ja ha dado sob '{DONO}'. Use --recriar para apagar antes.")

        async with conn.transaction():
            if recriar:
                for t in ("bilhetes", "parceiros", "tipsters", "custo_store"):
                    n = await conn.execute(f"DELETE FROM {t} WHERE dono = $1", DONO)
                    print(f"   apagado {t}: {n}")

            await conn.executemany(
                INSERT_PARCEIRO,
                [(p["casa"], p["nome"], bool(p["arquivado"]),
                  _data(p.get("adquirida_em")), _data(p.get("arquivada_em")), DONO)
                 for p in dados["parceiros"]])
            print(f"   parceiros gravados")

            await conn.executemany(
                INSERT_TIPSTER,
                [(t["nome"], DONO, t.get("casas"), t.get("mercados"),
                  bool(t.get("arquivado")), t.get("stake_min"), t.get("stake_max"))
                 for t in dados["tipsters"]])
            print(f"   tipsters gravados")

            for c in dados.get("custos", []):
                await conn.execute(
                    INSERT_CUSTO, DONO,
                    json.dumps(c.get("custo_tipster") or {}),
                    json.dumps(c.get("custo_geral") or []),
                    json.dumps(c.get("custo_conta") or {}))
            print(f"   custos gravados")

            LOTE = 2000
            bilhetes = dados["bilhetes"]
            for i in range(0, len(bilhetes), LOTE):
                await conn.executemany(
                    INSERT_BILHETE,
                    [linha_bilhete(b) for b in bilhetes[i:i + LOTE]])
                print(f"   bilhetes {min(i + LOTE, len(bilhetes)):,}/{len(bilhetes):,}"
                      .replace(",", "."))

        # Conferencia POS-GRAVACAO: contagem devolvida pelo banco e' dado, nao
        # enfeite -- compara-se com o que se mandou (CLAUDE.md).
        print("\n## conferindo no banco")
        depois = {t: await conn.fetchval(
            f"SELECT count(*) FROM {t} WHERE dono = $1", DONO)
            for t in ("bilhetes", "parceiros", "tipsters", "custo_store")}
        # O esperado do TIPSTER e' o numero de nomes DISTINTOS, nao de linhas:
        # o mapa de tipster e' global de proposito (tipster de mesmo nome nos
        # dois lados e' a MESMA pessoa -- eles assinam os mesmos canais), entao
        # os que Feca e Jonathan tem em comum viram um ficticio so e o
        # `ON CONFLICT` descarta a segunda linha. Medido: 133 linhas -> 110
        # nomes. Comparar contra 133 marcaria defeito no comportamento correto.
        alvo = {
            "bilhetes": len(dados.get("bilhetes", [])),
            "parceiros": len({(p["casa"], p["nome"]) for p in dados.get("parceiros", [])}),
            "tipsters": len({t["nome"] for t in dados.get("tipsters", [])}),
            "custo_store": len(dados.get("custos", [])),
        }
        for k, v in depois.items():
            marca = "ok" if v == alvo[k] else "!!"
            print(f"   {marca} {k}: {v} (esperado {alvo[k]})")
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--recriar", action="store_true")
    ap.add_argument("--amostra", type=int, default=25)
    ap.add_argument("--arquivo", type=pathlib.Path, default=PADRAO)
    a = ap.parse_args()
    asyncio.run(principal(a.arquivo, a.gravar, a.recriar, a.amostra))
