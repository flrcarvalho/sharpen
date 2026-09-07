# FAXINA DE DOCUMENTAÇÃO — proposta (Fase 1)

> **Nada foi editado, movido ou apagado.** Este arquivo é o único produto da Fase 1.
> Medido em **2026-09-06**, contra o código real e o git — não contra o que os documentos
> dizem de si mesmos.
>
> Escopo declarado pelo Feca: `global/MASTER_*.md`, `casas/CASA_*.md` e `.claude/commands/`
> **estão fora**. Não foram lidos para efeito de classificação nem entram em nenhum lote.

---

## 0. O que foi medido (e como)

| Medição | Comando | Resultado |
|---|---|---|
| Suíte de testes | `python -m pytest tests/ -q` | **756 passed, 30 skipped** (786 coletados), 37s |
| Casas (leitura) | `python tools/audit_casas.py` | **28 OK, 0 FAIL** |
| Casas (captura) | `python tools/audit_sharpenup.py` | **0 FAIL** — 26 robô + 3 print |
| `.md` vivos | walk fora de `node_modules/`, `Backups/`, `.git/` | **103 arquivos** |
| Links markdown | varredura própria (script em scratchpad) | **1 quebrado** (ver §1.2) |
| `Backups/` | walk + agregação | **551 pastas · 128,1 MB · 2.050 arquivos** |

> ⚠️ **Divergências do briefing, para você conferir:** o briefing falava em 748 testes
> (medi 756), 137 `.md` vivos (medi 103 — a diferença são os `casas/` e `global/`, que o
> briefing contava e que aqui ficam fora), 550 pastas / 129 MB em `Backups/` (medi 551 /
> 128,1 MB) e **75 blocos de sessão no STATUS** (medi **10** blocos `## Sessão` + 16
> parágrafos `_Anterior:` no cabeçalho). Nenhuma dessas diferenças muda a conclusão.

### A anatomia do STATUS.md, em bytes

| Faixa | O que é | Bytes | % |
|---|---|---|---|
| linhas 1–46 | cabeçalho: título + `_Atualizado:` + **16 `_Anterior:`** | **66.913** | 36 % |
| 47–125 | `## Onde parei (fim da sessão 328)` | 4.168 | 2 % |
| 126–1136 | 10 blocos `## Sessão` (327 → 317) | 57.154 | 30 % |
| 1137–1215 | §1 a §4 (construção, invariantes, estrutura, estado) | 3.921 | 2 % |
| **1216–1438** | **§5 Pendências** | **51.400** | **27 %** |
| 1439–1460 | §6 rodar/produção + §7 workflow | 3.350 | 2 % |

O maior `_Anterior:` sozinho tem **17.230 caracteres** — um parágrafo só, numa linha só.
Os 16 somados dão **64,6 KB** de narrativa que **já está inteira** no `docs/HISTORICO.md`
ou nos blocos `## Sessão` logo abaixo.

---

## 1.1 Tabela de papéis — papel declarado × papel real

> "Data declarada" = a que o **texto** afirma (`> Atualizado em…`, `**Status:**`,
> `_Última atualização_`), não o `mtime` nem o git.

### Raiz

| Arquivo | Tam. | Data declarada | Papel declarado × papel real |
|---|---|---|---|
| `CLAUDE.md` | 65,9 KB | 2026-09-06 (s328) | **Declarado:** regras operacionais obrigatórias. **Real:** regras **+** ~28 KB de narrativa de caso (quem quebrou, com que bilhete, em que sessão) **+** um rodapé `VERSÃO/ATUALIZADO` de 2,2 KB que é changelog de sessão. Divergência: **é regra e é história no mesmo arquivo**, e a história é auto-carregada em toda sessão. |
| `STATUS.md` | 187,6 KB | 2026-09-06 (s328) | **Declarado:** "documento de rehydration de sessão… lê isto primeiro". **Real:** rehydration (5 %) + changelog de 26 sessões (64 %) + **o backlog inteiro do projeto** (§5, 27 %). Divergência: **o único backlog real do repo está escondido dentro de um changelog**, atrás de 124 KB de história. |
| `ONDE_ESTOU.md` | 10,4 KB | corpo = **2026-07-11 (s122)**; banner = 2026-07-19 (s158-160) | **Declarado:** "bater o olho e saber exatamente onde o projeto está". **Real:** retrato de 49 dias e ~206 sessões atrás, com um banner por cima dizendo que o corpo não vale. Divergência: **o papel é "onde estou" e o conteúdo é "onde eu estava"** — números errados (§1.2), frentes fechadas listadas como abertas. |
| `Ideias/README.md` | 9,1 KB | **2026-07-11** | **Declarado:** "índice mestre de tudo que é plano, estudo ou ideia futura… página viva". **Real:** índice de 8 semanas atrás. Diz "Fase 1 = tabela `usuarios`" como *próximo passo* — Fases 1, 2 e 3 estão no ar desde a s233-s236. Divergência: **índice de planos que não acompanhou os planos.** |

### `docs/` — vivos e referências

| Arquivo | Tam. | Data declarada | Papel declarado × papel real |
|---|---|---|---|
| `HISTORICO.md` | 1,18 MB | — (sem data) | **Declarado:** sessões anteriores. **Real:** bate. Único problema é **forma**: 1,18 MB em 1.326 linhas, 4 seções paralelas com faixas sobrepostas, sem índice. |
| `SHARPENUP_ARQUITETURA.md` | 38,8 KB | — | Mapa da captura. **Bate.** Referenciado por `CLAUDE.md`, 2 guias, `extensor/README`, `app/main.py`. É o doc mais saudável do repo. |
| `GUIA_CASA_SHARPENUP.md` | 18,2 KB | — | Procedimento. **Bate.** 7 referências de entrada. |
| `GUIA_NOVA_CASA.md` | 7,3 KB | — | Procedimento. **Bate.** |
| `GUIA_RECON_TESTER.md` | 6,1 KB | — | Texto para repassar ao tester. **Bate.** |
| `GUIA_BOT_TIPSTER.md` | 5,2 KB | 2026-09-04 | Uso interno, 8 passos. **Bate** (o mais novo dos guias). |
| `GUIA_CREDENCIAIS_LOGIN_SOCIAL.md` | 6,2 KB | s236 | **Declarado:** procedimento para acordar a Fase 3. **Real:** ainda válido para o Google; o botão **Telegram foi removido do `/login` na s324** e o guia não sabe. Divergência parcial. |
| `UI_REFERENCE.md` | 9,1 KB | **2026-06-28** | **Declarado:** regras de UI da marca. **Real:** bate no essencial (§5 padrão monetário é citado como lei pelo `CLAUDE.md` e pelo `/nova-ui`), mas a data é de 70 dias atrás e há **conflito conhecido com a Escada de Tinta** sobre cor de label (registrado na memória do projeto, não no arquivo). |
| `SHELL_SPEC.md` | 5,6 KB | s80d | Contrato da casca. **Bate**; `check-tokens.mjs` aponta para ele. |
| `REFERENCIA_CHIPS_CASAS.md` | 10,7 KB | — | Spec autocontida. **Bate** (citada por `index.html` e `database.py`). |
| `REFERENCIA_EMOJIS_ESPORTES.md` | 8,7 KB | — | Spec autocontida. **Bate.** |
| `REFERENCIA_LISTA_APOSTAS.md` | 13,7 KB | — | Spec autocontida. **Bate**, mas só o `HISTORICO` a menciona. |
| `CASAS_CONFIABILIDADE.md` | 11,6 KB | — | **Declarado:** "espelho do estado atual" das pendências das casas. **Real:** espelho de 13-14 casas; hoje são **28**. Divergência: **espelho parado.** |
| `runbook-rotacao-postgres.md` | 3,4 KB | — | Procedimento de produção. **Bate**; execução segue pendente (é o achado #1 da `AUDITORIA_2026`). |
| `marketing/README.md` | 6,1 KB | — | Regras dos 2 HTML de marketing (DARK ONLY). **Bate**, e é **load-bearing**: `tests/test_landing.py` cita a regra dele. |
| `ADR-001-migracao-numeric-decimal.md` | 5,2 KB | 2026-07-03 | Decisão com gate. **Bate** (proposto, execução adiada por desenho). |
| `ADR-002-dashboard-primeira-carga.md` | 5,1 KB | s95 | Decisão com gate. **Bate** (Fase 1 aplicada, Fase 2 condicional). |
| `DESAMBIGUACAO_RAQUETE_2026.md` | 16,2 KB | 2026-07 | **Declarado:** "blocos prontos pra colar, não aplicado". **Real:** bate — mas o Badminton **foi** aplicado nos 3 MASTERs (s245). Precisa dizer o que sobrou. |
| `PESQUISA_BADMINTON_2026.md` | 16,1 KB | 2026-07-21 | Mesmo caso do anterior: pesquisa cujo resultado já virou MASTER. |
| `ESTUDO_PRECIFICACAO_2026.md` | 14,9 KB | 2026-08-24 (s295) | Estudo com status honesto (A e C aplicadas, B bloqueada). **Bate.** |

### `docs/` — auditorias e planos

Detalhe item a item em **§1.3**. Resumo do papel real:

| Arquivo | Tam. | Data declarada | Papel real |
|---|---|---|---|
| `AUDITORIA_2026.md` | 11,9 KB | reconciliado **2026-07-10 (s122)** | **Declara-se "documento único e vivo"** e não é vivo há 206 sessões. 5 dos itens que ele mostra como abertos **estão fechados no código** (§1.2). |
| `AUDITORIA_CRITICA_2026-07-02.md` | 31,4 KB | 2026-07-02 | Fonte histórica dos 50 achados; **o próprio `AUDITORIA_2026` declara que virou histórico**. |
| `RELATORIO_CORRECOES_2026-07-03.md` | 13,9 KB | 2026-07-03 | Idem — declarado histórico pelo `AUDITORIA_2026`. |
| `RISK_REDUCTION_PLAN.md` | 8,8 KB | 2026-07-03 | Idem — declarado histórico pelo `AUDITORIA_2026`. |
| `AUDITORIA_TURBO_2026-07-19.md` | 23,5 KB | 2026-07-19, com tracker até s160 | **Tem backlog vivo** (#6, #15/#16, #21, #22, #23, #25) — não é histórico. |
| `AUDITORIA_TURBO_2026-07-20.md` | 17,1 KB | 2026-07-20 | **95 achados confirmados, ZERO tracker.** É o maior backlog não rastreado do repo. |
| `AUDITORIA_SHARPENUP_2026-07-25.md` | 18,1 KB | 2026-07-25 (s194) | Auditoria cujo produto (o padrão + os guias + `audit_sharpenup.py`) **existe e está verde**. Executada. |
| `AUDITORIA_VISUAL_CASCA_2026-06-30.md` | 3,5 KB | 2026-06-30 (s78/79) | Punch-list visual; o próprio `Ideias/README` diz "hoje quase toda superada". |
| `PLANO_CONSTRUCAO.md` | 5,6 KB | jun/2026 | **Auto-declarado histórico**, com banner. Honesto. |
| `PLANO_UNIFICACAO_2026.md` | 14,3 KB | 2026-06-27, "aguardando CSV limpo" | Executado — o `STATUS §4` diz "migração planilha → Postgres **completa e reconciliada**". |
| `PLANO_BET365_CAPTURA_API.md` | 12,5 KB | 2026-07-22, "falta escrever o código" | Executado — `extensor/b3_inject.js` existe e a Bet365 passa no `audit_sharpenup`. |
| `PLANO_POLY_PERSISTIR_ATIVAS.md` | 6,6 KB | 2026-07-11, "plano pronto" | Executado — `polymarket.coletar_ativas` no ar; ativa vira bilhete aberto. |
| `PLANO_MULTIUSUARIO_2026.md` | 10,8 KB | s233–s236, Fases 1-3 ✅ | **Vivo** (Fase 4 = pagamento). Status honesto. |
| `PLANO_TRADUTOR_DETERMINISTICO.md` | 22,4 KB | s295/s297, Fase 0 ✅ | **Vivo** (Fases 1-4). Citado por `app/tradutor.py` e `app/main.py`. |
| `PLANO_TIPSTER.md` | 20,8 KB | 2026-07-11, Fase 0 no ar | **Vivo** (P1/P2/P3). Citado por `database.py`, `main.py`, 2 testes. |
| `PLANO_EXTRACAO_WORLDWIDE.md` | 11,6 KB | s132, Fase 0 validada | **Vivo** (Fases 1-5). Citado por `database.py` e pelo `STATUS §5`. |
| `PLANO_CASCA_UNIFICADA.md` | 7,4 KB | s86, Fatias 1-2 ✅ | **Vivo** (Fatia 3). |
| `PLANO_POLY_INCREMENTAL.md` | 5,1 KB | s158, desenho pronto | **Vivo** — sem marca d'água em `polymarket.py`. |
| `PLANO_DASHBOARD_C.md` | 15,4 KB | "não iniciado" | **Vivo** (condicional, ADR-002 Fase 2). |
| `PLANO_INFERENCIA_POR_CAMPO.md` | 7,5 KB | s133, "sem código" | **Vivo** (backlog). |
| `PLANO_INTELIGENCIA_TIPSTER.md` | 17,2 KB | s146, "rascunho, sem código" | **Vivo mas defasado** — descreve o matcher v5 de 15/07; ele mudou muito (s221, s289, s310). |
| `auditoria_turbo/gerente_*.md` (11 arq.) | 90 KB | 2026-07-19 | Anexos de UMA auditoria. Só ela os linka. |

### Fora de `docs/`

| Arquivo | Tam. | Papel real |
|---|---|---|
| `extensor/README.md` | 7,2 KB | Vivo — README do produto extensão. |
| `extensor/harness/README.md` | 3,2 KB | Vivo — como rodar a regressão. |
| `golden_set/README.md` | 0,8 KB | Vivo — explica o propósito da pasta. |
| `tools/eval_zeroshot/README.md` | 2,9 KB | Vivo — ferramenta da Fase 0 worldwide. |

---

## 1.2 Contradições factuais entre arquivos

> Onde dois documentos afirmam coisas diferentes **sobre o mesmo fato**.
> "Verificado" = rodei o comando / li o código hoje. "A confirmar" = não provei.

### C1 — Número de testes

| Fonte | Afirma |
|---|---|
| `ONDE_ESTOU.md` (banner) | "**172 testes** passam (eram 65)" |
| `ONDE_ESTOU.md` §2 | "`pytest` ✅ **65/65** passam" *(o mesmo arquivo se contradiz)* |
| `docs/AUDITORIA_2026.md` #40 | "**65 testes** em `tests/`" |
| `AUDITORIA_TURBO_2026-07-19` | "baseline **140** testes" → "suíte segue **172**" |
| `AUDITORIA_TURBO_2026-07-20` | "**178 passed, 4 skipped**" |

**Correto hoje: 756 passed, 30 skipped.** Verificado — `python -m pytest tests/ -q`.

### C2 — Número de casas

| Fonte | Afirma |
|---|---|
| `ONDE_ESTOU.md` §2 e §3 | "**14 casas** OK" · "6 masters globais + **14 casas**" |
| `docs/CASAS_CONFIABILIDADE.md` | matriz de **13** casas |
| `STATUS.md` §3 | "as **28** casas em `/casas/`" |
| `STATUS.md` §4 | "**25 casas por API**" |

**Correto hoje: 28 casas** (`casas/CASA_*.md` sem o `CASA_MODELO.md`), todas OK no
`audit_casas.py`. Das 28 + Polymarket, **26 capturam por robô** e **3 por print**.
Verificado — `ls` + os dois `audit_*.py`.
O `STATUS §3` está certo na contagem de arquivos; o `STATUS §4` erra por 1 na de robôs.

### C3 — Estado do SaaS multiusuário

| Fonte | Afirma |
|---|---|
| `Ideias/README.md` §1.1 | Fase 1 (tabela `usuarios`) = "🟢 **próximo passo**" |
| `ONDE_ESTOU.md` §5 | "**Fase 1 do SaaS** → na canteira" |
| `docs/PLANO_MULTIUSUARIO_2026.md` | "**FASES 1, 2 e 3 EXECUTADAS**" (s233–s236) |
| `CLAUDE.md` | "desde a Fase 2 quem se cadastra pelo site cria a própria linha em `usuarios`" |

**Correto hoje: Fases 1, 2 e 3 no ar; Fase 4 (pagamento) não iniciada.** Verificado —
tabela `usuarios` em `database.py`, `POST /signup` e `/admin` em `main.py`, `/auth/google`
+ `/auth/telegram` presentes.

### C4 — Cinco achados que a `AUDITORIA_2026` mostra abertos e que estão fechados

| # | Diz | Está |
|---|---|---|
| #4 | 🔴 "rate limit confia em `X-Forwarded-For`" | **Fechado** — `main.py:1941-1946` tem o comentário do hop confiável do Railway |
| #6 | ⏸️→🔴 "`SESSION_SECRET` efêmero, só avisa" | **Fechado** — `auth.py:38-49`: em produção **não sobe** sem a env |
| #15 | 🔴 "falta índice em `criado_em`/`codigo_bilhete`" | **Fechado** — `idx_bilhetes_dono_criado` e `idx_bilhetes_dono_codigo` em `database.py:178-181` |
| #22 | 🔴 "delete em massa sem limite" | **Fechado por outro caminho** — `lixeira_contas` (`database.py:362`) + confirmação reconferida no servidor |
| #36 | 🔴 "Google Fonts externo" | **Fechado** — zero `fonts.googleapis` em `app/static/`; `app/static/fonts.css` + 4 `.woff2` self-hosted |

Todos **verificados por `grep` hoje**. O próprio `AUDITORIA_TURBO_2026-07-19` já tinha
registrado isso como achado **#23** ("itens já resolvidos ainda listados como abertos").

### C5 — Cinco achados que a `AUDITORIA_2026` mostra abertos e que **continuam** abertos

Verificados hoje, para o backlog não perder nada de verdade:

| # | Estado medido |
|---|---|
| #32 | `_calc_odd` (`polymarket.py:894`) ainda devolve um só número — o comentário na `:987` admite "odd de entrada, **ou** a efetiva na liquidação". **Aberto.** |
| #44 | zero ocorrências de `request_id` em `app/*.py`. **Aberto.** |
| #16 | `SELECT *` em `repository.py`: eram 2, hoje são **6**. **Piorou.** |
| #10 | `scripts/import_lava.py:23` ainda tem `CSV_PATH = r'C:\Users\Fernando\...'`. **Aberto.** |
| #37 | 5 `confirm(` em `app/static/index.html`. **Aberto.** |

### C6 — Qual é a fonte de verdade do backlog

Quatro arquivos reivindicam o papel, e nenhum concorda com o outro:

- `ONDE_ESTOU.md`: *"Fonte de verdade ATUAL do backlog: `AUDITORIA_TURBO_2026-07-19.md`"*
- `Ideias/README.md`: *"Índice mestre de tudo que é plano, estudo ou ideia futura"*
- `docs/AUDITORIA_2026.md`: *"a partir daqui, a fonte de verdade do estado de risco é este arquivo"*
- `STATUS.md §5`: 51,4 KB de pendências **varridas contra o código em 10/08 (s261)** — de longe a mais recente e a mais rigorosa (ela inclusive documenta o método: ✅ VIVA / NÃO-MEDIDA / HUMANA).

**Correto hoje: o `STATUS §5` é o único backlog com varredura recente.** Os outros três
descrevem o projeto entre 30/06 e 19/07.

### C7 — Link markdown quebrado (1, e é o único)

`docs/HISTORICO.md` contém um link para `docs/HISTORICO.md` escrito de dentro de `docs/`
— resolve para `docs/docs/HISTORICO.md`, que não existe. Já estava registrado como achado
**#24** do `AUDITORIA_TURBO_2026-07-19` ("link quebrado no HISTORICO"); a parte de mover os
planos foi feita, esta não. **Conserto: 1 linha.**

> Fora dos links markdown, `docs/auditoria_turbo/findings.json` cita
> `docs/docs/PLANO_EXTRACAO_WORLDWIDE.md` (mesmo erro de prefixo). É dado de auditoria, não
> navegação — anoto e não mexo.

### C8 — O invariante #4 do `CLAUDE.md` nunca foi cumprido

O `CLAUDE.md` manda: *"copiar para o backup só os arquivos que serão editados — **nunca**
`docs/HISTORICO.md`… podar snapshots além de ~últimas sessões / 90 dias"*.

**Medido:** `Backups/` tem **143 cópias de `STATUS.md`** e **22 de `HISTORICO.md`**, somando
**21,2 MB — 17 % da pasta inteira**. E o corte de 90 dias **não corta nada**: o snapshot
mais antigo é de 2026-06, dentro da janela. Os dois critérios do invariante se anulam na
prática (§ Lote A).

---

## 1.3 Classificação — as cinco caixas

### VIVO (fica onde está, ou vira o novo backlog)

| Arquivo | Por quê |
|---|---|
| `CLAUDE.md` | Regras vinculantes (Lote E encolhe, não move) |
| `STATUS.md` | Estado atual (Lote B corta, não move) |
| `docs/HISTORICO.md` | Registro (Lote C particiona) |
| `docs/PLANO_MULTIUSUARIO_2026.md` | Fase 4 aberta |
| `docs/PLANO_TRADUTOR_DETERMINISTICO.md` | Fases 1-4 abertas; citado por `app/tradutor.py` |
| `docs/PLANO_TIPSTER.md` | P1/P2/P3 abertos; citado por 2 testes e 2 módulos |
| `docs/PLANO_EXTRACAO_WORLDWIDE.md` | Fases 1-5 abertas; citado por `database.py` e `STATUS §5` |
| `docs/PLANO_CASCA_UNIFICADA.md` | Fatia 3 aberta |
| `docs/PLANO_POLY_INCREMENTAL.md` | Não executado (sem marca d'água em `polymarket.py`) |
| `docs/PLANO_DASHBOARD_C.md` | Condicional, decisão do Feca pendente |
| `docs/PLANO_INFERENCIA_POR_CAMPO.md` | Sem código |
| `docs/PLANO_INTELIGENCIA_TIPSTER.md` | ⚠️ vivo **mas defasado** — ver nota abaixo |
| `docs/ESTUDO_PRECIFICACAO_2026.md` | Correção B ainda bloqueada |
| `docs/GUIA_BOT_TIPSTER.md` | Procedimento em uso (s316-317) |
| `docs/AUDITORIA_TURBO_2026-07-20.md` | ⚠️ **95 achados sem tracker** — ver nota abaixo |

> **`PLANO_INTELIGENCIA_TIPSTER`:** descreve o matcher **v5** de 15/07. Desde então o
> matcher ganhou o corte de valor redondo e `valores.size===1` (s221), o peso declarativo
> (s289) e a volta do declarado onde a base é cega (s310). O doc não é falso, é **velho**.
> Proponho manter em `docs/` com um banner de data na 1ª linha, e **não** arquivar — a tese
> dele (o resolvedor) segue aberta.
>
> **`AUDITORIA_TURBO_2026-07-20`:** é o único doc que não consigo classificar honestamente
> sem uma sessão própria. São **95 achados confirmados**, sem nenhum tracker. Amostrei 4 dos
> 17 ALTOS: **A1 aberto** (`resultado_login` roda `bcrypt` **fora** de `to_thread` no `POST
> /login`, `main.py:1962` — embora `/signup` e a troca de senha já usem `asyncio.to_thread`),
> **A4 parcialmente fechado** (há 413 por imagem/PDF/total, mas depois do parse),
> **B2 aberto** (`index.html:5324` ainda manda `xlsFiles[0]`), **A2 aberto** (sem cache no
> `extensao_download`). **Proposta: não arquivar.** Ver a pergunta P3 em §1.6.

### REFERÊNCIA (fica; confira o conteúdo)

| Arquivo | Ainda bate com o código? |
|---|---|
| `docs/SHARPENUP_ARQUITETURA.md` | ✅ sim (gate `audit_sharpenup.py` verde) |
| `docs/GUIA_CASA_SHARPENUP.md` | ✅ sim |
| `docs/GUIA_NOVA_CASA.md` | ✅ sim (gate `audit_casas.py` verde) |
| `docs/GUIA_RECON_TESTER.md` | ✅ sim (`tools/recon_casa.js` existe) |
| `docs/UI_REFERENCE.md` | ⚠️ **sim no §5**, mas há conflito com a Escada de Tinta sobre cor de label. Vale uma linha de reconciliação, sem mudar regra |
| `docs/SHELL_SPEC.md` | ✅ sim (`check-tokens.mjs` referencia) |
| `docs/REFERENCIA_CHIPS_CASAS.md` | ✅ autocontida |
| `docs/REFERENCIA_EMOJIS_ESPORTES.md` | ✅ autocontida |
| `docs/REFERENCIA_LISTA_APOSTAS.md` | ✅ autocontida |
| `docs/ADR-001-…` / `ADR-002-…` | ✅ decisões com gate, status honesto |
| `docs/runbook-rotacao-postgres.md` | ✅ procedimento; execução pendente |
| `docs/marketing/README.md` | ✅ **load-bearing** (`tests/test_landing.py` cita a regra) |
| `docs/GUIA_CREDENCIAIS_LOGIN_SOCIAL.md` | ⚠️ Google ok; **Telegram saiu do `/login` na s324** e o guia não sabe — 2 linhas |
| `docs/CASAS_CONFIABILIDADE.md` | ⚠️ 13 casas de 28. **Espelho parado** — ver P4 |
| `extensor/README.md`, `extensor/harness/README.md`, `golden_set/README.md`, `tools/eval_zeroshot/README.md` | ✅ todos batem |

### HISTÓRICO → `docs/arquivo/`

| Arquivo | Nome proposto em `docs/arquivo/` | Onde o resultado vive hoje |
|---|---|---|
| `ONDE_ESTOU.md` | `2026-07-19_ONDE_ESTOU.md` | Estado → `STATUS.md`; backlog → `BACKLOG.md` |
| `Ideias/README.md` | `2026-07-11_IDEIAS_INDICE.md` | Índice de planos → `BACKLOG.md` §Planos |
| `docs/AUDITORIA_CRITICA_2026-07-02.md` | `2026-07-02_AUDITORIA_CRITICA.md` | Já declarado histórico pelo próprio `AUDITORIA_2026` |
| `docs/RELATORIO_CORRECOES_2026-07-03.md` | `2026-07-03_RELATORIO_CORRECOES.md` | Idem |
| `docs/RISK_REDUCTION_PLAN.md` | `2026-07-03_RISK_REDUCTION_PLAN.md` | Idem |
| `docs/AUDITORIA_VISUAL_CASCA_2026-06-30.md` | `2026-06-30_AUDITORIA_VISUAL_CASCA.md` | Punch-list superado; resto → `PLANO_CASCA_UNIFICADA` Fatia 3 |
| `docs/PLANO_CONSTRUCAO.md` | `2026-06_PLANO_CONSTRUCAO.md` | Auto-declarado histórico; Fase 5 → `PLANO_TIPSTER` P3 |
| `docs/PESQUISA_BADMINTON_2026.md` | `2026-07-21_PESQUISA_BADMINTON.md` | Badminton aplicado nos 3 MASTERs (s245) |
| `docs/DESAMBIGUACAO_RAQUETE_2026.md` | `2026-07-21_DESAMBIGUACAO_RAQUETE.md` | Idem — mas **confirmar o que sobrou** antes de mover (P5) |
| `docs/auditoria_turbo/` (11 arq.) | `docs/arquivo/auditoria_turbo_2026-07-19/` | Anexos de UMA auditoria; só ela os linka |

### EXECUTADO → `docs/arquivo/`, com a linha "onde o resultado vive hoje"

| Arquivo | Prova de execução (medida hoje) | Resultado vive em |
|---|---|---|
| `docs/PLANO_UNIFICACAO_2026.md` | `STATUS §4`: "migração planilha → Postgres completa e reconciliada" | `STATUS §4` + `scripts/import_*.py` |
| `docs/PLANO_BET365_CAPTURA_API.md` | `extensor/b3_inject.js` existe; Bet365 = robô no `audit_sharpenup` | `casas/CASA_BET365.md` + `extensor/b3_inject.js` |
| `docs/PLANO_POLY_PERSISTIR_ATIVAS.md` | `polymarket.py:1058` `_derivar_ativas` + `:966` "ativa → `extraction_state 'aberta'`, sem P/L" | `app/polymarket.py` + `casas/CASA_POLYMARKET.md` |
| `docs/AUDITORIA_SHARPENUP_2026-07-25.md` | O padrão que ela pedia existe: `GUIA_CASA_SHARPENUP.md` (12 pontos), `SHARPENUP_ARQUITETURA.md`, `tools/audit_sharpenup.py` **verde**, 4 skills `/sharpenup-*` | os 2 guias + o gate |
| `docs/AUDITORIA_2026.md` | ⚠️ **caso especial** — ver abaixo |
| `docs/AUDITORIA_TURBO_2026-07-19.md` | ⚠️ **caso especial** — ver abaixo |

#### `AUDITORIA_2026.md` — executada em parte, e **defasada demais para ficar como está**

50 achados. Estado real: **16 fechados** conforme ela mesma diz, **+5 fechados que ela não
sabe** (C4), **5 que confirmei abertos** (C5), e ~24 não reverificados hoje.

Ela **não pode continuar sendo "a auditoria viva"** — o rótulo é o problema, mais do que o
conteúdo. **Proposta:** arquivar como `2026-07-10_AUDITORIA_2026.md`, e o **que sobrou vivo
migra para o `BACKLOG.md`** com o número original preservado (`#32`, `#44`, `#16`, `#10`,
`#37`, `#1` rotação do Postgres, `#19`, `#20`, `#28`, `#38`, `#39`, `#47`, `#48`, `#50`).
Sem varredura, arquivar isso **perde backlog** — é a linha vermelha do briefing.

#### `AUDITORIA_TURBO_2026-07-19.md` — 25 achados, e 6 ainda vivos

| # | Achado | Estado medido hoje |
|---|---|---|
| #1/#2 | Custo de tipster → Postgres | ✅ **FEITO** — `custo_tipster JSONB` em `database.py:334` |
| #3, #4, #5 | schema banco vazio · `/polymarket/sync` tenancy · `fmtPL` zero neutro | ✅ FEITO (tracker s158) |
| #6 | Tooltip de Esportes vaza HTML cru | ⚠️ **a confirmar** — a função mudou de lugar (`performance.js:1165-1166` monta `.money` como string); precisa de olho na tela, não de grep |
| #7, #8, #9, #10 | SESSION_SECRET · XFF · `.dockerignore` · `test_auth.py` | ✅ FEITO (verificado no código) |
| #11 | Harness de camada-DB real | ✅ FEITO (tracker s160; 30 skipped hoje = os testes gateados em `TEST_DATABASE_URL`) |
| #12 | Índices em `bilhetes` | ✅ FEITO (verificado) |
| #13 | Autodiagnóstico universal das casas-robô | ✅ FEITO (tracker s160) |
| #14 | `domain.py` | ✅ **MORTO por decisão** (s160: premissa obsoleta) |
| **#15/#16** | **Solidez: gate de rentabilidade + separar força do sinal** | 🔴 **ABERTO** — tentado e **revertido** (`9394553`); requer sessão dedicada de redesenho |
| #17 | Win rate HW=½ backend=front | ✅ FEITO (`1360bbf`/`0941bf7`) |
| #18 | Backtest sem split temporal | 🔴 **ABERTO** — roteado à frente de tipster; a regra "assinatura tem ERA" já está no `CLAUDE.md`, o holdout temporal não foi construído |
| #19 | Separador de bet builder | ✅ FEITO (` // ` único, no `CLAUDE.md`) |
| #20 | 3 lacunas de propagação nos masters | ✅ FEITO (`40deee0`, aprovado) |
| **#21** | **Popular `golden_set/bilhetes/`** | 🔴 **ABERTO** — `golden_set/` tem só `descricoes.jsonl` e o README. Bloqueado em prints do Feca |
| **#22** | **Docs de consolidação defasados** | 🔴 **ABERTO — é exatamente esta faxina** |
| **#23** | **Itens resolvidos ainda listados como abertos** | 🔴 **ABERTO — é o C4 acima** |
| #24 | 2 planos na raiz + link quebrado + `NOTA_AO_AUDIT` | 🟡 **parcial** — planos movidos (`0d528a0`), `NOTA` removida, **link continua quebrado** (C7) |
| **#25** | **`Backups/` sem retenção** | 🔴 **ABERTO — é o Lote A** |

**Proposta:** os 6 vivos (#6, #15/#16, #18, #21, #22/#23/#24-link, #25) saem para o
`BACKLOG.md`, e só então o arquivo vai para `docs/arquivo/2026-07-19_AUDITORIA_TURBO.md`
junto com os 11 anexos `gerente_*`.

### ÓRFÃO — **pergunto antes de mover** (regra do briefing)

São os `.md` que **nenhum documento vivo e nenhum código menciona** — só o `HISTORICO.md`
os cita, e citação no histórico é registro, não uso:

| Arquivo | Tam. | Quem menciona |
|---|---|---|
| `docs/AUDITORIA_TURBO_2026-07-20.md` | 17,1 KB | só `HISTORICO.md` |
| `docs/AUDITORIA_SHARPENUP_2026-07-25.md` | 18,1 KB | só `HISTORICO.md` |
| `docs/DESAMBIGUACAO_RAQUETE_2026.md` | 16,2 KB | só `HISTORICO.md` |
| `docs/GUIA_CREDENCIAIS_LOGIN_SOCIAL.md` | 6,2 KB | só `HISTORICO.md` |
| `docs/REFERENCIA_LISTA_APOSTAS.md` | 13,7 KB | só `HISTORICO.md` |

> ⚠️ **Órfão ≠ inútil.** O `GUIA_CREDENCIAIS` é o único lugar que diz como acordar o login
> Google; a `REFERENCIA_LISTA_APOSTAS` é spec autocontida de uma tela que existe. Eles são
> órfãos de **link**, não de **valor** — proponho **manter e linkar**, não arquivar. As
> perguntas concretas estão em §1.6.

---

## 1.4 Estrutura final proposta

### O desenho: um arquivo, uma pergunta

| Pergunta | Arquivo | Teto |
|---|---|---|
| "Que regras eu **não posso** quebrar aqui?" | `CLAUDE.md` | **40 KB** |
| "Onde o projeto **está** agora?" | `STATUS.md` | **40 KB / 400 linhas** |
| "O que está **aberto** e o que vem a seguir?" | **`BACKLOG.md`** *(novo, na raiz)* | sem teto — é o inventário |
| "Como se **faz** X?" | `docs/GUIA_*.md`, `docs/*_SPEC.md`, `docs/REFERENCIA_*.md`, `docs/ADR-*.md`, `docs/runbook-*` | — |
| "O que foi **decidido/planejado** e ainda não terminou?" | `docs/PLANO_*.md` **vivos** | — |
| "O que **aconteceu**?" | `docs/historico/HISTORICO_sNNN-sMMM.md` + `docs/HISTORICO.md` (índice) | — |
| "O que **foi** verdade e virou registro?" | `docs/arquivo/` + `docs/arquivo/README.md` (1 linha por arquivo) | — |

### `CLAUDE.md` — regra + link, nunca a narrativa inteira

Hoje: 65,9 KB em 25 seções. As 5 maiores somam **25,7 KB** e cada uma é **uma regra** com
3 a 8 parágrafos de caso (bilhete, casa, valor em R$, número da sessão):

| Seção | Hoje |
|---|---|
| Regras de deduplicação (sistema) | 6.421 B |
| ⚠️ REGRA DE UI / MARCA OBRIGATÓRIA | 5.125 B |
| Gate que confere UM campo deixa os vizinhos livres | 4.690 B |
| Escada de Tinta | 4.451 B |
| Caixa Inteligente | 4.028 B |

**Método proposto (e o motivo de este ser o último lote):** a narrativa **não some** — ela
vai para `docs/CASOS.md`, um arquivo novo, e a seção do `CLAUDE.md` fica com **a regra em
forma imperativa + um ponteiro `docs/CASOS.md#ancora` (arquivo a criar no Lote E)**. Ganho estimado: **−25 KB**, para
~40 KB. Nenhuma regra sai; a prova disso é o gate de diff de regras.

Duas coisas saem de vez, sem virar caso:
- o rodapé `VERSÃO: 2026 / ATUALIZADO: …` (**2,2 KB**) — é changelog de sessão dentro de um
  arquivo de regras, e o `STATUS.md` já faz isso melhor;
- as tabelas de "Estrutura do projeto" e "Onde encontrar o quê", que duplicam `STATUS §3`.

### `STATUS.md` — o formato que o `/encerrar` já manda

> O ritual `/encerrar` **já diz**: *"o changelog no topo tem o estado atual + no máximo as
> 3 últimas sessões"*, e tem até uma salvaguarda que reconhece este repo:
> *"se o STATUS já estiver muito acima de ~150 linhas de changelog… avise que precisa de
> faxina dedicada"*. **A regra existe. O Lote B é só executá-la.**

```
STATUS.md  (alvo ~40 KB / ~400 linhas)
├─ cabeçalho: _Atualizado:_ + NO MÁXIMO 2 _Anterior:_        (~5 KB, hoje 66,9 KB)
├─ ## Onde parei (fim da sessão N)                            (intacto)
├─ ## Sessão N-1 / ## Sessão N-2                              (~12 KB, hoje 57,2 KB)
├─ §1 construção · §2 invariantes · §3 estrutura · §4 estado  (~4 KB, intactos)
├─ §5 → vira "Pendências: ver BACKLOG.md" + as 3 mais quentes (~1 KB, hoje 51,4 KB)
└─ §6 rodar · §7 workflow                                     (~3,3 KB, intactos)
```

### `BACKLOG.md` — o arquivo que hoje não existe

É a peça central da faxina. Ele **absorve** (não copia — a origem passa a apontar para cá):

| Origem | O que entra |
|---|---|
| `STATUS §5` (51,4 KB) | inteiro, com as marcas ✅ VIVA / NÃO-MEDIDA / HUMANA preservadas |
| `AUDITORIA_TURBO_2026-07-19` | #6, #15/#16, #18, #21, #22, #23, #24-link, #25 |
| `AUDITORIA_2026` | os ~14 achados abertos, com o número original |
| `AUDITORIA_TURBO_2026-07-20` | **pendente da decisão P3** |
| `ONDE_ESTOU §4` e `§5` | o que sobrar depois de tirar o já fechado |
| `Ideias/README` | a tabela de planos vivos, com horizonte 🟢🟡🔵 |

Organizado por **natureza**, porque é assim que se decide o que fazer:
`Bloqueado por humano` · `Bloqueado por amostra/bilhete real` · `Decisão do Feca pendente` ·
`Dívida técnica medida` · `Planos com fase aberta` · `Não medido`.

### `docs/HISTORICO.md` → índice + partições

Hoje são 1,18 MB em 4 seções com faixas **sobrepostas** (são logs paralelos de origens
diferentes, não um contínuo):

| Seção atual | Faixa | Bytes |
|---|---|---|
| corpo | s315 → s243 | 382 KB |
| "Changelog — cadeia `_Anterior_`" | s242 → s61 | 684 KB |
| "Log (antigo §4 Estado atual)" | s62 → s14 | 76 KB |
| "Log (antigo §6 Próxima sessão)" | s43 → s24 | 34 KB |

Proposta:

```
docs/HISTORICO.md                              ← vira ÍNDICE (~3 KB)
docs/historico/HISTORICO_s243-s327.md          ← corpo atual + o que sair do STATUS
docs/historico/HISTORICO_s151-s242.md          ┐ a cadeia _Anterior_ partida ao meio
docs/historico/HISTORICO_s061-s150.md          ┘  (~340 KB cada)
docs/historico/HISTORICO_s014-s062_estado.md   ← log paralelo, preservado como está
docs/historico/HISTORICO_s024-s043_proximo.md  ← log paralelo, preservado como está
```

Os dois últimos mantêm o nome com sufixo porque **não** são a mesma série — fundi-los
inventaria uma ordem que não existe.

### `docs/arquivo/`

```
docs/arquivo/README.md            ← uma linha por arquivo: o que era, quando, onde o resultado vive
docs/arquivo/2026-07-19_ONDE_ESTOU.md
docs/arquivo/2026-07-11_IDEIAS_INDICE.md
docs/arquivo/2026-07-02_AUDITORIA_CRITICA.md
… (a lista de §1.3)
docs/arquivo/auditoria_turbo_2026-07-19/gerente_*.md
```

### `ONDE_ESTOU.md` e `Ideias/` — a decisão

**Proposta: os dois morrem como arquivos vivos.** Não fundir — o conteúdo deles já está
espalhado em 3 lugares melhores.

- `ONDE_ESTOU.md` → `docs/arquivo/2026-07-19_ONDE_ESTOU.md`. O que ele fazia bem (o retrato
  de saúde da §2, a lista do que está firme na §3) é o que o `STATUS` já faz melhor e mais
  recente. O que ele fazia mal (backlog de 11/07 com frentes já fechadas) vai corrigido para
  o `BACKLOG.md`.
- `Ideias/README.md` → `docs/arquivo/2026-07-11_IDEIAS_INDICE.md`, e a tabela de planos vira
  a seção "Planos com fase aberta" do `BACKLOG.md`.
- **A pasta `Ideias/` continua existindo** com os 2 PDFs de estudo de negócio (503 KB), que
  não têm outro lar. Entra um `Ideias/README.md` novo de **5 linhas**, dizendo só o que são
  os PDFs e apontando para o `BACKLOG.md`.

**Motivo de não fundir os dois num "ONDE_ESTOU vivo":** a causa da defasagem não foi
descuido, foi **falta de gatilho**. `STATUS.md` e `CLAUDE.md` têm ritual (`/encerrar`,
invariante #7); `ONDE_ESTOU` e `Ideias` nunca tiveram. Criar um terceiro arquivo sem ritual
reproduz o problema em 8 semanas. O `BACKLOG.md` só sobrevive se o `/encerrar` passar a
tocá-lo — o que exige editar `~/.claude/commands/encerrar.md`, **fora do escopo desta
faxina** e que eu levanto como pergunta (P6).

---

## 1.5 Custo e ganho

### Hoje — o que uma sessão nova lê antes de escrever a primeira linha

| Fonte | KB | Obrigatório? |
|---|---|---|
| `FDC Capital/CLAUDE.md` | 2,4 | auto-carregado |
| `Planilhador/CLAUDE.md` | **65,9** | auto-carregado |
| `MEMORY.md` (índice de memórias) | 19,4 | auto-carregado |
| `STATUS.md` | **187,6** | o próprio arquivo manda: *"quem abrir o Claude Code neste repo lê isto primeiro"* |
| **Total** | **275,3 KB** | ≈ **78 mil tokens** de prosa pt-BR |

### Depois

| Fonte | KB |
|---|---|
| `FDC Capital/CLAUDE.md` | 2,4 |
| `Planilhador/CLAUDE.md` | **40** (−26) |
| `MEMORY.md` | 19,4 (fora do escopo) |
| `STATUS.md` | **40** (−148) |
| **Total** | **101,8 KB** ≈ **29 mil tokens** |

**Economia: 173,5 KB / ~49 mil tokens por abertura de sessão — 63 %.**
Em janela de 1M isso é ~5 % do contexto; o ganho real não é a janela, é **quanto do começo
da conversa é história que ninguém vai usar**.

### Onde o ganho é menor do que parece — e eu prefiro dizer

1. **O `BACKLOG.md` não é economia, é mudança de lugar.** Os 51,4 KB do `STATUS §5` não
   encolhem; deixam de ser lidos *sempre* e passam a ser lidos *quando se escolhe trabalho*.
   Se você abre o backlog em toda sessão, a economia cai de 173 KB para ~122 KB (44 %).
2. **`Backups/` (Lote A) economiza 0 KB de leitura.** A pasta é **gitignored** — não entra em
   contexto, não entra no deploy (`.dockerignore` cobre), não entra no git. Recupera ~100 MB
   de disco e cumpre um invariante escrito. **Não tem commit** e não acelera sessão nenhuma.
3. **`docs/HISTORICO.md` (Lote C) também economiza 0 KB de leitura hoje** — ninguém o lê
   inteiro; ele já é consultado por `grep`. Particionar melhora o `grep` e permite abrir uma
   faixa sem carregar 1,18 MB. É ganho de **manuseio**, não de contexto.
4. **O Lote E é o de maior ganho e maior risco.** −26 KB em toda sessão, e é literalmente o
   arquivo de regras. Por isso ele vai por último, item a item, com o diff de regras.

### Vale a pena?

**Sim, e a maior parte do valor não está em bytes.** Está no C6: hoje **quatro arquivos
dizem ser a fonte do backlog e nenhum concorda**, e três deles descrevem o projeto de
30/06 a 19/07. Uma sessão que acredita no `ONDE_ESTOU` vai construir a Fase 1 do
multiusuário que está no ar desde a s233. Isso já quase aconteceu: a varredura da s261
registra que *"a primeira pendência que eu fui atacar já estava feita desde 26/07"*.

**Se você quiser fazer só metade:** os Lotes **B** (STATUS) e **F** (backlog único) entregam
~85 % do valor. Os Lotes A, C e D são higiene. O Lote E é o mais caro e o mais arriscado —
e é legítimo adiá-lo.

---

## 1.6 Perguntas que preciso responder antes da Fase 2

**P1 — `Backups/`: qual corte?** Os dois critérios do invariante #4 se anulam: "90 dias"
não corta nada (nada é mais velho que 2026-06) e "últimas ~10 sessões" corta quase tudo.
Medido:

| Corte | Fica | Sai |
|---|---|---|
| últimas 10 sessões (s ≥ 318) | 13 pastas · 4,3 MB | 538 pastas · 123,8 MB |
| últimas ~20 (s ≥ 310) | 26 · 9,4 MB | 525 · 118,7 MB |
| **últimas ~30 (s ≥ 300)** | 37 · 13,0 MB | 514 · 115,0 MB |
| últimas ~40 (s ≥ 290) | 50 · 20,5 MB | 501 · 107,6 MB |
| só tirar `STATUS.md`/`HISTORICO.md` de dentro dos snapshots | tudo | 165 arquivos · **21,2 MB** |

Minha recomendação: **s ≥ 300 + remover as 165 cópias de `STATUS`/`HISTORICO` de todos os
snapshots que ficarem**. Recupera ~115 MB e deixa 30 sessões de rede. Você decide o número.

> ⚠️ 396 das 551 pastas **não têm prefixo `sNNN`** (nomes como
> `backfill-criado-em-import-20260628_230659`, `zoraesports-conta-slug`) e somam 74,5 MB.
> Para elas o corte teria de ser por **data de modificação**. Confirmo a regra com você antes.

**P2 — Os 5 órfãos de link.** Recomendo **manter e linkar** (`GUIA_CREDENCIAIS` e
`REFERENCIA_LISTA_APOSTAS` têm valor de uso; `AUDITORIA_TURBO_2026-07-20` tem backlog).
Arquivar algum deles?

**P3 — `AUDITORIA_TURBO_2026-07-20` (95 achados, sem tracker).** Três caminhos:
(a) sessão própria de reconciliação item a item, antes desta faxina; (b) migrar só os **17
ALTOS** para o `BACKLOG.md` e arquivar o resto com um aviso de "não reconciliado";
(c) deixar o arquivo em `docs/` como está, com banner de data. **Recomendo (b)** — os 4 que
amostrei mostram que há coisa real aberta lá, e reconciliar 95 achados é uma sessão inteira
que não é esta.

**P4 — `CASAS_CONFIABILIDADE.md`.** Espelha 13 de 28 casas. Atualizar (fora do escopo, mexe
em leitura de `casas/`), arquivar, ou deixar com banner de data?

**P5 — `DESAMBIGUACAO_RAQUETE_2026`.** O Badminton foi aplicado (s245), mas o doc traz
rosters de Dardos e Tênis que podem não ter entrado. Confirmo contra o `MASTER_ESPORTES §7`
antes de arquivar? (é leitura, não edição — não fere a regra de não tocar em `global/`).

**P6 — O ritual.** O `BACKLOG.md` só não apodrece se algo o tocar toda sessão. O
`/encerrar` mora em `~/.claude/commands/encerrar.md`, **fora deste repo** — e o briefing
proíbe mexer em `.claude/commands/`. Quer que eu (a) proponha o texto e você cola, (b)
registre a obrigação como invariante #10 no `CLAUDE.md` do projeto, ou (c) as duas?

**P7 — Ordem dos lotes.** O briefing pede A → B → C → D → E → F. Sugiro **trocar F e B de
ordem**: criar o `BACKLOG.md` (F) **antes** de cortar o `STATUS` (B), porque o §5 é a origem
do backlog e cortá-lo antes de o destino existir é justamente o jeito de perder pendência.
Ordem proposta: **A → F → B → C → D → E**.

---

## Gates que rodarão ao fim de cada lote (baseline de hoje)

| Gate | Baseline 2026-09-06 |
|---|---|
| `python -m pytest tests/ -q` | **756 passed, 30 skipped** |
| `python tools/audit_casas.py` | **28 OK, sem FAIL** |
| `python tools/audit_sharpenup.py` | **sem FAIL** (26 robô + 3 print) |
| links markdown quebrados | **1** (C7) → alvo **0** |
| diff de regras do `CLAUDE.md` | 25 seções de nível 2 — lista item a item no Lote E |

---

_Fim da Fase 1. Nada foi escrito além deste arquivo. Aguardando aprovação e as respostas
de P1 a P7._

---

## Anexo A — texto proposto para o `/encerrar` (P6, item _a_)

> O `/encerrar` mora em `~/.claude/commands/encerrar.md`, **fora deste repo**. O texto
> abaixo é para o Feca colar. A mudança é de **duas linhas**: o passo 2 passa a tocar o
> `BACKLOG.md`, e o passo 4 passa a rodar o gate.

No **passo 2 (Anota)**, depois da linha que fala do STATUS enxuto, acrescentar:

```
- PENDENCIA NOVA VAI PARA O BACKLOG.md, nunca para o STATUS.md. O STATUS
  responde "onde o projeto esta"; o BACKLOG responde "o que esta aberto".
  Item que FECHOU nesta sessao sai do BACKLOG.md na mesma sessao: se virou
  regra, vai para o lugar canonico (MASTER_* / CASA_* / CLAUDE.md); se virou
  historia, vai para docs/HISTORICO.md.
```

No **passo 4 (Limpa)**, antes do `git add -A`:

```
- Rode `python tools/check_docs.py`. Se der FAIL, conserte ANTES de commitar —
  e o gate do invariante #10 (tamanho do STATUS, copia em Backups/, link
  quebrado). Ele nao le conteudo: STATUS de 39 KB so de historia passa.
```

A **SALVAGUARDA** do passo 2 ("se o STATUS já estiver muito acima de ~150 linhas de
changelog, não tente reorganizar sozinho") pode sair depois do Lote B — ela existia
justamente porque este repo nunca tinha passado pela faxina.
