## UX

**Veredito da área:** Sólido no núcleo — o fluxo principal (extração e análise) é resiliente e bem feito; precisa de atenção pontual em dois itens de dados/fórmula e num conjunto de polimentos de descoberta.

**Top 3 ações prioritárias:**
- **Escopar Custo de Tipsters e Custos Gerais por dono** (localStorage sem sufixo de dono) — mesmo vazamento de privacidade já corrigido para Custo de Contas segue aberto; contamina o P/L Líquido ao trocar de login no mesmo browser. `[alto/confirmado, esforço pequeno]`
- **Corrigir o P/L Líquido da Visão Geral** — ele subtrai o custo de tipster do histórico inteiro ignorando o filtro de data, enquanto o custo de contas ao lado respeita o filtro → número incoerente ao filtrar um dia/mês. `[alto/confirmado, esforço médio]`
- **Devolver a affordance de edição inline** — um `class` duplicado no HTML descarta a classe `.ap-edit`, matando a única pista visual (cursor de texto) e tornando o duplo-clique praticamente não-descobrível. `[médio, esforço pequeno]`

---

### Achados críticos e altos (detalhados)

**1. Custo de Tipsters e Custos Gerais vazam entre donos** — `app.js:907-915` `[alto/confirmado]`
As chaves `CT_KEY='custoTipsterData'` e `CG_KEY='custoGeralData'` são fixas, sem sufixo de dono. As abas Custo de Tipsters e Custos Gerais persistem no mesmo namespace para todos os usuários do mesmo navegador — exatamente o vazamento já corrigido para Custo de Contas (que usa `costKey()` com `::dono`). Além do risco de privacidade em máquina compartilhada, ao trocar de login o novo dono vê os custos de tipster do anterior, e esses valores entram no P/L Líquido da Visão Geral (`overview.js:17`).
**Rec:** Escopar `CT_KEY`/`CG_KEY` por dono, espelhando `costKey()` (ex.: `'custoTipsterData::'+dono`). Idealmente migrar esses custos para o Postgres por dono, já que localStorage não sincroniza entre dispositivos. `[esforço pequeno]`

**2. P/L Líquido ignora o filtro de data no custo de tipster** — `overview.js:16-23` `[alto/confirmado]`
No KPI hero da Visão Geral, `costConta` vem de `calcCostFiltered(rows)` (respeita período e escopo), mas `costTipster` soma TODOS os valores de `ctData` de todos os meses, sem olhar o filtro. Ao filtrar "Hoje" ou um único mês, o P/L Líquido leva um abatimento de meses/anos de assinatura que não pertencem ao período — número enganoso e incoerente com o Custo de Contas ao lado, que é filtrado. O card "Custo de Tipsters" tem o mesmo problema.
**Rec:** Filtrar `ctData` pelos meses dentro de `[minDate,maxDate]` do recorte (mesma lógica temporal de `calcCostFiltered`), ou rotular o custo de tipster como "total do histórico" e removê-lo do P/L Líquido quando há filtro de período ativo. `[esforço médio]`

> **Observação de gerência:** os dois altos estão acoplados — o vazamento do achado 1 alimenta a fórmula do achado 2. Recomendo tratá-los na mesma sessão: escopar as chaves e, no mesmo passo, ajustar o filtro temporal do custo de tipster.

---

### Achados médios e baixos (resumidos)

| # | Sev | Achado | Local | Rec (resumo) | Esforço |
|---|-----|--------|-------|--------------|---------|
| 3 | médio | Edição inline sem pista visual: `class` duplicado descarta `.ap-edit` (cursor:text nunca aplica; afeta data, tipo, desc, casa, parceiro) | `apostas.js:121-137` | Emitir um único `class` por célula (concatenar `ap-edit` na string base); reforçar com sublinhado pontilhado no hover | pequeno |
| 4 | médio | Campo Resultado incoerente: texto livre no modal (✎) vs `<select>` restrito no inline — sem validação, aceita "GANHOU"/"w" minúsculo no PATCH | `index.html:1882` | Trocar `ed-resultado` por `<select>` com as 5 opções (+ vazio); fecha a porta do bug histórico do "v" minúsculo | pequeno |
| 5 | médio | Erro cru do servidor (HTML/stacktrace 500) despejado na linha de progresso do card | `index.html:3886` | Truncar/detectar content-type; exibir mensagem acionável e guardar o cru só no console | pequeno |
| 6 | médio | Cards Cenário Atual / Diagnóstico de Risco mantêm números velhos quando o filtro zera resultados (`return` silencioso) | `overview.js:216-266` | Pintar estado vazio explícito (`mkEmpty`) no caminho `rows.length===0`, como já faz o heatmap | pequeno |
| 7 | médio | Dashboard sem responsividade: `layout.css` sem nenhuma `@media`; KPIs travados em `repeat(4,1fr)` inline → mobile inviável | `layout.css:39-92` | Breakpoints (sidebar em drawer, KPIs 2/1 col abaixo de ~680px); trocar grids inline por classe reutilizável | grande |
| 8 | baixo | Edição inline por duplo-clique indescoberta na grade de Extração (só cursor:text como pista) | `index.html:1135` | Adicionar `title="Duplo-clique para editar"` nas células `.ap-edit` ou legenda no cabeçalho | trivial |
| 9 | baixo | Atalhos da coluna Tipster (F2, Ctrl+C/V, Shift+setas) só existem em comentário de código, zero dica na UI | `index.html:4904` | Tooltip/ícone "?" no cabeçalho listando os atalhos, ou `title` no input | trivial |
| 10 | baixo | "Limpar" apaga texto + imagens do lote (e deleta `estadoExtrator`) sem confirmação nem desfazer | `index.html:3501` | Confirmar quando houver conteúdo relevante (>1 imagem ou texto), ou oferecer "desfazer" no status | pequeno |
| 11 | baixo | Onboarding do RAIO-X promete "confere e confirma", mas a extração já salva direto no banco | `index.html:3757` | Ajustar texto: "Já entra na tabela — confira e ajuste se preciso" | trivial |
| 12 | baixo | "Baixar base (CSV)" ignora os filtros ativos e devolve a base inteira, apesar do contador "X de Y" | `app.js:550` | Rotular como "Baixar base completa (backup)" + botão "Exportar recorte filtrado" (cliente) | médio |
| 13 | baixo | Filtros não persistem ao trocar de aba (estado por página) — refazer o recorte em cada aba | `filters.js:1-3` | Avaliar filtro global compartilhado, ou ao menos propagar Período + seleções; se deliberado, explicitar na UI | médio |

> **Nota de agrupamento:** os achados 3 e 8 são a mesma classe de problema (edição inline sem affordance) em superfícies distintas — dashboard (Apostas) e Extração. Vale um passe único padronizando a pista visual (sublinhado pontilhado + `title`) nas duas telas.

---

### Pontos positivos (o que está bem feito)

- **Contador de imagens 15/15 com degradê de cor** (`index.html:3446-3454`) — feedback preventivo claro: contador ao vivo, neutro→warn (12+)→neg (15), truncamento gracioso das extras com aviso, sem travar o usuário de repente.
- **Cards multi-paralelo com progresso granular** (`index.html:3878-3906`) — spinner, segundos decorridos, chars streamados, chunk X/Y, tokens in/out com % de cache, cancelar (AbortController) e thumbnails; contas em paralelo sem bloquear o formulário.
- **Carimbo de hora de envio estabiliza a ordem do feed** (`index.html:4011`) — `submittedAt` capturado no clique vira `criado_em` do lote; combinado com a devolução ao `estadoExtrator` em falha, o fluxo é resiliente a corridas e a retry sem perda.
- **Datas em fuso local, bem documentado** (`filters.js:13-21`) — `_ymd/_today/_wtdStart/_mtdStart` no fuso do usuário, com comentário do porquê UTC quebraria "Hoje" à noite no Brasil; bug histórico prevenido. **Referência para qualquer novo cálculo de data no front.**
- **Aba Apostas com virtual scroll e trava de edição** (`apostas.js:90-104`) — janela virtual + `requestAnimationFrame`, e `_apInlineEditing` impede o re-render matar o input em edição; padrão a replicar (ex.: Contas Individuais em `gestao.js`, hoje sem virtualização).
- **Boot instantâneo (IndexedDB stale-while-revalidate)** (`app.js:1042-1109`) — serve o dado velho no boot e revalida em 2º plano, com máscara "Sincronizando… os números podem estar desatualizados", loading no botão Atualizar e banner de erro com retry; honestidade sobre frescura dos dados bem cuidada. *(Único ajuste: alinhar o `left:220px` fixo do banner de erro quando houver breakpoint mobile.)*