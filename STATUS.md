# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-26 (sessão 203 — **"a bet365 do Marlon está duplicando ou não está encerrando": nenhum dos dois. Ela estava perdendo bilhete pela JANELA da tela.** **Sintoma do Feca:** a casa mostrava **35** apostas abertas, o painel mostrava **61 aguardando resultado** + **116 aguardando informação**, depois de rodar 48h finalizadas + 48h em aberto. **Diagnóstico por SELECT em produção, não por leitura de código:** **(1) Zero duplicação.** As 61 abertas têm **todas** código `BR`; nenhum código se repete na conta; nenhum "miolo" de recibo aparece duas vezes. Das 4.046 linhas, só **1** par tem mesma descrição+stake com códigos diferentes, e são duas apostas legítimas (uma `W` e uma `L` no mesmo mercado, 17/07). **(2) Os 116 "aguardando informação" não são bug:** são exatamente os 116 bilhetes do lote do dia, todos sem tipster. É o "Sugerir tipsters" não rodado. **(3) As 61 abertas se partem em dois grupos:** **35** tocadas no lote de hoje, que **batem exatamente** com o contador da casa, e **26** resíduo dos lotes de 25/07 01:34 e 01:38, com `atualizado_em` congelado lá. **(4) O UPSERT está certo e sempre esteve:** os dias 14/07 a 23/07 têm **zero** abertas nessa conta. Tudo que volta na captura, fecha. **Causa real:** as 26 **não voltaram**. A captura de abertas trouxe 35, o total exato da casa, logo as 26 já tinham liquidado; a de encerradas 48h trouxe 86 bilhetes, **todos INSERT novo**, nenhum deles entre os 26. Pelo volume da conta (50 a 86 apostas/dia), 48h de encerradas seriam 110+. **Mecanismo, no código:** o `b3_inject` é **100% passivo**, o parâmetro `dias` nem é usado para filtrar; ele só enxerga os summaries que a **própria página** baixou. O summary pagina (cursor `PT=` no header) e o "Mostrar Mais" é não-automatizável (s180). Lista não expandida, ou aposta colocada antes da janela, é bilhete que não chega, **em silêncio**. Pior: aberta que sai da janela fica presa **para sempre**, porque a cada dia se afasta mais dela. **CONFIRMADO AO VIVO pelo Feca, é o que fecha a questão:** uma passada de `Período` sobre 19 a 21/07 fechou **8** das 26, e o total da conta ficou em **4.046 linhas antes e depois** — zero inserção, UPSERT puro, nada duplicado. Restaram **20** presas (17 de 25/07, 2 de 24/07, 1 de 20/07). **Regra gravada no canônico** (`CASA_BET365 §2`, aval do Feca): `Últimas 24/48 horas` não cobre aposta **colocada** antes da janela mesmo que ela tenha liquidado dentro; para reconciliar abertas antigas rode `Período` **desde a data em que a aposta foi feita**, não desde a data do jogo; e a captura é passiva, então expanda a lista antes e confira o `[SharpenUp] Bet365 API: N bilhete(s) · com código=X/Y` no console. **Higiene, achada no caminho:** o commit `d7f82c4` (outro terminal) subiu as fixtures da bet365 para um repo **PÚBLICO**. Nome, endereço e CPF o Feca já tinha redigido; sobravam cidade, user-agent e **device ID**, agora redigidos também. O histórico do git guarda o que já foi pushado e **não houve rewrite** (force push no `main` dispara deploy no Railway; risco não compensa o dado, que é leve). **Nada de produção foi tocado:** só `casas/`, `STATUS`, `HISTORICO` e a fixture. **PENDÊNCIAS honestas:** (1) as **20 presas restantes** exigem mais passadas de `Período` sobre 24 e 25/07, o Feca estava rodando; (2) o **guard de resíduo NÃO foi construído** — proposto e aguardando decisão: ao salvar um lote, comparar as abertas que o banco já tem com as que voltaram e sinalizar em âmbar as que sumiram dos dois lados, na mesma família do guard `salvou N × grade 0` da s195; (3) a bet365 segue **sem caso no harness**, agora sem desculpa (as fixtures estão no repo desde a s202). Ver [[bet365_captura_api]] · [[extracao_perda_silenciosa_chunk]]. **Anterior: s202 abaixo.**)_

_Anterior: 2026-07-26 (sessão 202 — **Faxina do backlog: duas pendências listadas já estavam fechadas, e os payloads reais da bet365 entraram no repo.** **(1) Backlog mentindo — conferido com as funções REAIS, não por leitura:** `conferir_cobertura("[Código: JR8714690761I]")` devolve `esperados: 1` (a bet365 **está** coberta desde a `831f97f`, que trocou as regexes por formato por um **gabarito genérico de marcador** — casa nova entra sem regex) e `_CASAS_MARCADOR_CODIGO` já contém `PINNACLE` (e `TIVO`) desde a `7cf11ae`. Os dois itens seguiam no §5 como se estivessem abertos; foram removidos. Sessão que "conserta" o que já está consertado é a mesma perda de uma sessão que não conserta nada. **(2) Fixtures da bet365 resgatadas:** `harness/fixtures/bet365.summary.txt` + `bet365.confirmation.txt` — os payloads REAIS (`F|00;…`) do bilhete com **bet builder**, que quebrou o parser três vezes (registro `04` ignorado, `02` lido como perna, `TP=00010101000000` virando "01/01/0001"). Estavam só numa pasta temporária do Windows. **Pendente:** a bet365 é a única casa de robô **sem caso no harness** — o material bruto agora está no repo, falta escrever `casos/bet365.mjs`. Nada de produção tocado nesta sessão. Ver [[bet365_captura_api]]. **Anterior: s201 abaixo.**)_

_Anterior: 2026-07-26 (sessão 201 — **Pinnacle: o gêmeo do erro da Betfair, fechado — a odd exibida deixa de ser autoritativa em `W`.** A s199 corrigiu o `CASA_BETFAIR §6` e **deixou o achado anotado**: a `CASA_PINNACLE` repetia a mesma instrução em **dois** lugares. **§6** ("a Pinnacle não tem boost, **por isso** a odd exibida é autoritativa") e **§11** ("sem boost e sem cashout → a odd exibida é autoritativa para W/L/V/HW/HL. O `Retorno÷Stake` global **daria o mesmo valor**"). **Três defeitos, não um:** (a) a conclusão não decorre da premissa — não ter promoção significa só que não há nada a caçar; (b) arquivo de casa **redefinindo regra global** viola o invariante 2; (c) "daria o mesmo valor" é premissa frágil — **basta a casa arredondar** para a igualdade cair. **Diferença em relação à Betfair, que mudou o desenho do fix:** lá o §11 já estava certo e bastou o §6 apontar para ele; aqui **o §11 ERA o segundo trecho errado** — não havia seção correta para onde apontar, então ela precisou ser **construída**. O §11 novo traz a tabela por resultado, colada na global (`MASTER_RESULTADO §2`): **`W` = `Retorno ÷ Stake` = `(Stake + Vitória/derrota) ÷ Stake`, nunca a exibida** · `L`/`V`/`HW`/`HL` e abertas = exibida · fallback global (`W` sem retorno legível → exibida). O insumo já estava dentro do próprio §11 e **contradizia a frase de cima no mesmo parágrafo**: `Vitória/derrota` é P&L **líquido**, logo `retorno total = Stake + Vitória/derrota`. **Decisão do Feca (é ela que fecha a questão):** a diferença de casas decimais e o arredondamento tornam a conferência `Retorno ÷ Stake` **sempre necessária e autoritária** — travar a odd da visualização é risco, mesmo sem boost. Por isso o texto **não** diz "confira quando divergir": diz que em `W` a odd **sai do dinheiro, ponto**. A Pinnacle é ainda mais exposta que a Betfair — exibe a odd com **3 casas** e o P&L ao **centavo**. O exemplo que sustentava o texto velho (`3066865337`: 400 + 243,6 = 643,6 ÷ 400 = 1,609 ✓) ficou no arquivo **com o sinal trocado**: é ilustração de que costuma bater, rotulada como **coincidência, não autoridade**. **Terceiro trecho, achado no caminho e corrigido junto (aval do Feca):** `extensor/content.js:1181`, o comentário que descreve o bloco que a IA lê, dizia a mesma frase — "a odd exibida é autoritativa; P/L é só cross-check". É comentário (não muda comportamento — o `formatTicketPN` emite `Odd total:` + `· P/L` e quem decide é a IA), mas ficava no lugar exato onde alguém vai entender o campo, e o §11 novo diz o **oposto**: o P/L **não é cross-check, é o insumo**. **NÃO verificado nos dados:** a Pinnacle segue **sem fixture** no harness (só Betfair, KTO e Tivo têm) e o banco guarda stake e odd, **nunca o retorno** — então "daria o mesmo valor" não foi refutado com bilhete real, apenas **deixou de ser afirmado**. Fechar isso exige o JSON do `POST /member-service/v2/wager-filter` → `fixtures/pinnacle.*.json` + `casos/pinnacle.mjs`, como foi feito na Betfair. Gates: `audit_casas` **15/15 sem FAILs** · `audit_sharpenup` **15/15 sem FAILs** · harness **3 casos / 65 bilhetes verde** · `node --check` OK. Backup `Backups/casa-pinnacle-odd-w/`. Ver [[betfair-data-mes-com-ponto]]. **Anterior: s200 abaixo.**)_

_Anterior: 2026-07-26 (sessão 200 — **Polymarket: "por que uma aposta do dia 13 aparece como aberta?" — ela não estava aberta, estava ANULADA, e a pergunta destampou 4 defeitos de uma raiz só.** **Sintoma do Feca:** apostas antigas presas em "aguardando resultado" (13/07 e 16/07). **Prova ao vivo (API da carteira, não dedução):** as 2 presas vêm `redeemable: true` + `curPrice: 0.5` + `currentValue > 0` — assinatura da resolução **50/50** (mercado anulado: cada cota paga $0,50). **Raiz:** `fechados = redeemable AND currentValue < 0.01`. O `redeemable` **sozinho** já significa resolvido, e o `currentValue < 0,01` só é verdade na DERROTA; **anulada** (0,5) e **vitória ainda não resgatada** (1,0) valem dinheiro, falhavam o teste, caíam no complemento `ativas` e viravam bilhete ABERTO **para sempre** — só sairiam de lá se o Feca resgatasse na mão. **Os outros 3, achados no mesmo fio:** (2) anulada JÁ resgatada virava W/L **cheio** com o dobro da odd — 7 casos, o `Map 3 Total Rounds` marcava −R$462 onde o real era −R$67; (3) **comprar os DOIS lados** do mesmo mercado virava **duas vitórias** — o `_reconciliar_redeems` agregava por `conditionId` e o `_split_multibuys` carimbava o mesmo W nas duas pernas (5 mercados; `KT vs Kiwoom` marcava +R$868 onde o real era +R$28, e 5 derrotas contavam como vitória no Win Rate); (4) **venda antecipada (`SELL`) era ignorada pelo módulo inteiro** e a aposta **não gerava linha nenhuma** na planilha. **Desenho:** o resultado passa a sair de **quanto cada cota pagou na liquidação** (`_payouts_por_lado`), não de um P/L agregado por mercado, e a régua é a de cashout do `MASTER_RESULTADO §5.6` — **W com odd = retorno ÷ stake** (decisão do Feca). Na vitória cheia isso **É** `1/preço`, então devolvemos a odd de entrada e **o histórico provado não muda um dígito**. A reconciliação agrupa por **`conditionId` + `asset`**: cada lado é aposta própria e pode até vir de outro tipster. **Armadilha que quase virou regressão — pega pelo gate, não por sorte:** `outcomeIndex: 999` **não** é "anulado", é índice **NÃO INFORMADO** — a Polymarket usa o mesmo marcador no resgate via adaptador de *negative-risk* (o `conditionId` sai com uma fila de zeros), onde a cota pagou **$1 cheio**; lê-lo como anulado cortou uma vitória real pela metade (`Z10 vs Ilbirs`: R$241 → R$14). Quem desempata é **o valor pago**, e a regra foi **validada contra os 180 resgates da carteira**: 172 conferem pelo índice ao centavo, 7 anulados (metade das cotas), 1 negative-risk (cheio), **zero ambíguos**. **Gate de aceite (é o que dá confiança):** rodar o código **velho e o novo** sobre o MESMO snapshot da carteira → **389 linhas, nenhum `codigo_bilhete` alterado, nenhuma linha perdida**, 375 byte a byte idênticas, **exatamente as 13 diagnosticadas mudaram**, mais 1 nova (a vendida). Cada corrigida passou a bater com o extrato dentro da folga de taxa/slippage já documentada (R$3–13). **Códigos preservados de propósito:** o índice `__i` é numerado sobre TODAS as compras do `conditionId`, não por lado — numerar por lado mudaria o código dos 10 bilhetes de dois lados e **o re-sync duplicaria o histórico**. **Gates:** **225 passed** (+13 novos, incluindo o caso negative-risk e o pó de cota na venda total) · `audit_casas` sem FAILs · verificação **ao vivo**: 389 resolvidas, **0 presas em aberto**. `CASA_POLYMARKET §3/§5/§7` reescritos. Backup `Backups/polymarket-resolucao-anulado-2026-07-26/`. **ACHADO PRÁTICO para o Feca:** o painel mostra portfólio de **$109,82 com 0 posições ativas** — é dinheiro **liquidado e não resgatado** na carteira (as 2 anuladas); vale clicar em resgatar na Polymarket. **5º DEFEITO, achado DEPOIS pelo Feca ("tem certeza sobre essa aposta em aberto? ela tá com data do dia 20") — e ele estava certo:** eu tinha dito que a MOUZ de 20/07 "resolveu entre o print e agora". **Errado: ela nunca ia resolver.** Era linha **órfã**. **Prova (SELECT em produção):** o mercado tem **3** linhas — `cid` cru (20/07, $21, odd 2,5, **aberta**) + `cid__0` (L, lado MOUZ, $31) + `cid__1` (W, lado Nuclear, $21). A crua é duplicata exata da `__1`. **Causa (pré-existente, independente dos 4 acima):** o código do bilhete depende de **quantas compras** o mercado tem — 1 compra grava `cid`, e quando entra a 2ª o coletor passa a emitir `cid__i`; a linha antiga **sai do radar do UPSERT** e congela em "aberta" para sempre. O docstring antigo alegava estabilidade ("compra nova entra como `__N` no fim"), mas isso só vale de 2 compras em diante — **o buraco é a transição 1→2**. **Cobertura conferida, não estimada:** 390 linhas no banco × 389 emitidas pelo coletor = **exatamente 1 órfã** em toda a base, só do Feca. Como está "aberta", não distorce P/L nem Win Rate — só infla a contagem e mostra fantasma. **Fix estrutural (decisão do Feca):** `/polymarket/sync` herda o tipster da linha crua ANTES do upsert e a remove DEPOIS, via `remover_bilhetes_supersedidos` (`repository.py`) — o SQL é **auto-verificável**: só apaga o código cru se as fatias irmãs já existirem na MESMA conta (`split_part`, não `LIKE`, que trataria o `_` do sufixo como curinga), então upsert que falhou não apaga nada. **Validado contra o banco real dentro de transação com ROLLBACK** (sem Postgres local nem docker aqui): apagaria exatamente a órfã, compra única → 0, dono errado → 0, e 390 linhas antes e depois. +4 testes em `tests/test_repository_db.py` (gate `TEST_DATABASE_URL`, rodam no CI). A órfã existente **o Feca apaga no X da grade** (é 1 clique e ele vê o que remove). **PENDÊNCIAS honestas:** (1) o re-sync corrige as 13 linhas erradas por UPSERT, mas **só vale no banco quando o Feca clicar em Sincronizar**; (2) os 4 testes de DB **não rodaram localmente** — dependem do Postgres do CI. Ver [[polymarket_guarda_chuva]] · [[pl_calculo_derivado]] · [[dedup_gap_sem_codigo_reextracao]]. **Anterior: s199 abaixo.**)_

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
