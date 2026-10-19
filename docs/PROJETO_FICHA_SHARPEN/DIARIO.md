# DIÁRIO · Projeto Ficha Sharpen

> Uma entrada por dia ou por etapa, a mais nova no topo. Todo número com prova. A última entrada diz onde o
> projeto está e qual é a próxima ação.

---

## 2026-10-19 · s423 · Parte B: as cópias com dado pessoal apagadas

`scripts/apagar_copias_filtro_s423.py --aplicar` (decisão do Feca de 12/10, BACKLOG §1). Antes: `captura_crua_copia_filtro` 192, `ficha_sombra_copia_filtro` 55; as 6.841 linhas da `captura_crua` com 0 a cortar pelo filtro de hoje (`limpar_cru_filtro.plano`) e 0 com hash diferente de `cru.impressao`. `DROP TABLE` nas duas, numa transação. Depois (consulta só leitura, `to_regclass`): as duas não existem; `captura_crua` 6.841 e `ficha_sombra` 6.124, intactas.

## 2026-10-19 · s423 · Parte A, passo 1: nenhuma aposta é descartada em silêncio

**Pedido do Feca (pós-parecer 021).** Ensaio da Parte A aprovado; ordem: (1) a aposta que some sem
erro, (2) rastro da Ficha em `correcoes` (A3), (3) as 8 odds vazias ficam como estão, (4) D30 no
diário e lixeira no BACKLOG.

**O caso.** Jaao26, Shuffle, 14/10 07:26:52: 43 crus (apostas de 29/09 a 13/10). A Ficha resolveu 25 e
mandou 18 à IA; o texto da captura trazia 9 códigos (`virada_log` 49: capturadas 9). Os 25 e os 2 que a
IA leu foram gravados (ids 382997 a 383023) e **o usuário os apagou um a um** pela grade entre 07:27 e
07:28 (`DELETE /bilhetes/{id}` no log do Railway, deploy `53567226`); às 07:28 lançou 7 por print, sem
código. Os outros **16 nunca chegaram à IA**: perda do sistema, sem erro. Não regravados (decisão do
Feca: ele refez o histórico à mão e parte é de setembro, D10).

**Conserto.** `ficha_virada.pendente_desde` + `virada._pendentes`, chamado no `/extrair` da casa
virada: tenta de novo os pendentes pela Ficha (cru guardado mais recente, conta do cru), marca o `ia`
decidido DEPOIS do último `/extrair` que o texto não trouxe e sem linha no banco (na mesma casa), e
solta o que virou Ficha, veio no texto ou ganhou linha. Tela: `GET /ficha/nao_lidas` e o card soma
`⚠️ N aposta(s) não lida(s) nesta casa, capture de novo`. O furo do A1 no leitor (e36745b): o bloco que
manda deixar a odd VAZIA passa (`conferir_linha(odd_vazia=)`); a passada final (`_leitor(final=True)`)
nunca derruba por odd; W/HW sem odd grava aberta e avisa o admin (`disparar_aviso`); linha recusada
na passada final volta como faltante da cobertura.

**Casos parecidos desde 12/10** (`ficha_virada` `ia` sem bilhete do dono; a tabela guarda só a última
decisão, então é piso): Shuffle/Jaao26 16 (+2 que a IA leu e o usuário apagou); MyStake/LavaPessoal 1
(307046481, 18/10, cru sem texto). A 1win 338677290 do Jaao26 **não é perda**: a rota do cru a gravou
em 14/10 06:41 (id 382913), o usuário pôs tipster às 06:44 e a apagou às 06:46; em 16/10 12:38 a conta
`Old` recebeu 116 linhas, 47 com gêmea na conta `1win`, e o usuário apagou os 48 ids 386190-386237,
ela inclusive (log do deploy `777c160d`).

**Achado sem conserto.** `virada._liquidados` filtra só dono e código (BACKLOG §4.18).

**Gates.** `tests/test_aposta_nao_some_s423.py` (bloco real da SapphireBet 88092600919) e 4 testes de
banco com 3 crus reais da Shuffle de 14/10 (`tests/ficha_crus_shuffle_s423.json`). Mutações: N1 a N5 e
M1 a M5, 11 detectadas e 1 inócua registrada (N5.1, mascarada pelo `_liquidados`). Suíte pura: 1943
verdes e 1 vermelha (`test_auth::fail_closed`), que falha igual na main limpa (worktree temporária,
`2939590`); banco 77 verdes. Tela aberta no demo, headless: sem erro de script, aviso no card.

## 2026-10-14 (tarde) · s417 · moeda do cru (D30), D31 e o leitor por tipo (parecer 020)

**D30 (moeda).** O vigia achou: LavaPessoal na Megapari, cru `CurrencyCode: BRL`, banco com stake
377,98 em USDT (75 × 5,0397). A conversão usava só a moeda da conta, e a do cru só avisava. Agora a
moeda do cru (`captura_crua`, pelo adaptador) vence: a linha vai na moeda do cru, com alerta e linha
em `alerta_moeda`; a da conta vale só com a moeda ausente (5A). Real numa conta em dólar grava a
origem explícita (`BRL`, ×1). Levantamento (`scratchpad/moeda_lev.py`): só esse caso, 52 apostas
(27 IA, 25 Ficha), todas de 14/10; a conta já estava em BRL quando olhei. Regravadas depois do
deploy: soma R$ 21.733,51 → R$ 4.320,00 (ex.: 88715070881, L, 501,63 → 100,00), rastro em
`correcoes` (`origem='d30'`, 156 linhas). Sem cru: nenhuma. Vigia: as duas pontas na moeda da
casa; das 21 linhas de `vigia_ficha` até hoje, as de stake em conta USD/USDT eram falso alarme.

**D31.** 32 correções do Feca no dicionário (`scratchpad/s417_d31.py`); 4 apostas da Ficha do mês
regravadas (BetMartini 3, Vavada 1). Incluí `empate devolve aposta` (Vavada, Betrebels) como gêmeo
do `empate anula`: a categoria dela na Vavada era ML. `canceled` da BetBy com retorno = stake é V.

**Parecer 020 (leitor).** Na `sombra_tsv` (992 linhas da IA): 126 tinham o Tipster pulado (Shuffle,
MyStake, Duel, BetMartini) e eram lidas deslocadas; as de 10 campos o `validar_linhas` recusava em
silêncio e a captura seguinte recuperava. O leitor novo as realinha; 18 recusadas, todas erradas
(outra casa no campo, "A conferir" no resultado, linha entre crases). As 2 da BetMartini regravadas
pelo cru. Mutação de colunas (tirar uma, somar outra em todas as posições, 770 linhas) achou 5
furos antes do commit (Esporte, casa no Tipster/Parceiro, categoria na Descrição).

## 2026-10-14 (madrugada) · s416 · D27, D29, vigia ligado, R32 e a 1win virada

**D27 (mercados de jogador).** 24 correções do Feca gravadas (`origem='feca'`) pelo
`dicionario.corrigir_termo`: `Ressaltos`/`Rebounds`/`Rebotes` = `{jogador} - {ou} Rebotes`, as
assistências = `Assistências`, PRA da Bet Panda = `Pontos + Assistências + Rebotes`, nas chaves
`{jogador}` da DEX, Bet Panda e Megapari e no `{ent}` da BetMartini e da Vavada (hóquei), com a
categoria `Player Props`; os gêmeos da DEX: `o empate anula a aposta` (futebol e handebol) =
`DNB {ent}` e categoria DNB, `vencedor. quarto {n}` = ML com a forma do Feca (`Time X - NQ`).
Nenhuma aposta da Ficha a regravar (essas tinham ido à IA). O estilo (`descricao_ficha.estilo`)
também junta os nomes. Achados no levantamento: `Time de Fora total de escanteios` (MyStake) era
lido como jogador desde a s415 (o lado do jogo saiu de `_jogador`), e na Megapari o jogador vem
depois do subjogo (`players' stats {jogador} total assists {n}`). Combinações não decididas,
para o consultor: nenhuma nos crus das casas da Ficha; nas descrições que a IA escreveu nas
outras casas, `Rebotes + Assistências` (Betano 42, Bet365 26, Betfair 8, Superbet 2, Stake 2) e
`Pontos + Rebotes` (Betano 13, Bet365 10, Betfair 6, Pinnacle 1).

**D29 (contradição de descrição por regra).** A descrição não usa mais os 90% e nunca fica
contradita: a. total puro → `{ou}`; b. só entre formas do mesmo esqueleto (troca de palavra),
fica a com menos palavras fora do Master; c. a que escreve o mercado vence a do time sozinho
(palavra de verdade: `VFL` não é mercado); d. estilo é um voto (minuto vira `{n}min`, `Ressaltos`,
`PRA`); e. a mais votada, para a revisão (empate exato marcado). A 1ª versão da regra b comparava
formas inteiras e deixava `{time} {ou} Gols` (1 voto, sem o minuto) derrubar 63 votos com o
minuto: achado na medição, corrigido, com teste e mutação. Sobre as 46 da semente_log 17 (votos
daquela rodada): a 6, c 8, estilo 4, e 28 (7 empates) → 28 na revisão; nas 55 chaves de hoje que
vieram delas, 32 decididas, 21 na revisão, 2 sem voto. Semente de hoje: 658 termos de descrição,
0 contraditos, 36 na revisão (7 empates). Megapari: o conserto do `Individual Total 1/2` e do
handicap (s415) já resolvia 9 das 21 com `{t1}`/`{t2}` ou `{n1}`/`{n2}`; as outras o D29 decide.
`medicoes/medir_d29_contradicoes.py`. Cobertura na captura de 13/10 (virada_log 14 a 29, 95
códigos ainda identificáveis; as capturas seguintes regravam o `ficha_virada`): pela Ficha 55 →
65 (DEX 6→8, Duel 9→10, Megapari 1→7, Vavada 3→4), `medir_jogador_chave.py --logs 14-29`.

**D28 (vigia).** Uma chamada por casa virada por dia, de qualquer dono, com até 3 apostas
(`VIGIA_POR_DIA=3`), reserva em memória contra duas capturas juntas. Ligado em 14/10, por 2
semanas: rever em 27/10.

**R32.** O cru vale para a captura se chegou depois do último `/extrair` da mesma casa e dono
(`virada_log`), não mais na janela de 30 s. Duel do Feca, 14/10 (log 43): os 8 eram falsos (crus
32 s antes). Gabriel, 13/10: logs 25 (5) e 28 (2) eram verdadeiros (crus anteriores ao `/extrair`
passado, às 16:52:08 e 17:16:12).

**1win.** Fiscal acha o retorno em 3 de 3 ganhas (todas as que ela tem) → `EXTRACAO_SEM_PENSAMENTO`.
Backtest: 25 comparadas (10 liquidadas), nenhum dinheiro divergente, 25/25 traduzidas iguais à IA;
descrição: 2 defeitos achados e corrigidos (handicap positivo sem sinal, `FC Slavia Mozyr 1.5`; o
total puro com o jogo em ` - `), e então 20 de 25 descritas, 16 iguais, as 4 diferenças explicadas
(2 pela regra do total puro do Feca, 1 de estilo do nome de dupla, 1 em que a IA omitiu `Games`).
Virada.

**Conferências.** DEX do Gabriel 16:53 (log 25): as 5 estão L hoje; a quinta é `12ca7bb3` (Sabah
U19 + Chou Tien Chen, 120,53), a única criada naquela captura (16:53:36), editada (tipster) às
17:01:10. Bet Panda 14/10 04:19: cru com status `canceled` (devolveu os 60 USDT), que o adaptador
`jb` não mapeia; a IA leu e gravou V.

Commit `5b8fdef`, deploy `3085492d (codigo) e 7a26b9fc (variaveis)`.

## 2026-10-13 (tarde) · s415 · o jogador fora da chave, o vigia e o N3 de verdade

**T1.** A DEX escreve o jogador dentro do mercado (`Alec Peters. Ressaltos. Com prorrogação`) e a
chave de descrição era uma por jogador. Agora o nome do começo do mercado vira `{jogador}` quando a
IA escreveu esse mesmo nome. Medido na captura das 15h54 a 16h01 UTC (virada_log 14 a 21), com o
dicionário que existia antes dela: 59 de 154 códigos pela Ficha antes, 65 depois. O ganho veio da
Bet Panda (o jogador antes de um `total` minúsculo) e da Megapari, não da DEX: as chaves fundidas da
DEX ficaram **contraditas**, porque a própria IA escreve `Ressaltos` 14 vezes, `Rebotes` 5 e
`Rebounds` 4 para o mesmo mercado. Decididas (o Master escreve `Rebotes`), a DEX iria de 6 para 18.
Por isso o voto vale também na chave do próprio jogador: com a de qualquer um contradita, quem já
foi visto não piora. A ordem importa: a de qualquer jogador vem primeiro, senão o voto isolado de um
jogador (o que a maioria de 90% venceu) continuaria valendo para ele.

**Lado da 1xBet.** `Handicap 1 (-1.5)` e `Handicap 2 (1.5)` viram `handicap {hc}`; a Megapari
escreve `Handiсap` com o `с` cirílico em algumas linhas. A lista de contradições mostrou mais um:
`Individual Total 2` não era lido como time, e a IA votava `{t1}` contra `{t2}` na mesma chave.

**Vigia.** A amostra da IA não pode ir no lote da extração: o lote volta para a extensão, que o grava
pelo `/salvar`, e a IA escreveria por cima da Ficha. Vai numa chamada à parte, em segundo plano. O
teste de banco achou o furo do primeiro desenho: a aposta que a Ficha liquida pela rota do cru já
chega ao `/extrair` como resolvida, então quem escolhe a amostra é o banco (`origem = 'ficha'`, ainda
não conferida naquele resultado), não o que a Ficha resolveu no `/extrair`.

**N3 de verdade.** Às 16h53 e 17h18 UTC o Gabriel capturou DEX e Duel com aposta que mudou e sem cru
novo: `sem_cru_novo` 5 e 2, a IA leu os 7, e as 5 da DEX estão no banco como L resolvida. Recarregar a
extensão não provoca o caso porque cada captura reinjeta o `content.js` e o inject.

## 2026-10-13 (madrugada) · dicionário de descrição · o mercado aprendido uma vez

**Onde está:** commit `a24bcb6`, deploy `666dcf1d` (03h11 UTC), semente em produção às 03h23 UTC. **Próxima
ação:** na 1ª captura de casa virada, conferir `virada_log.descricao_fora` e o `semente_log` (a semente roda
logo depois e o mercado deixa de ir à IA); o Feca decide os 5 mercados `1x2` de cartões/escanteios que
aprenderam só o time (BACKLOG §1). Seguem a conferência da etapa 1 e o N3 ao vivo.

**Regra do Feca:** chamada extra à IA só para a descrição, nunca. O mercado é aprendido uma vez, sem lado e
sem linha, e depois nenhuma variação dele vai à IA.

- **Chave** (`app/descricao_ficha.py`): `<esporte da casa> | <mercado normalizado>`. O esporte entrou porque,
  sem ele, 62 mercados se contradiziam (`1st half - total` é `Gols 1º Tempo` no futebol e `Pontos 1ª Metade`
  no basquete). O time do jogo escrito no mercado vira `{time}` (com fronteira de palavra: o time `A` não
  está dentro de `total`, pego pelo teste).
- **Valor:** o nome do mercado tirado da descrição da IA, com marcas na posição de seleção, lado/linha,
  handicap e time; o número do período vira `{n1}` (`Winner. Set 1` e `Set 2` são o mesmo mercado).
- **Voto:** só quando a descrição fecha com o cru (jogo, lado, linha, seleção; número que não veio do cru
  não vota). A IA escreve o mesmo mercado de vários jeitos (`Time - Over` × `Time Over`, `1º Tempo` ×
  `1ª Metade`): é um voto só, guardada a variante mais votada. Mercado do time (ou do lado, `Time de casa
  ...`) sem o time é erro da IA e não vota. Maioria de 90% decide; o isolado vai à revisão (P7).
- **Medido e descartado:** virar `Sobrenome, Nome` como a IA. Ela vira em metade das vezes e na outra não
  (a igualdade com a IA CAIU de 108 para 74 na Bet Panda e de 57 para 36 na Shuffle); fica o nome do cru.
- **Conferido no cru:** "Sérvia -1.5 Cartões" (Ficha) × "+1.5" (IA) na MyStake: o cru tem `hisminus: true`,
  a regra provada na tela (s392) inverte, e o texto que a IA leu era de versão anterior da extensão.
- **Cobertura antes de ligar** (`medicoes/medir_descricao_cobertura.py`, in-sample, 845 apostas com cru):
  descritas Bet Panda 153/168, Shuffle 73/80, Duel 130/149, MyStake 175/212, DEX 44/62, BetMartini 66/97,
  Megapari 13/19, Vavada 37/58. No holdout temporal (aprende nos 70% antigos) a cobertura cai muito (MyStake
  27%, BetMartini 5%): mercado novo continua aparecendo, e é a semente logo depois da IA que o cobre.
- **Produção:** 783 termos de semente (469 de descrição), 38 apostas da Ficha de outubro regravadas, 19
  ainda com o termo da casa. Achado para o Feca: 5 mercados `1x2` de cartões/escanteios/assistências
  aprenderam `{ent}` (a IA escreveu só o time, igual a um ML; a Vavada `Lens Cartões 1x2` virou `Lens`).

**Gates:** `tests/test_descricao_ficha.py` 12 (35 mercados reais), `test_virada` 33, banco 70 (2 novos:
mercado novo vai à IA uma vez e depois não; a semente regrava a descrição do mês e não a do mês passado);
23 mutações, 23 detectadas (M6, M7 e M14b escaparam na 1ª rodada; M6 mirava o ramo errado, M7 era barrada
também por outra regra e ganhou caso próprio, M14b era inócua e a condição saiu). pytest tests 1888.
Na conferência em produção, o `semente_log` mostrava 0 contraditos com 12 de descrição contraditos: o filtro
que esconde o par `mercado | seleção` escondia também a chave de descrição (mesmo separador). Corrigido,
com teste e mutação (M15).

## 2026-10-12 (fim da noite) · etapa 1 · furo N3, motivo de cada ida à IA, dicionário D24/R27

**Onde está:** commit `201ac56`, deploy `ba47530f` (23h20 UTC); as 8 casas seguem viradas. **Próxima ação:**
o Feca captura 2 ou 3 casas viradas; o consultor confere no banco com o `virada_log` (motivos) e o
`medicoes/medir_virada_custo.py`; depois o teste real do N3 (recarregar a extensão SEM F5 na aba da casa).
Etapa 2 (Master: Críquete, Boxe, Defesas, Laterais, Dupla/Tripla, grafias) só com a liberação do Feca.

**A · furo N3 (parecer 012).** A Ficha tirava o código da fila da IA com o cru GUARDADO mesmo quando o texto
tinha mudado: o cru velho (aberto) escondia a liquidação. Agora só tira se o cru é desta captura (janela de
30 s + a espera) ou se o bloco não mudou desde a última leitura; senão a IA lê e o `virada_log` conta à
parte (`sem_cru_novo`). Junto: a Ficha grava o `bloco_visto` do que resolveu (sem ele, a captura seguinte
de texto igual mandaria a aberta de volta à IA) e a linha no código de que a espera supõe um processo só.
Teste de banco escrito antes da correção: falhava (a IA recebia `[]`), passa depois; a mutação que tira a
checagem é pega.

**B · dicionário (D24: o termo entra com 1 voto e o erro se conserta depois).**
- `Total` sem qualificador é regra, não termo (`dicionario.categoria_do_total`): Futebol, Hóquei, Handebol
  = Gols; Basquete, Futebol Americano = Pontos; Tênis até 4,5 Sets, acima Games; Vôlei até 4,5 Sets, acima
  Pontos; outro esporte = IA. Descrição `Over/Under X.X [A v B]`. O `total → Gols` de 1 voto da BetMartini
  saiu na semente seguinte.
- Termos vagos (`VAGOS`, hoje `especiais`) nunca entram e sempre vão à IA; `especiais → Futebol` (`*` e
  7Games) apagado.
- Correções do Feca (`scripts/corrigir_termo.py`, `origem='feca'`, vencem a semente inclusive a da casa):
  `winner. quarter {n}` (DEX) = ML, descrição `Time - 1Q [A v B]`; `fastest lap` e `volta mais rápida` =
  Player Props em todas as casas, descrição `<piloto> volta mais rápida [<prova>]`; `fourth quarter -
  total` = Pontos (o termo real da BetMartini é `fourth quarter - total (incl. overtime)`: gravados os
  dois). 0 apostas da Ficha do mês usavam esses termos (só apostas da IA e pernas de múltipla).
- R27: a semente só aprende valor do Master (`app/taxonomia.py`), ignora aposta editada à mão (o bilhete e
  o voto do texto da mesma aposta), e a Ficha confere o Master antes de gravar (`fora do Master` → IA).
- Semente logo depois de um `/extrair` de casa virada que mandou termo novo à IA (lê a decisão da IA na
  `sombra_rotulos`), além da rodada das 04h; cada rodada vai ao `semente_log` (termos por casa,
  contraditos, novos). 1ª rodada (manual, 23h30 UTC): 329 termos, 1 contraditório, 65 novos.

**Gates:** `tests/test_virada.py` 33 e harness de banco 68; 20 mutações (P a AH), 20 detectadas (AH escapou
na 1ª rodada: o teste não tinha o voto do texto da aposta editada; ganhou). pytest tests 1876 verde.

## 2026-10-12 (noite) · D10 · a aposta sai da IA na origem; D10 corrigido; dicionário diário

**Onde está:** commit `53f4609` no ar; as 8 casas seguem viradas. **Próxima ação:** na 1ª captura depois
do deploy, rodar `medicoes/medir_virada_custo.py` e conferir no banco (`ficha_virada`, `virada_log`,
`origem='ficha'`).

**Pedido do Feca (12/10, noite):**
- **D10 corrigido:** "não mexer no passado é não ir futricar as apostas de mês passado". A 1ª versão
  travava todo código gravado pela IA (`_de_outro_caminho`); agora só a LIQUIDADA no banco fica intocada.
- **A aposta sai da IA enquanto aberta:** a Ficha grava a aberta, o pré-dedup tira todo código resolvido
  pela Ficha, e a liquidação vem pela Ficha. A aberta que a IA gravou antes da virada passa para a Ficha
  pelo cru guardado (a extensão não reenvia cru igual; `extensor/cru.js`, registro de "já enviado").
- **Corrida:** o `/extrair` da casa virada espera o cru (em voo + folga 1,5 s, teto 8 s).
- **Métrica:** `virada_log` por captura + `medir_virada_custo.py` (antes: 7 dias de `uso_tokens` e
  `sombra_rotulos`; depois: `virada_log` + `uso_tokens`). Antes da virada, 7 dias: MyStake 16 capturas
  com IA, 242 lidas, US$ 5,65; DEX 33, 1.087, US$ 20,65; Bet Panda 12, 204, US$ 3,22 (o resto no script).
- **Dicionário diário:** a semente roda no app às 07h UTC (`dicionario.diario`); a linha gravada pela
  própria Ficha não vota.

**Gates:** 26 testes em `tests/test_virada.py` e 63 no harness de banco (aberta sai da IA, aberta da IA
passa para a Ficha, liquidada não é reescrita, cru guardado antes da virada, métrica, semente sem a
linha da Ficha). Mutações G a O, todas detectadas (K travava em vez de falhar: o teste ganhou
`wait_for`). pytest tests 1869 verde.

## 2026-10-12 · D5-D10 · as 8 casas viraram: dicionário, D10 e o critério novo do Feca

**Onde está:** `FICHA_CASAS_VIRADAS=MYSTAKE,DEXSPORT,BETPANDA,DUEL,SHUFFLE,VAVADA,BETMARTINI,MEGAPARI`
(12/10 ~19h40 UTC, deploys `6ec6baf8` só MyStake e `ea08a265` as oito); sombra em 8 casas (Megapari
entrou). **Próxima ação:** conferir no banco a 1ª captura de cada casa virada (aposta nova com
`origem='ficha'`, recusada e D10 pela IA); casas novas quando o cru delas chegar (BACKLOG §1).

**Regras novas do Feca (12/10):** toda casa que pode virar vira na hora; o Gabriel é só usuário e não
é critério; critério = backtest com o cru que já chegou, a casa vira se nenhum dinheiro (stake,
resultado, retorno) divergir sem explicação; caem as 30 liquidadas e as 10 ganhas; o histórico não é
reescrito pela Ficha (D10). Registrado em `03_REGUA_NUMEROS §4`.

**O que entrou (commit `3660701`, CI e deploy `e073bd36`):**
- **Dicionário** (`app/dicionario.py`, tabela `dicionario_termos`, `scripts/semear_dicionario.py`).
  Semente dos pares cru × banco (697 apostas, todas com bilhete) e, para o esporte, do texto da
  `sombra_rotulos` (linha `Esporte:` por perna, desde 03/10). Entra só o unânime; o esporte vale para
  todas as casas (`*`) quando a decisão mais votada é a mesma em cada casa. 318 termos; 1 contradição
  (Betnacional `tênis`: Tênis ×10, Futebol ×1). Dois cuidados medidos: o número fica no termo de
  esporte (a Altenar escreve `sportTypeId 4`; com `{n}` os 8 esportes viraram um termo só, com 8
  decisões) e na seleção (`1`/`2` viravam o mesmo `{n}`).
- **Virada:** esporte e categoria traduzidos; termo sem par e código já gravado por outro caminho (D10)
  ficam com a IA. Descrição `<seleção> <linha> <mercado> [jogo]`. Coluna `sistema` da Altenar pela
  Ficha (`3x Duplas`).
- **`tv` (MyStake) inverte a linha com `hisminus`**, como a extensão faz desde a s392: sem isso a
  descrição gravaria o handicap de sinal trocado (306726935: `h -2.5, hisminus` = +2,5).
- **Backtest** (`medicoes/medir_backtest_virada.py`): zero dinheiro divergente nas 8 casas (tabela em
  `03 §4`). As 3 da DEX que apareceram no meio da tarde são crus que acabaram de chegar, já liquidados,
  com a linha da IA ainda aberta: o script separa como "IA ainda aberta".
- **Ensaio antes de ligar:** as 628 linhas que a virada montaria (8 casas) passam no `validar_linhas`
  real do `/salvar`, 0 recusadas.
- Megapari: 19 crus (`x1`, 0.7.52), nomes de campo varridos (79 caminhos, só aposta e evento),
  ligada na sombra, reprocesso 19 aceitas, backtest 19 comparadas, 0 divergem.

**Gates:** `tests/test_virada.py` 20 testes, 15 mutações novas + 3 antigas reconferidas, todas
detectadas; harness de banco com termo fora do dicionário e D10 (mutações E e F, detectadas no
Postgres local); pytest tests 1863 verde, banco 58 verde.

**Achado:** a IA erra a regra do `Múltiplos` nos dois sentidos (12 apostas na régua); a Ficha segue o
`MASTER_ESPORTES §2`. Histórico fica como está (D10); BACKLOG §1.

## 2026-10-12 · D4-D5 · caminho normal provado, BetMartini na sombra, 6 casas sem pensamento, virada construída desligada, adaptador x1

**Onde está:** sombra em 7 casas; virada no ar e DESLIGADA (`FICHA_CASAS_VIRADAS` vazia). **Próxima ação:**
o Gabriel instalar a 0.7.51 e a régua rodar no dia do cru dele (inclusive Megapari, `x1`); resposta do
Feca à proposta das 10 ganhas; o "pode" de cada virada (candidatas DEX e MyStake).

- **Caminho normal provado (Feca, 16h40 UTC):** 133 crus novos nas 6 casas, 133 Fichas aceitas pela rota.
- **Fiscal nas 8 casas 1xBet/Altenar** (`medicoes/medir_fiscal_acha_retorno.py`, código real do fiscal
  `e8ce01f`, ganhas de outubro, bloco mais recente de cada código): Megapari 36/36 (Gabriel 33, Feca 3),
  SapphireBet 13/13, PariPesa 4/4, BetMartini 26/26, Vavada 10/10, Betrebels 18/20; o retorno achado é o
  dinheiro da linha em todas, e o gate não mudaria nenhuma. As 2 da Betrebels não são falha: o bloco
  mais recente está em aberto e o W veio de correção manual (2 registros em `correcoes` cada). **Entraram
  em `EXTRACAO_SEM_PENSAMENTO`: MEGAPARI, PARIPESA, SAPPHIREBET, BETMARTINI, BETREBELS, VAVADA** (17h36
  UTC, deploy `3b1854f1`). **Ficaram fora:** 1xBit (8 apostas, todas perdidas) e Kikobet (3 ganhas, sem
  bloco na sombra): sem amostra para provar (BACKLOG §1).
- **BetMartini na sombra:** varredura de campos limpa; o `vb` recusava 3 (sistema com pernas do mesmo
  jogo; sistema ganho abaixo da stake): corrigido, IA certa nas três; 97 Fichas aceitas. Régua: 82 batem,
  15 só na odd, 0 divergem. **O R16 é sistema 2 de 3** (odd = média das duplas, 6,02385; 14,25 é a tripla),
  e os outros dois exemplos da Altenar também; o texto da extensão escreve sistema como `Múltipla`
  (BACKLOG). Gate: 4 crus reais, 3 mutações, 3 detectadas.
- **Régua:** coluna de ganhas e só o cru mais recente de cada aposta (o antigo, aberto, dava 17 falsas
  divergências). 3ª rodada: 678 apostas, 0 divergem, 0 recusadas; todas as casas com 30+ liquidadas e
  10+ ganhas, só com o Feca. Tabela em `medicoes/REGUA_ADAPTADORES_s409.md`.
- **Virada do §7, desligada** (`app/virada.py`): a aceita grava pelo `/salvar` (`main.gravar_tsv`,
  `origem='ficha'`); o pré-dedup de sempre a tira do lote da IA quando liquidada; recusada, sem cru e
  aberta vão para a IA. Teste dos 3 bilhetes no Postgres real (instalado local nesta sessão, no
  scratchpad: o harness de banco deixou de ser "só no CI" para mutação), 9 mutações, 9 detectadas, 1
  inócua. Pré-requisito anotado: dicionário (`04 §3`) antes da 1ª virada.
- **Adaptador `x1`** (1xBet e espelhos) das fixtures da bancada: 119 apostas, 118 Fichas, 1 recusa (sistema
  sem `Coef`, vai para a IA); 6 mutações, 6 detectadas. Não ligado.
- `pytest tests` 1831 verde; harness de banco 56 verde.

---

## 2026-10-12 · D4 · régua conta as liquidadas por casa e por dono; cópias com dado pessoal até 19/10

**Onde está:** sombra ligada em 6 casas, 559 Fichas aceitas (conferido pelo Feca). **Próxima ação:**
quando o Feca e o Gabriel instalarem a 0.7.51, conferir a 1ª Ficha de cada casa vinda da captura normal.
Só depois disso: a virada do `03_REGUA_NUMEROS §7`, construída DESLIGADA, com o teste dos 3 bilhetes
(aceito, recusado e sem cru, os três chegando ao banco). Candidatas à 1ª virada: DEX e MyStake. Cada
virada só com o "pode" do Feca.

- **Decisões do Feca (12/10):** arredondar retorno ÷ stake em 10 casas está ok. As cópias
  `captura_crua_copia_filtro` (192, todas com `Player` ou `nickname`) e `ficha_sombra_copia_filtro` (55)
  ficam até **19/10** e então são apagadas, se nada tiver dado errado (BACKLOG §1, STATUS).
- **Liquidadas comparadas (D12)**, no `medir_regua_adaptadores.py`: aposta em que a Ficha e a IA estão
  liquidadas; aberta não conta; Feca e Gabriel separados. Feca: Bet Panda 163, Duel 60, DEX 52, MyStake
  135, Shuffle 63, Vavada 45, nenhuma diverge com dinheiro. Gabriel: 0 (sem cru). Conferido por SELECT
  independente. Todas vêm da varredura de histórico de 12/10. Tabela em `medicoes/REGUA_ADAPTADORES_s409.md`.

---

## 2026-10-12 · D2-D4 · 0.7.51 no ar, adaptadores jb/shf/tv/vb na main, sombra em 6 casas

**Onde está:** `FICHA_SOMBRA_CASAS=DEXSPORT,BETPANDA,DUEL,MYSTAKE,SHUFFLE,VAVADA` (deploy `a74bb4ad`,
12/10 ~14h19 UTC). Banco: 559 crus nas 6 casas, 559 com Ficha, 0 recusadas, 0 sem. **Próxima ação:**
conferir que o cru NOVO de cada casa ganha Ficha pela rota (nenhum chegou depois das chaves) e, com 30
liquidadas por casa, a virada pela régua (`03_REGUA_NUMEROS.md`).

- **SharpenUp 0.7.51 publicada em silêncio** (Feca): `sharpenup-cru` na main, declarada em
  `sharpenup_sem_nota`, deploy `ac4526ac`, pacote do `/extensao/download` conferido.
- **Rota endurecida:** erro qualquer do adaptador vira recusa gravada; `CRU_CAPTURA_DESLIGADA` responde 503;
  `scripts/reprocessar_ficha_cru.py` monta a Ficha do cru sem nenhuma.
- **Adaptadores `jb` (Bet Panda, Duel), `shf`, `tv` (MyStake) e `vb` (Vavada)**, medidos offline contra a IA:
  [`medicoes/REGUA_ADAPTADORES_s409.md`](medicoes/REGUA_ADAPTADORES_s409.md). 1ª rodada (545): 4 divergiam com
  dinheiro e 2 eram recusadas. Correções do Feca (12/10), todas aplicadas:
  - **sistema ganho = retorno ÷ stake** (`MASTER_RESULTADO §7.1`); o `derivar` usava a média sobre a stake
    inteira, +650,77 USDT em 4 bilhetes. A IA estava certa.
  - **Shuffle: aceite parcial, não venda parcial** (Feca, na tela da casa). A stake é o `amount` aceito; o
    `originalAmount` fica em `stake_pedida`, só informação. A IA estava certa; eu tinha lido errado.
  - **filtro:** `Player` (MyStake, login da conta) e `nickname` (DEX) só no servidor; a lista do servidor
    CONTÉM a da extensão. 192 crus limpos com hash recalculado (`scripts/limpar_cru_filtro.py`), cópia em
    `captura_crua_copia_filtro` (192) e `ficha_sombra_copia_filtro` (55). Hash = impressão do cru nos 559.
  - 2ª rodada (559): 481 batem, 78 só na odd sem dinheiro (Ficha certa ou empate), **0 divergem, 0 recusadas**.
- **Varredura de nomes de campo** antes de ligar as 5 casas (banco de 12/10 ~14h): nenhum campo de pessoa
  além dos dois filtrados. Família nova passa pela mesma varredura.

---

## 2026-10-12 · D2 · teste real do Feca: 545 crus, 545 batem com o banco

O Feca instalou a extensão da branch `sharpenup-cru` e capturou 6 casas de 5 famílias. Conferido no banco
(só leitura), tabela `captura_crua` contra `bilhetes`, mesma conta:

| Casa | Família | Cru | Batem |
|---|---|---|---|
| Betpanda | jb | 167 | 167 |
| MyStake | tv | 137 | 137 |
| Shuffle | shf | 72 | 72 |
| Duel | jb | 65 | 65 |
| DEX Sport | dx | 55 | 55 |
| Vavada | vb | 49 | 49 |

O filtro removeu 0 campos nessas casas. O texto e a extração saíram como sempre. Condição (c) cumprida.

**Shuffle e Duel na 1ª vez:** o texto chegou e o cru não. A aba estava aberta antes da troca da extensão, e o
Chrome não injeta o content script novo em aba já aberta. Com F5, o cru chegou. Não é defeito; o aviso aos
testers pede o F5.

**Próxima ação:** com o "pode mandar" do Feca, merge na main + bump 0.7.51 + aviso
(`scripts/avisar_testers.py`) + push. Mensagem pronta no STATUS.

---

## 2026-10-12 · D1-D2 · atualização única do SharpenUp (as 22 casas mandam o cru), esperando o teste do Feca

**Onde está:** pronta e provada na branch `sharpenup-cru` (commit `e919499`, **sem push**), na cópia isolada
`../Planilhador-sharpenup-cru`. A `main` e o link dos testers seguem na 0.7.50 de hoje: o
`/extensao/download` empacota a pasta `extensor/` da `main` na hora, então qualquer push dela publicaria
a versão nova antes do teste. **Próxima ação: o Feca instala e testa 2 ou 3 casas reais (condição c).**

- **Pacote atual guardado** para voltar: `Backups/sharpenup_0.7.50_antes_do_cru/` (pasta e zip).
- **Pacote de teste:** `Backups/sharpenup_cru_teste_feca/sharpenup-0.7.50-cru.zip` (a versão segue 0.7.50;
  o bump vai junto com o aviso aos testers, porque o gate do changelog exige as duas coisas no mesmo ato).
- **O que mudou:** cada um dos 22 injects guarda o objeto da casa ao lado do bilhete e manda num campo
  NOVO `cru` da mesma mensagem (lista de sempre intacta); 7 casas já mandavam o objeto da casa (Betano,
  Superbet, Betfair, Altenar, SportingBet, Lottu, `bn`); Betnacional manda as pernas cruas; Pitaco, os
  bytes do protobuf em base64; Bet365, o par summary + confirmation. O `content.js` junta e, DEPOIS do
  texto e sem esperar, pede o envio; `extensor/cru.js` (no background) filtra por nome exato, só marca no
  200, trata o 409 como final e poda o registro (60 dias, 20 mil entradas).
- **(a) Diferença zero:** fotografia do harness (toda mensagem dos injects sem o `cru` + toda saída dos
  formatadores), 2.231 registros em 44 casos, antes × depois: **diferença zero**. Única variação tolerada:
  o cronômetro `"ms"` das mensagens do resolvedor da Bet365, que varia entre duas rodadas do mesmo código.
- **(b) Cru quebrado, texto igual:** `extensor/harness/cru_mutacao.mjs` (no CI da branch) roda o harness
  normal e o quebrado (cada ponto do cru lança erro, 6 alvos, todos casaram): texto idêntico. Prova das
  proteções: tirar o `try` do `_marcarCru`, tirar o do `_crus` e tirar o `cru` da DEX, **3 de 3
  detectadas**.
- **(d) Registro com limite:** caso `cru_envio` (20 conferências; 200/409/401/500/rede, lotes de 200, poda
  por idade e por teto, filtro, ordem texto→cru): **6 mutações, 6 detectadas**.
- **Cobertura medida:** em 33 de 44 casos todo código do texto tem cru e todo cru tem código no texto; as
  exceções são objetos montados pelo próprio teste (Esportiva anuladas/cashout, sintéticos da Bet365 e da
  Betnacional), sem passar pelo inject. Trava permanente: casa que imprime código e não manda cru derruba
  o harness.
- **Gates na branch:** harness 45 casos verde em Brasília e em UTC; `audit_sharpenup` sem FAIL; `pytest
  tests` 1.787 verde; teste novo trava a lista do filtro da extensão igual à do servidor.
- **Virada (pedido do Feca):** desenho de "recusada volta ao caminho de hoje" em `03_REGUA_NUMEROS.md §7`.

---

## 2026-10-11 · D1 · o cru vai ao servidor; filtro por nome exato; adaptador da DEX; CI verde

**Onde está:** servidor pronto para receber o cru (tabela, filtro, adaptador da DEX), testado. A
extensão ainda NÃO manda o cru. Próxima ação: a atualização única do SharpenUp (as 22 casas
mandando o cru), que será mostrada ao Feca antes de distribuir.

**Rumo do Feca:** primeiro as casas de outubro rodando perfeito; depois Bet365, Betano e as demais,
até virar a chave de vez. **Mudança de desenho:** os adaptadores saem da extensão e vão para o
servidor (Python, um por família); a extensão manda o cru de **todas** as casas que já escuta, numa
atualização só. Cru guardado de todas as casas desde o 1º dia (aprovado).

- **CI (item 5):** o resolvedor de abertas da Bet365 falha só em UTC (`TZ=UTC node
  extensor/harness/run.mjs bet365` reproduz); vermelho desde a s407, travava 3 passos. Isolado como
  falha CONHECIDA no `extensor/harness/run.mjs` (só as do caso Bet365 com prefixo `resolver`; outra
  falha, até da Bet365, derruba, provado por mutação). `BACKLOG.md §4.16`. **CI verde** em `0f09b63`,
  todos os passos.
- **Filtro** (`app/cru.py`), refeito como o Feca mandou: **nome exato**, igualdade sem caixa, lista
  fechada; e-mail pelo valor. Lista: a de partida da consultoria + `CurrentBalanceDetails`,
  `CustomerId`, `CustomerCode`, `playerId` (identificam o cliente; nenhum inject usa; o `playerId`
  da Novibet é número real de cliente). Varredura das 61 fixtures: a lista pega o que a
  consultoria achou em 12 fixtures, e e-mail pelo valor em 3 pontos da Lottu.
- **Tabela `captura_crua`** (`app/database.py`): cru filtrado em JSONB, caminhos removidos, hash
  recalculado no servidor; cru igual não grava de novo. `ficha_sombra.cru_id` aponta a origem.
- **Rota** (`app/ficha.py`): recebe `{token, versao, origem, familia, itens:[{codigo, hash, cru}]}`
  (até 200); filtra de novo; guarda o cru de toda casa; com `FICHA_SOMBRA_CASAS` ligando a casa,
  monta a Ficha pelo adaptador e grava aceita ou recusada com motivo. Cru do site de outra casa:
  **409 final**, não grava, conta no log. `CRU_CAPTURA_DESLIGADA=1` desliga tudo.
- **Adaptador DEX** (`app/adaptadores/dx.py`): bate com o **gabarito lido na tela** (10 bilhetes do
  recon de 03/10: odd, resultado, stake e data, incluindo perna anulada e perdida com perna
  aberta) e monta os 41 da fixture sem recusa. O que hoje sobe "a conferir" é **recusado com
  motivo**. A `impressao` é calculada pelo servidor sobre o cru guardado, não pelo adaptador.
- **Teste obrigatório do Feca:** Ficha do cru filtrado = Ficha do cru sem filtro, em toda fixture
  com adaptador; adaptador novo sem fixture registrada quebra o teste.
- **Gate:** `tests/test_cru.py` (15) e `tests/test_ficha.py` (rota refeita); **11 mutações, 11
  detectadas** (a da odd da ganha escapou na 1ª rodada: o `derivar` chega a 3,75 pelo dinheiro, então
  o teste passou a conferir o campo da Ficha). INSERT do cru no harness de DB. `pytest tests`:
  **1.786 passed**.
- **Régua (item 4):** moeda e código bloqueiam; contar ganhas em "nenhuma fecha"
  (`03_REGUA_NUMEROS.md §6`).

---

## 2026-10-11 · D1 · rota da Ficha em modo sombra (no ar, desligada)

**Onde está:** rota pronta, testada e publicada com a chave **vazia** (`FICHA_SOMBRA_CASAS`), então
nada é gravado ainda. Próxima ação: o adaptador da DEX na extensão (envio separado do
`/captura/enviar`, sem esperar resposta), que precisa de aprovação.

**Aprovado pelo Feca com 3 ajustes:** (a) recusada gravada com o motivo; (b) dizer antes de onde saem
casa e conta; (c) no adaptador, envio separado e sem esperar. Fica para depois, com asterisco no
`BACKLOG.md §3.21`: Lottu e a folga de 0,5% / Novibet 1,001.

- **(b) Casa e conta** saem da **sessão de captura** (`app/captura.py`, `Sessao`): o
  `POST /captura/parear` grava dono logado + casa + conta escolhidas no dashboard, e o token da
  extensão aponta para essa sessão. Ficha com outra casa é recusada (motivo gravado); conta vazia
  grava `parceiro = ''`; token inválido responde 401 e não grava (sem dono, gravar seria abrir o
  banco para requisição anônima).
- **Código:** `app/ficha.py` (rota `POST /captura/ficha`, `validar`, `derivar`, `gravar`); tabela
  `ficha_sombra` no `app/database.py` (aceita dedupa por dono+casa+conta+código+impressão;
  recusada por hash do conteúdo); no `app/main.py` só o registro (`include_router` + a isenção de
  CSRF em `_CAPTURA_ISENTAS`).
- **`derivar`** segue a regra da odd aprovada e a data do MASTER_OUTPUT §4/§4.0.1 em Brasília. Roda
  na hora do relatório, não na gravação.
- **Gate:** `tests/test_ficha.py`, 28 testes com valores reais da DEX; **11 mutações, 11
  detectadas**, 1 inócua registrada (a trava "nunca anda para frente" da perna perdida, que a
  aritmética já garante). Uma mutação escapou na 1ª rodada por defeito do teste (HW e W davam a
  mesma resposta no caso montado). Um erro de digitação no teste (`meia_ganha`) mostrou que
  `derivar` tratava status desconhecido como cashout: agora levanta erro. O INSERT real ganhou
  teste em `tests/test_repository_db.py` (só roda no CI). `pytest tests`: **1.767 passed**.

---

## 2026-10-11 · D1 · fiscal lê `Retorno:` + aquecedor nas duas versões (um deploy)

**Onde está:** fiscal e aquecedor no código, testados; vão num commit e num deploy só. Próxima ação: a
rota da Ficha em modo sombra. As 8 casas seguem **fora** da chave até o Feca decidir a volta.

**Respostas do Feca:** 8 casas fora (feito 21:59); medir o fiscal nas 7 que ficam; fiscal lendo
`Retorno:` aprovado, com mutação obrigatória da aberta com `Retorno potencial:`; aquecedor nas duas
aprovado; desenho da odd aprovado com 3 complementos (Ficha §3 e `03_REGUA_NUMEROS.md §3`). Vale daqui
para frente, nada retroativo.

- **As 7 que ficam na chave:** o fiscal acha o retorno em **213 de 213** apostas ganhas de outubro
  (DEX 64/64, MyStake 20/20, Shuffle 27/27, Duel 30/30, Betpanda 57/57, Betfury 12/12, Betcoin 3/3;
  `Status:` com `→ W`/`→ HW`, último bloco de cada código). Nenhuma sai.
- **Fiscal** (`app/repository.py`, `_RETORNO_LINHA_RE` + 2ª fonte no `_financeiro_do_texto`): lê
  `Retorno:` em coluna zero, só quando o `Status:` não traz o número. `Retorno potencial:` e linha recuada
  não casam. Em 60 dias de `sombra_rotulos`, nenhuma casa escreve `Retorno:` em aposta aberta.
- **Alcance medido antes de publicar** (`medicoes/medir_fiscal_retorno_linha.py`, função antiga × nova
  sobre as apostas gravadas): 1.588 resolvidas com a linha, em 19 casas; **21 mudariam**, nenhuma das 8
  casas do projeto (lá a IA tinha acertado as 135). Fora do projeto: Lottu 6 (odd `7,455` onde a casa
  pagou `4,97`; P/L R$ 1.170 inflado), SportingBet 8, Betboo 2, Esportiva 2, Estrela Bet 2: odd que não
  fechava o retorno. **1 discutível:** Novibet `347813`, W @ 1,001 com retorno R$ 51,05 sobre stake 51
  vira V, porque o fiscal testa V antes de W com folga de R$ 0,10 (regra antiga, agora alcançando a
  Novibet). P/L −R$ 0,05. Resolvida é congelada no banco: nada disso é retroativo.
- **Aquecedor** (`app/main.py`, `_variantes_do_aquecedor`): com a chave não vazia, aquece a versão padrão
  e a sem pensamento do mesmo prefixo.
- **Gate:** 5 testes novos no `test_odd_resultado_determinista.py` (blocos reais Megapari e BetMartini) e
  2 no `test_extracao_sem_pensamento.py`; **6 mutações, 6 detectadas**. `pytest tests`: **1.739 passed**.
- Backup: `Backups/s409b_fiscal_retorno_e_aquecedor/`.

---

## 2026-10-11 · D1 · decisões do Feca, aquecedor, qualidade por casa e regra da odd

**Onde está:** decisões registradas; três propostas esperando o Feca (abaixo). Nada de código novo.

**21:59: as 8 casas sem rede do fiscal saíram da chave** (o Feca rodou o `railway variables --set`).
`EXTRACAO_SEM_PENSAMENTO=DEXSPORT,MYSTAKE,SHUFFLE,DUEL,BETPANDA,BETFURY,BETCOIN`, deploy `88011cb8`
SUCCESS. Entre 21:10 e 21:59 o `uso_tokens` não tem **nenhuma** extração, de casa nenhuma: nenhuma das 8
extraiu sem pensamento.

**Decisões do Feca** (`README.md §3`, itens 8 a 12): Ficha antes da Fase 2 da blueprint (`STATUS.md`
atualizado); só esta sessão mexe em `main.py`/`repository.py` (`docs/ESTRUTURA_DO_TIME.md`); virada só com
30 apostas **liquidadas** comparadas (`03_REGUA_NUMEROS.md §4`); odd: aberta pelas pernas, resolvida por
retorno ÷ stake; as 249 apostas antigas ficam como estão (item fechado).

**1. Aquecedor de cache.** A `SUPERBET` **não** está na chave. Confirmado no código: os 6 manuais gerais
são um prefixo de cache comum a todas as casas (`app/prompts.py`, `build_system`, breakpoint no 6º master),
e o aquecedor (`app/main.py`, `_cache_warmer`) só aquece a versão com pensamento. Proposta: com a chave
não vazia, aquecer **as duas** versões (com pensamento para print, PDF e casas fora da lista; sem, para as
listadas). Custo: uma leitura de cache a mais a cada 55 min. Amanhã: `cache esc.` por extração depois
de 21:10 no `medicoes/medir_qualidade_por_casa.py`.

**2. Qualidade por casa.** `medicoes/medir_qualidade_por_casa.py` pronto (uso_tokens, repescagem pela
`sombra_tsv`, fiscal mexeu pela `sombra_numeros`, liquidadas × abertas). Rodado às 21:4x: **nenhuma
extração depois da chave ainda**. O "antes" da sombra é fino (ela grava desde 11/10 19:57: 1 a 3
extrações por casa).
- **Achado, e ele pesa:** em **1xBet (Megapari, PariPesa, SapphireBet, 1xBit) e Altenar (BetMartini,
  Betrebels, Vavada, Kikobet)** o retorno vem numa linha `Retorno:` própria, e o fiscal só lê o retorno
  dentro do `Status:` (`repository._financeiro_do_texto`, `_RETORNO_TXT_RE` sobre o status). Medido com a
  função real em blocos ganhos de outubro: **0 de 40** Megapari, 0/40 BetMartini, 0/40 Betrebels, 0/40
  Vavada, 0/30 SapphireBet, 0/27 PariPesa. Nessas 8 casas o fiscal da odd **nunca roda**, com ou sem
  pensamento, e o erro que a medição da DEX achou passaria direto.

**3. Regra da odd** (`medicoes/medir_regra_odd.py`; 1.547 apostas de outubro das 15 casas, 1.347
comparáveis; sistema e HL fora; odd gravada × odd pela regra, igualdade exata):
- **Mudariam 527 de 1.347.** Por causa: **499 são só precisão** (diferença < 0,5%: `6,169904` ×
  `6,169904352`, `5,5648` × `5,565`), **28 são diferença grande**. P/L: 33 apostas mudariam ≥ R$ 0,01,
  saldo líquido R$ 0,31.
- **As 28 grandes são casos em que o produto das pernas NÃO é a odd que a casa pagou:** ComboBOOST da
  Betpanda (casa `8,918` = produto `8,494` × 1,05), perna anulada (8), mesmo jogo/Bet Builder (2) e
  múltiplas Altenar em que o produto passa do dobro da odd da casa (BetMartini `6,02` × produto `14,25`;
  Betrebels `3,56` × `6,67`; Vavada `6,69` × `15,79`), causa ainda não explicada.
- **(c) cashout pela regra da aberta quebra o P/L:** o P/L de W é `stake × (odd − 1)`; com a odd das
  pernas, um cashout de R$ 50 numa aposta de odd 4 grava lucro de odd 4. Hoje o `MASTER_RESULTADO §5.6`
  manda retorno ÷ stake.

---

## 2026-10-11 · D1 · etapa 2: pensamento atrás de chave (no código, chave desligada)

**Onde está:** **chave LIGADA** para as 15 casas de outubro em 11/10, 21:10 (o Feca rodou o
`railway variables --set`; o modo auto do Claude Code barra a escrita). Deploy `97387a25` SUCCESS, app no
ar (`www.sharpen.bet` responde, startup limpo no log). Próxima ação: depois de um dia de extrações,
conferir no `uso_tokens` a saída por pedaço nessas casas e os números na régua.

- **Chave:** `EXTRACAO_SEM_PENSAMENTO` = lista de casas ou `*`. Vazia = como sempre. Só lote de **texto**
  (print e PDF seguem pensando: não foram medidos sem). Lida a cada chamada.
- **Onde age** (`app/main.py`, `_pensamento_kw`): todas as chamadas do titular, ou seja, paralelo,
  sequencial e as repescagens de cobertura e de fidelidade. Também no aquecedor de cache, que aquece a
  Superbet: o pensamento entra na chave do cache (medido hoje: a chamada sem pensamento não leu o cache
  escrito com ele), então ele acompanha quando a chave cobre a Superbet. Contrato de 4 campos e sombra:
  intocados.
- Conferido na API real: `max_tokens=0` com `thinking` desligado é aceito (aquecedor).
- **Gate:** `tests/test_extracao_sem_pensamento.py`, 9 testes, **5 mutações, 5 detectadas**. Os dublês
  de `_repescar_faltantes` em `test_cobertura.py` e `test_fidelidade.py` passaram a aceitar o argumento
  novo. `pytest tests`: **1.732 passed**.
- Valor das 15 casas de outubro, conferido contra `casas/CASA_*.md`:
  `DEXSPORT,MEGAPARI,MYSTAKE,SHUFFLE,BETREBELS,DUEL,BETPANDA,BETMARTINI,BETFURY,VAVADA,BETCOIN,PARIPESA,SAPPHIREBET,1XBIT,KIKOBET`

---

## 2026-10-11 · D1 · etapa 1 publicada + quanto do banco caiu no furo

- **Commit `ec50274`, pushado** (fix + teste + STATUS s409, com a s407 indo para o HISTORICO). O commit
  desta pasta foi **barrado pelo filtro de permissão** do Claude Code; fica para o Feca rodar.
- **Medição no banco (só leitura)**, harness `medicoes/medir_furo_folga_odd.py`: para cada aposta W/HW
  com bloco cru na `sombra_rotulos`, a função de antes (backup) × a de agora, com a stake do bloco.
  - 9.436 apostas W/HW com bloco; **249 caíram no furo** (a odd gravada não fecha o retorno e a da casa
    fecha). Todas de agosto (41) e setembro (208); **nenhuma de outubro**.
  - Dinheiro: **R$ 27,94 somando em módulo**, saldo líquido de R$ 0,34; **maior diferença numa aposta:
    R$ 0,80**. Quase tudo é odd com dízima (`1,9505…` onde a casa diz `1,95`), Bet365 à frente
    (Jonathan 81, Feca 65, Gabriel 33).
  - **Ficaram de fora 298** em que a stake do bloco difere da gravada: casa em USDT/USD (o banco guarda em
    real) ou stake editada. As casas cripto do projeto (DEX, Betpanda, Duel, Shuffle) **não foram
    medidas** por isso.
  - Não conferi `correcoes` (edição humana manda). Qualquer reparo precisa pular essas linhas.
  - Primeira rodada saiu inflada (447, R$ 130 mil) por erro meu: usei a stake do banco contra o retorno do
    bloco em USDT. Corrigido antes de reportar.

---

## 2026-10-11 · D1 · etapa 1: furo de 0,005 do fiscal fechado (não commitado)

**Onde está:** código e teste prontos no working tree, **sem commit** (aguarda o Feca). Próxima ação:
commit + push com o "pode" do Feca; depois, a etapa 2 (pensamento desligado atrás de chave).

- **Mudança:** `app/repository.py`, `_veredito_do_retorno`, logo depois da linha 696. Dentro da folga de
  0,005 da odd, em W e HW, a odd da casa substitui a da linha quando **ela fecha o retorno no centavo e a
  da linha não**. Casa que arredonda a odd na tela: a da linha fecha e fica. Nenhuma fecha: nada muda.
  Fora da folga, o comportamento é o de antes.
- Não está atrás de chave por casa: é conserto do fiscal de hoje, vale para todas as casas e todos os
  modelos (decisão desta etapa, aprovada como "fechar o furo").
- **Gate:** 4 testes novos em `tests/test_odd_resultado_determinista.py` (bloco real da DEX); **7
  mutações, 7 detectadas** (lista no cabeçalho do arquivo, itens 13 a 19). `pytest tests`: **1.723
  passed**, 51 skipped.
- **Prova na medição de hoje**, sem chamada nova à API (respostas gravadas da medição, refeitas pelo
  fiscal novo): números A × B **30 de 30 iguais** em stake, odd e resultado (era 29 de 30). O fiscal
  corrigiu 1 linha do B e nenhuma do A.
- Backup: `Backups/s409_fiscal_odd_fecha_no_centavo/`.
- **Não medido:** quantas linhas já gravadas no banco caíram nesse furo. Dá para medir só leitura.

---

## 2026-10-11 · D1 (início) · medição do pensamento do Sonnet 5

**Onde está:** medido; **nada mudou em produção**. Próxima ação: o Feca escolhe o que fazer com o
pensamento (ver "Pendente").

**Pergunta do Feca:** voltar para o Sonnet 4.6 não resolve mais fácil? **Não**, e não foi feito:
- na bancada limpa da s380 (21/09, 300 blocos), o 4.6 **perdeu 6 bilhetes** e o Sonnet 5 nenhum
  (`docs/historico/HISTORICO_s300-s327.md:25`); foi o motivo da troca da s377 (`docs/HISTORICO.md:49`);
- o 4.6 custa mais por token (3/15 contra 2/10 por MTok) e saiu do `ALLOWED_MODELS` (`app/config.py`).

**Medição** (harness: `medicoes/medir_pensamento.py`; 5 lotes × 6 blocos reais da DEX Sport de outubro,
`sombra_rotulos`; caminho de produção; banco só leitura; juiz = `app/sombra_numeros.comparar`):

| | A: como hoje | B: pensamento desligado |
|---|---|---|
| Respostas com bloco de pensamento | 5 de 5 | 0 de 5 |
| Saída por pedaço (média) | **11.407 tok** | **1.545 tok** |
| Custo por pedaço, cache quente | US$ 0,142 (medido) | ~US$ 0,039 (calculado com o cache lido; na medição o cache não foi reaproveitado, ver abaixo) |

- **Confirmado: o excesso é pensamento.** Saída cai 86% sem ele.
- **Números, A × B, 30 apostas:** stake 30/30 iguais, resultado 30/30, **odd 29/30**. A diferente é um
  **erro do B**: bilhete `1d15646f…` (DEX, múltipla ganha, stake 40, retorno 158,80 USDT, odd da casa
  3,97). 158,80 ÷ 40 = **3,97** (A acertou). O B gravou **3,9672**, que é o produto das pernas
  (2,28 × 1,74), e escreveu na nota que era "retorno ÷ stake". Os fiscais (`corrigir_stake_tsv`)
  **não pegaram**: o final saiu igual ao bruto. No P/L seria R$ 118,69 no lugar de R$ 118,80.
- Amostra pequena (30 apostas, 1 casa, 1 rodada): é sinal, não taxa.
- **Custo da medição: ~US$ 2,24**, acima do "menos de US$ 1" que eu prometi. Mudar o pensamento
  invalida o cache do manual, e cada chamada B escreveu o cache de novo (70 mil tokens).

**Por que o fiscal não pegou** (reproduzido com as funções reais, sem IA): `_financeiro_do_texto` leu
certo o bloco (`odd_total 3,97`, `retorno 158,80`), e `_veredito_do_retorno(40, 3,9672, 158,80, …)`
devolveu `('W', None)`: confirmou o W e **não trocou a odd**, porque `app/repository.py:696` só troca
quando a diferença passa de **0,005** (`abs(n_bloco - odd) > 0,005`), pensado para barrar ruído de estilo
(`1,95` × `1,950`). 3,97 − 3,9672 = 0,0028. É um furo do fiscal que vale para **qualquer** modelo e casa,
não só sem pensamento.

**Pendente com o Feca:** desligar o pensamento hoje **troca dinheiro por erro de número** (1 em 30
aqui). Opções na resposta da sessão: manter como está até a Ficha virar a casa, ou medir um meio-termo
(esforço médio) antes.

---

## 2026-10-11 · D0 · Ficha aprovada

**Onde está:** Ficha Sharpen v1 aprovada, nenhum código escrito. **Próxima ação: D1**, começando por
confirmar que os tokens a mais do Sonnet 5 são pensamento, antes de mexer nele.

**Respostas do Feca às 5 perguntas** (detalhe no §9 de `01_FICHA_SHARPEN.md`): 1A, 2A, 3A, 4A, 5A.
- Data: regra do §3 inteira, incluindo "sem início = colocação".
- Termo desconhecido grava na hora; o lote atualiza só Esporte e Aposta.
- Descrição fica com o termo original da casa e nunca é reescrita (pergunta extra do Feca; resposta:
  "a descrição não tem essa importância toda").
- Sem caixa de revisão. Moeda ausente = moeda da conta.

**Medido para responder a pergunta 1** (leitura de código, não de dado): as 6 famílias de outubro
entregam início por perna: DEX `extensor/content.js:4656`, 1xBet `extensor/x1_inject.js:143`
(`StartDate`), BetConstruct `content.js:5257` e `5303`, BetBy `content.js:4515`, Altenar
`content.js:5746` (`eventDate`), Shuffle `content.js:4865`. Pernas sem início nas fixtures não foram
contadas.

**Feito por outras frentes hoje (não por este projeto), conferido no git:**
- Sombra no `claude-haiku-5-5` por padrão: `app/main.py:490`, commit `e2427d4` (s407). A régua de
  números (`app/sombra_numeros.py`, `scripts/relatorio_sombra_numeros.py`) entrou no mesmo commit.
- Barreira de recaptura (porteiro) da DEX Sport e da Shuffle: commit `9d5a66c` (s407/s408).
- Outra sessão segue mexendo em `app/repository.py` e `global/MASTER_OUTPUT_2026.md` (git status de
  11/10, noite).

**Pendente com o Feca:**
- A ordem das casas do `02_CASAS_OUTUBRO.md §2` não foi perguntada explicitamente; segue a do arquivo.
- D1: reduzir o pensamento do Sonnet 5 (depois de confirmar que é pensamento) e a rota sombra da Ficha.

---

## 2026-10-11 · D-1 · Projeto aberto

**Onde está:** desenho pronto, nenhum código escrito. **Próxima ação: D0, aprovar a Ficha** (as 5 perguntas
do §9 de `01_FICHA_SHARPEN.md`).

**O que aconteceu hoje:**
- Mapa independente do Sharpen concluído (Fase 1), com verificação cega: 53 de 55 fatos confirmados na
  fonte. `Auditorias\mapa_2026-10\claude\MAPA.md`.
- Revisão do processo de extração com o Feca, passo a passo, em duas gravações. Página final:
  `referencias/viagem-de-uma-aposta.html`.
- Decisões do Feca registradas no `README.md §3`.
- Medido para este projeto (banco de produção, só leitura):
  - custo por extração: US$ 0,22 no Sonnet 4.6 → US$ 0,45 no Sonnet 5 (`uso_tokens` por modelo);
  - 69% da conta do Sonnet 5 é a IA escrevendo (`uso_tokens` × preço de tabela, bate com o gravado);
  - 73% do manual geral é padrão de esporte, categoria e descrição (`count_tokens` por arquivo);
  - as 15 casas do projeto custaram cerca de US$ 87,5 de 01/10 a 11/10, só Feca e Gabriel
    (`02_CASAS_OUTUBRO.md`).
- Em paralelo, outra frente está construindo a sombra de números Sonnet × Haiku (`app/sombra_numeros.py`,
  `scripts/relatorio_sombra_numeros.py`, ainda não commitados) a partir de
  `referencias/PROMPT_SOMBRA_NUMEROS.md`. Também em paralelo: as correções do porteiro para DEX Sport e
  Shuffle.

**Pendente com o Feca:**
- As 5 perguntas do §9 da Ficha.
- Reduzir ou desligar o "pensamento" do Sonnet 5 no caminho de hoje (D1). Que os 4,6 mil tokens a mais por
  pedaço são pensamento é dedução: confirmar com o uso detalhado de uma resposta real antes de mexer.
- Trocar a sombra para `claude-haiku-5-5` (variável `SOMBRA_MODELO` no Railway).
