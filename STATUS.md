# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-10 (sessao 341: **duas frentes pedidas pelo Feca, e as duas expuseram PROPAGACAO INCOMPLETA por baixo.** (1) **Renomear tipster** na tela Tipsters & Metodos. A rota `POST /tipsters/{id}/renomear` existia desde sempre e **nunca teve botao** — e propagava a **3 das 6** referencias. O tipster nao tem id em lugar nenhum: seis tabelas o apontam pelo NOME, e as tres esquecidas falhavam **em silencio**. `casa_config.tipsters` (CSV) deixava a casa dedicada apontando para um nome inexistente e **o matcher parava de cravar**; `custo_store.custo_tipster` (chave de JSONB) mantinha o custo **cobrado no KPI e sumido da tabela onde se lanca** (familia do "tipster cobrado e ineditavel", s274); e `polymarket_ativos_tipster`. Mais a **7a ponta, na rota**: `matcher.invalidar(dono)`, senao o modelo cacheado sugere o nome velho e o `/bilhetes/tipster` o **regrava** na base recem-renomeada. Tres decisoes: o CSV troca o **ELEMENTO**, nunca a substring ("Ze" vive dentro de "Ze Turbo"); no custo os meses se fundem com a **ORIGEM vencendo**, porque so ela tem tipster vivo por tras; e o `DELETE` das colidentes da escada vem **ANTES** do `UPDATE`, senao `UNIQUE (dono, tipster, vigente_desde)` derruba a rota com 500. A contagem do modal vem de `GET /tipsters/{id}/resumo`, que conta na **MESMA clausula que o UPDATE usa** — regua do `resumo_parceiro`; se ela falhar, o modal **diz que nao conseguiu contar** em vez de mostrar um numero do feed cacheado com cara de conferido. **12 de 12 mutacoes detectadas**, e a 10a **ESCAPOU na 1a rodada por dado sintetico frouxo**: eu usei "Peixe" x "Peixinho" para provar "conta por elemento, nao por substring", e **"Peixe" nao e substring de "Peixinho"** (e Peix-I-nho); o par virou "Peixe" x "Peixe Turbo". (2) **Editar apostas em massa** nas 3 telas (Extracao, Base Completa, Em Aberto), com Data, Resultado, Tipster, Esporte, Casa, Parceiro e Aposta — stake, odd e descricao ficam de fora de proposito. `POST /bilhetes/lote` chama o **MESMO miolo de uma edicao so**, id a id (`_atualizar_bilhete_conn`, extraido do `atualizar_bilhete`): o atalho `UPDATE ... WHERE id = ANY(ids)` pularia **assinatura**, `extraction_state`, `origem_tipster` e `correcoes`, e assinatura velha **nao da erro** — so faz a proxima captura da casa nao deduplicar e **duplicar o historico** (s198/s312). Num lote de 300 linhas e 300 vezes o mesmo defeito, e a **mutacao 1 do gate e justamente esse atalho**. Aplicacao **POR LINHA**, sem tudo-ou-nada, com `atualizados` + `ignorados` na resposta (regua do `/salvar`, que grava as boas e devolve as recusadas): tudo-ou-nada trocaria 297 edicoes boas por zero por causa de 3 ids que nao sao do dono. Campo **AUSENTE = nao mexe**, string **VAZIA = LIMPA** — sao coisas diferentes e o front manda campo a campo em vez de inferir por "esta vazio". `flags_pos_edicao_lote` devolve **CONTAGEM, nao booleano**: "algumas podem ser desfeitas" sem dizer quantas vira caca manual numa selecao de 300 linhas. A selecao vive num **Set FORA do DOM** porque a Base Completa e virtualizada, e a coluna nova mexeu na grade posicional (`BTBL_W_KEY` para v3; celula VAZIA, nunca ausente, na vitrine publica). **10 de 10 mutacoes detectadas.** **UI:** `shConfirm()` no dash substitui o `confirm()` nativo — a faixa branca no topo do navegador vira modal **centrado com o lockup do Sharpen**, e erro de servidor aparece **DENTRO** do modal, com o texto digitado intacto. **Gates:** 829 passed / 36 skipped, `check-tokens` verde, e as 4 telas **renderizadas headless** antes do commit (cabecalho e linha com o mesmo numero de celulas e colunas alinhadas ao pixel — 11 e 11 na Base, 10 e 10 nas Abertas —, modal centrado, botao travado com o campo vazio, zero erro de console). **Fica aberto (BACKLOG §4):** `var(--text1)` nao existe em token nenhum, com 4 usos no `dash/assets/js/app.js`; e `@app.post("/tipsters/sugerir")` esta registrado **duas vezes** em `app/main.py`, com a segunda inalcancavel. Outra sessao rodou em PARALELO nesta noite.)

_Anterior: 2026-09-09 (sessao 339: **o mes do Ctrl Alt Green fechava negativo porque a captura datava 8 vitorias em AMANHA.** Relato do Feca as 22:50 de 09/09, com duas perguntas que eram o MESMO defeito: "o resultado nao parece atualizado" e "por que voce finalizou apostas com 10/09?". As 8 linhas estavam no banco, todas `W`, somando **+R$ 928,00** — mas datadas de **10/09**, um dia que ainda nao tinha chegado. O MTD recorta `[1o do mes, hoje]` (`filters.js`, `st.dt = today`), entao bilhete datado de amanha cai fora da conta do mes: com elas dentro o mes vai de **-R$ 892,87 para +R$ 35,02** (medido no banco DEPOIS do reparo: 137 apostas, exatamente as 129 da tela mais as 8), ou seja **o filtro trocava o SINAL do resultado**. **A causa:** `_dataFimB3` somava ao kickoff uma "folga de encerramento" por esporte (`_OFF_B3`: 2,5 h em basquete, 3 h em tenis) para estimar a liquidacao. eBasket chega da bet365 como `CL=18` — Basquete, porque a casa nao separa os dois; quem separa e o `_e_ebasket` do `app/tradutor.py`, pelo handle do gamer nos dois lados — e levava **2,5 h de folga num jogo que dura ~4 minutos**. **A assinatura, medida:** as 8 foram capturadas entre 22:30 e 22:40 e as 8 ganharam data +1; nenhum dos outros 397 eBasket da base, fora dessa faixa de horario, foi deslocado. **A escala:** todo esporte tinha folga, entao havia uma janela diaria de ~21h a meia-noite. Piso medido (data = dia da captura + 1, capturado depois das 21h): **188 linhas** da Bet365 (73 Multiplos, 54 Futebol, 37 Badminton, 8 Basquete, 8 eBasket, 5 Tenis, 2 Dardos, 1 E-Sports) — e e PISO, porque quem foi capturado no lote da manha seguinte carrega o mesmo deslocamento e o banco nao guarda o kickoff para conferir. **Por que sobreviveu tanto tempo:** o efeito no KPI se desfaz sozinho (amanha 10/09 entra no MTD), so o DIA errado fica — defeito que se apaga da tela toda madrugada nao vira reclamacao, vira desconfianca difusa. **Decisao do Feca: `Data = kickoff`, para todos os esportes** — e o que a tela da bet365 mostra, o que as outras casas gravam e a unica data que o payload tem. A conversao UK->Brasilia NAO e a folga e continua obrigatoria (hora de parede de Londres). O rotulo do bloco virou `Data (evento):`, que ja era o das outras casas de API. **Gate novo** (bloco 9 do `extensor/harness/casos/bet365.mjs`), **provado por 5 mutacoes** — e a 3a ESCAPOU na primeira rodada: fixar `ukToBr = 4` deixava tudo verde porque nos casos escolhidos a diferenca entre UK-3 e UK-4 caia dentro do MESMO dia. O horario de verao britanico so troca o dia na faixa **03:00-04:00 UK**, entao foram precisos um caso em janeiro e outro em julho, ambos as 03:30, para prender o erro nos dois sentidos. **Reparo aplicado:** `scripts/corrigir_data_folga_s339.py` (ensaio por padrao) corrigiu as 8 linhas do Ctrl Alt Green e registrou cada uma em `correcoes`; a prova de que a data certa e o dia da captura e que a linha entrou no banco **ja resolvida**, e bilhete so resolve depois de o evento acabar. Harness 27 casos / 436 bilhetes verde. **Fica aberto (BACKLOG 1.6 e 1.8):** o `CLAUDE.md` ESTOUROU o teto (65,4 contra 65) e nao ha mais duplicacao para mover — qual regra sai e decisao do Feca; e sobraram **21 linhas ARQUIVADAS** ja resolvidas com data no futuro, de outros tipsters, que o reparo nao tocou porque filtra `archived = FALSE` e o escopo aprovado foi um tipster so. Outra sessao rodou em PARALELO nesta noite.)

_Anterior: 2026-09-09 (sessao 338: **a Blaze duplicando bilhete, e a causa nao era a Blaze: era a PROCEDENCIA do codigo.** Relato do Jonathan: "a blaze ta puxando bet duplicada, tinha feito isso ontem com prints e agora com a extensao". Medido no banco ANTES de tocar em codigo: o bilhete do Susanto (31/08) estava **5 vezes** na base dele, com **5 codigos diferentes**, um deles gravado literalmente como `270625314492244...` e outros dois com espaco no meio do numero. **Nao e defeito da captura: a Blaze so entrou na captura nesta mesma noite** (commit `d3f2233`, 19:24), entao 100% do que estava no banco veio de PRINT. O discriminador foi o `uso_tokens.n_itens`, que conta imagens + blocos de texto: toda extracao de Blaze anterior tem `n_itens` de imagem, e so a de 20:43 e texto. **O id do BetBy tem 19 digitos e a IA lendo o card erra quase sempre:** 53 dos 55 codigos de Blaze no banco tem comprimento errado (17, 18, 20, 21). Para comparar, Betboom (77 de 77) e Jonbet (18 de 18), que so entram por captura, acertam os 19 digitos em 100%. **Como o codigo entra na assinatura, cada leitura vira um bilhete novo** e o pre-dedup por codigo nunca casa: ao ligar a extensao, o historico inteiro da casa duplicaria. Nao e so o Jonathan (germano tem 20 linhas assim, Jaao26 uma). **Tres frentes.** (1) A coluna `codigo_ocr` carrega a PROCEDENCIA do codigo, decidida no servidor (o `/extrair` e quem sabe se o lote tinha imagem) e transportada pelo front ate o `/salvar`. A formula do ON CONFLICT e um **AND das duas pontas**, entao a confianca so DESCE: basta uma leitura confiavel para o codigo deixar de ser suspeito, e nenhum print o rebaixa de volta. O backfill da Blaze e **deterministico, nao heuristico**: toda linha criada antes do deploy da captura veio de print porque nao existia outro caminho. (2) A **Migracao B'** do UPSERT adota essa linha quando o mesmo bilhete volta pela captura com o codigo verdadeiro, em vez de inserir a sexta. Duas travas que a Migracao B nao tem, porque aqui o candidato CARREGA um codigo e adotar o errado nao duplica, **sequestra** a identidade de outro bilhete: candidato UNICO, e o indice so e montado quando o lote que chega e confiavel (print nao adota print). (3) `scripts/reparar_duplicatas_codigo_ocr.py` une o que ja esta duplicado: ensaio por padrao, escolha pelo valor **MODAL** de stake e odd (com N leituras do mesmo card, a moda e a melhor estimativa que o banco tem, e isso importa porque o UPSERT congela stake/odd em linha resolvida), e snapshot em `lixeira_bilhetes` pelo `DELETE ... RETURNING to_jsonb`, uma operacao so. **Gates:** 789 passed / 36 skipped, **7 de 7 mutacoes detectadas** (`scripts/mutar_codigo_ocr.py`), 6 testes de ponta a ponta no harness de DB, `check-tokens` e `audit_sharpenup` verdes.)



> **Histórico completo das sessões 332 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 341)

### As duas frentes que o Feca pediu, e a propagação incompleta que as duas expuseram

Pedido em uma mensagem: **selecionar várias apostas e editar em massa** (não só o tipster),
e **renomear o tipster** na página Tipsters & Métodos, com uma tela de confirmação da marca
no meio da tela, não a faixa branca do navegador.

As duas entraram. E as duas encontraram, por baixo, o mesmo tipo de defeito: **uma
referência que ficou para trás e não dá erro nenhum**.

### 1. Renomear tipster: a rota existia, o botão não, e faltavam 3 das 6 pontas

`POST /tipsters/{id}/renomear` está no repo desde sempre e **nunca teve interface**. Pior:
ela propagava para `tipsters`, `bilhetes` e `tipster_unidade`, e deixava três de fora.

O tipster **não tem id em lugar nenhum**. Seis tabelas o referenciam pelo **nome**:

| Ficava para trás | O que quebrava, sem erro |
|---|---|
| `casa_config.tipsters` (CSV) | a casa dedicada aponta para um nome inexistente e **o matcher para de cravar** |
| `custo_store.custo_tipster` (chave de JSONB) | o custo segue **cobrado no KPI e sumido da tabela onde se lança** (s274) |
| `polymarket_ativos_tipster` | a atribuição das posições ativas |

E uma sétima ponta que não é tabela: **`matcher.invalidar(dono)` na rota**. Sem ela o
modelo em cache guarda o nome velho e o `/bilhetes/tipster` o **regrava** na base
recém-renomeada.

Três decisões que valem repetir:

- o CSV troca o **elemento**, nunca a substring — `Zé` vive dentro de `Zé Turbo`;
- no custo os meses **se fundem com a origem vencendo**: chave com o nome novo só pode ser
  órfã (é UNIQUE), e quem tem tipster vivo por trás é a origem;
- o `DELETE` das colidentes da escada vem **antes** do `UPDATE`. `tipster_unidade` é
  `UNIQUE (dono, tipster, vigente_desde)` e um degrau órfão no destino derrubaria a rota
  com 500.

A contagem do modal (`34 apostas`) vem de `GET /tipsters/{id}/resumo`, que conta na **mesma
cláusula que o UPDATE usa** — a régua do `resumo_parceiro`. Se ela falhar, o modal **diz que
não conseguiu contar**, em vez de mostrar um número do feed cacheado com cara de conferido.

### 2. Editar em massa: o atalho tentador era o defeito

O `UPDATE ... WHERE id = ANY(ids)` pularia, em silêncio, a **assinatura** (`casa`,
`parceiro`, `data` e `aposta` estão em `_SIG_COLS`), o `extraction_state`, o
`origem_tipster` e o registro em `correcoes`. Assinatura velha não dá erro: só faz a próxima
captura da casa não deduplicar e **duplicar o histórico inteiro** (s198/s312). Num lote de
300 linhas é 300 vezes o mesmo defeito — e é exatamente a **mutação 1** do gate.

Então o lote chama o **mesmo miolo de uma edição só**, id a id, numa conexão só
(`_atualizar_bilhete_conn`, extraído do `atualizar_bilhete`: uma implementação, não duas).

Aplicação **por linha**, sem tudo-ou-nada, com `atualizados` + `ignorados` na resposta —
mesma régua do `/salvar`. Tudo-ou-nada trocaria 297 edições boas por zero por causa de 3 ids
que não são deste dono.

**Campo ausente = não mexe; string vazia = limpa.** São coisas diferentes, e o front manda
campo a campo (o tique de cada linha do modal) em vez de inferir por "está vazio" — senão
não há como apagar um tipster errado em massa.

A seleção vive num **Set fora do DOM**: a Base Completa é virtualizada e um checkbox marcado
que rola para fora da janela seria perdido sem erro nenhum.

### 3. A tela de confirmação da marca

`shConfirm()` (`dash/assets/js/app.js`) substitui o `confirm()` nativo: abre no meio da tela,
com o lockup do Sharpen, sobre o mesmo véu dos outros modais. Erro do servidor aparece
**dentro** do modal, com o texto digitado intacto — uma recusa como "já existe um tipster com
esse nome" não pode obrigar a refazer tudo.

### Gates

- `tests/test_renomear_tipster.py` — 16 testes, **12 de 12 mutações detectadas**.
- `tests/test_editar_lote.py` — 16 testes, **10 de 10 mutações detectadas**.
- 829 passed / 36 skipped · `check-tokens` verde.
- As 4 telas **renderizadas headless** antes do commit: cabeçalho e linha com o mesmo número
  de células e colunas alinhadas ao pixel (11 e 11 na Base, 10 e 10 nas Abertas), modal
  centrado, botão travado com o campo vazio, zero erro de console.

> **A mutação que escapou, e por quê.** Na 1ª rodada do gate do rename, a mutação "conta a
> casa por substring em vez de por elemento" passou verde. O dado sintético é que estava
> frouxo: eu usara `Peixe` × `Peixinho`, e **`Peixe` não é substring de `Peixinho`** (é
> Peix‑**i**‑nho). O par virou `Peixe` × `Peixe Turbo`. É a família "o dado sintético não
> exerce a regra", do `CLAUDE.md`.

### Fica aberto

Duas dívidas achadas de lado, registradas no [`BACKLOG.md`](BACKLOG.md) §4 e **não mexidas**
(mudança própria): `var(--text1)` não existe em token nenhum e tem 4 usos no
`dash/assets/js/app.js`; e `@app.post("/tipsters/sugerir")` está registrado **duas vezes** em
`app/main.py`, com a segunda inalcançável.

## Sessão 339 — o mês que fechou negativo porque a folga datou 8 vitórias em amanhã

### O mês que fechava negativo porque a captura datava 8 vitórias em "amanhã"

**22:50 de 09/09/2026.** O relatório do tipster `Ctrl Alt Green` mostrava **MTD −R$ 892,87**
e a grade trazia oito apostas de eBasket datadas de **10/09** — um dia que ainda não tinha
chegado. Duas perguntas na mesma mensagem, *"o resultado não parece atualizado"* e *"por que
você finalizou apostas com 10/09?"*, e **era o mesmo defeito nas duas**.

As 8 estavam no banco, todas `W`, somando **+R$ 928,00**. O MTD recorta `[1º do mês, hoje]`
(`filters.js`, `st.dt = today`), então bilhete datado de amanhã cai fora. Com elas dentro o
mês vai para **+R$ 35,13**: o filtro trocava o **sinal** do resultado.

### A causa: uma folga que estimava um instante que a casa não informa

`_dataFimB3` somava ao kickoff uma folga de encerramento por esporte (`_OFF_B3`), para
estimar a liquidação. eBasket chega da bet365 como `CL=18` — **Basquete**, porque a casa não
separa os dois; quem separa é o `_e_ebasket` do `app/tradutor.py`, pelo handle do gamer nos
dois lados — e levava **2,5 h de folga num jogo que dura ~4 minutos**.

A assinatura bate: as 8 foram capturadas entre **22:30 e 22:40** e as 8 ganharam data +1.
Nenhum dos outros 397 eBasket da base, fora dessa faixa de horário, foi deslocado.

| Esporte (Bet365) | linhas com data = dia da captura + 1, capturadas após 21h |
|---|---|
| Múltiplos | 73 |
| Futebol | 54 |
| Badminton | 37 |
| Basquete | 8 |
| eBasket | 8 |
| Tênis · Dardos · E-Sports | 8 |
| **total** | **188** |

É **piso**, não total: quem foi capturado no lote da manhã seguinte carrega o mesmo
deslocamento e não entra nessa conta, porque o banco não guarda o kickoff para conferir.

> **Por que sobreviveu tanto tempo:** o efeito no KPI se desfaz sozinho — amanhã 10/09 entra
> no MTD e o número "conserta". O que não se desfaz é o **dia errado**. Um defeito que se
> apaga da tela toda madrugada não vira reclamação, vira desconfiança difusa.

### A decisão: `Data = kickoff`, para todos os esportes

Do Feca. É o que a tela da própria bet365 mostra, o que as outras casas gravam e a única data
que o payload realmente tem. Um jogo que começa 22:00 do dia 09 e termina 00:30 do dia 10 é
do dia 09. A **conversão UK→Brasília não é a folga** e continua obrigatória (o payload traz
hora de parede de Londres). O rótulo do bloco virou `Data (evento):`, que já era o das outras
casas de API — o tradutor casa a chave por prefixo, então nada mais precisou mudar.

Regra em `CASA_BET365 §4` e no `CLAUDE.md`; o caso em [`docs/CASOS.md`](docs/CASOS.md).

### O gate, e a mutação que passou verde

Bloco 9 do `extensor/harness/casos/bet365.mjs`, **provado por 5 mutações**. A terceira
**escapou na primeira rodada**: fixar `ukToBr = 4` (ignorar o GMT do inverno britânico)
deixava tudo verde, porque nos casos escolhidos a diferença entre UK−3 e UK−4 caía **dentro
do mesmo dia**. O horário de verão britânico só troca o **dia** na faixa **03:00–04:00 UK**,
então foram precisos um caso em janeiro e outro em julho, ambos às 03:30, para prender o erro
**nos dois sentidos** — com um só, metade do defeito passa.

É o segundo modo de falso verde do `CLAUDE.md` ("o dado sintético não exerce a regra")
aparecendo num teste escrito **na mesma sessão** que a regra.

### O reparo

`scripts/corrigir_data_folga_s339.py`, ensaio por padrão. Corrigiu as **8 linhas** do
Ctrl Alt Green e registrou cada uma em `correcoes`. A prova de que a data certa é o dia da
captura, e não um palpite: a linha entrou no banco **já resolvida**, e bilhete só resolve
depois de o evento acabar — logo o evento é anterior à captura.

Quatro travas, todas fail-closed: só linha **com código** (sem código a `data` entra na
assinatura), só onde a data é posterior ao dia da captura, pula bilhete com correção humana
em `data`, e escopo explícito obrigatório (`--dono` + `--tipster`).

O UPSERT congela `data` em linha resolvida, então **recapturar não conserta** o que já está
gravado. Foi por isso que precisou de script.

### O que ficou aberto, e o próximo passo

**Medido depois do reparo:** o MTD do Ctrl Alt Green fechou em **+R$ 35,02** com 137 apostas,
que são exatamente as 129 da tela mais as 8 recuperadas. O delta previsto e o medido batem.

1. **`CLAUDE.md` estourou o teto** (65,4 contra 65). Não há mais duplicação para mover, e isso
   foi medido: zero frases longas repetidas entre ele e o `CASOS.md`. Fechar significa escolher
   qual regra sai, e é curadoria do Feca. → `BACKLOG.md 1.6`, que já traz o candidato
   (`## Convenções de output`, espelho declarado do `MASTER_OUTPUT`).
2. **Sobraram 21 linhas arquivadas**, já resolvidas, ainda datadas no futuro, de outros
   tipsters (Coxadoido, Fatuch, Perereca NFL, MarcoF1 e outros). O script filtra
   `archived = FALSE` e o escopo aprovado foi um tipster só. → `BACKLOG.md 1.8`.
   **Próximo passo:** rodar o ensaio com o escopo que o Feca autorizar.

> Cuidado ao ler o item 2: das 43 arquivadas com data no futuro, 22 estão ABERTAS e são
> legítimas — aposta aberta em evento de amanhã tem data futura por direito. Só as 21
> **resolvidas** é que são impossíveis.

---

## Sessão 338 — a Blaze e a procedência do código

### A Blaze duplicando bilhete, e a causa não era a Blaze

O relato do Jonathan: *"a blaze ta puxando bet duplicada, tinha feito isso ontem com
prints e agora com a extensao"*. A causa não é a captura nova: é **quem leu o número do
código**.

O `codigo_bilhete` entra na assinatura (`ID|casa|parceiro|codigo`), então um dígito trocado
é um bilhete NOVO. Só que ele nem sempre vem da mesma fonte:

| Fonte | De onde sai o código | Acerto medido |
|---|---|---|
| captura (texto do robô) | `[Código: …]`, exato da API | Betboom 77/77, Jonbet 18/18 |
| print (imagem) | a IA lê o número no card | Blaze **2 de 55** |

Na base do Jonathan o mesmo bilhete estava **5 vezes**, com 5 códigos diferentes:

```
Susanto, Yulia Yosephine · 31/08 · stake 200 · odd 1,85 · W
  #212907 [20] 27063531449244906924   01/09   print
  #216590 [19] 2706253144924498034    02/09   print
  #218223 [18] 270625314492244...     03/09   print   ← a IA escreveu as reticências
  #257345 [20] 27062531440244968824   09/09   print
  #258494 [19] 2706253144924496624    09/09   print
```

**Nada disso veio da extensão.** A Blaze entrou na captura nesta mesma noite (`d3f2233`,
19:24), e o discriminador é o `uso_tokens.n_itens`, que conta imagens + blocos de texto:
toda extração de Blaze anterior é de imagem, e só a de 20:43 é texto. Foi ela que o
Jonathan viu duplicar na tela, e ele parou antes de salvar (nenhuma linha nova entrou).

### O que mudou

**1. A procedência do código passa a existir** (`bilhetes.codigo_ocr`). Quem decide é o
servidor, no `/extrair`, que é quem sabe se o lote tinha imagem; o front só transporta o
flag até o `/salvar`. A fórmula do `ON CONFLICT` é um **AND das duas pontas**, então a
confiança só desce: uma leitura confiável limpa o código para sempre, e nenhum print o
rebaixa de volta. O backfill da Blaze é **determinístico**, não heurístico: linha criada
antes do deploy da captura veio de print porque não existia outro caminho.

**2. A Migração B' adota em vez de duplicar.** Quando o bilhete volta pela captura com o
código verdadeiro, a linha antiga é adotada (código novo + assinatura nova + `codigo_ocr`
limpo). Duas travas que a Migração B não precisa ter: **candidato único** e **índice só com
lote confiável**. O motivo é que o candidato daqui CARREGA um código próprio, então adotar
o errado não duplica, sequestra a identidade de outro bilhete.

**3. O que já está duplicado sai pelo script**, com olho humano:
`scripts/reparar_duplicatas_codigo_ocr.py` (ensaio é o padrão). Ele agrupa por descrição
normalizada, mostra o P/L de cada linha e escolhe pelo valor **modal** de stake e odd, que
importa porque o UPSERT congela stake/odd em linha resolvida: o valor da linha que fica é o
que permanece. Saída para `lixeira_bilhetes`, pelo `DELETE … RETURNING to_jsonb` numa
operação só.

### Aplicado em produção

A migração marcou as **55** linhas de Blaze e o reparo moveu **4** para `lixeira_bilhetes`:
o grupo do Susanto, na conta do Jonathan, que eram **R$ 679,62 de lucro que nunca existiu**.
Quatro leituras concordavam em 200,00 / 1,85 e uma divergia, então a moda decidiu sozinha.
O ensaio agora devolve `0 grupo(s) duplicado(s)`, e sobrou **candidato único** para a
Migração B' adotar quando a captura passar.

germano (20 linhas com código torto) e Jaao26 (1) **não** tinham duplicata: leram cada
bilhete uma vez só. Código errado não é duplicata, é dívida esperando a captura.

### Gates

| Gate | Resultado |
|---|---|
| `pytest tests/` | 789 passed / 36 skipped |
| `python scripts/mutar_codigo_ocr.py` | **7 de 7** mutações detectadas |
| `tests/test_repository_db.py` | 6 casos novos de ponta a ponta (só no CI) |
| `check-tokens` · `audit_sharpenup` | verdes |

O que os testes de forma **não** cobrem está escrito no cabeçalho deles: adotar, recusar o
ambíguo e não rebaixar o confirmado exigem Postgres e vivem no harness de DB.

---

## Sessão 337 — a Blaze na captura

### Blaze: a terceira casa BetBy, e o degrau de odd que ela expôs nas outras duas

Detalhes em [`casas/CASA_BLAZE.md`](casas/CASA_BLAZE.md). O espelho foi **provado antes de
escrever código e sem login**: `/pt/sports` carrega `blaze.sptpub.com/bt-renderer`, e o
tráfego sai em `api-31-sp-c7818b61-584` — **mesmo cluster e mesmo hash de operador da
Jonbet**. Zero arquivo de captura novo: reusa `jb_inject.js`, `formatTicketJB` e
`roboJBPassive`.

Varredura ao vivo de **165 bilhetes** (`status` vazio), com 5 cards lidos verbatim na tela.

### O achado que muda código: a odd que a casa NÃO tem

`total_k` veio `"0"` em **86 de 86 perdidas** — a armadilha conhecida da família. A nova é
que **em 4 dessas 86 o `k` também vem zero**, e a odd só existe dentro da seleção.

E o card concorda com a API: a linha **"Total de odds" aparece VAZIA**. A casa também não
tem o número, e não escreve zero nenhum.

Parar no `k` gravaria `0` numa coluna Odd. É a família do *"zero não é ausência"*: o `0`
passa em toda checagem de forma porque tem cara de conta feita — e num bilhete **ganho**
faria `stake × (0 − 1)` virar `−1u`. O `_oddDeclJB` ganhou um terceiro degrau:

```
total_k, se ≠ 0  →  k, se ≠ 0  →  produto das seleções, se todas > 0  →  null (nunca 0)
```

**Conserta as três casas de uma vez.** E o degrau só pode disparar com os dois campos
zerados: em `refund`/`canceled` a casa achata a odd para **1** e ali o `1` é a verdade da
tela — o produto das pernas (2,5 · 1,5) seria invenção nossa por cima do card. O caso do
harness trava os **dois** lados.

### O que a paginação ensinou

Pedi `limit=100` e a Blaze devolveu **21 por página**, oito páginas, `count` constante em
165. A casa **ignora o `limit` pedido**. Quem avança o `skip` pelo que pediu pula 79
bilhetes por página; o loop do `jb_inject` só não quebra porque avança pelo tamanho que
**voltou**.

### Gates, e as duas coisas que eles pegaram

| Gate | Resultado |
|---|---|
| `node extensor/harness/run.mjs` | verde — 27 casos, **436 bilhetes** |
| `python tools/audit_sharpenup.py` | sem FAIL |
| `python tools/audit_casas.py` | limpo |
| `pytest tests/` | 773 passed (as falhas restantes são da s336, em curso noutra sessão) |

O `audit_casas` **pegou uma categoria que eu inventei**: `Placar Exato` não existe no
`MASTER_APOSTAS §3`. Virou `Outros ⚠️` mais um item de feedback no rodapé do arquivo da
casa — criar categoria é decisão do Feca e arrasta a propagação inteira.

E a **mutação foi provada nos dois sentidos**: o gate nasceu **vermelho** no bilhete certo
e, com o produto vencendo sempre, acende 7 falhas — 2 delas exatamente nos `V`. A mesma
mutação passa **inócua** na Jonbet e na Betboom: espelho compartilha o conserto, não
compartilha a prova.

### O que NÃO está coberto (medido, e escrito no cabeçalho do caso)

A conta não tinha **aposta aberta**, **cashout**, **boost**, **freebet** nem **sistema**
(`combinations` vazio em 165 de 165). E 3 dos 8 valores esperados vieram do corpo da
resposta, não do card: os bilhetes de março estão ~100 posições abaixo na lista e o filtro
"Personalizado" da casa travou carregando nas duas tentativas.

**Descoberta de lado:** o BetBy da Blaze renderiza dentro de um **shadow root** —
`document.body.innerText` traz 2,9 KB de casca e nenhum bilhete. Casa assim nunca pode ter
fallback de texto: o robô genérico não falharia, ele mandaria a casca para a IA.

**Pendente:** a validação ao vivo (recarregar a extensão, Ctrl+Shift+R na aba da Blaze e
capturar), que só o operador faz.

### Duas sessões, um index: os registros de `app/main.py` foram levados pela s336

Aconteceu de novo o [caso 8](docs/CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026),
e desta vez a favor: os dois registros da Blaze em `app/main.py` (`_CASA_DISPLAY` e
`_CASAS_MARCADOR_CODIGO`) entraram no commit `2143c06` da s336, que estava com o arquivo
para a Fase 1 da barreira. **Histórico já enviado não se reescreve** — fica registrado aqui
e segue. O resto dos 12 pontos veio no commit desta sessão.

Vale a lição inversa da regra: quando o arquivo é o MESMO, `git add` por nome não separa
nada. Antes de editar `main.py` com outra sessão aberta, o barato é combinar quem leva.

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
