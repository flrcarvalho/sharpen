"""Corrige as descrições que a IA escreveu a partir do bilhete ERRADO (sessão 302).

Cada linha desta lista foi conferida **uma a uma contra o bloco cru do robô**
(`sombra_rotulos.bruto`), que é a fonte de verdade — o robô acertou em todos os casos;
o que errou foi a tradução. Quatro famílias:

  A) carryover  — a descrição pertence a outro bilhete (o vizinho no mesmo chunk).
                  Betfair 1941, Betfast 301490938/301491163, Betnacional (as duas
                  trocaram entre si).
  B) número inventado — `Vai até o Final? · Não` virou `Under 1.5 Rounds`; `5+ chutes`
                  virou `Over 5.5` (que é ≥6, não ≥5 — muda a aposta).
  C) período perdido  — `3º Set` / `1º Quarto` sumiram e a aposta ficou indistinguível
                  da mesma aposta no jogo inteiro. Corrigido pela regra nova
                  (`MASTER_DESCRICAO §12.10`).
  D) separador decimal — `3,5` onde a casa e o golden set mandam `3.5`.

POR QUE ISTO PRECISA DE SCRIPT: o UPSERT congela `esporte`/`aposta`/`descricao` fora de
`origem='sync'` (`repository.py`, `ON CONFLICT`). Recapturar a casa NÃO conserta estas
linhas — nem as que ainda estão `aberta`. Sem esta correção elas ficam erradas para
sempre.

Escreve pelo caminho sancionado (`repository.atualizar_bilhete`), que registra a
correção em `correcoes` e recalcula a assinatura se o hash for tocado. Grava o snapshot
ANTES em JSON, ao lado do backup da sessão.

Uso:
    python scripts/corrigir_descricoes_infieis_s302.py            # ensaio (não escreve)
    python scripts/corrigir_descricoes_infieis_s302.py --aplicar
"""
import asyncio
import json
import os
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

DESTINO = ROOT / "Backups" / "s302-fidelidade-descricao" / "bilhetes_antes.json"

# (código, dono, campos novos, motivo)
CORRECOES = [
    # ── A) carryover: descrição de OUTRO bilhete ──────────────────────────────
    ("O/25146258/0001941", "Feca", {
        "esporte": "Futebol", "aposta": "Cartões",
        "descricao": "Over 3.5 Cartões [Norwich v Burnley]",
    }, "carryover: saiu a seleção do 1943/1944 (Matthew Dennant), Dardos/ML"),

    # `esporte = Múltiplos` FICA: são 3 confrontos distintos, e o MASTER_ESPORTES §2.2
    # manda `Múltiplos` em acumulada de 3+ jogos diferentes ainda que do mesmo esporte.
    # A ordem é `Entidade - Linha Mercado` (MASTER_DESCRICAO §12.3), e "time de fora" /
    # "time de casa" do rótulo resolvem QUAL time do confronto entra.
    ("301490938", "Gabriel", {
        "descricao": ("Middlesbrough FC - Under 1.5 Impedimentos "
                      "[Blackburn Rovers FC v Middlesbrough FC] // "
                      "Inter Miami - Under 17.5 Finalizações [Inter Miami v Toronto FC] // "
                      "Atletico Mineiro MG - Over 2.5 Impedimentos "
                      "[Internacional RS v Atletico Mineiro MG]"),
    }, "carryover: descrição inteira de outro bilhete (Charlotte/Cruzeiro/Gold Coast)"),

    ("301491163", "Gabriel", {
        "descricao": ("Middlesbrough FC - Under 1.5 Impedimentos "
                      "[Blackburn Rovers FC v Middlesbrough FC] // "
                      "Inter Miami - Under 17.5 Finalizações [Inter Miami v Toronto FC] // "
                      "Atletico Mineiro MG - Over 2.5 Impedimentos "
                      "[Internacional RS v Atletico Mineiro MG]"),
    }, "carryover: mesma descrição fabricada do 301490938"),

    # As duas Betnacional trocaram de descrição ENTRE SI. A leitura correta de cada uma
    # existe na sombra — é a que a IA produziu para a outra.
    ("NXBNAC000156350861787914945174", "Gabriel", {
        "descricao": ("Virginia USC -1 [Virginia USC v Club Universitario Beni] // "
                      "1X [KSS Kotwica Kornik v Chemik Bydgoszcz] // "
                      "Over 3.5 Gols [KS Polonia Sroda Wlkp v Gedania Gdansk]"),
    }, "troca: estava com a descrição do …852005"),

    ("NXBNAC000156350861787922852005", "Gabriel", {
        "descricao": ("Over 10.5 Escanteios [Al-Khaleej v Al-Hilal] // "
                      "Over 2.5 Gols [Cremonese v Modena] // "
                      "Over 3.5 Gols [Tabor Sezana v Brezice]"),
    }, "troca: estava com a descrição do …945174"),

    # ── B) número inventado ───────────────────────────────────────────────────
    ("O/25146258/0001938", "Feca", {
        "descricao": ("Hector Santiago [Lawrence Lui v Hector Santiago] // "
                      "Não Vai até o Final [Lawrence Lui v Hector Santiago]"),
    }, "inventado: `Vai até o Final? · Não` virou `Under 1.5 Rounds` (o 1.5 é do 1936)"),

    ("O/25146258/0001895", "Feca", {
        "descricao": "Corinthians - 5+ Chutes no Gol e Classificação [Corinthians v Rosario]",
    }, "inventado: `5+` (≥5) virou `Over 5.5` (≥6) — MASTER_DESCRICAO §10.2 manda `X+`"),

    # ── C) período perdido (MASTER_DESCRICAO §12.10, criado nesta sessão) ─────
    ("O/25146258/0001915", "Feca", {
        "descricao": "Suécia 3º Set [Suécia v Croácia]",
    }, "período: `Vence o 3º Set` estava indistinguível de um ML de partida"),

    ("O/25146258/0001921", "Feca", {
        "descricao": ("Under 39.5 Pontos 3º Set "
                      "[Trinidad & Tobago Women v Costa Rica Women]"),
    }, "período: `Total de Pontos no 3º Set` estava igual ao total do jogo"),

    ("O/25146258/0001913", "Feca", {
        "descricao": ("Megan DiLeo - Under 1.5 Triplos [Portland Fire v Dallas Wings] // "
                      "Over 40.5 Pontos 1º Quarto "
                      "[Washington Mystics v Phoenix Mercury]"),
    }, "período: `Total de pontos no 1º quarto` estava igual ao total do jogo"),

    # ── D) separador decimal + nome de time ───────────────────────────────────
    ("O/25146258/0001942", "Feca", {
        "descricao": "Over 3.5 Cartões [Bristol City v Portsmouth]",
    }, "decimal: saiu `3,5` enquanto os 5 bilhetes idênticos saíram `3.5`"),

    ("O/25146258/0001886", "Feca", {
        "descricao": ("Chicago Fire [Orlando City v Chicago Fire] // "
                      "Al-Hilal -2.5 Gols [Al-Fayha v Al-Hilal]"),
    }, "nome: a casa escreve `Al-Fayha`, saiu `Al-Feiha`; e `-2,5` vira `-2.5`"),
]


async def main(aplicar: bool) -> int:
    conn = await asyncpg.connect(dsn())
    codigos = [c for c, _d, _f, _m in CORRECOES]
    antes = await conn.fetch(
        """SELECT id, dono, casa, parceiro, codigo_bilhete, esporte, aposta, descricao,
                  extraction_state, resultado, assinatura
           FROM bilhetes WHERE codigo_bilhete = ANY($1::text[])""", codigos)
    por_codigo = {r["codigo_bilhete"]: dict(r) for r in antes}

    faltando = [c for c in codigos if c not in por_codigo]
    if faltando:
        print(f"!! não encontrados no banco: {faltando}")

    if aplicar:
        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(json.dumps(
            {"gravado_em": datetime.now(timezone.utc).isoformat(),
             "linhas": list(por_codigo.values())},
            ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"snapshot ANTES: {DESTINO}\n")

    mudadas = 0
    for codigo, dono, campos, motivo in CORRECOES:
        atual = por_codigo.get(codigo)
        if not atual:
            continue
        if atual["dono"] != dono:
            print(f"!! {codigo}: dono no banco é '{atual['dono']}', esperado '{dono}' — PULADO")
            continue
        delta = {k: v for k, v in campos.items() if (atual.get(k) or "") != v}
        if not delta:
            print(f"=  {codigo} [{dono}] já está correto")
            continue
        print(f"\n{'→' if aplicar else '·'}  #{atual['id']} {codigo} [{dono}] — {motivo}")
        for k, v in delta.items():
            print(f"     {k}: {atual.get(k)!r}")
            print(f"     {' ' * len(k)}  →  {v!r}")
        if aplicar:
            ok = await atualizar_bilhete(atual["id"], campos, dono)
            print(f"     gravado: {ok}")
        mudadas += 1

    print(f"\n=== {mudadas} linha(s) {'corrigida(s)' if aplicar else 'a corrigir (ENSAIO)'} ===")

    if aplicar:
        depois = await conn.fetch(
            """SELECT codigo_bilhete, esporte, aposta, descricao, assinatura, extraction_state
               FROM bilhetes WHERE codigo_bilhete = ANY($1::text[])
               ORDER BY codigo_bilhete""", codigos)
        print("\n=== CONFERÊNCIA (o que está no banco agora) ===")
        for r in depois:
            a = por_codigo[r["codigo_bilhete"]]
            sig = "assinatura recalculada" if a["assinatura"] != r["assinatura"] else "assinatura intacta"
            print(f"{r['codigo_bilhete']}  [{r['esporte']} | {r['aposta']} | {r['extraction_state']}] · {sig}")
            print(f"   {r['descricao']}")
    await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main("--aplicar" in sys.argv)))
