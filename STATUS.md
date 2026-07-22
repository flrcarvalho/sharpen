# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-22 (sessão 175 — **O ↻ "Atualizar" passou a valer na tela de Início (e a furar o cache da planilha viva).** **Sintoma (Fatuch):** o painel "Apostas em Aberto" mostrava 2 apostas de tênis já liquidadas (Zhou vs Geerts @1,50 e Seggerman / Herbert @1,80, TCINSIDER) e **nenhuma** das 20 do dia que o "TODAY BETS" da planilha dele listava (TCINSIDER 1 · PEIXE 1 · ARRUDEX 18, R$ 6.134). **Diagnóstico (feed puxado ao vivo, não deduzido):** o `/exec` do Apps Script dele respondeu `ok=true count=5485 builtAt=18:45:41Z` com **21 abertas** — as 18 ARRUDEX, a PEIXE e a TCINSIDER "Faria / Rocha", batendo linha a linha com o TODAY BETS; as duas do print **não estavam mais lá** (liquidadas na planilha, saíram sozinhas). Ou seja: **os dois sintomas são o mesmo, e nenhum é bug de lógica** — o painel do início une feed + Postgres corretamente desde a s168. O que ele viu foi um retrato velho. **Causa raiz:** a carteira de planilha AO VIVO tem DOIS caches empilhados — Apps Script grava o JSON no Drive a cada **30 min** (gatilho) e `planilha_viva.py` guarda **120 s** em memória → defasagem de até ~32 min entre planilha e tela. Trigger conferido saudável (cache de 15 min na hora da checagem), então o atraso é o projetado, não uma pane. **Agravante corrigido:** o único caminho que fura os dois caches é `?refresh=1` (`dashboard_data(refresh)` → `dashboard_rows_ao_vivo(refresh=True)`), disparado pelo ↻ da casca — mas o handler só falava com o iframe do Dashboard e **saía em silêncio se ele não tivesse aberto**. Quem estava na tela de Início clicava e não acontecia nada — justo onde mora o painel que mais envelhece. **Fix (escolha do Feca: só os botões, gatilho de 30 min intocado):** (a) `inicio.html` — `boot(force)` passa `?refresh=1` ao feed (só ele; `/bilhetes`, `/parceiros` e `/incompletos` são Postgres, sempre frescos), expõe `window.loadData(force)` no **mesmo contrato do dash** e publica `window._dataBuiltMs` a partir do `builtAt`; (b) `app.html` — `refreshTarget()` escolhe o app **visível** que sabe recarregar (Início ou Dashboard; na Extração cai no Dashboard carregado ou no Início, pra o botão nunca ficar morto) e `paintSync` lê o `builtAt` desse alvo, não mais só do dash. Reexecutar `boot` é seguro: todo render substitui `innerHTML` (listeners junto). **Validação:** `check-tokens` verde (drift/paleta/shell/monetário) e `vm.Script` OK nos scripts inline dos 2 arquivos. Nenhum dado, cor, dinheiro ou formatador tocado — só wiring do botão. Backup `Backups/s175-botao-atualizar-inicio/` (só os 2 arquivos editados). **Pendente:** teste do clique em prod pelo Feca/Fatuch (não validei em navegador); a defasagem de base (gatilho de 30 min + TTL de 120 s) **continua de pé** por decisão — as opções recusadas foram baixar o gatilho p/ 5-10 min e carimbar "dados de HH:MM" no painel. Ver [[fatuch_cadastro]] · [[abertas_duas_fontes_disjuntas]] · [[shell_app_sidebar_dupla]].)_

_Anterior: 2026-07-22 (sessão 174 — **Badminton entrou como esporte novo nos masters + pacote de desambiguação Tier 1/2.** Motivo: vamos começar a apostar em badminton. É o 3º esporte de raquete (com Tênis e Dardos); a colisão de identificação sobe para 3 vias. **Pesquisa (esquadrão de agentes + captura ao vivo da bet365, China Open, sem login):** taxonomia de mercados, sistema de pontuação (3×21 em 2026; vira 3×15 em 04/01/2027; Índia doméstica já em jul/2026), rosters BWF e PDC verificados nos rankings oficiais. Deliverables: `docs/PESQUISA_BADMINTON_2026.md` (mercados, casas, calendário, sites de resultado) e `docs/DESAMBIGUACAO_RAQUETE_2026.md` (rosters + blocos prontos + mapa de colisão). **Aplicado nos 3 masters globais:** `MASTER_ESPORTES` §4 (exemplo válido), §7 (entrada `## Badminton` com sinônimos + Referências auxiliares MS/WS/duplas do ranking BWF jun/2026 + Contextos auxiliares), Regra Crítica Badminton vs Tênis vs Dardos, nota na desambiguação de Sets, validação §8 itens 9 e 17. `MASTER_APOSTAS`: categoria `Pontos` estendida para Badminton (§3, §5, §7, §8) + regra por esporte §6 Badminton. `MASTER_DESCRICAO` §13.4 Badminton. **Decisões (Feca delegou):** (A) parcial do badminton → categoria `Sets` (o game do badminton = set do tênis); (B) total/handicap de pontos → `Pontos`; (C) unidade na descrição = `Sets` (game/jogo/set são sinônimos de entrada). **UI:** ícone 🏸 + SVG peteca nos 3 mapas (`app/static/index.html`, `dash/assets/js/data.js`, `docs/REFERENCIA_EMOJIS_ESPORTES.md`); alias `Badminton`/`Badmington`; bump `data.js?v` 5→6. **Design defensivo:** badminton exige sinal positivo (BWF/torneio/nome); padrão de desempate continua Tênis, nunca vira ralo-padrão. **Validação:** `check-tokens` verde; `node --check` OK em data.js e no SPORT_KEY do index. Backup `Backups/badminton-esporte-novo/`. **Pendente:** mapa §9 das casas (bet365 e Betano têm badminton, mas segue a regra — só cadastrar quando surgir bilhete real); 3 postos de simples e 3 de duplas faltaram no ranking-fonte (não inventados). Ver [[badminton_pesquisa]] · [[feedback_nova_ui_gate_total]].)_

_Anterior: 2026-07-21 (sessão 173 — **Extração: a grade agora preenche a viewport (fix de altura em telas baixas) + botão "Recolher captura".** **Sintoma (Feca):** em monitores baixos (ultrawide 25/29" ~1080px) a lista de apostas caía a ~3 linhas e ficava abaixo da dobra; num 32" parecia ok. **Causa REAL (achada na validação visual em Chrome, NÃO no read estático — meu diagnóstico inicial de "itens 1-3 já prontos" estava errado):** `.workfull` é um `display:grid` cuja única linha era implícita/`auto` → a `.colmain` colapsava ao conteúdo (medido: 76px de 632 disponíveis), então `partner-page`/`grade-section`/`.btbl-scroll` ficavam sem altura definida e o **scroll interno nunca se formava**. Em telas altas todo o conteúdo cabia (parecia ok); em baixas o `.content` (overflow:hidden) cortava a grade. **Fix estrutural (1 linha):** `grid-template-rows: minmax(0,1fr)` no `.workfull` — a linha passa a preencher a altura definida do flex:1, a `.colmain` estica (76→614px em 720px de viewport) e a grade vira área rolável de altura real; no modo 1-coluna (≤1180px) volta a `grid-template-rows:none` p/ preservar o comportamento estreito. **Item 4 — compactação por altura:** `@media (max-height:860px)` e `(max-height:720px)` encolhem padding/altura de `.capbox`/`.capbox__area`/`.tile`/`.input-section` (só dimensões px, como o resto do arquivo; nenhum token de cor/dinheiro tocado) p/ devolver linhas em telas curtas. **Item 5 — "Recolher captura":** botão no `#upload-section` (barra de ação, alinhado à direita via `.cap__sp`) colapsa as duas caixas de intake (`.cap__inputs`) via classe `.cap-recolhida`; preferência em `localStorage` `sharpen_cap_recolhida`, **default recolhido quando `innerHeight<820`**; script isolado no fim do body, **sem tocar em nenhum id/handler existente**. **Validação:** `check-tokens` verde (drift/paleta/shell/monetário); 3 scripts inline `node --check` OK; render headless (Chrome, cópia `_lt.html` neutralizando frame-buster/fetch, servida em :8791) medida em **720/900/1400px** → grade preenche até o rodapé, **scroll INTERNO** ativo (conteúdo 1566px > viewport), **thead sticky** grudado no topo, ~3/~8/~23 linhas visíveis rolando; toggle recolher 3→8 linhas + rótulo alterna "Recolher/Expandir"; empty-state (sem conta) rola por dentro, não quebra. Só moldura/CSS + 1 script — nenhum dado/cor/dinheiro/wiring alterado. Backup `Backups/extracao-viewport-fill-2026-07-21/` (só `index.html`). **Não meu (intocado):** untracked `docs/PESQUISA_BADMINTON_2026.md` e `docs/DESAMBIGUACAO_RAQUETE_2026.md`. Ver [[railv2_raiox]] · [[shell_app_sidebar_dupla]] · [[feedback_nova_ui_gate_total]].)_

_Anterior: 2026-07-21 (sessão 172 — **Pinnacle entrou no SharpenUp (modo texto) + faixa "Novidades" na home.** **1. Pinnacle vira casa de robô** (commits `8355423` back+extensão, `344b4e8` gate do front). Antes só dava print; agora o SharpenUp puxa o dado exato por hook JSON, como Betano/Betfair. **Como:** `extensor/pn_inject.js` (novo, mundo MAIN) faz hook do `POST /member-service/v2/wager-filter` — cada bilhete é um **array posicional** (~98 campos, SEM nomes), convertido em objeto nomeado por de-para ancorado (0=P/L, 6=WIN/LOSE, 7=ID, 9/10=confronto, 14=colocação, 15=data-evento, 16=odd, 18=SETTLED, 20/22=seleção, 24=linha, 28=liga, 29=stake, 31=esporte, 44=pernas-múltipla, 45=categoria, 46=unidade, 93=WON/LOST/PUSHED). **Replay ativo** (espelho do `bf_inject`): re-emite a busca das DUAS abas numa rodada — `s=SETTLED&type=WAGER` (encerradas, janela de dias) + `s=OPEN&type=EVENT` (abertas, todas); campos `s/type/sd/f/t/d` confirmados nos dois Payloads reais (`sd=false` nas duas, `type` é o discriminador junto do `s`). `content.js`: `formatTicketPN`, `roboPinnaclePassive`, `pnById` (SETTLED vence aberta), autodiagnóstico. `captura.py`: PINNACLE=texto + host. `popup.js`: injetor MAIN + guard. `manifest` 0.4.0→**0.5.0**. Parser+formato **validados contra o dump real** (ML/OU/prop-WNBA/Mix-Parlay) e os goldens da CASA_PINNACLE. Feca testou ao vivo: **funcionou.** Fiel à §4 (data=evento), §1 (ponto→vírgula), §6/§7 (sem boost/cashout), §13 (`-vs-`→`v`, esporte≠liga). **Pendente:** confirmar o formato do bilhete ABERTO real (trato `≠SETTLED`→aberta; se índice deslocar em aberta é ajuste de 1 linha). **2. Faixa "Novidades" na home** (`inicio.html`): changelog dev-controlado (array `NOVIDADES`, mesmo p/ todos os donos), faixa larga abaixo dos KPIs; some sozinha após `NOV_DIAS=45`; badge "novo" some depois que o dono vê (localStorage `sharpen_novidades_seen::<dono>`). 1ª entrada = a própria Pinnacle. Reusa a casca `.panel/.ph`, cor 100% token, data em fuso local (nunca UTC), sem dinheiro/formatador. Gate `/nova-ui` cumprido: JS `vm.Script` OK, `check-tokens` verde, render headless conferido. Backups `Backups/sessao170-pinnacle-sharpenup/` e `Backups/sessao172-novidades-inicio/`. **Segurança:** Feca colou cookies de sessão vivos da Pinnacle no chat (JWT `sb`/`BIAB_CUSTOMER`, `cf_clearance`) → recomendei trocar a senha. **Não meu (intocado):** untracked `docs/PESQUISA_BADMINTON_2026.md` e `docs/DESAMBIGUACAO_RAQUETE_2026.md`. Ver [[pinnacle_sharpenup]] · [[extensor_captura]] · [[feedback_nova_ui_gate_total]].)_


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
