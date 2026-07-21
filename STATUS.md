# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-20 (sessão 169 — **Re-auditoria turbo profunda + Onda 0 de segurança (2 XSS).** Rodou em paralelo às sessões 165-168; git intercalou limpo, commitei só os meus paths. **Auditoria (read-only, 2 passadas):** rasa (27 agentes) e **profunda (219 agentes, arquivos inteiros, adversarial em cada achado, crítico de completude).** Chão medido: 178 testes verdes, check-tokens verde, audit_casas sem FAILs. Resultado: 95 achados confirmados, 17 altos, 0 crítico. Entregável `docs/AUDITORIA_TURBO_2026-07-20.md` + painel privado. **Altos em 3 temas:** event loop único frágil (bcrypt no login, gzip da base inteira, upload antes da auth, teto de captura); dinheiro silencioso em escala (chunker de modo cego corrompe stake/odd em casa nova; XLS múltiplo processa só o 1º arquivo; goldens de VitoriaBet/Betnacional ensinam separador `+`); segurança nova (XSS armazenado por nome de casa; offboarding não revoga sessão). **Corrigido e no ar (Onda 0):** C1 XSS armazenado via nome de casa (`eb8d0ac`: `encodeURIComponent` no `faviconUrl` + `esc()` nos `data-casa`/`alt` do `index.html`); C2 XSS refletido `/extensao?v=` (`8f342c1`: `esc()` no `innerHTML` do `extensao.html`). check-tokens verde; backups `Backups/xss-c1-casa-2026-07-20/` e `Backups/xss-c2-extensao-2026-07-20/`. **Decisões do Feca:** Fatuch `doGet` público é risco contido no Fatuch (Apps Script na conta dele, sem ligação com o Sharpen), adiado e fecha na expansão. C3 (offboarding não revoga sessão de 30 dias) não patchar o auth atual; virou requisito da Fase 1 do projeto SaaS (o token checa o status do usuário). **Pendente (próximo passo, ver o relatório):** Onda 1 tirar bloqueio do event loop (bcrypt para thread, limite de upload, teto de captura); Onda 2 dinheiro silencioso (chunker de modo cego, XLS múltiplo, goldens `+` para `//`); Onda 3 Monte Carlo assíncrono. Ver [[reaudit_turbo_2026-07-20]] · `docs/AUDITORIA_TURBO_2026-07-20.md`.)_

_Anterior: 2026-07-20 (sessão 168 — **Painel "Apostas em Aberto" da tela de início lia só o Postgres.** O Fatuch viu a contradição: o card **APOSTAS** da página Apostas mostrava `Abertas:2`, mas o painel "Apostas em Aberto" da tela de início dizia "Nenhuma aposta em aberto — tudo resolvido ✓". **Causa:** duas fontes diferentes. O card lê do feed `/dashboard/data`, que para a carteira do Fatuch é a **planilha AO VIVO** (Apps Script) e traz as abertas com `resultado='ABERTA'`. O painel do início (`inicio.html:308`) só consultava `/bilhetes?extraction_state=aberta` (Postgres) — vazio, porque a base do Fatuch não está no Postgres, é planilha-viva. Detalhe que fecha o raciocínio: `repository.dashboard_rows` (feed do Postgres) **exclui** abertas (`resultado not in {W,L,V,HW,HL}: continue`), enquanto a planilha viva **inclui**; por isso o `Abertas:N` só aparecia pra quem é planilha-viva. **Fix (`ce67012`):** o painel agora **une** as abertas do feed (`rows` com `resultado==='ABERTA'`, stake normalizada via `fmt(num(...),2)`) com as do Postgres. Cada dono é sempre planilha-viva **OU** Postgres (fontes disjuntas), então a união não duplica; donos Postgres (Feca, Jonathan, etc.) ficam **idênticos** ao de antes porque o feed deles não traz linhas ABERTA (`feedAbertas=[]`). Reusou os helpers existentes (`fmt`/`num`/`moneyStake`), sem formatador novo; gate `/nova-ui` ok, `check-tokens` verde. **Ressalva:** as abertas da planilha não carregam `criado_em`, então não entram no alerta "parada há 48h+" (a planilha não carimba horário de envio). Backup `Backups/s168-inicio-painel-abertas/` (STATUS) + `Backups/inicio-painel-abertas-planilha-viva/` (inicio.html). **Residual não meu (deixado intocado por decisão do Feca):** `app/static/extensao.html` (modificado) + untracked `docs/AUDITORIA_TURBO_2026-07-20.md` e `scratch_findings.txt` — pré-existentes, fora do meu commit. Ver [[fatuch_cadastro]] · [[betano_abertas_e_upsert]].)_

_Anterior: 2026-07-20 (sessão 167 — **Custo por Conta → Postgres por dono (gêmeo do s165; fecha o trio de custos no servidor).** Continuação natural do custo tipster/geral: o **custo por conta/fornecedor** (`dash_custos_v2::<dono>`) tinha a MESMA fragilidade de localStorage (não sincroniza entre aparelhos), só que espalhado em DOIS lugares — dashboard (`gestao.js costKey/loadCusto/saveCusto`, com o `CUSTO_SEED` do Feca) e **extrator** (`index.html` `_custoKey/_lerCusto/_salvarCusto`). Detalhe unificado de brinde: o dashboard usava `window.__dono` e o extrator `window.__donoEfetivo`; no servidor os dois passam por `dono_efetivo`. **Backend:** coluna `custo_conta JSONB` em `custo_store` via `ALTER … ADD COLUMN IF NOT EXISTS` (a tabela já existia em prod desde s165) + `get_custo_conta`/`salvar_custo_conta` (upsert que toca SÓ `custo_conta`, não mexe no blob tipster/geral) + rotas **próprias** `GET`/`POST /custos/conta` (`dono_efetivo`; `existe` = dict não-vazio, pois uma linha criada só pelo import de tipster tem conta vazia). **Front dashboard (`gestao.js`):** `loadCusto` async (servidor = verdade, localStorage = cache; re-pinta `renderOvCusto` ao resolver); `saveCusto` sobe com a **mesma trava anti-semeadura-parcial** (`_custoServerBacked`/`_custoHadLegacy`); o `CUSTO_SEED` do Feca virou fallback só EM MEMÓRIA (não grava/sobe sozinho). **Front extrator (`index.html`):** `_syncCustoContaServidor()` no boot (após `_migrarCustoLegado`) puxa servidor→cache e re-pinta a faixa; `_lerCusto`/`_salvarCusto` seguem no cache síncrono (como antes), e `_salvarCusto` sobe com a trava. **Página `importar-custos.html` estendida** p/ os 3 custos num envio só: 3 seções (tipster/geral/conta), usa `/me` p/ o dono da chave da conta, e **só envia a seção que tem dado** (nunca sobrescreve o servidor com vazio). Bump `gestao.js?v=20` (o `app.js` fica no `?v=24` da s166 — não toquei). **Verificação:** `py_compile` (3 py) + `node --check` (gestao) + `vm.Script` (página + extrator) + `check-tokens` verdes; gate `/nova-ui` (custo agregado = `fmtR` inteiro via `.money`). **Convivência com a s166 (paralela):** reconciliei o git antes (working tree limpo/current; a s166 já tinha pushado kpi+XSS); **não toquei `app.js`**; commitei só os meus paths. **Escopo:** fecha o trio (tipster+geral+conta) no Postgres. **Pendente:** custo respeitar o filtro de data no P/L Líquido (achado Turbo `overview.js`) — persistência ≠ gate por data. Backup `Backups/s167-custo-conta-postgres/`. **+ Achado Turbo do P/L Líquido fechado (mesma sessão):** o Custo de Tipsters no P/L Líquido (`overview.js:14-23`) agora respeita o filtro de data — soma só os meses dentro do período (assinatura é mensal), espelhando o Custo de Contas que já filtrava via `calcCostFiltered`; **sem filtro o número é idêntico ao de antes**, só as visões filtradas corrigem o double-count (filtrar "julho" descontava jan..jul). Testado o reduce (full=1050 / só-julho=550 / vazio=0). Bump `overview.js?v=11`. Backup `Backups/s167b-pl-liquido-custo-data/`. **Trio de custos + filtro de data do P/L: fechado.** Ver [[custo_tipster_incidente_jonathan]] · [[custo_conta_isolado_por_dono]] · [[auditoria_turbo_2026-07-19]].)_

_Anterior: 2026-07-20 (sessão 166 — **Topo Histórico / Drawdown Atual: aposta-por-aposta → dia a dia.** O Feca notou no tipster LBB um topo em 18/07 (+R$ 3.125,06) com o dia 19/07 positivo e P/L total R$ 2.877,99; sobrava um "Drawdown Atual" de R$ 247,07 que não batia. **Causa:** `calcTopoDrawdown` (`app.js`) empilhava o acumulado **aposta por aposta** ordenando por `data`; mas `data` no dashboard é só o dia (`YYYY-MM-DD`, sem hora — `repository._data_iso` converte DD/MM/YYYY). Todas as apostas do dia empatam, então a ordem intradiária é a do feed, não a de resolução. Isso criava picos intradiários fantasmas: as vitórias do dia caíam antes das derrotas, o acumulado batia 3.125 no meio do 18/07 e caía; como esse pico fica acima de qualquer fechamento de dia, o 19/07 positivo não o alcança e sobra um drawdown que nunca existiu. Prova: com o último dia positivo, o topo dia-a-dia não pode ser um dia anterior. **Fix (`104f9f4`):** `calcTopoDrawdown` passou a agregar por dia, alinhado com `calcDrawdownReal` (`app.js:149`) e com o gráfico "Resultado Geral". Afeta os 3 chamadores (Por Casa, Por Esporte, drill do Tipster); cada um agora bate com seu gráfico. Varredura confirmou que nenhum outro ponto soma aposta-por-aposta (o Monte Carlo `_calcMCdrawdownRaw` embaralha o conjunto de propósito, ordem irrelevante). **Regra confirmada pelo Feca:** sem liquidação online não dá pra saber qual bet encerrou antes, então dia sempre. Bump `app.js?v=24`. `check-tokens` verde. Backup `Backups/fix-topo-drawdown-diario-s166/`. **Residual não meu (fora do meu commit):** `app/static/index.html` (endurecimento XSS no favicon/nomes de casa, não fui eu nesta sessão) + untracked `docs/AUDITORIA_TURBO_2026-07-20.md` e `scratch_findings.txt` (pré-existentes), a fechar um a um com o Feca. Ver [[topo_drawdown_dia_a_dia]] · [[solidez_kpi_proposito]].)_

> **Histórico completo das sessões 165 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
