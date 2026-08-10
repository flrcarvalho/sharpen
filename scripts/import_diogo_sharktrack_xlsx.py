# -*- coding: utf-8 -*-
"""Importa a base do Diogo exportada do SharkTrack (.xlsx) para dono='Diogo'.

Toda a base do Diogo vem do SharkTrack (decisão do Feca, s255): o export é a
fonte única. O banco do Diogo estava **vazio** de bilhetes (0 linhas) e com 20
contas já cadastradas — este import é a primeira carga.

Layout do export (header na linha 1, 15 colunas):

    0 Data de cadastro | 1 Data do jogo | 2 Tipo de Aposta | 3 Esporte |
    4 Evento | 5 Aposta | 6 Mercado | 7 Odd | 8 Valor apostado | 9 Status |
    10 Casa de apostas | 11 Tipster | 12 Torneio | 13 País | 14 Cashout

Decisões do Feca (s255):

- **Parceiro** = `SharkTrack` para TODA linha, **sem fornecedor** (nome puro, sem
  `[...]`, que é o que `dashboard_rows` usa para derivar conta × fornecedor).
  As 20 contas reais já cadastradas do Diogo seguem intactas — este import não
  as toca.
- **Casa** preenchida a partir de `Casa de apostas`, normalizada para a grafia
  **canônica que a base do Diogo já usa** (`_CASA_MAP` abaixo). `casa` é TEXTO em
  7 tabelas: grafia divergente = casa diferente no sistema (CLAUDE.md).

Decisões de mapeamento (derivadas dos MASTERs, não do export):

- **Data** = `Data do jogo` (decisão do Feca, s255), não `Data de cadastro`. As
  duas divergem em 984 das 3.590 linhas: 589 apostas feitas na véspera ou antes,
  395 ao vivo (cadastro depois do início). O P/L fica agrupado pela data da
  PARTIDA, não pela do aporte.
- **Esporte** = `MASTER_ESPORTES §2`, recalculado do zero — o rótulo do
  SharkTrack não segue a regra. `Vários` do SharkTrack significa "vários
  mercados" e cai em bilhete de UM jogo só (769 linhas), que o §2 manda
  classificar com o esporte do jogo, nunca `Múltiplos`. A regra aplicada:
  3+ confrontos distintos OU mistura de esportes → `Múltiplos`; senão, o esporte
  do jogo (inferido por torneio/mercado quando o SharkTrack disse `Vários`).
- **Aposta** (categoria) = `MASTER_APOSTAS`. Cupom com mais de uma seleção
  (`Múltipla`, `Criar Aposta` ou ` / ` no mercado) → `Múltipla` (§5 Bet Builder).
  Seleção única → classificador por OBJETO apostado (§5 Desambiguação: o tipo de
  mercado — handicap, total, comparativo — nunca muda a categoria).
- **Descrição** = `MASTER_DESCRICAO`: seleções unidas por ` // ` (regra #19),
  confronto em `[A v B]`. Confronto só é montado quando a perna do `Evento` parte
  limpo em dois por ` - `; senão o nome do evento entra verbatim entre colchetes
  (F1, torneio) — §9 proíbe inventar confronto.
- **Resultado** = `MASTER_RESULTADO`. `Cashout` segue §5.1.2/§5.6: cashout = stake
  → `V` (odd exibida); cashout ≠ stake → `W` com `Odd = Cashout ÷ Stake`.
  `Pendente` → resultado vazio (aposta aberta).

Uso:
    python scripts/import_diogo_sharktrack_xlsx.py --xlsx "C:\\...\\apostas.xlsx"        # DRY
    python scripts/import_diogo_sharktrack_xlsx.py --xlsx "C:\\...\\apostas.xlsx" --go   # escreve
"""
import argparse
import asyncio
import datetime as dt
import hashlib
import os
import re
from collections import Counter

import openpyxl

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
DONO = 'Diogo'
PARCEIRO = 'SharkTrack'      # sem fornecedor: nome puro, nunca "Conta [Fornecedor]"
ORIGEM = 'import'
VALID = {'W', 'L', 'V', 'HW', 'HL'}

SEP_SEL = ' / '              # separador de seleção do SharkTrack
SEP_CONF = ' - '             # separador de confronto do SharkTrack


# ---------- sanitização ----------
_CTRL = re.compile(r'[\x00-\x1f\x7f]+')


def limpa(v) -> str:
    if v is None:
        return ''
    return re.sub(r'\s{2,}', ' ', _CTRL.sub(' ', str(v))).strip()


def _para_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = limpa(v).replace('R$', '').replace('\xa0', '').replace(' ', '')
    if not s:
        return None
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def _float_str(n: float) -> str:
    """Precisão completa (nunca truncar odd), vírgula decimal."""
    s = repr(round(float(n), 10))
    if s.endswith('.0'):
        s = s[:-2]
    return s.replace('.', ',')


# ---------- casa ----------
# Grafias CANÔNICAS: as que a base do Diogo já usa em `parceiros` (20 contas) e
# as do `_CASA_DISPLAY` (app/main.py). Registrar grafia gêmea criaria casa
# paralela — `casa` é TEXTO em 7 tabelas.
_CASA_MAP = {
    'bet365':          'Bet365',
    'betano':          'Betano',
    'pinnacle':        'Pinnacle',
    'superbet':        'Superbet',
    'betfair':         'Betfair',
    'novibet':         'Novibet',
    'jonbet':          'Jonbet',
    'rei do pitaco':   'Rei do Pitaco',
    'blaze':           'Blaze',
    'vixe':            'VixeBet',
    'bingo':           'BingoBet',
    'bingoplus':       'BingoPlus',
    'lance de sorte':  'Lance de Sorte',
    'betboom':         'Betboom',
    'polymarket':      'Polymarket',
    'sportingbet':     'Sportingbet',
    'betesporte':      'BETesporte',
    'vaidebet':        'VaideBet',
    'bolsa de aposta': 'Bolsa de Aposta',
    'aposta ganha':    'Aposta Ganha',
    'betão':           'Betão',
}


def norm_casa(v) -> str:
    bruto = limpa(v)
    return _CASA_MAP.get(bruto.lower(), bruto)


# ---------- tipster ----------
def norm_tipster(v) -> str:
    """O SharkTrack guarda a caixa que o Diogo digitou ('peixe' e 'Peixe' são o
    mesmo tipster). Unifica em Title Case — o dashboard trata tipster por texto."""
    t = limpa(v)
    if not t:
        return ''
    return ' '.join(p[:1].upper() + p[1:] for p in t.split(' '))


# ---------- esporte ----------
# `Padel` é PROIBIDO como valor de Esporte (MASTER_ESPORTES §7, "Regra Crítica —
# Tênis vs Padel"): notação de duplas `X/Y v W/Z` é sinal forte de Tênis.
_ESPORTE_MAP = {
    'futebol': 'Futebol', 'tênis': 'Tênis', 'dardos': 'Dardos',
    'esports': 'E-Sports', 'e-sports': 'E-Sports', 'vôlei': 'Vôlei',
    'badminton': 'Badminton', 'fórmula 1': 'F1', 'basquete': 'Basquete',
    'mma': 'MMA', 'rugby': 'Rugby', 'handebol': 'Handebol',
    'padel': 'Tênis', 'outros esportes': 'Outro', 'vários': '',
}

# Inferência de esporte quando o SharkTrack disse "Vários" (= vários mercados,
# não vários esportes). Ordem = prioridade; casa com Torneio + Mercado + Aposta.
_INFER = [
    ('F1',        r'grande pr[êe]mio|gp d|grand prix|\bf1\b|f[óo]rmula|volta|pit stop|classificat[óo]ri|p[óo]dio|piloto'),
    ('MMA',       r'\bufc\b|\bluta\b|method of victory|m[ée]todo de vit[óo]ria|nocaute|inside distance|submiss'),
    ('Tênis',     r'wimbledon|roland|us open|australian open|\batp\b|\bwta\b|challenger|\bitf\b|montreal|toronto|cincinnati|masters|sem perder um set|\bset\b|\bgames?\b|jogador vence jogo'),
    ('Badminton', r'badminton|\bbwf\b|super \d{3}'),
    ('Dardos',    r'dardos|darts|180|checkout|\blegs?\b|\bpdc\b'),
    ('Basquete',  r'\bnba\b|wnba|ncaa|basquete|\bnbb\b|cestas|rebote'),
    ('Baseball',  r'baseball|\bmlb\b|innings?|strikeout|home run|\brbi'),
    ('Vôlei',     r'v[ôo]lei|volleyball|\bvnl\b'),
    ('E-Sports',  r'e-?sports|\bcs2\b|csgo|counter|dota|league of legends|valorant|rainbow|call of duty|\bmapa'),
    ('Futebol',   r'\bgol|escanteio|cart[ãa]o|cart[õo]es|impedimento|brasileir|copa|liga|s[ée]rie [ab]|uefa|libertadores|sul-americana|campeonato|divis[ãa]o|amistoso|fifa|premier|laliga|bundesliga'),
]


def infer_esporte(evento: str, torneio: str, mercado: str, aposta: str) -> str:
    alvo = f'{evento} | {torneio} | {mercado} | {aposta}'.lower()
    for esporte, padrao in _INFER:
        if re.search(padrao, alvo):
            return esporte
    return ''


def pernas(txt: str) -> list[str]:
    return [p for p in (limpa(txt).split(SEP_SEL)) if p]


def confrontos(evento: str) -> list[str]:
    """Pernas de confronto do `Evento`, com a armadilha das DUPLAS resolvida.

    O SharkTrack usa ` / ` para duas coisas: separar jogos de uma acumulada
    (`A - B / C - D`) e separar os parceiros de uma dupla (`A / B - C / D`,
    Badminton e Tênis de duplas). Partir sempre por ` / ` transformava UMA
    partida de duplas em três "confrontos" — e o bilhete virava `Múltiplos`
    com a descrição picada.

    Regra: o corte por ` / ` só vale quando TODA perna resultante tem
    exatamente um ` - `. Senão, string com um único ` - ` é um confronto só
    (duplas); o resto vai perna a perna, em melhor esforço.
    """
    legs = pernas(evento)
    if legs and all(p.count(SEP_CONF) == 1 for p in legs):
        return legs
    if limpa(evento).count(SEP_CONF) == 1:
        return [limpa(evento)]
    return legs


def esporte_final(esp_bruto: str, evento: str, torneio: str,
                  mercado: str, aposta: str) -> str:
    """MASTER_ESPORTES §2 — `Múltiplos` só com 3+ CONFRONTOS distintos ou mistura
    de esportes. Bet builder do mesmo jogo usa o esporte do jogo."""
    confs = {c for c in confrontos(evento) if SEP_CONF in c}
    if len(confs) >= 3:
        return 'Múltiplos'
    canon = _ESPORTE_MAP.get(limpa(esp_bruto).lower(), limpa(esp_bruto))
    if canon:
        return canon
    inferido = infer_esporte(evento, torneio, mercado, aposta)
    if inferido:
        return inferido
    # Sem esporte dedutível. Com 2+ confrontos, o `Vários` do SharkTrack é
    # mistura de modalidades (§2 regra 1) → `Múltiplos`. Sem isso, `Outro` (§3).
    return 'Múltiplos' if len(confs) >= 2 else 'Outro'


# ---------- categoria (MASTER_APOSTAS) ----------
_TIPOS_COMBO = {'múltipla', 'criar aposta'}

# Ordem = prioridade. OBJETO apostado primeiro (§5 Desambiguação: handicap/total/
# comparativo não mudam a categoria), tipo de mercado só no fim.
_REGRAS = [
    ('Escanteios',     r'escanteio|corner|\bcanto'),
    ('Cartões',        r'cart[ãõ]|cartao|cartoes|\bcard'),
    ('Impedimentos',   r'impedimento|offside'),
    ('Chutes no Gol',  r'chutes? (?:no|ao|a) gol|chutes? no alvo|finaliza[çc][õo]es no gol|shots on target|\bsot\b'),
    ('Chutes',         r'chute|finaliza[çc][ãõ]|\bshots?\b'),
    ('Desarmes',       r'desarme|tackle|intercept'),
    ('E-Sports Props', r'\bkills?\b|\babates?\b|\btorres\b|drag[õo]es|inibidor|bomba plantada'),
    ('Ambas Marcam',   r'amb[ao]s.*marcam|both teams|\bbtts\b'),
    ('Assistência',    r'assist[êe]ncia|\bassists?\b'),
    ('Anytime',        r'marcar|marcador|\bscorer\b|marca gol'),
    ('Gols',           r'\bgol|\bgoals?\b'),
    ('Legs',           r'\blegs?\b'),
    # 180's: comparativo entre os dois jogadores = H2H; total (do jogo ou de um
    # jogador) = Player Props (§6 Dardos). `Outros` seria pior — §2 manda usar a
    # categoria mais específica aplicável.
    ('H2H',            r"maioria de 180|mais 180|most 180|head to head|\bh2h\b|comparativ|duelo"),
    ('Player Props',   r"180'?s|checkout|maior finaliza|highest finish|rebote|\bfaltas?\b"),
    ('Sets',           r'\bsets?\b'),
    ('Games',          r'\bgames?\b|total de jogos'),
    ('Pontos',         r'\bponto'),
    ('Rounds',         r'\brounds?\b|assalto'),
    ('Dupla Chance',   r'dupla chance|chance dupla|double chance|resultado duplo|dupla resultado'),
    ('DNB',            r'draw no bet|empate anula|empate devolve|\bdnb\b'),
    ('Handicap',       r'handicap|spread|asi[áa]tic|\blinha\b'),
    ('ML',             r'moneyline|\bml\b|vencedor|vencer|ganhar|ganha|resultado|1x2|winner|vence|'
                       r'classifica|qualifica|intervalo/|m[ée]todo de vit|inside distance|aposta na partida'),
]

# Fallback do total genérico ('Total', 'Totais do Jogo', 'Total - 2 Opções',
# 'Partida OU'): o objeto contado vem do ESPORTE.
_TOTAL_POR_ESPORTE = {
    'Futebol': 'Gols', 'eSoccer': 'Gols',
    'Basquete': 'Pontos', 'eBasket': 'Pontos', 'Vôlei': 'Pontos',
    'Badminton': 'Pontos', 'E-Sports': 'Pontos',
    'Tênis': 'Games', 'Dardos': 'Legs', 'MMA': 'Rounds',
}


def eh_combo(tipo: str, mercado: str, aposta: str) -> bool:
    """Cupom com mais de uma seleção. O TIPO manda; o ` / ` pega as linhas
    rotuladas 'Simples' que na verdade são bet builder. `Super Odds` /
    `Todos ganham` são o combo promocional da casa — várias seleções coladas
    por `&`, sem o ` / ` de sempre."""
    if limpa(tipo).lower() in _TIPOS_COMBO:
        return True
    if re.search(r'super odds|super combina|todos ganham|todas as respostas|'
                 r'especiais do dia|todos se qualificam|tudo para ganhar',
                 f'{mercado} {aposta}', re.I):
        return True
    return len(pernas(mercado)) > 1 or len(pernas(aposta)) > 1


def categoria(mercado: str, aposta: str, esporte: str, combo: bool) -> str:
    if combo:
        return 'Múltipla'
    alvo = f'{limpa(mercado)} {limpa(aposta)}'.lower()
    # Handicap de rounds/mapas é Handicap, não Rounds (§6 MMA e E-Sports).
    if 'handicap' in alvo and re.search(r'\brounds?\b|\bmapas?\b', alvo):
        return 'Handicap'
    # F1 não tem seção própria no MASTER_APOSTAS: o vencedor do GP é o resultado
    # principal (`ML`); pódio, posição na volta, grid e Q3 são resultado
    # INDIVIDUAL do piloto → `Player Props` (§2: antes de `Outros`).
    if esporte == 'F1':
        if re.search(r'\bh2h\b|comparativ|duelo', alvo):
            return 'H2H'
        if re.search(r'vencedor|winner|vencer|carro vencedor', alvo):
            return 'ML'
        return 'Player Props'
    for cat, padrao in _REGRAS:
        if re.search(padrao, alvo):
            return cat
    if re.search(r'\btota(l|is)\b|partida ou', alvo):
        return _TOTAL_POR_ESPORTE.get(esporte, 'Outros')
    return 'Outros'


# ---------- descrição (MASTER_DESCRICAO) ----------
def _conf(perna: str) -> str:
    """`A - B` → `[A v B]`. Perna que não é confronto (GP, torneio) entra
    verbatim entre colchetes — §9 proíbe inventar o que não está no bilhete."""
    partes = perna.split(SEP_CONF)
    return f'[{partes[0].strip()} v {partes[1].strip()}]' if len(partes) == 2 else f'[{perna}]'


def descricao(aposta: str, evento: str) -> str:
    sels = pernas(aposta)
    evs = confrontos(evento)          # mesmo parse do esporte (duplas resolvidas)
    if not sels:
        sels = [limpa(aposta)]
    # Acumulada perna-a-perna: mesma quantidade de seleções e de eventos (>1) →
    # cada seleção carrega o próprio confronto.
    if len(evs) > 1 and len(evs) == len(sels):
        return ' // '.join(f'{s} {_conf(e)}'.strip() for s, e in zip(sels, evs))
    corpo = ' // '.join(sels)
    if len(evs) == 1:
        return f'{corpo} {_conf(evs[0])}'.strip()
    if evs:
        return f'{corpo} ' + ' '.join(_conf(e) for e in evs)
    return corpo


# ---------- resultado / odd / stake (MASTER_RESULTADO) ----------
_STATUS = {
    'ganha': 'W', 'perdida': 'L', 'reembolsada': 'V',
    'meio ganha': 'HW', 'meio perdida': 'HL', 'pendente': '',
}


def resultado_e_odd(status, odd_bruta, stake_n, cashout) -> tuple[str, str]:
    """Devolve (resultado, odd). Cashout segue MASTER_RESULTADO §5.1.2 / §5.6."""
    s = limpa(status).lower()
    odd_n = _para_float(odd_bruta)
    if s == 'cashout':
        c = _para_float(cashout)
        if c is None or not stake_n:
            return '', _float_str(odd_n) if odd_n else ''
        if abs(c - stake_n) < 0.005:                    # cashout = stake → V
            return 'V', _float_str(odd_n) if odd_n else ''
        return 'W', _float_str(c / stake_n)             # cashout ≠ stake → W
    return _STATUS.get(s, ''), (_float_str(odd_n) if odd_n else '')


def norm_data(v) -> str:
    s = limpa(v)
    if isinstance(v, dt.datetime):
        return v.strftime('%d/%m/%Y')
    return s.split(' ')[0]


# ---------- carga ----------
COLS = ['Data de cadastro', 'Data do jogo', 'Tipo de Aposta', 'Esporte', 'Evento',
        'Aposta', 'Mercado', 'Odd', 'Valor apostado', 'Status', 'Casa de apostas',
        'Tipster', 'Torneio', 'País', 'Cashout']


def carregar_rows(xlsx_path: str) -> list[dict]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    brutas = list(ws.iter_rows(values_only=True))
    hdr = [limpa(h) for h in brutas[0]]
    faltando = [c for c in COLS if c not in hdr]
    if faltando:
        raise SystemExit(f'colunas ausentes no export: {faltando} — header: {hdr}')
    I = {h: i for i, h in enumerate(hdr)}
    out = []
    for r in brutas[1:]:
        if not any(r):
            continue
        mercado, ap, ev = limpa(r[I['Mercado']]), limpa(r[I['Aposta']]), limpa(r[I['Evento']])
        esp = esporte_final(r[I['Esporte']], ev, limpa(r[I['Torneio']]), mercado, ap)
        combo = eh_combo(r[I['Tipo de Aposta']], mercado, ap)
        stake_n = _para_float(r[I['Valor apostado']]) or 0.0
        res, odd = resultado_e_odd(r[I['Status']], r[I['Odd']], stake_n, r[I['Cashout']])
        out.append({
            'data': norm_data(r[I['Data do jogo']]),
            'esporte': esp,
            'tipster': norm_tipster(r[I['Tipster']]),
            'casa': norm_casa(r[I['Casa de apostas']]),
            'parceiro': PARCEIRO,
            'aposta': categoria(mercado, ap, esp, combo),
            'descricao': descricao(ap, ev),
            'stake': f'{stake_n:.2f}'.replace('.', ','),
            'odd': odd,
            'resultado': res,
            '_mercado': mercado,          # só para o relatório do DRY
            '_status': limpa(r[I['Status']]),
        })
    return out


# ---------- assinatura (idêntica a repository._assinatura) ----------
# ATENÇÃO: `stake` ENTRA no hash. Não copiar `import_lava.py` /
# `import_dashboard_xlsx.py` (versão pré-s133, sem stake).
def _norm_odd_sig(v: str) -> str:
    try:
        return f"{round(float(v.replace(',', '.')), 2):.2f}"
    except (ValueError, AttributeError):
        return v


def assinaturas(rows: list[dict]) -> list[str]:
    counts: dict[str, int] = {}
    sigs = []
    for r in rows:
        base_raw = "|".join([
            r['casa'], r['parceiro'], r['data'], r['aposta'], r['descricao'],
            r['stake'], _norm_odd_sig(r['odd']),
        ])
        base_sig = hashlib.sha256(base_raw.encode()).hexdigest()[:20]
        cnt = counts.get(base_sig, 0) + 1
        counts[base_sig] = cnt
        raw = base_raw if cnt == 1 else f"{base_raw}|{cnt}"
        sigs.append(hashlib.sha256(raw.encode()).hexdigest()[:20])
    return sigs


def estado_extracao(resultado: str, odd: str) -> str:
    if resultado not in VALID:
        return 'aberta'
    return 'resolvida' if (_para_float(odd) or 0) > 0 else 'aberta'


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
    casas = sorted({r['casa'] for r in rows})

    registros = [(
        DONO, r['casa'], r['parceiro'], sig, None,
        r['data'], r['esporte'], r['tipster'], r['aposta'], r['descricao'],
        r['stake'], r['odd'], r['resultado'] or None,
        estado_extracao(r['resultado'], r['odd']),
        None, None, ORIGEM,
    ) for r, sig in zip(rows, sigs)]

    last_err = None
    for tentativa in range(1, 4):
        try:
            conn = await asyncpg.connect(url, command_timeout=180)
            try:
                async with conn.transaction():
                    # idempotente: reimportar não acumula. Limpa SÓ o que este
                    # import escreveu — captura da extensão tem outra origem.
                    apagadas = await conn.execute(
                        "DELETE FROM bilhetes WHERE dono=$1 AND origem=$2", DONO, ORIGEM)
                    print(f'  [tentativa {tentativa}] limpou import anterior: {apagadas}')
                    await conn.executemany(
                        """
                        INSERT INTO bilhetes
                            (dono, casa, parceiro, assinatura, codigo_bilhete, data, esporte,
                             tipster, aposta, descricao, stake, odd, resultado,
                             extraction_state, confianca, stake_usd, origem)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
                        ON CONFLICT (dono, casa, parceiro, assinatura) DO NOTHING
                        """, registros)
                    for casa in casas:
                        await conn.execute(
                            """INSERT INTO parceiros (dono, casa, nome) VALUES ($1,$2,$3)
                               ON CONFLICT (dono, casa, nome) DO NOTHING""",
                            DONO, casa, PARCEIRO)
                    # feed ordena por criado_em DESC; num import não existe
                    # "envio" → ancora na data da aposta para sair cronológico
                    await conn.execute(
                        """
                        WITH ordered AS (
                            SELECT id,
                                   ROW_NUMBER() OVER (ORDER BY to_date(data,'DD/MM/YYYY') ASC,
                                                               id ASC) AS rn,
                                   COUNT(*) OVER () AS total
                            FROM bilhetes WHERE dono=$1 AND origem=$2
                        )
                        UPDATE bilhetes b
                        SET criado_em = NOW() - ((o.total - o.rn) * INTERVAL '1 second')
                        FROM ordered o WHERE b.id = o.id
                        """, DONO, ORIGEM)
                n = await conn.fetchval("SELECT COUNT(*) FROM bilhetes WHERE dono=$1", DONO)
                nc = await conn.fetchval(
                    "SELECT COUNT(DISTINCT casa) FROM parceiros WHERE dono=$1", DONO)
                np = await conn.fetchval("SELECT COUNT(*) FROM parceiros WHERE dono=$1", DONO)
                print(f'\nOK — bilhetes dono={DONO}={n} | casas={nc} | contas={np}')
                return
            finally:
                await conn.close()
        except Exception as e:                       # noqa: proxy instável → retry
            last_err = e
            print(f'  [tentativa {tentativa}] falhou: {type(e).__name__}: {e}')
    raise SystemExit(f'import falhou após 3 tentativas: {last_err}')


# ---------- relatório do DRY ----------
def _pl(stake: str, odd: str, res: str):
    s = _para_float(stake) or 0.0
    o = _para_float(odd)
    if res == 'L':
        return -s
    if res == 'V':
        return 0.0
    if o is None or o <= 0:
        return None
    if res == 'W':
        return s * (o - 1)
    if res == 'HW':
        return s * (o - 1) / 2
    if res == 'HL':
        return -s / 2
    return None


def _relatorio(rows: list[dict]):
    print(f'DONO={DONO} | conta={PARCEIRO!r} (sem fornecedor) | linhas: {len(rows)}')
    datas = sorted(dt.datetime.strptime(r['data'], '%d/%m/%Y') for r in rows)
    print(f'período: {datas[0]:%d/%m/%Y} → {datas[-1]:%d/%m/%Y}')

    for campo in ('casa', 'esporte', 'aposta'):
        print(f'\n{campo} ({len(set(r[campo] for r in rows))}):',
              dict(Counter(r[campo] for r in rows).most_common()))
    print(f'\ntipster ({len(set(r["tipster"] for r in rows))}):',
          dict(Counter(r['tipster'] for r in rows).most_common(20)))
    print('\nresultado:',
          dict(Counter(r['resultado'] or '(aberta)' for r in rows).most_common()))

    sigs = assinaturas(rows)
    print(f'\nassinaturas: {len(set(sigs))} únicas de {len(sigs)} '
          f'({len(sigs) - len(set(sigs))} desambiguadas por contador)')
    print('extraction_state:',
          dict(Counter(estado_extracao(r['resultado'], r['odd']) for r in rows)))

    outros = [r for r in rows if r['aposta'] == 'Outros']
    if outros:
        print(f'\n⚠ {len(outros)} linha(s) em `Outros` — mercados não classificados:')
        for k, c in Counter(r['_mercado'] for r in outros).most_common(20):
            print(f'    {c:4d}  {k!r}')

    outro_esp = [r for r in rows if r['esporte'] in ('Outro', '')]
    if outro_esp:
        print(f'\n⚠ {len(outro_esp)} linha(s) com esporte `Outro`:')
        for r in outro_esp[:12]:
            print(f'    {r["descricao"][:70]}  |  {r["_mercado"][:40]}')

    sem_odd = [r for r in rows if not r['odd']]
    if sem_odd:
        print(f'\n⚠ {len(sem_odd)} linha(s) sem odd (ficam abertas)')
    sem_stake = [r for r in rows if (_para_float(r['stake']) or 0) <= 0]
    if sem_stake:
        print(f'⚠ {len(sem_stake)} linha(s) com stake 0 (invisíveis no dashboard)')

    turnover = sum(_para_float(r['stake']) or 0 for r in rows)
    pl = sum(v for r in rows if (v := _pl(r['stake'], r['odd'], r['resultado'])) is not None)
    print(f'\nturnover:     R$ {turnover:>13,.2f}')
    print(f'P/L derivado: R$ {pl:>13,.2f}   (ROI {pl / turnover * 100:.2f}%)')

    print('\n=== 18 AMOSTRAS (Data|Esporte|Tipster|Casa|Conta|Aposta|Descrição|Stake|Odd|Res) ===')
    step = max(1, len(rows) // 18)
    for r in rows[::step][:18]:
        print(' | '.join([r['data'], r['esporte'], r['tipster'], r['casa'], r['parceiro'],
                          r['aposta'], r['descricao'][:60], r['stake'], r['odd'],
                          r['resultado'] or '—']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', required=True)
    ap.add_argument('--go', action='store_true')
    args = ap.parse_args()
    rows = carregar_rows(args.xlsx)
    _relatorio(rows)
    if not args.go:
        print('\n[DRY] nada escrito. Rode com --go para importar.')
        return
    for r in rows:
        r.pop('_mercado', None)
        r.pop('_status', None)
    carregar_env()
    asyncio.run(importar(rows))


if __name__ == '__main__':
    main()
