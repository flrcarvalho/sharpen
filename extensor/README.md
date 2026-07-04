# Sharpen Capture — extensão de captura

Extensão de navegador (Manifest V3) que captura bilhetes das casas e envia para o
**sharpen.bet** por um **código de pareamento**. Funciona em qualquer Chromium —
**Octo Browser**, Chrome, Edge, Brave, Opera.

> Marca provisória (nome "Sharpen Capture", ícone azul placeholder). Quando a
> identidade final chegar, trocar `icons/*.png`, o `name` no `manifest.json` e as
> variáveis de cor no topo do `popup.css` — o resto acompanha.

## Como funciona (modelo de pareamento)

1. No **dashboard**, com a conta (casa/parceiro) aberta, clique **"🔗 Conectar
   extensão"** → ele gera um código (`ABCD-EFGH`) e copia para a área de
   transferência.
2. Na **extensão** (ícone na barra), cole o código e clique **Conectar**.
3. Navegue até o bilhete na casa e clique **📸 Capturar região** → arraste a
   moldura sobre o bilhete → **Capturar**.
4. O print aparece na área de colar do dashboard, naquela conta. Repita para cada
   bilhete e depois **Processar** normalmente (com revisão na grade).
5. Trocou de casa? Gere um novo código no dashboard e reconecte.

Cada navegador/perfil Octo cola o **seu** código → várias pontes ao mesmo tempo,
cada uma numa casa. O código carrega dono + casa + parceiro + modo.

- **Superbet** (e demais) → modo **print** (moldura ajustável). ✅ pronto
- **Betano** → modo **texto** (robô de rolagem). ⏳ próxima fase

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
| `overlay.js` | Moldura de seleção injetada na página da casa |
| `background.js` | Print da aba + recorte + envio para `/captura/enviar` |
| `icons/` | Ícones 16/32/48/128 (placeholder) |

## Contrato com o backend

- `POST /captura/conectar` — `{codigo}` → `{token, casa, parceiro, modo, dono}`
- `POST /captura/enviar` — multipart `token` + `tipo=imagem` + `imagem` (PNG)

Ambas isentas do guarda CSRF no servidor (autenticam por código/token). Lógica no
`app/captura.py` e rotas em `app/main.py`.
