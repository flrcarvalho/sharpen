# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-25 (sessão 193 — **Betfair destravada: a casa trocou `"18-jul-26"` por `"18-jul.-26"` (mês abreviado COM PONTO) e isso zerou 5 dias de bilhetes.** **Sintoma:** o Feca extraiu várias vezes e "não vinha nada". **Prova, não dedução:** o Postgres mostrou última gravação de Betfair em **20/07 02:27 UTC** (códigos `O/…0001770-1777`) e **zero** linha criada OU atualizada desde então, enquanto 534 bilhetes de 9 outras casas entraram no mesmo dia → nada de sessão/ponte/backend. `uso_tokens` mostrou **4 extrações de Betfair no dia, US$ 0,83, ~5,4k tokens de output cada** → a IA rodou e produziu. Os logs do Railway (`victorious-generosity`/`extrator`) não trouxeram `cobertura:` nem `id-fix` → o TSV voltou **completo e com os códigos certos**. Logo, a perda era depois da IA. **Causa raiz, achada no JSON cru da API (o Feca colou o `POST /activity/sportsbook` — ele cobrou "não é mais fácil investigar a API?" e estava certo, foi o caminho curto):** `"placedDate": "17-jul.-26 13:45:15"`. O `_dbrBF` (`content.js:751`) casava `([a-zç]{3})` e esperava `-`, encontrava `.` → **data vazia em 100% dos bilhetes**. **Fix:** ponto opcional (`\.?`) — estritamente permissivo, o formato antigo segue casando (testado: `18-jul.-26`→`18/07/2026` · `12-jul-26`→`12/07/2026` · `15-set.-26`→`15/09/2026` · lixo→vazio). **Por que UM ponto derrubou tudo (o amplificador, ainda ABERTO):** `Data` é a 1ª coluna do TSV; vazia, ela vira um TAB inicial, e o `parse_tsv` (`repository.py:287`) faz `line.strip()` que **engole esse TAB** → todas as colunas deslocam uma casa (`odd` recebe `'W'`) → `validar_linhas` rejeita 100% → `/salvar` devolve "0 novos · N alertas" e **não grava nada, sem erro**. Reproduzido com o texto real do Feca (6/6 linhas rejeitadas, `odd inválido — valor 'W'`). É bug **GERAL**, não da Betfair: vale para qualquer casa que legitimamente venha sem data. **O fix do `_dbrBF` subiu carona no commit `9992829` (KTO), sem commit próprio** — trabalho paralelo do KTO estava na mesma árvore. **CORRIGIDO na mesma sessão (commit próprio, backend-only):** (1) `parse_tsv` — `.strip()` → `rstrip("\r\n")` + strip por CAMPO. Testado nos 3 casos: linha sem data entra íntegra (`data=''`, código no lugar certo), linha normal inalterada, aposta aberta sem código inalterada → 3 válidas, 0 rejeitadas (antes a 1ª era rejeitada). (2) `_betfair_data` (`main.py:440`) — ponto opcional, gêmeo do `_dbrBF`; comentário cruzado nos dois para não dessincronizarem. Suíte: **191 passed, 4 skipped, 2 failed** — as 2 falhas são **PRÉ-EXISTENTES no HEAD** (provado rodando com `git stash`): `test_ordem_bet365::test_build_chunks_bet365_split_por_marcador` (cobra o marcador `[Bilhete Bet365]` que a s189 removeu de propósito — teste ficou stale) e `test_captura::test_casa_de_host_desconhecido_ou_vazio_retorna_none`. **Elas deixam o CI vermelho e precisam de um passo próprio.** **PENDENTE:** `formatTicketBF` ecoa `potentialReturn` cru, que agora chega en-US (`"1,380.00"`) — usar `_brl()` do número (exige reload da extensão, fica p/ o próximo). **NÃO validado ao vivo** — o Feca recarrega a extensão (0.6.23) + Ctrl+Shift+R na aba da Betfair, recaptura e processa (esperado: datas preenchidas e os ~5 dias entrando). Ver [[betfair-data-mes-com-ponto]] · [[betfair_captura_json]]. **Anterior: s192 abaixo.**)_

_Anterior: 2026-07-25 (sessão 192 — **KTO vira casa de API (Kambi) — aposenta o robô de texto, que estava perdendo ~90% dos bilhetes.** **Causa PROVADA (contagem, não dedução):** o Feca capturou e vieram 14 "bilhetes". Os 14 **não eram bilhetes** — eram os 14 pedaços da PÁGINA: o `coletar()` do `roboScroll` parte o `document.body.innerText` por **linha em branco**, e a lista da KTO **não tem linha em branco entre cupons** → 1 bloco gigante com o menu + os ~140 bilhetes + o rodapé, mais 13 cacos de cabeçalho/rodapé. A IA recebia esse blob como um chunk só, extraía os primeiros e perdia o resto em silêncio ([[extracao_perda_silenciosa_chunk]]). **O Feca perguntou "não é mais fácil vir por trás, F12, como nas outras casas?" — e era.** A KTO roda em **Kambi**: `GET …/player/api/v2019/ktobr/coupon/history.json?…&range_size&range_start&status`, paginação por offset com `range.more`. **Construído:** `extensor/kto_inject.js` (novo — hook fetch/XHR, normaliza, aprende a requisição real e **repagina até `more:false`**, avançando pelo `range.size` que VOLTA; replay cobre as URLs que a página disparou + variantes de `status`, então **ninguém clica "Mostrar mais"**) · `content.js` (ouvinte `ktoById`, ramo `casa==="kto"` → `roboKTOPassive`, `formatTicketKTO` com marcador `[Código: <couponRef>]`, autodiagnóstico) · `popup.js` (dispatch do injetor + `CASA_HOSTS`) · `manifest` **0.6.22→0.6.23** · `main.py` (KTO entra no chunking e no pré-dedup por `[Código:]`) · `CASA_KTO.md` §2.5 (campos da API) + §5 (de-para `betStatus`). **Armadilhas confirmadas no dado real:** `betOdds` vem **0 em toda perdida** (usar `playedOdds`); stake/odd/line em **milésimos**; ODDÃO+ tem 2 naturezas (`ODDS_BOOST` sobe a odd · `PROFIT_BOOST` sobe o lucro X%) e **`payout ÷ stake` resolve as duas** (= regra global W). **Conciliação da odd (achado do harness):** retorno é arredondado ao centavo e odd declarada é truncada em 3 casas — regra: a declarada vence **se explicar o retorno até o centavo**, senão o dinheiro manda; nunca truncar. **VALIDADO OFFLINE contra o JSON real** (harness carrega os arquivos do repo, não uma cópia): **6/6 cupons** — aberta múltipla 2,0435 · perdida 6 · W 2,15 · boost 15% 2,3226 · boost odd 2 · bet builder 2,2, datas UTC→BRT batendo com o card. `node --check` verde nos 3 JS + manifest, `py_compile` OK. Backup `Backups/kto-inject-api-2026-07-25/`. **NÃO validado ao vivo** — o Feca recarrega a extensão (0.6.23) + **Ctrl+Shift+R na aba da KTO** (recarregar extensão não re-injeta em aba aberta), conecta e clica "Copiar bilhetes". **Ainda sem amostra:** VOID/Nula, Recusado, cashout encerrado, `systemBets`, aposta grátis, stake dividida — o bloco leva o `Status (API)` cru e a leitura financeira, e enum desconhecido **nunca** vira W/L por chute. Ver [[extracao_perda_silenciosa_chunk]] · [[feedback-isolar-mudanca-nao-quebrar]]. **Anterior: s191 abaixo.**)_

_Anterior: 2026-07-25 (sessão 191 — **KTO: o botão "Conectar" acende — o gate da FRENTE que faltava na s190.** **Causa (provada por leitura de código, não deduzida):** a s190 pôs a KTO em modo texto no backend e eu pedi ao Feca que gerasse um código KTO no dashboard — **impossível**: `CASAS_CONECTAVEIS` (`app/static/index.html:3162`) não listava KTO, então `_casaConectavel()` → `aplicarModoCasa()` marcava o `#btn-conectar-ext` com `disabled` + `.is-off` e o title "O SharpenUp ainda não cobre esta casa — envie os prints manualmente". Sem código gerado, **nada** da s190 chegava a rodar. A s190 não estava errada, estava **incompleta**. **Fix:** `'KTO'` no Set + comentário explicando que é casa de texto SEM injetor. **Sem bump de `?v=`** (o Set é código inline do próprio `index.html`, não `.js` externo). **Resto da cadeia conferido linha a linha e de pé:** `modo_da_casa("KTO")="texto"` (`captura.py:49`) · `/captura/conectar` sem whitelist de casa (`main.py:1508`) · `popup.js:169-176` → `inj=null` p/ KTO (correto: sem interceptor de API, só `START_ROBOT`) · `popup.js:303-305` → cai em `isBetSup` (janela de dias + stopId + "Copiar bilhetes") · `content.js:570` → ramo `else` → `roboScroll` genérico · `content.js:496` `re2` casa "24 de jul. de 2026" · `CASA_HOSTS` sem KTO no popup → `hostBate` devolve `true`, **não bloqueia** (só perde a mensagem de erro amigável). Backup `Backups/kto-botao-conectar-2026-07-25/` (só `index.html`). **NÃO validado ao vivo** — o Feca seleciona KTO na Extração (esperado: botão clicável), gera o código, conecta, abre `kto.bet.br/app/.../historico-de-apostas` e clica "Copiar bilhetes". **Adiado p/ pacote separado (exige bump+reload da extensão, não misturar com o código da bet365 s182-189):** `CASA_HOSTS["KTO"]` no popup + favicon `kto.com`→`kto.bet.br` nos 3 mapas. Ver [[feedback-isolar-mudanca-nao-quebrar]]. **Anterior: s190 abaixo.**)_

_Anterior: 2026-07-24 (sessão 190 — **KTO vira casa de robô de TEXTO na captura (SharpenUp) — backend-only, sem tocar a extensão.** **Contexto:** o `CASA_KTO.md` já existia completo (8 goldens, en-US decimal, boost ODDÃO+, regra `Recusado`) e KTO já estava registrada em `main.py`/`index.html`/popup — mas capturava só em `print` (moldura+Snap → OCR), porque `modo_da_casa("KTO")` caía no default. O Feca pediu extração via SharpenUp e escolheu **robô de texto** (mais barato, sem OCR, dado do DOM). **Fix isolado (só `app/captura.py`):** `_MODO_POR_CASA["KTO"]="texto"` (o `/captura/conectar` passa a devolver `modo:texto` p/ códigos KTO) + `_HOSTS_POR_CASA["KTO"]=("kto.bet.br",)` (backstop casa↔site do `main.py:1561`; `kto.bet.br`→KTO==KTO passa, só barra código KTO em site alheio). **SEM injetor dedicado e SEM mudança na extensão:** a lista "Minhas Apostas" da KTO renderiza o cupom inteiro no DOM, então o `roboScroll` genérico (`content.js`, o ramo `else` do dispatch p/ casa `"kto"`) rola+lê o innerText+dedupa; o corte de lookback usa a data "DD de mmm. de AAAA" que o `parseDatas` (re2) já reconhece após lowercase. O popup também já trata casa de texto nova sem alteração (cai em `isBetSup`: janela de dias + stopId + "Copiar bilhetes"). **Nenhum reload de extensão necessário** (deploy Railway backend basta) — protege o código recém-estabilizado da bet365 (s182-189). `py_compile` OK. Backup `Backups/pre_kto_texto_2026-07-24/` (só `captura.py`). **NÃO validado ao vivo** — o Feca gera um código KTO no dashboard, conecta na extensão, abre `kto.bet.br/app/.../historico-de-apostas` e clica "Copiar bilhetes" (esperado: robô rola a lista e envia o texto dos cupons; IA parseia via `CASA_KTO.md`). **Opcionais adiados (exigiriam bump+reload da extensão):** espelhar `CASA_HOSTS` no `popup.js` (mensagem de erro mais amigável) + corrigir favicon `kto.com`→`kto.bet.br` no popup/index.html. Ver [[feedback-isolar-mudanca-nao-quebrar]]. **Anterior: s189 abaixo.**)_

> **Histórico completo das sessões 189 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

**Próximo passo:**
- **Testar a KTO ao vivo (s192, nada validado no navegador).** Recarregar a extensão (**0.6.23**), dar **Ctrl+Shift+R na aba da KTO** (recarregar a extensão não re-injeta em aba já aberta), conectar e clicar "Copiar bilhetes". Não precisa clicar "Mostrar mais". Diagnóstico pelo console: logs `[SharpenUp kto_inject]` com `lista aprendida`, `cupons na resposta` e o `range` de cada página.
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
