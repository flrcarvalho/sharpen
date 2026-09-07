# -*- coding: utf-8 -*-
"""Atribui cada uma das 196 apostas do atraso do canal ao ADMIN que a postou.

O canal `Grego Tips - VIP` tem **Sign messages** ligado, então cada post carrega
a assinatura de quem escreveu. No export (`ChatExport_2026-09-06`) são
**`grego` 958 posts e `ricklxrd` 110** — e nas 79 mensagens de aposta do atraso,
**58 são do grego e 21 do ricklxrd**.

Isso torna a atribuição **determinística**: não há heurística, não há join
aproximado. A assinatura vem do mesmo bloco HTML de onde eu li a legenda, e o
`import_grego_canal_s325.py` já grava o id da mensagem no cabeçalho de cada
seção — o código do bilhete e a assinatura se encontram pelo `msg`.

── Por que o HISTÓRICO (as 956 do tracker) fica de fora ──────────────────────

O CSV do tracker não tem id de mensagem: para atribuir aquelas linhas seria
preciso casá-las com o post por (título, stake, data), e isso foi MEDIDO:

    título inteiro + stake + janela de ±1 dia → 704 de 956 (73,6%), 0 ambíguas
    palavra-chave  + stake + janela de ±1 dia → 735 (76,9%), mas 87 ambíguas

Ou seja: um quarto da base ficaria sem autor. E o estrago não é a lacuna — é o
que ela faz com a leitura: um ROI "por admin" calculado sobre 74% das apostas
**parece completo e não é**. Enquanto o histórico inteiro está sob a marca
`Grego Tips - VIP`, ninguém lê aquilo como "a carteira do Grego".

Então a régua é: **o atraso (196) e tudo o que o bot planilhar daqui pra frente
saem por autor; as 956 do tracker continuam sob a marca.** Se o Feca quiser as
956 assim mesmo, os números acima é que decidem — não é medição a refazer.

Uso:
    python scripts/atribuir_autor_grego_s325.py --dono gregozxrd
    python scripts/atribuir_autor_grego_s325.py --dono gregozxrd --go
"""
import argparse
import asyncio
import html
import os
import re
from collections import Counter
from pathlib import Path

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
EXPORT = Path(r'C:\Users\Fernando\Downloads\Telegram Desktop\ChatExport_2026-09-06')
SCRIPT_IMPORT = Path(os.path.dirname(__file__)) / 'import_grego_canal_s325.py'

# assinatura do canal → nome que vai para a coluna `Tipster`. O mesmo nome que o
# bot usa em `GV_TIPSTER_NOMES` — divergir aqui criaria dois rótulos para a
# mesma pessoa, e a coluna é TEXTO (cada grafia é um tipster diferente na tela).
NOMES = {'grego': 'Grego', 'ricklxrd': 'Rick'}


def assinaturas() -> dict[int, str]:
    """msg id → assinatura, lida do export."""
    bruto = ''
    for nome in ('messages.html', 'messages2.html'):
        p = EXPORT / nome
        if p.exists():
            bruto += p.read_text(encoding='utf-8')
    if not bruto:
        raise SystemExit(f'export não encontrado em {EXPORT}')
    out = {}
    for bloco in re.split(r'(?=<div class="message )', bruto):
        mid = re.search(r'id="message(\d+)"', bloco)
        if not mid:
            continue
        sig = re.search(r'<div class="signature details">\s*(.*?)\s*</div>', bloco, re.S)
        out[int(mid.group(1))] = html.unescape(sig.group(1)).strip() if sig else None
    return out


def codigos_por_msg() -> list[tuple[str, int]]:
    """(código, msg) na MESMA ordem que o import gerou — o bloco `DADOS` do
    script de import é a fonte, para não haver duas numerações."""
    texto = SCRIPT_IMPORT.read_text(encoding='utf-8')
    corpo = texto.split('DADOS = """', 1)[1].split('"""', 1)[0]
    cab = re.compile(r'^#\s+\d+\s+(\d+)\s+\d{2}/\d{2}/\d{4}\s+.+$')
    out, msg, n = [], None, 33      # o import começa em GV202609-33
    for linha in corpo.strip().splitlines():
        l = linha.strip()
        if not l:
            continue
        m = cab.match(l)
        if m:
            msg = int(m.group(1))
            continue
        if l.startswith('#'):
            continue
        if msg is None:
            raise SystemExit(f'linha de aposta antes do cabeçalho: {l!r}')
        out.append((f'GV202609-{n}', msg))
        n += 1
    return out


def carregar_env():
    for line in open(ENV_PATH, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def aplicar(pares: list[tuple[str, str]], dono: str, go: bool):
    import asyncpg
    carregar_env()
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    conn = await asyncpg.connect(url, command_timeout=120)
    try:
        antes = await conn.fetch(
            'SELECT tipster, COUNT(*) FROM bilhetes WHERE dono=$1 GROUP BY 1 ORDER BY 2 DESC', dono)
        print('tipster ANTES:', {r['tipster']: r['count'] for r in antes})

        # o código tem de existir, senão a atribuição silenciosamente não faz nada
        faltando = await conn.fetch(
            'SELECT c FROM unnest($2::text[]) AS c '
            'WHERE NOT EXISTS (SELECT 1 FROM bilhetes b WHERE b.dono=$1 AND b.codigo_bilhete=c)',
            dono, [c for c, _ in pares])
        if faltando:
            raise SystemExit(
                f'✋ ABORTADO — {len(faltando)} código(s) desta faixa não existem na base: '
                f'{[r["c"] for r in faltando][:6]}. Rode o import do canal antes.')

        if not go:
            print('\nDRY RUN — nada foi escrito. Repita com --go para gravar.')
            return
        async with conn.transaction():
            for nome in sorted({n for _, n in pares}):
                cods = [c for c, n in pares if n == nome]
                r = await conn.execute(
                    'UPDATE bilhetes SET tipster=$3 WHERE dono=$1 AND codigo_bilhete = ANY($2::text[])',
                    dono, cods, nome)
                print(f'  {nome:<8} {r}')
        depois = await conn.fetch(
            'SELECT tipster, COUNT(*) FROM bilhetes WHERE dono=$1 GROUP BY 1 ORDER BY 2 DESC', dono)
        print('tipster DEPOIS:', {r['tipster']: r['count'] for r in depois})
    finally:
        await conn.close()


def main():
    ap = argparse.ArgumentParser(description='Atribui as 196 do atraso ao admin que postou.')
    ap.add_argument('--dono', required=True)
    ap.add_argument('--go', action='store_true')
    a = ap.parse_args()

    sigs = assinaturas()
    pares = []
    sem_assinatura = []
    for codigo, msg in codigos_por_msg():
        sig = sigs.get(msg)
        nome = NOMES.get(sig)
        if not nome:
            sem_assinatura.append((codigo, msg, sig))
            continue
        pares.append((codigo, nome))

    print(f'{"=" * 74}\n{"GRAVAÇÃO" if a.go else "DRY RUN"} — autor por assinatura do post\n{"=" * 74}')
    print(f'linhas: {len(pares) + len(sem_assinatura)} | atribuídas: {len(pares)}')
    print('por autor:', dict(Counter(n for _, n in pares).most_common()))
    msgs_por_autor = Counter()
    vistos = set()
    for codigo, msg in codigos_por_msg():
        if msg in vistos:
            continue
        vistos.add(msg)
        msgs_por_autor[NOMES.get(sigs.get(msg), '(sem assinatura)')] += 1
    print('mensagens por autor:', dict(msgs_por_autor.most_common()))

    if sem_assinatura:
        print(f'\n⚠ {len(sem_assinatura)} linha(s) sem assinatura reconhecida — ficam como estão:')
        for c, m, s in sem_assinatura[:10]:
            print(f'    {c} (msg {m}) assinatura={s!r}')

    asyncio.run(aplicar(pares, a.dono, a.go))


if __name__ == '__main__':
    main()
