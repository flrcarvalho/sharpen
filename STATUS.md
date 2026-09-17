# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-16 (sessao 369: **o custo RECONCILIOU, e nao havia defeito na regua: os dois numeros estavam certos e liam TABELAS DE PRECO diferentes.** Fecha a pendencia (a) da s366. **R$ 59.600 e a regua com o `CUSTO_SEED`** (11 pares cravados no `gestao.js`, so para o username `Feca`) e **R$ 76.600 e a mesma regua com o `custo_store`** (14 pares). As duas tabelas concordam em 10 pares e divergem em 4, e **os TRES pares de Bet365 sao identicos nelas** — que e a causa exata do sintoma que parecia aleatorio: *so a Bet365 batia* porque a Bet365 e onde as fontes concordam. **SOBROU UM RESIDUO CONSTANTE DE R$ 500, so em Superbet, presente nas DUAS medicoes — e era um SEGUNDO defeito, de outra natureza.** A conta `arthurbarbosabets`, com **13 bilhetes**, estava gravada como `arthurbarbosabets [[JC]]`, **colchete duplo**: o `_splitParceiro` parte isso como fornecedor `[JC]` (com os colchetes dentro), a chave vira `[JC]||Superbet`, que nao existe em tabela de preco nenhuma, e **o custo daquela conta simplesmente nao existia** — sem erro, sem zero visivel, sem linha faltando. Ela foi renomeada entre a s366 e hoje, e por isso a regua passou a cobrar os R$ 500. **PROVA POR REMOCAO, nao por deducao:** a `calcCostFiltered` RECORTADA do `gestao.js` de producao rodou contra um dump do Postgres real, duas vezes, uma com cada tabela; com o nome de hoje ela da 60.100 e 77.100, e **devolvendo o colchete duplo ao dump ela da 59.600 e 76.600, exatos, casa por casa**. **Quatro hipoteses anteriores tinham sido descartadas e nenhuma era a causa** — o erro de metodo foi procurar UMA explicacao para uma divergencia que tinha DUAS. **O produto ja denunciava e ninguem leu como denuncia:** a tabela de precos mostrava uma linha de fornecedor chamada `[JC]`, com *FALTA 1 PRECO · 1 casa · 1 conta*, ao lado do `JC` de verdade; fornecedor fantasma com nome quase igual a um real le como duplicata cosmetica, nao como custo sumindo. **VARRIDO DEPOIS EM 1.025 CONTAS DE TODOS OS DONOS: ZERO nomes com artefato de parse no fornecedor.** Caso unico, ja corrigido — **nenhuma mudanca de codigo**, porque inventar validacao para uma classe de incidencia zero e piorar o codigo para o teste caber. **A LICAO, que virou o sintoma no [`CASOS.md`](docs/CASOS.md#dois-numeros-certos-e-um-colchete-que-apagou-o-custo-de-13-bilhetes--s364-s366-s369):** dois numeros da mesma grandeza que diferem em algumas dimensoes e **batem exatamente em outras** nao acusam a regua, acusam a FONTE — as duas leituras concordam onde as fontes concordam. E **resto constante em cima de uma diferenca ja explicada nao e mais da mesma coisa**: e um segundo defeito, que so aparece depois que o primeiro sai. Suite 1.200 passed, `check_docs` verde, working tree limpo. **PENDENTE, e e do Feca: (a) as duas contas de fornecedor sujo** que a s366 listou seguem esperando o "pode" — `Sem dono [Sem fornecedor - Ago 2026]` (id 514, Betano, **207 bilhetes**) viraria `[Eu]`, e essa nao e cosmetica; **(b) remover o `CUSTO_SEED`**, que agora tem motivo a mais: enquanto ele existir, um dono cujo fetch de custo falhe ve a tela preenchida com numero que nao e dele.)

_Anterior: 2026-09-15 (sessao 368: **a trava que guardava custo so no navegador caiu nas TRES telas, e a regra virou lei no `CLAUDE.md`.** Regra do Feca, em termos absolutos: *"JAMAIS, JAMAIS JAMAIS DEVEMOS ARMAZENAR CUSTO OU QUALQUER INFORMACAO LOCALMENTE NOS USUARIOS"*, com *"pode fazer td q e preciso ser feito"*. **O ACHADO: a faixa da s360 recuperava o passado, mas o FUTURO continuava caindo no buraco.** `saveCusto` (`charts/gestao.js`), `ctSave` (`dash/app.js`) e `_salvarCusto` (`app/static/index.html`) tinham a mesma forma — `if(serverBacked) push; else if(!hadLegacy) push;` — e o terceiro caso, **servidor vazio + legado no navegador, nao subia NADA**. Quem estava nesse estado digitava um custo e ele ficava so na maquina, sem erro e sem aviso. **A trava tinha motivo real e ele nao sumiu:** o custo viveu anos so no `localStorage`, entao o mesmo dono pode ter conjuntos DIFERENTES em maquinas diferentes, nenhum no servidor; a maquina com menos chaves escrevendo primeiro viraria a verdade e a outra adotaria o conjunto menor na carga seguinte. **A DEFESA MUDOU DE LUGAR em vez de sumir:** o front sobe SEMPRE, e o 1o envio de um navegador para servidor sem registro manda `semear`, que **UNE** em vez de substituir. Edicao normal continua substituindo, e tem de continuar — apagar um lancamento e tirar a chave, e uniao nenhuma apaga chave. **A uniao nao e trivial nas duas estruturas, e por isso ela e Python e nao `||` de jsonb:** `custo_tipster` une **mes a mes** (unir por tipster trocaria o mapa inteiro e apagaria os meses que so existem de um lado, que e o dado que a semeadura veio salvar) e `custo_geral` une **por `id`** (concatenar lista duplicaria a linha `VPS` em vez de uni-la). O `SELECT FOR UPDATE` e o INSERT ficam na MESMA transacao: entre um e outro cabe a escrita de outra aba do mesmo dono. **MAIS DUAS VIOLACOES DA MESMA REGRA, achadas na varredura:** a tela dizia *"Valores salvos permanentemente no navegador"* (`dash/app.js`), ou seja o produto anunciava como recurso o proprio defeito; e a **carteira do Polymarket** que o usuario digita vivia so no `localStorage`, entao trocar de maquina obrigava a digitar de novo. Hoje e coluna `usuarios.poly_wallet`, servida pelo `/me` e gravada por `POST /polymarket/carteira` (por `dono_efetivo`: e configuracao da BASE, nao credencial de quem olha). **O QUE FICA no `localStorage`, de proposito:** largura de coluna, aba lembrada, painel recolhido e a marca d'agua de throttle do Polymarket. O corte e *"o usuario digitou isso?"*. **GATE NOVO: `tests/test_nada_local_no_usuario.py` + `tests/js/dado_digitado_sobe_sempre.mjs`, 10 de 10 mutacoes detectadas de primeira**, mais 7 testes das duas funcoes de uniao. O .mjs exercita os TRES saves recortados de producao nos TRES estados e exige POST em todos; recortar do `index.html` exigiu um recorte por INDENTACAO, porque ali a funcao vive dentro de `<script>` e nao tem fecho em coluna zero. **MEDIDO NO NAVEGADOR, que e o unico gate que pega crase em template literal:** Custos abre com 4 KPIs, o `saveCusto` dispara `/custos/conta` com `semear=true` **no estado exato que a trava bloqueava**, e o payload leva o legado junto (`JC||Betano` + a chave nova); a Extracao roda dentro do `#fr-plan` com `_salvarCusto`, `#poly-wallet` e `__polyWallet` de pe. Zero erro de pagina nas duas. **O `CLAUDE.md` estourou o teto ao receber a regra (66,0 de 65) e DOIS espelhos sairam, pelo criterio do invariante #10:** `Convencoes de output` -> [`RUNBOOK_FORMATO_SAIDA`](docs/RUNBOOK_FORMATO_SAIDA.md) e a TABELA de dedup -> [`RUNBOOK_DEDUP`](docs/RUNBOOK_DEDUP.md). **As subsecoes de dedup FICARAM** (orfa, codigo escrito pela IA, congelamento do UPSERT, recalculo de assinatura): elas decidem escrita, nao descrevem formato. Fechou em 64,7 KB. **O `check_docs` me pegou** apontando para um caso do `CASOS.md` que eu ainda nao tinha escrito. **E O `?v=` ME MORDEU DE NOVO, do mesmo jeito:** meu `sed` mirava `app.js?v=56`, que era o valor que eu tinha lido, e o HEAD ja estava em **59** — o sed nao casou e passaria batido se eu nao tivesse conferido o `git diff --cached` depois. Hoje em 51/60. **A licao operacional: `sed` em arquivo compartilhado confere o resultado, nunca o comando.** Suite 1.200 passed, zero vermelho (a 0.7.13 saiu pela vizinha). **PENDENTE: remover o `CUSTO_SEED`** quando os donos tiverem guardado — a query esta no BACKLOG.)

_Anterior: 2026-09-15 (sessao 367: **a sidebar do tipster mostrava numero CERTO de um instante VELHO, e o KPI ao lado mostrava o de agora.** O Feca abriu com um print do Gabriel: *"os valores da sidebar do Gabriel nao batem com os resultados dele"*. Sidebar em `+R$ 48.614,76 / +3,57%`, KPI da Visao Geral em `+R$ 50.782,00 / +3,72%`, mesma tela, mesmo dono, sem filtro nenhum ligado. **A REGUA ERA A MESMA E OS DOIS NUMEROS ESTAVAM CERTOS:** `resumo_perfil` (que serve o `/conta/perfil`) roda o mesmo `_resumir_apostas` com os mesmos filtros do `dashboard_rows`, e rodado contra a base agora ele devolve exatamente os `50.782,00 / 3,72%` do KPI. **O QUE DIFERIA ERA O INSTANTE, e deu para datar:** reconstruindo a base por `criado_em`/`atualizado_em`, os quatro valores da sidebar (mes e historico, ROI e P/L) batem na casa do centavo com o estado de **15/09/2026 14:00:45 UTC**, o momento em que a casca foi carregada. A diferenca era **identica** nas duas janelas (`R$ 2.167,24`), que e a assinatura de retrato congelado: tudo que mudou desde entao caiu no mes corrente. **A CAUSA e estrutural e estava escrita no proprio desenho:** a casca (`app/static/app.html`) nunca recarrega, de proposito (navegar e mostrar e esconder iframe), e o `fetch('/conta/perfil')` do bloco rodava UMA vez, no load. O dashboard, que vive num iframe, se atualiza por tres gatilhos (SSE `/eventos`, botao ↻ e volta de aba), todos em `executarRefresh`, que **so falava com os iframes**. Cada captura subia o KPI e deixava a sidebar para tras, sem erro em lugar nenhum. **A PONTE E UM EVENTO, `base-recarregada`**, disparado por `executarRefresh` e escutado pelo IIFE do bloco, que agora tem o `recarregarPerfil()` nomeado em vez de codigo solto. **A ORDEM dentro do `executarRefresh` e load-bearing:** o aviso sai ANTES do `if (!fila.length) return`, que dispara quando nenhum iframe tem base carregada (usuario so na Extracao); o perfil e agregado no servidor e nao depende de iframe nenhum, entao avisar depois deixaria justamente essa sessao parada. **EFEITO COLATERAL QUE A PROPRIA CORRECAO CRIOU, e ele e a parte interessante:** com `aplicar` voltando a rodar a cada recarga, o cache-bust da logo por `Date.now()` passaria a dar a ela uma URL inedita a cada repintura, request novo e piscada sem a imagem ter mudado. O carimbo virou memorizado no `pintarLogo`; quem PRECISA furar o cache (o upload) segue passando a versao explicita, e e ela que fica valendo. **Repintar algo que so era pintado uma vez exige reler o que a pintura faz de efeito colateral.** **GATE NOVO: `tests/test_sidebar_perfil_repinta.py`, 6 de 6 mutacoes detectadas** (tira o dispatch; move o dispatch para depois do early-return; tira o listener; tira a chamada de dentro do `recarregarPerfil`; acrescenta uma segunda chamada solta ao `/conta/perfil`; devolve o `Date.now()` inline na logo). O cabecalho diz o que ele NAO cobre: que a repintura aconteca no navegador. **Essa metade foi medida a parte, no Chrome**, contra o `servidor_demo`: clique real no ↻, `/conta/perfil` indo de 1 para 2 requisicoes, celulas pintadas e **zero erro de JS** (os dois 404 sao rotas que o mock nao tem). **A ARMADILHA DO `write_text` MORDEU DE NOVO**, como na s363: as mutacoes foram aplicadas por script Python e devolveram os arquivos em CRLF; pegou no `diff` contra a copia feita com `cp` antes da primeira mutacao, e os bytes foram restaurados. **Quem muta arquivo por script neste repo confere o fim de linha depois, nao so o conteudo.** Suite **1.182 passed**, `check_docs` verde. `?v=` do `sb-tipster.js` em 3, nas DUAS cascas que o carregam (`app.html` e `dash/index.html`).)



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
