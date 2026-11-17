# Executor SO-LEITURA contra o Postgres de producao do Sharpen.
# - a URL vem do CLI da Railway dentro do processo e nunca e impressa;
# - conexao com default_transaction_read_only=on + transacao READ ONLY explicita;
# - recusa qualquer comando que nao comece com SELECT/WITH/SHOW/EXPLAIN.
# Uso: python prodq.py arquivo.sql   (consultas separadas por linha '-- @@ titulo')
import asyncio, os, re, subprocess, sys, json, decimal, datetime

CWD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

def _url():
    out = subprocess.run(["railway", "variables", "--service", "Postgres", "--kv"],
                         cwd=CWD, capture_output=True, text=True, shell=True).stdout
    for ln in out.splitlines():
        if ln.startswith("DATABASE_PUBLIC_URL="):
            return ln.split("=", 1)[1].strip()
    raise SystemExit("sem DATABASE_PUBLIC_URL")

PERMITIDO = re.compile(r"^\s*(select|with|show|explain)\b", re.I)
PROIBIDO = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum|call|do)\b\s", re.I)

def _fmt(v):
    if isinstance(v, (decimal.Decimal,)): return str(v)
    if isinstance(v, (datetime.datetime, datetime.date)): return v.isoformat(sep=' ') if isinstance(v, datetime.datetime) else v.isoformat()
    if isinstance(v, (list, dict)): return json.dumps(v, default=str, ensure_ascii=False)[:300]
    s = "" if v is None else str(v)
    return s.replace("\n", "\\n").replace("\t", " ")[:300]

async def main(path):
    import asyncpg
    blocos = re.split(r"^-- @@ ?(.*)$", open(path, encoding="utf-8").read(), flags=re.M)
    consultas = []
    if blocos[0].strip(): consultas.append(("", blocos[0]))
    for i in range(1, len(blocos), 2): consultas.append((blocos[i], blocos[i+1]))
    conn = await asyncpg.connect(_url(), server_settings={"default_transaction_read_only": "on",
                                                          "statement_timeout": "120000"}, timeout=30)
    try:
        for titulo, sql in consultas:
            sql = sql.strip().rstrip(";")
            if not sql: continue
            corpo = re.sub(r"--[^\n]*", "", sql)
            if not PERMITIDO.match(corpo) or (PROIBIDO.search(corpo) and not corpo.lower().lstrip().startswith(("select","with"))):
                print(f"### {titulo}\nRECUSADO (nao e leitura)\n"); continue
            print(f"### {titulo}")
            try:
                async with conn.transaction(readonly=True):
                    rows = await conn.fetch(sql)
            except Exception as e:
                print(f"ERRO: {type(e).__name__}: {e}\n"); continue
            if not rows: print("(0 linhas)\n"); continue
            cols = list(rows[0].keys())
            print("\t".join(cols))
            for r in rows[:400]: print("\t".join(_fmt(r[c]) for c in cols))
            if len(rows) > 400: print(f"... {len(rows)} linhas")
            print()
    finally:
        await conn.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main(sys.argv[1]))
