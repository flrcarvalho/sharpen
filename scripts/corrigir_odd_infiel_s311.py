"""Corrige as ODDS que não seguem nenhuma regra do sistema (sessão 311).

Irmão do `corrigir_stake_infiel_s311.py`. Enquanto aquele nasceu da stake que pula de
bilhete, este nasceu da varredura que veio junto: **3.692 odds conferidas contra o bloco
cru** (`sombra_rotulos`, 26/08–01/09, 20 casas), classificadas pelas regras legítimas do
sistema — odd do bloco verbatim (3.646), `Retorno ÷ Stake` em W/cashout (27) e média das
linhas de sistema (15). **Sobraram 4**, e as 4 são erro.

Nenhuma delas mexe em dinheiro: são todas `L` ou `HL`, e `calcular_pl` não usa a odd
nesses códigos (`L → 0`, `HL → stake/2`). O que elas estragam é o número na tela, o
retorno potencial e qualquer análise por odd.

  1. Betano `20926898412` — `3 x Duplas` lido como TRIPLA. A odd de sistema é a MÉDIA das
     linhas (`MASTER_RESULTADO §7.3`: `(ab+ac+bc)/3`), nunca o produto. O banco tem
     17,388, que não é nem a média (6,7425) nem o produto (17,442) — a IA tentou o
     produto e ainda errou a conta.
  2. Betfast `301490938` — mesmo caso: `Tipo: Sistema (3 seleções)`, média = 5,27733…
  3. Betfast `301491163` — o gêmeo do anterior (mesmas 3 seleções, apostadas também como
     múltipla cheia). Aqui a regra é o PRODUTO, e ele já está impresso no bloco: 11,766.
     **Estes dois são os mesmos bilhetes que a s302 corrigiu na descrição** — o carryover
     tinha atingido os dois campos, e só a descrição foi olhada na época.
  4. Bet365 `JR3841878921I` — meia asiática com metade devolvida (`retorno R$ 40,18` =
     exatamente metade da stake → HL). A odd que vale é a exibida, 2,05; o banco tem 1,85.

RAIZ (não corrigida aqui, é mudança de captura): Bet365 e Novibet emitem o marcador
canônico `Tipo: SISTEMA <rótulo> — <N> apostas de <k> seleção(ões)` **e** a
`Odd (estrutural do sistema)` já calculada — e acertaram 15 de 15. Betano ("Tipo: Dupla")
e Betfast ("Tipo: Sistema (3 seleções)") **não emitem nenhum dos dois**, então a IA tem de
deduzir a regra da odd, e a coluna 12 (`sistema`) nunca é preenchida para essas casas.

REGRA DE ESCRITA: o script **recalcula a odd das odds das pernas do próprio bloco** e só
grava se o valor bater com o esperado desta lista. Lista e bloco discordando = não escreve.

Uso:
    python scripts/corrigir_odd_infiel_s311.py            # ensaio (não escreve)
    python scripts/corrigir_odd_infiel_s311.py --aplicar
"""
import asyncio
import itertools
import json
import math
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

DESTINO = ROOT / "Backups" / "s311-stake-infiel" / "bilhetes_antes_odd.json"

# (código, dono, odd nova, regra de conferência, motivo)
#   "media2" = média das C(n,2) duplas · "produto" = produto das pernas · "exibida" = a
#   odd que o bloco imprime, verbatim.
CORRECOES = [
    ("20926898412", "Gabriel", "6,7425", "media2",
     "3x Duplas lido como tripla; MASTER_RESULTADO §7.3 manda a média das 3 linhas"),
    ("301490938", "Gabriel", "5,27733333333333", "media2",
     "Tipo: Sistema (3 seleções) — média das 3 duplas; o gêmeo do 301491163"),
    ("301491163", "Gabriel", "11,766", "produto",
     "Múltipla cheia das mesmas 3 seleções — produto das pernas, já impresso no bloco"),
    ("JR3841878921I", "Jonathan", "2,05", "exibida",
     "meia asiática HL (retorno = metade da stake); a odd que vale é a exibida"),
]

_ODD_BLOCO = re.compile(r"^[ \t]*Odd(?: total)?:[ \t]*([\d.,]+)", re.MULTILINE)
_PERNA = re.compile(r"Odd da perna:[ \t]*([\d.,]+)")
_ARROBA = re.compile(r"@[ \t]*([\d.,]+)")


def _pernas(bruto: str) -> list[float]:
    achadas = _PERNA.findall(bruto) or _ARROBA.findall(bruto)
    return [v for v in (_num_or_none(x) for x in achadas) if v]


def _esperada(bruto: str, regra: str) -> float | None:
    """Recalcula a odd a partir do bloco. None = o bloco não sustenta a regra."""
    if regra == "exibida":
        m = _ODD_BLOCO.search(bruto)
        return _num_or_none(m.group(1)) if m else None
    pernas = _pernas(bruto)
    if len(pernas) < 2:
        return None
    if regra == "produto":
        return math.prod(pernas)
    if regra == "media2":
        combos = list(itertools.combinations(pernas, 2))
        return sum(math.prod(c) for c in combos) / len(combos)
    return None


async def main(aplicar: bool) -> int:
    conn = await asyncpg.connect(dsn())
    codigos = [c for c, _d, _o, _r, _m in CORRECOES]
    antes = await conn.fetch(
        """SELECT id, dono, casa, codigo_bilhete, descricao, stake, odd, resultado,
                  sistema, extraction_state, assinatura
           FROM bilhetes WHERE codigo_bilhete = ANY($1::text[])""", codigos)
    por_codigo = {(r["codigo_bilhete"], r["dono"]): dict(r) for r in antes}

    brutos = await conn.fetch(
        """SELECT DISTINCT ON (codigo, dono) codigo, dono, bruto
           FROM sombra_rotulos WHERE codigo = ANY($1::text[])
           ORDER BY codigo, dono, criado_em DESC""", codigos)
    bloco = {(r["codigo"], r["dono"]): r["bruto"] for r in brutos}

    editados = {r["bilhete_id"] for r in await conn.fetch(
        "SELECT DISTINCT bilhete_id FROM correcoes WHERE campo = 'odd'")}

    if aplicar:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(json.dumps(
            {"gravado_em": datetime.now(timezone.utc).isoformat(),
             "linhas": list(por_codigo.values())},
            ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"snapshot ANTES: {DESTINO}\n")

    mudadas = 0
    for codigo, dono, odd_nova, regra, motivo in CORRECOES:
        atual = por_codigo.get((codigo, dono))
        if not atual:
            print(f"!! {codigo} [{dono}]: não encontrado no banco — PULADO")
            continue
        if atual["id"] in editados:
            print(f"!! {codigo} [{dono}]: já há correção de odd registrada — PULADO")
            continue
        bruto = bloco.get((codigo, dono))
        if not bruto:
            print(f"!! {codigo} [{dono}]: sem bloco cru na sombra — PULADO (sem prova)")
            continue

        calc = _esperada(bruto, regra)
        if calc is None or abs(calc - _num_or_none(odd_nova)) > 0.0005:
            print(f"!! {codigo} [{dono}]: bloco calcula {calc}, a lista diz {odd_nova} "
                  f"(regra {regra}) — PULADO (não confere)")
            continue
        if _num_or_none(atual["odd"]) == _num_or_none(odd_nova):
            print(f"=  {codigo} [{dono}] já está correto")
            continue

        print(f"\n{'→' if aplicar else '·'}  #{atual['id']} {codigo} [{dono}] "
              f"{atual['casa']} · {atual['resultado']} · {atual['descricao'][:60]}")
        print(f"     motivo: {motivo}  (regra {regra} sobre {_pernas(bruto)})")
        print(f"     odd: {atual['odd']!r}  →  {odd_nova!r}")
        if aplicar:
            ok = await atualizar_bilhete(atual["id"], {"odd": odd_nova}, dono)
            print(f"     gravado: {ok}")
        mudadas += 1

    print(f"\n=== {mudadas} linha(s) {'corrigida(s)' if aplicar else 'a corrigir (ENSAIO)'} ===")

    if aplicar:
        depois = await conn.fetch(
            """SELECT codigo_bilhete, dono, casa, stake, odd, resultado, assinatura
               FROM bilhetes WHERE codigo_bilhete = ANY($1::text[]) ORDER BY codigo_bilhete""",
            codigos)
        print("\n=== CONFERÊNCIA (o que está no banco agora) ===")
        for r in depois:
            a = por_codigo[(r["codigo_bilhete"], r["dono"])]
            sig = "assinatura recalculada" if a["assinatura"] != r["assinatura"] else "assinatura intacta"
            print(f"{r['codigo_bilhete']} [{r['dono']}] {r['casa']} · odd {r['odd']} · "
                  f"{r['resultado']} · {sig}")
    await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main("--aplicar" in sys.argv)))
