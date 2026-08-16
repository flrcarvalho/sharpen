# CASA_PITACO
## Camada de tradução — Pitaco → padrão global (FDC Capital)

> Este arquivo descreve **apenas** as particularidades da Pitaco.
> Estrutura, taxonomia, descrição, resultado e **cálculo** de odd vivem nos masters globais. Este arquivo **traduz**; não redefine.
> **Cálculo é global, localização é da casa.**
>
> Autoridades globais: `MASTER_OUTPUT_2026`, `MASTER_ESPORTES_2026`, `MASTER_APOSTAS_2026`, `MASTER_DESCRICAO_2026`, `MASTER_RESULTADO_2026`, `MASTER_PIPELINE_2026`.
> Saída final: **TSV** (ver `MASTER_OUTPUT_2026`).

---

## 1. Identidade

- Casa canônica: `Pitaco`
- Domínio: `pitaco.bet.br`
- Locale: pt-BR na interface **e** nos valores — dinheiro em formato BR (`R$ 101,00`) e odd com **ponto** decimal e sufixo `x` (`5.45x`)
- `Parceiro` / `Tipster`: preenchidos pela app; extrator deixa vazio

> **A casa é a antiga "Rei do Pitaco"** — mesma operação, marca nova do `.bet.br`.
> **`Pitaco` é o nome padrão desde 16/08/2026 (s270)**, e a grafia velha foi **unificada no
> banco** na mesma sessão (`scripts/unificar_casas.py --somente "Rei do Pitaco"`): 54 bilhetes
> de dois donos movidos, **54 assinaturas recalculadas**, resíduo **zero** nas 7 tabelas onde
> `casa` é texto, e as 57 assinaturas resultantes conferidas contra o que a próxima captura
> vai gerar (0 divergem → a dedup continua fechando). Não recriar a grafia antiga em lugar
> nenhum: ela não casa mais nenhuma linha.

> **Plataforma PRÓPRIA** (Next.js + gRPC-Web). Não é espelho de Altenar/BetBy/Kambi/
> BetConstruct: nenhum vocabulário de campo coincide, e o transporte é protobuf binário.

---

## 2. Modo de ingestão e layout

### 2.1 Modo de ingestão

- **PRIMÁRIO (captura SharpenUp):** **API + replay** — o `pt_inject.js` aprende url+headers de uma requisição real e busca ele mesmo o histórico em `POST /api/ui_betting_my_bets_components.UiMyBetsService/GetUiMyBetsTabContent` (ver §2.5).
- **SECUNDÁRIO:** screenshot / visão — cards de "Minhas Apostas".
- **FALLBACK:** texto colado da mesma lista.

> ⚠️ O robô de **rolagem genérico** (`roboScroll`) **não serve**: os cards ficam colados, sem linha em branco entre bilhetes, então o `innerText` vira um bloco único e a extração perde tudo depois dos primeiros (lição da KTO, s192).

### 2.2 Tipo do bilhete

A casa **estampa** o rótulo (`Dupla`, `Tripla`) no topo do card, e o robô o emite como `Rótulo da casa:`. A categoria, porém, sai do **número de seleções**, como nas demais:

| Seleções | Categoria `Aposta` |
|---|---|
| 1 | categoria do mercado da seleção |
| 2+ em **jogos diferentes** | `Múltipla` |
| 2+ no **mesmo jogo** (mesmo id de evento) | `Múltipla` — bet builder; seleções separadas por ` // ` (regra global #19) |

> Na amostra do recon (71 bilhetes) eram **51 duplas e 20 triplas**: **nenhuma simples**. O rótulo de bilhete simples ainda não foi visto.

### 2.3 Anatomia do card

```
[PITACO ▨]                                  ← faixa verde só nas GANHAS
Dupla                          4.18x » 2.18x ← rótulo + odd (riscada quando muda)
[✓|✗|◍] [Seleção]  [Anulado]     [Mercado]  ← uma linha por perna
Expandir aposta ⌄
Aposta                              Ganhou
R$ 101,00                        R$ 550,45  ← stake · retorno (R$ 0,00 em perdida)
[Encerrar aposta R$ 156,09]                 ← cashout (só em bilhete aberto)
5001000003872452 5                16/08/2026 - 09:05   ← código · data de COLOCAÇÃO
```

O código só aparece no card das **abertas**; nas finalizadas ele vive só no payload (§3).

### 2.4 Ordem do output

A lista exibe do **mais recente (topo)** para o **mais antigo (baixo)**. O TSV sai na ordem **inversa**: bilhete mais antigo = 1ª linha.

### 2.5 Captura por API — campos e armadilhas

Endpoint: `POST https://pitaco.bet.br/api/ui_betting_my_bets_components.UiMyBetsService/GetUiMyBetsTabContent`
Transporte: **gRPC-Web com protobuf binário** — corpo e resposta são frames de 5 bytes (flag + tamanho BE) + mensagem. Não há `.proto` publicado; o de-para abaixo foi medido cruzando o payload com o card e está travado em `extensor/harness/casos/pitaco.mjs`.

Corpo: `.1=1 · .2=pageSize · .3={.1:"finished"|"open", .2:2|1} · .4=página`.

**Autenticação é por HEADER** (Firebase Auth), não por cookie: `credentials:"include"` sozinho devolve **401**. O replay repete o pacote de ~20 headers da página.

> ⚠️ **O modo passivo é IMPOSSÍVEL nesta casa.** A página cancela o stream da própria resposta (`AbortController`); o `clone().arrayBuffer()` do hook morre com *"The user aborted a request"* em 100% das tentativas. Quem busca o dado é sempre o replay.

> ⚠️ **NUNCA paginar por página (`.4`) — perde bilhete.** Medido, determinístico: com `pageSize=20` as páginas devolvem 20 · 10 · 20 · 0 · 1, a **página 3 repete o primeiro código da página 1**, e a varredura vê **31 códigos únicos onde existem 49**. O critério "página menor que a pedida = fim" também é falso (a 2ª veio com 10 e a 3ª veio cheia). A estratégia certa é pedir a lista inteira num `pageSize` grande — o `pageSize` **é respeitado** (200 devolveu as 49 de uma vez). O fim autoritativo é o campo **`.5` da resposta**, presente só quando a página encheu **e** há mais.

> A própria tela da casa sofre da paginação furada: o filtro "Perdidas" trava em **20 cards** por mais que se role, enquanto a API tem **38**. A captura enxerga mais que a casa mostra.

Campos do bilhete:

| Campo | Conteúdo |
|---|---|
| `.1.1` | rótulo do tipo (`Dupla`, `Tripla`) |
| `.1.2` | stake formatado (`R$ 101,00`) |
| `.1.3` | odd **vigente** — ⚠ arredondada a 2 casas (§11) |
| `.1.4` | odd **original**, só quando mudou (perna anulada / mudança da casa) |
| `.4.1.1` | **código do bilhete** (17 dígitos) — chave de dedup |
| `.4.2` | timestamp unix da **colocação** |
| `.5.1` / `.5.4` | stake |
| `.5.2` / `.5.3` | retorno — ⚠ **realizado só depois de liquidado** |
| `.5.5` | retorno **potencial** |
| `.5.6` | stake em **centavos** (inteiro — a única grandeza que não passa por parser) |
| `.6` | **status do bilhete** (§5) |
| `.7.1` / `.7.2` / `.7.3` | cashout disponível: flag · valor formatado · centavos |
| `.3` (repetido) | pernas |

Campos da perna: `.2.1.2` seleção · `.2.1.3` mercado · `.2.1.6` status · `.2.1.8` odd vigente · `.2.1.9` odd original · `.1.1.1.1.1` mandante · `.1.1.2.1.1` visitante · `.3.4` id do evento.

> ⚠️ **`.5.2` de bilhete ABERTO vem igual ao potencial.** Lido como retorno, vira vitória fantasma — a mesma armadilha do `totalWin` da VaideBet. Quem decide é o status, nunca o dinheiro.

> ⚠️ **Não existe campo de ESPORTE no payload.** Busca por futebol/tênis/basquete/… no payload inteiro: zero ocorrências. O esporte sai do confronto e do mercado, como no modo cego — por isso o robô emite sempre `Jogo: <mandante> x <visitante>`.

---

## 3. ID do bilhete

- Formato: **17 dígitos** (`80010000038631931`). Prefixo `8001…` nas finalizadas e `5001…` nas abertas da amostra.
- Origem: `.4.1.1` do payload. Na tela, só o card de aposta **aberta** o estampa.
- Vai para a 11ª coluna interna (`Código`) e é a chave de dedup.

> ⚠️ Os códigos são **sequenciais por segundo de colocação** (`…632231` × `…632214`), logo quase idênticos entre si. Por isso a casa fica **fora** do snap por edit-distance de `corrigir_codigos_tsv` — e fica de graça: nenhuma das regexes que alimentam o snap casa 17 dígitos. A conferência de cobertura funciona pelo marcador genérico `[Código: …]`.

---

## 4. Data

**A coluna `Data` é a do EVENTO** (`MASTER_OUTPUT §2`). Numa múltipla, o evento **mais recente**.

⚠️ **Esta é a parte frágil da casa.** O campo de data da perna é um *oneof* de três formas, e a forma muda com o estado do evento:

| Forma | Quando | Conteúdo |
|---|---|---|
| `.3.3.1` | evento futuro | timestamp unix do início |
| `.3.1.1` + `.3.1.2` | evento **ao vivo** | período (`"1T "`) + timestamp |
| `.3.2.1` | evento passado | **texto `"15/08"` — SEM ANO** |

Em bilhete **finalizado**, são **112 de 112** pernas na forma de texto. O ano é derivado da **colocação** (`.4.2`), com janela de ±180 dias para a virada de ano.

> **A colocação NÃO substitui a data do evento:** elas divergem em **46 das 112** pernas resolvidas (41%). O bilhete `80010000038606210` foi colocado em 14/08 e o evento mais recente é 15/08.

O robô emite as duas, rotuladas (`Data (evento):` e `Data (colocação):`), justamente porque uma foi derivada da outra.

---

## 5. Status e Resultado

De-para do `.6`, medido **por contagem contra o filtro da tela** (recon s270) — não deduzido:

| `.6` | Tela | Resultado global |
|---|---|---|
| `1` | Em aberto (evento não começou) | **vazio** (não liquidar) |
| `2` | Em aberto (jogo em andamento) | **vazio** (não liquidar) |
| `3` | Ganhas | **W** |
| `4` | Perdidas | **L** |
| `8` | Reembolsadas ("A aposta foi recusada após revisão") | **V** |

Conferência: filtro "Ganhas" = 10 cards e a API devolve 10 com `.6=3`; "Reembolsadas" = 1 e a API devolve 1 com `.6=8`; "Encerradas" = 0 e a API devolve 0.

> ⚠️ **Leia o ENUM, nunca o dinheiro.** Na anulada o retorno é o **próprio stake devolvido** (R$ 101,00 sobre R$ 101,00): uma heurística financeira leria isso como ganho de odd 1,00.

Status de **perna** (`.2.1.6`): `1` não começou · `2` ao vivo · `3` ganhou · `4` perdeu · `5` anulado.

**Sem amostra** (não decidir por dedução quando aparecer): cashout **executado**, `half-won`/`half-lost` (HW/HL), aposta recusada por outro motivo, freebet.

---

## 6. Boost / promoção

Sem amostra. A home anuncia promoções ("Super Aumentadas", "Aumentadas", "Odd total mín. 4.00x"), mas **nenhum bilhete da amostra veio turbinado** e não há campo de boost identificado no payload.

Quando aparecer, vale a regra global: **W → `retorno ÷ stake`**, que absorve boost de odd e de lucro.

---

## 7. Cashout

A casa **tem** cashout: o card aberto mostra `Encerrar aposta R$ 156,09` e o payload traz `.7.1` (disponível), `.7.2` (valor) e `.7.3` (centavos). Existe também um método próprio, `GetUiMyBetsCalculateCashout`.

O robô emite `Cashout disponível (não executado):` — deixando explícito que é **oferta**, não realização.

> **Sem amostra de cashout EXECUTADO:** o filtro "Encerradas" da tela veio com **0 cards**. Qual `.6` sobra depois de sacar é desconhecido. Quando aparecer, aplicar `MASTER_RESULTADO §5.1.2`/`§5.6`: cashout ≠ stake → **W** com `Odd = Cashout ÷ Stake`; cashout = stake → **V**.

---

## 8. Bônus

Sem amostra.

---

## 9. Mapa de mercados (Pitaco → `Aposta` global)

Só o que a casa **confirmou** na amostra real (71 bilhetes / 162 pernas). Categoria pelo **objeto** da aposta (`MASTER_APOSTAS §1`).

| Pitaco exibe | Aposta global | Status |
|---|---|---|
| `Empate Anula a Aposta` | DNB | ✓ confirmado (19 pernas) |
| `Total De Gols` | Gols | ✓ confirmado (17) |
| `[Time] - Total De Gols` | Gols | ✓ confirmado (mercado por entidade) |
| `Time com Mais Escanteios` | Escanteios | ✓ confirmado (15) |
| `[Time] - Total de Escanteios` | Escanteios | ✓ confirmado |
| `Escanteios - Handicap de 3 Vias [placar]` | Escanteios | ✓ confirmado; o objeto é o escanteio, o handicap é a forma (§1) |
| `Vencedor` | ML | ✓ confirmado (13) |
| `Resultado Final` | ML | ✓ confirmado |
| `Dupla chance` | Dupla Chance | ✓ confirmado (12) |
| `Handicap` · `Handicap [placar]` · `Handicap Asiático` · `Handicap (Inc. Prorrogação e Penâltis)` | Handicap | ✓ confirmado |
| `Número Total de Quebras de Saque` | Games | ✓ confirmado (11); objeto = game/serviço. Sem sinônimo no master — ver §Feedback |
| `Total 180s` | Legs | ✓ confirmado (dardos) |
| `Leg Handicap` | Legs | ✓ confirmado (dardos) |
| `[Jogador] Assistências - Jogador` | Assistência | ✓ confirmado |
| `[Jogador] - Total de Pontos` | Pontos | ✓ confirmado |

> O mercado com **nome de time/jogador prefixado** (`Slovan Sabinov - Total De Gols`, `K. Mitchell Assistências - Jogador`) é o padrão desta casa para mercado de **entidade**: o prefixo vai para a **descrição**, não para a categoria.

---

## 10. Stake

- Campo `.5.6`, em **centavos inteiros** (`10100` = R$ 101,00). É a única grandeza que não passa por parser de texto — usar sempre este.
- O texto `.1.2` (`R$ 101,00`) é o mesmo valor, formatado.

---

## 11. Odds

Formato da casa: `5.45x` — ponto decimal e sufixo `x`.

⚠️ **A odd exibida é ARREDONDADA a 2 casas e não explica o retorno.** Medido: 3 das 10 ganhas divergem. O bilhete `80010000038606210` estampa `3.67x`, mas pagou **R$ 371,62** sobre R$ 101,00 — a odd real é **3,6795** (o produto das pernas: 2.23 × 1.65). Emitir a exibida erraria R$ 0,95 num bilhete só.

Ordem de precedência (implementada em `_oddPTC`):

1. **Ganha** → `retorno ÷ stake`, conciliado com o produto das pernas: se o produto explica o dinheiro **até o centavo**, ele é a odd verdadeira (quem arredondou foi o pagamento).
2. **Aberta / perdida** → `potencial ÷ stake`, com a mesma conciliação. O `.5.5` existe nas duas e carrega a odd contratada.
3. **Anulada** → a odd **vigente** (`1.00x`), com a original saindo na linha `Odd original (riscada pela casa):`. O potencial dela ainda guarda a odd de antes da anulação (5,94) e devolvê-la como "a odd" contradiria o card.

> **Redundância útil:** o produto das odds das pernas bate com a odd total do bilhete em **49 de 49** finalizados. Serve de conferência independente.

> **Odd riscada** (`4.18x » 2.18x`) aparece quando uma perna é anulada e o resto do bilhete segue valendo — o bilhete continua **W**, com a odd nova.

**Nunca truncar** (regra primordial). Decimal com vírgula no output.

---

## 12. Ruído a ignorar

Faixa verde `PITACO ▨` das ganhas · botão `Expandir aposta` / `Resumir aposta` · ícone de compartilhar · chips de filtro (`Todas`, `Ganhas`, `Perdidas`, `Encerradas`, `Reembolsadas`) · logos de time · rodapé institucional.

---

## 13. Pegadinhas (resumo rápido)

1. **Odd exibida arredondada** — não explica o retorno; o dinheiro (ou o produto das pernas) manda.
2. **Data do evento sem ano** em bilhete finalizado (112 de 112 pernas) — ano vem da colocação; e colocação ≠ evento em 41% das pernas.
3. **Retorno de aberta = potencial** — vitória fantasma se lido como realizado.
4. **Anulada devolve o stake** — o dinheiro parece ganho; quem decide é o `.6`.
5. **Paginação por página perde bilhete** (31 de 49) — pedir a lista inteira.
6. **Passivo impossível** — a página aborta a própria resposta; só replay.
7. **Sem campo de esporte** — inferir pelo confronto e pelo mercado.
8. **Auth por header, não por cookie** — `credentials:"include"` sozinho dá 401.

---

## 14. Validações específicas

- Todo bilhete tem `[Código: …]` de 17 dígitos.
- `Data (evento)` presente e coerente com `Data (colocação)` (evento ≥ colocação, salvo aposta ao vivo).
- Ganha: `retorno ÷ stake` bate com a odd emitida até o centavo.
- Aberta: sai **sem resultado** e com `Retorno potencial:`, nunca com "Ganhou".
- Anulada: `V`, P/L zero, com a observação de stake devolvido.

---

## 15. Exemplos golden (bilhetes reais — captura por API, 14–16/08/2026)

Travados em `extensor/harness/casos/pitaco.mjs`.

### G1 — W · Dupla · produto das pernas exato
`80010000038631931` · colocada 15/08/2026 09:29:43 · evento 15/08/2026 · stake R$ 101,00 · pernas 2.50 × 2.18 · retorno R$ 550,45 → **odd 5,45**.

### G2 — W · Dupla · **uma perna anulada, bilhete segue valendo**
`80010000038631915` · odd riscada `4.18x → 2.18x` · perna `Puchov` com `sel_status=5` e odd 1.00 (original 1.92) · retorno R$ 220,18 → **odd 2,18**.

### G3 — W · Dupla · **a odd exibida NÃO explica o retorno**
`80010000038606210` · exibida `3.67x` · stake R$ 101,00 · retorno **R$ 371,62** · produto 2.23 × 1.65 = 3,6795 → **odd 3,6795**. Também prova a data: colocada **14/08**, evento **15/08**.

### G4 — L · Dupla · odd do potencial
`80010000038632231` · exibida `3.51x` · potencial R$ 355,02 ÷ 101 = 3,515 → **odd 3,515** (o produto 1.90 × 1.85 confirma).

### G5 — V · Dupla · **anulada com stake devolvido**
`80010000038596497` · "A aposta foi recusada após revisão" · as duas pernas `Anulado` · odd riscada `5.94x → 1.00x` · retorno R$ 101,00 = stake → **V**, P/L zero.

### G6 — aberta · **com cashout oferecido**
`80010000038724525` · `.6=2` · odd 4,564 · `Encerrar aposta R$ 156,09` → sai **sem resultado**, com `Retorno potencial` e `Cashout disponível (não executado)`.

### G7 — aberta · **perna ao vivo**
`80010000038724511` · `.6=1` · perna `Eisenach ou empate` no `1T` → rotulada `AO VIVO (1T)`.

---

## Feedback para a camada global / MODELO

1. **Casa com duas grafias vivas no banco** é situação nova para o `_CASA_DISPLAY`: aqui foi resolvida registrando as duas e apontando as duas para um manual só (alias em `prompts.py`). Se repetir, vale generalizar em vez de multiplicar aliases.
2. **`Total 180s` e `Leg Handicap` (dardos)** foram mapeados para `Legs` pelo princípio do objeto; conferir contra `MASTER_APOSTAS §6 Dardos` quando houver mais amostra.
3. **`Número Total de Quebras de Saque`** (tênis) → `Games`: o objeto é o game/serviço. Não há sinônimo no MASTER para esse rótulo.

---

VERSÃO: 2026
ATUALIZADO: 2026-08-16 (sessão 270 — casa nova, captura por API)
