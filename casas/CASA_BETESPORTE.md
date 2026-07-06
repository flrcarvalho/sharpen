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
- Locale: pt-BR na interface, mas **números mistos** — **odd em ponto decimal** (`1.85`, `12.60`); **stake e retorno em pt-BR com vírgula** e prefixo `R$` (`R$ 50,00`)
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** texto colado / screenshot da lista **"Minhas Apostas"** (cards verticais empilhados).
- **FALLBACK:** tela de detalhe do bilhete (botão **"Ver Cupom"**) — usar para recuperar a **data do evento** (a lista não a exibe — ver §4) e o confronto/adversário das múltiplas (ver §9).

### 2.2 Tipo do bilhete declarado

A BETesporte **declara o tipo no início do título** dos mercados combinados: `DUPLA - …`, `TRIPLA - …`, `MÚLTIPLA - …`. Este rótulo define a categoria `Múltipla` e a fórmula de odd (`MASTER_RESULTADO_2026 §7`).
- `DUPLA` / `TRIPLA` / `MÚLTIPLA` no início do título → `Múltipla`.
- Sem rótulo de tipo → categoria do mercado da seleção (no lote atual, só `Jogo com o Gol mais Rápido` → `H2H`).

### 2.3 Layout do bilhete (card de "Minhas Apostas")

Anatomia de cima para baixo:
```
[badge status]  Em Aberto / Ganho / Perdido      ← status ← traduzir (§5)
Odd  <n.nn>                                       ← ODD (ponto decimal)
R$ <stake>                                        ← stake
R$ <retorno potencial/obtido>                     ← campo financeiro
<título do mercado>                               ← linha bold (o mercado)
<subtítulo / repetição do mercado>                ← cinza itálico (repete o título)
<seleção>                                         ← verde: "Sim" ou o confronto escolhido
[ícone] Ver Cupom                                 ← botão p/ detalhe (ruído)
Encerrar Indisponível  /  R$ <retorno> Retorno    ← rodapé: aberto / liquidado
```

**Ordem do output:** a lista exibe do mais recente (topo) ao mais antigo (baixo). TSV: **inverso** — último card no texto (mais antigo) = 1ª linha; primeiro card (mais recente) = última linha (`MASTER_OUTPUT_2026 §15`).

---

## 3. ID do bilhete

- Caso: **ausente** — a lista não expõe número/ID do bilhete; só o botão "Ver Cupom".
- Assinatura derivada = `data + stake + retorno + confronto(s)` (regra global de dedup, `repository.py`).
- Coluna `Código` (11ª interna) fica **vazia**.
- **Limitação:** dois bilhetes 100% idênticos (mesmo mercado, stake, odd, retorno) não são distinguíveis sem ID — o sistema salva um e avisa (ver dedup em `CLAUDE.md`). No lote atual isso ocorre: **`DUPLA - Egito e Gana Vencerem Seus Jogos` · R$ 20,00 · 21.78** aparece **duas vezes** idêntica → colisão de assinatura esperada.

---

## 4. Data

- Fonte primária: **data do evento** no detalhe **"Ver Cupom"** (a lista de cards **não** exibe data por bilhete).
- Fallback(s), em ordem: data informada pela operação → colocação (se o evento for no mesmo dia) → **data atual em `America/Sao_Paulo`** (último recurso).
- Formato fonte (no cupom): converter para `DD/MM/AAAA` (descartar horário).
- Múltipla: data = evento da **perna mais recente** (regra global, `MASTER_OUTPUT_2026`).

> ⚠️ **Pegadinha crítica:** o topo da tela mostra apenas um **filtro de período** (ex.: `05/06/2026 - 05/07/2026`) — **não é a data do bilhete**. Nunca usar o período como data. Se a data não estiver disponível (lote só da lista), cai no fallback de extração — documentar. Em servidor UTC (Railway), fixar `America/Sao_Paulo` ao usar "data atual".

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar o rótulo visual da casa direto. Traduzir sempre para `W · L · V · HW · HL`.

| BETesporte exibe | Nosso código |
|---|---|
| `Ganho` (badge verde) + `Retorno > Stake` | W |
| `Perdido` (badge vermelho) + `Retorno R$ 0,00` | L |
| `Em Aberto` (badge azul) | *(não liquida — `extraction_state = aberta`)* |
| *(void/anulação — rótulo não confirmado)* | V *(aguarda amostra)* |
| *(meia vitória — rótulo não confirmado)* | HW *(aguarda amostra)* |
| *(meia derrota — rótulo não confirmado)* | HL *(aguarda amostra)* |

Conferência financeira (segunda linha de defesa): `Retorno = 0` → L · `Retorno = Stake` → V · `Retorno > Stake` → W.

**Gatilho de meia-liquidação (HW/HL):**
- Primário: rótulo não confirmado — só detectável pela assinatura financeira.
- Confirmação por assinatura financeira **exata**: `HL → Retorno = Stake/2` · `HW → Retorno = (Stake/2) × (odd + 1)`.
- Esta assinatura também distingue HW/HL de cashout (retorno arbitrário).

Apostas abertas (`Em Aberto`) → `extraction_state = aberta` (fora da fila de cópia). O rodapé dessas mostra **"Encerrar Indisponível"** (cashout indisponível — ver §7).

---

## 6. Boost / promoção

- Tem boost: **não confirmado** — aguarda amostra.
- Comportamento (regra global): se o campo de retorno já embutir o boost → `Odd = Retorno ÷ Stake` captura automaticamente.

<!-- TODO: confirmar se há odds turbinadas/promos e se o retorno embute o boost. -->

---

## 7. Cashout

- Tem cashout: **parcial/condicional** — o rodapé exibe **"Encerrar"**, mas no lote observado sempre como **"Encerrar Indisponível"** (função existe, indisponível nesses bilhetes). Valor de cashout encerrado ainda **sem amostra**.
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → resultado `V`, preservar odd exibida.
- **Distinção de meia-liquidação:** cashout produz retorno arbitrário (não casa com `Stake/2` nem `(Stake/2)×(odd+1)`).

<!-- TODO: confirmar localizador e formato do valor quando um bilhete for encerrado por cashout. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — aguarda amostra.
- **Política:** pendente até ter amostra real.

<!-- TODO: confirmar se há apostas de bônus e como identificá-las. -->

---

## 9. Mapa de mercados (BETesporte → `Aposta` global)

> Fonte de verdade das categorias: `MASTER_APOSTAS_2026 §3`. Este mapa lista **apenas** os mercados já confirmados num bilhete real desta casa (camada fina) — a taxonomia completa vive no MASTER e **não** se reescreve aqui.

| BETesporte exibe (rótulo real) | Aposta global |
|---|---|
| `DUPLA - … Vencerem Seus Jogos` · `TRIPLA - … Vencerem seus Jogos` · `MÚLTIPLA - … Vencerem Seus Jogos` (seleção "Sim") | Múltipla |
| `Jogo com o Gol mais Rápido` · `… ter o Gol + Rápido Contra o Jogo …` (seleção = jogo escolhido ou "Sim") | H2H |

**Notas de reconstrução:**
- **"Vencerem Seus Jogos" = Múltipla:** é um parlay de vitórias (ML) de times distintos, pré-montado pela casa e apostado como "Sim". Espelha o precedente Vitória Bet (`Vencedores` plural → Múltipla) e a regra global Bet Builder → Múltipla. A casa **não exibe os adversários** → descrição = os times unidos por ` // `, **sem confronto** (`MASTER_DESCRICAO_2026 §19.10` — descrição válida sem confronto; nunca inventar adversário).
- **"Gol mais Rápido" = H2H (decisão do Feca):** mercado comparativo entre **dois jogos** — aposta-se em qual dos dois terá o gol mais rápido. Estende o conceito de H2H (entidade-vs-entidade) para jogo-vs-jogo. Descrição: `Gol mais Rápido - [jogo apostado] v [outro jogo]`, com o **jogo apostado primeiro** (o verde da seleção / o primeiro no título "A e B (x) C e D"). Registrado no §Feedback como extensão.
- Título "A e B **(x)** C e D": o `(x)` separa os **dois jogos comparados**; o `e` liga os dois times de **um** jogo → confronto `[A v B]`. Não confundir o `e` (times de um jogo) com o `(x)` (jogos comparados).
- Seleção `Sim` é o wrapper da resposta à proposição — **nunca** vai na coluna Aposta nem na Descrição.
- Sufixos como `(LIMITE: R$1.000)` = teto de pagamento (ruído) → ignorar na descrição.
- Mercado sem categoria global → `Outros` ⚠️ + registrar no §Feedback.

---

## 10. Stake

- Localização: 1ª linha `R$ <valor>` do bloco financeiro do card (acima do retorno).
- Formato: **pt-BR** — `R$ 50,00`, `R$ 200,00` (vírgula decimal, ponto de milhar se houver).
- Normalização: remover `R$ `, preservar vírgula decimal → `50,00`. Normalização final (símbolo, trim, milhar) = global (`MASTER_OUTPUT_2026 §11/§16`).

---

## 11. Odds

> **Campo financeiro principal: o valor de `Retorno`** — na lista, o 2º `R$` do card. Em aberto é o **retorno potencial** (`Stake × Odd`); liquidado é o **retorno obtido** (`R$ 252,00 Retorno`) em W e `R$ 0,00` em L.

- Localização da odd exibida: rótulo `Odd <n.nn>` no topo do card.
- Odd em **ponto decimal** → converter para vírgula; **preservar a precisão exibida** (`1.85` → `1,85`; `12.60` → `12,60`).

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Retorno obtido ÷ Stake` (deve coincidir com a odd exibida) |
| L | odd **exibida** — nunca `0,00` |
| V | odd **exibida** — nunca `1,00` |
| HW | odd **exibida** — nunca metade |
| HL | odd **exibida** — nunca metade |
| Cashout (≠ Stake) | `Odd = Cashout ÷ Stake` |

**Múltiplas ("Vencerem Seus Jogos"):** a casa exibe **uma odd única** já combinada (ex.: `12.60`) → usá-la direto em L/V; em W, `Retorno ÷ Stake` (deve coincidir). **Não** recalcular por produto de pernas (os adversários/odds individuais não aparecem).

> ⚠️ Em `L` a odd nunca vira `0,00`; em `V` nunca `1,00`. Odd exibida é sempre preservada. `Retorno ÷ Stake` vale **só** para W / cashout / boost. Precisão: preservar — não truncar nem arredondar.

---

## 12. Ruído a ignorar

badge de status (o texto é traduzido, não copiado) · rótulos `Odd` / `Retorno` (os valores vêm ao lado) · botão `Ver Cupom` e ícone de olho · rodapé `Encerrar Indisponível` · subtítulo cinza (repete o título — não é 2ª seleção) · seleção `Sim` (wrapper) · filtro de período no topo (**não é data**) · sufixo `(LIMITE: R$X)`

---

## 13. Pegadinhas (resumo rápido)

- **Sem data por bilhete na lista** — o topo mostra só o **filtro de período** (`05/06 - 05/07`), que **não é** a data do bilhete. Data real vem do "Ver Cupom"; sem ela, cai no fallback de extração (§4).
- **Sem ID visível** → dedup por assinatura; dois bilhetes idênticos não se distinguem (o par `Egito e Gana` R$ 20 · 21.78 aparece duplicado no lote).
- **`(x)` no título separa dois JOGOS, `e` separa dois TIMES de um jogo** — errar isso quebra o confronto do H2H.
- **`DUPLA/TRIPLA/MÚLTIPLA` é o tipo, não o mercado** → categoria `Múltipla`; a odd exibida já é a combinada (não multiplicar pernas).
- **Múltipla sem adversários** — descrição fica sem confronto (só os times por ` // `). Nunca inventar o adversário.
- **Odd em ponto, stake/retorno em vírgula** — converter só a odd; não confundir.
- **`Em Aberto` não liquida** — vai como `aberta`, fora da fila de cópia.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

**Específicas da BETesporte:**
- Odd convertida de ponto para vírgula, precisão preservada: `1.85` → `1,85`; `12.60` → `12,60`.
- W cross-check: `Retorno obtido ÷ Stake = odd exibida` (devem bater — discrepância indica leitura errada).
- Múltipla usa a **odd única exibida** — nunca produto de pernas (adversários ausentes).
- Título com `(x)`: separar corretamente jogos (`(x)`) de times (`e`); confronto = `[Time A v Time B]`.
- Seleção `Sim` nunca aparece na coluna Aposta nem na Descrição.
- `Código` sempre vazio (casa sem ID visível).
- Período do topo nunca usado como data.

---

## 15. Exemplos golden (bilhetes reais — lista "Minhas Apostas")

Lote real (screenshots + texto colado, capturado 05/07/2026; período do filtro `05/06/2026 - 05/07/2026`).

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

> **Ordem de output:** lista = mais recente no topo → TSV inverso (último card do texto = 1ª linha).
> **Data (§4):** a lista não traz data por bilhete → os goldens usam o **fallback de extração** `05/07/2026`; na prática, puxar do "Ver Cupom".
> **Pendências de amostra (não bloqueiam):** V, HW/HL, cashout encerrado, boost e bônus ainda não observados. As regras globais cobrem esses casos quando surgirem.

---

### G1 (TSV linha 1) — L · H2H · Gol mais Rápido (Argélia v Áustria)

**Input (card):** badge `Perdido` · `Odd 4.00` · `R$ 150,00` · `R$ 600,00` · título `Argélia e Áustria (x) Jordânia e Argentina` · mercado `Jogo com o Gol mais Rápido` · seleção `Argélia x Áustria` · rodapé `R$ 0,00 Retorno`.

**Verificação:** Retorno = 0 → L. Odd exibida = 4,00 (preservar, nunca 0). `(x)` separa os dois jogos; jogo apostado (verde) = Argélia v Áustria (primeiro). H2H entre os dois jogos.

**TSV esperado:**
```
05/07/2026	Futebol		BETesporte		H2H	Gol mais Rápido - [Argélia v Áustria] v [Jordânia v Argentina]	150,00	4,00	L	
```

---

### G2 (TSV linha 2) — W · H2H · Gol mais Rápido (Brasil v Japão)

**Input (card):** badge `Ganho` · `Odd 3.00` · `R$ 200,00` · `R$ 600,00` · título `Brasil (x) Japão ter o Gol + Rápido Contra o Jogo da Alemanha (x) Paraguai (LIMITE: R$1.000)` · seleção `Sim` · rodapé `R$ 600,00 Retorno`.

**Verificação:** Retorno R$ 600 > Stake R$ 200 → W. Odd = 600 ÷ 200 = 3,00 ✓. Comparação de gol mais rápido entre `[Brasil v Japão]` (apostado) e `[Alemanha v Paraguai]`. `(LIMITE: R$1.000)` = teto de pagamento (ruído). H2H.

**TSV esperado:**
```
05/07/2026	Futebol		BETesporte		H2H	Gol mais Rápido - [Brasil v Japão] v [Alemanha v Paraguai]	200,00	3,00	W	
```

---

### G3 (TSV linha 3) — W · Múltipla · TRIPLA (3 vitórias)

**Input (card):** badge `Ganho` · `Odd 12.60` · `R$ 20,00` · `R$ 252,00` · título `TRIPLA - Criciúma, Londrina e Novorizontino Vencerem seus Jogos` · seleção `Sim` · rodapé `R$ 252,00 Retorno`.

**Verificação:** Retorno R$ 252 > Stake R$ 20 → W. Odd = 252 ÷ 20 = 12,60 ✓ (bate com a exibida). `TRIPLA` → Múltipla; odd única combinada. Adversários não exibidos → descrição sem confronto, times por ` // `.

**TSV esperado:**
```
05/07/2026	Futebol		BETesporte		Múltipla	Criciúma // Londrina // Novorizontino	20,00	12,60	W	
```

---

### G4 (TSV linha 4) — L · Múltipla · DUPLA (par duplicado no lote)

**Input (card):** badge `Perdido` · `Odd 21.78` · `R$ 20,00` · `R$ 435,60` · título `DUPLA - Egito e Gana Vencerem Seus Jogos` · seleção `Sim` · rodapé `R$ 0,00 Retorno`.

**Verificação:** Retorno = 0 → L. Odd exibida = 21,78 (preservar). `DUPLA` → Múltipla. **Este card aparece duas vezes idêntico no lote** — sem ID, a assinatura (`data+stake+retorno+confronto`) colide → o sistema salva um e avisa (§3). Demonstra a limitação de dedup sem ID.

**TSV esperado:**
```
05/07/2026	Futebol		BETesporte		Múltipla	Egito // Gana	20,00	21,78	L	
```

---

### G5 (TSV linha 5) — L · Múltipla · MÚLTIPLA (4 vitórias)

**Input (card):** badge `Perdido` · `Odd 20.12` · `R$ 30,00` · `R$ 603,60` · título `MÚLTIPLA - Suíça, Marrocos, Brasil e Inglaterra Vencerem Seus Jogos` · seleção `Sim` · rodapé `R$ 0,00 Retorno`.

**Verificação:** Retorno = 0 → L. Odd exibida = 20,12 (preservar). `MÚLTIPLA` → Múltipla; 4 pernas unidas por ` // `, ordem original preservada (`MASTER_DESCRICAO_2026 §15`). Sem confronto (adversários ausentes).

**TSV esperado:**
```
05/07/2026	Futebol		BETesporte		Múltipla	Suíça // Marrocos // Brasil // Inglaterra	30,00	20,12	L	
```

---

### G6 (aberta — fora da fila de cópia) — H2H · Gol mais Rápido (EUA v Bélgica)

**Input (card):** badge `Em Aberto` · `Odd 1.85` · `R$ 50,00` · `R$ 92,50` · título `México e Inglaterra (x) EUA e Bélgica` · mercado `Jogo com o Gol mais Rápido` · seleção `EUA x Bélgica` · rodapé `Encerrar Indisponível`.

**Verificação:** `Em Aberto` → **não liquida** → `extraction_state = aberta` (Resultado vazio, fora da fila de cópia). Odd exibida = 1,85 (retorno R$ 92,50 é o **potencial**, não usar p/ derivar resultado). Jogo apostado (verde) = EUA v Bélgica (primeiro). H2H.

**TSV esperado (linha extraída, marcada `aberta`; Resultado vazio):**
```
05/07/2026	Futebol		BETesporte		H2H	Gol mais Rápido - [EUA v Bélgica] v [México v Inglaterra]	50,00	1,85		
```

---

## Feedback para a camada global / MODELO

1. **"Gol mais Rápido" classificado como `H2H` (decisão do Feca):** mercado comparativo entre **dois jogos** (qual terá o gol mais rápido). Estende o conceito de `H2H` do `MASTER_APOSTAS_2026 §5` (hoje exemplificado com entidade-vs-entidade — pilotos, jogadores) para **jogo-vs-jogo**. Sugestão: registrar essa extensão no §5/§6 do MASTER_APOSTAS se o padrão reaparecer em outras casas, para não recair em `Outros`.
2. **Mercados "N times Vencerem Seus Jogos" sem adversários:** a casa pré-monta um parlay de ML mas só mostra os times que devem vencer (sem confronto). Tratamento adotado (sem mudança de master): `Múltipla` + descrição sem confronto (`MASTER_DESCRICAO_2026 §19.10`), times por ` // `. Espelha o precedente Vitória Bet.
3. **Lista sem data por bilhete:** só há filtro de período. Documentado como pegadinha (§4/§13); fonte de data = detalhe "Ver Cupom". Sem proposta de mudança global.

---

VERSÃO: 2026
STATUS: ATIVO (v1 — 6 goldens reais, 05/07/2026; W/L confirmados em H2H e Múltipla; aberta demonstrada; V/HW/HL/cashout/boost/bônus sem amostra — não bloqueiam)
CASA: `BETesporte`
