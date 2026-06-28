# UI Reference — Planilhador (FDC Capital)

> Regras de UI da marca FDC Capital, trazidas do **Betting Dashboard** e adaptadas ao
> Planilhador (ferramenta de tela única: upload de prints → extração → grade de bilhetes).
> Fonte de verdade dos tokens: [`app/static/tokens.css`](../app/static/tokens.css)
> (espelha [`../../pack/tokens/tokens.css`](../../pack/tokens/tokens.css)).
> Atualizado: 2026-06-28 (sessão de alinhamento de marca).

---

## 1. Paleta e tokens

| Papel | Token | Valor |
|---|---|---|
| Base / fundo | `--bg` | `#0A0D12` (Platinum Black) |
| **Acento único de UI** | `--accent` | `#2E8BFF` (Electric Blue) |
| Acento claro | `--accent-2` | `#7FB2FF` |
| Positivo (resultado/PnL) | `--pos` | `#2BC07E` |
| Negativo (resultado/PnL) | `--neg` | `#E5524B` |
| Aviso | `--warn` | `#E0A21A` |
| Superfícies | `--surface` / `--surface-2` / `--elevated` | `#12161D` / `#161B22` / `#1A2029` |
| Bordas | `--line` / `--line-2` | `rgba(255,255,255,.08)` / `.05` |
| Tinta | `--ink` / `--ink-soft` / `--ink-mute` | `#EEF2F7` / `#95A1B0` / `#5E6775` |
| Steel (chips) | `--fdc-steel` | `#222831` |
| Grid de fundo | `--grid` | `rgba(255,255,255,.05)` |

**Regras de cor (invioláveis):**
- **Azul `#2E8BFF` é o único acento cromático de UI.** Nada de roxo, teal, laranja, rosa como decoração.
- **Verde e vermelho só para semântica de resultado/PnL** (W/HW = verde, L/HL = vermelho).
- **Âmbar só para aviso.**
- **Cor sempre via `var(--token)`** — nunca hex hardcoded fora do `tokens.css`.
- Para opacidades, usar os triplets RGB: `rgba(var(--accent-rgb), .12)`, idem `--pos-rgb`, `--neg-rgb`, `--warn-rgb`.

---

## 2. Tipografia

- **UI:** Manrope — `var(--font-sans)`.
- **Dados / números / labels:** JetBrains Mono — `var(--font-mono)`.
- **Assinatura FDC:** labels de seção, headers de tabela, KPIs e badges usam
  **mono + UPPERCASE + `letter-spacing` .04–.16em**, tamanho 9–11px, cor `--ink-mute`.
- **Números** (odds, stake, valores, IDs): sempre mono + `font-variant-numeric: tabular-nums`,
  **alinhados à direita** em colunas numéricas.
- Pesos Manrope disponíveis: 400 / 500 / 600 / 700 / 800.

---

## 3. Chrome e sistema

| Elemento | Regra |
|---|---|
| **Grid de fundo** | 44×44px, `var(--grid)`, baixa opacidade, via pseudo-elemento `body::before`. |
| **Scrollbar** | fina (8px), thumb `--fdc-steel`, track `--surface`, hover `--ink-mute`. |
| **Raio** | só via `--r-*` — `--r-xs` 4 · `--r-sm` 8 · `--r-md` 12 · `--r-lg` 18 · `--r-xl` 26 · `--r-pill` 999. |
| **Espaço** | escala `--sp-*` de 4px (4/8/12/16/20/24/32/40/56/80). |
| **Sombra/foco** | `--shadow-card` para cards; `--glow` para foco e menus suspensos. |
| **Easing** | `--ease: cubic-bezier(.22,1,.36,1)`. |

> **Sidebar:** no Betting Dashboard a sidebar é 220px (nav de dashboard). No Planilhador a
> sidebar é a **lista de casas/parceiros** (produto diferente) e usa **292px** — divergência
> proposital, não um desvio de marca.

---

## 4. Componentes

- **Cards:** `--surface` + `1px var(--line)` + raio `--r-sm/md`; cards de resultado com
  borda colorida (pos/neg).
- **Botões:** primário = `--accent` + `--glow` no hover; ghost = transparente + `--line`,
  hover borda `--accent`.
- **Inputs:** `--field`/`--surface-2` + `1px var(--line)` + raio `--r-sm`; foco = borda
  `--accent` (+ `--glow`).
- **Pills / toggles:** raio `--r-pill`; ativo = `--accent`, inativo = `--ink-mute`.
- **Chips de casa/esporte:** 24×24, raio 7px, fundo `--fdc-steel`, logo/emoji dessaturado
  (espec. em `REFERENCIA_CHIPS_CASAS.md` / `REFERENCIA_EMOJIS_ESPORTES.md`).
- **Badges de resultado** (`W · L · V · HW · HL`): pill mono uppercase; W/HW verde, L/HL
  vermelho, V neutro.
- **Tabelas:** header mono uppercase `--ink-mute`; linhas separadas por `--line`; números
  mono + direita.

---

## 5. Notas de migração (2026-06-28)

Alinhamento aplicado ao `index.html` nesta sessão:
- ~10 cores fora da paleta → tokens (`#36d399`, `#f5a623`, `#e53935`, 2º azul `#4A90E2`, etc.).
- Triplets `--accent-rgb / --pos-rgb / --neg-rgb / --warn-rgb` adicionados ao `tokens.css`;
  todos os `rgba()` de acento/resultado derivam deles.
- Scrollbar de marca adicionada (antes usava a do navegador).
- Bordas do bloco Polymarket: `var(--grid)` → `var(--line)`; raios `10px` → `--r-sm`.
- 9 labels com a assinatura FDC ganharam `var(--font-mono)`.
- Bug corrigido: `var(--surface2,#2a2a2a)` / `var(--border,#333)` referenciavam tokens
  inexistentes (caíam em cinza off-brand) → `--surface-2` / `--line`.

- `.btbl-num` (Stake/Odd da Lista de Apostas) → `text-align:right` + headers "Stake"/"Odd"
  com `.right`, igualando a grade de extração (que já alinhava números à direita).
