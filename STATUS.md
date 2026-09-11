# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-10 (sessao 345: **o selo de captura automatica ao lado do nome da casa, e um commit cruzado que quebrou a producao.** Feedback do Feca: toda casa com extracao automatica tem de DIZER isso na tela. O selo entra em TRES lugares, um por superficie: **pill com a marca escrita** no cabecalho de casa do Painel de Contas, e **so a lamina** no dropdown de conta e no idcard, onde o nome ja trunca. Uma peca (`.su-badge` / `--icon`), reusando a lamina e a lockup do `#btn-conectar-ext`; nenhum desenho novo. **Transporte:** `GET /casas` passa a devolver `captura`, o subconjunto da lista `casas` que ele ja manda, na MESMA grafia. Quem normaliza e o servidor (`_display_to_key`), onde a conversao mora; o front so faz `Set.has` e nao mantem lista nenhuma, entao **casa nova na captura acende o selo sozinha**. `CASAS_COM_CAPTURA` e uma VISTA de `_HOSTS_POR_CASA` (30 casas), nunca uma copia — copiar recriaria a armadilha dos tres mapas de favicon. **O ACHADO DE UI: o degrau tem de medir a CELULA, nao a tabela.** A pill soma ~105px e a trilha do nome e `minmax(228px, 1fr)`, com o piso 228 calculado na s331 **sem selo nenhum**: medido no headless, ela truncava **6 nomes de casa** e `Bolsa de Aposta` virava `Bolsa d…`. E a largura da TABELA **nao prevê** a da trilha (tabela 1.046 da trilha 298; tabela 988 da 372), porque os cortes 990/1150 ligam colunas opcionais que comem o `1fr` — com `@container acct` a pill so aparecia em janela de **2.560px**. Com `container-type` na PROPRIA celula do nome: **9 larguras medidas (1.100 a 2.560), zero nome truncado e zero overflow**, pill em 5 delas e lamina em 4. No piso da trilha o selo **sai da linha** em vez de mutilar o nome, que e o que o `casaDisplay` existe para evitar. Tambem medido: o `.nm` do idcard tem `overflow:hidden` e **decepava** o "up" do selo, que sobe 22% acima do tile; o corte desceu para o span do nome, que e quem precisa truncar. **O SUSTO:** o `app/main.py` com a linha da rota foi levado pelo commit `e343386` da outra sessao (index compartilhado, [caso 8](docs/CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026)), que subiu **sem o `captura.py`** — la `main.py` chamava `_captura.casa_tem_captura` e a funcao nao existia, entao `/casas` quebrava com `AttributeError` **para todo dono**. Historico ja pushado nao se reescreve; o `4798135` conserta. **A licao e nova e e da familia do caso 8: conferir o `git status` depois de commitar nao basta, porque o arquivo pode ter ido no commit ALHEIO** — o sintoma e o seu arquivo sumir do seu diff **sem** estar no seu commit, e quem so olha "limpou, entao foi" nao ve. **Gates:** `tests/test_casas_captura.py` exerce a ROTA e nao uma copia da linha que monta o campo, 18 casos, **5 de 5 mutacoes detectadas** (casa fora do mapa, lista escrita a mao, rota normalizando a grafia, rota sem o de-para, campo ausente da resposta). 863 passed / 36 skipped, `check-tokens` verde, Escada de Tinta varrida nos tres criterios, tela renderizada headless. **Pendente:** a Etapa 2 (o modal antes de processar texto/print em casa com captura, Opcao 1 enxuta, ja aprovada) — no `BACKLOG`. **`check_docs` acusa 2 FAIL PREEXISTENTES, nenhum desta sessao:** `CLAUDE.md` em 65,4 KB (teto 65) e 223 copias de STATUS/HISTORICO no `Backups/` (28,7 MB). As 344/343 sao de outra sessao. **ETAPA 2 no ar, na mesma sessao: o modal antes de processar.** Clicar em **Processar Bilhetes** com texto ou print numa casa que tem captura abre um modal **com a cara da marca** (lockup no topo, centrado) em vez do `confirm()` do Chrome: *A <casa> tem captura automatica*, com **Usar o SharpenUp** e **Processar mesmo assim**. Mensagem enxuta por decisao do Feca — sem "nao avisar de novo" e sem ressalva sobre bilhete antigo. **CSV/XLS ficam de fora**: import de planilha e outro caminho e a extensao nao o substitui. O helper e o `shConfirm` da s341, **mesmo nome e mesmo contrato do dashboard**, portado para ca — um padrao de confirmacao para os dois apps, e os outros `confirm()` nativos deste arquivo passam a ter para onde migrar. Nao e duplicata do `.modal` que ja existe aqui: aquele e modal de FORMULARIO e este e de DECISAO. **Gates: 6 de 6 mutacoes detectadas — e as DUAS PRIMEIRAS ESCAPARAM, por buraco no harness, nao no codigo.** (a) tirar o `if (!(await ...)) return` nao aparecia, porque o `await` sozinho ja segura o fluxo enquanto o modal esta aberto: so o clique no botao PRIMARIO revela, e o harness nunca clicava nele. (b) avisar mesmo sem texto nem print nao aparecia, porque o harness sempre digitava antes de clicar. Com os casos 4 e 5, cada mutacao passou a cair num caso diferente. E antes disso a propria prova estava **invalida**: sob `subprocess` o caminho `/c/Users/...` nao e convertido, o screenshot estourava com ENOENT e matava o script **antes dos casos 2 e 3** — tres mutacoes "pegaram" por artefato. **A base tem de passar em TODOS os casos antes de mutar**, e e por isso que agora ha um `assert` dizendo isso. Medido tambem: o botao era anunciado como *"SharpenUp Usar o SharpenUp"* porque o selo repetia a marca; virou modo `decor` (`aria-hidden`). **Desvio registrado, nao replicado as cegas:** `#fff` sobre `--accent` da **3,36:1** e a Escada manda tinta escura (`var(--bg)` = 5,8:1), mas TODO botao primario do app usa `#fff` — divergir so aqui criaria dois estilos para o mesmo papel. Esta comentado no CSS e trocar os dois de uma vez e decisao de marca. **Avisado ao grupo** (`message_id 3456`) e a mesma nota na home (`changelog.json`, 16 itens) pelo `avisar_testers.py --novidade` — nao houve bump do SharpenUp, a mudanca e do painel. A licao do commit cruzado foi para o [caso 8](docs/CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026), que e onde o invariante 8 ja aponta; o `CLAUDE.md` nao cresceu porque esta estourado. **PROXIMO PASSO: validar ao vivo** (F5 no dashboard; selo nas casas certas e modal ao colar texto numa conta Bet365) — tudo aqui foi provado headless contra o demo. **Tres decisoes do Feca em aberto:** (1) pill SEMPRE no Painel exige subir o piso da trilha do nome de 228 para ~340 e recalibrar os cortes 990/1150, sessao propria; (2) `#fff` sobre `--accent` da 3,36:1 em TODO botao primario dos dois apps, decisao de marca; (3) a poda do `Backups/` (223 copias, 28,7 MB) e o `CLAUDE.md` em 65,4 KB, os dois FAIL preexistentes do `check_docs`.)

_Anterior: 2026-09-10 (sessao 344: **as 298 apostas de 2025 que a Betbra exportou sairam da base, e agora elas NAO VOLTAM.** A 1a captura da casa (s343) gravou 411 bilhetes de uma vez, 298 deles de 01/06/2025 a 31/10/2025, e a Betbra e a UNICA casa deste dono com bilhete de 2025: toda a base dele comeca em 2026. **Apagar do banco nao resolvia**, e essa era a metade que faltava: o `bda_inject` varre 3 anos por DESENHO (`DIAS_HISTORICO = 1095`, fixo desde a s299, quando a janela curta do painel trouxe 21 de 418 bilhetes), entao a captura seguinte reencontra os mesmos codigos e regrava tudo, sem erro nenhum. Exclusao sem corte dura ate a proxima varredura, que e a familia do 'volta pela CASA, nunca pelo banco'. **O corte ficou no `/extrair`, nao na extensao**, por dois motivos: o inject e COMPARTILHADO com a Bolsa de Aposta e vale para todo dono (encurtar o horizonte la quebraria a casa que ele existe para proteger), e aqui a regua e por **(dono, casa)** e roda ANTES da IA, entao o bloco cortado nao paga leitura, nao vira TSV e nao chega ao `/salvar`. Regua declarada em `main._CORTE_HISTORICO`: Feca x Betbra, nada anterior a **01/01/2026**. A data lida e a do **EVENTO**, a mesma que decide a coluna Data (ler a colocacao cortaria aposta feita em dezembro para jogo de janeiro), e o bloco sem data legivel **FICA** (fail-open: esconder bilhete e o modo de falha caro; um a mais para a IA e o que a barreira de recaptura ja devolve). Tela: contagem em balde PROPRIO (`fora_corte`), nunca somada em `xls_skipped`, porque 'ja salva' afirma que existe uma linha no banco e esta nunca existiu. **Aplicado depois de conferir o deploy no ar** (o `/static/index.html` de producao ja servia o campo novo): 298 linhas movidas para `lixeira_bilhetes` com motivo nomeado, saindo da base R$ 10.125,25 de turnover e **+R$ 5.262,25 de P/L**. Restam 113 Betbra do Feca, todas de 2026, e **zero** bilhete de 2025 em qualquer casa dele; as contas dos outros 4 donos na Betbra ficaram intactas. **Gates:** `tests/test_corte_historico.py`, 16 casos sobre blocos REAIS da `sombra_rotulos`, **6 de 7 mutacoes detectadas** (a 7a e inocua, o log some); a de numero 5 e a chamada REMOVIDA da rota, que e o jeito de o corte ficar verde e inutil. 863 passed / 36 skipped, `check-tokens` verde, `index.html` renderizado headless sem erro de script. **Pendente:** validar ao vivo (recapturar a Betbra e conferir que as 298 nao voltam), que e o unico teste que fecha isto. O commit levou um susto pelo caminho: outra sessao escrevia no mesmo `index.html` e o 1o commit levou o selo de captura dela junto; corrigido ANTES do push, com o blob do indice trocado para conter so os meus hunks e o trabalho dela intacto no working copy. As 343/342 sao de outra sessao.)

_Anterior: 2026-09-10 (sessao 343: **BETBRA no ar como casa ESPELHO da Bolsa de Aposta — zero inject novo — e um cupom que virava MULTIPLA FALSA sem erro nenhum.** Medido no navegador: mesma plataforma, mesmas rotas de casca (`/b/exchange` · `/fbook`), Exchange LayBack em `mexchange.betbra.bet.br` (cookie, 0 parametros) e Sportsbook msjxk em `prod20454-176166310.msjxk.com` (`operatorToken` na URL). Os dois injects ja derivavam o endereco de `location`, entao **o unico bloqueio real era o `match` do manifest**, preso em `*.bolsadeaposta.bet.br`. Volume: **403 ofertas no Exchange** (mai/2025 → set/2026, varridas em 29 chamadas com ZERO erro) + 10 no Sportsbook. **O ACHADO:** `Selections` NAO e a lista do que foi apostado. No bet builder a casa manda, no MESMO array, as PERNAS soltas (cada uma com a odd de mercado dela, que nao foi apostada) e uma entrada AGREGADA do cupom (`MarketTypeId: "QA0"`) com a odd do conjunto e os textos concatenados por ` | `. Quem manda e `MappedSelections`. O codigo lia todas: uma aposta de **4,61** virava multipla de **26,72** (1,13 × 2,30 × 2,23 × 4,61) — **sem erro, e com o P/L intacto**, porque a odd do bilhete vem de outro campo; errariam so turnover, ROI e a assinatura de stake do matcher (familia da s311). Medido 10/10: a odd bate com o produto das MAPPED em 10/10 e com o de TODAS em **0/10**. **O defeito atravessou o recon da Bolsa sem aparecer** — la o campo e sempre `[0]` com uma selecao so, e o caso da Bolsa fica verde COM ou SEM a correcao. Isso foi PROVADO, nao deduzido: das **5 mutacoes, o caso Betbra pegou 5 e o caso Bolsa pegou 0**. Formato decidido contra a tela: ordem das pernas vem do TEXTO AGREGADO (o array traz outra — o `SelectionId` da agregada e `0VS0|2|1`), perna de cupom **nao tem odd propria** no bloco, e o tipo virou `Criador de Apostas (bet builder — N selecoes do MESMO jogo, odd unica do cupom)`. **BOOST confirmado** (era "nao confirmado" na Bolsa): `ClientOdds` e a odd COM boost e `DbTrueOdds` da agregada e a SEM (a tela risca `2.89` e estampa `3.36`); o percentual NAO se deduz do `Campaigns[].Type` (1,32 e 1,16 em tipos diferentes). **Medido antes de registrar:** a grafia canonica e `Betbra` — unica no banco nas 5 tabelas onde `casa` e texto (5 contas, 158 bilhetes), apesar de `import_dashboard_xlsx.py` mapear para a gemea `BetBra`; e as series de codigo sao POR CASA, nao por plataforma (7-8 digitos aqui, 9 na Bolsa) — **comprimento de codigo nao diz de que casa o bilhete e**. **Gates:** harness 28 casos / 447 bilhetes verde, `audit_sharpenup` e `audit_casas` sem FAIL, 826 passed, manifest 0.7.10 → **0.7.11** com aviso publicado no grupo (`message_id 3380`). **Pendente:** validacao ao vivo (recarregar a extensao + Ctrl+Shift+R na aba da casa + F5 no dashboard). SUPERBET e BETESPORTE seguem SEM caso no harness, e nenhuma das duas foi tocada. As 342/341/339 sao de outra sessao.)




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
