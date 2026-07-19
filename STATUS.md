# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-19 (sessão 158 — **Onda 1 da Auditoria Turbo: 4 correções aplicadas e no ar** (uma por commit, backup em `Backups/onda1-turbo-2026-07-19/`, 140 testes + check-tokens verdes em cada). (1) `database.py` — CREATE parceiros movido para ANTES dos `UPDATE parceiros` (rodavam antes da tabela existir → rollback do SCHEMA_SQL inteiro em banco vazio: DR/novo cliente/dev local nunca inicializavam) — commit `201b223`. (2) `main.py` — `/polymarket/sync` passou de `Depends(dono_efetivo)` p/ `usuario_atual` (era a única rota de CRIAÇÃO gravando na base do operador visualizado em modo "ver como"; alinha a /extrair, /salvar, /bilhetes/manual — regra da sessão 82) — `eee55c1`. (3) `dashboard` — P/L **zero neutro** no `fmtPL` (§5.1: pintava zero de verde com "+"; toda Void/cashout=stake) + espelhos de texto `_txtPL` (temporal) e tooltip mensal (overview); bump app.js 20→21, overview 7→8, temporal 3→4 — `31166ad`. (4) `dashboard` — tooltip do gráfico de Esportes vazava HTML cru (`fmtPL`→`_txtPL` no canvas; os 24 `fmtPL` restantes são render de innerHTML, corretos) + `.dot.hw/.hl` deixaram de ser **âmbar idêntico** → verde/vermelho apagados `rgba(var(--pos-rgb/--neg-rgb),.5)` (distintos entre si e do W/L cheio, sem `!important`); bump performance 9→10, components 10→11 — `d2f23ba`. **PENDENTE (amanhã, COM o Jonathan):** itens #1/#2 do custo por tipster — o incidente do Jonathan (localStorage não sincroniza entre PCs) reorientou a correção para **migração ao Postgres com recuperação MANUAL disparada do PC do trabalho** (não auto-migrar; ver memória `custo_tipster_incidente_jonathan`). Relatório completo em `docs/AUDITORIA_TURBO_2026-07-19.md` + `docs/auditoria_turbo/`. Verificação visual ao vivo (Ctrl+F5) pendente.)_

_Anterior: 2026-07-18 (sessão 157 — **UI: "Baixar CSV" de-triplicado → toolbar da aba Apostas (passo 1 de 2 do rodapé da casca).** Decisão do Feca: o export pertence à **aba Apostas** e o comportamento **fica dump cru de backup** (confirmado via `AskUserQuestion`) — backend `/exportar.csv` (`main.py:1710`) **intocado** (todas as linhas/colunas do dono, `;`+BOM). O mesmo `<a href="/exportar.csv">` estava **triplicado**; consolidado em 1: **removido** dos 3 rodapés — `.sb-actions` da casca (`app.html`), sidebar do dashboard (`dash/assets/js/app.js`) e rodapé da Extração (`index.html`) — e **adicionado** na toolbar da aba Apostas (bloco de "Busca rápida por coluna", ao lado do "✕ Limpar"), rótulo **"Baixar base (CSV)"**, estilo ghost mono casando com o Limpar (tokens `--line`/`--ink-mute`, hover borda `--accent`; sem cor nova). Limpeza: `.sb-actions` da casca virou grid **1 coluna** (só resta "Atualizar") + regras `.sb-csv` órfãs removidas de `app.html`, `index.html`, `dash/.../layout.css`. **Marca:** botão sem R$/número (§5 N/A); `/nova-ui` cumprido — `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação), `node --check` do `app.js` OK, zero `sb-csv` restante. Bump `dash/index.html`: `layout.css?v=6→7`, `app.js?v=19→20`. Backup em `Backups/csv-para-aba-apostas/`. Verificação visual ao vivo pendente (Ctrl+F5). **Passo 2 pendente:** gatear o botão "Atualizar" (`#hostRefresh`) por `planilha_ao_vivo(dono)` (expor flag no `/me`; esconder pra base Postgres). Ver [[rodape_sidebar_botoes_decisao]] · [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total.md]].)_

_Anterior: 2026-07-18 (sessão 156 — **Dedup CRUZADA em conta compartilhada (Feca ↔ Lava).** O Feca repassou ao operador Lava uma conta que ele mesmo usou e arquivou (`Betano / yasmimsoaresbets [JC]`). Regras do Feca: (1) o que o Lava planilhar = resultado do Lava; (2) não pode duplicar o que o Feca já planilhou. **Diagnóstico:** a Regra 1 já valia (extração carimba `dono`=logado; dedup é `(dono,casa,parceiro,assinatura)`, por dono). O buraco era a Regra 2 — a dedup nunca cruza donos, então se o Lava rolar o histórico compartilhado e recapturar aposta antiga do Feca, ela entra sob `dono='Lava'` sem colidir → **dupla contagem** no painel do supervisor (soma Feca+Lava). **Fix — guard simétrico auto-escopado:** novo `auth.coproprietarios(usuario)` (outros donos da linhagem `OPERADORES`; `Lava→['Feca']`, `Feca→['Lava']`, solo→`[]`); `repository.upsert_bilhetes` ganha param `coproprietarios=` + **prefetch** das assinaturas já existentes sob os co-donos p/ as contas do lote (inclui arquivados) + **guard** que, se `sig` já pertence a um co-dono, **não insere e só avisa** (`id_per_row.append(None)`+`continue`, alinhamento por índice preservado); `main.py` passa `coproprietarios(dono)` **só na extração** (sync/manual/import intocados, param nasce `None`). Só dispara quando `casa+parceiro` batem EXATAMENTE entre donos (conta genuinamente compartilhada) — Betano tem código, assinatura `ID|casa|parceiro|codigo` à prova de erro. **Diagnóstico read-only na prod:** conta confirmada sob Feca (136 linhas, 96 arq); Lava ainda **não** a tinha (colisão cruzada = **0**) → **nenhuma limpeza necessária**. Bônus: já compartilhavam `mullereverton2026 [JC]` (colisão 0 lá também) — o guard passa a proteger essa conta e qualquer futura, automaticamente. AST OK + helper/assinatura testados; sem UI (check-tokens N/A). Backup em `Backups/dedup-cruzada-conta-compartilhada/`. Ver [[bet365_dedup_e_vazamento_imagens]] · [[dedup_gap_sem_codigo_reextracao]] · [[feedback_regra_duplicata]] · [[sessao44_login_multiusuario]].)_

_Anterior: 2026-07-18 (sessão 155 — **UI: 3 ajustes no rodapé da sidebar da casca (`app.html`, feedback do Feca por print).** Refino do tier de rodapé feito na sessão 153: (1) **removido o endosso** "by FDC Capital" (markup + CSS `.sb-endorse`) — "por enquanto"; (2) **rótulo do operador "Operador" → "Usuário"** (estático `#sbOpLbl` + o write em JS `vendo ? 'Vendo' : 'Usuário'`); (3) **status de sync recentralizado** — `.last-update` virou `flex-column align-items:center`: dot + "Dados sincronizados" na 1ª linha (`.sync-top` inline-flex), **data na 2ª linha** (`.sync-time`, antes empurrada à direita com `margin-left:auto` sem se alinhar a nada). `paintSync` ajustado p/ emitir a nova estrutura de 2 linhas. **Marca:** sem R$/número (§5 N/A), só tokens; `check-tokens` verde, JS inline 0 erro, **render headless conferido** (3 pedidos batem). CSS/JS inline no `app.html` (sem `?v=`; Ctrl+F5). Ver [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total.md]].)_

_Anterior: 2026-07-18 (sessão 154 — **UI: integração do pack "Tipster / Método" (Modelo B) do Feca** — `Tipster-Metodo.zip`, reimplementação da tela com 5 features, aplicada em 4 fases. **Todos os tokens do pack já existiam** no `tokens.css` do projeto → CSS drop-in (literais de azul → `var(--accent-rgb)`). **Fase A — backend `origem` (commit `PENDENTE`):** coluna `casa_config.origem` ('sharpen'=aplicada da sugestão / 'custom'=editada); `casas_visao` retorna + `salvar_casa_config`/rota aceitam; `pytest` 140 verde. **Fase B — CSS (commit `PENDENTE2`):** novo `dash/assets/css/tipster-metodo.css` (pack, classes preservadas) ligado no `dash/index.html`; base (`.panel`/`.toolbar`/`.search`/`.btn--primary`/`.inp`/`.pill-warn`) escopada sob `.tm-wrap` (só `.kpi` colidia); `check-tokens` verde. **Fase C — abas + tabela Casas (commit `PENDENTE3`):** `renderTipsterMetodo` reescrito com **tab bar** (Tipster/Método | Casas) + KPIs alternantes + panes. Aba Casas virou **tabela em grade** (`.chead`/`.crow`) com atribuição segmentada, **multi-select "Tipster dedicado"** (busca + checkboxes, cap 2, in-place) e coluna **Origem** (Sharpen/Personalizado — qualquer edição vira custom; aplicar-sugestões = sharpen). **Fase D — escada → timeline (commit `PENDENTE4`):** `tmRenderEscada` virou `.ladder` (form à esquerda + **linha do tempo horizontal**, mais novo à esquerda, selo `atual`, delta ▲/▼, remover) movida pra largura total abaixo do editor 2-colunas; valor R$ 2 casas via `fmt` (mesmo formatador do `.money`), R$ menor via `.tl-val .cur` — design do pack, honra o §5 (sem abreviação). **Verificação:** `node --check` + `check-tokens` verdes; **2 renders headless (Chrome)** conferidos — aba Casas (com dropdown aberto) e escada batem o `referencia-completa.html`. Bump `gestao.js?v=13→15`, `tipster-metodo.css?v=1`. Backup em `Backups/casas-visual-redesign-s151/`. Pack extraído em scratchpad (não commitado). **Adaptações ao framework:** multi-select limitado a 2 (o matcher casa-feudo só usa 1-2); accordion de tipster (`_tmBox`) mantido funcional dentro do pane (reskin `.acc__row` do reference = polimento futuro). **AJUSTES DE FEEDBACK do Feca (pós-deploy, commits `06f9df2`+`63c1765`):** (1) **P/L removido** da lista de tipster (só quantidade de apostas importa) + contagem e tick de inativo alinhados em colunas fixas; (2) input de data da escada virou `type="date"` (calendário nativo + digitação, `color-scheme:dark`; backend `_data_iso` já aceita ISO); (3) **KPI virava círculo** — colisão do `.kpi` do pack com o `.kpi` do `components.css` (card `min-height:120px`/coluna); renomeado pra **`.tm-kpi`** (nome próprio + `min-height:0`/`inline-flex`). **Lição:** o `white-space:nowrap` da 1ª tentativa não resolveu (altura vinha do `min-height`, não da quebra); harness de verificação precisa carregar **TODOS** os CSS reais (o meu não tinha `components.css` → não reproduziu a colisão); (4) **bolinha da timeline cortando** → `.tl-list` padding-top 14→30px + glow 4→3px. Confirmado em render headless com CSS completo. Bump `gestao.js?v=15→18`, `tipster-metodo.css?v=1→4` (últimos por sessão paralela). ⚠️ **Nota de processo:** um `git add -A` meu varreu WIP da sessão 156 (`coproprietarios`) pro commit `06f9df2` — sem estrago (140 testes verdes, sintaxe OK), mas passei a usar `git add <arquivos específicos>` com sessões concorrentes. Verificação ao vivo pendente (Ctrl+F5). Ver [[feedback_nova_ui_gate_total.md]] · [[matcher_sugerir_tipsters]].)_

_Anterior: 2026-07-18 (sessão 153 — **UI: reorganização do rodapé da sidebar da casca (`.sidebar-bottom` do `app.html`) em tiers.** Feedback do Feca (Bloco 2 já tinha movido o operador pro rodapé, mas o bloco ficou frouxo — elementos soltos, espaço morto, botões empilhados de peso igual). Rodapé reordenado em **5 tiers** do topo pra base: (1) **Operador** (`#sbOperador` — caixa clicável `--surface-2`/borda `--line`, já existente); (2) **Status de sync** (`.last-update` — dot pulsante + "Dados sincronizados" à esquerda, **timestamp `15/07 · 01:02` empurrado à direita** via `.sync-time{margin-left:auto}`, mono 10px `--ink-mute`); (3) **Ações pareadas** — "Baixar CSV" + "Atualizar" num `.sb-actions` **grid 1fr 1fr gap 6px** (antes empilhados), ambos **ghost mono** com ícone 13px, hover borda azul `rgba(var(--accent-rgb),.4)` (base visual unificada entre `.sb-csv` e `.host-refresh`); (4) **Sair** full-width discreto (`--ink-mute`), hover vermelho `rgba(var(--neg-rgb),.45)`+`--neg` (sem cara de desabilitado); (5) **Endosso** "by FDC Capital" centralizado mono 9px uppercase `.16em` `opacity .65`. Container `.sidebar-bottom` virou `flex-column` com `margin-top:auto`, `padding 14px 6px 4px`, `gap 10px` (ritmo por gap, sem margens soltas nos filhos). **JS preservado:** `paintSync`/`fmtSync` reestruturados p/ emitir `.sync-label`+`.sync-time` (timestamp à direita) e `setRefreshing` encurtado p/ "Atualizar"; handlers `#hostLogout`/`.sb-csv`/`#hostRefresh` intactos. **Marca:** sem R$/número na tela (§5 N/A), só tokens; `/nova-ui` cumprido — `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação), JS inline validado (0 erro), **render headless conferido** (5 tiers batem o spec). CSS/JS inline no `app.html` (documento de navegação, sem `?v=` a bumpar; Ctrl+F5). Backup em `Backups/sidebar-bottom-reorg-app-html/`. Ver [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total.md]].)_


> **Histórico completo das sessões 152 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
