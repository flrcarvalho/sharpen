# MASTER_APOSTAS_2026
## Padrão Oficial da Coluna `Aposta` — Extrações de Apostas (2026)

Este documento define o padrão oficial da coluna:

```text
Aposta
```

Ele é a fonte única de verdade para:
- classificação de mercados
- taxonomia oficial de apostas
- regras de prioridade
- normalização de categorias
- desambiguação entre mercados similares

Todos os extratores devem obedecer exatamente este padrão.

---

# 1. Regras Gerais

A coluna `Aposta` deve conter apenas categorias definidas neste documento.

Nunca:
- inventar categorias
- alterar capitalização
- criar aliases
- misturar categorias semanticamente diferentes

**Princípio fundamental:** a categoria registra o **objeto** da aposta — o que está sendo medido — não o tipo de mercado (linha, handicap, total, ML, comparativo).

Dentro de qualquer categoria pode existir um mercado de handicap, total (over/under), resultado comparativo (ML) ou linha. A categoria não muda por causa disso.

Exemplos:
- `-3 cartões Time A` → `Cartões`
- `0,5 escanteios` → `Escanteios`
- `Time B handicap -3,5 finalizações` → `Chutes`
- `Time A mais chutes` (comparativo) → `Chutes`
- `Time B mais escanteios` (comparativo) → `Escanteios`
- `Time A -1,5 impedimentos` → `Impedimentos`
- `Primeiro a marcar 9 escanteios` (race / corrida) → `Escanteios`

---

# 2. Prioridade de Classificação

A classificação deve seguir obrigatoriamente esta ordem:

1. Categoria específica da tabela
2. Regra específica por esporte
3. `Player Props`
4. `Outros`

Nunca utilizar:
```text
Player Props
```

ou:
```text
Outros
```

quando existir categoria mais específica aplicável.

---

# 3. Tabela Oficial de Categorias

| Categoria | Descrição Oficial |
|---|---|
| Ambas Marcam | Mercado de ambas equipes marcam |
| Anytime | Jogador para marcar a qualquer momento |
| Assistência | Assistência de jogador em Futebol |
| Cartões | Mercados de cartões |
| Chutes | Mercados de total de finalizações |
| Chutes no Gol | Mercados de finalizações no alvo (shots on target) |
| Corridas | Mercados de corridas e estatísticas de Baseball |
| Desarmes | Mercados de tackles/desarmes |
| DNB | Draw No Bet / Empate anula |
| Dupla Chance | Mercado de resultado com duas alternativas cobertas |
| Double-Double | Mercado específico de basquete |
| E-Sports Props | Estatísticas específicas de E-Sports |
| Escanteios | Mercados de escanteios |
| Games | Mercados de games em Tênis |
| Gols | Mercados de gols |
| H2H | Mercado comparativo entre duas entidades |
| Handicap | Handicap / Spread / Linha |
| Impedimentos | Mercados de impedimentos em Futebol |
| Jardas | Mercados de jardas em NFL |
| Legs | Mercados de legs em Dardos |
| ML | Resultado principal do evento |
| Múltipla | Cupom com múltiplas seleções |
| Outros | Último recurso |
| Player Props | Estatísticas individuais de jogador |
| Pontos | Mercados de pontos de jogo ou de time (Basquete / eBasket) |
| Sets | Mercados de sets |
| Team Props | Estatísticas de equipe |
| Triplo-Duplo | Mercado específico de basquete |

---

# 4. Sinônimos Oficiais

---

## Ambas Marcam

Sinônimos:
- BTTS
- Both Teams To Score
- Ambas equipes marcam

---

## Anytime

Sinônimos:
- Anytime scorer
- Marcar a qualquer momento
- Para marcar
- Anytime Goal Scorer
- Para marcar 2 ou mais / dois ou mais gols (marcador 2+)
- Para marcar 3 ou mais / três ou mais gols (marcador 3+)
- Hat-trick / marcar um hat-trick

> `Anytime` cobre toda a família "jogador para marcar", inclusive os limiares 2+/3+. O **limiar não muda a categoria** — vai na Descrição (`MASTER_DESCRICAO_2026 §12.1`): 1+ sem sufixo, 2+ = `- 2+ Gols`, 3+ = `- Hat-trick`.

---

## Assistência

Sinônimos:
- Assists
- Assistências
- Passe para gol

---

## Cartões

Sinônimos:
- Cards
- Cartão
- Cartões totais
- Mais cartões
- Para o Jogador Receber Cartão
- Para Receber Cartão
- Cartão Amarelo para Jogador

**Mercados para jogador específico:** mesmo que o mercado envolva um jogador individual (ex: "Nico Williams — Para o Jogador Receber Cartão"), a categoria é `Cartões`, NUNCA `Player Props`. O objeto apostado é o cartão, não uma estatística pessoal do jogador. Princípio §1: categoria = objeto apostado.

---

## Chutes

Sinônimos:
- Shots
- Finalizações
- Total de chutes
- Total de finalizações

---

## Chutes no Gol

Sinônimos:
- SOT
- Shots on Target
- Finalizações no Gol
- Chutes no alvo
- Chutes a gol

---

## Corridas

Sinônimos:
- Runs
- RBIs
- Bases
- Home Runs

---

## Desarmes

Sinônimos:
- Tackles
- Interceptions
- Desarmes

---

## DNB

Sinônimos:
- Draw No Bet
- Empate anula aposta

---

## Dupla Chance

Sinônimos:
- Double Chance
- 1X
- X2
- 12

---

## Double-Double

Sinônimos:
- Double-Double
- Duplo Duplo

---

## E-Sports Props

Sinônimos:
- E-Sports Props
- Estatísticas de E-Sports
- Kills / Deaths / Assists (over/under de jogador)
- Total de Kills / Abates
- Map / Series Total (estatística de E-Sports)

> Sempre que o objeto for estatística de E-Sports, a categoria é `E-Sports Props`
> (nunca `Player Props`) e o Esporte é `E-Sports` — ver §6 (E-Sports) e §7 (prioridade).

---

## Escanteios

Sinônimos:
- Corners
- Cantos
- Escanteio
- Primeiro a marcar X escanteios (race / corrida)
- Race to X corners
- Corrida de escanteios

---

## Games

Sinônimos:
- Games
- Mais/Menos games

---

## Gols

Sinônimos:
- Goals
- Total de gols
- Mais/Menos gols

---

## H2H

Sinônimos:
- Head to Head
- Duelo
- Match Bet
- Matchup
- Mais 180's (Dardos)
- Maioria de 180's (Dardos)
- 180s H2H (Dardos)

---

## Handicap

Sinônimos:
- Handicap
- Spread
- Linha
- Asian Handicap

---

## Impedimentos

Sinônimos:
- Offsides
- Impedimento
- Total de impedimentos

---

## Jardas

Sinônimos:
- Yards
- Passing Yards
- Rushing Yards
- Receiving Yards

---

## Legs

Sinônimos:
- Legs
- Mais/Menos legs

---

## ML

Sinônimos:
- Moneyline
- Resultado final
- Vencedor
- Winner

---

## Múltipla

Sinônimos:
- Parlay
- Acumulada
- Dupla
- Tripla

---

## Player Props

Sinônimos:
- Props
- Player Specials
- Aposta do jogador

---

## Pontos

Sinônimos:
- Points
- Total de Pontos
- Mais/Menos pontos
- Totais do Jogo (Basquete / eBasket)
- Total - 2 Opções (Basquete / eBasket)
- Total de Pontos do Time
- Team Total Points

> `Pontos` cobre o total de pontos do **jogo** ou de um **time**. Pontos de um
> **jogador** continuam `Player Props` — ver §5 (Pontos) e §7 (prioridade).
> Os rótulos `Totais do Jogo` e `Total - 2 Opções` só significam `Pontos` em
> Basquete / eBasket; em outros esportes seguem o objeto (Futebol → `Gols`).

---

## Sets

Sinônimos:
- Sets
- Mais/Menos sets

---

## Team Props

Sinônimos:
- Team Totals
- Total do time
- Especial do time
- Tiros de Meta
- Total de Tiros de Meta

---

## Triplo-Duplo

Sinônimos:
- Triple-Double
- Triplo Duplo

---

# 5. Regras Oficiais por Categoria

---

## ML

`ML` representa:

```text
Resultado principal do evento
```

Exemplos:
- vencedor da partida
- vencedor do confronto
- vencedor do mapa
- vencedor da luta

---

## H2H

`H2H` representa:

```text
Mercado comparativo entre duas entidades específicas,
independentemente do resultado principal do evento.
```

Exemplos:
- piloto A vs piloto B
- jogador A vs jogador B
- mais rebotes
- mais assistências
- mais kills
- mais jardas
- mais pontos
- mais 180's (Dardos — quem faz mais 180s no confronto)

H2H não deve ser confundido com:
- ML
- Handicap
- Player Props

---

## Player Props

`Player Props` é uma categoria genérica para estatísticas individuais de jogador.

Utilizar apenas quando:
- não existir categoria mais específica
- o mercado for estatístico individual

**NÃO usar `Player Props` quando o objeto apostado tiver categoria própria**, mesmo que o mercado envolva um jogador específico:
- Jogador receber cartão → `Cartões`
- Jogador marcar a qualquer momento → `Anytime`
- Jogador dar assistência → `Assistência`

---

## Team Props

`Team Props` representa:
- totais de equipe
- estatísticas coletivas
- mercados específicos do time

Não confundir com:
- `Pontos` (total de pontos do jogo ou do time em Basquete / eBasket — tem categoria própria)

---

## Pontos

`Pontos` representa:

```text
Total de pontos do jogo ou de um time, em Basquete e eBasket.
```

É a categoria da unidade de pontuação do basquete, equivalente a `Gols` (Futebol),
`Games` (Tênis), `Legs` (Dardos) e `Sets` (Vôlei).

Como qualquer categoria, admite over/under, handicap de total ou comparativo — o
tipo de mercado não altera a classificação (§1).

**Discriminante — a entidade apostada** (mesmo critério de `Sets`):

| Entidade no mercado | Categoria |
|---|---|
| Jogo inteiro (soma dos dois times) | `Pontos` |
| Time | `Pontos` |
| Jogador individual | `Player Props` |

Exemplos:

```text
Under 220.5 [LAL Lakers v CHI Bulls]          → Pontos   (total do jogo)
Mais de 92.5 [OKC Thunder v NY Knicks]        → Pontos   (total do jogo, eBasket)
OKC Thunder Mais de 49.5 [OKC v NY]           → Pontos   (total do time)
Mitchell Robinson - Under 3.5 Pontos [SA v NY] → Player Props (jogador)
```

Não confundir com:
- `Player Props` (pontos de jogador — ver §6 NBA / Basquete)
- `Team Props` (outras estatísticas coletivas: tiros de meta, etc.)
- `Handicap` (spread do resultado, não total de pontos)

---

## Múltipla

Utilizar:

```text
Múltipla
```

quando houver:
- múltiplas seleções independentes
- parlay
- acumulada
- dupla
- tripla

A descrição deve utilizar:

```text
//
```

entre seleções.

---

## Bet Builder / Criar Aposta

Bet Builder deve ser classificado como:

```text
Múltipla
```

mesmo quando todas as seleções forem do mesmo jogo.

A distinção é apenas visual/operacional da casa.

---

## Impedimentos

Mercado de total de impedimentos em partidas de Futebol.

Aplicável exclusivamente ao Futebol.

Não confundir com:
- `Gols` (finalizações convertidas)
- `Chutes` (finalizações totais)
- `Team Props` (estatísticas coletivas genéricas)

---

## Desambiguação — Mercados Estatísticos de Futebol

Categorias distintas que não devem ser confundidas:

| Categoria     | O que mede                              |
|---------------|-----------------------------------------|
| Gols          | Finalizações convertidas (gols marcados) |
| Chutes no Gol | Finalizações que acertaram o alvo (SOT) |
| Chutes        | Total de finalizações (no alvo ou não)  |
| Escanteios    | Escanteios                              |
| Impedimentos  | Impedimentos                            |
| Cartões       | Cartões amarelos e/ou vermelhos         |

Cada uma dessas categorias pode conter mercados de handicap, total (over/under), resultado comparativo (time A vs time B) ou linha. O tipo de mercado não altera a categoria — apenas o objeto apostado define a classificação.

---

## Race (Primeiro a marcar X)

"Race" (corrida) é um **tipo de mercado**, não uma categoria. Aposta-se em qual entidade atinge **primeiro** um número inteiro de eventos (escanteios, gols, pontos, cartões…). Sinônimos da casa: `Primeiro a marcar X`, `Race to X`, `Corrida para X`.

Como qualquer tipo de mercado, a categoria segue o **objeto** apostado (§1):

| Mercado da casa | Categoria |
|---|---|
| Primeiro a marcar X escanteios | `Escanteios` |
| Primeiro a marcar X gols | `Gols` |
| Primeiro a marcar X pontos (time/jogo) | `Pontos` |
| Primeiro a marcar X pontos (jogador) | `Player Props` |
| Primeiro a receber X cartões | `Cartões` |

A estrutura "Race" e o número X ficam na **Descrição** (`MASTER_DESCRICAO_2026 §10.3`), nunca na categoria.

Não confundir com:
- `ML` (vencedor da partida — Race tem descrição própria com `Race N`)
- `Anytime` (marcar a qualquer momento, sem alvo numérico)

---

## Dupla Chance

Mercado onde duas das três alternativas de resultado são cobertas:
- 1X: Casa ou Empate
- X2: Empate ou Visitante
- 12: Casa ou Visitante

Aplicável principalmente ao Futebol.

Não confundir com:
- `ML` (cobre apenas uma alternativa)
- `DNB` (empate anula a aposta, não cobre duas alternativas)

---

# 6. Regras Específicas por Esporte

---

## Futebol

---

### Gol de jogador

Classificar como:

```text
Anytime
```

Exemplos:
- Harry Kane para marcar
- Mbappé Anytime Scorer

**Limiar 2+/3+:** mercados "Para Marcar 2 ou Mais" / "dois ou mais gols" e "Hat-trick" / "três ou mais gols" **continuam `Anytime`** — o limiar vai só na Descrição (`MASTER_DESCRICAO_2026 §12.1`: `- 2+ Gols`, `- Hat-trick`), nunca vira categoria própria.

---

### Assistência de jogador

Classificar como:

```text
Assistência
```

Exemplos:
- Kevin De Bruyne assistência
- Lucas Moura dar assistência

---

### Resultado da partida

Sem handicap:

```text
ML
```

Com handicap:

```text
Handicap
```

---

### Total de gols

Classificar como:

```text
Gols
```

---

### Chutes (total de finalizações)

Classificar como:

```text
Chutes
```

Inclui: handicap de chutes, total de chutes, time com mais chutes.

---

### Chutes no Gol (finalizações no alvo / SOT)

Classificar como:

```text
Chutes no Gol
```

Inclui: handicap de SOT, total de chutes no alvo, time com mais chutes no gol.

---

### Ambas marcam

Classificar como:

```text
Ambas Marcam
```

---

### Dupla Chance

Classificar como:

```text
Dupla Chance
```

---

### Impedimentos

Classificar como:

```text
Impedimentos
```

---

### Tiros de Meta

Classificar como:

```text
Team Props
```

Não confundir com:
- `Chutes no Gol` (finalizações no alvo / SOT)
- `Chutes` (total de finalizações)

Tiro de Meta = bola sai pela linha de fundo após toque do atacante; o goleiro reinicia o jogo.
É uma estatística de pressão/posse, não de finalização.

---

## NBA / Basquete

### Total de pontos (jogo ou time)

Classificar como:

```text
Pontos
```

Inclui: over/under do total do jogo, total de um time, handicap de total de pontos.

Exemplos:
- `Under 220.5 [LAL Lakers v CHI Bulls]` → `Pontos`
- `OKC Thunder Mais de 49.5 [OKC v NY]` → `Pontos`

---

### Estatísticas individuais de jogador

Qualquer estatística individual de jogador deve ser classificada como:

```text
Player Props
```

Inclui:
- pontos
- rebotes
- assistências
- PRA
- PR
- PA
- roubos
- blocks
- turnovers
- estatísticas combinadas

Mesmo quando existir equivalência matemática com outras categorias.

---

### Exceções

Mercados específicos devem manter categoria própria:

```text
Double-Double
Triplo-Duplo
```

---

## eBasket

O eBasket (basquete virtual / NBA 2K) usa a **mesma taxonomia do Basquete** — muda
apenas o valor da coluna `Esporte` (ver `MASTER_ESPORTES_2026`).

---

### Total de pontos (jogo ou time)

Classificar como:

```text
Pontos
```

Rótulos usuais da casa: `Totais do Jogo`, `Total - 2 Opções`.

Exemplo:
- `Mais de 92.5 [OKC Thunder v NY Knicks]` → `Pontos`

---

### Resultado principal

Sem handicap:

```text
ML
```

Com handicap:

```text
Handicap
```

---

### Estatísticas individuais

Classificar como:

```text
Player Props
```

> ⚠️ Nunca usar `E-Sports Props` em eBasket. `E-Sports Props` é exclusivo do
> Esporte `E-Sports` (invariante do `MASTER_ESPORTES_2026 §7`) e o vocabulário
> dele (kills, mapas, torres) não existe no basquete virtual.

---

## NFL

---

### Jardas

Classificar como:

```text
Jardas
```

---

### Touchdown de jogador

Classificar como:

```text
Anytime
```

---

### Resultado principal

Sem handicap:

```text
ML
```

Com handicap:

```text
Handicap
```

---

## Baseball

---

### Corridas e RBIs

Classificar como:

```text
Corridas
```

---

### Strikeouts e estatísticas individuais

Classificar como:

```text
Player Props
```

---

## Tênis

---

### Resultado principal

Sem handicap:

```text
ML
```

Com handicap:

```text
Handicap
```

---

### Total de games

Classificar como:

```text
Games
```

---

### Total de sets

Classificar como:

```text
Sets
```

---

### Estatísticas individuais

Classificar como:

```text
Player Props
```

Exemplos:
- aces
- double faults
- break points

---

### Regras Críticas — Tênis

Tênis utiliza:
- games
- sets

Nunca utilizar:
- legs
- frames

---

## Dardos

---

### Resultado principal

Sem handicap:

```text
ML
```

Com handicap:

```text
Handicap
```

---

### Total de legs

Classificar como:

```text
Legs
```

---

### Estatísticas individuais (over/under de um jogador)

Classificar como:

```text
Player Props
```

Exemplos:
- Over 3.5 180s (de um jogador específico)
- checkout
- highest finish

---

### H2H de 180's (mercado comparativo)

Quando o mercado compara qual dos dois jogadores fará **mais 180s** no confronto, classificar como:

```text
H2H
```

Sinalizadores: "Mais 180's" / "Maioria de 180's" / equivalente em inglês "Most 180s".

⚠️ Não confundir com Player Props:
- `Over 3.5 180s [Littler v Humphries]` → **Player Props** (total individual de um jogador)
- `Luke Littler - Mais 180's [Littler v Humphries]` → **H2H** (comparativo entre os dois)

---

### Regras Críticas — Dardos

Dardos utiliza:
- legs

Nunca utilizar:
- games
- sets
- frames

---

## Vôlei

---

### Resultado principal

Sem handicap:

```text
ML
```

Com handicap (de sets):

```text
Handicap
```

---

### Total de sets

Classificar como:

```text
Sets
```

> Nota: a categoria `Sets` também aparece em Tênis. O discriminante é a entidade apostada:
> - time / seleção + sets → Vôlei
> - jogador individual / dupla + sets → Tênis

---

### Estatísticas individuais

Classificar como:

```text
Player Props
```

---

## E-Sports

---

### Resultado principal

Classificar como:

```text
ML
```

---

### Handicap de rounds/mapas

Classificar como:

```text
Handicap
```

---

### Estatísticas individuais

Classificar como:

```text
E-Sports Props
```

Inclui: kills, deaths, assists, torres, dragões, inibidores, bombas plantadas e qualquer estatística específica do universo de e-sports.

Nunca utilizar `Player Props` para estatísticas de E-Sports — `E-Sports Props` tem prioridade.

---

# 7. Regras de Prioridade Semântica

Mercados específicos possuem prioridade sobre categorias genéricas.

Exemplos:

```text
Games          > Player Props          (→ Tênis)
Legs           > Player Props          (→ Dardos)
H2H            > Player Props          (→ Dardos 180s comparativo)
Anytime        > Player Props
Assistência    > Player Props
E-Sports Props > Player Props
Sets (time)    > Player Props          (→ Vôlei)
Sets (jogador) > Player Props          (→ Tênis)
Pontos         > Team Props            (→ Basquete / eBasket)
Pontos         > Handicap              (total de pontos ≠ spread)
```

Desambiguação da categoria `Sets`:
- `Sets` com **time / seleção** → Vôlei
- `Sets` com **jogador individual / dupla** → Tênis

Desambiguação da categoria `Pontos` (Basquete / eBasket):
- pontos do **jogo** (soma dos dois times) → `Pontos`
- pontos de um **time** → `Pontos`
- pontos de um **jogador** → `Player Props` (§6 NBA / Basquete)

> `Player Props` tem prioridade sobre `Pontos` **apenas** quando a entidade for um
> jogador. Sem jogador nomeado, o total é sempre `Pontos` — nunca `Team Props`
> nem `Outros`.

Marcador discreto vs total de gols do jogador (Futebol):
- `Para Marcar N ou Mais` / `Hat-trick` (mercado sim/não de marcar) → `Anytime`, limiar na descrição (`MASTER_DESCRICAO_2026 §12.1`)
- `Total de Gols do Jogador` Over/Under X.5 (linha numérica) → `Player Props`

Nunca utilizar:
```text
Player Props
```

por conveniência.

---

# 8. Uso de Outros

`Outros` é exclusivamente o último recurso.

Utilizar apenas quando:
- nenhuma categoria do documento se aplicar
- o mercado for genuinamente novo
- não houver classificação semanticamente segura

---

# 9. Validação Final

Antes de retornar a saída, o extrator deve validar:

1. a categoria existe neste documento
2. a capitalização está correta
3. nenhuma categoria inventada foi criada
4. `Games` não foi usado para Dardos
5. `Legs` não foi usado para Tênis
6. `Player Props` não foi utilizado quando havia categoria específica
7. `E-Sports Props` foi utilizado para estatísticas de E-Sports (nunca `Player Props`)
8. `Outros` foi utilizado apenas como último recurso
9. `Bet Builder` foi classificado como `Múltipla`
10. `Assistência` foi utilizado apenas para Futebol
11. mercados comparativos foram corretamente classificados como `H2H`
12. `Dupla Chance` foi utilizado apenas para mercados 1X / X2 / 12 (exclusivo do Futebol)
13. `Impedimentos` foi utilizado apenas para Futebol
14. `Chutes no Gol` foi utilizado apenas para finalizações no alvo (SOT) — nunca para total de finalizações (`Chutes`)
15. `Sets` com nome de **time / seleção** = Vôlei (nunca Tênis, exceto Copa Davis explícita)
16. `Sets` com nome de **jogador individual / dupla** = Tênis (nunca Vôlei)
17. mercado "Mais 180's" / "Maioria de 180's" em Dardos foi classificado como `H2H` (nunca `Player Props` nem `Legs`)
18. total de pontos de **jogo ou time** em Basquete / eBasket = `Pontos` (nunca `Team Props`, `Handicap` nem `Outros`)
19. pontos de **jogador** em Basquete / eBasket = `Player Props` (nunca `Pontos`)
20. `E-Sports Props` não foi utilizado em eBasket (é exclusivo do Esporte `E-Sports`)

Se qualquer regra falhar, a linha deve ser considerada inválida.

---

VERSÃO: 2026  
STATUS: ATIVO  
USO: Extratores de apostas esportivas