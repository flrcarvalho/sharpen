# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-30 (sessão 219 — **Excluir conta: a terceira ação que faltava no Painel de Contas, com lixeira de 7 dias por trás.** **Pedido do Feca:** *"hoje uma conta pode ser arquivada ou reativada, porém não pode ser excluída"*, com a confirmação obrigatória de que *"todas as apostas registradas nela serão excluídas e que a ação é irreversível"*. **A primeira decisão foi de escopo, e ele escolheu:** o painel tem duas entidades — a **conta** (`parceiros`, a linha) e a **casa** (o grupo). Excluir passou a ser da **conta**; a casa não é entidade apagável. Consequência levantada no código, não deduzida: `/casas` (`main.py`) monta a lista como *casas com manual `CASA_*.md`* **∪** *casas que têm conta*, então Bet365/Betano/KTO **nunca somem** do seletor mesmo com zero contas — pôr outra conta no lugar é imediato, que era o requisito dele. Só sai da lista casa criada em **modo cego** que ficou sem contas; recriada com o mesmo nome, `casas_meta` devolve favicon e curadoria intactos. **A segunda decisão foi a rede de segurança, e a forma importa mais que a existência:** soft-delete (coluna `excluido` em `bilhetes`) foi **descartado** — obrigaria a filtrar em dezenas de queries espalhadas (dashboard, KPIs, dedup, export, P/L) e **um esquecimento vira lucro fantasma**, a mesma família do UPSERT meio-atualizado já documentada no `CLAUDE.md`. A exclusão **move** as linhas para `lixeira_contas`, tabela que **nada mais no sistema lê**: acoplamento zero por construção. Snapshot em **JSONB** (`to_jsonb(b.*)`) e não em tabela-espelho, porque `bilhetes` ganha coluna via `ALTER TABLE` de tempos em tempos e um espelho pararia de copiar a coluna nova **em silêncio**. Retenção **7 dias** (escolha do Feca), purga **preguiçosa** a cada exclusão — mesmo padrão da poda de tipster órfão em `list_tipsters_cadastro`, sem cron. **A UI não expõe a lixeira, de propósito:** prometer "dá pra desfazer" convida ao clique fácil, que é o que o modal existe para impedir; a volta é `scripts/restaurar_conta_lixeira.py` (lista, prévia, `--aplicar`), que casa o snapshot com as colunas que `bilhetes` tem **hoje**, usa `ON CONFLICT DO NOTHING` nos dois passos (entre excluir e restaurar o operador pode ter recriado a conta e a captura já ter regravado assinatura igual — **dado novo manda**) e realinha a sequence do `id`. **O `DELETE` e o snapshot são a MESMA operação** (`DELETE ... RETURNING to_jsonb`), então é impossível gravar lixeira que não corresponda ao que saiu. **O que NÃO é apagado, e por quê:** `correcoes` e `uso_tokens` só têm `casa`, não `parceiro` — não há como escopar por conta, e são log de aprendizado/custo; `casas_meta`/`casa_config` pertencem à casa, que continua existindo. **A confirmação é dupla e a segunda não é cosmética:** o modal só libera o botão com o nome exato digitado **e** a contagem já recebida, e o backend **reconfere o nome** — a rota é destrutiva e não pode confiar só no cliente (um `DELETE /parceiros/7` por engano não pode apagar histórico). A contagem sai de `GET /parceiros/{id}/resumo`, **a mesma cláusula que o DELETE usa** — não de `/dashboard/data`, que é cacheado e em conta de planilha viva atrasa dezenas de minutos: número velho numa tela que promete "isto será apagado" seria pior que número nenhum. **Uma imprecisão antiga foi corrigida junto:** `Arquivar` era `.conta-act danger` (vermelho) sendo **reversível**. Perdeu o vermelho; `Excluir` é a única ação em `--neg`. Se as duas fossem vermelhas, a cor não avisaria nada. `Excluir` aparece nas **duas** abas — conta arquivada é justamente a que mais se quer apagar. **Dois defeitos vieram do render headless, não da leitura:** (1) `.btn-danger` não tinha regra `:disabled` (só `.btn-primary` tinha), então o botão travado ficava **idêntico** ao habilitado e o operador leria "o clique falhou" em vez de "falta digitar"; (2) o nome a digitar vive dentro de um `.modal-field label`, que é **UPPERCASE** — a tela pedia `FECA [JOAOCONTAS]` e o botão só liberaria com `Feca [JoaoContas]`: mostrava uma coisa e exigia outra. **Gates:** `/nova-ui` rodado antes de escrever a UI (sem R$ no que foi construído — a contagem é de apostas, e reusa o `toLocaleString('pt-BR')` que o arquivo já usa; nenhum formatador novo) · `pytest tests/` **270 passed, 13 skipped** (7 novos em `test_excluir_parceiro.py`, cobrindo vazamento de escopo para outra conta/casa/**dono** e as três formas de disparar sem confirmação) · `check-tokens` OK · `compileall` OK · JS inline sem erro de sintaxe · render headless conferido. Backup `Backups/excluir-conta-lixeira/`. **Anterior: s218 abaixo.**)_

_Anterior: 2026-07-29 (sessão 218 — **Conta nova `WilliamOliveira` (dono solo, base virgem) + o diagnóstico de por que a `LavaPessoal` da s216 não entrava.** Mesmo procedimento da s216: 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_WILLIAMOLIVEIRA_HASH` no Railway, sem migration nem seed. Dono solo (não é operador de ninguém, `coproprietarios == []` → sem dedup cruzada). **O caso do LavaPessoal virou método, e é o que vale guardar:** o Feca reportou "usuário ou senha inválidos" e a tentação era mexer no código. **Distingui código de configuração com duas medições em produção, sem acesso ao Railway:** (1) `/static/dash/assets/js/mc-core.js` responde **200** — arquivo que nasceu na s217, portanto o deploy no ar é **posterior** ao commit da s216 e o usuário **existe** em `USUARIOS`; (2) `POST /login` responde **401**, e no `main.py` esse 401 tem **uma única origem** (`verificar_credenciais` falso) — 429 seria rate-limit, 500 seria erro. Usuário existindo + credencial falsa = **hash vazio ou diferente**, isto é, a env var não chegou ao Railway. **A lição operacional: criar usuário é uma mudança de DUAS metades, e a segunda é humana.** O código sobe pelo push; a senha depende de alguém colar a variável no Railway, e enquanto isso não acontece o login falha com a mesma cara de "senha errada" (fail-closed por desenho — `USUARIOS[x] == ""` nunca autentica). **O `$` do hash bcrypt é a armadilha de transporte:** `$2b$12$...` colado em qualquer shell que interpole variável chega mutilado; na caixa de Variables do Railway vai literal. Confira 60 caracteres, sem espaço nas pontas. **Hashes conferidos ponta a ponta antes do commit** (comprimento 60, valida a senha certa, rejeita a caixa trocada, `verificar_credenciais` + roundtrip do token) — o hash nunca entra no git. **A regra virou canônica, não história:** a seção "Conta de usuário nova = duas metades" entrou no `CLAUDE.md` (procedimento, o diagnóstico 401 × 429 × 500, a armadilha do `$` e a decisão solo × operador). **Gates:** `pytest tests/test_auth.py` **28 passed**. Backup `Backups/s218-user-williamoliveira/`. **Pendente do lado humano:** as duas env vars de senha no Railway (ver §5). **Anterior: s217 abaixo.**)_

_Anterior: 2026-07-29 (sessão 217 — **O dashboard travava a aba: o Web Worker do Monte Carlo estava MORTO em produção havia 26 dias, e o fallback síncrono escondia isso.** **Sintoma do Feca:** *"tô sentindo o Sharpen MUITOOOO LENTO, inclusive direto aparece a mensagem de aguardar ou fechar a aba"* — em **toda** navegação do dashboard; a Extração, normal. **Medido no Chrome dele, na base real** (30.851 encerradas + 57 abertas), com `PerformanceObserver` de longtask: **52,7 s** de thread principal bloqueada no boot do dashboard, **40 s** na tela Métricas e **11,9 s** ao abrir o drill de um tipster — tudo atribuído ao iframe `fr-dash`. O Chrome oferece "aguardar ou fechar a aba" a partir de ~15 s. **Causa raiz, e é o CRUZAMENTO de duas mudanças que estavam certas isoladamente:** o worker nasceu em `408255f` (29/06) como `new Worker(URL.createObjectURL(blob))`; a CSP entrou em `2e835ed` (03/07, sprint de risco pós-auditoria) com `default-src 'self'` e **sem `worker-src`** — worker de `blob:` cai no default-src e o construtor é **bloqueado**. Como o código tinha fallback ("worker falhou → calcula síncrono"), **o número continuou certo e ninguém viu**: a regressão não quebrou nada, só travou tudo. Vinte e seis dias. **A prova foi feita na página em produção, não deduzida:** `new Worker(blob:)` devolve `onerror` **sem mensagem** (assinatura de bloqueio por CSP), enquanto um worker de **mesma origem** criado ali do lado sobrevive. **O backend foi inocentado com número:** `/dashboard/data` responde em **1,3 s** (11,6 MB crus, 1,18 MB gzipados) e cada tela renderiza em **35–475 ms** com o cache quente — o gargalo era 100% cliente. **Escolha do Feca entre as duas saídas:** afrouxar a CSP com `worker-src 'self' blob:` (1 linha) **ou** extrair o núcleo e servir o worker como arquivo. Ficou a segunda — **num projeto recém-auditado, trocar segurança por performance é a troca errada**, e o caminho de mesma origem cabe em `script-src 'self'` sem afrouxar nada. **Como ficou:** `assets/js/mc-core.js` é a **fonte única** de `mulberry32`/`_calcMCdrawdownRaw`/`_calcPValueMCraw` — a página carrega por `<script>`, o `mc-worker.js` carrega por `importScripts('mc-core.js' + location.search)`, que **repassa o `?v=`** para o núcleo do worker nunca ficar velho por baixo da página nova. O `.toString()` que gerava o worker morreu junto com o blob. **Equivalência provada, não presumida:** as 3 funções do `mc-core.js` × as mesmas do `app.js` de antes (backup), em 3 tamanhos — `xmdd`, `p50/p95/p99` e p-value **idênticos**. **Duas telas nem tentavam o worker** e seguiam no cálculo bloqueante: **Métricas** (`gestao.js`) e o **drill de tipster** (`performance.js`), que a migração da Visão Geral deixou para trás. As duas passaram a `mcComputeAsync`, com selo **"calculando…"** nos valores que ainda vão chegar e um **contador de render** (`_metricsReq`/`_tipDrillReq`) para a resposta de uma janela antiga nunca pintar por cima da nova — abrir o tipster A, fechar e abrir o B não pode mostrar o número do A. **Medido depois no servidor de demonstração (24.000 apostas):** Métricas pinta em **54 ms** (era 40 s congelados) e o drill abre em **676 ms** (era ~12 s); durante todo o cálculo o *ping* da thread ficou em **0 ms** e `_mcModo` reportou `worker`. **Um defeito meu apareceu só no render:** o esqueleto trocava a `className` junto com o conteúdo e **apagava a classe semântica do markup** (`d-proj`), então `mv_xmdd`/`mv_p95`/`mv_p99` voltariam com a cor errada — o esqueleto passou a trocar **só** o conteúdo, que é o que `setLive` sem 3º argumento pressupõe. **O silêncio virou ruído de propósito:** quando o worker cai, o console agora **avisa** que o cálculo foi para a thread principal — foi o silêncio que custou os 26 dias. **Gates (`tests/test_monte_carlo_worker.py`, 16 casos):** a **implicação** que estava quebrada em produção (worker de `blob:` **exige** `worker-src` na CSP — o teste lê as duas coisas e reprova a combinação impossível), nenhuma tela chamando `calcMCdrawdown`/`calcPValueMC` síncrono, a matemática definida **uma vez só**, o worker importando o núcleo com o `?v=`, a ordem de carga no HTML e os dois arquivos **realmente servidos** como JavaScript. **Três quebras deliberadas** confirmaram que protege: voltar o worker para blob, pôr o cálculo síncrono numa tela e duplicar `mulberry32` — cada uma reprovada pelo teste certo. **O gate reprovou de primeira por um falso positivo instrutivo:** acusou o próprio comentário do `app.js` que diz *"NUNCA VOLTAR PARA `new Worker(...blob...)`"* — passou a limpar comentários antes de auditar, **a mesma lição da s214: o gate tem de ler o código, não a prosa sobre o código**. **Gates:** `pytest tests` **263 passed** · `check-tokens` OK · `node --check` nos 5 JS · render conferido nas duas telas (valores finais e estado "calculando…"). Bump `app.js v27` · `gestao v21` · `performance v11` · `mc-core v1`. Backup `Backups/s217-worker-monte-carlo/`. **Quatro achados laterais medidos e NÃO corrigidos** (ver §5): o `sims=10000` fixo, `/uso/tokens` respondendo **500**, os **3 iframes** da casca puxando o feed inteiro cada um, e o deep-link a frio montando tela vazia. **Anterior: s216 abaixo.**)_

_Anterior: 2026-07-29 (sessão 216 — **Conta nova `LavaPessoal` (amigo do Feca), DONO SOLO e base virgem.** Usuário novo no Sharpen são **duas coisas e nada mais**: uma linha em `USUARIOS` (`app/auth.py`) e a env var `SENHA_LAVAPESSOAL_HASH` no Railway. **Não existe migration, seed nem import** — o isolamento é por coluna `dono` no Postgres, então a base nasce vazia por construção: o primeiro bilhete capturado cria as linhas dele. **Decisão do Feca: dono solo, não operador do Feca** — apesar do nome parecido com `Lava` (que É operador do Feca). Consequências que valem registrar: ninguém "vê como" LavaPessoal, ele não vê ninguém, e `coproprietarios('LavaPessoal') == []` → **sem dedup cruzada** (a que barra recaptura de conta física compartilhada dentro da linhagem). **A semelhança de nome é a armadilha real**, então ela ficou travada em dois lugares: comentário explícito acima de `OPERADORES` e teste `test_lavapessoal_e_dono_solo_isolado_do_feca` — pendurar a conta em `OPERADORES['Feca']` numa sessão futura derruba a suíte. **O `.env.example` estava defasado** (listava 3 dos 8 usuários) e passou a listar os 9 — quem monta um `.env` local pelo exemplo não descobria que faltavam 5 hashes senão pelo login falhando calado (fail-closed). **Hash gerado com bcrypt e conferido ponta a ponta antes do commit** (valida a senha certa, rejeita a errada com caixa trocada, `verificar_credenciais` + roundtrip do token). O hash **não** entra no git — vai na env var do Railway pela mão do Feca. **Gates:** `pytest` **247 passed** (7 novos). Backup `Backups/s216-user-lavapessoal/`. **Anterior: s215 abaixo.**)_

> **Histórico completo das sessões 215 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
