# -*- coding: utf-8 -*-
"""Importa a base do tipster **RogerinComeuMeuSaldo** (`sobolas.csv`) — 6º
tipster público.

⚠️ **O arquivo se chama `sobolas.csv` e a marca NÃO é essa.** A conversa começou
como "Tipsters/SoBolas" e o Feca trocou o nome antes do import: a marca é
`RogerinComeuMeuSaldo`, slug `/tipsters/rogerincomeumeusaldo`. O nome do arquivo
não é fonte de nada — nem da marca, nem do dono.

⚠️ O `dono` NÃO está escrito neste arquivo, de propósito. Ele é o **username**
com que a pessoa se cadastrou no site, e no dia em que este script foi escrito
(31/08/2026) essa conta **ainda não existia** — medido, não suposto: o cadastro
mais recente na tabela `usuarios` era `Tonelada` (22/08/2026), e nenhum username
parecido existia. Por isso o `--dono` é **argumento obrigatório** e é **conferido
na tabela** antes de qualquer escrita (`status='ativo'`, hash de 60 caracteres).

É a regra da s260: com o `dono` errado o isolamento falha em **silêncio** —
nenhum erro, só tela vazia para o usuário certo. E marca ≠ username, como em
`Fleury`/`Flurray` e `PassaTips VIP`/`passapano`. A ponte entre os dois é o
registro `TIPSTERS_PUBLICOS` (`app/main.py`), onde o slug é a marca e o `dono` é
o username. Nunca deduza um do outro.

── Fonte ─────────────────────────────────────────────────────────────────────

Export de tracker (formato pt-PT: `Cotação`, `Ténis`, `Basquetebol`, `Bónus`),
CSV com `;`, aspas em tudo, UTF-8 com BOM. **393 linhas, 24 colunas,
10/04/2026 → 31/08/2026.**

    Data | Tipo | Esporte | Título da aposta | Cotação | Valor | Ganho | Lucro |
    Estado | Casa de apostas | Tipster | Categoria | Competição | Tipo de aposta |
    Closing Odds | Probabilidade estimada % | EV | Comissão | Bónus de ganho |
    Ao vivo | Aposta gratuita | Cashout | Eachway | Comentário

**Catorze colunas estão VAZIAS nas 393 linhas** (`Tipster`, `Categoria`,
`Competição`, `Tipo de aposta`, `Closing Odds`, `Probabilidade estimada %`,
`EV`, `Comissão`, `Bónus de ganho`, `Ao vivo`, `Aposta gratuita`, `Cashout`,
`Eachway`, `Comentário`). O tracker tem os campos; ele não os preencheu. Sobram
9 colunas com informação, e **nenhuma delas diz o mercado** — daí a categoria
sair da leitura do título, e não de uma coluna.

A planilha é **aritmeticamente consistente**, e isso foi MEDIDO: `Ganho` bate com
`Cotação × Valor` nas 163 ganhas (0 divergências) e `Lucro` bate com
`Ganho − Valor` nas 393 (0 divergências). O `_relatorio` refaz essa conta linha a
linha, então erro de normalização (odd com ponto/vírgula trocados, resultado mal
lido) aparece como divergência em vez de passar calado. **Medido com o código que
está aqui: 0 divergências em 393.**

── Duas ERAS, e elas não se parecem ──────────────────────────────────────────

    ERA 1  10/04 → 30/05  181 apostas  245,90u  P/L  +18,72u  ROI  +7,61%
    ERA 2  27/07 → 31/08  212 apostas  212,92u  P/L  +53,93u  ROI +25,33%
    TOTAL                 393 apostas  458,82u  P/L  +72,66u  ROI +15,84%

A ERA 1 é quase toda **prop de jogador da NBA** (162 de 181 rotuladas
Basquetebol: `Adebayo 5 assist`, `Dylan Harper 3 3pt`, `Gobert DD`). A ERA 2 é
**multiesporte** (Ténis 105, Futebol 68) com títulos no formato `A / B`. Há um
hiato de ~2 meses entre as duas (30/05 → 27/07), e a taxa de acerto salta de
29,8 % para 51,4 %. Isso importa para quem for ler o histórico depois:
**assinatura tem ERA** (regra do `CLAUDE.md`), e um backtest que misture as duas
mede duas pessoas diferentes.

── Stake em UNIDADES ─────────────────────────────────────────────────────────

`Valor` vai de 0,10 a 5,00 (248 das 393 são exatamente 1,00). É unidade, não
real — mesma decisão do `SoChutes`, `Fleury`, `Rei do Criquete` e `PassaTips`. O
P/L do dashboard é o P/L em unidades.

── Resultado: só duas metades, e uma delas esconde um cashout ────────────────

`Estado` tem **apenas** `Ganha` (163) e `Perdida` (230). Nenhuma aberta, nenhuma
anulada, nenhum void — todas as 393 estão liquidadas.

    Ganha → W        Perdida → L

**Uma linha desmente o rótulo** e é tratada como o que ela é: `25/08 Kostanay /
Kaisar`, `Estado=Ganha`, odd **0,690**, stake 1,00, `Ganho` 0,69, `Lucro` −0,31.
Retorno MENOR que a stake com resultado "ganha" é a assinatura de **cashout**, e
o `MASTER_RESULTADO §5.6` é explícito: cashout ≠ stake → `W` com
`Odd = Cashout ÷ Stake`. Como o tracker já gravou a odd como 0,69 (= 0,69 ÷
1,00), a leitura LITERAL do arquivo já produz o resultado certo — nada a
converter. Fica registrado porque um leitor futuro vai estranhar um `W` com P/L
negativo, e a explicação é essa.

── Descrição: VERBATIM, com os erros de digitação ────────────────────────────

O `Título da aposta` é texto livre digitado à mão, e traz o que texto digitado à
mão traz: `Royuce oneal`, `Dosonmu`, `Hartensteins`, `Kelly obre`, `Daniss`.
Vai **verbatim** (só limpeza de espaço e caractere de controle) — o
`MASTER_DESCRICAO §1` proíbe inventar informação, e "corrigir" nome de jogador
por palpite é inventar. Mesmo precedente do `import_passatips_xlsx.py`.

**O confronto não existe em coluna nenhuma** e por isso não entra na descrição.
O `MASTER_DESCRICAO §2` pede `Entidade - Mercado [Confronto]`; esta fonte não
tem o terceiro termo, e fabricá-lo seria pior que omiti-lo.

⚠️ **CORREÇÃO (mesma sessão, depois dos prints do canal).** Eu tinha escrito aqui
que a barra dos títulos `A / B` da ERA 2 "NÃO é separador de seleção" e que ele
pareava entidades de esportes diferentes por engano. **Está errado.** Os prints
do Telegram provam que ` / ` **É o separador de PERNA de uma DUPLA**, abreviada
pelo sobrenome de cada seleção — e a prova é a odd, que bate exato em 4 de 4:

    Egito / Mensik        @3,70 = Egito -3,5 (2,00) × Jakub Mensik -7,5 (1,85)
    Altrincham / Hurkacz  @3,02 = Altrincham +0,75 (2,10) × Hurkacz -5,5 (1,44)
    Virtanen /Sabalenka   @1,84 = Virtanen +7,5 (1,50) × Sabalenka +15,5 (1,23)
    Mezxa / Arsenal       @2,36 = A. G. **Meza** +6,5 (1,30) × **Arsenal** (1,82)

`Mezxa / Arsenal` é o caso que mata a hipótese antiga: "Meza" é tenista e o
Arsenal é clube de futebol — não é dado embaralhado, é uma dupla de duas
modalidades. **182 das 212 linhas da ERA 2 (86 %) têm a barra.**

**Consequência para o que já foi importado, e ela NÃO foi aplicada:** essas
linhas são bilhetes de 2 pernas, então a categoria deveria ser `Múltipla` (não
`ML`), e onde as duas pernas são de esportes diferentes o `MASTER_ESPORTES §2`
manda `Múltiplos`. **Não reclassifiquei porque não é decidível pelo título:**
`A / B` também pode ser um confronto de verdade (`Kostanay / Kaisar` são dois
clubes cazaques que se enfrentam), e sem o print não dá para separar os dois
casos. Fica como decisão, com o caminho medido: ou os prints do canal, ou ele
confirmando. **O P/L não é afetado** — stake, odd e resultado estão certos; o que
está errado é `esporte`/`aposta` num subconjunto dessas 182.

O ` // ` do `#19` (separador de bet builder) continua sendo o único separador de
seleção do sistema, e ele não aparece nesta fonte.

── A odd "aumentada" é a TURBINADA, não a do print ───────────────────────────

As 13 linhas `aumentada`/`booster` são o **Criar Aposta Turbinada** da Betano —
bet builder com bônus de odd. O bônus é pago **POR FORA da odd exibida**, mesma
família do `SuperMúltipla` da Estrela Bet (s303), e ele já registra a odd certa:

    Barcelona    print 2,18 +25% → 1 + 1,18 × 1,25 = 2,475   ele registrou 2,47 ✔
    Real Madrid  print 2,60 +25% → 1 + 1,60 × 1,25 = 3,000   ele registrou 3,00 ✔
    Arsenal      print 3,05 +25% → 1 + 2,05 × 1,25 = 3,562   ele registrou 3,05 ✘

O Arsenal é a exceção que confirma a regra: **é PERDIDA**, e em L o P/L é −stake
e não depende da odd, então ele não refez a conta. É exatamente o
`MASTER_RESULTADO` — em W a odd é `Retorno ÷ Stake`.

Confirmado por um terceiro caminho, o print com valor em R$: aposta R$557,00,
"Ganhos Potenciais" R$1.364,65 (= 557 × 2,45) e "Turbinada +50%" **+R$403,83**,
que é exatamente 50 % do lucro de R$807,65. Retorno real R$1.768,48 → odd
efetiva **3,175** = 1 + (2,45 − 1) × 1,5.

**Isto é requisito do bot:** planilhar a odd do print num bilhete turbinado
subestima toda vitória dele.

── ⚠️ A coluna `Esporte` NÃO é confiável ─────────────────────────────────────

**13 linhas de prop da NBA estão rotuladas `Futebol`** (`Kuminga 20 pt`,
`Derrick white 4+ 3pt`, `Bruce brown 5+ ass`, `Royce oneal 10+ reb`…). São erros
de digitação do tracker, não modalidade.

**Decisão do Feca (31/08/2026): CORRIGIR.** Elas vão para `Basquete` — o título
traz objeto inequívoco (`3pt`, `ass`, `reb`, `pt`, `DD`, `PAR`, `LL`). O padrão
do script é corrigir; `--nao-corrigir-esporte` volta ao verbatim. O DRY lista as
13, uma a uma, antes de qualquer escrita.

**A categoria, essa, nunca depende do rótulo.** A regra de prop de jogador roda
solta do esporte de propósito: presa ao rótulo, estas 13 cairiam em `ML` e o
import erraria DUAS colunas em vez de uma. Medido: a regra solta classifica 18
linhas como `Player Props` fora de Basquete e **nenhuma é falso positivo** (as 13
da NBA + 3 `G/A` de futebol + 2 de `aces` no tênis).

⚠️ **Há mais rótulo errado do que o script consegue detectar.** `Sakkari aces`
(tenista) está sob Futebol e não casa com a regra de NBA; os pares cruzados da
ERA 2 são indecidíveis sem saber qual metade é a certa. O script corrige o que
prova e deixa o resto como está.

── Esporte: grafia do BANCO, não a do arquivo ────────────────────────────────

O arquivo escreve em pt-PT. As grafias de destino foram MEDIDAS no banco
(`select esporte, count(*) from bilhetes group by 1`), não supostas:

    Basquetebol       178 → Basquete           (9.484 no banco)
    Ténis             105 → Tênis              (6.445)
    Futebol            87 → Futebol           (62.576)
    eSport              9 → E-Sports            (1.991)
    Beisebol            6 → Baseball            (1.293)   ⚠ ver abaixo
    Handebol            5 → Handebol              (108)
    Futebol americano   1 → Futebol Americano     (118)
    MMA                 1 → MMA                   (309)
    Voleibol            1 → Vôlei                 (829)

⚠️ `Beisebol` **existe no banco com 4 bilhetes** e mesmo assim mapeia para
`Baseball`: `Baseball` é o valor do `MASTER_ESPORTES §7` e tem 1.293 linhas.
Importar na grafia minoritária criaria esporte gêmeo na base dele.

── Múltiplas rotuladas `Simples` ─────────────────────────────────────────────

A coluna `Tipo` diz `Simples` nas 393, mas **22 títulos declaram combinação**: 9
combos explícitos (`Dupla wendell mark` @140 · `Multipla 26-04` @500 ·
`Bingo 28-04` @300 · `Dosunmu + Maxey bingo` @85 · `Reed/gobert dupla` @70 ·
`Dupla Lebron + reaves` @3,8 · `Dupla under cartoes` @1,82 · `Multipla 1` @4,93 ·
`Duas bets q eu pedi` @2,0) e 13 bet builders da Betano. As odds altas
confirmam: 500,0 não é aposta simples.

Todas ganham `aposta = Múltipla`. **Só `multipla`/`bingo` viram
`esporte = Múltiplos`**; `dupla` NÃO — o `MASTER_ESPORTES §2` reserva `Múltiplos`
para 3+ seleções de jogos diferentes, e "dupla" declara exatamente duas. Sem
saber quantas pernas tem um "bingo", a única leitura honesta do rótulo é
"acumulada grande" → 3+.

── Bet builder da Betano ─────────────────────────────────────────────────────

13 títulos terminam em `aumentada` / `aumento` / `booster` (`Real madrid
aumentada`, `Flamengo booster`). É o aumento de odd da Betano — bet builder do
MESMO jogo. Esporte **Futebol** (os 13 são de futebol) e categoria `Múltipla`,
porque bet builder é Múltipla mesmo com tudo do mesmo jogo. Mesmo precedente do
`import_passatips_xlsx.py`.

── Casa vazia em 126 linhas (32 %) → Betano ──────────────────────────────────

`Casa de apostas` está vazia em 126 das 393 (abril 68 · maio 22 · agosto 36).
Linha sem casa nasce **invisível no Painel de Contas** — a casa é a chave da
conta e entra na assinatura.

**Decisão do Feca (31/08/2026): as 126 são Betano.** Registro que isso
**contraria** o que a distribuição por mês sugeria — nas linhas que TÊM casa,
abril/maio é Bet365 (82 de 90) e só agosto é Betano (162 de 168). Quem sabe é o
dono da conta, não a estatística; fica escrito para ninguém "consertar" isso
depois achando que foi engano.

O padrão do script é `Betano` por causa dessa decisão. Passar `--casa-vazia ""`
faz o script **abortar** se houver linha sem casa — é a guarda para o dia em que
alguém apontar este script para outro arquivo.

── Casas ─────────────────────────────────────────────────────────────────────

As 3 grafias do arquivo batem EXATO com as do banco, medidas antes de escolher:
`Betano` (15.438) · `Bet365` (58.994) · `Pinnacle` (3.189). Nenhuma casa nova,
nenhum favicon a cadastrar. Casa fora do mapa entra **verbatim** (nunca
title-casear) e o DRY avisa.

── Numeração ─────────────────────────────────────────────────────────────────

Código `RG<aaaamm>-<n>`, na família do `PT` (PassaTips), `RC` (Rei do Criquete) e
`ZE` (Zora). O prefixo `RG` foi conferido como **livre** no banco (os únicos em
uso são `PT`, `RC`, `ZE` e um `BB` solitário). Numeração **mensal**, reiniciando
em 1, na ordem cronológica das linhas.

Isso não é cosmético: `repository._assinatura` com código é
`ID|casa|parceiro|codigo` — o CONTEÚDO não entra no hash. Numerar é o que faz o
bot, ao planilhar a próxima aposta do canal, casar com a linha certa em vez de
duplicar o histórico.

⚠️ **Ele vai usar o bot.** No dia em que o bot entrar, ele e esta planilha passam
a escrever na MESMA série `RG<aaaamm>-<n>`. Suba o contador (`/contador N` no
apoio) para além do último código gerado por este import ANTES da primeira
aposta, e decida qual é a fonte — a partir daí o bot planilha e isto vira
histórico congelado. O script ABORTA se um código que ele geraria já existir sob
outra origem.

── Decisões ──────────────────────────────────────────────────────────────────

- **Dono solo** — sem `OPERADORES`, sem dedup cruzada.
- **Tipster** = `RogerinComeuMeuSaldo` (nome de marca) em todas as linhas, como
  no PassaTips. A coluna `Tipster` do arquivo está vazia nas 393.
- **Uma conta `Padrão` por casa** — 1 linha por casa no Painel de Contas, cada
  uma com custo próprio.

── O que este script NÃO resolve ─────────────────────────────────────────────

- **As 2 odds de 0,500** (`Robinson 10+ pt`, `wendell carter jr 3+ 3pt`) são
  impossíveis para aposta real. As duas são `Perdida`, então o P/L é `−stake` e
  **não depende da odd** — entram como estão e saem listadas no relatório. Só
  ele sabe o valor certo; corrige-se na grade depois.
- **O confronto**, que não existe na fonte (ver Descrição).
- **Qual dos dois está errado** quando rótulo e título discordam (ver Esporte).

Uso:
    python scripts/import_rogerin_csv.py --csv "C:\\...\\sobolas.csv" --dono <username>
    python scripts/import_rogerin_csv.py --csv "C:\\...\\sobolas.csv" --dono <username> --go
"""
import argparse
import asyncio
import csv
import datetime as dt
import hashlib
import os
import re
import unicodedata
from collections import Counter, defaultdict

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
PARCEIRO = 'Padrão'
TIPSTER = 'RogerinComeuMeuSaldo'   # nome de MARCA (o username vai em --dono)
PREFIXO = 'RG'                     # código RG<aaaamm>-<n>; conferido livre no banco
ORIGEM = 'import'
VALID = {'W', 'L', 'V', 'HW', 'HL'}
DELIM = ';'
# Decisão do Feca (31/08/2026) para as 126 linhas sem casa. Ver docstring — ela
# contraria a distribuição por mês de propósito.
CASA_VAZIA_PADRAO = 'Betano'

# Cabeçalhos exatos do export (pt-PT). Se o tracker mudar o layout, o script
# aborta em vez de ler coluna errada em silêncio.
COL_DATA = 'Data'
COL_TIPO = 'Tipo'
COL_ESPORTE = 'Esporte'
COL_TITULO = 'Título da aposta'
COL_ODD = 'Cotação'
COL_STAKE = 'Valor'
COL_GANHO = 'Ganho'
COL_LUCRO = 'Lucro'
COL_ESTADO = 'Estado'
COL_CASA = 'Casa de apostas'
OBRIGATORIAS = (COL_DATA, COL_TIPO, COL_ESPORTE, COL_TITULO, COL_ODD, COL_STAKE,
                COL_GANHO, COL_LUCRO, COL_ESTADO, COL_CASA)


# ---------- sanitização de texto ----------
_CTRL = re.compile(r'[\x00-\x1f\x7f]+')


def limpa(v) -> str:
    if v is None:
        return ''
    # TAB é o separador de coluna do TSV de saída: se um nome vier com tab
    # literal, ele parte a linha inteira (a armadilha da Estrela Bet, s303).
    # _CTRL já cobre \t — a higienização é na FRONTEIRA, aqui.
    return re.sub(r'\s{2,}', ' ', _CTRL.sub(' ', str(v))).strip()


def _chave(s) -> str:
    """minúscula sem acento — casa rótulo pt-PT com grafia pt-BR
    (`Ténis`/`Tênis`, `Basquetebol`/`Basquete`)."""
    s = unicodedata.normalize('NFKD', limpa(s).lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def _k(s) -> str:
    """_chave sem espaço — casa nome com espaçamento livre."""
    return _chave(s).replace(' ', '')


# ---------- casa ----------
# As 3 grafias do arquivo batem EXATO com as do banco (medidas: Bet365 58.994,
# Betano 15.438, Pinnacle 3.189). Casa fora do mapa entra VERBATIM — nunca
# title-casear, que mutila nome e cria conta paralela — e o DRY avisa.
_CASA_MAP = {
    'bet365': 'Bet365',
    'betano': 'Betano',
    'pinnacle': 'Pinnacle',
}


def norm_casa(v, casa_vazia: str) -> str:
    bruto = limpa(v)
    if not bruto:
        return casa_vazia
    return _CASA_MAP.get(_k(bruto), bruto)


# ---------- esporte ----------
# Destino = grafia MEDIDA no banco, não a do arquivo. `Beisebol` existe no banco
# (4 linhas) e mesmo assim vai para `Baseball` (1.293, valor do §7): importar na
# grafia minoritária criaria esporte gêmeo.
_ESPORTE_MAP = {
    'basquetebol': 'Basquete',
    'tenis': 'Tênis',
    'futebol': 'Futebol',
    'esport': 'E-Sports',
    'esports': 'E-Sports',
    'beisebol': 'Baseball',
    'handebol': 'Handebol',
    'futebolamericano': 'Futebol Americano',
    'mma': 'MMA',
    'voleibol': 'Vôlei',
    'volei': 'Vôlei',
}


def norm_esporte(v) -> str:
    return _ESPORTE_MAP.get(_k(v), limpa(v) or 'Outro')


# `Multipla`/`Bingo` declaram acumulada grande → `Múltiplos` (§2: 3+ seleções de
# jogos diferentes). `Dupla` declara DUAS e por isso NÃO vira `Múltiplos` — só
# ganha a categoria `Múltipla`.
_RE_ACUMULADA = re.compile(r'\b(multipla|bingo)\b')
_RE_DUPLA = re.compile(r'\b(dupla|duas bets)\b')
# Bet builder da Betano ("aumento de odd"): mesmo jogo → esporte do jogo (§2).
_RE_BOOST = re.compile(r'\b(aumentad[ao]|aumento|booster|boost)\b')

# Objeto inequívoco de prop de jogador no título.
# `PAR` = pontos+assistências+rebotes; `LL` = lances livres; `DD` = double-double.
_RE_NBA = re.compile(
    r'\b\d+\s*\+?\s*(3pt|ass|assists?|assistt?s?|reb|rebs?|pts?|ll)\b'
    r'|\bdd\b|\bpar\b|\b3pt\b|\bassists?\b|\brebs?\b')


def _combo(titulo: str) -> str:
    """'acumulada' | 'dupla' | 'boost' | '' — lido do título."""
    d = _chave(titulo)
    if _RE_ACUMULADA.search(d):
        return 'acumulada'
    if _RE_DUPLA.search(d):
        return 'dupla'
    if _RE_BOOST.search(d):
        return 'boost'
    return ''


# ---------- categoria ----------
# `MASTER_APOSTAS §1`: a categoria registra o OBJETO da aposta, não o tipo de
# mercado. `MASTER_APOSTAS §5`: no basquete, pontos/rebotes/assistências de um
# JOGADOR são `Player Props`; total do jogo ou do time é `Pontos`.
_RE_TOTAL = re.compile(r'\b(over|under|mais de|menos de)\b|[+-]?\d+[.,]\d')
_TOTAL_POR_ESPORTE = {
    'Basquete': 'Pontos', 'Futebol Americano': 'Pontos', 'Vôlei': 'Pontos',
    'Futebol': 'Gols', 'Handebol': 'Gols',
    'Tênis': 'Games', 'Baseball': 'Corridas', 'E-Sports': 'E-Sports Props',
    'MMA': 'Rounds',
}


def norm_categoria(esporte: str, titulo: str, combo: str) -> str:
    d = _chave(titulo)

    # 1. Combinação — declarada no próprio título. Bet builder também é Múltipla.
    if combo:
        return 'Múltipla'

    # 2. OBJETO da aposta — vence sempre o tipo de mercado (§1).
    if re.search(r'escanteio|\bcantos?\b', d):
        return 'Escanteios'
    if re.search(r'\bcart(ao|oes)\b|expuls|vermelho', d):
        return 'Cartões'
    if re.search(r'\bshots?\b|chutes? no gol|no alvo', d):
        return 'Chutes no Gol'
    if re.search(r'\bchutes?\b|finaliza', d):
        return 'Chutes'
    if re.search(r'\bgols?\b', d):
        return 'Gols'
    if re.search(r'\bgames?\b', d):
        return 'Games'
    if re.search(r'\bkills?\b', d):
        return 'E-Sports Props'
    if re.search(r'\baces?\b|duplas? faltas?|break ?points?', d):
        return 'Player Props'          # §6 Tênis: aces / duplas faltas
    # `G/A` = "gol ou assistência" do jogador. É estatística individual, e o §5
    # manda estatística de JOGADOR para Player Props — a categoria `Gols` é do
    # total do jogo/time.
    if re.search(r'\bg\s*/\s*a\b', d):
        return 'Player Props'
    # Props de jogador: pontos/rebotes/assistências/3pt/DD/PAR de um NOME.
    # NÃO é gateado pelo esporte de propósito. A coluna `Esporte` do arquivo é
    # comprovadamente errada em 13 linhas (`Bruce brown 3+ ass` rotulada
    # Futebol), e prender a regra ao rótulo mandaria essas 13 para `ML` — errando
    # duas colunas em vez de uma. O objeto é estatística individual em qualquer
    # modalidade, então a categoria independe de quem rotulou o esporte.
    if _RE_NBA.search(d):
        return 'Player Props'
    if re.search(r'\bassi(st|t)\w*', d):
        return 'Assistência' if esporte == 'Futebol' else 'Player Props'
    if re.search(r'\brebotes?\b|\brebs?\b', d):
        return 'Player Props'
    if re.search(r'\bpontos?\b|\bpts\b', d):
        return 'Pontos'
    if re.search(r'\bsets?\b', d):
        return 'Sets'

    # 3. Mercados de RESULTADO (nenhum objeto próprio foi nomeado).
    if re.search(r'\bdc\b|dupla chance', d):
        return 'Dupla Chance'
    if re.search(r'\bdnb\b|empate anula', d):
        return 'DNB'
    if re.search(r'\bambas\b', d):
        return 'Ambas Marcam'
    if re.search(r'\bha\b|handicap|spread|[+-]\d+[.,]\d', d):
        return 'Handicap'
    if re.search(r'\bml\b|moneyline|vencedor|\bempate\b|vence\w*|vitoria', d):
        return 'ML'

    # 4. Sem objeto nomeado: com linha numérica é total (objeto padrão do
    #    esporte); sem linha, é nome solto — resultado.
    if _RE_TOTAL.search(d):
        return _TOTAL_POR_ESPORTE.get(esporte, 'Outros')
    return 'ML'


# ---------- data / stake / odd ----------
def _para_float(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = limpa(v).replace('R$', '').replace('\xa0', '').replace(' ', '')
    if not s:
        return None
    # O export usa PONTO decimal ("3.700", "1.00"). Vírgula aparece só em texto
    # livre, mas a guarda fica: se houver os dois, o ponto é milhar.
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def fmt_stake(v) -> str:
    n = _para_float(v)
    return '' if n is None else f'{n:.2f}'.replace('.', ',')


def _float_str(n: float) -> str:
    """Precisão completa (nunca truncar odd), vírgula decimal."""
    s = repr(float(n))
    if s.endswith('.0'):
        s = s[:-2]
    return s.replace(',', '').replace('.', ',')


def norm_odd(v) -> str:
    n = _para_float(v)
    return '' if n is None or n <= 0 else _float_str(n)


# `Ganha` → W · `Perdida` → L. O arquivo não tem mais nada (medido: 163 + 230 =
# 393). Os demais ficam mapeados para o dia em que ele registrar um void.
_RESULTADO_MAP = {
    'ganha': 'W', 'ganho': 'W', 'green': 'W',
    'perdida': 'L', 'perdido': 'L', 'red': 'L',
    'anulada': 'V', 'anulado': 'V', 'void': 'V', 'devolvida': 'V',
    'meio ganha': 'HW', 'meio perdida': 'HL',
}


def norm_resultado(v) -> str:
    r = _RESULTADO_MAP.get(_chave(v), _chave(v).upper())
    return r if r in VALID else ''


# ---------- carga do CSV ----------
def carregar_rows(csv_path: str, casa_vazia: str, corrigir_esporte: bool) -> list[dict]:
    # utf-8-sig: o export vem com BOM, e sem isto a 1ª coluna se chamaria
    # '\ufeffData' e o KeyError sairia só na leitura.
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        brutas = list(csv.DictReader(f, delimiter=DELIM))
    if not brutas:
        raise SystemExit(f'{csv_path}: nenhuma linha de dados.')
    faltando = [c for c in OBRIGATORIAS if c not in brutas[0]]
    if faltando:
        raise SystemExit(
            f'coluna(s) obrigatória(s) ausente(s): {faltando}\n'
            f'colunas do arquivo: {list(brutas[0])}\n'
            f'O layout do tracker mudou — revise o mapa antes de importar.')

    out: list[dict] = []
    for i, b in enumerate(brutas, start=2):          # 2 = linha do arquivo (1 é o cabeçalho)
        crua = limpa(b[COL_DATA])
        try:
            momento = dt.datetime.strptime(crua, '%d/%m/%Y %H:%M')
        except ValueError:
            raise SystemExit(f'linha {i}: data ilegível {crua!r} (esperado dd/mm/aaaa hh:mm)')
        titulo = limpa(b[COL_TITULO])
        esporte_bruto = limpa(b[COL_ESPORTE])
        esporte = norm_esporte(esporte_bruto)
        combo = _combo(titulo)

        # `Multipla`/`Bingo` = acumulada grande → esporte especial `Múltiplos`.
        # `Dupla` (2 seleções) e bet builder do MESMO jogo mantêm o esporte (§2).
        esporte_final = 'Múltiplos' if combo == 'acumulada' else esporte

        # Prop da NBA rotulada com o esporte errado (13 linhas medidas). Só move
        # quando o título é inequívoco; `--nao-corrigir-esporte` desliga.
        nba_fora = (esporte not in ('Basquete', 'eBasket', 'Múltiplos')
                    and combo == ''
                    and bool(_RE_NBA.search(_chave(titulo))))
        if nba_fora and corrigir_esporte:
            esporte_final = 'Basquete'

        out.append({
            'data': momento.strftime('%d/%m/%Y'),
            '_dt': momento,
            '_linha': i,
            'esporte': esporte_final,
            'tipster': TIPSTER,
            'casa': norm_casa(b[COL_CASA], casa_vazia),
            'parceiro': PARCEIRO,
            'aposta': norm_categoria(esporte_final, titulo, combo),
            'descricao': titulo,
            'stake': fmt_stake(b[COL_STAKE]),
            'odd': norm_odd(b[COL_ODD]),
            'resultado': norm_resultado(b[COL_ESTADO]),
            '_lucro': _para_float(b[COL_LUCRO]),     # conferência do DRY
            '_ganho': _para_float(b[COL_GANHO]),
            '_esporte_bruto': esporte_bruto,
            '_casa_bruta': limpa(b[COL_CASA]),
            '_tipo': limpa(b[COL_TIPO]),
            '_combo': combo,
            '_nba_fora': nba_fora,
        })
    # O export vem do mais recente para o mais antigo; a numeração é cronológica.
    out.sort(key=lambda r: (r['_dt'], r['_linha']))
    return numerar(out)


def numerar(rows: list[dict]) -> list[dict]:
    """Código RG<aaaamm>-<n>. Numeração MENSAL (reinicia em 1 a cada mês), na
    ordem cronológica."""
    contador: dict[str, int] = defaultdict(int)
    for r in rows:
        mes = f"{r['_dt']:%Y%m}"
        contador[mes] += 1
        r['codigo'] = f'{PREFIXO}{mes}-{contador[mes]}'
        r['_mes'] = mes
    return rows


# ---------- assinatura (idêntica a repository._assinatura) ----------
# COM código o hash é `ID|casa|parceiro|codigo` — o CONTEÚDO não entra. É o que
# faz o bot casar a linha certa quando reprocessar o mesmo número.
def assinatura(r: dict) -> str:
    raw = '|'.join(['ID', r['casa'], r['parceiro'], r['codigo']])
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def estado_extracao(resultado: str, odd: str) -> str:
    """Espelha repository.estado_extracao: desde a s259 a odd só é exigida onde o
    P/L depende dela (W/HW); L/V/HL nascem `resolvida`."""
    if resultado not in VALID:
        return 'aberta'
    if resultado in ('W', 'HW'):
        return 'resolvida' if (_para_float(odd) or 0) > 0 else 'aberta'
    return 'resolvida'


def carregar_env():
    for line in open(ENV_PATH, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# ---------- escrita ----------
async def importar(rows: list[dict], dono: str):
    import asyncpg
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    casas = sorted({r['casa'] for r in rows})

    # ── O DONO É CONFERIDO NA TABELA, nunca deduzido (s260) ──────────────────
    # `dono` errado não dá erro: dá tela vazia para o usuário certo, e os
    # bilhetes ficam sob um nome que ninguém acessa.
    conn = await asyncpg.connect(url, command_timeout=120)
    try:
        u = await conn.fetchrow(
            'SELECT username, status, length(senha_hash) AS h, bot_habilitado '
            'FROM usuarios WHERE username = $1', dono)
        if not u:
            parecidos = await conn.fetch(
                "SELECT username, status FROM usuarios "
                "WHERE username ILIKE '%' || $1 || '%' ORDER BY username", dono[:4])
            raise SystemExit(
                f'✋ ABORTADO — username {dono!r} NÃO existe na tabela `usuarios`.\n'
                f'   O `dono` é o USERNAME do cadastro, não a marca nem o nome do '
                f'arquivo.\n'
                f'   Parecidos: {[dict(p) for p in parecidos] or "nenhum"}')
        if u['status'] != 'ativo':
            raise SystemExit(
                f'✋ ABORTADO — {dono!r} está com status {u["status"]!r}. '
                f'Aprove a conta em /admin antes de importar.')
        print(f'  dono conferido: {dono} | status={u["status"]} | '
              f'hash={u["h"]} chars | bot_habilitado={u["bot_habilitado"]}')

        ja = await conn.fetchval('SELECT COUNT(*) FROM bilhetes WHERE dono=$1', dono)
        print(f'  base atual de {dono}: {ja} bilhete(s)')

        # ── GUARD DE COLISÃO COM O BOT ──────────────────────────────────────
        # Planilha e bot escrevem na MESMA série `RG<aaaamm>-<n>`, e o código
        # entra na assinatura. Quem escreveu antes tem precedência; o conserto
        # (subir o contador do bot) é decisão humana, não palpite do script.
        colisoes = await conn.fetch(
            'SELECT codigo_bilhete, casa, descricao, origem FROM bilhetes '
            'WHERE dono = $1 AND origem <> $2 AND codigo_bilhete = ANY($3::text[]) '
            'ORDER BY codigo_bilhete',
            dono, ORIGEM, [r['codigo'] for r in rows])
    finally:
        await conn.close()

    if colisoes:
        print(f'\n✋ ABORTADO — {len(colisoes)} código(s) que este import geraria já '
              f'existem na base, gravados por OUTRA origem (o bot):')
        for c in colisoes:
            print(f"    {c['codigo_bilhete']} | {c['casa']} | {c['descricao'][:50]} "
                  f"| origem={c['origem']}")
        raise SystemExit(
            'Sobrescrever isso apagaria aposta que o bot planilhou. Suba o contador do '
            'bot (/contador N no apoio) para além do último código da planilha e rode '
            'de novo.')

    registros = [(
        dono, r['casa'], r['parceiro'], assinatura(r), r['codigo'],
        r['data'], r['esporte'], r['tipster'], r['aposta'], r['descricao'],
        r['stake'], r['odd'], r['resultado'] or None,
        estado_extracao(r['resultado'], r['odd']),
        None, None, ORIGEM,                       # confianca, stake_usd, origem
    ) for r in rows]

    last_err = None
    for tentativa in range(1, 4):
        try:
            conn = await asyncpg.connect(url, command_timeout=120)
            try:
                async with conn.transaction():
                    # idempotente: reimportar não acumula (limpa só o que ESTE
                    # import escreveu — captura do bot/extensão tem outra origem)
                    apagadas = await conn.execute(
                        'DELETE FROM bilhetes WHERE dono=$1 AND origem=$2', dono, ORIGEM)
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
                    # uma conta `Padrão` POR CASA: 1 linha por casa no Painel de
                    # Contas, cada uma com custo próprio
                    for casa in casas:
                        await conn.execute(
                            'INSERT INTO parceiros (dono, casa, nome) VALUES ($1,$2,$3) '
                            'ON CONFLICT (dono, casa, nome) DO NOTHING',
                            dono, casa, PARCEIRO)
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
                        """, dono, ORIGEM)
                n = await conn.fetchval('SELECT COUNT(*) FROM bilhetes WHERE dono=$1', dono)
                nc = await conn.fetchval(
                    'SELECT COUNT(DISTINCT casa) FROM parceiros WHERE dono=$1', dono)
                np = await conn.fetchval('SELECT COUNT(*) FROM parceiros WHERE dono=$1', dono)
                print(f'\nOK — bilhetes dono={dono}={n} | casas={nc} | contas={np}')
                print(f'\n⚠ ÚLTIMO CÓDIGO GRAVADO: {rows[-1]["codigo"]}. Antes da 1ª aposta '
                      f'pelo bot, suba o contador (/contador N no apoio) para além dele — '
                      f'planilha e bot escrevem na MESMA série.')
                return
            finally:
                await conn.close()
        except Exception as e:                       # noqa: proxy instável → retry
            last_err = e
            print(f'  [tentativa {tentativa}] falhou: {type(e).__name__}: {e}')
    raise SystemExit(f'import falhou após 3 tentativas: {last_err}')


# ---------- relatório do DRY ----------
def _pl_derivado(stake: str, odd: str, res: str):
    s = _para_float(stake) or 0.0
    o = _para_float(odd)
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


def _relatorio(rows: list[dict], dono: str, casa_vazia: str, corrigir_esporte: bool):
    print(f'DONO={dono!r} | tipster={TIPSTER!r} | conta={PARCEIRO!r} por casa | '
          f'linhas: {len(rows)}')
    datas = sorted(r['_dt'] for r in rows)
    print(f'período: {datas[0]:%d/%m/%Y} → {datas[-1]:%d/%m/%Y} | '
          f'códigos {rows[0]["codigo"]} … {rows[-1]["codigo"]}')

    print('\n— por mês —')
    for mes in sorted({r['_mes'] for r in rows}):
        sub = [r for r in rows if r['_mes'] == mes]
        print(f'  {mes}  {len(sub):>4} | {sub[0]["codigo"]} … {sub[-1]["codigo"]}')

    for campo in ('casa', 'esporte', 'aposta'):
        print(f'\n{campo}:', dict(Counter(r[campo] for r in rows).most_common()))
    print('\nresultado:',
          dict(Counter(r['resultado'] or '(aberta)' for r in rows).most_common()))
    print('extraction_state:', dict(Counter(
        estado_extracao(r['resultado'], r['odd']) for r in rows)))

    novas = {r['casa'] for r in rows} - set(_CASA_MAP.values())
    if novas:
        print(f'\n⚠ casa(s) fora do mapa, gravadas VERBATIM: {sorted(novas)} — '
              f'cada uma precisa de favicon nos 3 mapas (index.html, data.js, '
              f'inicio.html).')

    n_vazia = sum(1 for r in rows if not r['_casa_bruta'])
    if n_vazia:
        por_mes = Counter(r['_mes'] for r in rows if not r['_casa_bruta'])
        print(f'\n⚠ {n_vazia} linha(s) sem casa no arquivo → gravadas como '
              f'{casa_vazia!r} (decisão do Feca; a distribuição por mês sugeria '
              f'outra coisa — ver docstring).')
        print(f'   distribuição por mês: {dict(sorted(por_mes.items()))}')

    fora = [r for r in rows if r['_nba_fora']]
    if fora:
        estado = 'CORRIGIDAS para Basquete' if corrigir_esporte else 'mantidas VERBATIM'
        print(f'\n⚠ {len(fora)} linha(s) com objeto de prop de jogador e esporte '
              f'rotulado diferente — {estado}:')
        for r in fora:
            print(f'    {r["codigo"]:<14} {r["data"]} | rótulo={r["_esporte_bruto"]:<12} '
                  f'→ {r["esporte"]:<10} | {r["descricao"][:45]}')

    combos = [r for r in rows if r['_combo']]
    if combos:
        print(f'\n⚠ {len(combos)} linha(s) declaram combinação no título, embora a '
              f'coluna Tipo diga {combos[0]["_tipo"]!r}:')
        for r in combos:
            print(f'    {r["codigo"]:<14} {r["data"]} | {r["_combo"]:<9} | '
                  f'{r["esporte"]:<10} {r["aposta"]:<10} | @{r["odd"]:<8} | '
                  f'{r["descricao"][:40]}')

    odd_ruim = [r for r in rows if (_para_float(r['odd']) or 0) < 1.01]
    if odd_ruim:
        print(f'\n⚠ {len(odd_ruim)} linha(s) com odd < 1,01 (impossível para aposta '
              f'real, exceto cashout):')
        for r in odd_ruim:
            pl = _pl_derivado(r['stake'], r['odd'], r['resultado'])
            nota = ('cashout: retorno < stake com Estado=Ganha '
                    '(MASTER_RESULTADO §5.6, odd = cashout ÷ stake)'
                    if r['resultado'] == 'W' else
                    'PERDIDA — o P/L é −stake e NÃO depende da odd; corrigir na grade')
            print(f'    {r["codigo"]:<14} {r["data"]} | {r["descricao"][:35]:<35} | '
                  f'@{r["odd"]} u={r["stake"]} {r["resultado"]} P/L={pl:+.2f} | {nota}')

    sem_odd = [r for r in rows if not r['odd']]
    if sem_odd:
        print(f'\n⚠ {len(sem_odd)} linha(s) sem odd')
    sem_stake = [r for r in rows if (_para_float(r['stake']) or 0) <= 0]
    if sem_stake:
        print(f'\n⚠ {len(sem_stake)} linha(s) com stake 0 ou vazio: gravadas, porém '
              f'INVISÍVEIS no dashboard (dashboard_rows corta stake <= 0)')

    sigs = [assinatura(r) for r in rows]
    cods = [r['codigo'] for r in rows]
    print(f'\ncódigos: {len(set(cods))} únicos de {len(cods)}')
    print(f'assinaturas: {len(set(sigs))} únicas de {len(sigs)}')

    # Conferência contra as colunas Ganho/Lucro da própria fonte, linha a linha:
    # se o P/L derivado divergir, a normalização (odd, stake, resultado) quebrou.
    liq = [r for r in rows if r['resultado']]
    div = [r for r in liq
           if (v := _pl_derivado(r['stake'], r['odd'], r['resultado'])) is None
           or abs(v - (r['_lucro'] or 0)) > 0.02]
    print(f'\nP/L derivado × coluna "Lucro" do arquivo: '
          f'{len(div)} divergência(s) em {len(liq)} liquidadas')
    for r in div[:12]:
        print(f'    {r["codigo"]} | {r["data"]} | {r["resultado"]} | '
              f'{r["descricao"][:38]} | u={r["stake"]} @{r["odd"]} | '
              f'arquivo={r["_lucro"]} | derivado='
              f'{_pl_derivado(r["stake"], r["odd"], r["resultado"])}')

    turnover = sum(_para_float(r['stake']) or 0 for r in rows)
    pl = sum(v for r in liq
             if (v := _pl_derivado(r['stake'], r['odd'], r['resultado'])) is not None)
    print(f'\nturnover total (u):      {turnover:>10,.2f}')
    print(f'P/L total (u):           {pl:>+10,.2f}')
    print(f'ROI:                     {100 * pl / turnover if turnover else 0:>+9.2f}%')

    # As duas ERAS não se parecem — quem for ler o histórico depois precisa saber
    # que está olhando duas amostras, não uma (regra "assinatura tem ERA").
    print('\n— por era —')
    for nome, ini, fim in (('ERA 1 (props NBA)', dt.datetime(2026, 1, 1), dt.datetime(2026, 7, 1)),
                           ('ERA 2 (multiesporte)', dt.datetime(2026, 7, 1), dt.datetime(2030, 1, 1))):
        sub = [r for r in rows if ini <= r['_dt'] < fim]
        if not sub:
            continue
        t = sum(_para_float(r['stake']) or 0 for r in sub)
        p = sum(v for r in sub
                if (v := _pl_derivado(r['stake'], r['odd'], r['resultado'])) is not None)
        g = sum(1 for r in sub if r['resultado'] == 'W')
        print(f'  {nome:<22} {len(sub):>4} apostas | {t:>7,.2f}u | {p:>+7,.2f}u | '
              f'ROI {100 * p / t if t else 0:>+6.2f}% | green {g} '
              f'({100 * g / len(sub):.1f}%)')

    print('\n— amostra (10 primeiras) —')
    for r in rows[:10]:
        print(f'  {r["codigo"]:<14} {r["data"]} | {r["esporte"]:<10} | '
              f'{r["aposta"]:<13} | {r["casa"]:<9} | {r["descricao"][:38]:<38} | '
              f'u={r["stake"]:<6} @{r["odd"]:<8} {r["resultado"]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--csv', required=True, help='caminho do sobolas.csv')
    ap.add_argument('--dono', required=True,
                    help='USERNAME do cadastro (conferido em `usuarios`; NÃO é a marca)')
    ap.add_argument('--casa-vazia', default=CASA_VAZIA_PADRAO,
                    help=f'casa para as linhas sem `Casa de apostas` '
                         f'(padrão {CASA_VAZIA_PADRAO!r}, decisão do Feca em 31/08/2026; '
                         f'passe "" para abortar em vez de preencher)')
    ap.add_argument('--nao-corrigir-esporte', action='store_true',
                    help='mantém VERBATIM as props da NBA rotuladas com outro esporte '
                         '(o padrão é corrigi-las para Basquete)')
    ap.add_argument('--go', action='store_true', help='escreve no banco (default: DRY)')
    a = ap.parse_args()

    corrigir = not a.nao_corrigir_esporte
    rows = carregar_rows(a.csv, a.casa_vazia, corrigir)

    # Guarda para o dia em que alguém apontar este script para outro arquivo:
    # linha sem casa nasce invisível no Painel de Contas (a casa é a chave da
    # conta e entra na assinatura), e preencher por dedução inventa conta.
    n_vazia = sum(1 for r in rows if not r['_casa_bruta'])
    if n_vazia and not a.casa_vazia:
        por_mes = Counter(r['_mes'] for r in rows if not r['_casa_bruta'])
        raise SystemExit(
            f'✋ ABORTADO — {n_vazia} de {len(rows)} linha(s) vêm SEM casa no arquivo '
            f'(por mês: {dict(sorted(por_mes.items()))}).\n'
            f'   Linha sem casa nasce invisível no Painel de Contas: a casa é a chave '
            f'da conta e entra na assinatura.\n'
            f'   Passe --casa-vazia "<Casa>" com o que o dono confirmar.')

    _relatorio(rows, a.dono, a.casa_vazia, corrigir)

    if not a.go:
        print('\n[DRY] nada foi escrito. Use --go para gravar.')
        return
    carregar_env()
    asyncio.run(importar(rows, a.dono))


if __name__ == '__main__':
    main()
