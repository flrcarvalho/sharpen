"""Move um SUBCONJUNTO de bilhetes de uma conta para outra, recalculando a assinatura.

Irmão do `reparar_orfaos_parceiro.py`, com uma diferença que é a razão de existir: aquele
move a conta INTEIRA (todo bilhete cujo `parceiro` órfão bate). Aqui o caso é outro — a
conta de destino errada é uma conta VIVA, cheia de histórico legítimo, e só o lote recém
capturado precisa sair. Mover a conta inteira seria o estrago maior.

O caso que o originou (s266): a captura da Bet365 da conta `Taliacoelho01` foi disparada
com a página da conta `marloncezar01` selecionada. 72 bilhetes da Talia entraram na conta
do Marlon, ao lado dos 4.566 legítimos dele. Nada foi sobrescrito — bilhete da Bet365 tem
código e a assinatura é `ID|casa|parceiro|codigo`, então os intrusos entraram como linhas
novas —, mas P/L, turnover e ROI das duas contas ficaram errados.

POR QUE RECALCULAR A ASSINATURA (regra do CLAUDE.md, "Mexeu em `casa` ou `parceiro`?"):
`parceiro` entra no hash de `_assinatura`, com ou sem código. Trocar o parceiro sem
recalcular deixa a linha com o hash da conta ANTIGA: a próxima captura da conta certa
gera uma assinatura nova, não colide com nada, o UPSERT não dedupa e o histórico
DUPLICA inteiro. O laço de `_counter` abaixo é o mesmo de `_assinatura_pos_edicao`.

POR QUE RE-ARQUIVAR AS DUAS CONTAS NO FIM: `auto_arquivar` mantém visíveis as 40 linhas
mais recentes POR CONTA (`criado_em DESC`) e arquiva o resto. Com o lote intruso no topo,
a grade da conta errada mostra só ele; tirá-lo sem recomputar deixaria a conta de origem
com a grade VAZIA — o histórico está lá, mas invisível, que é como um conserto vira um
susto. Chamamos a função do próprio app, não uma cópia do SQL.

Uso (dry-run por padrão — nada é escrito sem `--aplicar`):

    python scripts/mover_bilhetes_entre_contas.py \
        --dono Feca --casa Bet365 \
        --de "marloncezar01 [Richard]" --para "Taliacoelho01 [Richard]" \
        --desde "2026-08-13 21:30" --ate "2026-08-13 21:50"

    ... o mesmo comando com --aplicar no fim executa.

A janela é sobre `criado_em` (quando a linha entrou no banco), NÃO sobre a data do
bilhete — é a captura errada que se quer desfazer, e ela tem hora. Horário de Brasília.
`--ids` aceita uma lista explícita quando a janela não separa (lote misto).
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

from repository import _assinatura, auto_arquivar  # noqa: E402

# O console do Windows abre em cp1252 e derruba o script no primeiro caractere fora da
# tabela — erro de encoding disfarçado de erro de operação é o pior tipo.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

_BR = timezone(timedelta(hours=-3))
_BACKUP_DIR = os.path.join(_RAIZ, "Backups", "s266-mover-bilhetes-entre-contas")


def _hora(txt: str) -> datetime:
    """'2026-08-13 21:30' -> datetime com fuso de Brasília. Aceita ISO com fuso."""
    dt = datetime.fromisoformat(txt.strip())
    return dt if dt.tzinfo else dt.replace(tzinfo=_BR)


def _dump_backup(rows: list[dict], rotulo: str) -> str:
    """Snapshot em JSON, uma linha por bilhete, com TODAS as colunas.

    JSON e não CSV com colunas fixas pela mesma razão que a lixeira usa JSONB: `bilhetes`
    ganha coluna via `ALTER TABLE` de tempos em tempos (`sistema`/`sistema_linhas` são da
    semana passada), e um dump de colunas nomeadas à mão pararia de copiar a coluna nova
    em silêncio.
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
        SELECT id, assinatura, codigo_bilhete, data, aposta, descricao, stake, odd,
               resultado, criado_em, archived, to_jsonb(bilhetes.*) AS linha
          FROM bilhetes
         WHERE {' AND '.join(cond)}
         ORDER BY criado_em, id"""
    return [dict(r) | {"linha": json.loads(r["linha"])} for r in await conn.fetch(sql, *par)]


async def main() -> None:
    # description em ASCII de propósito: o --help no console cp1252 estoura com acento.
    ap = argparse.ArgumentParser(
        description="Move um subconjunto de bilhetes entre contas (ver docstring).")
    ap.add_argument("--dono", required=True)
    ap.add_argument("--casa", required=True)
    ap.add_argument("--de", required=True, help="conta que recebeu os bilhetes por engano")
    ap.add_argument("--para", required=True, help="conta a que os bilhetes pertencem")
    ap.add_argument("--desde", help="criado_em >= (ex.: '2026-08-13 21:30', hora de BR)")
    ap.add_argument("--ate", help="criado_em <= (ex.: '2026-08-13 21:50')")
    ap.add_argument("--ids", help="lista explícita de ids, separada por vírgula")
    ap.add_argument("--aplicar", action="store_true", help="sem isto, é só simulação")
    a = ap.parse_args()

    if not (a.desde or a.ate or a.ids):
        print("ABORTADO: informe --desde/--ate ou --ids. Sem filtro isto moveria a conta "
              "INTEIRA, que é trabalho do reparar_orfaos_parceiro.py.")
        raise SystemExit(2)
    if a.de == a.para:
        print("ABORTADO: origem e destino são a mesma conta.")
        raise SystemExit(2)

    desde = _hora(a.desde) if a.desde else None
    ate = _hora(a.ate) if a.ate else None
    ids = [int(x) for x in a.ids.split(",")] if a.ids else None

    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        destino = await conn.fetchrow(
            "SELECT id, arquivado FROM parceiros WHERE dono = $1 AND casa = $2 AND nome = $3",
            a.dono, a.casa, a.para)
        if not destino:
            print(f"ABORTADO: não existe a conta destino {a.casa} / '{a.para}' "
                  f"(dono {a.dono}). Crie-a antes — mover para uma conta inexistente "
                  f"produz bilhete órfão, invisível em toda tela.")
            raise SystemExit(2)

        rows = await _selecionar(conn, a.dono, a.casa, a.de, desde, ate, ids)
        if not rows:
            print("Nenhum bilhete bate com o filtro. Nada a fazer.")
            return

        liq = sum(1 for r in rows if (r["resultado"] or "").strip())
        print("=" * 78)
        print(f"MOVER {len(rows)} bilhete(s) — {a.casa} (dono {a.dono})")
        print(f"  de:   '{a.de}'")
        print(f"  para: '{a.para}'")
        print(f"  janela criado_em: {rows[0]['criado_em']:%d/%m %H:%M} .. "
              f"{rows[-1]['criado_em']:%d/%m %H:%M} (UTC)")
        print(f"  liquidadas: {liq}   abertas: {len(rows) - liq}")
        print(f"  com código: {sum(1 for r in rows if (r['codigo_bilhete'] or '').strip())}")
        print("=" * 78)

        # Calcula a assinatura nova de todos ANTES de escrever qualquer coisa: uma colisão
        # descoberta no meio do laço deixaria metade movido, e meio-conserto é a família do
        # UPSERT meio-atualizado (lucro fantasma).
        planos, colisoes = [], []
        for r in rows:
            final = {
                "casa": a.casa, "parceiro": a.para,
                "data": r["data"] or "", "aposta": r["aposta"] or "",
                "descricao": r["descricao"] or "", "stake": r["stake"] or "",
                "odd": r["odd"] or "", "codigo_bilhete": r["codigo_bilhete"] or "",
            }
            tem_codigo = bool(final["codigo_bilhete"].strip())
            nova = None
            # Mesmo laço de `_assinatura_pos_edicao`: conteúdo que colide com uma linha JÁ
            # existente no destino escala o `_counter` (regra do Feca: sem ID, duplicata só
            # quando stake+odd+descrição batem os três). COM código o hash ignora o counter,
            # então escalar não sai do lugar — ali a colisão é real e a linha não se move.
            for cnt in range(1, 51):
                sig = _assinatura(final, _counter=cnt)
                livre = await conn.fetchval(
                    """SELECT NOT EXISTS (
                           SELECT 1 FROM bilhetes
                            WHERE dono = $1 AND casa = $2 AND parceiro = $3
                              AND assinatura = $4 AND id <> $5)""",
                    a.dono, a.casa, a.para, sig, r["id"])
                if livre:
                    nova = sig
                    break
                if tem_codigo:
                    break
            if nova is None:
                colisoes.append(r)
            else:
                planos.append((r["id"], nova))

        if colisoes:
            print(f"\nCOLIDEM no destino e NÃO serão movidos ({len(colisoes)}):")
            for r in colisoes:
                print(f"  #{r['id']} {r['codigo_bilhete']} {r['data']} "
                      f"stake={r['stake']} odd={r['odd']}")
            print("  -> a conta destino já tem esse bilhete. Confira antes de forçar.")

        if not a.aplicar:
            print(f"\n[SIMULAÇÃO] {len(planos)} seriam movidos. "
                  f"Rode de novo com --aplicar para executar.")
            return

        bkp = _dump_backup(rows, f"{a.casa}-{a.de}".replace(" ", "_").replace("/", "-"))
        print(f"\nbackup do estado ANTES: {bkp}")

        async with conn.transaction():
            for bid, sig in planos:
                await conn.execute(
                    "UPDATE bilhetes SET parceiro = $1, assinatura = $2, "
                    "atualizado_em = NOW() WHERE id = $3 AND dono = $4",
                    a.para, sig, bid, a.dono)
        print(f"movidos: {len(planos)}")

        # Fora da transação, e nas DUAS contas: sem isto a conta de origem fica com a
        # grade vazia (o lote movido era o que segurava a janela dos 40 visíveis).
        for conta in (a.de, a.para):
            n = await auto_arquivar(a.casa, conta, 40, a.dono)
            visiveis = await conn.fetchval(
                "SELECT COUNT(*) FROM bilhetes WHERE dono = $1 AND casa = $2 "
                "AND parceiro = $3 AND NOT archived", a.dono, a.casa, conta)
            print(f"  re-arquivado '{conta}': {n} linha(s) mudaram de estado, "
                  f"{visiveis} visíveis na grade")

        print("\n== CONFERÊNCIA PÓS-MOVIMENTAÇÃO ==")
        for conta in (a.de, a.para):
            r = await conn.fetchrow(
                """SELECT COUNT(*) AS n, MAX(criado_em) AS ultimo
                     FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3""",
                a.dono, a.casa, conta)
            print(f"  {conta:<34} total={r['n']:<7} último={r['ultimo']:%d/%m/%Y %H:%M}")
    finally:
        await conn.close()


asyncio.run(main())
