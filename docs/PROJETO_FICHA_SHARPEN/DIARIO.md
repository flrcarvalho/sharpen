# DIÁRIO · Projeto Ficha Sharpen

> Uma entrada por dia ou por etapa, a mais nova no topo. Todo número com prova. A última entrada diz onde o
> projeto está e qual é a próxima ação.

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
