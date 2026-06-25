# CASA_KTO
## Camada de tradução — KTO → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da KTO.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `KTO`
- Domínio: `kto.bet.br`
- Locale: pt-BR na interface, **mas valores monetários e odds em formato en-US** — ponto decimal (ex.: `R$94.29`, `2.43`, `R$607.50`). Converter sempre para vírgula no output.
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** screenshot / visão — lista de cupons em "Minhas Apostas" / histórico.
- **FALLBACK:** texto colado da mesma lista (mesma anatomia).

### 2.2 Tipo do bilhete declarado

O cabeçalho de cada cupom declara o tipo:

| KTO exibe no cabeçalho | Significado | Categoria `Aposta` |
|---|---|---|
| `Simples @ X.XX` ou `Simples` | 1 seleção | categoria do mercado da seleção |
| `Dupla` | 2 seleções combinadas | `Múltipla` |
| `Tripla` / `Quadrupla` / N seleções | N combinadas | `Múltipla` |
| `Simples (N)` | **N apostas simples independentes no mesmo cupom** | `Múltipla` (ver §13 — decisão FDC) |
| `Duplas (X), Triplas (Y)` etc. | aposta de **sistema** (ex.: `Duplas (3), Triplas (1)` = Trixie) | `Múltipla` |

> **Regra de odd da KTO (decisão do dono):** a KTO **trata qualquer cupom como uma única aposta e exibe apenas a odd total** (odd de visualização). Use sempre essa odd exibida (`@ X.XX` no cabeçalho ou `Cotações (Odds): X.XX`). Quando o bilhete for **Ganha**, calcule `Odd = Pagamento ÷ Stake` (regra global W). Cada cupom = **uma linha** no TSV, independentemente do nº de seleções.

### 2.3 Anatomia do cupom

```
[Tipo] [@ X.XX]? • [Status]            ← Simples/Dupla/Quadrupla/Simples (N)/sistema + status
DD de mmm. de AAAA • HH:MM:SS          ← data e hora de colocação
ID do Cupom: NNNNNNNNNNN               ← ID visível (11 dígitos) → Código
[Mercado: Seleção]                      ← uma ou mais seleções (cada uma com seu confronto)
[Confronto: Time A - Time B]
[Ao vivo] [placar] [tempo]              ← se ao vivo (IGNORAR)
Cotações (Odds): X.XX                   ← odd total (ou no cabeçalho via @ )
Aposta: R$XX.XX                         ← stake
Ganho potencial: R$XX.XX                ← retorno potencial (aberta/perdida) — NÃO é pagamento
Pagamento: R$XX.XX                      ← retorno real (somente em Ganha) → usar para W
[ODDÃO+]                                 ← selo de boost (se houver)
```

### 2.4 Ordem do output

A lista exibe do **mais recente (topo)** para o **mais antigo (baixo)**. O TSV sai na ordem **inversa**: último cupom no texto/imagem (mais antigo) = **1ª linha**; primeiro cupom (mais recente) = última linha.

---

## 3. ID do bilhete

- Caso: **ID visível e impresso** — campo `ID do Cupom: NNNNNNNNNNN` (numérico, 11 dígitos), ex.: `12807210793`.
- O ID vai para a 11ª coluna interna `Código` exatamente como exibido.
- Dedup: por `Código` (= ID do Cupom) via `repository.py`.
- **IDs diferentes = bilhetes distintos** — sempre INSERT, mesmo com conteúdo idêntico. Ex.: um `Simples (2)` (ID `12518213015`) e uma `Dupla` (ID `12518208383`) sobre as **mesmas** seleções são cupons distintos com IDs distintos → ambos salvos.

---

## 4. Data

- Fonte: campo `DD de mmm. de AAAA • HH:MM:SS` = **data/hora de colocação** do cupom.
- A lista não exibe data do evento separada; usar a data de colocação como **proxy do evento** (padrão de casas sem data de evento explícita — ver `CASA_BETANO`).
- **Coluna `Data`:** descartar horário → output `DD/MM/AAAA`.
- Meses pt-BR abreviados: `jan. fev. mar. abr. mai. jun. jul. ago. set. out. nov. dez.` → `01…12`.
- Múltipla / sistema: data = perna mais recente (regra global, `MASTER_OUTPUT_2026`). Na KTO o cupom já exibe uma data única → usá-la.

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar sinal visual diretamente. Traduzir sempre para `W · L · V · HW · HL`.

| KTO exibe | Nosso código |
|---|---|
| `Ganha` (+ `Pagamento` > Aposta) | W |
| `Perdida` | L |
| *(void / anulada — rótulo não confirmado)* | V |
| *(meia vitória — rótulo não confirmado)* | HW |
| *(meia derrota — rótulo não confirmado)* | HL |
| `Aberta` | — (não liquidada → `extraction_state = aberta`, coluna Resultado vazia) |
| `Recusado` | **IGNORAR o cupom por completo** (ver §13) |

Conferência financeira (segunda linha de defesa): `Pagamento > Aposta` → W · `Perdida` sem pagamento → L.

**Gatilho de meia-liquidação (HW/HL):** rótulo explícito aguarda amostra. Confirmação por assinatura financeira (`HL → Pagamento = Aposta/2`; `HW → Pagamento = (Aposta/2)×(odd+1)`), só em linhas asiáticas de quarto (`.25`/`.75`).

---

## 6. Boost / promoção

- Tem boost: **sim** — selo `ODDÃO+`.
- Formato: a casa mostra a odd original **riscada** seguida da odd final boosted. Ex.: `Cotações (Odds): 3.60 4.50` (`3.60` riscada → `4.50` final).
- Regra: usar sempre a **odd final** (boosted). A original riscada é ruído.
- Em W, `Pagamento ÷ Stake` já embute o boost automaticamente.

---

## 7. Cashout

- Tem cashout: **não confirmado** — aguarda amostra.
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → `V`.

<!-- TODO: confirmar localizador e rótulo visual do cashout encerrado na KTO. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — aguarda amostra.
- **Política:** pendente até ter amostra real.

<!-- TODO: confirmar se há apostas de bônus/freebet e como identificá-las. -->

---

## 9. Mapa de mercados (KTO → `Aposta` global)

> Mercados da KTO estão em português do Brasil.
> A classificação segue `MASTER_APOSTAS_2026 §3` (27 categorias).

| KTO exibe | Aposta global | Status |
|---|---|---|
| (aguarda amostra) | Ambas Marcam | aguarda amostra |
| `Para marcar: [Jogador] - Sim` (em cupom Simples) | Anytime | ✓ confirmado |
| (aguarda amostra) | Assistência | aguarda amostra |
| `Para receber um cartão: [Jogador] - Sim` · mercados de cartão | Cartões | ✓ confirmado |
| (aguarda amostra) | Chutes | aguarda amostra |
| (aguarda amostra) | Chutes no Gol | aguarda amostra |
| (aguarda amostra — Baseball) | Corridas | aguarda amostra |
| (aguarda amostra) | Desarmes | aguarda amostra |
| (aguarda amostra) | DNB | aguarda amostra |
| (aguarda amostra — Basquete) | Double-Double | aguarda amostra |
| (aguarda amostra) | Dupla Chance | aguarda amostra |
| (aguarda amostra — E-Sports) | E-Sports Props | aguarda amostra |
| (aguarda amostra) | Escanteios | aguarda amostra |
| (aguarda amostra — Tênis) | Games | aguarda amostra |
| (aguarda amostra) | Gols | aguarda amostra |
| (aguarda amostra — comparativo) | H2H | aguarda amostra |
| (aguarda amostra) | Handicap | aguarda amostra |
| (aguarda amostra) | Impedimentos | aguarda amostra |
| (aguarda amostra — NFL) | Jardas | aguarda amostra |
| (aguarda amostra — Dardos) | Legs | aguarda amostra |
| `Vencedor da partida: [Time/Jogador]` | ML | ✓ confirmado |
| `Dupla` · `Quadrupla` · `Simples (N)` · `Duplas (X), Triplas (Y)` (sistema) | Múltipla | ✓ confirmado |
| `[Time] vence e ambos os times marcam` (resultado + BTTS combinados) · mercado sem categoria | Outras ⚠️ | fallback (ver §Feedback) |
| `Faltas concedidas/cometidas pelo jogador` · estatística individual de jogador sem categoria própria | Player Props | ✓ confirmado |
| (aguarda amostra — Tênis) | Sets | aguarda amostra |
| (aguarda amostra) | Team Props | aguarda amostra |
| (aguarda amostra — Basquete) | Triplo-Duplo | aguarda amostra |

**Notas de reconstrução:**
- Confronto: separador `-` (ex.: `Strasbourg - Mainz`, `Chéquia - México`) → normalizar para `v` com colchetes: `[Strasbourg v Mainz]`.
- `Para marcar: [Jogador] - Sim` em cupom **Simples** = `Anytime`; dentro de cupom Dupla/Quadrupla/Sistema, o cupom inteiro = `Múltipla` (a seleção entra só na Descrição).
- `Para receber um cartão: [Jogador] - Sim` = `Cartões` mesmo sendo jogador individual (princípio §1 `MASTER_APOSTAS`; object = cartão, nunca Player Props).
- `Faltas concedidas pelo jogador` = `Player Props` (estatística individual; não há categoria `Faltas`). `(Fechado usando dados Opta)` é ruído.
- `Mais X` / `Menos X` → `Over X` / `Under X` (padrão global `MASTER_DESCRICAO_2026 §11`).
- Mercado sem categoria → `Outras ⚠️` + registrar no §Feedback.

---

## 10. Stake

- Localização: campo `Aposta: R$XX.XX`.
- Formato: **en-US — ponto decimal** (ex.: `R$331.57`, `R$20.00`).
- Normalização: remover `R$` → converter ponto decimal para **vírgula** (`331.57` → `331,57`).

---

## 11. Odds

> **Campo de odd exibida:** `Cotações (Odds): X.XX` (ou `@ X.XX` no cabeçalho de cupom Simples). **Campo financeiro de W:** `Pagamento: R$XX.XX` (retorno real do cupom ganho).
> ⚠️ `Ganho potencial` **não** é pagamento — é o retorno *potencial* de cupons abertos/perdidos. Nunca usar `Ganho potencial` para calcular odd de W.

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Pagamento ÷ Stake` (deve coincidir com a odd exibida) |
| L | odd exibida (`Cotações (Odds)` / `@`) — nunca `0,00` |
| V | odd exibida — nunca `1,00` (aguarda amostra de rótulo void) |
| HW | odd exibida (aguarda amostra) |
| HL | odd exibida (aguarda amostra) |
| Aberta | odd exibida; coluna Resultado vazia + `extraction_state = aberta` |
| Cashout | `Odd = Cashout ÷ Stake` (aguarda amostra) |

- Formato de odd: en-US (ponto) → vírgula (`40.80` → `40,80`; `2.43` → `2,43`).
- Boost (`ODDÃO+`): usar a odd **final** boosted; a riscada é ruído (ver §6).
- Precisão: preservar — não truncar nem arredondar (`MASTER_RESULTADO_2026`).

---

## 12. Ruído a ignorar

`Ao vivo` · placar (`0-0`) · cronômetro / tempo (`1º Tempo 26:19`) · `ODDÃO+` (selo de boost — sinaliza boost mas não vai ao output) · odd **riscada** (original pré-boost) · `Ganho potencial` (potencial, não real) · `X de X resolvidas` (contador) · `(Fechado usando dados Opta)` · `Compartilhar` · rótulos de campo `Cotações (Odds):` / `Aposta:` / `Pagamento:` (os valores vêm na sequência) · cupons `Recusado` (ignorar por completo, §13)

---

## 13. Pegadinhas (resumo rápido)

- **Cupons `Recusado` são IGNORADOS por completo:** aposta recusada pela casa nunca foi aceita/liquidada — não extrair, não gerar linha. (Ex.: ID `12807217380` `Recusado` não vira linha; a versão `Aberta` ID `12807210793` da mesma seleção, sim.)
- **Formato en-US em dinheiro E odds:** ponto é decimal (`R$94.29` = 94 reais e 29 centavos; `2.43` = odd 2,43). Converter sempre para vírgula. Nunca interpretar `R$331.57` como 331 mil.
- **`Ganho potencial` ≠ `Pagamento`:** `Ganho potencial` aparece em cupons abertos e perdidos (retorno *se* ganhar). Só `Pagamento` (exclusivo de `Ganha`) é o retorno real → usar para W. Nunca calcular odd de W a partir de `Ganho potencial`.
- **`Simples (N)` = N simples independentes num cupom:** a lista mostra só o stake total e o ID do cupom, **sem odd/resultado por perna** (ex.: `Simples (3)` ID `12485412764`, 3 seleções, `Aposta R$150.00`, `Ganho potencial R$50.00` = R$50 por perna). **Decisão FDC (24/06/2026):** tratar o cupom como **uma linha `Múltipla`**, todas as seleções na Descrição (separador ` // `), usando a odd de visualização (Pagamento÷Stake se Ganha). Quando a lista não exibir odd nem resultado da perna (cupom só com `X de X resolvidas`, sem `Ganha`/`Perdida` e sem `Cotações`), os dados estão incompletos neste view → registrar no §Feedback / usar a tela de detalhe do cupom.
- **Boost `ODDÃO+`:** a odd final boosted é a válida; a odd riscada (original) é ruído.
- **`Vencedor da partida` entre dois indivíduos:** pode ser Dardos ou Tênis — desambiguar pelo conhecimento dos atletas. Ex.: `Steve West`, `William Borland`, `Simon Stevenson` = Dardos (PDC).
- **Apostas ao vivo:** mostram placar e cronômetro — ignorar; não afetam categoria nem resultado.
- **Confronto com separador `-`:** `Lanús - Always Ready` → `[Lanús v Always Ready]`.

---

## 14. Validações específicas

**Transversais (todas as casas):**
- Código de resultado é um dos oficiais (`W / L / V / HW / HL`) — nunca sinal visual cru.
- Odd preservada em L/HL/V: nunca `0,00`, nunca metade, nunca `1,00`.
- Coluna `Esporte` contém o esporte, nunca a liga.
- Jogador normalizado: sem `Sobrenome, Nome`; sem `[colchetes]` residuais na descrição.
- Nº de linhas = nº de cupons detectados (**exceto cupons `Recusado`, que não contam**).

**Específicas da KTO:**
- Cupons `Recusado` não geram linha.
- Dinheiro e odds convertidos de ponto para vírgula (`607.50` → `607,50`; `4.20` → `4,20`).
- W cross-check: `Pagamento ÷ Stake ≈ Odd exibida` (devem bater — discrepância indica leitura errada).
- ID do Cupom presente na 11ª coluna `Código`.
- Odd de W vem de `Pagamento`, nunca de `Ganho potencial`.

---

## 15. Exemplos golden (cupons reais — visão "Minhas Apostas")

Lotes de 31/03 a 24/06/2026. Cupons `Recusado` excluídos.

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

**Ordem de output:** lista = mais recente primeiro. TSV: inverso (mais antigo primeiro).

---

### G1 (TSV linha 1) — L · Múltipla (Quadrupla) · cartões Chéquia/Kosovo

**Input (cupom):**
```
Quadrupla • Perdida
31 de mar. de 2026 • 15:24:42
ID do Cupom: 12443717594
Para receber um cartão: Ladislav Krejcí - Sim   (Chéquia - Dinamarca)
Para receber um cartão: Morten Hjulmand - Sim   (Chéquia - Dinamarca)
Para receber um cartão: Lumbardh Dellova - Sim  (Kosovo - Turquia)
Para receber um cartão: Ismail Yüksek - Sim      (Kosovo - Turquia)
Cotações (Odds): 95.00
Aposta: R$75.00
```

**Verificação:** `Perdida` → L. 4 seleções combinadas → Múltipla. Odd exibida 95,00 (preservar, não calcular em L). Cartões individuais ficam na Descrição.

**TSV esperado:**
```
31/03/2026	Futebol		KTO		Múltipla	Ladislav Krejcí - Cartão [Chéquia v Dinamarca] // Morten Hjulmand - Cartão [Chéquia v Dinamarca] // Lumbardh Dellova - Cartão [Kosovo v Turquia] // Ismail Yüksek - Cartão [Kosovo v Turquia]	75,00	95,00	L	12443717594
```

---

### G2 (TSV linha 2) — L · Múltipla (Quadrupla) · cartões Chéquia/Kosovo

**Input (cupom):**
```
Quadrupla • Perdida
31 de mar. de 2026 • 15:25:35
ID do Cupom: 12443732091
Para receber um cartão: Ladislav Krejcí - Sim   (Chéquia - Dinamarca)
Para receber um cartão: Morten Hjulmand - Sim   (Chéquia - Dinamarca)
Para receber um cartão: Ismail Yüksek - Sim      (Kosovo - Turquia)
Para receber um cartão: Albian Hajdari - Sim     (Kosovo - Turquia)
Cotações (Odds): 76.00
Aposta: R$75.00
```

**Verificação:** `Perdida` → L. Odd exibida 76,00.

**TSV esperado:**
```
31/03/2026	Futebol		KTO		Múltipla	Ladislav Krejcí - Cartão [Chéquia v Dinamarca] // Morten Hjulmand - Cartão [Chéquia v Dinamarca] // Ismail Yüksek - Cartão [Kosovo v Turquia] // Albian Hajdari - Cartão [Kosovo v Turquia]	75,00	76,00	L	12443732091
```

---

### G3 (TSV linha 3) — L · ML · Dardos (Steve West)

**Input (cupom):**
```
Simples @ 1.80 • Perdida
4 de abr. de 2026 • 12:03:34
ID do Cupom: 12460499172
Vencedor da partida: Steve West   (Steve West - William Borland)
Aposta: R$300.00
```

**Verificação:** `Perdida` → L. Odd exibida 1,80 (preservar). `Vencedor da partida` entre dois atletas de Dardos (PDC) → Esporte = Dardos, categoria ML.

**TSV esperado:**
```
04/04/2026	Dardos		KTO		ML	Steve West [Steve West v William Borland]	300,00	1,80	L	12460499172
```

---

### G4 (TSV linha 4) — W · ML · Dardos (Steve West)

**Input (cupom):**
```
Simples @ 2.43 • Ganha
4 de abr. de 2026 • 12:05:23
ID do Cupom: 12460511765
Vencedor da partida: Steve West   (Simon Stevenson - Steve West)
Aposta: R$250.00
Pagamento: R$607.50
```

**Verificação:** `Ganha` → W. Odd = Pagamento ÷ Stake = 607,50 ÷ 250 = 2,43 ✓ (coincide com a exibida). Dardos, ML.

**TSV esperado:**
```
04/04/2026	Dardos		KTO		ML	Steve West [Simon Stevenson v Steve West]	250,00	2,43	W	12460511765
```

---

### G5 (TSV linha 5) — L · Múltipla (Dupla) · anytime scorer

**Input (cupom):**
```
Dupla • Perdida
9 de abr. de 2026 • 12:59:13
ID do Cupom: 12485395277
Para marcar: Guido Mainero - Sim   (Platense - Corinthians)
Para marcar: Yeiber Murillo - Sim  (UCV FC - Libertad Asuncion)
Cotações (Odds): 85.50
Aposta: R$12.40
```

**Verificação:** `Perdida` → L. 2 seleções combinadas → Múltipla. Odd exibida 85,50.

**TSV esperado:**
```
09/04/2026	Futebol		KTO		Múltipla	Guido Mainero [Platense v Corinthians] // Yeiber Murillo [UCV FC v Libertad Asuncion]	12,40	85,50	L	12485395277
```

---

### G6 (TSV linha 6) — L · Múltipla (Dupla) · anytime scorer

**Input (cupom):**
```
Dupla • Perdida
16 de abr. de 2026 • 08:50:48
ID do Cupom: 12518208383
Para marcar: Ramiro Angel Carrera - Sim  (Lanús - Always Ready)
Para marcar: Samir El Mourabet - Sim     (Strasbourg - Mainz)
Cotações (Odds): 40.80
Aposta: R$44.19
```

**Verificação:** `Perdida` → L. Odd exibida 40,80. Ordem das seleções preservada do bilhete.

**TSV esperado:**
```
16/04/2026	Futebol		KTO		Múltipla	Ramiro Angel Carrera [Lanús v Always Ready] // Samir El Mourabet [Strasbourg v Mainz]	44,19	40,80	L	12518208383
```

---

### G7 (TSV linha 7) — Aberta · Outras · resultado + BTTS (boost ODDÃO+)

**Input (cupom):**
```
Simples • Aberta
24 de jun. de 2026 • 21:20:28
ID do Cupom: 12806921824
México vence e ambos os times marcam: Sim   (Chéquia - México)
Ao vivo  0-0  1º Tempo 25:38
Cotações (Odds): 3.60  4.50   (ODDÃO+)
Aposta: R$20.00
Ganho potencial: R$90.00
```

**Verificação:** `Aberta` → não liquidada (`extraction_state = aberta`, Resultado vazio). Boost ODDÃO+: usar odd final 4,50 (3,60 riscada é ruído). Mercado "vence E ambos marcam" = combo sem categoria própria → `Outras ⚠️`. `Ganho potencial` ignorado para odd.

**TSV esperado:**
```
24/06/2026	Futebol		KTO		Outras	México vence e ambos marcam [Chéquia v México]	20,00	4,50		12806921824
```

---

### G8 (TSV linha 8) — Aberta · Player Props · faltas (Makgopa)

**Input (cupom):**
```
Simples @ 4.20 • Aberta
24 de jun. de 2026 • 21:59:55
ID do Cupom: 12807210793
Faltas concedidas pelo jogador (Fechado usando dados Opta): Evidence Makgopa - Mais 1.5
Ao vivo  África do Sul - Coreia do Sul  0-0  1º Tempo 26:19
Aposta: R$225.71
Ganho potencial: R$947.98
```

**Verificação:** `Aberta` → não liquidada (`extraction_state = aberta`, Resultado vazio). Odd exibida 4,20. `Faltas concedidas pelo jogador` = estatística individual → Player Props. `(Fechado usando dados Opta)` = ruído. `Mais 1.5` → `Over 1,5`.

> ⚠️ O cupom `Recusado` ID `12807217380` (mesma seleção Makgopa, mesmo jogo, Aposta R$94.29) **não** gera linha — apostas recusadas são ignoradas (§13).

**TSV esperado:**
```
24/06/2026	Futebol		KTO		Player Props	Evidence Makgopa - Over 1,5 Faltas [África do Sul v Coreia do Sul]	225,71	4,20		12807210793
```

---

## Feedback para a camada global / MODELO

1. **Mercado combinado "Resultado + Ambas Marcam" (`[Time] vence e ambos marcam`):** não há categoria dedicada no `MASTER_APOSTAS_2026 §3`. Classificado provisoriamente como `Outras ⚠️`. Avaliar se merece categoria própria ou regra de prioridade (é um mercado comum em várias casas).
2. **`Simples (N)` (apostas simples agrupadas):** decisão FDC = tratar como uma linha `Múltipla` com a odd de visualização. Limitação: o view de lista não expõe odd/stake/resultado por perna; quando o cupom não traz odd nem `Ganha`/`Perdida`, os dados ficam incompletos. Avaliar ingestão pela tela de detalhe do cupom se o rastreio por perna for necessário.
3. **`Faltas` (fouls) de jogador:** mapeado para `Player Props` por falta de categoria dedicada. Se recorrente em várias casas, avaliar categoria `Faltas`.
4. **Formato en-US em casa pt-BR:** a KTO usa interface em português mas valores monetários/odds com ponto decimal. Reforça a regra global de normalização de locale por casa (`CASA_MODELO §10`).

---

VERSÃO: 2026
STATUS: ATIVO (v1 — 8 goldens reais, 24/06/2026)
CASA: `KTO`
