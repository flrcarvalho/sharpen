# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-24 (sessão 186 — **Grade da Extração: ordem por resolução — em aberto no TOPO → resolvido mais recente → mais antigo.** Sistema (SharpenUp), todos os users. **Causa:** a grade ordenava por `criado_em` (ordem de captura), não pela data do bilhete → não refletia "resolvido mais recentemente". **Fix (aditivo, isolado):** novo modo `order="data_desc"` no `list_bilhetes` — EM ABERTO (`resultado` vazio) no topo, depois RESOLVIDOS por **data do EVENTO desc** (`to_date` do `DD/MM/AAAA`, guardado por regex `^\d{2}/\d{2}/\d{4}$`; vazio/malformado → fim do grupo; empate no mesmo dia = `criado_em`). A grade (`carregarGrade`, `index.html`) passa a pedir `data_desc`; os modos `asc`/`desc` e a **exportação** (`carregarTodosBilhetes`, `order=asc`, caminho separado) ficam **intactos** — a planilha segue mais-antigo-embaixo. `py_compile` OK (suíte não coleta local por mount de `StaticFiles` — ambiente, não a mudança; CI cobre). Backup `Backups/grade-ordem-data-desc/`. Ver [[ordem_feed_hora_envio]]. **Anterior: s185 abaixo.**)_

_Anterior: 2026-07-24 (sessão 185 — **Bet365: multi-passada destrava o Período (24h/48h intocados).** **Contexto:** a s184 fez o 48h fechar 20/20, mas o Período deu **20/61** — `feitos:20 · pulados:0 · falhas:0` com total 61. O Feca (com razão) cobrou que eu tinha ASSUMIDO "período = 48h" sem investigar. Sem acesso ao **Octo** (a conta não roda no Chrome → minhas ferramentas de browser não alcançam), não dava pra cravar SE era `fim` prematuro (multi-frame) OU lock de uma passada só. **Conserto robusto aos DOIS, sem apostar em qual:** o driver não trava mais depois de UMA passada (`jaVarri` → Set `jaTentados`): cada re-pedido "detalhar" detalha o LOTE que chegou depois (a lista grande carrega em lotes), tentando cada bsid 1× (término garantido). No `content.js`, o `fim` de uma passada só ENCERRA quando não sobra bilhete sem código (`semCodigo()===0`); enquanto sobrar, re-pede "detalhar" (a cada ~6s) e reabre a janela de fim. **24h/48h fecham tudo na 1ª passada → sobra 0 → encerra na hora, comportamento idêntico ao de antes** — só o Período (que sobra) ativa as passadas extras. Manifest **0.6.18 → 0.6.19**. `node --check` verde nos 2, zero `jaVarri` órfão. Backup `Backups/bet365-multipassada-periodo/`. **NÃO validado ao vivo** — o Feca recarrega 0.6.19 + Ctrl+Shift+R e roda o Período (esperado: 61/61 em passadas sucessivas; se travar, ver os logs `rota: detalhando N` por passada). **Guardrail:** parei de assumir e fiz robusto à incerteza em vez de chutar. Ver [[bet365_captura_api]] · [[feedback-isolar-mudanca-nao-quebrar]]. **Anterior: s184 abaixo.**)_

_Anterior: 2026-07-24 (sessão 184 — **Bet365: pacing+retry no ramo D0 (48h/Período) — 24h INTOCADO.** **Causa PROVADA, não chute:** o Feca clicou "Detalhes" manualmente num bilhete do 48h → o `confirmation` voltou **200 com `BR`** (código `ER7253222741F`, rota `#/HICO/BSSB/C…/D0/` — a MESMA que o fix da s183 gera) em **692ms**. As requisições do ROBÔ pra mesma rota voltam **500**. Rota certa, dado existe; o 500 é **rajada** — o token `x-net-sync-term` rotaciona por request, o disparo em sequência corre o token, o clique isolado tem token fresco = 200. D0 não é lento (692ms), só não aguenta burst (a intuição do Feca de "velocidade igual" estava certa). **Fix (só D0, ramificado pelo `PD`):** helper `navegarUm` isolado; se `isD0` (o PD tem `#D0#`), espera mais (teto 9s), folga 900ms entre bilhetes, e RETENTA 2× com "bounce" no hash (volta à lista e retorna → hashchange novo = re-fetch com token fresco, que é o que faz o clique manual dar 200). **D1 (24h) = idêntico ao de antes** (teto 8s, folga 300ms, sem retry) — nenhum bilhete D1 entra no ramo novo, então 24h não pode quebrar. Manifest **0.6.17 → 0.6.18**. `node --check` verde. Backup `Backups/bet365-d0-pacing-retry/`. **NÃO validado ao vivo** — o Feca recarrega 0.6.18 + Ctrl+Shift+R e testa 48h (esperado: 500s caem, código+data chegam; se ainda 500, ajustar folga/teto/retries). **Guardrail do Feca:** parar de mexer na extração inteira por chute e isolar por D0/D1 pra proteger o que funciona. Ver [[bet365_captura_api]]. **Anterior: s183 abaixo.**)_

_Anterior: 2026-07-24 (sessão 183 — **Bet365: 48h e Por período destravados — rota da confirmation derivada do `PD`, não mais chutada.** **Combate real do que a s182 preparou.** **Causa raiz provada pelo payload real (o Feca colou o `summary` do 48h no Network):** cada bilhete traz `PD=#HICO#BSSB#C<id>#D<ns>#` e o namespace MUDA por janela — 24h recentes = `D1`, **48h/Período = `D0`**. O `detalharPorRota` (`b3_inject.js`) chutava `/D1/` fixo → fora do 24h a confirmation voltava VAZIA (`confirmation sem BR`), e caía toda a cascata (sem código, sem data, grind de 8s×N, contagem inflada porque sem `BR` não deduplica). **Fix:** `parseSummary` captura o `PD` (novo campo `pd`), `mergeSummary` guarda, e `detalharPorRota` deriva a rota do `PD` (`"#" + pd.replace(/#/g,"/")` → `#/HICO/BSSB/C<id>/D0/`); sem `PD`, cai no `/D1/` legado. 24h segue idêntico (PD lá é `D1`). Manifest **0.6.16 → 0.6.17**. `node --check` verde + transform testada isolada. Backup `Backups/bet365-rota-pd-namespace/`. **NÃO validado ao vivo ainda** — o Feca recarrega a extensão (0.6.17) + Ctrl+Shift+R e testa 48h/Período (esperado: código+data completos como no 24h). **Pendente (Frente 2):** UI do popup — seletor de modo (24/48/período), scanner travado até escolher + aviso "expanda tudo antes de iniciar". Ver [[bet365_captura_api]]. **Anterior: s182 abaixo.**)_

> **Histórico completo das sessões 182 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
