# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-07 (sessao 330 — **handoff de design aplicado: `FDC - Contas e Parceiros Opcao A`, 5 fases, 5 commits, todos pushados.** A tela tratava tudo com o mesmo peso: 4 KPIs (um deles sempre `0`), 3 colunas concorrentes, `Editar/Arquivar/Excluir` acesos nas ~100 linhas com um vermelho em cada uma, 29 casas em barras de escala inutil e um log de 40 acoes onde 37 diziam `100%`. **Fase 1** — titulo sai do gradiente azul (o maior texto da tela era acento, e com isso o azul deixava de significar sinal); eyebrow sobe um degrau na Escada de Tinta (9px/--ink-mute media 3,0:1, abaixo do 4,5:1 do papel Label). Aplicado tambem no Dashboard, com `SHELL_SPEC.md` e `check-tokens.mjs` atualizados junto. **Fase 2** — 4 KPIs viram 3, ordenados por CERTEZA DO DINHEIRO: disponivel (garantido) → em aberto (projecao, ambar) → banca total (soma, neutro). Sai o medidor ATIVAS/INATIVAS e o `Caixa total`, que imprimia o MESMO `totais.banca` do KPI ao lado. **Fase 3** — linha da casa e da conta na MESMA grade de 4 trilhas, com a coluna de acoes reservada mesmo vazia; acoes so no hover; `Excluir` sai da linha e vira o ultimo item do menu `⋯`. **Fase 4** — coluna Conciliacao com vocabulario FECHADO num helper so (`tagConciliacao`), sem abreviacao e sem teto no numero; vermelho so em `Divergencia` (erro realizado), ambar em pendencia (fato a conferir). **Fase 5** — `Contas por casa` mostra 6 e colapsa a cauda; na gestao de contas o rail vira fila de `Pendencias` (so excecoes, com `ver log completo`), e na Extracao segue sendo o log. **Dois desvios do handoff, ambos medidos no render, nao deduzidos:** (1) as trilhas fixas do handoff somam 500px e a lista caia a 539px em 1600px de viewport — o nome da casa era CLIPADO; a lista passou a ocupar a linha inteira e `Contas por casa` desceu para fazer par com `Custos por fornecedor`; (2) a tag `Sem caixa` NAO vira tinta — a Caixa esta ligada em 4 de 102 contas e ela pintaria 98 linhas com o mesmo rotulo, que e o defeito que o handoff existe para matar. Tag em 10px e nao 9,5px porque dois rotulos sao --ink-mute e a Escada proibe --ink-mute abaixo de 10px. **Gates:** check-tokens verde, 3 blocos inline compilados por `vm.Script`, **756 passed / 30 skipped**, e render headless contra o `servidor_demo` a cada fase. Varredura da Escada em 3 criterios: os 3 achados sao excecoes ja documentadas (caret/seta e `opacity` como estado), nenhum e codigo novo.)

_Anterior: 2026-09-07 (sessao 329 — **a faxina de documentacao achou 14 regras que governavam o comportamento e nao estavam escritas.** Esse e o resultado, nao os KB. Quatro arquivos disputavam o papel de "onde o projeto esta" e tres descreviam o projeto de julho; a varredura da s261 ja tinha medido o custo disso ("a primeira pendencia que eu fui atacar ja estava feita desde 26/07"). Cinco lotes fechados. **F** — nasce o `BACKLOG.md` (70 KB), que absorve o §5 do STATUS VERBATIM: as 192 linhas nao-vazias conferidas uma a uma, zero perdida, com contraprova por canario. **B** — STATUS de 183 para 44 KB; as 1.157 linhas de antes reprocuradas uma a uma (483 ficaram, 491 foram para o HISTORICO, 183 para o BACKLOG, ZERO perdidas). **C** — HISTORICO de 1,21 MB vira indice de 3 KB + 6 particoes, com as 1.445 linhas conferidas. **D** — 16 docs + 11 anexos para `docs/arquivo/`, `docs/` cai de 43 para 27 vivos, 20 links consertados. **E** — CLAUDE.md de 68,3 para 62,7 KB e nasce o `docs/CASOS.md` (22,9 KB), que NAO e auto-carregado: a regra fica no CLAUDE, o bilhete/casa/valor/sessao vai para o CASOS. **O gate final de regras deu ZERO perdidas**: das 434 ancoras verificaveis, 384 seguem no CLAUDE e 57 migraram para o CASOS; dos 50 numeros que decidem comportamento, 36 ficaram e 11 migraram. 255 regras contadas item a item em 12 secoes. **E 14 regras foram ACRESCENTADAS** — o `git add` por nome, os tres 'os tetos travam crescimento', o trio de causas da Escada de Tinta, a inversao de hierarquia, o 'node --check e falso verde para tudo em template literal', e mais 7. Elas ja governavam o comportamento; so nao estavam escritas como regra. **Gate novo:** `tools/check_docs.py`, no CI, com 7 checagens todas provadas por mutacao — tetos de CLAUDE (65 KB), CASOS (60) e STATUS (50), forma do STATUS (<=3 blocos, <=2 _Anterior), copia em Backups por PREFIXO, link quebrado e ANCORA. Regra sem gate nao e cumprida neste repo: o invariante #4 estava escrito e claro, e Backups chegou a 551 pastas com 165 copias de STATUS/HISTORICO. **Reconciliacao da Auditoria Turbo:** os 78 achados MEDIO/BAIXO do mergulho de 20/07 NAO EXISTEM por escrito (o doc enumera 16 e o rodape diz "Deliverables uncommitted"); reconciliei os 139 do findings.json de 19/07 — 40 fechados, 68 abertos, 20 a confirmar na tela, 3 parciais e 3 que nao eram achado, um deles um placeholder de teste. **#129 medido e rebaixado:** a odd nao entra no calcular_pl em L/V e o risco de dedup deu ZERO de extracao em 528 multiplas sem codigo expostas; virou divida de documentacao. **Lote A ABERTO** — podar Backups (223 arquivos, 28,7 MB), com o zip para fora do repo ANTES de qualquer coisa apagada.)

_Anterior: 2026-09-06 (sessão 324 — **botão que não leva a lugar nenhum confunde mais que botão ausente.** O `Entrar com Telegram` saiu do `/login`: o fluxo não conclui e o relato de uso era gente apertando sem retorno. Só o BOTÃO saiu — backend, rotas e os 27 testes do login social seguem inteiros, e o teste que trava a remoção diz como desfazê-la. `temSocial` deixou de olhar `m.telegram` para o separador **ou** não acender sozinho. 2 mutações aplicadas e 2 detectadas; 717 passed. Causa raiz do clique morto segue ABERTA (suspeito: `/setdomain` do BotFather) — não medida, o pedido era tirar o botão. Antes, s323 — **filtrar um dia zerava o Custo de Contas com o parque inteiro em uso.** A régua velha lançava o custo de aquisição num ÚNICO dia — o da primeira aposta LIQUIDADA — e só o cobrava quando o intervalo das LINHAS filtradas continha aquele dia; recorte sem aposta zerava, e conta comprada e ainda não usada não existia no mapa (entrava nos R$ 3.100 da aba Custos e nunca no KPI). Agora o custo tem JANELA DE VIDA: `ini = menor(adquirida_em, 1ª aposta)`, `fim = maior(última aposta, arquivada_em)`, e todo período que CRUZA a janela cobra o custo cheio. Colunas novas `parceiros.adquirida_em` / `arquivada_em`, editável no modal. O escopo saiu das linhas e foi para o filtro: Casa e Operador recortam o custo, Esporte e Tipster não. ⚠️ A régua NÃO é aditiva e o preço foi aceito na mesa: o P/L Líquido de um dia carrega o custo cheio das contas vivas. 9 mutações aplicadas e 9 detectadas; 716 passed. Método: o vídeo do tester tinha ÁUDIO e a tela sozinha apontava para o alvo errado. Antes, s322 — mexer no multiselect invalida o recorte cacheado: o `_filterCache` só era zerado pelo `renderPage`, e a barra própria da Base Completa não passava por ele.)_

> **Histórico completo das sessões 325 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 330)

### O handoff `Contas e Parceiros Opção A` está aplicado, nas 5 fases

Um commit por fase, todos pushados. A tarefa era de **hierarquia**, não de redesenho:
nada de grid geral, raio, sombra, largura de sidebar, rota ou dado persistido.

| Fase | O que mudou |
|---|---|
| 1 | Título sai do gradiente azul · eyebrow sobe um degrau na Escada · `+ Nova conta` e `Fornecedores` no topo direito · `A conferir` vira chip |
| 2 | 4 KPIs viram 3, ordenados por certeza do dinheiro · sai o medidor e o `Caixa total` duplicado |
| 3 | Casa e conta na mesma grade de 4 trilhas · ações só no hover · `Excluir` vai para o menu `⋯` |
| 4 | Coluna Conciliação com vocabulário fechado num helper só · sem abreviação · uma tag por linha |
| 5 | `Contas por casa` mostra 6 e colapsa a cauda · rail vira fila de `Pendências` |

### O que o render pegou e a leitura do spec não pegaria

Duas coisas só apareceram porque cada fase foi fotografada headless contra o
`scripts/demo/servidor_demo.py`. Nenhuma das duas dá erro em lugar nenhum.

- **As trilhas fixas não cabiam.** O handoff pede `minmax(0,1fr) 190px 108px 202px`,
  que são 500px de coluna fixa. A maquete dava ~1.000px à lista; aqui ela dividia a
  linha com `Contas por casa` **e** com o rail da casca, e media **539px em 1600px de
  viewport**. Sobravam 9px para o nome, e o nome da casa saía **clipado**. Medido em
  quatro larguras: 679px em 1440, 539px em 1600, 736px em 1920. **Não é monotônico** —
  o rail entra entre 1440 e 1600 e come ~300px. Por isso a trilha compacta é
  `@container`, não `@media`: quem manda é a largura do painel, não a da janela.
- **Duas regras de `margin-left:auto` da era flex sobreviveram** e esticavam a célula do
  nome. Foi o que clipou o nome da casa na primeira tentativa, com o CSS novo correto.

### Os dois desvios do handoff, e por quê

- **`Sem caixa` não vira tinta.** A Caixa está ligada em **4 de 102 contas**: a tag
  pintaria 98 linhas com o mesmo rótulo, que é exatamente o defeito que o handoff
  existe para matar (os 37 `100%` do log) reencenado noutra coluna. A ausência já está
  dita pelo travessão da coluna Caixa. O estado segue nomeado no mapa, com a flag
  `vazio`, para ninguém inventar rótulo novo quando ele voltar a ser exceção.
- **Tag em 10px, não em 9,5px.** Dois rótulos da lista são `--ink-mute`, e a Escada de
  Tinta proíbe `--ink-mute` abaixo de 10px em qualquer superfície. Meio pixel preserva a
  distinção de cor; baixar a cor apagaria a diferença entre `Calculado` e `Sem caixa`.

O mesmo vale para o título: o handoff pede 20px e 9,5px, que **não existem na escada** do
`SHELL_SPEC` (9 · 10 · 11 · 13 · 14 · 15 · 18 · 22). O `check-tokens` barra px literal de
propósito. Ficou `--text-xl` no título (a mudança que carrega o argumento é a **cor**) e
`--text-xxs` no eyebrow, que é o degrau seguinte.

### Gates

`check-tokens` verde · 3 blocos inline compilados por `vm.Script` · **756 passed, 30
skipped** · render headless a cada fase · varredura da Escada em 3 critérios (px literal,
tamanho por token e `opacity` sobre tom apagado): 3 achados, **todos** exceções já
documentadas (caret/seta e `opacity` como estado), nenhum de código novo.

Comportamento conferido no navegador, não deduzido: 6 barras visíveis / 23 na cauda /
rótulo `+ 23 casas com 1–2 contas` com a faixa real / abre e fecha nos dois sentidos com
`aria-expanded` correto; menu `⋯` abre, fecha em `Esc` e devolve o foco a quem abriu.

### Ficou de fora, e está no `BACKLOG.md`

- **`Duplicar cadastro` e `Transferir de parceiro`** no menu `⋯`: o handoff os lista, mas
  não existe nada por trás dos dois. Item de menu que não faz nada é pior que item
  ausente, então entraram só `Ver extrato da conta` e `Excluir conta…`.
- **`Sincronizando`**: está no vocabulário e não é emitido — a extração em curso não é
  publicada por conta hoje. Fica no mapa para o dia em que houver a fonte.
- **Assimetria do `Custo de Tipsters`** (já aberta desde a s323) segue de pé.

---

## Sessão 329 — a faxina de documentação

### A faxina fechou em F, B, C, D, E. O Lote A ficou aberto, de propósito.

O que mudou de forma, e o custo de abrir uma sessão:

| Arquivo | Antes | Depois |
|---|---:|---:|
| `CLAUDE.md` (auto-carregado) | 68,3 KB | **62,7 KB** |
| `STATUS.md` | 187,6 KB | **~39 KB** |
| `docs/HISTORICO.md` | 1,21 MB | **3,0 KB** (índice + 6 partições) |
| `BACKLOG.md` | não existia | **70 KB** |
| `docs/CASOS.md` | não existia | **22,9 KB** (lido por escolha) |

**O resultado não é o corte de bytes — é que 14 regras que já governavam o comportamento
passaram a estar escritas.** Elas não vieram de análise nova: vieram de ler cada parágrafo
perguntando *"um agente que leia só isto faz a coisa certa?"*. As mais úteis: o `git add`
por nome (prática combinada, nunca escrita), os três "os tetos travam crescimento, não
mandam cortar", o trio de causas da Escada de Tinta e a inversão de hierarquia (as duas
narradas dentro de um caso), e o `node --check` ser falso verde para **tudo** que vive em
template literal (era o exemplo de uma crase).

**Nenhuma regra se perdeu**, e isso foi medido, não afirmado: das 434 âncoras verificáveis
do `CLAUDE.md`, 384 seguem lá e 57 migraram para o `docs/CASOS.md` — zero sumiram. O gate
automático achou **uma perda real** que a conferência manual não veria: uma âncora partida
por quebra de linha no `CASOS.md`.

### O que fica valendo daqui em diante

- **Um arquivo, uma pergunta** (invariante #10). Pendência nova vai para o `BACKLOG.md`,
  nunca para o `STATUS.md`; caso que originou regra vai para o `docs/CASOS.md`.
- **`python tools/check_docs.py`** roda no CI, com 7 checagens **todas provadas por
  mutação**. Ele declara no cabeçalho o que **não** cobre — não lê conteúdo, e a checagem
  de `Backups/` sai como AVISO no CI, nunca como verde vazio.
- **Os tetos travam crescimento; não mandam cortar.** Ao encostar num deles, mova caso ou
  sessão. Nunca corte bloco de "sintoma", nunca suba o teto.

### Este encerramento exerceu o `BACKLOG §1.3` pela primeira vez

O `STATUS.md` estava em 48,2 KB, a 1,8 KB do teto. O bloco desta sessão o estouraria. A
saída foi a que a regra manda: **mover o bloco mais antigo** (`Sessão 325`, 14,5 KB) para
`docs/historico/HISTORICO_s300-s327.md` **antes** de escrever o novo — não subir o teto.

### Ainda aberto

- **Lote A da faxina.** Podar `Backups/`: 223 arquivos `STATUS*`/`HISTORICO*`, 28,7 MB, num
  total de 551 pastas / 128 MB. Corte em **s ≥ 300**, e para as 396 pastas sem prefixo
  `sNNN` a mesma data de corte. ⚠️ **`Backups/` é gitignored — apagar é IRREVERSÍVEL.**
  Zipar a pasta inteira para **fora do repo** e confirmar que o zip abre **antes** de
  apagar qualquer coisa.
- **O resto está no [`BACKLOG.md`](BACKLOG.md)**, agora em um lugar só.

---

## Sessão 328 — a Pinnacle chama o push de `DRAW`


### A Pinnacle chama o push de `DRAW` — e o rótulo desconhecido virava pendente eterno

O relato foi de uma linha só: *"Pinnacle não atualizou o resultado do void na última
extração"*. O bilhete `3117191609` — Aguila `0.0` no 1º tempo contra o Alianza, `1:1` no
intervalo, R$ 408 — estava **liquidado na casa** (`Decidido / REEMBOLSADO`,
`Vitória/derrota 0.00`) e com `?` na grade do Sharpen.

**O rótulo que a tela mostra não é o que a API devolve.** A tela diz `REEMBOLSADO`; o campo
cru do resultado (93 e 6) traz **`DRAW`**, que não estava no de-para do `formatTicketPN`. O
bloco entregue à IA saía:

```
Status: DRAW (a conferir — não liquidar automaticamente) · P/L 0,00
```

**A IA não errou — ela obedeceu.** Ainda registrou no RAIO-X que o `DRAW` ali não era empate
de jogo e que o P/L 0,00 confirmava reembolso; só não tinha autorização para liquidar. O
backend gravou `aberta` e a linha ficou pendente para sempre. Vale como sintoma: quando a
nota da IA explica o caso certo e mesmo assim nada acontece, a instrução veio de quem
formatou o bloco, não do modelo.

`DRAW` é o **push**: handicap ou total que bate exato na linha (`0.0`, `2.0`) devolve a
stake. Não é o empate do jogo — numa Moneyline de 3 vias o empate dá `LOST`. O campo nomeia
o desfecho da **aposta**, não o do jogo.

### A trava que vale é a de baixo: o dinheiro decide, não o rótulo

Duas foram para o código, e a segunda é a que fecha a família:

1. `DRAW`/`TIE` entraram no de-para junto de `PUSHED`/`VOID`/`REFUNDED`/`CANCELLED`.
2. **Rede por baixo dele:** resolvido + rótulo desconhecido + P/L **exatamente 0** ⇒
   retorno = stake ⇒ `V`, que é a 2ª das cinco fórmulas de `_veredito_do_retorno` lidas ao
   contrário. O próximo nome que a casa inventar para push já nasce coberto.

Com **P/L ≠ 0** o rótulo desconhecido continua subindo como "a conferir": inferir `W`/`L`
de um nome que ninguém conhece é chute, e a rede não pode alcançar a **aberta** (o payload
traz P/L 0 nela também — mesmo número, significado oposto).

### As mutações, incluindo a que escapou

| Mutação | Resultado |
|---|---|
| tirar `DRAW` do de-para | **PEGOU** |
| tirar a rede do P/L | **PEGOU** |
| as duas juntas | **PEGOU** — e reproduz o bug palavra por palavra: `DRAW (a conferir — não liquidar automaticamente) · P/L 0,00` |
| tirar o `!t.aberta` de dentro do `plZero` | **ESCAPOU** |

A que escapou está anotada no caso como **inócua**, não como buraco: quem decide a aberta é
o `if (t.aberta)` de cima, então o `!t.aberta` dentro do `plZero` é defesa dupla. O teste
trava o *comportamento* (aberta com P/L 0 não liquida), não aquela linha.

Anotado também que as duas travas **se cobrem de propósito** — tirar `DRAW` sozinho ainda
daria `V`, pela rede; o que a mutação pegou foi o texto do status mudar. É defesa em
profundidade, não independência.

### O que ficou

- `extensor/content.js` (`formatTicketPN`), `casas/CASA_PINNACLE.md §5.1` (o de-para do
  rótulo **cru**, que a tabela antiga não tinha), fixture + caso no harness.
- Fixture `9000000003` é **derivada** do `3099205574` — só o resultado mudou; nenhum campo
  inventado. O JSON cru do `3117191609` não foi capturado, e o cabeçalho do caso pede a
  troca quando aparecer.
- Harness verde (23 casos, 399 bilhetes) · `audit_sharpenup` e `audit_casas` sem FAIL.
- **SharpenUp 0.7.7.** A linha presa **fecha sozinha na próxima captura** — ela está
  `aberta`, e o UPSERT atualiza resultado em linha aberta. Nenhum script no banco.

### Anotado, não resolvido (não é desta sessão)

O mesmo bilhete entrou na grade como **ML**, não como Handicap Asiático `0.0`. A causa é
outra e é de descrição: `_linhaPN` devolve `""` quando a linha é `0`, então o `0.0` some do
bloco e a IA classifica pelo que sobrou. Some a informação que **distingue** DNB de
Moneyline — e é justamente a linha que explica o push. Não mexi: é mudança de descrição,
com o congelamento do UPSERT no caminho (linha já resolvida não reescreve `aposta`/
`descricao`), e merece sessão própria.

---


## Sessão 327 — a Caixa ligada no meio da captura

### `abertas_corte` mede o que o Sharpen SABE, não o que a casa TEM

O relato veio em três sintomas que pareciam três problemas: "a Betnacional não exporta",
"uma aposta de ontem não resolve" e "preenchi a Caixa e ela não bate". Era **um só**, e
nenhum deles estava na casa — os 11 bilhetes do período estão lá, completos, com odd e
retorno corretos (conferidos card a card no Chrome; a casa diz **"Sem apostas
pendentes"**).

**Defeito 1 — a Caixa foi ligada no meio da captura.** Cronologia medida no banco:

```
03:17:32  Caixa ligada     → abertas_corte = []   (o banco ainda não tinha aberta)
03:17:59  IA termina       (uso_tokens id 2163)
03:18:19  /salvar grava    → 3 apostas nascem ABERTAS: R$ 600,00
03:18:35  Conferência      → projetado −599,00 · saldo real 2.379,87
                           → Ajuste +2.978,87  (R$ 600,00 a mais do que devia)
```

`_caixa_abertas_ids` diz que com `corte = hoje` "toda aposta aberta entra: se ela está
aberta agora, o stake saiu antes de agora, é exato". **É exato só se o Sharpen já souber
da aposta.** O dinheiro sai da conta na casa, não no nosso banco — e entre a captura
começar e o `/salvar` gravar existe uma janela de ~1 minuto em que a Caixa enxerga zero
abertas e grava esse zero para sempre. Pior: o Ajuste da conferência, que existe para
fechar a conta, **cimenta o erro** com cara de número conferido.

**Defeito 2 — a linha órfã sem código.** A captura de 05/09 devolveu a múltipla do
Falkirk sem a 11ª coluna. Sem código a dedup cai na assinatura por conteúdo, e a
"Migração B" do UPSERT (que adota linha sem código) exige `odd` **idêntica**: `14` não é
`14,00`. Quando o bilhete liquidou em 06/09, entrou linha **nova** (246454) e a velha
(243667) ficou `aberta` para sempre — o `AGUARDANDO RESULTADO 1` da grade.

**A prova, contra a casa:**

```
Saldo no corte (05/09)                              2.379,87
+ retorno das 3 abertas no corte                    1.662,26
    243665  R$300 @2,834    L  →        0,00
    243666  R$150 @11,08173 W  →    1.662,26   ← card da casa: "Retorno R$ 1.662,26"
    243667  R$150 @14       L  →        0,00
+ líquido das 8 apostadas depois do corte             515,96
                                                 ──────────
= saldo esperado hoje                               4.558,09   ← bate com a casa
```

A Caixa projetava 3.195,83. A diferença de **1.362,26** é exatamente **+1.662,26** (o
retorno que ela não conta — a `data` 04/09 é anterior ao corte, então ela lê a linha como
"já embutida no saldo informado"; só o **stake** estava, o **retorno** não) **−300,00** (o
Falkirk descontado duas vezes: R$ 150 como fantasma em aberto e R$ 150 como L liquidado).

**Correção aplicada** (`scripts/corrigir_caixa_fantasma_s327.py`, ensaio → `--aplicar`):
apaga o fantasma, grava `abertas_corte = [243665, 243666, 246454]` (o id que carrega
**hoje** cada bilhete — o do Falkirk é o 246454) e baixa o Ajuste em exatamente o
`preso_corte` que faltou, `2.978,87 → 2.378,87`. O script **aborta** se a projeção
corrigida não fechar com o saldo lido na casa. Resultado, relido da API de produção:
`preso_corte 600,00 (3) · pl 1.578,22 (11) · aberto 0,00 (0) · banca 4.558,09 ·
disponível 4.558,09` — divergência **0,00** depois da nova conferência.

O lançamento `conferencia` de 05/09 **não** foi tocado: ele é a medição daquele momento e
não se recalcula. O que ele registrou aconteceu de verdade.

> **Sintoma para reconhecer isto noutro lugar:** um retrato tirado de uma fonte que ainda
> está sendo preenchida. Vale para todo campo que congela estado no instante do clique —
> se a escrita que o alimenta é assíncrona, o clique pode chegar antes dela.

### Os dois defeitos de produto, corrigidos

**1. A órfã não era adotada porque `"14"` não era `"14,00"`.** A Migração B do UPSERT
adota a linha sem código quando o mesmo bilhete volta COM código — e comparava a odd como
**string crua**. `_assinatura` já normaliza a odd (`_norm_odd`) para decidir se duas
linhas são o mesmo bilhete; a Migração B contradizia a própria régua do sistema. Agora as
duas usam `chave_orfa()`, onde o porquê e o caso medido estão escritos. `descricao` fica
de fora **de propósito** — a Migração B nasceu para casar import por imagem com captura da
casa, e é justamente a descrição que diverge entre as duas; há teste para essa ausência
ser decisão registrada, não esquecimento.

De quebra, o índice de órfãs virou **uma consulta por conta** em vez de um
UPDATE-com-subconsulta por linha do lote, e cada órfã só é adotada **uma vez** (`pop`):
sem isso dois bilhetes iguais reivindicariam a mesma linha antiga — e a Migração B, quando
erra, não duplica: ela **sequestra**.

**2. A Caixa ligada no meio da captura gravava `abertas_corte` vazio.** Ao INSERIR uma
aposta que **nasce** aberta e cuja captura (`criado_em`) antecede a ativação, o id agora
entra no `abertas_corte`. Não é heurística: a aposta não pode ter liquidado e
desliquidado, então o stake já tinha saído quando o saldo foi lido. Três travas — só linha
recém-**inserida**; a decisão é do próprio `_caixa_abertas_ids` com `ate` = instante da
ativação (um segundo critério divergiria do original em silêncio); e a lista **só cresce**,
porque tirar um id descontaria o stake duas vezes. `criado_em` nulo ou sem fuso fica de
fora: sem ele não há prova, e comparar um naive estouraria **dentro** do `/salvar`,
derrubando a gravação inteira por causa de uma linha de caixa.

**3. A raiz: a repescagem acrescentava a linha e deixava a órfã.** `conferir_cobertura`
cobra **quantidade por código** — ela não sabe que o bilhete "faltante" pode estar ali
como uma linha que perdeu a 11ª coluna. E a repescagem só ACRESCENTA
(`_extract_tsv_rows(resultado) + novas`); ninguém removia a órfã. Os dois desfechos
deixavam linha sem código: repescagem OK dava **duas** linhas do mesmo bilhete no lote;
repescagem falha (o que aconteceu em 05/09) deixava a órfã — e sem código ela nunca dedupa.

`_reconciliar_orfas` faz duas coisas, ambas conservadoras:

- **Adoção** — a órfã recebe o código do bloco faltante de que ela é **fiel**
  (`checar_fidelidade`, o gate de procedência da s302: todo nome próprio e todo decimal da
  descrição existem naquele bloco). Só quando o par é único **nos dois sentidos** — a órfã
  casa com um único bloco livre, e aquele bloco casa com uma única órfã. Ambíguo não vira
  chute.
- **Descarte** — sobrando órfã depois disso, e não havendo mais bilhete do texto sem linha
  própria, ela é cópia de alguém que já tem a sua. Sai.

**NO-OP integral onde a coluna 11 vazia é legítima:** casa sem marcador (prints, texto
colado) e texto que traga **qualquer** `[Código: ]` vazio — é o que a bet365 manda quando o
detalhe não chegou, e descartar ali apagaria bilhete real.

Roda em **todos** os caminhos de saída, inclusive quando não houve repescagem: era esse o
desfecho que deixava fantasma. O sort por posição no texto-fonte passou a rodar **só quando
este passo mexeu no TSV** — reordenar de graça mudaria calado a ordem que o resto do
sistema lê como hora de envio.

**Gates, provados por mutação** (cada uma pega por exatamente o teste que devia pegá-la):
`_norm_odd` → string crua deixa **6** vermelhos, incluindo o caso medido `14`/`14,00`;
tirar `aposta` da chave, **1**; tirar o `ate`, **1**; sobrescrever `abertas_corte` em vez
de unir, **1**; tirar a guarda de `criado_em`, **2**. Nas órfãs, **1** cada: trava de
par único, guarda do marcador vazio, descarte, adoção e a **ligação** dentro do
`_garantir_cobertura`.

> A **ligação** tem gate próprio no harness de DB (`test_upsert_adota_aberta_que_chegou_
> depois_da_caixa_ligada`). O dublê testa a função, não a chamada: removendo o
> `await _caixa_adotar_abertas_tardias(...)` do `upsert_bilhetes`, o arquivo de dublê fica
> **todo verde** e a Caixa volta a nascer torta. Foi o modo de falso verde nº 1 da
> s286. O mesmo vale para as órfãs: removendo a chamada de dentro do
> `_garantir_cobertura`, os 7 testes de `_reconciliar_orfas` seguem verdes — só o
> teste da ligação pega.

Suíte: **756 passed, 30 skipped**. CI verde em `863f67c`, com os 30 do harness de
Postgres (é lá que o SQL novo do UPSERT é exercido de verdade).

**Backfill: nada a fazer.** `recalcular_abertas_corte_s314.py` em ensaio sobre todas as
caixas ligadas devolve **0 a corrigir**. As 3 contas que uma primeira query apontou
(`Gabriel/Pinnacle`, `Gabriel/1xBet`, `Feca/Bet365 marloncezar01`) são o **piso
deliberado** de corte no passado — o `_caixa_abertas_ids` as exclui de propósito.

**Pendente para a próxima sessão:**

1. **Duas órfãs antigas**, anteriores à correção: `passapica / BETesporte` (04/09,
   R$ 0,75) e `Diogo / Betfair` (12/08, R$ 400,00). São linhas abertas sem código em
   conta que usa código. A Migração B as adota quando o bilhete voltar liquidado, **se**
   data, categoria e stake baterem — não é garantido, e a do Diogo está aberta há quase
   um mês. Duas linhas; resolver à mão é mais barato que esperar.
2. **Aviso aos testers não foi enviado.** Sem bump do SharpenUp, o tester não tem ação a
   tomar. Decisão do Feca; a pergunta ficou em aberto.

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
