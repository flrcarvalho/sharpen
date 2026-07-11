# AUDITORIA 2026 — documento único e vivo

> **O que é:** a auditoria consolidada do Planilhador. **Funde e substitui** três documentos
> antigos que tratavam do mesmo assunto em momentos diferentes:
> - `AUDITORIA_CRITICA_2026-07-02.md` (os 50 achados originais do Codex)
> - `RELATORIO_CORRECOES_2026-07-03.md` (o que foi corrigido na primeira leva)
> - `RISK_REDUCTION_PLAN.md` (a priorização calibrada)
>
> Aqueles três viraram **histórico**. A partir daqui, a fonte de verdade do estado de risco é
> **este arquivo**. Ele foi reconciliado contra o código real em **2026-07-10** (commit `c4b49fd`,
> sessão 122), rodando `pytest`, `grep` e leitura dos arquivos citados.
>
> **Regra:** ao resolver/adiar um achado, atualize a linha dele aqui (status + evidência). Não crie
> um relatório novo — mantenha um só documento vivo.

---

## 1. Placar de hoje (2026-07-10)

| Status | Qtde | Leitura |
|---|---:|---|
| ✅ Resolvido | 12 | inclui **3 a mais** do que o relatório de 03/07 registrava (ver §4) |
| 🟡 Parcial | 9 | quick-win feito, estrutural adiado (inclui as métricas quant #29-31: disclaimer já no tooltip, falta o rótulo) |
| 🔴 Aberto | 17 | concentrados em P2 (UX / manutenção) |
| ⏸️ Adiado-por-design | 12 | dívida consciente, não esquecimento |

**Veredito:** todos os **P0 de integridade de dinheiro e de segurança barata** foram resolvidos ou
conscientemente adiados. Os 🔴 restantes **não bloqueiam a operação atual** (3–7 operadores, dinheiro
real, deploy Railway) — bloqueiam o salto para "SaaS global de 1M usuários", que **não é a fase atual**.
A nota 42/100 da auditoria original media prontidão para venda global; para a operação real de hoje o
sistema está de pé, testado (65/65) e conectado (ver `docs/` do smoke test na §5).

---

## 2. Os 50 achados — status reconciliado

Legenda: ✅ Resolvido · 🟡 Parcial · 🔴 Aberto · ⏸️ Adiado-por-design

| # | Achado | Prio | Status | Evidência no código |
|---|---|---|---|---|
| 1 | Credencial de banco no `.env` | P0 | 🟡 | `.env.example` existe; `.env` gitignorado e nunca commitado. **Falta:** rotação humana no Railway (`docs/runbook-rotacao-postgres.md`) |
| 2 | XSS por `innerHTML` | P0 | ✅ | `esc()` em `dash/.../data.js` reusado nos charts; `index.html` já usava `esc()` |
| 3 | CSRF robusto | P0 | ✅ | `_csrf_origin_guard` `main.py:221` (valida Origin/Referer) — **feito depois** do relatório |
| 4 | Rate limit confia em `X-Forwarded-For` | P0 | 🔴 | `_client_ip` `main.py:1047` usa `xff.split(",")[0]` sem proxy confiável. Baixo |
| 5 | Usuários hardcoded | P0 | ⏸️ | `auth.py` (dict `USUARIOS`); fail-closed. Endereçado pelo `PLANO_MULTIUSUARIO_2026` |
| 6 | `SESSION_SECRET` efêmero | P0 | ⏸️→🔴 | `auth.py:37` gera `token_hex(32)` e só **avisa**. **Correção barata pendente:** fail-closed em produção |
| 7 | CDN sem SRI/CSP | P0 | ✅ | Vendorizado (`dash/vendor/chart.umd.js`, `html2canvas.min.js`, ref. `dash/index.html:54`) + CSP `main.py:166` |
| 8 | Dashboard abre sem login | P1 | 🟡 | `/dashboard/` → `RedirectResponse('/app')` `main.py:1022`; dados dão 401, shell ainda monta |
| 9 | Backups/artefatos no workspace | P0 | 🔴 | `Backups/`, `__pycache__/` no repo. **Verificar `.dockerignore`** (ver §3 reorg) |
| 10 | `import_lava.py` caminho pessoal | P1 | 🔴 | `scripts/import_lava.py:23` `CSV_PATH = r'C:\Users\Fernando\...'`. Script one-off |
| 11 | Backend monolítico | P1 | ⏸️ | `main.py` ~1.8k linhas. Manutenibilidade, zero risco runtime |
| 12 | Frontend monolítico | P1 | ⏸️ | `index.html` 249KB. Dívida do `PLANO_CASCA_UNIFICADA` |
| 13 | Dinheiro/odd/data como TEXT | P1 | ⏸️ | Sem colunas canônicas em `database.py`. **ADR-001** escrito, não executado |
| 14 | Schema inline no boot | P1 | ⏸️ | `SCHEMA_SQL` roda no boot. ADR-001 Fase 0 |
| 15 | Índices insuficientes | P1 | 🔴 | Falta índice em `criado_em`/`codigo_bilhete`. Baixo no volume atual |
| 16 | `SELECT *` em rotas | P1 | 🔴 | 2 ocorrências em `repository.py` |
| 17 | Dashboard carrega tudo | P1 | 🟡 | gzip `/dashboard/data` `main.py:1580` (**ADR-002 Fase 1**); agregação SQL adiada |
| 18 | IA sem quota/fila global | P1 | 🟡 | Semáforo(4) por request; teto global ausente. Aceito p/ poucos operadores |
| 19 | Cache warmer por instância | P2 | 🔴 | Não endereçado |
| 20 | Paginação por offset | P2 | 🔴 | Não endereçado (baixo) |
| 21 | PATCH sem validação forte | P1 | ✅ | `_BilheteFinanceiroBase` + `field_validator` `main.py:1716`, herdado por `AtualizarBilheteRequest` |
| 22 | Delete em massa sem limite | P2 | 🔴 | Não endereçado |
| 23 | `/salvar` não valida TSV | P1 | ✅ | `validar_linhas` `repository.py:286` (rejeição linha-a-linha), usado em `main.py:1414` — **feito depois** |
| 24 | Modo "ver como" confunde | P1 | ⏸️ | Achado invertido; comportamento é proteção deliberada (sessão 82) |
| 25 | Cálculos com `float` | P1 | ⏸️ | Ainda `float`; erro << 1 centavo (verificado). ADR-001 |
| 26 | Parser devolve `0.0` em erro | P1 | ✅ | `_num_or_none` `repository.py:33` + guard de odd em `calcular_pl` (T1.1) |
| 27 | Win rate conta HW cheio | P2 | 🔴 | `calcWR` (`app.js:109`) usa `['W','HW']` como win integral. **Decisão do Feca:** HW=0,5? |
| 28 | Odd média sem definição de void | P2 | 🔴 | Não documentado/testado explicitamente |
| 29 | p-value não validado | P1 | 🟡 | **Disclaimer JÁ existe** no tooltip (`overview.js:299`, `performance.js:974`): _"Indicador heurístico (bootstrap)… não é prova estatística nem recomendação"_. Falta só (decisão do Feca) renomear o **rótulo-título** "p-value" |
| 30 | Monte Carlo simplista | P1 | 🟡 | Tooltip já marca _"projetado · média"_ e _"Não aconteceu — é estimativa"_ (`overview.js:272`). Método bootstrap não reconstruído (mas honesto no rótulo) |
| 31 | Solidez arbitrária | P2 | 🟡 | Rotulado _"índice composto"_; herda o disclaimer do p-value. Pesos seguem heurísticos |
| 32 | Polymarket mistura entry/realized odd | P1 | 🔴 | Só o câmbio foi tratado; `_calc_odd` ainda mistura. **Maior risco quant aberto** |
| 33 | Fallback de câmbio p/ cotação de hoje | P1 | ✅ | Janela 10 dias + `CambioIndisponivel` `polymarket.py:55,148,524` (T1.4) |
| 34 | Inline handlers no HTML | P2 | ⏸️ | `onclick` inline seguem; por isso CSP mantém `'unsafe-inline'` |
| 35 | Cores literais | P2 | 🟡 | `check-tokens` verde; drift residual segue |
| 36 | Google Fonts externo | P2 | 🔴 | `dash/index.html:26` ainda carrega `fonts.googleapis.com`. Só as libs JS foram vendorizadas |
| 37 | `alert`/`confirm` em fluxo crítico | P2 | 🔴 | Não endereçado |
| 38 | Mensagens de erro genéricas | P2 | 🔴 | Não endereçado |
| 39 | Acessibilidade | P2 | 🔴 | Não endereçado |
| 40 | Ausência de testes | P0 | ✅ | **65 testes** em `tests/` (formulas, dedup, betfair, ordem_bet365) |
| 41 | Ausência de CI | P1 | ✅ | `.github/workflows/ci.yml`: compileall + pytest + audit_casas + check-tokens |
| 42 | Docker sem hardening | P1 | ✅ | `Dockerfile`: `appuser` não-root + `HEALTHCHECK` |
| 43 | Dependências com `>=` | P2 | ✅ | `requirements.txt` com tetos `<major`. Lockfile real ainda pendente |
| 44 | Observabilidade insuficiente | P1 | 🔴 | Sem `request_id`/structured logging. **Sobe na lista quando escalar** |
| 45 | TODOs em regras de casas | P1 | ✅ | `CASAS_CONFIABILIDADE.md` (matriz 13 casas). Amostras seguem pendentes |
| 46 | Modelos Anthropic hardcoded | P2 | ⏸️ | `config.py:15` `ALLOWED_MODELS` fixo (decisão humana consciente) |
| 47 | RPCs públicos Polymarket | P2 | 🔴 | Não endereçado |
| 48 | Mojibake/encoding | P2 | 🔴 | Não tratado sistematicamente |
| 49 | Multi-tenancy só lógica | P0 | ⏸️ | Isolamento por `dono` consistente; sem RBAC/billing formal (over-eng p/ hoje) |
| 50 | Falta estratégia de beta/release | P1 | 🟡 | CI dá guardrail; sem plano formal de SLO/rollback |

---

## 3. Fórmulas financeiras — veredito

Todas verificadas **matematicamente corretas** e cobertas por golden tests (`tests/test_formulas.py`):

- **P/L**: `W: stake·odd−stake` · `L: −stake` · `V: 0` · `HW: (stake/2)·odd−stake/2` · `HL: −stake/2` ✅
- **ROI** = Σ(P/L) / Σ(turnover) · 100 (turnover exclui V) ✅
- **Turnover** = Σ(stake onde resultado≠V) ✅
- **Odd média** = Σ(odd·stake)/Σ(stake) ✅ (falta documentar se void entra — #28)
- **Win Rate** = #(W ou HW) / #(resultado≠V) — ⚠️ **HW conta cheio** (#27, decisão pendente)
- **Drawdown real**: curva acumulada por dia; `BASE_BANK=100000` hardcoded (parametrizar por dono — ADR-001 decisão 3)
- **Monte Carlo / p-value / Solidez**: heurísticas úteis, **não** estatística rigorosa. Precisam rename + disclaimer (#29–31)

O único caminho onde erro de dado corrompia dinheiro exibido (odd ilegível em W virando `−stake`) foi
**fechado** (T1.1 / #26).

---

## 4. O que foi feito DESDE o relatório de 03/07 (não estava documentado lá)

As 5 "perguntas em aberto" do relatório antigo, respondidas pelo código de hoje:

1. **Decimal/NUMERIC** → segue **adiado** (ADR-001 escrito, nada executado).
2. **`/salvar` warning vs hard-reject** → **hard-reject por linha implementado** (`validar_linhas`). Foi além.
3. **Rename métricas quant + disclaimer** → **parcial**: o disclaimer JÁ está nos tooltips (_"Indicador heurístico… não é prova estatística nem recomendação"_). Falta só o Feca decidir se renomeia o rótulo-título "p-value".
4. **CDN vendorizar vs SRI** → **vendorização FEITA**. CSP `script-src` caiu para `'self'`. (Google Fonts #36 ainda externo.)
5. **CSRF/Origin check** → **implementado** (`_csrf_origin_guard`).

---

## 5. Top 10 riscos AINDA abertos (por severidade real, não nominal)

| # | Risco | Recomendação |
|---|---|---|
| 1 | **#32** Polymarket mistura entry/realized odd | Persistir `entry_odd`/`realized_odd`/`avg_price` separados |
| 2 | **#44** Observabilidade zero | request_id + log estruturado nas rotas de escrita/extração |
| 3 | **#13/#25** dinheiro em TEXT/float | Executar ADR-001 Fases 1–2 (colunas + backfill auditado) na próxima janela |
| 4 | **#6** `SESSION_SECRET` efêmero em prod | Fail-closed no startup quando `ENV=production` |
| 5 | **#4** XFF spoofável no rate-limit de login | Confiar só no hop do proxy Railway / IP do socket |
| 6 | **#17** dashboard baixa a base inteira | Medir pós-gzip; se doer, ADR-002 opção B (colunar) |
| 7 | **#29/#30/#31** métricas quant — rótulo-título "p-value" ainda técnico | Disclaimer já existe no tooltip; falta só decidir renomear o rótulo (decisão de marca) |
| 8 | **#9** backups/artefatos no pacote de release | Garantir `.dockerignore`/`.gitignore` cobrindo `Backups/`, `__pycache__/` |
| 9 | **#27** win rate infla HW como vitória cheia | Decidir regra oficial (HW=0,5) ou exibir bruto+ajustado |
| 10 | **#36** Google Fonts externo | Self-host das fontes (fecha o CSP e remove dependência) |

---

## 6. Estado dos ADRs

- **ADR-001 (NUMERIC/Decimal/DATE)** — parou na **Fase 0 (não iniciado)**. Gate 1 ("`/salvar` rejeitando
  malformado") já cumprido; falta escolher mecanismo (Alembic vs SQL one-shot) + Fases 1–5 + golden tests
  do caminho Decimal + janela com o Feca. **Nada de execução feito.**
- **ADR-002 (primeira carga do dashboard)** — **Fase 1 (gzip) concluída** (`main.py:1580`). **Fase 2 adiada**:
  só começar depois de medição real pós-gzip mostrar que a 1ª carga ainda incomoda + decisão do Feca (B→C→D).

Ambos são **decisões conscientes com gate**, não trabalho abandonado.

---

VERSÃO: 2026 · consolidado em 2026-07-10 (sessão de auditoria única) · substitui os 3 docs antigos citados no topo
