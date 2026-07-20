# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-20 (sessão 165 — **Custo por Tipster + Custos Gerais: localStorage global → Postgres por dono.** Motivo: **incidente Jonathan** — preencheu os custos no PC do trabalho e, ao abrir noutra máquina, viu tudo zerado menos um tipster. Causa (achado da Turbo confirmado): `CT_KEY='custoTipsterData'`/`CG_KEY='custoGeralData'` eram chaves de localStorage **globais, sem dono** (ao contrário de `costKey()`), e localStorage **não sincroniza entre aparelhos nem tem backup** → o custo digitado num PC nunca chegava a outro. **Feito (backend):** tabela `custo_store (dono PK, custo_tipster JSONB, custo_geral JSONB)` no `SCHEMA_SQL` (idempotente, cria no boot); `get_custo_store`/`salvar_custo_store` no `repository.py` (espelham `casas_meta`; JSONB→str via `json.loads`, escrita `::jsonb`); rotas `GET`/`POST /custos/store` com `Depends(dono_efetivo)` no `main.py`. **Front:** `ctLoad()` virou async (servidor = fonte de verdade, localStorage = cache/paint instantâneo); `ctSave()` ganhou **trava anti-semeadura-parcial** (`_ctServerBacked`/`_ctHadLegacy`): servidor vazio **E** com custo legado no navegador → **NÃO cria o registro sozinho** (só a página de importação semeia, do PC certo — regra do Feca); usuário novo sem legado grava normal no 1º save. `renderCustoTipster` deixou de chamar `ctLoad` (carga separada no dispatcher da aba). **Página avulsa** `app/static/dash/importar-custos.html` (servida em `/dashboard/importar-custos.html`, mesma origem → lê o MESMO localStorage): prévia (nº tipsters, nº custos gerais, **total `fmtR`**) + lista p/ conferir + botão **Enviar ao servidor**; trata cópia errada / já-existe-no-servidor / sem-login. **Fluxo Jonathan:** abrir a página **no PC do trabalho** → conferir a prévia (≈12 tipsters, R$ 1.520) → Enviar → passa a aparecer em qualquer aparelho. Bump `gestao.js?v=19` + `app.js?v=23`. **Escopo:** só CT/CG (o que sumiu); o custo **por-conta** (`dash_custos_v2` em `gestao.js costKey`) tem a MESMA fragilidade → **próximo passo**. **Verificação:** `py_compile` (3 py) + `node --check` (bundle) + `vm.Script` (JS da página) verdes; `check-tokens` verde; gate `/nova-ui` (custo agregado = `fmtR` inteiro via `.money`, espelho de `app.js:13,15`). Headless não rodou (limitação `file://` no ambiente) → **e2e real = clique do Jonathan** (acompanhar no deploy). Rodou **em paralelo à sessão de auditoria** (untracked `docs/AUDITORIA_TURBO_2026-07-20.md` + `scratch_findings.txt` **não são meus** — ficam fora do meu commit). Backup `Backups/s165-custos-postgres/`. Ver [[custo_conta_isolado_por_dono]] · [[auditoria_turbo_2026-07-19]].)_

_Anterior: 2026-07-20 (sessão 164 — **Reconciliação da Auditoria Turbo + solos de baixo risco.** Rodou em paralelo ao terminal do SharpenUp (sessões 161-163). **Susto resolvido:** o Feca achou que um terminal fechou e perdeu trabalho. Nada perdido: todo commit estava salvo e pushado, fechar a janela não desfaz commit. **Reconciliação dos 186 achados de `docs/auditoria_turbo/findings.json`:** 4 agentes verificaram cada achado acionável contra o código vivo. Números reais: 35 fechados, 47 positivos (elogio do auditor, sem ação), 2 adiados, 1 placeholder, **101 pendências reais**. Zero crítico, zero alto. O "175 pendentes" inicial era teto ilusório (positivos somados a já-feitos rotulados errado). Painel filtrável gerado como Artifact privado (feito x pendente por severidade/esforço/área). **Fechados nesta sessão (11):** migalhas de doc `#138`/`#143`/`#144`/`#148`/`#169` (`6cbb9ed`); solos de doc `#145`/`#146`/`#147` (`fa641f4`); solos de UI `#60`/`#61` (`3cfc12a`). **#60:** `tc()` no `app.js`, dark `#505060` para `#5E6775` (valor de `--ink-mute`, label de eixo apagado mas legível). **#61:** eixo `y1` (Win Rate) ganhou `min:0`/`max:100` no `overview.js` (auto-scale exagerava variação pequena). Bump `overview.js?v=10` + `app.js?v=22`. Passou pelo gate `/nova-ui`, `check-tokens` verde, `node --check` ok. Backups `Backups/audit-migalhas-doc-2026-07-19/` e `Backups/audit-solos-2026-07-20/`. **Pendente:** canon `#126`/`#127` (masters, precisam OK do Feca antes de mexer); dinheiro/dedup `#1`/`#44`/`#112`/`#113`/`#114` (propor diff, não blastar); parkado `#31` Solidez e `#150` Poly ativas (sessões dedicadas). **Próximo passo:** retomar pelas 9 médias rápidas restantes ou preparar o diff dos 2 canon. Ver [[auditoria_turbo_2026-07-19]] · `docs/AUDITORIA_TURBO_2026-07-19.md`.)_

_Anterior: 2026-07-20 (sessão 163 — **CI verde de novo: harness de DB estava quebrando em TODO push.** Sintoma: o Feca recebendo centenas de emails "Run failed: CI - main" do GitHub — **um por commit**. O CI (`.github/workflows/ci.yml`) falhava desde que o harness de camada-DB entrou (sessão 160, #11) — **nunca tinha passado**; fecha o "a conferir" que ficou lá (`gh` não rodava local). Só o passo **"Harness de camada-DB (Postgres)"** quebrava; os outros 5 sempre verdes. **Causa raiz:** `tests/test_repository_db.py` chamava `asyncio.run(body())` por teste → um event loop NOVO a cada teste; mas `database.get_pool()` cacheia o pool asyncpg num global de módulo, criado no loop do 1º teste → do 2º em diante o pool fica preso a um loop já fechado → `got Future attached to a different loop` (padrão `.FFF`). **Tentativa 1 errada (`9ab4f6e`):** descartar o pool por teste com `terminate()` — também falha (`Event loop is closed`, `.E.E`): `terminate()` agenda `call_soon` no loop antigo. **Fix real (`5b516e4`):** UM `asyncio.new_event_loop()` persistente no módulo + helper `_run(coro)`; os 4 testes usam `_run(body())`; fixture `scope="module"` fecha o pool DENTRO desse loop no teardown. Só mexe no teste — `database.py` de produção intocado (lá o loop é único e de vida longa, cache correto). **CI confirmado VERDE ao vivo** via `gh run watch` (run `29715737275` → `success`). Local não reproduz (sem Postgres; pula sem `TEST_DATABASE_URL`); acompanhei a run real pra não chutar. Backup do arquivo em `Backups/ci-harness-db-loop-fix/`. Aviso residual "Node.js 20 deprecated" é benigno (não falha). **Pendente (limpeza manual do Feca):** os ~23k emails antigos de falha já na caixa — filtrar no Gmail por `from:notifications@github.com "Run failed"` e arquivar em massa, ou silenciar as notificações de Actions do repo. Ver [[ci_harness_db_loop_unico]] · [[harness_db_ci]].)_

_Anterior: 2026-07-19 (sessão 162 — **Distribuição + auto-aviso de versão da extensão SharpenUp.** Contexto: a extensão foi **REJEITADA na Chrome Web Store** (política de jogos de azar; item `jjndgojmdkgahenceejibfehbbmpckff`) e é instalada *unpacked*, que **não tem auto-update**. A distribuição era zip na mão (só o Jonathan instalou, já desatualizado). Não existe auto-update silencioso em unpacked/Octo → estratégia: **link fixo sempre-atual + aviso de quem está velho** (a extensão reporta a própria versão nos handshakes). **Fase 1 — distribuição:** `extensor/` saiu do `.dockerignore` e passou a ser copiado na imagem (`COPY extensor/` no Dockerfile) → o app o serve em runtime. 3 rotas públicas em `main.py`: `/extensao` (página on-brand de instalar/atualizar), `/extensao/versao` (versão publicada; **fonte única = `extensor/manifest.json` no deploy**), `/extensao/download` (`.zip` gerado on-the-fly da pasta → sempre a versão do deploy, sem build manual). Nova página `app/static/extensao.html` (card atualizado ✓ / desatualizado ⚠ lendo `?v=` + passo-a-passo Carregar sem compactação). **Fase 2 — detecção:** `Sessao.versao_ext` + `registrar_versao` em `captura.py`; a extensão manda a versão nos 3 handshakes (`popup.js` conectar/validar, `background.js` enviar imagem+texto); `main.py` compara (`versao_desatualizada`) e devolve `versao_atual`+`desatualizada` no conectar/validar/poll. Instalação antiga sem reporte de versão conta como desatualizada (pega o Jonathan). **Fase 3 — avisos:** faixa amarela no popup (`popup.html`/`popup.css` token `--warn`/`popup.js`) com botão **Atualizar** → abre `/extensao?v=<versão>`; footer do popup passou a ler a versão real do manifest (era `v0.3.3` hardcoded, dessincronizado); **badge "desatualizada" no extrator** (`index.html`, poll da ponte, link Atualizar). **Fase 4 (empurrar central via Octo) descartada pelo Feca.** Bug pego e corrigido: `renderAvisoVersao` rodava antes do `validar` popular a versão → faixa só apareceria no 2º render; agora re-renderiza após o validar. Regra nova: **todo mexer na extensão bumpa `manifest.json version`** (senão a detecção não vê). Manifest 0.3.8→**0.4.0** (**Feca precisa recarregar a extensão**). Verificado: `py_compile` + `node --check` verdes; TestClient nas 3 rotas (200; zip válido `sharpenup-0.4.0.zip`, 17 arquivos, manifest na raiz); `registrar_versao` (strip; vazio não apaga); comparação (antigas/0.3.8=desatualizadas, 0.4.0=ok). Backup `Backups/sessao162-auto-update-extensao/`. **No ar e validado ao vivo:** as 3 rotas respondem 200 em `www.sharpen.bet` (`/extensao/versao`=0.4.0, download `sharpenup-0.4.0.zip`). **Atenção ao domínio:** o apex `sharpen.bet/extensao` (sem `www`) dá **404** — o forwarding da GoDaddy não preserva o path; o link certo é **`www.sharpen.bet/extensao`** (a extensão já fala com o `www` via `config.js`, então popup/extrator montam a URL certa sozinhos). **Pendente:** instalar a 0.4.0 e ver a faixa ao conectar versão antiga + mandar `www.sharpen.bet/extensao` pro Jonathan atualizar. Ver [[extensor_captura]] · [[dominio_sharpen_bet]].)_

_Anterior: 2026-07-19 (sessão 161 — **Abertas por casa (continuação da 159): BETesporte + Superbet.** O Feca pediu estender o "ler apostas EM ABERTO" (feito na Betano) às outras casas passivas. Mapa: **backend + export já são universais** (blindagem do UPSERT e ordenação "abertas no topo" casam por CÓDIGO, que todas têm) → falta só a extensão, casa por casa. **Regra de ouro = código/ID estável** (senão a aberta que fecha não casa e duplica). Estado: **Betano** ✅ (159); **BETesporte** ✅ (`1c301b4` — `formatTicketBE` já tratava aberta via `openBetsCount`; só alinhei o texto do status p/ o sinal inequívoco "aguardando resultado — NÃO liquidar; sem resultado", igual à Betano); **Superbet** ✅ AGORA — a amostra do Feca revelou o discriminador NA URL (`status=active`=aberta · `status=finished`=liquidada, igual à Betano `settled=`); `sb_inject` marca `__aberta` pela URL + chave `seen` por ticketId+estado; `content.js` virou `sbById` (liquidada vence aberta), ramo aberto no `formatTicket` (odd estrutural `coefficient`, `win.payoff`=ganho potencial), `roboSuperbetPassive` itera `sbById` e não corta pela janela na aba `/abertos`. **Betfair** — resolvidas ✅ **validadas ao vivo**: o dump do Feca provou que a Data vem da **resolução inclusive nas perdas** (`O/…/0001748` LOST apostado 10/07, resolvido 19/07 → Data 19/07) → **o extrato CSV virou redundante, Feca pode parar de anexar**; +2 fixes (`c02d739`): odd de múltipla perdida por **produto das pernas** (não cai mais como 'aberta') e **guard de freebet** (só exibe `stakeBonus` ≤ stake; um Each Way trouxe 10000 num stake 200). Status `PLACED` (outright não resolvido) segue "a conferir" de propósito. **Abertas** da Betfair 🔴 aguardam amostra da aba Aberta (`bf_inject` rejeita não-`SETTLED`; sem aposta aberta agora → adiado). **Bet365** ⛔ EXCLUÍDA (sem ID nem data → aberta que fecha viraria duplicata fantasma). `node --check` verde; manifest 0.3.6→**0.3.8** (**recarregar a extensão**). Backups `pre_betesporte_abertas_2026-07-19/` + `pre_superbet_abertas_2026-07-19/` + `pre_betfair_fixes_2026-07-19/`. Verificação ao vivo nas abas "Em aberto" (BETesporte + Superbet) pendente. Ver [[betano_abertas_e_upsert]] · [[extensor_captura]].)_

> **Histórico completo das sessões 160 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
