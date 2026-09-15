# -*- coding: utf-8 -*-
"""Zera a base do usuário `Ewanderson1` — ele recomeça como conta virgem.

Pedido do Feca (15/09/2026): *"por favor apague tudo q subimos para a conta do
ewanderson. Ele vai passar a usar como se fosse uma conta virgem"*.

── Escopo, confirmado pelo Feca ──────────────────────────────────────────────

**A linha em `usuarios` FICA.** Mesmo e-mail, mesma senha, `status='ativo'`: ele
entra e vê a tela do primeiro dia. Apagar o cadastro o obrigaria a se recadastrar
e a ser aprovado de novo no `/admin` — não é o que "conta virgem" pede aqui.

**`uso_tokens` FICA** (1 linha): é o log de gasto de API do painel `/uso/tokens`,
contabilidade da operação, e não aparece para o usuário.

Sai todo o resto que tem coluna `dono` — inclusive as tabelas hoje em zero, para
o caso de alguma linha nascer entre este levantamento e a execução.

── Por que `bloco_visto` é OBRIGATÓRIO no pacote ─────────────────────────────

`bloco_visto` guarda o sha1 do bloco cru por (dono, casa, código) e a extração
PULA o bloco cujo hash não mudou (`repository`, barreira da s356). Apagar os
bilhetes e deixar os 220 hashes da Betano faria a próxima captura dele pular os
220 blocos: ele recaptura, a tela continua vazia e **não há erro em lugar nenhum**.
Mesma família do `CLAUDE.md`: estado que sobrevive ao dado que ele descrevia.

── Exclusão destrutiva, e por isso o dump vem antes ──────────────────────────

O `CLAUDE.md` manda mover para tabela isolada em vez de soft-delete, mas a
`lixeira_contas` cobre a exclusão de UMA conta pelo Painel, não o esvaziamento de
uma base inteira. Aqui a rede é um **dump JSON** de todas as tabelas em
`Backups/s364-zerar-ewanderson/`, gravado e conferido ANTES do primeiro DELETE —
e o dump sai do Postgres já em `to_jsonb`, então nenhuma conversão de tipo do
Python pode deformar o que for restaurado.

O DELETE roda numa transação só: ou zera tudo, ou não zera nada.

Uso:
    python scripts/zerar_base_ewanderson.py            # ENSAIO (padrão): só conta
    python scripts/zerar_base_ewanderson.py --executar # dump + DELETE de verdade
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENV_PATH = RAIZ / '.env'
BACKUP_DIR = RAIZ / 'Backups' / 's364-zerar-ewanderson'

DONO = 'Ewanderson1'

# Tabelas com coluna `dono` que são DADO DO USUÁRIO. A ordem é a do dump.
TABELAS = (
    'bilhetes',
    'parceiros',
    'correcoes',
    'bloco_visto',
    'sombra_rotulos',
    'tipsters',
    'tipster_unidade',
    'custo_store',
    'fornecedor_preco',
    'conta_logo',
    'casa_config',
    'casas_meta',
    'caixa_mov',
    'lixeira_bilhetes',
    'lixeira_contas',
    'polymarket_ativos_tipster',
)

# Fica de pé, e é medido no fim para provar que ficou.
PRESERVADAS = ('usuarios', 'uso_tokens')


def carregar_env() -> None:
    for line in ENV_PATH.open(encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def main(executar: bool) -> None:
    import asyncpg

    carregar_env()
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    conn = await asyncpg.connect(url, command_timeout=120)
    try:
        # O `dono` é conferido na tabela, nunca deduzido: username errado não dá
        # erro, apaga a base de outra pessoa (`CLAUDE.md`, a regra da s260).
        u = await conn.fetchrow(
            'SELECT username, email, status FROM usuarios WHERE username = $1', DONO)
        if not u:
            raise SystemExit(f'dono {DONO!r} não existe em `usuarios` — abortado')
        print(f'dono conferido: {u["username"]} · {u["email"]} · {u["status"]}')

        existentes = []
        for t in TABELAS:
            if await conn.fetchval('SELECT to_regclass($1)', f'public.{t}') is None:
                print(f'  ⚠️ tabela {t} não existe neste banco — pulada')
                continue
            existentes.append(t)

        print('\n── o que será apagado ──')
        antes = {}
        for t in existentes:
            antes[t] = await conn.fetchval(f'SELECT count(*) FROM {t} WHERE dono = $1', DONO)
            if antes[t]:
                print(f'  {t:28s} {antes[t]}')
        total = sum(antes.values())
        print(f'  {"TOTAL":28s} {total}')

        print('\n── o que fica ──')
        print(f'  usuarios: 1 linha ({u["username"]}, senha e status intactos)')
        n_tok = await conn.fetchval('SELECT count(*) FROM uso_tokens WHERE dono = $1', DONO)
        print(f'  uso_tokens: {n_tok}')

        if not executar:
            print('\nENSAIO — nada foi apagado. Rode com --executar para valer.')
            return

        # ---------- dump ANTES de qualquer DELETE ----------
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        carimbo = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        dump: dict[str, object] = {
            'dono': DONO,
            'gerado_em': carimbo,
            'usuario': {k: str(v) for k, v in dict(u).items()},
            'tabelas': {},
        }
        for t in existentes + list(PRESERVADAS[1:]):
            # to_jsonb no servidor: o Python não converte tipo nenhum no caminho.
            bruto = await conn.fetchval(
                f'SELECT json_agg(to_jsonb(t))::text FROM {t} t WHERE t.dono = $1', DONO)
            dump['tabelas'][t] = json.loads(bruto) if bruto else []

        destino = BACKUP_DIR / f'ewanderson1_{carimbo}.json'
        destino.write_text(json.dumps(dump, ensure_ascii=False, indent=1), encoding='utf-8')

        # Confere o que foi escrito antes de apagar a origem: dump que ninguém
        # releu é promessa, não backup.
        relido = json.loads(destino.read_text(encoding='utf-8'))
        for t in existentes:
            if len(relido['tabelas'][t]) != antes[t]:
                raise SystemExit(
                    f'dump de {t} tem {len(relido["tabelas"][t])} linhas, '
                    f'esperado {antes[t]} — nada foi apagado')
        kb = destino.stat().st_size / 1024
        print(f'\ndump conferido: {destino} ({kb:.0f} KB, {total} linhas)')

        # ---------- DELETE, tudo numa transação ----------
        apagado = {}
        async with conn.transaction():
            for t in existentes:
                r = await conn.execute(f'DELETE FROM {t} WHERE dono = $1', DONO)
                apagado[t] = int(r.split()[-1])

        print('\n── apagado ──')
        for t, n in apagado.items():
            if n:
                print(f'  {t:28s} {n}')
        print(f'  {"TOTAL":28s} {sum(apagado.values())}')

        print('\n── conferência depois ──')
        sobrou = 0
        for t in existentes:
            n = await conn.fetchval(f'SELECT count(*) FROM {t} WHERE dono = $1', DONO)
            sobrou += n
            if n:
                print(f'  ⚠️ {t}: ainda {n}')
        print(f'  linhas restantes nas tabelas de dado: {sobrou}')
        u2 = await conn.fetchrow(
            'SELECT username, email, status FROM usuarios WHERE username = $1', DONO)
        print(f'  usuarios: {dict(u2) if u2 else "SUMIU — isto é defeito"}')
        print(f'  uso_tokens: '
              f'{await conn.fetchval("SELECT count(*) FROM uso_tokens WHERE dono = $1", DONO)}')
    finally:
        await conn.close()


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    asyncio.run(main('--executar' in sys.argv))
