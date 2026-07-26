# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-26 (sessão 208 — **Mapas de favicon limpos: os três param de mentir sobre quais casas existem.** Fecha a pendência aberta na s206. **(1) Aliases mortos removidos** do `index.html` e do `inicio.html`: `BetBra` · `Multibet` · `Faz1be` · `7k Bet` · `Esportiva Bet`. Essas grafias **não existem mais no banco** (unificadas na s204) e a `casa_canonica` impede que voltem — as linhas só faziam o mapa mentir. Diferença só de **caixa** também não precisa mais de alias: o lookup casa por caixa-baixa desde a s204. **(2) No `data.js` era o OPOSTO:** a chave era `Faz1bet` (grafia aposentada) e **não existia** `Faz1Bet` (a que ficou) — **renomeada**, não removida; sem isso a limpeza teria deixado a casa sem ícone no dash. **(3) A limpeza revelou um buraco:** o `data.js` **não tinha domínio para `Aposta Ganha` nem `Pagol`** — as duas caíam no fallback **só no dashboard**, enquanto os outros dois mapas já as conheciam desde sempre. Preenchidas com os domínios existentes. **Estado final, conferido contra as 45 casas do banco:** `index.html` **45 chaves para 45 casas, um-para-um**; `inicio.html` e `data.js` com 46 — as 45 + `Betao`, alias **sem acento** de `Betão`, **mantido de propósito** (o lookup casa caixa, não acento; tirar deixaria a casa exposta se a grafia sem acento reaparecer num import). **Cobertura: zero casa sem domínio nos quatro mapas.** Bump `data.js?v=8→9`. Gates: `node --check` no `data.js`, blocos JS inline sem erro, `check-tokens` OK. **Nada de backend tocado.** **Anterior: s207 abaixo.**)_

_Anterior: 2026-07-26 (sessão 207 — **"faça uma extração do ZERO na poly e bata que não há erro algum": o dinheiro estava impecável, a CLASSIFICAÇÃO tinha 40 linhas erradas.** **Método:** script de auditoria com **20 conferências**, cada uma com um número — coleta pela API do zero e reconcilia contra o extrato on-chain. **A conferência que mais vale é a nº 3, porque NÃO é circular:** para cada um dos 377 mercados, o payout que o modelo deduz tem de reproduzir o dólar que a blockchain de fato pagou — **bateu nos 180 resgates, centavo a centavo**. **Dinheiro: 8/8 OK** (389 linhas × 389 compras · códigos únicos · P/L difere do real por **$445,32 = exatamente** a taxa de entrada de 1,73% · retorno bruto W+V == resgatado + vendido + parado, $24.107,32 dos dois lados). **Classificação: 40 linhas erradas.** **Raiz:** no `_categoria` o teste genérico de over/under rodava **antes** das regras por esporte; como a Polymarket escreve quase tudo como `O/U X`, o genérico vencia sempre e **escanteio, gol, ponto e round caíam todos em `Player Props`** — 35 linhas, **nenhuma de jogador**, contra o `MASTER_APOSTAS §1` (categoria = objeto apostado) e o `§7` (mercado específico > genérico). Reclassificado: **17 Escanteios · 8 Gols · 5 Rounds · 2 Pontos · 1 Corridas · 3 ML**; sobrou **1** Player Props — o strikeout do arremessador, que o `§6 Baseball` manda ser exatamente isso. **Mais dois defeitos no caminho:** (a) o regex casava **`under` DENTRO de palavra** — `Spurs vs. Th·under` e dois jogos do torneio `Th·under·pick` viravam mercado de total; agora tem `\b`; (b) faltavam os prefixos de slug **`col`** (Conference League — o slug **não** usa a sigla oficial `uecl`), **`per1`** (Liga 1 do Peru) e **`auc`** (Australia Cup): 7 jogos de futebol em esporte `Outro`. **Categoria `Rounds` criada (decisão do Feca) com a REGRA DE PROPAGAÇÃO inteira:** `MASTER_APOSTAS §3` (tabela) · `§4` (sinônimos) · `§5` (regra + o que **não** é Rounds) · `§6` (**seção MMA/Boxe criada — o MASTER não tinha NENHUMA regra de MMA**) · `§7` (Rounds > Player Props, ML > Rounds) · `§9` (validação 22); `MASTER_DESCRICAO §12.5` (exemplo); `CASA_POLYMARKET §9` — **o mapa da casa TINHA a regra errada escrita** (`over/under → Player Props`), ou seja o doc ensinava o bug. `audit_casas` sem FAILs. **Bloqueio estrutural, mesma família da odd da s205:** `esporte`/`aposta`/`descricao` **nunca** eram atualizados (só no INSERT) → a correção do classificador não alcançaria as 389 linhas. Entraram na exceção `origem='sync'`. **Extração rodada chamando a FUNÇÃO DA ROTA** (não replicando a lógica, que divergiria dos passos): **389 coletados · 0 inseridos · 389 atualizados · 0 alertas**. **Reauditoria: 20/20 OK** — banco × coletor com **0 campo divergente** e P/L idêntico (**−R$5.732,60** dos dois lados; era −R$3.158,44 antes da s205 chegar ao banco). **Gates:** **231 passed** + **13 passed** no harness de DB (Postgres real, +2 casos: sync refresca classificação, IA não sobrescreve) · `audit_casas` sem FAILs · `check-tokens` OK. Backup `Backups/categoria-rounds-mma/`. **PENDÊNCIA honesta:** o painel segue **~1,7% otimista** por não contabilizar a taxa de entrada da Polymarket (~R$2.250 no acumulado) — é decisão de projeto documentada (odd limpa = 1/preço), **não** bug, mas agora está medida. Ver [[polymarket_liquidacao_payout]] · [[betano_abertas_e_upsert]]. **Anterior: s206 abaixo.**)_

_Anterior: 2026-07-26 (sessão 206 — **Favicon: cobertura 45/45, verificada baixando os ícones — e a PixBet estava com o logo ANTIGO.** **(1) As 3 casas sem domínio fecharam** com os endereços que o Feca passou: `Aposta1`→`aposta1.bet.br` · `Bet do Milhão`→`milhao.bet.br` · `Bingoplus`→`bingoplus.bet.br`. Entram nos **três** mapas paralelos (`index.html` DOMINIOS · `inicio.html` CASA_DOMAIN · `data.js` CASA_ICONS **+** HOUSE_DOMAIN) — ver [[favicons_tres_mapas]]. **(2) Verificação de verdade, não leitura de código:** baixei o favicon das **45 casas do banco** pelo Google S2 e comparei com um baseline de domínio inexistente. **45/45 devolvem ícone real** — nenhuma em 404, nenhuma no genérico. **(3) Achado: 5 casas tinham ícone diferente entre o `.com` do mapa e o `.bet.br`.** Montei a folha de comparação lado a lado: **4 são o MESMO ícone** (só recorte/compressão — Betboo, Pinnacle, SportingBet, MatchBook, não mexidos), mas a **PixBet era logo ANTIGO** — `pixbet.com` serve o X azul em círculo; o correto é **`pix.bet.br`** (domínio da regulada BR, informado pelo Feca), que serve o X verde/branco atual. Trocado nos 3 mapas. Bump `data.js?v=6→8`. Gates: `node --check` no `data.js`, blocos JS inline sem erro, `check-tokens` OK. **Nada de backend tocado.** **PENDÊNCIA honesta:** os mapas seguem com **aliases mortos** das grafias unificadas na s204 (`BetBra`, `Multibet`, `Faz1be`, `7k Bet`, `Esportiva Bet`) — inofensivos, mas mentem sobre o que existe. **Anterior: s205 abaixo.**)_

_Anterior: 2026-07-26 (sessão 205 — **"parece ter saldo em aberto sem aposta em aberto, não sei se tá tudo redondo" — não estava, e o buraco era maior que o rótulo: a correção da odd NUNCA chegou ao banco.** **Como apareceu:** o Feca olhou o painel depois do conserto da s200 e desconfiou de um KPI. **O que a conferência achou (SELECT + coletor, lado a lado):** **28 linhas do banco divergem do que o coletor produz hoje.** A `odd` estava velha em 181 linhas, `data` em 25, `stake` em 22. **Raiz:** o `upsert_bilhetes` congela `odd`/`data`/`stake` assim que a aposta resolve — blindagem CERTA para extração por IA, onde a re-leitura é ruidosa. Só que **`resultado` nunca foi blindado**. Com fonte determinística isso deixa a linha **meio atualizada**: ao corrigir o cálculo do mercado anulado, o resultado mudou de L para W e a odd ficou a antiga, **dobrada** — e 7 anuladas passaram a exibir **lucro fantasma** (`BetBoom vs Aurora` marcando **+R$578** onde o real é **−R$11,80**). **Blindar metade dos campos é pior que blindar todos ou nenhum** — a s200 melhorou o cálculo e PIOROU o banco, porque só metade da correção passou. **Fix (aval do Feca):** exceção `origem='sync'` no ON CONFLICT e no UPDATE de fallback — fonte determinística MANDA em data/stake/odd mesmo na linha já resolvida. **Escopo medido antes de mexer:** `origem='sync'` é usada **só** pela Polymarket (384 linhas, 1 dono, query em produção) → nenhuma casa de IA muda de comportamento. Contrapartida aceita: edição manual de data/stake/odd em casa sincronizada não sobrevive ao sync (o `tipster` sobrevive, pelo COALESCE). **P/L verdadeiro: −R$5.732**, não os −R$3.158 que o painel mostrava — ou seja, o "salto" de −R$6.516 para −R$3.158 que parecia boa notícia era, em boa parte, este defeito. **Conferido contra o dinheiro, em USD puro (sem câmbio no meio, que era o vício da 1ª tentativa de conferência):** P/L do painel −$1.114,49 × P/L real da carteira −$1.559,81 → diferença de **$445,32 = exatamente a taxa de entrada de 1,73%** que o projeto deliberadamente não contabiliza (odd limpa = 1/preço). O lado do retorno fecha com folga de **$100,00 redondos**, que é o `SPARTA vs Bebop` — anulado devolvendo o stake exato, classificado V (P/L 0) e por isso fora da soma das W. **Nada mais diverge.** **(2) KPI "A resgatar" (passou pelo `/nova-ui`):** o $109,82 de "Saldo em Aberto" com **0 posições ativas** era dinheiro **liquidado e não resgatado** (as 2 anuladas: $74,59 VSC + $35,23 Dota). Agora sai em card próprio, âmbar (`--warn`, mesmo token do badge "aguardando resultado"), que **só aparece quando há o que resgatar** — sem ele o layout de 4 colunas fica idêntico. Backend devolve `em_aberto` + `a_resgatar`, com `em_aberto` saindo por **subtração** para as parcelas sempre fecharem com o portfólio. Helpers **reusados** (`fmtUSD`/`fmtBRLsub`, a exceção USD do `UI_REFERENCE §5.3`) — nenhum formatador novo. Gates do `/nova-ui`: `check-tokens` verde, JS inline sem erro de sintaxe, **render headless conferido** nos dois estados (4 e 5 cards). **(3) 1 centavo que não fechava, pré-existente:** `total` era arredondado do valor cru enquanto as parcelas eram arredondadas em separado → a tela mostrava 109,82 + 949,94 = **1.059,75**. Agora o total soma o que a tela mostra. **A órfã da s200 sumiu sozinha** — o `remover_bilhetes_supersedidos` funcionou no sync do Feca, sem precisar do X na grade. **Gates:** **231 passed** + **11 passed** no harness de DB (Postgres real no CI, +3 casos cobrindo os dois lados da regra: sync refresca, IA continua blindada, tipster preservado) · `check-tokens` OK. Backups `Backups/polymarket-kpi-a-resgatar/`. **PENDÊNCIAS honestas:** (1) **o Feca precisa clicar em Sincronizar** — só então as 28 linhas são corrigidas no banco e o P/L vai para ~−R$5.732; (2) **desvio de marca anotado, NÃO corrigido** (fora do aval): o `fmtUSD` não agrupa milhar — mostra `$ 1059,76` em vez de `$ 1.059,76`, contrariando o `§5.2`; é o helper canônico de USD, decidir antes de mexer. Ver [[polymarket_liquidacao_payout]] · [[pl_calculo_derivado]]. **Anterior: s204 abaixo.**)_

_Anterior: 2026-07-26 (sessão 204 — **Casas duplicadas por grafia: 54 → 45. O sistema para de tratar "PixBet" e "Pixbet" como duas casas.** **Como apareceu:** rastreando por que o chip da Faz1bet mostrava ícone errado, o mapa de favicon revelou o problema de baixo — `casa` é TEXTO em todas as tabelas, então **cada grafia é uma casa diferente**: contas, KPIs, filtros e favicon separados. Cada base importada trouxe a sua grafia, e **ninguém via a divisão porque cada dono só enxerga a própria** (as variantes perdedoras eram todas do Jonathan). **8 grupos unificados, grafia escolhida pelo Feca um a um:** `BetBra`→**Betbra** · `Faz1bet`→**Faz1Bet** · `Matchbook`→**MatchBook** · `Multibet`→**MultiBet** · `Pixbet`→**PixBet** · `Esportiva Bet`→**Esportiva** · `7k Bet`→**7K** · `Fullbet`→**Fulltbet** (mesma casa, confirmado pelo endereço fulltbet.bet.br). **`Betboo` × `Betboom` NÃO foram unificadas** — são casas diferentes (betboo.com × betboom.bet.br). **`scripts/unificar_casas.py`** (novo; relatório por padrão, `--aplicar` numa transação): **358 bilhetes movidos, 358 assinaturas recalculadas** — obrigatório, `casa` entra no hash de `_assinatura`, e sem recalcular a próxima captura duplicaria o histórico inteiro (mesma armadilha do rename de conta, s198) — mais 56 linhas em `parceiros`/`casas_meta`/`correcoes`/`uso_tokens` e **4 tipsters** (`tipsters.casas` é lista em TEXTO: troca o item exato, nunca por substring, senão "Esportiva" casaria DENTRO de "Esportiva Bet"). **Onde a casa mora foi levantado no `information_schema`, não chutado.** **Colisões medidas ANTES de escrever uma linha: zero** — em `bilhetes` (assinatura) e em `parceiros`/`casas_meta`/`casa_config` (unicidade que inclui casa); o script aborta sozinho se alguma aparecer. Conta de typo `Faz1be/Pessoal` (Jonathan, 0 bilhetes) apagada. Backup em `Backups/s199-unificar-casas/*.csv`. **Trava na entrada (`casa_canonica`)** para não nascer variante nova: ao **criar conta** (onde a casa nasce) e no `/salvar` sem `parceiro_id`, a casa casa por caixa/espaço com as existentes e **reusa a grafia**. Casa realmente nova segue **verbatim** — não title-caseia nem come espaço, que foi o bug da s141 ("Rei do Pitaco"→"Rei Do Pitaco"). Consulta em `parceiros` (350 linhas), não em `bilhetes` (dezenas de milhares): toda casa nasce com uma conta. Smoke contra o banco real: `pixbet`/`PIXBET`→`PixBet`, `bolsadeaposta`→`Bolsa de Aposta`, `Rei do Pitaco` e casa inexistente intactos, e `esportiva bet` **não** casa com `Esportiva` (sufixo é decisão humana — a trava não adivinha). **Antes disso, o chip parou de errar o ícone por CAIXA:** o lookup era exato (`DOMINIOS[casa]`) e caía no palpite `nome+.com`; agora casa por caixa-baixa nos dois mapas, espelhando o `dash/app.js:48-50`, e 6 domínios que só existiam no `inicio.html` foram copiados para o `index.html` (os mapas estavam dessincronizados). **Gates:** `231 passed, 11 skipped` (+5 da trava, +1 do `/salvar`) · `audit_casas` e `audit_sharpenup` sem FAILs · harness 3 casos/65 bilhetes verde · **zero bilhete órfão no banco**. **PENDÊNCIAS honestas:** (1) **3 casas seguem sem domínio em mapa nenhum** — `Aposta1`, `Bet do Milhão`, `Bingoplus`: o chip cai no fallback e eu não invento domínio. (2) Os mapas de favicon ficaram com **aliases mortos** das grafias unificadas (`BetBra`, `Multibet`, `Faz1be`, `7k Bet`, `Esportiva Bet`) — inofensivos, mas mentem sobre o que existe. (3) A trava pega o **cadastro**; dado escrito direto no banco por script de import não passa por ela. **Anterior: s203 abaixo.**)_

_Anterior: 2026-07-26 (sessão 203 — **"a bet365 do Marlon está duplicando ou não está encerrando": nenhum dos dois. Ela estava perdendo bilhete pela JANELA da tela.** **Sintoma do Feca:** a casa mostrava **35** apostas abertas, o painel mostrava **61 aguardando resultado** + **116 aguardando informação**, depois de rodar 48h finalizadas + 48h em aberto. **Diagnóstico por SELECT em produção, não por leitura de código:** **(1) Zero duplicação.** As 61 abertas têm **todas** código `BR`; nenhum código se repete na conta; nenhum "miolo" de recibo aparece duas vezes. Das 4.046 linhas, só **1** par tem mesma descrição+stake com códigos diferentes, e são duas apostas legítimas (uma `W` e uma `L` no mesmo mercado, 17/07). **(2) Os 116 "aguardando informação" não são bug:** são exatamente os 116 bilhetes do lote do dia, todos sem tipster. É o "Sugerir tipsters" não rodado. **(3) As 61 abertas se partem em dois grupos:** **35** tocadas no lote de hoje, que **batem exatamente** com o contador da casa, e **26** resíduo dos lotes de 25/07 01:34 e 01:38, com `atualizado_em` congelado lá. **(4) O UPSERT está certo e sempre esteve:** os dias 14/07 a 23/07 têm **zero** abertas nessa conta. Tudo que volta na captura, fecha. **Causa real:** as 26 **não voltaram**. A captura de abertas trouxe 35, o total exato da casa, logo as 26 já tinham liquidado; a de encerradas 48h trouxe 86 bilhetes, **todos INSERT novo**, nenhum deles entre os 26. Pelo volume da conta (50 a 86 apostas/dia), 48h de encerradas seriam 110+. **Mecanismo, no código:** o `b3_inject` é **100% passivo**, o parâmetro `dias` nem é usado para filtrar; ele só enxerga os summaries que a **própria página** baixou. O summary pagina (cursor `PT=` no header) e o "Mostrar Mais" é não-automatizável (s180). Lista não expandida, ou aposta colocada antes da janela, é bilhete que não chega, **em silêncio**. Pior: aberta que sai da janela fica presa **para sempre**, porque a cada dia se afasta mais dela. **CONFIRMADO AO VIVO pelo Feca, é o que fecha a questão:** uma passada de `Período` sobre 19 a 21/07 fechou **8** das 26, e o total da conta ficou em **4.046 linhas antes e depois** — zero inserção, UPSERT puro, nada duplicado. Restaram **20** presas (17 de 25/07, 2 de 24/07, 1 de 20/07). **Regra gravada no canônico** (`CASA_BET365 §2`, aval do Feca): `Últimas 24/48 horas` não cobre aposta **colocada** antes da janela mesmo que ela tenha liquidado dentro; para reconciliar abertas antigas rode `Período` **desde a data em que a aposta foi feita**, não desde a data do jogo; e a captura é passiva, então expanda a lista antes e confira o `[SharpenUp] Bet365 API: N bilhete(s) · com código=X/Y` no console. **Higiene, achada no caminho:** o commit `d7f82c4` (outro terminal) subiu as fixtures da bet365 para um repo **PÚBLICO**. Nome, endereço e CPF o Feca já tinha redigido; sobravam cidade, user-agent e **device ID**, agora redigidos também. O histórico do git guarda o que já foi pushado e **não houve rewrite** (force push no `main` dispara deploy no Railway; risco não compensa o dado, que é leve). **Nada de produção foi tocado:** só `casas/`, `STATUS`, `HISTORICO` e a fixture. **PENDÊNCIAS honestas:** (1) as **20 presas restantes** exigem mais passadas de `Período` sobre 24 e 25/07, o Feca estava rodando; (2) o **guard de resíduo NÃO foi construído** — proposto e aguardando decisão: ao salvar um lote, comparar as abertas que o banco já tem com as que voltaram e sinalizar em âmbar as que sumiram dos dois lados, na mesma família do guard `salvou N × grade 0` da s195; (3) a bet365 segue **sem caso no harness**, agora sem desculpa (as fixtures estão no repo desde a s202). Ver [[bet365_captura_api]] · [[extracao_perda_silenciosa_chunk]]. **Anterior: s202 abaixo.**)_

_Anterior: 2026-07-26 (sessão 202 — **Faxina do backlog: duas pendências listadas já estavam fechadas, e os payloads reais da bet365 entraram no repo.** **(1) Backlog mentindo — conferido com as funções REAIS, não por leitura:** `conferir_cobertura("[Código: JR8714690761I]")` devolve `esperados: 1` (a bet365 **está** coberta desde a `831f97f`, que trocou as regexes por formato por um **gabarito genérico de marcador** — casa nova entra sem regex) e `_CASAS_MARCADOR_CODIGO` já contém `PINNACLE` (e `TIVO`) desde a `7cf11ae`. Os dois itens seguiam no §5 como se estivessem abertos; foram removidos. Sessão que "conserta" o que já está consertado é a mesma perda de uma sessão que não conserta nada. **(2) Fixtures da bet365 resgatadas:** `harness/fixtures/bet365.summary.txt` + `bet365.confirmation.txt` — os payloads REAIS (`F|00;…`) do bilhete com **bet builder**, que quebrou o parser três vezes (registro `04` ignorado, `02` lido como perna, `TP=00010101000000` virando "01/01/0001"). Estavam só numa pasta temporária do Windows. **Pendente:** a bet365 é a única casa de robô **sem caso no harness** — o material bruto agora está no repo, falta escrever `casos/bet365.mjs`. Nada de produção tocado nesta sessão. Ver [[bet365_captura_api]]. **Anterior: s201 abaixo.**)_

> **Histórico completo das sessões 199 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
/global/                 (autoridade única — 6 masters)
    MASTER_PIPELINE_2026.md
    MASTER_ESPORTES_2026.md
    MASTER_APOSTAS_2026.md
    MASTER_DESCRICAO_2026.md
    MASTER_RESULTADO_2026.md
    MASTER_OUTPUT_2026.md
/casas/                  (1 arquivo por casa — traduz, nunca redefine)
    CASA_MODELO.md         (gabarito — 15 seções)
    CASA_BET365.md
    CASA_BETANO.md
    CASA_BETESPORTE.md
    CASA_BETFAIR.md
    CASA_BETNACIONAL.md
    CASA_BOLSADEAPOSTA.md
    CASA_JOGODEOURO.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_PINNACLE.md
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

Os 6 MASTER_*.md vivem em `/global/`; as 15 casas em `/casas/` (Polymarket por API, as demais por IA/texto).

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`).
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Casas:** 15 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. Casas por **API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365 e **KTO** (Kambi, desde a s192).
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências (aguardam bilhete real)

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betfair:** cashout **parcial** (`isPartialCashOut`) sem amostra — o total já está travado no harness (2 casos) · HW/HL sem amostra · Each Way com `0 < Retorno < Stake` (o §5 não cobre essa faixa; hoje sai "a conferir", sem chute)
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

**Próximo passo (backlog vivo, um por vez):**
- **Pinnacle sem fixture no harness** (s201): a instrução foi corrigida (§6/§11 não afirmam mais que a exibida é autoritativa em `W`), mas a leitura da odd **nunca foi travada contra dado real** — só Betfair, KTO e Tivo têm caso. Com o JSON do `POST /member-service/v2/wager-filter` dá para criar `fixtures/pinnacle.*.json` + `casos/pinnacle.mjs` e medir de fato o quanto a exibida diverge de `Retorno ÷ Stake`. O banco não serve para isso: guarda stake e odd, nunca o retorno.
- **bet365 sem caso no harness** (s202): é a única casa de robô sem regressão travada — e o parser dela já quebrou 3 vezes. As fixtures reais (`summary` + `confirmation` do bilhete com bet builder) já estão em `extensor/harness/fixtures/`; falta escrever `casos/bet365.mjs`. A conferência de cobertura dela **já está ligada** (`831f97f`).
- **`renomear_parceiro` não recalcula a assinatura** (s198): `parceiro` entra no hash, então toda conta renomeada duplica o histórico na próxima captura.
- **41 apostas com odd truncada em reticências** (`2.50001664442...`): 22 Bet365, 6 Novibet, 6 Bolsa, 4 Betfair, 3 Esportiva Bet. A instrução proíbe reticências e uma odd assim não converte para número — mexe em P/L, não é cosmético.
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Solto (cosmético):** favicon da KTO aponta para `kto.com`; o domínio real é `kto.bet.br`. Corrigir nos 3 mapas (`extensor/popup.js`, `app/static/index.html`, `app/static/dash/assets/js/data.js` + `inicio.html`).
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

Quando chegar um bilhete novo: abrir o arquivo da casa correspondente, preencher a pendência, rodar o checklist do `CLAUDE.md` se envolver categoria nova.

---

## 6. Rodar / produção

**App em produção:** `https://sharpen.bet/` (www.sharpen.bet → Railway)

Para rodar localmente:
```
cd app
pip install -r requirements.txt
# .env na raiz do Planilhador com ANTHROPIC_API_KEY e DATABASE_URL
uvicorn main:app --reload
# Abrir http://localhost:8000
```

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/sharpen`, renomeado de `extrator` na sessão 129). Deploy automático via Railway conectado ao GitHub — push dispara deploy.
