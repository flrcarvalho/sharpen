# CASA_ESTRELABET
## Camada de tradução — `Estrela Bet` → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Estrela Bet.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Estrela Bet` — grafia **medida antes de registrar** (s303), nas 7 tabelas onde `casa` é texto: **41 bilhetes** (26 do dono `passapano`, 15 do `Feca`), **3 contas** em `parceiros`, 1 `casas_meta`, 1 `casa_config`. `ilike '%estrela%'` devolveu **uma única grafia** — zero variantes a unificar. Round-trip `_casa_display(_display_to_key(x))` rodado nas **69 grafias distintas** de `parceiros`: 0 quebradas.
- ⚠️ A **MARCA** escreve `EstrelaBet` (logo e título da página). A canônica do sistema é `Estrela Bet`, porque é a que a base usa. Registrar no `_CASA_DISPLAY` é mudança **retroativa** (ver `docs/SHARPENUP_ARQUITETURA.md §5`): a casa **já era usada por print**, então isto é *upgrade de print para API*, não cadastro.
- Domínio de captura: `estrelabet.bet.br` (operação regulada BR). O `estrelabet.com` aparece só nos 3 mapas de favicon, de antes, e **não** autoriza captura — mesmo critério da Pitaco e da 1xBet.
- Locale: pt-BR (rótulos em português)
- Formato numérico da TELA: **en-GB** — ponto decimal e vírgula de milhar (`R$1,727.40`, `11.01`) → converter para o padrão BR (`1.727,40`, `11,01`)
- Moeda: `R$`
- **Motor: Altenar / BIA** (`biahosted.com`) — o mesmo da VaideBet, Esportiva, Jogo de Ouro e Betpix365. É a **5ª casa** do motor. Ver §2.1.
- `Parceiro` / `Tipster`: preenchidos pelo app

> **Como se confirma o motor sem login:** abra a seção de **esportes** (a home de cassino não carrega o widget) e olhe o Network — `sb2frontend-altenar2.biahosted.com/api/widget/GetHighlights?…&integration=estrelabet` e `sb2wsdk-cdn-altenar2.biahosted.net`. O `integration` desta casa é **`estrelabet`**.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

**Captura por API + replay** (SharpenUp · `extensor/vb_inject.js` — o **mesmo** das outras quatro casas Altenar, sem uma linha de diferença). Antes disso a casa era de **print**.

```
POST https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory
{"culture":"pt-BR","timezoneOffset":180,"integration":"estrelabet","deviceType":1,
 "numFormat":"en-GB","countryCode":"BR","dateFrom":"…Z","dateTo":"…Z","liveOnly":false,
 "pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}
→ {"isLastPage":true,"bets":[…]}
```

**Onde o operador captura:** clique em **"Ver minhas apostas"** (rail direito da seção de esportes). Isso abre a **tela cheia** do histórico, com as abas `Aberto · Processado · Ganhou · Perdida · Cashout` e um seletor de datas.

**A superfície é a mais LISA das cinco casas do motor**, e isso foi medido, não suposto:

| | Jogo de Ouro | Betpix365 | **Estrela Bet** |
|---|---|---|---|
| Dispara o `widgetExpandedBetHistory`? | só na tela cheia | **nunca** (só o compacto) | **sim, sozinha** |
| Onde roda | iframe | página | **window de TOPO** |
| `clone().text()` passivo resolve? | sim | sim | **sim** |
| Custo para o operador | achar a tela certa | nenhum | nenhum |

**Prova da união de chaves** (o método barato da Faz1bet, `SHARPENUP_ARQUITETURA §4`): as **60 chaves aninhadas** dos 12 bilhetes reais desta conta são subconjunto exato das **77** das quatro irmãs — **zero campo novo**. As 17 ausentes são todas de *bet builder preenchido* (`bbOdds[].*`) e de *boost* (`boostedBet.*`, `boostedSelection.*`), que esta amostra não tem.

### 2.1.1 ⚠️ O gateway RECUSA `credentials:"include"` — e a falha é total, não parcial

O que esta casa tem de próprio **não está na tela, está no CORS**. O gateway responde
`Access-Control-Allow-Origin: *` para este tenant, e o navegador recusa a requisição com
credencial **antes de ela sair**:

| Chamada | Resultado | Amostras |
|---|---|---|
| `fetch(…, {credentials:"include"})` | `TypeError: Failed to fetch` | **3 de 3** |
| `fetch(…)` (sem credencial) | **200** · 8 bilhetes · `isLastPage:true` | **3 de 3** |
| `XHR` com `withCredentials = true` | erro de rede | 1 de 1 |

Até a s303 o replay do `vb_inject.js` mandava `credentials:"include"` fixo. Como **o replay
inteiro passa por ali**, isso não degradaria a captura desta casa: **zeraria a metade que
importa**. Medido com a mutação que restaura o código antigo: chegam **8 de 12** bilhetes —
as 8 resolvidas vêm pelo caminho passivo (a própria página as baixou) e **as 4 abertas
somem em silêncio**, porque só o replay pede a aba `Aberto`.

Perder a credencial **não custa autenticação**: quem autentica neste gateway é o
`Authorization: Bearer` dos headers aprendidos, não cookie (§2.2) — foi por isso que a
chamada sem credencial voltou 200 com os bilhetes da conta.

O `pedirPagina` do inject tenta **`include` primeiro** (o que as quatro irmãs usam hoje e
sabidamente funciona nelas) e cai para a chamada sem credencial em quem for recusado,
memorizando a escolha. A ordem é deliberada: **não temos conta nas outras quatro para medir
o CORS de cada tenant**, e inverter a ordem "porque o Bearer basta" seria mudar 4 casas em
produção por dedução. Os dois lados estão travados em `extensor/harness/casos/estrelabet.mjs §5`.

### 2.2 Autenticação

`Authorization: Bearer <JWT da sessão>`, header — **não** cookie. O endpoint é de outra
origem (`biahosted.com`), então o replay reusa os headers **exatos** da requisição que a
página fez. Sem eles volta 401.

### 2.3 Abas

Mesma URL; o discriminador é o array `statuses` do **corpo**:

| Aba da tela | `statuses` |
|---|---|
| Aberto | `[0, 10, 3, 20, 17]` |
| Processado | `[1, 8, 2, 4, 18]` |

O inject pede as **duas** a partir de uma requisição só, mais o `7` de propósito (ver
`CASA_VAIDEBET §5` — enum que nenhum filtro da casa pede e que sumiria dos dois lados).
O estado real vem no próprio bilhete (`status`), então não dependemos de saber qual aba
disparou.

### 2.4 Fim autoritativo

`isLastPage: true`. Paginação por `pageNumber`, 10 por página.

---

## 3. ID do bilhete

- Campo `id` no payload; a tela estampa o mesmo número no rodapé do card como `ID: 5346391363`.
- **Numérico de 10 dígitos** — mesmo espaço de IDs do motor Altenar (VaideBet, Esportiva, Jogo de Ouro, Betpix365).
- É a chave de dedup e o conteúdo do marcador `[Código: …]`. Reconhecido pela regex **genérica** do `repository.py` (`_ID_MARCADOR_RE`), sem regex por casa.

---

## 4. Data

- **A coluna Data do TSV sai do EVENTO mais recente** entre as seleções (`selections[].eventDate`), não da colocação — `MASTER_OUTPUT §4`.
- `createdDate` (colocação) vai junto no bloco, como contexto.
- **Os dois campos são UTC (`Z`) e precisam virar America/São_Paulo.** Na amostra, 3 dos 12 bilhetes têm colocação e evento em **dias diferentes** (colocado 28/08 23:40, jogo em 29/08) — usar a colocação gravaria no dia errado.
- ⚠️ **Armadilha ao conferir contra a tela:** o card já imprime em Brasília e o payload em UTC. O `5353319605` tem `eventDate` máximo em `2026-08-31T00:00:00Z`, que é **30/08 21:00** no TSV — copiar o dia do JSON põe a linha no dia seguinte.

---

## 5. Status e Resultado

Enum `status` do bilhete (o bloco emite cru em `Status (API): status=N`):

| `status` | Significado | Saída |
|---|---|---|
| `0` | Aberto | **vazio** (não liquidar) |
| `1` | Ganhou / Vencido | `W` |
| `2` | Perdido | `L` |
| `8` | Anulada | `V` (stake devolvido) |
| `4` e `18` | **Cashout** | `V` se o valor encerrado = stake · `W` com `Odd = cashout ÷ stake` se ≠ |
| outro | desconhecido | sobe cru, "a conferir" — **nunca** vira W/L |

Na amostra desta conta só apareceram `0`, `1` e `2`. O `8` vem do código compartilhado,
provado na Esportiva (`CASA_ESPORTIVA §5`, s285); o **cashout** (`4`/`18`) também, na s310
(`CASA_ESPORTIVA §5.4`), com três bilhetes reais e o filtro `statuses:[4,18]` da própria tela.

⚠️ **No cashout, `cashOutValue` e `partialCashOut` vêm ZERO** — o valor encerrado mora no
`totalWin`. É o `status` que diz que aquele `totalWin` é encerramento e não prêmio.

⚠️ **`totalWin` de bilhete ABERTO é o retorno POTENCIAL**, e vem preenchido. Os 4 abertos da
amostra estampam "Ganho total R$897.36 / R$1,115.39 / R$1,596.18 / R$1,797.15" com os jogos
ainda rolando (6', 34', 36'). Lê-lo como realizado vira **vitória fantasma** — o incidente
que a VaideBet levou a produção na s210. Só `status:1` autoriza `retorno ÷ stake`.

---

## 6. Boost / promoção

Sem amostra: nenhum dos 12 bilhetes tem `boostedBet` ou `boostedSelection`. O tratamento
existe no código compartilhado (o riscado do card é `preBoostedPrice` e a tela **trunca**) e
está travado em `CASA_ESPORTIVA §6`.

**Não confundir boost com a SuperMúltipla (§8)** — boost sobe a odd; a SuperMúltipla paga
por fora dela.

---

## 7. Cashout

- A tela oferece cashout em bilhete aberto (botões `Cashout R$51.23`, `R$150.00`, `R$119.40`
  nos 3 abertos com jogo em andamento), mas o payload traz **`cashOutValue: 0`** nos 12.
- O valor oferecido mora em `POST /api/WidgetCashout/GetOpenBetsCashoutValues`, outro
  endpoint — **e essa ausência é proteção, não defeito**: oferta de venda não pode virar
  cashout executado.
- **Cashout de verdade (executado) segue sem amostra nesta casa.** Quando vier, a regra é a
  global (`MASTER_RESULTADO §5.1.2` e `§5.6`), não desta casa.

---

## 8. Bônus — ⚠️ "SuperMúltipla" quebra `totalOdds`

O campo `bonus` é bônus de múltipla pago **por fora da odd**. Esta marca o estampa como
**`SuperMúltipla`** (com 🎁); a Betpix365 chama o **mesmo campo** de `Ganhos extra`. **O nome
do selo é da marca, o campo é do motor** — igual a `GOLDEN BOOST` × `TURBINADA` × `ODDS DE OURO`.

Medido no `5346391363`, o único W da conta. O card mostra **quatro** linhas:

```
Cotações totais           11.01        ← truncada na tela (payload: 11.015269)
Valor total da aposta     R$150.00
SuperMúltipla          🎁 R$75.11
Ganho total               R$1,727.40
```

`150 × 11,015269 = 1.652,29` **+ 75,11 = 1.727,40**, exato ao centavo.

**Consequência: `totalOdds` NÃO explica o retorno, e a régua do dinheiro vence** — a odd que
vai para o TSV é `Retorno ÷ Stake` = **11,516**, não os 11,015269 declarados (regra global do
W, `MASTER_RESULTADO`). Usar a declarada deixaria R$ 75,11 fora do P/L deste bilhete.

`bonus` também vem preenchido nos **4 abertos** (35,59 · 45,97 · 68,87 · 78,44), já somado ao
`totalWin` potencial — mais um motivo para não tratar potencial como realizado (§5).

---

## 9. Mapa de mercados (Estrela Bet → `Aposta` global)

Fonte de verdade das categorias: `MASTER_APOSTAS_2026 §3`. Este mapa lista **apenas** os
mercados já confirmados num bilhete real **desta** casa (camada fina).

> ⚠️ **Espelho compartilha CÓDIGO, não DICIONÁRIO.** O mesmo motor entrega rótulos
> diferentes por tenant (foi o `2º Tempo -` × `2º metade -` de Betfast × Faz1bet, s284).
> Copiar o §9 da irmã deixaria rótulo sem correspondência. Todos os 13 abaixo saíram do
> payload real desta conta.

| Estrela Bet exibe | Aposta global | Status |
|---|---|---|
| `Vencedor (incluindo Prorrogação)` | ML | ✓ confirmado |
| `Empate devolve aposta` | DNB | ✓ confirmado (`MASTER_APOSTAS §DNB`, sinônimo "Empate anula aposta") |
| `Handicap (incluindo Prorrogação)` | Handicap | ✓ confirmado |
| `Total de Gols (incluindo linhas Asiáticas)` | Gols | ✓ confirmado |
| `1º tempo - total` (basquete) | Pontos | ✓ confirmado (o objeto manda; recorte `1ºT` vai na descrição) |
| `Total de Escanteios` · `<Time> total de escanteios` | Escanteios | ✓ confirmado |
| `1X2 de cartões` | Cartões | ✓ confirmado |
| `1X2 de faltas` | Faltas | ✓ confirmado |
| `Total de Impedimentos` · `<Time> total de impedimentos` | Impedimentos | ✓ confirmado |
| `Total de chutes <Time>` | Chutes | ✓ confirmado |
| `Total de chutes a Gol <Time>` | **Chutes no Gol** | ✓ confirmado |
| `Hits Mais de/Menos de (incluindo innings extra)` | **Outros ⚠️** | ver pendência abaixo |
| (mercado não mapeado) | Outros | ✓ fallback |

> ⚠️ **`Chutes` × `Chutes no Gol` convivem nesta casa com rótulos quase homógrafos** — a
> mesma armadilha da Esportiva (s254). `Total de chutes CS Maritimo` são **finalizações**
> (`Chutes`); `Total de chutes a Gol Le Havre` é **SOT** (`Chutes no Gol`). São categorias
> **diferentes** no `MASTER_APOSTAS §3`, e o que separa é o `a Gol`.

**Pendência de MASTER (decisão do Feca, não conserto):** `Hits Mais de/Menos de (incluindo
innings extra)` é total de *rebatidas válidas* do jogo de baseball. O `MASTER_APOSTAS
§Baseball` só prevê `Corridas` (runs/RBIs) e `Player Props` (estatística individual) —
**hits de time não tem gaveta**, e `Corridas` mede outra coisa. Fica em `Outros` até a
categoria ser decidida; criar uma aqui dispararia a **regra de propagação obrigatória** do
`CLAUDE.md`, que é decisão, não correção. Dois bilhetes da amostra usam este mercado.

**Notas de reconstrução:**
- Separador de times: `vs.` (`Zwolle vs. Nijmegen`) → normalizar para `[Zwolle v Nijmegen]` (lowercase `v`, colchetes).
- Odd e dinheiro da tela em **en-GB** (ponto decimal, vírgula de milhar): `11.01` → `11,01`; `R$1,727.40` → `1.727,40`.
- **`Mais de X` / `Menos de X` → `Over X` / `Under X`** (`MASTER_DESCRICAO §11`).
- Recorte temporal: `1º tempo - total` → manter o recorte na descrição (`MASTER_DESCRICAO §12.10`; ausência de sufixo significa **partida inteira**).
- Múltipla: separador ` // ` entre seleções (`MASTER_DESCRICAO §16`).
- Placar do jogo (`2:1`) e `gameTime` (`36'`) ao lado do confronto → estado do jogo, **fora** da descrição.
- `pitcherInfo` (arremessadores, no baseball) → ruído para o TSV; ignorar.

---

## 10. Stake

- Campo `Valor total da aposta R$XX.XX` na tela = `totalStake` (também em `unitStake` e `finalStake`; os três batem nos 12 bilhetes).
- Valores em **reais**, não em milésimos.
- Stake quebrada existe: o `5347925916` é `R$113.63`.

---

## 11. Odds

- `totalOdds` é a odd estrutural do bilhete.
- ⚠️ **A tela TRUNCA em 2 casas** (não arredonda): `9.660625 → 9.66`, `11.912784 → 11.91`, `13.050109 → 13.05`. Vale também para a odd de cada seleção (`1.9091 → 1.90`, `2.625 → 2.62`, `1.7143 → 1.71`). **A odd nunca é truncada no bloco** — regra primordial.
- **No W vale a régua global do dinheiro** (`Retorno ÷ Stake`), e nesta casa ela **diverge** de `totalOdds` sempre que houver `bonus` — ver §8.
- `totalOdds` **não zera** em bilhete perdido (ao contrário do `betOdds` da KTO).

---

## 12. Esporte

O payload **não traz o nome** do esporte, só ids. Mapa confirmado nesta casa:

| `sportTypeId` | `sportId` | Esporte (valor oficial do `MASTER_ESPORTES`) |
|---|---|---|
| `1` | `66` | `Futebol` |
| `12` | `67` | `Basquete` |
| `13` | `76` | `Baseball` |

São os três **com amostra nesta casa**. O mapa do código é do **motor** e hoje tem **16 ids**
— a lista inteira, os 9 deixados crus de propósito e o `sportTypeId 300` (que **não é
esporte**, é a gaveta de especiais) estão em
[`CASA_ESPORTIVA §12.1` e `§12.2`](CASA_ESPORTIVA.md).

O `12` entrou na s303, provado por **dois eixos independentes**, nenhum deles dedução a
partir do nome do time:

1. toda seleção com `sportTypeId:12` traz `sportId:67`, e **a própria API da casa nomeia
   esse id** — `GetHighlights` devolve `{"id":67,"name":"Basquete"}` (e 66=Futebol, 76=Beisebol,
   que batem com os `sportTypeId` 1 e 13 já mapeados);
2. as 8 seleções da amostra são basquete real (WNBA, LNBP, CIBACOPA, FIBA Asia), com mercados
   de basquete (`1º tempo - total Mais de 83.5`, `Handicap (+11.5)`).

> O eixo 1 virou método na s310: **`GetAllSports` devolve `{typeId, id, name}` no mesmo
> objeto**, sem login, para os 25 esportes de uma vez. O mapa parou de crescer de bilhete em
> bilhete — id novo não precisa mais esperar amostra.

⚠️ **O rótulo escrito no bloco TEM de ser o valor OFICIAL do MASTER — a IA copia verbatim.**
A casa exibe `Beisebol` no menu, que é **sinônimo de entrada**; a saída é `Baseball`. Foi
assim que a VaideBet gravou duas grafias do mesmo esporte no banco (s210).

⚠️ **`Basquete` ≠ `eBasket`** (`MASTER_ESPORTES §Regra Crítica`). Esta casa lista
`E-Basquete` como **sport próprio** no menu, ao lado de `Basquete` — o que é indício de que
não mistura os dois no `sportTypeId 12`. **Não há bilhete de basquete virtual na amostra
para provar**; fica declarado como limite.

Id fora do mapa sobe cru e marcado "a conferir" — nunca vira esporte inventado.

---

## 13. Ruído a ignorar

- Placar (`eventScore`, `2:1`) e tempo de jogo (`gameTime`, `36'`) — estado do jogo.
- `pitcherInfo` (baseball) — a tela mostra "Soriano, Jose (Mão: Dir)".
- `Tipo de Dispositivo Usado: Desktop` no rodapé do card (`device: 0`).
- Ícones e selo `SuperMúltipla` — o valor está em `bonus` (§8).

---

## 14. ⚠️ TAB LITERAL no nome do time — o dicionário deste tenant corrompe TSV

Medido nesta casa (s303), e **é dado real, não corrompido no transporte**:

```
"eventName": "Real Sociedad vs. RCD Espanyol\t\t"      ← bilhete 5347925916
"name":      "RCD Espanyol\t\t"
"eventName": "Mirassol  vs. Palmeiras"                 ← espaço DUPLO
"eventName": "MK Dons (F) vs.  Queens Park Rangers (F)"
```

O menu da própria casa traz `"E-sports +\t\t"`, então é do dicionário do tenant, não do bilhete.

**Por que importa:** TAB é o **separador de coluna do TSV** (`MASTER_OUTPUT`), e a IA copia
nome próprio **verbatim** — é justamente a premissa em que o gate de fidelidade da s302 se
apoia. Um TAB copiado para a coluna Descrição empurra Stake/Odd/Resultado uma casa à direita,
e o `parse_tsv` passa a ler o **código do bilhete** no lugar do resultado. É a família do bug
da s193, com outra origem.

**Nenhum gate existente pegaria:** `checar_descricao` olha forma, `checar_fidelidade` confere
nome por *substring* (e o nome COM tab contém o nome sem tab), e o financeiro fica certo
porque stake/odd/resultado são copiados do bloco.

**Correção (s303):** `_limpoVB` no `content.js` colapsa qualquer corrida de espaço em branco
e apara as pontas antes de o nome entrar no bloco. As 4 irmãs também tinham nome com espaço
final (`"Náutico vs. Ceará "`) e passam a sair aparadas — que é o certo. Travado em
`extensor/harness/casos/estrelabet.mjs §6`, com a fixture guardando o TAB de verdade (se
alguém "limpar" o JSON, o caso acusa que deixou de testar).

---

## 15. Pegadinhas (resumo rápido)

1. **`credentials:"include"` é recusado pelo gateway** — sem o fallback, chegam 8 de 12 e as **abertas somem em silêncio** (§2.1.1).
2. **TAB literal no nome do time** parte a coluna do TSV (§14).
3. **`bonus` (SuperMúltipla) é pago por fora da odd** — `totalOdds` não explica o retorno no W (§8).
4. **`totalWin` de aberta é POTENCIAL** e vem preenchido — vitória fantasma (§5).
5. **A tela trunca a odd** em 2 casas, no bilhete e na seleção (§11).
6. **Data do TSV é a do EVENTO**, em UTC, e diverge da colocação em dia (§4).
7. **`cashOutValue: 0` mesmo com botão de cashout ativo** — e isso é proteção (§7).
8. **`Chutes` × `Chutes no Gol`** com rótulos quase homógrafos (§9).
9. **`Beisebol` é sinônimo de entrada; a saída é `Baseball`** (§12).

---

## 16. Validações específicas

- [ ] Todo bilhete tem `[Código: <10 dígitos>]` na 1ª linha do bloco.
- [ ] Nenhum bloco emitido contém TAB literal.
- [ ] Bilhete `status:0` sai com Resultado **vazio** e sem linha `Retorno:`.
- [ ] W com `bonus` > 0 sai com odd = `Retorno ÷ Stake`, não `totalOdds`.
- [ ] Odd nunca truncada em 2 casas.
- [ ] Data da coluna 1 = evento mais recente, convertido para Brasília.
- [ ] `sportTypeId` fora dos 16 mapeados (`CASA_ESPORTIVA §12.1`) sai marcado "a conferir" — e o `300` sai como **aposta especial**, nunca como esporte.
- [ ] `Hits Mais de/Menos de` continua caindo em `Outros` enquanto a categoria não for decidida.

---

## 17. Amostra do reconhecimento (30/08/2026)

Conta pequena e recente: **12 bilhetes no total** (o replay de 730 dias devolve os mesmos,
com `isLastPage:true` na página 1). Todos são **múltiplas de 3 pernas**.

| | |
|---|---|
| Resolvidas | 8 (1 × `status:1`, 7 × `status:2`) |
| Abertas | 4 (`status:0`) |
| Esportes | Futebol, Basquete, Baseball |
| Sem amostra | anulada (`8`), cashout executado, bet builder, boost, paginação > 1 página, eBasket |

---

## Feedback para a camada global

- **Pendência de categoria:** `Hits` (baseball, total do time) não tem gaveta no `MASTER_APOSTAS §Baseball` — hoje cai em `Outros`. Ver §9.
- **Higiene de nome vinda da casa** virou tratamento no formatador (§14); nada mudou no MASTER.

---

VERSÃO: 2026
ATUALIZADO: 2026-08-30 (sessão 303 — nasce a casa na camada de captura; 5ª do motor Altenar)
