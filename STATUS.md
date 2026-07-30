# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-29 (sessão 218 — **Conta nova `WilliamOliveira` (dono solo, base virgem) + o diagnóstico de por que a `LavaPessoal` da s216 não entrava.** Mesmo procedimento da s216: 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_WILLIAMOLIVEIRA_HASH` no Railway, sem migration nem seed. Dono solo (não é operador de ninguém, `coproprietarios == []` → sem dedup cruzada). **O caso do LavaPessoal virou método, e é o que vale guardar:** o Feca reportou "usuário ou senha inválidos" e a tentação era mexer no código. **Distingui código de configuração com duas medições em produção, sem acesso ao Railway:** (1) `/static/dash/assets/js/mc-core.js` responde **200** — arquivo que nasceu na s217, portanto o deploy no ar é **posterior** ao commit da s216 e o usuário **existe** em `USUARIOS`; (2) `POST /login` responde **401**, e no `main.py` esse 401 tem **uma única origem** (`verificar_credenciais` falso) — 429 seria rate-limit, 500 seria erro. Usuário existindo + credencial falsa = **hash vazio ou diferente**, isto é, a env var não chegou ao Railway. **A lição operacional: criar usuário é uma mudança de DUAS metades, e a segunda é humana.** O código sobe pelo push; a senha depende de alguém colar a variável no Railway, e enquanto isso não acontece o login falha com a mesma cara de "senha errada" (fail-closed por desenho — `USUARIOS[x] == ""` nunca autentica). **O `$` do hash bcrypt é a armadilha de transporte:** `$2b$12$...` colado em qualquer shell que interpole variável chega mutilado; na caixa de Variables do Railway vai literal. Confira 60 caracteres, sem espaço nas pontas. **Hashes conferidos ponta a ponta antes do commit** (comprimento 60, valida a senha certa, rejeita a caixa trocada, `verificar_credenciais` + roundtrip do token) — o hash nunca entra no git. **A regra virou canônica, não história:** a seção "Conta de usuário nova = duas metades" entrou no `CLAUDE.md` (procedimento, o diagnóstico 401 × 429 × 500, a armadilha do `$` e a decisão solo × operador). **Gates:** `pytest tests/test_auth.py` **28 passed**. Backup `Backups/s218-user-williamoliveira/`. **Pendente do lado humano:** as duas env vars de senha no Railway (ver §5). **Anterior: s217 abaixo.**)_

_Anterior: 2026-07-29 (sessão 217 — **O dashboard travava a aba: o Web Worker do Monte Carlo estava MORTO em produção havia 26 dias, e o fallback síncrono escondia isso.** **Sintoma do Feca:** *"tô sentindo o Sharpen MUITOOOO LENTO, inclusive direto aparece a mensagem de aguardar ou fechar a aba"* — em **toda** navegação do dashboard; a Extração, normal. **Medido no Chrome dele, na base real** (30.851 encerradas + 57 abertas), com `PerformanceObserver` de longtask: **52,7 s** de thread principal bloqueada no boot do dashboard, **40 s** na tela Métricas e **11,9 s** ao abrir o drill de um tipster — tudo atribuído ao iframe `fr-dash`. O Chrome oferece "aguardar ou fechar a aba" a partir de ~15 s. **Causa raiz, e é o CRUZAMENTO de duas mudanças que estavam certas isoladamente:** o worker nasceu em `408255f` (29/06) como `new Worker(URL.createObjectURL(blob))`; a CSP entrou em `2e835ed` (03/07, sprint de risco pós-auditoria) com `default-src 'self'` e **sem `worker-src`** — worker de `blob:` cai no default-src e o construtor é **bloqueado**. Como o código tinha fallback ("worker falhou → calcula síncrono"), **o número continuou certo e ninguém viu**: a regressão não quebrou nada, só travou tudo. Vinte e seis dias. **A prova foi feita na página em produção, não deduzida:** `new Worker(blob:)` devolve `onerror` **sem mensagem** (assinatura de bloqueio por CSP), enquanto um worker de **mesma origem** criado ali do lado sobrevive. **O backend foi inocentado com número:** `/dashboard/data` responde em **1,3 s** (11,6 MB crus, 1,18 MB gzipados) e cada tela renderiza em **35–475 ms** com o cache quente — o gargalo era 100% cliente. **Escolha do Feca entre as duas saídas:** afrouxar a CSP com `worker-src 'self' blob:` (1 linha) **ou** extrair o núcleo e servir o worker como arquivo. Ficou a segunda — **num projeto recém-auditado, trocar segurança por performance é a troca errada**, e o caminho de mesma origem cabe em `script-src 'self'` sem afrouxar nada. **Como ficou:** `assets/js/mc-core.js` é a **fonte única** de `mulberry32`/`_calcMCdrawdownRaw`/`_calcPValueMCraw` — a página carrega por `<script>`, o `mc-worker.js` carrega por `importScripts('mc-core.js' + location.search)`, que **repassa o `?v=`** para o núcleo do worker nunca ficar velho por baixo da página nova. O `.toString()` que gerava o worker morreu junto com o blob. **Equivalência provada, não presumida:** as 3 funções do `mc-core.js` × as mesmas do `app.js` de antes (backup), em 3 tamanhos — `xmdd`, `p50/p95/p99` e p-value **idênticos**. **Duas telas nem tentavam o worker** e seguiam no cálculo bloqueante: **Métricas** (`gestao.js`) e o **drill de tipster** (`performance.js`), que a migração da Visão Geral deixou para trás. As duas passaram a `mcComputeAsync`, com selo **"calculando…"** nos valores que ainda vão chegar e um **contador de render** (`_metricsReq`/`_tipDrillReq`) para a resposta de uma janela antiga nunca pintar por cima da nova — abrir o tipster A, fechar e abrir o B não pode mostrar o número do A. **Medido depois no servidor de demonstração (24.000 apostas):** Métricas pinta em **54 ms** (era 40 s congelados) e o drill abre em **676 ms** (era ~12 s); durante todo o cálculo o *ping* da thread ficou em **0 ms** e `_mcModo` reportou `worker`. **Um defeito meu apareceu só no render:** o esqueleto trocava a `className` junto com o conteúdo e **apagava a classe semântica do markup** (`d-proj`), então `mv_xmdd`/`mv_p95`/`mv_p99` voltariam com a cor errada — o esqueleto passou a trocar **só** o conteúdo, que é o que `setLive` sem 3º argumento pressupõe. **O silêncio virou ruído de propósito:** quando o worker cai, o console agora **avisa** que o cálculo foi para a thread principal — foi o silêncio que custou os 26 dias. **Gates (`tests/test_monte_carlo_worker.py`, 16 casos):** a **implicação** que estava quebrada em produção (worker de `blob:` **exige** `worker-src` na CSP — o teste lê as duas coisas e reprova a combinação impossível), nenhuma tela chamando `calcMCdrawdown`/`calcPValueMC` síncrono, a matemática definida **uma vez só**, o worker importando o núcleo com o `?v=`, a ordem de carga no HTML e os dois arquivos **realmente servidos** como JavaScript. **Três quebras deliberadas** confirmaram que protege: voltar o worker para blob, pôr o cálculo síncrono numa tela e duplicar `mulberry32` — cada uma reprovada pelo teste certo. **O gate reprovou de primeira por um falso positivo instrutivo:** acusou o próprio comentário do `app.js` que diz *"NUNCA VOLTAR PARA `new Worker(...blob...)`"* — passou a limpar comentários antes de auditar, **a mesma lição da s214: o gate tem de ler o código, não a prosa sobre o código**. **Gates:** `pytest tests` **263 passed** · `check-tokens` OK · `node --check` nos 5 JS · render conferido nas duas telas (valores finais e estado "calculando…"). Bump `app.js v27` · `gestao v21` · `performance v11` · `mc-core v1`. Backup `Backups/s217-worker-monte-carlo/`. **Quatro achados laterais medidos e NÃO corrigidos** (ver §5): o `sims=10000` fixo, `/uso/tokens` respondendo **500**, os **3 iframes** da casca puxando o feed inteiro cada um, e o deep-link a frio montando tela vazia. **Anterior: s216 abaixo.**)_

_Anterior: 2026-07-29 (sessão 216 — **Conta nova `LavaPessoal` (amigo do Feca), DONO SOLO e base virgem.** Usuário novo no Sharpen são **duas coisas e nada mais**: uma linha em `USUARIOS` (`app/auth.py`) e a env var `SENHA_LAVAPESSOAL_HASH` no Railway. **Não existe migration, seed nem import** — o isolamento é por coluna `dono` no Postgres, então a base nasce vazia por construção: o primeiro bilhete capturado cria as linhas dele. **Decisão do Feca: dono solo, não operador do Feca** — apesar do nome parecido com `Lava` (que É operador do Feca). Consequências que valem registrar: ninguém "vê como" LavaPessoal, ele não vê ninguém, e `coproprietarios('LavaPessoal') == []` → **sem dedup cruzada** (a que barra recaptura de conta física compartilhada dentro da linhagem). **A semelhança de nome é a armadilha real**, então ela ficou travada em dois lugares: comentário explícito acima de `OPERADORES` e teste `test_lavapessoal_e_dono_solo_isolado_do_feca` — pendurar a conta em `OPERADORES['Feca']` numa sessão futura derruba a suíte. **O `.env.example` estava defasado** (listava 3 dos 8 usuários) e passou a listar os 9 — quem monta um `.env` local pelo exemplo não descobria que faltavam 5 hashes senão pelo login falhando calado (fail-closed). **Hash gerado com bcrypt e conferido ponta a ponta antes do commit** (valida a senha certa, rejeita a errada com caixa trocada, `verificar_credenciais` + roundtrip do token). O hash **não** entra no git — vai na env var do Railway pela mão do Feca. **Gates:** `pytest` **247 passed** (7 novos). Backup `Backups/s216-user-lavapessoal/`. **Anterior: s215 abaixo.**)_

_Anterior: 2026-07-29 (sessão 215 — **As apostas em aberto entram no dashboard: aparecem na lista da base e ganham tela própria, "Minhas Apostas › Em Aberto".** **Pedido do Feca:** com a captura passando a importar aposta não liquidada, a régua de informação precisava subir. **A causa do item 1 era de BACKEND, não de tela:** o front já tinha o encanamento pronto (`DADOS_ABERTAS`, `filtrarAbertas`, linha "Aberta" no topo da lista, contador), mas `repository.dashboard_rows` **descartava** toda linha com `resultado` fora de {W,L,V,HW,HL} — as abertas nunca chegavam ao feed e o encanamento rodava sobre um array vazio. Agora a linha sem resultado sai marcada `resultado='ABERTA'` com `lucro=0`; `resultado` preenchido e desconhecido continua sendo lixo descartado. `criado_em` viaja **só** nas abertas (carimbar as ~30k encerradas custaria ~1MB de feed sem consumidor). **Mudar o feed obrigou a auditar quem consome, e havia dois pontos que somariam a aberta como se fosse encerrada:** o Início (turnover e ROI do mês, "apostas encerradas hoje") e o painel de atividade das contas na Extração (coluna "Apostas", duração da conta). Os dois ganharam corte explícito por `resultado==='ABERTA'`. **Um terceiro era duplicação:** o Início unia `/bilhetes?extraction_state=aberta` (Postgres) com as abertas do feed, apoiado na premissa — verdadeira até esta sessão — de que as duas fontes eram **disjuntas**; com o feed carregando as do Postgres, cada aberta contaria **duas vezes**. O corte é `r.id==null`: linha de planilha ao vivo não tem id. **Tela nova (`charts/abertas.js`), com três decisões deliberadas:** (1) **sem filtro de período** — aposta aberta aponta para o futuro, e um recorte "últimos 30 dias" esconderia o jogo de amanhã, que é o que a tela existe para mostrar (`buildFiltersSemData`); (2) **sem verde/vermelho** — não há P/L porque nada resolveu; exposição é âmbar (`--warn`, o mesmo "pendente" do Início) e projeção é azul; (3) **toda agregação temporal usa a data do EVENTO**, não a da captura. **Conteúdo:** 4 KPIs (Valor em Aberto · Apostas · Odd Média ponderada · **Retorno Potencial** — nome escolhido no lugar de "Retorno Possível" porque é stake × odd, o retorno bruto que cai na conta, com o lucro potencial na legenda) · horizonte em 5 faixas (Atrasadas · Hoje · Amanhã · Próximos 7 dias · Depois), que é o que responde "quanto é pra quarta, quanto pro sábado" · calendário mensal com a exposição de cada dia · exposição por casa e por tipster em barras · lista completa ordenada por **quem liquida primeiro**, com editar/deletar reusando o modal da Minha Base. **Nav:** "Apostas" virou **"Minha Base"** dentro do grupo novo **"Minhas Apostas"**, ao lado de "Em Aberto" — nas **duas** sidebars (a casca `app.html` e a interna `dash/app.js`), que precisam andar juntas. **Dois defeitos vieram do render headless, não da leitura:** as barras de exposição eram `<span>` com `height` — span inline ignora altura, e a barra saía como um fio sem preenchimento (corrigido com `display:block`); e o `.money` dentro da legenda do KPI é `width:100%` + `min-width:10ch` (largura de **coluna de tabela**), que numa frase corrida quebrava "lucro de R$ 28.650 se todas ganharem" em três linhas — relaxado em `.kpi-sub`, o que **conserta o mesmo defeito latente** em qualquer KPI que ponha dinheiro na legenda. O calendário também passou a **podar as semanas vazias das pontas**: aposta aberta ocupa poucos dias, e sem isso o mês abria com quatro semanas em branco. **O contrato do feed ganhou teste próprio** (`tests/test_dashboard_feed.py`, 7 casos, sem DB — `export_bilhetes` é substituído): aberta marcada com lucro 0, aberta e encerrada convivendo, resultado inválido descartado, `criado_em` só na aberta, e as exclusões de fronteira (stake 0 e data ilegível cortam; **odd ausente não corta** — é dinheiro exposto). **O servidor de demonstração passou a espelhar o contrato novo** (abertas no feed, com data de evento espalhada pelos próximos dias); sem isso não havia como renderizar a tela para conferir. **Gates:** `pytest` **238 passed** · `check-tokens` OK · harness da captura **6 casos / 142 bilhetes verde** · `audit_casas` sem FAIL · `vm.Script` nos 5 JS tocados · render headless conferido nas duas telas. Backup `Backups/s215-em-aberto/`. **A TELA SUBIU VAZIA EM PRODUÇÃO, e a causa não era ela: era CACHE DA CASCA.** O navegador do Feca serviu o `index.html` **antigo** do dashboard. Ele carregou `app.js` e `filters.js` novos (mesma URL, conteúdo atualizado — daí a tela, a sidebar e os cards existirem), mas `charts/abertas.js` é **arquivo novo**, e a tag que o chama só existe no `index.html` novo: o script nunca foi pedido, `renderAbertas` não existia, e `renderPage` morria antes de pintar. **A causa raiz é estrutural, não deste arquivo:** o `?v=` renova os assets, mas o `?v=` **mora dentro do HTML**, e o HTML era servido **sem `Cache-Control` nenhum** — aí o navegador escolhe sozinho por quanto tempo não perguntar (heurística de ~10% da idade do arquivo). **Toda tela nova que trouxesse um arquivo novo nasceria invisível para quem já usou o site.** Corrigido no `_security_headers` (`main.py`): resposta `text/html` leva `no-cache, must-revalidate` — guardar pode, revalidar é obrigatório, e com o ETag que o `StaticFiles` já manda o custo normal é um **304 sem corpo**. **Só HTML**: JS/CSS seguem cacheáveis, senão o `?v=` perderia a razão de existir. Os **dois lados** da regra estão travados em `tests/test_cache_headers.py` (8 casos); quebra deliberada do middleware derruba 4. **Nota operacional: o fix não desfaz o cache já gravado** — quem estava com a casca velha precisa de um `Ctrl+Shift+R` **uma vez**; a partir daí, nunca mais. **Diagnóstico só fechou porque foi medido dentro da sessão logada:** de fora, `sharpen.bet/...` responde 404 em qualquer path (é o redirect da GoDaddy; o app vive em **`www`.sharpen.bet`**), e eu cheguei a ler isso como "site fora do ar" — era erro de domínio meu. **O ROI do mês no Início também foi corrigido na mesma sessão, a pedido do Feca:** ele somava **todas** as stakes no turnover, enquanto a regra canônica (`MASTER_OUTPUT` / `calcTurnover`) exclui Void — mesmo P/L sobre denominador inflado dava **5,70% contra 6,13%** do dashboard na mesma janela. Agora batem: **+6,13% nos dois**, conferido lado a lado no servidor de demonstração. **Anterior: s214 abaixo.**)_

> **Histórico completo das sessões 214 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
    CASA_JOGODEOURO.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_PINNACLE.md
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_VAIDEBET.md
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

Os 6 MASTER_*.md vivem em `/global/`; as 17 casas em `/casas/` (Polymarket por API, as demais por IA/texto).

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway; base nasce vazia sem migration.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Casas:** 17 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **10 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210) e **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`, sem código duplicado).
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências (aguardam bilhete real)

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betfair:** cashout **parcial** (`isPartialCashOut`) sem amostra — o total já está travado no harness (2 casos) · HW/HL sem amostra · Each Way com `0 < Retorno < Stake` (o §5 não cobre essa faixa; hoje sai "a conferir", sem chute)
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

- **Betfast / Tivo (s211):** cashout · bônus · aposta de sistema · outright · **aposta ABERTA** (as 50 da amostra são liquidadas) · `§9` de duas categorias (`Total de defesas do goleiro` · `Handicap de mapas`/`Map Advantage`)

**Achados de performance da s217 — medidos, não corrigidos (decisão do Feca, um por vez):**
- **`sims=10000` fixo mesmo com a base cheia.** As chamadas passam `10000` explícito, o que **atropela** a escala adaptativa que o `_calcPValueMCraw` tem por dentro (`n>10000 → 3000`). Com 30.851 linhas são ~308 milhões de iterações por cálculo, duas vezes. Fora da thread principal a tela não trava mais, mas o valor ainda leva **~1 minuto** para chegar (conferido no demo com 24.000: os cards ficaram girando bem depois do render). Cair para ~2.000 sims em base grande resolveria — **muda número exibido** (p95/p99 e p-value), então exige antes/depois medido na mesa e aval do Feca.
- **`/uso/tokens` responde 500** em produção (visto ao cronometrar as rotas do feed). Não investigado.
- **A casca `/app` carrega 3 iframes e os 3 puxam `/dashboard/data`** — `/inicio`, `/` (Extração) e `/dashboard/`, cada um montando o feed inteiro no servidor (3 × 11,6 MB por abertura). Um cache compartilhado entre os frames (ou o feed servido uma vez pela casca) cortaria 2/3 do trabalho.
- **Deep-link a frio monta a tela vazia.** Abrir `/app#dash/metrics` sem cache local: a casca chama `showPage('metrics')` antes de o `buildHTML` existir, `_lastPage` já fica marcado, e o `loadData` termina **sem chamar `renderPage`** (`app.js:1183`) — o `showPage` seguinte volta cedo pelo `if(id===_lastPage&&sig===_lastPageSig)return`. A tela fica com os `—` do markup. **Pré-existente**, não veio da s217.

**Próximo passo (backlog vivo, um por vez):**
- **Betfast: rodar a captura pela EXTENSÃO** (s211). A API já foi validada ao vivo (varredura do teto: 32 de 32, ver acima), mas o robô em si nunca rodou: recarregar a extensão, **Ctrl+Shift+R** na aba, capturar e conferir contagem/datas/odds/código no dashboard. **O gatilho do teto continua sem exercício ao vivo** — a conta que loga no navegador tem 32 bilhetes e não chega nas 50; para ver o toast *"a captura foi além do teto"* seria preciso rodar na conta `fecanario`.
- **Pinnacle sem fixture no harness** (s201): a instrução foi corrigida (§6/§11 não afirmam mais que a exibida é autoritativa em `W`), mas a leitura da odd **nunca foi travada contra dado real** — só Betfair, KTO e Tivo têm caso. Com o JSON do `POST /member-service/v2/wager-filter` dá para criar `fixtures/pinnacle.*.json` + `casos/pinnacle.mjs` e medir de fato o quanto a exibida diverge de `Retorno ÷ Stake`. O banco não serve para isso: guarda stake e odd, nunca o retorno.
- **bet365 sem caso no harness** (s202): é a única casa de robô sem regressão travada — e o parser dela já quebrou 3 vezes. As fixtures reais (`summary` + `confirmation` do bilhete com bet builder) já estão em `extensor/harness/fixtures/`; falta escrever `casos/bet365.mjs`. A conferência de cobertura dela **já está ligada** (`831f97f`).
- **`renomear_parceiro` não recalcula a assinatura** (s198): `parceiro` entra no hash, então toda conta renomeada duplica o histórico na próxima captura.
- **41 apostas com odd truncada em reticências** (`2.50001664442...`): 22 Bet365, 6 Novibet, 6 Bolsa, 4 Betfair, 3 Esportiva Bet. A instrução proíbe reticências e uma odd assim não converte para número — mexe em P/L, não é cosmético.
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Solto (cosmético):** favicon da KTO aponta para `kto.com`; o domínio real é `kto.bet.br`. Corrigir nos 3 mapas (`extensor/popup.js`, `app/static/index.html`, `app/static/dash/assets/js/data.js` + `inicio.html`).
- **Tela "Em Aberto" fora do material de venda** (s215): `scripts/demo/capturar.mjs` não captura a tela nova — o servidor de demonstração já a serve, falta só decidir se ela entra no showcase (e a numeração dos arquivos existentes muda). **Decisão do Feca: entra, mas só depois de a tela estar finalizada.**
- **Em Aberto: relato do Gabriel SEM confirmação** (s215, aberto): funciona para o Feca (57 abertas, R$ 13.325, conferido na sessão logada em `www.sharpen.bet`), mas o Gabriel disse que não. **Hipótese principal: casca velha ainda gravada no navegador dele** — o `no-cache` só vale a partir da próxima ida ao servidor, não desfaz cache já gravado; `Ctrl+Shift+R` uma vez resolve (F5 normal pode não recarregar o iframe do dashboard). **Antes de mexer na tela, distinguir pelo que ele vê:** cards com título e corpo vazio, sem nenhum KPI = ainda é cache; os 4 KPIs em `R$ 0` / "nada em aberto" = não é bug, a base dele não tem aposta aberta (conferir de quem é a base pelo filtro "Operador"). O jeito de medir é ler quais scripts o navegador dele carregou (`[...frame.contentDocument.scripts].map(s=>s.src)`) — versão antiga ou tag ausente = cache.
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

### Bloqueado por ação humana (não é bilhete)

- **Duas env vars de senha faltando no Railway** (s216 e s218): `SENHA_LAVAPESSOAL_HASH` e `SENHA_WILLIAMOLIVEIRA_HASH`. O código dos dois usuários está no ar; sem as variáveis o login responde "usuário ou senha inválidos" (fail-closed, hash vazio). Os hashes foram gerados e conferidos, mas **não entram no git** — se perdidos, gerar de novo com bcrypt. Confirmação depois de colar: `POST /login` devolve **200** (401 = hash ausente ou diferente).

Quando chegar um bilhete novo: abrir o arquivo da casa correspondente, preencher a pendência, rodar o checklist do `CLAUDE.md` se envolver categoria nova.

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
