# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-08-02 (sessão 233 — **Multiusuário Fase 1 / Deploy A: tabela `usuarios` criada e semeada no Postgres — comportamento 100% inalterado (o auth segue lendo os dicts de `auth.py`).** Primeiro passo executado do `docs/PLANO_MULTIUSUARIO_2026.md` (fundação do cadastro self-service e do login Google/Telegram, Fases 2–3). `SCHEMA_SQL` ganha `CREATE TABLE IF NOT EXISTS usuarios`: `username` = coluna `dono` (sem FK, integridade lógica), `senha_hash` NULL = conta só-social, `status ativo/pendente/suspenso` (implementa o "aberto com aprovação" e, no Deploy B, a revogação de sessão do C3 da auditoria), `role admin/user`, `parent_owner` (substituirá `OPERADORES`), `planilha_url` (substituirá `PLANILHAS_AO_VIVO`), `google_sub`/`telegram_id` já criados para a Fase 3 (evita 2ª migração). Seed idempotente `database.seed_usuarios()` chamado no lifespan após `init_db()` — `ON CONFLICT (username) DO NOTHING`, e falha do seed **não derruba o boot** (nesta fase nada lê a tabela; o checkpoint pega). A montagem das linhas é **pura** em `auth.linhas_seed_usuarios()` (12 usuários `status='ativo'`, Feca único `admin`, Lava→Feca · Primo→Diogo · LavaFatuch→Fatuch, solos com `parent_owner` NULL — inclusive `LavaPessoal`, hash/planilha vazios → NULL) — testável sem banco, porque o conftest stuba o módulo `database` (o stub ganhou `seed_usuarios`, senão todo teste que importa `main` quebrava no import). **Gates:** `pytest` **284 passed** (novo `tests/test_seed_usuarios.py`, 6 testes puros travando o contrato das 6 colunas) · `py_compile` OK. Backup `Backups/multiusuario-fase1-deployA/`. **PENDENTE (checkpoint obrigatório antes do Deploy B):** após o deploy, inspecionar a tabela em prod (read-only) e conferir os 12 usuários (hashes de 60 chars, parent_owner, planilha do LavaFatuch); só então virar a chave — auth lendo cache em memória lastreado no banco (`§1.2`/`Deploy B` do plano). **Anterior: s232 abaixo.**)_

_Anterior: 2026-08-02 (sessão 232 — **`eSoccer` vira esporte próprio nos MASTERs (espelho do eBasket) + chip nos 3 mapas de UI. Backfill da base fica pontual (§5).** Motivo: os bilhetes de futebol virtual da Bet365 (liga `eSoccer LBB`, confronto com handle de gamer — `Germany (vladl3n) v Morocco (hrk)`) caíam como `Futebol`, e 2–3 como `eBasket` — a única regra de "handle entre parênteses" que existia era a do eBasket, então a IA via o handle e ignorava que o mercado era Gols. Aplicado: `MASTER_ESPORTES` ganha seção `eSoccer` (valor oficial + sinônimos; **Regra Crítica — Futebol vs eSoccer** com tabela de sinais: handle > liga `eSoccer`/`LBB`/`Battle`/`GT Leagues` > duração `8 mins play` > linha de gols ~4.5–9.5; **"o esporte da skin decide entre os virtuais"**: clube/seleção de futebol → eSoccer, NBA → eBasket — nota espelho também no bloco do eBasket), nota "Futebol é o real" na seção Futebol, exceção de capitalização agora `eBasket` **e** `eSoccer`, §4 exemplos válidos/inválidos, validação §8 itens 18–20; `MASTER_APOSTAS §6` bloco eSoccer (mesma taxonomia do Futebol; linha alta 5.5/6.5/8.5 segue `Gols`, nunca `Pontos`; nunca `E-Sports Props`) + §9 item 20 estendido e item 23 novo; `MASTER_DESCRICAO §13.5` (handle preservado no confronto, mesma Regra Crítica do §13.3) + validação item 12; comentário do `_CL_B3` no `content.js` (CL=1 segue âncora `Futebol` — quem emite `eSoccer` é a IA); alias `eSoccer → ⚽ futebol` nos **3 mapas** `SPORT_KEY` (`index.html` · `dash/assets/js/data.js` com bump `?v=10→11` · `inicio.html`). Gate `/nova-ui` executado (sem R$; chip e emoji reusados, zero formatador/cor nova). **Gates:** harness 7 casos / 151 bilhetes verde · `check-tokens` OK · `vm.Script` nos scripts inline OK · `node --check` data.js OK · golden_set sem eSoccer (nenhum esperado a re-gravar). **NÃO feito de propósito: o backfill dos bilhetes já gravados** (esporte congela no UPSERT para origem IA, então recaptura não corrige) — os 5 problemas pontuais estão listados no topo do §5. Backup `Backups/esoccer-esporte-novo/`. **Anterior: s231 abaixo.**)_

_Anterior: 2026-08-02 (sessão 231 — **De-para da 1ª captura BetNacional pelo robô: 63 bilhetes antigos (print/import) eliminados, tipsters preservados nos novos, badge NEW temporário na página de Apostas.** A 1ª rodada do robô da s227/s228 subiu **76 bilhetes** (códigos reais `NXBNAC…`, 02/07 → 01/08) que **não colidem** com o legado — o legado usava código sintético `BN-…` (e 35 eram `import` da conta `Marsella [Eu]`), então a dedup por assinatura nunca casaria. De-para por **stake+odd+data** (ordem do Feca: descrição legada era resumida e não bate): 46 casaram exato; +17 num 2º passe com **tolerância de data** (a extração antiga gravava a data até 4 dias antes da API — validado 1 a 1 por sobreposição de nomes na descrição). Achados no caminho: o legado tinha **1 bilhete duplicado** (Mbappé 1+ chutes, extraído 2×, os dois deletados) e 2 pares 106×2,20 do mesmo dia desambiguados por descrição. Executado em transação única: **62 tipsters copiados** (antigo → novo, `origem_tipster='humano'`; sobrevive a recapturas — o UPSERT só sobrescreve tipster com valor real), **1 resultado V** copiado para o novo que a API vê aberto (`extraction_state` derivado por `estado_extracao`), **63 antigos deletados** com snapshot `DELETE…RETURNING to_jsonb` em `Backups/betnacional-depara-sharpenup-2026-08-02/` (+ `plano_depara.json`). Base Betnacional do Feca: 228 → **165** (76 robô + 89 fora da janela, dez/jan). **Zero antigos órfãos na janela**; os **14 novos sem par** (bets nunca extraídas, sem tipster) ficam para revisão manual do Feca. **Badge NEW** (gate `/nova-ui` executado): `dashboard_rows` marca `novo: true` só em Betnacional+`NXBNAC%` (chave ausente nas demais ~30k linhas), `apostas.js` renderiza pill `bet-new-pill` (mono uppercase, `--accent`, fora do modo público), classe em `components.css`; bumps `apostas.js v10` · `components.css v15`. **CICLO FECHADO na mesma sessão:** o Feca revisou na hora, preencheu os tipsters dos 14 sem par e aprovou os 2 casos decididos pelo de-para (dois 60×31,19 de 23/07 mantidos; par 02/07 50×4 L deletado) — o badge NEW foi então **removido por inteiro** (chave `novo` do `dashboard_rows`, pill do `apostas.js`, classe do `components.css`; bumps `apostas.js v11` · `components.css v16`). Nenhuma pendência restou desta sessão. **Gates (2× — na criação e na remoção):** `check-tokens` OK · `vm.Script` no apostas.js OK · `py_compile` OK · contagem pós-transação conferida (165; 14 sem tipster = exatamente os sem par) · grep confirma zero referências ao badge. Backups: `Backups/betnacional-depara-sharpenup-2026-08-02/` (snapshot dos 63 deletados + plano) · `betnacional-badge-new-2026-08-02/` · `betnacional-badge-remocao-2026-08-02/`. **Anterior: s230 abaixo.**)_

> **Histórico completo das sessões 230 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_VAIDEBET.md
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

Os 6 MASTER_*.md vivem em `/global/`; as 17 casas em `/casas/` (Polymarket por API, as demais por IA/texto).

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway; base nasce vazia sem migration.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Base do `LavaPessoal` (s222):** 2.877 apostas importadas do `.xlsx` pessoal do Lava (23/02 → 30/07/2026), `origem='import'`, conta `Padrão` em cada uma das 19 casas (ele não anota fornecedor). Script próprio e idempotente: `scripts/import_lavapessoal_xlsx.py` (re-rodar limpa só `origem='import'` daquele dono; captura da extensão sobrevive). **Não confundir com o dono `Lava`** — são bases distintas que só compartilham o apelido. **O P/L do dashboard não bate com a planilha de origem por desenho** (ela contabiliza em unidade; ver s222 no topo).
- **Base do `SoChutes` (s224):** 23.199 apostas all-time do tipster Só Chutes (17/09/2024 → 27/07/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` (Bet365/Superbet/Betano; casa não informada entrou como Bet365 — decisão do Feca). **Stake em UNIDADES** (1u = 1; o P/L do dashboard é o P/L em unidades: +1.381,29u). Script idempotente: `scripts/import_sochutes_xlsx.py`. O planilhamento novo é do **bot Sharpen** (repo próprio, ver s223).
- **Casas:** 17 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **10 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210) e **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`, sem código duplicado).
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências (aguardam bilhete real)

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betfair:** cashout **parcial** (`isPartialCashOut`) sem amostra — o total já está travado no harness (2 casos) · HW/HL sem amostra · Each Way com `0 < Retorno < Stake` (o §5 não cobre essa faixa; hoje sai "a conferir", sem chute)
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

- **Betfast / Tivo (s211):** cashout · bônus · aposta de sistema · outright · **aposta ABERTA** (as 50 da amostra são liquidadas) · `§9` de duas categorias (`Total de defesas do goleiro` · `Handicap de mapas`/`Map Advantage`)

**Achados de performance da s217 — medidos, não corrigidos (decisão do Feca, um por vez):**
- **`sims=10000` fixo mesmo com a base cheia.** As chamadas passam `10000` explícito, o que **atropela** a escala adaptativa que o `_calcPValueMCraw` tem por dentro (`n>10000 → 3000`). Com 30.851 linhas são ~308 milhões de iterações por cálculo, duas vezes. Fora da thread principal a tela não trava mais, mas o valor ainda leva **~1 minuto** para chegar (conferido no demo com 24.000: os cards ficaram girando bem depois do render). Cair para ~2.000 sims em base grande resolveria — **muda número exibido** (p95/p99 e p-value), então exige antes/depois medido na mesa e aval do Feca.
- **`/uso/tokens` responde 500** em produção (visto ao cronometrar as rotas do feed). Não investigado.
- **A casca `/app` carrega 3 iframes e os 3 puxam `/dashboard/data`** — `/inicio`, `/` (Extração) e `/dashboard/`, cada um montando o feed inteiro no servidor (3 × 11,6 MB por abertura). Um cache compartilhado entre os frames (ou o feed servido uma vez pela casca) cortaria 2/3 do trabalho.
- **Deep-link a frio monta a tela vazia.** Abrir `/app#dash/metrics` sem cache local: a casca chama `showPage('metrics')` antes de o `buildHTML` existir, `_lastPage` já fica marcado, e o `loadData` termina **sem chamar `renderPage`** (`app.js:1183`) — o `showPage` seguinte volta cedo pelo `if(id===_lastPage&&sig===_lastPageSig)return`. A tela fica com os `—` do markup. **Pré-existente**, não veio da s217.

**Próximo passo (backlog vivo, um por vez):**
- **Backfill eSoccer na base (s232) — regra nova aplicada, dado velho não.** Bilhetes de futebol virtual já gravados seguem `Futebol` (e os 2–3 que o Feca corrigiu na mão de `eBasket`). Problemas pontuais, na ordem: **(1) recaptura não corrige** — o UPSERT congela `esporte` para origem IA (só `origem='sync'` refresca), então é UPDATE manual no Postgres, nunca "deixa o robô re-passar"; **(2) escopo por conteúdo, não por tipster** — identificar por `casa='Bet365'` + handle `(...)` na descrição com mercado de Gols (o tipster `eSoccer LBB` é atalho, mas pode haver linha sem tipster e outros donos além do Feca — varrer todos); **(3) filtro duro do matcher** — perfil de tipster que declara `esportes` com `Futebol` (ex.: LBB) **para de casar** com bilhete eSoccer após o backfill (lição s221: morre em silêncio, só a coluna vazia) → adicionar `eSoccer` aos `esportes` do(s) perfil(is) afetado(s) NA MESMA operação; **(4) conferir as edições manuais do Feca de hoje** — para que valor as ex-eBasket foram (se `Futebol`, entram no backfill; se já `eSoccer`, verificar grafia exata, `e` minúsculo); **(5) P/L por esporte muda de gaveta** — a aba Esportes do dash perde essas linhas de `Futebol` e ganha `eSoccer`; esperado, mas avisar antes para não parecer sumiço. **Confirmado que NÃO é problema:** `esporte` está fora de `_SIG_COLS` → assinatura/dedup intactas, sem recálculo.
- **Matcher: "feudo empírico" — medido na s221, NÃO implementado.** O `Sugerir tipsters` é 100 % **declarativo**: lê só os perfis (casas · esportes · mercados · dica de stake) e **nunca** o histórico. Por isso as stakes **quebradas** (109,38 · 112,18 · 184,21…) ficam eternamente vazias — nenhum perfil declara quebrada na Bet365, e por stake elas são de todo mundo (M&M 284 · SóChutes 121 · SóTudo 31 · LBB 30). **O sinal que falta está na própria base:** no trio **casa · esporte · categoria**, um tipster domina. Medido na janela de 2.207 bilhetes que a tela **já carrega** (dá para computar no front, sem endpoint novo): `Bet365·Futebol·Gols → LBB 98 %` (226) · `Bet365·Futebol·Escanteios → SóTudo 82 %` (257) · `Bet365·eBasket·Pontos → Ctrl Alt Green 100 %` (219) · `Bet365·Tênis·ML → Robotenis 99 %` (168) · `Superbet·Múltiplos·Múltipla → Arrudex 92 %` (169) · `BETesporte·Futebol·Múltipla → Peixe 100 %`. Regra proposta: tipster **ativo** com ≥ 90 % e ≥ 15 bilhetes no trio leva; senão cai no matcher declarativo de hoje. **Cuidado que o próprio caso do 199 ensina:** o dono de um trio **muda com o tempo** (SóTudo → LBB entre maio e julho), então a janela precisa ser **recente**, não a base inteira — na base inteira `Bet365·Futebol·Gols` cai para 52 % de LBB e o critério não dispara. Fazer só depois de backtest com **holdout temporal** (treina no passado, mede no futuro), nunca in-sample.
- **Excluir conta: o caminho nunca rodou contra Postgres de verdade** (s219). Os 7 casos de `test_excluir_parceiro.py` usam conn simulado, como o resto da suíte. Três coisas ficaram sem prova real: o `DELETE ... RETURNING to_jsonb(b.*)`, o cast `::jsonb` do snapshot no INSERT da lixeira, e o corpo do `DELETE` via HTTP. **Teste barato, fazer antes de excluir qualquer conta com histórico:** criar conta descartável, capturar 1 ou 2 bilhetes, excluir pelo modal, e rodar `python scripts/restaurar_conta_lixeira.py` para ver se a linha aparece com a contagem certa. Depois `--aplicar` num id e conferir se as apostas voltam. A forma travada seria um caso em `tests/test_repository_db.py` (roda no CI com `TEST_DATABASE_URL`, nunca em prod).
- **Betfast: rodar a captura pela EXTENSÃO** (s211). A API já foi validada ao vivo (varredura do teto: 32 de 32, ver acima), mas o robô em si nunca rodou: recarregar a extensão, **Ctrl+Shift+R** na aba, capturar e conferir contagem/datas/odds/código no dashboard. **O gatilho do teto continua sem exercício ao vivo** — a conta que loga no navegador tem 32 bilhetes e não chega nas 50; para ver o toast *"a captura foi além do teto"* seria preciso rodar na conta `fecanario`.
- **Pinnacle sem fixture no harness** (s201): a instrução foi corrigida (§6/§11 não afirmam mais que a exibida é autoritativa em `W`), mas a leitura da odd **nunca foi travada contra dado real** — só Betfair, KTO e Tivo têm caso. Com o JSON do `POST /member-service/v2/wager-filter` dá para criar `fixtures/pinnacle.*.json` + `casos/pinnacle.mjs` e medir de fato o quanto a exibida diverge de `Retorno ÷ Stake`. O banco não serve para isso: guarda stake e odd, nunca o retorno.
- **bet365 sem caso no harness** (s202): é a única casa de robô sem regressão travada — e o parser dela já quebrou 3 vezes. As fixtures reais (`summary` + `confirmation` do bilhete com bet builder) já estão em `extensor/harness/fixtures/`; falta escrever `casos/bet365.mjs`. A conferência de cobertura dela **já está ligada** (`831f97f`).
- **`renomear_parceiro` não recalcula a assinatura** (s198): `parceiro` entra no hash, então toda conta renomeada duplica o histórico na próxima captura.
- **41 apostas com odd truncada em reticências** (`2.50001664442...`): 22 Bet365, 6 Novibet, 6 Bolsa, 4 Betfair, 3 Esportiva Bet. A instrução proíbe reticências e uma odd assim não converte para número — mexe em P/L, não é cosmético.
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Solto (cosmético):** favicon da KTO aponta para `kto.com`; o domínio real é `kto.bet.br`. Corrigir nos 3 mapas (`extensor/popup.js`, `app/static/index.html`, `app/static/dash/assets/js/data.js` + `inicio.html`).
- **Tela "Em Aberto" fora do material de venda** (s215): `scripts/demo/capturar.mjs` não captura a tela nova — o servidor de demonstração já a serve, falta só decidir se ela entra no showcase (e a numeração dos arquivos existentes muda). **Decisão do Feca: entra, mas só depois de a tela estar finalizada.**
- **Material de venda: 4 correções abertas nas capturas** (s214). O pipeline funciona (`scripts/demo/`: perfil → base fictícia → servidor → `capturar.mjs`) e as 8 telas saíram, mas quatro coisas travam o uso na landing. **(1) Contas irreais: o mock devolve 1.830 contas, o real são 102** — `servidor_demo.py:_parceiros()` deriva conta de cada par (parceiro, casa) visto no feed, então cada pessoa nasce com ~18 contas. **E a tela repete essas 1.830 embaixo de cada uma das 29 casas, somando 53.070** — essa segunda multiplicação foi medida, não diagnosticada; conferir se é forma do payload antes de mexer no front. **(2) `Diagnóstico de Risco` sai em "calculando…"**: é Monte Carlo de 10.000 simulações sobre 24 mil apostas e o screenshot dispara antes de terminar — esperar o cálculo, não o relógio. É o painel que sustenta o argumento estatístico da página. **(3) Custo de contas e de tipsters em R$ 0**, então o "P/L Líquido" fica idêntico ao bruto e a tela perde justamente o recurso que diferencia — popular `/custos/store` no mock. **(4) `Nível de Solidez: Baixa`**, com MDD 90,88% e Recovery Factor 0,94×. É coerente com odd média 7,7, mas é a nossa própria régua reprovando a operação da demonstração. Subir o edge de 4,5% para ~8% leva o ROI a ~4% e a folga para faixa saudável, sem sair do plausível.
- **Landing do usuário final: reescrita aprovada, não feita** (s214). O Feca pediu duas frentes: **tirar detalhe de arquitetura** e **entrar com print real**. Sai da página a seção "Integramos o motor" (Kambi/BetConstruct/Altenar), a aba "API do motor" do hero (`Koef`, `WinAmount`), os pesos e cortes da Solidez, "27 categorias fechadas", os "94,5% de acerto de categoria" e a faixa de números do hero. Fica o que é confiança e não mecanismo: não pedimos senha, a extensão não aposta nem move saldo, e o bloco "o que o Sharpen não é". **A ordem importa: print primeiro, texto depois** — hoje a página se defende explicando o mecanismo porque não mostra nada. Fonte em `docs/marketing/landing-usuario-final.html`.
- **Em Aberto: relato do Gabriel SEM confirmação** (s215, aberto): funciona para o Feca (57 abertas, R$ 13.325, conferido na sessão logada em `www.sharpen.bet`), mas o Gabriel disse que não. **Hipótese principal: casca velha ainda gravada no navegador dele** — o `no-cache` só vale a partir da próxima ida ao servidor, não desfaz cache já gravado; `Ctrl+Shift+R` uma vez resolve (F5 normal pode não recarregar o iframe do dashboard). **Antes de mexer na tela, distinguir pelo que ele vê:** cards com título e corpo vazio, sem nenhum KPI = ainda é cache; os 4 KPIs em `R$ 0` / "nada em aberto" = não é bug, a base dele não tem aposta aberta (conferir de quem é a base pelo filtro "Operador"). O jeito de medir é ler quais scripts o navegador dele carregou (`[...frame.contentDocument.scripts].map(s=>s.src)`) — versão antiga ou tag ausente = cache.
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

### Bloqueado por ação humana (não é bilhete)

- **Env vars de senha no Railway (s216, s218, s220) — estado NÃO instrumentado.** `SENHA_LAVAPESSOAL_HASH` **está no ar e o Lava entra** (confirmado pelo Feca em 31/07, s222). `SENHA_WILLIAMOLIVEIRA_HASH` e `SENHA_VINICIUSOLIVEIRA_HASH`: **não confirmadas** — podem já ter sido coladas; ninguém atualiza esta linha quando a ação acontece fora do repo.
  > ⚠️ **Esta linha é uma pendência declarada, não uma medição.** Não afirme a partir dela que um login está quebrado — foi exatamente o erro cometido na s222. Para saber de verdade: `POST /login` devolvendo **200** = hash certo; **401** = ausente ou diferente (429 é rate-limit, 500 é erro do app). Sem esse teste ou a palavra do Feca, escreva "não confirmado".

  Procedimento, se algum dia faltar mesmo: os hashes **não entram no git** — se perdidos, gerar de novo com bcrypt e colar na caixa de Variables do Railway (literal, 60 caracteres, sem espaço nas pontas; o `$` do `$2b$12$…` chega mutilado por qualquer shell que interpole variável).
- **`LavaPessoal`: 30 apostas com stake 0** (s222) — importadas, mas **invisíveis no dashboard** (`dashboard_rows` corta `stake <= 0`). 23 delas têm resultado. Aparecem na grade da **Extração** (`list_bilhetes` não filtra), então a correção é humana: preencher a stake lá e elas entram no P/L. Todas do tipster `Peixe`, abr–jul.
- **`LavaPessoal`: duas contas pré-existentes vazias** (s222) — `Bet365 | monster@2025 [Richard]` e `Betano | karlmarxrosa@aurainteligente.com [221193Cy*]`, criadas em 30/07, arquivadas, **zero** bilhetes. Não vieram do import e não foram tocadas. Se forem lixo de teste, apagar pelo botão Excluir do Painel de Contas (s219).

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
