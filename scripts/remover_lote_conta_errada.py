# -*- coding: utf-8 -*-
"""Move para a lixeira o resto de uma captura disparada na conta ERRADA (s370).

CONTEXTO. Irmão do `mover_bilhetes_entre_contas.py`, e o par dele. Quando a captura entra
na conta errada, parte do lote costuma já existir na conta certa: ali mover não é possível
(a assinatura colide, e com código o `_counter` não escala) e manter também não, porque a
cópia intrusa suja P/L, turnover e ROI das duas contas. Sobra remover a cópia.

O caso que o originou: 235 bilhetes da Bet365 da conta `BrunnoAD [Fatuch]` (dono Gabriel)
entraram na `matheushds62 [Fatuch]` em 16/09/2026 22:11. Seis eram mais novos que a última
captura da conta certa e foram MOVIDOS pelo script irmão; as outras 229 já estavam lá,
com tipster preenchido, e são estas que saem por aqui.

A TRAVA QUE FAZ ISTO SER SEGURO: nenhuma linha sai sem a gêmea PROVADA. Para cada alvo o
script exige um bilhete de mesmo `codigo_bilhete` na conta de destino (mesmo dono, mesma
casa), e grava o id dela em `mantido_id`. Linha sem código, ou com código que não aparece
lá, NÃO é removida e derruba a aplicação inteira: remover ali seria perda de dado, e o
caminho dela é o `mover_bilhetes_entre_contas.py`. Fail-closed de propósito.

Exclusão é MOVIMENTO, nunca soft-delete (`CLAUDE.md`): o `DELETE … RETURNING to_jsonb(b.*)`
é uma operação só (ler antes e apagar depois abre janela para gravar uma lixeira que não
corresponde ao que saiu) e o snapshot vai inteiro, em JSONB, para `lixeira_bilhetes`.

RE-ARQUIVAR AS DUAS CONTAS NO FIM, pelo mesmo motivo do script irmão: `auto_arquivar`
mantém visíveis as 40 linhas mais recentes por conta, e o lote intruso estava no topo da
conta errada. Tirá-lo sem recomputar deixaria a grade dela vazia, e um conserto que
esvazia a tela vira susto pior que o problema.

A JANELA é sobre `criado_em` (quando a linha entrou no banco), NÃO sobre a data do
bilhete: é a captura que se quer desfazer, e ela tem hora. Horário de Brasília.

USO (ensaio é o padrão — só mexe no banco com --aplicar):

    python scripts/remover_lote_conta_errada.py \
        --dono Gabriel --casa Bet365 \
        --de "matheushds62 [Fatuch]" --gemea-em "BrunnoAD [Fatuch]" \
        --desde "2026-09-16 22:11" --ate "2026-09-16 22:13"

    ... o mesmo comando com --aplicar no fim executa.
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import asyncpg
from dotenv import load_dotenv

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_RAIZ, ".env"))
# `app/repository.py` importa os vizinhos de forma flat (`from database import ...`),
# então quem entra no path é a pasta `app/`, não a raiz.
sys.path.insert(0, os.path.join(_RAIZ, "app"))

from repository import auto_arquivar  # noqa: E402

# O console do Windows abre em cp1252 e derruba o script no primeiro caractere fora da
# tabela — erro de encoding disfarçado de erro de operação é o pior tipo.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

_BR = timezone(timedelta(hours=-3))
_BACKUP_DIR = os.path.join(_RAIZ, "Backups", "s370-lote-na-conta-errada")


def _hora(txt: str) -> datetime:
    """'2026-09-16 22:11' -> datetime com fuso de Brasília. Aceita ISO com fuso."""
    dt = datetime.fromisoformat(txt.strip())
    return dt if dt.tzinfo else dt.replace(tzinfo=_BR)


def _dump_backup(rows: list[dict], rotulo: str) -> str:
    """Snapshot em JSON, uma linha por bilhete, com TODAS as colunas.

    Redundante com a `lixeira_bilhetes` de propósito: a lixeira vive no banco, e um
    arquivo local sobrevive a acidente no próprio banco. JSON e não CSV de colunas
    nomeadas, que para de copiar coluna nova em silêncio.
    """
    os.makedirs(_BACKUP_DIR, exist_ok=True)
    carimbo = datetime.now(_BR).strftime("%Y%m%d-%H%M%S")
    alvo = os.path.join(_BACKUP_DIR, f"{carimbo}-{rotulo}.json")
    with open(alvo, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r["linha"], ensure_ascii=False, default=str) + "\n")
    return alvo


async def _selecionar(conn, dono, casa, de, desde, ate, ids) -> list[dict]:
    cond = ["dono = $1", "casa = $2", "parceiro = $3"]
    par = [dono, casa, de]
    if desde:
        par.append(desde)
        cond.append(f"criado_em >= ${len(par)}")
    if ate:
        par.append(ate)
        cond.append(f"criado_em <= ${len(par)}")
    if ids:
        par.append(ids)
        cond.append(f"id = ANY(${len(par)}::int[])")
    sql = f"""
        SELECT id, codigo_bilhete, data, aposta, descricao, stake, odd, resultado,
               tipster, criado_em, to_jsonb(bilhetes.*) AS linha
          FROM bilhetes
         WHERE {' AND '.join(cond)}
         ORDER BY criado_em, id"""
    return [dict(r) | {"linha": json.loads(r["linha"])} for r in await conn.fetch(sql, *par)]


async def main() -> None:
    # description em ASCII de propósito: o --help no console cp1252 estoura com acento.
    ap = argparse.ArgumentParser(
        description="Move para a lixeira o resto de uma captura na conta errada.")
    ap.add_argument("--dono", required=True)
    ap.add_argument("--casa", required=True)
    ap.add_argument("--de", required=True, help="conta que recebeu os bilhetes por engano")
    ap.add_argument("--gemea-em", required=True, dest="gemea_em",
                    help="conta a que os bilhetes pertencem e onde a gemea tem de existir")
    ap.add_argument("--desde", help="criado_em >= (ex.: '2026-09-16 22:11', hora de BR)")
    ap.add_argument("--ate", help="criado_em <= (ex.: '2026-09-16 22:13')")
    ap.add_argument("--ids", help="lista explícita de ids, separada por vírgula")
    ap.add_argument("--aplicar", action="store_true", help="sem isto, é só simulação")
    a = ap.parse_args()

    if not (a.desde or a.ate or a.ids):
        print("ABORTADO: informe --desde/--ate ou --ids. Sem filtro isto esvaziaria a "
              "conta INTEIRA.")
        raise SystemExit(2)
    if a.de == a.gemea_em:
        print("ABORTADO: a conta de origem e a da gêmea são a mesma.")
        raise SystemExit(2)

    desde = _hora(a.desde) if a.desde else None
    ate = _hora(a.ate) if a.ate else None
    ids = [int(x) for x in a.ids.split(",")] if a.ids else None

    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        rows = await _selecionar(conn, a.dono, a.casa, a.de, desde, ate, ids)
        if not rows:
            print("Nenhum bilhete bate com o filtro. Nada a fazer.")
            return

        print("=" * 78)
        print(f"REMOVER {len(rows)} bilhete(s) — {a.casa} (dono {a.dono})")
        print(f"  da conta errada: '{a.de}'")
        print(f"  gêmea exigida em: '{a.gemea_em}'")
        print(f"  janela criado_em: {rows[0]['criado_em']:%d/%m %H:%M} .. "
              f"{rows[-1]['criado_em']:%d/%m %H:%M} (UTC)")
        print("=" * 78)

        # Prova a gêmea de TODOS antes de escrever qualquer coisa: uma linha sem gêmea
        # descoberta no meio do laço deixaria metade removido, e meio-conserto é a família
        # do UPSERT meio-atualizado.
        planos, sem_gemea = [], []
        for r in rows:
            cod = (r["codigo_bilhete"] or "").strip()
            gemea = None
            if cod:
                gemea = await conn.fetchval(
                    """SELECT id FROM bilhetes
                        WHERE dono = $1 AND casa = $2 AND parceiro = $3
                          AND codigo_bilhete = $4
                        ORDER BY id LIMIT 1""",
                    a.dono, a.casa, a.gemea_em, cod)
            if gemea is None:
                sem_gemea.append(r)
            else:
                planos.append((r, gemea))

        if sem_gemea:
            print(f"\nSEM GÊMEA na conta certa ({len(sem_gemea)}) — estas NÃO podem sair:")
            for r in sem_gemea:
                print(f"  #{r['id']} {r['codigo_bilhete'] or '(sem código)'} {r['data']} "
                      f"stake={r['stake']} odd={r['odd']} "
                      f"{(r['descricao'] or '')[:44]}")
            print("  -> este bilhete só existe aqui. Mova-o com "
                  "`mover_bilhetes_entre_contas.py` antes de remover o resto.")
            print("\nABORTADO: nada foi removido.")
            raise SystemExit(3)

        com_tipster = sum(1 for r, _ in planos if (r["tipster"] or "").strip())
        print(f"\ngêmea provada por código para {len(planos)} de {len(rows)}.")
        print(f"  com tipster preenchido nesta conta (errada): {com_tipster}")
        print("  amostra (5 primeiras):")
        for r, g in planos[:5]:
            print(f"    #{r['id']} {r['codigo_bilhete']} {r['data']} "
                  f"{r['resultado'] or '(aberta)'} -> gêmea #{g} em '{a.gemea_em}'")

        if not a.aplicar:
            print(f"\n[SIMULAÇÃO] {len(planos)} seriam movidas para `lixeira_bilhetes`. "
                  f"Rode de novo com --aplicar para executar.")
            return

        bkp = _dump_backup(rows, f"{a.casa}-{a.de}".replace(" ", "_").replace("/", "-"))
        print(f"\nbackup do estado ANTES: {bkp}")

        motivo = (f"captura disparada na conta errada — cópia de '{a.gemea_em}' que entrou "
                  f"em '{a.de}' ({a.casa} · {a.dono} · s370)")
        movidas = 0
        async with conn.transaction():
            for r, gemea in planos:
                snap = await conn.fetchval(
                    "DELETE FROM bilhetes WHERE id = $1 AND dono = $2 "
                    "RETURNING to_jsonb(bilhetes.*)", r["id"], a.dono)
                if snap is None:           # já saiu por outro caminho
                    continue
                await conn.execute(
                    """INSERT INTO lixeira_bilhetes (dono, motivo, mantido_id, bilhete)
                       VALUES ($1, $2, $3, $4::jsonb)""",
                    a.dono, motivo, gemea, snap)
                movidas += 1
        print(f"movidas para `lixeira_bilhetes`: {movidas}")

        # Fora da transação, e nas DUAS contas: o lote removido era o que segurava a
        # janela dos 40 visíveis da conta errada.
        for conta in (a.de, a.gemea_em):
            n = await auto_arquivar(a.casa, conta, 40, a.dono)
            visiveis = await conn.fetchval(
                "SELECT COUNT(*) FROM bilhetes WHERE dono = $1 AND casa = $2 "
                "AND parceiro = $3 AND NOT archived", a.dono, a.casa, conta)
            print(f"  re-arquivado '{conta}': {n} linha(s) mudaram de estado, "
                  f"{visiveis} visíveis na grade")

        print("\n== CONFERÊNCIA PÓS-REMOÇÃO ==")
        for conta in (a.de, a.gemea_em):
            r = await conn.fetchrow(
                """SELECT COUNT(*) AS n, MAX(criado_em) AS ultimo
                     FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3""",
                a.dono, a.casa, conta)
            print(f"  {conta:<34} total={r['n']:<7} último={r['ultimo']:%d/%m/%Y %H:%M}")
        resto = await conn.fetchval(
            """SELECT COUNT(*) FROM bilhetes
                WHERE dono = $1 AND casa = $2 AND parceiro = $3
                  AND criado_em >= $4 AND criado_em <= $5""",
            a.dono, a.casa, a.de, desde or rows[0]["criado_em"],
            ate or rows[-1]["criado_em"])
        print(f"  remanescentes do lote na conta errada: {resto}")
        print("\nO snapshot é JSONB e nada mais no sistema lê a `lixeira_bilhetes` — "
              "voltar é decisão humana, por script.")
    finally:
        await conn.close()


asyncio.run(main())
