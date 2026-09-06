# -*- coding: utf-8 -*-
"""Importa a base do tipster **Grego Tips - VIP** (`gregotips.csv`) — 8º tipster
público, em `/tipsters/gregotipsvip`.

⚠️ O `dono` é o **username do cadastro** (`gregozxrd`, alyssongrego587@gmail.com),
não a marca e não o nome do arquivo. Foi conferido na tabela `usuarios` antes de
qualquer escrita — cadastro por autosserviço em 06/09/2026, aprovado para `ativo`
na mesma sessão. É a regra da s260: `dono` errado não dá erro, dá **tela vazia**
para o usuário certo. A ponte entre marca e username é o registro
`TIPSTERS_PUBLICOS` (`app/main.py`).

── Fonte ─────────────────────────────────────────────────────────────────────

O MESMO tracker do Rogerin (`import_rogerin_csv.py`): export pt-PT (`Cotação`,
`Ténis`, `Bónus`), CSV com `;`, aspas em tudo, UTF-8 com BOM. **956 linhas, 24
colunas, 01/08/2026 → 01/09/2026.** Treze colunas estão vazias nas 956; sobram
9 com informação, e **nenhuma diz o mercado** — a categoria sai da leitura do
título, como no Rogerin.

    Data | Tipo | Esporte | Título da aposta | Cotação | Valor | Ganho | Lucro |
    Estado | Casa de apostas | (+ 13 vazias) | Tipo de aposta

`Tipo de aposta` é o único extra preenchido, em 86 linhas (`Anytimes e Assists`
62, `Props` 24). Não é usado: é rótulo de pasta do tracker, mais pobre que o
título, e nas 870 restantes não existe.

**A planilha é aritmeticamente consistente, e isso foi MEDIDO:** `Ganho` bate com
`Cotação × Valor` nas 267 ganhas (0 divergências) e `Lucro = Ganho − Valor` em
todas menos as 14 reembolsadas (onde `Lucro = 0`, que é o void). O `_relatorio`
refaz essa conta linha a linha, então erro de normalização (odd com separador
trocado, resultado mal lido) aparece como divergência em vez de passar calado.

── O gabarito público de agosto ──────────────────────────────────────────────

Ele publicou o fechamento no canal em 01/09 (`📊GREGO VIP: AGOSTO — P/L +127.84u
· ROI 13.02% · Apostas: 924`). Este script, lendo só o CSV, deriva **924
apostas, +127,73u, ROI 13,00%** em agosto. A diferença de 0,11u é o
arredondamento a centavo da coluna `Ganho`, acumulado em 267 vitórias — o
derivado usa a odd inteira. É uma conferência CONTRA FONTE EXTERNA, mais forte
que a reconciliação interna: o número saiu da boca do dono antes de existir
import.

── Stake: ele escreve `%`, o tracker escreve número ──────────────────────────

No canal a stake é **percentual da banca** (`1.25%`); no CSV é o mesmo número na
coluna `Valor` (0,25 a 3,00). Entra como **unidade**, igual a SoChutes, Fleury,
Rei do Criquete, PassaTips, Rogerin e Soh Props — o P/L do dashboard é em
unidades. A gestão declarada por ele é de 175u (msg de 31/07).

── Resultado: três estados, e o terceiro é void ──────────────────────────────

    Ganha (267) → W        Perdida (675) → L        Reembolsada (14) → V

As 14 reembolsadas têm `Ganho = 0` **e** `Lucro = 0`: o dinheiro voltou. É void,
não derrota — `MASTER_RESULTADO §5.1.2` manda `V` com a odd exibida, e é o que o
mapa faz. Nenhum cashout disfarçado nesta base (não há `Ganha` com retorno menor
que a stake: as 267 batem `odd × stake` exato).

── Casa: 6 linhas sem casa, resolvidas PELO CANAL ────────────────────────────

Linha sem casa nasce invisível no Painel de Contas (a casa é a chave da conta e
entra na assinatura). O Rogerin resolveu isso com uma decisão do Feca; **aqui a
resposta estava medida no export do Telegram** (`ChatExport_2026-09-06`), nas
mensagens que ele mesmo postou naquele dia:

    Nesta Elphege chutes 3+/4+/5+   01/09  → Bet365   (msg 938, 01/09 12:39)
    Forson +2 Chutes / +3 Chutes    01/09  → Bet365   (msg 940, 01/09 14:41)
    Summerville Ast                 01/09  → Betano   (msg 942, 01/09 14:53)

O mapa `_CASA_POR_TITULO` é fechado e casado por (data, título): título que não
estiver nele e vier sem casa **aborta** o script. Nunca chutar casa — casa errada
não dá erro, dá conta paralela.

Grafias de destino MEDIDAS no banco antes de escolher (`select casa, count(*)`):

    Betano 485 → Betano (18.580)      Bet365 301 → Bet365 (65.539)
    BetMGM  71 → BetMGM (628)         Novibet 49 → Novibet (2.069)
    Betnacional 23 → (1.696)          Superbet 6 → (7.681)
    KTO      5 → KTO (539)            BetFair 3 → **Betfair** (3.157)
    Rei do Pitaco 2 → **Pitaco** (443)  EstrelaBet 1 → **Estrela Bet** (112)
    ApostaGanha   1 → **Aposta Ganha** (61)

⚠️ **`Betsson` (3 linhas) é casa NOVA no banco** — 0 bilhetes em qualquer dono.
Entra verbatim (nunca title-casear) e precisa de favicon nos mapas do front
(`index.html`, `data.js` com `CASA_ICONS` **e** `HOUSE_DOMAIN`, `inicio.html`).
O DRY avisa.

── Categoria: o objeto sai do título, e três leituras são load-bearing ───────

A carteira é quase toda **prop de jogador de futebol** (Chutes 467 · Anytime 212
· Desarmes 30 · Faltas 29 · Assistência 25 · SOT/SOA 9), e três regras não são
óbvias:

1. **`<Nome> +2 Gols` é `Anytime`, não `Gols`.** O `MASTER_APOSTAS §3 Anytime`
   é explícito: "para marcar 2 ou mais gols (marcador 2+)" pertence à família
   Anytime, e o limiar vai na descrição. As odds confirmam (11,0 a 81,0 — total
   de jogo não paga isso), e o canal mostra a escada: `Tresoldi Anytime 1.50%` +
   `Tresoldi +2 Gols 0.50%`, mesmo jogador. `Gols` fica com o que é do JOGO:
   `Gol em ambos os tempos`, `próximo gol`, linha decimal (`2.5 gols`).

2. **`25%` / `50%` no começo do título é odd TURBINADA, não mercado.** É o
   aumento de odd da Betano — mesma família do `aumentada` do Rogerin (s306) e do
   `SuperMúltipla` da Estrela Bet (s303). Ele escreve a conta no canal:
   `2.02 + 25% = 2,27@` (msg 532) e `só vale com 25% odd final @2.93` (msg
   sobre `Fluminense ht`). São 26 linhas, todas bet builder → `Múltipla`.

3. **` e ` separa PERNAS.** 12 títulos combinam sem dizer "dupla"
   (`Peyton Miller chutes 1+ e Jack Harrison chutes 2+`, `Haland anytime e city
   vencer`, `Priske e Tolaj` @24,96). Viram `Múltipla`. Com 3 pernas declaradas
   (`A, B e C`, `tripla`, `multipla`) o esporte vira `Múltiplos` (§2); com duas,
   o esporte do arquivo é mantido.

**`SOA` = "score or assist" — marcar OU assistir** (respondido pelo Feca em
06/09/2026, vindo do tipster). São 5 linhas, e elas vão para `Player Props`,
junto com o `G/A` do mesmo arquivo: é o mesmo mercado escrito de dois jeitos, o
`§3` não tem categoria para ele, e escolher `Anytime` ou `Assistência` sozinhas
jogaria metade do mercado fora.

⚠️ **A primeira leitura foi `Chutes no Gol`, e estava errada.** A inferência era
razoável e mesmo assim falhou: `SOA` e `SOT` aparecem na MESMA escada e os dois
pareados com `Anytime` (`Kvam SOA 2.00%` + `Kvam Anytime 1.00%`, msg de 06/08),
o que fazia `SOA` parecer variação de `SOT`. Vizinhança tipográfica não é
significado — **sigla que não aparece por extenso em lugar nenhum do export só
se resolve perguntando ao dono.** Ficou marcada como inferência declarada no
relatório, que foi o que fez a pergunta acontecer.

**Defesas de goleiro → `Player Props`** (10 linhas): não há categoria própria no
`MASTER_APOSTAS §3` para defesa, mesmo precedente do `import_sohprops_csv.py`.

**`Nome N+` sem objeto → `Player Props`**, nunca o total do esporte. São ~20
linhas em que ele omitiu o mercado (`Julio Enciso 3+`, `Sebastian 2+`), e o canal
também as postou sem mercado — não é decidível. `Player Props` é a gaveta certa
(`§3: Props / Aposta do jogador`); mandá-las para `Gols` (o total do futebol)
inventaria um objeto que ninguém escreveu. Quatro casos em que o canal DIZ o
mercado estão em `_MERCADO_POR_TITULO`, com a mensagem citada.

── Descrição: VERBATIM, com os erros de digitação ────────────────────────────

O `Título da aposta` é texto livre digitado à mão e vai como está
(`Braiz Mendez`, `hadeyn`, `tZOLIS`) — o `MASTER_DESCRICAO §1` proíbe inventar
informação, e "corrigir" nome por palpite é inventar. Mesmo precedente do
`import_passatips_xlsx.py` e do `import_rogerin_csv.py`.

**Duas limpezas, e nenhuma delas é reescrita:** um `-` solto no fim (12 linhas,
`Priske +2 Gols -`) e um `- <número>` final **quando o número é exatamente a
stake da linha** (1 linha, `Forson +2 Chutes - 1.50`, u=1,50) — é a stake
vazando para dentro do título, não informação. O corte é condicionado à
igualdade de propósito: `cruzeiro -1` (stake 2,50) é handicap e **fica
intocado**.

O confronto não existe em coluna nenhuma e por isso não entra na descrição — o
`MASTER_DESCRICAO §2` pede `Entidade - Mercado [Confronto]`, e fabricar o
terceiro termo seria pior que omiti-lo.

── Numeração ─────────────────────────────────────────────────────────────────

Código `GV<aaaamm>-<n>`, mensal, reiniciando em 1 na ordem cronológica.

⚠️ **O prefixo foi conferido com `LIKE` sobre a coluna INTEIRA**, não contra o
formato da série (regra da s316): `GR` (233), `GT` (35), `GG` (8), `GX` (35) e
`GP` (34) estão todos ocupados por **código NATIVO da bet365**
(`GR3383912251I`), que também é duas letras mais dígitos e que um regex ancorado
em `XX<aaaamm>-<n>` não enxerga. `GV` é o único par com G livre: **0 linhas**.

Numerar não é cosmético: `repository._assinatura` com código é
`ID|casa|parceiro|codigo` — o conteúdo não entra no hash. É o que faz o bot, ao
planilhar a próxima aposta do canal, casar com a linha certa em vez de duplicar
o histórico. **Ele vai usar o bot** (canal `-1003928624343`, apoio
`-5577016989`): no dia em que o bot entrar, suba o contador (`/contador N` no
apoio) para além do último código deste import, ANTES da primeira aposta, e
decida qual é a fonte. O script ABORTA se um código que ele geraria já existir
sob outra origem.

── Decisões ──────────────────────────────────────────────────────────────────

- **Dono solo** — sem `OPERADORES`, sem dedup cruzada.
- **Tipster** = `Grego Tips - VIP` (nome de marca, escolhido pelo Feca em
  06/09/2026) em todas as linhas. A coluna `Tipster` do arquivo está vazia.
- **Uma conta `Padrão` por casa** — 1 linha por casa no Painel de Contas, cada
  uma com custo próprio.

── O que este script NÃO resolve ─────────────────────────────────────────────

- **O mercado das ~20 linhas `Nome N+`** — nem o canal diz (ver acima).
- **O confronto**, que não existe na fonte.
- **Esporte de múltipla mista.** As 4 linhas `ML <time> e <tenista>` (22/08)
  cruzam futebol e tênis, e o §2 pediria `Múltiplos`; o arquivo as rotula
  `Futebol` e separar time de tenista exigiria conhecer os nomes. Ficam como
  `Futebol`/`Múltipla` e saem listadas no DRY.

Uso:
    python scripts/import_grego_csv.py --csv "C:\\...\\gregotips.csv" --dono gregozxrd
    python scripts/import_grego_csv.py --csv "C:\\...\\gregotips.csv" --dono gregozxrd --go
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
TIPSTER = 'Grego Tips - VIP'       # nome de MARCA (o username vai em --dono)
PREFIXO = 'GV'                     # código GV<aaaamm>-<n>; conferido livre no banco
ORIGEM = 'import'
VALID = {'W', 'L', 'V', 'HW', 'HL'}
DELIM = ';'

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
    (`Ténis`/`Tênis`)."""
    s = unicodedata.normalize('NFKD', limpa(s).lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def _k(s) -> str:
    """_chave sem espaço — casa nome com espaçamento livre."""
    return _chave(s).replace(' ', '')


# ---------- casa ----------
# Destino = grafia MEDIDA no banco, não a do arquivo (ver docstring). Casa fora
# do mapa entra VERBATIM — nunca title-casear, que mutila nome e cria conta
# paralela — e o DRY avisa.
_CASA_MAP = {
    'bet365': 'Bet365',
    'betano': 'Betano',
    'betmgm': 'BetMGM',
    'novibet': 'Novibet',
    'betnacional': 'Betnacional',
    'superbet': 'Superbet',
    'kto': 'KTO',
    'betfair': 'Betfair',           # arquivo escreve `BetFair`; banco tem 3.157 `Betfair`
    'betsson': 'Betsson',           # ⚠ casa NOVA no banco (0 bilhetes) — precisa de favicon
    'reidopitaco': 'Pitaco',        # banco tem 443 sob `Pitaco`
    'estrelabet': 'Estrela Bet',    # banco tem 112 sob `Estrela Bet`
    'apostaganha': 'Aposta Ganha',  # banco tem 61 sob `Aposta Ganha`
}

# As 6 linhas sem casa no arquivo, resolvidas pelo export do Telegram (mensagem
# citada). Chave: (dd/mm/aaaa, título). Título sem casa e fora deste mapa ABORTA
# o script — casa chutada não dá erro, dá conta paralela.
_CASA_POR_TITULO = {
    ('01/09/2026', 'Nesta Elphege chutes 3+'): 'Bet365',   # msg 938, 01/09 12:39
    ('01/09/2026', 'Nesta Elphege chutes 4+'): 'Bet365',   # msg 938
    ('01/09/2026', 'Nesta Elphege chutes 5+'): 'Bet365',   # msg 938
    ('01/09/2026', 'Forson +2 Chutes - 1.50'): 'Bet365',   # msg 940, 01/09 14:41
    ('01/09/2026', 'Forson +3 Chutes'): 'Bet365',          # msg 940
    ('01/09/2026', 'Summerville Ast'): 'Betano',           # msg 942, 01/09 14:53
}


def norm_casa(v, data: str, titulo: str) -> str:
    bruto = limpa(v)
    if bruto:
        return _CASA_MAP.get(_k(bruto), bruto)
    achada = _CASA_POR_TITULO.get((data, titulo))
    if not achada:
        raise SystemExit(
            f'✋ ABORTADO — linha sem casa e fora do mapa: {data} {titulo!r}.\n'
            f'   A casa é a chave da conta e entra na assinatura: linha sem ela '
            f'nasce invisível no Painel de Contas.\n'
            f'   Ache a mensagem dela no export do Telegram e acrescente a '
            f'_CASA_POR_TITULO, citando a msg. Nunca chutar.')
    return achada


# ---------- esporte ----------
# Destino = grafia MEDIDA no banco (`Futebol` 72.894, `Tênis` 6.777).
_ESPORTE_MAP = {
    'futebol': 'Futebol',
    'tenis': 'Tênis',
    'basquetebol': 'Basquete',
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


# ---------- combinação ----------
# Acumulada DECLARADA (3+ seleções) → esporte `Múltiplos` (§2). `dupla` declara
# duas e por isso NÃO vira `Múltiplos` — só ganha a categoria `Múltipla`.
_RE_ACUMULADA = re.compile(r'\b(tripla|multipla|bingo)\b')
_RE_DUPLA = re.compile(r'\bduplas?\b')
# `25% flamengo e botafogo`, `50% flamengo x cruzeiro`: odd turbinada da Betano
# (bet builder do MESMO jogo). São 24 títulos, todos 25 ou 50.
# ⚠ O `%` tem DOIS papéis nesta fonte: em 2 títulos ele é a própria STAKE
# vazando (`Cuevas Christian Chutes +2 0.50%`, u=0,50) — e essas duas são
# `Chutes` simples, não bet builder. Quem separa os papéis é `norm_descricao`,
# que corta o sufixo quando o número é a stake da linha; a categoria lê o texto
# JÁ limpo, então aqui só sobra a turbinada.
_RE_BOOST = re.compile(r'\d+\s*%')
# ` e ` / `, ` separando pernas sem a palavra "dupla" (12 linhas medidas).
_RE_LIGA = re.compile(r'\s+e\s+')


def _combo(titulo: str) -> str:
    """'acumulada' | 'dupla' | 'boost' | '' — lido do título."""
    d = _chave(titulo)
    if _RE_ACUMULADA.search(d):
        return 'acumulada'
    if _RE_BOOST.search(d):
        return 'boost'
    if _RE_DUPLA.search(d):
        return 'dupla'
    if _RE_LIGA.search(d):
        # `A, B e C` declara TRÊS pernas → acumulada; `A e B`, duas.
        return 'acumulada' if ',' in d else 'dupla'
    return ''


# ---------- categoria ----------
# Mercado que o CANAL diz e o título omite. Chave: (dd/mm/aaaa, título), com a
# mensagem citada. Só entra aqui o que está escrito no export — nunca dedução.
_MERCADO_POR_TITULO = {
    ('31/08/2026', 'Andres Garcia +1'): 'Chutes',   # msg 31/08 11:51 "+1 Chutes"
    ('31/08/2026', 'Andres Garcia +2'): 'Chutes',   # msg 31/08 11:51 "+2 Chutes"
    ('01/08/2026', 'Chris Mochrie +2'): 'Chutes',   # msg 01/08 10:30 "+2 Chutes"
    ('01/08/2026', 'Chris Mochrie +3'): 'Chutes',   # msg 01/08 10:30
    ('01/08/2026', 'Chris Mochrie +4'): 'Chutes',   # msg 01/08 10:30
    ('13/08/2026', 'Neto moura'): 'Chutes',         # msg 13/08 18:12 "Neto Moura chutes 2+"
    # "Add 0.75% no milan" (msg 08/08 10:30) é reforço da aposta `Milan
    # Anytime` (msg 07/08 19:34); o `+0.75u` do título é a stake, não linha.
    ('08/08/2026', '+0.75u milan rasmussen'): 'Anytime',
    # "Everton ML 2.5 gols 2.75% @2.29" (msg 26/08 15:12): DOIS mercados no
    # mesmo bilhete (resultado + total) — bet builder do mesmo jogo → Múltipla.
    ('26/08/2026', 'Everton ML 2.5 gols'): 'Múltipla',
}

# Gol do JOGO (não do jogador): ambos os tempos, próximo gol, linha decimal.
_RE_GOL_DE_JOGO = re.compile(r'\bambos\b|\bproximo\b|\d+[.,]\d+\s*gols?\b')
# `+2 Gols` / `2 Gols <Nome>`: marcador 2+ → família Anytime (§3).
_RE_MARCADOR = re.compile(r'[+]?\s*\d\s*[+]?\s*gols?\b')


def norm_categoria(esporte: str, titulo: str, combo: str, data: str) -> str:
    d = _chave(titulo)

    # 1. Combinação — declarada no título. Bet builder e turbinada também são
    #    Múltipla (mesmo jogo não muda a natureza da aposta).
    if combo:
        return 'Múltipla'

    # 2. Mercado que só o canal diz (mapa fechado, com a msg citada).
    achado = _MERCADO_POR_TITULO.get((data, limpa(titulo)))
    if achado:
        return achado

    # 3. OBJETO da aposta — vence sempre o tipo de mercado (§1).
    if re.search(r'escanteio|\bcantos?\b', d):
        return 'Escanteios'
    if re.search(r'\bcart(ao|oes)\b|expuls|vermelho', d):
        return 'Cartões'
    if re.search(r'\bimpedimento', d):
        return 'Impedimentos'
    # `SOA` = **score or assist** — "marcar ou assistir" (respondido por ele em
    # 06/09/2026). NÃO é chute no gol, e a sigla nunca apareceu por extenso no
    # export: eu havia inferido `Chutes no Gol` pela vizinhança (`SOA` e `SOT`
    # aparecem na mesma escada, os dois pareados com `Anytime`) e estava errado.
    # Vai para `Player Props` junto com o `G/A`: é o MESMO mercado escrito de
    # dois jeitos, e o §5 manda estatística composta de JOGADOR para lá — não
    # existe categoria "marcar ou assistir" no §3, e escolher `Anytime` ou
    # `Assistência` sozinhas descartaria metade do mercado.
    # Vem ANTES do Anytime de propósito: "marcar ou assist" casa com `marcar`.
    if re.search(r'\bsoa\b|\bg\s*/\s*a\b|\bm\s*/\s*a\b|marcar ou assist', d):
        return 'Player Props'
    # SOT antes de "chutes": `Rasmus sot 2+` é chute NO GOL, não chute.
    if re.search(r'\bsots?\b|chutes? (a|ao) gol|no alvo', d):
        return 'Chutes no Gol'
    if re.search(r'chutes?|\bshots?\b|\bsots\b|finaliza', d):
        return 'Chutes'
    if re.search(r'\bdefesas?\b', d):
        return 'Player Props'      # defesa de goleiro não tem categoria no §3
    if re.search(r'faltas?\b', d):
        return 'Faltas'
    if re.search(r'desarmes?|tackles?', d):
        return 'Desarmes'
    if re.search(r'\bassist\w*|\basist\w*|\bast\b|\bass\b', d):
        return 'Assistência' if esporte == 'Futebol' else 'Player Props'
    # Anytime cobre a família "jogador para marcar", limiar 2+/3+ inclusive (§3).
    # `Mosquera Any` / `Sergio Anyt`: ele abrevia. `any` isolado só aparece nesse
    # papel nos 956 títulos (medido).
    if re.search(r'anytime|\banyt\w*|\bany\b|headscore|marcar|marcador', d):
        return 'Anytime'
    if re.search(r'gols?\b', d):
        if _RE_GOL_DE_JOGO.search(d):
            return 'Gols'
        return 'Anytime' if _RE_MARCADOR.search(d) else 'Gols'
    # "Vencer sem perder um set" (2 linhas de tênis, 03/08): o objeto é o SET,
    # e o §7 manda o objeto vencer o tipo de mercado. As duas casam aqui mesmo
    # com o título truncado (`taylor fritz vencer sem perder`) — deixar uma em
    # `Sets` e a outra em `ML` seria classificar o mesmo mercado de dois jeitos.
    if re.search(r'\bsets?\b|vencer sem perder', d):
        return 'Sets'
    if re.search(r'\bgames?\b', d):
        return 'Games'
    if re.search(r'\bpontos?\b|\bpts\b', d):
        return 'Pontos'

    # 4. Mercados de RESULTADO (nenhum objeto próprio foi nomeado).
    if re.search(r'\bdc\b|dupla chance', d):
        return 'Dupla Chance'
    if re.search(r'\bdnb\b|empate anula', d):
        return 'DNB'
    if re.search(r'\bambas\b', d):
        return 'Ambas Marcam'
    if re.search(r'\bml\b|moneyline|vencedor|\bempate\b|vence\w*|vitoria|'
                 r'classificar|\bht\b|1 tempo|1o tempo', d):
        return 'ML'
    # Handicap se declara pelo SINAL. Prop dele é sempre positiva (`+2`, `3+`);
    # linha negativa no fim (`cruzeiro -1`) é handicap e não existe como prop.
    if re.search(r'handicap|spread|[+-]\d+[.,]\d|[-–]\s*\d+([.,]\d+)?\s*$', d):
        return 'Handicap'

    # 5. Nome + limiar, sem objeto: é prop de jogador com o mercado omitido
    #    (~20 linhas; nem o canal diz qual). `Player Props` é a gaveta do §3 —
    #    mandar para `Gols` (o total do futebol) inventaria o objeto.
    if re.search(r'[+]\s*\d|\d\s*[+]|\d+[.,]\d', d):
        return 'Player Props'
    return 'Player Props' if esporte == 'Futebol' else 'Outros'


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


# `Ganha` → W · `Perdida` → L · `Reembolsada` → V (§5.1.2: void devolve a stake,
# e as 14 têm Ganho=0 E Lucro=0). Os demais ficam mapeados para o dia em que o
# tracker devolver meia vitória.
_RESULTADO_MAP = {
    'ganha': 'W', 'ganho': 'W', 'green': 'W',
    'perdida': 'L', 'perdido': 'L', 'red': 'L',
    'reembolsada': 'V', 'reembolsado': 'V',
    'anulada': 'V', 'anulado': 'V', 'void': 'V', 'devolvida': 'V',
    'meio ganha': 'HW', 'meio perdida': 'HL',
}


def norm_resultado(v) -> str:
    r = _RESULTADO_MAP.get(_chave(v), _chave(v).upper())
    return r if r in VALID else ''


# ---------- descrição ----------
# Três limpezas, nenhuma delas reescrita (ver docstring): `-` solto no fim,
# `- <número>` final e `<número>%` final — as duas últimas SÓ quando o número é
# a própria stake da linha, que é a stake vazando para dentro do título. A
# condição de igualdade é o que protege o resto: `cruzeiro -1` (stake 2,50) é
# handicap e fica intocado.
_RE_TRAVESSAO_FINAL = re.compile(r'\s*[-–]\s*$')
_RE_SUFIXO_NUM = re.compile(r'\s*(?:[-–]\s*(\d+[.,]?\d*)|(\d+[.,]?\d*)\s*%)\s*$')


def norm_descricao(titulo: str, stake_num) -> str:
    t = limpa(titulo)
    m = _RE_SUFIXO_NUM.search(t)
    if m and stake_num is not None:
        n = _para_float(m.group(1) or m.group(2))
        if n is not None and abs(n - stake_num) < 1e-9:
            t = t[:m.start()].strip()
    return _RE_TRAVESSAO_FINAL.sub('', t).strip()


# ---------- carga do CSV ----------
def carregar_rows(csv_path: str) -> list[dict]:
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
    for i, b in enumerate(brutas, start=2):      # 2 = linha do arquivo (1 é o cabeçalho)
        crua = limpa(b[COL_DATA])
        try:
            momento = dt.datetime.strptime(crua, '%d/%m/%Y %H:%M')
        except ValueError:
            raise SystemExit(f'linha {i}: data ilegível {crua!r} (esperado dd/mm/aaaa hh:mm)')
        data = momento.strftime('%d/%m/%Y')
        titulo = limpa(b[COL_TITULO])
        esporte_bruto = limpa(b[COL_ESPORTE])
        esporte = norm_esporte(esporte_bruto)
        stake_num = _para_float(b[COL_STAKE])
        # A leitura do mercado é feita sobre o texto JÁ limpo: o sufixo cortado é
        # a stake vazando, e ela mente duas vezes se ficar — `0.50%` viraria
        # turbinada e `- 1.50` viraria handicap (o sinal é o que declara
        # handicap nesta fonte).
        descricao = norm_descricao(titulo, stake_num)
        combo = _combo(descricao)

        # Acumulada declarada (3+ seleções) → esporte especial `Múltiplos` (§2).
        # `dupla` e bet builder do MESMO jogo mantêm o esporte do arquivo.
        esporte_final = 'Múltiplos' if combo == 'acumulada' else esporte

        out.append({
            'data': data,
            '_dt': momento,
            '_linha': i,
            'esporte': esporte_final,
            'tipster': TIPSTER,
            'casa': norm_casa(b[COL_CASA], data, titulo),
            'parceiro': PARCEIRO,
            'aposta': norm_categoria(esporte_final, descricao, combo, data),
            'descricao': descricao,
            'stake': fmt_stake(b[COL_STAKE]),
            'odd': norm_odd(b[COL_ODD]),
            'resultado': norm_resultado(b[COL_ESTADO]),
            '_lucro': _para_float(b[COL_LUCRO]),     # conferência do DRY
            '_ganho': _para_float(b[COL_GANHO]),
            '_titulo_bruto': titulo,
            '_esporte_bruto': esporte_bruto,
            '_casa_bruta': limpa(b[COL_CASA]),
            '_estado_bruto': limpa(b[COL_ESTADO]),
            '_tipo': limpa(b[COL_TIPO]),
            '_combo': combo,
        })
    # O export vem do mais recente para o mais antigo; a numeração é cronológica.
    out.sort(key=lambda r: (r['_dt'], r['_linha']))
    return numerar(out)


def numerar(rows: list[dict]) -> list[dict]:
    """Código GV<aaaamm>-<n>. Numeração MENSAL (reinicia em 1 a cada mês), na
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
        # Planilha e bot escrevem na MESMA série `GV<aaaamm>-<n>`, e o código
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


def _relatorio(rows: list[dict], dono: str):
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
    print('estado bruto → resultado:', dict(Counter(
        f"{r['_estado_bruto']}→{r['resultado'] or '(aberta)'}" for r in rows).most_common()))
    print('extraction_state:', dict(Counter(
        estado_extracao(r['resultado'], r['odd']) for r in rows)))

    novas = {r['casa'] for r in rows} - set(_CASA_MAP.values())
    if novas:
        print(f'\n⚠ casa(s) fora do mapa, gravadas VERBATIM: {sorted(novas)}')
    print('\n⚠ Betsson é casa NOVA no banco (0 bilhetes antes deste import): '
          'precisa de favicon em index.html, data.js (CASA_ICONS **e** '
          'HOUSE_DOMAIN) e inicio.html.')

    sem_casa = [r for r in rows if not r['_casa_bruta']]
    if sem_casa:
        print(f'\n⚠ {len(sem_casa)} linha(s) sem casa no arquivo, resolvidas pelo '
              f'export do Telegram (mensagem citada em _CASA_POR_TITULO):')
        for r in sem_casa:
            print(f'    {r["codigo"]:<14} {r["data"]} | → {r["casa"]:<8} | '
                  f'{r["descricao"][:45]}')

    combos = [r for r in rows if r['_combo']]
    if combos:
        print(f'\n⚠ {len(combos)} linha(s) declaram combinação no título, embora a '
              f'coluna Tipo diga {combos[0]["_tipo"]!r}:')
        for tipo in ('acumulada', 'dupla', 'boost'):
            sub = [r for r in combos if r['_combo'] == tipo]
            print(f'   — {tipo}: {len(sub)}')
            for r in sub[:8]:
                print(f'      {r["codigo"]:<14} {r["data"]} | {r["esporte"]:<10} '
                      f'@{r["odd"]:<8} | {r["descricao"][:45]}')
            if len(sub) > 8:
                print(f'      … +{len(sub) - 8}')

    soa = [r for r in rows if re.search(r'\bsoa\b|\bg\s*/\s*a\b',
                                        _chave(r['descricao']))]
    if soa:
        print(f'\n  {len(soa)} linha(s) `SOA`/`G-A` = "score or assist" (marcar OU '
              f'assistir, confirmado pelo tipster em 06/09/2026) → `Player Props`:')
        for r in soa:
            print(f'    {r["codigo"]:<14} {r["data"]} | {r["aposta"]:<13} | '
                  f'{r["descricao"][:45]}')

    pp = [r for r in rows if r['aposta'] == 'Player Props'
          and not re.search(r'defesas?', _chave(r['descricao']))]
    if pp:
        print(f'\n⚠ {len(pp)} linha(s) `Nome N+` sem mercado no título — nem o canal '
              f'diz qual. Vão para `Player Props` (a gaveta do §3), nunca para o '
              f'total do esporte:')
        for r in pp:
            print(f'    {r["codigo"]:<14} {r["data"]} | @{r["odd"]:<8} | '
                  f'{r["descricao"][:45]}')

    mexidas = [r for r in rows if r['descricao'] != r['_titulo_bruto']]
    if mexidas:
        print(f'\n⚠ {len(mexidas)} descrição(ões) com limpeza de sufixo '
              f'(travessão solto ou a própria stake vazando para o título):')
        for r in mexidas:
            print(f'    {r["codigo"]:<14} {r["_titulo_bruto"]!r} → {r["descricao"]!r} '
                  f'(u={r["stake"]})')

    odd_ruim = [r for r in rows if (_para_float(r['odd']) or 0) < 1.01]
    if odd_ruim:
        print(f'\n⚠ {len(odd_ruim)} linha(s) com odd < 1,01:')
        for r in odd_ruim:
            print(f'    {r["codigo"]:<14} {r["data"]} | {r["descricao"][:35]:<35} | '
                  f'@{r["odd"]} u={r["stake"]} {r["resultado"]}')

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

    # Conferência contra FONTE EXTERNA: ele publicou o fechamento de agosto no
    # canal em 01/09 (`P/L +127.84u · ROI 13.02% · Apostas: 924`).
    ago = [r for r in rows if r['_mes'] == '202608']
    if ago:
        t = sum(_para_float(r['stake']) or 0 for r in ago)
        p = sum(v for r in ago
                if (v := _pl_derivado(r['stake'], r['odd'], r['resultado'])) is not None)
        print(f'\n— agosto × o que ELE publicou no canal em 01/09 —')
        print(f'  declarado: 924 apostas | P/L +127,84u | ROI 13,02%')
        print(f'  derivado : {len(ago)} apostas | P/L {p:+.2f}u | '
              f'ROI {100 * p / t if t else 0:+.2f}% | turnover {t:,.2f}u')
        print(f'  (a diferença de centavos é o arredondamento da coluna `Ganho`, '
              f'acumulado nas vitórias)')

    print('\n— amostra (10 primeiras) —')
    for r in rows[:10]:
        print(f'  {r["codigo"]:<14} {r["data"]} | {r["esporte"]:<10} | '
              f'{r["aposta"]:<13} | {r["casa"]:<11} | {r["descricao"][:38]:<38} | '
              f'u={r["stake"]:<6} @{r["odd"]:<8} {r["resultado"]}')


def main():
    ap = argparse.ArgumentParser(
        description='Importa a base do Grego Tips - VIP (8º tipster público).')
    ap.add_argument('--csv', required=True, help='caminho do gregotips.csv')
    ap.add_argument('--dono', required=True,
                    help='USERNAME do cadastro (conferido na tabela `usuarios`)')
    ap.add_argument('--go', action='store_true',
                    help='escreve no banco (sem isto é DRY RUN)')
    a = ap.parse_args()

    rows = carregar_rows(a.csv)
    print(f'{"=" * 78}\n{"IMPORT" if a.go else "DRY RUN"} — Grego Tips - VIP\n{"=" * 78}')
    _relatorio(rows, a.dono)
    if not a.go:
        print('\nDRY RUN — nada foi escrito. Repita com --go para gravar.')
        return
    carregar_env()
    if not os.environ.get('DATABASE_URL'):
        raise SystemExit('DATABASE_URL ausente (.env).')
    print()
    asyncio.run(importar(rows, a.dono))


if __name__ == '__main__':
    main()
