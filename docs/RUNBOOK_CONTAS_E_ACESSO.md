# RUNBOOK — contas de usuário, acesso e o bot de tipster

> **Procedimento, não regra de código.** Saiu do [`CLAUDE.md`](../CLAUDE.md) na s358, quando
> ele passou de 72 KB com teto de 65: o que se lê **ao fazer** mora aqui; o que se obedece
> **ao escrever código** ficou lá. Nada foi cortado no caminho.
>
> Estado atual → [`STATUS.md`](../STATUS.md) · o que está aberto →
> [`BACKLOG.md`](../BACKLOG.md) · regras vinculantes → [`CLAUDE.md`](../CLAUDE.md).

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
> `dono` é o username. → [o caso](CASOS.md#a-marca-não-é-o-username--fleury--flurray)

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
→ [o caso](CASOS.md#a-senha-simplesmente-não-era-aquela)

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
> → [o caso](CASOS.md#o-token-subiu-antes-dos-botões)

**Dado dessincronizado se conserta com `/ressincronizar [AAAA-MM]`** no apoio: o bot
reempurra ao Sharpen o que já está no storage dele. Seguro de repetir (UPSERT por código,
vazio nunca rebaixa). Deixa de fora anulado e bilhete **sem casa** — linha sem casa nasce
invisível no Painel de Contas e reenvio não conserta, porque a casa entra na assinatura.

---

