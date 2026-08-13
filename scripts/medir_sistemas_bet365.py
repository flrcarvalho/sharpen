"""
medir_sistemas_bet365.py — DIAGNÓSTICO READ-ONLY (só SELECT, nunca escreve).

Mede a exposição ao defeito da s265: bilhete de **sistema** da Bet365 (`3 x Duplas`,
`4 x Triplas`…) gravado com a odd da **múltipla cheia** (produto das odds) em vez da
**média das linhas** (`MASTER_RESULTADO §7.3`).

POR QUE ISTO NÃO É UM SCRIPT DE CORREÇÃO: o banco não guarda as odds **por perna**, então
não há como recalcular a odd correta a partir dele. A correção é por **re-captura** (o
UPSERT refresca `odd` enquanto `extraction_state = 'aberta'`), e para linha já resolvida é
decisão humana. Este script só MEDE, para o Feca decidir.

Quatro medidas, da mais certa para a mais incerta. **A (0) tornou as outras três
transitórias:** desde a s265 a captura grava a estrutura na coluna `sistema`, então quem
foi capturado com a extensão ≥ 0.6.45 é medido sem heurística nenhuma. As heurísticas (2a)
e (2b) só existem para a base ANTIGA, que ainda não passou por uma re-captura.

  (0) EXATO      — `sistema IS NOT NULL`. Sem heurística: a captura marcou. Vazio
                   significa "ninguém capturou com a versão nova ainda", não "não há".
  (1) UNIVERSO   — múltiplas da Bet365 ainda ABERTAS. É o que a re-captura conserta
                   sozinha; qualquer sistema aqui dentro se corrige ao rodar o robô
                   com a extensão ≥ 0.6.45.
  (2) SUSPEITOS  — bilhetes irmãos: mesma descrição e MESMA odd, stakes diferentes.
                   É a assinatura do defeito (o par duplas+tripla do caso original:
                   as duas linhas com 5,8149, uma com stake 303 e outra com 51).
                   Sai em DOIS níveis, porque o sinal sozinho é fraco:
                     2a FORTE — o par ainda tem **códigos BR irmãos** (mesmo prefixo,
                        sufixo vizinho: `LK9931120901I` / `…902I`), que é como a casa
                        numera duas apostas colocadas no mesmo gesto sobre as mesmas
                        seleções. É o retrato exato do caso da s265.
                     2b FRACO — sem exigir código. Enche de FALSO POSITIVO: a mesma
                        aposta repetida em stakes diferentes (tipster que entra com
                        R$ 37,50 numa conta e R$ 450,00 noutra) cai aqui e NÃO é
                        sistema. Serve de teto, nunca de contagem.
  (3) RESOLVIDOS — múltiplas `L` da Bet365. Universo onde um sistema mal lido ficou
                   CONGELADO (em `W` a odd saiu de Retorno ÷ Aposta e está certa).
                   Não dá para apontar quais sem re-ler o bilhete na casa.

Uso (precisa da env DATABASE_URL, a mesma do app — ou o .env do repo):
    python scripts/medir_sistemas_bet365.py
    python scripts/medir_sistemas_bet365.py --dono Fatuch --amostra 30
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg

# O console do Windows abre em cp1252 e derruba o script no primeiro caractere fora da
# tabela (`≥` mata; `—` passa) — erro de ENCODING mascarado de erro de medição. Saída em
# UTF-8 com substituição: o relatório sai inteiro em qualquer terminal.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip()
    print("DATABASE_URL ausente (nem no ambiente nem no .env).", file=sys.stderr)
    raise SystemExit(2)


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dono", default=None, help="filtrar por dono (ex.: Fatuch)")
    ap.add_argument("--amostra", type=int, default=15, help="linhas de amostra por grupo")
    args = ap.parse_args()

    conn = await asyncpg.connect(_database_url())
    try:
        filtro_dono = "AND dono = $1" if args.dono else ""
        p = [args.dono] if args.dono else []

        print("=" * 78)
        print("(0) MEDIDA EXATA — coluna `sistema` (só existe para captura ≥ 0.6.45)")
        print("    Sem heurística: quem tem `sistema` preenchido É sistema, ponto. A base")
        print("    antiga só aparece aqui depois de re-capturada (o UPSERT faz backfill).")
        print("=" * 78)
        exato = await conn.fetch(f"""
            SELECT sistema, sistema_linhas,
                   COUNT(*) AS n,
                   COUNT(*) FILTER (WHERE extraction_state = 'aberta') AS abertas,
                   COUNT(*) FILTER (WHERE resultado = 'L') AS perdidas
              FROM bilhetes
             WHERE sistema IS NOT NULL AND NOT archived
               {filtro_dono}
             GROUP BY sistema, sistema_linhas
             ORDER BY n DESC
        """, *p)
        if not exato:
            print("  nenhuma linha marcada ainda — ninguém capturou com a versão nova.")
        for r in exato:
            print(f"  {r['sistema']:<14} {r['sistema_linhas']:>3} linhas · {r['n']:>5} bilhete(s) "
                  f"· {r['abertas']} aberta(s) · {r['perdidas']} L")

        print()
        print("=" * 78)
        print("(1) UNIVERSO — múltiplas da Bet365 AINDA ABERTAS (a re-captura conserta)")
        print("=" * 78)
        universo = await conn.fetch(f"""
            SELECT dono, parceiro, COUNT(*) AS n
              FROM bilhetes
             WHERE casa ILIKE 'bet365' AND aposta ILIKE 'M%ltipla'
               AND extraction_state = 'aberta' AND NOT archived
               {filtro_dono}
             GROUP BY dono, parceiro
             ORDER BY n DESC
        """, *p)
        total_abertas = sum(r["n"] for r in universo)
        for r in universo:
            print(f"  {r['dono']:<12} {r['parceiro']:<24} {r['n']:>5}")
        print(f"  {'TOTAL':<12} {'':<24} {total_abertas:>5}")

        print()
        print("=" * 78)
        print("(2a) FORTE — mesma descrição, mesma odd, stakes diferentes E códigos IRMÃOS")
        print("     (duas apostas do mesmo gesto sobre as mesmas seleções: o retrato da s265)")
        print("=" * 78)
        fortes = await conn.fetch(f"""
            SELECT dono, parceiro, data, odd, descricao,
                   COUNT(*) AS n,
                   string_agg(codigo_bilhete, ' | ' ORDER BY codigo_bilhete) AS codigos,
                   string_agg(stake, ' | ' ORDER BY codigo_bilhete) AS lista_stake,
                   string_agg(DISTINCT COALESCE(NULLIF(resultado, ''), 'aberta'), '/') AS resultados
              FROM bilhetes
             WHERE casa ILIKE 'bet365' AND aposta ILIKE 'M%ltipla' AND NOT archived
               AND codigo_bilhete IS NOT NULL AND length(codigo_bilhete) > 4
               {filtro_dono}
             GROUP BY dono, parceiro, data, odd, descricao,
                      left(codigo_bilhete, length(codigo_bilhete) - 2)
            HAVING COUNT(*) > 1 AND COUNT(DISTINCT stake) > 1
             ORDER BY MAX(data) DESC
             LIMIT {int(args.amostra)}
        """, *p)
        if not fortes:
            print("  nenhum par — nada com a assinatura exata do defeito.")
        for r in fortes:
            print(f"  {r['dono']}/{r['parceiro']} · {r['data']} · odd {r['odd']} · "
                  f"{r['resultados']}")
            print(f"      códigos: {r['codigos']}  ·  stakes: {r['lista_stake']}")
            print(f"      {(r['descricao'] or '')[:110]}")

        print()
        print("=" * 78)
        print("(2b) FRACO — o mesmo sinal SEM exigir código irmão. Tem falso positivo:")
        print("     a mesma aposta em stakes diferentes cai aqui e NÃO é sistema. É teto.")
        print("=" * 78)
        suspeitos = await conn.fetch(f"""
            SELECT dono, parceiro, data, odd, descricao,
                   COUNT(*) AS n,
                   COUNT(DISTINCT stake) AS stakes,
                   string_agg(DISTINCT stake, ' | ' ORDER BY stake) AS lista_stake,
                   string_agg(DISTINCT COALESCE(extraction_state, '?'), '/') AS estados,
                   string_agg(DISTINCT COALESCE(NULLIF(resultado, ''), 'aberta'), '/') AS resultados
              FROM bilhetes
             WHERE casa ILIKE 'bet365' AND aposta ILIKE 'M%ltipla' AND NOT archived
               {filtro_dono}
             GROUP BY dono, parceiro, data, odd, descricao
            HAVING COUNT(*) > 1 AND COUNT(DISTINCT stake) > 1
             ORDER BY COUNT(*) DESC
             LIMIT {int(args.amostra)}
        """, *p)
        if not suspeitos:
            print("  nenhum grupo — nenhum par irmão detectável por este sinal.")
        for r in suspeitos:
            print(f"  {r['dono']}/{r['parceiro']} · {r['data']} · odd {r['odd']} · "
                  f"{r['n']} linhas · stakes: {r['lista_stake']} · {r['resultados']}")
            print(f"      {(r['descricao'] or '')[:110]}")

        print()
        print("=" * 78)
        print("(3) RESOLVIDOS — múltiplas Bet365 por resultado (onde a odd está CONGELADA)")
        print("    W está certa (Retorno ÷ Aposta). L é o universo de risco.")
        print("=" * 78)
        res = await conn.fetch(f"""
            SELECT COALESCE(NULLIF(resultado, ''), '(aberta)') AS r, COUNT(*) AS n
              FROM bilhetes
             WHERE casa ILIKE 'bet365' AND aposta ILIKE 'M%ltipla' AND NOT archived
               {filtro_dono}
             GROUP BY 1 ORDER BY n DESC
        """, *p)
        for r in res:
            print(f"  {r['r']:<10} {r['n']:>6}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
