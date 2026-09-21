# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-20 (sessao 378: **a travada da Bet365 nunca foi da casa, e a prova exigiu construir um gravador antes de tocar em qualquer conserto.** Pergunta do Feca (*"1 a 2 segundos por bilhete, extracoes de 500 a 600, existe um mundo onde isso seja rapido?"*). A explicacao em vigor vinha da s184: *a confirmation da 500 sob rajada no namespace D0*, e dela sairam a folga de 900ms, o teto de 9s e os dois retries com bounce. **Ninguem nunca tinha medido o STATUS das respostas.** Entrou um gravador no `b3_inject.js` (evento por evento com status HTTP e duracao, persistido em localStorage, sobrevive ao reconectar) mais catalogo de rotas e inventario de campos. **MEDIDO AO VIVO, na conta do Feca: 473 `confirmation` e 133 `summary` numa sessao, TODAS 200, sem degradacao nenhuma** (mediana 422ms no primeiro bloco de 50, 391ms no ultimo). Zero 500, zero 429. **Nao existe cota nem punicao por rajada.** **A CAUSA REAL: muro de historico do navegador.** Cada detalhe abria com `location.hash = rota`, e toda atribuicao ao hash empilha uma entrada; passadas ~420 entradas o roteador da pagina da casa para de trocar de rota e passa a devolver sempre o MESMO bilhete, com 200 em ~350ms, enquanto o `esperarCodigo` estoura o teto de 9s em todos os seguintes. **Reproduzido duas vezes em sessoes independentes: quebrou na 435a navegacao e na 417a.** "Reconectar" NAO cura (medido: contador parado em 436, 100 segundos sem um codigo novo, 0 de 18 navegacoes), so recarregar a pagina. Conserto: `location.replace` nos tres lugares que mexiam no hash. **SEGUNDO ACHADO, a memoria indexada pela VISAO e nao pela aposta.** Numa varredura de 1049 bilhetes ~95% ja planilhados, o driver registrou `alvos 1038 - pulados 0`: a memoria nao reconheceu UM. O `ID` do summary e do namespace (24h=D1, 48h/Periodo=D0) e a memoria e indexada por ele. Provado com as duas visoes carregadas com 5 minutos de diferenca, 269 entradas para 189 apostas reais e **77 duplicatas entre visoes, com o MESMO codigo de comprovante** (`TP 20260921002749000`: D0 id=49911954609 e D1 id=3152534307690061594, ambos `YR5088082431I`). Dentro do mesmo namespace ela funciona bem (passada seguinte: `alvos 282 - pulados 425`). O campo estavel e o **`TP`**, identico em 6 de 6 pares conferidos por codigo, mas **nao unico sozinho** (3 `TP` repetidos na mesma visao em 269 entradas, aposta feita no mesmo segundo), entao precisa do desempatador que o projeto ja usa para dedup sem id: stake e odd, os dois no summary, de graca. **TERCEIRO ACHADO: passada que nao termina nao grava memoria.** O `b3Lembrar` so rodava no fim do laco, e recarregar a pagina no meio (o gesto natural de quem ve a captura travada) matava a rodada antes disso: **435 bilhetes detalhados, ~15 minutos de confirmation paga, perdidos.** Agora grava em lotes a cada ~10s (`b3Colher`). **O QUE NAO ENTROU, e por que:** a folga de 900ms e **60% do custo por bilhete** (1.523ms medidos: 617 de navegacao real, 906 de espera nossa), mas **o Feca cobrou a prova e ele estava certo**: a medicao inteira foi feita COM os 900ms, ou seja ~40 requisicoes por minuto, o que derruba "punicao por volume" e **nao** derruba "limite por taxa". Baixar para 300ms leva a ~66/min, taxa que ninguem nunca exerceu contra esta casa, e o preco de errar esta medido: **o historico da conta ficou bloqueado por horas, duas vezes no mesmo dia, sempre depois de varredura de periodo largo, e sempre sem nenhum sinal no HTTP**. Fica para passo separado, uma variavel por vez, depois de o `replace` provar que o muro sumiu. **CUSTO x TEMPO, que o Feca tambem perguntou:** os bilhetes pulados **nao pagam IA** — o `/extrair` ja corta por `get_codigos_resolvidos` e pelo hash de `bloco_visto` antes do modelo. O desperdicio aqui e relogio, nao dinheiro. **E o custo cresce com o TAMANHO da lista, nao so com o que ha de novo:** expansao a 0,94s por clique com 189 bilhetes e **2,35s com 1049**; navegacao a 617ms com 189 e **998ms com 970**. Argumento medido a favor de janelas menores. **Nao existe rota de lote** (catalogo levantado por completo: a `confirmation` aceita um `bsid` e ponto). **DOCUMENTACAO:** os dois casos foram para `docs/casos/CASOS_BET365.md`, **particao nova** aberta porque o `docs/CASOS.md` encostou no teto de 60KB e o gate manda partir por assunto; a explicacao errada foi corrigida no log de retidos do `content.js`, nos comentarios do `b3_inject.js` e na tabela do `SHARPENUP_ARQUITETURA.md`. O historico da s184 nao foi reescrito, que e registro. **GATES:** harness do extensor verde (29 casos, 471 bilhetes) em cada passo, `node --check` nos dois arquivos, `check_docs` verde. **O harness pegou uma quebra real:** a primeira versao do gravador chamava `setInterval` solto, que nao existe no sandbox dele, e derrubava o `b3_inject.js` inteiro na carga (Bet365 foi de 471 bilhetes para excecao). **PENDENTE, nesta ordem:** (1) validar o `replace` ao vivo na proxima extracao, olhando se as navegacoes passam de 435 sem quebrar; (2) so entao baixar a folga, com o gravador vigiando o primeiro status diferente de 200; (3) trocar a chave da memoria para `TP` + stake + odd, com a trava de par unico nos dois sentidos que o projeto ja usa para orfas e codigo fantasma, porque chave errada ali nao perde bilhete, **corrompe** (atribui codigo e pernas de outro).)

_Anterior: 2026-09-20 (sessao 377: **o modelo da extracao estava uma geracao atras, e isso custou R$ 1.496 medidos.** Pergunta do Feca (*"qual modelo usamos? e o Haiku, quao mais barato?"*) que virou achado: o `DEFAULT_MODEL` era `claude-sonnet-4-6`, geracao ANTERIOR, a 3/15 por MTok, enquanto o Sonnet 5 custa 2/10. Medido em `uso_tokens`: **R$ 287 em julho, R$ 448 em agosto, R$ 761 so em setembro**. Ninguem errou codigo; a lista `ALLOWED_MODELS` foi curada quando o 4.6 era o atual e nunca mais foi revista. **PROVA ANTES DE TROCAR, sobre blocos REAIS da sombra e pelo caminho de producao** (mesmo `build_system`, mesma `_INSTRUCAO`, mesmo fatiamento de 6), com juiz DETERMINISTICO — `checar_descricao`, `checar_fidelidade`, `codigos_do_texto`, stake contra o `Stake:` do bloco e resultado contra a seta: **descricao fora do MASTER 13,9% -> 0,0%** (253 blocos, 10 casas), **codigo inventado 1 -> 0** (600 blocos), **coluna comida em aposta aberta 3 -> 0** (84 blocos, todos abertos), stake e resultado errados 1 -> 0 em cada. **O Sonnet 5 ganha em TUDO que deu para medir e custa 33% menos.** **O HAIKU 4.5 FOI REPROVADO, com numero:** perdeu **8,7% dos bilhetes** e inventou **19 codigos** em 253 blocos. Ele fecharia a escada de preco no papel (R$ 0,024/bilhete contra R$ 0,048) e quebra o dado — a prova offline custou US$ 1,46 e dispensou construir a sombra em producao que estava planejada. **DUAS VEZES EU QUASE ENTREGUEI NUMERO ERRADO, e as duas foram defeito do meu HARNESS, nao dos modelos.** (1) A 1a rodada montava lotes com 6 bilhetes SORTEADOS de dias diferentes; bilhete parecido lado a lado e' o que faz um modelo fundir dois num so. Refeito com 6 blocos CONSECUTIVOS da mesma extracao. (2) Eu passava `parceiro='(nao informado)'` e o modelo emitia a coluna 5 VAZIA; com duas vazias seguidas ele come a terceira (o `resultado` vazio da aposta aberta) e o codigo escorrega da 11a para a 10a coluna — o defeito de deslocamento da s193. **Provado por isolamento** (mesmos 14 lotes, so o parceiro mudando): com parceiro real o Sonnet 5 vai de 2 para **0** e o 4.6 fica em 3. **O banco confirmou que era meu:** zero `resultado` fora do conjunto canonico em 30 dias e so 2 de 898 abertas da Bet365 sem codigo. **RISCO DA TROCA, medido antes:** a assinatura de bilhete COM codigo e' `ID|casa|parceiro|codigo` e nao inclui descricao, entao 933 das 1.021 abertas tem risco ZERO; das 88 sem codigo, 82 vieram de import (nunca releem por IA) e **sobram 5**, duas delas da base `realtrial`. As 5 foram FOTOGRAFADAS antes em `Backups/s377_sonnet5/abertas_sem_codigo_antes_da_troca.json`. **O QUE O FECA PEDIU EXPLICITAMENTE — que o custo continue medido — virou DUAS pecas, nao promessa:** o `_PRECOS` ganhou a linha do Sonnet 5 **na mesma mudanca** (sem ela o `_PRECO_PADRAO` cobraria ao preco do 4.6 e a economia de 33% NAO apareceria no log, levando a conclusao "a troca nao adiantou"), o `custo_usd` passou a **gritar** no log quando o modelo esta fora da tabela, e entrou o `scripts/medir_troca_modelo.py`, que separa o que a BARREIRA move (tokens por bilhete) do que a TROCA move (US$ por bilhete) — comparar dinheiro misturaria os dois efeitos, que e' exatamente o erro de agosto. **GATE NOVO: `tests/test_modelo_e_preco.py`, 6 mutacoes, 6 detectadas**, com **prazo de validade**: `MODELO_REVISADO_EM` + teste que quebra o CI em 90 dias. E' a unica regua que este repo conhece contra decisao congelada, e e' a mesma familia de "assinatura tem ERA" e "casa dedicada e' retrato datado". Suite 1.243 passed. **NAO TESTADO, declarado:** print e PDF (a prova foi so texto de captura; print e' 70% saida e e' tarefa de visao). **SINAL PRELIMINAR da barreira da s376**, um dia parcial e pouca chamada, entao vale como indicio: tokens por bilhete **-35,3%** contra os 7 dias anteriores, onde o previsto era -34,2%. **PENDENTE: rodar `scripts/medir_troca_modelo.py` em 27/09** e conferir as 5 linhas fotografadas.)

_Anterior: 2026-09-20 (sessao 376: **a barreira de recaptura estava MORTA desde 09/09, com o CI verde, e o defeito era uma coluna sem prefixo.** A pergunta do Feca era de custo (*"por que depois de tanto tempo controlando o custo ele esta pior?"*), e a decomposicao respondeu com nome e tamanho. **O custo por bilhete subiu 31% (R$ 0,084 -> R$ 0,110) enquanto o volume TRIPLICOU** (13.831 -> 36.736 bilhetes por IA/mes, com 11 donos pagando contra 16). Atribuido componente a componente, com o preco VIGENTE em cada janela (o `cache_write` custava 3,75 antes da s295, e usar 6,00 nas duas pontas inflaria o passado): **`cache_read` +93% da variacao**, `input` +35%, `output` +24%, `cache_write` **-52%** (a correcao A, a unica coisa que baixou custo em 27 dias). **O `cache_read` e o produto de dois fatores e os DOIS pioraram:** pedacos por chamada 3,28 -> 4,85 (o `_BILHETES_POR_CHUNK = 6` da s301, que consertou o pedaco GORDO e abriu o pedaco NUMEROSO: o pedagio do manual deixou de ser travado em 4 e virou linear no tamanho do lote) e o manual por pedaco 47,9k -> 61,2k tokens, porque os masters **cresceram 31% no periodo** (128.648 -> 168.751 bytes, medido no git). Cada secao escrita ali e paga por todo pedaco de toda chamada de todo usuario. **O CONSERTO DESTA SESSAO:** `blocos_conhecidos` faz `FROM bilhetes b JOIN bloco_visto v`, e o `_filtro_conta` acrescentava ` AND casa = $3` **sem qualificar a tabela**; as duas tem a coluna, entao vinha `AmbiguousColumnError`, que caia no `except` e devolvia `{}`. A barreira nunca pulou um bloco sequer. **O modo de falha e economia que nao acontece, e ninguem abre chamado por isso.** Provado em producao antes de tocar no codigo: 399 de 400 blocos relidos JA tinham o hash exato em `bloco_visto`. **A prova do conserto tambem foi medida, e eu descartei a primeira:** o replay de lotes antigos contra a memoria de HOJE deu 99,7% de corte e e lixo (compara cada lote com o futuro dele). Refeito em ordem cronologica, pulando so o que um lote ANTERIOR ja tinha visto: **34,2% das leituras (Bet365 39,7%)**, que bate com os 32,5%/39,9% que o plano mediu por outro caminho em 09/09. Pelo modelo do plano sao ~US$ 230/mes dos US$ 788 de hoje. **O GATE NOVO BATE NO BANCO, que e a fresta por onde isso passou:** o `test_barreira_recaptura.py` declara no cabecalho que nao toca o Postgres e que o JOIN *"tem de ser conferido contra o banco real antes de a barreira valer em producao"* — o limite foi escrito e ninguem foi fechar. Entraram dois casos no `test_repository_db.py` (CI, Postgres de teste). **Mutacao provada contra producao, read-only:** sem o prefixo a query levanta `AmbiguousColumnError`; com ele devolve o hash em 5 de 5 casos reais, e conta errada continua devolvendo vazio. `_filtro_conta` ganhou o parametro `tabela` para fechar a CLASSE, nao a instancia: quem usa uma tabela so nao passa nada. Suite 1.238 passed, `check_docs` verde. **PENDENTE, e faz parte desta tarefa, nao de uma sessao futura: medir `uso_tokens` 7 dias depois do deploy** e comparar com os 7 anteriores. Se o corte nao aparecer, o conserto nao era esse. **DUAS FRENTES QUE A DECOMPOSICAO ABRIU** (`BACKLOG 3.11` e `3.12`): por teto no numero de pedacos e orcar o crescimento do manual. **E o registro que importa mais que o conserto:** em 27 dias e ~80 sessoes desde o estudo, tudo que atacaria o custo VARIAVEL esta escrito, testado, documentado e **desligado** — o `app/tradutor.py` e importado so por um script e um teste, nunca rodou em producao. Item de custo nao se fecha mais por commit; fecha por numero medido em producao.)





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
