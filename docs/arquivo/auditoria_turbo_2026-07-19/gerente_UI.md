## UI

**Veredito da área:** Sólido com pontos de atenção — a fundação (guardrail + tokens) está robusta; os problemas são divergência entre implementações do helper monetário e drift de paleta nos gráficos, todos corrigíveis sem retrabalho estrutural.

**Top 3 ações prioritárias:**
- **Corrigir o bug de tooltip do gráfico de Esportes** (`performance.js:154`): mostra tags HTML literais ao usuário — único defeito visível em produção. Esforço trivial.
- **Alinhar o `fmtPL` do dashboard ao do extrator** (`app.js:14`): hoje pinta P/L zero (todo Void/cashout=stake) de verde com `+`, violando o §5.1; não está rastreado em nenhuma pendência. Esforço trivial, superfície ampla (tabelas + KPIs).
- **Centralizar a paleta de séries dos gráficos em tokens** (`overview.js`, `performance.js`, `gestao.js`): existem 4+ verdes e 3+ vermelhos hardcoded para o mesmo "positivo/negativo", violando "cor sempre de token"; o padrão de leitura via `getComputedStyle` já existe no código.

---

### Achados críticos e altos (detalhados)

**1. Tooltip do gráfico de Esportes vaza HTML cru — `performance.js:154` [bug / médio]**
O callback de tooltip do `chartSport` retorna `fmtPL(e[1].l)`, que devolve markup (`<span class="money">…</span>`). O tooltip do Chart.js é desenhado no canvas via `fillText` e não interpreta HTML — o usuário vê as tags literais. É o único tooltip que usa `fmtPL`; os demais usam `_txtPL`/`fmtK`/`fmtPct` (texto puro) e estão corretos.
→ Trocar por formatador de texto puro (`_txtPL` ou `fmtK`), como nos outros gráficos. **Esforço: trivial.**

**2. `fmtPL` do dashboard pinta zero de verde com `+` — `app.js:14` [fórmula / médio, confirmado]**
Usa `cls = v>=0?'pos':'neg'` e `sign = v>=0?'+':−`, então P/L zero renderiza `+R$ 0,00` em verde. O §5.1 exige zero neutro (sem sinal, sem cor). Toda aposta Void/cashout=stake (resultado V) tem P/L 0 e aparece verde nas tabelas e KPIs. O `fmtPL` do **extrator** (`index.html:4357-4366`) trata o caso corretamente — ou seja, o mesmo produto tem duas versões divergentes do helper no zero. O comentário em `app.js:20-21` admite o desvio, mas ele **não** consta no UI_REFERENCE §5.4 nem na AUDITORIA_2026.
→ Espelhar o extrator: classe `''` e sinal `''` quando `v===0`. Conferir os espelhos crus que repetem `v>=0?'+'`: `temporal.js:23`, `gestao.js:384`, `overview.js:180`. **Esforço: trivial.**

**3. Cores de série pos/neg fora de qualquer token — `overview.js:90-94` + `performance.js:154` [design-ui / médio]**
Mesmo significado semântico (P/L positivo vs negativo) pintado com hues diferentes conforme o gráfico, sempre com RGBA hardcoded. As barras usam `#00d68f`/`#f0506e` (não batem com `--pos #2BC07E` nem `--d-pos #4FC79A`); os heatmaps usam ainda `#00a064`/`#c8283c`. Há **quatro verdes** diferentes para "positivo" no sistema, alguns visivelmente distintos lado a lado. Parte do código de chart **já lê tokens em runtime** (`--accent` via `getComputedStyle`; `--d-pos` via `var()`), então o padrão de correção existe — é drift real, não limitação técnica.
→ Definir qual verde/vermelho é o oficial de gráfico e padronizar via helper único lido por `getComputedStyle` (`--d-pos`/`--d-neg` ou `--pos`/`--neg`), eliminando os literais divergentes. **Esforço: médio.**

**4. Rótulos de eixo abaixo do mínimo WCAG — `app.js:43` [design-ui / médio, acessibilidade]**
Os ticks em dark usam `tc() = #505060` sobre `--surface #12161D` → contraste ~2,3:1, abaixo do mínimo (4,5:1 texto pequeno; nem os 3:1 de texto grande). Como o app é dark-only, o ramo claro de `tc()` é código morto. `#505060` é ainda mais escuro que o token mais apagado da marca (`--ink-mute #5E6775`), deixando os eixos menos legíveis que o texto mais discreto do sistema.
→ Elevar para no mínimo `--ink-mute (#5E6775)`, preferível `--ink-soft (#95A1B0)`, derivando de token. **Esforço: trivial.**

---

### Achados médios e baixos (resumidos em tabela)

| # | Achado | Local | Sev. | Esforço |
|---|---|---|---|---|
| 5 | Literais hex duplicam tokens `--d-*` já definidos (`#4fc79a`, `#d6a45a`, `#4da3ff`, `#aeb7c2`); não acompanham mudança do token | `gestao.js`, `overview.js` | baixo | pequeno |
| 6 | KPIs de custo montam dinheiro com string crua `'R$ '+fmt` (28 ocorrências) fora do `.money` — **tech-debt já documentada** no §5.4 | `gestao.js:127-479` | baixo | médio |
| 7 | Distribuição de Odds: WR% e ROI% em dois eixos auto-escalados independentes, ambos "%", induzem comparação de altura entre escalas incomparáveis | `overview.js:145-157` | médio | pequeno |
| 8 | Gráfico de banca (hero) sem legenda nem título de eixo: linha=acumulado / barras=diário em escalas R$ distintas, sem chave | `overview.js:59-78` | baixo | pequeno |
| 9 | Curva acumulada (y1) sem âncora no zero exagera variação/drawdown; sobreposta a barras diárias ancoradas no zero mistura baselines | `overview.js:77` | baixo | pequeno |
| 10 | Gráficos de evolução sem estado vazio quando `<2` dias — canvas em branco parece quebrado (`mkEmpty` existe, não é acionado) | `performance.js:487` | baixo | trivial |
| 11 | Barras de Fornecedores codificam sinal só por cor (sem data label), pior caso para daltonismo; Esportes tem rótulo com sinal, Fornecedores não | `gestao.js:237` | baixo | pequeno |
| 12 | Matriz de correlação inverte convenção de cor (positiva=vermelho); é deliberado (semântica de risco) e tem legenda+valor, mas contra-intuitivo | `temporal.js:262-263` | info | trivial |
| 13 | Variável `roi` morta no `valLabelPlugin` (rótulos de Esportes) — código morto inofensivo | `performance.js:144` | info | trivial |
| 14 | UI_REFERENCE §1 não documenta a camada `--d-*` usada nos charts — revisor de marca não distingue on-brand de drift | `docs/UI_REFERENCE.md:13-25` | info | trivial |

> Nota sobre #6: já mapeada no §5.4, portanto **conhecida** — mas segue sem migração e com superfície grande. Migrar para `fmtR` (agregado/custo) e `fmtPL` (P/L) no próximo toque em `gestao.js`.

---

### Pontos positivos (o que está bem feito)

- **Guardrail `check-tokens.mjs` robusto e bloqueante** (`scripts/tokens/`): cobre drift entre cópias do `tokens.css`, cores banidas, conformidade de tamanho da casca (SHELL_SPEC) e proibição de abreviar dinheiro. Rodou limpo — antídoto real contra a regressão da sessão 83. Sugestão: estender a trava (d) para pegar `'R$ '+fmt` em código **novo**.
- **`fmtPL` do extrator é a implementação de referência** (`index.html:4357-4366`): zero neutro, minus tipográfico U+2212, `.money` com R$ menor/neutro, cor só no `.money-val`, 2 casas pt-BR, travessão para aposta aberta. É a fonte única a espelhar no dashboard.
- **Formatação monetária dos eixos respeita o §5** (`app.js:265`): apesar do nome `fmtK`, **não** abrevia — retorna `R$ 12.345` com milhar completo e U+2212. Sugestão: renomear (ex.: `fmtEixoR$`) para o nome não convidar um "conserto" errado.
- **Heatmaps e matriz com redundância cor+número** (`temporal.js:81`): valor sempre visível na célula, texto clareia sobre fundo saturado (`heatTxt`) — daltônico-safe. Manter como padrão para novos heatmaps.
- **Higiene de ciclo de vida e densidade** (`app.js:40`): `destroyChart` antes de recriar (sem tooltips fantasma), thinning de labels (`length/14`), `maxRotation:30`, piso de opacidade no calendário. Boas decisões de legibilidade.
- **Tokens bem estruturados e sincronizados**: triplets RGB, temas dark/light, camada diagnóstica `--d-*` — sincronizados entre as cópias.

> **Tema transversal:** os quatro achados de cor (#3, #5, e as barras) têm a mesma raiz — literais hex onde já existe token. Resolver todos com **um** helper de leitura de token reaproveitado nos quatro módulos de gráfico, decidindo com o Feca qual verde/vermelho é o oficial. Nenhum dos achados de gráfico estava registrado como pendência conhecida (exceto o #6).