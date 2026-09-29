# Plano de lançamento — frente de LANÇAMENTO (Equipe 1)

> Registro da frente que preparou o produto para receber gente nova. Sessões 374 a 385,
> em terminal paralelo ao de marketing (Equipe 2).
> **O que virou regra vinculante não mora aqui**, mora no [`CLAUDE.md`](../CLAUDE.md) e nos
> runbooks citados. Isto é o mapa: quem fez o quê, o que ficou aberto, e de quem é.

---

## 1. A equipe

Não são oito pessoas. São oito papéis que uma frente de lançamento precisa cobrir,
executados em sequência e não em paralelo, porque o gargalo aqui é ordem, não braço.

| Papel | O que responde | O que entregou |
|---|---|---|
| **Tech Lead** | Sequência e critério de go / no-go | Este plano; o levantamento dos 6 pontos; a fila de execução |
| **SRE / Infra** | Deploy, rollback, backup, alerta, **e o custo de IA** | [Backup com prova de restore](RUNBOOK_BACKUP_POSTGRES.md) · [Rollback](RUNBOOK_ROLLBACK.md) · os dois gates da captura no CI |
| **AppSec** | Sessão, isolamento por `dono`, rate limit, exposição de rota | Auditoria das 112 rotas por AST; `SESSION_SECRET` confirmado; teto do `/extrair` levantado e adiado |
| **QA** | Rodar os gates; desenhar a jornada do usuário novo | Os 6 gates medidos; a jornada percorrida em Chrome headless nos dois cenários de base nova |
| **Onboarding** | O primeiro minuto de quem chega | A aba Resultados parou de mentir "Carregando dados…" |
| **Dados & Capacidade** | Integridade, medição, pool, carga | Pool e processo único medidos; a régua de tamanho do gate de docs corrigida |
| **Suporte / Ops** | Runbook de incidente, FAQ, canal | **Nada ainda.** É o próximo da fila |

**Dois ajustes na lista original, e o porquê:**

1. **Engenheiro de Dados e DBA viraram um papel só.** No repo os dois compartilham a mesma
   fonte (`repository.py`, `database.py`) e a mesma pergunta: o número chegou ao banco, e
   aguenta quanto? Separar criaria dois donos para o mesmo arquivo.
2. **O custo de IA ficou no SRE, explicitamente.** Não estava na lista e era um buraco
   medido. Ver a seção 4.

---

## 2. O que foi entregue

### B1. O banco passou a ter backup

Não havia nenhum. Nem `pg_dump`, nem job, nem snapshot documentado. O único caminho de
volta era a `lixeira_contas`, que cobre **uma** conta excluída pela tela e vive 7 dias.

`scripts/backup_postgres.py` + [`RUNBOOK_BACKUP_POSTGRES.md`](RUNBOOK_BACKUP_POSTGRES.md).

**A prova de restore é o gate, não o dump.** O modo `--provar` restaura num banco local
descartável e compara `count(*)` tabela a tabela contra a origem.

```
18 tabela(s) · 304.146 linha(s) na origem
PROVADO: o dump restaura e bate linha a linha com a origem.
```

Dump de 17,5 MB em 28,9s, zero divergências.

**O motivo de nunca ter existido era um instalador:** produção roda PostgreSQL 18.6 e a
máquina tinha o cliente 17. O `pg_dump` se recusa a dumpar servidor mais novo que ele, e o
erro cru não dizia isso. Hoje o script explica e dá o gesto seguinte.

Três travas, todas recusando em vez de avisar: restore só em `localhost` (o `.env` da
máquina aponta para produção), banco de prova com prefixo e `DROP` num `finally`, e nenhuma
URL ou senha impressa.

> **Pendência real:** a cadência é manual. Automatizar sem depender do PC ligado é trabalho
> separado, e enquanto não existir, backup depende de alguém lembrar.

### B2. A aba Resultados parou de mentir para quem acaba de chegar

`aplicarFeed` parte o feed em dois: `DADOS` recebe só aposta liquidada. Quem se cadastra,
instala o SharpenUp e captura hoje só tem aposta em aberto, então `DADOS` nasce vazio. O
`renderResultados` tratava "vazio" e "ainda carregando" com a mesma frase, e a tela ficava
em **"Carregando dados…" para sempre**. É o caso do Diogo (s239), que continuava vivo.

**Medido antes de propor**, em Chrome headless com o front real e dois feeds sintéticos
(base zero e base só com abertas). Nos dois a aba parava em 133 caracteres, sem KPI, sem
tabela e sem gráfico. **As outras dez abas renderizaram estado vazio honesto nos dois
cenários.**

O discriminador é `window._dataBuiltMs`, gravado logo depois de `aplicarFeed` nos dois
caminhos de carga. Truthy significa que o feed chegou, logo vazio é ausência e não espera.

**Limite declarado:** fetch que falha sem cache continua caindo em "Carregando", de
propósito. O erro de conexão tem canal próprio (`_errBanner`), e dizer "não há aposta
encerrada" ali seria a mentira inversa, culpando a base do usuário por falha de rede.

Gate: `tests/test_resultados_base_vazia.py`, 6 mutações e 6 detectadas.

### B3. O deploy ganhou botão de desfazer

Não existia runbook de rollback. [`RUNBOOK_ROLLBACK.md`](RUNBOOK_ROLLBACK.md), e a primeira
pergunta dele é a que importa: **é o código ou é o dado?** São dois desastres com remédio
oposto.

**Dois achados que mudaram o procedimento:**

1. **O CLI do Railway não faz rollback.** `deployment redeploy` reimplanta a última, que é
   a quebrada. Voltar para uma anterior é ação de painel. E `railway down` **remove** a
   implantação em vez de voltar.
2. **Todo deploy migra o banco sozinho** (`init_db()` no `lifespan`, `SCHEMA_SQL` inteiro a
   cada boot). Medido: 18 `CREATE TABLE IF NOT EXISTS`, 24 `ADD COLUMN IF NOT EXISTS`, 10
   índices com guarda, 1 `DROP COLUMN IF EXISTS`, 2 `DROP CONSTRAINT IF EXISTS` e **zero**
   DDL destrutiva ou sem guarda. Tudo idempotente, e por isso voltar o código é seguro hoje.

A medição datada virou gate: `tests/test_schema_aditivo.py` quebra o CI se entrar DDL
destrutiva ou sem guarda. Não proíbe a migração, obriga a conversa.

### A1. Os seis gates ligados, e o CI deixou de ser vermelho crônico

O CI rodava **4 dos 6**. Faltavam `node extensor/harness/run.mjs` e
`python tools/audit_sharpenup.py`, justamente os que cobrem o robô que lê as casas. O
`CLAUDE.md` manda rodar o harness antes de todo commit que toque `extensor/`, e isso
dependia de alguém lembrar, numa semana em que o `extensor/` muda quase todo dia.

Ao ligá-los, as duas execuções anteriores já estavam vermelhas: o `check_docs` acusava 5
links quebrados e **nenhum era quebrado** (apontam para `../pack/`, a pasta irmã, que existe
na máquina do Feca e nunca existe no checkout). Era o `BACKLOG 1.7`, aberto desde julho.

**Alarme novo num painel que já pisca vermelho não alerta ninguém**, então o conserto veio
junto. Resultado: `✓ main CI` em 2m36s, os 11 passos verdes.

---

## 3. Os erros cometidos, e o que eles ensinaram

Esta seção existe porque os erros desta frente foram mais instrutivos que os acertos, e
todos são de uma família que volta.

**O gate que nasceu falso verde.** `test_schema_aditivo` passava com 10 testes verdes
inspecionando **string vazia**: o limpador de docstrings apagava o `SCHEMA_SQL`, que é uma
triple-quoted string. Oito mutações, oito escaparam. Quem pegou foi a bateria de mutação.
Entrou um piso de tamanho como rede contra a família inteira.

**As duas tentativas espertas no gate de links.** A primeira fazia o gate parar de reclamar
**também quando o link estivesse errado**, trocando alarme que toca sempre por alarme mudo.
A segunda inventou "se a pasta existe, dá para julgar", regra que parece certa e quebra no
caso mais simples: `../CLAUDE.md` aponta para o diretório acima do repo, que existe em toda
máquina. **Quem pegou foi o próprio teste novo, no CI.** A regra final não tem esperteza:
link que sai da raiz nunca reprova e sempre é relatado.

**O teste que reimplementava a varredura.** O mesmo arquivo de teste tinha um fallback com
`rglob` que pulava `Backups` na mão e não conhecia `_backups/`. Quando a s387 criou
`_backups/auditoria_masters_s387/`, o teste ficou vermelho sozinho por 2 links que não
existem para o gate de verdade. Corrigido chamando `_todos_md()` do próprio `check_docs`.

> **A família:** as três são a mesma coisa. Código de teste que não é o código sob teste, e
> heurística esperta no lugar da regra simples. O `CLAUDE.md` já dizia ("teste verde não é
> teste que detecta", "o teste reimplementa o código sob teste"), e ainda assim foi preciso
> cair três vezes para escrever isto.

**E um erro de medição que valia 1 KB.** O gate media o **mesmo arquivo** de dois jeitos:
`CLAUDE.md` dava 64,03 KB no disco (LF) e 65,04 KB no CI (CRLF), diferença de 1.035 bytes,
exatamente um por linha, contra um teto de 65 KB. Quem editava local lia "sobra 1 KB" e não
sobrava. O `_kb` passou a medir o conteúdo canônico e os dois lugares dizem 64,0 KB.

> **O método que fez a diferença:** parar de conferir só na máquina local e usar um
> `git clone .` para um temp, sem as pastas irmãs, que reproduz o checkout do CI. Foi ele
> que mostrou o estouro de tamanho **antes** do push.

---

## 4. O que foi levantado e decidido NÃO fazer

### O teto de custo do `/extrair`

Só o trial tem teto. Usuário aprovado extrai sem limite e nada avisa ninguém. Medido em
`uso_tokens`: R$ 287 em julho, R$ 448 em agosto, R$ 761 em setembro, a ~R$ 0,048 por
bilhete. O número não cresce com o tempo, cresce com **quem entra**.

**Decisão do Feca (22/09), e a razão fica registrada porque ela tem prazo:** a fase é de
testers e o custo está em movimento (troca de modelo, IAs em teste, tradutor em construção).
Travar teto em cima de número que está mudando congela a medição justamente quando ela é o
produto. Palavras dele: *"ter um teto agora é um tiro no pé"*.

Aberto como `BACKLOG 1.22`, com os três gatilhos que reabrem a discussão e um lembrete
agendado para 22/10/2026.

### O `figs.map` intermitente da aba Contas

Visto uma vez na varredura headless, não reproduzido em 11 tentativas. Sem repetição,
conserto seria chute em cima de sintoma. Fica esperando um relato de tester.

---

## 5. O levantamento de segurança e capacidade

**112 rotas auditadas por AST.** 76 com dependência de identidade, 36 sem. Das 36, nenhuma
entrega dado de outro dono: 12 resolvem no corpo, 9 são de autenticação, 3 são da extensão
(autenticam por código de 8 caracteres ou token de sessão) e 3 são a vitrine pública de
tipster, cujo `dono` sai de um allowlist e **nunca da URL**.

Isolamento por `dono` conferido no SQL das rotas por id, não só no Python.

**Postura geral, e é boa:** CSP, `nosniff`, `X-Frame-Options`, cookie `httponly` + `secure`
+ `samesite=lax`, bcrypt, guarda de Origin nos métodos que mutam, `_client_ip` pegando o
último valor do `X-Forwarded-For` (não spoofável), login sem enumeração de conta, handler
global que não vaza schema. Os furos encontrados são de **operação**, não de código.

**Capacidade:** 1 worker, pool de 5 conexões, sessões de captura em memória.

> ⚠️ **Processo único não é detalhe de deploy, é invariante do produto.** Sessão de captura,
> rate limit de login e caches vivem na memória. Se alguém subir um segundo worker para
> aguentar carga, o pareamento da extensão quebra em silêncio: o usuário conecta num worker
> e o dashboard faz poll no outro. Isto precisa estar escrito antes de virar a correção
> óbvia que alguém faz sob pressão.

**Duas rotas duplicadas:** `POST /tipsters/sugerir` está registrada em `main.py:4625` e
`:4826`. O Starlette casa na ordem de registro, então a segunda é código morto. Vale
descobrir qual é a viva antes que alguém mantenha o lado que não roda.

---

## 6. Go / no-go

| | Item | Estado |
|---|---|---|
| B1 | Backup com restore provado | **Feito** |
| B2 | A tela do usuário novo | **Feito** |
| B3 | Runbook de rollback | **Feito, falta o ENSAIO** |
| B4 | Teto de custo | Adiado por decisão, lembrete em 22/10 |
| A1 | Os seis gates no CI | **Feito, CI verde** |

**O único bloqueante que sobra é o ensaio do rollback, e ele é do Feca.** Cinco minutos no
Railway: pegar o deploy anterior, Redeploy, cronometrar, voltar. Enquanto a tabela de
registro do runbook estiver vazia, o caminho rápido é teoria.

**Fila seguinte, decidida e não executada:**

1. Runbook de suporte para *"a captura da casa X parou"*. É a pergunta que o tester vai
   fazer, e hoje a resposta só existe na cabeça do Feca.
2. A aba Métricas parar de emitir veredito sobre base vazia (`Solidez Muito Baixa`,
   `Win Rate 0,0%` com zero aposta encerrada), junto do `overview.js:293`.
3. As duas pequenas: a rota duplicada e documentar o processo único.
