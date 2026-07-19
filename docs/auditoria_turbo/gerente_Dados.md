## Dados

**Veredito da área:** Sólido — os 6 masters estão maduros e as 14 casas passam no auditor determinístico; os defeitos vivem em consistência de descrição e cobertura de teste, nenhum corrompe odd/stake/resultado.

**Top 3 ações prioritárias:**
- **Unificar o separador de bet builder colapsado** — hoje o MESMO tipo de aposta sai no TSV do usuário com três símbolos diferentes (` // `, ` & `, ` + `), e dois deles não existem no global (fere invariante #2). Decidir no `MASTER_DESCRICAO §16` e padronizar as 6 casas.
- **Fechar as 3 lacunas de propagação entre masters** — `Primeiro/Último Marcador` (existe só na DESCRIÇÃO), `aposta aberta → Resultado vazio` (não propagada ao OUTPUT) e `Múltiplos` ausente da whitelist canônica de ESPORTES §7. Todas trivial, todas confundem a IA na extração.
- **Popular o `golden_set/bilhetes/`** — não há nenhuma regressão print→TSV automatizada por casa; editar um §9/§5 errado não quebra teste nenhum. Priorizar cashout=V, múltipla=produto, HW/HL e formatos atípicos (Jogo de Ouro/Pinnacle en-US).

### Achados críticos e altos (detalhados)

> Nenhum achado crítico ou alto. Os cinco itens abaixo são de severidade **média** — não corrompem valores, mas são "degraus" que a IA tropeça na extração. Detalho por serem os acionáveis prioritários.

**1. Separador de bet builder diverge entre casas e usa símbolos não sancionados (arquitetura)**
`casas/CASA_JOGODEOURO.md:177` e correlatas. O global (`MASTER_DESCRICAO §16/§19.7`) só sanciona ` // ` para seleções diferentes. Mas o bet builder colapsado em Múltipla sai como ` // ` em Bet365/Betano/Betfair/KingPanda/Betesporte (correto), ` & ` em Jogo de Ouro/Lottu e ` + ` em Betnacional/Superbet. `&` e `+` não existem no §16 → é casa redefinindo regra global (viola invariante #2) e produz output inconsistente na planilha do usuário para o mesmo tipo de aposta. O `audit_casas.py` não pega (só checa categorias/estrutura).
**Ação:** decidir no global — (a) separador próprio para same-game builder no §16 + padronizar as casas no MESMO símbolo, ou (b) tratar como "seleções diferentes" e converter as 4 divergentes para ` // `. Depois estender `audit_casas.py` para validar que todo separador usado nos §9/§15 existe no §16. *[esforço: médio]*

**2. `Primeiro Marcador`/`Último Marcador` são órfãos (dados)**
`global/MASTER_APOSTAS_2026.md:117-129, 634-646`. A DESCRIÇÃO §12.1 os trata como sub-templates de Anytime, mas a autoridade de categoria (APOSTAS) nunca os mapeia — sinônimos §4, §6 Futebol e §7 não cobrem "Para Marcar Primeiro/Por Último". A IA guiada por APOSTAS para preencher a coluna Aposta não tem regra que os leve a Anytime. É exatamente a lacuna que a REGRA DE PROPAGAÇÃO do CLAUDE.md existe para evitar.
**Ação:** adicionar ambos aos sinônimos de Anytime (APOSTAS §4) e às regras §6/§7, cross-linkando com DESCRIÇÃO §12.1. *[trivial]*

**3. OUTPUT §13/§18 dessincronizado com `aposta aberta → Resultado vazio` (dados)**
`global/MASTER_OUTPUT_2026.md:330-362, 454-461`. RESULTADO §1.1 definiu que bilhete não liquidado fica com Resultado vazio, mas OUTPUT §13 afirma que a coluna "deve utilizar exclusivamente W L V HW HL" e §18 item 8 só pede "resultado válido". Uma IA lendo o OUTPUT isoladamente (é o master do formato final) conclui que precisa SEMPRE emitir um código — casa com o histórico de bug "aberta" registrado na MEMORY.
**Ação:** documentar a exceção da célula vazia em OUTPUT §13 e §18 (ponteiro para RESULTADO §1.1). *[trivial]*

**4. `Múltiplos` ausente da tabela oficial ESPORTES §7 e dos exemplos §4 (dados)**
`global/MASTER_ESPORTES_2026.md:38-51, 81-93`. É valor válido de Esporte, mas só aparece em §2 (Uso) e §8 (validação item 16). A tabela canônica §7 — que a IA usa como whitelist — não o contém, e §8 item 1 exige que o valor "exista neste documento". Tensão real: existe em §2, não na lista principal.
**Ação:** incluir `Múltiplos` em §4 e/ou §7 com nota apontando para §2. *[trivial]*

**5. PIPELINE §3.1 conflita com RESULTADO sobre odd de múltipla com void (fórmula)**
`global/MASTER_PIPELINE_2026.md:108-118`. PIPELINE manda usar "ODDS TOTAIS do bilhete"; RESULTADO §5.1.1/§5.5.1 manda preservar a "odd estrutural original" (produto de TODAS as pernas, inclusive anuladas). Quando a casa recalcula o total já sem a perna void, as duas instruções produzem odds diferentes no mesmo cenário.
**Ação:** alinhar PIPELINE à RESULTADO — trocar por "odd estrutural original (produto de todas as pernas)", com o total exibido valendo só sem void. *[pequeno]*

### Achados médios e baixos (resumidos em tabela)

| # | Sev | Tipo | Local | Achado | Ação | Esforço |
|---|-----|------|-------|--------|------|---------|
| 6 | médio | teste | `golden_set/README.md:6-8` | `golden_set/bilhetes/` vazio: nenhuma regressão print→TSV por casa. Editar §9/§5 errado não quebra teste. HW/HL só tem exemplo textual (só na Bet365) | Popular com 1 par (entrada+TSV) por casa cobrindo cashout=V, múltipla=produto, HW/HL, boost; criar teste de regressão | grande |
| 7 | médio | dados | `MASTER_APOSTAS:520-556` | Assimetria mal referenciada: Múltipla (Aposta, ≥2) ≠ Múltiplos (Esporte, ≥3). Dupla/bet builder viram Múltipla mas NÃO Múltiplos — trap fácil | Nota cruzada em APOSTAS §5 Múltipla explicitando o limiar 2 vs 3 (ver ESPORTES §2) | pequeno |
| 8 | baixo | organização | `MASTER_ESPORTES:230` | Ref. quebrada: §6 Vôlei aponta "seção anterior", mas a regra de Sets está DEPOIS (l.694) | Corrigir ponteiro para "mais adiante neste documento" | trivial |
| 9 | baixo | dados | `MASTER_APOSTAS:79,177-184` | Colisão lexical: categoria `Corridas` (runs de Baseball) vs tipo de mercado `Race/corrida` | Nota de desambiguação em §5 Race e na linha `Corridas` §3 | trivial |
| 10 | baixo | dados | `MASTER_APOSTAS:79` | Descrição de `Corridas` em §3 ("estatísticas de Baseball") ampla demais vs §6 (só runs/RBIs; strikeouts→Player Props) | Estreitar para "Corridas, RBIs e bases (Baseball)" | trivial |
| 11 | baixo | organização | `MASTER_APOSTAS:1252-1253` | Regra Sets Vôlei/Tênis duplicada em APOSTAS §9 e ESPORTES §8 — risco de drift | Manter canônica em ESPORTES §8; APOSTAS §9 vira ponteiro | trivial |
| 12 | baixo | organização | `casas/CASA_MODELO.md:151` | "27 categorias" drifou — §3 já tem 28. CASA_MODELO semeia casas novas com o número errado | Trocar "27" por "as categorias" (sem número) nos 4 arquivos + CLAUDE.md | trivial |
| 13 | baixo | organização | `STATUS.md:94` | STATUS §5 diz Jogo de Ouro "§9 (23 categorias aguardam amostra)", mas §9 já está em camada fina (4 mercados + Outros). STATUS é lido no início de cada sessão → engana | Remover a menção obsoleta da linha Jogo de Ouro | trivial |
| 14 | info | organização | `MASTER_PIPELINE:281-291` | PIPELINE §6.3 lista 4 passos de prioridade; ESPORTES §5 lista 5 (falta "conhecimento próprio do modelo", crucial p/ atletas ITF/MODUS não listados) | Sincronizar §6.3 com ESPORTES §5 ou trocar por ponteiro | trivial |

### Pontos positivos (o que está bem feito)

- **Auditor determinístico + camada fina blindam a propagação** (`tools/audit_casas.py`): roda **verde nas 14 casas** — nenhuma categoria órfã no §9, nenhum placeholder "aguarda amostra", registro no app conferido. A disciplina de camada fina (§9 lista só o mercado confirmado; taxonomia mora só no MASTER) foi a correção estrutural certa para o drift de 13/06 e encolheu a superfície de propagação.
- **Cashout e invariante E-Sports Props↔E-Sports são o padrão-ouro de propagação** — regra idêntica e cross-referenciada em RESULTADO §5.1.2/§5.6, OUTPUT §14 e CLAUDE.md, com fonte canônica declarada e armadilhas nomeadas (LYON, eBasket≠E-Sports). **Usar essas duas como modelo ao corrigir os achados 2, 3 e 4.**
- **Guardas anti-colapso de dedup embutidas na DESCRIÇÃO** — o sufixo obrigatório de Anytime (Mbappé Primeiro×Último) e a preservação do handle do gamer em eBasket impedem que bilhetes distintos colapsem em texto idêntico. Ligação rara e valiosa entre dados e o comportamento de UPSERT.
- **Casas de formato atípico bem traduzidas** — Pinnacle (parser determinístico, HW/HL asiático nunca rebaixado), Betfair (settledDate exato via JSON) e Polymarket (API via Worker) honram a invariante #3 (cálculo global, localização na casa). Referência ao promover "Modo de ingestão" para o MASTER.
- **CASA_BETANO já não descreve scraping** — dívida conhecida na memória do projeto está resolvida: o arquivo documenta ingestão por texto colado + screenshot, com ordem, dedup por ID e odd = produto das seleções. Atualizar a nota de memória.

> **Nota metodológica:** todos os 19 achados vieram marcados `nao-verificado` pelos especialistas (auditoria de leitura, sem execução contra dados reais). Recomendo validar os 5 médios com um bilhete real por caso antes de editar os masters — especialmente o #1 (separador), que toca o output final do usuário.