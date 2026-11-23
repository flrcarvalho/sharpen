# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-11-22 (sessao 465: **E1.1 do plano do marco zero (Sportsbet.io), primeira parte: USDC pela Ficha.** Medicao so leitura em producao (captura_crua, bilhetes, lixeira, virada_log): os 185 codigos BRL que a Ficha recusava sao TODOS do Jonathan, conta `Pessoal [Pessoal]`, apostas de 18/04 a 26/09/2023 (o historico inteiro da conta, numa captura de 21/11). Foram a IA 4 vezes (189, 189, 189, 186; US$ 4,61 em `uso_tokens`), a IA gravou lixo (o `sbi_inject.js` divide toda moeda por 1e8: `stakeAmount` 2000000 virou `Stake: 0,02`) e o Jonathan apagou tudo a cada vez (740 entradas na `lixeira_bilhetes`). A escala do BRL NAO se mede: nao ha gabarito (a IA leu o numero ja dividido, e card de 2023 nao temos); BRL continua recusado. USDC: 5 bilhetes reais (20 e 21/11, 2 W e 3 L) batem a 1e8 em stake, odd, resultado e retorno contra o cru e contra a linha que a IA gravou (so a stake 45,4616 x 45,46: a IA arredondou). USDC entra em `sbi._MOEDAS_MEDIDAS`, e USDC = USDT para o cambio (decisao do Feca, 22/11/2026): `cambio._SIMBOLO` leva USDC a USDT e `_COMPATIVEIS` de USD/USDT aceitam USDC (antes a conta USDT recebia o aviso "a casa informou USDC" a cada captura, e numa conta em real o USDC seria gravado como R$). Gate `tests/test_sbi_usdc_s465.py` + fixture `tests/fixtures/sbi_usdc_s465.json` (os 5 crus, sem campo de identidade), 4 mutacoes, 4 detectadas; os alvos de 5 mutacoes do `test_moeda_captura` acompanharam a linha nova. pytest 2511 verde. Revisado pela consultoria (diff A aprovado, `d8f167e`). **Segunda parte: as travas de entrada** (`app/travas_entrada.py`, diff B, revisado em duas rodadas). (1) **D51 (Feca, 22/11/2026): aposta FINALIZADA com mais de 12 meses nao entra; aberta entra sempre.** No texto: so bloco com veredito (`Status: ... → W/L/V/HW/HL`, o mesmo `virada._VEREDITO`) e pela data MAIS RECENTE do bloco (colocacao, evento, `Liquidado em:`); no cru (`virada.aplicar`): Ficha que deriva resultado finalizado e a maior entre `colocada_em`, `liquidada_em` e inicio das pernas. Sem veredito ou sem data: entra (fail-open; a Superbet escreve o status cru e fica de fora, BACKLOG 4.18). (2) Sportsbet.io em moeda fora de `sbi._MOEDAS_MEDIDAS` (bloco sem `Moeda:` = real) nao vai a IA. O recorte roda no `/extrair` logo depois do corte historico, so em bloco com `[Codigo:]`; o barrado entra no `no_texto` da virada e ganha `ficha_virada.estado = 'barrada'` (nem `ficha` nem `ia`: nao vira aviso de "nao lida" nem de "sem linha"). O CHECK da `ficha_virada` (que so aceitava ficha/ia) ganhou `barrada` no CREATE e num `DO` que so troca quando falta, provado num Postgres real (o INSERT de `barrada` dava CheckViolation no CHECK antigo; migrado, entra, e o 2o boot nao muda nada). Medicao: `virada_log.fora_idade` e `fora_moeda` (migracao idempotente), `extracao_log.motivos`, o `done` e a tela ("N aposta(s) com mais de 12 meses ignorada(s)" e, em warn, "N aposta(s) em conta de real: ainda nao suportada nesta casa"), conferida no Chrome headless com o fluxo real do card. Replay de 30 dias (9.256 crus, funcoes reais): os 185 BRL do Jonathan barrados (174 pela idade, 11 "a conferir" pela moeda), 44 da Stake.com aceitos (Jonathan 37, Gabriel 7, nov-dez/2024) e 8 recusados do Gabriel contados pelo cru. Gate `tests/test_travas_entrada_s465.py` (27 testes), 29 mutacoes, 29 detectadas. pytest 2515 verde. No ar em 22/11 (`cb10c1e`, deploy SUCCESS); a consultoria conferiu no banco de producao o CHECK com `barrada` e as colunas `fora_idade`/`fora_moeda` (o ADD COLUMN sobre o `virada_log` existente rodou ali, ponto fechado no BACKLOG 4.18). Fica medindo a recusa e o gasto da Sportsbet.io ate a proxima captura. **E1.2 (CopaWin), em revisao, sem commit:** o `cw.py` passa a aceitar a aberta (`pending`/`active`, sem resultado nem retorno) e a multipla pelo dinheiro (`lost` com retorno 0; `won` sem perna perdida ou aberta que fecha por stake x `total_odds` ou por stake x produto das pernas nao anuladas); recusa antes da Ficha os 12 `won` reais que nenhuma conta explica, e a multipla `void`/cashout. Backtest D22 (30 dias, funcoes reais): 321 multiplas com gabarito, 309 aceitas iguais em stake, odd, resultado e retorno, 12 recusadas; a odd gravada fecha o retorno no centavo em todas as 817 aceitas; 345 passagens aberta -> liquidada, 344 aceitas (1 boost) e a stake nunca mudou. Unica divergencia: o 836516, aberto na casa e W no banco, gravado pela IA contra a propria nota (BACKLOG 4.0y). Fixture `tests/fixtures/cw_multipla_s465.json` (crus reais, sem `user_id`), mutacoes 12/12 no adaptador (a conta 'produto de TODAS as pernas' saiu: inocua em 144 crus `won`); harness de banco: a aberta nao rebaixa linha resolvida, duas camadas (`_liquidados` e o UPSERT), mutacoes no cabecalho. pytest 2542 verde, harness de banco 164. No ar (`da3dd06`). **E1.3 (Stake.com), em revisao, sem commit:** o `stc.py` aceita a XMulti LIQUIDADA (`_betStatus` settled, USDT, `cashoutMultiplier` 0) pelo dinheiro: `payout` 0 perdida, = stake anulada, = stake x `payoutMultiplier` ganha; odd da casa `_potentialMultiplier`, perna em `prices[0]` (o `outcome.odds` e a cotacao ao vivo), perna de props sem resultado, `voidedLost` sem resultado e so em perdida. A aberta segue recusada (passo 2, BACKLOG 4.0t). Backtest D22 nas 142 (30 dias, funcoes reais): stake, resultado e retorno 142/142; odd 141 (692098480: a IA gravou 0,17 USDT a mais); data 132 (nas 10 a IA gravou a colocacao, a Ficha segue o MASTER_OUTPUT §4); 2.518 crus que nao sao XMulti saem iguais ao adaptador antigo. Fixture `tests/fixtures/stc_xmulti_s465.json` (10 crus reais), 18 mutacoes, 18 detectadas (a 18a, condicao da consultoria: ganha com perna comum perdida recusa). Datas: a consultoria aceitou a Ficha (MASTER_OUTPUT §4, anulada inclusive). Dicionario: ensaio sem esporte/categoria novo, nao aplicado (201 de 206 'termo fora' ja cobertos pela semente). `test_s451_...` (test_virada) passou a exercer a recusa com `cashoutMultiplier` no cru real. pytest 2569 verde, harness de banco 183.)_

_Anterior: 2026-11-22 (sessao 464: **Vavada: a aposta repescada sumia no bloco tsv vazio.** Relato do Feca: extracao com 53 bilhetes, 52 gravados, Caixa 40 acima da casa. Producao (so leitura): o que faltava era 5679661219 (+11982151314 [Eu]), multipla perdida de 40 a 15,278406. Ela foi a IA nas duas extracoes ('termo fora do dicionario'). As 10:56 UTC a IA escreveu a linha deslocada na leitura e na repescagem e o leitor recusou as duas, certo. As 11:00 a IA respondeu SEM cabecalho e com o Tipster pulado; o leitor recusou a unica linha e o bloco ficou vazio (abre e fecha sem nada no meio). A repescagem trouxe a linha certa e o log disse '1 linha(s) repescada(s)', mas o recorte das quatro copias em `main.py` exigia uma quebra antes do fechamento: `_set_tsv_rows` nao achava o bloco, devolvia o texto intacto e a linha sumia sem erro; o front nem chamou o /salvar. Prova: o `titular_final` da `sombra_tsv` daquela extracao esta vazio, e o caso reproduz com o codigo real. Conserto: recorte unico `_bloco_tsv` (aceita bloco vazio) nos quatro helpers e em `contrato_texto.juntar_resultado`; `_set_tsv_rows` sem bloco nenhum CRIA o bloco com cabecalho (a repescada de chunk que respondeu so com notas tambem sumia); `_garantir_cobertura` confere quantas linhas entraram e acusa em ERROR se a montagem perder alguma. Gate `tests/test_tsv_bloco_vazio_s464.py` (TSV real da sombra, leitor de verdade, varredura que barra o padrao antigo em `app/`), 3 mutacoes, 3 detectadas; a primeira escapava porque a criacao de bloco salvava a linha num bloco duplicado, e o teste passou a exigir um bloco so. `test_set_tsv_rows_sem_bloco_tsv_no_op` trocado: ele travava o comportamento que descartava as linhas. pytest 2482 (1 falha anterior, `test_render_da_home_em_node`, a mesma do CI desde a s462). Depois, a pedido do Feca (resolver de vez): a aposta ia a IA porque a perna Hawks Helsinki x Westend Indians e `sportTypeId 18`, unica no cru guardado, e o dicionario nao o conhecia. `18` = Floorball em `dicionario.ESPORTE_D49` (mesma regua da D49: o menu da Altenar em `CASA_ESPORTIVA §12` ja dizia 18 Floorball, e a D33 criou o valor no MASTER). Simulado com o cru real e o dicionario de producao: a Ficha monta Multiplos / Multipla, 40, 15,278406, L, 21/11/2026, sem IA. Gate em `tests/test_dicionario_d49.py` (o 18 e a multipla real; mutacao sem o 18 derruba os dois). `CASA_ESPORTIVA §12` dizia que os numeros ficavam crus (desatualizado desde a D49): nota acrescentada. Nao mexido: `11` Boxe tambem tem valor oficial (D33) mas nenhum bilhete com ele foi visto. Pendente: o Feca recapturar a Vavada depois do deploy; a aposta entra pela Ficha (a virada reavalia o cru igual, como fez as 11:00) e a Caixa deve voltar a bater. Por fim, a pedido do Feca, novidade na home SO no site (`--so-changelog`, sem aviso ao grupo): as 32 casas que entraram na captura desde 01/10 e a Kalshi pela API. Medido em producao: 28 das 32 com captura real; 1xBit, Kikobet, PariPesa e Tornadobet so com bilhetes dos primeiros dias, por print ou a mao (mantidas na lista). Com a novidade, `test_render_da_home_em_node` volta a passar (vermelho no CI desde a s462).)_

_Anterior: 2026-11-22 (sessao 463: **O Deano nao inativava: tipster do operador, no supervisor.** Relato do Feca: o tick "inativo" do Deano dava "Nao foi possivel atualizar o status do tipster". Duas causas em fila. (1) Front: a lista une cadastro + bilhetes (`_tmNomes`) e o Deano nao tinha cadastro; o tick mandava `t.id` e o pedido ia para `/tipsters/undefined/arquivar`. `tmSetInativo` (`gestao.js?v=58`) cria o cadastro pela rota do `tmToggle` e arquiva o id devolvido (`2b51c78`). (2) Servidor: as 35 apostas do Deano estao na base do Lava; o Feca e supervisor e o feed consolidado as mostra, mas a poda de orfaos de `list_tipsters_cadastro` so olha a base do PROPRIO dono e apagava o cadastro recem-arquivado na listagem seguinte (provado em producao: criar 200, arquivar 200, listagem sem o Deano). A poda agora poupa `arquivado = TRUE`. Gate `tests/test_poda_tipster_arquivado_db.py` (3 casos, mutacao detectada) no passo de banco do CI. Suites: banco 181, pura 2484 (1 falha anterior: `test_render_da_home_em_node`). As apostas do Deano ficam, decisao do Feca. Depois do deploy (`4b1d2eb`), o Deano foi arquivado em producao (id 419382) e seguiu arquivado em duas listagens seguidas. Nao coberto: a poda segue sem olhar a base dos operadores para tipster ATIVO sem info (sem perda: a uniao o mostra).)_



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
