"""Corrige 5 linhas da Vavada cujo resultado/odd não bate com o dinheiro do cru (s453, 14/11/2026).

Achado da varredura com agentes (somente leitura) depois do "nunca acerta" do Gabriel:

  • 399827 (Feca [Eu], 5579339795): L, mas a casa RELIQUIDOU para ganha (status 1, retorno 191,25
    sobre 75) em 27/10, antes do conserto da s448; a linha nunca reabriu. → W @ 2,55.
  • 400375 (Feca [Eu], 5581722163): W @ 12,04, mas o cru final diz perdida (status 2, retorno 0). → L.
  • 381869 (Feca [Eu]), 412346 (laurabianchi146), 429158 (lospanasbr): W com a odd do bilhete, mas
    a casa pagou mais (boost): odd = retorno ÷ stake (7,6 · 5,7718 · 11,036).

Correção humana manda (CLAUDE.md): só se escreve campo SEM correção humana. 412346 e 429158 têm
`resultado` humano (W, que o dinheiro confirma): só a odd muda. Todo o resto: tipster/data, não
tocados. As contas em USDT: stake e retorno lidos em `stake_orig` (a moeda da casa).

A Caixa: os Ajustes de conferência JÁ ABSORVERAM estes erros (Feca Vavada −168,81 em 28/10 ≈
−168,67 das três linhas; laurabianchi146 +4,10 em 03/11 ≈ +4,68 da odd). Corrigir a linha sem
mexer no Ajuste contaria o mesmo dinheiro duas vezes, então o Ajuste fica só com o RESÍDUO
(valor antigo − efeito da correção), com a observação dizendo isso. lospanasbr não tem
conferência: a projeção dela sobe 9,83, que é o que a casa pagou.

    python scripts/corrigir_vavada_dinheiro_s453.py            # ensaio, nada escrito
    python scripts/corrigir_vavada_dinheiro_s453.py --aplicar
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from database import get_pool  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

RASTRO = "script_s453"
CENT = Decimal("0.01")
# id → (dono, código)
ALVOS = {
    399827: ("Feca", "5579339795"), 400375: ("Feca", "5581722163"), 381869: ("Feca", "5520005256"),
    412346: ("Gabriel", "5602432981"), 429158: ("Gabriel", "5633424308"),
}
AJ_FECA = ("Feca", "Feca [Eu]", Decimal("-168.81"), {399827, 400375, 381869})
AJ_LAURA = ("Gabriel", "laurabianchi146 [Fatuch]", Decimal("4.10"), {412346})


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


def _dec(v) -> Decimal:
    s = str(v)
    return Decimal(s.replace(".", "").replace(",", ".")) if "," in s else Decimal(s)


def _pl(stake: Decimal, odd: Decimal, res: str) -> Decimal:
    return stake * (odd - 1) if res == "W" else (-stake if res == "L" else Decimal(0))


def _br(d: Decimal) -> str:
    return format(d.normalize(), "f").replace(".", ",")


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    pool = await get_pool()
    plano, efeito, erros = [], {}, []
    async with pool.acquire() as conn:
        for bid, (dono, cod) in ALVOS.items():
            r = await conn.fetchrow(
                "SELECT id, dono, parceiro, codigo_bilhete, stake_orig, odd, resultado FROM bilhetes "
                "WHERE id = $1 AND dono = $2 AND casa = 'Vavada' AND codigo_bilhete = $3", bid, dono, cod)
            cru = await conn.fetchval(
                "SELECT cru FROM captura_crua WHERE dono = $1 AND upper(casa) = 'VAVADA' AND codigo = $2 "
                "ORDER BY recebido_em DESC LIMIT 1", dono, cod)
            humanos = {x["campo"] for x in await conn.fetch(
                "SELECT campo FROM correcoes WHERE bilhete_id = $1 AND origem IS NULL", bid)}
            if not r or cru is None or r["stake_orig"] is None:
                erros.append(f"{bid}: linha/cru/stake_orig ausente"); continue
            cru = json.loads(cru) if isinstance(cru, str) else cru
            st, ret = _dec(r["stake_orig"]), _dec(cru.get("totalWin"))
            if abs(st - _dec(cru.get("totalStake"))) >= CENT:
                erros.append(f"{bid}: stake {st} × cru {cru.get('totalStake')}"); continue
            status = str(cru.get("status"))
            if status == "2" and ret == 0:
                novo_res, nova_odd = "L", _dec(r["odd"])
            elif status == "1" and ret > st:
                novo_res, nova_odd = "W", (ret / st).quantize(Decimal("0.00000001"))
            else:
                erros.append(f"{bid}: cru status {status} retorno {ret} não prova"); continue
            mud = {}
            if novo_res != r["resultado"]:
                if "resultado" in humanos:
                    erros.append(f"{bid}: resultado humano {r['resultado']} ≠ dinheiro {novo_res}"); continue
                mud["resultado"] = novo_res
            if novo_res == "W" and abs(nova_odd - _dec(r["odd"])) * st >= Decimal("1.00"):
                if "odd" in humanos:
                    erros.append(f"{bid}: odd humana"); continue
                mud["odd"] = _br(nova_odd)
            antes = _pl(st, _dec(r["odd"]), r["resultado"])
            depois = _pl(st, nova_odd, novo_res)
            efeito[bid] = depois - antes
            print(f"{bid} {r['parceiro']} {cod}: {r['resultado']} @ {r['odd']} → {mud or 'nada'} "
                  f"(P/L {antes:.2f} → {depois:.2f} USDT)")
            if mud:
                plano.append((bid, dono, mud))
        ajs = []
        for dono, conta, valor, ids in (AJ_FECA, AJ_LAURA):
            rows = await conn.fetch(
                "SELECT m.id, m.valor, m.obs FROM caixa_mov m JOIN parceiros p ON p.id = m.parceiro_id "
                "WHERE m.dono = $1 AND p.casa = 'Vavada' AND p.nome = $2 AND m.tipo = 'ajuste'", dono, conta)
            if len(rows) != 1 or rows[0]["valor"] != valor:
                erros.append(f"ajuste de {conta}: esperava um só de {valor}, achei {[dict(x) for x in rows]}")
                continue
            soma = sum((efeito.get(i, Decimal(0)) for i in ids), Decimal(0))
            resid = (valor - soma).quantize(CENT)
            print(f"ajuste {rows[0]['id']} ({conta}): {valor} → {resid} (absorvia {soma:.2f} das linhas)")
            ajs.append((rows[0]["id"], dono, resid, rows[0]["obs"] or ""))
    if erros:
        print("NADA ESCRITO:\n  " + "\n  ".join(erros))
        return
    if not aplicar:
        print("\nENSAIO: nada escrito (use --aplicar).")
        return
    for bid, dono, mud in plano:
        ok = await atualizar_bilhete(bid, mud, dono, rastro=RASTRO)
        print(f"{bid}: {'gravado' if ok else 'atualizar_bilhete RECUSOU'}")
        if not ok:
            print("PARADO antes dos ajustes."); return
    async with pool.acquire() as conn:
        for mid, dono, resid, obs in ajs:
            await conn.execute(
                "UPDATE caixa_mov SET valor = $1, obs = $2 WHERE id = $3 AND dono = $4 AND tipo = 'ajuste'",
                resid, (obs + " · s453: resíduo depois de corrigir as apostas pelo dinheiro da casa")[:280],
                mid, dono)
            print(f"ajuste {mid}: {resid}")


if __name__ == "__main__":
    asyncio.run(main())
