# MASTER_ESPORTES_2026
## Padrão Oficial da Coluna `Esporte` — Extrações de Apostas (2026)

Este arquivo define o padrão oficial da coluna:

```text
Esporte
```

Ele é a fonte única de verdade para:
- normalização de esportes
- identificação contextual
- desambiguação semântica
- resolução de conflitos entre modalidades

Todos os extratores devem obedecer exatamente este padrão.

---

# 1. Regras Gerais

A coluna `Esporte` deve conter apenas valores definidos neste documento.

Nunca:
- inventar novos esportes
- alterar capitalização
- usar abreviações não definidas
- misturar idiomas

Se o esporte não puder ser identificado com segurança:

```text
Outro
```

---

# 2. Uso de Múltiplos

Utilizar:

```text
Múltiplos
```

exclusivamente quando uma única aposta misturar esportes diferentes.

Exemplo:

- Futebol
- Basquete

Resultado:

```text
Múltiplos
```

Nunca utilizar `Múltiplos`:
- em múltiplas do mesmo esporte
- em bet builders
- em combinações do mesmo jogo

---

# 3. Uso de Outro

Utilizar:

```text
Outro
```

apenas quando:
- o esporte não existir neste documento
- a identificação for genuinamente ambígua
- não houver contexto suficiente

Nunca utilizar `Outro` quando o esporte puder ser deduzido por:
- confronto
- nomes dos participantes
- mercado
- liga
- contexto do bilhete

---

# 4. Padronização de Escrita

A coluna `Esporte` deve utilizar exatamente os valores definidos neste documento.

Exemplos válidos:

```text
Futebol
Basquete
Futebol Americano
Hóquei
Tênis
Dardos
MMA
E-Sports
```

Exemplos inválidos:

```text
FUTEBOL
basquete
NBA
NFL
NHL
darts
tenis
```

---

# 5. Prioridade de Identificação

Quando o esporte não estiver explicitamente informado, identificar seguindo esta ordem:

1. Mercado especializado
2. Liga/Torneio — é pista de identificação; o valor final é sempre o esporte (ex.: NBA → Basquete, NFL → Futebol Americano)
3. Nomes dos participantes
4. **Conhecimento próprio do modelo** — quando o participante não estiver nas listas auxiliares, usar o conhecimento de treinamento para identificar o esporte de carreira do atleta. Exemplos: um tenista do circuito ITF não listado ainda deve ser classificado como Tênis; um dardista do circuito MODUS não listado deve ser classificado como Dardos. Só usar `Outro` quando genuinamente incerto após esgotar esse recurso.
5. Contexto geral do bilhete

# 5.1 Prioridade Semântica — Confronto

Quando houver confronto identificado:

- priorizar o confronto como principal fonte de inferência esportiva
- participantes possuem prioridade superior ao mercado textual
- nomes dos participantes possuem prioridade superior ao nome genérico do mercado

Exemplos:

[Celta de Vigo v Levante]
→ Futebol

[OKC Thunder v LA Lakers]
→ Basquete

[Luke Littler v Luke Humphries]
→ Dardos

[HEROIC v Magic]
→ E-Sports

O mercado textual sozinho não possui prioridade sobre confronto válido.

---

## Regras Críticas — ML / H2H

Mercados:

```text
ML
H2H
Handicap
```

possuem alta ambiguidade semântica.

Nesses casos:
- o confronto deve possuir prioridade máxima
- participantes possuem prioridade superior ao mercado
- listas auxiliares de participantes devem ser utilizadas obrigatoriamente

Especialmente em:
- Tênis
- Dardos
- E-Sports

Nunca classificar:
- Dardos como Tênis
- Tênis como Dardos

apenas por similaridade estrutural do mercado.

---

# 6. Mercados Especializados — Prioridade Máxima

Mercados especializados possuem prioridade absoluta sobre contexto genérico.

---

## Dardos

Se houver:

```text
legs
```

classificar obrigatoriamente como:

```text
Dardos
```

---

## Tênis

Se houver:

```text
games
```

classificar obrigatoriamente como:

```text
Tênis
```

---

## Vôlei

Não há mercado exclusivo de Vôlei com sinal único (como `legs` para Dardos).

O principal sinal é **sets com nome de time ou seleção**:

```text
Brasil -1.5 sets → Vôlei
```

Ver "Regra de Desambiguação — Sets" na seção anterior.

---

# 7. Tabela Oficial de Normalização

---

## Futebol

Valor oficial:

```text
Futebol
```

Sinônimos:
- SOCCER
- FUTBOL
- FOOTBALL
- FUTEBOL

---

## Basquete

Valor oficial:

```text
Basquete
```

Sinônimos:
- BASKETBALL
- BASQUETE
- NBA
- WNBA
- BASQUETE/NBA
- National Basketball Association

---

## Futebol Americano

Valor oficial:

```text
Futebol Americano
```

Sinônimos:
- NFL
- AMERICAN FOOTBALL
- FUTEBOL AMERICANO
- National Football League

---

## Hóquei

Valor oficial:

```text
Hóquei
```

Sinônimos:
- NHL
- HOCKEY
- ICE HOCKEY
- National Hockey League

---

## F1

Valor oficial:

```text
F1
```

Sinônimos:
- FORMULA 1
- FORMULA ONE
- F1
- AUTOMOBILISMO
- GRAND PRIX

---

## Tênis

Valor oficial:

```text
Tênis
```

Sinônimos:
- TENIS
- TÊNIS
- ATP
- WTA
- ITF
- ITF Men's World Tennis Tour
- ITF Women's World Tennis Tour
- CHALLENGER
- ATP CHALLENGER
- GRAND SLAM
- WIMBLEDON
- ROLAND GARROS
- US OPEN
- AUSTRALIAN OPEN

---

### Referências auxiliares — Tênis

Utilizar os nomes abaixo como apoio de desambiguação em mercados ML/H2H. A lista não é exaustiva — **quando o atleta não estiver listado, usar conhecimento próprio do modelo para identificar o esporte** (ver §5 item 4). Complementar com sinais contextuais (ATP, WTA, ITF, Challenger, torneio).

**ATP:**
- Jannik Sinner
- Carlos Alcaraz
- Novak Djokovic
- Alexander Zverev
- Daniil Medvedev
- Taylor Fritz
- Casper Ruud
- Hubert Hurkacz
- Andrey Rublev
- Tommy Paul
- Ben Shelton
- Grigor Dimitrov
- Holger Rune
- Alex De Minaur
- Lorenzo Musetti
- Frances Tiafoe
- Stefanos Tsitsipas
- Felix Auger-Aliassime
- Jack Draper
- Ugo Humbert
- Sebastian Korda
- Arthur Fils
- Francisco Cerundolo
- Nicolas Jarry
- Tomas Machac
- Jiri Lehecka
- Karen Khachanov
- Lorenzo Sonego
- Nicolas Kicker
- Dmitry Popko
- Aleksandar Vukic
- Harry Wendelken

**ATP Challenger / ITF (exemplos de sessões recentes):**
- Keshav Chopra
- Kerem Yilmaz
- Mate Valkusz
- Pietro Orlando Fellin
- Mickael Kaouk
- Filiberto Fumagalli
- Vignesh Gogineni
- Bryce Nakashima
- Tanguy Genier
- Noah Karma
- Jan Kluczynski
- Zian Vanderstappen
- Felix Romeo
- Lucien Forrestier
- Dennis Andre Dutine
- Yoav Versloot
- Nand Vandepoele
- Melvin Vix
- Maximo Nagele
- Jorge Alonso-Cortes
- Juan Bautista Otegui
- Joao Victor Couto Loureiro

**WTA:**
- Aryna Sabalenka
- Iga Swiatek
- Coco Gauff
- Elena Rybakina
- Jasmine Paolini
- Naomi Osaka
- Jessica Pegula
- Madison Keys
- Barbora Krejcikova
- Mirra Andreeva
- Karolina Muchova
- Marketa Vondrousova
- Qinwen Zheng
- Emma Navarro
- Diana Shnaider
- Paula Badosa
- Donna Vekic
- Anna Kalinskaya
- Yulia Putintseva
- Mary Stoiana
- Tatiana Prozorova

**WTA / ITF (exemplos de sessões recentes):**
- Gaeul Jang
- Aishi Das
- Marie Vogt
- Mia Slama
- Elsa Bonelli
- Emily Seibold
- Monika Ekstrand
- Alina Shcherbinina
- Andrea Palazon Lacasa
- Min Liu (chinesa, ITF W50 — não confundir com "Ming Liu" do tênis de mesa)

---

## Dardos

Valor oficial:

```text
Dardos
```

Sinônimos:
- DARTS
- DARDOS
- PDC
- BDO
- WDF
- MODUS
- MODUS Super Series

---

### Referências auxiliares — Dardos

Utilizar os nomes abaixo como apoio de desambiguação em mercados ML/H2H. A lista não é exaustiva — **quando o atleta não estiver listado, usar conhecimento próprio do modelo para identificar o esporte** (ver §5 item 4). Complementar com sinais contextuais (PDC, MODUS, torneio, legs).

**PDC:**
- Luke Littler
- Luke Humphries
- Michael van Gerwen
- Gerwyn Price
- Jonny Clayton
- Nathan Aspinall
- Rob Cross
- Stephen Bunting
- Michael Smith
- Gary Anderson
- Peter Wright
- Dimitri Van den Bergh
- José de Sousa
- Callan Rydz
- Danny Noppert
- Martin Schindler
- Andrew Gilding
- Dave Chisnall
- Damon Heta
- Joe Cullen
- Chris Dobey
- Brendan Dolan
- John Henderson
- Josh Rock
- Ricardo Pietreczko
- Radek Szaganski
- Danny Ayres
- Gian van Veen
- Dirk van Duijvenbode
- Jermaine Wattimena
- Mike De Decker
- Krzysztof Ratajski
- Cameron Menzies
- Madars Razma
- Bradley O'Connor
- Nico Plovier

**MODUS Super Series / outros circuitos (exemplos de sessões recentes):**
- Dylan Slevin
- Sam Spivey
- Steve Johnstone
- Oliver Mitchell
- Joe Croft
- Alec Small

---

### Contextos auxiliares — Dardos

Os seguintes termos fortalecem identificação como Dardos:

**Termos de mercado:**
- 180
- checkout
- highest finish
- oche
- arrows
- Best of X Legs
- First to X Legs

**Ligas e torneios:**
- PDC
- BDO
- WDF
- MODUS
- MODUS Super Series
- Premier League Darts
- World Matchplay
- World Grand Prix
- UK Open
- Grand Slam of Darts
- Players Championship
- European Tour
- Masters (Dardos)

---

### Regra Crítica — Dardos vs Tênis

Dardos e Tênis possuem alta taxa de conflito semântico em mercados:

- ML
- H2H
- Handicap
- Over/Under

Regras obrigatórias (em ordem de prioridade):

1. `legs` / `Best of X Legs` / `First to X Legs` → **Dardos** (prioridade máxima)
2. `games` → **Tênis** (prioridade máxima)
3. Participantes da lista de Dardos → priorizar Dardos
4. Participantes da lista de Tênis → priorizar Tênis
5. Termos como `180`, `checkout`, `PDC`, torneios PDC → Dardos
6. Termos como `ATP`, `WTA`, `ace`, `break`, torneios Grand Slam → Tênis

**Regra de desempate — atleta não identificado:**
Quando o confronto for entre dois participantes individuais em mercado ML/H2H e nenhum deles puder ser identificado pelo conhecimento do modelo nem pelas listas auxiliares, e não houver nenhum sinal positivo de Dardos (`legs`, `checkout`, `PDC`, `BDO`, `WDF`, `MODUS`, torneios de dardos), o esporte padrão é **Tênis**. Nunca usar Dardos como padrão de desempate — o circuito ITF tem ordens de magnitude mais atletas de nicho do que os circuitos de Dardos.

Quando houver conflito genuinamente insolúvel:

```text
Outro
```

Nunca classificar Dardos como Tênis apenas por similaridade de mercado.

---

### Regra Crítica — Tênis vs Padel

**`Padel` NÃO é um esporte reconhecido neste documento.** Nunca emitir o valor `Padel` na coluna `Esporte` (viola §1 — "nunca inventar novos esportes").

Confrontos de duplas em notação `X/Y v W/Z` (ou `X/Y x W/Z`) são sinal **forte de Tênis (duplas)**, não de Padel. O modelo tende a confundir duplas de tênis com padel por similaridade estrutural — isso é proibido.

Regras obrigatórias (em ordem de prioridade):

1. Notação de duplas `X/Y v W/Z` em mercado ML/H2H → **Tênis (duplas)** por padrão.
2. Participantes da lista de Tênis (singles ou duplas) → **Tênis**.
3. Atletas identificáveis pelo conhecimento do modelo como tenistas → **Tênis** (ex.: Máximo González, Santiago González, Román Burruchaga, Thiago Tirante, Dominic Stricker, Braden Shick, Johannus Monday).
4. Termos como `games`, `set`, `tie-break`, `ace`, `break`, `ATP`, `WTA`, `ITF`, torneios Grand Slam/Challenger → **Tênis**.

**Regra de desempate:** quando o confronto for entre duplas (ou indivíduos) em mercado ML/H2H e nenhum sinal positivo de outro esporte estiver presente, o esporte é **Tênis** — nunca Padel. Só usar `Outro` se houver dúvida genuína entre Tênis e outro esporte reconhecido.

> **Motivo:** em 24/06/2026 a Betnacional classificou duas duplas/jogos de tênis (Máximo González/Santiago González v Burruchaga/Tirante; Johannus Monday v Braden Shick) como `Padel`. A causa foi um exemplo golden rotulado errado em `CASA_BETNACIONAL.md` (corrigido) somado à ausência desta regra.

---

### Regra de Desambiguação — Sets (Vôlei vs Tênis)

A categoria `Sets` aparece tanto em Vôlei quanto em Tênis. O discriminante é a entidade apostada:

| Entidade no mercado | Esporte |
|---|---|
| Nome de **jogador individual** ou dupla | Tênis |
| Nome de **time / seleção** | Vôlei |

Exemplos:

- `Alcaraz -1.5 sets` → **Tênis**
- `Brasil -1.5 sets` → **Vôlei**
- `Sinner v Djokovic — Over 2.5 sets` → **Tênis**
- `Sérvia v Argentina — Over 3.5 sets` → **Vôlei**

> **Copa Davis** (Tênis por equipes) usa times, mas é contexto raro. Sem menção explícita a "Copa Davis" ou "Davis Cup", times nacionais em mercados de sets → presumir **Vôlei**.

---

### Regra de Desambiguação — Vôlei vs Futebol (Bet365)

Em mercados ML (`Partida - Vencedor`) com nomes de países/seleções, o sinal visual do jersey icon da Bet365 é o discriminante principal:

| Sinal na Bet365 | Esporte |
|---|---|
| Jersey icon colorido ao lado do país | **Futebol** |
| Sem jersey icon ao lado do país | **Vôlei** (ou outro esporte coletivo) |

Confirme pelo placar quando disponível: `2–3` ou `0–3` indica **sets de Vôlei**, não gols.

Exemplos reais:
- `Bélgica v Egito` com jersey icon → **Futebol**
- `Canadá v Turquia` sem jersey icon, placar 2–3 → **Vôlei**
- `Bulgária v Sérvia` sem jersey icon, placar 0–3 → **Vôlei**

---

### Regra Crítica — Futebol vs E-Sports

E-Sports é **exclusivo de jogos eletrônicos** (League of Legends, CS2, VALORANT, Dota 2, etc.). Futebol real nunca deve ser classificado como E-Sports.

**Invariante absoluta:** se a categoria for `E-Sports Props`, o Esporte é obrigatoriamente `E-Sports`. Não existe `E-Sports Props` com Esporte diferente de `E-Sports`.

**Indicadores positivos de E-Sports — prioridade máxima sobre nomes de times** (ao menos um presente → E-Sports, independentemente do nome dos participantes):
- Termos de mercado exclusivos: `Mapa N`, `inibidores`, `dragões`, `kills`, `deaths`, `assists`, `torres` (E-Sports), `bombas plantadas`
- Nome de jogo: `LOL`, `CS2`, `CSGO`, `VALORANT`, `Dota`, `Rocket League`, `R6`, `Overwatch`
- Times de organização: Cloud9, Fnatic, NAVI, HEROIC, Team Liquid, Astralis, LYON (E-Sports), etc.

> **Armadilha — LYON:** "LYON" pode ser confundido com o clube de futebol francês Olympique Lyonnais. Quando "LYON" aparecer ao lado de `Mapa N`, `Inibidores`, `Dragões` ou qualquer termo de E-Sports → é o time de E-Sports LYON, não o clube de futebol. O Esporte é `E-Sports`.

**Indicadores que NUNCA são E-Sports** (qualquer um presente → Futebol ou outro esporte real):
- Termos de mercado: `Chutes`, `Gols`, `Escanteios`, `Cartões`, `1º Tempo`, `2º Tempo`, `Handicap Asiático`
- Times nacionais: Alemanha, Brasil, Curaçao, França, Argentina, etc.
- Jersey icon visível ao lado dos participantes

**Armadilha: "Time 1" / "Time da Casa" em subcaptions da Bet365**

A Bet365 usa os rótulos `Time 1`, `Time 2` e `Time da Casa` nas subcaptions do **Criar Aposta** para identificar qual equipe o mercado se refere. Esses rótulos são nomenclatura de Futebol (e outros esportes coletivos) — **não são referências a equipes de E-Sports**. Quando aparecerem junto a mercados como `Chutes`, `Gols`, `Gols no 1º Tempo`, a classificação correta é **Futebol**.

```text
"Time 1 – Chutes"                     → Futebol (não E-Sports)
"Time da Casa – Gols"                 → Futebol (não E-Sports)
"LYON v Team Liquid — Mapa 2 Inibidores" → E-Sports (termos de mercado têm prioridade)
```

---

## MMA

Valor oficial:

```text
MMA
```

Sinônimos:
- MMA
- UFC
- BELLATOR
- PFL
- ONE CHAMPIONSHIP

---

## Vôlei

Valor oficial:

```text
Vôlei
```

Sinônimos:
- VOLEI
- VÔLEI
- VOLLEYBALL
- BEACH VOLLEY
- BEACH VOLLEYBALL
- VNL
- VOLLEYBALL NATIONS LEAGUE
- NATIONS LEAGUE VOLEI
- SUPERLIGA (contexto de vôlei brasileiro)
- CEV
- FIVB

---

### Regra Crítica — Vôlei vs Futebol

Times nacionais (Brasil, Argentina, Sérvia, Itália, etc.) aparecem em ambos os esportes.

Regras de desambiguação (em ordem de prioridade):

1. Liga/torneio contém termo de Vôlei (VNL, Superliga, Volleyball, CEV, FIVB…) → **Vôlei**
2. Mercado menciona `sets` + time/seleção → **Vôlei**
3. Mercado menciona `gols`, `escanteios`, `cartões`, `ambas marcam` → **Futebol**
4. Sem sinal específico → **Futebol** é o padrão para times nacionais genéricos

Nunca classificar como Futebol quando houver sinal de Vôlei.

---

## Baseball

Valor oficial:

```text
Baseball
```

Sinônimos:
- BASEBALL
- BEISEBOL
- BASEBOL
- MLB

---

## Rugby

Valor oficial:

```text
Rugby
```

Sinônimos:
- RUGBY
- RUGBY UNION
- RUGBY LEAGUE

---

## Handebol

Valor oficial:

```text
Handebol
```

Sinônimos:
- HANDBALL
- HANDEBOL

---

## E-Sports

Valor oficial:

```text
E-Sports
```

Sinônimos:
- ESPORTS
- E-SPORTS
- CS
- CS2
- CSGO
- VALORANT
- LOL
- DOTA
- DOTA 2
- R6
- OVERWATCH
- ROCKET LEAGUE

---

## Golf

Valor oficial:

```text
Golf
```

Sinônimos:
- GOLF
- GOLFE
- PGA
- LIV GOLF

---

## Ciclismo

Valor oficial:

```text
Ciclismo
```

Sinônimos:
- CYCLING
- CICLISMO
- TOUR DE FRANCE
- GIRO
- VUELTA

---

## Atletismo

Valor oficial:

```text
Atletismo
```

Sinônimos:
- ATHLETICS
- ATLETISMO
- TRACK AND FIELD

---

# 8. Validação Final

Antes de retornar a saída, o extrator deve validar:

1. o valor da coluna `Esporte` existe neste documento
2. a capitalização está correta
3. nenhum esporte inventado foi criado
4. nenhuma liga foi usada como valor de `Esporte` (NBA → Basquete, NFL → Futebol Americano, NHL → Hóquei)
5. `legs` / `Best of X Legs` / `First to X Legs` nunca foi classificado como `Tênis`
6. `games` nunca foi classificado como `Dardos`
7. conflitos genuínos utilizam `Outro`
8. mercados ML/H2H foram analisados utilizando desambiguação contextual
9. `sets` com nome de **jogador individual** = Tênis (nunca Vôlei, exceto Copa Davis explícita)
10. `sets` com nome de **time/seleção** = Vôlei (nunca Tênis, exceto Copa Davis explícita)
11. times nacionais genéricos sem sinal de Vôlei → Futebol; com sinal de Vôlei (liga/sets) → Vôlei
12. nenhum bilhete classificado como `Padel` (esporte inexistente); duplas em notação `X/Y v W/Z` = **Tênis**

Se qualquer regra falhar, a linha deve ser considerada inválida.

---

VERSÃO: 2026  
STATUS: ATIVO  
USO: Extratores de apostas esportivas
