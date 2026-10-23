# CASA_THUNDERPICK
## Camada de tradução — Thunderpick → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Thunderpick.
> Toda regra de estrutura, taxonomia, descrição, resultado e **cálculo** de odd vive nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Thunderpick` · site: `thunderpick.io` · apostas em **My Bets** (abas
  Settled e Open).
- Locale: a interface está em inglês, e **mercado, seleção, times e ligas vêm em INGLÊS**
  (`Match Handicap`, `Player Hayes Nigel - total points (incl. overtime)`, `Euroleague`).
- Moeda: **EUR, sempre** (§1.1). A API não manda campo de moeda.
- **Dinheiro em CENTAVOS** (`amount` 4383 = 43,83 EUR) e **odd em número** (`1.62`).
- Plataforma **PRÓPRIA**: front React Router v7, API `/api/*` no mesmo domínio, atrás da
  Cloudflare. Os feeds são Oddin.gg (eSports) e DATA.BET. Não é Altenar, BetBy, Kambi,
  BetConstruct nem softlabs. Família `thp` (inject `thp_inject.js`; `tp_` é da 1win).
- `Parceiro` / `Tipster`: não preenchidos na extração — vêm do workspace da app.

> **Grafia (s426):** `Thunderpick`, a da marca. Medido em 22/10/2026 (`audit_grafias`, 136
> casas): a base não tinha a casa em grafia nenhuma.

### 1.1 A conta é em EURO, mesmo quando a tela mostra outra moeda

A casa guarda aposta e saldo **em euro**. A própria tela de Wallet Settings diz que
"transactions and bets are always counted and settled in Euro", e a moeda escolhida ali é só
de exibição. Medido no recon (22/10/2026): com a exibição em USD, o mesmo bilhete de 2025
apareceu como 24,98 e depois 24,97 USD, e o saldo foi de $1,88 para $1,89. **A exibição usa
o câmbio do DIA**, não o da aposta. Com a exibição em EUR, o card bate com a API ao centavo.

Por isso (decisão do Feca, 22/10/2026):

- **Cadastre a conta em EUR**, qualquer que seja a moeda que a pessoa usa na tela da casa.
- O bloco leva `Moeda: EUR`, `Carimbo de colocação:` (dia da cotação) e o dinheiro sem `R$`.
  O `/salvar` converte para R$ pela PTAX do dia da aposta, **uma conversão só**
  ([`docs/PLANO_MOEDA_POR_CONTA.md`](../docs/PLANO_MOEDA_POR_CONTA.md)).
- Para conferir valor contra a casa, **troque a exibição da casa para EUR**. Em USD ou BRL o
  número da tela muda todo dia sem nenhuma aposta, e a Caixa Inteligente (que confere em EUR)
  pareceria divergir.

### 1.2 Esporte: a API não manda o nome

Só vem `gameId`. O mapa abaixo foi **medido pela liga de cada bilhete** da amostra; id fora
dele sobe cru no bloco (`gameId N, sem nome`) e a IA deduz pela liga.

| `gameId` | Esporte (MASTER) | Liga que provou |
|---|---|---|
| 6 | E-Sports (CS2) | BLAST Rivals Spring 2025, YaLLa Compass |
| 10 | Futebol | Europa League, Libertadores |
| 11 | Basquete | NBA, Euroleague |
| 14 | Hóquei | Alps Hockey League |
| 15 | Tênis | ATP / WTA |
| 43 | Badminton | BWF World Tour (23/10/2026) |

`23` ("Challenger League - 2026", FaZe vs Lucky Five) e `31` ("Liga Pro") só apareceram dentro
de múltipla, sem prova do esporte: ficam fora do mapa e vão à IA.

---

## 2. Modo de ingestão e layout  ⭐

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/thp_inject.js`).

```
GET https://thunderpick.io/api/wagers/v2/resolved?take=100&skip=N&sortColumn=finishTime
GET https://thunderpick.io/api/wagers/v2/pending
    thunderpick-token: <sessão>
→ { "statusCode":200, "ok":true, "data": { "wagers":[…], "totalWagersCount": N } }
```

Medido com a sessão do Feca (22/10/2026):

- **Auth pelo header `thunderpick-token`** (64 caracteres, opaco, não é JWT), que a página
  manda por `fetch` em toda chamada de `/api/`. Sem ele: **HTTP 403** com `errorCode 2013`.
  O mesmo valor fica em `localStorage["thp.sessionData"].sessionId`, e o inject parte dele a
  frio.
- **Liquidadas paginam por `take`/`skip`.** A página pede `take=20` e avança por botões.
  `take` de 100, 500 e 1000 foi aceito; **o teto real não foi medido** (a conta tinha 29). O
  inject pede 100 e avança pelo tamanho que VOLTOU.
- **Fim autoritativo = `totalWagersCount` da 1ª página.** ⚠️ `skip` além do fim devolve
  `{wagers:[], totalWagersCount:0}`: o total de uma página tardia mente.
- **Abertas (`/pending`) vêm todas de uma vez**, sem parâmetro.
- Outras rotas vistas no bundle, fora da captura: `wagers/resolved/:wagerId`,
  `combo-wagers/cashout`, `/api/freebets/`, `/api/exchange-rates`.

### 2.3 Layout do bilhete (card)

Card por bilhete na aba Settled/Open, com mercado, seleção e linha (`Vitality -5.5`,
`Round Handicap - Map 2`), odd (`@ 1.62`), stake e retorno na moeda de exibição. A
paginação é por botões e não há prova de linha em branco entre os cards no `innerText`:
**texto por DOM não serve; por isso API.**

---

## 2.5 Campos da API (o que o inject entrega)

| Campo | Confirmado na Thunderpick |
|---|---|
| `wagerId` | numérico, em **DUAS séries**: múltipla ~2,2M (`2225866`), simples 4,9M–10,3M (`10277912`). O código leva o prefixo de tipo: `C2225866` / `S10277912` |
| `uuid` | id único do bilhete (zerado na fixture). Não vai para o marcador |
| `wagerType` | `PreMatch` · `InPlays` (ao vivo) · `Combo` (múltipla). Simples e ao vivo usam `S` |
| `wagerUIState` | `won` · `lost` · `open` (o estado que o card mostra) |
| `state` | `resolved` nas liquidadas; **ausente** nas abertas |
| `amount` | stake em **centavos de euro** (4383 = 43,83 EUR) |
| `odds` | odd do bilhete, a do card; na múltipla, **já o produto das pernas** |
| `outcome` | retorno pago, em centavos de euro; `0` na perdida; **ausente** na aberta |
| `theoreticalOutcome` | só em múltipla liquidada: stake × odd arredondado (18721 contra o `outcome` 18720) |
| `createTime` | colocação, ISO UTC com 6 ou 7 casas de fração → o carimbo (dia da cotação) |
| `eventStartTime` | início do evento, ISO UTC; na múltipla, **o da perna mais tardia** |
| `finishTime` | liquidação, ISO UTC (fora do bloco: a data da linha é a do evento) |
| `gameId` | esporte, só o número (§1.2) |
| `eventName` · `competition.name` | jogo (`Vitality vs Wildcard`) e liga, verbatim |
| `marketName` · `selectionName` · `selectionTotal` | mercado, seleção e a **linha da seleção** (`-5.5`, `14.5`) |
| `winningSelectionName` | a seleção vencedora, segundo a casa |
| `subWagers[]` | pernas da múltipla, com os mesmos campos e `subWagerUIState` (`won`/`lost`/`open`) e `odds` próprios |
| `cancelReason` · `cashOutOdds` · `freeBet` | `null` em toda a amostra (§5, §7, §8) |
| `cashOutStatus` · `cashOutAmountThc` | só nas abertas (`3`, `0`): oferta, não dinheiro |

**Ficha (s426, 23/10/2026):** adaptador `app/adaptadores/thp.py`, gate
`tests/test_adaptador_thp.py`. Na casa virada a aposta sai da IA: o servidor monta a Ficha do
cru e só manda à IA o que a Ficha recusa (`cancelReason`, `cashOutOdds`, `freeBet`) ou o termo
que o dicionário ainda não conhece. O mercado de jogador vai à Ficha com o nome na ordem de
leitura e sem o ` - ` (`Player Doncic Luka - total points` → `Luka Doncic total points`), para
a chave do dicionário valer para qualquer jogador.

---

## 3. ID do bilhete

- `wagerId` com **prefixo de tipo** posto pela extensão: `C` múltipla, `S` simples (PreMatch e
  InPlays). As duas séries são independentes e nada impede o mesmo número nas duas; sem o
  prefixo, a dedup juntaria dois bilhetes diferentes.
- Dedup forte por ID. Vai para a 11ª coluna interna (`Código`).

---

## 4. Data

**A coluna Data é a do EVENTO** (`eventStartTime`, a perna mais tardia na múltipla), de UTC
para São Paulo. A colocação (`createTime`) sai em São Paulo no bloco e no carimbo. A
conversão cruza a meia-noite: a múltipla `C2225866` tem evento às 02:30 UTC de 22/10, que é
**21/10 23:30** em São Paulo; colocação 22/10 00:56 UTC = carimbo `20261021215600`.

> Múltipla perdida com perna ainda por jogar: o servidor puxa a data para a perna perdida
> (`repository.data_da_perna_perdida`, pelo rótulo `[perna perdida]`).

---

## 5. Status e Resultado

O retorno é arredondado ao centavo **sem regra fixa**: `2226 × 8,41 = 18720,66 → 18720`
(truncado), mas `2196 × 1,8 = 3952,8 → 3953` (arredondado). Por isso `W` exige que o retorno
feche com stake × odd **com tolerância de 1 centavo**, e a odd do bloco é sempre a do card
(abaixo do piso de R$ 1,00, a "correção" por retorno ÷ stake só sujaria a odd).

| `wagerUIState` · dinheiro | Leitura | Código |
|---|---|---|
| `open` | Em aberto (perna já ganha **não** liquida a múltipla) | *(vazio — não liquidar)* |
| `lost` · `outcome` = 0, sem `cancelReason` | Perdeu | `L` |
| qualquer · `outcome` = stake | P/L zero | `V` |
| `won` · `outcome` = stake × odd (± 1 centavo) | Ganhou | `W` |
| `lost` com dinheiro, `won` que não fecha, `cancelReason`, `cashOutOdds`, estado novo | sobe cru | *(a conferir)* |

Medido: `won` 8 e `lost` 21 nas liquidadas da fixture, `open` 13 (ao vivo no mesmo dia, depois
de liquidar as abertas: 11 `won`, 31 `lost`, 6 `open`). O resto é a régua acima, travada por
clone no harness, **não** por amostra real. O bloco sempre leva
`Status (API): wagerUIState=… · state=… · wagerType=… · wagerId=…`.

---

## 6. Boost / promoção

Nenhum campo de boost na amostra. Se a casa passar a mandar, vale a regra global do `W`
(`retorno ÷ stake`) e o bilhete sobe "a conferir" até ser medido.

---

## 7. Cashout

`cashOutOdds` = `null` em toda a amostra liquidada. Sem amostra: o bloco sobe o valor e a odd
de cashout crus e diz "a conferir"; só retorno = stake vira `V` (rede do dinheiro). A regra
global (`MASTER_RESULTADO §5.1.2` e `§5.6`) se aplica quando o campo for medido.
`cashOutStatus`/`cashOutAmountThc` das abertas são a **oferta**, não dinheiro.

---

## 8. Bônus

`freeBet` = `null` em toda a amostra. Se vier número ou `{amount}` (em centavos), o bloco
escreve `Freebet incluído: X EUR`, o rótulo que o servidor lê (`freebets_do_texto`,
`MASTER_RESULTADO §5.8`). Em qualquer outra forma o cru sobe e o bilhete fica "a conferir".

---

## 9. Mapa de mercados (Thunderpick → `Aposta` global)

Só os mercados **confirmados** no dado real, e só onde a tradução é direta (camada fina):

| Thunderpick exibe (mercado) | Aposta global |
|---|---|
| `Match Winner` (CS2) | ML |
| `Match Handicap` (CS2) | Handicap |
| `Player <nome> - total points / rebounds / assists… (incl. overtime)` (basquete) | Player Props |

> `Round Handicap - Map N`, `Corners 1X2`, `Total Shots on Goal`, `Aces - Total` e os totais
> de time também aparecem na amostra: a categoria sai do `MASTER_APOSTAS` pelo objeto
> medido, sem atalho aqui. A descrição segue o `MASTER_DESCRICAO` em pt-BR.

---

## 10. Stake

Campo `amount`, em centavos de euro (÷ 100 no inject); a conversão para R$ é do `/salvar`.

---

## 11. Odds

- **A odd do bilhete é `odds`**, a mesma do card; na múltipla, já é o produto das pernas.
- **W:** a odd do card. `retorno ÷ stake` difere dela só no centavo do arredondamento (§5).
- **L e aberta:** `odds`. Na perdida ela **não** zera (13,38 no `C2225863`).
- Odd **nunca** truncada; decimal com vírgula.

---

## 12. Ruído a ignorar

- `homeScore`/`awayScore`, `isLive`, `matchId`, `eventId`, `marketId`, `selectionId`,
  `competitorId`, `winningSelectionId`, `marketBaseLine` (a linha sem sinal; a com sinal é
  `selectionTotal`), `period`, `hasImage`.
- `cashOutStatus`/`cashOutAmountThc` (oferta).
- Chamadas de `/api/` que não são as listas: o inject só aprende o token delas.

---

## 13. Pegadinhas (resumo rápido)

1. **Conta em EUR com tela em outra moeda**: a exibição usa o câmbio do dia (§1.1).
2. **Centavos**: `amount`/`outcome` ÷ 100 (§2.5).
3. **Duas séries de `wagerId`**: o prefixo `C`/`S` é obrigatório (§3).
4. **Total da 1ª página**: `skip` além do fim diz `totalWagersCount: 0` (§2.1).
5. **Arredondamento do retorno sem regra fixa** (§5).
6. **Esporte só por `gameId`** (§1.2).

---

## 14. Validações específicas

- [ ] A conta foi cadastrada em **EUR** antes da 1ª captura.
- [ ] Nenhuma aberta liquidada; nenhuma perdida com odd zero.
- [ ] Coluna Data = evento em São Paulo (a perdida, pela perna perdida).
- [ ] Contagem capturada == Settled + Open da casa.
- [ ] **1ª devolvida / cancelada / cashout / freebet:** salvar o JSON como fixture e trocar o
      clone do harness.
- [ ] **`gameId` novo** (aparece `gameId N, sem nome` no bloco): medir pela liga e somar ao mapa
      do `formatTicketTHP` e da §1.2.
- [ ] **Teto do `take`**: com mais de 100 liquidadas, conferir que todas chegaram.

---

## 15. Exemplos golden (bilhetes reais)

Recon de 22/10/2026 — conta inteira (**42 bilhetes**: 29 liquidadas, 13 abertas):
`extensor/harness/fixtures/thunderpick.resolved.json` e `thunderpick.pending.json` (a resposta
da casa, `uuid` zerado).

| Código | Tipo | Estado | Stake (EUR) | Odd | Retorno (EUR) | Colocação (SP) | Evento (SP) | Fonte |
|---|---|---|---|---|---|---|---|---|
| S4965610 | Simples CS2 | `won` | 43,83 | 1,62 | 71,00 | 25/04/2025 19:19 | 30/04/2025 12:10 | card |
| S4986447 | Simples CS2 | `won` | 22,00 | 1,55 | 34,10 | — | — | card |
| S4962247 | Simples CS2 | `won` | 44,02 | 1,65 | 72,63 | — | — | card |
| S4988241 | Simples CS2 ao vivo | `lost` | 22,03 | 2,8 | 0 | — | — | card |
| S10277912 | Simples NBA | `won` | 66,76 | 1,76 | 117,49 | 21/10/2026 20:52 | 21/10/2026 21:00 | JSON |
| C2225866 | Múltipla 3 NBA | `won` | 22,26 | 8,41 | 187,20 | 21/10/2026 21:56 | 21/10/2026 23:30 | JSON |
| C2225863 | Múltipla 3 NBA | `lost` | 22,26 | 13,38 | 0 | — | — | JSON |
| C2225869 | Múltipla 3 Euroleague (1 perna já ganha) | `open` | 22,26 | 14,78 | potencial 329,00 | — | — | JSON |

**Sem amostra:** devolvida · cancelada · cashout · freebet · boost · bet builder · sistema.

---

## 16. Roteiro da 1ª captura

1. Cadastrar a conta em **EUR**.
2. Atualizar a extensão (**SharpenUp 0.7.61**) e dar **Ctrl+Shift+R** na aba da Thunderpick
   **e** na aba do painel.
3. Abrir **My Bets** logado (não é obrigatório: o inject parte do token do `localStorage`).
4. Conectar → Copiar bilhetes. O toast diz `respostas` e `vistos`; com `semToken` a sessão
   não está logada.
5. Conferir no dashboard: contagem, código `C…`/`S…`, colocação, odd e moeda.
6. Na 1ª devolvida/cashout/freebet, cumprir os itens da §14.

---

## Feedback para a camada global / MODELO

1. **Conta numa moeda, tela noutra.** Primeira casa em que a moeda que o usuário vê não é a
   da conta, e a da tela flutua com o câmbio do dia. Quem cadastrar a conta pela tela erra a
   moeda; a mensagem do cadastro precisa dizer isso (pendente, `BACKLOG`).
2. **Duas séries de id no mesmo campo.** Prefixo de tipo no código resolve sem tocar no
   servidor; vale para qualquer casa com ids por tabela.
