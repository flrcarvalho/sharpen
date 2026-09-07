# HISTÓRICO — Sessões 62 → 14 (log de “Estado atual”)

> **Log paralelo**, não a continuação da cadeia acima: é o antigo §4 “Estado atual” do STATUS, com a sua própria numeração.
>
> Partição do `docs/HISTORICO.md`, criada na faxina de documentação de 2026-09-07 (Lote C). **O texto é o original, verbatim** — só foi partido.

[↑ Índice](../HISTORICO.md) · [← mais recente: Sessões 149 → 61](HISTORICO_s061-s149.md) · [mais antigo: Sessões 43 → 24 (log de “Próxima sessão”) →](HISTORICO_s024-s043_proximo.md)

---

## Log de sessões 62 → 14 (antigo §4 "Estado atual")

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
