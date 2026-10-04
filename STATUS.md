# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-10-03 (sessao 391: **conta em outra moeda, passos 2a e 2b: a moeda entrou no cadastro da conta, e a captura avisa quando a casa diz outra.** O modal de conta (criar e editar) ganhou o seletor BRL / USD / USDT, o mesmo `.cxm-seg` do Tipo da Caixa, e a escolha grava em `parceiros.moeda` no mesmo gesto. `POST /parceiros` e `/parceiros/{id}/editar` validam contra `cambio.MOEDAS` (fora da lista e 400); `GET /parceiros` devolve a moeda. **Ausente nao mexe**, inclusive na reativacao de conta arquivada pelo `ON CONFLICT`. **Decisao do Feca: trocar a moeda vale daqui para frente**, nada e reconvertido, e o modal avisa quantas apostas ficam como estao. **Achado que dividiu o passo 2:** os injects leem a moeda da casa, mas nenhum formatador do `content.js` a escreve no bloco, entao ela nunca chegou ao servidor; o aviso de captura que contradiz o cadastro virou o passo 2b, com desenho aprovado em `docs/PLANO_MOEDA_POR_CONTA.md`. Gates: `test_moeda_conta.py` (rota 4 de 4 mutacoes a mao, front 13 de 13 automaticas), 1 caso de banco no `test_repository_db.py` (so no CI). Suite 1.403 passed. Tela aberta no servidor demo e conferida no Chrome, com o clique real no seletor. **2b (commit proprio):** o `content.js` escreve `Moeda: X` no bloco so quando X nao e real (casas em real ficam byte a byte iguais, harness verde sem tocar fixture); o `/extrair` devolve `moedas` nos tres `done`, o front transporta, e o `/salvar` avisa apontando a conta quando a moeda da casa nao cabe na da conta (`$` cabe em USD e USDT), sem bloquear. Versao da extensao NAO subiu: nenhuma casa capturada hoje manda moeda estrangeira. Gates: `test_moeda_captura.py` (cambio 8/8, content 9/9, rota 4/4 a mao). Suite 1.428 passed. **Passo 3 (commit proprio), decisoes do Feca:** formato `US$ 1.234,50` e `1.234,50 USDT`; seletor `Ver em R$ | USDT` so na grade da Extracao (aparece com a conta ativa em USD/USDT; troca stake e P/L das linhas, cabecalhos ganham a moeda, a stake convertida deixa de ser editavel nesse modo); Base Completa so com a sub-linha (feed leva `moeda`/`stake_orig` so nas linhas convertidas; a tabela virtualizada manteve 68 px por linha); `pl_orig` sai do `calcular_pl` sobre a `stake_orig`, nunca de `pl / cotacao`; a stake editada a mao limpa a origem quando o numero muda. Achado na tela: o sinal do P/L em USDT saia descolado do numero pelo `gap` do `.money`, corrigido e travado por mutacao. Gates: `test_moeda_valor_original.py` (repositorio 6/6, front 14/14) + 1 caso de banco no CI. Suite 1.451 passed. **Ajuste pedido pelo Feca na tela:** o P/L ganhou a mesma sub-linha da stake (R$ em cima, USDT embaixo, com sinal), na grade e na Base Completa (`lucro_orig` no feed); 6 mutacoes novas, todas detectadas; suite 1.457 passed. **Passo 4a, Bet Panda (commit proprio):** recon no Chrome do Feca (BetBy, `bt-renderer` na propria pagina, hash `c7818b61`, host `api-a-…` fora do padrao mas o inject casa por PATH), fixture com a conta inteira (45), 10 cards lidos na tela. 4a casa BetBy sem linha nova de captura; registro nos 12 pontos (`BETPANDA`/`Betpanda`, grafia da marca: a base nao tinha nenhuma). Armadilhas no harness: boost (`k` com, `result_k` sem; na perdida o card mostra o `total_k`), `total_k` que nao zera em multipla perdida, sistema 2/3, oferta de cashout em aberta. O formatador BetBy ganhou `_dinJB`: rotulo na moeda do bilhete, casas em real byte a byte iguais (controle no harness). SharpenUp 0.7.34 com nota GENERICA so na home (`--so-changelog`, decisao do Feca pelo sigilo); grupo nao avisado. Harness 30 casos/486 bilhetes, suite 1.457 passed. **Botao Conectar provado em producao** depois do deploy (`_casaConectavel('Betpanda')` true, controle negativo false, `Betpanda` em `captura` no `/casas`). **Validada ao vivo pelo Feca:** 45 de 45 bilhetes, stake e resultado certos, conversao USDT do `/salvar` funcionando em producao (Binance responde do Railway). **Visto em uso:** a Caixa leu como R$ os depositos em USDT (pendencia no BACKLOG, moeda item 5). **Passo 4b, Dexsport (commit proprio):** plataforma PROPRIA, 1a casa do motor. Recon no Chrome do Feca achou DUAS listas: a do perfil (`POST dexsport.io/api/v3/txs_list`) traz `token`, `ip` e `userId` no corpo e le o retorno de `reserve` (potencial na perdida), descartada; a do SDK de esportes (`GET prod.dexsport.work//api/sportsbook/history/tickets`, XHR, Authorization, `page` ate `meta.totalPages`) e a usada. `dx_inject.js` novo (replay por XHR, token nunca sai do inject), `formatTicketDX`/`roboDXPassive`, registro nos 12 pontos (`DEXSPORT`/`Dexsport`, grafia da marca), `CASA_DEXSPORT.md`. Harness com a conta inteira (41, sem `nickname`): perna anulada (odd 3,75 e nao os 12,56 da colocacao), `payout` 0 tambem na aberta, evento em UTC; 8 mutacoes detectadas. SharpenUp 0.7.35, nota generica so na home. Harness 31 casos/496 bilhetes, suite 1.457 passed. **Botao Conectar provado em producao** (`_casaConectavel('Dexsport')` true, controle negativo false, `Dexsport` em `captura`, nota 0.7.35 no ar). **Grafia corrigida para `DEX Sport` (decisao do Feca):** a 1a versao registrou `Dexsport`, a conta dele era `DEX Sport`, e o `_display_to_key` compara caixa mas NAO ignora espaco: a sessao nasceu em modo print (o Snap abriu na casa, 0 enviados). O registro passou a usar a grafia da conta. A afirmacao de que o `casa_canonica` resolvia isso estava errada (ele so ve grafia que ja existe em `parceiros`) e saiu dos CASA_*.md. **Falta validar ao vivo** a captura na conta do Feca. **Item 5, Caixa na moeda da conta (commit proprio, decisao do Feca):** conta USD/USDT tem a Caixa inteira na moeda dela (lancamentos digitados nela, apostas pela `stake_orig`, conferencia USDT x USDT); `caixa_mov.moeda` vazia = moeda da conta, entao os depositos que o Feca ja lancou passam a valer em USDT; painel soma em R$ pela cotacao de hoje com ≈. `test_caixa_moeda.py` (11 mutacoes detectadas). **Validacao da DEX Sport achou um defeito do passo 1:** 41 copiados, 31 gravados; as 10 que faltaram eram abertas com jogo amanha, e a cotacao usava a data do EVENTO (sem candle de amanha) -> recusadas por 'sem cotacao'. Corrigido no servidor: data posterior a hoje vira hoje (`cambio._iso_da_linha`, teste + mutacao). A barreira nao segura recusados, a proxima captura traz os 10. Pendente: carimbo de colocacao na Dex/Betpanda na proxima versao da extensao. **Passo 4c, SapphireBet + PariPesa + MegaPari (commit proprio, feito sem o Feca por autorizacao dele):** espelhos da 1xBet, mesmo POST em `/bethistory-api/Web/`; o `x1_inject` casa os dois caminhos. `formatTicket1X` ganhou moeda no dinheiro, tipo Sistema (perdido sem `Coef` -> odd vazia) e o carimbo de colocacao, que sai tambem na Betpanda e na DEX Sport em conta de outra moeda e decide o dia da cotacao (fecha a pendencia da Dex). Grafias `SapphireBet`/`PariPesa`/`MegaPari`; Sapphire e MegaPari fora do `CASA_HOSTS` (trocam de dominio). Harness 34 casos/522 bilhetes (7 mutacoes novas detectadas), suite verde, SharpenUp 0.7.36 com nota generica so na home. **Botao Conectar provado em producao** depois do deploy (`_casaConectavel` true nas tres, controle negativo false, as tres em `captura` no `/casas`, nota 0.7.36 no ar). **Falta validar ao vivo** a captura das tres. **Megapari: 1a captura invisivel na conta (20 bilhetes).** Registrei `MegaPari` (a marca) e a base ja tinha `Megapari` (medicao feita sem `lower()`); criar conta usava a grafia da BASE e o `/salvar` a do REGISTRO, entao conta e bilhetes ficaram em grafias diferentes, sem erro (o bug da s249). **Regra unica (pedido do Feca: "essas coisas precisam estar alinhadas"):** `main.casa_oficial` (registro sem caixa/espaco, senao a base, senao verbatim) em criar conta, editar conta e `/salvar` sem conta; `/salvar` com conta grava na casa DA conta, verbatim (nunca deixa bilhete invisivel). Gates: `test_casa_oficial.py` (8 mutacoes detectadas) e `tools/audit_grafias.py` (so leitura, base x registro; achou MegaPari/Megapari e a gemea antiga BingoPlus/Bingoplus, nada mais em 113 casas), que a skill `/sharpenup-casa` passa a exigir antes de registrar. Registro `Megapari`, SharpenUp 0.7.37 (nota generica). **Unificacao aplicada pelo Feca** (30 bilhetes, 30 assinaturas recalculadas, zero colisao; `audit_grafias` verde nas 113 casas). **Validadas ao vivo pelo Feca (04/10):** SapphireBet, PariPesa e Megapari na 0.7.37; DEX Sport recapturada (44, zero recusa, 42 com carimbo) e Caixa da DEX conferida batendo. Editar a casa da conta (item 6) era a base vencendo o registro, resolvido pela regra unica. **USD e USDT nao se contradizem mais** (decisao do Feca, 04/10: a casa nao distingue; o aviso fica para real x dolar). **Proximo passo:** validar ao vivo e investigar a edicao de casa da conta que o Feca relatou como quebrada. **s392, Bet365 de outros paises (etapa 1 de 2):** a captura barrava `bet365.com.au` ("Conectado como Bet365, mas esta aba e..."). Dominios medidos em 03/10: `bet365.com.au` e `bet365.bet.ar` respondem; Guatemala nao tem dominio proprio (usa `bet365.com`). Entraram no `_HOSTS_POR_CASA`, no `CASA_HOSTS` do popup e nos dois `matches` da Bet365 no manifest; o `b3_inject` ja usava `location.origin` e nao precisou mudar. SharpenUp 0.7.38. Teste novo em `test_captura.py` (mutacao detectada), `audit_sharpenup BET365` e harness verdes (35 casos/549). **Falta validar ao vivo** a 1a captura na Bet365 AU. **Etapa 2 (commit proprio):** conta em EUR, AUD e ARS. `cambio.MOEDAS` = BRL USD USDT EUR AUD ARS. EUR/AUD pelo PTAX generico (`CotacaoMoedaPeriodo`, so o boletim de Fechamento, recuo de 10 dias, mapa e faixa por moeda; o USD continua no mapa do Polymarket). O BCB nao tem ARS (medido): ARS = `USDT/BRL ÷ USDT/ARS`, abertura dos dois candles do mesmo dia (par existe desde 28/04/2023). Conferido ao vivo: EUR 5,88 · AUD 3,63 · 1 ARS = R$ 0,0032. Formato `€ 1.234,50` · `A$ 1.234,50` · `AR$ 1.234,50` (`$` solto nao cabe no peso no aviso de captura). Seletor da conta com 6 botoes (duas linhas de tres), conferido no Chrome headless. Guatemala aposta em USD (Feca), nada novo. Gates: `test_cambio_moeda.py` (8 mutacoes novas detectadas), `test_moeda_conta.py` ganhou o gate seletor = `cambio.MOEDAS` = `_MOEDA_ORIG` (index e app.js, provado por mutacao), 3 mutacoes novas no front. Suite 1.476 passed. **s392, MyStake (commit `3bcdb97`, outra sessao, publicado junto com o push da moeda):** pergunta do Feca: quanto falta para o SharpenUp reconhecer a plataforma sozinho? Tres agentes mediram: nos espelhos, a logica propria da casa e de 0 a 1 linha; o custo e registro repetido em ~17 listas, `CASA_*.md` copiado e versao nova da extensao a cada dominio (proposta de registro unico por plataforma + `registerContentScripts` + detector por caminho E forma, ~2-3 semanas, nao iniciada). **MyStake = BetConstruct** (reviews diziam Upgaming; o F12 logado desmentiu): mesmo `gethistory`, mesmas chaves, `Company: 28`. 4a casa do `tv_inject`, sem logica propria. Novidades da familia: `TicketType 3` = FREEBET (badge F, confirmado pelo Feca) sobe como `Freebet incluido:` (rotulo da Superbet) e `Items[].Result 6` = meia derrota. Grafia `MyStake` (a da base, 2 contas); dominios `mystake.bet` (provado) + `mystake.com`/`mystake2.com`; nao colide com `Stake` (host e nome exatos). Harness 35 casos/549 bilhetes, 4 mutacoes detectadas. SharpenUp 0.7.39 **sem aviso e sem nota na home (decisao do Feca)**: dispensada em `sharpenup_sem_nota`. **Decisao do Feca (03/10): freebet e dinheiro da casa em TODAS as casas** (perda 0, ganho = lucro, a casa paga so o lucro), nao implementada: `BACKLOG 4.0a`. Achado: `hisminus:true` inverte o sinal do handicap na descricao da familia BetConstruct: `BACKLOG 4.0b`. **Falta validar ao vivo** a 1a captura da MyStake e o botao Conectar em producao.)

_Anterior: 2026-10-03 (sessao 390, 02 a 03/10: **conta em outra moeda, passo 1, e o recon das 4 casas cripto.** Pedido do Feca: subir Bet Panda, Dex Sport, SapphireBet e PariPesa no SharpenUp, com aposta em USD/USDT convertida para R$ e visivel na moeda original. **Sigilo:** casas normais no seletor, mas sem aviso aos testers, sem changelog e sem home. **Recon (Chrome, contas do Feca):** Bet Panda e BetBy (`my_bets/list`, igual a Jonbet); Sapphire e PariPesa sao 1xBet (`GetBetInfoHistoryWithSummaryByDates`, outro caminho: `/bethistory-api/Web/`); Dex Sport e plataforma propria (`prod.dexsport.work/api/sportsbook/history/tickets`). A Bet Panda manda `currency: "$"` com carteira em Tether: **a API nao distingue USD de USDT, por isso a moeda e da CONTA.** **Passo 1 no ar:** `parceiros.moeda`; em `bilhetes`, `moeda`/`stake_orig`/`cotacao`, com `stake` sempre em R$. `app/cambio.py` converte so a stake no `/salvar`: USD pela PTAX do Polymarket, USDT pela ABERTURA do candle diario da Binance (fixa desde 00:00 UTC; o fechamento mudaria a stake ate a liquidacao congelar). Sem cotacao a linha e recusada, nunca gravada como R$. No UPSERT a origem troca exatamente quando a stake troca. **Nada grava `parceiros.moeda` ainda, entao nenhum numero no ar mudou.** Gates: `test_cambio_moeda.py` (9 de 9 mutacoes), 3 casos no `test_salvar_parceiro_id.py` (4 de 4), 4 casos de banco no `test_repository_db.py` (so no CI). Suite 1.382 passed. **Proximo passo:** moeda no cadastro da conta (passo 2). Plano e recon em `docs/PLANO_MOEDA_POR_CONTA.md`; pendencias no `BACKLOG §5`.)

_Anterior: 2026-09-29 (sessao 386, continuacao de 23 a 29/09: **viabilidade economica do fluxo de IA, medida e paga, no worktree `Planilhador-exp-s386` (branch `exp/s386-custo-haiku`). Nada entrou na main nem no ar.** Gasto autorizado: US$ 12 + US$ 12; usado US$ 11,25 + US$ 7,38. **Haiku ENCERRADO por medicao** nos dois papeis (le tudo; le o que o tradutor nao resolve), com criterio pre-registrado: +3,5 p.p. e +7,8 p.p. de erro de significado contra o Sonnet nos mesmos blocos. **Sonnet SEM pensamento ACEITAVEL:** fluxo completo pelo `/extrair` real (tradutor, contrato de 4 campos, retorno real ao caminho atual, 64k) em 902 blocos NOVOS de 7 donos: erro de significado 0,7% com pensamento x 0,9% sem (diferenca pareada -0,3 a +0,8 p.p.), 0 falso negativo em 30 por braco, custo MEDIDO US$ 0,00397 x 0,00308 por bloco. `normalizar_forma` no portao (` @ `->` v `, Mais/Menos de->Over/Under) projeta US$ 0,00193. **Corrigido no branch:** MASTER §10.1 (a linha e copiada, nunca vira .5), §12.5.1 (time do total de time, decisao do Feca de 24/09) e §12.2.1 (prop de sim/nao do jogador); CASA_BET365 §9; tradutor (`(F)` nao e eBasket, escopo de time, falta sofrida, data estimada recusada, CL=12/16 sem nome); portao recusa linha truncada. **Formato antigo da extensao: 0% desde 21/09.** **Por usuario (30 dias):** Feca e Gabriel custam R$ 798 e R$ 739/mes hoje e R$ 377 e R$ 425 no fluxo novo; 60-75% do que sobra sao OUTRAS casas, nao medidas. 42-67% das leituras Bet365 deles sao RELEITURAS cujo significado o UPSERT descarta. **Proximo passo e decisoes:** `BACKLOG 3.19`. O Haiku: `BACKLOG 3.13`. **Indice compartilhado:** outra sessao commitou o BACKLOG no meio deste encerramento; o 3.19 e o fechamento do 3.13 entraram em commit proprio, depois do dela (`96904e7`).)

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
