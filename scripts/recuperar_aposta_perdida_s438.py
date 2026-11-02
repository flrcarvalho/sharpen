"""Grava pela Ficha uma aposta que a IA leu e que nunca virou linha (s438, Fase 0 da consultoria 022).

Caso: Jaao26, 1win, código 338677290 (R$ 250 @ 2,16, L, evento em 13/10/2026). A IA leu a aposta
em 16/10 às 09:38 (lote de 116 com a conta `Old`, 115 gravadas) e ela não está no banco sob código
nenhum, nem na lixeira. O cru guardado (14/10) é aceito pela Ficha, e o dicionário de hoje traduz
esporte, categoria e descrição.

A linha sai do MESMO caminho da Ficha (`virada.gravar_na_planilha` → `main.gravar_tsv`, origem
`ficha`): dinheiro do cru, conversão de moeda e carimbo de colocação iguais aos da rota. Depois, uma
linha em `correcoes` (`origem='ficha'`, que o `campos_corrigidos` ignora: é robô, não decisão do
dono) diz de onde a aposta veio.

Travas (qualquer uma PARA sem escrever):
  • o código já existe no banco para o dono, em qualquer casa ou conta;
  • não há cru guardado, ou a Ficha o recusa;
  • esporte, categoria ou descrição faltam no dicionário, ou estão fora do Master;
  • a conta não existe no cadastro do dono;
  • o `/salvar` devolve a linha em `rejeitados`.

Script de banco roda SOZINHO: nada de push ou deploy enquanto ele roda (25/10/2026).

    python scripts/recuperar_aposta_perdida_s438.py                 # ensaio (só lê)
    python scripts/recuperar_aposta_perdida_s438.py --aplicar       # grava (só com o "pode" do Feca)
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "scripts"))

from limpar_cru_filtro import _carregar_env  # noqa: E402

DONO, CASA_KEY, CASA, CONTA, CODIGO = "Jaao26", "1WIN", "1win", "1win", "338677290"
MOTIVO = ("s438: aposta lida pela IA em 16/10/2026 (lote da conta Old) e nunca gravada; "
          "recuperada pela Ficha a partir do cru guardado, com o OK do Feca")


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    _carregar_env()
    aplicar = "--aplicar" in sys.argv
    import dicionario
    import ficha
    import virada
    from database import get_pool

    pool = await get_pool()
    async with pool.acquire() as conn:
        ja = await conn.fetch("SELECT id, casa, parceiro FROM bilhetes WHERE dono = $1 AND "
                              "codigo_bilhete = $2", DONO, CODIGO)
        if ja:
            print(f"PARADO: o código já está no banco: {[dict(r) for r in ja]}")
            return
        conta = await conn.fetchval("SELECT nome FROM parceiros WHERE dono = $1 AND casa = $2 "
                                    "AND nome = $3", DONO, CASA, CONTA)
        if not conta:
            print(f"PARADO: a conta {CONTA!r} da {CASA} não existe no cadastro de {DONO}")
            return
        c = await conn.fetchrow("SELECT id, familia, cru::text AS cru, recebido_em FROM captura_crua "
                                "WHERE dono = $1 AND casa = $2 AND codigo = $3 ORDER BY id DESC "
                                "LIMIT 1", DONO, CASA_KEY, CODIGO)
        if not c:
            print("PARADO: não há cru guardado para o código")
            return
        f, motivos = ficha.montar_ficha(c["familia"], json.loads(c["cru"]), CASA_KEY)
        if f is None or motivos:
            print(f"PARADO: a Ficha recusa o cru {c['id']}: {motivos}")
            return
        termos = await dicionario.carregar(conn, CASA_KEY)
    esporte, categoria, faltam = dicionario.traduzir(f, termos)
    desc = virada.descricao(f, termos)
    if faltam or not desc or not virada.no_master(esporte, categoria):
        print(f"PARADO: tradução incompleta: esporte {esporte!r}, categoria {categoria!r}, "
              f"faltam {faltam}, descrição {desc!r}")
        return
    linha = virada.linha_tsv(f, CASA, CONTA, esporte, categoria, desc)
    print(f"cru {c['id']} (recebido {c['recebido_em']}), status {f['status']}, moeda {f.get('moeda')}")
    print("linha a gravar (TSV, colunas do MASTER_OUTPUT):")
    for nome, v in zip(("Data", "Esporte", "Tipster", "Casa", "Conta", "Categoria", "Descrição",
                        "Stake", "Odd", "Resultado", "Código"), linha.split("\t")):
        print(f"  {nome:10s} {v}")
    print(f"rastro em correcoes: campo 'recuperacao', valor_novo {MOTIVO!r}, origem 'ficha'")
    if not aplicar:
        print("ensaio: nada escrito. Rode com --aplicar (só com o \"pode\" do Feca).")
        return

    r = await virada.gravar_na_planilha(DONO, CASA, CONTA, [(f, esporte, categoria, desc)])
    if r.get("rejeitados"):
        print(f"PARADO: o /salvar recusou a linha: {r['rejeitados']}")
        return
    async with pool.acquire() as conn:
        b = await conn.fetchrow("SELECT id, casa, parceiro, data, stake, odd, resultado, descricao, "
                                "origem FROM bilhetes WHERE dono = $1 AND codigo_bilhete = $2",
                                DONO, CODIGO)
        if not b:
            print(f"ERRO: o /salvar respondeu {r} e a linha não está no banco")
            return
        await conn.execute(
            "INSERT INTO correcoes (bilhete_id, dono, casa, campo, valor_anterior, valor_novo, "
            "descricao, origem) VALUES ($1, $2, $3, 'recuperacao', NULL, $4, $5, 'ficha')",
            b["id"], DONO, b["casa"], MOTIVO, b["descricao"])
    print(f"gravado: {dict(b)}")
    pend = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if pend:                                # efeitos do /salvar disparados em segundo plano
        await asyncio.wait(pend, timeout=30)


if __name__ == "__main__":
    asyncio.run(main())
