# SHELL_SPEC — contrato da casca compartilhada (FDC Capital)

> **Por que este arquivo existe.** Planilhador (`app/static/index.html`, CSS inline) e
> Betting Dashboard (`app/static/dash/assets/css/layout.css`) renderizam **a mesma casca**
> (sidebar + pagehead + nav + cards). Hoje cada um a reescreve à mão → drift de tamanho
> (ex.: título 30px no Planilhador vs 22px no Dashboard, sessão 80d). A governança de marca
> (sessão 74) só trava **cor**; **tamanho/tipografia/spacing não tinham contrato nem checagem.**
> Este é o contrato. **Fonte de verdade dos VALORES: `pack/tokens/tokens.css`** (e suas cópias
> geradas). Aqui mapeia-se **cada elemento da casca → o token** que ele DEVE usar.
>
> Regra de ouro: **nenhum elemento da casca usa `px` literal para fonte/spacing.** Sempre
> `var(--text-*)` / `var(--sp-*)` / `var(--r-*)`. Off-scale = drift (a checar pela etapa B).
>
> Referência de implementação canônica: o **Dashboard** (`dash/assets/css/layout.css`).
> Quando Planilhador e Dashboard divergirem, **o Dashboard vence** (até a etapa A unificar num
> CSS só). Atualizado: 2026-06-30 (sessão 80d).

---

## 0. Base (body + fundo)

| Propriedade | Token | Valor |
|---|---|---|
| `body` font-family | `--font-sans` | Manrope |
| `body` font-size | `--text-sm` | 13px |
| `body` background | `--bg` | Platinum Black |
| `body` color | `--ink` | — |
| Grid de fundo (`body::before`) | cor `--grid` · `background-size: 44px 44px` · `opacity: .55` | — |

> Grid: **idêntico** nos dois apps. Não alterar opacidade/tamanho sem mudar nos dois.

---

## 1. Sidebar

| Elemento | Propriedade | Token / valor |
|---|---|---|
| `.sidebar` | width | **264px** |
| | background | `--surface` (Planilhador) / `--bg2` (Dashboard — unificar em A) |
| | border-right | `1px var(--line-2)` |
| brand `img` | width | `100%` (logo horizontal preenche a largura) |
| `.nav-group` | font-size | `--text-nano` (9px) |
| | weight / ls / transform | `700` · `.2em` · uppercase · `--font-mono` · `--ink-mute` |
| `.nav-item` | font-size | `--text-sm` (13px) |
| | weight | `600` |
| | height | `34px` |
| | gap | `--sp-2` (8px) |
| | padding | `4px 8px 4px 16px` (`--sp-1 --sp-2 --sp-1 --sp-4`) |
| | border-left | `2px solid transparent` |
| `.nav-item.active` | cor / bg / borda | `--accent` · `rgba(var(--accent-rgb),.12)` · border-left `--accent` |
| `.nav-icon` | size | `15px` |

---

## 2. Pagehead / topbar (faixa do título)

> No Dashboard é um `.topbar` **fixo, opaco** (`bg --bg`, `border-bottom --line-2`, altura 68px)
> → o grid **não** aparece atrás do título. No Planilhador é uma faixa equivalente (`.pagehead`
> com `bg --bg` + `border-bottom`, sangrando para as bordas do `.content`). **O título NUNCA
> fica sobre o grid.**

| Elemento | Propriedade | Token / valor |
|---|---|---|
| Título (`.page-title` / `.pagehead-title`) | font-size | **`--text-xl` (22px)** |
| | weight / ls / line-height | `800` · `-.035em` · `1` |
| | cor | gradiente `linear-gradient(100deg, var(--accent), var(--accent-2))` (clip text) |
| Eyebrow (`.page-sub` / `.pagehead-eyebrow`) | font-size | **`--text-nano` (9px)** |
| | família / transform / ls | `--font-mono` · uppercase · `.18em` · `--ink-mute` |
| Faixa | background / borda | `--bg` · `border-bottom 1px var(--line-2)` |

---

## 3. Cards / panels

| Elemento | Token / valor |
|---|---|
| Card padrão | `background var(--surface)` · `border 1px var(--line)` · `border-radius var(--r-lg)` |
| Card de KPI — **tarja azul** antes do label | `4px × 13px`, `background var(--accent)`, `border-radius 2px`, `margin-right 8px` |
| KPI label | `--font-mono` · uppercase · weight `700` · ls `.08em` · `--ink-mute` |
| KPI valor | `--font-mono` · tabular-nums · **alinhado à direita** · weight `800` |

---

## 4. Padrão monetário (resumo — spec completo em `UI_REFERENCE.md §5`)

- Sempre `--font-mono` + `font-variant-numeric: tabular-nums`, **alinhado à direita**.
- Sinal + `R$` neutros (`--ink-soft`); **cor pos/neg só no número**.
- Zero (Void / cashout=stake) = neutro, sem sinal e sem cor.

---

## 5. Escala de tipografia (de `tokens.css` — referência rápida)

`--text-nano` 9 · `--text-xxs` 10 · `--text-xs` 11 · `--text-sm` 13 · `--text-md` 14 ·
`--text-base` 15 · `--text-lg` 18 · `--text-xl` 22 · `--text-2xl` 28 · `--text-3xl` 36.

Espaço (`--sp-*`, escala 4px): 1=4 · 2=8 · 3=12 · 4=16 · 5=20 · 6=24 · 8=32 · 10=40 · 14=56 · 20=80.

Raio (`--r-*`): xs 4 · sm 8 · md 12 · lg 18 · xl 26 · pill 999.

---

## 6. Como isto é mantido (etapas B e A)

- **B (guardrail): ✅ FEITO.** `scripts/tokens/check-tokens.mjs §(c)` trava os selectors-chave do
  shell no `index.html`: o `font-size` DEVE ser o token do spec (`body`=--text-sm,
  `.pagehead-title`=--text-xl, `.pagehead-eyebrow`/`.nav-group`=--text-nano, `.nav-item`=--text-sm),
  nunca px literal. Off-scale → exit 1 (pre-commit barra). A tabela `SHELL_RULES` cresce conforme a
  etapa A tokeniza mais selectors.
- **A (shell compartilhado):** sidebar/pagehead/nav/cards saem do `index.html` inline e do
  `dash/layout.css` para **um CSS único** que os dois apps incluem → uma fonte só, drift impossível.
  *(a implementar, com revisão do Feca na branch)*
- **Shell runtime (`/app`):** feito na sessão 86 (Fatia 2). Host `app/static/app.html` com a
  sidebar única + os 2 apps em iframes; navegar não recarrega a casca. Não substitui a etapa A
  (o CSS ainda é duplicado nos 2 apps), mas é a unificação em runtime. Plano em
  `PLANO_CASCA_UNIFICADA.md`.
