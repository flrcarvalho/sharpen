# -*- coding: utf-8 -*-
"""Importa a base do tipster **Soh Props - Vip** (`SOH PROPS 1/2/3.csv`) — 7º
tipster público, em `/tipsters/sohpropsvips`.

⚠️ **A MARCA NÃO É O NOME DO ARQUIVO.** Os CSV se chamam `SOH PROPS`, a conversa
começou por "SÓ PROPS" e a marca que o Feca fechou (03/09/2026) é
**`Soh Props - Vip`**, slug `sohpropsvips`. O username do cadastro é `sohprops`,
e são três coisas distintas — mesmo precedente do Rogerin (`sobolas.csv` →
`RogerinComeuMeuSaldo` → `Rogeringambler`). Nome de arquivo não é fonte de nada.

⚠️ **TRÊS arquivos, e eles são DISJUNTOS.** Medido antes de escrever uma linha:
2.241 + 5.000 + 37 = 7.278 registros, `interseção = 0` pela chave
`data+título+odd+stake`. O corte é temporal e encaixado (arq1 até 02/03/2026,
arq2 de 03/03 a 01/09, arq3 de 02/09 a 03/09), não re-exportação. Os três entram
no mesmo import; o script confere a interseção de novo em tempo de execução e
AVISA se ela deixar de ser zero — o dia em que alguém reexportar a base inteira
num arquivo só, esse aviso é o que impede o histórico de duplicar.

── Fonte ─────────────────────────────────────────────────────────────────────

Export de tracker Bet-Analytix, o MESMO formato do `import_rogerin_csv.py`:
CSV com `;`, aspas em tudo, cabeçalho em pt-PT (`Cotação`, `Bónus`), 24 colunas.
**Sem BOM** (o do Rogerin tinha; a leitura usa `utf-8-sig`, que cobre os dois).

    Data | Tipo | Esporte | Título da aposta | Cotação | Valor | Ganho | Lucro |
    Estado | Casa de apostas | Tipster | Categoria | Competição | Tipo de aposta |
    Closing Odds | Probabilidade estimada % | EV | Comissão | Bónus de ganho |
    Ao vivo | Aposta gratuita | Cashout | Eachway | Comentário

**Treze colunas estão vazias nas 7.278.** Sobram 10 com informação, e a coluna
`Tipster` — que no Rogerin era vazia — aqui traz `lucas` (616) e `rafael` (309).

A planilha é **aritmeticamente consistente**, medido: `Ganho = Cotação × Valor`
bate nas **1.489 ganhas, 0 divergências**; `Lucro = Ganho − Valor` bate em todas
menos as 225 `Reembolsada`, que gravam lucro 0 — que é exatamente o `V`. O
`_relatorio` refaz essa conta linha a linha, então erro de normalização aparece
como divergência em vez de passar calado.

── Duas ERAS de FORMATO DE TÍTULO, com corte limpo em 31/03/2026 ─────────────

Não são duas amostras de comportamento (como no Rogerin) — é a mesma aposta
escrita de dois jeitos, e isso decide como a categoria é lida:

    ERA 1  05/01 → 31/03  3.196 linhas  título VERBOSO, com confronto
           `Nottm Forest v Arsenal: I. Sangare O2.5 Chutes`
           `Chelsea v Pafos: R. James O2.5 Desarmes`
           2.775 têm `:` — mercado por extenso, em português.

    ERA 2  01/04 → 03/09  4.082 linhas  título CURTO, minúsculo, SEM confronto
           `olise shot3` · `mctominay g/a` · `alesson FS2` · `frank tack2`
           ZERO têm `:` — mercado em CÓDIGO.

O dicionário de mercado é, portanto, **um só com as duas grafias**: `desarmes` e
`tack2` caem na mesma regra, `chutes no gol` e `sot1` também. Um dicionário por
era duplicaria a manutenção sem ganhar nada — e a data não é fronteira
confiável, porque a ERA 2 ainda escreve `gol de cabeça` por extenso.

── ⚠️ A barra `/` é DUAS coisas diferentes ───────────────────────────────────

Esta é a armadilha que mais custaria caro, e ela é da ERA 1:

    `1+ Chutes p/ fora`                   → `p/` abrevia **"para"**
    `O1,5 P/ Sofrer Falta`                → idem
    `S. Villa Marcar / 1+ Chutes no gol`  → ` / ` É separador de bet builder

Só ` / ` **com espaço dos dois lados** separa seleção (129 linhas, todas em
fev–mar). Tratar todo `/` como separador mandaria props simples para `Múltipla`;
ignorar o separador deixaria os 129 bet builders como aposta simples. `p/`,
`d/`, `g/a` e `m/a` são explicitamente excluídos antes de olhar a barra.

Na ERA 2 a barra volta SEM espaço, e aí é dupla escrita compacta
(`salah/ketelaere`, `mols/payne`, `eze/saka1`). Como `g/a` e `m/a` já saíram
antes, o que sobra com `/` na ERA 2 é combinação.

**E a barra não é o único separador.** A ERA 1 usa mais dois, e cada um tem um
CONTRAEXEMPLO dentro da própria base — o que faz a regra ingênua errar nos dois
sentidos:

    ` e `   `rice e casemiro 1.5 desarmes`  é separador
            `Brighton e Hove Albion v …`     NÃO é — está no nome do time
    ` - `   `Marcar - 1+ Chutes no gol`     é separador
            `BN - Cuffy 1+ Chutes`           NÃO é — `BN` é prefixo de nota
            `2+ Faltas Recebidas - CASHOUT`  NÃO é — sufixo

Os discriminadores são medidos, não deduzidos. Para o ` e `, a **posição**: na
ERA 1 o confronto vem antes do `:` e a seleção depois, então só o ` e ` de
depois dos dois-pontos conta — mais um piso de 2 caracteres de cada lado, que
remove o único falso positivo restante (`Tono E any1`, onde o `E` é inicial de
nome, como em `E Haaland any1`). 15 de 15. Para o ` - `, o **mercado**: só é
separador quando os DOIS lados nomeiam um objeto de aposta, o que `BN` e
`CASHOUT` não fazem. Juntos, os dois somam 30 bet builders que sem eles
entrariam como aposta simples.

── Descrição: VERBATIM, com os erros de digitação ────────────────────────────

`Título da aposta` é texto livre digitado à mão e traz o que texto assim traz:
`Independiente Ridavia Mendonza`, `S. McTomnay`, `Zoboslai`, `Briston City`.
Vai **verbatim** (só limpeza de espaço e caractere de controle) — o
`MASTER_DESCRICAO §1` proíbe inventar informação, e "corrigir" nome de jogador
por palpite é inventar. Mesmo precedente do `import_passatips_xlsx.py` e do
`import_rogerin_csv.py`.

O confronto existe na ERA 1 (dentro do próprio título) e **não existe** na
ERA 2. Fabricá-lo onde não há seria pior que omiti-lo.

── Esporte: Futebol, e desta vez o rótulo CONFERE ────────────────────────────

`Esporte` diz `Futebol` em 7.277 das 7.278 (a única vazia é a linha-cabeçalho da
múltipla, abaixo). Diferente do Rogerin — onde 13 props de NBA estavam rotuladas
Futebol —, aqui o rótulo bate com o conteúdo: é base de **prop de jogador de
futebol** de ponta a ponta, como o nome diz. Não há correção de esporte a fazer,
e o script **não tem** flag para isso.

`Múltiplos` (`MASTER_ESPORTES §2`) fica reservado a quem declara 3+ seleções:
`multipla`, `tripla` e `bingo`. `dupla` declara DUAS e mantém `Futebol` — mesmo
corte do `import_rogerin_csv.py`, com uma diferença registrada: lá `tripla` não
subia para `Múltiplos`, aqui sobe, porque três é exatamente o piso do §2.

── Estado → resultado ────────────────────────────────────────────────────────

    Perdida       5.563 → L
    Ganha         1.489 → W
    Reembolsada     225 → V     (Ganho 0 E Lucro 0 nas 225 — é void, não perda)
    Pendente          1 → só na perna de múltipla; ver abaixo

── ⚠️ DUAS linhas não são apostas: são PERNAS de uma múltipla ────────────────

O arq1 (linhas 1819-1821) traz o bloco de uma múltipla do jeito que o
Bet-Analytix exporta: a linha-cabeçalho com o cupom inteiro (`Múltipla 2
Apostas`, @441, stake 0,25, Perdida) seguida das **pernas** — que repetem data e
título mas vêm com `Valor`, `Ganho`, `Lucro` e `Casa` VAZIOS.

Perna não é aposta. Importá-la criaria bilhete com stake 0 — gravado, porém
invisível no dashboard (`dashboard_rows` corta stake <= 0), e ainda inflando a
contagem. O critério de corte é `Valor` vazio, e as descartadas saem **listadas
uma a uma** no DRY. A única `Pendente` da base é uma dessas pernas: fora delas,
a base inteira está liquidada.

⚠️ Não confundir com a linha 1822, que repete o mesmo título com `Tipo=Simples`
e stake própria: essa é uma aposta simples de verdade e entra.

── Tipster: `Lucas` e `Rafael` são do SOH PROPS ──────────────────────────────

A coluna `Tipster` do arquivo traz `lucas` (616) e `rafael` (309) — as duas só
entre 03/03 e 29/03/2026, 925 linhas ao todo. **Decisão do Feca (03/09/2026):
preservar os dois como tipsters, ambos sob o dono `sohprops`.**

Então a coluna `tipster` do banco recebe `Lucas` / `Rafael` naquelas 925 e
`Soh Props - Vip` nas outras 6.351. O `dono` é `sohprops` nas 7.276 — é ele que
isola os dados; o `tipster` é só o rótulo de quem deu o pick.

A caixa é normalizada para `Lucas`/`Rafael` (o arquivo escreve minúsculo) por
ser nome próprio em coluna de exibição. Isso NÃO contraria a regra de "casa
verbatim": aquela existe porque `casa` é chave de conta e entra na assinatura —
`tipster` não entra em nenhuma das duas coisas.

── Casa: 47 grafias, 12 divergem do banco, 183 linhas sem nenhuma ───────────

O mapa abaixo foi MEDIDO contra `select casa, count(*) from bilhetes group by 1`
— importar na grafia do arquivo criaria casa gêmea (`BetFair` ao lado das 2.569
linhas de `Betfair`). Casa fora do mapa entra **VERBATIM**: nunca title-casear,
que mutila nome (`BETesporte`, `VaideBet`) e cria conta paralela.

O DRY **consulta o banco** e imprime, casa a casa, se a grafia de destino já
existe e com quantas linhas — inclusive avisando de gêmea que só difere por
caixa. Medição no relatório vale mais que asserção em comentário: o dia que
alguém unificar uma casa no banco, o mapa daqui fica velho e o DRY acusa.

**183 linhas vêm sem casa.** O tipster foi perguntado (03/09/2026) e respondeu
que são variadas — *"as vezes o planilhador n colocava"* — e autorizou casa
fictícia. O padrão é **`Outra`**, que é o nome que o sistema JÁ usa para isso (o
bot grava `Outra` quando não identifica a casa pelo link). Inventar um nome de
casa real ali criaria uma conta que pede custo, saldo e favicon como se fosse
verdadeira. `--casa-vazia ""` faz o script **abortar** em vez de preencher.

── Stake em UNIDADES ─────────────────────────────────────────────────────────

`Valor` vai de 0,02 a 3,00 (moda 0,50 · 1,00 · 0,25 · 0,75). É unidade, não
real — mesma decisão do `SoChutes`, `Fleury`, `Rei do Criquete`, `PassaTips` e
`Rogerin`. O P/L do dashboard é o P/L em unidades.

── Numeração ─────────────────────────────────────────────────────────────────

Código `SO<aaaamm>-<n>`, mensal, reiniciando em 1 na ordem cronológica.

⚠️ **O prefixo NÃO é `SP`.** `SP` parece o óbvio para "Soh Props" e está
**ocupado**: os códigos NATIVOS da Superbet são `SP8399910931W`. Não haveria
colisão de assinatura (o formato difere e a casa entra no hash), mas `SP` na
base já lê como Superbet. `SO` foi conferido com **zero ocorrências em qualquer
`codigo_bilhete` do banco** — livre de verdade.

⚠️ **Se ele passar a usar o bot**, planilha e bot escrevem na MESMA série
`SO<aaaamm>-<n>` e o código entra na assinatura. Suba o contador (`/contador N`
no apoio) para além do último código deste import ANTES da primeira aposta. O
script ABORTA se um código que ele geraria já existir sob outra origem.

── Decisões ──────────────────────────────────────────────────────────────────

- **Dono solo** — sem `OPERADORES`, sem dedup cruzada.
- **Uma conta `Padrão` por casa** — 1 linha por casa no Painel de Contas.
- **`dono` = `sohprops`** (username do cadastro, e-mail jabuticabaxp@gmail.com,
  aprovado para `ativo` em 03/09/2026). Conferido na tabela `usuarios`, nunca
  deduzido: `dono` errado não dá erro, dá **tela vazia para o usuário certo**
  (s260). Marca (`Soh Props - Vip`), slug (`sohpropsvips`) e username
  (`sohprops`) são TRÊS strings diferentes — como no Fleury e no PassaTips.

── O que este script NÃO resolve ─────────────────────────────────────────────

- ~~`set1`/`set2`~~ — **RESOLVIDO em 03/09/2026, pelo tipster.** Ficam aqui o
  que ele respondeu e o que a medição já sugeria, porque é o glossário da ERA 2
  inteira e não existe em lugar nenhum além da cabeça dele:

      chute = shot1 · chute ao gol = SOT1 · jogador marcar = any1
      falta cometida = FC1 · falta sofrida = FS1 · desarme = tack1
      marcar ou assistir = M/A · assistência = ass
      set<n> = chutes + chutes ao gol   ← combinação, não mercado único
      CA = "Criar Aposta", o bet builder antigo da bet365

  As duas últimas eram as que faltavam, e as duas são **combinação do mesmo
  jogo** → `Múltipla` com esporte `Futebol`. A escada de odds já apontava para
  isso antes da resposta: `set1` mediana 3,15 e `set2` 8,62, ao lado de `sot1`
  2,75 e `sot2` 9,00 — perto demais de SOT para ser mercado novo, e acima dele
  como uma combinação correlacionada tem de ser.
- **A odd de 57.834** (`tripla 2`, 28/04, stake 0,05) e as **2 odds de 0,75**.
  Odd < 1 é impossível para aposta real e 57.834 é implausível até para tripla
  de props. As três são `Perdida`, então o P/L é −stake e **não depende da odd**
  — entram como estão e saem no relatório.
- **A casa das 183 linhas sem casa** — ver acima; ficam em `Outra`.
- **Favicon de casa nova**, que vive em TRÊS mapas (`app/static/index.html`,
  `dash/assets/js/data.js`, `inicio.html`). O DRY lista as 15 casas que não
  existem no banco; o favicon é passo separado, depois do import.
- **22 linhas em `Outros` (0,3 %)**, e é onde elas devem ficar. A maioria é
  NOME SOLTO, sem mercado nenhum (`quintana`, `J Torres`, `toni fruk`,
  `aleksandr mrynskiy ???`); 2 são artilheiro de torneio (`H Kane golden boot
  copa`), que é outright e não tem categoria no §3; 1 é `Cashout M. Vojvoda`,
  sem mercado; e sobram `Patrick HS1` e `Palacios 2more`, dois códigos que nem
  ele decifrou. Chutar mercado a partir de um nome é inventar — o DRY lista as
  22 uma a uma para quem quiser perguntar de novo.
- **UMA linha em que a própria fonte se contradiz:** `SO202601-1097`,
  `Tripla (D. Sertanejo)`, `Estado=Perdida` mas `Lucro=0,00` com stake 0,30.
  Nas outras 7.238 o `Lucro` do arquivo bate com o P/L derivado. O `Estado` é a
  fonte do resultado, então ela entra como `L` (P/L −0,30) e sai no relatório —
  reconciliar em silêncio é que seria errado. Vale 0,30u no total de 5.742u.

Uso — os TRÊS arquivos de uma vez. Importar em partes REESCREVE a numeração: o
código é sequencial por mês sobre o conjunto todo, então rodar só o arq3 daria
`SO202609-1` a um bilhete que já é o `-38`, e o `DELETE ... WHERE origem='import'`
do começo apagaria o resto da base dele.

    python scripts/import_sohprops_csv.py \\
        --csv "…\\SOH PROPS 1.csv" "…\\SOH PROPS 2.csv" "…\\SOH PROPS 3.csv" \\
        --dono sohprops            # DRY; acrescente --go para gravar
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

# O relatório tem `→`, `⚠`, `✋` e acento. No Windows a saída padrão é cp1252 e
# um `print` com seta derruba o script INTEIRO no meio do DRY (UnicodeEncodeError)
# — pior que ilegível: o relatório para na primeira linha e some o resto.
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

ENV_PATH = os.path.join(os.path.dirname(__file__), '..', '.env')
PARCEIRO = 'Padrão'
TIPSTER = 'Soh Props - Vip'        # nome de MARCA (o username vai em --dono)
PREFIXO = 'SO'                     # código SO<aaaamm>-<n>; ver docstring (NÃO é SP)
ORIGEM = 'import'
VALID = {'W', 'L', 'V', 'HW', 'HL'}
DELIM = ';'
# Decisão do Feca (03/09/2026), com o tipster consultado: as 185 linhas sem casa
# vão para `Outra`, a casa fantasma que o sistema já usa. Ver docstring.
CASA_VAZIA_PADRAO = 'Outra'
# Corte das eras — só para o RELATÓRIO. A classificação não usa data.
CORTE_ERA = dt.datetime(2026, 4, 1)

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
COL_TIPSTER = 'Tipster'
OBRIGATORIAS = (COL_DATA, COL_TIPO, COL_ESPORTE, COL_TITULO, COL_ODD, COL_STAKE,
                COL_GANHO, COL_LUCRO, COL_ESTADO, COL_CASA, COL_TIPSTER)


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
    """minúscula sem acento — casa `cabeça`/`cabeca`, `Cartão`/`cartao`."""
    s = unicodedata.normalize('NFKD', limpa(s).lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def _k(s) -> str:
    """_chave sem espaço nem pontuação — casa nome de casa com grafia livre."""
    return re.sub(r'[^a-z0-9]', '', _chave(s))


# ---------- casa ----------
# Grafia de DESTINO medida no banco (`select casa, count(*) from bilhetes`), não
# suposta. Só entra aqui quem DIVERGE do arquivo ou tem gêmea conhecida; o resto
# passa verbatim. O DRY reconfere cada destino contra o banco.
_CASA_MAP = {
    'bet365': 'Bet365',                    # 60.656
    'betano': 'Betano',                    # 16.248
    'superbet': 'Superbet',                # 7.545
    'pinnacle': 'Pinnacle',                # 3.241
    'betfair': 'Betfair',                  # 2.569  (arquivo escreve `BetFair`)
    'novibet': 'Novibet',                  # 1.852
    'betnacional': 'Betnacional',          # 1.516
    'betesporte': 'BETesporte',            # 1.448
    'betfast': 'Betfast',                  # 1.346
    'esportiva': 'Esportiva',              # 746
    'bolsadeaposta': 'Bolsa de Aposta',    # 613    (arquivo: `Bolsa De Aposta`)
    'pitaco': 'Pitaco',                    # 440
    'reidopitaco': 'Pitaco',               #        (arquivo: `Rei do Pitaco`)
    'kto': 'KTO',                          # 358
    'sportingbet': 'SportingBet',          # 302
    'stake': 'Stake',                      # 290
    'casadeapostas': 'Casa de Apostas',    # 210    (arquivo: `CasadeApostas`)
    'betbra': 'Betbra',                    # 156    (arquivo: `Bet Bra`)
    'faz1bet': 'Faz1bet',                  # 133    (arquivo: `faz1bet`)
    'betboo': 'Betboo',                    # 97
    'estrelabet': 'Estrela Bet',           # 90     (arquivo: `EstrelaBet`)
    'betmgm': 'BetMGM',                    # 89
    'bateu': 'Bateu',                      # 75
    'betvip': 'Betvip',                    # 27     (arquivo: `BetVIP`)
    'pagol': 'Pagol',                      # 22
    '7k': '7K',                            # 20
    '7kbet': '7K',                         #        (arquivo: `7KBet`)
    'apostaganha': 'Aposta Ganha',         # 19     (arquivo: `ApostaGanha`)
    'brbet': 'BRBet',                      # 3      (arquivo: `BRBET`)
    'apostou': 'Apostou',                  # 2
    '4play': '4Play',                      # 2
    'mcgames': 'Mcgames',                  # 1      (arquivo: `MC Games`)
    # `Esporte Da Sorte` (102) e `Esportes da Sorte` (45) já são GÊMEAS no banco,
    # anteriores a este import. O arquivo escreve a segunda, que existe — manter
    # a grafia dele não cria gêmea nova. Unificar as duas é tarefa à parte
    # (`scripts/unificar_casas.py`) e decisão do Feca, não deste import.
    'esportesdasorte': 'Esportes da Sorte',
    'esportedasorte': 'Esportes da Sorte',
}


def norm_casa(v, casa_vazia: str) -> str:
    bruto = limpa(v)
    if not bruto:
        return casa_vazia
    return _CASA_MAP.get(_k(bruto), bruto)


# ---------- tipster ----------
# Decisão do Feca (03/09/2026): `lucas`/`rafael` da coluna `Tipster` são
# preservados, ambos sob o dono `sohprops`. Caixa normalizada porque é nome
# próprio de exibição — `tipster` não é chave de conta nem entra na assinatura.
_TIPSTER_MAP = {'lucas': 'Lucas', 'rafael': 'Rafael'}


def norm_tipster(v) -> str:
    bruto = limpa(v)
    if not bruto:
        return TIPSTER
    return _TIPSTER_MAP.get(_chave(bruto), bruto)


# ---------- esporte ----------
_ESPORTE_MAP = {'futebol': 'Futebol'}


def norm_esporte(v) -> str:
    return _ESPORTE_MAP.get(_k(v), limpa(v) or 'Futebol')


# ---------- combinação ----------
# `multipla`/`tripla`/`bingo` declaram 3+ → esporte `Múltiplos` (§2).
# `dupla` declara DUAS e mantém `Futebol`.
_RE_ACUMULADA = re.compile(r'\b(multipla\w*|mult|multpl\w*|tripla\w*|bingo|trixie)\b')
# `CA` = **Criar Aposta** (o bet builder antigo da bet365) e `set<n>` = chutes +
# chutes ao gol do mesmo jogador — os dois confirmados pelo tipster em
# 03/09/2026. São combinação do MESMO jogo, então entram como `dupla`: categoria
# `Múltipla` e esporte `Futebol` (só `multipla`/`tripla`/`bingo` sobem para
# `Múltiplos`, que o §2 reserva a 3+ seleções de jogos diferentes).
#
# `\bca\b` assusta por ser curto, mas foi MEDIDO: acerta as 5 linhas de `CA` e
# mais nada em 7.278 — nenhum nome de jogador, time ou mercado tem `ca` solto.
# `set` estava em `_RE_PLAYER` como mercado não identificado; saiu de lá.
_RE_DUPLA = re.compile(r'\b(duplas?|duas bets|combo|ca|sets?\d+)\b')
# `Dupla Chance` é mercado de RESULTADO, não cupom — sai antes de tudo.
_RE_DUPLA_CHANCE = re.compile(r'dupla chance')
# ` / ` COM espaço dos dois lados = separador de bet builder (ERA 1).
# `p/ fora`, `P/ Sofrer Falta`, `g/a`, `m/a` NÃO são separador — ver docstring.
_RE_SEP_ESPACO = re.compile(r'\s/\s')
_RE_GA = re.compile(r'\b[gm]\s*/\s*a\b|\bany or ass\b|marcar ou (dar )?assist'
                    r'|marcar\s*/\s*assist')
_RE_PARA = re.compile(r'\b[pd]/')
# Barra colada entre nomes (ERA 2): `salah/ketelaere`, `mols/payne`.
_RE_SEP_COLADO = re.compile(r'[a-z]/[a-z]')


# ---------- grafia: pt-PT e os erros de digitação DESTE arquivo ----------
# Aplicado SÓ ao texto que vai para a classificação. A `descricao` gravada segue
# VERBATIM — o `MASTER_DESCRICAO §1` proíbe inventar informação, e o que está
# aqui é leitura, não reescrita da fonte.
#
# Dois grupos, e a diferença importa:
#
#   • VOCABULÁRIO — `remates` é chute em pt-PT, `fouled` é falta sofrida em
#     inglês. São palavras certas de outro idioma, não erro.
#   • ERRO DE DIGITAÇÃO — `chutess`, `chure`, `assit`, `tac1`, `sho1`, `amy1`,
#     `an1`. Cada um é um caractere de distância de um código que ESTE MESMO
#     arquivo usa centenas de vezes (`chutes` 851, `tack` 256, `shot` 412,
#     `any` 1.751, `assist` 474). Não é dicionário geral: é a lista fechada dos
#     escorregões medidos aqui, e ela não deve crescer por palpite — mercado que
#     ninguém identifica pertence a `Outros`, que é justamente o que o DRY lista.
_CORRECOES_GRAFIA = (
    (re.compile(r'\bremates?\b'), 'chutes'),                     # pt-PT
    (re.compile(r'(player )?to be fouled|\bfouled\b'), 'falta sofrida'),  # inglês
    (re.compile(r'\bchutes+\b'), 'chutes'),                      # `chutess`
    (re.compile(r'\bchure\b'), 'chute'),
    (re.compile(r'\bassit\w*\b'), 'assist'),
    (re.compile(r'\btac(\d)'), r'tack\1'),
    (re.compile(r'\bsho(\d)'), r'shot\1'),
    (re.compile(r'\b(?:amy|an)(\d)'), r'any\1'),
    (re.compile(r'\bdubla\w*\b'), 'dupla'),
    (re.compile(r'(\d)\s*gols?\b'), r'\1 gols'),                 # `4gols+`
)


def _grafia(titulo: str) -> str:
    """_chave + as correções acima. Só para classificar; nunca para gravar."""
    d = _chave(titulo)
    for rx, sub in _CORRECOES_GRAFIA:
        d = rx.sub(sub, d)
    return d


# ── mais dois separadores da ERA 1, os dois com CONTRAEXEMPLO na própria base ──
#
# ` e ` liga duas seleções (`rice e casemiro 1.5 desarmes`) — e também está
# dentro de `Brighton e Hove Albion v Bournemouth`. O discriminador é a POSIÇÃO:
# na ERA 1 o confronto vem antes do `:` e a seleção depois, então só o ` e ` de
# depois dos dois-pontos é separador. Sobrava um falso positivo, `Tono E any1`,
# onde o `E` é INICIAL de nome — daí o piso de 2 caracteres dos dois lados
# (`E Haaland any1`, `E Mahmoud any1` mostram que inicial solta é comum aqui).
# Medido: 16 candidatos na base, 15 combinações reais e 1 inicial, que o piso
# remove. 15 de 15.
_RE_SEP_E = re.compile(r'\b\w{2,}\s+e\s+\w{2,}')
# ` - ` separa perna de bet builder (`Marcar - 1+ Chutes no gol`), e também
# aparece como PREFIXO de nota (`BN - Cuffy 1+ Chutes`) e como SUFIXO
# (`2+ Faltas Recebidas - CASHOUT`). O discriminador é o MERCADO: só é separador
# quando os DOIS lados nomeiam um. Nos contraexemplos um dos lados (`BN`,
# `CASHOUT`) não nomeia nenhum.
_RE_SEP_TRACO = re.compile(r'\s-\s')


def _tem_mercado(txt: str) -> bool:
    """Algum OBJETO de aposta é nomeado neste pedaço de título? Usa as MESMAS
    regras da classificação — um dicionário só, nunca uma segunda cópia."""
    return any(rx.search(txt) for _, rx in _REGRAS_OBJETO)


def _selecao(d: str) -> str:
    """Na ERA 1 o confronto vem antes do `:` e a seleção depois; na ERA 2 não há
    `:` e o título inteiro é a seleção."""
    return d.split(':', 1)[1] if ':' in d else d


def _combo(titulo: str) -> str:
    """'acumulada' | 'dupla' | '' — lido do título."""
    d = _grafia(titulo)
    if _RE_DUPLA_CHANCE.search(d):
        return ''
    if _RE_ACUMULADA.search(d):
        return 'acumulada'
    if _RE_DUPLA.search(d):
        return 'dupla'
    # Bet builder / dupla compacta. `g/a` e `p/` saem antes de olhar a barra.
    resto = _RE_PARA.sub(' ', _RE_GA.sub(' ', d))
    if _RE_SEP_ESPACO.search(resto) or _RE_SEP_COLADO.search(resto):
        return 'dupla'
    sel = _selecao(resto)
    if _RE_SEP_E.search(sel):
        return 'dupla'
    partes = [p for p in _RE_SEP_TRACO.split(sel) if p.strip()]
    if len(partes) >= 2 and sum(1 for p in partes if _tem_mercado(p)) >= 2:
        return 'dupla'
    return ''


# ---------- categoria ----------
# `MASTER_APOSTAS §1`: a categoria registra o OBJETO da aposta. O §5 é explícito
# em dois pontos que valem aqui: falta de JOGADOR é `Faltas` (não Player Props) e
# cartão de JOGADOR é `Cartões`. `Player Props` é gaveta de estatística
# individual SEM categoria própria.
#
# Cada regra casa as DUAS grafias — por extenso (ERA 1) e em código (ERA 2).
_REGRAS = (
    ('Cartões',       r'\bcart(ao|oes)\b|\bcards?\b|amarelo|vermelho|expuls'),
    ('Impedimentos',  r'impedimento|offside'),
    ('Escanteios',    r'escanteio|\bcorners?\b|\bcantos\b'),
    ('Desarmes',      r'desarme|\btacks?\d*\b|\btackles?\b|intercep'),
    # faltas COMETIDAS e SOFRIDAS: o objeto é a falta nos dois casos.
    # `fc` = fouls committed · `fs`/`sof` = fouls suffered / sofridas.
    ('Faltas',        r'\bfaltas?\b|\bfouls?\b|\bf[cs]\d+\b|\bsof\d+\b|sofrer falta'),
    # SOT vem antes de Chutes: `chute no gol` também contém `chute`. E o "no" é
    # OPCIONAL de propósito — ele escreve `Chutes no gol`, `Chutes ao gol` e
    # `chute gol` para o mesmo mercado; exigir o "no" deixava 24 SOT em `Chutes`.
    ('Chutes no Gol', r'chutes? (no |a |ao )?gol|\bsots?\d*\b|no alvo'
                      r'|shots? on target|cabecada no gol|finaliza\w* no gol'),
    ('Chutes',        r'\bchutes?\d*\b|\bshots?\d*\b|\bshotf\d*\b|finaliza|\bfora\d+\b'),
    ('Assistência',   r'\bassist\w*\b|\bass\d*\b'),
    ('Anytime',       r'\bany\d*\b|\banytime\b|\bmarcar?\b|\bmarca\b|\bgols?\d*\b'
                      r'|\bcabec\w*|artilheiro|primeiro marcador|ultimo marcador'),
    # ── daqui para baixo NÃO é objeto de prop: são mercados de RESULTADO. O
    #    `_REGRAS_OBJETO` abaixo corta exatamente aqui, e é essa metade de cima
    #    que decide se um pedaço de título entre ` - ` nomeia mercado.
    # resultado — a base quase não tem, mas a escada fecha em ML
    ('Dupla Chance',  r'dupla chance'),
    ('DNB',           r'\bdnb\b|empate anula'),
    ('Ambas Marcam',  r'\bambas\b'),
    ('Handicap',      r'handicap|spread'),
    ('ML',            r'\bml\b|moneyline|vencedor|\bempate\b|vence\w*|vitoria'),
)
_REGRAS_C = tuple((cat, re.compile(pat)) for cat, pat in _REGRAS)
# Só a metade de cima (objeto de prop, até `Anytime`). `_tem_mercado` usa esta:
# `Dupla Chance`/`ML`/`Handicap` não nomeiam objeto, e incluí-los faria
# `- CASHOUT` parecer perna de bet builder.
_REGRAS_OBJETO = _REGRAS_C[:9]
# Total de gols do JOGO ou do TIME é `Gols` (§5); o JOGADOR que marca é
# `Anytime`, limiar 2+/3+ incluído. A escada acima manda tudo que diz "gols"
# para `Anytime`, o que está certo em 48 das 49 linhas — a exceção é
# `Genk v Sint-Truidense: O0,5 Gols`, que não tem jogador nenhum. A regra existe
# menos por essa linha e mais para o próximo export não classificar total como
# prop em silêncio.
_RE_TOTAL_GOLS = re.compile(r'(\bo\d|\bu\d|over|under|mais de|menos de)[^a-z]{0,8}gols?\b')
_RE_MARCA = re.compile(r'\bmarcar?\b|\bmarca\b|\bany\d*\b|\banytime\b|marcador')
# "de fora da área": as três formas passam pelas mesmas palavras, e a odd prova
# que são mercados diferentes — `D rice chute fora area1` sai @2,00 (chute), e
# gol de fora da área do mesmo jogador seria @15+. O `d[ae]?` é opcional porque
# ele escreve tanto `fora da area` quanto `fora area`.
_RE_FORA_AREA = re.compile(r'fora\s*(d[ae]?\s*)?(grande\s*)?area')
_RE_CHUTE_NO_GOL = re.compile(r'chutes? (no |a |ao )?gol')
_RE_CHUTE = re.compile(r'\bchu\w*')
# Estatística de jogador SEM categoria própria no `MASTER_APOSTAS §3` — defesas de
# goleiro, passes, dribles. É a gaveta do §5, não "não sei o que é": o objeto está
# nomeado, só não tem categoria. (`set` saiu daqui na s316: o tipster confirmou que
# é chutes + chutes ao gol, ou seja combinação — ver `_RE_DUPLA`.)
_RE_PLAYER = re.compile(r'\bdefesas?\d*\b|\bpasses?\d*\b|\bdribles?\d*\b')


def norm_categoria(titulo: str, combo: str) -> str:
    d = _grafia(titulo)

    # 1. Combinação declarada ou separada por barra. Bet builder também é
    #    Múltipla (precedente do PassaTips), mesmo com tudo do mesmo jogo.
    if combo:
        return 'Múltipla'

    # 2. `gol de fora da área` × `chute de fora da área` × `chute NO GOL de fora
    #    da área` — as três passam pelas mesmas palavras, então decidem antes da
    #    escada, do mais específico para o mais genérico.
    if _RE_FORA_AREA.search(d):
        if _RE_CHUTE_NO_GOL.search(d):
            return 'Chutes no Gol'
        if _RE_CHUTE.search(d):
            return 'Chutes'
        return 'Anytime'

    # 3. `G/A` / `M/A` / "marcar ou assistir" — o objeto é composto (gol OU
    #    assistência), então nem `Anytime` nem `Assistência` servem: §5 manda
    #    estatística individual sem categoria própria para Player Props. Vem
    #    ANTES de `Assistência`, senão "marcar ou assist" cairia lá.
    if _RE_GA.search(d):
        return 'Player Props'

    # 4. Total de gols do jogo/time (linha numérica + `gols`, sem ninguém
    #    marcando) é `Gols`; jogador que marca é `Anytime`. Vem antes da escada
    #    porque a regra de `Anytime` casa a palavra `gols` sozinha.
    if _RE_TOTAL_GOLS.search(d) and not _RE_MARCA.search(d):
        return 'Gols'

    # 5. Escada de objeto → mercado de resultado.
    for cat, rx in _REGRAS_C:
        if rx.search(d):
            return cat

    # 6. Estatística individual sem categoria própria (`set1`, `defesa2`).
    if _RE_PLAYER.search(d):
        return 'Player Props'

    return 'Outros'


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


# `Reembolsada` é o `V` desta fonte: Ganho 0 E Lucro 0 nas 223 (medido) — void,
# não perda. O resto do mapa fica para o dia em que o tracker gravar outro rótulo.
_RESULTADO_MAP = {
    'ganha': 'W', 'ganho': 'W', 'green': 'W',
    'perdida': 'L', 'perdido': 'L', 'red': 'L',
    'reembolsada': 'V', 'reembolsado': 'V', 'anulada': 'V', 'anulado': 'V',
    'void': 'V', 'devolvida': 'V',
    'meio ganha': 'HW', 'meio perdida': 'HL',
    'pendente': '', 'em aberto': '', 'aberta': '',
}


def norm_resultado(v) -> str:
    r = _RESULTADO_MAP.get(_chave(v), _chave(v).upper())
    return r if r in VALID else ''


def resultado_com_financeiro(estado, ganho, lucro) -> tuple[str, bool]:
    """`Estado` diz o rótulo; `Lucro` diz o que aconteceu com o dinheiro. Quando
    os dois discordam, o dinheiro ganha.

    **Perda de verdade tem `Lucro = −stake`.** `Perdida` com `Lucro = 0,00`
    quer dizer que a stake voltou — é void (`V`), não perda. Decisão do Feca
    (03/09/2026), e ela resolve as DUAS únicas linhas em que esta fonte se
    contradiz, medidas em 7.278:

        28/01  `Tripla (D. Sertanejo)`   stake 0,30  Ganho 0,00  Lucro 0,00
        04/03  `Dupla (Sem Van Dujin)`   stake 0,00  Ganho 0,00  Lucro 0,00

    A segunda é a que tinha stake 0 e sumia do feed (`dashboard_rows` corta
    stake <= 0). Vira `V`, e em `V` o P/L é 0 qualquer que seja a stake — então
    a stake desconhecida deixa de distorcer o que quer que seja; ela continua
    invisível na tela, mas agora invisível e inofensiva.

    Devolve (resultado, corrigido) — o DRY lista as corrigidas uma a uma.
    """
    r = norm_resultado(estado)
    if r == 'L' and lucro is not None and abs(lucro) < 0.005:
        return 'V', True
    return r, False


# ---------- carga do CSV ----------
def carregar_rows(csv_paths: list[str], casa_vazia: str) -> tuple[list[dict], list[dict]]:
    """Devolve (bilhetes, pernas_descartadas)."""
    brutas: list[tuple[str, int, dict]] = []
    for caminho in csv_paths:
        # utf-8-sig: o Rogerin vinha com BOM e este não. Cobre os dois.
        with open(caminho, encoding='utf-8-sig', newline='') as f:
            linhas = list(csv.DictReader(f, delimiter=DELIM))
        if not linhas:
            raise SystemExit(f'{caminho}: nenhuma linha de dados.')
        faltando = [c for c in OBRIGATORIAS if c not in linhas[0]]
        if faltando:
            raise SystemExit(
                f'{os.path.basename(caminho)}: coluna(s) obrigatória(s) ausente(s): '
                f'{faltando}\ncolunas do arquivo: {list(linhas[0])}\n'
                f'O layout do tracker mudou — revise o mapa antes de importar.')
        nome = os.path.basename(caminho)
        for i, b in enumerate(linhas, start=2):   # 2 = linha do arquivo (1 é cabeçalho)
            brutas.append((nome, i, b))

    out: list[dict] = []
    pernas: list[dict] = []
    for arq, i, b in brutas:
        crua = limpa(b[COL_DATA])
        try:
            momento = dt.datetime.strptime(crua, '%d/%m/%Y %H:%M')
        except ValueError:
            raise SystemExit(
                f'{arq}:{i}: data ilegível {crua!r} (esperado dd/mm/aaaa hh:mm)')
        titulo = limpa(b[COL_TITULO])

        # PERNA de múltipla: repete data/título do cupom mas vem sem `Valor`.
        # Não é aposta — ver docstring. Sai listada no DRY.
        if _para_float(b[COL_STAKE]) is None:
            pernas.append({'_arq': arq, '_linha': i, 'data': momento.strftime('%d/%m/%Y'),
                           'descricao': titulo, 'odd': limpa(b[COL_ODD]),
                           'estado': limpa(b[COL_ESTADO]), '_tipo': limpa(b[COL_TIPO])})
            continue

        esporte_bruto = limpa(b[COL_ESPORTE])
        combo = _combo(titulo)
        lucro = _para_float(b[COL_LUCRO])
        resultado, res_corrigido = resultado_com_financeiro(
            b[COL_ESTADO], _para_float(b[COL_GANHO]), lucro)
        # `Multipla`/`Tripla`/`Bingo` = 3+ seleções → esporte `Múltiplos` (§2).
        # `dupla` declara DUAS e mantém o esporte do jogo.
        esporte = 'Múltiplos' if combo == 'acumulada' else norm_esporte(esporte_bruto)

        out.append({
            'data': momento.strftime('%d/%m/%Y'),
            '_dt': momento,
            '_arq': arq,
            '_linha': i,
            'esporte': esporte,
            'tipster': norm_tipster(b[COL_TIPSTER]),
            'casa': norm_casa(b[COL_CASA], casa_vazia),
            'parceiro': PARCEIRO,
            'aposta': norm_categoria(titulo, combo),
            'descricao': titulo,
            'stake': fmt_stake(b[COL_STAKE]),
            'odd': norm_odd(b[COL_ODD]),
            'resultado': resultado,
            '_res_corrigido': res_corrigido,
            '_lucro': lucro,                         # conferência do DRY
            '_ganho': _para_float(b[COL_GANHO]),
            '_esporte_bruto': esporte_bruto,
            '_casa_bruta': limpa(b[COL_CASA]),
            '_tipster_bruto': limpa(b[COL_TIPSTER]),
            '_estado_bruto': limpa(b[COL_ESTADO]),
            '_tipo': limpa(b[COL_TIPO]),
            '_combo': combo,
        })
    # O export vem do mais recente para o mais antigo; a numeração é cronológica.
    out.sort(key=lambda r: (r['_dt'], r['_arq'], r['_linha']))
    return numerar(out), pernas


def numerar(rows: list[dict]) -> list[dict]:
    """Código SO<aaaamm>-<n>. Numeração MENSAL (reinicia em 1 a cada mês), na
    ordem cronológica."""
    contador: dict[str, int] = defaultdict(int)
    for r in rows:
        mes = f"{r['_dt']:%Y%m}"
        contador[mes] += 1
        r['codigo'] = f'{PREFIXO}{mes}-{contador[mes]}'
        r['_mes'] = mes
    return rows


# ---------- assinatura (idêntica a repository._assinatura) ----------
# COM código o hash é `ID|casa|parceiro|codigo` — o CONTEÚDO não entra.
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


# ---------- P/L ----------
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


# ---------- conferência das casas contra o BANCO ----------
async def conferir_casas(casas: list[str]) -> dict:
    """Para cada grafia de destino: quantas linhas já existem no banco com ela, e
    que gêmeas (mesma chave sem caixa/pontuação) existem com OUTRA grafia.

    Medição vale mais que asserção em comentário: o dia que alguém unificar uma
    casa, o `_CASA_MAP` daqui fica velho e este relatório acusa."""
    import asyncpg
    url = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://', 1)
    conn = await asyncpg.connect(url, command_timeout=120)
    try:
        banco = {r['casa']: r['n'] for r in
                 await conn.fetch('SELECT casa, COUNT(*) n FROM bilhetes GROUP BY 1')}
    finally:
        await conn.close()
    por_chave: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for nome, n in banco.items():
        por_chave[_k(nome)].append((nome, n))
    return {c: {'exata': banco.get(c, 0),
                'gemeas': [(g, n) for g, n in por_chave.get(_k(c), []) if g != c]}
            for c in casas}


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
            'SELECT username, status, email, length(senha_hash) AS h, bot_habilitado '
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
              f'e-mail={u["email"]} | hash={u["h"]} chars | '
              f'bot_habilitado={u["bot_habilitado"]}')

        ja = await conn.fetchval('SELECT COUNT(*) FROM bilhetes WHERE dono=$1', dono)
        print(f'  base atual de {dono}: {ja} bilhete(s)')

        # ── GUARD DE COLISÃO COM O BOT ──────────────────────────────────────
        # Planilha e bot escrevem na MESMA série `SO<aaaamm>-<n>`, e o código
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
            conn = await asyncpg.connect(url, command_timeout=300)
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
                print(f'\n⚠ ÚLTIMO CÓDIGO GRAVADO: {rows[-1]["codigo"]}. Se ele passar a '
                      f'usar o bot, suba o contador (/contador N no apoio) para além dele '
                      f'ANTES da 1ª aposta — planilha e bot escrevem na MESMA série.')
                return
            finally:
                await conn.close()
        except Exception as e:                       # noqa: proxy instável → retry
            last_err = e
            print(f'  [tentativa {tentativa}] falhou: {type(e).__name__}: {e}')
    raise SystemExit(f'import falhou após 3 tentativas: {last_err}')


# ---------- relatório do DRY ----------
def _relatorio(rows, pernas, dono, casa_vazia, casas_banco):
    print(f'DONO={dono!r} | tipster padrão={TIPSTER!r} | conta={PARCEIRO!r} por casa')
    print(f'bilhetes: {len(rows)} | pernas descartadas: {len(pernas)}')
    datas = sorted(r['_dt'] for r in rows)
    print(f'período: {datas[0]:%d/%m/%Y} → {datas[-1]:%d/%m/%Y} | '
          f'códigos {rows[0]["codigo"]} … {rows[-1]["codigo"]}')

    # ── pernas de múltipla ───────────────────────────────────────────────────
    if pernas:
        print(f'\n— {len(pernas)} linha(s) DESCARTADA(s): perna de múltipla '
              f'(sem `Valor`; ver docstring) —')
        for p in pernas:
            print(f'    {p["_arq"]}:{p["_linha"]} | {p["data"]} | Tipo={p["_tipo"]!r} | '
                  f'Estado={p["estado"]!r} | @{p["odd"]} | {p["descricao"][:55]}')

    # ── interseção entre os arquivos ─────────────────────────────────────────
    arqs = sorted({r['_arq'] for r in rows})
    if len(arqs) > 1:
        def chave(r):
            return (r['data'], r['descricao'], r['odd'], r['stake'])
        conj = {a: {chave(r) for r in rows if r['_arq'] == a} for a in arqs}
        inter = set.intersection(*conj.values())
        marca = '✔' if not inter else '⚠'
        print(f'\n{marca} interseção entre os {len(arqs)} arquivos: {len(inter)} '
              f'linha(s) com mesma data+descrição+odd+stake')
        for k in list(inter)[:10]:
            print(f'    {k}')
        if inter:
            print('    ⚠ Se for re-exportação, isto DUPLICA o histórico — cada '
                  'ocorrência ganha código próprio. Confira antes do --go.')

    # ── por mês ──────────────────────────────────────────────────────────────
    print('\n— por mês —')
    for mes in sorted({r['_mes'] for r in rows}):
        sub = [r for r in rows if r['_mes'] == mes]
        t = sum(_para_float(r['stake']) or 0 for r in sub)
        p = sum(v for r in sub
                if (v := _pl_derivado(r['stake'], r['odd'], r['resultado'])) is not None)
        print(f'  {mes}  {len(sub):>5} | {sub[0]["codigo"]:<12} … {sub[-1]["codigo"]:<12}'
              f' | {t:>8,.2f}u | {p:>+8,.2f}u | ROI {100 * p / t if t else 0:>+6.2f}%')

    # ── casas ────────────────────────────────────────────────────────────────
    print('\n— casas (grafia do arquivo → destino; "banco" = linhas já existentes) —')
    pares = Counter((r['_casa_bruta'], r['casa']) for r in rows)
    novas, gemeas = [], []
    for (bruta, destino), n in sorted(pares.items(), key=lambda kv: -kv[1]):
        info = casas_banco.get(destino) if casas_banco else None
        if info is None:
            marca, extra = ' ', ''
        else:
            marca = '  ' if info['exata'] else '🆕'
            extra = (f" | banco: {info['exata']:,}" if info['exata']
                     else ' | banco: NÃO EXISTE (casa nova)')
            if not info['exata']:
                novas.append(destino)
            if info['gemeas']:
                extra += f" | ⚠ GÊMEA no banco: {info['gemeas']}"
                gemeas.append((destino, info['gemeas']))
        rotulo = f'{bruta!r}' if bruta else "'' (vazia)"
        seta = '' if bruta == destino else f' → {destino!r}'
        print(f'  {marca} {n:>5}  {rotulo:<24}{seta}{extra}')
    if novas:
        print(f'\n  🆕 {len(novas)} casa(s) NOVA(s) no banco: {sorted(set(novas))}')
        print('     Favicon vive em TRÊS mapas (app/static/index.html, '
              'dash/assets/js/data.js, inicio.html) — passo separado, depois do import.')
    if gemeas:
        print(f'\n  ⚠ {len(gemeas)} destino(s) com gêmea de outra grafia no banco. '
              f'Unificar é tarefa à parte (scripts/unificar_casas.py).')
    n_vazia = sum(1 for r in rows if not r['_casa_bruta'])
    if n_vazia:
        por_mes = Counter(r['_mes'] for r in rows if not r['_casa_bruta'])
        print(f'\n  {n_vazia} linha(s) SEM casa no arquivo → {casa_vazia!r} '
              f'(por mês: {dict(sorted(por_mes.items()))})')

    # ── tipster ──────────────────────────────────────────────────────────────
    print('\n— tipster —')
    for t, n in Counter(r['tipster'] for r in rows).most_common():
        sub = [r['_dt'] for r in rows if r['tipster'] == t]
        print(f'  {t:<14} {n:>5}  {min(sub):%d/%m/%Y} → {max(sub):%d/%m/%Y}')

    # ── esporte / categoria / resultado ──────────────────────────────────────
    print('\n— esporte —')
    for e, n in Counter(r['esporte'] for r in rows).most_common():
        print(f'  {e:<14} {n:>5}')
    print('\n— categoria (aposta) —')
    for a, n in Counter(r['aposta'] for r in rows).most_common():
        print(f'  {a:<16} {n:>5}')
    print('\n— resultado —')
    for res, n in Counter(r['resultado'] or '(aberta)' for r in rows).most_common():
        brutos = Counter(r['_estado_bruto'] for r in rows
                         if (r['resultado'] or '(aberta)') == res)
        print(f'  {res:<10} {n:>5}   ← {dict(brutos)}')

    # ── categoria por ERA (o dicionário é um só; isto confere que ele cobre as duas) ──
    print('\n— categoria por ERA (o mesmo dicionário lê as duas grafias) —')
    e1 = [r for r in rows if r['_dt'] < CORTE_ERA]
    e2 = [r for r in rows if r['_dt'] >= CORTE_ERA]
    cats = sorted({r['aposta'] for r in rows})
    print(f'  {"":<16} {"ERA 1 (verbosa)":>16} {"ERA 2 (código)":>16}')
    for cat in cats:
        a = sum(1 for r in e1 if r['aposta'] == cat)
        b = sum(1 for r in e2 if r['aposta'] == cat)
        print(f'  {cat:<16} {a:>16} {b:>16}')
    print(f'  {"TOTAL":<16} {len(e1):>16} {len(e2):>16}')

    # ── amostras da classificação, para conferir a olho ──────────────────────
    print('\n— amostra por categoria (2 de cada era) —')
    for cat in cats:
        for nome, sub in (('E1', e1), ('E2', e2)):
            ex = [r for r in sub if r['aposta'] == cat][:2]
            for r in ex:
                print(f'  {cat:<16} {nome} | {r["descricao"][:62]}')

    # ── `Outros`: o que a escada não classificou ─────────────────────────────
    outros = [r for r in rows if r['aposta'] == 'Outros']
    if outros:
        print(f'\n⚠ {len(outros)} linha(s) caíram em `Outros` (nenhuma regra casou):')
        for r in outros[:25]:
            print(f'    {r["codigo"]} | {r["data"]} | @{r["odd"]:<9} | {r["descricao"][:60]}')
        if len(outros) > 25:
            print(f'    … e mais {len(outros) - 25}')

    # ── mercado não identificado ─────────────────────────────────────────────
    sets = [r for r in rows if _RE_PLAYER.search(_grafia(r['descricao']))
            and r['aposta'] == 'Player Props']
    if sets:
        print(f'\n⚠ {len(sets)} linha(s) com mercado NÃO identificado → `Player Props` '
              f'(estatística de jogador sem categoria própria; corrigir na grade):')
        for r in sets[:20]:
            print(f'    {r["codigo"]} | {r["data"]} | @{r["odd"]:<9} | {r["descricao"][:50]}')
        if len(sets) > 20:
            print(f'    … e mais {len(sets) - 20}')

    # ── rótulo × dinheiro ────────────────────────────────────────────────────
    corr = [r for r in rows if r.get('_res_corrigido')]
    if corr:
        print(f'\n⚠ {len(corr)} linha(s) com `Estado=Perdida` mas `Lucro=0,00` na '
              f'fonte → gravadas como `V` (perda de verdade tem Lucro = −stake):')
        for r in corr:
            print(f'    {r["codigo"]} | {r["data"]} | {r["descricao"][:38]:<38} | '
                  f'u={r["stake"]} @{r["odd"]} | fonte dizia Perdida, Lucro={r["_lucro"]}')

    # ── odds impossíveis ─────────────────────────────────────────────────────
    odd_ruim = [r for r in rows if (_para_float(r['odd']) or 0) < 1.01
                or (_para_float(r['odd']) or 0) > 2000]
    if odd_ruim:
        print(f'\n⚠ {len(odd_ruim)} linha(s) com odd implausível (< 1,01 ou > 2.000):')
        for r in sorted(odd_ruim, key=lambda r: -(_para_float(r['odd']) or 0)):
            pl = _pl_derivado(r['stake'], r['odd'], r['resultado'])
            nota = ('cashout: retorno < stake com Estado=Ganha '
                    '(MASTER_RESULTADO §5.6, odd = cashout ÷ stake)'
                    if r['resultado'] == 'W' else
                    'PERDIDA — o P/L é −stake e NÃO depende da odd; corrigir na grade')
            print(f'    {r["codigo"]} | {r["data"]} | {r["descricao"][:32]:<32} | '
                  f'@{r["odd"]:<10} u={r["stake"]} {r["resultado"]} P/L={pl:+.2f} | {nota}')

    sem_odd = [r for r in rows if not r['odd']]
    if sem_odd:
        print(f'\n⚠ {len(sem_odd)} linha(s) sem odd')
    sem_stake = [r for r in rows if (_para_float(r['stake']) or 0) <= 0]
    if sem_stake:
        print(f'\n⚠ {len(sem_stake)} linha(s) com stake 0: gravadas, porém INVISÍVEIS no '
              f'dashboard (dashboard_rows corta stake <= 0)')

    # ── unicidade ────────────────────────────────────────────────────────────
    sigs = [assinatura(r) for r in rows]
    cods = [r['codigo'] for r in rows]
    print(f'\ncódigos: {len(set(cods))} únicos de {len(cods)}')
    print(f'assinaturas: {len(set(sigs))} únicas de {len(sigs)}')

    # ── conferência contra as colunas Ganho/Lucro da própria fonte ───────────
    # Se o P/L derivado divergir, a normalização (odd, stake, resultado) quebrou.
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

    print('\n— por era —')
    for nome, sub in (('ERA 1 (título verboso)', e1), ('ERA 2 (título em código)', e2)):
        if not sub:
            continue
        t = sum(_para_float(r['stake']) or 0 for r in sub)
        p = sum(v for r in sub
                if (v := _pl_derivado(r['stake'], r['odd'], r['resultado'])) is not None)
        g = sum(1 for r in sub if r['resultado'] == 'W')
        print(f'  {nome:<26} {len(sub):>5} apostas | {t:>8,.2f}u | {p:>+8,.2f}u | '
              f'ROI {100 * p / t if t else 0:>+6.2f}% | green {g} '
              f'({100 * g / len(sub):.1f}%)')

    print('\n— amostra (10 primeiras) —')
    for r in rows[:10]:
        print(f'  {r["codigo"]:<14} {r["data"]} | {r["esporte"]:<10} | '
              f'{r["aposta"]:<14} | {r["casa"]:<10} | {r["tipster"]:<10} | '
              f'{r["descricao"][:40]:<40} | u={r["stake"]:<6} @{r["odd"]:<8} '
              f'{r["resultado"]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--csv', required=True, nargs='+',
                    help='caminho(s) do(s) CSV (os dois arquivos do SOH PROPS)')
    ap.add_argument('--dono', required=True,
                    help='USERNAME do cadastro (conferido em `usuarios`; NÃO é a marca)')
    ap.add_argument('--casa-vazia', default=CASA_VAZIA_PADRAO,
                    help=f'casa para as linhas sem `Casa de apostas` '
                         f'(padrão {CASA_VAZIA_PADRAO!r}, decisão do Feca em 03/09/2026; '
                         f'passe "" para abortar em vez de preencher)')
    ap.add_argument('--sem-banco', action='store_true',
                    help='DRY sem consultar o banco (pula a conferência das casas)')
    ap.add_argument('--go', action='store_true', help='escreve no banco (default: DRY)')
    a = ap.parse_args()

    rows, pernas = carregar_rows(a.csv, a.casa_vazia)

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

    casas_banco = None
    if not a.sem_banco:
        carregar_env()
        casas_banco = asyncio.run(conferir_casas(sorted({r['casa'] for r in rows})))

    _relatorio(rows, pernas, a.dono, a.casa_vazia, casas_banco)

    if not a.go:
        print('\n[DRY] nada foi escrito. Use --go para gravar.')
        return
    carregar_env()
    asyncio.run(importar(rows, a.dono))


if __name__ == '__main__':
    main()
