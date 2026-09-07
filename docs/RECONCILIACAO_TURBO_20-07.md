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

_(preenchido ao fim; ver §Cobertura)_

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
