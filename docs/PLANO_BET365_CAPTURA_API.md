# PLANO — Bet365 como casa de captura passiva (sportshistoryapi)

> **Status:** especificação aprovada (sessão 22/07/2026). Modelo **validado ponta a
> ponta** em dados reais capturados pelo Feca (F12). Falta escrever o código.
> **Fonte de verdade de marca/UI:** `pack/CLAUDE.md`. Este doc é o **plano técnico**;
> ao construir, o comportamento de dedup segue `app/repository.py` (código é a verdade).
>
> **Motivação:** a Bet365 pela página de resultados nunca deu extração decente (hoje é
> **modo visão/screenshot** — ver `casas/CASA_BET365.md §2`). Mas a Bet365 tem uma API de
> histórico (`/sportshistoryapi/…`) que devolve **tudo estruturado**, inclusive o que
> faltava: resultado exato, código estável do bilhete e uma âncora confiável para a **data
> de encerramento**. Isto promove a Bet365 de *print* para **texto passivo** — o mesmo
> modelo da Betfair (`bf_inject.js`) e da Pinnacle (`pn_inject.js`).

---

## 1. Endpoints

Base autenticada por sessão: `https://members.bet365.bet.br`

| Chamada | Para quê |
|---|---|
| `GET /sportshistoryapi/summary?settled={0\|1}&lid=33&cid=28&csid=0&from={ISO}&to={ISO}` | **Lista** de bilhetes. `settled=1` = resolvidas · `settled=0` = pendentes. |
| `GET /sportshistoryapi/confirmation?settled={0\|1}&lid=33&cid=28&bsid={ID}&cr={0\|1}` | **Detalhe** de 1 bilhete (jogo, mercado, liga, **código `BR`**, cashout). |
| `GET /pam/ui-historymenuapi/menu?...&lid=33&cid=28` | Menu do histórico (de onde saem `lid`/`cid` e os rótulos `BSSB`/`BSUB`). |

- `lid=33`, `cid=28` são estáveis na sessão (vêm do `menu`). `csid=0`.
- **`summary` NÃO traz jogo/mercado/liga nem o código `BR`** — só a seleção crua, odd,
  stake, retorno e o esporte (`CL`). Para a linha completa é **obrigatório** o
  `confirmation` de cada bilhete (N+1 chamadas — aceitável).
- Corpo das respostas: `text/plain` no formato proprietário `F|00;chave=valor;…|01;…|`.

### 1.1 Paginação (cursor `PT`)

A lista é paginada por cursor no parâmetro **`to`**, com `from` fixo:
1. 1ª chamada: `from`=início da janela, `to`=agora.
2. A resposta traz no registro `00` um campo **`PT=<ISO>`**.
3. Próxima página: repetir com **`to = PT`** da resposta anterior. Repetir até esgotar.

A própria página faz isso quando o usuário **rola a lista** (scroll infinito). Ver §7
para passivo (scroll) vs ativo (replay).

---

## 2. Decodificação do formato `F|…`

Registros separados por `|`; dentro de cada um, pares `chave=valor` por `;`. O 1º token
de cada registro é o **código do registro** (`00`, `01`, `02`, `03`).

### 2.1 `summary` (lista)

| Registro | Campos que importam |
|---|---|
| `00` header | `PT` = **cursor de paginação** (vira o `to` da próxima página) |
| `01` bilhete | `ID` (numérico — **NÃO estável**, ver §6) · `BS` (**0=aberta, 1=resolvida**) · `BT` (1=simples, 2=combo/duplas) · `BC` (nº de seleções) · `TP` (**colocação**, `YYYYMMDDHHMMSSmmm`, hora servidor) · `PD` (contém `C<ID>` e `BSSB`/`BSUB` + `D0`/`D1`) |
| `02;TY=SR` | abre bloco de seleções |
| `03` seleção | `NA`/`FN` (seleção) · `OD` (odd fracionária) · `CL` (esporte, §4) |
| `02;TY=SD` | `NA` (tipo: `Simples`/`Duplas`) · `ST` (stake) · `TS` (stake total) · `BT` |
| `02;TY=ST` | `ST` (stake) · **`RT`** (retorno — **AUSENTE quando aberta**) |

### 2.2 `confirmation` (detalhe)

| Registro | Campos que importam |
|---|---|
| `00` cabeçalho | **`BR`** (código do comprovante — **CHAVE DE DEDUP**, §6) · `DA` (**colocação**, hora servidor) · `BS` (0/1) · `BT` · `BC` · `NA` (tipo) |
| `01;TY=SR` | `ST` (stake) |
| `02` (tem `FN`) = **perna** | `NA` (seleção) · `OD` · **`TP`** (**kickoff do jogo**, hora servidor — âncora da data de encerramento, §5) · `CL` · `L3` (liga) · `FN` (jogo) · `MN` (mercado) |
| `02;DE=…` (só combos) | combinações do sistema (`1/2`, `1/3`…), odd combinada, `RT` potencial por combo |
| `01;…;TY=CS` (linha final) | `WD` (ganho) · `TR` (retorno total) · `RT` (retorno) · `TS` (stake total) · `US` (unit stake) |
| `01;TY=DI` + `02;SY=DI/TO` | KYC/local: cidade, device, **nome, endereço, CPF** → **IGNORAR** (dado sensível, nunca vai pra planilha nem pro banco) |

---

## 3. Aberta vs resolvida

Três sinais concordantes (usar `BS` como autoritativo):
- `BS=0` (aberta) vs `BS=1` (resolvida) — **autoritativo**.
- `PD` contém `BSUB` (unsettled) vs `BSSB` (settled).
- No `summary`, a aberta **não tem `RT`**; a resolvida tem.

Aberta → `Resultado` **vazio**, sobe como `aberta` (padrão Betano/Pinnacle:
[[betano_abertas_e_upsert]] / [[pinnacle_sharpenup]]). Quando resolve, o UPSERT por
código preenche o resultado (§6).

> ⚠️ **Armadilha:** no `confirmation`, o campo `RT` de uma **aberta** é o retorno
> **potencial** (não realizado). Nunca derivar resultado do `RT` do confirmation — usar
> `BS` + o `RT` do **summary** (que só existe quando resolvida).

---

## 4. Esporte (`CL`) — mapa

| `CL` | Esporte |
|---|---|
| 1 | Futebol |
| 13 | Tênis |
| 18 | Basquete |
| 94 | Badminton |
| 15 | **? — a confirmar** (visto em "Mais de 13.5") |
| 151 | **? — a confirmar** (visto em "Mais de 11.5") |

- **eSoccer / eSports:** vem com `CL=1` (não distingue de futebol real). O sinal é o
  **handle do gamer entre parênteses** — ex.: `Croatia (hotShot)`, `Norway (RossFCDK)`.
  Mesma lógica do eBasket ([[ebasket_e_categoria_pontos]]). Tratar na categorização.
- **Múltiplos:** aplica a regra vigente — combo com **3+ seleções de jogos diferentes**
  (ou mistura de esportes) → esporte `Múltiplos` ([[multiplos_regra_jogos_diferentes]]).
  Validado no PoC (aposta `CR4983554651I`, 3 pernas MLS → `Múltiplos`).

---

## 5. Data de encerramento

Não existe carimbo de liquidação para o caso **normal** (fim de jogo) — confirmado
varrendo os payloads completos. Dois caminhos:

1. **Liquidação normal:** `data_encerramento = kickoff (TP da perna) + folga do esporte`.
   Para combos, usar a perna que liquida **por último** (maior `TP`+folga). Ruído só em
   jogo que cruza a meia-noite — e a folga já corrige a maioria.

   | `CL` | Esporte | Folga (kickoff→liquidação) |
   |---|---|---|
   | 1 | Futebol | +2h30 |
   | 18 | Basquete | +2h30 |
   | 13 | Tênis | +3h |
   | 94 | Badminton | +1h30 |
   | (default) | — | +2h30 |

2. **Cashout ("Encerrar Aposta"):** o `confirmation` traz um bloco **"Encerrar Aposta –
   Histórico"** com **Data/Hora EXATA** do encerramento. Quando existir, usar essa data
   (melhor que kickoff+folga).
   > 🔲 **Pendente:** mapear o **nome exato do campo** desse bloco no payload `F|…` — o
   > cashout capturado até agora foi de valor cheio (aposta vencedora encerrada faltando
   > 1 min). Precisa de **1 payload cru de cashout "quebrado"** (valor ≠ retorno cheio).

### 5.1 Fuso

Timestamps (`TP`, `DA`) vêm em **hora de servidor (Reino Unido / `Europe/London`)**.
Converter para Brasília via `Europe/London → America/Sao_Paulo` (**−4h no verão britânico,
−3h no inverno**). **Validado:** Croatia colocada `04:32:58` UK → `00:32:58` Brasília
(bateu com a tela). Regra de fuso do front: [[data_fuso_local_nunca_utc]].

---

## 6. Deduplicação — **chave = código `BR`**

**Validado com a MESMA aposta capturada aberta e depois resolvida (`Croatia hotShot`):**

| Campo | Aberta | Resolvida | Estável? |
|---|---|---|---|
| `ID` numérico (summary) | `3134517985033890854` | `49634495897` | ❌ **muda** (namespace `D1`→`D0`) |
| **`BR` (confirmation)** | `QR1535188621F` | `QR1535188621F` | ✅ **estável** |

- **Chave de dedup = `BR`** (código do comprovante). O `ID` numérico do summary **muda**
  quando a aposta resolve → **não serve**. O `ID` serve só como `bsid` para buscar o
  `confirmation` **dentro da mesma visão**.
- `BR` na coluna interna **`Código`** (`MASTER_OUTPUT §11ª coluna`).
- Aberta hoje + resolvida amanhã → mesmo `BR` → **UPSERT na mesma linha** (vazio não
  rebaixa resolvida; resolvida preenche a aberta — [[betano_abertas_e_upsert]]).
- Implementação: `_assinatura()`/`upsert_bilhetes()` em `app/repository.py` devem chavear
  pelo código quando houver (código é a verdade).

---

## 7. Arquitetura (segue Betfair/Pinnacle)

Novo inject **`extensor/b3_inject.js`** (mundo MAIN), fiado no `content.js`
(`roboBet365Passive`), host `members.bet365.bet.br`. `casas/CASA_BET365.md §2` passa de
**modo visão** para **modo texto** (robô colhe dado exato, dedup por código).

**Fluxo:** hook `fetch`/`XHR` → filtra `/sportshistoryapi/summary` e `confirmation` →
parseia o `F|…` → para cada bilhete da lista, busca o `confirmation` (jogo/mercado/`BR`) →
monta um **bloco de texto marcado `[Código: BR…]`** por bilhete (igual Betfair/Pinnacle) →
backend split/dedupa pelo código. Roda as **duas listas** numa rodada: `settled=1`
(resolvidas, janela de dias) **e** `settled=0` (abertas, todas).

### 7.1 Passivo (scroll) vs ativo (replay) — o nó do token

O cabeçalho **`x-net-sync-term` ROTACIONA a cada requisição** (confirmado: mesmo
`x-request-id`, sufixos diferentes). Logo:
- **Forjar requisição do zero é inviável** (não dá pra gerar o token) → descartado o
  "Sharpen monta a URL sozinho".
- **Replay estilo `bf_inject`** (re-emitir com `credentials:include` reaproveitando os
  headers capturados da 1ª requisição, avançando o cursor `to`): **testar** — o token
  capturado pode ser aceito ou recusado por ser de uso único. **Se funcionar**, paginação
  ativa como a Betfair. **Se recusar**, cair no…
- **Passivo puro (scroll-driven):** o inject acompanha as respostas que a **própria
  página** dispara ao rolar a lista (a página gera o token fresco). O robô rola a lista
  até esgotar. Zero risco de anti-bot. **É o fallback garantido.**

A UI que o Feca desenhou (Pendentes/Resolvidas × 24h/48h/Intervalo) **já existe nativa na
Bet365** — no passivo, o operador escolhe o filtro lá e o Sharpen captura.

---

## 8. Resultado / cashout (regra global)

- `BS=0` → aberta (`Resultado` vazio).
- `BS=1`, do `RT` do **summary** vs stake (`MASTER_RESULTADO`):
  - `RT=0` → **L**
  - `RT=ST` → **V**
  - `RT=ST×odd` (cheio) → **W**
  - `ST<RT<cheio` → **HW** · `0<RT<ST` → **HL**
- **Cashout** (`RT ≠ cheio`, detectado pelo bloco "Encerrar Aposta"): `Cashout≠stake` →
  **W**, `Odd = Cashout ÷ Stake`; `Cashout=stake` → **V** (regra de cashout do
  `MASTER_RESULTADO §5.1.2/§5.6`; resumo em `CLAUDE.md`). Validado: Croatia stake R$1 →
  cashout R$1,50 → W, odd 1,50.
- **Odd sempre em precisão completa** ([[feedback_odd_precisao_completa]]): `OD` fracionária
  → decimal = `num/den + 1`. Encurtar só no display, nunca no cálculo/export.

---

## 9. Plano de build (faseado — uma etapa por vez)

- **Fase 1 — parser + inject passivo.** `b3_inject.js` (hook + parse `F|…` + busca
  `confirmation` por bilhete) · `roboBet365Passive` no `content.js` · saída em blocos
  `[Código: BR…]` · `CASA_BET365 §2` → modo texto. Mapa `CL`, offsets, fuso London→SP.
- **Fase 2 — paginação.** Testar replay ativo (token); se recusar, scroll-driven. Seguir
  o cursor `PT` até esgotar as duas listas.
- **Fase 3 — dedup + abertas.** Garantir chave por `BR` em `_assinatura/upsert_bilhetes`;
  UPSERT aberta→resolvida.
- **Fase 4 — categorização fina.** eSoccer via handle `(…)`, mercados `MN`→categorias
  (`MASTER_APOSTAS`), `CL=15`/`CL=151`. Bumpar `version` no `manifest.json` a cada release.

---

## 10. Pendências / decisões para o Feca

1. 🔲 **Payload cru de um cashout "quebrado"** (valor ≠ retorno cheio) → mapear o campo de
   valor e a **data/hora** do bloco "Encerrar Aposta".
2. 🔲 **`CL=15` e `CL=151`** = quais esportes? (aparecem em "Mais de 13.5" e "Mais de 11.5").
3. 🔲 **Offsets por esporte** (§5) — os valores propostos servem?
4. 🔲 **Parse no inject (JS)** — como Betfair/Pinnacle — vs parse no servidor (Python).
   Recomendação: **JS no content/inject** (dado já exato, casa com a arquitetura atual).

---

## Anexo — PoC validado (scratchpad, sessão 22/07/2026)

Parser standalone rodado sobre os payloads reais capturados confirmou: parse do `F|…`,
resultado W/L/V, aberta vs resolvida, data de encerramento (kickoff+folga; cashout exato),
regra dos múltiplos, fuso −4h e **dedup por `BR` estável**. Nada persistido; prova de
conceito descartável.
