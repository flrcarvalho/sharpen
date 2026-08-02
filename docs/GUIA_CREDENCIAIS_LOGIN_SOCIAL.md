# GUIA — Credenciais do login social (Google + Telegram)

> **Contexto:** a Fase 3 do multiusuário (s236) está no ar em modo **dormente**.
> O código já sabe fazer tudo; os botões "Entrar com Google/Telegram" só aparecem
> na tela de login quando as env vars abaixo existirem no Railway. **Nenhum
> deploy novo é necessário** — colar as variáveis reinicia o serviço e pronto.
>
> Rotas envolvidas: `GET /auth/metodos` (diz quais botões mostrar),
> `GET /auth/google` + `/auth/google/callback`, `GET /auth/telegram/ir` →
> `oauth.telegram.org` → `/auth/telegram/retorno` → `POST /auth/telegram`.
> Plano canônico: [`PLANO_MULTIUSUARIO_2026.md`](PLANO_MULTIUSUARIO_2026.md).

---

## 1. Google (~15 min, grátis)

1. Acesse [console.cloud.google.com](https://console.cloud.google.com) e crie um
   projeto (ex.: **Sharpen**).
2. **APIs e serviços → Tela de permissão OAuth**:
   - Tipo **Externo** → nome do app "Sharpen", seu e-mail de suporte.
   - Escopos: não precisa adicionar nada (openid/email/profile são os básicos).
3. **APIs e serviços → Credenciais → Criar credenciais → ID do cliente OAuth**:
   - Tipo: **Aplicativo da Web**.
   - Em **URIs de redirecionamento autorizados**, adicione EXATAMENTE:
     ```
     https://www.sharpen.bet/auth/google/callback
     ```
     (com `www`, sem barra no final — qualquer diferença dá `redirect_uri_mismatch`.)
4. Copie o **Client ID** (`…apps.googleusercontent.com`) e o **Client Secret**.

> ⚠️ **Pegadinha do modo "Em teste":** a tela de permissão nasce com status
> **Testing** — nesse modo, SÓ os e-mails adicionados em "Test users" conseguem
> logar (os outros veem "acesso bloqueado"). Para liberar geral: **Tela de
> permissão OAuth → Publicar app** (para escopos básicos não exige verificação
> da Google, é 1 clique). Enquanto testa, dá para simplesmente adicionar seu
> Gmail como test user.

## 2. Telegram (~5 min)

1. Fale com o [@BotFather](https://t.me/BotFather):
   - `/newbot` → nome de exibição (ex.: "Sharpen Login") → username (ex.:
     `SharpenLoginBot`). Pode também reusar um bot existente.
2. Mande `/setdomain` → escolha o bot → responda:
   ```
   www.sharpen.bet
   ```
   (sem `https://`. É isso que autoriza o oauth.telegram.org a devolver o login
   para o nosso domínio — sem esse passo o fluxo abre e morre em silêncio.)
3. Copie o **token** do bot (formato `123456789:AAxxxxxxxx…`).

## 3. Railway (Variables do serviço do app)

| Variável | Valor |
|---|---|
| `GOOGLE_CLIENT_ID` | Client ID do passo 1.4 |
| `GOOGLE_CLIENT_SECRET` | Client Secret do passo 1.4 |
| `TELEGRAM_BOT_TOKEN` | token do bot do passo 2.3 |

- Colar na caixa de Variables (sem aspas, sem espaço nas pontas — mesma régua
  dos hashes de senha; o token do Telegram tem `:` no meio, é normal).
- Salvar → o Railway reinicia o serviço sozinho (~1 min).

## 4. Conferir que acendeu

1. `https://www.sharpen.bet/auth/metodos` deve responder
   `{"google": true, "telegram": true}`.
2. `https://www.sharpen.bet/login` → os botões "Entrar com Google" e "Entrar
   com Telegram" aparecem abaixo do Entrar (divisor "ou").
3. Teste cada fluxo com uma conta que NÃO existe no sistema → deve terminar em
   **"Cadastro recebido! Sua conta está em análise"** e a conta aparecer
   **pendente** no [`/admin`](https://www.sharpen.bet/admin). Aprove e entre de
   novo — aí sim loga direto.

## Como o sistema decide quem é quem (referência rápida)

| Situação | O que acontece |
|---|---|
| `google_sub`/`telegram_id` já vinculado a uma conta **ativa** | Loga direto (mesmo cookie de sessão de sempre) |
| Conta existente com o **mesmo e-mail** (verificado pela Google) | Vincula o Google àquela conta e loga |
| Conta pendente/suspensa | Não loga; mensagem na tela de login |
| Desconhecido | Cria conta **pendente** (username derivado do e-mail/nome; aparece no /admin para aprovação) |

## Se algo falhar

- **`redirect_uri_mismatch` (Google):** o URI do passo 1.3 não está idêntico —
  confira `www` e a ausência de barra final.
- **"Acesso bloqueado" (Google):** app em modo Testing sem o seu e-mail em Test
  users — publique o app ou adicione o e-mail.
- **Telegram abre e volta para o login com erro:** `/setdomain` faltando ou com
  domínio diferente de `www.sharpen.bet`.
- **Botões não aparecem:** `GET /auth/metodos` responde `false` → env var
  faltando/truncada no Railway (o código não sobe sem redeploy, mas env var não
  precisa de deploy — só salvar e esperar o restart).

---

CRIADO: sessão 236 (2026-08-03, madrugada autorizada).
