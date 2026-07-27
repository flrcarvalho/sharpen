# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-27 (sessão 210 — **VaideBet entra no SharpenUp: 9ª casa de captura, do reconhecimento ao registro completo.** A casa **não existia em nenhuma das duas camadas** — nem `casas/CASA_*.md`, nem `_CASA_DISPLAY`, nem nos mapas de favicon. Nasceu inteira nesta sessão. **Motor: Altenar/BIA** (`sb2bethistory-gateway-altenar2.biahosted.com`), o mesmo padrão que outras `.bet.br` usam — se outra casa Altenar entrar, o `vb_inject` é o espelho. **Modo: API + replay** (`POST /api/WidgetReports/widgetExpandedBetHistory`), decidido por prova, não por gosto: a lista **não carrega sozinha** (a tela tem "Mostrar mais apostas", do tipo que checa `isTrusted` e não se automatiza — lição da bet365) e vem de 10 em 10. O robô pagina por `pageNumber` na própria API e **ignora o botão**. **As duas abas são o array `statuses` do CORPO** — Processado `[1,8,2,4,18]` · Aberto `[0,10,3,20,17]` — mesma URL; o robô varre as duas partindo de qualquer uma que o operador tenha aberto. **Fim autoritativo: `isLastPage:true`**, sinal explícito da casa. **Autenticação é `Authorization: Bearer` de OUTRA origem, não cookie** → o replay reusa os headers exatos da requisição real (`credentials:"include"` sozinho voltaria 401). **A armadilha central desta casa, travada em 3 testes:** em bilhete **ABERTO** o `totalWin` **já vem preenchido com o valor potencial** (`5236294996`: stake 30, `totalWin: 90`, e o card mostra "Ganho total R$90,00" como promessa). Ler isso como retorno realizado transformaria **toda** aposta em aberto em vitória fantasma — a mesma família do incidente da Betano. Só `status:1` autoriza a régua do W; a aberta sai com `Retorno potencial:` e **nunca** com `Retorno:`. **Enum de status provado contra o card:** `0` aberta · `1` ganha · `2` perdida. Os outros 7 valores que as abas pedem (3,4,8,10,17,18,20) **nunca apareceram num bilhete** → sobem **crus**, marcados "a conferir", jamais viram W/L por dedução. **Data:** `createdDate` (colocação, rodapé do card) × `eventDate` (evento, dentro do card), ambos ISO `Z` = UTC → São Paulo. Quem vai para o TSV é o **evento** — e as duas abertas provam que divergem de DIA (colocadas 26/07 21:1x para jogos em 27/07). **Odd:** `totalOdds` **já boostada**; o número riscado do card é `preBoostedPrice` e a tela **trunca** (`2.3334` → `2.33`). Dois boosts: `GOLDEN BOOST` (`boostProperty 3`) e `ODDS TURBINADAS` (`1`). Nos 3 W a odd declarada explica o retorno ao centavo, então dinheiro e odd concordam. **Test-first, como manda o guia:** o harness veio **antes** do código e ficou vermelho pelo motivo certo (`vb_inject.js` não existia). Caso `casos/vaidebet.mjs`: **17 conferências** — 12 bilhetes reais (10 resolvidas + 2 abertas, cada valor lido do card), a paginação ativa (a página 1 responde `isLastPage:false` e o inject **tem** de pedir a 2), um clique trazendo as duas listas partindo de qualquer aba, e 3 casos **sintéticos** rotulados como tais (status desconhecido não vira resultado · múltipla de jogos diferentes não é "mesmo jogo" · `cashOutValue` preenchido não some do bloco). **Um bug real caiu no processo:** o guarda anti-loop lia "0 bilhete novo" como fim — mas a página 1 já tinha chegado passivamente, então a paginação morria nos 10 primeiros. Repetição não é fim; **vazio** é. Agora só para depois de **duas** páginas seguidas sem novidade, com `isLastPage` como critério e o teto de 60 páginas como rede. **Registro completo (12 pontos):** `CASA_VAIDEBET.md` (15 seções) · `_CASA_DISPLAY` · `_CASAS_MARCADOR_CODIGO` (chunking + pré-dedup) · `_MODO_POR_CASA` · `_HOSTS_POR_CASA` · `CASAS_CONECTAVEIS` · `NOMES`/`DOMINIOS` · os **três** mapas de favicon · `popup.js` (`CASA_HOSTS` + dispatch) · `manifest.json` (content_script + bump **0.6.29 → 0.6.30**) · `CODIGO_EXEMPLO` no audit. **Gates:** harness **5 casos / 97 bilhetes verde** · `audit_sharpenup` **16 casas sem FAIL** · `audit_casas` sem FAIL · `pytest` **231 passed** · `check-tokens` OK · `node --check` nos 3 JS + manifest. Backup `Backups/sessao209-vaidebet-sharpenup/`. **PENDÊNCIA honesta — nada disto rodou na casa ao vivo:** falta o operador recarregar a extensão + **Ctrl+Shift+R** na aba da VaideBet e conferir contagem/datas/odds no dashboard. **Sem amostra de:** cashout (a conta não tem nenhum; `cashOutValue` vem 0 até nas abertas com botão ativo, o valor real está noutro endpoint), bilhete anulado/devolvido, múltipla de jogos diferentes, e esporte fora de futebol/beisebol. **Mapa de mercados fechado na mesma sessão, contra o MASTER — 4 dos 5 "pendentes" não eram pendência, era eu não ter lido:** `Chutes a Gol - <Jogador>` → **`Chutes no Gol`** (o §Player Props diz literalmente *"NÃO usar `Player Props` quando o objeto apostado tiver categoria própria, mesmo que o mercado envolva um jogador específico"*, e o precedente canônico é o cartão de jogador → `Cartões`; a regra "jogador → `Player Props`" existe **só** como exceção de `Pontos`/`Sets`) · `Marcador - <Jogador>` + `Qualq. Altura` → **`Anytime`** (PT-PT de "anytime") · `<Time> para marcar em ambos os tempos` → **`Team Props`**, padrão já firmado em `CASA_BETNACIONAL §9` e `CASA_LOTTU §9` · beisebol `Mais de/Menos de (incl. innings extra)` → **`Corridas`**. **A 5ª foi decidida na hora pelo Feca:** `Winner & total (incl. extra innings)` — mercado **combinado** (resultado + total de corridas numa seleção só), onde `ML` esconde o total e `Corridas` esconde o resultado — vai para **`Outros`**, com os dois componentes na Descrição. Decisão **local** da casa; o `MASTER_APOSTAS` segue **sem regra geral para combinado**, e o padrão existe no futebol (`Resultado & Ambas Marcam`) — fica no Feedback da `CASA_VAIDEBET` como candidato a subir ao global. **O `audit_casas` pegou um deslize meu no caminho:** deixei `"Chutes no Gol — ver nota abaixo"` dentro da célula da tabela, o que registra uma **categoria órfã**; a coluna `Aposta global` só aceita o nome exato da categoria (fix `e4aa0af`). **Anterior: s209 abaixo.**)_

_Anterior: 2026-07-26 (sessão 209 — **Betano: a aba "Em aberto" exportava 25 bilhetes onde a tela mostra 5.** **Sintoma do Feca:** rodar o robô na aba `Em aberto` coletou **25** bilhetes: as 5 abertas corretas (batem com "Apostas abertas (5)" do painel de saldo) **mais 20 liquidadas**, que não estão naquela tela. **Prova, não dedução:** as 20 têm resultado e retorno, dado que **só existe** na resposta `settled=true` — ou seja, a aba Liquidada tinha sido carregada antes, na mesma sessão de página. **Causa (`content.js`, `roboBetanoPassive`):** `bnById` é acumulador da **sessão da página**. A Betano é SPA, trocar de aba não recarrega, então o hook guarda as duas listas ao mesmo tempo, e o `processar()` varria o mapa inteiro. A variável `naAbaAberta` já existia, mas só decidia se a janela de dias corta e qual sinal de fim de paginação vale; **não filtrava o que era emitido**. **Dois estragos, um deles silencioso:** (a) token à toa, porque o pré-dedup do `/extrair` só descarta o que já está **resolvido** no banco; (b) **perda das abertas** — o mapa é percorrido em ordem de inserção, e com o campo "parar no ID" preenchido com um bilhete **liquidado** o `travado` disparava antes de chegar nas abertas, sem erro na tela. **Fix:** uma guarda no `processar()`. Cada rodada exporta só a lista da aba que está na tela; para pegar tudo, rode nas duas abas. Regra gravada no canônico (`CASA_BETANO §2.0`). **Primeiro caso da Betano no harness** (`casos/betano.mjs`): aba Em aberto só solta abertas, aba Liquidada só solta liquidadas, `stopId` de liquidado não decepa as abertas, `stopId` da própria aba continua parando onde deve. **Desligando a guarda de propósito o caso fica vermelho com 6 falhas, uma delas "saíram 0 de 5 abertas" — a perda silenciosa reproduzida, não teorizada.** **Gates:** harness **4 casos / 80 bilhetes verde** · `audit_sharpenup BETANO` sem FAILs. Bump da extensão `0.6.28 → 0.6.29`. Backup `Backups/betano-abertas-por-aba/`. **Nada de backend tocado.** **Pendência fechada na mesma sessão — o Feca mandou o payload real e o caso virou completo:** fixtures `betano.open.json` (3 abertas, sem `LastId`) + `betano.settled.json` (5 liquidadas, `LastId: 20707886166`) + `betano.settled2.json` (pág. 2, outright de F1). **15 conferências**, cada valor batido contra o print da casa E contra o texto que o robô exportou ao vivo — os blocos saem **idênticos, linha a linha**. Prova o fim autoritativo **nos dois sentidos** (sem `LastId` → `fimOpen` true · com `LastId` → `fimSettled` false) e que um sinal não vaza para a outra lista. Armadilhas travadas: `Accumulator: "{number}-fold"` é **placeholder cru** da API (vira "5-seleções" pela contagem de pernas); **aberta não tem `Return`**, só `PossibleWinnings`, então nenhuma linha de retorno sai (comportamento seguro, agora protegido); em `L` a odd é a **exibida** mesmo com boost (2,75, jamais `Return÷Stake` = 0); `VoidNotStartingPlayersSelected` é condição, não resultado. **Segundo teste de quebra revelou um buraco que eu não tinha visto:** desligando o `oddW`, o **valor** da odd continuou certo — porque nenhum W desta fixture tem `Retorno÷Stake` diferente da odd exibida — e só o rótulo `(= Retorno ÷ Stake)` sumiu. Por isso o caso confere o **rótulo em separado**; sem ele a regressão passaria batido. **ACHADO NOVO, medido e NÃO consertado (precisa de decisão):** a Betano turbina de **duas** formas e o robô só enxerga uma. `OddsBeforeEnhancement` (odd turbinada na seleção) **já está** dentro do `Return` — ok. Mas o **`BonusOffer`** ("Criar Aposta Turbinada +25%") fica **FORA**: no `20712642016` o `Return` é 902,70 (= 306 × 2,95) e os **R$149,18** do bônus não entram em lugar nenhum; no `20705552856`, mais **R$84,15**. São **R$233,33 só nesses dois bilhetes**. Como a odd de W sai de `Return ÷ Stake`, esse dinheiro some do P/L. Falta saber se cai como **saldo real ou bônus** — `CASA_BETANO §6` (boost) e `§8` (bônus) seguem em **TODO**, então não há regra para aplicar. Conferir em `Histórico → Transações`. **Medido e não consertado (decisão do Feca):** rodar a aba Em aberto de novo reenvia as mesmas abertas ao modelo, porque o pré-dedup não pula bilhete em estado `aberta`; no volume atual não compensa mexer no backend. Ver [[betano_abertas_e_upsert]]. **Anterior: s208 abaixo.**)_

_Anterior: 2026-07-26 (sessão 208 — **Mapas de favicon limpos: os três param de mentir sobre quais casas existem.** Fecha a pendência aberta na s206. **(1) Aliases mortos removidos** do `index.html` e do `inicio.html`: `BetBra` · `Multibet` · `Faz1be` · `7k Bet` · `Esportiva Bet`. Essas grafias **não existem mais no banco** (unificadas na s204) e a `casa_canonica` impede que voltem — as linhas só faziam o mapa mentir. Diferença só de **caixa** também não precisa mais de alias: o lookup casa por caixa-baixa desde a s204. **(2) No `data.js` era o OPOSTO:** a chave era `Faz1bet` (grafia aposentada) e **não existia** `Faz1Bet` (a que ficou) — **renomeada**, não removida; sem isso a limpeza teria deixado a casa sem ícone no dash. **(3) A limpeza revelou um buraco:** o `data.js` **não tinha domínio para `Aposta Ganha` nem `Pagol`** — as duas caíam no fallback **só no dashboard**, enquanto os outros dois mapas já as conheciam desde sempre. Preenchidas com os domínios existentes. **Estado final, conferido contra as 45 casas do banco:** `index.html` **45 chaves para 45 casas, um-para-um**; `inicio.html` e `data.js` com 46 — as 45 + `Betao`, alias **sem acento** de `Betão`, **mantido de propósito** (o lookup casa caixa, não acento; tirar deixaria a casa exposta se a grafia sem acento reaparecer num import). **Cobertura: zero casa sem domínio nos quatro mapas.** Bump `data.js?v=8→9`. Gates: `node --check` no `data.js`, blocos JS inline sem erro, `check-tokens` OK. **Nada de backend tocado.** **Anterior: s207 abaixo.**)_

_Anterior: 2026-07-26 (sessão 207 — **"faça uma extração do ZERO na poly e bata que não há erro algum": o dinheiro estava impecável, a CLASSIFICAÇÃO tinha 40 linhas erradas.** **Método:** script de auditoria com **20 conferências**, cada uma com um número — coleta pela API do zero e reconcilia contra o extrato on-chain. **A conferência que mais vale é a nº 3, porque NÃO é circular:** para cada um dos 377 mercados, o payout que o modelo deduz tem de reproduzir o dólar que a blockchain de fato pagou — **bateu nos 180 resgates, centavo a centavo**. **Dinheiro: 8/8 OK** (389 linhas × 389 compras · códigos únicos · P/L difere do real por **$445,32 = exatamente** a taxa de entrada de 1,73% · retorno bruto W+V == resgatado + vendido + parado, $24.107,32 dos dois lados). **Classificação: 40 linhas erradas.** **Raiz:** no `_categoria` o teste genérico de over/under rodava **antes** das regras por esporte; como a Polymarket escreve quase tudo como `O/U X`, o genérico vencia sempre e **escanteio, gol, ponto e round caíam todos em `Player Props`** — 35 linhas, **nenhuma de jogador**, contra o `MASTER_APOSTAS §1` (categoria = objeto apostado) e o `§7` (mercado específico > genérico). Reclassificado: **17 Escanteios · 8 Gols · 5 Rounds · 2 Pontos · 1 Corridas · 3 ML**; sobrou **1** Player Props — o strikeout do arremessador, que o `§6 Baseball` manda ser exatamente isso. **Mais dois defeitos no caminho:** (a) o regex casava **`under` DENTRO de palavra** — `Spurs vs. Th·under` e dois jogos do torneio `Th·under·pick` viravam mercado de total; agora tem `\b`; (b) faltavam os prefixos de slug **`col`** (Conference League — o slug **não** usa a sigla oficial `uecl`), **`per1`** (Liga 1 do Peru) e **`auc`** (Australia Cup): 7 jogos de futebol em esporte `Outro`. **Categoria `Rounds` criada (decisão do Feca) com a REGRA DE PROPAGAÇÃO inteira:** `MASTER_APOSTAS §3` (tabela) · `§4` (sinônimos) · `§5` (regra + o que **não** é Rounds) · `§6` (**seção MMA/Boxe criada — o MASTER não tinha NENHUMA regra de MMA**) · `§7` (Rounds > Player Props, ML > Rounds) · `§9` (validação 22); `MASTER_DESCRICAO §12.5` (exemplo); `CASA_POLYMARKET §9` — **o mapa da casa TINHA a regra errada escrita** (`over/under → Player Props`), ou seja o doc ensinava o bug. `audit_casas` sem FAILs. **Bloqueio estrutural, mesma família da odd da s205:** `esporte`/`aposta`/`descricao` **nunca** eram atualizados (só no INSERT) → a correção do classificador não alcançaria as 389 linhas. Entraram na exceção `origem='sync'`. **Extração rodada chamando a FUNÇÃO DA ROTA** (não replicando a lógica, que divergiria dos passos): **389 coletados · 0 inseridos · 389 atualizados · 0 alertas**. **Reauditoria: 20/20 OK** — banco × coletor com **0 campo divergente** e P/L idêntico (**−R$5.732,60** dos dois lados; era −R$3.158,44 antes da s205 chegar ao banco). **Gates:** **231 passed** + **13 passed** no harness de DB (Postgres real, +2 casos: sync refresca classificação, IA não sobrescreve) · `audit_casas` sem FAILs · `check-tokens` OK. Backup `Backups/categoria-rounds-mma/`. **PENDÊNCIA honesta:** o painel segue **~1,7% otimista** por não contabilizar a taxa de entrada da Polymarket (~R$2.250 no acumulado) — é decisão de projeto documentada (odd limpa = 1/preço), **não** bug, mas agora está medida. Ver [[polymarket_liquidacao_payout]] · [[betano_abertas_e_upsert]]. **Anterior: s206 abaixo.**)_

> **Histórico completo das sessões 206 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
