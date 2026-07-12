# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-12 (sessão 132 — **PLANO de extração worldwide + Fase 0 validada. Sem código de app.** O Feca levantou a dor de escala: milhares/dezenas de milhares de casas no mundo → construir "1 extrator por casa" é esteira infinita e inviável. Rodei 3 modelos independentes (Sonnet, Opus, Fable): **consenso total** — o gargalo NÃO é a IA de leitura (zero-shot lê bilhete auto-descritivo em qualquer idioma; custo é O(volume), não O(nº de casas)), é a **tradução por casa ser artesanato humano** (o `casas/CASA_*.md` escrito ANTES do uso = *push*). O SharpenUp por DOM (`extensor/content.js` com dispatcher + `*_inject.js` por casa) é o único bespoke real → fica premium, não escala. **A virada:** de *push* para *pull* — zero-shot é o default; o arquivo de casa vira **cache aprendido** pelo uso (tabela `mapa_mercado`), não markdown escrito à mão; confidence por campo (amarelo + confirmação em 1 clique); graduação automática da casa. Isso É o popup **"+adicionar conta"** do Feca (digita casa nova → 1 linha + url/favicon → extrai já → correções engordam o cache). **Invariante crítico:** adicionar casa = 1 linha + funciona já; tradução vem do uso, nunca antes. **Fase 0 rodada e validada:** extraí 110 pares `rótulo cru → categoria` dos §9 de 13 casas; agente Sonnet categorizou em modo cego (só MASTERs globais, proibido ler `casas/`). **Resultado: 90,0% match cru → 94,5% de acerto real de categoria; erro silencioso só 3,6% (4/110), 100% em nicho obscuro (RBIs baseball, 1º/último marcador, total de faltas) — exatamente onde o cache aprendido atua; 1 alucinação (categoria fora da §3) → guardrail de enum na Fase 1.** Plano completo das 5 fases (esforço/custo/prazo) + evidência da Fase 0 em [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md). **Custo op.:** extração segue ~$0,011/bilhete, não sobe com nº de casas. **Prazo:** MVP "funciona no mundo dia 1" = Fases 0+1+2 ~6-8 sessões; produto que melhora sozinho = +3+4+5 ~9-14 sessões. **PRÓXIMO PASSO:** construir Fase 1 (confidence da IA + guardrail de enum) quando o Feca quiser. Ver [[migracao_planilha_dashboard]] · [[pl_calculo_derivado]] · [[polymarket_proxy_e_slug]].)_

_Anterior: 2026-07-12 (sessão 131 — **Faxina do STATUS.md.** O arquivo tinha 982 linhas / ~392 KB e era relido inteiro via `@STATUS.md` a cada sessão (~100k tokens). O changelog narrativo das sessões 127→14 (cadeia `_Anterior_` do topo + os corpos dos antigos §4 "Estado atual" e §6 "Próxima sessão") foi movido **verbatim** para `docs/HISTORICO.md` (commit `f61ee5e`); o §4 virou estado-vivo enxuto e as duas listas de pendências duplicadas viraram uma só (§5). Auditoria (2 agentes) confirmou que as regras enterradas na narração já vivem nos docs canônicos (`casas/CASA_*`, `global/MASTER_*`, `CLAUDE.md`) — o HISTORICO preserva o texto integral, nada se perdeu. STATUS: 982 → ~115 linhas. Backup em `Backups/faxina-status-sessao-131/`.)_

_Anterior: 2026-07-12 (sessão 130 — **FATUCH: dashboard "sumiu tudo" no sync. Apps Script passa a ler por cabeçalho.** O operador Gabriel (Los Panas) reportou que clicou em sincronizar e a carteira zerou, sem mensagem de erro. **Causa:** ele apagou duas colunas da base (Parceiro e Tipo) que "não usava mais". O `apps_script/Code_LavaFatuch.gs` lia as colunas por POSIÇÃO fixa (Stake sempre na coluna I). Com duas colunas a menos, tudo deslizou para a esquerda; o Stake passou a ser lido da coluna W/L (texto vira 0); a regra `stake<=0` descartou toda linha; o feed voltou `ok:true, data:[]` e o dashboard renderizou vazio sem erro. Como o Fatuch não tem base no Postgres (tudo vem da planilha viva do LavaFatuch), zerou 100%. **Fix (commit `8b31cb9`):** `getData` agora mapeia as colunas pelo NOME do cabeçalho (linha 3), não por posição. Mexer, mover ou renomear coluna não quebra mais. Coluna obrigatória ausente vira ERRO VISÍVEL (`ok:false`) em vez de base vazia em silêncio. Layout novo confirmado no print: Data, Esporte, Tipster, CASA, Aposta, Descrição, Stake(R$), Odd, W/L, U Investida, P/L(U), P/L(R$), Earn, Espelho. Sem Parceiro nem Tipo. **Decisão do Feca:** a coluna Espelho (MGM/365/Pinnacle/7k) vira parceiro/conta/fornecedor no dashboard (abas Fornecedores e Custos agrupam por ela). **Validação:** `node --check` OK; harness com os dados do print (5 linhas voltam certas, P/L da planilha como fonte de verdade, erro visível quando falta coluna); `check-tokens` verde no pre-commit. **Estado AO VIVO confirmado:** bati na URL `/exec` com `refresh=1` (roda o código deployado agora) e voltou `ok=true, count=5150`, com `fornecedor="MGM"` (=Espelho) na 1ª linha. Isso prova que o código novo JÁ está deployado (o código velho deixaria `fornecedor` vazio e retornaria 0 linhas). Dashboard do Fatuch de volta ao ar. **Achado de dados (não é código):** a coluna Espelho tem um VLOOKUP que não acha "Maximabet" e devolve `#N/A`; esse texto de erro vaza como fornecedor no dashboard. Não quebra nada, mas aparece feio na aba Fornecedores. **PENDENTE:** (a) Fatuch clicar "Atualizar dados" para ver a carteira; (b) Gabriel adicionar "Maximabet" à tabela do VLOOKUP da coluna Espelho; (c) renomear o rótulo do projeto no dashboard do Railway (herdado da 129, cosmético). Backup `Backups/apps-script-lavafatuch-header-based/`. **Nota operacional:** commit no repo NÃO atualiza o Apps Script vivo; alguém tem que colar o `Code_LavaFatuch.gs` no editor da planilha e reimplantar a MESMA implantação (Gerenciar implantações, Editar, Nova versão) para a URL `/exec` não mudar. Neste caso já foi feito. Ver [[fatuch_cadastro]] · [[migracao_planilha_dashboard]] · [[pl_calculo_derivado]].)_

_Anterior: 2026-07-12 (sessão 129 — **Organização pós-migração. Sem código de app.** O Feca perguntou por que a pasta ainda se chama Planilhador se o produto virou Sharpen, e se o projeto ainda estava dividido. **Diagnóstico:** o dashboard já vive 100% dentro da Planilhador (`app/static/dash/`, servido por `app/main.py`); a pasta antiga `Betting Dashboard/` era repo git separado e morto (último commit 28/06). **Feito, tudo reversível:** (1) `Betting Dashboard/` movida para `Backups/betting-dashboard-aposentado_20260712/` com histórico git e as mudanças não commitadas de resize de coluna (conferido: a feature já estava no dash vivo, nada perdido; nenhum código da Planilhador dependia da pasta). (2) Zips soltos da raiz (`Planilhador.zip`, `Be Rich.zip`) movidos para `Backups/zips-raiz_20260712/`. (3) **Repo GitHub renomeado `flrcarvalho/extrator` para `flrcarvalho/sharpen`** via API PATCH (token do Windows Credential Manager, que o próprio git já usa). GitHub mantém redirect do nome antigo. Remote local atualizado para `https://github.com/flrcarvalho/sharpen.git`; conectividade testada (`ls-remote` lista refs OK). Deploy do Railway não quebra: a integração é keyed por ID do repo, não pelo nome. **PENDENTE (precisa do Feca, não sai pela CLI):** (a) renomear o rótulo do projeto/serviço no dashboard web do Railway. A CLI v5.8 não tem comando de rename. É cosmético e não afeta deploy. (b) **Decisão do Feca: NÃO renomear a pasta local `Planilhador/` por ora.** Custo alto (órfã a memória, que é keyed no caminho `.claude/projects/...-Planilhador`, e quebra caminhos absolutos) e ganho nulo (só o Feca vê a pasta; o Railway lê do repo). O que importa já está Sharpen: produto, domínio sharpen.bet e repo. Memória `rename_sharpen_repo` criada. **PRÓXIMO PASSO:** renomear o rótulo no dashboard do Railway quando conveniente. Ver [[rename_sharpen_repo]] · [[dominio_sharpen_bet]].)_

_Anterior: 2026-07-12 (sessão 128 — **DASHBOARD: máscara de "sincronizando" no gráfico durante a revalidação (Opção A do ADR-002).** O Feca reportou que ao abrir a Visão Geral o "Resultado Geral" aparece com número baixo/errado (~R$100k) por 20-30s e só depois corrige (~R$300k). **CAUSA (não é bug):** é o stale-while-revalidate documentado (`ADR-002`). `loadData` (`app.js`) faz boot instantâneo com o **cache local (IndexedDB, dado velho)** e busca o fresco em 2º plano em `/dashboard/data` (base inteira, 24k+ linhas do Feca) — esse fetch leva os 20-30s; ao terminar, `renderPage` redesenha com o dado certo. O problema é só percepção: o dado velho passava como real. **FIX (Opção A, só UI):** enquanto revalida a partir do cache, `document.body.is-revalidating` **escurece o `#card-bankroll .chart-wrap`** (opacity .35 + saturate) e mostra um **pill fixo "Sincronizando dados… os números podem estar desatualizados"** com spinner (reusa o keyframe `update-spin`). Helpers `_revalOn()`/`_revalOff()` no `app.js`; `_revalOn` no ramo de cache (após `buildHTML`), `_revalOff` no bloco 3a (quando o fresco chega ou falha). Só no boot por cache — refresh manual (`force`) já tem o giro do botão. **VALIDAÇÃO:** `/nova-ui` (sem padrão monetário; cor de token; reuso de keyframe); `check-tokens` verde; `node --check app.js` OK; render headless confirmou dim + pill on-brand. Cache-bump `layout.css?v=5→6`, `app.js?v=16→17`. Backup `Backups/dash-mascara-revalidacao/`. **PENDENTE:** validação AO VIVO do Feca (abrir a Visão Geral: gráfico esmaecido + pill por ~20-30s → limpa quando o dado fresco entra). **Opção C (acelerar de verdade) explicada ao Feca com números, NÃO executada** — é a Fase 2 do ADR-002 (agregação no servidor / payload colunar), reescrita de núcleo, gate próprio. **128b — PLANO COMPLETO DE C escrito (sem código):** `docs/PLANO_DASHBOARD_C.md`, fundamentado em inventário do dashboard (agente Explore mapeou 10 páginas → A/B/C: maioria group-by materializável; C irredutíveis = Monte Carlo + correlação de tipsters; tabela Apostas = linhas cruas não-agregável). Decisões-chave: (1) contrato novo com **buckets diários** → período fatiado no cliente (navegação instantânea), só filtro categórico bate no servidor; (2) **custo em localStorage NÃO é bloqueador** — camada de custo fica no cliente sobre agregados brutos + accounts-meta do servidor; (3) faseamento por ONDE roda a matemática: Fase 1 agregação Python (source-agnóstica, cobre Postgres + Apps Script do LavaFatuch), Fase 2 GROUP BY SQL, Fase 3/D views materializadas; (4) Fase 0 = revalidação condicional `304` (barata, independente). Custos: egress no 15k ~$270→~$4,50/mês; build ~3-4 semanas meio-período + tokens em baixas centenas de US$. Riscos: paridade de número (harness dual-run), MC não-determinístico (tolerância estatística), UX de filtro (buckets diários). **Modelo ideal: híbrido — Opus no núcleo de paridade + port de MC; Sonnet no fan-out de endpoints/cliente/testes; Fable fora do caminho crítico.** Próximo passo proposto: Fase 0 + piloto da Fase 1 só na Overview (provar paridade + medir) antes do fan-out. Ver [[migracao_planilha_dashboard]].)_

> **Histórico completo das sessões 127 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
