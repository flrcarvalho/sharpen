## Arquitetura

**Veredito da área:** Sólido no núcleo, precisa de atenção — funciona bem em produção e tem decisões de modelagem maduras, mas carrega dívida estrutural crescente que vai doer conforme as casas mudam e a base escala (saúde amarela).

**Top 3 ações prioritárias:**
- **Autodiagnóstico em TODAS as casas-robô da extensão** (hoje só a Betfair tem). É o único achado *confirmado* e o de maior risco vivo: quando uma casa muda o DOM/API, a captura zera **silenciosamente** e o usuário só descobre reclamando. Adicionar sinal de "hook vivo / resposta vista / seletor casou" + telemetria leve de "captura vazia" ao backend detecta a quebra antes do cliente. [esforço: médio]
- **Criar índices na tabela `bilhetes`** — `(dono, criado_em)` para o feed/ordenação e índice parcial `(dono, codigo_bilhete)` para o pré-dedup. Hoje toda home do dashboard faz seq scan + sort por dono; com 25k+ linhas e supervisor consolidando N operadores por request, o custo cresce linear. Aditivo, idempotente, independe da migração NUMERIC. [esforço: pequeno — maior retorno por hora investida]
- **Separar `repository.py` em `domain.py` (puro) + `repository.py` (só DB).** Destrava teste unitário da regra mais crítica do sistema (`upsert_bilhetes`/dedup, ~270 l hoje sem teste viável), remove os stubs de asyncpg do conftest e reduz o god file. Movimentação mecânica, risco baixo. [esforço: médio]

> Nota: não há achados de severidade **crítica** nem **alta**. O topo da lista é **médio**. Nada corrompe dado ou vaza entre tenants nos caminhos atuais — os problemas são estruturais e de escala.

---

### Achados médios e altos (detalhados)

**1. Scraping acoplado a seletores/URLs hardcoded quebra silenciosamente** · *`extensor/content.js:1042-1097`* · **CONFIRMADO**
Todo o pipeline de robô depende de seletores CSS e regex de URL fixos por casa. Um build novo do front da casa (renomear classe, mudar path/shape da API) faz a captura retornar zero, com feedback genérico ("Nada coletado") que não diz **o que** quebrou. Só a Betfair tem autodiagnóstico. Sem telemetria ao backend, a quebra é invisível até o cliente reclamar. → Autodiagnóstico universal + evento leve de "captura vazia + casa + versão" ao backend.

**2. Comportamento por casa hardcoded em Python contradiz o invariante do projeto** · *`app/main.py:608-616, 989-1001, 1395-1465`*
O invariante diz "a casa localiza, o global calcula", mas decisões de ingestão por casa (quem faz pré-dedup por ID, quem inverte ordem de linhas, quem faz join de datas por CSV, print vs texto) estão gravadas como literais `casa_key.upper() in (...)` espalhadas por `main.py` e `captura.py`. A taxonomia de casa tem **dois lares**: o `.md` (para o LLM) e branches Python (para o pipeline). Adicionar casa que precise de pré-dedup exige editar `main.py`, não só criar um `.md`. → Registro declarativo `CASA_INGEST` (pre_dedup/ordem/modo/join_data) lido no boot; branches viram consulta a dado.

**3. `repository.py` mistura domínio puro e acesso a dados** · *`app/repository.py:70-547`*
~8 agregados de persistência async convivem com lógica de domínio pura (`calcular_pl`, `sugerir_tipster`, `_assinatura`, `corrigir_codigos_tsv`, `unidade_vigente`). A prova do acoplamento está no conftest: testar as fórmulas exige injetar stubs de asyncpg **antes** do import. A regra de dedup fica sem teste unitário viável. → `domain.py` (puro) + `repository.py` (só DB, importa domain).

**4. Contrato IA↔parser é TSV em markdown lido por regex, sem validação de forma** · *`app/main.py:640-651`* · [esforço: grande]
`parse_tsv` descarta silenciosamente qualquer linha com <10 colunas. Se o modelo variar o formato (nome do fence, header traduzido, coluna a menos), linhas somem sem erro — o usuário só percebe pela contagem. → Avaliar structured output / tool use da API Anthropic (schema de bilhete); no mínimo, contar `linhas_no_texto vs linhas_parseadas` e sinalizar divergência. Falha de formato deixa de ser perda silenciosa.

**5. `bf_inject` foge do modelo passivo: re-dispara até 400 requisições autenticadas com paginação adivinhada** · *`extensor/bf_inject.js:100-127`*
Ao contrário dos demais injects (read-only), o `bf_inject` re-emite ativamente a requisição de bilhetes com `credentials:include`, adivinhando o campo de paginação por heurística. Riscos: (a) disparar anti-bot/rate-limit da Betfair; (b) paginar em falso mutando o campo errado; (c) maior superfície de quebra quando o schema do POST mudar. → Preferir paginar pela própria UI e só ler as respostas; se o replay for necessário, backoff/jitter, teto conservador e campo de paginação travado por nome confirmado.

**6. Sem handshake de versão extensão↔backend; mapa casa→robô hardcoded por string de display** · *`extensor/popup.js:159-165`*
O modo (texto/print) é server-authoritative, mas **qual inject rodar** é decidido na extensão por string de display exata. Uma casa nova marcada como "texto" cai no robô genérico numa extensão antiga → coleta ruído. Pior: o casamento em `popup.js` é case-sensitive (`casa === 'BETesporte'`) enquanto `content.js` usa `toLowerCase` — um rename de display quebra a seleção de inject de forma inconsistente. → Enviar versão da extensão no `/conectar`, backend responde capacidades; normalizar comparação por `casa_key`, não display.

**7. Sessão de pareamento em memória — cliff de escala** · *`app/captura.py:14-16, 99-100`*
`_SESSOES` é um dict no processo (docstring assume 1 worker). Seguro hoje (1 uvicorn, 1 réplica Railway), mas adicionar `--workers N` ou réplicas faz `/parear` cair num worker e `/conectar` em outro → 404/401 intermitentes sem erro claro. Nada no código impede o escalonamento. → Guardrail no deploy ("captura exige 1 worker/1 réplica") ou migrar para store compartilhado (Redis com TTL) antes de qualquer autoscaling.

**8. Tabela `bilhetes` (a mais quente) sem índices além da unique** · *`app/database.py:8-29`*
Só PK + índice da UNIQUE. Sem `(dono, criado_em)` nem `(dono, codigo_bilhete)`, toda leitura do dashboard é seq scan + sort em memória por dono; o pré-dedup por código filtra sem índice. Custo cresce linear com a base e com o número de operadores consolidados. → Índices citados no Top 3 (aditivo, idempotente).

**9. Assinatura de dedup normaliza a odd mas usa o stake TEXT cru** · *`app/repository.py:558-562`*
Em bilhetes sem código, a odd passa por `_norm_odd` mas o stake entra como string literal. O mesmo bilhete gravado como `'250,00'` e depois `'250'` gera assinaturas diferentes → UPSERT não dedupa, insere **duplicata silenciosa**. Mesma classe de bug que motivou `_norm_odd`, com o stake de fora. Edição manual e re-extração são fontes reais. → Normalizador de stake na assinatura; cuidado com hashes já gravados (seguir `_assinatura_pos_edicao` ou só linhas novas, filosofia "deixa arder").

**10. Sem chaves estrangeiras — rename incompleto em `casa_config`** · *`app/repository.py:1499-1537`*
Vínculos por igualdade de texto. `renomear_tipster` propaga para `tipsters`, `bilhetes` e `tipster_unidade`, **mas não** para `casa_config.tipsters` (CSV) — após rename, a curadoria de casa-feudo aponta para o nome antigo. Impacto baixo hoje (matcher por casa ainda não plugado), mas morde quando a auto-atribuição entrar. → Incluir `casa_config` na transação de rename; estrategicamente, migrar tipster/parceiro para referência por id na leva do ADR-001.

**11. Coluna `dono` é TEXT livre com DEFAULT 'Feca' — misattribution por omissão** · *`app/database.py:41`*
`dono TEXT NOT NULL DEFAULT 'Feca'`, sem enum/CHECK/FK. Conveniência de migração virou footgun: qualquer INSERT futuro que esqueça `dono` grava na base do Feca — vazamento entre tenants por omissão, não por bug de filtro. Os caminhos atuais passam `dono` explicitamente (verificado), então **não há problema ativo**; o risco é para código novo. → Remover o DEFAULT (força falha explícita); quando existir a tabela `usuarios` do plano SaaS, adicionar FK.

---

### Achados médios e baixos (resumidos em tabela)

| # | Sev | Área | Achado | Local | Esforço |
|---|-----|------|--------|-------|---------|
| 12 | baixo | dívida | `main.py` é god file (2191 l): parsing/dedup por fonte + orquestração de streaming na camada HTTP, sem camada de serviço. Já é AUDITORIA #11 (deferida) — nuance nova: falta `extraction_service.py`/`ingest/parsers.py` | `main.py:269-479` | grande |
| 13 | baixo | dívida | Semântica de "mesmo bilhete" duplicada entre `main._scroll_key` e `repository._assinatura` — duas fontes de verdade, risco de drift | `main.py:742-761` | pequeno |
| 14 | baixo | dívida | Evolução de schema sem migrations: `SCHEMA_SQL` roda DDL + UPDATEs de dados + backfill a cada boot, para sempre (full-scan recorrente). Já é dívida #14 do ADR-001; ângulo novo = custo no boot | `database.py:57-67, 197-203` | médio |
| 15 | baixo | segurança | Content script aceita `postMessage` de qualquer origem; injects postam com `targetOrigin '*'` — iframe hostil no site da casa poderia forjar/capturar bilhetes (ameaça baixa: conta do próprio usuário) | `content.js:26-34` | pequeno |
| 16 | baixo | dívida | Mapa casa↔host duplicado em 3+ lugares (`captura.py`, `popup.js`, manifest, DOMINIOS) — mesma fragilidade dos "3 mapas de favicon"; drift silencioso ao mudar domínio | `popup.js:21-27` | médio |
| 17 | baixo | segurança | `/captura/conectar` anônimo, sem rate limit/lockout, vaza `dono`/`casa`/`parceiro` — código de 8 chars adivinhável só em teoria, mas sem defesa em profundidade | `main.py:1261-1269` | pequeno |
| 18 | baixo | segurança | `host_permissions '*://*/*'` + content script em toda página — casas são conjunto finito; modo print poderia usar `activeTab` + `scripting.executeScript` | `manifest.json:18-27` | médio |
| 19 | baixo | performance | Robôs genéricos fazem `querySelectorAll('*')` + `getComputedStyle` por nó, repetido até 400 voltas — pode travar aba em DOM pesado/virtualizado | `content.js:333-359` | pequeno |
| 20 | baixo | dados | Guard cross-dono pode descartar silenciosamente aposta idêntica **legítima** em conta compartilhada sem ID (edge estreito, colisão atual = 0) — documentar trade-off; considerar confirmação humana em vez de descarte | `repository.py:730-741` | pequeno |
| 21 | baixo | dívida | PKs inconsistentes: `bilhetes.id` SERIAL (int4) vs BIGINT/BIGSERIAL nas tabelas novas — atrapalha FK futura (cast) | `database.py:9` | trivial |
| 22 | info | dívida | Dinheiro/odd/data como TEXT + cálculo em float — **pendência conhecida e contida** (ADR-001); auditoria de 03/07 confirmou zero corrupção hoje (erro << 1 centavo). Plano NUMERIC(18,6)+Decimal aprovado, execução adiada até haver janela de backfill | `repository.py:64-110` | grande |

---

### Pontos positivos (o que está bem feito)

**Núcleo de modelagem — a base mais forte do sistema:**
- **P/L e escada de unidade nunca persistidos, sempre derivados** (`calcular_pl`, `unidade_vigente`/`pl_em_unidades`). Corrigir stake/odd/resultado retroativamente recalcula todo o histórico de graça; o app permanece read-only sobre o banco. É a decisão arquitetural mais elegante do sistema. *Preservar ao migrar para Decimal (ADR-001).*
- **Multi-tenancy disciplinado e fail-closed.** Toda query de dados é escopada por `dono` (conferido em 100% dos `FROM bilhetes`, inclusive subqueries de dedup). Separação `usuario_atual` vs `dono_efetivo` reavaliada por HMAC a cada request; `SESSION_SECRET` ausente cai em segredo efêmero (nunca default conhecido). UNIQUE `(dono, casa, parceiro, assinatura)` garante namespaces independentes.
- **Procedência do rótulo de tipster** (`origem_tipster`) deliberadamente fora de `_SIG_COLS` — impede que o futuro matcher aprenda das próprias sugestões (circularidade). Cuidado de qualidade de dados raro e correto para um sistema que vai virar ML.

**Robustez contra o LLM:**
- **`corrigir_codigos_tsv`** — correção determinística de IDs por edit-distance contra os IDs reais do texto-fonte, com gates calibrados (81 corrigidos, zero corrupção em 108 amostras). Mitigação certa, aplicada **fora** do prompt. *Bom candidato a `domain.py` + teste unitário.*
- **Streaming resiliente** — retry com backoff só quando nada foi emitido (não duplica tokens), keepalive 20s, continuação por `max_tokens`, cancelamento limpo. Um dos pontos mais delicados, bem coberto. *Referência ao migrar a lógica para a camada de serviço — migrar junto, não reescrever.*

**Extensão SharpenUp — decisões arquiteturais certas:**
- **Arquitetura passiva de leitura de API** (injects MAIN `sb/be/bn/bf_inject`): em vez de OCR/scraping de texto, embrulham `fetch`/`XHR` e leem as respostas JSON que a própria casa já baixa — dado exato (ID, odd, stake, `settledDate`) com auth da própria página. A abordagem mais robusta possível sem API oficial. *Ao adicionar casas-robô, espelhar `sb_inject` — não inventar scraping DOM (ver achado #5, o `bf_inject` é a exceção a corrigir).*
- **Modelo de token com defesa em profundidade**: código curto (8 chars sem ambíguos, TTL 15 min) → token de 32 bytes urlsafe, `compare_digest`, prune por TTL, tetos anti-OOM. Amarração casa↔host no cliente **e** backstop 409 no servidor (não dá para burlar). Isenção de CSRF estreita e justificada.