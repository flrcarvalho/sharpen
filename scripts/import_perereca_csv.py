# -*- coding: utf-8 -*-
"""Importa a base do usuário `perereca` (bets.csv) para dono='perereca'.

O `dono` é o USERNAME, conferido na tabela `usuarios` antes do import — não o nome
do arquivo nem um apelido (regra da s260: `dono` errado não dá erro, dá tela vazia).
Medido em 14/08/2026: `perereca` · status `ativo` · hash de 60 chars · criado pelo
PRÓPRIO usuário no site (Fase 2 do onboarding), aprovado pelo Feca. Base ZERADA
(0 bilhetes) — este é o primeiro import.

── Fonte ─────────────────────────────────────────────────────────────────────

CSV com `;`, 17 colunas, 746 linhas (10/05/2026 → 14/08/2026):

    DESPORTO | LIGA | EVENTO | HORA | APOSTA | BOOKMAKER | STAKE | MOEDA | ODDS |
    EV | CLV | ODDS JUSTAS | ODDS JUSTAS ATUAIS | PERFIL | ESTADO |
    DATA DA APOSTA | NOTAS

É um tracker de **valuebet**, não de tipster: traz EV, CLV e odds justas (pré e
atuais) por aposta. Todas as 746 são SIMPLES — nenhuma múltipla, nenhum bet
builder (medido: 100% dos eventos têm exatamente um ` vs `).

**Quatro colunas não têm destino no schema e se perdem:** `EV`, `CLV`,
`ODDS JUSTAS` e `ODDS JUSTAS ATUAIS`. O banco não tem coluna para odd justa nem
para CLV. Fica registrado porque CLV é justamente uma frente aberta do produto —
se um dia existir coluna, a fonte para backfill é este mesmo arquivo.

── Decisões (confirmadas pelo Feca, 14/08/2026) ──────────────────────────────

- **Tipster VAZIO.** A coluna `PERFIL` está vazia nas 746 linhas; a base é de
  valuebet própria. Inventar um nome criaria um tipster que não existe.
- **Cashout → `V`.** 4 linhas (R$530 de stake) vêm com `ESTADO=cashout` e a odd
  SOBRESCRITA por `1.0` — o tracker descartou a odd contratada e nunca gravou o
  valor do cashout (as `ODDS JUSTAS` dessas linhas, 1.736–2.279, provam que a odd
  real não era 1.0). Odd 1.0 = retorno igual à stake, que é exatamente o caso
  `MASTER_RESULTADO §5.1.2` (cashout = stake → `V`, P/L 0). É a leitura LITERAL
  do que o arquivo afirma, não um palpite sobre o cashout real. As 4 saem listadas
  no relatório para correção manual no editor, se ele souber os valores.
- **`data` = `DATA DA APOSTA`**, nunca a `HORA` do evento. É o que a captura da
  bet365 grava (data de colocação do bilhete), então o histórico importado fica
  na mesma régua do que ele capturar daqui pra frente. Os dois divergem de verdade:
  aposta feita 14/08 às 15:01 para evento de 15/08 às 07:00.
- **Uma conta `Padrão` por casa** — 5 linhas no Painel de Contas, cada uma com
  custo próprio (mesmo desenho do `import_reidocriquete_xlsx.py`).
- **Stake em REAIS** (`MOEDA=BRL` nas 746, R$10–380). Diferente dos imports de
  tipster (SóChutes/Fleury/RC), que são em unidades.
- **Dono solo** — sem `OPERADORES`, sem dedup cruzada.

── Casa: grafia do banco, nunca a do arquivo ─────────────────────────────────

`casa` é TEXTO em 7 tabelas — cada grafia é uma casa DIFERENTE no sistema. As 5
grafias abaixo foram MEDIDAS no banco, não supostas:

    Bet365 49.467 · Betano 11.181 · Betfair 2.159 · Betnacional 540 · Stake 37

O arquivo escreve `bet365`, `BetNacional`, `betfair` e `Stake (BR)`. Importar
verbatim criaria 4 casas paralelas. Casa DESCONHECIDA (nenhuma aqui) entraria
verbatim — nunca title-casear, que mutila `BETesporte`/`VaideBet`/`KingPanda`.

── Resultado ─────────────────────────────────────────────────────────────────

    won 287 → W    lost 411 → L    void 26 → V    push 11 → V
    half-lost 1 → HL              cashout 4 → V   pending 6 → (aberta)

`push` é o handicap asiático que fecha na linha: stake devolvido, P/L 0 = `V`.
`pending` vira resultado VAZIO (aposta em aberto, `MASTER_OUTPUT §13.1`).
Não há `half-won` no arquivo.

── Esporte ───────────────────────────────────────────────────────────────────

Os 10 valores vêm em inglês minúsculo e mapeiam para o canônico do
`MASTER_ESPORTES §7`. `table tennis` → `Tênis de Mesa` é NÃO-CANÔNICO (não está
nos 21 do MASTER) e entra na grafia que o sistema já conhece — mesmo precedente
do `import_reidocriquete_xlsx.py`: a base preserva grafia herdada de import e a
rota `/taxonomia` serve a UNIÃO do canônico com a base do dono.

── Categoria: o objeto apostado, não o tipo de mercado ───────────────────────

61 rótulos distintos de mercado. O segmento inicial (`1o Set - `, `1a Parte - `,
`4o Quarto - `) é DESCARTADO antes de classificar e reaparece só na descrição:
`MASTER_APOSTAS §1` — over/under, handicap e período não mudam a categoria.

Dois cortes que não são óbvios e vêm do MASTER, medidos linha a linha:

- **`Corridas de Jogador` (12) e `RBIs de Jogador` (9) → `Corridas`**, não
  `Player Props`. É o `§6 Baseball` explícito ("Corridas e RBIs → Corridas").
  Todas as 21 são baseball (medido). Os demais props de baseball — strikeouts,
  home runs, bases, hits, outs — seguem `Player Props` pela mesma seção.
- **`Handicap Asiático de Cartões` → `Cartões`**, não `Handicap`. O objeto
  apostado é o cartão; o handicap é só a forma do mercado (§1).

`Total Aces` (total do match) e `Aces da Equipa` (aces de um jogador) vão os dois
para `Player Props` — o `§6 Tênis` lista aces como estatística individual e não
existe categoria de objeto para ace. `Jogos de Equipa` (games de um lado) fica em
`Games`: o objeto é o game, igual ao total do match.

── Dedup: o CSV NÃO tem ID de bilhete ────────────────────────────────────────

Sem código, `repository._assinatura` hasheia CONTEÚDO
(`casa|parceiro|data|aposta|descricao|stake|odd`). Consequência a declarar:

⚠️ Se o `perereca` instalar a extensão e capturar a bet365, as apostas recentes
   voltam COM código real. Assinatura por ID nunca colide com assinatura por
   conteúdo → **não deduplica, duplica**. São 65 linhas nos últimos 2 dias e 117
   nos últimos 7. Não há como evitar pelo import; a saída é deletar as
   sobrepostas pelo Painel, ou capturar ANTES de importar.

Linhas de conteúdo 100% idêntico dentro do próprio CSV escalam com `_counter`
(`B`, `B|2`, …) em vez de colidir — mesmo laço do `upsert_bilhetes`.

Uso:
    python scripts/import_perereca_csv.py --csv "C:\\...\\bets.csv"        # DRY
    python scripts/import_perereca_csv.py --csv "C:\\...\\bets.csv" --go   # escreve
"""
import argparse
import asyncio
import csv
import datetime as dt
import hashlib
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
DONO = 'perereca'        # username conferido em `usuarios`, não deduzido do arquivo
PARCEIRO = 'Padrão'
TIPSTER = ''             # PERFIL vazio nas 746 — não inventar tipster
ORIGEM = 'import'
VALID = {'W', 'L', 'V', 'HW', 'HL'}


# ---------- sanitização ----------
_CTRL = re.compile(r'[\x00-\x1f\x7f]+')
# Marcas de formatação invisíveis (Cf): zero-width, LTR/RTL mark, BOM. Chegam
# coladas em nome próprio vindo de scraping (`Nicolle Caliari‎`) e são
# INVISÍVEIS na tela — mas entram no hash da assinatura, então o mesmo nome com
# e sem a marca vira bilhete diferente na dedup.
_INVIS = re.compile(r'[​-‏‪-‮⁠-⁤﻿]')


def limpa(v) -> str:
    if v is None:
        return ''
    return re.sub(r'\s{2,}', ' ', _CTRL.sub(' ', _INVIS.sub('', str(v)))).strip()


def _chave(s: str) -> str:
    s = unicodedata.normalize('NFKD', limpa(s))
    return ''.join(c for c in s if not unicodedata.combining(c)).lower().replace(' ', '')


# ---------- casa ----------
# Grafias MEDIDAS no banco (14/08/2026). Casa fora do mapa entra verbatim.
_CASA_MAP = {
    'bet365': 'Bet365',
    'betano': 'Betano',
    'betnacional': 'Betnacional',
    'betfair': 'Betfair',
    'stake(br)': 'Stake',
    'stake': 'Stake',
}


def norm_casa(v) -> str:
    bruto = limpa(v)
    return _CASA_MAP.get(_chave(bruto), bruto)


# ---------- esporte ----------
_ESPORTE_MAP = {
    'tennis': 'Tênis',
    'basketball': 'Basquete',
    'baseball': 'Baseball',
    'soccer': 'Futebol',
    'rugby': 'Rugby',
    'americanfootball': 'Futebol Americano',
    'mma': 'MMA',
    'handball': 'Handebol',
    'icehockey': 'Hóquei',
    'tabletennis': 'Tênis de Mesa',   # NÃO-CANÔNICO (grafia já usada no sistema)
}
NAO_CANONICOS = {'Tênis de Mesa'}


def norm_esporte(v) -> str:
    return _ESPORTE_MAP.get(_chave(v), limpa(v) or 'Outro')


# ---------- segmento (período) ----------
# Prefixo de período do rótulo da casa (pt-PT). Sai da categoria e vai para a
# descrição — `MASTER_APOSTAS §1`: o período não altera o objeto apostado.
_SEGMENTOS = {
    '1o set': '1º Set',
    '2o set': '2º Set',
    '1a parte': '1º Tempo',      # grafia dominante no banco (15.363 descrições)
    '1o quarto': '1º Quarto',
    '4o quarto': '4º Quarto',
    '1o período': '1º Período',
    '1o jogo': '1º Game',        # tênis de mesa: "jogo" (pt-PT) = game
}


def parte_segmento(prefixo: str):
    """`1o Set - Vencedor` → (`1º Set`, `Vencedor`)."""
    if ' - ' in prefixo:
        seg, resto = prefixo.split(' - ', 1)
        canon = _SEGMENTOS.get(_chave(seg).replace('o', 'o'), None)
        if canon is None:
            canon = _SEGMENTOS.get(seg.strip().lower())
        if canon:
            return canon, resto.strip()
    return '', prefixo.strip()


# ---------- categoria ----------
# Rótulo do mercado (já sem o segmento) → categoria do `MASTER_APOSTAS §3`.
_CAT = {
    'vencedor': 'ML',
    'apostasemempate': 'DNB',
    'duplahipotese': 'Dupla Chance',
    'ambasmarcam': 'Ambas Marcam',
    'handicapasiatico': 'Handicap',
    'handicapeuropeu': 'Handicap',
    'handicapasiaticodejogos': 'Handicap',
    'handicapasiaticodecartoes': 'Cartões',      # objeto = cartão, não o handicap
    'totaldejogos': 'Games',
    'jogosdeequipa': 'Games',                    # games de um lado; objeto = game
    'totaldepontos': 'Pontos',
    'pontosdaequipa': 'Pontos',
    'totaldegolos': 'Gols',
    'golosdaequipa': 'Gols',
    'totaldecartoes': 'Cartões',
    'cartoesdeequipa': 'Cartões',
    'totaldecantos': 'Escanteios',               # pt-PT: canto = escanteio
    'cantosdaequipa': 'Escanteios',
    'totalderondas': 'Rounds',                   # pt-PT: ronda = round (MMA/Boxe)
    'totalderemat esenquadrados': 'Chutes no Gol',
    'totalderematesenquadrados': 'Chutes no Gol',  # pt-PT: remate enquadrado = SOT
    'rematesenquadradosdaequipa': 'Chutes no Gol',
    'triesdeequipa': 'Team Props',               # rugby: sem categoria de objeto
    'hitsdeequipa': 'Team Props',
    'totalaces': 'Player Props',                 # §6 Tênis lista aces como individual
    'acesdaequipa': 'Player Props',
    # Baseball — §6 explícito: Corridas e RBIs têm categoria própria.
    'corridasdejogador': 'Corridas',
    'rbisdejogador': 'Corridas',
}


def norm_categoria(mercado: str) -> str:
    k = _chave(mercado)
    if k in _CAT:
        return _CAT[k]
    # Qualquer outra estatística individual (`... de/do Jogador`) → Player Props.
    if re.search(r'\bd[eo]s?\s+jogador\b', mercado, re.I):
        return 'Player Props'
    return 'Outros'


# ---------- descrição ----------
_OU = re.compile(r'^(.*?)\s*\b(Mais de|Menos de)\s+([\d.,]+)$', re.I)
_HCP = re.compile(r'^(.*?)\s*([+-]\d+(?:[.,]\d+)?)$')

# Objeto que acompanha a linha na descrição, por categoria (§10.1: `Over X.5 Mercado`).
_OBJ = {
    'Games': 'Games',
    'Pontos': 'Pontos',
    'Gols': 'Gols',
    'Cartões': 'Cartões',
    'Escanteios': 'Escanteios',
    'Chutes no Gol': 'Chutes no Gol',
    'Corridas': 'Corridas',
    'Sets': 'Sets',
    'Rounds': 'Rounds',    # `Total de Rondas` → `Under 2.5 Rounds` (§12.5)
}

# Rótulo do objeto para Player Props / Team Props: vem do próprio mercado, sem o
# sufixo "de Jogador"/"da Equipa", que já está implícito na entidade.
_STRIP_ENT = re.compile(
    r'\s*(?:de|do|dos|da|das)\s+(?:jogador|equipa)\b.*$', re.I)


def _objeto(categoria: str, mercado: str) -> str:
    if categoria in _OBJ:
        return _OBJ[categoria]
    base = _STRIP_ENT.sub('', mercado).strip()
    base = re.sub(r'^Total\s+(?:de\s+)?', '', base, flags=re.I).strip()
    return base


def _conf(evento: str) -> str:
    """`A vs B` → `[A v B]` (§4/§5: separador é `v`, nunca `vs`)."""
    ev = limpa(evento)
    if ' vs ' in ev:
        a, b = ev.split(' vs ', 1)
        return f'[{a.strip()} v {b.strip()}]'
    return f'[{ev}]' if ev else ''


def _num(s: str) -> str:
    """Linha da aposta: mantém o ponto decimal (padrão da descrição no banco)."""
    return limpa(s).replace(',', '.')


def _dupla_chance(alvo: str, evento: str) -> str:
    """`Lokomotiv Oslo ou Empate` + `A vs B` → `1X`/`X2`/`12` (§12.9 obriga o símbolo)."""
    ev = limpa(evento)
    casa, fora = (ev.split(' vs ', 1) + [''])[:2] if ' vs ' in ev else ('', '')
    partes = [p.strip() for p in re.split(r'\s+ou\s+', alvo, flags=re.I)]
    tem_empate = any(_chave(p) == 'empate' for p in partes)
    times = [p for p in partes if _chave(p) != 'empate']
    if not tem_empate:
        return '12'
    if times and _chave(times[0]) == _chave(casa):
        return '1X'
    if times and _chave(times[0]) == _chave(fora):
        return 'X2'
    return alvo  # não casou com nenhum lado: preserva o texto, nunca chuta o símbolo


def norm_descricao(aposta: str, evento: str, categoria: str,
                   segmento: str, mercado: str) -> str:
    conf = _conf(evento)
    alvo = aposta.split(':', 1)[1].strip() if ':' in aposta else ''
    seg = f' {segmento}' if segmento else ''

    if categoria == 'Dupla Chance':
        return f'{_dupla_chance(alvo, evento)}{seg} {conf}'.strip()

    m = _OU.match(alvo)
    if m:                                   # Over / Under (§10.1 + §11)
        ent, direcao, linha = m.group(1).strip(), m.group(2), _num(m.group(3))
        ou = 'Over' if direcao.lower() == 'mais de' else 'Under'
        obj = _objeto(categoria, mercado)
        corpo = f'{ou} {linha} {obj}'.strip()
        # §12.3 Player Props / Team Props: `Jogador - Linha Mercado [Confronto]`
        # §12.5 Totais do jogo:            `Mercado [Confronto]`
        return f'{ent} - {corpo}{seg} {conf}'.strip() if ent else f'{corpo}{seg} {conf}'.strip()

    m = _HCP.match(alvo)
    if m:                                   # §12.6 Handicap: `Entidade Linha [Confronto]`
        ent, linha = m.group(1).strip(), m.group(2).replace(',', '.')
        obj = _objeto(categoria, mercado) if categoria in ('Games', 'Cartões') else ''
        corpo = f'{ent} {linha}' + (f' {obj}' if obj else '')
        return f'{corpo}{seg} {conf}'.strip()

    # Texto puro. ML/DNB (§12.7): `Entidade [Confronto]`. Ambas Marcam: `Sim`/`Não`.
    if not alvo:
        return f'{mercado}{seg} {conf}'.strip()
    if segmento:
        # o segmento é o mercado aqui — `Kokkinakis - Vencedor 1º Set [A v B]`
        return f'{alvo} - {mercado}{seg} {conf}'.strip()
    return f'{alvo} {conf}'.strip()


# ---------- resultado ----------
_RES = {
    'won': 'W',
    'lost': 'L',
    'void': 'V',
    'push': 'V',        # handicap asiático na linha: stake devolvido
    'cashout': 'V',     # odd sobrescrita por 1.0 → retorno = stake (§5.1.2)
    'half-lost': 'HL',
    'half-won': 'HW',   # não ocorre no arquivo; mapeado por segurança
    'pending': '',      # aberta — resultado VAZIO (§13.1)
}


# ---------- números ----------
def _para_float(v):
    try:
        return float(str(v).replace(',', '.'))
    except (TypeError, ValueError):
        return None


def fmt_stake(v) -> str:
    f = _para_float(v)
    return '' if f is None else f'{f:.2f}'.replace('.', ',')


def fmt_odd(v) -> str:
    """Odd com PRECISÃO COMPLETA — nunca truncar (só o display encurta)."""
    s = limpa(v).replace(',', '.')
    f = _para_float(s)
    if f is None:
        return ''
    s = s.rstrip('0').rstrip('.') if '.' in s else s
    return s.replace('.', ',')


def fmt_data(v) -> str:
    """`14/08/2026 15:01` → `14/08/2026`."""
    return limpa(v).split(' ')[0]


def estado_extracao(resultado: str, odd: str) -> str:
    """Espelha repository.estado_extracao: desde a s259 a odd só é exigida onde o
    P/L depende dela (W/HW); L/V/HL nascem `resolvida`."""
    if resultado not in VALID:
        return 'aberta'
    if resultado in ('W', 'HW'):
        return 'resolvida' if (_para_float(odd) or 0) > 0 else 'aberta'
    return 'resolvida'


def assinatura(r: dict, _counter: int = 1) -> str:
    """Espelha `repository._assinatura` SEM código: o hash é de CONTEÚDO.
    A ordem dos campos é a do repository — mudá-la invalida a dedup."""
    raw = '|'.join([r['casa'], r['parceiro'], r['data'], r['aposta'],
                    r['descricao'], r['stake'], r['odd']])
    if _counter > 1:
        raw += f'|{_counter}'
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


# ---------- leitura ----------
def ler(caminho: str) -> list[dict]:
    with open(caminho, encoding='utf-8-sig', newline='') as fh:
        brutas = list(csv.DictReader(fh, delimiter=';'))
    if not brutas:
        raise SystemExit('CSV vazio')

    faltando = {'DESPORTO', 'EVENTO', 'APOSTA', 'BOOKMAKER', 'STAKE', 'MOEDA',
                'ODDS', 'ESTADO', 'DATA DA APOSTA'} - set(brutas[0])
    if faltando:
        raise SystemExit(f'colunas ausentes no CSV: {sorted(faltando)}')

    moedas = {limpa(b['MOEDA']) for b in brutas}
    if moedas != {'BRL'}:
        # stake em moeda mista exigiria conversão por data — não é este arquivo.
        raise SystemExit(f'esperado só BRL, veio {sorted(moedas)} — abortado')

    rows, avisos = [], []
    for i, b in enumerate(brutas, start=2):
        estado = _chave(b['ESTADO']).replace('-', '')
        estado_raw = limpa(b['ESTADO']).lower()
        if estado_raw not in _RES:
            raise SystemExit(f'linha {i}: ESTADO desconhecido {estado_raw!r}')

        prefixo = limpa(b['APOSTA']).split(':', 1)[0]
        segmento, mercado = parte_segmento(prefixo)
        categoria = norm_categoria(mercado)
        resultado = _RES[estado_raw]
        esporte = norm_esporte(b['DESPORTO'])

        r = {
            'linha': i,
            'casa': norm_casa(b['BOOKMAKER']),
            'parceiro': PARCEIRO,
            'data': fmt_data(b['DATA DA APOSTA']),
            'esporte': esporte,
            'tipster': TIPSTER,
            'aposta': categoria,
            'descricao': norm_descricao(limpa(b['APOSTA']), b['EVENTO'],
                                        categoria, segmento, mercado),
            'stake': fmt_stake(b['STAKE']),
            'odd': fmt_odd(b['ODDS']),
            'resultado': resultado,
            '_estado': estado_raw,
            '_mercado': mercado,
            '_segmento': segmento,
            '_liga': limpa(b['LIGA']),
            '_evento': limpa(b['EVENTO']),
            '_aposta_txt': limpa(b['APOSTA']),
            '_dt': dt.datetime.strptime(limpa(b['DATA DA APOSTA']), '%d/%m/%Y %H:%M'),
        }
        if categoria == 'Outros':
            avisos.append((i, prefixo, r['descricao']))
        rows.append(r)

    # Conteúdo idêntico escala com `_counter` em vez de colidir (mesma regra do
    # `upsert_bilhetes`): duas apostas reais iguais não podem virar uma só.
    vistos = defaultdict(int)
    for r in rows:
        base = assinatura(r)
        vistos[base] += 1
        r['assinatura'] = assinatura(r, _counter=vistos[base])
        r['_colidiu'] = vistos[base] > 1

    return rows, avisos


# ---------- relatório do DRY ----------
def _pl(r: dict):
    s = _para_float(r['stake']) or 0.0
    o = _para_float(r['odd'])
    res = r['resultado']
    if res == 'L':
        return -s
    if res == 'V':
        return 0.0
    if res == 'HL':
        return -s / 2
    if o is None:
        return None
    if res == 'W':
        return s * (o - 1)
    if res == 'HW':
        return s * (o - 1) / 2
    return None


def relatorio(rows: list[dict], avisos: list):
    print(f'DONO={DONO} | tipster={TIPSTER!r} (vazio) | conta={PARCEIRO!r} por casa '
          f'| linhas: {len(rows)}')
    datas = sorted(r['_dt'] for r in rows)
    print(f'período: {datas[0]:%d/%m/%Y} → {datas[-1]:%d/%m/%Y}')

    print('\n— casa (grafia do banco) —')
    for k, v in Counter(r['casa'] for r in rows).most_common():
        print(f'  {k:<14} {v:>4}')

    print('\n— esporte —')
    for k, v in Counter(r['esporte'] for r in rows).most_common():
        flag = '  ⚠️ NÃO-CANÔNICO' if k in NAO_CANONICOS else ''
        print(f'  {k:<20} {v:>4}{flag}')

    print('\n— categoria —')
    for k, v in Counter(r['aposta'] for r in rows).most_common():
        print(f'  {k:<16} {v:>4}')

    print('\n— resultado —')
    for k, v in Counter(r['resultado'] or '(aberta)' for r in rows).most_common():
        print(f'  {k:<10} {v:>4}')

    liq = [r for r in rows if r['resultado']]
    turn = sum(_para_float(r['stake']) or 0 for r in liq)
    pl = sum(_pl(r) or 0 for r in liq)
    print(f'\n— P/L —\n  liquidadas {len(liq)} | turnover R$ {turn:,.2f} '
          f'| P/L R$ {pl:,.2f} | ROI {pl / turn * 100:.2f}%')

    if avisos:
        print(f'\n⚠️ {len(avisos)} linha(s) em `Outros` (mercado sem categoria):')
        for i, pref, desc in avisos[:15]:
            print(f'  L{i:<4} {pref:<34} {desc[:60]}')

    colidiu = [r for r in rows if r['_colidiu']]
    if colidiu:
        print(f'\n⚠️ {len(colidiu)} linha(s) de conteúdo idêntico (escalam com _counter):')
        for r in colidiu[:8]:
            print(f'  L{r["linha"]:<4} {r["data"]} {r["casa"]:<12} {r["descricao"][:58]}')

    cash = [r for r in rows if r['_estado'] == 'cashout']
    if cash:
        print(f'\n⚠️ {len(cash)} cashout → V (odd real perdida na fonte; corrigir no editor):')
        for r in cash:
            print(f'  L{r["linha"]:<4} {r["data"]} stake {r["stake"]:>8} | {r["descricao"][:58]}')

    hoje = datas[-1]
    for dias in (2, 7):
        n = sum(1 for r in rows if r['_dt'] >= hoje - dt.timedelta(days=dias))
        print(f'\n⚠️ {n} linha(s) nos últimos {dias}d — recaptura pela extensão DUPLICA '
              f'(CSV sem ID de bilhete)' if dias == 2 else
              f'   {n} linha(s) nos últimos {dias}d')

    print('\n— amostra (10 primeiras) —')
    for r in rows[:10]:
        print(f'  {r["data"]} | {r["casa"]:<12} | {r["esporte"]:<10} | '
              f'{r["aposta"]:<14} | {r["stake"]:>8} @ {r["odd"]:<8} | '
              f'{r["resultado"] or "-":<2} | {r["descricao"][:70]}')

    print('\n— amostra por categoria (1 de cada) —')
    vistos = set()
    for r in rows:
        if r['aposta'] in vistos:
            continue
        vistos.add(r['aposta'])
        print(f'  {r["aposta"]:<14} | {r["_aposta_txt"][:44]:<44} → {r["descricao"][:66]}')


# ---------- escrita ----------
def carregar_env():
    for line in open(ENV_PATH, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def importar(rows: list[dict]):
    import asyncpg
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    casas = sorted({r['casa'] for r in rows})

    registros = [(
        DONO, r['casa'], r['parceiro'], r['assinatura'], None,
        r['data'], r['esporte'], r['tipster'], r['aposta'], r['descricao'],
        r['stake'], r['odd'], r['resultado'] or None,
        estado_extracao(r['resultado'], r['odd']),
        None, None, ORIGEM,
    ) for r in rows]

    last_err = None
    for tentativa in range(1, 4):
        try:
            conn = await asyncpg.connect(url, command_timeout=120)
            try:
                async with conn.transaction():
                    # idempotente: reimportar não acumula. Limpa SÓ o que este
                    # import escreveu — captura da extensão tem outra origem.
                    apagadas = await conn.execute(
                        'DELETE FROM bilhetes WHERE dono=$1 AND origem=$2', DONO, ORIGEM)
                    print(f'  [tentativa {tentativa}] limpou import anterior: {apagadas}')
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
                    for casa in casas:
                        await conn.execute(
                            """INSERT INTO parceiros (dono, casa, nome) VALUES ($1,$2,$3)
                               ON CONFLICT (dono, casa, nome) DO NOTHING""",
                            DONO, casa, PARCEIRO)
                    # feed ordena por criado_em DESC; num import não existe "envio"
                    # → ancora na data da aposta para sair cronológico
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
                n = await conn.fetchval('SELECT COUNT(*) FROM bilhetes WHERE dono=$1', DONO)
                nc = await conn.fetchval(
                    'SELECT COUNT(DISTINCT casa) FROM parceiros WHERE dono=$1', DONO)
                np = await conn.fetchval('SELECT COUNT(*) FROM parceiros WHERE dono=$1', DONO)
                print(f'\nOK — bilhetes dono={DONO}={n} | casas={nc} | contas={np}')
                return
            finally:
                await conn.close()
        except Exception as e:                       # noqa: proxy instável → retry
            last_err = e
            print(f'  [tentativa {tentativa}] falhou: {type(e).__name__}: {e}')
    raise SystemExit(f'import falhou após 3 tentativas: {last_err}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--go', action='store_true', help='escreve no banco (sem isto = DRY)')
    a = ap.parse_args()

    rows, avisos = ler(a.csv)
    relatorio(rows, avisos)

    if not a.go:
        print('\n(DRY — nada foi escrito. Use --go para gravar.)')
        return
    carregar_env()
    asyncio.run(importar(rows))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
