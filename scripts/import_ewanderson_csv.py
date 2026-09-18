# -*- coding: utf-8 -*-
"""Importa a base do usuário `Ewanderson1` (`01 a 14.csv`) para dono='Ewanderson1'.

⚠️ O `dono` é o USERNAME, conferido na tabela `usuarios` ANTES de qualquer escrita,
não deduzido do nome do arquivo nem do e-mail. Medido em 13/09/2026 e reconferido
em 17/09/2026: username `Ewanderson1` · e-mail `ewanferreira962385@gmail.com` ·
status `ativo` · criado em 13/09/2026 16:24 UTC pelo PRÓPRIO usuário no site
(Fase 2 do onboarding), aprovado pelo Feca na mesma sessão. **Não existe env var
nem linha em `app/auth.py` para esta conta.**

É a regra da s260: `dono` errado não dá erro, dá **tela vazia** para o usuário certo.

── Duas cargas, e o que mudou entre elas ─────────────────────────────────────

**13/09/2026 (s357):** primeira carga, base zerada, 784 apostas. Foi DESFEITA em
15/09 (s364) a pedido do Feca — ele capturou a Betano pelo SharpenUp sobre um
import sem ID de bilhete e a base duplicou. Ver `scripts/zerar_base_ewanderson.py`
e `Backups/s364-zerar-ewanderson/`.

**17/09/2026 (s372):** esta carga, e o quadro agora é OUTRO — medido, não suposto:

- a base dele tem **179 bilhetes, todos `origem='extracao'`, de 15/09 a 20/09**.
  O CSV vai de 01/09 a 14/09: **sobreposição ZERO**. O risco que derrubou a
  primeira carga não existe nesta janela — mas volta no dia em que ele capturar
  uma casa com histórico longo (a Betano varre 3 anos). O corte por casa/dono
  (`main._CORTE_HISTORICO`) é a régua para isso, se acontecer.
- o export novo traz **1.104 linhas para o MESMO período** contra 784 do de 13/09.
  O anterior estava incompleto; a fonte é a mesma planilha dele.
- ele cadastrou **conta com nome real por casa** ao instalar a extensão. Daí a
  conta `Planilha` — ver `PARCEIRO`, abaixo.
- `Padovan` do tracker é `Padovan All Sports` na base dele — ver `_TIPSTER_MAP`.
- `Rei do Pitaco` voltou a existir (conta criada à mão) e foi unificada em
  `Pitaco` ANTES deste import, com recálculo de assinatura
  (`scripts/unificar_casas.py --somente "Rei do Pitaco" --aplicar`).

── Fonte ─────────────────────────────────────────────────────────────────────

CSV com `;`, 11 colunas, 1.104 apostas (01/09/2026 → 14/09/2026).

    DATE | SPORT | TIPSTER | GAME | BET | BOOKMAKER | TYPE | ODD | STAKE |
    STATUS | RESULT

É um tracker de SEGUIDOR de tipsters, não de casa: 5 tipsters (Padovan 378,
Arrudex 374, FEZINHA 175, PEI 125, Padovan NBA/NFL 52) em 24 casas.

**Uma única data por linha** (`DATE`). O arquivo não separa data da aposta de data
do evento, então ela é a data do bilhete — não há o que estimar (`CLAUDE.md`:
data derivada por estimativa é dado inventado).

── Decisões (confirmadas pelo Feca, 13/09/2026) ──────────────────────────────

- **Stake convertida para REAIS a 1u = R$ 50,00** (s373; na s357 era gravada em
  unidades, verbatim, porque o tamanho da unidade dele não era conhecido e
  supô-lo seria palpite). A planilha vai de 0,10u a 4,00u — R$ 5,00 a R$ 200,00,
  com 0,5u/0,25u/1u dominando. O Feca declarou o valor em 17/09 e ele **confere
  contra a própria base**: as stakes que a captura trouxe das casas, já em R$, são
  12,50 · 25,00 · 37,50 · 50,00 · 100,00 — 0,25u · 0,5u · 0,75u · 1u · 2u. Ver
  `UNIDADE_BRL`. Sem a conversão, a Caixa e o custo comparariam unidades com
  reais na mesma tela, e as apostas de 01→14 pareceriam 50× menores que as de
  15→20. `RESULT` continua em unidades, e é o P/L já pronto — **não é gravado**
  (o P/L é derivado, nunca persistido), mas é o que audita os outros campos.
- **Uma conta `Planilha` por casa** (s372; na s357 era `Padrão`) — 24 linhas no
  Painel de Contas. O histórico da planilha fica numa conta PRÓPRIA, ao lado das
  contas reais que ele cadastrou depois: o CSV não diz de quem era a conta em
  setembro, e casar o histórico com a conta capturada seria palpite gravado como
  fato. Custo continua por conta.
- **`Padovan` e `Padovan NBA/NFL` ficam SEPARADOS.** Ele separou no tracker e o
  P/L dos dois diverge de verdade (+59,19u contra −10,13u). Fundir apagaria uma
  medição que já existe.
- **Onde o rótulo contradiz o dinheiro, manda o dinheiro** (§ abaixo).
- **Dono solo** — sem `OPERADORES`, sem dedup cruzada.

── O dinheiro audita o rótulo, e pegou 5 linhas ──────────────────────────────

`RESULT` é o P/L em unidades, então ele é conferível contra as fórmulas do
`calcular_pl` lidas ao contrário (`CLAUDE.md`: a prova é o retorno, o rótulo não).
Medido linha a linha no export de 17/09 (1.104 linhas, **0 divergentes** no
confronto final; a diferença de −0,10u no total é arredondamento do tracker, que
grava o P/L ao centavo de unidade e a odd com 2 casas):

- **342 `won` batem EXATOS** com `stake × (odd − 1)`, tolerância 0,02. Zero
  divergência ⇒ não há meia-vitória escondida sob o rótulo `won`.
- **753 `lost` batem** com `−stake`.
- **2 `lost` com RESULT POSITIVO** (L796 e L1099) batem exatamente com a fórmula
  de VITÓRIA (+0,90 e +1,08). São `W` mal rotuladas.
- **3 `void` com RESULT = −stake** (L803, L1024, L1025). Void devolve o stake e dá
  P/L 0; retorno 0 é `L`. São `L` mal rotuladas.
- **nenhuma `pending`** neste export — o período está todo liquidado.

Fica `W` 346 · `L` 756 · `V` 2. As 5 corrigidas saem NOMEADAS no relatório do DRY:
correção automática que ninguém vê é correção que ninguém audita.

── Zero não é ausência ───────────────────────────────────────────────────────

4 linhas trazem `ODD 0.00` (L258, L489, L1026, L1029), todas perdidas. Zero é uma
odd que não existe e passa por toda checagem de forma, então a odd entra **VAZIA**,
nunca 0 (`CLAUDE.md`: com odd 0 um bilhete ganho viraria −1u). Em `L` o P/L não
depende da odd, e desde a s259 a odd só é exigida em `W`/`HW` — as quatro nascem
`resolvida`.

Odd alta NÃO é defeito: as múltiplas chegam a 16.946,72 (10+ pernas). Todas são
perdidas e o RESULT confere com `−stake`; não há o que corrigir.

── Casa: grafia do banco, nunca a do arquivo ─────────────────────────────────

`casa` é TEXTO em 7 tabelas — cada grafia é uma casa DIFERENTE no sistema. As
grafias abaixo foram MEDIDAS no banco, uma a uma, e RECONFERIDAS em 17/09/2026
(a contagem é a do sistema inteiro, nesta data):

    TivoBet      → Tivo               (`_CASA_DISPLAY`; 282 bilhetes)
    BetNacional  → Betnacional        (`_CASA_DISPLAY`; 2.232 bilhetes)
    Rei do Pitaco→ Pitaco             (unificada na s270; 524 bilhetes. A grafia
                 velha RESSUSCITOU na base dele — conta criada à mão — e foi
                 refundida antes deste import, com assinatura recalculada.)
    Esportiva Bet→ Esportiva          (1.453 bilhetes)
    BetEsporte   → BETesporte         (1.720 bilhetes)
    Onabet       → OnaBet             (8 bilhetes)
    Bateu Bet    → Bateu              (131 bilhetes, contra 1 em `Bateubet`)
    King Panda   → KingPanda          (447 bilhetes; novo neste export)
    Esporte da Sorte → Esportes da Sorte  (a base tem as DUAS grafias já
                 duplicadas: `Esporte Da Sorte` 102 × `Esportes da Sorte` 100.
                 Escolhida a da marca, decisão do Feca. Unificar as gêmeas é
                 trabalho à parte, com recálculo de assinatura — ver
                 `scripts/unificar_casas.py`.)
    Outras Casas → Outra              (casa fantasma que o sistema já usa, 189)

`LottoLand` (16) e `Esporte 365` (11) **não existem na base** e entram VERBATIM —
nunca title-casear, que mutila `BETesporte`/`VaideBet`/`KingPanda`. As outras
já batem com a grafia do banco.

── Categoria: o objeto apostado, não o tipo de mercado ───────────────────────

O `BET` é texto livre do tracker (mercado e seleção colados, sem acento), então a
classificação é por palavra-chave sobre o texto inteiro, na ordem do `_REGRAS` —
**objeto específico antes da forma do mercado**, que é o `§1`: over/under,
handicap e período não mudam a categoria. Daí `Handicap de Escanteios` cair em
`Escanteios` e `Handicap de games` em `Games`, não em `Handicap`.

Quatro rótulos foram decididos pelo PRECEDENTE MEDIDO na base (não por palpite):

    tiros de meta, laterais → Team Props     (17 e 34 linhas já assim)
    defesas do goleiro      → Player Props   (89 linhas)
    strikeouts, sacks, top 3→ Player Props   (338, 22 e 50 linhas)

`Bet Builder` / `Criar Aposta` (os `- CA `) e `Todos ganham` vão para `Múltipla`:
é o `MASTER_APOSTAS §Bet Builder`, "mesmo quando todas as seleções forem do mesmo
jogo".

`Placar Exato`, `Resultado Exato` e `Intervalo/Final` ficam em `Outros` — não há
categoria canônica para eles, e a base já os trata assim.

── Descrição: cópia, nunca invenção ──────────────────────────────────────────

A descrição é o `BET` limpo mais o confronto em `[A v B]` (`MASTER_DESCRICAO`),
com o `GAME` convertido do separador do arquivo (` x ` ou ` - `). Nenhum nome é
reescrito e nenhum acento é reposto: o tracker exportou sem acento
(`Cartoes`, `Finalizacoes`) e "corrigir" isso inventaria texto que a fonte não tem.

⚠️ **As múltiplas chegam com `GAME = N/A` e `BET = Multipla`** — o tracker não
exporta as pernas. A descrição delas é literalmente `Múltipla` (510 linhas neste
export), e outras vêm sem confronto. Não há como recuperar: o detalhe nunca saiu
da casa.

── Dedup: o CSV NÃO tem ID de bilhete ────────────────────────────────────────

Sem código, `repository._assinatura` hasheia CONTEÚDO
(`casa|parceiro|data|aposta|descricao|stake|odd`). Consequência a declarar:

⚠️ Recaptura de casa que já esteja aqui traz a aposta COM código real. Assinatura
   por ID nunca colide com assinatura por conteúdo → **não deduplica, duplica**.
   Foi isso que derrubou a carga de 13/09.

   **Nesta carga a janela está limpa, e isso foi MEDIDO, não suposto:** os 179
   bilhetes que ele tem são de 15/09 em diante; o CSV para em 14/09. A conta
   `Planilha` afasta ainda mais, porque `parceiro` entra no hash.

   O que reabre o risco: casa que exporta histórico longo (a Betano varre 3 anos
   por desenho). Se acontecer, a régua é o corte por (dono, casa)
   — `main._CORTE_HISTORICO` —, aplicado no `/extrair` ANTES da IA. Apagar do
   banco não basta: a linha volta inteira na varredura seguinte.

Linhas de conteúdo 100% idêntico dentro do próprio CSV escalam com `_counter`
(`B`, `B|2`, …) em vez de colidir — mesmo laço do `upsert_bilhetes`. Isso importa
aqui: as múltiplas com a mesma descrição `Múltipla` só se distinguem por casa,
data, stake e odd.

Uso:
    python scripts/import_ewanderson_csv.py --csv "C:\\...\\01 a 14.csv"        # DRY
    python scripts/import_ewanderson_csv.py --csv "C:\\...\\01 a 14.csv" --go   # escreve
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
DONO = 'Ewanderson1'     # username conferido em `usuarios`, não deduzido do arquivo
# Conta `Planilha` (decisão do Feca, 17/09/2026): o histórico da planilha fica numa
# conta PRÓPRIA, separada das contas reais que ele cadastrou ao instalar a extensão
# (`Ykaro` na Betano, `Woshington` na Bet365, `Joao` na SportingBet…). O CSV é um
# tracker de tipster e não diz de QUEM era a conta em setembro — atribuir o histórico
# à conta capturada seria gravar um palpite como fato. `parceiro` entra na assinatura,
# então a separação também é dedup: nada do import colide com nada da captura.
PARCEIRO = 'Planilha'
ORIGEM = 'import'
VALID = {'W', 'L', 'V', 'HW', 'HL'}
TOL = 0.02               # tolerância do confronto RESULT × fórmula (centavo de unidade)

# ---------- a unidade ----------
# O tracker exporta stake e RESULT em UNIDADES; o banco guarda REAIS. **1u = R$ 50,00**,
# declarado pelo Feca em 17/09/2026 e CORROBORADO contra a própria base dele: as stakes
# que a captura trouxe das casas (já em R$) são 12,50 · 25,00 · 37,50 · 50,00 · 100,00 —
# exatamente 0,25u · 0,5u · 0,75u · 1u · 2u. Não é conversão por palpite: os dois lados
# da mesma base concordam.
#
# ⚠️ **A auditoria continua em UNIDADES**, que é a moeda da fonte: o `RESULT` vem em
# unidades e a `TOL` é centavo de unidade. Converter antes do confronto multiplicaria a
# tolerância por 50 e deixaria passar erro de até R$ 1,00 por linha. A conversão é o
# ÚLTIMO passo, só do que vai ao banco.
UNIDADE_BRL = 50.0

# Correção humana feita na grade ANTES desta recarga, a preservar. O import apaga e
# regrava o que ele mesmo escreveu, então edição do dono se perderia em silêncio — e
# **correção humana manda sobre a fonte** (`CLAUDE.md`). Chave: número da linha no CSV;
# valor: a stake em UNIDADES, como se estivesse escrita no arquivo (a conversão para R$
# acontece depois, igual para todo mundo).
#
#   L2 — Tivo, 14/09, múltipla @12,50: o Ewanderson trocou 2,33 → 0,25 no dashboard em
#        17/09 18:42 BRT (`correcoes` id 44752). Decisão do Feca: vale como unidades,
#        logo R$ 12,50. Ela DIVERGE do `RESULT` do arquivo (−2,33u) de propósito, e por
#        isso o confronto do relatório continua usando a stake do CSV — o que se audita
#        ali é a tradução, não a decisão do dono.
_AJUSTES_STAKE = {2: '0,25'}


# ---------- sanitização ----------
_CTRL = re.compile(r'[\x00-\x1f\x7f]+')
# Marcas de formatação invisíveis (Cf): zero-width, LTR/RTL mark, BOM. São
# INVISÍVEIS na tela mas entram no hash da assinatura, então o mesmo nome com e
# sem a marca vira bilhete diferente na dedup.
_INVIS = re.compile(r'[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]')


def limpa(v) -> str:
    if v is None:
        return ''
    return re.sub(r'\s{2,}', ' ', _CTRL.sub(' ', _INVIS.sub('', str(v)))).strip()


def _chave(s: str) -> str:
    s = unicodedata.normalize('NFKD', limpa(s))
    return ''.join(c for c in s if not unicodedata.combining(c)).lower().replace(' ', '')


def _sa(s) -> str:
    """Sem acento, minúsculo, espaços preservados — base da classificação."""
    s = unicodedata.normalize('NFKD', limpa(s))
    return ''.join(c for c in s if not unicodedata.combining(c)).lower()


# ---------- casa ----------
# Grafias MEDIDAS no banco (13/09/2026). Casa fora do mapa entra VERBATIM.
_CASA_MAP = {
    'tivobet':        'Tivo',
    'betnacional':    'Betnacional',
    'reidopitaco':    'Pitaco',
    'esportivabet':   'Esportiva',
    'betesporte':     'BETesporte',
    'onabet':         'OnaBet',
    'bateubet':       'Bateu',
    'esportedasorte': 'Esportes da Sorte',
    'outrascasas':    'Outra',
    # Não vinha no export de 13/09. `KingPanda` é a grafia do banco (447 bilhetes) e
    # title-casear mutilaria a marca — o mesmo caso de `BETesporte`/`VaideBet`.
    'kingpanda':      'KingPanda',
    # já batem com a base, mapeados para travar a grafia contra variação do arquivo
    'betano':         'Betano',
    'bet365':         'Bet365',
    'betmgm':         'BetMGM',
    'sportingbet':    'SportingBet',
    'casadeapostas':  'Casa de Apostas',
    'lottu':          'Lottu',
    'sportybet':      'SportyBet',
    'betao':          'Betão',
    'brasildasorte':  'Brasil da Sorte',
    'vbet':           'VBet',
    'multibet':       'MultiBet',
}
CASAS_NOVAS = {'LottoLand', 'Esporte 365'}   # não existem na base — entram verbatim


def norm_casa(v) -> str:
    bruto = limpa(v)
    return _CASA_MAP.get(_chave(bruto), bruto)


# ---------- esporte ----------
_ESPORTE_MAP = {
    'futebol':  'Futebol',
    'nfl':      'Futebol Americano',
    'basebol':  'Baseball',
    'basquete': 'Basquete',
}


def norm_esporte(v) -> str:
    return _ESPORTE_MAP.get(_chave(v), limpa(v) or 'Outro')


# ---------- tipster ----------
# O tracker exporta `Padovan`; na base dele o mesmo tipster se chama `Padovan All
# Sports` — está assim no cadastro (`tipsters`) E nos 65 bilhetes já capturados.
# MEDIDO em 17/09/2026, não suposto: os outros quatro nomes batem caractere a
# caractere. Sem o de-para, a carteira do Padovan nasce partida em dois tipsters
# que a tela lê como pessoas diferentes — e o filtro de tipster recorta por NOME.
_TIPSTER_MAP = {'padovan': 'Padovan All Sports'}


def norm_tipster(v) -> str:
    bruto = limpa(v)
    return _TIPSTER_MAP.get(_chave(bruto), bruto)


# ---------- categoria ----------
# Ordem É a regra: objeto apostado ANTES da forma do mercado (`MASTER_APOSTAS §1`).
# `Handicap de Escanteios` é Escanteios; `Handicap de games` é Games. Handicap só
# fica quando não há objeto específico no texto.
_REGRAS: list[tuple[str, str]] = [
    # bet builder e combinadas vendidas como mercado único (§ Bet Builder)
    (r'\bcriar? aposta\b|(^|\s)- ?ca |todos ganham|todos ganhadores|todos ganhham', 'Múltipla'),
    # objetos estatísticos do futebol
    (r'impedimento', 'Impedimentos'),
    (r'escanteio|\bcorner', 'Escanteios'),
    (r'cartao|cartoes', 'Cartões'),
    (r'desarme', 'Desarmes'),
    (r'chutes? (a|ao|no) gol|finalizac\w+ no gol|remates? (a|à) baliza', 'Chutes no Gol'),
    (r'\bchutes?\b|finalizac\w+|\bremates?\b', 'Chutes'),
    (r'\bassist', 'Assistência'),
    (r'\bfaltas?\b', 'Faltas'),
    # precedente MEDIDO na base: estatística DE EQUIPE
    (r'tiros? de meta|\blaterais\b|\blateral\b', 'Team Props'),
    # ANTES de Player Props: jarda é jarda, venha de corrida, passe ou recepção.
    # Com a ordem invertida, `Jardas por recepção` caía em Player Props e
    # `Jardas corridas` em Jardas — dois nomes para a mesma coisa.
    (r'jardas', 'Jardas'),
    # precedente MEDIDO na base: estatística DE JOGADOR
    (r'defesas?( do goleiro)?|strikeout|\bsacks?\b|top 3|podio|\bduelos?\b|'
     r'\bdribles?\b|recepc\w+|touchdown|interceptac\w+|\bpasses\b|rebote|'
     r'roubo de bola|\btocos?\b|home run|\bhits?\b|\bbases\b|\baces?\b', 'Player Props'),
    (r'\bgames?\b|tie ?breaks?', 'Games'),   # tie break: precedente medido na base
    (r'\bsets?\b', 'Sets'),
    (r'\brounds?\b', 'Rounds'),
    (r'marcador|marcar\b|a marcar|para marcar|anytime', 'Anytime'),
    (r'ambas (as )?(equipes|times) marcam|ambos os times marcam|ambas marcam', 'Ambas Marcam'),
    (r'dupla chance|chance dupla|\bdc\b', 'Dupla Chance'),
    (r'\bgols?\b|\bgolos?\b', 'Gols'),
    (r'\bpontos?\b', 'Pontos'),
    (r'vencedor|resultado final|resultado do|resultado \d|\b1x2\b|moneyline|'
     r'metodo de vitoria|para ganhar|vence\b', 'ML'),
    (r'handicap', 'Handicap'),
]
_REGRAS_C = [(re.compile(rx), cat) for rx, cat in _REGRAS]


_RX_CORRIDA = re.compile(r'\brbis?\b|\bcorridas?\b')


def norm_categoria(bet: str, tipo: str, esporte: str) -> str:
    if _chave(tipo) == 'multipla':
        return 'Múltipla'
    t = _sa(bet)
    if not t or t == 'n/a':
        return 'Outros'
    # `Corridas` é categoria de BASEBALL (`MASTER_APOSTAS §6`: corridas e RBIs).
    # No futebol americano "tentativas de corrida" é estatística de jogador, e
    # mandá-la para cá misturaria dois mercados que não têm nada em comum.
    if esporte == 'Baseball' and _RX_CORRIDA.search(t):
        return 'Corridas'
    for rx, cat in _REGRAS_C:
        if rx.search(t):
            return cat
    if _RX_CORRIDA.search(t):
        return 'Player Props'
    return 'Outros'


# ---------- descrição ----------
def _conf(game: str) -> str:
    """`A x B` ou `A - B` → `[A v B]` (`MASTER_DESCRICAO`: o separador é `v`)."""
    ev = limpa(game)
    if not ev or ev.upper() == 'N/A':
        return ''
    for sep in (' x ', ' X ', ' vs ', ' - '):
        if sep in ev:
            a, b = ev.split(sep, 1)
            return f'[{a.strip()} v {b.strip()}]'
    return f'[{ev}]'


SEM_DETALHE = 'Sem detalhe no export'


def norm_descricao(bet: str, game: str, categoria: str) -> str:
    """Cópia fiel do rótulo da casa + confronto. NUNCA reescreve nome próprio.

    Onde a fonte não diz o que foi apostado, a descrição DIZ ISSO — chamar de
    `Múltipla` uma simples sem detalhe seria inventar o que o arquivo não tem."""
    alvo = limpa(bet)
    if alvo.upper() == 'N/A':
        alvo = ''
    if _chave(alvo) == 'multipla':
        alvo = 'Múltipla'
    conf = _conf(game)
    if not alvo and categoria == 'Múltipla':
        alvo = 'Múltipla'
    desc = f'{alvo} {conf}'.strip()
    return desc or SEM_DETALHE


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
    """Odd com PRECISÃO COMPLETA — nunca truncar (só o display encurta).

    Odd 0 vira VAZIO: zero não é ausência, e uma odd 0 gravada passa por toda
    checagem de forma para depois virar P/L errado em qualquer recaptura."""
    s = limpa(v).replace(',', '.')
    f = _para_float(s)
    if f is None or f <= 0:
        return ''
    s = s.rstrip('0').rstrip('.') if '.' in s else s
    return s.replace('.', ',')


# ---------- resultado ----------
_RES = {
    'won':     'W',
    'lost':    'L',
    'void':    'V',
    'push':    'V',     # handicap asiático na linha: stake devolvido
    'pending': '',      # aberta — resultado VAZIO (§13.1)
}


def _pl_esperado(resultado: str, stake: float, odd) -> float | None:
    """As fórmulas do `calcular_pl`, para conferir o RESULT do arquivo."""
    if resultado == 'L':
        return -stake
    if resultado == 'V':
        return 0.0
    if resultado == 'HL':
        return -stake / 2
    if odd is None:
        return None
    if resultado == 'W':
        return stake * (odd - 1)
    if resultado == 'HW':
        return stake * (odd - 1) / 2
    return None


def veredito_do_dinheiro(rotulo: str, stake: float, odd, pl: float):
    """Onde o rótulo contradiz o RESULT, manda o dinheiro (`CLAUDE.md`).

    Devolve (resultado, motivo|None). Só corrige quando o P/L bate EXATO com
    outra fórmula — divergência sem fórmula que feche não autoriza escrita
    nenhuma, e a linha fica com o rótulo do arquivo."""
    esperado = _pl_esperado(rotulo, stake, odd)
    if esperado is not None and abs(pl - esperado) <= TOL:
        return rotulo, None
    for alvo in ('W', 'L', 'V', 'HW', 'HL'):
        if alvo == rotulo:
            continue
        e = _pl_esperado(alvo, stake, odd)
        if e is not None and abs(pl - e) <= TOL:
            return alvo, f'RESULT {pl:+.2f} bate com {alvo}, não com {rotulo}'
    return rotulo, None


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
def ler(caminho: str):
    with open(caminho, encoding='utf-8-sig', newline='') as fh:
        brutas = list(csv.DictReader(fh, delimiter=';'))
    if not brutas:
        raise SystemExit('CSV vazio')

    faltando = {'DATE', 'SPORT', 'TIPSTER', 'GAME', 'BET', 'BOOKMAKER', 'TYPE',
                'ODD', 'STAKE', 'STATUS', 'RESULT'} - set(brutas[0])
    if faltando:
        raise SystemExit(f'colunas ausentes no CSV: {sorted(faltando)}')

    rows, avisos, corrigidas, sem_odd, ajustados = [], [], [], [], []
    for i, b in enumerate(brutas, start=2):
        estado = limpa(b['STATUS']).lower()
        if estado not in _RES:
            raise SystemExit(f'linha {i}: STATUS desconhecido {estado!r}')

        data = limpa(b['DATE']).split(' ')[0]
        try:
            quando = dt.datetime.strptime(data, '%d/%m/%Y')
        except ValueError:
            raise SystemExit(f'linha {i}: DATE ilegível {data!r}')

        stake_txt = fmt_stake(b['STAKE'])
        odd_txt = fmt_odd(b['ODD'])
        stake = _para_float(stake_txt) or 0.0
        odd = _para_float(odd_txt)
        pl = _para_float(b['RESULT'])

        resultado = _RES[estado]
        motivo = None
        if resultado and pl is not None:
            resultado, motivo = veredito_do_dinheiro(resultado, stake, odd, pl)
        if motivo:
            corrigidas.append((i, estado, resultado, motivo))
        if not odd_txt:
            sem_odd.append((i, limpa(b['ODD']), resultado))

        # A correção humana entra DEPOIS da auditoria acima (que confronta o RESULT com
        # a stake do arquivo) e ANTES da conversão para R$, que é igual para todo mundo.
        stake_u = stake_txt
        if i in _AJUSTES_STAKE:
            stake_u = _AJUSTES_STAKE[i]
            ajustados.append((i, stake_txt, stake_u))

        esporte = norm_esporte(b['SPORT'])
        categoria = norm_categoria(b['BET'], b['TYPE'], esporte)
        r = {
            'linha': i,
            'casa': norm_casa(b['BOOKMAKER']),
            'parceiro': PARCEIRO,
            'data': data,
            'esporte': esporte,
            'tipster': norm_tipster(b['TIPSTER']),
            'aposta': categoria,
            'descricao': norm_descricao(b['BET'], b['GAME'], categoria),
            # `stake` é o que vai ao BANCO, em REAIS. As duas colunas em unidades ficam
            # como `_`: `_stake_u_csv` é o que a planilha diz (e é contra ela que o
            # RESULT é conferido), `_stake_u` é a efetiva, com a correção humana.
            'stake': fmt_stake((_para_float(stake_u) or 0.0) * UNIDADE_BRL),
            'odd': odd_txt,
            'resultado': resultado,
            '_estado': estado,
            '_bet': limpa(b['BET']),
            '_game': limpa(b['GAME']),
            '_pl_arquivo': pl,
            '_stake_u_csv': stake_txt,
            '_stake_u': stake_u,
            '_dt': quando,
        }
        if categoria == 'Outros':
            avisos.append((i, r['_bet'], r['descricao']))
        rows.append(r)

    # Conteúdo idêntico escala com `_counter` em vez de colidir (mesma regra do
    # `upsert_bilhetes`): duas apostas reais iguais não podem virar uma só.
    vistos = defaultdict(int)
    for r in rows:
        base = assinatura(r)
        vistos[base] += 1
        r['assinatura'] = assinatura(r, _counter=vistos[base])
        r['_colidiu'] = vistos[base] > 1

    return rows, avisos, corrigidas, sem_odd, ajustados


# ---------- relatório do DRY ----------
def _pl(r: dict):
    """P/L em REAIS — a moeda que vai para o banco."""
    return _pl_esperado(r['resultado'], _para_float(r['stake']) or 0.0,
                        _para_float(r['odd']))


def _pl_u(r: dict):
    """P/L em UNIDADES pela stake do ARQUIVO — é este que confronta o `RESULT`.

    Não é o `_pl` dividido por 50: a linha com correção humana tem stake diferente
    da do CSV de propósito, e o confronto audita a TRADUÇÃO, não a decisão do dono."""
    return _pl_esperado(r['resultado'], _para_float(r['_stake_u_csv']) or 0.0,
                        _para_float(r['odd']))


def relatorio(rows, avisos, corrigidas, sem_odd, ajustados):
    print(f'DONO={DONO} | conta={PARCEIRO!r} por casa | linhas: {len(rows)}')
    datas = sorted(r['_dt'] for r in rows)
    print(f'período: {datas[0]:%d/%m/%Y} → {datas[-1]:%d/%m/%Y}')

    print('\n— casa (grafia do banco) —')
    for k, v in Counter(r['casa'] for r in rows).most_common():
        flag = '  ⚠️ CASA NOVA (não existe na base)' if k in CASAS_NOVAS else ''
        print(f'  {k:<20} {v:>4}{flag}')

    print('\n— tipster —')
    for k, v in Counter(r['tipster'] for r in rows).most_common():
        print(f'  {k:<20} {v:>4}')

    print('\n— esporte —')
    for k, v in Counter(r['esporte'] for r in rows).most_common():
        print(f'  {k:<20} {v:>4}')

    print('\n— categoria —')
    for k, v in Counter(r['aposta'] for r in rows).most_common():
        print(f'  {k:<16} {v:>4}')

    print('\n— resultado —')
    for k, v in Counter(r['resultado'] or '(aberta)' for r in rows).most_common():
        print(f'  {k:<10} {v:>4}')

    liq = [r for r in rows if r['resultado']]
    turn = sum(_para_float(r['stake']) or 0 for r in liq)
    pl = sum(_pl(r) or 0 for r in liq)
    turn_u = sum(_para_float(r['_stake_u']) or 0 for r in liq)
    pl_u = sum(_pl_esperado(r['resultado'], _para_float(r['_stake_u']) or 0.0,
                            _para_float(r['odd'])) or 0 for r in liq)
    print(f'\n— P/L (REAIS — 1u = R$ {UNIDADE_BRL:,.2f}) —\n'
          f'  liquidadas {len(liq)} | turnover R$ {turn:,.2f} '
          f'| P/L R$ {pl:+,.2f} | ROI {pl / turn * 100:.2f}%')
    print(f'  nas unidades da planilha: turnover {turn_u:,.2f}u | P/L {pl_u:+,.2f}u')

    # A prova de que a tradução não perdeu dinheiro: o P/L calculado pelas nossas
    # fórmulas contra o P/L que o arquivo já trazia pronto, linha a linha. Fica em
    # UNIDADES e com a stake do CSV — é a moeda em que o `RESULT` foi escrito, e a
    # `TOL` de 0,02 só significa alguma coisa nela.
    pl_arq = sum(r['_pl_arquivo'] or 0 for r in liq)
    pl_csv = sum(_pl_u(r) or 0 for r in liq)
    fora = [r for r in liq
            if r['_pl_arquivo'] is not None and abs((_pl_u(r) or 0) - r['_pl_arquivo']) > TOL]
    # A diferença que sobra com ZERO linhas divergentes é arredondamento do
    # tracker (ele grava o P/L já arredondado ao centavo de unidade, e a odd com
    # 2 casas). Só vira defeito se alguma linha estourar a TOL, e aí ela aparece.
    print(f'  confronto com o RESULT do arquivo: calc {pl_csv:+,.2f}u × arquivo '
          f'{pl_arq:+,.2f}u | diferença {pl_csv - pl_arq:+.2f}u '
          f'| linhas divergentes: {len(fora)}')
    for r in fora[:10]:
        print(f'    ⚠️ L{r["linha"]:<4} calc {(_pl_u(r) or 0):+.2f} × arquivo '
              f'{r["_pl_arquivo"]:+.2f} | {r["descricao"][:52]}')

    if ajustados:
        print(f'\n⚠️ {len(ajustados)} correção(ões) HUMANA(S) preservada(s) sobre o CSV '
              f'(`_AJUSTES_STAKE`):')
        for i, de, para in ajustados:
            em_reais = (_para_float(para) or 0.0) * UNIDADE_BRL
            print(f'  L{i:<4} stake {de}u → {para}u  (R$ {em_reais:,.2f})')

    if corrigidas:
        print(f'\n⚠️ {len(corrigidas)} linha(s) em que o RÓTULO contradiz o DINHEIRO '
              f'(o dinheiro mandou):')
        for i, de, para, motivo in corrigidas:
            print(f'  L{i:<4} {de:<8} → {para:<2} | {motivo}')

    if sem_odd:
        print(f'\n⚠️ {len(sem_odd)} linha(s) sem odd utilizável (zero não é ausência '
              f'— entram VAZIAS):')
        for i, bruto, res in sem_odd:
            print(f'  L{i:<4} ODD={bruto!r} resultado={res}')

    if avisos:
        print(f'\n⚠️ {len(avisos)} linha(s) em `Outros` (mercado sem categoria):')
        for i, bet, desc in avisos[:20]:
            print(f'  L{i:<4} {bet[:48]:<48} → {desc[:52]}')

    colidiu = [r for r in rows if r['_colidiu']]
    if colidiu:
        print(f'\n⚠️ {len(colidiu)} linha(s) de conteúdo idêntico (escalam com _counter):')
        for r in colidiu[:8]:
            print(f'  L{r["linha"]:<4} {r["data"]} {r["casa"]:<12} {r["descricao"][:52]}')

    hoje = datas[-1]
    for dias in (2, 7):
        n = sum(1 for r in rows if r['_dt'] >= hoje - dt.timedelta(days=dias))
        print(f'\n⚠️ {n} linha(s) nos últimos {dias}d — recaptura pela extensão '
              f'DUPLICA (CSV sem ID de bilhete)')

    print('\n— amostra (10 primeiras) —')
    for r in rows[:10]:
        print(f'  {r["data"]} | {r["casa"]:<12} | {r["tipster"]:<16} | '
              f'{r["esporte"]:<18} | {r["aposta"]:<14} | {r["stake"]:>6} @ '
              f'{r["odd"] or "-":<9} | {r["resultado"] or "-":<2} | {r["descricao"][:60]}')

    print('\n— amostra por categoria (1 de cada) —')
    vistos = set()
    for r in rows:
        if r['aposta'] in vistos:
            continue
        vistos.add(r['aposta'])
        print(f'  {r["aposta"]:<14} | {r["_bet"][:44]:<44} → {r["descricao"][:60]}')


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
                # O `dono` é conferido AQUI também: escrever sob username que não
                # existe não dá erro nenhum, só deixa a base invisível.
                u = await conn.fetchrow(
                    'SELECT username, status FROM usuarios WHERE username=$1', DONO)
                if not u:
                    raise SystemExit(f'dono {DONO!r} não existe em `usuarios` — abortado')
                if u['status'] != 'ativo':
                    print(f'  ⚠️ atenção: {DONO} está {u["status"]!r}, não `ativo`')

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
                    # → ancora na data da aposta para sair cronológico.
                    #
                    # ⚠️ A âncora é o criado_em MAIS ANTIGO do que o dono já tem, não
                    # `NOW()`. Em 13/09 a base estava vazia e `NOW()` servia; hoje ele
                    # tem 179 bilhetes capturados (15→20/09) e ancorar em `NOW()` jogaria
                    # as 1.104 linhas de 01→14/09 para o TOPO do feed, acima das mais
                    # novas. A data da aposta continuaria certa na grade — só o feed
                    # nasceria de cabeça para baixo, sem erro nenhum.
                    await conn.execute(
                        """
                        WITH base AS (
                            SELECT COALESCE(
                                     (SELECT MIN(criado_em) FROM bilhetes
                                       WHERE dono=$1 AND origem IS DISTINCT FROM $2),
                                     NOW()
                                   ) - INTERVAL '1 second' AS ancora
                        ), ordered AS (
                            SELECT id,
                                   ROW_NUMBER() OVER (ORDER BY to_date(data,'DD/MM/YYYY') ASC,
                                                               id ASC) AS rn,
                                   COUNT(*) OVER () AS total
                            FROM bilhetes WHERE dono=$1 AND origem=$2
                        )
                        UPDATE bilhetes b
                        SET criado_em = (SELECT ancora FROM base)
                                        - ((o.total - o.rn) * INTERVAL '1 second')
                        FROM ordered o WHERE b.id = o.id
                        """, DONO, ORIGEM)
                # ⚠️ A conferência é sobre o que ESTE import escreveu, não sobre o total
                # do dono: a base já tem bilhete de outra origem (captura), e comparar o
                # total com as linhas do CSV acusaria colisão que não houve.
                n = await conn.fetchval(
                    'SELECT COUNT(*) FROM bilhetes WHERE dono=$1 AND origem=$2', DONO, ORIGEM)
                tot = await conn.fetchval('SELECT COUNT(*) FROM bilhetes WHERE dono=$1', DONO)
                nc = await conn.fetchval(
                    'SELECT COUNT(DISTINCT casa) FROM parceiros WHERE dono=$1', DONO)
                np = await conn.fetchval('SELECT COUNT(*) FROM parceiros WHERE dono=$1', DONO)
                print(f'\nOK — importados={n} | total do dono={tot} | casas={nc} | contas={np}')
                if n != len(rows):
                    print(f'  ⚠️ o CSV tinha {len(rows)} linhas e o import gravou {n} — '
                          f'diferença = colisão de assinatura, confira antes de seguir')
                return
            finally:
                await conn.close()
        except SystemExit:
            raise
        except Exception as e:                       # noqa: proxy instável → retry
            last_err = e
            print(f'  [tentativa {tentativa}] falhou: {type(e).__name__}: {e}')
    raise SystemExit(f'import falhou após 3 tentativas: {last_err}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--go', action='store_true', help='escreve no banco (sem isto = DRY)')
    a = ap.parse_args()

    rows, avisos, corrigidas, sem_odd, ajustados = ler(a.csv)
    relatorio(rows, avisos, corrigidas, sem_odd, ajustados)

    if not a.go:
        print('\n(DRY — nada foi escrito. Use --go para gravar.)')
        return
    carregar_env()
    asyncio.run(importar(rows))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
