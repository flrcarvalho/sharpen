# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-10-29 (sessao 433: **Extracao em uma passada, as 6 entregas (plano aprovado pelo Feca, versao A).** Pente fino pedido pelo Feca: a 1a extracao da Vavada nova demorou ~2 min e "nada veio instantaneo"; o Gabriel (28/10 19h48) viu o Sharpen "travar". Medido nos logs da Railway: o dicionario da Ficha e por CASA, nao por conta (a hipotese do Feca nao se confirmou); na Vavada 21 de 26 pela Ficha em 1 s e 5 na IA (4 descricao fora, 1 termo fora) em 25 s, 14 deles de repescagem; o resto foi pareamento e a extensao lendo a casa. Na janela do Gabriel o servidor respondeu tudo em ms, sem 5xx: ele recarregou a pagina 2 vezes (499). Achados sem mexer: a pagina dispara ~63 `GET /parceiros` por carga (um por casa, `carregarParceiros`) e a semente do dicionario (`semear_agora`, gatilho extrair) segura o event loop alguns segundos (um PATCH de 5,2 s no meio dela). Plano visual aprovado (artifact `UZcw3dRnV6NCYqkZH43Niw`, passado pelo `/nova-ui`): 1.1 atualizacao unica, 1.2 barra "Processando N de M" sem expor Ficha/IA, 1.3 linhas "processando", 1.4 pagina de Logs (`extracao_log`, parte so do admin), 2.1 faixa de 7 KPIs (Turnover + apostas no mesmo card, Em aberto ambar, Caixa sem a linha Saldo disponivel e numero 20px), 2.2 painel da conta (curva com topo/minima + calendario, no lugar do Raio-X) e cards de tipster. **1.1 feita:** o `carregarGrade` pede resumo e Caixa JUNTO com a lista (antes, depois de desenhar); o ramo "nada novo" do `runExtractionCard` (tudo pela Ficha) passa a recarregar; o `loadData` da Extracao ouve o "base mudou" (`_recarregarGradeDeFora`) com tres travas: foco na lista, linha marcada (s432) e recarga propria ha menos de 2,5 s (o ↻ ignora esta). Medido no Chrome headless contra o `servidor_demo` (5 casos verdes, 0 erro de pagina), 4 mutacoes detectadas; o ramo "nada novo" e a trava de foco nao tem medicao. pytest 2040 verdes; os 3 `test_changelog` vermelhos sao anteriores (manifest em 0.7.68 sem nota, s431). Backup em `Backups/s433_extracao_atualizacao_unica/`. **1.2 feita:** o `/extrair` manda a contagem no 1o evento (`triagem` = total e prontas, saida do pre-dedup: `_dedup_superbet_text(info=...)`, codigo repetido pelo scroll conta uma vez; `_com_triagem`), so em lote de texto com marcador e sem imagem/planilha; a barra (`#procBar`, `_procPorConta` por conta) toma o lugar da barra de acao enquanto a conta da tela processa: indeterminada sem total, "N de M" com o avanco por lote (`chunk_progress`), "Finalizando" no ultimo, resumo de 6 s ("5 novas · 1 atualizada · 2 a conferir") e some; a 1a batida recarrega lista e P/L assim que chega a contagem. Ficha, IA e conferencia nao aparecem para o usuario (pedido do Feca). Gates: `tests/test_triagem_progresso.py` 5 testes, 4 mutacoes detectadas; medido no Chrome headless com `/extrair` e `/salvar` simulados (indeterminada, 24 de 30, 27 de 30, troca de conta no meio, Pronto com aviso, some em 6 s, caminho "tudo pronto"), 0 erro de pagina; pytest 2045 verdes. Backup em `Backups/s433_progresso_por_aposta/`. **1.3 feita:** a `triagem` leva `lendo` (codigo, data e stake de cada bloco que segue a IA, ate 300, copiados do bloco; stake com dois valores vai vazia, regua do `corrigir_stake_tsv`; `_resumo_do_bloco`); a lista mostra uma linha "Processando" para cada uma no topo da 1a pagina sem filtro (`_linhasLendo`), tirando o codigo que a lista ja tem (aberta relida); saem no fim, no erro e no cancelamento (que ganhou titulo proprio). Gates: 8 testes em `test_triagem_progresso.py`; 4 mutacoes detectadas (2 no servidor, 2 na tela medidas no headless); pytest 2048 verdes. **1.4 feita:** pagina **Logs de extracao** no dash (`charts/logs.js`, `#dash/logs`, item nos DOIS menus em Operacao, `test_sidebar_dupla` verde), tabela `extracao_log` (uma linha por `/extrair`): o `_com_log` embrulha todo fluxo do `/extrair` e grava ao passar o `done` ou o `error` (total, prontas, para_ia, motivos da virada, notas da IA, modelo, custo, avisos de cobertura/fidelidade) e devolve `log_id` no `done`; o `/salvar` recebe o `log_id` e completa novas/atualizadas/alertas (`fechar_extracao`, escopado por dono). `GET /extracoes/log` (dono_efetivo; a parte do motor so sai com `eh_admin`). Na Extracao o RAIO-X e o historico sairam (`sem-rail` sempre; o codigo do rail fica dormente ate a 2.2 ocupar a coluna) e o aviso que pede acao fica na tela (`#extAviso`) ate ser dispensado, com link para o log. Achado no caminho: o 1o `showPage` da casca chega antes do `buildHTML` e marcava a pagina como pintada (tela vazia); Logs agora sempre busca ao abrir. Desvio conhecido reusado sem copiar a regra: `.qbtn.active` e branco sobre o acento (Escada pede tinta escura). Gates: 4 testes de banco novos (Postgres local) e 4 mutacoes no SQL detectadas; 3 testes do `_com_log` e 3 mutacoes detectadas; medido no headless (pagina, detalhe com admin, so com aviso, Extracao sem rail, `log_id` no `/salvar`, aviso fica/dispensa/link), 0 erro de pagina; pytest 2052 + 88 de banco verdes. Backup em `Backups/s433_pagina_de_logs/`. **2.1 feita:** faixa de 5 cards (fora da Polymarket, classe `.faixa` na `.colmain`): P/L com ROI embaixo, Turnover com apostas e win rate embaixo, Em aberto (ambar, `.money.aberto`, regua do selo Aguardando resultado: `extraction_state = 'aberta'`, `repository._em_aberto` no `/conta/resumo`), Dias ativos com a duracao e o inicio, Custo; Duracao e Win Rate deixaram de ser cards. Card da conta compacto (duas linhas). 5 numa linha quando cada um tem 175px, senao 3 + 2 (grade de 6 com spans). Label dos tiles corrigido para `--ink-soft` (era `--ink-mute`, desvio da Escada). Caixa sem a linha Saldo disponivel e numero de 25 para 20px. `_moneyInt` ganhou a classe opcional (nada de mascara nova). DESVIO DO MOCKUP, medido: a faixa na largura toda empurrava a Caixa e a lista comecava 125px mais baixo em Full HD; a faixa ficou na coluna da esquerda e a Caixa ao lado das duas linhas, como antes; e o ROI desceu para baixo do P/L para caberem 5 cards. Lista em relacao ao antes: 1366 +3px, 1536 -5px, 1920 -41px (Caixa mais baixa). Gates: 3 testes do `_em_aberto`, 1 de banco do `resumo_conta` (mutacao sem a coluna detectada); medido no headless em 3 larguras, 0 estouro, 0 erro de pagina; pytest 2055 + 89 de banco. Achado SEM mexer: `resumo_conta` nao seleciona `stake_freebet` (a mesma falha que a s405 consertou na sidebar): freebet perdida entra cobrada inteira no P/L da faixa. Backup em `Backups/s433_faixa_kpi/`. **2.2 feita:** `GET /conta/painel` (`repository.painel_conta`/`_painel_conta`, pura, mesmo SELECT e filtros do `resumo_conta`): serie DIA A DIA partindo do ZERO (regua do `calcTopoDrawdown`, memoria topo_drawdown_dia_a_dia), topo e minima com data `None` quando sao o inicio, e por tipster apostas, P/L, ROI, win rate (fracao HW/HL) e odd media; sem tipster conta tambem as abertas. Na tela, o `#painelConta` mora na coluna que era do RAIO-X (372px, 440px a partir de 2200px, recolhe pela MESMA alca `.rx-alca`; nasce recolhido abaixo de 1500px de janela, preferencia no localStorage), com a curva (topo, minima, do topo, "i" com o numero real) e o calendario do mes (cor pela intensidade do P/L do dia, valor em `fmtPL` so no dia selecionado, nav de meses). Os cards de tipster (`#tipCards`, ate uma linha) ficam no vao embaixo da captura SO se nao empurram a lista (medido na propria lista, com e sem os cards; `ResizeObserver` na faixa, captura e Caixa), senao descem para o painel; empilhado (<= 1180px) moram no painel, depois da lista. Medido no headless em 1366/1536/1920 e conta nova: lista no MESMO lugar da 2.1 (831/586/804), 0 estouro, 0 erro. Tres armadilhas medidas no caminho: `.workfull.sem-rail.rx-off` (3 classes) vencia a coluna do painel; o `renderCaixa` desenha antes de a Caixa ficar visivel; a fonte carrega depois e muda as alturas. Gates: 5 testes do `_painel_conta` (4 mutacoes detectadas, uma refeita por errar o alvo), 1 de banco da rota; pytest 2060 + 90 de banco. Backup em `Backups/s433_painel_da_conta/`. Pendencias novas no `BACKLOG.md` (3.0a freebet no resumo e no painel, decisao do Feca; 4.0a os 63 `/parceiros`; 4.0b a semente no event loop; 4.0c `.qbtn.active` branco sobre o acento). **Ajustes do Feca depois da entrega:** o titulo "Painel da conta" saiu (o "desde" foi para o card do P/L acumulado); P/L acumulado, Resultado por dia, Apostas e Tipsters desta conta usam o titulo da Caixa (`.cx__hd .t, .sec-t`, um padrao so; o `.grade-title` cinza saiu); os tipsters ganharam box proprio; cada dia do calendario mostra o P/L inteiro com sinal (`_pcPlDia`; valor exato no rodape e no aria-label). Freebet (3.0a, decisao do Feca: a regra do §5.8 vale em todo o Sharpen): `resumo_conta` e `painel_conta` passam a ler `stake_freebet`, e o Em aberto da faixa soma o dinheiro real, como a Caixa. Gates: 1 teste de banco e 1 do `_em_aberto`, 3 mutacoes detectadas; headless em 3 larguras com a lista no mesmo lugar (831/586/804), 0 erro. Backup em `Backups/s433b_painel_ajustes/`. **Polymarket no visual novo** (mockup v2 aprovado pelo Feca, artifact `2iG2vPP3XZ5bs4AeGmxvjn`): a grade de 12 cards saiu; a Polymarket usa a mesma faixa de 5, o painel da conta e os tipsters de qualquer casa (`_pcVisivel` deixou de excluí-la; a rota do painel já lia o P/L dela em reais). A carteira virou um bloco próprio no lugar da captura (`.pcart`, dentro do `#capwrap`): cabeçalho com endereço, Sincronizar e status, e Disponível, Em posições (era "Saldo em aberto", renomeado para não colidir com o "Em aberto" de stake da faixa), A resgatar (só quando há) e Total. O card "Posições ativas" saiu (a contagem está no Em aberto da faixa). Medido no headless em 1366/1536/1920: lista em 695/437/634 (antes, em Full HD, 635), 0 estouro, 0 erro. Desvio conhecido, mantido: `fmtUSD` sem ponto de milhar e `fmtBRLsub` com `toFixed` no ≈ R$ (anteriores, decisão do Feca pendente). Backup em `Backups/s433c_polymarket_visual/`. **Divergência de US$ 767,78 na Caixa da Polymarket (o Feca achou que era do redesenho; não era):** o extrato v2 fecha com o on-chain (916 linhas, US$ 198,16) e a carteira não tem atividade depois de 09/10/2026 00:03 (a lista acabar em 08/10 é real). O coletor dava −US$ 2.153,61 e o extrato −US$ 2.921,40 em apostas: 8 mercados de maio a setembro, todos com REDEEM do lado PERDEDOR (`usdcSize: 0`), que `_payouts_por_lado` lia como índice vencedor (W cheio). Agora o payout é por lado resgatado (`usdcSize ÷ size` de cada índice). Medido contra a carteira real: coletor −US$ 2.921,67, sobra ~US$ 0,27 de centavos (tolerância da Polymarket com 624 apostas: US$ 0,31). O próximo Sincronizar reescreve as 8 linhas (`origem='sync'` refresca resultado e odd). Gates: 2 testes com os dados reais (Zagreb; KT × Kiwoom), código antigo reprova os 2, mutação no ramo do perdedor detectada. Regra em `CASA_POLYMARKET.md`. **Ajustes do Feca na Polymarket (30/10):** card da conta em três andares em toda casa (nome; ‹ conta ›; editar e arquivar); carteira numa linha, rótulos com a tarja azul do KPI e Em posições/A resgatar em âmbar quando há valor (zero neutro); na Caixa da Polymarket as notas fixas (moeda, "automática") foram para o "i" da Conferência automática e a divergência ficou mais curta (`tests/js/caixa_polymarket_front.mjs` passou a conferir o `title` do "i"; mutação detectada). Lista: Polymarket 603/646 (2560 e 1920 / 1366), outras casas no mesmo lugar (831/586/804). **2ª rodada (30/10):** Carteira virou box com título, endereço + Sincronizar e os saldos no MESMO `.tile` da faixa; faixa com número que acompanha a largura do tile (`cqi`, piso 13px) e, com a coluna da esquerda abaixo de 720px (1600px com painel aberto), o card da conta deita numa linha acima da faixa (`@container esq`); input de Custo encolhe e o botão fica no card; cabeçalho da Caixa quebra linha em vez de cortar a pílula (1536 nas outras casas: lista 586 → 599); na Polymarket, Caixa batendo NÃO mostra mensagem (decisão do Feca: é automática), a diferença real de centavos foi para o title da pílula CONFERE e o "i" com as notas para o título (testes da tela ajustados, mutação do arredondamento segue detectada). Medido 1920/1600/1366 sem estouro, 0 erro. **Próximo passo:** o Feca clica Sincronizar na Polymarket (regrava as 8 derrotas; a Caixa deve voltar a bater) e confere no Chrome dele a Extração e o menu Logs com uma captura real. Abertos no `BACKLOG.md`: 3.0b (dólar sem milhar), 4.0a (63 `/parceiros`), 4.0b (semente no event loop), 4.0c (`.qbtn.active`).)

_Anterior: 2026-10-29 (sessao 432: **Excluir em massa na Base Completa e no Em Aberto.** Pedido do tester Gabriel (Los Panas): apagar a base de tipsters importada e ficar so com os proprios dados; a barra de selecao so tinha "Editar em massa". Botao `Excluir` na barra (`apSelExcluir`, `charts/apostas.js`) abre o `shConfirm` em modo perigo e so libera com o NUMERO de apostas digitado (aceita `42.045` e `42045`). Rota nova `POST /bilhetes/excluir-lote` (dono efetivo): o servidor reconfere o numero (ids deduplicados) e MOVE as linhas para a `lixeira_bilhetes` numa instrucao so (`WITH sai AS (DELETE ... RETURNING to_jsonb) INSERT`), motivo `exclusao em massa pela tela`; id de outro dono volta em `ignorados`; invalida o matcher. Restaurar e manual, por script. O modal avisa que aposta da captura do SharpenUp volta na proxima captura (o caso do Gabriel e base importada, que nao volta). O `DELETE /bilhetes` antigo (Extracao, "Desfazer analise") ficou como estava, sem lixeira. Gates: `tests/test_excluir_bilhetes_lote.py` 10 testes, 5 mutacoes detectadas; pytest 2040 verde fora o `test_changelog` (3 falhas anteriores a esta sessao: manifest 0.7.68 da s431 sem entrada no changelog); check-tokens e check_docs sem FAIL; tela medida em headless no `servidor_demo` (botao, modal, numero errado trava, corpo `{ids, confirmar}`, fecha e limpa a selecao). Sem aviso ao grupo de testers (pedido de um tester, respondido direto). **Proximo passo:** responder o Gabriel; acertar o changelog da 0.7.68 para o `test_changelog` voltar ao verde.)_

_Anterior: 2026-10-27 (sessao 431: **1win, o cashout ficava ABERTO no Sharpen (conserto, SharpenUp 0.7.68, sem aviso aos testers).** O Feca fez cashout em 5 multiplas da 1win (27/10, conta `Feca [Eu]`, USDT) e nada contabilizou. Medido nos crus (so leitura): a 1win manda o cashout como `bet.status 4` com TODA perna em `4`, ate perna cujo jogo ja terminou (Petrolul 0x6), e `profitAmount` = o valor recebido; o `4` nunca tinha tido amostra, a Ficha recusava (`tp.py`) e o bloco dizia `a conferir`, entao os 5 ficaram abertos (253,64 USDT recebidos fora da Caixa). Conserto nos dois lados (`tp._status` -> `cashout`, o `ficha.derivar` decide; `_cashoutTP` no `content.js`): status 4 + toda perna 4 + retorno > 0 -> cashout, que pela regra global (`MASTER_RESULTADO §5.1.2`/`§5.6`) e V se recebido = stake e W com odd = retorno / stake se nao (361482655: 31,80 / 40 = 0,795). Fora do formato medido (perna fora do 4, retorno zero, cashout parcial) segue a conferir. Gates: crus reais em `extensor/harness/fixtures/1win.cashout.json`; `test_adaptador_tp.py` 4 mutacoes novas detectadas; harness 1win (`cashout`) 5 detectadas; harness 55 casos verde; audits sharpenup/casas/check_docs sem FAIL. **Proximo passo:** depois do deploy, o Feca recaptura a 1win: a Ficha relê o cru guardado (texto igual = `iguais`) e grava os 5 como W, sem precisar da 0.7.68.)


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
