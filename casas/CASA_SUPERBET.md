# CASA_SUPERBET
## Camada de tradução — Superbet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Superbet.
> Toda regra de estrutura, taxonomia, descrição, resultado e cálculo de odd vive nos masters globais.
> O arquivo de casa **traduz** a Superbet para a língua global; **nunca redefine** regra global.
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Superbet`
- Locale: pt-BR · Moeda: R$ (exibida como **sufixo**: `100,00 R$`) · Decimal: vírgula
- `Parceiro` / `Tipster`: **não preenchidos na extração**. Vêm da camada de app (Parceiro = workspace; Tipster = Telegram). O extrator deixa vazios.

---

## 2. Modo de ingestão e layout

A Superbet entra por **três formas**. O cálculo é o mesmo; muda só de onde os campos vêm. Todas começam com o marcador **`[Código: XXXX-XXXXXX]`** (código exato do DOM/API, sem OCR).

### Modo A — TEXTO ROTULADO (scanner/API, PADRÃO)

Formato limpo, campos rotulados, um bloco por bilhete. Exemplo real:

```
[Código: 8909-QNRSXW]
Data: 03/07/2026
Apostado em: 03/07/2026
Stake: 100,00
Odd total: 2,04
Status: win · retorno 204,00
Seleções (1):
  • 03/07/2026 · Argentina — Cabo Verde · Total de Cartões: Menos de 2.5 + Argentina - Total de Cartões: Menos de 2.5 @ 1,8
```

**Mapa de campos** (o scanner já entrega tudo normalizado — vírgula, precisão cheia, boost embutido):

| Campo | Significado / uso |
|---|---|
| **`Data:`** | data do **EVENTO** (perna mais recente) → **é a data do bilhete** (col 1). **Usar esta.** |
| **`Apostado em:`** | data de **criação** → **ignorar** na saída (contexto só). |
| **`Stake:`** | stake já **cheio** (inclui freebet, se houver). |
| **`Freebet incluído: X`** | parte grátis, **já embutida no Stake** → não somar nem subtrair (ver §8). |
| **`Odd total:`** | odd **efetiva**, precisão completa, **já com boost** em win (= `retorno ÷ stake`) → **usar direto** (ver §11). |
| **`Status:`** | `lost`→**L** · `win`→**W** · `cashout`→ §7 (retorno=stake → **V**; ≠ → **W**, odd=`retorno÷stake`). `retorno` = valor pago. |
| **`Seleções (N)`** | pernas; cada linha `data · Time A — Time B · [Super Odds — ][mercado —] seleção @ odd`. |

- **Bet-builder (`CRIAR APOSTA` / `DICAS DE APOSTA`):** vem como **1 seleção** com os mercados juntados por **`+`** (`Total de Cartões: Menos de 2.5 + Argentina - Total de Cartões: Menos de 2.5`) → conta como **≥2 seleções = `Múltipla`** (ver §9), Descrição = os mercados concatenados.
- **Ruído a ignorar:** rótulos de produto (`Super Odds`, `CRIAR APOSTA`, `DICAS DE APOSTA`, `Longo Prazo - …`) e o `Apostado em:`.

### Modo A-cru — TEXTO do robô clique/DOM (fallback)

Se a captura pela API falhar, o robô cai no scrape cru do DOM. Bloco por perna, de cima para baixo: `país/região` → `liga` → `data da seleção` → `time casa` → `time visitante` → placar → `linha do mercado` → `mercado` → `odd`; depois o rodapé: `ID` repetido → criação (`DD DE MMM. DE AAAA`) → `ODDS TOTAIS` → `APOSTA` → [`SUPERTURBO X%`] → [`PRÊMIO`/`SACADO`/`REEMBOLSO`] → [`APOSTA GRÁTIS`] → `STATUS` (`Perdido`/`Ganhou`/`Sacado`/`Reembolso`). **Odds vêm com PONTO** (`17.53`) → converter p/ vírgula. Boost: em W a odd é `PRÊMIO÷Stake`, não `ODDS TOTAIS`.

### Modo B — PRINT (imagem, ainda suportado)

Cada aposta é um **bloco único**: card(s) de seleção (liga + data/hora + confronto + placar + mercado + odd + ✓/✗) → ID → `ODDS TOTAIS` → `APOSTA` → [boost] → `PRÊMIO`/`REEMBOLSO`/`SACADO` → `STATUS` → cabeçalho de criação. No print o ID só aparece no **detalhe** (ver §3).

### Regras comuns às três formas

- Interpretar cada bloco **completo**; nunca misturar pernas de blocos diferentes.
- **Ordenação de output:** manter a ordem em que veio (1º bloco = 1ª linha no TSV). NÃO inverter.

---

## 3. ID do bilhete (chave de deduplicação)

- Formato: `XXXX-XXXXXX` (alfanumérico). Ex.: `890C-QDPCUD`, `898K-7Y2U4H`.
- Regra: 1 ID = 1 aposta = 1 linha.
- **Modo TEXTO:** o ID vem **sempre** no marcador `[Código: XXXX-XXXXXX]` no topo do bloco (e repetido no rodapé). Exato do DOM — nunca falta. A dedup por ID é direta e à prova de falha; dois bilhetes de conteúdo idêntico com IDs distintos (ex.: `8901-QI2PSS` vs `8901-QI2PS1`) são **sempre** 2 linhas.
- **Modo PRINT — pegadinha:** o ID só aparece no **detalhe**, não na lista. Sem ID na imagem, dedup por assinatura derivada = `data_criação + stake + odds_totais + confronto`; abrir o detalhe (pegar o ID real) só nos candidatos que a assinatura marcar como novos.
- Existe também um hash UUID minúsculo no rodapé de cada bilhete (ex.: `33048385-a4e1-4ac8-...`). Possível chave alternativa, mas **não confirmado** se é estável por aposta ou por render/sessão. Não usar até confirmar.
- Nunca duplicar, agrupar ou ignorar ID válido.

---

## 4. Data

> **Modo rotulado (scanner):** já resolvido — use o campo **`Data:`** (evento/perna mais recente); **ignore** `Apostado em:` (criação). O resto desta seção vale para os modos cru/print.

A Superbet exibe **duas** datas. Não confundir.

- **Cabeçalho do bloco** (ex.: `12 DE JUN. DE 2026 — 09:31`) = data de **criação** do bilhete. Não usar como data da aposta. Só fallback absoluto se nenhuma seleção tiver data interpretável.
- **Data dentro de cada seleção** = a que vale. Formatos vistos:
  - Relativa: `Hoje, 13:00` · `Ontem, 20:15` · `Amanhã, 18:00`
  - Absoluta com dia da semana: `Qua 10. Jun, 19:40` · `Seg 1. Jun, 14:30` · `Dom 31. Mai, 15:30`
  - Ao vivo: `1º Tempo 45+3'` (sem data própria → usar as outras pernas)

Datas relativas (Hoje/Ontem/Amanhã) resolvem contra a **data de referência da captura** (timestamp do print), fornecida pela camada de app — **nunca** contra o cabeçalho do bilhete nem contra a data de processamento.

> ⚠️ Pipeline assíncrono (Batch API): a data de referência precisa **viajar junto com a imagem**. Captura ontem + processamento hoje → "Hoje" = dia da captura.

Escolha da data final do bilhete = **seleção mais recente** entre as pernas → regra **global** (candidata a entrar no `MASTER_OUTPUT_2026`). A Superbet só fornece os displays.

Formato final: `DD/MM/AAAA` (global).

---

## 5. Status e Resultado

| Superbet exibe (`STATUS`) | Código |
|---|---|
| `Ganhou` ✓ | W |
| `Perdido` ✗ | L |
| `Reembolso` 🔄 | V |
| `Sacado` | cashout → ver §7 |

No modo cru/print o `STATUS` vem como palavra pt-BR (`Perdido`, `Ganhou`, `Sacado`, `Reembolso`). **No modo rotulado (scanner)** vem em inglês no campo `Status:` — `lost`→**L**, `win`→**W**, `cashout`→§7 — seguido de `· retorno X,XX` (valor pago). Por seleção, o rótulo **`Anulada`** marca a perna anulada (push/void da seleção).

<!-- TODO: como a Superbet sinaliza HW / HL (meia ganha / meia perdida), se sinaliza. Não apareceu em nenhum dos golden atuais. -->

Códigos válidos e regra de odd por código: `MASTER_RESULTADO_2026`.

---

## 6. Boost / promoção

- Indicadores: **`SUPERTURBO X%`** (rótulo atual) ou `SUPERMÚLTIPLA X%` (legado) · linha "Você ganhou R$ XX a mais 🎉".
- O `PRÊMIO` **já contém** o boost. Logo, em `W`, `Odd = PRÊMIO ÷ Stake` captura o boost naturalmente (regra global `MASTER_RESULTADO_2026 §6`). A `ODDS TOTAIS` é a odd **sem** boost — não usar quando há PRÊMIO visível.
- Ex. real (texto, `8909-QNRSXW`): `SUPERTURBO 30%` (+R$ 24,00); ODDS TOTAIS 1,80; PRÊMIO 204,00; stake 100 → Odd = `204,00 ÷ 100 = 2,04`. Nunca registrar 1,80.
- Exemplo real (golden #2): ODDS TOTAIS 8,68; boost 5% (+R$19,22); PRÊMIO 453,64; stake 50 → Odd registrada = `453,64 ÷ 50 = 9,0728`.

---

## 7. Cashout

Rótulo do cashout na Superbet: **`SACADO`** (valor sacado) + `STATUS Sacado`. `REEMBOLSO` (§5) é devolução de **void**, NÃO cashout — não confundir.

Regra de odd no cashout é **global** (`MASTER_RESULTADO_2026 §5.1.2` e `§5.6`); aqui fica só o localizador:

- `SACADO` **=** `APOSTA` (stake) → **V**, odd = `ODDS TOTAIS` do bilhete.
- `SACADO` **≠** `APOSTA` (maior ou menor) → **W**, `Odd = SACADO ÷ Stake`.

**Modo rotulado (scanner):** o cashout vem como `Status: cashout · retorno X,XX`. Mesma regra: `retorno` **=** `Stake` → **V** (odd = `Odd total`); `retorno` **≠** `Stake` → **W** (odd = `retorno ÷ Stake`).

Ex. real (`891J-YN5HZ1`): `Status: cashout · retorno 256,00`, Stake 256,00 → **V**, odd = 1,97.

---

## 8. Bônus / freebet

A Superbet opera com aposta grátis (freebet). No modo texto o rótulo é **`APOSTA GRÁTIS`** com o valor da parte grátis, **separado** do `APOSTA` (dinheiro real):

```
APOSTA
140,00
R$
APOSTA GRÁTIS
10,00
R$
```

- **Política (decisão Feca): registrar o valor CHEIO.** `Stake = APOSTA + APOSTA GRÁTIS`.
- Ex. real (`890N-QN9C4G`): APOSTA 140,00 + APOSTA GRÁTIS 10,00 → **Stake = 150,00**.
- **Modo rotulado (scanner):** o `Stake:` **já vem cheio** (150,00) e a linha `Freebet incluído: 10,00 (dinheiro real = stake − freebet)` é só informativa → **usar o `Stake:` como está**, não somar nem subtrair.
- Layout antigo (colapsado) exibia tudo junto: `VALOR (10 R$ DE APOSTA GRÁTIS INCL.) 150,00 R$` — mesmo resultado (150,00).

---

## 9. Mapa de mercados (Superbet → `Aposta` global)

| Superbet exibe | Aposta global |
|---|---|
| Resultado Final / Vencedor / `1` `2` (na seleção) | ML |
| Handicap / Handicap (Inc. prorrogação) / Handicap de Mapas | Handicap |
| Empate Anula Aposta | DNB |
| Total de Gols | Gols |
| Total de Escanteios | Escanteios |
| Total de Cartões | Cartões |
| Total de Finalizações | Chutes |
| Handicap - Finalizações / Handicap de Finalizações | Chutes |
| Chutes no Gol | Chutes no Gol |
| Total de Desarmes | Desarmes |
| Handicap - Desarmes | Desarmes |
| Total de Games / Games Ímpar/Par | Games |
| Total de Quebras (tênis) | Player Props |
| Total de strikeouts do arremessador (MLB) | Player Props |
| Total de Impedimentos | Impedimentos |
| Empate ou 2 / Dupla Chance | Dupla Chance |
| Tiros de Meta / Total de Tiros de Meta | Team Props |

Notas:
- **Padrão geral `Handicap - [Estatística]`:** a categoria registra o objeto apostado (MASTER_APOSTAS §1), não o tipo de mercado. `Handicap - Finalizações` → `Chutes`; `Handicap - Escanteios` → `Escanteios`; `Handicap - Cartões` → `Cartões`. A linha de handicap fica na Descrição (ex.: `Catar (+10.5) Chutes [Catar v Suíça]`).
- "Total de X" precedido de nome de time/jogador (`Tunísia - Total de Cartões`, `Brusque - Total de Escanteios`) = total **da entidade**; a entidade entra na descrição (`MASTER_DESCRICAO_2026 §12.3/12.5`), a categoria segue a mesma.
- Nome de jogador em "Sobrenome, Nome" (`Valdez, Framber`) → normalizar para `Framber Valdez` na descrição.
- **Esportes individuais (Dardos, Tênis):** a seleção exibe apenas o **nome do jogador** (ex.: `Alec Small`) — sem rótulo "Resultado Final" ou "Vencedor". Nome do jogador = seleção do vencedor do confronto → `ML`. Nunca classificar como `Outros`.

---

## 10. Stake

- Localizar após o rótulo `APOSTA`. Exibida como `50,00 R$` → normalizar para `50,00`.
- A normalização (remover ` R$`/milhar, trim, vírgula decimal) é **global** (`MASTER_OUTPUT_2026 §11/§16`). Aqui fica só o localizador.

---

## 11. Odds

- **Modo rotulado (scanner):** o campo **`Odd total:`** já é a odd **efetiva**, em **vírgula** e **precisão completa** (`17,536905`, `2,261`), **já com boost** em win (= `retorno ÷ stake`) → **usar direto**, sem conversão nem cálculo. Ignorar as odds por perna (`@ 1,8`) para a odd do bilhete.
- Formato exibido nos outros modos: **PRINT** = decimal com vírgula; **TEXTO cru** (robô) = decimal com **PONTO** (`17.53`, `2.25`) → converter o ponto em vírgula antes de escrever a odd (regra global — a planilha lê ponto como milhar e corrompe).
- `ODDS TOTAIS` = odd estrutural (produto das seleções). Confirmado: bilhete `890C-QDPCUD` → 2,70 × 2,17 × 2,75 × 2,35 = 37,86 = ODDS TOTAIS.
- **Odd dupla (Super Odds / CRIAR APOSTA / DICAS DE APOSTA):** a seleção mostra duas odds (`2.17` e `2.35`) = **original** e **turbinada**. A odd que vale é a **turbinada** (a maior) — que é a que aparece em `ODDS TOTAIS`. Ignorar a original. Ex.: `8901-QI2PSS` → 2,35. (Em W, `PRÊMIO ÷ Stake` governa de qualquer forma.)
- Fonte e prioridade da odd: **global** (`MASTER_RESULTADO_2026`). Resumo da localização Superbet:
  - `W` → `Odd = PRÊMIO ÷ Stake`

> ⚠️ **Para W: `ODDS TOTAIS` é a odd estrutural SEM boost — NUNCA usar para W.** Mesmo que o valor pareça razoável, `ODDS TOTAIS` não captura boost/promoção. Para W, usar SEMPRE `PRÊMIO ÷ Stake` com precisão total.

  - `L` em múltipla sem retorno → `ODDS TOTAIS` (estrutural)
  - `V` → `ODDS TOTAIS` (do bilhete)
- **Precisão:** preservar a precisão natural — não forçar, não truncar, não arredondar. Até 12 casas decimais, seja odd calculada (`PRÊMIO ÷ Stake`) ou lida diretamente do bilhete. Manter `Stake × Odd ≈ PRÊMIO`.

---

## 12. Ruído a ignorar

`Interaja com a comunidade` · `Entrar no Supersocial` · `Dicas` · `+ Adicionar` · banners promocionais · barras de progresso ao vivo com número (ex.: `16`, `8`, `13` — são o stat ao vivo da seleção, não fazem parte da aposta) · quando houver badge ou indicação de substituição: o nome tachado/riscado = jogador original (usar), o nome em destaque acima = substituto (ignorar).

**Ruído específico do modo TEXTO:**
- **Placar embutido:** os dois números logo após os nomes dos times (`Vestmannaeyjar` / `Valur Reykjavik` / `1` / `0`) = placar ao vivo/final. Ignorar.
- **Pênaltis:** `PEN`, `(2)`, `(4)` (ex.: `898M-7SGYY3`, Austrália × Egito) = disputa de pênaltis. Ignorar.
- **Números soltos** entre pernas (`0`, `6`, `10`, `73`, `95`) = stat ao vivo. Ignorar.
- **Rótulos de produto** (NÃO são mercado nem seleção): `CRIAR APOSTA`, `DICAS DE APOSTA`, `Super Odds`, `Super Odds — …`, `Longo Prazo - …`. São o nome do produto/construtor de aposta; a odd que os segue é a combinada (usar `ODDS TOTAIS`, ver §11).
- **Cabeçalho de liga:** as linhas `país/região` + `liga` no topo de cada perna (`Internacional` / `Copa do Mundo`) contextualizam, mas o **esporte** vem da regra global (esporte ≠ liga).

---

## 13. Pegadinhas (resumo rápido)

- Cabeçalho do bloco é data de **criação**, não da aposta.
- ID só no **detalhe** → assinatura para dedup na lista.
- Hoje/Ontem/Amanhã ancoram na **captura**, não no processamento.
- Boost já embutido no `PRÊMIO`; `ODDS TOTAIS` é sem boost.
- `REEMBOLSO` = void, não cashout.
- **Dardos/Tênis individual:** seleção = nome do jogador (ex.: `Alec Small`) → `ML`. Nunca `Outros`.

---

## 14. Validações específicas da Superbet

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18` (resultado oficial, odd preservada em L/HL/V, esporte ≠ liga, jogador normalizado, nº de linhas = nº de bilhetes, data de múltipla = seleção mais recente). Não duplicar aqui.

- Nenhuma aposta com "Hoje" recebeu a data do cabeçalho.
- Hoje/Ontem/Amanhã convertidos pela data de referência da captura.
- Em W com boost (`SUPERTURBO`/`SUPERMÚLTIPLA`), a odd usa `PRÊMIO`, nunca `ODDS TOTAIS`.
- **Modo texto:** toda odd escrita com vírgula (nenhum ponto sobrando).
- **Modo texto:** `STATUS Sacado` → V se `SACADO = APOSTA`; W (odd = SACADO÷Stake) se diferente.
- **Modo texto:** com `APOSTA GRÁTIS`, o Stake gravado = `APOSTA + APOSTA GRÁTIS` (valor cheio).
- **Modo texto:** placar/pênaltis/stat ao vivo nunca entram em odd, stake ou descrição.

---

## 15. Exemplos golden (bilhetes reais)

Colunas: `Data \t Esporte \t Tipster \t Casa \t Parceiro \t Aposta \t Descrição \t Stake \t Odd \t Resultado`

**#1 — Simples W, Player Props MLB (`890E-Q6MWIB`)** — retorno em PRÊMIO, odd limpa:
```
10/06/2026	Baseball		Superbet		Player Props	Framber Valdez - Under 4.5 Strikeouts [Detroit Tigers v Minnesota Twins]	52,00	2,20	W
```

**#2 — Supermúltipla W com boost (`898K-7Y2U4H`)** — odd = PRÊMIO÷Stake, precisão preservada:
```
31/05/2026	Futebol		Superbet		Múltipla	Over 10.5 Escanteios [Juazeirense v Atletico Alagoinhas] // Ucrânia [Ucrânia v Portugal] // Brasil - Under 1.5 Impedimentos [Brasil v Panamá]	50,00	9,0728	W
```

**#3 — Void / Reembolso, DNB (`8915-YKX4GB`)** — V mantém odd do bilhete:
```
11/06/2026	Futebol		Superbet		DNB	Springvale White Eagles [Springvale White Eagles v Altona City]	60,00	1,78	V
```

**#4 — Múltipla L multi-esporte (`8905-QH5UJ4`)** — Esporte = Múltiplos, odd estrutural = ODDS TOTAIS:
```
02/06/2026	Múltiplos		Superbet		Múltipla	Voluntari - Over 4.5 Chutes [Voluntari v Hermannstadt] // Under 24.5 Chutes [Turquia v Macedônia do Norte] // Tunísia - Under 1.5 Cartões [Áustria v Tunísia] // Over 8.5 Escanteios [Maguary v Sousa PB] // Brusque - Under 4.5 Escanteios [Barra SC v Brusque] // Par Games [Filip Peliwo v Eliakim Coulibaly] // Mirra Andreeva - Under 4.5 Quebras [Mirra Andreeva v Sorana Cirstea] // Over 21.5 Games [Jack Pinnington Jones v Aleksandar Vukic]	20,00	283,67	L
```

**#5 — Múltipla W com SUPERMÚLTIPLA 5% (`890T-QKIRVD`)** — odd = PRÊMIO÷Stake, NÃO ODDS TOTAIS:
```
14/06/2026	Futebol		Superbet		Múltipla	1º Tempo - Over 4.5 Faltas [Alemanha v Curaçao] // Total de Cartões Vermelhos [Universidad Católica v Universidad de Concepción] // Costa do Marfim - Total de Tiros de Meta [Costa do Marfim v Equador]	150,00	11,37606666666667	W
```
> ODDS TOTAIS exibido = 10,88 (sem boost). SUPERMÚLTIPLA 5% (+R$ 74,11). PRÊMIO = 1.706,41.
> **Odd correta = 1.706,41 ÷ 150 = 11,37606666666667** — nunca registrar 10,88.

**#6 — Múltipla L 4 seleções (`890J-QD71FJ`)** — 1 linha, Odd=ODDS TOTAIS, Stake=campo APOSTA inteiro:
```
12/06/2026	Futebol		Superbet		Múltipla	X2 [Ursus Warszawa v Wilga Garwolin] // X2 [Lech Rypin v Orleta Aleksandrow Kujawski] // Under 30.5 Desarmes [Canadá v Bósnia e Herzegovina] // Under 21.5 Chutes [EUA v Paraguai]	200,00	37,86	L	890J-QD71FJ
```
> 4 seleções (2× Dupla Chance + Desarmes + Chutes). ODDS TOTAIS = 37,86; APOSTA = 200,00 R$; STATUS = Perdido.
> Esporte = Futebol (todas as pernas). Data = perna mais recente (Sex 12. Jun, 22:00 = 12/06/2026).
> NUNCA gerar 4 linhas separadas — é 1 bilhete, 1 ID, 1 linha.

**#7 — Múltipla L 3 seleções Handicap-Chutes (`890T-QKIS3M`)** — categoria Chutes (não Handicap):
```
13/06/2026	Futebol		Superbet		Múltipla	Catar (+10.5) Chutes [Catar v Suíça] // Brasil (-2.5) Chutes [Brasil v Marrocos] // Haiti (+6.5) Chutes [Haiti v Escócia]	200,00	5,40	L	890T-QKIS3M
```
> 3 seleções "Handicap - Finalizações" → Aposta=Chutes (objeto=Finalizações, tipo de mercado=Handicap).
> ODDS TOTAIS = 5,40; APOSTA = 200,00 R$; STATUS = Perdido (Haiti ✓ mas bilhete geral = L).
> Datas: "Ontem" com captura em 14/06/2026 → Ontem = 13/06/2026. Perna mais recente: 13/06/2026 22:00.

**#8 — Dardos ML simples** — seleção = nome do jogador, sem rótulo "Resultado Final":
```
18/06/2026	Dardos		Superbet		ML	Alec Small [Joe Croft v Alec Small]	303,00	1,78	L
```
> Seleção exibida na Superbet: `Alec Small` (apenas o nome do vencedor apostado). Sem rótulo "Resultado Final".
> Aposta = `ML` (resultado principal do confronto). NUNCA classificar como `Outros`.

### Goldens do modo TEXTO (robô)

Ilustram os rótulos e mecânicas novas do texto. Regra transversal: **≥2 seleções = `Múltipla`** — o rótulo de produto (`CRIAR APOSTA`/`DICAS DE APOSTA`/`Super Odds`) é ruído, não muda a categoria.

**#T1 — Cashout `SACADO` = stake → V (`891J-YN5HZ1`)** — `SACADO 256,00 = APOSTA 256,00` → V, odd = ODDS TOTAIS:
```
03/07/2026	Futebol		Superbet		Múltipla	Under 2.5 Cartões [Suíça v Argélia] // Argélia - Under 2.5 Cartões [Suíça v Argélia]	256,00	1,97	V	891J-YN5HZ1
```

**#T2 — Boost `SUPERTURBO` W → odd = PRÊMIO÷Stake (`8909-QNRSXW`)** — SUPERTURBO 30%; ODDS TOTAIS 1,80 (sem boost); PRÊMIO 204,00; stake 100 → `204 ÷ 100 = 2,04`:
```
03/07/2026	Futebol		Superbet		Múltipla	Under 2.5 Cartões [Argentina v Cabo Verde] // Argentina - Under 2.5 Cartões [Argentina v Cabo Verde]	100,00	2,04	W	8909-QNRSXW
```

**#T3 — Freebet `APOSTA GRÁTIS` → stake cheio (`890N-QN9C4G`)** — APOSTA 140,00 + APOSTA GRÁTIS 10,00 → Stake 150,00; L → odd = ODDS TOTAIS 20,15; data = perna mais recente (Suíça×Argélia, 03/07 00:00):
```
03/07/2026	Futebol		Superbet		Múltipla	Espanha - Over 5.5 Tiros de Meta [Espanha v Áustria] // Over 1.5 Cartões 2º Tempo [Portugal v Croácia] // Over 27.5 Finalizações [Fortaleza v Ponte Preta] // Suíça - Under 6.5 Tiros de Meta [Suíça v Argélia]	150,00	20,15	L	890N-QN9C4G
```

---

## Feedback para a camada global (registrar no track TSV)

1. **Data = perna mais recente** em múltiplas → `MASTER_OUTPUT_2026` (hoje é lacuna).
2. **Precisão da odd calculada** (não arredondar/truncar) → `MASTER_RESULTADO_2026`.
3. **Categoria `Dupla Chance`** → `MASTER_APOSTAS_2026` (hoje cai em Outros).
4. **Categoria `Impedimentos`** → `MASTER_APOSTAS_2026` (hoje cai em Outros).

---

VERSÃO: 2026
STATUS: QUASE COMPLETO (pendência: §5 HW/HL — sem amostra. §7 cashout e §8 freebet resolvidos na sessão de modo-texto.)
CASA: Superbet
