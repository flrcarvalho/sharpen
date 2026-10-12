"""Métrica de cada virada (pedido do Feca, 12/10/2026; s411): por casa, antes × depois.
Banco: só SELECT. Sem IA, sem custo.

    python docs/PROJETO_FICHA_SHARPEN/medicoes/medir_virada_custo.py [--desde ISO] [--dias N]

`--desde` = o instante da virada (padrão: 2026-10-12T19:40Z, quando as 8 casas viraram);
`--dias` = a janela ANTES dele (padrão 7). Todos os donos (a chave vale para a casa inteira).

DEPOIS (`virada_log`, uma linha por `/extrair` da casa virada, gravada pelo pré-dedup):
  capturas         quantos `/extrair`
  capturadas       códigos distintos no texto, somados
  IA não leu       capturadas − enviadas à IA (já liquidadas no banco + resolvidas pela Ficha +
                   bloco sem mudança desde a última leitura); "pela Ficha" sai à parte
  custo/captura    soma de `uso_tokens.custo_usd` da casa desde a virada ÷ capturas

ANTES (sem `virada_log`, que não existia):
  capturas c/ IA   linhas de `uso_tokens` (uma por extração que chegou à IA; captura que o
                   pré-dedup zerou não deixa linha, então ANTES conta só as que pagaram)
  lidas pela IA    blocos em `sombra_rotulos` (um por bilhete por extração)
  custo/captura    custo ÷ capturas com IA

Por isso o "custo por captura" de antes é um TETO (só as capturas que pagaram); o de depois
divide por todas. A comparação honesta é o custo TOTAL por dia e as lidas pela IA por dia.
"""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402

CASAS = {"MYSTAKE": "MyStake", "DEXSPORT": "DEX Sport", "BETPANDA": "Betpanda", "DUEL": "Duel",
         "SHUFFLE": "Shuffle", "VAVADA": "Vavada", "BETMARTINI": "BetMartini",
         "MEGAPARI": "Megapari"}


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _arg(nome, padrao):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    desde = datetime.fromisoformat(_arg("--desde", "2026-10-12T19:40:00+00:00"))
    dias = float(_arg("--dias", "7"))
    ini = desde - timedelta(days=dias)
    agora = datetime.now(timezone.utc)
    dias_depois = max((agora - desde).total_seconds() / 86400, 1e-9)
    pool = await get_pool()
    async with pool.acquire() as conn:
        print(f"ANTES: {ini:%d/%m %H:%M} → {desde:%d/%m %H:%M} UTC ({dias:g} dias) · "
              f"DEPOIS: {desde:%d/%m %H:%M} → agora ({dias_depois * 24:.1f} h)\n")
        for key, nome in CASAS.items():
            a = await conn.fetchrow(
                "SELECT count(*) AS n, coalesce(sum(custo_usd), 0) AS c FROM uso_tokens "
                "WHERE casa = $1 AND criado_em >= $2 AND criado_em < $3", nome, ini, desde)
            lidas_a = await conn.fetchval(
                "SELECT count(*) FROM sombra_rotulos WHERE casa = $1 AND criado_em >= $2 "
                "AND criado_em < $3", nome, ini, desde)
            d = await conn.fetchrow(
                "SELECT count(*) AS n, coalesce(sum(capturadas), 0) AS cap, "
                "coalesce(sum(para_ia), 0) AS ia, coalesce(sum(pela_ficha), 0) AS f, "
                "coalesce(avg(espera_s), 0) AS esp, "
                "sum(ficha_recusada) AS \"Ficha recusada\", sum(termo_fora) AS \"termo fora\", "
                "sum(fora_do_master) AS \"fora do Master\", "
                "sum(recusada_salvar) AS \"recusada no /salvar\", "
                "sum(cru_nao_chegou) AS \"cru não chegou\", "
                "sum(sem_cru_novo) AS \"texto mudou sem cru novo\" FROM virada_log "
                "WHERE casa = $1 AND criado_em >= $2", key, desde)
            motivos = ", ".join(f"{k} {d[k]}" for k in list(d.keys())[5:] if d[k])
            custo_d = await conn.fetchval(
                "SELECT coalesce(sum(custo_usd), 0) FROM uso_tokens WHERE casa = $1 "
                "AND criado_em >= $2", nome, desde)
            antes = (f"antes: {a['n']} capturas c/ IA, {lidas_a} lidas pela IA, "
                     f"US$ {a['c']:.2f} (US$ {a['c'] / a['n'] if a['n'] else 0:.3f}/captura c/ IA, "
                     f"US$ {a['c'] / dias:.2f}/dia)")
            if d["n"]:
                depois = (f"depois: {d['n']} capturas, {d['cap']} capturadas, IA não leu "
                          f"{d['cap'] - d['ia']} (pela Ficha {d['f']}), US$ {custo_d:.2f} "
                          f"(US$ {custo_d / d['n']:.3f}/captura), espera média {d['esp']:.1f} s"
                          + (f"\n{'':11} à IA por motivo (desde s412): {motivos}" if motivos else ""))
            else:
                depois = "depois: nenhuma captura ainda"
            print(f"{nome:11} {antes}\n{'':11} {depois}")


if __name__ == "__main__":
    asyncio.run(main())
