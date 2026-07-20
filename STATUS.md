# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-20 (sessão 167 — **Custo por Conta → Postgres por dono (gêmeo do s165; fecha o trio de custos no servidor).** Continuação natural do custo tipster/geral: o **custo por conta/fornecedor** (`dash_custos_v2::<dono>`) tinha a MESMA fragilidade de localStorage (não sincroniza entre aparelhos), só que espalhado em DOIS lugares — dashboard (`gestao.js costKey/loadCusto/saveCusto`, com o `CUSTO_SEED` do Feca) e **extrator** (`index.html` `_custoKey/_lerCusto/_salvarCusto`). Detalhe unificado de brinde: o dashboard usava `window.__dono` e o extrator `window.__donoEfetivo`; no servidor os dois passam por `dono_efetivo`. **Backend:** coluna `custo_conta JSONB` em `custo_store` via `ALTER … ADD COLUMN IF NOT EXISTS` (a tabela já existia em prod desde s165) + `get_custo_conta`/`salvar_custo_conta` (upsert que toca SÓ `custo_conta`, não mexe no blob tipster/geral) + rotas **próprias** `GET`/`POST /custos/conta` (`dono_efetivo`; `existe` = dict não-vazio, pois uma linha criada só pelo import de tipster tem conta vazia). **Front dashboard (`gestao.js`):** `loadCusto` async (servidor = verdade, localStorage = cache; re-pinta `renderOvCusto` ao resolver); `saveCusto` sobe com a **mesma trava anti-semeadura-parcial** (`_custoServerBacked`/`_custoHadLegacy`); o `CUSTO_SEED` do Feca virou fallback só EM MEMÓRIA (não grava/sobe sozinho). **Front extrator (`index.html`):** `_syncCustoContaServidor()` no boot (após `_migrarCustoLegado`) puxa servidor→cache e re-pinta a faixa; `_lerCusto`/`_salvarCusto` seguem no cache síncrono (como antes), e `_salvarCusto` sobe com a trava. **Página `importar-custos.html` estendida** p/ os 3 custos num envio só: 3 seções (tipster/geral/conta), usa `/me` p/ o dono da chave da conta, e **só envia a seção que tem dado** (nunca sobrescreve o servidor com vazio). Bump `gestao.js?v=20` (o `app.js` fica no `?v=24` da s166 — não toquei). **Verificação:** `py_compile` (3 py) + `node --check` (gestao) + `vm.Script` (página + extrator) + `check-tokens` verdes; gate `/nova-ui` (custo agregado = `fmtR` inteiro via `.money`). **Convivência com a s166 (paralela):** reconciliei o git antes (working tree limpo/current; a s166 já tinha pushado kpi+XSS); **não toquei `app.js`**; commitei só os meus paths. **Escopo:** fecha o trio (tipster+geral+conta) no Postgres. **Pendente:** custo respeitar o filtro de data no P/L Líquido (achado Turbo `overview.js`) — persistência ≠ gate por data. Backup `Backups/s167-custo-conta-postgres/`. **+ Achado Turbo do P/L Líquido fechado (mesma sessão):** o Custo de Tipsters no P/L Líquido (`overview.js:14-23`) agora respeita o filtro de data — soma só os meses dentro do período (assinatura é mensal), espelhando o Custo de Contas que já filtrava via `calcCostFiltered`; **sem filtro o número é idêntico ao de antes**, só as visões filtradas corrigem o double-count (filtrar "julho" descontava jan..jul). Testado o reduce (full=1050 / só-julho=550 / vazio=0). Bump `overview.js?v=11`. Backup `Backups/s167b-pl-liquido-custo-data/`. **Trio de custos + filtro de data do P/L: fechado.** Ver [[custo_tipster_incidente_jonathan]] · [[custo_conta_isolado_por_dono]] · [[auditoria_turbo_2026-07-19]].)_

_Anterior: 2026-07-20 (sessão 166 — **Topo Histórico / Drawdown Atual: aposta-por-aposta → dia a dia.** O Feca notou no tipster LBB um topo em 18/07 (+R$ 3.125,06) com o dia 19/07 positivo e P/L total R$ 2.877,99; sobrava um "Drawdown Atual" de R$ 247,07 que não batia. **Causa:** `calcTopoDrawdown` (`app.js`) empilhava o acumulado **aposta por aposta** ordenando por `data`; mas `data` no dashboard é só o dia (`YYYY-MM-DD`, sem hora — `repository._data_iso` converte DD/MM/YYYY). Todas as apostas do dia empatam, então a ordem intradiária é a do feed, não a de resolução. Isso criava picos intradiários fantasmas: as vitórias do dia caíam antes das derrotas, o acumulado batia 3.125 no meio do 18/07 e caía; como esse pico fica acima de qualquer fechamento de dia, o 19/07 positivo não o alcança e sobra um drawdown que nunca existiu. Prova: com o último dia positivo, o topo dia-a-dia não pode ser um dia anterior. **Fix (`104f9f4`):** `calcTopoDrawdown` passou a agregar por dia, alinhado com `calcDrawdownReal` (`app.js:149`) e com o gráfico "Resultado Geral". Afeta os 3 chamadores (Por Casa, Por Esporte, drill do Tipster); cada um agora bate com seu gráfico. Varredura confirmou que nenhum outro ponto soma aposta-por-aposta (o Monte Carlo `_calcMCdrawdownRaw` embaralha o conjunto de propósito, ordem irrelevante). **Regra confirmada pelo Feca:** sem liquidação online não dá pra saber qual bet encerrou antes, então dia sempre. Bump `app.js?v=24`. `check-tokens` verde. Backup `Backups/fix-topo-drawdown-diario-s166/`. **Residual não meu (fora do meu commit):** `app/static/index.html` (endurecimento XSS no favicon/nomes de casa, não fui eu nesta sessão) + untracked `docs/AUDITORIA_TURBO_2026-07-20.md` e `scratch_findings.txt` (pré-existentes), a fechar um a um com o Feca. Ver [[topo_drawdown_dia_a_dia]] · [[solidez_kpi_proposito]].)_

_Anterior: 2026-07-20 (sessão 165 — **Custo por Tipster + Custos Gerais: localStorage global → Postgres por dono.** Motivo: **incidente Jonathan** — preencheu os custos no PC do trabalho e, ao abrir noutra máquina, viu tudo zerado menos um tipster. Causa (achado da Turbo confirmado): `CT_KEY='custoTipsterData'`/`CG_KEY='custoGeralData'` eram chaves de localStorage **globais, sem dono** (ao contrário de `costKey()`), e localStorage **não sincroniza entre aparelhos nem tem backup** → o custo digitado num PC nunca chegava a outro. **Feito (backend):** tabela `custo_store (dono PK, custo_tipster JSONB, custo_geral JSONB)` no `SCHEMA_SQL` (idempotente, cria no boot); `get_custo_store`/`salvar_custo_store` no `repository.py` (espelham `casas_meta`; JSONB→str via `json.loads`, escrita `::jsonb`); rotas `GET`/`POST /custos/store` com `Depends(dono_efetivo)` no `main.py`. **Front:** `ctLoad()` virou async (servidor = fonte de verdade, localStorage = cache/paint instantâneo); `ctSave()` ganhou **trava anti-semeadura-parcial** (`_ctServerBacked`/`_ctHadLegacy`): servidor vazio **E** com custo legado no navegador → **NÃO cria o registro sozinho** (só a página de importação semeia, do PC certo — regra do Feca); usuário novo sem legado grava normal no 1º save. `renderCustoTipster` deixou de chamar `ctLoad` (carga separada no dispatcher da aba). **Página avulsa** `app/static/dash/importar-custos.html` (servida em `/dashboard/importar-custos.html`, mesma origem → lê o MESMO localStorage): prévia (nº tipsters, nº custos gerais, **total `fmtR`**) + lista p/ conferir + botão **Enviar ao servidor**; trata cópia errada / já-existe-no-servidor / sem-login. **Fluxo Jonathan:** abrir a página **no PC do trabalho** → conferir a prévia (≈12 tipsters, R$ 1.520) → Enviar → passa a aparecer em qualquer aparelho. Bump `gestao.js?v=19` + `app.js?v=23`. **Escopo:** só CT/CG (o que sumiu); o custo **por-conta** (`dash_custos_v2` em `gestao.js costKey`) tem a MESMA fragilidade → **próximo passo**. **Verificação:** `py_compile` (3 py) + `node --check` (bundle) + `vm.Script` (JS da página) verdes; `check-tokens` verde; gate `/nova-ui` (custo agregado = `fmtR` inteiro via `.money`, espelho de `app.js:13,15`). Headless não rodou (limitação `file://` no ambiente) → **e2e real = clique do Jonathan** (acompanhar no deploy). Rodou **em paralelo à sessão de auditoria** (untracked `docs/AUDITORIA_TURBO_2026-07-20.md` + `scratch_findings.txt` **não são meus** — ficam fora do meu commit). Backup `Backups/s165-custos-postgres/`. Ver [[custo_conta_isolado_por_dono]] · [[auditoria_turbo_2026-07-19]].)_

_Anterior: 2026-07-20 (sessão 164 — **Reconciliação da Auditoria Turbo + solos de baixo risco.** Rodou em paralelo ao terminal do SharpenUp (sessões 161-163). **Susto resolvido:** o Feca achou que um terminal fechou e perdeu trabalho. Nada perdido: todo commit estava salvo e pushado, fechar a janela não desfaz commit. **Reconciliação dos 186 achados de `docs/auditoria_turbo/findings.json`:** 4 agentes verificaram cada achado acionável contra o código vivo. Números reais: 35 fechados, 47 positivos (elogio do auditor, sem ação), 2 adiados, 1 placeholder, **101 pendências reais**. Zero crítico, zero alto. O "175 pendentes" inicial era teto ilusório (positivos somados a já-feitos rotulados errado). Painel filtrável gerado como Artifact privado (feito x pendente por severidade/esforço/área). **Fechados nesta sessão (11):** migalhas de doc `#138`/`#143`/`#144`/`#148`/`#169` (`6cbb9ed`); solos de doc `#145`/`#146`/`#147` (`fa641f4`); solos de UI `#60`/`#61` (`3cfc12a`). **#60:** `tc()` no `app.js`, dark `#505060` para `#5E6775` (valor de `--ink-mute`, label de eixo apagado mas legível). **#61:** eixo `y1` (Win Rate) ganhou `min:0`/`max:100` no `overview.js` (auto-scale exagerava variação pequena). Bump `overview.js?v=10` + `app.js?v=22`. Passou pelo gate `/nova-ui`, `check-tokens` verde, `node --check` ok. Backups `Backups/audit-migalhas-doc-2026-07-19/` e `Backups/audit-solos-2026-07-20/`. **Pendente:** canon `#126`/`#127` (masters, precisam OK do Feca antes de mexer); dinheiro/dedup `#1`/`#44`/`#112`/`#113`/`#114` (propor diff, não blastar); parkado `#31` Solidez e `#150` Poly ativas (sessões dedicadas). **Próximo passo:** retomar pelas 9 médias rápidas restantes ou preparar o diff dos 2 canon. Ver [[auditoria_turbo_2026-07-19]] · `docs/AUDITORIA_TURBO_2026-07-19.md`.)_

_Anterior: 2026-07-20 (sessão 163 — **CI verde de novo: harness de DB estava quebrando em TODO push.** Sintoma: o Feca recebendo centenas de emails "Run failed: CI - main" do GitHub — **um por commit**. O CI (`.github/workflows/ci.yml`) falhava desde que o harness de camada-DB entrou (sessão 160, #11) — **nunca tinha passado**; fecha o "a conferir" que ficou lá (`gh` não rodava local). Só o passo **"Harness de camada-DB (Postgres)"** quebrava; os outros 5 sempre verdes. **Causa raiz:** `tests/test_repository_db.py` chamava `asyncio.run(body())` por teste → um event loop NOVO a cada teste; mas `database.get_pool()` cacheia o pool asyncpg num global de módulo, criado no loop do 1º teste → do 2º em diante o pool fica preso a um loop já fechado → `got Future attached to a different loop` (padrão `.FFF`). **Tentativa 1 errada (`9ab4f6e`):** descartar o pool por teste com `terminate()` — também falha (`Event loop is closed`, `.E.E`): `terminate()` agenda `call_soon` no loop antigo. **Fix real (`5b516e4`):** UM `asyncio.new_event_loop()` persistente no módulo + helper `_run(coro)`; os 4 testes usam `_run(body())`; fixture `scope="module"` fecha o pool DENTRO desse loop no teardown. Só mexe no teste — `database.py` de produção intocado (lá o loop é único e de vida longa, cache correto). **CI confirmado VERDE ao vivo** via `gh run watch` (run `29715737275` → `success`). Local não reproduz (sem Postgres; pula sem `TEST_DATABASE_URL`); acompanhei a run real pra não chutar. Backup do arquivo em `Backups/ci-harness-db-loop-fix/`. Aviso residual "Node.js 20 deprecated" é benigno (não falha). **Pendente (limpeza manual do Feca):** os ~23k emails antigos de falha já na caixa — filtrar no Gmail por `from:notifications@github.com "Run failed"` e arquivar em massa, ou silenciar as notificações de Actions do repo. Ver [[ci_harness_db_loop_unico]] · [[harness_db_ci]].)_

> **Histórico completo das sessões 162 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
