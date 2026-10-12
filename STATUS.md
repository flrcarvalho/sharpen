# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-10-12 (sessao 411, Projeto Ficha Sharpen D5-D10: **as 8 casas da sombra VIRARAM.** Regras novas do Feca (12/10): toda casa que pode virar vira na hora; o Gabriel e so usuario e nao e criterio de nada; criterio = backtest com o cru que ja chegou, a casa vira se nenhum dinheiro (stake, resultado, retorno) divergir sem explicacao (caem as 30 liquidadas e as 10 ganhas); o historico nao e reescrito pela Ficha (D10) (`docs/PROJETO_FICHA_SHARPEN/03_REGUA_NUMEROS.md §4`). **Dicionario de termos** (`app/dicionario.py`, tabela `dicionario_termos`, `scripts/semear_dicionario.py --aplicar`): semente dos pares cru x `bilhetes` (697) e, no esporte, do texto da `sombra_rotulos`; so o unanime entra; 318 termos. **Virada** traduz esporte e categoria pelo dicionario; termo sem par e codigo que o banco ja tem por outro caminho (D10) ficam com a IA; descricao `<selecao> <linha> <mercado> [jogo]`; coluna `sistema` da Altenar pela Ficha (`3x Duplas`); `tv` inverte a linha com `hisminus` (s392). Gates: `tests/test_virada.py` 20 testes, 15 mutacoes novas + 3 reconferidas, todas detectadas; harness de banco com termo fora do dicionario e D10 (2 mutacoes, detectadas no Postgres local); pytest tests 1863 verde, banco 58 verde. Commit `3660701`, deploy `e073bd36`. **Backtest** (`medicoes/medir_backtest_virada.py`): 0 dinheiro divergente em MyStake 146, DEX 60, Bet Panda 168, Duel 70, Shuffle 80, Vavada 57, BetMartini 97, Megapari 19; ensaio das 628 linhas no `validar_linhas` real, 0 recusadas. **Megapari** (19 crus `x1`, 0.7.52): campos varridos, sombra ligada, 19 Fichas aceitas. **`FICHA_CASAS_VIRADAS=MYSTAKE`** (deploy `6ec6baf8`) e logo depois as oito (`...,DEXSPORT,BETPANDA,DUEL,SHUFFLE,VAVADA,BETMARTINI,MEGAPARI`, deploy `ea08a265`, ~19h40 UTC); `FICHA_SOMBRA_CASAS` + MEGAPARI. A outra sessao publicou a SharpenUp 0.7.52 (s410, dominio novo da Megapari); main puxada antes do commit. **Proximo passo:** conferir no banco a 1a captura de cada casa virada (aposta nova `origem='ficha'`, recusada e D10 pela IA); casas novas quando o cru delas chegar (BACKLOG §1). **2a rodada (noite, pedido do Feca):** D10 = so a LIQUIDADA no banco fica intocada ("nao futricar as apostas de mes passado"); na casa virada a aposta sai da IA na ORIGEM, enquanto aberta: a Ficha grava a aberta, o `/extrair` espera o cru (em voo + folga 1,5 s, teto 8 s), monta a Ficha do cru GUARDADO (a extensao nao reenvia cru igual) e o pre-dedup tira todo codigo resolvido pela Ficha; a IA so recebe recusada, termo fora do dicionario e cru que nao chegou. Tabelas `ficha_virada` e `virada_log`; metrica `medicoes/medir_virada_custo.py`; dicionario aprende sozinho 1x/dia (07h UTC), sem votar na linha da propria Ficha. Mutacoes G-O detectadas; pytest tests 1869 verde, banco 63. Commit `53f4609`. **Ainda valem:** apagar as copias com dado pessoal em 19/10/2026.)

_Anterior: 2026-10-11 (sessao 409, Projeto Ficha Sharpen D0-D1: **o fiscal de odd deixava passar a odd errada quando a diferenca cabia na folga de grafia.** Medicao do pensamento do Sonnet 5 (5 lotes x 6 blocos reais da DEX Sport, harness `docs/PROJETO_FICHA_SHARPEN/medicoes/medir_pensamento.py`): o excesso de escrita E pensamento (11.407 -> 1.545 tok por pedaco sem ele), e sem pensamento a IA gravou `3,9672` (produto das pernas) numa multipla GANHA de stake 40 e retorno 158,80, onde a casa imprime `3,97`. O `_veredito_do_retorno` leu certo o bloco e confirmou o W sem trocar a odd, porque so troca quando a diferenca passa de 0,005 (`app/repository.py:696`); 0,0028 de odd = R$ 0,11 de P/L. Correcao: dentro da folga, em W e HW, a odd da casa entra quando ELA fecha o retorno no centavo e a da linha nao; casa que arredonda a odd na tela fica com a da linha; nenhuma fecha, nada muda. Vale para todos os modelos e casas, sem chave. Gate: 4 testes novos em `tests/test_odd_resultado_determinista.py` (bloco real da DEX), 7 mutacoes, 7 detectadas; pytest tests 1723 verde. Na medicao, refeita sem API: numeros A x B 30 de 30 iguais (eram 29). Bugfix, grupo nao avisado. **Banco (so leitura, `medicoes/medir_furo_folga_odd.py`):** 249 de 9.436 W/HW com bloco cairam no furo, todas de ago/set, R$ 27,94 em modulo, maior R$ 0,80; casas em USDT nao medidas (298 fora, stake do bloco != gravada). Nao serao corrigidas (decisao do Feca, 11/10; item fechado). **Pensamento atras de chave:** `EXTRACAO_SEM_PENSAMENTO` (lista de casas ou `*`; vazia = como sempre), so lote de TEXTO, repassada a todas as chamadas do titular (paralelo, sequencial, repescagens de cobertura e fidelidade) e ao aquecedor de cache (o pensamento entra na chave do cache, medido). Gate `tests/test_extracao_sem_pensamento.py`, 5 mutacoes, 5 detectadas; dubles de `test_cobertura`/`test_fidelidade` aceitam o argumento novo; pytest tests 1732 verde. Chave LIGADA 21:10 para as 15 casas de outubro (deploy `97387a25`). **Decisoes do Feca (11/10):** a Ficha vem ANTES da Fase 2 da blueprint; enquanto o projeto Ficha estiver ativo, so a sessao dele mexe em `app/main.py` e `app/repository.py` (`docs/ESTRUTURA_DO_TIME.md`); casa so vira com 30 apostas LIQUIDADAS comparadas. **Fiscal le `Retorno:` em linha propria** (1xBet, Altenar, Novibet, Bolsa de Aposta e outras: antes o gate nunca rodava nelas, 0 de 40 blocos ganhos na Megapari e na BetMartini); `Retorno potencial:` e linha recuada nao casam; replay em 1.588 resolvidas: 21 mudariam, nenhuma das casas do projeto (Lottu 6 com odd que nao fechava o retorno). As 8 casas 1xBet/Altenar sairam da chave as 21:59; as 7 que ficam tem o retorno achado em 213 de 213 ganhas. **Aquecedor** aquece as duas versoes (com e sem pensamento) quando a chave nao esta vazia. Gate: 7 testes novos, 6 mutacoes, 6 detectadas; pytest tests 1739 verde. **Regra da odd aprovada** (Ficha §3, daqui para frente). **Rota da Ficha em modo sombra no ar, DESLIGADA** (`FICHA_SOMBRA_CASAS` vazia): `app/ficha.py` (`POST /captura/ficha`, validar/derivar/gravar), tabela `ficha_sombra` (aceita e RECUSADA com motivo; nao toca `bilhetes`), casa e conta da SESSAO de captura; no `main.py` so o registro. Gate `tests/test_ficha.py` 28 testes, 11 mutacoes, 11 detectadas, 1 inocua; INSERT no harness de DB. Lottu e folga 0,5%/Novibet adiados (BACKLOG 3.21). **Desenho mudou (Feca):** a extensao manda o JSON CRU de todas as casas que escuta (uma atualizacao so) e o SERVIDOR monta a Ficha, adaptador por familia em Python (`app/adaptadores/`, DEX feito, bate com o gabarito lido na tela); filtro por NOME EXATO (`app/cru.py`); tabela `captura_crua` guarda o cru de todas as casas; 409 final para cru de outro site. Teste obrigatorio: Ficha do cru filtrado = sem filtro em toda fixture com adaptador. 11 mutacoes, 11 detectadas; pytest tests 1786 verde. **CI verde de novo** (`0f09b63`): resolvedor da Bet365 isolado como falha CONHECIDA (so falha em UTC), BACKLOG 4.16. **Atualizacao unica do SharpenUp pronta na branch `sharpenup-cru` (`e919499`, SEM push; worktree `../Planilhador-sharpenup-cru`)**: as 22 casas mandam o cru num campo novo da mesma mensagem, o texto nao muda (fotografia do harness, 2.231 registros, diferenca zero; cru quebrado, texto identico, no CI da branch). A `main` NAO recebe a extensao ate o Feca testar: o `/extensao/download` empacota a `extensor/` da main na hora. Pacote 0.7.50 guardado em `Backups/sharpenup_0.7.50_antes_do_cru/`. Desenho da virada (recusada volta ao texto/IA) em `docs/PROJETO_FICHA_SHARPEN/03_REGUA_NUMEROS.md §7`. **Teste real do Feca (12/10, ~04h UTC), condicao (c) cumprida:** 6 casas, 5 familias (Betpanda 167, MyStake 137, Shuffle 72, Duel 65, DEX 55, Vavada 49): 545 crus, 545 batem com bilhetes na mesma conta, filtro removeu 0, texto como sempre. Shuffle e Duel nao mandaram o cru na 1a vez: a aba estava aberta antes da troca da extensao (o Chrome nao injeta em aba ja aberta); com F5 chegou. Nao e defeito; o aviso aos testers diz "recarregue a pagina da casa (F5)". **Publicada em silencio (12/10, decisao do Feca):** `sharpenup-cru` juntada na main, SharpenUp **0.7.51** (declarada em `sharpenup_sem_nota`, sem `avisar_testers.py`, grupo nao avisado), CI verde, deploy `ac4526ac`, pacote do `/extensao/download` conferido = 0.7.51 com `cru.js`. Falta o Feca instalar na maquina dele e na do Gabriel, com F5 nas abas das casas. **Rota endurecida (deploy so de servidor):** erro QUALQUER do adaptador vira Ficha recusada `erro do adaptador: ...` (antes: 500 depois do `gravar_cru`, e o reenvio caia em "cru igual" sem Ficha); com `CRU_CAPTURA_DESLIGADA` a rota responde 503 (a extensao so marca enviado no 200). Script `scripts/reprocessar_ficha_cru.py --casa X [--aplicar]` monta a Ficha do cru que nao tem nenhuma (idempotente por `cru_id`); ensaio DEX: 55 crus, 55 aceitas. Gate: 3 testes novos em `tests/test_ficha.py`, 3 mutacoes, 3 detectadas; pytest tests 1789 verde. **`FICHA_SOMBRA_CASAS=DEXSPORT` ligada** (12/10 ~04h56 UTC, deploy `be647434`); reprocesso `--aplicar`: 55 Fichas gravadas; banco: 55 crus da DEX, 55 com Ficha (todas aceitas), 0 sem. Cru NOVO da DEX ainda nao chegou depois da chave: conferir na proxima captura. **Adaptadores jb (Betpanda, Duel), shf, tv (MyStake) e vb (Vavada) na main** (merge `e616838`, CI verde, deploy `a70353a6`), medidos offline contra a IA (`docs/PROJETO_FICHA_SHARPEN/medicoes/REGUA_ADAPTADORES_s409.md`). Correcoes do Feca (12/10) junto: sistema ganho = retorno / stake (`MASTER_RESULTADO 7.1`; o `derivar` lancava +650,77 USDT em 4 bilhetes, a IA estava certa); Shuffle aceita MENOS que o pedido (stake = `amount` aceito, `originalAmount` so como `stake_pedida`; nao era venda parcial, a IA estava certa); filtro do servidor tira `Player` (MyStake, login da conta) e `nickname` (DEX), so no servidor, e o teste exige que a lista do servidor CONTENHA a da extensao. Gates: 12 + 9 mutacoes, todas detectadas; pytest tests 1809 verde. 192 crus limpos com hash recalculado (`scripts/limpar_cru_filtro.py`, copia em `captura_crua_copia_filtro` e `ficha_sombra_copia_filtro`). Varredura de nomes de campo das 5 familias antes de ligar: nada mais de pessoa. **`FICHA_SOMBRA_CASAS=DEXSPORT,BETPANDA,DUEL,MYSTAKE,SHUFFLE,VAVADA`** (deploy `a74bb4ad`, ~14h19 UTC); reprocesso: 559 crus, 559 com Ficha, 0 recusadas. Regua na 2a rodada: 481 batem, 78 so na odd sem dinheiro, 0 divergem. **Copias com dado pessoal: APAGAR EM 19/10/2026** (decisao do Feca, 12/10): `captura_crua_copia_filtro` (192 linhas, todas com `Player` ou `nickname`) e `ficha_sombra_copia_filtro` (55) ficam ate 19/10 como seguro; nessa data, se nada tiver dado errado, `DROP TABLE` nas duas (BACKLOG secao 1). **Regua com liquidadas comparadas por casa e por dono** (D12: 30 por casa, aberta nao conta; harness `medir_regua_adaptadores.py`, conferido por SELECT): Feca Bet Panda 163, Duel 60, DEX 52, MyStake 135, Shuffle 63, Vavada 45, 0 divergem; Gabriel 0 em todas (sem cru ainda). Todas da varredura de historico de 12/10. Atingir 30 nao vira a casa: so com o "pode" do Feca. **Caminho normal provado** (Feca, 16h40 UTC: 133 crus novos, 133 Fichas aceitas pela rota); Gabriel ainda nao instalou. **Fiscal provado em 6 das 8 casas 1xBet/Altenar** (`medicoes/medir_fiscal_acha_retorno.py`: Megapari 36/36, SapphireBet 13/13, PariPesa 4/4, BetMartini 26/26, Vavada 10/10, Betrebels 18/20, as 2 com bloco aberto e W manual): as 6 entraram em `EXTRACAO_SEM_PENSAMENTO` (deploy `3b1854f1`); 1xBit e Kikobet fora, sem ganha com bloco. **BetMartini na sombra** (`FICHA_SOMBRA_CASAS` + BETMARTINI): campos varridos; `vb` corrigido (sistema nao combina pernas do mesmo jogo; sistema ganho abaixo da stake = W), 97 Fichas aceitas; o R16 (6,02 x 14,25) e sistema 2 de 3, odd = media das duplas, e o texto da extensao escreve sistema como Multipla (BACKLOG). **Regua:** coluna de ganhas e so o cru mais recente por aposta; 678 apostas, 0 divergem, 0 recusadas; todas com 30+ liquidadas e 10+ ganhas (so Feca). Proposta ao Feca: 10 ganhas alem das 30 liquidadas (`03_REGUA_NUMEROS §4`). **Virada do §7 no ar, DESLIGADA** (`app/virada.py`, `FICHA_CASAS_VIRADAS` vazia; o corpo do `/salvar` virou `main.gravar_tsv`): aceita grava pela Ficha (`origem='ficha'`), recusada, sem cru e aberta vao pela IA; teste dos 3 bilhetes em Postgres real (local), 9 mutacoes, 9 detectadas. **Adaptador `x1`** (1xBet e espelhos) das fixtures, 6 mutacoes, 6 detectadas, nao ligado. pytest tests 1831 verde. **Proximo passo:** Gabriel na 0.7.51 e regua no dia do cru dele (inclusive `x1`); o "pode" de cada virada (candidatas DEX e MyStake), com o dicionario de esporte/categoria antes (BACKLOG §1). A Fase 2 da blueprint fica para depois.)

_Anterior: 2026-10-11 (sessao 405, continuacao: **a regra de data da multipla perdida foi corrigida depois da auditoria independente.** A auditoria cega (pedido do Feca) confirmou a sidebar ao centavo (Feca -14.228,05, Gabriel +8.884,86 em 11/10) e achou dois defeitos ja no ar em `repository.data_da_perna_perdida`: redatava aposta de SISTEMA (Duel 378272, sistema 2/3, ia de 10/10 para 08/10; 10 no ensaio) e lia `sel_status=4` como perdida tambem na Stake, onde e anulada (a fixture "Pitaco" do teste era formato Stake). Correcao: sistema fica fora (`Tipo: Sistema`, `type=SYSTEM_BET`, `BetTypeName=Sistema` no cabecalho), `sel_status` lido por casa pelo `Status (API):` (Pitaco 4, Stake 3), KTO `[LOST]` entrou (Novibet nao: perna sem `Inicio:`, 0 de 2.914), `MASTER_OUTPUT §4.0.1` diz sistema fora, Stake 4 = anulada, Bet365 fora (decisao do Feca 11/10) e dia do INICIO mesmo com `Liquidado em` (proposta aprovada). Script `reparar_data_multipla_s405.py` numa transacao so, snapshot gravado antes do 1o UPDATE, e importavel pelo teste. Gate: `tests/test_data_multipla_perdida.py` com blocos reais da sombra (19 testes); 16 mutacoes novas, 14 detectadas, 2 inocuas registradas no cabecalho; pytest inteiro verde (1719). Ensaio: 271 linhas a redatar (eram 281), 1 pulada por edicao manual. Bugfix, grupo nao avisado. **NAO aplicado:** o script so roda com o "pode aplicar" do Feca. **Em aberto (BACKLOG 1.17):** orfa com data mudada (medir), `Liquidado em` para cashout, grupo B, Bet365, grupo C.)


> **Histórico completo das sessões 332 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 342)

> **Sessão longa, de custo e do tradutor.** O registro durável está nos planos; isto aqui
> é o mapa para retomar.

### O que entrou no ar hoje

| | Onde está |
|---|---|
| Estudo de custo **remedido** | [`ESTUDO_PRECIFICACAO_2026 §7`](docs/ESTUDO_PRECIFICACAO_2026.md) |
| **Barreira de recaptura**, Fases 0 e 1 | [`PLANO_BARREIRA_RECAPTURA.md`](docs/PLANO_BARREIRA_RECAPTURA.md) (novo) |
| O gate do tradutor **trocado** | [`PLANO_TRADUTOR §II.9`](docs/PLANO_TRADUTOR_DETERMINISTICO.md) |
| Decisões **A e B** do Feca, aplicadas | `MASTER_DESCRICAO §10.1` e **§10.1.1** · `MASTER_OUTPUT §19` |

### O achado que reorganiza a frente

**Em 76,7% das releituras a IA descreveu de forma diferente algo que ela mesma já tinha
descrito.** No maior mercado da base a mesma seleção saiu de **doze** jeitos. O teto de
acerto de qualquer tradutor determinístico contra esse juiz é **~23%**.

E a causa não é a casa (a entrada é byte a byte idêntica) nem só o buraco do MASTER. A
instabilidade segue **quantas decisões o modelo precisa tomar para montar a frase**:

| A descrição exige | Instável |
|---|---|
| Copiar um nome | 18% |
| Montar com linha meia (**tem** template) | 42% |
| Montar com linha partida (sem template) | **100%** |

> **Descrição montada por modelo estocástico não converge para um formato só, por melhor
> que fique o MASTER.** Só compor em código elimina. O tradutor ganhou com isso uma
> segunda justificativa que não depende do preço da API: **ele é o que dá formato único
> ao dado.**

### Onde o tradutor está

| | |
|---|---|
| Cobertura na Bet365 | **68,0%** (7.606 de 11.186) |
| **Conformidade com o MASTER** | **100,0%** contra 67,1% da IA |
| Maior buraco de cobertura | `mercado desconhecido`, 1.644 bilhetes |

### O PRÓXIMO PASSO, concreto

**Ampliar o mapa com a régua nova.** Ela mudou o jogo: rótulo que eu rejeitei na s334 por
"divergir 98% da IA" pode estar certo. Já reavaliei os 10 podados e **dois voltaram**
(`total de pontos`, `corrida - handicap`); os outros quatro têm agora motivo nomeado no
próprio `app/tradutor.py`, logo abaixo do mapa. Falta rodar a mesma reavaliação nos
**1.644 bilhetes de `mercado desconhecido`**, que é onde está o volume.

O script que produz a lista de trabalho está descrito no `PLANO_TRADUTOR §II.8`; ele
casa cada rótulo desconhecido com a maioria da IA e a frequência.

### O que depende do Feca

`BACKLOG §3.8`, decisões **C** (prop de SIM/NÃO, ~100 leituras) e **D** (escopo de tempo,
~60). São pequenas perto das ~5.700 que A e B resolveram, mas destravam quatro rótulos
que hoje estão de fora com motivo escrito.

### Três hipóteses de custo que MORRERAM medidas

Estão no `BACKLOG §3.10`, e valem por poupar a próxima sessão de tentar de novo: aparato
editorial no prompt (**US$ 0,76/mês**), fatiar esportes por casa (**US$ 7,30**), e cortar
o preâmbulo do output (**o modelo não aceita prefill de assistente**; sobra US$ 9/mês pelo
`stop_sequences`). **Os masters estão densos, não inchados.**

### Duas coisas que não são minhas e ficaram vermelhas

- **`CLAUDE.md` está em 65,4 KB, acima do teto de 65.** Veio commitado em `db5b77c` /
  `cea574b`. Pela regra do próprio arquivo, o conserto é mover **caso** para o
  `docs/CASOS.md`, nunca subir o teto.
- **`test_changelog` com 3 falhas:** o `extensor/manifest.json` está numa versão sem nota
  de changelog. Resolve rodando o `scripts/avisar_testers.py`.

---

## Sessão 344 — as 298 de 2025 saíram, e o que impede elas de voltarem

### O que estava errado

A 1ª captura da Betbra (s343) gravou **411 bilhetes de uma vez**, e **298 eram de 2025**
(01/06 a 31/10). A Betbra é a **única** casa deste dono com bilhete daquele ano: toda a
base dele começa em 2026. A exportação da casa trouxe o histórico inteiro junto.

### A metade que faltava: apagar não bastava

`extensor/bda_inject.js` varre **3 anos** por desenho (`DIAS_HISTORICO = 1095`), e o
`lookbackDias` do painel só é respeitado quando pede **mais**. Isso é deliberado desde a
s299, quando a janela curta fez o robô trazer 21 de 418 bilhetes da Bolsa.

Consequência: a próxima captura reencontra os mesmos 298 códigos e regrava tudo, sem erro
nenhum. **Exclusão sem corte dura até a varredura seguinte**, que é a mesma família do
"volta pela CASA, nunca pelo banco". E não havia nada no sistema segurando isso:
`lixeira_bilhetes` é snapshot de reparo, ninguém a consulta no `/salvar`.

### Onde o corte ficou, e por quê

No **`/extrair`**, não na extensão. Dois motivos:

| | |
|---|---|
| O inject é **compartilhado** com a Bolsa de Aposta e vale para todo dono | encurtar o horizonte lá quebraria a casa que ele existe para proteger |
| Aqui a régua é por **(dono, casa)** e roda **antes da IA** | o bloco cortado não paga leitura, não vira TSV e não chega ao `/salvar` |

Régua em `main._CORTE_HISTORICO`, um mapa de par exato: **Feca × Betbra, nada anterior a
01/01/2026**. Casa nenhuma entra ali sem decisão escrita.

Três decisões de leitura, todas com gate próprio:

- A data que manda é a do **EVENTO**, a mesma que decide a coluna Data. Ler a colocação
  cortaria aposta feita em dezembro para jogo de janeiro.
- Bloco **sem data legível FICA** (fail-open). Esconder bilhete é o modo de falha caro,
  porque ninguém reclama do que não apareceu; um a mais para a IA é o que a barreira de
  recaptura já devolve.
- A contagem tem **balde próprio** na tela (`fora_corte`), nunca somada em `xls_skipped`:
  "já salva" afirma que existe uma linha no banco, e esta nunca existiu.

### O que saiu da base

Aplicado **depois** de conferir o deploy no ar (o `/static/index.html` de produção já
servia o campo novo), por `scripts/excluir_historico_fora_do_corte.py`, que lê a régua do
próprio `_CORTE_HISTORICO` em vez de repetir a data.

| | |
|---|---|
| Movidas para `lixeira_bilhetes` | **298**, motivo nomeado, snapshot JSONB |
| Saiu da base | R$ 10.125,25 de turnover · **+R$ 5.262,25 de P/L** |
| Restam na Betbra do Feca | **113**, todas de 2026 |
| Bilhete de 2025 em qualquer casa dele | **zero** |
| Contas dos outros 4 donos na Betbra | intactas |

### Gates

`tests/test_corte_historico.py`: 16 casos sobre blocos **reais** da `sombra_rotulos`,
**6 de 7 mutações detectadas**. A 7ª é inócua (o log some) e está registrada como tal.

A mutação nº 5 é a que interessa: **a chamada removida da rota**. Sem ela o corte fica
verde e inútil, que é como uma regra sem gate morre neste repo.

863 passed / 36 skipped · `check-tokens` verde · `index.html` renderizado headless sem
erro de script.

### Pendente

**Validar ao vivo:** recapturar a Betbra e conferir que as 298 não voltam. É o único teste
que fecha isto, porque o gate lê o fonte da rota, não a executa ponta a ponta.

> **Duas sessões no mesmo `index.html`.** O 1º commit levou junto o selo de captura que a
> outra sessão estava escrevendo no arquivo. Corrigido **antes do push**: o blob do índice
> foi trocado por uma versão com só os meus hunks, e o trabalho dela seguiu intacto no
> working copy. O `git show --stat` é o que acusa isso, e ele só serve se for lido.

---

## Sessão 343 — Betbra: a casa espelho e o cupom que virava múltipla falsa

### A casa

A **Betbra** entrou na captura como **casa espelho da Bolsa de Aposta** — é a mesma
plataforma com outra marca. Medido no navegador, lendo o `src` real dos dois iframes:
rotas de casca idênticas (`/b/exchange` · `/fbook`), Exchange LayBack em
`mexchange.betbra.bet.br` (cookie, 0 parâmetros) e Sportsbook msjxk em
`prod20454-176166310.msjxk.com` (`operatorToken` na URL). **Zero inject novo, zero
formatador novo:** os dois já derivavam o endereço de `location`.

**O único bloqueio real era o `match` do manifest**, preso em `*.bolsadeaposta.bet.br` —
o `bda_inject` nunca subiria em `mexchange.betbra.bet.br`. O Sportsbook já vinha coberto
pelo curinga `*://*.msjxk.com/*`.

Volume: **403 ofertas no Exchange** (mai/2025 → set/2026, varridas em 29 chamadas com zero
erro) e 7 liquidadas + 3 abertas no Sportsbook.

### O achado: `Selections` não é a lista do que foi apostado

No Criador de Apostas (bet builder) o Sportsbook manda, dentro do MESMO array: as **pernas
soltas**, cada uma com a odd de mercado dela — que não foi apostada —, e uma entrada
**agregada** do cupom (`MarketTypeId: "QA0"`), com a odd do conjunto e os textos das pernas
concatenados por ` | `. Quem diz o que entrou é **`MappedSelections`**, uma lista de índices.

O código lia todas. Uma aposta de **4,61** virava uma múltipla de **26,72** (1,13 × 2,30 ×
2,23 × 4,61) — **sem erro nenhum, e com o P/L continuando certo**, porque a odd do bilhete
vem de outro campo. Errariam só turnover, ROI e a assinatura de stake do matcher. Mesma
família de "a stake que era do vizinho, com o P/L intacto" (s311).

Medido em **10 de 10** bilhetes: a odd bate com o produto das *mapped* em 10/10 e com o
produto de todas em **0/10**.

> **O defeito atravessou o recon da Bolsa sem aparecer.** Lá `MappedSelections` é sempre
> `[0]` com uma seleção só: as duas leituras coincidem. O caso da Bolsa fica **verde com ou
> sem a correção** — falso verde do tipo 2 do `CLAUDE.md` ("o dado sintético não exerce a
> regra"), e está escrito no cabeçalho dos dois arquivos.

**Decisões de formato**, todas contra a tela: a ordem das pernas vem do **texto agregado**
(o array traz outra ordem — o `SelectionId` da agregada é `0VS0|2|1`); a perna de um cupom
**não tem odd própria** no bloco (publicá-la seria oferecer à IA um número que parece conta
feita e não é); e o tipo virou `Criador de Apostas (bet builder — N seleções do MESMO jogo,
odd única do cupom)`, nunca "Múltipla", que mentiria em três frentes.

### O boost, que a Bolsa tinha como "não confirmado"

`ClientOdds` é a odd **com** boost e `DbTrueOdds` da agregada é a **sem**. A tela risca a
segunda e estampa a primeira (`2.89 → 3.36`). A odd que vale é a `ClientOdds` do bilhete —
200 × 3,36 = 672 = "Retorno Total" da tela. A regra global de W (`retorno ÷ stake`) absorve
o boost sozinha; o percentual **não** se deduz do `Campaigns[].Type` (1,32 e 1,16 medidos em
tipos diferentes).

### Gates

| | |
|---|---|
| Harness | **28 casos, 447 bilhetes** — verde |
| Mutação | **5 de 5 detectadas** pelo caso Betbra · **0 de 5** pelo caso Bolsa |
| `audit_sharpenup` / `audit_casas` / `audit_changelog` | sem FAIL |
| `pytest` | 826 passed / 36 skipped |
| Manifest | 0.7.10 → **0.7.11**, aviso publicado no grupo (`message_id 3380`) |

As 5 mutações confirmam por medição o que o cabeçalho do caso dizia por dedução: **a fixture
da Bolsa não protege esta regra.** Sem o caso da Betbra, a correção teria entrado parecendo
coberta.

### Duas coisas medidas antes de registrar

**A grafia.** `_CASA_DISPLAY` é retroativo, e o código já tinha duas grafias divergentes
(`import_arrudex_xlsx.py` grava `Betbra`, `import_dashboard_xlsx.py` grava `BetBra`). No
banco só existe **`Betbra`**, em todas as cinco tabelas onde `casa` é texto: 5 contas, 158
bilhetes, 1 em `casas_meta`, 23 em `correcoes`, 1 em `uso_tokens`. A decisão do Feca
("Betbra para todos") confirmou a base.

**As séries de código são por CASA, não por plataforma.** Exchange da Betbra: 7–8 dígitos.
Exchange da Bolsa: 9. Mesma plataforma, contadores independentes — **comprimento de código
não diz de que casa o bilhete é**.

### Pendente

**Validação ao vivo**, que não fecha sem o operador: recarregar a extensão, **Ctrl+Shift+R
na aba da Betbra** (recarregar a extensão não re-injeta em aba já aberta) e **F5 no
dashboard** (a casa nova não aparece no seletor numa aba que já estava aberta).

**Sem cobertura automatizada no harness, e portanto ainda dependentes de teste ao vivo:**
`SUPERBET` e `BETESPORTE` — nenhuma das duas tocada por este diff.

**Não provado nesta casa** (medido, não suposto): `lay` (403 de 403 são `back`),
cashout/Retirada, freebet, `push_win`/`push_lose`, casamento parcial no Exchange, e
`MappedSelections` com 2+ índices (múltipla de eventos diferentes).

---

---

## 1. O que estamos construindo

A base de conhecimento (masters) do scanner de bets. Camada **global** (regra única, muda devagar) + camada **por casa** (traduz cada casa para a língua global). A saída final é **TSV**.

---

## 2. Invariantes (não se quebram)

1. O app **lê** os masters, **nunca escreve** neles. Mudança de regra = diff revisado por humano + commit. Git é a porta de aprovação.
2. O arquivo de casa **traduz** a casa para a língua global; **não redefine** regra global.
3. **Cálculo é global, localização é da casa.** Ex.: "W → Retorno÷Stake" é global; "o retorno está no campo PRÊMIO" é da Superbet.
4. Nenhuma regra nova é aplicada sozinha. Propor como diff, esperar aprovação.

---

## 3. Estrutura-alvo do repo

```
/global/                 (autoridade única — 6 masters)
    MASTER_PIPELINE_2026.md
    MASTER_ESPORTES_2026.md
    MASTER_APOSTAS_2026.md
    MASTER_DESCRICAO_2026.md
    MASTER_RESULTADO_2026.md
    MASTER_OUTPUT_2026.md
/casas/                  (1 arquivo por casa — traduz, nunca redefine)
    CASA_MODELO.md         (gabarito — 15 seções)
    CASA_BET365.md
    CASA_BETANO.md
    CASA_BETESPORTE.md
    CASA_BETFAIR.md
    CASA_BETNACIONAL.md
    CASA_BOLSADEAPOSTA.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_NOVIBET.md        (plataforma própria BlueBrown — replay que ALARGA o filtro)
    CASA_PINNACLE.md
    CASA_PITACO.md         (ex-"Rei do Pitaco" — gRPC-Web/protobuf; 2 grafias, 1 manual)
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_JONBET.md
    CASA_BETBOOM.md        (espelho técnico da Jonbet — mesmo motor BetBy/sptpub)
    CASA_VAIDEBET.md
    CASA_ESPORTIVA.md      (espelho técnico da VaideBet — mesmo motor Altenar/BIA)
    CASA_JOGODEOURO.md     (3ª casa Altenar — captura na TELA CHEIA do histórico)
    CASA_BETPIX365.md      (4ª casa Altenar — a casa NÃO chama o endpoint que ela precisa)
    CASA_ESTRELABET.md     (5ª casa Altenar — a mais lisa na tela; o gateway recusa credencial)
    CASA_STAKE.md          (mesma Kambi da KTO, mas REST próprio — captura NÃO é espelho)
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (guias, referências, ADRs, planos VIVOS — índice em docs/README.md)
    CASOS.md               (os casos que originaram as regras do CLAUDE.md; não auto-carregado)
    HISTORICO.md           (índice) → historico/  (6 partições por faixa de sessão)
    arquivo/               (o que virou registro; índice em arquivo/README.md)
CLAUDE.md                  (regras vinculantes)
STATUS.md                  (este arquivo — estado atual + as 3 últimas sessões)
BACKLOG.md                 (tudo que está aberto)
```

**Um arquivo, uma pergunta** (invariante #10), com gate em `python tools/check_docs.py`.

Os 6 MASTER_*.md vivem em `/global/`; as **28** casas em `/casas/` (Polymarket por API, as demais por IA/texto), mais o gabarito `CASA_MODELO.md`.

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Identidade na tabela `usuarios` do Postgres via cache em memória (s233 — Fase 1 do `docs/PLANO_MULTIUSUARIO_2026.md`); os dicts de `app/auth.py` são a SEMENTE. Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway (o seed leva ao banco no boot); base nasce vazia sem migration. Suspender no banco (`status`) revoga login E sessão em ≤60s.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Base do `LavaPessoal` (s222):** 2.877 apostas importadas do `.xlsx` pessoal do Lava (23/02 → 30/07/2026), `origem='import'`, conta `Padrão` em cada uma das 19 casas (ele não anota fornecedor). Script próprio e idempotente: `scripts/import_lavapessoal_xlsx.py` (re-rodar limpa só `origem='import'` daquele dono; captura da extensão sobrevive). **Não confundir com o dono `Lava`** — são bases distintas que só compartilham o apelido. **O P/L do dashboard não bate com a planilha de origem por desenho** (ela contabiliza em unidade; ver s222 no topo).
- **Base do `SoChutes` (s224):** 23.199 apostas all-time do tipster Só Chutes (17/09/2024 → 27/07/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` (Bet365/Superbet/Betano; casa não informada entrou como Bet365 — decisão do Feca). **Stake em UNIDADES** (1u = 1; o P/L do dashboard é o P/L em unidades: +1.381,29u). Script idempotente: `scripts/import_sochutes_xlsx.py`. O planilhamento novo é do **bot Sharpen** (repo próprio `BOTS/sharpen-bot`, ver s223), que desde a **s251** roda 24/7 no Railway — serviço `sharpen-bot`, no mesmo projeto do app, com o estado em volume próprio. Ele escreve nesta base por `/salvar` + `/bilhetes/tipster`: **mudança no contrato dessas rotas quebra o bot em silêncio.**
- **Base do `Flurray` / tipster Fleury (s260):** 473 apostas (11/06 → 09/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 4 casas (Bet365, Betano, Superbet, BetMGM). Base de **nicho**: 100 % mercados de finalização no futebol. **Stake em UNIDADES** (1u = 1; P/L +122,30u sobre 447,80u de turnover). Script idempotente: `scripts/import_fleury_xlsx.py`. **⚠️ A marca é `Fleury` e o username é `Flurray`** — o `dono` é sempre o username; a ponte entre os dois é o `TIPSTERS_PUBLICOS`. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/fleury`** (3ª do sistema).
- **Base do `passapano` / tipster PassaTips VIP (s273):** 911 apostas (02/06 → 17/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 7 casas (Bet365, Betano, Betnacional, Betvip, Estrela Bet, Novibet, Suprema Bet). Base **multiesporte**: 20 esportes, de futebol e tênis a polo aquático e críquete. **Stake em UNIDADES** (1u = 1; P/L +90,20u sobre 1.102,61u de turnover liquidado). Script idempotente: `scripts/import_passatips_xlsx.py`. **⚠️ A marca é `PassaTips VIP` e o username é `passapano`** — mesmo caso do Fleury. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/passatipsvip`** (5ª do sistema). O planilhamento novo é do **bot Sharpen** (4º tenant, `passatips`) — **1º perfil sem visão**, porque a legenda dele já traz tudo.
- **Casas:** 28 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **25 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210), **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`), BetNacional, Jonbet (BetBy/sptpub, s248), **Betboom** (s250 — **espelho da Jonbet**: mesmo motor BetBy, mesmo `jb_inject.js`) **Pitaco** (s270 — plataforma própria, **gRPC-Web/protobuf binário**, replay puro) **Novibet** (s271 — plataforma própria BlueBrown, replay puro que **alarga o filtro** da tela: ela pede 24 h e só as fechadas) e **Estrela Bet** (s303 — **5ª casa Altenar**, mesmo `vb_inject.js`; a mais lisa na TELA e a única cujo gateway **recusa `credentials:"include"`**). **Dois pares de espelho, zero código duplicado** — o inject casa por caminho de API, nunca por host, e é isso que faz a casa seguinte da mesma plataforma custar registro em vez de implementação.
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências

> **As pendências mudaram de casa.** Elas moram em **[`BACKLOG.md`](BACKLOG.md)**, na raiz —
> organizadas por natureza (bloqueado por humano · por amostra · decisão do Feca · dívida
> técnica medida · planos com fase aberta · não medido), com as marcas
> **VIVA / NÃO-MEDIDA / HUMANA** da varredura da s261 preservadas.
>
> Motivo: o §5 tinha **51 KB** e ficava atrás de 124 KB de changelog. Quatro arquivos
> disputavam o papel de "onde o projeto está" e três descreviam o projeto de julho. Ver
> [`docs/FAXINA_PROPOSTA.md`](docs/FAXINA_PROPOSTA.md).
>
> **Pendência nova vai para o `BACKLOG.md`, nunca para cá** (invariante #10 do `CLAUDE.md`).
> Gate: `python tools/check_docs.py`.

As três mais quentes de hoje, com o resto no `BACKLOG.md`:

1. **`apps_script/Code_LavaFatuch.gs` expõe a base do Fatuch sem autenticação nenhuma.**
   `doGet(e)` na linha 95, zero token ou segredo no arquivo — e é a fronteira que alimenta o
   `app/planilha_viva.py`, a base financeira **ao vivo** de um cliente. Qualquer um com a URL
   lê. Medido em 06/09. → `BACKLOG §4.3`, e é sessão própria.

2. **PassaTips: 3 passos humanos para fechar o buraco do #259, e a ORDEM importa.**
   Enquanto o painel do #259 estiver armado, um clique ✅ vira o `L` do dia 17 em `W`
   (`resultado` não é congelado). O `/anular #259` **apaga** a linha `Under 1.5 cartões
   Elche`, então o tipster tem de repostar **antes**. → `BACKLOG §1`.

3. **Polymarket ainda mistura `entry_odd` e `realized_odd`** (`AUDITORIA_2026 #32`).
   `_calc_odd` (`app/polymarket.py:894`) devolve um número só, e o próprio comentário da
   `:987` admite "odd de entrada, **ou** a efetiva na liquidação". É o maior risco quant
   aberto e mexe em P/L. → `BACKLOG §4.1`.

---

## 6. Rodar / produção

**App em produção:** `https://sharpen.bet/` (www.sharpen.bet → Railway)

Para rodar localmente:
```
cd app
pip install -r requirements.txt
# .env na raiz do Planilhador com ANTHROPIC_API_KEY e DATABASE_URL
uvicorn main:app --reload
# Abrir http://localhost:8000
```

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/sharpen`, renomeado de `extrator` na sessão 129). Deploy automático via Railway conectado ao GitHub — push dispara deploy.
