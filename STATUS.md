# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-19 (sessão 160 — **modo turbo/CEO: +6 correções da Auditoria Turbo no ar** (uma por commit, backup + testes/gate verdes em cada; suíte segue 172 + 3 skipped do harness de DB). **(1) #14c** faxina CSS — removidos 3 blocos de componente MORTOS (uso-zero provado por grep em `app/static/dash`): `.seg-btn` "canônica" nunca adotada, família `.badge/.badge-*` de status, `.apostas-sort-*` órfãos; `check-tokens` verde, bump `components.css?v=12` — `ee8ba22`. **(2) #13** autodiagnóstico universal nas casas-robô passivas (**maior risco vivo**): antes só a Betfair diagnosticava captura zerada; Superbet/BETesporte/Betano caíam num "Nada coletado" genérico → quando a casa troca o DOM/endpoint a captura zerava em SILÊNCIO. Cada inject (`sb/be/bn_inject.js`) passou a contar `respostas` e emitir SEMPRE `hook:true`+`respostas` (heartbeat, mesmo com 0 bilhetes); `content.js` lê isso das 3 casas e mostra um **toast diferencial** (`hook NÃO carregou` / `endpoint mudou` = 0 respostas / `formato mudou-ou-conta-vazia` = respostas>0 & 0 vistos) + escala ao popup (`lastError`) só na falha inequívoca; `bn` preserva `fimOpen`/`fimSettled`+`__aberta`. Manifest 0.3.4→**0.3.5** (**Feca precisa RECARREGAR a extensão** no Octium). Backup `Backups/autodiagnostico-extensao-13-2026-07-19/` — `5b548ea`. **(3) #11** harness de camada-DB REAL: 1º teste do caminho de ESCRITA de dinheiro que o conftest stuba — `tests/test_repository_db.py` exerce `upsert_bilhetes` (insert vs update por código), isolamento por `dono` (tenancy) e as 2 blindagens aberta→resolvida, contra um Postgres de teste. `conftest.py` virou CONDICIONAL: com `TEST_DATABASE_URL` (só no CI, `postgres:16` em localhost) pula os stubs e carrega asyncpg/database reais; sem a var (dev local, ambiente do Feca) stuba como antes → os 3 pulam. **Gateado em `TEST_DATABASE_URL` (nunca `DATABASE_URL`) + trava anti-prod (recusa URL não-localhost)** — o `.env` do Feca tem o `DATABASE_URL` de prod, jamais tocado. CI ganhou serviço Postgres + step isolado (`e7a8188` + `1e66d20`). Local: 172 passed, 3 skipped; **os 3 de DB estreiam no CI** (a conferir — `gh` não instalado local). **(4) #20** fecha 3 lacunas de propagação nos masters (**aprovado**): Primeiro/Último Marcador entram como sinônimos de `Anytime` em `MASTER_APOSTAS §4`; `aposta aberta → Resultado vazio` documentada em `MASTER_OUTPUT §13.1`+`§18.8` (+ espelho no `CLAUDE.md`); `Múltiplos` entra na whitelist oficial de `MASTER_ESPORTES §7`. Nenhuma cria/renomeia categoria → não dispara checklist de casas, `audit_casas` verde — `40deee0`. **(5) #15/#16** índice **Solidez** (**aprovado**): gate de rentabilidade (yield<0 trava em "Muito Baixa" — 40% do índice era agnóstico a lucro e perdedor floreava) + separa força-do-sinal (Edge cheio exige yield ≥3%, não só significância — amostra grande tornava edge trivial "significativo") de tamanho-de-amostra; `calcSolidez` ganha param `roi` (%), os 3 callers (gestao/overview/performance) passam `calcROI(rows)`, disclaimer novo no card, bump 4 `?v=` — `1923052`. **Decisões do Feca:** #20 aplicar · #15/#16 corrigir os dois · **#5 Poly odd → junto com a Poly incremental**. **Adiado/aberto:** #14 domain.py (risco alto/ganho marginal — puras já testadas, #11 destravou sem o split); #18 backtest temporal (metodologia da frente de tipster); **#19 separador bet builder** (achado: ` & ` = mesmo-jogo em Jogo de Ouro/Lottu vs ` // ` = jogos diferentes → recomendação: codificar ` & ` no §16; aguarda OK); #21 golden bilhetes; #25 Backups retenção; **Poly incremental + #5** (precisa a carteira do Feca — probe do filtro conditionId, fixtures e paridade ao vivo; não subir sem paridade). Ver [[custo_tipster_incidente_jonathan]] (Jonathan amanhã) · `docs/AUDITORIA_TURBO_2026-07-19.md` (tracker atualizado).)_

_Anterior: 2026-07-19 (sessão 159 — **SharpenUp/Betano: robô passou a LER as apostas EM ABERTO** (antes só liquidadas). **Causa raiz:** `bn_inject.js` filtrava `settled=true` e descartava a aba "Em aberto"; como o robô re-processa a memória acumulada, trocar de aba só re-enviava as liquidadas. **Fix em 4 arquivos (backup `Backups/pre_betano_abertas_2026-07-19/`):** (1) `extensor/bn_inject.js` — captura as DUAS listas (settled=true→liquidada · senão→aberta), marca cada bilhete `__aberta` e sinaliza fim POR LISTA (`fimOpen`/`fimSettled`). (2) `extensor/content.js` — acumulador virou `bnById` (1 por BetId, **liquidada vence aberta**); `formatTicketBN` ganhou ramo ABERTA (Status "em aberto — NÃO liquidar; sem resultado", odd estrutural, `Return`=potencial); `roboBetanoPassive` itera `bnById`, usa o fim da **aba ativa** (`/open` na URL) e **não corta pela janela de dias na aba abertas**. Envia abertas+liquidadas carregadas numa rodada (UPSERT por código nunca duplica). (3) `app/repository.py` — UPSERT blindado: **(a)** resultado VAZIO nunca sobrescreve resolvido (uma re-leitura tardia de "aberta" não rebaixa a linha já fechada); **(b)** só quando a linha ESTAVA `'aberta'` e agora resolve os campos financeiros (odd/data/stake) são refrescados com a verdade da liquidação (vitória com boost passa a odd=Retorno÷Stake) — linha já resolvida fica intacta; assinatura por código não usa esses campos → match não quebra. Mesma lógica no fallback de `UniqueViolationError`. **(4)** `app/static/index.html` — `exportar()` ordena **abertas (sem resultado) acima das resolvidas** (sort estável). Fluxo confirmado: aberta sobe sem resultado → `estado_extracao`→`'aberta'` (não rejeitada em `validar_linhas`, `main.py:1513`) → bilhete fecha → mesmo BetId=mesma assinatura → UPSERT preenche resultado + refresca odd. `py_compile` + `node --check` verdes. Manifest 0.3.3→0.3.4 (**Feca precisa recarregar a extensão** no Octium). Verificação AO VIVO na Betano pendente (rodar nas duas abas). Ver [[extensor_captura]] · [[betano_lentidao_chunker]] · [[extracao_sem_odd_flag]] · [[dedup_gap_sem_codigo_reextracao]] · [[ordem_feed_hora_envio]].)_

_Anterior: 2026-07-19 (sessão 158 — **Onda 1 da Auditoria Turbo: 4 correções aplicadas e no ar** (uma por commit, backup em `Backups/onda1-turbo-2026-07-19/`, 140 testes + check-tokens verdes em cada). (1) `database.py` — CREATE parceiros movido para ANTES dos `UPDATE parceiros` (rodavam antes da tabela existir → rollback do SCHEMA_SQL inteiro em banco vazio: DR/novo cliente/dev local nunca inicializavam) — commit `201b223`. (2) `main.py` — `/polymarket/sync` passou de `Depends(dono_efetivo)` p/ `usuario_atual` (era a única rota de CRIAÇÃO gravando na base do operador visualizado em modo "ver como"; alinha a /extrair, /salvar, /bilhetes/manual — regra da sessão 82) — `eee55c1`. (3) `dashboard` — P/L **zero neutro** no `fmtPL` (§5.1: pintava zero de verde com "+"; toda Void/cashout=stake) + espelhos de texto `_txtPL` (temporal) e tooltip mensal (overview); bump app.js 20→21, overview 7→8, temporal 3→4 — `31166ad`. (4) `dashboard` — tooltip do gráfico de Esportes vazava HTML cru (`fmtPL`→`_txtPL` no canvas; os 24 `fmtPL` restantes são render de innerHTML, corretos) + `.dot.hw/.hl` deixaram de ser **âmbar idêntico** → verde/vermelho apagados `rgba(var(--pos-rgb/--neg-rgb),.5)` (distintos entre si e do W/L cheio, sem `!important`); bump performance 9→10, components 10→11 — `d2f23ba`. **PENDENTE (amanhã, COM o Jonathan):** itens #1/#2 do custo por tipster — o incidente do Jonathan (localStorage não sincroniza entre PCs) reorientou a correção para **migração ao Postgres com recuperação MANUAL disparada do PC do trabalho** (não auto-migrar; ver memória `custo_tipster_incidente_jonathan`). Relatório completo em `docs/AUDITORIA_TURBO_2026-07-19.md` + `docs/auditoria_turbo/`. **Onda 2 (trio de segurança) TAMBÉM feita e no ar** (backup em `Backups/onda2-turbo-2026-07-19/`): (5) `main.py` — rate-limit `_client_ip` passou a usar o ÚLTIMO `X-Forwarded-For` (o IP que o proxy Railway viu) em vez do leftmost forjável — `afad142`. (6) `.dockerignore` criado — contexto de build sem `Backups/` (~55MB)/`.git`/docs/tests; NÃO exclui `app/ global/ casas/` (masters ficam) — `947cef7`. (7) `auth.py` — **SESSION_SECRET fail-closed em produção**: em Railway (detectado por `RAILWAY_ENVIRONMENT`/`RAILWAY_PROJECT_ID`) a ausência levanta `RuntimeError` no boot em vez de gerar segredo efêmero que derrubava logins a cada restart; dev mantém fallback + aviso; **Feca setou o SESSION_SECRET no Railway antes do deploy** (ordem obrigatória p/ não derrubar prod) — `06be977`. Guard testado nos 3 cenários (dev/prod-sem/prod-com). **Onda 2 (testes) — #10 `test_auth.py` FEITO** (`0bf12f2`): 27 testes cobrindo token HMAC (round-trip/adulteração/outro-segredo/expiração/usuário-fantasma), matriz `pode_ver_como`, `dono_efetivo` (cookie ver-como forjado/não-autorizado cai no real), `coproprietarios`, `verifica_hash` e o guard SESSION_SECRET fail-closed (regressão via subprocess); suíte 140→167. **Resta da Onda 2:** #11 harness de camada-DB (exercer `upsert_bilhetes` + queries por dono; esforço grande). **Onda 3 #12** índices em `bilhetes` `(dono,criado_em,id)` + parcial `(dono,codigo_bilhete)` — feed deixa de ser seq scan+sort (`8e6e7c4`, sintaxe validada offline). **Onda 4 #17** win rate do backend (`_resumir_apostas`) passou a espelhar o `wrFrac` do front (HW=½, HL=½, Void fora) — mesma conta nas 2 telas; +2 testes, suíte 167→169 (`0941bf7`). **Onda 6 faxina** (via agente, revisado antes do commit): `PLANO_MULTIUSUARIO/UNIFICACAO_2026.md` movidos raiz→`docs/` (refs corrigidas em Ideias/README + ONDE_ESTOU; git preservou histórico), link quebrado do HISTORICO corrigido, `NOTA_AO_AUDIT.md` removida (`0d528a0`). **Abertos:** #11 harness DB, #13/#14/#14b (Onda 3), solidez #15/#16 e backtest #18 (Onda 4), Onda 5 (dados). **Frente Polymarket (a pedido do Feca):** teto de sanidade na paginação `_paginate` (anti loop-infinito de proxy preso; aborta >200k itens, +2 testes → suíte 171) `771aea3`; **auto-sync ao entrar/voltar na Poly** com throttle de 5 min (marca d'água `poly-last-sync::<wallet>` gravada em todo sync; pausa se aba oculta; gatilhos: entrar na conta + `visibilitychange` + piggyback no poll de 60s) `efbd55f`. **PENDENTE Poly (fatia dedicada, mexe na orquestração do dinheiro → exige test harness de cliente-fake + paridade ao vivo):** **FEITO** — fetch consolidado `coletar_tudo` (1× em vez de 2×, ~2× mais rápido, saída provada idêntica por teste de paridade offline) `c749056`. **RESTA:** `_portfolio`→`None`/"—" (achado #47 irmão, backend+front), e o **sync incremental por marca d'água** (não re-escanear o resolvido imutável — depende do que a API `/positions`+`/activity` permite: ordem/cursor; precisa sanity-check do Feca na carteira real; desenho pronto em `docs/PLANO_POLY_INCREMENTAL.md` após sondagem real da API). Backup Poly em `Backups/onda-poly-2026-07-19/`. Verificação visual ao vivo (Ctrl+F5) pendente.)_

_Anterior: 2026-07-18 (sessão 157 — **UI: "Baixar CSV" de-triplicado → toolbar da aba Apostas (passo 1 de 2 do rodapé da casca).** Decisão do Feca: o export pertence à **aba Apostas** e o comportamento **fica dump cru de backup** (confirmado via `AskUserQuestion`) — backend `/exportar.csv` (`main.py:1710`) **intocado** (todas as linhas/colunas do dono, `;`+BOM). O mesmo `<a href="/exportar.csv">` estava **triplicado**; consolidado em 1: **removido** dos 3 rodapés — `.sb-actions` da casca (`app.html`), sidebar do dashboard (`dash/assets/js/app.js`) e rodapé da Extração (`index.html`) — e **adicionado** na toolbar da aba Apostas (bloco de "Busca rápida por coluna", ao lado do "✕ Limpar"), rótulo **"Baixar base (CSV)"**, estilo ghost mono casando com o Limpar (tokens `--line`/`--ink-mute`, hover borda `--accent`; sem cor nova). Limpeza: `.sb-actions` da casca virou grid **1 coluna** (só resta "Atualizar") + regras `.sb-csv` órfãs removidas de `app.html`, `index.html`, `dash/.../layout.css`. **Marca:** botão sem R$/número (§5 N/A); `/nova-ui` cumprido — `check-tokens` verde (5/5 shell, sem cor banida, sem abreviação), `node --check` do `app.js` OK, zero `sb-csv` restante. Bump `dash/index.html`: `layout.css?v=6→7`, `app.js?v=19→20`. Backup em `Backups/csv-para-aba-apostas/`. Verificação visual ao vivo pendente (Ctrl+F5). **Passo 2 pendente:** gatear o botão "Atualizar" (`#hostRefresh`) por `planilha_ao_vivo(dono)` (expor flag no `/me`; esconder pra base Postgres). Ver [[rodape_sidebar_botoes_decisao]] · [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total.md]].)_

> **Histórico completo das sessões 156 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
