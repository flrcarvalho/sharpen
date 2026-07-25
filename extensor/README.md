# SharpenUp — extensão de captura

> _A perninha do Sharpen que sobe seus bilhetes pro dashboard._

Extensão de navegador (Manifest V3) que captura bilhetes das casas e envia para o
**sharpen.bet** por um **código de pareamento**. Funciona em qualquer Chromium —
**Octo Browser**, Chrome, Edge, Brave, Opera.

Marca conforme o kit **"SharpenUp — Kit de Marca (Extensão)"** (FDC Capital): lâmina
do Sharpen + selo ↑, azul `#2E8BFF` / `#7FB2FF`, verde só em confirmação. Fonte do
ícone em `icons/icon.svg`; paleta no topo do `popup.css`.

| Para… | Leia |
|---|---|
| entender como a captura funciona | [`docs/SHARPENUP_ARQUITETURA.md`](../docs/SHARPENUP_ARQUITETURA.md) |
| **ligar uma casa nova** | [`docs/GUIA_CASA_SHARPENUP.md`](../docs/GUIA_CASA_SHARPENUP.md) |
| rodar a regressão da captura | [`harness/README.md`](harness/README.md) |
| conferir se a casa está registrada | `python tools/audit_sharpenup.py` |

## Como funciona (modelo de pareamento)

1. No **dashboard**, com a conta (casa/parceiro) aberta, clique **"🔗 Conectar
   extensão"** → ele gera um código (`ABCD-EFGH`) e copia para a área de
   transferência.
2. Na **extensão** (ícone na barra), cole o código e clique **Conectar**.
3. Navegue até o bilhete na casa. Clique no **botão flutuante SharpenUp** (aparece
   sobre a página quando há pareamento ativo — arrastável) **ou** no ícone →
   **Capturar**.
   - **modo texto:** o robô colhe os bilhetes sozinho e envia tudo de uma vez;
   - **modo print:** arraste a moldura sobre o bilhete → **Capturar** (Snap por bilhete).
4. O material aparece na área de colar do dashboard, naquela conta. Depois **Processar**
   normalmente (com revisão na grade).
5. Trocou de casa? Gere um novo código no dashboard e reconecte.

Cada navegador/perfil Octo cola o **seu** código → várias pontes ao mesmo tempo,
cada uma numa casa. O código carrega dono + casa + parceiro + modo.

## Casas em modo texto (robô)

**Superbet · BETesporte · Betano · Betfair · Pinnacle · KTO · Bet365.**
Todas as demais → modo **print** (moldura fixa + Snap). O modo vem do backend
(`app/captura.py` `_MODO_POR_CASA`), não da extensão.

Em todas, o dado vem da **própria API que a página já baixa** — sem OCR, sem adivinhar
auth: o inject roda no mundo `MAIN`, lê a resposta e repassa ao `content.js`. Detalhes de
endpoint, chave de dedup e fim de paginação por casa: `SHARPENUP_ARQUITETURA.md §4`.

- **Betfair · Pinnacle · KTO** — o inject **repagina sozinho** a partir de uma requisição
  real da página (aprende url+headers), então ninguém precisa clicar "mostrar mais".
- **Bet365** — não dá para chamar a API direto (o token `x-net-sync-term` rotaciona por
  requisição): o inject navega por **rota** (`location.hash`) até a confirmação de cada
  bilhete, de onde vem o código `BR` estável. Ver `docs/PLANO_BET365_CAPTURA_API.md`.
- **Superbet** — o código do bilhete vem no atributo `id` do card (exato, sem OCR).
- **Parada do robô:** janela de **look-back** (padrão 30 dias) **OU** um **ID de parada**
  ("copiar dele pra cima"). Na Betfair, cujo histórico é ilimitado e fora de ordem, o freio
  é por **quantidade** (padrão 100) + dias opcional + "varrer conta inteira". A janela corta
  **só bilhetes resolvidos** — aposta em aberto nunca é cortada.
- **Nada foi perdido se a conexão cair:** o texto raspado fica bancado em `envioPendente` e
  o popup mostra **Reenviar** (sem re-raspar).

## Instalar (modo desenvolvedor / unpacked)

**Chrome / Edge / Brave / Octo:**

1. Abra `chrome://extensions` (no Octo, o gerenciador de extensões do perfil).
2. Ligue o **Modo do desenvolvedor** (canto superior).
3. **Carregar sem compactação** (Load unpacked) → selecione esta pasta `extensor/`.
4. Fixe o ícone na barra. Pronto.

No **Octo**, a extensão é adicionada por perfil (ou global, conforme a config do
Octo). Repita o carregamento nos perfis onde for capturar.

> **Depois de atualizar a extensão, dê `Ctrl+Shift+R` na aba da casa.** Recarregar a
> extensão **não** re-injeta em aba já aberta — é a causa nº 1 de "capturou 0 bilhetes".

## Distribuição e atualização

A extensão **não está na Chrome Web Store** (rejeitada pela política de jogos de azar) e é
instalada *unpacked*, que não tem auto-update. A distribuição é um **link fixo**:

- **`www.sharpen.bet/extensao`** (com `www` — o apex `sharpen.bet` dá 404 em paths, o
  forwarding da GoDaddy não preserva o caminho) — página pública com o botão de baixar o `.zip`
  (gerado on-the-fly a partir desta pasta no deploy, sempre a última versão) e o passo-a-passo
  de instalar/recarregar. É o único canal — mande este link para cada operador.
- A extensão reporta a própria versão (`manifest.json`) nos handshakes de captura
  (`conectar`/`validar`/`enviar`). O backend compara com a versão publicada e, se estiver
  atrás, mostra um aviso **no popup** (faixa amarela → botão Atualizar) e **no extrator do
  dashboard** (badge na ponte). Instalação antiga (que ainda não reporta versão) conta como
  desatualizada.

> **Regra:** toda mudança nesta pasta **precisa bumpar `version` no `manifest.json`** — senão
> a detecção de desatualizado não enxerga a nova release.

## Configurar o servidor (opcional)

Por padrão a extensão fala com `https://www.sharpen.bet`. Para testar contra outro
host, abra o popup → **Configurar servidor** → informe a URL → Salvar.

## Arquivos

| Arquivo | Papel |
|---|---|
| `manifest.json` | Manifesto MV3 (permissões, ícones, service worker, injects por host) |
| `config.js` | URL da API (ponto único), lida por popup e background |
| `popup.html/.css/.js` | Painel: parear, estado, freios do robô, botão capturar |
| `content.js` | Mundo isolado: FAB, moldura de print, robôs de texto e os `formatTicket*` |
| `background.js` | Print da aba + recorte + envio para `/captura/enviar` |
| `sb_inject.js` | Superbet — mundo MAIN, hook da API de tickets |
| `be_inject.js` | BETesporte — hook de `RequestUserTickets` |
| `bn_inject.js` | Betano — hook de `bet-history-v3` (duas abas) |
| `bf_inject.js` | Betfair — hook + **replay** de `/activity/sportsbook` |
| `pn_inject.js` | Pinnacle — hook + replay de `/wager-filter` (array posicional → objeto) |
| `kto_inject.js` | KTO/Kambi — hook + replay de `/coupon/history.json` |
| `b3_inject.js` | Bet365 — hook do `/sportshistoryapi` + navegação por rota |
| `harness/` | Regressão offline: roda o código real contra payloads salvos |
| `icons/` | Ícones 16/32/48/128 |

## Contrato com o backend

- `POST /captura/conectar` — `{codigo, versao}` → `{token, casa, parceiro, modo, dono, desatualizada}`
- `POST /captura/validar` — `{token, versao}` → 401 se a sessão morreu (popup volta a parear)
- `POST /captura/enviar` — multipart `token` + `tipo=imagem|texto` + conteúdo + `origem` (host)

As três são isentas do guarda CSRF (autenticam por código/token). Lógica em
`app/captura.py`, rotas em `app/main.py`. A `origem` é o backstop casa↔site: captura vinda
do site de outra casa conhecida é recusada com 409.
