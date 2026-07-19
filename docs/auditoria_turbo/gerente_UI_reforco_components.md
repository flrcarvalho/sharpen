# Reforço — Design System / components.css (2ª passada)

Escopo: `components.css` (1597), `layout.css` (461), `tipster-metodo.css` (129), `shell.css` (57).

> **Calibração:** `check-tokens.mjs` só bloqueia drift de token, hex off-brand fechado, font-size de 5 seletores da casca e abreviação de milhar. **Não** valida raio/spacing/z-index/`rgba` literal (só WARN). Os achados abaixo são drift real **não coberto** pela trava.

## Achados

**[alto] Segmented-button quadruplicado — o "canônico" `.seg-btn` nasceu órfão** — `components.css:21-41` (`.qbtn`), `:85-105` (`.seg-btn`), `:1208-1230` (`.tcard-seg button`), `:795-810` (`.apostas-sort-btn`)
O comentário declara `.seg-btn` como canônico ("substitui .qbtn, .ap-btn, .tcard-seg"), mas `.seg-btn` tem **zero uso** no `app/`; `.qbtn` segue em 4 arquivos. Blocos byte-a-byte idênticos. → Migrar call-sites para `.seg-btn` e apagar as cópias, OU apagar `.seg-btn` morto e assumir `.qbtn`. Esforço: médio.

**[alto] `.dot.hw` e `.dot.hl` pintam meio-ganho e meia-perda com o MESMO âmbar** — `components.css:662-663`
Ambos `background: var(--warn) !important`. No resto do sistema HW=verde, HL=vermelho. Nos streak dots ficam indistinguíveis + viola marca (âmbar só p/ aviso) + `!important` trava override. → `.dot.hw→var(--pos)`, `.dot.hl→var(--neg)`, remover `!important`. Esforço: baixo.

**[médio] Contraste insuficiente de `--ink-mute` em labels pequenos (8–11px)** — `tokens.css:39` aplicado em massa
`--ink-mute` (#5E6775) sobre `--surface` ≈ **3.2:1** (< AA 4.5:1). Atinge `.kpi-label`, `.btbl-th` 9px, `.nav-group`, `.filter-label`, `.tl-badge` 8px etc. → Labels ≤11px em `--ink-soft`, ou clarear `--ink-mute`. Decisão de token com o Feca. Esforço: médio.

**[médio] Raios fora da escala `--r-*`** — 6/7/3/2px espalhados (`.day-nav` 6px, `.ms-dd` 7px, `.sp-chip`/`.house-chip` 7px…). → `--r-xs`/`--r-sm`. Esforço: médio.

**[médio] `rgba()` de acento/resultado literal em vez dos triplets** — `tipster-metodo.css` foi convertido; `components.css` mantém `rgba(46,139,255,…)`, `rgba(43,192,126,…)` e um `rgba(128,128,128,.1)` que não vem de token nenhum. → Sweep para triplets. Esforço: médio.

**[médio] `.filters` e `.ms-wrap` definidos em 2 lugares** — `layout.css:259` + `components.css:1126/1127`; `.ms-dd` com `z-index:9999 !important` duplicado. → Consolidar cada componente num bloco. Esforço: baixo.

**[médio] z-index sem sistema** — 2000/9997/9999/99999/100/50 soltos; toast e loader empatam em 9999; `cal-tip` 99999 fura tudo. → Tokens `--z-*` (base/dropdown/overlay/toast/tooltip). Esforço: médio.

**[médio] "Número grande de KPI" reimplementado 4×** — `.kpi-val`, `.cal__hero .v`, `.cal__kpi .v`, `.cal-tip .ct-pl` com pesos divergentes (`--weight-extrabold` vs `800` literal). → Extrair `.kpi-num`. Esforço: médio.

**[médio] Pill de resultado duplicada** — `.badge*` (:637-655) vs `.bet-res-*` (:911-927) com alphas ligeiramente diferentes (`.12/.2` vs `.15/.3`). → Unificar + tokens de alpha. Esforço: médio.

**[baixo] Falta `:focus-visible` na maioria dos botões** — inputs têm foco, botões só `:hover`. → `:focus-visible{outline:2px solid var(--accent)}` global. Esforço: baixo.

**[baixo] Tipografia fracionária off-scale** — 8.5/10.5/12.5/13.5/9.5px. → Mapear p/ `--text-*`. Esforço: baixo.

**[baixo] `#fff` literal como cor de texto** — `:20,41,105…`; existe `--fdc-white`. Esforço: baixo.

**[info] Convenções de nome divergentes** — `.bet-res-ABERTA` UPPERCASE vs resto lowercase; globais genéricas (`.num`/`.mono`/`.dot`/`.card`) sem prefixo (família que já causou a colisão `.kpi`).

## Positivos
1. **`.money` implementa o §5 corretamente** (`:395-416,625-628`) — `.money-val` herda pos/neg, `.money-sign` forçado a `--ink-soft` neutro, `tabular-nums`.
2. **Colisão histórica `.kpi` resolvida com disciplina** — renomeada p/ `.tm-kpi` com comentário do porquê, sem mais `!important`.
3. **`:disabled` bem coberto** — export/day-nav/cal-nav/update/primary, spinner num único `@keyframes`.
4. **Tokens sólidos e theme-aware** — dark/light/navy, triplets RGB, camada `--d-*`; `shell.css` enxuto.
