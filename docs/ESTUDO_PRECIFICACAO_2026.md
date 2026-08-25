# ESTUDO — Precificação do apostador (Sharpen SaaS)

> **Status:** estudo concluído em 2026-08-24 (sessão 295). **As correções A e C já foram
> APLICADAS** (s295); a **B está bloqueada** — ver `PLANO_TRADUTOR_DETERMINISTICO.md §IV.6`.
> A decisão de produto que saiu deste estudo é o **tradutor determinístico** (plano ao lado):
> as correções de cache são analgésico, não a cura.
> Fonte dos números: medição direta no Postgres de produção (`uso_tokens`, `bilhetes`,
> `parceiros`) + `messages.count_tokens` da API Anthropic. Janela: **30 dias (25/07 a 24/08/2026)**.
> Câmbio: **PTAX de 24/08/2026 = R$ 5,1512** (venda, Banco Central).
>
> **Teto de preço definido pelo Feca: R$ 149/mês.** Nenhum plano acima disso.
>
> Frentes relacionadas: `PLANO_MULTIUSUARIO_2026.md` (Fase 4 = pagamento, não iniciada) ·
> `../Ideias/Estudo_Assinatura_Tipsters_Sharpen.pdf` (outro negócio: assinatura DO tipster).

---

## 0. Resumo em cinco linhas

1. O custo real hoje é **R$ 0,077 por bilhete** — 36 % acima da estimativa de 04/07 (s107), que
   nunca tinha sido conferida contra dado real.
2. Existe **um custo invisível de ~US$ 173/mês** (o `_cache_warmer`) que **não aparece em
   `uso_tokens`** porque `registrar_uso` só roda no caminho da extração. O custo verdadeiro é
   **~US$ 402/mês (≈ R$ 2.071)**, não os US$ 228 que a tabela mostra.
3. **Com o custo de hoje, R$ 149 não fecha.** Um usuário de 20 contas custa R$ 278/mês em token.
4. Quatro correções levam o custo a **R$ 0,028/bilhete** (−63 %). Três delas são baratas; a quarta
   (parser determinístico da Bet365) é a que já estava no plano desde a s107.
5. **Depois delas o teto de R$ 149 fecha com 31–69 % de margem bruta.** O parser deixa de ser
   "otimização" e passa a ser **pré-condição do modelo de preço**.

---

## 1. Onde está o custo — medido, não estimado

### 1.1 O agregado

| Métrica | Valor |
|---|---|
| Custo registrado em `uso_tokens` (30 d) | **US$ 228,63** ≈ R$ 1.177 |
| Custo do `_cache_warmer` (não registrado — ver §2.1) | **≈ US$ 173** ≈ R$ 891 |
| **Custo real de API** | **≈ US$ 402/mês ≈ R$ 2.071** |
| Chamadas ao modelo | 1.050 (35/dia) |
| Bilhetes novos por extração | 15.278 |
| **Custo por bilhete (variável)** | **US$ 0,0150 = R$ 0,0773** |
| Modelo | `claude-sonnet-4-6`, único em uso |
| Infra (Railway: app + Postgres + bot) | **NÃO MEDIDO** — ver §5.3 |

### 1.2 Por dono (30 d) — a conta é concentrada em dois

| Dono | US$ | Bilhetes novos | Contas ativas | US$/bilhete |
|---|---|---|---|---|
| **Feca** | **83,11** | 4.890 | 28 | 0,0170 |
| **Gabriel** | **74,39** | 3.162 | 14 | 0,0235 |
| **Jonathan** | **28,35** | 2.702 | 15 | 0,0105 |
| WilliamOliveira | 14,18 | 1.774 | 9 | 0,0080 |
| Jaao26 | 5,43 | 96 | 2 | 0,0566 |
| perereca | 5,05 | 622 | 1 | 0,0081 |
| Tonelada | 4,03 | 453 | 4 | 0,0089 |
| Diogo | 3,53 | 32 | 8 | 0,1104 |
| LavaPessoal | 2,60 | 195 | 2 | 0,0133 |
| Lava | 2,06 | 173 | 1 | 0,0119 |
| outros 6 | ≤ 1,76 cada | — | — | — |

**Feca + Gabriel = 69 % de toda a fatura.** A mediana dos 16 donos com custo é ~US$ 2,60/mês.

> **Sobre o Fatuch:** ele **não tem custo de token**. A base dele é lida da **planilha ao vivo**
> (`planilha_url`, Google Apps Script), não do Postgres — não passa pela IA. O que existe é
> `LavaFatuch`, com **US$ 1,55 em 5 chamadas num único dia (21/08)**. Se a pergunta era "quanto o
> Fatuch me custa", a resposta é **praticamente zero**. O segundo maior gasto não é ele, é o
> **Gabriel**.

### 1.3 Por casa — a Bet365 é quase metade

| Casa | US$ 30 d | % do total | Bilhetes |
|---|---|---|---|
| **Bet365** | **99,33** | **43 %** | 511 |
| Betano | 32,27 | 14 % | 125 |
| Pinnacle | 15,42 | 7 % | 78 |
| Superbet | 13,79 | 6 % | 78 |
| Betfast | 13,30 | 6 % | 42 |
| Betfair | 7,98 | 3 % | 30 |
| outras 15 | 46,54 | 20 % | — |

### 1.4 Por componente de token — só 39 % é trabalho entregue

| Componente | Tokens 30 d | US$/MTok | US$ | % |
|---|---|---|---|---|
| **Output** (o TSV que a IA escreve) | 6,00 M | 15,00 | **90,00** | 39 % |
| **Cache write** (regravar o prompt) | 14,42 M | 3,75 | **54,08** | 24 % |
| **Cache read** (reler o prompt) | 165,07 M | 0,30 | **49,52** | 22 % |
| **Input** (o bilhete em si) | 11,67 M | 3,00 | **35,01** | 15 % |
| | | | **228,63** | |

**Leitura:** 46 % da conta (`cache write` + `cache read`) é o **prompt de sistema sendo relido e
reescrito** — não tem nada a ver com quantos bilhetes o usuário mandou. É overhead fixo por
chamada, e é aí que está o dinheiro fácil.

---

## 2. Os quatro vazamentos

### 2.1 O `_cache_warmer` custa mais do que economiza — e é invisível

**O que ele faz** (`app/main.py:240`): a cada **240 s**, dispara uma chamada com
`system=build_system("SUPERBET")` e `max_tokens=1`, para manter o cache dos masters vivo
(TTL padrão = 5 min).

**Tamanho medido do prompt** (via `messages.count_tokens`, exato):

| Bloco | Tokens |
|---|---|
| 6 masters globais (breakpoint 1) | **44.593** |
| + `CASA_SUPERBET` (breakpoint 2) | 53.555 |
| + `CASA_BET365` | 55.642 |
| + `CASA_BETANO` | 49.442 |

**A conta do warmer:** 360 pings/dia × 53.555 tokens × US$ 0,30/MTok = **US$ 5,78/dia ≈
US$ 173/mês**. Isso **não entra em `uso_tokens`** — `registrar_uso` só é chamado dentro de
`_stream_seq` / `_stream_parallel`.

**A prova de que ele roda mesmo** (medição, não dedução): das casas com ≥ 8 chamadas em 60 dias,
**a Superbet é a única com `cache_write = 0` em 100 % das chamadas — 130 de 130.** Bet365 paga em
41 % delas, Betfair em 96 %. O warmer aquece **exatamente uma casa**, a que está escrita no código.

**E ele não se paga.** Distribuição do intervalo entre chamadas consecutivas (30 d):

| Intervalo | Chamadas | % | O warmer ajuda? |
|---|---|---|---|
| ≤ 5 min | 643 | **61,2 %** | **Não** — o tráfego real já mantém o cache quente sozinho |
| 5 min – 1 h | 279 | 26,6 % | Só se o TTL fosse de 1 h |
| > 1 h | 127 | 12,1 % | Frio de qualquer jeito |

Sem o warmer, apenas as 406 chamadas das duas últimas faixas pagariam a escrita dos masters
(44.593 × US$ 3,75/MTok = US$ 0,167 cada) = **US$ 68/mês**. Ou seja: **ele gasta US$ 173 para
economizar US$ 68.** Prejuízo líquido de ~US$ 105/mês, mais 7 h/dia (1 h–7 h BRT) em que quase não
há tráfego e ele pinga ~105 vezes para ninguém.

**Correção (A):** trocar o TTL dos dois breakpoints para **1 hora** (`cache_control:
{"type": "ephemeral", "ttl": "1h"}`) e reduzir o warmer para **um ping a cada ~55 min**, usando
`max_tokens: 0` (o padrão atual da API para pré-aquecimento: não gera token de saída e não há
resposta para descartar; o `max_tokens=1` é o workaround antigo).

- Warmer: 26 pings/dia × 53.555 × US$ 0,30/MTok = **US$ 12,6/mês** (era 173).
- A escrita a 1 h custa 2× a base (US$ 6,00/MTok) em vez de 1,25× — mas passa a ser **rara**:
  as faixas "≤ 5 min" e "5 min–1 h" (87,8 % das chamadas) ficam quentes.
- **Economia: ~US$ 160 (warmer) + ~US$ 40 (cache_write da extração) = ~US$ 200/mês.**

> ⚠️ Conferir depois de aplicar: `usage.cache_read_input_tokens` tem de continuar alto. Qualquer
> byte que mude no prefixo invalida tudo depois dele — e o breakpoint 1 são os 6 masters, que só
> mudam quando editamos um MASTER.

### 2.2 O prompt de sistema é relido uma vez por chunk

Cada extração é fatiada em até `_MAX_CHUNKS = 4` pedaços paralelos (média medida: **3,28**), e
**cada chunk carrega o system inteiro**. Resultado: **157.212 tokens de `cache_read` por chamada**
(≈ 3,28 × 48 k) = US$ 0,047 só para reler o manual.

Onde isso dói: **84 % do custo está nas chamadas com 4 chunks** (692 chamadas, US$ 192,85), e a
média delas é de **1,14 "itens"** — ou seja, lotes pequenos sendo fatiados em 4 mesmo assim.

**Correção (B):** só fatiar acima de um piso de bilhetes. Abaixo dele, chamada única.
Economia estimada: **~US$ 25/mês.** Custo: latência maior nos lotes pequenos (que já são rápidos).

### 2.3 Os chunks correm entre si para escrever o mesmo cache

Os 3–4 chunks são disparados **ao mesmo tempo**. Quando o bloco da casa está frio, **todos erram o
cache juntos e todos escrevem** — daí o `cache_write` médio de **26.456 tokens** nas chamadas frias,
sendo que o bloco da casa tem 5–11 k. É a mesma escrita paga 2–4 vezes.

**Correção (C):** disparar o chunk 0 sozinho, esperar o primeiro token, e só então soltar os
demais — que passam a **ler** o que o primeiro escreveu. Economia estimada: **~US$ 15/mês.**

### 2.4 A Bet365 ainda passa pela IA — e é 43 % da conta

A extensão já lê o payload da API da casa e monta um bloco de texto estruturado. A IA é usada para
converter esse bloco estruturado em TSV — trabalho determinístico, com preço de modelo.

**Correção (D):** o parser determinístico já previsto na s107, começando pela Bet365.
Economia estimada: **~US$ 65/mês** (43 % do que sobrar depois de A, B e C).
Custo real: **manutenção** — quebra quando a casa muda o formato. É por isso que só vale para o
topo da fila de volume, e a Bet365 é, com folga, o topo.

### 2.5 Somando

| Correção | Esforço | Economia/mês |
|---|---|---|
| **A** — TTL 1 h + warmer a cada 55 min com `max_tokens: 0` | baixo | **US$ 200** |
| **B** — não fatiar lote pequeno | baixo | US$ 25 |
| **C** — escalonar o disparo dos chunks | baixo | US$ 15 |
| **D** — parser determinístico da Bet365 | alto | US$ 65 |
| | | **US$ 305 de US$ 402** |

| Cenário | Custo/mês | Custo/bilhete |
|---|---|---|
| Hoje | US$ 402 | **R$ 0,0773** |
| Depois de A + B + C | US$ 213 | **R$ 0,0501** |
| Depois de A + B + C + D | **US$ 97** | **R$ 0,0285** |

---

## 3. O eixo do plano: **contas ativas**, não bilhetes

O usuário não sabe quantos bilhetes faz por mês. Ele sabe quantas contas acompanha — e a medição
mostra que os dois andam juntos com folga surpreendente:

| Dono | Bilhetes/mês | Contas ativas | **Bilhetes por conta** |
|---|---|---|---|
| Feca | 4.890 | 28 | 175 |
| Gabriel | 3.162 | 14 | 226 |
| Jonathan | 2.702 | 15 | 180 |
| WilliamOliveira | 1.774 | 9 | 197 |
| Tonelada | 453 | 4 | 113 |

**Referência adotada: ~180 bilhetes por conta ativa por mês.** "Conta ativa" = conta com bilhete
no mês, não conta cadastrada (o Feca tem 174 cadastradas e 28 ativas — cobrar por cadastro seria
cobrar por arquivo morto).

---

## 4. Os planos

### 4.1 A escada proposta

| Plano | Contas ativas | Bilhetes/mês | **Preço** |
|---|---|---|---|
| **Teste** (14 dias) | 1 | ~180 | R$ 0 |
| **Solo** | 3 | ~540 | **R$ 49** |
| **Pro** | 10 | ~1.800 | **R$ 99** |
| **Operação** | 15 | ~2.700 | **R$ 149** |
| Operação+ | acima de 15 | — | sob consulta |

### 4.2 A margem — e por que o parser é pré-condição

| Plano | Preço | Custo **hoje** | Custo pós **A+B+C** | Custo pós **A+B+C+D** | Margem final |
|---|---|---|---|---|---|
| Solo (540) | R$ 49 | R$ 41,70 | R$ 27,05 | **R$ 15,39** | **69 %** |
| Pro (1.800) | R$ 99 | R$ 139,10 ❌ | R$ 90,20 | **R$ 51,30** | **48 %** |
| Operação (2.700) | R$ 149 | R$ 208,70 ❌ | R$ 135,30 | **R$ 76,95** | **48 %** |

**Leitura da tabela, que é o resultado do estudo:**

- **Hoje, com o custo real, só o Solo se paga.** O Pro dá prejuízo de R$ 40/mês por assinante e o
  Operação de R$ 60. Lançar preço agora seria vender abaixo do custo nos dois tiers de cima.
- **Só com A+B+C** (as três correções baratas, dias de trabalho) a escada inteira sai do vermelho,
  mas com margem apertada no topo.
- **Com o parser da Bet365**, a escada fecha em **48–69 % de margem bruta** e o teto de R$ 149 vira
  confortável.

> **Recomendação de ordem:** aplicar **A** primeiro (é uma linha de config, a maior economia e o
> menor risco), medir uma semana, depois B e C. Só então decidir sobre o parser — com o log de
> tokens já limpo do overhead, a fila de casas a portar fica óbvia.

### 4.3 Regras de contorno

- **Excedente, não corte.** Estourou o teto de contas: cobra R$ 0,10 por bilhete excedente (≈ 3,5×
  o custo pós-parser) ou sobe de plano. **Nunca parar de capturar** — o dano de um buraco no
  histórico é maior que o do excedente.
- **Import de planilha é gratuito e ilimitado.** Não passa pela IA (`origem='import'`: 43.492 dos
  58.967 bilhetes dos últimos 30 dias). É, inclusive, a melhor porta de entrada: o usuário chega
  com o histórico inteiro sem nos custar nada.
- **Quem vem pelo bot de tipster custa R$ 0 em token.** `SoChutes`, `reidocriquete`, `passapano` e
  `ZoraEsports` geraram 942 bilhetes em 30 dias com **zero** chamada ao modelo. É outra unidade
  econômica — e é o elo com o estudo de assinatura de tipsters, que já está feito.
- **Operadores multi-conta não cabem em plano público.** Feca (28 contas ativas / 174 cadastradas),
  arrudex (99 cadastradas), Jonathan (87). São conversa comercial, não tabela de preço.

---

## 5. O que este estudo NÃO resolve

### 5.1 Disposição a pagar não foi medida
Toda a escada acima é **construída de baixo para cima, a partir do custo**. Ninguém perguntou a
nenhum tester quanto pagaria. R$ 49/99/149 é o que o custo permite, não o que o mercado aceita.
O grupo `Sharpen - Testers` é a amostra à mão para descobrir isso.

### 5.2 O `/uso/tokens` mostra um "custo por item" errado por ~10×
`n_itens` é `len(base_content)` — número de **imagens/blocos de texto do lote**, comentado como
proxy no `main.py:2652`, não número de bilhetes. A tela acusa US$ 0,14–0,22 por "item" enquanto o
custo real por bilhete é US$ 0,015. **Quem olhar aquela tela para decidir preço decide errado.**
Corrigir o rótulo (ou o campo) é pré-requisito para a tela virar ferramenta de gestão.

### 5.3 Infra não foi medida
Railway (app + Postgres + `sharpen-bot`) não entra em nenhuma conta deste documento. É custo
**fixo**, então dilui com escala, mas define o piso do tier de entrada. Medir antes de publicar
preço.

### 5.4 Impostos, gateway e churn ficaram de fora
O estudo de assinatura de tipsters já tem o modelo de gateway (Asaas, split, Pix Automático) e a
crítica de opex com folha. Ao fechar o preço do apostador, reaproveitar aquele modelo em vez de
montar outro.

---

## 6. Decisões pendentes do Feca

| # | Decisão |
|---|---|
| 1 | Aplico a correção **A** (TTL 1 h + warmer 55 min, `max_tokens: 0`)? É a de maior retorno e menor risco. |
| 2 | Depois de medir A por ~1 semana, sigo com **B** e **C**? |
| 3 | O parser determinístico da Bet365 (**D**) entra na fila? Sem ele, R$ 149 não fecha com margem. |
| 4 | Consultar os testers sobre preço, ou fechar a tabela por dentro primeiro? |
| 5 | Medir a conta do Railway para completar o custo por usuário. |

---

VERSÃO: 2026
ATUALIZADO: 2026-08-24 (sessão 295 — estudo criado; nenhuma alteração de código)
