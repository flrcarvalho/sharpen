# CASA_VITORIABET
## Camada de tradução — Vitória Bet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Vitória Bet.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Vitória Bet`
- Domínio: `vitoriabet.bet` · Aliases: `vitoriabet.bet.br`, "Vitoria Bet" (sem acento)
- Locale: pt-BR na interface, mas **valores numéricos em en-US** — stake e odd usam **ponto decimal** (`138.07`, `4.1`); moeda com **sufixo `BRL`** (`138.07 BRL`), não prefixo `R$`
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** texto colado / screenshot da aba **"Histórico de apostas"** (lista de cards).
- **FALLBACK:** tela de **detalhe** do bilhete (chevron `>`) ou botão **"Compartilhar"** — usar quando a descrição da lista vier truncada e a precisão importar (ver §13).

> ⚠️ **A lista de histórico trunca a descrição** (ex.: `Ambas as equipes marcarão. Espan...`), tanto no copiar/colar quanto no print. O mercado quase sempre continua legível; o que se perde é o **confronto / as pernas**. Para o texto completo, abrir o detalhe do bilhete ou "Compartilhar".

### 2.2 Tipo do bilhete declarado

A Vitória Bet **não** exibe rótulo "Simples / Múltipla". Todo bilhete aparece com o chip genérico **`Sim / Não · Sim`** (wrapper de seleção, **não** é o mercado). Tipo inferido:
- 1 seleção / 1 confronto → categoria do mercado da seleção
- 2+ pernas, `Vencedores` no **plural**, ou múltiplos confrontos separados por `•` → `Múltipla`. Fórmula de odd: `MASTER_RESULTADO_2026 §7`.

### 2.3 Layout do bilhete (card do Histórico)

Anatomia de cima para baixo:
```
Nº<n> • <data/hora de colocação>          ← ID do bilhete + colocação
[chip]  Sim / Não · Sim · <odd> · >       ← wrapper de seleção + ODD + chevron p/ detalhe
[ícone] ✅ verde (ganha) / ❌ vermelho (perde)
<DATA DO EVENTO>, <HH:MM>                  ← data do evento ← USAR ESTA DATA
<descrição do mercado / confronto>         ← TRUNCADA na lista ("...")
Soma da aposta            <NNN.NN BRL>     ← stake
Pagamento                 <NNN.NN BRL>     ← retorno (campo financeiro)
[ Compartilhar ]                           ← botão (ruído)
```

**Ordem do output:** o Histórico exibe do mais recente (topo) ao mais antigo (baixo). TSV: **inverso** — último card no texto (mais antigo) = 1ª linha; primeiro card (mais recente) = última linha (`MASTER_OUTPUT_2026 §15`).

---

## 3. ID do bilhete

- Caso: **visível** — campo `Nº<n>` (numérico sequencial por conta), primeiro campo do card. Ex.: `Nº20`, `Nº15`.
- **Código (11ª coluna interna):** gravar o **número puro** exibido, sem o rótulo `Nº` (ex.: `20`).
- Nunca vai no output para o usuário (10 colunas); serve para contar, validar e deduplicar.
- Dedup por `Código` via `repository.py` (`_assinatura` = `ID|casa|parceiro|codigo`). O escopo `casa+parceiro` garante que o número curto/sequencial não colida entre contas.
- **IDs diferentes = bilhetes distintos** — sempre INSERT, mesmo com conteúdo idêntico (ex.: Nº18 e Nº19 são a mesma aposta com stake diferente → duas linhas).

---

## 4. Data

- Fonte primária: **data do evento** — campo `DD DE MMM., HH:MM` (ex.: `2 DE JUL., 16:00`) logo abaixo do ícone de resultado.
- Fallback: colocação (`Nº<n> • <data>`) só se a data do evento não estiver visível.
- Formato fonte: `DD DE MMM., HH:MM` (mês abreviado em pt-BR) → converter para `DD/MM/AAAA` (descartar horário).
- Múltipla: data = evento da **perna mais recente** (regra global, `MASTER_OUTPUT_2026`).

> ⚠️ Há **duas datas** no card (colocação no topo, evento abaixo do resultado). Usar sempre a do **evento**. Se rodar em servidor UTC (Railway), fixar `America/Sao_Paulo` ao usar "data atual".

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar o sinal visual (✅/❌) direto. Traduzir sempre para `W · L · V · HW · HL`.

| Vitória Bet exibe | Nosso código |
|---|---|
| Ícone ✅ verde + `Pagamento > Soma da aposta` | W |
| Ícone ❌ vermelho + `Pagamento = 0.00 BRL` | L |
| `Pagamento = Soma da aposta` (stake devolvida) | V *(aguarda amostra)* |
| *(meia vitória — rótulo não confirmado)* | HW *(aguarda amostra)* |
| *(meia derrota — rótulo não confirmado)* | HL *(aguarda amostra)* |

Conferência financeira (segunda linha de defesa): `Pagamento = 0` → L · `Pagamento = Soma` → V · `Pagamento > Soma` → W.

**Gatilho de meia-liquidação (HW/HL):**
- Primário: rótulo não confirmado — só detectável pela assinatura financeira.
- Confirmação por assinatura financeira **exata**: `HL → Pagamento = Soma/2` · `HW → Pagamento = (Soma/2) × (odd + 1)`.
- Esta assinatura também distingue HW/HL de cashout (retorno arbitrário).

Apostas abertas → `extraction_state = aberta`.

---

## 6. Boost / promoção

- Tem boost: **não confirmado** — aguarda amostra.
- Comportamento (regra global): se o `Pagamento` já embutir o boost → `Odd = Pagamento ÷ Soma` captura automaticamente.

<!-- TODO: confirmar se há boost/odds turbinadas e se o Pagamento embute o boost. -->

---

## 7. Cashout

- Tem cashout: **não confirmado** — aguarda amostra.
- Regra global: `Odd = Cashout ÷ Soma` (resultado = W); se `Cashout = Soma` → resultado `V`, preservar odd exibida.

<!-- TODO: confirmar localizador e rótulo visual do cashout encerrado. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — aguarda amostra.
- **Política:** pendente até ter amostra real.

<!-- TODO: confirmar se há apostas de bônus e como identificá-las. -->

---

## 9. Mapa de mercados (Vitória Bet → `Aposta` global)

> Fonte de verdade das categorias: `MASTER_APOSTAS_2026 §3`. Este mapa lista **apenas** os mercados já confirmados num bilhete real desta casa (camada fina) — a taxonomia completa vive no MASTER e **não** se reescreve aqui.

| Vitória Bet exibe (rótulo real) | Aposta global | Status |
|---|---|---|
| `Ambas as equipes marcarão` | Ambas Marcam | ✓ confirmado |
| `[Seleção] vencerá` · `Vencedores` (1 confronto) | ML | ✓ confirmado |
| `Vencedores.` (plural / 2+ confrontos separados por `•`) · 2+ pernas combinadas | Múltipla | ✓ confirmado |

**Notas de reconstrução:**
- O chip **`Sim / Não · Sim`** é o wrapper da seleção, **não** o mercado — o mercado real está na linha de descrição. Nunca vai na coluna Aposta nem na Descrição.
- Confronto: separador `•` entre duas seleções → `[Time A v Time B]` (padrão global, `MASTER_DESCRICAO_2026`). Atenção: na lista, `•` às vezes separa os dois times de **um** confronto e às vezes separa **pernas** de uma múltipla — desambiguar pelo detalhe quando incerto.
- Descrição truncada na lista → preservar o parcial legível (confronto/seleção visíveis); **nunca inventar** perna cortada. Só usar `Mercado Especial - REVISAR` (`MASTER_DESCRICAO_2026 §18`) se o mercado em si for irrecuperável.
- Mercado sem categoria global → `Outros` ⚠️ + registrar no §Feedback.

---

## 10. Stake

- Localização: campo `Soma da aposta` no rodapé do card.
- Formato: **en-US com sufixo `BRL`** — `138.07 BRL`, `200.00 BRL`, `100.00 BRL` (ponto decimal, sem separador de milhar visível).
- Normalização: remover ` BRL`, trocar o ponto decimal por vírgula → `138,07`. Se aparecer vírgula de milhar (`1,050.00`), ela é **milhar** (remover), não decimal.
- Normalização final (símbolo, trim, milhar) = global (`MASTER_OUTPUT_2026 §11/§16`).

---

## 11. Odds

> **Campo financeiro principal: `Pagamento`** — retorno bruto total (stake × odd em W). O chip exibe a **odd**.

- Localização da odd exibida: número dentro do chip `Sim / Não · Sim · <odd> · >` (ex.: `10`, `4.1`).
- Localização do campo financeiro: `Pagamento: <NNN.NN BRL>`.
- Odd em **ponto decimal** → converter para vírgula; **preservar a precisão exibida** (`4.1` → `4,1`, nunca `4,10`).

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Pagamento ÷ Soma` (deve coincidir com a odd do chip) |
| L | odd **exibida** no chip — nunca `0,00` |
| V | odd **exibida** — nunca `1,00` |
| HW | odd **exibida** — nunca metade |
| HL | odd **exibida** — nunca metade |
| Cashout (≠ Soma) | `Odd = Cashout ÷ Soma` |

**Múltiplas:** a odd do chip já é a odd combinada → usá-la em L/V; em W, `Pagamento ÷ Soma`.

> ⚠️ Em `L` a odd nunca vira `0,00`; em `V` nunca `1,00`. Odd exibida é sempre preservada. `Pagamento ÷ Soma` vale **só** para W / cashout / boost. Precisão: preservar — não truncar nem arredondar.

---

## 12. Ruído a ignorar

chip `Sim / Não` (wrapper de seleção) · botão `Compartilhar` · labels `Soma da aposta` / `Pagamento` (os valores vêm ao lado) · prefixo `Nº` e separador `•` do cabeçalho · chevron `>` · data/hora de **colocação** (usar a do evento) · ícones ✅ / ❌

---

## 13. Pegadinhas (resumo rápido)

- **Descrição truncada na lista** (`...`): o mercado geralmente é legível, mas o confronto/pernas podem estar cortados. Preservar o parcial; abrir o detalhe/`Compartilhar` para o texto completo. Nunca completar por inferência insegura.
- **Chip `Sim / Não · Sim` não é o mercado** — é só a moldura da seleção. O mercado está na linha de descrição.
- **Stake e odd em en-US (ponto decimal), moeda em sufixo `BRL`** — converter para vírgula; não confundir ponto decimal com milhar.
- **Duas datas** (colocação × evento) — usar sempre a do **evento**.
- **Odd alta + `Vencedores` plural / `•` entre confrontos = Múltipla**, não simples. Não classificar como ML uma combinação de vencedores.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

**Específicas da Vitória Bet:**
- Odd e stake convertidos de ponto para vírgula: `4.1` → `4,1`; `138.07 BRL` → `138,07`.
- W cross-check: `Pagamento ÷ Soma = odd do chip` (devem bater — discrepância indica leitura errada).
- Chip `Sim / Não` nunca aparece na coluna Aposta nem na Descrição.
- Confronto normalizado: separador `•` → `v`, com colchetes `[Time A v Time B]`.
- `Código` = número do `Nº` sem o rótulo (ex.: `Nº20` → `20`).

---

## 15. Exemplos golden (bilhetes reais — Histórico de apostas)

Lote real (2 prints do Histórico, Nº15–Nº20, capturado 02–03/07/2026).

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

> **Ordem de output:** lista = mais recente (Nº20) no topo → TSV inverso (Nº15 = 1ª linha, Nº20 = última).
> **Política de descrição (§2.1/§9):** classificar pelo mercado legível; descrição parcial honesta onde o confronto/perna vem truncado — nunca inventar. O `Nº` vai no `Código`.
> **Pendências de amostra (não bloqueiam):** V, HW/HL, cashout, boost, bônus e **W-simples** ainda não observados (o único W do lote, Nº16, é Múltipla). Casa **low-volume** — o lote completo disponível já foi processado; novas amostras desses cenários são improváveis a curto prazo. As regras globais cobrem esses casos quando surgirem.

---

### G1 (TSV linha 1) — L · ML · Países Baixos v Marrocos

**Input (card Histórico):** `Nº15` · chip `Sim / Não · Sim · 5.1` · ❌ · evento `29 DE JUN., 22:00` · desc `Países Baixos Marrocos. Países Baixos vencerá • ...` · Soma `100.00 BRL` · Pagamento `0.00 BRL`.

**Verificação:** Pagamento = 0 → L. Odd exibida = 5,1 (preservar). Mercado legível = "Países Baixos vencerá" → ML. Confronto = [Países Baixos v Marrocos]. Trailing `• ...` truncado — se for 2ª perna, seria Múltipla; confirmar no detalhe.

**TSV esperado:**
```
29/06/2026	Futebol		Vitória Bet		ML	Países Baixos [Países Baixos v Marrocos]	100,00	5,1	L	15
```

---

### G2 (TSV linha 2) — W · Múltipla · Noruega + França

**Input (card Histórico):** `Nº16` · chip `Sim / Não · Sim · 6` · ✅ · evento `30 DE JUN., 14:00` · desc `Vencedores. Noruega (Costa do Ma... Noruega) • França (França...` · Soma `100.00 BRL` · Pagamento `600.00 BRL`.

**Verificação:** Pagamento R$600 > Soma R$100 → W. Odd = 600 ÷ 100 = 6 ✓. `Vencedores` plural + dois confrontos (`•`) → Múltipla (2 vencedores). Adversário da França truncado — preservar parcial.

**TSV esperado:**
```
30/06/2026	Futebol		Vitória Bet		Múltipla	Noruega [Noruega v Costa do Marfim] + França [França v ...]	100,00	6	W	16
```

---

### G3 (TSV linha 3) — L · Múltipla · Inglaterra + Bélgica

**Input (card Histórico):** `Nº17` · chip `Sim / Não · Sim · 4.3` · ❌ · evento `1 DE JUL., 13:00` · desc `Vencedores. Inglaterra (Inglaterra RD Congo) • Bélgica (Bélgica...` · Soma `100.00 BRL` · Pagamento `0.00 BRL`.

**Verificação:** Pagamento = 0 → L. Odd exibida = 4,3 (preservar). `Vencedores` plural + dois confrontos → Múltipla. Adversário da Bélgica truncado — preservar parcial.

**TSV esperado:**
```
01/07/2026	Futebol		Vitória Bet		Múltipla	Inglaterra [Inglaterra v RD Congo] + Bélgica [Bélgica v ...]	100,00	4,3	L	17
```

---

### G4 (TSV linha 4) — L · ML · Estados Unidos v Bósnia e Herzegovina

**Input (card Histórico):** `Nº18` · chip `Sim / Não · Sim · 4.1` · ❌ · evento `1 DE JUL., 21:00` · desc `Estados Unidos Bósnia e Herzegovina. Estados Uni...` · Soma `100.00 BRL` · Pagamento `0.00 BRL`.

**Verificação:** Pagamento = 0 → L. Odd exibida = 4,1 (preservar). Mercado legível = "Estados Unidos [vencerá]" → ML. Confronto = [Estados Unidos v Bósnia e Herzegovina].

**TSV esperado:**
```
01/07/2026	Futebol		Vitória Bet		ML	Estados Unidos [Estados Unidos v Bósnia e Herzegovina]	100,00	4,1	L	18
```

---

### G5 (TSV linha 5) — L · ML · Estados Unidos v Bósnia e Herzegovina (mesma aposta, stake maior)

**Input (card Histórico):** `Nº19` · chip `Sim / Não · Sim · 4.1` · ❌ · evento `1 DE JUL., 21:00` · desc `Estados Unidos Bósnia e Herzegovina. Estados Uni...` · Soma `200.00 BRL` · Pagamento `0.00 BRL`.

**Verificação:** Pagamento = 0 → L. Odd exibida = 4,1. Conteúdo idêntico ao Nº18, mas **`Nº` diferente** → bilhete distinto (INSERT), nunca deduplicado com o G4. Demonstra a regra de dedup por `Código`.

**TSV esperado:**
```
01/07/2026	Futebol		Vitória Bet		ML	Estados Unidos [Estados Unidos v Bósnia e Herzegovina]	200,00	4,1	L	19
```

---

### G6 (TSV linha 6) — L · Múltipla · Ambas Marcam (BTTS combinado)

**Input (card Histórico):** `Nº20` · chip `Sim / Não · Sim · 10` · ❌ · evento `2 DE JUL., 16:00` · desc `Ambas as equipes marcarão. Espan... • Áustria • Portugal` · Soma `138.07 BRL` · Pagamento `0.00 BRL`.

**Verificação:** Pagamento = 0 → L. Odd exibida = 10 (preservar). Mercado = "Ambas as equipes marcarão"; odd 10 + múltiplas referências → Múltipla (BTTS combinado). Confronto [Áustria v Portugal] legível; demais pernas (`Espan...`) truncadas — preservar parcial, não inventar.

**TSV esperado:**
```
02/07/2026	Futebol		Vitória Bet		Múltipla	Ambas Marcam [Áustria v Portugal] + Ambas Marcam [Espanha v ...]	138,07	10	L	20
```

---

## Feedback para a camada global / MODELO

1. **Descrição truncada na lista de histórico:** a Vitória Bet corta a descrição no view de lista (copiar/colar e print), preservando só o início do mercado. Tratamento adotado (sem mudança de master; **decisão do Feca: a descrição não fica perfeita de qualquer jeito → a IA tem latitude para escolher o melhor caminho por bilhete na extração**): classificar pelo mercado legível + descrição parcial honesta; fallback = tela de detalhe / "Compartilhar". Espelha o padrão KTO/Superbet (segunda fonte quando a lista não expõe o campo).
2. **Chip genérico `Sim / Não`:** todos os bilhetes usam a moldura "Sim / Não · Sim" como wrapper de seleção; o mercado real vive na descrição. Documentado como ruído (§12) e pegadinha (§13). Sem proposta de mudança global.

---

VERSÃO: 2026
STATUS: ATIVO (v1 — 6 goldens reais, 03/07/2026; casa low-volume, lote completo processado; W/L confirmados; V/HW/HL/cashout/boost/bônus e W-simples sem amostra — não bloqueiam)
CASA: `Vitória Bet`
