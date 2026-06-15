# MASTER_PIPELINE_2026
## Pipeline Operacional Oficial — Extrações de Apostas (2026)

Este documento define o pipeline operacional obrigatório para processamento de apostas esportivas.

Ele é responsável por:
- ordenar o fluxo de execução
- definir prioridades operacionais
- coordenar os masters globais
- padronizar comportamento entre modelos
- reduzir inconsistências de parsing

Este arquivo NÃO redefine:
- esportes
- categorias
- descrição
- resultado
- output

Essas regras pertencem exclusivamente aos respectivos masters globais.

---

# 1. Ordem Oficial do Pipeline

Toda extração deve seguir obrigatoriamente esta sequência:

```text
1. Detecção de bilhetes
2. Separação de apostas
3. Extração bruta
4. Reconstrução contextual
5. Identificação semântica
6. Normalização
7. Validação
8. Serialização final
```

Nunca inverter etapas.

---

# 2. FASE 1 — DETECÇÃO DE BILHETES

Objetivo:
- identificar quantos bilhetes existem
- separar corretamente blocos independentes
- evitar fusão entre apostas distintas

---

## 2.1 Fontes válidas

O pipeline deve aceitar:
- imagem
- OCR
- texto puro
- conteúdo híbrido

---

## 2.2 Detecção visual

Quando houver imagem:
- utilizar separação visual dos blocos
- identificar espaçamento
- detectar divisores da interface
- identificar mudança estrutural entre apostas

---

## 2.3 Ordem dos bilhetes

As casas normalmente exibem apostas:

```text
mais recente → mais antiga
```

A saída final deve inverter para:

```text
mais antiga → mais recente
```

A inversão deve seguir:
- posição visual
- ordem textual
- estrutura do bilhete

Nunca utilizar:
- horário
- timestamp
- data do evento

---

# 3. FASE 2 — SEPARAÇÃO DE APOSTAS

Objetivo:
- separar corretamente cada seleção
- detectar múltiplas
- detectar create bets
- evitar duplicações

---

## 3.1 Múltiplas

Um bilhete com N seleções = **1 linha no TSV**.

- `Aposta`: `Múltipla`
- `Descrição`: seleções concatenadas com ` // ` na ordem original do bilhete
- `Odd`: W com retorno visível → retorno ÷ stake; L ou V → ODDS TOTAIS do bilhete
- `Stake`: valor total do bilhete — nunca dividir entre as seleções
- **Nunca** gerar uma linha por seleção
- **Nunca** reordenar as seleções

---

## 3.2 Bet Builder / Criar Aposta

Quando múltiplas seleções pertencerem ao mesmo evento:
- tratar como Múltipla
- preservar contexto compartilhado
- reconstruir confronto comum

---

## 3.3 Separação de Seleções

O pipeline deve identificar:
- seleções independentes
- mercados do mesmo jogador
- props combinadas
- múltiplos mercados dentro da mesma seleção

---

## 3.4 Mercados do Mesmo Jogador

Quando a mesma seleção possuir múltiplos mercados do mesmo jogador:

Exemplo:

```text
10+ Assistências
10+ Pontos
```

serializar utilizando:

```text
Mercado A / Mercado B
```

Nunca dividir em seleções independentes.

---

# 4. FASE 3 — EXTRAÇÃO BRUTA

Objetivo:
- capturar dados brutos antes da normalização

---

## 4.1 Campos obrigatórios

Extrair sempre que possível:
- stake
- retorno
- odd
- cashout
- status
- seleção
- confronto
- entidade
- mercado

---

## 4.2 Preservação de contexto

Durante extração:
- preservar linhas vizinhas
- preservar agrupamento visual
- preservar ordem original

---

## 4.3 OCR Imperfeito

Quando OCR estiver quebrado:
- priorizar contexto estrutural
- utilizar reconstrução contextual
- evitar hallucination

Nunca:
- inventar entidades
- inventar linhas
- inventar confrontos

---

# 5. FASE 4 — RECONSTRUÇÃO CONTEXTUAL

Objetivo:
- reconstruir informações fragmentadas no layout

---

## 5.1 Reconstrução de confronto

Quando confronto não estiver na mesma linha:
- buscar linhas próximas
- utilizar contexto visual
- utilizar estrutura do bilhete

---

## 5.2 Prioridade da reconstrução

Quando confronto existir no bilhete:
- reconstrução possui prioridade máxima
- evitar fallback sem confronto

---

## 5.3 Reconstrução proibida

Nunca reconstruir utilizando:
- inferência insegura
- memória do modelo
- suposição contextual fraca

Melhor:
- descrição sem confronto

do que:
- confronto hallucinado

---

# 6. FASE 5 — IDENTIFICAÇÃO SEMÂNTICA

Objetivo:
- identificar esporte
- categoria
- entidades
- tipo de mercado

---

## 6.1 Identificação de esporte

Utilizar exclusivamente:

```text
MASTER_ESPORTES_2026
```

---

## 6.2 Identificação de categoria

Utilizar exclusivamente:

```text
MASTER_APOSTAS_2026
```

---

## 6.3 Prioridade semântica

A identificação deve seguir:

```text
1. Mercado especializado
2. Liga/Torneio
3. Participantes
4. Contexto geral
```

---

## 6.4 Mercados especializados

Mercados especializados possuem prioridade máxima.

Exemplos:

```text
games → Tênis
legs → Dardos
```

---

## 6.5 ML/H2H

Mercados ML/H2H exigem:
- análise contextual
- desambiguação nominal
- identificação dos participantes

Especialmente em:
- Tênis
- Dardos
- E-Sports

---

# 7. FASE 6 — NORMALIZAÇÃO

Objetivo:
- transformar dados brutos em padrão oficial

---

## 7.1 Descrição

Utilizar exclusivamente:

```text
MASTER_DESCRICAO_2026
```

---

## 7.2 Resultado e Odd

Utilizar exclusivamente:

```text
MASTER_RESULTADO_2026
```

---

## 7.3 Output

Utilizar exclusivamente:

```text
MASTER_OUTPUT_2026
```

---

## 7.4 Normalizações obrigatórias

Aplicar:
- trim
- UTF-8
- vírgula decimal
- Over/Under em inglês
- casing oficial

---

# 8. FASE 7 — VALIDAÇÃO

Objetivo:
- impedir saída inconsistente

---

## 8.1 Validações obrigatórias

Validar:
- esporte válido
- categoria válida
- descrição válida
- resultado válido
- odd válida
- TSV válido
- ordem cronológica correta

---

## 8.2 Integridade estrutural

Validar:
- nenhuma coluna extra
- nenhuma linha quebrada
- nenhuma seleção perdida
- nenhuma duplicação

---

## 8.3 Integridade semântica

Validar:
- Games não usado em Dardos
- Legs não usado em Tênis
- Assistência corretamente classificada
- Player Props não usado indevidamente
- confrontos não hallucinated

---

# 9. FASE 8 — SERIALIZAÇÃO FINAL

Objetivo:
- gerar saída final oficial

---

## 9.1 Ordem final

A saída final deve respeitar:

```text
mais antiga → mais recente
```

---

## 9.2 Formato final

Utilizar exclusivamente:

```text
TSV
```

seguindo:

```text
MASTER_OUTPUT_2026
```

---

## 9.3 Conteúdo final

A saída final deve conter:
- apenas linhas TSV
- nenhum markdown
- nenhum comentário
- nenhum cabeçalho
- nenhuma explicação adicional

---

# 10. Regras de Segurança Operacional

---

## 10.1 Prioridade da precisão

Melhor:
- informação parcial correta

do que:
- informação completa hallucinated

---

## 10.2 Nunca inventar

Nunca inventar:
- confrontos
- jogadores
- odds
- stake
- cashout
- resultados
- mercados

---

## 10.3 Fallback seguro

Quando houver ambiguidade genuína:
- preservar informação parcial
- utilizar fallback oficial
- evitar inferência insegura

---

# 11. Responsabilidades Oficiais

| Função | Arquivo responsável |
|---|---|
| Output TSV | MASTER_OUTPUT_2026 |
| Resultado/Odd | MASTER_RESULTADO_2026 |
| Esporte | MASTER_ESPORTES_2026 |
| Categoria | MASTER_APOSTAS_2026 |
| Descrição | MASTER_DESCRICAO_2026 |
| Fluxo operacional | MASTER_PIPELINE_2026 |

---

# 12. Objetivo do Pipeline

O pipeline existe para:
- padronizar comportamento entre modelos
- reduzir inconsistência operacional
- minimizar hallucination
- aumentar robustez de parsing
- estabilizar reconstrução contextual
- garantir compatibilidade entre GPTs

---

VERSÃO: 2026  
STATUS: ATIVO  
USO: Pipeline operacional dos extratores esportivos