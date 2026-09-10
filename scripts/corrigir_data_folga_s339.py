"""Corrige a DATA de bilhetes que a folga de encerramento datou no futuro (sessão 339).

NASCEU DE: 22:50 de 09/09/2026. O relatório do tipster `Ctrl Alt Green` fechava o mês em
**-R$ 892,87** e a grade mostrava oito apostas de eBasket datadas de **10/09** — um dia que
ainda não tinha chegado. As 8 estavam no banco, todas `W`, somando **+R$ 928,00**. O MTD do
dashboard recorta `[1º do mês, hoje]`, então bilhete datado de amanhã cai fora da conta do
mês: com elas dentro, o mês vai para **+R$ 35,13**. O filtro trocou o SINAL do resultado.

A CAUSA (corrigida à parte, em `extensor/content.js`): `_dataFimB3` somava ao kickoff uma
"folga de encerramento" por esporte (`_OFF_B3`) para estimar a liquidação. eBasket chega da
bet365 como `CL=18` — Basquete, porque a casa não separa os dois — e levava **2,5 h de folga
num jogo que dura ~4 minutos**. Kickoff 22:35 + 2,5 h = 01:05 do dia seguinte.

POR QUE PRECISA DE SCRIPT: o UPSERT **congela** `data` assim que a linha resolve
(`_ORIGEM_AUTORITATIVA`, `app/repository.py`). Recapturar a casa com a extensão nova NÃO
conserta o que já está gravado — a linha resolvida ignora a data que chegar.

A PROVA DE QUE A DATA CERTA É O DIA DA CAPTURA, e não um palpite: a linha entrou no banco já
**resolvida**, com retorno. Um bilhete só resolve depois de o evento acabar, então o evento
ocorreu ANTES do instante da captura — logo a data do evento é, no máximo, o dia da captura.
Em eBasket ela é exatamente o dia da captura, porque o jogo dura minutos. Não há estimativa
aqui: é a mesma aritmética que o defeito violava, lida ao contrário.

QUATRO TRAVAS, todas fail-closed:

  1. SÓ BILHETE COM CÓDIGO. Sem código a assinatura é feita do conteúdo e `data` entra nela
     (`_assinatura`, `_SIG_COLS`) — mexer na data exigiria recalcular o hash e tratar
     colisão. Com código o hash é `ID|casa|parceiro|codigo` e não depende da data. Linha sem
     código sai no relatório e NÃO é tocada.
  2. SÓ ONDE A DATA É POSTERIOR AO DIA DA CAPTURA. É a assinatura do defeito e a única forma
     de prová-lo sem o kickoff, que o banco não guarda. Data anterior ou igual fica de fora.
  3. CORREÇÃO HUMANA MANDA. Bilhete com registro em `correcoes` no campo `data` é PULADO,
     certo ou errado: é decisão do dono da conta (mesma regra do `corrigir_resultado_odd_s321`).
  4. ESCOPO EXPLÍCITO. `--dono` e `--tipster` são obrigatórios juntos ou `--tudo` precisa ser
     dito por escrito. Sem isso o script não roda: a s339 autorizou o reparo das 8 linhas do
     `Ctrl Alt Green`, não uma varredura da base.

O QUE ELE NÃO FAZ: não mexe em linha ABERTA (ali a data ainda é refrescada por qualquer
reenvio, então o conserto vem sozinho na próxima captura com a extensão nova) e não toca em
esporte nenhum além dos passados em `--esporte` (padrão: eBasket). Em esporte real o evento
pode ter começado no dia anterior ao da captura, e aí "dia da captura" seria um palpite —
exatamente o erro que este script existe para desfazer.

Uso:
    python scripts/corrigir_data_folga_s339.py --dono Feca --tipster "Ctrl Alt Green"
    python scripts/corrigir_data_folga_s339.py --dono Feca --tipster "Ctrl Alt Green" --aplicar
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg

# O console do Windows abre em cp1252 e derruba o script no primeiro caractere fora da tabela.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RAIZ = Path(__file__).resolve().parent.parent

# `bilhetes.data` guarda DD/MM/YYYY e ISO na MESMA coluna (`_data_iso` converte só na saída).
# Todo SQL que leia data precisa dos DOIS ramos — ler só ISO acha quase nada.
_ISO = """
  CASE
    WHEN b.data ~ '^\\d{2}/\\d{2}/\\d{4}$' THEN to_date(b.data, 'DD/MM/YYYY')
    WHEN b.data ~ '^\\d{4}-\\d{2}-\\d{2}'  THEN to_date(left(b.data, 10), 'YYYY-MM-DD')
  END
"""
_CAPTURA = "(b.criado_em AT TIME ZONE 'America/Sao_Paulo')::date"


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip()
    print("DATABASE_URL ausente (nem no ambiente nem no .env).", file=sys.stderr)
    raise SystemExit(2)


def _mesmo_formato(original: str, novo_iso) -> str:
    """Grava na MESMA convenção da linha original. Trocar o formato junto com o valor faria
    o reparo mexer em duas coisas ao mesmo tempo e sujaria qualquer conferência depois."""
    if original and original[4:5] == "-":
        return novo_iso.isoformat()
    return novo_iso.strftime("%d/%m/%Y")


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dono", default=None, help="dono da base (obrigatório, salvo --tudo)")
    ap.add_argument("--tipster", default=None, help="filtrar por tipster (obrigatório, salvo --tudo)")
    ap.add_argument("--casa", default="Bet365", help="casa (padrão: Bet365)")
    ap.add_argument("--esporte", action="append", default=None,
                    help="esporte elegível; repetível (padrão: eBasket)")
    ap.add_argument("--tudo", action="store_true",
                    help="dispensa --dono/--tipster. NÃO use sem medir antes")
    ap.add_argument("--aplicar", action="store_true", help="escreve (padrão: ensaio)")
    args = ap.parse_args()

    if not args.tudo and not (args.dono and args.tipster):
        print("Escopo obrigatório: passe --dono E --tipster, ou --tudo por escrito.\n"
              "A s339 autorizou o reparo de um tipster, não uma varredura da base.",
              file=sys.stderr)
        raise SystemExit(2)

    esportes = args.esporte or ["eBasket"]
    onde = ["b.archived = FALSE", "b.extraction_state = 'resolvida'",
            "COALESCE(b.codigo_bilhete, '') <> ''", "b.casa = $1",
            "b.esporte = ANY($2)", f"{_ISO} > {_CAPTURA}"]
    par: list = [args.casa, esportes]
    if args.dono:
        par.append(args.dono)
        onde.append(f"b.dono = ${len(par)}")
    if args.tipster:
        par.append(args.tipster)
        onde.append(f"b.tipster = ${len(par)}")

    conn = await asyncpg.connect(_database_url())
    try:
        linhas = await conn.fetch(f"""
            SELECT b.id, b.dono, b.casa, b.parceiro, b.tipster, b.esporte, b.codigo_bilhete,
                   b.data, b.stake, b.odd, b.resultado, b.descricao,
                   {_ISO} AS data_atual, {_CAPTURA} AS dia_captura,
                   to_char(b.criado_em AT TIME ZONE 'America/Sao_Paulo', 'DD/MM HH24:MI') AS hora
              FROM bilhetes b
             WHERE {' AND '.join(onde)}
             ORDER BY b.id
        """, *par)

        if not linhas:
            print("Nada elegível. Nenhuma linha resolvida, com código, datada depois do dia "
                  "da própria captura, no escopo pedido.")
            return

        ids = [r["id"] for r in linhas]
        # Trava 3: correção humana em `data` manda sobre a captura.
        editados = {r["bilhete_id"] for r in await conn.fetch(
            "SELECT DISTINCT bilhete_id FROM correcoes "
            "WHERE campo = 'data' AND bilhete_id = ANY($1::bigint[])", ids)}

        print("=" * 92)
        print(f"REPARO DE DATA — folga de encerramento (s339)   {'APLICAR' if args.aplicar else 'ENSAIO'}")
        print(f"casa={args.casa}  esporte={'/'.join(esportes)}"
              f"{'  dono=' + args.dono if args.dono else ''}"
              f"{'  tipster=' + args.tipster if args.tipster else ''}")
        print("=" * 92)

        alvo, pulados = [], []
        for r in linhas:
            if r["id"] in editados:
                pulados.append(r)
                continue
            alvo.append(r)
            print(f"  #{r['id']:<7} {r['codigo_bilhete']:<15} {r['parceiro']:<26} "
                  f"{r['data']} → {_mesmo_formato(r['data'], r['dia_captura'])}"
                  f"   (capturado {r['hora']}, {r['resultado']}, stake {r['stake']})")

        for r in pulados:
            print(f"  PULADO #{r['id']} ({r['codigo_bilhete']}): tem correção humana em `data` — "
                  f"é decisão do dono da conta, certo ou errado")

        print("-" * 92)
        print(f"  {len(alvo)} linha(s) a corrigir · {len(pulados)} pulada(s) por correção humana")

        if not args.aplicar:
            print("\nENSAIO — nada foi escrito. Repita com --aplicar para gravar.")
            return
        if not alvo:
            print("\nNada a aplicar.")
            return

        async with conn.transaction():
            for r in alvo:
                nova = _mesmo_formato(r["data"], r["dia_captura"])
                await conn.execute(
                    "UPDATE bilhetes SET data = $1, atualizado_em = NOW() WHERE id = $2",
                    nova, r["id"])
                # Registra a correção: a próxima rodada deste script pula o que ele mesmo
                # arrumou, e o histórico fica auditável como qualquer edição humana.
                await conn.execute(
                    "INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, "
                    "valor_novo, descricao) VALUES ($1, $2, $3, 'data', $4, $5, $6)",
                    r["id"], r["dono"], r["casa"], r["data"], nova,
                    "s339: folga de encerramento datava o bilhete no futuro "
                    "(kickoff + 2,5 h em jogo de ~4 min). Data = dia da captura, "
                    "provado por a linha ter entrado já resolvida.")
        print(f"\nAPLICADO: {len(alvo)} linha(s) corrigida(s) e registrada(s) em `correcoes`.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
