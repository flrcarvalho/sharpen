# Auditoria forense do histórico git do Sharpen

Repo: `Planilhador`, 1.745 commits (14/06/2026 a 17/11/2026). Lente: os DIFFS são o fato; a mensagem de commit só foi usada para rotular (tipo `fix`/`feat`) e para achar candidatos, e cada família abaixo foi conferida lendo o diff de commits-exemplo. CLAUDE.md, STATUS, BACKLOG, docs/ e memória não foram usados como explicação.

Scripts e dados brutos: `aud_git/a1.py` ... `a14.py`, `numstat.txt`, `blame.json` (blame do pai de cada um dos 530 commits de fix, linha a linha), `chains.json`.

Ressalvas de método:
- "Fix" = assunto começando com `fix`/`revert` (498 commits). Há `feat` que são conserto e `fix` que são ajuste visual; a família foi decidida pelo diff nos exemplos, mas as contagens por família vêm de palavra-chave e são aproximadas (±20%).
- "Fix-de-fix" = o fix altera ou apaga linhas que o `git blame` do pai atribui a um commit de até 14 dias antes. Em arquivos de 7 a 11 mil linhas isso dá algum falso positivo de vizinhança; as cadeias listadas foram conferidas.
- Junho e novembro são meses parciais (17 dias cada).

---

## 1. Ritmo

### 1.1 Por mês

| mês | commits | commits/semana | feat | fix | docs | fix/(feat+fix) | linhas de código/semana |
|---|---|---|---|---|---|---|---|
| 2026-06 (17 d) | 345 | 142 | 87 | 104 | 122 | 54% | 9.065 |
| 2026-07 | 548 | 124 | 177 | 155 | 165 | 47% | 15.141 |
| 2026-08 | 203 | 46 | 64 | 58 | 74 | 48% | 8.103 |
| 2026-09 | 401 | 94 | 105 | 107 | 170 | 50% | 17.238 |
| 2026-10 | 183 | 41 | 76 | 44 | 53 | 37% | 12.659 |
| 2026-11 (17 d) | 62 | 26 | 29 | 26 | 7 | 47% | 11.699 |

Leitura: o NÚMERO de commits caiu para 1/4 do início, mas as linhas de código por semana não caíram (11 a 17 mil). Os commits ficaram 4 a 5 vezes maiores: em outubro e novembro um commit típico de "casa nova" toca 11 a 18 arquivos de código.

### 1.2 Por semana (fix% = fix/(feat+fix))

```
sem   n   feat fix  fix%   linhas_cod
S24   37    6  14   70%   ##############
S25  103   22  42   66%   #############
S26  114   33  24   42%   ########
S27  238   83  56   40%   ########
S28   98   29  28   49%   #########
S29  162   55  43   44%   ########
S30  112   24  48   67%   #############   (auditoria Turbo 19-20/07)
S31   52   24   4   14%   ##
S32   67   12  31   72%   ##############  (varredura "Escada de Tinta": 21 fix de CSS em 1 dia)
S33   27    9   9   50%   ##########
S34   28   10   3   23%   ####
S35   47   18  14   44%   ########
S36   84   19  30   61%   ############    (Caixa, s314-s327)
S37  121   38  18   32%   ######
S38  101   31  29   48%   #########
S39   94   20  28   58%   ###########     (bet365 Resolver: 14 fix em 2 dias)
S40   51   18  10   36%   #######
S41   52   18  15   45%   #########       (moeda, freebet, Ficha s409)
S42   46   15  10   40%   ########
S43   22   10   6   38%   #######
S44   35   21   8   28%   #####
S45   17   14   2   12%   ##
S46   30    7  20   74%   ##############  (CopaWin/Stake/Cloudbet/Ficha, s443-s457)
```

### 1.3 Existe um ponto de inflexão?

Não na taxa de defeito por feature. Medido pelo blame (quantos `feat` com código tiveram linhas alteradas por um fix em até 30 dias):

| mês do feat | feats c/ código | precisaram de fix em 30 d | fixes atribuídos |
|---|---|---|---|
| 06 | 78 | 28 (36%) | 66 |
| 07 | 169 | 64 (38%) | 106 |
| 08 | 55 | 16 (29%) | 22 |
| 09 | 91 | 33 (36%) | 64 |
| 10 | 76 | 28 (37%) | 37 |
| 11 | 28 | 4 (14%, janela incompleta) | 4 |

A taxa é estável em ~36% desde o primeiro dia: **um em cada três features precisa de conserto em 30 dias, e isso nunca mudou**. O que mudou foi a SUPERFÍCIE onde esse terço cai e a natureza da falha (ver §1.4 e §4). A sensação "funcionava e parou" bate com três adições estruturais concentradas em ~10 semanas:

| janela | o que entrou (diff) | efeito medido |
|---|---|---|
| 03/09 a 14/09 | Caixa Inteligente (`_caixa_*`, s314), **barreira de recaptura** (`c357847`/`2143c06`, 09/09: pular bloco "já visto"), custo por janela | a barreira ficou MORTA 11 dias sem ninguém ver (`eaa3788`, 20/09) |
| 03/10 a 12/10 | moeda/câmbio (s390-s398), freebet, **Ficha + virada** (`4ac4519`, `e919499`, `53f4609`: o servidor passa a decidir pelo JSON cru e a SEGURAR aposta) | linhas que "recusam/seguram/pulam/descartam" no núcleo: 76 (01/10) para 189 (01/11) |
| 03/10 a 16/11 | ~30 casas novas na extensão (uma a cada 1,5 dia), metade de plataforma própria | 13 de 42 casas tiveram fix em 30 dias; nas de plataforma própria, quase todas |

Origem dos 66 fixes com código desde 01/10 (commit dono da maioria das linhas alteradas): casa nova/extensão 21 · Ficha/virada/barreira 19 · moeda/freebet/Caixa/Polymarket 14 · outros 12. **82% dos consertos de out-nov limpam código de out-nov.**

Idade mediana das linhas que os fixes alteram: jun 0,3 d · jul 1,0 d · ago 13,3 d · set 0,9 d · out 0,7 d · **nov 25,5 d**. Em novembro, pela primeira vez, o conserto típico mexe em código com quase um mês de produção: o defeito ficou um mês na mão do usuário antes de ser visto.

### 1.4 Crescimento estrutural

Arquivos principais (linhas):

| data | main.py | repository.py | static/index.html | dash/app.js | ext/content.js | database.py |
|---|---|---|---|---|---|---|
| 20/06 | 735 | 374 | 1.612 | 0 | 0 | 76 |
| 01/07 | 1.308 | 941 | 4.169 | 1.141 | 0 | 126 |
| 01/08 | 2.800 | 2.541 | 6.058 | 1.350 | 2.933 | 330 |
| 01/09 | 4.119 | 3.098 | 6.746 | 1.416 | 5.615 | 676 |
| 15/09 | 5.082 | 4.838 | 9.330 | 1.884 | 6.168 | 972 |
| 01/10 | 5.661 | 5.230 | 9.674 | 1.964 | 6.672 | 1.056 |
| 15/10 | 6.344 | 6.495 | 10.609 | 1.981 | 7.448 | 1.368 |
| 17/11 | 6.843 | 7.156 | 11.803 | 1.996 | 9.174 | 1.492 |

Em bytes, hoje: `index.html` 711 KB (JS inline), `content.js` 532 KB, `repository.py` 373 KB, `main.py` 354 KB.

Composição do repo:

| data | .py em app/ | JS da extensão | arquivos de teste | scripts/ | .md |
|---|---|---|---|---|---|
| 30/06 | 7 (133 KB) | 0 | 0 | 5 | 522 KB |
| 31/07 | 10 (354 KB) | 13 (278 KB) | 26 | 20 | 1,7 MB |
| 31/08 | 14 (524 KB) | 24 (603 KB) | 52 | 39 | 2,5 MB |
| 30/09 | 17 (821 KB) | 25 (764 KB) | 123 | 79 | 3,8 MB |
| 15/10 | **33** (1,18 MB) | 29 (902 KB) | 163 | 86 | 4,2 MB |
| 17/11 | 46 (1,46 MB) | 37 (1,17 MB) | 193 | 102 | 4,6 MB |

Entre 30/09 e 15/10 o número de módulos Python dobrou (17 para 33): é a camada Ficha (`ficha.py`, `virada.py`, `dicionario.py`, `descricao_ficha.py`, `cru.py`, `sombra_numeros.py`, `app/adaptadores/*`), que se pendura no MESMO caminho `/extrair` -> `/salvar` -> `upsert_bilhetes`.

Funções do caminho crítico (linhas e nº de parâmetros, via `ast`):

| data | upsert_bilhetes | extrair | blocos_conhecidos | get_codigos_resolvidos | virada.resolver_no_extrair |
|---|---|---|---|---|---|
| 01/07 | 169 (4) | 113 (9) | - | 20 (2) | - |
| 01/09 | 329 (6) | 173 (10) | - | 23 (4) | - |
| 15/09 | 433 (7) | 201 (10) | 36 (4) | 23 (4) | - |
| 15/10 | 496 (9) | 219 (10) | 38 (4) | 23 (4) | 47 (6) |
| 17/11 | **568 (10)** | 250 (11) | **81 (6)** | 40 (5) | 97 (9) |

Docs: 591 commits (34% do total) são só de documentação; até setembro, 246 commits/mês tocavam STATUS/BACKLOG.

---

## 2. Hotspots (últimos 90 dias, desde 19/08)

478 commits tocaram app/extensor/scripts/tests; 199 são fix.

### 2.1 Arquivos mais tocados por commits de fix

| commits de fix | linhas | arquivo |
|---|---|---|
| 43 | 97 | extensor/manifest.json (bump de versão) |
| 37 | 224 | app/changelog.json |
| 37 | 146 | app/static/dash/index.html (quase só `?v=`) |
| 34 | 1.473 | extensor/content.js |
| 30 | 1.510 | app/repository.py |
| 29 | 1.357 | app/static/index.html |
| 26 | 897 | app/main.py |
| 16 | 473 | dash/assets/css/components.css |
| 13 | 695 | extensor/harness/casos/bet365.mjs |
| 10 | 338 | app/virada.py |
| 10 | 945 | extensor/b3_inject.js |

Os três primeiros são burocracia de VERSÃO e CACHE: 117 toques em 90 dias só para dizer ao navegador e à extensão que algo mudou (ver família C).

### 2.2 Funções mais tocadas por commits de fix (hunk mapeado para a função que o contém, via `ast` no Python e regex no JS)

| fixes | função | exemplos |
|---|---|---|
| 18 | main.py nível de módulo (registros/constantes por casa) | 5b45387 8baadbd b78ea69 761c74d |
| 15 | repository.py nível de módulo (SQL/constantes) | 8baadbd 6083cad 761c74d |
| 8 | content.js `processar` | e0161c1 b78ea69 0e2f003 f116a1a 76f1805 |
| 8 | main.py `_stream_sequential` | 761c74d e36745b 2b3360a 9d5a66c 7d223be |
| 8 | main.py `_stream_parallel` | **os mesmos 8 commits** |
| 7 | captura.py nível de módulo (`_MODO_POR_CASA`, `_HOSTS_POR_CASA`, `CASAS_COM_FICHA`) | ea9de0e 28cdc4b cf0e3b8 a58b362 |
| 6 | virada.py `aplicar` | 5b45387 7228c2b 3694269 8baadbd edda986 |
| 6 | main.py `_dedup_superbet_text` (166 linhas; é a barreira/pré-dedup de TODAS as casas, com nome de uma) | 3694269 8baadbd 8caaacb 8e16a6b 761c74d |
| 6 | repository.py `upsert_bilhetes` | 8baadbd b78ea69 6083cad 90fb343 e87bb8c |
| 6 | b3_inject.js `resolverAbertas` | d194caa 263ce9d 6f8b523 52749af |
| 4 | repository.py `_caixa_projetar` | 2d4139b f63e21d cb92739 5dc9eb4 |
| 4 | content.js `conferir` | a0a560a e0161c1 55cd675 b78ea69 |
| 4 | repository.py `_financeiro_do_texto` | e8ce01f 60b0623 3a7f675 7d8952f |
| 3 | repository.py `blocos_conhecidos` | 8caaacb 8e16a6b eaa3788 |
| 3 | content.js `_resultadoCW` | 075ee6e d902a84 27fe6a3 |
| 3 | repository.py `_veredito_do_retorno`, `corrigir_stake_tsv`, `_caixa_abertas_ids`, `caixa_lancar` | ... |
| 3 | dash app.js `atualizarOpcoesFiltros` | 76f8f44 91f95fa d9be460 |

Achado direto: `_stream_sequential` e `_stream_parallel` são duas cópias do pós-processamento da extração (leitor, repescagem, cobertura). Todo conserto do pós-processamento é aplicado duas vezes (conferido no diff de `761c74d`: o mesmo bloco `_leitor(..., final=True)` + recálculo de cobertura entra nas duas). Esquecer uma das cópias é regressão silenciosa garantida para um dos dois modos (lote pequeno ou grande).

---

## 3. Fix-de-fix

| mês | fixes com código | alteram linhas de ≤14 d (≥20% das linhas) | dessas, o dono era outro fix | era um feat |
|---|---|---|---|---|
| 06 | 70 | 70 (100%) | 19 | 30 |
| 07 | 143 | 118 (83%) | 36 | 81 |
| 08 | 48 | 27 (56%) | 3 | 23 |
| 09 | 84 | 65 (77%) | 12 | 51 |
| 10 | 44 | 33 (75%) | 4 | 28 |
| 11 | 22 | 11 (50%) | 6 | 5 |

27 cadeias fix -> fix -> fix (cada elo mexe nas linhas do anterior em ≤14 d). As mais longas:

1. **Ordem/chunk/cobertura da extração por IA, 11 elos, 20/06 a 25/07**: f484a31 -> 06f1455 -> cb5573c -> 50af1a1 -> fc149a6 (Superbet) -> d99dca0 (Superbet) -> 8eecf76 (Bet365) -> 8cff103 (Betano) -> 08926c6 -> fc81f47 (Betfair "fora do gabarito por acidente") -> 831f97f (Bet365 "religa o guarda"). Ramos paralelos: 7df73a3/7cf11ae ("Pinnacle entra no chunking e no pré-dedup"), 5376a0b (Betfair). Comum: a mesma regra (ordem determinística, marcador de código, cobertura) aplicada casa por casa, com listas de casas que esquecem uma.
2. **Bet365 Resolver de abertas, 5+4 elos em 24-25/09**: 2bb2888, 7805622, 44e2e3a, e448a25, ba9cbce, 90f5388, 2d98903, 52749af, 6f8b523, d194caa, 8ab2cdd. Comum: tentativa e erro contra a API da casa em produção (14 fix em 2 dias, `diag` intercalado).
3. **Auditoria Turbo, 6 elos em 19-20/07**: 31166ad -> 1923052 -> **9394553 (revert do 1923052 no mesmo dia)** -> 2572e90 -> 3cfc12a -> 570bd89.
4. **Financeiro contra o bloco, 3 elos 01/09 a 13/09**: 7d8952f (stake sai da IA) -> 3a7f675 (odd e resultado contra o retorno) -> 60b0623 (a odd do bloco decide antes da odd da IA: "39 meias vitórias gravadas como W"). Cada elo descobriu o campo vizinho do anterior.
5. **Stake.com, 3 elos 11 a 14/11**: b78ea69 (XMulti ficava aberta) -> 55cd675 (múltipla de props com perna anulada) -> a0a560a (múltipla SportBet com perna anulada). Mesma condição em `content.js`, alargada um tipo de bilhete por vez.
6. **CopaWin, 3 elos em 14/11 (mesmo dia)**: 27fe6a3 (cashout) -> d902a84 (múltipla com perna anulada) -> 075ee6e (meia vitória asiática). Dois dias depois do feat 60e9da4.
7. **Barreira/Ficha "já visto", 4 elos 20/10 a 12/11**: 8e16a6b (`gravados=True`) -> 8caaacb (`exigir_linha=False`) -> 4734b0b (`cru_recusado` lido como "cru aberto") ; ramo 3694269/7228c2b. Cada elo acrescenta um parâmetro ou um caso ao mesmo predicado.
8. **UI em sequência**: 4f3c12e -> 7c13385 -> 5b9ac8f (cartões 180 -> 156 -> 140 -> 120 px em 2 dias); 545ba47 -> f3bd982 (revert) -> e8a2ca3.

Reverts e restaurações no diff: 70e2be9 (Betfair chunker, perdia bilhetes em silêncio), 9394553 (solidez), f3bd982 (grade), **2b3360a: "restaura o main.py da e2427d4 que o commit 9d5a66c desfez"** (o fix 9d5a66c apagou 95 de 98 linhas de um feat de outra sessão feito no MESMO dia; o blame confirma). Mais 8 commits de docs registram "o commit X levou o trabalho da sessão vizinha" (13/09, 14/09, 15/09, 23/09, 29/09, 09/10, 11/10, 11/11), e `ca32978`/`d779315` (23/09) consertam deploy quebrado porque `main.py` publicado importava um módulo que outra sessão não tinha commitado.

O que as cadeias têm em comum: **a regra é implementada por instância (por casa, por tipo de bilhete, por modo de streaming, por campo) e cada elo descobre a próxima instância em produção.** Nenhum elo generaliza a regra; o elo seguinte acrescenta um `if`, uma casa na lista ou um parâmetro.

---

## 4. Famílias recorrentes (mecanismo lido no diff)

Contagem de commits `fix` por família e mês (classificação por palavra-chave, conferida por amostragem):

```
familia                                      06 07 08 09 10 11  total  ultima
L liquidacao/resultado por casa               3 10  5 10  7 14    49   17/11
B "ja visto" -> pula/segura (barreira/Ficha)  2  7  1  6  7  6    29   17/11
C frescor do cliente (cache/estado/versao)    4  8  1  5  1  0    19   03/10 (+ ver nota)
D identidade: dedup/assinatura/grafia/codigo  9 16  6  6  3  0    40   26/10
N numero: moeda/odd/stake/parse/tipo          7 10  3 10 11  0    41   19/10
F data/fuso                                   2  3  1  5  0  1    12   14/11
E API/dominio/rota da casa mudou              3 18  4  5  3  1    34   17/11
K caixa/custo/filtro/escopo                   3 15  4 19  7  1    49   12/11
P processo/deploy/CI/sessoes paralelas        5  4  0  9  1  1    20   01/11
U visual/layout                              16 21 21 15  0  0    73   24/09
I IA/prompt/taxonomia                        25 18  4  6  1  2    56   13/11
```

A tendência: as famílias de produto visual (U) e de prompt (I) secaram; as que crescem em novembro são **L e B**, ambas com o mesmo sintoma para o usuário: **a aposta fica aberta ou some, sem erro**.

### Família L: liquidação reimplementada por casa

- **Ocorrências**: ~24 commits de fix em 14 casas (mais as importações de dados que os acompanham). Últimas: 464d5c4 (17/11, Thunderpick), 075ee6e, d902a84, 27fe6a3 (14/11, CopaWin), a0a560a, 55cd675, b78ea69 (Stake.com), e0161c1 (Cloudbet), 0e2f003 (3et), f116a1a e 76f1805 (1win), edda986 (20bet), 25712f6 (MyStake), bda3f75 (Pinnacle DRAW), 739ef63 (Esportiva/VaideBet status 8), 157bc1f (Betfair Each Way), 2448a83/378b054 (Bet365 meia vitória), 314725a (Betano bônus), 56adf37 (Lottu boost), d3b49d9/07882ff (Polymarket).
- **Mecanismo comum (diff)**: cada casa tem um tradutor próprio de status para W/L/V/HW/HL (`_resultadoCW`, `_resultadoB3`, `formatTicketTP`... em `content.js`, mais `app/adaptadores/<casa>.py` no servidor). O ramo `else` diz literalmente "a conferir — não liquidar automaticamente" (visto em 27fe6a3). Cada casa nova nasce sem cashout, sem perna anulada, sem meia asiática, sem push, e cada um desses vira um fix separado quando um usuário tem o caso. Em 27fe6a3/d902a84/075ee6e a mesma fórmula de dinheiro (`retorno = stake × odd`, `= stake/2 × odd + stake/2`, `= stake/2`, `= stake`) é reescrita dentro de funções `_cashoutCW`, `_meiaCW`, que já existem em outra forma para outras casas e no servidor (`repository._veredito_do_retorno`).
- **Escala**: funções `_resultado*` em content.js: 0 (jun) -> 4 (jul) -> 12 (ago) -> 15 (out) -> 24 (nov). Casas de plataforma própria tiveram fix em 30 d: 1win 4, CopaWin 4, Stake.com 3, Cloudbet 2, 20bet 2, Shuffle 2, Betrebels 2, 3et 1, Thunderpick 1. Casas espelho (Altenar/BetBy/BetConstruct): 0 na maioria (Vavada, Kikobet, BetMartini, Tornadobet, Sportaza, Jack, GoldenBet, Locasbet, MelBet, 1xBit). **O modelo espelho funciona; o modelo "casa nova = tradutor novo" falha sempre do mesmo jeito.**
- **Por que o remendo não fechou**: cada fix acrescenta o caso para AQUELA casa (`if (b.status === "cashout")` dentro do bloco da CopaWin) e um fixture da casa (`harness/fixtures/copawin.cashout.json`). Nada obriga a casa seguinte a cobrir os quatro casos. Ainda vem acompanhado de script de dado (`liquidar_won_copawin_gabriel_s453.py`, `liquidar_presas_copawin_s453.py`): o defeito chega ao banco antes de ser visto.
- **Correção estrutural**: tirar a decisão de resultado das casas. Cada adaptador só extrai fatos (`liquidada?`, stake, retorno pago, odd da casa, pernas com status, flag de cashout); UMA função global decide W/L/V/HW/HL pelo dinheiro (é a `_veredito_do_retorno` que já existe). Status desconhecido + liquidada + retorno conhecido nunca fica aberto. Um teste de contrato único roda os mesmos ~8 cenários (simples W/L/V, cashout acima/abaixo/igual, múltipla com perna anulada, meia asiática, push) contra TODOS os adaptadores; casa nova sem os 8 fixtures reprova o CI.

### Família B: "já visto" que pula ou segura a aposta

- **Ocorrências**: 14 fixes desde a criação da barreira (09/09): eaa3788 (barreira morta 11 dias por coluna sem prefixo no JOIN), 9d5a66c (minúscula no código), 8e16a6b (leitura não salva libera o salto: "aposta aberta que liquidou ficava aberta para sempre"), 8257c28 e 7228c2b (código liquidado noutra casa/conta), 761c74d (cru recusado descartado em silêncio), edda986 (aposta excluída volta na recaptura), 8caaacb (aposta apagada e recapturada segurada "captura incompleta"), 4734b0b (recusa lida como "cru aberto"), 3694269 (liquidada pela rota do cru durante o /extrair), 8baadbd (reliquidação pulada pelo pré-dedup), 5b45387 (marca de lido por conta), 224d166 (dados: 4 apostas 1win presas). Última: 14/11 (+ 9a70608 e ea9de0e, travas novas que precisaram de exceção ou afrouxamento em 16-17/11).
- **Mecanismo comum (diff)**: três memórias de "já processado" que não são a verdade: `bloco_visto` (hash do bloco de texto, servidor), `cruEnviado` (extensão, não reenvia cru igual) e o pré-dedup `get_codigos_resolvidos`/`_dedup_superbet_text`. A decisão "pular" ou "segurar" consulta a memória, e a memória não é invalidada quando a linha real some (apagada pelo usuário), não chega (o `/salvar` não aconteceu), muda de conta, ou a casa reliquida. É uma família de **cache sem invalidação**, só que no servidor e na extensão, não no navegador.
- **Escala**: `blocos_conhecidos` passou de 4 para 6 parâmetros, dois deles booleanos que invertem o sentido (`gravados`, `exigir_linha`, com `assert not gravados` entre eles). `virada.py` tem 4 janelas de tempo heurísticas (`SEGURADA_EXTRAIRS=2`, `SEGURADA_HORAS=24`, `CRU_RECENTE_DIAS=7`, `JANELA_CRU`) e uma data cravada (`D39_DESDE = 2026-11-02`). Linhas com recusa/segura/pula/descarta/bloqueia em main+repository+virada+captura: 33 (01/08) -> 44 (01/09) -> 71 (15/09) -> 127 (15/10) -> 189 (01/11) -> 211 (17/11).
- **Por que o remendo não fechou**: cada fix adiciona uma condição à memória (mais uma flag, mais uma coluna, mais uma janela) em vez de trocar a pergunta. A pergunta continua "eu já vi este texto?" quando o que importa é "o banco tem esta aposta no estado que a casa mostra agora?".
- **Correção estrutural**: a memória só pode servir para ECONOMIZAR (não chamar a IA), nunca para DESCARTAR ou SEGURAR. Pular só quando o banco tem a linha com o mesmo veredito e o mesmo dinheiro que o bloco atual (comparação com a verdade, não com um hash). Toda aposta segurada precisa ter um estado visível com saída no próprio fluxo (não depender de reenvio da extensão). Um teste de propriedade: para qualquer sequência {capturar, apagar, recapturar, liquidar, reliquidar, mudar de conta, /salvar falhar}, o banco converge para o estado da casa.

### Família C: frescor do cliente (cache do navegador, estado global do front, versão da extensão)

- **Ocorrências**: ~19 fixes explícitos: 3961db8 (15/06, Cache-Control no root), c1b08e5 (29/07, "casca em cache escondia a tela nova"), 48c3575, 4e4da54, c7d9855, 238b446 (bumps de `?v=` esquecidos), 2996067 (recorte cacheado não invalidado no multiselect), d9be460 (opção de filtro congelava no primeiro paint), 56fc222 (sidebar não repinta quando a base recarrega), 5d2cd6e ("Carregando dados..." para sempre), 2ba5758 (painel não se atualizava), a4e507a/2d6cd01 (botão Atualizar não furava o cache da planilha viva), 90f5388 (botão da extensão travava quando a extensão era atualizada), 5fb8b6d/d22b73a/bd2db22 (estado salvo sobrescrito/apagado). Último explícito: 03/10.
- **Mecanismo comum (diff)**:
  1. Assets JS/CSS são servidos por `StaticFiles` sem `Cache-Control` (só HTML ganhou `no-cache` em c1b08e5). A renovação depende de bump MANUAL de `?v=N` no HTML. **47 de 236 commits (20%) que mudaram JS/CSS do dashboard não mexeram no `dash/index.html`** (ex.: todos os `data.js` de casa nova de 2d88a34, 60e9da4, 0b7b0ee, d09322e...; 7a0ba79 moeda EUR/AUD no app.js, consertado depois por 238b446). O mesmo `/static/shell.css` é referenciado como `?v=2` em `index.html`, `?v=3`/`?v=4` em `app.html` e `?v=4` em `dash/index.html` (o `index.html` nunca foi bumpado depois de 3 mudanças do arquivo); `tokens.css` mudou 5 vezes e não tem `?v=` em lugar nenhum.
  2. O front é estado global mutável (`DADOS`, `DADOS_ABERTAS`, `MSS`, `_filterCache`) com render sob demanda; dado que chega depois do primeiro render (fetch) não repinta sozinho. Cada tela consertada ganhou seu próprio evento/flag (`base-recarregada`, `_ctRepintou`, `atualizarOpcoesFiltros`).
  3. Extensão: 86 versões publicadas em 4 meses (`manifest.json`, 43 bumps em 90 dias). O servidor calcula `versao_desatualizada` e só AVISA no popup; captura de versão velha é aceita e processada com os tradutores velhos (família L) e sem o cru (família B). Distribuição manual.
- **Por que o remendo não fechou**: cada fix bumpa o `?v=` daquele arquivo, ou acrescenta um repinte naquela tela. Não há gate: o teste `tests/test_cache_headers.py` só confere que HTML revalida e asset continua cacheável; nada confere que asset alterado teve o `?v=` alterado.
- **Correção estrutural**: hash de conteúdo no nome/URL gerado no deploy (ou `?v=<sha do commit>` injetado pelo servidor em TODAS as tags) e fim do bump manual; um teste que falha se algum asset referenciado não tiver versão. No front, um único ponto de "dados mudaram -> repinta tudo que é visível". Na extensão, versão mínima por servidor: abaixo dela `/captura/enviar` recusa com mensagem acionável (ou o servidor ignora a decisão de resultado da extensão, se a família L for movida para o servidor, o que torna a versão irrelevante para a correção do dado).

### Família D: identidade (casa como texto livre, assinatura com campos mutáveis, código transcrito pela IA)

- **Ocorrências**: ~40. Exemplos: 9c3fae1 (JonBet x Jonbet: "a conta enxergava uma casa, o /salvar gravava outra"), c7811a7 (8 grafias duplicadas, 54 -> 45 casas), 0413f6a, d92cdab, b43a534 (Win.Bet x Win.bet, 26/10), ae72de5 e 50e68ee (editar/renomear não recalculava a assinatura), 3f19720 (órfã não adotada porque "14" != "14,00"), 7d223be e 90fb343 (código escrito pela IA/OCR), bdc16f2 (repescagem deixava a órfã), 918cb48 (stake entra na assinatura). Última: 26/10.
- **Mecanismo**: `casa` é string em pelo menos 7 tabelas, comparada por igualdade; a assinatura de dedup é hash de campos que o usuário pode editar (casa, parceiro); o código do bilhete chega pela IA. Cada grafia nova é uma casa nova; cada edição sem recálculo é duplicata futura.
- **Por que não fechou**: a normalização foi espalhada (`casa_oficial`, `casa_chave.py` criado em 01/11, `casaDisplay` no front, 4 mapas de favicon) e cada caminho novo de escrita precisa lembrar de chamar. `app/casa_chave.py` aparece modificado e não commitado no working tree de hoje.
- **Correção estrutural**: tabela `casas` com id inteiro; todas as tabelas guardam o id; a grafia só existe na tabela de casas. Assinatura baseada em ids imutáveis + código nativo da casa; nunca em texto exibível.

### Família N: número (parsers múltiplos, tipos, moeda)

- **Ocorrências**: ~41. 5452e49 ("a tela Custos lia 179.90 como 17.990, o `_c2num` tinha régua própria"), a524810 (U+2212 e milhar ao reordenar), ff6642c, 2b37a1a (`_numBR`), 155a39e e 23bb223 (asyncpg recusa float em NUMERIC e string em DATE, no mesmo INSERT, dois fixes), ec50274, 3d4b275, 6b52cda, ad6172f, 8ba8b91, c2b4c1f. Última: 19/10.
- **Mecanismo**: cada camada (extensão, IA, servidor, front, scripts) tem seu parser de número BR/EN; a fronteira com o banco não converte tipo.
- **Por que não fechou**: o parser "certo" (`parseNum`, `_num_bloco`) foi criado, mas os antigos continuam existindo e novos aparecem a cada tela/casa.
- **Correção estrutural**: números viajam como número desde a extensão (o JSON cru já tem número); um único parser por linguagem, e um lint que proíbe `parseFloat`/`float(` sobre string de dinheiro fora dele.

### Família F: data e fuso

- **Ocorrências**: ~12 (06ed546 filtro em UTC, c2a2bcf, db5b77c "folga de encerramento datava em amanhã", da95c75 "data é do evento: stake descontado duas vezes", b779d9a, 645f964, a0a560a "Caixa usa o hoje de Brasília", 6029b63 "desfaz edição em massa de data, 2.252 apostas"). Última: 14/11.
- **Mecanismo**: `bilhetes.data` mistura `DD/MM/YYYY` e ISO na mesma coluna e é a data do EVENTO, mas várias contas a usam como data da aposta; "hoje" calculado em fusos diferentes em lugares diferentes.
- **Correção estrutural**: duas colunas tipadas (`colocada_em timestamptz`, `evento_em timestamptz`), migração única, e "hoje" vindo de uma função só (America/Sao_Paulo).

### Família E: a casa mudou a API/domínio/rota

- **Ocorrências**: ~34 (concentradas em julho na construção dos robôs). Recentes: 464d5c4 (Thunderpick rota nova, 17/11), ea9de0e (Betfury .io, 17/11), eb980cf (Polymarket API v1 aposentada, 410), c2b4c1f (BCB passou a recusar `$select`), 28cdc4b, cf0e3b8, a58b362 (domínios novos).
- **Mecanismo**: externo e inevitável; o problema estrutural é que só se descobre quando um usuário reclama. Com 57 casas em `_MODO_POR_CASA`, a probabilidade de alguma ter mudado numa semana qualquer é alta.
- **Correção estrutural**: canário por casa (última captura bem-sucedida por casa e por versão; alerta quando uma casa com usuários ativos fica N dias sem capturar ou com 0 liquidações), e o domínio aceito por padrão de plataforma, não por lista fechada.

### Família P: processo (sessões paralelas no mesmo working tree)

- **Ocorrências**: 9 incidentes no histórico (13/09 a 11/11) em que um commit levou arquivo/trecho de outra sessão; 1 regressão real provada pelo blame (9d5a66c apagou 95 de 98 linhas de e2427d4 no mesmo dia; restaurado por 2b3360a); 2 deploys quebrados (ca32978, d779315). O working tree de hoje tem `app/casa_chave.py` modificado sem commit.
- **Por que não fechou**: a regra criada foi "add por nome e conferir `git show --stat`", ou seja, disciplina; o index continua compartilhado.
- **Correção estrutural**: uma worktree/branch por sessão e merge pela main com CI verde; nunca duas sessões no mesmo diretório.

### Famílias K (Caixa/custo/filtro, ~49) e U/I

K é a família de "cada tela tem seu escopo de filtro" (76f8f44, ef232db, 570bd89, 91f95fa, 9471516...) e do saldo derivado da Caixa (`_caixa_projetar` tocado por 4 fixes; 2d4139b em 14/11: aposta já liquidada na ativação somava P/L de novo). U e I estão em queda e não explicam a piora recente.

---

## 5. Cobertura dos fixes

| mês | fixes c/ código | com teste/harness no mesmo commit | só teste de CASO (fixture/casa/sessão) | algum teste genérico | trazem script de reparo de dado |
|---|---|---|---|---|---|
| 06 | 81 | 0 (0%) | 0 | 0 | 1 |
| 07 | 144 | 31 (22%) | 12 | 19 | 3 |
| 08 | 50 | 17 (34%) | 6 | 11 | 5 |
| 09 | 84 | 53 (63%) | 18 | 35 | 12 |
| 10 | 43 | 34 (79%) | 14 | 20 | 6 |
| 11 | 22 | 21 (95%) | 7 | 14 | 4 |

Scripts de reparo (corrigir/reparar/liquidar/recalcular...) adicionados: jul 5, ago 5, set 13, out 6, nov 7 (mês parcial).

Leitura:
- A disciplina de teste subiu de 0% para 95%, e a taxa de defeito por feature (§1.3) não se moveu. Os testes travam o caso consertado; não impedem a próxima instância da família.
- Na família L, 100% dos testes são fixture da própria casa (`harness/casos/<casa>.mjs` + `fixtures/<casa>.<caso>.json`, ex.: 27fe6a3, d902a84, 075ee6e). Não existe teste que diga "toda casa trata cashout". A mesma família foi consertada ~24 vezes, cada vez com teste, e reapareceu na casa seguinte.
- Na família B, os testes (`test_barreira_recaptura.py`, `test_virada.py`, `test_repository_db.py`) cobrem o cenário do incidente (apagar e recapturar, leitura não salva), adicionados um por fix; 5 fixes na mesma família em 30 dias mostram que a combinação seguinte não está coberta.
- Na família C não há gate algum para bump de `?v=` (20% dos commits de asset sem bump).
- Fixes de família sem fechar a família (estimativa): L ~24, B ~14, C ~19, D ~40, N ~41, F ~12.

---

## 6. Regras especiais por casa, por usuário e por exceção

| data | flags de ambiente (`os.environ`/`getenv` distintos) | `casa === 'literal'` no JS (front+ext) | `_resultado*` na extensão | adaptadores no servidor | `*_inject.js` | literais de dono no Python |
|---|---|---|---|---|---|---|
| 30/06 | 4 | 4 | 0 | 0 | 0 | 0 |
| 31/07 | 17 | 25 | 4 | 0 | 9 | 3 |
| 31/08 | 25 | 49 | 12 | 0 | 19 | 3 |
| 15/09 | 25 | 57 | 12 | 0 | 20 | 5 |
| 30/09 | 28 | 59 | 12 | 0 | 20 | 5 |
| 15/10 | 33 | 86 | 15 | 7 | 23 | 7 |
| 31/10 | 33 | 98 | 19 | 11 | 27 | 10 |
| 17/11 | 33 | **114** | **24** | **15** | **31** | 11 |

Mais:
- `captura._MODO_POR_CASA` tem 57 entradas; há ainda `_HOSTS_POR_CASA`, `CASAS_COM_FICHA`, `PRINT_LIBERADO = {"GIROCERTO"}` (exceção criada no dia seguinte à regra, 9a70608), `_CASAS_MARCADOR_CODIGO`, a lista `FICHA_CASAS_VIRADAS`/`FICHA_SOMBRA_CASAS` por env, e os mapas de favicon em 4 lugares.
- Uma casa nova toca 11 a 18 arquivos de código (média ~13 em out-nov). A casa CopaWin aparece em 17 arquivos de código, 3 deles scripts de correção de dados.
- Datas cravadas no código: 13 (`virada.D39_DESDE`, 5 em `content.js`, 2 em `pn_inject.js`, 2 em `tv_inject.js`...).
- Exceções por usuário: `_CORTE_HISTORICO` (dono, casa) -> data, scripts nomeados por usuário (`liquidar_won_copawin_gabriel_s453.py`, `corrigir_caixa_copawin_jonathan_s453.py`).

Crescimento: as regras por casa no front/extensão cresceram ~28x em 4,5 meses; o salto mais íngreme é 30/09 -> 17/11 (59 -> 114 comparações, 12 -> 24 tradutores de resultado, 0 -> 15 adaptadores), exatamente a janela em que a sensação de piora aparece.

---

## 7. Diagnóstico sistêmico (só o que os diffs sustentam)

1. **Não há um ponto em que "o código piorou"**: a taxa de defeito por feature é a mesma desde junho (~36% em 30 dias). O que mudou foi o número de lugares onde ela incide: de ~10 casas e 1 caminho de decisão (IA -> UPSERT) para 57 casas, 24 tradutores de resultado, 15 adaptadores, e 3 memórias de "já visto" no meio do caminho. Mesma taxa de erro x muito mais superfície = muito mais erro visível.
2. **O tipo de falha mudou de barulhento para silencioso.** Até agosto o fix típico era de tela/prompt (se vê na hora). Desde setembro, a falha típica é a aposta que fica aberta, segurada ou pulada sem erro (famílias L e B), visível só quando o usuário compara com a casa. Por isso a idade mediana do código consertado em novembro é 25 dias.
3. **Regras são escritas por instância, não por mecanismo.** Toda cadeia longa é a mesma regra descoberta casa a casa, tipo a tipo, modo a modo (incluindo o pós-processamento duplicado em `_stream_sequential`/`_stream_parallel`). Os testes acompanham essa forma (fixture por casa) e por isso sobem para 95% sem baixar a recorrência.
4. **Os "problemas de cache" são três caches diferentes, todos sem invalidação por construção**: o navegador (bump manual de `?v=`, 20% esquecido, versões divergentes do mesmo CSS), o front (estado global sem repinte quando o dado chega depois) e o servidor/extensão (`bloco_visto`, `cruEnviado`, pré-dedup), que decide pular ou segurar com base no que viu e não no que o banco tem. Este terceiro é o que gera "aposta presa" e "aposta que não volta".
5. **Usuário que volta depois de meses bate em vários problemas de uma vez** porque acumula todas as instâncias: extensão com versão velha (o servidor só avisa), tradutores velhos sem os casos acrescentados depois, memória "já visto" de meses atrás, travas novas (Ficha recusa print, conta arquivada exige confirmação, captura de outra conta recusada) que o fluxo antigo dele não conhece, e grafias de casa que mudaram.
6. **Processo**: sessões paralelas no mesmo working tree já produziram pelo menos uma regressão silenciosa provada pelo blame e dois deploys quebrados.

Correções estruturais, por ordem de alavanca:
1. Resultado decidido UMA vez, no servidor, pelo dinheiro; adaptadores só extraem fatos; teste de contrato com os mesmos cenários para todas as casas.
2. "Já visto" vira otimização, nunca decisão: pular só quando o banco confirma o mesmo estado; teste de propriedade para sequências de captura/apagar/reliquidar/falha de /salvar.
3. Versão de asset gerada no deploy (hash), versão mínima da extensão aplicada no servidor.
4. Casa como id; assinatura sobre ids imutáveis.
5. Um parser de número e uma função de "hoje" por linguagem, com lint.
6. Unificar `_stream_sequential` e `_stream_parallel` no pós-processamento.
7. Uma worktree por sessão.
8. Canário por casa (sem captura/sem liquidação há N dias com usuários ativos).
