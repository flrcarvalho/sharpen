# CASA_BOLSADEAPOSTA
## Camada de tradução — Bolsa de Aposta → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Bolsa de Aposta.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Bolsa de Aposta`
- Domínio: `bolsadeaposta.bet.br`
- Locale: pt-BR · Moeda: R$ prefixo, ponto de milhar, vírgula decimal (ex.: `R$1.000,00`)
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** texto colado — copiar o conteúdo da aba **Ordens** (histórico de apostas) da interface web, com todas as apostas expandidas (ícone `∨` clicado)
- **FALLBACK:** screenshot / visão — usar quando o texto colado não estiver disponível

### 2.2 Tipo do bilhete declarado

A Bolsa de Aposta não exibe rótulo fixo de tipo (Simples / Múltipla). O tipo é inferido:
- 1 seleção → categoria do mercado
- 2+ seleções → `Múltipla`

### 2.3 Layout do bilhete

**Estrutura de duas linhas por aposta (texto colado, com aposta expandida):**

```
[espaços]  [Data/Hora evento: DD/MM/AAAA HH:MM]  [Esporte]
[Confronto / Mercado]
[L/P]
A favor (Back)
[Data/Hora colocação: DD/MM/AAAA HH:MM]
[Seleção] @[odd] • R$[stake]
ID da Aposta: [ID]
[L/P] (repetido)
```

**Campos por posição:**
- Linha 1: data e hora do **evento** (autoridade para coluna Data) + esporte
- Linha 2: `Confronto / Mercado` — separador `/` divide confronto (antes) de mercado (depois)
- Linha 3: L/P total do bilhete — positivo = W, negativo = L
- Linha 4: `A favor (Back)` — indica bet de Back (apostar a favor)
- Linha 5: data e hora de **colocação** (secundária, usar como fallback de data)
- Linha 6: `Seleção @odd • R$stake` — fonte da odd e da stake
- Linha 7: `ID da Aposta: XXXXX` — ID do bilhete

**Modo screenshot:** mesma anatomia. Linha branca = dados principais; linha azul expandida = detalhes (A favor, seleção, ID).

**Ordem do output:** a interface exibe da mais recente (topo) para a mais antiga (baixo). TSV: **último no texto = 1ª linha** (cronológico crescente, mais antiga primeiro).

---

## 3. ID do bilhete

- Caso: **visível**
- Formato: numérico, ~8 dígitos (ex.: `98293971`, `98223547`)
- Localização: linha 7 do bloco de detalhe — `ID da Aposta: XXXXX`
- Nunca vai no output; serve para dedup e auditoria (11ª coluna interna)

---

## 4. Data

- Fonte primária: `Data/Hora evento` — linha 1 do bloco (coluna `Data/Hora` da interface), ex.: `20/06/2026 22:57`
- Fallback: `Data/Hora colocação` — linha 5 do bloco de detalhe, ex.: `19/06/2026 23:50`
- Formato fonte: `DD/MM/AAAA HH:MM` → converter para `DD/MM/AAAA` (descartar horário)
- Múltipla: data = evento da **perna mais recente** (regra global, `MASTER_OUTPUT_2026`)

> ⚠️ Duas datas por aposta: linha 1 = evento (preferir sempre); linha 5 = colocação (só usar se evento não disponível).

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar o sinal visual diretamente. Traduzir sempre para `W · L · V · HW · HL`.

| Bolsa de Aposta exibe | Nosso código |
|---|---|
| L/P positivo (verde, sem sinal) | W |
| L/P negativo (vermelho, prefixo `-`) | L |
| L/P = R$0,00 + stake devolvida | V (aguarda amostra) |
| Meia vitória | HW (aguarda amostra) |
| Meia derrota | HL (aguarda amostra) |

Conferência financeira (segunda linha de defesa): `L/P = −stake` → L · `L/P = 0` → V · `L/P > 0` → W.

**Gatilho de meia-liquidação (HW/HL):**
- Primário: aguarda amostra (rótulo explícito da plataforma não confirmado)
- Confirmação por assinatura financeira exata: `HL → L/P = −stake/2` · `HW → L/P = (stake/2) × (odd − 1)`
- Só ocorre em linhas asiáticas de quarto (`.25` / `.75`)

Apostas abertas → `extraction_state = aberta`.

---

## 6. Boost / promoção

- Tem boost: **não confirmado** — aguarda amostra
- Observado: rótulo `"BEST ODDS IN BRAZIL"` aparece no campo Descrição como parte do nome do mercado (ex.: `Germany vs. Ivory Coast "BEST ODDS IN BRAZIL"`). Indica promoção de melhores odds garantidas.
- Comportamento confirmado nas amostras: @odd da linha de detalhe coincide exatamente com `(Stake + L/P) ÷ Stake` → odd exibida é a odd real (sem discrepância de boost).
- Regra enquanto não confirmado: usar `@odd` da linha de detalhe como autoritativa.

<!-- TODO: confirmar se algum mercado exibe odd decorativa diferente do retorno real. -->

---

## 7. Cashout

- Tem cashout: **não confirmado** — aguarda amostra
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → resultado `V`.

<!-- TODO: confirmar localizador visual e rótulo de cashout encerrado. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — aguarda amostra
- **Política:** pendente até ter amostra real.

<!-- TODO: confirmar se há apostas de bônus e como identificá-las. -->

---

## 9. Mapa de mercados (Bolsa de Aposta → `Aposta` global)

> A Bolsa de Aposta exibe descrições de mercado predominantemente em inglês.
> Traduzir para a categoria global; não traduzir a Descrição final (usar seleção como mostrada no bilhete).

| Bolsa de Aposta exibe | Aposta global | Status |
|---|---|---|
| `Both Score` / `Both Teams to Score` | Ambas Marcam | ✓ confirmado |
| `Over X Goals` / `Under X Goals` | Gols | ✓ confirmado |
| Nome de time como seleção (ex.: `Alemanha`) + mercado de resultado | ML | ✓ confirmado |
| Outros mercados sem categoria específica | Outras ⚠️ | fallback |

**Notas de reconstrução:**
- Confronto: a Bolsa exibe `Time A vs Time B` (inglês, com "s" em "vs") → normalizar para `[Time A v Time B]` (sem "s").
- Seleção `Sim` = resultado booleano ("sim/não") — indica mercado de BTTS, Over/Under etc.; usar a categoria do mercado (não "Sim").
- Seleção = nome de time → ML; usar nome como mostrado no bilhete (ex.: `Alemanha`).
- `Enner Valencia: Ready to Score at Any Moment` → Anytime; jogador = `Enner Valencia`; descrição = `Enner Valencia [Confronto]`.
- `Over X Goals` / `Under X Goals` → Gols; descrição = `Over X,Y [Confronto]` (ponto → vírgula no número).
- **`Mais de X` / `Menos de X` em qualquer mercado → `Over X` / `Under X`**: padrão global — ver `MASTER_DESCRICAO_2026 §11`.
- `"BEST ODDS IN BRAZIL"` no campo mercado = rótulo promocional; ignorar para classificação.
- Mercado sem categoria global → `Outras ⚠️` + registrar no §Feedback.

---

## 10. Stake

- Localização: linha 6 do bloco de detalhe — `[Seleção] @[odd] • R$[stake]`
- Formato: pt-BR — `R$100,00` (vírgula decimal, ponto de milhar quando necessário)
- Extrair o valor após `R$` e antes do fim da linha ou próximo separador

---

## 11. Odds

> **Campo financeiro principal:** `@odd` na linha 6 do bloco de detalhe (ex.: `Sim @1.90 • R$100,00`).
> Este é o campo autoritativo para a odd. Em Back bets de exchange, a odd exibida é a odd real negociada.

- Campo financeiro principal: `@odd` (linha de detalhe)
- Localização: após `@`, antes de `•`
- Verificação por L/P: para W, confirmar que `(Stake + L/P) ÷ Stake ≈ @odd`

| Resultado | Regra da odd |
|---|---|
| W | `@odd` da linha de detalhe (verificar: `(Stake + L/P) ÷ Stake`) |
| L | `@odd` da linha de detalhe — nunca `0,00` |
| V | `@odd` da linha de detalhe — nunca `1,00` |
| HW | `@odd` da linha de detalhe (aguarda amostra) |
| HL | `@odd` da linha de detalhe (aguarda amostra) |
| Cashout | `Odd = Cashout ÷ Stake` (aguarda amostra) |

**Múltiplas:**
- Aguarda amostra para confirmar se a Bolsa exibe odd combinada ou se deve calcular produto das seleções.

> ⚠️ Regra crítica: em `L` a odd nunca vira `0,00`; em `V` nunca vira `1,00`. Usar sempre `@odd` exibida.
> Precisão: preservar — não truncar nem arredondar (`MASTER_RESULTADO_2026`).

---

## 12. Ruído a ignorar

`Ordens` (cabeçalho de coluna) · `Data/Hora` (cabeçalho) · `Esporte` (cabeçalho) · `Descrição` (cabeçalho) · `L/P` (cabeçalho) · `A favor (Back)` (tipo de aposta — informacional) · `Subtotal` (linha de total ao fim da listagem) · `∨` / `^` (ícones de expansão de linha) · links de confronto (o texto do link é o confronto — usar) · `"BEST ODDS IN BRAZIL"` ou outros slogans promocionais no nome do mercado

---

## 13. Pegadinhas (resumo rápido)

- **L/P ≠ retorno total:** L/P = lucro/prejuízo, não retorno bruto. Para W: retorno = Stake + L/P. Para calcular odd via financeiro: `(Stake + L/P) ÷ Stake`. Nunca confundir L/P com retorno total.
- **Confronto em inglês com "vs":** o separador é "vs" (com "s"). Normalizar para "v" (sem "s") no output: `[Time A v Time B]`.
- **Seleção "Sim" não vai na Descrição:** "Sim" = resposta booleana ao mercado (BTTS, Over/Under etc.). A descrição segue o padrão global (ex.: `Ambas Marcam [...]`, `Over 2,5 [...]`).
- **L/P aparece duas vezes:** a última repetição (linha 8) é idêntica à linha 3 — ignorar a repetição.
- **"BEST ODDS IN BRAZIL"** = rótulo promocional no campo Descrição; ignorar para classificação de mercado e categoria.
- **Odd com ponto decimal:** o campo `@odd` usa ponto como separador decimal (en-US), ex.: `@1.90`. Converter para vírgula no output: `1,90`.
- **Data do evento vs data de colocação:** a data do evento está na linha 1 (branca); a de colocação na linha 5 (azul). Para múltiplas apostas no mesmo evento, as datas podem diferir entre os dois campos. Sempre usar data do **evento**.
- **Exchange — Back vs Lay:** amostras contêm apenas Back (`A favor`). Se aparecer Lay (`A contra`), a lógica de L/P se inverte — documentar quando surgir.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

**Específicas da Bolsa de Aposta:**
- L/P negativo → L; L/P positivo → W. Nunca invertir.
- `@odd` convertido de ponto para vírgula decimal no output.
- Confronto normalizado: `vs` → `v`; sem "s".
- Seleção `Sim` não aparece na Descrição final (substituída pelo padrão global do mercado).
- ID extraído de `ID da Aposta: XXXXX` — apenas os dígitos.

---

## 15. Exemplos golden (bilhetes reais)

Bilhetes da aba Ordens em 20/06/2026. Texto colado com apostas expandidas.

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

**Ordem de output:** última no texto (mais antiga) = primeira linha TSV.

---

### G1 — W simples · Ambas Marcam (Netherlands vs Sweden)

**Input (texto):**
```
    20/06/2026 15:45    Futebol    
Netherlands vs Sweden / Both Score
R$77,00
A favor (Back)
19/06/2026 23:51
Sim @1.77 • R$100,00
ID da Aposta: 98223602
R$77,00
```

**Verificação:** L/P = R$77,00 (positivo) → W. Odd: @1.77 = (100 + 77) ÷ 100 = 1,77 ✓

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		Ambas Marcam	Ambas Marcam [Netherlands v Sweden]	100,00	1,77	W	98223602
```

---

### G2 — W simples · ML (Germany vs Ivory Coast) com rótulo promocional

**Input (texto):**
```
    20/06/2026 19:03    Futebol    
Germany vs Ivory Coast / Germany vs. Ivory Coast "BEST ODDS IN BRAZIL"
R$53,76
A favor (Back)
20/06/2026 11:35
Alemanha @1.56 • R$96,00
ID da Aposta: 98318394
R$53,76
```

**Verificação:** L/P = R$53,76 (positivo) → W. Odd: @1.56 = (96 + 53,76) ÷ 96 = 1,56 ✓. Seleção "Alemanha" = time → ML. "BEST ODDS IN BRAZIL" = ruído.

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		ML	Alemanha [Germany v Ivory Coast]	96,00	1,56	W	98318394
```

---

### G3 — L simples · Gols Over (Ecuador vs Curaçao)

**Input (texto):**
```
    20/06/2026 22:57    Futebol    
Ecuador vs Curaçao / Ecuador Over 2.5 Goals
-R$100,00
A favor (Back)
19/06/2026 23:50
Sim @1.90 • R$100,00
ID da Aposta: 98223547
-R$100,00
```

**Verificação:** L/P = −R$100,00 (negativo = −stake) → L. Odd: @1.90 (lida diretamente).

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		Gols	Over 2,5 [Ecuador v Curaçao]	100,00	1,90	L	98223547
```

---

### G4 — L simples · Anytime (Enner Valencia)

**Input (texto):**
```
    20/06/2026 22:57    Futebol    
Ecuador vs Curaçao / Enner Valencia: Ready to Score at Any Moment
-R$100,00
A favor (Back)
20/06/2026 08:09
Sim @1.90 • R$100,00
ID da Aposta: 98293971
-R$100,00
```

**Verificação:** L/P = −R$100,00 → L. Odd: @1.90 (lida diretamente). Seleção "Sim" → ignorar; jogador = "Enner Valencia" (do nome do mercado) → Anytime.

**TSV esperado:**
```
20/06/2026	Futebol		Bolsa de Aposta		Anytime	Enner Valencia [Ecuador v Curaçao]	100,00	1,90	L	98293971
```

---

## Feedback para a camada global / MODELO

1. **`Resultado Correto` (Correct Score)** — mercado comum em exchanges; não tem categoria no `MASTER_APOSTAS_2026`. Aguarda amostra para propor adição ao MASTER.
2. **Apostas Lay (`A contra`)** — exchanges permitem apostar contra. Não há amostra; se aparecer, o tratamento de L/P se inverte (Lay W = receber lucro quando evento NÃO ocorre). Aguarda amostra para documentar.
3. **Comissão sobre ganhos** — exchanges tipicamente cobram comissão (ex.: 2–5%) sobre L/P positivo. Nas amostras, `(Stake + L/P) ÷ Stake = @odd` exatamente (sem desconto visível). Confirmar se Bolsa de Aposta cobra comissão ou já embute no spread de odds.

---

VERSÃO: 2026
STATUS: ATIVO (v1 — 4 goldens reais, 21/06/2026)
CASA: `Bolsa de Aposta`
