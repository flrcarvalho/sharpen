# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-18 (sessão 151 — **UI Bloco 1: tela "Gestão de Contas & Parceiros" (feedback do Feca, prints).** Redesenho da visão de Contas — que é o **estado sem conta ativa do `index.html`**, não uma página separada. Fechado com o Feca via `AskUserQuestion`: **Bloco 1 (tela Contas) primeiro, Bloco 2 (operador→sidebar) depois**; operador vai pra sidebar como **só identidade**. **Bloco 1 FEITO (commit `PENDENTE`, `index.html`):** (1) **título único** — o pagehead vira "Gestão de Contas & Parceiros" (`mostrarView`); o hero perdeu o título/eyebrow duplicado "Painel de contas", sobrou só o "+ Nova conta" alinhado à direita. (2) **linha de conta ativa inteira clicável** → `contasAbrir` abre o perfil na Extração (`.conta-row.clickable` + `onclick`; removido o botão "Abrir" redundante; Renomear/Arquivar com `event.stopPropagation()`). Arquivadas seguem sem clique (não têm perfil vivo). (3) **tick azul de marca** (`::before` 4×13 `--accent`, SHELL_SPEC §3) nos 4 headers de card (Contas, Contas por casa, Custos por fornecedor, Atividade). (4) **lista mais estreita** (`.painel-top` 1.25fr→1.6fr/1fr). (5) **RAIO-X escondido na visão Contas** — `mostrarView('contas')` põe `.rail--histonly` no `#rail` (grid 7fr/3fr → 1fr, some o `.rail-card--raiox`), deixando só o histórico; volta ao entrar na Extração. **Marca:** sem R$ novo (custos seguem `_moneyInt`); só tokens; `/nova-ui` cumprido — `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação), JS inline validado (2 blocos, 0 erro). JS/CSS inline no `index.html` (sem `?v=`; Ctrl+F5). Backup em `Backups/contas-redesign-bloco1/`. **Bloco 2 PENDENTE (aprovado, aguarda revisão do Bloco 1):** mover `.idcard__op` (nome do operador + trocar operador + Sair) pro `.sidebar-bottom` da casca `app.html` (cross-iframe); na Extração sobra só Casa|Parceiro + Trocar conta; some o box OPERADOR da tela de Contas (resolve o espaço vazio). Verificação visual ao vivo pendente. Ver [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total.md]].)_

_Anterior: 2026-07-18 (sessão 150 — **UI: painel "Apostas em Aberto" da Início ganha info por linha, toggle e rodapé fixo.** Feedback do Feca (print da Início). As linhas de apostas abertas mostravam só o tipo (`Múltipla`) + casa · parceiro · esporte: faltava **descrição** e **tipster**. O "+N outras em aberto" era texto morto (não expandia) e o "Capital em aberto" flutuava no meio do box em vez de ficar na base. **Fix (`app/static/inicio.html`, commit `PENDENTE`):** (1) helper `ejRow` — título = **descrição** (a substância); subtítulo = **tipo · tipster · casa · parceiro · esporte** (tipo só entra no sub quando o título já é a descrição, sem duplicar; fallback do título p/ tipo/esporte quando não há descrição). (2) "+N outras" virou **linha clicável** (`.ejtoggle`, id `emjogo-toggle`) que dobra/desdobra o excedente das 7 primeiras (▾ / ▴ "mostrar menos"). (3) `#emjogo-list` ganhou `flex:1` + `overflow-y:auto` + `min-height:0` → a lista cresce e rola por dentro, **fixando o rodapé "Capital em aberto" na base do box**. Os dados já vinham do `/bilhetes` (`SELECT *`: descricao/tipster/aposta presentes) — era só render, sem toque no backend. **Marca:** reusa `moneyStake`/`fmtOdd` (stake+odd) e `fmtR` (capital), toggle só com tokens `--accent-2`/`--accent`, zero formatador novo, sem cor literal. `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação monetária); auto-auditoria §5 limpa. JS inline no `inicio.html` (sem `?v=` a bumpar). Backup em `Backups/inicio-apostas-aberto-info-expand/`. Verificação visual ao vivo pendente (Ctrl+F5). Ver [[feedback_nova_ui_gate_total.md]] · [[feedback_marca_helpers_dinheiro]].)_

_Anterior: 2026-07-18 (sessão 149 — **UI: botão "Sugerir tipsters" vira ouro duotone + glow (material do Feca).** O botão da barra de ações da Extração (`index.html`) usava o emoji ✨ — único elemento flat/multicolor numa UI que só usa glyphs de traço (Lucide, stroke 1.7) + paleta FDC. Trocado por um glyph de sparkles em **traço** (dois `path`, `currentColor`) + tratamento **ouro duotone**: fundo em gradiente dourado suave, **borda gradiente via `::after` mascarado** (XOR) e `box-shadow` de glow. Sinaliza "função especial/inteligente" **sem competir com o primário azul** (só o `+ Inserir aposta` é primário; a barra segue com **um** azul). **Integração com a base:** classe `.btn--gold-duo` **herda** padding/font/radius de `.btn`+`.btn-sm` (spec standalone tinha esses; removidos p/ não duplicar); trocado `btn-ghost`→`btn--gold-duo` (o hover do ghost sobrescreveria o fundo dourado). `position:relative` mantido (ancora o `::after`). **Marca:** os golds (#F6D98A→#C9963C, texto #F2D9A0) derivam da família `--d-proj` (#D6A45A, camada de diagnóstico); **não** entram na lista BANIDA do `check-tokens` (cyan/azul-off/Tailwind) → guardrail **verde** (literais golds só contam no WARN informativo, não-bloqueante). `/nova-ui`: sem R$/número/formatador na tela; `check-tokens` OK (5/5 shell, sem cor banida, sem abreviação monetária). CSS inline no `index.html` (sem `?v=` a bumpar). Backup em `Backups/botao-sugerir-gold-duo/`. Verificação visual ao vivo pendente (Ctrl+F5). Ver [[matcher_sugerir_tipsters]] · [[feedback_nova_ui_gate_total.md]] · [[programa_governanca_marca]].)_

_Anterior: 2026-07-17 (sessão 148 — **Matcher de tipster: distintividade contextual da stake + dono único sobrevivente.** Feedback do Feca (7 prints da carteira dele, extração ao vivo). Dois falsos-positivos e dois falsos-negativos reais. **Diagnóstico (read-only via `.env`, cadastro + banco + porta do matcher rodada nas 7 apostas):** (1) **Australia era ímã de stake 300** — a dica dela é só "300", e o gate `size===1` do `_stakeSignal` dava peso 25 (fingerprint) mesmo 300 sendo declarada por **8 tipsters** (M&M, SóChutes, Várzea…). O comentário do código prometia "STAKE distintiva (≤2 donos)" mas isso **nunca fora implementado**. Confusão `SóChutes→Australia(22)` era a 3ª maior do Feca no backtest. (2) **DartsVader não passava a folga-7 sozinho** — único candidato de Dardos (score 3, tudo compartilhado + stake redonda=0), mas a folga é contra o 2º lugar (=0) → 3<7 → vazio. (3) Os "BFM" dos prints eram **resíduo de versão anterior**: o código atual já veta o BFM (final 2) em stake quebrada → deixa em aberto (correto). (4) `Sonny` levou uma múltipla do `Fezinha` porque ela foi classificada **Futebol** (devia ser `Múltiplos`, regra dos 3 jogos) → filtro duro tirou o Fezinha; **raiz de extração, frente separada (Fix 3, não feito)**. **Fix (commit `PENDENTE`):** (a) helper `_declaraStake` (membership: quantos sobreviventes DECLARAM aquele stake, ignora tamanho de lista) + gate `stakeDistinta = claimants ≤ 2` no `_sugParaBilhete` — stake declarada por ≥3 donos NO CONTEXTO (após filtro de esporte) vira ruído (peso 0). Mede por DECLARAÇÃO, não por pontuação (senão valor comum de vários donos passa batido). O `size===1` do `_stakeSignal` foi **mantido** (é load-bearing: separa "é minha assinatura única" de "é um dos vários que aposto" — tirá-lo fez o M&M virar ímã, `Peixe→M&M(391)`, revertido). (b) **Dono único sobrevivente do esporte → sugere sem exigir folga** (não há concorrente). Espelhado no `scripts/backtest_matcher.py` (porta fiel). **Validação (backtest 30d):** Feca precisão **86%→86%** (sem regressão), cobertura **56%→58%**, `SóChutes→Australia` sumiu do top; Jonathan **97%** intacto; `Regista→Robotenis(21)` que subiu ao top-3 já existia no baseline (comportamento idêntico). **7 apostas dos prints:** dardos 500/400 → **DartsVader** ✅; anytime/múltipla 300 → **vazio** (300=4 donos → ruído; SóChutes sem assinatura própria → aberto é o certo pela régra "melhor vazio que errado") ✅; halfada 201,93/161,54 → **vazio** ✅; só o Sonny/Fezinha resta (Fix 3). Sintaxe node OK. **Fix 3-A FEITO (mesmo dia, commit `PENDENTE2`):** o prompt de extração `main.py:525` dizia *"mesmo esporte em todas → esse esporte; misto → Múltiplos"* — **contradizia** o `MASTER_ESPORTES §2` reescrito na s146 (não capturava "acumulada de 3+ confrontos [A v B] diferentes → Múltiplos"). Por isso TODA múltipla de jogos diferentes entrava com o esporte do jogo (Futebol), e o filtro duro do matcher tirava o Fezinha (esporte=Múltiplos). Prompt corrigido pra espelhar o MASTER (mistura de esportes OU 3+ confrontos distintos → Múltiplos; 1–2 seleções ou bet builder mesmo-confronto → esporte do jogo). Sintaxe `ast.parse` OK. Vale nas próximas extrações. **Fix 3-B (backfill) NÃO feito — decisão do Feca:** medido read-only, **1897 bilhetes** têm 3+ confrontos distintos mas esporte ≠ Múltiplos (Feca 1446: SóChutes 702, M&M 472, Peixe 116…; Jonathan 440; Lava 11). Reclassificar contraria a decisão da s146 ("corrigir só Fezinha+Arrudex, deixar o passado dos outros intocado"). **Feca decidiu NÃO mexer nas antigas ("de boa") — passado intocado; só o forward-fix vale, a re-extração corrige aos poucos.** **FRENTE NOVA — Casa-feudo (auto-atribuição por casa).** Sacada do Feca: a gente afinou o tipster por stake/mercado/esporte mas nunca por CASA. Muitas casas de nicho são monogâmicas na operação (na BETesporte é sempre Peixe, independente do valor). Medido read-only: na carteira do Feca, ~**28% do volume** está em casa-feudo (BETesporte 99% Peixe, Lottu 99%, Jogo de Ouro 100%, Vitória Bet 100% Nomade, 7K 94% Rei do Under…), enquanto Bet365 é 19% no topo (58 tipsters = ruído). **Simulação do modelo** (holdout temporal limpo, casa 1-dono crava / 2-donos restringe+stake desempata / 3+ normal, ADITIVO — nunca suprime o baseline): Feca **cobertura 58%→62%, precisão 86%→88%** (ganho Pareto); fatia casa-1-dono 96%, casa-2-donos 100%. Jonathan não deu p/ medir (base importada, sem split temporal). **Etapa 1 (registro + curadoria, SEM plugar no matcher):** **1A FEITO (commit `PENDENTE3`):** tabela `casa_config` (dono, casa, modo 'dedicada'|'multi', tipsters CSV 1-2); `repository.casas_visao` (pureza observada só de rótulos HUMANOS → sem circularidade + sugestão de feudo: dono ativo ≥10% individual, máx 2, só 'dedicada' se cobrem ≥85% do volume) e `salvar_casa_config`; rotas `GET/POST /casas/config`. Verificado contra o banco real (39 casas, sugestões batendo: feudos→dedicada, Bet365/Betano→multi) + round-trip save/delete + validação (dedicada exige 1-2). `pytest` **140 verde**. **1B FEITO (commit `PENDENTE4`):** seção **"Casas · atribuição por casa"** na página Tipster/Método (`gestao.js` `renderCasasFeudo`, terceiro card — decisão de ficar na mesma página em vez de nav nova = menor risco de casca/dual-sidebar). Cada casa mostra evidência (`N apostas · top X% · M tipsters`), toggle **Dedicada/Compartilhada** + selects de tipster (1-2), auto-salva no `POST /casas/config`; chip `sugerido`→`curada`; botão "Aplicar N sugestões pendentes" em lote; busca. Reusa `casaCell`/`mkCard`/`fmtPct`/`fmt`/`_tmIV` (zero formatador novo, sem R$ na tela). `/nova-ui` cumprido: `check-tokens` verde, `node --check` OK, auto-auditoria §5 limpa; bump `gestao.js?v=11→12`. Verificação visual ao vivo pendente (Ctrl+F5). **Etapa 2 FEITA (commit `PENDENTE6`):** casa-feudo plugado no matcher. `index.html`: núcleo `_sugRanqueia(b,idx,allowed)` (pool opcional) extraído do `_sugParaBilhete`, que agora consulta `_casasDedicadas` (carregado de `/casas/config`, só `modo='dedicada'`): **1 dono → crava** (retorna direto), **2 donos → restringe o pool aos 2** e o resto do matcher (stake) desempata, senão **cai no baseline (aditivo, nunca suprime)**. `carregarCasasDedicadas()` roda junto do `carregarPerfisTipster` no `sugerirTipstersLote`. Espelhado no `backtest_matcher.py` (`suggest` vira wrapper de casa-feudo sobre `_ranqueia`, lê `casa_config`). **Validação:** `node --check` OK; backtest fiel com `casa_config` VAZIO → `feudos=0`, baseline **intacto** (Feca 58%/86%, Jonathan 45%/97%) = **dormente até curar, zero regressão**; simulação (curadoria=sugestões, holdout temporal) → Feca **58%→62% cob / 86%→88% prec**, casa-1-dono 96% / 2-donos 100%. **Ativa quando o Feca curar** (tela Casas / "Aplicar sugestões"). Matcher inline no `index.html` (sem `?v=`; Ctrl+F5). **LIMPEZA — órfãos de cadastro (commit `PENDENTE5`):** typo corrigido na base (bilhetes re-atribuídos) deixava a linha do tipster órfã na tabela `tipsters` sujando a lista (o backfill do boot só ADICIONA). Pedido do Feca: "typo corrigido → some da lista". `list_tipsters_cadastro` agora **poda** no carregamento: `DELETE` guardado de tipster com **0 bilhetes E nenhuma info** (nunca apaga quem tem bilhete — o backfill traria de volta — nem quem tem info curada). Não há criação manual de tipster na UI, então 0 bilhetes = sempre órfão → seguro. Espelho read-only confirmou alvo = exatamente os **8** atuais (Feca: CtrlAltGreen, CtrlGreen, nom; Jonathan: BO, DartsLove, Darts Vader, fez, Só Chuets); somem no 1º load pós-deploy e qualquer typo futuro some ao reabrir. Delete direto em prod foi barrado pela camada de segurança (correto) → fix roda no app, não avulso. `pytest` **140 verde**. **PENDENTE geral:** deploy (matcher inline no `index.html`, Ctrl+F5). Ver [[matcher_sugerir_tipsters]] · [[assinatura_tem_era]] · [[multiplos_regra_jogos_diferentes]] · [[fase0_procedencia_baseline]].)_

> **Histórico completo das sessões 147 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
