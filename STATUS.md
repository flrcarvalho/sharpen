# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-24 (sessão 183 — **Bet365: 48h e Por período destravados — rota da confirmation derivada do `PD`, não mais chutada.** **Combate real do que a s182 preparou.** **Causa raiz provada pelo payload real (o Feca colou o `summary` do 48h no Network):** cada bilhete traz `PD=#HICO#BSSB#C<id>#D<ns>#` e o namespace MUDA por janela — 24h recentes = `D1`, **48h/Período = `D0`**. O `detalharPorRota` (`b3_inject.js`) chutava `/D1/` fixo → fora do 24h a confirmation voltava VAZIA (`confirmation sem BR`), e caía toda a cascata (sem código, sem data, grind de 8s×N, contagem inflada porque sem `BR` não deduplica). **Fix:** `parseSummary` captura o `PD` (novo campo `pd`), `mergeSummary` guarda, e `detalharPorRota` deriva a rota do `PD` (`"#" + pd.replace(/#/g,"/")` → `#/HICO/BSSB/C<id>/D0/`); sem `PD`, cai no `/D1/` legado. 24h segue idêntico (PD lá é `D1`). Manifest **0.6.16 → 0.6.17**. `node --check` verde + transform testada isolada. Backup `Backups/bet365-rota-pd-namespace/`. **NÃO validado ao vivo ainda** — o Feca recarrega a extensão (0.6.17) + Ctrl+Shift+R e testa 48h/Período (esperado: código+data completos como no 24h). **Pendente (Frente 2):** UI do popup — seletor de modo (24/48/período), scanner travado até escolher + aviso "expanda tudo antes de iniciar". Ver [[bet365_captura_api]]. **Anterior: s182 abaixo.**)_

_Anterior: 2026-07-24 (sessão 182 — **Bet365: faxina do "código antigo" (primeira tentativa) antes do combate no 48h/período.** Removido o robô de raspagem de DOM (`roboBet365DOM` + `acharScrollBet365`, ~70 linhas no `content.js`) e sua fiação de fallback — ele só disparava quando a API vinha 100% vazia e produzia bloco de texto **sem código BR nem data** (o "manco" que polui a dedup). A API por rota (s180b) é agora a **única** fonte; API vazia = aba do Histórico não aberta ou hook não injetado (recarregar com Ctrl+Shift+R). Corrigidos comentários mentirosos que ainda diziam "replay"/"driver de clique" (ambos já mortos) → agora descrevem o detalhamento por rota. Manifest **0.6.15 → 0.6.16**. `node --check` verde nos 2 arquivos, zero referência órfã. Backup `Backups/limpeza-bet365-dom-fallback/`. **Próximo (combate real):** 48h e Por período voltam `confirmation sem BR` porque a rota chuta o namespace `/D1/` (`b3_inject.js`) e ignora o campo `PD` do summary — 24h calha de ser D1 e funciona. Fix planejado: capturar `PD` no `parseSummary` e derivar a rota dele. **+ UI nova:** seletor de modo (24/48/período) no popup, scanner travado até escolher + aviso "expanda tudo antes de iniciar". Aguardando o Feca colar um registro `01` do summary do 48h/período (com o `PD`). Ver [[bet365_captura_api]]. **Anterior: s181 abaixo.**)_

_Anterior: 2026-07-24 (sessão 181 — **Bet365: caça a uma fonte passiva no domínio `www` — negativa (investigação, sem código).** Cruzando o que o SharpenUp já captura, o Feca inspecionou no F12 a família `mybetscontentapi/*` (fora do iframe de membros) para ver se algum endpoint entregava o bilhete inteiro sem o detalhamento por bilhete. **Não entrega.** `settledstats` (POST) e `playerml` (GET) são **decorativos**: devolvem escudo/cor/placar (`SS=1-1`, `S1=Goals`) e nomes de jogador (`ON`/`PN`), keyed pelo **ID numérico instável** (prefixo `BSB`/`SSB`), **sem `BR`, sem odd/stake, sem mercado em texto**. Prova de que são só enfeite: a seleção chega **pronta no request** (`st=Para Lucas Villalba Receber Cartão`) — a página já tem o conteúdo, o endpoint só desenha a figurinha do card. Busca global do DevTools (`Ctrl+Shift+F`) por time/mercado (`Bolivar`, `Mais de 2.5`) = **zero** em qualquer resposta do `www`; e o `confirmation` **não dispara ao rolar** a lista de Resolvidas. **Conclusão: não há atalho passivo por fora do `members` — o conteúdo (`BR` + jogo/mercado/liga) só existe no `confirmation`, disparado pelo detalhamento por ROTA (s180b). Nada a mudar no código.** Achado gravado em [[bet365_captura_api]] p/ ninguém repetir a caça; se um dia a lentidão incomodar, é otimizar o driver por rota, não substituí-lo. **Anterior: s180b abaixo.**)_

_Anterior: 2026-07-24 (sessão 180b — **Bet365: detalhamento por ROTA (hash) — o método definitivo, valida 10/10 sem tocar na lista.** **Contexto:** o driver de UI (s180a, abaixo) funcionava mas dependia de dois pontos frágeis: clicar "Detalhes"→"Voltar" (a lista REINICIA no topo) e o **"Mostrar Mais", que é BUGADO na própria bet365 — falha até no clique humano** (o Feca precisa clicar centenas de vezes; 984 e 1032 cliques sintéticos = 0 resultado, provado). **Virada (o Feca achou no Network/Initiator):** a confirmação de cada bilhete vive numa ROTA de hash — `#/HICO/BSSB/C<bsid>/D1/` — e o próprio `summary` já entrega essa rota em cada bilhete (`PD=#HICO#BSSB#C<id>#D1#`). O Initiator mostrou que o "Mostrar Mais" é `showMore.clickHandler`→`nextPageUrl`→`o.load` passando pelo nosso hook (`b3_inject.js`): **é a própria página que faz a chamada com o token `x-net-sync-term` (que rotaciona e não dá pra forjar) — a gente não replica, a gente DIRIGE.** **Novo detalhamento (`detalharPorRota`):** para cada bsid do resumo, `location.hash = "#/HICO/BSSB/C"+bsid+"/D1/"` → o app carrega a confirmation (com o token dele) → o hook captura código BR + jogo/mercado/liga. **Não clica na lista, não usa "Voltar", não toca no botão bugado.** **Validado ao vivo:** `driver(rota): 10 detalhe(s) · 0 falha(s) · com código=10/10`, extração completa (Dupla com 2 jogos, bet builder com pernas, eBasket `B-EBASKBLITZ4X5`). Manifest **0.6.6 → 0.6.15**. **v1 VALIDADO ao vivo (o fluxo de produção):** o operador **expande a lista do jeito dele** (o "Mostrar Mais" na marra) e o robô detalha **TODOS** por rota — testado com ~42 bilhetes, 42/42 com código+jogo+mercado+liga (múltiplas de 3, bet builders, eBasket, dardos, vôlei). **v2 (automação total, sem expandir) está BLOQUEADO pela bet365 e não será perseguido:** não há "próximo/anterior" no detalhe (confirmado pelo Feca); o "Mostrar Mais" é o único gatilho de paginação e (a) ignora clique sintético (~1000 = 0, barreira `isTrusted`), (b) é flaky até no clique humano; o seletor de data é por DIA (um dia cheio = 4 páginas); e só a própria página gera o token por fetch. **CLs mapeados dos payloads reais (s180):** `CL=15`=Dardos (liga `DARTS-MODUS`), `CL=91`=Vôlei (liga `VB-*`, "Handicap (Pontos)") — corrigidos em `_CL_B3`/`_OFF_B3` (content.js); resta `CL=151`. **Faxina:** o driver de clique/martelo (v0.6.5→0.6.13, ~230 linhas) foi removido do `b3_inject.js` — o método por rota o substitui; sobraram só `jaVarri`/`espera`/`esperarCodigo`. `check-tokens` verde. Commits `f022a08` (rota) + este. Ver [[bet365_captura_api]]. **Abaixo: s180a (o driver de UI por clique, que este método supera).**)_

_Anterior: 2026-07-23 (sessão 180a — **Bet365: extração COMPLETA no navegador — o driver de UI varre a lista inteira (10/10 com código BR).** Validado AO VIVO no Octo (conta marloncezar01). **Sintoma persistente das s177-179:** só 1 de N bilhetes ganhava código/detalhe; o resto vinha só com a casca do `summary` (seleção crua, stake, odd, resultado) — sem jogo/mercado/liga/BR. **Causa raiz (provada pelo console, não deduzida):** (1) o driver achava os botões por **TEXTO** ("Detalhes da Aposta"/"Voltar") — o botão real renderiza **"‹ Voltar"** com a setinha, o casamento exato falhava, caía no `history.back()` e a navegação embolava depois do 1º-2º bilhete; (2) **armadilha de teste que custou 2 rodadas:** recarregar a EXTENSÃO não re-injeta o content script em abas já abertas → os 2 primeiros testes da 0.6.5 rodaram o **código VELHO**. A prova foi o log `driver: 0 detalhe(s) · 1 pulado(s)` — o contador "pulado" só existe no código antigo (a reescrita não tem) → soube na hora que a página não tinha recarregado. O `código=1` era **fantasma**: o `FB9371265531W` vinha re-hidratado da memória (`chrome.storage b3Detalhes`), não de um clique novo. **Fix (`extensor/b3_inject.js`, classes mapeadas via Inspecionar do Feca):** driver reescrito com **seletor por CLASSE** em vez de texto — `.h-BetSummary_BetDetails` (detalhes), `.hl-BackButtonWithHistory` (voltar), `.hl-SummaryRenderer_ShowMore` (mostrar mais), `.hl-SummaryRenderer_Container` (lista), `.h-BetConfirmation` (detalhe). Varre a lista **inteira**: clica "Mostrar Mais" e **re-expande a cada volta** (`revelarAte`, aguenta a lista reiniciar no topo — O(n²) no pior caso, rápido em 24/48h); `garantirLista` **alterna** clique-no-Voltar e `history.back()` (se um não navegar o outro cobre) e **espera a re-renderização** em vez de desistir na 1ª lista vazia (era esse o travamento); **só o frame com a lista dirige** (guarda `temLista`, mata o conflito dos 2 iframes de membros). `content.js`: o timeout de inatividade conta o **tick de qualquer mensagem do inject** (não morre durante a expansão do Mostrar Mais, quando a contagem não cresce) + re-pede "detalhar" até `b3FimReal`. **Resultado ao vivo:** `driver={"feitos":10} · com código=10/10 · fimReal=true` — cada bilhete saiu com **jogo · mercado · seleção · liga · código BR**, inclusive Dupla (2 jogos) e bet builder (pernas). Manifest **0.6.4 → 0.6.6**. `node --check` nos 2 arquivos + `check-tokens` verde. Backup `Backups/s180-bet365-driver-seletores/` (só os 3 arquivos editados). **Lição operacional gravada:** ao atualizar a extensão, recarregar a extensão **E** dar `Ctrl+Shift+R` na página — senão a aba roda o script velho e o teste mente. **Pendências não-bloqueantes:** `CL=91` mapeia p/ esporte errado (Peru Women +23.5 = vôlei/basquete fem — o payload do confirmation traz "Handicap (Pontos)" e "COPAAMW", dá p/ desambiguar) e `CL=15` sem mapa → formatação/masters, não driver; bet builder sem "Data (encerramento)" (`TP=00010101` zerado pela guarda de ano<2000); `frames=13 · respostas=214` = ruído do re-ping (funciona, dá p/ enxugar); **backfill de 45 dias** segue pendente (automatizar "Intervalo de Datas" em janelas curtas). Ver [[bet365_captura_api]] · [[extensor_captura]].)_

_Anterior: 2026-07-23 (sessão 179 — **Perda silenciosa na extração: bilhete que estava no texto e nunca virou linha.** **Sintoma (Feca, Superbet):** dois bilhetes capturados dias antes como ABERTOS liquidaram, apareceram na captura de hoje com `Status: win` — e continuaram "aguardando resultado" na grade. **Diagnóstico (medido, não deduzido — e a 1ª leitura estava errada):** minha primeira hipótese foi o robô (janela de dias / `stopId` do `content.js` nunca revisitando bilhete antigo). **Errada** — o Feca colou o texto da captura e os dois estavam lá, com `win`. O que fecha o caso é o cruzamento código a código: `uso_tokens` mostra 3 extrações Superbet do Feca hoje (03:49, 03:51, 03:52), todas com 4 chunks; a primeira recebeu os **61 blocos** do texto e **só 22 viraram linha no banco** — exatamente os blocos 1 a 22, na ordem invertida esperada. Os 39 restantes (blocos 23→61) não geraram nada: 12 não existem no banco em lugar nenhum e 27 seguem com `atualizado_em` de 20/07, inclusive `891F-YWE4RL` e `891J-YNUVM0` (ids 61026/61025, ainda `aberta`). O UPSERT está correto (`repository.py` já trata aberta→resolvida por código) — **nunca recebeu essas linhas**. **Causa raiz:** `_extract_tsv_rows` devolve `[]` quando um chunk responde **sem o bloco ```tsv** → o pedaço inteiro some sem levantar exceção, e `chunks_falhos` (que só conta exceção) não acusa. A tela mostrou "✓ 22 novo(s)" com 39 bilhetes perdidos. **Fix (`conferência de cobertura`, casa-agnóstico):** o gabarito é determinístico — cada `[Código: …]` do texto vem do DOM/API, não da IA. (1) `repository.py`: `codigos_do_texto` (ordem do texto, sem repetir), `codigos_do_tsv` (pula o cabeçalho, cuja 11ª coluna é o rótulo "Código" — furo pego pelo próprio teste) e `conferir_cobertura`; (2) `main.py`: `_garantir_cobertura` roda nos **dois** caminhos (paralelo e sequencial), depois da inversão de linhas, e **repesca** o que faltou numa 2ª chamada com **só os blocos faltantes** (`_blocos_dos_codigos` recorta pelo mesmo marcador do chunker; o system, que é o caro, vem do cache) — as linhas recuperadas entram na posição certa pela ordem do texto, não empilhadas no fim (`_set_tsv_rows`); (3) `index.html`: o que **não** voltar nem na repescagem sobe como aviso alto — "⚠️ N de M bilhete(s) do texto NÃO foram extraídos — REPROCESSE". Erro na repescagem é engolido (segunda chance nunca derruba extração que já deu certo); `scroll_overlap_indices` é descartado quando a lista muda. **Casa sem marcador de código (Bet365, prints) → `esperados`=0 → no-op integral: nada do caminho Bet365 foi tocado** (trabalho da s178 em andamento). **Validação:** `tests/test_cobertura.py` novo (13 casos: gabarito, conferência com chunk sumido, recorte só dos faltantes, costura preservando header/notas, repescagem ponta a ponta com a chamada ao modelo dublada — ordem final oldest→newest e falta residual ainda avisada). Suíte: **191 passed, 4 skipped**. Backup `Backups/s179-cobertura-extracao/` (só os 3 arquivos editados). **Pendente:** os dois bilhetes do Feca continuam `aberta` — resolvem reprocessando o mesmo texto após o deploy (UPSERT por código, sem duplicar). Não validado em navegador. Ver [[extracao_sem_odd_flag]] · [[dedup_gap_sem_codigo_reextracao]].)_

_Anterior: 2026-07-23 (sessão 178 — **Bet365: o replay por API está morto (token rotativo, provado ao vivo) + 2 bugs de parser corrigidos.** **Etapa 1 de 2.** **Sintoma:** a captura trouxe 10 bilhetes "reduzidos" — `[Código: ]` vazio, bet builder com 1 linha em vez de 3, e a lista não passou da 1ª página. **Diagnóstico (aritmética, não suposição):** o console reportou `respostas=13 · b3ById=10 · fimReal=true` sem nenhum `erro replay`. A conta fecha exatamente como `1` (summary passivo que a página fez no load) `+ 1` (replay settled=1) `+ 1` (replay settled=0) `+ 10` (confirmations) — **todas as 12 do replay voltaram vazias**, e os 10 bilhetes vieram do único summary passivo. O erro não aparecia porque (a) resposta recusada volta **200 com corpo vazio**, sem exceção, e (b) `parseSummary` **nunca** retorna `null` (devolve `{cursor:null,bets:[]}`), então `respostas++` contava resposta fantasma. **Prova ao vivo (3 rodadas até rodar no frame certo — o seletor de contexto do console precisa ser trocado de `top` para `MembersIframe`):** mesma URL de `confirmation`, mesma sessão, do frame `members.bet365.bet.br` → com os headers da página **200 + payload `F|…`**; só com cookie, sem token → **`len: 0`**; com token **vencido** → **HTML de 404** (que o parser lia como cabeçalho sem `BR` e devolvia código vazio em silêncio). Ou seja: `x-net-sync-term` é obrigatório, rotaciona por requisição e não temos como gerar → **replay descartado**. Quem consegue chamar a API é a própria página. **Aplicado nesta etapa:** (1) replay inteiro removido do `b3_inject` (`varrerLista`/`buscarDetalhes`/`arrancar`/`urlSummary`/`urlConfirmation`/`getText`/captura de headers) — o arquivo volta a ser só ouvinte; (2) **`parseSummary` passa a ler o registro `04`** = pernas do bet builder (`NA`=seleção, `N2`=mercado), que estavam no payload e eram jogadas fora — era essa a causa do "reduzido", e ela é independente do token; (3) **`parseConfirmation` corrigido contra o payload real**: `02` é o **evento** (`NA`, `FN`=jogo, `L3`=liga, `MN`=mercado, `TP`=kickoff) e `03` são as **pernas** — o código tratava `02` como perna e devolvia `jogo:""`/`mercado:""`; (4) **guarda `BR` no cabeçalho** — sem ela, HTML de erro virava bilhete com código vazio, sem ruído; (5) bloco `01;TY=DI` (nome/endereço/CPF) explicitamente cortado do parse; (6) `_dataFimB3` ignora ano < 2000 (bet builder vem com `TP=00010101000000` → gerava "01/01/0001"); (7) formatador imprime as sub-pernas e não repete a odd `0/1` da perna como "@ 1"; esporte e contagem de jogos passam a sair também do summary. **Validação (offline, sobre os payloads REAIS capturados):** harness em `scratchpad/b3parse` roda os parsers **de produção** e o `formatTicketB3` **de produção** sobre o `summary` e o `confirmation` crus — bet builder sai com as 3 pernas nos dois modos (com e sem detalhe) e o código `BR=JR8714690761I` aparece quando o detalhe existe. `node --check` nos 2 arquivos + `JSON.parse` do manifest + `check-tokens` verde. Manifest **0.6.2 → 0.6.3**. Backup `Backups/bet365-robo-ui-2026-07-23/`. **Pendente — etapa 2 (decisão do Feca: opção 1, híbrido com memória):** transformar o `roboBet365Passive` em robô de UI — rolar a lista (a página pagina sozinha, cursor `PT` confirmado) e abrir "Detalhes da Aposta" só dos bilhetes sem `BR` guardado **ou capturados abertos** (guarda do `BS=1`, por causa do cashout, que só aparece no confirmation). Estimativa: ~16 min no 1º backfill de 45 dias, ~1-2 min nas rodadas seguintes. **Etapa 2 APLICADA no mesmo dia (manifest 0.6.4):** o Feca confirmou que **a lista volta ao topo** ao sair do detalhe — então varrer 45 dias de uma vez seria O(n²). **Descoberta de arquitetura:** a lista do Histórico é renderizada **dentro do iframe `members`** (outra origem) → o `content.js` (`all_frames:false`) **não alcança esse DOM**; quem clica tem de ser o `b3_inject`, que já roda lá dentro. O driver foi para o inject: acha os nós-folha com texto exato "Detalhes da Aposta", clica o i-ésimo (a ordem dos cards = ordem do summary = ordem de inserção do Map), espera o `confirmation` chegar (teto 8s), clica "Voltar" (fallback `history.back()`) e segue. O content só coordena: `b3Pedir(N,"detalhar",jaTem)`, acompanha e formata. **Timeout de inatividade passou a medir PROGRESSO** (`size` + quantos têm código) — medir só o tamanho matava o robô no meio da varredura, porque durante os detalhes a quantidade não cresce, só o conteúdo. **Furo pego pelo harness (não pela leitura):** a memória guardava só "esse bsid já foi detalhado" → na 2ª rodada o bilhete pulado saía com `[Código: ]` **vazio** e sem mercado/liga, e o UPSERT trocaria dado bom por pior. Corrigido: a memória (`chrome.storage.local` `b3Detalhes`, teto 3000 com poda) guarda **`{code, da, legs}`** e o robô **re-hidrata** o que o driver pulou antes de formatar. **Validação:** harness em `scratchpad/b3parse/driver.js` carrega o `b3_inject.js` REAL num DOM emulado (3 cards + link Voltar + página respondendo o `confirmation` no clique) → sequência `detalhe#0 → voltar → [pula #1, já conhecido] → detalhe#2 → voltar`, `{feitos:2, pulados:1, falhas:0}`, termina na lista. `node --check` nos 2 arquivos + `check-tokens` verde. **Não validado em navegador:** os seletores por texto ("Detalhes da Aposta"/"Voltar") e o comportamento real do Voltar — o log do robô agora diz `com código=X/Y` e avisa explicitamente quando sobra bilhete sem código. **Ação:** atualizar a extensão p/ 0.6.4, deixar a tela em **"Últimas 24 horas"** (lista curta = o Voltar custa ~zero) e rodar. **Backfill de 45 dias segue pendente** — precisa automatizar "Intervalo de Datas" em janelas curtas (etapa 2b). Ver [[bet365_captura_api]] · [[extensor_captura]].)_




> **Histórico completo das sessões 176 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências (aguardam bilhete real)

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus

**Próximo passo:**
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
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
