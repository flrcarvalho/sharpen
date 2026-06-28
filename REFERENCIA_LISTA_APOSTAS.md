# Referência — Lista de Apostas (espelho da base / scroll virtual)

> Extraído do **Betting Dashboard** (página "Apostas" → tabela linha a linha `.btbl-*`).
> Especificação completa e **autocontida** (valores já resolvidos, sem depender de tokens CSS),
> pronta para replicar em outro projeto.

---

## 1. Visão geral da arquitetura

- Tabela construída com **CSS Grid** (não `<table>`): header e linhas de dado compartilham o
  **mesmo `grid-template-columns`** → colunas sempre alinhadas.
- **9 colunas:** Data · Aposta/Evento · Esporte · Tipster · Casa·Parceiro · Stake · Odd · Resultado · P/L
- **Scroll virtual:** só renderiza as linhas visíveis + buffer de 10. Altura de linha fixa **68px**.
- Header fixo no topo (38px) + contador ("22.381 de 22.381 apostas") logo abaixo.

### Template de colunas (idêntico no header e nas linhas)
```css
grid-template-columns: 80px 1fr 108px 114px 168px 92px 68px 80px 108px;
gap: 0 12px;
padding: 0 22px;
```
| # | Coluna            | Largura |
|---|-------------------|---------|
| 1 | Data              | 80px    |
| 2 | Aposta / Evento   | 1fr (flexível) |
| 3 | Esporte           | 108px   |
| 4 | Tipster           | 114px   |
| 5 | Casa · Parceiro   | 168px   |
| 6 | Stake             | 92px    |
| 7 | Odd               | 68px    |
| 8 | Resultado         | 80px    |
| 9 | P/L               | 108px   |

---

## 2. HTML — header (linha de títulos)

```html
<div class="btbl-wrap">
  <div class="btbl-cols btbl-hdr-row">
    <div class="btbl-th sortable" data-col="0">Data <span class="sort-arrow">↓</span></div>
    <div class="btbl-th">Aposta / Evento</div>
    <div class="btbl-th">Esporte</div>
    <div class="btbl-th">Tipster</div>
    <div class="btbl-th">Casa · Parceiro</div>
    <div class="btbl-th sortable" data-col="7">Stake <span class="sort-arrow">↕</span></div>
    <div class="btbl-th sortable" data-col="8">Odd <span class="sort-arrow">↕</span></div>
    <div class="btbl-th">Resultado</div>
    <div class="btbl-th sortable" data-col="10" style="text-align:right">P/L <span class="sort-arrow">↕</span></div>
  </div>
  <div class="btbl-counter">22.381 de 22.381 apostas</div>
  <!-- linhas virtualizadas aqui -->
</div>
```
- Setas de ordenação: `↓` (coluna ativa desc), `↑` (asc), `↕` (inativa). Data começa ativa `↓`.

---

## 3. HTML — linha de dado

```html
<div class="btbl-cols btbl-data-row" style="height:68px">
  <div class="btbl-cell btbl-date">27/06/2026</div>
  <div class="btbl-cell">
    <div class="btbl-tipo">MÚLTIPLA</div>          <!-- só se houver "aposta" (tipo) -->
    <div class="btbl-desc">Uzbequistão - Over 10.5 Chutes [RD Congo v Uzbequistão] // ...</div>
  </div>
  <div class="btbl-cell btbl-sport"><span class="sp-chip">⚽</span><span>Futebol</span></div>
  <div class="btbl-cell btbl-tipster">Arrudex</div>
  <div class="btbl-cell btbl-casa">
    <span class="house-chip" data-casa="Betano"><img src="..." alt="Betano"></span>
    <div class="btbl-casa-sub">
      <span class="btbl-casa-nome">Betano</span>
      <span class="btbl-casa-conta">leudeson15 [P2Pro]</span>  <!-- parceiro, se houver -->
    </div>
  </div>
  <div class="btbl-cell btbl-num"><span class="money"><span class="money-sign">R$</span><span class="money-val">25</span></span></div>
  <div class="btbl-cell btbl-num">34,22</div>
  <div class="btbl-cell" style="display:flex;align-items:center;justify-content:center">
    <span class="bet-res-pill bet-res-L">L</span>
  </div>
  <div class="btbl-cell btbl-pl"><span class="money neg"><span class="money-sign">−R$</span><span class="money-val">25,00</span></span></div>
</div>
```

> **Chips:** o chip de esporte (`.sp-chip`) e o chip de casa (`.house-chip`) seguem exatamente a
> mesma especificação do arquivo **REFERENCIA_CHIPS_CASAS.md** (24×24, raio 7px, fundo `#222831`,
> filtro grayscale). Veja aquele arquivo para a URL de favicon e exceções por casa.

---

## 4. Fontes por elemento

| Elemento                         | Fonte           | Tamanho | Peso | Cor (dark) | Observações |
|----------------------------------|-----------------|---------|------|-----------|-------------|
| Header (`.btbl-th`)              | JetBrains Mono  | 9px     | normal | `#5E6775` | UPPERCASE, `letter-spacing:0.14em` |
| Contador (`.btbl-counter`)       | JetBrains Mono  | 9px     | normal | `#5E6775` | UPPERCASE-ish, `letter-spacing:0.08em`, à direita |
| Data (`.btbl-date`)              | JetBrains Mono  | 11px    | normal | `#5E6775` | — |
| Tipo da aposta (`.btbl-tipo`)    | JetBrains Mono  | 9px     | 700  | `#2E8BFF` (azul) | UPPERCASE, `letter-spacing:0.1em` ("MÚLTIPLA","OUTROS") |
| Descrição (`.btbl-desc`)         | Manrope         | 12px    | normal | `#EEF2F7` | truncada com `…` |
| Esporte (`.btbl-sport`)          | Manrope         | 11px    | normal | `#95A1B0` | chip + texto, `gap:6px` |
| Tipster (`.btbl-tipster`)        | Manrope         | 11px    | normal | `#95A1B0` | truncado |
| Nome da casa (`.btbl-casa-nome`) | Manrope         | 11px    | normal | `#EEF2F7` | — |
| Parceiro (`.btbl-casa-conta`)    | JetBrains Mono  | 9px     | normal | `#5E6775` | sob o nome da casa |
| Stake / Odd (`.btbl-num`)        | JetBrains Mono  | 12px    | normal | `#EEF2F7` | `tabular-nums`, à direita |
| P/L (`.btbl-pl`)                 | JetBrains Mono  | 12px    | **700** | verde/vermelho | `tabular-nums`, à direita |
| Pílula resultado (`.bet-res-pill`)| JetBrains Mono | 10px    | 700  | conforme resultado | UPPERCASE, `letter-spacing:0.04em` |

```css
--font-sans: "Manrope", "Inter", system-ui, -apple-system, sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, "SF Mono", monospace;
```

---

## 5. CSS completo (valores já resolvidos — modo dark)

```css
/* container */
.btbl-wrap {
  background: #12161D;                       /* --surface */
  border: 1px solid rgba(255,255,255,0.08);  /* --line */
  border-radius: 18px;
  overflow: hidden;
}

/* grid compartilhado header + linhas */
.btbl-cols {
  display: grid;
  grid-template-columns: 80px 1fr 108px 114px 168px 92px 68px 80px 108px;
  gap: 0 12px;
  padding: 0 22px;
  box-sizing: border-box;
  align-items: center;
}

/* header */
.btbl-hdr-row {
  height: 38px;
  background: #161B22;                        /* --surface-2 */
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.btbl-th {
  font-family: "JetBrains Mono", monospace;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #5E6775;                            /* --ink-mute */
  white-space: nowrap;
  user-select: none;
}
.btbl-th.sortable { cursor: pointer; display: inline-flex; align-items: center; gap: 3px; }
.btbl-th.sortable:hover { color: #95A1B0; } /* --ink-soft */
.btbl-th.sort-active     { color: #EEF2F7; } /* --ink */
.btbl-th .sort-arrow { font-size: 8px; }

/* contador */
.btbl-counter {
  font-family: "JetBrains Mono", monospace;
  font-size: 9px;
  color: #5E6775;
  letter-spacing: 0.08em;
  text-align: right;
  padding: 8px 22px 6px;
}

/* linha de dado */
.btbl-data-row {
  height: 68px;
  border-bottom: 1px solid rgba(255,255,255,0.028);
  transition: background 0.1s;
}
.btbl-data-row:hover { background: rgba(46,139,255,0.04); }
.btbl-cell { min-width: 0; overflow: hidden; }

/* coluna Data */
.btbl-date {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  color: #5E6775;
  white-space: nowrap;
  line-height: 1.4;
}

/* coluna Aposta/Evento */
.btbl-tipo {
  font-family: "JetBrains Mono", monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #2E8BFF;                            /* --accent */
  margin-bottom: 3px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.btbl-desc {
  font-size: 12px;
  color: #EEF2F7;                            /* --ink */
  line-height: 1.35;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* coluna Esporte */
.btbl-sport {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11px;
  color: #95A1B0;                            /* --ink-soft */
  white-space: nowrap; overflow: hidden;
}

/* coluna Tipster */
.btbl-tipster {
  font-size: 11px;
  color: #95A1B0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* coluna Casa · Parceiro */
.btbl-casa {
  display: inline-flex; align-items: center; gap: 8px;
  min-width: 0; overflow: hidden;
}
.btbl-casa-sub { display: flex; flex-direction: column; min-width: 0; overflow: hidden; }
.btbl-casa-nome {
  font-size: 11px;
  color: #EEF2F7;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.btbl-casa-conta {
  font-family: "JetBrains Mono", monospace;
  font-size: 9px;
  color: #5E6775;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* colunas numéricas (Stake, Odd) */
.btbl-num {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: #EEF2F7;
  white-space: nowrap; text-align: right;
}

/* coluna P/L */
.btbl-pl {
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  white-space: nowrap; text-align: right;
}
```

---

## 6. Pílula de resultado (`.bet-res-pill`)

```css
.bet-res-pill {
  display: inline-flex; align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  font-family: "JetBrains Mono", monospace;
  white-space: nowrap;
  letter-spacing: 0.04em;
}
.bet-res-W  { background: rgba(43,192,126,0.15); color: #2BC07E; border: 1px solid rgba(43,192,126,0.30); }
.bet-res-HW { background: rgba(43,192,126,0.12); color: #2BC07E; border: 1px solid rgba(43,192,126,0.25); }
.bet-res-L  { background: rgba(229,82,75,0.13);  color: #E5524B; border: 1px solid rgba(229,82,75,0.25); }
.bet-res-HL { background: rgba(229,82,75,0.12);  color: #E5524B; border: 1px solid rgba(229,82,75,0.25); }
.bet-res-V  { background: rgba(128,128,128,0.10); color: #5E6775; border: 1px solid rgba(255,255,255,0.08); }
```

| Código | Rótulo exibido | Significado |
|--------|----------------|-------------|
| `W`    | `W`            | Win (verde)         |
| `HW`   | `½W`           | Half win (verde)    |
| `L`    | `L`            | Loss (vermelho)     |
| `HL`   | `½L`           | Half loss (vermelho)|
| `V`    | `V`            | Void / devolvida (cinza) |

---

## 7. Formatação de valores (R$ / Odd)

A coluna **Stake** e a **P/L** usam o mesmo componente `.money` (sinal e número em cores separadas):

```html
<!-- Stake: R$ neutro -->
<span class="money"><span class="money-sign">R$</span><span class="money-val">25</span></span>

<!-- P/L positivo -->
<span class="money pos"><span class="money-sign">+R$</span><span class="money-val">358,40</span></span>

<!-- P/L negativo -->
<span class="money neg"><span class="money-sign">−R$</span><span class="money-val">25,00</span></span>
```
```css
.money {
  display: inline-flex; justify-content: flex-end; gap: 4px;
  width: 100%;
  font-family: "JetBrains Mono", monospace;
}
.money-sign { min-width: 2ch; text-align: right; flex-shrink: 0; font-size: 0.76em; }
.money-val  { text-align: right; font-variant-numeric: tabular-nums; min-width: 10ch; }

.money.pos { color: #2BC07E; }   /* número verde */
.money.neg { color: #E5524B; }   /* número vermelho */
/* o "R$"/sinal fica SEMPRE neutro, independente de pos/neg */
.money.pos .money-sign,
.money.neg .money-sign { color: #95A1B0; }
```

### Regras de formatação (JS)
- **Sinal:** `+` para ≥0, `−` (minus tipográfico U+2212, **não** hífen) para <0. Colado ao `R$`.
- **Moeda:** `valor.toLocaleString('pt-BR', {minimumFractionDigits, maximumFractionDigits})`.
  - Stake: **0 casas** (`R$ 25`). P/L: **2 casas** (`R$ 358,40`).
- **Odd:** sempre **2 casas** pt-BR → `34,22` (`toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})`).
- **Data:** `DD/MM/AAAA` a partir de ISO `AAAA-MM-DD`.
- **Contador:** `n.toLocaleString('pt-BR')` → separador de milhar `22.381`.

---

## 8. Paleta (modo dark — valores já resolvidos)

| Uso                         | Valor                       |
|-----------------------------|-----------------------------|
| Fundo container             | `#12161D` (--surface)       |
| Fundo header                | `#161B22` (--surface-2)     |
| Borda container/header      | `rgba(255,255,255,0.08)`    |
| Divisória entre linhas      | `rgba(255,255,255,0.028)`   |
| Hover de linha              | `rgba(46,139,255,0.04)`     |
| Texto forte (desc, casa, num)| `#EEF2F7` (--ink)          |
| Texto médio (esporte/tipster)| `#95A1B0` (--ink-soft)     |
| Texto fraco (data/parceiro/header)| `#5E6775` (--ink-mute) |
| Azul (tipo da aposta)       | `#2E8BFF` (--accent)        |
| Verde (W/HW, P/L+)          | `#2BC07E` (--pos)           |
| Vermelho (L/HL, P/L−)       | `#E5524B` (--neg)           |
| Fundo do chip (steel)       | `#222831`                   |

---

## 9. Scroll virtual (lógica essencial)

- Altura de linha fixa: `BTBL_ROW_H = 68`.
- A cada scroll: calcula `startIdx`/`endIdx` a partir de `scrollTop`, `clientHeight` e um buffer de 10 linhas.
- Renderiza só as linhas do intervalo + dois espaçadores (`.virt-spacer`) para preservar a altura total:
  - `topPad = startIdx * 68`
  - `botPad = (total - endIdx) * 68`
- Listener: `onscroll` com `requestAnimationFrame` (re-render no máx. 1×/frame).
```css
.virt-spacer { pointer-events: none; }
```
> Se a lista do outro projeto for pequena (< ~500 linhas), pode dispensar o scroll virtual e
> renderizar tudo direto — todo o HTML/CSS acima funciona igual sem os espaçadores.
