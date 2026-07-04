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

**REGRA DEFINITIVA DE ORDEM DO OUTPUT:**
O grid e o texto colado exibem bilhetes em ordem de leitura: esquerda→direita, cima→baixo (coluna 1 linha 1, coluna 2 linha 1, coluna 3 linha 1, coluna 1 linha 2…). O TSV deve sair na ordem **estritamente inversa**:

| Posição | Texto / grid | TSV output |
|---|---|---|
| 1ª | Primeiro bilhete (topo-esquerdo) | Última linha |
| … | … | … |
| Última | Último bilhete (baixo-direito) | Primeira linha |

Exemplo com o batch de 8 bilhetes desta sessão:
- Texto posição 1 → **Florian Wirtz** [Alemanha v Costa do Marfim] → **última linha** do TSV
- Texto posição 8 → **Países Baixos** [Resultado 1ºT] [Países Baixos v Suécia] → **primeira linha** do TSV

> O ID do **último bilhete** no texto colado pode estar ausente (texto cortado antes do rodapé) — completar com a imagem se disponível.

---

## 3. ID do bilhete

- Caso: **visível**
- Formato: numérico longo, 18–19 dígitos — ex.: `856196311719649280`
- Localização: última linha do bilhete, após a data de colocação — `ID: [número]`
- Nunca vai no output do usuário (11ª coluna interna para dedup).

> ⚠️ **O ID só é confiável quando vem do TEXTO COLADO.** Um número de 18–19 dígitos
> lido por **visão/OCR de imagem** erra dígitos a cada leitura — e como a dedup do
> sistema usa o ID como chave (`ID/código diferente → INSERT`, ver `CLAUDE.md`), um
> ID mal-lido faz o **mesmo bilhete entrar como novo**. Regras práticas:
> 1. **Sempre prefira o modo TEXTO** (§2.1) — o ID vem exato, a dedup funciona.
> 2. **Nunca re-suba o mesmo print** já processado — cada re-envio de imagem tende a
>    gerar um ID diferente do anterior → duplicata silenciosa.
> 3. Se só houver imagem e o ID estiver borrado/parcial, é **melhor deixar o ID vazio**
>    (a dedup cai no fallback por conteúdo) do que "chutar" dígitos — um ID inventado é
>    pior que nenhum ID.
>
> **Causa raiz (sessão 100):** a conta `KingPanda · Ellen [Eu]` acumulou 178 linhas
> para 83 bilhetes reais porque a mesma cartela foi re-enviada por imagem em várias
> levas, cada uma com o ID lido diferente. Corrigido no banco por reconciliação contra
> o texto colado (a verdade). A prevenção estrutural (dedup por conteúdo mesmo com ID
> presente) é decisão de app pendente — ver `CLAUDE.md §Regras de deduplicação`.

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

Fonte de verdade das categorias: `MASTER_APOSTAS_2026 §3`. Este mapa lista **apenas** os mercados já confirmados num bilhete real desta casa (camada fina) — a taxonomia completa vive no MASTER e **não** se reescreve aqui.

| KingPanda exibe | Aposta global | Status |
|---|---|---|
| `Ambas equipes Marcam` | Ambas Marcam | ✓ confirmado |
| `Jogador a Marcar um Gol` · `Marcar a qualquer momento` | Anytime | ✓ confirmado |
| `Cartões` · `Equipe com Mais Cartões` · `Mais Cartões` | Cartões | ✓ confirmado |
| `Chance Dupla` | Dupla Chance | ✓ confirmado |
| `Escanteios Mais/Menos (2-Vias)` · `Escanteios Mais/Menos` | Escanteios | ✓ confirmado |
| `Total de Gols Mais/Menos` · `Total de Gols` | Gols | ✓ confirmado |
| `Resultado Final` · `Resultado do 1º Tempo` · `Resultado do 2º Tempo` · `Vencedor da Partida` · `1X2` | ML | ✓ confirmado |
| `Criador de apostas` (múltiplas seleções) | Múltipla | ✓ confirmado |
| `Resultado Correto` · `Resultado Correto - 1º Tempo` · mercado não mapeado | Outros | ✓ fallback |
| `Jogador a Marcar um gol ou dar uma assistência` · ação individual de jogador | Player Props | ✓ confirmado |
| `[Time]: Equipe Marca nos Dois Tempos` · estatística coletiva de equipe | Team Props | ✓ confirmado |

**Notas de reconstrução:**
- Confronto: `Time A vs Time B` → `[Time A v Time B]` (lowercase `v`, colchetes)
- `Mais de X` / `Menos de X` → Over X / Under X; decimal ponto → vírgula (`2.5` → `2,5`)
- Player Props: seleção = nome do jogador; mercado usa prefixo "Jogador a". Na descrição: substituir "Jogador a [ação]" por "[Nome do Jogador] a [ação]" — ex.: `Viktor Gyokeres a Marcar um Gol ou dar uma Assistência`
- Criador de apostas (Múltipla): cada seleção = `[Seleção] [Mercado] [Confronto]`; concatenar com ` // `
- Odds: ponto decimal en-US → vírgula no output: `3.20` → `3,20`
- Prioridade: usar sempre a categoria mais específica; `Player Props` e `Outros` são último recurso (`MASTER_APOSTAS_2026 §2`)

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
- **Ordem de output = inversa do texto/grid:** primeiro no texto (topo-esquerdo) = última linha do TSV; último no texto (baixo-direito) = primeira linha do TSV.
- **ID ausente no final do texto:** normal quando o texto foi cortado antes do rodapé do último bilhete — usar ID da imagem.
- **ID de imagem é não-confiável (§3):** OCR erra dígitos do número de 18–19 casas → mesmo bilhete vira duplicata. Priorize o **texto colado**; nunca re-suba o mesmo print; ID borrado → deixe vazio, não chute.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

**Específicas KingPanda:**
- Cross-check de W: `Ganho Potencial ÷ Total Apostado` deve igualar `Total de Odds` — discrepância indica leitura errada.
- "Criador de apostas": número de seleções na descrição deve bater com os blocos no texto.
- ID: pode estar ausente no **último bilhete** do texto colado (texto cortado antes do rodapé) — normal; completar com a imagem. ID ausente em bilhete do meio = texto incompleto.
- Ordem de output: último bilhete do texto = primeira linha do TSV; conferir via IDs — o ID com menor timestamp (geralmente o menor numericamente) deve aparecer primeiro no TSV do batch.

---

## 15. Exemplos golden — batch completo (8 bilhetes, 20/06/2026)

Jogos: Alemanha vs Costa do Marfim (17:00) · Países Baixos vs Suécia (14:00)
Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**Numeração = ordem do TSV output (inversa do texto/grid).**
Grid: col 1 linha 1 → col 2 linha 1 → col 3 linha 1 → col 1 linha 2 → … → col 2 linha 3
TSV: linha 1 = último do grid · linha 8 = primeiro do grid

---

**G1 (TSV linha 1) — W · ML · Países Baixos vs Suécia · posição 8 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	ML	Países Baixos [Resultado 1º Tempo] [Países Baixos v Suécia]	100,00	2,76	W
```
ID: 856187092232609792 · GP BRL 276.00 · 276÷100=2,76 ✓ · boost 2.26→2.76
⚠️ ID ausente no texto colado (texto cortado) — ler da imagem.

**G2 (TSV linha 2) — L · Outros · Países Baixos vs Suécia · posição 7 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Outros	1:0 [Resultado Correto 1º Tempo] [Países Baixos v Suécia]	20,00	5,06	L
```
ID: 856170471199985664 · GP BRL 0.00 · boost 3.71→5.06

**G3 (TSV linha 3) — W · Múltipla (2 sel.) · Países Baixos vs Suécia · posição 6 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Múltipla	Over 2,5 [Total de Gols Mais/Menos] [Países Baixos v Suécia] // Suécia [Equipe com Mais Cartões] [Países Baixos v Suécia]	30,00	4,90	W
```
ID: 856170588514590720 · GP BRL 147.00 · 147÷30=4,90 ✓ · boost 3.60→4.90

**G4 (TSV linha 4) — W · Player Props · Países Baixos vs Suécia · posição 5 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Player Props	Cody Gakpo a Marcar um Gol ou dar uma Assistência [Países Baixos v Suécia]	25,00	2,40	W
```
ID: 856196804571353088 · GP BRL 60.00 · 60÷25=2,40 ✓ · boost 1.81→2.40

**G5 (TSV linha 5) — L · Player Props · Países Baixos vs Suécia · posição 4 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Player Props	Viktor Gyokeres a Marcar um Gol ou dar uma Assistência [Países Baixos v Suécia]	25,00	3,20	L
```
ID: 856196311719649280 · GP BRL 0.00 · boost 2.27→3.20

**G6 (TSV linha 6) — L · Múltipla (3 sel.) · Alemanha vs Costa do Marfim · posição 3 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Múltipla	Sim [Ambas Marcam] [Alemanha v Costa do Marfim] // Alemanha [Resultado 2º Tempo] [Alemanha v Costa do Marfim] // Sim [Alemanha: Equipe Marca nos Dois Tempos] [Alemanha v Costa do Marfim]	25,00	7,00	L
```
ID: 856170034874834944 · GP BRL 0.00 · boost 5.47→7.00

**G7 (TSV linha 7) — L · Múltipla (2 sel.) · Alemanha vs Costa do Marfim · posição 2 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Múltipla	Empate ou Costa do Marfim [Dupla Chance] [Alemanha v Costa do Marfim] // Over 9,5 [Escanteios] [Alemanha v Costa do Marfim]	50,00	6,61	L
```
ID: 856170236574720000 · GP BRL 0.00 · boost 4.74→6.61

**G8 (TSV linha 8 — última) — L · Player Props · Alemanha vs Costa do Marfim · posição 1 no texto**
```
20/06/2026	Futebol		KingPanda	[parceiro]	Player Props	Florian Wirtz a Marcar um Gol ou dar uma Assistência [Alemanha v Costa do Marfim]	25,00	2,30	L
```
ID: 856196861957820416 · GP BRL 0.00 · boost 1.81→2.30
⚠️ Evento 20/06 • 17:00 (usar) ≠ colocação 20/06 • 12:40 (ignorar).

---

## Feedback para a camada global

1. **`Resultado Correto` ausente do `MASTER_APOSTAS_2026`** — mercado de placar exato (`Resultado Correto`, `Resultado Correto - 1º Tempo`) aparece no KingPanda e provavelmente em outras casas. Não existe categoria global. Mapeado temporariamente como `Outros ⚠️`. **Proposta: criar categoria `Resultado Correto` no master global.**

---

VERSÃO: 2026
STATUS: ATIVO
CASA: KingPanda
PENDÊNCIAS: §5 rótulos V/HW/HL; §7 cashout; §8 bônus.
