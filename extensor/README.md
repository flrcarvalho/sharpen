# SharpenUp — extensão de captura

> _A perninha do Sharpen que sobe seus bilhetes pro dashboard._

Extensão de navegador (Manifest V3) que captura bilhetes das casas e envia para o
**sharpen.bet** por um **código de pareamento**. Funciona em qualquer Chromium —
**Octo Browser**, Chrome, Edge, Brave, Opera.

Marca conforme o kit **"SharpenUp — Kit de Marca (Extensão)"** (FDC Capital): lâmina
do Sharpen + selo ↑, azul `#2E8BFF` / `#7FB2FF`, verde só em confirmação. Fonte do
ícone em `icons/icon.svg`; paleta no topo do `popup.css`.

## Como funciona (modelo de pareamento)

1. No **dashboard**, com a conta (casa/parceiro) aberta, clique **"🔗 Conectar
   extensão"** → ele gera um código (`ABCD-EFGH`) e copia para a área de
   transferência.
2. Na **extensão** (ícone na barra), cole o código e clique **Conectar**.
3. Navegue até o bilhete na casa. Clique no **botão flutuante SharpenUp** (aparece
   sobre a página quando há pareamento ativo — arrastável) **ou** no ícone →
   **Capturar** → arraste a moldura sobre o bilhete → **Capturar**.
4. O print aparece na área de colar do dashboard, naquela conta. Repita para cada
   bilhete e depois **Processar** normalmente (com revisão na grade).
5. Trocou de casa? Gere um novo código no dashboard e reconecte.

Cada navegador/perfil Octo cola o **seu** código → várias pontes ao mesmo tempo,
cada uma numa casa. O código carrega dono + casa + parceiro + modo.

- **Superbet** (e demais) → modo **print** (moldura fixa + Snap). ✅
- **Betano** → modo **texto** (robô rola a página, colhe e deduplica os bilhetes). ✅

## Instalar (modo desenvolvedor / unpacked)

**Chrome / Edge / Brave / Octo:**

1. Abra `chrome://extensions` (no Octo, o gerenciador de extensões do perfil).
2. Ligue o **Modo do desenvolvedor** (canto superior).
3. **Carregar sem compactação** (Load unpacked) → selecione esta pasta `extensor/`.
4. Fixe o ícone na barra. Pronto.

No **Octo**, a extensão é adicionada por perfil (ou global, conforme a config do
Octo). Repita o carregamento nos perfis onde for capturar.

## Configurar o servidor (opcional)

Por padrão a extensão fala com `https://www.sharpen.bet`. Para testar contra outro
host, abra o popup → **Configurar servidor** → informe a URL → Salvar.

## Arquivos

| Arquivo | Papel |
|---|---|
| `manifest.json` | Manifesto MV3 (permissões, ícones, service worker) |
| `config.js` | URL da API (ponto único), lida por popup e background |
| `popup.html/.css/.js` | Painel: parear, estado, botão capturar |
| `fab.js` | Botão flutuante (content script em todas as casas) — some durante o print |
| `overlay.js` | Moldura de seleção injetada na página da casa |
| `background.js` | Print da aba + recorte + envio para `/captura/enviar` |
| `icons/` | Ícones 16/32/48/128 (placeholder) |

## Contrato com o backend

- `POST /captura/conectar` — `{codigo}` → `{token, casa, parceiro, modo, dono}`
- `POST /captura/enviar` — multipart `token` + `tipo=imagem` + `imagem` (PNG)

Ambas isentas do guarda CSRF no servidor (autenticam por código/token). Lógica no
`app/captura.py` e rotas em `app/main.py`.
