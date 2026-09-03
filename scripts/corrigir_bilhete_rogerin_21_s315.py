"""Conserta o bilhete #21 do Rogerin (RG202609-21), sessão 315.

O DEFEITO (no bot, já corrigido lá): o `RE_STAKE_G` do perfil `rogerin` exigia
`^` ou `[\\s,;]` antes do número. A legenda veio `2u/1u/0,5u` — a BARRA não estava
na lista, então `1u` e `0,5u` não casavam pelo começo, mas a VÍRGULA de `0,5u`
casava, e a varredura devolveu `[2u, 5u]`. A 2ª aposta foi planilhada com **5u**.
Perder a stake seria erro; TROCAR por outra dez vezes maior é o defeito calado —
o número é plausível, o resultado está certo e nada acusa.

O QUE ESTE SCRIPT FAZ, e por que precisa de script:

1. `RG202609-21-S2` — stake `5` → `1`. O print marca R$1,00 nessa seleção e
   R$2,00 na primeira: a proporção 2:1 é a de `2u/1u`, na ordem do print. P/L
   passa de −5,00u para −1,00u. O UPSERT **congela** stake em linha resolvida
   (`repository.py`, `ON CONFLICT`), então reenviar o bilhete não conserta —
   tem de ser edição, pelo caminho que registra em `correcoes` e recalcula a
   assinatura (`stake` está em `_SIG_COLS`).

2. `RG202609-21-S3` — a 3ª aposta, que nunca chegou à planilha: `Lucas Piton -
   Mais de 2.5` @11,00, 0,5u, **L**. Ela é o 3º valor da legenda e fecha a
   aritmética do print: `Retorno Total R$12,83` = 3,33 (2,00 @1,66) + 4,00
   (1,00 @4,00) + **5,50** (0,50 @11,00). O modal da bet365 rola com o rodapé
   fixo, então o print mostra 2 apostas e soma 3. Resultado L é dedução fechada,
   não chute: "Mais de 1.5" perdeu, logo "Mais de 2.5" perdeu junto.
   O bot não tem comando para ACRESCENTAR aposta a bilhete já publicado — daí a
   escrita aqui, pelo mesmo `upsert_bilhetes` que o `/salvar` usa.

O QUE ELE NÃO FAZ: o post do canal e o registro do bot seguem com 5u na 2ª e sem
a 3ª. Para o canal, alguém com acesso ao apoio digita `/atualizastake #21 2 1` —
o bot risca a stake antiga no post e reenvia. A 3ª aposta não tem esse caminho.

Idempotente: confere o valor de ANTES e pula o que já estiver certo.
Leitura pura com `--ensaio` (padrão). Escreve só com `--aplicar`.
"""
import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))  # o app importa por nome curto (`from database …`)

# O console do Windows abre em cp1252 e engasga nos acentos do relatório.
sys.stdout.reconfigure(encoding="utf-8")

if "DATABASE_URL" not in os.environ:
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        if linha.startswith("DATABASE_URL="):
            os.environ["DATABASE_URL"] = linha.split("=", 1)[1].strip().strip('"').strip("'")

import repository  # noqa: E402

DONO = "Rogeringambler"
TIPSTER = "RogerinComeuMeuSaldo"
CASA = "Bet365"
PARCEIRO = "Padrão"

# A 2ª aposta: o que estava lá e o que entra. O `de` é conferido em execução —
# se o banco não disser 5, alguém já mexeu e o script não escreve por cima.
S2 = {"codigo": "RG202609-21-S2", "de": "5", "para": "1"}

# A 3ª aposta, na forma exata que o bot manda ao /salvar: 11 colunas, TAB real,
# decimal vírgula, tipster vazio (ele entra depois, por `set_tipster_bulk`, que é
# como a rota `/bilhetes/tipster` grava).
S3_TSV = "\t".join([
    "02/09/2026",                                        # Data (do evento)
    "Futebol",                                           # Esporte
    "",                                                  # Tipster — vai depois
    CASA,                                                # Casa
    PARCEIRO,                                            # Parceiro
    "Chutes",                                            # Aposta (MASTER_APOSTAS §3)
    "#21 Lucas Piton - Mais de 2.5 [Vitória v Vasco da Gama]",  # Descrição
    "0,5",                                               # Stake (unidades)
    "11",                                                # Odd
    "L",                                                 # Resultado
    "RG202609-21-S3",                                    # Código (11ª, interna)
])

# `criado_em` ancora a ORDEM do feed. S1 e S2 nasceram em 22:16:18(+1µs); a 3ª
# entra logo depois delas, no mesmo bilhete, e não no topo da lista de hoje.
CRIADO_BASE = datetime(2026, 9, 2, 22, 16, 18, 2, tzinfo=timezone.utc)


async def linhas_do_bilhete(conn):
    return await conn.fetch(
        """SELECT id, codigo_bilhete, descricao, stake, odd, resultado, tipster,
                  extraction_state, criado_em
             FROM bilhetes
            WHERE dono = $1 AND codigo_bilhete LIKE 'RG202609-21%'
            ORDER BY codigo_bilhete""",
        DONO,
    )


def mostrar(rows, titulo):
    print(f"\n── {titulo} ──")
    for r in rows:
        pl = repository.calcular_pl(r["stake"], r["odd"], r["resultado"])
        print(f'  {r["codigo_bilhete"]:<18} stake={r["stake"]:<5} odd={r["odd"]:<6} '
              f'{r["resultado"] or "—":<2} P/L={pl if pl is None else round(pl, 2):<7} '
              f'{r["descricao"]}')


async def main(aplicar: bool):
    pool = await repository.get_pool()
    async with pool.acquire() as conn:
        antes = await linhas_do_bilhete(conn)
        mostrar(antes, "ANTES")
        por_codigo = {r["codigo_bilhete"]: r for r in antes}

    # ── 1. a stake da 2ª ──────────────────────────────────────────────────────
    alvo = por_codigo.get(S2["codigo"])
    if not alvo:
        print(f'\n⚠️  {S2["codigo"]} não existe — nada a corrigir.')
    elif alvo["stake"] == S2["para"]:
        print(f'\n👌 {S2["codigo"]} já está em {S2["para"]}u.')
    elif alvo["stake"] != S2["de"]:
        print(f'\n⚠️  {S2["codigo"]} está em {alvo["stake"]!r}, e não {S2["de"]!r} — '
              "alguém já mexeu. NÃO escrevo por cima.")
    elif aplicar:
        ok = await repository.atualizar_bilhete(alvo["id"], {"stake": S2["para"]}, DONO)
        print(f'\n✔ {S2["codigo"]}: stake {S2["de"]}u → {S2["para"]}u ({ok})')
    else:
        print(f'\n[ensaio] {S2["codigo"]}: stake {S2["de"]}u → {S2["para"]}u')

    # ── 2. a 3ª aposta ────────────────────────────────────────────────────────
    if "RG202609-21-S3" in por_codigo:
        print("👌 RG202609-21-S3 já está na planilha.")
    elif aplicar:
        rows = repository.parse_tsv(S3_TSV)
        validas, rejeitadas = repository.validar_linhas(rows)
        if rejeitadas or len(validas) != 1:
            print(f"⚠️  linha rejeitada pela validação: {rejeitadas}")
            return
        ins, atu, ids, alertas, _dups = await repository.upsert_bilhetes(
            validas, DONO, origem="extracao", criado_base=CRIADO_BASE)
        print(f"✔ RG202609-21-S3: {ins} nova(s), {atu} atualizada(s), ids={ids}")
        for a in alertas:
            print(f"   alerta: {a}")
        if ids:
            n = await repository.set_tipster_bulk(ids, TIPSTER, DONO)
            print(f"✔ tipster {TIPSTER} em {n} linha(s)")
    else:
        rows = repository.parse_tsv(S3_TSV)
        validas, rejeitadas = repository.validar_linhas(rows)
        print(f"[ensaio] RG202609-21-S3 entraria: {validas} (rejeitadas: {rejeitadas})")

    async with pool.acquire() as conn:
        depois = await linhas_do_bilhete(conn)
    mostrar(depois, "DEPOIS" if aplicar else "DEPOIS (sem escrita — ensaio)")
    total = sum(
        (repository.calcular_pl(r["stake"], r["odd"], r["resultado"]) or 0) for r in depois)
    print(f"\nP/L do bilhete #21: {round(total, 2)}u")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--aplicar", action="store_true", help="escreve (o padrão é ensaio)")
    args = p.parse_args()
    if not os.environ.get("DATABASE_URL"):
        sys.exit("DATABASE_URL ausente — confira o .env do Planilhador.")
    asyncio.run(main(args.aplicar))
