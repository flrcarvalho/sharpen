# CASA_VAIDEBET
## Camada de tradução — VaideBet → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da VaideBet.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `VaideBet` · site: `vaidebet.bet.br`
- Locale: pt-BR · Moeda: R$ (BRL) — a API carimba `currency: "BRL"`
- **Decimal exibido na tela: PONTO** (`3.00`, `R$30.00`) → normalizar para vírgula.
- Motor: **Altenar / BIA** (`biahosted.com`), embutido no site da casa. O histórico é um widget do motor, mas roda no **frame de topo** (o `origin` da requisição é `www.vaidebet.bet.br`).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js`).

```
POST https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory
{"culture":"pt-BR","timezoneOffset":180,"integration":"vaidebet","deviceType":1,
 "countryCode":"BR","dateFrom":"…Z","dateTo":"…Z","liveOnly":false,"numFormat":"en-GB",
 "pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}
→ {"isLastPage":false,"bets":[…]}
```

Quatro consequências que mandam no desenho:

1. **O endpoint é de OUTRA origem** (`biahosted.com`) e autentica por header **`Authorization: Bearer <JWT da sessão>`**, não por cookie. O replay tem de reusar os headers exatos da requisição que a página fez — `credentials:"include"` sozinho não basta.
2. **A lista NÃO carrega sozinha:** vem de 10 em 10 e a tela tem um botão **"Mostrar mais apostas"**. O robô **não** usa o botão (esse tipo de botão costuma checar `isTrusted` e não é automatizável — lição da bet365): pagina por `pageNumber` na própria API.
3. **As abas são o array `statuses` do corpo**, mesma URL:
   - **Processado** (resolvidas): `[1, 8, 2, 4, 18]`
   - **Aberto**: `[0, 10, 3, 20, 17]`
   O robô varre as duas a cada rodada, partindo de qualquer uma que o operador tenha aberto.
4. **Fim autoritativo: `isLastPage: true`.** Sinal explícito da casa — nada de heurística por rolagem.

**Janela de datas:** `dateFrom`/`dateTo` são nativos do corpo. As **resolvidas** respeitam os dias pedidos no popup; as **abertas** vão com janela larga de propósito — aposta colocada há meses pode ter jogo amanhã, e o filtro do servidor a apagaria do lote.

### 2.2 Tipo do bilhete declarado

O card não rotula "Simples/Múltipla". O tipo sai da estrutura:

- `selections.length ≥ 2` → **Múltipla**;
- 1 seleção com `isBetBuilder: true` → **Bet Builder** (as pernas ficam em `bbOdds[]`, todas do mesmo evento) — o bloco capturado escreve `Bet Builder (mesmo jogo · N seleções)`;
- 1 seleção sem `bbOdds` → **Simples**.

> A conta do reconhecimento (s209) só tinha **simples e bet builder**. Múltipla de jogos diferentes está coberta no formato e no harness (caso sintético), mas **nunca foi vista ao vivo**.

### 2.3 Layout do bilhete

Cards em **grid de 2 colunas**, com faixa colorida de status no topo (`ABERTO` / `GANHOU / VENCIDO` / `PERDIDO`) e rodapé cinza com `DD/MM • HH:MM` **da colocação** + `ID: …`. **Não** há linha em branco entre bilhetes — por isso a casa nunca pode cair no robô de texto genérico (`roboScroll`), que parte o `innerText` por linha em branco (lição da KTO, s192).

---

## 2.5 Campos da API (o que o inject entrega)

| Campo (API) | Significado | Observação |
|---|---|---|
| `id` | ID do bilhete | é o `ID:` do rodapé do card · chave de dedup e do `[Código:]` |
| `status` | estado do bilhete | enum bruto — ver §5 |
| `createdDate` | **colocação**, ISO **UTC** (`…Z`) | converter para America/Sao_Paulo · **não** é a coluna Data (ver §4) |
| `selections[].eventDate` | início do evento, ISO UTC | a **mais recente** vira a coluna Data |
| `totalStake` (= `unitStake` = `finalStake`) | **stake** | unidade normal (`30.0` = R$ 30,00) — **não** há milésimos |
| `totalWin` | retorno | ⚠ **na aberta é POTENCIAL e já vem preenchido** — ver §5 |
| `openStake` / `remainingTotalWin` | só existem em bilhete **aberto** | reforço para distinguir aberta de resolvida |
| `totalOdds` (= `selections[].price`) | **odd total, já boostada** | precisão completa; a tela trunca — ver §11 |
| `selections[].boostedSelection.preBoostedPrice` | odd **antes** do boost | é o número riscado do card · nunca é a odd válida |
| `boostedBet.preBoostedPotWin` | retorno que teria sem o boost | informativo |
| `selections[].bbOdds[]` | pernas do **bet builder** | `marketName` + `oddName` + `status` por perna |
| `selections[].name` | seleção; no bet builder, as pernas concatenadas por `" \| "` | traduzir para `" // "` (separador canônico, achado #19) |
| `selections[].marketName` | mercado, em pt-BR (beisebol às vezes em inglês) | ver §9 |
| `selections[].eventName` | confronto (`Bahia vs. Corinthians`) | |
| `selections[].eventScore` | **placar** (`"1:1"`) | ausente em bilhete aberto |
| `selections[].spec` | linha/handicap em JSON (`{"1":"0.5"}`) | ruído — a linha já vem no `oddName` |
| `selections[].sportTypeId` | esporte, **só o id** | `1` = `Futebol` · `13` = `Baseball` (confirmados) — ver §12 |
| `cashOutValue` / `partialCashOut` / `partialCashouts[]` | cashout | **sempre 0 na amostra** — ver §7 |
| `bonus` / `bonusPart` / `bonusInsurance` | bônus | sem caso na amostra (§8) |
| `isLastPage` (raiz) | **fim autoritativo** da paginação | |

---

## 3. ID do bilhete

- Formato: **numérico, 10 dígitos** (ex.: `5234878919`), exibido no rodapé do card como `ID: 5234878919`.
- Sempre visível → **dedup forte por ID**, dispensa assinatura derivada.
- Vai para a 11ª coluna interna (`Código`), nunca para a planilha do usuário.

---

## 4. Data

**Coluna Data do TSV = data do EVENTO da seleção mais recente** (`MASTER_OUTPUT §4`).

A VaideBet expõe as duas, e elas divergem:

- **colocação** — `createdDate`. É o que o **rodapé do card** mostra. Serve de contexto e de ordem; **não** é a coluna Data.
- **evento** — `selections[].eventDate`, exibido dentro do bloco branco do card. **Usar a mais recente.**

> Não é detalhe: os dois bilhetes **abertos** da amostra foram colocados em **26/07 21:1x** para jogos em **27/07**. Usar a colocação gravaria os dois no dia errado. O harness (`extensor/harness/casos/vaidebet.mjs`) trava as duas leituras.

Fuso: os dois campos são **ISO com `Z` = UTC** → converter para America/Sao_Paulo. Sem converter, um bilhete de `01:55Z` do dia 26 aparece no dia 26 em vez de 25 (o card mostra `25/07 • 22:55`).

---

## 5. Status e Resultado

De-para do `status` do bilhete:

| `status` | Leitura | Código |
|---|---|---|
| 0 | Em aberto (faixa `ABERTO` no card) | *(vazio — não liquidar)* |
| 1 | Ganhou (faixa `GANHOU / VENCIDO`) — conferir o dinheiro | `W` |
| 1 + retorno **igual** à stake | Devolvida / void | `V` |
| 2 | Perdeu (faixa `PERDIDO`) | `L` |
| 3 · 4 · 8 · 10 · 17 · 18 · 20 | **Desconhecidos** — sobem crus, não liquidar automaticamente | — |

Os valores desconhecidos aparecem **só nos filtros das abas** — nenhum bilhete real trouxe um deles até agora. O mais provável é que cubram anulado/devolvido/cashout/recusado, mas **enquanto não houver um bilhete para cruzar com a tela, é chute** e sobe cru.

O `status` também existe **por perna** (`bbOdds[].status`), com os mesmos valores: `0` pendente · `1` ganhou · `2` perdeu. Confere com o ✓/✗ verde/vermelho do card.

> ⚠️ **A armadilha central desta casa.** Em bilhete **aberto**, `totalWin` **já vem preenchido com o valor potencial** (`5236294996`: stake 30, `totalWin: 90`) e o card mostra isso como "Ganho total R$90,00". Lê-lo como retorno realizado transforma **toda** aposta em aberto numa vitória fantasma. Só `status: 1` autoriza a régua financeira do W. O bloco capturado emite `Retorno potencial:` nesse caso, nunca `Retorno:`.

Quem decide W/V/HW/HL é a régua financeira do `MASTER_RESULTADO_2026`, não o enum sozinho.

---

## 6. Boost / promoção

A casa opera **dois** boosts, ambos visíveis no card como `2.33 » 3.00` (odd antiga riscada → odd valendo):

| Selo no card | `boostedSelection.boostProperty` |
|---|---|
| `GOLDEN BOOST` | `3` |
| `ODDS TURBINADAS` | `1` |

**O boost já está embutido em `totalOdds` / `price`** — é essa a odd válida. O `preBoostedPrice` é a odd **antes** do boost (o riscado) e nunca vai para o TSV; o bloco capturado o emite apenas como `Marcação da casa: odd turbinada …`.

Nos 3 bilhetes `W` da amostra a odd declarada explica o retorno ao centavo (40÷10=4 · 75÷30=2,5 · 120÷30=4), ou seja as duas fontes concordam. A regra global do `W` (`retorno ÷ stake`) continua valendo — se um dia a casa aplicar boost só na liquidação, o dinheiro pega sozinho.

---

## 7. Cashout

A casa **tem** cashout (as abertas mostram botão `Cashout R$30,00`), mas **nenhum bilhete da amostra foi cashouteado**.

⚠️ **`cashOutValue` do histórico veio `0` inclusive nas abertas com botão ativo** — o valor oferecido vem de outro endpoint (`GetOpenBetsCashoutValues`). Ou seja: esse campo só deve significar alguma coisa **depois** de o cashout ser executado, e isso ainda não foi observado.

Quando aparecer, vale a regra global: cashout **=** stake → `V`; cashout **≠** stake → `W` com `Odd = Cashout ÷ Stake` (`MASTER_RESULTADO §5.1.2` e `§5.6`).

<!-- TODO: capturar um bilhete com cashout real, ver em que `status` ele cai e travar no harness. -->

---

## 8. Bônus

`bonus`, `bonusPart`, `bonusInsurance` existem no payload; **sem caso na amostra** (todos 0). O bloco capturado emite `Marcação da casa: aposta com bônus (R$ …)` quando vier valor, para a IA decidir pelo global.

---

## 9. Mapa de mercados (VaideBet → `Aposta` global)

Só os mercados **confirmados** no dado real (camada fina — mercado nunca visto não entra aqui):

| VaideBet exibe | Aposta global |
|---|---|
| `Total de gols` · `Criciúma total de gols` · `Sport total de gols` · `1º tempo - total` | Gols |
| `Total de escanteios` · `Lanús total de escanteios` · `Criciúma total de escanteios` · `1º tempo - total de escanteios` | Escanteios |
| `Ambas equipes 4+ escanteios cada uma` · `Ambas equipes 5+ escanteios cada uma` · `1º tempo - Ambas equipes 2+ escanteios cada uma` | Escanteios |
| `Total cartões` · `1º tempo - total cartões` | Cartões |
| `Vencedor do encontro` · `Vencedor (incluindo innings extra)` | ML |
| `Ambas equipes marcam` | Ambas Marcam |
| `Chutes a Gol - <Jogador> (TIME)` (ex.: `Chutes a Gol - Yuri Alberto (COR)`) | Chutes no Gol |
| `Marcador - <Jogador> (TIME)`, seleção `Qualq. Altura` ¹ | Anytime |
| `<Time> para marcar em ambos os tempos` ¹ | Team Props |
| `<Time> Mais de/Menos de (incluindo innings extra)` (beisebol) ¹ | Corridas |
| `Winner & total (incl. extra innings)` (beisebol) | Outros |

> **Estatística de JOGADOR não vira `Player Props` aqui.** O `MASTER_APOSTAS §Player Props` é explícito: *"NÃO usar `Player Props` quando o objeto apostado tiver categoria própria, mesmo que o mercado envolva um jogador específico"* — e `Chutes a gol` é sinônimo literal de `Chutes no Gol` (§4). O precedente canônico é o cartão: `"Nico Williams — Para o Jogador Receber Cartão"` → `Cartões`, **nunca** `Player Props` (§5 Cartões). A regra "jogador individual → `Player Props`" existe **só** para `Pontos` e `Sets`, onde está escrita como exceção da própria categoria — não é regra geral.

> **`para marcar em ambos os tempos` = `Team Props`**, não `Gols`: o objeto é um feito da equipe no jogo, não a contagem de gols. Padrão já estabelecido em `CASA_BETNACIONAL §9` e `CASA_LOTTU §9` (confirmado originalmente na KingPanda).

> **`Winner & total` = mercado COMBINADO → `Outros`** (decisão do Feca, s210). Uma seleção só que carrega **duas** apostas — resultado + total de corridas (`LA Dodgers e mais de 8.5`). Nenhuma categoria descreve o objeto sozinha: `ML` esconderia o total, `Corridas` esconderia o resultado. Cai no `§2` como último recurso, e **as duas partes vão na Descrição** (`LA Dodgers // Over 8,5 Corridas`), que é onde a informação não se perde. Vale para qualquer mercado combinado desta casa enquanto o `MASTER_APOSTAS` não tiver regra geral (ver Feedback).

¹ Visto no card da casa (print do histórico), ainda não no payload da amostra salva — o mercado existe, mas não está nas fixtures do harness.

---

## 10. Stake

- Origem: `totalStake` (unidade normal, sem milésimos). `unitStake` e `finalStake` trazem o mesmo valor em 100% da amostra.
- Normalização de moeda/milhar = global.

---

## 11. Odds

- Origem: `totalOdds` (bilhete) e `selections[].price` (seleção), **precisão completa**.
- ⚠ **A tela trunca a odd riscada em 2 casas**: `preBoostedPrice: 2.3334` aparece como `2.33` e `3.1429` como `3.14`. **Nunca ler odd do card.**
- A odd que vale é a **boostada** (`totalOdds`), não a riscada — ver §6.
- No `W`, o dinheiro confirma: `totalOdds × stake == totalWin` ao centavo nos 3 casos da amostra.
- Bilhete **aberto** usa `totalOdds`; `totalWin` ali é potencial e **não** pode virar odd.

---

## 12. Ruído a ignorar

- **`sportTypeId` é o esporte, mas só como número.** Confirmados: `1` = **`Futebol`**, `13` = **`Baseball`** — os valores **oficiais** do `MASTER_ESPORTES_2026` (⚠️ "Beisebol" é sinônimo de *entrada*, nunca de saída: no 1º lote real o bloco escreveu "Beisebol" e o banco ficou com **duas grafias do mesmo esporte**, contadas como esportes diferentes). Há ainda `sportId` (66 / 76), numeração paralela do motor — usar `sportTypeId`. Id fora do mapa sobe cru e a IA resolve pelo evento/mercado.
- `spec` (`{"1":"0.5"}`, `{"30":"4"}`) — a linha já vem legível no `oddName`/`name`.
- `marketTypeId`, `sportMarketId`, `childMarketTypeId`, `selectionTypeId`, `marketId`, `dbId` — internos do motor.
- `champId` / `catId` — liga e país, **só como id** (sem nome). Não há campo de liga legível no payload.
- `device` (0/1 = desktop/mobile), `priceType`, `isBanker`, `isVirtual`, `linesCount`, `combLength` — internos.
- `pitcherInfo` (beisebol) — informativo do jogo, não é dado do bilhete.

---

## 13. Pegadinhas (resumo rápido)

- **`totalWin` de aposta ABERTA é potencial e vem preenchido** → nunca ler como retorno (§5).
- Odd: a tela **trunca** a riscada; a válida é a **boostada** (`totalOdds`).
- Data: card mostra colocação no rodapé; o TSV quer o **evento** (as 2 abertas mudam de dia).
- Datas em `Z` = UTC → converter; sem isso o bilhete pula de dia.
- `status` fora de {0,1,2} nunca vira W/L por dedução — 7 valores ainda não batizados.
- A lista **não** carrega sozinha ("Mostrar mais apostas") → só API paginada resolve.
- O endpoint é de outra origem e usa **Bearer**: replay sem os headers reais volta 401.
- `cashOutValue` = 0 **não** significa "sem cashout disponível" (o valor vem de outro endpoint).
- Nome do esporte **não existe** no payload — só id.

---

## 14. Validações específicas

> **Transversais (todas as casas):** ver `MASTER_PIPELINE_2026 §8` + `MASTER_OUTPUT_2026 §17–§18`. Não duplicar aqui.

- **Coluna Data = a linha `Data (evento mais recente):` do bloco, copiada literalmente.** Nunca inferir da vizinhança nem da ordem da lista. **Erro real no 1º lote (s210):** os dois únicos bilhetes cujo evento caía em **24/07** saíram gravados como **23/07** — a data dos bilhetes vizinhos — embora o bloco trouxesse `24/07/2026` nas duas linhas. Data errada é a coluna 1 do TSV: desloca o bilhete de dia no painel inteiro.
- Odd com precisão completa, decimal com vírgula, e sempre a **pós-boost**.
- Bilhete aberto sai **sem** resultado (`extraction_state = aberta`) e **sem** retorno realizado.
- Bet builder: pernas unidas por `" // "` na Descrição (achado #19) e `Aposta = Múltipla` **mesmo sendo tudo do mesmo jogo** (`MASTER_APOSTAS §Bet Builder` — confirmado no 1º lote).
- Esporte: copiar o valor **oficial** do bloco (`Futebol` / `Baseball`), nunca um sinônimo.

---

## 15. Exemplos golden (bilhetes reais)

<!-- TODO: a casa acabou de entrar (s209) e ainda NÃO houve extração real validada ponta a
     ponta. Preencher com o primeiro lote conferido contra a planilha — sem isso, exemplo
     aqui seria chute com cara de gabarito. A regressão da CAPTURA (campos, data, odd,
     status, aberta × potencial) já está travada em `extensor/harness/casos/vaidebet.mjs`,
     com 12 bilhetes reais + 3 casos sintéticos. -->

---

## Feedback para a camada global / MODELO

1. **Mercado COMBINADO não tem regra** no `MASTER_APOSTAS`: `Winner & total` junta resultado + total numa seleção só, e a §2 (prioridade) pressupõe que existe *uma* categoria específica aplicável. Nesta casa ficou **`Outros`** por decisão do Feca (s210) — mas é decisão **local**, e o mesmo padrão existe no futebol (`Resultado & Ambas Marcam`) e vai reaparecer em qualquer casa. Vale promover a regra ao global: combinado → `Outros`, com os componentes na Descrição.
2. **Mercados de beisebol chegam em inglês** neste motor (`Winner & total (incl. extra innings)`) mesmo com `culture: pt-BR`. Se outras casas Altenar entrarem, o padrão vai se repetir.
3. *(resolvido na própria sessão — fica como registro)* A dúvida "estatística de jogador vira `Player Props`?" **já está respondida** no §Player Props + §5 Cartões. Não é lacuna: o objeto manda, e a exceção por entidade existe só em `Pontos`/`Sets`.

---

VERSÃO: 2026
STATUS: CAPTURA COMPLETA (harness verde) · mapa de mercados **fechado** (§9) · golden a preencher (§15) · **sem validação ao vivo**
CASA: VaideBet
