# s460 (18/11/2026), autorizado pelo Feca: a conta Thunderpick do arrudex foi cadastrada em
# USD, mas a Thunderpick liquida sempre em EUR (`adaptadores/thp.py`). Os 204 bilhetes dela
# já estão gravados em EUR, linha a linha, pela moeda que o cru mandou (`cambio.moeda_do_cru`),
# e a conta não tem movimento de Caixa. A troca é o mesmo UPDATE que a tela de Contas faz
# (`repository.editar_parceiro`): vale daqui para frente e nenhum bilhete é reconvertido.
#
# Trava: muda exatamente UMA linha (id, dono, casa e moeda atual conferidos); qualquer outra
# contagem desfaz a transação.
#
# Uso:
#   python scripts/s460_moeda_thunderpick_arrudex.py --url-env TEST_DATABASE_URL [--aplicar]
#   python scripts/s460_moeda_thunderpick_arrudex.py --railway [--aplicar]
# Sem --aplicar é ensaio: mostra a linha e desfaz.
import argparse
import asyncio
import os
import subprocess
import sys

PARCEIRO_ID = 1849
DONO = "arrudex"
CASA = "Thunderpick"
DE, PARA = "USD", "EUR"


def _url_railway() -> str:
    raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    out = subprocess.run(["railway", "variables", "--service", "Postgres", "--kv"],
                         cwd=raiz, capture_output=True, text=True, shell=True).stdout
    for ln in out.splitlines():
        if ln.startswith("DATABASE_PUBLIC_URL="):
            return ln.split("=", 1)[1].strip()
    raise SystemExit("sem DATABASE_PUBLIC_URL")


async def main(url: str, aplicar: bool, pid: int) -> int:
    import asyncpg
    conn = await asyncpg.connect(url, timeout=30)
    try:
        tr = conn.transaction()
        await tr.start()
        antes = await conn.fetch(
            "SELECT id, dono, casa, nome, moeda FROM parceiros WHERE id = $1", pid)
        print("antes:", [dict(r) for r in antes])
        st = await conn.execute(
            "UPDATE parceiros SET moeda = $1 "
            "WHERE id = $2 AND dono = $3 AND casa = $4 AND moeda = $5",
            PARA, pid, DONO, CASA, DE)
        n = int(st.split()[-1])
        depois = await conn.fetch(
            "SELECT id, dono, casa, nome, moeda FROM parceiros WHERE id = $1", pid)
        print("depois:", [dict(r) for r in depois], "linhas:", n)
        if n != 1:
            await tr.rollback()
            print("ABORTADO: esperava 1 linha; nada gravado.")
            return 1
        if aplicar:
            await tr.commit()
            print("GRAVADO.")
        else:
            await tr.rollback()
            print("ENSAIO: desfeito.")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url-env")
    g.add_argument("--railway", action="store_true")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--id", type=int, default=PARCEIRO_ID, help="só para o teste local")
    a = ap.parse_args()
    url = _url_railway() if a.railway else os.environ[a.url_env]
    sys.exit(asyncio.run(main(url, a.aplicar, a.id)))
