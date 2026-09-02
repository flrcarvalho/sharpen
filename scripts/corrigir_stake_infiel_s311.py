"""Corrige a STAKE que a IA copiou do bilhete vizinho no mesmo chunk (sessão 311).

A s302 documentou o carryover na **descrição** e registrou, como observação medida, que
"o financeiro não viaja junto". Esta sessão provou que viaja. O caso que abriu:

    Pinnacle 3113103675 (LOUD v MIBR) · bloco cru do robô:
        Stake: 204,00 · P/L 330,48 · Odd total: 2,620
    Banco:
        stake 400,00 · odd 1,826199999999999

400,00 é a stake do bilhete `3114339695` (Patrick Rivera), **duas linhas acima no mesmo
chunk**. A odd saiu certa a partir da stake errada — a `CASA_PINNACLE §11` manda derivar
`odd = Retorno ÷ Stake` em W, e `(400 + 330,48) ÷ 400 = 1,8262`. Por isso o P/L continua
exato e **nada** acusa: `checar_descricao` e `checar_fidelidade` passam (a descrição está
certa), a cobertura conta o bilhete, o resultado bate. O que quebra é o turnover, o ROI e
a assinatura de stake que o matcher de tipster usa.

Medido na sombra inteira (26/08–01/09, 3.700 bilhetes com `Stake:` no bloco, 15 casas):
**3 divergências reais** — esta, mais duas do WilliamOliveira (BETesporte 195072327,
Betano 20951200252). Uma quarta era correção humana legítima (Jaao26/KTO), e por isso o
script **pula toda linha que já tenha `correcoes.campo = 'stake'`**: onde o humano já
decidiu, o bloco cru não manda.

POR QUE PRECISA DE SCRIPT: o UPSERT congela `stake`/`odd` assim que a linha resolve
(`repository.py`, `ON CONFLICT`, fora de `origem='sync'`). Recapturar a casa NÃO conserta.

REGRA DE ESCRITA — só grava o que o bloco cru PROVA:
  • `stake`  = o `Stake:` do bloco daquele código, verbatim.
  • `odd`    = só em W e só quando o bloco traz `P/L`: `(stake + P/L) ÷ stake`. Se o
               `Odd total:` do bloco bater com essa conta (±0,005), grava o texto do
               bloco, preservando a precisão original (`CASA_PINNACLE §11`). Em L/V a
               odd não depende da stake e fica intacta.
  • `tipster` NÃO entra. Ele é inferência, não está no bloco — com a stake certa o
               "Sugerir tipsters" volta a propor sozinho.

Cada linha da lista foi conferida contra o bloco, e o script **reconfere em tempo de
execução**: se o bloco não disser o valor esperado, a linha é pulada.

Escreve pelo caminho sancionado (`repository.atualizar_bilhete`), que registra em
`correcoes` e recalcula a assinatura — `stake` e `odd` estão em `_SIG_COLS`, e linha com
hash velho duplica na próxima captura.

Uso:
    python scripts/corrigir_stake_infiel_s311.py            # ensaio (não escreve)
    python scripts/corrigir_stake_infiel_s311.py --aplicar
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

# O console do Windows abre em cp1252 e engasga na seta e nos acentos do relatório.
sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

import asyncpg  # noqa: E402
from database import dsn  # noqa: E402
from repository import atualizar_bilhete  # noqa: E402

DESTINO = ROOT / "Backups" / "s311-stake-infiel" / "bilhetes_antes.json"

# (código, dono, stake que o bloco cru manda, motivo)
# As três divergências que a varredura da sombra achou. As duas do WilliamOliveira são
# base de outro dono; o Feca autorizou ("se tem erro precisa ser corrigido"). As duas são
# `L`, então só a stake muda — a odd de uma perda não depende dela.
CORRECOES = [
    ("3113103675", "Feca", "204,00",
     "carryover de stake: 400,00 é do 3114339695 (Patrick Rivera), 2 linhas acima no chunk"),

    ("195072327", "WilliamOliveira", "20,00",
     "carryover: 18,00 é do 195134703, vizinho imediato COM A MESMA descrição"),
    ("20951200252", "WilliamOliveira", "164,09",
     "carryover: 60,00 é do 20951198152, vizinho que também começa por Cameron Norrie"),
]


def _num(txt):
    """'R$ 1.234,56' → 1234.56. Devolve None no que não for número."""
    if txt is None:
        return None
    s = str(txt).replace("R$", "").replace("−", "-").strip()
    s = s.replace(".", "").replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _campo(bruto: str, rotulo: str) -> str | None:
    m = re.search(rf"{rotulo}:\s*([^\n]+)", bruto or "")
    return m.group(1).strip() if m else None


def _odd_esperada(bruto: str, resultado: str, stake: float) -> str | None:
    """Odd que a stake certa produz em W (`CASA_PINNACLE §11`: Retorno ÷ Stake, e o
    Retorno sai do P/L). Devolve None quando não dá para provar — em L/V a odd não
    depende da stake, e sem `P/L` no bloco não há de onde derivar."""
    if (resultado or "").strip().upper() != "W" or not stake:
        return None
    m = re.search(r"P/L\s*(-?[\d.,]+)", bruto or "")
    pl = _num(m.group(1)) if m else None
    if pl is None:
        return None
    calculada = (stake + pl) / stake
    exibida = _campo(bruto, "Odd total")
    if exibida is not None and (_num(exibida) is not None) and abs(_num(exibida) - calculada) <= 0.005:
        return exibida                       # preserva a precisão original do bloco
    return f"{calculada:.6f}".rstrip("0").rstrip(".").replace(".", ",")


async def main(aplicar: bool) -> int:
    conn = await asyncpg.connect(dsn())
    codigos = [c for c, _d, _s, _m in CORRECOES]
    if not codigos:
        print("nada na lista.")
        await conn.close()
        return 0

    antes = await conn.fetch(
        """SELECT id, dono, casa, parceiro, codigo_bilhete, data, descricao, stake, odd,
                  resultado, tipster, extraction_state, assinatura
           FROM bilhetes WHERE codigo_bilhete = ANY($1::text[])""", codigos)
    por_codigo = {(r["codigo_bilhete"], r["dono"]): dict(r) for r in antes}

    # Bloco cru do robô — a fonte de verdade desta correção.
    brutos = await conn.fetch(
        """SELECT DISTINCT ON (codigo, dono) codigo, dono, bruto
           FROM sombra_rotulos WHERE codigo = ANY($1::text[])
           ORDER BY codigo, dono, criado_em DESC""", codigos)
    bloco = {(r["codigo"], r["dono"]): r["bruto"] for r in brutos}

    # Onde o humano já editou a stake, o bloco cru não manda.
    editados = {r["bilhete_id"] for r in await conn.fetch(
        "SELECT DISTINCT bilhete_id FROM correcoes WHERE campo = 'stake'")}

    if aplicar:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(json.dumps(
            {"gravado_em": datetime.now(timezone.utc).isoformat(),
             "linhas": list(por_codigo.values())},
            ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"snapshot ANTES: {DESTINO}\n")

    mudadas = 0
    for codigo, dono, stake_nova, motivo in CORRECOES:
        atual = por_codigo.get((codigo, dono))
        if not atual:
            print(f"!! {codigo} [{dono}]: não encontrado no banco — PULADO")
            continue
        if atual["id"] in editados:
            # Inclui a edição feita por este próprio script: rodar de novo é no-op.
            print(f"!! {codigo} [{dono}]: já há correção de stake registrada — PULADO")
            continue

        bruto = bloco.get((codigo, dono))
        if not bruto:
            print(f"!! {codigo} [{dono}]: sem bloco cru na sombra — PULADO (sem prova)")
            continue
        # Reconferência: o bloco tem de dizer exatamente a stake que vamos gravar.
        no_bloco = _campo(bruto, "Stake")
        if _num(no_bloco) is None or _num(no_bloco) != _num(stake_nova):
            print(f"!! {codigo} [{dono}]: bloco diz {no_bloco!r}, a lista diz "
                  f"{stake_nova!r} — PULADO (não confere)")
            continue

        campos = {"stake": stake_nova}
        odd_nova = _odd_esperada(bruto, atual["resultado"], _num(stake_nova))
        if odd_nova and _num(odd_nova) != _num(atual["odd"]):
            campos["odd"] = odd_nova

        delta = {k: v for k, v in campos.items() if (atual.get(k) or "") != v}
        if not delta:
            print(f"=  {codigo} [{dono}] já está correto")
            continue

        print(f"\n{'→' if aplicar else '·'}  #{atual['id']} {codigo} [{dono}] "
              f"{atual['casa']} · {atual['descricao']}")
        print(f"     motivo: {motivo}")
        for k, v in delta.items():
            print(f"     {k}: {atual.get(k)!r}  →  {v!r}")
        if aplicar:
            ok = await atualizar_bilhete(atual["id"], campos, dono)
            print(f"     gravado: {ok}")
        mudadas += 1

    print(f"\n=== {mudadas} linha(s) {'corrigida(s)' if aplicar else 'a corrigir (ENSAIO)'} ===")

    if aplicar:
        depois = await conn.fetch(
            """SELECT codigo_bilhete, dono, stake, odd, resultado, assinatura,
                      extraction_state, tipster
               FROM bilhetes WHERE codigo_bilhete = ANY($1::text[])
               ORDER BY codigo_bilhete""", codigos)
        print("\n=== CONFERÊNCIA (o que está no banco agora) ===")
        for r in depois:
            a = por_codigo[(r["codigo_bilhete"], r["dono"])]
            sig = "assinatura recalculada" if a["assinatura"] != r["assinatura"] else "assinatura intacta"
            print(f"{r['codigo_bilhete']} [{r['dono']}] stake {r['stake']} · odd {r['odd']} · "
                  f"{r['resultado']} · {r['extraction_state']} · tipster {r['tipster'] or '—'} · {sig}")
    await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main("--aplicar" in sys.argv)))
