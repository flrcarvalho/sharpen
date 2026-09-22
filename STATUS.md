# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-22 (sessao 381: **o card de custo da Extracao gravava no preco de TABELA do fornecedor, nao na conta.** O Feca corrigiu UMA conta do Richard para R$ 916 meses atras e hoje viu que tinha mudado a tabela: o campo, rotulado "Custo · Richard", escrevia em `custo_store.custo_conta["Richard||Superbet"]`. **MEDIDO NO BANCO:** a tabela Superbet do Richard esta em **R$ 916** e **25 contas** Richard na Superbet a herdam, nenhuma com custo proprio; nao ha `fornecedor_preco` do Richard, entao o banco nao guarda o valor anterior. **CONSERTO:** o card grava `parceiros.custo` (o custo proprio da s348, que a tela de Custos ja usava e a Extracao nunca foi ligada) pela rota `POST /parceiros/{id}/custo`; a tabela aparece so como placeholder, o rotulo diz a fonte (`Custo · tabela` / `Custo · proprio`) e o title nomeia o fornecedor e o valor da tabela. Vazio devolve a conta a tabela (`null`, nunca 0). O erro aparece NO card (`Custo · erro`, em `--neg`). O parser segue a regua do `parseNum` (`179.90` e decimal, `1.200` e milhar), porque o antigo apagava todo ponto. **O index.html nao faz mais POST para `/custos/conta`**, e isso virou gate. **GATES:** `dado_digitado_sobe_sempre.mjs` secao C reescrita (rota da conta, nunca a tabela, vazio = null, zero recusado, parser); `test_nada_local_no_usuario.py` **11 mutacoes, 11 detectadas** (saíram as 3 da trava antiga da Extracao, que deixou de existir; entraram 4). **MEDIDO NA TELA** (demo, 1280/1600/2560): herdando, proprio, erro e apagado; so saem POSTs para `/parceiros/94/custo` (916 e depois null) e todos os rotulos ficam em UMA linha (a 1a versao, `Custo · tabela Norte`, quebrava e desalinhava o card). Suite 1.262 passed; o unico vermelho e o `test_landing` dos travessoes, anterior e de outra sessao. **REPARO DO DADO, APLICADO:** o Feca informou a tabela antiga (R$ 400) e nao lembra qual conta custou 916, entao a decisao dele foi *"joga tudo pra 400"*: `custo_store.custo_conta["Richard||Superbet"]` do dono Feca foi de 916 para **400** por `jsonb_set` numa transacao que conferia o 916 antes (as outras 13 chaves intactas; nenhuma das 25 contas tinha custo proprio). Sem linha em `fornecedor_preco`, de proposito: data de vigencia inventada e o que o CLAUDE.md barra. **E A RENOVACAO DE CONTA ENTROU** (pedido do Feca: o fornecedor vende X dias e, em vez de devolver, ele paga de novo, noutro valor). **Lista `parceiros.renovacoes` (JSONB, `[{id, valor, data}]`)**, porque cada renovacao e dinheiro que sai noutro DIA e cobra no mes DELA, independente da compra; rotas `POST/DELETE /parceiros/{id}/renovacoes`. **Sem prazo nem vencimento** (*"cada fornecedor trabalha de uma forma"*). **Regua:** `_custoNaJanela('pago')` cobra a compra no mes do pagamento E cada renovacao no mes dela (a regua continua SOMANDO); `'vivo'` (contas em operacao) = compra + renovacoes ja pagas ate o fim do recorte, sem as futuras (decisao dele); aba Contas soma as duas no custo da conta; tela de Custos ganha uma LINHA por renovacao (`renovacao`, sem botao de editar) e a legenda passou a dizer `N contas compradas · M renovacoes` (a 1a versao contava renovacao como conta comprada, visto no demo). **UI:** botao-icone `.cxe-edit` no card de custo da Extracao com SELO de contagem (o numero em linha estourava o card de 160px, medido) e o MESMO modal/tabela da Caixa, data pelo SharpenCal, apagar em dois cliques. **GATES:** `custo_janela_vida` +10 mutacoes (47/47; uma escapou na 1a rodada e o buraco era do TESTE: nenhum caso olhava o mes SEGUINTE a renovacao), `custos_regua_unica` +3 (13/13, tabela = KPI com renovacao), 4 ancoras antigas reescritas para a linha nova sem mudar o defeito que simulam, teste de banco novo em `test_repository_db.py` (roda so no CI; o SQL foi provado antes contra tabela TEMPORARIA de sessao em producao, sem tocar `parceiros`). **MEDIDO NO DEMO** em 1280/1600: lancar, recusar zero, `1.200` = mil e duzentos, apagar, card, tela de Custos (tabela = KPI) e contas em operacao subindo exatamente o valor lancado. Suite 1.273 passed; o unico vermelho segue o `test_landing` alheio. **E CONTA ARQUIVADA ABRE NA EXTRACAO** (pedido do Feca): a linha do Painel de Contas era clicavel so na aba Ativas porque `clic = contasTab === 'ativas'` decidia o clique E a acao (Arquivar/Reativar); agora `clic` so escolhe a acao, a linha e clicavel nas duas abas e toda acao para a propagacao. O `contasAbrir` ja procurava no `parceirosArquivadosCache`. Gate `test_painel_arquivada_abre.py` (3 mutacoes, 3 detectadas; a 1a versao do teste tinha regex errado e reprovava o arquivo BOM, pego antes das mutacoes). **A pergunta dele, "editar o valor de uma arquivada o sistema entende?", foi respondida por MEDICAO:** no demo, abrir arquivada, gravar custo 777 e renovacao 250 (as duas escritas foram para a conta certa), e o caso R6 do `custo_janela_vida` prova a regua: compra com custo proprio cobra no mes dela, renovacao no mes dela, e a arquivada fica fora das contas em operacao. **Achado lateral, NAO corrigido:** o "Tudo" da tela de Custos vai ate HOJE e o do KPI nao tem fim, entao qualquer pagamento datado no FUTURO (compra ou renovacao) aparece num e nao no outro. **E A ABA CONTAS FOI PUBLICADA (22/09), com texto numerado e FOLDER.** O Feca pediu *"uma mensagem super completa, no estilo daquela q vem com um folder"*, depois *"numerar o texto e mandar"*. Saiu em **dois envios**: o texto (message_id **4910**, 2.385 caracteres, itens 1 a 6) e o **folder de uma pagina** (**4911**), com a nota gravada em `app/changelog.json` no mesmo ato. **Dois envios porque a Bot API corta legenda de foto em 1024 caracteres** e o texto nao cabe: com `--foto` a chamada FALHARIA depois do `getChat`, que e o pior lugar para descobrir isso. A numeracao do texto casa com as chamadas da imagem. **O FOLDER e a tela REAL, nao um desenho** ([`docs/marketing/folders/contas/`](docs/marketing/folders/contas/README.md)): o script abre a aba no `servidor_demo` e troca so os VALORES no DOM, com os numeros da operacao do Feca (decisao dele) e **nomes de conta e fornecedor ficticios**, declarado no rodape da peca. **O dado do demo nao servia:** as 102 contas dele sao **todas ativas** e apostam o periodo inteiro, entao o histograma sai com quatro faixas zeradas e o painel `Ultimas contas` sem mediana -- um folder assim ensinaria a tela errado. Consertar o gerador (simular limitacao) e o caminho certo se isso virar rotina, e ficou registrado. **Tres armadilhas medidas, todas no README:** `cnToggle` **repinta** a tela e desfaz a injecao nas fichas (dai injetar duas vezes); **trocar o nome da casa nao troca o favicon**, que vem do `mkHouseChip`, e a Superbet ficou com o icone da Bet365; e o recorte da casa comeca na FICHA, porque o cabecalho `Por casa` ja e o recorte do meio. As chamadas numeradas saem de um `pos.json` **medido no DOM**, nao de chute. `BACKLOG 1.21` FECHADA. **Continua aberto e e do Feca:** conferir o card `Custo das contas` contra a tela de Custos, que e a regua canonica.)

_Anterior: 2026-09-21 (sessao 380: **eu reprovei o Haiku 4.5 com dois numeros que eram da minha bancada, nao do modelo. Reprovacao RETIRADA.** O Feca cobrou (*"descartamos muito rapidamente... 19 codigos inventados, isso assusta, mas e' mesmo?"*) e a remedicao deu: ele perde **ZERO** bilhete (300 blocos -> 300 linhas) e inventa **ZERO** codigo. Os "8,7% perdidos" eram linhas com a COLUNA comida, nao bilhete sumido, e os "19 codigos" sumiram com o parceiro real. **Dois defeitos meus, os dois no arranjo da ENTRADA:** lotes montados com bilhetes SORTEADOS de dias diferentes (producao usa blocos CONSECUTIVOS de uma extracao; bilhete parecido lado a lado e' o que faz um modelo fundir dois) e `parceiro='(nao informado)'`, que deixa a coluna 5 vazia e faz o modelo perder a conta das colunas. **A PISTA EXISTIA E EU USEI METADE:** no mesmo dia eu vi a bancada dizer 3,6% de coluna comida contra 0,2% de orfas no banco, concluir corretamente *"o defeito e' do meu harness"* — e usar isso **so para absolver o Sonnet 5**, sem voltar para reexaminar a condenacao do Haiku, que saiu da MESMA bancada no MESMO dia. Caso em `docs/CASOS.md` ("a bancada que condenou o modelo errado"): **regua nova e' codigo nao testado, e codigo nao testado nao condena ninguem; quando a regua e' desmentida uma vez, TODO veredito dela volta para a fila.** **A TABELA LIMPA (300 blocos, lotes reais, parceiro real):** perdidos Sonnet 5 **0** / Haiku **0** / Sonnet 4.6 **6** (o unico que perdeu foi o que estava em producao ate ontem); codigo inventado 0/0/0; descricao fora do MASTER 0% / **25,7%** / 0,7%; custo do mesmo teste US$ 4,83 / **0,75** / 4,91. **O UNICO bloqueio real do Haiku e' a descricao, e ela e' 97% FORMATO:** dos 37 erros, 24 sao `over-under-pt` (escreve *Mais de* onde o MASTER manda *Over*) e 12 sao `decimal-virgula`; **1** e' de conteudo. Ele entende o bilhete e escreve no dialeto errado, igual a IA fazia antes das decisoes A e B da s336. **TRES ITENS NOVOS NO BACKLOG, todos medidos:** `4.6` o normalizador de COLUNA (linha com 10 campos cujo ultimo e' codigo valido = TAB faltando; conserta orfa de QUALQUER modelo) + o de FORMATO (o `checar_descricao` ja DETECTA, falta CORRIGIR) — os dois sao pre-requisito do `3.13` e valem por si; `4.7` **print e' 3,2% dos bilhetes** (1.283 de 39.741, pelo marcador `codigo_ocr`), concentrado em **Jaao26** (28,1% dos bilhetes dele) e germano, e **o proxy `input>25k` do ESTUDO SUPERESTIMA** (acusa 43,8% da conta e pega lote grande de TEXTO junto: pelo proxy o Feca teria 107 prints de Bet365 e ele nao manda print); `4.8` **`ricardo05` gastou US$ 13,42 em 18 chamadas e gravou ZERO bilhete** — na base inteira, zero. Pagou e o `/salvar` nunca recebeu, e **isso nao tem alarme nenhum**: ninguem pergunta "houve chamada e nao houve gravacao?", e a resposta esta a um JOIN de distancia. **A RESSALVA ESTRATEGICA que decide a ORDEM:** o normalizador de descricao e' 80% do que o tradutor faz, e o tradutor custa ZERO token nas linhas que cobre contra os 0,5x do Haiku — construir o normalizador so para viabilizar o Haiku e' fazer a parte dificil e ficar com o premio pequeno. **`scripts/bancada_modelos.py` entrou no repo** (era o metodo que o `3.13` prometia e que so existia no scratchpad). **NAO MEDIDO em modelo nenhum: print e PDF.** **E UMA FALHA QUE NAO E' MINHA:** `test_landing.py::test_nenhum_travessao_no_texto` esta VERMELHO desde o `efe5b3a` — 5 travessoes entraram em COMENTARIOS da `landing.html` (linhas 266, 500, 1032, 1094, 1100). Nao toquei: e' arquivo de outra sessao aberta, e reescrever arquivo alheio foi o que apagou trabalho na s372.)







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
