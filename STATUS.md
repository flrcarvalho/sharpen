# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-14 (sessão 142d — **Perfil de Tipster — gestão CONSOLIDADA na página Tipsters do dashboard (feedback do Feca).** O Feca notou que já existia uma "Tipsters" (a análise do dashboard) e a minha nova ficou como aba SEPARADA no extrator → duas "Tipsters", confuso. Decisão (`AskUserQuestion`): **tudo na página do dashboard**, clicar num card abre a gestão. **Removido do extrator** (`index.html` restaurado do backup pré-Surface-A/B — reverte nav item, `#painelTipsters`, modais de info/escada, JS e CSS `.un-*`; diff confirmado = só as minhas adições + o `mostrarView` original; `check-tokens` verde, JS OK). **Adicionado no dashboard** (`dash/charts/performance.js`): seção **"Gestão do tipster"** DENTRO do drill-down (`renderTipsterDrill`, que já abre ao clicar no card) — `#tipDrillGestao` renderizado por `renderGestaoTipster(nome)`: campos de info (casas/mercados/obs → `PATCH /tipsters/{id}/info`, via cache `_tipCadastro` nome→id de `GET /tipsters/cadastro`) + editor de escada (`GET/POST/DELETE /tipsters/unidades`, valor no `.money`); handlers usam `_drillBaseName` (sem escaping de nome); invalidam `_tipEscadas` (cache do switch C2) ao mudar. Estilo inline com tokens (idiom do drill). **Verificado:** `node --check` OK, `check-tokens` verde, **render headless on-brand** (título, info, escada 100→200, botões). Backend intacto (endpoints agora servidos pelo dashboard). Backup do revert = o próprio `Backups/fatia0-ui-painel-tipster_2026-07-14/`. **PENDENTE:** validação ao vivo (Ctrl+F5); polir `(i)` de incompleto no card (deferido — precisa `_tipCadastro` no render dos cards). Ver [[perfil_tipster_plano]].)_

_Anterior: 2026-07-14 (sessão 142c — **Perfil de Tipster — UI Surface A+B (painel de cadastro no extrator).** Depois que o editor de apostas (sessão 143) mergeou, construí a UI da Fatia 0 no `index.html` (arquivo diferente do dashboard → sem colisão). **Nav** ganhou item "Tipsters" (`mostrarView('tipsters')`, espelha `#nav-contas`); **painel** `#painelTipsters` no hub (empty-state), renderizado por `renderPainelTipsters`/`renderTipList` a partir de `GET /tipsters/cadastro` — espelha o Painel de Contas (`.painel-hero`/`.contas-tabs` Ativos·Inativos/`.contas-search`/`.conta-row`/`.conta-act`), com **badge `(i)` azul** (`.acct-badge pend`) nos incompletos + aviso azul contando quantos faltam; ações **Editar info / Renomear / Arquivar** (Reativar na aba Inativos). **Modal** `#tipster-info-modal` (casas/mercados/observações → `PATCH /tipsters/{id}/info`); Renomear via `prompt` → `POST /tipsters/{id}/renomear`. **Zero CSS novo** — só classes já provadas em produção; onclicks passam só `id` (sem injeção). **`/nova-ui` rodado inteiro:** §5 monetário N/A (não renderiza dinheiro); cor 100% token, tipografia mono/uppercase nos eyebrows/labels, componentes reusados. **Verificação:** `check-tokens` verde (5/5 shell), sintaxe JS (`vm.Script`, 0 erro), **render headless (Chrome)** de um harness com o `tokens.css`+CSS reais confirmou tema escuro on-brand (badge azul, abas, modal, Salvar primário). Backup `Backups/fatia0-ui-painel-tipster_2026-07-14/`. **Surface C1 (editor da escada de unidade) TAMBÉM FEITA:** botão "Unidades" na linha do tipster → modal `#tipster-unidade-modal` que lista os degraus (`GET /tipsters/unidades`, valor no `.money`/`moneyStake`), adiciona (`POST`, data DD/MM/AAAA + valor) e remove (`DELETE`); backend `UnidadeSegmentoRequest.valor` relaxado p/ `float|str` (aceita BR "1.234,50" via `_num_or_none`). Fix de layout: `.modal-body` é grid 2col → `.un-hint/#un-lista/.un-add` ganharam `grid-column:1/-1` (como `.modal-field.full`). Render headless confirmou (a escada 100→200 dos 135u). **Formato do "u" CRAVADO pelo Feca (`AskUserQuestion`):** `+3,25u` / `−1,50u` (sufixo, 2 casas, espelha `fmtPL`, zero neutro `0,00u`). **Surface C2 (switch R$⇄u no dashboard) TAMBÉM FEITA e VERIFICADA COM O APP AO VIVO:** helper `fmtU` em `dash/app.js` (espelha `fmtPL`, sufixo `u` neutro `+3,25u`, `.money-u`, zero neutro — o `fmtPL` do dash trata zero como `+`, desvio herdado que o `fmtU` NÃO copia); mirror JS `_uVigente`+`_tipsterUnidades` computa o u **sobre as linhas JÁ FILTRADAS** (respeita data/esporte/casa — por isso client-side, não o batch); toggle `.tcard-seg` "Exibir P/L em R$/u" no card Tipsters (pref. por dono no localStorage `dash_tipunit::<dono>`); `renderTipsters` busca `GET /tipsters/escadas` sob demanda e troca P/L Carteira + coluna P/L da tabela p/ `fmtU` (ROI/Turnover ficam em R$). **Backend:** `get_escadas_todas` + rota `GET /tipsters/escadas` (substituiu um endpoint batch que eu ia usar mas dava u sem filtro — errado p/ view filtrada). **Verificação com o app REAL (uvicorn local + `.env` + cookie forjado):** backfill de 61 tipsters no banco real, `resultado-unidades` E2E (Arrudex +1136,79u etc.), `/tipsters/escadas` `{}`, math client-side reproduz os 135u+fallback no node, **render headless on-brand** (toggle, KPIs e tabela em `u`). NÃO escrevi no prod (classifier barrou POST de teste, respeitado). `pytest` 116, `check-tokens` verde, JS `--check` OK. Backup `Backups/fatia1-ui-switch-unidades_2026-07-14/`. **Perfil de Tipster: Fatias 0 e 1 COMPLETAS (backend+UI).** PENDENTE: só validação ao vivo do Feca (Ctrl+F5). Ver [[perfil_tipster_plano]] · [[feedback_nova_ui_gate_total]].)_

_Anterior: 2026-07-14 (sessão 143 — **Editor de apostas: editar (lápis/modal) e deletar na página de Apostas + edição inline por duplo-clique nas duas telas.** Pedido do Feca: corrigir uma aposta já planilhada (ex.: tipster digitado errado) direto na aba Apostas, e ter duplo-clique para editar célula. Rodou em paralelo à sessão 142 (Perfil de Tipster). Sem colisão de arquivos: mexi só no dashboard (`dash/app.js`, `dash/charts/apostas.js`, `dash/components.css`, `dash/index.html`), no `index.html` do extrator, e na linha `id` do feed em `repository.py dashboard_rows` (esta foi absorvida no commit `26b72f1` da 142). **Etapa 1 (commit `8d42d67`):** coluna Ações na lista de Apostas com lápis (abre modal dos 10 campos, `PATCH /bilhetes/{id}`) e X (`DELETE /bilhetes/{id}`, com confirm). O feed passou a expor `id`. Editável só quando há id (Postgres) E a linha é do dono efetivo; linha de planilha ao vivo ou de operador em visão consolidada fica view-only (lápis apagado). Após salvar/deletar, `loadData(false)` re-busca o feed para o P/L derivado e KPIs baterem com o servidor. **Etapa 2 (commits `938665d` Apostas, `ba529f5` Extração):** duplo-clique numa célula troca por input (ou `<select>` no resultado); Enter/blur salva via `PATCH`, Esc cancela. Colunas: data, esporte, casa, parceiro, descrição, stake, odd, resultado (na Apostas também aposta e tipster). O Tipster da EXTRAÇÃO mantém o motor de planilha próprio (autocomplete/seleção); a categoria incerta mantém o clique que abre o modal. Na Apostas (virtualizada) a flag `_apInlineEditing` trava o virtual-scroll enquanto edita, para o input não sumir ao rolar. **Odd nunca truncada:** só campos alterados entram no patch, então uma odd intocada nunca é reenviada. **Verificação:** `check-tokens` verde, sintaxe JS (`vm.Script`) e Python (`ast`) OK, render headless (Chrome) confirmou modal, coluna de ações (editável vs view-only) e inputs inline nas duas telas. Reuso de `fmtR`/`fmtOdd`/`fmtPL`/`esc` (sem formatador caseiro). Backups `Backups/apostas-editar-deletar/` e `Backups/extracao-inline-dblclick/`. **Contexto:** duas sessões escreviam na mesma `main` (esta e a 142); os commits se intercalaram e o push levou os dois lados. **PENDENTE:** o Feca confirmou o lápis funcionando; validar ao vivo o duplo-clique nas duas telas (Ctrl+F5 na extração, que é HTML cacheado). Habilitar edição de linha de operador (visão consolidada) exigiria mexer no endpoint (hoje escopa por dono efetivo), fica p/ depois se pedir. Ver [[pl_calculo_derivado]] · [[feedback_marca_helpers_dinheiro]] · [[data_fuso_local_nunca_utc]].)_

_Anterior: 2026-07-14 (sessão 142 — **Perfil de Tipster — Fatia 0 (espinha do cadastro), BACKEND.** Frente nova aprovada pelo Feca ("vc decide, eu concordo"): dar existência real ao tipster, que hoje é só texto livre em `bilhetes.tipster`. Precedida de **3 scouts read-only em paralelo** (schema/derivação, fluxo do campo tipster, UI de dinheiro) que confirmaram o terreno pronto: `parceiros` + CRUD completo p/ espelhar, `list_tipsters`/`set_tipster_bulk` já existentes, regras do `/nova-ui §5` p/ o "u" futuro. **Decisão de identidade travada:** chave **`(dono, nome)`**, unificação por nome SEMPRE (mesmo tipster em N casas = 1 registro; separar = nomes distintos "João 365"). **Entregue nesta fatia (só backend, sem UI):** (1) tabela **`tipsters (id, nome, dono, casas, mercados, obs, arquivado, criado_em)`** UNIQUE `(dono, nome)` + **backfill idempotente** dos tipsters distintos já nos bilhetes (nascem incompletos) — em `database.py SCHEMA_SQL`, roda no boot; (2) em `repository.py`: `garantir_tipster` (auto-cadastro `ON CONFLICT DO NOTHING`, best-effort), `criar_tipster`, `list_tipsters_cadastro` (com flag `completo`), `arquivar`/`reativar`/`atualizar_tipster_info`/`renomear_tipster` (propaga rename p/ `bilhetes.tipster`, espelha `renomear_parceiro`); (3) **cadastro automático** enganchado em `set_tipster_bulk` + `atualizar_bilhete` — o tipster passa a existir no instante em que o nome é digitado; (4) rotas em `main.py`: `GET/POST /tipsters/cadastro`, `PATCH /tipsters/{id}/info`, `POST /tipsters/{id}/{arquivar,reativar,renomear}` (`dono_efetivo`), sem colidir com o `GET /tipsters` do autocomplete. **Verificação:** `compileall` OK, `pytest tests/` **107 verde**, rotas registradas conferidas por import. Backup `Backups/fatia0-cadastro-tipster_2026-07-14/`. **FATIA 1 (backend, motor de unidades) TAMBÉM FEITA na mesma sessão** — enquanto o editor de apostas do dashboard roda num terminal paralelo (mexe em `dash/app.js`+`components.css`; o motor de unidades é só `.py`, zero colisão, e sem render → sem `/nova-ui`): tabela **`tipster_unidade (dono, tipster, vigente_desde, valor)`** UNIQUE `(dono,tipster,vigente_desde)` = escada-degrau (`database.py`); funções PURAS **`unidade_vigente`** (degrau + clamp à esquerda) e **`pl_em_unidades`** (`Σ pl_R$ ÷ unidade_da_data`, fallback + flags `usou_fallback`/`sem_unidade`) junto de `calcular_pl` (`repository.py`); wrappers `get_escada_unidade`/`set_unidade`/`remover_unidade`/`resultado_em_unidades` (fallback = stake média do próprio tipster; plano sugere média global — trocar é 1 linha); `renomear_tipster` agora propaga p/ `tipster_unidade` também; rotas `GET/POST /tipsters/unidades`, `DELETE /tipsters/unidades/{id}`, `GET /tipsters/resultado-unidades` (tipster por query param, sem encoding no path). **`tests/test_unidades.py`** cobre o exemplo dos **135u** (prova que NÃO vira 90u dividindo tudo pela unidade atual) + clamp + fallback + prejuízo. `pytest tests/` **116 verde**. Backup `Backups/fatia1-unidades_2026-07-14/`. **PENDENTE (UI, espera o editor de apostas mergear p/ não colidir + passa pelo `/nova-ui` INTEIRO):** página de info do tipster + sinal `(i)` no `inicio.html` (Fatia 0 UI) e o **switch R$⇄u** + helper `fmtU` (Fatia 1 UI). **Regra reforçada pelo Feca:** nada visual sobe sem `/nova-ui` checando TODAS as regras (não só §5) — ver [[feedback_nova_ui_gate_total]]. **UI já ESPECIFICADA e auditada pelo `/nova-ui`** (rodado o checklist inteiro) em `docs/PLANO_TIPSTER.md §"UI — spec auditado"`: Surface A (painel de Tipsters no extrator, espelha Contas), B (modal de info), C (switch R$⇄u + `fmtU` espelhando `fmtPL`, no dashboard = espera o merge do editor de apostas). Não construída às cegas de propósito — o passo 4 do `/nova-ui` (verificação visual) exige subir o app com o Postgres. Doc-fonte `docs/PLANO_TIPSTER.md`. Ver [[perfil_tipster_plano]] · [[pl_calculo_derivado]] · [[feedback_marca_helpers_dinheiro]].)_

_Anterior: 2026-07-13 (sessão 141 — **Nome de casa de MODO CEGO mutilado no `/salvar` → conta paralela ("bets somem").** O Jonathan cadastrou **Esportiva Bet** (casa cega, sem `CASA_*.md`), extraiu 65 bilhetes ("65 novo(s)" no rail) e reclamou que "não aparecem — mostra só até dia 01". **Diagnóstico (só banco, sem pedir print):** os 65 (69 no banco, datas 30/06→13/07, todos resolvidos) **existiam**, mas em `casa='Esportivabet'` (sem espaço, `b` minúsculo) — grafia diferente da conta que ele olha (`casa='Esportiva Bet'`, 222 bilhetes importados 04/07, evento máx **01/07**). Duas contas paralelas. **Causa raiz:** round-trip de nome de casa no `/salvar` — como "Esportiva Bet" não está no mapa `_CASA_DISPLAY` (casa cega), `_display_to_key` fazia `upper.replace(" ","")` → `ESPORTIVABET` e `_casa_display` fazia `.title()` → `Esportivabet`. Atingia TODA casa cega de 2+ palavras (`Rei do Pitaco → Rei Do Pitaco`, `Faz1 Bet → Faz1Bet`). **Parte 2 (código, evita recorrência):** as duas funções viraram par inverso — fora do mapa, `_display_to_key` devolve o nome **verbatim** (só `.strip()`) e `_casa_display` devolve a chave **sem `.title()`** → round-trip IDENTIDADE; mapeadas seguem canonizando. **3 testes de regressão** em `tests/test_modo_cego.py` (verbatim / canonicaliza / idempotente); `conftest` ganhou stub `init_db` p/ importar `main`. Suíte **107 verde**. **Parte 1 (dado):** os 69 renomeados `Esportivabet → Esportiva Bet` **recalculando a `assinatura`** (embute a casa → senão re-extração futura viraria fantasma), 0 colisão (índice `dono,casa,parceiro,assinatura`; 222 antigos sem código); parceiro duplicado id 325 removido. Conta unificada **`Esportiva Bet · Pessoal` = 291 bilhetes**, dias 11/12/13-07 presentes. Backup `Backups/sessao141-casa-nome-modo-cego/` (main.py + JSON dos 69, gitignored). Ver [[extracao_worldwide_fase012]] · [[favicons_tres_mapas]] · [[dedup_gap_sem_codigo_reextracao]].)_

_Anterior: 2026-07-13 (sessão 140 — **Destaques Bookies/Tipsters da tela Início viram LEADERBOARD (PACK "Destaques Leaderboard") + auditoria /nova-ui.** Pedido do Feca: auditar regras de UI da tela Início ("fontes e coisas fora do padrão") e executar o PACK `Downloads/PACK - Destaques Leaderboard (Claude Code).md`. **Auditoria (`/nova-ui`):** `check-tokens` já verde e `fmtPL`/`fmtR` verbatim de `app.js`, cor só no `.money-val`, zero neutro (KPI usa `fmtR(0)` sem apostas) — tudo OK. Desvios reais: (1) os blocos **Bookies/Tipsters eram tabela `.rk` com grade dupla** (visual "Excel com bordas", `.rk-h` a 8.5px abaixo do piso 9–11px do `UI_REFERENCE §2`) → resolvido pelo PACK; (2) `.money-sign` a **0.76em** vs canônico **.78em** (index.html:1092) → corrigido. **Arquivo único** `app/static/inicio.html`, **Etapa 1 (CSS)** trocou `.dcols/.dcol/.rk-*` por **leaderboard** (`.dcols` 2 colunas com respiro, `.lb-h` 9px on-spec, `.lb-row/.lb-track/.lb-fill` barra de magnitude, `.casa-chip` favicon 24×24 raio7 steel, `.tip-chip` avatar redondo neutro); **Etapa 2 (JS)** removeu `rkTable`, reescreveu `destaques(map,noun,kind)` + `lbCol`/`casaFavicon`/`tipAvatar` (barra ∝ maior |P/L| da coluna, piso 3%). Casa = favicon Google S2 (`sz=128` p/ casar com `CASA_ICONS`, fallback inicial via `onerror`); tipster = avatar neutro (pessoa, sem cor). **`CASA_DOMAIN` copiado COMPLETO do `HOUSE_DOMAIN` canônico** (`dash/assets/js/data.js`) com ⚠️ comentário-ponteiro — não carreguei `data.js` (colide com `esc/SPORT_*/MESES` inline). Barra usa `rgba(var(--pos-rgb/--neg-rgb),.55)` (triplets existem em `tokens.css`). **Validação:** `check-tokens` **verde** (drift/paleta/shell/monetário); JS inline sem erro (`vm.Script`); zero resíduo das classes/funções antigas. Backup `Backups/inicio-leaderboard-destaques/`. **Ressalva:** `CASA_DOMAIN` é cópia — ao criar/renomear casa em `data.js`, replicar aqui. **Revisão ao vivo do Feca → 3 correções (commits `59c313a`, `47b09ec`):** (1) **favicons vinham COLORIDOS** — o `.casa-chip img` do PACK saiu sem filtro; apliquei o canônico do app (`grayscale(1) contrast(0.2) brightness(1.35)` + overrides de geometria Novibet/Esportiva/PixBet scale 1.3, BetMGM/BETesporte scale 1.5 via `data-casa`) — a marca **nunca** usa favicon colorido (`UI_REFERENCE §4`); (2) **avatar de letra do tipster removido** — não existe esse padrão no app (inicial só é fallback de casa); tipster = rank+nome+P/L+barra; (3) **`.lrow .t` fixado em Manrope 500 explícito** (herança sem peso parecia fonte errada só na pendência; casa o peso dos nomes do leaderboard `.lb-nm`). Vermelho do P/L/rótulo/barra **é permitido** (§1, semântica de resultado); o único fora-de-regra era o logo colorido → resolvido pelo grayscale. **(4) SELF-HOST das fontes (commit `0a696c6`):** o Feca ainda via fonte fora do padrão; auditoria confirmou que o CSS só usa as 2 fontes da marca (Manrope/JetBrains Mono), mas ambas vinham do `<link>` do **Google Fonts** → se o download falha, cai no fallback **Segoe UI** (parece off-brand). Decisão do Feca (`AskUserQuestion`): **self-host**. Baixei os `.woff2` oficiais (subsets **latin + latin-ext** = pt-BR, incluindo **U+2212** do `fmtPL`); ambas são **VARIÁVEIS** (md5 idêntico entre pesos) → **4 arquivos** em `app/static/fonts/` + 4 `@font-face` (faixa 400–800) em `app/static/fonts.css`. `inicio.html` troca o `<link>` do Google por `/static/fonts.css`. CSP já cobre (`font-src 'self'`). **Render headless (Chrome)** confirmou Manrope/JBM distintas do fallback serif, pesos e acentos OK. **Propagação CONCLUÍDA (commit `a866257`):** o self-host foi estendido ao app inteiro — `app.html` (casca), `index.html` (app), `login.html` e `dash/index.html` (dashboard) trocaram o `<link>` do Google Fonts por `/static/fonts.css`; nenhuma referência a `googleapis`/`gstatic` sobrou. **CSP apertada:** `style-src` e `font-src` viraram `'self'` (removido Google); `img-src https:` mantido (favicons das casas via S2). **(5) FAVICONS — Vitória Bet + reconciliação (commit `c028e6b`):** o Feca viu o favicon da Vitória Bet como globo na tela Início. Auditoria (script S2, 48 domínios): **TODOS resolvem p/ favicon real, 0 quebrados** → o problema era **drift entre 3 mapas** de domínio (`index.html DOMINIOS` = vivo/completo; `data.js HOUSE_DOMAIN`/`CASA_ICONS` = defasado; a cópia `CASA_DOMAIN` do `inicio.html` = incompleta). Corrigido: (a) `inicio.html CASA_DOMAIN` agora **espelha o `DOMINIOS` do index verbatim** (cross-check = cobertura 100%, 0 divergência) + fallback tira acento; (b) `data.js` (que o dashboard usa via `casaDomain()`) ganha as **4 casas só-do-Planilhador** (Vitória Bet, KingPanda, Lottu, Jogo de Ouro) e `Rei do Pitaco → pitaco.bet.br`. Os 3 mapas agora concordam. **Lição:** o mapa de favicon vive em 3 lugares — ao adicionar casa, atualizar os 3 (`index.html DOMINIOS`, `data.js HOUSE_DOMAIN`+`CASA_ICONS`, `inicio.html CASA_DOMAIN`). Ver [[railv2_raiox]] · [[feedback_marca_helpers_dinheiro]] · [[fontes_self_host]] · [[favicons_tres_mapas]].)_

_Anterior: 2026-07-13 (sessão 139 — **Sidebar do menu: presença visual (PACK "Menu Sidebar").** Aplicado o PACK `Downloads/PACK - Menu Sidebar (Claude Code).md` — só aparência da navegação, sem mexer em estrutura/ícones/rotas/ordem. **Arquivo único** `app/static/shell.css` (Fatia 1 = casca compartilhada Planilhador + Dashboard, `.nav-group/.nav-item/.nav-icon`). Três defeitos → três correções: (1) linha ativa full-bleed + tab 2px → **pílula inset arredondada** (`margin:1px 10px`, `border-radius:var(--r-sm)`) com **fundo degradê azul** (`linear-gradient` sobre `--accent-rgb` alpha .24→.10), hairline interna (`box-shadow inset ... rgba(--accent-rgb,.35)`), **aba curta arredondada** à esquerda (`::before` 3×18px `var(--accent)`) e texto branco; (2) ícones de `--ink-mute` (cinza morto) → **`--ink-soft` em repouso** (vivos), `--accent-2` no ativo; (3) grupos que somem → **hairline** (`::after` `var(--line-2)`) após o rótulo mono. As travas de `font-size` do SHELL_SPEC seguem intactas (`--text-nano` no grupo, `--text-sm` no item → shell 5/5). Literais `#fff`/`rgba(255,255,255,.045)` **não** estão na lista de cores banidas do `check-tokens` (só WARN informativo); tokens `--line-2`/`--r-sm`/`--accent-2` confirmados em `tokens.css`. `/nova-ui` + `check-tokens` **verde** (drift/paleta/shell/monetário). Backup `Backups/shell-css-sidebar-pilula/`. Commit `3d66abd`. **PENDENTE:** revisão AO VIVO do Feca (item ativo como pílula/aba, legibilidade em `data-theme="light"`) — vale nos DOIS apps. Ver [[programa_governanca_marca]] · [[feedback_marca_helpers_dinheiro]].)_

> **Histórico completo das sessões 138 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

Os 6 MASTER_*.md vivem em `/global/`; as 15 casas em `/casas/` (Polymarket por API, as demais por IA/texto).

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`).
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Casas:** 15 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências (aguardam bilhete real)

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus · §9 (23 categorias aguardam amostra)

**Próximo passo:**
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

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
