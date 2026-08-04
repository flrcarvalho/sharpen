"""Remove os bilhetes da Bet365 que subiram SEM o `confirmation` — linha datada de hoje,
sem código e com a descrição decapitada.

O DEFEITO (s244). Na Bet365 a captura lê duas respostas:
  • `/sportshistoryapi/summary`      → seleção crua, odd, stake, resultado.
  • `/sportshistoryapi/confirmation` → código BR, kickoff (A DATA), jogo/mercado/liga.
Até a v0.6.36 da extensão, quando o `confirmation` não chegava o bilhete subia assim mesmo.
O resultado não é um bilhete "incompleto", é errado em três eixos ao mesmo tempo:

  1. SEM CÓDIGO   → a assinatura vira conteúdo → a próxima captura não reconhece → INSERT
                    duplicado (`repository._assinatura`, ramo sem código).
  2. SEM DATA     → o bloco não traz linha de data → o backend cai na DATA DE REFERÊNCIA
                    (`main.py::_INSTRUCAO` / `data_referencia`), que é HOJE. Aposta de julho
                    entra datada de hoje, dentro do P/L de hoje.
  3. SEM `legs`   → a descrição sai só com a seleção ("HNK Gorica"), sem o confronto `[A v B]`.

Medido na s244, conta `marloncezar01 [Richard]`, lote de 04/08: 206 bilhetes, 139 sem
`confirmation`. Os MESMOS 139 estavam com data de hoje. 113 casavam stake+odd+resultado e 84
casavam também a seleção com um bilhete que JÁ EXISTIA na base com código — duplicata pura.

POR QUE APAGAR E NÃO CORRIGIR: não há o que corrigir. A linha não tem a informação (código,
data, evento, mercado, liga) — ela só existe porque foi emitida sem ela. O dado certo já está
na base para a maioria, e o restante volta inteiro numa recaptura com janela curta.

CRITÉRIO (exato, não heurístico): na Bet365 o código BR **só** vem do `confirmation`, e o
`confirmation` é a mesma resposta que traz data e evento. Então, dentro de um lote de captura
por robô, `codigo_bilhete` vazio ⇔ o `confirmation` não chegou. Não é aproximação.

  ⚠️ Por isso o `--desde` é OBRIGATÓRIO e deve cobrir só o lote defeituoso: bilhete ANTIGO
  da mesma conta capturado por PRINT também não tem código, e é legítimo. Rode primeiro sem
  `--aplicar` e confira a contagem contra o que você viu na grade.

Uso:

    # 1) RELATÓRIO (padrão — não escreve nada)
    python scripts/limpar_bet365_sem_confirmation.py \
        --dono Feca --parceiro "marloncezar01 [Richard]" --desde 2026-08-04

    # 2) APLICAR (snapshot + DELETE na MESMA operação, numa transação)
    python scripts/limpar_bet365_sem_confirmation.py \
        --dono Feca --parceiro "marloncezar01 [Richard]" --desde 2026-08-04 --aplicar

O snapshot sai em `Backups/<pasta>/` como JSONB completo de cada linha — mesma forma da
`lixeira_contas` (`CLAUDE.md`, "Excluir dado"): o `DELETE ... RETURNING to_jsonb(b.*)` é UMA
operação, então o que foi salvo é exatamente o que saiu. JSONB e não tabela-espelho porque
`bilhetes` ganha coluna via `ALTER TABLE` de tempos em tempos e um espelho pararia de copiar
a coluna nova em silêncio.
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import asyncpg

RAIZ = Path(__file__).resolve().parent.parent


def _dsn() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        return dsn
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("DATABASE_URL ausente (env ou .env na raiz do Planilhador).")


# `criado_em` é TIMESTAMPTZ; o corte é pelo DIA em América/São_Paulo, que é como o operador
# pensa ("o lote de hoje"). Comparar em UTC pegaria o fim do dia anterior.
FILTRO = """
    casa ILIKE $1
    AND dono = $2
    AND parceiro = $3
    AND coalesce(codigo_bilhete, '') = ''
    AND (criado_em AT TIME ZONE 'America/Sao_Paulo')::date >= $4::date
"""


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dono", required=True, help="dono da base (ex.: Feca)")
    ap.add_argument("--parceiro", required=True, help='conta exata (ex.: "marloncezar01 [Richard]")')
    ap.add_argument("--desde", required=True, help="data do lote, AAAA-MM-DD (fuso de Brasília)")
    ap.add_argument("--casa", default="Bet365", help="casa (default Bet365)")
    ap.add_argument("--aplicar", action="store_true", help="executa o DELETE (sem isto, só relatório)")
    ap.add_argument("--pasta", default=None, help="subpasta em Backups/ para o snapshot")
    args = ap.parse_args()

    conn = await asyncpg.connect(_dsn())
    try:
        # `date` de verdade, não string: o asyncpg tipa o $4 pelo `::date` do SQL e recusa texto.
        # Converter aqui também valida o formato antes de qualquer query.
        try:
            desde = date.fromisoformat(args.desde)
        except ValueError:
            sys.exit(f"--desde inválido: {args.desde!r} (esperado AAAA-MM-DD)")
        alvo = (args.casa, args.dono, args.parceiro, desde)

        resumo = await conn.fetchrow(f"""
            SELECT count(*) AS n,
                   count(*) FILTER (WHERE data = to_char(now() AT TIME ZONE 'America/Sao_Paulo',
                                                         'DD/MM/YYYY')) AS data_hoje,
                   count(*) FILTER (WHERE coalesce(descricao, '') NOT LIKE '%% v %%') AS sem_confronto,
                   count(*) FILTER (WHERE resultado IN ('W','L','V','HW','HL')) AS liquidadas,
                   min((criado_em AT TIME ZONE 'America/Sao_Paulo')::text) AS primeiro,
                   max((criado_em AT TIME ZONE 'America/Sao_Paulo')::text) AS ultimo
              FROM bilhetes WHERE {FILTRO}
        """, *alvo)

        total = resumo["n"]
        print(f"Casa={args.casa} · dono={args.dono} · conta={args.parceiro} · desde {args.desde}")
        print(f"  bilhetes SEM código (confirmation não chegou): {total}")
        if not total:
            print("  Nada a fazer.")
            return
        print(f"  com data de HOJE ............ {resumo['data_hoje']}")
        print(f"  descrição SEM confronto ..... {resumo['sem_confronto']}")
        print(f"  liquidadas (entram no P/L) .. {resumo['liquidadas']}")
        print(f"  janela de criação ........... {resumo['primeiro']} → {resumo['ultimo']}")

        # Rede de segurança: um lote de robô é criado em minutos. Se a janela abrir muitos dias,
        # o --desde está pegando bilhete de PRINT (legítimo, também sem código) e não só o lote.
        d0 = datetime.fromisoformat(resumo["primeiro"]).date()
        d1 = datetime.fromisoformat(resumo["ultimo"]).date()
        if (d1 - d0).days > 1:
            print(f"\n  ⚠️  A janela cobre {(d1 - d0).days + 1} dias. Bilhete antigo capturado por "
                  f"PRINT também não tem código e é legítimo. Estreite o --desde antes de aplicar.")

        # `correcoes.bilhete_id` é BIGINT solto (sem FK): apagar o bilhete deixa a correção
        # apontando para o nada. Medir antes de decidir, não depois.
        #
        # DECISÃO (s244): as correções são PRESERVADAS. `correcoes` é trilha de auditoria
        # write-only — nenhum código do app a lê (conferido por grep em app/, scripts/, tools/),
        # e a base já convive com centenas de órfãs. Apagar registro de auditoria para deixar a
        # tabela "limpa" é pior que deixá-lo órfão: some a prova de que a edição aconteceu.
        orfas = await conn.fetchval(f"""
            SELECT count(*) FROM correcoes c
             WHERE c.bilhete_id IN (SELECT id FROM bilhetes WHERE {FILTRO})
        """, *alvo)
        print(f"  correções preservadas (ficam órfãs, por decisão): {orfas}")

        amostra = await conn.fetch(f"""
            SELECT id, data, esporte, aposta, left(coalesce(descricao,''), 44) AS d,
                   stake, odd, resultado
              FROM bilhetes WHERE {FILTRO} ORDER BY id LIMIT 10
        """, *alvo)
        print("\n  amostra:")
        for r in amostra:
            print(f"    id={r['id']:<7} {r['data']} {str(r['esporte'])[:9]:9} {str(r['aposta'])[:11]:11} "
                  f"| {r['d']:44} | {r['stake']:>9} @ {str(r['odd'])[:8]:8} {r['resultado']}")

        if not args.aplicar:
            print(f"\n  RELATÓRIO apenas. Nada foi alterado. Repita com --aplicar para remover as {total}.")
            return

        pasta = RAIZ / "Backups" / (args.pasta or "s244-bet365-sem-confirmation")
        pasta.mkdir(parents=True, exist_ok=True)
        carimbo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destino = pasta / f"removidos-{args.dono}-{carimbo}.json"

        # Snapshot e DELETE são a MESMA operação (RETURNING). Ler antes e apagar depois abriria
        # janela para gravar um snapshot que não corresponde ao que saiu.
        async with conn.transaction():
            linhas = await conn.fetch(f"""
                DELETE FROM bilhetes b WHERE {FILTRO} RETURNING to_jsonb(b.*) AS linha
            """, *alvo)
            destino.write_text(
                json.dumps([json.loads(r["linha"]) for r in linhas], ensure_ascii=False,
                           indent=2, default=str),
                encoding="utf-8")

        print(f"\n  REMOVIDOS: {len(linhas)} bilhete(s).")
        print(f"  Snapshot: {destino}")
        restam = await conn.fetchval(f"SELECT count(*) FROM bilhetes WHERE {FILTRO}", *alvo)
        print(f"  Conferência pós-DELETE (deve ser 0): {restam}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
