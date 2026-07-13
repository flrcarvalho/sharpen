# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-13 (sessão 137 — **Ordem de envio no feed: extrações paralelas fora de ordem.** O Feca fez 2 extrações Bet365 em sequência (1ª: 2 múltiplas 12/07; 2ª: 7 dardos 13/07); as múltiplas, mais lentas de processar, salvaram DEPOIS dos dardos e furaram a fila (subiram ao topo). **Causa:** o feed ordena por `criado_em DESC, id DESC` e `criado_em` era `DEFAULT NOW()` carimbado no INSERT (fim do processamento, dentro de `/salvar`), não no envio; extrações rodam concorrentes (fire-and-forget — `runExtractionCard` chamado sem `await` em `index.html`) → a que termina primeiro ganha `criado_em` menor. **Fix estrutural (carimbar a hora do ENVIO, decidido com o Feca via `AskUserQuestion`):** o cliente captura `new Date().toISOString()` no clique de Extrair e manda `submitted_at` no `/salvar`; `SalvarRequest` aceita o campo, `salvar` converte p/ datetime aware (trata sufixo `Z`), `upsert_bilhetes(criado_base=...)` grava `criado_em = COALESCE($18::timestamptz, NOW())` com `+i µs` por linha (preserva a ordem interna do lote via desempate temporal + `id`). Ausente/inválido → `NOW()` — sync/import/extensão seguem intactos. **Verificado contra o banco** (linhas de teste descartáveis, 3 casos: carimbo == envio; **UPSERT/dedup NÃO altera `criado_em`**, só `atualizado_em`; fallback `NOW()`). **Fix de dados (Parte A):** as 2 múltiplas (`id 54298` odd 66,31 = "6 Múltiplas"; `id 54297` odd 9,30 = "Triplas") tiveram `criado_em` reposicionado p/ logo ABAIXO do lote de dardos (T_min−1s / −2s), mantendo 66,31 acima de 9,30 → feed agora: 10 dardos 13/07 no topo, depois as 2 múltiplas 12/07. Único campo tocado foi `criado_em` (nada de `atualizado_em`/conteúdo). Backup dos dados em `Backups/sessao137-ordem-bet365-12-07/`. Arquivos de código: `app/static/index.html`, `app/main.py`, `app/repository.py` (+backup dos 3 no mesmo `Backups/`). Ver [[data_fuso_local_nunca_utc]] · [[dedup_gap_sem_codigo_reextracao]].)_

_Anterior: 2026-07-12 (sessão 136 — **Página de Início (home pós-login) + fix do seletor de conta ativa.** Handoff do Claude Design (`Downloads/FDC Capital - Branding (2).zip` → `handoff-inicio/`: 2 SPECs + referências navegáveis). **(1) Seletor de conta ativa** (`renderAcctTree` + CSS, só `index.html`): dropdown "Conta ativa" redesenhado no modelo **casa é moldura, parceiro é botão** — cada casa vira cartão de grupo NÃO clicável (banda com logo 20px, nome mono 9.5px uppercase apagado, **contagem "N conta(s)"**); cada conta vira linha-botão (dot de status, nome sans 13.5px semibold, sub-linha `operador · {Fornecedor}` vinda do parse REAL de `"Conta [Fornecedor]"`, badges azul/âmbar preservados, chevron › no hover, selecionada com **check + accent**), alvo ≥40px, focável + Enter/Espaço. Busca/tabs ATIVAS·INATIVAS/+Nova conta intactos. **(2) Nova rota `/inicio`** (`app/static/inicio.html` + `GET /inicio` em `main.py`): home híbrida **C+A** servida como **3º iframe** da casca (`app.html`) — cabeçalho saudação-por-hora + CTA "Processar bilhetes" (glifo IA) → Extração; briefing narrativo por regras (dia positivo/negativo/sem-apostas); **4 KPIs** (P/L hoje `fmtPL`, P/L mês + ROI, em jogo agora n + R$ em risco `fmtR`, contas ativas n/total·casas); e — **após feedback do Feca** ("não copie o layout do Claude Design sem o cérebro do produto; é a porta de entrada, não pode ser página burra") — os **3 pilares de navegação (que só duplicavam a sidebar) foram trocados por conteúdo real** e refinados em 2ª rodada de feedback: **Apostas em Aberto** (exposição viva: stake@odd via `moneyStake`/`fmtOdd`, rodapé = **soma do capital em aberto** `fmtR`), **Bookies** e **Tipsters** (cada um: **top 5 ↑ Ganhando / top 5 ↓ Perdendo** do mês por P/L, `fmtPL`), **Precisa de você** (pendências: sem tipster / paradas 48h+ / custos sem preencher) e **Últimas extrações** (histórico RAIO-X do `localStorage`). Briefing virou **resumo escrito de verdade** (sem travessão "—" nem repetir o número do KPI). Página **alinhada à esquerda** (colada na sidebar, não centralizada). P/L hoje **neutro** (`R$ 0`) quando não há apostas encerradas. Layout em blocos que fecham na mesma altura (sem área morta). **3ª rodada — conformidade /nova-ui:** chip de esporte dessaturado (§4: `.sp-chip` 24×24 steel `grayscale(1)`, não colorido); Bookies/Tipsters viraram **tabela canônica** (§2/§4: header mono uppercase, rank/nome/valor, `fmtPL` cor só no número, linhas `--line-2`); rótulos **Positivos/Negativos**; totalizador "Capital em aberto" como **linha de soma** (rótulo mono uppercase, valor `--ink` à direita). **Item "Início" no topo da sidebar** + roteamento `#inicio` + **redirect pós-login cai em Início** (host `route()` default = `go('inicio')`). Todos os números vêm dos endpoints reais (`/dashboard/data`, `/bilhetes?extraction_state=aberta`, `/parceiros`, `/incompletos`) — **nada hardcoded**. **Marca:** todo R$ via `.money` canônico (`fmtPL`/`fmtR`/`fmtPct` copiados **verbatim** de `dash/assets/js/app.js`); **ressalva registrada** — `fmtPL` verbatim renderiza um P/L exatamente zero como `+R$ 0,00` verde (divergência **pré-existente do helper canônico** vs "zero neutro" do `UI_REFERENCE §5.1`; NÃO introduzi formatador novo, mantive consistência com o dashboard — corrigir na fonte canônica fica p/ passo dedicado). **Validação:** `check-tokens` verde (drift/paleta/shell/monetário); JS do `index.html` passa `node --check`; **render headless (Chrome)** confirmou KPIs/briefing/pendências/histórico populados com a base do Feca (P/L hoje +R$ 4.652,74 · 135 encerradas · 19 contas de 144 · 13 casas · 28.363 apostas). Aceite dos 2 SPECs ✅. Backup `Backups/inicio-e-seletor-2026-07-12/`. Ver [[railv2_raiox]] · [[migracao_planilha_dashboard]] · [[feedback_marca_helpers_dinheiro]].)_

_Anterior: 2026-07-12 (sessão 135 — **Dois furos de integridade na extração (dados + gravação).** Trabalho paralelo à 134. **Furo 1 — resultado minúsculo virava "aguardando resultado".** O Feca editou 5 bilhetes da Superbet digitando `v` minúsculo. Badge e `calcular_pl` já faziam `.strip().upper()` (mostravam **V** e R$ 0,00), mas a derivação de `extraction_state` na GRAVAÇÃO usava o conjunto case-sensitive `{W,L,V,HW,HL}` → `'v'` não batia → ficava `'aberta'` → contava como "aguardando resultado". **Fix (commit `27b8717`):** `.strip().upper()` em `upsert_bilhetes` e `atualizar_bilhete`. Backfill de 6 linhas já gravadas (`scripts/backfill_resultado_maiusculo.py`, 5×'v' + 1×'w'). **Furo 2 — aposta com resultado mas SEM odd salvava como "resolvida limpa" e duplicava.** Extrair a Bolsa de Aposta com as linhas **colapsadas** (odd e "ID da Aposta" escondidos) salvava o bilhete sem odd e sem código; como não tem código, não casa (dedup) com a versão correta já extraída COM código → duplicata fantasma. **Fix (commits `b72ebf5` + `1445785`):** helper novo `estado_extracao(resultado, odd)` — `resolvida` EXIGE resultado canônico E odd > 0; senão `aberta` (badge âmbar + aviso "sem odd" no Raio-X, que já existia em `analisar_extracao`). Aplicado em `upsert_bilhetes` e `atualizar_bilhete` (recalcula estado quando resultado OU odd muda, usando o valor final de cada um). +1 teste; 99 passando. **Decisão deliberada — NÃO gatear o feed por `extraction_state`:** há **148 L + 5 V sem odd** na base inteira; numa aposta L o P/L = −stake **independe da odd**, então esses valores estão corretos. Excluir "sem odd" do feed apagaria 148 perdas reais de todos os donos. O feed (`dashboard_rows`) segue recomputando por resultado/stake/odd/data e ignora `extraction_state`; o flag é só sinal de visibilidade. **Limpeza:** Bolsa de Aposta/Feca 222→219 (`scripts/limpar_orfas_bolsa_2026-07-12.py`: 2 duplicatas sem odd + 1 "Saque R$ 674,48" com stake 0). Deixada 1 órfã arquivada (Folarin 25/06, V, sem odd — inócua). **PENDENTE:** nada crítico; opção de apagar a órfã `id 3351`. **Nota:** esta sessão rodou em paralelo à 134 (fix de fuso do dashboard); a 134 varreu meu `repository.py` staged e commitou como `b72ebf5`. Ver [[resultado_case_sensitive_bug]] · [[extracao_sem_odd_flag]] · [[dedup_gap_sem_codigo_reextracao]].)_

_Anterior: 2026-07-12 (sessão 134 — **Filtro de data do dashboard usava UTC → "Hoje" virava amanhã à noite.** O Feca mostrou que às 22:41 (Brasília, UTC−3) o botão Hoje resolvia para o dia seguinte (13/07) e, ao voltar um dia, o label das flechas descasava do input (input 12/07, flecha 11/07, e o scroll ficava em 11/07). **Causa:** todos os helpers de data usavam `.toISOString().slice(0,10)`, que formata em UTC; à noite o relógio UTC já virou o dia. Em `navDay` o label das flechas era calculado em fuso local mas o filtro em UTC → fontes diferentes, descasamento. **Fix (só JS do dash, commit `06ed546`):** helper novo `_ymd(d)` formata a data no fuso local (mesma lógica do `hojeISO()` do `index.html`); trocados todos os `toISOString().slice(0,10)` de data em `dash/assets/js/filters.js` (`_today` / `_wtdStart` / `_mtdStart` / `navDay` / `navMonth` / `filtrarPagina` / `filtrarAbertas` / `_selRange`) e `dash/assets/js/charts/performance.js` (`_sliceByPeriod` + cutoffs 30/15d). `temporal.js` não tocado (já ancorado em `T12:00:00` local, nunca cruza fronteira de dia UTC). Cache-bump `filters.js?v=6→7`, `performance.js?v=7→8`. `check-tokens` verde. **Nota:** após este commit outros 3 commits (`01b1fb3` / `b72ebf5` / `1445785` — plano de flag de inferência + dedup `estado_extracao` resultado sem odd) entraram na main; não documentados aqui (fora desta sessão). **PENDENTE:** verificação AO VIVO do Feca (Hoje = dia certo; flecha e input casados ao voltar um dia). Ver [[migracao_planilha_dashboard]].)_

_Anterior: 2026-07-12 (sessão 133 — **Bet365 `Criar Aposta +` (super múltipla) lida como N bilhetes → fix na regra.** O Feca mandou um print de uma super múltipla Bet365 (`R$20,00 Criar Aposta +`, quatro blocos `CRIAR APOSTA 4.50/5.50/6.00/6.00`, um só rodapé) que a IA quebrou em **4 linhas de R$20 cada** em vez de **1 bilhete**. **Causa:** a regra do §3/§14 já dizia "1 cabeçalho verde = 1 bilhete", mas nada ensinava a IA a NÃO tratar os sub-rótulos internos `CRIAR APOSTA <odd>` (verde/cinza, **sem** prefixo `R$`) como cabeçalho — eles são **pernas** (cada uma um Bet Builder), não bilhetes. **Fix (só `casas/CASA_BET365.md`, doc/regra):** (§1 Anatomia) só conta como bilhete o cabeçalho com `R$<stake>`; confirmar pela contagem de blocos financeiros no rodapé (um só = um bilhete). (§9) nota nova "Criar Aposta + (super múltipla) → ainda UMA linha": odd = **produto** das odds dos blocos (`4,50×5,50×6,00×6,00 = 891,00`; em L é a odd estrutural, nunca 0,00), descrição junta todas as seleções de todos os blocos com ` // `. (§13/§14) 1 pegadinha + 1 validação. (§15) golden **#11** com o bilhete real (stake 20,00, odd 891,00, L; Erling Haaland/Mikel Oyarzabal = originais tachados sob SUBSTITUIÇÃO+). Backup em `Backups/casa-bet365-super-multipla-criar-aposta/`. **Correção operacional pro Feca no dashboard:** excluir as 4 linhas e reprocessar (agora lê como 1), ou editar 1 linha p/ odd 891,00 e apagar as outras 3. Ver [[bet365_dedup_e_vazamento_imagens]].)_

_Anterior: 2026-07-12 (sessão 133 — **Rail "Sharpen IA" — Fase 1 (rename + compactar topo).** O Feca quer repensar o rail direito da tela de Extração: (1) nome mais ligado à marca; (2) resultado da IA **objetivo pro cliente** e um **backoffice maior só pra nós** (devs) com histórico/evolução; (3) layout: encolher a barra Operador/Conta + a strip de KPIs e o rail virar full-lateral. Fatiado em 3 fases (invariante 6). **Fase 1 aplicada, só `index.html`, baixo risco:** (a) título do rail `Análise IA` → **`Sharpen IA`** (nome escolhido pelo Feca no `/nova-ui`); (b) **compactada a casca do topo** — `.ctxbar` (padding 8/12→6/10, margin-bottom 12→8) e `.ctx-kpis`/`.ctx-kpi` (margin-bottom 12→8, kpi padding 9/16→6/14, gap 3→2) → o topo fica mais denso e o rail (full-height do `partner-body`) ganha altura. Só spacing + label, zero JS/backend. `/nova-ui` conferido: rail é 100% token, sem dinheiro, confiança é `%`; **check-tokens verde** (drift/paleta/shell 5/5/monetário). Backup em `Backups/sessao133-sharpen-ia-rail-layout/`. **PENDENTE (aguardando OK do Feca):** **Fase 2** — limpar o registro do rail pro cliente (tirar da vista tokens crus `in/out/%`, modelo, segundos, assinatura; guardar esses dados pro backoffice); **Fase 3** — persistir cada extração no Postgres (timestamp/dono/operador/casa/modelo/tempo/tokens/custo/itens/confiança/duplicadas) + página de backoffice dev com histórico e métricas de evolução (candidato: evoluir a `/uso/tokens`). Fase 3 mexe em backend+banco → plano dedicado antes. **FASE 2 APLICADA (limpar o rail pro cliente, CSS puro, no ar):** os dois pontos técnicos visíveis foram escondidos da vista do cliente — (a) `.ec-tok` (tokens crus `in:… out:… %↑` no card) e (b) `.rail-foot` (modelo `Sonnet 4.6` + segundos; o nº de itens já vive no KPI). **Só `display:none`, reversível, zero risco de JS:** o dado técnico CONTINUA chegando no evento SSE `done` e é logado server-side (`/uso/tokens`) — a Fase 3 lê de lá, nada se perdeu. O rail agora mostra ao cliente só: pill de estado, 3 KPIs (Itens/Duplicadas/Confiança), veredito ("Extração limpa…") e "✓ N novo(s)" + identidade casa·parceiro + horário + thumbs. check-tokens verde. **PENDENTE:** **Fase 3** — persistir cada extração no Postgres + backoffice dev com histórico/evolução (plano dedicado antes, mexe em backend+banco). **PIVOT no mesmo dia — rail v2 "RAIO-X" (handoff do Claude Design).** O Feca trouxe um handoff (zip `Downloads/FDC Capital - Branding (1).zip` → `handoff-rail-v2/`: SPEC + mockup navegável `reference/planilhador-v2.html` + `glifo-kit.html` + tokens + SVGs) e mandou implementar no Planilhador/Contas & Parceiros. **Decisões fechadas (não reabrir):** rail se chama **RAIO-X** (eyebrow mono; nunca "Análise IA", **nunca "Sharpen IA"** — a IA é assinada pelo glifo, não por texto); técnico (modelo/tokens/custo) só dentro do `<details>` Backoffice; histórico persiste os resumos por extração e reabre resultados. **4 FASES ENTREGUES E NO AR (só `index.html`):** (1) **Layout** — grid `.workfull` (`minmax(0,1fr) 372px`): ctxbar + KPI bar + intake + grade vão pra `.colmain` (esquerda), o rail sai do `partner-body` e vira 2ª coluna full-lateral. **Adaptação:** o SPEC usa scroll de página + rail `sticky/100vh`; o app usa shell de viewport fixa com scroll interno → adaptei pro grid com scroll interno (mesmo visual, sem tocar na casca). (2) **Intake compacto** — dropzone vira faixa horizontal; textarea nasce 1 linha (38px) e expande no focus (70px). (3) **Camadas do rail** — veredito didático (cliente, síntese ok/warn), notas AÇÃO/CONFERIDO (info→backoffice), `<details>` Backoffice (modelo/duração/tokens/confiança/assinatura), rodapé de cliente ("Extração de hoje HH:MM · N itens"), e **histórico "Últimas extrações · 7 dias"** persistido em `localStorage` (`sharpen_raiox_hist::<dono>`, 40 máx, filtro 7d) clicável p/ reabrir o resumo; `renderRail` reescrito; skeletons no processando. (4) **Glifo IA** — assina botão Processar (14px) + linhas do histórico (13px, cor semântica); head do rail já assinado. **Deferidos (registrados, não fabricados):** seletor de modelo (não existe no app — modelo é backend-only) e célula "campo inferido" na grade (precisa de flag de confiança por-campo do backend). **Limitação:** <1180px o rail cai pra baixo (checklist ✓) mas o empilhamento clipa no shell de altura fixa — desktop (alvo) é limpo. **Verificação:** `/nova-ui` rodado; check-tokens verde (cores por token/triplet); JS 0 erros (vm); render headless (Chrome) conferido contra o mockup em desktop + estado concluído; checklist de aceite 8/8 (responsivo com a ressalva). Backup `Backups/sessao133-railv2-raiox/`. O nome "Sharpen IA" **não existe mais** na UI (absorvido pelo RAIO-X). **MCP Claude Design:** implementado do handoff local (espelha o projeto de design); o round-trip do `DesignSync` não foi necessário (serve p/ sincronizar biblioteca de componentes, não p/ implementar numa página de produto). **FOLLOW-UP (mesmo dia): célula inferida entregue via o sinal REAL de incerteza.** O ponto deferido "campo inferido pela IA" foi construído ancorando o **glifo âmbar 11px** no amarelo acionável já existente (`.btbl-tipo.incerta` ↔ `_apostaIncerta`/`repository._aposta_incerta`: categoria `Outros`/⚠️), clicável → `abrirEdicao`. **Achado importante:** o app não tem confiança por-campo da IA e o **tipster sai vazio da extração** (é atribuído pelo operador, não inferido) — logo "tipster deduzido" do mockup não tem gatilho real hoje; um flag de confiança por-campo (ligado ao loop de correções da extração worldwide) fica pra frente. Só resta mesmo deferido o **seletor de modelo** (não existe no app; modelo é backend-only). Ver [[railv2_raiox]] · [[extracao_worldwide_fase012]] · [[custo_escala_extracao]].)_

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
