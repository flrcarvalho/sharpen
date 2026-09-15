# RUNBOOK — aviso de versão ao grupo `Sharpen - Testers`

> **Procedimento, não regra de código.** Saiu do [`CLAUDE.md`](../CLAUDE.md) na s358 pelo
> mesmo motivo do runbook de contas. Nada foi cortado.
>
> A regra que ficou no `CLAUDE.md` é a que decide: **o aviso e a home são o MESMO ato**
> (`python scripts/avisar_testers.py`), e **nunca se envia sem o "pode mandar" do Feca**.

---

## Aviso de versão ao grupo `Sharpen - Testers`

O `@sharpenbetbot` é admin do grupo e serve de canal de **novas versões e atualizações**.

**O aviso e a home são o MESMO ato — `python scripts/avisar_testers.py`.** Ele mostra a
prévia (ensaio é o padrão; só envia com `--enviar`), confere o destino por `getChat`,
publica no grupo e grava a mesma nota em `app/changelog.json`, que é o que a home lê pela
rota `/changelog`. **Nunca edite o changelog à mão e nunca mande a mensagem por fora** —
senão a home fica versões atrás em silêncio ([o caso](CASOS.md#o-changelog-ficou-8-versões-atrás-duas-vezes)).
`tests/test_changelog.py` fica **vermelho** quando a versão do manifest não tem nota
(dispensa só declarada, em `sharpenup_sem_nota`). Gate manual: `python tools/audit_changelog.py`.

**Só informamos. Não damos detalhes.** A mensagem diz o que mudou em **uma linha** e o que o
tester precisa **fazer**. Ficam de fora: mecânica interna, nome de campo, causa raiz, número de
bilhete, arquivo, commit. O nível é o de nota de release curta, não o do `STATUS.md`.

> ⚠️ **`Sharpen` é o SISTEMA; `SharpenUp` é a EXTENSÃO.** O número de versão é do
> **SharpenUp** — é ele que o tester atualiza. Escrever "Sharpen 0.6.46" versiona o produto
> inteiro. Vale para release note, changelog e qualquer texto voltado ao usuário.
> → [o caso](CASOS.md#sharpen-0646-versionou-o-produto-inteiro)

- `chat_id` = `-5172183099` · `BOT_TOKEN` no `.env` de `Downloads/BOTS/sharpen-bot`.
- **Confirmar o destino com `getChat` antes de publicar.** Mensagem em grupo não tem desfazer.
- **Nunca `getUpdates`** — briga com o polling do bot em produção.
- **Nunca diagnostique envio chamando `sendMessage` de novo.** Grupo real não tem desfazer,
  e a segunda chamada publica o teste. Na primeira falha, **imprima o `description` da
  resposta**: ele já diz a causa ([o caso](CASOS.md#o-teste-de-diagnóstico-foi-parar-no-grupo)).
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

