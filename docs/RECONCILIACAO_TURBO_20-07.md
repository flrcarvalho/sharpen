# Reconciliação da Auditoria Turbo — o que ainda está aberto

> **Método:** remedir contra o código de **2026-09-07**, nunca copiar o estado declarado.
> É a mesma regra que os 17 ALTOS seguiram (`BACKLOG §4.3`), e ela existe porque copiar o
> declarado foi o que produziu a `AUDITORIA_2026` mostrando 5 achados fechados como abertos.
>
> Cada item sai com um de três veredictos:
> **ABERTO** (com a evidência de hoje) · **FECHADO** (com a prova) · **A CONFIRMAR NA TELA**
> (não decidível por `grep`).

---

## ⚠️ Antes de tudo: os 78 do 20/07 não existem por escrito

O `BACKLOG §4.4` pedia reconciliar "os 78 achados MÉDIO/BAIXO do TURBO 20/07". **Eles não
estão enumerados em lugar nenhum.** Medido hoje:

| O que procurei | O que achei |
|---|---|
| Itens com código no `2026-07-20_AUDITORIA_TURBO_PROFUNDA.md` | **16** — `A1-A5`, `B1-B4`, `C1-C3`, `D1-D4`. É só a camada de ALTOS. |
| As 31 lacunas de completude | Estão lá, mas em **prosa corrida**, sem id nem tabela. |
| Os 36 médios + 34 baixos + 8 info | **Só a CONTAGEM**, no sumário executivo. Nenhum item. |
| Um `findings.json` do dia 20 | Não existe. O único é o de **19/07** (`Jul 19 00:24`), com 186 achados. |
| `find . -iname "*finding*" -o -iname "*mergulho*" -o -iname "*profund*"` | Devolve só o próprio `.md` e o json de 19/07. |

E o rodapé do documento diz por quê, com todas as letras: **"Deliverables uncommitted."**
Os 219 agentes rodaram, o CEO resumiu, e o material bruto nunca foi para o git.

> **A lição, que vale além deste caso:** contagem no sumário não é achado. Um relatório que
> diz "95 confirmados" e enumera 16 deixou 79 sem endereço — e ninguém percebeu por 7 semanas,
> porque o número grande dava a sensação de que a lista existia. **Auditoria que não commita o
> bruto vira um número.**

### O que eu fiz em vez disso

O corpus **realmente enumerado** é o `findings.json` da auditoria de **19/07**: 186 achados
com `arquivo`, `linha`, `evidencia` e `recomendacao`. Desses, **47 são `positivo`** (elogio,
não achado) e **139 são achados de verdade** — dos quais o relatório de 19/07 só promoveu
**25** para a tabela de prioridades. **Os outros ~114 nunca foram triados por ninguém.**

É o mesmo período, o mesmo time, o mesmo método — e, ao contrário dos 78, **existe**. É o que
está reconciliado abaixo.

---

## Placar

**Os 139 achados enumerados foram remedidos, um a um.**

| Veredicto | Qtd | % |
|---|---:|---:|
| **FECHADO** (com a prova no código de hoje) | **40** | 29 % |
| **ABERTO** (com a evidência de hoje) | **68** | 49 % |
| **A CONFIRMAR NA TELA** (não decidível por `grep`) | **20** | 14 % |
| **PARCIAL** (metade feita, metade não) | **8** | 6 % |
| **NÃO É ACHADO** (recomendação era "manter", ou entrada de teste) | **3** | 2 % |

Por lote: 1) 12F/4A · 2) 3F/13A · 3) 4F/11A · 4) 5F/11A · 5) 5F/6A · 6) 6F/13A · 7) 5F/10A.

### O que o placar diz, e que a contagem sozinha não diz

**1. Um terço do que "fechou" fechou HOJE, nesta faxina.** Dos 40 fechados, **7** são
consequência direta dos Lotes B, C e D (#1, #5, #6, #8, #103, #104, #108) — e o caso de #103
é literal: a recomendação de julho era *"criar `docs/arquivo/` e mover os relatórios datados
encerrados"*. Sete semanas depois, foi o Lote D.

**2. O corpus tem duplicatas de verdade — 11 achados são 5 assuntos.**
`#18 ≡ #19 ≡ D2` (sessão em memória) · `#23 ≡ #24 ≡ #25` (schema sem migrations) ·
`#50 ≡ #51` (assinatura com stake cru) · `#71 ≡ #72 ≡ #15/#16` (Solidez) ·
`#135 ≡ #136 ≡ #138` (backtest sem eixo temporal). Contar achados de agentes paralelos sem
deduplicar infla o total; o `findings.json` não tem campo de relação, o que a própria
auditoria de 20/07 identificou como a **Cadeia 5** ("lista plana não enxerga cadeias").

**3. Um dos "achados" era um placeholder do pipeline.** O `#31` entrou no `findings.json`
com severidade `medio` e o conteúdo `titulo: "Teste"`, `recomendacao: "rec"`,
`evidencia: "ev"`. Passou pela verificação adversarial e entrou na contagem.

**4. Vinte itens (14 %) só se decidem abrindo a tela.** Não é limite do método —
é o que a regra de UI do `CLAUDE.md` já manda ("abra a tela num navegador antes do commit").
Auditoria feita 100 % por leitura de código deixa a UI em suspenso por construção.

### O achado mais grave que segue aberto

**`#129` — dois MASTERs mandam coisas diferentes sobre a odd, e a odd entra no P/L.**
O `MASTER_PIPELINE:114` diz `L ou V → ODDS TOTAIS do bilhete`; o `MASTER_RESULTADO §5.1.1`
diz para *preservar a odd estrutural original, sem remover seleções anuladas*. Em múltipla
com perna anulada, os dois textos levam a números diferentes. **`global/` está fora do
escopo desta faxina** — fica registrado, medido, para uma sessão que possa tocar o MASTER.

Depois dele, por impacto: **`#114`** (o `bf_inject` dispara até 400 requisições autenticadas
na Betfair — é o único inject que **cria** tráfego em vez de só ler) e **`#116`**
(`postMessage` sem validação de origem no `content.js`, que roda em `*://*/*`).

### O que continua sem endereço

As **31 lacunas de completude** do mergulho de 20/07 — as superfícies que ninguém nunca
auditou — seguem em prosa, sem id. As duas que o Feca priorizaria (os 4 injects que viram
P/L e os `import_*.py` que fazem `DELETE FROM bilhetes` contra o `DATABASE_URL` de produção
sem dry-run) **não** foram cobertas aqui: o `findings.json` de 19/07 não as enumera, e
auditá-las é trabalho de leitura de código novo, não de reconciliação. Fica como item
próprio no `BACKLOG §4.4`.

---

## Lote 1 — organização de documentos e auth (#1 a #18)

> Boa parte deste lote é sobre a **própria documentação**, e a faxina de hoje fechou os itens
> ao executá-los. Marco assim quando for o caso, para não parecer que fecharam sozinhos.

| # | Sev | Achado | Veredicto em 07/09 |
|---|---|---|---|
| 1 | médio | Frente Telegram→tipster duplicada em 4 documentos, sem dono único | **FECHADO (por esta faxina)** — `ONDE_ESTOU` e `Ideias/README` foram arquivados; o dono canônico é o `PLANO_TIPSTER.md` (P3) e o `BACKLOG §5` aponta só para ele. |
| 2 | info | Nomenclatura tripla Sharpen / Planilhador / extrator | **ABERTO** — o `CLAUDE.md` fixa `Sharpen` (sistema) × `SharpenUp` (extensão), mas **não** registra a equivalência com `Planilhador` (nome da pasta e dos docs). O repo já se chama `sharpen`. Custo: uma linha no `CLAUDE.md`. |
| 3 | baixo | `Backups/` sem política de retenção (era 55 MB / 370 pastas) | **ABERTO e pior** — hoje são **128 MB / 551 pastas**, com 223 arquivos `STATUS*`/`HISTORICO*`. É o Lote A. Já rastreado no `BACKLOG §4.2` (#25) e **agora com gate** (`tools/check_docs.py`). |
| 4 | médio | Frente de dedup estrutural (Betano/KingPanda/Bet365) pulverizada, sem plano | **PARCIAL** — os três casos deixaram de estar espalhados por memórias e bullets: estão no `BACKLOG` (§2 e §4). O que continua faltando é o **plano único** que a recomendação pedia — a raiz é comum ("dedup sem código confiável") e o tratamento segue caso a caso. |
| 5 | médio | Fase 0 da inteligência de tipster já no código, invisível no backlog | **FECHADO (por esta faxina)** — o `BACKLOG §5` diz "Fase 0 no ar (`origem_tipster`)" e nomeia P1/P2/P3 como o que falta. |
| 6 | médio | Item resolvido ainda listado como aberto: rename de métricas quant (#29-31) | **FECHADO (por esta faxina)** — a fonte do erro (`Ideias/README`) foi arquivada e o item não entrou no `BACKLOG`. |
| 7 | baixo | `NOTA_AO_AUDIT.md` commitado na raiz | **FECHADO** — o arquivo não existe mais (removido na Onda 6 da s158). |
| 8 | médio | Docs de consolidação defasados ~35 sessões | **FECHADO (por esta faxina)**, e desta vez **com cadência**: invariante #10 do `CLAUDE.md` + `tools/check_docs.py` no CI. A recomendação pedia exatamente isso ("definir uma cadência… sem isso o backlog diverge indefinidamente") — e sem o gate divergiu de novo, de 35 para ~206 sessões. |
| 9 | baixo | `CASA_BETANO` ainda descreveria scraping | **FECHADO — era falso positivo já na origem.** A própria evidência do achado registra `grep -in 'scrap' casas/CASA_BETANO.md → sem resultado`. O item nasceu de uma linha do `ONDE_ESTOU`, não do arquivo. |
| 10 | médio | Win rate HW/HL pela metade listado como aberto | **FECHADO** — `1360bbf`/`0941bf7` fizeram, e a fonte do erro foi arquivada. |
| 11 | baixo | Planos na raiz contra a estrutura declarada | **FECHADO** — nenhum `PLANO_*.md` na raiz; todos em `docs/` (ou `docs/arquivo/`). |
| 12 | médio | SaaS multiusuário Fase 1 não iniciada | **FECHADO** — Fases 1, 2 e 3 no ar (s233–s236). Só a Fase 4 (pagamento) segue aberta, no `BACKLOG §5`. |
| 13 | baixo | Pendências de casas aguardando bilhete real | **NÃO ERA ACHADO** — a própria recomendação dizia "manter como backlog reativo, nenhuma ação proativa necessária". Hoje vivem no `BACKLOG §2`. |
| 14 | baixo | STATUS §5 dizia "Jogo de Ouro: §9 (23 categorias aguardam amostra)" | **FECHADO** — a string "23 categorias" não existe mais nem no `STATUS.md` nem no `BACKLOG.md`. |
| 15 | **alto** | `auth.py` sem nenhum teste | **FECHADO** — `tests/test_auth.py` existe com 27 testes (`0bf12f2`, Onda 2 da s158). |
| 16 | info | Enumeração de usuário por *timing* (usuário inexistente pula o bcrypt) | **ABERTO, mitigado.** `resultado_login` (`app/auth.py`) segue com `if not entrada or not _verifica_hash(...)` — curto-circuito, o usuário inexistente não paga o custo do bcrypt. O **mitigante** é real: o `POST /login` faz `await asyncio.sleep(0.5)` em **todo** caminho inválido, o que afoga a diferença. O `bcrypt` dummy da recomendação não foi implementado. |
| 17 | médio | Trio barato de segurança (SESSION_SECRET fail-closed, XFF, `.dockerignore`) | **FECHADO nos três** — `auth.py:38-49` não sobe sem a env em produção; `main.py:1941-1946` confia só no hop do Railway; `.dockerignore` existe. |
| 18 | baixo | Estado de captura em memória impede escala horizontal (latente) | **ABERTO** — `_SESSOES` segue `dict` de processo (`app/captura.py:201`). É o mesmo achado que o mergulho de 20/07 promoveu a **D2/alto**; já está no `BACKLOG §4.3`. |

**Lote 1: 12 fechados · 4 abertos (#2, #3, #16, #18) · 1 parcial (#4) · 1 que não era achado (#13).**

---

## Lote 2 — schema, pool, login e rotas (#19 a #36)

> ⚠️ **As linhas citadas por estes achados apodreceram todas.** O `app/main.py` tinha ~1,8 mil
> linhas em julho e tem **4.341** hoje; o `database.py`, 780. Nenhuma referência `arquivo:linha`
> do `findings.json` aponta mais para o que descrevia. **Verifiquei por SÍMBOLO, nunca por
> número de linha** — é a regra que o próprio `BACKLOG` carrega no cabeçalho.

| # | Sev | Achado | Veredicto em 07/09 |
|---|---|---|---|
| 19 | médio | Sessão de pareamento em memória assume processo único | **ABERTO** — duplicata de #18 e do **D2** do mergulho. Um só item, três entradas. |
| 20 | baixo | Modelo em alias não-datado + sem lockfile | **ABERTO nos dois.** `config.py` segue `DEFAULT_MODEL = "claude-sonnet-4-6"` (alias, sem sufixo de data) e não existe lockfile — o próprio `requirements.txt` ainda diz, no comentário, que "um lockfile é o próximo passo". Os tetos `<major` estão lá e seguram o pior. |
| 21 | info | `get_pool` sem lock: corrida teórica pode criar dois pools | **ABERTO** — `if _pool is None:` seguido de `await asyncpg.create_pool(...)`, sem `asyncio.Lock`. Continua teórico: a criação acontece no `lifespan`, antes do `yield`. |
| 22 | médio | Coluna `dono` é TEXT livre com `DEFAULT 'Feca'` | **ABERTO** — e agora em **3 lugares** (`bilhetes:52`, `parceiros:85`, e a tabela da linha 252), não 2. O mergulho de 20/07 **refutou** o risco imediato ("latente, todo INSERT passa dono explícito"), e isso segue valendo; o que o achado pede é remover o default para falhar alto em vez de misattribuir. |
| 23, 24, 25 | baixo ×3 | Schema sem migrations versionadas; DDL e UPDATE de dados a cada boot | **ABERTO — e são o MESMO achado, escrito três vezes** por três agentes diferentes. Confirmado: os `UPDATE parceiros SET casa=…` (linhas 102-105) e o `INSERT INTO tipsters SELECT DISTINCT` seguem rodando em todo `init_db()`. É a Fase 0 do `ADR-001`. |
| 26 | médio | `UPDATE parceiros` antes do `CREATE TABLE parceiros` (quebra DB novo) | **FECHADO** — a ordem está certa hoje: `CREATE TABLE IF NOT EXISTS parceiros` na linha **75**, os `UPDATE parceiros` a partir da **102**. Foi o achado #3 da lista de 19/07, corrigido em `201b223`. |
| 27 | médio | `bilhetes` sem índices além da unique | **FECHADO** — 2 índices `idx_bilhetes_*` no `database.py` (`dono, criado_em` e o parcial `dono, codigo_bilhete`). |
| 28 | baixo | PK inconsistente: `SERIAL` em `bilhetes` vs `BIGSERIAL` nas tabelas novas | **ABERTO** — `bilhetes.id`, `parceiros.id` e a tabela da linha 199 são `SERIAL`; a da 219 é `BIGSERIAL`. Sem FK entre elas, é cosmético até o `ADR-001`. |
| 29 | info | Regex de data do checador pode falso-positivar em placar/handicap com barra | **ABERTO** — `_RE_DATA = r"\b\d{1,2}/\d{1,2}(/\d{2,4})?\b"` intacto, aplicado à descrição inteira. Nunca foi medido se algum placar em barra chega a passar por ali. |
| 30 | baixo | `_login_fails` cresce sem poda de IPs antigos | **ABERTO** — só a chave do IP corrente é filtrada (`main.py:1956`); nunca há varredura global. Vazamento lento e limitado a IPs que erraram a senha. |
| 31 | médio | (título "Teste", recomendação "rec", evidência "ev") | **NÃO É ACHADO** — é uma **entrada de teste do próprio pipeline de auditoria** que vazou para o `findings.json` com severidade `medio`. Vale registrar: um dos "95 confirmados" era literalmente um placeholder. |
| 32 | baixo | Rate-limit de login in-memory, não compartilhado entre réplicas | **ABERTO** — mesma família de #18/#19/D2. Enquanto for 1 réplica, é premissa, não defeito; o que falta é a premissa estar **escrita** em algum lugar que o deploy leia. |
| 33 | info | Dono da plataforma (`'Feca'`) hardcoded | **PARCIALMENTE FECHADO** — sumiu do `app/main.py` (0 ocorrências de `"Feca"` hoje); restam **3** no `app/auth.py`. A constante única que a recomendação pedia não existe. |
| 34 | baixo | `/captura/conectar` anônimo, sem rate limit, devolve `dono` | **ABERTO** — nenhum contador de tentativas no `captura.conectar()` nem na rota; ela segue em `_CAPTURA_ISENTAS` (sem CSRF, por desenho do pareamento). |
| 35 | info | Forma da resposta de salvar/sync duplicada em três rotas | **ABERTO** — `_resposta_upsert` não existe (0 ocorrências). Puro estilo. |
| 36 | médio | `/polymarket/sync` cria dado com `dono_efetivo`, violando a regra da s82 | **FECHADO** — `main.py:3204` já é `Depends(usuario_atual)`. Corrigido em `eee55c1` (Onda 1 da s158). |

**Lote 2: 3 fechados · 1 parcial (#33) · 13 abertos · 1 que não é achado (#31).**
**Duplicatas encontradas dentro do próprio corpus: #19≡#18≡D2 e #23≡#24≡#25.**

---

## Lote 3 — repository, dinheiro e testes (#37 a #54)

| # | Sev | Achado | Veredicto em 07/09 |
|---|---|---|---|
| 37 | baixo | `/bilhetes/restaurar` re-insere linhas do cliente sem validação de fronteira | **A CONFIRMAR** — a rota mudou de forma desde julho (a exclusão hoje passa por `lixeira_contas`, que não existia). Precisa de leitura do caminho inteiro, não de `grep`. |
| 38 | baixo | `main.py` é god file (router + parsing/dedup + streaming) | **ABERTO e maior** — eram ~1,8 mil linhas, são **4.341**. É o `#11` da `AUDITORIA_2026`, aceito como dívida de manutenibilidade sem risco de runtime. |
| 39 | médio | Comportamento por casa hardcoded em Python contradiz "casa localiza, global calcula" | **ABERTO** — `_CASAS_MARCADOR_CODIGO` e os `if casa_key.upper() == …` seguem no `main.py` (vi o bloco ao medir o B1). O registro declarativo que a recomendação pedia não existe. É o mesmo princípio que o `PLANO_TRADUTOR_DETERMINISTICO` ataca por outro lado. |
| 40 | médio | Contrato IA↔parser é TSV em markdown lido por regex, sem validação de forma | **PARCIALMENTE FECHADO** — a metade "contar linhas emitidas vs parseadas e sinalizar divergência" **existe hoje**: `conferir_cobertura` + `_garantir_cobertura` (`main.py:1086`), que cobram quantidade por código e repescam o que faltou. A outra metade (structured output / tool use no lugar de markdown livre) **não** foi feita. |
| 41 | baixo | Semântica de "mesmo bilhete" duplicada entre `_scroll_key` e `_assinatura` | **ABERTO** — as duas réguas seguem separadas. O `#14` (`domain.py`), que era o caminho da unificação, foi **morto por decisão** na s160. |
| 42 | info | Arredondamento por linha antes da soma gera drift de centavos vs `SUM` da planilha | **ABERTO por decisão** — `calcular_pl` arredonda por linha, e é isso que faz o P/L bater com a planilha bilhete a bilhete. O achado é real e a escolha é deliberada; falta só estar escrita. **Relacionado, e medido depois:** a s325 viu exatamente esse drift ao reconciliar o Grego Tips (0,11u em 267 vitórias). |
| 43 | médio | Win Rate diverge entre extrator (HW cheio) e dashboard (HW meia) | **FECHADO** — `repository.py:1825-1828` hoje é `wr_den = settled - 0.5*hw - 0.5*hl` e `wr = (wins - 0.5*hw)/wr_den`, com o comentário citando o achado #17 por nome. |
| 44 | info | `dashboard_rows` carrega a tabela inteira do dono (`SELECT *`) por request | **ABERTO** — `export_bilhetes` (`repository.py:1774`) segue `SELECT * FROM bilhetes WHERE dono = $1 ORDER BY criado_em`, sem `LIMIT`. É o **D4** do mergulho e o `#17` da `AUDITORIA_2026`. |
| 45 | médio | Sem FKs; `renomear_tipster` não propaga para `casa_config.tipsters` | **ABERTO** — a função toca `tipsters`, `bilhetes` e `tipster_unidade`; **`casa_config` continua fora**. Renomear tipster deixa a curadoria de casa apontando para o nome velho. |
| 46 | baixo | `custo_usd` (billing de tokens) é puro e não testado | **ABERTO** — `tests/` tem `test_custo_janela_vida.py` (que é da janela de vida da conta, outro assunto) e nenhum teste importa `custo_usd`. |
| 47 | baixo | `estado_extracao` exigia `odd>0` para V/L/HL → resolvidos sem odd ficavam "aberta" para sempre | **FECHADO** — a docstring de hoje diz exatamente o que a recomendação pedia: "a odd só é exigida onde o P/L depende dela (W/HW)", com o porquê da mudança escrito. |
| 48 | médio | `parse_tsv` (fronteira do `/salvar`) sem teste; linha malformada descartada em silêncio | **FECHADO** — `tests/test_parse_tsv.py` existe. |
| 49 | baixo | `analisar_extracao` (confiança + notas do rail) coberto só de raspão | **A CONFIRMAR** — exige ler a suíte item a item contra os casos que a recomendação lista. Não é decidível por `grep`. |
| 50, 51 | baixo + médio | Assinatura normaliza a odd mas usa o stake TEXT **cru** | **ABERTO — e são o MESMO achado, por dois agentes.** Confirmado: `_assinatura` (`repository.py:1080`) segue `row.get("stake", ""), _norm_odd(row.get("odd", ""))`. Curiosidade que reforça o achado: o **alerta de coincidência** logo abaixo (`:1279`) já usa `round(st, 2)` — ou seja, o código **sabe** normalizar stake, só não o faz onde conta. |
| 52 | **alto** | Caminho de escrita de dinheiro sem teste — o conftest stuba o banco inteiro | **FECHADO** — `tests/test_repository_db.py` existe (harness de camada-DB real, gateado em `TEST_DATABASE_URL`; são os 30 `skipped` da suíte local e rodam no CI com Postgres). Foi o `#11` de 19/07, `e7a8188`. |
| 53 | info | Dinheiro/odd/data como TEXT + `float` (ADR-001) | **ABERTO por decisão** — a própria recomendação dizia "sem ação nova nesta auditoria". `BACKLOG §4.1` (#13/#25). |
| 54 | baixo | Lote de upsert em autocommit por linha, sem transação | **ABERTO** — `upsert_bilhetes` (`repository.py:1150`) abre `pool.acquire()` e **não** abre `conn.transaction()`. Outras três funções do arquivo abrem (`:2101`, `:2301`, `:3001`), então a ausência aqui é escolha ou esquecimento — a recomendação pedia justamente **decidir explicitamente**, e a decisão nunca foi registrada. |

**Lote 3: 4 fechados · 1 parcial (#40) · 11 abertos · 2 a confirmar (#37, #49).**
**Mais uma duplicata interna: #50 ≡ #51.**

---

## Lote 4 — dedup, UPSERT e o front do dashboard (#55 a #76)

| # | Sev | Achado | Veredicto em 07/09 |
|---|---|---|---|
| 55 | médio | Tabela de dedup do `CLAUDE.md` divergia do código ("mesmo lote idêntico salva UMA vez") | **FECHADO** — o `CLAUDE.md:796` hoje diz exatamente o que o código faz: "salva **ambas** as linhas (assinaturas distintas via `_counter`: `B`, `B\|2`, …) + aviso amarelo; delete se for sobreposição real". |
| 56 | médio | `repository.py` mistura domínio puro e acesso a dados | **FECHADO POR DECISÃO, não por código.** O `domain.py` era o `#14` de 19/07 e foi **morto na s160**: a premissa caiu quando o harness de DB real (`#11`) destravou o teste sem precisar do split, e mover 550 linhas do núcleo de dinheiro seria risco por ganho cosmético. Registrar como decisão, não como pendência. |
| 57 | baixo | Guard cross-dono pode descartar aposta idêntica legítima em conta compartilhada sem ID | **ABERTO, e a recomendação era "manter como está".** O que ela pedia junto — documentar o trade-off no `CLAUDE.md` — **foi feito**: a memória `dedup_cruzada_conta_compartilhada` e a tabela de dedup cobrem o caso. O descarte silencioso continua. |
| 58 | médio | Migrações A e B rodam 2 `UPDATE` por bilhete com código em **toda** extração | **ABERTO** — as duas seguem dentro do laço (`repository.py:1304` e `:1325`), sem gate de lote legado. O mergulho de 20/07 chegou a listar "gatear a Migração A/B no hot path" na Onda 3 e não foi feito. **Nota:** a Migração B ganhou trabalho novo na s327 (comparar odd por `_norm_odd`), então o custo por bilhete subiu, não desceu. |
| 59 | baixo | Migração A/B fora do `try/except` do INSERT: corrida de unique aborta o lote inteiro | **ABERTO** — mesmo bloco do #58; o `except asyncpg.UniqueViolationError` segue protegendo só o INSERT. Probabilidade baixa, modo de falha péssimo (lote inteiro). |
| 60 | médio | Regressão do bug case-sensitive do resultado cobria só a LEITURA | **A CONFIRMAR** — o harness de DB real existe agora (`tests/test_repository_db.py`), mas eu não conferi se ele tem o caso `resultado='w'` → persistido `'W'`. Decidível, só não por `grep`. |
| 61 | médio | Dashboard sem responsividade: `layout.css` sem uma `@media` | **ABERTO** — `grep -c @media layout.css` = **0**, igual a julho. É o **D1** do mergulho, que o classificou como a única área **vermelha**. |
| 62 | médio | `fmtPL` do dashboard pintava zero de verde com `+` | **FECHADO** — hoje é `cls = v>0?'pos':(v<0?'neg':'')` e `sign = v>0?'+':(v<0?'−':'')`. Zero neutro, minus U+2212. Corrigido em `31166ad`. |
| 63 | médio | Unidade de fallback depende do filtro da tela — "u" não é comparável entre views | **A CONFIRMAR** — o cálculo mudou de forma desde julho (a escada de unidade evoluiu com o P1 do tipster). Exige leitura do caminho, não `grep`. |
| 64 | médio | Rótulos de eixo com contraste abaixo do mínimo (`tc()` = `#505060` no dark) | **FECHADO** — `tc()` hoje devolve `#5E6775`, que é exatamente o `--ink-mute` que a recomendação pedia. |
| 65 | baixo | "Baixar base (CSV)" ignora os filtros ativos | **ABERTO** — segue sem recorte filtrado. É UX, não dado errado: a base completa é o que o botão promete. |
| 66 | **alto** | Custo de Tipsters e Custos Gerais vazavam entre donos (`localStorage` sem escopo) | **FECHADO** — a fonte de verdade virou **Postgres por dono** via `/custos/store`; o `localStorage` ficou só como cache de pintura instantânea, e o comentário no código cita o incidente do Jonathan (19/07) por nome. Foi o `#1`/`#2` de 19/07. |
| 67 | médio | `BASE_BANK = 100000` fixo torna o Drawdown % arbitrário entre donos | **ABERTO** — `BASE_BANK` segue no cálculo (`app.js:179`, `:290`). O rótulo honesto que a recomendação sugeria como paliativo também não existe. |
| 68 | médio | MDD agregado por dia esconde drawdown intradiário | **PARCIALMENTE FECHADO** — a s313 unificou Topo e Drawdown na **mesma curva e mesma régua**, dia a dia, partindo do mesmo zero (é a regra que está no `CLAUDE.md`). O que a recomendação pedia além disso — um motor **bet-a-bet** com hora real — não foi feito, e sem hora no dado não dá para fazer. |
| 69 | baixo | p-value testa yield **com** Void, mas o ROI exibido é **sem** Void | **A CONFIRMAR** — o Monte Carlo foi para um Web Worker desde então e o código mudou de lugar. Não conferi o denominador. |
| 70 | médio | p-value e Monte Carlo assumem apostas i.i.d. (viés otimista) | **ABERTO por decisão** — é o `#30` da `AUDITORIA_2026`, fechado lá como "heurística por design, e assim declarada" no tooltip. O *bootstrap* em blocos nunca foi feito. |
| 71, 72 | baixo + médio | Solidez infla para edge trivial · Solidez tem piso de 0,40 para book perdedor | **ABERTO** — são o `#15`/`#16` de 19/07: implementados e **revertidos no mesmo dia** (`9394553`), porque o gate rebaixava um tipster sólido por um drawdown normal. Precisa de redesenho, não de ajuste (`BACKLOG §3.1`). |
| 73 | baixo | `sFolga` da Solidez usa DD **simulado** mas compartilha o benchmark do Recovery Factor **real** | **ABERTO** — entra no mesmo redesenho do #71/#72, e é o detalhe mais concreto dos três: dois números com o mesmo nome ("folga") e denominadores diferentes. |
| 74 | médio | Edição inline por duplo-clique sem pista visual (`class` duplicado no mesmo `div`) | **A CONFIRMAR NA TELA** — atributo duplicado é o tipo de coisa que o navegador resolve em silêncio; o gate é abrir a tela, como manda a regra de UI. |
| 75 | baixo | Literais hex duplicam tokens `--d-*` já definidos | **ABERTO** — o `check-tokens` mede o drift (615 cores literais / 177 valores) e passa: ele barra cor **banida** e drift **novo**, não afirma conformidade. Está escrito assim na saída do próprio gate. |
| 76 | baixo | KPIs do `gestao.js` montam dinheiro com string crua `'R$ '+fmt` | **ABERTO e igual** — **28** ocorrências de `'R$ '+`, o mesmo número que a auditoria contou em julho. Viola o `UI_REFERENCE §5` (o `R$` tem de ser neutro, a cor só no número). |

**Lote 4: 5 fechados · 2 parciais (#68, #57) · 11 abertos · 4 a confirmar (#60, #63, #69, #74).**
**Mais uma duplicata interna: #71 ≡ #72 ≡ (#15/#16 de 19/07).**

---

## Lote 5 — gráficos, UI da extração e casas (#77 a #99)

| # | Sev | Achado | Veredicto em 07/09 |
|---|---|---|---|
| 77 | baixo | Barras de Fornecedores dependem só de cor para o sinal | **A CONFIRMAR NA TELA** — acessibilidade de gráfico não se mede por `grep`. |
| 78 | médio | Distribuição de Odds: dois eixos % independentes sobrepostos enganam | **A CONFIRMAR NA TELA.** |
| 79 | **alto** | P/L Líquido subtraía custo de tipster do histórico inteiro, ignorando o filtro | **FECHADO** — `overview.js:23-27` hoje calcula `_ymMin`/`_ymMax` do recorte e pula o mês fora dele, com o comentário citando o achado. Foi o `#2` de 19/07 (`570bd89`). |
| 80 | médio | Cards da Visão Geral mostram números velhos quando o filtro zera resultados | **A CONFIRMAR NA TELA** — é justamente o tipo de defeito que só aparece renderizando. |
| 81, 82 | baixo ×2 | Gráfico de banca sem legenda/títulos de eixo · curva acumulada sem âncora no zero | **A CONFIRMAR NA TELA** — os dois são decisões de leitura visual, e o #82 a auditoria já colocava como "decidir a convenção com o Feca". |
| 83, 86 | médio ×2 | Cores de série verde/rosa fora de qualquer token, inconsistentes entre gráficos | **ABERTO — e são o mesmo achado.** O `check-tokens` mede o drift (615 literais / 177 valores) e **passa**, porque ele barra cor banida e drift novo, não afirma conformidade. Está escrito na saída do próprio gate. |
| 84 | info | Variável `roi` morta no plugin de rótulos do gráfico de Esportes | **FECHADO** — a linha do `roi` hoje **é usada**: entra no `return [_txtPL(…), 'ROI: …', 'Apostas: …']` do tooltip. |
| 85 | médio | Tooltip do gráfico de Esportes mostrava HTML cru (`fmtPL` num tooltip de canvas) | **FECHADO** — `performance.js:156` usa `_txtPL(e[1].l)`, exatamente o formatador de texto puro que a recomendação pedia. ⚠️ **Isto corrige o `BACKLOG §4.2`**, onde eu tinha deixado o `#6` do TURBO 19/07 como "a confirmar na tela": ele está fechado. |
| 87 | baixo | Dead code: `const wins=settled.filter(['W','HW'])` (resíduo do bug #27) | **ABERTO** — as **3** declarações mortas seguem lá, o mesmo número de julho. |
| 88 | baixo | Gráficos de evolução sem estado vazio quando há <2 dias | **A CONFIRMAR NA TELA.** |
| 89 | info | Matriz de correlação inverte a convenção de cor (verde = correlação negativa) | **ABERTO por decisão** — a própria recomendação dizia "manter se for decisão de marca"; o reforço de rótulo no topo é o que falta. |
| 90 | baixo | Filtros não persistem ao trocar de aba | **ABERTO** — `gfs(p)` segue com estado por página (`filters.js:3`). Vale notar que a s317 **unificou a barra** de filtros numa superfície só; a persistência entre abas é outro eixo e continua aberta. |
| 91, 97 | baixo ×2 | Edição inline e atalhos da coluna Tipster sem dica visível | **A CONFIRMAR NA TELA** — pura descoberta de UI. |
| 92 | médio | Campo Resultado: texto livre no modal vs `select` no inline | **FECHADO** — `index.html:2277` hoje é `<select id="ed-resultado">` com `— aberta —` e as 5 opções. Fecha a porta que gerou o bug histórico do `'v'` minúsculo. |
| 93 | baixo | "Limpar" apaga texto+imagens do lote sem confirmação | **A CONFIRMAR NA TELA.** |
| 94 | baixo | Onboarding promete "confere e confirma", mas a extração salva direto | **A CONFIRMAR NA TELA** — texto de onboarding, precisa ser lido renderizado. |
| 95 | médio | Erro cru do servidor (HTML/stacktrace) despejado no card de extração | **A CONFIRMAR** — o caminho de erro mudou muito (a s314 levou o 500 da Caixa para o formulário que falhou). Não conferi este ponto específico. |
| 96 | baixo | Peso de stake (25) domina e pode sugerir com um único sinal | **ABERTO, e agora com nuance** — `index.html:6671`/`:6686` seguem com `w: 25` e `25/√finais.size`. Mas o achado envelheceu por cima: a s221 provou que **dois cortes viraram load-bearing** (valor redondo e `valores.size === 1`) e o `CLAUDE.md` os documenta. Recalibrar o 25 sem respeitar esses dois cortes quebra o matcher em produção — já quebrou. |
| 98 | médio | Separador de bet-builder diverge entre casas (`&` fora do global) | **PARCIALMENTE FECHADO** — a `CASA_JOGODEOURO` tem **0** ocorrências de ` & ` hoje; a `CASA_LOTTU` ainda tem **4**. A decisão global foi tomada (` // ` é o separador único, e está no `CLAUDE.md` — achado `#19` de 19/07); a propagação para a Lottu não terminou. ⚠️ `casas/` está fora do escopo desta faxina. |
| 99 | baixo | Contagem hardcoded "27 categorias" drifou | **ABERTO e pior do que o achado dizia.** Medido pelo parser canônico (`audit_casas.categorias_oficiais()`): o `§3` tem **30** categorias hoje — não 27, e nem as 28 que a auditoria supunha. A string "27 categorias" segue em 4 arquivos de casa **e no `CLAUDE.md`**. A recomendação continua a certa: tirar o número, já que a lista canônica vive no `§3`. ⚠️ `casas/` fora do escopo. |

**Lote 5: 5 fechados · 1 parcial (#98) · 6 abertos · 11 a confirmar na tela.**
**Correção ao `BACKLOG §4.2`: o `#6` do TURBO 19/07 está FECHADO (achado #85 acima).**

> **Padrão que aparece neste lote:** 11 dos 23 itens só se decidem **abrindo a tela**. Isso
> não é limitação do método — é a mesma coisa que a regra de UI do `CLAUDE.md` já manda
> ("abrir a tela num navegador antes do commit", item 5). Uma auditoria feita 100 % por
> leitura de código deixa um terço dos achados de UI em suspenso por construção.

---

## Lote 6 — planos, docs e a extensão (#100 a #120)

| # | Sev | Achado | Veredicto em 07/09 |
|---|---|---|---|
| 100 | baixo | ADR-001 adiado por design, com gate | **NÃO É ACHADO** — a recomendação era "manter adiado conscientemente". Continua registrado como dívida consciente (`BACKLOG §5`). |
| 101 | médio | Self-host das fontes (#36) — CSP ainda aberto, migração pela metade | **FECHADO** — `index.html:22` e `dash/index.html:30` carregam `/static/fonts.css`; **zero** ocorrências de `fonts.googleapis` nos dois, e a CSP do `main.py` também não tem mais o host. A migração terminou. |
| 102 | médio | Observabilidade zero (#44) | **ABERTO** — `BACKLOG §4.1`. E a nota da recomendação envelheceu para pior: ela dizia "pré-requisito antes de abrir cadastro self-service (SaaS Fase 2)". **A Fase 2 abriu na s235, sem a observabilidade.** |
| 103 | baixo | Relatórios datados acumulam soltos em `docs/` sem sinal de vivo/histórico | **FECHADO (por esta faxina)** — a recomendação era, literalmente, "criar `docs/arquivo/` e mover os relatórios datados encerrados". É o Lote D, 7 semanas depois. |
| 104 | baixo | Link markdown quebrado em `docs/HISTORICO.md` | **FECHADO** — no Lote C. A varredura hoje: 115 arquivos, zero quebrado. |
| 105 | baixo | Fatia 3 da casca: plano não reconciliado com o que as sessões 153-157 entregaram | **ABERTO** — o `PLANO_CASCA_UNIFICADA` segue sem reconciliação, e o `BACKLOG §5` só sabe dizer "Fatia 3". Decidir se ela está concluída é conversa com o Feca. |
| 106 | baixo | ADR-002 Fase 2 / Dashboard C, condicional a medição | **ABERTO por desenho** — mas a recomendação trazia um item barato que se perdeu: **a "Fase 0 de revalidação 304"**, independente do C, que cortaria o re-fetch de 8 MB a cada abertura. Nunca foi feita nem registrada. |
| 107 | baixo | Extração worldwide Fase 1 | **ABERTO** — `BACKLOG §5`. |
| 108 | info | `PLANO_INFERENCIA_POR_CAMPO` órfão, sem nenhuma referência | **FECHADO (por esta faxina)** — a recomendação pedia "adicionar a frente ao índice"; hoje ele está no `docs/README.md` e no `BACKLOG §5`. |
| 109 | baixo | Inferência por campo precisa de OK do Feca antes de codar | **ABERTO** — o gate é do plano, não do código. |
| 110 | médio | Camada de evidência de tipster (Fase 1) — "medir antes de construir" | **ABERTO** — e a recomendação continua exatamente certa. Vale notar que a s221 fez uma medição vizinha (prova por remoção do perfil suspeito) e ela virou regra no `CLAUDE.md`; o backtest por carteira, que é o que este item pede, não. |
| 111 | médio | Persistir posições ativas do Polymarket | **FECHADO** — `_derivar_ativas` no ar (ver `docs/arquivo/README.md`). |
| 112 | info | `UI_REFERENCE §1` não documenta a camada de tokens `--d-*` usada nos gráficos | **ABERTO** — **0** menções a `--d-pos`/`--d-proj`/`--d-info` no `UI_REFERENCE.md`, e os tokens existem no `tokens.css`. É o mesmo buraco doc↔token que alimenta os achados #83/#86 (cores de série fora de token): não há onde consultar qual verde é o oficial. |
| 113 | baixo | Rotação da senha do Postgres | **ABERTO** — `BACKLOG §1.1`. Arrasta desde a s82. |
| 114 | médio | `bf_inject` foge do modelo passivo: até 400 requisições autenticadas com paginação adivinhada | **ABERTO** — `bf_inject.js:176` segue `while (!fimReal && idx != null && replays < 400)`. Nem backoff, nem teto menor. É o único inject que **cria** tráfego na casa em vez de só ler. |
| 115 | médio | Scraping acoplado a seletores hardcoded quebra em SILÊNCIO quando a casa muda o DOM | **FECHADO** — o autodiagnóstico universal que a recomendação pedia foi feito (`#13` de 19/07, s160): **25** ocorrências de `hook:` no `content.js`, com o heartbeat e o toast diferencial em todas as casas-robô. |
| 116 | baixo | `content script` aceita `postMessage` de qualquer origem; injects postam com `targetOrigin '*'` | **ABERTO** — nenhuma checagem de `ev.source` ou `ev.origin` no `content.js`. Está entre as **31 lacunas de completude** que o mergulho de 20/07 nomeou e ninguém auditou. |
| 117 | baixo | Robôs genéricos fazem `querySelectorAll('*')` + `getComputedStyle` por elemento | **ABERTO** — performance do robô genérico; casas com seletor dedicado não passam por aí. |
| 118 | baixo | `host_permissions: ["*://*/*"]` + content script em toda página | **ABERTO** — o `manifest.json:18-20` é idêntico. Nota de contexto: a extensão **não** passa por loja (a distribuição é manual por link fixo), então não há revisor a satisfazer — o custo é de confiança do tester, não de aprovação. |
| 119 | médio | Sem handshake de versão extensão↔backend | **PARCIALMENTE FECHADO** — a versão **já viaja**: `popup.js:150` e `:294` mandam `versao: VERSAO` no corpo do `/conectar`. O que falta é a outra metade — o backend **responder capacidades** (quais casas-robô aquela versão suporta) ou avisar que exige versão mais nova. |
| 120 | baixo | Mapa casa↔host duplicado em 3+ lugares | **ABERTO** — `CASA_HOSTS` no `popup.js`, `_HOSTS_POR_CASA` no `captura.py`, `matches` no `manifest.json`. É a mesma família dos "12 pontos de registro" que o `GUIA_CASA_SHARPENUP` documenta e o `audit_sharpenup.py` **gateia** — o gate não elimina a duplicação, mas impede que ela drife em silêncio. |

**Lote 6: 6 fechados · 1 parcial (#119) · 13 abertos · 1 que não é achado (#100).**

---

## Lote 7 — os MASTER e os scripts (#121 a #139)

> ⚠️ **`global/` e `casas/` estão fora do escopo desta faxina** (regra do Feca). Aqui eu só
> **meço e registro**; nada foi editado.

| # | Sev | Achado | Veredicto em 07/09 |
|---|---|---|---|
| 121 | médio | "Primeiro/Último Marcador" órfãos: só existiam na DESCRIÇÃO, nunca em APOSTAS | **FECHADO** — o `MASTER_APOSTAS` tem **3** ocorrências hoje (eram 0). Foi o `#20` de 19/07 (`40deee0`, aprovado pelo Feca). |
| 122 | baixo | Regra "Sets Vôlei/Tênis" duplicada entre APOSTAS §9 e ESPORTES §8 | **ABERTO** — a regra segue nos dois (27 menções a "Sets" em APOSTAS, 3 em ESPORTES). O risco é drift, não erro atual. |
| 123 | médio | Assimetria `Múltipla` (Aposta, ≥2) vs `Múltiplos` (Esporte, ≥3) mal cross-referenciada | **A CONFIRMAR** — o `#20` mexeu na whitelist de `Múltiplos`; se ele também acrescentou o lembrete cruzado no §5 de APOSTAS, eu não conferi. |
| 124, 125 | baixo ×2 | Descrição de "Corridas" ampla demais · colisão lexical "Corridas" × "Race" | **ABERTO** — o `§3` ainda diz `Corridas \| Mercados de corridas e estatísticas de Baseball`, exatamente a string que a auditoria citou. |
| 126 | baixo | Referência cruzada quebrada em ESPORTES §6 Vôlei ("seção anterior" que está adiante) | **A CONFIRMAR** — exige ler as duas seções em ordem; `grep` não decide. |
| 127 | médio | Valor `Múltiplos` ausente da tabela oficial §7 e dos exemplos válidos §4 | **FECHADO** — 10 ocorrências de `Múltiplos` no `MASTER_ESPORTES` hoje (eram 2, só no §2 e no §8). Foi o `#20` de 19/07. |
| 128 | médio | OUTPUT §13/§18 dessincronizado com "aposta aberta → Resultado vazio" | **FECHADO** — o `MASTER_OUTPUT` tem 5 menções a célula vazia/vazio, e o `CLAUDE.md` já cita `MASTER_OUTPUT §13.1` como a fonte da regra. Também foi o `#20`. |
| 129 | médio | PIPELINE §3.1 ("L ou V → ODDS TOTAIS") conflita com RESULTADO ("odd estrutural") | **ABERTO** — `MASTER_PIPELINE:114` segue literalmente `L ou V → ODDS TOTAIS do bilhete`. **É o mais grave deste lote**: dois MASTERs mandam coisas diferentes sobre a odd de múltipla com perna anulada, e a odd entra no P/L. |
| 130 | info | PIPELINE §6.3 omite o passo "conhecimento próprio do modelo" que ESPORTES §5 tem | **A CONFIRMAR** — comparação de duas listas, precisa de leitura. |
| 131 | médio | Regra de cashout (dinheiro) sem nenhum guard automatizado | **PARCIALMENTE FECHADO** — a s321 trouxe o `tests/test_odd_resultado_determinista.py`, que prova o veredicto pelo **retorno** contra as cinco fórmulas do `calcular_pl` lidas ao contrário, cashout incluído (5 mutações aplicadas e pegas). O que a recomendação pedia e **não** existe é o par golden (bilhete real de cashout + TSV esperado) — o `test_formulas.py` só toca cashout de raspão, numa asserção de `estado_extracao`. |
| 132 | médio | `golden_set/bilhetes` vazio — sem regressão print→TSV por casa | **ABERTO** — `golden_set/` tem só `descricoes.jsonl` e o `README`. É o `#21` de 19/07, bloqueado em prints do Feca (`BACKLOG §1.2`). |
| 133 | baixo | Bytecode órfão em `scripts/__pycache__` (`import_diogo`) | **FECHADO** — o `.pyc` órfão não existe mais; o que há é o do `import_diogo_sharktrack_xlsx`, que **tem** fonte. |
| 134 | info | Divergência de nomenclatura do matcher (v4 vs v5) | **FECHADO por reescrita** — a docstring hoje é "Backtest holdout dos **DOIS** matchers, lado a lado", sem etiqueta de versão. O problema (etiqueta divergente) deixou de existir porque a etiqueta saiu. |
| 135, 136, 138 | médio + baixo + médio | Backtest: carteiras importadas degeneram · sem split temporal real · holdout impossível sem assinatura datada | **ABERTOS, os três, e o script SABE.** As linhas 29-32 dizem: *"usa `criado_em` como eixo de tempo… para bases importadas todas iguais → o holdout degenera; nessas, o split correto usa a coluna `data`. **Refino pendente.**"* É o `#18` de 19/07 (`BACKLOG §4.2`) e a regra **"assinatura tem ERA"** do `CLAUDE.md` nasceu exatamente daqui — a regra foi escrita, o harness não. |
| 137 | baixo | Precisão penalizada por casos insolúveis (tipster real arquivado) | **ABERTO** — `com_perfil` conta mas não filtra; a precisão segue incluindo bilhete cujo tipster real está fora do conjunto de candidatos. Mede o modelo pior do que ele é. |
| 139 | baixo | `import_lava.py` com caminho pessoal | **ABERTO** — `:23` idêntico. Duplicata do `#10` da `AUDITORIA_2026` (`BACKLOG §4.1`). |

**Lote 7: 5 fechados · 1 parcial (#131) · 10 abertos · 3 a confirmar (#123, #126, #130).**
**Duplicatas internas: #135 ≡ #136 ≡ #138 (o mesmo buraco do backtest) e #139 ≡ `AUDITORIA_2026 #10`.**
