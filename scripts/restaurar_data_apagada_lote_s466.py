"""Devolve a `data` que a edição em massa apagou (s466, 24/11/2026).

Por quê: o modal "Editar em massa" (tela de Extração) trata "tique ligado com o campo vazio"
como LIMPAR, e o tique da Data liga sem querer (clique no rótulo, digitar e apagar, "Limpar"
do calendário). A `/bilhetes/lote` aceitou `data: ""` e gravou. Aposta sem data some de toda
tela com período, e recapturar não devolve: a linha está resolvida (o UPSERT congela `data`) e
a edição ficou em `correcoes` como correção humana.

Só houve dois eventos assim no histórico inteiro (medido em 24/11/2026, `correcoes` com
`campo='data'` e `valor_novo` vazio):
  • jonathan: Jonathan · Stake.com · 100 linhas · 24/11/2026 10:00:53-54 UTC;
  • jaao26:   Jaao26 · Pinnacle · 7 linhas · 28/09/2026 06:28 UTC.

A data certa é o `valor_anterior` da própria `correcoes`, copiado verbatim (sem inferir nada).
Antes de escrever, confere linha a linha; QUALQUER divergência no lote e nada é escrito:
  • o lote tem exatamente o número esperado de edições, uma por bilhete;
  • o `valor_anterior` é uma data legível (DD/MM/AAAA ou ISO);
  • o bilhete existe, é do dono e continua com a `data` vazia;
  • nenhuma edição de `data` posterior ao evento (se alguém já mexeu, a mão dele manda).

A assinatura é conferida pela função REAL (`repository._assinatura_pos_edicao`) numa conexão
SÓ-LEITURA, e o ensaio diz se ela muda e se colide com outra linha da conta. A escrita passa
por `atualizar_bilhete` (recalcula a assinatura e grava em `correcoes` com `script_s466`).

    python scripts/restaurar_data_apagada_lote_s466.py --lote jonathan            # ensaio
    python scripts/restaurar_data_apagada_lote_s466.py --lote jonathan --aplicar
    python scripts/restaurar_data_apagada_lote_s466.py --lote jaao26              # ensaio

O ensaio não escreve por construção: conexão com `default_transaction_read_only=on`.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from datetime import datetime, timezone  # noqa: E402

import asyncpg  # noqa: E402

from repository import _assinatura, _assinatura_pos_edicao, atualizar_bilhete  # noqa: E402

# lote → (dono, casa, início da janela UTC, fim da janela UTC, edições esperadas)
# A janela vai como `datetime` com fuso: o asyncpg não converte string em timestamptz.
_UTC = timezone.utc
LOTES = {
    "jonathan": ("Jonathan", "Stake.com", datetime(2026, 11, 24, 10, 0, 53, tzinfo=_UTC),
                 datetime(2026, 11, 24, 10, 0, 55, tzinfo=_UTC), 100),
    "jaao26": ("Jaao26", "Pinnacle", datetime(2026, 9, 28, 6, 28, tzinfo=_UTC),
               datetime(2026, 9, 28, 6, 29, tzinfo=_UTC), 7),
}
RASTRO = "script_s466"
_DATA_RE = re.compile(r"^(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})$")


def _carregar_env() -> None:
    if "DATABASE_URL" not in os.environ:
        for linha in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if linha.startswith("DATABASE_URL="):
                os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")


async def _planejar(conn, lote: str) -> tuple[list[dict], list[str]]:
    dono, casa, ini, fim, esperado = LOTES[lote]
    eds = await conn.fetch(
        "SELECT id, bilhete_id, valor_anterior, criado_em FROM correcoes "
        "WHERE dono = $1 AND casa = $2 AND campo = 'data' AND COALESCE(valor_novo, '') = '' "
        "AND criado_em >= $3 AND criado_em < $4 ORDER BY criado_em",
        dono, casa, ini, fim)
    erros: list[str] = []
    if len(eds) != esperado:
        erros.append(f"lote com {len(eds)} edições (esperava {esperado})")
    if len({e["bilhete_id"] for e in eds}) != len(eds):
        erros.append("há bilhete com mais de uma edição no lote")
    plano: list[dict] = []
    for e in eds:
        bid, anterior = e["bilhete_id"], (e["valor_anterior"] or "").strip()
        antes = await conn.fetchrow("SELECT * FROM bilhetes WHERE id = $1 AND dono = $2", bid, dono)
        if antes is None:
            erros.append(f"id {bid}: bilhete não existe mais para {dono}")
            continue
        if not _DATA_RE.match(anterior):
            erros.append(f"id {bid}: valor_anterior ilegível {anterior!r}")
            continue
        if (antes["data"] or "").strip():
            erros.append(f"id {bid}: a data já está preenchida ({antes['data']!r})")
            continue
        depois = await conn.fetchval(
            "SELECT count(*) FROM correcoes WHERE bilhete_id = $1 AND campo = 'data' "
            "AND criado_em > $2", bid, e["criado_em"])
        if depois:
            erros.append(f"id {bid}: {depois} edição(ões) de data depois do evento")
            continue
        # Assinatura: o que a edição gravaria (função real) e, para o relatório, se o hash
        # com a data devolvida bate com OUTRA linha da conta.
        nova = await _assinatura_pos_edicao(conn, antes, {"data": anterior}, dono, bid)
        final = {c: (antes[c] or "") for c in ("casa", "parceiro", "data", "aposta",
                                                 "descricao", "stake", "odd")}
        final["data"] = anterior
        final["codigo_bilhete"] = antes["codigo_bilhete"] or ""
        sig1 = _assinatura(final)
        outro = await conn.fetchval(
            "SELECT id FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3 "
            "AND assinatura = $4 AND id <> $5 LIMIT 1",
            dono, antes["casa"], antes["parceiro"], sig1, bid)
        mesmo_codigo = 0
        if final["codigo_bilhete"].strip():
            mesmo_codigo = await conn.fetchval(
                "SELECT count(*) FROM bilhetes WHERE dono = $1 AND casa = $2 "
                "AND codigo_bilhete = $3 AND id <> $4", dono, antes["casa"],
                antes["codigo_bilhete"], bid)
        if sig1 == antes["assinatura"]:
            sig_txt = "inalterada"
        elif nova:
            sig_txt = f"nova {nova}"
        else:
            sig_txt = "mantida (colisão)"
        plano.append({
            "id": bid, "dono": dono, "codigo": antes["codigo_bilhete"] or "",
            "parceiro": antes["parceiro"], "resultado": antes["resultado"] or "",
            "agora": antes["data"] or "", "restaura": anterior, "sig": sig_txt,
            "colide_com": outro, "mesmo_codigo": mesmo_codigo,
            "descricao": (antes["descricao"] or "")[:60],
        })
    return plano, erros


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", required=True, choices=sorted(LOTES))
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()
    _carregar_env()
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], timeout=30,
                                 server_settings={"default_transaction_read_only": "on"})
    try:
        plano, erros = await _planejar(conn, args.lote)
    finally:
        await conn.close()

    print("id\tcodigo\tparceiro\tres\tdata_agora\tdata_restaurada\tassinatura\tcolide_com\t"
          "outra_linha_mesmo_codigo\tdescricao")
    for p in plano:
        print(f"{p['id']}\t{p['codigo']}\t{p['parceiro']}\t{p['resultado']}\t"
              f"{p['agora'] or '(vazia)'}\t{p['restaura']}\t{p['sig']}\t{p['colide_com'] or '-'}\t"
              f"{p['mesmo_codigo']}\t{p['descricao']}")
    colisoes = [p for p in plano if p["colide_com"]]
    duplos = [p for p in plano if p["mesmo_codigo"]]
    print(f"\nlote {args.lote}: {len(plano)} a restaurar · assinatura muda em "
          f"{sum(p['sig'] != 'inalterada' for p in plano)} · colide com outra linha em "
          f"{len(colisoes)} · código repetido noutra linha em {len(duplos)}")
    if erros:
        print("NADA ESCRITO:\n  " + "\n  ".join(erros))
        return
    if colisoes:
        print("NADA ESCRITO: há colisão de assinatura; precisa de olho humano.")
        return
    if not args.aplicar:
        print("ENSAIO: nada escrito (use --aplicar).")
        return
    falhas = 0
    for p in plano:
        ok = await atualizar_bilhete(p["id"], {"data": p["restaura"]}, p["dono"], rastro=RASTRO)
        if not ok:
            falhas += 1
            print(f"id {p['id']}: atualizar_bilhete RECUSOU")
    print(f"gravadas {len(plano) - falhas} de {len(plano)}")


if __name__ == "__main__":
    asyncio.run(main())
