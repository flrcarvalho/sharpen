# CASA_KINGPANDA
## Camada de tradução — `KingPanda` → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades de `KingPanda`.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `KingPanda`
- Aliases: `kingpanda.bet.br`
- Locale: `pt-BR` · Moeda: `BRL` prefixo, decimal en-US (ponto) → converter para vírgula no output
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa Tipster vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** texto colado — copiar/colar da aba "Minhas Apostas" em `kingpanda.bet.br`
- **FALLBACK:** visão (screenshot) — quando não for possível copiar o texto

### 2.2 Tipo do bilhete declarado

- Localização do rótulo: aparece **após** as seleções, antes das odds — ex.: `Criador de apostas`
- `Criador de apostas` = Bet Builder (usuário combina seleções no mesmo bilhete) → categoria `Múltipla`
- Bilhete simples: sem rótulo de tipo — exatamente 1 seleção

### 2.3 Layout do bilhete (texto colado)

**Bilhete simples:**
```
[Confronto]                  ← ex.: "Países Baixos vs Suécia"
[Status]                     ← "Perdido" | "Venceu" | ...
[Seleção]                    ← ex.: "Viktor Gyokeres" | "Países Baixos" | "1:0"
[odd original]               ← IGNORAR — odd antes do boost
[odd final]                  ← = Total de Odds (usar)
[Mercado]                    ← ex.: "Jogador a Marcar um gol ou dar uma assistência"
                             ← linha em branco
[DD/MM • HH:MM]             ← data e hora do EVENTO (usar para coluna Data)
[Time A] [placar]           ← placar presente quando o mercado é de placar/resultado
[Time B] [placar]
Total de Odds    [valor]
Total Apostado   BRL [valor]
Ganho Potencial  BRL [valor]
                             ← linha em branco
Compartilhar
[DD/MM • HH:MM]             ← data e hora de COLOCAÇÃO — ignorar para output
                             ← linha em branco
ID: [número]
```

**Bilhete "Criador de apostas" (Bet Builder / Múltipla):**
```
[Confronto]
[Status]
[Seleção 1]                  ← ex.: "Mais de 2.5"
[Mercado 1]                  ← ex.: "Total de Gols Mais/Menos"
[Seleção 2]                  ← ex.: "Suécia"
[Mercado 2]                  ← ex.: "Equipe com Mais Cartões"
Criador de apostas           ← rótulo do tipo — aparece APÓS todas as seleções
[odd original]
[odd final]
                             ← linha em branco
[DD/MM • HH:MM]
...
```

**⚠️ Formato de odd dupla:** o texto exibe `[odd original]` e `[odd final]` em linhas separadas, correspondentes ao padrão visual `[odd original] >> [odd final]` na interface gráfica. **Sempre usar a segunda linha (odd final) = valor em `Total de Odds`. Ignorar a primeira.**

**⚠️ Duas datas por bilhete:** a **data do evento** (`[DD/MM • HH:MM]` antes de "Total de Odds") = usar; a **data de colocação** (após "Compartilhar") = ignorar para output.

---

## 3. ID do bilhete

- Caso: **visível**
- Formato: numérico longo, 18–19 dígitos — ex.: `856196311719649280`
- Localização: última linha do bilhete, após a data de colocação — `ID: [número]`
- Nunca vai no output do usuário (11ª coluna interna para dedup).

---

## 4. Data

Cada bilhete contém **exatamente duas** ocorrências de `DD/MM • HH:MM`. São estruturalmente distintas:

| Ocorrência | Posição no texto | Posição na imagem | Usar? |
|---|---|---|---|
| **Data do evento** | Dentro do bloco de apostas, antes dos times e de "Total de Odds" | Dentro do card (fundo branco/creme) | **Sim** |
| **Data de colocação** | Imediatamente após "Compartilhar", imediatamente antes de "ID:" | Fora do card, rodapé cinza | **Não** |

**Regra para texto colado:** se `DD/MM • HH:MM` é seguido pelo nome dos times → data do evento (usar). Se é seguido por `ID:` → data de colocação (ignorar).

**Padrão inequívoco no texto:**
```
Compartilhar
20/06 • 12:40     ← PLACEMENT — ignorar
                  ← linha em branco
ID: 856196861957820416
```
```
20/06 • 17:00     ← EVENT — usar
Alemanha
Costa do Marfim
Total de Odds
```

- Formato fonte: `DD/MM` sem ano → inferir ano de `data_referencia`; output: `DD/MM/AAAA`
- Múltipla: data = evento da perna mais recente (regra global, `MASTER_OUTPUT_2026`)

> ⚠️ Se DD/MM do evento for maior que DD/MM de `data_referencia`, pode ser ano anterior — sinalizar nas Notas Críticas.

---

## 5. Status e Resultado

| KingPanda exibe | Nosso código |
|---|---|
| `Venceu` | W |
| `Perdido` | L |
| `Reembolsado` | V *(rótulo presumido — aguarda confirmação)* |
| *(meia vitória — rótulo ainda não visto)* | HW |
| *(meia derrota — rótulo ainda não visto)* | HL |

Conferência financeira (segunda linha de defesa): `Ganho Potencial = 0` → L · `Ganho Potencial = Total Apostado` → V · `Ganho Potencial > Total Apostado` → W.

**Gatilho de meia-liquidação (HW/HL):**
- Primário: rótulo ainda não confirmado — usar assinatura financeira
- `HL → Ganho Potencial = Total Apostado ÷ 2` · `HW → Ganho Potencial = (Total Apostado ÷ 2) × (odd + 1)`
- Só ocorre em linhas asiáticas de quarto (`.25` / `.75`) ou split

Apostas abertas → `extraction_state = aberta`.

<!-- TODO: confirmar rótulo de void/reembolso e de HW/HL com amostras reais -->

---

## 6. Boost / promoção

- Tem boost: **sim** — KingPanda exibe boosts regularmente
- Localizador visual: `[odd original] >> [odd final]`; no texto colado: duas linhas consecutivas de números, onde a segunda = `Total de Odds`
- `Total de Odds` sempre reflete a odd boosted (final)
- Para W: `Ganho Potencial ÷ Total Apostado` já captura o boost automaticamente
- Para L: usar `Total de Odds` diretamente (Ganho Potencial = 0)

<!-- TODO: verificar se há rótulo visual explícito de "boost" além do formato `>>` -->

---

## 7. Cashout

- Tem cashout: **não confirmado** — aguarda amostra

<!-- TODO: confirmar se KingPanda oferece cashout e qual o rótulo/campo -->

---

## 8. Bônus

- Tem bônus: **não confirmado** — aba "Meus Bônus" existe na interface
- Política: pendente — não misturar com capital próprio até decisão

<!-- TODO: confirmar rótulo de aposta de bônus e definir política de tratamento -->

---

## 9. Mapa de mercados (KingPanda → `Aposta` global)

| KingPanda exibe | Aposta global |
|---|---|
| `Jogador a Marcar um gol ou dar uma assistência` | Player Props |
| `Jogador a Marcar um Gol` / `Marcar a qualquer momento` | Anytime |
| `Ambas equipes Marcam` | Ambas Marcam |
| `Chance Dupla` | Dupla Chance |
| `Escanteios Mais/Menos (2-Vias)` / `Escanteios Mais/Menos` | Escanteios |
| `Total de Gols Mais/Menos` | Gols |
| `Equipe com Mais Cartões` | Cartões |
| `Resultado do 1º Tempo` / `Resultado do 2º Tempo` | ML |
| `Resultado Final` / `Vencedor da Partida` | ML |
| `[Time]: Equipe Marca nos Dois Tempos` | Team Props |
| `Resultado Correto` / `Resultado Correto - 1º Tempo` | Outras ⚠️ |
| `Criador de apostas` (múltiplas seleções) | Múltipla |
| mercado não mapeado | Outras ⚠️ |

**Notas de reconstrução:**
- Confronto: `Time A vs Time B` → `[Time A v Time B]` (lowercase `v`, colchetes)
- `Mais de X` / `Menos de X` → Over X / Under X. Decimal: ponto → vírgula (`2.5` → `2,5`)
- Player Props: seleção = nome do jogador; mercado = ação genérica com prefixo "Jogador a". Na descrição: substituir "Jogador a" + ação pelo nome do jogador + ação — ex.: `"Jogador a Marcar..."` com jogador `"Viktor Gyokeres"` → `"Viktor Gyokeres a Marcar..."`
- Criador de apostas: cada seleção = `[Seleção] [Mercado] [Confronto]`; concatenar com ` // `
- Odds no texto: ponto decimal (en-US) → vírgula no output: `3.20` → `3,20`

---

## 10. Stake

- Localização: `Total Apostado: BRL [valor]`
- Formato fonte: `BRL 25.00` — prefixo `BRL `, ponto decimal (en-US)
- Normalização: remover `BRL `, trocar ponto por vírgula → `25,00`
- ⚠️ Valores com milhar (ex.: `BRL 1,050.00`): remover vírgula de milhar + trocar ponto por vírgula → `1050,00`

---

## 11. Odds

- Campo financeiro principal: `Ganho Potencial` (retorno bruto = stake × odd, inclui o stake)
- Localização: `Ganho Potencial BRL [valor]` no bloco financeiro
- Odd estrutural sempre disponível: `Total de Odds` — fallback e fonte direta para L/V/HW/HL

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Ganho Potencial ÷ Total Apostado` (deve igualar `Total de Odds`) |
| L | `Total de Odds` diretamente — Ganho Potencial = 0, nunca usar como base |
| V | `Total de Odds` diretamente |
| HW | `Total de Odds` diretamente |
| HL | `Total de Odds` diretamente |
| Cashout (≠ stake) | `Odd = Ganho Potencial ÷ Total Apostado` |

**Boost:** `Total de Odds` = odd boosted (segunda no formato `>>`). Para W, `Ganho Potencial ÷ Total Apostado` já captura automaticamente.

> ⚠️ Sempre ignorar a primeira odd no formato `>>` (odd original pré-boost).
> ⚠️ Formato fonte usa ponto decimal: `3.20` → output com vírgula: `3,20`.

---

## 12. Ruído a ignorar

`Compartilhar` · ícone de compartilhamento · `Minhas Apostas` · `Meus Bônus` · `Minhas Ofertas` · abas `Abertas / Resolvidas / Ganho / Perdeu / Retirada` · `Últimos 30 Dias` · ícone `ⓘ` · data e hora de colocação (linha após "Compartilhar") · placar exibido no card (não altera o resultado — já determinado pelo rótulo `Venceu`/`Perdido`)

---

## 13. Pegadinhas (resumo rápido)

- **Duas datas por bilhete:** usar a data do evento (antes de "Total de Odds"), nunca a data de colocação (após "Compartilhar").
- **Odd dupla:** no texto colado, duas linhas consecutivas com números = odd original + odd final. Usar sempre a segunda (= `Total de Odds`).
- **`Ganho Potencial` é retorno bruto:** inclui stake. Odd = `Ganho Potencial ÷ Total Apostado`.
- **`Ganho Potencial = 0` em L:** nunca calcular odd a partir disso — usar `Total de Odds`.
- **"Criador de apostas" vem APÓS as seleções:** não confundir com o confronto; o rótulo aparece depois dos blocos de seleção.
- **Ano ausente:** DD/MM sem ano → inferir de `data_referencia`.
- **Locale numérico:** interface pt-BR mas valores e odds em en-US (ponto decimal) → converter sempre para vírgula no output.

---

## 14. Validações específicas

**Transversais (todas as casas):**
- Código de resultado é um dos oficiais (`W / L / V / HW / HL`) — nunca o código visual cru da casa.
- Odd preservada em L/HL/V: nunca `0,00`, nunca metade, nunca `1,00`.
- Coluna `Esporte` contém o esporte, nunca a liga.
- Jogador normalizado: sem `Sobrenome, Nome`; sem `[colchetes]` residuais na descrição.
- Nº de linhas = nº de IDs detectados.

**Específicas KingPanda:**
- Cross-check de W: `Ganho Potencial ÷ Total Apostado` deve igualar `Total de Odds` — discrepância indica leitura errada.
- "Criador de apostas": número de seleções na descrição deve bater com os blocos no texto.
- ID presente em todos os bilhetes: se ausente no texto colado, o texto foi copiado de forma incompleta.

---

## 15. Exemplos golden (bilhetes reais — Países Baixos vs Suécia, 20/06/2026)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**Golden 1 — L simples · Player Props · boost 2.27→3.20**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Player Props	Viktor Gyokeres a Marcar um Gol ou dar uma Assistência [Países Baixos v Suécia]	25,00	3,20	L
```
ID: 856196311719649280 · Ganho Potencial BRL 0.00

**Golden 2 — W simples · Player Props · boost 1.81→2.40**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Player Props	Cody Gakpo a Marcar um Gol ou dar uma Assistência [Países Baixos v Suécia]	25,00	2,40	W
```
ID: 856196804571353088 · Ganho Potencial BRL 60.00 · 60÷25=2,40 ✓

**Golden 3 — W Múltipla · Criador de apostas · 2 seleções · boost 3.60→4.90**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Múltipla	Mais de 2,5 [Total de Gols Mais/Menos] [Países Baixos v Suécia] // Suécia [Equipe com Mais Cartões] [Países Baixos v Suécia]	30,00	4,90	W
```
ID: 856170588514590720 · Ganho Potencial BRL 147.00 · 147÷30=4,90 ✓

**Golden 4 — L simples · Resultado Correto (→ Outras) · boost 3.71→5.06**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Outras	1:0 [Resultado Correto 1º Tempo] [Países Baixos v Suécia]	20,00	5,06	L
```
ID: 856170471199985664 · Ganho Potencial BRL 0.00

**Golden 5 — W simples · ML (Resultado 1º Tempo) · boost 2.26→2.76**
```
20/06/2026	Futebol		KingPanda	[parceiro]	ML	Países Baixos [Resultado 1º Tempo] [Países Baixos v Suécia]	100,00	2,76	W
```
ID: 856187092232609792 · Ganho Potencial BRL 276.00 · 276÷100=2,76 ✓

**Golden 6 — L simples · Player Props · boost 1.81→2.30**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Player Props	Florian Wirtz a Marcar um Gol ou dar uma Assistência [Alemanha v Costa do Marfim]	25,00	2,30	L
```
ID: 856196861957820416 · Ganho Potencial BRL 0.00 · data evento 20/06 • 17:00 (≠ colocação 20/06 • 12:40)

**Golden 7 — L Múltipla · Criador de apostas · 2 seleções (Dupla Chance + Escanteios) · boost 4.74→6.61**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Múltipla	Empate ou Costa do Marfim [Dupla Chance] [Alemanha v Costa do Marfim] // Mais de 9,5 [Escanteios] [Alemanha v Costa do Marfim]	50,00	6,61	L
```
ID: 856170236574720000 · Ganho Potencial BRL 0.00

**Golden 8 — L Múltipla · Criador de apostas · 3 seleções (Ambas Marcam + ML + Team Props) · boost 5.47→7.00**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Múltipla	Sim [Ambas Marcam] [Alemanha v Costa do Marfim] // Alemanha [Resultado 2º Tempo] [Alemanha v Costa do Marfim] // Sim [Alemanha: Equipe Marca nos Dois Tempos] [Alemanha v Costa do Marfim]	25,00	7,00	L
```
ID: 856170034874834944 · Ganho Potencial BRL 0.00

---

## Feedback para a camada global

1. **`Resultado Correto` ausente do `MASTER_APOSTAS_2026`** — mercado de placar exato (`Resultado Correto`, `Resultado Correto - 1º Tempo`) aparece no KingPanda e provavelmente em outras casas. Não existe categoria global. Mapeado temporariamente como `Outras ⚠️`. **Proposta: criar categoria `Resultado Correto` no master global.**

---

VERSÃO: 2026
STATUS: ATIVO
CASA: KingPanda
PENDÊNCIAS: §5 rótulos V/HW/HL; §7 cashout; §8 bônus; §15 Golden 5 ID confirmar no print.
