# CASA_LOTTU
## Camada de tradução — `Lottu` → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Lottu.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Lottu`
- Domínio: `lottu.bet.br`
- Locale: pt-BR · Moeda: `R$` com vírgula decimal (stake e retorno)
- Odd: **en-US** (ponto decimal, ex.: `7.60`) → converter para vírgula (`7,60`)
- `Parceiro` / `Tipster`: preenchidos pelo app

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** texto colado — aba "Apostas" do histórico no site (sem filtro de resolvidas disponível)
- **FALLBACK:** screenshot — quando texto não for possível

> ⚠️ **A Lottu não permite filtrar apenas apostas resolvidas.** As apostas em aberto ficam misturadas na lista. O badge amarelo `Aberto` identifica claramente cada aposta em aberto — **ignorar completamente** bets com esse badge. Extrair apenas `Ganhou` e `Perdeu`.

### 2.2 Tipo do bilhete declarado

- Localização do rótulo: linha `Simples de X.XX` no topo de cada bilhete
- Regra: `Simples de X.XX` sem `&` na Resposta → Simples (usar categoria do mercado); `Simples de X.XX` com `&` na Resposta → **Múltipla** (Desafio = Bet Builder de condições combinadas num único jogo)
- Nota: na Lottu, combinações de condições sobre o mesmo jogo são vendidas como "Simples de X" mas têm múltiplas condições na Resposta — tratá-las sempre como `Múltipla`.

### 2.3 Layout do bilhete

```
[ID numérico]
Simples de
[ODD em en-US]
Aposta
R$ [STAKE]
Retorno
R$ [RETORNO_POTENCIAL]
[Badge: Ganhou (verde) / Perdeu (vermelho) / Aberto (amarelo — IGNORAR)]
Resposta: [CONDIÇÃO_1] & [CONDIÇÃO_2] ([ODD])
[Time A] x [Time B]
[Tags: Desafio - Campeonato - Promoção - Torneio]
DD/MM/AAAA - HH:MM          ← início do jogo
Resolvido em: DD/MM/AAAA HH:MM     ← liquidação (usar esta)
([ODD])                     ← repetição da odd (ignorar)
```

**Ordem de output:** a lista exibe do mais recente (topo) ao mais antigo (fundo). TSV deve sair invertido: última aposta no texto = primeira linha do TSV. → `reverse=True`.

---

## 3. ID do bilhete

- Caso: **visível**
- Formato: numérico, ~7 dígitos (ex.: `4889268`, `4842688`)
- Localização: primeira linha do bilhete, antes de "Simples de"
- Nunca vai no output — serve só para dedup e validação.

---

## 4. Data

- Fonte primária: `Resolvido em: DD/MM/AAAA HH:MM` → usar `DD/MM/AAAA` (descartar horário)
- Fallback: `DD/MM/AAAA - HH:MM` (data de início do jogo, mesma linha abaixo das tags) — usar quando "Resolvido em" não estiver visível (bet ainda sem liquidação — não deve ocorrer após ignorar as abertas)
- Nota: ambas as datas geralmente são do mesmo dia; a instrução é sempre preferir `Resolvido em`.
- Múltipla: data = perna mais recente (regra global, `MASTER_OUTPUT_2026`).

---

## 5. Status e Resultado

| Lottu exibe | Nosso código |
|---|---|
| `Ganhou` | W |
| `Perdeu` | L |
| `Aberto` | **IGNORAR** (não extrair) |
| (sem amostra) | V |
| (sem amostra) | HW |
| (sem amostra) | HL |

Conferência financeira (segunda linha de defesa): `Retorno = 0` → L · `Retorno = Stake` → V · `Retorno > Stake` → W.

> ⚠️ O campo `Retorno R$ XX,XX` exibido no bilhete é o **retorno potencial** — sempre igual a `Stake × Odd`. Num bilhete `Perdeu`, o retorno real é R$0. Nunca usar o retorno potencial para inferir resultado.

**Gatilho de meia-liquidação (HW/HL):** aguarda amostra. Usar assinatura financeira: `HL → retorno = stake/2` · `HW → retorno = (stake/2) × (odd + 1)`.

Apostas abertas → `extraction_state = aberta` — não incluir no TSV.

---

## 6. Boost / promoção

- Tem boost individual: **aguarda amostra**
- Rótulos `Odds Turbinadas` e `MEGA ODDS` aparecem no campo de tags (ex.: `Desafio - Internacional - Odds Turbinadas`) — são **campanhas de marketing da casa**, não indicadores de boost individual por bilhete. Ignorar para fins de cálculo de odd.
- Nas amostras disponíveis: `Retorno = Stake × Odd exibida` exato — sem evidência de boost por bilhete.

<!-- TODO confirmar se existe boost individual (odd exibida diferente do calculado Retorno÷Stake). -->

---

## 7. Cashout

- Tem cashout: **aguarda amostra**
- Localizador: aguarda confirmação.
- Regra global: `Odd = Cashout ÷ Stake`; se `Cashout = Stake` → resultado `V`.

<!-- TODO confirmar localizador e rótulo visual de cashout encerrado. -->

---

## 8. Bônus

- Tem bônus: **aguarda amostra**
- Localizador: aguarda confirmação.

<!-- TODO confirmar se há freebets ou apostas de bônus identificáveis no histórico. -->

---

## 9. Mapa de mercados (Lottu → `Aposta` global)

> A Lottu usa o campo `Resposta:` para descrever o mercado apostado, em português maiúsculo.
> Condições com `&` → bilhete inteiro é `Múltipla` (Desafio).

| Lottu exibe (campo `Resposta`) | Aposta global | Status |
|---|---|---|
| `X PARA MARCAR A QUALQUER MOMENTO` (simples) | Anytime | ✓ confirmado |
| `MAIS DE X ESCANTEIOS` · `MAIOR NÚMERO DE ESCANTEIOS` | Escanteios | ✓ confirmado |
| `MAIS DE X GOLS` · `MAIS DE X GOLS NO Xº TEMPO` | Gols | ✓ confirmado |
| `X PARA GANHAR` | ML | ✓ confirmado |
| Desafio com `&` na Resposta (2+ condições) | Múltipla | ✓ confirmado |
| `MAIS DE X [stat] [jogador]` · `[JOGADOR] MAIS DE X [stat]` | Player Props | ✓ confirmado |
| `X PARA GANHAR AMBOS OS TEMPOS` · `X PARA MARCAR EM AMBOS OS TEMPOS` | Team Props | ✓ confirmado |

**Notas de reconstrução:**
- Separador de times: `x` (ex.: `Uruguai x Cabo Verde`) → normalizar para `[Uruguai v Cabo Verde]`.
- Odd em en-US com ponto decimal: `7.60` → converter para vírgula `7,60`.
- **`Mais de X` / `Menos de X` → `Over X` / `Under X`**: padrão global — ver `MASTER_DESCRICAO_2026 §11`. A Lottu exibe em português; a saída TSV é sempre em inglês.
- Tags de campanha (`Desafio`, `Odds Turbinadas`, `MEGA ODDS`, `Copa do Mundo 2026`, `Internacional`, `Brasil`) → ruído, ignorar para classificação de esporte e aposta.
- Nome do jogador em Player Props aparece no início da Resposta em maiúsculas (`VOZINHA MAIS DE 3.5 DEFESAS`) → normalizar para `Nome Próprio`.
- Conector `E` entre jogadores em Desafio multi-player (`VINICIUS JR. E RAPHINHA`) → tratar como separador de seleção, bilhete é `Múltipla`.
- Descrição de Múltipla (Desafio): usar ` // ` como separador de seleções normalizadas, seguido de `[Confronto]` no final. O site mostra `&`/`E` entre as condições no campo "Resposta:" → **traduzir para ` // `** (o separador oficial de seleção do sistema; `MASTER_DESCRICAO §16`).

---

## 10. Stake

- Localização: campo `Aposta R$ XX,XX` no cabeçalho do bilhete
- Formato: pt-BR — vírgula decimal, ponto de milhar (ex.: `R$ 59,36`, `R$ 1.000,00`)
- Normalizar: remover `R$ ` e ponto de milhar.

---

## 11. Odds

- Campo principal: `Simples de X.XX` (en-US, ponto decimal) — repetido no final como `(X.XX)`
- Ambos os campos são idênticos; usar `Simples de X.XX` como primário.

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Retorno ÷ Stake` (Retorno = campo `Retorno R$ XX,XX`) |
| L | odd **exibida** em `Simples de X.XX` → converter ponto para vírgula — nunca `0,00` |
| V | odd **exibida** — nunca `1,00` |
| HW | odd **exibida** — nunca metade |
| HL | odd **exibida** — nunca metade |
| Cashout (≠ stake) | `Odd = Cashout ÷ Stake` |

> ⚠️ O campo `Retorno R$ XX,XX` é **retorno potencial** (`Stake × Odd`). Para W ele é o retorno real (confirmado pelas amostras). Para L o retorno real é R$0 — nunca usar `Retorno ÷ Stake` em bet Perdeu.

---

## 12. Ruído a ignorar

`Aberto` (badge — ignorar o bilhete inteiro) · Tags de campanha (`Odds Turbinadas`, `MEGA ODDS`, `Desafio`, campeonato, liga) · `Resolvido em: HH:MM` (usar só a data) · `DD/MM/AAAA - HH:MM` (hora de início — usar só a data) · `(X.XX)` repetido no final do bilhete · Ícone de compartilhar (↗) nas bets abertas

---

## 13. Pegadinhas (resumo rápido)

- **Bets "Aberto" misturadas:** ignorar qualquer bilhete com badge `Aberto` — não extrair.
- **Retorno = potencial, não real:** `Retorno R$ XX,XX` é `Stake × Odd`. Para L não representa retorno recebido.
- **Odd en-US:** `7.60` → `7,60`. Não confundir com pt-BR onde vírgula é decimal.
- **Desafio com `&` = Múltipla:** o campo diz `Simples de X`, mas múltiplas condições via `&` → `Múltipla`.
- **Conector `E` = `&`:** `VINICIUS JR. E RAPHINHA PARA MARCAREM` → Múltipla, não uma única Player Props.
- **Separador de times `x`:** `Uruguai x Cabo Verde` → normalizar para `Uruguai v Cabo Verde`.
- **Tags no campo de categoria:** `Desafio - Internacional - Odds Turbinadas` → não inferir esporte a partir das tags; inferir do confronto.
- **Odd exibida ≠ boost:** `Odds Turbinadas` é campanha; odd individual não foi majorada individualmente (verificar cruzando `Retorno ÷ Stake = Odd exibida`).

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

**Específicas da Lottu:**
- Nenhum bilhete com badge `Aberto` deve aparecer no output.
- `Retorno ÷ Stake = Odd exibida` para bets W (validação cruzada).
- Separador de times no output: `v` — nunca `x` nem `vs`.
- Odd sempre com vírgula decimal (en-US → pt-BR).

---

## 15. Exemplos golden (bilhetes reais)

> Amostras de 19–21/06/2026. Ordem: última no texto = primeira linha do TSV (mais antiga = última linha).
> Tipster e Parceiro deixados em branco (preenchidos pelo app).

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

---

### G1 — W · Múltipla (Desafio) · ID 4842688

**Bilhete:**
```
4842688
Simples de
7.60
Aposta
R$ 29,00
Retorno
R$ 220,40
Ganhou
Resposta: JAPÃO PARA GANHAR AMBOS OS TEMPOS & JAPÃO MAIS DE 4.5 ESCANTEIOS (7.60)
Tunisia x Japão
Desafio - Internacional - Odds Turbinadas - Copa do Mundo 2026
21/06/2026 - 00:59
Resolvido em: 21/06/2026 02:58
(7.60)
```

**Odd:** `Retorno ÷ Stake = 220,40 ÷ 29,00 = 7,60` ✓

**TSV esperado:**
```
21/06/2026	Futebol		Lottu		Múltipla	Japão Ganhar Ambos os Tempos // Over 4,5 Escanteios [Tunisia v Japão]	29,00	7,60	W
```

---

### G2 — L · Player Props · ID 4841836

**Bilhete:**
```
4841836
Simples de
2.20
Aposta
R$ 100,00
Retorno
R$ 220,00
Perdeu
Resposta: VOZINHA MAIS DE 3.5 DEFESAS DO GOLEIRO (2.20)
Uruguai x Cabo Verde
Desafio - Internacional - Copa do Mundo 2026 - MEGA ODDS
21/06/2026 - 18:55
Resolvido em: 21/06/2026 21:07
(2.20)
```

**Odd:** `2,20` (lida diretamente — bet Perdeu)

**TSV esperado:**
```
21/06/2026	Futebol		Lottu		Player Props	Vozinha - Over 3,5 Defesas do Goleiro [Uruguai v Cabo Verde]	100,00	2,20	L
```

---

### G3 — W · Múltipla (Desafio ML + Anytime) · ID 4769545

**Bilhete:**
```
4769545
Simples de
4.20
Aposta
R$ 100,00
Retorno
R$ 420,00
Ganhou
Resposta: JAPÃO PARA GANHAR & AYASE UEDA PARA MARCAR A QUALQUER MOMENTO (4.20)
Tunisia x Japão
Desafio - Internacional - Odds Turbinadas - Copa do Mundo 2026
20/06/2026 - 23:59
Resolvido em: 21/06/2026 02:57
(4.20)
```

**Odd:** `Retorno ÷ Stake = 420,00 ÷ 100,00 = 4,20` ✓

**TSV esperado:**
```
21/06/2026	Futebol		Lottu		Múltipla	Japão Ganhar // Ayase Ueda Marcar a Qualquer Momento [Tunisia v Japão]	100,00	4,20	W
```

---

### G4 — L · Múltipla (Desafio ML + Anytime) · ID 4770248

**Bilhete:**
```
4770248
Simples de
3.50
Aposta
R$ 59,36
Retorno
R$ 207,76
Perdeu
Resposta: ALEMANHA PARA GANHAR & KAI HAVERTZ PARA MARCAR A QUALQUER MOMENTO (3.50)
Alemanha x Costa do Marfim
Desafio - Internacional - Odds Turbinadas - Copa do Mundo 2026
20/06/2026 - 16:59
Resolvido em: 20/06/2026 18:57
(3.50)
```

**Odd:** `3,50` (lida diretamente — bet Perdeu)

**TSV esperado:**
```
20/06/2026	Futebol		Lottu		Múltipla	Alemanha Ganhar // Kai Havertz Marcar a Qualquer Momento [Alemanha v Costa do Marfim]	59,36	3,50	L
```

---

### G5 — L · Múltipla (Desafio dois Anytime) · ID 4680704

**Bilhete:**
```
4680704
Simples de
4.50
Aposta
R$ 76,00
Retorno
R$ 342,00
Perdeu
Resposta: VINICIUS JR. E RAPHINHA PARA MARCAREM A QUALQUER MOMENTO (4.50)
Brasil x Haiti
Desafio - Brasil - Copa do Mundo 2026
19/06/2026 - 21:29
Resolvido em: 19/06/2026 22:27
(4.50)
```

**Odd:** `4,50` (lida diretamente — bet Perdeu; `E` como conector = `&` → Múltipla)

**TSV esperado:**
```
19/06/2026	Futebol		Lottu		Múltipla	Vinicius Jr. // Raphinha Marcar a Qualquer Momento [Brasil v Haiti]	76,00	4,50	L
```

---

## Feedback para a camada global

1. Produto **Desafio** (Bet Builder intra-jogo): a Lottu exibe como `Simples de X.XX` mas combina múltiplas condições de um único jogo via `&`. O sinal discriminante é o `&` na `Resposta`. Padrão similar ao "Criador de Apostas" da Bet365 e "Combo" de outras casas → classificado como `Múltipla` (validado no `MASTER_APOSTAS §93`).
2. **Conector `E` em multi-player:** `VINICIUS JR. E RAPHINHA PARA MARCAREM` usa `E` como conector em vez de `&`. Ambos são equivalentes → documentado na §9 desta casa.

---

VERSÃO: 2026
STATUS: ATIVA
CASA: `Lottu`
ATUALIZADO: 2026-06-21 (sessão 41)
