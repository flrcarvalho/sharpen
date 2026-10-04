"""Uma casa, uma grafia: confere a BASE contra o REGISTRO (s391). Só leitura.

`casa` é TEXTO em todas as tabelas, e cada grafia é uma casa diferente para o sistema. A regra
única de gravação (`main.casa_oficial`) segura o que entra pelas rotas; este audit pega o que
já está na base e o que entra por fora delas (importadores que gravam `casa` direto no SQL).

FAIL quando:
  1. a mesma casa (sem caixa e sem espaço) aparece em MAIS DE UMA grafia em `parceiros` ou
     `bilhetes` — a gêmea que esconde bilhete da conta;
  2. uma casa REGISTRADA aparece na base numa grafia diferente da oficial — os bilhetes da
     próxima captura iriam para a oficial e a conta não os veria.

**Rode ANTES de registrar casa nova** (`/sharpenup-casa`, Fase 5) e escolha a grafia que a
base já tem. Foi o que faltou na Megapari: a medição procurou a grafia exata.

Saída: a lista e o remédio. A correção é `scripts/unificar_casas.py` (recalcula assinatura).

Uso: python tools/audit_grafias.py   (precisa de DATABASE_URL no .env)
"""
import asyncio
import os
import sys

import asyncpg
from dotenv import load_dotenv

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_RAIZ, ".env"))
sys.path.insert(0, os.path.join(_RAIZ, "app"))
os.environ.setdefault("SESSION_SECRET", "audit-grafias-so-leitura")

from main import _CASA_DISPLAY, _casa_registrada, _norm_casa  # noqa: E402


async def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL ausente: o audit precisa do banco.")
        return 2
    c = await asyncpg.connect(url)
    try:
        contas = {r["casa"]: r["n"] for r in await c.fetch("SELECT casa, COUNT(*) n FROM parceiros GROUP BY casa")}
        bil = {r["casa"]: r["n"] for r in await c.fetch("SELECT casa, COUNT(*) n FROM bilhetes GROUP BY casa")}
    finally:
        await c.close()

    grupos: dict[str, set] = {}
    for casa in set(contas) | set(bil):
        if casa:
            grupos.setdefault(_norm_casa(casa), set()).add(casa)

    falhas = 0
    print(f"Casas na base: {len(grupos)} · registradas: {len(_CASA_DISPLAY)}\n")
    for n, grafias in sorted(grupos.items()):
        oficial = _casa_registrada(next(iter(grafias)))
        fora = sorted(g for g in grafias if oficial and g != oficial)
        if len(grafias) > 1 or fora:
            falhas += 1
            print(f"  FAIL {' / '.join(sorted(grafias))}"
                  + (f"  (registro: {oficial})" if oficial else "  (fora do registro)"))
            for g in sorted(grafias):
                print(f"         {g!r}: {contas.get(g, 0)} conta(s), {bil.get(g, 0)} bilhete(s)")
    if falhas:
        print(f"\nRESULTADO: {falhas} casa(s) com mais de uma grafia. Remédio: MAPA do "
              "scripts/unificar_casas.py (relatório, depois --aplicar).")
        return 1
    print("RESULTADO: uma grafia por casa, e a registrada é a da base.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
