# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-14 (sessão 142 — **Perfil de Tipster — Fatia 0 (espinha do cadastro), BACKEND.** Frente nova aprovada pelo Feca ("vc decide, eu concordo"): dar existência real ao tipster, que hoje é só texto livre em `bilhetes.tipster`. Precedida de **3 scouts read-only em paralelo** (schema/derivação, fluxo do campo tipster, UI de dinheiro) que confirmaram o terreno pronto: `parceiros` + CRUD completo p/ espelhar, `list_tipsters`/`set_tipster_bulk` já existentes, regras do `/nova-ui §5` p/ o "u" futuro. **Decisão de identidade travada:** chave **`(dono, nome)`**, unificação por nome SEMPRE (mesmo tipster em N casas = 1 registro; separar = nomes distintos "João 365"). **Entregue nesta fatia (só backend, sem UI):** (1) tabela **`tipsters (id, nome, dono, casas, mercados, obs, arquivado, criado_em)`** UNIQUE `(dono, nome)` + **backfill idempotente** dos tipsters distintos já nos bilhetes (nascem incompletos) — em `database.py SCHEMA_SQL`, roda no boot; (2) em `repository.py`: `garantir_tipster` (auto-cadastro `ON CONFLICT DO NOTHING`, best-effort), `criar_tipster`, `list_tipsters_cadastro` (com flag `completo`), `arquivar`/`reativar`/`atualizar_tipster_info`/`renomear_tipster` (propaga rename p/ `bilhetes.tipster`, espelha `renomear_parceiro`); (3) **cadastro automático** enganchado em `set_tipster_bulk` + `atualizar_bilhete` — o tipster passa a existir no instante em que o nome é digitado; (4) rotas em `main.py`: `GET/POST /tipsters/cadastro`, `PATCH /tipsters/{id}/info`, `POST /tipsters/{id}/{arquivar,reativar,renomear}` (`dono_efetivo`), sem colidir com o `GET /tipsters` do autocomplete. **Verificação:** `compileall` OK, `pytest tests/` **107 verde**, rotas registradas conferidas por import. Backup `Backups/fatia0-cadastro-tipster_2026-07-14/`. **PENDENTE (próxima fatia):** UI — página de info do tipster + sinal `(i)` de incompleto no onboarding (`inicio.html`). **Depois:** Fatia 1 = unidades no tempo + switch R$⇄u (render do "u" passa pelo `/nova-ui`). Doc-fonte `docs/PLANO_TIPSTER.md`. Ver [[perfil_tipster_plano]] · [[pl_calculo_derivado]] · [[feedback_marca_helpers_dinheiro]].)_

_Anterior: 2026-07-13 (sessão 141 — **Nome de casa de MODO CEGO mutilado no `/salvar` → conta paralela ("bets somem").** O Jonathan cadastrou **Esportiva Bet** (casa cega, sem `CASA_*.md`), extraiu 65 bilhetes ("65 novo(s)" no rail) e reclamou que "não aparecem — mostra só até dia 01". **Diagnóstico (só banco, sem pedir print):** os 65 (69 no banco, datas 30/06→13/07, todos resolvidos) **existiam**, mas em `casa='Esportivabet'` (sem espaço, `b` minúsculo) — grafia diferente da conta que ele olha (`casa='Esportiva Bet'`, 222 bilhetes importados 04/07, evento máx **01/07**). Duas contas paralelas. **Causa raiz:** round-trip de nome de casa no `/salvar` — como "Esportiva Bet" não está no mapa `_CASA_DISPLAY` (casa cega), `_display_to_key` fazia `upper.replace(" ","")` → `ESPORTIVABET` e `_casa_display` fazia `.title()` → `Esportivabet`. Atingia TODA casa cega de 2+ palavras (`Rei do Pitaco → Rei Do Pitaco`, `Faz1 Bet → Faz1Bet`). **Parte 2 (código, evita recorrência):** as duas funções viraram par inverso — fora do mapa, `_display_to_key` devolve o nome **verbatim** (só `.strip()`) e `_casa_display` devolve a chave **sem `.title()`** → round-trip IDENTIDADE; mapeadas seguem canonizando. **3 testes de regressão** em `tests/test_modo_cego.py` (verbatim / canonicaliza / idempotente); `conftest` ganhou stub `init_db` p/ importar `main`. Suíte **107 verde**. **Parte 1 (dado):** os 69 renomeados `Esportivabet → Esportiva Bet` **recalculando a `assinatura`** (embute a casa → senão re-extração futura viraria fantasma), 0 colisão (índice `dono,casa,parceiro,assinatura`; 222 antigos sem código); parceiro duplicado id 325 removido. Conta unificada **`Esportiva Bet · Pessoal` = 291 bilhetes**, dias 11/12/13-07 presentes. Backup `Backups/sessao141-casa-nome-modo-cego/` (main.py + JSON dos 69, gitignored). Ver [[extracao_worldwide_fase012]] · [[favicons_tres_mapas]] · [[dedup_gap_sem_codigo_reextracao]].)_

_Anterior: 2026-07-13 (sessão 140 — **Destaques Bookies/Tipsters da tela Início viram LEADERBOARD (PACK "Destaques Leaderboard") + auditoria /nova-ui.** Pedido do Feca: auditar regras de UI da tela Início ("fontes e coisas fora do padrão") e executar o PACK `Downloads/PACK - Destaques Leaderboard (Claude Code).md`. **Auditoria (`/nova-ui`):** `check-tokens` já verde e `fmtPL`/`fmtR` verbatim de `app.js`, cor só no `.money-val`, zero neutro (KPI usa `fmtR(0)` sem apostas) — tudo OK. Desvios reais: (1) os blocos **Bookies/Tipsters eram tabela `.rk` com grade dupla** (visual "Excel com bordas", `.rk-h` a 8.5px abaixo do piso 9–11px do `UI_REFERENCE §2`) → resolvido pelo PACK; (2) `.money-sign` a **0.76em** vs canônico **.78em** (index.html:1092) → corrigido. **Arquivo único** `app/static/inicio.html`, **Etapa 1 (CSS)** trocou `.dcols/.dcol/.rk-*` por **leaderboard** (`.dcols` 2 colunas com respiro, `.lb-h` 9px on-spec, `.lb-row/.lb-track/.lb-fill` barra de magnitude, `.casa-chip` favicon 24×24 raio7 steel, `.tip-chip` avatar redondo neutro); **Etapa 2 (JS)** removeu `rkTable`, reescreveu `destaques(map,noun,kind)` + `lbCol`/`casaFavicon`/`tipAvatar` (barra ∝ maior |P/L| da coluna, piso 3%). Casa = favicon Google S2 (`sz=128` p/ casar com `CASA_ICONS`, fallback inicial via `onerror`); tipster = avatar neutro (pessoa, sem cor). **`CASA_DOMAIN` copiado COMPLETO do `HOUSE_DOMAIN` canônico** (`dash/assets/js/data.js`) com ⚠️ comentário-ponteiro — não carreguei `data.js` (colide com `esc/SPORT_*/MESES` inline). Barra usa `rgba(var(--pos-rgb/--neg-rgb),.55)` (triplets existem em `tokens.css`). **Validação:** `check-tokens` **verde** (drift/paleta/shell/monetário); JS inline sem erro (`vm.Script`); zero resíduo das classes/funções antigas. Backup `Backups/inicio-leaderboard-destaques/`. **Ressalva:** `CASA_DOMAIN` é cópia — ao criar/renomear casa em `data.js`, replicar aqui. **Revisão ao vivo do Feca → 3 correções (commits `59c313a`, `47b09ec`):** (1) **favicons vinham COLORIDOS** — o `.casa-chip img` do PACK saiu sem filtro; apliquei o canônico do app (`grayscale(1) contrast(0.2) brightness(1.35)` + overrides de geometria Novibet/Esportiva/PixBet scale 1.3, BetMGM/BETesporte scale 1.5 via `data-casa`) — a marca **nunca** usa favicon colorido (`UI_REFERENCE §4`); (2) **avatar de letra do tipster removido** — não existe esse padrão no app (inicial só é fallback de casa); tipster = rank+nome+P/L+barra; (3) **`.lrow .t` fixado em Manrope 500 explícito** (herança sem peso parecia fonte errada só na pendência; casa o peso dos nomes do leaderboard `.lb-nm`). Vermelho do P/L/rótulo/barra **é permitido** (§1, semântica de resultado); o único fora-de-regra era o logo colorido → resolvido pelo grayscale. **(4) SELF-HOST das fontes (commit `0a696c6`):** o Feca ainda via fonte fora do padrão; auditoria confirmou que o CSS só usa as 2 fontes da marca (Manrope/JetBrains Mono), mas ambas vinham do `<link>` do **Google Fonts** → se o download falha, cai no fallback **Segoe UI** (parece off-brand). Decisão do Feca (`AskUserQuestion`): **self-host**. Baixei os `.woff2` oficiais (subsets **latin + latin-ext** = pt-BR, incluindo **U+2212** do `fmtPL`); ambas são **VARIÁVEIS** (md5 idêntico entre pesos) → **4 arquivos** em `app/static/fonts/` + 4 `@font-face` (faixa 400–800) em `app/static/fonts.css`. `inicio.html` troca o `<link>` do Google por `/static/fonts.css`. CSP já cobre (`font-src 'self'`). **Render headless (Chrome)** confirmou Manrope/JBM distintas do fallback serif, pesos e acentos OK. **Propagação CONCLUÍDA (commit `a866257`):** o self-host foi estendido ao app inteiro — `app.html` (casca), `index.html` (app), `login.html` e `dash/index.html` (dashboard) trocaram o `<link>` do Google Fonts por `/static/fonts.css`; nenhuma referência a `googleapis`/`gstatic` sobrou. **CSP apertada:** `style-src` e `font-src` viraram `'self'` (removido Google); `img-src https:` mantido (favicons das casas via S2). **(5) FAVICONS — Vitória Bet + reconciliação (commit `c028e6b`):** o Feca viu o favicon da Vitória Bet como globo na tela Início. Auditoria (script S2, 48 domínios): **TODOS resolvem p/ favicon real, 0 quebrados** → o problema era **drift entre 3 mapas** de domínio (`index.html DOMINIOS` = vivo/completo; `data.js HOUSE_DOMAIN`/`CASA_ICONS` = defasado; a cópia `CASA_DOMAIN` do `inicio.html` = incompleta). Corrigido: (a) `inicio.html CASA_DOMAIN` agora **espelha o `DOMINIOS` do index verbatim** (cross-check = cobertura 100%, 0 divergência) + fallback tira acento; (b) `data.js` (que o dashboard usa via `casaDomain()`) ganha as **4 casas só-do-Planilhador** (Vitória Bet, KingPanda, Lottu, Jogo de Ouro) e `Rei do Pitaco → pitaco.bet.br`. Os 3 mapas agora concordam. **Lição:** o mapa de favicon vive em 3 lugares — ao adicionar casa, atualizar os 3 (`index.html DOMINIOS`, `data.js HOUSE_DOMAIN`+`CASA_ICONS`, `inicio.html CASA_DOMAIN`). Ver [[railv2_raiox]] · [[feedback_marca_helpers_dinheiro]] · [[fontes_self_host]] · [[favicons_tres_mapas]].)_

_Anterior: 2026-07-13 (sessão 139 — **Sidebar do menu: presença visual (PACK "Menu Sidebar").** Aplicado o PACK `Downloads/PACK - Menu Sidebar (Claude Code).md` — só aparência da navegação, sem mexer em estrutura/ícones/rotas/ordem. **Arquivo único** `app/static/shell.css` (Fatia 1 = casca compartilhada Planilhador + Dashboard, `.nav-group/.nav-item/.nav-icon`). Três defeitos → três correções: (1) linha ativa full-bleed + tab 2px → **pílula inset arredondada** (`margin:1px 10px`, `border-radius:var(--r-sm)`) com **fundo degradê azul** (`linear-gradient` sobre `--accent-rgb` alpha .24→.10), hairline interna (`box-shadow inset ... rgba(--accent-rgb,.35)`), **aba curta arredondada** à esquerda (`::before` 3×18px `var(--accent)`) e texto branco; (2) ícones de `--ink-mute` (cinza morto) → **`--ink-soft` em repouso** (vivos), `--accent-2` no ativo; (3) grupos que somem → **hairline** (`::after` `var(--line-2)`) após o rótulo mono. As travas de `font-size` do SHELL_SPEC seguem intactas (`--text-nano` no grupo, `--text-sm` no item → shell 5/5). Literais `#fff`/`rgba(255,255,255,.045)` **não** estão na lista de cores banidas do `check-tokens` (só WARN informativo); tokens `--line-2`/`--r-sm`/`--accent-2` confirmados em `tokens.css`. `/nova-ui` + `check-tokens` **verde** (drift/paleta/shell/monetário). Backup `Backups/shell-css-sidebar-pilula/`. Commit `3d66abd`. **PENDENTE:** revisão AO VIVO do Feca (item ativo como pílula/aba, legibilidade em `data-theme="light"`) — vale nos DOIS apps. Ver [[programa_governanca_marca]] · [[feedback_marca_helpers_dinheiro]].)_

_Anterior: 2026-07-13 (sessão 138 — **Betfair por CAPTURA JSON (SharpenUp `bf_inject`) — Etapa 1/2.** O Feca notou que apostas Betfair vinham datadas na **colocação**, não na resolução. **Diagnóstico (só leitura, banco vs extrato `AccountStatement_(18).csv`):** os **ganhos/voids já estavam corretos** (125/125 batiam a `settledDate` do extrato); o problema eram só as **PERDAS**, que **não geram linha no extrato** (perda não devolve dinheiro) → eram datadas por **interpolação** (aproximação, herdando data ~colocação da era antiga). Teto **estrutural** do fluxo texto+extrato. **Achado que muda o jogo:** a página de bilhetes resolvidos da Betfair chama `POST myactivity.betfair.bet.br/activity/sportsbook` e a resposta JSON traz **`settledDate` de TODO bilhete — perda inclusive** (+ `betId` O/…, `status` WON/LOST/VOID limpo, odd/stake/bônus/cashout exatos, `marketType`). O `settledDate` bate ao segundo com o `Bet Settled` do CSV → continuidade perfeita. **Decisão do Feca (`AskUserQuestion`): espelhar Betano (via IA)** — captura → texto formatado → IA lê (não parser determinístico). **Etapa 1 ENTREGUE e no ar (commit `e4233df`):** extensão `bf_inject.js` (novo, espelha `bn_inject`: engancha fetch/XHR em `/activity/sportsbook`, acumula por `betId`, fim autoritativo `moreAvailable:false`); `content.js` (listener `__sharpenupBFData` + `formatTicketBF` com `Data=settledDate` via `_dbrBF` DD-mmm-YY local + `roboBetfairPassive` + dispatch `casa==='betfair'`, SEM fallback de scrape); `popup.js` injeta `bf_inject`; `manifest` 0.2.9→0.3.0. Backend: `captura.py` marca `BETFAIR:'texto'` (modo robô); `main.py` roteia **por conteúdo** — bloco com `[Código: O/…]` fatia/pré-dedupa como Superbet, **legado texto+CSV intacto** (sem `[Código:]` → `_split_betfair_bilhetes`). Doc `CASA_BETFAIR.md` §2/§4/§5: captura JSON = via principal, texto+extrato = legado. +2 testes de roteamento (suíte `tests/` **101 verde**; JS/JSON/py sintaxe OK; `check-tokens` verde no hook). Marcador `[Código: O/…]` casa 100% no `_SUPERBET_SPLIT_RE`/`_SUPERBET_ID_RE`. Backup `Backups/betfair-captura-json-sessao138/` (gitignored). **Freio de captura (commit `47c6b0e`, no teste ao vivo o Feca viu o robô rolar ~1 ano — a Betfair NÃO corta o histórico como a Betano):** como a lista é por **postagem** (resolução fora de ordem → "parar no já-salvo" fura), o freio previsível é **QUANTIDADE**. Popup ganha, só na Betfair: **Quantidade** (padrão **100**, editável) + **Dias** (opcional) + checkbox **Varrer conta inteira**; robô para no 1º limite (`ctx.qtdMax`/`ctx.bfCutoff` em `roboBetfairPassive`, reusa o padrão de teto da Bet365). Recapturas baratas (pré-dedup pula já-salvos antes da IA). **Ressalva:** aposta de futuro (colocada há meses, resolvida agora) fica no fundo da lista por postagem → limite de qtd/dias não pega; remédio = "varrer tudo" periódico. **Dois fixes de integridade do pareamento (commit `4608188`, valem p/ todas as casas, achados no teste ao vivo):** **(1) status de conexão falso** — o popup mostrava "online" só por existir token salvo, mas a sessão vive em memória no servidor (some no restart do Railway / TTL 6h) → token órfão. Novo `POST /captura/validar`; popup valida o token ao abrir (só afirma Conectado se a sessão existe; 401 → limpa token e volta a parear; rede fora → offline, mantém token). **(2) amarração casa↔site** — conectar código de Betfair e capturar na Superbet gravava no slot errado sem aviso. Cliente: popup bloqueia se o domínio da aba ≠ casa conectada (`CASA_HOSTS`). Servidor (backstop): extensão manda `origem` (host) no `/captura/enviar`; `captura.casa_de_host` mapeia host→casa e rejeita **409** se for de outra casa conhecida ≠ a da sessão (print desconhecido passa). +3 testes (`tests/test_captura.py`, 104 verde). **Saga de debug da captura → RESOLVIDA (extensão v0.3.3, commits `383a1e2`→`1cc3e2f`):** o "0 bilhetes" tinha 3 causas — (a) o `open` recebe a URL **relativa** e o regex `/activity/sportsbook` não batia → passei a casar pela **FORMA do JSON** (`bets[]`, URL frouxa `sportsbook`); (b) a aba **Aberta** também chama o endpoint com `moreAvailable:false` → zerava a paginação e misturava aberto/resolvido → filtro `responseFilters.status===SETTLED`; (c) o **scroll da Betfair não dispara a próxima página** (lista curta não rola) → o `bf_inject` passou a **PAGINAR SOZINHO** (captura a requisição SETTLED e re-emite avançando `nextPageIndex`, `credentials:include`, até o teto do robô ou `moreAvailable:false`; guardas anti-loop: para se não vem `betId` novo, se o índice não avança, ou em 400 replays). Também: `/captura/validar` estava fora de `_CAPTURA_ISENTAS` → tomava 403 → "offline" falso; isentado (commit `7541f15`). Autodiagnóstico na tela quando dá 0 (hook/respostas/bilhetes). **PENDENTE:** (1) Feca **confirmar a captura ponta-a-ponta** ("acho q foi" — contador subindo sozinho até 100, bilhetes no dashboard com data certa **inclusive perdas**); se travar na 1ª página, mandar a linha `requisição capturada p/ replay · body:` do console (mostra o nome do campo de página). (2) **Etapa 2 — backfill retroativo**: puxar histórico (Varrer conta inteira) e re-datar as **perdas já salvas** pela `settledDate` real, substituindo a interpolação (JSON cobre 90 dias = toda a base Betfair do Feca jun–jul). Ver [[betfair_captura_json]] · [[extensor_captura]] · [[data_fuso_local_nunca_utc]].)_

> **Histórico completo das sessões 132 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
