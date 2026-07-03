# Plano de Redução de Risco — Planilhador

> **Origem:** auditoria crítica do Codex (`AUDITORIA_CRITICA_2026-07-02.md`, 50 achados) **re-verificada contra o código real** por 4 agentes em paralelo (segurança, matemática/finanças, banco/performance, arquitetura/API/produto) na sessão de 2026-07-03.
>
> **Propósito:** ser a bússola das próximas sessões. A auditoria original é o mapa de dívida; este arquivo é a **priorização calibrada para o estágio real do produto** (~3 operadores, dinheiro real, deploy Railway) — não para "SaaS de 1 milhão de usuários".
>
> **Tese que guia tudo:** *o objetivo agora não é adicionar features — é reduzir risco.* E "reduzir risco" para ESTE produto significa, nesta ordem: **integridade do dinheiro → 2 furos reais de segurança → rede de testes**. Não é tenancy platform, materialized views nem RBAC.

---

## Veredito da re-verificação

- Os 50 achados da auditoria são **quase todos factualmente reais** no código — pouquíssimo falso positivo.
- **Porém o placar 42/100 usa a régua errada** (SaaS de massa). Contra a régua do estágio atual, o núcleo está são:
  - Fórmulas de P/L (W/L/V/HW/HL) **matematicamente corretas** (verificado linha a linha).
  - Isolamento por `dono` **consistente em todas as rotas** verificadas.
  - Várias posturas "assustadoras" são **fail-closed por design**: `SESSION_SECRET` efêmero, senhas em env var, allowlist de modelos.
- **Achados da auditoria que caem de prioridade após verificação:**
  - `.env` (auditoria #1): segredo real existe em disco, mas está **gitignorado e NUNCA entrou em nenhum commit** (`git log --all --full-history -- .env` → vazio). Risco de versionamento = nulo.
  - CSRF (auditoria #3): mitigado por `SameSite=Lax` + corpo JSON.
  - Dashboard "sem login" (auditoria #8): expõe só a casca; dados retornam 401.
  - **"Ver como" (auditoria #24): achado INVERTIDO** — é decisão deliberada e documentada (sessão 82) que *previne* salvar na base errada.
  - Índices (auditoria #15): não é "sem índices" — o UNIQUE composto `(dono,casa,parceiro,…)` cobre por prefixo os filtros comuns. Falta só índice em `criado_em` e `codigo_bilhete`.
  - Fila/quota de IA (auditoria #18): já existe semáforo de concorrência de 4 por request; falta só teto global (irrelevante com 3 operadores).

---

## O QUE ATACAR

### 🟥 Tier 1 — Integridade do dinheiro (razão de existir do produto)

| # | Tarefa | Diagnóstico verificado | Local | Auditoria |
|---|---|---|---|---|
| T1.1 | **Guard de odd/stake inválido** | `_num` devolve `0.0` em erro de parse. Um `W` com odd ilegível vira **`−stake` silenciosamente** no P/L da grade e no agregado. Existe filtro `stake<=0 → skip`, mas **não** existe equivalente para `odd` em `dashboard_rows` nem em `calcular_pl`. Único caminho onde erro de dado corrompe dinheiro exibido sem alarme. | `repository.py` (`_num`, `calcular_pl`, `dashboard_rows`) | #26 |
| T1.2 | **Validação na fronteira da API** | `/salvar` valida só nº de colunas (≥10) + avisos não-bloqueantes; `PATCH` (`AtualizarBilheteRequest`) aceita `stake`/`odd`/`resultado`/`data` como `Optional[str]` cru. Lixo da IA ou erro de digitação entra e contamina o P/L derivado (`odd×stake`). Linha com <10 colunas é **descartada silenciosamente**. | `main.py` (`AtualizarBilheteRequest`, `/salvar`), `repository.py` (`parse_tsv`, `upsert_bilhetes`, `atualizar_bilhete`) | #21, #23 |
| T1.3 | **Golden tests das fórmulas** | Zero testes no repo (`tests/`, `test_*.py`, pytest → vazio). Nenhuma rede de regressão sobre dinheiro. É o **amplificador de todos os outros**: cria a base que torna qualquer refactor futuro seguro. Fazer **antes** de mexer em fórmula. | novo `tests/test_formulas.py` | #40 |
| T1.4 | **Câmbio histórico Polymarket** | `_cotacao_para` tenta PTAX do dia + 4 dias atrás; se falha, faz **fallback para cotação de HOJE**. Como `stake_brl = stake_usd × cotacao` e o P/L deriva de `stake_brl`, um câmbio errado escala stake **e** P/L em BRL — e o re-sync recalcula (valor não-determinístico). Mitigado (só dispara após 5 dias sem PTAX; aborta se hoje também falha), mas para bilhetes antigos o desvio é material. | `polymarket.py` (`_cotacao_para`, `coletar_bilhetes`) | #33 |

### 🟧 Tier 2 — Furos de segurança reais (baratos)

| # | Tarefa | Diagnóstico verificado | Local | Auditoria |
|---|---|---|---|---|
| T2.1 | **XSS no dashboard** | O `index.html` **já está seguro** (todo dado dinâmico passa por `esc()`). Mas os charts do dashboard injetam dados **crus**: `descricao`/`tipster`/`parceiro`/nomes de casa e esporte. `descricao` vem da transcrição de prints pela IA (conteúdo arbitrário). Vetor de **stored-XSS na fronteira operador→dono** no feed consolidado / "ver como". | `charts/apostas.js:104-112`, `charts/performance.js:46`, `charts/gestao.js:229,262`, `app.js:54-59` | #2 |
| T2.2 | **CSP + SRI** | Sem header/meta `Content-Security-Policy` no projeto; Chart.js e html2canvas carregados do cdnjs sem `integrity`. Isolado é baixo, mas **casa com T2.1**: sem CSP, nada barra XSS injetado. | `dash/index.html:54-56`, headers | #7 |

### 🟨 Tier 3 — Higiene barata, alta alavancagem

| # | Tarefa | Nota | Auditoria |
|---|---|---|---|
| T3.1 | **Rotacionar senha do banco + `.env.example`** | Já previsto na memória (fim das migrações). Segredo nunca vazou por git, mas rotação higieniza o disco compartilhado. | #1 |
| T3.2 | **Pin de dependências** | Todas as 8 deps com `>=` + deploy-on-push = armadilha real (um rebuild pode puxar `anthropic`/`fastapi` maior e quebrar em produção sem mudança de código). | #43 |
| T3.3 | **CI mínimo** | Pipeline rodando `compileall` + `audit_casas.py` + `check-tokens.mjs` + pytest (após T1.3). Guardrail antes do deploy automático. | #41 |
| T3.4 | **Docker hardening** | `USER` não-root + `HEALTHCHECK`. Barato. | #42 |
| T3.5 | **Matriz de confiabilidade das casas** | 12 casas com TODOs abertos de cashout/void/freebet/boost — quase todos "sem amostra ainda" (lacuna de localização, **não** erro de cálculo: a regra é global no MASTER_RESULTADO §5). Marcar cada casa: pronta / parcial / precisa-amostra. Bloquear promessa comercial de casa incompleta. | #45 |

---

## O QUE **NÃO** ATACAR AGORA (e por quê)

| Achado da auditoria | Por que fica de fora agora |
|---|---|
| Migrar dinheiro para `NUMERIC`/`DATE` (#13, #25) | `TEXT` é dívida **deliberada** (odd guarda precisão livre); `float` é inofensivo (arredonda por bilhete, erro << 1 centavo). Backfill caro sem ganho real hoje. Atrelar a necessidade concreta futura. |
| Quebrar monólitos `main.py` (1.340 l) / `index.html` (4.426 l) (#11, #12) | Pura manutenibilidade, **zero risco de runtime**. Grande superfície de regressão para pouco ganho. Não é redução de risco. |
| Tenancy formal / RBAC / billing / quotas (#5, #49) | Over-engineering para 3 operadores. Coluna `dono` faz o isolamento certo e consistente. |
| Fila/quota global de IA (#18) | Semáforo de concorrência de 4 por request já existe; 3 operadores não estouram limite Anthropic. |
| Materialized views / keyset / agregação SQL (#17, #20) | O dashboard puxar a base inteira e agregar no cliente é o **único a VIGIAR** conforme o volume cresce — mas ainda responde. Cache barato depois, se doer. |
| Rigor de Monte Carlo / p-value / solidez (#29, #30, #31) | Preocupação válida para **marketing**, não é bug. Correção barata = renomear para "indicador heurístico" + disclaimer. Não reconstruir o quant. |
| Máquina de token CSRF (#3) | `SameSite=Lax` + JSON já cobre o CSRF clássico. Validação de `Origin` é belt-and-suspenders barato se quisermos, mas não urgente. |
| Rework do "ver como" (#24) | Achado invertido — o design atual está correto. |
| `import_lava.py` caminho pessoal (#10) | Script one-off de migração, não roda em produção. Cosmético. |

---

## Sequência recomendada

1. **T1.3 (golden tests) primeiro** — a rede que torna T1.1/T1.2/T1.4 seguros de mexer.
2. **T1.1 (guard de odd inválida)** — maior corrupção de dinheiro exibido, correção cirúrgica.
3. **T1.2 (validação de fronteira)** — fecha a entrada de lixo.
4. **T2.1 + T2.2 (XSS + CSP)** — juntos, único risco de segurança Médio.
5. **T1.4 (câmbio Polymarket)** — dinheiro persistido, frequência baixa.
6. **Tier 3** conforme janela (T3.2/T3.3 combinam bem: pin + CI num golpe).

Cada item respeita os invariantes do `CLAUDE.md`: uma tarefa por vez, backup antes de editar, arquivo completo, `STATUS.md` atualizado no fim, commit + push juntos.

---

VERSÃO: 2026
CRIADO: 2026-07-03 (sessão pós-auditoria Codex)
FONTE: `AUDITORIA_CRITICA_2026-07-02.md` re-verificada por 4 agentes contra o código real
