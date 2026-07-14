# MASTER_DESCRICAO_2026
## Padrão Oficial da Coluna `Descrição` — Extrações de Apostas (2026)

Este documento define o padrão oficial da coluna:

```text
Descrição
```

Ele é a fonte única de verdade para:
- serialização da descrição
- estrutura textual das apostas
- padronização de confrontos
- reconstrução contextual
- normalização semântica

Todos os extratores devem obedecer exatamente este padrão.

---

# 1. Regras Gerais

A descrição deve ser:
- determinística
- legível
- auditável
- consistente entre casas

A descrição deve conter informação suficiente para identificar a aposta de forma única.

Nunca:
- inventar informações
- criar confrontos inexistentes
- alterar semanticamente o mercado
- modificar entidades identificadas corretamente

---

# 2. Estrutura Oficial

Sempre que possível utilizar a estrutura:

```text
Entidade - Mercado [Confronto]
```

Exemplo:

```text
Ja Morant - Over 7.5 Assistências [MEM Grizzlies v PHI 76ers]
```

---

# 3. Separador Oficial

Utilizar obrigatoriamente:

```text
" - "
```

(espaço + hífen + espaço)

Nunca utilizar:
- `:`
- `|`
- `_`
- múltiplos espaços
- hífen sem espaços laterais

---

# 4. Estrutura do Confronto

O confronto deve utilizar obrigatoriamente o formato:

```text
[Entidade A v Entidade B]
```

Exemplos válidos:

```text
[LAL Lakers v CHI Bulls]
[Manchester City v Arsenal]
[Sinner v Alcaraz]
[Luke Littler v Luke Humphries]
```

---

# 5. Separador Oficial de Confronto

Utilizar exclusivamente:

```text
v
```

Nunca utilizar:
- `x`
- `vs`
- `@`
- hífen

---

# 6. Reconstrução de Confronto

Em diversas casas, o confronto não aparece na mesma linha do mercado.

O extrator deve reconstruir o confronto utilizando:
- linhas vizinhas
- contexto do bilhete
- estrutura visual da aposta

---

## Exemplo

Entrada visual:

```text
Russell Westbrook
10+ Assistências

SAC Kings
LA Clippers
```

Descrição correta:

```text
Russell Westbrook - 10+ Assistências [SAC Kings v LA Clippers]
```

---

# 7. Prioridade da Reconstrução

Quando o confronto existir no bilhete, sua reconstrução possui prioridade máxima.

O extrator deve tentar reconstruir o confronto antes de utilizar fallback sem confronto.

---

# 8. Confronto Ausente

Descrição sem confronto é permitida apenas como fallback.

Utilizar apenas quando:
- o confronto realmente não estiver disponível
- não houver reconstrução segura possível
- houver risco de hallucination

Exemplo válido:

```text
Russell Westbrook - 10+ Assistências
```

---

# 9. Proibição de Hallucination

Nunca inventar:
- confrontos
- jogadores
- times
- mercados
- linhas
- entidades ausentes

Quando houver dúvida:
- preservar informação parcial
- nunca completar utilizando inferência insegura

---

# 10. Estrutura de Mercados

---

## 10.1 Mercado Contínuo (Over / Under)

Mercados contínuos utilizam linhas fracionadas.

Formato oficial:

```text
Over X.5 Mercado
Under X.5 Mercado
```

Exemplos:

```text
Over 2.5 Gols
Under 7.5 Assistências
Over 22.5 Pontos
```

---

## 10.2 Mercado Discreto (X+)

Mercados discretos utilizam linhas inteiras.

Formato oficial:

```text
X+ Mercado
```

Exemplos:

```text
10+ Pontos
15+ Rebotes
3+ Assistências
```

---

## 10.3 Mercado Race (Primeiro a marcar X)

Mercados "Race" (corrida / `Primeiro a marcar X`) apostam em qual entidade atinge **primeiro** um número inteiro de eventos. A entidade vencedora e o alvo `N` vão na descrição; a categoria segue o objeto (`MASTER_APOSTAS_2026 §5 — Race`).

Formato oficial:

```text
Race N - Entidade [Confronto]
```

Exemplos:

```text
Race 9 - Suécia [Japão v Suécia]
Race 3 - Brasil [Brasil v Argentina]
Race 20 - Lakers [LAL Lakers v CHI Bulls]
```

- `N` é sempre inteiro (nunca `.5`).
- `Race` é fixo em inglês (como Over / Under), seguido do objeto **apenas na coluna `Aposta`** (ex.: `Escanteios`), não repetido na descrição.

---

# 11. Normalização Over / Under

Converter sempre para inglês.

---

## Conversões obrigatórias

| Casa exibe | Descrição correta |
|---|---|
| Mais de 2.5 | Over 2.5 |
| Menos de 6.5 | Under 6.5 |
| +2.5 | Over 2.5 |
| -2.5 | Under 2.5 |

---

# 12. Templates Oficiais

---

## 12.1 Anytime

A categoria `Anytime` cobre toda a família "jogador para marcar". O **limiar de gols** entra na Descrição — nunca vira categoria própria:

- **1+ (marcar a qualquer momento):** sem sufixo → `Jogador [Confronto]`
- **2+ gols** (Marcar 2 ou Mais / dois ou mais gols): `Jogador - 2+ Gols [Confronto]`
- **3+ gols** (Hat-trick / Marcar 3 Gols / três ou mais gols): `Jogador - Hat-trick [Confronto]`
- Outros limiares (N≥2, exceto 3): `Jogador - N+ Gols [Confronto]`
- **Primeiro Marcador** (Primeiro Marcador de Gol / Para Marcar Primeiro): `Jogador - Primeiro Marcador [Confronto]`
- **Último Marcador** (Último Marcador de Gol / Para Marcar Por Último): `Jogador - Último Marcador [Confronto]`

> O sinal do mercado é a **linha "Para Marcar…"** do bilhete (presente em todo card). Parênteses ao lado do nome (`(2 ou Mais)`, `(A Qualquer Altura)`) são inconsistentes / qualificadores — **não** usar como fonte do limiar.

> ⚠️ **O sufixo é OBRIGATÓRIO — sem ele, bilhetes DISTINTOS colapsam numa descrição idêntica.** `2+ Gols`, `Hat-trick`, `Primeiro Marcador` e `Último Marcador` são **mercados diferentes** do `anytime` (1+) e diferentes **entre si**. Omitir o sufixo faz dois bilhetes reais virarem texto igual. Exemplo real: `Kylian Mbappe - Primeiro Marcador [França v Marrocos]` (ganhou) e `Kylian Mbappe - Último Marcador [França v Marrocos]` (perdeu), **mesma stake e mesma odd** — sem o sufixo os dois viram `Kylian Mbappe [França v Marrocos]` e o sistema os confunde como duplicata. Cada mercado carrega o seu sufixo, **sempre**. E o `[Confronto]` é igualmente obrigatório: sem ele, o mesmo mercado do mesmo jogador em jogos diferentes também colapsa.

Formato:

```text
Jogador [Confronto]                        ← 1+ (anytime)
Jogador - 2+ Gols [Confronto]              ← 2+
Jogador - Hat-trick [Confronto]            ← 3+
Jogador - Primeiro Marcador [Confronto]    ← primeiro a marcar
Jogador - Último Marcador [Confronto]      ← último a marcar
```

Exemplos:

```text
Mbappé [PSG v Marseille]
Raphinha [Barcelona v Real Madrid]
Daniel Rios - 2+ Gols [Vancouver FC v CF Montreal]
Daniel Rios - Hat-trick [Vancouver FC v CF Montreal]
Kylian Mbappe - Primeiro Marcador [França v Marrocos]
Kylian Mbappe - Último Marcador [França v Marrocos]
```

---

## 12.2 Assistência (Futebol)

Formato:

```text
Jogador [Confronto]
```

Exemplo:

```text
Kevin De Bruyne [Manchester City v Arsenal]
```

---

## 12.3 Player Props

Formato:

```text
Jogador - Linha Mercado [Confronto]
```

Exemplos:

```text
Anthony Davis - 10+ Rebotes [LAL Lakers v CHI Bulls]
Anthony Davis - Under 10.5 Rebotes [LAL Lakers v CHI Bulls]
Ja Morant - Over 7.5 Assistências [MEM Grizzlies v PHI 76ers]
```

**Substituição de jogador:** Quando o bilhete indica que o jogador original foi substituído, SEMPRE usar o nome do jogador ORIGINAL (aquele por quem a aposta foi feita). Ignore o nome do substituto.

Sinal visual (varia por casa): nome original aparece riscado/tachado; substituto em destaque acima, frequentemente com um badge ("SUBSTITUIÇÃO+", "SUB", ou similar).

```text
✓ Correto:  Benjamin Nygren - Jogador a Dar Assistência [Suécia v Tunisia]
✗ Errado:   Lucas Bergvall - Jogador a Dar Assistência [Suécia v Tunisia]
```

---

## 12.4 Múltiplos Mercados do Mesmo Jogador

Quando um mesmo jogador possuir múltiplos mercados dentro da mesma seleção:

Formato:

```text
Jogador - Mercado A / Mercado B [Confronto]
```

Exemplo:

```text
Russell Westbrook - 10+ Assistências / 10+ Pontos [SAC Kings v LA Clippers]
```

---

## 12.5 Totais do Jogo

Formato:

```text
Mercado [Confronto]
```

Exemplos:

```text
Over 2.5 Gols [Parma v Fiorentina]
Under 220.5 Pontos [LAL Lakers v CHI Bulls]
Over 5.5 Legs [Luke Littler v Luke Humphries]
```

---

## 12.6 Handicap

Formato:

```text
Entidade Linha [Confronto]
```

Exemplos:

```text
Everton +0.5 [Nottingham Forest v Everton]
Lakers -4.5 [LAL Lakers v CHI Bulls]
Alcaraz -2.5 Games [Sinner v Alcaraz]
Luke Littler -1.5 Legs [Luke Littler v Luke Humphries]
```

---

## 12.7 ML

Formato:

```text
Entidade [Confronto]
```

Exemplos:

```text
Lakers [LAL Lakers v CHI Bulls]
Manchester City [Manchester City v Arsenal]
Sinner [Sinner v Alcaraz]
Luke Littler [Luke Littler v Luke Humphries]
```

---

## 12.8 H2H

H2H utiliza exatamente o mesmo formato textual do ML.

A diferença pertence exclusivamente à coluna:

```text
Aposta
```

Formato:

```text
Entidade [Confronto]
```

---

## 12.9 Dupla Chance

Formato:

```text
Opção [Confronto]
```

Opções válidas:

```text
1X  →  Casa ou Empate
X2  →  Empate ou Visitante
12  →  Casa ou Visitante
```

Exemplos:

```text
1X [Manchester City v Arsenal]
X2 [PSG v Marseille]
12 [Barcelona v Real Madrid]
```

Usar sempre o símbolo (`1X`, `X2`, `12`), nunca a descrição textual — o símbolo é universal e elimina ambiguidade sobre qual time é casa ou visitante.

---

# 13. Templates Específicos por Esporte

---

## 13.1 Tênis

---

### ML

```text
Sinner [Sinner v Alcaraz]
```

---

### Games

```text
Over 22.5 Games [Sinner v Alcaraz]
```

---

### Sets

```text
Under 2.5 Sets [Sinner v Alcaraz]
```

---

### Handicap

```text
Alcaraz -3.5 Games [Sinner v Alcaraz]
```

---

### Player Props

```text
Sinner - Over 8.5 Aces [Sinner v Alcaraz]
```

---

## 13.2 Dardos

---

### ML

```text
Luke Littler [Luke Littler v Luke Humphries]
```

---

### Legs

```text
Over 5.5 Legs [Luke Littler v Luke Humphries]
```

---

### Handicap

```text
Luke Humphries +1.5 Legs [Luke Littler v Luke Humphries]
```

---

### Player Props

```text
Luke Littler - Over 3.5 180s [Luke Littler v Luke Humphries]
```

---

### H2H 180's

Mercado comparativo de quem faz mais 180s no confronto. Usar `Aposta = H2H`.

Formato:

```text
Jogador - Mais 180's [Jogador A v Jogador B]
```

Exemplo:

```text
Luke Littler - Mais 180's [Luke Littler v Luke Humphries]
```

**Reconstrução do confronto (Bet365 / Betfair):** o bilhete exibe dois nomes sem o formato `A v B` explícito. O jogador em negrito / primeira posição = apostado (entidade); o segundo nome = adversário. Confronto = `[apostado v adversário]`.

---

## 13.3 eBasket

Basquete virtual (NBA 2K). Usa os templates do Basquete — a única especificidade é
o **handle do gamer**.

---

### Regra Crítica — preservar o handle

O confronto deve manter o handle entre parênteses, **exatamente como no bilhete**:

```text
[OKC Thunder (BRAZEN) v NY Knicks (EQUALIZER)]
```

Nunca remover o handle:

```text
[OKC Thunder v NY Knicks]        ← PROIBIDO
```

> **Motivo:** o time NBA é apenas uma skin — quem joga é o gamer. Sem o handle,
> `DAL Mavericks (TD24) v CHA Hornets (HYPER)` e `CHA Hornets (PROTOTYPE) v DAL
> Mavericks (GALAXY)` colapsam no mesmo confronto, e dois bilhetes distintos viram
> duplicata na régua de dedup (stake + odd + descrição). O handle é a identidade
> do participante, como o nome do jogador em Tênis.

Preservar a grafia do handle em maiúsculas, como a casa exibe.

---

### Pontos (total do jogo)

```text
Over 92.5 Pontos [OKC Thunder (BRAZEN) v NY Knicks (EQUALIZER)]
```

---

### Pontos (total do time)

```text
OKC Thunder (BRAZEN) Over 49.5 Pontos [OKC Thunder (BRAZEN) v NY Knicks (EQUALIZER)]
```

---

### ML

```text
OKC Thunder (BRAZEN) [OKC Thunder (BRAZEN) v NY Knicks (EQUALIZER)]
```

---

### Handicap

```text
NY Knicks (EQUALIZER) +4.5 [OKC Thunder (BRAZEN) v NY Knicks (EQUALIZER)]
```

---

# 14. Múltiplas

Múltiplas devem separar seleções utilizando:

```text
 // 
```

(espaço + barra dupla + espaço)

---

## Exemplo

```text
Ja Morant - Over 7.5 Assistências [MEM Grizzlies v PHI 76ers] // Over 2.5 Gols [Parma v Fiorentina]
```

---

# 15. Ordem das Seleções

Em múltiplas:
- preservar a ordem original do bilhete
- nunca reordenar seleções
- nunca agrupar automaticamente

---

# 16. Separadores Oficiais

| Contexto | Separador |
|---|---|
| Entidade ↔ Mercado | ` - ` |
| Mercados do mesmo jogador | ` / ` |
| Seleções diferentes | ` // ` |
| Confronto | ` v ` |

---

# 17. Conteúdo Proibido

A descrição nunca deve conter:
- odds
- stake
- resultado
- placar
- campeonato
- liga
- horário
- data
- ID da aposta
- status da aposta

---

# 18. Fallback

Utilizar fallback apenas quando:
- entidade não puder ser identificada
- mercado não puder ser identificado
- reconstrução falhar completamente

Formato oficial:

```text
Mercado Especial - REVISAR
```

Esse fallback deve ser extremamente raro.

---

# 19. Validação Final

Antes de retornar a saída, o extrator deve validar:

1. descrição não contém valores financeiros
2. descrição não contém odds
3. descrição não contém resultado
4. confronto segue o padrão `[A v B]`
5. separador do confronto é `v`
6. Over/Under está em inglês
7. múltiplas utilizam ` // `
8. múltiplos mercados utilizam ` / `
9. entidade ↔ mercado utilizam ` - `
10. confronto não foi inventado
11. ordem original das seleções foi preservada
12. em eBasket, o handle do gamer foi preservado no confronto (§13.3)

Caso o confronto não possa ser identificado com segurança, a descrição permanece válida sem confronto.

---

VERSÃO: 2026  
STATUS: ATIVO  
USO: Extratores de apostas esportivas