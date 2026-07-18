# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-18 (sessão 153 — **UI: reorganização do rodapé da sidebar da casca (`.sidebar-bottom` do `app.html`) em tiers.** Feedback do Feca (Bloco 2 já tinha movido o operador pro rodapé, mas o bloco ficou frouxo — elementos soltos, espaço morto, botões empilhados de peso igual). Rodapé reordenado em **5 tiers** do topo pra base: (1) **Operador** (`#sbOperador` — caixa clicável `--surface-2`/borda `--line`, já existente); (2) **Status de sync** (`.last-update` — dot pulsante + "Dados sincronizados" à esquerda, **timestamp `15/07 · 01:02` empurrado à direita** via `.sync-time{margin-left:auto}`, mono 10px `--ink-mute`); (3) **Ações pareadas** — "Baixar CSV" + "Atualizar" num `.sb-actions` **grid 1fr 1fr gap 6px** (antes empilhados), ambos **ghost mono** com ícone 13px, hover borda azul `rgba(var(--accent-rgb),.4)` (base visual unificada entre `.sb-csv` e `.host-refresh`); (4) **Sair** full-width discreto (`--ink-mute`), hover vermelho `rgba(var(--neg-rgb),.45)`+`--neg` (sem cara de desabilitado); (5) **Endosso** "by FDC Capital" centralizado mono 9px uppercase `.16em` `opacity .65`. Container `.sidebar-bottom` virou `flex-column` com `margin-top:auto`, `padding 14px 6px 4px`, `gap 10px` (ritmo por gap, sem margens soltas nos filhos). **JS preservado:** `paintSync`/`fmtSync` reestruturados p/ emitir `.sync-label`+`.sync-time` (timestamp à direita) e `setRefreshing` encurtado p/ "Atualizar"; handlers `#hostLogout`/`.sb-csv`/`#hostRefresh` intactos. **Marca:** sem R$/número na tela (§5 N/A), só tokens; `/nova-ui` cumprido — `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação), JS inline validado (0 erro), **render headless conferido** (5 tiers batem o spec). CSS/JS inline no `app.html` (documento de navegação, sem `?v=` a bumpar; Ctrl+F5). Backup em `Backups/sidebar-bottom-reorg-app-html/`. Ver [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total.md]].)_

_Anterior: 2026-07-18 (sessão 152 — **UI: refino visual da tela "Casas · atribuição por casa" (feudo).** A tela de curadoria de casa-feudo (card na página Tipster / Método, `gestao.js`) tinha subido crua; o Feca pediu pra deixar on-brand. `_casaRow` reescrito: **barra de pureza** por casa (share do tipster top — cheia + `--accent` = feudo, toco + `--ink-mute` = compartilhada; lê monogamia num relance), hierarquia limpa (favicon + nome forte via `mkHouseChip`, meta mono discreta), **toggle segmentado** único (ativo em `--accent` cheio + `#fff`), **borda `inset 3px --accent`** à esquerda nas curadas, chip de estado (`curada`/`compartilhada`/`sugerido`). `renderCasasFeudo` ganhou linha de **resumo** (N casas · X feudos · Y curadas) e `renderCasasLista` passou a **ordenar feudos primeiro** (por pureza), o resto por volume. Reusa `mkHouseChip`/`fmtPct`/`fmt` — zero formatador novo, sem R$ na tela. `/nova-ui` cumprido: `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação), `node --check` OK, auto-auditoria §5 limpa. Bump `gestao.js?v=12→13`. Backup em `Backups/casas-visual-redesign-s151/`. Verificação visual ao vivo pendente (Ctrl+F5). Ver [[matcher_sugerir_tipsters]] · [[feedback_nova_ui_gate_total.md]].)_

_Anterior: 2026-07-18 (sessão 151 — **UI Bloco 1: tela "Gestão de Contas & Parceiros" (feedback do Feca, prints).** Redesenho da visão de Contas — que é o **estado sem conta ativa do `index.html`**, não uma página separada. Fechado com o Feca via `AskUserQuestion`: **Bloco 1 (tela Contas) primeiro, Bloco 2 (operador→sidebar) depois**; operador vai pra sidebar como **só identidade**. **Bloco 1 FEITO (commit `PENDENTE`, `index.html`):** (1) **título único** — o pagehead vira "Gestão de Contas & Parceiros" (`mostrarView`); o hero perdeu o título/eyebrow duplicado "Painel de contas", sobrou só o "+ Nova conta" alinhado à direita. (2) **linha de conta ativa inteira clicável** → `contasAbrir` abre o perfil na Extração (`.conta-row.clickable` + `onclick`; removido o botão "Abrir" redundante; Renomear/Arquivar com `event.stopPropagation()`). Arquivadas seguem sem clique (não têm perfil vivo). (3) **tick azul de marca** (`::before` 4×13 `--accent`, SHELL_SPEC §3) nos 4 headers de card (Contas, Contas por casa, Custos por fornecedor, Atividade). (4) **lista mais estreita** (`.painel-top` 1.25fr→1.6fr/1fr). (5) **RAIO-X escondido na visão Contas** — `mostrarView('contas')` põe `.rail--histonly` no `#rail` (grid 7fr/3fr → 1fr, some o `.rail-card--raiox`), deixando só o histórico; volta ao entrar na Extração. **Marca:** sem R$ novo (custos seguem `_moneyInt`); só tokens; `/nova-ui` cumprido — `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação), JS inline validado (2 blocos, 0 erro). JS/CSS inline no `index.html` (sem `?v=`; Ctrl+F5). Backup em `Backups/contas-redesign-bloco1/`. **Bloco 2 FEITO (commit `PENDENTE3`):** identidade do operador movida pro rodapé da sidebar da casca. `app.html` ganhou `#sbOperador` no `.sidebar-bottom` (nome + trocador "ver base de", só p/ donos com operadores; `POST /ver-como` + `location.reload()` recria os iframes com o novo dono efetivo; Sair segue no `#hostLogout` já existente). `index.html`: removido o `.idcard__op` (idcard agora foca em **Casa | Parceiro + Trocar conta**); `carregarUsuario` mantém o trabalho **load-bearing** (`window.__donoEfetivo`, `renderHist`, custos) com os writes de DOM do operador **guardados** (elementos não existem mais no iframe); removidas a IIFE do menu operador e o listener `btn-logout`; `mostrarView('contas')` esconde o `.arow` (idcard + tiles vazias) → some o box OPERADOR e o espaço vazio da tela de Contas, painel sobe. `check-tokens` verde; JS inline 0 erro (index+app); backup em `Backups/operador-sidebar-bloco2/`. Testar ao vivo: troca de operador (donos) + Sair + Casa|Parceiro na Extração. **Refino Bloco 1 (feedback do Feca, commit `PENDENTE2`):** (a) colunas do `.painel-top` **invertidas** — **esquerda = painel de lista** com o resumo CONTAS/14% ativas como **cabeçalho da lista** (`resumoHead` → `.painel-lista-resumo`, não mais card solto), **direita = Contas por casa**; (b) **tick azul** (`::before` 4×13 `--accent`) adicionado ao header do histórico (`.hist__head` → "Últimas ações"); (c) **"+ Nova conta"** movido do topo flutuante pra dentro do card CONTAS (linha dos totais, `.painel-nova-conta` com `margin-left:auto`); `hero` fica só no estado sem contas; (d) **idcard da Extração empilhado** — `.idcard__foot` vira coluna: "Trocar conta"→**"Selecionar conta"** full width em cima, **editar | arquivar 50/50** embaixo. `check-tokens` verde, JS inline 0 erro. Verificação visual ao vivo pendente. Ver [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total.md]].)_

_Anterior: 2026-07-18 (sessão 150 — **UI: painel "Apostas em Aberto" da Início ganha info por linha, toggle e rodapé fixo.** Feedback do Feca (print da Início). As linhas de apostas abertas mostravam só o tipo (`Múltipla`) + casa · parceiro · esporte: faltava **descrição** e **tipster**. O "+N outras em aberto" era texto morto (não expandia) e o "Capital em aberto" flutuava no meio do box em vez de ficar na base. **Fix (`app/static/inicio.html`, commit `PENDENTE`):** (1) helper `ejRow` — título = **descrição** (a substância); subtítulo = **tipo · tipster · casa · parceiro · esporte** (tipo só entra no sub quando o título já é a descrição, sem duplicar; fallback do título p/ tipo/esporte quando não há descrição). (2) "+N outras" virou **linha clicável** (`.ejtoggle`, id `emjogo-toggle`) que dobra/desdobra o excedente das 7 primeiras (▾ / ▴ "mostrar menos"). (3) `#emjogo-list` ganhou `flex:1` + `overflow-y:auto` + `min-height:0` → a lista cresce e rola por dentro, **fixando o rodapé "Capital em aberto" na base do box**. Os dados já vinham do `/bilhetes` (`SELECT *`: descricao/tipster/aposta presentes) — era só render, sem toque no backend. **Marca:** reusa `moneyStake`/`fmtOdd` (stake+odd) e `fmtR` (capital), toggle só com tokens `--accent-2`/`--accent`, zero formatador novo, sem cor literal. `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação monetária); auto-auditoria §5 limpa. JS inline no `inicio.html` (sem `?v=` a bumpar). Backup em `Backups/inicio-apostas-aberto-info-expand/`. Verificação visual ao vivo pendente (Ctrl+F5). Ver [[feedback_nova_ui_gate_total.md]] · [[feedback_marca_helpers_dinheiro]].)_

_Anterior: 2026-07-18 (sessão 149 — **UI: botão "Sugerir tipsters" vira ouro duotone + glow (material do Feca).** O botão da barra de ações da Extração (`index.html`) usava o emoji ✨ — único elemento flat/multicolor numa UI que só usa glyphs de traço (Lucide, stroke 1.7) + paleta FDC. Trocado por um glyph de sparkles em **traço** (dois `path`, `currentColor`) + tratamento **ouro duotone**: fundo em gradiente dourado suave, **borda gradiente via `::after` mascarado** (XOR) e `box-shadow` de glow. Sinaliza "função especial/inteligente" **sem competir com o primário azul** (só o `+ Inserir aposta` é primário; a barra segue com **um** azul). **Integração com a base:** classe `.btn--gold-duo` **herda** padding/font/radius de `.btn`+`.btn-sm` (spec standalone tinha esses; removidos p/ não duplicar); trocado `btn-ghost`→`btn--gold-duo` (o hover do ghost sobrescreveria o fundo dourado). `position:relative` mantido (ancora o `::after`). **Marca:** os golds (#F6D98A→#C9963C, texto #F2D9A0) derivam da família `--d-proj` (#D6A45A, camada de diagnóstico); **não** entram na lista BANIDA do `check-tokens` (cyan/azul-off/Tailwind) → guardrail **verde** (literais golds só contam no WARN informativo, não-bloqueante). `/nova-ui`: sem R$/número/formatador na tela; `check-tokens` OK (5/5 shell, sem cor banida, sem abreviação monetária). CSS inline no `index.html` (sem `?v=` a bumpar). Backup em `Backups/botao-sugerir-gold-duo/`. Verificação visual ao vivo pendente (Ctrl+F5). Ver [[matcher_sugerir_tipsters]] · [[feedback_nova_ui_gate_total.md]] · [[programa_governanca_marca]].)_


> **Histórico completo das sessões 148 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
