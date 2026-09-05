# GUIA — pôr um tipster novo no ar (sharpen-bot)

> **Uso interno.** Isto saiu da página pública `/bot` de propósito (decisão do Feca,
> 04/09/2026): lá vive o manual do tipster — dia a dia, comandos, avisos. Aqui fica o
> que só quem opera o sistema faz.
>
> A página pública é `app/static/bot.html`, servida em `sharpen.bet/bot`.

Os oito passos abaixo são o que as sessões 316 e 317 mostraram serem necessários,
com o Soh Props - Vip (6º tenant). Dois deles já custaram bilhete em produção e
estão marcados.

---

## 1. Aprovar a conta

O tipster se cadastra sozinho em `sharpen.bet`. Em `/admin`, o status vai para **ativo**.

⚠️ O **`dono` é o USERNAME do cadastro**, nunca o nome de marca. Os dois divergem com
frequência (`Fleury`/`Flurray`, `PassaTips VIP`/`passapano`) e o isolamento por `dono`
falha **em silêncio**: import feito sob o nome errado não dá erro nenhum, só entrega
tela vazia para o usuário certo. Confira na tabela `usuarios`.

## 2. Ligar o bot

Ainda no `/admin`, o botão **Ligar bot** naquele usuário.

São **três condições, todas obrigatórias** (`auth.dono_do_bot`): o token confere, o dono
está `ativo` e o dono tem `bot_habilitado`. A terceira é o que impede o token de virar
chave-mestra.

⚠️ Sem ela, **toda escrita do robô toma 401** — e o sintoma engana: o canal mostra ✅/❌
e a planilha não acompanha, sem erro nenhum. Aconteceu na s276 com três tenants.

## 3. Criar os dois grupos

Um **grupo de apoio** (onde o tipster posta e os comandos são digitados) e o **canal
oficial** (onde os seguidores leem).

## 4. Adicionar o `@sharpenbetbot` nos dois

No canal ele precisa ser **administrador**, com `can_post_messages` **e**
`can_edit_messages` — é a edição que atualiza o post quando o resultado é marcado.

## 5. Pegar os ids — e conferir os dois

```bash
getChat(<id>)                       # existe? é o tipo certo?
getChatMember(<id>, <id do bot>)    # no canal: status e can_post_messages
```

⚠️ **Grupo que vira supergrupo TROCA de id** (s316). O número antigo para de funcionar e
o roteamento do bot compara `msg.chat.id` com o `apoioId` — com o id velho o tenant fica
**surdo**: ninguém recebe erro, o tipster posta e nada acontece.

Para achar o id novo **sem `getUpdates`** (que briga com o polling em produção), o próprio
Telegram devolve no erro:

```
sendChatAction(<id velho>)  →  parameters.migrate_to_chat_id
```

`sendChatAction` é a sonda certa porque **não publica nada** — grupo real não tem desfazer.

⚠️ `chat not found` tem DUAS causas com consertos opostos: id inexistente ou **bot fora do
chat**. O que separa é a presença do `migrate_to_chat_id`. Antes de suspeitar do id, prove
que o token que você está sondando é o mesmo do Railway (compare por fingerprint, sem
imprimir o segredo).

## 6. Cadastrar o tenant

Bloco em `src/config.js` + as env vars no Railway (serviço `sharpen-bot`):

```
<XX>_APOIO_ID · <XX>_DESTINO_ID · <XX>_TIPSTER_IDS · <XX>_SHARPEN_USER · <XX>_MODO_TESTE
```

Nada de senha: a autenticação é o `SHARPEN_BOT_TOKEN` (um só, para todos) mais o header
`X-Sharpen-Dono`.

⚠️ **Tenant novo mexe em TRÊS lugares, não dois** (s316). Além do `config.js` e do
`src/perfis/<perfil>.js`, o **registro `PERFIS` do `index.js`** precisa da linha. O guard de
boot é fail-closed (`process.exit(1)`) e com `restartPolicyType = ALWAYS` isso vira
**crash-loop**: o bot inteiro fora do ar, não só o tenant novo. Hoje há teste para isso.

⚠️ **A API do Railway dá timeout.** Sempre **releia** depois de gravar — um `set` que
parece ter passado pode não ter.

## 7. Semear o contador

Se o histórico dele já foi importado, a numeração precisa **continuar de onde parou**.

O código entra na assinatura (`ID|casa|parceiro|codigo`), então um bilhete novo com número
já usado é tratado pelo UPSERT como o **mesmo bilhete**: o congelamento mantém descrição,
odd e stake da linha antiga e "vazio nunca rebaixa" mantém o resultado. **A aposta do dia é
absorvida — sem erro, sem aviso, sem linha nova.** Foi a s276.

```sql
select max((substring(codigo_bilhete from '-(\d+)$'))::int)
from bilhetes where dono = '<user>' and codigo_bilhete ~ '^<XX>\d{6}-\d+$';
```

A semente vai no `index.js`, idempotente (só roda enquanto o mês está zerado).

## 8. Primeiro dia em modo teste

`<XX>_MODO_TESTE=1` publica **no apoio** em vez do canal. Confira o formato do post antes
de os seguidores verem, e só então ponha em `0`.

---

## Depois: o que o tipster consegue fazer sozinho

Hoje os passos 1 e 2 são autosserviço + um clique. Os passos 3, 4 e 5 são do tipster mas
ele não tem como pegar o id. Os passos 6 e 7 são o gargalo real — exigem deploy.

O caminho proposto (ainda não implementado) é **matar as env vars por tipster**: o registro
do tenant vira tabela no Postgres, com tela no `/admin`; e o id, que é a parte que ninguém
acerta digitando, resolve sozinho com um `/vincular <código>` no apoio — o bot já sabe o
próprio `chat.id`, e ele chega **já migrado**. A semente sai da mesma tela, lendo o último
código do dono no banco.
