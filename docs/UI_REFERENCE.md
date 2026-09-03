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
- **Campo de data (regra desde a s246):** todo campo de data usa o **SharpenCal**
  (`app/static/sharpen-cal.js`) — botão de ícone + `SharpenCal.abrir(anchor, valor, onPick,
  {saida:'br'|'iso'})`, input segue digitável. Em `type=date`, embrulhar em `.shcal-datewrap`
  (esconde o indicador nativo) e despachar `change` no onPick. **Nunca** usar o popup nativo
  do Chrome (sem marca, e `showPicker()` de input escondido falha em silêncio) nem criar um
  segundo calendário.

---

## 5. Padrão monetário (R$ e P/L)

> Fonte de verdade: helpers `fmt` / `fmtPL` / `fmtR` do Betting Dashboard
> (`assets/js/app.js`) e a classe `.money` em `assets/css/components.css`.
> O Planilhador apenas espelha — não reinventa a máscara.

### 5.1 — Um componente, duas variações (por contexto)

**Todo valor em R$ usa o componente `.money`** — nunca string crua (`'R$ ' + x`).
O `.money` sempre entrega: `R$`/sinal **neutros e menores** (`.money-sign`,
`--ink-soft`, `~0.78em`) + o número em `.money-val` (mono, `tabular-nums`), com
**cor só no número**. O que muda entre um caso e outro é **só as casas decimais e o
sinal**, conforme o contexto:

| Contexto | Helper | Casas | Sinal |
|---|---|---|---|
| **P/L** (célula de tabela **e** KPI) | `fmtPL(v)` | **2** | `+R$`/`−R$` colado, minus **U+2212**, **zero neutro** (`R$ 0,00` sem sinal/cor) |
| **Agregado / KPI / resumo** — turnover, totais, custos | `fmtR(v)` | **0 (inteiro)** | sem sinal |
| **Stake / valor unitário** | `moneyStake(v)` / `.money` | 2 | sem sinal |
| **Saldo de conta** (Caixa Inteligente) | `fmtSaldo(v[, sinal])` | **2** | sem sinal; com `sinal=true` para movimento (`+R$`/`−R$`, minus **U+2212**), **zero neutro** |

> **Regra de decisão (fim da ambiguidade):** é P/L? → `fmtPL` (2 casas). É um
> agregado/total/turnover/custo? → `fmtR` (**inteiro**). É saldo de conta? →
> `fmtSaldo` (2 casas). Não existe outra máscara de R$; contexto novo que não se
> encaixe → **perguntar ao Feca**.

> **Por que saldo tem 2 casas e não é `fmtR`** (decidido com o Feca na s314): o número
> existe para ser **conferido contra o extrato da casa**, e o centavo é exatamente a
> divergência que se procura — arredondar para inteiro esconderia o que a tela existe
> para achar. Entra na régua do `moneyStake`, não na dos agregados.
>
> **E saldo NÃO tem cor.** Verde e vermelho são semântica de **resultado**: saque não é
> prejuízo e depósito não é lucro. O sinal fica no `.money-sign`, que já é neutro por
> construção. Na Caixa Inteligente, a única linha colorida é o **Resultado**, que é P/L de verdade e
> usa o `fmtPL`. **Divergência de conferência é `--warn`** (aviso), nunca `--neg`:
> dinheiro que saiu sem registro é alerta, não resultado negativo.

### 5.2 — Invariantes (valem nas duas variações)

- **Número pt-BR:** milhar `.`, decimal `,` (ex.: `1.234,50` / `18.912`).
- **Nunca abreviar** milhar (`k`/`M`/`mil`) — **barrado pelo `check-tokens §(d)`** (pre-commit).
- **Cor** verde (`--pos`) / vermelho (`--neg`) **só no `.money-val`**; `R$` e sinal neutros.
- **Cor sempre de token** (`var(--…)`), nunca literal.
- **Mono + `tabular-nums`, à direita** (§2).
- **Cabeçalho PT-BR:** `"P/L"`, `"Turnover"` (termo do produto) — nunca `"PROFIT"`.
- **Backend entrega número cru** (ex.: `81.0`, `-100.0`); a máscara é exclusiva da UI.

### 5.3 — Exceções (não são R$ / têm helper próprio)

- **%** → `fmtPct(v)` (cor por sinal é OK; **não** é dinheiro, não segue as regras de R$).
- **Odd** → `fmtOdd(v)` (2 casas, **sem** `R$`).
- **USD (Polymarket)** → `fmtUSD(v)` / `fmtBRLsub(v,cot)` (`$ …` / `≈ R$ …`).
- ⚠️ O `fmtOdd`/odd do extrator e o `fmtUSD`/`fmtBRLsub` usam `.toFixed().replace()`
  — a **única** exceção tolerada à regra "sem `.toFixed`/`.replace` no display",
  porque são caminhos isolados (odd/USD) que **não** passam pelo `.money`. **Não
  replicar esse padrão em R$** — R$ é sempre `.money` via `fmtPL`/`fmtR`.

### 5.4 — Desvio conhecido (tech-debt, NÃO copiar)

Alguns KPIs do `charts/gestao.js` e o `metricsKPI` montam dinheiro com
`'R$ ' + fmt(v,0)` **cru** (fora do `.money`) → o `R$` não fica menor/neutro e a
cor do KPI pinta o `R$` junto do número. Devem migrar para `fmtR`/`fmtPL`. **Código
novo não deve copiar** — é a origem histórica da confusão "qual padrão usar".

---

## 6. Notas de migração (2026-06-28)

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
