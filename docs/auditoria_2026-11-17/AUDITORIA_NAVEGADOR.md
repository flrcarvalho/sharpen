# Auditoria independente: cache e estado no NAVEGADOR (Sharpen)

Data: 17/11/2026 · Escopo: tudo que faz o usuário ver código velho, dado velho, tela que não
atualiza ou estado salvo incompatível com o código novo. Somente leitura: nada no repo foi
alterado, nenhuma chamada a produção.

Fontes de verdade usadas: execução do `app.main` real (TestClient, sem banco), réplica mínima
da política de cache do servidor, o front REAL (`app/static`) servido pelo `servidor_demo.py`
envelopado por um mock controlável, Chrome headless (puppeteer-core do repo) com perfil
persistente, e o histórico do git. Documentação e comentários NÃO foram usados como prova.

Material reexecutável em `aud_navegador/`:
- `hdrs.py` + `headers_medidos.txt`: headers reais emitidos pelo `app.main`.
- `bump.py` + `bump_resultado_v2.txt`: medição de cache-bust esquecido no git.
- `exp1/`: réplica da política de cache (StaticFiles + middleware) e `exp1.mjs`.
- `exp2/srv2.py`: o front real + feed/custos controlados por `modo.txt`; `exp2.mjs` … `exp8.mjs`.

---

## Resumo: quatro famílias, não quinze bugs

| Família | O que o usuário vê | Achados |
|---|---|---|
| **A. Código velho sem identidade de build** | "foi corrigido e voltou", "pra mim funciona, pra ele não", F5 não resolve | C1, C2, M1, M4, M5 |
| **B. Estado do navegador sem dono e sem versão** | dado de outra pessoa/época na tela, custo que "aparece do nada" | C3, C4, M3, B1, B2 |
| **C. Falha de rede vira dado** | zeros, número velho com cara de atual, "Dados sincronizados" mentindo | A2, A3, B3 |
| **D. Estado completo, último escritor vence** | lançamento de custo que some sozinho | A1 |

O usuário que volta depois de meses atravessa as quatro na mesma sessão: boot pelo cache de
meses atrás (M3), chaves sem dono (C4), arquivos com `?v=` esquecido (C2), e qualquer falha
transitória escondida (A3). Isso bate com "4 ou 5 problemas no mesmo dia". O usuário
frequente mora na família A: aba aberta por dias atravessa deploys sem receber código (C1).

---

## CRÍTICO

### C1. A aba aberta nunca recebe código novo. O deploy só recarrega DADO. (COMPROVADO)
- **Sintoma:** quem deixa o Sharpen aberto continua rodando a versão de quando abriu, por
  dias. Correção publicada "não pega" para ele, e o defeito "volta" até ele fechar a aba.
  Contra o backend novo, o JS velho pode quebrar de formas novas.
- **Mecanismo:** a casca `/app` é desenhada para nunca recarregar (`app/static/app.html:339`,
  "Navegar = mostrar/esconder o iframe certo, NUNCA recarregar a casca"). O SSE `/eventos`
  reconecta depois do deploy e chama `agendarAutoRefresh()` (`app.html:506-508`), que só
  chama `loadData()` dos iframes. Não existe identidade de build em lugar nenhum: nenhum
  endpoint, header ou evento informa a versão do código, e nenhum código compara versão
  (grep por `RAILWAY_GIT_COMMIT`, `build`, `versao` no app: só a versão da EXTENSÃO existe).
- **Evidência:** `exp2/exp3.mjs`. Abri `/app#dash/overview`, marquei `window.__MARCA` nos 4
  documentos (`/app`, `/inicio`, `/`, `/dashboard/`), derrubei o servidor (taskkill) e subi
  outro processo, como num deploy. Depois da reconexão: o servidor novo recebeu `GET /eventos`
  e 2× `GET /dashboard/data` (dado recarregado), e os 4 documentos mantinham a marca, ou seja,
  zero recarga de documento ou script. Saída literal em "ANTES/DEPOIS" do experimento.
- **Família:** A. **Correção estrutural:** expor `BUILD_ID` (ex.: `RAILWAY_GIT_COMMIT_SHA`)
  num header de toda resposta e no primeiro evento do `/eventos`; a casca guarda o seu e,
  ao ver um diferente, recarrega a si mesma num momento seguro (aba oculta, sem modal
  preenchido nem extração em curso) ou mostra "nova versão, recarregar". Um ponto só, na
  casca, cobre os três iframes.

### C2. JS/CSS saem sem `Cache-Control` e o cache-bust é manual: F5 não resolve e o `?v=` é esquecido em 20% das mudanças. (COMPROVADO)
- **Sintoma:** depois de um deploy, parte dos usuários recebe o arquivo novo e parte fica
  com o velho, e apertar F5 não muda nada. Só Ctrl+F5 ou limpar cache resolve.
- **Mecanismo:** o middleware (`app/main.py:973-998`) só põe `Cache-Control` em `text/html`.
  Todo JS/CSS sai com `ETag` + `Last-Modified` e **sem** `Cache-Control`, o que liga o
  *cache heurístico* do navegador (10% da idade do arquivo sem perguntar ao servidor).
  A proteção contra isso é o `?v=N` escrito à mão em cada `<script>/<link>`.
- **Evidência 1 (headers reais):** `hdrs.py` contra o `app.main`. `/static/app.html`,
  `/dashboard/`: `cache-control: no-cache, must-revalidate`. `/dashboard/assets/js/app.js`,
  `/static/shell.css`, `/static/sharpen-cal.js`, `/static/fonts.css`, `mc-worker.js`: só
  `etag`/`last-modified`, sem `cache-control` (`headers_medidos.txt`).
- **Evidência 2 (F5 não resolve):** `exp1/exp1.mjs`, réplica exata dessa política. Arquivo
  com 20 dias de idade, carregado; troquei o conteúdo (deploy) mantendo a URL. Resultado:
  nova navegação, **F5** e aba nova executaram o conteúdo ANTIGO, e o log do servidor
  mostra que o navegador nem pediu o JS de novo (só revalidou o HTML, 304).
- **Evidência 3 (o `?v=` é esquecido):** `bump.py` percorre o git: para cada commit que mudou
  um asset versionado, confere se o `?v=` mudou no MESMO commit em toda página que o
  referencia. **96 de 470 commits (20%) mudaram asset sem bump.** Casos recentes:
  `data.js` está em `?v=32` desde 31/10 e mudou em 01/11, 08/11, 10/11, 12/11 e 16/11
  (s455, GiroCerto) sem bump; `app.js` 15×, `performance.js` 7×, `layout.css` 7×.
  Nunca versionados: `/static/tokens.css` (5 mudanças), `/static/fonts.css`, `vendor/*.js`.
- **Contagem de descasamento possível:** o dash carrega 21 arquivos locais (`dash/index.html:30-83`),
  todos scripts clássicos que compartilham funções globais entre si (`renderKPI`, `parseNum`,
  `costKey`, `window.__dono`). Cada um tem cache independente; após um deploy com bump
  parcial, qualquer subconjunto pode estar velho, e a quebra aparece como `TypeError` ou
  regra antiga num arquivo e nova no vizinho.
- **Família:** A. A s215 (HTML `no-cache`) e cada bump esquecido corrigido depois são
  remendos da mesma família. **Correção estrutural:** URL com hash do CONTEÚDO, gerada pelo
  servidor e nunca escrita à mão: no boot, calcular o hash de cada arquivo de `static/` e
  reescrever as referências ao servir o HTML (ou um passo de build), servir URL com hash
  com `Cache-Control: public, max-age=31536000, immutable` e todo o resto com `no-cache`.
  Gate: teste que falha se algum HTML tiver `?v=` literal ou referência local fora do hasher.

### C3. O cache do feed no IndexedDB não tem dono: o próximo usuário do navegador vê a base do anterior. (COMPROVADO)
- **Sintoma:** ao trocar de conta no mesmo navegador (logout/login, ou "Ver base de" do
  supervisor, que recarrega a casca), o Dashboard abre com as apostas da conta ANTERIOR por
  10 a 30 s (o tempo do feed em produção), com a pílula "sincronizando".
- **Mecanismo:** `_IDB_KEY = 'dados_v1'` fixo (`app/static/dash/assets/js/app.js:1538`),
  sem dono. `loadData()` pinta o cache antes do fetch (`app.js:1626-1640`).
- **Evidência:** `exp2/exp2.mjs`. Alice carrega (24.000 linhas, `dono:"Alice"`). Bob entra
  no mesmo navegador (feed dele com 123 linhas, atraso de 6 s): aos 2,5 s e aos 9,5 s o dash
  do Bob mostrava as **24.000 linhas da Alice** (`parceiro0: "Léo [Pauta]"`); só aos 21 s
  virou `123 / BOB-…`.
- **Família:** B. Também é exposição de dado entre contas. **Correção:** chave do IDB com o
  dono (resolvido antes de ler: `/me` é barato) e limpeza do IDB/LS no logout e no "ver como".

### C4. Custo de tipster e custo geral vivem em chaves GLOBAIS e a "semeadura" grava o custo de outra pessoa na conta nova. (COMPROVADO)
- **Sintoma:** usuário que entra num navegador onde outra conta já usou o Sharpen vê, no
  Dashboard, os custos de tipster/gerais da outra conta descontados do P/L dele. Ao editar
  qualquer custo, esses valores passam a ser DELE no servidor, para sempre.
- **Mecanismo:** `CT_KEY='custoTipsterData'` e `CG_KEY='custoGeralData'` sem dono
  (`app.js:1401-1402`). `ctLoad()` (`app.js:1416-1440`) carrega o local; se o servidor diz
  `existe:false` (ou existe com blob vazio, `vazioLa && _ctHadLegacy`), mantém o local.
  `ctSave()` (`app.js:1459`) manda `semear:true`, e `salvar_custo_store`
  (`app/repository.py:5802-5832`) UNE o que veio com o que há.
- **Evidência:** `exp2/exp4.mjs`. Alice usa o navegador (10 tipsters, 4 gerais no LS). Bob
  (servidor sem registro) abre: `ctTipsters:10, cgLinhas:4` na memória do dash dele. Uma
  chamada a `ctSave()` (o que toda edição de custo faz) gerou `POST /custos/store` com os
  custos da Alice ("Linha Fria 690,00", "Corner Value 450,00"…) e `"semear":true`.
- **Família:** B (chave sem dono) cruzada com D (blob inteiro). O mesmo vale para "ver como"
  entre operadores do mesmo supervisor. **Correção:** apagar CT/CG do navegador como fonte
  (servidor é a única), ou no mínimo namespace por dono + nunca semear a partir de chave
  sem dono; a semeadura legada deveria ser um ato explícito e único, não efeito de edição.

---

## ALTO

### A1. Duas abas: a segunda apaga do servidor o que a primeira lançou. (COMPROVADO)
- **Sintoma:** custo de tipster/geral (e custo por conta) lançado "some" depois.
- **Mecanismo:** o front manda o estado INTEIRO (`_ctPush`, `_custoPush`) e o servidor
  substitui (`salvar_custo_store`/`salvar_custo_conta` com `semear=false`). Nenhuma checagem
  de versão, e nenhum listener de `storage` entre abas.
- **Evidência:** `exp2/exp7.mjs` com servidor em memória que substitui como o real. Aba 1
  lança "Tip Dois 250,00" → servidor `{Tip Um 100, Tip Dois 250}`. Aba 2 (aberta antes)
  edita "Tip Um 120,00" → servidor `{Tip Um 120}`: **Tip Dois sumiu**, sem erro.
- **Família:** D. Vale para abas, aparelhos e para a casca com dois iframes que escrevem.
  **Correção:** escrita por item (`PATCH` de uma chave) ou concorrência otimista
  (`atualizado_em` enviado de volta, servidor responde 409 se mudou).

### A2. Falha do feed na Início vira R$ 0 e "Dados sincronizados agora". (COMPROVADO)
- **Sintoma:** a home mostra P/L do mês `+R$0,00`, "sem apostas encerradas", e a casca diz
  "Dados sincronizados 17/11 · 13:55" (agora), justamente quando o dado NÃO chegou.
- **Mecanismo:** `jget()` engole qualquer erro em `null` (`app/static/inicio.html:281`);
  `rows=[]`; e `window._dataBuiltMs = feed ? builtAt : Date.now()` (`inicio.html:490`).
- **Evidência:** `exp2/exp5.mjs`: feed OK → `+R$1.688,60`, sync 11:00; feed 401 →
  `+R$0,00`, sync com o horário atual. Print: `exp2/exp5_inicio_feed_falhou.png`.
- **Família:** C. **Correção:** um wrapper de fetch único que distingue 401 (→ login),
  5xx/rede (→ estado "sem conexão, dados de HH:MM") e sucesso; nunca `Date.now()` como
  frescura de dado que não chegou.

### A3. No Dashboard, falha com cache em tela some sem aviso. (COMPROVADO)
- **Sintoma:** sessão expirada, timeout ou 5xx: o Dashboard continua mostrando o dado
  antigo, sem banner, sem pílula, como se fosse atual. Só o pequeno "último sync" denuncia.
- **Mecanismo:** `app.js:1685` mantém o cache; `app.js:1699` só mostra banner
  `if(!servedFromCache)`; `_revalOff()` tira a máscara de qualquer jeito.
- **Evidência:** `exp2/exp2.mjs` passos 4-5: feed 401, `pill:false, banner:false`, 123
  linhas antigas na tela após 11 s. 401 é o caso típico do usuário que volta.
- **Família:** C. **Correção:** a mesma do A2, e 401 em qualquer iframe leva a casca ao login.

---

## MÉDIO

### M1. `ETag` e `Last-Modified` vêm do `mtime`, não do conteúdo. (mecanismo COMPROVADO; produção HIPÓTESE)
- **Mecanismo:** Starlette 1.2.0 `FileResponse.set_stat_headers`: `etag = md5(mtime-size)`.
  A validade do cache depende de como o builder da Railway grava `mtime` no `COPY app/`.
- **Evidência:** `exp1`: troquei o conteúdo de `a.js` mantendo tamanho e `mtime` → o servidor
  respondeu **304** ao ETag antigo (navegador mantém conteúdo velho). Se o build gravar
  `mtime` = hora do build, todo deploy invalida tudo (ok, só custo); se normalizar `mtime`,
  edição de mesmo tamanho nunca chega. E a janela heurística do C2 é 10% de
  (agora − `mtime`), então ela também depende disso.
- **Correção:** a do C2 (hash de conteúdo na URL + `immutable`) elimina a dependência.

### M2. O middleware apaga o `no-store` que as rotas pedem; a página volta pelo bfcache. (COMPROVADO no header; bfcache medido na demo)
- **Mecanismo:** `/`, `/app`, `/inicio`, `/login` declaram `no-cache, no-store, must-revalidate`
  (`main.py:3016, 3044, 3055, 3124`) e o middleware sobrescreve com `no-cache, must-revalidate`
  (`main.py:997`). Medido em `/login`: sai sem `no-store`.
- **Evidência:** `exp2/exp6.mjs`: `/app` → outra página → Voltar: `window.__MARCA` preservada,
  página restaurada da memória (bfcache), sem recarga e sem handler de `pageshow` no código.
  Efeitos: depois do logout, "Voltar" pode reexibir a casca com dados; e a volta reexibe
  números velhos sem disparar refresh.
- **Correção:** decidir por rota (o middleware usar `setdefault` em vez de sobrescrever) e um
  handler `pageshow` com `event.persisted` na casca que revalida sessão e dado.

### M3. Cache do feed sem versão de schema: quem volta depois de meses vê o feed de meses atrás, no formato antigo. (COMPROVADO)
- **Evidência:** `exp2/exp8.mjs`: IDB reescrito com linhas no formato de jul/2026 (sem `id`,
  `stake_freebet`, `moeda`, `operador`, `conta`, `fornecedor`) e `savedAt` de 10/07. Boot:
  24.000 linhas, **0 com `id`**, "último sync: 10/07" por ~10 s até o feed chegar. Sem
  crash, mas nessa janela edição de linha não tem `id` e campos novos (freebet, moeda) somem
  da conta. Com falha de rede (A3) a janela vira permanente.
- **Correção:** registro do IDB com `{build, schema, dono}` e descarte se divergir; não pintar
  cache mais velho que X horas.

### M4. A mesma folha com versões diferentes e versões acopladas à mão.
- `shell.css?v=2` em `index.html:24` e `?v=4` em `app.html:16` e `dash/index.html:34`
  (o git mostra 3 mudanças do `shell.css` sem bump em todas as páginas). O worker de Monte
  Carlo herda a versão da URL do worker (`mc-worker.js:10`, `importScripts('mc-core.js' +
  location.search)`) e não a do `mc-core.js`: dois números para acertar juntos.
- **Correção:** a do C2.

### M5. Iframes carregados em momentos diferentes rodam versões diferentes dentro da mesma casca. (HIPÓTESE forte, deriva do C1)
- `/inicio` e `/` carregam com a casca; `/dashboard/` só no 1º clique (`app.html:370`).
  Abrir o dash depois de um deploy junta casca e Extração velhas com Dashboard novo, e as
  chamadas cruzadas (`mostrarView`, `showPage`, `loadData`, `_dataBuiltMs`, `sb-tipster.js`
  da casca) ficam entre versões. Os `try{}catch(e){}` vazios de `app.html:359-360, 416, 434,
  469` engolem a incompatibilidade em silêncio.

---

## BAIXO

- **B1. Chaves órfãs e migração ad hoc (COMPROVADO por git).** Saíram do código e ficam no
  navegador: `aparencia_v1`, `theme`, `poly-wallet`, `btbl_colw_v1/v2`, `dash_custos_v2`
  (legado global, migrado só quando o dono é `Feca`: `gestao.js:41-44`, `index.html:8185-8190`).
  Cada estado tem seu próprio esquema de versão (sufixo manual + checagem de tamanho:
  `fdc-btbl-cols-v3`, `btbl_colw_v3`). Funciona, mas é mais um número manual.
- **B2. Boot pelo cache usa o namespace `_` (COMPROVADO).** `window.__dono` só existe depois
  do fetch (`dono:null` medido em exp2/exp8); nessa janela `costKey()` e `dash_tipunit::` leem
  `::_`.
- **B3. Caches de memória que retêm o último valor sem dizer.** `ensureCaixaVisao`
  (`index.html:5046-5056`): falha mantém o número velho (ou um vazio na 1ª carga) sem
  marcação; mesmo padrão em `loadCusto`/`ctLoad` ("offline: fica no cache"). Família C.
- O código morto `setupColResize` (`index.html:11657`, sem chamadas) persistiria larguras
  por ÍNDICE de coluna; não roda hoje.

---

## Inventário (referência)

**Headers medidos (`app.main`):** HTML `no-cache, must-revalidate` + ETag (304 em revalidação);
JS/CSS sem `Cache-Control` (heurístico); rotas que pedem `no-store` perdem o `no-store`.

**Referências a assets locais:** versionados à mão: 19 (`dash/index.html` 18 + `mc-worker`);
sem versão: `/static/fonts.css` (6 páginas), `/static/tokens.css` (4 páginas),
`vendor/chart.umd.js`, `vendor/html2canvas.min.js`, favicons, `site.webmanifest`,
`brand/*.svg`, woff2. Sem service worker, sem `caches.open`. ES modules: nenhum (tudo script
clássico com globais). Worker por URL de arquivo e por Blob.

**Armazenamento:** IndexedDB `fdc_dash/kv/dados_v1` (feed inteiro, sem dono) e
`dados_pub_<slug>`. localStorage com dono: `dash_custos_v2::<dono>`, `dash_tipunit::`,
`sharpen_raiox_hist::`, `sharpen_activity::`, `sharpen_novidades_seen::`, `poly-last-sync::<wallet>`.
Sem dono: `custoTipsterData`, `custoGeralData` (dado de negócio), `fdc-btbl-cols-v3`,
`btbl_colw_v3`, `cn_geral_aberto`, `sharpen_painel_off`, `sharpen_cap_recolhida`,
`sharpen_raiox_off` (preferências). sessionStorage: não usado.

---

## Correção estrutural proposta (ordem sugerida)

1. **Identidade de build** (C1, M5): `BUILD_ID` no header e no `/eventos`; a casca recarrega
   quando muda. É o que acaba com "corrigido e voltou" para o usuário frequente.
2. **URL por hash de conteúdo, gerada pelo servidor** (C2, M1, M4): fim do `?v=` manual,
   `immutable` nos hasheados, `no-cache` no resto, gate contra `?v=` literal.
3. **Um módulo de armazenamento** (C3, C4, M3, B1, B2): chave `sharpen:<dono>:<schema>:<nome>`,
   IDB por dono com `{build, schema}`, limpeza no logout/"ver como", varredura de chaves
   desconhecidas no boot. Dado de negócio nunca no navegador como fonte.
4. **Um wrapper de fetch** (A2, A3, B3): 401 → login pela casca; falha → estado visível com
   a hora do último dado bom; sucesso é o único que mexe em `_dataBuiltMs`.
5. **Escrita por item ou com versão** (A1, C4): `PATCH` por chave ou 409 em conflito.

---

## O que não consegui verificar

- **Produção:** por regra, nenhuma requisição foi feita a `sharpen.bet`. Não medi o
  `Last-Modified`/`ETag` reais nem se o builder da Railway preserva ou normaliza `mtime`
  (decide o tamanho real da janela do C2 e se o M1 acontece). Para medir, só leitura:
  `curl -sI https://www.sharpen.bet/dashboard/assets/js/data.js?v=32` em dois deploys.
- **Navegadores reais dos usuários:** só Chrome headless no Windows. Não testei Safari/iOS,
  Firefox, Edge com políticas corporativas, nem extensões que mexem em cache.
- **Duração exata da janela heurística no Chrome** (se há teto) não foi medida em dias;
  o exp1 provou o comportamento com arquivo de 20 dias.
- **bfcache com os headers exatos de produção:** a demo serve `/app` sem `Cache-Control`;
  produção manda `no-cache` (sem `no-store`), que pela regra do Chrome também é elegível,
  mas não reproduzi com o `app.main` real (exige sessão e banco).
- **TTL da sessão** (`SESSION_MAX_AGE`) e o comportamento real de 401 em todas as rotas que
  os iframes chamam: simulei 401 só no `/dashboard/data`.
- **Extensão SharpenUp** (`chrome.storage.local`: `envioPendente`, `token`, `frameRect`,
  memórias por casa) e as várias cópias instaladas: fora desta lente, não auditado.
- **Caches de servidor** que alimentam o navegador (cache de 120 s do `/dashboard/data`,
  planilha ao vivo de 30 min, cache de identidade de 60 s): fora desta lente.
- Não reproduzi um `TypeError` concreto de arquivos descasados (C2); a medição mostra que o
  descasamento acontece, não qual quebra ele causou em cada caso.
