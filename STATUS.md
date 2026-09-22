# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-22 (sessao 381: **o card de custo da Extracao gravava no preco de TABELA do fornecedor, nao na conta.** O Feca corrigiu UMA conta do Richard para R$ 916 meses atras e hoje viu que tinha mudado a tabela: o campo, rotulado "Custo · Richard", escrevia em `custo_store.custo_conta["Richard||Superbet"]`. **MEDIDO NO BANCO:** a tabela Superbet do Richard esta em **R$ 916** e **25 contas** Richard na Superbet a herdam, nenhuma com custo proprio; nao ha `fornecedor_preco` do Richard, entao o banco nao guarda o valor anterior. **CONSERTO:** o card grava `parceiros.custo` (o custo proprio da s348, que a tela de Custos ja usava e a Extracao nunca foi ligada) pela rota `POST /parceiros/{id}/custo`; a tabela aparece so como placeholder, o rotulo diz a fonte (`Custo · tabela` / `Custo · proprio`) e o title nomeia o fornecedor e o valor da tabela. Vazio devolve a conta a tabela (`null`, nunca 0). O erro aparece NO card (`Custo · erro`, em `--neg`). O parser segue a regua do `parseNum` (`179.90` e decimal, `1.200` e milhar), porque o antigo apagava todo ponto. **O index.html nao faz mais POST para `/custos/conta`**, e isso virou gate. **GATES:** `dado_digitado_sobe_sempre.mjs` secao C reescrita (rota da conta, nunca a tabela, vazio = null, zero recusado, parser); `test_nada_local_no_usuario.py` **11 mutacoes, 11 detectadas** (saíram as 3 da trava antiga da Extracao, que deixou de existir; entraram 4). **MEDIDO NA TELA** (demo, 1280/1600/2560): herdando, proprio, erro e apagado; so saem POSTs para `/parceiros/94/custo` (916 e depois null) e todos os rotulos ficam em UMA linha (a 1a versao, `Custo · tabela Norte`, quebrava e desalinhava o card). Suite 1.262 passed; o unico vermelho e o `test_landing` dos travessoes, anterior e de outra sessao. **O reparo do DADO e a renovacao (proximo passo) estao no `BACKLOG 1.22`.**)

_Anterior: 2026-09-21 (sessao 380: **eu reprovei o Haiku 4.5 com dois numeros que eram da minha bancada, nao do modelo. Reprovacao RETIRADA.** O Feca cobrou (*"descartamos muito rapidamente... 19 codigos inventados, isso assusta, mas e' mesmo?"*) e a remedicao deu: ele perde **ZERO** bilhete (300 blocos -> 300 linhas) e inventa **ZERO** codigo. Os "8,7% perdidos" eram linhas com a COLUNA comida, nao bilhete sumido, e os "19 codigos" sumiram com o parceiro real. **Dois defeitos meus, os dois no arranjo da ENTRADA:** lotes montados com bilhetes SORTEADOS de dias diferentes (producao usa blocos CONSECUTIVOS de uma extracao; bilhete parecido lado a lado e' o que faz um modelo fundir dois) e `parceiro='(nao informado)'`, que deixa a coluna 5 vazia e faz o modelo perder a conta das colunas. **A PISTA EXISTIA E EU USEI METADE:** no mesmo dia eu vi a bancada dizer 3,6% de coluna comida contra 0,2% de orfas no banco, concluir corretamente *"o defeito e' do meu harness"* — e usar isso **so para absolver o Sonnet 5**, sem voltar para reexaminar a condenacao do Haiku, que saiu da MESMA bancada no MESMO dia. Caso em `docs/CASOS.md` ("a bancada que condenou o modelo errado"): **regua nova e' codigo nao testado, e codigo nao testado nao condena ninguem; quando a regua e' desmentida uma vez, TODO veredito dela volta para a fila.** **A TABELA LIMPA (300 blocos, lotes reais, parceiro real):** perdidos Sonnet 5 **0** / Haiku **0** / Sonnet 4.6 **6** (o unico que perdeu foi o que estava em producao ate ontem); codigo inventado 0/0/0; descricao fora do MASTER 0% / **25,7%** / 0,7%; custo do mesmo teste US$ 4,83 / **0,75** / 4,91. **O UNICO bloqueio real do Haiku e' a descricao, e ela e' 97% FORMATO:** dos 37 erros, 24 sao `over-under-pt` (escreve *Mais de* onde o MASTER manda *Over*) e 12 sao `decimal-virgula`; **1** e' de conteudo. Ele entende o bilhete e escreve no dialeto errado, igual a IA fazia antes das decisoes A e B da s336. **TRES ITENS NOVOS NO BACKLOG, todos medidos:** `4.6` o normalizador de COLUNA (linha com 10 campos cujo ultimo e' codigo valido = TAB faltando; conserta orfa de QUALQUER modelo) + o de FORMATO (o `checar_descricao` ja DETECTA, falta CORRIGIR) — os dois sao pre-requisito do `3.13` e valem por si; `4.7` **print e' 3,2% dos bilhetes** (1.283 de 39.741, pelo marcador `codigo_ocr`), concentrado em **Jaao26** (28,1% dos bilhetes dele) e germano, e **o proxy `input>25k` do ESTUDO SUPERESTIMA** (acusa 43,8% da conta e pega lote grande de TEXTO junto: pelo proxy o Feca teria 107 prints de Bet365 e ele nao manda print); `4.8` **`ricardo05` gastou US$ 13,42 em 18 chamadas e gravou ZERO bilhete** — na base inteira, zero. Pagou e o `/salvar` nunca recebeu, e **isso nao tem alarme nenhum**: ninguem pergunta "houve chamada e nao houve gravacao?", e a resposta esta a um JOIN de distancia. **A RESSALVA ESTRATEGICA que decide a ORDEM:** o normalizador de descricao e' 80% do que o tradutor faz, e o tradutor custa ZERO token nas linhas que cobre contra os 0,5x do Haiku — construir o normalizador so para viabilizar o Haiku e' fazer a parte dificil e ficar com o premio pequeno. **`scripts/bancada_modelos.py` entrou no repo** (era o metodo que o `3.13` prometia e que so existia no scratchpad). **NAO MEDIDO em modelo nenhum: print e PDF.** **E UMA FALHA QUE NAO E' MINHA:** `test_landing.py::test_nenhum_travessao_no_texto` esta VERMELHO desde o `efe5b3a` — 5 travessoes entraram em COMENTARIOS da `landing.html` (linhas 266, 500, 1032, 1094, 1100). Nao toquei: e' arquivo de outra sessao aberta, e reescrever arquivo alheio foi o que apagou trabalho na s372.)

_Anterior: 2026-09-21 (sessao 379: **o boost da Lottu e pago POR FORA da odd, a captura nunca o somou, e sao R$ 1.170,93 de P/L que nunca existiram no sistema — quem acusou foi a Caixa.** O Feca voltou a operar na conta, viu R$ 1.124,58 de divergencia contra o saldo real da casa e trouxe a suspeita certa (*"acho q e pq o sharpenup ta desconsiderando as apostas com boost de 25%"*). **MEDIDO NA API DA CASA, logado ao vivo:** `return_value` e `gross_return_value` trazem `stake x odd` NUA e o extra vive sozinho em `promotions.odds_boost.value`; o card soma os dois (`8410665`: odd 7,38, `return_value: 738`, `odds_boost.value: 184.5`, card "Retorno R$ 922,50"). **O P/L da janela calculado SEM o boost deu R$ 3.602,05 — o mesmo centavo que a Caixa mostrava.** A captura reproduzia a casa com fidelidade perfeita, menos o bonus; com ele, R$ 4.772,98. **O defeito e invisivel na linha:** `stake x odd` fecha exato, o resultado esta certo, e nenhuma checagem de forma acusa. **MESMA ORIGEM, mais TRES defeitos, todos do Criador de Apostas (`is_custom_bet`), que apareceu na conta em 13/09 e o formatador nao conhecia:** a perna nao tem `answer` e a descricao saia VAZIA (**11 de 11 custom bets nasceram no banco com `Mercado Especial - REVISAR`, 100%**), o evento nao tem `question` e sim `home_team`/`away_team` (o CONFRONTO sumia junto) e a odd de cada perna e a do CUPOM repetida (7,3779 nas tres do `8410665`, cujo produto daria 401). O bloco cru da `sombra_rotulos` mostra os quatro de uma vez. **Um quarto ganho de graca:** no custom bet o evento traz `__t: "Soccer"` — a casa INFORMA o esporte, e o bloco mandava deduzir. **CONSERTO:** `_boostLT`/`_retornoLT`, com o bonus entrando SO em `WON`, porque `odds_boost.value` vem preenchido na PERDIDA tambem (2 de 2 medidos) — e' a mesma armadilha do `return_value`, agora inflando em vez de encolher; odd efetiva tirada do DINHEIRO (`Retorno / Stake`, `MASTER_RESULTADO §7.1`) e nao de `odd x (1+pct)`, porque o `return_value` da casa e calculado sobre a odd ARREDONDADA do card; `_descPernaLT` sobe os campos CRUS (`type`/`header`/`name`/`team`/`time`) em vez de traduzir — de-para escondido na captura seria um segundo dicionario fora do MASTER. **GATE: 10 mutacoes, 10 detectadas**, com o bilhete REAL na fixture e dois controles negativos (o mesmo bilhete como `LOST` nao pode somar o bonus; sem boost nao pode existir linha de odd efetiva). **Uma mutacao escapou na primeira bateria e o defeito era do TESTE:** `txt.includes` casava com a mesma frase na linha da PERNA, e a asserção passou a usar `linha()`, que so enxerga o cabecalho. **E o harness pegou um erro MEU:** deixei duas baterias de mutacao rodando ao mesmo tempo, uma restaurou o `content.js` por cima da outra e uma mutacao ficou gravada no arquivo — o gate ficou vermelho e apontou a linha antes do commit. **REPARO RETROATIVO:** `scripts/corrigir_boost_lottu_s371.py` recalcula a odd a partir do BLOCO CRU da sombra (`retorno x (1+pct) / stake`) e so grava se bater com a lista — bloco e lista discordando nao escreve. 6 bilhetes, **R$ 1.170,93 devolvidos**, assinatura intacta (odd nao entra no hash quando ha codigo), e pula qualquer linha com correcao humana em `odd`/`resultado`. **A divergencia da Caixa caiu de R$ 1.124,58 para R$ 46,35**, que NAO e do boost: nao ha aposta aberta na casa (conferido na API), nem cashout, nem anulada na janela. Sobra movimento fora do esportivo ou o saldo inicial de R$ 500,00 redondo digitado em 02/08 — e e o que o botao Ajuste existe para resolver. **ESCOPO DECLARADO, nao resolvido:** a Lottu tem 8 contas de 6 donos; o conserto na captura protege todos daqui em diante, mas o reparo retroativo so foi feito na conta do Feca, a unica com prova — as outras exigiriam a API de cada dono. E as 11 descricoes `Mercado Especial - REVISAR` continuam no banco: traduzir mercado e trabalho da IA com o `MASTER_APOSTAS`, e o UPSERT congela `descricao` em linha resolvida, entao nem recaptura conserta. Os dois foram para o `BACKLOG`. **GATES:** harness verde (29 casos, 474 bilhetes), `audit_casas`, `audit_sharpenup` e `check_docs` sem FAIL, suite 1.240 passed — os 3 vermelhos do `test_changelog` sao a nota da 0.7.17, que so passa a existir com o aviso. **DEPOIS DO REPARO, duas perguntas do Feca viraram medicao.** (1) *"quem mais vem usando a lottu?"*: **8 contas de 6 donos, e so tres vivos** (Jaao26 e Feca capturaram hoje, Ewanderson1 em 19/09; realtrial parou em 02/08, Jonathan em 21/07, WilliamOliveira em 26/08). (2) **Ninguem alem do Feca perdeu dinheiro com o boost**, e a medicao FECHOU o item que eu tinha acabado de abrir no BACKLOG como divida. A regua e barata e serve para a proxima casa: **o bloco antigo so imprimia a linha `odds_boost` na PRESENCA do boost, entao a `sombra_rotulos` vira censo**. Jaao26 tem 3 codigos com boost e **todos perderam**; Ewanderson1 tem 1, tambem perdido; o bonus so vira dinheiro em `WON`. E os outros tres donos **nao podem** ter boost: a promocao nasce em 13/09 e os tres pararam antes. **ACHADO NOVO, de outro dono e de outra causa:** os 187 bilhetes da Lottu do WilliamOliveira sao de UMA captura de 26/08 e estao **sem data, sem esporte, com `Mercado Especial - REVISAR` e travados em `aberta`**, com codigo, stake e odd presentes. E a assinatura de bilhete que subiu **sem o DETALHE**, a chamada por item que traz jogo e data do evento. Sao **187 das 205 abertas dele em toda a base**, e somados aos 11 do Feca fecham **exatamente** as 198 linhas da Lottu com REVISAR. O `roboLTPassive` ja avisa por toast quando isso acontece, e o aviso morreu na tela de quem capturou. Fica no `BACKLOG 3.15`, e metade dele e barata: linha `aberta` refresca data/odd/stake em qualquer reenvio, entao **recaptura da conta dele resolve quase tudo**, sobrando so a `descricao`, que o UPSERT congela. **COMMIT CRUZADO, registrado e NAO desfeito:** outra sessao estava aberta e o commit `20dd13b` levou junto o meu `STATUS.md` e o meu `BACKLOG.md`. Nada se perdeu (a versao commitada por ela ja continha as minhas edicoes finais) e o historico pushado nao foi reescrito, conforme o `CLAUDE.md §8`. **O AVISO AO GRUPO NAO FOI ENVIADO:** a mensagem esta pronta e o "pode mandar" nao veio; a nota da 0.7.17 entrou na home por `--so-changelog`, que e o caminho previsto para nota sem aviso. **PROXIMO PASSO:** mandar o aviso (um comando) ou decidir que este bugfix nao vira aviso. **EM PARALELO, na aba Contas (outra janela):** o agregado da base inteira virou **um bloco so, recolhivel**. Pedido do Feca: *"essa parte, com o Geral das casas deveria ser um bloco so e possivel de minimizar para facilitar a leitura de casa a casa abaixo"*. Eram tres coisas soltas (a faixa de escopo, os tres paineis, a secao Por casa) lendo como tres secoes irmas, quando as duas primeiras sao UMA. **Nada de estilo novo:** o cabecalho e o MESMO `.cn-secao__top` da secao Por casa e o acordeao e o idioma do `.c2-acc` da tela Custos, que por sua vez copiou o `_tmBox` -- dois estilos para o mesmo papel e o item 8 do checklist. A alca fica na **borda do painel** que ela controla, nunca numa barra de acoes sobre o dado. **A REGUA DE ESCOPO FICA FORA DO QUE SE RECOLHE, e isso e decisao, nao descuido:** ela existe para impedir a tela de mentir sobre o que o periodo corta, e a tabela de baixo TAMBEM tem coluna de duracao; recolhe-la junto esconderia o aviso exatamente na hora em que o usuario le casa a casa, que e o momento para o qual o aviso foi escrito. **Some o que e resposta; fica o que e ressalva.** Duas coisas que so a tela deu: o caret sozinho **nao se achava** (ganhou a palavra `mostrar`/`recolher` ao lado, o mesmo recurso da dica da secao irma), e em `--ink-mute` o unico elemento **clicavel** da linha era o mais apagado dela, invertendo a hierarquia -- subiu para `--ink-soft`. Recolher e conveniencia daquele navegador, o exemplo que o `CLAUDE.md` cita como uso legitimo de `localStorage`: nada digitado, nada que precise voltar ao servidor, `try/catch` nas duas pontas. **GATES: 5 mutacoes, 5 detectadas** (a regua indo para dentro do corpo recolhivel, o toggle repintando a tela, o `innerHTML`, o `localStorage` sem `try/catch`, e o seletor de esconder trocado por um que pega a regua junto), em `test_contas_vida.py`, agora com 13 casos. **E MEDIDO NA TELA:** a tabela por casa sobe **376px**, a regua continua visivel recolhida, `aria-expanded` acompanha e a preferencia sobrevive ao recarregar. **Uma armadilha do proprio medidor apareceu no caminho:** o caso novo entrou depois do teste do `Limpar tudo`, que devolve a Populacao ao default (`Inativas`), e no dado do demo isso **esvazia a tela** -- media-se um bloco que nao existe. O arquivo ja documentava a mesma pegadinha para o drill. `?v=` de contas/components em 16/67. **EM PARALELO, no terminal de LANCAMENTO (outra janela):** **(1) o banco passou a ter backup, que nao tinha.** Nem `pg_dump`, nem job, nem snapshot documentado — o unico caminho de volta era a `lixeira_contas` (UMA conta, 7 dias). Entraram `scripts/backup_postgres.py` e [`docs/RUNBOOK_BACKUP_POSTGRES.md`](docs/RUNBOOK_BACKUP_POSTGRES.md). **A prova de restore E o gate, nao o dump:** restaura num banco LOCAL descartavel e compara `count(*)` tabela a tabela contra a origem. **PROVADO: 18 tabelas, 304.146 linhas, zero divergencia**, dump de 17,5 MB em 28,9s. **O motivo de nunca ter existido era um instalador:** producao roda **PostgreSQL 18.6** e a maquina tinha cliente 17, e o `pg_dump` se recusa a dumpar servidor mais novo; o script agora diz isso em vez de repetir o erro cru. Tres travas, todas recusando: restore so em `localhost` (o `.env` daqui aponta para PRODUCAO — mesma familia da trava do `TEST_DATABASE_URL`), banco de prova com prefixo e `DROP` num `finally`, e nenhuma URL/senha impressa. **Duas armadilhas medidas:** `-w` em todo binario (sem ele o `psql` abre prompt e **trava para sempre** em vez de falhar; com ele o erro chega em 0,6s) e o dump so recebe o nome final depois de terminar (parcial com nome definitivo seria restaurado num incidente como se estivesse completo). **(2) a aba Resultados parou de mentir "Carregando dados..." para quem acaba de chegar.** `DADOS` so recebe W/L/V/HW/HL, entao usuario novo — que por definicao so tem aposta em aberto — nunca saia desse estado: e o caso do Diogo (s239), vivo. **MEDIDO ANTES DE PROPOR**, em Chrome headless com o front REAL e dois feeds sinteticos (base ZERO e base SO-ABERTAS): nos dois a aba parava em `chars=133`, sem KPI, sem tabela, sem grafico; **as outras dez abas renderizaram estado vazio honesto nos dois cenarios.** O discriminador e `window._dataBuiltMs`, gravado logo DEPOIS de `aplicarFeed` nos dois caminhos de carga — truthy ⇒ o feed chegou ⇒ vazio e ausencia, nao espera. Reusa o `mkEmpty`, aposentando um `<p>` com style inline. **LIMITE DECLARADO:** fetch que falha sem cache continua caindo em "Carregando", de proposito — o erro de conexao tem canal proprio (`_errBanner`), e dizer "nao ha aposta encerrada" ali seria a mentira inversa, culpando a base do usuario por falha de rede. **GATE: 6 mutacoes, 6 detectadas**, mutando **copias** via `ALVO_TEMPORAL` com aborto se o trecho alvo nao for achado — o arquivo de producao nunca foi editado. `?v=` de temporal em 8. **PENDENTE, tudo no BACKLOG:** cadencia do backup e MANUAL (automatizar sem depender do PC do Feca ligado); o CI **nao roda** `extensor/harness/run.mjs` nem `audit_sharpenup.py`; `/extrair` **sem teto** para usuario aprovado (so o trial tem); `POST /tipsters/sugerir` registrado DUAS vezes (`main.py:4625` e `:4826`, a segunda e codigo morto); `overview.js:293` tem o mesmo padrao com "Sem dados carregados"; a aba Metricas emite **"Solidez Muito Baixa"** sobre base vazia; e o `temporal.js` tem `--ink-soft` em 9px e `opacity:.7` sobre 9px **pre-existentes**, nao replicados pela mudanca. **(3) o deploy ganhou botao de desfazer, e ele nao existia:** [`docs/RUNBOOK_ROLLBACK.md`](docs/RUNBOOK_ROLLBACK.md), com o primeiro passo sendo separar **codigo** de **dado** (sao dois desastres com remedio oposto). **O CLI do Railway NAO faz rollback** — `deployment redeploy` reimplanta a ULTIMA, que e a quebrada; voltar para uma anterior e acao de painel (conferido na v5.8.0). E `railway down` **remove** a implantacao em vez de voltar. **O achado que muda o procedimento: todo deploy MIGRA O BANCO sozinho** (`init_db()` no `lifespan`, `SCHEMA_SQL` inteiro a cada boot). Medido: 18 `CREATE TABLE IF NOT EXISTS`, 24 `ADD COLUMN IF NOT EXISTS`, 10 indices com guarda, 1 `DROP COLUMN IF EXISTS`, **2 `DROP CONSTRAINT IF EXISTS`** (troca da unique pre-multiusuario pela versao com `dono`) e **zero** `SET NOT NULL`/`DROP TABLE`/`ALTER COLUMN TYPE`/DDL sem guarda. **Tudo idempotente**, e por isso o rollback de codigo e seguro hoje — com a ressalva dos dois `DROP CONSTRAINT`, o unico ponto em que voltar nao e simetrico. **A medicao virou GATE** (`tests/test_schema_aditivo.py`): DDL destrutiva ou sem guarda quebra o CI e manda escrever o caminho de volta no runbook antes de liberar. **E O GATE NASCEU FALSO VERDE, o que vale mais que ele:** a 1a versao limpava docstrings do arquivo para nao ler comentario como DDL, e como o `SCHEMA_SQL` **E** uma triple-quoted string, ela apagava o schema inteiro — 10 testes verdes inspecionando string vazia, **8 mutacoes, 8 escaparam**. Quem pegou foi a bateria de mutacao. Entrou o `test_o_gate_esta_mesmo_lendo_o_schema` (piso de tamanho) como rede contra essa familia. **10 mutacoes, 10 detectadas**, sobre COPIAS via `ALVO_DATABASE`. **O RUNBOOK AINDA NAO FOI ENSAIADO** e diz isso na propria tabela de registro: procedimento de emergencia nunca executado e ficcao, e o Caminho A depende de um botao de painel que ninguem desta equipe clicou. **B4 (teto de custo do `/extrair`) foi RECUSADO pelo Feca, com razao registrada:** a fase e de testers, o custo esta em movimento (troca de modelo, IAs em teste, tradutor em construcao) e travar teto agora congela a medicao justamente quando ela e o produto — *"ter um teto agora e um tiro no pe"*. Pedido dele: que o assunto **volte a tona** depois. **EM PARALELO, na aba Contas (outra janela), TRES pedidos do Feca.** **(1) A aba abre em `Ambas`.** Ela nasceu em `Inativas` porque essa e a regua honesta de durabilidade (conta viva ainda nao morreu, e conta-la junto responde "quanto uma conta aguenta" com 103 dias no lugar de 20). O argumento segue valendo **para o numero**; o que mudou foi a pergunta com que a tela ABRE: abrir escondendo as contas vivas faz a tela nascer descrevendo so o que ja morreu, e o segmentado esta a um clique de quem quiser a regua pura. **(2) O drill entra por ESTADO**, ativas em cima e inativas **da ultima limitada para a primeira**. Era turnover desc, que e pergunta de historico e poe no topo uma conta encerrada ha meses. Recencia = `fim` (a regua do `_buildContaVida`); conta ativa e cadastrada tem `fim` = HOJE, entao as ativas empatam entre si e caem no 2o desempate, o `ini`. **(3) 4o PAINEL, so dentro da casa: `Ultimas 10 contas`.** *"O historico nao representa fielmente o momento"*. Ele le so a ponta e poe o recente contra o historico da casa lado a lado -- sem isso o numero recente nao diz se melhorou ou piorou. **Eixo = 1a APOSTA** (decisao dele: *"ordenadas pela aposta 1, independente de estar on ou ja limitada"*), que difere da data de aquisicao porque em base migrada ela foi **DEDUZIDA** por backfill. **A DURACAO DE CONTA ATIVA E CENSURADA E FICA FORA DA MEDIANA:** ela ainda vai crescer, e mistura-la diria que a casa piorou quando o que houve foi so a conta ser nova -- que e exatamente o que o painel existe para responder. Sem nenhuma encerrada a mediana e `null`, **nunca 0**, e o rodape diz por que (familia do "zero se disfarca de conta feita"). Os numeros historicos chegam PRONTOS dos paineis irmaos, nunca recalculados: dois caminhos para o mesmo numero e quando duas partes da tela comecam a divergir. **GATES: 17 mutacoes, 17 detectadas** (8 na ordem e nos defaults, 9 no painel novo). **Tres escaparam na primeira rodada, e cada uma era buraco de verdade:** o bloco JS passa a chave de ordenacao na mao e por isso **nunca via os DEFAULTS** (virou gate de forma), e o caso que devia provar que o desempate **nao vaza** para outras colunas usava dois turnovers DIFERENTES -- o desempate nunca era chamado. O comparador saiu do `_cnDrill` para o `_cnOrdenarDrill` para o teste EXECUTAR o codigo real: recortar a funcao que monta o HTML arrastaria `fmtR`, `fmtPL` e `esc` junto. **E a MEDICAO DE TELA pegou o que o `node --check` nao ve:** ao extrair o comparador eu deixei `key` e `dir` orfaos no cabecalho do drill (`ReferenceError`, o drill parou de abrir), o medidor procurava os paineis num seletor que o bloco Geral tinha invalidado e devolvia **ZERO calado**, com 4 colunas o titulo do 3o painel quebrava em duas linhas **so ele** e desalinhava as quatro figuras, e abaixo de 1250 o `auto-fit` punha TRES e deixava o quarto **orfao** numa segunda fileira (virou 2x2). Medido em 1280/1366/1440/1600/1920/2560. Suite 1.261. `?v=` de contas/components em 18/68.)







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
