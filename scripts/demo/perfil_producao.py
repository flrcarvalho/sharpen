# -*- coding: utf-8 -*-
"""Perfil ESTATISTICO da base real -- calibra o gerador de demonstracao.

SOMENTE LEITURA. Nao escreve, nao altera, nao apaga nada. Roda `SELECT` de
agregacao e imprime distribuicoes.

Para que serve: o print de vendas precisa de numero ficticio que se PARECA com
o real. Chutar a escala (quantas apostas, que stake, que ROI) daria uma tela
que nao convence quem opera. Entao medimos a forma da base verdadeira e o
`dados_demo.py` reproduz a forma -- nunca o conteudo.

O que NAO sai daqui, de proposito: descricao de aposta, nome de tipster, nome
de parceiro, codigo de bilhete. Sao dados que identificam pessoa e operacao.
Contamos quantos existem; nao lemos quais sao.

    python scripts/demo/perfil_producao.py [dono]
"""
import asyncio
import os
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[2]


def _database_url() -> str:
    """Le a DATABASE_URL do .env (o app nao usa python-dotenv)."""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8", errors="ignore").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL nao encontrada (.env ou ambiente)")


# `stake`, `odd` e `data` sao TEXTO no banco (decimal com virgula, data dd/mm/aaaa).
# Sem o cast, percentile_cont estoura e min(data) sai lexicografico -- foi o que
# aconteceu na primeira rodada: "de 01/01 ate 31/05" era ordem alfabetica, nao
# cronologica. NUM/DIA normalizam antes de qualquer agregacao.
NUM = "NULLIF(replace(replace({c}, '.', ''), ',', '.'), '')::numeric"
DIA = "to_date(NULLIF(data, ''), 'DD/MM/YYYY')"

CONSULTAS = {
    "volume": f"""
        SELECT count(*) AS apostas,
               count(DISTINCT casa) AS casas,
               count(DISTINCT parceiro) AS contas,
               count(DISTINCT tipster) FILTER (WHERE tipster <> '') AS tipsters,
               count(DISTINCT esporte) AS esportes,
               min({DIA}) AS de, max({DIA}) AS ate
        FROM bilhetes WHERE dono = $1 AND data ~ '^\\d{{2}}/\\d{{2}}/\\d{{4}}$'
    """,
    # CASE, e nao WHERE: o planner do Postgres empurra o cast para antes do
    # filtro e estoura em "invalid input syntax for numeric". CASE avalia
    # condicionalmente, entao lixo de extracao (odd em reticencias) vira NULL
    # em vez de derrubar a consulta inteira.
    "stake": """
        SELECT round(percentile_cont(0.10) WITHIN GROUP (ORDER BY s)::numeric, 2) AS p10,
               round(percentile_cont(0.50) WITHIN GROUP (ORDER BY s)::numeric, 2) AS mediana,
               round(percentile_cont(0.90) WITHIN GROUP (ORDER BY s)::numeric, 2) AS p90,
               round(avg(s)::numeric, 2) AS media
        FROM (SELECT CASE WHEN stake ~ '^[0-9]+([.,][0-9]+)?$'
                          THEN replace(stake, ',', '.')::numeric END AS s
              FROM bilhetes WHERE dono = $1) t
        WHERE s IS NOT NULL AND s > 0
    """,
    "odd": """
        SELECT round(percentile_cont(0.10) WITHIN GROUP (ORDER BY o)::numeric, 2) AS p10,
               round(percentile_cont(0.50) WITHIN GROUP (ORDER BY o)::numeric, 2) AS mediana,
               round(percentile_cont(0.90) WITHIN GROUP (ORDER BY o)::numeric, 2) AS p90,
               round(avg(o)::numeric, 2) AS media,
               count(*) AS lidas
        FROM (SELECT CASE WHEN odd ~ '^[0-9]+([.,][0-9]+)?$'
                          THEN replace(odd, ',', '.')::numeric END AS o
              FROM bilhetes WHERE dono = $1) t
        WHERE o IS NOT NULL AND o > 1 AND o < 100
    """,
    "resultado": """
        SELECT upper(trim(resultado)) AS resultado, count(*) AS n
        FROM bilhetes WHERE dono = $1 AND resultado IS NOT NULL AND trim(resultado) <> ''
        GROUP BY 1 ORDER BY n DESC
    """,
    "casa": """
        SELECT casa, count(*) AS n FROM bilhetes WHERE dono = $1
        GROUP BY 1 ORDER BY n DESC LIMIT 14
    """,
    "esporte": """
        SELECT esporte, count(*) AS n FROM bilhetes WHERE dono = $1 AND esporte <> ''
        GROUP BY 1 ORDER BY n DESC LIMIT 12
    """,
    "mercado": """
        SELECT aposta, count(*) AS n FROM bilhetes WHERE dono = $1 AND aposta <> ''
        GROUP BY 1 ORDER BY n DESC LIMIT 18
    """,
    "por_dia": """
        SELECT round(avg(n)::numeric, 1) AS apostas_por_dia_ativo,
               max(n) AS pico_no_dia,
               count(*) AS dias_com_aposta
        FROM (SELECT data, count(*) AS n FROM bilhetes WHERE dono = $1 GROUP BY data) t
    """,
}


def _saida_utf8() -> None:
    """O console do Windows e' cp1252 e engasga no '·' dos rotulos."""
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


async def principal(dono: str) -> None:
    try:
        import asyncpg
    except ImportError:
        raise SystemExit("asyncpg nao instalado: pip install asyncpg")

    conn = await asyncpg.connect(_database_url())
    try:
        print(f"# perfil estatistico -- dono={dono} (somente leitura)\n")
        for nome, sql in CONSULTAS.items():
            linhas = await conn.fetch(sql, dono)
            print(f"## {nome}")
            for r in linhas:
                print("   " + " · ".join(f"{k}={v}" for k, v in dict(r).items()))
            print()
    finally:
        await conn.close()


if __name__ == "__main__":
    _saida_utf8()
    asyncio.run(principal(sys.argv[1] if len(sys.argv) > 1 else "Feca"))
