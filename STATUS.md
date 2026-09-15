# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-15 (sessao 365: **o pacote do horizonte da Bolsa de Aposta estava pronto no disco havia dois dias e nunca tinha sido commitado** (`fe29c2b`). Ele nao veio de um pedido de feature: o computador do Feca desligou na madrugada e ele pediu para **recuperar as janelas ativas**. Foram achadas quatro (tres do Planilhador — o par de Custos que conversava por cross-session, e a do `.sb-tipster` —, uma do Midas Hub), **todas com working tree limpo e nada perdido**; o que apareceu junto foi um working tree com **8 arquivos modificados desde 13/09 que nao eram de nenhuma delas**. **A frente estava INTEIRA, nao pela metade:** harness verde (28 casos, 454 bilhetes), `CASA_BOLSADEAPOSTA §2.6` escrito, medicao feita na tela da casa. Faltava so o `git commit`. **E ela estava custando caro parada:** o `manifest.json` ja estava em **0.7.13** no disco, entao os **3 vermelhos do `test_changelog`** que as sessoes 360, 362 e 363 registraram, cada uma, como *"o manifest 0.7.13 sem nota, de outra frente"* eram **desta** — tres sessoes seguidas viram a mesma falha, anotaram que nao era delas, e seguiram. **SINTOMA PARA RECONHECER ISTO DE NOVO: um vermelho que mais de uma sessao seguida descreve como sendo de outro.** Nao e ruido de CI, e frente pendurada — e ninguem a adota justamente porque cada uma sabe que nao e sua. A pista barata e cruzar o vermelho com `git status`: o arquivo que o teste acusa estava **modificado e nao commitado** o tempo todo. **O bump de versao e o que amarra as duas metades:** ele mora no repo, mas so fecha quando a nota entra no `changelog.json`, e a nota so entra pelo `avisar_testers.py` — publicar no grupo e gravar a home sao o MESMO ato, entao um bump commitado sem aviso deixa o CI vermelho por desenho. **O QUE O PACOTE FAZ:** o horizonte deixou de ser 3 anos fixos (`_bolsaHorizonte`, `extensor/content.js`) e virou 1 ano na 1a captura desta casa neste navegador, 15 dias de liquidadas e 90 de abertas nas recapturas, esticados pelo tempo parado + 3 de margem, teto de 365; o `lookbackDias` do painel so manda quando pede MAIS. Antes eram **26 requisicoes sequenciais** por clique (13 fatias de 90 dias x 2 status) para reencontrar o mesmo historico, com a tela parada em `0 bilhetes`. Os dois ambientes passaram a varrer em PARALELO, o painel passou a dizer o que esta fazendo, e o carimbo `capUltima:<casa>` so e gravado quando a varredura termina INTEIRA. **`scripts/recon/bda_qual_data_filtra.js` entrou junto, e e ele que torna a janela curta segura:** no Exchange o `after-day`/`before-day` recorta pela data que **corresponde ao status pedido**, medido com o bilhete `47658074` (colocado 31/12/2025, liquidado 04/01/2026), que aparece na janela de 02-04/01 e **nao** na de 30-31/12. Guardar o script e o que impede a medicao de ser refeita daqui a seis meses. **`docs/PLANO_ONBOARDING_TIPSTER.md` (07/09) entrou no repo** (`fa1a48b`): frente ainda nao iniciada, que vivia so no disco. **Uma linha em branco espuria no `MASTER_RESULTADO_2026.md` foi revertida.** **O INVARIANTE #8 FOI OBEDECIDO, e o metodo vale o registro:** a sessao vizinha estava viva no mesmo repo (os dois arquivos do dash dela mudaram **as 16:25, no meio desta**), entao o `add` foi por NOME, os arquivos dela nunca entraram no meu index, e o `git show --stat` depois confirmou 8 arquivos, nenhum alheio. `check_docs` e `check-tokens` verdes. **PENDENTE, e e do Feca: a nota da 0.7.13** — e ela apaga os 3 vermelhos.)

_Anterior: 2026-09-15 (sessao 364: **a base do `Ewanderson1` foi ZERADA a pedido do Feca:** *"apague tudo q subimos para a conta do ewanderson. Ele vai passar a usar como se fosse uma conta virgem"*. **O levantamento ANTES de apagar mudou o escopo:** nao eram so as 784 do import da s357. Havia **961 bilhetes**, 741 de `origem='import'` e **220 de `origem='extracao'`**, ou seja ele ja tinha instalado o SharpenUp e capturado a Betano; mais 23 contas (as 22 `Padrao` do import e a `Nedver [Geilson]`, criada por ele), 1005 `correcoes`, 220 `bloco_visto`, 220 `sombra_rotulos`, 5 `tipsters` e 1 `custo_store`. **2.435 linhas em 7 tabelas, apagadas numa transacao so; 0 restantes, conferido depois.** **O ACHADO QUE MUDA O RESULTADO: `bloco_visto` TINHA de ir junto.** Ele guarda o sha1 do bloco cru por (dono, casa, codigo) e a extracao PULA bloco cujo hash nao mudou (a barreira da s356). Zerar os bilhetes deixando os 220 hashes da Betano faria a proxima captura dele **pular os 220 blocos**: ele recaptura, a tela continua vazia, e **nao ha erro em lugar nenhum**. Estado que sobrevive ao dado que ele descrevia, mesma familia do `abertas_corte` gravado no meio da captura. **DUAS COISAS FICAM, por decisao do Feca:** a linha em `usuarios` (mesmo e-mail, mesma senha, `ativo`; apagar o cadastro o obrigaria a se recadastrar e a ser aprovado de novo no `/admin`) e `uso_tokens`, que e log de gasto de API, contabilidade da operacao e invisivel para ele. `correcoes` foi junto por escolha dele, ciente de que e a semente do cache aprendido por casa. **A REDE E UM DUMP JSON, nao a lixeira:** a `lixeira_contas` cobre a exclusao de UMA conta pelo Painel, nao o esvaziamento de uma base inteira. O `scripts/zerar_base_ewanderson.py` grava `Backups/s364-zerar-ewanderson/ewanderson1_<carimbo>.json` (1,3 MB, 2.435 linhas) **e RELE o arquivo, conferindo a contagem tabela a tabela, antes do primeiro DELETE**: dump que ninguem releu e promessa, nao backup. O dump sai do Postgres ja em `to_jsonb`, entao nenhuma conversao de tipo do Python deforma o que for restaurado. ENSAIO como padrao, e o `dono` reconferido em `usuarios` dentro do script, porque username errado nao da erro, apaga a base de outra pessoa. **O `BACKLOG §1.10` FECHOU tendo acontecido:** o risco medido na s357 era a base duplicar se ele capturasse uma casa do import, e os 220 bilhetes de `extracao` na Betano sao exatamente isso; com a base zerada o risco morreu com ela. O §1.11 foi REMEDIDO na mesma consulta: `Esporte Da Sorte` 102 (Tonelada 99, Marques19981 3) contra `Esportes da Sorte` 99, agora sem nenhuma linha dele. **PENDENTE, e e do Feca:** o custo dele pode ter sobrado no **localStorage do navegador dele** (`dash_custos_v2::Ewanderson1`), que DELETE nenhum no banco alcanca; se aparecer numero na tela de Custos de uma base zerada, e isso. **— E A FATIA 5 FECHOU, noutra frente da mesma sessao: BOOKIES ganhou custo e P/L Liquido, e o PLANO DE CUSTOS acabou.** Detalhe no [`PLANO_CUSTOS_TELA_UNICA`](docs/PLANO_CUSTOS_TELA_UNICA.md) ("O que a Fatia 5 ensinou"). **METADE DELA JA ESTAVA NO AR e o plano nao sabia:** o DRILL de uma casa recebeu Custo / P/L Liquido / ROI Liquido na s358, de carona com a regua de lancamento; faltava a LISTA, que e onde se decide se a operacao numa casa vale a pena. Ler o que ja esta no ar antes de construir uma fatia — o plano descreve a INTENCAO, nao o estado. **A MEDICAO DESAUTORIZOU A IDEIA OBVIA:** na base do Feca sao **48 casas com aposta e 3 com custo** (Superbet R$ 21.500 · Betano R$ 20.300 · Bet365 R$ 17.800, os R$ 59.600 inteiros), entao um stat de custo em cada card sairia `R$ 0` em **45** deles — e ali zero nao e *de graca*, e *nao ha preco lancado*, o zero se disfarcando de conta feita. **Decisao do Feca: os cards ficam INTACTOS**; o custo entra so nos KPIs de topo, que foram de 4 tiles para **duas fileiras de 3** (P/L Bruto · Custo de Contas · P/L Liquido em cima; ROI · Casas Positivas · Turnover embaixo). **O tile se chama `Custo de Contas` de proposito:** custo de tipster e custo geral nao pertencem a casa nenhuma, entao este P/L Liquido **nao e** o da Visao Geral — o nome carrega o escopo e nao sobra paragrafo para explicar. **O custo vem do `calcCostFiltered('casas')`, a MESMA funcao do KPI da Visao Geral** — somar `calcCasaCost` casa a casa daria o mesmo numero por um caminho novo, que e exatamente o que a s362 desfez no `_c2contas`. **GATE NOVO: `tests/test_bookies_custo.py` + `tests/js/bookies_custo.mjs`, 12 de 12 mutacoes detectadas** em `performance.js` E `gestao.js`, mais um teste de FORMA da regua unica — o de comportamento nao distingue as duas derivacoes enquanto elas concordam, que e justamente quando o defeito entra. **QUATRO DEFEITOS DO PROPRIO GATE, todos medidos:** (1) `msGet` devolve um Set **DESCARTAVEL** quando o id ainda nao existe em `MSS`, entao `msGet(id).add(v)` nao seleciona nada e o teste passava medindo o estado SEM filtro — o caminho real e o `msToggle`; (2) funcao de UMA linha quebra o recorte por regex (ele vai ate o proximo `}` na coluna 0 e engoliu o `_filterCache` do topo do `filters.js`), o mesmo que a sessao vizinha viu com o `costKey` engolindo o `CUSTO_SEED` — o ramo de one-liner entrou nos DOIS gates da frente; (3) duas ancoras de mutacao existiam tambem no `renderCasaDrill` e precisaram do `const _apFiltroP=[` junto; (4) com uma conta por casa, `nContas` e o numero de CASAS coincidem, e trocar um pelo outro passava despercebido — entrou o caso de duas contas na MESMA casa. **O teste de forma reprovou o meu proprio COMENTARIO:** ele cita `calcCasaCost` para explicar por que nao se usa ali, e a checagem por substring simples reprovava o texto que documenta a regra; hoje ele checa a CHAMADA (`calcCasaCost(`). **Medido no Chrome de verdade, dentro do iframe:** grid em 3 colunas, 6 tiles, nada truncado (`scrollWidth === clientWidth`), cards intactos com 4 stats, e a cascata fechando — +R$ 267.002,47 − R$ 29.400,00 = +R$ 237.602,47, com os R$ 29.400 batendo com a tela de Custos no mesmo dado. **E o caso que o rotulo existe para explicar foi exercido na tela:** filtrar Tenis leva o liquido de +R$ 237.602,47 para **−R$ 38.992,93** sem nada ter piorado, porque o custo nao recorta por esporte — o sub passa a dizer *das casas inteiras · nao recorta por esporte*. `?v=` de performance/app em 22/57. Suite 1.164 passed; os 3 vermelhos do `test_changelog` seguem sendo o manifest 0.7.13 sem nota, de outra frente.)

_Anterior: 2026-09-15 (sessao 363: **o nome do tipster saiu de metadado da marca e virou o bloco `.sb-tipster`, com avatar preenchivel e prova de resultado — nas DUAS cascas.** Handoff de design do Feca (`handoff-tipster-avatar/reference/sidebar-tipster-c.html`, opcao C), importado pelo claude_design MCP. **Ele pediu as 5 fatias do SPEC**, e o levantamento mudou duas coisas do desenho. (1) **Sao duas cascas, nao uma:** no `/app` logado quem aparece e a sidebar do HOST (`app.html`), porque `html.embedded .sidebar{display:none}` (layout.css) apaga a interna do dash; a sidebar do dash so aparece na vitrine publica. As duas carregam `/static/shell.css`, entao o CSS novo mora la, uma vez so, e o markup mora no `/static/sb-tipster.js`, tambem compartilhado — copiar o bloco em dois lugares e' garantir que divergem no primeiro ajuste. (2) **Ninguem esta logado na vitrine:** o upload nao pode acontecer la. O tipster sobe a logo na conta DELE (os 8 do registro tem linha em `usuarios`) e a vitrine so exibe, o que fecha o furo do §4 do SPEC sem inventar auth publica. **UMA SUPERFICIE SO, e essa foi a decisao que o `/nova-ui` sozinho nao pegaria:** o rodape da sidebar do host JA tinha identidade + caret + trocador (`.sb-operador`), entao o bloco novo no topo teria criado o defeito da s317 de novo — dois lugares com o mesmo papel, o de cima fora do campo de visao de quem mexe no de baixo. O `.sb-tipster` **absorveu** o `.sb-operador`: nome, "Ver base de" e o aviso de `vendo` (que agora ocupa o lugar do selo do plano, em `--accent`) vivem nele, e o CSS/HTML/JS morto saiu. **O PLANO virou campo:** `TIPSTERS_PUBLICOS` ganhou `plano`, e o `nome` perdeu o sufixo (`Soh Props - Vip` -> nome `Soh Props` + plano `VIP`; idem PassaTips e Grego Tips). Coladas na mesma string a tela nao consegue dar tipografia diferente a IDENTIDADE e a DIREITO DE ACESSO, e era isso que rebaixava o nome a rotulo. **LOGO EM `bytea`, nao em arquivo:** o Railway roda do Dockerfile sem volume, entao logo gravada em disco some no deploy seguinte, em silencio. Tabela `conta_logo` (dono PK), rotas `/conta/logo` (POST/GET/DELETE) e `/tipsters/<slug>/logo` — esta **registrada antes do `/tipsters/{slug}`**, senao o slug dinamico a engole. **O tipo vem dos BYTES, nunca do content-type do multipart:** o cabecalho e' dado do remetente e vira o Content-Type com que servimos de volta. `pillow` entrou no requirements (o pymupdf que ja estava la nao decodifica WEBP, que o SPEC pede); raster sai PNG 256x256 `contain` sobre fundo transparente, SVG sai saneado (script, `on*`, `foreignObject`, DOCTYPE/ENTITY e href externo) + CSP `default-src 'none'` na rota. **TRES COISAS QUE SO A TELA MOSTROU**, medidas em headless contra o `servidor_demo`: (a) a regra da celula pegava todo `span` DESCENDENTE e vencia o `.money-val` por specificity — **o P/L saia em `--ink` com o verde preso no container invisivel**, e o `R$` saia do mesmo tamanho do numero; virou `> span` e a cor voltou; (b) **a matriz em R$ nao cabe** nos 264px como cabe em unidades (o mockup foi desenhado em `u`): a 13px, que e' o piso da Escada de Tinta para valor numerico, ela fecha ate R$ 999.999,99 e estoura no 7o digito — dai a classe `.apertado`, posta pelo JS medindo `scrollWidth` depois de pintar, que encolhe padding e tracking e **nunca o numero**; (c) a barra de acento a esquerda do mockup SAIU: nesta casca item ativo e' uma pilula degrade, nao uma barra, e o bloco nao e' item de navegacao. **DUAS TROCAS CONSCIENTES contra o mockup, as duas pela Escada de Tinta:** rotulo de coluna/linha em `--ink-soft` 10px (o mockup pedia `--ink-mute` 9px, que mede 3,0:1 e reprova o papel LABEL — mesma correcao da `.pagehead-eyebrow` na s330); e a coluna Historico em `--ink` neutro em vez de `--ink-soft` apagado, porque ali e' VALOR NUMERICO e numero apagado vira textura. **A hierarquia Mes x Historico virou COR e PESO em vez de tom** — o mes carrega verde/vermelho cheio, o historico fica neutro —, e a leitura do mockup se mantem. **GATES NOVOS, todos provados por mutacao:** `tests/test_logo_conta.py` (21 casos, 7/7 mutacoes), `tests/test_logo_rotas.py` (11 casos, 6/6 — e uma 7a, o `nosniff`, **escapou e era INOCUA**: o middleware `_security_headers` ja o poe em toda resposta, entao a linha na rota era redundante e foi removida em vez de ganhar assercao), `tests/test_sb_tipster_perfil.py` (8 casos, 2/2) e `tests/js/sb_tipster.mjs` (10/10), que carrega o `sb-tipster.js` de producao num DOM dublado. **Tres mutacoes escaparam na 1a rodada do gate JS e as tres eram defeito do TESTE:** o caso do travessao incluia um rotulo de linha no fatiamento, e o minus U+2212 era conferido por "existe em algum lugar" — com tres mascaras com sinal proprio (`fmtPL`, `fmtU`, `fmtPct`), trocar uma por hifen passava porque as outras ainda punham o dela. Cada uma passou a ser conferida por si. **O `_medir` headless tambem virou ferramenta, nao so conferencia:** foi ele que achou (a) e (b), que nenhum gate de codigo pegaria. **EFEITO COLATERAL DO MEU PROPRIO SCRIPT, e vale registrar:** `pathlib.write_text` no Windows converte LF em CRLF, e os arquivos que reescrevi por script cresceram ~1 byte por linha — o `git diff` nao acusou (o `core.autocrlf` normaliza), mas o `check_docs` mede BYTES EM DISCO e o `CLAUDE.md` estourou o teto de 65 KB sem uma linha de conteudo nova. Reconvertidos para LF; **quem editar por script neste repo escreve com `newline=''` ou em bytes**. Suite 1.149 passed; `check-tokens` e `check_docs` verdes; bloco medido e fotografado nas duas cascas. `?v=` de shell.css em 3, app.js do dash em 56, sb-tipster.js em 1. **PENDENTE, e e' do Feca:** (1) **avisar os tipsters de que da' para por a logo** — o recurso nasce sem uso se ninguem souber; (2) os avisos ja represados (custo, manifest 0.7.13). **AJUSTE DO FECA NA MESMA SESSAO: o selo do plano virou BADGE e "Sem plano" virou "Tester" em azul da marca.** Ele viu o bloco no ar, achou legal, e pediu: *"para os users atuais, ao inves de 'Sem Plano' coloque Tester num badge bacana. azul do sharpen por ex."* **A troca e' mais do que cosmetica:** "Sem plano" descreve o que a conta NAO tem; "Tester" descreve o que ela E' — e hoje TODA conta do sistema e' de teste. **E o badge levou os TRES estados junto, nao so um:** deixar "Tester" com fundo solido e "Plano VIP" como texto puro seria o sintoma do item 8 da regra de UI (dois estilos para o mesmo papel no mesmo slot, que o olho le como inconsistente sem saber qual metade esta certa). Entao o selo virou pill nos tres — **ambar** para plano pago, **azul** para Tester, **ambar + borda do bloco** para "vendo base de" —, que alias e' o que o README do handoff pedia desde o comeco (*"vira pill ambar"*) e o CSS do mockup nao tinha feito. **Tinta ESCURA sobre acento, nunca branca**, e medido em headless: `var(--bg)` sobre `--accent` da **5,79:1** e sobre `--warn` da **8,67:1** — exatamente os 5,8 e 8,7 que a Escada de Tinta documenta, enquanto `#fff` sobre `--accent` daria 3,36 e reprovaria. **GATE NOVO, e ele existe porque esta e' uma regra que a propria sidebar ja quebrou** (os `.pend-badge`/`.open-badge` usam `#fff` literal e sao desvio conhecido): `test_o_selo_do_plano_usa_tinta_escura_sobre_o_acento` le as declaracoes de `color` da regra e exige `var(--bg)`, 4 de 4 mutacoes detectadas. **O 1o rascunho dele reprovava sozinho:** procurava a palavra "white" no bloco inteiro e batia no `white-space: nowrap` — substring de CSS nao e' leitura de CSS. **No gate JS, uma mutacao escapou e era buraco de teste:** eu conferia o TEXTO do selo ("Plano VIP") mas nao a classe, entao colar `tester` em todo mundo deixava o plano pago escrito certo e pintado de AZUL. `?v=` de shell.css em 4 e sb-tipster.js em 2. **E a resposta a outra pergunta dele fica registrada: a logo NAO e' obrigatoria** — sem ela o avatar fica no monograma das iniciais, que e' como toda conta nasce, por desenho do SPEC. **Os 3 vermelhos do `test_changelog` seguem sendo o manifest 0.7.13 sem nota, de outra frente — nao desta.** **E O INVARIANTE #8 ACONTECEU DE NOVO, na forma classica:** os meus 3 arquivos do dash (`dash/index.html`, `dash/assets/js/app.js`, `dash/assets/css/components.css`) foram levados pelo commit `32fe631` da sessao vizinha — o index e' compartilhado e o `git add` dela pegou o que estava esperando do meu lado. **Conferido byte a byte: o conteudo chegou INTEIRO** (`sbTipsterPintar` 4x, `shell.css?v=3`, `.pub-tipster` removido), e `32fe631` ja estava pushado — entao **nao reescrevi historico**, como o invariante manda. O efeito e' so de leitura: quem procurar a origem do bloco da vitrine pelo `git log` vai achar 3 dos 20 arquivos sob uma mensagem de custo. O `git show --stat` DEPOIS de commitar e' o que acusa isso, e foi assim que apareceu.)

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
