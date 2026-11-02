"""Importa a base do operador Lava (dono='Lava', origem='import').

Bloco do CSV "2026 Contas Pessoais - DB Apostas (9).csv" a partir do marcador
"Lava:" (linha 25856) — 3315 apostas. Normaliza tipster e mercado ao canon do
projeto (decisão do Feca, sessão 75). P/L é derivado (não persistido).

A assinatura é computada localmente, idêntica a repository._assinatura (mesma
ordem de campos, _norm_odd, contador de duplicatas por lote), e a escrita é
um bulk INSERT numa única transação — robusto contra a queda do proxy público
do Railway (que derrubava o upsert linha-a-linha no meio).

Uso:
    python scripts/import_lava.py --dry   # só valida e mostra o que faria (sem DB)
    python scripts/import_lava.py --go    # escreve no Postgres de produção
"""
import asyncio
import csv
import hashlib
import os
import sys
from collections import Counter
from _lixeira import mover_para_lixeira  # Fase 7 (s438): aposta sai pela lixeira

CSV_PATH = r'C:\Users\Fernando\Downloads\2026 Contas Pessoais - DB Apostas (9).csv'
ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
DONO = 'Lava'
VALID = {'W', 'L', 'V', 'HW', 'HL'}

# ---------- normalização de tipster (ao canon do Feca, sessão 70) ----------
TIPSTER_MAP = {'Tcinsider': 'TC Insider', 'Insider': 'TC Insider', 'Só Chutes': 'SóChutes'}


def norm_tipster(t: str) -> str:
    t = (t or '').strip()
    return TIPSTER_MAP.get(t, t)


# ---------- normalização de mercado (ao canon MASTER_APOSTAS) ----------
CANON_KEEP = {
    'ML', 'Handicap', 'Player Props', 'Cartões', 'Games', 'Sets', 'Team Props',
    'Desarmes', 'Anytime', 'DNB', 'Chutes', 'Gols', 'Escanteios', 'Dupla Chance',
    'Múltipla', 'Outros', 'Ambas Marcam', 'Corridas',
}


def norm_mercado(esp: str, ap: str, desc: str) -> str:
    esp = (esp or '').strip(); ap = (ap or '').strip(); d = (desc or '').lower()
    if ap in CANON_KEEP:
        return ap
    if ap == 'BTTS':
        return 'Ambas Marcam'
    if ap.lower() == 'handicap':
        return 'Handicap'
    if ap == '':
        return 'Múltipla' if esp.startswith('Múlti') else 'Outros'
    if ap == 'Resultado Correto':
        return 'Outros'            # placar exato não tem categoria própria
    if ap == 'Campeão':
        return 'ML'                # vencedor do torneio = resultado principal
    if ap == 'Race':
        return 'Outros'            # objeto não identificável na descrição (8 linhas)
    if ap == 'Under':              # tipo de mercado → categoria pelo objeto/esporte
        if esp == 'Basquete':
            return 'Player Props'  # MASTER §673: stat individual NBA = Player Props
        if esp == 'Futebol':
            return 'Gols'          # under de futebol = total de gols
        if esp == 'Baseball':
            return 'Corridas'      # under de baseball = total de runs
        if esp == 'Tênis':
            if 'set' in d:
                return 'Sets'
            if 'jogo' in d or 'game' in d:
                return 'Games'
            return 'Player Props'
        return 'Outros'
    return 'Outros'


# ---------- assinatura (idêntica a repository._assinatura / _norm_odd) ----------
def _norm_odd(v: str) -> str:
    try:
        return f"{round(float(v.replace(',', '.')), 2):.2f}"
    except (ValueError, AttributeError):
        return v


def assinaturas(rows: list[dict]) -> list[str]:
    """Assinatura por linha com contador de duplicatas por lote (igual ao app)."""
    counts: dict[str, int] = {}
    sigs = []
    for r in rows:
        base_raw = "|".join([
            r['casa'], r['parceiro'], r['data'], r['aposta'], r['descricao'],
            _norm_odd(r['odd']),
        ])
        base_sig = hashlib.sha256(base_raw.encode()).hexdigest()[:20]
        cnt = counts.get(base_sig, 0) + 1
        counts[base_sig] = cnt
        raw = base_raw if cnt == 1 else f"{base_raw}|{cnt}"
        sigs.append(hashlib.sha256(raw.encode()).hexdigest()[:20])
    return sigs


def carregar_rows() -> list[dict]:
    rows = list(csv.reader(open(CSV_PATH, encoding='utf-8')))
    start = next(i for i, r in enumerate(rows)
                 if r and r[0].strip().lower().startswith('lava'))
    data = [r for r in rows[start + 1:]
            if len(r) >= 10 and r[0].strip() and r[0].strip()[0].isdigit()]
    out = []
    for r in data:
        out.append({
            'data': r[0].strip(),
            'esporte': r[1].strip(),
            'tipster': norm_tipster(r[2]),
            'casa': r[3].strip(),
            'parceiro': r[4].strip(),
            'aposta': norm_mercado(r[1], r[5], r[6]),
            'descricao': r[6].strip(),
            'stake': r[7].strip(),
            'odd': r[8].strip(),
            'resultado': r[9].strip(),
        })
    return out


def carregar_env():
    for line in open(ENV_PATH, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def importar(rows: list[dict]):
    import asyncpg
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    sigs = assinaturas(rows)
    pares = sorted(set((r['casa'], r['parceiro']) for r in rows))

    # tuplas do INSERT (mesma ordem de colunas do upsert_bilhetes do app)
    registros = []
    for r, sig in zip(rows, sigs):
        estado = 'resolvida' if r['resultado'] in VALID else 'aberta'
        registros.append((
            DONO, r['casa'], r['parceiro'], sig, None,            # codigo_bilhete
            r['data'], r['esporte'], r['tipster'], r['aposta'], r['descricao'],
            r['stake'], r['odd'], r['resultado'] or None, estado,
            None, None, 'import',                                 # confianca, stake_usd, origem
        ))

    last_err = None
    for tentativa in range(1, 4):
        try:
            conn = await asyncpg.connect(url, command_timeout=120)
            try:
                async with conn.transaction():
                    # limpa qualquer import parcial anterior (idempotente)
                    apagadas = len(await mover_para_lixeira(conn, "dono=$1 AND origem='import'", [DONO], "reimport: import_lava.py"))
                    print(f'  [tentativa {tentativa}] limpou parciais: {apagadas}')
                    await conn.executemany(
                        """
                        INSERT INTO bilhetes
                            (dono, casa, parceiro, assinatura, codigo_bilhete, data, esporte,
                             tipster, aposta, descricao, stake, odd, resultado,
                             extraction_state, confianca, stake_usd, origem)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
                        ON CONFLICT (dono, casa, parceiro, assinatura) DO NOTHING
                        """,
                        registros,
                    )
                    for casa, parceiro in pares:
                        await conn.execute(
                            """INSERT INTO parceiros (dono, casa, nome) VALUES ($1,$2,$3)
                               ON CONFLICT (dono, casa, nome) DO NOTHING""",
                            DONO, casa, parceiro)
                    # backfill criado_em por data (lista ordena por criado_em DESC)
                    await conn.execute(
                        """
                        WITH ordered AS (
                            SELECT id,
                                   ROW_NUMBER() OVER (ORDER BY to_date(data,'DD/MM/YYYY') ASC, id ASC) AS rn,
                                   COUNT(*) OVER () AS total
                            FROM bilhetes WHERE dono=$1 AND origem='import'
                        )
                        UPDATE bilhetes b
                        SET criado_em = NOW() - ((o.total - o.rn) * INTERVAL '1 second')
                        FROM ordered o WHERE b.id = o.id
                        """, DONO)
                # auditoria (fora da transação)
                n = await conn.fetchval("SELECT COUNT(*) FROM bilhetes WHERE dono=$1", DONO)
                nc = await conn.fetchval(
                    "SELECT COUNT(DISTINCT casa) FROM parceiros WHERE dono=$1", DONO)
                np = await conn.fetchval("SELECT COUNT(*) FROM parceiros WHERE dono=$1", DONO)
                print(f'\nOK — bilhetes dono=Lava={n} | casas sidebar={nc} | parceiros={np}')
                return
            finally:
                await conn.close()
        except Exception as e:                       # noqa: proxy instável → retry
            last_err = e
            print(f'  [tentativa {tentativa}] falhou: {type(e).__name__}: {e}')
    raise SystemExit(f'import falhou após 3 tentativas: {last_err}')


def main(go: bool):
    rows = carregar_rows()
    print(f'linhas a importar: {len(rows)}')
    print('casas:', dict(Counter(r['casa'] for r in rows)))
    print('aposta (pós-normalização):', dict(Counter(r['aposta'] for r in rows).most_common()))
    print(f'pares (casa, parceiro) distintos: {len(set((r["casa"], r["parceiro"]) for r in rows))}')
    if not go:
        print('\n[DRY] nada escrito. Rode com --go para importar.')
        return
    carregar_env()
    asyncio.run(importar(rows))


main(go='--go' in sys.argv)
