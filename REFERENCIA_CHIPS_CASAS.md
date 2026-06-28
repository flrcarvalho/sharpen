# Referência — Chips de Casas (favicons) e Tabela "POR CASA"

> Extraído do **Betting Dashboard** (popup de drill-down de tipster → seção "Por Casa").
> Especificação completa e **autocontida** (valores já resolvidos, sem depender de tokens CSS),
> pronta para replicar em outro projeto.

---

## 1. Estrutura HTML de uma célula de casa

Cada linha da tabela tem, na 1ª coluna, o chip do favicon + o nome:

```html
<span style="display:inline-flex;align-items:center;gap:6px">
  <span class="house-chip" data-initial="B" data-casa="Bet365">
    <img src="https://www.google.com/s2/favicons?domain=bet365.com&sz=64" alt="Bet365">
  </span>
  Bet365
</span>
```

- `gap` entre chip e nome: **6px**
- `align-items:center`

---

## 2. Favicon (chip da casa)

### URL do favicon — padrão Google S2, sempre `sz=64`
```
https://www.google.com/s2/favicons?domain={DOMINIO}&sz=64
```

| Casa            | Domínio              |
|-----------------|----------------------|
| Bet365          | bet365.com           |
| Betano          | betano.com           |
| Rei do Pitaco   | reidopitaco.com.br   |
| Superbet        | superbet.com         |
| Betfair         | betfair.com          |
| Novibet         | novibet.com          |
| PixBet          | pixbet.com           |

### CSS do container `.house-chip`
```css
.house-chip {
  width: 24px; height: 24px;
  border-radius: 7px;
  background: #222831;                       /* steel */
  border: 1px solid rgba(255,255,255,0.08);  /* hairline dark */
  display: inline-grid; place-items: center;
  flex: none;
  overflow: hidden;
}
```

### CSS da imagem — o "segredo" do cinza uniforme
```css
.house-chip img {
  width: 100%; height: 100%;
  object-fit: cover;
  display: block;
  /* dessatura + normaliza logos de fundo escuro para ~#50 cinza */
  filter: grayscale(1) contrast(0.5) brightness(1.25);
}
```

### Exceções por casa
```css
/* logos circulares com margem transparente → corta a borda */
.house-chip[data-casa="Novibet"] img,
.house-chip[data-casa="PixBet"]  img,
.house-chip[data-casa="Esportiva"] img { transform: scale(1.3); }

/* logo clara em fundo escuro: só clareia, sem reduzir contraste */
.house-chip[data-casa="KTO"]    img,
.house-chip[data-casa="BetMGM"] img { filter: grayscale(1) brightness(1.8); }

/* fundo branco: inverte e funde com o chip escuro */
[data-theme="dark"] .house-chip[data-casa="BETesporte"] img {
  filter: grayscale(1) invert(1) brightness(1.4);
  mix-blend-mode: screen;
}
```
> Das casas acima, **Novibet** e **PixBet** usam `transform: scale(1.3)`.

### Fallback (favicon não carrega)
A `<img>` é trocada por `<span class="chip-initial">` com a inicial maiúscula:
```css
.chip-initial {
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 11px;
  color: #95A1B0;
}
```
O `.chip-initial` herda o box do `.house-chip` (24×24, fundo steel, borda).
Troca via event delegation (sem `onerror` inline):
```js
document.addEventListener('error', e => {
  const chip = e.target.closest?.('.house-chip');
  if (chip && e.target.tagName === 'IMG') {
    const init = chip.dataset.initial || '?';
    e.target.replaceWith(Object.assign(
      document.createElement('span'),
      { className: 'chip-initial', textContent: init }
    ));
  }
}, true);
```

---

## 3. Fontes

| Elemento                      | Fonte           | Tamanho / peso                                                  |
|-------------------------------|-----------------|----------------------------------------------------------------|
| Nome da casa ("Bet365")       | Manrope         | 12px, normal                                                   |
| Números ("1.167") `.td-num`   | JetBrains Mono  | 12px, `tabular-nums`                                           |
| Cabeçalho ("CASA","BETS")     | Manrope         | 11px, 700, UPPERCASE, `letter-spacing:0.12em`, cor `#95A1B0`   |
| Título da seção ("POR CASA")  | Manrope         | 12px, 700, UPPERCASE, `letter-spacing:0.05em`, cor `#7FB2FF`   |

```css
--font-sans: "Manrope", "Inter", system-ui, -apple-system, sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, "SF Mono", monospace;
```
Separador de milhar pt-BR (`1.167`): `(n).toLocaleString('pt-BR')`.

---

## 4. Tabela `.tbl`

```css
.tbl {
  width: 100%;
  font-size: 12px;
  border-collapse: collapse;
  font-family: "Manrope", sans-serif;
  font-variant-numeric: tabular-nums;
}
.tbl th {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #95A1B0;
}
.tbl td {
  padding: 7px 10px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  color: #95A1B0;
  white-space: nowrap;
}
.tbl tr:last-child td { border-bottom: none; }

/* zebra + hover */
.tbl tbody tr:nth-child(even) td { background: rgba(255,255,255,0.015); }
.tbl tbody tr:hover td           { background: rgba(46,139,255,0.05); }

/* colunas numéricas → mono + à direita */
.tbl td.td-num {
  text-align: right !important;
  font-family: "JetBrains Mono", monospace;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}
```

### Setinha de ordenação no cabeçalho (▲)
```html
<th class="th-r"><span class="th-k">BETS<span class="sort-icon"></span></span></th>
```
```css
.sort-icon { display:inline-flex; align-items:center; justify-content:center;
             margin-left:5px; width:12px; height:12px; opacity:0.3; }
.sort-icon::after {
  content:''; display:inline-block; width:0; height:0;
  border-left:4px solid transparent; border-right:4px solid transparent;
  border-bottom:5px solid currentColor;
}
.sort-asc .sort-icon, .sort-desc .sort-icon { opacity:1; color:#2E8BFF; }
```

### Caixa do popup (container em volta da tabela)
```css
.analise-popup-section {
  background: #161B22;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  padding: 20px 24px;
  backdrop-filter: blur(8px);
}
.analise-popup-section-title {  /* "POR CASA" */
  font-size: 12px;
  color: #7FB2FF;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}
```

---

## 5. Paleta (modo dark — valores já resolvidos)

| Uso                       | Valor                      |
|---------------------------|----------------------------|
| Fundo do chip (steel)     | `#222831`                  |
| Borda chip / seção        | `rgba(255,255,255,0.08)`   |
| Divisória entre linhas    | `rgba(255,255,255,0.06)`   |
| Texto tabela / cabeçalho  | `#95A1B0`                  |
| Título "POR CASA"         | `#7FB2FF`                  |
| Fundo da caixa do popup   | `#161B22`                  |
| Hover de linha            | `rgba(46,139,255,0.05)`    |
| Setinha de ordenação ativa| `#2E8BFF`                  |

---

## 6. Exemplo mínimo completo (copiar e colar)

```html
<!DOCTYPE html>
<html lang="pt-BR" data-theme="dark">
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  body { background:#0E1116; margin:0; padding:24px; }
  .house-chip { width:24px; height:24px; border-radius:7px; background:#222831;
    border:1px solid rgba(255,255,255,0.08); display:inline-grid; place-items:center;
    flex:none; overflow:hidden; }
  .house-chip img { width:100%; height:100%; object-fit:cover; display:block;
    filter:grayscale(1) contrast(0.5) brightness(1.25); }
  .house-chip[data-casa="Novibet"] img,
  .house-chip[data-casa="PixBet"] img { transform:scale(1.3); }
  .chip-initial { font-family:"JetBrains Mono",monospace; font-size:11px; color:#95A1B0; }

  .analise-popup-section { background:#161B22; border:1px solid rgba(255,255,255,0.08);
    border-radius:18px; padding:20px 24px; max-width:380px; }
  .analise-popup-section-title { font-family:"Manrope",sans-serif; font-size:12px;
    color:#7FB2FF; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;
    margin-bottom:0.75rem; }

  .tbl { width:100%; font-size:12px; border-collapse:collapse;
    font-family:"Manrope",sans-serif; font-variant-numeric:tabular-nums; }
  .tbl th { font-size:11px; font-weight:700; text-transform:uppercase;
    letter-spacing:0.12em; color:#95A1B0; padding:7px 10px; }
  .tbl th.th-r { text-align:right; } .tbl th.th-l { text-align:left; }
  .tbl td { padding:7px 10px; border-bottom:1px solid rgba(255,255,255,0.06);
    color:#95A1B0; white-space:nowrap; }
  .tbl tr:last-child td { border-bottom:none; }
  .tbl tbody tr:nth-child(even) td { background:rgba(255,255,255,0.015); }
  .tbl tbody tr:hover td { background:rgba(46,139,255,0.05); }
  .tbl td.td-num { text-align:right; font-family:"JetBrains Mono",monospace;
    font-variant-numeric:tabular-nums; font-feature-settings:"tnum"; }
  .casa-cell { display:inline-flex; align-items:center; gap:6px; }
</style>
</head>
<body>
  <div class="analise-popup-section">
    <div class="analise-popup-section-title">Por Casa</div>
    <table class="tbl">
      <thead><tr><th class="th-l">Casa</th><th class="th-r">Bets</th></tr></thead>
      <tbody>
        <tr>
          <td><span class="casa-cell"><span class="house-chip" data-initial="B" data-casa="Bet365"><img src="https://www.google.com/s2/favicons?domain=bet365.com&sz=64" alt="Bet365"></span>Bet365</span></td>
          <td class="td-num">1.167</td>
        </tr>
        <tr>
          <td><span class="casa-cell"><span class="house-chip" data-initial="B" data-casa="Betano"><img src="https://www.google.com/s2/favicons?domain=betano.com&sz=64" alt="Betano"></span>Betano</span></td>
          <td class="td-num">374</td>
        </tr>
        <tr>
          <td><span class="casa-cell"><span class="house-chip" data-initial="R" data-casa="Rei do Pitaco"><img src="https://www.google.com/s2/favicons?domain=reidopitaco.com.br&sz=64" alt="Rei do Pitaco"></span>Rei do Pitaco</span></td>
          <td class="td-num">17</td>
        </tr>
        <tr>
          <td><span class="casa-cell"><span class="house-chip" data-initial="N" data-casa="Novibet"><img src="https://www.google.com/s2/favicons?domain=novibet.com&sz=64" alt="Novibet"></span>Novibet</span></td>
          <td class="td-num">49</td>
        </tr>
      </tbody>
    </table>
  </div>
  <script>
    document.addEventListener('error', e => {
      const chip = e.target.closest && e.target.closest('.house-chip');
      if (chip && e.target.tagName === 'IMG') {
        const init = chip.dataset.initial || '?';
        e.target.replaceWith(Object.assign(document.createElement('span'),
          { className: 'chip-initial', textContent: init }));
      }
    }, true);
  </script>
</body>
</html>
```
