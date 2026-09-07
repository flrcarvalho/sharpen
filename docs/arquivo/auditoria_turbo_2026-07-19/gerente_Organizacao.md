## Organizacao

**Veredito da area:** Precisa atencao — o sistema tecnico esta solido (65/65, no ar) e a higiene de repo e boa, mas a camada de organizacao do backlog derivou ~35 sessoes e virou uma bussola que aponta para o retrato errado.

**Top 3 acoes prioritarias:**
- **Re-sincronizar os 3 docs de consolidacao** (ONDE_ESTOU.md, docs/AUDITORIA_2026.md, Ideias/README.md) contra o STATUS atual (sessao 157) e travar uma cadencia — sem isso todo planejamento e medido contra a sessao 122.
- **Fechar o trio barato de seguranca** numa unica sessao: SESSION_SECRET fail-closed (#6), X-Forwarded-For (#4), criar .dockerignore (#9). Confirmados no codigo, esforco pequeno cada.
- **Executar as duas frentes curtas com plano pronto:** persistir posicoes ativas do Polymarket e a Fase 1 da inteligencia de tipster (depois de rodar o backtest da Fase 0B para ter baseline por carteira).

---

### Achados criticos e altos (detalhados)

**1. Docs de consolidacao defasados ~35 sessoes (medio, confirmado) — `ONDE_ESTOU.md:3`**
Os tres documentos que servem de fonte de verdade do backlog foram escritos na sessao 122 (10-11/07). STATUS.md ja esta na 157 (18-07). Consequencias verificadas abaixo (itens resolvidos listados como abertos, entregas invisiveis, frentes duplicadas). **Acao:** sessao dedicada de reconciliacao (como a madrugada 10-11/07) + cadencia fixa (a cada 10 sessoes ou dentro do ritual `/encerrar`).

**2. Trio barato de seguranca pendente (medio, confirmado) — `app/auth.py:37`**
Confirmado no codigo: (#6) SESSION_SECRET cai para `token_hex(32)` efemero e so avisa — nao e fail-closed em producao; (#4) rate-limit confia em `X-Forwarded-For` spoofavel; (#9) nao existe `.dockerignore`, entao `Backups/` e `__pycache__` entram no contexto de build Docker. Sao os itens 4/5/8 do top-10 da AUDITORIA. **Acao:** fail-closed no startup quando `ENV=production`; confiar so no hop do proxy Railway; `.dockerignore` cobrindo `Backups/ _backups/ __pycache__`. Fazer os tres juntos.

**3. Maior risco quant aberto — Polymarket entry/realized odd (#32)**
Sinalizado pela gerencia como o maior risco quantitativo ainda em aberto. Nao veio detalhado no lote verificado dos especialistas; **acao:** puxar o achado #32 da AUDITORIA para uma sessao propria antes de tocar em qualquer metrica derivada do Polymarket.

---

### Achados medios e baixos (resumidos em tabela)

#### Itens ja resolvidos ainda listados como abertos (corrigir os docs)
| Item | Onde | Estado real | Esforco |
|---|---|---|---|
| Rename metricas quant (#29-31) | `Ideias/README.md:78` | ✅ decidido pelo Feca 11/07 (nomes tecnicos + tooltip) | trivial |
| Win rate HW/HL pela metade (#27) | `ONDE_ESTOU.md:68` + AUDITORIA §3 l.102 | ✅ feito 11/07 (commit 1360bbf) | trivial |
| CASA_BETANO "descreve scraping" | `ONDE_ESTOU.md:60` | Provavelmente ✅ (busca por `scrap` = 0); confirmar §2/§3/§12 | trivial |

#### Entregas invisiveis / frentes duplicadas (dar dono unico)
| Frente | Onde | Acao | Esforco |
|---|---|---|---|
| Fase 0 inteligencia de tipster (origem_tipster) ja no codigo | `Ideias/README.md:43` | Marcar Fase 0 entregue, abrir Fase 1 | pequeno |
| Telegram→tipster duplicada em 4 docs | ONDE_ESTOU §4, Ideias §1.3/§4.1, PLANO_TIPSTER, PLANO_INTELIGENCIA | PLANO_TIPSTER.md = dono canonico; resto vira ponteiro | pequeno |
| Dedup estrutural "Betano capturar ID" pulverizada | `Ideias/README.md:127` | Mini-plano unindo Betano/KingPanda/Bet365 sob "dedup sem codigo confiavel" | pequeno |

#### Frentes abertas com plano pronto (executar quando o Feca quiser)
| Frente | Horizonte | Esforco | Tem plano |
|---|---|---|---|
| Persistir posicoes ativas Polymarket | curto | pequeno/medio | sim, completo |
| Camada de evidencia tipster (Fase 1) — apos backtest Fase 0B | medio | grande | sim, detalhado |
| Rotacao senha Postgres (runbook pronto, arrasta da sessao 82) | curto | trivial | sim |
| Self-host fontes (#36) — fechar CSP | medio | pequeno | parcial |
| Extracao worldwide Fase 1 (confidence + guardrail enum) | medio | medio | sim, gate aberto |
| Inferencia por campo (glifo ambar) — 2 perguntas de produto ao Feca antes de codar | medio | medio | sim, bloqueado por decisao |
| Casca unificada Fatia 3 — reconciliar com o que 153-157 ja fizeram no rodape | curto | pequeno/medio | sim |
| SaaS multiusuario Fase 1 (tabela usuarios) | longo | grande | sim |

#### Dividas conscientes / condicionais (manter adiado com registro)
| Item | Estado | Esforco |
|---|---|---|
| Observabilidade zero (#44) — pre-requisito antes de abrir SaaS self-service | sem plano dedicado | medio |
| ADR-001 dinheiro→NUMERIC/Decimal (#13/#25) — erro <1 centavo, Gate 1 cumprido | adiado por design | grande |
| ADR-002 Fase 2 / PLANO_DASHBOARD_C — gated por medicao; fazer Fase 0 (304) barata antes | condicional | medio/grande |
| Pendencias de casas aguardando bilhete real (STATUS §5) — reativas | backlog reativo | trivial |

#### Higiene de arrumacao (baixa severidade)
| Item | Onde | Acao | Esforco |
|---|---|---|---|
| NOTA_AO_AUDIT.md commitado na raiz | `NOTA_AO_AUDIT.md` | `git rm` apos a auditoria | trivial |
| 2 planos na raiz contra a estrutura /docs declarada | `PLANO_MULTIUSUARIO_2026.md`, `PLANO_UNIFICACAO_2026.md` | Mover para docs/ + atualizar links do hub | pequeno |
| Link markdown quebrado | `docs/HISTORICO.md` | `docs/PLANO_EXTRACAO_WORLDWIDE.md` → `PLANO_EXTRACAO_WORLDWIDE.md` | trivial |
| Plano orfao sem referencia | `docs/PLANO_INFERENCIA_POR_CAMPO.md` | Indexar no Ideias/README ou arquivar com banner | trivial |
| Bytecode orfao (fonte ja removido) | `scripts/__pycache__/import_diogo.cpython-314.pyc` | Apagar local (gitignored, nada muda no git) | trivial |
| Script one-off com caminho pessoal (#10) | `scripts/import_lava.py:23` | Parametrizar via argv/env ou mover para scripts/oneoff/ | trivial |
| Relatorios datados soltos em docs/ sem sinal vivo/historico | `docs/AUDITORIA_CRITICA_2026-07-02.md` e linhagem | Banner "consolidado em AUDITORIA_2026.md" ou docs/arquivo/ | pequeno |
| Backups/ sem politica de retencao (55MB, 370 pastas) | `Backups/` | Retencao (N sessoes/90d); nao copiar HISTORICO (497KB) a cada backup; documentar no CLAUDE.md | pequeno |
| Nomenclatura tripla Sharpen/Planilhador/extrator | repo | Nome canonico Sharpen; registrar equivalencia num ponto (CLAUDE.md) | medio |

---

### Pontos positivos (o que esta bem feito)

- **`.gitignore` correto e efetivo** — `__pycache__`, `*.pyc`, `.env` (com excecao de `.env.example`), `Backups/` cobertos e **verificados**: 0 artefatos indevidos versionados apesar de existirem no disco. E o alicerce que impede o repo de inchar.
- **Consolidacao de auditoria em documento unico e vivo** — tres auditorias antigas fundidas em `docs/AUDITORIA_2026.md` com placar por status. O formato e o padrao certo; o problema e so a frequencia de atualizacao.
- **Janela deslizante STATUS→HISTORICO disciplinada** — STATUS mantem ~5 sessoes recentes + ponteiro para HISTORICO (152→14), com faxina registrada (commit 3798488) e HISTORICO explicando a procedencia. Rehydration enxuto e rastreavel.
- **Hub de ideias com dono-fonte por frente** — `Ideias/README.md` indexa as frentes apontando para o doc-plano canonico, sem duplicar conteudo. Desenho correto de chief-of-staff; falha e so manutencao de datas.
- **Doc desatualizado corretamente sinalizado** — `PLANO_CONSTRUCAO.md` abre com banner "DOCUMENTO HISTORICO / DESATUALIZADO", lista as referencias vencidas e redireciona para a fonte atual. **Isso supera a premissa da missao de que ele engana** — e confirma que CASA_BETANO.md nao tem scraping. E o padrao a replicar nos relatorios datados de docs/.

> **Nota de premissa:** a saude organizacional do repo e fundamentalmente boa. O que resta em "arrumacao" e majoritariamente baixa severidade. O risco real da area nao e o codigo nem a higiene de arquivos — e a **defasagem dos docs de consolidacao**, que faz o backlog divergir da realidade e precisa de cadencia, nao so de um mutirao pontual.