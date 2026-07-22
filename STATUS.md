# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-22 (sessão 176 — **Bet365 reaberta no SharpenUp: o que travava era o gate do front.** **Sintoma (Feca):** "o SharpenUp ainda não tá disponível nas 365". **Diagnóstico:** não era a extensão nem o backend. A extensão publicada já trazia a captura passiva da Bet365 (`b3_inject`, commit `d919d92`) e o `captura.py` já listava `BET365: "texto"` no `_MODO_POR_CASA` + os hosts no `_HOSTS_POR_CASA`. O que barrava era o **gate do front**: o Set `CASAS_CONECTAVEIS` (`app/static/index.html`), fechado na época em que o robô de DOM da Bet365 não segurava, **nunca foi reaberto** quando a captura virou passiva — o `d919d92` mexeu só em `extensor/` e `casas/`. Efeito: em conta Bet365 o botão **Conectar** ficava `disabled`+`is-off` com o tooltip "O SharpenUp ainda não cobre esta casa", e a dica "SharpenUp disponível nesta casa" do RAIO-X não aparecia. **Fix (3 arquivos, cirúrgico):** (1) `+ 'BET365'` no `CASAS_CONECTAVEIS` e comentário trocado (documenta a volta e o porquê: passiva via `/sportshistoryapi`, robô de DOM só como fallback); (2) `manifest.json` — o `b3_inject` casava só `*.bet365.bet.br`, mas o `_HOSTS_POR_CASA` do backend e o `CASA_HOSTS` do popup aceitam **também `bet365.com`** → sem o match o inject não carrega no `.com` e a captura cairia no fallback DOM sem dizer por quê; adicionados `*://*.bet365.com/*` e `*://bet365.com/*`. Versão **0.6.0 → 0.6.1** (bumpar o manifest é o gesto que faz o backend detectar instalações antigas; o `.zip` do `/extensao/download` é gerado on-the-fly do `extensor/` no deploy, sem build manual). (3) comentário obsoleto no `content.js` ("casas sem inject (bet365/genéricos)") — a Bet365 já tem inject e já está no autodiagnóstico diferencial. **Prod conferida antes do fix:** `www.sharpen.bet/extensao/versao` → `0.6.0`, ou seja, a extensão com a Bet365 já estava publicada; só a UI escondia. (`sharpen.bet` sem `www` dá 404 — a raiz é 301 do GoDaddy, comportamento conhecido.) **Gate `/nova-ui` cumprido:** nenhum número, dinheiro, cor ou token tocado (a mudança é um Set de strings + comentários + `matches`); `check-tokens` **verde** (drift/paleta/shell/monetário); `vm.Script` nos 3 scripts inline do `index.html` OK; `node --check` em `content.js` e `b3_inject.js` + `JSON.parse` do manifest OK. Backup `Backups/bet365-gate-front-2026-07-22/` (só os arquivos editados). **Pendente — o mesmo de antes, agora destravado:** **teste ao vivo na Bet365 logada** (a incógnita é se o token rotativo `x-net-sync-term` aceita o replay; se recusar, cai no fallback DOM). Seguem abertos: payload cru do cashout "quebrado", `CL=15`/`151`, ajuste dos offsets de encerramento. **Ação do Feca:** reinstalar a extensão (Extração › Conectar SharpenUp › Atualizar) para a 0.6.1 pegar o novo `matches`. Ver [[bet365_captura_api]] · [[extensor_captura]] · [[feedback_nova_ui_gate_total]].)_

_Anterior: 2026-07-22 (sessão 175 — **O ↻ "Atualizar" passou a valer na tela de Início (e a furar o cache da planilha viva).** **Sintoma (Fatuch):** o painel "Apostas em Aberto" mostrava 2 apostas de tênis já liquidadas (Zhou vs Geerts @1,50 e Seggerman / Herbert @1,80, TCINSIDER) e **nenhuma** das 20 do dia que o "TODAY BETS" da planilha dele listava (TCINSIDER 1 · PEIXE 1 · ARRUDEX 18, R$ 6.134). **Diagnóstico (feed puxado ao vivo, não deduzido):** o `/exec` do Apps Script dele respondeu `ok=true count=5485 builtAt=18:45:41Z` com **21 abertas** — as 18 ARRUDEX, a PEIXE e a TCINSIDER "Faria / Rocha", batendo linha a linha com o TODAY BETS; as duas do print **não estavam mais lá** (liquidadas na planilha, saíram sozinhas). Ou seja: **os dois sintomas são o mesmo, e nenhum é bug de lógica** — o painel do início une feed + Postgres corretamente desde a s168. O que ele viu foi um retrato velho. **Causa raiz:** a carteira de planilha AO VIVO tem DOIS caches empilhados — Apps Script grava o JSON no Drive a cada **30 min** (gatilho) e `planilha_viva.py` guarda **120 s** em memória → defasagem de até ~32 min entre planilha e tela. Trigger conferido saudável (cache de 15 min na hora da checagem), então o atraso é o projetado, não uma pane. **Agravante corrigido:** o único caminho que fura os dois caches é `?refresh=1` (`dashboard_data(refresh)` → `dashboard_rows_ao_vivo(refresh=True)`), disparado pelo ↻ da casca — mas o handler só falava com o iframe do Dashboard e **saía em silêncio se ele não tivesse aberto**. Quem estava na tela de Início clicava e não acontecia nada — justo onde mora o painel que mais envelhece. **Fix (escolha do Feca: só os botões, gatilho de 30 min intocado):** (a) `inicio.html` — `boot(force)` passa `?refresh=1` ao feed (só ele; `/bilhetes`, `/parceiros` e `/incompletos` são Postgres, sempre frescos), expõe `window.loadData(force)` no **mesmo contrato do dash** e publica `window._dataBuiltMs` a partir do `builtAt`; (b) `app.html` — `refreshTarget()` escolhe o app **visível** que sabe recarregar (Início ou Dashboard; na Extração cai no Dashboard carregado ou no Início, pra o botão nunca ficar morto) e `paintSync` lê o `builtAt` desse alvo, não mais só do dash. Reexecutar `boot` é seguro: todo render substitui `innerHTML` (listeners junto). **Validação:** `check-tokens` verde (drift/paleta/shell/monetário) e `vm.Script` OK nos scripts inline dos 2 arquivos. Nenhum dado, cor, dinheiro ou formatador tocado — só wiring do botão. Backup `Backups/s175-botao-atualizar-inicio/` (só os 2 arquivos editados). **Pendente:** teste do clique em prod pelo Feca/Fatuch (não validei em navegador); a defasagem de base (gatilho de 30 min + TTL de 120 s) **continua de pé** por decisão — as opções recusadas foram baixar o gatilho p/ 5-10 min e carimbar "dados de HH:MM" no painel. **Adendo da mesma sessão — o ↻ virou cascata, "apertou, atualizou TUDO" (2º commit):** a 1ª entrega deixava dois buracos que o Feca cobrou na hora ("apertou atualizou TUDO?"): (i) o iframe **carregado mas escondido** ficava com dado velho até você clicar já dentro dele; (ii) a **Extração** cacheia o feed (`index.html` `painelDashRows`/`_painelDashPromise`, painel de atividade das contas) pela **sessão inteira**, sem nenhuma invalidação — só F5 renovava. Agora `refreshQueue()` monta a fila com o app **visível na frente** e os demais carregados atrás, e **só o 1º leva `force=true`**: ele reconstrói a planilha no Apps Script E preenche o cache de 120 s do backend; os seguintes vêm sem force e caem nesse cache recém-cheio — mesmo dado fresco sem pagar de novo os ~10-20 s da reconstrução. **A ordem não é cosmética:** invertida, os demais serviriam cache velho e o clique pareceria ter funcionado. `index.html` ganhou `window.loadData(force)` no mesmo contrato dos outros dois, que **invalida sempre** (com ou sem force — cache de sessão não tem TTL, preservá-lo devolveria o mesmo dado velho; o `force` só decide o `?refresh=1`) e re-renderiza o painel se ele estiver na tela. Erro de um app não derruba os outros (cada `loadData` embrulhado em `catch`). **Verificação real, não só sintática:** harness em `vm` roda o script **de produção** do `app.html` sobre um DOM stub, captura o handler do ↻ e observa quem recebe `loadData`, em que ordem e com qual force — **5/5 cenários OK** (Início com dash fechado → `inicio:force, plan:cache`; Início com dash aberto → `inicio:force, plan:cache, dash:cache`; Dashboard → `dash:force, inicio:cache, plan:cache`; Extração → `plan:force, inicio:cache, dash:cache`; Extração servida em versão antiga sem `loadData` → `inicio:force, dash:cache`, degrada sem quebrar). Sempre exatamente 1 force, sempre no app visível. `check-tokens` verde; `vm.Script` OK nos 3 arquivos. Backup `Backups/s175b-atualizar-cascata/`. **Pendente:** segue faltando o teste do clique em prod (não abri navegador); a defasagem da base (gatilho 30 min + TTL 120 s) continua de pé por decisão. Ver [[fatuch_cadastro]] · [[abertas_duas_fontes_disjuntas]] · [[shell_app_sidebar_dupla]].)_

_Anterior: 2026-07-22 (sessão 174 — **Badminton entrou como esporte novo nos masters + pacote de desambiguação Tier 1/2.** Motivo: vamos começar a apostar em badminton. É o 3º esporte de raquete (com Tênis e Dardos); a colisão de identificação sobe para 3 vias. **Pesquisa (esquadrão de agentes + captura ao vivo da bet365, China Open, sem login):** taxonomia de mercados, sistema de pontuação (3×21 em 2026; vira 3×15 em 04/01/2027; Índia doméstica já em jul/2026), rosters BWF e PDC verificados nos rankings oficiais. Deliverables: `docs/PESQUISA_BADMINTON_2026.md` (mercados, casas, calendário, sites de resultado) e `docs/DESAMBIGUACAO_RAQUETE_2026.md` (rosters + blocos prontos + mapa de colisão). **Aplicado nos 3 masters globais:** `MASTER_ESPORTES` §4 (exemplo válido), §7 (entrada `## Badminton` com sinônimos + Referências auxiliares MS/WS/duplas do ranking BWF jun/2026 + Contextos auxiliares), Regra Crítica Badminton vs Tênis vs Dardos, nota na desambiguação de Sets, validação §8 itens 9 e 17. `MASTER_APOSTAS`: categoria `Pontos` estendida para Badminton (§3, §5, §7, §8) + regra por esporte §6 Badminton. `MASTER_DESCRICAO` §13.4 Badminton. **Decisões (Feca delegou):** (A) parcial do badminton → categoria `Sets` (o game do badminton = set do tênis); (B) total/handicap de pontos → `Pontos`; (C) unidade na descrição = `Sets` (game/jogo/set são sinônimos de entrada). **UI:** ícone 🏸 + SVG peteca nos 3 mapas (`app/static/index.html`, `dash/assets/js/data.js`, `docs/REFERENCIA_EMOJIS_ESPORTES.md`); alias `Badminton`/`Badmington`; bump `data.js?v` 5→6. **Design defensivo:** badminton exige sinal positivo (BWF/torneio/nome); padrão de desempate continua Tênis, nunca vira ralo-padrão. **Validação:** `check-tokens` verde; `node --check` OK em data.js e no SPORT_KEY do index. Backup `Backups/badminton-esporte-novo/`. **Pendente:** mapa §9 das casas (bet365 e Betano têm badminton, mas segue a regra — só cadastrar quando surgir bilhete real); 3 postos de simples e 3 de duplas faltaram no ranking-fonte (não inventados). Ver [[badminton_pesquisa]] · [[feedback_nova_ui_gate_total]].)_

_Anterior: 2026-07-21 (sessão 173 — **Extração: a grade agora preenche a viewport (fix de altura em telas baixas) + botão "Recolher captura".** **Sintoma (Feca):** em monitores baixos (ultrawide 25/29" ~1080px) a lista de apostas caía a ~3 linhas e ficava abaixo da dobra; num 32" parecia ok. **Causa REAL (achada na validação visual em Chrome, NÃO no read estático — meu diagnóstico inicial de "itens 1-3 já prontos" estava errado):** `.workfull` é um `display:grid` cuja única linha era implícita/`auto` → a `.colmain` colapsava ao conteúdo (medido: 76px de 632 disponíveis), então `partner-page`/`grade-section`/`.btbl-scroll` ficavam sem altura definida e o **scroll interno nunca se formava**. Em telas altas todo o conteúdo cabia (parecia ok); em baixas o `.content` (overflow:hidden) cortava a grade. **Fix estrutural (1 linha):** `grid-template-rows: minmax(0,1fr)` no `.workfull` — a linha passa a preencher a altura definida do flex:1, a `.colmain` estica (76→614px em 720px de viewport) e a grade vira área rolável de altura real; no modo 1-coluna (≤1180px) volta a `grid-template-rows:none` p/ preservar o comportamento estreito. **Item 4 — compactação por altura:** `@media (max-height:860px)` e `(max-height:720px)` encolhem padding/altura de `.capbox`/`.capbox__area`/`.tile`/`.input-section` (só dimensões px, como o resto do arquivo; nenhum token de cor/dinheiro tocado) p/ devolver linhas em telas curtas. **Item 5 — "Recolher captura":** botão no `#upload-section` (barra de ação, alinhado à direita via `.cap__sp`) colapsa as duas caixas de intake (`.cap__inputs`) via classe `.cap-recolhida`; preferência em `localStorage` `sharpen_cap_recolhida`, **default recolhido quando `innerHeight<820`**; script isolado no fim do body, **sem tocar em nenhum id/handler existente**. **Validação:** `check-tokens` verde (drift/paleta/shell/monetário); 3 scripts inline `node --check` OK; render headless (Chrome, cópia `_lt.html` neutralizando frame-buster/fetch, servida em :8791) medida em **720/900/1400px** → grade preenche até o rodapé, **scroll INTERNO** ativo (conteúdo 1566px > viewport), **thead sticky** grudado no topo, ~3/~8/~23 linhas visíveis rolando; toggle recolher 3→8 linhas + rótulo alterna "Recolher/Expandir"; empty-state (sem conta) rola por dentro, não quebra. Só moldura/CSS + 1 script — nenhum dado/cor/dinheiro/wiring alterado. Backup `Backups/extracao-viewport-fill-2026-07-21/` (só `index.html`). **Não meu (intocado):** untracked `docs/PESQUISA_BADMINTON_2026.md` e `docs/DESAMBIGUACAO_RAQUETE_2026.md`. Ver [[railv2_raiox]] · [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total]].)_



> **Histórico completo das sessões 171 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus

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
