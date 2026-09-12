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

### 1.4 A validação ao vivo da adoção do código (s338). **VIVA — o reparo já foi APLICADO**

A regra, a barreira e o reparo estão no ar. **Feito em 09/09/2026:** a migração marcou as
**55** linhas de Blaze como `codigo_ocr`, e o reparo (autorizado pelo Feca) moveu **4**
linhas para `lixeira_bilhetes` — o grupo do Susanto na conta do Jonathan, que eram
**R$ 679,62 de lucro que nunca existiu**. Sobrou uma linha por bilhete e o ensaio agora
devolve `0 grupo(s) duplicado(s)`. germano (20 linhas com código torto) e Jaao26 (1) não
tinham duplicata: leram cada bilhete uma vez só.

**Falta a validação ao vivo, que só o operador faz:** rodar a captura da Blaze numa dessas
contas e conferir que a linha é **ADOTADA** (mesma linha física, código passa a ter 19
dígitos, `codigo_ocr` vira FALSE), em vez de nascer outra. É a única parte que o harness de
DB não alcança.

> A conferência é uma consulta: `select id, codigo_bilhete, codigo_ocr from bilhetes where
> dono='Jonathan' and casa='Blaze' and descricao ilike '%Susanto%'`. Continuar sendo
> `#212907` é o sinal de que a B' funcionou.

### 1.5 Casa nova na captura herda a dívida de código por print (s338). **VIVA, não medida**

O backfill de `codigo_ocr` cobriu **só a Blaze**, e por prova de DATA (a captura não existia
antes de 09/09 19:24). Toda outra casa que já era planilhada por print antes de ganhar
captura tem a mesma dívida, e ninguém a mediu: a pista barata é o **comprimento do código
variando entre linhas da MESMA casa**, que id de casa não faz.

Não dá para backfillar por palpite de formato: `_CASAS_MARCADOR_CODIGO` documenta o formato
de algumas casas em comentário, não em código, e errar aqui marca como suspeito um código
que está certo.

### 1.6 O `CLAUDE.md` ESTOUROU o teto (s338 previu, s339 aconteceu). **VIVA — gate vermelho**

Estava em 64,4 KB contra 65 KB do `tools/check_docs.py`, e a s338 escreveu aqui que "a
próxima regra que precisar entrar reprova o gate". Foi o que aconteceu: a regra da data por
kickoff (s339) levou o arquivo a **65,4 KB**. O gate acusa desde o commit `db5b77c`.

**O que já foi feito, para ninguém refazer:** movido o caso da Blaze (medição dos 55 códigos)
para o `docs/CASOS.md`, encolhido o parágrafo "Limitação" que repetia a 4ª linha da tabela de
dedup, e a própria regra nova comprimida ao núcleo. Rendeu ~0,8 KB e **não é suficiente**.

**Medido: não há mais duplicação para mover.** Zero frases longas (> 45 caracteres) repetidas
entre o `CLAUDE.md` e o `docs/CASOS.md`. O arquivo é regra pura, então fechar os 0,4 KB
significa **decidir qual regra sai**, e isso é curadoria do Feca, não faxina mecânica.

O candidato mais óbvio, se ele quiser um: a seção **`## Convenções de output`** (1,5 KB) se
declara "espelho operacional" do `global/MASTER_OUTPUT_2026.md`, que é a fonte canônica.
Virar um ponteiro de 3 linhas libera folga para esta regra e para as próximas. É a única
duplicação **declarada** que restou no arquivo.

> ⚠️ Não suba o teto. Foi assim que o `STATUS.md` chegou a 187 KB.

**Atualização s344: 66,3 KB.** A regra do corte de histórico por casa entrou (casa que
exporta o histórico inteiro não some só apagando o banco) e custou ~0,9 KB, já comprimida
ao núcleo, com o caso inteiro escrito no `docs/CASOS.md`. Procurei de novo o que mover e
**confirmo a medição da s339: não há caso solto no arquivo**, só regra. A dívida está em
~1,3 KB.

O candidato do parágrafo acima segue de pé e **depende de um "pode" do Feca**: virar
`## Convenções de output` num ponteiro de 3 linhas para o `MASTER_OUTPUT_2026.md`, que ela
mesma declara ser a fonte canônica.

### 1.8 Sobraram 21 linhas ARQUIVADAS datadas no futuro pela folga (s339). **VIVA, medida**

O reparo da s339 (`scripts/corrigir_data_folga_s339.py`) filtra `archived = FALSE`, e o
escopo aprovado pelo Feca foi só o `Ctrl Alt Green`. Contando as arquivadas, **21 linhas já
resolvidas continuam com data posterior a hoje** — todas Bet365, de outros tipsters
(Coxadoido 15+2, Fatuch 6, Perereca Tips NFL 6, Aumentadinhas 3+1, MarcoF1 2, DartsVader 1
e outras). Nenhuma é do Ctrl Alt Green: as 8 dele estavam todas não arquivadas.

**Só as resolvidas contam.** Havia 43 arquivadas com data no futuro, mas 22 delas estão
ABERTAS, e aposta aberta em evento de amanhã tem data futura por direito. Resolvida com
evento no futuro é que é impossível.

O script já resolve: falta decidir o escopo. Ele exige `--dono` + `--tipster` de propósito
(ou `--tudo` por escrito), e roda em ensaio por padrão. **Decisão do Feca.**

> Isto é o retrato de HOJE, não o histórico. O piso de 188 linhas medido na s339 é maior e
> não é reparável por aqui: sem o kickoff no banco, não há como provar o deslocamento de
> uma linha cuja data já ficou no passado.

### 1.7 O CI está VERMELHO por defeito do próprio gate, não do repo (s338). **VIVA**

`check_docs.py` acusa 5 links quebrados no CI e **nenhum deles é quebrado**: são links para
`../pack/…`, que existe na máquina do Feca (é a pasta irmã) e **nunca** existe no checkout,
porque o repo publicado é só o `Planilhador/`. Confirmado em commits de sessões diferentes:
a falha é a mesma antes e depois desta sessão.

O custo não é cosmético. **CI cronicamente vermelho não é gate**: ninguém distingue a falha
nova da de sempre, e foi por isso que a quebra real desta sessão (um kwarg colidindo num
teste) passou despercebida até alguém abrir o log à mão.

Conserto: o `check_docs.py` precisa tratar link que sai da raiz do repo como **fora de
escopo**, não como quebrado. Um link para fora não é conferível de dentro.

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
- **Betano:** §5 rótulo de void/anulada · §8 bônus/freebet · `BonusOffer` em aposta **aberta** e em **cashout** (sem amostra dos dois)
- **Betano — a dívida do turbo `Criar Aposta Turbinada`, três frentes (s349). ✅ RESOLVIDA para
  frente, aberta para trás.** Desde a **0.7.12** o bloco soma o `BonusOffer.Winnings` ao retorno
  e a odd de W sai certa. O que falta:
  **(1) `CASA_BETANO §6` ainda afirma que *"em W a regra `Ganhos ÷ Aposta` já resolve o boost
  sozinha quando o card traz os valores em R$"*.** Não resolve: o `Ganhos` do card é **pré-boost**
  e o turbo aparece em linha separada, que foi exatamente o que a §6 mediu em 31/08 e concluiu ao
  contrário. Corrigir o texto e documentar o campo da API (hoje a §6 só descreve o card).
  **(2) MEDIR a dívida.** O UPSERT congela `odd` em linha resolvida, então **recapturar não
  conserta bilhete turbinado já gravado** — e nenhuma coluna do banco registra o turbo, então a
  contagem só sai comparando bloco × banco depois de uma recaptura. Todo W turbinado da Betano,
  de todos os donos, está com odd e P/L subestimados desde sempre.
  **(3) Script de reparo**, no molde do `scripts/corrigir_resultado_odd_s321.py`: ensaio por
  padrão, piso de R$ 1,00 e respeito à tabela `correcoes` (correção humana manda sobre a captura).
  Origem: bilhete `21048480456` do Diogo, R$165 a menos de P/L, medido contra o saldo da conta.
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

- **Betfast / Tivo (s211):** cashout · bônus · aposta de sistema · outright · **aposta ABERTA** (as 50 da amostra são liquidadas) · `§9` de duas categorias (`Total de defesas do goleiro` · `Handicap de mapas`/`Map Advantage`)
- **Jonbet:** ~~captura NÃO validada ao vivo~~ **VALIDADA na s249** — a extensão capturou na 1ª tentativa e gravou **13 bilhetes** (3 W · 7 L · 3 abertas), com código, stake e odd conferidos no banco. **A coluna Data ficou provada ao vivo:** saiu 04/08 (3) · 05/08 (4) · 06/08 (3) · **07/08 (3)**, e as 3 abertas são justamente as de 07/08 — eventos futuros, que a data de **colocação** teria carimbado em 05 ou 06/08. **Falta só a conferência visual do Feca contra o card** (contagem e datas lado a lado). Segue sem amostra: **cashout executado** · múltipla · bet builder · sistema · `half-won`/`half-lost` · `void`/`refund`/`rejected` · **boost** (`boost:false` em tudo) · **imposto** (`payout_tax:"0"` e `taxes` ausente — quando aparecer, decidir de uma vez se o `W` usa retorno bruto ou líquido, ver `CASA_JONBET` Feedback #2). `§9` só tem os 3 mercados de badminton confirmados.

- **Blaze (s337):** ⚠️ **captura NÃO validada ao vivo** — o harness e a API foram exercitados (a varredura completa rodou contra o servidor real, 165 bilhetes), mas nenhum lote passou pela extensão. Fazer: recarregar a extensão (**0.7.9**), **Ctrl+Shift+R** em `blaze.bet.br`, abrir **Esportes → As Minhas Apostas**, Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **A leitura crítica é a ODD DO BILHETE `2518879929848968006`: tem de sair `1,92`, nunca `0`** — é o caso em que `k` e `total_k` vêm zerados juntos e o card deixa "Total de odds" vazio (`CASA_BLAZE §11.1`). Conferir junto que os dois `V` (`…964347` reembolsada e `…249307` cancelada) saem com odd **1**, e não com o produto das pernas. **Sem amostra** (a conta tem 165 bilhetes e nenhum destes): **aposta em aberto** · **cashout executado** (a aba voltou `count: 0`) · **boost** · **freebet** · **sistema** (`combinations` vazio em 165 de 165) · `half-won`/`half-lost` · imposto > 0. **Herda de graça o buraco das irmãs:** quando um cashout aparecer em qualquer uma das três casas BetBy, ele fecha o mesmo buraco nas outras duas. O `§9` tem 6 mercados confirmados e **mistura pt-BR com inglês** (`Vencedor` × `Winner`) porque o dicionário do tenant é parcial — a lista vai crescer.

- **Betboom (s250):** ⚠️ **captura NÃO validada ao vivo pela EXTENSÃO** — mas o **replay foi medido ao vivo na conta real na s340**, no navegador, e foi ali que apareceu o defeito do CORS (`credentials:"include"` recusado → replay zerado → só as 15 da 1ª tela). Com o fallback do `pedirPagina`, a varredura fechou `[21,21,21,5]` = **68 únicos, `count` 68**. Falta o lote passar pela extensão de ponta a ponta: recarregar a extensão (**0.7.10**), **Ctrl+Shift+R** em `betboom.bet.br`, **Esportes → o ícone de bilhetes na barra lateral** (`/sport/bets/`, é essa tela que dispara `my_bets/list`, não o "Histórico de apostas" do perfil), Conectar → "Copiar bilhetes", conferir contagem/datas/odds/código contra o card. **A contagem esperada é 68**, não 15. **A leitura crítica é a DATA** — nesta casa colocação e evento divergem em **7 de 7**, e a coluna Data tem de sair com a do **evento**. Sem amostra (a conta tem 7 bilhetes, todos simples, badminton): **cashout executado** · múltipla · bet builder · sistema · `half-won`/`half-lost` · `void`/`refund`/`rejected` · boost · imposto. As abas `Cashout efetuado`, `Canceladas` e `Reembolsadas` **existem na tela** mas vieram vazias — quando encherem, elas fecham buracos das **duas** casas BetBy de uma vez. `§9` só tem 2 mercados confirmados (`Vencedor`, `Handicap pontos`); `Total pontos` está na Jonbet e **não** foi importado para cá de propósito (camada fina).

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

### 3.8 A Extração PERDE a grade em janela menor que ~1450px (s346). **VIVA, medida**

**Sintoma:** com a área do iframe abaixo de 1180px o `.workfull` cai no modo empilhado
(`@media (max-width:1180px)`) e o `#partner-page` fica com **altura 0** — a lista de
apostas some da tela e o RAIO-X aparece **sobreposto** à área de captura. Medido headless
contra o `servidor_demo`: em janela de 1366 o `#partner-page` mede `1050x0` e a
`.grade-section` mede `1050x2`; em 1700 mede `996x240` e está correto.

**Não é da dieta de colunas.** Provado por remoção, do jeito que o `CLAUDE.md` manda:
o mesmo script contra o `index.html` do `HEAD` (antes da s346) devolve os **mesmos**
`1050x0` e `1050x2`. Injetar `container-type: normal` também não muda nada — a causa não
é o container query, é a linha do grid no modo empilhado.

**Por que ninguém relatou:** a casca come 264px de sidebar, então o empilhamento só
começa por volta de **1450px de janela**, e os testers que reportaram esta tela estão
acima disso (o relato deles foi scroll horizontal, não tela em branco). Quem abrir o
Sharpen num laptop de 1366 real cai nele.

**Onde olhar:** `.workfull` e `.colmain` (`app/static/index.html`, o bloco
`@media (max-width: 1180px)`) — a `.colmain` declara `grid-template-rows: auto minmax(0,1fr)`
e no modo empilhado vira `auto auto minmax(0,1fr)`, mas o `.workfull` passa a
`grid-template-rows: none`, e é aí que a linha do `#partner-page` perde a altura.

**Decisão do Feca:** consertar o modo empilhado (dar altura à linha da grade) ou deixar o
rail sempre lateral com a alça de recolher fazendo o papel. A segunda é mais barata e
combina com a alça da s346, mas muda o comportamento em tela pequena.

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

### 3.10 O prompt de sistema: três hipóteses testadas, três negativas (s336). FECHADA como medição, aberta como decisão.

O prompt de sistema é **45.904 tokens de masters mais 11.055 da Bet365**, relidos uma vez
por pedaço. Isso é **US$ 123/mês só de `cache_read` dos masters**, um terço da conta. Eu
apostei que boa parte fosse gordura. **Não é.** As três hipóteses baratas morreram:

| Hipótese | O que se mediu | Economia |
|---|---|---|
| Aparato editorial (rodapé de versão, ponteiro para caso, link) | **19 linhas em 8 arquivos** | **US$ 0,76/mês** |
| Cada casa carregar só os esportes que vê | a Bet365 usa **24 de 22 seções** | **US$ 7,30/mês** |
| Cortar os esportes de nicho | quebraria 4,4 % dos bilhetes | US$ 26/mês, inaceitável |

`build_system` manda o **arquivo cru, verbatim** (`app/prompts.py`), e mesmo assim quase
tudo ali é regra. **Os masters estão densos, não inchados.**

> **Fatiar por chamada está fora, e o motivo é o cache.** Todas as casas compartilham o
> mesmo prefixo de 45.904 tokens, e é isso que faz a releitura custar US$ 0,30/MTok em vez
> de US$ 3,00. Dar a cada casa um prefixo próprio multiplicaria as escritas de cache e o
> aquecedor só aquece um. **Mover conteúdo entre os dois breakpoints também não economiza
> nada:** os dois são lidos em toda chamada.

#### O que sobrou para decisão humana, e não é urgente

**A desproporção entre peso e volume**, que é achado de manutenção, não de custo:

| Esporte | % dos bilhetes | % do `MASTER_ESPORTES` |
|---|---|---|
| Futebol | **49,9 %** | 0,8 % (117 tokens) |
| Múltiplos | 23,3 % | 0,7 % |
| **Badminton** | 2,4 % | **25,2 %** (3.917 tok) |
| **Dardos** | 2,0 % | **29,5 %** (4.592 tok) |
| **Atletismo** | **0,01 %** (2 bilhetes na base inteira) | **7,3 %** (1.130 tok) |

Dardos, Badminton e Atletismo são **62 % do arquivo para 4,4 % dos bilhetes**.

**Isso provavelmente está certo**: o tamanho segue a AMBIGUIDADE, não o volume. Futebol
resolve em 117 tokens porque é óbvio; badminton inverte a ordem do nome e dardos tem
`legs`, `sets` e `180s`. Mas o **Atletismo com 1.130 tokens para 2 bilhetes em toda a
história** merece uma olhada de quem mantém o arquivo, e vale US$ 3/mês.

#### A única alavanca grande que sobrou, e ela tem preço

**Compilar os masters**: enviar ao modelo uma forma operacional compacta e manter o
documento completo para humanos. Levaria os 45.904 para talvez 20 mil, uns US$ 55/mês.

**Custo real disso:** cria uma SEGUNDA fonte de verdade, contra o invariante nº 1
(*"o app LÊ os masters, nunca escreve"*) e a regra de propagação. Toda categoria nova
passaria a ter dois lugares para atualizar, e o segundo é o que o modelo lê. É a família
do defeito que a camada fina existe para não repetir.

**Decisão do Feca**, e a minha recomendação é **não fazer agora**: o tradutor tira a IA do
caminho e torna o tamanho do prompt irrelevante para a parte que ele cobre. Comprimir o
manual para depois não precisar dele é trabalhar duas vezes.

### 3.9 O output que o parser descarta: medido, e menor do que a estimativa (s336). VIVA.

**A estimativa que eu dei ao Feca estava alta e está corrigida aqui.** A conta offline
(TSV real contado no `count_tokens`, que é gratuito) deu **70,8 % do output descartado**,
o equivalente a ~US$ 110/mês. O experimento controlado, com 4 chamadas reais sobre 6
bilhetes de Bet365, mostra que o número verdadeiro é **bem menor e muito ruidoso**.

O desperdício são **duas coisas de naturezas opostas**, e só uma é removível de graça:

| | O que é | Tamanho medido | Dá para cortar? |
|---|---|---|---|
| **Preâmbulo** | raciocínio bilhete a bilhete ANTES do bloco | 935 a 2.227 chars, varia 2,4× entre rodadas | **não sem risco** |
| **Notas** | análise escrita DEPOIS do bloco | 518 a 1.497 chars | **sim, de graça** |

**As notas não têm como melhorar o que já foi decidido** — elas vêm depois da resposta.
Já o preâmbulo é cadeia de raciocínio, e a s301 já viu que tirar espaço de deliberação
piora a extração.

**Duas medições que fecham o caminho e valem por si:**

1. **`claude-sonnet-4-6` NÃO aceita prefill de assistente.** A API responde
   `This model does not support assistant message prefill. The conversation must end
   with a user message.` Então a técnica clássica de forçar o início da resposta com a
   cerca ```` ```tsv ```` **está fora**. Fica registrado para ninguém tentar de novo.
2. **`stop_sequences=["\n```\n"]` funciona e é seguro.** Nas duas rodadas com ele o
   texto depois do bloco foi a **zero**, o `stop_reason` veio `stop_sequence`, e **o TSV
   saiu IDÊNTICO ao das rodadas sem ele, nas 4 execuções**.

⚠️ **A costura:** `_extract_tsv_rows` casa `` ```tsv\n(.*?)\n``` `` e **exige a cerca de
fechamento**, que a sequência de parada NÃO devolve na resposta. Quem implementar tem de
remontar a cerca antes de parsear, senão o parser devolve `[]` e a extração inteira some
sem erro — a família do §179 (chunk sem bloco ```tsv).

**Quanto vale:** as notas somam ~260 tokens por chamada. Com o ritmo atual (~2.240
chamadas/mês) isso é da ordem de **US$ 9/mês**, não os US$ 110 da estimativa. É barato de
fazer e não tem risco medido, mas **não é a alavanca que eu tinha anunciado** — a
economia grande continua sendo o tradutor e a barreira.

**Decisão do Feca:** ligar o `stop_sequences` (ganho pequeno, risco medido como zero, mas
mexe no caminho quente da extração) ou deixar para quando outra coisa já for tocar ali.

### 3.8 O MASTER é silencioso em 4 pontos, e a IA improvisa em 76,7 % das releituras (s333, ampliado na s336). VIVA.

> ⚠️ **Este item cresceu.** Ele começou como "a notação da linha partida", que continua
> abaixo e é a maior das quatro. A medição da s336 mostrou que o problema é geral, não de
> um mercado: → [`PLANO_TRADUTOR §II.9`](docs/PLANO_TRADUTOR_DETERMINISTICO.md#ii9-o-gate-da-fase-3-é-impossível-como-está-escrito-s336)

**Medido sobre 8.255 leituras da sombra: em 76,7 % delas a IA descreveu de forma
DIFERENTE algo que ela já tinha descrito.** No maior mercado da base (`Gols + -`, 4.123
leituras) a instabilidade é **100 %**, com doze formatos para a mesma seleção.

Isso tem duas consequências que valem mais que a economia de token:

1. **O gate da Fase 3 do tradutor é impossível como está escrito** ("< 1 % de divergência
   contra a IA"): o teto de acerto de qualquer tradutor determinístico contra este juiz é
   **~23 %**. A régua tem de passar a ser o MASTER, não a IA.
2. **A base tem a mesma aposta descrita de doze formas.** Não quebra o P/L, mas envenena
   leitura por descrição e a dedup de bilhete **sem código**, que compara descrição.

**As quatro decisões, por tamanho:**

| # | Decisão | Leituras que resolve | Status |
|---|---|---|---|
| **A** | Notação da linha: `Over` × `Mais de`, ponto × vírgula, forma da linha partida | **~5.000** | ✅ **FECHADA (s336)** |
| **B** | O objeto (`Gols`, `Pontos`, `Escanteios`) é obrigatório na descrição? | ~700 | ✅ **FECHADA (s336)** |
| **C** | Prop de SIM/NÃO: o rótulo entra na descrição, e em que forma | ~100 | aberta |
| **D** | Escopo de tempo: onde e como o período aparece | ~60 | aberta |

#### A e B, como o Feca decidiu em 09/09

1. **Linha asiática → sempre o QUARTO DE LINHA.** `Over 2.25 Gols`, nunca `Over 2.0,2.5`.
   **A recomendação que eu tinha dado era outra, e estava errada:** eu otimizei para "zero
   conversão no tradutor" e perdi o argumento que decide. Medido depois, **a Bet365 é a
   ÚNICA casa que manda as duas linhas** (2.207 blocos); as outras 21 já mandam `2,25`
   direto. Manter a forma dela faria a MESMA aposta ser descrita de dois jeitos conforme
   a casa, que é a inconsistência que esta frente existe para matar.
2. **Decimal da descrição é PONTO.** A vírgula do `MASTER_OUTPUT §12.1` vale para as
   colunas numéricas, e o motivo dela (a planilha em pt-BR ler ponto como milhar) não
   alcança texto. O item 5 do checklist do §19 dizia "decimal com `,`" **sem escopo**, e
   foi corrigido.
3. **O objeto é obrigatório, sempre.** `Over 2.5 Gols`, nunca `Over 2.5`, mesmo quando o
   esporte torna óbvio: "é óbvio" é julgamento, e julgamento refeito a cada leitura é a
   origem medida da variação.

**Aplicado:** `MASTER_DESCRICAO §10.1` (as duas regras) e **§10.1.1** (novo, a linha
asiática) · `MASTER_OUTPUT §19` item 5 (escopo) · `descricao_check` passou a derivar a
média **exata** das duas linhas do bloco, senão toda descrição de asiática da Bet365
reprovaria em `linha-fora-do-bloco`. Média errada continua reprovando, com teste para os
dois lados e prova por mutação. **Um teste antigo foi INVERTIDO** de propósito
(`test_media_de_linha_asiatica_partida_e_pega`), com o motivo escrito nele.

Fechada cada uma, ela entra no `MASTER_DESCRICAO`, o `descricao_check` ganha a checagem
positiva e o tradutor implementa. **Nenhuma linha de código do tradutor deveria ser
escrita antes da A**, senão ela é escrita contra um alvo que ainda vai mudar.

---

#### A (detalhe): a notação da LINHA PARTIDA

Medido na sombra: das 538 divergências de número entre tradutor e IA na Bet365,
**520 (96,7 %) são notação, não valor**. O `MASTER_DESCRICAO` mostra `Over 2.5 Gols`
(decimal com **ponto**) e **não diz nada sobre linha partida**. Sem regra, a IA escreve o
mesmo caso de três jeitos:

| A casa manda | A IA escreveu | O tradutor escreve |
|---|---|---|
| `Menos de 2.5,3.0` | `Under 2,5/3,0` | `Under 2.5,3.0` |
| `Menos de 4.0,4.5` | `Under 4,25` (média) | `Under 4.0,4.5` |
| `Menos de 3.0,3.5` | `Under 3.25` (média, com ponto) | `Under 3.0,3.5` |

**Decisão do Feca:** qual é a forma canônica. Três candidatas, e a escolha vale para os
dois lados (a IA passa a ser corrigida pelo MASTER, o tradutor passa a ter contra o que
conferir):

- **`3.0,3.5`** (as duas linhas, vírgula) — é o que a casa manda e o que o tradutor copia.
- **`3.0/3.5`** (as duas linhas, barra) — mais legível, e a barra não colide com decimal.
- **`3.25`** (a média) — mais curta, e **o sistema já a rejeita** (ver abaixo).

**A terceira já é ERRO hoje, e isso não é opinião: foi medido.** `checar_fidelidade`
exige que todo decimal da descrição exista no bloco cru daquele código, e `4,25` não
existe num bloco que diz `Menos de 4.0,4.5`. Rodando o gate contra os casos reais da
sombra:

| Descrição que a IA escreveu | `descricao_check` |
|---|---|
| `Under 3.0,3.5 [KRC Harelbeke v RFC Mandel Utd]` | passa |
| `Under 2,5/3,0 Gols [CD Coopsol v Juventud Huracán]` | passa |
| `Under 4,25 Gols [Auckland United (F) v …]` | **erro · `linha-fora-do-bloco`** |
| `Under 3.25 Gols [Wiener Sportclub (F) v …]` | **erro · `linha-fora-do-bloco`** |

**E o bilhete `FR8047691271I` aparece na sombra escrito dos DOIS jeitos** (`Under 3.0,3.5`
duas vezes, `Under 3.25 Gols` uma). Mesmo bilhete, mesma casa, mesmo dia: é a família do
"a IA acertou nas duas últimas e o banco ficou com a primeira", agora medida na notação.

> **Correção de uma afirmação minha da mesma sessão:** eu escrevi que a forma média
> quebraria HW/HL. **Não quebra.** O `_LINHA_PARTIDA_RE` (`repository.py:472`) aceita
> quarter (o ramo que casa decimal terminado em 25 ou 75), e toda média de duas
> meias-linhas consecutivas cai em
> `.25` ou `.75`. O que ela quebra é o gate de fidelidade, acima — argumento mais forte,
> e conferido.

Fechada a regra, ela entra no `MASTER_DESCRICAO` e o `descricao_check` ganha a checagem
positiva (hoje ele só reprova o que não está no bloco; não exige uma forma). Enquanto não
fechar, **não conte as 520 linhas de notação como divergência do tradutor** — não são.
→ [`PLANO_TRADUTOR_DETERMINISTICO §II.8`](docs/PLANO_TRADUTOR_DETERMINISTICO.md#ii8-a-sombra-medida-s333-0909--e-os-três-achados-que-mudaram-o-desenho)

---

## 4. Dívida técnica medida

> Achado, com arquivo e linha, e não corrigido. Aqui a referência é pista, não endereço.

*(bloco herdado do `STATUS §5`, verbatim — a varredura de 10/08, s261.)*

**Próximo passo (backlog vivo, um por vez):**
- **O `/casas` do `servidor_demo` não devolve o campo `captura` (s347). VIVA, medida.** A rota real passou a devolver `captura` na s345 (`GET /casas`), e o mock em `scripts/demo/servidor_demo.py` ficou com `{"casas": [...]}` só. Consequência: no demo o **selo de captura** e o **aviso antes de processar** nunca acendem sozinhos — todo harness que os exercite tem de alimentar `CASAS_CAPTURA` à mão, e um print de material de venda sai sem o selo sem que nada acuse. É uma linha no mock. **Sintoma para reconhecer isto noutro campo:** o demo serve o front REAL, então campo novo na rota é dívida silenciosa do lado dele.
- **`var(--text1)` não existe em token nenhum, e tem 4 usos (s341). VIVA, sem defeito visível.**
  `dash/assets/js/app.js` usa `color:var(--text1)` nos títulos dos drills de **tipster**, **casa**
  e **esporte** e no cabeçalho do modal de editar aposta. O token **não está definido** em
  `dash/assets/css/tokens.css`, em `app/static/tokens.css` nem no `pack/`. Hoje isso **não dá
  defeito**: sem valor, a propriedade cai no `color` herdado, e `html, body` já é `--ink`
  (`layout.css:8`) — exatamente a cor certa. É token MORTO, e o problema é que ele **passa em
  qualquer grep de cor** e sobrevive a auditoria: quem trocar a cor do body um dia leva os quatro
  títulos junto, sem aviso. **Conserto: trocar por `var(--ink)` nos 4 pontos** (`grep -n "var(--text1)"
  app/static/dash/assets/js/app.js`). Achado na s341, ao escrever o `shConfirm()` — que **nasceu
  com `--ink`, sem replicar a violação**.
- **`@app.post("/tipsters/sugerir")` está registrado DUAS vezes (s341). VIVA — a 2a é inalcançável.**
  `app/main.py:4094` (`sugerir_tipsters_route`, o matcher por evidência da s289) e `:4236`
  (`sugerir_tipster_route`, que o próprio docstring chama de *"de gaveta/teste"*). O FastAPI casa
  na ordem de registro, então **a primeira vence sempre** e a segunda é código morto que ainda
  carrega um `SugerirTipsterRequest` e uma chamada a `sugerir_tipster`. **Perigo real: quem editar
  a de baixo achando que é a rota em uso não vê efeito nenhum** — e não há erro que denuncie.
  Conserto: apagar a segunda, ou renomeá-la para um path próprio se o teste de gaveta ainda
  servir. Conferir antes se `tests/test_rota_sugerir.py` mira alguma das duas.
- **A Jonbet é a única das três casas do `jb_inject` sem o CORS medido (s340). VIVA.** Betboom
  (`api-32-sp-c7818b61-598`) e Blaze (`api-31-sp-c7818b61-584`) foram medidas no navegador e
  **as duas recusam `credentials:"include"`**. A Jonbet roda no MESMO cluster e MESMO hash da
  Blaze, mas a conta estava deslogada no Chrome do teste. O fallback já a cobre, então isto
  **não é bug aberto, é medição faltando**: quando houver sessão, repetir a mesma chamada com
  e sem `credentials` e anotar em `CASA_JONBET §2.1`. Se as três recusarem, o `include`
  vira tentativa perdida em toda captura e pode simplesmente sair.
- **`credentials:"include"` sem fallback em 12 injects (s340). VIVA, não medida.** A Betboom
  provou que a recusa de credencial pelo CORS **zera o replay inteiro** em vez de degradá-lo,
  e que o sintoma não parece defeito: a captura volta com o punhado que o hook passivo colheu
  da tela. Só `vb_inject` (s303) e `jb_inject` (s340) têm o fallback; seguem sem ele
  `bda_inject`, `bds_inject`, `bf_inject`, `bnc_inject`, `kto_inject`, `nv_inject`,
  `pn_inject`, `pt_inject`, `rg_inject`, `spb_inject`, `stk_inject`, `tv_inject` e
  `x1_inject`. **A política é por TENANT, não por motor**, então nenhuma dessas está provada
  por herança. **Medir antes de mexer** (é uma linha de F12 na casa logada: repetir a chamada
  do replay com e sem `credentials`), e comparar a contagem capturada com o `count`/total que
  a API declara. O conserto, quando for, é o `pedirPagina` do `vb_inject.js:175-204` copiado
  verbatim — aditivo, nunca troca o caminho de quem já funciona.
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
| **SaaS multiusuário** | [`docs/PLANO_MULTIUSUARIO_2026.md`](docs/PLANO_MULTIUSUARIO_2026.md) | **Fase 4 (pagamento)**: gate `assinatura_ativa` + webhook. As Fases 1, 2 e 3 estão no ar (s233–s236). **Gateway decidido na s342: Asaas**, por levantamento de 21 provedores (Efí é o plano B). O critério que decidiu não foi preço, foi **quem leva o Pix até a assinatura** — Stripe e Pagar.me só fazem recorrência por cartão. Três gates ANTES de qualquer código, e nenhum é engenharia: **(1)** idade do CNPJ, porque o Pix Automático exige CNPJ ativo há 6 meses (Asaas e Cielo) e sem isso sobra QR mensal que o cliente paga à mão; **(2)** CNAE primário de software, nunca 92.00-3, porque o MCC deriva dele e é o MCC que cria o risco (a Pagar.me publica esse de-para); **(3)** ler o Anexo I de Bets dos Termos da Asaas logado (está atrás de 403, e é onde repousa todo o sinal positivo dela). **Não abrir a conta antes da Fase 4.1** — os 3 meses de tarifa promocional contam da criação, não da 1ª venda. E ligar cobrança de Pro/Operação só depois do tradutor: o `ESTUDO_PRECIFICACAO §7.5` mede os dois negativos com o custo de hoje | 🟡 |
| **Barreira de recaptura** | [`docs/PLANO_BARREIRA_RECAPTURA.md`](docs/PLANO_BARREIRA_RECAPTURA.md) | **Fase 0 (registro escuro) no ar desde a s334** — mede sem filtrar. Faltam a **Fase 1** (ligar o filtro, com as 4 costuras do `§6`: cobertura, órfãs, bilhete sem código e lote vazio) e a **Fase 2** (medir 30 dias). Simulado: **−29,3 % da conta**, R$ 0,092 → R$ 0,065 por bilhete | 🔴 |
| **Tradutor determinístico** | [`docs/PLANO_TRADUTOR_DETERMINISTICO.md`](docs/PLANO_TRADUTOR_DETERMINISTICO.md) | Fases 1 a 4. A Fase 0 roda em **modo sombra** (13.965 pares, 21 casas, em 13 dias). A correção **B** segue **bloqueada** (`§IV.6`). **Remedição de 08/09** ([`ESTUDO_PRECIFICACAO §7`](docs/ESTUDO_PRECIFICACAO_2026.md#7-revisão-de-08092026-s332--o-que-aconteceu-depois-de-a-e-c)): a pré-condição do preço virou **Bet365 + Betano**, não a Bet365 sozinha | 🔴 |
| **Perfil de Tipster** | [`docs/PLANO_TIPSTER.md`](docs/PLANO_TIPSTER.md) | **P1** resultado em unidades (backend pronto; a UI trava no formato "u", passa pelo `/nova-ui`) · **P2** atribuição por watermark · **P3** Telegram como fonte. Fase 0 no ar (`origem_tipster`) | 🟢 / 🟡 / 🔵 |
| **Resolvedor de atribuição** | [`docs/PLANO_INTELIGENCIA_TIPSTER.md`](docs/PLANO_INTELIGENCIA_TIPSTER.md) | ⚠️ **doc defasado** — descreve o matcher **v5, de 15/07**; ele mudou muito desde então (corte de valor redondo e `valores.size===1` na s221, peso declarativo na s289, volta do declarado onde a base é cega na s310). A tese (o resolvedor) segue aberta; o texto precisa de banner de data | 🟡 |
| **Extração worldwide** | [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) | Fases 1 a 5 (confidence da IA + guardrail de enum). Fase 0 validada | 🟡 |
| **Custos numa tela so** | [`docs/PLANO_CUSTOS_TELA_UNICA.md`](docs/PLANO_CUSTOS_TELA_UNICA.md) | **Fatias 0 e 1 no ar desde a s348** (previa so-leitura + preco do fornecedor com data de vigencia, tabela `fornecedor_preco`, espelhada em `custo_conta` para as telas antigas seguirem certas). Faltam: **2** custo sai do par `fornecedor||casa` e vai para a CONTA, com migracao e a decisao de qual regua vira unica (hoje a Visao Geral cobra por janela de vida e a tela nova por lancamento, as duas certas e rotuladas) · **3** tipo de cobranca do tipster (mensalidade arrasta, staking nao) · **4** categorias de gerais · **5** Bookies recebe custo e P/L liquido por casa, e as tres telas antigas saem do menu. **Proximo passo e humano:** o Feca navegar na previa com a base real antes da Fatia 1 | 🟡 |
| **Casca unificada** | [`docs/PLANO_CASCA_UNIFICADA.md`](docs/PLANO_CASCA_UNIFICADA.md) | **Fatia 3**: topbar compartilhada, poda de CSS morto, aposentar links cross-app. Fatias 1 e 2 no ar. Fatia 4 (SPA único) só se o host com iframe não bastar | 🟢 |
| **Polymarket incremental** | [`docs/PLANO_POLY_INCREMENTAL.md`](docs/PLANO_POLY_INCREMENTAL.md) | A marca d'água não existe em `app/polymarket.py` (conferido hoje). É caminho de dinheiro: **precisa de teste de paridade na carteira do Feca** antes de subir | 🟡 |
| **Dashboard opção C** | [`docs/PLANO_DASHBOARD_C.md`](docs/PLANO_DASHBOARD_C.md) | Não iniciado. Condicional à medição pós-gzip (`ADR-002` Fase 2) | 🔵 |
| **Flag de inferência por campo** | [`docs/PLANO_INFERENCIA_POR_CAMPO.md`](docs/PLANO_INFERENCIA_POR_CAMPO.md) | Sem código. Precisa de OK do Feca + passo dedicado (mexe no pipeline de extração) | 🔵 |
| **Dinheiro → NUMERIC/Decimal** | [`docs/ADR-001-migracao-numeric-decimal.md`](docs/ADR-001-migracao-numeric-decimal.md) | Fase 0. **Adiado por desenho**, com gate | 🔵 |
| **Dashboard 1ª carga** | [`docs/ADR-002-dashboard-primeira-carga.md`](docs/ADR-002-dashboard-primeira-carga.md) | Fase 2 (agregação no servidor), condicional à medição | 🔵 |
| **Assinatura de tipsters** | `Ideias/Estudo_Assinatura_Tipsters_Sharpen.pdf` + `Ideias/Modelo_Financeiro_Rota_propag_Sharpen.pdf` | Estudo concluído (s122), execução **não iniciada**. Rota B (gateway regulado com split — **Asaas**); Stripe descartada. Próximo: fundir os 2 PDFs num documento mestre e a conversa comercial com a Asaas. Depende da Fase 4 do SaaS. **A s342 mediu o risco de segmento e ele é PIOR aqui que na rota A** — a rota A é software de gestão e não aparece em lista nenhuma; a rota B é venda de prognóstico e aparece: a Gumroad, único processador do mundo que documenta a fronteira e que nos **permite** explicitamente (*"bet logs, bankroll and session trackers, profit-and-loss spreadsheets"*), proíbe do outro lado *"picks, predictions, tips or 'signals'"*. Some que split de tipster nos torna marketplace, com obrigação contratual de policiar o segmento dos parceiros. **Não construir antes do gate 3 da Fase 4** (Anexo I da Asaas), e a pergunta ao comercial vai por escrito, com a resposta guardada. Vedam por escrito e alcançam software de terceiro: Iugu, Mercado Pago, AbacatePay, Pagali, e todo o bloco de infoproduto (a Eduzz nomeia *"robôs, softwares ou jogos digitais de aposta"*) | 🔵 |
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
