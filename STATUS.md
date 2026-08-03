# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-08-02 (sessão 238 — **Zora eSports nasce no Sharpen: conta `ZoraEsports` (dono solo) + página pública `/tipsters/zoraesports` (etapa 1 de 4).** Plano aprovado pelo Feca: o bot Sharpen (repo `flrcarvalho/sharpen-bot`) vira **produto multi-tipster** ("a ideia é que atenda muitos tipsters"); a Zora eSports é o 2º tipster. Nesta etapa, só o app: linha `ZoraEsports` em `USUARIOS` (`app/auth.py` — semente; o seed leva ao banco no boot, base nasce vazia sem migration) + slug `zoraesports` em `TIPSTERS_PUBLICOS` (`app/main.py`). Senha gerada e hash bcrypt entregue ao Feca no chat — **o login só passa a funcionar quando `SENHA_ZORAESPORTS_HASH` for colada no Railway** (fail-closed por desenho; pendência em §5). Dados do Telegram já levantados para as próximas etapas: apoio `Apoio - Zora eSports` = `-1004350370479` · tipster Zora = `5024465308` · destino = tópico **Esports** (`message_thread_id` **3**, confirmado pelo link `t.me/c/4371822520/3`) do grupo-fórum TG-Betting `-1004371822520` — destino é TÓPICO de fórum, não canal (o envio do bot muda). **Gates:** `pytest tests` **337 passed** (⚠️ rodar `pytest tests`, não `pytest` na raiz — a raiz coleta snapshots de `Backups/` e explode com 14 erros falsos) · `py_compile` OK. Backup `Backups/zoraesports-conta-slug/`. **Próximas etapas (no repo do bot, FORA deste):** (2) refactor multi-tipster preservando o Só Chutes em produção (registro de tenants, dados/cookie por tipster com migração no boot, testes verdes); (3) tipster Zora com contador próprio (`ZE<aaaamm>-<n>` sem link) + perfil de parser eSports — **aguarda 2–3 bilhetes reais da Zora (print + legenda)**; (4) smoke `MODO_TESTE` no apoio → produção. **Na sequência da mesma sessão, o BACKFILL:** Feca confirmou stake em **unidades** e mandou os prints de todo o histórico do tópico ("pode planilhar já") — **17 bilhetes de 01–02/08 subiram ao Postgres** (ids 122243–122259) por script one-off no scratchpad usando o caminho canônico do app (`parse_tsv → validar_linhas → upsert_bilhetes`, um upsert por bilhete com `criado_base` = hora da mensagem; nunca assinatura manual — lição dos importadores velhos). Casa pelo estilo do print (regra do Feca): escuro com `$ Vol.` = **Polymarket** (14) · tabela `Partida Vencedor/HDP/OU` 3 decimais = **Pinnacle** (3). Códigos `ZE202608-1..17` (contador mensal; **o bot da etapa 3 continua do 18**). Conferido no banco e no feed público: 17 linhas, **8 W · 5 L · 4 abertas**, tipster `Zora eSports`, contas `Polymarket|Zora eSports` e `Pinnacle|Zora eSports`. Convenções da Zora aprendidas dos prints: `@X.XX min` é odd MÍNIMA recomendada (planilha usa a odd do print da seleção); resultado = emoji ✅/❌ editado na legenda; "Bunker" = perna segura de combo; **bilhete riscado + "Evitem, deu ruim" NÃO planilha** (1 caso: KT Rolster Map 2 de 02/08 — validar convenção com o Feca). Stake da Zora: **unidades** (confirmado). **Anterior: s237 abaixo.**)_

_Anterior: 2026-08-02 (sessão 237 — **Bot Sharpen do Só Chutes (repo próprio `flrcarvalho/sharpen-bot`): formato "individuais + dupla" destravado + aliases de comando.** Primeira legenda real nesse formato ("Sundgot 1u / Carranza 0,75u / 0,25u dupla") revelou que o parser só reconhecia individual com parênteses (`Nome (1u)`): as 2 individuais ficariam **fora da planilha em silêncio** (só a dupla de 0,25u entraria, porque `citouAlgo` desliga o fallback). Fix no `parseLegenda`: aceita as duas formas — `Nome (1u)` e `Nome 1u` — e linha com `dupla`/`tripla` nunca vira individual; a legenda real virou caso de teste (parser + `montarApostas` gerando as 3 apostas). Commit `2a52370`, bot reiniciado, e o **bilhete #12 entrou em produção com individuais + dupla** (log `ZjJcn-J1`/`-D1`). Segundo achado na sequência: o `/ajuste #11` do Feca **não teve resposta nenhuma** — o comando é `/ajustar` e o roteador descartava comando desconhecido com `return` silencioso (parecia bot morto). Fix: aliases `/ajuste`→`/ajustar` e `/anula`→`/anular` (roteador + regex internos dos handlers, senão o alias cairia na mensagem de "Uso:"), comando em qualquer caixa (`toLowerCase`), e **comando desconhecido agora responde com a lista de comandos** (regra: nunca ignorar em silêncio). README do bot atualizado. Gates: `node --check` + `node test/testes.js` verdes nos 2 commits. Bot local reiniciado 2× com o código novo (roda por `cmd /c node src\index.js >> bot.log`, processo confirmado + `login ok`). **Nada mudou no Planilhador além deste STATUS.** **Anterior: s236 abaixo.**)_

_Anterior: 2026-08-03 (sessão 236 — **Multiusuário Fase 3 no ar em modo DORMENTE: login Google (OIDC) + Telegram prontos; os botões acendem sozinhos quando o Feca colar as credenciais no Railway.** Madrugada autorizada pelo Feca ("total aprovação para trabalhar a madrugada inteira"). **Fail-safe por env var:** sem `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`TELEGRAM_BOT_TOKEN`, `GET /auth/metodos` nega tudo, os botões nem aparecem no login e TODAS as rotas sociais dão 404 (deploy zero-risco; smoke confirmou a tela idêntica). **Google:** `GET /auth/google` (redirect ao consent com `state` anti-CSRF = `criar_token_curto('oauth-google')`, 10 min, assinado com o SESSION_SECRET) → `GET /auth/google/callback` troca o code via httpx no endpoint /token e valida claims com `_claims_do_id_token` — **sem verificação de assinatura de propósito** (o id_token vem direto da Google via TLS+client_secret, não é token apresentado pelo cliente; valida iss/aud/exp/sub) e **e-mail não-verificado é descartado** (anti account-takeover por e-mail). **Telegram SEM widget embarcado** (a CSP não abre para script externo): `GET /auth/telegram/ir` redireciona a `oauth.telegram.org/auth` (bot_id = metade numérica do token) → volta em `GET /auth/telegram/retorno` (página-ponte inline que lê o `#tgAuthResult` do fragmento — nunca chega ao servidor sozinho — e entrega ao `POST /auth/telegram`) → valida `_telegram_dados_validos` (HMAC-SHA256 da spec, chave = SHA256(bot_token), anti-replay `auth_date` ≤10 min). **Os dois convergem em `_resolver_social`:** vínculo existente (`google_sub`/`telegram_id`) → sessão se `ativo` (mesmo `criar_token`+cookie de sempre); conta existente com o MESMO e-mail verificado → vincula e loga; **desconhecido → nasce `pendente` no funil do /admin, NUNCA entra direto** (username auto-derivado por `derivar_username` — sanitiza p/ a régua do `dono`, colisão case-insensitive ganha sufixo). Login.html: bloco social (divisor "ou" + botões ghost) escondido por padrão, populado por fetch `/auth/metodos`; mensagens `?social=pendente/suspenso/erro` no card. DB: `buscar_usuario_social` (whitelist de campo — nome de coluna nunca vem do usuário), `vincular_social` (e-mail só preenche se vazio), `usernames_em_uso`, `criar_usuario_social` (senha_hash NULL = conta só-social). **Gates:** `pytest` **337 passed** (21 novos em `tests/test_login_social.py`: fail-safe 404, HMAC do Telegram — adulterado/velho/bot errado reprovam, claims Google — aud/iss/exp/email_verified, derivação de username, POST /auth/telegram ponta-a-ponta com DB falso: ativo=cookie · pendente/suspenso/novo=sem cookie) · `check-tokens` OK · `vm.Script` (login.html + página-ponte) OK · `py_compile` OK. `docs/PLANO_MULTIUSUARIO_2026.md` atualizado (Fases 1-3 ✅; falta só a parte externa do Feca e a Fase 4). Backup `Backups/multiusuario-fase3-social/`. **PRÓXIMO PASSO (decidido no encerramento: fica para a PRÓXIMA sessão, parte do Feca):** seguir `docs/GUIA_CREDENCIAIS_LOGIN_SOCIAL.md` — OAuth Client no Google Cloud (redirect `https://www.sharpen.bet/auth/google/callback`; publicar o app, senão só test users logam) + bot no @BotFather (`/setdomain` → `www.sharpen.bet`); colar `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`TELEGRAM_BOT_TOKEN` no Railway → botões acendem sem novo deploy; aí testar os 2 fluxos ponta a ponta (conta nova → pendente no `/admin` → aprovar → logar). Depois disso, resta só a Fase 4 (pagamento; gateway a definir). **Anterior: s235 abaixo.**)_

> **Histórico completo das sessões 235 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Identidade na tabela `usuarios` do Postgres via cache em memória (s233 — Fase 1 do `docs/PLANO_MULTIUSUARIO_2026.md`); os dicts de `app/auth.py` são a SEMENTE. Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway (o seed leva ao banco no boot); base nasce vazia sem migration. Suspender no banco (`status`) revoga login E sessão em ≤60s.
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
- **Backfill eSoccer — Feca FEITO (s234); resta o residual dos outros donos, se eles quiserem.** A auditoria da s234 varreu a Bet365 inteira e viu, fora do Feca: **Gabriel** ~14 bilhetes eSoccer como `Futebol` (tipsters próprios `Esoccer`/`LBB`) + **1 linha com grafia `Esoccer` na coluna esporte** (única da base; padroniza para `eSoccer` se mexer); Jonathan/William/LavaPessoal só têm eBasket-like (fora do escopo eSoccer). Método pronto e testado: script da s234 (`Backups/esoccer-backfill-feca-2026-08-02/`) — UPDATE por id auditado + perfil do tipster ganhando `eSoccer` nos `esportes` (senão o filtro duro do matcher mata as sugestões em silêncio, lição s221). `esporte`/`tipster` fora de `_SIG_COLS` → dedup intacta. Decisão do Feca (s234): **não tocar na base de outros donos sem eles pedirem**.
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

- **`SENHA_ZORAESPORTS_HASH` no Railway (s238) — aguardando o Feca colar.** A conta `ZoraEsports` já está no código (seed no boot); até a env var existir, o login dela devolve 401 (fail-closed, igual senha errada). Hash entregue no chat da s238 (60 caracteres, colar literal na caixa de Variables). Enquanto isso a página `/tipsters/zoraesports` já responde (base vazia).
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
