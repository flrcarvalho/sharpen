# MASTER_RESULTADO_2026
## Padrão Oficial da Coluna `Resultado` e Registro de Odds (2026)

Este documento define as regras oficiais para:

- classificação do resultado da aposta
- normalização da coluna Resultado
- cálculo e registro correto da odd
- tratamento de cashout
- tratamento de half settlement
- tratamento de múltiplas e sistemas

Este arquivo é a autoridade máxima para as colunas:

```text
Resultado
Odd
```

---

# 1. Códigos Oficiais de Resultado

A coluna Resultado deve utilizar exclusivamente os seguintes códigos:

```text
W   → Aposta vencedora
L   → Aposta perdida
V   → Void / aposta anulada
HW  → Half Win (meia ganha)
HL  → Half Loss (meia perdida)
```

Nenhum outro valor é permitido.

---

# 2. Tabela Oficial de Decisão da Odd

Esta tabela possui prioridade sobre qualquer interpretação contextual.

| Resultado | Situação | Regra da Odd |
|---|---|---|
| W | Retorno visível | Odd = Retorno ÷ Stake |
| W | Sem retorno visível | Odd exibida no bilhete |
| W | Cashout ≠ stake | Odd = Cashout ÷ Stake |
| L | Sem cashout | Odd exibida no bilhete |
| V | Cashout = stake | Odd exibida no bilhete |
| V | Void / anulada | Odd exibida no bilhete |
| HW | Qualquer situação | Odd exibida no bilhete |
| HL | Qualquer situação | Odd exibida no bilhete |

---

# 3. Prioridade de Aplicação das Regras

Quando houver conflito entre múltiplas regras possíveis, aplicar na seguinte ordem:

1. Cashout
2. Half Settlement (HW / HL)
3. Void (V)
4. Retorno financeiro visível
5. Odd exibida no bilhete

---

# 4. Mapeamento de Resultados das Casas

Todos os termos das casas devem ser convertidos para os códigos oficiais deste documento.

---

## 4.1 Vitória → W

Converter para `W` quando houver contexto claro de aposta vencedora.

Exemplos comuns:

- Ganhou
- Vencida
- Green
- Won
- Winner
- Win
- Acertou
- Pagou
- Bet Won
- Prêmio pago

---

## 4.2 Derrota → L

Converter para `L` quando houver contexto claro de aposta perdida.

Exemplos comuns:

- Perdida
- Perdido
- Loss
- Lost
- Red
- Não bateu
- Bet Lost

---

## 4.3 Void → V

Converter para `V` quando a aposta tiver sido anulada ou devolvida integralmente.

Exemplos comuns:

- Void
- Cancelada
- Cancelado
- Anulada
- Anulado
- Push
- Stake devolvida
- Stake returned
- Reembolsada
- Evento cancelado
- Mercado cancelado

---

## 4.4 Half Win → HW

Converter para `HW` quando houver meia vitória.

Exemplos comuns:

- Half Win
- Half Won
- Meia ganha
- Partial Win
- ½ Ganho

---

## 4.5 Half Loss → HL

Converter para `HL` quando houver meia derrota.

Exemplos comuns:

- Half Loss
- Meia perdida
- Partial Loss
- ½ Perdido

---

## 4.6 Uso do termo "Settled"

O termo:

```text
Settled
```

isoladamente nunca define o resultado da aposta.

O resultado deve ser inferido utilizando:
- retorno financeiro
- cashout
- valor recebido
- contexto da liquidação

---

# 5. Regras Oficiais por Resultado

---

## 5.1 Void (V)

Quando a aposta for anulada:

```text
Resultado = V
```

A odd registrada deve ser a odd exibida no bilhete.

Nunca registrar automaticamente:

```text
1,00
```

apenas porque a stake foi devolvida.

A planilha já trata `V` devolvendo a stake automaticamente.

---

### 5.1.1 Void em múltiplas e sistemas

Quando houver void em múltiplas ou sistemas:

- preservar a odd estrutural original da aposta
- não recalcular utilizando retorno financeiro
- não remover automaticamente seleções anuladas

---

### 5.1.2 Cashout igual à Stake

Quando:

```text
Cashout recebido = Stake
```

registrar:

```text
Resultado = V
```

e manter a odd exibida no bilhete.

Motivo:
- não houve lucro
- não houve perda
- operacionalmente equivale a void

---

## 5.2 Vitória (W)

Quando houver aposta vencedora:

```text
Resultado = W
```

---

### 5.2.1 Vitória com retorno visível

Se houver:
- retorno total
- retorno obtido
- ganhos
- prêmio
- valor recebido

utilizar:

```text
Odd = Retorno ÷ Stake
```

Exemplo:

```text
Stake:   100,00
Retorno: 235,00
Odd:     2,35
```

Precisão: preservar o resultado completo da divisão — até 12 casas decimais se necessário.
Nunca arredondar nem truncar para forçar 2 casas decimais.
**NUNCA** usar reticências (`...` ou `…`) ao final de uma odd. Escreva todos os dígitos significativos e pare no último dígito real (ex: `1,90917218543046`, não `1,909106...`).
**Separador decimal:** a divisão sai com **ponto** — converta para **vírgula** antes de escrever (`75,26066666666666`, nunca `75.26066666666666`). A planilha pt-BR lê o ponto como milhar e corrompe a odd. Ver `MASTER_OUTPUT_2026 §12.1`.

---

### 5.2.2 Vitória sem retorno visível

Se não houver retorno financeiro explícito:

```text
Odd = odd exibida no bilhete
```

---

### 5.2.3 Prioridade do retorno real

Quando houver conflito entre:
- odd exibida
- retorno real

o retorno real possui prioridade absoluta.

Isso é obrigatório especialmente em:
- odds boost
- promoções
- múltiplas com void
- ajustes de liquidação
- sistemas

---

## 5.3 Half Win (HW)

Quando ocorrer meia vitória:

```text
Resultado = HW
```

A odd registrada deve permanecer exatamente igual à odd exibida no bilhete.

Nunca recalcular:

```text
Retorno ÷ Stake
```

---

### Exemplo

```text
Stake:           100,00
Odd do bilhete:    2,00

Liquidação:
50 × 2,00 = 100
50 devolvidos

Retorno total = 150,00
```

Odd correta no TSV:

```text
2,00
```

Nunca registrar:

```text
1,50
```

---

## 5.4 Half Loss (HL)

Quando ocorrer meia derrota:

```text
Resultado = HL
```

A odd registrada deve permanecer exatamente igual à odd exibida no bilhete.

Nunca recalcular:

```text
Retorno ÷ Stake
```

Nunca registrar:

```text
0,50
```

---

### Exemplo

```text
Stake:           100,00
Odd do bilhete:    1,90

Liquidação:
50 perdidos
50 devolvidos
```

Odd correta:

```text
1,90
```

---

## 5.5 Derrota sem Cashout (L)

Quando houver derrota sem cashout:

```text
Resultado = L
```

A odd registrada deve permanecer igual à odd exibida no bilhete.

Nunca registrar:

```text
0,00
```

apenas porque o retorno foi zero.

---

### 5.5.1 Derrota em múltiplas e sistemas

Quando não houver odd total explícita:

- calcular a odd estrutural da aposta
- preservar a composição original do bilhete
- não remover seleções anuladas
- nunca utilizar `Retorno ÷ Stake`

O objetivo é preservar o preço estrutural da aposta para análises futuras.

---

## 5.6 Cashout ≠ Stake (W)

Quando houver cashout com valor diferente da stake:

```text
Resultado = W
Odd = Cashout ÷ Stake
```

Aplica-se tanto para cashout maior quanto menor que a stake — o que define é o valor recebido ser diferente da stake.

### Exemplo com ganho

```text
Stake:   100,00
Cashout: 160,00

Odd: 1,60  →  planilha: 100 × 1,60 = 160,00 ✓
```

### Exemplo com perda parcial

```text
Stake:   100,00
Cashout: 40,00

Odd: 0,40  →  planilha: 100 × 0,40 = 40,00 ✓
```

Precisão: mesma regra de §5.2.1 — preservar divisão completa, sem arredondar nem truncar, sem reticências.

---

## 5.7 Cashout Parcial

Quando houver cashout parcial combinado com settlement posterior:

- priorizar o resultado final exibido pela casa
- utilizar o valor financeiro final efetivamente recebido
- se o comportamento da casa for ambíguo, preservar:
  - odd exibida
  - estrutura original do bilhete

---

# 6. Promoções e Odds Boost

Regra universal:

> A casa exibe a odd **antes** do boost. O retorno (PRÊMIO/ganhos) já inclui o boost.
> Portanto, sempre que houver retorno visível, a odd registrada **deve** ser recalculada:

```text
Odd = Retorno ÷ Stake
```

mesmo que a odd exibida no bilhete seja diferente (menor, sem boost).

Exemplos de boost:
- SUPERMÚLTIPLA X% (Superbet)
- Odds Boost (Bet365, Betano, etc.)
- Bet Boost
- Promoções com retorno aumentado

Em todos esses casos: **a odd exibida é estrutural (sem boost), o retorno é real (com boost)**. Registrar sempre o retorno real ÷ stake.

Exemplo prático:
```
ODDS TOTAIS exibido = 10,88  (sem boost)
SUPERMÚLTIPLA 5%
PRÊMIO = 1.706,41  (com boost)
Stake = 150,00

Odd registrada = 1.706,41 ÷ 150 = 11,37606666666667
                 ↑ nunca registrar 10,88
```

---

# 7. Múltiplas e Sistemas

---

## 7.1 Regra Geral

| Situação | Regra |
|---|---|
| W com retorno visível | Retorno ÷ Stake |
| W sem retorno visível | Odd exibida |
| L sem cashout | Odd estrutural |
| V | Odd estrutural original |
| HW / HL | Odd exibida |

---

## 7.2 Múltipla Comum

A odd estrutural é calculada multiplicando as odds individuais.

> ⚠️ **Separador decimal (inquebrável):** o produto sai do cálculo com **ponto**. Converta para
> **vírgula** antes de escrever — `8,580978`, nunca `8.580978`. **Precisão total, sem arredondar
> para 2 casas.** A planilha pt-BR lê o ponto como separador de milhar e corrompe a odd
> (`8.580978` → `8.580.978`). Ver `MASTER_OUTPUT_2026 §12.1`.

### Dupla

```text
Odd = a × b
```

### Tripla

```text
Odd = a × b × c
```

### Quádrupla

```text
Odd = a × b × c × d
```

### Quíntupla

```text
Odd = a × b × c × d × e
```

---

## 7.3 Trixie

Trixie = 3 duplas + 1 tripla

Total de linhas:

```text
4
```

Fórmula:

```text
(ab + ac + bc + abc) / 4
```

---

## 7.4 Yankee

Yankee = 6 duplas + 4 triplas + 1 quádrupla

Total de linhas:

```text
11
```

Fórmula:

```text
(ab + ac + ad + bc + bd + cd + abc + abd + acd + bcd + abcd) / 11
```

---

## 7.5 Super Yankee

Super Yankee =:
- 10 duplas
- 10 triplas
- 5 quádruplas
- 1 quíntupla

Total:

```text
26 linhas
```

Fórmula:

```text
(ab + ac + ad + ae + bc + bd + be + cd + ce + de
+ abc + abd + abe + acd + ace + ade + bcd + bce + bde + cde
+ abcd + abce + abde + acde + bcde
+ abcde) / 26
```

---

# 8. Compatibilidade com Planilha

Este padrão foi projetado para funcionar com:

```excel
=IF(J="";"-";LET(stake;H;odd;I;res;J;
SWITCH(res;
"W"; stake*odd;
"L"; 0;
"V"; stake;
"HW"; (stake/2)*odd + (stake/2);
"HL"; stake/2;
"-"
)))
```

A planilha é responsável pelo cálculo financeiro final.

O TSV deve preservar:
- odd real
- odd estrutural
- odd estatística
- composição original da aposta

---

# 9. Validação Final

Antes de retornar a saída, o extrator deve validar:

1. Resultado pertence aos códigos oficiais
2. Odd segue a tabela oficial de decisão
3. Decimal utiliza vírgula
4. Stake e Odd são numéricos
5. Stake nunca é `0`
6. Odd nunca é `0,00`
7. Void nunca gera `1,00` automaticamente
8. HW e HL nunca utilizam `Retorno ÷ Stake`
9. W com retorno visível utiliza `Retorno ÷ Stake`
10. múltiplas perdedoras preservam odd estrutural
11. cashout igual à stake gera `V`; cashout diferente da stake gera `W` com Odd = Cashout ÷ Stake
12. odd calculada por divisão preserva precisão total (sem arredondamento)

---

VERSÃO: 2026  
STATUS: ATIVO  
USO: Extratores de apostas esportivas