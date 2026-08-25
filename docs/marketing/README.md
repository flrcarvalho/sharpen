# docs/marketing — documentos HTML na pegada Sharpen (dark)

Duas páginas publicadas como **Artifacts privados** (claude.ai), fora do app.
Não são servidas pelo FastAPI, não entram no `main.py` e não têm rota.

| Arquivo | O que é | Público |
|---|---|---|
| `landing-usuario-final.html` | Landing do produto — como funciona, recursos, métricas, comparativo com os trackers globais | Usuário final (apostador metódico, operador de banca, tipster) |
| `briefing-agencia.html` | Briefing de marca e produto, 14 seções numeradas | Agência de marketing |
| `build_fontes.py` | Gera as duas saídas a partir da fonte | — |

---

## ⚠️ DARK ONLY — a regra que já quebrou uma vez

Documento da marca **não tem tema claro**. Sem `@media (prefers-color-scheme: light)`,
sem `:root[data-theme="light"]`, sem toggle, sem detecção de SO.

> **O que aconteceu (s214):** as duas primeiras versões saíram com um bloco
> `prefers-color-scheme: light`, porque a página publicada segue o tema do leitor.
> Resultado: quem abria o arquivo com o Windows em tema claro recebia um documento
> **branco**. A regra da marca perdeu para uma convenção de plataforma.
>
> Isso não depende mais de eu lembrar: o `build_fontes.py` **recusa gerar** se achar
> tema claro no CSS. O gate ignora comentários — senão acusa a própria nota que diz
> "sem prefers-color-scheme".

O gate também exige `<!DOCTYPE html>` e `data-theme="dark"` no `<html>`.

---

## As três formas de cada documento

```
landing-usuario-final.html            ← FONTE, versionada. Documento completo,
                                        com o marcador <!--FONTS-->
landing-usuario-final.build.html      ← ABRA ESTA. Documento completo + fontes
                                        em base64. Offline, duplo-clique.
landing-usuario-final.fragment.html   ← o que sobe pro Artifact (sem <html>)
```

```
python build_fontes.py landing-usuario-final.html     # gera .build e .fragment
python build_fontes.py briefing-agencia.html
```

Os dois gerados são **gitignored**: cada um é a fonte mais ~75 KB de base64, blob
binário que não diffa e sujaria o histórico. Regerar leva um segundo.

**Por que existe o fragmento:** o Artifact embrulha o arquivo no próprio esqueleto
(`<!doctype html>…<head>…<body>`). Uma segunda `<html>` dentro geraria markup
inválido — então a versão publicada é só `<title>` + `<style>` + conteúdo do body.
O que mata o bug branco vale nas duas formas: sem tokens light definidos, mesmo que
o Artifact carimbe `data-theme="light"` no root, a página continua escura.

**Por que as fontes são embutidas:** a CSP do Artifact bloqueia host externo, então
webfont por URL cairia em fallback silencioso — e Manrope + JetBrains Mono são
metade da assinatura visual. Só o subset `latin` (`U+0000-00FF`) entra: já cobre
todo o pt-BR, porque os acentos vivem no Latin-1 Supplement.

---

## Regras de conteúdo (não afrouxar sem falar com o Feca)

1. **Todo número usado nas páginas sai da seção 12 do briefing** (`Provas e números
   autorizados`). Número novo entra lá primeiro, com a qualificação de uso.
2. **O comparativo tem de perder pelo menos uma linha.** Hoje perde em CLV e em busca
   de valor. Comparativo que ganha tudo é propaganda, e este público reconhece.
3. **Nada de "baixe na loja"** para o SharpenUp: loja de extensão não aceita software
   de apostas, a distribuição é por link direto e vai continuar assim.
4. **Sem promessa de lucro, sem estética de tipster/cassino, 18+ sempre visível.**
5. **Verde e vermelho só em resultado numérico** ou no par faça/não-faça. Nunca em
   título, ícone decorativo ou palavra solta no meio do texto.
6. **Todo número em JetBrains Mono** com `tabular-nums`; todo texto corrido em Manrope.
7. Um único `--shadow-card` por documento, no elemento-tese. Hierarquia é por
   superfície e borda, não por sombra.
8. Breakpoints: **900px e 760px**, só.

Marca e tokens: `../../../pack/CLAUDE.md` + `../../../pack/tokens/tokens.css`.
Padrão monetário: `../UI_REFERENCE.md §5`.

> Exceção de cor documentada: `#fff` no texto do botão primário — é o que
> `pack/CLAUDE.md §6` especifica ("botão primário = `var(--accent)` com texto branco").
> É o único hex fora da lista de tokens nos dois arquivos.

---

## ⚠️ A landing do produto agora é uma ROTA, não um documento (s294)

A reescrita aprovada na s214 foi feita — mas **noutro lugar**, e é isso que importa
saber antes de mexer aqui:

| Arquivo | Onde vive | Para quem |
|---|---|---|
| `../../app/static/landing.html` | **rota `/` de sharpen.bet**, pública e indexável | quem ainda não é cliente |
| `landing-usuario-final.html` (aqui) | Artifact privado | histórico / apresentação avulsa |

A página pública nasceu com print real (14 telas + 7 recortes de elemento, gerados
por `../../scripts/demo/`), sem detalhe de arquitetura e sem JavaScript nenhum. Ela
é a peça viva. **Este documento aqui virou histórico** — não o edite achando que
está mexendo no que o público vê.

As 4 correções que travavam o uso dos prints foram fechadas na s294 (contas irreais,
Monte Carlo em "calculando…", custos zerados e a faixa de Solidez).

---

## Pendências conhecidas

- **A seção 12 do briefing está DESATUALIZADA e é a fonte obrigatória de número.**
  Medido na s294: *fontes lidas na origem* passou de 11 para **23** (22 casas com robô
  + Polymarket on-chain) e *categorias de mercado* de 27 para **30** (contadas pelo
  extrator canônico, `app/taxonomia.py`). A landing pública já usa os números novos.
  Atualizar o §12 para os dois voltarem a bater.
- **Versão em inglês** não foi feita — o posicionamento é worldwide, mas as duas
  páginas estão em pt-BR. Foram escritas para que a troca seja só de copy (nenhum
  texto está preso em imagem ou SVG).
- **Parecer jurídico** (briefing §8.2) trava a mídia paga. É o caminho crítico.
- **Preço** não está definido — nenhuma das duas páginas cita valor, de propósito.
