"""Poda uma conta para a lista de códigos que a CASA mostra — apaga o que sobra.

Irmão de `mover_bilhetes_entre_contas.py`, para o caso em que não há destino: os
bilhetes intrusos não pertencem a nenhuma outra conta do sistema (nenhum outro
`parceiro` tem esses códigos), então mover não é opção — ou saem, ou ficam
mentindo no P/L.

O caso que o originou (s267): a conta Betano `elianemaria12233 [Annderson]` tinha
534 bilhetes no banco e 321 no extrato da casa. O P/L do banco dizia −R$7.412 numa
conta que recebeu R$4.000 de depósito e ainda tem ~R$2.000 — impossível por
aritmética, não por opinião. O P/L dos 321 do extrato dá −R$2.419, que cabe no
depósito. Os 213 restantes eram de outra origem (provavelmente uma captura
disparada com outra conta selecionada, cujo dono nunca foi identificado).

A LISTA DA CASA É A VERDADE, e ela é a única fonte que sobrou: o banco não sabe
distinguir um bilhete legítimo antigo de um intruso, porque intruso não vem
marcado. Quem sabe é o extrato da conta na casa.

POR QUE NÃO É `excluir_parceiro`: aquele apaga a conta INTEIRA e a linha em
`parceiros`. Aqui a conta é viva e continua existindo — sai só o recorte.

POR QUE O SNAPSHOT SAI DO PRÓPRIO DELETE (`DELETE ... RETURNING to_jsonb`): ler
antes e apagar depois abre janela para gravar uma lixeira que não corresponde ao
que saiu (regra do CLAUDE.md, "Excluir dado"). O snapshot vai para DOIS lugares,
de propósito:
  · `lixeira_contas`, sob um nome de parceiro MARCADO — é o caminho que o resto do
    sistema já conhece, mas tem retenção de 7 dias (`LIXEIRA_DIAS`);
  · um arquivo `.json` em `Backups/`, que não expira. Bilhete de mês passado não
    volta pela casa (o extrato não vai tão longe): se o arquivo sumir, o dado
    sumiu junto.

POR QUE RE-ARQUIVAR NO FIM: `auto_arquivar` mantém visíveis as 40 linhas mais
recentes por conta (`criado_em DESC`). Tirar linhas do topo sem recomputar deixa a
grade com buracos — conserto que vira susto.

Uso (dry-run por padrão — nada é escrito sem `--aplicar`):

    python scripts/podar_conta_para_lista.py \
        --dono Feca --casa Betano --parceiro "elianemaria12233 [Annderson]" \
        --lista caminho/para/codigos.txt

    ... o mesmo comando com --aplicar no fim executa.

`--manter-abertas` preserva as linhas sem resultado (aposta ainda não liquidada)
mesmo que não estejam na lista: extrato de "apostas resolvidas" não as mostra, e
apagá-las por ausência seria confundir "não listado" com "não existe".
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

import asyncpg
from dotenv import load_dotenv

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_RAIZ, ".env"))
# `app/repository.py` importa os vizinhos de forma flat (`from database import ...`),
# então quem entra no path é a pasta `app/`, não a raiz.
sys.path.insert(0, os.path.join(_RAIZ, "app"))

from repository import auto_arquivar  # noqa: E402

# O console do Windows abre em cp1252 e derruba o script no primeiro caractere fora
# da tabela — erro de encoding disfarçado de erro de operação é o pior tipo.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _num(v) -> float:
    """'1.234,56' → 1234.56. Stake e odd são TEXTO no banco, em formato BR."""
    if v is None:
        return 0.0
    s = str(v).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _pl(linhas) -> tuple[float, float]:
    """(P/L, turnover) pela mesma regra do app: W/L/HW/HL contam, aberta não."""
    pl = turn = 0.0
    for r in linhas:
        stake, odd = _num(r["stake"]), _num(r["odd"])
        res = (r["resultado"] or "").strip().upper()
        turn += stake
        if res == "W":
            pl += stake * odd - stake
        elif res == "L":
            pl -= stake
        elif res == "HW":
            pl += (stake * odd - stake) / 2
        elif res == "HL":
            pl -= stake / 2
    return pl, turn


async def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dono", required=True)
    p.add_argument("--casa", required=True)
    p.add_argument("--parceiro", required=True, help="nome exato da conta em `parceiros`")
    p.add_argument("--lista", required=True,
                   help="arquivo texto com um código de bilhete por linha (a verdade da casa)")
    p.add_argument("--manter-abertas", action="store_true",
                   help="preserva linhas sem resultado que não estejam na lista")
    p.add_argument("--aplicar", action="store_true", help="sem isto, só mostra")
    a = p.parse_args()

    with open(a.lista, encoding="utf-8") as fh:
        codigos = [ln.strip() for ln in fh if ln.strip()]
    lista = set(codigos)
    if len(lista) != len(codigos):
        print(f"AVISO: a lista tem {len(codigos)} linhas e {len(lista)} códigos distintos.")

    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    con = await asyncpg.connect(url)
    try:
        rows = await con.fetch(
            "SELECT id, codigo_bilhete, data, stake, odd, resultado, esporte, descricao,"
            " criado_em FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3"
            " ORDER BY criado_em, id",
            a.dono, a.casa, a.parceiro,
        )
        if not rows:
            print("Nenhum bilhete nessa conta. Confira dono/casa/parceiro — o nome é exato.")
            return 1

        no_banco = {r["codigo_bilhete"] for r in rows if r["codigo_bilhete"]}
        ausentes = sorted(lista - no_banco)

        fica, sai = [], []
        for r in rows:
            cod = r["codigo_bilhete"] or ""
            aberta = not (r["resultado"] or "").strip()
            if cod in lista or (a.manter_abertas and aberta):
                fica.append(r)
            else:
                sai.append(r)

        print(f"conta   : {a.dono} / {a.casa} / {a.parceiro}")
        print(f"banco   : {len(rows)} bilhetes")
        print(f"lista   : {len(lista)} códigos (a casa)")
        # Código da lista que não está no banco é o sinal de que a lista está errada
        # ou incompleta — some ANTES de apagar qualquer coisa por ausência.
        print(f"ausentes: {len(ausentes)} códigos da lista que NÃO estão no banco"
              + (" ← confira a lista antes de aplicar" if ausentes else ""))
        for c in ausentes[:20]:
            print(f"          {c}")
        print(f"fica    : {len(fica)}")
        print(f"sai     : {len(sai)}")

        pl_f, tu_f = _pl(fica)
        pl_s, tu_s = _pl(sai)
        pl_t, tu_t = _pl(rows)
        print(f"\nP/L hoje      : {pl_t:>12,.2f}   turnover {tu_t:>12,.2f}")
        print(f"P/L do que sai: {pl_s:>12,.2f}   turnover {tu_s:>12,.2f}")
        print(f"P/L depois    : {pl_f:>12,.2f}   turnover {tu_f:>12,.2f}")

        if sai:
            print("\namostra do que sai (10 primeiros):")
            for r in sai[:10]:
                print(f"  id={r['id']} cod={r['codigo_bilhete']} {r['data']} "
                      f"stake={r['stake']} odd={r['odd']} res={r['resultado']!r} "
                      f"| {(r['descricao'] or '')[:70]}")

        if not a.aplicar:
            print("\n[DRY-RUN] nada foi escrito. Repita com --aplicar para executar.")
            return 0
        if not sai:
            print("\nNada a fazer.")
            return 0

        ids = [r["id"] for r in sai]
        async with con.transaction():
            snap = await con.fetch(
                "DELETE FROM bilhetes b WHERE b.id = ANY($1::int[])"
                " RETURNING to_jsonb(b.*) AS linha",
                ids,
            )
            linhas = [r["linha"] for r in snap]
            # Nome MARCADO: a lixeira é indexada por conta, e uma entrada com o nome
            # limpo se confundiria com a exclusão da conta inteira numa restauração.
            marcado = f"{a.parceiro} — poda {datetime.now():%Y-%m-%d}"
            # asyncpg devolve jsonb como str (sem codec global registrado); o array
            # inteiro entra como texto + cast ::jsonb — mesmo padrão do repository.
            await con.execute(
                "INSERT INTO lixeira_contas (dono, casa, parceiro, arquivado, n_bilhetes,"
                " bilhetes) VALUES ($1, $2, $3, FALSE, $4, $5::jsonb)",
                a.dono, a.casa, marcado, len(linhas), "[" + ",".join(linhas) + "]",
            )

        destino = os.path.join(_RAIZ, "Backups",
                               f"poda-{a.casa}-{datetime.now():%Y-%m-%d}")
        os.makedirs(destino, exist_ok=True)
        arq = os.path.join(destino, f"{a.parceiro.replace('/', '-')}.json")
        with open(arq, "w", encoding="utf-8") as fh:
            json.dump([json.loads(x) for x in linhas], fh, ensure_ascii=False, indent=1)

        n_arq = await auto_arquivar(a.casa, a.parceiro, 40, a.dono)
        restam = await con.fetchval(
            "SELECT COUNT(*) FROM bilhetes WHERE dono = $1 AND casa = $2 AND parceiro = $3",
            a.dono, a.casa, a.parceiro,
        )
        print(f"\nAPLICADO: {len(linhas)} bilhetes removidos, {restam} restam na conta.")
        print(f"  snapshot em lixeira_contas: \"{marcado}\"")
        print(f"  snapshot em arquivo       : {arq}")
        print(f"  re-arquivamento           : {n_arq} linhas ajustadas")
        if restam != len(fica):
            print(f"  ATENÇÃO: esperava {len(fica)} e restaram {restam}.")
            return 1
        return 0
    finally:
        await con.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
