# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-06-15 (sessão 22 — fix prioridade rótulo "Perdida" vs RO)_

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
/global/                 (autoridade única)
    MASTER_PIPELINE_2026.md
    MASTER_ESPORTES_2026.md
    MASTER_APOSTAS_2026.md
    MASTER_DESCRICAO_2026.md
    MASTER_RESULTADO_2026.md
    MASTER_OUTPUT_2026.md
/casas/
    CASA_MODELO.md             (v2 — 15 seções; consolida Superbet+Pinnacle+Bet365+Betfair+Betano)
    CASA_SUPERBET.md           (pronto — dropar aqui)
    CASA_BET365.md             (quase completo — pendências: §6 rótulo boost, §7 rótulo cashout)
    CASA_BETANO.md             (quase completo — pendências: §5 rótulo void/anulada, §6 boost — aguardam amostra)
    CASA_BETFAIR.md            (quase completo — join bilhete+extrato; bônus incluído; H2H confirmado p/ 180's Dardos)
    CASA_PINNACLE.md           (pronto — dual mode export+print; pendência §5 HW/HL)
/golden_set/
    bilhetes/                  (print + TSV esperado)
STATUS.md                      (este arquivo)
```

Os 6 MASTER_*.md estão em `/global/` (reorganização concluída em 12/06/2026).

---

## 4. Estado atual

- 6 masters globais existem e foram auditados. Separação por coluna de saída está boa; **não** subdividir mais (exceto candidatos opcionais: listas de jogadores fora do ESPORTES; math de sistemas fora do RESULTADO).
- `CASA_SUPERBET.md` formalizado e preenchido com 8 bilhetes reais (mapa de mercados, status, localizadores, 4 golden). Pendências internas: HW/HL (§5) e cashout parcial real (§7).
- Migração TSV: **aplicada** em 12/06/2026 — `MASTER_OUTPUT_2026.md` atualizado (separador TAB, título interno corrigido, seções 3, 3.1, 16, 18 e todos os exemplos reescritos).
- Reorganização do repo: **aplicada** em 12/06/2026 — `/global/`, `/casas/`, `/golden_set/bilhetes/` criados; masters movidos; `CASA_SUPERBET.md` em `/casas/`. Backup em `Planilhador/Backups/Planilhador_pre_reorg_2026-06-12`.
- Remoção de liga como Esporte: **aplicada** em 12/06/2026 — `MASTER_ESPORTES_2026.md` atualizado: seção "Prioridade por Liga" removida; NBA/WNBA viram sinônimos de Basquete; NFL → Futebol Americano; NHL → Hóquei; seção de validação corrigida. Somente 1 arquivo alterado (APOSTAS e CASA_SUPERBET sem toque). Backup em `Planilhador/Backups/esportes_pre_liga-esporte_2026-06-12`.
- `CASA_BET365.md` adicionada em 12/06/2026 — modo visão; 8 golden (W/L/V/HW/HL/Múltipla/Sistema/E-Sports); pendências: §6 rótulo boost, §7 rótulo cashout (aguardam bilhete real). `CASA_MODELO.md` em v1 aguardando passe de revisão. Backup em `Planilhador/Backups/STATUS_pre_bet365_2026-06-12.md`.
- `CASA_BETFAIR.md` adicionada em 12/06/2026 — ingestão por join bilhete+extrato CSV; 4 golden (W/W/V/L); bônus incluído no fluxo; H2H confirmado p/ 180's Dardos; colisão de código V/N documentada. Backup em `Planilhador/Backups/STATUS_pre_betfair_2026-06-12.md`.
- `CASA_BETANO.md` adicionada em 12/06/2026 — ingestão por texto (resolvidas) + screenshot (abertas); 5 golden (W/W/W/V/L); múltipla sem odd combinada → produto das seleções; data = colocação como proxy. Pendências: §5 void, §6 boost. Backup em `Planilhador/Backups/STATUS_pre_betano_2026-06-12.md`.
- Uniformização de estrutura em 13/06/2026: `CASA_SUPERBET.md` §2 renomeado para "Modo de ingestão e layout"; `CASA_BETFAIR.md` reestruturada para 15 seções (§6 Boost + promoção adicionada, §8 Bônus separada, §9–§15 renumerados). Backups em `Planilhador/Backups/*_2026-06-13.md`.
- §8 Bônus adicionada em 13/06/2026 a `CASA_SUPERBET.md`, `CASA_PINNACLE.md`, `CASA_BET365.md`, `CASA_BETANO.md` (via script Python). Todas as 5 casas + `CASA_MODELO.md` agora têm exatamente 15 seções com estrutura idêntica (§1 Identidade … §8 Bônus … §15 Exemplos golden). `CASA_BETFAIR.md` já tinha §8 Bônus preenchida (política decidida: incluir com stake do bônus).
- Regras globais aplicadas em 13/06/2026 (sessão 6):
  - `MASTER_OUTPUT_2026.md` §4: data de múltipla = perna mais recente. Backup: `MASTER_OUTPUT_pre_data_multipla_2026-06-13.md`.
  - `MASTER_RESULTADO_2026.md` §5.2.1, §5.6, §9: odd calculada por divisão preserva precisão total (sem arredondamento/truncamento). Backup: `MASTER_RESULTADO_pre_precisao_odd_2026-06-13.md`.
  - `MASTER_APOSTAS_2026.md`: 4 mudanças em sequência — (1) `Dupla Chance` criada (§3, §4, §5, §6 Futebol); (2) `Impedimentos` criada (§3, §4, §5, §6 Futebol); (3) `Chutes no Gol` criada, SOT removido de `Chutes` (§3, §4, §5, §6 Futebol); (4) princípio geral adicionado ao §1: categoria = objeto apostado, não tipo de mercado (com exemplos de handicap/total/ML sobre Cartões, Escanteios, Chutes, Impedimentos); tabela de desambiguação dos 6 mercados estatísticos de Futebol adicionada ao §5. Backups: `MASTER_APOSTAS_pre_dupla_chance_2026-06-13.md` e `MASTER_APOSTAS_pre_chutes_no_gol_2026-06-13.md`.

- `MASTER_DESCRICAO_2026.md` atualizado em 13/06/2026 (sessão 7): §12.9 Dupla Chance adicionado — formato `1X / X2 / 12 [Confronto]`. Backup em `Planilhador/Backups/pre_descricao_dupla_chance_2026-06-13/`.
- `MASTER_APOSTAS_2026.md` corrigido em 13/06/2026 (sessão 7): §6 E-Sports `Player Props` → `E-Sports Props`; §7 prioridade semântica atualizada; §9 validação itens 7, 12, 13, 14 adicionados (E-Sports Props, Dupla Chance, Impedimentos, Chutes no Gol). Backup em `Planilhador/Backups/pre_esports_props_2026-06-13/`.
- `CLAUDE.md` criado em 13/06/2026 (sessão 7) com regra de propagação obrigatória: toda criação/renomeação/remoção de categoria em MASTER_APOSTAS deve atualizar §3, §4, §9 do MASTER + §9 de todas as casas + templates de MASTER_DESCRICAO. Checklist incluído.
- Mapas de mercado corrigidos em 13/06/2026 (sessão 7): `CASA_SUPERBET §9` (Chutes no Gol separado de Finalizações; Impedimentos e Dupla Chance saíram de Outras); `CASA_BETANO §9` (Chance Dupla / X2 saiu de Outras → Dupla Chance). Backup em `Planilhador/Backups/pre_mapas_categorias_2026-06-13/`.
- Regra de cashout corrigida em 13/06/2026 (sessão 7 — auditoria): cashout ≠ stake → `W`, Odd = Cashout ÷ Stake (antes era `L`). Compatibilidade com planilha: W → stake × odd = cashout ✓. Arquivos alterados: `MASTER_RESULTADO_2026.md` (§2, §5.6, §9), `CASA_BET365.md` (§7), `CASA_BETFAIR.md` (§7), `CASA_BETANO.md` (§7, §11). Backup em `Planilhador/Backups/pre_cashout_W_2026-06-13/`.
- Melhoria de identificação Dardos/Tênis/Vôlei em 13/06/2026 (sessão 8): `MASTER_ESPORTES_2026.md` — listas de jogadores ampliadas (Dardos: 34 jogadores; Tênis: 30 ATP + 21 WTA); torneios PDC adicionados como contextos auxiliares; "Best of X Legs"/"First to X Legs" como sinal de prioridade máxima de Dardos; sinônimos de Vôlei expandidos (VNL, CEV, FIVB, Superliga); seção Vôlei adicionada a §6 Mercados Especializados; "Regra Crítica — Vôlei vs Futebol" criada; "Regra de Desambiguação — Sets (Vôlei vs Tênis)" criada (Sets+time→Vôlei; Sets+jogador→Tênis); §8 Validação itens 9, 10, 11 adicionados. `MASTER_APOSTAS_2026.md` — §6 Vôlei criado; §7 prioridade atualizada; §9 validação itens 15, 16 adicionados. `CASA_BETANO.md` §13 — nota desatualizada de Dupla Chance corrigida. Backup em `Planilhador/Backups/pre_dardos_tenis_volei_2026-06-13/`.

- `PLANO_CONSTRUCAO.md` criado em 13/06/2026 (sessão 9): documento de visão completo do sistema Scanner de Bets — 8 fases, stack, modelo de dados, decisões registradas e detalhamento técnico da Fase 1. Backup em `Planilhador/Backups/STATUS_pre_plano_construcao_2026-06-13.md`.
- **Fase 1 construída em 14/06/2026 (sessão 10):** `app/` criado com 5 arquivos:
  - `config.py` — MODEL_ID (`claude-haiku-4-5-20251001`), ALLOWED_MODELS (Haiku/Sonnet/Opus), GLOBAL_MASTERS, caminhos GLOBAL_DIR e CASAS_DIR.
  - `prompts.py` — monta 7 blocos de sistema com 2 breakpoints de cache (bloco 6 = último master global; bloco 7 = arquivo da casa).
  - `main.py` — FastAPI com 3 rotas: `GET /` (UI), `GET /casas` (lista dinâmica), `POST /extrair` (extração). Aceita imagens (base64) + texto + parceiro + modelo opcional. Retorna TSV + confiança + usage de tokens.
  - `requirements.txt` — fastapi, uvicorn[standard], anthropic, python-multipart.
  - `static/index.html` — UI de teste com sidebar Casa > Parceiro, seletor de modelo (dropdown), upload drag-and-drop, preview de imagens, botão "Copiar TSV" e barra de tokens com % de cache.
  - `.gitignore` criado na raiz do Planilhador — exclui Backups/, .env, __pycache__, .venv.
  - Git inicializado e projeto enviado para GitHub (repo privado `fdc-capital-planilhador`).
  - Backup: `Planilhador/Backups/STATUS_pre_fase1_2026-06-14.md`.
- **Fase 2 construída em 14/06/2026 (sessão 11):** PostgreSQL no Railway + camada de persistência:
  - `app/database.py` — pool asyncpg, schema SQL (`bilhetes` com estados duplos), `init_db()` no lifespan do FastAPI.
  - `app/repository.py` — `parse_tsv()`, `upsert_bilhetes()` (dedup por assinatura SHA-256), `list_bilhetes()`, `marcar_copiada()`.
  - `app/main.py` — 3 novas rotas: `POST /salvar`, `GET /bilhetes`, `POST /bilhetes/copiar`.
  - `app/requirements.txt` — adicionado `asyncpg>=0.30.0`.
  - `Dockerfile` + `railway.toml` corrigidos para build e startup corretos.
  - URL pública: `https://extrator-production.up.railway.app/`
  - Todos os 4 endpoints testados e validados em produção.

- **Fase 3 construída em 14/06/2026 (sessão 12):** interface completa com grade de bilhetes e padronização visual FDC Capital.
  - `app/static/index.html` — aba [Extrair | Exportar]; grade com 10 colunas + checkbox de cópia (pendente/copiada); badges W/L/V/HW/HL; botões Copiar pendentes / Baixar .tsv / Marcar todas / Desmarcar todas; botão Salvar na Grade no extrator; badge de count no tab.
  - `app/repository.py` — `marcar_pendente()`, parâmetro `order` em `list_bilhetes()`.
  - `app/main.py` — `POST /bilhetes/desmarcar`; `GET /bilhetes` aceita `order=asc|desc`, `copy_state` padrão `None` (retorna tudo).
  - `app/static/tokens.css` — cópia de `pack/tokens/tokens.css`; `--grid` dark/light adicionado.
  - `app/static/favicon.svg/.png` — favicon FDC Capital do pack.
  - `app/static/fdc-logo-horizontal-dark.svg` — logo horizontal do pack.
  - Padronização visual: `body::before` grid quadriculado 44×44px; wrapper `.app` z-index 1; logo FDC Capital na sidebar; chips de casa com favicon via Google API (`dominio.bet.br`); `btn-primary` hover com `var(--glow)`; badges com tokens `--d-*-soft`; letter-spacing títulos `-0.035em`.

- **Redesign parceiro-cêntrico em 14/06/2026 (sessão 13):** sidebar e app reescritos para modelo parceiro-cêntrico.
  - `app/database.py` — tabela `parceiros (id, casa, nome, arquivado, criado_em)` adicionada ao schema.
  - `app/repository.py` — 4 funções: `criar_parceiro`, `list_parceiros`, `arquivar_parceiro`, `reativar_parceiro`.
  - `app/main.py` — 4 rotas: `GET /parceiros`, `POST /parceiros`, `POST /parceiros/{id}/arquivar`, `POST /parceiros/{id}/reativar`.
  - `app/static/index.html` — redesign completo: sidebar com casas colapsáveis + lista de parceiros persistida por casa + botão "+ Novo parceiro" + botão arquivar no hover; área principal com empty state → mini-página do parceiro com tabs Extrair/Exportar internas e filtradas; clipboard paste (Ctrl+V) para imagens; botão "+ Arquivo" explícito.
  - Backup em `Planilhador/Backups/pre_parceiro_centric_2026-06-14/`.

- **Layout two-column + grade editável em 14/06/2026 (sessão 13):**
  - Layout sem tabs: esquerda = inputs + grade sempre visível; direita = painel Análise IA.
  - Painel direito com 3 seções: Confiança, Notas Críticas, Recomendações (TSV removido do painel).
  - Grade preenchida automaticamente após extração (auto-save + reload).
  - Células da grade editáveis via `contenteditable` (exceto Casa e Parceiro); save automático ao sair da célula via `PATCH /bilhetes/{id}`; Enter confirma edição.
  - Resultado colorido inline (W/L/V/HW/HL) sem badge; atualiza `extraction_state` no banco.
  - `_INSTRUCAO` atualizada: Claude retorna 4 seções com `##` headers (TSV + Confiança + Notas Críticas + Recomendações).
  - `CLAUDE.md` invariante 8 adicionada: commit e push sempre juntos.
  - Backups em `Planilhador/Backups/pre_layout_twocol_2026-06-14_*` e `pre_editable_grade_2026-06-14_*`.

- **Sessão 14 (14/06/2026) — Fix grade vazia + deletar + resizer + odd:**
  - **Fix crítico (root cause):** `/salvar` agora recebe `casa` e `parceiro` do app e sobrescreve os valores do TSV antes de salvar. A IA deixava `parceiro` vazio e escrevia `"Superbet"` (não `"SUPERBET"`), causando mismatch no filtro `WHERE casa=SUPERBET AND parceiro=...` → grade sempre 0 resultados.
  - `upsert_bilhetes` alterado para retornar `list[int]` (IDs via `RETURNING id`). `/salvar` retorna `{"salvos": N, "ids": [...]}`.
  - `DELETE /bilhetes` (lote) e `DELETE /bilhetes/{id}` (individual) adicionados. `deletar_bilhetes()` em `repository.py`.
  - Grade: botão `✕` por linha; checkbox de seleção múltipla com "selecionar todos"; "Deletar Selecionados" (aparece dinamicamente); "Desfazer Análise" (apaga apenas os bilhetes da última extração).
  - Botão renomeado: "Extrair TSV" → "Processar Bilhetes".
  - Divisor redimensionável entre painel esquerdo e painel IA (arraste, mín 220px / máx 700px).
  - `_INSTRUCAO` em `main.py`: regra inviolável de precisão de odd (até 12 casas decimais, sem arredondamento).
  - Backup em `Planilhador/Backups/sessao14-grade-fix/`.
  - **Odd com boost (root fix):** `_INSTRUCAO` reescrita com regra em 2 passos — (1) W + PRÊMIO visível → PRÊMIO ÷ Stake sempre, ODDS TOTAIS ignorada; (2) precisão exata sem arredondamento. Exemplo concreto na instrução: SUPERMÚLTIPLA 5%, PRÊMIO 1.706,41, Stake 150 → 11,37606666666667 (não 10,88).
  - `CASA_SUPERBET.md §15`: golden #5 (bilhete 890T-QKIRVD) adicionado com odd correta para caso SUPERMÚLTIPLA.
  - `MASTER_RESULTADO_2026 §6`: reescrito com linguagem direta: "casa exibe odd SEM boost; retorno JÁ INCLUI boost; Odd = Retorno ÷ Stake". Exemplo prático incluído.
  - Backup em `Planilhador/Backups/sessao14-odd-instrucao/`.
  - **Data de referência de captura:** campo "Captura" (date input, default = hoje) adicionado na área de ações do extrator. Data enviada como `data_referencia` (DD/MM/AAAA) para `/extrair`. `_INSTRUCAO` resolve Hoje/Ontem/Amanhã contra esse valor, nunca contra horário de processamento. `MASTER_OUTPUT_2026 §4.1` documenta como regra global (vale para todas as casas). Fallback = data atual do servidor.
  - Backup em `Planilhador/Backups/sessao14-data-ref-boost/`.

- **Sessão 22 — Regra de substituição de jogador em Player Props (15/06/2026):**
  - **Bug:** quando um jogador era substituído, o sistema extraía o nome do substituto (em destaque no bilhete) em vez do jogador original (riscado/tachado). A aposta foi feita no original — ele deve aparecer na Descrição.
  - **Causa raiz:** `SUBSTITUIÇÃO+` estava classificado como ruído (correto para o badge) mas sem instrução sobre qual nome usar quando há substituição. O modelo escolhia o mais visualmente proeminente = substituto.
  - **Fix: `MASTER_DESCRICAO_2026 §12.3`** — nota de substituição adicionada globalmente: "nome tachado = jogador original (usar); nome em destaque acima = substituto (ignorar)". Exemplo concreto: Benjamin Nygren vs Lucas Bergvall.
  - **Fix: `CASA_BET365 §12`** — badge `SUBSTITUIÇÃO+` diferenciado: badge = ruído, mas quando presente o nome tachado = original (usar), o nome acima = substituto (ignorar).
  - **Fix: `CASA_SUPERBET §12`** — nota de substituição adicionada.
  - **Fix: `CASA_BETANO §12`** — nota de substituição adicionada.
  - **Fix: `CASA_BETFAIR §12`** — aclaração: "Substituição Segura" = produto de seguro (ruído); substituição de jogador durante jogo com nome tachado → regra global.
  - Backup em `Planilhador/Backups/substituicao-player-props-2026-06-15/`.

- **Sessão 22 — Fix prioridade rótulo "Perdida" vs RO / OCR (15/06/2026):**
  - **Bug:** bilhete "Criar Aposta" com rótulo `Perdida` e `Retorno Obtido R$0,00` foi extraído como W, Odd=0,50 (cashout).
  - **Causa raiz:** o prompt de `main.py` instruía "W com retorno visível → Odd = Retorno ÷ Stake" sem verificar o rótulo primeiro. A IA inferia W a partir do RO (RO>0 → W). Quando OCR leu "R$0,00" como "R$50" (símbolo `$` confundido com dígito `5`), nenhum filtro bloqueou: RO=50 → W → Odd=0,50.
  - **Fix 1: `app/main.py`** — adicionado bloco `RESULTADO — LEITURA OBRIGATÓRIA ANTES DA ODD` antes das regras de odd: instrui a IA a ler o rótulo do bilhete ANTES de qualquer campo financeiro. "Perdida" → L, encerrar sem calcular RO÷Stake. Alerta OCR explícito: "R$0,00 pode ser lido como R50 ($ confundido com 5)".
  - **Fix 2: `casas/CASA_BET365.md §5`** — tabela de resultados clarificada: linha ambígua `Perdida / R$0,00 → L` separada em duas linhas (OR explícito). Nota de prioridade absoluta adicionada: rótulo "Perdida" prevalece mesmo se OCR retornar RO>0.
  - Backup em `Planilhador/Backups/sessao22-fix-rotulo-perdida/`.

- **Sessão 21 — Fix completo: segunda extração + alucinação de casa (15/06/2026):**
  - **Root cause confirmado:** Railway proxy timeout (~60s) matava `/extrair` com 502. System prompt da Bet365 cresceu para ~26K tokens; com Sonnet 4.6 + 9 imagens a chamada levava 90-120s.
  - **Fix crítico: SSE streaming** — `/extrair` agora usa `_client.messages.stream()` + `StreamingResponse(media_type="text/event-stream")`. Chunks chegam ao browser em tempo real; Railway nunca fica idle; timeout eliminado.
  - **`max_tokens`: 8192 → 16000** — evita truncamento do TSV em extrações grandes.
  - **Fix: âncora de casa na instrução** — `_INSTRUCAO` agora recebe `{casa}` e injeta em Notas Críticas e Recomendações. Removidas referências a "Superbet" da instrução genérica (causavam alucinação ao extrair Bet365).
  - **Fix: `Cache-Control: no-cache`** no endpoint `/` — impede browser de servir `index.html` stale após deploy.
  - **Fix: `/salvar` com check `!rs.ok`** — erros de banco aparecem em vermelho em vez de "0 bilhetes" silencioso.
  - **Fix: timer `Processando… (Xs · N chars)`** durante spinner — usuário vê progresso real.
  - **Resultado:** extração Dia 14 (9 imagens Bet365, 46 bets) concluída com sucesso. Grade acumulou 73 bets (29 Dia 13 + 44 Dia 14).
  - Backups: `fix-async-client-*`, `pre-streaming-sse-main.py`, `pre-fix-instrucao-casa-*`.

- **Sessão 20 — Fix AsyncAnthropic: segunda extração travava (15/06/2026):**
  - **Root cause:** `Anthropic()` (sync) bloqueava o event loop durante chamadas de 60–180s → conexões asyncpg morriam → DB operation falhava silenciosamente.
  - **Fix crítico: `AsyncAnthropic()` em `main.py`** — chamada de IA é agora não-bloqueante.
  - **Fix pool: `max_inactive_connection_lifetime=60`** em `database.py` — recicla conexões idle antes do Railway PostgreSQL fechá-las.
  - **Fix frontend:** `if (!rs.ok) throw Error` após `/salvar` — erros de banco aparecem como `✗ ...` em vez de silencioso "0 bilhetes".
  - **Fix frontend:** TSV vazio mostra aviso amarelo explícito ("nenhum bilhete extraído").
  - **Fix frontend:** timer de progresso `Processando… (Xs)` durante spinner.
  - Backup: `fix-async-client-2026-06-15-{main,database,index}.py/html`.

- **Sessão 19 — Análise Bet365 + fix DEFAULT_MODEL (15/06/2026):**
  - Análise comparativa Haiku vs Sonnet em 29 bilhetes reais da Bet365: Haiku falhou em categorias, descrições e odds; Sonnet acertou 28/29.
  - **Fix crítico: DEFAULT_MODEL = Haiku → Sonnet 4.6** (`app/config.py`). Aplica a todas as casas (Superbet, Bet365, etc.).
  - **CASA_BET365 §9**: adicionadas entradas faltantes: `"Partida - Vencedor" → ML` e `"Para Sofrer Falta / props individuais de Futebol" → Player Props`.
  - **CASA_BET365 §2**: dica visual de jersey icon documentada — ícone de camisa = esporte de equipe; sem ícone = esporte individual. Corrige caso Lavenirosso NC (erroneamente classificado como Tênis).
  - Backup: `config_pre_sonnet_default_2026-06-15.py` e `CASA_BET365_pre_mapa_icone_2026-06-15.md`.

- **Sessão 18 — Crise Superbet + Tiros de Meta (15/06/2026):**
  - **Fix crítico: colunas invertidas.** Root cause: `_INSTRUCAO` tinha "Stake: campo APOSTA do bilhete" — a Superbet chama o valor apostado de "APOSTA" (mesmo nome da coluna TSV "Aposta" = categoria), gerando inversão Aposta↔Descrição e Stake↔Odd em todos os bilhetes. Fix: numeração explícita `(col 6/7/8/9)` + bloco "COLUNAS — NUNCA INVERTER". Confirmado resolvido.
  - **Capacidade de modelo:** Haiku 4.5 perde bilhetes e mistura descrições com 15 imagens Superbet complexas (11/15). Recomendado Sonnet 4.6 → 15/15 extraídos. Configurar Sonnet 4.6 como padrão para uploads volumosos.
  - **Fix semântico: Tiros de Meta → Team Props.** "Tiro de Meta" = goal kick (reinício pelo goleiro), completamente diferente de "Chutes no Gol" (SOT). A AI mapeava erroneamente para Chutes no Gol. Corrigido em 3 arquivos: `MASTER_APOSTAS §4` (sinônimos Team Props), `MASTER_APOSTAS §6` (subseção Futebol com distinção explícita), `CASA_SUPERBET §9` (mapa de mercados). Commit `bfd3da7`.

- **Sessão 17 — Auditoria completa (14–15/06/2026):**
  - **Parte 1 (14/06):** Bug múltiplas fragmentadas — `_INSTRUCAO` adicionou regra MÚLTIPLA; `MASTER_PIPELINE §3.1` corrigido; `CASA_SUPERBET §9` + goldens #6/#7 adicionados.
  - **Parte 2 (15/06):** 3 bugs adicionais identificados e corrigidos:
    - Bug 1 (leitura incompleta): `_INSTRUCAO` reescrita — "leia a imagem inteiramente incluindo campos abaixo do ID (ODDS TOTAIS, APOSTA, STATUS)"; "L → ODDS TOTAIS lida diretamente, nunca calculada"; "TODAS as N seleções na Descrição".
    - Bug 2 (imagens puladas): `_INSTRUCAO` — "para cada imagem extraia TODOS os bilhetes; não pule nenhuma imagem". `max_tokens` 4096 → 8192.
    - Bug 3 (ordenação universal incorreta): `MASTER_OUTPUT §15` — regra universal removida, redirecionada para §2 de cada casa. Regras adicionadas individualmente: `CASA_SUPERBET §2` (manter ordem), `CASA_BET365 §2` (última aposta da última imagem = 1ª linha), `CASA_BETANO §2` (fim do texto = 1ª linha), `CASA_BETFAIR §2` (fim do texto = 1ª linha), `CASA_PINNACLE §2` (aposta #1 = mais nova = última linha).
  - Backups em `sessao17-fix-multiplas-2026-06-14/` e `sessao17-auditoria-completa-2026-06-15/`.

- **Sessão 16 (14/06/2026) — UX upload de imagens + deduplicacao por ID:**
  - Fix: X vermelho do thumbnail abria file browser (event bubbling). Substituido pseudo-elemento ::after por `<button class="thumb-del">` real com `stopPropagation`.
  - Feat: botao "Limpar imagens" aparece com 2+ imagens; remove so imagens sem apagar texto/status.
  - Feat: lightbox — clique na imagem abre overlay em tela cheia (ate 90% da tela); fecha com clique no overlay ou Esc.
  - Fix: div `#img-lightbox` estava apos o `</script>`, causando `TypeError: Cannot read properties of null`. Movida para antes do bloco script.
  - Feat: contador de imagens na barra de acoes (`X imagem(ns)`); some ao limpar.
  - Fix critico: deduplicacao agora usa ID/codigo do bilhete como chave primaria quando disponivel. A IA extrai o ID como 11a coluna interna no TSV (nao vai para a planilha do usuario). IDs diferentes = INSERT separado mesmo com conteudo identico. Sem ID no lote = alerta amarelo de possivel sobreposicao de prints.
  - Fix: `odd` incluida no hash de assinatura — bilhetes com mesmos jogos mas odds diferentes nao sao mais colapsados.
  - Fix: coluna `codigo_bilhete TEXT` adicionada ao banco com migracao idempotente (`ADD COLUMN IF NOT EXISTS`).
  - Fix: nome de casa normalizado para display name (`Superbet`, nao `SUPERBET`). Migracao SQL atualiza registros existentes em `bilhetes` e `parceiros` no proximo boot.
  - `CLAUDE.md` atualizado com 11a coluna interna e tabela de regras de deduplicacao.
  - Backups em `Planilhador/Backups/fix-upload-bubbling-limpar-imgs/`, `fix-dedup-odd-lightbox/`, `feat-codigo-bilhete-dedup/`, `fix-casa-display-name/`.

- **Sessão 15 (14/06/2026) — Auditoria aliases e travamento de odd:**
  - Auditoria completa em todos os `casas/CASA_*.md` e `global/MASTER_*.md` para dois tipos de ruido: grafia de casas e travamento de odd.
  - `CASA_BET365.md §1`: linha `Aliases` removida + `Odds: 2-3 casas` removido do locale.
  - `CASA_BETANO.md §1`: linha `Aliases` removida.
  - `CASA_SUPERBET.md §1`: linha `Aliases` removida (incluindo variante `SuperBet`).
  - `CASA_SUPERBET.md §11`: corrigido travamento "2 casas para odd do bilhete" — padrao agora e ate 12 casas decimais em qualquer fonte (calculada ou lida do bilhete).
  - `CASA_PINNACLE.md §1`: linha `Aliases` removida.
  - `CASA_PINNACLE.md §11`: "Preservar as 3 casas" corrigido para "preservar a precisao original do export — nao truncar nem preencher zeros".
  - `CASA_PINNACLE.md §13`: "Odd: 3 casas, ponto" corrigido para "ponto → virgula, preservar precisao original".
  - `MASTER_OUTPUT_2026.md §7`: nota da convencao de duas camadas adicionada (IA escreve `Superbet`; banco armazena `SUPERBET` via normalizacao do backend; IA nunca identifica a casa).
  - Backup em `Planilhador/Backups/auditoria-aliases-odds-2026-06-14/`.

---

## 5. Pendências (ordem)

1. ~~**Organizar repo**~~ — concluído em 12/06/2026.
2. ~~**Propostas de regra global**~~ — todas concluídas em 13/06/2026.
3. ~~**CASA_MODELO.md**~~ — **entregue em v2** (12/06/2026): 15 seções, consolida aprendizados das 5 casas. Novidades: §2 ingestão multi-modo + tipo declarado, §3 ID 3 casos, §4 cadeia de data completa, §5 disciplina de tradução + gatilho HW/HL, §8 Bônus (nova), §9 normalização de jogador, §10 alerta en-US, §11 campo financeiro único + sistemas.
4. **Outras casas:** ~~Bet365~~ · ~~Betfair~~ · ~~Betano~~ — todas adicionadas. Pendências de amostra (aguardam bilhete real):
   - Bet365: §6 rótulo boost, §7 rótulo cashout visual.
   - Betano: §5 rótulo void/anulada, §6 boost.
   - Pinnacle: §5 HW/HL — rótulo exato no export (precisa de bilhete com Asian Handicap de quarto).

---

## 6. Próxima sessão

**App em produção:** `https://extrator-production.up.railway.app/`

Para rodar localmente:
```
cd app
pip install -r requirements.txt
# .env na raiz do Planilhador com ANTHROPIC_API_KEY e DATABASE_URL
uvicorn main:app --reload
# Abrir http://localhost:8000
```

**Estado após sessão 22:** Fix de prioridade de rótulo aplicado (`main.py` + `CASA_BET365.md §5`): IA agora lê o rótulo "Perdida" antes de qualquer campo financeiro e nunca calcula RO÷Stake quando rótulo=Perdida. Regra de substituição de jogador documentada globalmente (MASTER_DESCRICAO) e nas 4 casas afetadas (Bet365, Superbet, Betano, Betfair). App em produção estável.

**Pendências que aguardam bilhete real (amostra do usuário):**
- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)

Quando chegar um bilhete novo: abrir o arquivo da casa correspondente, preencher a pendência, rodar o checklist do `CLAUDE.md` se envolver categoria nova.

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/extrator`). Deploy automático via Railway conectado ao GitHub — push dispara deploy.
