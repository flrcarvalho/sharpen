# CASA_JOGODEOURO
## Camada de tradução — `Jogo de Ouro` → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Jogo de Ouro.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Jogo de Ouro`
- Domínio: `jogodeouro.bet.br`
- Locale: pt-BR (rótulos em português)
- Formato numérico: **en-US** — ponto decimal em dinheiro e odds (ex.: `R$30.00`, `3.50`) → converter para vírgula (`30,00`, `3,50`)
- Moeda: `R$`
- `Parceiro` / `Tipster`: preenchidos pelo app

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO:** screenshot — bilhetes exibidos em cards (grid de duas colunas)
- **FALLBACK:** texto colado — aguarda confirmação de que o site permite copiar o histórico como texto

> A casa oferece abas de filtro no topo: `Aberto · Processado · Ganhou · Perdida · Cashout`. Extrair apenas bilhetes resolvidos (`Processado` / `Ganhou` / `Perdida` / `Cashout`); ignorar `Aberto`.

### 2.2 Tipo do bilhete declarado

- Badge **`CA`** (amarelo, canto superior esquerdo do card) = **Criar Aposta** (Bet Builder intra-jogo) → bilhete inteiro é `Múltipla`.
- Card sem badge `CA` e com uma única seleção = Simples (usar a categoria do mercado).
- Numa `Criar Aposta`, as seleções aparecem como itens com marcador (bullet) ligados: `[mercado] → [seleção] ✓/✗`.

### 2.3 Anatomia do bilhete (card)

**Bilhete simples:**
```
[Confronto]                              [GANHOU / VENCIDO | PERDIDO]   ← header colorido
[Seleção]  ✓/✗                           [odd_original] >> [odd_final]
[Badge: ODDS DE OURO]
[Mercado]
[Confronto]                              [placar final, ex.: 3:2]
DD/MM • HH:MM                            ← início do evento
Cotações totais                          [ODD_FINAL]
Valor total de aposta                    R$[STAKE]
Ganho total                              R$[RETORNO]   ← só em W; vazio em L
Tipo de Dispositivo Usado               Tipo de Dispositivo: Desktop
DD/MM • HH:MM   ID: [número]            ← colocação + ID
```

**Bilhete Criar Aposta (múltipla):**
```
[Confronto]                              [GANHOU / VENCIDO | PERDIDO]
[CA] ✓                                   [odd_original] >> [odd_final]
[Confronto]                              [placar final]
• [Mercado 1]
  [Seleção 1] ✓/✗
• [Mercado 2]
  [Seleção 2] ✓/✗
[Badge: ODDS DE OURO]
DD/MM • HH:MM                            ← início do evento
Cotações totais                          [ODD_FINAL]
Valor total de aposta                    R$[STAKE]
Ganho total                              R$[RETORNO]
...
DD/MM • HH:MM   ID: [número]
```

**Ordem de output:** o grid exibe do mais recente (topo-esquerda) ao mais antigo, lendo esquerda→direita, cima→baixo. O TSV deve sair na ordem **inversa**: último card na ordem de leitura = primeira linha do TSV. → `reverse=True`.

---

## 3. ID do bilhete

- Caso: **visível**
- Formato: numérico, ~10 dígitos (ex.: `5093265488`, `5093260948`)
- Localização: última linha do card, após a data de colocação — `ID: [número]`
- Nunca vai no output do usuário — serve só para dedup e validação (11ª coluna interna).

---

## 4. Data

Cada card contém **duas** ocorrências de `DD/MM • HH:MM`:

| Ocorrência | Posição no card | Usar? |
|---|---|---|
| **Data do evento** | Abaixo do badge `ODDS DE OURO`, acima de `Cotações totais` | **Sim** |
| **Data de colocação** | Última linha, imediatamente antes de `ID:` | **Não** |

- Formato fonte: `DD/MM • HH:MM` sem ano → inferir ano de `data_referencia`; output: `DD/MM/AAAA`.
- Múltipla (Criar Aposta): como todas as seleções são do mesmo jogo, a data do evento é única.
- Múltipla multi-jogo (se surgir): data = perna mais recente (regra global, `MASTER_OUTPUT_2026`).

> ⚠️ Se `DD/MM` do evento for maior que `DD/MM` de `data_referencia`, pode ser ano anterior — sinalizar nas Notas Críticas.

---

## 5. Status e Resultado

| Jogo de Ouro exibe | Nosso código |
|---|---|
| `GANHOU / VENCIDO` (header verde) | W |
| `PERDIDO` (header vermelho) | L |
| `Aberto` (aba) | **IGNORAR** (não extrair) |
| (aba `Cashout` — rótulo de card aguarda amostra) | W ou V (ver regra global de cashout) |
| (sem amostra) | V |
| (sem amostra) | HW |
| (sem amostra) | HL |

Conferência financeira (segunda linha de defesa): `Ganho total` vazio/`0` → L · `Ganho total = Stake` → V · `Ganho total > Stake` → W.

> ⚠️ Em bilhetes `PERDIDO`, o campo `Ganho total` aparece **vazio** (sem valor). Nunca inferir retorno para L.

**Gatilho de meia-liquidação (HW/HL):** aguarda amostra. Usar assinatura financeira: `HL → Ganho total = stake/2` · `HW → Ganho total = (stake/2) × (odd + 1)`.

Apostas abertas → `extraction_state = aberta` — não incluir no TSV.

<!-- TODO: confirmar rótulo exato do card na aba Cashout e de V/HW/HL com amostras reais -->

---

## 6. Boost / promoção

- Tem boost: **sim** — a Jogo de Ouro turbina odds regularmente.
- Localizador visual: `[odd_original] >> [odd_final]` no canto superior direito do card + badge verde **`ODDS DE OURO`**.
- `Cotações totais` sempre reflete a odd **final (boosted)**.
- Para W: `Ganho total ÷ Stake` já captura o boost automaticamente.
- Para L: usar `Cotações totais` diretamente (Ganho total vazio).

> ⚠️ A odd `[odd_original]` (antes do `>>`) é a odd pré-boost — **ignorar**. Usar sempre a odd final (`Cotações totais`).

---

## 7. Cashout

- Tem cashout: **sim** — aba `Cashout` existe na interface.
- Localizador: rótulo do card na aba Cashout aguarda amostra.
- Regra global: `Odd = Cashout ÷ Stake`; se `Cashout = Stake` → resultado `V`.

<!-- TODO: confirmar rótulo visual do card encerrado por cashout e onde aparece o valor recebido. -->

---

## 8. Bônus

- Tem bônus: **aguarda amostra**
- Localizador: aguarda confirmação.

<!-- TODO: confirmar se há freebets ou apostas de bônus identificáveis no histórico. -->

---

## 9. Mapa de mercados (Jogo de Ouro → `Aposta` global)

Fonte de verdade das categorias: `MASTER_APOSTAS_2026 §3`. Este mapa lista **apenas** os mercados já confirmados num bilhete real desta casa (camada fina) — a taxonomia completa vive no MASTER e **não** se reescreve aqui.

| Jogo de Ouro exibe | Aposta global | Status |
|---|---|---|
| `Total de escanteios` · `1º tempo - total de escanteios` | Escanteios | ✓ confirmado |
| `Total de gols` | Gols | ✓ confirmado |
| `Vencedor do encontro` | ML | ✓ confirmado |
| `Criar Aposta` (badge `CA`, 2+ seleções) | Múltipla | ✓ confirmado |
| (mercado não mapeado) | Outros | ✓ fallback |

**Notas de reconstrução:**
- Separador de times: `vs.` (ex.: `Noruega vs. Senegal`) → normalizar para `[Noruega v Senegal]` (lowercase `v`, colchetes).
- Odd e dinheiro em en-US (ponto decimal): `3.50` → `3,50`; `R$30.00` → `30,00`.
- **`Mais de X` / `Menos de X` → `Over X` / `Under X`**: padrão global — ver `MASTER_DESCRICAO_2026 §11`. A casa exibe em português; a saída TSV é sempre em inglês.
- Recorte temporal de mercado: `1º tempo - total de escanteios` → manter o recorte na descrição (`Escanteios 1ºT`).
- Placar final do jogo (`3:2`) ao lado do confronto → ruído, ignorar.
- Descrição de Criar Aposta (Múltipla): usar ` // ` como separador das seleções normalizadas, seguido de `[Confronto]` no final (o card liga as seleções do mesmo jogo → **traduzir para ` // `**, o separador oficial de seleção do sistema; `MASTER_DESCRICAO §16`).

---

## 10. Stake

- Localização: campo `Valor total de aposta R$XX.XX`.
- Formato fonte: **en-US** — ponto decimal (ex.: `R$30.00`, `R$50.00`).
- Normalizar: remover `R$`, converter ponto decimal para vírgula (`30,00`).

---

## 11. Odds

- Campo principal: `Cotações totais` (en-US, ponto decimal) = odd final boosted.

| Resultado | Regra da odd |
|---|---|
| W | `Odd = Ganho total ÷ Stake` (captura o boost) |
| L | `Cotações totais` **exibida** → converter ponto para vírgula — nunca `0,00` |
| V | `Cotações totais` exibida — nunca `1,00` |
| HW | `Cotações totais` exibida — nunca metade |
| HL | `Cotações totais` exibida — nunca metade |
| Cashout (≠ stake) | `Odd = Cashout ÷ Stake` |

> ⚠️ A odd antes do `>>` (`[odd_original]`) é decorativa/pré-boost — ignorar. Para W a odd é `Ganho total ÷ Stake` (já boosted). A odd exibida em `Cotações totais` é a final; conferir cruzando com `Ganho total ÷ Stake` em W.

---

## 12. Ruído a ignorar

`Aberto` (aba — ignorar bilhetes em aberto) · Badge `ODDS DE OURO` (branding de boost) · `[odd_original] >>` (odd pré-boost) · Placar final do jogo (`3:2`) · `Tipo de Dispositivo Usado: Tipo de Dispositivo: Desktop` · Ícone de compartilhar (↗) · `DD/MM • HH:MM` da linha do `ID:` (colocação — usar só a data do evento) · Marcadores ✓ (verde) / ✗ (vermelho) das seleções

---

## 13. Pegadinhas (resumo rápido)

- **Decimal en-US:** `R$30.00`, `3.50`, `1.70` usam **ponto** decimal. Converter para vírgula. Não confundir com pt-BR.
- **Badge `CA` = Criar Aposta = Múltipla:** card com `CA` e 2+ seleções é sempre `Múltipla`, não bets separadas.
- **`Ganho total` é retorno bruto (só em W):** em `PERDIDO` o campo fica vazio — nunca usar para inferir retorno em L.
- **`ODDS DE OURO` ≠ campo de cálculo:** é branding de boost. A odd final está em `Cotações totais`.
- **Odd antes do `>>` é pré-boost:** ignorar; usar a odd final.
- **Duas datas no card:** evento (acima de `Cotações totais`) vs colocação (linha do `ID:`). Usar o evento.
- **Placar final (`3:2`) é ruído:** não é mercado nem odd.
- **Abas misturam estados:** extrair só `Processado`/`Ganhou`/`Perdida`/`Cashout`; ignorar `Aberto`.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` (FASE 7 — Validação) + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes). Não duplicar aqui.

**Específicas da Jogo de Ouro:**
- Nenhum bilhete da aba `Aberto` deve aparecer no output.
- `Ganho total ÷ Stake = Cotações totais` para bets W (validação cruzada do boost).
- Separador de times no output: `v` — nunca `vs.` nem `x`.
- Odd e stake sempre com vírgula decimal (en-US → pt-BR).
- Card com badge `CA` → `Aposta = Múltipla`.

---

## 15. Exemplos golden (bilhetes reais)

> Amostra de 22/06/2026. Ordem: último card na ordem de leitura = primeira linha do TSV (mais antigo = primeira linha).
> Tipster e Parceiro deixados em branco (preenchidos pelo app).

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

---

### G1 — L · Gols (simples) · ID 5093260948

**Bilhete (card direito, PERDIDO):**
```
Noruega vs. Senegal                    PERDIDO
Menos de 3.5  ✗                        1.40 >> 1.70
ODDS DE OURO
Total de gols
Noruega vs. Senegal                    3:2
22/06 • 21:00
Cotações totais                        1.70
Valor total de aposta                  R$50.00
Ganho total
Tipo de Dispositivo Usado              Tipo de Dispositivo: Desktop
22/06 • 20:48   ID: 5093260948
```

**Odd:** `1,70` (lida de `Cotações totais` — bet PERDIDO; o jogo terminou 3:2 = 5 gols > 3,5 → Under perdeu)

**TSV esperado:**
```
22/06/2026	Futebol		Jogo de Ouro		Gols	Under 3,5 Gols [Noruega v Senegal]	50,00	1,70	L
```

---

### G2 — W · Múltipla (Criar Aposta: ML + Escanteios 1ºT) · ID 5093265488

**Bilhete (card esquerdo, GANHOU / VENCIDO):**
```
Noruega vs. Senegal                    GANHOU / VENCIDO
CA  ✓                                  3.33 >> 3.50
Noruega vs. Senegal                    3:2
• Vencedor do encontro
  Noruega  ✓
• 1º tempo - total de escanteios
  Mais de 3.5  ✓
ODDS DE OURO
22/06 • 21:00
Cotações totais                        3.50
Valor total de aposta                  R$30.00
Ganho total                            R$105.00
Tipo de Dispositivo Usado              Tipo de Dispositivo: Desktop
22/06 • 20:49   ID: 5093265488
```

**Odd:** `Ganho total ÷ Stake = 105,00 ÷ 30,00 = 3,50` ✓ (= `Cotações totais`, boost final)

**TSV esperado:**
```
22/06/2026	Futebol		Jogo de Ouro		Múltipla	Noruega Ganhar // Over 3,5 Escanteios 1ºT [Noruega v Senegal]	30,00	3,50	W
```

---

## Feedback para a camada global

1. **Criar Aposta** (Bet Builder intra-jogo): a Jogo de Ouro marca com o badge `CA` e combina seleções do mesmo jogo. Sinal discriminante = badge `CA` + 2+ seleções com bullet. Padrão equivalente ao "Criador de apostas" da KingPanda e "Criar Aposta" da Bet365 → classificado como `Múltipla`.
2. **Boost `ODDS DE OURO`:** formato `[orig] >> [final]` + badge verde, idêntico em estrutura ao `>>` da KingPanda. `Cotações totais` = odd final. Documentado em §6 e §11.
3. **Recorte temporal de mercado** (`1º tempo - total de escanteios`): mantido na descrição como `Escanteios 1ºT`. Avaliar se o `MASTER_DESCRICAO` deve padronizar sufixos de recorte (`1ºT` / `2ºT`) globalmente.

---

VERSÃO: 2026
STATUS: ATIVA
CASA: `Jogo de Ouro`
ATUALIZADO: 2026-06-22 (sessão 43)
