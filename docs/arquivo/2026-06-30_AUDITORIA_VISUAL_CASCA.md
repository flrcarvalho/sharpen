# Auditoria visual — Planilhador vs modelo "Casca Unificada"

> Read-only. Comparação do estado NO AR (sessão 78/79) contra o arquivo de referência
> `FDC Capital - Casca Unificada (Modelo).html` (Claude Design, projectId `d0f95445-…`).
> Objetivo: punch-list preciso do que ainda falta **visualmente**, com tamanho e se depende de backend.

## Veredito

O grosso da marca já está aplicado e no ar. **Sidebar (nav do shell), context bar (Operador + Conta ativa + Modelo), brand/logo, tokens e a coluna "Análise IA"** já existem e batem com o modelo. O que falta é **pouco e delimitado** — não há backlog visual grande.

| # | Item | O que o modelo tem | O que temos hoje | Tamanho | Backend? |
|---|---|---|---|---|---|
| **A** | **Pagehead vs partner-header redundante** | Um título de página `Planilhador` + eyebrow `Operação · extração de bilhetes` no topo; a identidade da conta vive SÓ na context bar | Não há pagehead; em vez disso um `partner-header` grande (favicon + nome + sub) que **repete** o que a context bar "Conta ativa" já mostra | pequeno | não |
| **B** | **Resumo do rail (3 KPIs) + notas estruturadas** | `rail__sum` com **Itens · Duplicadas · Confiança** + pill "extração concluída" + notas com tarja colorida (info/warn/ok) + rodapé "Sonnet · 1,2s · N itens" | Coluna "Análise IA" com cards de extração + "Notas Críticas" + token-bar (funcional, real) | médio | **parcial** — Itens/Duplicadas já temos; **Confiança** e **anomalia de stake** são sinais novos |
| **C** | **Enquadramento em cards `.panel`** | Intake e grade dentro de cartões arredondados `.panel` (borda + raio + surface) | `input-section` + `btbl-wrap` já são cartões de marca; pode haver diferença fina de raio/padding/borda | pequeno | não |
| **D** | **Toggle de tema (Escuro/Claro)** | Segmento Escuro/Claro no pagehead | Dark-only (adiado de propósito na sessão 74) | médio | não |
| **E** | **Filtros/segmentos `.seg` e eyebrows** | Pílulas `.seg`, eyebrows mono em maiúscula, tick de seção `.panel__head .tick` | Variações próprias já alinhadas; pequenos detalhes de tipografia/maiúscula | pequeno | não |

## Já batendo com o modelo (não mexer)

- **Sidebar** = nav do shell agrupada (Operação/Análise/Resultados/Gestão), brand horizontal, rodapé sync + CSV.
- **Context bar** = Operador (com "ver como operador") · Conta ativa (dropdown + "+ Nova conta" no topo) · Modelo (+ sync Poly).
- **Coluna direita "Análise IA"** já existe (título + token-bar + cards + notas).
- **Duas colunas** (intake + grade | análise) com resizer.
- **Dashboard**: 1 logo por tema (corrigido), sidebar idêntica à do Planilhador.

## Recomendação de ordem

1. **A — pagehead** (ganho rápido, sem backend): trocar o `partner-header` redundante por um pagehead `Planilhador / Operação · extração de bilhetes`, deixando a identidade da conta só na context bar. Tira duplicação e fecha o topo igual ao modelo.
2. **4.3 — Contas & Parceiros** (feature): página de gestão (criar/renomear/arquivar/custos) + deep-link da nav por página.
3. **B/4.4 — rail Análise IA**: evoluir a coluna existente para o resumo de 3 KPIs + notas estruturadas. Itens/Duplicadas já dá pra ligar; **Confiança** e **anomalia de stake** exigem backend novo.
4. **D — tema claro** e **C/E — polimentos finos**: por último, sob demanda (decisão de marca: produto = dark).

> Nada aqui é destrutivo como a 4.2.c foi. A casca está completa; isto é refino e features novas.
