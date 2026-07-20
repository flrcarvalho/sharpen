# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-19 (sessão 162 — **Distribuição + auto-aviso de versão da extensão SharpenUp.** Contexto: a extensão foi **REJEITADA na Chrome Web Store** (política de jogos de azar; item `jjndgojmdkgahenceejibfehbbmpckff`) e é instalada *unpacked*, que **não tem auto-update**. A distribuição era zip na mão (só o Jonathan instalou, já desatualizado). Não existe auto-update silencioso em unpacked/Octo → estratégia: **link fixo sempre-atual + aviso de quem está velho** (a extensão reporta a própria versão nos handshakes). **Fase 1 — distribuição:** `extensor/` saiu do `.dockerignore` e passou a ser copiado na imagem (`COPY extensor/` no Dockerfile) → o app o serve em runtime. 3 rotas públicas em `main.py`: `/extensao` (página on-brand de instalar/atualizar), `/extensao/versao` (versão publicada; **fonte única = `extensor/manifest.json` no deploy**), `/extensao/download` (`.zip` gerado on-the-fly da pasta → sempre a versão do deploy, sem build manual). Nova página `app/static/extensao.html` (card atualizado ✓ / desatualizado ⚠ lendo `?v=` + passo-a-passo Carregar sem compactação). **Fase 2 — detecção:** `Sessao.versao_ext` + `registrar_versao` em `captura.py`; a extensão manda a versão nos 3 handshakes (`popup.js` conectar/validar, `background.js` enviar imagem+texto); `main.py` compara (`versao_desatualizada`) e devolve `versao_atual`+`desatualizada` no conectar/validar/poll. Instalação antiga sem reporte de versão conta como desatualizada (pega o Jonathan). **Fase 3 — avisos:** faixa amarela no popup (`popup.html`/`popup.css` token `--warn`/`popup.js`) com botão **Atualizar** → abre `/extensao?v=<versão>`; footer do popup passou a ler a versão real do manifest (era `v0.3.3` hardcoded, dessincronizado); **badge "desatualizada" no extrator** (`index.html`, poll da ponte, link Atualizar). **Fase 4 (empurrar central via Octo) descartada pelo Feca.** Bug pego e corrigido: `renderAvisoVersao` rodava antes do `validar` popular a versão → faixa só apareceria no 2º render; agora re-renderiza após o validar. Regra nova: **todo mexer na extensão bumpa `manifest.json version`** (senão a detecção não vê). Manifest 0.3.8→**0.4.0** (**Feca precisa recarregar a extensão**). Verificado: `py_compile` + `node --check` verdes; TestClient nas 3 rotas (200; zip válido `sharpenup-0.4.0.zip`, 17 arquivos, manifest na raiz); `registrar_versao` (strip; vazio não apaga); comparação (antigas/0.3.8=desatualizadas, 0.4.0=ok). Backup `Backups/sessao162-auto-update-extensao/`. **Pendente:** verificação ao vivo (baixar de `sharpen.bet/extensao`, instalar, ver a faixa ao conectar versão antiga) + mandar o link fixo `sharpen.bet/extensao` pro Jonathan atualizar. Ver [[extensor_captura]] · [[dominio_sharpen_bet]].)_

_Anterior: 2026-07-19 (sessão 161 — **Abertas por casa (continuação da 159): BETesporte + Superbet.** O Feca pediu estender o "ler apostas EM ABERTO" (feito na Betano) às outras casas passivas. Mapa: **backend + export já são universais** (blindagem do UPSERT e ordenação "abertas no topo" casam por CÓDIGO, que todas têm) → falta só a extensão, casa por casa. **Regra de ouro = código/ID estável** (senão a aberta que fecha não casa e duplica). Estado: **Betano** ✅ (159); **BETesporte** ✅ (`1c301b4` — `formatTicketBE` já tratava aberta via `openBetsCount`; só alinhei o texto do status p/ o sinal inequívoco "aguardando resultado — NÃO liquidar; sem resultado", igual à Betano); **Superbet** ✅ AGORA — a amostra do Feca revelou o discriminador NA URL (`status=active`=aberta · `status=finished`=liquidada, igual à Betano `settled=`); `sb_inject` marca `__aberta` pela URL + chave `seen` por ticketId+estado; `content.js` virou `sbById` (liquidada vence aberta), ramo aberto no `formatTicket` (odd estrutural `coefficient`, `win.payoff`=ganho potencial), `roboSuperbetPassive` itera `sbById` e não corta pela janela na aba `/abertos`. **Betfair** — resolvidas ✅ **validadas ao vivo**: o dump do Feca provou que a Data vem da **resolução inclusive nas perdas** (`O/…/0001748` LOST apostado 10/07, resolvido 19/07 → Data 19/07) → **o extrato CSV virou redundante, Feca pode parar de anexar**; +2 fixes (`c02d739`): odd de múltipla perdida por **produto das pernas** (não cai mais como 'aberta') e **guard de freebet** (só exibe `stakeBonus` ≤ stake; um Each Way trouxe 10000 num stake 200). Status `PLACED` (outright não resolvido) segue "a conferir" de propósito. **Abertas** da Betfair 🔴 aguardam amostra da aba Aberta (`bf_inject` rejeita não-`SETTLED`; sem aposta aberta agora → adiado). **Bet365** ⛔ EXCLUÍDA (sem ID nem data → aberta que fecha viraria duplicata fantasma). `node --check` verde; manifest 0.3.6→**0.3.8** (**recarregar a extensão**). Backups `pre_betesporte_abertas_2026-07-19/` + `pre_superbet_abertas_2026-07-19/` + `pre_betfair_fixes_2026-07-19/`. Verificação ao vivo nas abas "Em aberto" (BETesporte + Superbet) pendente. Ver [[betano_abertas_e_upsert]] · [[extensor_captura]].)_

_Anterior: 2026-07-19 (sessão 160 — **modo turbo/CEO: +6 correções da Auditoria Turbo no ar** (uma por commit, backup + testes/gate verdes em cada; suíte segue 172 + 3 skipped do harness de DB). **(1) #14c** faxina CSS — removidos 3 blocos de componente MORTOS (uso-zero provado por grep em `app/static/dash`): `.seg-btn` "canônica" nunca adotada, família `.badge/.badge-*` de status, `.apostas-sort-*` órfãos; `check-tokens` verde, bump `components.css?v=12` — `ee8ba22`. **(2) #13** autodiagnóstico universal nas casas-robô passivas (**maior risco vivo**): antes só a Betfair diagnosticava captura zerada; Superbet/BETesporte/Betano caíam num "Nada coletado" genérico → quando a casa troca o DOM/endpoint a captura zerava em SILÊNCIO. Cada inject (`sb/be/bn_inject.js`) passou a contar `respostas` e emitir SEMPRE `hook:true`+`respostas` (heartbeat, mesmo com 0 bilhetes); `content.js` lê isso das 3 casas e mostra um **toast diferencial** (`hook NÃO carregou` / `endpoint mudou` = 0 respostas / `formato mudou-ou-conta-vazia` = respostas>0 & 0 vistos) + escala ao popup (`lastError`) só na falha inequívoca; `bn` preserva `fimOpen`/`fimSettled`+`__aberta`. Manifest 0.3.4→**0.3.5** (**Feca precisa RECARREGAR a extensão** no Octium). Backup `Backups/autodiagnostico-extensao-13-2026-07-19/` — `5b548ea`. **(3) #11** harness de camada-DB REAL: 1º teste do caminho de ESCRITA de dinheiro que o conftest stuba — `tests/test_repository_db.py` exerce `upsert_bilhetes` (insert vs update por código), isolamento por `dono` (tenancy) e as 2 blindagens aberta→resolvida, contra um Postgres de teste. `conftest.py` virou CONDICIONAL: com `TEST_DATABASE_URL` (só no CI, `postgres:16` em localhost) pula os stubs e carrega asyncpg/database reais; sem a var (dev local, ambiente do Feca) stuba como antes → os 3 pulam. **Gateado em `TEST_DATABASE_URL` (nunca `DATABASE_URL`) + trava anti-prod (recusa URL não-localhost)** — o `.env` do Feca tem o `DATABASE_URL` de prod, jamais tocado. CI ganhou serviço Postgres + step isolado (`e7a8188` + `1e66d20`). Local: 172 passed, 3 skipped; **os 3 de DB estreiam no CI** (a conferir — `gh` não instalado local). **(4) #20** fecha 3 lacunas de propagação nos masters (**aprovado**): Primeiro/Último Marcador entram como sinônimos de `Anytime` em `MASTER_APOSTAS §4`; `aposta aberta → Resultado vazio` documentada em `MASTER_OUTPUT §13.1`+`§18.8` (+ espelho no `CLAUDE.md`); `Múltiplos` entra na whitelist oficial de `MASTER_ESPORTES §7`. Nenhuma cria/renomeia categoria → não dispara checklist de casas, `audit_casas` verde — `40deee0`. **(5) #15/#16** índice **Solidez** (**aprovado**): gate de rentabilidade (yield<0 trava em "Muito Baixa" — 40% do índice era agnóstico a lucro e perdedor floreava) + separa força-do-sinal (Edge cheio exige yield ≥3%, não só significância — amostra grande tornava edge trivial "significativo") de tamanho-de-amostra; `calcSolidez` ganha param `roi` (%), os 3 callers (gestao/overview/performance) passam `calcROI(rows)`, disclaimer novo no card, bump 4 `?v=` — `1923052`. **→ REVERTIDO `9394553`** (rumo errado: o gate rebaixava tipster sólido em drawdown normal — o KPI existe pra fugir de "perdeu=ruim"; Solidez fica p/ sessão dedicada de redesenho, ver memória `solidez_kpi_proposito`). **Decisões do Feca:** #20 aplicar · #15/#16 corrigir os dois · **#5 Poly odd → junto com a Poly incremental**. **Migalhas MORTAS:** #14 domain.py **fechado** (premissa obsoleta — puras já testáveis, o #11 destravou o teste de DB sem o split; mover 550 linhas do core de dinheiro = risco por ganho cosmético); #18 backtest temporal → frente de inteligência de tipster; #21 golden bilhetes → precisa prints de amostra do Feca (regressão roda a IA, não é teste unitário); #25 Backups → convenção no `CLAUDE.md` invariante #4 (não copiar HISTORICO/dirs; retenção ~sessões/90d). #19 separador ✅ FEITO `46abe69` (` // ` é o único separador; Lottu/Jogo de Ouro traduzem `&`→` // `; bilhete cru mantém `&` como input). **Backlog restante = só 3 sessões próprias:** (1) **Custo tipster → Postgres** (Jonathan, amanhã); (2) **Sessão só-Poly** (incremental + #5 odd + `_portfolio`; precisa a carteira do Feca — probe do `conditionId`, fixtures, paridade ao vivo; não subir sem paridade); (3) **Sessão só-Solidez** (redesenho do KPI — robustez do histórico, não lucro da janela). Ver [[custo_tipster_incidente_jonathan]] (Jonathan amanhã) · `docs/AUDITORIA_TURBO_2026-07-19.md` (tracker atualizado).)_

_Anterior: 2026-07-19 (sessão 159 — **SharpenUp/Betano: robô passou a LER as apostas EM ABERTO** (antes só liquidadas). **Causa raiz:** `bn_inject.js` filtrava `settled=true` e descartava a aba "Em aberto"; como o robô re-processa a memória acumulada, trocar de aba só re-enviava as liquidadas. **Fix em 4 arquivos (backup `Backups/pre_betano_abertas_2026-07-19/`):** (1) `extensor/bn_inject.js` — captura as DUAS listas (settled=true→liquidada · senão→aberta), marca cada bilhete `__aberta` e sinaliza fim POR LISTA (`fimOpen`/`fimSettled`). (2) `extensor/content.js` — acumulador virou `bnById` (1 por BetId, **liquidada vence aberta**); `formatTicketBN` ganhou ramo ABERTA (Status "em aberto — NÃO liquidar; sem resultado", odd estrutural, `Return`=potencial); `roboBetanoPassive` itera `bnById`, usa o fim da **aba ativa** (`/open` na URL) e **não corta pela janela de dias na aba abertas**. Envia abertas+liquidadas carregadas numa rodada (UPSERT por código nunca duplica). (3) `app/repository.py` — UPSERT blindado: **(a)** resultado VAZIO nunca sobrescreve resolvido (uma re-leitura tardia de "aberta" não rebaixa a linha já fechada); **(b)** só quando a linha ESTAVA `'aberta'` e agora resolve os campos financeiros (odd/data/stake) são refrescados com a verdade da liquidação (vitória com boost passa a odd=Retorno÷Stake) — linha já resolvida fica intacta; assinatura por código não usa esses campos → match não quebra. Mesma lógica no fallback de `UniqueViolationError`. **(4)** `app/static/index.html` — `exportar()` ordena **abertas (sem resultado) acima das resolvidas** (sort estável). Fluxo confirmado: aberta sobe sem resultado → `estado_extracao`→`'aberta'` (não rejeitada em `validar_linhas`, `main.py:1513`) → bilhete fecha → mesmo BetId=mesma assinatura → UPSERT preenche resultado + refresca odd. `py_compile` + `node --check` verdes. Manifest 0.3.3→0.3.4 (**Feca precisa recarregar a extensão** no Octium). Verificação AO VIVO na Betano pendente (rodar nas duas abas). Ver [[extensor_captura]] · [[betano_lentidao_chunker]] · [[extracao_sem_odd_flag]] · [[dedup_gap_sem_codigo_reextracao]] · [[ordem_feed_hora_envio]].)_

> **Histórico completo das sessões 158 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
