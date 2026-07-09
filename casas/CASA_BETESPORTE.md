# CASA_BETESPORTE
## Camada de tradução — BETesporte → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da BETesporte.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `BETesporte` *(BET em caixa alta + esporte em minúsculas — grafia exata na coluna `Casa`)*
- Domínio: `betesporte.bet.br` · Aliases: `BET esporte`, "Betesporte" (sem o caixa-alta)
- Locale: pt-BR na interface, mas **números mistos** — **odd em ponto decimal** (`1.85`, `12.60`); **stake e retorno em pt-BR com vírgula** e prefixo `R$` (`R$ 50,00`). Via robô/API os números já vêm normalizados (ver §2.1).
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO (robô SharpenUp — modo texto):** a extensão lê **passivamente** a RESPOSTA da API que a própria página baixa — `POST /api/bet/RequestUserTickets` (JSON exato: `id`, `odd`, `value`, `possibleReturn`, `status`, `date`, `betNome`, `optionNome`). O robô só **rola** a lista p/ a página paginar; **não clica em "Ver Cupom"** e não faz requisição nova (o Bearer/JWT fica com a página). Cada bilhete vira um bloco de texto com o marcador **`[Código: <id>]`** — a mesma fronteira da Superbet, que o backend usa para split + pré-dedup por ID.
  - Registro: `captura.py` `_MODO_POR_CASA["BETESPORTE"] = "texto"`; interceptor em `extensor/be_inject.js` (mundo MAIN, só no domínio da casa); formatação em `extensor/content.js` (`formatTicketBE` / `roboBetesportePassive`).
- **FALLBACK (print da lista "Minhas Apostas"):** screenshots dos cards verticais. **Sem ID** → dedup só por assinatura (ver §3). Usar apenas se o robô não estiver disponível.

### 2.2 Tipo do bilhete declarado

A BETesporte **declara o tipo no início do título** (`betNome`) dos mercados combinados: `DUPLA - …`, `TRIPLA - …`, `MÚLTIPLA - …`. Este rótulo define a categoria `Múltipla` e a fórmula de odd (`MASTER_RESULTADO_2026 §7`).
- `DUPLA` / `TRIPLA` / `MÚLTIPLA` no início do título → `Múltipla`.
- Sem rótulo de tipo → categoria do mercado da seleção (ex.: `Jogo com o Gol mais Rápido` → `H2H`).

### 2.3 Layout do bloco (robô/API)

Cada bilhete chega assim (campos derivados do JSON da API):
```
[Código: 189070937]                               ← id do bilhete (dedup — §3)
Data: 02/07/2026                                  ← date (§4)
Stake: 20,00                                      ← value
Odd: 25,24                                        ← odd (já combinada nas múltiplas)
Retorno potencial: 504,80                         ← possibleReturn (value × odd, NÃO realizado)
Status: 1 (Perdido → L)                           ← status ← traduzir (§5)
Mercado: DUPLA - Portugal e Ponte Preta Vencerem Seus Jogos   ← betNome
Título: <partidaNome, se ≠ mercado>               ← só quando traz o confronto (H2H)
Seleção: Sim                                      ← optionNome (wrapper — ruído; §9)
```

**Ordem do output:** a API/lista vem do mais recente ao mais antigo. TSV: **inverso** — bilhete mais antigo = 1ª linha; mais recente = última (`MASTER_OUTPUT_2026 §15`). O backend já inverte no modo texto.

> **Layout do card (fallback print):** `[badge status] · Odd n.nn · R$ stake · R$ retorno · título · subtítulo (repete) · seleção verde · "Ver Cupom" · rodapé`. Sem ID.

---

## 3. ID do bilhete

- Caso: **VISÍVEL via API** (modo robô) — o campo `id` (numérico, ~9 dígitos, ex.: `189070937`) chega no marcador `[Código: <id>]`. É a chave forte de dedup, **exata** (vem do JSON, sem OCR).
- Backend: split por `[Código: …]` (`_SUPERBET_SPLIT_RE`), pré-dedup por ID (`_dedup_superbet_text`) e validação de código numérico (`_ID_BETESPORTE_RE`) — tudo reusado do trilho Superbet.
- Coluna `Código` (11ª interna) = o `id`.
- **Fallback print (sem robô):** a lista **não** expõe o ID (só o "Ver Cupom") → assinatura derivada = `data + stake + retorno + confronto(s)`; dois bilhetes 100% idênticos não se distinguem (o sistema salva um e avisa). Essa limitação **desaparece** no modo robô.

---

## 4. Data

- Fonte primária (robô/API): campo **`date`** (`2026-07-02T10:55:18`) → `DD/MM/AAAA` (descarta horário). Vem **sem timezone = já local** (America/São_Paulo) — o robô só recorta `AAAA-MM-DD` (não converte de UTC, senão pularia 1 dia).
- É a data de **colocação/liquidação** do bilhete (a API não expõe data de evento por perna nos parlays "Vencerem Seus Jogos"). Fica na cadeia de fallback global como proxy de colocação — muito melhor que "data atual".
- Múltipla: a API traz uma data única do bilhete (usar direto).

> ⚠️ **Pegadinha (fallback print):** o topo da tela mostra só um **filtro de período** (`08/06/2026 - 08/07/2026`) — **não é a data do bilhete**. Nunca usar o período como data.

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar o rótulo/código visual da casa direto. Traduzir sempre para `W · L · V · HW · HL`.

**Mapa do `status` numérico da API** (confirmados nos goldens reais):

| `status` da API | BETesporte exibe | Nosso código |
|---|---|---|
| `1` | `Perdido` (badge vermelho, `Retorno R$ 0,00`) | **L** |
| `2` | `Ganho` (badge verde, `Retorno > Stake`) | **W** |
| *(qualquer outro código)* | Aberto / Devolvido / Encerrado / Cancelado — **sem amostra** | *(a conferir — ver abaixo)* |

- **Só `1` e `2` foram observados** (o dono nunca teve outro estado). O robô, ao ver `status ∉ {1,2}` **ou** `openBetsCount > 0`, emite `Status: … (a conferir — não liquidar automaticamente)` / `em aberto` — a linha **não vira W/L sozinha**; sai marcada p/ revisão manual. Isso cumpre a regra: **nunca chutar resultado**.
- Quando o primeiro Aberto/Devolvido/Encerrado/Cancelado real aparecer, mapear o número aqui (2 min) — Devolvido → `V`; Encerrado → cashout (§7); Aberto → `extraction_state = aberta`.

Conferência financeira (segunda linha de defesa): `Retorno realizado = 0` → L · `= Stake` → V · `> Stake` → W. **Atenção:** o `possibleReturn` da API é o retorno **potencial** (`value × odd`), **não** o realizado — nunca usá-lo para decidir W/L; quem decide é o `status`.

**Meia-liquidação (HW/HL):** sem amostra nesta casa. Se surgir, confirmação por assinatura financeira **exata**: `HL → retorno = Stake/2` · `HW → retorno = (Stake/2) × (odd + 1)`.

---

## 6. Boost / promoção

- Tem boost: **não confirmado** — aguarda amostra. Nos goldens, `possibleReturn = value × odd` exatamente (sem boost embutido).
- Comportamento (regra global): se o retorno já embutir boost → `Odd = Retorno realizado ÷ Stake` captura automaticamente.

<!-- TODO: confirmar se há odds turbinadas/promos e se o retorno embute o boost. -->

---

## 7. Cashout

- Tem cashout: **sim** (campo `cashoutValue` na API; `0` quando não houve). Rodapé "Encerrar" no card; no lote observado sempre "Encerrar Indisponível".
- O robô emite `Cashout: <valor>` quando `cashoutValue > 0`.
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → `V`, preservar odd exibida.
- **Distinção de meia-liquidação:** cashout produz retorno arbitrário (não casa com `Stake/2` nem `(Stake/2)×(odd+1)`).

<!-- TODO: confirmar o status numérico de um bilhete Encerrado por cashout quando surgir. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — aguarda amostra. A API traz `paymentType` (nos goldens sempre `1`); um valor diferente pode indicar bônus.
- **Política:** pendente até ter amostra real.

<!-- TODO: confirmar se paymentType ≠ 1 identifica bônus/freebet. -->

---

## 9. Mapa de mercados (BETesporte → `Aposta` global)

> Fonte de verdade das categorias: `MASTER_APOSTAS_2026 §3`. Este mapa lista **apenas** os mercados já confirmados num bilhete real desta casa (camada fina).

| BETesporte exibe (`betNome`) | Aposta global |
|---|---|
| `DUPLA - … Vencerem Seus Jogos` · `TRIPLA - … Vencerem seus Jogos` · `MÚLTIPLA - … Vencerem Seus Jogos` (seleção "Sim") | Múltipla |
| `Jogo com o Gol mais Rápido` · `… ter o Gol + Rápido Contra o Jogo …` (seleção = jogo escolhido) | H2H |

**Notas de reconstrução:**
- **Campos do robô:** `Mercado` = `betNome` (o mercado); `Título` = `partidaNome` (o confronto, só aparece quando ≠ mercado, ex.: H2H); `Seleção` = `optionNome`.
- **"Vencerem Seus Jogos" = Múltipla:** parlay de vitórias (ML) de times distintos, pré-montado pela casa e apostado como "Sim". A casa **não exibe os adversários** (nem no card, nem na API) → descrição = os times unidos por ` // `, **sem confronto** (`MASTER_DESCRICAO_2026 §19.10`; nunca inventar adversário). Espelha o precedente Vitória Bet.
- **"Gol mais Rápido" = H2H (decisão do Feca):** mercado comparativo entre **dois jogos** — aposta-se em qual dos dois terá o gol mais rápido. Descrição: `Gol mais Rápido - [jogo apostado] v [outro jogo]`, com o **jogo apostado primeiro** (o `optionNome` / o primeiro no título "A e B (x) C e D").
- Título "A e B **(x)** C e D": o `(x)` separa os **dois jogos comparados**; o `e` liga os dois times de **um** jogo → confronto `[A v B]`. Não confundir o `e` (times de um jogo) com o `(x)` (jogos comparados).
- Seleção `Sim` é o wrapper da proposição — **nunca** vai na coluna Aposta nem na Descrição.
- Sufixos como `(LIMITE: R$1.000)` = teto de pagamento (ruído) → ignorar na descrição.
- Mercado sem categoria global → `Outros` ⚠️ + registrar no §Feedback.

---

## 10. Stake

- Localização: campo `value` da API (robô) / 1º `R$` do card (fallback print).
- Formato: robô entrega já normalizado com vírgula (`20,00`); no card é pt-BR (`R$ 50,00`).
- Normalização final (símbolo, trim, milhar) = global (`MASTER_OUTPUT_2026 §11/§16`).

---

## 11. Odds

> **Campo financeiro principal:** `possibleReturn` (retorno **potencial** = `value × odd`). Em W, potencial = realizado → `possibleReturn ÷ Stake` reconstrói a odd (cross-check). Em L/V/HL, a odd vem do campo `odd` — **nunca** derivar odd de retorno potencial de um bilhete perdido.

- Localização da odd exibida: campo `odd` da API / rótulo `Odd n.nn` no card.
- Odd em **ponto decimal** → converter para vírgula, **preservar precisão** (`1.85` → `1,85`; `25.24` → `25,24`). Odds inteiras da API vêm sem casas (`3.00` → `3`; `4.00` → `4`) — é a precisão completa, nada foi truncado (`3` ≡ `3,00`).

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Retorno realizado ÷ Stake` (coincide com o campo `odd`) |
| L | campo `odd` — nunca `0,00` |
| V | campo `odd` — nunca `1,00` |
| HW / HL | campo `odd` — nunca metade |
| Cashout (≠ Stake) | `Odd = Cashout ÷ Stake` |

**Múltiplas ("Vencerem Seus Jogos"):** a API traz **uma odd única** já combinada (ex.: `25.24`) → usá-la direto em L/V; em W, `Retorno ÷ Stake`. **Não** recalcular por produto de pernas (os adversários/odds individuais não aparecem).

> ⚠️ Em `L` a odd nunca vira `0,00`; em `V` nunca `1,00`. `Retorno ÷ Stake` vale **só** para W / cashout / boost. Precisão: preservar.

---

## 12. Ruído a ignorar

`Seleção: Sim` (wrapper) · rótulos dos campos (os valores vêm ao lado) · `Retorno potencial` (é potencial, não decide resultado) · sufixo `(LIMITE: R$X)` · **[fallback print]** badge de status (traduzido, não copiado), botão `Ver Cupom`, subtítulo cinza (repete o título), filtro de período no topo (**não é data**)

---

## 13. Pegadinhas (resumo rápido)

- **`status` decide W/L, não o retorno** — `possibleReturn` é o potencial (`value × odd`); um bilhete PERDIDO tem `possibleReturn > 0` e mesmo assim é `L` (`status 1`).
- **Só `status 1` (L) e `2` (W) mapeados** — qualquer outro (ou `openBetsCount > 0`) sai "a conferir", **não** liquida automático.
- **`date` vem sem timezone** = já local; recortar `AAAA-MM-DD`, **não** converter de UTC.
- **`(x)` no título separa dois JOGOS, `e` separa dois TIMES de um jogo** — errar isso quebra o confronto do H2H.
- **`DUPLA/TRIPLA/MÚLTIPLA` é o tipo, não o mercado** → categoria `Múltipla`; a odd da API já é a combinada (não multiplicar pernas).
- **Múltipla sem adversários** — descrição fica sem confronto (só os times por ` // `). Nunca inventar o adversário.
- **Odd inteira vem sem casas** (`3`, `4`) — é precisão completa, não truncar "de volta".
- **[fallback print] sem ID** → dedup por assinatura; o modo robô resolve.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7) + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

**Específicas da BETesporte:**
- Resultado **só** de `status` (1→L, 2→W); status desconhecido / `openBetsCount>0` → linha "a conferir", nunca W/L.
- `Código` = `id` numérico da API (11ª coluna preenchida no modo robô).
- Odd convertida de ponto para vírgula, precisão preservada; odd inteira sem casas é válida.
- W cross-check: `Retorno realizado ÷ Stake = odd exibida`.
- Múltipla usa a **odd única** — nunca produto de pernas (adversários ausentes).
- Título com `(x)`: separar jogos (`(x)`) de times (`e`); confronto = `[Time A v Time B]`.
- Seleção `Sim` nunca aparece na coluna Aposta nem na Descrição.
- `possibleReturn` (retorno potencial) nunca decide resultado.

---

## 15. Exemplos golden (bilhetes reais — API `RequestUserTickets`)

Lote real capturado da API em 08/07/2026 (dados do dono FERNANDO CARVALHO).

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

> **Ordem de output:** API = mais recente primeiro → TSV inverso (bilhete mais antigo = 1ª linha).
> **Pendências (não bloqueiam):** V, HW/HL, cashout encerrado, boost, bônus e aberta ainda sem amostra — as regras globais + o "a conferir" (§5) cobrem quando surgirem.

---

### G1 — L · H2H · Gol mais Rápido (Argélia v Áustria) · id 188644540

**Input (bloco do robô):**
```
[Código: 188644540]
Data: 27/06/2026
Stake: 150,00
Odd: 4
Retorno potencial: 600,00
Status: 1 (Perdido → L)
Mercado: Jogo com o Gol mais Rápido
Título: Argélia e Áustria (x) Jordânia e Argentina
Seleção: Argélia x Áustria
```

**Verificação:** `status 1` → L. Odd = campo `odd` = 4 (preservar, nunca 0 nem derivar do potencial). `(x)` separa os dois jogos; jogo apostado (`Seleção`) = Argélia v Áustria (primeiro). H2H entre os dois jogos.

**TSV esperado:**
```
27/06/2026	Futebol		BETesporte		H2H	Gol mais Rápido - [Argélia v Áustria] v [Jordânia v Argentina]	150,00	4	L	188644540
```

---

### G2 — W · H2H · Gol mais Rápido (Brasil v Japão) · id 188755646

**Input (bloco do robô):**
```
[Código: 188755646]
Data: 29/06/2026
Stake: 200,00
Odd: 3
Retorno potencial: 600,00
Status: 2 (Ganho → W)
Mercado: Brasil (x) Japão ter o Gol + Rápido Contra o Jogo da Alemanha (x) Paraguai (LIMITE: R$1.000)
Seleção: Sim
```

**Verificação:** `status 2` → W. Retorno realizado = 600 = Stake 200 × 3 → odd 3 ✓ (cross-check). Comparação de gol mais rápido entre `[Brasil v Japão]` (apostado) e `[Alemanha v Paraguai]`. `(LIMITE: R$1.000)` = teto de pagamento (ruído). H2H.

**TSV esperado:**
```
29/06/2026	Futebol		BETesporte		H2H	Gol mais Rápido - [Brasil v Japão] v [Alemanha v Paraguai]	200,00	3	W	188755646
```

---

### G3 — L · Múltipla · DUPLA (2 vitórias) · id 189070937

**Input (bloco do robô):**
```
[Código: 189070937]
Data: 02/07/2026
Stake: 20,00
Odd: 25,24
Retorno potencial: 504,80
Status: 1 (Perdido → L)
Mercado: DUPLA - Portugal e Ponte Preta Vencerem Seus Jogos
Seleção: Sim
```

**Verificação:** `status 1` → L (o `possibleReturn` 504,80 é potencial — **não** torna a aposta W). Odd = 25,24 (preservar). `DUPLA` → Múltipla; odd única combinada. Adversários ausentes → descrição sem confronto, times por ` // `.

**TSV esperado:**
```
02/07/2026	Futebol		BETesporte		Múltipla	Portugal // Ponte Preta	20,00	25,24	L	189070937
```

---

### G4 — L · Múltipla · TRIPLA (3 vitórias) · id 189056063

**Input (bloco do robô):**
```
[Código: 189056063]
Data: 02/07/2026
Stake: 26,00
Odd: 13,81
Retorno potencial: 359,06
Status: 1 (Perdido → L)
Mercado: TRIPLA - Espanha, Portugal e América-MG Vencerem Seus Jogos
Seleção: Sim
```

**Verificação:** `status 1` → L. Odd = 13,81 (preservar). `TRIPLA` → Múltipla. 3 times unidos por ` // `, ordem original preservada (`MASTER_DESCRICAO_2026 §15`). Sem confronto.

**TSV esperado:**
```
02/07/2026	Futebol		BETesporte		Múltipla	Espanha // Portugal // América-MG	26,00	13,81	L	189056063
```

---

### G5 — L · Múltipla · MÚLTIPLA (4 vitórias) · id 188957818

**Input (bloco do robô):**
```
[Código: 188957818]
Data: 01/07/2026
Stake: 26,00
Odd: 8,11
Retorno potencial: 210,86
Status: 1 (Perdido → L)
Mercado: MÚLTIPLA - Bélgica, EUA, Espanha e Portugal Vencerem Seus jogos
Seleção: Sim
```

**Verificação:** `status 1` → L. Odd = 8,11 (preservar). `MÚLTIPLA` → Múltipla; 4 pernas unidas por ` // `, ordem original preservada. Sem confronto (adversários ausentes).

**TSV esperado:**
```
01/07/2026	Futebol		BETesporte		Múltipla	Bélgica // EUA // Espanha // Portugal	26,00	8,11	L	188957818
```

---

## Feedback para a camada global / MODELO

1. **"Gol mais Rápido" classificado como `H2H` (decisão do Feca):** mercado comparativo entre **dois jogos** (qual terá o gol mais rápido). Estende o `H2H` do `MASTER_APOSTAS_2026 §5` (hoje exemplificado com entidade-vs-entidade) para **jogo-vs-jogo**. Sugestão: registrar no §5/§6 do MASTER_APOSTAS se reaparecer em outras casas.
2. **Mercados "N times Vencerem Seus Jogos" sem adversários:** a casa pré-monta um parlay de ML mas só mostra os times que devem vencer. Tratamento (sem mudança de master): `Múltipla` + descrição sem confronto, times por ` // `. Espelha o precedente Vitória Bet.
3. **Ingestão por API passiva (robô):** a BETesporte entra no mesmo trilho da Superbet (interceptor no mundo MAIN + marcador `[Código:]` → split/dedup do backend reusados). Sem mudança de master — só reuso da maquinaria existente.

---

VERSÃO: 2026
STATUS: ATIVO (v2 — robô/API `RequestUserTickets`; 5 goldens reais com Código, 08/07/2026; W/L confirmados em H2H e Múltipla; status 1=L, 2=W; Aberto/Devolvido/Encerrado/Cancelado sem amostra → "a conferir", não bloqueiam)
CASA: `BETesporte`
