# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-06-29 (sessão 72 — ODD COM 2 CASAS DECIMAIS NO VISUAL (frontend, pedido do Feca). A odd continua armazenada e exportada com precisão total (quantas casas forem necessárias); muda só a **exibição**: na grade aparece com 2 casas decimais por padrão e, quando há mais precisão, o valor completo aparece no hover (tooltip `title="Odd completa: …"` + dica de sublinhado pontilhado `.odd-trunc`). Novo helper `_fmtOddDisplay(v)` em `index.html` (arredonda via `toFixed(2)`, vírgula decimal; só marca hover quando o arredondamento perde precisão). Aplicado nas 2 tabelas com coluna Odd: grade principal (`.btbl-num`) e Posições Ativas Polymarket. **Intocados** (mantêm valor completo): input do modal de edição (`ed-odd` ← `b.odd` direto) e export TSV (`montarTSV` → `_limparOdd`). Backup do original: `Backups/odd-2-casas-decimais/index.html.orig`. Mudança puramente de CSS/JS de exibição — sem backend, sem migração.)_

_Anterior: 2026-06-29 (sessão 71 — MUTIRÃO DE AUDITORIA DOCUMENTAL (global × casas), em paralelo ao outro terminal (sessões 68-70). 3 auditores simultâneos: 6 MASTERs globais; 13 casas; código×doc dos commits do dia. **Veredito da pergunta-mãe (a nova ordem "dashboard"):** NÃO exige mudança de doc — a *exportação* da lista usa `order=asc` (cronológica), batendo com OUTPUT §15/§18 e PIPELINE §2.3/§9.1; o "último acima" mudou só na *visualização*. Correções (cada uma backup + arquivo completo + push):
  • **🟢 ESPORTE da Polymarket (commit `2a3b869`):** causa raiz do "muita aposta em Outro" (tênis/futebol/baseball) — esportes tradicionais são titulados por nome de time/jogador, que o regex de título não pega. O **`eventSlug` é prefixado pela liga** (`mlb-`, `atp-`, `nba-`, `ucl-`, `lol-`…) → novo `_detes_from_slug` lê esse prefixo como sinal primário; título vira fallback. **Validado contra a carteira real (115 posições via worker proxy): Outro 21→0**, todos no esporte certo. (Proxy exige User-Agent de navegador; 403 sem ele.) `CASA_POLYMARKET §13` atualizada.
  • **Preservação de edição manual no re-sync (confirmado, sem mudar código):** a assinatura da Poly é por `conditionId` (não por conteúdo) e o `ON CONFLICT DO UPDATE` NÃO toca `esporte`/`aposta`/`descrição`/`stake`/`odd` → **edição manual de esporte fica preservada**; só `resultado`/`extraction_state`/`stake_usd`(se vazio)/`tipster`(se vazio) são atualizados. O classificador novo só beneficia bilhetes NOVOS; os ~200 corrigidos à mão pelo Feca permanecem.
  • **A1 — `CASA_POLYMARKET §5` (commit `e3866ef`):** pnl≈0 → **V** (banda neutra), não L.
  • **C1 — `CASA_BETANO §9` (commit `f90eb75`):** 180's de Dardos não é Legs → Over/Total individual=Player Props, Maioria/H2H=H2H (MASTER validação 17).
  • **C2+C3 — Betano (`f91d0b7`) + Bet365 (`bcc0630`):** tiros de meta→Team Props (era Outros); handicap de objeto estatístico segue o objeto (Handicap-Cartões→Cartões, Tiros de meta Handicap→Team Props) por APOSTAS §1; handicap de unidade de pontuação (gols/games/sets) continua Handicap. Rótulo do golden #2 da Betano corrigido (era "em cartões", é handicap de resultado).
  • **B1/B2/B3 globais (`82f7884`):** PIPELINE §6.2 nota da exceção Polymarket (casas por API não herdam as listas dos masters); OUTPUT §14 cashout completo (≠stake=W incl. menor; =stake=V); APOSTAS §4 bloco de sinônimos E-Sports Props.
  • **C4/C5 casas (`0453e39`):** removida a frase "cobre todas as 27 categorias" (Jogo de Ouro/KingPanda); Pinnacle §9 documenta a convenção de handicap.
  `audit_casas`: 12/12 OK (rodado 2×). Backups: `Backups/poly-classificador-esporte-slug_2026-06-29/`, `betano-c1-180s_…`, `auditoria-cosmetica-globais_…`, `auditoria-cosmetica-casas_…`, `betano-bet365-c2-c3_…`. **Coordenação 2-terminais:** commits intercalados na mesma tree (lock serializa); não toquei nas entradas de STATUS das sessões 68-70 do outro terminal. **Pendente:** (opcional, sob demanda) backfill de esporte dos ~200 Poly já gravados.)_

_Anterior: 2026-06-29 (sessão 70 — NORMALIZAÇÃO DE TIPSTER (dados, produção). Pedido do Feca: unificar variantes de nome de tipster no banco. Aplicado direto no Postgres (Railway), sem mudança de código. Predicado robusto a acento/espaço/caixa (`translate`+`replace`+`lower`). Resultados: `Só Chutes` (4) consolidado em **`SóChutes`** (total 2485); `Tcinsider` (28) + `TCinsider` (8) consolidados em **`TC Insider`** (total 36). 40 linhas alteradas, dentro de transação. Backup reversível das 2521 linhas afetadas (UTF-8): `Backups/sessao70-normaliza-tipster/tipsters_antes.csv` (id/dono/casa/parceiro/tipster). Nota: o garble "S�Chutes" no log foi só o codepage do terminal Windows — dados no banco estão em UTF-8 corretos. LOTE 2 (varredura geral de variantes, escolha do Feca): `Robotennis` (91) → **`Robotenis`** (total 649); `Insider` (46) → **`TC Insider`** (total 82). `NBA Tom` vs `NBA Tom [BR]` mantidos separados (tipsters distintos, decisão do Feca). 137 linhas, backup `Backups/sessao70-normaliza-tipster/tipsters_antes_lote2.csv`. Banco tem 62 tipsters distintos + 1 sem tipster; resta o suspeito `Ω Teste Encerrado` (170 linhas, parece dado de teste) — não tratado, aguarda decisão.)_

_Anterior: 2026-06-29 (sessão 70 — DARDOS CLASSIFICADO COMO TÊNIS (4 nomes). Dois bilhetes Bet365 do tipster `DartsVader` (Adam Sevada v Alex Spellman; Leonard Gates v Fred Krueger), mercado `ML` puro, saíram como **Tênis** devendo ser **Dardos**. Causa raiz: (a) a IA NÃO vê o tipster — `main.py:274` força "Tipster: SEMPRE VAZIO" (atribuído depois pelo dashboard), então o sinal óbvio `DartsVader→Dardos` não chega à classificação; (b) os 4 nomes são dardistas do circuito americano (CDC) mas não estavam nas listas auxiliares de Dardos → a regra de desempate `MASTER_ESPORTES §571` (atleta não identificado em ML sem sinal de dardos → Tênis) caiu em Tênis, comportamento projetado. Fix (escolha do Feca: só adicionar nomes): adicionados Adam Sevada, Alex Spellman, Leonard Gates, Fred Krueger ao bloco MODUS/circuitos `MASTER_ESPORTES §512`. Limite conhecido: é "whack-a-mole" — o sinal robusto seria o tipster, adiado (recurso maior/arriscado). Os 2 bilhetes já salvos precisam de correção manual na tela (re-extração futura sairá certa). Backup: `Backups/sessao70-dardos-cdc-nomes/`.)_

_Anterior: 2026-06-29 (sessão 69 — HASH DE SENHA FECHADO (fase 2, commit `3f89208`). Feca definiu `SENHA_FECA_HASH`/`SENHA_DIOGO_HASH` (bcrypt) no Railway e confirmou login funcionando. Então: `auth.py` agora lê os hashes SOMENTE das env vars (sem default no código → fail-closed se faltar), os 2 hashes SHA-256 versionados foram REMOVIDOS (vazamento fechado), e `_verifica_hash` virou bcrypt-only (caminho SHA-256 aposentado). `hashlib`/`hmac` seguem só na assinatura do cookie. **Os 2 🔴/🟠 de segredo/senha da auditoria estão FECHADOS.** Após o redeploy deste commit, reconfirmar 1× o login (agora não há fallback). Nota: senha do Diogo (`Cerveja`) é fraca — trocar quando der. Resíduo de segurança restante é só hardening 🟡 (headers HTTP, revogação de sessão) — opcional.)_

_Anterior: 2026-06-29 (sessão 68 — SEGURANÇA: SESSION_SECRET + bcrypt fase 1. (a) **SESSION_SECRET CONFIGURADO** no Railway (env var no serviço `extrator`, deployado pelo Feca) → o 🔴 do segredo do cookie está FECHADO: segredo forte e persistente entre reinícios, sem default hardcoded. (b) **bcrypt fase 1 NO AR** (commit `84cbed8`): `auth.py` aceita hash bcrypt ($2…) OU SHA-256 legado, auto-detectando; `bcrypt` no requirements; import defensivo. Sem lockout — os defaults SHA-256 ainda validam. **PENDENTE (hash de senha, fase 2):** o Feca ainda NÃO definiu `SENHA_FECA_HASH`/`SENHA_DIOGO_HASH` (bcrypt) no Railway, então as senhas continuam SHA-256 (fracas, vazaram no git; mitigado pelo rate limit da sessão 67). Quando o Feca quiser fechar: me passar as 2 senhas novas → gero os hashes bcrypt → ele cola nas env vars + deploy → testar login → AÍ removo os defaults SHA-256 do código (fase 2). Ver bloco "Hash de senha".)_

_Anterior: 2026-06-29 (sessão 67 — AUDITORIA MULTI-AGENTE + CORREÇÕES. Após uma sessão longa com 4 terminais e conflitos de merge, rodei 5 auditores em paralelo (segurança, backend/arquitetura, frontend, Polymarket/IA, consistência de domínio). Veredito: SEM resíduo estrutural (zero marcadores de conflito, sem função/rota duplicada, isolamento por `dono` íntegro, SQL parametrizado, invariante "app só lê masters" intacto, audit_casas sem FAILs). 14 commits de correção aplicados (cada um backup + arquivo completo + push):
  • **🔴 segredo do cookie** (`auth.py`): removido o fallback hardcoded conhecido (permitia forjar cookie). Agora usa `SESSION_SECRET` da env, senão gera aleatório no boot — não derruba o app.
  • **🔴 P/L com odd ponto-decimal** (`repository._num`): confirmado no banco — 5 odds Betano tipo `75.2606` (sem vírgula) viravam 7,5e15 e estouravam o P/L na coluna nova. Regra: sem vírgula → ponto é decimal; com vírgula → ponto é milhar (formato `1.000,00` intacto).
  • **model id inválido** (`config.py`+`index.html`): removido `claude-sonnet-4-5-20251001` (não existe → 404).
  • **CASA_MODELO §7**: cashout ≠ stake = **W** (era L, contradizia o global e propagava via `nova-casa`).
  • **segurança backend** (`main.py`): handlers de erro não vazam mais detalhe interno (5 pontos); limites de upload no servidor (qtd/tamanho/tipo); rate limit no login (10 falhas/5min por IP + atraso).
  • **auto_arquivar**: usa display canônico (casas multi-palavra como "Bolsa de Aposta" não arquivavam).
  • **origem='sync'**: novos syncs Polymarket eram gravados como 'extracao' (default).
  • **resiliência Polymarket** (`polymarket.py`): retry/backoff (proxy+PTAX); sem cotação ABORTA (não grava USD como R$); resposta inesperada falha alto (não trunca histórico); pnl==0 → V.
  • **frontend**: poll de 60s não apaga tipster sendo digitado; `login.html` usa tokens reais; "selecionar todos" ressincroniza ao paginar; export em massa trata erro; `MASTER_APOSTAS §5` esclarece que "Pontos" não é categoria.
  ADIADOS (precisam de você): (1) **hash de senha** → bcrypt/argon2 + RESET das senhas (não dá p/ migrar sozinho sem trancar fora — ver §"hash de senha" abaixo). (2) **SESSION_SECRET no Railway** (definir p/ sessões persistirem entre reinícios). (3) **limpeza de CSS/JS morto** (#13) — base de auditoria ficou desatualizada: o commit "Posições Ativas no layout" reusou as classes `c-*` antes mortas; remoção exige passada fresca. (4) **golden_set/** vazio vs doc — os goldens vivem no §15 das casas; decidir reconciliar doc ou repovoar. (5) **upsert sem transação de lote** — wrapper exigiria savepoints por linha (a recuperação de UniqueViolation por linha quebraria numa tx única); não feito por risco. Backups da sessão: `Backups/sessao63-auditoria-2026-06-29/`.)_

_Anterior: 2026-06-28 (sessão 66 — POSIÇÕES ATIVAS no LAYOUT da lista resolvida (Polymarket). Pedido do Feca: a tabela de Posições Ativas não espelhava a linha das apostas resolvidas (faltavam tipo/esporte/Casa·Parceiro). Decisão (com o Feca): **aumentar** — adotar a linha visual da lista resolvida MANTENDO as colunas vivas. Backend `polymarket.py` `coletar_dashboard`: cada ativa agora carrega `esporte` (`_norm_esporte(_detes_raw(title))`) e `aposta`/categoria (`_categoria`), reusando as MESMAS funções do `coletar_bilhetes`. Frontend `index.html`: tabela `pm-ativas` reordenada para 10 colunas — Data · Aposta/Evento (badge `.btbl-tipo` + `.btbl-desc`) · Esporte (`.sp-chip`+nome) · Tipster (editável) · Casa·Parceiro (`.casa-chip` Polymarket + parceiro de `parceiroSelecionado.nome`) · Stake · Odd · Status (badge ativa) · P&L % · Valor atual. Reusa os componentes da linha resolvida (`.btbl-tipo/.btbl-desc/.btbl-sport/.sp-chip/.btbl-casa`); CSS de larguras por coluna (Aposta/Evento absorve a sobra), linhas mais altas (`td padding 9px`), odd voltou a neutro (era âmbar `.pm-odd`, removida). Backup: `Backups/polymarket-ativas-layout-resolvidas_2026-06-28/`. Backend `py_compile` OK; não rodei o app (sem DATABASE_URL local). Pendente: validação visual no deploy.)_

_Anterior: 2026-06-28 (sessão 65 — STAKE USD ORIGINAL NA GRADE (Polymarket). Pedido do Feca: abaixo do R$ já convertido na coluna Stake da Lista, mostrar o valor original em USD (o que saiu da conta) em fonte menor, p/ referência. O USD era descartado na ingestão (só o BRL ia ao banco). Mudanças: (1) `database.py` — coluna `stake_usd REAL` (migração `ADD COLUMN IF NOT EXISTS`; NULL para casas em R$ nativo); (2) `polymarket.py` `coletar_bilhetes` — grava `stake_usd` (= `initialValue`, valor que saiu da conta); (3) `repository.py` `upsert_bilhetes` — INSERT $16 + `ON CONFLICT DO UPDATE` com `COALESCE(EXCLUDED.stake_usd, bilhetes.stake_usd)` (backfill em re-sync, nunca apaga); `list_bilhetes` já faz `SELECT *`; (4) `index.html` — sub-linha `.btbl-stake-usd` (mono 10px `--ink-mute`) sob o R$, só quando `b.stake_usd != null` (reusa `fmtUSD`). **Backfill dos 202 existentes:** Feca clica ↻ Sincronizar 1× na Polymarket após o deploy → ON CONFLICT preenche o USD (BRL intacto). Backup: `Backups/polymarket-stake-usd_2026-06-28/`. NOTA de coordenação 2-terminais: minha edição em `repository.py` foi commitada junto no `4cf9a7a` (commit do terminal do /esportes), pois o tree é compartilhado — código correto, só atribuição misturada. Pendente: validação visual no deploy + re-sync.)_

_Anterior: 2026-06-28 (sessão 64 — COLUNA P/L NA LISTA DE APOSTAS. Liga o campo `pl` (calculado no backend, sessão 62) à UI, em `app/static/index.html`. Coluna nova entre **Resultado** e **Ações** (pedido do Feca, seguindo `UI_REFERENCE`). Mudanças: (1) header `<div class="btbl-th right">P/L</div>`; (2) grid-template + `BTBL_DEFAULT` ganham 1 largura (100px) → 11 colunas px + spacer 1fr; chave localStorage `fdc-btbl-cols-v2`→`v3` (invalida larguras salvas antigas, que tinham 10 itens); (3) helper `fmtPL(v)` espelha o `fmtPL` do Betting Dashboard / `UI_REFERENCE §5`: sinal colado +R$/−R$ (minus U+2212), pt-BR 2 casas, cor pos/neg só no `.money-val`; aposta aberta (`pl=null`) → travessão neutro; (4) CSS `.money.pos/.neg .money-val` + `.btbl-pl .money{width:auto}` p/ alinhar à direita. Endpoint `/bilhetes` já repassa `pl` (retorna `rows` direto). Backup: `Backups/sessao62_pl_e_padrao_monetario/index.html`. Zero (Void/cashout=stake) é NEUTRO por decisão do Feca: `R$ 0,00` sem sinal e sem cor (refinamento sobre o fmtPL do Dashboard; documentado em `UI_REFERENCE §5`). Pendente: validação visual no deploy; P/L no Betting Dashboard (Fase C).)_

_Anterior: 2026-06-28 (sessão 63 — UI DO PAINEL POLYMARKET (alinhamento de marca). 3 pedidos do Feca, todos no `app/static/index.html`: (A) carteira + botão Sincronizar saíram da linha abaixo dos inputs e subiram para o `.partner-header`, ocupando o lugar do seletor de modelo (escondido na Polymarket — casa sem IA de visão); novo grupo `.poly-head-sync` (status + input `.poly-wallet-input` + botão), `#polymarket-section` removido, `aplicarModoCasa` agora alterna `#poly-head-sync`/`#modelo`. (B+C) KPIs e caixa de Posições Ativas eram full-bleed (encostavam no x=0) e a caixa usava raio `--r-sm` — agora recuados 18px nas laterais (mesmo inset da `.btbl-wrap` das apostas) e a caixa de ativas com raio `--r-lg`, virando o mesmo card de marca (UI_REFERENCE §4), alinhada com a caixa das apostas. Backup: `Backups/polymarket-ui-cabecalho-card_2026-06-28/`. Pendente: validação visual do Feca no deploy.)_

_Anterior: 2026-06-28 (sessão 62 — P/L NO BACKEND + PADRÃO MONETÁRIO. Contexto: o Planilhador vai substituir a planilha como fonte do Betting Dashboard, então o cálculo de P/L (antes nas fórmulas das colunas K/L da planilha) precisa morar no backend. Implementado em `app/repository.py`: helper `_num()` (parse BR "1.234,50"→float) + `calcular_pl(stake, odd, resultado)` — campo DERIVADO (calculado na leitura de `list_bilhetes`, NÃO persistido; edições refletem na hora). Espelha o SWITCH da planilha: W=stake×odd; L=0; V=stake; HW=(stake/2)×odd+stake/2; HL=stake/2; P/L=Valor−stake; aberta→None. Validado contra 9 casos reais dos prints da planilha (561,10 V→0; 100×1,81 W→81; etc.) — todos batem. Decisão (com o Feca): backend entrega P/L como número cru; a máscara monetária é da UI. Padrão monetário FDC documentado em `docs/UI_REFERENCE.md §5` (era ausente): toLocaleString pt-BR 2 casas, sinal colado +R$/−R$ com minus U+2212, cor pos/neg só no número, R$ menor 0.76em neutro. RESOLVIDO (confirmado pelo Feca): em TODO o histórico da planilha a odd já representa Resultado÷Stake, então a fórmula derivada gera o P/L correto também para as linhas importadas — descartadas as colunas persistidas `pl_num`/`valor_num` (item 6 do plano, agora obsoleto). Coluna P/L na lista ligada na sessão 64; resta o P/L no Betting Dashboard (Fase C).)_

_Anterior: 2026-06-28 (sessão 62 — ORDEM DA LISTA. Diagnóstico: a lista ordena por `criado_em DESC` (= hora de inserção no Postgres), não pela data da aposta. O import de hoje (20.215 linhas `origem='import'`) carimbou `criado_em = NOW()` e subiu ao topo, na frente das extrações reais. Correção 1 (dado, produção): backfill do `criado_em` do bloco `import` para abaixo do corte `T_min` (15/06 01:06, extração/sync mais antiga), ordenado pela data real DD/MM/YYYY desc — fórmula `(T_min − 1min) − (data_max − data_linha)`. 20.215 linhas; bloco vai de 24/12/2025 (data 01/01) a 15/06 01:05 (data 23/06); 0 acima do corte; extração/sync intactas. Backup reversível em `Backups/backfill-criado-em-import-20260628_230659/snapshot_criado_em.csv` (22.452 linhas, criado_em original). Correção 2 (código, commit `31bd60c`): `list_bilhetes` ORDER BY ganha desempate `, id {dir}` — sem ele, linhas de mesmo `criado_em` voltavam embaralhadas e instáveis entre páginas. Pendente: validar na tela após deploy)_

_Anterior: 2026-06-28 (sessão 61 — ALINHAMENTO DE MARCA UI no `index.html` via 5 auditores. ~10 cores off-brand viraram tokens (`#36d399`, `#f5a623`, `#e53935`, 2º azul `#4A90E2`). Triplets `--accent/pos/neg/warn-rgb` em `tokens.css`. Scrollbar de marca (antes era a do navegador). Bloco Polymarket: `--grid` virou `--line`, `10px` virou `--r-sm`. 9 labels ganharam `font-mono`. Bug de tokens inexistentes `--surface2`/`--border` (caíam em cinza off-brand) corrigido. Stake/Odd da Lista alinhados à direita (número + cabeçalho). Brilho da bolinha de online não corta mais (`overflow` movido para `#user-nome`). Doc `docs/UI_REFERENCE.md` criado. Board do Betting Dashboard: topbar corrigida de 68px para 44px. Pendente: validação visual do Feca)_

> Próxima sessão: (1) **Validar no deploy** a ordem da lista (extrações reais no topo, bloco importado no fim ordenado por data desc) + a UI da sessão 61. (2) **Decidir o modelo de login de operadores** (ver §4 sessão 60). (3) **Migrar a base do OPERADOR** (CSV separado que o Feca vai subir; mesmos padrões da migração do Feca — ver §4 lote 19). **Atenção:** a migração do operador deve carimbar `criado_em` do bloco abaixo do `T_min` dele (mesma lógica do backfill da sessão 62), senão o import sobe ao topo. (4) **Rotacionar a senha do Postgres** no Railway (a DATABASE_URL trafegou no chat). (5) Fase C do PLANO_UNIFICACAO: endpoint `/dashboard/data` + dashboard same-origin (o campo `pl` derivado da sessão 62 já está disponível em `list_bilhetes`). (6) Ligar o campo `pl` na coluna P/L da lista/Dashboard (cálculo já feito no backend; falta só exibir com a máscara monetária FDC do `UI_REFERENCE §5`). (7) Candidatos antigos: aposentar app Polymarket standalone; cadastrar Snooker em `MASTER_ESPORTES`. (8) **SEGURANÇA (auditoria sessão 67):** definir `SESSION_SECRET` no Railway (senão sessões caem a cada reinício); **migrar hash de senha** para bcrypt/argon2 — ver bloco "Hash de senha" abaixo; rotacionar a senha do Postgres (item 4). (9) **Adiados da sessão 67:** limpeza de CSS/JS morto no `index.html` (passada fresca, ver entrada da sessão 67); reconciliar doc do `golden_set/`.

> **Hash de senha (plano — fazer COM o Feca, não sozinho).** Hoje `auth.py` guarda SHA-256 **sem salt** e os hashes estão versionados no código (defaults). Problema: rápido de quebrar offline e exposto no git. Não dá para migrar sozinho porque exige a senha em texto puro (que eu não tenho) — trocar o algoritmo sem isso trancaria os usuários para fora. Passos quando o Feca puder: (a) adicionar `bcrypt` (ou `argon2-cffi`) ao `requirements.txt`; (b) Feca escolhe senhas novas e gera os hashes (`python -c "import bcrypt,getpass; print(bcrypt.hashpw(getpass.getpass().encode(), bcrypt.gensalt()).decode())"`); (c) pôr os hashes em env vars no Railway (`SENHA_FECA_HASH`/`SENHA_DIOGO_HASH`), **não** no código; (d) `verificar_credenciais` passa a usar `bcrypt.checkpw`; (e) remover os hashes default do código. Enquanto não rola, o risco está mitigado mas não eliminado.

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

- **Sessão 62 (28/06/2026) — Backfill de tipster (falha da migração) + badges da sidebar repensados:**
  - **Sintoma (Feca):** navegando casas/parceiros, muita aposta sem Tipster. **Diagnóstico:** 1.991 bilhetes sem tipster, **100% `origem='extracao'`** — nenhuma do import. Eram as linhas que o app extraiu nas **contas ativas** e que a migração era-split manteve de propósito (têm código → dedup), mas **sem backfill do tipster a partir da planilha**. A linha extraída vinha com tipster vazio enquanto a planilha já tinha o tipster.
  - **Correção (cruzamento com `2026 Contas Pessoais - DB Apostas (7).csv`):** casador em camadas (descrição+stake+odd → stake+odd+resultado → stake+odd → descrição+stake → tolerância de odd ±0,01), tratando os 2 problemas de formato de odd: **ponto-decimal das múltiplas Betano** (bug s50, `75.260...`) e **arredondamento de odd de 3 casas** (banker's no DB vs 2 casas no sheet). **1.981 tipsters preenchidos** via `UPDATE` cirúrgico (só onde tipster vazio, dono Feca, em transação; snapshot de rollback salvo). Restam **8 sem tipster**, todos sem origem no CSV: 6 `Betnacional/renanfernando01` (DB-only reais, extraídos após a última planilha) + 2 `Betano/pabloga03` (mesma múltipla de Desarmes que o CSV lista com Arrudex **e** Peixe → 2 bilhetes distintos, impossível desambiguar sem código). **Lição p/ a base do operador:** ao manter linha extraída de conta ativa no overlap, **backfillar o tipster do sheet** (o app sempre extrai tipster vazio).
  - **Badges da sidebar repensados (o "não copiadas" perdeu sentido — base migrada, não se copia mais):** a bolinha agora sinaliza bilhetes **incompletos**. **Azul (`--accent`)** = sem tipster; **âmbar (`--warn` #E0A21A)** = abertas (sem resultado). Backend: `repository.contar_incompletos` + `GET /incompletos` (sem_tipster + abertas por casa/parceiro, `COUNT FILTER`, `HAVING > 0`). Frontend: 2 badges por linha (casa-header + parceiro-item), `atualizarPendentes` agora puxa `/pendentes` (rodapé copiadas/pendentes, **mantido**) **e** `/incompletos` (sidebar); `aplicarBadgesPendentes`→`aplicarBadgesSidebar`. Pós-backfill a sidebar fica quase limpa (8 azuis + 3 âmbar na base toda) → sinal volta a ser informativo. Verificação: `py_compile` + `node --check` OK. **Falta o Feca validar visualmente no deploy.**
  - **Preenchimento de tipster estilo planilha (lista):** o Feca pediu velocidade tipo Google Sheets. **Pass 1 (teclado/autocomplete):** melhor match já vem destacado no dropdown → Enter/Tab aceita sem precisar de seta. **Pass 2 (Sheets-puro, escolhido pelo Feca):** os inputs de tipster da lista (`.btbl-tip-input`) viraram `readonly` por padrão e ganharam um **controlador único de coluna** — clique **seleciona**, Shift+clique/Shift+setas **estende** a faixa, setas **movem**, duplo-clique/F2/Enter/digitar **edita**, **Ctrl+C/Ctrl+V** copia/cola (1 valor → preenche a faixa; N valores → cola sequencial; `navigator.clipboard` + fallback interno), **Delete** limpa. Commit por Enter/Tab (desce) ou Shift (sobe); Esc cancela. CSS de marca: `.cell-sel` (faixa `--accent`) + `.cell-active` (outline `--accent`); sem caret no modo seleção. Removidos o save-inline e a navegação do Pass 1 (o controlador novo assume); save reutilizável `salvarTipsterVal(id, valor)` (PATCH otimista + sinal azul + badge). Dropdown de autocomplete segue compartilhado com modal/Polymarket. `node --check` OK. **Falta o Feca validar no deploy.**
  - **Editor (modal) — Esporte com autocomplete + Data com calendário:** `Esporte` virou `js-ac-esporte` (mesmo controlador de dropdown do tipster, lista própria via `repository.list_esportes` + `GET /esportes`, 14 esportes distintos). `Data` ganhou um `<input type="date">` sobreposto invisível: **duplo-clique** abre o calendário (`showPicker()` com fallback) e escreve de volta em DD/MM/YYYY; digitar à mão continua funcionando (conversões BR↔ISO). `node --check` + `py_compile` OK.
  - Backup: `Backups/badges-incompletas-sidebar_2026-06-28/`. ⚠️ Lembrete pendente: **rotacionar a senha do Postgres** (DATABASE_URL trafegou no chat).

- **Sessão 60 (28/06/2026) — Ajustes visuais da sidebar (antes da base do operador):**
  - **Logo fixo no scroll + export na base (commit `9c29600`):** `.sidebar` virou layout de 3 faixas — topo fixo (logo + operador), miolo rolável (`.sidebar-scroll`, casas), rodapé fixo. O **Baixar base (CSV)** foi pro fim do menu. Só o miolo rola.
  - **"Usuário" → "Operador" com menu suspenso:** a `user-bar` virou `.operador-bar` (botão rotulado **Operador** + caret, dropdown com Sair; abre/fecha por clique e fecha ao clicar fora/Esc). **Prep visual** para o modelo de login de operadores — ver abaixo.
  - **Header do parceiro sem repetição:** deixou de mostrar "Casa · Parceiro" grande **e** "Parceiro" embaixo. Agora **casa grande** + **parceiro menor embaixo** (padrão do print BOOKIE). `selecionarParceiro`: `partner-name = nomeCasa`, `partner-sub = p.nome`.
  - **Abas Ativas / Inativas na sidebar (commit `50c24ce`):** separa as casas pelo estado do parceiro (`arquivado`). **Ativas** (padrão) esconde as contas migradas/arquivadas; **Inativas** mostra só os arquivados, com botão **Reativar** (↩) no lugar de Arquivar (▣). `carregarParceiros` busca `arquivados=true` e separa em `parceirosCache` (ativos) + `parceirosArquivadosCache`. Arquivar/reativar move entre abas em tempo real. Regra de visibilidade: casa aparece na Ativas com ≥1 ativo **ou** quando totalmente vazia (preserva criar o 1º parceiro); some quando só tem arquivados. Reusa endpoints `/parceiros?arquivados=`, `/arquivar`, `/reativar` (nada no backend).
  - **Lista de apostas estilo Dashboard (commits `e80aa38` backend + `a6e0bfe` frontend):** a grade-planilha virou a lista `.btbl-*` do Betting Dashboard (ref: `REFERENCIA_LISTA_APOSTAS.md`). **Ordem mais novo→mais antigo**; **paginação de 100** substitui o "arquivar acima de 40" (o `auto_arquivar` segue rodando no save mas a lista lê `archived=all`, então não esconde nada — paginação governa). Backend: `/bilhetes` ganhou `limit`/`offset` + `total` real (`contar_bilhetes`, `_filtros_bilhetes`). Frontend: grid de colunas, chips de esporte (emoji) + casa (favicon), pílula de resultado, stake em `.money`, contador "X de Y". **Tipster editável inline**; **botão Editar (✎) → modal** com os 10 campos visíveis (código interno fica de fora por ser chave de dedup). Removida a maquinaria de planilha (contenteditable, seleção retangular, teclado, copiar/colar TSV). **Fluxo de export mantido** (decisão "mais seguro"): Copiar pendentes/Baixar .tsv/Marcar/Desmarcar agora operam sobre TODAS as páginas (helper `bilhetesPorEstado` pagina em blocos de 1000); stats do parceiro inteiro (total=contagem, pendentes=mapa `/pendentes`, copiadas=total−pendentes). **Faltou de propósito:** coluna **P/L** (depende da Fase A2 `pl_num` — recálculo dá erro de arredondamento) e **ordenação por coluna** (não pedida). Verificação: `py_compile` + `node` (sintaxe) OK; **falta o Feca validar visualmente no deploy.**
  - **Polimento da lista + chips (commits `704f989` card+modal, `d72275f` chips, `483aa4a`+`631d3cf` colunas/alinhamento):** lista dentro de **card** (descola do grid de fundo: `--surface`+`--line`+`r-lg`). **Modal de edição** no padrão de formulário da marca (inputs JetBrains Mono em `--field`+`r-sm`, labels mono `.16em`, título com tick de acento, botão fechar em caixa — ref: `pack/tokens` + Dashboard modelo). **Chips de esporte** na `REFERENCIA_EMOJIS_ESPORTES` (24×24, grayscale, alias map case-insensitive, fallback **🏅**, combinadas **🔗**). **Colunas redimensionáveis:** template em CSS var, alça por cabeçalho, persiste em `localStorage` (chave `fdc-btbl-cols-v2`), duplo-clique reseta; todas px (incl. **Aposta/Evento**) + spacer `1fr`. Header+linhas num **scroll único** (sticky header) → corrige o desalinhamento que vinha do scrollbar só no corpo; scroll horizontal quando passa da largura. Removido o ✓ de copiar na linha; contador "X–Y de Z apostas"; **Resultado** renomeado+centralizado. (Stake/Odd terminaram **à direita** — ajuste final do terminal paralelo, commit `c60bb4a`.)
  - **Terminal paralelo (outro agente, MESMA working tree) — backend + favicons/tipografia:** fix do **UniqueViolation da Betnacional** (`repository.py`, guard NOT EXISTS). Favicons/sidebar: chips greyscale iguais ao Dashboard, mapa de domínios `.bet.br`/`.com`, casas novas (7K, Bateu, Betbra, Betpontobet), **Rei do Pitaco → exibe "Pitaco"** (favicon `pitaco.bet.br`), preenchimento de chip BETesporte/BetMGM, **hierarquia de fonte casa/parceiro** na sidebar (commits `868ccef`, `bbf1ef1`, `75d54bd`, `4d226f8`, `e1fde2d`, `8d19ff7`).
  - **Coordenação de 2 terminais (mesma working tree):** STATUS centralizado **neste** terminal (escriba único); o outro encerra **sem commit de STATUS** e sem `git add -A`. Commits em série (1 working tree → lock impede simultâneos). Histórico linear, local == origin.
  - **Autocomplete de tipster custom:** o `<datalist>` nativo (não estilizável → espaçamento/alinhamento ruins) foi trocado por um dropdown próprio (`.ac-menu`, position:fixed no body, teclado ↑/↓/Enter/Esc + clique, fecha em scroll/blur). Um controlador único serve os 3 inputs marcados `.js-ac-tipster` (grade, modal, Polymarket); seleção dispara `change` (Poly) + `blur` (grade salva no focusout). `carregarTipsters` agora guarda em `tipstersList`.
  - **Respiro no input de tipster (commit `7b9f90c`):** padding simétrico `4px 7px` (texto não cola na borda no foco) + header Tipster com `padding-left:7px` (`.th-tip`) p/ acompanhar.
  - **Fechamento da sessão (terminal paralelo, commits `992b0be` + `c60bb4a`):** alinhamento final do `index.html` à marca FDC (Betting Dashboard) e Stake/Odd da lista à direita. São os 2 últimos commits no `index.html`.
  - **Refs versionadas:** `REFERENCIA_CHIPS_CASAS.md`, `REFERENCIA_EMOJIS_ESPORTES.md`, `REFERENCIA_LISTA_APOSTAS.md` commitadas (specs da marca que embasaram a UI).
  - **PENDENTE (decisão do Feca, discutir antes de codar): modelo de login de operadores.** Conceito travado: **dono de carteira** (usuário, ex. Feca) pode **criar logins de operador** que acessam aquela base; criar novo usuário = novo dono. O dono cria o login do operador e ele passa a ter acesso à base do dono. Isso mexe em `auth.py` (hoje `USUARIOS` é dict estático em código + senha hash) e no modelo `dono` (coluna que isola dados). **Só o relabel visual foi feito; a mecânica de login fica para sessão dedicada.**
  - Backup: `Backups/ajustes-visuais-sidebar_2026-06-28/` + `Backups/pre_lista_dashboard_2026-06-28/`.

- **Sessão 59 (28/06/2026) — Início da migração planilha → Postgres (unificação c/ Dashboard):**
  - **Plano completo:** `PLANO_UNIFICACAO_2026.md`. Resumo da memória: [[migracao-planilha-dashboard]].
  - **Decisões travadas:** era-split (NÃO apagar o banco — recentes têm Código→dedup intacta; importar só era pré-DB; Polymarket fora); **P/L vem da planilha** (coluna L), nunca recalculado (odd arredondada → −R$319 de erro, achado do harness); migração **em fatias por casa inativa**; coluna `origem` (extracao|sync|import); de-para completo já definido (esporte/casa/categoria); `Outras→Outros` já aplicado (commit `a9da64c`); arquivar parceiro inativo = >20 dias.
  - **Acesso prod:** `DATABASE_URL` (proxy público Railway) no `.env` (gitignored). ⚠️ **ROTACIONAR a senha do Postgres quando a migração terminar** (saiu no chat).
  - **Feito:** A1 = botão **Export base CSV** (backup, commit `77b2b5c`). **Coluna `origem`** + `/casas` une manuais+casas-com-dados (commit `dfdd8fa`). **PILOTO** (casas inativas **7K + Bateu**, linhas 2–68 da planilha = **67 bilhetes**) gravado na prod e **auditado**: stake R$ 13.061,83, P/L −231,07, 67/67 tipsters, 0 linhas pré-existentes alteradas. Validado pelo export do Feca (2.174→2.241, +67, só 7K/Bateu).
  - **Lote 2 (Bet365 inativos):** faixa 70-8522 do CSV(5), **8.453 bilhetes, 19 parceiros** (NÃO os 3 ativos: gleicecacia01/marloncezar01/Taliacoelho01 [Richard]), gravados na prod. Auditado: turnover R$ 1.955.209,12, profit R$ 106.630,50, 552 ativos preservados. ⚠️ **Lição:** `upsert_bilhetes` linha-a-linha estoura o timeout de 2min em lotes grandes (deu insert parcial de 564, limpo e refeito). **Método novo p/ lotes grandes:** bulk `executemany` em transação, replicando `_assinatura` (com contador de duplicata), `ON CONFLICT DO NOTHING`. Rápido e atômico. CSV fonte: usar sempre CSV (não XLSX — float reabre precisão).
  - **Lote 3 (Betano arquivados):** faixa 15144-18344 do CSV(5), **3.201 bilhetes, 32 parceiros**, gravados. Turnover R$ 880.177,32. **Overlap resolvido:** `lucasgeremias2026 [JC]` tinha 26 no DB (extracao, c/ código) que eram as 26 mais recentes das 516 do sheet → deletei os 26 e importei os 516 (sheet autoritativo, com correções de odd). Ativos preservados: 435 (pabloga03 253 + leudeson15 114 + caueglsports 68). **Padrão p/ overlap de conta arquivada:** sheet é a verdade → delete do DB + import completo.
  - **Próximo:** continuar na ordem da planilha (Pinnacle, Superbet, Betnacional inativos + ~28 casas totalmente inativas). As ATIVAS (3 Bet365: gleice/marlon/Talia; 3 Betano: pablo/leudeson/caue) ficam pra passada final com era-split/backfill (tipster+odd+resultado). Base do operador entra depois (CSV separado).
  - **Lote 4 (Betano ATIVA — leudeson15 [P2Pro], 1ª conta ativa):** padrão de overlap p/ conta ATIVA (diferente da arquivada): **DB manda no overlap** (precisão de odd + código pro dedup futuro), importa só a **era antiga por data** (< início do DB). Sheet rows 18346-18561 (216): 72 antigas (<11/06) importadas, 144 overlap mantidas intactas (com código), 1 lixo deletado (odd=500 erro de extração, código 20475505441, não estava no sheet — era o descasamento 145 vs 144). **Correções reais investigadas = 0** (as "diferenças" eram só arredondamento de odd 2-casas no sheet vs precisão cheia no DB → DB é melhor, não tocar). Turnover R$ 26.062,99 ✓. **Regra:** conta ativa nunca sobrescreve o DB no overlap; match por DESCRIÇÃO (col estável); só importar data < cobertura do DB.
  - **Lotes 5-6 (Betano ativas pabloga03 + caueglsports):** pabloga03 (sheet 18614-18890, 277): importadas 25 (21 antigas + 4 feitas à mão em 10/06 que o app não pegou), deletada 1 REKONIX duplicada (DB tinha L+W, sheet só W → manter W, deletar L stale), 252 mantidas. caueglsports (sheet 18891-18958, 68): **match perfeito, 0 a importar, 0 correções** — app já tinha tudo. Correções genuínas nas duas = 0 (só arredondamento de odd).
  - **✅ BETANO 100% RECONCILIADA:** DB 3.762 = planilha 3.762, turnover R$ 947.669,33 idêntico, 35 parceiros. (import 3.298 + extracao 464 mantidos c/ código). Primeira casa fechada inteira.
  - **Lote 7 (5 contas inativas multi-casa):** Betão|Laud (16), Betboom|Tumbalha (161), Betboo|Marsella (55), BETesporte|Feca (52), Betbra|Feca (43) = **327 bets, stake R$ 77.776,93**. **Lição de seleção:** selecionar por (casa,parceiro) e não por faixa de linha literal (a faixa do Feca pegava 1 stray Betfair|Duka da conta ativa seguinte). **Dados especiais confirmados pelo Feca como válidos:** Betboom "Generica CSV 1-11" = reconstrução por saldo (provedor sumiu c/ as apostas); BETesporte/Betbra "S:..." (odd fixa 2,00) = contas planilhadas só por saldo no início do ano. Importados como estão.
  - **Lote 8 (Betfair|Duka ativa grande + Betfast|Bell nova):** arquivo CSV(7), faixa 20415-21416. Betfair|Duka: sheet 995, importadas 862 antigas (22/01→18/06), 133 mantidas c/ código (0 correção, 0 DB-only). Betfast|Bell: 7 (casa nova, completa). Turnover R$ 123.590,99 ✓. (Atenção: a faixa tinha 7 Betfast no fim — conta separada, importada junto pois é nova e estava no total.)
  - **Lote 9 (multi-casa 21425-21582):** BetMGM|Feca (30), Betfast|Duka (24), Betfast|Feca [Eu] (29, typo "[ Eu]"→"[Eu]" normalizado), Betnacional|Marsella (35) = 118 bets, R$ 22.627,34. BetMGM casa nova. 40 linhas-template vazias na faixa, ignoradas.
  - **Betnacional RESOLVIDA:** Feca re-extraiu no app (bloco perfeito); Marsella [Eu] inativa/arquivada mantida. Não voltar.
  - **Lote 10 (Betpontobet nova + Bolsa de Aposta ativa):** Betpontobet|Feca = 35 (casa nova, R$ 2.635,77). Bolsa de Aposta|Feca (ativa): importadas 49 antigas (01/01→19/03), mantidas 80 (79 c/ código). 3 DB-only de 23/06 (2 REKONIX stakes 202/402 + Comedores de Rune, E-Sports) = **apostas REAIS confirmadas pelo Feca → mantidas**; logo Bolsa DB=129 > sheet=126 (sheet do Feca está faltando essas 3 reais; DB mais completo, OK).
  - **Lote 11 (multi-casa 21862-22078, 8 novas + 1 skip):** Casa de Apostas|Feca (49), Donald Bet|Feca (32), Esportes da Sorte|Feca (2)+|Marsella (7), Esportiva|Ellen (52), Estrela Bet|Ellen (15), Faz1Bet|Feca (4, casa "Faz1bet"→"Faz1Bet" de-para), Fulltbet|Feca (49) = 210 bets, R$ 35.943,64. Jogo de Ouro|Feca (7) já no DB, MATCH PERFEITO → pulado.
  - **Lote 12 (KingPanda match + KTO ativa):** KingPanda|Ellen (100) MATCH PERFEITO no DB → nada a fazer. KTO|Feca (ativa): importadas 17 antigas (02/03→16/04), 4 mantidas c/ código, 0 correções. Total KTO 21.
  - **Lote 13 (misto 22262-22851):** 6 novas = Lance de Sorte|Feca (20), MatchBook|Feca (48), MultiBet|Feca (47), Novibet|Ellen (152)+|Feca (277)+|Laud (8) = 552 bets R$ 95.180,64. Lottu|Feca (ativa): match 30=30, **1ª correção de data aplicada** (James Rodriguez 24→23/06, assinatura recalculada para não quebrar dedup).
  - **Lote 14 (Pinnacle ativa) CONCLUÍDO:** Feca processou export MyBets no app (DB Pinnacle|Feca 229→281, coded, 25/05→26/06 = bloco perfeito, janela 01-15/06 resolvida). Eu importei sheet < 25/05 = 66 antigas (01/01-24/05), R$ 26.367. Total Pinnacle|Feca = 347. **Lição:** export oficial usa redação de descrição DIFERENTE do sheet → match por descrição não pareia o período do export (apareceriam falsos "a importar" >= data do export que duplicariam). Regra: export manda no período dele; importar só era anterior POR DATA.
  - **Lote 15 (multi-casa, GAP Polymarket pulado):** PixBet|Feca (47), Rei do Pitaco|Ellen (16)+|Feca (18), SportingBet|Marsella (41) = 122 bets, R$ 26.663,10. Tipster "Ω Teste Encerrado" = marcador legítimo do Feca (estratégia descontinuada), importado normal.
  - **Lote 16 (Superbet, bloco 23678-25698):** 23 contas novas + 5 ativas overlap (Pedrog12contas 217 import, Evertonbatista03, viniciusisa422, anapetry03, pedrofeitosa20211) + guisouza123654 = **1.725 importadas + 56 correções de data** (18+38). **Bug de data futura 19/07/2026 ELIMINADO** (6 bets Superbet origem=extracao: 3 Everton, 1 anapetry, 2 guisouza → corrigidas pra junho via sheet). anapetry tinha 2 DB-only reais (Chris Wood, Michael Olise) mantidas. Offsets de ±1 dia (liquidação vs evento) também corrigidos p/ bater com sheet.
  - **Lote 17 (Superbet thuany01 + lucielesales03):** match perfeito (13=13, 24=24), 0 import, só 12 correções de data (+1 dia, 24→25/06).
  - **Lote 18 (Bet365 marloncezar01 + stragglers):** marloncezar01 importadas 2.867 antigas (19/03→14/06), 248 mantidas → 3.115 = sheet. valdilealrpb +2, João Pedro Invest +1 (stragglers CSV-5→CSV-7) → batem. Superbet "Parceiro1" (id=1, TesteTipster Flamengo x Vasco) DELETADO. **CHECK GERAL:** 35 casas reconciliadas; "+N" são DB-only reais (Betnacional/Bolsa/Pinnacle/Superbet/Polymarket); 0 datas futuras. Falta só gleicecacia01.
  - **Lote 19 (Bet365 gleicecacia01 + Taliacoelho01) — FECHA A BASE DO FECA:** gleice importadas 1.437 antigas + 39 correções de data → 1.657 (1.655 sheet + 2 DB-only reais: Bósnia v Qatar, tênis Dev/Sinha). Talia match perfeito (84=84). 
  - **🎉 MIGRAÇÃO DA BASE DO FECA COMPLETA (CHECK FINAL):** planilha 22.394 vs DB 22.451 (+57 = DB-only reais/API, todos explicados: Bet365 +2, Superbet +2, Bolsa +3, Pinnacle +30, Betnacional +11, Polymarket +9). 30 casas batem exato. 0 datas futuras. origem: import 20.215 / extracao 2.029 / sync 207.
  - **Progresso prod:** Base do Feca migrada e reconciliada. **PRÓXIMO: base do OPERADOR (CSV separado, o Feca sobe depois).** Depois: Fase C (endpoint /dashboard/data + dashboard same-origin) + Fase A2 (pl_num) do PLANO_UNIFICACAO. **Lembrar: rotacionar senha do Postgres no fim.**
  - **Padrões da migração (referência p/ a base do operador):** importar por `executemany` em transação (não `upsert_bilhetes`, que estoura timeout em lote grande); selecionar sempre por (casa,parceiro), não por faixa de linha crua; conta inativa = import limpo; conta ativa = DB manda no overlap (preserva código), importa só era anterior por data, aplica correções reais de data com recálculo de assinatura; DB-only reais = manter; normalizar typos de parceiro (`[ Eu]`→`[Eu]`) e casa (`Faz1bet`→`Faz1Bet`). Acesso prod via `DATABASE_URL` no `.env` (gitignored). Arquivo fonte da base do Feca: `2026 Contas Pessoais - DB Apostas (7).csv`.
  - **Pendente do plano (fases futuras):** endpoint `GET /dashboard/data` (replica contrato do `Code.gs`) + hospedar Dashboard same-origin + colunas numéricas `pl_num` p/ o dashboard.

- **Sessão 58 (27/06/2026) — Auditoria da integração Polymarket + correções + modo online:**
  - **Auditoria (3 auditores em paralelo + checagem própria):** port Python vs app standalone JS, integração backend (rotas/dono/COALESCE), frontend, e conexão casa↔masters. `audit_casas`: 12/12 OK; taxonomia 100% conectada (10 categorias e todos os esportes emitidos são canônicos). Veredito: integração sólida, nada quebrava produção.
  - **Correções aplicadas (commit desta sessão):**
    - **Paginação (`polymarket.py`):** `/positions` voltou a `limit=100` e `/activity` a `limit=500` (espelha o app standalone). O `limit=500` em positions podia truncar o histórico em silêncio (a parada `len < limit` quebrava na 1ª página). Dry-run pós-fix: 207 resolvidos.
    - **Tipster sobrescrito no re-sync (`repository.limpar_ativos_tipster` + `main.py`):** a `polymarket_ativos_tipster` nunca era limpa após o carry-over → re-sync reinjetava o tipster antigo por cima de uma edição na grade. Agora, após o upsert, as linhas migradas são deletadas (resolve também o crescimento de órfãos).
    - **Dashboard multi-compra (`_split_multibuys`):** `currentValue` agora é distribuído proporcional ao stake de cada split (espelha o JS) — antes cada split herdava o valor cheio e inflava portfólio/%P&L de ativas multi-compra.
    - **reconciliarRedeems:** fallback do valor resgatado `size‖amount` (alinhado ao JS; era `size‖usdcSize`).
    - **PTAX de hoje (`coletar_bilhetes`):** recua até 6 dias em fim de semana/feriado (igual ao dashboard) — evitava gravar stake em USD rotulado como BRL quando o sync caía num dia sem boletim.
    - **E-Sports Props:** over/under de estatística de E-Sports agora vira `E-Sports Props` (invariante global), não `Player Props`.
    - **Frontend:** `esc(data_rel)` (XSS), `salvarTipsterAtivo` checa `rs.ok` + rollback + aviso (paridade com a grade), guard de duplo-sync (clique+Enter+auto via flag `polySyncing`), âmbar `#E0A21A`→`var(--warn)`, feedback de carteira inválida no dashboard.
  - **Modo online (`index.html`):** ao entrar na casa Polymarket, um poll de 60s atualiza o dashboard; quando uma posição **sai das ativas** entre dois polls (resolveu), dispara um **sync silencioso** que a puxa pro TSV automaticamente. Sem clique. Sync manual (botão) continua. Decisão: detecção por encolhimento do conjunto de ativas (eficiente) em vez de full-sync a cada tick.
  - **Doc:** `CASA_POLYMARKET §2` (tamanho de página por endpoint) e `§13` (exceção arquitetural consciente: classificação esporte/categoria é em código, não herda as listas dos masters).
  - Backup: `Backups/pre_auditoria_polymarket_2026-06-27/`.

- **Sessão 56 (27/06/2026) — Polymarket vira fonte na grade unificada (branch `feat/polymarket-ingestao`, NÃO mergeado):**
  - **Pedido (Feca):** o projeto Polymarket (pasta-irmã, Node/Express+JS) faz a mesma coisa que o Planilhador — extrai apostas — só que via API com conversão USD→BRL. Não faz sentido serem separados; trazer a Polymarket como guarda-chuva do extrator. Escopo decidido: **só a ingestão** (o dashboard analítico da Poly fica fora). Mecanismo: **reescrita em Python** (um app só). Feca delegou decisão+execução.
  - **Insight:** os dois apps já convergem no mesmo contrato — o `buildTSVRow` da Poly emite exatamente as 10 colunas do Planilhador. A Poly só reimplementava (pior, em localStorage) a grade/tipster/copiadas que o Planilhador já faz melhor (Postgres, multiusuário, dedup, teclado). A diferença é só a porta de entrada: screenshot+IA vs API.
  - **Coletor (`app/polymarket.py`, novo, commit `96b2743`):** porta o pipeline do app standalone — busca `positions`+`activity` (paginação **sem teto** → histórico desde a 1ª aposta), reconcilia vitórias resgatadas (`reconciliarRedeems`), expande compras múltiplas (`splitMultiBuys`), converte USD→BRL via PTAX/BCB do dia. Detecção de esporte/categoria determinística normalizada p/ a taxonomia global (e-sports colapsa em `E-Sports`; Snooker→`Outro`). Código de dedup = `conditionId`/`__i`. **Reusa o Worker Cloudflare** `polymarket-proxy.flrcarvalho.workers.dev` (a peça que destrava a API no BR) — confirmado respondendo do Brasil (HTTP 200).
  - **Validação real (dry-run, sem tocar banco):** carteira `0x2b3c…9f22` → **202 bilhetes resolvidos, 83 W / 119 L**, conversão BRL correta, odds em precisão cheia com vírgula. 33/202 caíram em `Outro` (cauda longa sem liga no título) — ajustável na grade.
  - **Integração (commit `6bc9055`):** `CASA_POLYMARKET.md` (camada fina, 15 seções, passa o audit), `POLYMARKET` em `_CASA_DISPLAY`+`NOMES`/`DOMINIOS`, rota `POST /polymarket/sync` (espelha `/salvar`: upsert+auto-arquivar), painel **carteira+Sincronizar** que troca o upload quando a casa é Polymarket (`aplicarModoCasa`), reusa a grade inteira. `httpx` em requirements. **`audit_casas`: 12/12 OK.**
  - **Decisões registradas:** ingere só posições RESOLVIDAS (W/L) — espelha o `getOrderedFechados` do app antigo e evita a borda de dedup aberta→resolvida em compras múltiplas; posições abertas ficam p/ fase futura. Snooker é candidato a esporte canônico no `MASTER_ESPORTES` (mudança separada, não feita aqui).
  - **Status:** MERGEADO na main + deployado na Railway em 27/06. A coleta/parceiro NÃO puderam ser feitos daqui — sem `DATABASE_URL` de prod nem sessão de login local (só `ANTHROPIC_API_KEY` no `.env`). **Falta o Feca fazer no app (3 cliques):** criar parceiro `Feca [Eu]` sob Polymarket → colar a carteira `0x2b3cf54201a00def81ec5d840da7d58fc37e9f22` → Sincronizar.
  - **1ª sync do Feca (27/06):** 202 bilhetes vieram (= 202 encerradas do app antigo ✓), MAS (a) ordem embaralhada e (b) painel de sync com caixa tracejada grandona inútil. **Fix (commit `d7f7798`):** ordenação por `(data, _buyTimestamp)` — compra única não tinha timestamp e empilhava com chave 0; agora cresce 07/05→27/06 igual ao app antigo (validado). UI: painel compacto (linha única carteira+Sincronizar). Backup: `Backups/polymarket-fix-ordem-ui_2026-06-27/`.
  - **Migração da ordem já gravada:** a grade ordena por `criado_em` (ordem de inserção) → os 202 já gravados embaralhados NÃO reordenam sozinhos. Como não havia edição (tipster vazio), orientação ao Feca: **deletar os 202 + re-sincronizar** (entram na ordem certa), depois copiar as últimas + Marcar todas.
  - **Import de tipsters do app antigo (commit `a53e584`):** os tipsters viviam só no localStorage do app standalone (`flrc_tipster_assign_v1`). Como a API não os tem, re-sync não traz. Solução: rota `POST /polymarket/importar-tipsters` lê o `.tsv` exportado do app antigo (col Tipster + Descrição) e casa por **descrição** (chave exata — mesmo título da API). Botão "⇪ Importar tipsters" no painel Polymarket. Validado local contra `polymarket_2026-06-27.tsv`: **202/202 casados, 0 sem-match**, 8 tipsters (eSports LG 87, Punter 28, Tenis LG 28, deLucca 25, Nine 15, fullpicks 9, Nomade 9, Femguia 1). **Feca rodou no app → deu certo (202 tipsters preenchidos).** Por ser one-shot, a ferramenta foi **REMOVIDA** logo após (rota + função + botão; commit de remoção) — restaurável pelo git (`a53e584`) se precisar de novo.
  - **Fix crítico — tipster apagado no UPSERT (commit `d3cc4ff`):** extração e sync sempre mandam `tipster=''` → o `ON CONFLICT`/fallback sobrescreviam e **apagavam** o tipster a cada reprocesso (os 202 importados sumiriam no próximo sync). Agora `tipster = COALESCE(NULLIF(EXCLUDED.tipster,''), bilhetes.tipster)` — vazio preserva o existente. Vale p/ todas as casas.
  - **Dashboard ao vivo da Polymarket (commit `a646e5e`):** a pedido do Feca, trouxe os widgets marcados do dash antigo. `coletar_dashboard(wallet)` → posições ativas + Portfólio (`/value`) + **Cash on-chain** (pUSD+USDC.e via `eth_call balanceOf` na Polygon — o "pedaço on-chain" que estava adiado, port simples) + Total. Rota `GET /polymarket/dashboard` (mescla tipster salvo), `POST /polymarket/ativo-tipster`, tabela `polymarket_ativos_tipster` (tipster da ativa, separado da grade de exportação). **Carry-over:** tipster posto na ativa migra pro bilhete quando resolve (UPSERT preserva). Odd da ativa = odd de entrada (1/preço), não mark-to-market. Frontend: painel KPIs + tabela com tipster editável (datalist), acima da grade, só na casa Polymarket; USD + sub BRL. Validado ao vivo: 7 ativas, cash on-chain $93, total $538.
  - **Fase 5 (aposentar standalone) ADIADA por decisão do Feca (27/06):** manter o app Polymarket antigo (`FDC Capital/Polymarket`) intacto **como backup** por enquanto. Não mexer nele até nova ordem. A nova ingestão no Planilhador roda em paralelo.
  - **Pendente pós-validação:** Feca confirmar ordem certa após delete+resync. Backup inicial: `Backups/polymarket-ingestao-fase1-2/`.

- **Sessão 55 (26/06/2026) — grade com teclado estilo planilha + autocomplete de tipster:**
  - **Pedido (Feca):** preencher tipster dentro do app (hoje exporta TSV pro Google Sheets só por causa da musculatura de teclado). Tipster é imprevisível bilhete a bilhete, mas os nomes se repetem → autocomplete pesa muito.
  - **Decisão:** caminho A (turbinar a grade que já existe), MVP. Caminho C (pré-preencher por leva/parceiro) descartado — tipster não é inferível. Caminho B (Handsontable/AG Grid) descartado — esforço alto, nunca bate a memória muscular do Sheets.
  - **Backend:** `repository.list_tipsters(dono)` (DISTINCT, não-vazio, por dono) + `GET /tipsters` em `main.py`. `tipster` já era PATCH-editável (`_EDITAVEIS`).
  - **Frontend (`app/static/index.html`):**
    - Célula de tipster virou `<input class="cell-input" list="tipster-options">` (datalist global) — autocomplete nativo dos tipsters já usados. Demais células seguem `contenteditable`.
    - Navegação por teclado: `Enter`/`Shift+Enter` desce/sobe na coluna · `Tab`/`Shift+Tab` anda lado a lado (estoura p/ próxima/linha anterior) · `↑`/`↓` movem entre linhas (exceto no input de tipster, onde controlam o dropdown).
    - Entrar numa célula via navegação seleciona todo o conteúdo → digitar substitui (igual Sheets).
    - Salvamento inline generalizado (`focusout`) atende tanto `contenteditable` quanto o input; novo tipster recarrega o autocomplete. `carregarTipsters()` dispara junto de `carregarGrade()`.
  - Backup: `Backups/pre_grade_teclado_autocomplete_2026-06-26/`. Commit: `3d311a2`.
  - **Fase 2 (mesmo dia, a pedido do Feca) — seleção retangular + copiar/colar:**
    - Seleção de células sobre as 8 colunas editáveis (data, esporte, tipster, aposta, descrição, stake, odd, resultado): `Shift+setas` estende a partir da âncora; clique define âncora, `Shift+clique` estende. Destaque azul (`.cell-sel`).
    - `Ctrl+C` copia o retângulo como TSV (com caret colapsado copia a célula ativa; com texto selecionado dentro de 1 célula deixa o copy nativo).
    - `Ctrl+V`: 1 valor + faixa selecionada → preenche a faixa toda (caso clássico: mesmo tipster em N linhas); matriz NxM → cola a partir do canto superior-esquerdo. PATCH otimista por célula + `renderGrade`; reverte célula a célula em erro. Colar 1 valor numa célula isolada cai no paste nativo (não tira o foco).
    - Backup: `Backups/pre_selecao_copiar_colar_2026-06-26/`. Commit: (este).

- **Sessão 54 (26/06/2026) — data de captura vazava entre parceiros:**
  - **Sintoma (Feca):** ao mudar a data de captura num parceiro (ex.: setar "ontem" na Bet365 para um print que diz "Ontem"), o valor grudava e era usado em todos os outros parceiros. Na Superbet seguinte, "Ontem" resolvia para anteontem porque a data de referência ainda era a de ontem.
  - **Causa raiz:** havia **um único** `<input id="data-ref">` global. O `estadoExtrator` (estado por parceiro) salvava `arquivos/csvFiles/xlsFiles/texto` mas **não a data** — então a data nunca era isolada por parceiro.
  - **Decisão (Feca):** manter o campo, isolar por parceiro. Default de cada parceiro = **hoje real** (fuso local do navegador) → "Ontem" sempre = ontem real, que é como o print vem.
  - **Fix (`app/static/index.html`, frontend apenas — backend já recebe `data_referencia` por requisição):**
    - Helper `hojeISO()` (YYYY-MM-DD no fuso local).
    - `dataRef` agora faz parte do `estadoExtrator` (salvo/restaurado por parceiro); guard de form vazio ainda atualiza só a data.
    - `restaurarEstadoExtrator` aplica `e.dataRef || hojeISO()` → parceiro novo cai em hoje.
  - **Comportamento:** trocar de parceiro não herda mais a data do anterior; recarregar a página zera tudo para hoje. Backup: `Backups/data-por-parceiro/`. Commit: (este).

- **Sessão 53 (26/06/2026) — cadastro do mercado Race ("Primeiro a marcar X"):**
  - **Sintoma (Feca):** bilhete Bet365 "Suécia — Primeiro a marcar 9 Escanteios" (Japão v Suécia) saiu da extração como `Suécia [Japão v Suécia]` — idêntico a um ML, perdeu o "9 escanteios". O mercado é o que chamamos de **Race** (corrida).
  - **Causa raiz:** "Race / Primeiro a marcar X" é uma **terceira estrutura de mercado** que não existia. `MASTER_DESCRICAO §10` só conhecia Contínuo (`Over/Under X.5`) e Discreto (`X+`); sem template, a extração descartava o alvo. Não há sinônimo nem regra em `MASTER_APOSTAS`.
  - **Decisão:** Race é **tipo de mercado**, não categoria. Categoria segue o objeto (§1): escanteios → `Escanteios`, gols → `Gols`, etc. Nenhuma categoria nova criada (segue 27).
  - **Fix global (descrição vem das regras globais — sem edição de casa, decisão do Feca):**
    - `MASTER_DESCRICAO §10.3` — nova estrutura `Race N - Entidade [Confronto]` (ex.: `Race 9 - Suécia [Japão v Suécia]`).
    - `MASTER_APOSTAS §1` — exemplo `Primeiro a marcar 9 escanteios → Escanteios`.
    - `MASTER_APOSTAS §4` — sinônimos de Escanteios (`Primeiro a marcar X escanteios`, `Race to X corners`, `Corrida de escanteios`).
    - `MASTER_APOSTAS §5` — nova regra "Race (Primeiro a marcar X)" com tabela objeto→categoria.
  - **Linha correta:** `Futebol  Bet365  Escanteios  Race 9 - Suécia [Japão v Suécia]  99,00  3,40  L`.
  - Auditoria: `python tools/audit_casas.py` → 11 OK, 0 FAIL. Backup: `Backups/cadastro-mercado-race-escanteios/`. Commit: (este).

- **Sessão 52 (26/06/2026) — Tênis ITF classificado errado como Dardos:**
  - **Sintoma (Feca):** `Sebastian Sorger [Sebastian Sorger v Khumoyun Sultanov]` saiu como **Dardos**; o correto é **Tênis** (M25 Zagreb, circuito ITF/Challenger — confirmado: Sultanov é nº 2 da Uzbequistão, jogou Davis Cup).
  - **Verificação de contradição:** o usuário trouxe também `Fallon Sherrock v Scott Mitchell` como suposto tênis mal classificado, mas a verificação web mostrou que é **genuinamente Dardos** (PDC UK Q-School; Sherrock é PDC, Mitchell campeão BDO 2015). Esse bilhete estava **correto** — não foi tocado, para não quebrar bilhetes reais de dardos da Sherrock/Mitchell.
  - **Causa raiz:** a regra de desempate (§568) já manda "atleta desconhecido + sem sinal de dardos → Tênis, nunca Dardos", mas o modelo usou "conhecimento próprio" (§5 item 4, prioridade sobre o desempate) e chutou Dardos para os nomes Sorger/Sultanov.
  - **Fix (`global/MASTER_ESPORTES_2026.md` §388, bloco ATP Challenger / ITF):** adicionados `Sebastian Sorger` e `Khumoyun Sultanov` à lista auxiliar de Tênis → prioridade explícita (§561 item 4). Correção cirúrgica, mesmo padrão de "exemplos de sessões recentes".
  - Backup: `Backups/s52-esportes-sorger-sultanov/`. Commit: (este).

- **Sessão 51 (26/06/2026) — Lote inteiro perdido por bilhete duplicado (Betnacional):**
  - **Sintoma (Feca):** reprocesso do histórico da Betnacional retornou `0 exportadas`. A análise mostrou `UniqueViolationError: ... bilhetes_dono_casa_parceiro_assinatura_key already exists`.
  - **Causa raiz:** Betnacional não mostra ID no print, então a assinatura vem do conteúdo. O histórico já tinha sido salvo antes. No `upsert_bilhetes`, um bilhete colidiu com a linha existente, o `UniqueViolationError` escapou do `ON CONFLICT` (corrida entre dois `/salvar` do mesmo lote), subiu e abortou a função inteira. Os 34 outros bilhetes se perderam.
  - **Fix (`app/repository.py`):** gravação resiliente por linha. A colisão agora cai num `UPDATE` explícito (o mesmo que o `ON CONFLICT` faria), conta como atualizada e o loop segue. Um bilhete duplicado nunca mais derruba o lote.
  - **Commit:** `a7535bb`. Inclui edições pendentes de docs/casas que estavam no working tree.
  - **Pendente:** nenhum. Próximo passo: na próxima reprocessada da Betnacional, confirmar que os repetidos aparecem como `atualizado(s)`.

- **Sessão 50 (25/06/2026) — Bug de odd corrompida (ponto → milhar na planilha):**
  - **Sintoma (Feca):** extração da Betano gerou odds absurdas — `7.526.066.666.666.660,00`, `8.580.978,00`, `306.035.275,00`, `12.767.283.900,00`, `10.5777`.
  - **Causa raiz:** a IA emitiu odds **calculadas** (W = `RO ÷ Stake`; L múltipla = **produto das pernas**, pois a Betano não exibe odd combinada) com **ponto** decimal e precisão longa. O Google Sheets em locale pt-BR lê o ponto como **separador de milhar** → `8.580978` vira `8.580.978,00`. O `12,07` escapou por dar 2 casas exatas.
  - **Fix (sem arredondar — precisão é inquebrável):** reforçado em 4 pontos que odd usa **SEMPRE vírgula, JAMAIS ponto**, e que todo cálculo (÷ ou ×) sai com ponto e precisa ser convertido antes de escrever, preservando precisão total:
    - `app/main.py` (prompt vivo): nova seção ODD com SEPARADOR DECIMAL + PRECISÃO inquebráveis; resolvida a contradição "L → nunca calcule o produto" (errada p/ Betano, que não exibe odd combinada).
    - `MASTER_OUTPUT_2026 §12.1` (separador) + `§12.2` (precisão), novos.
    - `MASTER_RESULTADO_2026 §5.2.1` (divisão) e `§7.2` (produto): nota vírgula-nunca-ponto.
    - `CASA_BETANO §11`: nota vírgula + precisão.
  - **Valores corrigidos das 5 células:** `75,26066666666666` · `8,580978` · `30,6035275` · `10,5777` · `127,672839`. Backup: `Backups/sessao50-regra-virgula-odd/`.

- **Sessão 49 (24/06/2026) — Refactor "camada fina" + 3 skills (dívida de duplicação casa × global):**
  - **Motivação (Feca):** os arquivos de casa estavam **copiando** conteúdo global (tabela das 27 categorias no §9, validações transversais no §14) → risco de drift/bug quando o global muda. Auditoria confirmou **151 linhas `aguarda amostra`** + bloco "Transversais" duplicado em 6 casas.
  - **Padrão "camada fina" (commit `34dac4a`):** `CASA_MODELO §9` proíbe reescrever as 27 categorias / linhas "aguarda amostra" (só mercados confirmados); `CASA_MODELO §14` transversais viram ponteiro p/ `MASTER_PIPELINE §8` + `MASTER_OUTPUT §17–§18`; `GUIA_NOVA_CASA` (formato §9 enxuto, 4 pontos); `CLAUDE.md` regra de propagação encolhida para "só casas afetadas" (grep-driven). **Nenhum master global precisou mudar** — as transversais já viviam no pipeline.
  - **Emagrecimento das 6 casas novas (commit `8202cde`, −149 linhas):** removidas 119 linhas placeholder do §9 + bloco transversal → ponteiro no §14, via scripts (`scratchpad/slim_s9.py`, `slim_s14.py`). Nuances específicas preservadas (KTO "Recusado", Jogo de Ouro/Lottu "Aberto"). As 5 casas antigas (Bet365/Betano/Betfair/Pinnacle/Superbet) já eram enxutas no §9; resíduo transversal menor no §14 fica como WARN (limpeza opcional). Backup: `Backups/pre_camada_fina_2026-06-24/`.
  - **3 skills + checker (commit `b84159a`):** `tools/audit_casas.py` — auditoria determinística casa × global (categoria órfã no §9, placeholder `aguarda amostra`, bloco transversal cru, registro em main.py/index.html); **11/11 casas OK, exit 0**. Skills em `.claude/commands/`: `/audit-casas` (roda o checker + spot-check de goldens), `/nova-casa` (cadastro guiado camada fina, com o audit como gate), `/propagar-categoria` (checklist de propagação grep-driven). `.gitignore` ignora `.claude/settings.local.json`.
  - **Limpeza do §14 das 5 casas antigas (commit `f0b05a6`):** removidos os bullets puramente transversais (odd em L/HL/V, liga ≠ esporte, nº de linhas, Assistência só Futebol, data de múltipla) que duplicavam o global; adicionado o ponteiro padrão; preservadas as validações específicas de cada casa. Backup: `Backups/pre_limpeza_s14_antigas_2026-06-24/`. **`/audit-casas` final: 11/11 OK, exit 0, sem FAIL.**

- **Sessão 49 (24/06/2026) — Nova casa: KTO:**
  - **`casas/CASA_KTO.md` criada** (15 seções, 8 goldens reais; lote 31/03–24/06/2026). Modo de ingestão: screenshot/visão "Minhas Apostas" (texto colado como fallback).
  - **Decisão do dono:** a KTO exibe uma **única odd total por cupom** (trata até dupla como simples) → cada cupom = **uma linha**; usar a odd de visualização; se `Ganha`, `Odd = Pagamento ÷ Stake`.
  - **Particularidades:** locale pt-BR na UI mas **dinheiro/odds em en-US (ponto decimal)** → converter p/ vírgula; ID visível `ID do Cupom:` (11 dígitos) → `Código`/dedup; `Recusado` = cupom ignorado por completo; `Aberta` → `extraction_state=aberta`; boost `ODDÃO+` (odd riscada = ruído, usar a final); `Pagamento` = retorno real (só em `Ganha`), `Ganho potencial` nunca usado p/ odd.
  - **Categorias confirmadas (§9):** ML (`Vencedor da partida`), Cartões (`Para receber um cartão`, mesmo individual — §1 APOSTAS), Anytime (`Para marcar` em single), Player Props (`Faltas concedidas pelo jogador`), Múltipla (`Dupla`/`Quadrupla`/`Simples (N)`/sistema), Outras (`vence e ambos marcam` = combo result+BTTS). Dardos confirmado p/ `Vencedor da partida` entre indivíduos (Steve West/William Borland/Simon Stevenson, PDC).
  - **Goldens:** G1/G2 Quadruplas L (95,00 / 76,00, cartões); G3 ML L Dardos (1,80); G4 ML W Dardos (2,43 = 607,50÷250 ✓); G5/G6 Duplas L scorer (85,50 / 40,80); G7 Aberta Outras boost (4,50); G8 Aberta Player Props faltas (4,20). Cupom `Recusado` ID 12807217380 excluído de propósito.
  - **Pendências documentadas:** §5 V/HW/HL, §7 cashout, §8 bônus (aguardam amostra). §Feedback: combo "Resultado+Ambas Marcam" sem categoria própria; `Simples (N)` sem odd/resultado por perna no view de lista (limitação); categoria `Faltas` candidata.
  - **`app/main.py`:** `KTO: 'KTO'` adicionado ao `_CASA_DISPLAY` (ordem alfabética). **`app/static/index.html`:** `KTO` em `NOMES` e `DOMINIOS` (favicon `kto.bet.br`).
  - Backup: `Backups/pre_kto_2026-06-24/`. Commit: `377833a`.

- **Sessão 48 (24/06/2026) — Badge de pendências: refresh faltante no "Desfazer":** o recurso de badge azul de pendências (bolinha FDC `--accent #2E8BFF` com nº de bilhetes não copiados, por parceiro e por casa) foi implementado e commitado junto do commit `34f09e9` (`contar_pendentes` em `repository.py`, `GET /pendentes` em `main.py`, `.pend-badge` + `atualizarPendentes()`/`aplicarBadgesPendentes()` em `index.html`; refresh em load, pós-salvar, copiar/desmarcar/marcar/toggle, deletar individual e seleção).
  - **Gap corrigido nesta sessão (`app/static/index.html`):** o handler do botão **"Desfazer"** (apaga os bilhetes da última análise) não chamava `atualizarPendentes()` — a contagem ficava obsoleta até a próxima ação. Adicionado o refresh, alinhando com os demais handlers.
  - **Limitação:** verificação manual local é difícil (cookie `secure=True` não persiste em http://localhost — caveat sessão 44); validar na URL Railway após deploy.

- **Sessão 47 (24/06/2026) — Fix Tênis vs Padel (Betnacional classificava tênis como Padel):** o Feca reportou dois jogos de tênis da Betnacional rotulados como `Padel` (Máximo González/Santiago González v Burruchaga/Tirante; Johannus Monday v Braden Shick — todos tenistas). Já corrigidos na planilha; pedido = evoluir o sistema.
  - **Causa raiz dupla:** (1) `Padel` nunca existiu na lista canônica do `MASTER_ESPORTES` (modelo inventou, violando §1) e não havia regra de desambiguação Tênis vs Padel; (2) um exemplo golden em `CASA_BETNACIONAL.md` (§15, G1) estava rotulado **errado** como `Padel` para uma dupla de tenistas (Stricker/Hunziker v Wessels/Wehnelt) — ensinava o modelo a chamar duplas de tênis de Padel.
  - **Correção (sem tocar em código):** decisão do Feca = Padel nunca é válido, duplas/individuais sem sinal de outro esporte → **Tênis**.
    - `casas/CASA_BETNACIONAL.md` G1: `Padel` → `Tênis` + nota de verificação.
    - `global/MASTER_ESPORTES_2026.md`: nova "Regra Crítica — Tênis vs Padel" (Padel proibido; notação de duplas `X/Y v W/Z` = Tênis; lista de atletas-referência) + item 12 na validação §9.
  - Backup: `Backups/sessao45-fix-tenis-padel/`.

- **Sessão 46 (24/06/2026) — Betnacional: dedup por timestamp (fim das duplicatas):** o Feca reportou que a Betnacional registrava o mesmo bilhete várias vezes (ex.: "Espanha 2+ gols 2ºT" gravado 3×, com categorias diferentes Team Props/Gols). Causa: a Betnacional não tem ID impresso, então a dedup caía na descrição — que a IA reescreve a cada rodada ("[Argentina v Áustria]" ↔ "[Argentina v ?]") → cada variação virava INSERT em vez de UPSERT.
  - **Correção (`casas/CASA_BETNACIONAL.md`, sem tocar em código):** a Betnacional exibe o **horário de colocação** (`às HH:MM`) em todo bilhete — identificador estável entre reprocessamentos. Agora o extrator sintetiza a 11ª coluna `Código` = `BN-DD/MM/AAAA-HH:MM-<odd exibida>`. A dedup chaveia por esse `Código` (mecanismo de ID já existente em `repository.py`) → reprocessar o mesmo bilhete vira UPSERT limpo.
  - **§3** reescrita (Código sintético obrigatório, odd exibida nunca calculada, nota de colisão mesmo-minuto+mesma-odd); **§4** ajustada (horário não é mais descartado por completo — vai para o Código); **§13** ganhou pegadinha; **7 goldens (§15)** atualizados com a coluna Código.
  - **Limitação:** as duplicatas já gravadas antes desta correção não somem sozinhas — deletar pelo botão da grade. A correção previne as futuras. Backup: `Backups/sessao45-betnacional-dedup-timestamp/`.

- **Sessão 45 (23/06/2026) — Retry com backoff para sobrecarga da API:** o Diogo recebeu `overloaded_error` (HTTP 529 da Anthropic) durante teste. Não era bug do login — é pico de capacidade da API, e o app não tinha retry.
  - **`app/main.py`:** helper `_is_retryable()` (cobre 429/500/502/503/529 e tipos `overloaded_error`/`rate_limit_error`/`api_error`) + retry com backoff exponencial (1s, 2s, 4s, 8s; `_RETRY_MAX=4`) nos dois pontos de chamada ao modelo.
    - **Sequencial:** retry interno no task `_call`, só enquanto nenhum token foi emitido (evita duplicar saída).
    - **Paralelo:** retry por tentativa em buffer local `attempt_text`; comita em `accumulated` só no sucesso.
  - Picos da Anthropic agora são absorvidos de forma transparente. Backup: `Backups/pre_retry_backoff_2026-06-23/main.py`.

- **Sessão 44 (23/06/2026) — Login multiusuário + isolamento por dono:** o app ganhou autenticação para um amigo (Diogo) testar sem misturar dados com os do dono do projeto (Feca).
  - **`app/auth.py` (novo):** login por cookie assinado (HMAC, stdlib — zero dependência nova). `USUARIOS` = dict usuário→hash SHA-256 (`Feca`, `Diogo`), sobrescrevível por env `SENHA_<USER>_HASH` e `SESSION_SECRET`. Cookie `httponly`, `samesite=lax`, `secure=True` (válido sob HTTPS do Railway). Dependency `usuario_atual` exige sessão; senão 401.
  - **`app/database.py`:** coluna `dono TEXT NOT NULL DEFAULT 'Feca'` em `bilhetes` e `parceiros` (migração idempotente; registros antigos viram do Feca). Constraints `UNIQUE` trocadas para `(dono, casa, parceiro, assinatura)` e `(dono, casa, nome)` via bloco `DO` idempotente — cada usuário tem seu próprio espaço.
  - **`app/repository.py`:** `dono` propagado a TODAS as funções. Operações por `id` (deletar/editar/marcar/arquivar) filtram também por `dono` — um usuário nunca toca bilhete/parceiro de outro nem por ID forjado. Dedup por código (`get_codigos_*`) é por dono.
  - **`app/main.py`:** rotas `/login` (GET tela + POST autentica), `/logout`, `/me`; `/` redireciona p/ `/login` sem sessão; **todas** as rotas de dados protegidas com `Depends(usuario_atual)` e `dono` injetado nas chamadas do repositório.
  - **`app/static/login.html` (novo):** tela de login on-brand (tokens.css + logo FDC).
  - **`app/static/index.html`:** cabeçalho na sidebar com nome do usuário logado + botão "Sair"; interceptor global de `fetch` redireciona p/ `/login` em 401 (sessão expirada).
  - **Credenciais:** Feca (dono, dados existentes) e Diogo (teste). Senhas em hash no código; recomendado mover p/ env no Railway depois.
  - **Caveat local:** cookie `secure=True` só trafega em HTTPS — login local em `http://localhost` não persiste; testar na URL Railway (HTTPS).
  - Backup: `Backups/pre_multiusuario_2026-06-23/`.

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

- **Sessão 23 — Upload CSV/XLS + dedup pré-extração + labels Props (15/06/2026):**
  - Upload de `.csv` habilitado: JS lê como texto, envia via `csv_content`; frontend exibe card 📄.
  - Upload de `.xls/.xlsx` habilitado: backend lê com `xlrd`, formata cada aposta em texto estruturado, envia via `xls_file`. Frontend exibe card 📊.
  - `_xls_sel_labels()`: detecta tipo de aposta pelo padrão `-vs-` e aplica labels corretos por estrutura (padrão / Player Props / Team Props). Antes, "Jogador" ficava rotulado como "Confronto" em bets de Props.
  - `_parse_xls()` (async): filtra IDs já no banco via `get_codigos_existentes()` antes de chamar o Claude. Inverte ordem das linhas (mais antiga primeiro, conforme `CASA_PINNACLE §2.1`). Caso 100% ignorado retorna SSE sem custo de tokens.
  - `repository.py`: `get_codigos_existentes()` adicionada.
  - `requirements.txt`: `xlrd>=2.0.1`.
  - Frontend: status exibe "N já salva(s) ignorada(s)"; guarda contra divisão por zero no % cache.
  - Bug reportado (pendente): Betfair ML Dardos `Oliver Mitchell [Steve Johnstone v Oliver Mitchell]` classificado como Futebol. Causa: nenhum dos dois está na lista de referência do `MASTER_ESPORTES_2026`. Fix proposto: adicionar ambos à lista. Aguardava confirmação quando sessão encerrou.
  - Commits: `f30a3cc`, `3a6ca8f`, `6c1ca61`, `68856fd`.

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
4. **Outras casas:** ~~Bet365~~ · ~~Betfair~~ · ~~Betano~~ · ~~KingPanda~~ — todas adicionadas. Pendências de amostra (aguardam bilhete real):
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

**Sessão 30 (20/06/2026) — Auditoria de performance (Opus) + paralelismo de chunks:**

- **Auditoria com agente Opus:** identificou 7 oportunidades de performance. Ranking executado: UptimeRobot descartado (Railway Serverless OFF; o evento de 12 min foi tempo de processamento, nao cold start — registrado em `PLANO_CONSTRUCAO.md §10`).
- **Cache warming (commit `36d185a`):** `main.py` — background task `_cache_warmer()` pinga a cada 4 min para manter TTL de 5 min do cache Anthropic vivo.
- **In-memory cache com mtime (commit `b48701b`):** `prompts.py` — `_file_cache` armazena `(conteudo, mtime)`; relê o arquivo só se o mtime mudar. `reload_masters()` para invalidacao forcada.
- **Logs de tempo (commit `b48701b`):** `main.py` — `logging.basicConfig` + logs `extrair inicio`, `seq chunk N`, `seq total`, `par chunk N/M`, `par total` com duracao e tokens. Confirma causa real no proximo evento.
- **Sonnet 4.5 no dropdown (commit `36d185a`):** `config.py` + `index.html` — opcao "Sonnet 4.5 · mais rapido" disponivel para teste. Padrao continua Sonnet 4.6.
- **Paralelismo de chunks (commit `9f630a4`):** `main.py` — `_build_chunks()` divide imagens em grupos de `ceil(N/4)` ou texto por paragrafos/blocos XLS. `_stream_parallel()` roda N chamadas async com `asyncio.Semaphore(4)`, reassembla por indice, combina TSV, trata erro por chunk sem derrubar a request. Frontend: evento `chunk_progress` mostra "chunk N/M" no card.
  - Ganho esperado: 12 imgs → ~4 chunks paralelos → tempo cai ~4x. 40 bets Betano texto → 4 chunks → ~1,5 min vs ~6 min sequencial.
- **Auditoria de consistencia 10 vs 11 colunas (commit `801e983`):** pipeline confirmado consistente. `MASTER_OUTPUT_2026.md §2, §17, §18` — excecao documentada para coluna `Codigo` (11a coluna interna de dedup, nao vai para planilha do usuario).

**Proximos passos imediatos:**
- **Testar paralelismo em producao:** submeter lote de 8+ imagens e confirmar que chunks coexistem, grade sai em ordem correta, dedup funciona.
- **Avaliar Sonnet 4.5:** testar mesmo lote com Sonnet 4.5 e Sonnet 4.6 e comparar qualidade linha a linha.
- ~~Adicionar `Steve Johnstone` e `Oliver Mitchell` a lista de Dardos em `MASTER_ESPORTES_2026.md`~~ — **feito** (commit `8bd99d6`).
- ~~Limpar duplicatas no banco~~ — **cancelado** (sessao 30): duplicatas pontuais sao tratadas individualmente quando surgem; nao ha limpeza retroativa em batch.

**Sessão 33 (20/06/2026) — KingPanda consolidado + GUIA_NOVA_CASA:**

- **KingPanda §4 (data):** tabela explícita evento vs colocação; regra: `Compartilhar` = delimitador; data após "Compartilhar" + antes de "ID:" = colocação (ignorar).
- **KingPanda §9:** expandido para todas as 27 categorias do `MASTER_APOSTAS_2026 §3`. Colunas reordenadas para padrão do template: `KingPanda exibe | Aposta global | Status`.
- **KingPanda §2.3 (ordem de output):** REGRA DEFINITIVA documentada — grid exibe esquerda→direita, cima→baixo; TSV sai na ordem inversa. Exemplo: Florian Wirtz (pos 1 no texto) = ultima linha TSV; Paises Baixos Resultado 1ºT (pos 8) = primeira linha.
- **KingPanda §13/§14:** pegadinhas e validacoes atualizadas com regra de ordem e ID ausente no ultimo bilhete (normal).
- **KingPanda §15:** 8 goldens reordenados em ordem de output (G1 = primeira linha TSV = pos 8 no texto). +3 novos goldens de Alemanha vs Costa do Marfim: Dupla Chance, Escanteios, Ambas Marcam, Resultado 2ºT, Team Props confirmados.
- **`GUIA_NOVA_CASA.md` criado:** 6 etapas + checklist + referencia de padroes para cadastrar qualquer casa nova.
- Backups: `Backups/pre_kingpanda_v2_2026-06-20/`. Commits: `051ae9b`, `2535a2f`, `b4e8a0f`, `9360882`.

**Proximo passo: cadastrar novas casas usando `GUIA_NOVA_CASA.md`.**

**Sessão 34 (20/06/2026) — Fix scroll overlap + normalização de odd:**

- **Contexto herdado:** sessão anterior aplicou detecção de sobreposição de scroll (badge azul) e correção de ordem cronológica (chunks paralelos). O badge não aparecia.
- **Root cause:** `_scroll_key` em `_combine_parallel_results` (`main.py`) comparava a odd como string bruta. Chunks paralelos podem calcular a mesma odd de formas diferentes: um lê `"1,83"` do cabeçalho do bilhete; outro calcula `RO ÷ Stake = "1,8331168..."`. Strings diferentes = chave diferente = overlap não detectado.
- **Fix 1 — `main.py` `_scroll_key`:** odd normalizada para 2 casas decimais antes da comparação de chave. `"1,83"` e `"1,8331..."` viram `1.83` e batem. Commit `b3afde3`.
- **Fix 2 — `CASA_BET365.md`, `CASA_BETANO.md`, `CASA_SUPERBET.md` §11:** aviso explícito adicionado logo abaixo da regra W: "a odd exibida no cabeçalho é decorativa para W — ignorar; calcular sempre com RO real." Commit `7e1321c`.
- **Fix 3 — `repository.py` `_assinatura`:** odd normalizada para 2dp antes de gerar o hash (`_norm_odd`). Previne duplicatas silenciosas no banco quando o AI produz precisões diferentes em sessões distintas (ex.: re-upload da mesma aposta). Commit `7e1321c`.
- **Fix 4 — `index.html`:** coluna de badge (duplicata/scroll) movida do final da grade para ao lado da coluna Esporte. Commit `ca7e5fb`.
- Casas afetadas pelos fixes de odd: Bet365, Betano, Superbet (têm boost; odd exibida pode diferir do calculado). Pinnacle, Betfair e KingPanda não afetadas (odd exibida = autoritativa ou = calculado).

**Sessão 32 (20/06/2026) — Nova casa: KingPanda:**

- **`casas/CASA_KINGPANDA.md` criada** — 15 seções, 5 goldens reais (Países Baixos vs Suécia, 20/06/2026).
- **Modo de ingestão:** texto colado (primário) + screenshot (fallback).
- **ID:** visível, numérico longo (18–19 dígitos), ex.: `856196311719649280`.
- **Boost:** formato `[odd original] >> [odd final]` (texto: duas linhas consecutivas); usar sempre a segunda = `Total de Odds`.
- **Ganho Potencial:** retorno bruto (stake × odd); locale en-US (ponto decimal) → converter para vírgula.
- **Criador de apostas** = Bet Builder → `Múltipla`.
- **Pendências documentadas:** rótulos V/HW/HL, cashout, bônus. Categoria `Resultado Correto` ausente do `MASTER_APOSTAS_2026` → flagged no §Feedback como proposta.
- **`app/main.py`:** `KINGPANDA: 'KingPanda'` adicionado ao `_CASA_DISPLAY`.
- **`app/static/index.html`:** `KingPanda` adicionado a `NOMES` e `DOMINIOS` (favicon via `kingpanda.bet.br`).
- Backup: `Backups/pre_kingpanda_2026-06-20/`. Commit: `ed60f15`.

**Sessão 31 (20/06/2026) — Arquivamento automático de apostas antigas:**

- **Feature:** após cada `/salvar`, o sistema arquiva automaticamente as apostas antigas de cada parceiro, mantendo visíveis apenas `max(tamanho_do_lote, 40)` apostas mais recentes.
- **Regra:** apostas arquivadas (`archived=TRUE`) permanecem no banco e são acessíveis — nunca deletadas. A grade oculta arquivadas por padrão.
- **UI:** chip "⊞ N arquivados" aparece na stats bar quando há arquivadas; clique alterna para mostrar tudo (arquivadas com estilo esmaecido `row-arc`); "Copiar pendentes" e "Baixar TSV" operam apenas sobre apostas ativas.
- **Arquivos alterados:**
  - `database.py`: coluna `archived BOOLEAN NOT NULL DEFAULT FALSE` + migração `ALTER TABLE IF NOT EXISTS`.
  - `repository.py`: `auto_arquivar()`, `contar_arquivados()`, `list_bilhetes()` com parâmetro `archived`.
  - `main.py`: `/salvar` chama `auto_arquivar` e retorna `arquivados`; `/bilhetes` aceita `?archived=false|true|all`.
  - `index.html`: chip toggle, estilo `.row-arc`, filtros de cópia/download excluem arquivadas.
- Backup: `Backups/pre_arquivamento_auto_2026-06-20/`. Commit: `7e4b76a`.

**Sessão 29 (20/06/2026) — Bugs CASA_BETANO + UI multi-cards:**

- **Auditoria de performance (investigado, sem fix estrutural possivel):**
  - Evento: 40+ bets Betano em texto levou 12 min. GPT-4o fez o mesmo em 27s. Claude Web (Opus 4.8) fez em menos de 3 min.
  - Causa raiz do evento de 12 min: Railway pod frio + lentidao pontual da API Anthropic simultaneos. Nao e o comportamento normal.
  - Expectativa realista com arquitetura atual: **3–6 min (cache frio) / 1–2 min (cache quente)**. Cache TTL = 5 min; reinicio de pod zera o cache.
  - `max_tokens=64000` NAO e o gargalo — e um teto, o modelo para quando termina. Nao reduzir (foi aumentado para resolver leitura incompleta de imagens).
  - Gap vs GPT-4o e estrutural: GPT-4o e intrinsecamente mais rapido, sem overhead de Railway, sem TTL de cache. Fechar esse gap exigiria trocar de provider — nao planejado.
  - **O que melhora o UX sem trocar provider:** multi-cards (implementado nesta sessao) — o usuario nao fica bloqueado enquanto espera.
  - **Proxima alavanca possivel de velocidade:** Sonnet 4.5 (mais rapido que 4.6; nao testado ainda em extracao de bets) — avaliar em sessao futura.

- **Auditoria de qualidade Betano:** comparação do output do sistema vs GPT-4o em 40+ bets reais (15/06–20/06). Sistema acertou mais que o GPT-com-masters: GPT perdeu 1 bet inteiro (Lyndon Dykes), classificou tripla multi-esporte como "Baseball" e usou nomes errados em Player Props. Sistema tinha apenas 2 bugs reais — ambos corrigidos.
- **Bug 1 — REKONIX duplicado:** texto copiado de bilhete simples Betano repete a seleção duas vezes (linha-resumo antes do `sport-icon` + linha-detalhe com odd/mercado/confronto). O modelo interpretava como 2 bilhetes. **Fix:** `CASA_BETANO.md §12` — regra "Seleção repetida em bilhetes simples = 1 bilhete" adicionada com exemplo concreto.
- **Bug 2 — 180s Dardos → Outras:** mercados `Total de 180s` / `Mais/Menos 180s` / `H2H 180s` caíam em `Outras` mesmo com a categoria `Legs` já definida no MASTER_APOSTAS. **Fix:** `CASA_BETANO.md §9` — mapeamento explícito `Total de 180s / Mais/Menos 180s / H2H 180s (Dardos) → Legs` adicionado à tabela.
- Backup: `Backups/CASA_BETANO_pre_sessao29/`. Commit: `e755045`.
- **Feature — UI multi-cards de extração paralela:** `app/static/index.html` — clicar em "Processar Bilhetes" cria um card independente no painel direito, limpa o formulário imediatamente e re-habilita o botão. Múltiplos cards processam em paralelo (backend já suportava; zero mudança em main.py). Cada card: header (casa·parceiro·horário·tokens+%cache), contador `Processando… (Xs · N chars)`, botão ✕ individual para cancelar, status final colorido (`✓ N novo(s)`, `⚠️`, `✗`). Troca de parceiro limpa o painel; "Limpar" só limpa o formulário. `_abortCtrl` → `_activeStreams Map`. Backup: `Backups/pre-multi-cards-sessao29.html`. Commit: `6795b63`.

**Estado após sessão 28 (cont. 20/06/2026):** MASTER_ESPORTES_2026.md — 3 melhorias de identificação de esporte:
- §5 nova regra (item 4): modelo deve usar **conhecimento próprio de treinamento** quando atleta não estiver nas listas auxiliares — só usar `Outro` quando genuinamente incerto após esgotar esse recurso.
- §7 Tênis: sinônimos ITF/Challenger adicionados; sublistas `ATP Challenger / ITF` e `WTA / ITF` com jogadores identificados nesta sessão (Keshav Chopra, Kerem Yilmaz, Mate Valkusz, Pietro Orlando Fellin, Mickael Kaouk, Filiberto Fumagalli, Vignesh Gogineni, Bryce Nakashima, Tanguy Genier, Noah Karma, Gaeul Jang, Aishi Das, Marie Vogt, Mia Slama, Elsa Bonelli, Emily Seibold).
- §7 Dardos: sinônimos MODUS/MODUS Super Series adicionados; sublista `MODUS Super Series` com Dylan Slevin, Sam Spivey.
- Backup: `MASTER_ESPORTES_2026_pre-sessao28.md`.

**Convencao de terminal (registrada em 20/06/2026):** PowerShell 5.1 ConstrainedLanguage. Proibido heredoc bash, New-Object .NET, Out-File -Encoding utf8 (gera BOM). Commits multilinha: multiplos `-m`. Regra documentada em `FDC Capital/CLAUDE.md` (fora do repo, sem versionamento git).

**Próximo passo imediato (ver sessão 30 acima).**

**Sessão 27 (17/06/2026):**
- **Contexto:** extração Betfair com bets já processadas gerava confusão — contador dizia "25 salvos" sem distinguir updates de inserts; regra de ordenação §2 usava "texto colado" como referência, ambígua quando havia imagens + CSV.
- **Fix insert vs update:** `app/repository.py` — `upsert_bilhetes` usa `xmax = 0` para detectar INSERT real; retorna `(inseridos, atualizados, ids, alertas)`. `app/main.py` — `/salvar` retorna `inseridos`/`atualizados` separados. `app/static/index.html` — status bar mostra `"X novo(s) · Y atualizado(s)"`.
- **Fix ordenação Betfair:** `casas/CASA_BETFAIR.md §2` — regra reescrita com tabela explícita: Fonte A (prints/imagens) é a autoridade de ordem; CSV apenas para join de data, nunca reordena.
- Commit: `2d98ca1`.

**Sessão 28 (17/06/2026):**
- **Bug:** re-upload de XLS Pinnacle gerava duplicatas — bets já copiadas voltavam como pendentes sem tick.
- **Root cause:** `upsert_bilhetes()` deduplicava só por `assinatura` (SHA-256). Bets importadas sem código (via imagem ou extração anterior sem 11ª coluna) têm hash baseado em conteúdo. Nova extração via XLS gera hash baseado em ID → assinaturas diferentes → INSERT em vez de UPSERT → linha duplicada com `copy_state='pendente'`.
- **Fix:** duas migrações antes do INSERT em `upsert_bilhetes()`:
  - Migração A: se linha existente tem mesmo `codigo_bilhete` mas assinatura diferente → atualiza assinatura (normaliza formato antigo).
  - Migração B: se linha existente tem `codigo_bilhete IS NULL` e bate em `data+aposta+stake+odd` → adopta: atribui assinatura e código à linha existente.
- **Também:** `DO UPDATE SET` agora propaga `codigo_bilhete` via `COALESCE` se a linha existente não tinha código.
- Backup: `Backups/repository_pre_dedup_fix_2026-06-17.py`.
- Commit: (este).

**Sessão 26 (17/06/2026):**
- **Notas Críticas full-height:** `app/static/index.html` — `.analysis-box` `flex-shrink:0` → `flex:1`; `.box-body` `max-height:220px` removido, `flex:1` adicionado. Painel de análise agora é totalmente ocupado pelas notas. Commits `801c9e0`.
- **Fix esporte Dardos:** `global/MASTER_ESPORTES_2026.md` — `Bradley O'Connor` e `Nico Plovier` adicionados à lista de referência de jogadores de Dardos. Sem esses nomes, o modelo inferia Golf pelo sobrenome irlandês. Commit `f253a5e`.

**Sessão 25 (16/06/2026):**
- **Fix keepalive SSE:** chamada Anthropic migrada para `asyncio.Task` paralela. Loop aguarda itens da fila com timeout de 20s; ao expirar emite comentário SSE `": keepalive"` para manter conexão viva no Railway enquanto o modelo processa. Elimina erro "Resposta incompleta — sem evento 'done'". Commit `5eda00f`.
- **Remoção do Haiku:** removido de `ALLOWED_MODELS` em `config.py`, do dropdown em `index.html` e da validação de imagem em `main.py`. Dropdown agora só tem Sonnet 4.6 (padrão) e Opus 4.8. Commit `d08ec96`.
- **Output enxuto:** `_INSTRUCAO` reescrita — removidas seções `## Confiança` (por linha) e `## Recomendações`. Mantida apenas `## Notas Críticas` (máx 5 itens, "Nenhuma" se não houver). Frontend: boxes de confiança e recomendações removidas; painel direito mostra só Notas Críticas. Redução estimada de 50-60% nos tokens de saída. Commit `0a07baa`.
- **Sidebar expandida:** largura `216px → 292px` (+35%), padding `10 → 14px`. Logo escala junto (usa `width:100%`). Todas as casas carregam abertas por padrão (toggle ainda funciona). Commit `8ef221e`.

**Sessão 24 (15/06/2026):**
- **Continuation automática:** `max_tokens=64000`; quando `stop_reason == "max_tokens"` o backend reinicia com o texto acumulado como turno do assistente — o modelo continua sem regeração. Frontend exibe "Continuando… parte N".
- **Botão Cancelar:** AbortController no frontend; aparece durante processamento; `AbortError` exibe "Análise cancelada." em amarelo.
- **Fix SUBSTITUIÇÃO+:** `CASA_BET365 §12` reforçado com bloco visual explícito (▲=substituto IGNORAR / ▼=original USAR) e dois avisos ⚠️. Golden #9 adicionado (Bruno Guimarães vs Danilo dos Santos).
- **H2H 180's Dardos:** novo mercado documentado em: `MASTER_APOSTAS §4` (sinônimos), `§5` (regra H2H), `§6 Dardos` (distinção Player Props individual vs H2H comparativo), `§7` (prioridade), `§9` (validação #17). `MASTER_DESCRICAO §13.2` (template + nota de reconstrução de confronto). `CASA_BET365 §9` (mapeamento + nota de layout). `CASA_BETFAIR §9` (nota de layout adicionada ao mapeamento existente).

- **Sessão 35 (21/06/2026) — Fixes de streaming, estado do extrator e ordem Pinnacle:**
  - `app/main.py` — `_stream_parallel`: `asyncio.wait_for(timeout=20)` + keepalive a cada 20s para evitar timeout do proxy Railway durante espera de chunks. Adicionado try/except em torno de `_combine_parallel_results`.
  - `app/main.py` — `_build_chunks`: se "DADOS CSV:" estiver no texto, retorna modo sequencial (CSV+texto Betfair precisam ficar juntos para o join).
  - `app/main.py` — `_stream_parallel`: sort dos chunks agora é `reverse=False` para modo texto/XLS (Pinnacle oldest-first) e `reverse=True` para imagens. Corrige ordem aleatória no export XLS da Pinnacle.
  - `app/static/index.html` — `salvarEstadoExtrator`: auto-save do texto em tempo real (listener `input`). `limparExtrator(explicit)`: quando chamada pela submissao, salva estado antes de limpar (permite retry via navegacao). `salvarEstadoExtrator`: nao sobrescreve estado existente com formulario vazio (impede navegacao apagar o estado salvo antes da submissao).
  - Commits: `8ef765d`, `d22b73a`, `5fb8b6d`, `06f1455`.

**Sessão 36 (21/06/2026) — Nova casa: Bolsa de Aposta:**

- **`casas/CASA_BOLSADEAPOSTA.md` criada** — 15 seções, 4 goldens reais (20/06/2026).
- **Modo de ingestão:** texto colado (primário) + screenshot (fallback).
- **Particularidade crítica:** L/P = lucro/prejuízo, **não** retorno total. Para W: odd = (Stake + L/P) ÷ Stake. Para L: odd lida diretamente do campo `@odd`.
- **Odd campo:** `@odd` na linha de detalhe (ex.: `Sim @1.90 • R$100,00`) — autoritativo; usa ponto decimal (en-US) → converter para vírgula.
- **ID:** `ID da Aposta: XXXXX` — numérico, ~8 dígitos, visível na linha de detalhe.
- **Confronto:** em inglês com "vs" → normalizar para "v" no output: `[Time A v Time B]`.
- **Seleção "Sim":** resposta booleana (BTTS, Over/Under) — não vai na descrição; usar padrão global.
- **"BEST ODDS IN BRAZIL":** rótulo promocional no campo Descrição — ruído, ignorar.
- **Goldens confirmados:** W Ambas Marcam (98223602) · W ML com boost label (98318394) · L Gols (98223547) · L Anytime/Enner Valencia (98293971).
- **Pendências documentadas:** §5 V/HW/HL (sem amostra) · §6 boost real · §7 cashout · §8 bônus · apostas Lay (A contra) · comissão sobre ganhos · Resultado Correto (Correct Score) flagged no §Feedback.
- **`app/main.py`:** `BOLSADEAPOSTA: "Bolsa de Aposta"` adicionado ao `_CASA_DISPLAY`.
- **`app/static/index.html`:** `BOLSADEAPOSTA` adicionado a `NOMES`; `'Bolsa de Aposta'` adicionado a `DOMINIOS` com domínio `bolsadeaposta.bet.br`.
- Backup: `Backups/pre_bolsadeaposta_2026-06-21/`. Commit: `2217206`.

**Sessão 37 (21/06/2026) — Auditoria de ordem de extração + fix definitivo de chunks paralelos:**

- **Auditoria com agente Opus:** comparação histórica git entre ~16/06 e 21/06 em todos os `casas/CASA_*.md`. Conclusão: as regras de planilhamento (§9) **não foram alteradas** no período. O único problema era no backend (`app/main.py`), não nos docs das casas.
- **Root cause identificado:** `_stream_parallel` usava `is_image_mode` (bool) para decidir `reverse`. Isso não distinguia os 4 casos reais:
  - Betano **texto**: `is_image_mode=False` → `reverse=False` → TSV invertido (apostas recentes primeiro) — **ERRADO**
  - Superbet **imagens**: `is_image_mode=True` → `reverse=True` → TSV invertido (última imagem colada saía primeiro) — **ERRADO**
  - Pinnacle XLS: `is_image_mode=False` → `reverse=False` — correto (parser já inverte)
  - BET365/Betano imgs/KingPanda/Betfair: `is_image_mode=True` → `reverse=True` — correto
- **Regressão rastreada:** commit `06f1455` (fix Pinnacle de hoje cedo) introduziu a regressão no Betano texto; o bug da Superbet existia desde o commit `9f630a4` (paralelismo, 20/06).
- **Fix (`app/main.py`, commit `cb5573c`):** substituiu `is_image_mode` por duas verificações independentes:
  - `is_xls_mode`: detecta texto com `"=== Aposta ID"` (marcador exclusivo do parser XLS Pinnacle)
  - `casa_key.upper() == "SUPERBET"`: Superbet sempre `reverse=False`
  - Todos os outros casos: `reverse=True`
  - `casa_key` passado como parâmetro para `_stream_parallel`
- **Regra consolidada (confirmada pelo usuário):**
  - `reverse=False`: Pinnacle XLS (pré-invertido pelo parser) · Superbet (colagem na ordem certa)
  - `reverse=True`: Betano texto · Betfair texto · BET365 imgs · Betano imgs · KingPanda imgs
- **Validado em produção:** Betano texto ✅ · KingPanda ✅ · Betfair ✅ · Superbet (lógica confirmada pelo usuário).
- Backup: `Backups/main_pre_fix_sort_order_21jun.py`. Commit: `cb5573c`.

**Sessão 41 (21/06/2026) — Nova casa: Lottu:**

- **`casas/CASA_LOTTU.md` criada** — 15 seções, 5 goldens reais (19–21/06/2026).
- **Modo de ingestão:** texto colado (primário) + screenshot (fallback).
- **Particularidade crítica:** apostas em aberto ficam misturadas no histórico (sem filtro disponível). Badge amarelo `Aberto` identifica-as — **ignorar completamente**. Extrair apenas `Ganhou` e `Perdeu`.
- **Produto Desafio:** a Lottu exibe como `Simples de X.XX` mas combina condições via `&` na Resposta = **Múltipla** (Bet Builder intra-jogo). Sinal discriminante: presença de `&` na Resposta.
- **ID:** numérico ~7 dígitos (ex.: `4842688`), primeira linha do bilhete.
- **Data:** usar `Resolvido em: DD/MM/AAAA` (descartar horário e data de início do jogo).
- **Odd:** en-US (ponto decimal) → converter para vírgula. Para W: `Retorno ÷ Stake`. Para L: odd exibida em `Simples de X.XX`.
- **Resultado:** `Ganhou` → W · `Perdeu` → L · `Aberto` → IGNORAR.
- **Goldens confirmados:** W Múltipla (4842688 · Tunisia v Japão, 7,60) · L Player Props (4841836 · Vozinha Defesas, 2,20) · W Múltipla (4769545 · Tunisia v Japão, 4,20) · L Múltipla (4770248 · Alemanha v Costa do Marfim, 3,50) · L Múltipla multi-player (4680704 · Brasil v Haiti, 4,50).
- **Pendências:** §5 V/HW/HL · §6 boost individual · §7 cashout · §8 bônus.
- **`app/main.py`:** `"LOTTU": "Lottu"` adicionado ao `_CASA_DISPLAY` (entre KINGPANDA e PINNACLE).
- **`app/static/index.html`:** `LOTTU: 'Lottu'` adicionado a `NOMES`; `Lottu: 'lottu.bet.br'` adicionado a `DOMINIOS`.
- Backup: `Backups/pre_lottu_2026-06-21/`. Commit: `32d40d0`.

**Sessão 40 (21/06/2026) — Fix MASTER_ESPORTES: tenistas ITF classificados como Dardos:**

- **Bug:** 8 confrontos de Tênis (Bet365, ML) extraídos como Dardos. Causa: o modelo não reconhece jogadores de nicho do circuito ITF (M25/Juniors/WTA feminino de baixo escalão) e chutava Dardos por similaridade estrutural de mercado ML.
- **Fix 1 — regra de desempate:** `MASTER_ESPORTES §Regra Crítica — Dardos vs Tênis` — novo bloco: atleta não identificado em ML/H2H sem sinal positivo de Dardos (`legs`, `PDC`, `BDO`, `MODUS`, etc.) → padrão **Tênis**, nunca Dardos. Nunca usar Dardos como desempate.
- **Fix 2 — referências ampliadas:** 12 tenistas masculinos ITF adicionados (Jan Kluczynski, Zian Vanderstappen, Felix Romeo, Lucien Forrestier, Dennis Andre Dutine, Yoav Versloot, Nand Vandepoele, Melvin Vix, Maximo Nagele, Jorge Alonso-Cortes, Juan Bautista Otegui, Joao Victor Couto Loureiro).
- **Fix 3 — referências femininas:** 4 tenistas adicionadas (Monika Ekstrand, Alina Shcherbinina, Andrea Palazon Lacasa, Min Liu).
- **Fix 4 — desambiguação:** nota "Min Liu (tênis de quadra, chinesa) ≠ Ming Liu (tênis de mesa)" adicionada à lista WTA/ITF.
- Backup: `Backups/MASTER_ESPORTES_2026_pre_regra_desempate_tenis.md`. Commit: `347fddd`.

**Sessão 39 (21/06/2026) — Nova casa: Betnacional:**

- **`casas/CASA_BETNACIONAL.md` criada** — 15 seções, 7 goldens reais (20/06/2026).
- **Modo de ingestão:** texto colado — aba "Histórico de apostas" com filtro **"Liquidadas"** aplicado antes de copiar (primário). Screenshot da aba "Apostas" (últimas 24h) como fallback.
- **ID:** sem ID impresso → dedup por **Código sintético** = `BN-DD/MM/AAAA-HH:MM-<odd exibida>` a partir do horário de colocação (estável entre reprocessamentos). _Atualizado na sessão 46 — antes era assinatura de conteúdo, que duplicava._
- **Data:** campo `DD/MM/AAAA, às HH:MM` no Histórico = data do evento/liquidação → coluna `Data` usa DD/MM/AAAA; o **horário** vai para o Código (não descartar por completo).
- **Resultado:** `Retorno = 0 → L` · `Retorno = Aposta → V` · `Retorno > Aposta → W`.
- **Odd para W:** `Retorno ÷ Aposta` (confirmado em todos os 7 goldens). Para L/V: Odd exibida no campo `Odd` (ponto decimal → vírgula).
- **Confronto:** separador `x` (ex.: "Holanda x Suécia") → normalizar para `[Time A v Time B]`. Abreviações expandidas: HOL→Holanda · SUE→Suécia · Ale→Alemanha · CdM→Costa do Marfim.
- **Promoções:** "Super Odds" e "Turbinaço CazéTV" = rótulos de promoção; ignorar para classificação de categoria.
- **Confronto ausente (Layout A):** algumas apostas Turbinaço não incluem confronto no Histórico → AI infere do contexto; documentado como pegadinha.
- **Goldens confirmados:** V·ML (D S Stricker/A Hunziker) · L·Múltipla (3 condições Holanda×Suécia) · W·Player Props (Cody Gakpo) · W·Cartões (Tunísia×Japão) · W·Ambas Marcam 2ºT (Holanda×Suécia) · L·Player Props (Kai Havertz) · W·Player Props (Vozinha).
- **`app/main.py`:** `"BETNACIONAL": "Betnacional"` adicionado a `_CASA_DISPLAY` (ordem alfabética, entre BETFAIR e BOLSADEAPOSTA).
- **`app/static/index.html`:** `BETNACIONAL: 'Betnacional'` adicionado a `NOMES`; `Betnacional: 'betnacional.bet.br'` adicionado a `DOMINIOS`.
- Backup: `Backups/pre_betnacional_2026-06-21/`. Commit: `c05ef80`.

**Sessão 38 (21/06/2026) — Fix UI: copiar/baixar pendentes arquivados:**

- **`app/static/index.html`:** botoes "Copiar pendentes" e "Baixar .tsv" removeram filtro `!b.archived`. Agora incluem apostas arquivadas pendentes quando a visao de arquivados esta ativa. Aviso amarelo exibido quando ha arquivados mas a visao esta desligada. Commits: `0d22f0e`, `fb71076`.

**Sessão 39 (21/06/2026, continuacao) — Docs Dardos ML:**

- **`casas/CASA_SUPERBET.md`:** §9 nota explicita — nome de jogador em esporte individual (Dardos, Tenis) = `ML`, nunca `Outras`. §13 pegadinha equivalente. §15 golden #8 `Alec Small [Joe Croft v Alec Small]` (Dardos ML L). Commit: `8433259`.
- **`global/MASTER_ESPORTES_2026.md`:** `Joe Croft` e `Alec Small` adicionados a lista de referências auxiliares de Dardos (secao MODUS/outros circuitos). Commit: `2291149`.

**Sessão 40 (21/06/2026) — Fix: cadastro de parceiro Bolsa de Aposta:**

- **Bug:** ao criar parceiro com casa "Bolsa de Aposta", o app retornava "Casa desconhecida: Bolsa de Aposta".
- **Causa raiz:** `body.casa.upper()` convertia `"Bolsa de Aposta"` → `"BOLSA DE APOSTA"`, e o sistema buscava `CASA_BOLSA DE APOSTA.md` (inexistente). O arquivo correto e `CASA_BOLSADEAPOSTA.md`.
- **Fix:** `app/main.py` — funcao `_display_to_key()` adicionada. Faz reverse lookup no `_CASA_DISPLAY` antes de usar fallback `upper().replace(' ','')`. Corrigidos os 3 pontos: `/extrair`, `/salvar` e `/parceiros` (POST).
- Backup: `Backups/pre_bolsadeaposta_fix_2026-06-21/`. Commit: `6636106`.

**Sessão 42 (22/06/2026) — Fix lentidão da Betano (auditoria independente):**

- **Sintoma:** Betano era a única casa lenta — extração de TEXTO de 30-50 bets levava 8-12 min (475s medidos em produção, print do usuário), enquanto Bet365 (15 imgs), Pinnacle (XLS) e Betfair (texto+CSV) eram rápidas.
- **Causa raiz (provada com teste local):** `_build_chunks` (`app/main.py`), para texto puro, dividia por linha em branco (`split("\n\n")`). O colar da Betano vem **grudado** (sem linha em branco entre bilhetes) → caía em **1 bloco → 1 chunk → chamada 100% sequencial** com ~90 bilhetes. Era a única casa de alto volume sem separador de bilhete reconhecido pelo chunker (Pinnacle usa `=== Aposta ID`, Bet365 usa 1 chunk/imagem).
- **Fix 1 — split por bilhete:** `_build_chunks` recebe `casa_key`; para Betano divide na linha-tipo (`Simples`/`Dupla`/`Tripla`/`N-seleções`) via `_BETANO_SPLIT_RE` — a fronteira real do bilhete (análogo ao `=== Aposta ID` da Pinnacle). ~90 bilhetes → 4 chunks equilibrados → paralelismo 4× real.
- **Fix 2 — pré-dedup por ID:** `_dedup_betano_text` + `repository.get_codigos_resolvidos()` descartam, antes do modelo, bilhetes já **liquidados** no banco (`extraction_state='resolvida'`) + duplicatas de scroll dentro do colar. Mantém os salvos como `aberta` (transição aberta→liquidada ainda processa). No caso real: 90 lidos → 37 novos, corta >50% do trabalho.
- **Validação:** teste local lado a lado confirmou — colar grudado: split atual = 1 chunk (sequencial); split novo = N blocos → chunks equilibrados, IDs detectados. Sintaxe OK (`py_compile`).
- Backup: `Backups/betano_chunker_dedup_2026-06-22/`. Commit: `34b7cf1`.
- ⚠️ **Nota de histórico:** a edição de `app/main.py` da tarefa Over/Under abaixo ("instrução layout horizontal") foi feita em paralelo e pegou carona neste commit `34b7cf1` (não no `abf8860`). Conteúdo correto; só a atribuição git ficou junta.

**Sessão 42 (22/06/2026) — Fix Over/Under em golden sets + instrução layout horizontal:**

- **Auditoria Over/Under:** varredura em todos os `casas/CASA_*.md`. Regra do `MASTER_DESCRICAO §11` é absoluta: "Mais de"/"Menos de" são inputs, nunca output válido. 4 ocorrências corrigidas:
  - `CASA_KINGPANDA.md §15 G3`: `Mais de 2,5 [Total de Gols...]` → `Over 2,5 [Total de Gols...]`.
  - `CASA_KINGPANDA.md §15 G7`: `Mais de 9,5 [Escanteios]` → `Over 9,5 [Escanteios]`.
  - `CASA_LOTTU.md §15 G1`: `Mais de 4,5 Escanteios` → `Over 4,5 Escanteios`.
  - `CASA_LOTTU.md §15 G2`: `Mais de 3,5 Defesas do Goleiro` → `Over 3,5 Defesas do Goleiro`.
  - As outras 7 casas (Bet365, Betano, Betfair, Betnacional, Bolsa de Aposta, Pinnacle, Superbet) estão corretas.
- **Fix instrução de extração (`app/main.py`):** regra 2 de "LEITURA DAS IMAGENS" reescrita — agora explica que bilhetes podem estar lado a lado (horizontal) e instrui o modelo a CONTAR todos os bilhetes visíveis antes de extrair. Corrige caso de terceiro bilhete não detectado quando layout é horizontal (3 tickets side-by-side).
- **Auditoria de referências globais nas casas:** todas as casas verificadas quanto ao cabeçalho de autoridades e à regra Over/Under. Princípio arquitetural reforçado: arquivos de casa traduzem especificidades da casa; regras universais ficam nos masters globais e as casas **referenciam**, não redefinem.
  - `CASA_LOTTU.md`: cabeçalho sem lista de autoridades globais → adicionado bloco `Autoridades globais: MASTER_OUTPUT_2026, ...` (padrão de todas as casas). Também adicionada referência a `MASTER_DESCRICAO_2026 §11` para conversão `Mais de → Over`.
  - `CASA_BETFAIR.md §10`: sem regra Over/Under → adicionada referência a `MASTER_DESCRICAO_2026 §11` (inclui variante `N ou mais X` da Betfair).
  - `CASA_BETNACIONAL.md §10`: sem regra Over/Under → adicionada referência a `MASTER_DESCRICAO_2026 §11`.
  - `CASA_BOLSADEAPOSTA.md §9`: cobria apenas `Over X Goals` → generalizado para qualquer mercado + referência a `MASTER_DESCRICAO_2026 §11`.
  - Casas corretas (sem alteração): Bet365, Betano, KingPanda, Pinnacle, Superbet.
- Backups: `CASA_KINGPANDA_pre_over_under_*.md`, `CASA_LOTTU_pre_over_under_*.md`, `main_pre_instrucao_layout_horizontal_*.py`, `CASA_LOTTU_pre_refs_globais_*.md`, `CASA_BETFAIR_pre_refs_globais_*.md`, `CASA_BETNACIONAL_pre_refs_globais_*.md`, `CASA_BOLSADEAPOSTA_pre_refs_globais_*.md`.

**Sessão 43 (22/06/2026) — Nova casa: Jogo de Ouro:**

- **`casas/CASA_JOGODEOURO.md` criada** — 15 seções, 2 goldens reais (22/06/2026).
- **Modo de ingestão:** screenshot (primário — cards em grid de duas colunas); texto colado como fallback (aguarda confirmação). Abas de filtro `Aberto · Processado · Ganhou · Perdida · Cashout` — extrair só os resolvidos, ignorar `Aberto`.
- **Formato numérico en-US:** dinheiro e odds com **ponto** decimal (`R$30.00`, `3.50`) → converter para vírgula.
- **ID:** visível, numérico ~10 dígitos (ex.: `5093265488`), na linha do `ID:` (rodapé do card).
- **Boost:** sim — formato `[orig] >> [final]` + badge verde `ODDS DE OURO`. `Cotações totais` = odd final (boosted). W: `Ganho total ÷ Stake`. L: `Cotações totais` direto.
- **Criar Aposta (badge `CA`)** = Bet Builder intra-jogo → `Múltipla`.
- **Status:** `GANHOU / VENCIDO` (header verde) → W · `PERDIDO` (header vermelho) → L · `Aberto` → IGNORAR.
- **Data:** duas ocorrências `DD/MM • HH:MM` — evento (acima de `Cotações totais`, usar) vs colocação (linha do `ID:`, ignorar). Ano inferido de `data_referencia`.
- **`Ganho total`:** retorno bruto (só em W); vazio em L. Stake = `Valor total de aposta`.
- **Mapa §9 confirmado:** `Vencedor do encontro`→ML · `Total de gols`→Gols · `Total de escanteios` / `1º tempo - total de escanteios`→Escanteios · `Criar Aposta` (badge `CA`)→Múltipla. Demais 23 categorias aguardam amostra.
- **Goldens confirmados:** L·Gols (`5093260948` · Noruega v Senegal · Under 3,5 · 1,70) · W·Múltipla Criar Aposta (`5093265488` · Noruega v Senegal · ML+Escanteios 1ºT · 3,50).
- **Pendências:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout (valor recebido) · §8 bônus.
- **`app/main.py`:** `"JOGODEOURO": "Jogo de Ouro"` adicionado ao `_CASA_DISPLAY` (entre BOLSADEAPOSTA e KINGPANDA).
- **`app/static/index.html`:** `JOGODEOURO: 'Jogo de Ouro'` adicionado a `NOMES`; `'Jogo de Ouro': 'jogodeouro.bet.br'` adicionado a `DOMINIOS`.
- Backup: `Backups/pre_jogodeouro_2026-06-22/`. Commit: (este).

**Pendências que aguardam bilhete real:**
- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus · §9 (23 categorias aguardam amostra)

**Próximo passo:**
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).

Quando chegar um bilhete novo: abrir o arquivo da casa correspondente, preencher a pendência, rodar o checklist do `CLAUDE.md` se envolver categoria nova.

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/extrator`). Deploy automático via Railway conectado ao GitHub — push dispara deploy.
