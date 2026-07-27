# docs/marketing — páginas de apresentação do Sharpen

Duas páginas publicadas como **Artifacts privados** (claude.ai), fora do app.
Não são servidas pelo FastAPI, não entram no `main.py` e não têm rota.

| Arquivo | O que é | Público |
|---|---|---|
| `landing-usuario-final.html` | Landing de apresentação do produto — como funciona, recursos, métricas, comparativo com os trackers globais | Usuário final (apostador metódico, operador de banca, tipster) |
| `briefing-agencia.html` | Briefing completo de marca e produto (14 seções numeradas) | Agência de marketing |
| `build_fontes.py` | Injeta as fontes da marca como data URI no lugar do marcador `<!--FONTS-->` | — |

---

## Por que existe um passo de build

A CSP dos Artifacts **bloqueia host externo** — webfont por URL cairia em fallback
silencioso e a página perderia Manrope + JetBrains Mono, que são metade da assinatura
visual da marca. Por isso as duas fontes entram **embutidas em base64**.

Os arquivos versionados aqui são as **fontes** (com o marcador `<!--FONTS-->`).
O arquivo publicado é o **gerado** (`*.build.html`, ~135–145 KB), que fica **fora do git**
(ver `.gitignore`): é a fonte mais ~75 KB de base64, blob binário que não diffa.

> **Abrir a fonte no navegador funciona, mas sem as fontes da marca** — o marcador
> `<!--FONTS-->` ocupa o lugar das `@font-face`, então cai em system-ui + mono genérica.
> Para ver a página exatamente como está publicada, abra o `.build.html`.

```
cd docs/marketing
python build_fontes.py landing-usuario-final.html landing-usuario-final.build.html
python build_fontes.py briefing-agencia.html      briefing-agencia.build.html
```

Depois é só republicar o arquivo gerado pelo mesmo caminho de sempre — a URL do
Artifact é mantida quando o `file_path` não muda.

> Só o subset **latin** (`U+0000-00FF`) é embutido: ele já cobre todo o pt-BR, porque
> os acentos vivem no Latin-1 Supplement. O `latin-ext` fica de fora de propósito —
> dobraria o peso sem cobrir nada que a página use.

---

## Regras de conteúdo (não afrouxar sem falar com o Feca)

1. **Todo número usado nas páginas sai da seção 12 do briefing** (`Provas e números
   autorizados`). Número novo entra lá primeiro, com a qualificação de uso, e só
   depois vai para a peça.
2. **O comparativo tem de perder pelo menos uma linha.** Hoje perde em CLV e em busca
   de valor. Comparativo que ganha tudo é propaganda, e este público reconhece.
3. **Nada de "baixe na loja"** para o SharpenUp: loja de extensão não aceita software
   de apostas, a distribuição é por link direto e vai continuar assim.
4. **Sem promessa de lucro, sem estética de tipster/cassino, 18+ sempre visível.**
5. Marca e tokens: `../../../pack/CLAUDE.md` + `../../../pack/tokens/tokens.css`.
   Padrão monetário: `../UI_REFERENCE.md §5`.

---

## Pendências conhecidas

- **Versão em inglês da landing** não foi feita — o posicionamento é worldwide, mas as
  duas páginas estão em pt-BR. A landing foi escrita para que a troca de idioma seja
  só de copy (nenhum texto está preso em imagem ou em SVG).
- **Parecer jurídico** (briefing §8.2) trava a mídia paga. É o item de caminho crítico.
- **Preço** não está definido — nenhuma das duas páginas cita valor, de propósito.
