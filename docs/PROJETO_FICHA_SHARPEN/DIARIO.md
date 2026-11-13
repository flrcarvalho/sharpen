# DIÁRIO · Projeto Ficha Sharpen

> Uma entrada por dia ou por etapa, a mais nova no topo. Todo número com prova. A última entrada diz onde o
> projeto está e qual é a próxima ação.

---

- **2026-11-13 · s450 · RC45 pela D49:** o `sporttypeid` da Altenar é esporte (34 Tênis de Mesa, 31 Críquete, 23 Futsal, 82 Rugby; fora do `VAGOS`, camada do Feca no código, `dicionario.ESPORTE_D49`); Sportsbet.io passa o slug e Thunderpick o `gameId <n>` em vez de vazio; `tests/test_dicionario_d49.py`, mutações D1 a D7 detectadas. Sem push. A sombra (commit 3 da D50) espera a 1ª linha `caminho='print'`: zero em 13/11.
- **2026-11-11 · s450 · D50:** "nada pode ser gasto sem ser medido"; o `uso_tokens.caminho` passa a marcar `print` e `pdf`, e o aquecedor grava o seu uso (`caminho='aquecedor'`); `tests/test_uso_caminho.py`, mutações U1 a U4 detectadas; no ar em 11/11 23:31. Casa com Ficha (29, fora as `.bet.br`) recusa print e PDF no `/extrair` e na tela (`tests/test_bloqueio_print.py`, mutações B1 a B5 detectadas, headless sem truncar nome); a planilha (.csv/.xls) segue entrando pela caixa nessas casas (`tests/test_planilha_na_ficha.py`, 7 mutações detectadas). Sem push.
- **2026-11-11 · s449 · RC44 e RC46:** depois de esperar o cru, o `/extrair` refaz o "já no banco" com o mesmo filtro de conta e tira do lote da IA o que a rota do cru liquidou na espera (`app/main.py`, `test_rc44_corrida_da_rota_do_cru_com_o_extrair`; mutações R1 e R2 detectadas). **RC46:** o vigia passa a uma chamada por casa por semana, segunda a domingo em Brasília (`virada.semana_brasilia`, `test_vigia_uma_chamada_por_casa_por_semana`; mutações V1, V2 e W9 detectadas). No ar desde 11/11 22:42 (deploy `786759cd`). Depois, o código liquidado só noutra conta ganha o motivo `liquidada em outra conta` (`virada_log.outra_conta`; mutações O1 a O3 detectadas), sem push.

## 2026-11-07 · s438 · D44: bônus na aposta ajusta a odd

**Onde está:** no ar com o "pode" do Feca (07/11). Nenhuma correção aplicada: as duas oferecidas
(5520005256 e 5602432981) o Feca clica depois do deploy. Congelado até 08/11, só conserto de defeito.

- **A regra (Feca, 04/11/2026, substitui o "bônus não é odd" de 02/11):** bônus na aposta (bônus de
  múltipla e afins) ajusta a odd: odd = retorno ÷ stake. No red a stake se perde normalmente; no
  green o bônus entra na odd. Freebet não muda (`MASTER_RESULTADO §5.8`: no red o retorno é zero).
- **Onde a regra mora:** `global/MASTER_RESULTADO_2026.md` §6 (Promoções e Odds Boost), que já dizia
  isso. Sem segunda cópia em CLAUDE.md ou runbook (decisão do Feca: "o MASTER §6 basta").
- **Ficha:** sem mudança; a conta está em `app/ficha.py:211-212` ("nenhuma fecha: retorno ÷ stake").
- **D44:** sai `e_so_bonus` e a contagem `bonus`; a aposta ganha com bônus fora da odd vira
  divergência comum, oferecida com a odd da Ficha. A nota da tela perde a frase do bônus. O piso de
  R$ 1,00 no P/L continua.
- **Prova:** `test_bonus_na_aposta_ajusta_a_odd`; mutações C12 (bônus volta a sair da lista) e C13
  (odd oferecida deixa de ser retorno ÷ stake) detectadas. Dado real, só leitura: Vavada 5520005256
  7,471205 → 7,6 e 5602432981 5,678262 → 5,7718, as duas oferecidas.
- **Dicionário, 8 chaves de "shots towards the goal" (03/11):** Megapari (4), Melbet (2), Vavada
  `total shots` e Sapphirebet `shots on target individual total 2`, por `corrigir_termo.py` com origem
  `feca`, no teste e depois em produção, SELECT antes e depois. 0 apostas de novembro regravadas; as
  12 de outubro ficam como estão.
- **Sportsbet.io, medição só leitura (07/11):** 187 apostas da IA com cru; 8 têm odd ≠ `totalOdds`, e
  nas 8 a odd do banco é a do card (`boostedOdds`). Lucro a mais: R$ 0,52 em outubro, zero em novembro.
  Os erros grandes (411204, 416353 e outras 9) a Ficha já tinha corrigido.

---

## 2026-11-03 · s438 · D44 item 3: origem em todo caminho que grava `correcoes`

**Onde está:** no ar com o "pode" do Feca. **Sem mudança nova até domingo, 08/11, a não ser
conserto de defeito** (Feca, 03/11). Próximo: o relatório da semente das 04h (os 13 termos da
Megapari antes e depois, as apostas de novembro regravadas, se a 412223 entrou, as chaves de
estatística e o texto do aviso).

- **A regra (Feca, 03/11/2026):** "Robô = só ficha, conferir e resolver. Qualquer outra origem, ou
  NULL, é humana." A origem diz de onde veio, não quem manda.
- **Resolver da bet365** (`main._resolver_abertas`): grava `resolver` e entra em `ORIGENS_DE_ROBO`.
  Antes gravava NULL, e uma liquidação pelos números da casa travava a aposta como se fosse correção
  do dono.
- **Bot dos tipsters** (`PATCH /bilhetes/{id}` sem sessão de navegador): grava `bot` e segue
  HUMANO. Conferido em `app/auth.py:632-643`: o `dono_efetivo_ou_bot` só aceita a sessão
  (`usuario_do_request`, cookie assinado) e o token do bot (`dono_do_bot`); nenhum middleware
  injeta identidade, e o PATCH só é chamado pela grade e pelo sharpen-bot.
- **Scripts:** `corrigir_resultado_odd_s321` grava `script_s321`; o runbook de scripts manda todo
  script novo gravar `script_sNNN`. `script_s429`, D30 e parecer020 seguem humanos. Nada de ALTER e
  nada de regravar origem no passado.
- **Ficam como estão (Feca):** o s321 decide quem pular lendo `correcoes` sem olhar a origem, e a
  regravação da Ficha só considera robô a `ficha` (lê esporte, mercado e descrição, que Resolver e
  Conferir nunca gravam).
- **Gates:** suíte pura 2.179, banco 132, mutações 6/6 com controle verde (bot sem origem, grade
  vira bot, `bot` vira robô, `resolver` vira humano, Resolver sem rastro, script vira robô), audits,
  harness 58 casos, `cru_mutacao`, `check-tokens`, `check_docs`.

---

## 2026-11-03 · s438 · c3: a trava do período (o número do time não é o tempo)

**Onde está:** no ar com o "pode" do Feca. Próximo: na primeira semente com a trava, mostrar os 13
termos da Megapari antes e depois, as apostas de novembro regravadas (dizendo se a 412223 entrou) e o
que as chaves de estatística aprenderam; o texto do aviso das 04h de 03/11; depois a lista de todo
caminho que grava `correcoes`, com arquivo:linha e se grava `origem` (item 3 da D44), e só depois o
código, com "pode".

- **A regra (Feca, 03/11/2026):** `Handicap 1` / `Team 1` / `Individual Total 1` é o time da casa (o
  primeiro do jogo); com `2`, o de fora. Esse número é sempre o time, nunca o tempo. O tempo só vem de
  "Half", "st half", "º Tempo" e afins.
- **O defeito:** quando o tempo e o time tinham o mesmo número, a `aprender` pegava o primeiro `{nX}`
  igual, e o primeiro era o do time. O termo saía certo por coincidência e errado no dia em que o time 2
  jogasse o 1º tempo.
- **A trava:** `_ocupados` marca o índice do time (`_INDICE_TRAVA`, que exige espaço, "(" ou fim depois
  do número, e por isso deixa "Handicap 1-st half" de fora) e a linha (depois de over/under, ou entre
  parênteses quando igual à linha ou ao handicap). Só o número da IA seguido de º/ª respeita a trava; o
  resto segue livre.
- **Medido (replay no código real, 02/11, 3.997 pares do estoque):** 15 termos mudam, todos Megapari:
  14 consertos e 1 de estilo; 0 pioras, nenhum termo novo. 2 dos 15 já são do Feca e a semente não
  mexe neles.
- **Teste antigo corrigido com o "pode" do Feca:** `test_sufixo_de_periodo_e_prorrogacao` esperava
  `{n1}` (o "2" do `Handicap 2`) para o 2º tempo; agora `{n3}` (o "2 Half").
- **Gates:** suíte pura 2.176, banco 130, mutações 4/4 (sem trava, sem a linha entre parênteses, índice
  com `\b`, trava em todo uso), audits, harness 58 casos, `cru_mutacao`, `check-tokens`, `check_docs`.

---

## 2026-11-02 · s438 · c1.2: o aviso diário só com o que está travado

**Onde está:** no ar com o "pode" do Feca. Próximo: mostrar ao Feca o texto do aviso das 04h de 03/11;
os termos das chaves de estatística na próxima semente; depois a trava da c3 (código, mutação e diff,
com "pode") e a lista de todo caminho que grava `correcoes` (item 3 da D44).

- **O defeito:** a semente relê a base inteira a cada rodada, então a mesma recusa voltava todo dia,
  mesmo com a chave já traduzida por outro voto, pela família (D41) ou por correção do Feca.
- **A régua:** `aviso_diario.travadas` usa a mesma `dicionario.carregar` da gravação (casa > família >
  geral, correção do Feca inclusive) e deixa no aviso só a chave sem termo por caminho nenhum, nas
  recusas repetidas e nos mercados gravados com o texto da casa. O aviso diz quantas saíram.
- **Medido (SELECT, 02/11):** recusas repetidas 185 → 19 ("perna sem trecho da IA do mesmo jogo" 137 →
  8); mercados com o texto da casa 39 → 31.
- **D41 medida (sementes 451 e 452, 02/11 21h20):** 80 apostas de novembro regravadas, 14 pela família
  (Vavada 13, BetRebels 1); as 80 batem com o dicionário só de termo unânime.
- **Gates:** suíte pura 2.174, banco 130, mutações 4/4 (sem filtro, sem família, sem o Feca geral,
  chave sem tipo), audits, harness 58 casos, `cru_mutacao`, `check-tokens`, `check_docs`.

---

## 2026-11-02 · s438 · c1.1: estatística da família x1 entra na chave

**Onde está:** no ar com o "pode" do Feca. Próximo: na primeira semente, mostrar ao Feca o que as chaves
novas aprenderam (chutes totais contra chutes no gol) antes de ele confiar nelas; depois, a c1.2 (o aviso
só com o que está travado de verdade), diff com "pode" antes do commit.

- **O defeito:** a Megapari escreve a estatística no nome do jogo (`Fouls Le Mans - Fouls Toulouse`), e
  a lista do subjogo não a conhecia: `Fouls Total Under (25.5)` caía em `football | total ({n})`, a
  chave de gols. A gravação da Ficha sairia "Under 25.5 Gols" para uma perna de faltas.
- **A lista (fechada, só estatística):** shots towards the goal, shots on target, fouls, offsides,
  throw-ins, goal kicks, two/three-point field goals scored, breaks, assists, time penalty, yellow
  cards, chutes no gol, remates na direção da baliza, lançamento lateral, foras de jogo, stats,
  estatísticas. "Los Angeles", "Clube Atletico", "C.D." e "1." ficam no nome.
- **Os dois lados:** o prefixo só sai quando abre os dois times (`descricao_ficha._times`);
  `Breaks Team - Outro` fica inteiro.
- **Medido (SELECT, 02/11):** o termo de gols da MEGAPARI (`{ou} Gols`) estava certo, com 2 votos de
  estatística em 19; 0 de 784 pernas da última semana mudam de chave; 334 no estoque da família x1.
- **Gates:** suíte pura 2.174, banco 129, mutações 6/6 (4 nomes tirados, regra genérica, `and` → `or`),
  audits, harness 58 casos, `cru_mutacao`, `check-tokens`, `check_docs`.

---

## 2026-11-02 · s438 · D41: dicionário por família

**Onde está:** no ar com o "pode" do Feca. Próximo: medir na primeira semente depois do deploy quantas
apostas de novembro tiveram a descrição regravada pela família (5 exemplos, antes e depois); depois, o
plano da etapa c (sem código).

- **Precedência:** casa > família > geral, e a correção do Feca vence a semente em qualquer nível.
- **Família:** vem do cru (`captura_crua.familia`), relida a cada 10 min (`irmas`). Sem mapa à mão, sem
  tabela nova. A consultoria conferiu no banco: nenhuma casa tem duas famílias, então a herança não
  cruza plataforma.
- **Unanimidade:** termo em que as irmãs divergem não passa de uma casa para a outra (decisão do Feca).
  Hoje são 118 (vb 84, x1 14, tv 13, jb 7); os 10 mais usados estão na mensagem ao Feca de 02/11.
- **Quem usa:** só a gravação da Ficha (`virada.py`) e o `regravar_mes`. A semente continua aprendendo
  por casa.
- **Herança medida (SELECT, 02/11):** de 0 a 77 categorias e de 6 a 248 descrições por casa (MelBet 248,
  Sportaza 239, Sapphirebet 226, BetRebels 205). Teto da regravação deste mês: 86 apostas da Ficha
  (Vavada 73, Megapari 10, BetRebels 2, Duel 1); campo editado à mão fica de fora.
- **Gates:** suíte pura 2.171, banco 129, `test_virada` 48, mutações 7/7, audits, harness 58 casos,
  `check-tokens`, `check_docs`.

---

## 2026-11-02 · s438 · D44: Conferir conta com a casa

**Onde está:** no ar com o "pode" do Feca, só a ferramenta. Nenhuma correção aplicada: o Feca clica
depois de olhar. Próximo: D41 (dicionário por família), com "pode" antes do commit; depois, origem em
todo caminho automático que grava `correcoes` (a liquidação automática do `main.py` primeiro).

- **Tela:** cartão "Conferir com a casa" no painel da conta (Extração) e um modal com a lista: data,
  aposta, o que está no Sharpen, o que está na casa e o que diverge (o campo em `--warn`). Valores em
  `fmtSaldo`, na moeda da casa (decisão do Feca). As oferecidas vêm marcadas; "Corrigir N".
- **Régua:** a do vigia (`vigia_comparar`), as duas pontas na moeda da casa, contra o cru mais
  recente de cada código. O cliente manda só ids; o servidor confere de novo e grava pela edição de
  sempre (`atualizar_bilhete`).
- **Origem da correção (decisão do Feca):** `correcoes.origem` já existia (s415, `'ficha'`). O botão
  grava `'conferir'`, e `ORIGENS_DE_ROBO` faz o `campos_corrigidos` e o próprio botão ignorarem as
  duas: a reliquidação da casa continua corrigindo. Origem nula é correção humana e não é oferecida.
  Sem ALTER.
- **Fora da lista, cada um com a sua contagem:**
  - cru aberto contra linha liquidada (o cru é de antes da liquidação): 25;
  - só a odd diverge e o P/L muda menos de 1,00 (Shuffle e Sportsbet.io guardam stake com 7 a 8 casas):
    6 que eram ruído de centavo;
  - bônus da casa no retorno, com a linha na odd da casa (Feca: "bônus não é odd"): Vavada 5520005256
    (1,29) e 5602432981 (4,68).
- **Medição antes do deploy** (uma consulta pelo `db_ro.py`, conferência local pela mesma função):
  Feca 3.060 conferidas de 3.101, **2 oferecidas** (Vavada 5579339795 L→W, 5581722163 W→L); Gabriel
  2.155 de 2.207, **1 oferecida** (MyStake 307657834 W→L), 16 corrigidas à mão. Das 16, 14 são da DEX
  marcadas V em 23/10 14:14: certas, a casa cancelou tudo, devolveu e encerrou a conta (Feca).
- **Testes:** 13 puros (`tests/test_conferir_conta.py`) e 3 no banco (`test_d44_*`). Mutações C7 a
  C13 detectadas; C13b (sem a trava de status no bônus) é inócua, porque cashout nunca paga acima de
  stake × odd. Suíte pura 2.166 e harness de banco 129 verdes.
- Achado para a etapa seguinte: há 67.428 correções com origem nula, e a liquidação automática
  (`main.py`, `_resolver_abertas`) grava sem origem. Não dá para separar o humano do automático no
  passado; o código passa a gravar daqui para a frente.

---

## 2026-11-02 · s438 · Primeira captura depois da D39: tudo pela Ficha

**Onde está:** a vigia da D39 fechou. Próximo: D44 com as decisões do Feca (diff e medição à espera do "pode").

- Gabriel, 02/11 07:47 a 07:54 (`virada_log`, SELECT pelo `db_ro.py`, conferido pela consultoria):
  1WIN 49 capturadas, 39 no banco, **10 pela Ficha**; VAVADA 138, 136, **2**; SPORTSBETIO 44, 43, **1**.
  13 apostas novas, todas pela Ficha, **nenhuma para a IA**; `cru_nao_chegou`, `sem_cru_novo`,
  `captura_incompleta` e `captura_esgotada` em zero. 7 das 13 gravaram perna com o texto da casa (D40).
- Telegram: o Feca confirmou as duas mensagens (o teste às 00:39 e o aviso diário às 04:00).
- Decisões do Feca para a D44 e a D41 (02/11): valores da D44 em `fmtSaldo`; a medição só pelo
  `db_ro.py`, nada de caminho novo de conexão; a correção feita pelo botão leva origem própria e não
  trava a reliquidação, a digitada à mão continua intocável; na D41 os 105 termos em que as irmãs
  divergem não passam de uma casa para a outra.

---

## 2026-11-02 · s438 · Manhã depois da autorização noturna: o que entrou, o que parou, o que falta

**Onde está:** D42 (commits 2 a 5) e D43 no ar. D44 e D41 só em código local, sem commit (limite
do Feca). Próximo: as 3 decisões do `PLANO_D41_D44.md` e a primeira captura de casa virada pós-D39.

**No ar, cada um com healthcheck aprovado e "Application startup complete":**

| Etapa | Commit | Deploy |
|---|---|---|
| D42 c2 · leitura da descrição | `1d78d8d` | `ae52454c` |
| D42 c3 · `semente_recusa` | `d3c893d` | `e72cd6f5` |
| D42 c4 · aviso diário | `c6f331b` | `c140c34a` |
| D42 c5 · vigia como fonte de voto | `a12398d` | `614833cb` |
| D43 · Bet Builder pela Ficha (Sportsbet.io) | `a8d8ec3` | `5c0372b7` |

**O que parou e por quê:** só a 1ª tentativa de commit da D43, barrada porque o teste carregava os
crus de produção dos 5 aprovados. O arquivo saiu e os testes foram refeitos com a fixture do
harness e pernas sintéticas; nada foi para o ar com dado de produção. Nenhuma etapa deixou de subir.

**Telegram:** a mensagem "teste do aviso diário da semente" saiu em 02/11 00:39:13 (`aviso_admin`
teste-s438, ok). Falta o Feca confirmar que chegou no celular.

**Semente e aviso das 04h (SELECT às 04:35):**
- `semente_log` id 450, `diaria`, 04:00:49: 2.424 termos na rodada, 205 preservados pelo E1.
- 1º aviso diário real: `aviso_admin` diario-2026-11-02, ok, 04:00:49. 174 chaves com recusa
  repetida (≥3 na rodada); as três primeiras são da MEGAPARI, "perna sem trecho da IA do mesmo
  jogo" (96, 77 e 74). É o primeiro alvo de ajuste da leitura.
- `semente_recusa`: 1.881 linhas, 3.129 recusas somadas, todas `origem='semente'`.

**Vigia da primeira captura pós-D39:** nenhuma captura de casa virada entre o deploy (01/11 23:02)
e 04:35 de 02/11 (`virada_log` e `ficha_virada` vazios no período). A vigia segue aberta; a
medição sai na primeira captura do dia. Também nenhuma aposta Sportsbet.io pela Ficha ainda (D43).

**D44 e D41, só local:** testes e mutações verdes (D44 6/6, suíte pura 2162, banco 128; D41 7/7,
pura 2158, banco 126). Patches em `Planilhador/Backups/s438_d41_d44_local/`, plano em
`Auditorias/consultoria_ficha_2026-10/PLANO_D41_D44.md`. Decisões com o Feca: (1) convenção da tela
da D44 (`fmtSaldo`?); (2) medição só leitura na produção por um caminho novo, fora do `db_ro.py`;
(3) correção feita pelo botão vira "corrigida à mão" numa reliquidação, aceitar ou marcar a origem
em `correcoes`. Na D41: 105 termos em que as irmãs divergem (vb 73), quase tudo estilo.

**Alarme falso registrado:** o Git Bash mostrou UTC rotulado como horário de Brasília e por alguns
minutos pareceu que a semente das 04h tinha falhado. Eram 01:30. Hora se lê do `now()` do banco.

---

## 2026-11-02 · s438 · D43: Bet Builder pela Ficha, Sportsbet.io (deploy autônomo)

**Onde está:** no ar sob a autorização noturna do Feca. Próximo: D44 e D41 só como plano e código
local, sem commit (limite do Feca).

- O adaptador `sbi` deixou de recusar o Bet Builder. Ele já era UMA perna (`_perna`), com a odd do
  conjunto; o dinheiro sai do bilhete pelo caminho que já existia (stake, status, retorno,
  `totalOdds`), sem mudança no cálculo. Nos 5 aprovados, odd e resultado iguais aos que a IA tinha
  gravado (4,6 L · 3,75 W · 6 L · 5,25 L · 24 L).
- Categoria: Bet Builder é sempre `Múltipla` (`MASTER_APOSTAS`, "Bet Builder / Criar Aposta"),
  inclusive o que a IA tinha gravado como Player Props. Esporte: o do jogo.
- Descrição (`dicionario.descricao_bet_builder`), no formato das 5 linhas aprovadas: o mesmo jogador
  junta com ` / ` na ordem da casa, jogadores ou jogos diferentes com ` // `, um colchete só. No
  5º aprovado (dois Bet Builders numa múltipla) a ordem das pernas é a da casa (J. Smith primeiro),
  não a que a IA tinha escrito.
- Medido nos 52 Bet Builders da casa (25 a 31/10): só Pontos, Rebotes e Assistências, todos de
  "Partida". Seleção fora disso grava com o texto da casa (D40), nunca vai à IA por isso.
- A semente não aprende com o Bet Builder (categoria e descrição vêm de regra) e ele não gera recusa
  falsa na `semente_recusa`.
- Testes: os 11 Bet Builders da fixture do harness (já no repositório) e as 5 aprovadas por pernas
  montadas só com seleção e jogo. A 1ª versão trazia os crus de produção dos 5 aprovados num JSON
  de teste; o commit foi barrado (dado de produção no repositório público) e o arquivo saiu.
  Bilhete de Bet Builder com 3+ jogos sai `Múltiplos` de esporte pela regra global, não pela D43.
- 20bet e Altenar seguem recusando Bet Builder (3 e 1 no histórico). Mutações 7/7; gates do CI
  verdes (suíte pura 2154, harness de banco 126, harness da extensão 58).

---

## 2026-11-02 · s438 · D42, commit 5: o vigia como fonte de voto (deploy autônomo); D42 completa

**Onde está:** D42 inteira no ar. Próximo: D43 (Bet Builder pela Ficha, no formato das 5 linhas).

- **Aviso de teste:** enviado pelo app ao subir o commit 4 e confirmado pelo Telegram (`aviso_admin`,
  chave `teste-s438`, `ok = true`, 02/11 00:39:13). O Feca confere de manhã se chegou.
- A D40 tirou a IA do caminho da descrição desconhecida; o vigia é quem ainda lê essas apostas. A
  semente passa a usar a descrição que o vigia leu (`vigia_ficha.ia->>'descricao'`) quando a aposta
  não tem voto melhor (linha da IA ou sombra): só descrição, porque o vigia não lê esporte nem
  categoria (`semente_log.fontes.vigia`).
- A gravação da Ficha marca no `ficha_virada` a aposta com perna no texto da casa (`motivo = 'texto
  da casa'`), e o `vigia_candidatos` a escolhe primeiro. A cota (3 por casa e dia) e a comparação de
  dinheiro do vigia não mudam.
- Achado de teste: a `vigia_ficha` não era limpa entre testes do harness; passou a ser.
- Mutações 3/3. Nada muda em odd, stake ou resultado; nenhum ALTER.

---

## 2026-11-02 · s438 · D42, commit 4: o aviso diário ao Feca (deploy autônomo)

**Onde está:** no ar sob a autorização noturna do Feca. Próximo: commit 5 (o vigia como fonte de voto).

- `app/aviso_diario.py`, chamado logo depois da semente das 04h (`dicionario.diario`), manda ao canal
  `TELEGRAM_ALERTA_*` (o do aviso de cadastro, `main.avisar_admin`): recusas repetidas (≥3 na rodada,
  da `semente_recusa`), mercados gravados com o texto da casa nas últimas 24 h, se a semente rodou
  (termos, preservadas) ou falhou (as falhas da semente diária e da semente logo depois da IA entram
  pelo `registrar_falha`), apostas pendentes há mais de 24 h e captura incompleta esgotada em 24 h.
- Só contagens por casa e chaves de mercado: nenhum usuário (teste com dono `TDonoSecreto` confere).
  Dia quieto não manda. No máximo um por dia: tabela nova `aviso_admin`, reservada antes do envio
  (`ON CONFLICT DO NOTHING`); o envio que falha fica com `ok = false` e não se repete no dia.
- A mensagem de teste que o Feca pediu ("teste do aviso diário da semente") sai UMA vez, pelo próprio
  app ao subir (`teste_uma_vez`, chave `teste-s438`): ninguém toca no token.
- Mutações 7/7. Não cobre a entrega real do Telegram (dublada nos testes) nem o horário das 04h.

---

## 2026-11-02 · s438 · D42, commit 3: a `semente_recusa` (deploy autônomo)

**Onde está:** no ar sob a autorização noturna do Feca. Próximo: commit 4 (aviso diário).

- Tabela nova e pequena `semente_recusa`: uma linha por (casa, tipo, chave, motivo), com o termo, um
  exemplo e `n`. Três fontes: o voto de descrição que a semente recusa, com o motivo exato (jogo da
  IA diferente, IA sem o `[jogo]`, IA sem `{time}`/`{ent}`/`{ou}`, número que sobrou, nome próprio
  sobrou, seleção Sim/Não sozinha, perna sem trecho da IA, mercado de time sem o time); o voto de
  categoria ou esporte com valor da IA fora do Master; e a perna que a Ficha gravou com o texto da
  casa (`origem='gravacao'`, o `faltam` que o `virada.py:145` descartava).
- `n` da semente é o retrato da rodada (ela relê a base inteira); o da gravação soma por gravação.
- Registrar nunca para a semente nem a gravação (try/except com log). Mutações 7/7. Sem ALTER em
  tabela grande; nada muda em odd, stake ou resultado.

---

## 2026-11-02 · s438 · D42, commit 2: a leitura da descrição (deploy autônomo)

**Onde está:** no ar sob a autorização noturna do Feca (02/11, "pode seguir sozinha, uma etapa por
vez"). Próximo: commit 3 (`semente_recusa`).

O que muda em `app/descricao_ficha.py`, com exemplo real da semana de 26/10 a 01/11 em cada:
- **Prefixo comum** só sai quando é subjogo da 1xBet (Cantos, Corners, Escanteios, Cartões, Cards,
  Remates enquadrados, Estatísticas dos jogadores, Players' stats): 344 pernas perdiam nome de time
  (`Los Angeles Lakers - Los Angeles Clippers` virava `[Lakers v Clippers]`; `FC Slavia Mozyr` perdia
  o `FC`; `Cantos VfL Wolfsburg` cortava o `VfL`).
- **Sufixo no time 2 (E2):** o período (`2 Half`, `1 Metade`) entra na chave do mercado (antes um
  handicap do 2º tempo caía na chave do jogo inteiro); a prorrogação (`(Including Overtime)`) só sai
  do time, para não deixar órfã a chave já aprendida, e `_mesmo_jogo` a ignora nos dois lados.
- **F1:** `Mexican Grand Prix Practice 1 vs Winner` é prova, não confronto; o colchete é a prova.
- **E3:** `más` é lado; seleção Sim/Não não ensina nem monta descrição que seja só ela (`Sim [jogo]`,
  o caso que o Gabriel corrigiu em 18/10): vira texto da casa (D40).
- **E4:** ordinal por extenso antes de período vira número (`Primeiro set` → `1 set`). A chave
  aprendida na forma antiga segue valendo como 2ª tentativa: sem isso, 113 pernas perdiam a
  descrição do dicionário (medido no replay).
- **Linha asiática:** `1.5/2` é 1.75, como a IA escreve. **E5:** nome de 2 palavras também invertido.

Replay contra o dicionário de produção (sem banco): votos que a IA consegue dar 3.257 → 3.529; 46
apostas passam a ser cobertas; 4 perdem a cobertura, todas do E3 e intencionais; 9 descrições da F1
mudam (o colchete). Mutações 12/12. Sem exemplo medido na semana (teste sintético): `más` e o nome
invertido sem vírgula. Nada muda em odd, stake ou resultado; nenhum ALTER.

---

## 2026-11-02 · s438 · D42, commit 1: a semente para de esquecer (E1)

**Onde está:** aprovado pelo Feca para deploy. Próximo: commit 2 da D42 (leitura da descrição: E2 a
E5, prefixo comum e confronto falso da F1); depois, logo, os commits 3 e 4 (`semente_recusa` e o
aviso diário), que vão mostrar ao Feca os erros que a semente agora guarda.

- A semente era refeita do zero a cada rodada (DELETE de toda a semente), e a chave cuja fonte sumia
  sumia junto (medido em 01/11: 350 ausentes, 86 saíram e voltaram com o mesmo valor). Agora
  `gravar_semente` acumula; a chave sai só com prova contra: contraditória na rodada, retirada por
  aposta editada à mão (R27: `pares_completo` devolve `chaves_que_votaria` da aposta editada) ou
  casa de grafia antiga. O `semente_log` registra as preservadas.
- Fica descoberto, por decisão (D24): chave errada de 1 voto cuja fonte sumiu sem edição à mão fica
  até um voto novo ou a correção do Feca.
- Gates: 4 testes no harness; mutações 4/4 (a da edição à mão escapava no teste antigo da R27, onde
  o voto do texto compensava; o teste novo confere a categoria). Sem teste: a retirada pelo voto do
  texto quando a aposta editada é da Ficha.

---

## 2026-11-01 · s438 · D40: descrição desconhecida nunca manda a aposta à IA

**Onde está:** aprovada pelo Feca para deploy. Próximo: D42 (com o prefixo comum e o confronto
falso da F1, pedido do Feca).

- A perna sem par no dicionário de descrição grava como a casa escreve:
  `<mercado da casa> - <seleção da casa> [A v B]` (`descricao_ficha.texto_da_casa`, limpo de
  espaço, quebra e TAB), sem marca para corrigir. As outras pernas saem do dicionário. A aposta só
  vai à IA com outro motivo (ou perna sem mercado e sem seleção).
- Quem grava usa `virada.descricao_para_gravar`; `virada.descricao` segue estrita (regravação do mês
  e scripts). Aprovado pelo Feca: quando o dicionário aprende o mercado, a regravação do mês troca o
  texto da casa pela forma do dicionário, com rastro e respeitando edição à mão. Estrita também
  protege contra o E1: chave que some do dicionário não rebaixa descrição boa a texto da casa.
- Replay da semana de 26/10 a 01/11 (sem banco): das 318 apostas à IA só por descrição, 173 a Ficha
  grava agora, 145 o dicionário de hoje já cobre, nenhuma sem montar (132 com 1 perna no texto da
  casa, 27 com 2, 14 com 3). Mutações 6/6.
- Herdados da forma `[A v B]` (valem também para as pernas do dicionário), para a D42: prefixo comum
  cortado (`FC Brest [Brest v Vitebsk]`) e evento de F1 virando confronto falso
  (`[Mexican Grand Prix Practice 1 v Winner]`).

---

## 2026-11-01 · s438 · Scripts pela lixeira e expurgo de 90 dias

**Onde está:** aprovado pelo Feca para deploy. Próximo: D40.

- Os 24 scripts com `DELETE FROM bilhetes` (16 imports que se refazem, 4 reparos, 4 avulsos)
  passam por `repository._mover_para_lixeira`, via `scripts/_lixeira.py`. A função ganhou
  `mantido_id` (reparo de duplicata) e `snapshot` (backup em arquivo). A poda de conta saiu da
  `lixeira_contas`.
- Expurgo da `lixeira_bilhetes` em **90 dias** (Feca: a prova do Gabriel foi pedida semanas
  depois), preguiçoso, por dono, na exclusão (função da lixeira e Base Completa).
- Gate `tests/test_lixeira_sempre.py` estendido a `scripts/`; 3 testes no harness; mutações 5/5.
- Achado e corrigido antes do commit: a troca deixou o `podar_conta_para_lista.py` imprimindo uma
  variável que saiu (`NameError` depois de apagar); `pyflakes` limpo nos 25. E os meus executores
  de mutação restauravam com `write_text` (CRLF): agora gravam em bytes.
- **Regra nova do Feca:** a 1ª execução de cada um dos 24 roda antes no Postgres de teste local
  (`docs/RUNBOOK_SCRIPTS_DE_BANCO.md`, com a tabela de quem já rodou). O `CLAUDE.md` estava no teto:
  o relato do `_c2num` foi para o `CASOS.md` e uma frase duplicada do caso dos 16 donos saiu.

---

## 2026-11-01 · s438 · Fase 7: toda exclusão de aposta passa pela lixeira

**Onde está:** Fase 7 aprovada para deploy. Ordem do Feca daqui em diante: scripts e expurgo
(90 dias) da lixeira, D40, D42, D43, D44 ("Conferir conta com a casa"), D41.

**Por que o Gabriel apagou e recapturou a Shuffle (31/10):** a Caixa de 17/10 projetava −US$ 305,94
contra US$ 250,29 na casa, e ele lançou ajuste de +US$ 556,23 (`caixa_mov` 1454/1455). A tela não
tem como corrigir base gravada (recapturar não conserta linha resolvida, o UPSERT congela), então a
saída foi apagar. Hoje os 109 códigos da casa estão no banco. O que estava errado antes não dá para
saber: as linhas foram apagadas sem lixeira. O tipster não era o motivo (o "Editar selecionadas"
existe; ele remarcou 86 no mesmo minuto). Viraram a D44 e o BACKLOG 3.22.

**O que mudou:** `repository._mover_para_lixeira` (DELETE … RETURNING e INSERT na
`lixeira_bilhetes` numa instrução só, com `lixeira_id` de volta); `deletar_bilhetes` e
`remover_bilhetes_supersedidos` passam por ela; motivo escolhido por chave, texto do servidor; o
"Desfazer" do toast tira da lixeira a linha que voltou (a que colidiu fica: o dado novo mandou); o
"sem linha" da D39 lê também a `lixeira_contas`; o aviso do "Desfazer análise" diz lixeira, não
"apaga do banco". Gates: `tests/test_lixeira_sempre.py` (AST, nenhum `DELETE FROM bilhetes` no app
fora das três funções que guardam) e 5 testes no harness; mutações 5/5. BACKLOG 4.19 fechado.

**Ferramenta:** o `write_text` do Python tinha convertido 13 arquivos editados nesta sessão para
CRLF (o git normaliza no commit; o teste JS do aviso quebrou localmente). Voltados para LF e o teste
ficou imune a CRLF. Mesma família da memória `escrita_por_script_converte_lf_em_crlf`.

---

## 2026-11-01 · s438 · D39: falta de cru nunca vai à IA, e aposta nunca some em silêncio

**Onde está:** D39 escrita, testada e aprovada pelo Feca para deploy (com a proteção da extensão
sem cru e a saída do segurado). Próximo: conferir o deploy e a 1ª captura de casa virada com a
métrica nova; depois a **Fase 7** (toda exclusão pela lixeira), antes da D40, porque o aviso "sem
linha" marcaria para sempre as apostas apagadas pela tela de Extração.

**1ª captura depois da Extra:** Vavada do Feca, 01/11 22:54 (`virada_log`): 151 capturadas, 145 já
no banco, 5 pela Ficha, 1 à IA (US$ 0,035); 7 linhas da Ficha gravadas.

**As regras (`app/virada.py`, bloco "D39"):**
- (a) cru guardado **liquidado**: a Ficha grava, sem IA. Base: 963 de 976 "texto mudou sem cru
  novo" tinham cru final, 100% iguais ao que a IA gravou. Trava contra reliquidação: o veredito do
  próprio texto (`Status: … → X`, as 13 casas viradas o escrevem); só a CLASSE conta (W/HW, L/HL, V).
- (b) cru **aberto** com texto mudado, ou cru que não chegou: **segurado** (fora da IA), pendente
  com o aviso "captura incompleta: atualize a aba da casa (F5) e extraia de novo". Só segura cru
  ausente se a casa mandou cru ao dono nos últimos 7 dias (extensão sem cru: vai à IA; OK do Feca).
  **Saída:** segurado há 2 `/extrair` da mesma casa e dono, ou há mais de 24 h, vai à IA **uma
  vez** (`captura incompleta esgotada`, coluna `captura_esgotada`); "uma vez" é por impressão do
  cru, para o cashout na tela não ir à IA a cada 3 capturas. Log com contagem para o aviso diário
  da D42.
- (c) foi à IA num `/extrair` anterior e **não virou linha** (o caso da Duel): pendente "sem
  linha", só avisa; sai quando a linha existe, quando vai para a lixeira ou quando a Ficha grava.
  Só vale para decisões a partir de 01/11 22:00.
- (d) chave da casa sem espaço, **ponto e acento** (`app/casa_chave.py`): Sportsbet.io, Stake.com,
  Betão e Vitória Bet não batiam; o aviso de não lidas nunca funcionou nas casas com ponto, e a
  semente gravava chaves paralelas (somem na rodada das 04h, que regrava a semente).

**Gates:** `test_virada.py` 43, harness de banco 105, suíte pura 2.128 (a falha de
`test_recorte_custos` é anterior), `tests/js/aviso_captura_incompleta.mjs`. **Mutações 19/19 em
Python + 1 em JS.** Duas escaparam no caminho e eram defeito do teste ou do código, não inócuas: a
lixeira conferida em dois lugares (ficou só na soltura) e o teste das 24 h que a contagem de
`/extrair` mascarava. Backup em `Backups/s438_d39_falta_de_cru_e_grafia/`.

---

## 2026-11-01 · s438 · Consultoria 022: Parte 1, Fase 0 e a Extra (lock_timeout + healthcheck)

**Onde está:** ordem aprovada pelo Feca (01/11/2026): Extra, D39 (com a grafia com ponto), Fase 7,
D40, D42, D43, D41. A Extra foi escrita, testada e aprovada para deploy. Próximo: conferir o deploy,
gravar a aposta perdida da Duel (com prévia) e preparar a do Jaao26; depois a D39.

**Parte 1 (só leitura; consultas em `Auditorias/consultoria_ficha_2026-10`, painel de 01/11).**
- IA estável (1.316 contra 1.317, `virada_log`, semanas de 19 a 25/10 e de 26/10 a 01/11) por
  compensação: as casas antigas caíram cerca de 405; Shuffle +247 (216 do caso de 31/10) e Sportsbet.io
  +180 (casa nova). A Ficha caiu porque havia menos aposta aberta no texto (Vavada 1.235 para 648,
  capturando mais), não por piora.
- **Cru final esconde nada:** dos 976 códigos cujo último motivo foi "texto mudou sem cru novo", 963
  tinham o cru guardado já liquidado e o resultado bate 100% com o da IA (762 L, 209 W, 5 V); só 4
  de cru aberto viraram L, que é o caso que a N3 protege. É a base da D39.
- Custo: titular das casas viradas, de 26/10 a 01/11, US$ 16,58 / 1.321 envios = US$ 0,0126 por aposta.
- Descrição (7 dias): 314 de 318 códigos são múltiplas; 228 pernas sem par: sufixo no time 2 73,
  prefixo 16, IA sem o time 49 (erro da IA, a recusa está certa), número que sobrou e marca faltando
  42, jogo que não pareia por outro motivo 45.
- D41 medida com o dicionário de hoje: a família acrescenta 9 apostas por semana; 145 dos 318 códigos
  de descrição já passam só com a casa (a semente aprendeu depois).

**Fase 0.** Das 7 "sem linha": 6 Stake.com do Feca existem sob a grafia com ponto (`STAKE.COM` ≠
`STAKECOM`). Perdidas de fato: 1win 338677290 do Jaao26 (R$ 250 L; lote de 116 com a conta `Old`
criada 1 min antes, 115 gravadas; o log de 16/10 expirou) e Duel 2728364620980039864 do Feca (o
leitor recusou a linha da IA duas vezes, a 2ª com a odd na coluna do código; nunca virou pendente).
A Shuffle do Gabriel foi apagada pelo próprio Gabriel (confirmado pelo Feca), pela tela de Extração,
`DELETE /bilhetes` sem lixeira, em 31/10 às 19:54 e às 19:56; as 108 foram pagas duas vezes por
apagar e recapturar. **Corrige a Parte 1**, que tinha dado corrida de commit (o `criado_em` é o
`submitted_at` do clique, não a hora do INSERT).

**Apostas perdidas (01/11, depois do deploy da Extra).**
- **Duel 2728364620980039864 (Feca): ficou cerca de 22 h fora do banco** (de 31/10 23:58 a 01/11
  21:41) e só voltou porque houve uma nova captura depois da liquidação: a **3ª ida à IA**. Nas duas
  primeiras o leitor recusou a linha da IA (a 2ª com a odd na coluna do código), e nenhuma das duas
  virou pendente. Voltou como id 412424, R$ 161,35 (30 USDT) @ 13, L, dinheiro igual ao cru; a IA
  gravou categoria `Múltipla` numa simples (a Ficha diz `ML`). **É o caso que a D39 tem de fechar.**
- **1win 338677290 (Jaao26): gravada pela Ficha** com o OK do Feca
  (`scripts/recuperar_aposta_perdida_s438.py --aplicar`, 01/11 22:18): id 413103, conta `1win` (não
  `Old`: a `Old` só tem 26/09 a 10/10), 13/10/2026, Futebol, Gols, `Under 4.5 [Noruega (f) v Roménia
  (f)]`, R$ 250 @ 2,16, L, origem `ficha`; rastro em `correcoes` (campo `recuperacao`, origem `ficha`).

**Extra.** `init_db` com `SET LOCAL lock_timeout = '5s'`, 6 tentativas e 10 s de pausa;
`healthcheckPath = "/healthz"` e `healthcheckTimeout = 300` no `railway.toml`. Mutações 5 de 6; a
inócua (`SET` × `SET LOCAL`) está escrita no teste.

---

## 2026-10-23 · s427 · As 6 casas com adaptador viradas, e a Vave na Ficha (adaptador `vv`)

**Onde está:** BETREBELS, SAPPHIREBET, BETFURY, BETCOIN, MELBET e JACK viradas (deploy `ebd2ce2b`,
semente aplicada). Vave com adaptador escrito e testado, SharpenUp 0.7.63; **falta** push, deploy,
`VAVE` nas 3 listas da Railway e a 1ª captura com a 0.7.63 conferida no `virada_log`.

**Varredura das casas em uso (30 dias).** Viradas: DEXSPORT, MYSTAKE, VAVADA, 1WIN, DUEL, SHUFFLE,
BETPANDA, BETMARTINI, MEGAPARI, THUNDERPICK. Com adaptador e fora da virada: as seis acima. Cru
sem adaptador: VAVE. Sem cru nenhum gravado, embora o inject mande: as casas .bet.br (Bet365,
Betano, Stake, Novibet, Superbet, Pinnacle, Betnacional) e algumas de fora (Paripesa, 1xBit);
**decisão do Feca (23/10/2026): as .bet.br ficam em banho-maria até a legislação liberar**
(BACKLOG).

**Backtest das seis (Ficha × IA nos crus reais, só leitura):** BETREBELS 193 iguais de 212,
SAPPHIREBET 25/28, BETFURY 24/57, BETCOIN 10/25, MELBET 17/18, JACK 14/14. Toda divergência é
data ou odd de L. Data: a IA usou a colocação (BETREBELS 5507574880: pernas de 10/10 à tarde,
colocada 09/10 23:32) ou o dia em UTC (SAPPHIREBET 88903282387: perna às 00:00 de 17/10 em SP);
na perdida múltipla a Ficha segue a perna perdida mais cedo (BETFURY 2718264971782918604, 03/10).
Odd de L: a exata da casa contra a truncada da IA. A Ficha segue a regra aprovada; D10 garante
que nada liquidado é reescrito.

**Vave.** O histórico só traz o id do mercado e da seleção; o nome mora em dois dicionários
públicos da casa (template Sportradar). O `vv_inject` passa a mandar no cru as linhas que o
bilhete usa (`dicionario`, o template verbatim, montado na hora do envio, quando o dicionário já
carregou), e o `app/adaptadores/vv.py` resolve como o inject. Ganha medida nos crus reais
(5402884: 33 × 1,9; `win` = `winFull` = 62,7, o retorno). Recusa: cru sem `dicionario`, perna
sem a linha do dicionário, placeholder sem valor, `system`, bet builder, bônus, freebet,
`betCashoutAmount`, status 3/8/outro cujo dinheiro não é a stake.

**Genérico:** o time escrito no mercado (`{$competitor1} clean sheet` → `Athletic Bilbao clean
sheet`) era uma chave de categoria por time. `descricao_ficha.mercado_com_time` +
`dicionario._merc_time` acrescentam a chave com `{time}` (mesma família do `{jogador}`, s415);
nenhuma chave existente muda.

**Medido:** 35 crus `vv` no banco (Feca 11, Gabriel 24), com o dicionário baixado à parte: 35
aceitos, 34 iguais à IA em resultado, data e odd; 1 (5376409) com a odd do card 5,02 onde a IA
gravou 5,019999999778. Os 35 em produção não têm `dicionario` e seguem pela IA.

**Gates:** `tests/test_adaptador_vv.py` (17, 10 mutações detectadas), harness da Vave com o
dicionário no cru (3 mutações detectadas), `test_cru` com `vv`, pytest 1968, harness 51 verde.

**Próxima ação:** push; depois do deploy, `VAVE` em `FICHA_SOMBRA_CASAS`, `FICHA_CASAS_VIRADAS` e
`EXTRACAO_SEM_PENSAMENTO`; 1ª captura da Vave (e da Thunderpick) com a 0.7.63 conferida no
`virada_log`.

---

## 2026-10-23 · s426 · Thunderpick: o adaptador `thp` (a casa tinha entrado só pela IA)

**Onde está:** adaptador escrito e testado; **falta `THUNDERPICK` em `FICHA_CASAS_VIRADAS`** (a
CLI da Railway está deslogada nesta máquina) e a 1ª captura virada conferida no `virada_log`.

**O que aconteceu.** A Thunderpick entrou no SharpenUp 0.7.61 (s426, 22/10) com inject, formatador
e cru, mas sem adaptador: os 180 crus da família `thp` chegavam e nenhum virava Ficha, e cada
bilhete ia à IA. O Feca: "as exportações estão demorando eternidades … TODAS AS CASAS PRECISAM
ESTAR ASSIM". Erro de quem criou a casa; a Vave (s425) tem o mesmo buraco.

**Adaptador** (`app/adaptadores/thp.py`): código `C`/`S` + `wagerId` (o mesmo do texto), centavos
de euro ÷ 100, moeda `EUR`, ganha com tolerância de 1 centavo (a casa arredonda sem regra fixa),
retorno = stake é anulada, `cancelReason`/`cashOutOdds`/`freeBet` recusam, esporte pelo `gameId`
(mapa medido; 43 = Badminton somado hoje; 23 e 31 sem prova, ficam vazios). Mercado de jogador:
a casa escreve `Player <Sobrenome> <Nome> - …`, e o ` - ` escondia o jogador do
`descricao_ficha._jogador` (chave por jogador = todo jogador novo à IA); a Ficha leva `<Nome>
<Sobrenome> …`, a ordem que a IA escreve (conferido contra a descrição da IA em 11 crus reais).

**Medido (banco de produção, só leitura):**
- 152 crus distintos: 147 Fichas aceitas, 5 recusadas (3 "Cancelled by player", 1 perna
  "Technical lose", 1 `cashOutOdds 1.86`). Filtro de pessoa: nenhum campo removido; nomes de
  campo varridos (topo e perna), nenhum de pessoa.
- Nas 43 com linha no banco: resultado, data e odd iguais aos da IA; nas ganhas, a odd da IA fecha
  o retorno em EUR. A stake difere só pela conversão (o banco guarda R$; a Ficha, EUR).
- "Deixa um de fora" nos 43 pares: 26 resolveriam esporte, categoria e descrição sem a IA; nenhuma
  diferiu da IA. O resto é mercado visto uma vez só.
- Semente em ensaio: 26 categorias, 98 descrições e 4 esportes para a THUNDERPICK.
- 98 crus do Gabriel e 6 do Feca sem linha em `bilhetes` (captura sem `/salvar`).

**Gates:** `tests/test_adaptador_thp.py` (16, 11 mutações detectadas), `test_cru` com a família
`thp`, harness verde. SharpenUp 0.7.62 (só o badminton no texto).

**Próxima ação:** `FICHA_CASAS_VIRADAS` += `THUNDERPICK`; semente na hora
(`scripts/semear_dicionario.py --aplicar`); 1ª captura conferida no `virada_log`. Depois, a
varredura das casas em uso pedida pelo Feca (adaptador e virada de cada uma).

---

## 2026-10-19 · s423 · Parte C: a carga do dicionário (parecer 021, D33 a D37) e o §4.18

**Código e Master (commit `cfc38fd`, deploy `bbb2c0e0`).** `MASTER_ESPORTES §7` ganhou Boxe, Críquete,
Futsal, Polo Aquático, Futebol Australiano, Bandy e Floorball (D33), e MMA ganhou os sinônimos de artes
marciais. `descricao_ficha.estilo`: `Mortes`, `kills` e `Abates` viram `Kills` (D35, todas as casas).
`dicionario.VAGOS`: `sporttypeid 300` (D36) e `sporttypeid 34` e `31` (D37, Feca 18/10: o bilhete dizia
Tênis de Mesa e Críquete, mas o id não é esporte; o esporte sai do evento, pela IA). Os dois da D37
não tinham linha no banco. Gate: `tests/test_dicionario_d33_d36.py`, 6 mutações, 6 detectadas.

**Carga (`scripts/carga_dicionario_s423.py --aplicar`, depois do deploy).** 36 correções `origem=feca`
e o 300 apagado do `*` e da ESPORTIVA. Teste antes e depois:
- a. dicionário: `*` esporte de 57 semente para 28 feca + 50 semente; DEX descrição feca 7 → 10;
  MyStake descrição feca 1 → 3 e categoria 1 → 2; BetMartini descrição feca 5 → 6; ESPORTIVA 6 → 5.
- b. último `semente_log`: 178 nos dois (nenhuma semente rodou no meio).
- c. cobertura das 9 casas: 2.292 → 2.398 de 3.042 (75,3% → 78,8%); termo fora 244 → 95, descrição
  fora 504 → 547 (apostas que passaram do termo e param agora na descrição), Ficha recusada 2.
- d. agosto e setembro por casa: idêntico antes e depois (D10).
- Regravadas 3 apostas da Ficha, todas de outubro, todas do Gabriel, só a descrição, com rastro em
  `correcoes` (`origem=ficha`): 383276, 384179 e 385618, `Pontos 1º Quarto` → `Pontos 1ª Metade` na
  perna `total. half` (a perna `total. quarter` da 384179 segue `1º Quarto`).
- `novos` da próxima semente (a conta do `semear`, sem gravar): 0. Antes da carga eram 2, os dois Kills
  da MyStake, que a carga cobriu pela origem feca.

**§4.18 fechado.** `virada._liquidados` passou a conferir a casa (`upper(replace(casa,' ','')) = chave`,
a régua do `_pendentes`): o código liquidado noutra casa do dono não tira mais a aposta da Ficha. A chave
bate com `bilhetes.casa` nas 9 casas viradas; no banco, 0 códigos repetidos entre casas do mesmo dono
(nenhuma aposta se perdeu por isso). Gates: `test_s423_liquidada_noutra_casa_nao_tira_a_aposta_da_ficha`
e `test_s423_pendente_com_codigo_noutra_casa_e_tentado_de_novo`; mutações L1 (sem a casa), L2 (grafia de
exibição no lugar da chave) e N5.1 (a nova tentativa do `_pendentes` sem a casa, antes inócua), 3
detectadas.

**Próximo passo:** etapa 3 do anexo, o histórico como voto da semente, com ensaio próprio.

## 2026-10-19 · s423 · Parte A, passos 2 e 4: o rastro da Ficha em `correcoes` e a D30

**A3.** DEX Sport 850e48f2 (id 383282, Gabriel): a Ficha a gravou ABERTA com odd 6,05 (`coefficient`
nos três crus de 14/10); a perna DNB anulou e a captura das 23:40 a liquidou W com 2,48 (payout 124 ÷
50). A mudança está certa e não deixou rastro: o UPSERT nunca gravou em `correcoes`, só a regravação
do dicionário (e só descrição). Agora `repository._rastro_ficha`: com `origem='ficha'`, o
`upsert_bilhetes` lê a linha antes, o `RETURNING` devolve odd/stake/moeda/cotação, e cada campo que
mudou vira linha em `correcoes` com `origem='ficha'` (nos dois caminhos, ON CONFLICT e fallback do
`UniqueViolationError`). `campos_corrigidos` (o "correção humana manda" dos scripts de reparo) ignora
`origem='ficha'`; a edição à mão continua travando. Linha retroativa da 383282:
`scripts/rastro_retroativo_383282_s423.py`, no instante da mudança (14/10 23:41:21 UTC), aplicada
depois do deploy. Atenção para quem escrever script de reparo: os que leem `correcoes` sem filtro
de origem (`corrigir_*_s3xx`, `corrigir_bonus_odd_mystake_s422`) contariam o rastro da Ficha como
humano; o novo tem de filtrar como o `campos_corrigidos`. Gates: 4 testes de banco com o caso real;
mutações R1 a R4, 4 detectadas.

**A4 (D30, registro, sem refazer).** A regravação da D30 deixou rastro: 156 linhas em `correcoes`
(`origem='d30'`: 52 `moeda`, 52 `stake`, 52 `cotacao`), todas às 15:26:10 UTC de 14/10, nos ids
daquela data. Esses 52 ids não existem mais: o usuário apagou as apostas num `DELETE /bilhetes` em
lote pela tela da conta Megapari · Lava em 17/10 por volta de 04:37 UTC (log do deploy `0cca1a35`), e
às 04:38 a casa foi recapturada (87 capturadas, 87 à IA: 58 `texto mudou sem cru novo`, 17
`descrição fora`, 12 `termo fora`). As 52 renasceram com ids 388621 a 388672, `origem=extracao`,
moeda vazia (R$). O rastro existe e ficou órfão. Daqui para frente, regravação passa por
`correcoes`: o dicionário (`regravar_mes`) e os scripts de dados já passavam; o UPSERT da Ficha
passa a passar (A3). A lixeira do `DELETE /bilhetes` ficou no BACKLOG (§4.19), por decisão do Feca.

**A1.** As 8 apostas com odd vazia e resultado (4casterss 6, CopaWin 1, SapphireBet 1) ficam como
estão: nenhuma tem odd na fonte e o P/L de todas está certo (L, V, HL). Vão como informação ao Feca.

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
