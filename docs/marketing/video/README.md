# docs/marketing/video — cartões e títulos do vídeo (Remotion)

Projeto **isolado do app**: tem o próprio `package.json`, o próprio `node_modules`
(gitignored) e nenhuma ligação com o FastAPI. Nada daqui é servido em produção.

## O que é Remotion, em uma frase

Vídeo escrito em React: cada componente é um quadro, e o CLI renderiza a sequência em
MP4. A vantagem que decidiu a escolha não é estética, é esta: **o cartão lê o número
direto do Postgres**. Se a base do depoente mudar, re-renderizar é um comando, e a peça
nunca mente com cara de exatidão.

## Como rodar

```
npm install                 # uma vez
python gerar_dados.py       # lê o banco e escreve src/dados.json (só SELECT)
npx remotion studio src/index.jsx                                  # editar vendo
npx remotion render src/index.jsx CartaoProva out/cartao.mp4       # render final
npx remotion still  src/index.jsx CartaoProva out/cartao.png --frame=140
```

`gerar_dados.py` usa a `DATABASE_URL` do `.env` da raiz do Planilhador.

## Arquivos

| Arquivo | O que é |
|---|---|
| `gerar_dados.py` | Leitura pura do Postgres. Escreve `src/dados.json` |
| `src/dados.json` | Os números medidos. **Gerado, nunca editado à mão** |
| `src/tokens.js` | Espelho de `pack/tokens/tokens.css` e os helpers de número |
| `src/Marca.jsx` | A marca do Sharpen, copiada do `app/static/app.html` |
| `src/CartaoProva.jsx` | O cartão de prova do depoente |
| `src/Root.jsx` | Composições e as fontes self-host |
| `public/fonts/` | Manrope e JetBrains Mono, as mesmas do app |

## Regras que valem aqui

1. **Nenhuma cor literal.** Tudo sai do `src/tokens.js`, que espelha o CSS da marca.
2. **Dinheiro no padrão do produto:** agregado é inteiro, milhar com ponto, e **nunca
   abreviado com k ou M**. A peça não pode contradizer a tela.
3. **Escada de Tinta pelo papel:** identidade e valor em `ink`, label em `inkSoft`, e
   `inkMute` não carrega informação. Em vídeo o corpo é grande, mas o papel continua
   mandando na cor.
4. **Número exibido é número medido.** Nada de valor digitado no componente. O que não
   vem do banco (a fala "1 hora por dia") vive no `FRASES` do gerador, com a linha da
   transcrição anotada ao lado.
5. **Nada de terceiro na peça:** sem e-mail, sem custo em R$, sem nome de fornecedor ou
   de tipster. O cartão é do depoente, com autorização dele, e de mais ninguém.

## O que já existe

- **CartaoProva** (1920×1080, 8s): usado no ato 3 do
  [roteiro](../ROTEIRO_VIDEO_APRESENTACAO.md). Primeiro render em 19/09/2026 com os
  dados do Jonathan.
