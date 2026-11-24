"""Stake.com da Ellen [Eu] (Feca): conta cadastrada em USD, carteira em USDT (s465, 24/11/2026).

Decisão do Feca (opção b, 24/11/2026), com a consultoria: a conta `Ellen [Eu]` na Stake.com é
USDT; o cadastro em USD estava errado. O `/salvar` grava na moeda da CONTA (`cambio.py`, regra
5A) e trata USD × USDT como compatíveis, então todo cru em `usdt` desta conta foi convertido pela
régua do dólar (PTAX/BCB) em vez da do USDT (abertura do candle USDT/BRL da Binance). A
`stake_orig` (a moeda da casa) e o P/L em USDT estão certos; erram a cotação, a stake em reais e,
com ela, o P/L em reais.

O que o script faz, numa transação só:
  1. `parceiros.moeda` da conta (id 1842) de USD para USDT: é o mesmo UPDATE da tela de Contas e
     vale para as próximas capturas.
  2. Cada linha da conta gravada em USD: `moeda = USDT`, `cotacao` = USDT/BRL do MESMO dia que o
     `/salvar` usaria (`cambio._iso_da_linha`: o carimbo de colocação do cru, em Brasília) e
     `stake = stake_orig × cotacao` (`cambio._fmt_money`). `stake_orig`, odd, resultado, data e
     o resto ficam como estão.
  3. Rastro: uma linha em `correcoes` por aposta (campo `stake`, antes e depois, a cotação velha e
     a nova na descrição), com origem `script_s465` (RUNBOOK_SCRIPTS_DE_BANCO).
  4. Os lançamentos de Caixa da conta gravados em USD passam a USDT. A Caixa só soma lançamento
     de moeda IGUAL à da conta (`repository._caixa_projetar`, `n_mov_outra_moeda`): trocar a
     conta sem eles tiraria os depósitos da projeção em silêncio. Os valores são da carteira
     (USDT) e não mudam; nenhum tem corretora (`corretora_id`), então o bolso de câmbio não
     muda de lado.

Travas (qualquer uma desfaz tudo e nada é gravado):
  • conta id 1842 = (Feca, Stake.com, Ellen [Eu], USD);
  • linha com freebet, sem `stake_orig`, sem cru, sem carimbo, sem cotação USDT, ou com correção
    HUMANA de stake (`correcoes` com origem NULL) não é tocada e aborta o lote;
  • a cotação USD gravada tem de ser a que o `cambio` dá para o mesmo dia (prova de que o dia
    escolhido é o mesmo do `/salvar`); divergência aborta;
  • o número de linhas atualizadas tem de ser o do plano.

Uso:
  python scripts/s465_moeda_stakecom_ellen.py --url-env TEST_DATABASE_URL [--aplicar]
  python scripts/s465_moeda_stakecom_ellen.py --prod [--aplicar]
  [--ids 1,2,3]   restringe às linhas com esses ids (as demais ficam como estão)
Sem --aplicar é ensaio: transação só leitura, nada escrito.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import cambio  # noqa: E402
import polymarket as _poly  # noqa: E402
from repository import _num_or_none, calcular_pl  # noqa: E402

RASTRO = "script_s465"
PARCEIRO_ID = 1842
DONO, CASA, CONTA, CASA_KEY = "Feca", "Stake.com", "Ellen [Eu]", "STAKECOM"
DE, PARA = "USD", "USDT"


def _url_prod() -> str:
    out = subprocess.run(["railway", "variables", "--service", "Postgres", "--kv"],
                         cwd=str(ROOT), capture_output=True, text=True, shell=True).stdout
    for ln in out.splitlines():
        if ln.startswith("DATABASE_PUBLIC_URL="):
            return ln.split("=", 1)[1].strip()
    raise SystemExit("sem DATABASE_PUBLIC_URL")


def _carimbo(cru: dict) -> str | None:
    """`createdAt` do cru em Brasília, no formato do `virada._carimbo` (14 dígitos)."""
    b = (cru or {}).get("bet") or {}
    v = b.get("createdAt")
    if not v:
        return None
    try:
        d = datetime.strptime(v, "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None
    return d.astimezone(_poly.BRT).strftime("%Y%m%d%H%M%S")


def _fmt(x) -> str:
    return "—" if x is None else f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def main(url: str, aplicar: bool, ids: set[int] | None) -> int:
    import asyncpg
    conn = await asyncpg.connect(url, timeout=30)
    erros: list[str] = []
    try:
        tr = conn.transaction(readonly=not aplicar)
        await tr.start()
        conta = await conn.fetchrow("SELECT id, dono, casa, nome, moeda FROM parceiros WHERE id = $1",
                                    PARCEIRO_ID)
        if not conta or (conta["dono"], conta["casa"], conta["nome"]) != (DONO, CASA, CONTA) \
                or conta["moeda"] != DE:
            print("ABORTADO: conta não confere:", conta and dict(conta))
            await tr.rollback()
            return 1
        caixa = await conn.fetch(
            "SELECT id, tipo, data, valor, moeda, corretora_id FROM caixa_mov WHERE parceiro_id = $1 "
            "ORDER BY id", PARCEIRO_ID)
        print(f"conta {dict(conta)} · movimentos de Caixa: {len(caixa)}")
        caixa_usd = [m for m in caixa if m["moeda"] == DE]
        for m in caixa:
            print(f"  caixa {m['id']} {m['tipo']:<12} {m['data']} {m['valor']:>10} "
                  f"{m['moeda'] or '(vazia)'} → {PARA if m['moeda'] == DE else 'fica'}")
            if m["corretora_id"] is not None:
                erros.append(f"caixa {m['id']}: tem corretora; o bolso de câmbio mudaria de lado")
        linhas = await conn.fetch(
            "SELECT id, codigo_bilhete, stake, stake_orig, cotacao, stake_freebet, odd, resultado, "
            "data, extraction_state, origem FROM bilhetes "
            "WHERE dono = $1 AND casa = $2 AND parceiro = $3 AND moeda = $4 ORDER BY id",
            DONO, CASA, CONTA, DE)
        if ids is not None:
            linhas = [r for r in linhas if r["id"] in ids]
            faltam = ids - {r["id"] for r in linhas}
            if faltam:
                erros.append(f"ids pedidos que não são linha USD desta conta: {sorted(faltam)}")
        humanos = {r["bilhete_id"] for r in await conn.fetch(
            "SELECT DISTINCT bilhete_id FROM correcoes WHERE bilhete_id = ANY($1::bigint[]) "
            "AND campo = 'stake' AND origem IS NULL", [r["id"] for r in linhas])}
        plano = []
        isos = {}
        for r in linhas:
            cru = await conn.fetchval(
                "SELECT cru FROM captura_crua WHERE dono = $1 AND casa = $2 AND codigo = $3 "
                "ORDER BY recebido_em DESC, id DESC LIMIT 1", DONO, CASA_KEY, r["codigo_bilhete"])
            cru = json.loads(cru) if isinstance(cru, str) else cru
            car = _carimbo(cru) if cru else None
            if r["id"] in humanos:
                erros.append(f"{r['id']}: stake com correção humana")
            elif r["stake_freebet"] is not None:
                erros.append(f"{r['id']}: tem freebet")
            elif r["stake_orig"] is None:
                erros.append(f"{r['id']}: sem stake_orig")
            elif not car:
                erros.append(f"{r['id']}: sem cru ou sem createdAt")
            else:
                iso = cambio._iso_da_linha({"data": r["data"]}, car)
                isos[r["id"]] = iso
                plano.append((r, iso, (cru.get("bet") or {}).get("currency")))
        todas = sorted(set(isos.values()))
        await cambio.carregar("USD", todas)
        await cambio.carregar("USDT", todas)

        print(f"\n{'id':>7} {'código':>10} {'dia':>10} {'res':>3} {'orig':>8} "
              f"{'cot USD':>8} {'cot USDT':>8} {'stake R$ antes':>15} {'depois':>12} "
              f"{'P/L R$ antes':>13} {'depois':>12}")
        tot = {"st0": Decimal(0), "st1": Decimal(0), "pl0": Decimal(0), "pl1": Decimal(0)}
        novos = []
        for r, iso, moeda_cru in plano:
            if str(moeda_cru or "").lower() not in ("usdt", "usdc"):
                erros.append(f"{r['id']}: cru em {moeda_cru!r}, não USDT")
                continue
            usd = cambio.cotacao("USD", iso)
            usdt = cambio.cotacao("USDT", iso)
            if not usdt:
                erros.append(f"{r['id']}: sem cotação USDT para {iso}")
                continue
            if usd is None or abs(Decimal(str(round(usd, 6))) - r["cotacao"]) > Decimal("0.000001"):
                erros.append(f"{r['id']}: cotação gravada {r['cotacao']} ≠ USD do dia {iso} ({usd})")
                continue
            orig = float(r["stake_orig"])
            novo = cambio._fmt_money(orig * usdt)
            pl0 = calcular_pl(r["stake"], r["odd"], r["resultado"])
            pl1 = calcular_pl(novo, r["odd"], r["resultado"])
            st0 = _num_or_none(r["stake"])
            tot["st0"] += Decimal(str(st0))
            tot["st1"] += Decimal(str(_num_or_none(novo)))
            tot["pl0"] += Decimal(str(pl0 or 0))
            tot["pl1"] += Decimal(str(pl1 or 0))
            print(f"{r['id']:>7} {r['codigo_bilhete']:>10} {iso:>10} {r['resultado'] or '':>3} "
                  f"{orig:>8.2f} {float(r['cotacao']):>8.4f} {usdt:>8.4f} {r['stake']:>15} {novo:>12} "
                  f"{_fmt(pl0):>13} {_fmt(pl1):>12}")
            novos.append((r, round(usdt, 6), novo, iso))
        print(f"\nlinhas: {len(novos)} de {len(linhas)}")
        print(f"stake em R$: {_fmt(tot['st0'])} → {_fmt(tot['st1'])} ({_fmt(tot['st1'] - tot['st0'])})")
        print(f"P/L em R$:   {_fmt(tot['pl0'])} → {_fmt(tot['pl1'])} ({_fmt(tot['pl1'] - tot['pl0'])})")
        if erros:
            print("\nABORTADO, nada gravado:\n  " + "\n  ".join(erros))
            await tr.rollback()
            return 1
        if not aplicar:
            await tr.rollback()
            print("\nENSAIO: transação só leitura, nada gravado (use --aplicar).")
            return 0

        st = await conn.execute(
            "UPDATE parceiros SET moeda = $1 WHERE id = $2 AND dono = $3 AND casa = $4 AND nome = $5 "
            "AND moeda = $6", PARA, PARCEIRO_ID, DONO, CASA, CONTA, DE)
        if st != "UPDATE 1":
            await tr.rollback()
            print("ABORTADO: a conta não mudou (", st, "); nada gravado.")
            return 1
        n = 0
        for r, usdt, novo, iso in novos:
            st = await conn.execute(
                "UPDATE bilhetes SET moeda = $1, cotacao = $2, stake = $3 "
                "WHERE id = $4 AND dono = $5 AND casa = $6 AND parceiro = $7 AND moeda = $8 "
                "AND stake = $9", PARA, Decimal(str(usdt)), novo, r["id"], DONO, CASA, CONTA, DE,
                r["stake"])
            if st != "UPDATE 1":
                await tr.rollback()
                print(f"ABORTADO em {r['id']} ({st}); nada gravado.")
                return 1
            await conn.execute(
                "INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, valor_novo, "
                "descricao, origem) VALUES ($1, $2, $3, 'stake', $4, $5, $6, $7)",
                r["id"], DONO, CASA, r["stake"], novo,
                f"s465: conta cadastrada em USD com carteira USDT; {r['stake_orig']} USDT de {iso}, "
                f"cotação {r['cotacao']} (USD/PTAX) → {usdt} (USDT/Binance)", RASTRO)
            n += 1
        if n != len(novos):
            await tr.rollback()
            print("ABORTADO: contagem diferente do plano; nada gravado.")
            return 1
        st = await conn.execute(
            "UPDATE caixa_mov SET moeda = $1 WHERE parceiro_id = $2 AND moeda = $3 "
            "AND corretora_id IS NULL AND id = ANY($4::bigint[])",
            PARA, PARCEIRO_ID, DE, [m["id"] for m in caixa_usd])
        if st != f"UPDATE {len(caixa_usd)}":
            await tr.rollback()
            print(f"ABORTADO na Caixa ({st}, esperava {len(caixa_usd)}); nada gravado.")
            return 1
        await tr.commit()
        print(f"\nGRAVADO: conta {DE} → {PARA}, {n} linhas e {len(caixa_usd)} lançamentos de "
              f"Caixa; rastro {RASTRO} em correcoes.")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url-env")
    g.add_argument("--prod", action="store_true")
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--ids", help="ids separados por vírgula")
    a = ap.parse_args()
    url = _url_prod() if a.prod else os.environ[a.url_env]
    sel = {int(x) for x in a.ids.split(",")} if a.ids else None
    sys.exit(asyncio.run(main(url, a.aplicar, sel)))
