# -*- coding: utf-8 -*-
"""Unifica as grafias de TIPSTER do Diogo — no export do SharkTrack e no banco.

Contexto (s355): a base viva do Diogo tem 891 bilhetes capturados pelo SharpenUp
com o tipster em minúsculo (`milton`, `só chutes`), e o export do SharkTrack que
vai ser importado traz as mesmas pessoas em duas caixas (`peixe` / `Peixe`).
Sem unificar, o dashboard passa a mostrar o mesmo tipster duas vezes.

Decisão do Feca (s355): **Title Case em tudo**, inclusive renomeando o que já
está no banco. `tipster` NÃO entra na assinatura de dedup (`ID|casa|parceiro|
codigo`), então o rename não duplica nem sequestra bilhete nenhum.

O que este script faz, nesta ordem:

1. Lê TODAS as grafias das duas fontes (xlsx + banco) e monta o de-para com
   `tipster_nomes.construir_mapa` — o universo unido é obrigatório, senão o
   import e o rename escolhem vencedores diferentes para o mesmo grupo.
2. Grava o mapa em `scripts/tipsters_diogo_map.json`, que é o que o
   `import_diogo_sharktrack_xlsx.py` consome. **É aqui que entra um merge
   semântico** (`pei` → `Peixe`), se o Feca pedir: edita-se o JSON e roda-se de
   novo com `--usar-mapa`.
3. Com `--go`, renomeia no banco, numa transação só, os TRÊS lugares onde o nome
   do tipster vive para este dono:
     - `bilhetes.tipster`
     - `tipsters.nome` (os perfis que o matcher usa)
     - as CHAVES de `custo_store.custo_tipster` e `custo_tipster_meta`
   O terceiro é o que se esquece: o custo é guardado por NOME, e chave que fica
   para trás vira valor cobrado que ninguém consegue editar (CLAUDE.md, "o
   tipster cobrado e ineditável").

⚠️ Colisão de nome no rename é ESPERADA e desejada: `peixe` e `Peixe` viram
`Peixe`. Nos perfis (`tipsters`, que tem UNIQUE por dono+nome) isso significa
FUNDIR — o script recusa fundir perfis automaticamente e lista o caso, porque
escolher qual perfil sobrevive é decisão de quem conhece os dois.

Uso:
    python scripts/normalizar_tipsters_diogo.py --xlsx "C:\\...\\apostas.xlsx"
    python scripts/normalizar_tipsters_diogo.py --xlsx "..." --go
    python scripts/normalizar_tipsters_diogo.py --xlsx "..." --usar-mapa --go
"""
import argparse
import asyncio
import json
import os
import sys
from collections import Counter

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tipster_nomes as tn  # noqa: E402

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
DONO = 'Diogo'
COL_TIPSTER = 11          # 12ª coluna do export SharkTrack


def carregar_env():
    for line in open(ENV_PATH, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def grafias_do_xlsx(caminho: str) -> Counter:
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    c = Counter()
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or not any(x is not None for x in row):
            continue
        nome = tn.limpar(row[COL_TIPSTER])
        if nome:
            c[nome] += 1
    return c


async def grafias_do_banco(conn) -> tuple[Counter, Counter, dict]:
    bil = Counter()
    for r in await conn.fetch(
            "SELECT tipster, COUNT(*) n FROM bilhetes WHERE dono=$1 "
            "AND tipster IS NOT NULL AND tipster <> '' GROUP BY 1", DONO):
        bil[tn.limpar(r['tipster'])] += r['n']

    perfis = Counter()
    for r in await conn.fetch("SELECT nome FROM tipsters WHERE dono=$1", DONO):
        perfis[tn.limpar(r['nome'])] += 1

    custo = {}
    row = await conn.fetchrow(
        "SELECT custo_tipster, custo_tipster_meta FROM custo_store WHERE dono=$1", DONO)
    if row:
        for campo in ('custo_tipster', 'custo_tipster_meta'):
            v = row[campo]
            if isinstance(v, str):
                v = json.loads(v or '{}')
            custo[campo] = v or {}
    return bil, perfis, custo


def _fundir(dst: dict, src: dict) -> dict:
    """Funde dois dicionários de custo. Valor lançado NUNCA é sobrescrito por
    dicionário vazio — a fusão só acrescenta o que falta (mesma regra do
    'vazio nunca rebaixa' do UPSERT)."""
    out = dict(dst)
    for mes, val in src.items():
        if mes not in out or not out[mes]:
            out[mes] = val
    return out


def remapear_custo(bloco: dict, mapa: dict[str, str]) -> tuple[dict, list]:
    novo: dict = {}
    conflitos = []
    for nome, val in bloco.items():
        canon = tn.canonico(nome, mapa)
        if canon in novo and novo[canon] and val:
            conflitos.append((nome, canon))
        novo[canon] = _fundir(novo.get(canon, {}) if isinstance(novo.get(canon), dict) else {},
                              val if isinstance(val, dict) else {}) or val
    return novo, conflitos


async def aplicar(conn, mapa: dict[str, str], go: bool):
    bil, perfis, custo = await grafias_do_banco(conn)

    print('\n=== BANCO (dono=%s) ===' % DONO)

    # --- bilhetes
    mud_bil = {g: tn.canonico(g, mapa) for g in bil if tn.canonico(g, mapa) != g}
    tot_bil = sum(bil[g] for g in mud_bil)
    print(f'\nbilhetes.tipster: {len(bil)} grafias, {len(mud_bil)} mudam ({tot_bil} linhas)')
    for g, c in sorted(mud_bil.items(), key=lambda kv: -bil[kv[0]]):
        print(f'    {bil[g]:5d}  {g!r} -> {c!r}')

    # --- perfis (UNIQUE dono+nome: colisão = fusão, e fusão é decisão humana)
    destino = Counter(tn.canonico(g, mapa) for g in perfis)
    colisoes = {c: [g for g in perfis if tn.canonico(g, mapa) == c]
                for c, n in destino.items() if n > 1}
    mud_perf = {g: tn.canonico(g, mapa) for g in perfis
                if tn.canonico(g, mapa) != g and tn.canonico(g, mapa) not in colisoes}
    print(f'\ntipsters.nome (perfis): {len(perfis)}, {len(mud_perf)} mudam')
    for g, c in sorted(mud_perf.items()):
        print(f'           {g!r} -> {c!r}')
    if colisoes:
        print('  ⚠ perfis que colidiriam (NÃO renomeados — fundir é decisão humana):')
        for c, gs in colisoes.items():
            print(f'           {gs} -> {c!r}')

    # --- custo por tipster (a chave É o nome)
    planos = {}
    for campo, bloco in custo.items():
        novo, conf = remapear_custo(bloco, mapa)
        planos[campo] = novo
        muda = {k: tn.canonico(k, mapa) for k in bloco if tn.canonico(k, mapa) != k}
        com_valor = [k for k, v in bloco.items() if v]
        print(f'\ncusto_store.{campo}: {len(bloco)} chaves, {len(muda)} mudam, '
              f'{len(com_valor)} com valor lançado')
        for g, c in sorted(muda.items()):
            print(f'           {g!r} -> {c!r}')
        if conf:
            print(f'  ⚠ chaves com valor fundidas: {conf}')

    if not go:
        print('\n[ENSAIO] nada escrito no banco. Rode com --go para aplicar.')
        return

    async with conn.transaction():
        n_bil = 0
        for g, c in mud_bil.items():
            r = await conn.execute(
                "UPDATE bilhetes SET tipster=$3 WHERE dono=$1 AND tipster=$2", DONO, g, c)
            n_bil += int(r.split()[-1])
        for g, c in mud_perf.items():
            await conn.execute(
                "UPDATE tipsters SET nome=$3 WHERE dono=$1 AND nome=$2", DONO, g, c)
        for campo, novo in planos.items():
            await conn.execute(
                f"UPDATE custo_store SET {campo}=$2::jsonb, atualizado_em=NOW() WHERE dono=$1",
                DONO, json.dumps(novo, ensure_ascii=False))
    print(f'\nOK — {n_bil} bilhete(s), {len(mud_perf)} perfil(is) e '
          f'{len(planos)} bloco(s) de custo renomeados.')

    bil2, perfis2, _ = await grafias_do_banco(conn)
    print('grafias em bilhetes depois:', dict(bil2.most_common()))
    print('perfis depois:', sorted(perfis2))


async def main_async(args):
    import asyncpg
    carregar_env()
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    conn = await asyncpg.connect(url, command_timeout=120)
    try:
        bil, perfis, custo = await grafias_do_banco(conn)

        if args.usar_mapa:
            mapa = tn.carregar_mapa()
            if not mapa:
                raise SystemExit('--usar-mapa: %s não existe' % tn.MAPA_PATH)
            print(f'mapa CARREGADO de {tn.MAPA_PATH} ({len(mapa)} grafias)')
        else:
            universo = Counter()
            universo.update(grafias_do_xlsx(args.xlsx))
            universo.update(bil)
            for g in perfis:
                universo[g] += 0
            for bloco in custo.values():
                for g in bloco:
                    universo[tn.limpar(g)] += 0
            mapa = tn.construir_mapa(universo)

            grupos = {}
            for g, c in mapa.items():
                grupos.setdefault(c, []).append(g)
            print(f'=== DE-PARA: {len(mapa)} grafias -> {len(grupos)} tipsters ===')
            for c, gs in sorted(grupos.items()):
                marca = '  <= ' + ', '.join(repr(x) for x in sorted(gs)) if len(gs) > 1 else ''
                print(f'  {c!r}{marca}')
            tn.salvar_mapa(mapa)
            print(f'\nmapa gravado em {tn.MAPA_PATH}')

        await aplicar(conn, mapa, args.go)
    finally:
        await conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', help='export do SharkTrack (obrigatório sem --usar-mapa)')
    ap.add_argument('--usar-mapa', action='store_true',
                    help='usa o JSON como está (para merge semântico editado à mão)')
    ap.add_argument('--go', action='store_true', help='escreve no banco')
    args = ap.parse_args()
    if not args.usar_mapa and not args.xlsx:
        raise SystemExit('--xlsx é obrigatório (ou use --usar-mapa)')
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
