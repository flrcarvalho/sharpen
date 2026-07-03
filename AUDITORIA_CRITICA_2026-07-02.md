# Auditoria Critica do Projeto Planilhador

Data: 2026-07-02  
Objetivo: documentar riscos tecnicos, seguranca, produto, UX/UI, performance, banco, matematica e QA antes de qualquer lancamento comercial amplo.

## Resumo Executivo

O projeto tem valor de dominio: regras de apostas, casas, Polymarket, dashboard, extracao por IA e UI operacional ja estao bastante avancados.

Mas o estado atual ainda se parece mais com uma ferramenta interna evoluida do que com um SaaS global pronto para venda. Os maiores bloqueios sao:

- segredo real de banco presente em `.env`;
- ausencia de testes automatizados e CI;
- dados financeiros armazenados como `TEXT`;
- frontend monolitico com uso intenso de `innerHTML`;
- backend monolitico e acoplado;
- formulas financeiras sem suite de golden tests;
- falta de hardening de seguranca: CSRF, CSP, headers, tenancy formal, RBAC;
- ausencia de fila/quotas/rate limit global para chamadas caras de IA;
- varios TODOs de regras por casa;
- dashboard carregando/processando dados de forma que nao escala para SaaS grande.

Nota geral estimada: **42/100**.

## Verificacoes Executadas

Comandos executados:

```bash
python -m compileall app tools scripts
python tools/audit_casas.py
node scripts/tokens/check-tokens.mjs
```

Resultado:

- `compileall`: passou.
- `audit_casas.py`: passou para 12 casas.
- `check-tokens.mjs`: passou.

Importante: esses checks reduzem risco sintatico e alguns riscos de consistencia visual/dominio, mas nao cobrem seguranca, banco real, concorrencia, autorizacao, formulas financeiras, comportamento do frontend, nem regressao de produto.

## Notas Por Categoria

| Categoria | Nota | Diagnostico |
|---|---:|---|
| Arquitetura | 38/100 | Codigo concentrado em arquivos gigantes e responsabilidades misturadas. |
| Codigo | 45/100 | Funciona, mas com alto acoplamento e baixa testabilidade. |
| Seguranca | 30/100 | Segredos, CSRF, XSS, CSP e RBAC precisam de hardening antes de venda. |
| Banco | 35/100 | Tipos inadequados para dinheiro/data e ausencia de migracoes formais. |
| Performance | 40/100 | Nao escala bem para muitos usuarios/dados; calculos client/server pesados. |
| Matematica | 55/100 | Formulas principais fazem sentido, mas precisam de Decimal, testes e validacao estatistica. |
| UI | 50/100 | Visual evoluido, mas monolitico, dificil de manter e testar. |
| UX | 48/100 | Fluxos operacionais bons, mas confirmacoes, erros e acessibilidade precisam evoluir. |
| Testes | 5/100 | Praticamente inexistentes. |
| CI/CD | 20/100 | Sem pipeline formal de release. |
| Produto | 55/100 | Dominio rico, mas regras incompletas em algumas casas impedem promessa global. |

## Top Problemas Encontrados

### 1. Credencial real de banco no `.env`

- Categoria: Seguranca
- Gravidade: Critica
- Prioridade: P0
- Local: `.env`
- Problema: ha uma `DATABASE_URL` real no workspace.
- Impacto: quem obtiver esse arquivo pode acessar o banco.
- Como reproduzir: abrir `.env`.
- Correcao sugerida:
  - rotacionar imediatamente a senha do banco;
  - remover `.env` do workspace compartilhado;
  - garantir que secrets vivam apenas em Railway/env vars;
  - criar `.env.example` sem valores reais;
  - verificar se o segredo ja entrou em algum backup, zip ou commit historico.

### 2. Risco de XSS por uso extensivo de `innerHTML`

- Categoria: Seguranca / Frontend
- Gravidade: Critica
- Prioridade: P0
- Locais:
  - `app/static/index.html`
  - `app/static/dash/assets/js/charts/*.js`
- Problema: o frontend monta grandes blocos HTML por string e injeta com `innerHTML`.
- Impacto: se qualquer dado vindo de usuario, IA, banco ou API externa nao for escapado corretamente, pode ocorrer XSS.
- Como reproduzir: inserir valores maliciosos em campos como parceiro, descricao, tipster, mercado ou dados de API e observar renderizacao.
- Correcao sugerida:
  - trocar renderizacao de dados dinamicos para DOM APIs (`textContent`, `createElement`);
  - manter `innerHTML` somente para templates estaticos;
  - aplicar sanitizer confiavel se necessario;
  - adicionar CSP;
  - criar testes de XSS com payloads comuns.

### 3. Falta de CSRF robusto

- Categoria: Seguranca
- Gravidade: Alta
- Prioridade: P0
- Local: rotas mutaveis em `app/main.py`
- Problema: autenticacao usa cookie, mas mutacoes nao exigem token CSRF.
- Impacto: risco de acao indesejada via requisicoes cross-site, dependendo do contexto do navegador.
- Correcao sugerida:
  - implementar double-submit CSRF token;
  - validar `Origin`/`Referer` como camada adicional;
  - aplicar a todas as rotas `POST`, `PATCH`, `DELETE`.

### 4. Rate limit de login confiando em `x-forwarded-for`

- Categoria: Seguranca
- Gravidade: Alta
- Prioridade: P0
- Local: `app/main.py`, funcao `_client_ip`
- Problema: IP do cliente vem diretamente de `x-forwarded-for`.
- Impacto: atacante pode tentar burlar rate limit se header nao for sanitizado pelo proxy.
- Correcao sugerida:
  - confiar apenas em headers setados por proxy conhecido;
  - usar middleware/proxy config correta;
  - registrar tentativas por usuario + IP + fingerprint leve.

### 5. Usuarios e hierarquia hardcoded

- Categoria: Seguranca / Arquitetura
- Gravidade: Alta
- Prioridade: P0
- Local: `app/auth.py`
- Problema: usuarios (`Feca`, `Diogo`, `Lava`) e operadores estao fixos no codigo.
- Impacto: nao escala, dificulta auditoria, onboarding, offboarding e permissao por cliente.
- Correcao sugerida:
  - criar tabela `users`, `roles`, `memberships`, `tenant_users`;
  - mover hierarquia para banco;
  - adicionar auditoria de permissoes.

### 6. `SESSION_SECRET` efemero quando ausente

- Categoria: Seguranca / Operacao
- Gravidade: Alta
- Prioridade: P0
- Local: `app/auth.py`
- Problema: se `SESSION_SECRET` faltar, o app gera segredo aleatorio no boot.
- Impacto: sessoes caem a cada restart; comportamento perigoso em producao.
- Correcao sugerida:
  - em producao, falhar startup se `SESSION_SECRET` nao existir;
  - manter fallback efemero apenas para desenvolvimento local.

### 7. CDN sem SRI/CSP

- Categoria: Seguranca / Supply chain
- Gravidade: Alta
- Prioridade: P0
- Local: `app/static/dash/index.html`
- Problema: Chart.js/html2canvas/fontes externas sao carregadas sem Subresource Integrity e sem CSP forte.
- Impacto: comprometimento de CDN pode virar XSS.
- Correcao sugerida:
  - vendorizar bibliotecas;
  - ou adicionar `integrity` + `crossorigin`;
  - aplicar CSP restritiva.

### 8. Dashboard estatico abre sem login

- Categoria: Seguranca / Produto
- Gravidade: Alta
- Prioridade: P1
- Local: `app/main.py`, mount `/dashboard`
- Problema: HTML do dashboard pode carregar sem sessao; dados retornam 401, mas shell fica exposto.
- Impacto: exposicao desnecessaria da superficie do app.
- Correcao sugerida:
  - servir dashboard por rota autenticada;
  - ou redirecionar no frontend imediatamente se `/me` falhar.

### 9. Backups, artefatos locais e configuracoes no workspace

- Categoria: Seguranca / Release
- Gravidade: Alta
- Prioridade: P0
- Locais:
  - `Backups/`
  - `_backups/`
  - `.claude/settings.local.json`
  - `app/__pycache__/`
- Problema: muitos arquivos locais, antigos ou sensiveis convivem com codigo de produto.
- Impacto: risco de zip/deploy/revisao incorreta e vazamento.
- Correcao sugerida:
  - separar workspace de release;
  - limpar artefatos;
  - garantir que Docker context nao copie coisas indevidas;
  - revisar historico do git.

### 10. Script com caminho absoluto pessoal

- Categoria: Manutencao / Privacidade
- Gravidade: Alta
- Prioridade: P1
- Local: `scripts/import_lava.py`
- Problema: `CSV_PATH` aponta para caminho local pessoal.
- Impacto: script nao reprodutivel e pode expor estrutura local.
- Correcao sugerida:
  - receber caminho por argumento;
  - documentar uso;
  - remover referencia pessoal.

### 11. Backend monolitico

- Categoria: Arquitetura
- Gravidade: Alta
- Prioridade: P1
- Local: `app/main.py`
- Problema: arquivo com mais de 1100 linhas mistura auth, upload, IA, SSE, Polymarket, dashboard, parceiros e bilhetes.
- Impacto: alto risco de regressao e baixa testabilidade.
- Correcao sugerida:
  - dividir em routers: `auth`, `bilhetes`, `parceiros`, `extracao`, `polymarket`, `dashboard`;
  - extrair services;
  - manter `main.py` apenas como composicao da app.

### 12. Frontend monolitico

- Categoria: Arquitetura / Frontend
- Gravidade: Alta
- Prioridade: P1
- Local: `app/static/index.html`
- Problema: arquivo com mais de 4000 linhas.
- Impacto: dificil testar, revisar e manter; qualquer mudanca pode quebrar fluxo distante.
- Correcao sugerida:
  - separar JS, templates e CSS;
  - criar componentes;
  - considerar uma stack frontend com build se o produto continuar crescendo.

### 13. Dinheiro, odd e data como `TEXT`

- Categoria: Banco / Matematica
- Gravidade: Alta
- Prioridade: P1
- Local: `app/database.py`
- Problema: `stake`, `odd`, `data` sao texto.
- Impacto: parsing manual, risco de `0` silencioso, queries lentas e calculos inconsistentes.
- Correcao sugerida:
  - migrar para `NUMERIC(18,6)` ou equivalente;
  - datas em `DATE`;
  - manter texto original em campo separado se necessario;
  - validar antes de salvar.

### 14. Schema inline no startup

- Categoria: Banco / DevOps
- Gravidade: Alta
- Prioridade: P1
- Local: `app/database.py`
- Problema: alteracoes de schema rodam no boot.
- Impacto: deploy arriscado e dificil de auditar.
- Correcao sugerida:
  - adotar Alembic ou migracoes SQL versionadas;
  - separar migracao de runtime.

### 15. Indices insuficientes

- Categoria: Banco / Performance
- Gravidade: Alta
- Prioridade: P1
- Local: `app/database.py`
- Problema: filtros principais nao possuem indices compostos evidentes.
- Impacto: degradacao com volume.
- Correcao sugerida:
  - indices por `(dono, casa, parceiro, archived, criado_em)`;
  - `(dono, copy_state)`;
  - `(dono, extraction_state)`;
  - `(dono, codigo_bilhete)`;
  - avaliar indices parciais para pendentes/abertas.

### 16. `SELECT *` em rotas criticas

- Categoria: Performance / Manutencao
- Gravidade: Alta
- Prioridade: P1
- Local: `app/repository.py`
- Problema: listagem/export usa `SELECT *`.
- Impacto: payload maior e acoplamento ao schema.
- Correcao sugerida:
  - selecionar colunas explicitamente;
  - criar DTOs de resposta.

### 17. Dashboard carrega tudo e calcula em Python/JS

- Categoria: Performance / Escala
- Gravidade: Alta
- Prioridade: P1
- Local: `app/repository.py`, `app/static/dash/assets/js/*`
- Problema: feed do dashboard e agregacoes nao foram projetados para grandes volumes.
- Impacto: 1 milhao de usuarios inviavel.
- Correcao sugerida:
  - agregacoes SQL;
  - materialized views;
  - cache por periodo/filtro;
  - endpoints paginados por dimensao.

### 18. Chamadas de IA sem quota/fila global

- Categoria: Performance / Custo / Disponibilidade
- Gravidade: Alta
- Prioridade: P1
- Local: `app/main.py`, `/extrair`
- Problema: request pode disparar varias chamadas paralelas a Anthropic.
- Impacto: custo alto, DoS acidental, rate limit.
- Correcao sugerida:
  - fila de jobs;
  - limite por usuario/tenant;
  - budget mensal;
  - controle de concorrencia global;
  - idempotencia de extracao.

### 19. Cache warmer por instancia

- Categoria: Performance / Custo
- Gravidade: Media
- Prioridade: P2
- Local: `app/main.py`, `_cache_warmer`
- Problema: cada instancia pode manter loop de ping.
- Impacto: custo cresce com replicas.
- Correcao sugerida:
  - desabilitar por default;
  - fazer job unico;
  - controlar por env var.

### 20. Paginacao por offset

- Categoria: API / Performance
- Gravidade: Media
- Prioridade: P2
- Local: `/bilhetes`
- Problema: offset degrada em tabelas grandes.
- Impacto: listagem lenta.
- Correcao sugerida:
  - keyset pagination por `(criado_em, id)`.

### 21. PATCH aceita dados financeiros sem validacao forte

- Categoria: API / Matematica
- Gravidade: Alta
- Prioridade: P1
- Local: `app/main.py`, `AtualizarBilheteRequest`
- Problema: campos como `stake`, `odd`, `resultado`, `data` aceitam strings sem constraints robustas.
- Impacto: dados invalidos entram no banco e distorcem metricas.
- Correcao sugerida:
  - Pydantic validators;
  - enums;
  - validacao de formato monetario;
  - rejeitar valores impossiveis.

### 22. Delete em massa sem limite operacional

- Categoria: API / Produto
- Gravidade: Media
- Prioridade: P2
- Local: `DELETE /bilhetes`
- Problema: lista de IDs pode ser grande.
- Impacto: apagamento acidental amplo.
- Correcao sugerida:
  - limite por request;
  - soft delete;
  - auditoria;
  - confirmacao server-side para grandes volumes.

### 23. `/salvar` nao valida profundamente TSV

- Categoria: API / Dados
- Gravidade: Alta
- Prioridade: P1
- Local: `app/main.py`, `/salvar`
- Problema: dados extraidos por IA entram com validacao limitada.
- Impacto: IA pode gravar valores invalidos ou ambiguos.
- Correcao sugerida:
  - schema linha a linha;
  - erros por campo;
  - confidence gates;
  - bloquear salvar quando stake/odd/data forem invalidos.

### 24. Modo "ver como" pode confundir criacao de dados

- Categoria: Produto / UX
- Gravidade: Alta
- Prioridade: P1
- Local: `/extrair`, `/salvar`
- Problema: criacao usa usuario real, enquanto varias rotas usam dono efetivo.
- Impacto: operador/dono pode acreditar que esta salvando em outra base.
- Correcao sugerida:
  - UX explicita;
  - banner permanente;
  - logs;
  - talvez exigir escolha consciente do destino.

### 25. Calculos financeiros com `float`

- Categoria: Matematica
- Gravidade: Alta
- Prioridade: P1
- Local: `app/repository.py`, `app/polymarket.py`, JS do dashboard
- Problema: dinheiro calculado com `float`.
- Impacto: erros de arredondamento acumulados.
- Correcao sugerida:
  - usar `Decimal` no backend;
  - armazenar em `NUMERIC`;
  - definir politica de arredondamento.

### 26. Parser numerico devolve `0.0` em erro

- Categoria: Matematica / Dados
- Gravidade: Alta
- Prioridade: P1
- Local: `app/repository.py`, `_num`
- Problema: valor ilegivel vira zero.
- Impacto: erro de dado vira dado valido.
- Correcao sugerida:
  - retornar erro/None;
  - registrar campo invalido;
  - impedir calculo/salvamento.

### 27. Win rate conta `HW` como vitoria cheia

- Categoria: Matematica / Produto
- Gravidade: Media
- Prioridade: P2
- Local: `app/static/dash/assets/js/app.js`, `calcWR`
- Problema: `HW` entra como win integral.
- Impacto: win rate pode ficar inflado.
- Correcao sugerida:
  - decidir regra oficial;
  - possivelmente usar peso 0.5;
  - exibir metricas separadas.

### 28. Odd media pondera conjunto sem definicao clara

- Categoria: Matematica
- Gravidade: Media
- Prioridade: P2
- Local: `calcAvgOdd`
- Problema: filtro usa `odd > 0 && stake > 0`, sem explicitar void/cashout.
- Impacto: interpretacao ambigua.
- Correcao sugerida:
  - documentar se void entra;
  - criar teste;
  - alinhar backend/frontend.

### 29. p-value nao e estatistica validada para venda

- Categoria: Quant / Produto
- Gravidade: Alta
- Prioridade: P1
- Local: `_calcPValueMCraw`
- Problema: p-value bootstrap residual pode ser util como heuristica, mas nao deve ser vendido como probabilidade rigorosa de edge.
- Impacto: falsa confianca financeira.
- Correcao sugerida:
  - validar com quant;
  - renomear para indicador heuristico;
  - documentar limitacoes.

### 30. Monte Carlo simplificado demais

- Categoria: Quant / Risco
- Gravidade: Alta
- Prioridade: P1
- Local: `_calcMCdrawdownRaw`
- Problema: bootstrap iid de P/L ignora regime, ordenacao temporal, stake sizing, dependencia por tipster/casa/odd.
- Impacto: drawdown projetado pode ser subestimado.
- Correcao sugerida:
  - simular por unidades de risco;
  - estratificar por periodo/tipster/odd/casa;
  - exibir intervalo de incerteza.

### 31. Solidez e score arbitrario

- Categoria: Quant / Produto
- Gravidade: Media
- Prioridade: P2
- Local: `calcSolidez`
- Problema: pesos de p-value/drawdown/amostra/odd sao heuristicas.
- Impacto: selo pode influenciar decisao financeira indevidamente.
- Correcao sugerida:
  - renomear para "indicador heuristico";
  - calibrar com dados historicos;
  - explicar limitacoes.

### 32. Polymarket mistura odds de entrada e retorno realizado

- Categoria: Matematica / Produto
- Gravidade: Alta
- Prioridade: P1
- Local: `app/polymarket.py`, `_calc_odd`
- Problema: wins usam retorno realizado, losses/ativas usam `1/price`.
- Impacto: odd registrada pode significar coisas diferentes conforme resultado.
- Correcao sugerida:
  - guardar `entry_odd`, `realized_odd`, `avg_price`;
  - usar campo correto em cada dashboard.

### 33. Fallback de cambio historico para cotacao atual

- Categoria: Matematica / Polymarket
- Gravidade: Alta
- Prioridade: P1
- Local: `app/polymarket.py`, `_cotacao_para`
- Problema: se nao encontra PTAX da data, pode usar cotacao de hoje.
- Impacto: historico em BRL fica incorreto.
- Correcao sugerida:
  - exigir cotacao historica;
  - armazenar fonte/data da cotacao;
  - permitir reprocessamento.

### 34. Inline handlers no HTML

- Categoria: Frontend / Manutencao
- Gravidade: Media
- Prioridade: P2
- Local: `app/static/index.html`
- Problema: muitos `onclick` inline.
- Impacto: dificulta CSP forte, testes e manutencao.
- Correcao sugerida:
  - usar `addEventListener`;
  - remover handlers inline.

### 35. CSS e cores literais demais

- Categoria: UI / Design System
- Gravidade: Media
- Prioridade: P2
- Local: `components.css`, arquivos JS/HTML
- Problema: `check-tokens` passou, mas ainda ha muitas cores literais.
- Impacto: drift visual e manutencao dificil.
- Correcao sugerida:
  - expandir tokens;
  - lint de design;
  - reduzir estilos inline.

### 36. Dependencia de Google Fonts

- Categoria: UI / Performance / Privacidade
- Gravidade: Media
- Prioridade: P2
- Local: `app/static/dash/index.html`
- Problema: fontes carregadas externamente.
- Impacto: latencia, privacidade e dependencia externa.
- Correcao sugerida:
  - self-host das fontes.

### 37. `alert`/`confirm` em fluxo critico

- Categoria: UX
- Gravidade: Media
- Prioridade: P2
- Local: `app/static/index.html`
- Problema: confirmacoes nativas para arquivar/deletar/erros.
- Impacto: UX pobre, pouca informacao contextual.
- Correcao sugerida:
  - modais proprios;
  - undo/soft delete;
  - mensagens mais claras.

### 38. Mensagens de erro genericas

- Categoria: UX / Suporte
- Gravidade: Media
- Prioridade: P2
- Local: frontend e backend
- Problema: erros como "Erro de rede", "Erro ao processar".
- Impacto: usuario nao sabe agir; suporte fica dificil.
- Correcao sugerida:
  - codigos de erro;
  - mensagens orientadas a acao;
  - logs correlacionaveis.

### 39. Acessibilidade insuficientemente garantida

- Categoria: UI / Acessibilidade
- Gravidade: Media
- Prioridade: P2
- Local: botoes simbolicos, tabelas, inputs dinamicos
- Problema: varios controles usam simbolos/HTML dinamico.
- Impacto: teclado/leitor de tela podem falhar.
- Correcao sugerida:
  - `aria-label`;
  - foco visivel;
  - navegacao por teclado;
  - testes Playwright/axe.

### 40. Ausencia de testes automatizados

- Categoria: QA
- Gravidade: Critica
- Prioridade: P0
- Local: projeto
- Problema: nao ha suite de testes real.
- Impacto: regressao silenciosa em dinheiro, auth, IA e banco.
- Correcao sugerida:
  - `pytest`;
  - fixtures de formulas;
  - testes de rotas;
  - Playwright para fluxos principais.

### 41. Ausencia de CI

- Categoria: CI/CD
- Gravidade: Alta
- Prioridade: P1
- Local: projeto
- Problema: nao ha pipeline `.github`/equivalente.
- Impacto: deploy manual e sem guardrails.
- Correcao sugerida:
  - pipeline rodando compile, testes, audit scripts, token check e lint.

### 42. Docker sem hardening

- Categoria: DevOps / Seguranca
- Gravidade: Alta
- Prioridade: P1
- Local: `Dockerfile`
- Problema: imagem roda como root, sem healthcheck e sem pin forte.
- Impacto: risco operacional e de seguranca.
- Correcao sugerida:
  - usuario nao-root;
  - `HEALTHCHECK`;
  - lockfile;
  - multi-stage se necessario.

### 43. Dependencias com `>=`

- Categoria: Supply chain / Reprodutibilidade
- Gravidade: Media
- Prioridade: P2
- Local: `app/requirements.txt`
- Problema: versoes abertas.
- Impacto: build futuro pode quebrar ou mudar comportamento.
- Correcao sugerida:
  - gerar lockfile;
  - pin exato;
  - auditoria de vulnerabilidades.

### 44. Observabilidade insuficiente

- Categoria: Operacao
- Gravidade: Alta
- Prioridade: P1
- Local: backend
- Problema: logs sem request id, tenant, job id, tracing e metricas.
- Impacto: dificil debugar producao.
- Correcao sugerida:
  - structured logging;
  - request id;
  - metrics para IA, banco, erros, latencia.

### 45. TODOs em regras de casas

- Categoria: Produto / Dominio
- Gravidade: Alta
- Prioridade: P1
- Local: `casas/*.md`
- Problema: varias casas ainda tem pendencias sobre bonus, cashout, void/freebet.
- Impacto: extracao pode estar errada.
- Correcao sugerida:
  - matriz de confiabilidade por casa;
  - bloquear casas incompletas para cliente final;
  - exigir amostras reais.

### 46. Modelos Anthropic hardcoded

- Categoria: Configuracao
- Gravidade: Media
- Prioridade: P2
- Local: `app/config.py`
- Problema: modelos permitidos estao fixos no codigo.
- Impacto: mudancas exigem deploy.
- Correcao sugerida:
  - env/config;
  - feature flag por tenant;
  - fallback controlado.

### 47. RPCs publicos no Polymarket

- Categoria: Seguranca / Disponibilidade
- Gravidade: Media
- Prioridade: P2
- Local: `app/polymarket.py`
- Problema: usa RPCs publicos externos.
- Impacto: privacidade, instabilidade e rate limit.
- Correcao sugerida:
  - provider confiavel;
  - cache;
  - timeouts e circuit breaker.

### 48. Mojibake / encoding quebrado em comentarios e strings

- Categoria: Manutencao / UX
- Gravidade: Media
- Prioridade: P2
- Local: varios arquivos
- Problema: textos aparecem com caracteres corrompidos em alguns outputs.
- Impacto: manutencao ruim e risco de microcopy quebrada.
- Correcao sugerida:
  - normalizar UTF-8;
  - revisar encoding do editor;
  - evitar salvar arquivos com charset errado.

### 49. Multi-tenancy ainda logica, nao plataforma

- Categoria: Arquitetura / Produto
- Gravidade: Critica
- Prioridade: P0
- Local: arquitetura geral
- Problema: isolamento por `dono` existe, mas nao ha tenancy formal com billing, quotas, RBAC, auditoria, limites e backup/restore por cliente.
- Impacto: nao e SaaS global maduro.
- Correcao sugerida:
  - criar entidade `tenant`;
  - separar usuarios/roles/operadores;
  - quotas e auditoria por tenant;
  - politicas de retencao.

### 50. Falta de estrategia de beta/release

- Categoria: Produto / Operacao
- Gravidade: Alta
- Prioridade: P1
- Local: processo
- Problema: nao ha definicao visivel de beta fechado, criterios de pronto, SLO, rollback e suporte.
- Impacto: lancamento global seria arriscado.
- Correcao sugerida:
  - beta fechado;
  - checklist de release;
  - monitoramento;
  - plano de rollback.

## Formulas Encontradas E Avaliacao

### P/L

Local: `app/repository.py`, `calcular_pl`

Formula:

- `W`: `stake * odd - stake`
- `L`: `0 - stake`
- `V`: `stake - stake = 0`
- `HW`: `(stake / 2) * odd + (stake / 2) - stake`
- `HL`: `(stake / 2) - stake`

Veredito:

- Conceitualmente correta para a regra descrita.
- Problema: usa `float` e arredonda cedo.
- Correcao: usar `Decimal`, armazenar em `NUMERIC`, criar golden tests.

### ROI

Locais:

- `app/repository.py`, `resumo_conta`
- `app/static/dash/assets/js/app.js`, `calcROI`

Formula:

```text
ROI = soma(P/L) / soma(turnover) * 100
```

Turnover exclui `V`.

Veredito:

- Formula padrao e aceitavel.
- Precisa documentar claramente o tratamento de void, cashout, freebet e bonus.

### Turnover

Local: `calcTurnover`

Formula:

```text
turnover = soma(stake das apostas cujo resultado != V)
```

Veredito:

- Definicao coerente se void for stake devolvida.
- Precisa de testes para todos os resultados.

### Win Rate

Local: `calcWR`

Formula atual:

```text
win_rate = quantidade(W ou HW) / quantidade(resultado != V) * 100
```

Veredito:

- Questionavel: `HW` conta como vitoria cheia.
- Alternativas:
  - `HW = 0.5 win`;
  - exibir win rate bruto e win rate ajustado;
  - documentar regra oficial.

### Odd Media

Local: `calcAvgOdd`

Formula:

```text
odd_media = soma(odd * stake) / soma(stake)
```

Veredito:

- Matematicamente correta como media ponderada.
- Precisa definir se void/cashout/freebet entram.

### Drawdown Real

Local: `calcDrawdownReal`

Formula:

- agrega P/L por dia;
- ordena dias cronologicamente;
- acumula curva;
- pico = maior acumulado anterior;
- drawdown = `pico - acumulado_atual`;
- percentual = `drawdown / (BASE_BANK + pico) * 100`.

Veredito:

- Boa base.
- Problema: `BASE_BANK = 100000` hardcoded.
- Correcao:
  - parametrizar banca inicial por tenant/conta/periodo;
  - testar com series conhecidas.

### Monte Carlo

Local: `_calcMCdrawdownRaw`

Metodo:

- bootstrap iid dos P/Ls historicos;
- simula curvas aleatorias;
- calcula drawdowns medios e percentis.

Veredito:

- Util como heuristica visual.
- Nao deve ser vendido como risco quantitativo robusto sem validacao.
- Ignora dependencia temporal, stake sizing, mudanca de regime, tipster, casa e faixa de odd.

### p-value

Local: `_calcPValueMCraw`

Metodo:

- bootstrap residual comparando yield observado.

Veredito:

- Deve ser tratado com extrema cautela.
- Nao chamar de "probabilidade de ser acaso" sem validacao estatistica.
- Recomendacao: renomear para indicador heuristico ou validar com especialista quant.

### Polymarket

Locais:

- `_calc_odd`
- `coletar_bilhetes`
- `_cotacao_para`

Problemas:

- odd pode representar retorno realizado em wins e entrada em outros casos;
- fallback de cambio historico para cotacao atual pode corromper historico;
- stake original USD e stake BRL precisam de rastreabilidade.

Correcao:

- armazenar `stake_usd`, `stake_brl`, `fx_rate`, `fx_date`, `fx_source`;
- separar `entry_odd` de `realized_odd`;
- nao gravar BRL sem cambio historico confiavel.

## Quick Wins Recomendados

1. Rotacionar senha do banco imediatamente.
2. Remover `.env` real e criar `.env.example`.
3. Limpar `Backups/`, `_backups/`, `__pycache__` do pacote de release.
4. Adicionar CI minimo.
5. Criar testes de formulas financeiras.
6. Validar `stake`, `odd`, `data`, `resultado` antes de salvar/editar.
7. Adicionar CSP inicial.
8. Adicionar validacao de `Origin/Referer` nas rotas mutaveis.
9. Criar matriz de confiabilidade das casas.
10. Pin de dependencias.

## Plano Recomendado De 5 Dias

### Dia 1: Seguranca P0

- Rotacionar banco.
- Remover segredos.
- Revisar backups.
- CSP inicial.
- CSRF/Origin check.
- Bloquear startup sem `SESSION_SECRET` em producao.

### Dia 2: Matematica E Testes

- Criar `tests/test_formulas.py`.
- Cobrir `W`, `L`, `V`, `HW`, `HL`.
- Cobrir ROI, turnover, win rate.
- Cobrir parser numerico.
- Cobrir Polymarket basico.

### Dia 3: Validacao De Dados

- Pydantic validators para bilhetes.
- Rejeitar stake/odd/data invalidos.
- Impedir que parser silenciosamente transforme erro em zero.
- Criar mensagens de erro por campo.

### Dia 4: CI E Banco

- Pipeline rodando:
  - compile;
  - unit tests;
  - audit casas;
  - check tokens.
- Criar indices iniciais.
- Planejar migracao para `NUMERIC` e `DATE`.

### Dia 5: Produto E Casas

- Marcar casa como:
  - pronta;
  - parcial;
  - bloqueada;
  - precisa amostra.
- Bloquear comercialmente casas incompletas.
- Revisar TODOs de cashout, void, bonus, freebet.

## Melhorias Estruturais

### Backend

- Dividir `main.py` em routers:
  - `auth.py`;
  - `bilhetes.py`;
  - `parceiros.py`;
  - `extracao.py`;
  - `polymarket.py`;
  - `dashboard.py`.
- Criar camada de services.
- Criar DTOs de entrada/saida.
- Tirar regras de negocio do controller.

### Banco

- Alembic ou migracoes SQL versionadas.
- `NUMERIC` para dinheiro/odds.
- `DATE` para datas.
- Indices compostos.
- Auditoria de alteracoes.
- Soft delete para bilhetes.

### Frontend

- Quebrar `index.html`.
- Remover inline handlers.
- Reduzir `innerHTML`.
- Criar componentes.
- Melhorar acessibilidade.
- Criar testes Playwright.

### IA

- Fila de jobs.
- Quotas por usuario/tenant.
- Idempotencia.
- Persistencia do estado da extracao.
- Auditoria de custo por job.

## Melhorias Para Escala Mundial

- Tenancy formal.
- RBAC no banco.
- Billing/planos/quotas.
- Logs estruturados.
- Metricas por tenant.
- Backups e restore por cliente.
- Rate limit global.
- Cache de dashboard.
- Materialized views.
- Observabilidade de IA/custos.
- Politica de retencao de dados.
- Termos de uso e disclaimers financeiros.

## Melhorias De UX

- Substituir `alert/confirm` por modais contextuais.
- Adicionar undo para delete/arquivar.
- Explicar melhor modo "ver como".
- Estados de loading por acao.
- Erros acionaveis.
- Empty states por contexto.
- Status de confiabilidade da casa.
- Aviso quando casa tem regra incompleta.

## Melhorias De UI

- Remover estilos inline progressivamente.
- Self-host fonts.
- Aumentar uso de tokens.
- Verificar contraste.
- Verificar foco visivel.
- Padronizar botoes simbolicos com `aria-label`.
- Criar regressao visual.

## Melhorias De Performance

- Agregar dashboard no banco.
- Keyset pagination.
- Cache por filtros.
- Indices compostos.
- Evitar carregar tudo no frontend.
- Virtualizacao onde necessario.
- Fila para IA.
- Rate limit por tenant.

## Melhorias De Seguranca

- Rotacionar segredos.
- CSRF.
- CSP.
- SRI ou vendorizar CDNs.
- RBAC no banco.
- Audit log.
- Trusted proxy config.
- Headers de seguranca.
- Validacao forte de input.
- Sanitizacao de HTML.
- Secrets manager.

## Melhorias Matematicas

- `Decimal` no backend.
- `NUMERIC` no banco.
- Golden tests.
- Separar entry odd e realized odd.
- Parametrizar banca inicial.
- Revisar win rate de `HW`.
- Validar p-value/Monte Carlo com criterio quant.
- Exibir limitacoes de metricas heuristicas.

## Melhorias De Arquitetura

- Modularizar backend.
- Modularizar frontend.
- Separar dominio de infraestrutura.
- Criar camada de validacao central.
- Criar contrato API.
- Versionar API.
- Introduzir migrations.
- Criar services para formulas.

## Melhorias Para Manutencao Futura

- CI obrigatorio.
- Testes unitarios e E2E.
- Lint/format.
- Documentacao de arquitetura.
- ADRs para decisoes de negocio.
- Guia de release.
- Matriz de confiabilidade por casa.
- Ownership por modulo.

## Divida Tecnica Principal

1. Dados financeiros como texto.
2. Ausencia de testes.
3. Frontend monolitico.
4. Backend monolitico.
5. Sem migracoes.
6. Sem CI.
7. Sem RBAC real.
8. Sem fila/quotas para IA.
9. Regras incompletas em casas.
10. Metricas quant sem validacao suficiente para venda.

## O Que Impediria Uso Por 1 Milhao De Usuarios

- Banco e queries nao preparados para escala.
- Dashboard carrega dados demais.
- IA sem fila, quota e controle de custo.
- Multi-tenancy incompleta.
- Ausencia de CI/testes.
- Seguranca ainda insuficiente.
- Dados financeiros sem tipos numericos.
- Observabilidade insuficiente.
- Processo de release inexistente.
- Produto ainda depende de regras manuais incompletas por casa.

## Recomendacao Final

Nao lancar globalmente agora.

Recomendacao:

1. fazer sprint P0 de seguranca;
2. criar testes matematicos;
3. validar dados antes de salvar;
4. colocar CI;
5. rodar beta fechado com poucos usuarios reais;
6. so depois planejar lancamento comercial mais amplo.

O nucleo do produto e promissor, mas precisa de uma etapa clara de estabilizacao. O objetivo agora nao deve ser adicionar features; deve ser reduzir risco.
