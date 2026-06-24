# CASA_BETNACIONAL
## Camada de tradução — Betnacional → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Betnacional.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Betnacional`
- Domínio: `betnacional.bet.br`
- Locale: pt-BR · Moeda: R$ prefixo, ponto de milhar, vírgula decimal (ex.: `R$ 1.000,00`)
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** texto colado — aba **"Histórico de apostas"** com filtro **"Liquidadas"** aplicado antes de copiar. O filtro exclui apostas em aberto; só apostas liquidadas entram no texto.
- **FALLBACK:** screenshot / visão — aba **"Apostas"** (cards das últimas 24h). Usar quando o Histórico não estiver disponível.

> ⚠️ **Apostas em aberto:** aplicar sempre o filtro "Liquidadas" no Histórico antes de copiar. Sem o filtro, apostas em aberto podem mostrar `Retorno: R$0,00` — indistinguível de L no texto. O sistema já suporta `extraction_state = aberta` via mecanismo existente, mas o filtro é a solução mais limpa e confiável.

### 2.2 Tipo do bilhete declarado

A Betnacional não exibe rótulo de "Simples / Múltipla" no Histórico. Tipo inferido:
- 1 condição → categoria do mercado
- 2+ condições combinadas numa mesma aposta → `Múltipla`
- "Turbinaço CazéTV" e "Super Odds" = rótulos de promoção, não de tipo

### 2.3 Layout do bilhete (texto colado — View Histórico)

O Histórico exibe cada aposta em dois layouts possíveis:

**Layout A — promoção como cabeçalho:**
```
Super Odds | Turbinaço CazéTV         ← rótulo de promoção (ignorar para categoria)
[Descrição do mercado]                 ← pode conter confronto embutido como "Confronto: Mercado"
                                       ← ou só o mercado sem confronto explícito
DD/MM/AAAA, às HH:MM                  ← data do evento/liquidação ← USAR ESTA DATA
Odd
X.XX
Aposta
R$ XX,00
Retorno
R$ XX,00
[linha em branco]
```

**Layout B — confronto como cabeçalho:**
```
[Time A x Time B]                      ← confronto explícito (separador "x")
[Mercado - Seleção]                    ← ex.: "Vencedor - L Wessels / K Wehnelt"
DD/MM/AAAA, às HH:MM                  ← data do evento/liquidação ← USAR ESTA DATA
Odd
X.XX
Aposta
R$ XX,00
Retorno
R$ XX,00
[linha em branco]
```

**Campos extraídos:**
- `DD/MM/AAAA, às HH:MM` → Data (descartar horário)
- `Odd: X.XX` → Odd exibida (ponto decimal → converter para vírgula)
- `Aposta: R$XX,00` → Stake
- `Retorno: R$XX,00` → campo financeiro principal (positivo = W; zero = L; = Aposta = V)
- Confronto: extrair de Layout B (header) ou de "Confronto - Mercado" / "Confronto: Mercado" em Layout A

**Confronto ausente (Layout A sem prefix):** algumas apostas Turbinaço não incluem confronto no texto do Histórico (ex.: "Kai Havertz marca no segundo tempo"). AI deve inferir do contexto do lote (outros bets do mesmo evento) ou do conhecimento próprio. Se indisponível após esgotar inferência, omitir colchetes.

**Ordem do output:** Histórico exibe mais recente (topo) → mais antiga (baixo). TSV: **último no texto = 1ª linha** (cronológico crescente, mais antiga primeiro).

---

## 3. ID do bilhete

- Caso: **sem ID impresso** — a Betnacional não exibe códigos de bilhete nos views de texto (Histórico e cards de 24h)
- **Código sintético (11ª coluna interna) — OBRIGATÓRIO:** a Betnacional exibe o **horário de colocação** (`DD/MM/AAAA, às HH:MM`) em todo bilhete. Esse timestamp é estável entre reprocessamentos e único por bilhete — use-o para montar o `Código`:
  - **Formato:** `BN-DD/MM/AAAA-HH:MM-<odd exibida>` — ex.: `BN-22/06/2026-07:46-8.50`
  - **Odd no Código:** sempre a **odd exibida** (`Odd: X.XX`, 2 casas), nunca a calculada (`Retorno ÷ Aposta`). A exibida é estável; a calculada oscila em precisão e quebraria a dedup.
  - **Por quê:** sem ID, a dedup caía na descrição — que a IA reescreve a cada rodada ("[Argentina v Áustria]" ↔ "[Argentina v ?]", "Over 1,5 Gols" ↔ "Marca 2+ Gols") e às vezes muda a categoria. Cada variação virava uma duplicata. O timestamp não muda → UPSERT limpo ao reprocessar.
- **Colisão (rara):** dois bilhetes **distintos** colocados no mesmo minuto E com a mesma odd colidiriam (um sobrescreveria o outro). A odd no Código já desempata o caso comum (mesmo minuto, odds diferentes — ex.: os dois bilhetes das 07:46 com odds 8,50 e 7,00).
- Dedup: por `Código` (timestamp + odd) via `repository.py`. UPSERT silencioso ao re-processar o mesmo lote.

---

## 4. Data

- Fonte: campo `DD/MM/AAAA, às HH:MM` no Histórico = data do evento / liquidação
- **Coluna `Data`:** descartar horário → output: `DD/MM/AAAA`
- **Horário:** NÃO descartar por completo — capturar para montar o `Código` (ver §3). O horário é o identificador estável do bilhete e é o que evita duplicatas no reprocessamento.
- Múltipla: data = evento da **perna mais recente** (regra global, `MASTER_OUTPUT_2026`)

> ⚠️ Usar SEMPRE a data do evento (campo visível no Histórico). Nunca usar data de colocação ou data de processamento.

---

## 5. Status e Resultado

> ⚠️ **DISCIPLINA DE TRADUÇÃO — crítica:** nunca copiar sinal visual diretamente. Traduzir sempre para `W · L · V · HW · HL`.

**View Histórico (primário):**

| Betnacional exibe | Nosso código |
|---|---|
| `Retorno > Aposta` | W |
| `Retorno = R$0,00` (após filtro "Liquidadas") | L |
| `Retorno = Aposta` (stake devolvida) | V |
| *(meia vitória — rótulo não confirmado)* | HW |
| *(meia derrota — rótulo não confirmado)* | HL |

**View Apostas / cards (fallback):**

| Betnacional exibe | Nosso código |
|---|---|
| Ícone ✓ verde + `Ganho obtido > R$0,00` | W |
| Ícone ✗ vermelho + `Ganho obtido = R$0,00` | L |
| Ícone − (neutro) + `Ganho obtido = Valor da Aposta` | V |

Conferência financeira (segunda linha de defesa): `Retorno = 0` → L · `Retorno = Aposta` → V · `Retorno > Aposta` → W.

**Gatilho de meia-liquidação (HW/HL):**
- Rótulo explícito: aguarda amostra
- Confirmação por assinatura financeira exata: `HL → Retorno = Aposta/2` · `HW → Retorno = (Aposta/2) × (odd + 1)`
- Só em linhas asiáticas de quarto (`.25` / `.75`)

Apostas abertas → `extraction_state = aberta`.

---

## 6. Boost / promoção

- Tem boost: **sim** — "Super Odds" = odds boosted pela Betnacional
- Comportamento confirmado: `Retorno ÷ Aposta = Odd exibida` (boost já embutido no Retorno — sem discrepância)
- Regra: usar `Retorno ÷ Aposta` para W (captura boost automaticamente); usar `Odd` exibida para L/V
- "Super Odds" = rótulo de promoção; ignorar para classificação de mercado

---

## 7. Cashout

- Tem cashout: **não confirmado** — aguarda amostra
- Regra global: `Odd = Cashout ÷ Stake` (resultado = W); se `Cashout = Stake` → resultado `V`.

<!-- TODO: confirmar localizador e rótulo visual do cashout encerrado. -->

---

## 8. Bônus

- Tem bônus / freebet: **não confirmado** — aguarda amostra
- **Política:** pendente até ter amostra real.

<!-- TODO: confirmar se há apostas de bônus e como identificá-las. -->

---

## 9. Mapa de mercados (Betnacional → `Aposta` global)

> Mercados da Betnacional estão em português do Brasil.
> A classificação segue `MASTER_APOSTAS_2026 §3` (27 categorias).

| Betnacional exibe | Aposta global | Status |
|---|---|---|
| `Ambos times marcam` · `Ambas equipes marcam` (2ºT ou partida) | Ambas Marcam | ✓ confirmado |
| `[Jogador] marca a qualquer momento` | Anytime | aguarda amostra |
| (aguarda amostra) | Assistência | aguarda amostra |
| `Cartão Vermelho Sim/Não - Sim` · `Cartão Amarelo Sim/Não - Sim` | Cartões | ✓ confirmado |
| (aguarda amostra) | Chutes | aguarda amostra |
| `[Jogador] X+ Chutes ao Gol na Partida` | Chutes no Gol | ✓ confirmado (via bets combinadas) |
| (aguarda amostra — Baseball) | Corridas | aguarda amostra |
| (aguarda amostra) | Desarmes | aguarda amostra |
| (aguarda amostra) | DNB | aguarda amostra |
| (aguarda amostra — Basquete) | Double-Double | aguarda amostra |
| (aguarda amostra) | Dupla Chance | aguarda amostra |
| (aguarda amostra — E-Sports) | E-Sports Props | aguarda amostra |
| `X+ Escanteios Para Cada Time` · `Escanteios Mais/Menos` | Escanteios | ✓ confirmado (via bets combinadas) |
| (aguarda amostra — Tênis) | Games | aguarda amostra |
| `[Time] marca X+ gols` · `Total de gols Mais/Menos X` | Gols | ✓ confirmado |
| (aguarda amostra — comparativo) | H2H | aguarda amostra |
| (aguarda amostra) | Handicap | aguarda amostra |
| (aguarda amostra) | Impedimentos | aguarda amostra |
| (aguarda amostra — NFL) | Jardas | aguarda amostra |
| (aguarda amostra — Dardos) | Legs | aguarda amostra |
| `Vencedor - [Time/Jogador]` | ML | ✓ confirmado |
| 2+ condições independentes combinadas numa aposta (Turbinaço · Bet Builder) | Múltipla | ✓ confirmado |
| Outros mercados sem categoria específica | Outras ⚠️ | fallback |
| `[Jogador] marca OU dá assistência` · `[Jogador] X+ Defesas na Partida` · `[Jogador] marca no [tempo]` | Player Props | ✓ confirmado |
| (aguarda amostra — Tênis) | Sets | aguarda amostra |
| `[Time] Marca em Ambos os Tempos` | Team Props | ✓ confirmado |
| (aguarda amostra — Basquete) | Triplo-Duplo | aguarda amostra |

**Notas de reconstrução:**
- Confronto: separador `x` → normalizar para `v` (sem "s") com colchetes: `[Time A v Time B]`
- Abreviações de time: `HOL → Holanda`, `SUE → Suécia`, `Ale → Alemanha`, `CdM → Costa do Marfim`, `Hol → Holanda`, `Sué → Suécia`. Expandir sempre.
- Rótulo `- CazeTV` após confronto em View 1 (cards): ignorar
- Rótulo `(BN) TURBINACO DD/MM [Team]` em View 1: ignorar
- `[Jogador] marca no segundo tempo` = Player Props (tempo restrito — não é Anytime)
- `[Time] Marca em Ambos os Tempos` = Team Props (padrão global confirmado em KingPanda)
- Múltipla via Turbinaço/Bet Builder: descrever condições separadas por ` + ` no campo Descrição
- Mercado sem categoria → `Outras ⚠️` + registrar no §Feedback

---

## 10. Stake

- Localização (Histórico): campo `Aposta: R$ XX,00`
- Localização (cards): campo `Valor da Aposta: R$ XX,00`
- Formato: pt-BR — `R$ 50,00` (espaço após R$, vírgula decimal, ponto de milhar)
- Normalização: remover `R$ ` e espaços → manter valor com vírgula decimal
- **`Mais de X` / `Menos de X` → `Over X` / `Under X`**: padrão global — ver `MASTER_DESCRICAO_2026 §11`. A Betnacional exibe em português; a saída TSV é sempre em inglês.

---

## 11. Odds

> **Campo financeiro principal (Histórico): `Retorno`** — retorno bruto total = stake × odd para W.
> **Campo financeiro principal (cards): `Ganho obtido`** — mesmo significado.

- Localização Histórico: campo `Retorno: R$ XX,00`
- Localização cards: campo `Ganho obtido: R$ XX,00`
- Campo de odd exibida: `Odd: X.XX` (ponto decimal en-US → converter para vírgula)

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Retorno ÷ Aposta` (deve coincidir com `Odd` exibida) |
| L | `Odd` exibida — nunca `0,00` |
| V | `Odd` exibida — nunca `1,00` |
| HW | `Odd` exibida (aguarda amostra) |
| HL | `Odd` exibida (aguarda amostra) |
| Cashout | `Odd = Cashout ÷ Aposta` (aguarda amostra) |

**Múltiplas (Turbinaço / Bet Builder):** usar Odd exibida (campo `Odd` no Histórico) para L; `Retorno ÷ Aposta` para W.

> ⚠️ Odd em L nunca vira `0,00`; em V nunca vira `1,00`. Usar sempre `Odd` exibida.
> Precisão: preservar — não truncar nem arredondar (`MASTER_RESULTADO_2026`).

---

## 12. Ruído a ignorar

`Super Odds` (rótulo de promoção) · `Turbinaço CazéTV` (rótulo de promoção) · `- CazeTV` (sufixo no confronto em cards) · `(BN) TURBINACO DD/MM [Team]` (label de canal em cards) · `Compartilhar` (botão) · ícones de resultado (✓ / ✗ / −) · `Histórico de apostas` (título da aba) · `Filtro` / `Filtro 1` (botão de filtro) · `Odd` / `Aposta` / `Retorno` (labels de campo — os valores vêm na linha seguinte)

---

## 13. Pegadinhas (resumo rápido)

- **Retorno ≠ lucro:** `Retorno` = retorno total (stake + lucro). Odd = `Retorno ÷ Aposta` — nunca `(Retorno - Aposta) ÷ Aposta`.
- **Confronto ausente em Layout A (Turbinaço sem prefixo):** "Kai Havertz marca no segundo tempo" não inclui confronto no Histórico. Inferir de outros bets do lote ou de conhecimento geral. Não inventar se incerto.
- **Abreviações de confronto:** `HOL x SUE` / `Hol x Sué` / `Ale x CdM` → expandir para nomes completos antes de normalizar para `[Time A v Time B]`.
- **Separador de confronto é "x" (não "v"):** normalizar sempre: "Holanda x Suécia" → "[Holanda v Suécia]".
- **Odd usa ponto decimal:** campo `Odd: X.XX` usa en-US. Converter para vírgula: `4.50` → `4,50`.
- **Valores de Aposta e Retorno:** campo `R$ XX,00` tem espaço entre `R$` e o número. Remover ao extrair.
- **V detectado por `Retorno = Aposta`:** não há rótulo explícito de "Void" confirmado no Histórico. Usar assinatura financeira.
- **Filtro "Liquidadas" é obrigatório antes de copiar:** sem filtro, `Retorno = 0` pode ser apostas em aberto (indistinguível de L no texto).
- **Rótulo "Turbinaço CazéTV" e "Super Odds" não alteram categoria:** indicam promoção; a categoria vem do mercado descrito, não do rótulo.
- **Múltipla via condições combinadas:** "Ambos Marcam + 2.5+ Escanteios + 1.5+ Cartões" em uma única aposta = `Múltipla`, não categorias separadas.
- **Código sintético do timestamp é obrigatório (§3):** sem ID impresso, o horário de colocação (`às HH:MM`) é o que distingue/identifica o bilhete. Sempre montar `Código = BN-DD/MM/AAAA-HH:MM-<odd exibida>`. Esquecer o Código faz a dedup cair na descrição e gerar duplicatas ao reprocessar.

---

## 14. Validações específicas

**Transversais (todas as casas):**
- Código de resultado é um dos oficiais (`W / L / V / HW / HL`) — nunca sinal visual cru.
- Odd preservada em L/HL/V: nunca `0,00`, nunca metade, nunca `1,00`.
- Coluna `Esporte` contém o esporte, nunca a liga.
- Jogador normalizado: sem `Sobrenome, Nome`; sem `[colchetes]` residuais na descrição.
- Nº de linhas = nº de bets detectados.

**Específicas da Betnacional:**
- Odd convertida de ponto para vírgula: `4.50` → `4,50`.
- Confronto normalizado: `x` → `v`; abreviações expandidas antes da conversão.
- W cross-check: `Retorno ÷ Aposta = Odd exibida` (devem bater — discrepância indica leitura errada).
- Rótulos de promoção não aparecem na coluna Aposta nem na Descrição.

---

## 15. Exemplos golden (bilhetes reais — Histórico de apostas, filtro Liquidadas)

Lote de 20/06/2026 (View Histórico). Apostas filtradas com "Liquidadas".

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado \t Código`

> O `Código` (11ª coluna interna) é sintetizado do timestamp + odd exibida (§3): `BN-DD/MM/AAAA-HH:MM-<odd>`.

**Ordem de output:** texto do Histórico = mais recente primeiro. TSV: inverso (mais antiga primeiro).

---

### G1 (TSV linha 1) — V · ML · D S Stricker/A Hunziker x L Wessels/K Wehnelt

**Input (texto Histórico):**
```
D S Stricker/A Hunziker x L Wessels/K Wehnelt
Vencedor - L Wessels / K Wehnelt
20/06/2026, às 08:14
Odd
2.55
Aposta
R$ 250,00
Retorno
R$ 250,00
```

**Verificação:** Retorno = R$250 = Aposta → V. Odd exibida = 2,55 (preservar).

**TSV esperado:**
```
20/06/2026	Padel		Betnacional		ML	L Wessels/K Wehnelt [D S Stricker/A Hunziker v L Wessels/K Wehnelt]	250,00	2,55	V	BN-20/06/2026-08:14-2.55
```

---

### G2 (TSV linha 2) — L · Múltipla · Hol x Sué (3 condições)

**Input (texto Histórico):**
```
Turbinaço CazéTV
Hol x Sué - Ambos Os Times Marcam, 2.5+ Escanteios Para Cada Time E 1.5+ Cartões Para Cada Time
20/06/2026, às 08:32
Odd
14.00
Aposta
R$ 50,00
Retorno
R$ 0,00
```

**Verificação:** Retorno = 0 → L. Confronto "Hol x Sué" = Holanda x Suécia → [Holanda v Suécia]. Odd exibida = 14,00 (preservar).

**TSV esperado:**
```
20/06/2026	Futebol		Betnacional		Múltipla	Ambas Marcam + Over 2,5 Escanteios/Time + Over 1,5 Cartões/Time [Holanda v Suécia]	50,00	14,00	L	BN-20/06/2026-08:32-14.00
```

---

### G3 (TSV linha 3) — W · Player Props · Cody Gakpo (confronto ausente no texto)

**Input (texto Histórico):**
```
Super Odds
Cody Gakpo marca OU dá assistência em um gol
20/06/2026, às 09:37
Odd
2.20
Aposta
R$ 50,00
Retorno
R$ 110,00
```

**Verificação:** Retorno R$110 > Aposta R$50 → W. Odd = 110 ÷ 50 = 2,20 ✓. Confronto ausente no texto — inferir de outros bets do lote: Holanda vs Suécia.

**TSV esperado:**
```
20/06/2026	Futebol		Betnacional		Player Props	Cody Gakpo [Holanda v Suécia]	50,00	2,20	W	BN-20/06/2026-09:37-2.20
```

---

### G4 (TSV linha 4) — W · Cartões · Tunísia x Japão

**Input (texto Histórico):**
```
Tunísia x Japão
Cartão Vermelho Sim/Não - Sim
20/06/2026, às 13:11
Odd
6.50
Aposta
R$ 25,00
Retorno
R$ 162,50
```

**Verificação:** Retorno R$162,50 > Aposta R$25 → W. Odd = 162,50 ÷ 25 = 6,50 ✓.

**TSV esperado:**
```
20/06/2026	Futebol		Betnacional		Cartões	Cartão Vermelho - Sim [Tunísia v Japão]	25,00	6,50	W	BN-20/06/2026-13:11-6.50
```

---

### G5 (TSV linha 5) — W · Ambas Marcam · HOL x SUE 2ºT

**Input (texto Histórico):**
```
Turbinaço CazéTV
HOL x SUE: Ambos times marcam no segundo tempo
20/06/2026, às 14:56
Odd
4.10
Aposta
R$ 50,00
Retorno
R$ 205,00
```

**Verificação:** Retorno R$205 > Aposta R$50 → W. Odd = 205 ÷ 50 = 4,10 ✓. Confronto "HOL x SUE" → [Holanda v Suécia].

**TSV esperado:**
```
20/06/2026	Futebol		Betnacional		Ambas Marcam	Ambas Marcam 2ºT [Holanda v Suécia]	50,00	4,10	W	BN-20/06/2026-14:56-4.10
```

---

### G6 (TSV linha 6) — L · Player Props · Kai Havertz 2ºT (confronto ausente no texto)

**Input (texto Histórico):**
```
Turbinaço CazéTV
Kai Havertz marca no segundo tempo
20/06/2026, às 17:53
Odd
4.50
Aposta
R$ 50,00
Retorno
R$ 0,00
```

**Verificação:** Retorno = 0 → L. Odd exibida = 4,50 (preservar). "Marca no segundo tempo" = Player Props (não Anytime). Confronto ausente — inferir: Alemanha x Costa do Marfim (Kai Havertz joga pela Alemanha; outros bets do lote confirmam o jogo).

**TSV esperado:**
```
20/06/2026	Futebol		Betnacional		Player Props	Kai Havertz [Alemanha v Costa do Marfim]	50,00	4,50	L	BN-20/06/2026-17:53-4.50
```

---

### G7 (TSV linha 7) — W · Player Props · Vozinha (confronto embutido na descrição)

**Input (texto Histórico):**
```
Super Odds
Uruguai x Cabo Verde - Vozinha 6+ Defesas na Partida
20/06/2026, às 23:29
Odd
7.00
Aposta
R$ 50,00
Retorno
R$ 350,00
```

**Verificação:** Retorno R$350 > Aposta R$50 → W. Odd = 350 ÷ 50 = 7,00 ✓. Confronto embutido: "Uruguai x Cabo Verde" → [Uruguai v Cabo Verde]. Jogador: "Vozinha". Estatística: defesas (goalkeeper saves) → Player Props.

**TSV esperado:**
```
20/06/2026	Futebol		Betnacional		Player Props	Vozinha [Uruguai v Cabo Verde]	50,00	7,00	W	BN-20/06/2026-23:29-7.00
```

---

## Feedback para a camada global / MODELO

1. **Apostas abertas no Histórico:** sem filtro "Liquidadas", `Retorno = R$0,00` pode ser aposta aberta ou L — indistinguível. Solução documentada: usar filtro antes de copiar. Nenhuma mudança nos masters necessária.
2. **Confronto ausente em Layout A (Turbinaço sem prefixo):** limitação de formato do Histórico. O AI infere do contexto; documentado como pegadinha. Sem proposta de mudança global.
3. **"Marca no segundo tempo" vs Anytime:** Player Props foi escolhido por ser tempo-restrito. Verificar se o MASTER_APOSTAS §4 deve listar "Marcar no segundo/primeiro tempo" como sinônimo de Player Props (atualmente não listado explicitamente).

---

VERSÃO: 2026
STATUS: ATIVO (v1 — 7 goldens reais, 21/06/2026)
CASA: `Betnacional`
