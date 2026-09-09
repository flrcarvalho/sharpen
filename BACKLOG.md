# BACKLOG — o que está aberto no Sharpen / Planilhador

> **Este arquivo responde UMA pergunta: o que está aberto e o que vem a seguir.**
> Estado atual do projeto → [`STATUS.md`](STATUS.md).
> Regras vinculantes → [`CLAUDE.md`](CLAUDE.md).
> O que aconteceu → [`docs/HISTORICO.md`](docs/HISTORICO.md).
>
> Criado em **2026-09-06** pela faxina de documentação
> ([`docs/FAXINA_PROPOSTA.md`](docs/FAXINA_PROPOSTA.md), Lote F). Até aqui o backlog vivia
> espalhado por **quatro** arquivos que se contradiziam — e três deles descreviam o projeto
> entre 30/06 e 19/07. A varredura da s261 já tinha registrado o custo disso: *"a primeira
> pendência que eu fui atacar já estava feita desde 26/07"*.

---

## Como ler este arquivo

**As marcas são as da varredura da s261** (`STATUS §5`), mantidas de propósito porque elas
separam o que foi provado do que foi suposto:

| Marca | Significa |
|---|---|
| **VIVA** | confirmada no código, com arquivo:linha conferido, na data indicada |
| **NÃO-MEDIDA** | plausível, mas ninguém provou (falta banco, amostra ou reprodução) |
| **HUMANA** | depende de ação fora do repo (Feca, Railway, Telegram, extensão) |

**Duas lições da varredura da s261, que continuam valendo:**

1. **Referência de linha apodrece.** O código anda, o backlog não. `app.js:1183`,
   `content.js:911` e `main.py:2354` já apontavam para linha errada. Referência aqui é
   **pista, nunca endereço** — confirme por `grep` do símbolo antes de agir.
2. **A ausência de marca não é "vivo".** Item sem varredura é item **não verificado**, e
   descobrir isso no meio da execução custa meia sessão.

**Regra de higiene:** item fechado sai daqui na mesma sessão em que fecha. Se virou regra,
vai para o lugar canônico (`MASTER_*` / `CASA_*` / `CLAUDE.md`); se virou história, vai para
o `docs/HISTORICO.md`. Este arquivo só guarda o que está **aberto**.

**Gate:** `python tools/check_docs.py` (invariante #10 do `CLAUDE.md`).

---

## 1. Bloqueado por ação humana

> Não há o que codar. Falta alguém clicar, colar uma variável, criar um grupo ou mandar um
> print. São os itens que ficam parados mais tempo justamente por isso.

*(bloco herdado do `STATUS §5`, verbatim — a varredura de 10/08, s261.)*

### Bloqueado por ação humana (não é bilhete)

- ~~Login `ZoraEsports` 401~~ **RESOLVIDO na própria s238** — mas a lição fica: **conta nova deployada ANTES da env var de senha nasce com hash vazio na tabela `usuarios`, e o seed (`ON CONFLICT DO NOTHING`) nunca conserta** — colar a env var depois não basta (desde o Deploy B da s233 quem autentica é a TABELA via cache; a docstring do seed ainda descreve a Fase 1). Medido: `length(senha_hash)=0` na linha. Fix: UPDATE manual do hash (o Feca rodou o script via `!`; o classificador do Claude Code barra mexida direta em credencial de produção) → login 200 na primeira tentativa. **Ordem certa daqui em diante: env var no Railway PRIMEIRO, push da conta depois.**
- **Env vars de senha no Railway (s216, s218, s220) — estado NÃO instrumentado.** `SENHA_LAVAPESSOAL_HASH` **está no ar e o Lava entra** (confirmado pelo Feca em 31/07, s222). `SENHA_WILLIAMOLIVEIRA_HASH` e `SENHA_VINICIUSOLIVEIRA_HASH`: **não confirmadas** — podem já ter sido coladas; ninguém atualiza esta linha quando a ação acontece fora do repo.
- **Login por Telegram: o botão saiu da tela, a causa raiz continua aberta (s324). HUMANA + NÃO-MEDIDA.** O relato foi de uso: aperta e nada acontece. O `Entrar com Telegram` foi retirado do `/login`; o backend segue inteiro (`/auth/telegram/*`, `/auth/metodos`, `tests/test_login_social.py`). **Ninguém mediu por que o clique morre.** Suspeito principal: o `/setdomain` do BotFather nunca apontou para `www.sharpen.bet`, e o `oauth.telegram.org` recusa domínio não registrado sem sair do lugar. **Como medir, sem tocar em código:** abrir `/auth/telegram/ir` com o console aberto e ler o que o `oauth.telegram.org` responde. Se for isso, o conserto é no BotFather, fora do repo. Para devolver o botão: repor o `<a id="btn-telegram">` no `login.html`, voltar `temSocial` a olhar `m.telegram` e apagar `test_botao_telegram_esta_fora_da_tela` (o próprio teste diz isso).
  > ⚠️ **Esta linha é uma pendência declarada, não uma medição.** Não afirme a partir dela que um login está quebrado — foi exatamente o erro cometido na s222. Para saber de verdade: `POST /login` devolvendo **200** = hash certo; **401** = ausente ou diferente (429 é rate-limit, 500 é erro do app). Sem esse teste ou a palavra do Feca, escreva "não confirmado".

  Procedimento, se algum dia faltar mesmo: os hashes **não entram no git** — se perdidos, gerar de novo com bcrypt e colar na caixa de Variables do Railway (literal, 60 caracteres, sem espaço nas pontas; o `$` do `$2b$12$…` chega mutilado por qualquer shell que interpole variável).
- **`LavaPessoal`: 30 apostas com stake 0** (s222) — importadas, mas **invisíveis no dashboard** (`dashboard_rows` corta `stake <= 0`). 23 delas têm resultado. Aparecem na grade da **Extração** (`list_bilhetes` não filtra), então a correção é humana: preencher a stake lá e elas entram no P/L. Todas do tipster `Peixe`, abr–jul.
- **`LavaPessoal`: duas contas pré-existentes vazias** (s222) — `Bet365 | monster@2025 [Richard]` e `Betano | karlmarxrosa@aurainteligente.com [221193Cy*]`, criadas em 30/07, arquivadas, **zero** bilhetes. Não vieram do import e não foram tocadas. Se forem lixo de teste, apagar pelo botão Excluir do Painel de Contas (s219).

*(movidos da §2 em 06/09 — mesma marca HUMANA, texto intacto.)*

- **PassaTips VIP — o bot está pronto e PARADO num passo humano (s273). HUMANA.** Falta
  `PT_APOIO_ID`: **a Bot API do Telegram não cria grupo** (só cliente MTProto), então o
  apoio tem de ser criado à mão — Feca + `@passapano` (id `8290339271`) + `@sharpenbetbot`
  como **admin** (apagar mensagens e fixar). Falta também `SHARPEN_SENHA_PT` no Railway.
  O destino já está conferido por `getChat` (`-1003907895270`, `type: channel`) e o bot já
  é admin lá com `can_post_messages`/`can_edit_messages`. O tenant é **inerte** sem
  `PT_APOIO_ID`, então o código já em produção não faz nada até isso existir. **A 1ª
  captura ao vivo tem duas leituras críticas:** o bilhete tem de sair com o **esporte
  certo** (o padrão novo põe na 1ª linha) e a **casa vinda do host do link** — é o que a
  correção do `embutirLinks` destravou, e nenhum lote real atravessou a ponte ainda.
  Contador semeado em `data/passatips/contador.json` = **258**; a próxima do canal é a
  **#259**.
- **PassaTips — 3 passos humanos para fechar o buraco do #259 (s276). HUMANA.** O
  `/contador 271` já foi feito (18/08 09:33), então daqui para frente está limpo. Falta:
  **(1)** o tipster **repostar a aposta de hoje** no apoio (`Futebol` / `Over 3.5 gols -
  @2,25 (1,00u)` / link Betnacional) — ela virá como **#272**, porque hoje ela **não está
  na base**: o bot salvou às 09:20 sobre a linha importada `PT202608-259` e foi absorvida;
  **(2)** `/anular #259` para desarmar o painel antigo — ⚠️ isso **apaga** a linha
  `Under 1.5 cartões Elche` (17/08, id 186709), porque o bot guardou o id dela por engano;
  **(3)** reimportar a planilha, que recria essa linha exata. **Ordem importa: (1) antes de
  (2).** Enquanto o painel do #259 estiver armado, um clique ✅ vira o `L` do dia 17 em `W`
  (`resultado` não é congelado).
- **Zora — falta `/ressincronizar` (s276). HUMANA.** Só Chutes (62/62) e Rei do Criquete
  (65/67, 114 linhas repostas) já foram. A Zora é o único tenant que não passou; ela tem 17
  bilhetes e a última escrita é de 02/08, então provavelmente não há nada a repor — mas isso
  é dedução, não medição.
- **As 3 senhas de tipster no Railway podem sair (s276). HUMANA.** `SHARPEN_SENHA`,
  `SHARPEN_SENHA_ZORA` e `SHARPEN_SENHA_RC` só servem de fallback agora. Com os quatro
  botões ligados no `/admin`, apagá-las fecha a porta velha. Confirmar antes no log do boot:
  cada tenant loga `[sharpen:<user>] token de serviço`.
- **Bot Sharpen no Railway (s251) — falta o smoke test de ponta a ponta, que é do Feca.** O serviço está no ar e verificado por fora (contador conferido de volta do volume, `login ok` nas duas contas, fila do Telegram drenando), mas **nada passou pelo Telegram ainda** — eu não tenho acesso ao app. Fazer: mandar `/status` no apoio do Só Chutes; se responder com os bilhetes do mês, o caminho todo fechou. Sobraram dois diretórios aninhados de uma tentativa de upload (inofensivos, o `storage.js` não os lê), e **o CLI recusa deleção pedida por agente** — rodar `railway volume files delete --volume sharpen-bot-volume /sochutes/sochutes` e o mesmo para `/zora/zora`. **Solto (segurança):** o `SHARPEN_SENHA` do `SoChutes` tem **4 caracteres** numa conta de produção exposta na internet; trocar é `.env` → `scripts\exportar_env_railway.ps1` → `railway redeploy`. Detalhes de operação vivem no `README.md` do repo do bot, não aqui.

### 1.1 Rotação da senha do Postgres — `AUDITORIA_2026 #1`. HUMANA.

Runbook pronto e sem segredo nenhum dentro:
[`docs/runbook-rotacao-postgres.md`](docs/runbook-rotacao-postgres.md). Causa ~30-60s de
blip no app durante o redeploy; fazer em horário de baixo uso. As variáveis de conexão no
Railway são **literais** (não referências `${{}}`), então cada uma precisa ser atualizada à
mão.

### 1.3 O `STATUS.md` está a 1,8 KB do teto — o próximo `/encerrar` estoura o gate. **VIVA (07/09)**

Medido em 07/09: **48,2 KB** contra o teto de **50 KB** do `tools/check_docs.py`, com 3
blocos de sessão e 2 `_Anterior:` (ambos no máximo). O bloco da próxima sessão reprova o
gate, e é para isso que ele existe.

**A saída é rodar o corte, não subir o teto.** O procedimento é o do Lote B da faxina e o
`/encerrar` já o descreve: move o bloco de sessão mais antigo e o `_Anterior:` excedente
para `docs/historico/HISTORICO_s300-s327.md`, preservando o texto integral. Subir o teto
uma segunda vez é como o arquivo chegou a 187 KB na primeira.

> Não é escopo da faxina de documentação — ela fecha no Lote A. Fica aqui porque o gate vai
> reprovar e alguém vai precisar saber o que fazer.

### 1.2 `golden_set/bilhetes/` está vazio — `TURBO 19/07 #21`. HUMANA. **VIVA (06/09)**

Medido hoje: `golden_set/` tem só o `descricoes.jsonl` e o `README.md`. **Não existe
nenhuma regressão print → TSV por casa** — editar um `§9` errado não quebra teste nenhum.
Bloqueado em prints reais do Feca. É a mesma lacuna que a auditoria de 20/07 levantou por
outro caminho: *"a extração print→TSV nunca é verificada ponta a ponta"*.

---

## 2. Bloqueado por amostra / bilhete real

> A regra existe no MASTER; falta a casa mostrar o caso. Não dá para escrever o de-para de
> um rótulo que ninguém viu — e chutar aqui é o mesmo que o `else` do formatador: cria linha
> `aberta` para sempre, sem erro em lugar nenhum.

*(bloco herdado do `STATUS §5`, verbatim — a varredura de 10/08, s261.)*

> **Varrido em 10/08/2026 (s261), contra o código e o git.** Motivo: a primeira pendência
> que eu fui atacar (`renomear_parceiro`) **já estava feita desde 26/07** — o §5 misturava
> item vivo com item vencido, e não dava para saber qual era qual sem abrir o código.
>
> As marcas usadas abaixo:
> **✅ VIVA** = confirmada no código nesta data, com o arquivo:linha conferido ·
> **NÃO-MEDIDA** = plausível, mas ninguém provou (falta banco, amostra ou reprodução) ·
> **HUMANA** = depende de ação fora do repo (Feca, Railway, Telegram, extensão).
>
> **Duas coisas que a varredura ensinou, e que valem para a próxima:**
> **(1) Referência de linha apodrece.** Três itens apontavam para linha errada
> (`app.js:1183`, `content.js:911`, `main.py:2354`) — o código andou, o §5 não. Referência
> aqui é **pista, nunca endereço**: confirme por `grep` do símbolo antes de agir.
> **(2) A ausência de marca não é "vivo".** Item sem varredura é item **não verificado** —
> e o custo de descobrir isso no meio da execução é meia sessão.

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Bet365 — sistema, as 3 linhas `L` congeladas (s265). HUMANA + NÃO-MEDIDA.** O conserto da
  odd de sistema vale para captura nova, e as **10 abertas** se corrigem sozinhas na próxima
  passada do robô (o `ON CONFLICT` refresca `odd` enquanto `extraction_state='aberta'`). As **3
  já resolvidas como `L`** ficaram com a odd do produto e o UPSERT **não** as toca. Corrigir
  exige a odd **por perna**, que o banco não guarda → só re-lendo o bilhete na casa. Não mexer
  sem o Feca: `L` não move P/L (perda = −stake), então a urgência é baixa e o risco de UPDATE
  cru é alto. Medir de novo com `python scripts/medir_sistemas_bet365.py` (read-only).
- **Bet365 — sistema SEM irmão só some na base ANTIGA (s265, 2ª parte). ✅ RESOLVIDA para
  frente, HUMANA para trás.** A partir da 0.6.45 a captura grava `sistema`/`sistema_linhas`,
  então bilhete novo é medido sem heurística (`sistema IS NOT NULL`) — e como a estrutura
  atravessa o congelamento do UPSERT, **re-capturar bilhete antigo faz backfill**. O que ainda
  não aparece é só o que nunca foi re-capturado: ali valem as heurísticas de irmão, que perdem
  quem apostou só as duplas. Fecha sozinho conforme o histórico for re-passado; medir com
  `python scripts/medir_sistemas_bet365.py` (a seção **(0)** é a exata).
- **Trixie / Yankee / Lucky na captura (s265). NÃO-MEDIDA — sem bilhete real.** Sistemas que
  **misturam** tamanhos de linha não fecham `C(n,k) = BC`, então o robô entrega o dado e manda
  calcular pelo `MASTER_RESULTADO §7` em vez de emitir número. Nenhum apareceu nos payloads
  vistos até aqui; com um bilhete real dá para travar a fórmula deles no harness também.
- **Betfair:** cashout **parcial** (`isPartialCashOut`) sem amostra — o total já está travado no harness (2 casos) · HW/HL sem amostra · Each Way com `0 < Retorno < Stake` (o §5 não cobre essa faixa; hoje sai "a conferir", sem chute)
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

- **Betfast / Tivo (s211):** cashout · bônus · aposta de sistema · outright · **aposta ABERTA** (as 50 da amostra são liquidadas) · `§9` de duas categorias (`Total de defesas do goleiro` · `Handicap de mapas`/`Map Advantage`)
- **Jonbet:** ~~captura NÃO validada ao vivo~~ **VALIDADA na s249** — a extensão capturou na 1ª tentativa e gravou **13 bilhetes** (3 W · 7 L · 3 abertas), com código, stake e odd conferidos no banco. **A coluna Data ficou provada ao vivo:** saiu 04/08 (3) · 05/08 (4) · 06/08 (3) · **07/08 (3)**, e as 3 abertas são justamente as de 07/08 — eventos futuros, que a data de **colocação** teria carimbado em 05 ou 06/08. **Falta só a conferência visual do Feca contra o card** (contagem e datas lado a lado). Segue sem amostra: **cashout executado** · múltipla · bet builder · sistema · `half-won`/`half-lost` · `void`/`refund`/`rejected` · **boost** (`boost:false` em tudo) · **imposto** (`payout_tax:"0"` e `taxes` ausente — quando aparecer, decidir de uma vez se o `W` usa retorno bruto ou líquido, ver `CASA_JONBET` Feedback #2). `§9` só tem os 3 mercados de badminton confirmados.

- **Betboom (s250):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados, mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.38**), **Ctrl+Shift+R** em `betboom.bet.br`, Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **A leitura crítica é a DATA** — nesta casa colocação e evento divergem em **7 de 7**, e a coluna Data tem de sair com a do **evento**. Sem amostra (a conta tem 7 bilhetes, todos simples, badminton): **cashout executado** · múltipla · bet builder · sistema · `half-won`/`half-lost` · `void`/`refund`/`rejected` · boost · imposto. As abas `Cashout efetuado`, `Canceladas` e `Reembolsadas` **existem na tela** mas vieram vazias — quando encherem, elas fecham buracos das **duas** casas BetBy de uma vez. `§9` só tem 2 mercados confirmados (`Vencedor`, `Handicap pontos`); `Total pontos` está na Jonbet e **não** foi importado para cá de propósito (camada fina).

- **Stake (s257):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados (inclusive o replay, contra o servidor real), mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.41**), **Ctrl+Shift+R** em `stake.bet.br`, Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **As duas leituras críticas são o STAKE DA ANULADA** (tem de sair `34,45`, não `0,00`) e o **resultado da anulada** (`V`, não `L` — o dinheiro é o mesmo zero da perdida). Sem amostra (a conta tem 17 bilhetes, todos múltiplas de 2 a 4 pernas, futebol e tênis): **simples** (`bet_type` foi `1` nas 17 — não há de-para provado para esse campo) · **boost** (`*_boosted` todos `null`, embora a home anuncie promoções) · **cashout executado** (os campos `bet_cashout_*` só existem no endpoint de ABERTAS; que `bet_status` sobra depois de sacar é desconhecido) · freebet/bônus (`bet_bonus_type` sempre `null`) · bet builder · eSports · `half-won`/`half-lost`. `§9` só tem 6 mercados confirmados; `Total asiático` está mapeado para `Gols` pelo princípio do objeto, **sem sinônimo no MASTER** (registrado no Feedback da casa).

- **Pitaco (s270):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados
  (o replay rodou contra o servidor real, 200 e resposta idêntica à da tela), mas nenhum lote
  passou pela extensão. Fazer: recarregar a extensão (**0.6.46**), **Ctrl+Shift+R** em
  `pitaco.bet.br`, abrir **Minhas Apostas**, Conectar → "Copiar bilhetes". **As duas leituras
  críticas são do bilhete `80010000038606210`: a ODD tem de sair `3,6795` (não `3,67` — a casa
  exibe a odd arredondada e ela erra R$ 0,95 no retorno) e a DATA tem de ser a do evento,
  `15/08`, não a da colocação, `14/08`.** Conferir também que o lote traz **71** bilhetes (49
  finalizados + 22 abertos) e não 31 — 31 é o que a paginação por página devolveria, e é
  exatamente o defeito que o inject evita. Sem amostra: **bilhete simples** (a conta tem 51
  duplas e 20 triplas, nenhuma simples) · **cashout executado** (o filtro "Encerradas" veio com
  0 cards, embora o campo `.7` exista nas abertas com o valor de encerrar) · boost · freebet ·
  HW/HL. O `§9` tem 15 rótulos confirmados de 162 pernas reais. **A grafia já está unificada**
  (2ª parte da s270): a casa é `Pitaco` em toda a base — 57 bilhetes, 5 contas, resíduo zero
  da grafia velha e as 57 assinaturas conferidas contra o que a próxima captura vai gerar.

- **Novibet (s271):** o inject foi validado ao vivo — o `nv_inject.js` real rodou na página
  logada contra o servidor da casa e trouxe **42 bilhetes / 42 códigos únicos** (7 abertas,
  19 sistemas), com `hook:true`, `fim:true`, `truncado:false` e sem erro. Sem
  amostra: **bilhete simples** (a conta tem 3 de 2 seleções e 39 de 3) · **cashout executado**
  (`cashout` null em 42 de 42 — o card oferece, mas o preço vem por outro canal) · **imposto**
  (`withholdingTax` 0 em 35 de 35) · freebet · `costDiscount` · `isBanker` ·
  `overriddenResult` · e qualquer `result` fora de {Won, Lost, Pending} — **não há
  anulada/void na amostra**. O `§9` tem 34 rótulos confirmados de 123 pernas reais.
- **`Cobranças de lateral` e `Tiro de meta`: a régua ficou desalinhada de propósito
  (s273). NÃO-MEDIDA.** São a mesma família de `Faltas` (estatística de jogo), mas caem em
  lugares diferentes — lateral em `Outros` e tiro de meta em `Team Props`, por sinônimo
  explícito do `MASTER_APOSTAS §4`. A s273 criou **só** `Faltas`, que era o aprovado.
  Decidir se as duas viram categoria ou as duas viram `Outros` é mudança própria, com a
  regra de propagação inteira. Registrada no Feedback #2 da `CASA_BETFAST`.
- **O auto-deploy do `sharpen-bot` não está disparando com o push (s276). NÃO-MEDIDA.** O
  `casaPorHost` foi commitado às 12:07 e o bilhete `#131` falhou às 12:20 dizendo "não achei
  a casa" — código commitado e não rodando. É a mesma causa do `PT_APOIO_ID` não ser lido.
  **Deploy que não acontece é falha silenciosa:** o bot segue no ar respondendo, com código
  velho, e só se descobre por sintoma lateral. Investigar o gatilho do GitHub nesse serviço;
  até lá, conferir a aba Deployments depois de cada push.
- **O botão "Atualizar dados" mente na página pública `/tipsters/<slug>` (s276). ✅ VIVA.**
  A rota aceita e **ignora** o `?refresh=1` de propósito (cache de 5 min, `_PUBLICO_TTL`), e
  o botão promete algo que ela recusa — F5 e Ctrl+Shift+R também não furam, porque o cache é
  de servidor. Custou 4 minutos de "quebrou tudo" na s276. Duas saídas, decisão do Feca:
  esconder o botão no modo público (com rótulo "atualiza a cada 5 min") ou deixar o refresh
  furar o cache com teto por slug.
- **Imposto no `W`: bruto ou líquido? A decisão continua ADIADA, agora com duas casas
  esperando (s271).** A Novibet é a **primeira casa nossa com imposto explícito no payload**
  (`settlement.withholdingTax` + `taxBonus`), mas veio **0 em 35 de 35** — então dá para
  registrar o campo sem decidir a regra. A mesma pergunta está aberta na `CASA_JONBET`
  (Feedback #2, `payout_tax`). **Quando aparecer o primeiro bilhete com imposto ≠ 0, decidir
  de uma vez no `MASTER_RESULTADO`** e propagar às duas — decidir por casa criaria duas
  verdades para a mesma regra global.

- **Bot Sharpen — bilhete #21 do Só Chutes ainda está SEM a dupla (s252).** O fix está no ar (`dde8141`), mas ele não age sozinho sobre o passado: a recomposição roda quando o Telegram entrega um `edited_message`. **Fazer: editar a legenda do #21 no apoio outra vez.** Ela já diz `0,25u dupla`, então basta uma edição qualquer (pôr e tirar um espaço serve) para o bot responder `➕ Bilhete #21: acrescentei Sanguinetti + Sen 0.25u @ 9.75`, atualizar o post e planilhar. **O post do canal não é anulado nem renumerado** — os 28 👍 ficam. Qualquer pessoa com permissão de editar a mensagem serve; o bot escuta a edição, não quem editou. A dupla nasce **aberta** e a odd sai como produto das pernas (3,25 × 3 = 9,75), que é o que o card mostra; se algum dia divergir por boost ou arredondamento da casa, `/ajustar #21` com a foto crava a odd certa. **Sem amostra ainda:** a recomposição nunca rodou contra o Telegram de verdade, só contra o registro reconstruído no teste.
- **Betpix365 (s258):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados (inclusive o replay e a paginação, contra o gateway real), mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.43**), **Ctrl+Shift+R** em `betpix365.bet.br`, abrir **Minhas Apostas**, Conectar → "Copiar bilhetes". **A leitura crítica é a ODD DA MÚLTIPLA `5255274526`: tem de sair `4,23`, não `4,08345` nem `4,08`** — a casa paga "Ganhos extra" (R$ 0,15) por fora da odd, e é a 1ª casa Altenar em que a odd declarada não explica o retorno. Conferir também que o lote tem **9 bilhetes** (a conta inteira) e não 0 — se vier 0 com hook ATIVO, o aprendizado do molde falhou (sessão expirada ou path mudado), **não** é tela errada. Sem amostra (a conta tem 9 resolvidas e **zero abertas**): **aposta em aberto** (a armadilha do `totalWin` potencial não pôde ser verificada aqui — segue travada nos harnesses da VaideBet e da Esportiva) · cashout executado (`cashOutValue: 0` em 9/9) · V/HW/HL · freebet · aposta ao vivo (`isLive: false` em todas) · qualquer esporte além de **futebol** (`sportTypeId: 1` em 9/9) · os 7 valores de `status` fora de {0,1,2}. O `§9` tem 9 rótulos confirmados, de **uma** conta pequena — a lista vai crescer.

- **Jogo de Ouro — 1ª tentativa ao vivo FALHOU (10/08). Diagnóstico feito, conserto NÃO aplicado.** O Feca capturou e recebeu `Jogo de Ouro: 0 bilhetes. Hook: ATIVO · respostas da API: 0 · bilhetes vistos: 0 · abra o histórico COMPLETO`. **A causa raiz do lote vazio ainda não foi medida** (falta a versão da extensão e o console do Feca), mas a investigação achou um defeito certo: **a s258 mudou o mecanismo e deixou 3 lugares mentindo.** O `vb_inject.js` ganhou `RX_APRENDE = /widget(?:Expanded)?BetHistory/i`, que aprende url+headers de **qualquer um** dos dois widgets e reescreve o path no replay. Ou seja, desde a **0.6.43 o painel lateral já serve de molde e a tela cheia deixou de ser obrigatória**. Só que o `git show b59c3cc --stat` confirma que a s258 **não tocou** `extensor/content.js`, `casas/CASA_JOGODEOURO.md` nem `extensor/harness/casos/jogodeouro.mjs`. Então: o toast (`content.js:867`) manda abrir a tela cheia, o comentário do ramo (`content.js:811-815`) afirma que só o expandido é casado, e a tabela do `CASA_JOGODEOURO §2.1.1` diz que o compacto **não** é capturado. Os três são pré-s258. **O `vb_inject.js` está certo; a documentação e a dica é que ficaram para trás.** Pior: `respostas: 0` hoje **mistura três causas** e o toast escolhe uma delas às cegas — (a) aba aberta antes da 0.6.43, sem POST novo (o SPA já tinha os dados em memória); (b) molde aprendido e **replay falhou** (Bearer expirado → 401); (c) endpoint mudou. **Medição que separa as três, e que só o Feca pode fazer:** versão em `chrome://extensions` + console filtrado por `[SharpenUp`, onde `hook instalado em`, `requisição capturada p/ replay` e `erro no replay` decidem. **Conserto proposto, aguardando aprovação:** (1) trocar o `extra` da Jogo de Ouro pelo texto da Betpix365 (recarregar / refazer login); (2) mandar no heartbeat se o **molde foi aprendido** (`reqCtx != null`) e o **último erro do replay**, para o toast apontar a causa em vez de chutar; (3) corrigir a tabela do `§2.1.1`; (4) travar o caminho novo no `casos/jogodeouro.mjs`, servindo **só** o compacto e exigindo lote cheio (hoje só o `betpix365.mjs` cobre isso, e o caso da Jogo de Ouro ainda entrega o expandido em `urlsExtra`). **✅ A metade documental do diagnóstico foi RECONFIRMADA na varredura da s261**, contra o código: `vb_inject.js:47` tem mesmo o `RX_APRENDE = /widget(?:Expanded)?BetHistory/i` (e `:133` aprende por ele), enquanto o toast (`content.js:869`) segue mandando *"abra o histórico COMPLETO"* e a tabela do `CASA_JOGODEOURO §2.1.1:59` segue marcando o compacto como **"Não"** capturado. Os dois estão errados desde a 0.6.43. **A causa raiz do lote vazio continua NÃO-MEDIDA** — isso não muda sem o console do Feca. **Não aplicado de propósito:** mexe em `vb_inject.js` e `content.js`, compartilhados pelas 4 casas Altenar, e o harness está verde (14 casos, 237 bilhetes) — mudança própria, com gates, depois da medição. Ao capturar de novo, conferir contagem/datas/odds/código contra o card; a odd é sempre a **pós-boost** (10 de 10 turbinados). Sem amostra: **aposta em aberto** (a conta tinha zero) · cashout executado · V/HW/HL · bônus · múltipla de jogos diferentes · qualquer esporte além de futebol · os 7 `status` fora de {0,1,2}. O **§9 (mapa de mercados) é herdado da era print e NÃO foi revisado** contra o payload: a amostra da API trouxe rótulos que ele não lista (`1º tempo - 1x2`, `1º tempo - total de escanteios`, `Chance dupla`); revisar quando houver lote real.

- **Esportiva (s254):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados, mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.6.39**), **Ctrl+Shift+R** em `esportiva.bet.br` (recarregar a extensão *não* re-injeta em aba já aberta), Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **As duas leituras críticas:** a **DATA** (tem de sair a do **evento** — 1 dos 13 diverge de dia) e a **odd**, que aqui é sempre a **pós-boost** (13 de 13 turbinados; a tela trunca a riscada). Sem amostra: **cashout executado** · múltipla de jogos diferentes · `void`/anulado · `half-won`/`half-lost` · bônus aplicado a bilhete · os 7 valores de `status` fora de {0,1,2} · qualquer esporte além de **futebol**. O `§9` tem 8 mercados confirmados, de **1 dia** de amostra — a lista vai crescer. **A conta tem mais histórico do que a fixture:** a página 2 já veio com `isLastPage:false`, então o lote real será bem maior que 13.

- **Superbet e BETesporte seguem SEM caso no harness** (anotado na s250, ao mexer no `content.js`). ✅ **VIVA (s263, encolhida)** — `extensor/harness/casos/` tem **15** arquivos e nenhuma das duas está lá; **a Pinnacle saiu da lista na s263** (`casos/pinnacle.mjs`, 14 bilhetes). As mudanças da s250 são aditivas (um `||` no ramo do `iniciarRobo` e uma entrada no mapa de autodiagnóstico) e não alcançam essas três — mas elas continuam dependendo de **teste ao vivo** a cada mexida no `content.js`.

- **`LavaPessoal`: 42 bilhetes em `Faz1bet` esperando a unificação da s199** (achado de passagem na s249, ao rodar o relatório do `unificar_casas.py`). A base dele foi importada na **s222**, depois da unificação, e trouxe de volta a grafia que a s199 tinha aposentado — `Faz1bet` → `Faz1Bet`. **Não aplicado de propósito:** é base de outro dono e mexe em `casa` de bilhete, então **recalcula 42 assinaturas** (a decisão da s234 vale: não tocar sem o dono pedir). Quando for: `python scripts/unificar_casas.py --somente Faz1bet` para o relatório, depois `--aplicar`. **A lição maior é do `MAPA`, não do LavaPessoal:** ele é cumulativo e **todo import futuro pode ressuscitar qualquer grafia já aposentada** — rodar o relatório sem filtro de tempos em tempos é o que revela isso.

- **Blindar o round-trip de casa no `/salvar` (proposto na s249, NÃO feito). ✅ VIVA (s261).** Quando a conta é resolvida por `parceiro_id`, `conta["casa"]` **já é** a grafia canônica daquela conta (`main.py:2472`) — e `:2478-2481` passa ela por `_casa_display(_display_to_key(...))` assim mesmo, o que só pode corromper; foi exatamente o que aconteceu com a Jonbet. (A linha `:2354` que esta pendência citava é de outro trecho hoje.) Gravar a casa **verbatim** nesse ramo fecha a classe inteira do defeito para toda casa que venha a ser registrada no `_CASA_DISPLAY` **depois** de já existirem contas. Mexe em caminho compartilhado por todas as casas → mudança própria, com harness e `pytest` antes. Hoje o mecanismo está de pé por sorte: **1 grafia quebrada em 57**, e só porque ninguém mais cadastrou conta antes do mapa.

**BetNacional — divergência de rótulo de data, NÃO medida (anotada de passagem na s248):** o
`formatTicketBNC` (`extensor/content.js:2439-2440`, com `t.colocada` — a linha `:2164` que
esta pendência citava mudou de lugar) emite só `Data (colocação):`, enquanto
`CASA_BETNACIONAL §4` diz que a coluna Data é a **do evento** — e que o campo do Histórico já é
"evento / liquidação". Pode ser só nome infeliz da variável (`t.colocada`), ou pode ser o mesmo
defeito que a VaideBet levou a produção na s210 e que a Jonbet quase repetiu (lá as duas datas
divergem em 7 de 10 bilhetes). **Custo de medir: baixo** — comparar `t.colocada` com
`pernas[].inicio` (o bloco já emite como `Início:`) num lote real da casa. Não mexer antes de
medir: se o campo já for o do evento, "corrigir" quebraria o que funciona.

Quando chegar um bilhete novo: abrir o arquivo da casa correspondente, preencher a pendência, rodar o checklist do `CLAUDE.md` se envolver categoria nova.

---

## 3. Decisão do Feca pendente

> Medido, com o número na mão, e parado esperando qual dos caminhos seguir. Nenhum destes é
> dúvida técnica.

**Badminton (s245) — medido, não aplicado (aguarda decisão do Feca):**
- ~~2 bilhetes em `Outro`~~ **CORRIGIDO na própria sessão** (ids 125105/125106 → `Badminton`) via `scripts/corrigir_esporte_bilhete.py` (novo), que **reusa `atualizar_bilhete`** em vez de rodar UPDATE cru — assim a trilha em `correcoes` é gravada (2 linhas, `esporte: Outro → Badminton`) e a assinatura é reavaliada (não muda: `esporte` ∉ `_SIG_COLS`). Base do Feca: **19 → 21** bilhetes de badminton, P/L do tipster **Bad Milton** 169,67 → **547,17** (+377,50 = os dois W que estavam fora do esporte). Varredura por nome de atleta + faixa de mercado não achou **nenhum outro** badminton escondido em `Tênis`/`Outro` na base do Feca; os 18 "candidatos" que o filtro pegou são todos legítimos de **times** (eBasket, Rugby, Basquete) — a fronteira que a regra nova já declara.
- **Superbet não emite esporte/liga no texto do bilhete. ✅ VIVA (s261).** `formatTicket` (`extensor/content.js:1034` — a linha `:911` que esta pendência citava é de outra função hoje) manda data, stake, odd, status e seleções, e **nenhum `Esporte (casa)`**; o grep dessa string no `content.js` só acha `:1292`, `:1457` e `:3148`, todos de outras casas. Fecharia o buraco de **todos** os esportes dessa casa, não só badminton — mas exige ler os nomes dos campos no JSON de `/user/{id}/tickets` (F12 → Network). Não há fixture de Superbet no harness.
- **Categoria (não esporte):** 5 bilhetes Betano de 10–11/06 com `Over 78.5 Pontos [dupla v dupla]` estão em `Player Props` — é total da **partida**, então `Pontos` (`MASTER_APOSTAS §6`); e 9 bilhetes em `Games` onde o mesmo §6 manda `Sets`.

**Achados de performance da s217 — medidos, não corrigidos (decisão do Feca, um por vez):**
- **`sims=10000` fixo mesmo com a base cheia. ✅ VIVA (s261)** — as 3 chamadas seguem lá: `charts/overview.js:320`, `charts/gestao.js:488`, `charts/performance.js:1081`. As chamadas passam `10000` explícito, o que **atropela** a escala adaptativa que o `_calcPValueMCraw` tem por dentro (`n>10000 → 3000`). Com 30.851 linhas são ~308 milhões de iterações por cálculo, duas vezes. Fora da thread principal a tela não trava mais, mas o valor ainda leva **~1 minuto** para chegar (conferido no demo com 24.000: os cards ficaram girando bem depois do render). Cair para ~2.000 sims em base grande resolveria — **muda número exibido** (p95/p99 e p-value), então exige antes/depois medido na mesa e aval do Feca.
- **`/uso/tokens` responde 500** em produção (visto ao cronometrar as rotas do feed). **NÃO-MEDIDA, mas a s261 achou uma causa candidata na leitura do código:** `uso_resumo` (`repository.py:2571` e `:2573`) monta `NOW() - $1::interval` e passa a **string** `"30 days"`. Com o cast explícito o Postgres resolve `$1` como tipo `interval`, e aí o asyncpg exige um `timedelta` — string levanta `DataError`. Isso explicaria um 500 **constante**, não intermitente. **O contraste está no mesmo arquivo:** a purga da lixeira (`:2367`, escrita depois) usa `NOW() - ($1 || ' days')::interval`, e a concatenação mantém `$1` como texto — é a forma segura, e a rota de tokens ficou na antiga. **Nenhum teste cobre `uso_resumo`**, o que é o motivo de ninguém ter percebido. **Provar antes de mexer:** basta um `SELECT NOW() - $1::interval` com `"30 days"` contra qualquer Postgres — se levantar `DataError`, é isto; se passar, a causa é outra e o palpite morre aqui.
- **A casca `/app` carrega 3 iframes e os 3 puxam `/dashboard/data`. ✅ VIVA (s261)** — as 3 chamadas conferidas: `inicio.html:483`, `index.html:3504` e `dash/assets/js/data.js:4`. `/inicio`, `/` (Extração) e `/dashboard/`, cada um montando o feed inteiro no servidor (3 × 11,6 MB por abertura). Um cache compartilhado entre os frames (ou o feed servido uma vez pela casca) cortaria 2/3 do trabalho.
- **Deep-link a frio monta a tela vazia. ✅ VIVA (s261).** Abrir `/app#dash/metrics` sem cache local: a casca chama `showPage('metrics')` antes de o `buildHTML` existir, `_lastPage`/`_lastPageSig` já ficam marcados (`app.js:459`), e o **caminho frio** do `loadData` (`app.js:1233-1250`) chama `buildHTML()` + `applyAparencia()` e **nunca** `renderPage` — o `showPage` seguinte volta cedo pelo `if(id===_lastPage&&sig===_lastPageSig)return` (`:458`). A tela fica com os `—` do markup. **O caminho quente já faz certo** (`:1225`, `if(_lastPage)renderPage(_lastPage)`), o que dá o formato do conserto: espelhar essa linha no ramo frio. **Pré-existente**, não veio da s217.

### 3.1 Solidez — o redesenho do KPI. `TURBO 19/07 #15/#16`. **Já tentado e revertido.**

O gate de rentabilidade e a separação "força do sinal × tamanho de amostra" foram
implementados (`1923052`) e **revertidos no mesmo dia** (`9394553`): o rumo estava errado —
o gate rebaixava a "Baixa" um tipster sólido (11 de 12 meses positivos) por um drawdown
normal, justo o que o KPI existe para não fazer. Precisa de **sessão dedicada de
redesenho**, não de um ajuste de peso. O propósito do KPI (mede ROBUSTEZ, não lucro) é a
premissa que o redesenho tem de respeitar.

### 3.2 Bet365 modo texto — **pausado por decisão do Feca**

O card fechado não expõe o detalhe. Segue pausado; não reabrir sem pedido.

### 3.3 O botão "Atualizar dados" mente na página pública `/tipsters/<slug>` (s276). VIVA.

O item está na §2 (é da varredura da s261). A decisão é de produto: esconder o botão no modo público
(com rótulo "atualiza a cada 5 min") ou deixar o refresh furar o cache com teto por slug.

### 3.4 O que o handoff `Contas e Parceiros Opção A` pede e ficou fora (s330). **Em parte superado pelo v2 (s331)** — o menu `⋯` saiu (os três botões voltaram para a linha) e `Sincronizando` deixou de existir no vocabulário.

As 5 fases estão aplicadas. Três pontos ficaram de fora **de propósito**, e nenhum é
dúvida técnica — os três são decisão de produto.

- **`Duplicar cadastro` e `Transferir de parceiro` no menu `⋯`.** O handoff lista os dois
  como itens do menu, mas **não existe nada por trás deles** no app: não há rota, não há
  função, não há tela. Item de menu que não faz nada é pior que item ausente, então o
  menu entrou com `Ver extrato da conta` e `Excluir conta…`, que são reais. Implementar
  qualquer um dos dois é feature nova, não hierarquia — e "Transferir de parceiro" mexe em
  `parceiro`, que entra na assinatura (`_assinatura`): exige recalcular o hash na mesma
  transação, senão o histórico duplica inteiro.
- **Tag `Sincronizando`.** Está no vocabulário fechado de `tagConciliacao` e **não é
  emitida por ninguém**: o app não publica "extração em curso" por conta. Fica no mapa
  para o dia em que houver a fonte ser uma linha, e não um rótulo novo inventado na linha.
- **`Contas por casa` e `Custos por fornecedor` saíram da página** (s330, rev. 2). O
  contador por casa já vive no cabeçalho de cada grupo da lista, e o custo por fornecedor
  tem casa própria no Dashboard (`Fornecedores & Parceiros` / `Custos de Contas`). Se
  algum dos dois voltar, a pergunta a responder antes é *o que ele diz que a lista já não
  diz* — foi por não responder isso que os dois viraram enfeite.

### 3.6 Duas medidas do handoff v2 que a escada do SHELL_SPEC não tem (s331). VIVA.

O handoff pede **título 19px** e **eyebrow 9px**. Nenhuma das duas existe na escada do
`SHELL_SPEC` (9 · 10 · 11 · 13 · 14 · 15 · 18 · 22), e o `check-tokens` barra px literal
nesses selectors de propósito — foi assim que o título virou 30px na s80d.

- **Título:** ficou em `--text-xl` (22px). O degrau abaixo é `--text-lg` (18px). Mexer
  aqui muda o topo de **todas** as telas, o Dashboard incluído, porque o `SHELL_SPEC`
  amarra `.pagehead-title` a `.page-title`. A parte do handoff que carregava o argumento
  (sair do azul) já foi feita na s330.
- **Eyebrow:** ficou em `--text-xxs` (10px). 9px em `--ink-soft` fica **abaixo** do piso
  de 9,5px que a Escada de Tinta — a regra-mãe que o próprio handoff cita — exige do
  papel *Label*.

Decisão de produto: descer o título para 18px em todo o app, ou manter 22. Não é dúvida
técnica.

### 3.5 O log de extrações repete `100%` em quase toda linha (s330). VIVA.

**Isto é a queixa do handoff que continua de pé**, e a tentativa de resolvê-la na s330
foi desfeita por resolver a coisa errada: o painel virou `Pendências`, e ele não é uma
fila de tarefa — é o **histórico de extrações**, o RAIO-X. Rótulo errado é pior que
rótulo repetido, então o rename saiu inteiro.

O problema real permanece: num log de 40 linhas, ~37 imprimem `100%` de confiança.
Número que quase nunca varia deixa de ser informação e vira textura, e a linha que
importa (a que traz `82%` e `pendência`) não se destaca de nada.

**O que NÃO fazer:** trocar o nome do painel; filtrar o log por padrão (esconde
histórico, que é o produto daquela tela). **Caminhos plausíveis, nenhum medido:**
imprimir a confiança só quando ela **não** é 100%, deixando a coluna vazia no caso
rotineiro; ou manter as 40 linhas e dar peso visual só às que têm pendência. Decisão de
produto — a coluna é do RAIO-X, que também vive na tela de Extração.

### 3.7 O tradutor determinístico virou pré-condição de DUAS casas, não de uma (s332). VIVA.

Medição de 08/09 ([`ESTUDO_PRECIFICACAO §7`](docs/ESTUDO_PRECIFICACAO_2026.md#7-revisão-de-08092026-s332--o-que-aconteceu-depois-de-a-e-c)):
as correções A e C fecharam o vazamento **fixo** (aquecedor de US$ 173 para US$ 12,5/mês)
mas o custo **variável** por bilhete subiu 12 % (R$ 0,078 para R$ 0,087). Com isso a
escada do §4 do estudo não fecha só com a Bet365 determinística: Pro e Operação ficariam
em 12 % de margem bruta.

- **Bet365 + Betano = 64,3 % da conta e 58 % dos bilhetes por IA.** Com as duas, a escada
  fecha em 41–64 %.
- **A Fase 0 já tem massa:** `sombra_rotulos` acumulou 13.965 pares em 21 casas em 13 dias
  (Bet365 8.691, Betano 2.065). Não falta amostra.
- **Decisão do Feca:** abrir a Fase 1 do [`PLANO_TRADUTOR_DETERMINISTICO`](docs/PLANO_TRADUTOR_DETERMINISTICO.md) pelas duas
  casas, ou só pela Bet365 e remedir depois.

> **Cuidado que a própria s332 ensina:** o `_BILHETES_POR_CHUNK = 6` da s301 acertou o que
> mirava (output e latência) e piorou o custo variável, porque cada pedaço relê o manual
> inteiro (`cache_read` por chamada de 156k para 231k). Toda otimização daqui em diante
> precisa declarar **qual** custo ela mira e medir o outro depois.

---

## 4. Dívida técnica medida

> Achado, com arquivo e linha, e não corrigido. Aqui a referência é pista, não endereço.

*(bloco herdado do `STATUS §5`, verbatim — a varredura de 10/08, s261.)*

**Próximo passo (backlog vivo, um por vez):**
- **Backfill eSoccer — Feca FEITO (s234); resta o residual dos outros donos, se eles quiserem.** A auditoria da s234 varreu a Bet365 inteira e viu, fora do Feca: **Gabriel** ~14 bilhetes eSoccer como `Futebol` (tipsters próprios `Esoccer`/`LBB`) + **1 linha com grafia `Esoccer` na coluna esporte** (única da base; padroniza para `eSoccer` se mexer); Jonathan/William/LavaPessoal só têm eBasket-like (fora do escopo eSoccer). Método pronto e testado: script da s234 (`Backups/esoccer-backfill-feca-2026-08-02/`) — UPDATE por id auditado + perfil do tipster ganhando `eSoccer` nos `esportes` (senão o filtro duro do matcher mata as sugestões em silêncio, lição s221). `esporte`/`tipster` fora de `_SIG_COLS` → dedup intacta. Decisão do Feca (s234): **não tocar na base de outros donos sem eles pedirem**.
- **Matcher: "feudo empírico" — medido na s221, NÃO implementado.** O `Sugerir tipsters` é 100 % **declarativo**: lê só os perfis (casas · esportes · mercados · dica de stake) e **nunca** o histórico. Por isso as stakes **quebradas** (109,38 · 112,18 · 184,21…) ficam eternamente vazias — nenhum perfil declara quebrada na Bet365, e por stake elas são de todo mundo (M&M 284 · SóChutes 121 · SóTudo 31 · LBB 30). **O sinal que falta está na própria base:** no trio **casa · esporte · categoria**, um tipster domina. Medido na janela de 2.207 bilhetes que a tela **já carrega** (dá para computar no front, sem endpoint novo): `Bet365·Futebol·Gols → LBB 98 %` (226) · `Bet365·Futebol·Escanteios → SóTudo 82 %` (257) · `Bet365·eBasket·Pontos → Ctrl Alt Green 100 %` (219) · `Bet365·Tênis·ML → Robotenis 99 %` (168) · `Superbet·Múltiplos·Múltipla → Arrudex 92 %` (169) · `BETesporte·Futebol·Múltipla → Peixe 100 %`. Regra proposta: tipster **ativo** com ≥ 90 % e ≥ 15 bilhetes no trio leva; senão cai no matcher declarativo de hoje. **Cuidado que o próprio caso do 199 ensina:** o dono de um trio **muda com o tempo** (SóTudo → LBB entre maio e julho), então a janela precisa ser **recente**, não a base inteira — na base inteira `Bet365·Futebol·Gols` cai para 52 % de LBB e o critério não dispara. Fazer só depois de backtest com **holdout temporal** (treina no passado, mede no futuro), nunca in-sample.
- **Excluir conta: o caminho nunca rodou contra Postgres de verdade** (s219). ✅ **VIVA (s261)** — `tests/test_repository_db.py` tem 17 testes DB-real e **nenhum** toca `excluir_parceiro`. Os 7 casos de `test_excluir_parceiro.py` usam conn simulado, como o resto da suíte. Três coisas ficaram sem prova real: o `DELETE ... RETURNING to_jsonb(b.*)`, o cast `::jsonb` do snapshot no INSERT da lixeira, e o corpo do `DELETE` via HTTP. **Teste barato, fazer antes de excluir qualquer conta com histórico:** criar conta descartável, capturar 1 ou 2 bilhetes, excluir pelo modal, e rodar `python scripts/restaurar_conta_lixeira.py` para ver se a linha aparece com a contagem certa. Depois `--aplicar` num id e conferir se as apostas voltam. A forma travada seria um caso em `tests/test_repository_db.py` (roda no CI com `TEST_DATABASE_URL`, nunca em prod).
- **Betfast: rodar a captura pela EXTENSÃO** (s211). A API já foi validada ao vivo (varredura do teto: 32 de 32, ver acima), mas o robô em si nunca rodou: recarregar a extensão, **Ctrl+Shift+R** na aba, capturar e conferir contagem/datas/odds/código no dashboard. **O gatilho do teto continua sem exercício ao vivo** — a conta que loga no navegador tem 32 bilhetes e não chega nas 50; para ver o toast *"a captura foi além do teto"* seria preciso rodar na conta `fecanario`.
- ~~**Pinnacle sem fixture no harness** (s201)~~ **FEITO na s263** — `fixtures/pinnacle.settled.json` (6 bilhetes reais, inclusive uma múltipla de 2 pernas e a anulada) + `fixtures/pinnacle.open.json` + `casos/pinnacle.mjs` travam a ordem do replay, o freio por lista, o de-para posicional e o `CANCELLED → V`. **O que a fixture ainda NÃO cobre está escrito no cabeçalho do caso:** as duas ABERTAS são **derivadas** de linhas reais (a conta usada não tinha nenhuma em aberto no dia — a própria Pinnacle respondeu lista vazia nas três variantes de corpo testadas), `PUSHED`/`VOID`/`REFUND` seguem sem amostra, HW/HL também, e o campo 45 (categoria) é null nas 8 linhas. **A divergência "exibida × Retorno ÷ Stake" continua sem medição:** o payload traz P/L, não retorno, e o caso confere a odd exibida contra o JSON — não resolve a pergunta do §11.
- ~~**bet365 sem caso no harness** (s202)~~ **FEITO na s244** — `casos/bet365.mjs` trava a guarda `b3Emissivel`, o merge summary+confirmation, o corte do bloco KYC, a odd fracionária e o buraco da data. Harness passou de 7 para 8 casos (154 bilhetes).
- **Bet365 — data em bet builder de MESMO JOGO: DECISÃO DO FECA, medido e não corrigido** (s244). O `confirmation` desse tipo de bilhete vem com `TP=00010101000000` (sem kickoff) → `_dataFimB3` devolve vazio → o bloco sai **sem linha de data mesmo com o detalhe OK** → o backend cai na data de referência (= hoje). Provado por execução contra a fixture real, não deduzido. **O dado existe e está sem uso:** `da` (do confirmation, `DA=20260722233620`) e `tp` (do summary), ambos data de **colocação**. Usá-los contraria `CASA_BET365 §4`, que decide *"colocação nunca"* (cadeia `evento → informada → Brasília-hoje`) — logo é **mudança de regra**, não conserto de bug, e precisa da sua aprovação + atualização do §4 na mesma sessão. **CONFIRMADO na base, no fim da própria s244** (a 1ª medição tinha dado inconclusiva: 41,5% dos multi-seleção contra 24,1% dos simples, com captura diária confundindo o sinal — aquele número foi **descartado**, não use). O marcador `' // '` era grosseiro: mistura múltipla **entre jogos**, que tem kickoff, com bet builder de **mesmo jogo**, que não tem. Marcador exato: **2+ trechos e todos os confrontos `[A v B]` IGUAIS**. Com **controle dentro do mesmo lote** de captura (elimina o confundidor), `data == dia da captura`: **mesmo jogo 14/27 = 51,9%** · entre jogos 16/71 = 22,5% · simples 58/420 = 13,8%. O caso sem explicação inocente: no lote de 04/08 18:53:31, **0 de 20** simples eram do dia da captura e **2 de 2** bet builders de mesmo jogo eram. **Escala: pequena** — 34 bilhetes dessa classe na Bet365 do Feca desde 01/07, ~18 com data suspeita; hoje foram **6** (Internacional×Corinthians, Palmeiras×Fortaleza, Athletico-PR×Vitória, Juventude×Atlético-MG, Sonego×Griekspoor, Yu Chen Han×A Yeon Yoo). Dos 218 bilhetes Bet365 que entraram hoje, 84 têm data de hoje e **só esses 6** são da classe defeituosa; os outros 78 derivam do kickoff real. **O Feca viu o sintoma e o reportou** ("apostas de dias anteriores aparecendo como de hoje"), foi medido, ele leu o resultado e **decidiu não corrigir agora**. **Enquadramento para a decisão, quando ela vier:** a regra atual não escolhe entre colocação e data do evento — escolhe entre **colocação** (data do bilhete, erra por horas) e **o dia em que a captura rodou** (data da máquina, erra por semanas no modo Período). Proposta: cadeia `kickoff das pernas → colocação → data informada`, aplicando colocação **só** quando a API não dá kickoff, com o `CASA_BET365 §4` atualizado na mesma mudança. `casos/bet365.mjs` trava o estado atual **de propósito**: mexer nisso falha o gate e obriga a decisão consciente.
- ~~**Limpeza dos 139 da `marloncezar01`**~~ **APLICADA pelo Feca na s244** (o classificador barra escrita destrutiva em prod, então ele rodou via `!`). Verificado por fora, não pela saída do script: snapshot `removidos-Feca-20260804T194239Z.json` com **139 linhas de 22 colunas**, todas sem código e todas do parceiro certo, somando **exatos R$ 3.721,45** — o mesmo valor medido antes do DELETE. Base: **4447 → 4308** · sem-código **3586 → 3447** · `data = hoje` **168 → 29** (os 29 legítimos, que têm código) · lote do dia **206 → 67**, com código, data correta e confronto na descrição. Todos os deltas = 139.
- **Jonathan: 10 bilhetes Bet365 sem código em 04/08 — SUSPEITO, não confirmado** (s244). Mesma casa e mesmo dia do defeito do Feca, conta `edy-luc@hotmail.com [Gustavo]`, 10 de 10 sem código. **Não dá para separar robô de print pelo dado**: a coluna `origem` é `extracao` nos dois caminhos. Se for o mesmo defeito, o mesmo script limpa (trocando `--dono`/`--parceiro`); antes disso, perguntar ao Jonathan se ele capturou por print. **Não mexer na base de outro dono sem ele pedir** (mesma decisão da s234).
- ~~**`renomear_parceiro` não recalcula a assinatura** (s198)~~ **VENCIDA — feito em `50e68ee` (26/07)**, achado na varredura da s261. A função recalcula via `_assinatura_pos_edicao` com escalada de `_counter`, dentro da mesma transação (`repository.py:2439-2448`), e tem 4 testes em `tests/test_renomear_parceiro_assinatura.py`. O `CLAUDE.md` já a listava sob *"Quem já faz certo"* — **o §5 é que ficou para trás por duas semanas**, e eu quase gastei uma sessão "consertando" o que estava pronto.
- **41 apostas com odd truncada em reticências** (`2.50001664442...`): 22 Bet365, 6 Novibet, 6 Bolsa, 4 Betfair, 3 Esportiva Bet. A instrução proíbe reticências e uma odd assim não converte para número — mexe em P/L, não é cosmético. **NÃO-MEDIDA desde então (s261): a contagem é a do dia em que foi escrita e só o banco diz se ainda são 41** — `SELECT casa, count(*) FROM bilhetes WHERE odd LIKE '%...%' GROUP BY casa`.
- **165 bilhetes sem odd no sistema — MEDIDO na s262, não é defeito, não corrigir às cegas.** 149 são `origem='import'` (a planilha de origem trazia `0,00` na coluna Odd das perdidas; o import copia verbatim) e a esmagadora maioria é `L`, onde a odd não entra no P/L. Por dono: Feca 144 · LavaPessoal 8 · Lava 6 · ViniciusOliveira 4 · Jonathan 3. **A única classe que machuca é `W`/`HW`,** onde P/L vira não-calculável, e são **2**: `#18205` (Feca, KTO, 16/04, stake 331,57) e uma do LavaPessoal — as duas já em `extraction_state='aberta'` desde o backfill da s259. Backfill da odd das antigas **não é viável**: a Bet365 não mostra mais bilhete de abril/maio. Se for mexer, mexer só nas 2 de `W`.
- **`/uso/tokens` mostra um "custo por item" errado por ~10× (s295 §5.2, reconferido na s332 e ainda de pé).** `n_itens` é `len(base_content)` (`app/main.py:3069`), o número de **imagens/blocos de texto do lote**, não de bilhetes. A tela acusa US$ 0,14–0,22 por "item" enquanto o custo real por bilhete é US$ 0,017. **Quem olhar aquela tela para decidir preço decide errado.** Conserto: renomear a coluna para o que ela é (`blocos`), ou passar a contagem real de linhas do TSV para o `registrar_uso`. Enquanto não for feito, o número confiável sai do join `uso_tokens × bilhetes` por (dono, casa, dia), que é como o §7 do estudo mediu.
- **Dois "Banca total" na mesma tela do Painel de Contas, e eles divergem (achado medindo na s333, NÃO corrigido).** O KPI `Banca total` imprime `totais.banca` (soma de TODA conta com caixa ligada) e a faixa `BANCA TOTAL` dentro da Concentração imprime a soma das **casas com `banca > 0`**. Casa cujo total ficou zero ou negativo entra num e não no outro: na base de demonstração deu **R$ 98.264,58 contra R$ 101.245,83**, lado a lado. É a família de *"os dois números certos que pareciam defeito"* — os dois estão certos pela conta e a tela não diz que a régua é outra. Veio da s331c, quando a faixa entrou na Concentração para servir de denominador dos `% da banca`. **Conserto de uma linha, e a decisão é sua:** ou a faixa passa a imprimir `totais.banca` (e aí os `%` da lista deixam de somar 100), ou ela ganha o recorte no rótulo (`banca das casas com caixa`). Medir na base real antes: `select casa, sum(banca) ... having sum(banca) <= 0` diz quantas casas caem no vão.
- **Remedir o custo em 30 dias (a partir de 08/10/2026).** A janela do §7 tem 15 dias e é volátil: a semana de 31/08 custou US$ 128,22 (ritmo de US$ 550/mês) e a de 24/08 custou US$ 54,88 (ritmo de US$ 235/mês). Os scripts de medição da s332 não foram versionados (são read-only, rodaram do scratchpad); o método está descrito no §7 e se refaz em minutos.
- **Infra do Railway continua não medida** (estudo §5.3): app + Postgres + `sharpen-bot`. É custo fixo, dilui com escala, mas define o piso do tier de entrada. Medir antes de publicar preço.
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Solto (cosmético): favicon da KTO aponta para `kto.com`; o domínio real é `kto.bet.br`. ✅ VIVA (s261) — e são QUATRO arquivos, cinco ocorrências, não os "3 mapas" que esta linha dizia:** `extensor/popup.js:16` · `app/static/index.html:2432` · `app/static/dash/assets/js/data.js:52` **e** `:107` (o mesmo arquivo grafa duas vezes, uma na URL do serviço de favicon e outra no mapa de domínio) · `app/static/inicio.html:297`. É a mesma armadilha da memória *"Favicons: 3 mapas"* — o contador estava desatualizado, então **corrigir por `grep` de `kto.com`, nunca pela lista**.
- **Tela "Em Aberto" fora do material de venda** (s215): `scripts/demo/capturar.mjs` não captura a tela nova — o servidor de demonstração já a serve, falta só decidir se ela entra no showcase (e a numeração dos arquivos existentes muda). **Decisão do Feca: entra, mas só depois de a tela estar finalizada.**
- **Material de venda: 4 correções abertas nas capturas** (s214). O pipeline funciona (`scripts/demo/`: perfil → base fictícia → servidor → `capturar.mjs`) e as 8 telas saíram, mas quatro coisas travam o uso na landing. **(1) Contas irreais: o mock devolve 1.830 contas, o real são 102** — `servidor_demo.py:_parceiros()` deriva conta de cada par (parceiro, casa) visto no feed, então cada pessoa nasce com ~18 contas. **E a tela repete essas 1.830 embaixo de cada uma das 29 casas, somando 53.070** — essa segunda multiplicação foi medida, não diagnosticada; conferir se é forma do payload antes de mexer no front. **(2) `Diagnóstico de Risco` sai em "calculando…"**: é Monte Carlo de 10.000 simulações sobre 24 mil apostas e o screenshot dispara antes de terminar — esperar o cálculo, não o relógio. É o painel que sustenta o argumento estatístico da página. **(3) Custo de contas e de tipsters em R$ 0**, então o "P/L Líquido" fica idêntico ao bruto e a tela perde justamente o recurso que diferencia — popular `/custos/store` no mock. **(4) `Nível de Solidez: Baixa`**, com MDD 90,88% e Recovery Factor 0,94×. É coerente com odd média 7,7, mas é a nossa própria régua reprovando a operação da demonstração. Subir o edge de 4,5% para ~8% leva o ROI a ~4% e a folga para faixa saudável, sem sair do plausível.
- **Landing do usuário final: reescrita aprovada, não feita** (s214). O Feca pediu duas frentes: **tirar detalhe de arquitetura** e **entrar com print real**. Sai da página a seção "Integramos o motor" (Kambi/BetConstruct/Altenar), a aba "API do motor" do hero (`Koef`, `WinAmount`), os pesos e cortes da Solidez, "27 categorias fechadas", os "94,5% de acerto de categoria" e a faixa de números do hero. Fica o que é confiança e não mecanismo: não pedimos senha, a extensão não aposta nem move saldo, e o bloco "o que o Sharpen não é". **A ordem importa: print primeiro, texto depois** — hoje a página se defende explicando o mecanismo porque não mostra nada. Fonte em `docs/marketing/landing-usuario-final.html`.
- **Em Aberto: relato do Gabriel SEM confirmação** (s215, aberto): funciona para o Feca (57 abertas, R$ 13.325, conferido na sessão logada em `www.sharpen.bet`), mas o Gabriel disse que não. **Hipótese principal: casca velha ainda gravada no navegador dele** — o `no-cache` só vale a partir da próxima ida ao servidor, não desfaz cache já gravado; `Ctrl+Shift+R` uma vez resolve (F5 normal pode não recarregar o iframe do dashboard). **Antes de mexer na tela, distinguir pelo que ele vê:** cards com título e corpo vazio, sem nenhum KPI = ainda é cache; os 4 KPIs em `R$ 0` / "nada em aberto" = não é bug, a base dele não tem aposta aberta (conferir de quem é a base pelo filtro "Operador"). O jeito de medir é ler quais scripts o navegador dele carregou (`[...frame.contentDocument.scripts].map(s=>s.src)`) — versão antiga ou tag ausente = cache.
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

---

### 4.1 `AUDITORIA_2026` — os achados que continuam abertos

> Origem: [`docs/AUDITORIA_2026.md`](docs/arquivo/2026-07-10_AUDITORIA_2026.md) (vai para
> `docs/arquivo/2026-07-10_AUDITORIA_2026.md` no Lote D desta faxina). **O número original
> foi preservado** — `#32` aqui é o `#32` de lá, para o rastro não se perder.
>
> Aquele documento se declarava "único e vivo" e não era reconciliado desde **10/07 (s122)**.
> Cinco achados que ele mostrava como abertos **já estavam fechados** — a lista de "não
> reabrir" está logo abaixo.

| # | Achado | Estado medido em 06/09 |
|---|---|---|
| **#32** | Polymarket mistura `entry_odd` / `realized_odd` | **VIVA** — `_calc_odd` (`app/polymarket.py:894`) devolve um número só, e o comentário da `:987` admite "odd de entrada, **ou** a efetiva na liquidação". Maior risco quant aberto |
| **#44** | Observabilidade zero (sem `request_id`, sem log estruturado) | **VIVA** — zero ocorrências de `request_id` em `app/*.py`. Depurar produção é às cegas |
| **#16** | `SELECT *` em rotas | **VIVA e PIOROU** — eram 2, hoje são **6** em `app/repository.py` |
| **#10** | `scripts/import_lava.py` com caminho pessoal | **VIVA** — a `:23` ainda tem `CSV_PATH = r'C:\Users\Fernando\...'`. Script one-off |
| **#37** | `alert`/`confirm` em fluxo crítico | **VIVA** — 5 ocorrências de `confirm(` em `app/static/index.html` |
| #1 | Rotação da senha do Postgres | HUMANA — ver §1.1 |
| #8 | Dashboard abre sem login (os dados dão 401, a casca ainda monta) | NÃO-MEDIDA desde 07/07 |
| #11 | Backend monolítico (`main.py`) | Manutenibilidade, zero risco de runtime. Aceito por ora |
| #12 | Frontend monolítico (`index.html`) | Dívida do `PLANO_CASCA_UNIFICADA` |
| #13 / #25 | Dinheiro/odd/data como TEXT, cálculo em `float` | **Adiado por desenho** — `ADR-001`, com gate. Erro medido << 1 centavo |
| #14 | Schema inline no boot | `ADR-001` Fase 0 |
| #17 | Dashboard carrega a base inteira | `ADR-002` Fase 1 (gzip) feita; Fase 2 condicional |
| #18 | IA sem quota/fila global | Semáforo(4) por request; teto global ausente. Aceito para poucos operadores |
| #19 | Cache warmer por instância | Não endereçado |
| #20 | Paginação por offset | Não endereçado (baixo) |
| #28 | Odd média sem definição de void | Não documentado nem testado explicitamente |
| #34 | Handlers inline no HTML | É por isso que a CSP mantém `'unsafe-inline'` |
| #35 | Cores literais | `check-tokens` verde; drift residual segue |
| #38 | Mensagens de erro genéricas | Não endereçado |
| #39 | Acessibilidade | Não endereçado |
| #46 | Modelos Anthropic hardcoded | Decisão humana consciente (`config.py`) |
| #47 | RPCs públicos da Polymarket | Não endereçado |
| #48 | Mojibake / encoding | Não tratado sistematicamente |
| #49 | Multi-tenancy só lógica (sem RBAC/billing formal) | Isolamento por `dono` consistente. Over-engineering para hoje |
| #50 | Sem estratégia formal de beta/release (SLO, rollback) | O CI dá o guardrail |

> O **#24** ("modo ver como confunde") saiu da lista: o achado era **invertido** — o
> comportamento é proteção deliberada, da sessão 82.

#### NÃO REABRIR — fechados que o documento antigo mostrava como abertos

Verificados por `grep` em **06/09/2026**. Estão aqui para ninguém gastar sessão neles:

| # | Dizia | Está |
|---|---|---|
| #4 | rate limit confia em `X-Forwarded-For` spoofável | **fechado** — `app/main.py:1941-1946`, 1 hop confiável do Railway |
| #6 | `SESSION_SECRET` efêmero, só avisa | **fechado** — `app/auth.py:38-49`; em produção o app **não sobe** sem a env |
| #15 | falta índice em `criado_em`/`codigo_bilhete` | **fechado** — `idx_bilhetes_dono_criado` e `idx_bilhetes_dono_codigo` (`app/database.py:178-181`) |
| #22 | delete em massa sem limite | **fechado por outro caminho** — `lixeira_contas` (`app/database.py:362`) + confirmação reconferida no servidor |
| #36 | Google Fonts externo | **fechado** — zero `fonts.googleapis` em `app/static/`; `fonts.css` + 4 `.woff2` self-hosted |

---

### 4.2 `AUDITORIA TURBO 19/07` — os que sobraram vivos

> Origem: [`docs/AUDITORIA_TURBO_2026-07-19.md`](docs/arquivo/2026-07-19_AUDITORIA_TURBO.md) (vai
> para `docs/arquivo/` no Lote D). Dos 25 achados, **19 fecharam** — o tracker interno do
> próprio documento registra as ondas das sessões 158 e 160, e conferi os principais no
> código hoje (`custo_tipster JSONB` em `database.py:334`, índices, `.dockerignore`,
> `test_auth.py`, autodiagnóstico das casas-robô, HW=½ no backend, ` // ` como separador
> único). O `#14` (`domain.py`) foi **morto por decisão** na s160: premissa obsoleta.

| # | Achado | Estado medido em 06/09 |
|---|---|---|
| ~~#6~~ | ~~Tooltip do gráfico de Esportes vaza HTML cru~~ | **FECHADO (07/09)** — `charts/performance.js:156` usa `_txtPL(e[1].l)`, o formatador de texto puro que a recomendação pedia. Eu o tinha deixado como "a confirmar"; a reconciliação achou o `grep` certo. Ver [`docs/RECONCILIACAO_TURBO_20-07.md`](docs/RECONCILIACAO_TURBO_20-07.md) #85 |
| **#15/#16** | Solidez | **ABERTO** — ver §3.1 (revertido, precisa de redesenho) |
| **#18** | Backtest do matcher sem split temporal | **ABERTO** — a regra "assinatura tem ERA" já está no `CLAUDE.md`; o **holdout temporal** nunca foi construído. Roteado à frente de tipster |
| **#21** | `golden_set/bilhetes/` vazio | **VIVA** — ver §1.2 |
| #22 / #23 | Docs de consolidação defasados; itens resolvidos listados como abertos | **EM ANDAMENTO — é esta faxina.** Fecha ao fim do Lote E |
| #24 | Link quebrado no `HISTORICO` | **VIVA** — `docs/HISTORICO.md` linka `docs/HISTORICO.md` (resolve para `docs/docs/…`). Conserto de 1 linha, Lote D. Já pego pelo `tools/check_docs.py` |
| #25 | `Backups/` sem política de retenção | **VIVA e pior** — 551 pastas, 128 MB, **165 cópias** de `STATUS.md`/`HISTORICO.md` (21,2 MB). Lote A |

---

### 4.3 `AUDITORIA TURBO 20/07` — os 17 ALTOS, **remedidos hoje**

> Origem: [`docs/AUDITORIA_TURBO_2026-07-20.md`](docs/arquivo/2026-07-20_AUDITORIA_TURBO_PROFUNDA.md) (vai
> para `docs/arquivo/` no Lote D). 219 agentes, 104 achados brutos, **95 confirmados** após
> verificação adversarial (9 refutados) — e **nenhum tracker**.
>
> **Estes 17 não foram copiados: foram remedidos contra o código em 06/09/2026.** Copiar o
> estado declarado é exatamente o que produziu a `AUDITORIA_2026` mostrando 5 achados
> fechados como abertos.

**5 fecharam sozinhos desde 20/07** — não reabrir:

| # | Dizia | Está |
|---|---|---|
| C2 | XSS refletido em `/extensao?v=` | **fechado** — `app/static/extensao.html:143` documenta o escape |
| C3 | Offboarding via env não revoga sessão (token vive 30 dias) | **fechado** — `ler_token` (`app/auth.py`) ganhou gate de status a cada request (revoga em ≤60s) **e** gate de impressão de senha (s275) |
| D3 | Monte Carlo síncrono trava o browser | **fechado** — Web Worker em `charts/gestao.js:535` **e** `charts/performance.js:1080` |
| B4 | P/L Líquido mistura custo de tipster da vida inteira com contas filtradas | **fechado na s322** — `charts/overview.js:14-26` soma só os meses do período, e o comentário cita o achado Turbo por nome |
| D1 | Casca zero-responsiva (0 `@media`) | **parcial** — `app/static/app.html` tem 4 `@media` hoje; `dash/assets/css/layout.css` segue com **0**. Continua aberto para o Dashboard |

**12 seguem abertos:**

| # | Achado | Estado medido em 06/09 | Sev |
|---|---|---|---|
| **Compl. #1** | `apps_script/Code_LavaFatuch.gs` — `doGet` **público, sem autenticação** | **VIVA** — `doGet(e)` na linha 95, nenhum token ou segredo no arquivo. É a fronteira que alimenta o `app/planilha_viva.py`: a base financeira **ao vivo** do Fatuch. Qualquer um com a URL lê | **o mais urgente** |
| **A1** | `bcrypt` síncrono no `POST /login` congela o event loop (1 worker) | **VIVA** — `resultado_login` é chamado direto em `app/main.py:1962`, **fora** de `asyncio.to_thread`. O `/signup` e a troca de senha **já** usam `to_thread` (`:2149`, `:2584`), então o caminho da correção já existe no próprio arquivo | alto |
| **A2** | `/extensao/download` re-zipa a pasta inteira, síncrono, público, sem cache | **VIVA** — `extensao_download` (`app/main.py:1908`) sem cache por versão | alto |
| **A3** | `/dashboard/data` serializa a base + `gzip` síncrono no loop | **VIVA** — `app/main.py:3399-3403` comprime dentro do handler | alto |
| **A4** | Upload multipart parseado ANTES da auth | **PARCIAL** — há `413` por imagem (12 MB), por PDF (25 MB) e por total (60 MB) em `app/main.py:2837-2973`, mas **depois** do parse. Falta o limite de corpo no middleware ASGI | alto |
| **A5** | Sem teto de **bytes** agregado nas capturas | **VIVA** — `app/captura.py` só tem teto de **contagem** (`MAX_CAPTURAS = 60`, `MAX_SESSOES = 300`). Sessão abandonada retém ~960 MB; num container de 1 GB, 1 sessão = OOM | alto |
| **B1** | Chunker do modo cego fragmenta 1 bilhete via `split('\n\n')` | **VIVA, com atenuante** — `app/main.py:892` segue no `else`, mas ele já marca `por_bilhete = False`, então não promete fronteira que não tem. O risco de stake/odd corrompidos em casa NOVA continua | alto |
| **B2** | Import de XLS múltiplo: a UI mostra N cards, o backend processa só o primeiro | **VIVA** — `app/static/index.html:5324` manda `xlsFiles[0]`. Arrastar 3 planilhas evapora 2, sem card, alerta ou log. O onboarding depende disso | alto |
| **B3** | Dois goldens ensinam o separador `' + '` PROIBIDO | **A CONFIRMAR** — `casas/CASA_VITORIABET.md` e `casas/CASA_BETNACIONAL.md` têm ocorrências de ` + `, mas o `grep` não separa exemplo de prosa. **`casas/` está fora do escopo desta faxina** — medir e corrigir é sessão própria | alto |
| **C1** | XSS armazenado via nome de casa (modo cego), em 6 sinks | **A CONFIRMAR** — precisa rastrear os sinks um a um. O nome de casa entra **verbatim** por regra (`casa_canonica`), então o escape tem de estar na renderização | alto |
| **D2** | Pareamento + rate-limit em memória de processo | **VIVA** — `_SESSOES` é um `dict` de processo (`app/captura.py:201`). Subir para 2+ réplicas no Railway mata o handshake da captura e multiplica o orçamento de brute-force | alto |
| **D4** | Feed `SELECT *` sem `LIMIT` + P/L em Python por request | **VIVA** — `app/repository.py:1774`, `SELECT * FROM bilhetes WHERE dono = $1 ORDER BY criado_em` sem teto. É a raiz do A3 | alto |

### 4.4 O que sobrou da Auditoria Turbo — reconciliado em 07/09

> Feito: [`docs/RECONCILIACAO_TURBO_20-07.md`](docs/RECONCILIACAO_TURBO_20-07.md).

**Os 78 do mergulho de 20/07 não existem por escrito.** O documento enumera 16 itens
(`A1-A5`, `B1-B4`, `C1-C3`, `D1-D4`) e reporta "36 médios + 34 baixos + 8 info" **só como
contagem** no sumário. Não há `findings.json` do dia 20 — o único é o de 19/07. E o rodapé
do próprio documento diz por quê: **"Deliverables uncommitted."**

Em vez deles foi reconciliado o corpus que **existe**: os **139 achados enumerados** do
`findings.json` de 19/07, com arquivo, linha, evidência e recomendação — dos quais o
relatório daquele dia só promoveu 25 para a tabela de prioridades.

**Placar: 40 fechados · 68 abertos · 20 a confirmar na tela · 8 parciais · 3 que não eram
achado.** Cada um remedido contra o código de 07/09, nunca copiado.

**O que ficou como trabalho, em ordem de impacto:**

1. **`#129` — a coluna `Odd` guarda DUAS grandezas e nenhum MASTER as nomeia.**
   `MASTER_PIPELINE:114` diz `L ou V → ODDS TOTAIS do bilhete`; `MASTER_RESULTADO §5.1.1`
   manda *"preservar a odd estrutural original… não remover automaticamente seleções
   anuladas"*. Em múltipla com perna anulada os dois dão números diferentes.

   **Não é dinheiro — é consistência de coluna.** `calcular_pl` (`app/repository.py`) só lê
   a odd em `W` e `HW`; o comentário é explícito: *"Para L/V/HL a odd é irrelevante ao
   P/L"*. `L → 0.0`, `V → stake`. E a Caixa Inteligente prende **stake**, não retorno
   potencial, então odd de aberta também não toca caixa. O que sai errado é a **leitura**:
   em `W` a coluna guarda a odd **liquidada** (`Retorno ÷ Stake`, imposta pelo gate
   determinístico da s321), e em `L`/`V`/aberta ela pode guardar a **contratada**. Duas
   grandezas na mesma coluna, sem rótulo — e é isso que envenena odd média, odd média de
   sistema (`MASTER_RESULTADO §7.3`) e qualquer comparação de odd entre bilhetes.

   **O risco de dedup foi MEDIDO e deu ZERO** (07/09, só `SELECT`). A odd entra na
   `_assinatura` via `_norm_odd`, então duas leituras da mesma múltipla sem código
   gerariam assinaturas distintas e **duplicariam** — a mecânica do `14` × `14,00` da s327.
   Procurei: múltiplas sem código, agrupadas pela chave real da assinatura
   (`casa|parceiro|data|aposta|descricao|stake`), com odd divergente de valor.
   **192 grupos / 387 linhas, e os 192 são `origem='import'` — ZERO de `extracao`**,
   apesar de haver **528** múltiplas sem código vindas de extração na base. A superfície
   existe e nunca foi exercida. Com código: 19 grupos, **0** com o mesmo `codigo_bilhete`
   (são bilhetes distintos — o código está protegendo).

   Os 192 do import não são este defeito: o importador copia a odd da coluna da planilha
   verbatim, sem passar pelos MASTERs.

   **Portanto: dívida de DOCUMENTAÇÃO, não incidente.** Mexe em `global/`, que está fora
   do escopo da faxina. A decisão de regra pode esperar — e ela é sobre **nomear as duas
   grandezas**, não sobre escolher entre dois textos.

   > População em risco, para dimensionar quando a sessão acontecer: **23.398 múltiplas
   > `L`/`V` (20,19 % da base)** — Bet365 10.163 · Betano 4.950 · Superbet 3.719. A fatia
   > com perna anulada de fato **não é medível**: `bilhetes` não guarda perna, e só 3
   > linhas em toda a base trazem a palavra na descrição. O único percentual real é o da
   > `CASA_1XBET`: **9 em 66 perdidos (13,6 %)**.
   ### As casas NÃO discordam entre si — elas descrevem casas diferentes

   Eu tinha reportado que quatro arquivos de casa "legislaram sozinhos e discordam". **Está
   errado, e a correção muda o desenho da solução.** Relendo os quatro, cada um descreve o
   comportamento **daquela casa**, e os quatro comportamentos são genuinamente distintos:

   | Casa | O que a casa faz com a odd quando há perna anulada | Onde |
   |---|---|---|
   | **Pitaco** | **Recalcula** e publica a vigente; a original só aparece **quando mudou** — dois campos, um deles condicional | `CASA_PITACO §…` (`.1.3` odd vigente, `.1.4` odd original) |
   | **Novibet** · **Betfast/Tivo** | **Expõem as duas, sempre**, em campos separados | `placedPrice.value` × `finalPrice.value` · `Koef` × `WinKoef` |
   | **1xBet** | **Recalcula só em `W`**; em `L` o `Coef` fica **pré-anulação** (9 de 9 perdidos) | `CASA_1XBET §5` |
   | **Betano** | **Não expõe odd total** no texto resolvido — só as odds por seleção | `CASA_BETANO:192-196` |

   As "escolhas divergentes" que eu li como conflito são, na verdade, **cada arquivo
   traduzindo a sua casa** — que é exatamente o invariante #2 (*a casa traduz, não redefine*)
   funcionando. A `CASA_BETFAST` manda ficar com o `Koef` cheio em `L` porque é o único
   número que a casa dá ali; a `CASA_BET365` colapsa a perna para `1,00` porque a Bet365 não
   dá odd combinada resolvida. Não há discordância a arbitrar.

   **O conflito real é outro, e é global:** `PIPELINE` e `RESULTADO` falam de **UMA** odd, e
   existem **DUAS** grandezas — a **contratada** (no momento da aposta) e a **liquidada** (o
   que a casa de fato usou para pagar). Nenhum dos seis MASTERs nomeia essa distinção, então
   cada casa foi obrigada a inventar a sua no `§5`. A saída não é escolher entre
   `PIPELINE §3.1` e `RESULTADO §5.1.1` — é **nomear as duas grandezas no global** e dizer
   qual vai para a coluna `Odd` em cada resultado. Aí os quatro arquivos de casa deixam de
   ser exceções e viram o que deveriam ser: o mapa de qual campo da casa alimenta qual
   grandeza.

2. **`#114` — o `bf_inject` dispara até 400 requisições autenticadas** na Betfair
   (`bf_inject.js:176`), sem backoff. É o único inject que **cria** tráfego em vez de só ler.
3. **`#116` — `postMessage` sem validação de origem** no `content.js`, que roda em `*://*/*`.
4. Os outros 65 abertos e os 20 de tela estão listados um a um no documento.

**Ainda sem endereço: as 31 lacunas de completude** do mergulho de 20/07 — as superfícies
que ninguém nunca auditou. Seguem em prosa, sem id. As duas mais quentes (os 4 injects que
viram P/L e os `import_*.py` que fazem `DELETE FROM bilhetes` contra o `DATABASE_URL` de
produção sem dry-run) **não** foram cobertas: auditá-las é leitura de código novo, não
reconciliação. É a próxima sessão desta frente.

---

## 5. Planos com fase aberta

> Um plano só sai daqui quando **todas** as fases dele fecham. Plano com uma fase aberta é
> backlog, não história.

| Frente | Doc-fonte | O que falta | Horizonte |
|---|---|---|---|
| **SaaS multiusuário** | [`docs/PLANO_MULTIUSUARIO_2026.md`](docs/PLANO_MULTIUSUARIO_2026.md) | **Fase 4 (pagamento)**: gate `assinatura_ativa` + webhook. As Fases 1, 2 e 3 estão no ar (s233–s236) | 🟡 |
| **Tradutor determinístico** | [`docs/PLANO_TRADUTOR_DETERMINISTICO.md`](docs/PLANO_TRADUTOR_DETERMINISTICO.md) | Fases 1 a 4. A Fase 0 roda em **modo sombra** (13.965 pares, 21 casas, em 13 dias). A correção **B** segue **bloqueada** (`§IV.6`). **Remedição de 08/09** ([`ESTUDO_PRECIFICACAO §7`](docs/ESTUDO_PRECIFICACAO_2026.md#7-revisão-de-08092026-s332--o-que-aconteceu-depois-de-a-e-c)): a pré-condição do preço virou **Bet365 + Betano**, não a Bet365 sozinha | 🔴 |
| **Perfil de Tipster** | [`docs/PLANO_TIPSTER.md`](docs/PLANO_TIPSTER.md) | **P1** resultado em unidades (backend pronto; a UI trava no formato "u", passa pelo `/nova-ui`) · **P2** atribuição por watermark · **P3** Telegram como fonte. Fase 0 no ar (`origem_tipster`) | 🟢 / 🟡 / 🔵 |
| **Resolvedor de atribuição** | [`docs/PLANO_INTELIGENCIA_TIPSTER.md`](docs/PLANO_INTELIGENCIA_TIPSTER.md) | ⚠️ **doc defasado** — descreve o matcher **v5, de 15/07**; ele mudou muito desde então (corte de valor redondo e `valores.size===1` na s221, peso declarativo na s289, volta do declarado onde a base é cega na s310). A tese (o resolvedor) segue aberta; o texto precisa de banner de data | 🟡 |
| **Extração worldwide** | [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) | Fases 1 a 5 (confidence da IA + guardrail de enum). Fase 0 validada | 🟡 |
| **Casca unificada** | [`docs/PLANO_CASCA_UNIFICADA.md`](docs/PLANO_CASCA_UNIFICADA.md) | **Fatia 3**: topbar compartilhada, poda de CSS morto, aposentar links cross-app. Fatias 1 e 2 no ar. Fatia 4 (SPA único) só se o host com iframe não bastar | 🟢 |
| **Polymarket incremental** | [`docs/PLANO_POLY_INCREMENTAL.md`](docs/PLANO_POLY_INCREMENTAL.md) | A marca d'água não existe em `app/polymarket.py` (conferido hoje). É caminho de dinheiro: **precisa de teste de paridade na carteira do Feca** antes de subir | 🟡 |
| **Dashboard opção C** | [`docs/PLANO_DASHBOARD_C.md`](docs/PLANO_DASHBOARD_C.md) | Não iniciado. Condicional à medição pós-gzip (`ADR-002` Fase 2) | 🔵 |
| **Flag de inferência por campo** | [`docs/PLANO_INFERENCIA_POR_CAMPO.md`](docs/PLANO_INFERENCIA_POR_CAMPO.md) | Sem código. Precisa de OK do Feca + passo dedicado (mexe no pipeline de extração) | 🔵 |
| **Dinheiro → NUMERIC/Decimal** | [`docs/ADR-001-migracao-numeric-decimal.md`](docs/ADR-001-migracao-numeric-decimal.md) | Fase 0. **Adiado por desenho**, com gate | 🔵 |
| **Dashboard 1ª carga** | [`docs/ADR-002-dashboard-primeira-carga.md`](docs/ADR-002-dashboard-primeira-carga.md) | Fase 2 (agregação no servidor), condicional à medição | 🔵 |
| **Assinatura de tipsters** | `Ideias/Estudo_Assinatura_Tipsters_Sharpen.pdf` + `Ideias/Modelo_Financeiro_Rota_propag_Sharpen.pdf` | Estudo concluído (s122), execução **não iniciada**. Rota B (gateway regulado com split — **Asaas**); Stripe descartada (proíbe previsão esportiva no BR). Próximo: fundir os 2 PDFs num documento mestre e a conversa comercial com a Asaas. Depende da Fase 4 do SaaS | 🔵 |
| **Matriz de confiabilidade das casas** | [`docs/CASAS_CONFIABILIDADE.md`](docs/CASAS_CONFIABILIDADE.md) | Espelha **13 de 28** casas. Atualizar é sessão própria (lê `casas/`, fora do escopo da faxina) | 🟡 |

> **Vencido, registrado para não voltar:** o `Ideias/README` pedia "instalar a extensão nos
> perfis Octo **após aprovação** na Chrome Web Store". A loja **não aprova** extensão de
> apostas — a distribuição do SharpenUp é **sempre manual**, por link fixo em
> `sharpen.bet/extensao`. Não há aprovação a esperar.

---

## 6. Não medido / a reconciliar

> Aqui mora o que só o Postgres, a tela ou uma sessão dedicada respondem. **Nada nesta seção
> autoriza afirmação** — são perguntas, não fatos.

*(bloco herdado do `STATUS §5`, verbatim — a varredura de 10/08, s261.)*

### O que a varredura da s261 NÃO conseguiu classificar

**Cinco pendências são de DADO, não de código — nenhuma delas é verificável por leitura**, e todas trazem número datado que só o Postgres confirma:

| Pendência | Query que decide |
|---|---|
| 41 odds com reticências | `SELECT casa, count(*) FROM bilhetes WHERE odd LIKE '%...%' GROUP BY casa` |
| `LavaPessoal`: 42 em `Faz1bet` | `SELECT count(*) FROM bilhetes WHERE dono='LavaPessoal' AND casa='Faz1bet'` |
| `LavaPessoal`: 30 com stake 0 | `SELECT count(*) FROM bilhetes WHERE dono='LavaPessoal' AND stake IN ('','0','0,00')` |
| `LavaPessoal`: 2 contas vazias | `SELECT p.nome FROM parceiros p LEFT JOIN bilhetes b ON …` |
| Residual do backfill eSoccer | contagem por dono, fora do Feca |

O `DATABASE_URL` de produção está no `.env` local. **Medir é só SELECT e não muda nada** — mas é base de outros donos, então segue a decisão da s234: **ler pode, tocar só se o dono pedir.**

---

### 6.1 Itens que dependem de olhar a tela, não de `grep`

- **`TURBO 19/07 #6`** — tooltip de Esportes com HTML cru. Ver §4.2.
- **`TURBO 20/07 C1`** — os 6 sinks do nome de casa. Ver §4.3.
- **`TURBO 20/07 B3`** — os goldens com ` + `. Ver §4.3; mexe em `casas/`.

---

## Procedência — de onde veio cada parte

| Seção | Origem | Data da fonte |
|---|---|---|
| §1 (bloco herdado), §2, §3 (Badminton, perf. s217, BetNacional), §4 (abertura), §6 (bloco herdado) | `STATUS.md §5`, **verbatim** | varredura de **10/08/2026 (s261)**, com itens até a s328 |
| §1.1, §4.1 | `docs/AUDITORIA_2026.md` | reconciliado em 10/07/2026; **remedido em 06/09** |
| §1.2, §3.1, §4.2 | `docs/AUDITORIA_TURBO_2026-07-19.md` | tracker até a s160; **remedido em 06/09** |
| §4.3, §4.4, §6.1 | `docs/AUDITORIA_TURBO_2026-07-20.md` | 20/07/2026, sem tracker; **os 17 ALTOS remedidos em 06/09** |
| §5 | `docs/PLANO_*.md`, `docs/ADR-*.md`, `Ideias/README.md` | status lido de cada doc + conferência no código em 06/09 |

**Prova de que nada se perdeu:** as **192** linhas não-vazias do `STATUS §5` (linhas
1242–1463) foram conferidas uma a uma dentro deste arquivo — zero faltando, com contraprova
por canário.

**O que ainda NÃO entrou aqui:** os 78 achados MÉDIO/BAIXO e as 31 lacunas de completude do
TURBO 20/07. Eles estão representados por **um item vivo** (§4.4), não pelo conteúdo.

---

_Atualizado: 2026-09-06 (faxina de documentação, Lote F)._
