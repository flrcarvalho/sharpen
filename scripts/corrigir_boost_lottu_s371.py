"""Devolve aos bilhetes da Lottu o BOOST que a captura não somava (sessão 371).

O QUE ACONTECEU
---------------
A Lottu paga o boost ("⚡ Bônus +25%") **por fora da odd**, e nenhum dos dois campos de
retorno da API o contém: `return_value` e `gross_return_value` trazem `stake × odd` nua,
e o extra vive sozinho em `promotions.odds_boost.value`. O card soma os dois; o
`formatTicketLT` lia só o primeiro. O bloco cru guardado na sombra mostra o defeito
inteiro (bilhete `8410665`):

    Stake: R$ 100,00
    Odd: 7,38
    Retorno: R$ 738,00                              ← o card diz R$ 922,50
    Marcação da casa: odd turbinada (odds_boost 25%) ← o bônus estava AQUI, sem valor

O erro não parece erro: `stake × odd` fecha exato, o resultado está certo e a linha passa
em toda checagem de forma. Quem acusou foi a **Caixa Inteligente** — R$ 1.124,58 de
divergência contra o saldo real da casa, com o P/L do período batendo centavo a centavo
com a conta feita SEM o boost (R$ 3.602,05, medido na API em 21/09/2026).

A REGRA DE ESCRITA
------------------
`odd_nova = retorno_do_bloco × (1 + pct/100) ÷ stake_do_bloco`, tudo lido do **bloco cru**
daquele código (`sombra_rotulos`), nunca de uma lista digitada. A lista abaixo existe só
para o script ter contra o que conferir: **bloco e lista discordando = não escreve**.
É a mesma disciplina do `corrigir_odd_infiel_s311.py`.

Por que `Retorno ÷ Stake` e não `odd × 1,25`: `return_value` é calculado pela casa sobre a
odd ARREDONDADA do card (7,38, não os 7,3779 da perna), e só o dinheiro fecha exato com o
que a casa pagou. É a regra do W no `MASTER_RESULTADO §7.1`.

O QUE ESTE SCRIPT NÃO FAZ
-------------------------
Não toca em `resultado` (todos já estão `W`, e o boost não muda desfecho), não toca em
`stake`, `data` nem `descricao`, e **pula qualquer bilhete que já tenha correção humana
registrada em `odd`** — certo ou errado, ali a decisão é do dono (CLAUDE.md, "Correção
humana MANDA sobre a captura").

As descrições `Mercado Especial - REVISAR` dos mesmos bilhetes são outro defeito (a perna
do Criador de Apostas não tem `answer`), corrigido na captura e tratado à parte: traduzir
mercado é trabalho da IA com o `MASTER_APOSTAS`, não de um de-para escondido num script.

Uso:
    python scripts/corrigir_boost_lottu_s371.py            # ensaio (não escreve)
    python scripts/corrigir_boost_lottu_s371.py --aplicar
"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

import asyncpg  # noqa: E402
from database import dsn  # noqa: E402
from repository import atualizar_bilhete, _num_or_none  # noqa: E402

DESTINO = ROOT / "Backups" / "s371-lottu-boost" / "bilhetes_antes_odd.json"

# (código, dono, odd esperada, bônus em R$) — medidos na API da casa em 21/09/2026.
# O bônus fica aqui só para o relatório: quem manda na escrita é o bloco cru.
CORRECOES = [
    ("8127985", "Feca", "7,455",  "248,50"),   # +50%, o único; 4,97 → 7,455
    ("8180129", "Feca", "3,90",   "234,00"),
    ("8255637", "Feca", "3,8125", "190,63"),
    ("8262916", "Feca", "3,9625", "206,05"),
    ("8352161", "Feca", "5,3625", "107,25"),
    ("8410665", "Feca", "9,225",  "184,50"),
]

_STAKE = re.compile(r"^Stake:\s*R\$\s*([\d.,]+)", re.MULTILINE)
_RETORNO = re.compile(r"^Retorno:\s*R\$\s*([\d.,]+)", re.MULTILINE)
_BOOST = re.compile(r"odds_boost\s*([\d.,]+)\s*%")


def _odd_do_bloco(bruto: str):
    """Recalcula a odd turbinada a partir do bloco cru. None = o bloco não sustenta."""
    mst, mre, mbo = _STAKE.search(bruto), _RETORNO.search(bruto), _BOOST.search(bruto)
    if not (mst and mre and mbo):
        return None, None
    stake = _num_or_none(mst.group(1))
    retorno = _num_or_none(mre.group(1))
    pct = _num_or_none(mbo.group(1))
    if not stake or not retorno or not pct:
        return None, None
    bonus = retorno * pct / 100.0
    return (retorno + bonus) / stake, bonus


async def main(aplicar: bool) -> int:
    conn = await asyncpg.connect(dsn())
    codigos = [c for c, _d, _o, _b in CORRECOES]

    antes = await conn.fetch(
        """SELECT id, dono, casa, codigo_bilhete, descricao, stake, odd, resultado,
                  extraction_state, assinatura
           FROM bilhetes WHERE codigo_bilhete = ANY($1::text[]) AND casa ILIKE '%lottu%'""",
        codigos)
    por_codigo = {(r["codigo_bilhete"], r["dono"]): dict(r) for r in antes}

    brutos = await conn.fetch(
        """SELECT DISTINCT ON (codigo, dono) codigo, dono, bruto
           FROM sombra_rotulos WHERE codigo = ANY($1::text[])
           ORDER BY codigo, dono, criado_em DESC""", codigos)
    bloco = {(r["codigo"], r["dono"]): r["bruto"] for r in brutos}

    editados = {r["bilhete_id"] for r in await conn.fetch(
        "SELECT DISTINCT bilhete_id FROM correcoes WHERE campo IN ('odd', 'resultado')")}

    if aplicar:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(json.dumps(
            {"gravado_em": datetime.now(timezone.utc).isoformat(),
             "linhas": list(por_codigo.values())},
            ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"snapshot ANTES: {DESTINO}\n")

    mudadas, ganho = 0, 0.0
    for codigo, dono, odd_nova, bonus_txt in CORRECOES:
        atual = por_codigo.get((codigo, dono))
        if not atual:
            print(f"!! {codigo} [{dono}]: não encontrado no banco — PULADO")
            continue
        if atual["id"] in editados:
            print(f"!! {codigo} [{dono}]: já há correção humana de odd/resultado — PULADO")
            continue
        if atual["resultado"] != "W":
            print(f"!! {codigo} [{dono}]: resultado {atual['resultado']!r} ≠ W — PULADO "
                  f"(o bônus só vira dinheiro no ganho)")
            continue
        bruto = bloco.get((codigo, dono))
        if not bruto:
            print(f"!! {codigo} [{dono}]: sem bloco cru na sombra — PULADO (sem prova)")
            continue

        calc, bonus = _odd_do_bloco(bruto)
        if calc is None:
            print(f"!! {codigo} [{dono}]: o bloco não traz stake/retorno/boost — PULADO")
            continue
        if abs(calc - _num_or_none(odd_nova)) > 0.0005:
            print(f"!! {codigo} [{dono}]: o bloco calcula {calc:.4f}, a lista diz {odd_nova} "
                  f"— PULADO (não confere)")
            continue
        if abs(bonus - _num_or_none(bonus_txt)) > 0.02:
            print(f"!! {codigo} [{dono}]: bônus do bloco R$ {bonus:.2f} ≠ lista R$ {bonus_txt} "
                  f"— PULADO (não confere)")
            continue
        if _num_or_none(atual["odd"]) == _num_or_none(odd_nova):
            print(f"=  {codigo} [{dono}] já está correto")
            continue

        stake = _num_or_none(atual["stake"]) or 0
        pl_antes = stake * ((_num_or_none(atual["odd"]) or 0) - 1)
        pl_depois = stake * (_num_or_none(odd_nova) - 1)
        ganho += pl_depois - pl_antes

        print(f"\n{'→' if aplicar else '·'}  #{atual['id']} {codigo} [{dono}] "
              f"{atual['casa']} · {atual['resultado']} · stake {atual['stake']}")
        print(f"     odd: {atual['odd']!r}  →  {odd_nova!r}   (bônus R$ {bonus_txt} conferido no bloco)")
        print(f"     P/L: R$ {pl_antes:,.2f}  →  R$ {pl_depois:,.2f}")
        if aplicar:
            ok = await atualizar_bilhete(atual["id"], {"odd": odd_nova}, dono)
            print(f"     gravado: {ok}")
        mudadas += 1

    print(f"\n=== {mudadas} linha(s) {'corrigida(s)' if aplicar else 'a corrigir (ENSAIO)'} "
          f"· P/L devolvido: R$ {ganho:,.2f} ===")

    if aplicar:
        depois = await conn.fetch(
            """SELECT codigo_bilhete, dono, stake, odd, resultado, assinatura
               FROM bilhetes WHERE codigo_bilhete = ANY($1::text[]) AND casa ILIKE '%lottu%'
               ORDER BY codigo_bilhete""", codigos)
        print("\n=== CONFERÊNCIA (o que está no banco agora) ===")
        for r in depois:
            a = por_codigo[(r["codigo_bilhete"], r["dono"])]
            sig = "assinatura recalculada" if a["assinatura"] != r["assinatura"] else "assinatura intacta"
            print(f"{r['codigo_bilhete']} [{r['dono']}] · stake {r['stake']} · odd {r['odd']} · "
                  f"{r['resultado']} · {sig}")
    await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main("--aplicar" in sys.argv)))
