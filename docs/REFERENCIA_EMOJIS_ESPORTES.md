# Referência — Chips e Emojis de Esportes

> Extraído do **Betting Dashboard** (chip de esporte `.sp-chip` + mapas `SPORT_KEY` / `SPORT_EMOJI` / `SPORT_SVG`).
> Especificação completa e **autocontida**, pronta para replicar em outro projeto.

---

## 1. Como funciona (visão geral)

1. O nome do esporte (texto livre, ex.: "Futebol", "NBA", "CS:GO") é **normalizado** para uma
   **chave canônica** via `SPORT_KEY` (alias map — várias grafias → mesma chave).
2. A chave canônica aponta para um **emoji** (`SPORT_EMOJI`) ou um **ícone SVG** (`SPORT_SVG`).
3. O emoji é exibido dentro de um chip `.sp-chip` (24×24, igual ao chip de casa, porém com emoji).
4. **Fallback obrigatório:** esporte desconhecido → emoji `🏅` (nunca `•`, nunca `?`).

> Regra de marca: o glifo de múltiplas/combinadas é `🔗` — `🎰` (cassino) é **proibido**.

---

## 2. Chip de esporte (`.sp-chip`)

### HTML
```html
<span class="sp-chip">⚽</span>
<!-- com texto ao lado (sportCell): -->
<span style="display:inline-flex;align-items:center;gap:6px">
  <span class="sp-chip">⚽</span>Futebol
</span>
```

### CSS (valores já resolvidos — modo dark)
```css
.sp-chip {
  width: 24px; height: 24px;
  border-radius: 7px;
  background: #222831;                       /* --fdc-steel */
  border: 1px solid rgba(255,255,255,0.08);  /* --line */
  display: inline-grid; place-items: center;
  flex: none;
  font-size: 14px;
  line-height: 1;
  filter: grayscale(1);                      /* emoji dessaturado (cinza) */
}
```
> Mesma "casca" do `.house-chip` (24×24, raio 7px, fundo steel). A diferença: `.sp-chip` mostra
> **emoji** com `font-size:14px` + `filter:grayscale(1)` direto no elemento; `.house-chip` mostra `<img>`.

### Classe legada `.sport-emoji`
Ainda usada apenas em **labels de gráfico** (Chart.js). Em tabelas/cards/listas, usar `.sp-chip`.
```css
.sport-emoji { filter: grayscale(1); }
```

---

## 3. Tabela de esportes → emoji

| Chave canônica | Emoji | Esporte |
|----------------|-------|---------|
| `futebol`   | ⚽   | Futebol |
| `basquete`  | 🏀   | Basquete / NBA |
| `tenis`     | 🎾   | Tênis (inclui tênis de mesa / ping pong) |
| `mma`       | 🥊   | MMA / UFC / Boxe |
| `f1`        | 🏎️   | Fórmula 1 |
| `nfl`       | 🏈   | NFL / Futebol Americano |
| `nhl`       | 🏒   | NHL / Hóquei |
| `baseball`  | ⚾   | MLB / Baseball |
| `volei`     | 🏐   | Vôlei |
| `handbol`   | 🤾   | Handebol |
| `dardos`    | 🎯   | Dardos / Darts |
| `badminton` | 🏸   | Badminton (BWF) |
| `esports`   | 🎮   | E-Sports / CS:GO |
| `multiplos` | 🔗   | Múltiplos / combinadas |
| `peixe`     | 🐟   | "Peixe" (categoria interna) |
| `snooker`   | 🎱   | Snooker / sinuca |
| `golf`      | ⛳   | Golfe |
| `rugby`     | 🏉   | Rugby (também usado p/ Cricket) |
| *(fallback)* | 🏅  | Qualquer esporte sem chave |

---

## 4. Alias map (`SPORT_KEY`) — normalização nome → chave

Várias grafias caem na mesma chave. A busca é **case-insensitive** (se não achar exato,
procura ignorando maiúsc./minúsc.).

```js
const SPORT_KEY = {
  'Futebol':'futebol','Fútbol':'futebol','Soccer':'futebol',
  'NBA':'basquete','Basquete':'basquete','Basquetebol':'basquete','Basketball':'basquete','Nba':'basquete',
  'Tênis':'tenis','Tenis':'tenis','Tennis':'tenis','Tênis de Mesa':'tenis','Ping Pong':'tenis',
  'Badminton':'badminton','Badmington':'badminton',
  'MMA':'mma','UFC':'mma','Boxe':'mma','Boxing':'mma','Luta':'mma',
  'F1':'f1','Formula 1':'f1','Fórmula 1':'f1','Formula1':'f1',
  'NFL':'nfl','Futebol Americano':'nfl',
  'NHL':'nhl','Hóquei':'nhl','Hockey':'nhl',
  'MLB':'baseball','Baseball':'baseball','Beisebol':'baseball',
  'Vôlei':'volei','Volei':'volei','Volleyball':'volei',
  'Handeball':'handbol','Handebol':'handbol','Handball':'handbol',
  'Dardos':'dardos','Darts':'dardos',
  'CS':'esports','CS:GO':'esports','Counter-Strike':'esports','E-Sports':'esports','Esports':'esports','eSports':'esports',
  'Multiplos':'multiplos','Múltiplos':'multiplos','Multiple':'multiplos',
  'Peixe':'peixe','Fish':'peixe',
  'Snooker':'snooker',
  'Golf':'golf','Golfe':'golf',
  'Rugby':'rugby','Cricket':'rugby',
  'Outro':'outro','Other':'outro','Outros':'outro',
};

const SPORT_EMOJI = {
  futebol:'⚽', basquete:'🏀', tenis:'🎾', mma:'🥊', f1:'🏎️',
  nfl:'🏈', nhl:'🏒', baseball:'⚾', volei:'🏐', handbol:'🤾',
  dardos:'🎯', esports:'🎮', multiplos:'🔗', peixe:'🐟',
  snooker:'🎱', golf:'⛳', rugby:'🏉', badminton:'🏸',
};
```

---

## 5. Helpers (JS)

```js
// nome livre → chave canônica (case-insensitive)
function _sportKey(nome){
  let key = SPORT_KEY[nome];
  if(!key){
    const k = Object.keys(SPORT_KEY).find(k => k.toLowerCase() === (nome||'').toLowerCase());
    key = k ? SPORT_KEY[k] : null;
  }
  return key;
}

// chip pronto (emoji dentro de .sp-chip). Fallback 🏅.
function mkSpChip(sport){
  const key = _sportKey(sport);
  return `<span class="sp-chip" style="filter:grayscale(1)">${SPORT_EMOJI[key] || '🏅'}</span>`;
}

// só o emoji (sem chip). Fallback 🏅.
function sportEmoji(nome){
  if(!nome) return '🏅';
  const key = _sportKey(nome);
  return SPORT_EMOJI[key] || '🏅';
}

// chip + texto ao lado
function sportCell(nome){
  const key = _sportKey(nome);
  const emoji = SPORT_EMOJI[key] || '🏅';
  return `<span style="display:inline-flex;align-items:center;gap:6px"><span class="sp-chip">${emoji}</span>${nome||'—'}</span>`;
}
```

> No dashboard, `mkSpChip` aplica `filter:grayscale(1)` inline (além do CSS) para garantir o cinza
> mesmo quando o chip é exportado em PNG (html2canvas).

---

## 6. Variante em SVG (opcional — ícone de linha)

Além do emoji, existe um conjunto de **ícones SVG monocromáticos** (estilo linha, `stroke=currentColor`)
para contextos onde o emoji não fica nítido. Mesma normalização (`SPORT_KEY`), mas fallback = chave `outro`.

```js
function sportSvg(nome, size=14){
  if(!nome) return '';
  let key = SPORT_KEY[nome];
  if(!key){ const k = Object.keys(SPORT_KEY).find(k=>k.toLowerCase()===nome.toLowerCase()); key = k?SPORT_KEY[k]:'outro'; }
  const svg = SPORT_SVG[key] || SPORT_SVG.outro;
  return `<span style="display:inline-flex;align-items:center;justify-content:center;width:${size}px;height:${size}px;flex-shrink:0;opacity:.75">${svg}</span>`;
}
```

Os SVGs usam `viewBox="0 0 16 16"`, `fill="none"`, `stroke="currentColor"`, `stroke-width="1.4"`.
Chaves disponíveis: `futebol`, `basquete`, `tenis`, `mma`, `f1`, `nfl`, `nhl`, `baseball`, `volei`,
`handbol`, `dardos`, `esports`, `multiplos`, `peixe`, `snooker`, `golf`, `rugby`, `outro`.

Exemplos (futebol e múltiplos):
```html
<!-- futebol -->
<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.2"/><polygon points="8,4.5 9.8,6.2 9.2,8.4 6.8,8.4 6.2,6.2" stroke-width="1.2"/><line x1="8" y1="1.8" x2="8" y2="4.5"/><line x1="13.4" y1="5.2" x2="9.8" y2="6.2"/><line x1="11.6" y1="12.5" x2="9.2" y2="8.4"/><line x1="4.8" y1="12.5" x2="6.8" y2="8.4"/><line x1="2.6" y1="5.2" x2="6.2" y2="6.2"/></svg>

<!-- multiplos (4 quadrados) -->
<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="5.5" height="5.5" rx="1"/><rect x="8.5" y="2" width="5.5" height="5.5" rx="1"/><rect x="2" y="8.5" width="5.5" height="5.5" rx="1"/><rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1"/></svg>

<!-- outro (fallback: círculo com "i") -->
<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="8" cy="8" r="6.2"/><line x1="8" y1="5" x2="8" y2="8.5"/><circle cx="8" cy="11" r=".8" fill="currentColor" stroke="none"/></svg>
```
> O conjunto completo dos 18 SVGs está em `assets/js/data.js` (`SPORT_SVG`) no Betting Dashboard.

---

## 7. Regras de marca (resumo)

- Fallback de esporte = **🏅** (nunca `•`, nunca `?`).
- Múltiplas/combinadas = **🔗** (nunca 🎰 — cassino é proibido).
- Emoji sempre **dessaturado** (`filter: grayscale(1)`) — combina com o cinza dos chips de casa.
- Chip de esporte e chip de casa têm a **mesma casca**: 24×24, raio 7px, fundo `#222831`,
  borda `rgba(255,255,255,0.08)`.
- Em tabelas/cards/listas: usar `mkSpChip()` / `sportCell()`. Em labels de gráfico: `.sport-emoji`.

---

## 8. Paleta relevante (dark)

| Uso                 | Valor                      |
|---------------------|----------------------------|
| Fundo do chip (steel)| `#222831` (--fdc-steel)   |
| Borda do chip       | `rgba(255,255,255,0.08)`   |
