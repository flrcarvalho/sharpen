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

Cada aposta é um **bloco único**, de cima para baixo:

1. Card(s) de seleção (liga + data/hora da seleção + confronto + placar + mercado + odd + ✓/✗ por seleção)
2. ID da aposta
3. `ODDS TOTAIS`
4. `APOSTA` (stake)
5. Em boost: `SUPERMÚLTIPLA X%` + linha "Você ganhou R$ XX a mais"
6. `PRÊMIO` (em W) **ou** `REEMBOLSO` (em void)
7. `STATUS`
8. Cabeçalho de **criação** do bilhete (`DD DE MMM. DE AAAA — HH:MM`) — fica junto ao ID, **não** é a data da aposta (ver §4)

Regra de blocos: interpretar cada bloco até o ID; nunca misturar seleções de blocos diferentes.
Ordem na tela: mais recente no topo → mais antiga embaixo. A inversão para o output é **global** (`MASTER_OUTPUT_2026 §15`).

---

## 3. ID do bilhete (chave de deduplicação)

- Formato: `XXXX-XXXXXX` (alfanumérico). Ex.: `890C-QDPCUD`, `898K-7Y2U4H`.
- Regra: 1 ID = 1 aposta = 1 linha.
- **Pegadinha:** o ID aparece no **detalhe** da aposta, não na tela de lista. A lista mostra confronto/mercado/odd/stake/status, mas **não** o ID.
- **Dedup quando só há a lista:** assinatura derivada = `data_criação + stake + odds_totais + confronto`. Abrir o detalhe (pegar o ID real) só nos candidatos que a assinatura marcar como novos.
- Existe também um hash UUID minúsculo no rodapé de cada bilhete (ex.: `33048385-a4e1-4ac8-...`). Possível chave alternativa, mas **não confirmado** se é estável por aposta ou por render/sessão. Não usar até confirmar.
- Nunca duplicar, agrupar ou ignorar ID válido.

---

## 4. Data

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

| Superbet exibe (STATUS) | Código |
|---|---|
| Ganhou ✓ | W |
| Perdido ✗ | L |
| Reembolso 🔄 | V |

Por seleção, o rótulo **`Anulada`** marca a perna anulada (push/void da seleção).

<!-- TODO: como a Superbet sinaliza HW / HL (meia ganha / meia perdida), se sinaliza. Não apareceu em nenhum dos golden atuais. -->

Códigos válidos e regra de odd por código: `MASTER_RESULTADO_2026`.

---

## 6. Boost / promoção

- Indicadores: `SUPERMÚLTIPLA X%` · linha "Você ganhou R$ XX a mais 🎉".
- O `PRÊMIO` **já contém** o boost. Logo, em `W`, `Odd = PRÊMIO ÷ Stake` captura o boost naturalmente (regra global `MASTER_RESULTADO_2026 §6`). A `ODDS TOTAIS` é a odd **sem** boost — não usar quando há PRÊMIO visível.
- Exemplo real (golden #2): ODDS TOTAIS 8,68; boost 5% (+R$19,22); PRÊMIO 453,64; stake 50 → Odd registrada = `453,64 ÷ 50 = 9,0728`.

---

## 7. Cashout

`REEMBOLSO` (§5) é devolução de **void**, não cashout — não confundir.

<!-- TODO: onde a Superbet exibe um cashout PARCIAL (encerramento antecipado) e com qual rótulo. A regra de odd no cashout é global (MASTER_RESULTADO_2026 §5.6). Aqui entra só o localizador. Não apareceu em nenhum dos 8 bilhetes enviados. -->

---

## 8. Bônus

<!-- TODO: confirmar se a casa opera com bônus/freebets e qual a política de tratamento (excluir / marcar / incluir). Sem amostra ainda. -->

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
| Chutes no Gol | Chutes no Gol |
| Total de Desarmes | Desarmes |
| Total de Games / Games Ímpar/Par | Games |
| Total de Quebras (tênis) | Player Props |
| Total de strikeouts do arremessador (MLB) | Player Props |
| Total de Impedimentos | Impedimentos |
| Empate ou 2 / Dupla Chance | Dupla Chance |

Notas:
- "Total de X" precedido de nome de time/jogador (`Tunísia - Total de Cartões`, `Brusque - Total de Escanteios`) = total **da entidade**; a entidade entra na descrição (`MASTER_DESCRICAO_2026 §12.3/12.5`), a categoria segue a mesma.
- Nome de jogador em "Sobrenome, Nome" (`Valdez, Framber`) → normalizar para `Framber Valdez` na descrição.

---

## 10. Stake

- Localizar após o rótulo `APOSTA`. Exibida como `50,00 R$` → normalizar para `50,00`.
- A normalização (remover ` R$`/milhar, trim, vírgula decimal) é **global** (`MASTER_OUTPUT_2026 §11/§16`). Aqui fica só o localizador.

---

## 11. Odds

- Formato exibido: decimal com vírgula.
- `ODDS TOTAIS` = odd estrutural (produto das seleções). Confirmado: bilhete `890C-QDPCUD` → 2,70 × 2,17 × 2,75 × 2,35 = 37,86 = ODDS TOTAIS.
- Fonte e prioridade da odd: **global** (`MASTER_RESULTADO_2026`). Resumo da localização Superbet:
  - `W` → `Odd = PRÊMIO ÷ Stake`
  - `L` em múltipla sem retorno → `ODDS TOTAIS` (estrutural)
  - `V` → `ODDS TOTAIS` (do bilhete)
- **Precisão:** preservar a precisão natural — não forçar, não truncar, não arredondar. Até 12 casas decimais, seja odd calculada (`PRÊMIO ÷ Stake`) ou lida diretamente do bilhete. Manter `Stake × Odd ≈ PRÊMIO`.

---

## 12. Ruído a ignorar

`Interaja com a comunidade` · `Entrar no Supersocial` · `Dicas` · `+ Adicionar` · banners promocionais · barras de progresso ao vivo com número (ex.: `16`, `8`, `13` — são o stat ao vivo da seleção, não fazem parte da aposta).

---

## 13. Pegadinhas (resumo rápido)

- Cabeçalho do bloco é data de **criação**, não da aposta.
- ID só no **detalhe** → assinatura para dedup na lista.
- Hoje/Ontem/Amanhã ancoram na **captura**, não no processamento.
- Boost já embutido no `PRÊMIO`; `ODDS TOTAIS` é sem boost.
- `REEMBOLSO` = void, não cashout.

---

## 14. Validações específicas da Superbet

- Nenhuma aposta com "Hoje" recebeu a data do cabeçalho.
- Hoje/Ontem/Amanhã convertidos pela data de referência da captura.
- Data final = seleção mais recente.
- Nº de linhas geradas = nº de IDs detectados.
- Em W com boost, a odd usa `PRÊMIO`, nunca `ODDS TOTAIS`.

(Validações estruturais gerais — 10 colunas, TSV, ordem cronológica — são globais: `MASTER_PIPELINE_2026` / `MASTER_OUTPUT_2026`.)

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

---

## Feedback para a camada global (registrar no track TSV)

1. **Data = perna mais recente** em múltiplas → `MASTER_OUTPUT_2026` (hoje é lacuna).
2. **Precisão da odd calculada** (não arredondar/truncar) → `MASTER_RESULTADO_2026`.
3. **Categoria `Dupla Chance`** → `MASTER_APOSTAS_2026` (hoje cai em Outras).
4. **Categoria `Impedimentos`** → `MASTER_APOSTAS_2026` (hoje cai em Outras).

---

VERSÃO: 2026
STATUS: QUASE COMPLETO (pendências: §5 HW/HL, §7 cashout real)
CASA: Superbet
