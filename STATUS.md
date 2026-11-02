# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-11-01 (sessao 439: **Kalshi construida: chave cifrada, Sincronizar, painel com passo a passo e Caixa automatica (etapas 2 a 4 do BACKLOG 4.0w).** Pedido do Feca ("pode finalizar a construcao"), com aval para o `include_router` no `main.py`. Tudo mora em `app/kalshi_rotas.py`: `GET/POST/DELETE /kalshi/chave` e `POST /kalshi/sync` (`ensaio: true` le sem gravar). A chave privada fica em `kalshi_chave` (uma por conta, CASCADE), cifrada com Fernet pelo segredo `KALSHI_CHAVE_CIFRA` (env var, nunca o banco), e nunca volta a tela: o GET devolve so os 8 primeiros caracteres do ID. O POST confere na Kalshi que a chave autentica e e so leitura ANTES de gravar. Sync grava com `origem='sync'`, passa a conta a USD e confere a Caixa (`caixa_kalshi_sync`, o molde da Polymarket sem a trava da blockchain); depositos e saques pelo formato medido no recon (`amount_cents` inteiro, `created_ts`, data de Brasilia), e formato nao medido nao vira chute: a Caixa nao atualiza e o sync avisa. Tela: bloco `Conta Kalshi` no lugar do upload (Conectar chave, Sincronizar, auto-sync ao entrar e ao voltar a aba pela marca `ultimo_sync` do servidor), modal com os rotulos da tela da Kalshi (sem os prints, que mostram a chave do Feca) e a Caixa automatica da Polymarket estendida a Kalshi. Gates: `test_kalshi_rotas.py` (25) e `test_caixa_kalshi_golden_confere_e_nao_duplica` (Postgres local, 95 verdes); mutacoes 11 de 11 (a do fuso escapou na 1a rodada, porque o deposito real cai as 15:27 de Brasilia, e ganhou caso que cruza a meia-noite); pytest puro 2121, so o `test_recorte_custos` de sempre; check-tokens verde; render headless do fluxo inteiro (sem chave, chave de escrita recusada no modal, modal preenchido nao fecha no fundo, conectada, auto-sync, troca de casa). Backup em `Backups/s439_kalshi_sync_painel_caixa/`. `KALSHI_CHAVE_CIFRA` criada na Railway pelo Feca (o modo automatico barra escrever segredo). 1a sincronizacao na conta do Feca feita e conferida por ele na tela (aposta e Caixa). **Proximo passo:** o Feca apaga a chave do recon na Kalshi e conecta uma nova; conferir a 1a W, o 1o saque e a tolerancia da Caixa com mais apostas (BACKLOG 4.0w))

_Anterior: 2026-11-01 (sessao 438: **Extra da consultoria 022: `lock_timeout` no DDL do startup e healthcheck na Railway** (queda de 25/10). `init_db` roda o SCHEMA_SQL numa transacao com `SET LOCAL lock_timeout = '5s'`, 6 tentativas com 10 s de pausa; esgotadas, o boot falha e o deploy anterior segue no ar. `railway.toml`: `healthcheckPath = "/healthz"`, `healthcheckTimeout = 300` (cobre o pior caso de 90 s). Limite escrito no codigo: o backfill de `adquirida_em` (`DO ... EXCEPTION`) engole o estouro como WARNING e roda no boot seguinte. Gates: 3 testes de lock no Postgres local (`test_repository_db.py`, 94 verdes) e `test_deploy_config.py`; mutacoes 5 de 6 detectadas, a 6a (`SET` no lugar de `SET LOCAL`) e INOCUA: o pool do asyncpg roda `RESET ALL` ao devolver a conexao. Pytest puro 2097 verdes, `test_recorte_custos` falha igual na main limpa (s437). Backup em `Backups/s438_extra_lock_timeout_healthcheck/`. **Fase 0 da 022 (so leitura):** das 7 "sem linha", 6 sao Stake.com do Feca, gravadas sob a grafia com ponto (nao perdidas); PERDIDAS de fato: 1win 338677290 do Jaao26 (R$ 250 L, 13/10) e Duel 2728364620980039864 do Feca (R$ 30 @ 13, aberta; o leitor recusou a linha da IA duas vezes). A exclusao da Shuffle do Gabriel em 31/10 19:54 e 19:56 foi `DELETE /bilhetes` (tela de Extracao, sem lixeira), **acionada pelo proprio Gabriel** (confirmado pelo Feca). Correcao da Parte 1: as 108 pagas duas vezes vieram de apagar e recapturar, nao de corrida de commit. **Ordem aprovada:** Extra, D39 (com a grafia com ponto), Fase 7, D40, D42, D43, D41. **Deploy `27e93f57`:** healthcheck aprovado e "Application startup complete". **Apostas perdidas:** a Duel voltou sozinha em 01/11 21:41 (3a ida a IA, ~22 h fora do banco: o caso da D39); a 1win 338677290 do Jaao26 foi gravada pela Ficha (id 413103, conta `1win`, rastro em `correcoes`, `scripts/recuperar_aposta_perdida_s438.py`). **1a captura pos-Extra:** Vavada do Feca, 01/11 22:54: 151 capturadas, 145 no banco, 5 pela Ficha, 1 a IA (US$ 0,035). **D39 (falta de cru nunca vai a IA):** (a) cru guardado LIQUIDADO grava pela Ficha, conferido pelo veredito do texto (`Status: ... -> X`); (b) cru aberto com texto mudado ou cru ausente fica SEGURADO, pendente com aviso "captura incompleta" (so se a casa mandou cru ao dono em 7 dias, OK do Feca), e esgota para a IA uma vez depois de 2 `/extrair` ou 24 h (`captura incompleta esgotada`, uma vez por cru); (c) foi a IA e nao virou linha = pendente "sem linha" (so avisa); (d) chave da casa sem espaco, ponto e acento (`app/casa_chave.py`, Python = SQL nas 62 casas). Colunas `ficha_virada.aviso`, `virada_log.captura_incompleta` e `captura_esgotada`. Mutacoes 19/19 Python + 1 JS. Deploy D39 `8b49c8a2` (healthcheck ok, colunas criadas). **Fase 7 (toda exclusao pela lixeira):** `deletar_bilhetes` (Excluir selecionadas, Desfazer analise, linha unica) e a limpeza da Polymarket passam por `_mover_para_lixeira` (DELETE e INSERT na lixeira numa instrucao, motivo do servidor); o Desfazer tira da lixeira o que voltou; o "sem linha" da D39 le tambem a `lixeira_contas`; gate `test_lixeira_sempre.py`; mutacoes 5/5. BACKLOG 4.19 fechado. **Por que o Gabriel apagou:** a Caixa de 17/10 divergiu US$ 556 (ajuste) e recapturar nao conserta linha resolvida: so apagando. Decisoes do Feca (01/11): scripts tambem pela lixeira; expurgo de 90 dias; D44 "Conferir conta com a casa" (sem IA, com rastro, depois da D43); tipster padrao da conta no BACKLOG 3.22. Deploy Fase 7 `adbfe83a`. **Scripts e expurgo:** os 24 scripts com DELETE de aposta passam por `_mover_para_lixeira` (`scripts/_lixeira.py`; `mantido_id` nos reparos, `snapshot` para quem grava arquivo; a poda saiu da `lixeira_contas`); gate estendido a `scripts/`; expurgo da `lixeira_bilhetes` em 90 dias (`LIXEIRA_BILHETES_DIAS`), preguicoso; mutacoes 5/5. **Regra nova (Feca):** a 1a execucao de cada um dos 24 roda antes no Postgres de teste local (`docs/RUNBOOK_SCRIPTS_DE_BANCO.md`, ponteiro no `CLAUDE.md` "Excluir dado"; relato do `_c2num` movido para o `CASOS.md` para caber). Deploy scripts `da737670`. **D40 (descricao desconhecida nunca manda a aposta a IA):** `virada.descricao_para_gravar` grava a perna sem par como `<mercado da casa> - <selecao da casa> [A v B]` (`descricao_ficha.texto_da_casa`, limpo de espaco/quebra/TAB); `virada.descricao` segue ESTRITA (regravacao do mes e scripts; a troca automatica pelo dicionario aprendido foi aprovada pelo Feca); replay da semana: 173 das 318 apostas que foram a IA por descricao a Ficha grava agora, 145 o dicionario de hoje ja cobre; mutacoes 6/6. Herdados da forma `[A v B]`, para a D42: prefixo comum cortado (`FC Brest [Brest v Vitebsk]`) e F1 virando confronto falso (`[... Practice 1 v Winner]`). Deploy D40 `f5dbd432`. **D42 commit 1 (E1, a semente para de esquecer):** `gravar_semente` acumula (ON CONFLICT DO UPDATE); a chave sai so com prova contra: contraditoria na rodada, retirada por aposta editada a mao (R27, `pares_completo` + `chaves_que_votaria`) ou grafia antiga; `semente_log.fontes.preservadas`; mutacoes 4/4. Chave errada de 1 voto sem edicao fica ate voto novo ou `corrigir_termo` (D24): por isso os commits 3 e 4 (semente_recusa e aviso diario) vem logo. Deploy E1 `aa6ee437`. **D42 commit 2 (leitura da descricao), deploy autonomo autorizado pelo Feca:** prefixo comum so de subjogo da 1xBet (344 pernas da semana perdiam nome de time); sufixo de periodo no time 2 entra na chave e a prorrogacao so sai do time; F1 `X vs Winner` e prova, nao confronto; E3 `mas` e lado e Sim/Nao sozinho nao e descricao; E4 ordinal por extenso vira numero, com a chave antiga como 2a tentativa; linha asiatica pela media; E5 nome de 2 palavras invertido. Replay com o dicionario de producao: votos 3.257 -> 3.529, +46 apostas cobertas, -4 (todas do E3, intencionais). Mutacoes 12/12. Deploy commit 2 `ae52454c`. **D42 commit 3 (semente_recusa, deploy autonomo):** tabela nova `semente_recusa` (casa, tipo, chave, motivo, termo, exemplo, n): todo voto de descricao recusado pela semente com o motivo exato (`aprender(por_que)`, `votos(recusas)`), voto de categoria/esporte com valor fora do Master, e a perna que a Ficha grava com o texto da casa (`origem='gravacao'`, o `faltam` que o `virada.py:145` descartava). Falha ao registrar nunca para a semente nem a gravacao. Mutacoes 7/7. Deploy commit 3 `e72cd6f5` (tabela criada). **D42 commit 4 (aviso diario ao Feca, deploy autonomo):** `app/aviso_diario.py`, logo depois da semente das 04h, pelo TELEGRAM_ALERTA_*: recusas repetidas (>=3 na rodada), mercados gravados com o texto da casa (24 h), semente rodou/falhou, pendentes ha mais de 24 h, captura incompleta esgotada (24 h); so contagens por casa, sem usuario; dia quieto nao manda; no maximo 1 por dia (tabela nova `aviso_admin`, reservada antes do envio). Mensagem de teste ("teste do aviso diario da semente") mandada UMA vez pelo app ao subir. Mutacoes 7/7. Deploy commit 4 `c140c34a`; **mensagem de teste do aviso enviada e confirmada pelo Telegram** (`aviso_admin` teste-s438, ok, 02/11 00:39:13). **D42 commit 5 (o vigia como fonte de voto, deploy autonomo):** a semente usa a descricao que o vigia leu pela IA (`vigia_ficha.ia`) quando a aposta nao tem voto melhor (so descricao; `fontes.vigia`); a gravacao da Ficha marca no `ficha_virada` a aposta com perna no texto da casa (`motivo='texto da casa'`), e o vigia a escolhe primeiro (cota de 3 por casa/dia igual). Mutacoes 3/3. D42 completa. Deploy commit 5 `614833cb`. **D43 (Bet Builder pela Ficha, Sportsbet.io; deploy autonomo):** o `sbi` deixou de recusar o Bet Builder (uma perna, odd do conjunto, dinheiro do bilhete pelo caminho de sempre); categoria sempre Multipla (MASTER_APOSTAS); descricao no formato aprovado (`dicionario.descricao_bet_builder`: mesmo jogador com ` / ` na ordem da casa, jogadores diferentes com ` // `, um colchete); selecao fora do padrao medido (52 bilhetes: Pontos/Rebotes/Assistencias, "Partida") grava com o texto da casa; a semente nao aprende com o Bet Builder. Os 5 aprovados saem como aprovados, odds e resultados iguais aos gravados pela IA. 20bet e Altenar seguem recusando. Testes so com a fixture do harness e pernas sinteticas (crus de producao fora do repo). Mutacoes 7/7. **Manha de 02/11:** semente diaria rodou 04:00:49 (id 450, 2424 termos, 205 preservadas) e o 1o aviso diario saiu (`aviso_admin` diario-2026-11-02, ok; 174 recusas repetidas, topo MEGAPARI "perna sem trecho da IA do mesmo jogo"); `semente_recusa` 1881 linhas; nenhuma captura de casa virada desde a D39 ate 04:35, vigia da D39 segue aberta. **1a captura pos-D39** (Gabriel, 02/11 07:47-07:54): 13 novas, todas pela Ficha, nenhuma a IA, 7 com texto da casa. **D44 "Conferir conta com a casa":** cartao no painel da conta + modal (`fmtSaldo`); `app/conferir_conta.py` confere cada aposta contra o cru mais recente pela regua do vigia, sem IA; o aplicar recebe so ids e grava pela edicao de sempre com `correcoes.origem='conferir'` (coluna ja existia; `ORIGENS_DE_ROBO` em `campos_corrigidos`: a reliquidacao segue corrigindo; origem nula = humana, intocavel); fora da lista: cru aberto contra linha liquidada, so odd abaixo de 1,00 no P/L, bonus da casa no retorno (bonus nao e odd, Feca). Medicao pelo `db_ro.py`: Feca 3.060 conferidas, 2 oferecidas; Gabriel 2.155, 1 oferecida (16 corrigidas a mao, 14 delas DEX canceladas pela casa, certas). Mutacoes 12 detectadas, 1 inocua. Nenhuma correcao aplicada (o Feca clica). **D41 (dicionario por familia, "pode" do Feca 02/11):** `dicionario.carregar` empilha casa > familia > geral (feca vence semente em todo nivel); familia lida do cru (`captura_crua.familia`, cache 10 min, `irmas`); termo da familia so passa com as irmas unanimes (118 divergentes ficam na casa, decisao do Feca). Consultoria conferiu: nenhuma casa com duas familias. So a gravacao da Ficha e o `regravar_mes` usam; a semente nao. Teto da regravacao: 86 apostas da Ficha em novembro. Mutacoes 7/7. Proxima: medir a 1a semente pos-deploy, depois plano da etapa c)_

_Anterior: 2026-11-01 (sessao 437: **Locasbet no SharpenUp (0.7.71), 7a casa BetConstruct, espelho da MyStake, sem conta.** Pedido do Feca, sem login: mesmo caminho da Jack (s424). Medido por fora: `messagetosport` 401 contra 404 numa rota falsa em `locasbet12.com` (aba do Chrome) e em `locas.bet` (curl), e os dois servem o mesmo `scripts/common/helpers.js` com o mesmo hash. **O dominio RODA o numero:** responderam `locasbet12/13/14.com`, a raiz `locasbet.com` (403 de fora) e `locas.bet` (fixo da marca, 200); 1 a 11 e 15 a 20 nada. Registrados `locas.bet`, `locasbet.com` e `locasbet12` a `locasbet20.com` (15 a 20 adiantados) no manifest, no popup e em `_HOSTS_POR_CASA`. Grafia decidida pelo Feca: `Locasbet`. **A base ja tinha `Locas.bet`** (1 conta do Gabriel, 29/10, USDT, 0 bilhetes) e o `_norm_casa` nao tira o ponto: seria casa paralela, sem Conectar. Linha `"Locas.bet": "Locasbet"` no `scripts/unificar_casas.py`; relatorio: 1 `parceiros`, 1 `casas_meta`, 0 bilhetes, 0 colisao. O `--aplicar` foi rodado pelo Feca depois do deploy (01/11 16:58; backup em `Backups/s199-unificar-casas/20261101-165802-bilhetes.csv`); conferido depois: `Locasbet` em `parceiros` e `casas_meta`, nenhuma `Locas.bet`. Registro nos pontos do `audit_sharpenup` (`tv_inject` no manifest, ramo e toast no `content.js`, popup, `_CASA_DISPLAY`, `_CASAS_MARCADOR_CODIGO`, modo e hosts da captura, `CASAS_CONECTAVEIS`, dominios e icones), `CODIGO_EXEMPLO` emprestado da MyStake, `CASA_LOCASBET.md` com corpo herdado e roteiro da 1a captura (§16), harness `locasbet.mjs` com a fixture da MyStake em 3 hosts (`locas.bet`, `locasbet12`, `locasbet20`), blocos byte a byte iguais; 58 casos verdes. Mutacoes: ramo do `content.js`, `CASAS_CONECTAVEIS` e host faltando no popup, 3 FAIL detectados. Nota generica no changelog (`--so-changelog`), sem aviso ao grupo. Fora da virada da Ficha: vai pela IA. Suite: 2091 verdes; `test_recorte_custos` (mutacao "o fim do recorte deixa de ser hoje") falha igual na main limpa, nao e desta mudanca. Pendencia em `BACKLOG §4.0x`. **Proximo passo:** o Gabriel atualiza a extensao, recarrega painel e aba da casa e captura; conferir contra o card)_


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
