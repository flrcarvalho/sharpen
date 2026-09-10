# CLAUDE.md — Planilhador (FDC Capital)

> Regras operacionais obrigatórias para este projeto.
> A bíblia de marca e design está em [`../pack/CLAUDE.md`](../pack/CLAUDE.md).
> O ponteiro de navegação do projeto pai está em [`../CLAUDE.md`](../CLAUDE.md).

---

## ⚠️ CASA NOVA — leia antes de começar

Casa tem **duas camadas independentes**. Confira qual você vai mexer:

| Camada | O que é | Guia | Gate |
|---|---|---|---|
| **Leitura** | `casas/CASA_*.md` + registro no seletor/favicon. Já funciona por **print**. | [`docs/GUIA_NOVA_CASA.md`](docs/GUIA_NOVA_CASA.md) | `python tools/audit_casas.py` |
| **Captura** | robô do SharpenUp lendo a API da casa. **12 pontos de registro** em 4 camadas. | [`docs/GUIA_CASA_SHARPENUP.md`](docs/GUIA_CASA_SHARPENUP.md) | `python tools/audit_sharpenup.py` |

Mapa do sistema: [`docs/SHARPENUP_ARQUITETURA.md`](docs/SHARPENUP_ARQUITETURA.md).
Regressão da captura: `node extensor/harness/run.mjs` — **rode antes de todo commit que
toque `extensor/`**. Skills: `/sharpenup-recon` → `/sharpenup-casa` → `/sharpenup-validar`;
casa que parou → `/sharpenup-diagnostico`.

> **Nunca escolha o modo TEXTO sem provar que há linha em branco entre bilhetes no
> `innerText`.** Sem isso a lista vira um bloco só e a IA perde o resto **em silêncio**
> (s192: KTO, ~90 % dos bilhetes). Na dúvida, vá por trás — F12 → Network → a API da casa.

---

## Invariantes (nunca quebrar)

1. O app **lê** os masters, **nunca escreve**. Mudança = diff revisado + aprovação humana.
2. Arquivo de casa **traduz**; nunca redefine regra global.
3. **Cálculo é global, localização é da casa.**
4. Backup em `Planilhador/Backups/<nome-descritivo>/` antes de qualquer edição. Nunca usar `FDC Capital/Backups/`. **Copie só os arquivos que serão editados** — nunca `STATUS.md`, nunca `docs/HISTORICO.md` (o git já os versiona), nunca diretórios inteiros. `Backups/` é gitignored/manual; podar além de ~últimas sessões / 90 dias. Gate: `python tools/check_docs.py`.
5. Arquivos completos, nunca diffs parciais.
6. Uma mudança por vez. Propor → aguardar confirmação → executar.
7. Atualizar `STATUS.md` ao fim de cada mudança aplicada.
8. **Commit e push sempre juntos.** Após cada mudança aprovada: `git add` → `git commit` → `git push`. Deploy automático via Railway. Nunca deixar commit sem push.
   - **Com mais de uma sessão aberta, `add` e `commit` vão no MESMO comando**, e faça `add`
     dos seus arquivos **por nome** — nunca `git add -A`/`.`. O index é compartilhado:
     arquivo que fica esperando entre um e outro é levado por quem commitar primeiro.
     Confira com `git show --stat` depois de commitar; se levou arquivo alheio, **não
     reescreva histórico já pushado** — registre no `STATUS.md` e siga.
     → [o caso](docs/CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026)
9. **Toda atualização fechada = perguntar se avisa os testers**, já com a mensagem pronta (ver abaixo). O Feca escolhe informar ou não. Nunca enviar sem o "pode mandar".
10. **Um arquivo, uma pergunta — e o gate é `python tools/check_docs.py`.**
    `CLAUDE.md` = regras vinculantes · [`STATUS.md`](STATUS.md) = estado atual **+ no máximo as 3
    últimas sessões** · [`BACKLOG.md`](BACKLOG.md) = **tudo que está aberto** ·
    [`docs/HISTORICO.md`](docs/HISTORICO.md) = o resto. **Pendência nova vai para o `BACKLOG.md`,
    nunca para o `STATUS.md`** — foi de lá que ela virou 51 KB escondidos dentro de um changelog,
    e quatro arquivos passaram a disputar o papel de "onde o projeto está".
    Ao fechar um item, **tire-o do `BACKLOG.md` na mesma sessão**: regra nova vai para o lugar
    canônico (`MASTER_*` / `CASA_*` / este arquivo), história vai para o `HISTORICO.md` e o
    **caso** que originou uma regra vai para o [`docs/CASOS.md`](docs/CASOS.md).
    **Regra sem gate não é cumprida neste repo — está medido**
    ([o caso](docs/CASOS.md#10--o-inchaço-que-originou-o-gate)). O `check_docs.py` **não lê
    conteúdo**: um `STATUS.md` de 49 KB só de história passa. Ele cobre tamanho, forma
    (≤3 blocos de sessão, ≤2 `_Anterior:`), cópia em `Backups/`, link quebrado e âncora.
    > **Os tetos travam CRESCIMENTO; não mandam cortar.** Ao encostar num deles, mova
    > **caso** para o [`docs/CASOS.md`](docs/CASOS.md) ou **sessão** para o
    > `docs/historico/`. **Nunca corte os blocos "sintoma para reconhecer isto noutro
    > campo"** — são eles que fazem uma sessão nova reconhecer a **família** de um defeito
    > antes de repeti-la (a s321 e a s327 são a mesma família, e é isso que está escrito
    > ali). Subir um teto para não cortar é pior ainda: foi assim que o `STATUS.md` chegou
    > a 187 KB.

---

## Aviso de versão ao grupo `Sharpen - Testers`

O `@sharpenbetbot` é admin do grupo e serve de canal de **novas versões e atualizações**.

**O aviso e a home são o MESMO ato — `python scripts/avisar_testers.py`.** Ele mostra a
prévia (ensaio é o padrão; só envia com `--enviar`), confere o destino por `getChat`,
publica no grupo e grava a mesma nota em `app/changelog.json`, que é o que a home lê pela
rota `/changelog`. **Nunca edite o changelog à mão e nunca mande a mensagem por fora** —
senão a home fica versões atrás em silêncio ([o caso](docs/CASOS.md#o-changelog-ficou-8-versões-atrás-duas-vezes)).
`tests/test_changelog.py` fica **vermelho** quando a versão do manifest não tem nota
(dispensa só declarada, em `sharpenup_sem_nota`). Gate manual: `python tools/audit_changelog.py`.

**Só informamos. Não damos detalhes.** A mensagem diz o que mudou em **uma linha** e o que o
tester precisa **fazer**. Ficam de fora: mecânica interna, nome de campo, causa raiz, número de
bilhete, arquivo, commit. O nível é o de nota de release curta, não o do `STATUS.md`.

> ⚠️ **`Sharpen` é o SISTEMA; `SharpenUp` é a EXTENSÃO.** O número de versão é do
> **SharpenUp** — é ele que o tester atualiza. Escrever "Sharpen 0.6.46" versiona o produto
> inteiro. Vale para release note, changelog e qualquer texto voltado ao usuário.
> → [o caso](docs/CASOS.md#sharpen-0646-versionou-o-produto-inteiro)

- `chat_id` = `-5172183099` · `BOT_TOKEN` no `.env` de `Downloads/BOTS/sharpen-bot`.
- **Confirmar o destino com `getChat` antes de publicar.** Mensagem em grupo não tem desfazer.
- **Nunca `getUpdates`** — briga com o polling do bot em produção.
- **Nunca diagnostique envio chamando `sendMessage` de novo.** Grupo real não tem desfazer,
  e a segunda chamada publica o teste. Na primeira falha, **imprima o `description` da
  resposta**: ele já diz a causa ([o caso](docs/CASOS.md#o-teste-de-diagnóstico-foi-parar-no-grupo)).
  Chame a API por Python, que controla o UTF-8 de ponta a ponta. Para testar de verdade, use
  um chat seu, nunca o grupo.
- **Identificar mensagem já enviada, sem `getUpdates`:** a Bot API não tem `getMessage`. Use
  `editMessageText` com o texto **idêntico**. O erro `message is not modified` só aparece
  quando o conteúdo bate exatamente, então ele confirma a identidade **sem alterar a
  mensagem**. Faça isso antes de qualquer `deleteMessage` por id deduzido: id vizinho pode
  ser a linha de um tester, e apagar mensagem de terceiro não tem volta.
- É **grupo comum**, não supergrupo. Se for promovido, o id passa a `-100…` e o envio falha; o
  `getChat` acusa antes.
- Extensão: a ação do tester é sempre atualizar em `sharpen.bet/extensao` (distribuição manual).

---

## Conta de usuário nova = duas metades, e a segunda é humana

> **Antes de tudo: hoje quase toda conta nova NÃO passa por aqui.** Desde a Fase 2 quem
> se cadastra pelo site cria a própria linha em `usuarios`, com o hash da senha que ele
> mesmo escolheu; ao supervisor cabe **aprovar** (`status` → `ativo`). **Não há env var,
> não há deploy, não há linha em `app/auth.py`** — o dict `USUARIOS` é *semente* das
> contas anteriores ao autosserviço. Mande subir env var para quem se cadastrou sozinho
> e você está resolvendo um problema que não existe. **Meça primeiro:**
> `select username, status, length(senha_hash) from usuarios where …`.
>
> **E o `dono` TEM de ser o username — não o nome de marca.** Os dois divergem com
> frequência, e o isolamento por `dono` **falha em silêncio**: import feito sob o nome de
> marca não dá erro nenhum, só entrega tela vazia para o usuário certo. Confirme o username
> **na tabela**, nunca pelo nome do arquivo, do canal ou da planilha. A ponte entre os dois
> nomes é o registro `TIPSTERS_PUBLICOS` (`app/main.py`), onde o **slug** é a marca e o
> `dono` é o username. → [o caso](docs/CASOS.md#a-marca-não-é-o-username--fleury--flurray)

O caminho abaixo vale só para as contas **antigas** (semente) ou criadas à mão.

Criar login é 1 linha em `USUARIOS` (`app/auth.py`) + a env var `SENHA_<USER>_HASH` no
Railway. **Não existe migration, seed nem import:** o isolamento é a coluna `dono` no
Postgres, então a base nasce vazia e o primeiro bilhete capturado cria as linhas.

O código sobe no push. A senha depende de alguém colar a variável no Railway — e
**enquanto ela falta o login diz "usuário ou senha inválidos"**, igualzinho a senha
errada (`USUARIOS[x] == ""` nunca autentica; fail-closed por desenho).

**Antes de suspeitar do código, separe código de configuração medindo:** um asset que
só existe no deploy novo responde 200 → o usuário está em `USUARIOS`; `POST /login`
devolvendo **401** tem origem única (`verificar_credenciais` falso) — 429 é rate-limit,
500 é erro do app. Usuário existindo + 401 = env var ausente, env var truncada **ou a
senha simplesmente não é aquela**.

**Essa terceira causa é a mais provável em conta de autosserviço.** O supervisor passa a
senha que ele *planejou*; quem se cadastrou pelo site escolheu outra. **Não trate senha dita
por terceiro como fato: prove contra o hash**, é uma linha e é leitura pura —
`bcrypt.checkpw(b"<senha>", (select senha_hash from usuarios where username=…))`. Isso
separa "senha errada" de "transporte quebrou" antes de mexer em qualquer coisa.
→ [o caso](docs/CASOS.md#a-senha-simplesmente-não-era-aquela)

**Resetar a senha de quem se cadastrou sozinho é decisão do dono da conta, não sua.** Não
existe rota de troca no app (só `/admin/usuarios/{u}/aprovar` e `/suspender`), então
mudar significa `UPDATE` cru em `senha_hash` e derrubar o acesso da pessoa. Pergunte.

**Ao gravar senha em env var, confira o que CHEGOU, não o que você mandou:** comprimento
e último caractere. `!`, `$` e `` ` `` são comidos por shell que interpola — o `$` do
bcrypt é o caso clássico, e um `!` no fim de senha é o mesmo problema com outra roupa.

**O `$` do hash bcrypt é a armadilha de transporte:** `$2b$12$…` passa mutilado por
qualquer shell que interpole variável (PowerShell inclusive). Cole na caixa de Variables
do Railway, confira **60 caracteres** e nenhum espaço nas pontas. Hash nunca vai para o
git. Decidir também se a conta é **dono solo** ou entra em `OPERADORES` — solo é o
default; operador significa que o supervisor vê a base dele e que a dedup cruzada passa
a valer entre os dois.

---

## Bot de tipster: NUNCA peça a senha dele. Aprove a conta e ligue o botão.

É **um token de serviço só, para sempre** (`SHARPEN_BOT_TOKEN`, o mesmo valor nos
dois serviços do Railway: o app e o `sharpen-bot`). O bot se identifica assim:

```
Authorization: Bearer <SHARPEN_BOT_TOKEN>
X-Sharpen-Dono: <username do tipster>
```

**Tipster novo = aprovar a conta no `/admin` + clicar "Ligar bot".** Zero variável, zero
deploy, zero senha de terceiro. As env vars do tenant (`<XX>_APOIO_ID`, `<XX>_DESTINO_ID`)
seguem existindo porque são ids de Telegram, não credencial.

**Três condições, todas obrigatórias** (`auth.dono_do_bot`): token confere · dono está
`ativo` · dono tem `bot_habilitado`. A terceira é o que impede o token de virar
chave-mestra: conta aprovada não ganha escrita de robô de brinde. Desligar o botão corta
a escrita em ≤60s (TTL do cache), sem deploy e sem rotacionar o token.

**Escopo:** a identidade do bot **não** entra em `usuario_atual` nem em `dono_efetivo`.
Ela vive em `usuario_atual_ou_bot` / `dono_efetivo_ou_bot`, aplicadas só nas 4 rotas que o
bot usa. `grep -n "_ou_bot" app/main.py` lista tudo o que o token alcança, e
`tests/test_bot_token.py` **quebra** se alguém aplicar numa rota nova.

> **Ao migrar um tenant, ligue o botão ANTES de o token existir no Railway.** Os tenants
> trocam de caminho de autenticação **juntos**, e quem não tem botão passa a tomar 401 em
> cada operação — sem perder bilhete (o `/salvar` é UPSERT por código), mas **a marcação de
> resultado para de chegar**, sem erro nenhum.
> → [o caso](docs/CASOS.md#o-token-subiu-antes-dos-botões)

**Dado dessincronizado se conserta com `/ressincronizar [AAAA-MM]`** no apoio: o bot
reempurra ao Sharpen o que já está no storage dele. Seguro de repetir (UPSERT por código,
vazio nunca rebaixa). Deixa de fora anulado e bilhete **sem casa** — linha sem casa nasce
invisível no Painel de Contas e reenvio não conserta, porque a casa entra na assinatura.

---

## Perfil de tipster: a casa é SAÍDA da leitura. Nunca nomeie uma no prompt.

Todo perfil com visão fecha o prompt com `Print ilegível → {"erro": …}`. Se o prompt
também abre nomeando uma casa, o modelo lê as duas instruções como uma só e trata
**casa diferente como imagem ilegível**. O `vision.js` vira `throw` e o apoio publica
`⚠️ Não consegui ler o print`, **culpando a foto**.
→ [o caso](docs/CASOS.md#as-três-recusas-seguidas-do-rogerin--s309-dia-1-do-6º-tenant)

**A amostra diz o que o tipster FEZ, nunca o que ele FAZ.** Perfil nasce de um export
medido daquele canal, e escrever a casa observada no prompt transforma uma medição
datada em condição de entrada. Mesma família de "assinatura tem ERA".

**Como escrever:** liste `NOMES_CASAS` (`src/casas.js`), peça `"casa"` no JSON e diga
explicitamente que *casa, layout ou formato diferente NÃO é motivo de erro — "ilegível"
é sobre a IMAGEM*. No código, a precedência é **legenda → print → default**, passando o
que a visão devolveu por `casaPorTexto` (canoniza a grafia; verbatim ali cria conta
paralela) e **avisando no apoio quando é o default que decide** — casa errada não dá
erro, dá conta paralela.

Gate barato: o teste assere que a **1ª linha do prompt** não contém nome de casa nenhum.
Exporte o `SYSTEM` só para isso.

**O FORMATO do bilhete também não se herda da amostra.** Casa que vende N apostas
simples num print só (stake e retorno **por seleção**, "Aposta Total" no rodapé) quebra
o perfil que assume "1 print = 1 bilhete": **as pernas viram uma múltipla, sem erro
nenhum** — o produto delas no lugar de N apostas.
→ [o caso](docs/CASOS.md#as-três-simples-que-viraram-uma-múltipla-de-73)

Quando o print traz N simples, a stake **continua vindo da legenda, em unidades** — o
print traz R$ e o tamanho da unidade do tipster raramente foi medido. A stake em R$ do
print serve para conferir a **ORDEM**: as proporções não dependem da unidade, e legenda
escrita fora de ordem é o único jeito de o valor certo cair na aposta errada **sem o
total mudar**.

---

## Zero não é ausência. E "o app recusou" não é detalhe do app.

A casa nem sempre precifica as PERNAS. Bilhete de **mesmo jogo** ("Criar Aposta" /
Bet Builder / SGM) traz uma odd só, a do conjunto, e as seleções aparecem sem
número nenhum ao lado. Quem monta a combinação como produto das pernas faz
`0 × 0 = 0` e grava um zero onde havia um vazio.

**Zero é uma odd que não existe, e por isso ninguém a trata como ausência.** Ela
passa por toda checagem de forma: a linha tem stake, tem resultado, tem P/L. Só
que o P/L de W é `stake × (odd − 1)` — **com odd 0 o bilhete GANHO vira `−1u`**.
A regra vale para qualquer número derivado: se a fonte não tem o valor, a ausência
viaja como `null`/vazio até quem sabe decidir. `0` se disfarça de conta feita.
→ [o caso](docs/CASOS.md#o-bilhete-ganho-que-virou-1u--só-chutes-12-s318)

Onde há odd de conjunto, ela é a odd da aposta que cobre o **cupom inteiro** —
nunca de uma combinação parcial, que não é derivável de lugar nenhum.

**A outra metade: quem escreve na planilha tem de LER a resposta.** O `/salvar`
valida na fronteira (`validar_linhas`) e recusa stake/odd que não sejam número
> 0, devolvendo as recusadas em `rejeitados` e gravando só as boas — **a resposta
é `200`, não erro**. Escritor que ignora o campo marca "planilhado" e publica uma
linha que **nunca existiu**.
→ [o caso](docs/CASOS.md#a-linha-que-nunca-existiu-e-a-pista-que-apareceu-um-dia-depois)

- Recusa **total** é falha de planilha: erro alto, e o registro diz que não
  planilhou. Recusa **parcial** é aviso por linha, dizendo qual número caiu.
- O mapa `código → id` se remonta pelas linhas **aceitas** (`rejeitados[].linha`
  é a posição 1-based no TSV). Sem isso, uma recusa faz as apostas BOAS perderem
  o id junto — e é o id que o `PATCH` usa para corrigir linha já resolvida.

> Sintoma para reconhecer isso noutro escritor: o log diz "0 novas, 0
> atualizadas" e ninguém lê o log. Contagem devolvida pela API é dado, não
> enfeite — compare com o que você mandou.

---

## Data derivada por ESTIMATIVA é dado inventado. Use o instante que a fonte publica.

Duração típica não é duração. Somar ao kickoff uma "folga por esporte" para estimar quando o
evento acabou troca um instante **medido** por um **suposto** — e o suposto erra em prorrogação,
atraso e intervalo longo. Onde a casa só publica o início, **a data é o início**
(`CASA_BET365 §4`: jogo que começa 22:00 do dia 09 e acaba 00:30 do dia 10 é do dia 09).

Erro de horas só muda a **data** quando a soma cruza a meia-noite: some o dia inteiro e
aparece à noite. E como o MTD recorta `[1º do mês, hoje]`, o bilhete datado de amanhã **sai
da conta do mês** — não some da grade, some do KPI, e o dia seguinte "conserta" sozinho.
→ [o caso](docs/CASOS.md#o-mês-que-fechou-negativo-porque-a-folga-datou-8-vitórias-amanhã--s339)

**Converter FUSO é o contrário e continua obrigatório** (função exata do instante dado);
remover os dois juntos troca a data adiantada pela atrasada.

> Sintoma noutro campo: valor derivado por **duração típica**, **média** ou **estimativa** de
> algo que a fonte não publica. Mesma família do "zero se disfarça de conta feita", acima:
> aqui o palpite se disfarça de precisão.

---

## Gate que confere UM campo deixa os vizinhos livres. E o rótulo não é a prova — o número é.

**Confira cada campo por si.** A stake é determinística (vem do `Stake:` do bloco, sem IA);
a odd e o `resultado` precisam de conferência **própria**, nunca de carona no `if` da
stake — senão stake certa + odd errada passa reto.
→ [o caso](docs/CASOS.md#a-odd-que-era-o-retorno--bet365-s321)

**A prova é o RETORNO, contra as cinco fórmulas do `calcular_pl` lidas ao
contrário** (`repository._veredito_do_retorno`): `0 → L` · `= stake → V` ·
`= stake×odd → W` · `= (stake/2)×odd + stake/2 → HW` · `= stake/2 → HL` (só com
linha asiática **partida**) · nenhuma → cashout, `W` com `odd = retorno ÷ stake`.

> ⚠️ **O TEXTO do Status não serve de fonte, só o número.** `_resultadoB3`
> (`extensor/content.js`) escreve `Ganho → W` para **qualquer** retorno maior que a
> stake — meia vitória inclusive, e um gate que lesse o rótulo reescreveria `HW` correto
> como `W`. → [o caso](docs/CASOS.md#os-14-hw-que-um-gate-de-rótulo-teria-destruído)

**A outra ponta: o que a extensão escreve no bloco é uma ORDEM, não um recado.** O de-para
de rótulo sempre tem um `else`, e o `else` costuma dizer "a conferir — não liquidar
automaticamente". A IA obedece. Rótulo que ninguém cadastrou deixa de virar resultado e a
linha fica `aberta` para sempre, sem erro em lugar nenhum.
→ [o caso](docs/CASOS.md#o-push-da-pinnacle-que-ficou-pendente-depois-de-liquidado--draw-s328)

**Quando o número já prova, decida no formatador; não delegue.** Todo de-para de rótulo
precisa de rede por baixo, feita do dinheiro: resolvido + rótulo desconhecido + P/L
**exatamente 0** ⇒ retorno = stake ⇒ `V`. Isso fecha a família inteira em vez de um nome de
cada vez. Com P/L ≠ 0 o desconhecido continua subindo como "a conferir": inferir `W`/`L` de
um rótulo que não se conhece é chute.

> Sintoma para reconhecer isto em qualquer casa: a nota da IA explica o caso **certo** e
> mesmo assim nada muda. Procure o `else` de quem formatou o bloco antes de suspeitar da
> extração. E lembre que a **tela** e a **API** falam vocabulários diferentes — a Pinnacle
> exibe `REEMBOLSADO` e manda `DRAW`; documentar só o que a tela mostra esconde o caso.

**Só se escreve onde o DINHEIRO muda.** Retorno igual a stake/2 lê como `HL` ou como
cashout de metade — ambíguo — mas o P/L é idêntico; trocar ali é ruído por ruído.
Pelo mesmo motivo há **piso de R$ 1,00** no script de correção: abaixo dele a "correção"
troca a odd limpa da casa pela dízima do retorno arredondado ao centavo.
→ [o caso](docs/CASOS.md#o-piso-de-r-100--a-correção-que-sujava-a-odd)

**Formato de número é por TOKEN, não por casa** — a mesma casa mistura as duas convenções
no mesmo bloco. Daí o `_num_bloco`, separado do `_num_or_none`: o último separador é o
decimal, e **um separador só é sempre decimal**. A regra "3 dígitos = milhar", correta para
dinheiro, **multiplica toda odd de 3 casas por mil**.
→ [o caso](docs/CASOS.md#a-betfair-que-mistura-br-e-en-no-mesmo-bloco)

**Correção humana MANDA sobre a captura.** O script de reparo pula bilhete cujo
`resultado`/`odd` já tenha registro em `correcoes` — certo ou errado, é decisão do dono.
**O gate em tempo de extração NÃO tem essa trava** (roda antes do banco), e `resultado`
nunca foi congelado pelo UPSERT: recaptura de linha assim **desfaz a edição manual**.
Mesma família de "edição manual em casa sincronizada não sobrevive".
→ [o caso](docs/CASOS.md#os-3-bilhetes-betano-em-que-alguém-inverteu-w-e-l)

Gates: `tests/test_odd_resultado_determinista.py` e `scripts/corrigir_resultado_odd_s321.py`
— autorizados por um replay que mexeu em **3 de 5.316 blocos**, com zero falso positivo.
→ [a medição](docs/CASOS.md#a-medição-que-autorizou-o-gate)

> Sintoma para reconhecer isto noutro campo: um valor que é **outro campo do mesmo
> bloco**. Odd que é o retorno, stake que é a do vizinho (s311), descrição que é a do
> vizinho (s302). Quando a fonte imprime os dois, comparar é de graça.

---

## Planilha e bot escrevem na MESMA série de código. Só um pode ser a fonte.

Import de planilha e bot de tipster geram o mesmo `XX<aaaamm>-<n>`, e o código entra na
assinatura (`ID|casa|parceiro|codigo`). Dois escritores, uma série, nenhum sabendo do
outro.

Quando os dois escrevem o mesmo código, a assinatura bate e o `/salvar` trata como o
**mesmo bilhete**: o congelamento mantém descrição/odd/stake da linha importada e "vazio
nunca rebaixa" mantém o resultado. **A aposta é absorvida — sem erro, sem aviso, sem linha
nova.** → [o caso](docs/CASOS.md#a-aposta-que-foi-absorvida--passatips-259-s276)

- Os importadores **abortam** quando um código que gerariam já existe sob outra origem.
- No dia em que o bot entra, **suba o contador** (`/contador N` no apoio) para além do
  último código da planilha, antes da primeira aposta.
- **Prefixo novo se confere contra TODO `codigo_bilhete`, não contra a série.** Códigos
  nativos de casa também são duas letras mais dígitos (a Superbet grava `SP8399910931W`),
  e um regex ancorado no formato `XX<aaaamm>-<n>` **não os enxerga**: o prefixo aparece
  livre quando não está. **Use `LIKE '<PFX>%'` sobre a coluna inteira.** Não há colisão de
  assinatura (o formato difere e `casa` entra no hash), mas um prefixo já usado por casa lê
  como aquela casa para qualquer humano depois.
  → [o caso](docs/CASOS.md#o-prefixo-que-parecia-livre-e-não-estava--sp-s316)
- E decida qual é a fonte: **a partir daí o bot planilha e a planilha vira histórico
  congelado.** Manter os dois escrevendo é conviver com colisão a cada import.

---

## `DADOS` só tem aposta LIQUIDADA. Quem existe antes da 1ª aposta vem do cadastro.

`aplicarFeed` (`dash/assets/js/app.js`) parte o feed em dois: `DADOS` recebe só
`W/L/V/HW/HL` e `DADOS_ABERTAS` recebe o resto. Toda tela que deriva de `DADOS` herda
o mesmo ponto cego: **usuário novo, que só tem aposta em aberto, chega com `DADOS`
vazio.** O sintoma não é erro, é tela parada num "aguardando" que nunca resolve.
→ [o caso](docs/CASOS.md#a-tela-em-branco-do-diogo--s239)

A regra de fundo: **a existência de uma entidade não vem do bilhete.** Conta comprada
tem custo antes de apostar; o cadastro (`parceiros`) é a fonte de quem existe, e o
bilhete só acrescenta o que nunca foi cadastrado. Onde os dois valem, use a **união** —
na base do Feca são **130 contas** que só existem em bilhete e sumiriam se você trocasse
uma fonte pela outra em vez de somar.

Antes de unir cadastro e bilhete, **meça as duas divergências que duplicam linha**:
grafia de casa (`Bet365` × `BET365`) e fornecedor divergente para a mesma conta. Já
deram zero em todos os donos, mas isso é **medição datada, não garantia**.

> Separe **existir** de **contar no P/L**. Conta sem aposta aparece na tela para
> receber o custo, e continua fora de qualquer janela de P/L (`calcCostFiltered` usa
> a data da 1ª aposta). Misturar os dois é como o UPSERT meio-atualizado: vira lucro
> fantasma.

**Quem já tem valor lançado precisa ter linha na tela onde se lança.** É a mesma família
do UPSERT meio-atualizado, com um agravante que o esconde: **o total continua certo e só a
linha some** — a chave sai da tabela e o valor dela segue no KPI, cobrado e ineditável.
→ [o caso](docs/CASOS.md#o-tipster-cobrado-e-ineditável--s274-feedback-do-tester-joão-henrique)

Então a lista de qualquer tela de lançamento tem **duas** obrigações, não uma. Oferecer
quem existe (cadastro ∪ base, a regra acima) e **nunca esconder chave que já tem valor**.
Na prática são fontes distintas na mesma união: `_ctTipsters` (`charts/gestao.js`) soma
cadastro, `DADOS`, `DADOS_ABERTAS` e as chaves de `ctData` com valor > 0.

> Sintoma para reconhecer isso em outra tela: o KPI não bate com a soma da tabela que
> fica logo abaixo dele. Some pela tela antes de suspeitar do cálculo.

**Nem toda entidade tem cadastro. Esporte e mercado têm MASTER.** Para eles a fonte de
"o que existe" é a taxonomia canônica — `app/taxonomia.py` **lê** o `MASTER_ESPORTES §7`
e o `MASTER_APOSTAS §3`, e a rota `/taxonomia` serve as listas. A tela usa a **união** com
a base do dono, e os dois lados são load-bearing: o canônico oferece o que ele ainda não
apostou, a base preserva a grafia herdada de import (`Fórmula 1`, `Esoccer`,
`Tênis de Mesa`) que o canônico não tem e que **é a que o matcher compara**.

Ler o MASTER em vez de copiá-lo tira uma linha da regra de propagação acima, e o preço é
um parse que **falha em silêncio**: seção renumerada, tabela virando lista, e a extração
devolve `[]` sem erro nenhum — menu vazio para o usuário. Quem lê MASTER em código paga
o gate junto: `tests/test_taxonomia.py` trava âncoras e piso de tamanho, para MASTER
reformatado quebrar o CI em vez da tela.

---

## Custo de aquisição tem JANELA DE VIDA. Um dia e um mês da mesma conta custam igual.

O custo da conta é **único, pago na compra**, e existe enquanto a conta existe. Todo
período filtrado que **cruza** a janela cobra o custo **cheio** daquela conta:

```
ini = menor(adquirida_em, 1ª aposta)
fim = maior(última aposta, arquivada_em)   · HOJE p/ conta ativa ainda sem aposta
```

Comprou dia 01 e usou até o 22: qualquer recorte dentro disso cobra, o dia 28 não cobra,
o mês inteiro cobra uma vez.
→ [a régua antiga, e por que mudou](docs/CASOS.md#a-régua-antiga-r-0-de-custo-com-o-parque-inteiro-em-uso)

> ⚠️ **A régua NÃO é aditiva, e o preço foi aceito com a conta na mesa.** Somar os dias
> de setembro dá muito mais que o custo de setembro, e o P/L Líquido de UM dia carrega o
> custo cheio das contas vivas. Não "conserte" isso achando que é defeito. A alternativa
> (ratear pelos dias) foi recusada de propósito: rateio exige um horizonte arbitrário, e
> a janela pelo uso não tem constante nenhuma.

**O escopo vem do FILTRO, não das linhas.** `Casa` e `Operador` descrevem a CONTA e
recortam o custo; `Esporte` e `Tipster` descrevem a APOSTA e não recortam — a conta
Bet365 custou R$ 900 quer se olhe tênis ou futebol. Pelo mesmo motivo `calcCostFiltered`
não recebe mais `rows`: recorte sem aposta nenhuma tinha custo 0 com o período na tela, e
um mês filtrado encolhia até a última aposta dele.

**O fim da janela vem do USO, então ele existe sem ninguém declarar nada.** `arquivada_em`
só melhora o caso em que a conta foi encerrada de propósito. Arquivar carimba com
`COALESCE` (arquivar duas vezes não empurra o fim); reativar **zera** o carimbo, senão a
conta volta viva com o custo sumido dos dias em que já está em uso.

**`bilhetes.data` guarda DD/MM/YYYY e ISO na MESMA coluna** (`_data_iso` converte só na
saída). Todo backfill que leia data por SQL precisa dos dois ramos — ler só ISO acha quase
nada e faz toda conta antiga nascer com a janela começando na data do **import**.

**Fonte canônica:** `calcCostFiltered` / `_buildContaVida` / `_custoNaJanela`
(`dash/assets/js/charts/gestao.js`) e `parceiros.adquirida_em` / `arquivada_em`
(`database.py`). Gates: `tests/test_custo_janela_vida.py` (9 mutações, 9 detectadas) e os
três testes de janela em `tests/test_repository_db.py`, que medem o RESULTADO do backfill
— ele roda dentro de um `DO … EXCEPTION`, então erro sai como WARNING e o CI ficaria verde
com a coluna vazia.

> **Assimetria conhecida, ainda de pé:** o **Custo de Tipsters** (inline no `renderKPI`)
> segue com a régua antiga — cobra o **mês inteiro** e **ignora todo filtro**, inclusive o
> de tipster. Os dois cards ficam lado a lado medindo com réguas diferentes.

---

## "Sugerir tipsters" parou? O suspeito é um perfil novo, não o código.

O matcher (`_sugParaBilhete`, inline no `app/static/index.html`) só sugere com **folga ≥ 7**
entre o 1º e o 2º colocado. Em empate ele fica **vazio de propósito** — não chuta.

A consequência é o modo de falha: **um perfil novo pode matar um perfil antigo em silêncio.**
Nada aparece no rail nem no console, só a coluna vazia. O parser deriva o **final** de todo
valor não-redondo (`49 → 9`, `99 → 9`), então dois perfis podem virar donos do mesmo final e
se anularem. → [o caso](docs/CASOS.md#o-perfil-novo-que-matou-o-antigo--multilbb--lbb)

**Diagnóstico, nesta ordem:**

1. `select nome, criado_em from tipsters where dono = '<dono>' order by criado_em desc limit 5`
   — perfil criado ou editado nos últimos dias é o primeiro suspeito.
2. **Prove por remoção, não por dedução.** Extraia o bloco JS do `index.html`, rode em node
   contra os perfis e bilhetes **reais** do banco, e compare com e sem o perfil suspeito.
   Isola a causa sem editar nada.
3. Só então mexa no peso. E **meça**: backtest contra bilhetes já rotulados, antes e depois.

**Ao calibrar peso de stake, dois cortes são load-bearing** — tirar qualquer um já quebrou o
matcher em produção: valor **redondo** (50/100/250/800) não é digital, é valor comum; e
`valores.size === 1` separa "este valor É minha assinatura única" de "é um dos vários que
aposto". → [o caso](docs/CASOS.md#os-dois-cortes-que-já-quebraram-o-matcher-em-produção)

> **Assinatura tem ERA** — o mesmo valor troca de dono entre meses. Backtest in-sample pune
> o acerto de hoje com bilhete velho; use holdout **temporal** para qualquer regra que
> aprenda da base. → [o caso](docs/CASOS.md#assinatura-tem-era)

---

## ⚠️ REGRA DE UI / MARCA OBRIGATÓRIA (antes de criar QUALQUER visual novo)

> **Motivo: regra escrita sem hábito de conferir = pulada.** Esta seção é um checklist
> numerado, e não um texto, exatamente por isso.
> → [o caso](docs/CASOS.md#os-cards-de-kpi-com-formatador-caseiro--s83)

**Antes de escrever qualquer render de número, dinheiro, cor, tipografia ou componente visual, NESTA ordem:**

1. **Ler** `docs/UI_REFERENCE.md` (§5 = padrão monetário) e, se tocar na casca, `docs/SHELL_SPEC.md`. A bíblia de marca é [`../pack/CLAUDE.md`](../pack/CLAUDE.md); tokens em [`../pack/tokens/tokens.css`](../pack/tokens/tokens.css).
2. **Reusar helper existente, nunca criar formatador.** `grep` por `fmtPL`/`fmtR`/`moneyStake`/`.money` no arquivo e reusar. Todo R$ usa o componente `.money`; só muda as casas por contexto (ver `UI_REFERENCE §5`): **P/L → `fmtPL` (2 casas**, `R$` menor `--ink-soft`, cor SÓ no número, minus U+2212, zero neutro); **agregado/KPI/turnover/custo → `fmtR` (inteiro)**. **Nunca abreviar milhar (`k`/`M`) — barrado pelo `check-tokens §d`.** `.toFixed`/`.replace` só nas exceções documentadas (odd/USD), nunca em R$.
3. **Cor sempre de token** (`var(--…)`), nunca literal. `.money-sign`/sinal ficam neutros.
4. **Auto-auditar item a item contra §5 ANTES do commit** + rodar `node scripts/tokens/check-tokens.mjs`.
5. **Abrir a tela num navegador antes do commit.** `node --check` é **falso verde para tudo que vive dentro de template literal** — uma crase perdida num comentário derruba a página inteira e passa no check. Suba o `scripts/demo/servidor_demo.py` e renderize headless: medir a tela é o único gate que pega isso. → [o caso](docs/CASOS.md#a-crase-que-deixou-o-dash-em-branco--s296)

6. **Quem LÊ o número de volta da tela tem de conhecer o padrão que o imprimiu.** O item 2
   cobre a escrita; a metade que faltava é a leitura. Ordenação, filtro e qualquer código
   que reparseie o que `fmtR`/`fmtPL`/`fmtPct` renderizaram enfrenta duas armadilhas: o
   sinal negativo é **U+2212 (`−`)**, não hífen — `parseFloat` devolve `NaN`, que vira 0, e
   **todo valor negativo ordena como zero**; e `fmtR` imprime milhar **sem decimal**, então
   a regra de milhar decide pela **forma** do número (`^\d{1,3}(\.\d{3})+$`), nunca pelo que
   vem depois do ponto. Reuse `parseNum` (`dash/assets/js/app.js`) — não escreva um segundo
   parser. → [o caso](docs/CASOS.md#as-duas-armadilhas-de-reparsear-o-que-a-tela-imprimiu--s300)
7. **Coluna ordenável cujo texto não ordena sozinho leva `data-sort`.** `sortTable` lê o
   `dataset.sort` antes do `textContent`. Data em `dd/mm/aa` ordena pelo **dia do mês**;
   célula com chip/ícone carrega a letra do chip no `textContent`. Nos dois casos o valor
   canônico (ISO, nome limpo) vai no `data-sort` e o texto bonito fica na tela.

8. **O checklist valida o ÁTOMO, não a composição — confira a tela inteira depois dele.**
   Os itens 1–7 cobrem número, cor, tom, tamanho e componente. Não cobrem quantos cartões
   a tela tem nem onde mora cada controle. Componente novo passa item a item e ainda
   briga com a tela. Duas perguntas, sempre, depois do `/nova-ui`:
   - **Este controle tem irmão em outro lugar da mesma tela?** Se tem, é *uma* superfície
     só. Partida em dois, a de cima **sai do campo de visão** de quem mexe na de baixo, e
     **a tela passa a parecer que não tem o filtro que tem**. Antes de escrever markup que
     já existe, quebre o compartilhado em peças (`_grupoPeriodo` e cia., em `filters.js`) e
     componha; copiar cria dois Períodos que divergem no primeiro ajuste.
   - **Há dois estilos para o mesmo papel aqui?** É o sintoma barato de "fora do padrão", e
     ele aparece **mesmo quando uma das metades está certa** — o olho lê as duas como
     inconsistentes sem saber qual é qual. Resolva pela raiz: **exclua o estilo novo, reuse
     o existente e suba o existente** para o papel certo.
   → [o caso das duas](docs/CASOS.md#o-filtro-que-a-tela-já-tinha--s317)

9. **Recorte por DESFECHO não redefine a régua que mede a carteira.** Filtrar a tela por
   casa, esporte ou período é recortar carteira, e os KPIs seguem junto. Filtrar por
   resultado é outra natureza: `W` sozinho daria **Win Rate 100%** e ROI positivo —
   números certos pela conta e mentirosos pela leitura. Quem filtra desfecho corta a
   **tabela**; os KPIs leem o mesmo recorte **sem** esse corte (`apostasKpiRows`), e a
   tela **diz isso** enquanto o filtro está ligado. Sem o aviso, ler P/L positivo
   filtrando `L` parece defeito. Vale para qualquer tela que ofereça as duas coisas.

> Dúvida de qual convenção (tabela vs card)? Pergunte ao Feca — não invente uma terceira. Use `/nova-ui` para rodar este checklist guiado.

---

## Escada de Tinta — a cor do texto vem do PAPEL, não do espaço

> **Este defeito chega por USO, não por auditoria** — o lint não acusa e o olho acusa.
> → [o caso](docs/CASOS.md#o-cabeçalho-que-virou-textura--painel-de-contas)

**Três causas somam, e é o trio que se procura:** tom baixo, corpo minúsculo e tracking
largo em caixa alta. Junto costuma vir **inversão de hierarquia** — filho mais pesado que o
pai, e a varredura da lista passa a ler o dado errado.

A regra que faltava: **`--ink-mute` nunca teve piso de tamanho.** Ele é legítimo em 12px
sobre `--surface`; em 9,5px caixa alta sobre `--surface-2` deixa de ser texto e vira
textura.

**Contraste sempre medido sobre o FUNDO EFETIVO** — somando os overlays de
`rgba(255,255,255,…)`, não sobre o token de superfície que está no CSS. **É o overlay que
esconde o problema de quem mede pelo CSS.**

| Papel | Exemplo | Cor | Corpo mín. | Contraste mín. |
|---|---|---|---|---|
| Identidade / nome próprio | casa, tipster, operador, e-mail | `--ink` | 13px | 12:1 |
| Valor numérico | KPI, odd, saldo, P/L | `--ink` | 13px | 12:1 |
| Label / eyebrow / `thead` | CONTAS, PERÍODO, ESPORTE | `--ink-soft` | 9,5px | 4,5:1 |
| Metadado secundário | contador, unidade, timestamp | `--ink-mute` | 10px | 3:1 |
| Desabilitado / placeholder | input vazio, ícone off | `--ink-mute` | 12px | — |

Medido no tema escuro (o app é dark, sem toggle), sobre `--surface-2` com overlay:
`--ink` **14,7:1** · `--ink-soft` **6,3:1** · `--ink-mute` **3,0:1**.

**Faça**

- Um único elemento `--ink-mute` por linha ou cabeçalho. Se houver dois, um deles é
  conteúdo disfarçado de enfeite.
- Caixa alta + tracking só em **categoria**. Nome de marca vai em caixa própria — e aí o
  dado precisa chegar na caixa certa (`casaDisplay()` no `index.html`: title case **só**
  em quem vem sem informação de caixa; caixa mista é verbatim, senão mutila `BETesporte`,
  `VaideBet`, `KingPanda`).
- Abaixo de 11px: subir um degrau na escada e o peso para 500.

**Não faça**

- `--ink-mute` em texto abaixo de 10px, em qualquer superfície.
- Filho mais legível que o pai (e-mail em `--ink` dentro de grupo em `--ink-mute`).
- Resolver contraste com `#FFFFFF` — **a escala fecha em `--ink`**. "Mudar pra branco" se
  traduz, no sistema, como *subir um degrau na escada*.
- Compensar tom baixo com peso 700 em 9,5px: engorda o borrão, não corrige a leitura.

**Fundo sólido de acento pede tinta ESCURA, não branca.** A escada acima descreve tinta
sobre superfície escura; quando o fundo vira o próprio acento, ela se inverte e o reflexo
"texto claro sobre cor" reprova. Medido: `#FFFFFF` sobre `--accent` dá **3,36:1** e
`--ink` dá 2,78:1 — os dois abaixo do mínimo de texto pequeno. `var(--bg)` sobre
`--accent` dá **5,8:1**, e sobre `--warn` dá **8,7:1**. Vale para qualquer pill, badge ou
botão de estado ligado. Os `.pend-badge`/`.open-badge` da sidebar usam `#fff`/`#241a02`
literais e são **desvio conhecido, anterior a esta regra** — não copiar de lá.

**`opacity` não é um degrau da escada — é um multiplicador.** Aplicada sobre um tom já
apagado ela derruba o contraste efetivo sem aparecer em nenhum grep de cor: `--ink-mute`
com `opacity:.55` dava ~1,9:1, e `--ink-soft` com `opacity:.7` caía para ~4,4:1, logo
abaixo do mínimo do papel. Se o texto precisa ser mais discreto, **desça um degrau na
escada**, não aplique opacidade.

**Duas exceções, ambas comentadas no CSS para não virarem precedente:**

- **Ícone não é texto.** Caret, seta e o "i" de ajuda (`.operador-caret`, `.casa-arrow`,
  `.sb-op-caret`, `.metric-info`) ficam abaixo do piso, em `--ink-mute`, por desenho.
- **`opacity` como ESTADO é legítima** — `.act-btn.off`, `.update-btn.is-loading`,
  `.host-refresh.is-loading`. Ali ela sinaliza desabilitado/carregando, não hierarquia.

> **A varredura precisa de três critérios, não um.** O grep de `--ink-mute` por px
> literal é cego a tamanho vindo de token (`var(--text-nano)` = 9px), a `opacity` sobre
> tom apagado, e ao papel errado num corpo que passa no piso (label de legenda em 11px
> `--ink-mute` reprova por ser label, não por ser pequeno). Um lint que resolva só o
> primeiro critério dá falso verde.

---

## Teste verde não é teste que detecta

Gate novo só vale depois de provado por **mutação**: quebre o código de propósito e
confira que o teste falha. Verde sem essa prova não prova nada.

Dois modos de falso verde, ambos medidos ([os casos](docs/CASOS.md#o-teste-que-reimplementava-o-código--s286)):

1. **O teste reimplementa o código sob teste.** Recorte o código real do arquivo; nunca
   copie o trecho para o teste.
2. **O dado sintético não exerce a regra.** Dado pequeno demais nunca atinge o corte; sem
   empate, o desempate não decide nada; se o item "só da base" também está no MASTER, a
   união não foi provada. E o sort do V8 é **estável** — um empate pode "acertar" sem regra
   nenhuma, se a ordem natural já for a esperada.

Quando uma mutação escapa, o defeito quase sempre está no teste, não no código.

**Mutação inócua existe.** Se o código segue correto sem aquela linha, ela é redundante
e não é buraco de teste. Registre a diferença em vez de inventar asserção para ela.

**Diga o que o teste NÃO cobre**, no cabeçalho do arquivo — senão o verde vira promessa
falsa. DOM dublado sempre "clica" e nunca rola de verdade.

---

## Linha bem-formada pode ser de OUTRO bilhete. Confira a procedência, não só a forma.

A IA lê o lote em chunks de 6 bilhetes e **copia trecho do vizinho**. O resultado não
parece defeito: separador certo, confronto bem formado, nada proibido — **passa em
`checar_descricao` sem um arranhão, e a cobertura fecha**.
→ [o caso](docs/CASOS.md#a-descrição-que-era-do-vizinho--s302)

**O financeiro TAMBÉM viaja — e aí é pior, porque o P/L continua certo.** "Stake, odd e
resultado são cópia" era **observação medida, não garantia**: a stake pode vir do vizinho, e
como em `W` a odd é derivada (`Retorno ÷ Stake`), ela é recalculada **sobre a stake errada**
e o P/L fecha exato. Descrição certa, código certo, resultado certo, P/L certo — **erram só
turnover, ROI e a assinatura de stake do matcher**, e o bilhete perde o tipster.
→ [o caso](docs/CASOS.md#a-stake-que-era-do-vizinho-com-o-pl-intacto--pinnacle-s311)

Por isso a **stake saiu da mão da IA** (`repository.corrigir_stake_tsv`, irmão do
`anexar_sistema_tsv`): a coluna 8 vem do `Stake:` do bloco daquele código, e a odd de W é
refeita junto quando o bloco traz o `P/L` — determinístico, sem modelo no caminho. Vale só
onde há bloco (casas de API); **print continua 100% por conta da IA**. Bloco com dois
valores de `Stake:` é ambíguo e não autoriza escrita nenhuma. Gate:
`tests/test_stake_determinista.py`, autorizado por medição na sombra.
→ [as medições](docs/CASOS.md#as-medições-que-autorizaram-o-gate-de-stake)

> O gate copia o bloco **fielmente**, inclusive quando o bloco está errado na origem (a
> KTO manda `Stake: 1,00`). Isso é defeito de captura, não de tradução — e a correção
> humana numa linha já resolvida sobrevive, porque o UPSERT congela stake em `resolvida`.

A conferência é possível porque **a tradução não inventa NOME**: ela traduz rótulo,
canoniza separador e escolhe categoria, mas time, jogador e competição são cópia. Então
todo nome próprio e todo DECIMAL da descrição têm de existir no bloco cru **daquele
código** (`descricao_check.checar_fidelidade`, sem IA, microssegundos).

**A correção é perguntar de novo, sozinho.** `_garantir_fidelidade` devolve o bloco
suspeito ao modelo isolado — bilhete sem vizinho no chunk não tem de quem copiar — e
**só aceita a resposta nova se ELA passar no gate**. Nunca troca uma linha que passa por
outra que passa: isso seria o ruído de estilo que o congelamento do UPSERT existe para
barrar.

> **Recapturar a casa NÃO conserta linha assim.** O `ON CONFLICT` nunca atualiza
> `esporte`/`aposta`/`descricao` fora de `origem='sync'` — **nem com a linha `aberta`**,
> ao contrário de odd/data/stake. **A IA pode ler o mesmo bilhete várias vezes na MESMA
> extração e acertar só nas últimas — o banco fica com a primeira.** Linha já gravada errada
> sai por edição na grade ou por script.
> → [o caso](docs/CASOS.md#a-ia-que-acertou-nas-duas-últimas-e-o-banco-ficou-com-a-primeira--0001941)

Três tolerâncias do gate são load-bearing, todas nascidas de falso positivo medido:
acento agudo tipográfico (`St Patrick´s` × `St Patrick's`), hífen com espaços
(`Ararat - Armênia` × `Ararat-Armênia`) e plural (`Tiro de meta` × `Tiros de Meta`).
E **só o DECIMAL conta como linha da aposta**: a conferência de número é por substring,
e inteiro curto é achado dentro de qualquer odd (`2` vive dentro de `2,05`).

---

## ⚠️ REGRA DE PROPAGAÇÃO OBRIGATÓRIA

**Toda vez que uma categoria for criada, renomeada ou removida do `MASTER_APOSTAS_2026.md`, os seguintes arquivos DEVEM ser atualizados na mesma sessão, sem exceção:**

| O que atualizar | Onde | O quê |
|---|---|---|
| Tabela de categorias | `MASTER_APOSTAS_2026.md §3` | Adicionar / renomear / remover linha |
| Sinônimos | `MASTER_APOSTAS_2026.md §4` | Adicionar bloco de sinônimos |
| Regras por categoria | `MASTER_APOSTAS_2026.md §5` | Documentar casos especiais |
| Regras por esporte | `MASTER_APOSTAS_2026.md §6` | Atualizar se o esporte for afetado |
| Validação final | `MASTER_APOSTAS_2026.md §9` | Adicionar checagem da nova categoria |
| **Mapa de mercados — só casas afetadas** | `casas/CASA_*.md §9` | **Apenas** as casas cujo §9 já referencia a categoria/rótulo afetado. Buscar com `grep -rl "<categoria>" casas/`. Sob a camada fina, o §9 lista só mercados confirmados — uma categoria nunca vista por uma casa **não** aparece lá e **não** precisa de update. |
| Template de descrição | `MASTER_DESCRICAO_2026.md §12 ou §13` | Adicionar template se o formato for novo |
| Prioridade semântica | `MASTER_APOSTAS_2026.md §7` | Atualizar se houver risco de confusão com Player Props / Outros |

> Os menus de esporte e mercado do editor de tipster **não** entram nesta lista: eles leem
> o MASTER em tempo de execução (`/taxonomia`). Categoria criada aparece lá sozinha.

> **Motivo:** categoria criada no MASTER e mapa de casa apontando para `Outros ⚠️`. A
> **causa raiz era a DUPLICAÇÃO** — cada casa reescrevia a lista inteira de categorias.
> Desde a camada fina, o §9 lista só o que a casa confirma, e a superfície de propagação
> encolheu para as casas realmente afetadas.
> → [o caso](docs/CASOS.md#as-três-categorias-que-ficaram-apontando-para-outros--13062026)

**Checklist rápido ao criar/renomear/remover uma categoria:**

- [ ] `MASTER_APOSTAS §3` (tabela) atualizado
- [ ] `MASTER_APOSTAS §4` (sinônimos) atualizado
- [ ] `MASTER_APOSTAS §9` (validação) atualizado
- [ ] `MASTER_APOSTAS §7` (prioridade semântica) atualizado se houver risco de confusão
- [ ] `MASTER_DESCRICAO §12/§13` atualizado se o formato de descrição for novo
- [ ] `grep -rl "<categoria afetada>" casas/` → atualizar **só** os §9 que aparecerem (renomear/remover); novo nome quase nunca exige update de casa
- [ ] Rodar `/audit-casas` para confirmar que nenhum §9 ficou apontando para categoria inexistente

> Dica: use `/propagar-categoria` para automatizar este checklist.

---

## Convenções de output

> **Fonte canônica:** `global/MASTER_OUTPUT_2026.md` (TAB, 10 colunas, 11ª coluna interna `Código`, decimal vírgula, códigos de resultado). O resumo abaixo é um **espelho operacional** — ao mudar o formato, mude no MASTER primeiro.

- Separador: **TAB real** (U+0009) — nunca espaços, ponto-e-vírgula ou pipe
- **10 colunas para a planilha do usuário**: `Data | Esporte | Tipster | Casa | Parceiro | Aposta | Descrição | Stake | Odd | Resultado`
- **11ª coluna interna** (`Código`): ID/código do bilhete visível no print — nunca vai para a planilha do usuário, só para o banco de dados. A AI sempre retorna essa coluna; se não houver ID visível, a célula fica vazia.
- **12ª coluna interna** (`Sistema`, formato `3x Duplas`): estrutura de bilhete de sistema. **A IA NÃO a emite** — o backend a anexa depois de responder (`anexar_sistema_tsv`), lendo o `Tipo: SISTEMA …` do texto do robô e casando pelo código. Vira `sistema`/`sistema_linhas` no banco; ausente = bilhete de linha única. Existe porque a odd de sistema é a **média das linhas** (`MASTER_RESULTADO §7.3`) e nada mais no banco distinguia um `3 x Duplas` da tripla das mesmas seleções — a descrição dos dois é idêntica.
- Decimal: **vírgula** (`2,35`) — nunca ponto
- Resultado: `W · L · V · HW · HL` — ou **vazio** quando a aposta está aberta (não liquidada; ver `MASTER_OUTPUT §13.1` / `MASTER_RESULTADO §1.1`)
- Odd sem limite de casas decimais (planilha usa a precisão completa)

---

## Casa que exporta HISTÓRICO só some com corte. Apagar do banco não basta.

A captura varre o horizonte DELA (o `bda_inject` faz 3 anos por desenho: `DIAS_HISTORICO
= 1095`, e o painel só é obedecido quando pede MAIS). **Linha apagada volta inteira na
varredura seguinte, sem erro nenhum.**

A régua é `main._CORTE_HISTORICO`, mapa **(dono, casa) → data** aplicado no `/extrair`
**antes da IA** — o bloco cortado não paga leitura nem chega ao `/salvar`. Nunca na
extensão, que é compartilhada entre casas espelho e vale para todo dono. Manda a data do
**evento** (a da coluna Data) e bloco sem data legível **FICA**: esconder bilhete é o erro
caro. **E o corte sobe e se confere no ar ANTES de apagar** — na ordem inversa, uma
captura na janela entre as duas metades desfaz a exclusão.
→ [o caso](docs/CASOS.md#as-298-de-2025-que-voltariam-na-captura-seguinte-s344)

---

## Regras de deduplicação (sistema)

O sistema determina se dois bilhetes são iguais ou diferentes na seguinte ordem de prioridade:

| Situação | Comportamento |
|---|---|
| **ID/código do bilhete disponível e igual** | Mesmo bilhete — UPSERT (atualiza resultado/estado) |
| **ID/código do bilhete disponível e diferente** | Bilhetes distintos — sempre INSERT (mesmo conteúdo idêntico) |
| **Sem ID, conteúdo diferente** (odd, descrição, etc.) | Bilhetes distintos — INSERT |
| **Sem ID, conteúdo idêntico, mesmo lote** | Possível sobreposição de prints — salva **ambas** as linhas (assinaturas distintas via `_counter`: `B`, `B\|2`, …) + aviso amarelo ao usuário; delete se for sobreposição real |
| **Sem ID, conteúdo idêntico, lotes diferentes** | Re-processamento do mesmo bilhete — UPSERT silencioso |

**Limitação:** onde o ID não é visível no print, dois bilhetes 100% idênticos não têm como ser distinguidos — é a 4ª linha da tabela, e ela vale por desenho: salvar ambos e avisar.

**Fonte canônica (implementação):** `app/repository.py` — `_assinatura()` e `upsert_bilhetes()`. Esta tabela documenta o comportamento do código; ao mudar a lógica de dedup, **o código é a verdade** (atualize a tabela depois).

### Linha sem código, em casa que TEM código, é órfã. E órfã vira fantasma.

Linha sem código **nunca dedupa**. Ao liquidar, o mesmo bilhete volta com código e entra
como linha NOVA — a velha fica `aberta` para sempre, sem erro e sem aviso. **A pista é um
`AGUARDANDO RESULTADO` na grade + stake "em aberto" na Caixa num dia em que a casa não tem
pendente nenhuma.** → [o caso](docs/CASOS.md#a-órfã-que-virou-fantasma--a-múltipla-do-falkirk-betnacional-s327)

Três lugares seguram isso, e cada um cobre o que o outro não vê:

- **`_reconciliar_orfas` (`app/main.py`)** — na extração. **Adota** (dá à órfã o código do
  bloco faltante de que ela é fiel, por `checar_fidelidade`, só com par único **nos dois
  sentidos**) ou **descarta** (sobrou órfã e nenhum bilhete está sem linha própria → é
  cópia). `conferir_cobertura` sozinha não resolve: ela cobra QUANTIDADE por código e a
  repescagem só ACRESCENTA.
- **Migração B do UPSERT** — no banco. A órfã já gravada é adotada quando o bilhete volta
  com código. **Compare a odd pela régua do sistema** (`chave_orfa` → `_norm_odd`): em
  string crua, `14` não é `14,00` e a adoção falha.
- **NO-OP obrigatório** onde a coluna 11 vazia é **legítima**: casa sem marcador (prints,
  texto colado) e texto com qualquer `[Código: ]` vazio — é o que a bet365 manda quando o
  detalhe não chegou, e descartar ali apagaria bilhete real.

### Código lido de IMAGEM não é código. Marque a procedência.

O `codigo_bilhete` entra na assinatura, então um dígito trocado é um bilhete NOVO. Mas ele
tem duas origens de confiabilidade oposta: da captura vem do `[Código: …]`, exato; do PRINT
vem da IA lendo o card, e **em id longo ela erra quase sempre, diferente a cada leitura**
(medido: 2 de 55 por print, contra 100% por captura).
→ [o caso](docs/CASOS.md#o-mesmo-bilhete-com-5-códigos--blaze-s338)

**A coluna `codigo_ocr` carrega essa procedência**, e quem decide é o servidor: o
`/extrair` sabe se o lote tinha imagem, o front só transporta o flag até o `/salvar`. No
`ON CONFLICT` a fórmula é um **AND das duas pontas** — a confiança só DESCE. Uma leitura
confiável limpa o código para sempre; nenhum print o rebaixa de volta.

Com ela, a **Migração B'** adota a linha quando o mesmo bilhete volta pela captura com o
código verdadeiro. Duas travas que a Migração B não precisa ter, porque aqui o candidato
**carrega um código próprio** e adotar o errado não duplica, **sequestra** a identidade de
outro bilhete: candidato **único**, e índice montado só quando o lote que chega é confiável
(print não adota print). O que já está duplicado sai por
`scripts/reparar_duplicatas_codigo_ocr.py`, com ensaio por padrão e olho humano.

> **Casa nova na captura = o histórico dela por print vira dívida.** Antes de ligar, meça o
> comprimento dos códigos já gravados: variar entre linhas da MESMA casa é a assinatura do
> defeito, e o backfill de `codigo_ocr` só é legítimo com prova de DATA (a captura não
> existia), nunca por palpite de formato.

### Fonte determinística manda; extração por IA congela.

O UPSERT **congela** `odd`, `data`, `stake`, `esporte`, `aposta` e `descricao` assim que a
aposta resolve. Isso protege a extração por IA: a re-leitura é ruidosa e sobrescrever seria
pior que manter. **Exceção: `origem='sync'`** (fonte determinística — hoje só o
`/polymarket/sync`, que lê a API on-chain). Para ela esses campos são sempre refrescados.

**Por que a exceção existe:** `resultado` **nunca foi congelado**. Com fonte determinística
isso deixava a linha **meio atualizada** — resultado novo, odd velha — e virava lucro
fantasma. **Blindar metade dos campos é pior que blindar todos ou nenhum.**
→ [o caso](docs/CASOS.md#blindar-metade-dos-campos-28-linhas-de-lucro-fantasma)

Contrapartida: edição manual de data/stake/odd/esporte/categoria/descrição numa casa
sincronizada **não sobrevive** ao sync. O `tipster` sobrevive.

**E o congelamento só começa quando a linha RESOLVE.** Enquanto `extraction_state =
'aberta'`, `data`, `odd` e `stake` são refrescados por qualquer reenvio, de qualquer
origem — e quem escreve por robô reenvia a cada marcação. Então **editar esses campos à mão
no dashboard antes da liquidação é desfeito sem aviso**: a tela aceita, salva, e o próximo
reenvio devolve o valor antigo. Corrija NA FONTE (no bot, `/ajustar #N <data>`, que reenvia
e depois faz `PATCH /bilhetes/{id}`) ou espere a liquidação. A edição à mão vale sozinha em
linha já resolvida e em casa não sincronizada.

> **Método:** melhorar o cálculo não basta — confira se ele **chega ao banco**. Depois de
> corrigir qualquer fórmula, diffe `banco × coletor` linha a linha.

**Fonte canônica:** `app/repository.py` — `_ORIGEM_AUTORITATIVA` e o `ON CONFLICT` de
`upsert_bilhetes()`.

### Mexeu em `casa` ou `parceiro` de um bilhete? Recalcule a assinatura.

`casa` e `parceiro` entram no hash de `_assinatura` (com ou sem código de bilhete). Trocar
qualquer um dos dois sem recalcular deixa a linha com o hash antigo: a próxima captura
gera uma assinatura nova, não colide com nada, o UPSERT não dedupa e **o histórico
duplica inteiro**. Vale para renomear conta, **mover conta de casa**, unificar casa,
mover bilhete e backfill. → [o caso](docs/CASOS.md#a-assinatura-que-ficou-para-trás--s198-e-s312)

Quem já faz certo: `editar_parceiro()` (nome e/ou casa; `renomear_parceiro()` é wrapper dele),
`atualizar_bilhete()` (via `_assinatura_pos_edicao`), `scripts/unificar_casas.py` e
`scripts/reparar_orfaos_parceiro.py`. Reuse o laço de `_counter` deles — duas linhas de
conteúdo idêntico precisam escalar, não colidir.

**Os dois campos mudam JUNTOS, numa transação só.** O modal de edição de conta oferece
nome e casa na mesma tela, e gravar um de cada vez deixaria uma assinatura intermediária
que não corresponde a bilhete nenhum. Pelo mesmo motivo a colisão de nome é conferida na
casa de **destino**, nunca na de origem.

`casa` é **texto** em `bilhetes`, `parceiros`, `casas_meta`, `casa_config`, `correcoes`,
`uso_tokens` e `tipsters.casas`: cada grafia é uma casa **diferente** no sistema. Ao criar
conta, `repository.casa_canonica()` reusa a grafia que já existe; casa nova entra
**verbatim** (nunca title-casear — mutilar nome cria conta paralela).

---

## Caixa Inteligente: o saldo é DERIVADO, e o corte é o que o torna verdadeiro

A Caixa responde "quanto esta conta deveria ter na casa hoje" e confronta com o que a
casa mostra. Nada de saldo é persistido — ele é derivado, como o `calcular_pl`:

    banca      = saldo inicial + abertas no corte + depósitos − saques ± ajustes + P/L
    em aberto  = Σ stake das apostas elegíveis ainda não liquidadas
    disponível = banca − em aberto        ← é ESTE que a casa mostra na tela

**Toda aposta mexe no saldo DUAS vezes:** −stake quando é feita, +retorno quando
liquida. É daí que sai tudo o que segue.

**`bilhetes.data` é a data do EVENTO, não a da aposta.** Aposta feita ontem para um
jogo da próxima semana tem `data` depois do corte, e mesmo assim o stake dela já saiu
da conta. Qualquer conta de dinheiro que trate `data` como data da aposta erra —
descontando o stake duas vezes e fazendo a conta nascer com divergência.

**O corte não é um filtro de data, é o instante em que o saldo foi lido.** Por isso
`abertas_corte` grava os ids das apostas abertas naquele instante: o stake delas saiu
ANTES da leitura (logo não está no saldo informado) e volta INTEIRO ao liquidar.
Regra em `repository._caixa_abertas_ids`, um lugar só:

- **corte = hoje** (o caminho que a tela recomenda) → toda aposta aberta entra. Se
  está aberta agora, o stake saiu antes de agora. É exato.
- **corte no passado** → não dá para reconstruir; entra o que provadamente já existia
  (evento anterior ao corte, ou linha que o Sharpen já tinha, por `criado_em`). É um
  piso, não o exato.
- **script que recalcula depois** passa `ate` = o instante da ativação. Sem isso ele
  adota aposta feita mais tarde no mesmo dia e **infla a projeção**.
  → [o caso](docs/CASOS.md#o-script-que-inflou-a-projeção-em-r-10477)

**"Toda aposta aberta entra" só vale para a aposta que o Sharpen JÁ CONHECE.**
`abertas_corte` é um retrato do que o **banco** tinha naquele segundo, não do que a
**casa** tinha — e o dinheiro sai da conta na casa. Entre a captura começar e o
`/salvar` gravar há **~1 minuto**: ligar a Caixa dentro dessa janela grava lista
**vazia**, e o Ajuste da conferência seguinte **cimenta o erro com cara de número
conferido**. → [o caso](docs/CASOS.md#a-caixa-ligada-no-meio-da-captura--betnacional-s327)
Hoje o `/salvar` conserta sozinho: aposta que **nasce** aberta e cuja `criado_em`
antecede a ativação entra no `abertas_corte` (`_caixa_adotar_abertas_tardias`) — não é
heurística, a aposta não pode ter liquidado e desliquidado. A lista **só cresce**, e
`criado_em` nulo ou sem fuso fica de fora.

> Sintoma para reconhecer isto noutro campo: um retrato tirado de uma fonte que ainda
> está sendo preenchida. Vale para todo campo que congela estado no instante do clique —
> se a escrita que o alimenta é assíncrona, o clique pode chegar antes dela.

**A conferência REGISTRA, não absorve.** Ela grava o `projetado` daquele momento e
nunca o recalcula: a projeção de hoje já inclui aposta que não existia lá atrás, e
recalcular reescreveria o passado, apagando a divergência que foi medida. O box
continua acusando até alguém lançar o que faltava ou pedir o ajuste nomeado.

**Conta sem caixa não vira zero:** entra como "—", fica fora de toda soma, e a tela
diz quantas faltam. Total que engole conta desconhecida mente com cara de exatidão.

> **Número que parece contradizer o vizinho na mesma tela é defeito, mesmo estando
> certo.** A saída não é mudar número nenhum: é a tela **dizer o corte** (`Resultado ·
> desde <data>`) e o que ficou de fora.
> → [o caso](docs/CASOS.md#os-dois-números-certos-que-pareciam-defeito)

**Fonte canônica:** `app/repository.py` (`_caixa_projetar`, `_caixa_abertas_ids`,
`caixa_lancar`, `caixa_editar_mov`, `caixa_visao`) e `caixa_mov` no `database.py`.
Máscara do dinheiro: `fmtSaldo` (2 casas, sem cor) — `UI_REFERENCE §5.1`.

---

## O asyncpg não converte tipo: o argumento vai no TIPO DA COLUNA

`NUMERIC` exige `Decimal` (float levanta `DataError`), `DATE` exige `datetime.date`
(string levanta `'str' object has no attribute 'toordinal'`), `INTEGER[]` exige
`list[int]`. O erro nasce **dentro do driver**, antes de qualquer SQL rodar, e vira
500 na rota. Foi assim que o "Ativar" da Caixa não fez nada **duas vezes seguidas**,
com dois argumentos diferentes do mesmo INSERT.

Três coisas que a segunda vez ensinou:

- **`Decimal(str(v))`, nunca `Decimal(v)`** — o float carrega lixo binário.
- **Sem `::date` no SQL.** Com o cast, o tipo do parâmetro fica ambíguo; sem ele vem
  da coluna e não há dúvida sobre o que o driver espera.
- **Gate por LISTA, não por lembrança.** Olhar um argumento por vez foi o que deixou o
  segundo passar; `test_cada_argumento_do_insert_vai_no_tipo_da_coluna` percorre os
  oito de uma vez e quebra se o INSERT mudar de forma.

> **E o erro precisa aparecer onde o clique foi dado.** O 500 ia para o `#status-msg`
> da barra de captura, longe do modal: da cadeira de quem clicou, "não acontece nada".
> Falha de servidor aparece no formulário que falhou.
>
> ⚠️ **`display:flex` vence o atributo `hidden`** (que só vale pela folha do agente), e
> a faixa de erro nascia vermelha e vazia. Todo elemento escondido por `hidden` que
> tenha `display` próprio precisa de `[hidden] { display: none }` explícito.

---

## Excluir dado: mova para tabela isolada, nunca soft-delete

Exclusão destrutiva **move** as linhas para uma tabela que mais nada no sistema lê
(hoje `lixeira_contas`, alimentada pelo botão Excluir do Painel de Contas, retenção
de 7 dias com purga preguiçosa). Nunca marque `excluido = TRUE` na tabela de origem.

**Por quê:** soft-delete em `bilhetes` obrigaria a filtrar em dezenas de queries
espalhadas (dashboard, KPIs, dedup, export, P/L). Um esquecimento vira lucro
fantasma, a mesma família do UPSERT meio-atualizado descrito acima. Tabela separada
tem acoplamento zero por construção.

Duas regras de forma:

- **O snapshot e o DELETE são a MESMA operação** (`DELETE ... RETURNING to_jsonb(b.*)`).
  Ler antes e apagar depois abre janela para gravar uma lixeira que não corresponde
  ao que saiu.
- **Snapshot em JSONB, nunca tabela-espelho.** `bilhetes` ganha coluna via `ALTER TABLE`
  de tempos em tempos, e um espelho pararia de copiar a coluna nova em silêncio.

Restaurar casa o snapshot com as colunas que a tabela tem **hoje** e usa `ON CONFLICT
DO NOTHING`: entre excluir e restaurar o espaço pode ter sido reocupado, e **dado novo
manda**.

**Rota destrutiva reconfere a confirmação no servidor.** A UI trava o botão até o nome
exato ser digitado, mas isso é conveniência, não segurança: um `DELETE` disparado por
engano (histórico do navegador, script, curl) não pode apagar histórico.

**Fonte canônica:** `app/repository.py` (`excluir_parceiro`, `LIXEIRA_DIAS`) e
`scripts/restaurar_conta_lixeira.py`.

---

## API externa por item = latência E falha multiplicadas. Peça a FAIXA.

Duas coisas escalam juntas quando se chama uma API externa em laço, e a segunda é a que
morde: a **latência** (cresce com o histórico, sem teto) e a **probabilidade de falha** —
N chamadas são N chances de derrubar o processo, cada uma carregando o backoff do retry.

**Antes de otimizar o laço, procure o endpoint de faixa.** A pergunta certa quase nunca é
"como paralelizo N chamadas?", e sim "por que são N?".
→ [o caso: 113 chamadas ao BCB](docs/CASOS.md#113-chamadas-ao-banco-central--s247)

**Dado histórico é imutável — cacheie entre requisições.** Cotação de dia passado nunca
muda: o mapa é de módulo (`polymarket._PTAX_MAPA`) e o 2º sync não gasta rede nenhuma.
Vale para qualquer dado datado e fechado; não vale para saldo, preço ou posição aberta.

**Engolir a exceção transforma falha de rede em dado ausente.** **Se o chamador precisa
distinguir "não existe" de "a fonte caiu", o `except` não pode achatar os dois** — senão o
laço trata timeout como feriado e só derruba tudo no fim.
→ [o caso](docs/CASOS.md#o-except-que-achatava-dois-casos)

> **Trocar a fonte de um número exige provar que o número não mudou** — comparando valor a
> valor, em todas as datas. Sem isso o re-sync mexe em stake já gravado: `origem='sync'` é
> `_ORIGEM_AUTORITATIVA` e refresca `stake`/`odd`/`data` mesmo em bilhete resolvido. E a
> fonte nova tem de repetir as escolhas de desempate da velha (o BCB republica alguns dias
> com **dois** boletins; o mapa mantém o `setdefault` de propósito).
> → [o caso](docs/CASOS.md#a-conferência-antes-de-trocar-a-fonte)

---

## Regra de cashout (planilha-compatível)

> **Fonte canônica:** `global/MASTER_RESULTADO_2026.md §5.1.2` (cashout = stake → V) e `§5.6` (cashout ≠ stake → W), com resumo em `MASTER_OUTPUT_2026.md §14`. **Mudou? Mude no MASTER, nunca aqui.**

Resumo: cashout **≠** stake (maior **ou** menor) → **W**, `Odd = Cashout ÷ Stake`. Cashout **=** stake, void ou cancelada → **V**, odd exibida no bilhete.
