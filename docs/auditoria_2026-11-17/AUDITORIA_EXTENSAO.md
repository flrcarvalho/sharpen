# Auditoria independente: SharpenUp e o contrato extensão ↔ servidor ao longo do tempo

Data: 17/11/2026. Base: `main` em `464d5c4` (SharpenUp 0.7.86). Somente leitura; nada no repo foi
alterado. Experimentos e saídas nesta pasta (`aud_extensao/`).

Fonte de verdade usada: o código (`extensor/*.js`, `app/*.py`, `app/static/index.html`), o
histórico do git e medições feitas aqui. Comentário, CLAUDE.md, STATUS, BACKLOG, docs e memória
não foram usados como prova. Cada achado diz se é **COMPROVADO** (e como) ou **HIPÓTESE**.

---

## 0. A causa sistêmica, em uma página

Os 4 ou 5 problemas que um usuário encontra ao voltar depois de semanas não são defeitos
independentes. Eles saem de **quatro lacunas de projeto**, e cada conserto pontual tapa um
sintoma sem fechar a lacuna, por isso a família volta:

1. **A confirmação é de transporte, não de durabilidade.** O `200` do `/captura/enviar` quer dizer
   "o texto está na RAM do processo, numa fila de sessão, esperando uma aba do dashboard puxar".
   A extensão trata esse `200` como "gravado" e apaga a única cópia (`envioPendente`). Deploy
   (≈4,5 por dia), dashboard recarregado ou fechado, e a captura some sem erro (achado A1).
2. **Não existe negociação de versão em nenhuma das três fronteiras.** O servidor anota a versão e
   nunca a usa para recusar ou adaptar; o inject (mundo MAIN) e o content não trocam versão; e as
   regras de negócio (casa → inject, hosts por casa, ramos do robô) estão compiladas dentro da
   extensão, que é instalada à mão. Com 161 versões em 4,5 meses, quem volta está 20 a 40 versões
   atrás e cai em comportamento que nenhum teste exercita (A2, A3).
3. **O estado do cliente é gravado antes, e independente, da aceitação durável no servidor, e não
   tem escopo de dono, conta nem versão.** Marca d'água de horizonte gravada antes do envio,
   registro de "já enviado" por 60 dias sem dono, memória de detalhes sem versão, pendência num
   slot único que vence em 24 h (A6, A7, A8).
4. **Completo e parcial são indistinguíveis.** Erro HTTP no meio da paginação, teto de páginas,
   30 s sem crescer: tudo vira `fim`, o content limpa o `lastError` e o servidor recebe um lote
   que parece inteiro. Para quem volta com muito histórico, o parcial é o caso comum, não a
   exceção (A4, A5).

O harness (`node extensor/harness/run.mjs`, 62 casos, 1.150 bilhetes, **verde**) não pega nenhum
dos achados abaixo: ele roda **uma** versão, **uma** injeção, sem servidor, sem tempo e sem
volume. É um gate de formatação, não de contrato.

---

## A1. "Bilhetes enviados ✓" sem nada gravado: a fila é RAM, entrega única, e o cliente apaga a cópia

**Sintoma do usuário.** A extensão mostra "Bilhetes enviados ✓", e no dashboard nada aparece, ou
aparece numa aba e some. Nenhum erro em lugar nenhum. Reenviar não é oferecido: o cliente já
apagou o texto.

**Mecanismo.**
- `/captura/enviar` só faz `adicionar_captura`, que anexa o texto a `sess.capturas`, uma lista
  dentro de `_SESSOES`, um dict em memória do processo (`app/captura.py:388`, `:495-509`), e
  responde `{"ok": True}` (`app/main.py:4320`).
- O cliente trata esse `200` como sucesso final: `background.js:202` sinaliza "Bilhetes enviados ✓"
  e `content.js:2062-2063` remove o `envioPendente`, a única cópia do que foi raspado.
- Quem tira da fila é o poll da aba do dashboard: `GET /captura/sessao/{id}` chama
  `drenar_capturas`, que **esvazia a fila na leitura** (`captura.py:512-518`,
  `main.py:4152`). Se a resposta não chega ao navegador, o `catch (_) {}` do
  `pollExtensao` engole o erro (`index.html:7022`) e a captura já saiu do servidor. Entrega
  "no máximo uma vez".
- O id da sessão vive só numa variável JS (`let extSessao`, `index.html:6900`, atribuída só em
  `:6967`). **Recarregar ou fechar o dashboard órfã a sessão**: a extensão continua com token
  válido por até 6 h (`SESSAO_TTL`, `captura.py:27`), cada envio volta `200`, e ninguém nunca drena.
- Depois do poll, o texto vai para um `<textarea>` (`index.html:7011-7013`) e só vira dado se
  alguém clicar Processar. Até lá ele existe só no DOM daquela aba.
- Todo deploy reinicia o processo e zera `_SESSOES` com as filas. O repo tem 113 commits em
  25 dias desde 18/10 (≈4,5/dia; `git log --since=2026-10-18`), e a regra do projeto é commit e
  push juntos com deploy automático. Cada push derruba toda sessão pareada.
- Imagens: o servidor aceita até 60 na fila (`MAX_CAPTURAS`, `captura.py:29`), o dashboard
  aceita 15 (`IMG_MAX`, `index.html:7045`) e descarta o resto que já foi drenado
  (`index.html:7061-7063`), com um aviso que o próximo `setStatus` sobrescreve.

**Evidência.** COMPROVADO por leitura das linhas citadas (caminho completo, do clique ao
`textarea`). A frequência de deploy é inferência do log do git somada à regra de push.

**Severidade.** Crítica. Perde dado sem sinal nenhum, e o cliente destrói a cópia de
recuperação justamente porque confia na resposta.

**Pontual ou família.** Família: "confirmação de um passo intermediário lida como confirmação
final". A mesma forma aparece no `cruEnviado` (A8) e no carimbo da Bolsa (A6).

**Correção estrutural.** O servidor só responde `200` depois de gravar o lote num lugar durável
(tabela `captura_pendente` por dono/conta, com id), e devolve esse id. A extensão só apaga o
`envioPendente` com o id na mão. O dashboard lista as pendências do dono (não as da sessão JS),
re-anexa depois de recarregar, e apaga a linha só depois do `/salvar` (ack em dois tempos). A
sessão de pareamento passa a ser um registro em banco, e deploy deixa de derrubar o pareamento.

---

## A2. Atualizar sem F5 (ou ter duas cópias instaladas) deixa o inject VELHO capturando: "o conserto não pega"

**Sintoma do usuário.** Ele atualiza o SharpenUp porque um conserto saiu, clica "Copiar
bilhetes" e vê o mesmo erro de antes (ex.: Thunderpick "replay parou · HTTP 404"), ou uma
captura menor que a real. Com F5 na aba da casa, funciona. Com duas pastas da extensão carregadas
no mesmo perfil, nem o F5 resolve, e o resultado muda de um carregamento para outro.

**Mecanismo.**
- Os `*_inject.js` rodam no mundo MAIN da página. Atualizar a extensão não os descarrega: o
  closure velho fica vivo, com `window.fetch` embrulhado por ele.
- O popup reinjeta o inject a cada captura (`popup.js:484`). Nenhum inject tem trava de
  reinstalação (conferido nos 31: só o `x1_inject` tem `__suX1Cedo`, e para outra coisa). A única
  guarda é a marca no `fetch` (`!of.__suTHPW` etc., `thp_inject.js:417`). Resultado: o inject
  novo **não instala o hook** (o `fetch` já tem a marca da versão velha), mas **registra um
  segundo ouvinte** de pedido. Os dois respondem ao `__sharpenup…Req` e os dois rodam replay.
- O content termina no **primeiro** `fim` que chegar (`content.js:668`, `:6478`) e processa
  400 ms depois. O inject velho, com a rota antiga, chega primeiro.
- O contrato inject → content não carrega versão (nenhum inject manda a própria versão;
  `grep versao|version *_inject.js` só acha nomes de header de casa). O content não tem como
  perceber que está ouvindo código de outra versão.
- Duas instalações (a página `/extensao` baixa `sharpenup-<versão>.zip`, e o descompactador do
  Windows sugere uma pasta nova com esse nome; a página manda "descompacte por cima", sem dizer
  para remover a outra, `app/static/extensao.html:124-126`): os dois `document_start` correm, o
  primeiro a embrulhar o `fetch` vence, e os dois contents recebem as mensagens um do outro
  (`postMessage` é global da página). É o mesmo mecanismo, só que permanente.

**Evidência.** COMPROVADO por simulação com o código real do git:
`e1_inject_velho_na_aba.mjs` e `e1b_com_latencia.mjs` carregam o `thp_inject.js` da 0.7.85
(`git show 464d5c4^`) e o da 0.7.86 no mesmo contexto, com a casa respondendo como hoje (rota
antiga 404, nova 200, 900 ms de latência nas rotas novas):

```
hook de fetch continua o da 0.7.85?  true
ouvintes de message: depois da 0.7.85 = 1 · depois da 0.7.86 = 2
1o fim em +147ms (erro="replay parou · HTTP 404"); content processa em +547ms com 0 bilhetes; o total disponivel era 18
---- aba com F5 (so 0.7.86)
1o fim em +1950ms (erro=""); content processa em +2350ms com 18 bilhetes; o total disponivel era 18
```

O conserto da s457 (0.7.86) entrega 0 de 18 na aba aberta antes da atualização. Mesmo com a
mesma versão injetada duas vezes (o que acontece a cada clique), a página recebe dois replays
completos (12 mensagens em vez de 6).

A parte "duas cópias" é COMPROVADA no mecanismo (mesma guarda, mesmo `postMessage`), e
HIPÓTESE quanto à ordem de carga entre extensões no Chrome real.

**Severidade.** Alta. Explica "consertei e voltou" sem nenhum defeito novo no código.

**Pontual ou família.** Família, vale para as 31 injeções. A instrução "recarregue com
Ctrl+Shift+R" aparece espalhada em mensagens de casa (`content.js` diag da Bet365, popup do
Resolver), o que é sinal de que o sintoma já foi visto e tratado caso a caso.

**Correção estrutural.**
1. Todo inject carimba a própria versão (`__suVer: "0.7.86"`) em cada mensagem e no `fetch`
   embrulhado. O content compara com `chrome.runtime.getManifest().version`; divergiu, recusa a
   rodada e mostra "recarregue a aba (F5)". O mesmo carimbo vai para o servidor.
2. A reinjeção vira idempotente de verdade: `window.__suInj[familia]` com a versão; se já há
   uma da mesma versão, não registra ouvinte; se há uma de outra versão, não roda e pede F5.
3. No `onInstalled` (reason `update`), o service worker recarrega as abas das casas
   conhecidas ou marca a aba para pedir F5 antes de capturar.
4. A página `/extensao` e o popup detectam outra instalação (o content pode deixar uma marca no
   DOM com o id da extensão; duas marcas diferentes na mesma página = duas cópias).

---

## A3. O servidor anota a versão e nunca a usa; regras de negócio moram dentro da extensão

**Sintoma do usuário.** Com extensão antiga: casa nova "captura" lixo (texto da página), o popup
recusa a aba de um domínio que já é suportado, apostas ficam "pendentes" sem motivo visível, e o
aviso "versão desatualizada" aparece sempre, sem dizer se importa.

**Mecanismo.**
- `registrar_versao` (`captura.py:473-481`) grava; `versao_desatualizada` (`main.py:3166-3174`)
  só pinta aviso. Nenhuma rota recusa ou degrada por versão (`grep versao_ext app/*.py`: só
  gravação em tabela e aviso). Não existe versão mínima suportada.
- "Desatualizada" = qualquer versão menor que a publicada. Com 161 commits no
  `manifest.json` em ≈4,5 meses, todo usuário vira "desatualizado" quase todo dia, inclusive por
  bugfix de uma casa que ele não usa. O aviso perde valor. (Fadiga é HIPÓTESE de comportamento.)
- **Casa nova + extensão velha = raspagem genérica.** O servidor devolve `modo: "texto"` para
  toda casa de `_MODO_POR_CASA` no pareamento. A extensão velha não tem o ramo da casa e cai no
  `else { blocos = await roboScroll(ctx) }` (`content.js:1761-1762`), que raspa o `innerText`
  da página e manda como bilhetes. COMPROVADO estaticamente para a GiroCerto: o `content.js` da
  0.7.83 (`git show 2d88a34^`) tem 0 ramos `casa === "girocerto"` e 0 menções no `popup.js`,
  enquanto o servidor atual responde `"GIROCERTO": "texto"`. O servidor aceita (origem
  `girocerto.fun` bate com a sessão), e o texto segue para a IA.
- Regras duplicadas no cliente: `CASA_HOSTS` (popup.js) "espelha o `_HOSTS_POR_CASA`", o
  mapa casa → inject (`popup.js:366-480`), `X1_ESPELHOS_MOVEIS`, os ramos do robô por casa. Toda
  mudança nessas listas só chega ao usuário por reinstalação manual. Exemplo real: até a 0.7.85 o
  popup barrava `betfury.io` (commit `ea9de0e`, s456).
- **Skew entre perfis do MESMO dono (virada da Ficha).** `virada.resolver_no_extrair` decide se
  "o cru não chegou" segura a aposta olhando se **o dono** mandou cru daquela casa nos últimos
  7 dias (`virada.py:774-782`, `CRU_RECENTE_DIAS`). A pergunta é por dono+casa, não pela sessão
  nem pela versão. Um dono com dois perfis Octo, um atualizado e um velho (sem cru), tem as
  apostas do perfil velho seguradas como "captura incompleta" até 2 `/extrair` ou 24 h
  (`SEGURADA_EXTRAIRS`, `SEGURADA_HORAS`). COMPROVADO por leitura; frequência real é HIPÓTESE.
- Moeda: o texto só escreve `Moeda:` quando não é real, e o próprio servidor diz que "a ausência
  ali não distingue real de extensão antiga" (`ficha.py:315`). Extensão anterior à linha (commit
  `aeba412`, 03/10) em casa cripto/EUR cai na moeda da conta, sem aviso de contradição. Impacto
  depende do cadastro da conta: HIPÓTESE de dano real.

**Severidade.** Alta (casa nova com extensão velha grava lixo ou paga IA à toa; skew entre perfis
segura aposta real).

**Pontual ou família.** Família: "o servidor sabe e não decide".

**Correção estrutural.** Uma tabela de compatibilidade no servidor: `versao_minima` global e por
casa (a versão em que a casa entrou ou teve conserto de contrato). `/captura/conectar` e
`/captura/validar` recusam com mensagem clara ("esta casa exige SharpenUp ≥ 0.7.84; baixe aqui")
e `/captura/enviar` recusa com `426`. O aviso de versão ganha gravidade (`obrigatoria` ×
`recomendada`). Listas de hosts e casa → inject passam a vir do servidor no `/validar` (o código
dos injects continua no pacote, mas o roteamento não). A pergunta "este cliente manda cru?" passa
a ser da sessão (`versao_ext`), não do dono.

---

## A4. Captura grande morre em HTTP 400 no limite de 1 MB do multipart, e o Reenviar repete o 400

**Sintoma do usuário.** Volta depois de meses, roda "Copiar bilhetes" com janela grande (ou a
primeira captura de uma casa de replay longo), vê "Erro ao enviar (400)". O popup oferece
Reenviar, que falha igual. No dia seguinte o aviso some e o trabalho também.

**Mecanismo.**
- O texto inteiro vai num campo de formulário (`fd.append("texto", texto)`,
  `background.js:180`), num envio único, sem fatiar (`content.js:2056-2060`).
- O Starlette limita cada parte sem filename a 1 MB (`max_part_size`) e responde 400
  "Part exceeded maximum size of 1024KB.". Nenhum override no app (`grep max_part_size app/`
  vazio). O `requirements.txt` fixa `fastapi>=0.115.0,<0.116.0`; o `fastapi 0.115.14` exige
  `starlette>=0.40.0,<0.47.0`, e tanto o 0.40.0 quanto o 0.46.2 têm o limite (conferido no
  wheel baixado).
- O cliente trata 400 como erro genérico (`background.js:201`), mantém o `envioPendente`, e o
  Reenviar manda exatamente o mesmo texto. O `render` do popup apaga a pendência com mais de 24 h
  (`popup.js:646-648`).

**Evidência.** COMPROVADO localmente com a assinatura exata da rota (`e2_limite_multipart.py`):
500 KB → 200; 1.000 KB (com acentos) e acima → `400 Part exceeded maximum size of 1024KB.`
Tamanho médio de bloco medido com a fotografia do harness (`foto.json`, saída em
`tasks/…/bu5c15tct.output`): de 269 B (Pinnacle) a 1.136 B (Lottu). O teto cabe entre
**≈920 bilhetes** (Lottu, Cloudbet, Tivo, Betfast, Novibet: ~1.000) e **≈3.900** (Bet365,
Pinnacle) por envio. Os injects aceitam muito mais: `TETO_PAGINAS` de 200 a 500 páginas,
`COUNT_TETO = 25000` na 1xBet, `DIAS_HISTORICO = 1095` na Vave. Que algum usuário já tenha
batido nisso em produção é HIPÓTESE (não li log de produção).

**Severidade.** Alta para quem volta; nula para quem captura todo dia.

**Pontual ou família.** Família "o envio único não tem teto de tamanho nem fatiamento".

**Correção estrutural.** Fatiar por bilhete no cliente (lotes de ~300 blocos ou 512 KB), cada
lote com id e número de sequência, e o servidor confirmando cada um de forma durável (A1). Em
paralelo, `request.form(max_part_size=…)` explícito no servidor e 413 com texto acionável em vez
de 400 genérico.

---

## A5. Parcial vira completo: erro, teto e "30 s parado" encerram a rodada como se fosse o fim

**Sintoma do usuário.** A captura "deu certo", com menos bilhetes do que a casa tem. Nenhum
aviso. O próximo uso não recupera, porque a janela de dias é curta (A6).

**Mecanismo.**
- Nos replays, erro de rede ou HTTP não-ok no meio da paginação faz `return` e o `finally`
  marca `fimReplay = true` e envia (`kto_inject.js:257-261`, `:272-286`; `vb_inject.js:262-283`).
  Teto de páginas também (`vb_inject.js:278`: `TETO_PAGINAS = 60` × 10 = **600 bilhetes por
  aba** em toda a família Altenar: VaideBet, Esportiva, Jogo de Ouro, Betrebels, BetMartini,
  Vavada, Kikobet, Tornadobet, Sportaza). Só sai no `console.log`.
- Das 31 injeções, 20 não mandam campo de erro nenhum ao content (contagem `erro *:` por
  arquivo). Nas 11 que mandam, o content só mostra o erro quando a rodada deu **zero** blocos
  (`content.js:1767`); com 1 bloco ou mais, o erro vai ao console (`:4502`, `:4722`, `:5683` …)
  e a linha `:2049` **apaga o `lastError`** ("rodada OK").
- O content desiste depois de 30 s sem crescer e processa o que tem (29 laços com esse corte,
  ex. `content.js:6482`).
- O texto enviado não tem marcador de "incompleto"; o servidor não tem como saber.

**Evidência.** COMPROVADO por leitura (linhas citadas). O teto Altenar e o comportamento do
`finally` não dependem de dado.

**Severidade.** Média-alta. É o caso normal de quem volta com muito histórico.

**Pontual ou família.** Família, transversal a todas as casas de replay.

**Correção estrutural.** Um estado de rodada com três valores (`completo`, `parcial:<motivo>`,
`vazio`) emitido por todo inject, carregado no texto/cabeçalho do envio e mostrado na tela
("capturei 600; a casa tem mais; motivo: teto"). Teto deixa de ser silencioso: ou sobe com aviso,
ou vira paginação por janela de data. O servidor guarda o estado da rodada no log da captura.

---

## A6. Horizonte: 30 dias fixos para quase todos, e a única marca d'água (Bolsa) é gravada antes do envio

**Sintoma do usuário.** Volta depois de 3 meses, captura, e os 2 meses do meio não aparecem.

**Mecanismo.**
- `lookbackDias` padrão 30 (`content.js:1364`, `popup.js:703`), persistido por perfil, global
  para todas as casas, sem relação com a última captura daquela conta. Nada no `/validar`
  informa "a última aposta desta conta no servidor é de X".
- A Bolsa de Aposta é a única com horizonte pela última varredura (`_bolsaHorizonte`,
  `content.js:3484-3504`). Só que `_bolsaCarimbar` roda **ao fim da raspagem**
  (`content.js:1483`), antes do `ENVIAR_TEXTO` (`:2060`) e sem saber se o servidor gravou. Se o
  envio falha (sessão morta é o normal para quem volta) e o usuário, em vez de Reenviar, clica
  de novo em Copiar, a 2ª rodada é curta (15 dias liquidadas + 3 de folga) e **sobrescreve** o
  `envioPendente` da rodada longa (slot único, `:2057`). O que estava entre 18 dias e 1 ano
  some. E a chave é `capUltima:<casa>` (`:3473`), sem conta: trocar de conta logada na casa no
  mesmo perfil herda o carimbo da outra.
- GiroCerto: a API entrega só os 50 mais recentes (comentário em `content.js:483` e a decisão do
  `PRINT_LIBERADO`), sem nenhum aviso ao usuário que volta.

**Evidência.** COMPROVADO por leitura (ordem das chamadas `:1483` → `:2057` → `:2060`). O cenário
"clicar Copiar de novo" é HIPÓTESE de comportamento, mas é o reflexo natural depois de "Erro ao
enviar".

**Severidade.** Média.

**Pontual ou família.** Família "marca d'água gravada pelo cliente sem ack do servidor".

**Correção estrutural.** A marca d'água sai do cliente: `/captura/validar` devolve, por conta, a
data da última aposta liquidada e da mais antiga aberta que o servidor tem; a extensão usa
`max(lookback, hoje − última + folga)`. Se continuar local, ela só avança depois do ack durável
(A1) e é chaveada por `dono|conta`.

---

## A7. `envioPendente`: slot único, validade de 24 h, e o Reenviar não confere para onde vai

**Sintoma do usuário.** "Nada foi perdido, reconecte e reenvie", e depois: a pendência sumiu, ou
foi parar na conta errada.

**Mecanismo.**
- Slot único: cada rodada grava `envioPendente` antes de enviar (`content.js:2057`); uma
  segunda rodada apaga a primeira.
- Poda silenciosa: >24 h e some (`popup.js:646-648`). Quem volta depois de um fim de semana
  perde.
- O Reenviar sai do popup (`popup.js:510`), sem aba: `hostDaAba(undefined)` dá `""`, então não
  vai `origem` e o servidor pula a amarração casa↔site (`main.py:4286-4300`). E o popup não
  compara `pend.casa` com a casa pareada agora (`popup.js:502-521`). Se o usuário reconectou com
  o código de outra conta ou outra casa, o texto vai para lá. A trava de conta errada
  (`_checar_conta_errada`) só pega se a maioria dos códigos já existir noutra conta, então não
  pega a 1ª captura.
- Contexto invalidado (content órfão depois de atualizar a extensão): `chrome.storage` e
  `runtime.sendMessage` lançam; o `try {} catch {}` do `:2057` engole a falha de gravar e o toast
  `:2067` diz "guardados ... nada foi perdido". HIPÓTESE (comportamento documentado do Chrome
  para script órfão; não reproduzido aqui).
- Cota: sem `unlimitedStorage` no manifest, `chrome.storage.local` tem 10 MB. Somando
  `cruEnviado` (até 20.000 entradas, ≈120 B cada, ≈2,4 MB), `b3Detalhes` (até 3.000 entradas com
  pernas) e um `envioPendente` de vários MB, a gravação pode estourar; o erro é engolido nos três
  lugares. HIPÓTESE (precisa medir um perfil real).

**Severidade.** Média (e alta no caso "conta errada").

**Correção estrutural.** Pendências viram fila (lista com id, casa, conta, dono, sessão), e o
Reenviar só manda para a mesma casa e conta; se o pareamento mudou, pergunta. Validade longa
(ex.: 30 dias) com aviso, nunca poda muda. Com A1 resolvido, a pendência vive no servidor e o
cliente só guarda o que nem chegou lá.

---

## A8. Registros locais sem dono, sem conta e sem versão

| Chave (`chrome.storage.local`) | Quem grava | Quem lê | Expira | Escopo | Risco depois de meses parado |
|---|---|---|---|---|---|
| `token, casa, parceiro, modo, dono, codigo` | popup `conectar` (`popup.js:326`) | popup, background, content | 401 limpa | perfil | Morre a cada deploy (A1); FAB não valida antes de raspar |
| `lastError` | background, content | popup | quando uma rodada "dá certo" | perfil | Apagado por rodada parcial (A5) |
| `envioPendente` | content `:2057` | popup | 24 h, ou sobrescrito | perfil, 1 slot | A7 |
| `lookbackDias`, `stopId` | popup | content `:1363` | nunca | perfil, todas as casas | `stopId` digitado numa casa vale para todas; 30 dias fixos (A6) |
| `bfQtd, bfDias, bfFull` | popup | content | nunca | perfil | baixo |
| `capUltima:<casa>` | content `:3514` | content `:3487` | nunca | casa (sem conta) | A6 |
| `cruEnviado` | `cru.js:118` | `cru.js:86` | 60 dias / 20.000 | `origem|familia|codigo` (sem dono, sem conta) | Não reenvia cru para outro dono/conta no mesmo perfil; o servidor depende do cru para a virada (A3) |
| `cruDiag` | `cru.js` | ninguém na UI | últimos 20 | perfil | diagnóstico invisível ao usuário |
| `b3Detalhes` | content `:1067` | content `:8773-8866` | poda >3.000 | perfil, sem versão | Detalhe (`code, da, legs`) de versão antiga é reusado para sempre e o detalhe nunca é rebuscado (`pronto`, `:8778`); um conserto de parser não alcança bilhete já lembrado. HIPÓTESE de dano: não achei mudança de formato do detalhe desde a criação |
| `roboPendente` | popup `:234` | background | 90 s | aba | baixo |
| `frameAtivo, frameRect, frameCount` | content, popup | content | nunca | perfil | baixo |
| `apiBase` | ninguém na UI | `config.js` | nunca | perfil | baixo |
| `localStorage` da casa: `REC_KEY` | `b3_inject.js:118` | b3 | ? | página | baixo |

Nenhuma chave tem número de versão de esquema, e nenhum `onInstalled` migra ou limpa estado.
Variáveis globais do service worker: nenhuma guarda estado de negócio (o `background.js` lê tudo
do storage a cada evento), então o SW morrer e renascer não perde nada. COMPROVADO por leitura.

**Correção estrutural.** Prefixo de esquema (`v2:`) e `chrome.runtime.onInstalled` que migra
ou zera o que mudou de forma; chave com `dono|conta` onde o dado é da conta; o "já enviado" do
cru passa a ser decidido pelo servidor (o cliente manda hashes, o servidor diz quais faltam).

---

## A9. Content script órfão depois de atualizar (HIPÓTESE forte)

Depois de recarregar a extensão, o `content.js` da aba aberta perde o `chrome.runtime`. O popup
reinjeta (`popup.js:353`), mas o `content.js` começa com `if (window.__sharpenupCS) return;`
(`content.js:10`). Se o mundo isolado da aba for o mesmo depois do reload (mesmo id de extensão),
a nova cópia sai na guarda e o `START_ROBOT` não tem quem responda: o popup fecha e nada
acontece. O próprio popup já trata isso no Resolver ("Recarregue a página (F5)",
`popup.js:633`), o que indica que o sintoma foi visto. Não reproduzi no Chrome real.

Correção: a guarda guarda a versão e o id de runtime (`chrome.runtime.id` + um nonce do SW); se
o contexto antigo estiver invalidado (`chrome.runtime?.id` indefinido), a cópia nova assume.

---

## O que mede o quê (gates existentes)

- `node extensor/harness/run.mjs`: **verde**, 62 casos, 1.150 bilhetes (saída em
  `harness_out.txt`). Cobre formatação por casa com a versão atual. Não cobre: duas versões na
  mesma página, reinjeção, tamanho de envio, servidor, sessão, deploy, tempo.
- Nenhum teste no servidor recebe um payload de versão antiga.

## Experimentos desta auditoria (reexecutáveis)

- `e1_inject_velho_na_aba.mjs <velho.js> <novo.js> <fixtures>`: duas versões do mesmo inject no
  mesmo mundo MAIN. `old/thp_inject_0785.js` veio de `git show 464d5c4^:extensor/thp_inject.js`.
- `e1b_com_latencia.mjs`: o mesmo, com latência realista e o corte "1º fim + 400 ms" do content.
- `e2_limite_multipart.py` (rodar com `python -I`): a assinatura da rota `/captura/enviar` contra
  o limite de parte do Starlette.
- `foto.json`: fotografia do harness (`SHARPENUP_FOTO`) usada para medir bytes por bloco.
- `whl/`: wheels de `fastapi 0.115.14` e `starlette 0.40.0 / 0.46.2`, para conferir o limite na
  faixa fixada em produção.

## O que não consegui verificar

- Nada em produção: versões instaladas pelos usuários, logs de 400/401/429 do `/captura/enviar`,
  quantas capturas ficaram órfãs em fila, versão exata do Starlette na imagem da Railway (só a
  faixa permitida pelo `requirements.txt`).
- Comportamento real do Chrome para: guarda `__sharpenupCS` depois de reload (A9), exceção de
  `chrome.storage` em script órfão (A7), ordem de `document_start` entre duas cópias (A2), cota de
  `chrome.storage.local` num perfil real (A7), throttling de timers em aba de fundo durante uma
  raspagem longa.
- Se o shell `/app.html` recarrega o `index.html` ao trocar de tela (o que tornaria a perda do A1
  ainda mais comum).
- Se o Railway roda mais de uma réplica (o `virada.py` supõe uma; com duas, a fila do A1 nem
  sempre está no processo que recebe o poll).
- Payloads antigos contra o servidor inteiro (`/extrair` + IA + `/salvar`): exigiria banco e
  chave da Anthropic. A comparação de contrato foi estática (git) e por simulação de fronteira.
- Se algum formato de `b3Detalhes` mudou desde 23/07 (só conferi o commit `d458c3a`, que mexe no
  summary, não no detalhe).
